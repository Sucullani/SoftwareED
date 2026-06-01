"""
Panel reutilizable para listar modulos educativos por fase.

Cada modulo se renderiza como un boton + descripcion + chip de estado. La
funcion `render_module_buttons` retorna un controller (`ModuleButtonsPanel`)
que el caller usa para sincronizar el estado visual con la seleccion del
MeshCanvas (chip `#N` cuando hay un elemento seleccionado, tick ✓ tras
primera apertura).

Reglas de iluminacion (propuesta UX 2026):
    - Modulos globales (sin elemento requerido): siempre con color de
      fase. Sin chip de elemento.
    - Modulos por-elemento sin seleccion: bootstyle `secondary-outline`
      (gris desaturado). Click sigue funcionando — abre un dialog de
      seleccion como fallback.
    - Modulos por-elemento CON seleccion: bootstyle de fase (color),
      chip `#N` a la derecha. Click directo, sin dialog.
    - Visitado: chip muestra `✓` (queda permanente en la sesion como
      indicador de progreso pedagogico, sin bloquear re-apertura).

Sin scroll: el contenido (header + subtitle + N botones) cabe en cualquier
pantalla 1080p+ con el ancho actual del panel lateral.
"""

from __future__ import annotations

from typing import Callable, Optional, Set
from tkinter import TclError

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.settings import (
    FONT_UI, TEXT_MUTED_FG,
    MODULE_HEADER_FG_COLOR, MODULE_DESC_FG_COLOR, MODULE_EMPTY_FG_COLOR,
)


_BUTTON_WIDTH_CHARS = 30


class ModuleButtonsPanel:
    """Controller del panel de botones de modulos educativos.

    Retornado por `render_module_buttons`. El caller (pre_tab/proc_tab/
    post_tab) lo conecta al MeshCanvas para que la iluminacion reaccione
    a la seleccion.
    """

    def __init__(self, parent, *, bootstyle: str, global_modules: Set[str]):
        self.parent = parent
        self.bootstyle_active = bootstyle           # ej. "warning-outline"
        self.bootstyle_inactive = "secondary-outline"
        self.global_modules = set(global_modules or set())
        # mod_key -> dict(button, chip_label, visited, requires_element)
        self._rows: dict[str, dict] = {}

    # ── construccion (uso interno desde render_module_buttons) ──────
    def _register(self, mod_key: str, button: ttk.Button,
                  chip_label: ttk.Label) -> None:
        self._rows[mod_key] = {
            "button": button,
            "chip_label": chip_label,
            "visited": False,
            "requires_element": mod_key not in self.global_modules,
        }
        # Estado inicial: modulos globales siempre activos; los por-elemento
        # arrancan desactivados (sin chip) hasta que llegue una seleccion.
        if mod_key in self.global_modules:
            self._apply_active(mod_key, chip_text="")
        else:
            self._apply_inactive(mod_key)

    # ── API publica que consume el caller ──────────────────────────
    def update_selection(self, elem_id: Optional[int]) -> None:
        """Sincroniza todos los botones con la seleccion actual del canvas.

        elem_id : id del elemento seleccionado (unico) o None si no hay
                  exactamente uno. Cuando hay 0 o >1 elementos seleccionados,
                  los modulos por-elemento se desactivan visualmente — el
                  pedagogico se opera UN elemento a la vez.
        """
        for mod_key, row in self._rows.items():
            if not row["requires_element"]:
                continue  # los globales no cambian con la seleccion
            if elem_id is None:
                self._apply_inactive(mod_key)
            else:
                tick = " ✓" if row["visited"] else ""
                self._apply_active(mod_key, chip_text=f"#{elem_id}{tick}")

    def mark_visited(self, mod_key: str) -> None:
        """Marca el modulo como visitado (queda ✓ permanente en la sesion)."""
        row = self._rows.get(mod_key)
        if row is None or row["visited"]:
            return
        row["visited"] = True
        # Si esta activo en este momento, refrescar el chip para incluir el ✓.
        chip = row["chip_label"]
        try:
            current = chip.cget("text")
        except TclError:
            return
        if current and "✓" not in current:
            try:
                chip.configure(text=f"{current} ✓")
            except TclError:
                pass
        elif not current:
            # Modulo global o por-elemento sin seleccion actual: mostrar solo ✓.
            try:
                chip.configure(text="✓")
            except TclError:
                pass

    # ── helpers internos ────────────────────────────────────────────
    def _apply_active(self, mod_key: str, *, chip_text: str) -> None:
        row = self._rows[mod_key]
        try:
            row["button"].configure(bootstyle=self.bootstyle_active)
        except TclError:
            pass
        try:
            row["chip_label"].configure(text=chip_text)
        except TclError:
            pass

    def _apply_inactive(self, mod_key: str) -> None:
        row = self._rows[mod_key]
        try:
            row["button"].configure(bootstyle=self.bootstyle_inactive)
        except TclError:
            pass
        try:
            # En inactivo solo dejamos el ✓ si ya fue visitado.
            chip_txt = "✓" if row["visited"] else ""
            row["chip_label"].configure(text=chip_txt)
        except TclError:
            pass


def render_module_buttons(parent, modules, on_open, *, bootstyle="info-outline",
                          header_text=None, header_color=None,
                          subtitle=None, global_modules=None):
    """Renderiza la lista de modulos en `parent` (Frame plano sin scroll).

    parent          : Frame contenedor.
    modules         : list[(mod_key, label, descripcion)] de list_modules_for_phase.
    on_open(key)    : callback al click; recibe el mod_key.
    bootstyle       : estilo del boton ACTIVO (el inactivo es secondary-outline).
    header_text     : titulo opcional arriba.
    header_color    : color opcional del titulo.
    subtitle        : texto opcional bajo el titulo.
    global_modules  : set de mod_keys que NO requieren elemento (siempre
                      activos visualmente). Si es None, todos los modulos
                      se consideran por-elemento.

    Retorna un `ModuleButtonsPanel` controller. El caller llama
    `panel.update_selection(elem_id)` desde el callback de seleccion del
    MeshCanvas, y `panel.mark_visited(mod_key)` despues de abrir un modulo.
    """
    if header_text:
        ttk.Label(
            parent, text=header_text,
            font=("Segoe UI", 11, "bold"),
            foreground=header_color or MODULE_HEADER_FG_COLOR,
        ).pack(anchor=W, padx=10, pady=(10, 3))

    if subtitle:
        ttk.Label(
            parent, text=subtitle,
            font=FONT_UI, foreground=MODULE_DESC_FG_COLOR, wraplength=380,
        ).pack(anchor=W, padx=15, pady=(0, 10))

    panel = ModuleButtonsPanel(
        parent, bootstyle=bootstyle, global_modules=global_modules or set(),
    )

    if not modules:
        ttk.Label(
            parent,
            text="(sin modulos disponibles para esta fase)",
            font=FONT_UI, foreground=MODULE_EMPTY_FG_COLOR,
        ).pack(anchor=W, padx=15, pady=20)
        return panel

    for mod_key, label, desc in modules:
        row = ttk.Frame(parent)
        row.pack(fill=X, padx=15, pady=4)

        # Wrap del on_open para registrar `visited` SOLO si realmente abrio.
        # Convencion: si `on_open(key)` retorna truthy, marcamos. Cualquier
        # callsite que retorne `None` (Pre/Proc/Post legacy) NO marca — el
        # callsite debe retornar `ok` del launcher para optar in. Si lo
        # marcaramos siempre, el chip ✓ aparecería incluso cuando el
        # usuario cancela el simpledialog de seleccion de elemento.
        def _click(k=mod_key):
            opened = False
            try:
                opened = bool(on_open(k))
            finally:
                if opened:
                    panel.mark_visited(k)

        btn = ttk.Button(
            row, text=label, bootstyle=bootstyle,
            width=_BUTTON_WIDTH_CHARS,
            command=_click,
        )
        btn.pack(side=LEFT)

        desc_label = ttk.Label(
            row, text=desc, font=("Segoe UI", 8),
            foreground=MODULE_DESC_FG_COLOR, anchor=W, justify=LEFT,
        )
        desc_label.pack(side=LEFT, fill=X, expand=YES, padx=5)

        # Chip de estado a la derecha — visible solo cuando hay seleccion
        # o cuando el modulo fue visitado (✓). Texto vacio = oculto en la
        # practica porque no toma espacio horizontal perceptible.
        chip = ttk.Label(
            row, text="", font=("Segoe UI", 8, "bold"),
            foreground=TEXT_MUTED_FG, anchor=E,
        )
        chip.pack(side=RIGHT, padx=(4, 0))

        panel._register(mod_key, btn, chip)

        def _update_wrap(event, lbl=desc_label, b=btn, c=chip):
            try:
                btn_w = b.winfo_width()
                chip_w = c.winfo_width()
                avail = event.width - btn_w - chip_w - 25
                lbl.configure(wraplength=max(60, avail))
            except TclError:
                pass

        row.bind("<Configure>", _update_wrap)

    return panel
