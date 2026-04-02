#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="${REPO_OWNER:-chungddong}"
REPO_NAME="${REPO_NAME:-RPICTEST}"
BRANCH="${1:-main}"
PROJECT_DIR="${2:-/opt/pi-classroom-device}"
WLAN_IFACE="${3:-wlan0}"
HOTSPOT_SSID="${4:-RPIC-001}"
HOTSPOT_PASSWORD="${5:-classroompi}"
HOTSPOT_ADDRESS_CIDR="${6:-192.168.4.1/24}"
TMP_DIR="$(mktemp -d)"
ARCHIVE_URL="https://codeload.github.com/${REPO_OWNER}/${REPO_NAME}/tar.gz/refs/heads/${BRANCH}"
ARCHIVE_PATH="${TMP_DIR}/repo.tar.gz"

cleanup() {
  rm -rf "${TMP_DIR}"
}

trap cleanup EXIT

echo "[1/6] Checking runtime requirements"
for command in curl tar python3 sudo systemctl; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "Missing required command: ${command}" >&2
    exit 1
  fi
done

echo "[2/6] Installing optional package dependencies when missing"
MISSING_PACKAGES=()
command -v rsync >/dev/null 2>&1 || MISSING_PACKAGES+=("rsync")
command -v nmcli >/dev/null 2>&1 || MISSING_PACKAGES+=("network-manager")
command -v bluetoothctl >/dev/null 2>&1 || MISSING_PACKAGES+=("bluez")
command -v x11vnc >/dev/null 2>&1 || MISSING_PACKAGES+=("x11vnc")
command -v novnc_proxy >/dev/null 2>&1 || MISSING_PACKAGES+=("novnc" "websockify")

if [ "${#MISSING_PACKAGES[@]}" -gt 0 ]; then
  sudo apt-get update
  sudo apt-get install -y "${MISSING_PACKAGES[@]}"
fi

echo "[3/6] Downloading ${REPO_OWNER}/${REPO_NAME}@${BRANCH}"
curl -fsSL "${ARCHIVE_URL}" -o "${ARCHIVE_PATH}"

echo "[4/6] Extracting archive"
tar -xzf "${ARCHIVE_PATH}" -C "${TMP_DIR}"
SOURCE_DIR="$(find "${TMP_DIR}" -maxdepth 1 -mindepth 1 -type d -name "${REPO_NAME}-*" | head -n 1)"

if [ -z "${SOURCE_DIR}" ]; then
  echo "Failed to locate extracted source directory" >&2
  exit 1
fi

echo "[5/6] Installing project into ${PROJECT_DIR}"
chmod +x "${SOURCE_DIR}/deploy/install_pi_service.sh"
"${SOURCE_DIR}/deploy/install_pi_service.sh" "${PROJECT_DIR}"

echo "[6/6] Configuring hotspot and starting service"
chmod +x "${PROJECT_DIR}/deploy/setup_hotspot_nmcli.sh"
sudo "${PROJECT_DIR}/deploy/setup_hotspot_nmcli.sh" "${WLAN_IFACE}" "${HOTSPOT_SSID}" "${HOTSPOT_PASSWORD}" "${HOTSPOT_ADDRESS_CIDR}"
sudo systemctl restart pi-classroom-device.service

echo "Install complete"
echo "Hotspot: ${HOTSPOT_SSID} (${WLAN_IFACE})"
echo "URL: http://${HOTSPOT_ADDRESS_CIDR%/*}:8080"
echo "Service status:"
sudo systemctl --no-pager --full status pi-classroom-device.service || true
