from typing import (
    Any,
    overload,
)

import numpy as np
from numpy import typing as npt
from pandas import (
    DataFrame,
    Index,
    Series,
)
from typing_extensions import TypeIs

from pandas._libs.missing import NAType
from pandas._libs.tslibs import NaTType
from pandas._typing import (
    ArrayLike,
    Scalar,
    ScalarT,
)

isposinf_scalar = ...
isneginf_scalar = ...

@overload
def isna(obj: DataFrame) -> DataFrame: ...
@overload
def isna(obj: Series[Any]) -> Series[bool]: ...
@overload
def isna(obj: Index[Any] | list[Any] | ArrayLike) -> npt.NDArray[np.bool_]: ...
@overload
def isna(
    obj: Scalar | NaTType | NAType | None,
) -> TypeIs[NaTType | NAType | None]: ...

isnull = isna

@overload
def notna(obj: DataFrame) -> DataFrame: ...
@overload
def notna(obj: Series[Any]) -> Series[bool]: ...
@overload
def notna(obj: Index[Any] | list[Any] | ArrayLike) -> npt.NDArray[np.bool_]: ...
@overload
def notna(obj: ScalarT | NaTType | NAType | None) -> TypeIs[ScalarT]: ...

notnull = notna
