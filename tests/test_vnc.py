import unittest

from device_app.config import VncConfig
from device_app.services.vnc import VncManager


class VncTestCase(unittest.TestCase):
    def test_dry_run_vnc_status(self) -> None:
        manager = VncManager(
            VncConfig(
                enabled=True,
                display=":1",
                geometry="1280x720",
                depth=24,
                vnc_port=5901,
                novnc_port=6080,
                desktop_session="openbox-session",
            ),
            host="0.0.0.0",
            dry_run=True,
        )
        manager.start()
        status = manager.status()

        self.assertTrue(status["enabled"])
        self.assertTrue(status["started"])
        self.assertTrue(status["novnc_running"])
        self.assertEqual(status["novnc_port"], 6080)
        self.assertEqual(status["client_path"], "/vnc.html?autoconnect=1&resize=scale&view_only=0")


if __name__ == "__main__":
    unittest.main()
