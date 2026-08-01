"""The daemon's single source of truth for everything currently connected
or running: the actuator, cameras, the vla-server subprocess, and (while a
run is active) the shared queue between the inference and PID workers.

Every route module and both background workers import the module-level
`state` singleton below rather than passing connection objects around --
that's what lets, e.g., a route handler set up a camera and a completely
separate background thread read its frames without any direct coupling
between them.
"""

import re
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field

import cv2
import numpy as np
import scservo_sdk as scs

from application.server.local.config.config import ACTUATOR_GOAL_POSITION_ADDR, ACTUATOR_PRESENT_POSITION_ADDR

# The only readiness signal vla-server gives us -- there's no health-check
# RPC anywhere in vla.proto, so EngineConnection watches stdout for this
# exact line instead.
ENGINE_READY_PATTERN = re.compile(r"bound to .* ready", re.IGNORECASE)


@dataclass
class ActuatorConnection:
    """A live Feetech bus connection plus the servo IDs that actually
    responded to ping() at connect time (which may be fewer than were
    asked for -- see hardware_connection.py's connect_actuator)."""

    port: str
    port_handler: scs.PortHandler
    packet_handler: scs.protocol_packet_handler
    servo_ids: list[int]

    def close(self):
        self.port_handler.closePort()

    def read_positions(self) -> list[int] | None:
        """Reads Present_Position for every connected servo, in servo_ids
        order. Returns None if ANY read fails -- callers must hard-stop
        rather than build a state vector or PID correction from
        partial/stale data. A wrong real-time joint position is dangerous
        to act on, not just imprecise."""
        positions = []
        for servo_id in self.servo_ids:
            pos, result, _error = self.packet_handler.read2ByteTxRx(
                self.port_handler, servo_id, ACTUATOR_PRESENT_POSITION_ADDR
            )
            if result != scs.COMM_SUCCESS:
                return None
            positions.append(pos)
        return positions

    def write_positions(self, commands: list[int]) -> bool:
        """Writes Goal_Position for every connected servo, in servo_ids
        order (commands must line up 1:1 with servo_ids). Returns False if
        ANY write fails -- callers must hard-stop rather than keep
        commanding an arm we can no longer confirm is receiving orders."""
        for servo_id, command in zip(self.servo_ids, commands):
            result, _error = self.packet_handler.write2ByteTxRx(
                self.port_handler, servo_id, ACTUATOR_GOAL_POSITION_ADDR, int(command)
            )
            if result != scs.COMM_SUCCESS:
                return False
        return True


class SensorConnection:
    """One connected camera, with a background thread that continuously
    overwrites a single cached "latest frame" -- never a growing queue,
    memory use stays flat no matter how long the camera runs. Every
    consumer (the /view websocket, the inference worker) just reads
    whatever's freshest via get_latest_frame(); nobody manages capture
    themselves."""

    def __init__(self, index: int, view_name: str, handle: cv2.VideoCapture, method: str = "usb"):
        self.index = index
        self.view_name = view_name
        self.handle = handle
        self.method = method

        self.latest_frame: np.ndarray | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        # Cleared by default: the connection is held open (verified via a
        # test frame at connect time) but the loop below stays parked in
        # wait() doing no work until something (run) actually needs frames.
        # No point burning CPU/power decoding frames nobody's reading yet --
        # this matters on a Jetson's power budget, not just as an
        # optimization.
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
        """Returns a copy, not a reference -- safe to call concurrently
        from multiple threads without any of them racing the capture
        thread's next overwrite."""
        with self._lock:
            return None if self.latest_frame is None else self.latest_frame.copy()

    def release(self):
        self._stop.set()
        self._active.set()  # wake the wait() so it notices _stop promptly instead of on the next 0.5s tick
        self._thread.join(timeout=2)
        self.handle.release()


class EngineConnection:
    """Wraps the vla-server subprocess. A background thread continuously
    drains its stdout into a bounded log buffer -- if nobody reads this
    pipe, its OS buffer fills up once the process starts logging normally
    and vla-server blocks on write(), silently stalling inference. The
    same thread watches for the readiness line and sets `ready`."""

    def __init__(self, process: subprocess.Popen, model: str, bind_addr: str, log_lines: int = 200):
        self.process = process
        self.model = model
        self.bind_addr = bind_addr

        self.logs: deque[str] = deque(maxlen=log_lines)
        self.ready = threading.Event()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        for line in self.process.stdout:
            self.logs.append(line.rstrip("\n"))
            if ENGINE_READY_PATTERN.search(line):
                self.ready.set()

    def wait_until_ready(self, timeout_s: float = 60.0) -> bool:
        """Polls in short increments rather than blocking for the full
        timeout, so a process that exits early (bad ckpt, crash) is
        reported as failed within a fraction of a second instead of only
        after timeout_s has fully elapsed."""
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
    """Everything a single `run` needs, shared between the inference
    worker and the PID worker -- two separate background threads, each
    looping independently at its own pace, coordinating only through this
    object's FIFO action queue. Never run both loops on one thread: the
    whole point of the split is inference (slow, seconds per call for some
    models) and PID correction (fast, tens of times per second) proceeding
    concurrently, not one blocking the other.
    """

    def __init__(self, model: str, instruction: str, tokenizer, max_state_dim: int, log_lines: int = 200):
        self.model = model
        self.instruction = instruction
        self.tokenizer = tokenizer
        self.max_state_dim = max_state_dim

        # FIFO, not a "latest value" cache like SensorConnection's -- each
        # row in an action_chunk is a DIFFERENT timestep's target, order
        # matters and every row must be consumed once, not just the newest.
        self._queue: deque[np.ndarray] = deque()
        self._queue_lock = threading.Lock()

        self.logs: deque[str] = deque(maxlen=log_lines)
        self._logs_lock = threading.Lock()

        self.stop = threading.Event()

        # Set by run_model right after starting each worker, so /stop can
        # join them and know both loops have actually exited before
        # tearing down the engine/actuator underneath them.
        self.inference_thread: threading.Thread | None = None
        self.pid_thread: threading.Thread | None = None

    def push_chunk(self, actions: list[np.ndarray]):
        """Called by the inference worker after a successful PredictResponse."""
        with self._queue_lock:
            self._queue.extend(actions)

    def pop_next(self) -> np.ndarray | None:
        """Called by the PID worker. Returns None (not an exception) when
        empty -- an empty queue is the normal, expected steady state
        between inference calls, not an error."""
        with self._queue_lock:
            return self._queue.popleft() if self._queue else None

    def is_empty(self) -> bool:
        """The inference worker's chunk-replay gate: only build and send a
        new PredictRequest once the PID worker has fully drained the
        previous chunk."""
        with self._queue_lock:
            return len(self._queue) == 0

    def log(self, stage: str, message: str):
        """Pipeline-level log, distinct from EngineConnection.logs (which
        is vla-server's own raw stdout) -- this is Argos's own record of
        what each worker is doing, meant to back a future /logs route."""
        with self._logs_lock:
            self.logs.append(f"[{stage}] {message}")


@dataclass
class DaemonState:
    """The module-level singleton every route and worker reads/writes.
    None fields mean "nothing connected/running" -- routes check for None
    rather than assuming any of this exists."""

    actuator: ActuatorConnection | None = None
    sensors: dict[str, SensorConnection] = field(default_factory=dict)
    engine: EngineConnection | None = None
    run: RunSession | None = None


state = DaemonState()
