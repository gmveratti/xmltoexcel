# parsers/nfe_parser.py

import logging
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

from shared.constants import NFE_HEADERS
from shared.base_parser import BaseXMLParser

logger = logging.getLogger(__name__)

class NFeParser(BaseXMLParser):
    """Parser NF-e v4.00 (Mapeamento Estrutural Estrito 1:1 - Sem tags dinâmicas)"""

    def __init__(self, root: ET.Element):
        super().__init__(root)
        self._ns = "http://www.portalfiscal.inf.br/nfe"

    def extract_data(self) -> Optional[List[Dict[str, Any]]]:
        inf_nfe_node = self.root.find(f".//{{{self._ns}}}infNFe")
        if inf_nfe_node is None: return None

        # 1. Dicionário Base do Cabeçalho
        header_data = {h: "" for h in NFE_HEADERS}
        id_nfe = inf_nfe_node.get("Id", "")
        header_data["chv_nfe_Id"] = id_nfe.replace("NFe", "")
        header_data["NFe"] = id_nfe

        item_prefixes = ("det", "prod", "imposto", "ICMS", "IPI", "PIS", "COFINS")

        # --- A: Extração Estrutural (Automática) do Cabeçalho ---
        for header in NFE_HEADERS:
            if header in ("NFe", "chv_nfe_Id") or header.startswith(item_prefixes):
                continue
            
            path_parts = header.split("_")
            curr_node = inf_nfe_node
            for part in path_parts:
                curr_node = self._search_tag(curr_node, part)
                if curr_node is None: break
            
            if curr_node is not None:
                header_data[header] = self._safe_text(curr_node)

        # --- B: Extração e Achatamento dos Itens (Flattening) ---
        items_data = []
        det_nodes = inf_nfe_node.findall(f".//{{{self._ns}}}det")

        if not det_nodes:
            items_data.append(header_data)
            return items_data

        for det in det_nodes:
            row = header_data.copy()
            row["det_nItem"] = det.get("nItem", "")

            for header in NFE_HEADERS:
                if not header.startswith(item_prefixes) or header == "det_nItem":
                    continue

                # Lógica para Impostos (que possuem sub-tags variáveis como ICMS00, ICMS40)
                if header.startswith(("ICMS_", "IPI_", "PIS_", "COFINS_")):
                    tag_imposto, tag_filho = header.split("_")[0], header.split("_")[1]
                    group_node = det.find(f".//{{{self._ns}}}{tag_imposto}")
                    if group_node is not None and len(group_node) > 0:
                        target_node = self._search_tag(group_node[0], tag_filho)
                        if target_node is not None:
                            row[header] = self._safe_text(target_node)
                    continue

                # Extração Estrutural Normal para produtos
                path_parts = header.split("_")
                curr_node = det
                for part in path_parts:
                    if part == "det": continue
                    curr_node = self._search_tag(curr_node, part)
                    if curr_node is None: break
                
                if curr_node is not None:
                    row[header] = self._safe_text(curr_node)

            items_data.append(row)

        return items_data
