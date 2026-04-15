# core/pipeline.py

import functools
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
from core.strategy import resolve_strategy

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Pipeline completo: extração → parsing paralelo → quarentena → Excel."""

    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue

    def run(self, archive_path: str, dst_dir: str,
            cancel_event: threading.Event = None, doc_type: str = "CTE"):
        """
        Executa o pipeline completo utilizando a estratégia resolvida pelo doc_type.
        """
        try:
            strategy = resolve_strategy(doc_type)
            error_dir = os.path.join(dst_dir, "erros_quarentena")
            os.makedirs(error_dir, exist_ok=True)

            self.ui_queue.put(StatusMessage("Descompactando arquivos (pode levar alguns minutos)..."))

            with ArchiveHandler(archive_path) as archive_handler:
                if cancel_event and cancel_event.is_set():
                    return

                archive_handler.extract_all()
                self.ui_queue.put(StatusMessage("Buscando XMLs na pasta temporária..."))

                xml_files = archive_handler.find_xml_files()
                total_files = len(xml_files)

                if total_files == 0:
                    self.ui_queue.put(NoFilesMessage())
                    return

                self.ui_queue.put(StartMessage(total_files))
                self.ui_queue.put(StatusMessage("Extraindo dados das notas (Multiprocessamento)..."))

                all_main_data, all_event_data, error_count, duplicate_count, ignored_count = self._process_xmls(
                    xml_files, total_files, error_dir, cancel_event, strategy
                )

                if cancel_event and cancel_event.is_set():
                    self.ui_queue.put(StatusMessage("Processamento cancelado pelo utilizador."))
                    return

                self.ui_queue.put(StatusMessage("Gerando arquivo Excel (Modo Alta Performance)..."))
                base_name = os.path.splitext(os.path.basename(archive_path))[0]
                output_filename = os.path.join(dst_dir, f"{base_name}.xlsx")

                # Exportação unificada via estratégia
                ExcelExporter(
                    main_data=all_main_data,
                    strategy=strategy,
                    event_data=all_event_data
                ).export(output_filename)

                total_success = len(all_main_data) + len(all_event_data)
                self.ui_queue.put(DoneMessage(total_files, total_success, error_count, duplicate_count, ignored_count))

        except Exception as e:
            logger.exception("Erro fatal no pipeline")
            self.ui_queue.put(FatalErrorMessage(str(e)))

    def _process_xmls(self, xml_files: List[str], total_files: int,
                      error_dir: str, cancel_event: threading.Event,
                      strategy) -> tuple:
        """Processa XMLs em paralelo e gerencia quarentena de erros via estratégia."""
        all_main_data: List[Any] = []
        all_event_data: List[Dict[str, str]] = []

        error_count = 0
        duplicate_count = 0
        ignored_count = 0
        processed_count = 0

        seen_main_keys: set = set()
        seen_event_keys: set = set()

        max_workers = max(1, (os.cpu_count() or 1) - 1)
        worker_func = functools.partial(process_single_xml, doc_type=strategy.doc_type_name)

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(worker_func, xml_files, chunksize=100)

            for worker_result in results:
                if cancel_event and cancel_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                if worker_result and worker_result.result:
                    data = worker_result.result.data
                    data_type = worker_result.result.data_type

                    if data_type == DataType.IGNORE:
                        ignored_count += 1
                    elif data is not None:
                        duplicate_count += strategy.process_result_data(
                            data,
                            data_type,
                            all_main_data,
                            all_event_data,
                            seen_main_keys,
                            seen_event_keys
                        )

                if worker_result and worker_result.error:
                    error_count += 1
                    self._handle_quarantine(worker_result.error, error_dir)

                processed_count += 1
                if processed_count % PROGRESS_UPDATE_INTERVAL == 0 or processed_count == total_files:
                    self.ui_queue.put(ProgressMessage(processed_count, total_files))

        if duplicate_count > 0:
            logger.info("Deduplicação: %d nota(s)/item(ns) duplicado(s) removido(s)", duplicate_count)

        return all_main_data, all_event_data, error_count, duplicate_count, ignored_count

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
