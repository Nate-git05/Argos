import os

from fastapi import HTTPException
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError
from rich.console import Console

from application.server.local.config.config import (
    HF_CLIENT,
    MODELS_DIR,
    REQUIRED_CAMERA_VIEWS,
    load_model_catalog,
)
from application.server.local.routes import cli_commands
from application.server.local.tools.state import state

console = Console()


def _is_pulled(entry: dict) -> bool:
    filename = entry.get("filename")
    return bool(filename) and (MODELS_DIR / filename).is_file()


def _resolve_launch_config(entry: dict) -> tuple[str, dict]:
    launch_env = entry.get("launch_env")
    if launch_env is None:
        raise HTTPException(
            status_code=400,
            detail="this model has no single resolved launch configuration yet (ambiguous deployment variants)",
        )

    ckpt_path = str(MODELS_DIR / entry["filename"])
    env = {**os.environ, **launch_env}
    return ckpt_path, env


@cli_commands.get("/list")
def list_models():
    catalog = load_model_catalog()

    models = {
        name: {
            "repo_id": entry["repo_id"],
            "filename": entry["filename"],
            "pulled": _is_pulled(entry),
        }
        for name, entry in catalog.items()
    }

    if not any(m["pulled"] for m in models.values()):
        return {"message": "No models have been pulled yet.", "models": models}

    return {"models": models}


@cli_commands.post("/pull/{name}")
def pull_model(name: str):
    catalog = load_model_catalog()

    if name not in catalog:
        raise HTTPException(status_code=404, detail=f"unknown model: {name}")

    entry = catalog[name]
    filename = entry["filename"]
    if not filename:
        raise HTTPException(
            status_code=400,
            detail=f"model {name!r} has no filename set in the catalog yet",
        )

    try:
        with console.status(f"Pulling {name} ({filename})..."):
            path = hf_hub_download(
                repo_id=entry["repo_id"],
                filename=filename,
                local_dir=MODELS_DIR,
                token=HF_CLIENT.token,
            )
    except HfHubHTTPError as e:
        console.print(f"[red]failed[/red] {name}: {e}")
        raise HTTPException(status_code=502, detail=f"failed to pull {name!r} from the Hub: {e}")

    console.print(f"[green]done[/green] {name} -> {path}")
    return {"model": name, "path": path}


@cli_commands.post("/run")
def run_model(model: str):
    catalog = load_model_catalog()

    if model not in catalog:
        raise HTTPException(status_code=404, detail=f"unknown model: {model}")

    entry = catalog[model]

    if not _is_pulled(entry):
        raise HTTPException(status_code=400, detail=f"model {model!r} has not been pulled yet")

    if state.actuator is None:
        raise HTTPException(status_code=400, detail="no actuator connected")

    if len(state.sensors) < REQUIRED_CAMERA_VIEWS:
        raise HTTPException(
            status_code=400,
            detail=f"only {len(state.sensors)}/{REQUIRED_CAMERA_VIEWS} camera views connected",
        )

    ckpt_path, env = _resolve_launch_config(entry)

    for sensor in state.sensors.values():
        sensor.start_capture()

    return {"model": model, "ckpt_path": ckpt_path, "env_overrides": catalog[model].get("launch_env")}
