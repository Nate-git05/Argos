from application.cli import app
import application.cli.model_setup  # noqa: F401
import application.cli.hardware_connection  # noqa: F401

if __name__ == "__main__":
    app()
