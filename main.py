# main.py

import tkinter as tk
from ui.main_window import CTetoExcelApp

if __name__ == "__main__":
    # Inicia a Interface Gráfica
    root = tk.Tk()
    app = CTetoExcelApp(root)
    root.mainloop()