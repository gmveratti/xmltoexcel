# core/worker.py

import logging
import traceback
import xml.etree.ElementTree as ET

from core.models import ParseResult, ErrorInfo, WorkerResult, DataType
from core.strategy import resolve_strategy

logger = logging.getLogger(__name__)


def process_single_xml(xml_file: str, doc_type: str = "CTE") -> WorkerResult:
    """
    Processa um único arquivo XML utilizando a estratégia correspondente.

    Args:
        xml_file: Caminho absoluto para o arquivo XML.
        doc_type: "CTE" ou "NFE". Define a estratégia de parsing.

    Returns:
        WorkerResult com resultado ou erro de quarentena.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        strategy = resolve_strategy(doc_type)
        return _process_document(root, xml_file, strategy)

    except ET.ParseError as e:
        return WorkerResult(
            result=None,
            error=ErrorInfo(xml_file, f"XML malformado: {e}", traceback.format_exc())
        )
    except Exception as e:
        return WorkerResult(
            result=None,
            error=ErrorInfo(xml_file, str(e), traceback.format_exc())
        )


def _process_document(root: ET.Element, xml_file: str, strategy) -> WorkerResult:
    """Ramo de processamento genérico baseado em estratégia."""
    MainParser, EventParser = strategy.get_parsers()
    
    # 1. Tenta parsear como documento principal (CTE/NFE)
    main_parser = MainParser(root)
    main_data = main_parser.extract_data()
    if main_data is not None:
        return WorkerResult(result=ParseResult(strategy.main_data_type, main_data), error=None)

    # 2. Tenta parsear como evento
    event_parser = EventParser(root)
    event_data = event_parser.extract_data()
    if event_data is not None:
        return WorkerResult(result=ParseResult(DataType.EVENT, event_data), error=None)

    return WorkerResult(result=ParseResult(DataType.IGNORE, None), error=None)
