"""
UnitsGravityDialog: diálogo combinado para Sistema de Unidades y Gravedad.
Combobox con los sistemas disponibles + spinbox para valor de gravedad +
checkbox de inclusión de peso propio en el análisis.

Cuando se elige "Personalizado", aparece un mini-frame con 3 entries
para longitud / fuerza / tensión que el usuario puede definir libremente.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from config.units import UNIT_SYSTEMS, get_unit_system_names


CUSTOM_KEY = "Personalizado"


class UnitsGravityDialog:
    """Ventana modal para configurar Sistema de Unidades y gravedad."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("📏  Unidades y Gravedad")
        self.dialog.geometry("520x580")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        # Estado
        self.unit_var = tk.StringVar(value=project.unit_system)
        self.gravity_var = tk.StringVar(value=f"{project.gravity:.4g}")
        self.include_grav_var = tk.BooleanVar(value=project.include_gravity)

        cu = getattr(project, "custom_units",
                     {"longitud": "-", "fuerza": "-", "esfuerzo": "-"})
        self.custom_length_var = tk.StringVar(value=cu.get("longitud", "-"))
        self.custom_force_var = tk.StringVar(value=cu.get("fuerza", "-"))
        self.custom_stress_var = tk.StringVar(value=cu.get("esfuerzo", "-"))

        self._build()
        self._center()

    def _build(self):
        main = ttk.Frame(self.dialog, padding=20)
        main.pack(fill=BOTH, expand=YES)

        ttk.Label(
            main, text="Unidades y gravedad",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            main,
            text="Define el sistema de unidades y el valor de gravedad usado\n"
                 "para el cálculo de peso propio.",
            foreground="#aaa", font=("Segoe UI", 9), justify=LEFT,
        ).pack(anchor=W, pady=(0, 14))

        # ─── Sistema de unidades ────────────────────────────────────────
        u_frame = ttk.Labelframe(main, text="  Sistema de Unidades  ", padding=12)
        u_frame.pack(fill=X, pady=(0, 10))

        self.combo = ttk.Combobox(
            u_frame, textvariable=self.unit_var,
            values=get_unit_system_names(),
            state="readonly", font=("Segoe UI", 10),
        )
        self.combo.pack(fill=X, pady=(0, 8))
        self.combo.bind("<<ComboboxSelected>>", self._on_unit_changed)

        # Labels informativos de unidades derivadas
        info = ttk.Frame(u_frame)
        info.pack(fill=X)

        self.lbl_length = ttk.Label(info, text="", font=("Segoe UI", 9))
        self.lbl_force = ttk.Label(info, text="", font=("Segoe UI", 9))
        self.lbl_stress = ttk.Label(info, text="", font=("Segoe UI", 9))

        self.lbl_length.grid(row=0, column=0, sticky=W, padx=(0, 12))
        self.lbl_force.grid(row=0, column=1, sticky=W, padx=(0, 12))
        self.lbl_stress.grid(row=0, column=2, sticky=W)

        # ─── Frame "Personalizado" (se muestra sólo cuando aplica) ──────
        self.custom_frame = ttk.Labelframe(
            main, text="  Unidades Personalizadas  ", padding=12,
            bootstyle="info",
        )

        ttk.Label(
            self.custom_frame,
            text="Define las etiquetas que verás en toda la interfaz.\n"
                 "No convierten automáticamente los valores — sólo son rótulos.",
            foreground="#aaa", font=("Segoe UI", 8), justify=LEFT,
        ).grid(row=0, column=0, columnspan=2, sticky=W, pady=(0, 8))

        ttk.Label(self.custom_frame, text="Longitud:").grid(
            row=1, column=0, sticky=E, pady=3, padx=(0, 8)
        )
        ttk.Entry(
            self.custom_frame, textvariable=self.custom_length_var,
            width=18, font=("Segoe UI", 10),
        ).grid(row=1, column=1, sticky=W, pady=3)

        ttk.Label(self.custom_frame, text="Fuerza:").grid(
            row=2, column=0, sticky=E, pady=3, padx=(0, 8)
        )
        ttk.Entry(
            self.custom_frame, textvariable=self.custom_force_var,
            width=18, font=("Segoe UI", 10),
        ).grid(row=2, column=1, sticky=W, pady=3)

        ttk.Label(self.custom_frame, text="Tensión:").grid(
            row=3, column=0, sticky=E, pady=3, padx=(0, 8)
        )
        ttk.Entry(
            self.custom_frame, textvariable=self.custom_stress_var,
            width=18, font=("Segoe UI", 10),
        ).grid(row=3, column=1, sticky=W, pady=3)

        # Botones de preset para rellenar rápido
        preset_row = ttk.Frame(self.custom_frame)
        preset_row.grid(row=4, column=0, columnspan=2, sticky=W, pady=(8, 0))
        ttk.Label(preset_row, text="Rellenar con:", font=("Segoe UI", 8)).pack(
            side=LEFT, padx=(0, 4)
        )
        for label, length, force, stress in (
            ("kgf · cm", "cm", "kgf", "kgf/cm²"),
            ("tonf · m", "m", "tonf", "tonf/m²"),
            ("lbf · ft", "ft", "lbf", "psi"),
        ):
            ttk.Button(
                preset_row, text=label, bootstyle="secondary-outline",
                command=lambda l=length, f=force, s=stress:
                    self._fill_custom(l, f, s),
                width=10,
            ).pack(side=LEFT, padx=2)

        # ─── Gravedad ───────────────────────────────────────────────────
        self.g_frame = ttk.Labelframe(main, text="  Gravedad  ", padding=12)
        self.g_frame.pack(fill=X, pady=(0, 10))

        g_row = ttk.Frame(self.g_frame)
        g_row.pack(fill=X, pady=(0, 6))

        ttk.Label(g_row, text="Valor:").pack(side=LEFT, padx=(0, 8))
        self.grav_entry = ttk.Spinbox(
            g_row, from_=0.0, to=999.0, increment=0.01,
            textvariable=self.gravity_var, width=12,
            font=("Segoe UI", 10),
        )
        self.grav_entry.pack(side=LEFT)

        self.lbl_grav_unit = ttk.Label(g_row, text="", font=("Segoe UI", 9))
        self.lbl_grav_unit.pack(side=LEFT, padx=(8, 0))

        ttk.Checkbutton(
            self.g_frame,
            text="Incluir peso propio en el análisis (usado por M6 y fuerzas equivalentes)",
            variable=self.include_grav_var,
            bootstyle="info-round-toggle",
        ).pack(anchor=W, pady=(4, 0))

        ttk.Label(
            self.g_frame,
            text="El valor se guarda con el proyecto y se usa cuando el módulo\n"
                 "M6 calcula fuerzas nodales equivalentes por peso propio.",
            foreground="#888", font=("Segoe UI", 8), justify=LEFT,
        ).pack(anchor=W, pady=(6, 0))

        # ─── Botones ────────────────────────────────────────────────────
        btn_bar = ttk.Frame(main)
        btn_bar.pack(fill=X, pady=(12, 0))

        ttk.Button(
            btn_bar, text="Cancelar", bootstyle="secondary",
            command=self._on_cancel, width=12,
        ).pack(side=RIGHT, padx=4)
        ttk.Button(
            btn_bar, text="Aceptar", bootstyle="success",
            command=self._on_accept, width=12,
        ).pack(side=RIGHT, padx=4)

        # Estado inicial de visibilidad + labels + live refresh
        self._sync_custom_frame()
        self._refresh_unit_labels()
        for var in (self.custom_length_var, self.custom_force_var,
                    self.custom_stress_var):
            var.trace_add("write", lambda *_: self._refresh_unit_labels())

    def _fill_custom(self, length, force, stress):
        self.custom_length_var.set(length)
        self.custom_force_var.set(force)
        self.custom_stress_var.set(stress)
        self._refresh_unit_labels()

    def _sync_custom_frame(self):
        """Muestra / oculta el frame de unidades personalizadas entre
        el combobox y el frame de gravedad."""
        if self.unit_var.get() == CUSTOM_KEY:
            self.custom_frame.pack(
                fill=X, pady=(0, 10), before=self.g_frame,
            )
        else:
            self.custom_frame.pack_forget()

    def _refresh_unit_labels(self):
        if self.unit_var.get() == CUSTOM_KEY:
            length = self.custom_length_var.get().strip() or "-"
            force = self.custom_force_var.get().strip() or "-"
            stress = self.custom_stress_var.get().strip() or "-"
        else:
            info = UNIT_SYSTEMS.get(self.unit_var.get(), {})
            length = info.get("longitud", "-")
            force = info.get("fuerza", "-")
            stress = info.get("esfuerzo", "-")

        self.lbl_length.config(text=f"Longitud: {length}")
        self.lbl_force.config(text=f"Fuerza: {force}")
        self.lbl_stress.config(text=f"Tensión: {stress}")

        if length == "-":
            self.lbl_grav_unit.config(text="(unidades consistentes)")
        else:
            self.lbl_grav_unit.config(text=f"{length}/s²")

    def _on_unit_changed(self, _event=None):
        self._sync_custom_frame()
        self._refresh_unit_labels()

    def _on_accept(self):
        try:
            grav = float(self.gravity_var.get())
            if grav < 0:
                raise ValueError("La gravedad no puede ser negativa.")
        except ValueError:
            messagebox.showerror(
                "Error", "Valor de gravedad inválido.",
                parent=self.dialog,
            )
            return

        # Snapshot para undo: detecta cambio real antes de capturar
        new_us = self.unit_var.get()
        if (new_us != self.project.unit_system
                or grav != self.project.gravity
                or bool(self.include_grav_var.get()) != self.project.include_gravity):
            try:
                stack = getattr(self.main_window, "undo_stack", None)
                if stack is not None:
                    stack.capture("cambio de unidades/gravedad")
            except Exception:
                pass

        if self.unit_var.get() == CUSTOM_KEY:
            length = self.custom_length_var.get().strip()
            force = self.custom_force_var.get().strip()
            stress = self.custom_stress_var.get().strip()
            if not (length and force and stress):
                messagebox.showerror(
                    "Error",
                    "Complete las tres etiquetas (longitud, fuerza, tensión)\n"
                    "para el sistema personalizado.",
                    parent=self.dialog,
                )
                return
            self.project.custom_units = {
                "longitud": length,
                "fuerza": force,
                "esfuerzo": stress,
            }

        self.project.unit_system = self.unit_var.get()
        self.project.gravity = grav
        self.project.include_gravity = bool(self.include_grav_var.get())
        self.project.is_modified = True
        self.project.is_solved = False

        if self.main_window is not None:
            try:
                self.main_window.unit_system_var.set(self.project.unit_system)
                self.main_window._refresh_all_tabs()
                self.main_window._update_status_info()
                self.main_window._update_title()
                self.main_window._refresh_menu_state()
                self.main_window.set_status(
                    f"Unidades: {self.project.unit_system} · "
                    f"g = {self.project.gravity:g}"
                )
            except Exception:
                pass

        self.dialog.destroy()

    def _on_cancel(self):
        self.dialog.destroy()

    def _center(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
