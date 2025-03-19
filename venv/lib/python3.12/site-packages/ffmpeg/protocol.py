from __future__ import annotations

import os
from typing import Any, Callable, Optional, Union

from typing_extensions import Protocol, Self, overload

from ffmpeg import types


class FFmpegProtocol(Protocol):
    def __init__(self, executable: str = "ffmpeg"):
        ...

    def option(self, key: str, value: Optional[types.Option] = None) -> Self:
        ...

    def input(
        self,
        url: Union[str, os.PathLike],
        options: Optional[dict[str, Optional[types.Option]]] = None,
        **kwargs: Optional[types.Option],
    ) -> Self:
        ...

    def output(
        self,
        url: Union[str, os.PathLike],
        options: Optional[dict[str, Optional[types.Option]]] = None,
        **kwargs: Optional[types.Option],
    ) -> Self:
        ...

    @overload
    def execute(
        self,
        stream: Optional[types.Stream] = None,
    ) -> bytes:
        ...

    @overload
    async def execute(
        self,
        stream: Optional[types.AsyncStream] = None,
    ) -> bytes:
        ...

    def terminate(self):
        ...

    def on(
        self, event: str, f: Optional[types.Handler] = None
    ) -> Union[types.Handler, Callable[[types.Handler], types.Handler]]:
        ...

    def emit(self, event: str, *args: Any, **kwargs: Any) -> bool:
        ...
