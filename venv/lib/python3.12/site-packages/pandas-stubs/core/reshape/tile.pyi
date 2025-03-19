from collections.abc import Sequence
from typing import (
    Literal,
    overload,
)

import numpy as np
from pandas import (
    Categorical,
    CategoricalDtype,
    DatetimeIndex,
    Index,
    Interval,
    IntervalIndex,
    Series,
    Timestamp,
)
from pandas.core.series import TimestampSeries

from pandas._typing import (
    IntervalT,
    Label,
    npt,
)

@overload
def cut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    bins: int | Series | Index[int] | Index[float] | Sequence[int] | Sequence[float],
    right: bool = ...,
    *,
    labels: Literal[False],
    retbins: Literal[True],
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> tuple[npt.NDArray[np.intp], npt.NDArray]: ...
@overload
def cut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    bins: IntervalIndex[IntervalT],
    right: bool = ...,
    *,
    labels: Literal[False],
    retbins: Literal[True],
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> tuple[npt.NDArray[np.intp], IntervalIndex[IntervalT]]: ...
@overload
def cut(  # pyright: ignore[reportOverlappingOverload]
    x: TimestampSeries,
    bins: (
        int
        | TimestampSeries
        | DatetimeIndex
        | Sequence[Timestamp]
        | Sequence[np.datetime64]
    ),
    right: bool = ...,
    labels: Literal[False] | Sequence[Label] | None = ...,
    *,
    retbins: Literal[True],
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> tuple[Series, DatetimeIndex]: ...
@overload
def cut(
    x: TimestampSeries,
    bins: IntervalIndex[Interval[Timestamp]],
    right: bool = ...,
    labels: Sequence[Label] | None = ...,
    *,
    retbins: Literal[True],
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> tuple[Series, DatetimeIndex]: ...
@overload
def cut(
    x: Series,
    bins: int | Series | Index[int] | Index[float] | Sequence[int] | Sequence[float],
    right: bool = ...,
    labels: Literal[False] | Sequence[Label] | None = ...,
    *,
    retbins: Literal[True],
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> tuple[Series, npt.NDArray]: ...
@overload
def cut(
    x: Series,
    bins: IntervalIndex[Interval[int]] | IntervalIndex[Interval[float]],
    right: bool = ...,
    labels: Sequence[Label] | None = ...,
    *,
    retbins: Literal[True],
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> tuple[Series, IntervalIndex]: ...
@overload
def cut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    bins: int | Series | Index[int] | Index[float] | Sequence[int] | Sequence[float],
    right: bool = ...,
    labels: Sequence[Label] | None = ...,
    *,
    retbins: Literal[True],
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> tuple[Categorical, npt.NDArray]: ...
@overload
def cut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    bins: IntervalIndex[IntervalT],
    right: bool = ...,
    labels: Sequence[Label] | None = ...,
    *,
    retbins: Literal[True],
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> tuple[Categorical, IntervalIndex[IntervalT]]: ...
@overload
def cut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    bins: (
        int
        | Series
        | Index[int]
        | Index[float]
        | Sequence[int]
        | Sequence[float]
        | IntervalIndex
    ),
    right: bool = ...,
    *,
    labels: Literal[False],
    retbins: Literal[False] = ...,
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> npt.NDArray[np.intp]: ...
@overload
def cut(
    x: TimestampSeries,
    bins: (
        int
        | TimestampSeries
        | DatetimeIndex
        | Sequence[Timestamp]
        | Sequence[np.datetime64]
        | IntervalIndex[Interval[Timestamp]]
    ),
    right: bool = ...,
    labels: Literal[False] | Sequence[Label] | None = ...,
    retbins: Literal[False] = ...,
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> Series[CategoricalDtype]: ...
@overload
def cut(
    x: Series,
    bins: (
        int
        | Series
        | Index[int]
        | Index[float]
        | Sequence[int]
        | Sequence[float]
        | IntervalIndex
    ),
    right: bool = ...,
    labels: Literal[False] | Sequence[Label] | None = ...,
    retbins: Literal[False] = ...,
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> Series: ...
@overload
def cut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    bins: (
        int
        | Series
        | Index[int]
        | Index[float]
        | Sequence[int]
        | Sequence[float]
        | IntervalIndex
    ),
    right: bool = ...,
    labels: Sequence[Label] | None = ...,
    retbins: Literal[False] = ...,
    precision: int = ...,
    include_lowest: bool = ...,
    duplicates: Literal["raise", "drop"] = ...,
    ordered: bool = ...,
) -> Categorical: ...
@overload
def qcut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    q: int | Sequence[float] | Series[float] | Index[float] | npt.NDArray,
    *,
    labels: Literal[False],
    retbins: Literal[False] = ...,
    precision: int = ...,
    duplicates: Literal["raise", "drop"] = ...,
) -> npt.NDArray[np.intp]: ...
@overload
def qcut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    q: int | Sequence[float] | Series[float] | Index[float] | npt.NDArray,
    labels: Sequence[Label] | None = ...,
    retbins: Literal[False] = ...,
    precision: int = ...,
    duplicates: Literal["raise", "drop"] = ...,
) -> Categorical: ...
@overload
def qcut(
    x: Series,
    q: int | Sequence[float] | Series[float] | Index[float] | npt.NDArray,
    labels: Literal[False] | Sequence[Label] | None = ...,
    retbins: Literal[False] = ...,
    precision: int = ...,
    duplicates: Literal["raise", "drop"] = ...,
) -> Series: ...
@overload
def qcut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    q: int | Sequence[float] | Series[float] | Index[float] | npt.NDArray,
    *,
    labels: Literal[False],
    retbins: Literal[True],
    precision: int = ...,
    duplicates: Literal["raise", "drop"] = ...,
) -> tuple[npt.NDArray[np.intp], npt.NDArray[np.double]]: ...
@overload
def qcut(
    x: Series,
    q: int | Sequence[float] | Series[float] | Index[float] | npt.NDArray,
    labels: Literal[False] | Sequence[Label] | None = ...,
    *,
    retbins: Literal[True],
    precision: int = ...,
    duplicates: Literal["raise", "drop"] = ...,
) -> tuple[Series, npt.NDArray[np.double]]: ...
@overload
def qcut(
    x: Index | npt.NDArray | Sequence[int] | Sequence[float],
    q: int | Sequence[float] | Series[float] | Index[float] | npt.NDArray,
    labels: Sequence[Label] | None = ...,
    *,
    retbins: Literal[True],
    precision: int = ...,
    duplicates: Literal["raise", "drop"] = ...,
) -> tuple[Categorical, npt.NDArray[np.double]]: ...
