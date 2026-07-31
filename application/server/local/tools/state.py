import threading
from dataclasses import dataclass, field

import cv2
import numpy as np
import serial


@dataclass
class ActuatorConnection:
    port: str
    handle: serial.Serial


class SensorConnection:
    def __init__(self, index: int, view_name: str, handle: cv2.VideoCapture, method: str = "usb"):
        self.index = index
        self.view_name = view_name
        self.handle = handle
        self.method = method

        self.latest_frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        while not self._stop.is_set():
            ok, frame = self.handle.read()
            if ok:
                with self._lock:
                    self.latest_frame = frame.copy()

    def get_latest_frame(self) -> np.ndarray | None:
        with self._lock:
            return None if self.latest_frame is None else self.latest_frame.copy()

    def release(self):
        self._stop.set()
        self._thread.join(timeout=2)
        self.handle.release()


@dataclass
class DaemonState:
    actuator: ActuatorConnection | None = None
    sensors: dict[str, SensorConnection] = field(default_factory=dict)


state = DaemonState()
