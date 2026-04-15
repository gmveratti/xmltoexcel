# core/strategy.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Tuple, Optional
from core.models import DataType

class DocumentStrategy(ABC):
    """
    Interface para estratégias de processamento de documentos fiscais.
    Define como cada tipo de documento (CTE, NFE, etc.) deve ser
    identificado, processado e exportado para o Excel.
    """

    @property
    @abstractmethod
    def doc_type_name(self) -> str:
        """Retorna o nome identificador do tipo de documento (ex: 'CTE', 'NFE')."""
        pass

    @property
    @abstractmethod
    def main_data_type(self) -> DataType:
        """Retorna o DataType principal deste documento."""
        pass

    @property
    @abstractmethod
    def excel_headers(self) -> List[str]:
        """Retorna a lista de cabeçalhos para a aba principal do Excel."""
        pass

    @abstractmethod
    def get_parsers(self) -> Tuple[type, type]:
        """Retorna uma tupla (MainParserClass, EventParserClass)."""
        pass

    @property
    @abstractmethod
    def accounting_cols(self) -> Set[str]:
        """Retorna o conjunto de colunas que devem ter formato contábil."""
        pass

    @abstractmethod
    def is_gray_col(self, header: str) -> bool:
        """Determina se uma coluna deve ter fundo cinza (separador)."""
        pass

    @abstractmethod
    def process_result_data(self, 
                             data: Any, 
                             data_type: DataType,
                             all_main_data: List[Any], 
                             all_event_data: List[Any],
                             seen_main_keys: Set[Any], 
                             seen_event_keys: Set[Any]) -> int:
        """
        Processa o resultado do worker, aplica deduplicação e agrega nos containers.
        Retorna o número de duplicatas encontradas neste processamento.
        """
        pass

def resolve_strategy(doc_type: str) -> DocumentStrategy:
    """Resolve a estratégia de documento com base no doc_type string."""
    if doc_type == "NFE":
        from nfe.nfe_strategy import NFeStrategy
        return NFeStrategy()
    else:
        from cte.cte_strategy import CTeStrategy
        return CTeStrategy()
