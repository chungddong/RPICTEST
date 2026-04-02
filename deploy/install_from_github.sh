#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-https://github.com/chungddong/RPICTEST.git}"
PROJECT_DIR="${2:-/opt/pi-classroom-device}"
BRANCH="${3:-main}"

echo "[1/5] Checking required commands"
for command in git rsync python3 systemctl; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "Missing required command: ${command}" >&2
    exit 1
  fi
done

if ! command -v nmcli >/dev/null 2>&1; then
  echo "Warning: nmcli not found. Hotspot setup script will not run until NetworkManager is installed."
fi

if ! command -v bluetoothctl >/dev/null 2>&1; then
  echo "Warning: bluetoothctl not found. BLE advertising will not run until BlueZ is installed."
fi

echo "[2/5] Preparing project directory ${PROJECT_DIR}"
sudo mkdir -p "${PROJECT_DIR}"
sudo chown "$(id -u):$(id -g)" "${PROJECT_DIR}"

if [ -d "${PROJECT_DIR}/.git" ]; then
  echo "[3/5] Updating existing checkout"
  git -C "${PROJECT_DIR}" fetch --all --prune
  git -C "${PROJECT_DIR}" checkout "${BRANCH}"
  git -C "${PROJECT_DIR}" pull --ff-only origin "${BRANCH}"
else
  echo "[3/5] Cloning repository"
  rm -rf "${PROJECT_DIR}"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${PROJECT_DIR}"
fi

echo "[4/5] Installing systemd service"
"${PROJECT_DIR}/deploy/install_pi_service.sh" "${PROJECT_DIR}"

echo "[5/5] Installation finished"
echo "Optional next steps:"
echo "  sudo ${PROJECT_DIR}/deploy/setup_hotspot_nmcli.sh wlan0 RPIC-001 classroompi"
echo "  sudo systemctl start pi-classroom-device.service"
echo "  sudo systemctl status pi-classroom-device.service"
