from application.mcp import mcp
from application.mcp.client import daemon_request

# NOTE: `run_model` is deliberately NOT exposed here. Everything in this
# package is setup/inspection only -- it never starts the control loop that
# actually drives the arm. Starting a run is left to the user, via the CLI
# (`argos run <model> "<instruction>"`).


@mcp.tool()
def list_models() -> dict:
    """List the model catalog and show which ones are already pulled locally."""
    return daemon_request("GET", "/cli/list")


@mcp.tool()
def pull_model(model: str) -> dict:
    """Download a model's weights from Hugging Face into the local cache."""
    return daemon_request("POST", f"/cli/pull/{model}")
