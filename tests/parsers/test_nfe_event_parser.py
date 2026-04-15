# tests/parsers/test_nfe_event_parser.py

"""Testes unitários para o NFeEventParser — extração de eventos (Cancelamento, CC-e)."""

import xml.etree.ElementTree as ET
from nfe.nfe_event_parser import NFeEventParser


class TestNFeEventParserStructure:
    """Verifica que o parser identifica corretamente XMLs de evento."""

    def test_returns_none_for_non_event_xml(self, nfe_root: ET.Element):
        """XML de NF-e normal (não evento) → deve retornar None."""
        parser = NFeEventParser(nfe_root)
        result = parser.extract_data()
        assert result is None


class TestNFeEventExtraction:
    """Verifica a extração de dados de eventos específicos."""

    def test_returns_dict_for_valid_cancelamento(self, event_nfe_cancelamento_root: ET.Element):
        """Evento de cancelamento (110111) → extraído corretamente."""
        parser = NFeEventParser(event_nfe_cancelamento_root)
        result = parser.extract_data()

        assert result is not None
        assert result["Tipo de Evento"] == "Cancelamento"
        assert result["Detalhes / Justificativa"] == "Erro de digitacao nos itens"
        assert result["Chave de Acesso (Referência)"] == "35250412345678000195550010000012341000012340"

    def test_returns_dict_for_valid_cce(self, event_nfe_cce_root: ET.Element):
        """Evento de CC-e (110110) → extraído corretamente."""
        parser = NFeEventParser(event_nfe_cce_root)
        result = parser.extract_data()

        assert result is not None
        assert result["Tipo de Evento"] == "Carta de Correção (CC-e)"
        assert "Alteracao do endereco" in result["Detalhes / Justificativa"]

    def test_extracts_access_key(self, event_nfe_cancelamento_root: ET.Element):
        """A chave de acesso do evento deve ser extraída sem erros."""
        parser = NFeEventParser(event_nfe_cancelamento_root)
        result = parser.extract_data()
        assert result["Chave de Acesso (Referência)"] == "35250412345678000195550010000012341000012340"

    def test_extracts_event_datetime(self, event_nfe_cancelamento_root: ET.Element):
        """A data do evento deve ser extraída."""
        parser = NFeEventParser(event_nfe_cancelamento_root)
        result = parser.extract_data()
        assert "2025-04-11" in result["Data do Evento"]

    def test_unknown_event_code_fallback(self):
        """Evento com código desconhecido (999999) → fallback para 'Outro Evento'."""
        xml = """<procEventoNFe xmlns="http://www.portalfiscal.inf.br/nfe">
            <evento>
                <infEvento>
                    <tpEvento>999999</tpEvento>
                    <chNFe>35250412345678000195550010000012341000012340</chNFe>
                    <dhEvento>2025-04-13T10:00:00-03:00</dhEvento>
                </infEvento>
            </evento>
        </procEventoNFe>"""
        parser = NFeEventParser(ET.fromstring(xml))
        result = parser.extract_data()
        assert result["Tipo de Evento"] == "Outro Evento (999999)"
