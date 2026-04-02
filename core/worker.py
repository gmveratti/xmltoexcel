# core/worker.py

import logging
import traceback
import xml.etree.ElementTree as ET

from core.models import ParseResult, ErrorInfo, WorkerResult, DataType
from parsers.cte_parser import CTeParser
from parsers.cte_event_parser import CTeEventParser

logger = logging.getLogger(__name__)

def process_single_xml(xml_file: str) -> WorkerResult:
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        cte_parser = CTeParser(root)
        cte_data = cte_parser.extract_data()
        if cte_data is not None:
            # Substituído a string "CTE" pelo Enum DataType.CTE
            return WorkerResult(result=ParseResult(DataType.CTE, cte_data), error=None)

        event_parser = CTeEventParser(root)
        event_data = event_parser.extract_data()
        if event_data is not None:
            return WorkerResult(result=ParseResult(DataType.EVENT, event_data), error=None)

        return WorkerResult(result=ParseResult(DataType.IGNORE, None), error=None)

    except Exception as e:
        return WorkerResult(
            result=None,
            error=ErrorInfo(xml_file, str(e), traceback.format_exc())
        )
