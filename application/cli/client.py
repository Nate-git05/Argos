"""The CLI's only path to the daemon -- every command in model_setup.py
and hardware_connection.py goes through daemon_request() rather than
talking to application.control.state or the daemon's routes directly.
The CLI and the daemon are separate processes (the CLI is a short-lived
`python -m` invocation, the daemon is the long-running systemd service);
HTTP is the only thing connecting them.
"""

import httpx
import typer

DAEMON_BASE_URL = "http://127.0.0.1:8000"


def daemon_request(method: str, path: str, **kwargs) -> dict:
    """Turns the two ways a daemon call can fail into a clean message +
    non-zero exit instead of a raw exception traceback: the daemon isn't
    running at all (ConnectError -- most common failure mode for a fresh
    install, points the user at the fix), or the daemon is up but
    rejected the request (surfaces its actual HTTPException detail rather
    than a generic "request failed")."""
    try:
        resp = httpx.request(method, f"{DAEMON_BASE_URL}{path}", timeout=90.0, **kwargs)
    except httpx.ConnectError:
        typer.secho(
            "Could not reach the Argos daemon -- is it running? Try: sudo systemctl start argos",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        typer.secho(f"Error: {detail}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    return resp.json()
