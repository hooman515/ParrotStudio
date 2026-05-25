from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SubtitleCue:
    index: int
    start: float
    end: float
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JobArtifacts:
    artifact_dir: Path
    audio_dir: Path
    transcript_json: Path
    subtitles_json: Path
    subtitle_srt: Path
    output_video: Path
