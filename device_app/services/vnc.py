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

        vncserver = shutil.which("vncserver")
        if not vncserver:
            self.errors.append("vncserver command not found")
            self.started = False
            return

        novnc_proxy = self._find_novnc_proxy()
        if not novnc_proxy:
            self.errors.append("novnc_proxy command not found")
            self.started = False
            return

        self._ensure_xstartup()
        self._stop_existing()

        try:
            subprocess.run(
                [
                    vncserver,
                    self.config.display,
                    "-localhost",
                    "yes",
                    "-geometry",
                    self.config.geometry,
                    "-depth",
                    str(self.config.depth),
                    "-xstartup",
                    str(self._xstartup_path()),
                    "-SecurityTypes",
                    "None",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.novnc_process = subprocess.Popen(
                [
                    novnc_proxy,
                    "--listen",
                    str(self.config.novnc_port),
                    "--vnc",
                    f"localhost:{self.config.vnc_port}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            self.started = True
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            self.errors.append(str(exc))
            self.started = False

    def stop(self) -> None:
        self._stop_existing()

    def status(self) -> dict[str, object]:
        novnc_running = self.started if self.dry_run else (
            self.novnc_process is not None and self.novnc_process.poll() is None
        )
        return {
            "enabled": self.config.enabled,
            "started": self.started,
            "display": self.config.display,
            "geometry": self.config.geometry,
            "vnc_port": self.config.vnc_port,
            "novnc_port": self.config.novnc_port,
            "desktop_session": self.config.desktop_session,
            "host_hint": self.host,
            "client_path": "/vnc.html?autoconnect=1&resize=scale&view_only=0",
            "novnc_running": novnc_running,
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

        if self.dry_run or platform.system() != "Linux":
            return

        vncserver = shutil.which("vncserver")
        if vncserver:
            subprocess.run(
                [vncserver, "-kill", self.config.display],
                check=False,
                capture_output=True,
                text=True,
            )

    def _find_novnc_proxy(self) -> str | None:
        command = shutil.which("novnc_proxy")
        if command:
            return command

        candidate = Path("/usr/share/novnc/utils/novnc_proxy")
        if candidate.exists():
            return str(candidate)
        return None

    def _ensure_xstartup(self) -> None:
        xstartup = self._xstartup_path()
        xstartup.parent.mkdir(parents=True, exist_ok=True)
        session = self.config.desktop_session.strip()
        xstartup.write_text(
            "#!/usr/bin/env bash\n"
            "unset SESSION_MANAGER\n"
            "unset DBUS_SESSION_BUS_ADDRESS\n"
            "xsetroot -solid '#0f172a'\n"
            f"if command -v {session} >/dev/null 2>&1; then\n"
            f"  {session} &\n"
            "elif command -v startlxde >/dev/null 2>&1; then\n"
            "  startlxde &\n"
            "elif command -v openbox-session >/dev/null 2>&1; then\n"
            "  openbox-session &\n"
            "fi\n"
            "if command -v xterm >/dev/null 2>&1; then\n"
            "  xterm -fa 'Monospace' -fs 12 -bg '#111827' -fg '#c7f9cc' &\n"
            "fi\n"
            "wait\n",
            encoding="utf-8",
        )
        xstartup.chmod(0o755)

    def _xstartup_path(self) -> Path:
        return Path.home() / ".vnc" / "xstartup"
