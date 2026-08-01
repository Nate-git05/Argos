"""One shared router, imported by every route module in this package.
Each module attaches its own endpoints directly onto this same instance
(@cli_commands.get/post/websocket) rather than defining a separate
APIRouter per file and combining them later -- same pattern as
DaemonState in application/control/state.py: one shared object multiple
files write onto, instead of each file owning an isolated piece that
has to be stitched together afterward.
"""

from fastapi import APIRouter

cli_commands = APIRouter(prefix="/cli")
