# parsers/nfe_parser.py

import re
import logging
from typing import Dict, List, Optional, Any

import xml.etree.ElementTree as ET

from core.constants import NFE_HEADERS
from parsers.base_parser import BaseXMLParser

logger = logging.getLogger(__name__)

# Regex para extrair o Pedido Amazon do campo infCpl (texto livre)
_PEDIDO_AMAZON_RE = re.compile(r"Numero do pedido da compra:\s*([\d-]+)", re.IGNORECASE)


class NFeParser(BaseXMLParser):
    """Parser especializado em ler XMLs de NF-e v4.00.

    Implementa o padrão de Flattening: o cabeçalho (emitente, destinatário,
    totais) é replicado para cada item (<det>) da nota, gerando 1 linha
    no Excel por produto.
    """

    def __init__(self, root: ET.Element):
        super().__init__(root)
        self._ns = "http://www.portalfiscal.inf.br/nfe"

    def extract_data(self) -> Optional[List[Dict[str, Any]]]:
        """Extrai dados da NF-e. Retorna uma lista de dicts (1 por item/produto).

        Returns:
            None se o XML não contiver <infNFe>.
            Lista de dicionários com dados achatados (header + produto).
        """
        inf_nfe_node = self.root.find(f".//{{{self._ns}}}infNFe")
        if inf_nfe_node is None:
            return None

        header = self._extract_header(inf_nfe_node)
        return self._extract_items(inf_nfe_node, header)

    def _extract_header(self, inf_nfe_node: ET.Element) -> Dict[str, str]:
        """Extrai os dados comuns da nota (identificação, emitente, destinatário, totais)."""
        header: Dict[str, str] = {h: "" for h in NFE_HEADERS}
        header["chv_nfe_Id"] = inf_nfe_node.get("Id", "").replace("NFe", "")

        self._extract_ide(inf_nfe_node, header)
        self._extract_emit(inf_nfe_node, header)
        self._extract_dest(inf_nfe_node, header)
        self._extract_totals(inf_nfe_node, header)
        self._extract_inf_adic(inf_nfe_node, header)

        return header

    def _extract_ide(self, inf_nfe_node: ET.Element, header: Dict[str, str]) -> None:
        """Extrai dados de identificação da NF-e (<ide>)."""
        ide = self._search_tag(inf_nfe_node, "ide")
        if ide is None:
            return

        header["ide_natOp"] = self._safe_text(self._search_tag(ide, "natOp"))
        header["ide_nNF"] = self._safe_text(self._search_tag(ide, "nNF"))
        header["ide_dhEmi"] = self._safe_text(self._search_tag(ide, "dhEmi"))
        header["ide_tpNF"] = self._safe_text(self._search_tag(ide, "tpNF"))

        # NFe referenciada pode estar dentro de <NFref>
        ref_nfe = self._search_tag(inf_nfe_node, "refNFe")
        header["ide_NFref"] = self._safe_text(ref_nfe)

    def _extract_emit(self, inf_nfe_node: ET.Element, header: Dict[str, str]) -> None:
        """Extrai dados do emitente (<emit>)."""
        emit = self._search_tag(inf_nfe_node, "emit")
        if emit is None:
            return

        header["emit_CNPJ"] = self._safe_text(self._search_tag(emit, "CNPJ"))
        header["emit_xNome"] = self._safe_text(self._search_tag(emit, "xNome"))

    def _extract_dest(self, inf_nfe_node: ET.Element, header: Dict[str, str]) -> None:
        """Extrai dados do destinatário (<dest>), aceitando tanto CNPJ quanto CPF."""
        dest = self._search_tag(inf_nfe_node, "dest")
        if dest is None:
            return

        cnpj = self._search_tag(dest, "CNPJ")
        cpf = self._search_tag(dest, "CPF")
        header["dest_Doc"] = self._safe_text(cnpj) if cnpj is not None else self._safe_text(cpf)
        header["dest_xNome"] = self._safe_text(self._search_tag(dest, "xNome"))

        ender_dest = self._search_tag(dest, "enderDest")
        if ender_dest is not None:
            header["dest_UF"] = self._safe_text(self._search_tag(ender_dest, "UF"))
            header["dest_xMun"] = self._safe_text(self._search_tag(ender_dest, "xMun"))

    def _extract_totals(self, inf_nfe_node: ET.Element, header: Dict[str, str]) -> None:
        """Extrai os totais do ICMSTot."""
        total = self._search_tag(inf_nfe_node, "ICMSTot")
        if total is None:
            return

        header["tot_vBC"] = self._safe_text(self._search_tag(total, "vBC"))
        header["tot_vICMS"] = self._safe_text(self._search_tag(total, "vICMS"))
        header["tot_vProd"] = self._safe_text(self._search_tag(total, "vProd"))
        header["tot_vFrete"] = self._safe_text(self._search_tag(total, "vFrete"))
        header["tot_vNF"] = self._safe_text(self._search_tag(total, "vNF"))

    def _extract_inf_adic(self, inf_nfe_node: ET.Element, header: Dict[str, str]) -> None:
        """Extrai informações adicionais e tenta capturar o Pedido Amazon via regex."""
        inf_adic = self._search_tag(inf_nfe_node, "infAdic")
        if inf_adic is None:
            return

        inf_cpl = self._safe_text(self._search_tag(inf_adic, "infCpl"))
        header["infAdic_infCpl"] = inf_cpl

        match = _PEDIDO_AMAZON_RE.search(inf_cpl)
        header["ext_Pedido_Amazon"] = match.group(1) if match else ""

    def _extract_items(self, inf_nfe_node: ET.Element,
                       header: Dict[str, str]) -> List[Dict[str, Any]]:
        """Achata os itens: replica o header para cada <det> encontrado."""
        items_data: List[Dict[str, Any]] = []
        det_nodes = inf_nfe_node.findall(f".//{{{self._ns}}}det")

        if not det_nodes:
            # NF-e sem itens — retorna o cabeçalho puro
            items_data.append(header)
            return items_data

        for det in det_nodes:
            row = header.copy()
            row["nItem"] = det.get("nItem", "")

            self._extract_product(det, row)
            self._extract_item_icms(det, row)

            items_data.append(row)

        return items_data

    def _extract_product(self, det: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai dados do produto (<prod>) de um item."""
        prod = self._search_tag(det, "prod")
        if prod is None:
            return

        row["prod_cProd"] = self._safe_text(self._search_tag(prod, "cProd"))
        row["prod_cEAN"] = self._safe_text(self._search_tag(prod, "cEAN"))
        row["prod_xProd"] = self._safe_text(self._search_tag(prod, "xProd"))
        row["prod_NCM"] = self._safe_text(self._search_tag(prod, "NCM"))
        row["prod_CFOP"] = self._safe_text(self._search_tag(prod, "CFOP"))
        row["prod_qCom"] = self._safe_text(self._search_tag(prod, "qCom"))
        row["prod_vUnCom"] = self._safe_text(self._search_tag(prod, "vUnCom"))
        row["prod_vProd"] = self._safe_text(self._search_tag(prod, "vProd"))

    def _extract_item_icms(self, det: ET.Element, row: Dict[str, Any]) -> None:
        """Extrai vICMS do imposto a nível do item."""
        imposto = self._search_tag(det, "imposto")
        if imposto is None:
            return

        v_icms = imposto.find(f".//{{{self._ns}}}vICMS")
        row["prod_vICMS"] = self._safe_text(v_icms) if v_icms is not None else ""
