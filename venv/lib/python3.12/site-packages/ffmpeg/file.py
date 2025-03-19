from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from ffmpeg.options import Option


@dataclass(frozen=True)
class File:
    url: str
    options: list[Option] = field(default_factory=list)

    def build(self) -> Iterable[str]:
        raise NotImplementedError()


@dataclass(frozen=True)
class InputFile(File):
    def build(self) -> Iterable[str]:
        for option in self.options:
            yield from option.build()

        yield from ["-i", self.url]


@dataclass(frozen=True)
class OutputFile(File):
    def build(self) -> Iterable[str]:
        for option in self.options:
            yield from option.build()

        yield self.url
