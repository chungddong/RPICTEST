from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

from ..config import VncConfig


class VncManager:
    def __init__(self, config: VncConfig, host: str, dry_run: bool = False) -> None:
        self.config = config
        self.host = host
        self.dry_run = dry_run
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

        novnc_proxy = self._find_novnc_proxy()
        if not novnc_proxy:
            self.errors.append("novnc_proxy command not found")
            self.started = False
            return

        self._stop_existing()

        if not self._wait_for_builtin_vnc():
            self.errors.append(
                f"Built-in VNC server is not listening on localhost:{self.config.vnc_port}. "
                "Enable VNC and boot to the desktop with auto-login."
            )
            self.started = False
            return

        try:
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
        vnc_running = self.started if self.dry_run else self._check_local_vnc_server()
        return {
            "enabled": self.config.enabled,
            "started": self.started,
            "backend": "system-vnc-live-desktop",
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

    def _check_local_vnc_server(self) -> bool:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            return sock.connect_ex(("127.0.0.1", self.config.vnc_port)) == 0

    def _wait_for_builtin_vnc(self) -> bool:
        import time

        for _ in range(20):
            if self._check_local_vnc_server():
                return True
            time.sleep(0.3)
        return False
