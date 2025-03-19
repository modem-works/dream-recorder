from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta

from ffmpeg.protocol import FFmpegProtocol
from ffmpeg.statistics import Statistics


@dataclass(frozen=True)
class Progress:
    """Represents a progress of `FFmpeg` operation.

    Attributes:
        frame: The number of processed frames.
        fps: The processing speed in frame per seconds.
        size: The current size of the media in bytes.
        time: The current time of the media.
        bitrate: The processing speed in kilobits per second.
        speed: The processing speed
    """

    frame: int
    fps: float
    size: int
    time: timedelta
    bitrate: float
    speed: float


class Tracker:
    def __init__(self, ffmpeg: FFmpegProtocol):
        self._ffmpeg = ffmpeg
        self._ffmpeg.on("stderr", self._on_stderr)

    def _on_stderr(self, line: str):
        statistics = Statistics.from_line(line)
        if statistics is not None:
            self._ffmpeg.emit("progress", Progress(**asdict(statistics)))
