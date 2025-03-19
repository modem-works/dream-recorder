from collections.abc import (
    Callable,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
import datetime as dt
import sys
from typing import (
    Any,
    ClassVar,
    Generic,
    Literal,
    NoReturn,
    overload,
)

from _typing import TimeZones
from matplotlib.axes import Axes as PlotAxes
import numpy as np
from pandas import (
    Period,
    Timedelta,
    Timestamp,
)
from pandas.core.arraylike import OpsMixin
from pandas.core.generic import NDFrame
from pandas.core.groupby.generic import DataFrameGroupBy
from pandas.core.groupby.grouper import Grouper
from pandas.core.indexers import BaseIndexer
from pandas.core.indexes.base import Index
from pandas.core.indexes.category import CategoricalIndex
from pandas.core.indexes.datetimes import DatetimeIndex
from pandas.core.indexes.interval import IntervalIndex
from pandas.core.indexes.multi import MultiIndex
from pandas.core.indexes.period import PeriodIndex
from pandas.core.indexes.timedeltas import TimedeltaIndex
from pandas.core.indexing import (
    _iLocIndexer,
    _IndexSliceTuple,
    _LocIndexer,
)
from pandas.core.interchange.dataframe_protocol import DataFrame as DataFrameXchg
from pandas.core.series import Series
from pandas.core.window import (
    Expanding,
    ExponentialMovingWindow,
)
from pandas.core.window.rolling import (
    Rolling,
    Window,
)
from typing_extensions import (
    Never,
    Self,
    TypeAlias,
)
import xarray as xr

from pandas._libs.lib import NoDefault
from pandas._libs.missing import NAType
from pandas._libs.tslibs import BaseOffset
from pandas._libs.tslibs.nattype import NaTType
from pandas._typing import (
    S1,
    AggFuncTypeBase,
    AggFuncTypeDictFrame,
    AggFuncTypeDictSeries,
    AggFuncTypeFrame,
    AnyArrayLike,
    ArrayLike,
    AstypeArg,
    Axes,
    Axis,
    AxisColumn,
    AxisIndex,
    CalculationMethod,
    ColspaceArgType,
    CompressionOptions,
    Dtype,
    FilePath,
    FillnaOptions,
    FormattersType,
    Frequency,
    GroupByObjectNonScalar,
    HashableT,
    HashableT1,
    HashableT2,
    IgnoreRaise,
    IndexingInt,
    IndexLabel,
    IndexType,
    InterpolateOptions,
    IntervalClosedType,
    IntervalT,
    JoinHow,
    JsonFrameOrient,
    Label,
    Level,
    ListLike,
    ListLikeExceptSeriesAndStr,
    ListLikeU,
    MaskType,
    MergeHow,
    NaPosition,
    NDFrameT,
    ParquetEngine,
    QuantileInterpolation,
    RandomState,
    ReadBuffer,
    Renamer,
    ReplaceValue,
    Scalar,
    ScalarT,
    SequenceNotStr,
    SeriesByT,
    SortKind,
    StataDateFormat,
    StorageOptions,
    StrDtypeArg,
    StrLike,
    Suffixes,
    T as _T,
    TimestampConvention,
    TimeUnit,
    ValidationOptions,
    WriteBuffer,
    XMLParsers,
    npt,
    num,
)

from pandas.io.formats.style import Styler
from pandas.plotting import PlotAccessor

_str = str
_bool = bool

class _iLocIndexerFrame(_iLocIndexer, Generic[_T]):
    @overload
    def __getitem__(self, idx: tuple[int, int]) -> Scalar: ...
    @overload
    def __getitem__(self, idx: IndexingInt) -> Series: ...
    @overload
    def __getitem__(self, idx: tuple[IndexType | MaskType, int]) -> Series: ...
    @overload
    def __getitem__(self, idx: tuple[int, IndexType | MaskType]) -> Series: ...
    @overload
    def __getitem__(
        self,
        idx: (
            IndexType
            | MaskType
            | tuple[IndexType | MaskType, IndexType | MaskType]
            | tuple[slice]
        ),
    ) -> _T: ...
    def __setitem__(
        self,
        idx: (
            int
            | IndexType
            | tuple[int, int]
            | tuple[IndexType, int]
            | tuple[IndexType, IndexType]
            | tuple[int, IndexType]
        ),
        value: Scalar | Series | DataFrame | np.ndarray | NAType | NaTType | None,
    ) -> None: ...

class _LocIndexerFrame(_LocIndexer, Generic[_T]):
    @overload
    def __getitem__(self, idx: Scalar) -> Series | _T: ...
    @overload
    def __getitem__(  # type: ignore[overload-overlap]
        self,
        idx: (
            IndexType
            | MaskType
            | Callable[[DataFrame], IndexType | MaskType | Sequence[Hashable]]
            | list[Hashable]
            | tuple[
                IndexType
                | MaskType
                | list[HashableT]
                | slice
                | _IndexSliceTuple
                | Callable,
                MaskType | list[HashableT] | slice | Callable,
            ]
        ),
    ) -> _T: ...
    @overload
    def __getitem__(  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
        self,
        idx: tuple[
            int
            | StrLike
            | Timestamp
            | tuple[Scalar, ...]
            | Callable[[DataFrame], ScalarT],
            int | StrLike | tuple[Scalar, ...],
        ],
    ) -> Scalar: ...
    @overload
    def __getitem__(
        self,
        idx: (
            Callable[[DataFrame], ScalarT]
            | tuple[
                IndexType
                | MaskType
                | _IndexSliceTuple
                | SequenceNotStr[float | str | Timestamp]
                | Callable[
                    [DataFrame], ScalarT | list[HashableT] | IndexType | MaskType
                ],
                ScalarT | None,
            ]
            | None
        ),
    ) -> Series: ...
    @overload
    def __getitem__(self, idx: tuple[Scalar, slice]) -> Series | _T: ...
    @overload
    def __setitem__(
        self,
        idx: (
            MaskType | StrLike | _IndexSliceTuple | list[ScalarT] | IndexingInt | slice
        ),
        value: Scalar | NAType | NaTType | ArrayLike | Series | DataFrame | list | None,
    ) -> None: ...
    @overload
    def __setitem__(
        self,
        idx: tuple[_IndexSliceTuple, Hashable],
        value: Scalar | NAType | NaTType | ArrayLike | Series | list | None,
    ) -> None: ...

# With mypy 1.14.1 and python 3.12, the second overload needs a type-ignore statement
if sys.version_info >= (3, 12):
    class _GetItemHack:
        @overload
        def __getitem__(self, key: Scalar | tuple[Hashable, ...]) -> Series: ...  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
        @overload
        def __getitem__(  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
            self, key: Iterable[Hashable] | slice
        ) -> Self: ...
        @overload
        def __getitem__(self, key: Hashable) -> Series: ...

else:
    class _GetItemHack:
        @overload
        def __getitem__(self, key: Scalar | tuple[Hashable, ...]) -> Series: ...  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload]
        @overload
        def __getitem__(  # pyright: ignore[reportOverlappingOverload]
            self, key: Iterable[Hashable] | slice
        ) -> Self: ...
        @overload
        def __getitem__(self, key: Hashable) -> Series: ...

class DataFrame(NDFrame, OpsMixin, _GetItemHack):

    __hash__: ClassVar[None]  # type: ignore[assignment] # pyright: ignore[reportIncompatibleMethodOverride]

    @overload
    def __new__(
        cls,
        data: (
            ListLikeU
            | DataFrame
            | dict[Any, Any]
            | Iterable[ListLikeU | tuple[Hashable, ListLikeU] | dict[Any, Any]]
            | None
        ) = ...,
        index: Axes | None = ...,
        columns: Axes | None = ...,
        dtype=...,
        copy: _bool = ...,
    ) -> Self: ...
    @overload
    def __new__(
        cls,
        data: Scalar,
        index: Axes,
        columns: Axes,
        dtype=...,
        copy: _bool = ...,
    ) -> Self: ...
    def __dataframe__(
        self, nan_as_null: bool = ..., allow_copy: bool = ...
    ) -> DataFrameXchg: ...
    def __arrow_c_stream__(self, requested_schema: object | None = None) -> object: ...
    @property
    def axes(self) -> list[Index]: ...
    @property
    def shape(self) -> tuple[int, int]: ...
    @property
    def style(self) -> Styler: ...
    def items(self) -> Iterable[tuple[Hashable, Series]]: ...
    def iterrows(self) -> Iterable[tuple[Hashable, Series]]: ...
    @overload
    def itertuples(
        self, index: _bool = ..., name: _str = ...
    ) -> Iterable[_PandasNamedTuple]: ...
    @overload
    def itertuples(
        self, index: _bool = ..., name: None = None
    ) -> Iterable[tuple[Any, ...]]: ...
    def __len__(self) -> int: ...
    @overload
    def dot(self, other: DataFrame | ArrayLike) -> Self: ...
    @overload
    def dot(self, other: Series) -> Series: ...
    @overload
    def __matmul__(self, other: DataFrame) -> Self: ...
    @overload
    def __matmul__(self, other: Series) -> Series: ...
    @overload
    def __matmul__(self, other: np.ndarray) -> Self: ...
    def __rmatmul__(self, other): ...
    @overload
    @classmethod
    def from_dict(
        cls,
        data: dict[Any, Any],
        orient: Literal["index"],
        dtype: AstypeArg | None = ...,
        columns: Axes | None = ...,
    ) -> Self: ...
    @overload
    @classmethod
    def from_dict(
        cls,
        data: dict[Any, Any],
        orient: Literal["columns", "tight"] = ...,
        dtype: AstypeArg | None = ...,
    ) -> Self: ...
    def to_numpy(
        self,
        dtype: npt.DTypeLike | None = ...,
        copy: bool = ...,
        na_value: Scalar = ...,
    ) -> np.ndarray: ...
    @overload
    def to_dict(
        self,
        orient: Literal["records"],
        *,
        into: MutableMapping | type[MutableMapping],
        index: Literal[True] = ...,
    ) -> list[MutableMapping[Hashable, Any]]: ...
    @overload
    def to_dict(
        self,
        orient: Literal["records"],
        *,
        into: type[dict] = ...,
        index: Literal[True] = ...,
    ) -> list[dict[Hashable, Any]]: ...
    @overload
    def to_dict(
        self,
        orient: Literal["dict", "list", "series", "index"],
        *,
        into: MutableMapping | type[MutableMapping],
        index: Literal[True] = ...,
    ) -> MutableMapping[Hashable, Any]: ...
    @overload
    def to_dict(
        self,
        orient: Literal["split", "tight"],
        *,
        into: MutableMapping | type[MutableMapping],
        index: bool = ...,
    ) -> MutableMapping[Hashable, Any]: ...
    @overload
    def to_dict(
        self,
        orient: Literal["dict", "list", "series", "index"] = ...,
        *,
        into: MutableMapping | type[MutableMapping],
        index: Literal[True] = ...,
    ) -> MutableMapping[Hashable, Any]: ...
    @overload
    def to_dict(
        self,
        orient: Literal["split", "tight"] = ...,
        *,
        into: MutableMapping | type[MutableMapping],
        index: bool = ...,
    ) -> MutableMapping[Hashable, Any]: ...
    @overload
    def to_dict(
        self,
        orient: Literal["dict", "list", "series", "index"] = ...,
        *,
        into: type[dict] = ...,
        index: Literal[True] = ...,
    ) -> dict[Hashable, Any]: ...
    @overload
    def to_dict(
        self,
        orient: Literal["split", "tight"] = ...,
        *,
        into: type[dict] = ...,
        index: bool = ...,
    ) -> dict[Hashable, Any]: ...
    def to_gbq(
        self,
        destination_table: str,
        project_id: str | None = ...,
        chunksize: int | None = ...,
        reauth: bool = ...,
        if_exists: Literal["fail", "replace", "append"] = ...,
        auth_local_webserver: bool = ...,
        table_schema: list[dict[str, str]] | None = ...,
        location: str | None = ...,
        progress_bar: bool = ...,
        # Google type, not available
        credentials: Any = ...,
    ) -> None: ...
    @classmethod
    def from_records(
        cls, data, index=..., exclude=..., columns=..., coerce_float=..., nrows=...
    ) -> Self: ...
    def to_records(
        self,
        index: _bool = ...,
        column_dtypes: (
            _str | npt.DTypeLike | Mapping[HashableT1, npt.DTypeLike] | None
        ) = ...,
        index_dtypes: (
            _str | npt.DTypeLike | Mapping[HashableT2, npt.DTypeLike] | None
        ) = ...,
    ) -> np.recarray: ...
    @overload
    def to_stata(
        self,
        path: FilePath | WriteBuffer[bytes],
        *,
        convert_dates: dict[HashableT1, StataDateFormat] | None = ...,
        write_index: _bool = ...,
        byteorder: Literal["<", ">", "little", "big"] | None = ...,
        time_stamp: dt.datetime | None = ...,
        data_label: _str | None = ...,
        variable_labels: dict[HashableT2, str] | None = ...,
        version: Literal[117, 118, 119],
        convert_strl: SequenceNotStr[Hashable] | None = ...,
        compression: CompressionOptions = ...,
        storage_options: StorageOptions = ...,
        value_labels: dict[Hashable, dict[float, str]] | None = ...,
    ) -> None: ...
    @overload
    def to_stata(
        self,
        path: FilePath | WriteBuffer[bytes],
        *,
        convert_dates: dict[HashableT1, StataDateFormat] | None = ...,
        write_index: _bool = ...,
        byteorder: Literal["<", ">", "little", "big"] | None = ...,
        time_stamp: dt.datetime | None = ...,
        data_label: _str | None = ...,
        variable_labels: dict[HashableT2, str] | None = ...,
        version: Literal[114, 117, 118, 119] | None = ...,
        convert_strl: None = ...,
        compression: CompressionOptions = ...,
        storage_options: StorageOptions = ...,
        value_labels: dict[Hashable, dict[float, str]] | None = ...,
    ) -> None: ...
    def to_feather(self, path: FilePath | WriteBuffer[bytes], **kwargs) -> None: ...
    @overload
    def to_parquet(
        self,
        path: FilePath | WriteBuffer[bytes],
        engine: ParquetEngine = ...,
        compression: Literal["snappy", "gzip", "brotli", "lz4", "zstd"] | None = ...,
        index: bool | None = ...,
        partition_cols: Sequence[Hashable] | None = ...,
        storage_options: StorageOptions = ...,
        **kwargs: Any,
    ) -> None: ...
    @overload
    def to_parquet(
        self,
        path: None = ...,
        engine: ParquetEngine = ...,
        compression: Literal["snappy", "gzip", "brotli", "lz4", "zstd"] | None = ...,
        index: bool | None = ...,
        partition_cols: Sequence[Hashable] | None = ...,
        storage_options: StorageOptions = ...,
        **kwargs: Any,
    ) -> bytes: ...
    @overload
    def to_orc(
        self,
        path: FilePath | WriteBuffer[bytes],
        *,
        engine: Literal["pyarrow"] = ...,
        index: bool | None = ...,
        engine_kwargs: dict[str, Any] | None = ...,
    ) -> None: ...
    @overload
    def to_orc(
        self,
        path: None = ...,
        *,
        engine: Literal["pyarrow"] = ...,
        index: bool | None = ...,
        engine_kwargs: dict[str, Any] | None = ...,
    ) -> bytes: ...
    @overload
    def to_html(
        self,
        buf: FilePath | WriteBuffer[str],
        columns: SequenceNotStr[Hashable] | Index | Series | None = ...,
        col_space: ColspaceArgType | None = ...,
        header: _bool = ...,
        index: _bool = ...,
        na_rep: _str = ...,
        formatters: (
            list[Callable[[object], str]]
            | tuple[Callable[[object], str], ...]
            | Mapping[Hashable, Callable[[object], str]]
            | None
        ) = ...,
        float_format: Callable[[float], str] | None = ...,
        sparsify: _bool | None = ...,
        index_names: _bool = ...,
        justify: (
            Literal[
                "left",
                "right",
                "center",
                "justify",
                "justify-all",
                "start",
                "end",
                "inherit",
                "match-parent",
                "initial",
                "unset",
            ]
            | None
        ) = ...,
        max_rows: int | None = ...,
        max_cols: int | None = ...,
        show_dimensions: _bool = ...,
        decimal: _str = ...,
        bold_rows: _bool = ...,
        classes: Sequence[str] | None = ...,
        escape: _bool = ...,
        notebook: _bool = ...,
        border: int | None = ...,
        table_id: _str | None = ...,
        render_links: _bool = ...,
        encoding: _str | None = ...,
    ) -> None: ...
    @overload
    def to_html(
        self,
        buf: None = ...,
        columns: Sequence[Hashable] | None = ...,
        col_space: ColspaceArgType | None = ...,
        header: _bool = ...,
        index: _bool = ...,
        na_rep: _str = ...,
        formatters: (
            list[Callable[[object], str]]
            | tuple[Callable[[object], str], ...]
            | Mapping[Hashable, Callable[[object], str]]
            | None
        ) = ...,
        float_format: Callable[[float], str] | None = ...,
        sparsify: _bool | None = ...,
        index_names: _bool = ...,
        justify: (
            Literal[
                "left",
                "right",
                "center",
                "justify",
                "justify-all",
                "start",
                "end",
                "inherit",
                "match-parent",
                "initial",
                "unset",
            ]
            | None
        ) = ...,
        max_rows: int | None = ...,
        max_cols: int | None = ...,
        show_dimensions: _bool = ...,
        decimal: _str = ...,
        bold_rows: _bool = ...,
        classes: Sequence[str] | None = ...,
        escape: _bool = ...,
        notebook: _bool = ...,
        border: int | None = ...,
        table_id: _str | None = ...,
        render_links: _bool = ...,
        encoding: _str | None = ...,
    ) -> _str: ...
    @overload
    def to_xml(
        self,
        path_or_buffer: FilePath | WriteBuffer[bytes] | WriteBuffer[str],
        index: bool = ...,
        root_name: str = ...,
        row_name: str = ...,
        na_rep: str | None = ...,
        attr_cols: SequenceNotStr[Hashable] | None = ...,
        elem_cols: SequenceNotStr[Hashable] | None = ...,
        namespaces: dict[str | None, str] | None = ...,
        prefix: str | None = ...,
        encoding: str = ...,
        xml_declaration: bool = ...,
        pretty_print: bool = ...,
        parser: XMLParsers = ...,
        stylesheet: FilePath | ReadBuffer[str] | ReadBuffer[bytes] | None = ...,
        compression: CompressionOptions = ...,
        storage_options: StorageOptions = ...,
    ) -> None: ...
    @overload
    def to_xml(
        self,
        path_or_buffer: Literal[None] = ...,
        index: bool = ...,
        root_name: str | None = ...,
        row_name: str | None = ...,
        na_rep: str | None = ...,
        attr_cols: list[Hashable] | None = ...,
        elem_cols: list[Hashable] | None = ...,
        namespaces: dict[str | None, str] | None = ...,
        prefix: str | None = ...,
        encoding: str = ...,
        xml_declaration: bool | None = ...,
        pretty_print: bool | None = ...,
        parser: str | None = ...,
        stylesheet: FilePath | ReadBuffer[str] | ReadBuffer[bytes] | None = ...,
        compression: CompressionOptions = ...,
        storage_options: StorageOptions = ...,
    ) -> str: ...
    def info(
        self,
        verbose: bool | None = ...,
        buf: WriteBuffer[str] = ...,
        max_cols: int | None = ...,
        memory_usage: bool | Literal["deep"] | None = ...,
        show_counts: bool | None = ...,
    ) -> None: ...
    def memory_usage(self, index: _bool = ..., deep: _bool = ...) -> Series: ...
    def transpose(self, *args: Any, copy: _bool = ...) -> Self: ...
    @property
    def T(self) -> Self: ...
    def __getattr__(self, name: str) -> Series: ...
    def isetitem(
        self, loc: int | Sequence[int], value: Scalar | ArrayLike | list[Any]
    ) -> None: ...
    def __setitem__(self, key, value) -> None: ...
    @overload
    def query(self, expr: _str, *, inplace: Literal[True], **kwargs) -> None: ...
    @overload
    def query(self, expr: _str, *, inplace: Literal[False] = ..., **kwargs) -> Self: ...
    @overload
    def eval(self, expr: _str, *, inplace: Literal[True], **kwargs) -> None: ...
    @overload
    def eval(
        self, expr: _str, *, inplace: Literal[False] = ..., **kwargs
    ) -> Scalar | np.ndarray | Self | Series: ...
    AstypeArgExt: TypeAlias = (
        AstypeArg
        | Literal[
            "number",
            "datetime64",
            "datetime",
            "integer",
            "timedelta",
            "timedelta64",
            "datetimetz",
            "datetime64[ns]",
        ]
    )
    AstypeArgExtList: TypeAlias = AstypeArgExt | list[AstypeArgExt]
    @overload
    def select_dtypes(
        self, include: StrDtypeArg, exclude: AstypeArgExtList | None = ...
    ) -> Never: ...
    @overload
    def select_dtypes(
        self, include: AstypeArgExtList | None, exclude: StrDtypeArg
    ) -> Never: ...
    @overload
    def select_dtypes(self, exclude: StrDtypeArg) -> Never: ...
    @overload
    def select_dtypes(self, include: list[Never], exclude: list[Never]) -> Never: ...
    @overload
    def select_dtypes(
        self,
        include: AstypeArgExtList,
        exclude: AstypeArgExtList | None = ...,
    ) -> Self: ...
    @overload
    def select_dtypes(
        self,
        include: AstypeArgExtList | None,
        exclude: AstypeArgExtList,
    ) -> Self: ...
    @overload
    def select_dtypes(
        self,
        exclude: AstypeArgExtList,
    ) -> Self: ...
    def insert(
        self,
        loc: int,
        column: Hashable,
        value: Scalar | ListLikeU | None,
        allow_duplicates: _bool = ...,
    ) -> None: ...
    def assign(self, **kwargs) -> Self: ...
    def align(
        self,
        other: NDFrameT,
        join: JoinHow = ...,
        axis: Axis | None = ...,
        level: Level | None = ...,
        copy: _bool = ...,
        fill_value: Scalar | NAType | None = ...,
    ) -> tuple[Self, NDFrameT]: ...
    def reindex(
        self,
        labels: Axes | None = ...,
        index: Axes | None = ...,
        columns: Axes | None = ...,
        axis: Axis | None = ...,
        method: FillnaOptions | Literal["nearest"] | None = ...,
        copy: bool = ...,
        level: int | _str = ...,
        fill_value: Scalar | None = ...,
        limit: int | None = ...,
        tolerance: float | None = ...,
    ) -> Self: ...
    @overload
    def rename(
        self,
        mapper: Renamer | None = ...,
        *,
        index: Renamer | None = ...,
        columns: Renamer | None = ...,
        axis: Axis | None = ...,
        copy: bool = ...,
        inplace: Literal[True],
        level: Level | None = ...,
        errors: IgnoreRaise = ...,
    ) -> None: ...
    @overload
    def rename(
        self,
        mapper: Renamer | None = ...,
        *,
        index: Renamer | None = ...,
        columns: Renamer | None = ...,
        axis: Axis | None = ...,
        copy: bool = ...,
        inplace: Literal[False] = ...,
        level: Level | None = ...,
        errors: IgnoreRaise = ...,
    ) -> Self: ...
    @overload
    def fillna(
        self,
        value: Scalar | NAType | dict | Series | DataFrame | None = ...,
        *,
        axis: Axis | None = ...,
        limit: int = ...,
        inplace: Literal[True],
    ) -> None: ...
    @overload
    def fillna(
        self,
        value: Scalar | NAType | dict | Series | DataFrame | None = ...,
        *,
        axis: Axis | None = ...,
        limit: int = ...,
        inplace: Literal[False] = ...,
    ) -> Self: ...
    @overload
    def replace(
        self,
        to_replace: ReplaceValue | Mapping[Hashable, ReplaceValue] = ...,
        value: ReplaceValue | Mapping[Hashable, ReplaceValue] = ...,
        *,
        inplace: Literal[True],
        regex: ReplaceValue | Mapping[Hashable, ReplaceValue] = ...,
    ) -> None: ...
    @overload
    def replace(
        self,
        to_replace: ReplaceValue | Mapping[Hashable, ReplaceValue] = ...,
        value: ReplaceValue | Mapping[Hashable, ReplaceValue] = ...,
        *,
        inplace: Literal[False] = ...,
        regex: ReplaceValue | Mapping[Hashable, ReplaceValue] = ...,
    ) -> Self: ...
    def shift(
        self,
        periods: int = ...,
        freq: Frequency | dt.timedelta | None = ...,
        axis: Axis = ...,
        fill_value: Hashable | None = ...,
    ) -> Self: ...
    @overload
    def set_index(
        self,
        keys: (
            Label
            | Series
            | Index
            | np.ndarray
            | Iterator[Hashable]
            | Sequence[Hashable]
        ),
        *,
        drop: _bool = ...,
        append: _bool = ...,
        verify_integrity: _bool = ...,
        inplace: Literal[True],
    ) -> None: ...
    @overload
    def set_index(
        self,
        keys: (
            Label
            | Series
            | Index
            | np.ndarray
            | Iterator[Hashable]
            | Sequence[Hashable]
        ),
        *,
        drop: _bool = ...,
        append: _bool = ...,
        verify_integrity: _bool = ...,
        inplace: Literal[False] = ...,
    ) -> Self: ...
    @overload
    def reset_index(
        self,
        level: Level | Sequence[Level] = ...,
        *,
        drop: _bool = ...,
        col_level: int | _str = ...,
        col_fill: Hashable = ...,
        inplace: Literal[True],
        allow_duplicates: _bool = ...,
        names: Hashable | Sequence[Hashable] = ...,
    ) -> None: ...
    @overload
    def reset_index(
        self,
        level: Level | Sequence[Level] = ...,
        *,
        col_level: int | _str = ...,
        col_fill: Hashable = ...,
        drop: _bool = ...,
        inplace: Literal[False] = ...,
        allow_duplicates: _bool = ...,
        names: Hashable | Sequence[Hashable] = ...,
    ) -> Self: ...
    def isna(self) -> Self: ...
    def isnull(self) -> Self: ...
    def notna(self) -> Self: ...
    def notnull(self) -> Self: ...
    @overload
    def dropna(
        self,
        *,
        axis: Axis = ...,
        how: Literal["any", "all"] = ...,
        thresh: int | None = ...,
        subset: ListLikeU | Scalar | None = ...,
        inplace: Literal[True],
        ignore_index: _bool = ...,
    ) -> None: ...
    @overload
    def dropna(
        self,
        *,
        axis: Axis = ...,
        how: Literal["any", "all"] = ...,
        thresh: int | None = ...,
        subset: ListLikeU | Scalar | None = ...,
        inplace: Literal[False] = ...,
        ignore_index: _bool = ...,
    ) -> Self: ...
    @overload
    def drop_duplicates(
        self,
        subset: Hashable | Iterable[Hashable] | None = ...,
        *,
        keep: NaPosition | _bool = ...,
        inplace: Literal[True],
        ignore_index: _bool = ...,
    ) -> None: ...
    @overload
    def drop_duplicates(
        self,
        subset: Hashable | Iterable[Hashable] | None = ...,
        *,
        keep: NaPosition | _bool = ...,
        inplace: Literal[False] = ...,
        ignore_index: _bool = ...,
    ) -> Self: ...
    def duplicated(
        self,
        subset: Hashable | Iterable[Hashable] | None = ...,
        keep: NaPosition | _bool = ...,
    ) -> Series: ...
    @overload
    def sort_values(
        self,
        by: _str | Sequence[_str],
        *,
        axis: Axis = ...,
        ascending: _bool | Sequence[_bool] = ...,
        kind: SortKind = ...,
        na_position: NaPosition = ...,
        ignore_index: _bool = ...,
        inplace: Literal[True],
        key: Callable | None = ...,
    ) -> None: ...
    @overload
    def sort_values(
        self,
        by: _str | Sequence[_str],
        *,
        axis: Axis = ...,
        ascending: _bool | Sequence[_bool] = ...,
        kind: SortKind = ...,
        na_position: NaPosition = ...,
        ignore_index: _bool = ...,
        inplace: Literal[False] = ...,
        key: Callable | None = ...,
    ) -> Self: ...
    @overload
    def sort_index(
        self,
        *,
        axis: Axis = ...,
        level: Level | None = ...,
        ascending: _bool | Sequence[_bool] = ...,
        kind: SortKind = ...,
        na_position: NaPosition = ...,
        sort_remaining: _bool = ...,
        ignore_index: _bool = ...,
        inplace: Literal[True],
        key: Callable | None = ...,
    ) -> None: ...
    @overload
    def sort_index(
        self,
        *,
        axis: Axis = ...,
        level: Level | list[int] | list[_str] | None = ...,
        ascending: _bool | Sequence[_bool] = ...,
        kind: SortKind = ...,
        na_position: NaPosition = ...,
        sort_remaining: _bool = ...,
        ignore_index: _bool = ...,
        inplace: Literal[False] = ...,
        key: Callable | None = ...,
    ) -> Self: ...
    @overload
    def value_counts(
        self,
        subset: Sequence[Hashable] | None = ...,
        normalize: Literal[False] = ...,
        sort: _bool = ...,
        ascending: _bool = ...,
        dropna: _bool = ...,
    ) -> Series[int]: ...
    @overload
    def value_counts(
        self,
        normalize: Literal[True],
        subset: Sequence[Hashable] | None = ...,
        sort: _bool = ...,
        ascending: _bool = ...,
        dropna: _bool = ...,
    ) -> Series[float]: ...
    def nlargest(
        self,
        n: int,
        columns: _str | list[_str],
        keep: NaPosition | Literal["all"] = ...,
    ) -> Self: ...
    def nsmallest(
        self,
        n: int,
        columns: _str | list[_str],
        keep: NaPosition | Literal["all"] = ...,
    ) -> Self: ...
    def swaplevel(self, i: Level = ..., j: Level = ..., axis: Axis = ...) -> Self: ...
    def reorder_levels(self, order: list, axis: Axis = ...) -> Self: ...
    def compare(
        self,
        other: DataFrame,
        align_axis: Axis = ...,
        keep_shape: bool = ...,
        keep_equal: bool = ...,
        result_names: Suffixes = ...,
    ) -> Self: ...
    def combine(
        self,
        other: DataFrame,
        func: Callable,
        fill_value: Scalar | None = ...,
        overwrite: _bool = ...,
    ) -> Self: ...
    def combine_first(self, other: DataFrame) -> Self: ...
    def update(
        self,
        other: DataFrame | Series,
        join: _str = ...,
        overwrite: _bool = ...,
        filter_func: Callable | None = ...,
        errors: IgnoreRaise = ...,
    ) -> None: ...
    @overload
    def groupby(  # pyright: ignore reportOverlappingOverload
        self,
        by: Scalar,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[True] = True,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Scalar, Literal[True]]: ...
    @overload
    def groupby(
        self,
        by: Scalar,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[False] = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Scalar, Literal[False]]: ...
    @overload
    def groupby(  # pyright: ignore reportOverlappingOverload
        self,
        by: DatetimeIndex,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[True] = True,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Timestamp, Literal[True]]: ...
    @overload
    def groupby(  # pyright: ignore reportOverlappingOverload
        self,
        by: DatetimeIndex,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[False] = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Timestamp, Literal[False]]: ...
    @overload
    def groupby(  # pyright: ignore reportOverlappingOverload
        self,
        by: TimedeltaIndex,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[True] = True,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Timedelta, Literal[True]]: ...
    @overload
    def groupby(
        self,
        by: TimedeltaIndex,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[False] = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Timedelta, Literal[False]]: ...
    @overload
    def groupby(  # pyright: ignore reportOverlappingOverload
        self,
        by: PeriodIndex,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[True] = True,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Period, Literal[True]]: ...
    @overload
    def groupby(
        self,
        by: PeriodIndex,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[False] = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Period, Literal[False]]: ...
    @overload
    def groupby(  # pyright: ignore reportOverlappingOverload
        self,
        by: IntervalIndex[IntervalT],
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[True] = True,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[IntervalT, Literal[True]]: ...
    @overload
    def groupby(
        self,
        by: IntervalIndex[IntervalT],
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[False] = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[IntervalT, Literal[False]]: ...
    @overload
    def groupby(  # type: ignore[overload-overlap] # pyright: ignore reportOverlappingOverload
        self,
        by: MultiIndex | GroupByObjectNonScalar | None = ...,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[True] = True,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[tuple, Literal[True]]: ...
    @overload
    def groupby(  # type: ignore[overload-overlap]
        self,
        by: MultiIndex | GroupByObjectNonScalar | None = ...,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[False] = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[tuple, Literal[False]]: ...
    @overload
    def groupby(  # pyright: ignore reportOverlappingOverload
        self,
        by: Series[SeriesByT],
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[True] = True,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[SeriesByT, Literal[True]]: ...
    @overload
    def groupby(
        self,
        by: Series[SeriesByT],
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[False] = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[SeriesByT, Literal[False]]: ...
    @overload
    def groupby(
        self,
        by: CategoricalIndex | Index | Series,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[True] = True,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Any, Literal[True]]: ...
    @overload
    def groupby(
        self,
        by: CategoricalIndex | Index | Series,
        axis: AxisIndex | NoDefault = ...,
        level: IndexLabel | None = ...,
        as_index: Literal[False] = ...,
        sort: _bool = ...,
        group_keys: _bool = ...,
        observed: _bool | NoDefault = ...,
        dropna: _bool = ...,
    ) -> DataFrameGroupBy[Any, Literal[False]]: ...
    def pivot(
        self,
        *,
        index: IndexLabel = ...,
        columns: IndexLabel = ...,
        values: IndexLabel = ...,
    ) -> Self: ...
    def pivot_table(
        self,
        values: _str | None | Sequence[_str] = ...,
        index: _str | Grouper | Sequence | None = ...,
        columns: _str | Grouper | Sequence | None = ...,
        aggfunc=...,
        fill_value: Scalar | None = ...,
        margins: _bool = ...,
        dropna: _bool = ...,
        margins_name: _str = ...,
        observed: _bool = ...,
        sort: _bool = ...,
    ) -> Self: ...
    @overload
    def stack(
        self, level: Level | list[Level] = ..., dropna: _bool = ..., sort: _bool = ...
    ) -> Self | Series[Any]: ...
    @overload
    def stack(
        self, level: Level | list[Level] = ..., future_stack: _bool = ...
    ) -> Self | Series[Any]: ...
    def explode(
        self, column: Sequence[Hashable], ignore_index: _bool = ...
    ) -> Self: ...
    def unstack(
        self,
        level: Level = ...,
        fill_value: int | _str | dict | None = ...,
    ) -> Self | Series: ...
    def melt(
        self,
        id_vars: tuple | Sequence | np.ndarray | None = ...,
        value_vars: tuple | Sequence | np.ndarray | None = ...,
        var_name: Scalar | None = ...,
        value_name: Scalar = ...,
        col_level: int | _str | None = ...,
        ignore_index: _bool = ...,
    ) -> Self: ...
    def diff(self, periods: int = ..., axis: Axis = ...) -> Self: ...
    @overload
    def agg(  # pyright: ignore[reportOverlappingOverload]
        self, func: AggFuncTypeBase | AggFuncTypeDictSeries, axis: Axis = ..., **kwargs
    ) -> Series: ...
    @overload
    def agg(
        self,
        func: list[AggFuncTypeBase] | AggFuncTypeDictFrame = ...,
        axis: Axis = ...,
        **kwargs,
    ) -> Self: ...
    @overload
    def aggregate(  # pyright: ignore[reportOverlappingOverload]
        self, func: AggFuncTypeBase | AggFuncTypeDictSeries, axis: Axis = ..., **kwargs
    ) -> Series: ...
    @overload
    def aggregate(
        self,
        func: list[AggFuncTypeBase] | AggFuncTypeDictFrame,
        axis: Axis = ...,
        **kwargs,
    ) -> Self: ...
    def transform(
        self,
        func: AggFuncTypeFrame,
        axis: Axis = ...,
        *args,
        **kwargs,
    ) -> Self: ...

    # apply() overloads with default result_type of None, and is indifferent to axis
    @overload
    def apply(
        self,
        f: Callable[..., ListLikeExceptSeriesAndStr | Series[Any]],
        axis: AxisIndex = ...,
        raw: _bool = ...,
        result_type: None = ...,
        args: Any = ...,
        **kwargs: Any,
    ) -> Self: ...
    @overload
    def apply(
        self,
        f: Callable[..., S1 | NAType],
        axis: AxisIndex = ...,
        raw: _bool = ...,
        result_type: None = ...,
        args: Any = ...,
        **kwargs: Any,
    ) -> Series[S1]: ...
    # Since non-scalar type T is not supported in Series[T],
    # we separate this overload from the above one
    @overload
    def apply(
        self,
        f: Callable[..., Mapping[Any, Any]],
        axis: AxisIndex = ...,
        raw: _bool = ...,
        result_type: None = ...,
        args: Any = ...,
        **kwargs: Any,
    ) -> Series[Any]: ...

    # apply() overloads with keyword result_type, and axis does not matter
    @overload
    def apply(
        self,
        f: Callable[..., S1 | NAType],
        axis: Axis = ...,
        raw: _bool = ...,
        args: Any = ...,
        *,
        result_type: Literal["expand", "reduce"],
        **kwargs: Any,
    ) -> Series[S1]: ...
    @overload
    def apply(
        self,
        f: Callable[..., ListLikeExceptSeriesAndStr | Series[Any] | Mapping[Any, Any]],
        axis: Axis = ...,
        raw: _bool = ...,
        args: Any = ...,
        *,
        result_type: Literal["expand"],
        **kwargs: Any,
    ) -> Self: ...
    @overload
    def apply(
        self,
        f: Callable[..., ListLikeExceptSeriesAndStr | Mapping[Any, Any]],
        axis: Axis = ...,
        raw: _bool = ...,
        args: Any = ...,
        *,
        result_type: Literal["reduce"],
        **kwargs: Any,
    ) -> Series[Any]: ...
    @overload
    def apply(
        self,
        f: Callable[
            ..., ListLikeExceptSeriesAndStr | Series[Any] | Scalar | Mapping[Any, Any]
        ],
        axis: Axis = ...,
        raw: _bool = ...,
        args: Any = ...,
        *,
        result_type: Literal["broadcast"],
        **kwargs: Any,
    ) -> Self: ...

    # apply() overloads with keyword result_type, and axis does matter
    @overload
    def apply(
        self,
        f: Callable[..., Series[Any]],
        axis: AxisIndex = ...,
        raw: _bool = ...,
        args: Any = ...,
        *,
        result_type: Literal["reduce"],
        **kwargs: Any,
    ) -> Series[Any]: ...

    # apply() overloads with default result_type of None, and keyword axis=1 matters
    @overload
    def apply(
        self,
        f: Callable[..., S1 | NAType],
        raw: _bool = ...,
        result_type: None = ...,
        args: Any = ...,
        *,
        axis: AxisColumn,
        **kwargs: Any,
    ) -> Series[S1]: ...
    @overload
    def apply(
        self,
        f: Callable[..., ListLikeExceptSeriesAndStr | Mapping[Any, Any]],
        raw: _bool = ...,
        result_type: None = ...,
        args: Any = ...,
        *,
        axis: AxisColumn,
        **kwargs: Any,
    ) -> Series[Any]: ...
    @overload
    def apply(
        self,
        f: Callable[..., Series[Any]],
        raw: _bool = ...,
        result_type: None = ...,
        args: Any = ...,
        *,
        axis: AxisColumn,
        **kwargs: Any,
    ) -> Self: ...

    # apply() overloads with keyword axis=1 and keyword result_type
    @overload
    def apply(
        self,
        f: Callable[..., Series[Any]],
        raw: _bool = ...,
        args: Any = ...,
        *,
        axis: AxisColumn,
        result_type: Literal["reduce"],
        **kwargs: Any,
    ) -> Self: ...

    # Add spacing between apply() overloads and remaining annotations
    def map(
        self, func: Callable, na_action: Literal["ignore"] | None = ..., **kwargs
    ) -> Self: ...
    def join(
        self,
        other: DataFrame | Series | list[DataFrame | Series],
        on: _str | list[_str] | None = ...,
        how: MergeHow = ...,
        lsuffix: _str = ...,
        rsuffix: _str = ...,
        sort: _bool = ...,
        validate: ValidationOptions | None = ...,
    ) -> Self: ...
    def merge(
        self,
        right: DataFrame | Series[Any],
        how: MergeHow = ...,
        on: IndexLabel | AnyArrayLike | None = ...,
        left_on: IndexLabel | AnyArrayLike | None = ...,
        right_on: IndexLabel | AnyArrayLike | None = ...,
        left_index: _bool = ...,
        right_index: _bool = ...,
        sort: _bool = ...,
        suffixes: tuple[_str | None, _str | None] = ...,
        copy: _bool = ...,
        indicator: _bool | _str = ...,
        validate: _str | None = ...,
    ) -> Self: ...
    def round(self, decimals: int | dict | Series = ..., *args, **kwargs) -> Self: ...
    def corr(
        self,
        method: Literal["pearson", "kendall", "spearman"] = ...,
        min_periods: int = ...,
        numeric_only: _bool = ...,
    ) -> Self: ...
    def cov(
        self, min_periods: int | None = ..., ddof: int = ..., numeric_only: _bool = ...
    ) -> Self: ...
    def corrwith(
        self,
        other: DataFrame | Series,
        axis: Axis | None = ...,
        drop: _bool = ...,
        method: Literal["pearson", "kendall", "spearman"] = ...,
        numeric_only: _bool = ...,
    ) -> Series: ...
    @overload
    def count(
        self, axis: Axis = ..., numeric_only: _bool = ..., *, level: Level
    ) -> Self: ...
    @overload
    def count(
        self, axis: Axis = ..., level: None = ..., numeric_only: _bool = ...
    ) -> Series: ...
    def nunique(self, axis: Axis = ..., dropna: bool = ...) -> Series: ...
    def idxmax(
        self, axis: Axis = ..., skipna: _bool = ..., numeric_only: _bool = ...
    ) -> Series: ...
    def idxmin(
        self, axis: Axis = ..., skipna: _bool = ..., numeric_only: _bool = ...
    ) -> Series: ...
    @overload
    def mode(
        self,
        axis: Axis = ...,
        skipna: _bool = ...,
        numeric_only: _bool = ...,
        *,
        level: Level,
        **kwargs,
    ) -> Self: ...
    @overload
    def mode(
        self,
        axis: Axis = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    @overload
    def quantile(
        self,
        q: float = ...,
        axis: Axis = ...,
        numeric_only: _bool = ...,
        interpolation: QuantileInterpolation = ...,
        method: CalculationMethod = ...,
    ) -> Series: ...
    @overload
    def quantile(
        self,
        q: list[float] | np.ndarray,
        axis: Axis = ...,
        numeric_only: _bool = ...,
        interpolation: QuantileInterpolation = ...,
        method: CalculationMethod = ...,
    ) -> Self: ...
    def to_timestamp(
        self,
        freq=...,
        how: TimestampConvention = ...,
        axis: Axis = ...,
        copy: _bool = ...,
    ) -> Self: ...
    def to_period(
        self, freq: _str | None = ..., axis: Axis = ..., copy: _bool = ...
    ) -> Self: ...
    def isin(self, values: Iterable | Series | DataFrame | dict) -> Self: ...
    @property
    def plot(self) -> PlotAccessor: ...
    def hist(
        self,
        column: _str | list[_str] | None = ...,
        by: _str | ListLike | None = ...,
        grid: _bool = ...,
        xlabelsize: float | str | None = ...,
        xrot: float | None = ...,
        ylabelsize: float | str | None = ...,
        yrot: float | None = ...,
        ax: PlotAxes | None = ...,
        sharex: _bool = ...,
        sharey: _bool = ...,
        figsize: tuple[float, float] | None = ...,
        layout: tuple[int, int] | None = ...,
        bins: int | list = ...,
        backend: _str | None = ...,
        **kwargs,
    ): ...
    def boxplot(
        self,
        column: _str | list[_str] | None = ...,
        by: _str | ListLike | None = ...,
        ax: PlotAxes | None = ...,
        fontsize: float | _str | None = ...,
        rot: float = ...,
        grid: _bool = ...,
        figsize: tuple[float, float] | None = ...,
        layout: tuple[int, int] | None = ...,
        return_type: Literal["axes", "dict", "both"] | None = ...,
        backend: _str | None = ...,
        **kwargs,
    ): ...
    sparse = ...

    # The rest of these are remnants from the
    # stubs shipped at preview. They may belong in
    # base classes, or stubgen just failed to generate
    # these.

    Name: _str
    #
    # dunder methods
    def __iter__(self) -> Iterator[Hashable]: ...
    # properties
    @property
    def at(self): ...  # Not sure what to do with this yet; look at source
    @property
    def columns(self) -> Index[str]: ...
    @columns.setter  # setter needs to be right next to getter; otherwise mypy complains
    def columns(
        self, cols: AnyArrayLike | SequenceNotStr[Hashable] | tuple[Hashable, ...]
    ) -> None: ...
    @property
    def dtypes(self) -> Series: ...
    @property
    def empty(self) -> _bool: ...
    @property
    def iat(self): ...  # Not sure what to do with this yet; look at source
    @property
    def iloc(self) -> _iLocIndexerFrame[Self]: ...
    @property
    def index(self) -> Index: ...
    @index.setter
    def index(self, idx: Index) -> None: ...
    @property
    def loc(self) -> _LocIndexerFrame[Self]: ...
    @property
    def ndim(self) -> int: ...
    @property
    def size(self) -> int: ...
    @property
    def values(self) -> np.ndarray: ...
    # methods
    def abs(self) -> Self: ...
    def add(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def add_prefix(self, prefix: _str, axis: Axis | None = None) -> Self: ...
    def add_suffix(self, suffix: _str, axis: Axis | None = None) -> Self: ...
    @overload
    def all(
        self,
        axis: None,
        bool_only: _bool | None = ...,
        skipna: _bool = ...,
        **kwargs,
    ) -> _bool: ...
    @overload
    def all(
        self,
        axis: Axis = ...,
        bool_only: _bool | None = ...,
        skipna: _bool = ...,
        **kwargs,
    ) -> Series[_bool]: ...
    @overload
    def any(
        self,
        *,
        axis: None,
        bool_only: _bool | None = ...,
        skipna: _bool = ...,
        **kwargs,
    ) -> _bool: ...
    @overload
    def any(
        self,
        *,
        axis: Axis = ...,
        bool_only: _bool | None = ...,
        skipna: _bool = ...,
        **kwargs,
    ) -> Series[_bool]: ...
    def asof(self, where, subset: _str | list[_str] | None = ...) -> Self: ...
    def asfreq(
        self,
        freq,
        method: FillnaOptions | None = ...,
        how: Literal["start", "end"] | None = ...,
        normalize: _bool = ...,
        fill_value: Scalar | None = ...,
    ) -> Self: ...
    def astype(
        self,
        dtype: AstypeArg | Mapping[Any, Dtype] | Series,
        copy: _bool = ...,
        errors: IgnoreRaise = ...,
    ) -> Self: ...
    def at_time(
        self,
        time: _str | dt.time,
        asof: _bool = ...,
        axis: Axis | None = ...,
    ) -> Self: ...
    def between_time(
        self,
        start_time: _str | dt.time,
        end_time: _str | dt.time,
        axis: Axis | None = ...,
    ) -> Self: ...
    @overload
    def bfill(
        self,
        *,
        axis: Axis | None = ...,
        inplace: Literal[True],
        limit: int | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
    ) -> None: ...
    @overload
    def bfill(
        self,
        *,
        axis: Axis | None = ...,
        inplace: Literal[False] = ...,
        limit: int | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
    ) -> Self: ...
    @overload
    def clip(
        self,
        lower: float | AnyArrayLike | None = ...,
        upper: float | AnyArrayLike | None = ...,
        *,
        axis: Axis | None = ...,
        inplace: Literal[True],
        **kwargs,
    ) -> None: ...
    @overload
    def clip(
        self,
        lower: float | AnyArrayLike | None = ...,
        upper: float | AnyArrayLike | None = ...,
        *,
        axis: Axis | None = ...,
        inplace: Literal[False] = ...,
        **kwargs,
    ) -> Self: ...
    def copy(self, deep: _bool = ...) -> Self: ...
    def cummax(
        self, axis: Axis | None = ..., skipna: _bool = ..., *args, **kwargs
    ) -> Self: ...
    def cummin(
        self, axis: Axis | None = ..., skipna: _bool = ..., *args, **kwargs
    ) -> Self: ...
    def cumprod(
        self, axis: Axis | None = ..., skipna: _bool = ..., *args, **kwargs
    ) -> Self: ...
    def cumsum(
        self, axis: Axis | None = ..., skipna: _bool = ..., *args, **kwargs
    ) -> Self: ...
    def describe(
        self,
        percentiles: list[float] | None = ...,
        include: Literal["all"] | list[Dtype] | None = ...,
        exclude: list[Dtype] | None = ...,
    ) -> Self: ...
    def div(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def divide(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def droplevel(self, level: Level | list[Level], axis: Axis = ...) -> Self: ...
    def eq(self, other, axis: Axis = ..., level: Level | None = ...) -> Self: ...
    def equals(self, other: Series | DataFrame) -> _bool: ...
    def ewm(
        self,
        com: float | None = ...,
        span: float | None = ...,
        halflife: float | None = ...,
        alpha: float | None = ...,
        min_periods: int = ...,
        adjust: _bool = ...,
        ignore_na: _bool = ...,
        axis: Axis = ...,
    ) -> ExponentialMovingWindow[Self]: ...
    def expanding(
        self,
        min_periods: int = ...,
        axis: AxisIndex = ...,
        method: CalculationMethod = ...,
    ) -> Expanding[Self]: ...
    @overload
    def ffill(
        self,
        *,
        axis: Axis | None = ...,
        inplace: Literal[True],
        limit: int | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
    ) -> None: ...
    @overload
    def ffill(
        self,
        *,
        axis: Axis | None = ...,
        inplace: Literal[False] = ...,
        limit: int | None = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
    ) -> Self: ...
    def filter(
        self,
        items: ListLike | None = ...,
        like: _str | None = ...,
        regex: _str | None = ...,
        axis: Axis | None = ...,
    ) -> Self: ...
    def first(self, offset) -> Self: ...
    def first_valid_index(self) -> Scalar: ...
    def floordiv(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    # def from_dict
    # def from_records
    def ge(self, other, axis: Axis = ..., level: Level | None = ...) -> Self: ...
    @overload
    def get(self, key: Hashable, default: None = ...) -> Series | None: ...
    @overload
    def get(self, key: Hashable, default: _T) -> Series | _T: ...
    @overload
    def get(self, key: list[Hashable], default: None = ...) -> Self | None: ...
    @overload
    def get(self, key: list[Hashable], default: _T) -> Self | _T: ...
    def gt(self, other, axis: Axis = ..., level: Level | None = ...) -> Self: ...
    def head(self, n: int = ...) -> Self: ...
    def infer_objects(self) -> Self: ...
    # def info
    @overload
    def interpolate(
        self,
        method: InterpolateOptions = ...,
        *,
        axis: Axis = ...,
        limit: int | None = ...,
        limit_direction: Literal["forward", "backward", "both"] = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
        inplace: Literal[True],
        **kwargs,
    ) -> None: ...
    @overload
    def interpolate(
        self,
        method: InterpolateOptions = ...,
        *,
        axis: Axis = ...,
        limit: int | None = ...,
        limit_direction: Literal["forward", "backward", "both"] = ...,
        limit_area: Literal["inside", "outside"] | None = ...,
        inplace: Literal[False] = ...,
        **kwargs,
    ) -> Self: ...
    def keys(self) -> Index: ...
    def kurt(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    def kurtosis(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    def last(self, offset) -> Self: ...
    def last_valid_index(self) -> Scalar: ...
    def le(self, other, axis: Axis = ..., level: Level | None = ...) -> Self: ...
    def lt(self, other, axis: Axis = ..., level: Level | None = ...) -> Self: ...
    @overload
    def mask(
        self,
        cond: (
            Series
            | DataFrame
            | np.ndarray
            | Callable[[DataFrame], DataFrame]
            | Callable[[Any], _bool]
        ),
        other: Scalar | Series[S1] | DataFrame | Callable | NAType | None = ...,
        *,
        inplace: Literal[True],
        axis: Axis | None = ...,
        level: Level | None = ...,
    ) -> None: ...
    @overload
    def mask(
        self,
        cond: (
            Series
            | DataFrame
            | np.ndarray
            | Callable[[DataFrame], DataFrame]
            | Callable[[Any], _bool]
        ),
        other: Scalar | Series[S1] | DataFrame | Callable | NAType | None = ...,
        *,
        inplace: Literal[False] = ...,
        axis: Axis | None = ...,
        level: Level | None = ...,
    ) -> Self: ...
    def max(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    def mean(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    def median(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    def min(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    def mod(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def mul(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def multiply(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def ne(self, other, axis: Axis = ..., level: Level | None = ...) -> Self: ...
    def pct_change(
        self,
        periods: int = ...,
        fill_method: None = ...,
        limit: int | None = ...,
        freq=...,
        **kwargs,
    ) -> Self: ...
    def pop(self, item: _str) -> Series: ...
    def pow(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def prod(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        min_count: int = ...,
        **kwargs,
    ) -> Series: ...
    def product(
        self,
        axis: Axis | None = ...,
        skipna: _bool = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        min_count: int = ...,
        **kwargs,
    ) -> Series: ...
    def radd(
        self,
        other,
        axis: Axis = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def rank(
        self,
        axis: Axis = ...,
        method: Literal["average", "min", "max", "first", "dense"] = ...,
        numeric_only: _bool = ...,
        na_option: Literal["keep", "top", "bottom"] = ...,
        ascending: _bool = ...,
        pct: _bool = ...,
    ) -> Self: ...
    def rdiv(
        self,
        other,
        axis: Axis = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def reindex_like(
        self,
        other: DataFrame,
        method: _str | FillnaOptions | Literal["nearest"] | None = ...,
        copy: _bool = ...,
        limit: int | None = ...,
        tolerance: Scalar | AnyArrayLike | Sequence[Scalar] = ...,
    ) -> Self: ...
    # Rename axis with `mapper`, `axis`, and `inplace=True`
    @overload
    def rename_axis(
        self,
        mapper: Scalar | ListLike | None = ...,
        *,
        axis: Axis | None = ...,
        copy: _bool = ...,
        inplace: Literal[True],
    ) -> None: ...
    # Rename axis with `mapper`, `axis`, and `inplace=False`
    @overload
    def rename_axis(
        self,
        mapper: Scalar | ListLike | None = ...,
        *,
        axis: Axis | None = ...,
        copy: _bool = ...,
        inplace: Literal[False] = ...,
    ) -> Self: ...
    # Rename axis with `index` and/or `columns` and `inplace=True`
    @overload
    def rename_axis(
        self,
        *,
        index: _str | Sequence[_str] | dict[_str | int, _str] | Callable | None = ...,
        columns: _str | Sequence[_str] | dict[_str | int, _str] | Callable | None = ...,
        copy: _bool = ...,
        inplace: Literal[True],
    ) -> None: ...
    # Rename axis with `index` and/or `columns` and `inplace=False`
    @overload
    def rename_axis(
        self,
        *,
        index: _str | Sequence[_str] | dict[_str | int, _str] | Callable | None = ...,
        columns: _str | Sequence[_str] | dict[_str | int, _str] | Callable | None = ...,
        copy: _bool = ...,
        inplace: Literal[False] = ...,
    ) -> Self: ...
    def rfloordiv(
        self,
        other,
        axis: Axis = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def rmod(
        self,
        other,
        axis: Axis = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def rmul(
        self,
        other,
        axis: Axis = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    @overload
    def rolling(
        self,
        window: int | str | dt.timedelta | BaseOffset | BaseIndexer,
        min_periods: int | None = ...,
        center: _bool = ...,
        on: Hashable | None = ...,
        axis: AxisIndex = ...,
        closed: IntervalClosedType | None = ...,
        step: int | None = ...,
        method: CalculationMethod = ...,
        *,
        win_type: _str,
    ) -> Window[Self]: ...
    @overload
    def rolling(
        self,
        window: int | str | dt.timedelta | BaseOffset | BaseIndexer,
        min_periods: int | None = ...,
        center: _bool = ...,
        on: Hashable | None = ...,
        axis: AxisIndex = ...,
        closed: IntervalClosedType | None = ...,
        step: int | None = ...,
        method: CalculationMethod = ...,
        *,
        win_type: None = ...,
    ) -> Rolling[Self]: ...
    def rpow(
        self,
        other,
        axis: Axis = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def rsub(
        self,
        other,
        axis: Axis = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def rtruediv(
        self,
        other,
        axis: Axis = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    # sample is missing a weights arg
    def sample(
        self,
        n: int | None = ...,
        frac: float | None = ...,
        replace: _bool = ...,
        weights: _str | ListLike | None = ...,
        random_state: RandomState | None = ...,
        axis: AxisIndex | None = ...,
        ignore_index: _bool = ...,
    ) -> Self: ...
    def sem(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        ddof: int = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    # Not actually positional, but used to handle removal of deprecated
    def set_axis(self, labels, *, axis: Axis, copy: _bool = ...) -> Self: ...
    def skew(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    def squeeze(self, axis: Axis | None = ...): ...
    def std(
        self,
        axis: Axis = ...,
        skipna: _bool = ...,
        level: None = ...,
        ddof: int = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    def sub(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def subtract(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def sum(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        numeric_only: _bool = ...,
        min_count: int = ...,
        **kwargs,
    ) -> Series: ...
    def swapaxes(self, axis1: Axis, axis2: Axis, copy: _bool = ...) -> Self: ...
    def tail(self, n: int = ...) -> Self: ...
    def take(self, indices: list, axis: Axis = ..., **kwargs) -> Self: ...
    def to_clipboard(
        self, excel: _bool = ..., sep: _str | None = ..., **kwargs
    ) -> None: ...
    @overload
    def to_json(
        self,
        path_or_buf: FilePath | WriteBuffer[str],
        *,
        orient: Literal["records"],
        date_format: Literal["epoch", "iso"] | None = ...,
        double_precision: int = ...,
        force_ascii: _bool = ...,
        date_unit: TimeUnit = ...,
        default_handler: (
            Callable[[Any], _str | float | _bool | list | dict] | None
        ) = ...,
        lines: Literal[True],
        compression: CompressionOptions = ...,
        index: _bool = ...,
        indent: int | None = ...,
        mode: Literal["a"],
    ) -> None: ...
    @overload
    def to_json(
        self,
        path_or_buf: None = ...,
        *,
        orient: Literal["records"],
        date_format: Literal["epoch", "iso"] | None = ...,
        double_precision: int = ...,
        force_ascii: _bool = ...,
        date_unit: TimeUnit = ...,
        default_handler: (
            Callable[[Any], _str | float | _bool | list | dict] | None
        ) = ...,
        lines: Literal[True],
        compression: CompressionOptions = ...,
        index: _bool = ...,
        indent: int | None = ...,
        mode: Literal["a"],
    ) -> _str: ...
    @overload
    def to_json(
        self,
        path_or_buf: None = ...,
        orient: JsonFrameOrient | None = ...,
        date_format: Literal["epoch", "iso"] | None = ...,
        double_precision: int = ...,
        force_ascii: _bool = ...,
        date_unit: TimeUnit = ...,
        default_handler: (
            Callable[[Any], _str | float | _bool | list | dict] | None
        ) = ...,
        lines: _bool = ...,
        compression: CompressionOptions = ...,
        index: _bool = ...,
        indent: int | None = ...,
        mode: Literal["w"] = ...,
    ) -> _str: ...
    @overload
    def to_json(
        self,
        path_or_buf: FilePath | WriteBuffer[str],
        orient: JsonFrameOrient | None = ...,
        date_format: Literal["epoch", "iso"] | None = ...,
        double_precision: int = ...,
        force_ascii: _bool = ...,
        date_unit: TimeUnit = ...,
        default_handler: (
            Callable[[Any], _str | float | _bool | list | dict] | None
        ) = ...,
        lines: _bool = ...,
        compression: CompressionOptions = ...,
        index: _bool = ...,
        indent: int | None = ...,
        mode: Literal["w"] = ...,
    ) -> None: ...
    @overload
    def to_string(
        self,
        buf: FilePath | WriteBuffer[str],
        columns: SequenceNotStr[Hashable] | Index | Series | None = ...,
        col_space: int | list[int] | dict[HashableT, int] | None = ...,
        header: _bool | list[_str] | tuple[str, ...] = ...,
        index: _bool = ...,
        na_rep: _str = ...,
        formatters: FormattersType | None = ...,
        float_format: Callable[[float], str] | None = ...,
        sparsify: _bool | None = ...,
        index_names: _bool = ...,
        justify: _str | None = ...,
        max_rows: int | None = ...,
        max_cols: int | None = ...,
        show_dimensions: _bool = ...,
        decimal: _str = ...,
        line_width: int | None = ...,
        min_rows: int | None = ...,
        max_colwidth: int | None = ...,
        encoding: _str | None = ...,
    ) -> None: ...
    @overload
    def to_string(
        self,
        buf: None = ...,
        columns: Sequence[Hashable] | Index | Series | None = ...,
        col_space: int | list[int] | dict[Hashable, int] | None = ...,
        header: _bool | Sequence[_str] = ...,
        index: _bool = ...,
        na_rep: _str = ...,
        formatters: FormattersType | None = ...,
        float_format: Callable[[float], str] | None = ...,
        sparsify: _bool | None = ...,
        index_names: _bool = ...,
        justify: _str | None = ...,
        max_rows: int | None = ...,
        max_cols: int | None = ...,
        show_dimensions: _bool = ...,
        decimal: _str = ...,
        line_width: int | None = ...,
        min_rows: int | None = ...,
        max_colwidth: int | None = ...,
        encoding: _str | None = ...,
    ) -> _str: ...
    def to_xarray(self) -> xr.Dataset: ...
    def truediv(
        self,
        other: num | ListLike | DataFrame,
        axis: Axis | None = ...,
        level: Level | None = ...,
        fill_value: float | None = ...,
    ) -> Self: ...
    def truncate(
        self,
        before: dt.date | _str | int | None = ...,
        after: dt.date | _str | int | None = ...,
        axis: Axis | None = ...,
        copy: _bool = ...,
    ) -> Self: ...
    def tz_convert(
        self,
        tz: TimeZones,
        axis: Axis = ...,
        level: Level | None = ...,
        copy: _bool = ...,
    ) -> Self: ...
    def tz_localize(
        self,
        tz: TimeZones,
        axis: Axis = ...,
        level: Level | None = ...,
        copy: _bool = ...,
        ambiguous=...,
        nonexistent: _str = ...,
    ) -> Self: ...
    def var(
        self,
        axis: Axis | None = ...,
        skipna: _bool | None = ...,
        level: None = ...,
        ddof: int = ...,
        numeric_only: _bool = ...,
        **kwargs,
    ) -> Series: ...
    @overload
    def where(
        self,
        cond: (
            Series
            | DataFrame
            | np.ndarray
            | Callable[[DataFrame], DataFrame]
            | Callable[[Any], _bool]
        ),
        other=...,
        *,
        inplace: Literal[True],
        axis: Axis | None = ...,
        level: Level | None = ...,
    ) -> None: ...
    @overload
    def where(
        self,
        cond: (
            Series
            | DataFrame
            | np.ndarray
            | Callable[[DataFrame], DataFrame]
            | Callable[[Any], _bool]
        ),
        other=...,
        *,
        inplace: Literal[False] = ...,
        axis: Axis | None = ...,
        level: Level | None = ...,
    ) -> Self: ...
    # Move from generic because Series is Generic and it returns Series[bool] there
    def __invert__(self) -> Self: ...
    def xs(
        self,
        key: Hashable,
        axis: Axis = ...,
        level: Level | None = ...,
        drop_level: _bool = ...,
    ) -> Self | Series: ...
    # floordiv overload
    def __floordiv__(
        self, other: float | DataFrame | Series[int] | Series[float] | Sequence[float]
    ) -> Self: ...
    def __rfloordiv__(
        self, other: float | DataFrame | Series[int] | Series[float] | Sequence[float]
    ) -> Self: ...
    def __truediv__(self, other: float | DataFrame | Series | Sequence) -> Self: ...
    def __rtruediv__(self, other: float | DataFrame | Series | Sequence) -> Self: ...
    def __bool__(self) -> NoReturn: ...

class _PandasNamedTuple(tuple[Any, ...]):
    def __getattr__(self, field: str) -> Scalar: ...
