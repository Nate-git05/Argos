"""The daemon's actual entrypoint -- what the systemd service and every
CLI command talk to over HTTP. `uvicorn application.server.local.app:app`
is the real invocation (see install/argos.service.template).

Each route module registers its endpoints onto the shared `cli_commands`
router purely as an import side effect (the @cli_commands.get/post
decorators run at module import time) -- importing them here for that
side effect, even though nothing in this file calls into them directly,
is what actually wires every route up. Forgetting one of these imports
means its routes silently don't exist; there's no other registration step.
"""

from fastapi import FastAPI

import application.server.local.routes.hardware_connection  # noqa: F401
import application.server.local.routes.in_session  # noqa: F401
import application.server.local.routes.lifecycle  # noqa: F401
import application.server.local.routes.model_setup  # noqa: F401
from application.server.local.routes import cli_commands

app = FastAPI(title="Argos Daemon")
app.include_router(cli_commands)
