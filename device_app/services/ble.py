from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict

from ..config import BleConfig


class BleAdvertiser:
    def __init__(self, config: BleConfig, device_id: str, dry_run: bool = False) -> None:
        self.config = config
        self.device_id = device_id
        self.dry_run = dry_run
        self.started = False
        self.last_command: list[str] | None = None

    def start(self) -> None:
        if not self.config.enabled:
            self.started = False
            return

        command = [
            "bluetoothctl",
            "advertise",
            "on",
        ]
        self.last_command = command

        if self.dry_run or platform.system() != "Linux":
            self.started = True
            return

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            self.started = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.started = False

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.config.enabled,
            "started": self.started,
            "local_name": self.config.local_name,
            "service_uuid": self.config.service_uuid,
            "advertisement": self.advertisement_payload(),
            "last_command": self.last_command,
            "dry_run": self.dry_run,
        }

    def advertisement_payload(self) -> str:
        payload = {
            "device_id": self.device_id,
            **self.config.advertised_fields,
        }
        return json.dumps(payload, separators=(",", ":"))
