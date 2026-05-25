from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from parrot_studio.video.ffmpeg import mux_selectable_subtitles


class FFMpegTests(unittest.TestCase):
    @patch("parrot_studio.video.ffmpeg.require_ffmpeg")
    @patch("parrot_studio.video.ffmpeg.subprocess.run")
    def test_mux_tries_stream_copy_first(self, run, _require) -> None:
        run.return_value.returncode = 0
        mux_selectable_subtitles(Path("input.mkv"), Path("subs.srt"), Path("out.mp4"))
        command = run.call_args.args[0]
        self.assertIn("-c", command)
        self.assertIn("copy", command)
        self.assertIn("mov_text", command)

    @patch("parrot_studio.video.ffmpeg.require_ffmpeg")
    @patch("parrot_studio.video.ffmpeg.subprocess.run")
    def test_mux_falls_back_to_transcode(self, run, _require) -> None:
        first = Mock(returncode=1)
        second = Mock(returncode=0)
        run.side_effect = [first, second]
        mux_selectable_subtitles(Path("input.mkv"), Path("subs.srt"), Path("out.mp4"))
        fallback = run.call_args.args[0]
        self.assertIn("libx264", fallback)
        self.assertIn("aac", fallback)


if __name__ == "__main__":
    unittest.main()
