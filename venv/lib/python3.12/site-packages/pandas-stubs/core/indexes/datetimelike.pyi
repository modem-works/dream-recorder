import numpy as np
from pandas.core.indexes.extension import ExtensionIndex
from pandas.core.indexes.timedeltas import TimedeltaIndex
from typing_extensions import Self

from pandas._libs.tslibs import BaseOffset
from pandas._typing import (
    S1,
    AxisIndex,
    TimeUnit,
)

class DatetimeIndexOpsMixin(ExtensionIndex[S1]):
    @property
    def freq(self) -> BaseOffset | None: ...
    @property
    def freqstr(self) -> str | None: ...
    @property
    def is_all_dates(self) -> bool: ...
    def min(
        self, axis: AxisIndex | None = ..., skipna: bool = ..., *args, **kwargs
    ) -> S1: ...
    def argmin(
        self, axis: AxisIndex | None = ..., skipna: bool = ..., *args, **kwargs
    ) -> np.int64: ...
    def max(
        self, axis: AxisIndex | None = ..., skipna: bool = ..., *args, **kwargs
    ) -> S1: ...
    def argmax(
        self, axis: AxisIndex | None = ..., skipna: bool = ..., *args, **kwargs
    ) -> np.int64: ...
    def __rsub__(  # type: ignore[override] # pyright: ignore[reportIncompatibleMethodOverride]
        self, other: DatetimeIndexOpsMixin
    ) -> TimedeltaIndex: ...

class DatetimeTimedeltaMixin(DatetimeIndexOpsMixin[S1]):
    @property
    def unit(self) -> TimeUnit: ...
    def as_unit(self, unit: TimeUnit) -> Self: ...
