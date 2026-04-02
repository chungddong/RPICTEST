# Raspberry Pi Classroom Device MVP

This repository contains a Raspberry Pi device-side MVP for the flow below:

1. Raspberry Pi boots.
2. Hotspot and BLE advertisement start automatically.
3. A mobile app discovers nearby devices over BLE.
4. The app connects to the chosen device hotspot.
5. The app opens the device workspace inside a WebView.
6. The student uses the browser terminal or GPIO controls.

The first version in this repo is intentionally lightweight:

- Pure Python standard library
- Mobile-friendly local web UI
- Terminal session support
- GPIO abstraction with dry-run fallback
- Hotspot and BLE orchestration with Raspberry Pi friendly command hooks
- `systemd` unit and setup scripts for Pi deployment

## Quick start

```powershell
python -m device_app --host 127.0.0.1 --port 8080 --dry-run
```

Open `http://127.0.0.1:8080`.

## Project layout

- `device_app/`: Python runtime and local control server
- `static/`: browser UI that the mobile app can embed in a WebView
- `deploy/`: Raspberry Pi setup scripts and `systemd` unit
- `config/device.sample.json`: sample device configuration
- `tests/`: lightweight unit tests

## Raspberry Pi deployment idea

1. Copy this project to the Pi or install directly from GitHub.
2. Set up hotspot mode with `NetworkManager` or your preferred AP stack.
3. Install the `systemd` service from `deploy/`.
4. Boot the Pi and let the local server start automatically.

The local web app is designed to be reachable at `http://192.168.4.1:8080` after the phone joins the Pi hotspot.

## Install on Raspberry Pi

One-line install from GitHub with `curl`:

```bash
curl -fsSL https://raw.githubusercontent.com/chungddong/RPICTEST/main/install.sh | bash -s -- main /opt/pi-classroom-device
```

If the Pi already has this repo checked out:

```bash
chmod +x deploy/install_pi_service.sh
./deploy/install_pi_service.sh /opt/pi-classroom-device
```

If you want a one-step GitHub install from your repository:

```bash
git clone https://github.com/chungddong/RPICTEST.git
cd RPICTEST
chmod +x deploy/install_from_github.sh
./deploy/install_from_github.sh https://github.com/chungddong/RPICTEST.git /opt/pi-classroom-device main
```

After that, set up the hotspot profile:

```bash
sudo /opt/pi-classroom-device/deploy/setup_hotspot_nmcli.sh wlan0 RPIC-001 classroompi
sudo systemctl start pi-classroom-device.service
sudo systemctl status pi-classroom-device.service
```
