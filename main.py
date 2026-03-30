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
    """Função global obrigatória para o ProcessPoolExecutor (Pickling)."""
    try:
        parser = CTeParser(xml_file)
        row_data = parser.extract_data()
        return row_data, None
    except Exception as e:
        return None, (xml_file, str(e), traceback.format_exc())

class AppController:
    def __init__(self, input_dir: str = "files"):
        self.input_dir = input_dir
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
            print(f"Diretório criado: '{self.input_dir}/'. Coloque os arquivos .rar lá.")

    def run(self):
        print("--- Pipeline de Dados Fiscais 2.0 (CT-e) ---")
        rar_filename = input(f"Nome do arquivo .rar (na pasta '{self.input_dir}/'): ").strip()
        rar_path = os.path.join(self.input_dir, rar_filename)

        if not os.path.exists(rar_path):
            print(f"\nErro: Arquivo não encontrado em '{rar_path}'.")
            return

        error_dir = os.path.join(self.input_dir, "erros_quarentena")
        os.makedirs(error_dir, exist_ok=True)

        # Uso do Context Manager garante a exclusão dos arquivos temporários
        with ArchiveHandler(rar_path) as archive_handler:
            try:
                archive_handler.extract_all()
                xml_files = archive_handler.find_xml_files()
                total_files = len(xml_files)
                print(f"Total de arquivos XML encontrados: {total_files}")
                print("Iniciando Multiprocessamento (Verdadeiro uso de Múltiplos Núcleos)...")

                all_data = []
                error_details = []

                # Trocado para ProcessPoolExecutor (Bypassa o GIL do Python)
                with concurrent.futures.ProcessPoolExecutor() as executor:
                    future_to_xml = {executor.submit(process_single_xml, xml): xml for xml in xml_files}
                    
                    for future in tqdm(concurrent.futures.as_completed(future_to_xml), total=total_files, desc="Processando XMLs"):
                        row_data, error_info = future.result()
                        
                        if row_data is not None:
                            all_data.append(row_data)
                        
                        if error_info is not None:
                            xml_file, error_msg, error_trace = error_info
                            file_name = os.path.basename(xml_file)
                            error_details.append(f"Arquivo: [{file_name}] | Erro: {error_msg}")
                            
                            try:
                                shutil.copy2(xml_file, os.path.join(error_dir, file_name))
                                with open(os.path.join(error_dir, f"{os.path.splitext(file_name)[0]}_LOG.txt"), "w") as f:
                                    f.write(f"Arquivo: {file_name}\nErro: {error_msg}\n\nTrace:\n{error_trace}\n")
                            except Exception as copy_err:
                                error_details.append(f"FALHA FATAL: Não foi possível mover '{file_name}' para quarentena. Motivo: {copy_err}")

                # Relatório
                print("\n" + "="*50)
                print("         RELATÓRIO DE FIDELIDADE (AUDITORIA)")
                print("="*50)
                failed_count = len([e for e in error_details if not e.startswith("FALHA FATAL")])
                print(f"Total de XMLs lidos: {total_files}")
                print(f"Arquivos processados com sucesso: {total_files - failed_count}")
                print(f"Arquivos com falha (Quarentena): {failed_count}")
                print("="*50)

                if error_details:
                    log_filename = f"erros_{os.path.splitext(rar_filename)[0]}.log"
                    with open(log_filename, "w", encoding="utf-8") as f:
                        f.write("\n".join(error_details))
                    print(f"\n* Atenção: Os arquivos falhos estão na pasta '{error_dir}'.")

                output_filename = f"{os.path.splitext(rar_filename)[0]}.xlsx"
                ExcelExporter(all_data, EXCEL_HEADERS).export(output_filename)
                print(f"\nSucesso! Excel salvo como: {output_filename}")

            except Exception as e:
                print(f"\nErro inesperado no processo principal: {e}")

if __name__ == "__main__":
    controller = AppController()
    if os.path.exists(controller.input_dir):
        controller.run()