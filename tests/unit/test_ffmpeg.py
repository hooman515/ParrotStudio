from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from parrot_studio.video.ffmpeg import extract_audio_chunks, mux_selectable_subtitles


class FFMpegTests(unittest.TestCase):
    @patch("parrot_studio.video.ffmpeg.probe_duration")
    @patch("parrot_studio.video.ffmpeg.require_ffmpeg")
    @patch("parrot_studio.video.ffmpeg.subprocess.run")
    def test_extract_audio_chunks_uses_wav_and_measured_offsets(self, run, _require, probe_duration) -> None:
        run.return_value.returncode = 0
        probe_duration.side_effect = [300.012, 14.5]
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            (output_dir / "chunk_0000.wav").touch()
            (output_dir / "chunk_0001.wav").touch()

            chunks = extract_audio_chunks(Path("input.mkv"), output_dir, 300)

        command = run.call_args.args[0]
        self.assertIn("pcm_s16le", command)
        self.assertIn("wav", command)
        self.assertEqual(chunks[0].start, 0.0)
        self.assertEqual(chunks[1].start, 300.012)
        self.assertEqual(chunks[1].duration, 14.5)

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
