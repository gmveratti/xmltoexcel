# main.py

import multiprocessing
import tkinter as tk
from ui.main_window import CTetoExcelApp

if __name__ == "__main__":
    # Necessário para o ProcessPoolExecutor funcionar no .exe compilado no Windows
    multiprocessing.freeze_support()
    
    # Inicia a Interface Gráfica
    root = tk.Tk()
    app = CTetoExcelApp(root)
    root.mainloop()