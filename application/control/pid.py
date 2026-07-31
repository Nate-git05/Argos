import time

import numpy as np

from application.control.state import RunSession, state
from application.server.local.config.config import (
    PID_KD,
    PID_KI,
    PID_KP,
    PID_LOOP_HZ,
    PID_POSITION_TOLERANCE,
)

PID_LOOP_PERIOD_S = 1 / PID_LOOP_HZ


def run_pid_worker(run_session: RunSession):
    """Runs on its own background thread, independent of the inference
    worker's pace (see RunSession's docstring for why). Holds each target
    popped from the shared queue, correcting toward it every
    PID_LOOP_PERIOD_S, until the actuator's real position is within
    PID_POSITION_TOLERANCE -- only then advances to the next target."""
    servo_ids = state.actuator.servo_ids
    n = len(servo_ids)
    integral = np.zeros(n, dtype=np.float32)
    prev_error = np.zeros(n, dtype=np.float32)

    current_target: np.ndarray | None = None

    while not run_session.stop.is_set():
        if current_target is None:
            current_target = run_session.pop_next()
            if current_target is None:
                time.sleep(PID_LOOP_PERIOD_S)
                continue
            integral[:] = 0
            prev_error[:] = 0

        positions = state.actuator.read_positions()
        if positions is None:
            run_session.log("pid", "actuator position read failed -- stopping run")
            run_session.stop.set()
            break

        positions = np.array(positions, dtype=np.float32)

        target = np.zeros(n, dtype=np.float32)
        avail = min(n, len(current_target))
        target[:avail] = np.asarray(current_target[:avail], dtype=np.float32)

        error = target - positions
        integral += error * PID_LOOP_PERIOD_S
        derivative = (error - prev_error) / PID_LOOP_PERIOD_S
        correction = PID_KP * error + PID_KI * integral + PID_KD * derivative
        prev_error = error

        commands = positions + correction

        if not state.actuator.write_positions(commands):
            run_session.log("pid", "actuator position write failed -- stopping run")
            run_session.stop.set()
            break

        if np.all(np.abs(error) < PID_POSITION_TOLERANCE):
            run_session.log("pid", f"target reached (max_error={float(np.max(np.abs(error))):.1f})")
            current_target = None

        time.sleep(PID_LOOP_PERIOD_S)


def move_to_positions(target_positions: list[float], timeout_s: float) -> bool:
    """One-shot convergence, same PID gains/tolerance as run_pid_worker but
    without a queue -- drives toward a single fixed target and blocks until
    within tolerance or timeout_s elapses. Used by /stop to return the arm
    to its home position. Returns whether it actually converged."""
    servo_ids = state.actuator.servo_ids
    n = len(servo_ids)
    target = np.zeros(n, dtype=np.float32)
    avail = min(n, len(target_positions))
    target[:avail] = np.asarray(target_positions[:avail], dtype=np.float32)

    integral = np.zeros(n, dtype=np.float32)
    prev_error = np.zeros(n, dtype=np.float32)

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        positions = state.actuator.read_positions()
        if positions is None:
            return False
        positions = np.array(positions, dtype=np.float32)

        error = target - positions
        if np.all(np.abs(error) < PID_POSITION_TOLERANCE):
            return True

        integral += error * PID_LOOP_PERIOD_S
        derivative = (error - prev_error) / PID_LOOP_PERIOD_S
        correction = PID_KP * error + PID_KI * integral + PID_KD * derivative
        prev_error = error

        if not state.actuator.write_positions(positions + correction):
            return False

        time.sleep(PID_LOOP_PERIOD_S)

    return False
