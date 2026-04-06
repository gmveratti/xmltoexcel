# core/excel_exporter.py

import logging
from typing import List, Dict, Any
from datetime import datetime

import openpyxl
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import PatternFill, Font, Alignment

from core.constants import (
    GRAY_FILL_COLOR, ACCOUNTING_FORMAT, MAX_COLUMN_WIDTH,
    EVENT_SHEET_HEADERS, EVENT_DETAIL_COL_WIDTH, EVENT_KEY_COL_WIDTH
)

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Exporta para Excel em fluxo de disco (O(1) memória RAM)."""

    def __init__(self, cte_data: List[Dict[str, Any]], cte_headers: List[str],
                 event_data: List[Dict[str, Any]] = None):
        self.cte_data = cte_data
        self.cte_headers = cte_headers
        self.event_data = event_data or []

    def export(self, output_filename: str):
        if not self.cte_data and not self.event_data:
            raise ValueError("Nenhum dado válido para exportar.")

        # FASE 1: write_only=True despeja os dados no disco em tempo real.
        # Impede o consumo de Gigabytes de RAM em lote massivo.
        wb = openpyxl.Workbook(write_only=True)

        ws_cte = wb.create_sheet(title="CTe Data")
        self._build_cte_sheet(ws_cte)

        if self.event_data:
            ws_events = wb.create_sheet(title="Eventos e Correções")
            self._build_events_sheet(ws_events)

        wb.save(output_filename)
        logger.info("Excel salvo em: %s", output_filename)

    def _build_cte_sheet(self, ws):
        gray_fill = PatternFill(start_color=GRAY_FILL_COLOR, end_color=GRAY_FILL_COLOR, fill_type="solid")
        bold_font = Font(bold=True)
        center_alignment = Alignment(horizontal='center', vertical='center')

        accounting_columns = {
            "vPrest_vTPrest", "vPrest_vRec", "imp_vBC", "imp_pICMS",
            "imp_vICMS", "imp_vBCSTRet", "imp_vICMSSTRet", "imp_pICMSSTRet",
            "imp_ICMSOutraUF_vBCOutraUF", "imp_ICMSOutraUF_pICMSOutraUF",
            "imp_ICMSOutraUF_vICMSOutraUF", "imp_vTotTrib",
        }

        dynamic_cols = sorted({
            key for row in self.cte_data
            for key in row
            if key.startswith("comp_") and key not in self.cte_headers
        })

        final_headers = self.cte_headers + dynamic_cols

        # Larguras padrão de colunas fixadas no Excel
        for idx, _ in enumerate(final_headers, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(idx)].width = 25

        # --- Cabeçalho ---
        header_cells = []
        for header in final_headers:
            cell = WriteOnlyCell(ws, value=header)
            cell.font = bold_font
            cell.alignment = center_alignment
            if header.startswith("(") and header.endswith(")"):
                cell.fill = gray_fill
            header_cells.append(cell)
        ws.append(header_cells)

        # --- Linhas de Dados ---
        for row_data in self.cte_data:
            row_cells = []
            for header in final_headers:
                raw_val = row_data.get(header, "")
                raw_val = str(raw_val).strip() if raw_val is not None else ""
                
                cell = WriteOnlyCell(ws)
                cell.alignment = center_alignment

                if header.startswith("(") and header.endswith(")"):
                    cell.fill = gray_fill
                    row_cells.append(cell)
                    continue

                if header == "ide_dhEmi" and raw_val:
                    try:
                        dt_obj = datetime.fromisoformat(raw_val).replace(tzinfo=None)
                        cell.value = dt_obj
                        cell.number_format = 'DD/MM/YYYY HH:MM:SS'
                    except ValueError:
                        cell.value = raw_val
                        cell.number_format = '@'
                elif header in accounting_columns or header.startswith("comp_"):
                    if raw_val:
                        try:
                            cell.value = float(raw_val)
                            cell.number_format = ACCOUNTING_FORMAT
                        except ValueError:
                            cell.value = raw_val
                            cell.number_format = '@'
                else:
                    cell.value = raw_val
                    cell.number_format = '@'
                
                row_cells.append(cell)
            ws.append(row_cells)

    def _build_events_sheet(self, ws):
        bold_font = Font(bold=True)
        center_alignment = Alignment(horizontal='center', vertical='center')

        ws.column_dimensions['A'].width = EVENT_KEY_COL_WIDTH
        ws.column_dimensions['D'].width = EVENT_DETAIL_COL_WIDTH

        header_cells = []
        for header in EVENT_SHEET_HEADERS:
            cell = WriteOnlyCell(ws, value=header)
            cell.font = bold_font
            cell.alignment = center_alignment
            header_cells.append(cell)
        ws.append(header_cells)

        for row_data in self.event_data:
            row_cells = []
            for header in EVENT_SHEET_HEADERS:
                raw_val = row_data.get(header, "")
                raw_val = str(raw_val).strip() if raw_val is not None else ""
                
                cell = WriteOnlyCell(ws, value=raw_val)
                cell.alignment = center_alignment
                cell.number_format = '@'
                row_cells.append(cell)
            ws.append(row_cells)
