# core/models.py

from dataclasses import dataclass
from typing import Dict, Any, Optional, Union, List
from enum import Enum, auto


class DocType(Enum):
    """Tipo de documento fiscal selecionado pelo utilizador na UI."""
    CTE = auto()
    NFE = auto()


class DataType(Enum):
    """Tipo de dado retornado pelo parser após análise do XML."""
    CTE = auto()
    NFE = auto()
    EVENT = auto()
    IGNORE = auto()


@dataclass
class ParseResult:
    data_type: DataType
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]


@dataclass
class ErrorInfo:
    xml_file: str
    error_msg: str
    traceback: str


@dataclass
class WorkerResult:
    result: Optional[ParseResult]
    error: Optional[ErrorInfo]


# --- Mensagens para a Interface (UI) ---
@dataclass
class StatusMessage:
    text: str


@dataclass
class StartMessage:
    total_files: int


@dataclass
class ProgressMessage:
    current: int
    total: int


@dataclass
class NoFilesMessage:
    pass


@dataclass
class DoneMessage:
    total_read: int
    total_success: int
    total_errors: int


@dataclass
class FatalErrorMessage:
    error_msg: str
