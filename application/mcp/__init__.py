from mcp.server import MCPServer

mcp = MCPServer(
    "argos",
    instructions=(
        "Tools for connecting hardware and running VLA models on an Argos robot. "
        "This server is a thin client of the Argos daemon (application/server/local) -- "
        "the daemon must already be running (`sudo systemctl start argos` or "
        "`uvicorn application.server.local.app:app`) for any tool here to work. "
        "Typical order: connect_actuator -> connect_sensor (once per required camera view) "
        "-> pull_model (if not already pulled) -> run_model. Use status/devices to check "
        "what's connected before running, and stop to safely halt an active run."
    ),
)
