"""
ElementTypeDialog: dialogo del menu Modelo para configurar el tipo de
elemento (Q4 / Q9).

Layout minimalista (760x660, alineado al patron de AnalysisTypeDialog):
un unico video del cantilever Q4 vs Q9 (`resources/videos/
cantilever_q4_q9.webp`) que muestra ambos casos en paralelo + 2
toolbutton radios en grid 50/50 alineados con las columnas del video.
Seleccionar 'Q4' = elegir la columna izquierda gris de lo que el alumno
esta viendo; seleccionar 'Q9' = la columna derecha naranja.

Tres toques creativos aprovechando que el video tiene identidad
cromatica por columna (Q4=gris, Q9=naranja):
  1. Cada chip se colorea con la paleta de su columna del video:
     - Q4: bootstyle `secondary-toolbutton` (gris)
     - Q9: bootstyle `warning-toolbutton` (naranja PHASE_PROC_COLOR)
     → color-continuity: el alumno asocia "chip gris abajo ↔ columna
     gris arriba" sin esfuerzo.
  2. Cada chip incluye un mini-icono PIL del layout de nodos del
     elemento: 4 puntos en 2x2 para Q4, 9 puntos en 3x3 para Q9.
     Es una previsualizacion visual del concepto que el chip representa.
  3. El texto de cada chip incluye el conteo de GDL (informacion clave
     para decidir costo/precision): "Q4 · 8 GDL", "Q9 · 18 GDL".

Una linea de hint operativa preservada del diseño anterior: en Q9 los
5 nodos internos se generan automaticamente. Es info no obvia que
previene confusion cuando el alumno ve nodos aparecer al cambiar de
tipo, asi que sobrevive como italic muted de una linea.

Q9 -> Q4 dispara modal de confirmacion porque descarta nodos medios y
centroide sin datos (los con cargas/BCs se preservan como huerfanos).
"""

import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from PIL import Image, ImageDraw, ImageTk

from config.settings import (
    ELEMENT_Q4, ELEMENT_Q9,
    LABEL_BG, TEXT_MUTED_FG, ORPHAN_NODE_FG,
    PHASE_PROC_COLOR,
)
from education.components.plot_panel import _theme_colors
from gui.widgets.webp_player import WebpPlayer
from models.mesh_utils import expand_q4_to_q9, shrink_q9_to_q4


VIDEO_PATH = os.path.join("resources", "videos", "cantilever_q4_q9.webp")

# Misma anchura y video que AnalysisTypeDialog. La altura es 60 px
# mayor (720 vs 660) porque ElementTypeDialog tiene UN renglon de hint
# adicional ("En Q9 los 5 nodos internos se generan automaticamente")
# que AnalysisTypeDialog no tiene. Con 660 los botones del footer
# quedaban clipeados fuera del area visible del Toplevel.
VIDEO_W, VIDEO_H = 720, 480
DIALOG_W, DIALOG_H = 760, 720

# Color de cada chip pickea la identidad cromatica de su columna del
# video (Q4=gris, Q9=naranja). Si en el futuro el video cambia su
# paleta, actualizar aqui.
_Q4_DOT_COLOR = "#cdd2d8"   # gris claro (matches Q4 column header)
_Q9_DOT_COLOR = PHASE_PROC_COLOR  # naranja (matches Q9 column header)


class ElementTypeDialog:
    """Ventana modal para configurar Tipo de Elemento (Q4 / Q9)."""

    def __init__(self, parent, project, main_window=None):
        self.project = project
        self.main_window = main_window
        self.parent = parent
        self._video = None
        # Refs anti-GC para los iconos PIL embebidos en los chips
        self._icon_q4: ImageTk.PhotoImage | None = None
        self._icon_q9: ImageTk.PhotoImage | None = None

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("🔲  Tipo de Elemento")
        self.dialog.geometry(f"{DIALOG_W}x{DIALOG_H}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self.element_var = tk.StringVar(value=project.element_type)

        self._build()
        # Diferir carga del video para que el container tenga tamaño
        # real antes del primer render (si no, escala a 1×1 px).
        self.dialog.after(120, self._load_video)
        self._center()

    # ─── Layout ─────────────────────────────────────────────────────────
    def _build(self):
        main = ttk.Frame(self.dialog, padding=18)
        main.pack(fill=BOTH, expand=YES)

        self._build_video(main)
        self._build_selector(main)
        self._build_hint(main)
        self._build_footer(main)

    def _build_video(self, parent):
        """Container fijo 720x480 con el WebpPlayer adentro.
        `pack_propagate(False)` evita que el frame se ajuste al contenido."""
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
        """Dos toolbutton radios en grid 50/50, alineados con las
        columnas Q4|Q9 del video. Cada chip color-matches su columna:
        Q4 gris, Q9 naranja. Mini-icono con layout de nodos a la
        izquierda del texto."""
        # Generar iconos PIL antes de los chips (32px cuadrado → suficiente
        # para ver 2x2 vs 3x3 sin saturar el chip).
        self._icon_q4 = self._make_node_icon(grid=2, color=_Q4_DOT_COLOR)
        self._icon_q9 = self._make_node_icon(grid=3, color=_Q9_DOT_COLOR)

        sel = ttk.Frame(parent)
        sel.pack(fill=X, pady=(0, 6))
        sel.columnconfigure(0, weight=1, uniform="case")
        sel.columnconfigure(1, weight=1, uniform="case")

        ttk.Radiobutton(
            sel, text="  Q4 — Bilineal  ·  8 GDL",
            image=self._icon_q4, compound=LEFT,
            variable=self.element_var, value=ELEMENT_Q4,
            bootstyle="secondary-toolbutton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6), ipady=10)

        ttk.Radiobutton(
            sel, text="  Q9 — Bicuadrático  ·  18 GDL",
            image=self._icon_q9, compound=LEFT,
            variable=self.element_var, value=ELEMENT_Q9,
            bootstyle="warning-toolbutton",
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0), ipady=10)

    def _make_node_icon(self, grid: int, color: str,
                        size: int = 32) -> ImageTk.PhotoImage:
        """Genera un mini-icono RGBA con un cuadrado outline y `grid×grid`
        puntos en una grilla regular. Para Q4 grid=2 (4 corners), para
        Q9 grid=3 (corners + mids + centro). Pedagogicamente: el alumno
        ve el layout de nodos del elemento dentro del propio chip."""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        pad = 5
        inner = size - 2 * pad
        # Outline del elemento (cuadrado fino con el color del chip)
        draw.rectangle(
            [pad, pad, pad + inner, pad + inner],
            outline=color, width=1,
        )
        # Puntos en la grilla
        dot_r = max(2, size // 14)
        step = inner / (grid - 1) if grid > 1 else 0
        for i in range(grid):
            for j in range(grid):
                cx = pad + int(round(j * step))
                cy = pad + int(round(i * step))
                draw.ellipse(
                    [cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
                    fill=color,
                )
        return ImageTk.PhotoImage(img)

    def _build_hint(self, parent):
        """Hint operacional Q9 preservado: una sola linea italic muted
        que previene confusion cuando el alumno ve nodos aparecer al
        cambiar tipo. (AnalysisTypeDialog NO tiene equivalente porque
        TP/DP no tiene una sutileza operacional analoga.)"""
        ttk.Label(
            parent,
            text=("En Q9, los 5 nodos internos (medios + centroide) "
                  "se generan automáticamente."),
            font=("Segoe UI", 9, "italic"),
            foreground=TEXT_MUTED_FG,
            wraplength=700, justify=LEFT, anchor="w",
        ).pack(fill=X, pady=(0, 14))

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
        if not os.path.exists(VIDEO_PATH):
            self._show_missing_video()
            return
        try:
            self._video.load(VIDEO_PATH)
            self.dialog.after(80, self._video.play)
        except Exception as exc:
            self._show_missing_video(exc=exc)

    def _show_missing_video(self, exc=None):
        for w in self.video_frame.winfo_children():
            w.destroy()
        self._video = None
        msg = (f"Video no disponible.\n\n"
               f"Esperado en: {VIDEO_PATH}")
        if exc:
            msg += f"\n\nError: {exc}"
        tk.Label(
            self.video_frame, text=msg,
            bg=LABEL_BG, fg=ORPHAN_NODE_FG,
            font=("Segoe UI", 9), justify=CENTER,
        ).pack(expand=YES, padx=20, pady=20)

    # ─── Limpieza del video ─────────────────────────────────────────────
    def _stop_video(self):
        if self._video is not None:
            try:
                self._video.stop()
            except Exception:
                pass

    # ─── Aceptar / Cancelar ────────────────────────────────────────────
    def _on_accept(self):
        new_et = self.element_var.get()
        if new_et == self.project.element_type:
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
        sw = self.dialog.winfo_screenwidth()
        sh = self.dialog.winfo_screenheight()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h - 50))
        self.dialog.geometry(f"+{x}+{y}")
