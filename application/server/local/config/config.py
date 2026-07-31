import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from huggingface_hub import HfApi

MODELS_DIR = Path(__file__).resolve().parent.parent / "services" / "models"
MODELS_YAML_PATH = MODELS_DIR / "models.yaml"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(ENV_PATH)

HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
if not HUGGING_FACE_TOKEN:
    raise ValueError("HUGGING_FACE_TOKEN is not set in local/.env")

HF_CLIENT = HfApi(token=HUGGING_FACE_TOKEN)

REQUIRED_CAMERA_VIEWS = 2


def load_model_catalog(path: Path = MODELS_YAML_PATH) -> dict:
    with open(path, "r") as f:
        catalog = yaml.safe_load(f)

    return {
        name: {"repo_id": entry.get("repo_id"), "filename": entry.get("filename")}
        for name, entry in catalog.items()
    }
