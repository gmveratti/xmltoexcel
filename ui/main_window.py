# ui/main_window.py

import logging
import queue
import threading
import time
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.constants import WINDOW_TITLE, WINDOW_SIZE, QUEUE_POLL_INTERVAL_MS
from core.models import (
    StatusMessage, StartMessage, ProgressMessage,
    NoFilesMessage, DoneMessage, FatalErrorMessage
)
from core.pipeline import ProcessingPipeline

logger = logging.getLogger(__name__)


class CTetoExcelApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry("600x430")
        self.root.resizable(False, False)

        # FASE 4: DEFINIÇÃO DE ÍCONE (PORTÁTIL)
        self._set_app_icon()

        self.queue: queue.Queue = queue.Queue()
        self.is_processing = False
        self.start_time = 0
        self.doc_type_var = tk.StringVar(value="CTE")

        # FASE 1: Evento de cancelamento seguro
        self.cancel_event = threading.Event()
        
        # Interceta o clique no 'X' da janela para não deixar lixo temporário
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_ui()
        self.check_queue()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Configuração de Extração", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))

        # --- BLOCO DE ORIGEM ATUALIZADO (INPUT HÍBRIDO) ---
        ttk.Label(main_frame, text="Origem dos XMLs (Arquivo ou Pasta):").pack(anchor=tk.W)
        src_frame = ttk.Frame(main_frame)
        src_frame.pack(fill=tk.X, pady=(0, 10))
        self.src_entry = ttk.Entry(src_frame)
        self.src_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Dois botões para o utilizador escolher como quer enviar
        ttk.Button(src_frame, text="Procurar Pasta...", command=self.browse_src_folder).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(src_frame, text="Procurar Arquivo...", command=self.browse_src).pack(side=tk.RIGHT)

        ttk.Label(main_frame, text="Pasta de Destino (Onde salvar o Excel):").pack(anchor=tk.W)
        dst_frame = ttk.Frame(main_frame)
        dst_frame.pack(fill=tk.X, pady=(0, 10))
        self.dst_entry = ttk.Entry(dst_frame)
        self.dst_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dst_frame, text="Procurar...", command=self.browse_dst).pack(side=tk.RIGHT)

        # --- SELETOR DE TIPO DE DOCUMENTO ---
        ttk.Label(main_frame, text="Tipo de Documento:").pack(anchor=tk.W, pady=(0, 2))
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=(0, 12))
        self.rb_cte = ttk.Radiobutton(
            type_frame, text="CT-e  (Conhecimento de Transporte)",
            variable=self.doc_type_var, value="CTE"
        )
        self.rb_cte.pack(side=tk.LEFT, padx=(0, 20))
        self.rb_nfe = ttk.Radiobutton(
            type_frame, text="NF-e / DANFE  (Nota Fiscal de Produtos)",
            variable=self.doc_type_var, value="NFE"
        )
        self.rb_nfe.pack(side=tk.LEFT)

        ttk.Label(main_frame, text="Progresso da Conversão", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 5))

        self.lbl_status = ttk.Label(main_frame, text="Aguardando início...", foreground="gray")
        self.lbl_status.pack(anchor=tk.W, pady=(0, 5))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        self.lbl_count = ttk.Label(status_frame, text="Notas: 0 / 0 (0%)")
        self.lbl_count.pack(side=tk.LEFT)
        self.lbl_time = ttk.Label(status_frame, text="Tempo: 00:00")
        self.lbl_time.pack(side=tk.RIGHT)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        self.btn_cancel = ttk.Button(btn_frame, text="Cancelar", command=self.on_close)
        self.btn_cancel.pack(side=tk.RIGHT, padx=(5, 0))

        self.btn_start = ttk.Button(btn_frame, text="Iniciar Processamento", command=self.start_processing)
        self.btn_start.pack(side=tk.RIGHT)

    def browse_src(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo",
            filetypes=[("Arquivos Compactados", "*.rar *.zip"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, file_path)
            if not self.dst_entry.get():
                self.dst_entry.insert(0, os.path.dirname(file_path))

    # --- NOVA FUNÇÃO ADICIONADA ---
    def browse_src_folder(self):
        folder_path = filedialog.askdirectory(title="Selecione a pasta com os XMLs")
        if folder_path:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, folder_path)
            if not self.dst_entry.get():
                self.dst_entry.insert(0, os.path.dirname(folder_path))

    def browse_dst(self):
        folder = filedialog.askdirectory(title="Selecione a pasta de Destino")
        if folder:
            self.dst_entry.delete(0, tk.END)
            self.dst_entry.insert(0, folder)

    def start_processing(self):
        if self.is_processing:
            return
        rar_path = self.src_entry.get()
        dst_dir = self.dst_entry.get()

        if not rar_path or not dst_dir:
            messagebox.showwarning("Atenção", "Selecione o arquivo/pasta de origem e a pasta de destino.")
            return
            
        # Agora o sistema aceita se for arquivo OU se for pasta!
        if not os.path.isfile(rar_path) and not os.path.isdir(rar_path):
            messagebox.showerror("Erro", "A origem informada não existe.")
            return

        self.is_processing = True
        self.start_time = time.time()
        self.cancel_event.clear()

        doc_type = self.doc_type_var.get()

        self.btn_start.config(state=tk.DISABLED)
        self.src_entry.config(state=tk.DISABLED)
        self.dst_entry.config(state=tk.DISABLED)
        self.rb_cte.config(state=tk.DISABLED)
        self.rb_nfe.config(state=tk.DISABLED)

        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)

        pipeline = ProcessingPipeline(self.queue)
        threading.Thread(
            target=pipeline.run,
            args=(rar_path, dst_dir, self.cancel_event, doc_type),
            daemon=True
        ).start()

    def check_queue(self):
        if self.is_processing and self.start_time > 0:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.lbl_time.config(text=f"Tempo: {mins:02d}:{secs:02d}")

        while True:
            try:
                msg = self.queue.get_nowait()
                self._handle_message(msg)
            except queue.Empty:
                break

        self.root.after(QUEUE_POLL_INTERVAL_MS, self.check_queue)

    def _handle_message(self, msg):
        if isinstance(msg, StatusMessage):
            self.lbl_status.config(text=msg.text, foreground="blue")

        elif isinstance(msg, StartMessage):
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
            self.progress_bar['maximum'] = msg.total_files
            self.progress_var.set(0)
            self.lbl_count.config(text=f"Notas: 0 / {msg.total_files} (0.0%)")

        elif isinstance(msg, ProgressMessage):
            self.progress_var.set(msg.current)
            pct = (msg.current / msg.total) * 100
            self.lbl_count.config(text=f"Notas: {msg.current} / {msg.total} ({pct:.1f}%)")

        elif isinstance(msg, NoFilesMessage):
            messagebox.showinfo("Aviso", "Nenhum arquivo XML foi encontrado.")
            self.reset_ui()

        elif isinstance(msg, DoneMessage):
            messagebox.showinfo(
                "Sucesso",
                f"Concluído!\n\n"
                f"Lidos: {msg.total_read}\n"
                f"Sucesso: {msg.total_success}\n"
                f"Quarentena: {msg.total_errors}\n"
                f"Duplicados: {msg.total_duplicates}\n"
                f"Ignorados: {msg.total_ignored}"
            )
            self.reset_ui()

        elif isinstance(msg, FatalErrorMessage):
            messagebox.showerror("Erro Crítico", f"Erro fatal:\n{msg.error_msg}")
            self.reset_ui()

    def reset_ui(self):
        self.is_processing = False
        self.start_time = 0
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.btn_start.config(state=tk.NORMAL)
        self.src_entry.config(state=tk.NORMAL)
        self.dst_entry.config(state=tk.NORMAL)
        self.rb_cte.config(state=tk.NORMAL)
        self.rb_nfe.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.lbl_status.config(text="Aguardando início...", foreground="gray")
        self.lbl_count.config(text="Notas: 0 / 0 (0%)")
        self.lbl_time.config(text="Tempo: 00:00")

    def on_close(self):
        """Protocolo de fecho seguro da aplicação."""
        if self.is_processing:
            if messagebox.askokcancel("Cancelar", "O processamento está a decorrer. Deseja cancelar e sair?"):
                self.lbl_status.config(text="A cancelar em segurança. A limpar ficheiros temporários...", foreground="red")
                self.root.update()
                # Emite o sinal de paragem
                self.cancel_event.set()
                # Dá tempo à thread para fechar e limpar a pasta self.temp_dir
                self.root.after(1500, self.root.destroy)
        else:
            self.root.destroy()

    def _set_app_icon(self):
        """Define o ícone da janela de forma portável."""
        import sys
        if getattr(sys, 'frozen', False):
            # No binário compilado pelo PyInstaller
            base_path = sys._MEIPASS
        else:
            # Em modo de desenvolvimento (uv run main.py)
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        icon_path = os.path.join(base_path, "assets", "ico.ico")
        
        if os.path.exists(icon_path):
            try:
                # Tenta definir o ícone no Windows (.ico)
                self.root.iconbitmap(icon_path)
            except Exception as e:
                logger.warning("Não foi possível carregar o ícone da janela: %s", e)
