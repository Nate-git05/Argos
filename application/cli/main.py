from application.cli import app
import application.cli.model_setup  # noqa: F401
import application.cli.hardware_connection  # noqa: F401


def main():
    app()


if __name__ == "__main__":
    main()
