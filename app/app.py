\
import os
import sys

import gradio as gr

# Agar app.py bisa import file dari folder src
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.append(SRC_DIR)

from inference import generate_pantun


DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "pantun-gpt-gabungan")


def generate_ui(tema, temperature, top_k, top_p, max_new_tokens):
    if not os.path.exists(DEFAULT_MODEL_PATH):
        return (
            "Model belum ditemukan.\n\n"
            "Jalankan training terlebih dahulu:\n"
            "python src/train.py --output_dir models/pantun-gpt-gabungan"
        )

    if not tema or not tema.strip():
        return "Masukkan tema terlebih dahulu. Contoh: pendidikan, cinta, persahabatan."

    try:
        pantun = generate_pantun(
            model_path=DEFAULT_MODEL_PATH,
            tema=tema.strip(),
            max_new_tokens=int(max_new_tokens),
            temperature=float(temperature),
            top_k=int(top_k),
            top_p=float(top_p),
        )

        if not pantun:
            return "Model belum menghasilkan pantun yang valid. Coba ubah temperature atau tema."

        return pantun

    except Exception as e:
        return f"Terjadi error: {str(e)}"


with gr.Blocks(title="PANTUN-AI") as demo:
    gr.Markdown(
        """
        # PANTUN-AI
        Aplikasi Generative AI untuk membuat pantun Bahasa Indonesia berdasarkan tema pengguna.

        Dataset: `antonheryanto/pantun`
        """
    )

    with gr.Row():
        with gr.Column():
            tema = gr.Textbox(
                label="Tema / Kata Kunci",
                placeholder="Contoh: pendidikan, cinta, persahabatan, teknologi",
            )
            temperature = gr.Slider(
                minimum=0.1,
                maximum=1.5,
                value=0.9,
                step=0.1,
                label="Temperature",
            )
            top_k = gr.Slider(
                minimum=1,
                maximum=100,
                value=50,
                step=1,
                label="Top-K",
            )
            top_p = gr.Slider(
                minimum=0.1,
                maximum=1.0,
                value=0.95,
                step=0.05,
                label="Top-P",
            )
            max_new_tokens = gr.Slider(
                minimum=20,
                maximum=150,
                value=80,
                step=5,
                label="Max New Tokens",
            )
            btn = gr.Button("Generate Pantun")

        with gr.Column():
            output = gr.Textbox(
                label="Hasil Pantun",
                lines=8,
            )

    btn.click(
        fn=generate_ui,
        inputs=[tema, temperature, top_k, top_p, max_new_tokens],
        outputs=output,
    )

    gr.Markdown(
        """
        ## Cara Pakai
        1. Masukkan tema atau kata kunci.
        2. Atur parameter generation jika diperlukan.
        3. Klik **Generate Pantun**.
        """
    )


if __name__ == "__main__":
    demo.launch()
