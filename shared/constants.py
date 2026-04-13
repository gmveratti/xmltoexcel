# core/constants.py

from typing import List, Dict, Set



# Cabeçalhos fixos para aba de eventos
EVENT_SHEET_HEADERS: List[str] = [
    "Chave de Acesso (Referência)",
    "Tipo de Evento",
    "Data do Evento",
    "Detalhes / Justificativa"
]

# ==================== UI ====================

WINDOW_TITLE: str = "Conversor de XML para Excel"
WINDOW_SIZE: str = "600x380"
QUEUE_POLL_INTERVAL_MS: int = 100
PROGRESS_UPDATE_INTERVAL: int = 50

# ==================== Excel Styling ====================

GRAY_FILL_COLOR: str = "D3D3D3"
ACCOUNTING_FORMAT: str = '#,##0.00'
MAX_COLUMN_WIDTH: int = 50
EVENT_DETAIL_COL_WIDTH: int = 80
EVENT_KEY_COL_WIDTH: int = 50
