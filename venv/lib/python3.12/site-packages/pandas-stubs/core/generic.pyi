from collections.abc import (
    Callable,
    Hashable,
    Iterable,
    Mapping,
    Sequence,
)
import datetime as dt
import sqlite3
from typing import (
    Any,
    ClassVar,
    Literal,
    final,
    overload,
)

import numpy as np
from pandas import Index
import pandas.core.indexing as indexing
from pandas.core.resample import DatetimeIndexResampler
from pandas.core.series import Series
import sqlalchemy.engine
from typing_extensions import (
    Concatenate,
    Self,
)

from pandas._libs.lib import NoDefault
from pandas._typing import (
    S1,
    Axis,
    CompressionOptions,
    CSVQuoting,
    DtypeArg,
    DtypeBackend,
    FilePath,
    FileWriteMode,
    Frequency,
    HashableT1,
    HashableT2,
    HDFCompLib,
    IgnoreRaise,
    IndexLabel,
    Level,
    P,
    StorageOptions,
    T,
    TimedeltaConvertibleTypes,
    TimeGrouperOrigin,
    TimestampConvention,
    TimestampConvertibleTypes,
    WriteBuffer,
)

from pandas.io.pytables import HDFStore
from pandas.io.sql import SQLTable

_bool = bool
_str = str

class NDFrame(indexing.IndexingMixin):
    __hash__: ClassVar[None]  # type: ignore[assignment] # pyright: ignore[reportIncompatibleMethodOverride]

    def set_flags(
        self,
        *,
        copy: bool = ...,
        allows_duplicate_labels: bool | None = ...,
    ) -> Self: ...
    @property
    def attrs(self) -> dict[Hashable | None, Any]: ...
    @attrs.setter
    def attrs(self, value: Mapping[Hashable | None, Any]) -> None: ...
    @property
    def shape(self) -> tuple[int, ...]: ...
    @property
    def ndim(self) -> int: ...
    @property
    def size(self) -> int: ...
    def equals(self, other: Series[S1]) -> _bool: ...
    def __neg__(self) -> Self: ...
    def __pos__(self) -> Self: ...
    def __nonzero__(self) -> None: ...
    @final
    def bool(self) -> _bool: ...
    def __abs__(self) -> Self: ...
    def __round__(self, decimals: int = ...) -> Self: ...
    def __contains__(self, key) -> _bool: ...
    @property
    def empty(self) -> _bool: ...
    __array_priority__: int = ...
    def __array__(self, dtype=...) -> np.ndarray: ...
    def to_excel(
        self,
        excel_writer,
        sheet_name: _str = ...,
        na_rep: _str = ...,
        float_format: _str | None = ...,
        columns: _str | Sequence[_str] | None = ...,
        header: _bool | list[_str] = ...,
        index: _bool = ...,
        index_label: _str | Sequence[_str] | None = ...,
        startrow: int = ...,
        startcol: int = ...,
        engine: _str | None = ...,
        merge_cells: _bool = ...,
        inf_rep: _str = ...,
        freeze_panes: tuple[int, int] | None = ...,
    ) -> None: ...
    def to_hdf(
        self,
        path_or_buf: FilePath | HDFStore,
        *,
        key: _str,
        mode: Literal["a", "w", "r+"] = ...,
        complevel: int | None = ...,
        complib: HDFCompLib | None = ...,
        append: _bool = ...,
        format: Literal["t", "table", "f", "fixed"] | None = ...,
        index: _bool = ...,
        min_itemsize: int | dict[HashableT1, int] | None = ...,
        nan_rep: _str | None = ...,
        dropna: _bool | None = ...,
        data_columns: Literal[True] | list[HashableT2] | None = ...,
        errors: Literal[
            "strict",
            "ignore",
            "replace",
            "surrogateescape",
            "xmlcharrefreplace",
            "backslashreplace",
            "namereplace",
        ] = ...,
        encoding: _str = ...,
    ) -> None: ...
    @overload
    def to_markdown(
        self,
        buf: FilePath | WriteBuffer[str],
        mode: FileWriteMode | None = ...,
        index: _bool = ...,
        storage_options: StorageOptions = ...,
        **kwargs: Any,
    ) -> None: ...
    @overload
    def to_markdown(
        self,
        buf: None = ...,
        mode: FileWriteMode | None = ...,
        index: _bool = ...,
        storage_options: StorageOptions = ...,
        **kwargs: Any,
    ) -> _str: ...
    def to_sql(
        self,
        name: _str,
        con: str | sqlalchemy.engine.Connectable | sqlite3.Connection,
        schema: _str | None = ...,
        if_exists: Literal["fail", "replace", "append"] = ...,
        index: _bool = ...,
        index_label: IndexLabel = ...,
        chunksize: int | None = ...,
        dtype: DtypeArg | None = ...,
        method: (
            Literal["multi"]
            | Callable[
                [SQLTable, Any, list[str], Iterable[tuple[Any, ...]]],
                int | None,
            ]
            | None
        ) = ...,
    ) -> int | None: ...
    def to_pickle(
        self,
        path: FilePath | WriteBuffer[bytes],
        compression: CompressionOptions = ...,
        protocol: int = ...,
        storage_options: StorageOptions = ...,
    ) -> None: ...
    def to_clipboard(
        self, excel: _bool = ..., sep: _str | None = ..., **kwargs
    ) -> None: ...
    @overload
    def to_latex(
        self,
        buf: FilePath | WriteBuffer[str],
        columns: list[_str] | None = ...,
        header: _bool | list[_str] = ...,
        index: _bool = ...,
        na_rep: _str = ...,
        formatters=...,
        float_format=...,
        sparsify: _bool | None = ...,
        index_names: _bool = ...,
        bold_rows: _bool = ...,
        column_format: _str | None = ...,
        longtable: _bool | None = ...,
        escape: _bool | None = ...,
        encoding: _str | None = ...,
        decimal: _str = ...,
        multicolumn: _bool | None = ...,
        multicolumn_format: _str | None = ...,
        multirow: _bool | None = ...,
        caption: _str | tuple[_str, _str] | None = ...,
        label: _str | None = ...,
        position: _str | None = ...,
    ) -> None: ...
    @overload
    def to_latex(
        self,
        buf: None = ...,
        columns: list[_str] | None = ...,
        header: _bool | list[_str] = ...,
        index: _bool = ...,
        na_rep: _str = ...,
        formatters=...,
        float_format=...,
        sparsify: _bool | None = ...,
        index_names: _bool = ...,
        bold_rows: _bool = ...,
        column_format: _str | None = ...,
        longtable: _bool | None = ...,
        escape: _bool | None = ...,
        encoding: _str | None = ...,
        decimal: _str = ...,
        multicolumn: _bool | None = ...,
        multicolumn_format: _str | None = ...,
        multirow: _bool | None = ...,
        caption: _str | tuple[_str, _str] | None = ...,
        label: _str | None = ...,
        position: _str | None = ...,
    ) -> _str: ...
    @overload
    def to_csv(
        self,
        path_or_buf: FilePath | WriteBuffer[bytes] | WriteBuffer[str],
        sep: _str = ...,
        na_rep: _str = ...,
        float_format: _str | Callable[[object], _str] | None = ...,
        columns: list[HashableT1] | None = ...,
        header: _bool | list[_str] = ...,
        index: _bool = ...,
        index_label: Literal[False] | _str | list[HashableT2] | None = ...,
        mode: FileWriteMode = ...,
        encoding: _str | None = ...,
        compression: CompressionOptions = ...,
        quoting: CSVQuoting = ...,
        quotechar: _str = ...,
        lineterminator: _str | None = ...,
        chunksize: int | None = ...,
        date_format: _str | None = ...,
        doublequote: _bool = ...,
        escapechar: _str | None = ...,
        decimal: _str = ...,
        errors: _str = ...,
        storage_options: StorageOptions = ...,
    ) -> None: ...
    @overload
    def to_csv(
        self,
        path_or_buf: None = ...,
        sep: _str = ...,
        na_rep: _str = ...,
        float_format: _str | Callable[[object], _str] | None = ...,
        columns: list[HashableT1] | None = ...,
        header: _bool | list[_str] = ...,
        index: _bool = ...,
        index_label: Literal[False] | _str | list[HashableT2] | None = ...,
        mode: FileWriteMode = ...,
        encoding: _str | None = ...,
        compression: CompressionOptions = ...,
        quoting: CSVQuoting = ...,
        quotechar: _str = ...,
        lineterminator: _str | None = ...,
        chunksize: int | None = ...,
        date_format: _str | None = ...,
        doublequote: _bool = ...,
        escapechar: _str | None = ...,
        decimal: _str = ...,
        errors: _str = ...,
        storage_options: StorageOptions = ...,
    ) -> _str: ...
    def __delitem__(self, idx: Hashable) -> None: ...
    @overload
    def drop(
        self,
        labels: None = ...,
        *,
        axis: Axis = ...,
        index: Hashable | Sequence[Hashable] | Index[Any] = ...,
        columns: Hashable | Iterable[Hashable],
        level: Level | None = ...,
        inplace: Literal[True],
        errors: IgnoreRaise = ...,
    ) -> None: ...
    @overload
    def drop(
        self,
        labels: None = ...,
        *,
        axis: Axis = ...,
        index: Hashable | Sequence[Hashable] | Index[Any],
        columns: Hashable | Iterable[Hashable] = ...,
        level: Level | None = ...,
        inplace: Literal[True],
        errors: IgnoreRaise = ...,
    ) -> None: ...
    @overload
    def drop(
        self,
        labels: Hashable | Sequence[Hashable] | Index[Any],
        *,
        axis: Axis = ...,
        index: None = ...,
        columns: None = ...,
        level: Level | None = ...,
        inplace: Literal[True],
        errors: IgnoreRaise = ...,
    ) -> None: ...
    @overload
    def drop(
        self,
        labels: None = ...,
        *,
        axis: Axis = ...,
        index: Hashable | Sequence[Hashable] | Index[Any] = ...,
        columns: Hashable | Iterable[Hashable],
        level: Level | None = ...,
        inplace: Literal[False] = ...,
        errors: IgnoreRaise = ...,
    ) -> Self: ...
    @overload
    def drop(
        self,
        labels: None = ...,
        *,
        axis: Axis = ...,
        index: Hashable | Sequence[Hashable] | Index[Any],
        columns: Hashable | Iterable[Hashable] = ...,
        level: Level | None = ...,
        inplace: Literal[False] = ...,
        errors: IgnoreRaise = ...,
    ) -> Self: ...
    @overload
    def drop(
        self,
        labels: Hashable | Sequence[Hashable] | Index[Any],
        *,
        axis: Axis = ...,
        index: None = ...,
        columns: None = ...,
        level: Level | None = ...,
        inplace: Literal[False] = ...,
        errors: IgnoreRaise = ...,
    ) -> Self: ...
    @overload
    def pipe(
        self,
        func: Callable[Concatenate[Self, P], T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T: ...
    @overload
    def pipe(
        self,
        func: tuple[Callable[..., T], str],
        *args: Any,
        **kwargs: Any,
    ) -> T: ...
    def __finalize__(self, other, method=..., **kwargs) -> Self: ...
    def __setattr__(self, name: _str, value) -> None: ...
    def __copy__(self, deep: _bool = ...) -> Self: ...
    def __deepcopy__(self, memo=...) -> Self: ...
    def convert_dtypes(
        self,
        infer_objects: _bool = ...,
        convert_string: _bool = ...,
        convert_integer: _bool = ...,
        convert_boolean: _bool = ...,
        convert_floating: _bool = ...,
        dtype_backend: DtypeBackend = ...,
    ) -> Self: ...
    @final
    def resample(
        self,
        rule: Frequency | dt.timedelta,
        axis: Axis | NoDefault = ...,
        closed: Literal["right", "left"] | None = ...,
        label: Literal["right", "left"] | None = ...,
        convention: TimestampConvention = ...,
        kind: Literal["period", "timestamp"] | None = ...,
        on: Level | None = ...,
        level: Level | None = ...,
        origin: TimeGrouperOrigin | TimestampConvertibleTypes = ...,
        offset: TimedeltaConvertibleTypes | None = ...,
        group_keys: _bool = ...,
    ) -> DatetimeIndexResampler[Self]: ...
