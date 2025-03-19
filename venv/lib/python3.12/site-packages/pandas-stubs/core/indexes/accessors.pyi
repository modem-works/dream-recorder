import datetime as dt
from datetime import (
    timedelta,
    tzinfo,
)
from typing import (
    Generic,
    Literal,
    TypeVar,
)

from _typing import TimeZones
import numpy as np
import numpy.typing as npt
from pandas import (
    DatetimeIndex,
    Index,
    PeriodIndex,
    Timedelta,
    TimedeltaIndex,
)
from pandas.core.accessor import PandasDelegate
from pandas.core.arrays import (
    DatetimeArray,
    PeriodArray,
)
from pandas.core.base import NoNewAttributesMixin
from pandas.core.frame import DataFrame
from pandas.core.series import (
    PeriodSeries,
    Series,
    TimedeltaSeries,
    TimestampSeries,
)

from pandas._libs.tslibs import BaseOffset
from pandas._libs.tslibs.offsets import DateOffset
from pandas._typing import (
    TimestampConvention,
    TimeUnit,
    np_ndarray_bool,
)

class Properties(PandasDelegate, NoNewAttributesMixin): ...

_DTFieldOpsReturnType = TypeVar("_DTFieldOpsReturnType", bound=Series[int] | Index[int])

class _DayLikeFieldOps(Generic[_DTFieldOpsReturnType]):
    @property
    def year(self) -> _DTFieldOpsReturnType: ...
    @property
    def month(self) -> _DTFieldOpsReturnType: ...
    @property
    def day(self) -> _DTFieldOpsReturnType: ...
    @property
    def hour(self) -> _DTFieldOpsReturnType: ...
    @property
    def minute(self) -> _DTFieldOpsReturnType: ...
    @property
    def second(self) -> _DTFieldOpsReturnType: ...
    @property
    def weekday(self) -> _DTFieldOpsReturnType: ...
    @property
    def dayofweek(self) -> _DTFieldOpsReturnType: ...
    @property
    def day_of_week(self) -> _DTFieldOpsReturnType: ...
    @property
    def dayofyear(self) -> _DTFieldOpsReturnType: ...
    @property
    def day_of_year(self) -> _DTFieldOpsReturnType: ...
    @property
    def quarter(self) -> _DTFieldOpsReturnType: ...
    @property
    def days_in_month(self) -> _DTFieldOpsReturnType: ...
    @property
    def daysinmonth(self) -> _DTFieldOpsReturnType: ...

class _MiniSeconds(Generic[_DTFieldOpsReturnType]):
    @property
    def microsecond(self) -> _DTFieldOpsReturnType: ...
    @property
    def nanosecond(self) -> _DTFieldOpsReturnType: ...

class _DatetimeFieldOps(
    _DayLikeFieldOps[_DTFieldOpsReturnType], _MiniSeconds[_DTFieldOpsReturnType]
): ...

_DTBoolOpsReturnType = TypeVar(
    "_DTBoolOpsReturnType", bound=Series[bool] | np_ndarray_bool
)

class _IsLeapYearProperty(Generic[_DTBoolOpsReturnType]):
    @property
    def is_leap_year(self) -> _DTBoolOpsReturnType: ...

class _DatetimeBoolOps(
    _IsLeapYearProperty[_DTBoolOpsReturnType], Generic[_DTBoolOpsReturnType]
):
    @property
    def is_month_start(self) -> _DTBoolOpsReturnType: ...
    @property
    def is_month_end(self) -> _DTBoolOpsReturnType: ...
    @property
    def is_quarter_start(self) -> _DTBoolOpsReturnType: ...
    @property
    def is_quarter_end(self) -> _DTBoolOpsReturnType: ...
    @property
    def is_year_start(self) -> _DTBoolOpsReturnType: ...
    @property
    def is_year_end(self) -> _DTBoolOpsReturnType: ...

_DTFreqReturnType = TypeVar("_DTFreqReturnType", bound=str | BaseOffset)

class _FreqProperty(Generic[_DTFreqReturnType]):
    @property
    def freq(self) -> _DTFreqReturnType | None: ...

class _TZProperty:
    @property
    def tz(self) -> tzinfo | None: ...

class _DatetimeObjectOps(
    _FreqProperty[_DTFreqReturnType], _TZProperty, Generic[_DTFreqReturnType]
): ...

_DTOtherOpsDateReturnType = TypeVar(
    "_DTOtherOpsDateReturnType", bound=Series[dt.date] | np.ndarray
)
_DTOtherOpsTimeReturnType = TypeVar(
    "_DTOtherOpsTimeReturnType", bound=Series[dt.time] | np.ndarray
)

class _DatetimeOtherOps(Generic[_DTOtherOpsDateReturnType, _DTOtherOpsTimeReturnType]):
    @property
    def date(self) -> _DTOtherOpsDateReturnType: ...
    @property
    def time(self) -> _DTOtherOpsTimeReturnType: ...
    @property
    def timetz(self) -> _DTOtherOpsTimeReturnType: ...

class DatetimeAndPeriodProperties(_DatetimeFieldOps[Series[int]]): ...
class _DatetimeLikeOps(
    _DatetimeFieldOps[_DTFieldOpsReturnType],
    _DatetimeObjectOps[_DTFreqReturnType],
    _DatetimeBoolOps[_DTBoolOpsReturnType],
    _DatetimeOtherOps[_DTOtherOpsDateReturnType, _DTOtherOpsTimeReturnType],
    Generic[
        _DTFieldOpsReturnType,
        _DTBoolOpsReturnType,
        _DTOtherOpsDateReturnType,
        _DTOtherOpsTimeReturnType,
        _DTFreqReturnType,
    ],
): ...

# Ideally, the rounding methods would return TimestampSeries when `Series.dt.method`
# is invoked, but because of how Series.dt is hooked in and that we may not know the
# type of the series, we don't know which kind of series was ...ed
# in to the dt accessor

_DTTimestampTimedeltaReturnType = TypeVar(
    "_DTTimestampTimedeltaReturnType",
    bound=Series | TimestampSeries | TimedeltaSeries | DatetimeIndex | TimedeltaIndex,
)

class _DatetimeRoundingMethods(Generic[_DTTimestampTimedeltaReturnType]):
    def round(
        self,
        freq: str | BaseOffset | None,
        ambiguous: Literal["raise", "infer", "NaT"] | np_ndarray_bool = ...,
        nonexistent: (
            Literal["shift_forward", "shift_backward", "NaT", "raise"]
            | timedelta
            | Timedelta
        ) = ...,
    ) -> _DTTimestampTimedeltaReturnType: ...
    def floor(
        self,
        freq: str | BaseOffset | None,
        ambiguous: Literal["raise", "infer", "NaT"] | np_ndarray_bool = ...,
        nonexistent: (
            Literal["shift_forward", "shift_backward", "NaT", "raise"]
            | timedelta
            | Timedelta
        ) = ...,
    ) -> _DTTimestampTimedeltaReturnType: ...
    def ceil(
        self,
        freq: str | BaseOffset | None,
        ambiguous: Literal["raise", "infer", "NaT"] | np_ndarray_bool = ...,
        nonexistent: (
            Literal["shift_forward", "shift_backward", "NaT", "raise"]
            | timedelta
            | Timedelta
        ) = ...,
    ) -> _DTTimestampTimedeltaReturnType: ...

_DTNormalizeReturnType = TypeVar(
    "_DTNormalizeReturnType", TimestampSeries, DatetimeIndex
)
_DTStrKindReturnType = TypeVar("_DTStrKindReturnType", bound=Series[str] | Index)
_DTToPeriodReturnType = TypeVar(
    "_DTToPeriodReturnType", bound=PeriodSeries | PeriodIndex
)

class _DatetimeLikeNoTZMethods(
    _DatetimeRoundingMethods[_DTTimestampTimedeltaReturnType],
    Generic[
        _DTTimestampTimedeltaReturnType,
        _DTNormalizeReturnType,
        _DTStrKindReturnType,
        _DTToPeriodReturnType,
    ],
):
    def to_period(
        self, freq: str | BaseOffset | None = ...
    ) -> _DTToPeriodReturnType: ...
    def tz_localize(
        self,
        tz: TimeZones,
        ambiguous: Literal["raise", "infer", "NaT"] | np_ndarray_bool = ...,
        nonexistent: (
            Literal["shift_forward", "shift_backward", "NaT", "raise"]
            | timedelta
            | Timedelta
        ) = ...,
    ) -> _DTNormalizeReturnType: ...
    def tz_convert(self, tz: TimeZones) -> _DTNormalizeReturnType: ...
    def normalize(self) -> _DTNormalizeReturnType: ...
    def strftime(self, date_format: str) -> _DTStrKindReturnType: ...
    def month_name(self, locale: str | None = ...) -> _DTStrKindReturnType: ...
    def day_name(self, locale: str | None = ...) -> _DTStrKindReturnType: ...

class _DatetimeNoTZProperties(
    _DatetimeLikeOps[
        _DTFieldOpsReturnType,
        _DTBoolOpsReturnType,
        _DTOtherOpsDateReturnType,
        _DTOtherOpsTimeReturnType,
        _DTFreqReturnType,
    ],
    _DatetimeLikeNoTZMethods[
        _DTTimestampTimedeltaReturnType,
        _DTNormalizeReturnType,
        _DTStrKindReturnType,
        _DTToPeriodReturnType,
    ],
    Generic[
        _DTFieldOpsReturnType,
        _DTBoolOpsReturnType,
        _DTTimestampTimedeltaReturnType,
        _DTOtherOpsDateReturnType,
        _DTOtherOpsTimeReturnType,
        _DTFreqReturnType,
        _DTNormalizeReturnType,
        _DTStrKindReturnType,
        _DTToPeriodReturnType,
    ],
): ...

class DatetimeProperties(
    Properties,
    _DatetimeNoTZProperties[
        _DTFieldOpsReturnType,
        _DTBoolOpsReturnType,
        _DTTimestampTimedeltaReturnType,
        _DTOtherOpsDateReturnType,
        _DTOtherOpsTimeReturnType,
        _DTFreqReturnType,
        _DTNormalizeReturnType,
        _DTStrKindReturnType,
        _DTToPeriodReturnType,
    ],
    Generic[
        _DTFieldOpsReturnType,
        _DTBoolOpsReturnType,
        _DTTimestampTimedeltaReturnType,
        _DTOtherOpsDateReturnType,
        _DTOtherOpsTimeReturnType,
        _DTFreqReturnType,
        _DTNormalizeReturnType,
        _DTStrKindReturnType,
        _DTToPeriodReturnType,
    ],
):
    def to_pydatetime(self) -> np.ndarray: ...
    def isocalendar(self) -> DataFrame: ...
    @property
    def unit(self) -> TimeUnit: ...
    def as_unit(self, unit: TimeUnit) -> _DTTimestampTimedeltaReturnType: ...

_TDNoRoundingMethodReturnType = TypeVar(
    "_TDNoRoundingMethodReturnType", bound=Series[int] | Index
)
_TDTotalSecondsReturnType = TypeVar(
    "_TDTotalSecondsReturnType", bound=Series[float] | Index
)

class _TimedeltaPropertiesNoRounding(
    Generic[_TDNoRoundingMethodReturnType, _TDTotalSecondsReturnType]
):
    def to_pytimedelta(self) -> np.ndarray: ...
    @property
    def components(self) -> DataFrame: ...
    @property
    def days(self) -> _TDNoRoundingMethodReturnType: ...
    @property
    def seconds(self) -> _TDNoRoundingMethodReturnType: ...
    @property
    def microseconds(self) -> _TDNoRoundingMethodReturnType: ...
    @property
    def nanoseconds(self) -> _TDNoRoundingMethodReturnType: ...
    def total_seconds(self) -> _TDTotalSecondsReturnType: ...

class TimedeltaProperties(
    Properties,
    _TimedeltaPropertiesNoRounding[Series[int], Series[float]],
    _DatetimeRoundingMethods[TimedeltaSeries],
):
    @property
    def unit(self) -> TimeUnit: ...
    def as_unit(self, unit: TimeUnit) -> TimedeltaSeries: ...

_PeriodDTReturnTypes = TypeVar(
    "_PeriodDTReturnTypes", bound=TimestampSeries | DatetimeIndex
)
_PeriodIntReturnTypes = TypeVar("_PeriodIntReturnTypes", bound=Series[int] | Index[int])
_PeriodStrReturnTypes = TypeVar("_PeriodStrReturnTypes", bound=Series[str] | Index)
_PeriodDTAReturnTypes = TypeVar(
    "_PeriodDTAReturnTypes", bound=DatetimeArray | DatetimeIndex
)
_PeriodPAReturnTypes = TypeVar("_PeriodPAReturnTypes", bound=PeriodArray | PeriodIndex)

class _PeriodProperties(
    Generic[
        _PeriodDTReturnTypes,
        _PeriodIntReturnTypes,
        _PeriodStrReturnTypes,
        _PeriodDTAReturnTypes,
        _PeriodPAReturnTypes,
    ]
):
    @property
    def start_time(self) -> _PeriodDTReturnTypes: ...
    @property
    def end_time(self) -> _PeriodDTReturnTypes: ...
    @property
    def qyear(self) -> _PeriodIntReturnTypes: ...
    def strftime(self, date_format: str) -> _PeriodStrReturnTypes: ...
    def to_timestamp(
        self,
        freq: str | DateOffset | None = ...,
        how: TimestampConvention = ...,
    ) -> _PeriodDTAReturnTypes: ...
    def asfreq(
        self,
        freq: str | DateOffset | None = ...,
        how: Literal["E", "END", "FINISH", "S", "START", "BEGIN"] = ...,
    ) -> _PeriodPAReturnTypes: ...

class PeriodIndexFieldOps(
    _DayLikeFieldOps[Index[int]],
    _PeriodProperties[DatetimeIndex, Index[int], Index, DatetimeIndex, PeriodIndex],
): ...
class PeriodProperties(
    Properties,
    _PeriodProperties[
        TimestampSeries, Series[int], Series[str], DatetimeArray, PeriodArray
    ],
    _DatetimeFieldOps[Series[int]],
    _IsLeapYearProperty,
    _FreqProperty[BaseOffset],
): ...
class CombinedDatetimelikeProperties(
    DatetimeProperties[
        Series[int],
        Series[bool],
        Series,
        Series[dt.date],
        Series[dt.time],
        str,
        TimestampSeries,
        Series[str],
        PeriodSeries,
    ],
    _TimedeltaPropertiesNoRounding[Series[int], Series[float]],
    _PeriodProperties,
): ...
class TimestampProperties(
    DatetimeProperties[
        Series[int],
        Series[bool],
        TimestampSeries,
        Series[dt.date],
        Series[dt.time],
        str,
        TimestampSeries,
        Series[str],
        PeriodSeries,
    ]
): ...

class DatetimeIndexProperties(
    Properties,
    _DatetimeNoTZProperties[
        Index[int],
        np_ndarray_bool,
        DatetimeIndex,
        np.ndarray,
        np.ndarray,
        BaseOffset,
        DatetimeIndex,
        Index,
        PeriodIndex,
    ],
    _TZProperty,
):
    @property
    def is_normalized(self) -> bool: ...
    @property
    def tzinfo(self) -> tzinfo | None: ...
    def to_pydatetime(self) -> npt.NDArray[np.object_]: ...
    def std(
        self, axis: int | None = ..., ddof: int = ..., skipna: bool = ...
    ) -> Timedelta: ...

class TimedeltaIndexProperties(
    Properties,
    _TimedeltaPropertiesNoRounding[Index, Index],
    _DatetimeRoundingMethods[TimedeltaIndex],
): ...
