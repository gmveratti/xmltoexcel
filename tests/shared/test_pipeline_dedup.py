# tests/core/test_pipeline_dedup.py

"""Testes unitários para a lógica de deduplicação do pipeline.

A lógica é testada em isolamento sem rodar o ProcessPoolExecutor —
validamos apenas o algoritmo de sets que decide se uma nota é duplicata.
"""

from shared.models import DataType


class TestCteDeduplication:
    """Simula a lógica de deduplicação de CT-e (baseada em chv_cte_Id)."""

    def test_duplicate_cte_key_is_skipped(self):
        """A segunda ocorrência de uma chave idêntica deve ser descartada."""
        seen_keys: set = set()
        all_cte_data = []
        duplicate_count = 0

        entries = [
            {"chv_cte_Id": "35250312345678000195570010000012341000012340", "ide_nCT": "1234"},
            {"chv_cte_Id": "35250312345678000195570010000012341000012340", "ide_nCT": "1234"},  # Duplicada
            {"chv_cte_Id": "33250399887766000155570010000044441000044440", "ide_nCT": "4444"},
        ]

        for data in entries:
            cte_key = data.get("chv_cte_Id", "")
            if cte_key and cte_key in seen_keys:
                duplicate_count += 1
            else:
                if cte_key:
                    seen_keys.add(cte_key)
                all_cte_data.append(data)

        assert len(all_cte_data) == 2
        assert duplicate_count == 1

    def test_empty_cte_key_is_always_added(self):
        """Chave vazia não deve entrar no set de vistos, mas o dado é adicionado."""
        seen_keys: set = set()
        all_cte_data = []

        entries = [
            {"chv_cte_Id": "", "ide_nCT": "0001"},
            {"chv_cte_Id": "", "ide_nCT": "0002"},
        ]

        for data in entries:
            cte_key = data.get("chv_cte_Id", "")
            if cte_key and cte_key in seen_keys:
                pass  # skip duplicate
            else:
                if cte_key:
                    seen_keys.add(cte_key)
                all_cte_data.append(data)

        # Ambas devem ser adicionadas pois chave vazia não é rastreada
        assert len(all_cte_data) == 2
        assert len(seen_keys) == 0

    def test_three_unique_keys_all_kept(self):
        """Três chaves distintas devem resultar em três registros."""
        seen_keys: set = set()
        all_cte_data = []

        entries = [
            {"chv_cte_Id": "11111111111111111111111111111111111111111111"},
            {"chv_cte_Id": "22222222222222222222222222222222222222222222"},
            {"chv_cte_Id": "33333333333333333333333333333333333333333333"},
        ]

        for data in entries:
            cte_key = data.get("chv_cte_Id", "")
            if cte_key and cte_key in seen_keys:
                pass
            else:
                if cte_key:
                    seen_keys.add(cte_key)
                all_cte_data.append(data)

        assert len(all_cte_data) == 3
        assert len(seen_keys) == 3


class TestEventDeduplication:
    """Simula a lógica de deduplicação de Eventos (baseada em tupla composta)."""

    def test_duplicate_event_tuple_is_skipped(self):
        """Evento com a mesma (chave, tipo, data, detalhe) → descartado."""
        seen_event_keys: set = set()
        all_event_data = []
        duplicate_count = 0

        entries = [
            {
                "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
                "Tipo de Evento": "Cancelamento",
                "Data do Evento": "2025-03-16T14:00:00-03:00",
                "Detalhes / Justificativa": "Erro na emissao",
            },
            {
                "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
                "Tipo de Evento": "Cancelamento",
                "Data do Evento": "2025-03-16T14:00:00-03:00",
                "Detalhes / Justificativa": "Erro na emissao",
            },
        ]

        for data in entries:
            event_key = (
                data.get("Chave de Acesso (Referência)", ""),
                data.get("Tipo de Evento", ""),
                data.get("Data do Evento", ""),
                data.get("Detalhes / Justificativa", ""),
            )
            if event_key in seen_event_keys:
                duplicate_count += 1
            else:
                seen_event_keys.add(event_key)
                all_event_data.append(data)

        assert len(all_event_data) == 1
        assert duplicate_count == 1

    def test_same_key_different_type_is_not_duplicate(self):
        """Mesma chave com tipo de evento diferente → são registros distintos."""
        seen_event_keys: set = set()
        all_event_data = []

        entries = [
            {
                "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
                "Tipo de Evento": "Cancelamento",
                "Data do Evento": "2025-03-16T14:00:00-03:00",
                "Detalhes / Justificativa": "Motivo A",
            },
            {
                "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
                "Tipo de Evento": "Carta de Correção (CC-e)",
                "Data do Evento": "2025-03-17T09:00:00-03:00",
                "Detalhes / Justificativa": "[ide | UFIni -> MG]",
            },
        ]

        for data in entries:
            event_key = (
                data.get("Chave de Acesso (Referência)", ""),
                data.get("Tipo de Evento", ""),
                data.get("Data do Evento", ""),
                data.get("Detalhes / Justificativa", ""),
            )
            if event_key in seen_event_keys:
                pass
            else:
                seen_event_keys.add(event_key)
                all_event_data.append(data)

        assert len(all_event_data) == 2
