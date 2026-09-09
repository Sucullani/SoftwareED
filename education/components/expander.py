"""
Expander: dropdown colapsable mínimo (header clickable + body show/hide).

Patrón de "progressive disclosure" para los módulos educativos: el
contenido secundario (derivaciones LaTeX, expresiones simbólicas extensas,
detalles avanzados) vive colapsado por defecto — cero ruido visual — y se
revela a demanda con un click en el header.

Cero dependencias externas (solo tk/ttk). El header muestra
"▸ <titulo>" colapsado, "▾ <titulo>" expandido. Al togglear dispara
`on_toggle()` para que el caller pueble el body perezosamente (las
imágenes LaTeX solo se renderizan cuando el body está visible).

Uso típico:

    exp = Expander(parent, title="Ver derivación paso a paso",
                   on_toggle=self._on_expand, bg=bg)
    exp.pack(fill="x")
    # poblar exp.body con widgets...
    LatexExpressionImage(exp.body, expr="", ...).pack()
"""

from __future__ import annotations

import traceback
from typing import Callable, Optional

import tkinter as tk
import ttkbootstrap as ttk

from config.settings import FONT_UI, OVERLAY_ACCENT_BLUE


# Color "link" del header (celeste — descubrible, no agresivo).
_EXPANDER_FG = OVERLAY_ACCENT_BLUE
# Fuente del header: la misma del resto de la UI (`config/settings.FONT_UI`).
# Estaba escrita a mano tres veces como ("Segoe UI", 9) — la misma clase de
# literal duplicado que los colores, y con el agravante de que fuera de
# Windows "Segoe UI" no existe y Tk cae a una fuente cualquiera.
_HEADER_FONT = FONT_UI
_HEADER_FONT_HOVER = (*FONT_UI, "underline")


class Expander(ttk.Frame):
    """Dropdown colapsable: header clickable + body que aparece/desaparece."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        title: str,
        on_toggle: Optional[Callable[[], None]] = None,
        bg: str = "",
        fg: str = _EXPANDER_FG,
        body_padx: int = 14,
        expanded: bool = False,
    ):
        super().__init__(parent)
        self._title = title
        self._expanded = bool(expanded)
        self._on_toggle = on_toggle
        self._body_padx = body_padx
        self._fg = fg

        self._header = tk.Label(
            self, text="", font=_HEADER_FONT, fg=fg, bg=bg,
            cursor="hand2", anchor="w",
        )
        self._header.pack(fill="x", anchor="w")
        self._header.bind("<Button-1>", lambda _e: self.toggle())
        # Underline al hover — refuerza la affordance de "clickeable".
        self._header.bind("<Enter>",
                          lambda _e: self._header.configure(
                              font=_HEADER_FONT_HOVER))
        self._header.bind("<Leave>",
                          lambda _e: self._header.configure(
                              font=_HEADER_FONT))

        # body — contenedor que el caller puebla.
        self.body = ttk.Frame(self)

        self._sync_header()
        if self._expanded:
            self.body.pack(fill="x", padx=(self._body_padx, 0), pady=(2, 0))

    def toggle(self) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", padx=(self._body_padx, 0), pady=(2, 0))
        else:
            self.body.pack_forget()
        self._sync_header()
        if self._on_toggle is not None:
            try:
                self._on_toggle()
            except Exception:
                # El body se puebla PEREZOSAMENTE en este callback (M5 rinde
                # ahi su integrando simbolico): si falla mudo, el expander se
                # abre VACIO y el alumno no tiene ni el contenido ni el
                # motivo. Es el camino que escondio el `sympy` sin importar.
                traceback.print_exc()

    def _sync_header(self) -> None:
        arrow = "▾" if self._expanded else "▸"
        self._header.configure(text=f"{arrow}  {self._title}")

    @property
    def is_expanded(self) -> bool:
        return self._expanded


__all__ = ["Expander"]
