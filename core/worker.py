# core/worker.py

import logging
import traceback
import xml.etree.ElementTree as ET

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
        # Abertura física no disco acontece UMA ÚNICA VEZ em alta velocidade
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 1. Tenta extrair como CT-e normal (passa a memória, não o arquivo)
        cte_parser = CTeParser(root)
        cte_data = cte_parser.extract_data()
        if cte_data is not None:
            return WorkerResult(result=ParseResult("CTE", cte_data), error=None)

        # 2. Tenta extrair como Evento (usa a mesma memória, instantâneo)
        event_parser = CTeEventParser(root)
        event_data = event_parser.extract_data()
        if event_data is not None:
            return WorkerResult(result=ParseResult("EVENT", event_data), error=None)

        # 3. Ignora se não for nenhum dos dois
        return WorkerResult(result=ParseResult("IGNORE", None), error=None)

    except Exception as e:
        logger.warning("Falha ao processar XML '%s': %s", xml_file, e)
        return WorkerResult(
            result=None,
            error=ErrorInfo(xml_file, str(e), traceback.format_exc())
        )
