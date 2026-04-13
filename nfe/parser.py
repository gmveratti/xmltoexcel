# nfe/parser.py

import logging
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

from shared.base_parser import BaseXMLParser
from nfe.constants import NFE_HEADERS, NFE_NAMESPACE

logger = logging.getLogger(__name__)

class NFeParser(BaseXMLParser):
    def __init__(self, root: ET.Element):
        super().__init__(root)
        self._ns = NFE_NAMESPACE

    def extract_data(self) -> Optional[List[Dict[str, Any]]]:
        inf_nfe_node = self.root.find(f".//{{{self._ns.get('ns', 'http://www.portalfiscal.inf.br/nfe')}}}infNFe")
        if inf_nfe_node is None:
            # Fallback trying without ns dictionary wrap if the previous didn't work.
            # Using _search_tag might be safer but `find` is explicit here.
            inf_nfe_node = self.root.find(".//ns:infNFe", self._ns)
        
        if inf_nfe_node is None: return None

        header_data = {h: "" for h in NFE_HEADERS}
        id_nfe = inf_nfe_node.get("Id", "")
        header_data["chv_nfe_Id"] = id_nfe.replace("NFe", "")
        header_data["NFe"] = id_nfe

        item_prefixes = ("det", "prod", "imposto", "ICMS", "IPI", "PIS", "COFINS")

        # A: Extração Estrutural Rigorosa (Ignora os parênteses que criam as colunas cinzas)
        for header in NFE_HEADERS:
            if header in ("NFe", "chv_nfe_Id") or header.startswith(item_prefixes) or header.startswith("("):
                continue
            
            path_parts = header.split("_")
            curr_node = inf_nfe_node
            for part in path_parts:
                curr_node = self._search_tag(curr_node, part)
                if curr_node is None: break
            
            if curr_node is not None:
                header_data[header] = self._safe_text(curr_node)

        # B: Rede de Segurança Dinâmica (Tags Amazon, Mercado Livre, etc -> Vão para o fim do Excel)
        known_tags = {h.split("_")[-1] for h in NFE_HEADERS if not h.startswith("(")}
        known_tags.update({"infNFe", "emit", "dest", "enderEmit", "enderDest", "det", "prod", "imposto", "ICMS", "IPI", "PIS", "COFINS", "total", "ICMSTot", "transp", "cobr", "fat", "dup", "pag", "detPag", "infAdic", "obsCont", "obsFisco", "Signature"})
        
        for child in inf_nfe_node.iter():
            tag = child.tag.split('}')[-1]
            if tag not in known_tags and child.text and child.text.strip():
                header_data[f"Extra_{tag}"] = self._safe_text(child)

        # C: Achatamento dos Itens (Flattening: 1 produto = 1 linha)
        items_data = []
        ns_url = self._ns.get('ns', 'http://www.portalfiscal.inf.br/nfe')
        det_nodes = inf_nfe_node.findall(f".//{{{ns_url}}}det")
        if not det_nodes:
            det_nodes = inf_nfe_node.findall(".//ns:det", self._ns)

        if not det_nodes:
            items_data.append(header_data)
            return items_data

        for det in det_nodes:
            row = header_data.copy()
            row["det_nItem"] = det.get("nItem", "")

            for header in NFE_HEADERS:
                if not header.startswith(item_prefixes) or header == "det_nItem" or header.startswith("("):
                    continue

                if header.startswith(("ICMS_", "IPI_", "PIS_", "COFINS_")):
                    tag_imposto, tag_filho = header.split("_")[0], header.split("_")[1]
                    group_node = det.find(f".//{{{ns_url}}}{tag_imposto}")
                    if group_node is None: group_node = det.find(f".//ns:{tag_imposto}", self._ns)
                    
                    if group_node is not None and len(group_node) > 0:
                        target_node = self._search_tag(group_node[0], tag_filho)
                        if target_node is not None:
                            row[header] = self._safe_text(target_node)
                    continue

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
