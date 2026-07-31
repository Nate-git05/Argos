import re
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field

import cv2
import numpy as np
import scservo_sdk as scs

from application.server.local.config.config import ACTUATOR_PRESENT_POSITION_ADDR

ENGINE_READY_PATTERN = re.compile(r"bound to .* ready", re.IGNORECASE)


@dataclass
class ActuatorConnection:
    port: str
    port_handler: scs.PortHandler
    packet_handler: scs.protocol_packet_handler
    servo_ids: list[int]  # IDs that actually responded to ping at connect time

    def close(self):
        self.port_handler.closePort()

    def read_positions(self) -> list[int] | None:
        """Reads Present_Position for every connected servo, in servo_ids
        order. Returns None if ANY read fails -- the caller must hard-stop
        rather than build a state vector from partial/stale data."""
        positions = []
        for servo_id in self.servo_ids:
            pos, result, _error = self.packet_handler.read2ByteTxRx(
                self.port_handler, servo_id, ACTUATOR_PRESENT_POSITION_ADDR
            )
            if result != scs.COMM_SUCCESS:
                return None
            positions.append(pos)
        return positions


class SensorConnection:
    def __init__(self, index: int, view_name: str, handle: cv2.VideoCapture, method: str = "usb"):
        self.index = index
        self.view_name = view_name
        self.handle = handle
        self.method = method

        self.latest_frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        # Cleared by default -- the connection is held open (verified via a
        # test frame at connect time) but the loop below stays parked in
        # wait() doing no work until something (run) actually needs frames.
        # No point burning CPU/power decoding frames nobody's reading yet.
        self._active = threading.Event()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        while not self._stop.is_set():
            if not self._active.wait(timeout=0.5):
                continue
            ok, frame = self.handle.read()
            if ok:
                with self._lock:
                    self.latest_frame = frame.copy()

    def start_capture(self):
        self._active.set()

    def pause_capture(self):
        self._active.clear()

    def get_latest_frame(self) -> np.ndarray | None:
        with self._lock:
            return None if self.latest_frame is None else self.latest_frame.copy()

    def release(self):
        self._stop.set()
        self._active.set()  # wake the wait() so it notices _stop promptly
        self._thread.join(timeout=2)
        self.handle.release()


class EngineConnection:
    def __init__(self, process: subprocess.Popen, model: str, bind_addr: str, log_lines: int = 200):
        self.process = process
        self.model = model
        self.bind_addr = bind_addr

        self.logs: deque[str] = deque(maxlen=log_lines)
        self.ready = threading.Event()
        # Continuously drains stdout -- if nobody reads this pipe, its OS
        # buffer fills up once vla-server starts logging normally and the
        # process blocks on write(), silently stalling inference.
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        for line in self.process.stdout:
            self.logs.append(line.rstrip("\n"))
            if ENGINE_READY_PATTERN.search(line):
                self.ready.set()

    def wait_until_ready(self, timeout_s: float = 60.0) -> bool:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.ready.wait(timeout=0.5):
                return True
            if self.process.poll() is not None:
                return False
        return self.ready.is_set()

    def stop(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class RunSession:
    """Shared between the inference worker and the PID worker -- two
    separate background threads, each looping independently at its own
    pace, coordinating only through this object. Never run both loops on
    one thread: the whole point is inference (slow) and PID correction
    (fast) proceeding concurrently, not one blocking the other."""

    def __init__(self, model: str, instruction: str, log_lines: int = 200):
        self.model = model
        self.instruction = instruction

        self._queue: deque[np.ndarray] = deque()
        self._queue_lock = threading.Lock()

        self.logs: deque[str] = deque(maxlen=log_lines)
        self._logs_lock = threading.Lock()

        self.stop = threading.Event()

    def push_chunk(self, actions: list[np.ndarray]):
        with self._queue_lock:
            self._queue.extend(actions)

    def pop_next(self) -> np.ndarray | None:
        with self._queue_lock:
            return self._queue.popleft() if self._queue else None

    def is_empty(self) -> bool:
        with self._queue_lock:
            return len(self._queue) == 0

    def log(self, stage: str, message: str):
        with self._logs_lock:
            self.logs.append(f"[{stage}] {message}")


@dataclass
class DaemonState:
    actuator: ActuatorConnection | None = None
    sensors: dict[str, SensorConnection] = field(default_factory=dict)
    engine: EngineConnection | None = None
    run: RunSession | None = None


state = DaemonState()
