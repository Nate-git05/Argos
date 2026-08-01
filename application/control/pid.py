"""The PID worker: the fast background loop that turns model-predicted
targets into corrected servo commands.

Deliberately separate from the inference worker (application/control/
inference.py) even though both run only while a RunSession is active --
inference is slow (can take seconds per call depending on the model) while
PID correction needs to run at a steady, much faster rate regardless of
how long inference takes. Splitting them into two independently-looping
threads sharing only RunSession's action queue is what makes that possible;
see RunSession's docstring in state.py for the full reasoning.

Every gain/tolerance/register-address constant this module touches is a
placeholder -- see config.py's PID section for the full caveat. Nothing
here has been tuned against real hardware.
"""

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
    worker's pace. Pops one target off the shared queue and HOLDS it --
    correcting toward it every PID_LOOP_PERIOD_S -- until the actuator's
    real position is within PID_POSITION_TOLERANCE, and only then advances
    to the next target (confirmed design: error-tolerance-based advance,
    not a fixed timer, so a target is never abandoned mid-correction).
    A read or write failure hard-stops the whole run immediately: acting
    on an actuator we can no longer read from or confirm commands reached
    is a safety problem, not something to paper over and continue.
    """
    servo_ids = state.actuator.servo_ids
    n = len(servo_ids)
    integral = np.zeros(n, dtype=np.float32)
    prev_error = np.zeros(n, dtype=np.float32)

    current_target: np.ndarray | None = None

    while not run_session.stop.is_set():
        if current_target is None:
            current_target = run_session.pop_next()
            if current_target is None:
                time.sleep(PID_LOOP_PERIOD_S)  # queue empty -- inference hasn't produced a chunk yet
                continue
            # Fresh target: reset accumulated error state so the previous
            # target's integral/derivative history doesn't bleed into this
            # one's correction.
            integral[:] = 0
            prev_error[:] = 0

        positions = state.actuator.read_positions()
        if positions is None:
            run_session.log("pid", "actuator position read failed -- stopping run")
            run_session.stop.set()
            break

        positions = np.array(positions, dtype=np.float32)

        # current_target's length is the model's action_dim, which may not
        # equal the connected servo count -- pad/truncate defensively
        # rather than assume they always match.
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
            current_target = None  # next loop iteration pops the next queued target

        time.sleep(PID_LOOP_PERIOD_S)


def move_to_positions(target_positions: list[float], timeout_s: float) -> bool:
    """One-shot convergence toward a single fixed target -- same PID
    gains/tolerance/math as run_pid_worker, but without a queue to drain,
    since callers of this (currently just /stop, driving the arm to its
    home position) have exactly one target and no follow-up chunk coming.
    Blocks until within tolerance or timeout_s elapses; returns whether it
    actually converged so the caller can report that honestly rather than
    assume success.
    """
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

    return False  # timed out before converging
