import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from huggingface_hub import HfApi

MODELS_DIR = Path(__file__).resolve().parent.parent / "services" / "models"
MODELS_YAML_PATH = MODELS_DIR / "models.yaml"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

ENGINE_DIR = Path(__file__).resolve().parent.parent / "services" / "engine"
VLA_SERVER_BINARY = ENGINE_DIR / "build" / "vla-server"
ENGINE_BIND_ADDR = "tcp://127.0.0.1:5555"

load_dotenv(ENV_PATH)

HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
if not HUGGING_FACE_TOKEN:
    raise ValueError("HUGGING_FACE_TOKEN is not set in local/.env")

HF_CLIENT = HfApi(token=HUGGING_FACE_TOKEN)

REQUIRED_CAMERA_VIEWS = 2

# Feetech (scservo_sdk) actuator protocol -- the only supported driver for V1.
ACTUATOR_BAUDRATE = 1_000_000  # SDK default for STS/SMS-series Feetech servos
ACTUATOR_PROTOCOL_END = 0  # STS/SMS series; SCS series would be 1
DEFAULT_SERVO_IDS = [1, 2, 3, 4, 5, 6]  # reference arm's servo IDs; caller can override
ACTUATOR_PRESENT_POSITION_ADDR = 56  # common STS/SMS-series control-table address -- UNVERIFIED against your specific servo model
ACTUATOR_GOAL_POSITION_ADDR = 42  # common STS/SMS-series control-table address -- UNVERIFIED against your specific servo model

# PID gains -- PLACEHOLDER defaults, NOT tuned against real hardware. Must be
# tuned on the actual arm before this is safe to run for real.
PID_KP = 1.0
PID_KI = 0.0
PID_KD = 0.0
PID_LOOP_HZ = 50
PID_POSITION_TOLERANCE = 20  # servo position units -- PLACEHOLDER, needs tuning


def load_model_catalog(path: Path = MODELS_YAML_PATH) -> dict:
    with open(path, "r") as f:
        catalog = yaml.safe_load(f)

    return {
        name: {
            "repo_id": entry.get("repo_id"),
            "filename": entry.get("filename"),
            "launch_env": entry.get("launch_env"),
            "tokenizer_repo": entry.get("tokenizer_repo"),
            "max_state_dim": entry.get("max_state_dim"),
            "image_size": entry.get("image_size"),
            "camera_views": entry.get("camera_views"),
        }
        for name, entry in catalog.items()
    }
