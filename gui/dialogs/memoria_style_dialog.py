"""
MemoriaStyleDialog: diálogo modal previo a la exportación del PDF.

Permite al usuario elegir el estilo de la Memoria de Cálculo antes de
seleccionar el archivo de destino.

Estilos disponibles (DOS):
  'educativo' — Mismo procedimiento, con infografía del recorrido MEF,
                tarjetas "entra → fórmula → sale", una idea clave por
                concepto, diagnóstico comentado, interpretación de
                resultados y glosario final.
  'directo'   — El paso a paso matricial completo de inicio a fin
                (N → u=Na → J → B → D → kₑ, ensamblaje, solución,
                recuperación ε→σ, extrapolación, diagnóstico y resumen)
                pero SECO: fórmulas, matrices y resultados, sin
                explicaciones.

Filosofía minimalista (ver CLAUDE.md): sin Labelframes, sin subtítulo
descriptivo, sin banner explicativo. Solo los 2 radios + descripción muted
+ footer.

Constructor: MemoriaStyleDialog(parent)
Resultado:   self.result — str con el estilo elegido, o None si se canceló.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, BOTTOM, E, RIGHT, W, X, YES

from config.settings import FONT_UI, FONT_UI_BOLD, TEXT_MUTED_FG


_ESTILOS = [
    (
        "educativo",
        "🎓  Educativo",
        "Paso a paso comentado + infografía, diagnóstico, interpretación, glosario.",
    ),
    (
        "directo",
        "⚡  Directo",
        "Procedimiento matricial seco + diagnóstico y resumen. Sin explicaciones.",
    ),
]


class MemoriaStyleDialog:
    """Toplevel modal para seleccionar el estilo de la Memoria de Cálculo."""

    def __init__(self, parent):
        self.result: str | None = None

        self._top = ttk.Toplevel(parent)
        self._top.title("Estilo de Memoria de Cálculo")
        self._top.geometry("460x210")
        self._top.transient(parent)
        self._top.grab_set()
        self._top.resizable(False, False)
        self._top.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Default: educativo (balance recomendado para el alumno)
        self._style_var = tk.StringVar(value="educativo")

        self._build()
        self._center(parent)
        self._top.wait_window()

    # ─── Layout ─────────────────────────────────────────────────────────────

    def _build(self) -> None:
        main = ttk.Frame(self._top, padding=20)
        main.pack(fill=BOTH, expand=YES)

        ttk.Label(
            main,
            text="Seleccioná el estilo del documento",
            font=FONT_UI_BOLD,
        ).pack(anchor=W, pady=(0, 14))

        for value, label, desc in _ESTILOS:
            row = ttk.Frame(main)
            row.pack(fill=X, pady=3)

            ttk.Radiobutton(
                row,
                text=label,
                variable=self._style_var,
                value=value,
                bootstyle="primary",
            ).pack(anchor=W)

            ttk.Label(
                row,
                text=f"    {desc}",
                font=FONT_UI,
                foreground=TEXT_MUTED_FG,
            ).pack(anchor=W)

        # ─── Footer ─────────────────────────────────────────────────────────
        footer = ttk.Frame(main)
        footer.pack(fill=X, side=BOTTOM, pady=(18, 0))

        ttk.Button(
            footer,
            text="Continuar",
            bootstyle="success",
            command=self._on_accept,
            width=12,
        ).pack(side=RIGHT, padx=4)

        ttk.Button(
            footer,
            text="Cancelar",
            bootstyle="secondary",
            command=self._on_cancel,
            width=12,
        ).pack(side=RIGHT, padx=4)

    # ─── Acciones ───────────────────────────────────────────────────────────

    def _on_accept(self) -> None:
        self.result = self._style_var.get()
        self._top.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self._top.destroy()

    def _center(self, parent) -> None:
        self._top.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        dw = self._top.winfo_width()
        dh = self._top.winfo_height()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self._top.geometry(f"+{x}+{y}")
