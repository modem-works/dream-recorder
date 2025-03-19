import asyncio
import io
import re
import subprocess
from typing import Any, AsyncIterable, Awaitable

from ffmpeg import types
from ffmpeg.utils import is_windows


def create_subprocess(*args: Any, **kwargs: Any) -> Awaitable[asyncio.subprocess.Process]:
    # On Windows, CREATE_NEW_PROCESS_GROUP flag is required to use CTRL_BREAK_EVENT signal,
    # which is required to gracefully terminate the FFmpeg process.
    # Reference: https://docs.python.org/3/library/asyncio-subprocess.html#asyncio.subprocess.Process.send_signal
    if is_windows():
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

    return asyncio.create_subprocess_exec(*args, **kwargs)


def ensure_stream_reader(stream: types.AsyncStream) -> asyncio.StreamReader:
    if isinstance(stream, asyncio.StreamReader):
        return stream

    reader = asyncio.StreamReader()
    reader.feed_data(stream)
    reader.feed_eof()

    return reader


async def read_stream(stream: asyncio.StreamReader, size: int = -1) -> AsyncIterable[bytes]:
    while not stream.at_eof():
        chunk = await stream.read(size)
        if not chunk:
            break

        yield chunk


async def readlines(stream: asyncio.StreamReader) -> AsyncIterable[bytes]:
    pattern = re.compile(rb"[\r\n]+")

    buffer = bytearray()
    async for chunk in read_stream(stream, io.DEFAULT_BUFFER_SIZE):
        buffer.extend(chunk)

        lines = pattern.split(buffer)
        buffer[:] = lines.pop(-1)  # keep the last line that could be partial

        for line in lines:
            yield line

    if buffer:
        yield bytes(buffer)
