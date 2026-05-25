from __future__ import annotations

import asyncio
import base64
import hashlib
import struct
from collections.abc import Awaitable, Callable
from typing import Any

from parrot_studio.ipc.protocol import dumps, parse_command
from parrot_studio.shared.schemas import Event, to_wire


CommandHandler = Callable[[Any], Awaitable[None]]


class _WebSocketClient:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.reader = reader
        self.writer = writer
        self.lock = asyncio.Lock()

    async def handshake(self) -> None:
        header_bytes = await self.reader.readuntil(b"\r\n\r\n")
        headers: dict[str, str] = {}
        for line in header_bytes.decode("latin1").split("\r\n")[1:]:
            if ":" in line:
                name, value = line.split(":", 1)
                headers[name.lower()] = value.strip()
        key = headers.get("sec-websocket-key")
        if not key:
            raise ValueError("Missing Sec-WebSocket-Key")
        accept = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
        ).decode("ascii")
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        )
        self.writer.write(response.encode("ascii"))
        await self.writer.drain()

    async def read_text(self) -> str | None:
        first = await self.reader.readexactly(2)
        opcode = first[0] & 0x0F
        masked = (first[1] & 0x80) != 0
        length = first[1] & 0x7F
        if length == 126:
            length = struct.unpack("!H", await self.reader.readexactly(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", await self.reader.readexactly(8))[0]
        mask = await self.reader.readexactly(4) if masked else b""
        payload = bytearray(await self.reader.readexactly(length))
        if masked:
            for index in range(length):
                payload[index] ^= mask[index % 4]
        if opcode == 0x8:
            return None
        if opcode != 0x1:
            return ""
        return payload.decode("utf-8")

    async def send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        header = bytearray([0x81])
        if len(payload) < 126:
            header.append(len(payload))
        elif len(payload) <= 0xFFFF:
            header.append(126)
            header.extend(struct.pack("!H", len(payload)))
        else:
            header.append(127)
            header.extend(struct.pack("!Q", len(payload)))
        async with self.lock:
            self.writer.write(bytes(header) + payload)
            await self.writer.drain()

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()


class ControlServer:
    def __init__(self) -> None:
        self.port = 0
        self._server: asyncio.AbstractServer | None = None
        self._clients: set[_WebSocketClient] = set()
        self._command_handler: CommandHandler | None = None

    def set_command_handler(self, handler: CommandHandler) -> None:
        self._command_handler = handler

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, "127.0.0.1", 0)
        socket = self._server.sockets[0]
        self.port = int(socket.getsockname()[1])

    async def stop(self) -> None:
        for client in list(self._clients):
            await client.close()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def send_event(self, event: Event) -> None:
        if not self._clients:
            return
        message = dumps(to_wire(event))
        await asyncio.gather(*(client.send_text(message) for client in list(self._clients)), return_exceptions=True)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        client = _WebSocketClient(reader, writer)
        try:
            await client.handshake()
            self._clients.add(client)
            while True:
                raw = await client.read_text()
                if raw is None:
                    break
                if not raw:
                    continue
                command = parse_command(raw)
                if self._command_handler:
                    await self._command_handler(command)
        except (asyncio.IncompleteReadError, ConnectionError, ValueError):
            pass
        finally:
            self._clients.discard(client)
            await client.close()
