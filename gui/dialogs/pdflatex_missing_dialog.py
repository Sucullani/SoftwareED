"""
pdflatex_missing_dialog: aviso accionable cuando falta ``pdflatex``.

La Memoria de Cálculo (PDF) se compila con LaTeX (pylatex → pdflatex). Si el
usuario no tiene una distribución TeX instalada, en lugar de un `showerror`
seco se muestra este diálogo con un **botón que abre la página oficial de
descarga** (MiKTeX en Windows, MacTeX en macOS, TeX Live en Linux).

El resto de EduFEM funciona sin LaTeX — solo la exportación de la Memoria y la
teoría en PDF lo necesitan. Tras instalar la distribución hay que **reiniciar
EduFEM** (el PATH se lee al arrancar el proceso).

Uso:
    from gui.dialogs.pdflatex_missing_dialog import show_pdflatex_missing_dialog
    show_pdflatex_missing_dialog(parent)   # parent = widget Tk (root o Toplevel)

Filosofía minimalista (ver CLAUDE.md): sin Labelframes, sin subtítulo extra;
encabezado + mensaje muted + footer con dos botones.
"""

from __future__ import annotations

import platform
import webbrowser

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, BOTTOM, RIGHT, W, X, YES

from config.settings import FONT_UI, FONT_UI_BOLD, TEXT_MUTED_FG
from gui.dialogs._dialog_helpers import center_dialog


# (nombre de la distribución, URL oficial de descarga) por plataforma.
_TEX_DISTRO = {
    "Windows": ("MiKTeX", "https://miktex.org/download"),
    "Darwin": ("MacTeX", "https://tug.org/mactex/"),
}
_TEX_DISTRO_DEFAULT = ("TeX Live", "https://tug.org/texlive/")


def show_pdflatex_missing_dialog(parent: tk.Misc) -> None:
    """Muestra el diálogo modal de 'falta pdflatex' con botón de descarga.

    Debe invocarse desde el hilo principal de Tk (no desde un worker).
    """
    distro, url = _TEX_DISTRO.get(platform.system(), _TEX_DISTRO_DEFAULT)

    top = ttk.Toplevel(parent)
    top.title("Falta LaTeX para generar el PDF")
    top.transient(parent)
    top.resizable(False, False)

    main = ttk.Frame(top, padding=20)
    main.pack(fill=BOTH, expand=YES)

    ttk.Label(
        main,
        text="📄  Para exportar la Memoria de Cálculo falta pdflatex",
        font=FONT_UI_BOLD,
    ).pack(anchor=W, pady=(0, 10))

    ttk.Label(
        main,
        text=(
            "La Memoria de Cálculo (PDF) se compila con LaTeX. Tu equipo no "
            f"tiene una distribución TeX instalada.\n\n"
            f"Descargá e instalá {distro} (incluye pdflatex) y luego "
            "reiniciá EduFEM.\n\n"
            "El resto del programa funciona normalmente sin LaTeX."
        ),
        font=FONT_UI,
        foreground=TEXT_MUTED_FG,
        justify="left",
        wraplength=440,
    ).pack(anchor=W)

    footer = ttk.Frame(main)
    footer.pack(fill=X, side=BOTTOM, pady=(18, 0))

    def _open_download() -> None:
        try:
            webbrowser.open(url, new=2)
        except Exception:
            pass

    ttk.Button(
        footer,
        text=f"Descargar {distro}",
        bootstyle="success",
        command=_open_download,
        width=18,
    ).pack(side=RIGHT, padx=4)

    ttk.Button(
        footer,
        text="Cerrar",
        bootstyle="secondary",
        command=top.destroy,
        width=12,
    ).pack(side=RIGHT, padx=4)

    top.protocol("WM_DELETE_WINDOW", top.destroy)
    center_dialog(top, parent)
    try:
        top.grab_set()
    except Exception:
        pass
    top.wait_window()
