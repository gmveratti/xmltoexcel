# core/worker.py

import logging
import traceback
import xml.etree.ElementTree as ET

from shared.models import ParseResult, ErrorInfo, WorkerResult, DataType, DocType
from cte.parser import CTeParser
from cte.event_parser import CTeEventParser
from nfe.parser import NFeParser

logger = logging.getLogger(__name__)

def process_single_xml(xml_file: str, doc_type: DocType) -> WorkerResult:
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        if doc_type == DocType.CTE:
            cte_parser = CTeParser(root)
            cte_data = cte_parser.extract_data()
            if cte_data is not None:
                return WorkerResult(result=ParseResult(DataType.CTE, cte_data), error=None)

            event_parser = CTeEventParser(root)
            event_data = event_parser.extract_data()
            if event_data is not None:
                return WorkerResult(result=ParseResult(DataType.EVENT, event_data), error=None)
                
        elif doc_type == DocType.NFE:
            nfe_parser = NFeParser(root)
            nfe_data = nfe_parser.extract_data()
            if nfe_data is not None:
                return WorkerResult(result=ParseResult(DataType.NFE, nfe_data), error=None)

        return WorkerResult(result=ParseResult(DataType.IGNORE, None), error=None)

    except Exception as e:
        return WorkerResult(
            result=None,
            error=ErrorInfo(xml_file, str(e), traceback.format_exc())
        )
