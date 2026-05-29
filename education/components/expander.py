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

from typing import Callable, Optional

import tkinter as tk
import ttkbootstrap as ttk


# Color "link" del header (celeste — descubrible, no agresivo).
_EXPANDER_FG = "#90caf9"


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
            self, text="", font=("Segoe UI", 9), fg=fg, bg=bg,
            cursor="hand2", anchor="w",
        )
        self._header.pack(fill="x", anchor="w")
        self._header.bind("<Button-1>", lambda _e: self.toggle())
        # Underline al hover — refuerza la affordance de "clickeable".
        self._header.bind("<Enter>",
                          lambda _e: self._header.configure(
                              font=("Segoe UI", 9, "underline")))
        self._header.bind("<Leave>",
                          lambda _e: self._header.configure(
                              font=("Segoe UI", 9)))

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
                pass

    def _sync_header(self) -> None:
        arrow = "▾" if self._expanded else "▸"
        self._header.configure(text=f"{arrow}  {self._title}")

    @property
    def is_expanded(self) -> bool:
        return self._expanded


__all__ = ["Expander"]
