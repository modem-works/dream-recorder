from collections.abc import (
    Hashable,
    Iterator,
)
from typing import (
    Any,
    Generic,
    Literal,
    final,
    overload,
)

import numpy as np
from pandas import (
    Index,
    Series,
)
from pandas.core.arraylike import OpsMixin
from pandas.core.arrays import ExtensionArray
from pandas.core.arrays.categorical import Categorical
from typing_extensions import Self

from pandas._typing import (
    S1,
    AxisIndex,
    NaPosition,
    NDFrameT,
    Scalar,
    npt,
)
from pandas.util._decorators import cache_readonly

class NoNewAttributesMixin:
    def __setattr__(self, key: str, value: Any) -> None: ...

class SelectionMixin(Generic[NDFrameT]):
    obj: NDFrameT
    exclusions: frozenset[Hashable]
    @final
    @cache_readonly
    def ndim(self) -> int: ...
    def __getitem__(self, key): ...
    def aggregate(self, func, *args, **kwargs): ...

class IndexOpsMixin(OpsMixin, Generic[S1]):
    __array_priority__: int = ...
    @property
    def T(self) -> Self: ...
    @property
    def shape(self) -> tuple: ...
    @property
    def ndim(self) -> int: ...
    def item(self) -> S1: ...
    @property
    def nbytes(self) -> int: ...
    @property
    def size(self) -> int: ...
    @property
    def array(self) -> ExtensionArray: ...
    def to_numpy(
        self,
        dtype: npt.DTypeLike | None = ...,
        copy: bool = ...,
        na_value: Scalar = ...,
        **kwargs,
    ) -> np.ndarray: ...
    @property
    def empty(self) -> bool: ...
    def max(self, axis=..., skipna: bool = ..., **kwargs): ...
    def min(self, axis=..., skipna: bool = ..., **kwargs): ...
    def argmax(
        self, axis: AxisIndex | None = ..., skipna: bool = ..., *args, **kwargs
    ) -> np.int64: ...
    def argmin(
        self, axis: AxisIndex | None = ..., skipna: bool = ..., *args, **kwargs
    ) -> np.int64: ...
    def tolist(self) -> list[S1]: ...
    def to_list(self) -> list[S1]: ...
    def __iter__(self) -> Iterator[S1]: ...
    @property
    def hasnans(self) -> bool: ...
    @overload
    def value_counts(
        self,
        normalize: Literal[False] = ...,
        sort: bool = ...,
        ascending: bool = ...,
        bins=...,
        dropna: bool = ...,
    ) -> Series[int]: ...
    @overload
    def value_counts(
        self,
        normalize: Literal[True],
        sort: bool = ...,
        ascending: bool = ...,
        bins=...,
        dropna: bool = ...,
    ) -> Series[float]: ...
    def nunique(self, dropna: bool = ...) -> int: ...
    @property
    def is_unique(self) -> bool: ...
    @property
    def is_monotonic_decreasing(self) -> bool: ...
    @property
    def is_monotonic_increasing(self) -> bool: ...
    def factorize(
        self, sort: bool = ..., use_na_sentinel: bool = ...
    ) -> tuple[np.ndarray, np.ndarray | Index | Categorical]: ...
    def searchsorted(
        self, value, side: Literal["left", "right"] = ..., sorter=...
    ) -> int | list[int]: ...
    def drop_duplicates(self, *, keep: NaPosition | Literal[False] = ...) -> Self: ...
