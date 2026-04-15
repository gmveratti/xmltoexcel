# nfe/nfe_parser.py
#
# Parser especializado em NF-e (Nota Fiscal Eletrônica / DANFE).
# Implementa a relação 1→N: 1 XML gera N linhas (uma por produto).
# Completamente isolado do parser CT-e.

import copy
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

from core.parsers.base_parser import BaseXMLParser
from core.constants import SKIP_COLS
from nfe.nfe_constants import NFE_NAMESPACE, NFE_HEADERS, NFE_GRAY_COLS

logger = logging.getLogger(__name__)

# Namespace dict para o motor XPath do ElementTree
_NS = {"ns": NFE_NAMESPACE}


class NFeParser(BaseXMLParser):
    """Parser de NF-e. Retorna uma lista de dicionários (1 por item/produto)."""

    def __init__(self, root: ET.Element):
        super().__init__(root)

    def extract_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Extrai dados da NF-e aplicando flatten por produto via loop genérico.

        Returns:
            Lista de dicts (um por <det>), ou None se o XML não for NF-e.
        """
        inf_nfe = self.root.find(".//ns:infNFe", _NS)
        if inf_nfe is None:
            return None

        # Extrai chave de acesso removendo o prefixo "NFe"
        chave = inf_nfe.get("Id", "").replace("NFe", "")

        # 2. Monta o dicionário base com os dados gerais da nota (replicados em cada linha)
        base_data = self._extract_base_data(inf_nfe, chave)

        # 3. Itera sobre os produtos (det) para gerar uma linha por item
        det_nodes = inf_nfe.findall("ns:det", _NS)
        if not det_nodes:
            # Nota sem itens: retorna uma única linha com os dados gerais
            logger.warning("NF-e sem <det> encontrada: chave=%s", chave)
            return [base_data]

        results: List[Dict[str, Any]] = []
        for det_node in det_nodes:
            row = copy.deepcopy(base_data)
            self._extract_item_data(det_node, row)
            results.append(row)

        return results

    # ------------------------------------------------------------------
    # Extração dos dados gerais (cabeçalho da nota — replicados por linha)
    # ------------------------------------------------------------------

    def _extract_base_data(self, inf_nfe: ET.Element, chave: str) -> Dict[str, Any]:
        """Extrai os campos que se repetem em todas as linhas de produto via loop genérico."""
        data: Dict[str, Any] = {header: "" for header in NFE_HEADERS}
        data["chv_nfe_Id"] = chave

        for header in NFE_HEADERS:
            if header in NFE_GRAY_COLS or header in SKIP_COLS:
                continue

            # Ao chegar em dados de itens, paramos a extração de base_data
            if header == "NFeITEM":
                break

            path_parts = header.split("_")
            curr_node = inf_nfe
            for part in path_parts:
                curr_node = self._search_tag(curr_node, part)
                if curr_node is None:
                    break
            if curr_node is not None:
                data[header] = self._safe_text(curr_node)

        return data

    # ------------------------------------------------------------------
    # Extração dos dados específicos de cada item (det)
    # ------------------------------------------------------------------

    def _extract_item_data(self, det: ET.Element, row: Dict[str, Any]) -> None:
        """Preenche os campos de produto e impostos para um <det> específico."""
        row["nItem_nItem"] = det.get("nItem", "")

        self._extract_prod(det, row)
        self._extract_imposto(det, row)

        # infAdProd fica dentro do <det>, não dentro de <prod>
        inf_ad_prod = det.find("ns:infAdProd", _NS)
        row["infAdProd"] = self._safe_text(inf_ad_prod)

    def _extract_prod(self, det: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai bloco <prod> — Produto."""
        row["prod"] = ""
        prod = det.find("ns:prod", _NS)
        if prod is None:
            for field in ("cProd", "cEAN", "xProd", "NCM", "CEST", "CFOP",
                          "uCom", "qCom", "vUnCom", "vProd", "cEANTrib",
                          "uTrib", "qTrib", "vUnTrib", "indTot"):
                row[f"prod_{field}"] = ""
            return

        for field in ("cProd", "cEAN", "xProd", "NCM", "CEST", "CFOP",
                      "uCom", "qCom", "vUnCom", "vProd", "cEANTrib",
                      "uTrib", "qTrib", "vUnTrib", "indTot"):
            node = prod.find(f"ns:{field}", _NS)
            row[f"prod_{field}"] = self._safe_text(node)

    def _extract_imposto(self, det: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai bloco <imposto> — Impostos do item."""
        row["imposto"] = ""
        imposto = det.find("ns:imposto", _NS)
        if imposto is None:
            self._fill_imposto_empty(row)
            return

        # vTotTrib (direto dentro de <imposto>)
        node = imposto.find("ns:vTotTrib", _NS)
        row["imposto_vTotTrib"] = self._safe_text(node)

        self._extract_icms(imposto, row)
        self._extract_ipi(imposto, row)
        self._extract_pis(imposto, row)
        self._extract_cofins(imposto, row)
        self._extract_icms_uf_dest(imposto, row)

    def _extract_icms(self, imposto: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai <ICMS> — busca o primeiro grupo ICMS filho independente do regime."""
        row["imposto_ICMS"] = ""
        icms_wrap = imposto.find("ns:ICMS", _NS)
        _FIELDS = ("orig", "CST", "modBC", "vBC", "pICMS", "vICMS")

        if icms_wrap is None or len(icms_wrap) == 0:
            for f in _FIELDS:
                row[f"imposto_ICMS_{f}"] = ""
            return

        # O primeiro filho é o grupo ICMS concreto (ex: ICMS00, ICMS20, ICMS60...)
        grupo = icms_wrap[0]
        for field in _FIELDS:
            node = grupo.find(f"ns:{field}", _NS)
            row[f"imposto_ICMS_{field}"] = self._safe_text(node)

    def _extract_ipi(self, imposto: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai <IPI> — busca dentro do grupo IPITrib ou IPINt."""
        row["imposto_IPI"] = ""
        ipi = imposto.find("ns:IPI", _NS)
        _FIELDS = ("cEnq", "CST", "vBC", "pIPI", "vIPI")

        if ipi is None:
            for f in _FIELDS:
                row[f"imposto_IPI_{f}"] = ""
            return

        node = ipi.find("ns:cEnq", _NS)
        row["imposto_IPI_cEnq"] = self._safe_text(node)

        # O grupo concreto pode ser IPITrib ou IPINt
        grupo = ipi.find("ns:IPITrib", _NS) or ipi.find("ns:IPINt", _NS)
        if grupo is not None:
            for field in ("CST", "vBC", "pIPI", "vIPI"):
                node = grupo.find(f"ns:{field}", _NS)
                row[f"imposto_IPI_{field}"] = self._safe_text(node)
        else:
            for field in ("CST", "vBC", "pIPI", "vIPI"):
                row[f"imposto_IPI_{field}"] = ""

    def _extract_pis(self, imposto: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai <PIS> — busca dentro do grupo concreto (PISAliq, PISOutr…)."""
        row["imposto_PIS"] = ""
        pis = imposto.find("ns:PIS", _NS)
        _FIELDS = ("CST", "vBC", "pPIS", "vPIS")

        if pis is None or len(pis) == 0:
            for f in _FIELDS:
                row[f"imposto_PIS_{f}"] = ""
            return

        grupo = pis[0]
        for field in _FIELDS:
            node = grupo.find(f"ns:{field}", _NS)
            row[f"imposto_PIS_{field}"] = self._safe_text(node)

    def _extract_cofins(self, imposto: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai <COFINS> — busca dentro do grupo concreto."""
        row["imposto_COFINS"] = ""
        cofins = imposto.find("ns:COFINS", _NS)
        _FIELDS = ("CST", "vBC", "pCOFINS", "vCOFINS")

        if cofins is None or len(cofins) == 0:
            for f in _FIELDS:
                row[f"imposto_COFINS_{f}"] = ""
            return

        grupo = cofins[0]
        for field in _FIELDS:
            node = grupo.find(f"ns:{field}", _NS)
            row[f"imposto_COFINS_{field}"] = self._safe_text(node)

    def _extract_icms_uf_dest(self, imposto: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai <ICMSUFDest> — DIFAL."""
        row["imposto_ICMSUFDest"] = ""
        _FIELDS = (
            "vBCUFDest", "vBCFCPUFDest", "pFCPUFDest", "pICMSUFDest",
            "pICMSInter", "pICMSInterPart", "vFCPUFDest",
            "vICMSUFDest", "vICMSUFRemet",
        )
        uf_dest = imposto.find("ns:ICMSUFDest", _NS)
        if uf_dest is None:
            for f in _FIELDS:
                row[f"imposto_ICMSUFDest_{f}"] = ""
            return

        for field in _FIELDS:
            node = uf_dest.find(f"ns:{field}", _NS)
            row[f"imposto_ICMSUFDest_{field}"] = self._safe_text(node)

    def _fill_imposto_empty(self, row: Dict[str, Any]) -> None:
        """Preenche todos os campos de imposto com vazio quando <imposto> ausente."""
        _KEYS = [
            "imposto_vTotTrib",
            "imposto_ICMS", "imposto_ICMS_orig", "imposto_ICMS_CST",
            "imposto_ICMS_modBC", "imposto_ICMS_vBC", "imposto_ICMS_pICMS", "imposto_ICMS_vICMS",
            "imposto_IPI", "imposto_IPI_cEnq", "imposto_IPI_CST",
            "imposto_IPI_vBC", "imposto_IPI_pIPI", "imposto_IPI_vIPI",
            "imposto_PIS", "imposto_PIS_CST", "imposto_PIS_vBC",
            "imposto_PIS_pPIS", "imposto_PIS_vPIS",
            "imposto_COFINS", "imposto_COFINS_CST", "imposto_COFINS_vBC",
            "imposto_COFINS_pCOFINS", "imposto_COFINS_vCOFINS",
            "imposto_ICMSUFDest", "imposto_ICMSUFDest_vBCUFDest",
            "imposto_ICMSUFDest_vBCFCPUFDest",
            "imposto_ICMSUFDest_pFCPUFDest", "imposto_ICMSUFDest_pICMSUFDest",
            "imposto_ICMSUFDest_pICMSInter", "imposto_ICMSUFDest_pICMSInterPart",
            "imposto_ICMSUFDest_vFCPUFDest", "imposto_ICMSUFDest_vICMSUFDest",
            "imposto_ICMSUFDest_vICMSUFRemet",
        ]
        for key in _KEYS:
            row[key] = ""
