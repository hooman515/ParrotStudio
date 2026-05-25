from __future__ import annotations

import textwrap

from parrot_studio.video.models import SubtitleCue, TranscriptSegment


def seconds_to_srt_time(value: float) -> str:
    milliseconds = max(0, int(round(value * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def cues_to_srt(cues: list[SubtitleCue]) -> str:
    blocks: list[str] = []
    for cue in cues:
        blocks.append(
            "\n".join(
                [
                    str(cue.index),
                    f"{seconds_to_srt_time(cue.start)} --> {seconds_to_srt_time(cue.end)}",
                    cue.text,
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def wrap_subtitle_text(text: str, width: int = 42, max_lines: int = 2) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    lines = textwrap.wrap(cleaned, width=width, break_long_words=False, break_on_hyphens=False)
    if len(lines) <= max_lines:
        return "\n".join(lines)
    kept = lines[:max_lines]
    kept[-1] = kept[-1].rstrip(" .,;:") + "..."
    return "\n".join(kept)


def segments_to_cues(segments: list[TranscriptSegment], translated_texts: list[str]) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    previous_end = 0.0
    for index, (segment, text) in enumerate(zip(segments, translated_texts), start=1):
        wrapped = wrap_subtitle_text(text)
        if not wrapped:
            continue
        start = max(previous_end, segment.start)
        end = max(start + 1.2, segment.end)
        if cues and start < cues[-1].end:
            start = cues[-1].end
        cues.append(SubtitleCue(index=len(cues) + 1, start=start, end=end, text=wrapped))
        previous_end = end
    return cues
