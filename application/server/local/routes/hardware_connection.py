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


#function discovers all ports conncted to computer 
def _discover_actuator_ports() -> list[dict]:
    return [
        {"port": p.device, "description": p.description, "vid": p.vid, "pid": p.pid}
        for p in serial.tools.list_ports.comports()
    ] #returns a list of dictionsries containing port details 


#route to connect the actuator port to the jetson 
@cli_commands.post("/connect/actuator")
def connect_actuator(port: str | None = None, servo_ids: list[int] | None = Query(default=None)):
    #if no port returns dicsovered ports connected to computer 
    if port is None:
        return {"ports": _discover_actuator_ports()}

    #servo ids set as user entry or default value
    ids = servo_ids or DEFAULT_SERVO_IDS #servos -> motors that appluy force to the joints 

    port_handler = scs.PortHandler(port) #connects to passed port in request 

    #try/except block for opening the port handler
    try:
        port_opened = port_handler.openPort()
    except serial.SerialException as e:
        raise HTTPException(status_code=502, detail=f"failed to open {port!r}: {e}")

    if not port_opened:
        raise HTTPException(status_code=502, detail=f"failed to open {port!r}")

    #setting the baud rate -> rate which data is sent between jetson and servo
    if not port_handler.setBaudRate(ACTUATOR_BAUDRATE):
        port_handler.closePort()
        raise HTTPException(status_code=502, detail=f"failed to set baud rate on {port!r}")

    packet_handler = scs.PacketHandler(ACTUATOR_PROTOCOL_END) #packet for communication between servo and jetson

    responded = []
    unresponsive = []
    for servo_id in ids:
        """
        Iterating through the passed or defaulted servo ids 
        send over request to servos for ping with id passed -> if ping response == success append to lst
        if not append to unresponsive lst
        """
        model_number, result, _error = packet_handler.ping(port_handler, servo_id)
        if result == scs.COMM_SUCCESS:
            responded.append({"id": servo_id, "model_number": model_number})
        else:
            unresponsive.append(servo_id)

    #condition if no servo responded -> raise error and close the port handler
    if not responded:
        port_handler.closePort()
        raise HTTPException(
            status_code=502,
            detail=f"no servos responded on {port!r} (tried ids {ids})",
        )

    #condition to close connection to already connected actuator
    if state.actuator is not None:
        state.actuator.close()

    #creating new connection to actuator -> holds port, port handler, packet handler, ids for servo connected 
    state.actuator = ActuatorConnection(
        port=port,
        port_handler=port_handler,
        packet_handler=packet_handler,
        servo_ids=[s["id"] for s in responded],
    )

    #returning the connection details to the client in the command line 
    return {
        "port": port,
        "connected": True,
        "responded": responded,
        "unresponsive": unresponsive,
    }


#Helper function to discover the cameras connected to the actuator 
def _discover_cameras() -> list[dict]:
    found = []
    """
    Iterating through possble number of cameras that could be connected 
    creates video capture instance -. streams image from cap 
    checks if frame is read succesfully -> if so compress and append to found lst
    release the cap and return found lst 
    """
    for index in range(CAMERA_PROBE_LIMIT):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ok, frame = cap.read()
            preview_jpeg_b64 = None
            if ok:
                _, buf = cv2.imencode(".jpg", frame) #encodes the img to jpg 
                preview_jpeg_b64 = base64.b64encode(buf).decode()
            found.append({"index": index, "preview_jpeg_b64": preview_jpeg_b64})
        cap.release()
    return found


#route to connect the usb camera -> only sensor type to connect right now 
@cli_commands.post("/connect/sensor")
def connect_sensor(index: int | None = None, view_name: str | None = None):
    #if no index or view name -> returns any discoverd cameras connected to the computer 
    if index is None or view_name is None:
        return {
            "cameras": _discover_cameras(),
            "required_views": REQUIRED_CAMERA_VIEWS,
            "connected_views": list(state.sensors.keys()),
        }

    cap = cv2.VideoCapture(index) #connects the camera by the index 
    if not cap.isOpened():
        #if cap can't be opened -> release video capture and raise error 
        cap.release()
        raise HTTPException(status_code=502, detail=f"camera index {index} did not open")

    ok, test_frame = cap.read()  #testing the camera connected -> reading frame 
    if not ok:
        #if frame can't be read -> close the cap and raise error 
        cap.release()
        raise HTTPException(
            status_code=502,
            detail=f"camera index {index} opened but failed to capture a test frame",
        )

    """
    Frame was read successfully -> encode as jpg 
    then encode the buffer into base64 string 
    """
    _, buf = cv2.imencode(".jpg", test_frame)
    test_frame_jpeg_b64 = base64.b64encode(buf).decode()

    existing = state.sensors.get(view_name) #retrieving possible connection at the sesnsor view name 
    #if connection exits -> release the connection 
    if existing is not None:
        existing.release()

    #creating the new sensor connection at the view name -> holds index, name, and handle for the sensor 
    state.sensors[view_name] = SensorConnection(index=index, view_name=view_name, handle=cap)

    missing = max(REQUIRED_CAMERA_VIEWS - len(state.sensors), 0) #retrieving how many views still need to be connected 
    return {
        "index": index,
        "view_name": view_name,
        "connected": True,
        "test_frame_jpeg_b64": test_frame_jpeg_b64,
        "connected_views": list(state.sensors.keys()),
        "required_views": REQUIRED_CAMERA_VIEWS,
        "missing": missing,
    }

#helper fucntion to return the dict of the actuator connected
def _actuator_device() -> dict | None:
    if state.actuator is None:
        return None
    return {"port": state.actuator.port, "servo_ids": state.actuator.servo_ids, "connected": True}


#helper fucntion to return the list of sensors connected(right now only camera sensor)
def _sensor_devices() -> list[dict]:
    return [
        {"index": s.index, "view_name": s.view_name, "method": s.method, "connected": True}
        for s in state.sensors.values()
    ]


@cli_commands.get("/devices")
def list_devices(kind: str | None = None):
    #hit case -> for specific kind of device requested 
    if kind == "actuator":
        return {"actuator": _actuator_device()}
    if kind == "sensor":
        return {"sensors": _sensor_devices()}
    #case for unknown kind -> raises exception
    if kind is not None:
        raise HTTPException(status_code=400, detail=f"unknown kind {kind!r}; expected 'actuator' or 'sensor'")

    #if neither -> returns both sensor and actuators connected 
    return {"actuator": _actuator_device(), "sensors": _sensor_devices()}

#route for the subcommand for retrieving the actuator connected 
@cli_commands.get("/devices/actuators")
def list_actuator_devices():
    return {"actuator": _actuator_device()}


#route for subcommand to return the connected cameras 
@cli_commands.get("/devices/sensors")
def list_sensor_devices():
    return {"sensors": _sensor_devices()}
