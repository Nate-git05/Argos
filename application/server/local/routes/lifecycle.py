import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

from application.control.state import state
from application.server.local.routes import cli_commands


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.started_at = time.time()
    yield

    # Shutdown: release whatever hardware/processes are still held open
    # instead of leaving the arm powered mid-position, a camera handle
    # open, or the inference engine running as an orphan.
    if state.run is not None:
        state.run.stop.set()
        if state.run.inference_thread is not None:
            state.run.inference_thread.join(timeout=5)
        if state.run.pid_thread is not None:
            state.run.pid_thread.join(timeout=5)

    if state.engine is not None:
        state.engine.stop()

    if state.actuator is not None:
        state.actuator.close()

    for sensor in state.sensors.values():
        sensor.release()


@cli_commands.get("/health")
def health():
    return {"status": "ok", "uptime_s": round(time.time() - state.started_at, 1)}
