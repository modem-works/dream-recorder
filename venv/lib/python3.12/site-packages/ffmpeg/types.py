from __future__ import annotations

import asyncio
from typing import IO, Any, Callable, Iterable, TypeVar, Union

Numeric = Union[int, float]

T = Union[str, Numeric]
Option = Union[Iterable[T], T]

Stream = Union[bytes, IO[bytes]]
AsyncStream = Union[bytes, asyncio.StreamReader]

Handler = TypeVar("Handler", bound=Callable[..., Any])
