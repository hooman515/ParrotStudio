from __future__ import annotations

import json
import unittest

from parrot_studio.ipc.protocol import parse_command
from parrot_studio.shared.schemas import CancelJobCommand, StartVideoJobCommand


class ProtocolTests(unittest.TestCase):
    def test_parse_start_video_job(self) -> None:
        command = parse_command(
            json.dumps(
                {
                    "command": "start_video_job",
                    "input_path": "/tmp/input.mkv",
                    "output_path": "/tmp/output.mp4",
                    "openai_api_key": "sk-test",
                }
            )
        )
        self.assertIsInstance(command, StartVideoJobCommand)
        self.assertEqual(command.input_path, "/tmp/input.mkv")
        self.assertEqual(command.output_path, "/tmp/output.mp4")

    def test_parse_cancel_job(self) -> None:
        self.assertIsInstance(parse_command('{"command":"cancel_job"}'), CancelJobCommand)


if __name__ == "__main__":
    unittest.main()
