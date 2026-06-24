\
import re
from typing import Dict, List

from datasets import Dataset, DatasetDict, load_dataset
from sklearn.model_selection import train_test_split

from config import DATASET_NAMES, DEFAULT_THEME, SEED, TRAIN_TEST_SPLIT, SPECIAL_TOKENS


LINE_COLUMNS = ["Line 1", "Line 2", "Line 3", "Line 4"]


def clean_text(text: str) -> str:
    """
    Membersihkan teks pantun:
    - Menghapus spasi berlebihan
    - Menyeragamkan newline
    - Menghapus karakter kosong
    """
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\\n", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_last_word(line: str) -> str:
    words = re.findall(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)?", line.lower())
    return words[-1] if words else ""


def get_rhyme_key(line: str, length: int = 2) -> str:
    last_word = get_last_word(line)
    return last_word[-length:] if len(last_word) >= length else last_word


def is_abab_rhyme(lines: List[str]) -> bool:
    """
    Memeriksa rima pantun ABAB secara sederhana:
    baris 1 berima dengan baris 3, dan baris 2 dengan baris 4.
    """
    if len(lines) != 4:
        return False

    rhymes = [get_rhyme_key(line) for line in lines]
    return bool(
        rhymes[0]
        and rhymes[1]
        and rhymes[0] == rhymes[2]
        and rhymes[1] == rhymes[3]
        and rhymes[0] != rhymes[1]
    )


def normalize_pantun_lines(lines: List[str]) -> List[str]:
    return [clean_text(line) for line in lines if clean_text(line)]


def is_valid_pantun(lines: List[str]) -> bool:
    """
    Kaedah dasar pantun untuk data latih:
    - 4 baris
    - baris 1-2 sampiran, baris 3-4 isi
    - pola rima ABAB
    """
    normalized = normalize_pantun_lines(lines)
    return len(normalized) == 4 and is_abab_rhyme(normalized)


def detect_text_column(dataset: Dataset) -> str:
    """
    Mendeteksi kolom utama yang berisi teks pantun.
    Fungsi ini dibuat fleksibel karena struktur dataset Hugging Face bisa berbeda.
    """
    preferred_columns = [
        "pantun",
        "Pantun",
        "text",
        "Text",
        "content",
        "Content",
        "puisi",
        "poem",
    ]

    columns = dataset.column_names

    if all(col in columns for col in LINE_COLUMNS):
        return "__line_columns__"

    for col in preferred_columns:
        if col in columns:
            return col

    # fallback: cari kolom string pertama
    sample = dataset[0]
    for col in columns:
        if isinstance(sample.get(col), str):
            return col

    raise ValueError(
        f"Tidak menemukan kolom teks. Kolom tersedia: {columns}. "
        "Silakan cek struktur dataset dan sesuaikan fungsi detect_text_column()."
    )


def detect_theme_column(dataset: Dataset) -> str | None:
    """
    Mendeteksi kolom tema jika tersedia.
    Jika tidak ada, sistem tetap dapat berjalan dengan prompt tema dari user.
    """
    preferred_columns = ["tema", "Tema", "category", "kategori", "label", "topic"]
    columns = dataset.column_names

    for col in preferred_columns:
        if col in columns:
            return col

    return None


def load_dataset_split(dataset_name: str) -> Dataset:
    """
    Mengambil dataset Pantun Indonesia dari Hugging Face.
    Jika dataset punya split train, gunakan split train.
    Jika tidak, gabungkan split pertama.
    """
    ds = load_dataset(dataset_name)

    if isinstance(ds, DatasetDict):
        if "train" in ds:
            return ds["train"]

        # Ambil split pertama jika tidak ada train
        first_split = list(ds.keys())[0]
        return ds[first_split]

    return ds


def load_raw_datasets() -> List[tuple[str, Dataset]]:
    """
    Mengambil semua dataset dari Hugging Face.
    Setiap dataset boleh punya struktur kolom berbeda.
    """
    datasets = []

    for dataset_name in DATASET_NAMES:
        datasets.append((dataset_name, load_dataset_split(dataset_name)))

    return datasets


def build_training_text(tema: str, pantun: str) -> str:
    return (
        f"{SPECIAL_TOKENS['bos_token']}\n"
        f"Buat pantun Bahasa Indonesia dengan tema {tema}.\n"
        f"Pantun harus terdiri dari 4 baris.\n"
        f"Baris 1 dan 2 adalah sampiran.\n"
        f"Baris 3 dan 4 adalah isi.\n"
        f"Gunakan pola rima ABAB.\n"
        f"Pantun:\n"
        f"{pantun}\n"
        f"{SPECIAL_TOKENS['eos_token']}"
    )


def extract_pantun_lines(record: Dict, text_col: str) -> List[str]:
    if text_col == "__line_columns__":
        return normalize_pantun_lines([record.get(col, "") for col in LINE_COLUMNS])

    pantun = clean_text(record.get(text_col, ""))
    lines = normalize_pantun_lines(pantun.splitlines())

    if len(lines) == 1:
        # Beberapa dataset menyimpan empat baris sebagai satu teks dengan pemisah slash.
        lines = normalize_pantun_lines(re.split(r"\s*/\s*", lines[0]))

    return lines


def format_pantun_record(record: Dict, text_col: str, theme_col: str | None = None) -> Dict:
    """
    Mengubah satu data pantun menjadi format prompt-output untuk causal language modeling.

    Format training dibuat sama dengan prompt inference:
    <BOS_PANTUN>
    Buat pantun Bahasa Indonesia dengan tema pendidikan.
    Pantun harus terdiri dari 4 baris.
    Baris 1 dan 2 adalah sampiran.
    Baris 3 dan 4 adalah isi.
    Gunakan pola rima ABAB.
    Pantun:
    ...
    <END_PANTUN>
    """
    lines = extract_pantun_lines(record, text_col)
    pantun = "\n".join(lines)

    if theme_col and theme_col in record and record.get(theme_col):
        tema = clean_text(record.get(theme_col, DEFAULT_THEME))
    else:
        tema = DEFAULT_THEME

    return {
        "tema": tema,
        "pantun": pantun,
        "rima": "ABAB" if is_abab_rhyme(lines) else "tidak_valid",
        "text": build_training_text(tema, pantun),
    }


def normalize_dataset_rows(dataset_name: str, raw_ds: Dataset) -> List[Dict]:
    text_col = detect_text_column(raw_ds)
    theme_col = detect_theme_column(raw_ds)

    rows = []
    for record in raw_ds:
        lines = extract_pantun_lines(record, text_col)
        if not is_valid_pantun(lines):
            continue

        item = format_pantun_record(record, text_col=text_col, theme_col=theme_col)
        item["source_dataset"] = dataset_name

        if len(item["pantun"]) >= 20:
            rows.append(item)

    return rows


def prepare_dataset() -> DatasetDict:
    """
    Load dataset, bersihkan teks, format ulang, dan split train-validation.
    """
    rows = []
    seen_pantun = set()

    for dataset_name, raw_ds in load_raw_datasets():
        dataset_rows = normalize_dataset_rows(dataset_name, raw_ds)
        print(f"Dataset {dataset_name}: {len(dataset_rows)} pantun valid")

        added_count = 0
        for item in dataset_rows:
            dedupe_key = item["pantun"].lower()
            if dedupe_key in seen_pantun:
                continue

            seen_pantun.add(dedupe_key)
            rows.append(item)
            added_count += 1

        print(f"Dataset {dataset_name}: {added_count} pantun ditambahkan setelah deduplikasi")

    if len(rows) < 10:
        raise ValueError(
            "Jumlah data valid terlalu sedikit. Cek kembali format dataset atau fungsi preprocessing."
        )

    train_rows, val_rows = train_test_split(
        rows,
        test_size=TRAIN_TEST_SPLIT,
        random_state=SEED,
        shuffle=True,
    )

    return DatasetDict(
        {
            "train": Dataset.from_list(train_rows),
            "validation": Dataset.from_list(val_rows),
        }
    )


def tokenize_dataset(dataset: DatasetDict, tokenizer, max_length: int):
    """
    Tokenisasi dataset untuk causal language modeling.
    """
    def tokenize_function(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
        )

    tokenized = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["train"].column_names,
    )

    return tokenized
