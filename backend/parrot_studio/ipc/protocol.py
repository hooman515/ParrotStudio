from __future__ import annotations

import json
from typing import Any

from parrot_studio.shared.schemas import CancelJobCommand, StartVideoJobCommand


def parse_command(raw: str) -> StartVideoJobCommand | CancelJobCommand:
    payload: dict[str, Any] = json.loads(raw)
    command = payload.get("command")
    if command == "start_video_job":
        return StartVideoJobCommand.from_dict(payload)
    if command == "cancel_job":
        return CancelJobCommand()
    raise ValueError(f"Unknown command: {command}")


def dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"))
