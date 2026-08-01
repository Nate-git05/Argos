"""Central config for the Argos daemon: filesystem layout, the engine
binary/bind address, the Hugging Face client, actuator protocol constants,
and PID tuning. Every other daemon module imports its constants from here
instead of hardcoding them, so a hardware/deployment change only needs to
happen in one place.

Importing this module has a side effect: it loads local/.env and will raise
immediately if HUGGING_FACE_TOKEN isn't set. That's deliberate -- almost
every route in this daemon eventually needs Hub access (model pulls,
tokenizer downloads), so failing at import time surfaces a misconfigured
install immediately instead of on the first request that happens to need it.
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from huggingface_hub import HfApi

# --- filesystem layout -------------------------------------------------
# Everything below is resolved relative to this file's location, not the
# process's cwd, so the daemon works the same whether it's started by
# systemd (cwd = repo root) or run directly from anywhere.
MODELS_DIR = Path(__file__).resolve().parent.parent / "services" / "models"
MODELS_YAML_PATH = MODELS_DIR / "models.yaml"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

# The vla.cpp engine clone + its build output. install.sh is responsible for
# actually building vla-server here -- config.py just needs to know where to
# find (or fail to find) the resulting binary.
ENGINE_DIR = Path(__file__).resolve().parent.parent / "services" / "engine"
VLA_SERVER_BINARY = ENGINE_DIR / "build" / "vla-server"
# Loopback-only: vla-server prints an explicit "no authentication" warning if
# bound beyond localhost, and the daemon + engine always run on the same
# box, so there's no reason to expose this port more broadly.
ENGINE_BIND_ADDR = "tcp://127.0.0.1:5555"

load_dotenv(ENV_PATH)

HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
if not HUGGING_FACE_TOKEN:
    raise ValueError("HUGGING_FACE_TOKEN is not set in local/.env")

HF_CLIENT = HfApi(token=HUGGING_FACE_TOKEN)

# Every model in the catalog needs exactly 2 camera views -- confirmed by
# reading each architecture's actual predict-chunk code in vla.cpp, not
# assumed. See models.yaml's per-model camera_views field for the specific
# named views each model expects.
REQUIRED_CAMERA_VIEWS = 2

# --- Feetech (scservo_sdk) actuator protocol ----------------------------
# The only supported actuator driver for V1 -- there's no protocol-selection
# step anywhere in the codebase, connect_actuator always speaks Feetech.
ACTUATOR_BAUDRATE = 1_000_000  # SDK default for STS/SMS-series Feetech servos
ACTUATOR_PROTOCOL_END = 0  # STS/SMS series; SCS series would be 1
DEFAULT_SERVO_IDS = [1, 2, 3, 4, 5, 6]  # reference arm's servo IDs; connect_actuator's caller can override
# Both control-table addresses below are the common STS/SMS-series
# convention (matches LeRobot's Feetech driver), copied here as a starting
# point -- NEITHER has been verified against the actual servo model this
# arm uses. Wrong read address just returns garbage (low risk); wrong write
# address could write to an unintended register, so confirm these against
# your servo's datasheet before running real hardware.
ACTUATOR_PRESENT_POSITION_ADDR = 56
ACTUATOR_GOAL_POSITION_ADDR = 42

# --- PID loop tuning -----------------------------------------------------
# All four of these are PLACEHOLDER values, not derived from any real
# hardware characterization -- they exist so the control loop has *some*
# well-defined behavior to test the software architecture against. Treat
# a fresh arm as untuned and expect to retune Kp/Ki/Kd/tolerance once real
# position-vs-response data is available.
PID_KP = 1.0
PID_KI = 0.0
PID_KD = 0.0
PID_LOOP_HZ = 50  # control-loop rate; independent of and much faster than inference
PID_POSITION_TOLERANCE = 20  # servo position units within which a target counts as "reached"

# Mechanical center of a 12-bit position sensor (0-4095), applied uniformly
# to every connected servo when /stop drives the arm home. This is NOT a
# verified safe pose -- it says nothing about this specific arm's joint
# limits or collision geometry. Replace with real per-joint home positions
# before relying on this for anything safety-relevant.
ACTUATOR_HOME_POSITION = 2048
ACTUATOR_HOME_TIMEOUT_S = 5.0


def load_model_catalog(path: Path = MODELS_YAML_PATH) -> dict:
    """Parses models.yaml into the subset of fields code actually needs.

    Deliberately narrow: the yaml carries a lot of human-readable
    provenance/benchmark data (info_confidence_note, launch_notes,
    benchmark_*) that's valuable for a person deciding whether a model is
    ready to wire in, but has no business being read by run-time code. Only
    the fields below are meant to drive actual behavior -- if you need a
    new field here, add it deliberately, don't just dump the whole entry.
    """
    with open(path, "r") as f:
        catalog = yaml.safe_load(f)

    return {
        name: {
            "repo_id": entry.get("repo_id"),
            "filename": entry.get("filename"),
            # Machine-readable env vars this model NEEDS to run correctly
            # (empty dict = needs nothing extra). None specifically means
            # "ambiguous, multiple incompatible real deployments exist" --
            # see gr00t-n1.6's entry -- and callers must treat that as a
            # hard error, not silently guess a default.
            "launch_env": entry.get("launch_env"),
            "tokenizer_repo": entry.get("tokenizer_repo"),
            "max_state_dim": entry.get("max_state_dim"),
            "image_size": entry.get("image_size"),
            "camera_views": entry.get("camera_views"),
        }
        for name, entry in catalog.items()
    }
