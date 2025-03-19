from __future__ import annotations

import concurrent.futures
import io
import os
import signal
import subprocess
from typing import IO, Optional, Union

from pyee import EventEmitter
from typing_extensions import Self

from ffmpeg import types
from ffmpeg.options import Options
from ffmpeg.progress import Tracker
from ffmpeg.utils import create_subprocess, ensure_io, is_windows, read_stream, readlines


class FFmpegError(Exception):
    pass


class FFmpeg(EventEmitter):
    def __init__(self, executable: str = "ffmpeg"):
        """Initialize an `FFmpeg` instance.

        Args:
            executable: The path to the ffmpeg executable. Defaults to "ffmpeg".
        """
        super().__init__()

        self._executable: str = executable
        self._options: Options = Options()

        self._process: subprocess.Popen[bytes]
        self._executed: bool = False
        self._terminated: bool = False

        self._tracker = Tracker(self)  # type: ignore

    def option(self, key: str, value: Optional[types.Option] = None) -> Self:
        """Add a global option `-key` or `-key value`.

        Args:
            key: A key of the global option
            value: A value of the global option. If the option does not require a value, use None. Defaults to None.

        Returns:
            An instance of `FFmpeg` itself, so that calls can be chained.
        """
        self._options.option(key, value)
        return self

    def input(
        self,
        url: Union[str, os.PathLike],
        options: Optional[dict[str, Optional[types.Option]]] = None,
        **kwargs: Optional[types.Option],
    ) -> Self:
        """Add an input file.
           By calling this method multiple times, an arbitrary number of input files can be added.

        Args:
            url: URL for the input file.
            options: Options for the input file. Defaults to None.
            kwargs: Additional options for the input file.

        Returns:
            An instance of `FFmpeg` itself, so that calls can be chained.
        """
        self._options.input(url, options, **kwargs)
        return self

    def output(
        self,
        url: Union[str, os.PathLike],
        options: Optional[dict[str, Optional[types.Option]]] = None,
        **kwargs: Optional[types.Option],
    ) -> Self:
        """Add an output file.
           By calling this method multiple times, an arbitrary number of output files can be specified.

        Args:
            url: URL for the output file.
            options: Options for the output file. Defaults to None.
            kwargs: Additional options for the output file.

        Returns:
            An instance of `FFmpeg` itself, so that calls can be chained.
        """
        self._options.output(url, options, **kwargs)
        return self

    def execute(self, stream: Optional[types.Stream] = None) -> bytes:
        """Execute FFmpeg using specified global options and files.

        Args:
            stream: A stream to input to the standard input. Defaults to None.

        Raises:
            FFmpegError: If FFmpeg is already executed.
            FFmpegError: If FFmpeg process returns non-zero exit status.

        Returns:
            The output to the standard output.
        """
        if self._executed:
            raise FFmpegError("FFmpeg is already executed")

        self._executed = False
        self._terminated = False

        if stream is not None:
            stream = ensure_io(stream)

        arguments = [self._executable, *self._options.build()]
        self.emit("start", arguments)

        self._process = create_subprocess(
            arguments,
            bufsize=0,
            stdin=subprocess.PIPE if stream is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self._executed = True

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self._write_stdin, stream),
                executor.submit(self._read_stdout),
                executor.submit(self._handle_stderr),
                executor.submit(self._process.wait),
            ]

            for future in concurrent.futures.as_completed(futures):
                exception = future.exception()
                if exception is not None:
                    self._process.terminate()
                    raise exception

        self._executed = False

        if self._process.returncode == 0:
            self.emit("completed")
        elif self._terminated:
            self.emit("terminated")
        else:
            raise FFmpegError(f"Non-zero exit status {self._process.returncode}")

        return futures[1].result()

    def terminate(self):
        """Gracefully terminate the running FFmpeg process.

        Raises:
            FFmpegError: If FFmpeg is not executed
        """
        if not self._executed:
            raise FFmpegError("FFmpeg is not executed")

        sigterm = signal.SIGTERM
        if is_windows():
            # On Windows, SIGTERM is an alias for TerminateProcess().
            # To gracefully terminate the FFmpeg process, we should use CTRL_BREAK_EVENT signal.
            # References:
            # - https://docs.python.org/3/library/subprocess.html#subprocess.Popen.send_signal
            # - https://github.com/FFmpeg/FFmpeg/blob/release/5.1/fftools/ffmpeg.c#L371
            sigterm = signal.CTRL_BREAK_EVENT  # type: ignore

        self._terminated = True
        self._process.send_signal(sigterm)

    def _write_stdin(self, stream: Optional[IO[bytes]]):
        if stream is None:
            return

        assert self._process.stdin is not None

        for chunk in read_stream(stream, size=io.DEFAULT_BUFFER_SIZE):
            self._process.stdin.write(chunk)

        self._process.stdin.flush()
        self._process.stdin.close()

    def _read_stdout(self) -> bytes:
        assert self._process.stdout is not None

        buffer = bytearray()
        for chunk in read_stream(self._process.stdout, size=io.DEFAULT_BUFFER_SIZE):
            buffer.extend(chunk)

        self._process.stdout.close()
        return bytes(buffer)

    def _handle_stderr(self):
        assert self._process.stderr is not None

        for line in readlines(self._process.stderr):
            self.emit("stderr", line.decode())

        self._process.stderr.close()
