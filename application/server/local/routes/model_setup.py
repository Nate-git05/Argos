"""Model catalog + lifecycle routes: list what's available, pull weights,
and run a model end to end.

`run` is the one route in this whole daemon that does real work beyond a
single request/response -- it validates every precondition, spawns the
vla-server subprocess, loads the tokenizer, and then hands off to two
background worker threads (application/control/inference.py and
application/control/pid.py) that keep running long after this route
returns its HTTP response. Everything before that hand-off is written to
fail fast and cheap (cheapest checks first) so a bad request never gets as
far as spawning a process or downloading a tokenizer.
"""

import os
import subprocess
import threading

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
from application.control.inference import load_tokenizer, run_inference_worker
from application.control.pid import run_pid_worker
from application.control.state import EngineConnection, RunSession, state

console = Console()


def _is_pulled(entry: dict) -> bool:
    """Checks the actual weights file exists on disk rather than trusting
    any cached/remembered state -- the source of truth for "is this model
    pulled" is always the filesystem. Handles nested filenames correctly
    (e.g. bitvla's "libero_object/bitvla-libero-object.gguf") since it
    resolves the full relative path rather than comparing bare filenames
    against a flat directory listing, which was a real bug caught earlier."""
    filename = entry.get("filename")
    return bool(filename) and (MODELS_DIR / filename).is_file()


def _resolve_launch_config(entry: dict) -> tuple[str, dict]:
    """Turns a catalog entry into what subprocess.Popen actually needs:
    the resolved weights path and a real env dict. No per-model branching
    here -- launch_env in models.yaml is already clean, machine-readable
    data (deliberately restructured for exactly this reason: code should
    never need to special-case a specific model name to run it). The one
    thing this refuses to guess at is launch_env: null (currently only
    gr00t-n1.6, which has multiple incompatible real deployments) --
    that's a hard error, not a default to fall back on."""
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
    """Catalog + local pull status for every model, regardless of whether
    it's actually usable yet (missing tokenizer_repo, ambiguous
    launch_env, etc. don't hide a model from this list -- they surface as
    errors later, specifically when something tries to use that model,
    not here)."""
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
    """Downloads a model's weights straight into services/models/ (same
    directory models.yaml lives in), authenticated with the daemon's own
    HF token so gated repos work transparently once the account behind
    that token has accepted the relevant license."""
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
    """Validates every precondition (model pulled, actuator connected,
    the model's EXACT required camera views connected, no engine already
    running, the vla-server binary actually built), then spawns the
    engine, loads the tokenizer, and starts both background workers.
    Checks are ordered cheapest-first so a request that's going to fail
    does so before anything expensive (subprocess spawn, tokenizer
    download) happens."""
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

    # Must match the model's camera_views.keys EXACTLY, not just be "enough
    # cameras" -- the model was trained on a specific view ordering
    # (front vs. wrist, etc.), and connect_sensor's view_name is required
    # to be one of those exact key names for precisely this reason.
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
    tokenizer = load_tokenizer(entry)  # deliberately before spawning the engine, not after -- fail cheap first

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

    # Cameras were connected earlier (possibly long before this request)
    # with capture deliberately paused to avoid burning CPU/power while
    # idle -- this is the moment that actually turns capture on.
    for sensor in state.sensors.values():
        sensor.start_capture()

    # Thread handles are stored on RunSession itself so /stop can join
    # them later and know both loops have genuinely exited before tearing
    # down the engine/actuator underneath them.
    state.run.inference_thread = threading.Thread(target=run_inference_worker, args=(state.run, entry), daemon=True)
    state.run.pid_thread = threading.Thread(target=run_pid_worker, args=(state.run,), daemon=True)
    state.run.inference_thread.start()
    state.run.pid_thread.start()

    return {"model": model, "ckpt_path": ckpt_path, "bind_addr": ENGINE_BIND_ADDR, "pid": process.pid}
