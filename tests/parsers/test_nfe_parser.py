# tests/parsers/test_nfe_parser.py

"""Testes unitários para o parser de NF-e (Nota Fiscal Eletrônica).

Valida o flattening (1 linha por produto), extração de header,
dados de emitente/destinatário, totais, e regex do Pedido Amazon.
"""

from parsers.nfe_parser import NFeParser


class TestNFeParserValidXML:
    """Testa NFeParser com NF-e válida contendo 2 produtos."""

    def test_returns_list_not_none(self, nfe_root):
        """NF-e válida deve retornar uma lista (não None)."""
        result = NFeParser(nfe_root).extract_data()
        assert result is not None
        assert isinstance(result, list)

    def test_flattening_produces_one_row_per_item(self, nfe_root):
        """2 itens (<det>) → 2 linhas no resultado."""
        result = NFeParser(nfe_root).extract_data()
        assert len(result) == 2

    def test_access_key_extracted(self, nfe_root):
        """Chave de acesso (Id) é extraída e o prefixo 'NFe' removido."""
        result = NFeParser(nfe_root).extract_data()
        expected_key = "35250312345678000195550010000001231000001230"
        assert result[0]["chv_nfe_Id"] == expected_key
        assert result[1]["chv_nfe_Id"] == expected_key

    def test_ide_fields_extracted(self, nfe_root):
        """Campos de identificação (natOp, nNF, dhEmi, tpNF) preenchidos."""
        result = NFeParser(nfe_root).extract_data()
        row = result[0]
        assert row["ide_natOp"] == "VENDA DE MERCADORIAS"
        assert row["ide_nNF"] == "123"
        assert row["ide_dhEmi"] == "2025-03-20T10:30:00-03:00"
        assert row["ide_tpNF"] == "1"

    def test_emit_fields_extracted(self, nfe_root):
        """Dados do emitente (CNPJ, xNome) preenchidos."""
        result = NFeParser(nfe_root).extract_data()
        assert result[0]["emit_CNPJ"] == "12345678000195"
        assert result[0]["emit_xNome"] == "EMPRESA EMITENTE LTDA"

    def test_dest_fields_with_cnpj(self, nfe_root):
        """Destinatário com CNPJ → dest_Doc preenchido."""
        result = NFeParser(nfe_root).extract_data()
        assert result[0]["dest_Doc"] == "98765432000100"
        assert result[0]["dest_xNome"] == "CLIENTE DESTINATARIO SA"
        assert result[0]["dest_UF"] == "SP"
        assert result[0]["dest_xMun"] == "SAO PAULO"

    def test_totals_extracted(self, nfe_root):
        """Totais do ICMSTot preenchidos corretamente."""
        result = NFeParser(nfe_root).extract_data()
        row = result[0]
        assert row["tot_vBC"] == "2500.00"
        assert row["tot_vICMS"] == "450.00"
        assert row["tot_vProd"] == "2500.00"
        assert row["tot_vFrete"] == "50.00"
        assert row["tot_vNF"] == "2550.00"

    def test_item1_product_data(self, nfe_root):
        """Produto do item 1 extraído corretamente."""
        result = NFeParser(nfe_root).extract_data()
        row = result[0]
        assert row["nItem"] == "1"
        assert row["prod_cProd"] == "PROD001"
        assert row["prod_xProd"] == "TECLADO MECANICO RGB"
        assert row["prod_CFOP"] == "5102"
        assert row["prod_qCom"] == "10.0000"
        assert row["prod_vProd"] == "1500.00"

    def test_item2_product_data(self, nfe_root):
        """Produto do item 2 extraído corretamente."""
        result = NFeParser(nfe_root).extract_data()
        row = result[1]
        assert row["nItem"] == "2"
        assert row["prod_cProd"] == "PROD002"
        assert row["prod_xProd"] == "MOUSE GAMER WIRELESS"
        assert row["prod_vProd"] == "1000.00"

    def test_item_icms_extracted(self, nfe_root):
        """ICMS a nível do item extraído para cada produto."""
        result = NFeParser(nfe_root).extract_data()
        assert result[0]["prod_vICMS"] == "270.00"
        assert result[1]["prod_vICMS"] == "180.00"

    def test_header_is_replicated_across_items(self, nfe_root):
        """O header (emitente, totais) é idêntico em ambas as linhas."""
        result = NFeParser(nfe_root).extract_data()
        assert result[0]["emit_CNPJ"] == result[1]["emit_CNPJ"]
        assert result[0]["tot_vNF"] == result[1]["tot_vNF"]
        assert result[0]["dest_xNome"] == result[1]["dest_xNome"]


class TestNFeParserAmazonOrder:
    """Testa extração do Pedido Amazon e destinatário com CPF."""

    def test_amazon_order_extracted(self, nfe_amazon_root):
        """Regex extrai o número do pedido Amazon do infCpl."""
        result = NFeParser(nfe_amazon_root).extract_data()
        assert result[0]["ext_Pedido_Amazon"] == "123-4567890-1234567"

    def test_inf_cpl_stored(self, nfe_amazon_root):
        """Texto completo do infCpl armazenado."""
        result = NFeParser(nfe_amazon_root).extract_data()
        assert "Numero do pedido da compra" in result[0]["infAdic_infCpl"]

    def test_dest_with_cpf(self, nfe_amazon_root):
        """Destinatário com CPF (pessoa física) → dest_Doc = CPF."""
        result = NFeParser(nfe_amazon_root).extract_data()
        assert result[0]["dest_Doc"] == "12345678901"
        assert result[0]["dest_UF"] == "RJ"


class TestNFeParserEdgeCases:
    """Testa cenários de borda (NF-e sem itens, NF-e inválida)."""

    def test_no_det_returns_header_only(self, nfe_no_det_root):
        """NF-e sem <det> → retorna lista com 1 elemento (header puro)."""
        result = NFeParser(nfe_no_det_root).extract_data()
        assert result is not None
        assert len(result) == 1
        assert result[0]["ide_natOp"] == "REMESSA"
        assert result[0]["nItem"] == ""

    def test_invalid_nfe_returns_none(self, nfe_invalid_root):
        """NF-e sem <infNFe> → retorna None."""
        result = NFeParser(nfe_invalid_root).extract_data()
        assert result is None
