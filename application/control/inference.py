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
    tokenizer_repo = entry.get("tokenizer_repo")
    if not tokenizer_repo:
        raise HTTPException(
            status_code=400,
            detail="this model has no tokenizer_repo set in the catalog yet",
        )

    try:
        return AutoTokenizer.from_pretrained(tokenizer_repo, token=HF_CLIENT.token)
    except OSError as e:
        # AutoTokenizer.from_pretrained wraps huggingface_hub's GatedRepoError
        # into a plain OSError before it reaches here -- catching
        # GatedRepoError directly does NOT work for this call path.
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
    frames = []
    for view in required_views:
        frame = state.sensors[view].get_latest_frame()
        if frame is None:
            return None  # capture thread hasn't produced a frame yet -- caller retries
        frames.append(_resize_with_pad(frame, image_size))
    return frames


def _build_request(run_session: RunSession, frames: list[np.ndarray], positions: list[int], request_id: int):
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
    """Runs on its own background thread (started by run_model). Chunk-replay:
    only builds + sends a new PredictRequest when the shared action queue is
    empty. Never touches the actuator's servos beyond reading position --
    writing corrected commands is the PID worker's job, not this one's."""
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
                time.sleep(0.01)
                continue

            frames = _capture_all_frames(required_views, image_size)
            if frames is None:
                time.sleep(0.05)
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
