# main.py

import logging
import multiprocessing
import tkinter as tk

from ui.main_window import CTetoExcelApp


def main():
    """Entry point principal da aplicação."""
    # Configura logging para toda a aplicação
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    # Necessário para o ProcessPoolExecutor funcionar no .exe compilado no Windows
    multiprocessing.freeze_support()

    # Inicia a Interface Gráfica
    root = tk.Tk()
    CTetoExcelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()