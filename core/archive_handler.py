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
    """Extração recursiva segura com Context Manager contra falhas."""

    def __init__(self, archive_path: str):
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {archive_path}")
        self.archive_path = archive_path
        self.temp_dir = tempfile.mkdtemp(prefix="cte_extraction_")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def _is_safe_path(self, extract_path: str, target_path: str) -> bool:
        """Evita Zip Bomb / Path Traversal malicioso (../)"""
        return os.path.commonpath([os.path.abspath(extract_path), os.path.abspath(target_path)]) == os.path.abspath(extract_path)

    def _extract_recursive(self):
        while True:
            archives_found = False
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    extract_path = os.path.dirname(file_path)
                    try:
                        if file.lower().endswith(".rar"):
                            with rarfile.RarFile(file_path) as rf:
                                for member in rf.infolist():
                                    if self._is_safe_path(extract_path, os.path.join(extract_path, member.filename)):
                                        rf.extract(member, path=extract_path)
                            os.remove(file_path)
                            archives_found = True
                        elif file.lower().endswith(".zip"):
                            with zipfile.ZipFile(file_path) as zf:
                                for member in zf.infolist():
                                    if self._is_safe_path(extract_path, os.path.join(extract_path, member.filename)):
                                        zf.extract(member, path=extract_path)
                            os.remove(file_path)
                            archives_found = True
                    except Exception as e:
                        print(f"Aviso: Falha ao extrair arquivo aninhado '{file}': {e}")
                        os.rename(file_path, file_path + ".failed")
            if not archives_found:
                break

    def extract_all(self):
        print(f"Extraindo arquivo principal: {os.path.basename(self.archive_path)}...")
        try:
            with rarfile.RarFile(self.archive_path) as rf:
                for member in rf.infolist():
                    if self._is_safe_path(self.temp_dir, os.path.join(self.temp_dir, member.filename)):
                        rf.extract(member, path=self.temp_dir)
            self._extract_recursive()
        except rarfile.Error as e:
            raise RuntimeError(f"Falha crítica no UnRAR. Detalhes: {e}")

    def find_xml_files(self) -> List[str]:
        return [os.path.join(root, f) for root, _, files in os.walk(self.temp_dir) for f in files if f.lower().endswith(".xml")]

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except OSError:
                pass
