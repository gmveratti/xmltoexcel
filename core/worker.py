# core/worker.py

import traceback
from parsers.cte_parser import CTeParser

def process_single_xml(xml_file: str):
    """
    Função global isolada para o ProcessPoolExecutor.
    Garante que o Multiprocessamento funcione perfeitamente sem travar a GUI.
    """
    try:
        parser = CTeParser(xml_file)
        row_data = parser.extract_data()
        return row_data, None
    except Exception as e:
        return None, (xml_file, str(e), traceback.format_exc())
