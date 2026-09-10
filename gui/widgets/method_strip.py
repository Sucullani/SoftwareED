"""Tira del metodo: la cadena de pasos del calculo como chips clickeables.

Rediseño 2026-09-09. En el banner de Proceso se lee `N › J › B › D › kₑ ›
F › K`: los siete pasos con que el MEF pasa del elemento al sistema, 1:1
con los modulos ①..⑦. Cada chip abre su modulo, y su color dice en que
estado esta el alumno respecto de ese paso:

- **inactivo** (no visitado en la sesion): texto atenuado sobre el banner;
- **visitado**: texto blanco (indicador de progreso, no de bloqueo — se
  reabre para comparar elementos);
- **activo** (overlay abierto ahora): chip ambar.

Reemplaza al breadcrumb glifico `Ⓜ ① … ⑦` de la barra de estado, que
aparecia recien al abrir el primer modulo y no decia que era. El estado
llega por `set_active(mod_keys)` (cadena de `subscribe_overlay_change`).
Widget generico: recibe la lista de pasos y el callback de click.
"""

from __future__ import annotations

import tkinter as tk

from config.settings import (
    METHOD_CHIP_BG, METHOD_CHIP_INACTIVE_FG, METHOD_CHIP_VISITED_FG,
    METHOD_CHIP_ACTIVE_BG, METHOD_CHIP_ACTIVE_FG, METHOD_ARROW_FG,
)
from gui.widgets.tooltip import ToolTip


class MethodStrip:
    """`steps`: lista de (key, texto_del_chip, tooltip). `on_click(key)`."""

    def __init__(self, parent, steps, *, bg, on_click=None):
        self.frame = tk.Frame(parent, bg=bg)
        self._bg = bg
        self._on_click = on_click
        self._chips: dict[str, tk.Label] = {}
        self._visited: set[str] = set()
        self._active: set[str] = set()
        self._order = [key for key, _t, _tip in steps]
        for k, (key, text, tip) in enumerate(steps):
            if k > 0:
                tk.Label(
                    self.frame, text="›", bg=bg, fg=METHOD_ARROW_FG,
                    font=("Segoe UI", 10, "bold"), padx=1,
                ).pack(side="left")
            chip = tk.Label(
                self.frame, text=text, bg=METHOD_CHIP_BG,
                fg=METHOD_CHIP_INACTIVE_FG,
                font=("Segoe UI Semibold", 9), padx=6, pady=1, cursor="hand2",
            )
            chip.pack(side="left", padx=1)
            chip.bind("<Button-1>", lambda _e, kk=key: self._click(kk))
            if tip:
                ToolTip(chip, text=tip)
            self._chips[key] = chip

    # ── estado ────────────────────────────────────────────────────────

    def set_active(self, keys):
        """Chips con overlay abierto AHORA. Los visitados se acumulan."""
        self._active = set(keys or ())
        self._visited.update(self._active)
        self._repaint()

    def mark_visited(self, key):
        if key in self._chips:
            self._visited.add(key)
            self._repaint()

    def reset_visited(self):
        self._visited.clear()
        self._active.clear()
        self._repaint()

    @property
    def visited(self):
        return set(self._visited)

    @property
    def active(self):
        return set(self._active)

    def state_of(self, key):
        if key in self._active:
            return "active"
        if key in self._visited:
            return "visited"
        return "inactive"

    # ── internos ──────────────────────────────────────────────────────

    def _click(self, key):
        if self._on_click is not None:
            self._on_click(key)

    def _repaint(self):
        for key, chip in self._chips.items():
            state = self.state_of(key)
            try:
                if state == "active":
                    chip.configure(bg=METHOD_CHIP_ACTIVE_BG, fg=METHOD_CHIP_ACTIVE_FG)
                elif state == "visited":
                    chip.configure(bg=METHOD_CHIP_BG, fg=METHOD_CHIP_VISITED_FG)
                else:
                    chip.configure(bg=METHOD_CHIP_BG, fg=METHOD_CHIP_INACTIVE_FG)
            except tk.TclError:
                pass
