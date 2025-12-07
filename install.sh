#!/usr/bin/env bash
set -euo pipefail

# Directory where this script lives (repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Host paths
HOST_ROOT="/opt/arcade_app"
HOST_CONFIG="${HOST_ROOT}/config.ini"
HOST_DATA="${HOST_ROOT}/data"
HOST_LOG="${HOST_ROOT}/arcadecheck.log"

echo "[install] Preparing host directories under ${HOST_ROOT}..."
sudo mkdir -p "${HOST_ROOT}"
sudo mkdir -p "${HOST_DATA}"

# Copy config.example.ini -> config.ini if not present
if [ ! -f "${HOST_CONFIG}" ]; then
    if [ ! -f "${SCRIPT_DIR}/config.example.ini" ]; then
        echo "[install] ERROR: ${SCRIPT_DIR}/config.example.ini not found."
        echo "          Please create a config.example.ini in the repo first."
        exit 1
    fi
    echo "[install] Creating initial config at ${HOST_CONFIG}..."
    sudo cp "${SCRIPT_DIR}/config.example.ini" "${HOST_CONFIG}"
    sudo chmod 640 "${HOST_CONFIG}"
else
    echo "[install] Existing config found at ${HOST_CONFIG}, leaving it in place."
fi

# Ensure log file exists
if [ ! -f "${HOST_LOG}" ]; then
    echo "[install] Creating log file at ${HOST_LOG}..."
    sudo touch "${HOST_LOG}"
fi
sudo chmod 664 "${HOST_LOG}"

# Optional: create empty .ver files if you want them bootstraped
for app in mame launchbox retroarch ledblinky scummvm; do
    verfile="${HOST_DATA}/${app}.ver"
    if [ ! -f "${verfile}" ]; then
        echo "[install] Creating initial ${app}.ver at ${verfile}..."
        today="$(date +'%m-%d-%Y')"
        printf "0.0.0\n%s\n" "${today}" | sudo tee "${verfile}" >/dev/null
        sudo chmod 664 "${verfile}"
    fi
done

echo "[install] Host prep complete."
echo "[install] Building and starting docker stack with docker compose..."

cd "${SCRIPT_DIR}"
docker compose up -d

echo "[install] Done. Web UI should be available on http://<host>:5000/"
