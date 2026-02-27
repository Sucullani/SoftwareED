"""
EduFEM - Software Educativo de Elementos Finitos
Punto de entrada principal de la aplicación.

Ejecutar con:
    python main.py
"""

import sys
import os

# Asegurar que el directorio raíz del proyecto está en el PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Inicia la aplicación EduFEM."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
