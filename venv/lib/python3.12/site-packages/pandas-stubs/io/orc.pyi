from typing import Any

from pandas import DataFrame

from pandas._libs.lib import NoDefault
from pandas._typing import (
    DtypeBackend,
    FilePath,
    HashableT,
    ReadBuffer,
)

def read_orc(
    path: FilePath | ReadBuffer[bytes],
    columns: list[HashableT] | None = ...,
    dtype_backend: DtypeBackend | NoDefault = ...,
    **kwargs: Any,
) -> DataFrame: ...
