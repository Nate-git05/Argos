from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import application.server.web.routes.register  # noqa: F401
from application.server.web.config.config import ALLOWED_ORIGINS
from application.server.web.routes import register_router

app = FastAPI(title="Argos Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

app.include_router(register_router)
