# core/models.py

from dataclasses import dataclass
from typing import Dict, Any, Optional, Union, List
from enum import Enum, auto

# FASE 3: Enumeração para Tipos de Dados (Segurança de Tipagem)
class DataType(Enum):
    CTE = auto()
    NFE = auto()       # NOVO
    EVENT = auto()
    IGNORE = auto()

class DocType(Enum):
    CTE = "CTE"
    NFE = "NFE"        # NOVO

@dataclass
class ParseResult:
    data_type: DataType
    # data agora suporta List[Dict] para os múltiplos itens da NF-e
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
