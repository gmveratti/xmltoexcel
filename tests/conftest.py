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
