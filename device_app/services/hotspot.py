from __future__ import annotations

import platform
import shutil
import subprocess

from ..config import HotspotConfig


class HotspotManager:
    def __init__(self, config: HotspotConfig, dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self.started = False
        self.last_command: list[str] | None = None

    def start(self) -> None:
        command = [
            "nmcli",
            "device",
            "wifi",
            "hotspot",
            "ifname",
            self.config.interface,
            "ssid",
            self.config.ssid,
            "password",
            self.config.password,
        ]
        self.last_command = command

        if self.dry_run or platform.system() != "Linux":
            self.started = True
            return

        if not shutil.which("nmcli"):
            self.started = False
            return

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            self.started = True
        except subprocess.CalledProcessError:
            self.started = False

    def status(self) -> dict[str, object]:
        return {
            "started": self.started,
            "ssid": self.config.ssid,
            "interface": self.config.interface,
            "address": self.config.address,
            "subnet_cidr": self.config.subnet_cidr,
            "last_command": self.last_command,
            "dry_run": self.dry_run,
        }
