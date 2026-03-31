# core/models.py

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class ParseResult:
    """Resultado do parsing de um XML."""
    data_type: str  # "CTE" | "EVENT" | "IGNORE"
    data: Optional[Dict[str, Any]]


@dataclass(frozen=True)
class ErrorInfo:
    """Informação de erro durante o processamento de um XML."""
    xml_file: str
    error_msg: str
    traceback: str


@dataclass(frozen=True)
class WorkerResult:
    """Retorno completo do worker (resultado + erro)."""
    result: Optional[ParseResult]
    error: Optional[ErrorInfo]


# ==================== Mensagens da Queue (Thread -> UI) ====================

@dataclass(frozen=True)
class StatusMessage:
    """Atualização de status textual."""
    text: str


@dataclass(frozen=True)
class StartMessage:
    """Sinaliza o início do processamento com total de arquivos."""
    total_files: int


@dataclass(frozen=True)
class ProgressMessage:
    """Atualização de progresso numérico."""
    current: int
    total: int


@dataclass(frozen=True)
class NoFilesMessage:
    """Sinaliza que nenhum XML foi encontrado."""
    pass


@dataclass(frozen=True)
class DoneMessage:
    """Sinaliza conclusão do processamento."""
    total_read: int
    total_success: int
    total_errors: int


@dataclass(frozen=True)
class FatalErrorMessage:
    """Sinaliza erro fatal que interrompe o processamento."""
    error_msg: str
