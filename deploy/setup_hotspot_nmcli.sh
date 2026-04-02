#!/usr/bin/env bash
set -euo pipefail

IFNAME="${1:-wlan0}"
SSID="${2:-RPIC-001}"
PASSWORD="${3:-classroompi}"
ADDRESS_CIDR="${4:-192.168.4.1/24}"
CONNECTION_NAME="${5:-pi-classroom-hotspot}"
AP_HOST="${ADDRESS_CIDR%/*}"

echo "Configuring hotspot profile ${CONNECTION_NAME} for ${SSID} on ${IFNAME}"

if sudo nmcli -t -f NAME connection show | grep -Fxq "${CONNECTION_NAME}"; then
  sudo nmcli connection modify "${CONNECTION_NAME}" connection.interface-name "${IFNAME}" 802-11-wireless.ssid "${SSID}"
else
  sudo nmcli connection add type wifi ifname "${IFNAME}" con-name "${CONNECTION_NAME}" autoconnect yes ssid "${SSID}"
fi

sudo nmcli connection modify "${CONNECTION_NAME}" \
  802-11-wireless.mode ap \
  802-11-wireless.band bg \
  ipv4.method shared \
  ipv4.addresses "${ADDRESS_CIDR}" \
  ipv6.method disabled \
  wifi-sec.key-mgmt wpa-psk \
  wifi-sec.psk "${PASSWORD}"

sudo nmcli connection up "${CONNECTION_NAME}"

echo "Hotspot ready"
echo "SSID: ${SSID}"
echo "Address: ${AP_HOST}"
echo "Open: http://${AP_HOST}:8080"
echo "Confirm address and routing with:"
echo "  ip addr show ${IFNAME}"
echo "  nmcli connection show"
