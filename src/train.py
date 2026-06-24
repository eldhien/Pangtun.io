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
    set_seed,
)

from config import (
    DATASET_NAMES,
    DEFAULT_MODEL_NAME,
    DEFAULT_OUTPUT_DIR,
    MAX_LENGTH,
    SEED,
    SPECIAL_TOKENS,
)
from data_utils import prepare_dataset, tokenize_dataset


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tuning model generatif untuk Pantun AI")

    parser.add_argument(
        "--model_name",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help="Nama model Hugging Face. Contoh: distilgpt2 atau cahya/gpt2-small-indonesian-522M",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Folder output model hasil fine-tuning",
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--max_length", type=int, default=MAX_LENGTH)
    parser.add_argument("--save_steps", type=int, default=500)
    parser.add_argument("--eval_steps", type=int, default=500)

    return parser.parse_args()


def main():
    args = parse_args()
    set_seed(SEED)

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60)
    print("PANTUN-AI TRAINING")
    print("=" * 60)
    print(f"Dataset     : {', '.join(DATASET_NAMES)}")
    print(f"Base model  : {args.model_name}")
    print(f"Output dir  : {args.output_dir}")
    print("=" * 60)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    # Tambahkan special token jika belum tersedia
    tokenizer.add_special_tokens(SPECIAL_TOKENS)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = SPECIAL_TOKENS["pad_token"]

    model = AutoModelForCausalLM.from_pretrained(args.model_name)
    model.resize_token_embeddings(len(tokenizer))

    dataset = prepare_dataset()
    tokenized_dataset = tokenize_dataset(dataset, tokenizer, max_length=args.max_length)

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    use_cuda = torch.cuda.is_available()
    print(f"CUDA tersedia: {use_cuda}")

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        save_total_limit=2,
        logging_steps=50,
        prediction_loss_only=True,
        fp16=use_cuda,
        report_to="none",
        seed=SEED,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["validation"],
        data_collator=data_collator,
    )

    trainer.train()

    eval_result = trainer.evaluate()
    eval_loss = eval_result.get("eval_loss")

    if eval_loss is not None:
        perplexity = math.exp(eval_loss)
        print(f"Validation loss: {eval_loss:.4f}")
        print(f"Perplexity     : {perplexity:.4f}")

    print("Menyimpan model dan tokenizer...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    print(f"Model berhasil disimpan di: {args.output_dir}")


if __name__ == "__main__":
    main()
