from collections.abc import (
    Callable,
    Hashable,
    Mapping,
    Sequence,
)
import datetime
from typing import (
    Literal,
    overload,
)

import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.groupby.grouper import Grouper
from pandas.core.indexes.base import Index
from pandas.core.series import Series
from typing_extensions import TypeAlias

from pandas._typing import (
    AnyArrayLike,
    ArrayLike,
    HashableT1,
    HashableT2,
    HashableT3,
    Label,
    Scalar,
    ScalarT,
    npt,
)

_PivotAggCallable: TypeAlias = Callable[[Series], ScalarT]

_PivotAggFunc: TypeAlias = (
    _PivotAggCallable
    | np.ufunc
    | Literal["mean", "sum", "count", "min", "max", "median", "std", "var"]
)

_NonIterableHashable: TypeAlias = (
    str
    | datetime.date
    | datetime.datetime
    | datetime.timedelta
    | bool
    | int
    | float
    | complex
    | pd.Timestamp
    | pd.Timedelta
)

_PivotTableIndexTypes: TypeAlias = Label | list[HashableT1] | Series | Grouper | None
_PivotTableColumnsTypes: TypeAlias = Label | list[HashableT2] | Series | Grouper | None

_ExtendedAnyArrayLike: TypeAlias = AnyArrayLike | ArrayLike

@overload
def pivot_table(
    data: DataFrame,
    values: Label | list[HashableT3] | None = ...,
    index: _PivotTableIndexTypes = ...,
    columns: _PivotTableColumnsTypes = ...,
    aggfunc: (
        _PivotAggFunc | list[_PivotAggFunc] | Mapping[Hashable, _PivotAggFunc]
    ) = ...,
    fill_value: Scalar | None = ...,
    margins: bool = ...,
    dropna: bool = ...,
    margins_name: str = ...,
    observed: bool = ...,
    sort: bool = ...,
) -> DataFrame: ...

# Can only use Index or ndarray when index or columns is a Grouper
@overload
def pivot_table(
    data: DataFrame,
    values: Label | list[HashableT3] | None = ...,
    *,
    index: Grouper,
    columns: _PivotTableColumnsTypes | Index | npt.NDArray = ...,
    aggfunc: (
        _PivotAggFunc | list[_PivotAggFunc] | Mapping[Hashable, _PivotAggFunc]
    ) = ...,
    fill_value: Scalar | None = ...,
    margins: bool = ...,
    dropna: bool = ...,
    margins_name: str = ...,
    observed: bool = ...,
    sort: bool = ...,
) -> DataFrame: ...
@overload
def pivot_table(
    data: DataFrame,
    values: Label | list[HashableT3] | None = ...,
    index: _PivotTableIndexTypes | Index | npt.NDArray = ...,
    *,
    columns: Grouper,
    aggfunc: (
        _PivotAggFunc | list[_PivotAggFunc] | Mapping[Hashable, _PivotAggFunc]
    ) = ...,
    fill_value: Scalar | None = ...,
    margins: bool = ...,
    dropna: bool = ...,
    margins_name: str = ...,
    observed: bool = ...,
    sort: bool = ...,
) -> DataFrame: ...
def pivot(
    data: DataFrame,
    *,
    index: _NonIterableHashable | list[HashableT1] = ...,
    columns: _NonIterableHashable | list[HashableT2] = ...,
    values: _NonIterableHashable | list[HashableT3] = ...,
) -> DataFrame: ...
@overload
def crosstab(
    index: list | _ExtendedAnyArrayLike | list[Sequence | _ExtendedAnyArrayLike],
    columns: list | _ExtendedAnyArrayLike | list[Sequence | _ExtendedAnyArrayLike],
    values: list | _ExtendedAnyArrayLike,
    rownames: list[HashableT1] | None = ...,
    colnames: list[HashableT2] | None = ...,
    *,
    aggfunc: str | np.ufunc | Callable[[Series], float],
    margins: bool = ...,
    margins_name: str = ...,
    dropna: bool = ...,
    normalize: bool | Literal[0, 1, "all", "index", "columns"] = ...,
) -> DataFrame: ...
@overload
def crosstab(
    index: list | _ExtendedAnyArrayLike | list[Sequence | _ExtendedAnyArrayLike],
    columns: list | _ExtendedAnyArrayLike | list[Sequence | _ExtendedAnyArrayLike],
    values: None = ...,
    rownames: list[HashableT1] | None = ...,
    colnames: list[HashableT2] | None = ...,
    aggfunc: None = ...,
    margins: bool = ...,
    margins_name: str = ...,
    dropna: bool = ...,
    normalize: bool | Literal[0, 1, "all", "index", "columns"] = ...,
) -> DataFrame: ...
