import xml.etree.ElementTree as ET
from typing import Dict
from core.constants import XML_NAMESPACE, EXCEL_HEADERS, SKIP_COLS

class CTeParser:
    """
    Parser especializado em CT-e. 
    Implementa criação dinâmica de colunas para componentes e extração de NF-es vinculadas.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.ns = XML_NAMESPACE
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()

    def _search_tag(self, parent_node: ET.Element, target_tag: str) -> ET.Element:
        """Faz a busca ignorando o namespace, varrendo os filhos diretos e descendentes."""
        target = target_tag.lower()
        for child in parent_node.iter():
            if child.tag.split('}')[-1].lower() == target:
                return child
        return None

    def extract_data(self) -> Dict[str, str]:
        """Extrai os dados de um CT-e retornando um único dicionário (1 linha)."""
        base_data = {header: "" for header in EXCEL_HEADERS}
        
        inf_cte_node = self.root.find(".//ns:infCte", self.ns)
        if inf_cte_node is None:
            return base_data

        base_data["chv_cte_Id"] = inf_cte_node.get("Id", "").replace("CTe", "")

        # --- 1. EXTRAÇÃO FUZZY HIERÁRQUICA (De/Para Simples) ---
        for header in EXCEL_HEADERS:
            if header.startswith("(") or header in SKIP_COLS:
                continue
            
            path_parts = header.split("_")
            curr_node = inf_cte_node
            
            for part in path_parts:
                curr_node = self._search_tag(curr_node, part)
                if curr_node is None:
                    break
            
            if curr_node is not None and curr_node.text:
                base_data[header] = curr_node.text.strip()

        # --- 2. EXTRAÇÃO DE CHAVES NF-e (Vinculadas) ---
        nfe_keys = []
        for chave_node in inf_cte_node.findall(".//ns:infNFe/ns:chave", self.ns):
            if chave_node.text:
                nfe_keys.append(chave_node.text.strip())
        base_data["infNFe_chave"] = ", ".join(nfe_keys)

        # --- 3. EXTRAÇÃO DIRETA DE ICMS (Fisco Oficial) ---
        icms_node = self._search_tag(inf_cte_node, "ICMS")
        if icms_node is not None and len(icms_node) > 0:
            grupo_icms = icms_node[0] 
            tag_grupo = grupo_icms.tag.split("}")[-1].upper()

            if tag_grupo == "ICMSOUTRAUF":
                for child in grupo_icms:
                    c_tag = child.tag.split("}")[-1]
                    if c_tag == "CST": base_data["imp_ICMSOutraUF_CST"] = child.text.strip() if child.text else ""
                    elif c_tag == "vBCOutraUF": base_data["imp_ICMSOutraUF_vBCOutraUF"] = child.text.strip() if child.text else ""
                    elif c_tag == "pICMSOutraUF": base_data["imp_ICMSOutraUF_pICMSOutraUF"] = child.text.strip() if child.text else ""
                    elif c_tag == "vICMSOutraUF": base_data["imp_ICMSOutraUF_vICMSOutraUF"] = child.text.strip() if child.text else ""

            elif tag_grupo == "ICMS60":
                for child in grupo_icms:
                    c_tag = child.tag.split("}")[-1]
                    if c_tag == "CST": base_data["imp_CST"] = child.text.strip() if child.text else ""
                    elif c_tag == "vBCSTRet": base_data["imp_vBCSTRet"] = child.text.strip() if child.text else ""
                    elif c_tag == "vICMSSTRet": base_data["imp_vICMSSTRet"] = child.text.strip() if child.text else ""
                    elif c_tag == "pICMSSTRet": base_data["imp_pICMSSTRet"] = child.text.strip() if child.text else ""

            else:
                for child in grupo_icms:
                    c_tag = child.tag.split("}")[-1]
                    if c_tag == "CST": base_data["imp_CST"] = child.text.strip() if child.text else ""
                    elif c_tag == "vBC": base_data["imp_vBC"] = child.text.strip() if child.text else ""
                    elif c_tag == "pICMS": base_data["imp_pICMS"] = child.text.strip() if child.text else ""
                    elif c_tag == "vICMS": base_data["imp_vICMS"] = child.text.strip() if child.text else ""
                    elif c_tag == "vBCSTRet": base_data["imp_vBCSTRet"] = child.text.strip() if child.text else ""
                    elif c_tag == "vICMSSTRet": base_data["imp_vICMSSTRet"] = child.text.strip() if child.text else ""
                    elif c_tag == "pICMSSTRet": base_data["imp_pICMSSTRet"] = child.text.strip() if child.text else ""

        # --- 4. COMPONENTES COMERCIAIS DINÂMICOS (Sem Duplicar Linha) ---
        vprest_node = self._search_tag(inf_cte_node, "vPrest")
        if vprest_node is not None:
            comps = [c for c in vprest_node.iter() if c.tag.split('}')[-1].lower() == "comp"]
            for comp in comps:
                x_nome = self._search_tag(comp, "xNome")
                v_comp = self._search_tag(comp, "vComp")
                
                if x_nome is not None and x_nome.text and v_comp is not None and v_comp.text:
                    # Normaliza o nome do componente para virar nome de coluna (Ex: "VALOR FRETE" -> "comp_VALOR_FRETE")
                    nome_coluna = f"comp_{x_nome.text.strip().upper().replace(' ', '_')}"
                    base_data[nome_coluna] = v_comp.text.strip()

        return base_data
