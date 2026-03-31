# parsers/base_parser.py

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import defusedxml.ElementTree as ET

logger = logging.getLogger(__name__)


class BaseXMLParser(ABC):
    """Classe base para parsers de XML fiscal com proteção contra ataques XML."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()

    def _safe_text(self, element) -> str:
        """Extrai texto de um elemento XML com segurança contra None."""
        return element.text.strip() if element is not None and element.text else ""

    def _search_tag(self, parent_node, target_tag: str):
        """Busca hierárquica por tag ignorando namespace."""
        if parent_node is None:
            return None
        target = target_tag.lower()
        for child in parent_node.iter():
            if child.tag.split('}')[-1].lower() == target:
                return child
        return None

    @abstractmethod
    def extract_data(self) -> Optional[Dict[str, Any]]:
        """Extrai dados do XML. Retorna None se o XML não for do tipo esperado."""
        ...
