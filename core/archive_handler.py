# core/archive_handler.py

import logging
import os
import shutil
import tempfile
import zipfile
from collections import deque
from pathlib import Path
from typing import List

import rarfile

logger = logging.getLogger(__name__)

# Configura o caminho do UnRAR no Windows se ele existir
if os.name == 'nt':
    unrar_path = r"C:\Program Files\WinRAR\UnRAR.exe"
    if os.path.exists(unrar_path):
        rarfile.UNRAR_TOOL = unrar_path

_ARCHIVE_EXTENSIONS = ('.rar', '.zip')


class ArchiveHandler:
    """Extração recursiva segura com Context Manager contra falhas."""

    def __init__(self, archive_path: str):
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Arquivo ou pasta não encontrado(a): {archive_path}")
        self.archive_path = archive_path
        self.temp_dir = tempfile.mkdtemp(prefix="cte_extraction_")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def _is_safe_path(self, extract_path: str, target_path: str) -> bool:
        """Evita Zip Bomb / Path Traversal malicioso (../)"""
        abs_extract = os.path.abspath(extract_path)
        abs_target = os.path.abspath(target_path)
        return os.path.commonpath([abs_extract, abs_target]) == abs_extract

    def _extract_single_archive(self, file_path: str, extract_path: str) -> List[str]:
        """Extrai um único arquivo e retorna novos archives encontrados."""
        new_archives = []
        try:
            if file_path.lower().endswith(".rar"):
                with rarfile.RarFile(file_path) as rf:
                    for member in rf.infolist():
                        if self._is_safe_path(extract_path, os.path.join(extract_path, member.filename)):
                            rf.extract(member, path=extract_path)
                            if member.filename.lower().endswith(_ARCHIVE_EXTENSIONS):
                                new_archives.append(os.path.join(extract_path, member.filename))
            elif file_path.lower().endswith(".zip"):
                with zipfile.ZipFile(file_path) as zf:
                    for member in zf.infolist():
                        if self._is_safe_path(extract_path, os.path.join(extract_path, member.filename)):
                            zf.extract(member, path=extract_path)
                            if member.filename.lower().endswith(_ARCHIVE_EXTENSIONS):
                                new_archives.append(os.path.join(extract_path, member.filename))
            os.remove(file_path)
        except Exception as e:
            logger.warning("Falha ao extrair arquivo aninhado '%s': %s", os.path.basename(file_path), e)
            try:
                os.rename(file_path, file_path + ".failed")
            except OSError:
                pass
        return new_archives

    def _extract_recursive(self):
        """Extração recursiva usando fila (deque) em vez de os.walk() repetido."""
        archive_queue: deque = deque()

        # Popular fila com archives encontrados na extração inicial
        for root, _, files in os.walk(self.temp_dir):
            for f in files:
                if f.lower().endswith(_ARCHIVE_EXTENSIONS):
                    archive_queue.append(os.path.join(root, f))

        while archive_queue:
            file_path = archive_queue.popleft()
            if not os.path.exists(file_path):
                continue
            extract_path = os.path.dirname(file_path)
            new_archives = self._extract_single_archive(file_path, extract_path)
            archive_queue.extend(new_archives)

    def extract_all(self):
        """Extrai o arquivo principal ou copia a pasta e processa recursivamente."""
        logger.info("Processando origem: %s", os.path.basename(self.archive_path))
        try:
            if os.path.isdir(self.archive_path):
                # Se for diretório, copia todo o conteúdo para self.temp_dir
                shutil.copytree(self.archive_path, self.temp_dir, dirs_exist_ok=True)
            else:
                if self.archive_path.lower().endswith('.zip'):
                    with zipfile.ZipFile(self.archive_path) as zf:
                        for member in zf.infolist():
                            if self._is_safe_path(self.temp_dir, os.path.join(self.temp_dir, member.filename)):
                                zf.extract(member, path=self.temp_dir)
                else:
                    with rarfile.RarFile(self.archive_path) as rf:
                        for member in rf.infolist():
                            if self._is_safe_path(self.temp_dir, os.path.join(self.temp_dir, member.filename)):
                                rf.extract(member, path=self.temp_dir)
            
            # Chamada recursiva para extrair archives aninhados (mesmo se a origem for pasta)
            self._extract_recursive()
        except zipfile.BadZipFile as e:
            raise RuntimeError(f"Falha ao ler arquivo ZIP: {e}") from e
        except rarfile.Error as e:
            raise RuntimeError(f"Falha crítica no UnRAR. Detalhes: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Falha no processamento da origem. Detalhes: {e}") from e

    def find_xml_files(self) -> List[str]:
        """Busca todos os arquivos XML no diretório temporário."""
        return [str(p) for p in Path(self.temp_dir).rglob("*.xml")]

    def cleanup(self):
        """Remove o diretório temporário de extração."""
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except OSError as e:
                logger.warning("Não foi possível limpar diretório temporário '%s': %s", self.temp_dir, e)
