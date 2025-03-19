from datetime import timedelta
from typing import (
    Literal,
    overload,
)

from pandas import (
    DataFrame,
    Series,
    Timedelta,
)

from pandas._typing import (
    AnyArrayLike,
    HashableT,
    JoinHow,
    Label,
    MergeHow,
    ValidationOptions,
)

def merge(
    left: DataFrame | Series,
    right: DataFrame | Series,
    how: MergeHow = ...,
    on: Label | list[HashableT] | AnyArrayLike | None = ...,
    left_on: Label | list[HashableT] | AnyArrayLike | None = ...,
    right_on: Label | list[HashableT] | AnyArrayLike | None = ...,
    left_index: bool = ...,
    right_index: bool = ...,
    sort: bool = ...,
    suffixes: (
        list[str | None] | tuple[str, str] | tuple[None, str] | tuple[str, None]
    ) = ...,
    indicator: bool | str = ...,
    validate: ValidationOptions = ...,
) -> DataFrame: ...
@overload
def merge_ordered(
    left: DataFrame,
    right: DataFrame,
    on: Label | list[HashableT] | None = ...,
    left_on: Label | list[HashableT] | None = ...,
    right_on: Label | list[HashableT] | None = ...,
    left_by: Label | list[HashableT] | None = ...,
    right_by: Label | list[HashableT] | None = ...,
    fill_method: Literal["ffill"] | None = ...,
    suffixes: (
        list[str | None] | tuple[str, str] | tuple[None, str] | tuple[str, None]
    ) = ...,
    how: JoinHow = ...,
) -> DataFrame: ...
@overload
def merge_ordered(
    left: Series,
    right: DataFrame | Series,
    on: Label | list[HashableT] | None = ...,
    left_on: Label | list[HashableT] | None = ...,
    right_on: Label | list[HashableT] | None = ...,
    left_by: None = ...,
    right_by: None = ...,
    fill_method: Literal["ffill"] | None = ...,
    suffixes: (
        list[str | None] | tuple[str, str] | tuple[None, str] | tuple[str, None]
    ) = ...,
    how: JoinHow = ...,
) -> DataFrame: ...
@overload
def merge_ordered(
    left: DataFrame | Series,
    right: Series,
    on: Label | list[HashableT] | None = ...,
    left_on: Label | list[HashableT] | None = ...,
    right_on: Label | list[HashableT] | None = ...,
    left_by: None = ...,
    right_by: None = ...,
    fill_method: Literal["ffill"] | None = ...,
    suffixes: (
        list[str | None] | tuple[str, str] | tuple[None, str] | tuple[str, None]
    ) = ...,
    how: JoinHow = ...,
) -> DataFrame: ...
def merge_asof(
    left: DataFrame | Series,
    right: DataFrame | Series,
    on: Label | None = ...,
    left_on: Label | None = ...,
    right_on: Label | None = ...,
    left_index: bool = ...,
    right_index: bool = ...,
    by: Label | list[HashableT] | None = ...,
    left_by: Label | list[HashableT] | None = ...,
    right_by: Label | list[HashableT] | None = ...,
    suffixes: (
        list[str | None] | tuple[str, str] | tuple[None, str] | tuple[str, None]
    ) = ...,
    tolerance: int | timedelta | Timedelta | None = ...,
    allow_exact_matches: bool = ...,
    direction: Literal["backward", "forward", "nearest"] = ...,
) -> DataFrame: ...
