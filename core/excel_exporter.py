# core/excel_exporter.py

import re
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import PatternFill, Font

def format_accounting_numbers(val):
    """Regex que encontra valores numéricos e formata o Ponto (.) para Vírgula (,)."""
    if isinstance(val, str) and val:
        if re.match(r'^-?\d+\.\d{1,4}$', val.strip()):
            return val.strip().replace('.', ',')
    return val

class ExcelExporter:
    """Exporta para Excel usando APENAS openpyxl (Zero Pandas = -100MB de peso)."""
    
    def __init__(self, data: List[Dict[str, Any]], base_headers: List[str]):
        self.data = data
        self.base_headers = base_headers

    def export(self, output_filename: str):
        if not self.data:
            print("Aviso: Nenhum dado para exportar.")
            return
            
        print(f"Gerando arquivo Excel ({len(self.data)} linhas): {output_filename}...")

        # Coleta colunas dinâmicas criadas em tempo de execução
        dynamic_cols = set()
        for row in self.data:
            for key in row.keys():
                if key not in self.base_headers and key.startswith("comp_"):
                    dynamic_cols.add(key)
        
        final_headers = self.base_headers + sorted(list(dynamic_cols))

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "CTe Data"

        gray_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
        bold_font = Font(bold=True)

        # Escreve o Cabeçalho
        for col_idx, header in enumerate(final_headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = bold_font
            if header.startswith("(") and header.endswith(")"):
                cell.fill = gray_fill

        # Escreve os Dados (O(N) Alta performance)
        for row_idx, row_data in enumerate(self.data, 2):
            for col_idx, header in enumerate(final_headers, 1):
                val = row_data.get(header, "")
                
                # Só roda a Regex em colunas que sabemos que podem ter números (Economia de CPU)
                if val and (header.startswith("imp_") or header.startswith("vPrest_") or header.startswith("comp_")):
                    val = format_accounting_numbers(val)
                
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                if header.startswith("(") and header.endswith(")"):
                    cell.fill = gray_fill

        wb.save(output_filename)
