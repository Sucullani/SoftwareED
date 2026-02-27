"""
BaseEducationalModule: Ventana base para módulos educativos.
Todas las ventanas educativas heredan de esta clase.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import numpy as np

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class BaseEducationalModule:
    """Ventana base para módulos educativos con layout estandarizado."""

    def __init__(self, parent, project, element_id, title, width=1100, height=750):
        self.project = project
        self.element_id = element_id
        self.element = project.elements.get(element_id)

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title(f"Módulo Educativo: {title}")
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.transient(parent)

        # Layout principal: PanedWindow Horizontal
        self.paned = ttk.Panedwindow(self.dialog, orient=HORIZONTAL)
        self.paned.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # Panel izquierdo: Explicación y fórmulas
        self.left_frame = ttk.Frame(self.paned, width=450)
        self.paned.add(self.left_frame, weight=2)

        # Panel derecho: Gráfica/visualización
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame, weight=3)

        # Scroll en panel izquierdo
        self.left_canvas = tk.Canvas(self.left_frame, highlightthickness=0)
        self.left_scrollbar = ttk.Scrollbar(
            self.left_frame, orient=VERTICAL, command=self.left_canvas.yview
        )
        self.scroll_frame = ttk.Frame(self.left_canvas)
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        )
        self.left_canvas.create_window((0, 0), window=self.scroll_frame, anchor=NW)
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        self.left_scrollbar.pack(side=RIGHT, fill=Y)
        self.left_canvas.pack(side=LEFT, fill=BOTH, expand=YES)

        # Scroll con rueda del mouse
        self.left_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.left_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )

        # Coordenadas del elemento
        if self.element:
            self.node_coords = np.array([
                [project.nodes[nid].x, project.nodes[nid].y]
                for nid in self.element.node_ids
            ])
        else:
            self.node_coords = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])

    # ─── Helpers para agregar contenido educativo ──────────────────────

    def add_title(self, text, icon=""):
        """Agrega un título con icono al panel izquierdo."""
        ttk.Label(
            self.scroll_frame,
            text=f"{icon} {text}",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor=W, padx=10, pady=(15, 5))

    def add_subtitle(self, text):
        """Agrega un subtítulo."""
        ttk.Label(
            self.scroll_frame,
            text=text,
            font=("Segoe UI", 10, "bold"),
            foreground="#4fc3f7",
        ).pack(anchor=W, padx=10, pady=(10, 3))

    def add_text(self, text):
        """Agrega texto explicativo."""
        label = ttk.Label(
            self.scroll_frame,
            text=text,
            font=("Segoe UI", 9),
            wraplength=400,
            justify=LEFT,
        )
        label.pack(anchor=W, padx=15, pady=2)

    def add_formula(self, text):
        """Agrega una fórmula o ecuación."""
        frame = ttk.Frame(self.scroll_frame)
        frame.pack(fill=X, padx=15, pady=5)

        ttk.Label(
            frame,
            text=text,
            font=("Consolas", 10),
            foreground="#81c784",
            justify=LEFT,
        ).pack(anchor=W)

    def add_matrix_display(self, matrix, name="", fmt=".4f"):
        """Muestra una matriz NumPy con formato legible."""
        frame = ttk.Frame(self.scroll_frame)
        frame.pack(fill=X, padx=15, pady=5)

        if name:
            ttk.Label(
                frame, text=f"{name} =",
                font=("Consolas", 10, "bold"),
                foreground="#ffa726",
            ).pack(anchor=W)

        if isinstance(matrix, np.ndarray):
            rows, cols = matrix.shape if matrix.ndim == 2 else (1, matrix.shape[0])
            mat_2d = matrix.reshape(rows, cols)

            text_lines = []
            for row in mat_2d:
                line = "  ".join(f"{v:{fmt}}" for v in row)
                text_lines.append(f"  [{line}]")

            mat_text = "\n".join(text_lines)
        else:
            mat_text = str(matrix)

        ttk.Label(
            frame,
            text=mat_text,
            font=("Consolas", 8),
            justify=LEFT,
        ).pack(anchor=W)

    def add_separator(self):
        """Agrega un separador horizontal."""
        ttk.Separator(self.scroll_frame).pack(fill=X, padx=10, pady=10)

    def add_value(self, label, value, fmt=".6f"):
        """Muestra un valor individual con etiqueta."""
        frame = ttk.Frame(self.scroll_frame)
        frame.pack(fill=X, padx=15, pady=2)
        ttk.Label(
            frame, text=f"{label}: ",
            font=("Segoe UI", 9, "bold"),
        ).pack(side=LEFT)
        ttk.Label(
            frame,
            text=f"{value:{fmt}}" if isinstance(value, float) else str(value),
            font=("Consolas", 10),
            foreground="#ef5350",
        ).pack(side=LEFT)

    def create_figure(self, figsize=(6, 5)):
        """Crea una figura matplotlib embebida en el panel derecho."""
        if not HAS_MATPLOTLIB:
            ttk.Label(
                self.right_frame,
                text="matplotlib no disponible",
                font=("Segoe UI", 12),
            ).pack(expand=YES)
            return None, None

        fig = Figure(figsize=figsize, dpi=100, facecolor="#1e1e2e")
        canvas = FigureCanvasTkAgg(fig, master=self.right_frame)
        canvas.get_tk_widget().pack(fill=BOTH, expand=YES, padx=5, pady=5)
        return fig, canvas

    def style_axis(self, ax, title=""):
        """Aplica estilo oscuro a un eje matplotlib."""
        ax.set_facecolor("#1e1e2e")
        if title:
            ax.set_title(title, color="white", fontsize=11, fontweight="bold")
        ax.tick_params(colors="white", labelsize=8)
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        for spine in ax.spines.values():
            spine.set_color("#555")
