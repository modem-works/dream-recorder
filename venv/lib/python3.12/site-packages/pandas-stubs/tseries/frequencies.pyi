from typing import overload

from pandas import (
    DatetimeIndex,
    Series,
    TimedeltaIndex,
)

from pandas._typing import Frequency

from pandas.tseries.offsets import DateOffset

def get_period_alias(offset_str: str) -> str | None: ...
@overload
def to_offset(freq: None) -> None: ...
@overload
def to_offset(freq: Frequency) -> DateOffset: ...
def get_offset(name: str) -> DateOffset: ...
def infer_freq(index: Series | DatetimeIndex | TimedeltaIndex) -> str | None: ...
