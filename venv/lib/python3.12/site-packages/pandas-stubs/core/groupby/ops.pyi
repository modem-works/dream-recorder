from collections.abc import (
    Callable,
    Hashable,
    Iterator,
)
from typing import (
    Generic,
    final,
)

import numpy as np
from pandas import (
    Index,
    Series,
)
from pandas.core.groupby import grouper

from pandas._typing import (
    ArrayLike,
    AxisInt,
    Incomplete,
    NDFrameT,
    Shape,
    T,
    npt,
)
from pandas.util._decorators import cache_readonly

class BaseGrouper:
    axis: Index
    dropna: bool
    @property
    def groupings(self) -> list[grouper.Grouping]: ...
    @property
    def shape(self) -> Shape: ...
    def __iter__(self) -> Iterator: ...
    @property
    def nkeys(self) -> int: ...
    def get_iterator(
        self, data: NDFrameT, axis: AxisInt = ...
    ) -> Iterator[tuple[Hashable, NDFrameT]]: ...
    @final
    @cache_readonly
    def group_keys_seq(self): ...
    @cache_readonly
    def indices(self) -> dict[Hashable, npt.NDArray[np.intp]]: ...
    @final
    def result_ilocs(self) -> npt.NDArray[np.intp]: ...
    @final
    @property
    def codes(self) -> list[npt.NDArray[np.signedinteger]]: ...
    @property
    def levels(self) -> list[Index]: ...
    @property
    def names(self) -> list: ...
    @final
    def size(self) -> Series: ...
    @cache_readonly
    def groups(self) -> dict[Hashable, np.ndarray]: ...
    @final
    @cache_readonly
    def is_monotonic(self) -> bool: ...
    @final
    @cache_readonly
    def has_dropped_na(self) -> bool: ...
    @cache_readonly
    def group_info(self) -> tuple[npt.NDArray[np.intp], npt.NDArray[np.intp], int]: ...
    @cache_readonly
    def codes_info(self) -> npt.NDArray[np.intp]: ...
    @final
    @cache_readonly
    def ngroups(self) -> int: ...
    @property
    def reconstructed_codes(self) -> list[npt.NDArray[np.intp]]: ...
    @cache_readonly
    def result_index(self) -> Index: ...
    @final
    def get_group_levels(self) -> list[ArrayLike]: ...
    @final
    def agg_series(
        self,
        obj: Series,
        func: Callable[[Series], object],
        preserve_dtype: bool = ...,
    ) -> ArrayLike: ...
    @final
    def apply_groupwise(
        self, f: Callable[[NDFrameT], T], data: NDFrameT, axis: AxisInt = ...
    ) -> tuple[list[T], bool]: ...

class BinGrouper(BaseGrouper):
    bins: npt.NDArray[np.int64]
    binlabels: Index
    indexer: npt.NDArray[np.intp]
    @cache_readonly
    def indices(self) -> dict[Incomplete, list[int]]: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]

class DataSplitter(Generic[NDFrameT]):
    data: NDFrameT
    labels: npt.NDArray[np.intp]
    ngroups: int
    axis: AxisInt
    def __iter__(self) -> Iterator[NDFrameT]: ...
