from fastapi import FastAPI

import application.server.local.routes.hardware_connection  # noqa: F401
import application.server.local.routes.in_session  # noqa: F401
import application.server.local.routes.model_setup  # noqa: F401
from application.server.local.routes import cli_commands
from application.server.local.routes.lifecycle import lifespan

app = FastAPI(title="Argos Daemon", lifespan=lifespan)
app.include_router(cli_commands)
