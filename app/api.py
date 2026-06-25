import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.append(SRC_DIR)

from inference import generate_pantun


DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "pantun-gpt-gabungan")


class GeneratePantunRequest(BaseModel):
    tema: str = Field(..., min_length=1, max_length=120)
    temperature: float = Field(0.9, ge=0.1, le=1.5)
    top_k: int = Field(50, ge=1, le=100)
    top_p: float = Field(0.95, ge=0.1, le=1.0)
    max_new_tokens: int = Field(80, ge=20, le=150)


class GeneratePantunResponse(BaseModel):
    pantun: str


api = FastAPI(title="PANTUN-AI API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "model_exists": os.path.exists(DEFAULT_MODEL_PATH),
    }


@api.post("/api/generate", response_model=GeneratePantunResponse)
def generate_pantun_api(payload: GeneratePantunRequest):
    if not os.path.exists(DEFAULT_MODEL_PATH):
        raise HTTPException(
            status_code=404,
            detail=(
                "Model belum ditemukan. Jalankan training terlebih dahulu: "
                "python src/train.py --output_dir models/pantun-gpt-gabungan"
            ),
        )

    try:
        pantun = generate_pantun(
            model_path=DEFAULT_MODEL_PATH,
            tema=payload.tema.strip(),
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            top_k=payload.top_k,
            top_p=payload.top_p,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Terjadi error: {exc}") from exc

    if not pantun:
        raise HTTPException(
            status_code=500,
            detail="Model belum menghasilkan pantun yang valid. Coba ubah parameter atau tema.",
        )

    return GeneratePantunResponse(pantun=pantun)
