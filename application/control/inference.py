"""The inference worker: the background thread that talks to vla-server.

Owns one ZMQ REQ socket for the lifetime of a run. On each cycle (gated by
RunSession's chunk-replay queue being empty) it pulls the latest frame from
every required camera, reads the actuator's real-time position, tokenizes
the instruction, sends one PredictRequest, and pushes the resulting
action_chunk onto the shared queue for the PID worker to drain. It never
writes to the actuator itself -- that split is deliberate, see
RunSession's docstring in state.py for why inference and PID correction
run as two independent loops rather than one.
"""

import time

import cv2
import numpy as np
import zmq
from fastapi import HTTPException
from transformers import AutoTokenizer

from application.control.proto import vla_pb2
from application.control.state import RunSession, state
from application.server.local.config.config import HF_CLIENT

ZMQ_RECV_TIMEOUT_MS = 30_000


def load_tokenizer(entry: dict):
    """Loads whatever tokenizer_repo the requested model's catalog entry
    names -- generic across every model, not hardcoded to any one of them,
    so a newly-added model works here automatically once its catalog entry
    has tokenizer_repo set. Raises a clean, actionable HTTPException for
    both "not configured yet" and "gated, needs license acceptance"
    instead of letting either surface as a raw traceback."""
    tokenizer_repo = entry.get("tokenizer_repo")
    if not tokenizer_repo:
        raise HTTPException(
            status_code=400,
            detail="this model has no tokenizer_repo set in the catalog yet",
        )

    try:
        return AutoTokenizer.from_pretrained(tokenizer_repo, token=HF_CLIENT.token)
    except OSError as e:
        # transformers wraps huggingface_hub's GatedRepoError into a plain
        # OSError before it reaches this call site -- catching
        # GatedRepoError directly silently never fires for this specific
        # from_pretrained() path, confirmed by testing against pi0's real
        # gated tokenizer repo. Detecting on message content instead.
        if "gated repo" in str(e).lower():
            raise HTTPException(
                status_code=403,
                detail=(
                    f"tokenizer repo {tokenizer_repo!r} is gated -- accept its license at "
                    f"https://huggingface.co/{tokenizer_repo} with the account matching "
                    "HUGGING_FACE_TOKEN, then try again."
                ),
            )
        raise HTTPException(status_code=502, detail=f"failed to load tokenizer {tokenizer_repo!r}: {e}")


def _resize_with_pad(frame: np.ndarray, size: int) -> np.ndarray:
    """BGR uint8 (as read by OpenCV) -> RGB float32 in [0, 1], resized to
    fit within (size, size) preserving aspect ratio, zero-padded to fill
    the rest -- this is the F32_RGB_01 encoding vla-server expects."""
    h, w = frame.shape[:2]
    scale = size / max(h, w)
    new_h, new_w = max(int(round(h * scale)), 1), max(int(round(w * scale)), 1)
    resized = cv2.resize(frame, (new_w, new_h))

    padded = np.zeros((size, size, 3), dtype=np.uint8)
    padded[:new_h, :new_w] = resized

    rgb = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
    return rgb.astype(np.float32) / 255.0


def _capture_all_frames(required_views: list[str], image_size: int) -> list[np.ndarray] | None:
    """Pulls the current cached frame for every view the model needs, in
    the model's own required order -- not whatever order sensors happened
    to connect in (see connect_sensor: view_name is required to match the
    catalog's camera_views.keys exactly, precisely so this ordering is
    unambiguous). Returns None if any view doesn't have a frame yet, which
    is the normal state for the first ~0.5s after a sensor's capture
    thread is activated, not an error -- caller retries."""
    frames = []
    for view in required_views:
        frame = state.sensors[view].get_latest_frame()
        if frame is None:
            return None
        frames.append(_resize_with_pad(frame, image_size))
    return frames


def _build_request(run_session: RunSession, frames: list[np.ndarray], positions: list[int], request_id: int):
    """Assembles one PredictRequest. State is zero-padded up to
    max_state_dim -- the zero padding here means "this dimension doesn't
    exist for this robot" (a legitimate, expected value the model
    architecture accounts for), which is a completely different situation
    from a missing/failed position read (handled separately, upstream in
    run_inference_worker, by hard-stopping instead of padding)."""
    state_vec = np.zeros(run_session.max_state_dim, dtype=np.float32)
    state_vec[: len(positions)] = positions

    toks = run_session.tokenizer(run_session.instruction, return_tensors="np")
    lang_tokens = toks["input_ids"][0].astype(np.int32)

    req = vla_pb2.PredictRequest()
    req.request_id = request_id
    for frame in frames:
        img = req.images.add()
        img.encoding = vla_pb2.Image.F32_RGB_01
        img.height = frame.shape[0]
        img.width = frame.shape[1]
        img.data = frame.tobytes()
    req.lang_tokens.extend(lang_tokens.tolist())
    req.state.extend(state_vec.tolist())
    return req


def run_inference_worker(run_session: RunSession, entry: dict):
    """Runs on its own background thread, started by run_model once the
    engine is confirmed ready. Chunk-replay: only builds and sends a new
    PredictRequest once RunSession's shared queue is empty, i.e. once the
    PID worker has fully consumed the previous action_chunk. Never writes
    to the actuator -- only reads its position for the state vector;
    issuing corrected commands is exclusively the PID worker's job. Any
    failure here (missing actuator read, a vla-server-side error, a ZMQ
    transport error) hard-stops the entire run rather than retrying or
    limping along on partial data.
    """
    required_views = entry["camera_views"]["keys"]
    image_size = entry["image_size"]

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.RCVTIMEO, ZMQ_RECV_TIMEOUT_MS)
    socket.setsockopt(zmq.LINGER, 0)
    socket.connect(state.engine.bind_addr)

    request_id = 0
    try:
        while not run_session.stop.is_set():
            if not run_session.is_empty():
                time.sleep(0.01)  # queue still has targets for the PID worker; nothing to do yet
                continue

            frames = _capture_all_frames(required_views, image_size)
            if frames is None:
                time.sleep(0.05)  # cameras just activated, capture thread hasn't produced a frame yet
                continue

            positions = state.actuator.read_positions()
            if positions is None:
                run_session.log("inference", "actuator position read failed -- stopping run")
                run_session.stop.set()
                break

            request_id += 1
            req = _build_request(run_session, frames, positions, request_id)

            run_session.log("inference", f"sending PredictRequest id={request_id}")
            try:
                socket.send(req.SerializeToString())
                raw = socket.recv()
            except zmq.ZMQError as e:
                # REQ/REP is strict lockstep -- once a round-trip fails
                # (e.g. the 30s RCVTIMEO fires), this socket can't be
                # trusted for another request without reconnecting, and
                # the engine side may have already torn itself down on
                # its end too. Treat as fatal rather than attempt a retry
                # that's likely to fail again.
                run_session.log("inference", f"ZMQ error: {e} -- stopping run")
                run_session.stop.set()
                break

            resp = vla_pb2.PredictResponse()
            resp.ParseFromString(raw)

            if resp.error:
                run_session.log("inference", f"vla-server error: {resp.error} -- stopping run")
                run_session.stop.set()
                break

            chunk = np.array(resp.action_chunk, dtype=np.float32).reshape(resp.chunk_size, resp.action_dim)
            run_session.push_chunk(list(chunk))
            run_session.log("inference", f"received action_chunk shape={tuple(chunk.shape)}")
    finally:
        socket.close(linger=0)
        context.term()
