from __future__ import annotations

import re
import textwrap

from parrot_studio.video.models import SubtitleCue, TranscriptSegment


MIN_CUE_SECONDS = 0.35
OVERLAP_GAP_SECONDS = 0.05
MAX_CUE_CHARS = 84


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


def split_subtitle_text(text: str, max_chars: int = MAX_CUE_CHARS) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[str] = []
    current = ""
    for sentence in _sentence_fragments(cleaned):
        fragments = _word_chunks(sentence, max_chars) if len(sentence) > max_chars else [sentence]
        for fragment in fragments:
            candidate = f"{current} {fragment}".strip()
            if current and len(candidate) > max_chars:
                chunks.append(current)
                current = fragment
            else:
                current = candidate

    if current:
        chunks.append(current)
    return chunks


def _sentence_fragments(text: str) -> list[str]:
    fragments = [match.group(0).strip() for match in re.finditer(r"[^.!?]+[.!?]?", text)]
    return [fragment for fragment in fragments if fragment] or [text]


def _word_chunks(text: str, max_chars: int) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def segments_to_cues(
    segments: list[TranscriptSegment],
    translated_texts: list[str],
    *,
    offset_seconds: float = 0.0,
) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    for segment, text in zip(segments, translated_texts):
        text_chunks = split_subtitle_text(text)
        if not text_chunks:
            continue
        segment_start = max(0.0, segment.start + offset_seconds)
        segment_end = max(segment_start + MIN_CUE_SECONDS, segment.end + offset_seconds)
        cue_ranges = _split_time_range(segment_start, segment_end, len(text_chunks))
        for text_chunk, (start, end) in zip(text_chunks, cue_ranges):
            wrapped = wrap_subtitle_text(text_chunk)
            if wrapped:
                cues.append(SubtitleCue(index=len(cues) + 1, start=start, end=end, text=wrapped))

    for previous, current in zip(cues, cues[1:]):
        if previous.end > current.start:
            trimmed_end = current.start - OVERLAP_GAP_SECONDS
            previous.end = max(previous.start + 0.05, trimmed_end)

    return cues


def _split_time_range(start: float, end: float, count: int) -> list[tuple[float, float]]:
    if count <= 1:
        return [(start, end)]
    duration = max(MIN_CUE_SECONDS * count, end - start)
    cue_duration = duration / count
    return [
        (
            start + (index * cue_duration),
            start + ((index + 1) * cue_duration),
        )
        for index in range(count)
    ]
