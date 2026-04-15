# core/archive_handler.py

import os
import sys
import shutil
import tempfile
import zipfile
import rarfile
import logging
from typing import List

logger = logging.getLogger(__name__)

# FASE 3: LÓGICA DE PORTABILIDADE (PLUG AND PLAY)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UNRAR_PATH = os.path.join(BASE_DIR, "bin", "UnRAR.exe")

if os.path.exists(UNRAR_PATH):
    rarfile.UNRAR_TOOL = UNRAR_PATH
elif os.name == 'nt' and os.path.exists(r"C:\Program Files\WinRAR\UnRAR.exe"):
    rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe"

class ArchiveHandler:
    """Manipulação e extração recursiva segura de arquivos compactados e pastas."""

    def __init__(self, archive_path: str):
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Caminho não encontrado: {archive_path}")
        self.archive_path = archive_path
        self.temp_dir = tempfile.mkdtemp(prefix="xmltoexcel_extraction_")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def _is_safe_path(self, extract_path: str, target_path: str) -> bool:
        """Evita Zip Bomb / Path Traversal malicioso (../)"""
        return os.path.commonpath(
            [os.path.abspath(extract_path), os.path.abspath(target_path)]
        ) == os.path.abspath(extract_path)

    # FASE 3: DRY - Método centralizado para extrair tanto zip quanto rar
    def _process_archive(self, archive_obj, extract_path: str):
        """Extrai um objeto de arquivo (ZipFile ou RarFile) em segurança."""
        for member in archive_obj.infolist():
            if self._is_safe_path(extract_path, os.path.join(extract_path, member.filename)):
                archive_obj.extract(member, path=extract_path)

    def _extract_recursive(self):
        while True:
            archives_found = False
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    extract_path = os.path.dirname(file_path)
                    
                    try:
                        file_lower = file.lower()
                        if file_lower.endswith(".rar"):
                            with rarfile.RarFile(file_path) as rf:
                                self._process_archive(rf, extract_path)
                            os.remove(file_path)
                            archives_found = True
                            
                        elif file_lower.endswith(".zip"):
                            with zipfile.ZipFile(file_path) as zf:
                                self._process_archive(zf, extract_path)
                            os.remove(file_path)
                            archives_found = True
                            
                    except Exception as e:
                        logger.warning("Falha ao extrair arquivo aninhado '%s': %s", file, e)
                        try:
                            os.rename(file_path, file_path + ".failed")
                        except OSError:
                            pass
            if not archives_found:
                break

    def extract_all(self):
        """Prepara o diretório e inicia a extração em cascata."""
        logger.info("Preparando origem de dados: %s", os.path.basename(self.archive_path))
        try:
            if os.path.isdir(self.archive_path):
                shutil.copytree(self.archive_path, self.temp_dir, dirs_exist_ok=True)
            else:
                ext = self.archive_path.lower()
                if ext.endswith('.zip'):
                    with zipfile.ZipFile(self.archive_path) as zf:
                        self._process_archive(zf, self.temp_dir)
                elif ext.endswith('.rar'):
                    with rarfile.RarFile(self.archive_path) as rf:
                        self._process_archive(rf, self.temp_dir)
                else:
                    raise ValueError("O arquivo principal precisa ser .rar ou .zip")

            self._extract_recursive()

        except zipfile.BadZipFile as e:
            raise RuntimeError(f"O ficheiro ZIP parece corrompido: {e}")
        except rarfile.Error as e:
            raise RuntimeError(f"Falha no UnRAR (verifique se está instalado): {e}")

    def find_xml_files(self) -> List[str]:
        return [
            os.path.join(root, f)
            for root, _, files in os.walk(self.temp_dir)
            for f in files if f.lower().endswith(".xml")
        ]

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except OSError as e:
                logger.warning("Erro ao limpar diretório temporário: %s", e)
