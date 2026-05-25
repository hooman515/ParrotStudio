from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Union

from parrot_studio.shared.constants import (
    DEFAULT_TRANSCRIPTION_MODEL,
    DEFAULT_TRANSLATION_MODEL,
)


def now_ms() -> int:
    return int(time.monotonic() * 1000)


@dataclass
class StartVideoJobCommand:
    command: Literal["start_video_job"] = "start_video_job"
    input_path: str = ""
    output_path: str = ""
    transcription_model: str = DEFAULT_TRANSCRIPTION_MODEL
    translation_model: str = DEFAULT_TRANSLATION_MODEL
    source_language: str = "fa"
    target_language: str = "en"
    work_dir: str | None = None
    debug: bool = False
    openai_api_key: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StartVideoJobCommand":
        data = dict(payload)
        data.pop("command", None)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CancelJobCommand:
    command: Literal["cancel_job"] = "cancel_job"


@dataclass
class StatusEvent:
    type: Literal["status"] = "status"
    state: str = "idle"
    message: str = ""
    created_at_ms: int = field(default_factory=now_ms)


@dataclass
class ErrorEvent:
    type: Literal["error"] = "error"
    code: str = "INTERNAL_ERROR"
    message: str = ""
    retryable: bool = False
    created_at_ms: int = field(default_factory=now_ms)


@dataclass
class MetricEvent:
    type: Literal["metric"] = "metric"
    stage: str = ""
    duration_ms: int = 0
    session_id: str = ""
    created_at_ms: int = field(default_factory=now_ms)


@dataclass
class JobProgressEvent:
    type: Literal["job_progress"] = "job_progress"
    stage: str = ""
    progress: float = 0.0
    message: str = ""
    created_at_ms: int = field(default_factory=now_ms)


@dataclass
class JobCompleteEvent:
    type: Literal["job_complete"] = "job_complete"
    output_video_path: str = ""
    subtitle_path: str = ""
    artifact_dir: str = ""
    created_at_ms: int = field(default_factory=now_ms)


Event = Union[StatusEvent, ErrorEvent, MetricEvent, JobProgressEvent, JobCompleteEvent]


def to_wire(value: Event | StartVideoJobCommand | CancelJobCommand) -> dict[str, Any]:
    return asdict(value)
