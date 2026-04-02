from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import asdict

from ..config import GpioConfig


class GpioController:
    def __init__(self, config: GpioConfig, dry_run: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self.state = {pin: 0 for pin in config.pins}

    def write(self, pin: int, value: int) -> None:
        if pin not in self.state:
            raise ValueError(f"Pin {pin} is not configured")
        if value not in (0, 1):
            raise ValueError("GPIO value must be 0 or 1")

        self.state[pin] = value

        if self.dry_run or platform.system() != "Linux":
            return

        tool = shutil.which("pinctrl") or shutil.which("raspi-gpio")
        if not tool:
            return

        command = (
            [tool, "set", str(pin), "op", "dh" if value else "dl"]
            if tool.endswith("pinctrl")
            else [tool, "set", str(pin), "op", "dh" if value else "dl"]
        )
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    def status(self) -> dict[str, object]:
        return {
            "pins": [{"pin": pin, "value": value} for pin, value in sorted(self.state.items())],
            "dry_run": self.dry_run,
        }
