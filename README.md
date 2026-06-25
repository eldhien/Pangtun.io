# PANTUN-AI

PANTUN-AI adalah aplikasi Generative AI untuk membuat pantun Bahasa Indonesia berdasarkan tema atau kata kunci pengguna. Proyek ini menggunakan model causal language model dari Hugging Face, lalu di-fine-tuning dengan dataset pantun Indonesia.

Dataset yang digunakan:

- https://huggingface.co/datasets/antonheryanto/pantun
- https://huggingface.co/datasets/Abdi008/Pantun_Indonesia

## Fitur

- Load dataset pantun Indonesia dari Hugging Face
- Preprocessing teks pantun
- Filter data sesuai kaidah pantun 4 baris dan rima ABAB
- Fine-tuning model causal language model open source
- Generate pantun berdasarkan tema/kata kunci
- Evaluasi loss dan perplexity
- Demo aplikasi berbasis Gradio
- Fallback rule-based jika output model belum valid
- Guardrail keamanan untuk menolak tema berbahaya seperti pornografi, narkoba, kekerasan, aktivitas ilegal, dan ujaran kebencian

## Struktur Folder

```text
pantun-aiV2/
|-- README.md
|-- requirements.txt
|-- src/
|   |-- config.py
|   |-- data_utils.py
|   |-- train.py
|   |-- inference.py
|   `-- evaluate.py
|-- app/
|   `-- app.py
|-- outputs/
`-- models/
```

## Persiapan Environment

Disarankan menggunakan virtual environment (`venv`) agar package proyek tidak bercampur dengan instalasi Python global.

Pastikan Python sudah terinstall. Disarankan menggunakan Python 3.10 atau 3.11.

### 1. Buat virtual environment

Windows PowerShell:

```powershell
python -m venv venv
```

Linux/macOS:

```bash
python3 -m venv venv
```

### 2. Aktifkan virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Jika PowerShell menolak menjalankan script, jalankan:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install package yang dibutuhkan

Upgrade `pip` terlebih dahulu:

```bash
python -m pip install --upgrade pip
```

Install semua dependency:

```bash
pip install -r requirements.txt
```

Package utama yang digunakan proyek ini:

- `torch`: menjalankan dan training model neural network
- `transformers`: load model/tokenizer GPT dari Hugging Face
- `datasets`: mengambil dataset dari Hugging Face
- `accelerate`: membantu proses training model
- `evaluate`: evaluasi model
- `numpy`, `pandas`, `scikit-learn`: pengolahan data dan split dataset
- `gradio`: membuat demo aplikasi web

## Rekomendasi Model

Untuk perangkat kecil atau laptop tanpa GPU besar, gunakan `distilgpt2`.

Kelebihan:

- Lebih ringan
- Lebih cepat untuk eksperimen
- Cocok untuk testing pipeline training

Kekurangan:

- Model dasarnya berbahasa Inggris
- Hasil pantun Bahasa Indonesia biasanya tidak sebaik model Indonesia

Untuk hasil Bahasa Indonesia yang lebih optimal, gunakan:

```text
cahya/gpt2-small-indonesian-522M
```

Model tersebut lebih cocok untuk Bahasa Indonesia, tetapi membutuhkan resource lebih besar dibanding `distilgpt2`. Jika RAM/VRAM terbatas, kecilkan `--batch_size` menjadi `1` dan gunakan epoch lebih sedikit saat percobaan awal.

## Training / Fine-tuning

Script training ada di `src/train.py`.

Training ringan untuk device kecil:

```bash
python src/train.py --model_name distilgpt2 --output_dir models/pantun-gpt-gabungan --epochs 3 --batch_size 2
```

Training dengan model Bahasa Indonesia yang direkomendasikan:

```bash
python src/train.py --model_name cahya/gpt2-small-indonesian-522M --output_dir models/pantun-gpt-gabungan --epochs 3 --batch_size 2
```

Jika perangkat terasa berat atau muncul error memori:

```bash
python src/train.py --model_name cahya/gpt2-small-indonesian-522M --output_dir models/pantun-gpt-gabungan --epochs 1 --batch_size 1
```

Catatan:

- Output model disimpan ke folder yang diisi pada `--output_dir`.
- Aplikasi Gradio default membaca model dari `models/pantun-gpt-gabungan`.
- Jika ingin memakai path lain, sesuaikan `DEFAULT_MODEL_PATH` di `app/app.py` atau jalankan inference CLI dengan `--model_path`.

## Generate Pantun via CLI

Setelah training selesai, generate pantun dengan:

```bash
python src/inference.py --model_path models/pantun-gpt-gabungan --tema "pendidikan"
```

Contoh tema lain:

```bash
python src/inference.py --model_path models/pantun-gpt-gabungan --tema "persahabatan"
python src/inference.py --model_path models/pantun-gpt-gabungan --tema "teknologi"
python src/inference.py --model_path models/pantun-gpt-gabungan --tema "cinta"
```

Jika tema mengarah ke konten berbahaya, sistem akan menolak sebelum proses generate dijalankan:

```bash
python src/inference.py --model_path models/pantun-gpt-gabungan --tema "narkoba"
```

Contoh respons:

```text
Maaf, tema tersebut tidak dapat diproses karena berpotensi mengarah ke narkoba dan zat terlarang. Silakan gunakan tema yang aman dan positif, misalnya pendidikan, persahabatan, alam, kesehatan, atau teknologi.
```

Parameter generation yang bisa diatur:

```bash
python src/inference.py --model_path models/pantun-gpt-gabungan --tema "alam" --temperature 0.9 --top_k 50 --top_p 0.95 --max_new_tokens 80
```

Penjelasan singkat:

- `--temperature`: makin tinggi, output makin variatif
- `--top_k`: membatasi pilihan token ke kandidat terbaik
- `--top_p`: nucleus sampling untuk menjaga output tetap natural
- `--max_new_tokens`: panjang maksimal teks yang dihasilkan

## Evaluasi Model

Untuk mengevaluasi model:

```bash
python src/evaluate.py --model_path models/pantun-gpt-gabungan
```

Hasil evaluasi akan menampilkan:

- `loss` dan `perplexity` pada data validasi
- skor struktur pantun 4 baris
- skor rima ABAB
- skor relevansi tema
- skor fluency/readability
- skor koherensi
- perbandingan dengan baseline rule-based
- contoh output baik/kurang baik berdasarkan skor otomatis

File evaluasi yang dihasilkan:

```text
outputs/evaluation_result.txt
outputs/quality_summary.txt
outputs/quality_evaluation.csv
outputs/generated_samples.txt
```

Contoh evaluasi dengan tema khusus:

```bash
python src/evaluate.py --model_path models/pantun-gpt-gabungan --eval_themes "pendidikan,alam,teknologi,persahabatan,kesehatan"
```

Jika hanya ingin menghitung loss dan perplexity tanpa generate contoh pantun:

```bash
python src/evaluate.py --model_path models/pantun-gpt-gabungan --skip_quality_eval
```

Jika environment sedang bermasalah saat load dataset/pyarrow dan hanya ingin membuat evaluasi kualitas output:

```bash
python src/evaluate.py --model_path models/pantun-gpt-gabungan --skip_lm_eval
```

Perplexity yang lebih rendah biasanya menandakan model lebih baik dalam memprediksi teks validasi. Skor kualitas digunakan untuk melihat apakah output pantun relevan dengan tema, terbaca natural, koheren, dan mengikuti rima ABAB.

## Jalankan Aplikasi React shadcn

Pastikan model sudah ada di:

```text
models/pantun-gpt-gabungan
```

Jalankan backend Python API:

```bash
uvicorn app.api:api --reload --port 8000
```

Di terminal lain, jalankan frontend React:

```bash
cd frontend
pnpm install
pnpm run dev
```

Buka URL lokal Vite:

```text
http://127.0.0.1:5173
```

Frontend shadcn akan memanggil fitur Python melalui endpoint `POST /api/generate`.

## Jalankan Aplikasi Gradio Opsional

Pastikan model sudah ada di:

```text
models/pantun-gpt-gabungan
```

Lalu jalankan:

```bash
python app/app.py
```

Buka URL lokal yang muncul di terminal, biasanya:

```text
http://127.0.0.1:7860
```

Cara pakai aplikasi:

1. Masukkan tema atau kata kunci pantun.
2. Atur `Temperature`, `Top-K`, `Top-P`, dan `Max New Tokens` jika diperlukan.
3. Klik `Generate Pantun`.
4. Klik tombol baca pantun jika ingin mendengarkan hasilnya melalui fitur speech browser.

## Alur Penggunaan Singkat

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/train.py --model_name distilgpt2 --output_dir models/pantun-gpt-gabungan --epochs 3
python src/inference.py --model_path models/pantun-gpt-gabungan --tema "pendidikan"
uvicorn app.api:api --reload --port 8000
cd frontend
pnpm install
pnpm run dev
```

## Catatan

Proyek ini tidak menggunakan provider LLM/API tertutup sebagai inti AI. Model dijalankan dan di-fine-tuning secara lokal menggunakan library open source.

Proyek ini juga membatasi tema yang berpotensi membahayakan pengguna atau orang lain. Filter keamanan dilakukan pada input tema dan output pantun untuk mencegah konten pornografi, narkoba, kekerasan, aktivitas ilegal, dan ujaran kebencian.
