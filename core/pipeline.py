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

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Pipeline completo: extração → parsing paralelo → quarentena → Excel."""

    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue

    def run(self, archive_path: str, dst_dir: str,
            cancel_event: threading.Event = None, doc_type: str = "CTE"):
        """
        Executa o pipeline completo. Envia mensagens para a UI via queue.

        Args:
            archive_path: Caminho para o arquivo compactado ou pasta de XMLs.
            dst_dir: Pasta de destino para o Excel gerado.
            cancel_event: Evento de threading para cancelamento seguro.
            doc_type: "CTE" ou "NFE" — define o modo de parsing e exportação.
        """
        try:
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

                all_cte_data, all_event_data, all_nfe_data, error_count = self._process_xmls(
                    xml_files, total_files, error_dir, cancel_event, doc_type
                )

                if cancel_event and cancel_event.is_set():
                    self.ui_queue.put(StatusMessage("Processamento cancelado pelo utilizador."))
                    return

                self.ui_queue.put(StatusMessage("Gerando arquivo Excel (Modo Alta Performance)..."))
                base_name = os.path.splitext(os.path.basename(archive_path))[0]
                output_filename = os.path.join(dst_dir, f"{base_name}.xlsx")

                if doc_type == "NFE":
                    from nfe.nfe_constants import NFE_HEADERS
                    ExcelExporter(
                        cte_data=[], cte_headers=EXCEL_HEADERS,
                        event_data=all_event_data,
                        nfe_data=all_nfe_data, doc_type="NFE"
                    ).export(output_filename)
                    total_success = len(all_nfe_data) + len(all_event_data)
                else:
                    ExcelExporter(
                        cte_data=all_cte_data, cte_headers=EXCEL_HEADERS,
                        event_data=all_event_data,
                        doc_type="CTE"
                    ).export(output_filename)
                    total_success = len(all_cte_data) + len(all_event_data)

                self.ui_queue.put(DoneMessage(total_files, total_success, error_count))

        except Exception as e:
            logger.exception("Erro fatal no pipeline")
            self.ui_queue.put(FatalErrorMessage(str(e)))

    def _process_xmls(self, xml_files: List[str], total_files: int,
                      error_dir: str, cancel_event: threading.Event,
                      doc_type: str) -> tuple:
        """Processa XMLs em paralelo e gerencia quarentena de erros."""
        all_cte_data: List[Dict[str, Any]] = []
        all_event_data: List[Dict[str, str]] = []
        all_nfe_data: List[Dict[str, Any]] = []

        error_count = 0
        duplicate_count = 0
        processed_count = 0

        seen_cte_keys: set = set()
        seen_event_keys: set = set()
        seen_nfe_keys: set = set()  # Chave composta: chv_nfe_Id + "_" + nItem

        max_workers = max(1, (os.cpu_count() or 1) - 1)

        # Usa partial para fixar o doc_type em todas as chamadas do executor
        worker_func = functools.partial(process_single_xml, doc_type=doc_type)

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(worker_func, xml_files, chunksize=100)

            for worker_result in results:
                if cancel_event and cancel_event.is_set():
                    break

                if worker_result and worker_result.result and worker_result.result.data is not None:
                    data = worker_result.result.data
                    data_type = worker_result.result.data_type

                    if data_type == DataType.CTE:
                        cte_key = data.get("chv_cte_Id", "")
                        if cte_key and cte_key in seen_cte_keys:
                            duplicate_count += 1
                            logger.debug("CT-e duplicado ignorado: %s", cte_key)
                        else:
                            if cte_key:
                                seen_cte_keys.add(cte_key)
                            all_cte_data.append(data)

                    elif data_type == DataType.EVENT:
                        event_key = (
                            data.get("Chave de Acesso (Referência)", ""),
                            data.get("Tipo de Evento", ""),
                            data.get("Data do Evento", ""),
                            data.get("Detalhes / Justificativa", "")
                        )
                        if event_key in seen_event_keys:
                            duplicate_count += 1
                            logger.debug("Evento duplicado ignorado: %s", event_key[0])
                        else:
                            seen_event_keys.add(event_key)
                            all_event_data.append(data)

                    elif data_type == DataType.NFE:
                        # data é List[Dict] — itera para fazer o flatten e deduplicar por item
                        for row in data:
                            nfe_item_key = (
                                row.get("chv_nfe_Id", ""),
                                row.get("nItem_nItem", "")
                            )
                            if nfe_item_key in seen_nfe_keys:
                                duplicate_count += 1
                                logger.debug("NF-e item duplicado ignorado: %s #%s",
                                             nfe_item_key[0], nfe_item_key[1])
                            else:
                                seen_nfe_keys.add(nfe_item_key)
                                all_nfe_data.append(row)

                if worker_result and worker_result.error:
                    error_count += 1
                    self._handle_quarantine(worker_result.error, error_dir)

                processed_count += 1
                if processed_count % PROGRESS_UPDATE_INTERVAL == 0 or processed_count == total_files:
                    self.ui_queue.put(ProgressMessage(processed_count, total_files))

        if duplicate_count > 0:
            logger.info("Deduplicação: %d nota(s)/item(ns) duplicado(s) removido(s)", duplicate_count)

        return all_cte_data, all_event_data, all_nfe_data, error_count

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
