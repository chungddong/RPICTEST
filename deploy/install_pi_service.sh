#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROJECT_DIR="${1:-/opt/pi-classroom-device}"
SERVICE_PATH="/etc/systemd/system/pi-classroom-device.service"
SERVICE_USER="${SERVICE_USER:-${SUDO_USER:-${USER}}}"

if ! id "${SERVICE_USER}" >/dev/null 2>&1; then
  echo "Service user does not exist: ${SERVICE_USER}" >&2
  exit 1
fi

echo "[1/4] Copying project into ${PROJECT_DIR}"
sudo mkdir -p "${PROJECT_DIR}"
if command -v rsync >/dev/null 2>&1; then
  sudo rsync -a --delete \
    --exclude ".git" \
    --exclude "__pycache__" \
    --exclude "*.pyc" \
    "${REPO_ROOT}/" "${PROJECT_DIR}/"
else
  sudo rm -rf "${PROJECT_DIR}"
  sudo mkdir -p "${PROJECT_DIR}"
  sudo cp -a "${REPO_ROOT}/." "${PROJECT_DIR}/"
  sudo find "${PROJECT_DIR}" -name "__pycache__" -type d -prune -exec rm -rf {} +
  sudo find "${PROJECT_DIR}" -name "*.pyc" -delete
  sudo rm -rf "${PROJECT_DIR}/.git"
fi

echo "[2/4] Installing systemd unit"
sudo cp "${REPO_ROOT}/deploy/pi-classroom-device.service" "${SERVICE_PATH}"
sudo sed -i "s|/opt/pi-classroom-device|${PROJECT_DIR}|g" "${SERVICE_PATH}"
sudo sed -i "s|__SERVICE_USER__|${SERVICE_USER}|g" "${SERVICE_PATH}"

echo "[3/4] Reloading systemd"
sudo systemctl daemon-reload

echo "[4/4] Enabling service"
sudo systemctl enable pi-classroom-device.service

echo "Installation complete. Start with:"
echo "  sudo systemctl start pi-classroom-device.service"
echo "  sudo systemctl status pi-classroom-device.service"
echo "  service user: ${SERVICE_USER}"
