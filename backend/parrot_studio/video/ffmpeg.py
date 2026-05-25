from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from parrot_studio.shared.errors import ProviderUnavailableError


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise ProviderUnavailableError("Install ffmpeg and ffprobe to process video files.", retryable=False)


def probe_duration(input_path: Path) -> float:
    require_ffmpeg()
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(input_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def extract_audio_chunks(input_path: Path, output_dir: Path, chunk_seconds: int) -> list[Path]:
    require_ffmpeg()
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / "chunk_%04d.m4a"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-reset_timestamps",
            "1",
            str(pattern),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(output_dir.glob("chunk_*.m4a"))


def mux_selectable_subtitles(input_path: Path, subtitle_path: Path, output_path: Path) -> None:
    require_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    copy_command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-i",
        str(subtitle_path),
        "-map",
        "0",
        "-map",
        "1",
        "-c",
        "copy",
        "-c:s",
        "mov_text",
        "-metadata:s:s:0",
        "language=eng",
        str(output_path),
    ]
    result = subprocess.run(copy_command, capture_output=True, text=True)
    if result.returncode == 0:
        return

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-i",
            str(subtitle_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-map",
            "1",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "slow",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            "language=eng",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
