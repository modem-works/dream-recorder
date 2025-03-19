from collections import dict_keys  # type: ignore[attr-defined]
from collections.abc import (
    Callable,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    Generic,
    Literal,
    NoReturn,
    overload,
)

from _typing import (
    Label,
    ReplaceValue,
    TimeZones,
)
from matplotlib.axes import (
    Axes as PlotAxes,
    SubplotBase,
)
import numpy as np
from pandas import (
    Index,
    Period,
    PeriodDtype,
    Timedelta,
    Timestamp,
)
from pandas.core.api import (
    Int8Dtype as Int8Dtype,
    Int16Dtype as Int16Dtype,
    Int32Dtype as Int32Dtype,
    Int64Dtype as Int64Dtype,
)
from pandas.core.arrays import TimedeltaArray
from pandas.core.arrays.base import ExtensionArray
from pandas.core.arrays.categorical import CategoricalAccessor
from pandas.core.arrays.datetimes import DatetimeArray
from pandas.core.arrays.interval import IntervalArray
from pandas.core.base import IndexOpsMixin
from pandas.core.frame import DataFrame
from pandas.core.generic import NDFrame
from pandas.core.groupby.generic import SeriesGroupBy
from pandas.core.groupby.groupby import BaseGroupBy
from pandas.core.indexers import BaseIndexer
from pandas.core.indexes.accessors import (
    CombinedDatetimelikeProperties,
    PeriodProperties,
    TimedeltaProperties,
    TimestampProperties,
)
from pandas.core.indexes.category import CategoricalIndex
from pandas.core.indexes.datetimes import DatetimeIndex
from pandas.core.indexes.interval import IntervalIndex
from pandas.core.indexes.multi import MultiIndex
from pandas.core.indexes.period import PeriodIndex
from pandas.core.indexes.timedeltas import TimedeltaIndex
from pandas.core.indexing import (
    _AtIndexer,
    _iAtIndexer,
    _iLocIndexer,
    _IndexSliceTuple,
    _LocIndexer,
)
from pandas.core.strings import StringMethods
from pandas.core.window import (
    Expanding,
    ExponentialMovingWindow,
)
from pandas.core.window.rolling import (
    Rolling,
    Window,
)
from typing_extensions import (
    Never,
    Self,
    TypeAlias,
)
import xarray as xr

from pandas._libs.interval import (
    Interval,
    _OrderableT,
)
from pandas._libs.lib import NoDefault
from pandas._libs.missing import NAType
from pandas._libs.tslibs import BaseOffset
from pandas._libs.tslibs.nattype import NaTType
from pandas._typing import (
    S1,
    S2,
    AggFuncTypeBase,
    AggFuncTypeDictFrame,
    AggFuncTypeSeriesToFrame,
    AnyArrayLike,
    ArrayLike,
    Axes,
    Axis,
    AxisColumn,
    AxisIndex,
    BooleanDtypeArg,
    BytesDtypeArg,
    CalculationMethod,
    CategoryDtypeArg,
    ComplexDtypeArg,
    CompressionOptions,
    Dtype,
    DtypeObj,
    FilePath,
    FillnaOptions,
    FloatDtypeArg,
    Frequency,
    GroupByObjectNonScalar,
    HashableT1,
    IgnoreRaise,
    IndexingInt,
    IndexLabel,
    IntDtypeArg,
    InterpolateOptions,
    IntervalClosedType,
    IntervalT,
    JoinHow,
    JsonSeriesOrient,
    Level,
    ListLike,
    ListLikeU,
    MaskType,
    NaPosition,
    ObjectDtypeArg,
    QuantileInterpolation,
    RandomState,
    Renamer,
    Scalar,
    ScalarT,
    SequenceNotStr,
    SeriesByT,
    SortKind,
    StrDtypeArg,
    StrLike,
    T,
    TimedeltaDtypeArg,
    TimestampConvention,
    TimestampDtypeArg,
    TimeUnit,
    UIntDtypeArg,
    VoidDtypeArg,
    WriteBuffer,
    np_ndarray_anyint,
    npt,
    num,
)

from pandas.core.dtypes.base import ExtensionDtype
from pandas.core.dtypes.dtypes import CategoricalDtype

from pandas.plotting import PlotAccessor

_bool = bool
_str = str

class _iLocIndexerSeries(_iLocIndexer, Generic[S1]):
    # get item
    @overload
    def __getitem__(self, idx: IndexingInt) -> S1: ...
    @overload
    def __getitem__(self, idx: Index | slice | np_ndarray_anyint) -> Series[S1]: ...
    # set item
    @overload
    def __setitem__(self, idx: int, value: S1 | None) -> None: ...
    @overload
    def __setitem__(
        self,
        idx: Index | slice | np_ndarray_anyint | list[int],
        value: S1 | Series[S1] | None,
    ) -> None: ...

class _LocIndexerSeries(_LocIndexer, Generic[S1]):
    # ignore needed because of mypy.  Overlapping, but we want to distinguish
    # having a tuple of just scalars, versus tuples that include slices or Index
    @overload
    def __getitem__(  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
        self,
        idx: Scalar | tuple[Scalar, ...],
        # tuple case is for getting a specific element when using a MultiIndex
    ) -> S1: ...
    @overload
    def __getitem__(
        self,
        idx: (
            MaskType
            | Index
            | SequenceNotStr[float | str | Timestamp]
            | slice
            | _IndexSliceTuple
            | Sequence[_IndexSliceTuple]
            | Callable
        ),
        # _IndexSliceTuple is when having a tuple that includes a slice.  Could just
        # be s.loc[1, :], or s.loc[pd.IndexSlice[1, :]]
    ) -> Series[S1]: ...
    @overload
    def __setitem__(
        self,
        idx: Index | MaskType | slice,
        value: S1 | ArrayLike | Series[S1] | None,
    ) -> None: ...
    @overload
    def __setitem__(
        self,
        idx: str,
        value: S1 | None,
    ) -> None: ...
    @overload
    def __setitem__(
        self,
        idx: MaskType | StrLike | _IndexSliceTuple | list[ScalarT],
        value: S1 | ArrayLike | Series[S1] | None,
    ) -> None: ...

_ListLike: TypeAlias = (
    ArrayLike | dict[_str, np.ndarray] | Sequence[S1] | IndexOpsMixin[S1]
)

class Series(IndexOpsMixin[S1], NDFrame):
    __hash__: ClassVar[None]

    @overload
    def __new__(
        cls,
        data: npt.NDArray[np.float64],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series[float]: ...
    @overload
    def __new__(  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
        cls,
        data: Sequence[Never],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series[Any]: ...
    @overload
    def __new__(
        cls,
        data: Sequence[list[str]],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series[list[str]]: ...
    @overload
    def __new__(
        cls,
        data: Sequence[str],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series[str]: ...
    @overload
    def __new__(
        cls,
        data: (
            DatetimeIndex
            | Sequence[np.datetime64 | datetime | date]
            | dict[HashableT1, np.datetime64 | datetime | date]
            | np.datetime64
            | datetime
            | date
        ),
        index: Axes | None = ...,
        *,
        dtype: TimestampDtypeArg = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> TimestampSeries: ...
    @overload
    def __new__(
        cls,
        data: _ListLike,
        index: Axes | None = ...,
        *,
        dtype: TimestampDtypeArg,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> TimestampSeries: ...
    @overload
    def __new__(
        cls,
        data: PeriodIndex | Sequence[Period],
        index: Axes | None = ...,
        *,
        dtype: PeriodDtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> PeriodSeries: ...
    @overload
    def __new__(
        cls,
        data: (
            TimedeltaIndex
            | Sequence[np.timedelta64 | timedelta]
            | dict[HashableT1, np.timedelta64 | timedelta]
            | np.timedelta64
            | timedelta
        ),
        index: Axes | None = ...,
        *,
        dtype: TimedeltaDtypeArg = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> TimedeltaSeries: ...
    @overload
    def __new__(
        cls,
        data: (
            IntervalIndex[Interval[_OrderableT]]
            | Interval[_OrderableT]
            | Sequence[Interval[_OrderableT]]
            | dict[HashableT1, Interval[_OrderableT]]
        ),
        index: Axes | None = ...,
        *,
        dtype: Literal["Interval"] = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> IntervalSeries[_OrderableT]: ...
    @overload
    def __new__(  # type: ignore[overload-overlap]
        cls,
        data: Scalar | _ListLike | dict[HashableT1, Any] | None,
        index: Axes | None = ...,
        *,
        dtype: type[S1],
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Self: ...
    @overload
    def __new__(  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
        cls,
        data: Sequence[bool],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series[bool]: ...
    @overload
    def __new__(  # type: ignore[overload-overlap]
        cls,
        data: Sequence[int],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series[int]: ...
    @overload
    def __new__(
        cls,
        data: Sequence[float],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series[float]: ...
    @overload
    def __new__(  # type: ignore[overload-cannot-match] # pyright: ignore[reportOverlappingOverload]
        cls,
        data: Sequence[int | float],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series[float]: ...
    @overload
    def __new__(
        cls,
        data: S1 | _ListLike[S1] | dict[HashableT1, S1] | dict_keys[S1, Any],
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Self: ...
    @overload
    def __new__(
        cls,
        data: (
            Scalar
            | _ListLike
            | Mapping[HashableT1, Any]
            | BaseGroupBy
            | NaTType
            | NAType
            | None
        ) = ...,
        index: Axes | None = ...,
        *,
        dtype: Dtype = ...,
        name: Hashable = ...,
        copy: bool = ...,
    ) -> Series: ...
    @property
    def hasnans(self) -> bool: ...
    def div(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[float]: ...
    def rdiv(
        self,
        other: Series[S1] | Scalar,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    @property
    def dtype(self) -> DtypeObj: ...
    @property
    def dtypes(self) -> DtypeObj: ...
    @property
    def name(self) -> Hashable | None: ...
    @name.setter
    def name(self, value: Hashable | None) -> None: ...
    @property
    def values(self) -> ArrayLike: ...
    @property
    def array(self) -> ExtensionArray: ...
    def ravel(self, order: _str = ...) -> np.ndarray: ...
    def __len__(self) -> int: ...
    def view(self, dtype=...) -> Series[S1]: ...
    def __array_ufunc__(self, ufunc: Callable, method: _str, *inputs, **kwargs): ...
    def __array__(self, dtype=...) -> np.ndarray: ...
    @property
    def axes(self) -> list: ...
    def take(
        self, indices: Sequence, axis: AxisIndex = ..., **kwargs
    ) -> Series[S1]: ...
    def __getattr__(self, name: _str) -> S1: ...
    @overload
    def __getitem__(
        self,
        idx: (
            list[_str]
            | Index
            | Series[S1]
            | slice
            | MaskType
            | tuple[Hashable | slice, ...]
        ),
    ) -> Self: ...
    @overload
    def __getitem__(self, idx: Scalar) -> S1: ...
    def __setitem__(self, key, value) -> None: ...
    @overload
    def get(self, key: Hashable, default: None = ...) -> S1 | None: ...
    @overload
    def get(self, key: Hashable, default: S1) -> S1: ...
    @overload
    def get(self, key: Hashable, default: T) -> S1 | T: ...
    def repeat(
        self, repeats: int | list[int], axis: AxisIndex | None = ...
    ) -> Series[S1]: ...
    @property
    def index(self) -> Index | MultiIndex: ...
    @index.setter
    def index(self, idx: Index) -> None: ...
    @overload
    def reset_index(
        self,
        level: Sequence[Level] | Level | None = ...,
        *,
        drop: Literal[False] = ...,
        name: Level = ...,
        inplace: Literal[False] = ...,
        allow_duplicates: bool = ...,
    ) -> DataFrame: ...
    @overload
    def reset_index(
        self,
        level: Sequence[Level] | Level | None = ...,
        *,
        drop: Literal[True],
        name: Level = ...,
        inplace: Literal[False] = ...,
        allow_duplicates: bool = ...,
    ) -> Series[S1]: ...
    @overload
    def reset_index(
        self,
        level: Sequence[Level] | Level | None = ...,
        *,
        drop: bool = ...,
        name: Level = ...,
        inplace: Literal[True],
        allow_duplicates: bool = ...,
    ) -> None: ...
    @overload
    def to_string(
        self,
        buf: FilePath | WriteBuffer[str],
        na_rep: _str = ...,
        float_format: Callable[[float], str] = ...,
        header: _bool = ...,
        index: _bool = ...,
        length: _bool = ...,
        dtype: _bool = ...,
        name: _bool = ...,
        max_rows: int | None = ...,
        min_rows: int | None = ...,
    ) -> None: ...
    @overload
    def to_string(
        self,
        buf: None = ...,
        na_rep: _str = ...,
        float_format: Callable[[float], str] = ...,
        header: _bool = ...,
        index: _bool = ...,
        length: _bool = ...,
        dtype: _bool = ...,
        name: _bool = ...,
        max_rows: int | None = ...,
        min_rows: int | None = ...,
    ) -> _str: ...
    @overload
    def to_json(
        self,
        path_or_buf: FilePath | WriteBuffer[str],
        *,
        orient: Literal["records"],
        date_format: Literal["epoch", "iso"] | None = ...,
        double_precision: int = ...,
        force_ascii: _bool = ...,
        date_unit: TimeUnit = ...,
        default_handler: (
            Callable[[Any], _str | float | _bool | list | dict] | None
        ) = ...,
        lines: Literal[True],
        compression: CompressionOptions = ...,
        index: _bool = ...,
        indent: int | None = ...,
        mode: Literal["a"],
    ) -> None: ...
    @overload
    def to_json(
        self,
        path_or_buf: None = ...,
        *,
        orient: Literal["records"],
        date_format: Literal["epoch", "iso"] | None = ...,
        double_precision: int = ...,
        force_ascii: _bool = ...,
        date_unit: TimeUnit = ...,
        default_handler: (
            Callable[[Any], _str | float | _bool | list | dict] | None
        ) = ...,
        lines: Literal[True],
        compression: CompressionOptions = ...,
        index: _bool = ...,
        indent: int | None = ...,
        mode: Literal["a"],
    ) -> _str: ...
    @overload
    def to_json(
        self,
        path_or_buf: FilePath | WriteBuffer[str],
        orient: JsonSeriesOrient | None = ...,
        date_format: Literal["epoch", "iso"] | None = ...,
        double_precision: int = ...,
        force_ascii: _bool = ...,
        date_unit: TimeUnit = ...,
        default_handler: (
            Callable[[Any], _str | float | _bool | list | dict] | None
        ) = ...,
        lines: _bool = ...,
        compression: CompressionOptions = ...,
        index: _bool = ...,
        indent: int | None = ...,
        mode: Literal["w"] = ...,
    ) -> None: ...
    @overload
    def to_json(
        self,
        path_or_buf: None = ...,
        orient: JsonSeriesOrient | None = ...,
        date_format: Literal["epoch", "iso"] | None = ...,
        double_precision: int = ...,
        force_ascii: _bool = ...,
        date_unit: TimeUnit = ...,
        default_handler: (
            Callable[[Any], _str | float | _bool | list | dict] | None
        ) = ...,
        lines: _bool = ...,
        compression: CompressionOptions = ...,
        index: _bool = ...,
        indent: int | None = ...,
        mode: Literal["w"] = ...,
    ) -> _str: ...
    def to_xarray(self) -> xr.DataArray: ...
    def items(self) -> Iterable[tuple[Hashable, S1]]: ...
    def keys(self) -> Index: ...
    @overload
    def to_dict(self, *, into: type[dict] = ...) -> dict[Any, S1]: ...
    @overload
    def to_dict(
        self, *, into: type[MutableMapping] | MutableMapping
    ) -> MutableMapping[Hashable, S1]: ...
    def to_frame(self, name: object | None = ...) -> DataFrame: ...
    @overload
    def groupby(
        self,
        by: Scalar,
        axis: AxisIndex = ...,
        level: IndexLabel | None = ...,
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, Scalar]: ...
    @overload
    def groupby(
        self,
        by: DatetimeIndex,
        axis: AxisIndex = ...,
        level: IndexLabel | None = ...,
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, Timestamp]: ...
    @overload
    def groupby(
        self,
        by: TimedeltaIndex,
        axis: AxisIndex = ...,
        level: IndexLabel | None = ...,
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, Timedelta]: ...
    @overload
    def groupby(
        self,
        by: PeriodIndex,
        axis: AxisIndex = ...,
        level: IndexLabel | None = ...,
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, Period]: ...
    @overload
    def groupby(
        self,
        by: IntervalIndex[IntervalT],
        axis: AxisIndex = ...,
        level: IndexLabel | None = ...,
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, IntervalT]: ...
    @overload
    def groupby(
        self,
        by: MultiIndex | GroupByObjectNonScalar,
        axis: AxisIndex = ...,
        level: IndexLabel | None = ...,
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, tuple]: ...
    @overload
    def groupby(
        self,
        by: None,
        axis: AxisIndex,
        level: IndexLabel,  # level is required when by=None (passed as positional)
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, Scalar]: ...
    @overload
    def groupby(
        self,
        by: None = ...,
        axis: AxisIndex = ...,
        *,
        level: IndexLabel,  # level is required when by=None (passed as keyword)
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, Scalar]: ...
    @overload
    def groupby(
        self,
        by: Series[SeriesByT],
        axis: AxisIndex = ...,
        level: IndexLabel | None = ...,
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, SeriesByT]: ...
    @overload
    def groupby(
        self,
        by: CategoricalIndex | Index | Series,
        axis: AxisIndex = ...,
        level: IndexLabel | None = ...,
        as_index: _bool = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> SeriesGroupBy[S1, Any]: ...
    # need the ignore because None is Hashable
    @overload
    def count(self, level: None = ...) -> int: ...  # type: ignore[overload-overlap]
    @overload
    def count(self, level: Hashable) -> Series[S1]: ...
    def mode(self, dropna=...) -> Series[S1]: ...
    def unique(self) -> np.ndarray: ...
    @overload
    def drop_duplicates(
        self,
        *,
        keep: NaPosition | Literal[False] = ...,
        inplace: Literal[True],
        ignore_index: _bool = ...,
    ) -> None: ...
    @overload
    def drop_duplicates(
        self,
        *,
        keep: NaPosition | Literal[False] = ...,
        inplace: Literal[False] = ...,
        ignore_index: _bool = ...,
    ) -> Series[S1]: ...
    def duplicated(self, keep: NaPosition | Literal[False] = ...) -> Series[_bool]: ...
    def idxmax(
        self, axis: AxisIndex = ..., skipna: _bool = ..., *args, **kwargs
    ) -> int | _str: ...
    def idxmin(
        self, axis: AxisIndex = ..., skipna: _bool = ..., *args, **kwargs
    ) -> int | _str: ...
    def round(self, decimals: int = ..., *args, **kwargs) -> Series[S1]: ...
    @overload
    def quantile(
        self,
        q: float = ...,
        interpolation: QuantileInterpolation = ...,
    ) -> float: ...
    @overload
    def quantile(
        self,
        q: _ListLike,
        interpolation: QuantileInterpolation = ...,
    ) -> Series[S1]: ...
    def corr(
        self,
        other: Series[S1],
        method: Literal["pearson", "kendall", "spearman"] = ...,
        min_periods: int = ...,
    ) -> float: ...
    def cov(
        self, other: Series[S1], min_periods: int | None = ..., ddof: int = ...
    ) -> float: ...
    @overload
    def diff(self: Series[_bool], periods: int = ...) -> Series[type[object]]: ...  # type: ignore[overload-overlap]
    @overload
    def diff(self: Series[complex], periods: int = ...) -> Series[complex]: ...  # type: ignore[overload-overlap]
    @overload
    def diff(self: Series[bytes], periods: int = ...) -> Never: ...
    @overload
    def diff(self: Series[type], periods: int = ...) -> Never: ...
    @overload
    def diff(self: Series[str], periods: int = ...) -> Never: ...
    @overload
    def diff(self, periods: int = ...) -> Series[float]: ...
    def autocorr(self, lag: int = ...) -> float: ...
    @overload
    def dot(self, other: Series[S1]) -> Scalar: ...
    @overload
    def dot(self, other: DataFrame) -> Series[S1]: ...
    @overload
    def dot(
        self, other: ArrayLike | dict[_str, np.ndarray] | Sequence[S1] | Index[S1]
    ) -> np.ndarray: ...
    @overload
    def __matmul__(self, other: Series) -> Scalar: ...
    @overload
    def __matmul__(self, other: DataFrame) -> Series: ...
    @overload
    def __matmul__(self, other: np.ndarray) -> np.ndarray: ...
    @overload
    def __rmatmul__(self, other: Series) -> Scalar: ...
    @overload
    def __rmatmul__(self, other: DataFrame) -> Series: ...
    @overload
    def __rmatmul__(self, other: np.ndarray) -> np.ndarray: ...
    @overload
    def searchsorted(
        self,
        value: _ListLike,
        side: Literal["left", "right"] = ...,
        sorter: _ListLike | None = ...,
    ) -> list[int]: ...
    @overload
    def searchsorted(
        self,
        value: Scalar,
        side: Literal["left", "right"] = ...,
        sorter: _ListLike | None = ...,
    ) -> int: ...
    @overload
    def compare(
        self,
        other: Series,
        align_axis: AxisIndex,
        keep_shape: bool = ...,
        keep_equal: bool = ...,
    ) -> Series: ...
    @overload
    def compare(
        self,
        other: Series,
        align_axis: AxisColumn = ...,
        keep_shape: bool = ...,
        keep_equal: bool = ...,
    ) -> DataFrame: ...
    def combine(
        self, other: Series[S1], func: Callable, fill_value: Scalar | None = ...
    ) -> Series[S1]: ...
    def combine_first(self, other: Series[S1]) -> Series[S1]: ...
    def update(self, other: Series[S1] | Sequence[S1] | Mapping[int, S1]) -> None: ...
    @overload
    def sort_values(
        self,
        *,
        axis: Axis = ...,
        ascending: _bool | Sequence[_bool] = ...,
        kind: SortKind = ...,
        na_position: NaPosition = ...,
        ignore_index: _bool = ...,
        inplace: Literal[True],
        key: Callable | None = ...,
    ) -> None: ...
    @overload
    def sort_values(
        self,
        *,
        axis: Axis = ...,
        ascending: _bool | Sequence[_bool] = ...,
        kind: SortKind = ...,
        na_position: NaPosition = ...,
        ignore_index: _bool = ...,
        inplace: Literal[False] = ...,
        key: Callable | None = ...,
    ) -> Series[S1]: ...
    @overload
    def sort_index(
        self,
        *,
        axis: Axis = ...,
        level: Level | None = ...,
        ascending: _bool | Sequence[_bool] = ...,
        kind: SortKind = ...,
        na_position: NaPosition = ...,
        sort_remaining: _bool = ...,
        ignore_index: _bool = ...,
        inplace: Literal[True],
        key: Callable | None = ...,
    ) -> None: ...
    @overload
    def sort_index(
        self,
        *,
        axis: Axis = ...,
        level: Level | list[int] | list[_str] | None = ...,
        ascending: _bool | Sequence[_bool] = ...,
        kind: SortKind = ...,
        na_position: NaPosition = ...,
        sort_remaining: _bool = ...,
        ignore_index: _bool = ...,
        inplace: Literal[False] = ...,
        key: Callable | None = ...,
    ) -> Series[S1]: ...
    def argsort(
        self,
        axis: AxisIndex = ...,
        kind: SortKind = ...,
        order: None = ...,
    ) -> Series[int]: ...
    def nlargest(
        self, n: int = ..., keep: NaPosition | Literal["all"] = ...
    ) -> Series[S1]: ...
    def nsmallest(
        self, n: int = ..., keep: NaPosition | Literal["all"] = ...
    ) -> Series[S1]: ...
    def swaplevel(
        self, i: Level = ..., j: Level = ..., copy: _bool = ...
    ) -> Series[S1]: ...
    def reorder_levels(self, order: list) -> Series[S1]: ...
    def explode(self) -> Series[S1]: ...
    def unstack(
        self,
        level: Level = ...,
        fill_value: int | _str | dict | None = ...,
    ) -> DataFrame: ...
    @overload
    def map(
        self,
        arg: Callable[[S1], S2 | NAType] | Mapping[S1, S2] | Series[S2],
        na_action: Literal["ignore"] = ...,
    ) -> Series[S2]: ...
    @overload
    def map(
        self,
        arg: Callable[[S1 | NAType], S2 | NAType] | Mapping[S1, S2] | Series[S2],
        na_action: None = ...,
    ) -> Series[S2]: ...
    @overload
    def aggregate(
        self: Series[int],
        func: Literal["mean"],
        axis: AxisIndex = ...,
        *args,
        **kwargs,
    ) -> float: ...
    @overload
    def aggregate(
        self,
        func: AggFuncTypeBase,
        axis: AxisIndex = ...,
        *args,
        **kwargs,
    ) -> S1: ...
    @overload
    def aggregate(
        self,
        func: AggFuncTypeSeriesToFrame = ...,
        axis: AxisIndex = ...,
        *args,
        **kwargs,
    ) -> Series: ...
    agg = aggregate
    @overload
    def transform(
        self,
        func: AggFuncTypeBase,
        axis: AxisIndex = ...,
        *args,
        **kwargs,
    ) -> Series[S1]: ...
    @overload
    def transform(
        self,
        func: list[AggFuncTypeBase] | AggFuncTypeDictFrame,
        axis: AxisIndex = ...,
        *args,
        **kwargs,
    ) -> DataFrame: ...
    @overload
    def apply(
        self,
        func: Callable[
            ..., Scalar | Sequence | set | Mapping | NAType | frozenset | None
        ],
        convertDType: _bool = ...,
        args: tuple = ...,
        **kwds,
    ) -> Series: ...
    @overload
    def apply(
        self,
        func: Callable[..., BaseOffset],
        convertDType: _bool = ...,
        args: tuple = ...,
        **kwds,
    ) -> OffsetSeries: ...
    @overload
    def apply(
        self,
        func: Callable[..., Series],
        convertDType: _bool = ...,
        args: tuple = ...,
        **kwds,
    ) -> DataFrame: ...
    def align(
        self,
        other: DataFrame | Series,
        join: JoinHow = ...,
        axis: Axis | None = ...,
        level: Level | None = ...,
        copy: _bool = ...,
        fill_value: Scalar | NAType | None = ...,
    ) -> tuple[Series, Series]: ...
    @overload
    def rename(
        self,
        index: Callable[[Any], Label],
        *,
        axis: Axis | None = ...,
        copy: bool = ...,
        inplace: Literal[True],
        level: Level | None = ...,
        errors: IgnoreRaise = ...,
    ) -> None: ...
    @overload
    def rename(
        self,
        index: Mapping[Any, Label],
        *,
        axis: Axis | None = ...,
        copy: bool = ...,
        inplace: Literal[True],
        level: Level | None = ...,
        errors: IgnoreRaise = ...,
    ) -> None: ...
    @overload
    def rename(
        self,
        index: Scalar | tuple[Hashable, ...] | None = None,
        *,
        axis: Axis | None = ...,
        copy: bool = ...,
        inplace: Literal[True],
        level: Level | None = ...,
        errors: IgnoreRaise = ...,
    ) -> Self: ...
    @overload
    def rename(
        self,
        index: Renamer | Scalar | tuple[Hashable, ...] | None = ...,
        *,
        axis: Axis | None = ...,
        copy: bool = ...,
        inplace: Literal[False] = ...,
        level: Level | None = ...,
        errors: IgnoreRaise = ...,
    ) -> Self: ...
    def reindex_like(
        self,
        other: Series[S1],
        method: _str | FillnaOptions | Literal["nearest"] | None = ...,
        copy: _bool = ...,
        limit: int | None = ...,
        tolerance: Scalar | AnyArrayLike | Sequence[Scalar] = ...,
    ) -> Self: ...
    @overload
    def fillna(
        self,
        value: Scalar | NAType | dict | Series[S1] | DataFrame | None = ...,
        *,
        axis: AxisIndex = ...,
        limit: int | None = ...,
        inplace: Literal[True],
    ) -> None: ...
    @overload
    def fillna(
        self,
        value: Scalar | NAType | dict | Series[S1] | DataFrame | None = ...,
        *,
        axis: AxisIndex = ...,
        limit: int | None = ...,
        inplace: Literal[False] = ...,
    ) -> Series[S1]: ...
    @overload
    def replace(
        self,
        to_replace: ReplaceValue = ...,
        value: ReplaceValue = ...,
        *,
        regex: ReplaceValue = ...,
        inplace: Literal[True],
    ) -> None: ...
    @overload
    def replace(
        self,
        to_replace: ReplaceValue = ...,
        value: ReplaceValue = ...,
        *,
        regex: ReplaceValue = ...,
        inplace: Literal[False] = ...,
    ) -> Series[S1]: ...
    def shift(
        self,
        periods: int = ...,
        freq: Frequency | timedelta | None = ...,
        axis: AxisIndex = ...,
        fill_value: object | None = ...,
    ) -> Series: ...
    def info(
        self,
        verbose: bool | None = ...,
        buf: WriteBuffer[str] = ...,
        memory_usage: bool | Literal["deep"] | None = ...,
        show_counts: bool | None = ...,
    ) -> None: ...
    def memory_usage(self, index: _bool = ..., deep: _bool = ...) -> int: ...
    def isin(self, values: Iterable | Series[S1] | dict) -> Series[_bool]: ...
    def between(
        self,
        left: Scalar | ListLikeU,
        right: Scalar | ListLikeU,
        inclusive: Literal["both", "neither", "left", "right"] = ...,
    ) -> Series[_bool]: ...
    def isna(self) -> Series[_bool]: ...
    def isnull(self) -> Series[_bool]: ...
    def notna(self) -> Series[_bool]: ...
    def notnull(self) -> Series[_bool]: ...
    @overload
    def dropna(
        self,
        *,
        axis: AxisIndex = ...,
        inplace: Literal[True],
        how: Literal["any", "all"] | None = ...,
        ignore_index: _bool = ...,
    ) -> None: ...
    @overload
    def dropna(
        self,
        *,
        axis: AxisIndex = ...,
        inplace: Literal[False] = ...,
        how: Literal["any", "all"] | None = ...,
        ignore_index: _bool = ...,
    ) -> Series[S1]: ...
    def to_timestamp(
        self,
        freq=...,
        how: TimestampConvention = ...,
        copy: _bool = ...,
    ) -> Series[S1]: ...
    def to_period(self, freq: _str | None = ..., copy: _bool = ...) -> DataFrame: ...
    @property
    def str(
        self,
    ) -> StringMethods[Series, DataFrame, Series[bool], Series[list[str]]]: ...
    @property
    def dt(self) -> CombinedDatetimelikeProperties: ...
    @property
    def plot(self) -> PlotAccessor: ...
    sparse = ...
    def hist(
        self,
        by: object | None = ...,
        ax: PlotAxes | None = ...,
        grid: _bool = ...,
        xlabelsize: float | _str | None = ...,
        xrot: float | None = ...,
        ylabelsize: float | _str | None = ...,
        yrot: float | None = ...,
        figsize: tuple[float, float] | None = ...,
        bins: int | Sequence = ...,
        backend: _str | None = ...,
        **kwargs,
    ) -> SubplotBase: ...
    def swapaxes(
        self, axis1: AxisIndex, axis2: AxisIndex, copy: _bool = ...
    ) -> Series[S1]: ...
    def droplevel(self, level: Level | list[Level], axis: AxisIndex = ...) -> Self: ...
    def pop(self, item: Hashable) -> S1: ...
    def squeeze(self, axis: AxisIndex | None = ...) -> Scalar: ...
    def __abs__(self) -> Series[S1]: ...
    def add_prefix(self, prefix: _str, axis: AxisIndex | None = ...) -> Series[S1]: ...
    def add_suffix(self, suffix: _str, axis: AxisIndex | None = ...) -> Series[S1]: ...
    def reindex(
        self,
        index: Axes | None = ...,
        method: FillnaOptions | Literal["nearest"] | None = ...,
        copy: bool = ...,
        level: int | _str = ...,
        fill_value: Scalar | None = ...,
        limit: int | None = ...,
        tolerance: float | None = ...,
    ) -> Series[S1]: ...
    def filter(
        self,
        items: _ListLike | None = ...,
        like: _str | None = ...,
        regex: _str | None = ...,
        axis: AxisIndex | None = ...,
    ) -> Series[S1]: ...
    def head(self, n: int = ...) -> Series[S1]: ...
    def tail(self, n: int = ...) -> Series[S1]: ...
    def sample(
        self,
        n: int | None = ...,
        frac: float | None = ...,
        replace: _bool = ...,
        weights: _str | _ListLike | np.ndarray | None = ...,
        random_state: RandomState | None = ...,
        axis: AxisIndex | None = ...,
        ignore_index: _bool = ...,
    ) -> Series[S1]: ...
    @overload
    def astype(
        self,
        dtype: BooleanDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Series[bool]: ...
    @overload
    def astype(
        self,
        dtype: IntDtypeArg | UIntDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Series[int]: ...
    @overload
    def astype(
        self,
        dtype: StrDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Series[_str]: ...
    @overload
    def astype(
        self,
        dtype: BytesDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Series[bytes]: ...
    @overload
    def astype(
        self,
        dtype: FloatDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Series[float]: ...
    @overload
    def astype(
        self,
        dtype: ComplexDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Series[complex]: ...
    @overload
    def astype(
        self,
        dtype: TimedeltaDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> TimedeltaSeries: ...
    @overload
    def astype(
        self,
        dtype: TimestampDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> TimestampSeries: ...
    @overload
    def astype(
        self,
        dtype: CategoryDtypeArg,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Series[CategoricalDtype]: ...
    @overload
    def astype(
        self,
        dtype: ObjectDtypeArg | VoidDtypeArg | ExtensionDtype | DtypeObj,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Series[Any]: ...
    def copy(self, deep: _bool = ...) -> Series[S1]: ...
    def infer_objects(self) -> Series[S1]: ...
    @overload
    def ffill(
        self,
        *,
        axis: AxisIndex | None = ...,
        inplace: Literal[True],
        limit: int | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
    ) -> None: ...
    @overload
    def ffill(
        self,
        *,
        axis: AxisIndex | None = ...,
        inplace: Literal[False] = ...,
        limit: int | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
    ) -> Series[S1]: ...
    @overload
    def bfill(
        self,
        *,
        axis: AxisIndex | None = ...,
        inplace: Literal[True],
        limit: int | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
    ) -> None: ...
    @overload
    def bfill(
        self,
        *,
        axis: AxisIndex | None = ...,
        inplace: Literal[False] = ...,
        limit: int | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
    ) -> Series[S1]: ...
    @overload
    def interpolate(
        self,
        method: InterpolateOptions = ...,
        *,
        axis: AxisIndex | None = ...,
        limit: int | None = ...,
        inplace: Literal[True],
        limit_direction: Literal["forward", "backward", "both"] | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
        **kwargs,
    ) -> None: ...
    @overload
    def interpolate(
        self,
        method: InterpolateOptions = ...,
        *,
        axis: AxisIndex | None = ...,
        limit: int | None = ...,
        inplace: Literal[False] = ...,
        limit_direction: Literal["forward", "backward", "both"] | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
        **kwargs,
    ) -> Series[S1]: ...
    def asof(
        self,
        where: Scalar | Sequence[Scalar],
        subset: _str | Sequence[_str] | None = ...,
    ) -> Scalar | Series[S1]: ...
    @overload
    def clip(
        self,
        lower: AnyArrayLike | float | None = ...,
        upper: AnyArrayLike | float | None = ...,
        *,
        axis: AxisIndex | None = ...,
        inplace: Literal[True],
        **kwargs,
    ) -> None: ...
    @overload
    def clip(
        self,
        lower: AnyArrayLike | float | None = ...,
        upper: AnyArrayLike | float | None = ...,
        *,
        axis: AxisIndex | None = ...,
        inplace: Literal[False] = ...,
        **kwargs,
    ) -> Series[S1]: ...
    def asfreq(
        self,
        freq,
        method: FillnaOptions | None = ...,
        how: Literal["start", "end"] | None = ...,
        normalize: _bool = ...,
        fill_value: Scalar | None = ...,
    ) -> Series[S1]: ...
    def at_time(
        self,
        time: _str | time,
        asof: _bool = ...,
        axis: AxisIndex | None = ...,
    ) -> Series[S1]: ...
    def between_time(
        self,
        start_time: _str | time,
        end_time: _str | time,
        axis: AxisIndex | None = ...,
    ) -> Series[S1]: ...
    def first(self, offset) -> Series[S1]: ...
    def last(self, offset) -> Series[S1]: ...
    def rank(
        self,
        axis: AxisIndex = ...,
        method: Literal["average", "min", "max", "first", "dense"] = ...,
        numeric_only: _bool = ...,
        na_option: Literal["keep", "top", "bottom"] = ...,
        ascending: _bool = ...,
        pct: _bool = ...,
    ) -> Series[float]: ...
    @overload
    def where(
        self,
        cond: (
            Series[S1]
            | Series[_bool]
            | np.ndarray
            | Callable[[Series[S1]], Series[bool]]
            | Callable[[S1], bool]
        ),
        other=...,
        *,
        inplace: Literal[True],
        axis: AxisIndex | None = ...,
        level: Level | None = ...,
    ) -> None: ...
    @overload
    def where(
        self,
        cond: (
            Series[S1]
            | Series[_bool]
            | np.ndarray
            | Callable[[Series[S1]], Series[bool]]
            | Callable[[S1], bool]
        ),
        other=...,
        *,
        inplace: Literal[False] = ...,
        axis: AxisIndex | None = ...,
        level: Level | None = ...,
    ) -> Self: ...
    @overload
    def mask(
        self,
        cond: (
            Series[S1]
            | Series[_bool]
            | np.ndarray
            | Callable[[Series[S1]], Series[bool]]
            | Callable[[S1], bool]
        ),
        other: Scalar | Series[S1] | DataFrame | Callable | NAType | None = ...,
        *,
        inplace: Literal[True],
        axis: AxisIndex | None = ...,
        level: Level | None = ...,
    ) -> None: ...
    @overload
    def mask(
        self,
        cond: (
            Series[S1]
            | Series[_bool]
            | np.ndarray
            | Callable[[Series[S1]], Series[bool]]
            | Callable[[S1], bool]
        ),
        other: Scalar | Series[S1] | DataFrame | Callable | NAType | None = ...,
        *,
        inplace: Literal[False] = ...,
        axis: AxisIndex | None = ...,
        level: Level | None = ...,
    ) -> Series[S1]: ...
    def case_when(
        self,
        caselist: list[
            tuple[
                Sequence[bool]
                | Series[bool]
                | Callable[[Series], Series | np.ndarray | Sequence[bool]],
                ListLikeU | Scalar | Callable[[Series], Series | np.ndarray],
            ],
        ],
    ) -> Series: ...
    def truncate(
        self,
        before: date | _str | int | None = ...,
        after: date | _str | int | None = ...,
        axis: AxisIndex | None = ...,
        copy: _bool = ...,
    ) -> Series[S1]: ...
    def tz_convert(
        self,
        tz: TimeZones,
        axis: AxisIndex = ...,
        level: Level | None = ...,
        copy: _bool = ...,
    ) -> Series[S1]: ...
    def tz_localize(
        self,
        tz: TimeZones,
        axis: AxisIndex = ...,
        level: Level | None = ...,
        copy: _bool = ...,
        ambiguous=...,
        nonexistent: _str = ...,
    ) -> Series[S1]: ...
    def abs(self) -> Series[S1]: ...
    def describe(
        self,
        percentiles: list[float] | None = ...,
        include: Literal["all"] | list[S1] | None = ...,
        exclude: S1 | list[S1] | None = ...,
    ) -> Series[S1]: ...
    def pct_change(
        self,
        periods: int = ...,
        fill_method: _str = ...,
        limit: int | None = ...,
        freq=...,
        **kwargs,
    ) -> Series[S1]: ...
    def first_valid_index(self) -> Scalar: ...
    def last_valid_index(self) -> Scalar: ...
    @overload
    def value_counts(
        self,
        normalize: Literal[False] = ...,
        sort: _bool = ...,
        ascending: _bool = ...,
        bins: int | None = ...,
        dropna: _bool = ...,
    ) -> Series[int]: ...
    @overload
    def value_counts(
        self,
        normalize: Literal[True],
        sort: _bool = ...,
        ascending: _bool = ...,
        bins: int | None = ...,
        dropna: _bool = ...,
    ) -> Series[float]: ...
    @property
    def T(self) -> Self: ...
    # The rest of these were left over from the old
    # stubs we shipped in preview. They may belong in
    # the base classes in some cases; I expect stubgen
    # just failed to generate these so I couldn't match
    # them up.
    @overload
    def __add__(self, other: S1 | Self) -> Self: ...
    @overload
    def __add__(
        self,
        other: num | _str | timedelta | Timedelta | _ListLike | Series | np.timedelta64,
    ) -> Series: ...
    # ignore needed for mypy as we want different results based on the arguments
    @overload  # type: ignore[override]
    def __and__(  # pyright: ignore[reportOverlappingOverload]
        self, other: bool | list[int] | MaskType
    ) -> Series[bool]: ...
    @overload
    def __and__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: int | np_ndarray_anyint | Series[int]
    ) -> Series[int]: ...
    # def __array__(self, dtype: Optional[_bool] = ...) -> _np_ndarray
    def __div__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...
    def __eq__(self, other: object) -> Series[_bool]: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __floordiv__(self, other: num | _ListLike | Series[S1]) -> Series[int]: ...
    def __ge__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: S1 | _ListLike | Series[S1] | datetime | timedelta | date
    ) -> Series[_bool]: ...
    def __gt__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: S1 | _ListLike | Series[S1] | datetime | timedelta | date
    ) -> Series[_bool]: ...
    def __le__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: S1 | _ListLike | Series[S1] | datetime | timedelta | date
    ) -> Series[_bool]: ...
    def __lt__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: S1 | _ListLike | Series[S1] | datetime | timedelta | date
    ) -> Series[_bool]: ...
    @overload
    def __mul__(
        self, other: timedelta | Timedelta | TimedeltaSeries | np.timedelta64
    ) -> TimedeltaSeries: ...
    @overload
    def __mul__(self, other: num | _ListLike | Series) -> Series: ...
    def __mod__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...
    def __ne__(self, other: object) -> Series[_bool]: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __pow__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...
    # ignore needed for mypy as we want different results based on the arguments
    @overload  # type: ignore[override]
    def __or__(  # pyright: ignore[reportOverlappingOverload]
        self, other: bool | list[int] | MaskType
    ) -> Series[bool]: ...
    @overload
    def __or__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: int | np_ndarray_anyint | Series[int]
    ) -> Series[int]: ...
    @overload
    def __radd__(self, other: S1 | Series[S1]) -> Self: ...
    @overload
    def __radd__(self, other: num | _str | _ListLike | Series) -> Series: ...
    # ignore needed for mypy as we want different results based on the arguments
    @overload  # type: ignore[override]
    def __rand__(  # pyright: ignore[reportOverlappingOverload]
        self, other: bool | MaskType | list[int]
    ) -> Series[bool]: ...
    @overload
    def __rand__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: int | np_ndarray_anyint | Series[int]
    ) -> Series[int]: ...
    def __rdiv__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...
    def __rdivmod__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __rfloordiv__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...
    def __rmod__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...
    @overload
    def __rmul__(
        self, other: timedelta | Timedelta | TimedeltaSeries | np.timedelta64
    ) -> TimedeltaSeries: ...
    @overload
    def __rmul__(self, other: num | _ListLike | Series) -> Series: ...
    def __rnatmul__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...
    def __rpow__(self, other: num | _ListLike | Series[S1]) -> Series[S1]: ...
    # ignore needed for mypy as we want different results based on the arguments
    @overload  # type: ignore[override]
    def __ror__(  # pyright: ignore[reportOverlappingOverload]
        self, other: bool | MaskType | list[int]
    ) -> Series[bool]: ...
    @overload
    def __ror__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: int | np_ndarray_anyint | Series[int]
    ) -> Series[int]: ...
    def __rsub__(self, other: num | _ListLike | Series[S1]) -> Series: ...
    def __rtruediv__(self, other: num | _ListLike | Series[S1] | Path) -> Series: ...
    # ignore needed for mypy as we want different results based on the arguments
    @overload  # type: ignore[override]
    def __rxor__(  # pyright: ignore[reportOverlappingOverload]
        self, other: bool | MaskType | list[int]
    ) -> Series[bool]: ...
    @overload
    def __rxor__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: int | np_ndarray_anyint | Series[int]
    ) -> Series[int]: ...
    @overload
    def __sub__(
        self: Series[Timestamp],
        other: Timedelta | TimedeltaSeries | TimedeltaIndex | np.timedelta64,
    ) -> TimestampSeries: ...
    @overload
    def __sub__(
        self: Series[Timedelta],
        other: Timedelta | TimedeltaSeries | TimedeltaIndex | np.timedelta64,
    ) -> TimedeltaSeries: ...
    @overload
    def __sub__(
        self, other: Timestamp | datetime | TimestampSeries
    ) -> TimedeltaSeries: ...
    @overload
    def __sub__(self, other: num | _ListLike | Series) -> Series: ...
    def __truediv__(self, other: num | _ListLike | Series[S1] | Path) -> Series: ...
    # ignore needed for mypy as we want different results based on the arguments
    @overload  # type: ignore[override]
    def __xor__(  # pyright: ignore[reportOverlappingOverload]
        self, other: bool | MaskType | list[int]
    ) -> Series[bool]: ...
    @overload
    def __xor__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: int | np_ndarray_anyint | Series[int]
    ) -> Series[int]: ...
    def __invert__(self) -> Series[bool]: ...
    # properties
    # @property
    # def array(self) -> _npndarray
    @property
    def at(self) -> _AtIndexer: ...
    @property
    def cat(self) -> CategoricalAccessor: ...
    @property
    def iat(self) -> _iAtIndexer: ...
    @property
    def iloc(self) -> _iLocIndexerSeries[S1]: ...
    @property
    def loc(self) -> _LocIndexerSeries[S1]: ...
    # Methods
    def add(
        self,
        other: Series[S1] | Scalar,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: int = ...,
    ) -> Series[S1]: ...
    def all(
        self,
        axis: AxisIndex = ...,
        bool_only: _bool | None = ...,
        skipna: _bool = ...,
        **kwargs,
    ) -> _bool: ...
    def any(
        self,
        *,
        axis: AxisIndex = ...,
        bool_only: _bool | None = ...,
        skipna: _bool = ...,
        **kwargs,
    ) -> _bool: ...
    def cummax(
        self, axis: AxisIndex | None = ..., skipna: _bool = ..., *args, **kwargs
    ) -> Series[S1]: ...
    def cummin(
        self, axis: AxisIndex | None = ..., skipna: _bool = ..., *args, **kwargs
    ) -> Series[S1]: ...
    def cumprod(
        self, axis: AxisIndex | None = ..., skipna: _bool = ..., *args, **kwargs
    ) -> Series[S1]: ...
    def cumsum(
        self, axis: AxisIndex | None = ..., skipna: _bool = ..., *args, **kwargs
    ) -> Series[S1]: ...
    def divide(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[float]: ...
    def divmod(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    def eq(
        self,
        other: Scalar | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[_bool]: ...
    def ewm(
        self,
        com: float | None = ...,
        span: float | None = ...,
        halflife: float | None = ...,
        alpha: float | None = ...,
        min_periods: int = ...,
        adjust: _bool = ...,
        ignore_na: _bool = ...,
    ) -> ExponentialMovingWindow[Series]: ...
    def expanding(
        self,
        min_periods: int = ...,
        method: CalculationMethod = ...,
    ) -> Expanding[Series]: ...
    def floordiv(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex | None = ...,
    ) -> Series[int]: ...
    def ge(
        self,
        other: Scalar | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[_bool]: ...
    def gt(
        self,
        other: Scalar | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[_bool]: ...
    def item(self) -> S1: ...
    def kurt(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Scalar: ...
    def kurtosis(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Scalar: ...
    def le(
        self,
        other: Scalar | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[_bool]: ...
    def lt(
        self,
        other: Scalar | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[_bool]: ...
    def max(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> S1: ...
    def mean(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> float: ...
    def median(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> float: ...
    def min(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> S1: ...
    def mod(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex | None = ...,
    ) -> Series[S1]: ...
    @overload
    def mul(
        self,
        other: timedelta | Timedelta | TimedeltaSeries | np.timedelta64,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex | None = ...,
    ) -> TimedeltaSeries: ...
    @overload
    def mul(
        self,
        other: num | _ListLike | Series,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex | None = ...,
    ) -> Series: ...
    def multiply(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex | None = ...,
    ) -> Series[S1]: ...
    def ne(
        self,
        other: Scalar | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[_bool]: ...
    def nunique(self, dropna: _bool = ...) -> int: ...
    def pow(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex | None = ...,
    ) -> Series[S1]: ...
    def prod(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        min_count: int = ...,
        **kwargs,
    ) -> Scalar: ...
    def product(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        min_count: int = ...,
        **kwargs,
    ) -> Scalar: ...
    def radd(
        self,
        other: Series[S1] | Scalar,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    def rdivmod(
        self,
        other: Series[S1] | Scalar,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    def rfloordiv(
        self,
        other,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    def rmod(
        self,
        other: Series[S1] | Scalar,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    @overload
    def rmul(
        self,
        other: timedelta | Timedelta | TimedeltaSeries | np.timedelta64,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> TimedeltaSeries: ...
    @overload
    def rmul(
        self,
        other: num | _ListLike | Series,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series: ...
    @overload
    def rolling(
        self,
        window: int | _str | timedelta | BaseOffset | BaseIndexer,
        min_periods: int | None = ...,
        center: _bool = ...,
        on: _str | None = ...,
        closed: IntervalClosedType | None = ...,
        step: int | None = ...,
        method: CalculationMethod = ...,
        *,
        win_type: _str,
    ) -> Window[Series]: ...
    @overload
    def rolling(
        self,
        window: int | _str | timedelta | BaseOffset | BaseIndexer,
        min_periods: int | None = ...,
        center: _bool = ...,
        on: _str | None = ...,
        closed: IntervalClosedType | None = ...,
        step: int | None = ...,
        method: CalculationMethod = ...,
        *,
        win_type: None = ...,
    ) -> Rolling[Series]: ...
    def rpow(
        self,
        other: Series[S1] | Scalar,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    def rsub(
        self,
        other: Series[S1] | Scalar,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    def rtruediv(
        self,
        other,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[S1]: ...
    def sem(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        ddof: int = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Scalar: ...
    def skew(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Scalar: ...
    def std(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        ddof: int = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> float: ...
    def sub(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex | None = ...,
    ) -> Series[S1]: ...
    def subtract(
        self,
        other: num | _ListLike | Series[S1],
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex | None = ...,
    ) -> Series[S1]: ...
    # ignore needed because of mypy, for using `Never` as type-var.
    @overload
    def sum(
        self: Series[Never],
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        min_count: int = ...,
        **kwargs,
    ) -> Any: ...
    # ignore needed because of mypy, for overlapping overloads
    # between `Series[bool]` and `Series[int]`.
    @overload
    def sum(
        self: Series[bool],
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        min_count: int = ...,
        **kwargs,
    ) -> int: ...
    @overload
    def sum(
        self: Series[S1],
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        min_count: int = ...,
        **kwargs,
    ) -> S1: ...
    def to_list(self) -> list[S1]: ...
    def to_numpy(
        self,
        dtype: npt.DTypeLike | None = ...,
        copy: bool = ...,
        na_value: Scalar = ...,
        **kwargs,
    ) -> np.ndarray: ...
    def tolist(self) -> list[S1]: ...
    def truediv(
        self,
        other,
        level: Level | None = ...,
        fill_value: float | None = ...,
        axis: AxisIndex = ...,
    ) -> Series[float]: ...
    def var(
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        ddof: int = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Scalar: ...
    # Rename axis with `mapper`, `axis`, and `inplace=True`
    @overload
    def rename_axis(
        self,
        mapper: Scalar | ListLike | None = ...,
        *,
        axis: AxisIndex | None = ...,
        copy: _bool = ...,
        inplace: Literal[True],
    ) -> None: ...
    # Rename axis with `mapper`, `axis`, and `inplace=False`
    @overload
    def rename_axis(
        self,
        mapper: Scalar | ListLike | None = ...,
        *,
        axis: AxisIndex | None = ...,
        copy: _bool = ...,
        inplace: Literal[False] = ...,
    ) -> Self: ...
    # Rename axis with `index` and `inplace=True`
    @overload
    def rename_axis(
        self,
        *,
        index: Scalar | ListLike | Callable | dict | None = ...,
        copy: _bool = ...,
        inplace: Literal[True],
    ) -> None: ...
    # Rename axis with `index` and `inplace=False`
    @overload
    def rename_axis(
        self,
        *,
        index: Scalar | ListLike | Callable | dict | None = ...,
        copy: _bool = ...,
        inplace: Literal[False] = ...,
    ) -> Self: ...
    def set_axis(self, labels, *, axis: Axis = ..., copy: _bool = ...) -> Self: ...
    def __iter__(self) -> Iterator[S1]: ...
    def xs(
        self,
        key: Hashable,
        axis: AxisIndex = ...,
        level: Level | None = ...,
        drop_level: _bool = ...,
    ) -> Self: ...
    def __bool__(self) -> NoReturn: ...

class TimestampSeries(Series[Timestamp]):
    @property
    def dt(self) -> TimestampProperties: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __add__(self, other: TimedeltaSeries | np.timedelta64 | timedelta | BaseOffset) -> TimestampSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __radd__(self, other: TimedeltaSeries | np.timedelta64 | timedelta) -> TimestampSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    @overload  # type: ignore[override]
    def __sub__(
        self, other: Timestamp | datetime | TimestampSeries
    ) -> TimedeltaSeries: ...
    @overload
    def __sub__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        other: (
            timedelta | TimedeltaSeries | TimedeltaIndex | np.timedelta64 | BaseOffset
        ),
    ) -> TimestampSeries: ...
    def __mul__(self, other: float | Series[int] | Series[float] | Sequence[float]) -> TimestampSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __truediv__(self, other: float | Series[int] | Series[float] | Sequence[float]) -> TimestampSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def unique(self) -> DatetimeArray: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def mean(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Timestamp: ...
    def median(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Timestamp: ...
    def std(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        ddof: int = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Timedelta: ...
    def diff(self, periods: int = ...) -> TimedeltaSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]

class TimedeltaSeries(Series[Timedelta]):
    # ignores needed because of mypy
    @overload  # type: ignore[override]
    def __add__(self, other: Period) -> PeriodSeries: ...
    @overload
    def __add__(
        self, other: datetime | Timestamp | TimestampSeries | DatetimeIndex
    ) -> TimestampSeries: ...
    @overload
    def __add__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: timedelta | Timedelta | np.timedelta64
    ) -> TimedeltaSeries: ...
    def __radd__(self, other: datetime | Timestamp | TimestampSeries) -> TimestampSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __mul__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: num | Sequence[num] | Series[int] | Series[float]
    ) -> TimedeltaSeries: ...
    def unique(self) -> TimedeltaArray: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __sub__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        other: (
            timedelta | Timedelta | TimedeltaSeries | TimedeltaIndex | np.timedelta64
        ),
    ) -> TimedeltaSeries: ...
    @overload  # type: ignore[override]
    def __truediv__(self, other: float | Sequence[float]) -> Self: ...
    @overload
    def __truediv__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        other: (
            timedelta
            | TimedeltaSeries
            | np.timedelta64
            | TimedeltaIndex
            | Sequence[timedelta]
        ),
    ) -> Series[float]: ...
    def __rtruediv__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        other: (
            timedelta
            | TimedeltaSeries
            | np.timedelta64
            | TimedeltaIndex
            | Sequence[timedelta]
        ),
    ) -> Series[float]: ...
    @overload  # type: ignore[override]
    def __floordiv__(self, other: float | Sequence[float]) -> Self: ...
    @overload
    def __floordiv__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        other: (
            timedelta
            | TimedeltaSeries
            | np.timedelta64
            | TimedeltaIndex
            | Sequence[timedelta]
        ),
    ) -> Series[int]: ...
    def __rfloordiv__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        other: (
            timedelta
            | TimedeltaSeries
            | np.timedelta64
            | TimedeltaIndex
            | Sequence[timedelta]
        ),
    ) -> Series[int]: ...
    @property
    def dt(self) -> TimedeltaProperties: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def mean(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Timedelta: ...
    def median(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Timedelta: ...
    def std(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        axis: AxisIndex | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        ddof: int = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Timedelta: ...
    def diff(self, periods: int = ...) -> TimedeltaSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]

class PeriodSeries(Series[Period]):
    @property
    def dt(self) -> PeriodProperties: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def __sub__(self, other: PeriodSeries) -> OffsetSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
    def diff(self, periods: int = ...) -> OffsetSeries: ...  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]

class OffsetSeries(Series[BaseOffset]):
    @overload  # type: ignore[override]
    def __radd__(self, other: Period) -> PeriodSeries: ...
    @overload
    def __radd__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: BaseOffset
    ) -> OffsetSeries: ...

class IntervalSeries(Series[Interval[_OrderableT]], Generic[_OrderableT]):
    @property
    def array(self) -> IntervalArray: ...
    def diff(self, periods: int = ...) -> Never: ...
