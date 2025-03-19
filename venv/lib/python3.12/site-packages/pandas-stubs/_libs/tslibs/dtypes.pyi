from enum import Enum
from typing import cast

from .offsets import BaseOffset

class PeriodDtypeBase:
    def __init__(self, code: int) -> None: ...
    def __eq__(self, other) -> bool: ...
    @property
    def date_offset(self) -> BaseOffset: ...
    @classmethod
    def from_date_offset(cls, offset: BaseOffset) -> PeriodDtypeBase: ...

class FreqGroup:
    FR_ANN: int
    FR_QTR: int
    FR_MTH: int
    FR_WK: int
    FR_BUS: int
    FR_DAY: int
    FR_HR: int
    FR_MIN: int
    FR_SEC: int
    FR_MS: int
    FR_US: int
    FR_NS: int
    FR_UND: int

    @staticmethod
    def get_freq_group(code: int) -> int: ...

class Resolution(Enum):
    RESO_NS = cast(int, ...)
    RESO_US = cast(int, ...)
    RESO_MS = cast(int, ...)
    RESO_SEC = cast(int, ...)
    RESO_MIN = cast(int, ...)
    RESO_HR = cast(int, ...)
    RESO_DAY = cast(int, ...)
    RESO_MTH = cast(int, ...)
    RESO_QTR = cast(int, ...)
    RESO_YR = cast(int, ...)

    def __lt__(self, other) -> bool: ...
    def __ge__(self, other) -> bool: ...
    @property
    def freq_group(self) -> int: ...
    @property
    def attrname(self) -> str: ...
    @classmethod
    def from_attrname(cls, attrname: str) -> Resolution: ...
    @classmethod
    def get_reso_from_freq(cls, freq: str) -> Resolution: ...
