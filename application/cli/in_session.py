import typer

from application.cli import app
from application.cli.client import daemon_request


@app.command("status")
def status():
    """Show what's loaded, what's connected, and how long the daemon/run have been up."""
    data = daemon_request("GET", "/cli/status")

    typer.echo(f"daemon uptime: {data['daemon_uptime_s']}s")

    run = data["run"]
    if run["active"]:
        typer.secho(
            f"run: {run['model']} \"{run['instruction']}\" (uptime {run['uptime_s']}s)", fg=typer.colors.GREEN
        )
    else:
        typer.echo("run: none active")

    engine = data["engine"]
    if engine["running"]:
        typer.echo(f"engine: {engine['model']} (pid={engine['pid']}, bind={engine['bind_addr']})")
    else:
        typer.echo("engine: not running")

    typer.echo(f"actuator: {data['actuator']}" if data["actuator"] else "actuator: not connected")
    typer.echo(f"sensors: {data['sensors']}" if data["sensors"] else "sensors: none connected")


@app.command("logs")
def logs(
    source: str = typer.Option(None, help="Filter: 'engine' or 'run'. Omit to show both."),
    limit: int = typer.Option(50, help="Number of most-recent log lines to show."),
):
    """Show recent log lines from the inference engine and/or the active run."""
    params = {"limit": limit}
    if source:
        params["source"] = source

    data = daemon_request("GET", "/cli/logs", params=params)

    for key in [source] if source else ["engine", "run"]:
        lines = data.get(key)
        if lines is None:
            typer.echo(f"{key}: none")
            continue
        typer.secho(f"--- {key} ---", fg=typer.colors.CYAN)
        for line in lines:
            typer.echo(line)


@app.command("stop")
def stop():
    """Safely stop the active run: halts control, drives the arm home, tears down the engine."""
    data = daemon_request("POST", "/cli/stop")
    if data["home_reached"]:
        typer.secho("Stopped -- arm returned home.", fg=typer.colors.GREEN)
    else:
        typer.secho("Stopped, but the arm did not confirm reaching home position.", fg=typer.colors.YELLOW)
