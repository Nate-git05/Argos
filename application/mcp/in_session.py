from application.mcp import mcp
from application.mcp.client import daemon_request


@mcp.tool()
def status() -> dict:
    """Show what's loaded, what's connected, and how long the daemon/run have been up."""
    return daemon_request("GET", "/cli/status")


@mcp.tool()
def logs(source: str | None = None, limit: int = 50) -> dict:
    """Show recent log lines from the inference engine and/or the active run.

    `source`, if given, filters to just "engine" or "run" -- omit it to get both.
    """
    params = {"limit": limit}
    if source:
        params["source"] = source
    return daemon_request("GET", "/cli/logs", params=params)


@mcp.tool()
def stop() -> dict:
    """Safely stop the active run: halts control, drives the arm home, tears
    down the inference engine. This is the one tool here that moves the arm
    -- it only ever drives it to a fixed home position as part of shutting
    a run down safely, never as part of starting or steering one."""
    return daemon_request("POST", "/cli/stop")
