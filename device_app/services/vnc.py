from __future__ import annotations

import platform
import shutil
import subprocess
import time
from pathlib import Path

from ..config import VncConfig


class VncManager:
    def __init__(self, config: VncConfig, host: str, dry_run: bool = False) -> None:
        self.config = config
        self.host = host
        self.dry_run = dry_run
        self.vnc_process: subprocess.Popen[str] | None = None
        self.novnc_process: subprocess.Popen[bytes] | None = None
        self.started = False
        self.errors: list[str] = []

    def start(self) -> None:
        self.errors.clear()

        if not self.config.enabled:
            self.started = False
            return

        if self.dry_run or platform.system() != "Linux":
            self.started = True
            return

        x11vnc = shutil.which("x11vnc")
        if not x11vnc:
            self.errors.append("x11vnc command not found")
            self.started = False
            return

        novnc_proxy = self._find_novnc_proxy()
        if not novnc_proxy:
            self.errors.append("novnc_proxy command not found")
            self.started = False
            return

        self._stop_existing()

        try:
            self.vnc_process = subprocess.Popen(
                [
                    x11vnc,
                    self.config.display,
                    "-auth",
                    "guess",
                    "-rfbport",
                    str(self.config.vnc_port),
                    "-localhost",
                    "-forever",
                    "-shared",
                    "-nopw",
                    "-xkb",
                    "-noxdamage",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(1.0)
            if self.vnc_process.poll() is not None:
                stdout, stderr = self.vnc_process.communicate()
                self.errors.append((stderr or stdout or "x11vnc exited immediately").strip())
                self.vnc_process = None
                self.started = False
                return

            self.novnc_process = subprocess.Popen(
                [
                    novnc_proxy,
                    "--listen",
                    str(self.config.novnc_port),
                    "--vnc",
                    f"localhost:{self.config.vnc_port}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                start_new_session=True,
            )
            time.sleep(0.5)
            if self.novnc_process.poll() is not None:
                stdout, stderr = self.novnc_process.communicate()
                self.errors.append((stderr or stdout or b"novnc_proxy exited immediately").decode(errors="replace").strip())
                self.novnc_process = None
                self._stop_existing()
                self.started = False
                return
            self.started = True
        except FileNotFoundError as exc:
            self.errors.append(str(exc))
            self.started = False

    def stop(self) -> None:
        self._stop_existing()

    def status(self) -> dict[str, object]:
        novnc_running = self.started if self.dry_run else (
            self.novnc_process is not None and self.novnc_process.poll() is None
        )
        vnc_running = self.started if self.dry_run else (
            self.vnc_process is not None and self.vnc_process.poll() is None
        )
        return {
            "enabled": self.config.enabled,
            "started": self.started,
            "backend": "x11vnc-live-desktop",
            "display": self.config.display,
            "geometry": self.config.geometry,
            "vnc_port": self.config.vnc_port,
            "novnc_port": self.config.novnc_port,
            "desktop_session": self.config.desktop_session,
            "host_hint": self.host,
            "client_path": "/vnc.html?autoconnect=1&resize=scale&view_only=0",
            "novnc_running": novnc_running,
            "vnc_running": vnc_running,
            "dry_run": self.dry_run,
            "errors": self.errors,
        }

    def _stop_existing(self) -> None:
        if self.vnc_process is not None and self.vnc_process.poll() is None:
            self.vnc_process.terminate()
            try:
                self.vnc_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.vnc_process.kill()
        self.vnc_process = None

        if self.novnc_process is not None and self.novnc_process.poll() is None:
            self.novnc_process.terminate()
            try:
                self.novnc_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.novnc_process.kill()
        self.novnc_process = None

        self.started = False

    def _find_novnc_proxy(self) -> str | None:
        command = shutil.which("novnc_proxy")
        if command:
            return command

        candidate = Path("/usr/share/novnc/utils/novnc_proxy")
        if candidate.exists():
            return str(candidate)
        return None
