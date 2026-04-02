# core/worker.py

import logging
import traceback
import defusedxml.ElementTree as ET

from core.models import ParseResult, ErrorInfo, WorkerResult
from parsers.cte_parser import CTeParser
from parsers.cte_event_parser import CTeEventParser

logger = logging.getLogger(__name__)


def process_single_xml(xml_file: str) -> WorkerResult:
    """
    Função global para o ProcessPoolExecutor.
    Abre o XML UMA ÚNICA VEZ no disco e repassa a memória para os parsers (Velocidade Extrema).
    """
    try:
        # 1. Leitura segura e única do disco (Protegida contra XML Bomb)
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 2. Tenta extrair como CT-e normal (Passa a árvore na memória)
        cte_parser = CTeParser(root)
        cte_data = cte_parser.extract_data()
        if cte_data is not None:
            return WorkerResult(result=ParseResult("CTE", cte_data), error=None)

        # 3. Se não encontrou tag de CT-e, tenta extrair como Evento (Usa a mesma memória)
        event_parser = CTeEventParser(root)
        event_data = event_parser.extract_data()
        if event_data is not None:
            return WorkerResult(result=ParseResult("EVENT", event_data), error=None)

        # 4. Ignora o ficheiro se não for nenhum dos dois
        return WorkerResult(result=ParseResult("IGNORE", None), error=None)

    except Exception as e:
        logger.warning("Falha ao processar XML '%s': %s", xml_file, e)
        return WorkerResult(
            result=None,
            error=ErrorInfo(xml_file, str(e), traceback.format_exc())
        )
