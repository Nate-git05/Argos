"""The single shared Typer app every CLI command file attaches its
commands to -- same pattern as the daemon's cli_commands router
(application/server/local/routes/__init__.py): one instance, multiple
files register onto it via import side effects (see main.py)."""

import typer

app = typer.Typer(help="Argos -- run and connect VLA models on your robot.")
