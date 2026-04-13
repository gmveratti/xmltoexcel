# tests/core/test_pipeline_dedup.py

"""Testes unitários para a lógica de deduplicação do pipeline.

Testamos diretamente os métodos estáticos de produção
`ProcessingPipeline.check_and_register_main` e
`ProcessingPipeline.check_and_register_event`, garantindo que qualquer
alteração no código de produção seja imediatamente detectada aqui.
"""

from shared.pipeline import ProcessingPipeline
from shared.models import DataType


class TestCteDeduplication:
    """Testa dedup de CT-e via `check_and_register_main` com DataType.CTE."""

    def test_first_occurrence_is_accepted(self):
        """Primeiro CT-e com uma dada chave → aceito (retorna True) e chave registrada."""
        seen_keys: set = set()
        data = {"chv_cte_Id": "35250312345678000195570010000012341000012340"}

        result = ProcessingPipeline.check_and_register_main(data, seen_keys, DataType.CTE)

        assert result is True
        assert "35250312345678000195570010000012341000012340" in seen_keys

    def test_duplicate_cte_key_is_rejected(self):
        """Segunda ocorrência de uma chave idêntica → rejeitada (retorna False)."""
        seen_keys: set = {"35250312345678000195570010000012341000012340"}
        data = {"chv_cte_Id": "35250312345678000195570010000012341000012340"}

        result = ProcessingPipeline.check_and_register_main(data, seen_keys, DataType.CTE)

        assert result is False
        assert len(seen_keys) == 1

    def test_empty_cte_key_is_always_accepted(self):
        """Chave vazia não é rastreada no set, mas o registro é aceito."""
        seen_keys: set = set()
        data = {"chv_cte_Id": ""}

        result = ProcessingPipeline.check_and_register_main(data, seen_keys, DataType.CTE)

        assert result is True
        assert len(seen_keys) == 0

    def test_two_empty_keys_are_both_accepted(self):
        """Duas entradas com chave vazia são ambas aceitas."""
        seen_keys: set = set()
        data = {"chv_cte_Id": ""}

        r1 = ProcessingPipeline.check_and_register_main(data, seen_keys, DataType.CTE)
        r2 = ProcessingPipeline.check_and_register_main(data, seen_keys, DataType.CTE)

        assert r1 is True
        assert r2 is True

    def test_three_unique_keys_all_accepted(self):
        """Três chaves distintas → todas aceitas."""
        seen_keys: set = set()
        entries = [
            {"chv_cte_Id": "11111111111111111111111111111111111111111111"},
            {"chv_cte_Id": "22222222222222222222222222222222222222222222"},
            {"chv_cte_Id": "33333333333333333333333333333333333333333333"},
        ]

        results = [ProcessingPipeline.check_and_register_main(d, seen_keys, DataType.CTE) for d in entries]

        assert all(results)
        assert len(seen_keys) == 3

    def test_mixed_batch_counts_duplicates(self):
        """Lote misto: 3 entradas onde 1 é duplicata → 2 aceitas, 1 rejeitada."""
        seen_keys: set = set()
        entries = [
            {"chv_cte_Id": "35250312345678000195570010000012341000012340"},
            {"chv_cte_Id": "35250312345678000195570010000012341000012340"},
            {"chv_cte_Id": "33250399887766000155570010000044441000044440"},
        ]

        results = [ProcessingPipeline.check_and_register_main(d, seen_keys, DataType.CTE) for d in entries]

        assert sum(1 for r in results if r is True) == 2
        assert sum(1 for r in results if r is False) == 1


class TestNfeDeduplication:
    """Testa dedup de NF-e via `check_and_register_main` com DataType.NFE.

    A chave NF-e é composta: chv_nfe_Id + nItem (pois o header repete por produto).
    """

    def test_first_nfe_item_is_accepted(self):
        """Primeiro item NF-e → aceito e chave composta registrada."""
        seen_keys: set = set()
        data = {"chv_nfe_Id": "35250312345678000195550010000001231000001230", "det_nItem": "1"}

        result = ProcessingPipeline.check_and_register_main(data, seen_keys, DataType.NFE)

        assert result is True
        assert "35250312345678000195550010000001231000001230_1" in seen_keys

    def test_same_nfe_different_items_are_both_accepted(self):
        """Mesma NF-e com itens diferentes → ambos aceitos (chave composta difere)."""
        seen_keys: set = set()
        item1 = {"chv_nfe_Id": "35250312345678000195550010000001231000001230", "det_nItem": "1"}
        item2 = {"chv_nfe_Id": "35250312345678000195550010000001231000001230", "det_nItem": "2"}

        r1 = ProcessingPipeline.check_and_register_main(item1, seen_keys, DataType.NFE)
        r2 = ProcessingPipeline.check_and_register_main(item2, seen_keys, DataType.NFE)

        assert r1 is True
        assert r2 is True
        assert len(seen_keys) == 2

    def test_duplicate_nfe_item_is_rejected(self):
        """Mesmo item da mesma NF-e → duplicata rejeitada."""
        seen_keys: set = set()
        data = {"chv_nfe_Id": "35250312345678000195550010000001231000001230", "det_nItem": "1"}

        ProcessingPipeline.check_and_register_main(data, seen_keys, DataType.NFE)
        result = ProcessingPipeline.check_and_register_main(data, seen_keys, DataType.NFE)

        assert result is False
        assert len(seen_keys) == 1

    def test_different_nfes_same_item_number_are_both_accepted(self):
        """NF-es diferentes com mesmo nItem → ambas aceitas (chave difere)."""
        seen_keys: set = set()
        nfe_a = {"chv_nfe_Id": "11111111111111111111111111111111111111111111", "det_nItem": "1"}
        nfe_b = {"chv_nfe_Id": "22222222222222222222222222222222222222222222", "det_nItem": "1"}

        r1 = ProcessingPipeline.check_and_register_main(nfe_a, seen_keys, DataType.NFE)
        r2 = ProcessingPipeline.check_and_register_main(nfe_b, seen_keys, DataType.NFE)

        assert r1 is True
        assert r2 is True


class TestEventDeduplication:
    """Testa `ProcessingPipeline.check_and_register_event` com diferentes cenários."""

    def test_first_event_is_accepted(self):
        """Primeiro evento → aceito (retorna True)."""
        seen_keys: set = set()
        data = {
            "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
            "Tipo de Evento": "Cancelamento",
            "Data do Evento": "2025-03-16T14:00:00-03:00",
            "Detalhes / Justificativa": "Erro na emissao",
        }

        result = ProcessingPipeline.check_and_register_event(data, seen_keys)
        assert result is True

    def test_duplicate_event_tuple_is_rejected(self):
        """Evento com a mesma tupla-chave → rejeitado."""
        seen_keys: set = set()
        data = {
            "Chave de Acesso (Referência)": "35250312345678000195570010000012341000012340",
            "Tipo de Evento": "Cancelamento",
            "Data do Evento": "2025-03-16T14:00:00-03:00",
            "Detalhes / Justificativa": "Erro na emissao",
        }

        ProcessingPipeline.check_and_register_event(data, seen_keys)
        result = ProcessingPipeline.check_and_register_event(data, seen_keys)
        assert result is False

    def test_same_key_different_event_type_is_not_duplicate(self):
        """Mesma chave com tipo diferente → dois registros distintos."""
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

        r1 = ProcessingPipeline.check_and_register_event(cancelamento, seen_keys)
        r2 = ProcessingPipeline.check_and_register_event(cce, seen_keys)

        assert r1 is True
        assert r2 is True

    def test_same_key_same_type_different_date_is_not_duplicate(self):
        """Mesmo tipo em datas diferentes → dois registros legítimos."""
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

        r1 = ProcessingPipeline.check_and_register_event(event_day1, seen_keys)
        r2 = ProcessingPipeline.check_and_register_event(event_day2, seen_keys)

        assert r1 is True
        assert r2 is True
