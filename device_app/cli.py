from __future__ import annotations

import argparse
from pathlib import Path

from .app import DeviceApplication


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Raspberry Pi classroom device MVP")
    parser.add_argument("--config", default="config/device.sample.json", help="Path to device config JSON")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    parser.add_argument("--dry-run", action="store_true", help="Do not issue hardware control commands")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    app = DeviceApplication(
      config_path=Path(args.config),
      host=args.host,
      port=args.port,
      dry_run=args.dry_run,
    )
    app.run()
    return 0
