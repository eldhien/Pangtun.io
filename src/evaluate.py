\
import argparse
import csv
import math
import os
import re
from statistics import mean

from config import DEFAULT_OUTPUT_DIR, MAX_LENGTH
from inference import (
    generate_pantun,
    get_rule_based_fallback,
    is_abab_rhyme,
    is_readable_line,
    normalize_pantun_lines,
)


DEFAULT_EVAL_THEMES = [
    "pendidikan",
    "persahabatan",
    "teknologi",
    "alam",
    "kesehatan",
]

THEME_KEYWORDS = {
    "pendidikan": ["pendidikan", "belajar", "sekolah", "ilmu", "guru", "kampus"],
    "persahabatan": ["sahabat", "teman", "kawan", "persaudaraan", "bersaudara"],
    "teknologi": ["teknologi", "digital", "komputer", "internet", "ai", "aplikasi"],
    "alam": ["alam", "hutan", "laut", "gunung", "sungai", "bunga", "bumi"],
    "kesehatan": ["sehat", "kesehatan", "olahraga", "tubuh", "jiwa", "tenang"],
    "cinta": ["cinta", "kasih", "sayang", "rindu", "hati"],
}


def parse_themes(raw_themes: str) -> list[str]:
    themes = [theme.strip().lower() for theme in raw_themes.split(",") if theme.strip()]
    return themes or DEFAULT_EVAL_THEMES


def tokenize_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", text.lower())


def score_relevance(tema: str, pantun: str) -> float:
    words = set(tokenize_words(pantun))
    theme_words = set(tokenize_words(tema))
    keywords = set(THEME_KEYWORDS.get(tema.lower(), [])) | theme_words

    if not keywords:
        return 0.0

    matched = keywords & words
    return min(1.0, len(matched) / max(1, min(3, len(keywords))))


def score_fluency(lines: list[str]) -> float:
    if not lines:
        return 0.0

    readable_count = sum(1 for line in lines if is_readable_line(line))
    return readable_count / len(lines)


def score_coherence(lines: list[str]) -> float:
    if len(lines) != 4:
        return 0.0

    unique_ratio = len(set(line.lower() for line in lines)) / len(lines)
    word_counts = [len(tokenize_words(line)) for line in lines]
    balanced_length = sum(1 for count in word_counts if 3 <= count <= 10) / len(word_counts)

    return (unique_ratio + balanced_length) / 2


def evaluate_pantun_quality(tema: str, pantun: str, source: str) -> dict:
    lines = normalize_pantun_lines(pantun.splitlines())
    structure_score = 1.0 if len(lines) == 4 else 0.0
    rhyme_score = 1.0 if is_abab_rhyme(lines) else 0.0
    relevance_score = score_relevance(tema, pantun)
    fluency_score = score_fluency(lines)
    coherence_score = score_coherence(lines)

    total_score = mean(
        [
            structure_score,
            rhyme_score,
            relevance_score,
            fluency_score,
            coherence_score,
        ]
    )

    return {
        "source": source,
        "tema": tema,
        "pantun": pantun,
        "line_count": len(lines),
        "structure_score": structure_score,
        "rhyme_abab_score": rhyme_score,
        "relevance_score": relevance_score,
        "fluency_score": fluency_score,
        "coherence_score": coherence_score,
        "total_score": total_score,
        "quality_label": "baik" if total_score >= 0.75 else "kurang_baik",
    }


def summarize_quality(rows: list[dict], source: str) -> dict:
    source_rows = [row for row in rows if row["source"] == source]
    if not source_rows:
        return {
            "source": source,
            "avg_total_score": 0.0,
            "avg_relevance": 0.0,
            "avg_fluency": 0.0,
            "avg_coherence": 0.0,
            "abab_rate": 0.0,
            "valid_4_line_rate": 0.0,
        }

    return {
        "source": source,
        "avg_total_score": mean(row["total_score"] for row in source_rows),
        "avg_relevance": mean(row["relevance_score"] for row in source_rows),
        "avg_fluency": mean(row["fluency_score"] for row in source_rows),
        "avg_coherence": mean(row["coherence_score"] for row in source_rows),
        "abab_rate": mean(row["rhyme_abab_score"] for row in source_rows),
        "valid_4_line_rate": mean(row["structure_score"] for row in source_rows),
    }


def run_quality_evaluation(args) -> tuple[list[dict], list[dict]]:
    themes = parse_themes(args.eval_themes)
    rows = []

    for tema in themes:
        model_output = generate_pantun(
            model_path=args.model_path,
            tema=tema,
            max_new_tokens=args.quality_max_new_tokens,
            min_new_tokens=args.quality_min_new_tokens,
            temperature=args.quality_temperature,
            top_k=args.quality_top_k,
            top_p=args.quality_top_p,
            attempts=args.quality_attempts,
        )
        baseline_output = get_rule_based_fallback(tema)

        rows.append(evaluate_pantun_quality(tema, model_output, source="model"))
        rows.append(evaluate_pantun_quality(tema, baseline_output, source="baseline_rule_based"))

    summaries = [
        summarize_quality(rows, "model"),
        summarize_quality(rows, "baseline_rule_based"),
    ]

    return rows, summaries


def save_quality_outputs(rows: list[dict], summaries: list[dict]) -> None:
    os.makedirs("outputs", exist_ok=True)

    with open("outputs/quality_evaluation.csv", "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "source",
            "tema",
            "line_count",
            "structure_score",
            "rhyme_abab_score",
            "relevance_score",
            "fluency_score",
            "coherence_score",
            "total_score",
            "quality_label",
            "pantun",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with open("outputs/generated_samples.txt", "w", encoding="utf-8") as f:
        f.write("CONTOH OUTPUT MODEL DAN BASELINE\n")
        f.write("================================\n\n")
        for row in rows:
            f.write(f"Sumber : {row['source']}\n")
            f.write(f"Tema   : {row['tema']}\n")
            f.write(f"Label  : {row['quality_label']}\n")
            f.write(f"Skor   : {row['total_score']:.2f}\n")
            f.write(row["pantun"])
            f.write("\n\n---\n\n")

    with open("outputs/quality_summary.txt", "w", encoding="utf-8") as f:
        f.write("RINGKASAN EVALUASI KUALITAS\n")
        f.write("===========================\n")
        for summary in summaries:
            f.write(f"\nSumber              : {summary['source']}\n")
            f.write(f"Rata-rata skor total: {summary['avg_total_score']:.3f}\n")
            f.write(f"Relevansi tema      : {summary['avg_relevance']:.3f}\n")
            f.write(f"Fluency/readability : {summary['avg_fluency']:.3f}\n")
            f.write(f"Koherensi           : {summary['avg_coherence']:.3f}\n")
            f.write(f"Rima ABAB           : {summary['abab_rate']:.3f}\n")
            f.write(f"Struktur 4 baris    : {summary['valid_4_line_rate']:.3f}\n")


def format_metric(value) -> str:
    return "Dilewati" if value is None else str(value)


def run_language_model_evaluation(args) -> tuple[float | None, float | None]:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

    from data_utils import prepare_dataset, tokenize_dataset

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

    return eval_loss, perplexity


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluasi model Pantun-AI")
    parser.add_argument("--model_path", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--max_length", type=int, default=MAX_LENGTH)
    parser.add_argument(
        "--eval_themes",
        type=str,
        default=",".join(DEFAULT_EVAL_THEMES),
        help="Daftar tema evaluasi kualitas, dipisahkan koma.",
    )
    parser.add_argument("--quality_attempts", type=int, default=3)
    parser.add_argument("--quality_max_new_tokens", type=int, default=80)
    parser.add_argument("--quality_min_new_tokens", type=int, default=20)
    parser.add_argument("--quality_temperature", type=float, default=0.9)
    parser.add_argument("--quality_top_k", type=int, default=50)
    parser.add_argument("--quality_top_p", type=float, default=0.95)
    parser.add_argument(
        "--skip_quality_eval",
        action="store_true",
        help="Lewati evaluasi kualitas output dan hanya hitung loss/perplexity.",
    )
    parser.add_argument(
        "--skip_lm_eval",
        action="store_true",
        help="Lewati loss/perplexity dan hanya jalankan evaluasi kualitas output.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.model_path):
        raise FileNotFoundError(
            f"Model path tidak ditemukan: {args.model_path}. "
            "Jalankan training terlebih dahulu."
        )

    os.makedirs("outputs", exist_ok=True)

    eval_loss = None
    perplexity = None
    if not args.skip_lm_eval:
        eval_loss, perplexity = run_language_model_evaluation(args)

    quality_rows = []
    quality_summaries = []
    if not args.skip_quality_eval:
        quality_rows, quality_summaries = run_quality_evaluation(args)
        save_quality_outputs(quality_rows, quality_summaries)

    with open("outputs/evaluation_result.txt", "w", encoding="utf-8") as f:
        f.write("HASIL EVALUASI PANTUN-AI\n")
        f.write("========================\n")
        f.write(f"Eval loss  : {format_metric(eval_loss)}\n")
        f.write(f"Perplexity : {format_metric(perplexity)}\n")
        if quality_summaries:
            f.write("\nRINGKASAN EVALUASI KUALITAS\n")
            f.write("===========================\n")
            for summary in quality_summaries:
                f.write(f"\nSumber              : {summary['source']}\n")
                f.write(f"Rata-rata skor total: {summary['avg_total_score']:.3f}\n")
                f.write(f"Relevansi tema      : {summary['avg_relevance']:.3f}\n")
                f.write(f"Fluency/readability : {summary['avg_fluency']:.3f}\n")
                f.write(f"Koherensi           : {summary['avg_coherence']:.3f}\n")
                f.write(f"Rima ABAB           : {summary['abab_rate']:.3f}\n")
                f.write(f"Struktur 4 baris    : {summary['valid_4_line_rate']:.3f}\n")

    print("HASIL EVALUASI")
    print("=" * 60)
    print(f"Eval loss  : {format_metric(eval_loss)}")
    print(f"Perplexity : {format_metric(perplexity)}")
    if quality_summaries:
        print("\nRINGKASAN EVALUASI KUALITAS")
        print("=" * 60)
        for summary in quality_summaries:
            print(f"Sumber              : {summary['source']}")
            print(f"Rata-rata skor total: {summary['avg_total_score']:.3f}")
            print(f"Relevansi tema      : {summary['avg_relevance']:.3f}")
            print(f"Fluency/readability : {summary['avg_fluency']:.3f}")
            print(f"Koherensi           : {summary['avg_coherence']:.3f}")
            print(f"Rima ABAB           : {summary['abab_rate']:.3f}")
            print(f"Struktur 4 baris    : {summary['valid_4_line_rate']:.3f}")
            print("-" * 60)
    print("Hasil disimpan ke outputs/evaluation_result.txt")
    if quality_summaries:
        print("Detail kualitas disimpan ke outputs/quality_evaluation.csv")
        print("Contoh output disimpan ke outputs/generated_samples.txt")


if __name__ == "__main__":
    main()
