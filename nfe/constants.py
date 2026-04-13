# nfe/constants.py
from typing import List, Set

NFE_NAMESPACE: str = "http://www.portalfiscal.inf.br/nfe"

# Mapeamento 1:1 rigoroso conforme o CSV, com os separadores em Cinza (parênteses)
NFE_HEADERS: List[str] = [
    "(Identificação)", "chv_nfe_Id",
    "(ide)", "ide_cUF", "ide_cNF", "ide_natOp", "ide_mod", "ide_serie", "ide_nNF", "ide_dhEmi", 
    "ide_tpNF", "ide_idDest", "ide_cMunFG", "ide_tpImp", "ide_tpEmis", "ide_cDV", "ide_tpAmb", 
    "ide_finNFe", "ide_indFinal", "ide_indPres", "ide_indIntermed", "ide_procEmi", "ide_verProc",
    "(emit)", "emit_CNPJ", "emit_CPF", "emit_xNome", "emit_xFant", 
    "(emit_enderEmit)", "emit_enderEmit_xLgr", "emit_enderEmit_nro", "emit_enderEmit_xCpl", 
    "emit_enderEmit_xBairro", "emit_enderEmit_cMun", "emit_enderEmit_xMun", "emit_enderEmit_UF", 
    "emit_enderEmit_CEP", "emit_enderEmit_cPais", "emit_enderEmit_xPais", "emit_enderEmit_fone", 
    "emit_IE", "emit_CRT",
    "(dest)", "dest_CNPJ", "dest_CPF", "dest_xNome", 
    "(dest_enderDest)", "dest_enderDest_xLgr", "dest_enderDest_nro", "dest_enderDest_xCpl", 
    "dest_enderDest_xBairro", "dest_enderDest_cMun", "dest_enderDest_xMun", "dest_enderDest_UF", 
    "dest_enderDest_CEP", "dest_enderDest_cPais", "dest_enderDest_xPais", "dest_enderDest_fone", 
    "dest_indIEDest", "dest_IE", "dest_email",
    "(det)", "det_nItem", 
    "(prod)", "prod_cProd", "prod_cEAN", "prod_xProd", "prod_NCM", "prod_CEST", "prod_indEscala", 
    "prod_CFOP", "prod_uCom", "prod_qCom", "prod_vUnCom", "prod_vProd", "prod_cEANTrib", 
    "prod_uTrib", "prod_qTrib", "prod_vUnTrib", "prod_vFrete", "prod_vSeg", "prod_vDesc", 
    "prod_vOutro", "prod_indTot", "prod_xPed", "prod_nItemPed", "prod_nFCI",
    "(imposto)", "imposto_vTotTrib",
    "(ICMS)", "ICMS_CST", "ICMS_CSOSN", "ICMS_orig", "ICMS_vBC", "ICMS_pICMS", "ICMS_vICMS", 
    "ICMS_vBCST", "ICMS_pICMSST", "ICMS_vICMSST", "ICMS_pRedBC",
    "(IPI)", "IPI_CST", "IPI_vBC", "IPI_pIPI", "IPI_vIPI",
    "(PIS)", "PIS_CST", "PIS_vBC", "PIS_pPIS", "PIS_vPIS",
    "(COFINS)", "COFINS_CST", "COFINS_vBC", "COFINS_pCOFINS", "COFINS_vCOFINS",
    "(total)", "total_ICMSTot_vBC", "total_ICMSTot_vICMS", "total_ICMSTot_vICMSDeson", 
    "total_ICMSTot_vFCP", "total_ICMSTot_vBCST", "total_ICMSTot_vST", "total_ICMSTot_vFCPST", 
    "total_ICMSTot_vFCPSTRet", "total_ICMSTot_vProd", "total_ICMSTot_vFrete", "total_ICMSTot_vSeg", 
    "total_ICMSTot_vDesc", "total_ICMSTot_vII", "total_ICMSTot_vIPI", "total_ICMSTot_vIPIDevol", 
    "total_ICMSTot_vPIS", "total_ICMSTot_vCOFINS", "total_ICMSTot_vOutro", "total_ICMSTot_vNF",
    "(transp)", "transp_modFrete", "transp_transporta_CNPJ", "transp_transporta_CPF", "transp_transporta_xNome",
    "(cobr)", "cobr_fat_nFat", "cobr_fat_vOrig", "cobr_fat_vDesc", "cobr_fat_vLiq",
    "(pag)", "pag_detPag_tPag", "pag_detPag_vPag",
    "(infAdic)", "infAdic_infAdFisco", "infAdic_infCpl"
]

NFE_ACCOUNTING_COLUMNS: Set[str] = {
    "prod_vUnCom", "prod_vProd", "prod_vUnTrib", "imposto_vTotTrib",
    "ICMS_vBC", "ICMS_vICMS", "IPI_vBC", "IPI_vIPI", "PIS_vBC", "PIS_vPIS", "COFINS_vBC", "COFINS_vCOFINS",
    "total_ICMSTot_vBC", "total_ICMSTot_vICMS", "total_ICMSTot_vProd", "total_ICMSTot_vFrete", "total_ICMSTot_vNF",
    "cobr_fat_vOrig", "cobr_fat_vDesc", "cobr_fat_vLiq", "pag_detPag_vPag", "prod_qCom"
}
