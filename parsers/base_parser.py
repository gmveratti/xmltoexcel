# parsers/base_parser.py

import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BaseXMLParser(ABC):
    """Classe base para parsers de XML fiscal (Otimizada para Velocidade C)."""

    def __init__(self, root: ET.Element):
        # Agora recebe a raiz da árvore em memória, zero acessos ao disco!
        self.root = root

    def _safe_text(self, element) -> str:
        """Extrai texto de um elemento XML com segurança contra None."""
        return element.text.strip() if element is not None and element.text else ""

    def _search_tag(self, parent_node: ET.Element, target_tag: str) -> Optional[ET.Element]:
        """Busca hierárquica ultra-rápida combinando pesquisa linear de filhos e XPath."""
        if parent_node is None:
            return None
            
        target_lower = target_tag.lower()
        
        # 1. Busca Direta de Filhos (O(1) a O(N) filhos, extremamente rápido na memória)
        for child in parent_node:
            if child.tag.split('}')[-1].lower() == target_lower:
                return child
                
        # 2. Busca via XPath (Motor C nativo do ElementTree)
        try:
            res = parent_node.find(f".//{{*}}{target_tag}")
            if res is not None:
                return res
        except SyntaxError:
            pass

        # 3. Fallback de Segurança (Caso o nome da tag esteja muito aninhado e a engine C falhe)
        for child in parent_node.iter():
            if child.tag.split('}')[-1].lower() == target_lower:
                return child
                
        return None

    @abstractmethod
    def extract_data(self) -> Optional[Dict[str, Any]]:
        """Extrai dados do XML. Retorna None se o XML não for do tipo esperado."""
        ...
