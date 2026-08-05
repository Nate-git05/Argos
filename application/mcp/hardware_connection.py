from application.mcp import mcp
from application.mcp.client import daemon_request


@mcp.tool()
def connect_actuator(port: str | None = None, servo_ids: list[int] | None = None) -> dict:
    """Connect the actuator (robot arm) over the Feetech serial protocol.

    Call with no arguments first to discover available serial ports. Then
    call again with `port` set to one of those (e.g. "/dev/ttyUSB0") to
    actually connect. `servo_ids` restricts which servo IDs are pinged --
    omit it to use the arm's default servo set.
    """
    params = {}
    if port:
        params["port"] = port
    if servo_ids:
        params["servo_ids"] = servo_ids

    return daemon_request("POST", "/cli/connect/actuator", params=params)


@mcp.tool()
def connect_sensor(index: int | None = None, view_name: str | None = None) -> dict:
    """Connect a camera under a named view.

    Call with no arguments first to discover available cameras (returns a
    preview frame per camera). Then call again with `index` (the camera
    index) and `view_name` (must match the target model's expected
    camera_views key, e.g. "observation.images.image") to connect it.
    """
    params = {}
    if index is not None:
        params["index"] = index
    if view_name:
        params["view_name"] = view_name

    return daemon_request("POST", "/cli/connect/sensor", params=params)


@mcp.tool()
def devices(kind: str | None = None) -> dict:
    """List connected actuator and sensor devices.

    `kind`, if given, filters to just "actuator" or "sensor" -- omit it to
    get both.
    """
    params = {"kind": kind} if kind else {}
    return daemon_request("GET", "/cli/devices", params=params)
