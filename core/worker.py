# core/worker.py

import logging
import traceback

from core.models import ParseResult, ErrorInfo, WorkerResult
from parsers.cte_parser import CTeParser
from parsers.cte_event_parser import CTeEventParser

logger = logging.getLogger(__name__)


def process_single_xml(xml_file: str) -> WorkerResult:
    """
    Função global para o ProcessPoolExecutor.
    Decide automaticamente se o XML é um CT-e, um Evento, ou um lixo a ser ignorado.
    """
    try:
        # 1. Tenta extrair como CT-e normal
        cte_parser = CTeParser(xml_file)
        cte_data = cte_parser.extract_data()
        if cte_data is not None:
            return WorkerResult(result=ParseResult("CTE", cte_data), error=None)

        # 2. Se não encontrou tag de CT-e, tenta extrair como Evento (Cancelamento/CC-e)
        event_parser = CTeEventParser(xml_file)
        event_data = event_parser.extract_data()
        if event_data is not None:
            return WorkerResult(result=ParseResult("EVENT", event_data), error=None)

        # 3. Se não for nenhum dos dois, ignora o arquivo
        return WorkerResult(result=ParseResult("IGNORE", None), error=None)

    except Exception as e:
        logger.warning("Falha ao processar XML '%s': %s", xml_file, e)
        return WorkerResult(
            result=None,
            error=ErrorInfo(xml_file, str(e), traceback.format_exc())
        )
