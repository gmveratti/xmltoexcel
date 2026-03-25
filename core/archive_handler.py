# core/archive_handler.py

import os
import shutil
import tempfile
import zipfile
import rarfile
from typing import List

# Configura o caminho do UnRAR no Windows se ele existir
if os.name == 'nt':
    unrar_path = r"C:\Program Files\WinRAR\UnRAR.exe"
    if os.path.exists(unrar_path):
        rarfile.UNRAR_TOOL = unrar_path

class ArchiveHandler:
    """Lida com a extração recursiva de arquivos .rar e .zip e busca de XMLs."""

    def __init__(self, archive_path: str):
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {archive_path}")
        self.archive_path = archive_path
        self.temp_dir = tempfile.mkdtemp(prefix="cte_extraction_")

    def _extract_recursive(self):
        """Busca e extrai arquivos compactados dentro da pasta temporária até que não reste nenhum."""
        while True:
            archives_found = False
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    extract_path = os.path.dirname(file_path)
                    try:
                        if file.lower().endswith(".rar"):
                            with rarfile.RarFile(file_path) as rf:
                                rf.extractall(path=extract_path)
                            os.remove(file_path)
                            archives_found = True
                        elif file.lower().endswith(".zip"):
                            with zipfile.ZipFile(file_path) as zf:
                                zf.extractall(path=extract_path)
                            os.remove(file_path)
                            archives_found = True
                    except Exception:
                        os.rename(file_path, file_path + ".failed")
            if not archives_found:
                break

    def extract_all(self):
        """Ponto de entrada para a extração do arquivo principal."""
        print(f"Extraindo arquivo principal: {os.path.basename(self.archive_path)}...")
        try:
            with rarfile.RarFile(self.archive_path) as rf:
                rf.extractall(path=self.temp_dir)
            print("Escaneando por arquivos compactados aninhados...")
            self._extract_recursive()
        except rarfile.Error as e:
            raise RuntimeError(f"Falha ao extrair RAR. Verifique se o 'unrar' está instalado. Detalhes: {e}")

    def find_xml_files(self) -> List[str]:
        """Varre a pasta temporária e retorna uma lista com o caminho de todos os .xml encontrados."""
        xml_files = []
        for root, _, files in os.walk(self.temp_dir):
            for file in files:
                if file.lower().endswith(".xml"):
                    xml_files.append(os.path.join(root, file))
        return xml_files

    def cleanup(self):
        """Remove a pasta temporária do disco para liberar espaço."""
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except OSError as e:
                print(f"Aviso: Não foi possível limpar a pasta temporária {self.temp_dir}: {e}")
