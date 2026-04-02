from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class HotspotConfig:
    ssid: str
    password: str
    interface: str
    address: str
    subnet_cidr: str


@dataclass(slots=True)
class BleConfig:
    enabled: bool
    local_name: str
    service_uuid: str
    advertised_fields: dict[str, Any]


@dataclass(slots=True)
class GpioConfig:
    pins: list[int]


@dataclass(slots=True)
class VncConfig:
    enabled: bool
    display: str
    geometry: str
    depth: int
    vnc_port: int
    novnc_port: int
    desktop_session: str


@dataclass(slots=True)
class DeviceConfig:
    device_id: str
    device_name: str
    hotspot: HotspotConfig
    ble: BleConfig
    vnc: VncConfig
    gpio: GpioConfig

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["hotspot"]["password"] = "***"
        return data


def load_device_config(path: Path) -> DeviceConfig:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    vnc_defaults = {
        "enabled": True,
        "display": ":0",
        "geometry": "desktop-live",
        "depth": 24,
        "vnc_port": 5900,
        "novnc_port": 6080,
        "desktop_session": "system-desktop",
    }

    return DeviceConfig(
        device_id=raw["device_id"],
        device_name=raw["device_name"],
        hotspot=HotspotConfig(**raw["hotspot"]),
        ble=BleConfig(**raw["ble"]),
        vnc=VncConfig(**(vnc_defaults | raw.get("vnc", {}))),
        gpio=GpioConfig(**raw["gpio"]),
    )
