"""Actuator and sensor connection routes.

Two separate routes, not one shared route with a type parameter --
actuators and sensors have entirely different discovery mechanisms
(pyserial port enumeration vs. OpenCV camera probing), different
protocols, and different verification steps, so forcing them through one
generic endpoint would just mean branching on type internally anyway.
"""

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
    """Real device metadata via pyserial (vendor/product ID, description),
    not just filenames from a directory listing -- lets a caller
    distinguish "USB-Serial Controller" from a Bluetooth or virtual port
    with a similar-looking /dev entry."""
    return [
        {"port": p.device, "description": p.description, "vid": p.vid, "pid": p.pid}
        for p in serial.tools.list_ports.comports()
    ]


@cli_commands.post("/connect/actuator")
def connect_actuator(port: str | None = None, servo_ids: list[int] | None = Query(default=None)):
    """No port -> discovery. With a port -> opens it and PINGS every
    requested servo ID as the actual handshake, not just checking the
    port opened (a port can open successfully against a device that isn't
    a Feetech servo at all, or a servo that's powered off). servo_ids is
    caller-supplied so a non-default arm configuration can be connected
    without touching config.py; DEFAULT_SERVO_IDS is only the fallback
    when the caller doesn't specify.

    Note the `Query(default=None)` on servo_ids isn't decorative -- this
    FastAPI version silently drops repeated list-typed query params
    (?servo_ids=1&servo_ids=2) into a bare None without it, confirmed by
    testing; a plain `= None` default looks identical but is a real bug.
    """
    if port is None:
        return {"ports": _discover_actuator_ports()}

    ids = servo_ids or DEFAULT_SERVO_IDS

    port_handler = scs.PortHandler(port)
    try:
        port_opened = port_handler.openPort()
    except serial.SerialException as e:
        # openPort() raises rather than returning False for a genuinely
        # bad port (nonexistent, permission denied, already in use) --
        # confirmed by testing against a real bad path, not assumed.
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

    # Only one actuator connection per session for V1 -- replacing it
    # closes whatever was there first rather than leaking the old handle.
    if state.actuator is not None:
        state.actuator.close()

    state.actuator = ActuatorConnection(
        port=port,
        port_handler=port_handler,
        packet_handler=packet_handler,
        servo_ids=[s["id"] for s in responded],  # only the IDs that actually answered, not the full requested list
    )

    return {
        "port": port,
        "connected": True,
        "responded": responded,
        "unresponsive": unresponsive,
    }


def _discover_cameras() -> list[dict]:
    """Probes indices 0..CAMERA_PROBE_LIMIT and grabs one frame from each
    that opens, so the caller gets a visual preview to distinguish
    cameras by, not just a bare index number. Every capture is released
    immediately after probing -- discovery doesn't hold any camera open,
    only an actual connect_sensor call (with index + view_name) does."""
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
    """No index/view_name -> discovery. With both -> connects that camera
    under view_name, which is required to exactly match one of the
    eventual run target model's camera_views.keys (enforced later, in
    run_model) -- that's what makes the mapping from "this physical
    camera" to "this slot in the model's expected input order" exact
    rather than a guess based on connection order.

    isOpened() alone isn't sufficient verification -- a camera can report
    open while never actually producing frames (permissions, driver
    quirks, wrong backend). Grabbing and returning a real test frame here
    is the actual proof it works, and the same frame doubles as visual
    confirmation for whoever's connecting it.
    """
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
        existing.release()  # stops its background thread and releases the old capture before replacing it

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
