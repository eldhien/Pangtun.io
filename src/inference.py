\
import argparse
import os
import re

from config import DEFAULT_OUTPUT_DIR, SPECIAL_TOKENS


def normalize_pantun_lines(lines):
    return [line.strip() for line in lines if line and line.strip()]


def get_last_word(line: str) -> str:
    words = re.findall(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)?", line.lower())
    return words[-1] if words else ""


def get_rhyme_key(line: str, length: int = 2) -> str:
    last_word = get_last_word(line)
    return last_word[-length:] if len(last_word) >= length else last_word


def is_abab_rhyme(lines) -> bool:
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


def is_readable_line(line: str) -> bool:
    words = re.findall(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)?", line)
    if not 3 <= len(words) <= 10:
        return False

    letters = re.findall(r"[A-Za-zÀ-ÿ]", line)
    if not letters:
        return False

    letter_ratio = len(letters) / max(1, len(line))
    if letter_ratio < 0.65:
        return False

    # Tolak potongan teks yang tampak seperti token acak hasil model kecil.
    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", line.lower()):
        return False

    return True


def is_quality_pantun(lines) -> bool:
    return len(lines) == 4 and is_abab_rhyme(lines) and all(is_readable_line(line) for line in lines)


UNSAFE_TOPIC_KEYWORDS = {
    "konten seksual/pornografi": [
        "pornografi",
        "porno",
        "seks",
        "sex",
        "telanjang",
        "bugil",
        "mesum",
        "cabul",
        "pelecehan",
        "perkosaan",
    ],
    "narkoba dan zat terlarang": [
        "narkoba",
        "narkotika",
        "sabu",
        "ganja",
        "kokain",
        "heroin",
        "ekstasi",
        "obat terlarang",
        "jual obat",
        "meracik narkoba",
    ],
    "kekerasan dan senjata": [
        "membunuh",
        "bunuh diri",
        "pembunuhan",
        "bom",
        "teror",
        "senjata api",
        "menikam",
        "menyiksa",
        "racun",
    ],
    "aktivitas ilegal/berbahaya": [
        "mencuri",
        "penipuan",
        "scam",
        "phishing",
        "hack akun",
        "membobol",
        "membajak",
        "carding",
        "pemalsuan",
    ],
    "ujaran kebencian": [
        "rasis",
        "hina agama",
        "kebencian suku",
        "genosida",
    ],
}

SAFE_REFUSAL_MESSAGE = (
    "Maaf, tema tersebut tidak dapat diproses karena berpotensi mengarah ke "
    "{category}. Silakan gunakan tema yang aman dan positif, misalnya "
    "pendidikan, persahabatan, alam, kesehatan, atau teknologi."
)


def normalize_for_safety(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def detect_unsafe_category(text: str) -> str | None:
    normalized_text = normalize_for_safety(text)

    for category, keywords in UNSAFE_TOPIC_KEYWORDS.items():
        for keyword in keywords:
            normalized_keyword = normalize_for_safety(keyword)
            if re.search(rf"\b{re.escape(normalized_keyword)}\b", normalized_text):
                return category

    return None


def is_safe_text(text: str) -> bool:
    return detect_unsafe_category(text) is None


def build_refusal_message(category: str) -> str:
    return SAFE_REFUSAL_MESSAGE.format(category=category)


def choose_template_group(tema: str) -> str:
    tema_lower = tema.lower()
    groups = {
        "pendidikan": ["pendidikan", "belajar", "sekolah", "ilmu", "guru", "kampus"],
        "cinta": ["cinta", "sayang", "rindu", "kasih"],
        "persahabatan": ["sahabat", "teman", "persahabatan", "kawan"],
        "teknologi": ["teknologi", "komputer", "internet", "ai", "digital"],
        "alam": ["alam", "hutan", "laut", "gunung", "sungai", "bunga"],
        "agama": ["agama", "doa", "iman", "tuhan", "ibadah"],
        "kerja": ["kerja", "usaha", "karier", "bisnis", "dagang"],
        "kesehatan": ["sehat", "kesehatan", "olahraga", "sakit"],
    }

    for group, keywords in groups.items():
        if any(keyword in tema_lower for keyword in keywords):
            return group

    return "umum"


def get_rule_based_fallback(tema: str) -> str:
    clean_tema = re.sub(r"[^A-Za-zÀ-ÿ0-9 ]+", "", tema).strip().lower() or "kebaikan"
    template_group = choose_template_group(clean_tema)

    templates = {
        "pendidikan": [
            "Semalu tumbuh tepi perigi",
            "Tumbuh bersama pokok lada",
            "Rajin belajar setiap pagi",
            "Ilmu bertambah di dalam dada",
        ],
        "cinta": [
            "Bunga melati mekar di hati",
            "Harum semerbak di dalam taman",
            "Kasih dijaga sepenuh hati",
            "Agar bahagia sepanjang zaman",
        ],
        "persahabatan": [
            "Pergi ke dusun memetik duku",
            "Duku disimpan di atas para",
            "Sahabat setia menolong aku",
            "Susah senang tetap bersaudara",
        ],
        "teknologi": [
            "Pagi cerah membuka lemari",
            "Buku tersusun di meja utama",
            "Teknologi membantu sehari-hari",
            "Asal dipakai untuk sesama",
        ],
        "alam": [
            "Bunga melati menyejuk hati",
            "Embun menetes membasuh bumi",
            "Alam dijaga sepenuh hati",
            "Agar lestari di muka bumi",
        ],
        "agama": [
            "Bintang bersinar di malam hari",
            "Bulan terlihat di balik awan",
            "Doa dipanjat setiap hari",
            "Iman menjaga setiap insan",
        ],
        "kerja": [
            "Pergi ke pasar di pagi hari",
            "Membawa bekal di dalam raga",
            "Kerja tekun setiap hari",
            "Hasilnya baik untuk keluarga",
        ],
        "kesehatan": [
            "Jalan pagi menyehatkan diri",
            "Minum air dari telaga",
            "Tubuh sehat dirawat sendiri",
            "Hati tenang jiwa berharga",
        ],
        "umum": [
            "Pergi ke taman menata hati",
            "Melihat bunga dekat telaga",
            f"Tema {clean_tema} menguatkan hati",
            "Menjadi bekal penuh berharga",
        ],
    }

    return "\n".join(templates[template_group])


def build_prompt(tema: str) -> str:
    return (
        f"{SPECIAL_TOKENS['bos_token']}\n"
        f"Buat pantun Bahasa Indonesia dengan tema {tema}.\n"
        f"Pantun harus terdiri dari 4 baris.\n"
        f"Baris 1 dan 2 adalah sampiran.\n"
        f"Baris 3 dan 4 adalah isi.\n"
        f"Gunakan pola rima ABAB.\n"
        f"Pantun:\n"
    )


def clean_generated_text(text: str) -> str:
    """
    Membersihkan output model agar hanya menampilkan pantun.
    """
    text = text.replace(SPECIAL_TOKENS["bos_token"], "")
    text = text.replace(SPECIAL_TOKENS["eos_token"], "")
    text = text.replace("<PAD>", "")

    # Ambil bagian setelah label Pantun:
    if "Pantun:" in text:
        text = text.split("Pantun:", 1)[-1]

    # Hapus label tema jika ikut keluar
    text = re.sub(r"Tema\s*:\s*.*", "", text, flags=re.IGNORECASE)

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("pantun"):
            continue
        lines.append(line)

    # Pantun ideal 4 baris
    if len(lines) >= 4:
        lines = lines[:4]

    return "\n".join(lines).strip()


def generate_pantun(
    model_path: str,
    tema: str,
    max_new_tokens: int = 80,
    min_new_tokens: int = 20,
    temperature: float = 0.9,
    top_k: int = 50,
    top_p: float = 0.95,
    repetition_penalty: float = 1.2,
    attempts: int = 3,
) -> str:
    unsafe_category = detect_unsafe_category(tema)
    if unsafe_category:
        return build_refusal_message(unsafe_category)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    prompt = build_prompt(tema)

    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    fallback = ""

    with torch.no_grad():
        for _ in range(max(1, attempts)):
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                min_new_tokens=min_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

            generated_text = tokenizer.decode(output_ids[0], skip_special_tokens=False)
            pantun = clean_generated_text(generated_text)
            lines = normalize_pantun_lines(pantun.splitlines())

            if len(lines) == 4 and all(is_readable_line(line) for line in lines):
                fallback = pantun

            if is_quality_pantun(lines):
                safe_pantun = "\n".join(lines)
                if is_safe_text(safe_pantun):
                    return safe_pantun

    if fallback and is_safe_text(fallback):
        return fallback

    fallback_pantun = get_rule_based_fallback(tema)
    fallback_category = detect_unsafe_category(fallback_pantun)
    if fallback_category:
        return build_refusal_message(fallback_category)

    return fallback_pantun


def parse_args():
    parser = argparse.ArgumentParser(description="Generate pantun dari model Pantun-AI")
    parser.add_argument("--model_path", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--tema", type=str, required=True)
    parser.add_argument("--max_new_tokens", type=int, default=80)
    parser.add_argument("--min_new_tokens", type=int, default=20)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top_k", type=int, default=50)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--attempts", type=int, default=5)
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.model_path):
        raise FileNotFoundError(
            f"Model path tidak ditemukan: {args.model_path}. "
            "Jalankan training terlebih dahulu atau isi --model_path dengan benar."
        )

    pantun = generate_pantun(
        model_path=args.model_path,
        tema=args.tema,
        max_new_tokens=args.max_new_tokens,
        min_new_tokens=args.min_new_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        attempts=args.attempts,
    )

    print("=" * 60)
    print(f"Tema: {args.tema}")
    print("=" * 60)
    if pantun:
        print(pantun)
    else:
        print(
            "Model belum menghasilkan teks pantun. "
            "Coba naikkan --max_new_tokens, --temperature, atau train ulang beberapa epoch lagi."
        )


if __name__ == "__main__":
    main()
