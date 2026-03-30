# core/excel_exporter.py

from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import PatternFill, Font

class ExcelExporter:
    """Exporta para Excel separando Notas e Eventos em abas distintas."""
    
    def __init__(self, cte_data: List[Dict[str, Any]], cte_headers: List[str], event_data: List[Dict[str, Any]] = None):
        self.cte_data = cte_data
        self.cte_headers = cte_headers
        self.event_data = event_data or []

    def export(self, output_filename: str):
        if not self.cte_data and not self.event_data:
            print("Aviso: Nenhum dado válido para exportar.")
            return

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

    def _build_cte_sheet(self, ws):
        gray_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
        bold_font = Font(bold=True)
        accounting_format = '#,##0.00'

        dynamic_cols = set()
        for row in self.cte_data:
            for key in row.keys():
                if key not in self.cte_headers and key.startswith("comp_"):
                    dynamic_cols.add(key)
        
        final_headers = self.cte_headers + sorted(list(dynamic_cols))

        for col_idx, header in enumerate(final_headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = bold_font
            if header.startswith("(") and header.endswith(")"):
                cell.fill = gray_fill

        for row_idx, row_data in enumerate(self.cte_data, 2):
            for col_idx, header in enumerate(final_headers, 1):
                raw_val = row_data.get(header, "")
                cell = ws.cell(row=row_idx, column=col_idx)
                
                if header.startswith("(") and header.endswith(")"):
                    cell.fill = gray_fill
                    continue

                if raw_val and (header.startswith("imp_") or header.startswith("vPrest_") or header.startswith("comp_")):
                    try:
                        cell.value = float(raw_val.strip())
                        cell.number_format = accounting_format
                    except ValueError:
                        cell.value = raw_val
                else:
                    cell.value = raw_val

    def _build_events_sheet(self, ws):
        bold_font = Font(bold=True)
        # Cabeçalhos fixos para eventos
        headers = ["Chave de Acesso (Referência)", "Tipo de Evento", "Data do Evento", "Detalhes / Justificativa"]
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = bold_font

        for row_idx, row_data in enumerate(self.event_data, 2):
            for col_idx, header in enumerate(headers, 1):
                ws.cell(row=row_idx, column=col_idx, value=row_data.get(header, ""))
                
        # Ajusta a largura da coluna de detalhes
        ws.column_dimensions['D'].width = 80
        ws.column_dimensions['A'].width = 50
