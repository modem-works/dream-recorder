from collections.abc import (
    Callable,
    Hashable,
    Iterable,
    Iterator,
    Sequence,
)
from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    ClassVar,
    Literal,
    final,
    overload,
)

import numpy as np
from pandas import (
    DataFrame,
    DatetimeIndex,
    Interval,
    IntervalIndex,
    MultiIndex,
    Period,
    PeriodDtype,
    PeriodIndex,
    Series,
    TimedeltaIndex,
)
from pandas.core.arrays import ExtensionArray
from pandas.core.base import IndexOpsMixin
from pandas.core.strings import StringMethods
from typing_extensions import (
    Never,
    Self,
)

from pandas._libs.interval import _OrderableT
from pandas._typing import (
    S1,
    Dtype,
    DtypeArg,
    DtypeObj,
    FillnaOptions,
    HashableT,
    Label,
    Level,
    MaskType,
    NaPosition,
    TimedeltaDtypeArg,
    TimestampDtypeArg,
    np_ndarray_anyint,
    np_ndarray_bool,
    np_ndarray_complex,
    np_ndarray_float,
    type_t,
)

class InvalidIndexError(Exception): ...

_str = str

class Index(IndexOpsMixin[S1]):
    __hash__: ClassVar[None]  # type: ignore[assignment]
    # overloads with additional dtypes
    @overload
    def __new__(  # pyright: ignore[reportOverlappingOverload]
        cls,
        data: Sequence[int | np.integer] | IndexOpsMixin[int] | np_ndarray_anyint,
        *,
        dtype: Literal["int"] | type_t[int | np.integer] = ...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Index[int]: ...
    @overload
    def __new__(
        cls,
        data: Iterable,
        *,
        dtype: Literal["int"] | type_t[int | np.integer],
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Index[int]: ...
    @overload
    def __new__(
        cls,
        data: Sequence[float | np.floating] | IndexOpsMixin[float] | np_ndarray_float,
        *,
        dtype: Literal["float"] | type_t[float | np.floating] = ...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Index[float]: ...
    @overload
    def __new__(
        cls,
        data: Iterable,
        *,
        dtype: Literal["float"] | type_t[float | np.floating],
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Index[float]: ...
    @overload
    def __new__(
        cls,
        data: (
            Sequence[complex | np.complexfloating]
            | IndexOpsMixin[complex]
            | np_ndarray_complex
        ),
        *,
        dtype: Literal["complex"] | type_t[complex | np.complexfloating] = ...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Index[complex]: ...
    @overload
    def __new__(
        cls,
        data: Iterable,
        *,
        dtype: Literal["complex"] | type_t[complex | np.complexfloating],
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Index[complex]: ...
    # special overloads with dedicated Index-subclasses
    @overload
    def __new__(
        cls,
        data: Sequence[np.datetime64 | datetime] | IndexOpsMixin[datetime],
        *,
        dtype: TimestampDtypeArg = ...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> DatetimeIndex: ...
    @overload
    def __new__(
        cls,
        data: Iterable,
        *,
        dtype: TimestampDtypeArg,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> DatetimeIndex: ...
    @overload
    def __new__(
        cls,
        data: Sequence[Period] | IndexOpsMixin[Period],
        *,
        dtype: PeriodDtype = ...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> PeriodIndex: ...
    @overload
    def __new__(
        cls,
        data: Iterable,
        *,
        dtype: PeriodDtype,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> PeriodIndex: ...
    @overload
    def __new__(
        cls,
        data: Sequence[np.timedelta64 | timedelta] | IndexOpsMixin[timedelta],
        *,
        dtype: TimedeltaDtypeArg = ...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> TimedeltaIndex: ...
    @overload
    def __new__(
        cls,
        data: Iterable,
        *,
        dtype: TimedeltaDtypeArg,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> TimedeltaIndex: ...
    @overload
    def __new__(
        cls,
        data: Sequence[Interval[_OrderableT]] | IndexOpsMixin[Interval[_OrderableT]],
        *,
        dtype: Literal["Interval"] = ...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> IntervalIndex[Interval[_OrderableT]]: ...
    @overload
    def __new__(
        cls,
        data: Iterable,
        *,
        dtype: Literal["Interval"],
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> IntervalIndex[Interval[Any]]: ...
    # generic overloads
    @overload
    def __new__(
        cls,
        data: Iterable[S1] | IndexOpsMixin[S1],
        *,
        dtype: type[S1] = ...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Self: ...
    @overload
    def __new__(
        cls,
        data: Iterable = ...,
        *,
        dtype: type[S1],
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Self: ...
    # fallback overload
    @overload
    def __new__(
        cls,
        data: Iterable,
        *,
        dtype=...,
        copy: bool = ...,
        name: Hashable = ...,
        tupleize_cols: bool = ...,
        **kwargs,
    ) -> Self: ...
    @property
    def str(
        self,
    ) -> StringMethods[Self, MultiIndex, np_ndarray_bool, Index[list[str]]]: ...
    def is_(self, other) -> bool: ...
    def __len__(self) -> int: ...
    def __array__(self, dtype=...) -> np.ndarray: ...
    def __array_wrap__(self, result, context=...): ...
    @property
    def dtype(self) -> DtypeObj: ...
    def ravel(self, order: _str = ...): ...
    def view(self, cls=...): ...
    def astype(self, dtype: DtypeArg, copy: bool = ...) -> Index: ...
    def take(
        self, indices, axis: int = ..., allow_fill: bool = ..., fill_value=..., **kwargs
    ): ...
    def repeat(self, repeats, axis=...): ...
    def copy(self, name: Hashable = ..., deep: bool = ...) -> Self: ...
    def __copy__(self, **kwargs): ...
    def __deepcopy__(self, memo=...): ...
    def format(
        self, name: bool = ..., formatter: Callable | None = ..., na_rep: _str = ...
    ) -> list[_str]: ...
    def to_flat_index(self): ...
    def to_series(self, index=..., name: Hashable = ...) -> Series: ...
    def to_frame(self, index: bool = ..., name=...) -> DataFrame: ...
    @property
    def name(self): ...
    @name.setter
    def name(self, value) -> None: ...
    @property
    def names(self) -> list[_str]: ...
    @names.setter
    def names(self, names: list[_str]): ...
    def set_names(self, names, *, level=..., inplace: bool = ...): ...
    @overload
    def rename(self, name, inplace: Literal[False] = False) -> Self: ...
    @overload
    def rename(self, name, inplace: Literal[True]) -> None: ...
    @property
    def nlevels(self) -> int: ...
    def sortlevel(self, level=..., ascending: bool = ..., sort_remaining=...): ...
    def get_level_values(self, level: int | _str) -> Index: ...
    def droplevel(self, level: Level | list[Level] = ...): ...
    @property
    def is_monotonic_increasing(self) -> bool: ...
    @property
    def is_monotonic_decreasing(self) -> bool: ...
    @property
    def is_unique(self) -> bool: ...
    @property
    def has_duplicates(self) -> bool: ...
    @property
    def inferred_type(self) -> _str: ...
    def __reduce__(self): ...
    @property
    def hasnans(self) -> bool: ...
    def isna(self): ...
    isnull = ...
    def notna(self): ...
    notnull = ...
    def fillna(self, value=...): ...
    def dropna(self, how: Literal["any", "all"] = ...) -> Self: ...
    def unique(self, level=...) -> Self: ...
    def drop_duplicates(self, *, keep: NaPosition | Literal[False] = ...) -> Self: ...
    def duplicated(
        self, keep: Literal["first", "last", False] = ...
    ) -> np_ndarray_bool: ...
    def __and__(self, other: Never) -> Never: ...
    def __rand__(self, other: Never) -> Never: ...
    def __or__(self, other: Never) -> Never: ...
    def __ror__(self, other: Never) -> Never: ...
    def __xor__(self, other: Never) -> Never: ...
    def __rxor__(self, other: Never) -> Never: ...
    def __neg__(self) -> Self: ...
    def __nonzero__(self) -> None: ...
    __bool__ = ...
    def union(self, other: list[HashableT] | Index, sort=...) -> Index: ...
    def intersection(self, other: list[S1] | Self, sort: bool = ...) -> Self: ...
    def difference(self, other: list | Index, sort: bool | None = None) -> Self: ...
    def symmetric_difference(
        self, other: list[S1] | Self, result_name: Hashable = ..., sort=...
    ) -> Self: ...
    def get_loc(
        self,
        key: Label,
        method: FillnaOptions | Literal["nearest"] | None = ...,
        tolerance=...,
    ) -> int | slice | np_ndarray_bool: ...
    def get_indexer(self, target, method=..., limit=..., tolerance=...): ...
    def reindex(self, target, method=..., level=..., limit=..., tolerance=...): ...
    def join(
        self,
        other,
        *,
        how: _str = ...,
        level=...,
        return_indexers: bool = ...,
        sort: bool = ...,
    ): ...
    @property
    def values(self) -> np.ndarray: ...
    @property
    def array(self) -> ExtensionArray: ...
    def memory_usage(self, deep: bool = ...): ...
    def where(self, cond, other=...): ...
    def __contains__(self, key) -> bool: ...
    def __setitem__(self, key, value) -> None: ...
    @overload
    def __getitem__(
        self,
        idx: slice | np_ndarray_anyint | Sequence[int] | Index | MaskType,
    ) -> Self: ...
    @overload
    def __getitem__(self, idx: int | tuple[np_ndarray_anyint, ...]) -> S1: ...
    def append(self, other): ...
    def putmask(self, mask, value): ...
    def equals(self, other) -> bool: ...
    def identical(self, other) -> bool: ...
    def asof(self, label): ...
    def asof_locs(self, where, mask): ...
    def sort_values(self, return_indexer: bool = ..., ascending: bool = ...): ...
    def sort(self, *args, **kwargs) -> None: ...
    def shift(self, periods: int = ..., freq=...) -> None: ...
    def argsort(self, *args, **kwargs): ...
    def get_indexer_non_unique(self, target): ...
    def get_indexer_for(self, target, **kwargs): ...
    @final
    def groupby(self, values) -> dict[Hashable, np.ndarray]: ...
    def map(self, mapper, na_action=...) -> Index: ...
    def isin(self, values, level=...) -> np_ndarray_bool: ...
    def slice_indexer(self, start=..., end=..., step=...): ...
    def get_slice_bound(self, label, side): ...
    def slice_locs(self, start=..., end=..., step=...): ...
    def delete(self, loc): ...
    def insert(self, loc, item): ...
    def drop(self, labels, errors: _str = ...) -> Self: ...
    @property
    def shape(self) -> tuple[int, ...]: ...
    # Extra methods from old stubs
    def __eq__(self, other: object) -> np_ndarray_bool: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __iter__(self) -> Iterator[S1]: ...
    def __ne__(self, other: object) -> np_ndarray_bool: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __le__(self, other: Self | S1) -> np_ndarray_bool: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __ge__(self, other: Self | S1) -> np_ndarray_bool: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __lt__(self, other: Self | S1) -> np_ndarray_bool: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __gt__(self, other: Self | S1) -> np_ndarray_bool: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    # overwrite inherited methods from OpsMixin
    @overload
    def __mul__(
        self: Index[int] | Index[float], other: timedelta
    ) -> TimedeltaIndex: ...
    @overload
    def __mul__(self, other: Any) -> Self: ...
    def __floordiv__(
        self,
        other: (
            float
            | IndexOpsMixin[int]
            | IndexOpsMixin[float]
            | Sequence[int]
            | Sequence[float]
        ),
    ) -> Self: ...
    def __rfloordiv__(
        self,
        other: (
            float
            | IndexOpsMixin[int]
            | IndexOpsMixin[float]
            | Sequence[int]
            | Sequence[float]
        ),
    ) -> Self: ...
    def __truediv__(
        self,
        other: (
            float
            | IndexOpsMixin[int]
            | IndexOpsMixin[float]
            | Sequence[int]
            | Sequence[float]
        ),
    ) -> Self: ...
    def __rtruediv__(
        self,
        other: (
            float
            | IndexOpsMixin[int]
            | IndexOpsMixin[float]
            | Sequence[int]
            | Sequence[float]
        ),
    ) -> Self: ...

def ensure_index_from_sequences(
    sequences: Sequence[Sequence[Dtype]], names: list[str] = ...
) -> Index: ...
def ensure_index(index_like: Sequence | Index, copy: bool = ...) -> Index: ...
def maybe_extract_name(name, obj, cls) -> Label: ...
