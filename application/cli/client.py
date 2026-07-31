import httpx
import typer

DAEMON_BASE_URL = "http://127.0.0.1:8000"


def daemon_request(method: str, path: str, **kwargs) -> dict:
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
