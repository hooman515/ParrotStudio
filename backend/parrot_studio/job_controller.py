from __future__ import annotations

import asyncio

from parrot_studio.diagnostics.logging import configure_logging
from parrot_studio.shared.errors import error_info
from parrot_studio.shared.schemas import (
    CancelJobCommand,
    ErrorEvent,
    JobCompleteEvent,
    StartVideoJobCommand,
    StatusEvent,
)
from parrot_studio.video.pipeline import VideoJobPipeline


class JobController:
    def __init__(self, event_sink) -> None:
        self.event_sink = event_sink
        self._task: asyncio.Task | None = None
        self._logger = configure_logging(False)

    async def handle_command(self, command: StartVideoJobCommand | CancelJobCommand) -> None:
        if isinstance(command, CancelJobCommand):
            await self.cancel()
            return
        await self.start(command)

    async def start(self, command: StartVideoJobCommand) -> None:
        if self._task and not self._task.done():
            await self.event_sink(ErrorEvent(code="JOB_RUNNING", message="A video job is already running.", retryable=False))
            return
        self._logger = configure_logging(command.debug)
        await self.event_sink(StatusEvent(state="starting", message="Starting video subtitle job"))
        self._task = asyncio.create_task(self._run_job(command))

    async def cancel(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            await self.event_sink(StatusEvent(state="idle", message="Video job cancelled"))

    async def stop(self) -> None:
        await self.cancel()

    async def _run_job(self, command: StartVideoJobCommand) -> None:
        try:
            pipeline = VideoJobPipeline(self.event_sink)
            await self.event_sink(StatusEvent(state="processing", message="Processing video"))
            artifacts = await pipeline.run(command)
            await self.event_sink(
                JobCompleteEvent(
                    output_video_path=str(artifacts.output_video),
                    subtitle_path=str(artifacts.subtitle_srt),
                    artifact_dir=str(artifacts.artifact_dir),
                )
            )
            await self.event_sink(StatusEvent(state="complete", message="Export complete"))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            info = error_info(exc)
            self._logger.error("Video job error code=%s retryable=%s message=%s", info.code, info.retryable, info.message)
            await self.event_sink(ErrorEvent(code=info.code, message=info.message, retryable=info.retryable))
