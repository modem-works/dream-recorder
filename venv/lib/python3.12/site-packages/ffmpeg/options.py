from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Optional, Union

from ffmpeg import types
from ffmpeg.file import InputFile, OutputFile


def _unpack_options(options: dict[str, Optional[types.Option]]) -> Iterable[Option]:
    for key, values in options.items():
        if not isinstance(values, (list, set, tuple)):
            values = [values]

        for value in values:
            yield Option(key, value)


@dataclass(frozen=True)
class Option:
    key: str
    value: Optional[types.Option] = None

    def build(self) -> Iterable[str]:
        yield f"-{self.key}"

        if self.value is not None:
            yield str(self.value)


class Options:
    def __init__(self):
        self._global_options: list[Option] = []
        self._input_files: list[InputFile] = []
        self._output_files: list[OutputFile] = []

    def option(self, key: str, value: Optional[types.Option] = None):
        self._global_options.append(Option(key, value))

    def input(
        self,
        url: Union[str, os.PathLike],
        options: Optional[dict[str, Optional[types.Option]]] = None,
        **kwargs: Optional[types.Option],
    ):
        url = os.fspath(url)

        options = options if options is not None else {}
        options.update(kwargs)

        self._input_files.append(InputFile(url, [*_unpack_options(options)]))

    def output(
        self,
        url: Union[str, os.PathLike],
        options: Optional[dict[str, Optional[types.Option]]] = None,
        **kwargs: Optional[types.Option],
    ):
        url = os.fspath(url)

        options = options if options is not None else {}
        options.update(kwargs)

        self._output_files.append(OutputFile(url, [*_unpack_options(options)]))

    def build(self) -> Iterable[str]:
        for option in self._global_options:
            yield from option.build()

        for input_file in self._input_files:
            yield from input_file.build()

        for output_file in self._output_files:
            yield from output_file.build()
