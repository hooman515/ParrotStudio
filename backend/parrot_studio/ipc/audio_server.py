from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Awaitable, Callable

from parrot_studio.audio.ingest import AudioFrameAccumulator


FrameHandler = Callable[[bytes], Awaitable[None]]


class AudioServer:
    def __init__(self, socket_path: str, frame_handler: FrameHandler) -> None:
        self.socket_path = socket_path
        self.frame_handler = frame_handler
        self._server: asyncio.AbstractServer | None = None

    async def start(self) -> None:
        path = Path(self.socket_path)
        if path.exists():
            path.unlink()
        self._server = await asyncio.start_unix_server(self._handle_client, path=self.socket_path)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        try:
            os.unlink(self.socket_path)
        except FileNotFoundError:
            pass

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        accumulator = AudioFrameAccumulator()
        try:
            while data := await reader.read(4096):
                for frame in accumulator.feed(data):
                    await self.frame_handler(frame)
        finally:
            writer.close()
            await writer.wait_closed()
