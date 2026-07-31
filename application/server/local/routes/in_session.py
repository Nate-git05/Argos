import asyncio

import cv2
from fastapi import WebSocket, WebSocketDisconnect

from application.server.local.routes import cli_commands
from application.control.state import state

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
