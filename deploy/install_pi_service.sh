#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-/opt/pi-classroom-device}"
SERVICE_PATH="/etc/systemd/system/pi-classroom-device.service"

echo "[1/4] Copying project into ${PROJECT_DIR}"
sudo mkdir -p "${PROJECT_DIR}"
sudo rsync -a --delete ./ "${PROJECT_DIR}/"

echo "[2/4] Installing systemd unit"
sudo cp deploy/pi-classroom-device.service "${SERVICE_PATH}"
sudo sed -i "s|/opt/pi-classroom-device|${PROJECT_DIR}|g" "${SERVICE_PATH}"

echo "[3/4] Reloading systemd"
sudo systemctl daemon-reload

echo "[4/4] Enabling service"
sudo systemctl enable pi-classroom-device.service

echo "Installation complete. Start with:"
echo "  sudo systemctl start pi-classroom-device.service"
