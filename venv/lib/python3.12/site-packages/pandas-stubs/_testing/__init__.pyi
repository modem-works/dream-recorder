from collections.abc import (
    Container,
    Generator,
    Iterable,
)
from contextlib import contextmanager
from typing import (
    Any,
    Literal,
    overload,
)
import warnings

from matplotlib.artist import Artist
import numpy as np
from pandas import (
    Categorical,
    DataFrame,
    Index,
    Series,
)
from pandas.arrays import (
    DatetimeArray,
    IntervalArray,
    PeriodArray,
    SparseArray,
    TimedeltaArray,
)
from pandas.core.arrays.base import ExtensionArray

from pandas._typing import (
    AnyArrayLike,
    T,
)

def assert_almost_equal(
    left: T,
    right: T,
    check_dtype: bool | Literal["equiv"] = ...,
    rtol: float = ...,
    atol: float = ...,
    **kwargs,
) -> None: ...
def assert_dict_equal(left: dict, right: dict, compare_keys: bool = ...) -> None: ...
def assert_index_equal(
    left: Index,
    right: Index,
    exact: bool | Literal["equiv"] = ...,
    check_names: bool = ...,
    check_exact: bool = ...,
    check_categorical: bool = ...,
    check_order: bool = ...,
    rtol: float = ...,
    atol: float = ...,
    obj: str = ...,
) -> None: ...
def assert_class_equal(
    left: T, right: T, exact: bool | Literal["equiv"] = ..., obj: str = ...
) -> None: ...
def assert_attr_equal(
    attr: str, left: object, right: object, obj: str = ...
) -> None: ...
def assert_is_valid_plot_return_object(
    objs: Series | np.ndarray | Artist | tuple | dict,
) -> None: ...
def assert_is_sorted(seq: AnyArrayLike) -> None: ...
def assert_categorical_equal(
    left: Categorical,
    right: Categorical,
    check_dtype: bool = ...,
    check_category_order: bool = ...,
    obj: str = ...,
) -> None: ...
def assert_interval_array_equal(
    left: IntervalArray,
    right: IntervalArray,
    exact: bool | Literal["equiv"] = ...,
    obj: str = ...,
) -> None: ...
def assert_period_array_equal(
    left: PeriodArray, right: PeriodArray, obj: str = ...
) -> None: ...
def assert_datetime_array_equal(
    left: DatetimeArray, right: DatetimeArray, check_freq: bool = ...
) -> None: ...
def assert_timedelta_array_equal(
    left: TimedeltaArray, right: TimedeltaArray, check_freq: bool = ...
) -> None: ...
def assert_numpy_array_equal(
    left,
    right,
    strict_nan: bool = ...,
    check_dtype: bool | Literal["equiv"] = ...,
    err_msg: str | None = ...,
    check_same: Literal["copy", "same"] | None = ...,
    obj: str = ...,
    index_values: Index | np.ndarray | None = ...,
) -> None: ...
def assert_extension_array_equal(
    left: ExtensionArray,
    right: ExtensionArray,
    check_dtype: bool | Literal["equiv"] = ...,
    index_values: Index | np.ndarray | None = ...,
    check_exact: bool = ...,
    rtol: float = ...,
    atol: float = ...,
    obj: str = ...,
) -> None: ...
@overload
def assert_series_equal(
    left: Series,
    right: Series,
    check_dtype: bool | Literal["equiv"] = ...,
    check_index_type: bool | Literal["equiv"] = ...,
    check_series_type: bool = ...,
    check_names: bool = ...,
    check_exact: bool = ...,
    check_datetimelike_compat: bool = ...,
    check_categorical: bool = ...,
    check_category_order: bool = ...,
    check_freq: bool = ...,
    check_flags: bool = ...,
    rtol: float = ...,
    atol: float = ...,
    obj: str = ...,
    *,
    check_index: Literal[False],
    check_like: Literal[False] = ...,
) -> None: ...
@overload
def assert_series_equal(
    left: Series,
    right: Series,
    check_dtype: bool | Literal["equiv"] = ...,
    check_index_type: bool | Literal["equiv"] = ...,
    check_series_type: bool = ...,
    check_names: bool = ...,
    check_exact: bool = ...,
    check_datetimelike_compat: bool = ...,
    check_categorical: bool = ...,
    check_category_order: bool = ...,
    check_freq: bool = ...,
    check_flags: bool = ...,
    rtol: float = ...,
    atol: float = ...,
    obj: str = ...,
    *,
    check_index: Literal[True] = ...,
    check_like: bool = ...,
) -> None: ...
def assert_frame_equal(
    left: DataFrame,
    right: DataFrame,
    check_dtype: bool | Literal["equiv"] = ...,
    check_index_type: bool | Literal["equiv"] = ...,
    check_column_type: bool | Literal["equiv"] = ...,
    check_frame_type: bool = ...,
    check_names: bool = ...,
    by_blocks: bool = ...,
    check_exact: bool = ...,
    check_datetimelike_compat: bool = ...,
    check_categorical: bool = ...,
    check_like: bool = ...,
    check_freq: bool = ...,
    check_flags: bool = ...,
    rtol: float = ...,
    atol: float = ...,
    obj: str = ...,
) -> None: ...
def assert_equal(left, right, **kwargs) -> None: ...
def assert_sp_array_equal(left: SparseArray, right: SparseArray) -> None: ...
def assert_contains_all(iterable: Iterable[T], dic: Container[T]) -> None: ...
def assert_copy(iter1: Iterable[T], iter2: Iterable[T], **eql_kwargs) -> None: ...
@contextmanager
def assert_produces_warning(
    expected_warning: (
        type[Warning] | Literal[False] | tuple[type[Warning], ...] | None
    ) = ...,
    filter_level: Literal[
        "error", "ignore", "always", "default", "module", "once"
    ] = ...,
    check_stacklevel: bool = ...,
    raise_on_extra_warnings: bool = ...,
    match: str | None = None,
) -> Generator[list[warnings.WarningMessage], None, None]: ...
@contextmanager
def ensure_clean(
    filename: str | None = ..., return_filelike: bool = ..., **kwargs: Any
) -> Generator[str, None, None]: ...
