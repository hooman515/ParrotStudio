from __future__ import annotations

import textwrap

from parrot_studio.video.models import SubtitleCue, TranscriptSegment


MIN_CUE_SECONDS = 0.35
OVERLAP_GAP_SECONDS = 0.05


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
    for segment, text in zip(segments, translated_texts):
        wrapped = wrap_subtitle_text(text)
        if not wrapped:
            continue
        start = max(0.0, segment.start)
        end = max(start + MIN_CUE_SECONDS, segment.end)
        cues.append(SubtitleCue(index=len(cues) + 1, start=start, end=end, text=wrapped))

    for previous, current in zip(cues, cues[1:]):
        if previous.end > current.start:
            trimmed_end = current.start - OVERLAP_GAP_SECONDS
            previous.end = max(previous.start + 0.05, trimmed_end)

    return cues
