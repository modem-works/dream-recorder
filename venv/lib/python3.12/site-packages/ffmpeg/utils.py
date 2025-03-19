from __future__ import annotations

import io
import re
import subprocess
import sys
from datetime import timedelta
from typing import IO, Any, Iterable

from ffmpeg import types


def parse_time(time: str) -> timedelta:
    match = re.search(r"(-?\d+):(\d+):(\d+)\.(\d+)", time)
    assert match is not None

    return timedelta(
        hours=int(match.group(1)),
        minutes=int(match.group(2)),
        seconds=int(match.group(3)),
        milliseconds=int(match.group(4)) * 10,
    )


def is_windows() -> bool:
    return sys.platform == "win32"


def create_subprocess(*args: Any, **kwargs: Any) -> subprocess.Popen:
    # On Windows, CREATE_NEW_PROCESS_GROUP flag is required to use CTRL_BREAK_EVENT signal,
    # which is required to gracefully terminate the FFmpeg process.
    # Reference: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.send_signal
    if is_windows():
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore

    return subprocess.Popen(*args, **kwargs)


def ensure_io(stream: types.Stream) -> IO[bytes]:
    if isinstance(stream, bytes):
        stream = io.BytesIO(stream)

    return stream


def read_stream(stream: IO[bytes], size: int = -1) -> Iterable[bytes]:
    while True:
        chunk = stream.read(size)
        if not chunk:
            break

        yield chunk


def readlines(stream: IO[bytes]) -> Iterable[bytes]:
    pattern = re.compile(rb"[\r\n]+")

    buffer = bytearray()
    for chunk in read_stream(stream, io.DEFAULT_BUFFER_SIZE):
        buffer.extend(chunk)

        lines = pattern.split(buffer)
        buffer[:] = lines.pop(-1)  # keep the last line that could be partial

        yield from lines

    if buffer:
        yield bytes(buffer)
