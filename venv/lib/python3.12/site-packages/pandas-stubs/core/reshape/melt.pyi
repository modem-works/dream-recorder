from collections.abc import Hashable

import numpy as np
from pandas.core.frame import DataFrame

from pandas._typing import HashableT

def melt(
    frame: DataFrame,
    id_vars: tuple | list | np.ndarray | None = ...,
    value_vars: tuple | list | np.ndarray | None = ...,
    var_name: str | None = ...,
    value_name: Hashable = ...,
    col_level: int | str | None = ...,
    ignore_index: bool = ...,
) -> DataFrame: ...
def lreshape(
    data: DataFrame, groups: dict[HashableT, list[HashableT]], dropna: bool = ...
) -> DataFrame: ...
def wide_to_long(
    df: DataFrame,
    stubnames: str | list[str],
    i: str | list[str],
    j: str,
    sep: str = ...,
    suffix: str = ...,
) -> DataFrame: ...
