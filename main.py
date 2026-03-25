import os
import shutil
from tqdm import tqdm

# --- Importações da nossa nova arquitetura modular ---
from core.archive_handler import ArchiveHandler
from core.excel_exporter import ExcelExporter
from core.constants import EXCEL_HEADERS
from parsers.cte_parser import CTeParser

class AppController:
    """Orquestrador principal da aplicação (Pipeline de Dados 2.0)."""
    
    def __init__(self, input_dir: str = "files"):
        self.input_dir = input_dir
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
            print(f"Diretório criado: '{self.input_dir}/'. Por favor, coloque o seu ficheiro .rar lá dentro.")
            exit()

    def run(self):
        print("--- Pipeline de Dados Fiscais 2.0 (CT-e) ---")
        rar_filename = input(f"Introduza o nome do ficheiro .rar (deve estar na pasta '{self.input_dir}/'): ").strip()
        rar_path = os.path.join(self.input_dir, rar_filename)

        if not os.path.exists(rar_path):
            print(f"\nErro: Ficheiro não encontrado em '{rar_path}'.")
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
            print(f"Total de ficheiros XML encontrados: {total_files}")

            all_data = []
            error_details = []

            for xml_file in tqdm(xml_files, desc="A processar XMLs", unit="file"):
                try:
                    # Instancia o nosso parser especializado e extrai os dados
                    parser = CTeParser(xml_file)
                    row_data = parser.extract_data()
                    # Como o CTeParser agora retorna um único dicionário (1 linha por nota), usamos append
                    all_data.append(row_data) 
                except Exception as e:
                    file_name = os.path.basename(xml_file)
                    error_details.append(f"Ficheiro: [{file_name}] | Erro: {str(e)}")
                    # Move o ficheiro defeituoso para a Quarentena
                    try:
                        shutil.copy2(xml_file, os.path.join(error_dir, file_name))
                    except:
                        pass

            # --- RELATÓRIO DE AUDITORIA E FIDELIDADE ---
            print("\n" + "="*50)
            print("         RELATÓRIO DE FIDELIDADE (AUDITORIA)")
            print("="*50)
            print(f"Total de XMLs lidos: {total_files}")
            print(f"Ficheiros processados com sucesso: {total_files - len(error_details)}")
            print(f"Ficheiros com falha (Quarentena): {len(error_details)}")
            print("="*50)

            if error_details:
                log_filename = f"erros_{os.path.splitext(rar_filename)[0]}.log"
                with open(log_filename, "w", encoding="utf-8") as f:
                    f.write("RELATÓRIO DE ERROS DE PROCESSAMENTO - CT-e\n")
                    f.write("=" * 50 + "\n")
                    for err in error_details:
                        f.write(err + "\n")
                print(f"\n* Atenção: Os ficheiros que falharam foram isolados na pasta '{error_dir}'.")
                print(f"* Verifique o ficheiro '{log_filename}' para detalhes.")

            output_filename = f"{os.path.splitext(rar_filename)[0]}.xlsx"
            
            # Passa a responsabilidade de formatação e geração do ficheiro para o Exporter
            exporter = ExcelExporter(all_data, EXCEL_HEADERS)
            exporter.export(output_filename)
            print(f"\nSucesso! Excel guardado como: {output_filename}")

        except Exception as e:
            print(f"\nErro inesperado no processo principal: {e}")
        finally:
            print("\nA limpar ficheiros temporários...")
            archive_handler.cleanup()

if __name__ == "__main__":
    controller = AppController()
    controller.run()