# tests/parsers/test_cte_parser.py

"""Testes unitários para o CTeParser — regras de extração de dados de CT-e.

Cada teste recebe um fixture de ET.Element (in-memory) e valida que o parser
extrai os campos corretamente, sem nenhuma dependência de disco.
"""

import xml.etree.ElementTree as ET

from parsers.cte_parser import (
    CTeParser,
    _normalize_component_name,
    _resolve_component_column,
    COMPONENTS_MAP,
)


# ==================== Validação Estrutural ====================


class TestCTeParserStructure:
    """Verifica que o parser rejeita XMLs inválidos e aceita XMLs válidos."""

    def test_returns_none_for_invalid_xml(self, cte_invalid_root: ET.Element):
        """XML sem <infCte> → CTeParser.extract_data() deve retornar None."""
        parser = CTeParser(cte_invalid_root)
        result = parser.extract_data()
        assert result is None

    def test_returns_dict_for_valid_xml(self, cte_root: ET.Element):
        """XML válido → retorna dicionário com dados extraídos."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()
        assert result is not None
        assert isinstance(result, dict)


# ==================== Chave de Acesso ====================


class TestAccessKeyExtraction:
    """Verifica a extração correta da Chave de Acesso do CT-e."""

    def test_extracts_access_key_without_prefix(self, cte_root: ET.Element):
        """O prefixo 'CTe' deve ser removido, deixando os 44 dígitos puros."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()

        access_key = result["chv_cte_Id"]
        assert access_key == "35250312345678000195570010000012341000012340"
        assert not access_key.startswith("CTe")
        assert len(access_key) == 44

    def test_access_key_is_numeric_string(self, cte_root: ET.Element):
        """A chave de acesso deve conter apenas dígitos."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()
        assert result["chv_cte_Id"].isdigit()


# ==================== Campos Estruturais Base ====================


class TestBaseFieldExtraction:
    """Verifica a extração dos campos fiscais base via busca hierárquica."""

    def test_extracts_ide_fields(self, cte_root: ET.Element):
        """Campos do grupo <ide> devem ser extraídos corretamente."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()

        assert result["ide_cUF"] == "35"
        assert result["ide_CFOP"] == "6353"
        assert result["ide_nCT"] == "1234"
        assert result["ide_mod"] == "57"
        assert result["ide_serie"] == "1"
        assert result["ide_UFIni"] == "SP"
        assert result["ide_UFFim"] == "RJ"

    def test_extracts_emit_fields(self, cte_root: ET.Element):
        """Campos do emitente devem ser extraídos."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()

        assert result["emit_CNPJ"] == "12345678000195"
        assert result["emit_xNome"] == "TRANSPORTADORA EXEMPLO LTDA"

    def test_extracts_vprest_totals(self, cte_root: ET.Element):
        """Valores de prestação (vTPrest, vRec) devem vir preenchidos."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()

        assert result["vPrest_vTPrest"] == "1500.50"
        assert result["vPrest_vRec"] == "1500.50"

    def test_extracts_dhemi_datetime(self, cte_root: ET.Element):
        """A data de emissão deve ser preservada no formato ISO do XML."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()
        assert "2025-03-15" in result["ide_dhEmi"]

    def test_missing_fields_are_empty_string(self, cte_root: ET.Element):
        """Campos não presentes no XML devem retornar string vazia, nunca None."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()

        # O XML de teste não tem toma4, então os campos devem vir vazios
        assert result["ide_toma4_toma"] == ""
        assert result["ide_toma4_CNPJ"] == ""


# ==================== Chaves NF-e ====================


class TestNfeKeyExtraction:
    """Verifica a extração e concatenação das chaves NF-e."""

    def test_nfe_keys_joined_with_comma(self, cte_root: ET.Element):
        """Múltiplas chaves NF-e devem ser concatenadas com ', '."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()

        expected_keys = (
            "35250398765432000100550010000056781000056780, "
            "35250398765432000100550010000056791000056790"
        )
        assert result["infNFe_chave"] == expected_keys


# ==================== ICMS Mapping ====================


class TestIcmsMapping:
    """Verifica o mapeamento correto dos grupos ICMS via ICMS_MAP."""

    def test_icms_default_mapping(self, cte_root: ET.Element):
        """Grupo ICMS00 deve usar o DEFAULT mapping."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()

        assert result["imp_CST"] == "00"
        assert result["imp_vBC"] == "1500.50"
        assert result["imp_pICMS"] == "12.00"
        assert result["imp_vICMS"] == "180.06"

    def test_icms_outra_uf_mapping(self, cte_icms_outra_uf_root: ET.Element):
        """Grupo ICMSOutraUF deve mapear para colunas imp_ICMSOutraUF_*."""
        parser = CTeParser(cte_icms_outra_uf_root)
        result = parser.extract_data()

        assert result["imp_ICMSOutraUF_CST"] == "90"
        assert result["imp_ICMSOutraUF_vBCOutraUF"] == "800.00"
        assert result["imp_ICMSOutraUF_pICMSOutraUF"] == "7.00"
        assert result["imp_ICMSOutraUF_vICMSOutraUF"] == "56.00"

    def test_icms60_mapping(self, cte_icms60_root: ET.Element):
        """Grupo ICMS60 deve mapear CST e campos ST."""
        parser = CTeParser(cte_icms60_root)
        result = parser.extract_data()

        assert result["imp_CST"] == "60"
        assert result["imp_vBCSTRet"] == "500.00"
        assert result["imp_vICMSSTRet"] == "60.00"
        assert result["imp_pICMSSTRet"] == "12.00"


# ==================== Roteador Inteligente (Component Routing) ====================


class TestComponentRouting:
    """Verifica o COMPONENTS_MAP e o roteamento de nomes dinâmicos."""

    def test_component_routing_known_names(self, cte_root: ET.Element):
        """Componentes do COMPONENTS_MAP devem ser roteados corretamente."""
        parser = CTeParser(cte_root)
        result = parser.extract_data()

        assert result["comp_FRETE_PESO"] == "1200.00"
        assert result["comp_PEDAGIO"] == "150.25"
        assert result["comp_GRIS"] == "100.25"
        assert result["comp_DESPACHO"] == "50.00"

    def test_component_routing_fallback_dynamic(
        self, cte_unknown_component_root: ET.Element
    ):
        """Nome desconhecido deve gerar coluna dinâmica comp_{NOME_NORMALIZADO}."""
        parser = CTeParser(cte_unknown_component_root)
        result = parser.extract_data()

        assert result["comp_TAXA_ESPECIAL_INEDITA"] == "100.00"

    def test_component_accumulation(
        self, cte_duplicate_components_root: ET.Element
    ):
        """Dois pedágios (PEDAGIO + PEDÁGIO) devem somar 150.00 na mesma coluna."""
        parser = CTeParser(cte_duplicate_components_root)
        result = parser.extract_data()

        accumulated = float(result["comp_PEDAGIO"])
        assert accumulated == 150.00

    def test_component_accumulation_preserves_on_invalid_value(
        self, cte_invalid_comp_value_root: ET.Element
    ):
        """Valor não-numérico no 2º componente → preserva o valor anterior (200.00)."""
        parser = CTeParser(cte_invalid_comp_value_root)
        result = parser.extract_data()

        assert result["comp_GRIS"] == "200.00"


# ==================== Funções Auxiliares ====================


class TestNormalizationHelpers:
    """Testes unitários das funções puras de normalização."""

    def test_normalize_strips_and_uppercases(self):
        assert _normalize_component_name("  frete peso  ") == "FRETE PESO"

    def test_normalize_collapses_whitespace(self):
        assert _normalize_component_name("FRETE   PESO") == "FRETE PESO"

    def test_normalize_collapses_underscores(self):
        assert _normalize_component_name("FRETE__PESO") == "FRETE PESO"

    def test_normalize_mixed_separators(self):
        assert _normalize_component_name("  frt _ peso  ") == "FRT PESO"

    def test_resolve_known_synonym(self):
        """'FRT PESO' deve resolver para comp_FRETE_PESO."""
        assert _resolve_component_column("FRT PESO") == "comp_FRETE_PESO"

    def test_resolve_all_known_synonyms_map_to_canonical(self):
        """Todos os sinônimos no COMPONENTS_MAP devem resolver corretamente."""
        for raw_name, expected_column in COMPONENTS_MAP.items():
            assert _resolve_component_column(raw_name) == expected_column

    def test_resolve_unknown_generates_dynamic_column(self):
        """Nome fora do mapa deve gerar comp_{NORMALIZADO}."""
        result = _resolve_component_column("TAXA ESTRANHA NOVA")
        assert result == "comp_TAXA_ESTRANHA_NOVA"
