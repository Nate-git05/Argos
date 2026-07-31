import typer

from application.cli import app
from application.cli.client import daemon_request


@app.command("list")
def list_models():
    """List the model catalog and show which ones are already pulled locally."""
    data = daemon_request("GET", "/cli/list")

    if "message" in data:
        typer.echo(data["message"])

    for name, info in data["models"].items():
        mark = "[pulled]" if info["pulled"] else "[not pulled]"
        typer.echo(f"{name:15s} {mark}")


@app.command("pull")
def pull_model(model: str = typer.Argument(..., help="Model name from the catalog, e.g. 'smolvla'.")):
    """Download a model's weights from Hugging Face into the local cache."""
    data = daemon_request("POST", f"/cli/pull/{model}")
    typer.secho(f"Pulled {data['model']} -> {data['path']}", fg=typer.colors.GREEN)


@app.command("run")
def run_model(
    model: str = typer.Argument(..., help="Model name to run, e.g. 'smolvla'."),
    instruction: str = typer.Argument(..., help="Natural-language task instruction for the robot."),
):
    """Start running a model: spawns the inference engine and begins the control loop."""
    data = daemon_request("POST", "/cli/run", params={"model": model, "instruction": instruction})
    typer.secho(f"Running {data['model']} (pid={data['pid']}, bind={data['bind_addr']})", fg=typer.colors.GREEN)
