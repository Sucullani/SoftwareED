"""
ElementTypeDialog: diálogo del menú Modelo para configurar el tipo de
elemento (Q4 / Q9) con recursos visuales educativos.

Dos pestañas:
  · "Comparación visual"      — Q4 vs Q9 lado a lado con nodos numerados.
  · "Transición Q4 ↔ Q9"      — WebP animado generado en Claude Design
                                 que muestra el ciclo bidireccional sobre
                                 un elemento distorsionado canónico (loop
                                 seamless de 7 s, autoplay, sin controles
                                 visibles). NO muta el modelo.

Para aplicar el cambio al modelo real se selecciona Q4 / Q9 arriba y se
acepta — eso dispara `expand_q4_to_q9` o `shrink_q9_to_q4` (con
confirmación modal en el segundo caso porque se descartan los nodos
internos huérfanos sin cargas/BCs).
"""

import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

import numpy as np

from config.settings import (
    ELEMENT_TYPES, ELEMENT_Q4, ELEMENT_Q9,
    CANVAS_NODE_COLOR, CANVAS_NODE_MID_COLOR, CANVAS_NODE_CENTER_COLOR,
)
from education.components import PlotPanel
from education.components.plot_panel import _theme_colors
from gui.widgets.webp_player import WebpPlayer
from models.mesh_utils import expand_q4_to_q9, shrink_q9_to_q4


VIDEO_FILE = os.path.join("resources", "videos", "q4_q9_transition.webp")


# Coordenadas del mini-elemento sintético en el dominio natural [-1, 1]²
# usado SOLO en la pestaña "Comparación visual" (la transición se reemplazó
# por un video MP4 prerenderizado).
_DEMO_CORNERS = np.array([
    [-1.0, -1.0],   # N1
    [ 1.0, -1.0],   # N2
    [ 1.0,  1.0],   # N3
    [-1.0,  1.0],   # N4
])
_DEMO_MIDS = np.array([
    [ 0.0, -1.0],   # N5 (medio 1-2)
    [ 1.0,  0.0],   # N6 (medio 2-3)
    [ 0.0,  1.0],   # N7 (medio 3-4)
    [-1.0,  0.0],   # N8 (medio 4-1)
])
_DEMO_CENTER = np.array([0.0, 0.0])  # N9


class ElementTypeDialog:
    """Ventana modal para configurar Tipo de Elemento (Q4 ↔ Q9)."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🔲  Tipo de Elemento")
        self.dialog.geometry("820x680")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Variable local: NO mutar el project hasta Aceptar.
        self.element_var = tk.StringVar(value=project.element_type)
        self._video = None

        self._build()
        self._draw_comparison()
        self._center()

    # ─── Layout ─────────────────────────────────────────────────────────
    def _build(self):
        main = ttk.Frame(self.dialog, padding=14)
        main.pack(fill=BOTH, expand=YES)

        self._build_header(main)
        self._build_notebook(main)
        self._build_footer(main)

    def _build_header(self, parent):
        ttk.Label(
            parent, text="Tipo de Elemento Finito",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=W, pady=(0, 4))
        ttk.Label(
            parent,
            text=("Define cuántos nodos tiene cada elemento y, por tanto,"
                  " el orden de las funciones de forma."),
            foreground="#aaa", font=("Segoe UI", 9),
        ).pack(anchor=W, pady=(0, 10))

        sel_frame = ttk.Labelframe(parent, text="  Selección  ", padding=10)
        sel_frame.pack(fill=X, pady=(0, 10))
        for et in ELEMENT_TYPES:
            ttk.Radiobutton(
                sel_frame, text=et, variable=self.element_var, value=et,
                bootstyle="info",
            ).pack(anchor=W, pady=2)

    def _build_notebook(self, parent):
        nb = ttk.Notebook(parent, bootstyle="info")
        nb.pack(fill=BOTH, expand=YES, pady=(0, 10))

        # ── Tab 1: Comparación visual ────────────────────────────────
        tab_cmp = ttk.Frame(nb, padding=6)
        nb.add(tab_cmp, text="  Comparación visual  ")
        self.cmp_panel = PlotPanel(
            tab_cmp, figsize=(7.4, 3.2), subplots=(1, 2),
            show_toolbar=False,
        )
        self.cmp_panel.pack(fill=BOTH, expand=YES)

        # ── Tab 2: Transición Q4 ↔ Q9 (video prerenderizado) ─────────
        tab_anim = ttk.Frame(nb, padding=6)
        nb.add(tab_anim, text="  Transición Q4 ↔ Q9  ")

        # Banner superior con énfasis en la BIDIRECCIONALIDAD del cambio.
        banner = ttk.Frame(tab_anim)
        banner.pack(fill=X, pady=(0, 6))

        ttk.Label(
            banner,
            text="↔  Configuración bidireccional",
            font=("Segoe UI", 11, "bold"),
            foreground=CANVAS_NODE_CENTER_COLOR,
        ).pack(anchor=W)
        ttk.Label(
            banner,
            text=("El cambio Q4 ↔ Q9 se aplica en ambos sentidos sobre "
                  "un mismo elemento distorsionado canónico:\n"
                  "    Q4 → Q9   se generan los 4 nodos medios de arista "
                  "(N5..N8) y el centroide (N9), las aristas pasan a ser "
                  "bicuadráticas (curvas).\n"
                  "    Q9 → Q4   se truncan los nodos internos sin "
                  "datos y las aristas vuelven a ser rectas."),
            font=("Segoe UI", 9), foreground="#cfd2d8",
            justify=LEFT, wraplength=760,
        ).pack(anchor=W, pady=(2, 0))

        # Reproductor de WebP animado (autoplay + loop seamless, sin controles).
        video_frame = ttk.Frame(tab_anim, relief="flat")
        video_frame.pack(fill=BOTH, expand=YES, pady=(6, 0))

        if os.path.exists(VIDEO_FILE):
            try:
                self._video = WebpPlayer(
                    video_frame, scaled=True,
                    background=_theme_colors()["bg"],
                )
                self._video.pack(fill=BOTH, expand=YES)
                self._video.load(VIDEO_FILE)
                # Pequeño delay para que el widget esté montado y haya
                # capturado su tamaño antes de iniciar la reproducción.
                self.dialog.after(150, self._video.play)
            except Exception:
                self._video = None

        if self._video is None:
            # Degradación si el WebP no existe o falla la carga.
            ttk.Label(
                video_frame,
                text=(f"Video no disponible.\n\n"
                      f"Esperado en: {VIDEO_FILE}\n"
                      f"Asegurate de que el archivo existe."),
                foreground="#d68545", font=("Segoe UI", 9),
                justify=CENTER,
            ).pack(expand=YES)

        ttk.Label(
            tab_anim,
            text=("⚠ Demostración educativa: el video NO modifica el "
                  "modelo. Para aplicar el cambio al modelo real, "
                  "seleccioná Q4 o Q9 arriba y presioná Aceptar."),
            foreground="#d68545", font=("Segoe UI", 8), justify=LEFT,
            wraplength=760,
        ).pack(anchor=W, pady=(6, 0))

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

    # ─── Dibujo: Comparación ────────────────────────────────────────────
    def _draw_comparison(self):
        colors = _theme_colors()
        ax_q4, ax_q9 = self.cmp_panel.axes

        for ax, n_nodes, title in (
            (ax_q4, 4, "Q4 · Cuadrilátero bilineal"),
            (ax_q9, 9, "Q9 · Cuadrilátero bicuadrático"),
        ):
            ax.clear()
            self._style_natural_axes(ax, colors)

            # Polígono del elemento (los 4 corners)
            poly = np.vstack([_DEMO_CORNERS, _DEMO_CORNERS[0]])
            ax.plot(poly[:, 0], poly[:, 1],
                    color=colors["accent"], linewidth=1.6, alpha=0.9)

            # Corners siempre visibles
            for i, (x, y) in enumerate(_DEMO_CORNERS, start=1):
                ax.scatter([x], [y], s=110, color=CANVAS_NODE_COLOR,
                           edgecolors="white", linewidths=0.8, zorder=5)
                ax.annotate(str(i), (x, y),
                            xytext=(8, 8), textcoords="offset points",
                            color=colors["fg"], fontsize=10,
                            fontweight="bold")

            # Mids + centro: solo en Q9
            if n_nodes == 9:
                for i, (x, y) in enumerate(_DEMO_MIDS, start=5):
                    ax.scatter([x], [y], s=80, color=CANVAS_NODE_MID_COLOR,
                               edgecolors="white", linewidths=0.6, zorder=5)
                    ax.annotate(str(i), (x, y),
                                xytext=(8, 8), textcoords="offset points",
                                color=colors["fg"], fontsize=9)
                cx, cy = _DEMO_CENTER
                ax.scatter([cx], [cy], s=80, color=CANVAS_NODE_CENTER_COLOR,
                           edgecolors="white", linewidths=0.6, zorder=5)
                ax.annotate("9", (cx, cy),
                            xytext=(8, 8), textcoords="offset points",
                            color=colors["fg"], fontsize=9)

            ax.set_title(title, color=colors["fg"], fontsize=10, pad=8)
            ax.text(
                -0.95, -0.92,
                f"{n_nodes} nodos\n{2 * n_nodes} DOF",
                color=colors["fg"], fontsize=8,
                bbox=dict(facecolor=colors["panel"], edgecolor=colors["grid"],
                          boxstyle="round,pad=0.3"),
            )

        self.cmp_panel.figure.tight_layout()
        self.cmp_panel.redraw()

    @staticmethod
    def _style_natural_axes(ax, colors):
        """Estilo coherente para los ejes en coordenadas naturales [-1,1]²."""
        ax.set_xlim(-1.3, 1.3)
        ax.set_ylim(-1.3, 1.3)
        ax.set_aspect("equal")
        ax.set_facecolor(colors["panel"])
        ax.grid(True, color=colors["grid"], linewidth=0.5, alpha=0.6)
        for spine in ax.spines.values():
            spine.set_color(colors["grid"])
        ax.tick_params(colors=colors["fg"], labelsize=8)
        ax.set_xticks([-1, 0, 1])
        ax.set_yticks([-1, 0, 1])
        ax.set_xlabel("ξ", color=colors["fg"], fontsize=9)
        ax.set_ylabel("η", color=colors["fg"], fontsize=9)

    # ─── Limpieza del video ─────────────────────────────────────────────
    def _stop_video(self):
        """Detiene la reproducción del video y libera el thread interno."""
        if self._video is not None:
            try:
                self._video.stop()
            except Exception:
                pass

    # ─── Aceptar / Cancelar ────────────────────────────────────────────
    def _on_accept(self):
        new_et = self.element_var.get()
        if new_et == self.project.element_type:
            # Sin cambio real: cerrar sin tocar nada.
            self._on_cancel()
            return

        # Snapshot para undo antes de mutar.
        try:
            stack = getattr(self.main_window, "undo_stack", None)
            if stack is not None:
                stack.capture("cambio de tipo de elemento")
        except Exception:
            pass

        has_q4 = any(e.num_nodes == 4 for e in self.project.elements.values())
        has_q9 = any(e.num_nodes == 9 for e in self.project.elements.values())
        mids = centers = 0

        if new_et == ELEMENT_Q9 and has_q4:
            mids, centers = expand_q4_to_q9(self.project)
        elif new_et == ELEMENT_Q4 and has_q9:
            resp = messagebox.askyesno(
                "Reducir a Q4",
                "El modelo tiene elementos Q9. Al cambiar a Q4 se descartan "
                "los nodos medios y el centroide de cada elemento (solo se "
                "conservan los 4 vertices).\n\nLos nodos medios con carga o "
                "restriccion se preservan como nodos huerfanos para que no "
                "pierdas datos.\n\n¿Continuar?",
                parent=self.dialog,
            )
            if not resp:
                return
            shrink_q9_to_q4(self.project)
        else:
            # Modelo vacío o tipo coherente sin elementos: solo registrar.
            self.project.element_type = new_et

        self.project.is_modified = True
        self.project.is_solved = False

        if self.main_window is not None:
            try:
                self.main_window.element_type_var.set(self.project.element_type)
                self.main_window._refresh_all_tabs()
                self.main_window._update_status_info()
                self.main_window._refresh_menu_state()
                self.main_window._update_title()
                extra = ""
                if mids or centers:
                    extra = (f"  ({mids} nodos medios + {centers} centroides "
                             f"generados)")
                self.main_window.set_status(
                    f"Tipo de elemento: {self.project.element_type}{extra}"
                )
            except Exception:
                pass

        self._stop_video()
        self.dialog.destroy()

    def _on_cancel(self):
        self._stop_video()
        self.dialog.destroy()

    def _center(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
