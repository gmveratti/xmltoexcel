# core/worker.py

import logging
import traceback
import xml.etree.ElementTree as ET

from core.models import ParseResult, ErrorInfo, WorkerResult, DataType
from parsers.cte_parser import CTeParser
from parsers.cte_event_parser import CTeEventParser

logger = logging.getLogger(__name__)

# Importação lazy do NFeParser para não poluir o namespace do CT-e
# (e evitar problemas de import no multiprocessamento Windows)
_NFE_SENTINEL = ".//{{http://www.portalfiscal.inf.br/nfe}}infNFe"
_CTE_SENTINEL = ".//{{http://www.portalfiscal.inf.br/cte}}infCte"


def process_single_xml(xml_file: str, doc_type: str = "CTE") -> WorkerResult:
    """
    Processa um único arquivo XML.

    Args:
        xml_file: Caminho absoluto para o arquivo XML.
        doc_type: "CTE" ou "NFE". Define o parser e a validação de compatibilidade.

    Returns:
        WorkerResult com resultado ou erro de quarentena.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        if doc_type == "NFE":
            return _process_nfe(root, xml_file)
        else:
            return _process_cte(root, xml_file)

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


def _process_cte(root: ET.Element, xml_file: str) -> WorkerResult:
    """Ramo de processamento CT-e com validação de incompatibilidade."""
    # Detecta NF-e enviada por engano no modo CT-e
    nfe_ns = "http://www.portalfiscal.inf.br/nfe"
    if root.find(f".//{{{nfe_ns}}}infNFe") is not None:
        return WorkerResult(
            result=None,
            error=ErrorInfo(
                xml_file,
                "Incompatibilidade: Este XML é uma NF-e, mas o modo CT-e está selecionado.",
                "Selecione o tipo 'NF-e / DANFE' na interface antes de processar."
            )
        )

    cte_parser = CTeParser(root)
    cte_data = cte_parser.extract_data()
    if cte_data is not None:
        return WorkerResult(result=ParseResult(DataType.CTE, cte_data), error=None)

    event_parser = CTeEventParser(root)
    event_data = event_parser.extract_data()
    if event_data is not None:
        return WorkerResult(result=ParseResult(DataType.EVENT, event_data), error=None)

    return WorkerResult(result=ParseResult(DataType.IGNORE, None), error=None)


def _process_nfe(root: ET.Element, xml_file: str) -> WorkerResult:
    """Ramo de processamento NF-e com validação de incompatibilidade."""
    from nfe.nfe_parser import NFeParser  # import local — padrão seguro no Windows multiprocess

    # Detecta CT-e enviado por engano no modo NF-e
    cte_ns = "http://www.portalfiscal.inf.br/cte"
    if root.find(f".//{{{cte_ns}}}infCte") is not None:
        return WorkerResult(
            result=None,
            error=ErrorInfo(
                xml_file,
                "Incompatibilidade: Este XML é um CT-e, mas o modo NF-e está selecionado.",
                "Selecione o tipo 'CT-e (Transporte)' na interface antes de processar."
            )
        )

    nfe_parser = NFeParser(root)
    nfe_data = nfe_parser.extract_data()

    if nfe_data is not None:
        # nfe_data é uma List[Dict] — uma entrada por produto
        return WorkerResult(result=ParseResult(DataType.NFE, nfe_data), error=None)

    from nfe.nfe_event_parser import NFeEventParser
    event_parser = NFeEventParser(root)
    event_data = event_parser.extract_data()

    if event_data is not None:
        return WorkerResult(result=ParseResult(DataType.EVENT, event_data), error=None)

    return WorkerResult(result=ParseResult(DataType.IGNORE, None), error=None)
