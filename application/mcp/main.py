from application.mcp import mcp
import application.mcp.docs  # noqa: F401
import application.mcp.hardware_connection  # noqa: F401
import application.mcp.in_session  # noqa: F401
import application.mcp.model_setup  # noqa: F401


def main():
    mcp.run()


if __name__ == "__main__":
    main()
