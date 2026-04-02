import unittest
from pathlib import Path

from device_app.config import load_device_config


class ConfigTestCase(unittest.TestCase):
    def test_load_device_config_masks_password(self) -> None:
        config = load_device_config(Path("config/device.sample.json"))
        public = config.to_public_dict()
        self.assertEqual(public["hotspot"]["password"], "***")
        self.assertEqual(public["device_id"], "rpic-001")


if __name__ == "__main__":
    unittest.main()
