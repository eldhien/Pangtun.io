# PANTUN-AI

PANTUN-AI adalah aplikasi Generative AI untuk membuat pantun Bahasa Indonesia berdasarkan tema atau kata kunci pengguna.

Dataset:
https://huggingface.co/datasets/antonheryanto/pantun
https://huggingface.co/datasets/Abdi008/Pantun_Indonesia

## Fitur
- Load dataset Pantun Indonesia dari Hugging Face
- Preprocessing teks pantun
- Filter data sesuai kaedah pantun 4 baris dan rima ABAB
- Fine-tuning model causal language model open source
- Generate pantun berdasarkan tema/kata kunci
- Evaluasi loss dan perplexity
- Demo aplikasi berbasis Gradio

## Struktur Folder

```text
pantun-ai/
├── README.md
├── requirements.txt
├── src/
│   ├── config.py
│   ├── data_utils.py
│   ├── train.py
│   ├── inference.py
│   └── evaluate.py
├── app/
│   └── app.py
├── outputs/
└── models/
```

## Instalasi

```bash
pip install -r requirements.txt
```

## Training / Fine-tuning

Default model menggunakan `distilgpt2` agar ringan. Pipeline training menggabungkan dua dataset: `antonheryanto/pantun` dan `Abdi008/Pantun_Indonesia`. Karena struktur keduanya berbeda, preprocessing akan mendeteksi kolom teks secara otomatis, menggabungkan empat baris pantun bila kolomnya terpisah, lalu menormalisasi semuanya ke format training yang sama.

Data yang dipakai tetap difilter sesuai kaedah pantun dasar: 4 baris, baris 1-2 sebagai sampiran, baris 3-4 sebagai isi, dan pola rima ABAB.

Untuk hasil Bahasa Indonesia yang lebih baik, ganti model dengan model GPT Indonesia yang tersedia di Hugging Face.

```bash
python src/train.py --model_name distilgpt2 --output_dir models/pantun-gpt --epochs 3
```

Contoh jika ingin memakai model Indonesia:

```bash
python src/train.py --model_name cahya/gpt2-small-indonesian-522M --output_dir models/pantun-gpt --epochs 3
```

## Generate Pantun via CLI

```bash
python src/inference.py --model_path models/pantun-gpt --tema "pendidikan"
```

## Evaluasi

```bash
python src/evaluate.py --model_path models/pantun-gpt
```

## Jalankan Aplikasi Gradio

```bash
python app/app.py
```

Lalu buka URL lokal yang muncul di terminal.

## Catatan
Proyek ini tidak menggunakan provider LLM/API tertutup sebagai inti AI. Model dijalankan dan di-fine-tuning secara lokal menggunakan library open source.
