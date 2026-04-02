from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .config import DeviceConfig
from .services.ble import BleAdvertiser
from .services.gpio import GpioController
from .services.hotspot import HotspotManager
from .services.terminal import TerminalManager
from .services.vnc import VncManager

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class DeviceServer:
    def __init__(
        self,
        host: str,
        port: int,
        config: DeviceConfig,
        hotspot: HotspotManager,
        ble: BleAdvertiser,
        vnc: VncManager,
        gpio: GpioController,
        terminals: TerminalManager,
    ) -> None:
        self.host = host
        self.port = port
        self.config = config
        self.hotspot = hotspot
        self.ble = ble
        self.vnc = vnc
        self.gpio = gpio
        self.terminals = terminals

        handler = self._build_handler()
        self.httpd = ThreadingHTTPServer((host, port), handler)

    def serve_forever(self) -> None:
        print(f"Device server listening on http://{self.host}:{self.port}")
        try:
            self.httpd.serve_forever()
        finally:
            self.vnc.stop()
            self.terminals.close_all()

    def _build_handler(self) -> type[BaseHTTPRequestHandler]:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                try:
                    parsed = urlparse(self.path)

                    if parsed.path == "/":
                        return self._serve_file("index.html", "text/html; charset=utf-8")
                    if parsed.path == "/app.js":
                        return self._serve_file("app.js", "application/javascript; charset=utf-8")
                    if parsed.path == "/ui.js":
                        return self._serve_file("ui.js", "application/javascript; charset=utf-8")
                    if parsed.path == "/styles.css":
                        return self._serve_file("styles.css", "text/css; charset=utf-8")
                    if parsed.path == "/api/status":
                        return self._json_response(
                            {
                                "device": server.config.to_public_dict(),
                                "runtime": {
                                    "hotspot": server.hotspot.status(),
                                    "ble": server.ble.status(),
                                    "vnc": server.vnc.status(),
                                    "gpio": server.gpio.status(),
                                },
                            }
                        )
                    if parsed.path == "/healthz":
                        return self._json_response(
                            {
                                "ok": True,
                                "device_id": server.config.device_id,
                                "device_name": server.config.device_name,
                                "bind": f"{server.host}:{server.port}",
                            }
                        )
                    if parsed.path.startswith("/api/terminal/session/"):
                        session_id = parsed.path.rsplit("/", 1)[-1]
                        query = parse_qs(parsed.query)
                        offset = int(query.get("offset", ["0"])[0])
                        return self._json_response(server.terminals.read(session_id, offset))
                    if parsed.path == "/api/gpio":
                        return self._json_response(server.gpio.status())

                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                except KeyError as exc:
                    self._json_error(HTTPStatus.NOT_FOUND, f"Unknown resource: {exc}")
                except ValueError as exc:
                    self._json_error(HTTPStatus.BAD_REQUEST, str(exc))

            def do_POST(self) -> None:
                try:
                    parsed = urlparse(self.path)
                    payload = self._read_json_body()

                    if parsed.path == "/api/runtime/start":
                        server.hotspot.start()
                        server.ble.start()
                        server.vnc.start()
                        return self._json_response(
                            {
                                "hotspot": server.hotspot.status(),
                                "ble": server.ble.status(),
                                "vnc": server.vnc.status(),
                            }
                        )
                    if parsed.path == "/api/vnc/start":
                        server.vnc.start()
                        return self._json_response(server.vnc.status())
                    if parsed.path == "/api/terminal/session":
                        return self._json_response(server.terminals.create_session())
                    if parsed.path.startswith("/api/terminal/session/") and parsed.path.endswith("/input"):
                        session_id = re.sub(r"^/api/terminal/session/|/input$", "", parsed.path)
                        server.terminals.write(session_id, payload.get("input", ""))
                        return self._json_response({"ok": True})
                    if parsed.path == "/api/gpio/write":
                        pin = int(payload["pin"])
                        value = int(payload["value"])
                        server.gpio.write(pin, value)
                        return self._json_response(server.gpio.status())

                    self.send_error(HTTPStatus.NOT_FOUND, "Not found")
                except KeyError as exc:
                    self._json_error(HTTPStatus.NOT_FOUND, f"Unknown resource: {exc}")
                except ValueError as exc:
                    self._json_error(HTTPStatus.BAD_REQUEST, str(exc))

            def _serve_file(self, relative_path: str, content_type: str) -> None:
                path = STATIC_DIR / relative_path
                if not path.exists():
                    self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                    return
                data = path.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _read_json_body(self) -> dict[str, Any]:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length == 0:
                    return {}
                raw = self.rfile.read(content_length).decode("utf-8")
                return json.loads(raw)

            def _json_response(self, payload: dict[str, Any]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _json_error(self, status: HTTPStatus, message: str) -> None:
                body = json.dumps({"error": message}).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        return Handler
