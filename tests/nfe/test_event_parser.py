# tests/parsers/test_nfe_event_parser.py

"""Testes unitários para o parser de Eventos de NF-e.

Valida Cancelamento, CC-e, e cenários sem <infEvento>.
"""

from nfe.event_parser import NFeEventParser


class TestNFeEventCancelamento:
    """Testa o parser com evento de Cancelamento NF-e (110111)."""

    def test_returns_dict_not_none(self, nfe_event_cancelamento_root):
        """Evento válido deve retornar um dicionário."""
        result = NFeEventParser(nfe_event_cancelamento_root).extract_data()
        assert result is not None
        assert isinstance(result, dict)

    def test_access_key_extracted(self, nfe_event_cancelamento_root):
        """Chave de acesso NF-e extraída do <chNFe>."""
        result = NFeEventParser(nfe_event_cancelamento_root).extract_data()
        assert result["Chave de Acesso (Referência)"] == "35250312345678000195550010000001231000001230"

    def test_event_type_cancelamento(self, nfe_event_cancelamento_root):
        """Código 110111 → 'Cancelamento'."""
        result = NFeEventParser(nfe_event_cancelamento_root).extract_data()
        assert result["Tipo de Evento"] == "Cancelamento"

    def test_event_date_extracted(self, nfe_event_cancelamento_root):
        """Data do evento extraída."""
        result = NFeEventParser(nfe_event_cancelamento_root).extract_data()
        assert result["Data do Evento"] == "2025-03-21T09:00:00-03:00"

    def test_justification_extracted(self, nfe_event_cancelamento_root):
        """Justificativa do cancelamento extraída do <xJust>."""
        result = NFeEventParser(nfe_event_cancelamento_root).extract_data()
        assert result["Detalhes / Justificativa"] == "Erro na emissao da nota fiscal"


class TestNFeEventCCe:
    """Testa o parser com evento de Carta de Correção NF-e (110110)."""

    def test_event_type_cce(self, nfe_event_cce_root):
        """Código 110110 → 'Carta de Correção (CC-e)'."""
        result = NFeEventParser(nfe_event_cce_root).extract_data()
        assert result["Tipo de Evento"] == "Carta de Correção (CC-e)"

    def test_correction_detail_extracted(self, nfe_event_cce_root):
        """Texto da correção extraído do <xCorrecao>."""
        result = NFeEventParser(nfe_event_cce_root).extract_data()
        assert result["Detalhes / Justificativa"] == "Correcao no endereco do destinatario"


class TestNFeEventEdgeCases:
    """Testa cenários de borda para eventos NF-e."""

    def test_no_inf_evento_returns_none(self, nfe_event_no_info_root):
        """XML sem <infEvento> → retorna None."""
        result = NFeEventParser(nfe_event_no_info_root).extract_data()
        assert result is None
