# cte/cte_strategy.py

import logging
from typing import List, Dict, Any, Set, Tuple
from core.strategy import DocumentStrategy
from core.models import DataType
from core.constants import EXCEL_HEADERS
from cte.cte_parser import CTeParser
from cte.cte_event_parser import CTeEventParser

logger = logging.getLogger(__name__)

class CTeStrategy(DocumentStrategy):
    """Estratégia específica para processamento de CT-e."""

    @property
    def doc_type_name(self) -> str:
        return "CTE"

    @property
    def main_data_type(self) -> DataType:
        return DataType.CTE

    @property
    def excel_headers(self) -> List[str]:
        return EXCEL_HEADERS

    def get_parsers(self) -> Tuple[type, type]:
        return CTeParser, CTeEventParser

    @property
    def accounting_cols(self) -> Set[str]:
        return {
            "vPrest_vTPrest", "vPrest_vRec", "imp_vBC", "imp_pICMS",
            "imp_vICMS", "imp_vBCSTRet", "imp_vICMSSTRet", "imp_pICMSSTRet",
            "imp_ICMSOutraUF_vBCOutraUF", "imp_ICMSOutraUF_pICMSOutraUF",
            "imp_ICMSOutraUF_vICMSOutraUF", "imp_vTotTrib",
        }

    def is_gray_col(self, header: str) -> bool:
        return header.startswith("(") and header.endswith(")")

    def process_result_data(self, 
                             data: Any, 
                             data_type: DataType,
                             all_main_data: List[Any], 
                             all_event_data: List[Any],
                             seen_main_keys: Set[Any], 
                             seen_event_keys: Set[Any]) -> int:
        duplicate_count = 0
        
        if data_type == DataType.CTE:
            cte_key = data.get("chv_cte_Id", "")
            if cte_key and cte_key in seen_main_keys:
                duplicate_count += 1
                logger.debug("CT-e duplicado ignorado: %s", cte_key)
            else:
                if cte_key:
                    seen_main_keys.add(cte_key)
                all_main_data.append(data)
        
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
