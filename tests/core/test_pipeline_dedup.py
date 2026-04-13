# tests/core/test_pipeline_dedup.py

"""Testes unitários para a lógica de deduplicação do pipeline.

Testamos diretamente os métodos estáticos de produção
`ProcessingPipeline.check_and_register_cte` e
`ProcessingPipeline.check_and_register_event`, garantindo que qualquer
alteração no código de produção seja imediatamente detectada aqui.
"""

from core.pipeline import ProcessingPipeline


class TestCteDeduplication:
    """Testa `ProcessingPipeline.check_and_register_cte` com diferentes cenários."""

    def test_first_occurrence_is_accepted(self):
        """Primeiro CT-e com uma dada chave → aceito (retorna True) e chave registrada."""
        seen_keys: set = set()
        data = {"chv_cte_Id": "35250312345678000195570010000012341000012340"}

        result = ProcessingPipeline.check_and_register_cte(data, seen_keys)

        assert result is True
        assert "35250312345678000195570010000012341000012340" in seen_keys

    def test_duplicate_cte_key_is_rejected(self):
        """Segunda ocorrência de uma chave idêntica → rejeitada (retorna False)."""
        seen_keys: set = {"35250312345678000195570010000012341000012340"}
        data = {"chv_cte_Id": "35250312345678000195570010000012341000012340"}

        result = ProcessingPipeline.check_and_register_cte(data, seen_keys)

        assert result is False
        assert len(seen_keys) == 1  # Nenhuma chave nova foi inserida

    def test_empty_cte_key_is_always_accepted(self):
        """Chave vazia não é rastreada no set, mas o registro é aceito (retorna True)."""
        seen_keys: set = set()
        data = {"chv_cte_Id": ""}

        result = ProcessingPipeline.check_and_register_cte(data, seen_keys)

        assert result is True
        assert len(seen_keys) == 0  # Chave vazia não entra no set

    def test_two_empty_keys_are_both_accepted(self):
        """Duas entradas com chave vazia são ambas aceitas, pois não são rastreadas."""
        seen_keys: set = set()
        data = {"chv_cte_Id": ""}

        result_1 = ProcessingPipeline.check_and_register_cte(data, seen_keys)
        result_2 = ProcessingPipeline.check_and_register_cte(data, seen_keys)

        assert result_1 is True
        assert result_2 is True

    def test_three_unique_keys_all_accepted(self):
        """Três chaves distintas → todas aceitas e todas registradas no set."""
        seen_keys: set = set()
        entries = [
            {"chv_cte_Id": "11111111111111111111111111111111111111111111"},
            {"chv_cte_Id": "22222222222222222222222222222222222222222222"},
            {"chv_cte_Id": "33333333333333333333333333333333333333333333"},
        ]

        results = [ProcessingPipeline.check_and_register_cte(d, seen_keys) for d in entries]

        assert all(results)
        assert len(seen_keys) == 3

    def test_mixed_batch_counts_duplicates_correctly(self):
        """Lote misto: 3 entradas onde 1 é duplicata → 2 aceitas, 1 rejeitada."""
        seen_keys: set = set()
        entries = [
            {"chv_cte_Id": "35250312345678000195570010000012341000012340"},
            {"chv_cte_Id": "35250312345678000195570010000012341000012340"},  # duplicata
            {"chv_cte_Id": "33250399887766000155570010000044441000044440"},
        ]

        results = [ProcessingPipeline.check_and_register_cte(d, seen_keys) for d in entries]

        accepted = sum(1 for r in results if r is True)
        rejected = sum(1 for r in results if r is False)

        assert accepted == 2
        assert rejected == 1


class TestEventDeduplication:
    """Testa `ProcessingPipeline.check_and_register_event` com diferentes cenários."""

    def test_first_event_is_accepted(self):
        """Primeiro evento com uma dada tupla-chave → aceito (retorna True)."""
        seen_keys: set = set()
        data = {
            "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
            "Tipo de Evento": "Cancelamento",
            "Data do Evento": "2025-03-16T14:00:00-03:00",
            "Detalhes / Justificativa": "Erro na emissao",
        }

        result = ProcessingPipeline.check_and_register_event(data, seen_keys)

        assert result is True
        assert len(seen_keys) == 1

    def test_duplicate_event_tuple_is_rejected(self):
        """Evento com a mesma (chave, tipo, data, detalhe) → rejeitado (retorna False)."""
        seen_keys: set = set()
        data = {
            "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
            "Tipo de Evento": "Cancelamento",
            "Data do Evento": "2025-03-16T14:00:00-03:00",
            "Detalhes / Justificativa": "Erro na emissao",
        }

        ProcessingPipeline.check_and_register_event(data, seen_keys)  # Primeira: registra
        result = ProcessingPipeline.check_and_register_event(data, seen_keys)  # Segunda: duplicata

        assert result is False
        assert len(seen_keys) == 1

    def test_same_key_different_event_type_is_not_duplicate(self):
        """Mesma chave de acesso com tipo de evento diferente → dois registros distintos."""
        seen_keys: set = set()
        cancelamento = {
            "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
            "Tipo de Evento": "Cancelamento",
            "Data do Evento": "2025-03-16T14:00:00-03:00",
            "Detalhes / Justificativa": "Motivo A",
        }
        cce = {
            "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
            "Tipo de Evento": "Carta de Correção (CC-e)",
            "Data do Evento": "2025-03-17T09:00:00-03:00",
            "Detalhes / Justificativa": "[ide | UFIni -> MG]",
        }

        result_1 = ProcessingPipeline.check_and_register_event(cancelamento, seen_keys)
        result_2 = ProcessingPipeline.check_and_register_event(cce, seen_keys)

        assert result_1 is True
        assert result_2 is True
        assert len(seen_keys) == 2

    def test_same_key_same_type_different_date_is_not_duplicate(self):
        """Mesmo tipo de evento em datas diferentes → dois registros legítimos."""
        seen_keys: set = set()
        event_day1 = {
            "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
            "Tipo de Evento": "Cancelamento",
            "Data do Evento": "2025-03-16T14:00:00-03:00",
            "Detalhes / Justificativa": "Motivo A",
        }
        event_day2 = {
            "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
            "Tipo de Evento": "Cancelamento",
            "Data do Evento": "2025-03-17T09:00:00-03:00",
            "Detalhes / Justificativa": "Motivo A",
        }

        result_1 = ProcessingPipeline.check_and_register_event(event_day1, seen_keys)
        result_2 = ProcessingPipeline.check_and_register_event(event_day2, seen_keys)

        assert result_1 is True
        assert result_2 is True
