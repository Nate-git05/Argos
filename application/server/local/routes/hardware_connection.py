import base64

import cv2
import scservo_sdk as scs
import serial
import serial.tools.list_ports
from fastapi import HTTPException, Query

from application.server.local.config.config import (
    ACTUATOR_BAUDRATE,
    ACTUATOR_PROTOCOL_END,
    DEFAULT_SERVO_IDS,
    REQUIRED_CAMERA_VIEWS,
)
from application.server.local.routes import cli_commands
from application.control.state import ActuatorConnection, SensorConnection, state

CAMERA_PROBE_LIMIT = 10


def _discover_actuator_ports() -> list[dict]:
    return [
        {"port": p.device, "description": p.description, "vid": p.vid, "pid": p.pid}
        for p in serial.tools.list_ports.comports()
    ]


@cli_commands.post("/connect/actuator")
def connect_actuator(port: str | None = None, servo_ids: list[int] | None = Query(default=None)):
    if port is None:
        return {"ports": _discover_actuator_ports()}

    ids = servo_ids or DEFAULT_SERVO_IDS

    port_handler = scs.PortHandler(port)
    try:
        port_opened = port_handler.openPort()
    except serial.SerialException as e:
        raise HTTPException(status_code=502, detail=f"failed to open {port!r}: {e}")

    if not port_opened:
        raise HTTPException(status_code=502, detail=f"failed to open {port!r}")

    if not port_handler.setBaudRate(ACTUATOR_BAUDRATE):
        port_handler.closePort()
        raise HTTPException(status_code=502, detail=f"failed to set baud rate on {port!r}")

    packet_handler = scs.PacketHandler(ACTUATOR_PROTOCOL_END)

    responded = []
    unresponsive = []
    for servo_id in ids:
        model_number, result, _error = packet_handler.ping(port_handler, servo_id)
        if result == scs.COMM_SUCCESS:
            responded.append({"id": servo_id, "model_number": model_number})
        else:
            unresponsive.append(servo_id)

    if not responded:
        port_handler.closePort()
        raise HTTPException(
            status_code=502,
            detail=f"no servos responded on {port!r} (tried ids {ids})",
        )

    if state.actuator is not None:
        state.actuator.close()

    state.actuator = ActuatorConnection(
        port=port,
        port_handler=port_handler,
        packet_handler=packet_handler,
        servo_ids=[s["id"] for s in responded],
    )

    return {
        "port": port,
        "connected": True,
        "responded": responded,
        "unresponsive": unresponsive,
    }


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

    ok, test_frame = cap.read()
    if not ok:
        cap.release()
        raise HTTPException(
            status_code=502,
            detail=f"camera index {index} opened but failed to capture a test frame",
        )
    _, buf = cv2.imencode(".jpg", test_frame)
    test_frame_jpeg_b64 = base64.b64encode(buf).decode()

    existing = state.sensors.get(view_name)
    if existing is not None:
        existing.release()

    state.sensors[view_name] = SensorConnection(index=index, view_name=view_name, handle=cap)

    missing = max(REQUIRED_CAMERA_VIEWS - len(state.sensors), 0)
    return {
        "index": index,
        "view_name": view_name,
        "connected": True,
        "test_frame_jpeg_b64": test_frame_jpeg_b64,
        "connected_views": list(state.sensors.keys()),
        "required_views": REQUIRED_CAMERA_VIEWS,
        "missing": missing,
    }


def _actuator_device() -> dict | None:
    if state.actuator is None:
        return None
    return {"port": state.actuator.port, "servo_ids": state.actuator.servo_ids, "connected": True}


def _sensor_devices() -> list[dict]:
    return [
        {"index": s.index, "view_name": s.view_name, "method": s.method, "connected": True}
        for s in state.sensors.values()
    ]


@cli_commands.get("/devices")
def list_devices(kind: str | None = None):
    if kind == "actuator":
        return {"actuator": _actuator_device()}
    if kind == "sensor":
        return {"sensors": _sensor_devices()}
    if kind is not None:
        raise HTTPException(status_code=400, detail=f"unknown kind {kind!r}; expected 'actuator' or 'sensor'")

    return {"actuator": _actuator_device(), "sensors": _sensor_devices()}


@cli_commands.get("/devices/actuators")
def list_actuator_devices():
    return {"actuator": _actuator_device()}


@cli_commands.get("/devices/sensors")
def list_sensor_devices():
    return {"sensors": _sensor_devices()}
