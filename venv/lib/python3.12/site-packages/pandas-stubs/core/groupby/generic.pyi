from collections.abc import (
    Callable,
    Hashable,
    Iterable,
    Iterator,
    Sequence,
)
from typing import (
    Any,
    Generic,
    Literal,
    NamedTuple,
    TypeVar,
    final,
    overload,
)

from matplotlib.axes import Axes as PlotAxes
import numpy as np
from pandas.core.frame import DataFrame
from pandas.core.groupby.groupby import (
    GroupBy,
    GroupByPlot,
)
from pandas.core.series import Series
from typing_extensions import (
    Self,
    TypeAlias,
)

from pandas._libs.tslibs.timestamps import Timestamp
from pandas._typing import (
    S1,
    AggFuncTypeBase,
    AggFuncTypeFrame,
    ByT,
    CorrelationMethod,
    Dtype,
    IndexLabel,
    Level,
    ListLike,
    Scalar,
    TakeIndexer,
    WindowingEngine,
    WindowingEngineKwargs,
)

AggScalar: TypeAlias = str | Callable[..., Any]

class NamedAgg(NamedTuple):
    column: str
    aggfunc: AggScalar

class SeriesGroupBy(GroupBy[Series[S1]], Generic[S1, ByT]):
    @overload
    def aggregate(
        self,
        func: list[AggFuncTypeBase],
        *args,
        engine: WindowingEngine = ...,
        engine_kwargs: WindowingEngineKwargs = ...,
        **kwargs,
    ) -> DataFrame: ...
    @overload
    def aggregate(
        self,
        func: AggFuncTypeBase | None = ...,
        *args,
        engine: WindowingEngine = ...,
        engine_kwargs: WindowingEngineKwargs = ...,
        **kwargs,
    ) -> Series: ...
    agg = aggregate
    def transform(
        self,
        func: Callable | str,
        *args,
        engine: WindowingEngine = ...,
        engine_kwargs: WindowingEngineKwargs = ...,
        **kwargs,
    ) -> Series: ...
    def filter(
        self, func: Callable | str, dropna: bool = ..., *args, **kwargs
    ) -> Series: ...
    def nunique(self, dropna: bool = ...) -> Series[int]: ...
    # describe delegates to super() method but here it has keyword-only parameters
    def describe(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        *,
        percentiles: Iterable[float] | None = ...,
        include: Literal["all"] | list[Dtype] | None = ...,
        exclude: list[Dtype] | None = ...,
    ) -> DataFrame: ...
    @overload
    def value_counts(
        self,
        normalize: Literal[False] = ...,
        sort: bool = ...,
        ascending: bool = ...,
        bins: int | Sequence[int] | None = ...,
        dropna: bool = ...,
    ) -> Series[int]: ...
    @overload
    def value_counts(
        self,
        normalize: Literal[True],
        sort: bool = ...,
        ascending: bool = ...,
        bins: int | Sequence[int] | None = ...,
        dropna: bool = ...,
    ) -> Series[float]: ...
    def take(
        self,
        indices: TakeIndexer,
        **kwargs,
    ) -> Series[S1]: ...
    def skew(
        self,
        skipna: bool = ...,
        numeric_only: bool = ...,
        **kwargs,
    ) -> Series: ...
    @property
    def plot(self) -> GroupByPlot[Self]: ...
    def nlargest(
        self, n: int = ..., keep: Literal["first", "last", "all"] = ...
    ) -> Series[S1]: ...
    def nsmallest(
        self, n: int = ..., keep: Literal["first", "last", "all"] = ...
    ) -> Series[S1]: ...
    def idxmin(self, skipna: bool = ...) -> Series: ...
    def idxmax(self, skipna: bool = ...) -> Series: ...
    def corr(
        self,
        other: Series,
        method: CorrelationMethod = ...,
        min_periods: int | None = ...,
    ) -> Series: ...
    def cov(
        self, other: Series, min_periods: int | None = ..., ddof: int | None = ...
    ) -> Series: ...
    @property
    def is_monotonic_increasing(self) -> Series[bool]: ...
    @property
    def is_monotonic_decreasing(self) -> Series[bool]: ...
    def hist(
        self,
        by: IndexLabel | None = ...,
        ax: PlotAxes | None = ...,
        grid: bool = ...,
        xlabelsize: float | str | None = ...,
        xrot: float | None = ...,
        ylabelsize: float | str | None = ...,
        yrot: float | None = ...,
        figsize: tuple[float, float] | None = ...,
        bins: int | Sequence[int] = ...,
        backend: str | None = ...,
        legend: bool = ...,
        **kwargs,
    ) -> Series: ...  # Series[Axes] but this is not allowed
    @property
    def dtype(self) -> Series: ...
    def unique(self) -> Series: ...
    # Overrides that provide more precise return types over the GroupBy class
    @final  # type: ignore[misc]
    def __iter__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
    ) -> Iterator[tuple[ByT, Series[S1]]]: ...

_TT = TypeVar("_TT", bound=Literal[True, False])

class DataFrameGroupBy(GroupBy[DataFrame], Generic[ByT, _TT]):
    # error: Overload 3 for "apply" will never be used because its parameters overlap overload 1
    @overload  # type: ignore[override]
    def apply(
        self,
        func: Callable[[DataFrame], Scalar | list | dict],
        *args,
        **kwargs,
    ) -> Series: ...
    @overload
    def apply(
        self,
        func: Callable[[DataFrame], Series | DataFrame],
        *args,
        **kwargs,
    ) -> DataFrame: ...
    @overload
    def apply(  # pyright: ignore[reportOverlappingOverload]
        self,
        func: Callable[[Iterable], float],
        *args,
        **kwargs,
    ) -> DataFrame: ...
    # error: overload 1 overlaps overload 2 because of different return types
    @overload
    def aggregate(self, func: Literal["size"]) -> Series: ...  # type: ignore[overload-overlap]
    @overload
    def aggregate(
        self,
        func: AggFuncTypeFrame | None = ...,
        *args,
        engine: WindowingEngine = ...,
        engine_kwargs: WindowingEngineKwargs = ...,
        **kwargs,
    ) -> DataFrame: ...
    agg = aggregate
    def transform(
        self,
        func: Callable | str,
        *args,
        engine: WindowingEngine = ...,
        engine_kwargs: WindowingEngineKwargs = ...,
        **kwargs,
    ) -> DataFrame: ...
    def filter(
        self, func: Callable, dropna: bool = ..., *args, **kwargs
    ) -> DataFrame: ...
    @overload
    def __getitem__(self, key: Scalar) -> SeriesGroupBy[Any, ByT]: ...  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
    @overload
    def __getitem__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, key: Iterable[Hashable]
    ) -> DataFrameGroupBy[ByT, bool]: ...
    def nunique(self, dropna: bool = ...) -> DataFrame: ...
    def idxmax(
        self,
        skipna: bool = ...,
        numeric_only: bool = ...,
    ) -> DataFrame: ...
    def idxmin(
        self,
        skipna: bool = ...,
        numeric_only: bool = ...,
    ) -> DataFrame: ...
    @overload
    def boxplot(
        self,
        subplots: Literal[True] = ...,
        column: IndexLabel | None = ...,
        fontsize: float | str | None = ...,
        rot: float = ...,
        grid: bool = ...,
        ax: PlotAxes | None = ...,
        figsize: tuple[float, float] | None = ...,
        layout: tuple[int, int] | None = ...,
        sharex: bool = ...,
        sharey: bool = ...,
        backend: str | None = ...,
        **kwargs,
    ) -> Series: ...  # Series[PlotAxes] but this is not allowed
    @overload
    def boxplot(
        self,
        subplots: Literal[False],
        column: IndexLabel | None = ...,
        fontsize: float | str | None = ...,
        rot: float = ...,
        grid: bool = ...,
        ax: PlotAxes | None = ...,
        figsize: tuple[float, float] | None = ...,
        layout: tuple[int, int] | None = ...,
        sharex: bool = ...,
        sharey: bool = ...,
        backend: str | None = ...,
        **kwargs,
    ) -> PlotAxes: ...
    @overload
    def boxplot(
        self,
        subplots: bool,
        column: IndexLabel | None = ...,
        fontsize: float | str | None = ...,
        rot: float = ...,
        grid: bool = ...,
        ax: PlotAxes | None = ...,
        figsize: tuple[float, float] | None = ...,
        layout: tuple[int, int] | None = ...,
        sharex: bool = ...,
        sharey: bool = ...,
        backend: str | None = ...,
        **kwargs,
    ) -> PlotAxes | Series: ...  # Series[PlotAxes]
    @overload
    def value_counts(
        self: DataFrameGroupBy[ByT, Literal[True]],
        subset: ListLike | None = ...,
        normalize: Literal[False] = ...,
        sort: bool = ...,
        ascending: bool = ...,
        dropna: bool = ...,
    ) -> Series[int]: ...
    @overload
    def value_counts(
        self: DataFrameGroupBy[ByT, Literal[True]],
        subset: ListLike | None,
        normalize: Literal[True],
        sort: bool = ...,
        ascending: bool = ...,
        dropna: bool = ...,
    ) -> Series[float]: ...
    @overload
    def value_counts(
        self: DataFrameGroupBy[ByT, Literal[False]],
        subset: ListLike | None = ...,
        normalize: Literal[False] = ...,
        sort: bool = ...,
        ascending: bool = ...,
        dropna: bool = ...,
    ) -> DataFrame: ...
    @overload
    def value_counts(
        self: DataFrameGroupBy[ByT, Literal[False]],
        subset: ListLike | None,
        normalize: Literal[True],
        sort: bool = ...,
        ascending: bool = ...,
        dropna: bool = ...,
    ) -> DataFrame: ...
    def take(self, indices: TakeIndexer, **kwargs) -> DataFrame: ...
    @overload
    def skew(
        self,
        skipna: bool = ...,
        numeric_only: bool = ...,
        *,
        level: Level,
        **kwargs,
    ) -> DataFrame: ...
    @overload
    def skew(
        self,
        skipna: bool = ...,
        numeric_only: bool = ...,
        *,
        level: None = ...,
        **kwargs,
    ) -> Series: ...
    @property
    def plot(self) -> GroupByPlot[Self]: ...
    def corr(
        self,
        method: str | Callable[[np.ndarray, np.ndarray], float] = ...,
        min_periods: int = ...,
        numeric_only: bool = ...,
    ) -> DataFrame: ...
    def cov(
        self,
        min_periods: int | None = ...,
        ddof: int | None = ...,
        numeric_only: bool = ...,
    ) -> DataFrame: ...
    def hist(
        self,
        column: IndexLabel | None = ...,
        by: IndexLabel | None = ...,
        grid: bool = ...,
        xlabelsize: float | str | None = ...,
        xrot: float | None = ...,
        ylabelsize: float | str | None = ...,
        yrot: float | None = ...,
        ax: PlotAxes | None = ...,
        sharex: bool = ...,
        sharey: bool = ...,
        figsize: tuple[float, float] | None = ...,
        layout: tuple[int, int] | None = ...,
        bins: int | Sequence[int] = ...,
        backend: str | None = ...,
        legend: bool = ...,
        **kwargs,
    ) -> Series: ...  # Series[Axes] but this is not allowed
    @property
    def dtypes(self) -> Series: ...
    def __getattr__(self, name: str) -> SeriesGroupBy[Any, ByT]: ...
    # Overrides that provide more precise return types over the GroupBy class
    @final  # type: ignore[misc]
    def __iter__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
    ) -> Iterator[tuple[ByT, DataFrame]]: ...
    @overload
    def size(self: DataFrameGroupBy[ByT, Literal[True]]) -> Series[int]: ...
    @overload
    def size(self: DataFrameGroupBy[ByT, Literal[False]]) -> DataFrame: ...
    @overload
    def size(self: DataFrameGroupBy[Timestamp, Literal[True]]) -> Series[int]: ...
    @overload
    def size(self: DataFrameGroupBy[Timestamp, Literal[False]]) -> DataFrame: ...
