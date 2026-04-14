# nfe/nfe_event_parser.py

import logging
from typing import Dict, Optional

from parsers.base_parser import BaseXMLParser

logger = logging.getLogger(__name__)

EVENT_MAP = {
    "110110": "Carta de Correção (CC-e)",
    "110111": "Cancelamento"
}

class NFeEventParser(BaseXMLParser):
    """Parser especializado em ler XMLs de Eventos (Cancelamentos, CC-e) de NF-e."""

    def extract_data(self) -> Optional[Dict[str, str]]:
        # 1. Verifica se realmente é um XML de evento de NF-e
        evento_node = self._search_tag(self.root, "evento")
        if evento_node is None:
            # Tenta verificar se a raiz já é o próprio evento
            if "evento" in self.root.tag.lower():
                evento_node = self.root
            else:
                return None

        inf_evento = self._search_tag(evento_node, "infEvento")
        if inf_evento is None:
            return None

        # 2. Extrai os dados básicos do evento
        chave_node = self._search_tag(inf_evento, "chNFe")
        tp_evento_node = self._search_tag(inf_evento, "tpEvento")
        dh_evento_node = self._search_tag(inf_evento, "dhEvento")

        cod_evento = self._safe_text(tp_evento_node) or "Desconhecido"
        desc_evento = EVENT_MAP.get(cod_evento, f"Outro Evento ({cod_evento})")

        # 3. Extrai a Justificativa ou Detalhe da Correção
        detalhe = ""
        x_just = self._search_tag(inf_evento, "xJust")
        x_correcao = self._search_tag(inf_evento, "xCorrecao")
        x_cond_uso = self._search_tag(inf_evento, "xCondUso")

        if x_just is not None and x_just.text:
            detalhe = x_just.text.strip()
        elif x_correcao is not None and x_correcao.text:
            detalhe = x_correcao.text.strip()
            # Pode haver xCondUso junto com a correção
            if x_cond_uso is not None and x_cond_uso.text:
                detalhe += f" | {x_cond_uso.text.strip()}"
        elif x_cond_uso is not None and x_cond_uso.text:
            detalhe = x_cond_uso.text.strip()

        # Valida que as tags existem antes de classificar como concluído
        chave = self._safe_text(chave_node)
        if not chave:
            return None

        return {
            "Chave de Acesso (Referência)": chave,
            "Tipo de Evento": desc_evento,
            "Data do Evento": self._safe_text(dh_evento_node),
            "Detalhes / Justificativa": detalhe
        }
