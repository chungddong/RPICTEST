#!/usr/bin/env bash
set -euo pipefail

IFNAME="${1:-wlan0}"
SSID="${2:-RPIC-001}"
PASSWORD="${3:-classroompi}"

echo "Creating hotspot profile for ${SSID} on ${IFNAME}"
sudo nmcli device wifi hotspot ifname "${IFNAME}" ssid "${SSID}" password "${PASSWORD}"

echo "Hotspot created. Confirm address and routing with:"
echo "  ip addr show ${IFNAME}"
echo "  nmcli connection show"
