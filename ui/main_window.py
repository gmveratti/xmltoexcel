# ui/main_window.py

import os
import shutil
import concurrent.futures
import threading
import queue
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.archive_handler import ArchiveHandler
from core.excel_exporter import ExcelExporter
from core.constants import EXCEL_HEADERS
from core.worker import process_single_xml  # Importando o worker isolado

class CTetoExcelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pipeline de Dados Fiscais (CT-e)")
        self.root.geometry("600x380")
        self.root.resizable(False, False)
        
        self.queue = queue.Queue()
        self.is_processing = False
        self.start_time = 0
        
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
        
        ttk.Label(main_frame, text="Arquivo Compactado (.rar / .zip):").pack(anchor=tk.W)
        src_frame = ttk.Frame(main_frame)
        src_frame.pack(fill=tk.X, pady=(0, 10))
        self.src_entry = ttk.Entry(src_frame)
        self.src_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(src_frame, text="Procurar...", command=self.browse_src).pack(side=tk.RIGHT)

        ttk.Label(main_frame, text="Pasta de Destino (Onde salvar o Excel):").pack(anchor=tk.W)
        dst_frame = ttk.Frame(main_frame)
        dst_frame.pack(fill=tk.X, pady=(0, 20))
        self.dst_entry = ttk.Entry(dst_frame)
        self.dst_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dst_frame, text="Procurar...", command=self.browse_dst).pack(side=tk.RIGHT)

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
        self.btn_cancel = ttk.Button(btn_frame, text="Fechar", command=self.root.destroy)
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

    def browse_dst(self):
        folder = filedialog.askdirectory(title="Selecione a pasta de Destino")
        if folder:
            self.dst_entry.delete(0, tk.END)
            self.dst_entry.insert(0, folder)

    def start_processing(self):
        if self.is_processing: return
        rar_path = self.src_entry.get()
        dst_dir = self.dst_entry.get()

        if not rar_path or not dst_dir:
            messagebox.showwarning("Atenção", "Selecione o arquivo e a pasta de destino.")
            return
        if not os.path.isfile(rar_path):
            messagebox.showerror("Erro", "O arquivo informado não existe.")
            return

        # BUG RESOLVIDO AQUI: Dispara o cronómetro no milissegundo em que clica no botão
        self.is_processing = True
        self.start_time = time.time()
        self.btn_start.config(state=tk.DISABLED)
        self.src_entry.config(state=tk.DISABLED)
        self.dst_entry.config(state=tk.DISABLED)

        threading.Thread(target=self.process_files_thread, args=(rar_path, dst_dir), daemon=True).start()

    def process_files_thread(self, rar_path, dst_dir):
        try:
            error_dir = os.path.join(dst_dir, "erros_quarentena")
            os.makedirs(error_dir, exist_ok=True)

            self.queue.put(("STATUS", "Descompactando arquivos (pode levar alguns segundos)..."))
            
            with ArchiveHandler(rar_path) as archive_handler:
                archive_handler.extract_all()
                self.queue.put(("STATUS", "Buscando XMLs na pasta temporária..."))
                
                xml_files = archive_handler.find_xml_files()
                total_files = len(xml_files)

                if total_files == 0:
                    self.queue.put(("NO_FILES",))
                    return

                self.queue.put(("START", total_files))
                self.queue.put(("STATUS", "Extraindo dados das notas (Multiprocessamento)..."))
                
                all_data, error_details = [], []
                processed_count = 0

                with concurrent.futures.ProcessPoolExecutor() as executor:
                    future_to_xml = {executor.submit(process_single_xml, xml): xml for xml in xml_files}
                    
                    for future in concurrent.futures.as_completed(future_to_xml):
                        row_data, error_info = future.result()
                        
                        if row_data: all_data.append(row_data)
                        if error_info:
                            xml_file, error_msg, error_trace = error_info
                            file_name = os.path.basename(xml_file)
                            error_details.append(f"Arquivo: [{file_name}] | Erro: {error_msg}")
                            try:
                                shutil.copy2(xml_file, os.path.join(error_dir, file_name))
                            except: pass
                        
                        processed_count += 1
                        if processed_count % 50 == 0 or processed_count == total_files:
                            self.queue.put(("PROGRESS", processed_count, total_files))

                self.queue.put(("STATUS", "Gerando arquivo Excel..."))
                base_name = os.path.splitext(os.path.basename(rar_path))[0]
                output_filename = os.path.join(dst_dir, f"{base_name}.xlsx")
                
                ExcelExporter(all_data, EXCEL_HEADERS).export(output_filename)
                self.queue.put(("DONE", total_files, len(all_data), len(error_details)))
                
        except Exception as e:
            self.queue.put(("FATAL_ERROR", str(e)))

    def check_queue(self):
        # BUG RESOLVIDO AQUI: Só atualiza se o start_time já foi inicializado (> 0)
        if self.is_processing and self.start_time > 0:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.lbl_time.config(text=f"Tempo: {mins:02d}:{secs:02d}")

        while True:
            try:
                msg = self.queue.get_nowait()
                msg_type = msg[0]

                if msg_type == "STATUS":
                    self.lbl_status.config(text=msg[1], foreground="blue")
                elif msg_type == "START":
                    self.progress_bar['maximum'] = msg[1]
                    self.lbl_count.config(text=f"Notas: 0 / {msg[1]} (0.0%)")
                elif msg_type == "PROGRESS":
                    self.progress_var.set(msg[1])
                    self.lbl_count.config(text=f"Notas: {msg[1]} / {msg[2]} ({(msg[1] / msg[2]) * 100:.1f}%)")
                elif msg_type == "NO_FILES":
                    messagebox.showinfo("Aviso", "Nenhum arquivo XML foi encontrado.")
                    self.reset_ui()
                elif msg_type == "DONE":
                    messagebox.showinfo("Sucesso", f"Concluído!\n\nLidos: {msg[1]}\nSucesso: {msg[2]}\nQuarentena: {msg[3]}")
                    self.reset_ui()
                elif msg_type == "FATAL_ERROR":
                    messagebox.showerror("Erro Crítico", f"Erro fatal:\n{msg[1]}")
                    self.reset_ui()

            except queue.Empty:
                break

        self.root.after(100, self.check_queue)

    def reset_ui(self):
        self.is_processing = False
        self.start_time = 0
        self.btn_start.config(state=tk.NORMAL)
        self.src_entry.config(state=tk.NORMAL)
        self.dst_entry.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.lbl_status.config(text="Aguardando início...", foreground="gray")
        self.lbl_count.config(text="Notas: 0 / 0 (0%)")
        self.lbl_time.config(text="Tempo: 00:00") # BUG RESOLVIDO AQUI: Garante que visualmente ZERE
