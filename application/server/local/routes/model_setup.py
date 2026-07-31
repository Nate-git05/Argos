import os
import subprocess

from fastapi import HTTPException
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError
from rich.console import Console

from application.server.local.config.config import (
    ENGINE_BIND_ADDR,
    HF_CLIENT,
    MODELS_DIR,
    VLA_SERVER_BINARY,
    load_model_catalog,
)
from application.server.local.routes import cli_commands
from application.control.inference import load_tokenizer
from application.control.state import EngineConnection, RunSession, state

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
def run_model(model: str, instruction: str):
    if not instruction or not instruction.strip():
        raise HTTPException(status_code=400, detail="instruction is required")

    catalog = load_model_catalog()

    if model not in catalog:
        raise HTTPException(status_code=404, detail=f"unknown model: {model}")

    entry = catalog[model]

    if not _is_pulled(entry):
        raise HTTPException(status_code=400, detail=f"model {model!r} has not been pulled yet")

    if state.actuator is None:
        raise HTTPException(status_code=400, detail="no actuator connected")

    required_views = (entry.get("camera_views") or {}).get("keys") or []
    missing_views = [v for v in required_views if v not in state.sensors]
    if missing_views:
        raise HTTPException(
            status_code=400,
            detail=(
                f"missing required camera view(s): {missing_views}. "
                f"Connect each with connect_sensor(view_name=<one of {required_views}>)"
            ),
        )

    if state.engine is not None and state.engine.process.poll() is None:
        raise HTTPException(
            status_code=409,
            detail=f"engine already running (model={state.engine.model}); stop it first",
        )

    if not VLA_SERVER_BINARY.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"vla-server binary not found at {VLA_SERVER_BINARY} -- run install/install.sh first",
        )

    ckpt_path, env = _resolve_launch_config(entry)
    tokenizer = load_tokenizer(entry)  # fail before spawning the engine, not after

    process = subprocess.Popen(
        [str(VLA_SERVER_BINARY), ckpt_path, "--bind", ENGINE_BIND_ADDR],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    engine = EngineConnection(process=process, model=model, bind_addr=ENGINE_BIND_ADDR)

    if not engine.wait_until_ready(timeout_s=60.0):
        exit_code = process.poll()
        last_logs = list(engine.logs)[-10:]
        engine.stop()
        raise HTTPException(
            status_code=500,
            detail=f"vla-server did not become ready (exit_code={exit_code}). Last logs: {last_logs}",
        )

    state.engine = engine
    state.run = RunSession(
        model=model,
        instruction=instruction,
        tokenizer=tokenizer,
        max_state_dim=entry["max_state_dim"],
    )

    for sensor in state.sensors.values():
        sensor.start_capture()

    return {"model": model, "ckpt_path": ckpt_path, "bind_addr": ENGINE_BIND_ADDR, "pid": process.pid}
