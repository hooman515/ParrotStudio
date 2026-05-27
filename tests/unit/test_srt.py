from __future__ import annotations

import unittest

from parrot_studio.video.models import TranscriptSegment
from parrot_studio.video.srt import (
    cues_to_srt,
    seconds_to_srt_time,
    segments_to_cues,
    split_subtitle_text,
    wrap_subtitle_text,
)


class SRTTests(unittest.TestCase):
    def test_seconds_to_srt_time(self) -> None:
        self.assertEqual(seconds_to_srt_time(65.432), "00:01:05,432")

    def test_wrap_limits_to_two_lines(self) -> None:
        wrapped = wrap_subtitle_text(
            "This is a long archival subtitle that should be wrapped into readable lines for playback.",
            width=32,
        )
        self.assertLessEqual(len(wrapped.splitlines()), 2)

    def test_segments_to_srt(self) -> None:
        cues = segments_to_cues([TranscriptSegment(1.0, 3.0, "سلام")], ["Hello there."])
        self.assertEqual(cues[0].index, 1)
        self.assertIn("00:00:01,000 --> 00:00:03,000", cues_to_srt(cues))
        self.assertIn("Hello there.", cues_to_srt(cues))

    def test_subtitle_offset_applies_to_cue_times(self) -> None:
        cues = segments_to_cues([TranscriptSegment(1.0, 3.0, "سلام")], ["Hello there."], offset_seconds=-0.4)

        self.assertEqual(cues[0].start, 0.6)
        self.assertEqual(cues[0].end, 2.6)

    def test_overlap_trims_previous_cue_without_delaying_next_start(self) -> None:
        cues = segments_to_cues(
            [
                TranscriptSegment(1.0, 3.0, "سلام"),
                TranscriptSegment(2.2, 4.0, "خوبی"),
            ],
            ["Hello.", "How are you?"],
        )

        self.assertLess(cues[0].end, cues[1].start)
        self.assertEqual(cues[1].start, 2.2)

    def test_long_translation_splits_into_multiple_readable_cues(self) -> None:
        text = (
            "This first sentence should appear as one readable subtitle. "
            "This second sentence is also kept, and the final sentence should not be lost."
        )
        chunks = split_subtitle_text(text, max_chars=72)
        cues = segments_to_cues([TranscriptSegment(10.0, 16.0, "طولانی")], [text])

        self.assertGreaterEqual(len(chunks), 2)
        self.assertGreaterEqual(len(cues), 2)
        self.assertEqual(cues[0].start, 10.0)
        self.assertEqual(cues[-1].end, 16.0)
        self.assertIn("final sentence", " ".join(cue.text for cue in cues))


if __name__ == "__main__":
    unittest.main()
