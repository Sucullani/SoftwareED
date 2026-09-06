"""
AnalysisTypeDialog: diálogo del menú Modelo para configurar el tipo de
análisis (Tensión Plana / Deformación Plana).

Layout minimalista: un único video lado-a-lado
(`resources/videos/tension_deformacion_plana.webp`) que muestra TP y DP
en paralelo + dos toolbutton radios alineados con las columnas del video.

El paralelismo visual es deliberado: seleccionar 'Tensión Plana' es
elegir la columna izquierda de lo que el alumno está viendo, y
viceversa. No hace falta explicarlo con texto — la disposición lo dice.

NO contiene la matriz constitutiva D — eso vive en el módulo educativo
M4 (Proceso > Educación), porque D depende del material asignado a cada
elemento.

Aceptar guarda `project.analysis_type` con captura undo previa.
"""

import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.settings import (
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    ORPHAN_NODE_FG, FONT_UI, resource_path,
)
from education.components.edu_plot_style import _theme_colors
from gui.widgets.webp_player import WebpPlayer


VIDEO_PATH = resource_path("videos", "tension_deformacion_plana.webp")

# Tamaño del video. Nativo: 900×600 (3:2). Lo escalamos a 720×480 para
# que el diálogo entre cómodo en pantallas comunes sin perder calidad.
VIDEO_W, VIDEO_H = 720, 480
DIALOG_W, DIALOG_H = 760, 660


from gui.dialogs._dialog_helpers import center_dialog
class AnalysisTypeDialog:
    """Ventana modal para configurar Tipo de Análisis (TP ↔ DP)."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent
        self._video = None

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🔬  Tipo de Análisis")
        self.dialog.geometry(f"{DIALOG_W}x{DIALOG_H}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Selector TP/DP. La variable NO muta el project hasta Aceptar.
        self.analysis_var = tk.StringVar(value=project.analysis_type)

        self._build()
        # Diferir la carga del video para que el widget tenga tamaño
        # real antes del primer render (si no, escala a 1×1 px).
        self.dialog.after(120, self._load_video)
        self._center()

    # ─── Layout ─────────────────────────────────────────────────────────
    def _build(self):
        main = ttk.Frame(self.dialog, padding=18)
        main.pack(fill=BOTH, expand=YES)

        self._build_video(main)
        self._build_selector(main)
        self._build_footer(main)

    def _build_video(self, parent):
        """Container de tamaño fijo (720×480) que aloja el WebpPlayer.
        `pack_propagate(False)` impide que el frame se ajuste al contenido
        — así garantizamos que el video tenga su tamaño objetivo sin
        importar el primer ciclo de Configure."""
        container = ttk.Frame(parent, width=VIDEO_W, height=VIDEO_H)
        container.pack_propagate(False)
        container.pack(pady=(0, 14))
        self.video_frame = container

        self._video = WebpPlayer(
            container, scaled=True,
            background=_theme_colors()["bg"],
        )
        self._video.pack(fill=BOTH, expand=YES)

    def _build_selector(self, parent):
        """Dos toolbutton radios en grid 50/50 — visualmente alineados
        con las columnas TP y DP del video de arriba. El alumno asocia
        sin esfuerzo 'la columna izquierda es Tensión Plana, la derecha
        es Deformación Plana'. No hay otro texto que justifique esto
        porque la disposición lo dice todo."""
        sel = ttk.Frame(parent)
        sel.pack(fill=X, pady=(0, 16))
        sel.columnconfigure(0, weight=1, uniform="case")
        sel.columnconfigure(1, weight=1, uniform="case")

        ttk.Radiobutton(
            sel, text="Tensión Plana",
            variable=self.analysis_var, value=ANALYSIS_PLANE_STRESS,
            bootstyle="info-toolbutton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=10)

        ttk.Radiobutton(
            sel, text="Deformación Plana",
            variable=self.analysis_var, value=ANALYSIS_PLANE_STRAIN,
            bootstyle="info-toolbutton",
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=10)

    def _build_footer(self, parent):
        btn_bar = ttk.Frame(parent)
        btn_bar.pack(fill=X)

        ttk.Button(
            btn_bar, text="Cancelar", bootstyle="secondary",
            command=self._on_cancel, width=12,
        ).pack(side=RIGHT, padx=4)
        ttk.Button(
            btn_bar, text="Aceptar", bootstyle="success",
            command=self._on_accept, width=12,
        ).pack(side=RIGHT, padx=4)

    # ─── Ciclo de vida del video ────────────────────────────────────────
    def _load_video(self):
        """Carga el único asset TP+DP. Si falla, reemplaza el container
        por un mensaje informativo sin romper el diálogo."""
        if not self.dialog.winfo_exists():
            return  # el dialogo se cerro dentro de los 120 ms del after()
        if not os.path.exists(VIDEO_PATH):
            self._show_missing_video()
            return
        try:
            self._video.load(VIDEO_PATH)
            # Guard de existencia: cerrar el dialogo antes de los 80 ms
            # disparaba el callback sobre widgets ya destruidos (TclError).
            self.dialog.after(
                80,
                lambda: self._video.play() if self.dialog.winfo_exists() else None,
            )
        except Exception as exc:
            self._show_missing_video(exc=exc)

    def _show_missing_video(self, exc=None):
        for w in self.video_frame.winfo_children():
            w.destroy()
        self._video = None
        msg = (f"Video no disponible.\n\n"
               f"Esperado en: {VIDEO_PATH}\n\n"
               f"Renderá el .webp con tools/render_tp_dp_manim/.")
        if exc:
            msg += f"\n\nError: {exc}"
        ttk.Label(
            self.video_frame, text=msg,
            foreground=ORPHAN_NODE_FG, font=FONT_UI,
            justify=CENTER,
        ).pack(expand=YES)

    # ─── Aceptar / Cancelar ────────────────────────────────────────────
    def _on_accept(self):
        new_at = self.analysis_var.get()
        if new_at == self.project.analysis_type:
            self._on_cancel()
            return

        try:
            stack = getattr(self.main_window, "undo_stack", None)
            if stack is not None:
                stack.capture("cambio de tipo de análisis")
        except Exception:
            pass

        self.project.analysis_type = new_at
        self.project.is_modified = True
        self.project.is_solved = False

        if self.main_window is not None:
            try:
                self.main_window.analysis_type_var.set(self.project.analysis_type)
                self.main_window._refresh_all_tabs()
                self.main_window._update_status_info()
                self.main_window._update_title()
                self.main_window.set_status(
                    f"Tipo de análisis: {self.project.analysis_type}"
                )
            except Exception:
                pass

        self._stop_video()
        self.dialog.destroy()

    def _on_cancel(self):
        self._stop_video()
        self.dialog.destroy()

    def _stop_video(self):
        if self._video is not None:
            try:
                self._video.stop()
            except Exception:
                pass

    def _center(self):
        center_dialog(self.dialog, self.parent)
