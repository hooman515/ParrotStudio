from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable

from parrot_studio.shared.constants import DEFAULT_CHUNK_SECONDS
from parrot_studio.shared.schemas import JobProgressEvent, StartVideoJobCommand
from parrot_studio.video.ffmpeg import extract_audio_chunks, mux_selectable_subtitles, probe_duration
from parrot_studio.video.models import JobArtifacts, TranscriptSegment
from parrot_studio.video.openai_providers import OpenAIVideoProviders
from parrot_studio.video.srt import cues_to_srt, segments_to_cues


ProgressSink = Callable[[JobProgressEvent], Awaitable[None]]


class VideoJobPipeline:
    def __init__(self, progress_sink: ProgressSink) -> None:
        self.progress_sink = progress_sink

    async def run(self, command: StartVideoJobCommand) -> JobArtifacts:
        input_path = Path(command.input_path).expanduser()
        output_path = Path(command.output_path).expanduser()
        artifacts = self._artifacts(input_path, output_path, command.work_dir)
        artifacts.audio_dir.mkdir(parents=True, exist_ok=True)

        await self._progress("inspect", 0.03, "Inspecting video")
        duration = probe_duration(input_path)

        await self._progress("extract_audio", 0.10, "Extracting audio")
        chunks = extract_audio_chunks(input_path, artifacts.audio_dir, DEFAULT_CHUNK_SECONDS)

        providers = OpenAIVideoProviders(
            api_key=command.openai_api_key,
            transcription_model=command.transcription_model,
            translation_model=command.translation_model,
        )

        transcript_segments: list[TranscriptSegment] = []
        for index, chunk in enumerate(chunks):
            progress = 0.15 + (0.35 * ((index + 1) / max(1, len(chunks))))
            await self._progress("transcribe", progress, f"Transcribing audio chunk {index + 1} of {len(chunks)}")
            transcript_segments.extend(
                await providers.transcribe_chunk(
                    chunk.path,
                    offset_seconds=chunk.start,
                    language=command.source_language,
                )
            )
        transcript_segments = [segment for segment in transcript_segments if segment.start <= duration]
        artifacts.transcript_json.write_text(
            json.dumps([segment.to_dict() for segment in transcript_segments], indent=2),
            encoding="utf-8",
        )

        translated: list[str] = []
        for index, segment in enumerate(transcript_segments):
            progress = 0.52 + (0.30 * ((index + 1) / max(1, len(transcript_segments))))
            await self._progress("translate", progress, f"Translating subtitle {index + 1} of {len(transcript_segments)}")
            translated.append(
                await providers.translate_segment(
                    segment,
                    source_language=command.source_language,
                    target_language=command.target_language,
                )
            )

        await self._progress("subtitles", 0.86, "Generating subtitle track")
        cues = segments_to_cues(transcript_segments, translated)
        artifacts.subtitles_json.write_text(json.dumps([asdict(cue) for cue in cues], indent=2), encoding="utf-8")
        artifacts.subtitle_srt.write_text(cues_to_srt(cues), encoding="utf-8")

        await self._progress("mux", 0.94, "Embedding selectable subtitles")
        mux_selectable_subtitles(input_path, artifacts.subtitle_srt, artifacts.output_video)

        await self._progress("complete", 1.0, "Video export complete")
        return artifacts

    def _artifacts(self, input_path: Path, output_path: Path, work_dir: str | None) -> JobArtifacts:
        root = (
            Path(work_dir).expanduser()
            if work_dir
            else Path.home()
            / "Library"
            / "Application Support"
            / "Parrot Studio"
            / "Jobs"
            / f"{input_path.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        root.mkdir(parents=True, exist_ok=True)
        return JobArtifacts(
            artifact_dir=root,
            audio_dir=root / "audio",
            transcript_json=root / "transcript.fa.json",
            subtitles_json=root / "subtitles.en.json",
            subtitle_srt=output_path.with_suffix(".en.srt"),
            output_video=output_path,
        )

    async def _progress(self, stage: str, progress: float, message: str) -> None:
        await self.progress_sink(JobProgressEvent(stage=stage, progress=progress, message=message))
