# parsers/nfe_event_parser.py

import logging
from typing import Dict, Optional, Any

from shared.base_parser import BaseXMLParser

logger = logging.getLogger(__name__)

# Tabela oficial da SEFAZ para eventos de NF-e
NFE_EVENT_MAP = {
    "110110": "Carta de Correção (CC-e)",
    "110111": "Cancelamento",
    "110112": "Cancelamento por Substituição",
}


class NFeEventParser(BaseXMLParser):
    """Parser especializado em ler XMLs de Eventos de NF-e (Cancelamentos, CC-e)."""

    def __init__(self, root):
        super().__init__(root)
        self._ns = "http://www.portalfiscal.inf.br/nfe"

    def extract_data(self) -> Optional[Dict[str, Any]]:
        """Extrai dados do evento de NF-e.

        Returns:
            None se o XML não contiver <infEvento> no namespace NF-e.
            Dicionário compatível com EVENT_SHEET_HEADERS.
        """
        inf_evento = self.root.find(f".//{{{self._ns}}}infEvento")
        if inf_evento is None:
            return None

        event_data = {
            "Chave de Acesso (Referência)": self._safe_text(
                self._search_tag(inf_evento, "chNFe")
            ),
            "Data do Evento": self._safe_text(
                self._search_tag(inf_evento, "dhEvento")
            ),
        }

        tp = self._safe_text(self._search_tag(inf_evento, "tpEvento"))
        event_data["Tipo de Evento"] = NFE_EVENT_MAP.get(
            tp, f"Outro Evento ({tp})"
        )

        event_data["Detalhes / Justificativa"] = self._extract_detail(inf_evento)

        return event_data

    def _extract_detail(self, inf_evento) -> str:
        """Extrai justificativa ou correção do evento."""
        det = self._search_tag(inf_evento, "detEvento")
        if det is None:
            return ""

        x_correcao = self._search_tag(det, "xCorrecao")
        if x_correcao is not None and x_correcao.text:
            return x_correcao.text.strip()

        x_just = self._search_tag(det, "xJust")
        if x_just is not None and x_just.text:
            return x_just.text.strip()

        return ""
