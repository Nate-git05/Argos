import asyncio

import cv2
from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from application.control.pid import move_to_positions
from application.control.state import state
from application.server.local.config.config import ACTUATOR_HOME_POSITION, ACTUATOR_HOME_TIMEOUT_S
from application.server.local.routes import cli_commands

STREAM_FPS = 15


@cli_commands.websocket("/view/{view_name}")
async def view_sensor(websocket: WebSocket, view_name: str):
    if view_name not in state.sensors:
        await websocket.close(code=1008, reason=f"no connected camera for view {view_name!r}")
        return

    await websocket.accept()
    interval_s = 1 / STREAM_FPS

    try:
        while view_name in state.sensors:
            frame = state.sensors[view_name].get_latest_frame()
            if frame is not None:
                ok, buf = cv2.imencode(".jpg", frame)
                if ok:
                    await websocket.send_bytes(buf.tobytes())
            await asyncio.sleep(interval_s)
    except WebSocketDisconnect:
        pass


@cli_commands.post("/stop")
def stop_run():
    """Safe-stop: halts both workers, drives the arm to its home position,
    tears down the vla-server child process -- the daemon itself (this
    route included) keeps running the whole time."""
    if state.run is None:
        raise HTTPException(status_code=400, detail="no run is active")

    run_session = state.run
    run_session.stop.set()

    if run_session.inference_thread is not None:
        run_session.inference_thread.join(timeout=5)
    if run_session.pid_thread is not None:
        run_session.pid_thread.join(timeout=5)

    home_reached = False
    if state.actuator is not None:
        home_targets = [ACTUATOR_HOME_POSITION] * len(state.actuator.servo_ids)
        home_reached = move_to_positions(home_targets, timeout_s=ACTUATOR_HOME_TIMEOUT_S)

    if state.engine is not None:
        state.engine.stop()

    for sensor in state.sensors.values():
        sensor.pause_capture()

    state.run = None
    state.engine = None

    return {"stopped": True, "home_reached": home_reached}


@cli_commands.get("/logs")
def get_logs(source: str | None = None, limit: int = 50):
    if source == "engine":
        if state.engine is None:
            raise HTTPException(status_code=400, detail="no engine running")
        return {"engine": list(state.engine.logs)[-limit:]}

    if source == "run":
        if state.run is None:
            raise HTTPException(status_code=400, detail="no run active")
        return {"run": list(state.run.logs)[-limit:]}

    if source is not None:
        raise HTTPException(status_code=400, detail=f"unknown source {source!r}; expected 'engine' or 'run'")

    return {
        "engine": list(state.engine.logs)[-limit:] if state.engine is not None else None,
        "run": list(state.run.logs)[-limit:] if state.run is not None else None,
    }
