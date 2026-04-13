# parsers/cte_event_parser.py

import logging
from typing import Dict, Optional

from shared.base_parser import BaseXMLParser

logger = logging.getLogger(__name__)

# Tabela oficial da SEFAZ para eventos de CT-e
EVENT_MAP = {
    "110110": "Carta de Correção (CC-e)",
    "110111": "Cancelamento",
    "110113": "EPEC",
    "610110": "Prestação de Serviço em Desacordo"
}


class CTeEventParser(BaseXMLParser):
    """Parser especializado em ler XMLs de Eventos (Cancelamentos, CC-e, etc)."""

    def extract_data(self) -> Optional[Dict[str, str]]:
        # 1. Verifica se realmente é um XML de evento
        evento_node = self._search_tag(self.root, "eventoCTe")
        if evento_node is None:
            return None

        inf_evento = self._search_tag(evento_node, "infEvento")
        if inf_evento is None:
            return None

        # 2. Extrai os dados básicos do evento
        chave_node = self._search_tag(inf_evento, "chCTe")
        tp_evento_node = self._search_tag(inf_evento, "tpEvento")
        dh_evento_node = self._search_tag(inf_evento, "dhEvento")

        cod_evento = self._safe_text(tp_evento_node) or "Desconhecido"
        desc_evento = EVENT_MAP.get(cod_evento, f"Outro Evento ({cod_evento})")

        # 3. Extrai a Justificativa ou Detalhe da Correção
        detalhe = ""
        x_just = self._search_tag(inf_evento, "xJust")
        x_cond_uso = self._search_tag(inf_evento, "xCondUso")

        # Para Carta de Correção (CC-e), a SEFAZ separa os dados em sub-tags
        correcoes = []
        for corr in inf_evento.iter():
            if corr.tag.split('}')[-1].lower() == 'infcorrecao':
                grupo = self._search_tag(corr, "grupoAlterado")
                campo = self._search_tag(corr, "campoAlterado")
                valor = self._search_tag(corr, "valorAlterado")

                g_txt = self._safe_text(grupo)
                c_txt = self._safe_text(campo)
                v_txt = self._safe_text(valor)
                correcoes.append(f"[{g_txt} | {c_txt} -> {v_txt}]")

        if x_just is not None and x_just.text:
            detalhe = x_just.text.strip()
        elif x_cond_uso is not None and x_cond_uso.text:
            detalhe = x_cond_uso.text.strip()
        elif correcoes:
            detalhe = " | ".join(correcoes)

        return {
            "Chave de Acesso (Referência)": self._safe_text(chave_node),
            "Tipo de Evento": desc_evento,
            "Data do Evento": self._safe_text(dh_evento_node),
            "Detalhes / Justificativa": detalhe
        }
