from pathlib import Path

from fastapi import HTTPException
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError
from rich.console import Console

from application.server.local.config.config import HF_CLIENT, MODELS_DIR, load_model_catalog
from application.server.local.routes import cli_commands

console = Console()


@cli_commands.get("/list")
def list_models():
    catalog = load_model_catalog()
    pulled_files = {p.name for p in Path(MODELS_DIR).glob("*") if p.is_file()}

    models = {
        name: {
            "repo_id": entry["repo_id"],
            "filename": entry["filename"],
            "pulled": bool(entry["filename"]) and entry["filename"] in pulled_files,
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
