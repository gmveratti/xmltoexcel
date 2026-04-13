# core/pipeline.py

import logging
import os
import shutil
import concurrent.futures
import queue
import threading
from functools import partial
from typing import List, Dict, Any

from core.archive_handler import ArchiveHandler
from core.excel_exporter import ExcelExporter
from core.constants import EXCEL_HEADERS, NFE_HEADERS, PROGRESS_UPDATE_INTERVAL
from core.models import (
    WorkerResult, StatusMessage, StartMessage, ProgressMessage,
    NoFilesMessage, DoneMessage, FatalErrorMessage, DataType, DocType
)
from core.worker import process_single_xml

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Pipeline completo: extração → parsing paralelo → quarentena → Excel."""

    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue

    def run(self, archive_path: str, dst_dir: str,
            cancel_event: threading.Event = None,
            doc_type: DocType = DocType.CTE):
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

                all_main_data, all_event_data, error_count = self._process_xmls(
                    xml_files, total_files, error_dir, cancel_event, doc_type
                )

                if cancel_event and cancel_event.is_set():
                    self.ui_queue.put(StatusMessage("Processamento cancelado pelo utilizador."))
                    return

                self.ui_queue.put(StatusMessage("Gerando arquivo Excel (Modo Alta Performance)..."))
                base_name = os.path.splitext(os.path.basename(archive_path))[0]
                output_filename = os.path.join(dst_dir, f"{base_name}.xlsx")

                headers = EXCEL_HEADERS if doc_type == DocType.CTE else NFE_HEADERS
                ExcelExporter(all_main_data, headers, all_event_data, doc_type).export(output_filename)

                total_success = len(all_main_data) + len(all_event_data)
                self.ui_queue.put(DoneMessage(total_files, total_success, error_count))

        except Exception as e:
            logger.exception("Erro fatal no pipeline")
            self.ui_queue.put(FatalErrorMessage(str(e)))

    def _process_xmls(self, xml_files: List[str], total_files: int,
                      error_dir: str, cancel_event: threading.Event,
                      doc_type: DocType) -> tuple:
        """Processa XMLs em paralelo e gerencia quarentena de erros, com proteção de RAM."""
        all_main_data: List[Dict[str, Any]] = []
        all_event_data: List[Dict[str, str]] = []
        error_count = 0
        duplicate_count = 0
        processed_count = 0

        # Deduplicação por Chave de Acesso — impede linhas duplicadas
        seen_main_keys: set = set()
        seen_event_keys: set = set()

        max_workers = max(1, (os.cpu_count() or 1) - 1)

        # Envia o doc_type para cada worker via partial
        worker_func = partial(process_single_xml, expected_type=doc_type)

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # FASE 1: OTIMIZAÇÃO DE MEMÓRIA -> executor.map com chunksize=100
            # Evita instanciar milhares de Futures simultâneos na memória
            results = executor.map(worker_func, xml_files, chunksize=100)

            for worker_result in results:
                if cancel_event and cancel_event.is_set():
                    # Aborta o loop gentilmente se o utilizador fechar a janela
                    break

                if worker_result and worker_result.result and worker_result.result.data is not None:
                    data = worker_result.result.data
                    data_type = worker_result.result.data_type

                    if data_type in (DataType.CTE, DataType.NFE):
                        # NF-e retorna List[Dict], CT-e retorna Dict
                        items = data if isinstance(data, list) else [data]

                        for item in items:
                            if self.check_and_register_main(item, seen_main_keys, data_type):
                                all_main_data.append(item)
                            else:
                                duplicate_count += 1

                    elif data_type == DataType.EVENT:
                        if self.check_and_register_event(data, seen_event_keys):
                            all_event_data.append(data)
                        else:
                            duplicate_count += 1

                if worker_result and worker_result.error:
                    error_count += 1
                    self._handle_quarantine(worker_result.error, error_dir)

                processed_count += 1
                if processed_count % PROGRESS_UPDATE_INTERVAL == 0 or processed_count == total_files:
                    self.ui_queue.put(ProgressMessage(processed_count, total_files))

        if duplicate_count > 0:
            logger.info("Deduplicação: %d nota(s) duplicada(s) removida(s)", duplicate_count)

        return all_main_data, all_event_data, error_count

    @staticmethod
    def check_and_register_main(data: Dict[str, Any], seen_keys: set,
                                data_type: DataType) -> bool:
        """Verifica se um registro principal (CT-e ou NF-e) é duplicata.

        CT-e: chave = chv_cte_Id
        NF-e: chave = chv_nfe_Id + nItem (pois o header repete para cada produto)

        Returns:
            True  → registro é novo, deve ser adicionado à lista de resultados.
            False → registro é duplicata, deve ser descartado.
        """
        if data_type == DataType.NFE:
            key = f'{data.get("chv_nfe_Id", "")}_{data.get("nItem", "")}'
        else:
            key = data.get("chv_cte_Id", "")

        if key and key in seen_keys:
            logger.debug("Registro duplicado ignorado: %s", key)
            return False
        if key:
            seen_keys.add(key)
        return True

    @staticmethod
    def check_and_register_event(data: Dict[str, Any], seen_keys: set) -> bool:
        """Verifica se um Evento é duplicata. Registra a tupla-chave e retorna True se for novo.

        A chave composta é formada por (Chave de Acesso, Tipo de Evento, Data, Detalhes),
        pois o mesmo CT-e/NF-e pode ter múltiplos eventos legítimos de tipos diferentes.

        Returns:
            True  → evento é novo, deve ser adicionado à lista de resultados.
            False → evento é duplicata, deve ser descartado.
        """
        event_key = (
            data.get("Chave de Acesso (Referência)", ""),
            data.get("Tipo de Evento", ""),
            data.get("Data do Evento", ""),
            data.get("Detalhes / Justificativa", ""),
        )
        if event_key in seen_keys:
            logger.debug("Evento duplicado ignorado: %s", event_key[0])
            return False
        seen_keys.add(event_key)
        return True

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
