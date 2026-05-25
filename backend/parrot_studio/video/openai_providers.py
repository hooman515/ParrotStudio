from __future__ import annotations

from pathlib import Path

from parrot_studio.shared.errors import MissingAPIKeyError, NetworkFailureError
from parrot_studio.video.models import TranscriptSegment


class OpenAIVideoProviders:
    def __init__(self, *, api_key: str, transcription_model: str, translation_model: str) -> None:
        self.api_key = api_key
        self.transcription_model = transcription_model
        self.translation_model = translation_model

    async def transcribe_chunk(self, audio_path: Path, *, offset_seconds: float, language: str) -> list[TranscriptSegment]:
        if not self.api_key:
            raise MissingAPIKeyError("Add your OpenAI API key in Settings before processing video.")
        try:
            import httpx

            data = {
                "model": self.transcription_model,
                "language": language,
                "response_format": "verbose_json" if self.transcription_model == "whisper-1" else "json",
            }
            if self.transcription_model == "whisper-1":
                data["timestamp_granularities[]"] = "segment"

            async with httpx.AsyncClient(timeout=180.0) as client:
                with audio_path.open("rb") as audio:
                    response = await client.post(
                        "https://api.openai.com/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        data=data,
                        files={"file": (audio_path.name, audio, "audio/mp4")},
                    )
            response.raise_for_status()
            data = response.json()
            if "segments" in data:
                return [
                    TranscriptSegment(
                        start=offset_seconds + float(item.get("start", 0)),
                        end=offset_seconds + float(item.get("end", item.get("start", 0) + 2)),
                        text=str(item.get("text", "")).strip(),
                    )
                    for item in data["segments"]
                    if str(item.get("text", "")).strip()
                ]
            text = str(data.get("text", "")).strip()
            return [TranscriptSegment(start=offset_seconds, end=offset_seconds + 30.0, text=text)] if text else []
        except MissingAPIKeyError:
            raise
        except Exception as exc:
            raise NetworkFailureError(f"Could not transcribe audio chunk {audio_path.name}: {exc}", retryable=True) from exc

    async def translate_segment(self, segment: TranscriptSegment, *, source_language: str, target_language: str) -> str:
        if not self.api_key:
            raise MissingAPIKeyError("Add your OpenAI API key in Settings before processing video.")
        try:
            import httpx

            prompt = (
                "Translate this Persian/Farsi subtitle segment into natural archival English subtitles. "
                "Preserve meaning, names, tone, and intent. Output only the English subtitle text.\n\n"
                f"Source language: {source_language}\nTarget language: {target_language}\n"
                f"Timing: {segment.start:.2f}-{segment.end:.2f}s\n"
                f"Text: {segment.text}"
            )
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.translation_model,
                        "temperature": 0.1,
                        "max_tokens": 180,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert audiovisual subtitle translator for Persian/Farsi films.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
            response.raise_for_status()
            return str(response.json()["choices"][0]["message"]["content"]).strip()
        except MissingAPIKeyError:
            raise
        except Exception as exc:
            raise NetworkFailureError(f"Could not translate subtitle segment: {exc}", retryable=True) from exc
