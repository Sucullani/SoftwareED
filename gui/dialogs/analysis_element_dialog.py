"""
AnalysisElementDialog: diálogo combinado que agrupa por afinidad dos
configuraciones del modelo estrechamente relacionadas: tipo de análisis
(tensión plana / deformación plana) y tipo de elemento (Q4 / Q9) con un botón
de conversión automática Q4 -> Q9 que genera los 5 nodos faltantes.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from config.settings import (
    ANALYSIS_TYPES, ANALYSIS_PLANE_STRESS,
    ELEMENT_TYPES, ELEMENT_Q4, ELEMENT_Q9,
)
from models.mesh_utils import expand_q4_to_q9


class AnalysisElementDialog:
    """Ventana modal para configurar Tipo de Análisis + Tipo de Elemento."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🔬  Análisis y Elemento")
        self.dialog.geometry("520x520")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        # Variables locales (no tocar proyecto hasta Aceptar)
        self.analysis_var = tk.StringVar(value=project.analysis_type)
        self.element_var = tk.StringVar(value=project.element_type)

        self._build()
        self._center()

    def _build(self):
        main = ttk.Frame(self.dialog, padding=20)
        main.pack(fill=BOTH, expand=YES)

        ttk.Label(
            main,
            text="Configuración del análisis",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            main,
            text="Estos dos parámetros definen cómo se formula el elemento.",
            foreground="#aaa", font=("Segoe UI", 9),
        ).pack(anchor=W, pady=(0, 14))

        # ─── Tipo de análisis ───────────────────────────────────────────
        an_frame = ttk.Labelframe(main, text="  Tipo de Análisis  ", padding=12)
        an_frame.pack(fill=X, pady=(0, 10))

        for at in ANALYSIS_TYPES:
            ttk.Radiobutton(
                an_frame, text=at, variable=self.analysis_var, value=at,
                bootstyle="info",
            ).pack(anchor=W, pady=2)

        tip_an = (
            "Tensión plana: cuerpos delgados (placas, láminas).\n"
            "Deformación plana: cuerpos largos (túneles, presas)."
        )
        ttk.Label(
            an_frame, text=tip_an, foreground="#888",
            font=("Segoe UI", 8), justify=LEFT,
        ).pack(anchor=W, pady=(6, 0))

        # ─── Tipo de elemento ───────────────────────────────────────────
        el_frame = ttk.Labelframe(main, text="  Tipo de Elemento  ", padding=12)
        el_frame.pack(fill=X, pady=(0, 10))

        for et in ELEMENT_TYPES:
            ttk.Radiobutton(
                el_frame, text=et, variable=self.element_var, value=et,
                bootstyle="info", command=self._on_element_changed,
            ).pack(anchor=W, pady=2)

        self.q9_note = ttk.Label(
            el_frame,
            text=(
                "ℹ  Para Q9 basta con definir los 4 vértices de cada elemento\n"
                "     en el spreadsheet. Los 5 nodos faltantes (4 medios de\n"
                "     arista + 1 centro) se generan automáticamente."
            ),
            foreground="#4fc3f7", font=("Segoe UI", 8), justify=LEFT,
        )

        # Botón de conversión sólo si aplica
        self.convert_btn = ttk.Button(
            el_frame,
            text="🔁  Convertir elementos Q4 → Q9",
            bootstyle="warning-outline",
            command=self._convert_q4_to_q9,
        )

        self._refresh_q9_widgets()

        # ─── Botones Aceptar / Cancelar ─────────────────────────────────
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

    def _refresh_q9_widgets(self):
        """Muestra/oculta la nota Q9 y el botón de conversión según la selección."""
        self.q9_note.pack_forget()
        self.convert_btn.pack_forget()

        if self.element_var.get() == ELEMENT_Q9:
            self.q9_note.pack(anchor=W, pady=(8, 4))
            # Botón útil si hay elementos Q4 en el proyecto
            has_q4 = any(
                e.num_nodes == 4 for e in self.project.elements.values()
            )
            if has_q4:
                self.convert_btn.pack(anchor=W, pady=(4, 0), fill=X)

    def _on_element_changed(self):
        self._refresh_q9_widgets()

    def _convert_q4_to_q9(self):
        """Ejecuta la expansión Q4 -> Q9 sobre el proyecto actual."""
        if not any(e.num_nodes == 4 for e in self.project.elements.values()):
            messagebox.showinfo(
                "Conversión",
                "No hay elementos Q4 para convertir.",
                parent=self.dialog,
            )
            return

        resp = messagebox.askyesno(
            "Convertir Q4 → Q9",
            "Se generarán los nodos medios y el centro para cada elemento Q4.\n"
            "Esta operación modifica la malla.\n\n¿Continuar?",
            parent=self.dialog,
        )
        if not resp:
            return

        mids, centers = expand_q4_to_q9(self.project)

        messagebox.showinfo(
            "Conversión completa",
            f"Se añadieron {mids} nodos medios y {centers} nodos centro.\n"
            f"Total de nodos: {self.project.num_nodes}.",
            parent=self.dialog,
        )

        if self.main_window is not None:
            try:
                self.main_window._refresh_all_tabs()
                self.main_window._update_status_info()
            except Exception:
                pass

        self._refresh_q9_widgets()

    def _on_accept(self):
        self.project.analysis_type = self.analysis_var.get()

        # Si el usuario cambió a Q9 pero los elementos todavía son Q4,
        # expandir automáticamente (safety net).
        new_et = self.element_var.get()
        if new_et == ELEMENT_Q9 and any(
            e.num_nodes == 4 for e in self.project.elements.values()
        ):
            expand_q4_to_q9(self.project)
        else:
            self.project.element_type = new_et

        self.project.is_modified = True
        self.project.is_solved = False

        if self.main_window is not None:
            try:
                self.main_window.analysis_type_var.set(self.project.analysis_type)
                self.main_window.element_type_var.set(self.project.element_type)
                self.main_window._refresh_all_tabs()
                self.main_window._update_status_info()
                self.main_window._refresh_menu_state()
                self.main_window._update_title()
                self.main_window.set_status(
                    f"Modelo: {self.project.analysis_type} · "
                    f"{self.project.element_type}"
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
