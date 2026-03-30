# core/worker.py

import traceback
from parsers.cte_parser import CTeParser
from parsers.cte_event_parser import CTeEventParser

def process_single_xml(xml_file: str):
    """
    Função global para o ProcessPoolExecutor.
    Decide automaticamente se o XML é um CT-e, um Evento, ou um lixo a ser ignorado.
    """
    try:
        # 1. Tenta extrair como CT-e normal
        cte_parser = CTeParser(xml_file)
        cte_data = cte_parser.extract_data()
        if cte_data is not None:
            return ("CTE", cte_data), None
            
        # 2. Se não encontrou tag de CT-e, tenta extrair como Evento (Cancelamento/CC-e)
        event_parser = CTeEventParser(xml_file)
        event_data = event_parser.extract_data()
        if event_data is not None:
            return ("EVENT", event_data), None

        # 3. Se não for nenhum dos dois, ignora o arquivo (ex: xml corrompido ou de outro sistema)
        return ("IGNORE", None), None

    except Exception as e:
        return None, (xml_file, str(e), traceback.format_exc())
