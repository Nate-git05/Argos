import typer

from application.cli import app
from application.cli.client import daemon_request

connect_app = typer.Typer(help="Connect actuators and sensors.")
app.add_typer(connect_app, name="connect")


@connect_app.command("actuator")
def connect_actuator(
    port: str = typer.Option(None, help="Serial port, e.g. /dev/ttyUSB0. Omit to list available ports."),
    servo_id: list[int] = typer.Option(
        None, help="Servo ID to ping. Repeatable. Omit for the default set."
    ),
):
    """Connect the actuator over the Feetech protocol, or list available ports if --port is omitted."""
    params = {}
    if port:
        params["port"] = port
    if servo_id:
        params["servo_ids"] = servo_id

    data = daemon_request("POST", "/cli/connect/actuator", params=params)

    if port:
        typer.secho(
            f"Connected {data['port']}: responded={data['responded']} unresponsive={data['unresponsive']}",
            fg=typer.colors.GREEN,
        )
    else:
        for p in data["ports"]:
            typer.echo(f"{p['port']:20s} {p['description']}")


@connect_app.command("sensor")
def connect_sensor(
    index: int = typer.Option(None, help="Camera index. Omit to discover available cameras."),
    view: str = typer.Option(None, help="View name -- must match the model's expected camera_views key."),
):
    """Connect a camera under a named view, or discover available cameras if --index is omitted."""
    params = {}
    if index is not None:
        params["index"] = index
    if view:
        params["view_name"] = view

    data = daemon_request("POST", "/cli/connect/sensor", params=params)

    if index is not None:
        typer.secho(f"Connected camera {data['index']} as {data['view_name']!r}", fg=typer.colors.GREEN)
    else:
        for cam in data["cameras"]:
            typer.echo(f"index {cam['index']}")


@app.command("devices")
def devices(kind: str = typer.Option(None, help="Filter: 'actuator' or 'sensor'.")):
    """List connected actuator and sensor devices."""
    params = {"kind": kind} if kind else {}
    data = daemon_request("GET", "/cli/devices", params=params)
    typer.echo(data)
