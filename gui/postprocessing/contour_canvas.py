"""
ContourCanvas: Canvas de matplotlib embebido en tkinter para visualización
de contornos de resultados FEM (esfuerzos, desplazamientos, Von Mises).

Usa FigureCanvasTkAgg para integrar figuras matplotlib directamente
en el panel de Post-Proceso.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.tri import Triangulation
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


class ContourCanvas(ttk.Frame):
    """Canvas de matplotlib embebido para visualización de contornos FEM."""

    def __init__(self, parent, project, main_window):
        super().__init__(parent)
        self.project = project
        self.main_window = main_window

        # Estado de resultados
        self.result_values = None   # {node_id: float}
        self.result_label = ""
        self.displacements = None
        self.show_deformed = False
        self.deform_scale = 1.0

        # Opciones de visualización
        self.show_mesh_edges = True
        self.show_node_labels = False
        self.show_elem_labels = False
        self.show_isolines = True
        self.num_levels = 12
        self.cmap_name = "jet"

        self._build_ui()

    def _build_ui(self):
        """Construye el canvas matplotlib con toolbar."""
        # ─── Toolbar superior ────────────────────────────────────────────
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(fill=X, padx=2, pady=(2, 0))

        ttk.Label(
            toolbar_frame, text="  Contornos FEM",
            font=("Segoe UI", 10, "bold")
        ).pack(side=LEFT, padx=3)

        # Selector de colormap
        ttk.Label(toolbar_frame, text="Mapa:", font=("Segoe UI", 8)).pack(side=RIGHT, padx=(0, 2))
        self.cmap_var = tk.StringVar(value="jet")
        cmap_combo = ttk.Combobox(
            toolbar_frame, textvariable=self.cmap_var,
            values=["jet", "viridis", "plasma", "magma", "inferno",
                    "coolwarm", "RdYlBu_r", "Spectral_r", "turbo",
                    "hot", "rainbow"],
            state="readonly", width=10
        )
        cmap_combo.pack(side=RIGHT, padx=2)
        cmap_combo.bind("<<ComboboxSelected>>", lambda e: self._on_cmap_changed())

        # Checkbox isolíneas
        self.isolines_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar_frame, text="Isolíneas", variable=self.isolines_var,
            bootstyle="round-toggle",
            command=self._on_options_changed
        ).pack(side=RIGHT, padx=5)

        # Checkbox bordes de malla
        self.mesh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar_frame, text="Malla", variable=self.mesh_var,
            bootstyle="round-toggle",
            command=self._on_options_changed
        ).pack(side=RIGHT, padx=5)

        # Checkbox etiquetas nodos
        self.labels_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            toolbar_frame, text="IDs Nodos", variable=self.labels_var,
            bootstyle="round-toggle",
            command=self._on_options_changed
        ).pack(side=RIGHT, padx=5)

        # Niveles
        ttk.Label(toolbar_frame, text="Niveles:", font=("Segoe UI", 8)).pack(side=RIGHT, padx=(5, 2))
        self.levels_var = tk.IntVar(value=12)
        levels_spin = ttk.Spinbox(
            toolbar_frame, from_=4, to=30, textvariable=self.levels_var,
            width=4, command=self._on_options_changed
        )
        levels_spin.pack(side=RIGHT, padx=2)

        # ─── Figura matplotlib ───────────────────────────────────────────
        self.fig = Figure(figsize=(8, 6), facecolor='#1e1e2e', dpi=100)
        self.ax = self.fig.add_subplot(111)
        self._style_axes()

        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget.get_tk_widget().pack(fill=BOTH, expand=YES, padx=2, pady=2)

        # ─── Toolbar de matplotlib ───────────────────────────────────────
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=X, padx=2)
        self.nav_toolbar = NavigationToolbar2Tk(self.canvas_widget, nav_frame)
        self.nav_toolbar.update()

        # Texto inicial
        self._draw_empty_message()

    def _style_axes(self):
        """Aplica estilo oscuro a los ejes."""
        self.ax.set_facecolor('#1e1e2e')
        self.ax.tick_params(colors='#aaa', labelsize=8)
        self.ax.xaxis.label.set_color('#aaa')
        self.ax.yaxis.label.set_color('#aaa')
        for spine in self.ax.spines.values():
            spine.set_color('#555')
        self.ax.set_aspect('equal', adjustable='box')

    def _draw_empty_message(self):
        """Dibuja mensaje cuando no hay resultados."""
        self.ax.clear()
        self._style_axes()
        self.ax.text(
            0.5, 0.5,
            "Sin resultados\n\nResuelva el modelo en Post-Proceso\npara visualizar contornos.",
            transform=self.ax.transAxes,
            ha='center', va='center', fontsize=14,
            color='#666', fontfamily='Segoe UI',
            style='italic'
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas_widget.draw_idle()

    # ═════════════════════════════════════════════════════════════════════
    # MÉTODOS PÚBLICOS
    # ═════════════════════════════════════════════════════════════════════

    def set_result_values(self, values, label="Resultado"):
        """Activa la visualización del contorno con los valores nodales.

        Parámetros:
            values: dict {node_id: float} con valores en cada nodo.
            label: etiqueta para la barra de colores.
        """
        self.result_values = values
        self.result_label = label
        self.draw_contour()

    def set_deformed(self, displacements, scale=1.0):
        """Activa la visualización de la malla deformada.

        Parámetros:
            displacements: numpy array con desplazamientos u.
            scale: factor de escala para la deformación.
        """
        self.displacements = displacements
        self.deform_scale = scale
        self.show_deformed = True
        if self.result_values:
            self.draw_contour()

    def clear_results(self):
        """Limpia la visualización."""
        self.result_values = None
        self.result_label = ""
        self.show_deformed = False
        self.displacements = None
        self._draw_empty_message()

    # ═════════════════════════════════════════════════════════════════════
    # DIBUJO DE CONTORNOS
    # ═════════════════════════════════════════════════════════════════════

    def draw_contour(self):
        """Dibuja el contorno de resultados con triangulación."""
        if not self.result_values or not self.project.nodes or not self.project.elements:
            self._draw_empty_message()
            return

        self.ax.clear()
        self._style_axes()

        # Leer opciones
        self.show_mesh_edges = self.mesh_var.get()
        self.show_node_labels = self.labels_var.get()
        self.show_isolines = self.isolines_var.get()
        self.num_levels = self.levels_var.get()
        self.cmap_name = self.cmap_var.get()

        # ─── Preparar coordenadas ────────────────────────────────────────
        sorted_nids = sorted(self.project.nodes.keys())
        nid_to_idx = {nid: i for i, nid in enumerate(sorted_nids)}

        xs = []
        ys = []
        for nid in sorted_nids:
            node = self.project.nodes[nid]
            x, y = node.x, node.y

            # Aplicar deformada si está activa
            if self.show_deformed and self.displacements is not None:
                idx = 2 * (nid - 1)
                if idx + 1 < len(self.displacements):
                    # Calcular escala automática
                    max_disp = np.max(np.abs(self.displacements))
                    if max_disp > 0:
                        coords_arr = np.array(
                            [[self.project.nodes[n].x, self.project.nodes[n].y]
                             for n in sorted_nids]
                        )
                        model_size = max(
                            coords_arr[:, 0].max() - coords_arr[:, 0].min(),
                            coords_arr[:, 1].max() - coords_arr[:, 1].min()
                        )
                        auto_scale = model_size * 0.1 / max_disp * self.deform_scale
                    else:
                        auto_scale = 0
                    x += auto_scale * self.displacements[idx]
                    y += auto_scale * self.displacements[idx + 1]

            xs.append(x)
            ys.append(y)

        xs = np.array(xs)
        ys = np.array(ys)

        # Valores de resultado para cada nodo
        vals = np.array([self.result_values.get(nid, 0.0) for nid in sorted_nids])

        # ─── Triangulación a partir de los elementos ─────────────────────
        triangles = []
        for elem in self.project.elements.values():
            nids = elem.node_ids[:4]  # Para Q4
            valid = all(nid in nid_to_idx for nid in nids)
            if not valid:
                continue

            # Dividir cuadrilátero en 2 triángulos
            i0, i1, i2, i3 = [nid_to_idx[nid] for nid in nids]
            triangles.append([i0, i1, i2])
            triangles.append([i0, i2, i3])

        if not triangles:
            self._draw_empty_message()
            return

        triangles = np.array(triangles)
        triang = Triangulation(xs, ys, triangles)

        # ─── Dibujar contorno relleno ────────────────────────────────────
        vmin = vals.min()
        vmax = vals.max()
        if vmin == vmax:
            vmax = vmin + 1.0

        levels = np.linspace(vmin, vmax, self.num_levels + 1)
        cmap = plt.get_cmap(self.cmap_name)

        # Contorno relleno
        tcf = self.ax.tricontourf(
            triang, vals, levels=levels, cmap=cmap, extend='both'
        )

        # Isolíneas
        if self.show_isolines:
            tc = self.ax.tricontour(
                triang, vals, levels=levels, colors='black',
                linewidths=0.3, alpha=0.6
            )

        # ─── Bordes de la malla ──────────────────────────────────────────
        if self.show_mesh_edges:
            for elem in self.project.elements.values():
                nids = elem.node_ids[:4]
                valid = all(nid in nid_to_idx for nid in nids)
                if not valid:
                    continue

                # Dibujar bordes del cuadrilátero
                edge_xs = [xs[nid_to_idx[n]] for n in nids] + [xs[nid_to_idx[nids[0]]]]
                edge_ys = [ys[nid_to_idx[n]] for n in nids] + [ys[nid_to_idx[nids[0]]]]
                self.ax.plot(edge_xs, edge_ys, 'k-', linewidth=0.8, alpha=0.7)

        # ─── Malla original transparente (si deformada) ──────────────────
        if self.show_deformed and self.displacements is not None:
            for elem in self.project.elements.values():
                nids = elem.node_ids[:4]
                valid = all(nid in self.project.nodes for nid in nids)
                if not valid:
                    continue
                orig_xs = [self.project.nodes[n].x for n in nids] + [self.project.nodes[nids[0]].x]
                orig_ys = [self.project.nodes[n].y for n in nids] + [self.project.nodes[nids[0]].y]
                self.ax.plot(orig_xs, orig_ys, '--', color='#666', linewidth=0.5, alpha=0.5)

        # ─── Nodos ───────────────────────────────────────────────────────
        self.ax.scatter(xs, ys, c='white', s=8, zorder=5, edgecolors='black', linewidths=0.5)

        if self.show_node_labels:
            for i, nid in enumerate(sorted_nids):
                self.ax.annotate(
                    str(nid), (xs[i], ys[i]),
                    textcoords="offset points", xytext=(5, 5),
                    fontsize=7, color='white', fontweight='bold'
                )

        # ─── Cargas y restricciones ──────────────────────────────────────
        self._draw_loads_on_axes(xs, ys, sorted_nids, nid_to_idx)
        self._draw_constraints_on_axes(xs, ys, sorted_nids, nid_to_idx)

        # ─── Barra de colores ────────────────────────────────────────────
        # Eliminar colorbar anterior si existe
        if hasattr(self, '_colorbar') and self._colorbar is not None:
            try:
                self._colorbar.remove()
            except Exception:
                pass

        self._colorbar = self.fig.colorbar(
            tcf, ax=self.ax, shrink=0.85, pad=0.02, aspect=25
        )
        self._colorbar.ax.tick_params(labelsize=7, colors='#aaa')
        self._colorbar.set_label(
            self.result_label, fontsize=9, color='#ddd', fontweight='bold'
        )
        self._colorbar.outline.set_edgecolor('#555')

        # ─── Títulos y ejes ──────────────────────────────────────────────
        title = self.result_label
        if self.show_deformed:
            title += f"  (deformada ×{self.deform_scale:.1f})"

        self.ax.set_title(
            title, fontsize=11, color='#eee',
            fontweight='bold', pad=10
        )
        self.ax.set_xlabel("X", fontsize=9)
        self.ax.set_ylabel("Y", fontsize=9)

        # Margen
        x_margin = (xs.max() - xs.min()) * 0.08 + 0.5
        y_margin = (ys.max() - ys.min()) * 0.08 + 0.5
        self.ax.set_xlim(xs.min() - x_margin, xs.max() + x_margin)
        self.ax.set_ylim(ys.min() - y_margin, ys.max() + y_margin)

        self.fig.tight_layout()
        self.canvas_widget.draw_idle()

    def _draw_loads_on_axes(self, xs, ys, sorted_nids, nid_to_idx):
        """Dibuja flechas de cargas en los ejes matplotlib."""
        model_size = max(xs.max() - xs.min(), ys.max() - ys.min())
        arrow_len = model_size * 0.12

        for load in self.project.nodal_loads.values():
            if load.node_id not in nid_to_idx:
                continue
            idx = nid_to_idx[load.node_id]
            x, y = xs[idx], ys[idx]

            if abs(load.fx) > 1e-10:
                d = 1 if load.fx > 0 else -1
                self.ax.annotate(
                    '', xy=(x, y),
                    xytext=(x - d * arrow_len, y),
                    arrowprops=dict(
                        arrowstyle='->', lw=2, color='#ef5350',
                        mutation_scale=15
                    )
                )
                self.ax.text(
                    x - d * arrow_len * 0.5, y + arrow_len * 0.15,
                    f"Fx={load.fx:.0f}", fontsize=6, color='#ef5350',
                    ha='center', fontweight='bold'
                )

            if abs(load.fy) > 1e-10:
                d = 1 if load.fy > 0 else -1
                self.ax.annotate(
                    '', xy=(x, y),
                    xytext=(x, y - d * arrow_len),
                    arrowprops=dict(
                        arrowstyle='->', lw=2, color='#ef5350',
                        mutation_scale=15
                    )
                )
                self.ax.text(
                    x + arrow_len * 0.15, y - d * arrow_len * 0.5,
                    f"Fy={load.fy:.0f}", fontsize=6, color='#ef5350',
                    fontweight='bold'
                )

    def _draw_constraints_on_axes(self, xs, ys, sorted_nids, nid_to_idx):
        """Dibuja símbolos de restricción en los ejes matplotlib."""
        import matplotlib.patches as patches

        model_size = max(xs.max() - xs.min(), ys.max() - ys.min())
        tri_size = model_size * 0.04

        for bc in self.project.boundary_conditions.values():
            if bc.node_id not in nid_to_idx:
                continue
            idx = nid_to_idx[bc.node_id]
            x, y = xs[idx], ys[idx]

            if bc.restrain_x and bc.restrain_y:
                # Empotramiento: triángulo + líneas
                tri = plt.Polygon(
                    [[x, y - tri_size],
                     [x - tri_size, y - tri_size * 2],
                     [x + tri_size, y - tri_size * 2]],
                    fill=False, edgecolor='#ffa726', linewidth=1.5, zorder=6
                )
                self.ax.add_patch(tri)
                # Líneas de tierra
                for i in range(4):
                    lx = x - tri_size + i * tri_size * 2 / 3
                    self.ax.plot(
                        [lx, lx - tri_size * 0.4],
                        [y - tri_size * 2, y - tri_size * 2.4],
                        color='#ffa726', linewidth=1, zorder=6
                    )
            elif bc.restrain_x:
                # Rodillo horizontal
                tri = plt.Polygon(
                    [[x - tri_size, y],
                     [x - tri_size * 2, y - tri_size],
                     [x - tri_size * 2, y + tri_size]],
                    fill=False, edgecolor='#ffa726', linewidth=1.5, zorder=6
                )
                self.ax.add_patch(tri)
            elif bc.restrain_y:
                # Rodillo vertical
                tri = plt.Polygon(
                    [[x, y - tri_size],
                     [x - tri_size, y - tri_size * 2],
                     [x + tri_size, y - tri_size * 2]],
                    fill=False, edgecolor='#ffa726', linewidth=1.5, zorder=6
                )
                self.ax.add_patch(tri)
                circle = plt.Circle(
                    (x, y - tri_size * 2.3), tri_size * 0.3,
                    fill=False, edgecolor='#ffa726', linewidth=1, zorder=6
                )
                self.ax.add_patch(circle)

    # ═════════════════════════════════════════════════════════════════════
    # CALLBACKS
    # ═════════════════════════════════════════════════════════════════════

    def _on_cmap_changed(self):
        """Cambia el mapa de colores y redibuja."""
        if self.result_values:
            self.draw_contour()

    def _on_options_changed(self):
        """Redibuja cuando cambian las opciones."""
        if self.result_values:
            self.draw_contour()
