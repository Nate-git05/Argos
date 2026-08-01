"""Routes meant to be used while a run is active: watching the live camera
feed and stopping the session. Both read/write the same DaemonState
singleton everything else in the daemon shares -- there's no separate
"session" concept beyond state.run being non-None.
"""

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
    """Streams raw JPEG frames over a websocket at STREAM_FPS. Reads only
    from SensorConnection's cached latest-frame -- never touches the
    camera handle directly -- so this can run concurrently with the
    inference worker also reading frames, with no contention between them.
    Closes with 1008 (policy violation) if the view isn't connected,
    rather than accepting the connection and then having nothing to send.
    """
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
    """Safe-stop, in order: signal both workers to stop and wait for them
    to actually exit (not just fire-and-forget -- joining first means
    neither loop can still be mid-iteration, reading/writing the actuator,
    when the code below starts moving it to home and then tearing down
    the engine underneath them), drive the arm to its home position,
    tear down the vla-server subprocess, pause camera capture back to
    idle, and clear run/engine state so a fresh `run` can start cleanly
    afterward. The daemon process itself (this route included) is never
    touched -- /stop ends the ACTIVE RUN, not the daemon.
    """
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
        sensor.pause_capture()  # back to idle -- connections stay open, but stop burning CPU decoding frames

    state.run = None
    state.engine = None

    return {"stopped": True, "home_reached": home_reached}
