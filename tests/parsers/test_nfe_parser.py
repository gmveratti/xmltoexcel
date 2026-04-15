# tests/parsers/test_nfe_parser.py

"""Testes unitários para o NFeParser — regras de extração de dados de NF-e (1:N)."""

import xml.etree.ElementTree as ET
from nfe.nfe_parser import NFeParser


class TestNFeParserStructure:
    """Verifica que o parser rejeita XMLs inválidos e aceita XMLs válidos."""

    def test_returns_none_for_invalid_xml(self, nfe_invalid_root: ET.Element):
        """XML sem <infNFe> → NFeParser.extract_data() deve retornar None."""
        parser = NFeParser(nfe_invalid_root)
        result = parser.extract_data()
        assert result is None

    def test_returns_list_for_valid_xml(self, nfe_root: ET.Element):
        """XML válido → retorna lista de dicionários."""
        parser = NFeParser(nfe_root)
        result = parser.extract_data()
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0


class TestNFeItemExtraction:
    """Verifica a relação 1:N (uma nota para múltiplos itens)."""

    def test_one_row_per_product_item(self, nfe_root: ET.Element):
        """O XML de fixture tem 2 itens <det> → deve retornar 2 linhas."""
        parser = NFeParser(nfe_root)
        result = parser.extract_data()
        assert len(result) == 2
        assert result[0]["nItem_nItem"] == "1"
        assert result[1]["nItem_nItem"] == "2"


class TestNFeFieldExtraction:
    """Verifica a extração de campos de cabeçalho e produtos."""

    def test_extracts_access_key_without_prefix(self, nfe_root: ET.Element):
        """O prefixo 'NFe' deve ser removido, deixando os 44 dígitos."""
        parser = NFeParser(nfe_root)
        result = parser.extract_data()

        for row in result:
            access_key = row["chv_nfe_Id"]
            assert access_key == "35250412345678000195550010000012341000012340"
            assert not access_key.startswith("NFe")
            assert len(access_key) == 44

    def test_extracts_header_fields(self, nfe_root: ET.Element):
        """Campos de cabeçalho (ide, emit, dest) devem estar em todas as linhas."""
        parser = NFeParser(nfe_root)
        result = parser.extract_data()

        for row in result:
            assert row["ide_nNF"] == "1234"
            assert row["emit_CNPJ"] == "12345678000195"
            assert row["dest_xNome"] == "CLIENTE DESTINATARIO SA"
            assert row["total_ICMSTot_vNF"] == "1000.00"

    def test_extracts_product_fields(self, nfe_root: ET.Element):
        """Campos específicos de cada produto devem ser extraídos corretamente."""
        parser = NFeParser(nfe_root)
        result = parser.extract_data()

        # Item 1
        assert result[0]["prod_cProd"] == "P001"
        assert result[0]["prod_xProd"] == "PRODUTO A"
        assert result[0]["prod_vProd"] == "500.00"
        assert result[0]["imposto_ICMS_vICMS"] == "90.00"

        # Item 2
        assert result[1]["prod_cProd"] == "P002"
        assert result[1]["prod_xProd"] == "PRODUTO B"
        assert result[1]["prod_vProd"] == "500.00"

    def test_missing_fields_are_empty_string(self, nfe_root: ET.Element):
        """Campos ausentes (ex: cobr_fat) devem retornar string vazia."""
        parser = NFeParser(nfe_root)
        result = parser.extract_data()
        
        for row in result:
            assert row["cobr_fat_nFat"] == ""
            assert row["infAdic_infCpl"] == ""
