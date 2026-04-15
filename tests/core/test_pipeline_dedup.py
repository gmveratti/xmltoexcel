# tests/core/test_pipeline_dedup.py

"""Testes unitários para a lógica de deduplicação via Strategy Pattern.

Validamos que as estratégias implementam corretamente a lógica de
deduplicação de chaves (Id puro no CTe, Id + nItem no NFe).
"""

from core.models import DataType
from cte.cte_strategy import CTeStrategy
from nfe.nfe_strategy import NFeStrategy


class TestCteStrategyDeduplication:
    """Valida a lógica de deduplicação na CTeStrategy."""

    def test_duplicate_cte_key_is_skipped(self):
        """A segunda ocorrência de uma chave idêntica deve ser descartada."""
        strategy = CTeStrategy()
        seen_main_keys: set = set()
        all_main_data = []
        all_event_data = []
        seen_event_keys: set = set()

        entries = [
            {"chv_cte_Id": "35250312345678000195570010000012341000012340", "ide_nCT": "1234"},
            {"chv_cte_Id": "35250312345678000195570010000012341000012340", "ide_nCT": "1234"},  # Duplicada
        ]

        dup_count = 0
        for data in entries:
            dup_count += strategy.process_result_data(
                data, DataType.CTE, all_main_data, all_event_data, 
                seen_main_keys, seen_event_keys
            )

        assert len(all_main_data) == 1
        assert dup_count == 1
        assert "35250312345678000195570010000012341000012340" in seen_main_keys

    def test_empty_cte_key_is_always_added(self):
        """Chave vazia não deve entrar no set de vistos, mas o dado é adicionado."""
        strategy = CTeStrategy()
        seen_main_keys: set = set()
        all_main_data = []
        all_event_data = []
        seen_event_keys: set = set()

        entries = [
            {"chv_cte_Id": "", "ide_nCT": "0001"},
            {"chv_cte_Id": "", "ide_nCT": "0002"},
        ]

        for data in entries:
            strategy.process_result_data(
                data, DataType.CTE, all_main_data, all_event_data, 
                seen_main_keys, seen_event_keys
            )

        assert len(all_main_data) == 2
        assert len(seen_main_keys) == 0


class TestNfeStrategyDeduplication:
    """Valida a lógica de deduplicação na NFeStrategy (por item)."""

    def test_duplicate_nfe_item_is_skipped(self):
        """Mesmo Id com mesmo nItem deve ser descartado."""
        strategy = NFeStrategy()
        seen_main_keys: set = set()
        all_main_data = []
        all_event_data = []
        seen_event_keys: set = set()

        # NFe Parser retorna uma lista de dicionários
        entries = [
            [{"chv_nfe_Id": "NFe123", "nItem_nItem": "1"}],
            [{"chv_nfe_Id": "NFe123", "nItem_nItem": "1"}], # Duplicado
        ]

        dup_count = 0
        for data in entries:
            dup_count += strategy.process_result_data(
                data, DataType.NFE, all_main_data, all_event_data, 
                seen_main_keys, seen_event_keys
            )

        assert len(all_main_data) == 1
        assert dup_count == 1

    def test_different_items_same_nfe_are_kept(self):
        """Mesmo Id com nItems diferentes → OK."""
        strategy = NFeStrategy()
        seen_main_keys: set = set()
        all_main_data = []
        all_event_data = []
        seen_event_keys: set = set()

        entries = [
            [{"chv_nfe_Id": "NFe123", "nItem_nItem": "1"}, 
             {"chv_nfe_Id": "NFe123", "nItem_nItem": "2"}]
        ]

        dup_count = 0
        for data in entries:
            dup_count += strategy.process_result_data(
                data, DataType.NFE, all_main_data, all_event_data, 
                seen_main_keys, seen_event_keys
            )

        assert len(all_main_data) == 2
        assert dup_count == 0
        assert len(seen_main_keys) == 2


class TestEventDeduplicationViaStrategy:
    """Valida que ambas as estratégias deduplicam eventos da mesma forma."""

    def test_event_deduplication(self):
        for strategy in [CTeStrategy(), NFeStrategy()]:
            seen_main_keys: set = set()
            all_main_data = []
            all_event_data = []
            seen_event_keys: set = set()

            data = {
                "Chave de Acesso (Referência)": "KEY123",
                "Tipo de Evento": "Cancelamento",
                "Data do Evento": "2025",
                "Detalhes / Justificativa": "Motivo"
            }

            # Primeira vez
            d1 = strategy.process_result_data(data, DataType.EVENT, all_main_data, 
                                              all_event_data, seen_main_keys, seen_event_keys)
            # Segunda vez
            d2 = strategy.process_result_data(data, DataType.EVENT, all_main_data, 
                                              all_event_data, seen_main_keys, seen_event_keys)

            assert len(all_event_data) == 1
            assert d1 == 0
            assert d2 == 1
            assert len(seen_event_keys) == 1
