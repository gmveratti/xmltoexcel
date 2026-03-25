# core/excel_exporter.py

import re
import pandas as pd
from typing import List, Dict, Any
from openpyxl.styles import PatternFill, Font

def format_accounting_numbers(val):
    """Regex que encontra valores numéricos e formata o Ponto (.) para Vírgula (,)."""
    if isinstance(val, str) and val:
        # Se o texto for exatamente um número com casas decimais (ex: 15.30 ou -0.50)
        if re.match(r'^-?\d+\.\d{1,4}$', val.strip()):
            return val.strip().replace('.', ',')
    return val

class ExcelExporter:
    """Exporta os dados parseados para um arquivo Excel estilizado."""
    
    def __init__(self, data: List[Dict[str, Any]], base_headers: List[str]):
        self.data = data
        self.base_headers = base_headers

    def export(self, output_filename: str):
        if not self.data:
            return
        print(f"Gerando arquivo Excel: {output_filename}...")

        # Converte a lista de dicionários para um DataFrame do Pandas
        df = pd.DataFrame(self.data)

        # 1. TRATAMENTO DE COLUNAS DINÂMICAS (Componentes do Frete)
        # O parser gera tags como "comp_VALOR_FRETE" que não estão no cabeçalho base.
        # Precisamos identificar essas colunas novas e anexá-las no final do arquivo.
        dynamic_cols = [col for col in df.columns if col not in self.base_headers and col.startswith("comp_")]
        final_headers = self.base_headers + dynamic_cols

        # Reordena o dataframe e preenche células vazias
        df = df.reindex(columns=final_headers, fill_value="")

        # 2. SANITIZAÇÃO CONTÁBIL
        # Aplica a formatação de números (Ponto para Vírgula) em todas as colunas
        for col in df.columns:
            df[col] = df[col].apply(format_accounting_numbers)

        # 3. EXPORTAÇÃO E ESTILIZAÇÃO COM OPENPYXL
        with pd.ExcelWriter(output_filename, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="CTe Data")
            ws = writer.sheets["CTe Data"]

            gray_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            bold_font = Font(bold=True)

            for col_idx, header_text in enumerate(final_headers, 1):
                # Deixa o cabeçalho em Negrito
                ws.cell(row=1, column=col_idx).font = bold_font
                
                # Se o nome da coluna estiver entre parênteses (ex: "(ide)"), pinta de cinza
                if header_text.startswith("(") and header_text.endswith(")"):
                    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=col_idx, max_col=col_idx):
                        for cell in row:
                            cell.fill = gray_fill
