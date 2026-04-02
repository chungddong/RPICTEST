import time
import unittest

from device_app.services.terminal import TerminalManager


class TerminalTestCase(unittest.TestCase):
    def test_terminal_session_round_trip(self) -> None:
        terminals = TerminalManager()
        session = terminals.create_session()
        session_id = session["session_id"]

        terminals.write(session_id, "echo hello\n")
        time.sleep(0.3)
        payload = terminals.read(session_id, 0)

        self.assertEqual(payload["session_id"], session_id)
        self.assertIn("output", payload)
        self.assertGreaterEqual(payload["offset"], len(payload["output"]))

        terminals.close_all()


if __name__ == "__main__":
    unittest.main()
