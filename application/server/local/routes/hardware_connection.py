import base64

import cv2
import serial
import serial.tools.list_ports
from fastapi import HTTPException

from application.server.local.config.config import REQUIRED_CAMERA_VIEWS
from application.server.local.routes import cli_commands
from application.server.local.tools.state import ActuatorConnection, SensorConnection, state

ACTUATOR_BAUDRATE = 115200
ACTUATOR_TIMEOUT_S = 2
CAMERA_PROBE_LIMIT = 10


def _discover_actuator_ports() -> list[dict]:
    return [
        {"port": p.device, "description": p.description, "vid": p.vid, "pid": p.pid}
        for p in serial.tools.list_ports.comports()
    ]


@cli_commands.post("/connect/actuator")
def connect_actuator(port: str | None = None):
    if port is None:
        return {"ports": _discover_actuator_ports()}

    try:
        handle = serial.Serial(port, baudrate=ACTUATOR_BAUDRATE, timeout=ACTUATOR_TIMEOUT_S)
    except serial.SerialException as e:
        raise HTTPException(status_code=502, detail=f"failed to open {port!r}: {e}")

    if not handle.is_open:
        raise HTTPException(status_code=502, detail=f"port {port!r} did not open")

    if state.actuator is not None:
        state.actuator.handle.close()

    state.actuator = ActuatorConnection(port=port, handle=handle)
    return {"port": port, "connected": True}


def _discover_cameras() -> list[dict]:
    found = []
    for index in range(CAMERA_PROBE_LIMIT):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ok, frame = cap.read()
            preview_jpeg_b64 = None
            if ok:
                _, buf = cv2.imencode(".jpg", frame)
                preview_jpeg_b64 = base64.b64encode(buf).decode()
            found.append({"index": index, "preview_jpeg_b64": preview_jpeg_b64})
        cap.release()
    return found


@cli_commands.post("/connect/sensor")
def connect_sensor(index: int | None = None, view_name: str | None = None):
    if index is None or view_name is None:
        return {
            "cameras": _discover_cameras(),
            "required_views": REQUIRED_CAMERA_VIEWS,
            "connected_views": list(state.sensors.keys()),
        }

    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap.release()
        raise HTTPException(status_code=502, detail=f"camera index {index} did not open")

    existing = state.sensors.get(view_name)
    if existing is not None:
        existing.release()

    state.sensors[view_name] = SensorConnection(index=index, view_name=view_name, handle=cap)

    missing = max(REQUIRED_CAMERA_VIEWS - len(state.sensors), 0)
    return {
        "index": index,
        "view_name": view_name,
        "connected": True,
        "connected_views": list(state.sensors.keys()),
        "required_views": REQUIRED_CAMERA_VIEWS,
        "missing": missing,
    }
