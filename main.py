import os
import shutil
import traceback
import concurrent.futures
from tqdm import tqdm

from core.archive_handler import ArchiveHandler
from core.excel_exporter import ExcelExporter
from core.constants import EXCEL_HEADERS
from parsers.cte_parser import CTeParser

def process_single_xml(xml_file: str):
    """Função isolada para permitir o processamento paralelo seguro."""
    try:
        parser = CTeParser(xml_file)
        row_data = parser.extract_data()
        return row_data, None
    except Exception as e:
        # Pega a linha exata e o erro detalhado para escrever no .txt
        error_trace = traceback.format_exc()
        return None, (xml_file, str(e), error_trace)

class AppController:
    """Orquestrador principal da aplicação (Pipeline de Dados 2.0)."""
    
    def __init__(self, input_dir: str = "files"):
        self.input_dir = input_dir
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
            print(f"Diretório criado: '{self.input_dir}/'. Por favor, coloque o seu arquivo .rar lá dentro.")
            exit()

    def run(self):
        print("--- Pipeline de Dados Fiscais 2.0 (CT-e) ---")
        rar_filename = input(f"Introduza o nome do arquivo .rar (deve estar na pasta '{self.input_dir}/'): ").strip()
        rar_path = os.path.join(self.input_dir, rar_filename)

        if not os.path.exists(rar_path):
            print(f"\nErro: Arquivo não encontrado em '{rar_path}'.")
            return

        archive_handler = ArchiveHandler(rar_path)
        
        # Pasta de Quarentena para XMLs Corrompidos
        error_dir = os.path.join(self.input_dir, "erros_quarentena")
        if not os.path.exists(error_dir):
            os.makedirs(error_dir)

        try:
            archive_handler.extract_all()
            xml_files = archive_handler.find_xml_files()
            total_files = len(xml_files)
            print(f"Total de arquivos XML encontrados: {total_files}")
            print("Iniciando processamento paralelo em Alta Velocidade...")

            all_data = []
            error_details = []

            # --- MULTITHREADING (Uso de Múltiplos Núcleos do CPU) ---
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_xml = {executor.submit(process_single_xml, xml): xml for xml in xml_files}
                
                for future in tqdm(concurrent.futures.as_completed(future_to_xml), total=total_files, desc="Processando XMLs"):
                    row_data, error_info = future.result()
                    
                    if row_data:
                        all_data.append(row_data)
                    
                    if error_info:
                        xml_file, error_msg, error_trace = error_info
                        file_name = os.path.basename(xml_file)
                        error_details.append(f"Arquivo: [{file_name}] | Erro: {error_msg}")
                        
                        # --- QUARENTENA INTELIGENTE COM LOG EM .TXT ---
                        try:
                            # 1. Copia o XML problemático
                            shutil.copy2(xml_file, os.path.join(error_dir, file_name))
                            
                            # 2. Cria o arquivo .txt com os detalhes do erro
                            txt_name = f"{os.path.splitext(file_name)[0]}_LOG_ERRO.txt"
                            with open(os.path.join(error_dir, txt_name), "w", encoding="utf-8") as f:
                                f.write(f"--- RELATÓRIO DE FALHA DE EXTRAÇÃO ---\n")
                                f.write(f"Arquivo: {file_name}\n")
                                f.write(f"Erro Principal: {error_msg}\n\n")
                                f.write(f"Stack Trace Técnico:\n{error_trace}\n")
                                
                        except Exception as copy_err:
                            # Adeus 'pass' silencioso!
                            error_details.append(f"Erro fatal: Não foi possível mover '{file_name}' para a quarentena. Motivo: {copy_err}")

            # --- RELATÓRIO DE AUDITORIA E FIDELIDADE ---
            print("\n" + "="*50)
            print("         RELATÓRIO DE FIDELIDADE (AUDITORIA)")
            print("="*50)
            print(f"Total de XMLs lidos: {total_files}")
            print(f"Arquivos processados com sucesso: {total_files - len(error_details)}")
            print(f"Arquivos com falha (Quarentena): {len(error_details)}")
            print("="*50)

            if error_details:
                log_filename = f"erros_{os.path.splitext(rar_filename)[0]}.log"
                with open(log_filename, "w", encoding="utf-8") as f:
                    f.write("RELATÓRIO GERAL DE ERROS DE PROCESSAMENTO\n")
                    f.write("=" * 50 + "\n")
                    for err in error_details:
                        f.write(err + "\n")
                print(f"\n* Atenção: Os arquivos falhos e seus logs em .txt foram isolados na pasta '{error_dir}'.")
                print(f"* O arquivo resumo '{log_filename}' foi gerado na raiz.")

            output_filename = f"{os.path.splitext(rar_filename)[0]}.xlsx"
            exporter = ExcelExporter(all_data, EXCEL_HEADERS)
            exporter.export(output_filename)
            print(f"\nSucesso! Excel salvo como: {output_filename}")

        except Exception as e:
            print(f"\nErro inesperado no processo principal: {e}")
        finally:
            print("\nLimpando arquivos temporários...")
            archive_handler.cleanup()

if __name__ == "__main__":
    controller = AppController()
    controller.run()