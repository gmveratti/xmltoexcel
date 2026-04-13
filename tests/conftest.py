# tests/conftest.py

"""Fixtures centralizadas para testes unitários.

Todos os XMLs são criados in-memory via ET.fromstring() — zero acesso a disco.
O namespace padrão do SEFAZ é aplicado a todos os fixtures para simular XMLs reais.
"""

import pytest
import xml.etree.ElementTree as ET

NS = "http://www.portalfiscal.inf.br/cte"

# ==================== CT-e Fixtures ====================

VALID_CTE_XML = f"""\
<CTe xmlns="{NS}">
  <infCte Id="CTe35250312345678000195570010000012341000012340">
    <ide>
      <cUF>35</cUF>
      <cCT>00001234</cCT>
      <CFOP>6353</CFOP>
      <natOp>PRESTACAO DE SERVICO DE TRANSPORTE</natOp>
      <mod>57</mod>
      <serie>1</serie>
      <nCT>1234</nCT>
      <dhEmi>2025-03-15T08:30:00-03:00</dhEmi>
      <tpImp>1</tpImp>
      <tpEmis>1</tpEmis>
      <cDV>0</cDV>
      <tpAmb>1</tpAmb>
      <tpCTe>0</tpCTe>
      <procEmi>0</procEmi>
      <verProc>1.0</verProc>
      <cMunEnv>3550308</cMunEnv>
      <xMunEnv>SAO PAULO</xMunEnv>
      <UFEnv>SP</UFEnv>
      <modal>01</modal>
      <tpServ>0</tpServ>
      <cMunIni>3550308</cMunIni>
      <xMunIni>SAO PAULO</xMunIni>
      <UFIni>SP</UFIni>
      <cMunFim>3304557</cMunFim>
      <xMunFim>RIO DE JANEIRO</xMunFim>
      <UFFim>RJ</UFFim>
      <retira>0</retira>
      <indIEToma>1</indIEToma>
    </ide>
    <emit>
      <CNPJ>12345678000195</CNPJ>
      <IE>123456789012</IE>
      <xNome>TRANSPORTADORA EXEMPLO LTDA</xNome>
      <xFant>TRANS EXEMPLO</xFant>
    </emit>
    <rem>
      <CNPJ>98765432000100</CNPJ>
      <xNome>REMETENTE INDUSTRIA SA</xNome>
    </rem>
    <dest>
      <CNPJ>11223344000155</CNPJ>
      <xNome>DESTINATARIO COMERCIO LTDA</xNome>
    </dest>
    <vPrest>
      <vTPrest>1500.50</vTPrest>
      <vRec>1500.50</vRec>
      <Comp>
        <xNome>FRETE PESO</xNome>
        <vComp>1200.00</vComp>
      </Comp>
      <Comp>
        <xNome>PEDAGIO</xNome>
        <vComp>150.25</vComp>
      </Comp>
      <Comp>
        <xNome>GRIS</xNome>
        <vComp>100.25</vComp>
      </Comp>
      <Comp>
        <xNome>DESPACHO</xNome>
        <vComp>50.00</vComp>
      </Comp>
    </vPrest>
    <imp>
      <ICMS>
        <ICMS00>
          <CST>00</CST>
          <vBC>1500.50</vBC>
          <pICMS>12.00</pICMS>
          <vICMS>180.06</vICMS>
        </ICMS00>
      </ICMS>
      <vTotTrib>180.06</vTotTrib>
    </imp>
    <infCTeNorm>
      <infCarga>
        <vCarga>50000.00</vCarga>
        <proPred>MATERIAL ELETRONICO</proPred>
      </infCarga>
      <infNFe>
        <chave>35250398765432000100550010000056781000056780</chave>
      </infNFe>
      <infNFe>
        <chave>35250398765432000100550010000056791000056790</chave>
      </infNFe>
    </infCTeNorm>
  </infCte>
</CTe>"""


CTE_WITH_ICMS_OUTRA_UF_XML = f"""\
<CTe xmlns="{NS}">
  <infCte Id="CTe31250311111111000100570010000099991000099990">
    <ide>
      <cUF>31</cUF>
      <nCT>9999</nCT>
      <dhEmi>2025-03-20T10:00:00-03:00</dhEmi>
    </ide>
    <vPrest>
      <vTPrest>800.00</vTPrest>
      <vRec>800.00</vRec>
    </vPrest>
    <imp>
      <ICMS>
        <ICMSOutraUF>
          <CST>90</CST>
          <vBCOutraUF>800.00</vBCOutraUF>
          <pICMSOutraUF>7.00</pICMSOutraUF>
          <vICMSOutraUF>56.00</vICMSOutraUF>
        </ICMSOutraUF>
      </ICMS>
    </imp>
  </infCte>
</CTe>"""


CTE_WITH_ICMS60_XML = f"""\
<CTe xmlns="{NS}">
  <infCte Id="CTe33250322222222000200570010000088881000088880">
    <ide>
      <cUF>33</cUF>
      <nCT>8888</nCT>
    </ide>
    <imp>
      <ICMS>
        <ICMS60>
          <CST>60</CST>
          <vBCSTRet>500.00</vBCSTRet>
          <vICMSSTRet>60.00</vICMSSTRet>
          <pICMSSTRet>12.00</pICMSSTRet>
        </ICMS60>
      </ICMS>
    </imp>
  </infCte>
</CTe>"""


CTE_WITH_DUPLICATE_COMPONENTS_XML = f"""\
<CTe xmlns="{NS}">
  <infCte Id="CTe35250333333333000300570010000077771000077770">
    <ide><cUF>35</cUF><nCT>7777</nCT></ide>
    <vPrest>
      <vTPrest>500.00</vTPrest>
      <vRec>500.00</vRec>
      <Comp>
        <xNome>PEDAGIO</xNome>
        <vComp>100.00</vComp>
      </Comp>
      <Comp>
        <xNome>PEDÁGIO</xNome>
        <vComp>50.00</vComp>
      </Comp>
    </vPrest>
  </infCte>
</CTe>"""


CTE_WITH_INVALID_COMP_VALUE_XML = f"""\
<CTe xmlns="{NS}">
  <infCte Id="CTe35250344444444000400570010000066661000066660">
    <ide><cUF>35</cUF><nCT>6666</nCT></ide>
    <vPrest>
      <vTPrest>300.00</vTPrest>
      <vRec>300.00</vRec>
      <Comp>
        <xNome>GRIS</xNome>
        <vComp>200.00</vComp>
      </Comp>
      <Comp>
        <xNome>GRIS</xNome>
        <vComp>NAO_NUMERICO</vComp>
      </Comp>
    </vPrest>
  </infCte>
</CTe>"""


CTE_WITH_UNKNOWN_COMPONENT_XML = f"""\
<CTe xmlns="{NS}">
  <infCte Id="CTe35250355555555000500570010000055551000055550">
    <ide><cUF>35</cUF><nCT>5555</nCT></ide>
    <vPrest>
      <vTPrest>100.00</vTPrest>
      <vRec>100.00</vRec>
      <Comp>
        <xNome>TAXA ESPECIAL INEDITA</xNome>
        <vComp>100.00</vComp>
      </Comp>
    </vPrest>
  </infCte>
</CTe>"""


INVALID_CTE_XML = f"""\
<CTe xmlns="{NS}">
  <protCTe>
    <infProt>
      <tpAmb>1</tpAmb>
      <nProt>135250000012345</nProt>
    </infProt>
  </protCTe>
</CTe>"""


# ==================== Event Fixtures ====================

EVENT_CANCELAMENTO_XML = f"""\
<procEventoCTe xmlns="{NS}">
  <eventoCTe>
    <infEvento>
      <tpEvento>110111</tpEvento>
      <chCTe>35250312345678000195570010000012341000012340</chCTe>
      <dhEvento>2025-03-16T14:00:00-03:00</dhEvento>
      <xJust>Erro na emissao do documento fiscal</xJust>
    </infEvento>
  </eventoCTe>
</procEventoCTe>"""


EVENT_CCE_XML = f"""\
<procEventoCTe xmlns="{NS}">
  <eventoCTe>
    <infEvento>
      <tpEvento>110110</tpEvento>
      <chCTe>35250312345678000195570010000012341000012340</chCTe>
      <dhEvento>2025-03-17T09:00:00-03:00</dhEvento>
      <xCondUso>Uso permitido conforme legislacao vigente</xCondUso>
      <infCorrecao>
        <grupoAlterado>ide</grupoAlterado>
        <campoAlterado>UFIni</campoAlterado>
        <valorAlterado>MG</valorAlterado>
      </infCorrecao>
      <infCorrecao>
        <grupoAlterado>ide</grupoAlterado>
        <campoAlterado>UFFim</campoAlterado>
        <valorAlterado>RJ</valorAlterado>
      </infCorrecao>
    </infEvento>
  </eventoCTe>
</procEventoCTe>"""


EVENT_DESACORDO_XML = f"""\
<procEventoCTe xmlns="{NS}">
  <eventoCTe>
    <infEvento>
      <tpEvento>610110</tpEvento>
      <chCTe>31250399887766000155570010000044441000044440</chCTe>
      <dhEvento>2025-03-18T16:30:00-03:00</dhEvento>
      <xJust>Servico nao foi prestado conforme combinado</xJust>
    </infEvento>
  </eventoCTe>
</procEventoCTe>"""


EVENT_UNKNOWN_CODE_XML = f"""\
<procEventoCTe xmlns="{NS}">
  <eventoCTe>
    <infEvento>
      <tpEvento>999999</tpEvento>
      <chCTe>35250300000000000000570010000000001000000000</chCTe>
      <dhEvento>2025-04-01T12:00:00-03:00</dhEvento>
    </infEvento>
  </eventoCTe>
</procEventoCTe>"""


# ==================== Pytest Fixtures ====================

@pytest.fixture
def cte_root() -> ET.Element:
    """XML mínimo de CT-e válido para testes gerais."""
    return ET.fromstring(VALID_CTE_XML)


@pytest.fixture
def cte_icms_outra_uf_root() -> ET.Element:
    """CT-e com ICMSOutraUF para testar mapeamento do ICMS_MAP."""
    return ET.fromstring(CTE_WITH_ICMS_OUTRA_UF_XML)


@pytest.fixture
def cte_icms60_root() -> ET.Element:
    """CT-e com ICMS60 para testar mapeamento ST."""
    return ET.fromstring(CTE_WITH_ICMS60_XML)


@pytest.fixture
def cte_duplicate_components_root() -> ET.Element:
    """CT-e com dois pedágios para testar soma acumulativa."""
    return ET.fromstring(CTE_WITH_DUPLICATE_COMPONENTS_XML)


@pytest.fixture
def cte_invalid_comp_value_root() -> ET.Element:
    """CT-e com valor não-numérico no 2º componente para testar resiliência."""
    return ET.fromstring(CTE_WITH_INVALID_COMP_VALUE_XML)


@pytest.fixture
def cte_unknown_component_root() -> ET.Element:
    """CT-e com componente desconhecido para testar fallback dinâmico."""
    return ET.fromstring(CTE_WITH_UNKNOWN_COMPONENT_XML)


@pytest.fixture
def cte_invalid_root() -> ET.Element:
    """XML SEM <infCte> — deve retornar None."""
    return ET.fromstring(INVALID_CTE_XML)


@pytest.fixture
def event_cancelamento_root() -> ET.Element:
    """Evento de Cancelamento (110111)."""
    return ET.fromstring(EVENT_CANCELAMENTO_XML)


@pytest.fixture
def event_cce_root() -> ET.Element:
    """Evento de Carta de Correção (110110) com infCorrecao."""
    return ET.fromstring(EVENT_CCE_XML)


@pytest.fixture
def event_desacordo_root() -> ET.Element:
    """Evento de Prestação em Desacordo (610110)."""
    return ET.fromstring(EVENT_DESACORDO_XML)


@pytest.fixture
def event_unknown_code_root() -> ET.Element:
    """Evento com código desconhecido (999999)."""
    return ET.fromstring(EVENT_UNKNOWN_CODE_XML)


# ==================== NF-e Fixtures ====================

NS_NFE = "http://www.portalfiscal.inf.br/nfe"

VALID_NFE_XML = f"""\
<nfeProc xmlns="{NS_NFE}">
  <NFe>
    <infNFe Id="NFe35250312345678000195550010000001231000001230" versao="4.00">
      <ide>
        <natOp>VENDA DE MERCADORIAS</natOp>
        <nNF>123</nNF>
        <dhEmi>2025-03-20T10:30:00-03:00</dhEmi>
        <tpNF>1</tpNF>
      </ide>
      <emit>
        <CNPJ>12345678000195</CNPJ>
        <xNome>EMPRESA EMITENTE LTDA</xNome>
      </emit>
      <dest>
        <CNPJ>98765432000100</CNPJ>
        <xNome>CLIENTE DESTINATARIO SA</xNome>
        <enderDest>
          <UF>SP</UF>
          <xMun>SAO PAULO</xMun>
        </enderDest>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>PROD001</cProd>
          <cEAN>7891234567890</cEAN>
          <xProd>TECLADO MECANICO RGB</xProd>
          <NCM>84716052</NCM>
          <CFOP>5102</CFOP>
          <qCom>10.0000</qCom>
          <vUnCom>150.0000</vUnCom>
          <vProd>1500.00</vProd>
        </prod>
        <imposto>
          <ICMS><ICMS00><vICMS>270.00</vICMS></ICMS00></ICMS>
        </imposto>
      </det>
      <det nItem="2">
        <prod>
          <cProd>PROD002</cProd>
          <cEAN>7891234567891</cEAN>
          <xProd>MOUSE GAMER WIRELESS</xProd>
          <NCM>84716052</NCM>
          <CFOP>5102</CFOP>
          <qCom>5.0000</qCom>
          <vUnCom>200.0000</vUnCom>
          <vProd>1000.00</vProd>
        </prod>
        <imposto>
          <ICMS><ICMS00><vICMS>180.00</vICMS></ICMS00></ICMS>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vBC>2500.00</vBC>
          <vICMS>450.00</vICMS>
          <vProd>2500.00</vProd>
          <vFrete>50.00</vFrete>
          <vNF>2550.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>"""


NFE_WITH_AMAZON_ORDER_XML = f"""\
<nfeProc xmlns="{NS_NFE}">
  <NFe>
    <infNFe Id="NFe35250399887766000155550010000009991000009990" versao="4.00">
      <ide>
        <natOp>VENDA</natOp>
        <nNF>999</nNF>
        <dhEmi>2025-03-25T14:00:00-03:00</dhEmi>
        <tpNF>1</tpNF>
      </ide>
      <emit>
        <CNPJ>99887766000155</CNPJ>
        <xNome>LOJA ONLINE LTDA</xNome>
      </emit>
      <dest>
        <CPF>12345678901</CPF>
        <xNome>JOAO DA SILVA</xNome>
        <enderDest>
          <UF>RJ</UF>
          <xMun>RIO DE JANEIRO</xMun>
        </enderDest>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>AMZ001</cProd>
          <cEAN>SEM GTIN</cEAN>
          <xProd>FONE BLUETOOTH</xProd>
          <NCM>85183000</NCM>
          <CFOP>6102</CFOP>
          <qCom>1.0000</qCom>
          <vUnCom>299.9000</vUnCom>
          <vProd>299.90</vProd>
        </prod>
      </det>
      <total>
        <ICMSTot>
          <vBC>299.90</vBC>
          <vICMS>53.98</vICMS>
          <vProd>299.90</vProd>
          <vFrete>0.00</vFrete>
          <vNF>299.90</vNF>
        </ICMSTot>
      </total>
      <infAdic>
        <infCpl>Numero do pedido da compra: 123-4567890-1234567. Obrigado pela preferencia.</infCpl>
      </infAdic>
    </infNFe>
  </NFe>
</nfeProc>"""


NFE_NO_DET_XML = f"""\
<nfeProc xmlns="{NS_NFE}">
  <NFe>
    <infNFe Id="NFe35250300000000000000550010000000011000000010" versao="4.00">
      <ide>
        <natOp>REMESSA</natOp>
        <nNF>1</nNF>
        <dhEmi>2025-01-01T00:00:00-03:00</dhEmi>
        <tpNF>1</tpNF>
      </ide>
      <emit>
        <CNPJ>00000000000000</CNPJ>
        <xNome>EMITENTE VAZIO</xNome>
      </emit>
      <total>
        <ICMSTot>
          <vBC>0.00</vBC>
          <vICMS>0.00</vICMS>
          <vProd>0.00</vProd>
          <vFrete>0.00</vFrete>
          <vNF>0.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>"""


INVALID_NFE_XML = f"""\
<nfeProc xmlns="{NS_NFE}">
  <protNFe>
    <infProt>
      <tpAmb>1</tpAmb>
      <nProt>135250000012345</nProt>
    </infProt>
  </protNFe>
</nfeProc>"""


NFE_EVENT_CANCELAMENTO_XML = f"""\
<procEventoNFe xmlns="{NS_NFE}">
  <evento>
    <infEvento>
      <tpEvento>110111</tpEvento>
      <chNFe>35250312345678000195550010000001231000001230</chNFe>
      <dhEvento>2025-03-21T09:00:00-03:00</dhEvento>
      <detEvento>
        <xJust>Erro na emissao da nota fiscal</xJust>
      </detEvento>
    </infEvento>
  </evento>
</procEventoNFe>"""


NFE_EVENT_CCE_XML = f"""\
<procEventoNFe xmlns="{NS_NFE}">
  <evento>
    <infEvento>
      <tpEvento>110110</tpEvento>
      <chNFe>35250312345678000195550010000001231000001230</chNFe>
      <dhEvento>2025-03-22T11:00:00-03:00</dhEvento>
      <detEvento>
        <xCorrecao>Correcao no endereco do destinatario</xCorrecao>
      </detEvento>
    </infEvento>
  </evento>
</procEventoNFe>"""


NFE_EVENT_NO_INFO_XML = f"""\
<nfeProc xmlns="{NS_NFE}">
  <protNFe>
    <infProt>
      <tpAmb>1</tpAmb>
    </infProt>
  </protNFe>
</nfeProc>"""


# ==================== NF-e Pytest Fixtures ====================

@pytest.fixture
def nfe_root() -> ET.Element:
    """NF-e válida com 2 produtos para testar flattening."""
    return ET.fromstring(VALID_NFE_XML)


@pytest.fixture
def nfe_amazon_root() -> ET.Element:
    """NF-e com Pedido Amazon no infCpl e destinatário CPF."""
    return ET.fromstring(NFE_WITH_AMAZON_ORDER_XML)


@pytest.fixture
def nfe_no_det_root() -> ET.Element:
    """NF-e sem itens (<det>) — deve retornar apenas o cabeçalho."""
    return ET.fromstring(NFE_NO_DET_XML)


@pytest.fixture
def nfe_invalid_root() -> ET.Element:
    """NF-e SEM <infNFe> — deve retornar None."""
    return ET.fromstring(INVALID_NFE_XML)


@pytest.fixture
def nfe_event_cancelamento_root() -> ET.Element:
    """Evento de Cancelamento NF-e (110111)."""
    return ET.fromstring(NFE_EVENT_CANCELAMENTO_XML)


@pytest.fixture
def nfe_event_cce_root() -> ET.Element:
    """Evento de CC-e NF-e (110110) com xCorrecao."""
    return ET.fromstring(NFE_EVENT_CCE_XML)


@pytest.fixture
def nfe_event_no_info_root() -> ET.Element:
    """XML NF-e sem <infEvento> — deve retornar None."""
    return ET.fromstring(NFE_EVENT_NO_INFO_XML)

