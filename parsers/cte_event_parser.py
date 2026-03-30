# parsers/cte_event_parser.py

import xml.etree.ElementTree as ET
from typing import Dict, Optional

# Tabela oficial da SEFAZ para eventos de CT-e
EVENT_MAP = {
    "110110": "Carta de Correção (CC-e)",
    "110111": "Cancelamento",
    "110113": "EPEC",
    "610110": "Prestação de Serviço em Desacordo"
}

class CTeEventParser:
    """Parser especializado em ler XMLs de Eventos (Cancelamentos, CC-e, etc)."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()

    def _search_tag(self, parent_node: ET.Element, target_tag: str) -> Optional[ET.Element]:
        if parent_node is None: return None
        target = target_tag.lower()
        for child in parent_node.iter():
            if child.tag.split('}')[-1].lower() == target:
                return child
        return None

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

        cod_evento = tp_evento_node.text.strip() if tp_evento_node is not None and tp_evento_node.text else "Desconhecido"
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
                
                g_txt = grupo.text.strip() if grupo is not None and grupo.text else ""
                c_txt = campo.text.strip() if campo is not None and campo.text else ""
                v_txt = valor.text.strip() if valor is not None and valor.text else ""
                correcoes.append(f"[{g_txt} | {c_txt} -> {v_txt}]")

        if x_just is not None and x_just.text: detalhe = x_just.text.strip()
        elif x_cond_uso is not None and x_cond_uso.text: detalhe = x_cond_uso.text.strip()
        elif correcoes: detalhe = " | ".join(correcoes)

        return {
            "Chave de Acesso (Referência)": chave_node.text.strip() if chave_node is not None and chave_node.text else "",
            "Tipo de Evento": desc_evento,
            "Data do Evento": dh_evento_node.text.strip() if dh_evento_node is not None and dh_evento_node.text else "",
            "Detalhes / Justificativa": detalhe
        }
