import httpx

DAEMON_BASE_URL = "http://127.0.0.1:8000"


class DaemonError(Exception):
    """Raised when the Argos daemon is unreachable or returns an error response.
    Left uncaught, MCP surfaces this to the caller as a tool error."""


def daemon_request(method: str, path: str, **kwargs) -> dict:
    try:
        resp = httpx.request(method, f"{DAEMON_BASE_URL}{path}", timeout=90.0, **kwargs)
    except httpx.ConnectError as e:
        raise DaemonError(
            "Could not reach the Argos daemon -- is it running? Try: sudo systemctl start argos"
        ) from e

    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        raise DaemonError(f"Argos daemon error ({resp.status_code}): {detail}")

    return resp.json()
