from __future__ import annotations

from pathlib import Path

from .config import load_device_config
from .server import DeviceServer
from .services.ble import BleAdvertiser
from .services.gpio import GpioController
from .services.hotspot import HotspotManager
from .services.terminal import TerminalManager


class DeviceApplication:
    def __init__(self, config_path: Path, host: str, port: int, dry_run: bool = False) -> None:
        self.config = load_device_config(config_path)
        self.host = host
        self.port = port
        self.dry_run = dry_run

        self.hotspot = HotspotManager(self.config.hotspot, dry_run=dry_run)
        self.ble = BleAdvertiser(self.config.ble, self.config.device_id, dry_run=dry_run)
        self.gpio = GpioController(self.config.gpio, dry_run=dry_run)
        self.terminals = TerminalManager()

        self.server = DeviceServer(
            host=host,
            port=port,
            config=self.config,
            hotspot=self.hotspot,
            ble=self.ble,
            gpio=self.gpio,
            terminals=self.terminals,
        )

    def run(self) -> None:
        self.hotspot.start()
        self.ble.start()
        self.server.serve_forever()
