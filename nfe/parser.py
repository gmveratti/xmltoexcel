# parsers/nfe_parser.py

import re
import logging
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

from shared.constants import NFE_HEADERS
from shared.base_parser import BaseXMLParser

logger = logging.getLogger(__name__)
_PEDIDO_AMAZON_RE = re.compile(r"Numero do pedido da compra:\s*([\d-]+)", re.IGNORECASE)

class NFeParser(BaseXMLParser):
    """Parser NF-e v4.00 (Mapeamento Estrutural + Catch-All Dinâmico)"""

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
            if header in ("NFe", "chv_nfe_Id", "ext_Pedido_Amazon", "Extra_Tags_Dinamicas") or header.startswith(item_prefixes):
                continue
            
            path_parts = header.split("_")
            curr_node = inf_nfe_node
            for part in path_parts:
                curr_node = self._search_tag(curr_node, part)
                if curr_node is None: break
            
            if curr_node is not None:
                header_data[header] = self._safe_text(curr_node)

        # Regex do Pedido Amazon
        inf_cpl = header_data.get("infAdic_infCpl", "")
        match = _PEDIDO_AMAZON_RE.search(inf_cpl)
        if match: header_data["ext_Pedido_Amazon"] = match.group(1)

        # --- B: A Rede de Segurança Dinâmica (Extra_Tags_Dinamicas) ---
        # Cria lista de tags conhecidas para ignorar e pegar só as novidades
        known_tags = {h.split("_")[-1] for h in NFE_HEADERS}
        known_tags.update({"infNFe", "emit", "dest", "enderEmit", "enderDest", "det", "prod", "imposto", "ICMS", "IPI", "PIS", "COFINS", "total", "ICMSTot", "transp", "cobr", "fat", "dup", "pag", "detPag", "infAdic", "obsCont", "obsFisco", "Signature"})
        
        extras = []
        for child in inf_nfe_node.iter():
            tag = child.tag.split('}')[-1]
            if tag not in known_tags and child.text and child.text.strip():
                extras.append(f"{tag}: {child.text.strip()}")
        header_data["Extra_Tags_Dinamicas"] = " | ".join(extras)

        # --- C: Extração e Achatamento dos Itens (Flattening) ---
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

                # Lógica para Impostos (que possuem sub-tags varáveis como ICMS00, ICMS40)
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
