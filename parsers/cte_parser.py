# parsers/cte_parser.py

import re
import logging
from typing import Dict, Optional, Any

import xml.etree.ElementTree as ET

from core.constants import XML_NAMESPACE, EXCEL_HEADERS, SKIP_COLS
from parsers.base_parser import BaseXMLParser

logger = logging.getLogger(__name__)

# Mapa de ICMS para evitar duplicação brutal de código
ICMS_MAP: Dict[str, Dict[str, str]] = {
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

# Roteador Inteligente: Dicionário de sinônimos → coluna canônica.
# Ordem das chaves importa: o lookup é direto (O(1)), sem substring matching.
COMPONENTS_MAP: Dict[str, str] = {
    # ===== Frete Peso =====
    "FRETE PESO":       "comp_FRETE_PESO",
    "FRETE_PESO":       "comp_FRETE_PESO",
    "FRT PESO":         "comp_FRETE_PESO",
    "FRT_PESO":         "comp_FRETE_PESO",
    "FRETEPESO":        "comp_FRETE_PESO",

    # ===== Frete Valor =====
    "FRETE VALOR":      "comp_FRETE_VALOR",
    "FRETE_VALOR":      "comp_FRETE_VALOR",
    "FRT VALOR":        "comp_FRETE_VALOR",
    "FRT_VALOR":        "comp_FRETE_VALOR",
    "FRETEVALOR":       "comp_FRETE_VALOR",
    "FRETE":            "comp_FRETE_VALOR",
    "FRT":              "comp_FRETE_VALOR",

    # ===== Pedágio =====
    "PEDAGIO":          "comp_PEDAGIO",
    "PEDÁGIO":          "comp_PEDAGIO",
    "PEDAGIO REPASSE":  "comp_PEDAGIO",

    # ===== GRIS (Gerenciamento de Risco) =====
    "GRIS":             "comp_GRIS",
    "GERENCIAMENTO DE RISCO":  "comp_GRIS",
    "GERENCIAMENTO_RISCO":     "comp_GRIS",
    "G.R.I.S":          "comp_GRIS",
    "G.R.I.S.":         "comp_GRIS",

    # ===== TAS / Taxa de Administração de Seguro =====
    "TAS":              "comp_TAS",
    "TAXA ADM SEGURO":  "comp_TAS",

    # ===== ADEME / Ad Valorem =====
    "ADEME":            "comp_ADEME",
    "AD VALOREM":       "comp_ADEME",
    "ADVALOREM":        "comp_ADEME",

    # ===== Despacho =====
    "DESPACHO":         "comp_DESPACHO",
    "TAXA DESPACHO":    "comp_DESPACHO",

    # ===== SEC/CAT =====
    "SEC/CAT":          "comp_SEC_CAT",
    "SEC CAT":          "comp_SEC_CAT",
    "SECCAT":           "comp_SEC_CAT",

    # ===== Impostos genéricos =====
    "IMPOSTO":          "comp_IMPOSTOS",
    "IMPOSTOS":         "comp_IMPOSTOS",
    "TRIBUTO":          "comp_IMPOSTOS",
    "TRIBUTOS":         "comp_IMPOSTOS",
}

# Regex para colapsar múltiplos espaços/underscores em um único espaço
_WHITESPACE_RE = re.compile(r"[\s_]+")


def _normalize_component_name(raw_name: str) -> str:
    """Normaliza o texto livre do xNome para lookup no COMPONENTS_MAP."""
    return _WHITESPACE_RE.sub(" ", raw_name.strip()).upper()


def _resolve_component_column(raw_name: str) -> str:
    """Roteia o xNome para a coluna canônica via COMPONENTS_MAP.
    
    Fallback dinâmico: se não encontrar no mapa, gera comp_{NOME_NORMALIZADO}
    substituindo espaços por underscores.
    """
    normalized = _normalize_component_name(raw_name)
    column = COMPONENTS_MAP.get(normalized)
    if column:
        return column

    # Fallback dinâmico — garante que nenhum dado é descartado
    safe_name = normalized.replace(" ", "_")
    return f"comp_{safe_name}"


class CTeParser(BaseXMLParser):
    """Parser especializado em ler XMLs de CT-e (Conhecimento de Transporte Eletrônico)."""

    def __init__(self, root: ET.Element):
        super().__init__(root)
        self.ns = XML_NAMESPACE

    def extract_data(self) -> Optional[Dict[str, Any]]:
        base_data: Dict[str, str] = {header: "" for header in EXCEL_HEADERS}
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

        # 4. Componentes Dinâmicos (Roteador Inteligente + Soma Acumulativa Segura)
        self._extract_dynamic_components(inf_cte_node, base_data)

        return base_data

    def _extract_dynamic_components(self, inf_cte_node: ET.Element,
                                     base_data: Dict[str, Any]) -> None:
        """Extrai componentes de vPrest usando o COMPONENTS_MAP para roteamento preciso."""
        vprest_node = self._search_tag(inf_cte_node, "vPrest")
        if vprest_node is None:
            return

        comps = [c for c in vprest_node.iter() if c.tag.split('}')[-1].lower() == "comp"]
        for comp in comps:
            nome = self._safe_text(self._search_tag(comp, "xNome"))
            valor = self._safe_text(self._search_tag(comp, "vComp"))

            if not nome or not valor:
                continue

            nome_coluna = _resolve_component_column(nome)

            existing_value = base_data.get(nome_coluna)
            if existing_value:
                # Soma acumulativa segura: se a conversão falhar, PRESERVA o valor anterior
                try:
                    accumulated = float(existing_value) + float(valor)
                    base_data[nome_coluna] = str(accumulated)
                except ValueError:
                    # Ignora o valor inválido, mantém o que já havia sido acumulado
                    logger.warning(
                        "Valor não-numérico ignorado em comp '%s': '%s' (preservando: '%s')",
                        nome, valor, existing_value
                    )
            else:
                base_data[nome_coluna] = valor
