# tests/parsers/test_cte_event_parser.py

"""Testes unitários para o CTeEventParser — regras de extração de Eventos CT-e.

Cobre Cancelamentos, Cartas de Correção (CC-e), Prestação em Desacordo,
e códigos desconhecidos para validar o EVENT_MAP e a lógica de detalhes.
"""

import xml.etree.ElementTree as ET

from cte.cte_event_parser import CTeEventParser, EVENT_MAP


# ==================== Validação Estrutural ====================


class TestEventParserStructure:
    """Verifica que XMLs sem <eventoCTe> são rejeitados."""

    def test_returns_none_for_non_event_xml(self, cte_root: ET.Element):
        """Um XML de CT-e normal não deve ser interpretado como evento."""
        parser = CTeEventParser(cte_root)
        result = parser.extract_data()
        assert result is None

    def test_returns_dict_for_valid_event(
        self, event_cancelamento_root: ET.Element
    ):
        """Evento válido deve retornar dicionário com 4 campos."""
        parser = CTeEventParser(event_cancelamento_root)
        result = parser.extract_data()

        assert result is not None
        assert isinstance(result, dict)
        assert len(result) == 4


# ==================== Mapeamento de Tipos de Evento ====================


class TestEventTypeMapping:
    """Verifica que os códigos do SEFAZ são traduzidos corretamente."""

    def test_cancelamento_event_mapping(
        self, event_cancelamento_root: ET.Element
    ):
        """Código 110111 → 'Cancelamento'."""
        parser = CTeEventParser(event_cancelamento_root)
        result = parser.extract_data()
        assert result["Tipo de Evento"] == "Cancelamento"

    def test_cce_event_mapping(self, event_cce_root: ET.Element):
        """Código 110110 → 'Carta de Correção (CC-e)'."""
        parser = CTeEventParser(event_cce_root)
        result = parser.extract_data()
        assert result["Tipo de Evento"] == "Carta de Correção (CC-e)"

    def test_desacordo_event_mapping(
        self, event_desacordo_root: ET.Element
    ):
        """Código 610110 → 'Prestação de Serviço em Desacordo'."""
        parser = CTeEventParser(event_desacordo_root)
        result = parser.extract_data()
        assert result["Tipo de Evento"] == "Prestação de Serviço em Desacordo"

    def test_unknown_event_code_fallback(
        self, event_unknown_code_root: ET.Element
    ):
        """Código 999999 → 'Outro Evento (999999)'."""
        parser = CTeEventParser(event_unknown_code_root)
        result = parser.extract_data()
        assert result["Tipo de Evento"] == "Outro Evento (999999)"

    def test_event_map_contains_all_expected_codes(self):
        """O EVENT_MAP deve conter exatamente os 4 códigos oficiais do SEFAZ."""
        expected_codes = {"110110", "110111", "110113", "610110"}
        assert set(EVENT_MAP.keys()) == expected_codes


# ==================== Extração de Chave e Data ====================


class TestEventKeyAndDateExtraction:
    """Verifica a extração da Chave de Acesso e Data do Evento."""

    def test_extracts_access_key(self, event_cancelamento_root: ET.Element):
        """A chave de acesso referenciada deve ser extraída corretamente."""
        parser = CTeEventParser(event_cancelamento_root)
        result = parser.extract_data()

        expected_key = "35250312345678000195570010000012341000012340"
        assert result["Chave de Acesso (Referência)"] == expected_key

    def test_extracts_event_datetime(
        self, event_cancelamento_root: ET.Element
    ):
        """A data do evento deve ser preservada no formato ISO do XML."""
        parser = CTeEventParser(event_cancelamento_root)
        result = parser.extract_data()
        assert "2025-03-16" in result["Data do Evento"]


# ==================== Extração de Detalhes / Justificativa ====================


class TestEventDetailExtraction:
    """Verifica a extração de justificativas e correções."""

    def test_cancelamento_extracts_xjust(
        self, event_cancelamento_root: ET.Element
    ):
        """Cancelamento com <xJust> deve extraí-lo como detalhe."""
        parser = CTeEventParser(event_cancelamento_root)
        result = parser.extract_data()
        assert result["Detalhes / Justificativa"] == (
            "Erro na emissao do documento fiscal"
        )

    def test_cce_extracts_xconduso_when_present(
        self, event_cce_root: ET.Element
    ):
        """CC-e com <xCondUso> presente deve usá-lo como detalhe (prioridade sobre infCorrecao)."""
        parser = CTeEventParser(event_cce_root)
        result = parser.extract_data()

        detail = result["Detalhes / Justificativa"]
        assert detail == "Uso permitido conforme legislacao vigente"

    def test_desacordo_extracts_xjust(
        self, event_desacordo_root: ET.Element
    ):
        """Desacordo com <xJust> deve extraí-lo."""
        parser = CTeEventParser(event_desacordo_root)
        result = parser.extract_data()
        assert "nao foi prestado" in result["Detalhes / Justificativa"]

    def test_unknown_event_has_empty_detail(
        self, event_unknown_code_root: ET.Element
    ):
        """Evento sem xJust nem infCorrecao deve ter detalhe vazio."""
        parser = CTeEventParser(event_unknown_code_root)
        result = parser.extract_data()
        assert result["Detalhes / Justificativa"] == ""
