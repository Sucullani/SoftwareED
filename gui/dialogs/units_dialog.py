"""
UnitsDialog: dialogo del menu Modelo > Unidades.

Layout minimalista — un combobox con los 8 sistemas predefinidos +
footer. Sin chip-line de unidades derivadas (redundante con el nombre
del sistema en el combobox: 'SI (N, mm, MPa)' ya enumera las tres
unidades). Sin modal de confirmacion al cambiar: la conversion de
valores se aplica automaticamente — el usuario ve el cambio reflejado
en los headers de tablas y en los valores numericos.

El modo "Personalizado" fue eliminado en 2026-05 (no aportaba conversion
real, solo rotulos). Los .edufem legacy con ese sistema se migran al
default automaticamente en `ProjectModel.from_dict`.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.units import (
    get_unit_system_names, can_convert, get_conversion_factors,
)


from gui.dialogs._dialog_helpers import center_dialog
class UnitsDialog:
    """Ventana modal para configurar Sistema de Unidades del proyecto."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("📏  Unidades")
        self.dialog.geometry("440x180")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        self.unit_var = tk.StringVar(value=project.unit_system)

        self._build()
        self._center()

    def _build(self):
        main = ttk.Frame(self.dialog, padding=20)
        main.pack(fill=BOTH, expand=YES)

        ttk.Label(
            main, text="Sistema de unidades",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=W, pady=(0, 12))

        self.combo = ttk.Combobox(
            main, textvariable=self.unit_var,
            values=get_unit_system_names(),
            state="readonly", font=("Segoe UI", 10),
        )
        self.combo.pack(fill=X)

        btn_bar = ttk.Frame(main)
        btn_bar.pack(fill=X, pady=(20, 0), side=BOTTOM)
        ttk.Button(
            btn_bar, text="Cancelar", bootstyle="secondary",
            command=self._on_cancel, width=12,
        ).pack(side=RIGHT, padx=4)
        ttk.Button(
            btn_bar, text="Aceptar", bootstyle="success",
            command=self._on_accept, width=12,
        ).pack(side=RIGHT, padx=4)

    def _on_accept(self):
        new_us = self.unit_var.get()
        old_us = self.project.unit_system

        if new_us == old_us:
            self.dialog.destroy()
            return

        # Snapshot para undo antes de mutar.
        try:
            stack = getattr(self.main_window, "undo_stack", None)
            if stack is not None:
                stack.capture("cambio de unidades")
        except Exception:
            pass

        # Conversion automatica: aplica los factores entre los dos
        # sistemas. Si por algun motivo no es convertible (sistema legacy
        # desconocido), cae a "solo cambiar etiqueta".
        converted = False
        length_factor = 1.0
        if can_convert(old_us, new_us):
            try:
                factors = get_conversion_factors(old_us, new_us)
                self.project.convert_units(factors)
                length_factor = factors["length"]
                converted = True
            except ValueError:
                pass

        self.project.unit_system = new_us
        self.project.is_modified = True
        self.project.is_solved = False

        if self.main_window is not None:
            try:
                # Compensar la camara del MeshCanvas: world_to_screen es
                # `sx = x * scale + offset_x`. Si todas las coords se
                # multiplicaron por `length_factor`, dividir `scale` por
                # el mismo factor preserva la posicion en pantalla de
                # cada nodo (offsets quedan igual porque el origen world
                # (0,0) siempre mapea a (offset_x, offset_y) sin importar
                # el scale). El modelo NO salta ni cambia de tamaño —
                # solo cambian los numeros que el usuario lee.
                if converted and length_factor != 1.0:
                    canvas = getattr(self.main_window, "mesh_canvas", None)
                    if canvas is not None and getattr(canvas, "scale", None):
                        canvas.scale /= length_factor
                self.main_window.unit_system_var.set(self.project.unit_system)
                self.main_window._refresh_all_tabs()
                self.main_window._update_status_info()
                self.main_window._update_title()
                self.main_window._refresh_menu_state()
                suffix = " (valores convertidos)" if converted else ""
                self.main_window.set_status(
                    f"Unidades: {self.project.unit_system}{suffix}"
                )
            except Exception:
                pass

        self.dialog.destroy()

    def _on_cancel(self):
        self.dialog.destroy()

    def _center(self):
        center_dialog(self.dialog, self.parent)
