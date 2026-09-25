"""
pdflatex_missing_dialog: aviso accionable cuando falta ``pdflatex``.

La Memoria de Cálculo (PDF) se compila con LaTeX (pylatex → pdflatex). Si el
usuario no tiene una distribución TeX instalada, en lugar de un `showerror`
seco se muestra este diálogo con un **botón que abre la página oficial de
descarga** (MiKTeX en Windows, MacTeX en macOS, TeX Live en Linux).

Desde 2026-09 el instalador lleva un TeX Live recortado propio (carpeta
``texlive/`` junto al ``.exe``, ver ``education/components/latex_runtime.py``),
así que este diálogo solo aparece en la carpeta portable sin ``texlive/`` o
corriendo desde el código sin ``vendor/texlive``. El resto de EduFEM funciona
sin LaTeX — solo la exportación de la Memoria y la teoría en PDF lo necesitan.
El compilador se busca en cada exportación: instalar la distribución (o copiar
la carpeta) surte efecto sin reiniciar EduFEM.

Lo comparten los **dos** PDF que compila EduFEM, porque los dos fallan por la
misma causa: ``main_window._on_export_pdf`` (Memoria de Cálculo) y
``education.components.theory_viewer.open_theory_pdf`` (Ayuda ▸ Teoría MEF).
El kwarg ``documento`` nombra cuál de los dos se estaba pidiendo.

Uso:
    from gui.dialogs.pdflatex_missing_dialog import show_pdflatex_missing_dialog
    show_pdflatex_missing_dialog(parent)   # parent = widget Tk (root o Toplevel)
    show_pdflatex_missing_dialog(parent, documento="la Teoría MEF")

Filosofía minimalista (ver CLAUDE.md): sin Labelframes, sin subtítulo extra;
encabezado + mensaje muted + footer con dos botones.
"""

from __future__ import annotations

import platform
import traceback
import webbrowser

import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox
from ttkbootstrap.constants import BOTH, BOTTOM, RIGHT, W, X, YES

from config.settings import FONT_UI, FONT_UI_BOLD, TEXT_MUTED_FG
from gui.dialogs._dialog_helpers import bind_dialog_keys
from gui.scaling import clamp_window, center_on_parent


# (nombre de la distribución, URL oficial de descarga) por plataforma.
_TEX_DISTRO = {
    "Windows": ("MiKTeX", "https://miktex.org/download"),
    "Darwin": ("MacTeX", "https://tug.org/mactex/"),
}
_TEX_DISTRO_DEFAULT = ("TeX Live", "https://tug.org/texlive/")


def show_pdflatex_missing_dialog(
    parent: tk.Misc, *, documento: str = "la Memoria de Cálculo",
) -> None:
    """Muestra el diálogo modal de 'falta pdflatex' con botón de descarga.

    `documento` nombra en prosa lo que el alumno estaba pidiendo ("la Memoria
    de Cálculo", "la Teoría MEF"): son los **dos** PDF que compila EduFEM y
    los dos fallan por la misma causa, así que comparten esta salida. Antes
    el visor de Teoría escribía su propio texto en un label del encabezado —
    misma causa, dos tratamientos, y el peor le tocaba al alumno que solo
    quería leer.

    Debe invocarse desde el hilo principal de Tk (no desde un worker).
    """
    distro, url = _TEX_DISTRO.get(platform.system(), _TEX_DISTRO_DEFAULT)

    top = ttk.Toplevel(parent)
    top.title("Falta LaTeX para generar el PDF")
    top.transient(parent)

    main = ttk.Frame(top, padding=20)
    main.pack(fill=BOTH, expand=YES)

    ttk.Label(
        main,
        text=f"📄  Para generar {documento} falta pdflatex",
        font=FONT_UI_BOLD,
    ).pack(anchor=W, pady=(0, 10))

    ttk.Label(
        main,
        text=(
            f"EduFEM genera {documento} en PDF con LaTeX, y no encontró la "
            "carpeta 'texlive' que acompaña al programa ni una distribución "
            "TeX instalada.\n\n"
            "Solución recomendada: reinstalá EduFEM con el instalador "
            f"completo. Alternativa: descargá e instalá {distro} (incluye "
            "pdflatex) y volvé a intentarlo.\n\n"
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
            abierto = webbrowser.open(url, new=2)
        except Exception:
            traceback.print_exc()
            abierto = False
        if not abierto:
            # `webbrowser.open` devuelve False cuando no encontro navegador,
            # y ese retorno se estaba ignorando. Este dialogo existe porque
            # el alumno YA esta bloqueado: un boton que no abre nada y no
            # dice nada lo deja sin salida. Al menos mostrarle la URL.
            messagebox.showinfo(
                f"Descargar {distro}",
                "No se pudo abrir el navegador desde la aplicación.\n\n"
                "Copiá esta dirección y pegala en tu navegador:\n\n" + url,
                parent=top,
            )

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
    # Escape cierra. **Sin Return**: la acción principal de este diálogo
    # abre el navegador en la página de descarga de MiKTeX, y eso no se
    # dispara por un Enter que el alumno venía arrastrando del diálogo
    # anterior.
    bind_dialog_keys(top, on_escape=top.destroy)
    # Este dialogo no fija tamano: se ajusta a su texto. Aun asi hay que
    # recortarlo contra el area util —con la fuente del sistema mas grande
    # el bloque de texto se pasa de pantalla y el boton de descarga queda
    # fuera— y despues centrarlo dentro de ella.
    clamp_window(top, parent=parent)
    center_on_parent(top, parent)
    try:
        top.grab_set()
    except Exception:
        pass
    top.wait_window()
