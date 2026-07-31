#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="${REPO_ROOT}/application"
VENV_DIR="${APP_DIR}/.venv"
ENGINE_DIR="${APP_DIR}/server/local/services/engine"

log() { echo "[install] $*"; }

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[install] missing required command: $1" >&2
        exit 1
    fi
}

# --- 1. GPU detection -------------------------------------------------------
# Order matters: nvidia-smi does NOT work on Jetson/Tegra hardware (confirmed
# against vla.cpp's own docs -- Tegra's unified-memory GPU isn't queryable
# the way a discrete desktop GPU is), so Jetson has to be checked first via
# its own signals, not nvidia-smi. Only fall through to nvidia-smi for
# regular desktop/workstation NVIDIA GPUs. CPU is the last resort.
is_jetson() {
    [[ -f /etc/nv_tegra_release ]] && return 0
    [[ -f /proc/device-tree/model ]] && grep -qi "jetson" /proc/device-tree/model 2>/dev/null && return 0
    return 1
}

detect_cuda_arch() {
    if is_jetson; then
        # Confirmed via vla.cpp's README GPU table: 87 covers Orin Nano,
        # Orin NX, and AGX Orin -- no query needed, it's a fixed constant
        # for this whole hardware family.
        echo "87"
        return
    fi

    if command -v nvidia-smi >/dev/null 2>&1; then
        local compute_cap
        compute_cap=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | head -n1 | tr -d '[:space:]')
        if [[ -n "${compute_cap}" ]]; then
            echo "${compute_cap//./}"
            return
        fi
    fi

    echo ""
}

CUDA_ARCH="$(detect_cuda_arch)"
if is_jetson; then
    log "detected Jetson hardware -> CMAKE_CUDA_ARCHITECTURES=${CUDA_ARCH}"
elif [[ -n "${CUDA_ARCH}" ]]; then
    log "detected desktop NVIDIA GPU via nvidia-smi -> CMAKE_CUDA_ARCHITECTURES=${CUDA_ARCH}"
else
    log "WARNING: no GPU detected (no Jetson, no nvidia-smi) -- falling back to a CPU-only build."
    log "WARNING: CPU inference is dramatically slower than GPU and is unlikely to support real-time control. Proceed only for development/testing."
fi

# --- 2. system dependencies --------------------------------------------------
require_cmd cmake
require_cmd python3
require_cmd git

if command -v apt-get >/dev/null 2>&1; then
    log "installing system packages via apt-get (build-essential, libzmq3-dev, cppzmq-dev, protobuf-compiler, libprotobuf-dev)"
    sudo apt-get update -qq
    sudo apt-get install -y -qq build-essential libzmq3-dev cppzmq-dev protobuf-compiler libprotobuf-dev
else
    log "apt-get not found -- install build-essential, libzmq3-dev, cppzmq-dev, protobuf-compiler, and libprotobuf-dev manually before continuing" >&2
    exit 1
fi

# --- 3. python venv + deps ---------------------------------------------------
if [[ ! -d "${VENV_DIR}" ]]; then
    log "creating venv at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
fi

log "installing Python dependencies"
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip
"${VENV_DIR}/bin/pip" install --quiet -r "${APP_DIR}/requirements.txt"

# --- 4. build the vla.cpp inference engine -----------------------------------
log "building vla.cpp engine (this can take a while the first time)"
CMAKE_ARGS=(-B build -DCMAKE_BUILD_TYPE=Release)
if [[ -n "${CUDA_ARCH}" ]]; then
    CMAKE_ARGS+=(-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="${CUDA_ARCH}")
fi

cmake -S "${ENGINE_DIR}" "${CMAKE_ARGS[@]}"
cmake --build "${ENGINE_DIR}/build" -j"$(nproc)"

if [[ ! -x "${ENGINE_DIR}/build/vla-server" ]]; then
    echo "[install] build finished but vla-server binary not found at ${ENGINE_DIR}/build/vla-server" >&2
    exit 1
fi

log "done -- vla-server built at ${ENGINE_DIR}/build/vla-server"

# --- 5. systemd service for the daemon --------------------------------------
# The daemon (application/server/local/app.py) is what argos serve/run talk
# to over HTTP -- this installs it as a systemd service so it survives
# reboots/crashes instead of only running in a foreground terminal.
DAEMON_HOST="127.0.0.1"
DAEMON_PORT="8000"
SERVICE_USER="${SUDO_USER:-$USER}"
SERVICE_FILE="/etc/systemd/system/argos.service"
SERVICE_TEMPLATE="${REPO_ROOT}/install/argos.service.template"

log "installing systemd service (argos.service) -> daemon at http://${DAEMON_HOST}:${DAEMON_PORT}"
sed \
    -e "s|__SERVICE_USER__|${SERVICE_USER}|g" \
    -e "s|__REPO_ROOT__|${REPO_ROOT}|g" \
    -e "s|__VENV_DIR__|${VENV_DIR}|g" \
    -e "s|__DAEMON_HOST__|${DAEMON_HOST}|g" \
    -e "s|__DAEMON_PORT__|${DAEMON_PORT}|g" \
    "${SERVICE_TEMPLATE}" | sudo tee "${SERVICE_FILE}" >/dev/null

sudo systemctl daemon-reload
sudo systemctl enable argos >/dev/null

log "argos.service installed and enabled (not started yet)"
log "NEXT STEP: set HUGGING_FACE_TOKEN in ${APP_DIR}/server/local/.env, then run: sudo systemctl start argos"
