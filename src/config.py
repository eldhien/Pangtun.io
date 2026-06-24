DATASET_NAMES = [
    "antonheryanto/pantun",
    "Abdi008/Pantun_Indonesia",
]

# Alias untuk kompatibilitas kode lama.
DATASET_NAME = DATASET_NAMES[0]

DEFAULT_MODEL_NAME = "distilgpt2"
DEFAULT_OUTPUT_DIR = "models/pantun-gpt"

MAX_LENGTH = 160
TRAIN_TEST_SPLIT = 0.2
SEED = 42

DEFAULT_THEME = "umum"

SPECIAL_TOKENS = {
    "pad_token": "<PAD>",
    "bos_token": "<BOS_PANTUN>",
    "eos_token": "<END_PANTUN>",
}
