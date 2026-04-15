# nfe/nfe_strategy.py

import logging
from typing import List, Dict, Any, Set, Tuple
from core.strategy import DocumentStrategy
from core.models import DataType
from nfe.nfe_constants import NFE_HEADERS, NFE_GRAY_COLS, NFE_ACCOUNTING_COLS
from nfe.nfe_parser import NFeParser
from nfe.nfe_event_parser import NFeEventParser

logger = logging.getLogger(__name__)

class NFeStrategy(DocumentStrategy):
    """Estratégia específica para processamento de NF-e."""

    @property
    def doc_type_name(self) -> str:
        return "NFE"

    @property
    def main_data_type(self) -> DataType:
        return DataType.NFE

    @property
    def excel_headers(self) -> List[str]:
        return NFE_HEADERS

    def get_parsers(self) -> Tuple[type, type]:
        return NFeParser, NFeEventParser

    @property
    def accounting_cols(self) -> Set[str]:
        return NFE_ACCOUNTING_COLS

    def is_gray_col(self, header: str) -> bool:
        return header in NFE_GRAY_COLS

    def process_result_data(self, 
                             data: Any, 
                             data_type: DataType,
                             all_main_data: List[Any], 
                             all_event_data: List[Any],
                             seen_main_keys: Set[Any], 
                             seen_event_keys: Set[Any]) -> int:
        duplicate_count = 0
        
        if data_type == DataType.NFE:
            # data é List[Dict] — um por produto
            for row in data:
                nfe_item_key = (
                    row.get("chv_nfe_Id", ""),
                    row.get("nItem_nItem", "")
                )
                if nfe_item_key in seen_main_keys:
                    duplicate_count += 1
                    logger.debug("NF-e item duplicado ignorado: %s #%s",
                                 nfe_item_key[0], nfe_item_key[1])
                else:
                    seen_main_keys.add(nfe_item_key)
                    all_main_data.append(row)
        
        elif data_type == DataType.EVENT:
            event_key = (
                data.get("Chave de Acesso (Referência)", ""),
                data.get("Tipo de Evento", ""),
                data.get("Data do Evento", ""),
                data.get("Detalhes / Justificativa", "")
            )
            if event_key in seen_event_keys:
                duplicate_count += 1
                logger.debug("Evento duplicado ignorado: %s", event_key[0])
            else:
                seen_event_keys.add(event_key)
                all_event_data.append(data)
                
        return duplicate_count
