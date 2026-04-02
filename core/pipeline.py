# core/pipeline.py

import logging
import os
import shutil
import concurrent.futures
import queue
import threading
from typing import List, Dict, Any

from core.archive_handler import ArchiveHandler
from core.excel_exporter import ExcelExporter
from core.constants import EXCEL_HEADERS, PROGRESS_UPDATE_INTERVAL
from core.models import (
    WorkerResult, StatusMessage, StartMessage, ProgressMessage,
    NoFilesMessage, DoneMessage, FatalErrorMessage, DataType
)
from core.worker import process_single_xml

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Pipeline completo: extração → parsing paralelo → quarentena → Excel."""

    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue

    def run(self, archive_path: str, dst_dir: str, cancel_event: threading.Event = None):
        """Executa o pipeline completo. Envia mensagens para a UI via queue."""
        try:
            error_dir = os.path.join(dst_dir, "erros_quarentena")
            os.makedirs(error_dir, exist_ok=True)

            self.ui_queue.put(StatusMessage("Descompactando arquivos (pode levar alguns minutos)..."))

            with ArchiveHandler(archive_path) as archive_handler:
                if cancel_event and cancel_event.is_set(): return
                
                archive_handler.extract_all()
                self.ui_queue.put(StatusMessage("Buscando XMLs na pasta temporária..."))

                xml_files = archive_handler.find_xml_files()
                total_files = len(xml_files)

                if total_files == 0:
                    self.ui_queue.put(NoFilesMessage())
                    return

                self.ui_queue.put(StartMessage(total_files))
                self.ui_queue.put(StatusMessage("Extraindo dados das notas (Multiprocessamento)..."))

                all_cte_data, all_event_data, error_count = self._process_xmls(
                    xml_files, total_files, error_dir, cancel_event
                )

                if cancel_event and cancel_event.is_set():
                    self.ui_queue.put(StatusMessage("Processamento cancelado pelo utilizador."))
                    return

                self.ui_queue.put(StatusMessage("Gerando arquivo Excel (Modo Alta Performance)..."))
                base_name = os.path.splitext(os.path.basename(archive_path))[0]
                output_filename = os.path.join(dst_dir, f"{base_name}.xlsx")

                ExcelExporter(all_cte_data, EXCEL_HEADERS, all_event_data).export(output_filename)

                total_success = len(all_cte_data) + len(all_event_data)
                self.ui_queue.put(DoneMessage(total_files, total_success, error_count))

        except Exception as e:
            logger.exception("Erro fatal no pipeline")
            self.ui_queue.put(FatalErrorMessage(str(e)))

    def _process_xmls(self, xml_files: List[str], total_files: int,
                      error_dir: str, cancel_event: threading.Event) -> tuple:
        """Processa XMLs em paralelo e gerencia quarentena de erros, com proteção de RAM."""
        all_cte_data: List[Dict[str, Any]] = []
        all_event_data: List[Dict[str, str]] = []
        error_count = 0
        processed_count = 0

        max_workers = max(1, (os.cpu_count() or 1) - 1)

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # FASE 1: OTIMIZAÇÃO DE MEMÓRIA -> executor.map com chunksize=100
            # Evita instanciar milhares de Futures simultâneos na memória
            results = executor.map(process_single_xml, xml_files, chunksize=100)

            for worker_result in results:
                if cancel_event and cancel_event.is_set():
                    # Aborta o loop gentilmente se o utilizador fechar a janela
                    break

                if worker_result and worker_result.result and worker_result.result.data is not None:
                    if worker_result.result.data_type == DataType.CTE:
                        all_cte_data.append(worker_result.result.data)
                    elif worker_result.result.data_type == DataType.EVENT:
                        all_event_data.append(worker_result.result.data)

                if worker_result and worker_result.error:
                    error_count += 1
                    self._handle_quarantine(worker_result.error, error_dir)

                processed_count += 1
                if processed_count % PROGRESS_UPDATE_INTERVAL == 0 or processed_count == total_files:
                    self.ui_queue.put(ProgressMessage(processed_count, total_files))

        return all_cte_data, all_event_data, error_count

    @staticmethod
    def _handle_quarantine(error_info, error_dir: str):
        """Copia o XML com erro para quarentena e grava o _LOG.txt."""
        file_name = os.path.basename(error_info.xml_file)
        try:
            shutil.copy2(error_info.xml_file, os.path.join(error_dir, file_name))
        except OSError as e:
            logger.warning("Não foi possível copiar XML para quarentena: %s", e)

        log_path = os.path.join(error_dir, f"{file_name}_LOG.txt")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"Arquivo: {file_name}\n")
                f.write(f"Erro: {error_info.error_msg}\n\n")
                f.write(f"Traceback:\n{error_info.traceback}\n")
        except OSError as e:
            logger.warning("Não foi possível gravar log de quarentena: %s", e)
