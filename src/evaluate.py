\
import argparse
import math
import os

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

from config import DEFAULT_OUTPUT_DIR, MAX_LENGTH
from data_utils import prepare_dataset, tokenize_dataset


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluasi model Pantun-AI")
    parser.add_argument("--model_path", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--max_length", type=int, default=MAX_LENGTH)
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.model_path):
        raise FileNotFoundError(
            f"Model path tidak ditemukan: {args.model_path}. "
            "Jalankan training terlebih dahulu."
        )

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    model = AutoModelForCausalLM.from_pretrained(args.model_path)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dataset = prepare_dataset()
    tokenized_dataset = tokenize_dataset(dataset, tokenizer, max_length=args.max_length)

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    training_args = TrainingArguments(
        output_dir="outputs/eval_temp",
        per_device_eval_batch_size=args.batch_size,
        report_to="none",
        prediction_loss_only=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        eval_dataset=tokenized_dataset["validation"],
        data_collator=data_collator,
    )

    result = trainer.evaluate()
    eval_loss = result.get("eval_loss")
    perplexity = math.exp(eval_loss) if eval_loss is not None else None

    os.makedirs("outputs", exist_ok=True)

    with open("outputs/evaluation_result.txt", "w", encoding="utf-8") as f:
        f.write("HASIL EVALUASI PANTUN-AI\n")
        f.write("========================\n")
        f.write(f"Eval loss  : {eval_loss}\n")
        f.write(f"Perplexity : {perplexity}\n")

    print("HASIL EVALUASI")
    print("=" * 60)
    print(f"Eval loss  : {eval_loss}")
    print(f"Perplexity : {perplexity}")
    print("Hasil disimpan ke outputs/evaluation_result.txt")


if __name__ == "__main__":
    main()
