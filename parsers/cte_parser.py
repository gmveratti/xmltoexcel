# parsers/cte_parser.py

import xml.etree.ElementTree as ET
from typing import Dict
from core.constants import XML_NAMESPACE, EXCEL_HEADERS, SKIP_COLS

# Mapa de ICMS para evitar duplicação brutal de código (Refatoração Nível Sênior)
ICMS_MAP = {
    "ICMSOUTRAUF": {
        "CST": "imp_ICMSOutraUF_CST", "vBCOutraUF": "imp_ICMSOutraUF_vBCOutraUF",
        "pICMSOutraUF": "imp_ICMSOutraUF_pICMSOutraUF", "vICMSOutraUF": "imp_ICMSOutraUF_vICMSOutraUF"
    },
    "ICMS60": {
        "CST": "imp_CST", "vBCSTRet": "imp_vBCSTRet",
        "vICMSSTRet": "imp_vICMSSTRet", "pICMSSTRet": "imp_pICMSSTRet"
    },
    "DEFAULT": {
        "CST": "imp_CST", "vBC": "imp_vBC", "pICMS": "imp_pICMS", "vICMS": "imp_vICMS",
        "vBCSTRet": "imp_vBCSTRet", "vICMSSTRet": "imp_vICMSSTRet", "pICMSSTRet": "imp_pICMSSTRet"
    }
}

class CTeParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.ns = XML_NAMESPACE
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()

    def _safe_text(self, element: ET.Element) -> str:
        """Helper para evitar repetição de .strip() e validação de Nones."""
        return element.text.strip() if element is not None and element.text else ""

    def _search_tag(self, parent_node: ET.Element, target_tag: str) -> ET.Element:
        """Busca hierárquica focada nos filhos."""
        if parent_node is None:
            return None
        target = target_tag.lower()
        for child in parent_node.iter():
            if child.tag.split('}')[-1].lower() == target:
                return child
        return None

    def extract_data(self) -> Dict[str, str]:
        base_data = {header: "" for header in EXCEL_HEADERS}
        inf_cte_node = self.root.find(".//ns:infCte", self.ns)
        if inf_cte_node is None:
            return None

        base_data["chv_cte_Id"] = inf_cte_node.get("Id", "").replace("CTe", "")

        # 1. Busca Estrutural Base
        for header in EXCEL_HEADERS:
            if header.startswith("(") or header in SKIP_COLS:
                continue
            path_parts = header.split("_")
            curr_node = inf_cte_node
            for part in path_parts:
                curr_node = self._search_tag(curr_node, part)
                if curr_node is None:
                    break
            if curr_node is not None:
                base_data[header] = self._safe_text(curr_node)

        # 2. Chaves NF-e
        nfe_keys = [self._safe_text(node) for node in inf_cte_node.findall(".//ns:infNFe/ns:chave", self.ns)]
        base_data["infNFe_chave"] = ", ".join(filter(None, nfe_keys))

        # 3. ICMS usando o ICMS_MAP
        icms_node = self._search_tag(inf_cte_node, "ICMS")
        if icms_node is not None and len(icms_node) > 0:
            grupo_icms = icms_node[0] 
            tag_grupo = grupo_icms.tag.split("}")[-1].upper()
            mapping = ICMS_MAP.get(tag_grupo, ICMS_MAP["DEFAULT"])
            
            for child in grupo_icms:
                c_tag = child.tag.split("}")[-1]
                if c_tag in mapping:
                    base_data[mapping[c_tag]] = self._safe_text(child)

        # 4. Componentes Dinâmicos
        vprest_node = self._search_tag(inf_cte_node, "vPrest")
        if vprest_node is not None:
            comps = [c for c in vprest_node.iter() if c.tag.split('}')[-1].lower() == "comp"]
            for comp in comps:
                nome = self._safe_text(self._search_tag(comp, "xNome"))
                valor = self._safe_text(self._search_tag(comp, "vComp"))
                if nome and valor:
                    nome_coluna = f"comp_{nome.upper().replace(' ', '_')}"
                    base_data[nome_coluna] = valor

        return base_data
