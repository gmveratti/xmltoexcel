# core/excel_exporter.py

import logging
from typing import List, Dict, Any

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment

from core.constants import (
    GRAY_FILL_COLOR, ACCOUNTING_FORMAT, MAX_COLUMN_WIDTH,
    EVENT_SHEET_HEADERS, EVENT_DETAIL_COL_WIDTH, EVENT_KEY_COL_WIDTH
)

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Exporta para Excel separando Notas e Eventos em abas distintas."""

    def __init__(self, cte_data: List[Dict[str, Any]], cte_headers: List[str],
                 event_data: List[Dict[str, Any]] = None):
        self.cte_data = cte_data
        self.cte_headers = cte_headers
        self.event_data = event_data or []

    def export(self, output_filename: str):
        """Gera o arquivo Excel. Levanta ValueError se não houver dados."""
        if not self.cte_data and not self.event_data:
            raise ValueError("Nenhum dado válido para exportar.")

        wb = openpyxl.Workbook()

        # --- ABA 1: CT-E DATA ---
        ws_cte = wb.active
        ws_cte.title = "CTe Data"
        self._build_cte_sheet(ws_cte)

        # --- ABA 2: EVENTOS (Se existirem) ---
        if self.event_data:
            ws_events = wb.create_sheet(title="Eventos e Correções")
            self._build_events_sheet(ws_events)

        wb.save(output_filename)
        logger.info("Excel salvo em: %s", output_filename)

    def _build_cte_sheet(self, ws):
        gray_fill = PatternFill(start_color=GRAY_FILL_COLOR, end_color=GRAY_FILL_COLOR, fill_type="solid")
        bold_font = Font(bold=True)
        
        # 1. Alinhamento Global (Horizontal e Vertical centralizado)
        center_alignment = Alignment(horizontal='center', vertical='center')

        # 3. Colunas de Valor Contábil (Moeda/Decimal)
        accounting_columns = {
            "vPrest_vTPrest", "vPrest_vRec", "imp_vBC", "imp_pICMS",
            "imp_vICMS", "imp_vBCSTRet", "imp_vICMSSTRet", "imp_pICMSSTRet",
            "imp_ICMSOutraUF_vBCOutraUF", "imp_ICMSOutraUF_pICMSOutraUF",
            "imp_ICMSOutraUF_vICMSOutraUF", "imp_vTotTrib", 
            "comp_FRETE_VALOR", "comp_IMPOSTOS", "comp_PEDAGIO",
            "comp_VALOR_FRETE", "comp_VALOR_ICMS", "comp_VALOR_PEDAGIO"
        }

        # Descobrir colunas dinâmicas com set comprehension otimizado (restrição: NÃO alterar)
        dynamic_cols = sorted({
            key for row in self.cte_data
            for key in row
            if key.startswith("comp_") and key not in self.cte_headers
        })

        final_headers = self.cte_headers + dynamic_cols

        # Escrever cabeçalhos
        for col_idx, header in enumerate(final_headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = bold_font
            cell.alignment = center_alignment # Alinhamento Global
            
            # (Restrição) Manter preenchimento cinza para identificadores de grupo
            if header.startswith("(") and header.endswith(")"):
                cell.fill = gray_fill

        # Escrever dados
        for row_idx, row_data in enumerate(self.cte_data, 2):
            for col_idx, header in enumerate(final_headers, 1):
                raw_val = row_data.get(header, "")
                if raw_val is not None:
                    raw_val = str(raw_val).strip()
                else:
                    raw_val = ""
                    
                cell = ws.cell(row=row_idx, column=col_idx)
                
                # Alinhamento Global
                cell.alignment = center_alignment

                # (Restrição) Agrupamentos mantêm o cinza e são pulados
                if header.startswith("(") and header.endswith(")"):
                    cell.fill = gray_fill
                    continue

                # 3. Colunas de Valor Contábil -> Cast para float e tipagem com accounting format
                if header in accounting_columns:
                    if raw_val:
                        try:
                            cell.value = float(raw_val)
                            cell.number_format = ACCOUNTING_FORMAT
                        except ValueError:
                            # Fallback para string em caso de formatação suja (texto irrecusável)
                            cell.value = raw_val
                            cell.number_format = '@'
                # 4. Colunas de Texto Estrito (Todo o Restante) -> Cast forçado para String ('@')
                else:
                    cell.value = raw_val
                    cell.number_format = '@'

        # Auto-ajuste de largura de colunas
        self._auto_adjust_columns(ws)

    def _build_events_sheet(self, ws):
        bold_font = Font(bold=True)
        center_alignment = Alignment(horizontal='center', vertical='center')

        for col_idx, header in enumerate(EVENT_SHEET_HEADERS, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = bold_font
            cell.alignment = center_alignment

        for row_idx, row_data in enumerate(self.event_data, 2):
            for col_idx, header in enumerate(EVENT_SHEET_HEADERS, 1):
                raw_val = row_data.get(header, "")
                if raw_val is not None:
                    raw_val = str(raw_val).strip()
                else:
                    raw_val = ""
                    
                cell = ws.cell(row=row_idx, column=col_idx, value=raw_val)
                cell.alignment = center_alignment
                cell.number_format = '@' # Aba de eventos tem formato de texto explícito (datas longas, texto bruto)

        # Ajusta a largura das colunas de detalhes e chave
        ws.column_dimensions['A'].width = EVENT_KEY_COL_WIDTH
        ws.column_dimensions['D'].width = EVENT_DETAIL_COL_WIDTH

    @staticmethod
    def _auto_adjust_columns(ws):
        """Auto-ajusta a largura de todas as colunas baseado no conteúdo."""
        for column_cells in ws.columns:
            max_length = 0
            for cell in column_cells:
                try:
                    cell_length = len(str(cell.value or ""))
                    if cell_length > max_length:
                        max_length = cell_length
                except (TypeError, AttributeError):
                    pass
            col_letter = column_cells[0].column_letter
            ws.column_dimensions[col_letter].width = min(max_length + 2, MAX_COLUMN_WIDTH)
