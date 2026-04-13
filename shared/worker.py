# core/worker.py

import logging
import traceback
import xml.etree.ElementTree as ET

from shared.models import ParseResult, ErrorInfo, WorkerResult, DataType, DocType
from cte.parser import CTeParser
from cte.event_parser import CTeEventParser
from nfe.parser import NFeParser
from nfe.event_parser import NFeEventParser

logger = logging.getLogger(__name__)


def process_single_xml(xml_file: str, expected_type: DocType = DocType.CTE) -> WorkerResult:
    """Processa um único XML com validação de segurança e routing por DocType.

    O worker inspeciona a root tag do XML. Se o documento pertencer a uma
    família diferente da selecionada pelo utilizador (ex: NF-e quando se
    pediu CT-e), o ficheiro é bloqueado e enviado para quarentena.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        root_tag = root.tag.split('}')[-1].lower()

        _validate_document_type(root_tag, expected_type)

        if expected_type == DocType.CTE:
            return _route_cte(root)

        return _route_nfe(root)

    except Exception as e:
        return WorkerResult(
            result=None,
            error=ErrorInfo(xml_file, str(e), traceback.format_exc())
        )


def _validate_document_type(root_tag: str, expected_type: DocType) -> None:
    """Valida se o documento XML corresponde ao tipo esperado.

    Raises:
        ValueError: se houver divergência entre o tipo esperado e o conteúdo real.
    """
    if expected_type == DocType.CTE and "nfe" in root_tag:
        raise ValueError(
            "Divergência: O ficheiro é uma NF-e, mas o processamento "
            "selecionado foi CT-e. Ficheiro enviado para quarentena."
        )

    if expected_type == DocType.NFE and "cte" in root_tag:
        raise ValueError(
            "Divergência: O ficheiro é um CT-e, mas o processamento "
            "selecionado foi NF-e (DANFE). Ficheiro enviado para quarentena."
        )


def _route_cte(root: ET.Element) -> WorkerResult:
    """Tenta parsear como CT-e, depois como Evento CT-e."""
    cte_data = CTeParser(root).extract_data()
    if cte_data is not None:
        return WorkerResult(result=ParseResult(DataType.CTE, cte_data), error=None)

    event_data = CTeEventParser(root).extract_data()
    if event_data is not None:
        return WorkerResult(result=ParseResult(DataType.EVENT, event_data), error=None)

    return WorkerResult(result=ParseResult(DataType.IGNORE, None), error=None)


def _route_nfe(root: ET.Element) -> WorkerResult:
    """Tenta parsear como NF-e, depois como Evento NF-e."""
    nfe_data = NFeParser(root).extract_data()
    if nfe_data is not None:
        return WorkerResult(result=ParseResult(DataType.NFE, nfe_data), error=None)

    event_data = NFeEventParser(root).extract_data()
    if event_data is not None:
        return WorkerResult(result=ParseResult(DataType.EVENT, event_data), error=None)

    return WorkerResult(result=ParseResult(DataType.IGNORE, None), error=None)
