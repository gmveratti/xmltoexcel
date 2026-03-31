# core/constants.py

from typing import List, Dict, Set

# ==================== XML / Fiscal ====================

XML_NAMESPACE: Dict[str, str] = {"ns": "http://www.portalfiscal.inf.br/cte"}

# Ordem fixa das colunas base (As colunas dinâmicas "comp_*" serão adicionadas automaticamente no final)
EXCEL_HEADERS: List[str] = [
    "(CTe)", "chv_cte_Id", "(ide)", "ide_cUF", "ide_cCT", "ide_CFOP", "ide_natOp",
    "ide_mod", "ide_serie", "ide_nCT", "ide_dhEmi", "ide_tpImp", "ide_tpEmis",
    "ide_cDV", "ide_tpAmb", "ide_tpCTe", "ide_procEmi", "ide_verProc",
    "ide_cMunEnv", "ide_xMunEnv", "ide_UFEnv", "ide_modal", "ide_tpServ",
    "ide_cMunIni", "ide_xMunIni", "ide_UFIni", "ide_cMunFim", "ide_xMunFim",
    "ide_UFFim", "ide_retira", "ide_indIEToma", "(ide_toma3)", "ide_toma3_toma",
    "(ide_toma4)", "ide_toma4_toma", "ide_toma4_CNPJ", "ide_toma4_IE",
    "ide_toma4_xNome", "ide_toma4_xFant", "ide_toma4_fone",
    "(ide_toma4_enderToma)", "ide_toma4_enderToma_xLgr",
    "ide_toma4_enderToma_nro", "ide_toma4_enderToma_xBairro",
    "ide_toma4_enderToma_cMun", "ide_toma4_enderToma_xMun",
    "ide_toma4_enderToma_CEP", "ide_toma4_enderToma_UF",
    "ide_toma4_enderToma_cPais", "ide_toma4_enderToma_xPais", "ide_toma4_email",
    "(compl)", "(compl_Entrega)", "compl_Entrega_tpPer", "compl_Entrega_dProg",
    "compl_Entrega_tpHor", "compl_origCalc", "compl_destCalc", "compl_xObs",
    "(emit)", "emit_CNPJ", "emit_IE", "emit_xNome", "emit_xFant",
    "(emit_enderEmit)", "emit_enderEmit_xLgr",
    "emit_enderEmit_nro", "emit_enderEmit_xCpl", "emit_enderEmit_xBairro",
    "emit_enderEmit_cMun", "emit_enderEmit_xMun", "emit_enderEmit_CEP",
    "emit_enderEmit_UF", "emit_enderEmit_fone", "(rem)", "rem_CNPJ", "rem_CPF",
    "rem_IE", "rem_xNome", "rem_xFant", "rem_fone", "(rem_enderReme)",
    "rem_enderReme_xLgr", "rem_enderReme_nro", "rem_enderReme_xBairro",
    "rem_enderReme_cMun", "rem_enderReme_xMun", "rem_enderReme_CEP",
    "rem_enderReme_UF", "rem_enderReme_cPais", "rem_enderReme_xPais",
    "rem_email", "(exped)", "exped_CNPJ", "exped_IE", "exped_xNome",
    "exped_fone", "(exped_enderExped)", "exped_enderExped_xLgr",
    "exped_enderExped_nro", "exped_enderExped_xBairro",
    "exped_enderExped_cMun", "exped_enderExped_xMun", "exped_enderExped_CEP",
    "exped_enderExped_UF", "exped_enderExped_cPais", "exped_enderExped_xPais",
    "exped_email", "(receb)", "receb_CNPJ", "receb_CPF", "receb_IE", "receb_xNome",
    "receb_fone", "(receb_enderReceb)", "receb_enderReceb_xLgr",
    "receb_enderReceb_nro", "receb_enderReceb_xBairro",
    "receb_enderReceb_cMun", "receb_enderReceb_xMun", "receb_enderReceb_CEP",
    "receb_enderReceb_UF", "receb_enderReceb_cPais", "receb_enderReceb_xPais",
    "receb_email", "(dest)", "dest_CNPJ", "dest_CPF", "dest_IE", "dest_xNome",
    "dest_fone", "(dest_enderDest)", "dest_enderDest_xLgr",
    "dest_enderDest_nro", "dest_enderDest_xBairro", "dest_enderDest_cMun",
    "dest_enderDest_xMun", "dest_enderDest_CEP", "dest_enderDest_UF",
    "dest_enderDest_cPais", "dest_enderDest_xPais", "dest_email",
    "(vPrest)", "vPrest_vTPrest", "vPrest_vRec",
    "(imp)", "imp_CST", "imp_vBC", "imp_pICMS", "imp_vICMS",
    "imp_vBCSTRet", "imp_vICMSSTRet", "imp_pICMSSTRet", "(imp_ICMSOutraUF)",
    "imp_ICMSOutraUF_CST", "imp_ICMSOutraUF_vBCOutraUF",
    "imp_ICMSOutraUF_pICMSOutraUF", "imp_ICMSOutraUF_vICMSOutraUF",
    "imp_vTotTrib", "imp_infAdFisco",
    "(infCTeNorm)", "infNFe_chave",
    "(infCTeNorm_infCarga)", "infCTeNorm_infCarga_vCarga",
    "infCTeNorm_infCarga_proPred", "(infCTeNorm_infCteSub)",
    "infCTeNorm_infCteSub_chCte", "infCTeNorm_infCteSub_indAlteraToma",
    "(infCTeNorm_infServVinc)", "(infCTeNorm_infServVinc_infCTeMultimodal)",
    "infCTeNorm_infServVinc_infCTeMultimodal_chCTeMultimodal",
    "(infCteComp)", "infCteComp_chCTe"
]

# Set para ignorar as colunas que têm tratamento especial (Impostos e NF-e)
SKIP_COLS: Set[str] = {
    "imp_CST", "imp_vBC", "imp_pICMS", "imp_vICMS",
    "imp_vBCSTRet", "imp_vICMSSTRet", "imp_pICMSSTRet",
    "imp_ICMSOutraUF_CST", "imp_ICMSOutraUF_vBCOutraUF",
    "imp_ICMSOutraUF_pICMSOutraUF", "imp_ICMSOutraUF_vICMSOutraUF",
    "chv_cte_Id", "infNFe_chave"
}

# Cabeçalhos fixos para aba de eventos
EVENT_SHEET_HEADERS: List[str] = [
    "Chave de Acesso (Referência)",
    "Tipo de Evento",
    "Data do Evento",
    "Detalhes / Justificativa"
]

# ==================== UI ====================

WINDOW_TITLE: str = "Conversor de XML para Excel"
WINDOW_SIZE: str = "600x380"
QUEUE_POLL_INTERVAL_MS: int = 100
PROGRESS_UPDATE_INTERVAL: int = 50

# ==================== Excel Styling ====================

GRAY_FILL_COLOR: str = "D3D3D3"
ACCOUNTING_FORMAT: str = '#,##0.00'
MAX_COLUMN_WIDTH: int = 50
EVENT_DETAIL_COL_WIDTH: int = 80
EVENT_KEY_COL_WIDTH: int = 50
