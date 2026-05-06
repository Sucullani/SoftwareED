"""
AnalysisTypeDialog: diálogo del menú Modelo para configurar el tipo de
análisis (Tensión Plana / Deformación Plana).

Layout minimalista — UNA SOLA VENTANA de video (WebP animado) que cambia
su contenido según la selección TP/DP:
  · `resources/videos/tension_plana.webp`       — selector en TP
  · `resources/videos/deformacion_plana.webp`   — selector en DP

La explicación visual de cada caso (esquemas, casos reales, hipótesis)
está embebida en cada video — no se duplica con esquemas matplotlib.
La matriz constitutiva D vive en el módulo educativo M3 (fase Proceso),
porque depende del material asignado a cada elemento.

Aceptar guarda `project.analysis_type` con captura undo previa.
"""

import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.settings import (
    ANALYSIS_TYPES, ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    PHASE_PROC_COLOR,
)
from education.components.plot_panel import _theme_colors
from gui.widgets.webp_player import WebpPlayer


VIDEO_DIR = os.path.join("resources", "videos")
VIDEO_TP = os.path.join(VIDEO_DIR, "tension_plana.webp")
VIDEO_DP = os.path.join(VIDEO_DIR, "deformacion_plana.webp")


class AnalysisTypeDialog:
    """Ventana modal para configurar Tipo de Análisis (TP ↔ DP)."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent
        self._video = None
        self._current_source = None  # path del video actualmente cargado

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🔬  Tipo de Análisis")
        self.dialog.geometry("900x680")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Selector TP/DP (variable local, NO muta hasta Aceptar)
        self.analysis_var = tk.StringVar(value=project.analysis_type)
        self.analysis_var.trace_add("write", lambda *a: self._on_case_changed())

        self._build()
        # Cargar el video correspondiente al estado inicial
        self.dialog.after(150, self._load_video_for_current_case)
        self._center()

    # ─── Layout ─────────────────────────────────────────────────────────
    def _build(self):
        main = ttk.Frame(self.dialog, padding=14)
        main.pack(fill=BOTH, expand=YES)

        self._build_header(main)
        self._build_video(main)
        self._build_footer(main)

    def _build_header(self, parent):
        ttk.Label(
            parent, text="Tipo de Análisis (2D)",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            parent,
            text=("Cada caso asume una hipótesis geométrica distinta "
                  "y produce una matriz constitutiva D diferente. La "
                  "matriz D, sin embargo, depende del material asignado "
                  "a cada elemento — explorala desde el módulo M3 "
                  "(Proceso > Educación)."),
            foreground="#aaa", font=("Segoe UI", 9),
            wraplength=860, justify=LEFT,
        ).pack(anchor=W, pady=(0, 10))

        sel_frame = ttk.Labelframe(parent, text="  Selección  ", padding=10)
        sel_frame.pack(fill=X, pady=(0, 10))
        for at in ANALYSIS_TYPES:
            ttk.Radiobutton(
                sel_frame, text=at, variable=self.analysis_var, value=at,
                bootstyle="info",
            ).pack(anchor=W, pady=2)

        ttk.Label(
            sel_frame,
            text=("ℹ  Al cambiar la selección, el video de abajo se "
                  "actualiza al caso correspondiente."),
            font=("Segoe UI", 8), foreground=PHASE_PROC_COLOR,
        ).pack(anchor=W, pady=(6, 0))

    def _build_video(self, parent):
        """Una única ventana de video que se reasigna según TP/DP."""
        self.video_frame = ttk.Labelframe(
            parent, text="  Explicación en video  ",
            bootstyle="info", padding=4,
        )
        self.video_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))

        # Reproductor WebP (loop seamless interno, sin controles).
        # Si los .webp no existen, _load_video_for_current_case lo reemplaza
        # por un mensaje informativo en el frame.
        self._video = WebpPlayer(
            self.video_frame, scaled=True,
            background=_theme_colors()["bg"],
        )
        self._video.pack(fill=BOTH, expand=YES)

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

    # ─── Reactividad TP ↔ DP ────────────────────────────────────────────
    def _video_for_case(self, case: str) -> str:
        if case == ANALYSIS_PLANE_STRESS:
            return VIDEO_TP
        return VIDEO_DP

    def _load_video_for_current_case(self):
        """Carga el WebP correspondiente al caso seleccionado y arranca
        autoplay. Si el archivo no existe o falla, muestra un mensaje
        informativo en el frame del video."""
        case = self.analysis_var.get()
        path = self._video_for_case(case)

        # Si ya está cargado el mismo archivo, no recargar.
        if path == self._current_source:
            return

        if not os.path.exists(path):
            self._show_missing_video_message(case, path)
            self._current_source = None
            return

        self._restore_video_widget()
        try:
            self._video.stop()
        except Exception:
            pass
        try:
            self._video.load(path)
            self._current_source = path
            self.dialog.after(120, self._video.play)
        except Exception as exc:
            self._show_missing_video_message(case, path, exc=exc)
            self._current_source = None

    def _show_missing_video_message(self, case, path, exc=None):
        """Reemplaza el widget de video por un label informativo."""
        for w in self.video_frame.winfo_children():
            w.destroy()
        self._video = None
        msg = (f"Video del caso '{case}' no disponible.\n\n"
               f"Esperado en: {path}\n\n"
               f"Coloca el WebP animado en esa ruta para verlo aquí.")
        if exc:
            msg += f"\n\nError: {exc}"
        ttk.Label(
            self.video_frame, text=msg,
            foreground="#d68545", font=("Segoe UI", 9),
            justify=CENTER,
        ).pack(expand=YES)

    def _restore_video_widget(self):
        """Si el frame había sido reemplazado por un mensaje, recrea el
        widget de video. Sin efecto si ya está intacto."""
        if self._video is not None and self._video.winfo_exists():
            return
        for w in self.video_frame.winfo_children():
            w.destroy()
        self._video = WebpPlayer(
            self.video_frame, scaled=True,
            background=_theme_colors()["bg"],
        )
        self._video.pack(fill=BOTH, expand=YES)

    def _on_case_changed(self):
        """Cambio TP/DP — recarga el video correspondiente."""
        self._load_video_for_current_case()

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
                self.main_window._refresh_menu_state()
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
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
