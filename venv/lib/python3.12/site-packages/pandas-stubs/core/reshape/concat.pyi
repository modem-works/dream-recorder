from collections.abc import (
    Iterable,
    Mapping,
    Sequence,
)
from typing import (
    Any,
    Literal,
    overload,
)

from pandas import (
    DataFrame,
    Series,
)
from typing_extensions import Never

from pandas._typing import (
    Axis,
    AxisIndex,
    HashableT1,
    HashableT2,
    HashableT3,
    HashableT4,
)

@overload
def concat(  # type: ignore[overload-overlap]
    objs: Iterable[DataFrame] | Mapping[HashableT1, DataFrame],
    *,
    axis: Axis = ...,
    join: Literal["inner", "outer"] = ...,
    ignore_index: bool = ...,
    keys: Iterable[HashableT2] = ...,
    levels: Sequence[list[HashableT3] | tuple[HashableT3, ...]] = ...,
    names: list[HashableT4] | None = ...,
    verify_integrity: bool = ...,
    sort: bool = ...,
    copy: bool = ...,
) -> DataFrame: ...
@overload
def concat(  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
    objs: Iterable[Series[Any]] | Mapping[HashableT1, Series[Any]],
    *,
    axis: AxisIndex = ...,
    join: Literal["inner", "outer"] = ...,
    ignore_index: bool = ...,
    keys: Iterable[HashableT2] = ...,
    levels: Sequence[list[HashableT3] | tuple[HashableT3, ...]] = ...,
    names: list[HashableT4] | None = ...,
    verify_integrity: bool = ...,
    sort: bool = ...,
    copy: bool = ...,
) -> Series[Any]: ...
@overload
def concat(  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
    objs: (
        Iterable[Series[Any] | DataFrame] | Mapping[HashableT1, Series[Any] | DataFrame]
    ),
    *,
    axis: Axis = ...,
    join: Literal["inner", "outer"] = ...,
    ignore_index: bool = ...,
    keys: Iterable[HashableT2] = ...,
    levels: Sequence[list[HashableT3] | tuple[HashableT3, ...]] = ...,
    names: list[HashableT4] | None = ...,
    verify_integrity: bool = ...,
    sort: bool = ...,
    copy: bool = ...,
) -> DataFrame: ...
@overload
def concat(
    objs: Iterable[None] | Mapping[HashableT1, None],
    *,
    axis: Axis = ...,
    join: Literal["inner", "outer"] = ...,
    ignore_index: bool = ...,
    keys: Iterable[HashableT2] = ...,
    levels: Sequence[list[HashableT3] | tuple[HashableT3, ...]] = ...,
    names: list[HashableT4] | None = ...,
    verify_integrity: bool = ...,
    sort: bool = ...,
    copy: bool = ...,
) -> Never: ...
@overload
def concat(  # type: ignore[overload-overlap]
    objs: Iterable[DataFrame | None] | Mapping[HashableT1, DataFrame | None],
    *,
    axis: Axis = ...,
    join: Literal["inner", "outer"] = ...,
    ignore_index: bool = ...,
    keys: Iterable[HashableT2] = ...,
    levels: Sequence[list[HashableT3] | tuple[HashableT3, ...]] = ...,
    names: list[HashableT4] | None = ...,
    verify_integrity: bool = ...,
    sort: bool = ...,
    copy: bool = ...,
) -> DataFrame: ...
@overload
def concat(  # type: ignore[overload-overlap]
    objs: Iterable[Series[Any] | None] | Mapping[HashableT1, Series[Any] | None],
    *,
    axis: AxisIndex = ...,
    join: Literal["inner", "outer"] = ...,
    ignore_index: bool = ...,
    keys: Iterable[HashableT2] = ...,
    levels: Sequence[list[HashableT3] | tuple[HashableT3, ...]] = ...,
    names: list[HashableT4] | None = ...,
    verify_integrity: bool = ...,
    sort: bool = ...,
    copy: bool = ...,
) -> Series[Any]: ...
@overload
def concat(
    objs: (
        Iterable[Series[Any] | DataFrame | None]
        | Mapping[HashableT1, Series[Any] | DataFrame | None]
    ),
    *,
    axis: Axis = ...,
    join: Literal["inner", "outer"] = ...,
    ignore_index: bool = ...,
    keys: Iterable[HashableT2] = ...,
    levels: Sequence[list[HashableT3] | tuple[HashableT3, ...]] = ...,
    names: list[HashableT4] | None = ...,
    verify_integrity: bool = ...,
    sort: bool = ...,
    copy: bool = ...,
) -> DataFrame: ...

# Including either of the next 2 overloads causes mypy to complain about
# test_pandas.py:test_types_concat() in assert_type(pd.concat([s, s2]), "pd.Series")
# It thinks that pd.concat([s, s2]) is Any .  May be due to Series being
# Generic, or the axis argument being unspecified, and then there is partial
# overlap with the first 2 overloads.
#
# @overload
# def concat(
#     objs: Union[
#         Iterable[Union[Series, DataFrame]], Mapping[HashableT, Union[Series, DataFrame]]
#     ],
#     axis: Literal[0, "index"] = ...,
#     join: str = ...,
#     ignore_index: bool = ...,
#     keys=...,
#     levels=...,
#     names=...,
#     verify_integrity: bool = ...,
#     sort: bool = ...,
#     copy: bool = ...,
# ) -> Union[DataFrame, Series]: ...

# @overload
# def concat(
#     objs: Union[
#         Iterable[Union[Series, DataFrame]], Mapping[HashableT, Union[Series, DataFrame]]
#     ],
#     axis: Axis = ...,
#     join: str = ...,
#     ignore_index: bool = ...,
#     keys=...,
#     levels=...,
#     names=...,
#     verify_integrity: bool = ...,
#     sort: bool = ...,
#     copy: bool = ...,
# ) -> Union[DataFrame, Series]: ...
