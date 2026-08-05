from pathlib import Path

from application.mcp import mcp

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_PATH = REPO_ROOT / "README.md"
MODELS_README_PATH = REPO_ROOT / "application" / "server" / "local" / "services" / "models" / "Readme.md"


@mcp.resource("argos://readme")
def readme() -> str:
    """Argos project README -- what it is and how the pieces fit together."""
    return README_PATH.read_text()


@mcp.resource("argos://models")
def model_catalog() -> str:
    """Full model catalog: architecture, benchmarks, hardware fit, and
    confidence notes for every model Argos knows about -- richer than the
    `list_models` tool's pulled/not-pulled summary. Static reference data;
    doesn't require the daemon to be running."""
    return MODELS_README_PATH.read_text()
