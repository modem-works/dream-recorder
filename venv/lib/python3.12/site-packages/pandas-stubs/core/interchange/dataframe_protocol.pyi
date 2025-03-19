import abc
from abc import (
    ABC,
    abstractmethod,
)
from collections.abc import (
    Iterable,
    Sequence,
)
import enum
from typing import (
    Any,
    TypedDict,
    cast,
)

class DlpackDeviceType(enum.IntEnum):
    CPU = cast(int, ...)
    CUDA = cast(int, ...)
    CPU_PINNED = cast(int, ...)
    OPENCL = cast(int, ...)
    VULKAN = cast(int, ...)
    METAL = cast(int, ...)
    VPI = cast(int, ...)
    ROCM = cast(int, ...)

class DtypeKind(enum.IntEnum):
    INT = cast(int, ...)
    UINT = cast(int, ...)
    FLOAT = cast(int, ...)
    BOOL = cast(int, ...)
    STRING = cast(int, ...)
    DATETIME = cast(int, ...)
    CATEGORICAL = cast(int, ...)

class ColumnNullType(enum.IntEnum):
    NON_NULLABLE = cast(int, ...)
    USE_NAN = cast(int, ...)
    USE_SENTINEL = cast(int, ...)
    USE_BITMASK = cast(int, ...)
    USE_BYTEMASK = cast(int, ...)

class ColumnBuffers(TypedDict):
    data: tuple[Buffer, Any]
    validity: tuple[Buffer, Any] | None
    offsets: tuple[Buffer, Any] | None

class CategoricalDescription(TypedDict):
    is_ordered: bool
    is_dictionary: bool
    categories: Column | None

class Buffer(ABC, metaclass=abc.ABCMeta):
    @property
    @abstractmethod
    def bufsize(self) -> int: ...
    @property
    @abstractmethod
    def ptr(self) -> int: ...
    @abstractmethod
    def __dlpack__(self): ...
    @abstractmethod
    def __dlpack_device__(self) -> tuple[DlpackDeviceType, int | None]: ...

class Column(ABC, metaclass=abc.ABCMeta):
    @property
    @abstractmethod
    def size(self) -> int: ...
    @property
    @abstractmethod
    def offset(self) -> int: ...
    @property
    @abstractmethod
    def dtype(self) -> tuple[DtypeKind, int, str, str]: ...
    @property
    @abstractmethod
    def describe_categorical(self) -> CategoricalDescription: ...
    @property
    @abstractmethod
    def describe_null(self) -> tuple[ColumnNullType, Any]: ...
    @property
    @abstractmethod
    def null_count(self) -> int | None: ...
    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]: ...
    @abstractmethod
    def num_chunks(self) -> int: ...
    @abstractmethod
    def get_chunks(self, n_chunks: int | None = ...) -> Iterable[Column]: ...
    @abstractmethod
    def get_buffers(self) -> ColumnBuffers: ...

class DataFrame(ABC, metaclass=abc.ABCMeta):
    version: int
    @abstractmethod
    def __dataframe__(self, nan_as_null: bool = ..., allow_copy: bool = ...): ...
    @property
    @abstractmethod
    def metadata(self) -> dict[str, Any]: ...
    @abstractmethod
    def num_columns(self) -> int: ...
    @abstractmethod
    def num_rows(self) -> int | None: ...
    @abstractmethod
    def num_chunks(self) -> int: ...
    @abstractmethod
    def column_names(self) -> Iterable[str]: ...
    @abstractmethod
    def get_column(self, i: int) -> Column: ...
    @abstractmethod
    def get_column_by_name(self, name: str) -> Column: ...
    @abstractmethod
    def get_columns(self) -> Iterable[Column]: ...
    @abstractmethod
    def select_columns(self, indices: Sequence[int]) -> DataFrame: ...
    @abstractmethod
    def select_columns_by_name(self, names: Sequence[str]) -> DataFrame: ...
    @abstractmethod
    def get_chunks(self, n_chunks: int | None = ...) -> Iterable[DataFrame]: ...
