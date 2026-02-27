"""
MeshCanvas: Canvas interactivo compartido para visualizar la malla FEM.
Soporta zoom, pan, nodos, elementos, cargas, restricciones,
y visualizacion de resultados con mapa de colores (jet).
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import numpy as np

from config.settings import (
    CANVAS_BG_COLOR, CANVAS_GRID_COLOR, CANVAS_NODE_COLOR,
    CANVAS_ELEMENT_COLOR, CANVAS_LOAD_COLOR, CANVAS_CONSTRAINT_COLOR,
    CANVAS_SELECTED_COLOR, CANVAS_NODE_RADIUS, CANVAS_FONT_SIZE
)


class MeshCanvas(ttk.Frame):
    """Canvas interactivo compartido para la malla FEM con resultados."""

    def __init__(self, parent, project, main_window):
        super().__init__(parent)
        self.project = project
        self.main_window = main_window

        # Estado de vista
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.highlighted_node = None
        self.highlighted_element = None

        # Estado de resultados
        self.result_values = None   # {node_id: float}
        self.result_label = ""
        self.result_vmin = 0.0
        self.result_vmax = 1.0

        # Deformada
        self.show_deformed = False
        self.deform_scale = 0.0
        self.displacements = None

        # Opciones de dibujo
        self.show_node_labels = True
        self.show_elem_labels = True
        self.show_loads = True
        self.show_constraints = True
        self.show_mesh_edges = True

        # ─── Toolbar ────────────────────────────────────────────────────
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, padx=2, pady=(2, 0))

        ttk.Label(
            toolbar, text="  Modelo FEM",
            font=("Segoe UI", 10, "bold")
        ).pack(side=LEFT, padx=3)

        ttk.Button(
            toolbar, text="Ajustar Vista", bootstyle="secondary-outline",
            command=self.fit_view, width=13
        ).pack(side=RIGHT, padx=2)

        ttk.Button(
            toolbar, text="Limpiar Resultados", bootstyle="warning-outline",
            command=self.clear_results, width=16
        ).pack(side=RIGHT, padx=2)

        # Coordenadas del mouse
        self.coord_label = ttk.Label(
            toolbar, text="x: --  y: --",
            font=("Consolas", 8), foreground="#888"
        )
        self.coord_label.pack(side=RIGHT, padx=10)

        # ─── Canvas ─────────────────────────────────────────────────────
        self.canvas = tk.Canvas(
            self, bg=CANVAS_BG_COLOR, highlightthickness=0
        )
        self.canvas.pack(fill=BOTH, expand=YES, padx=2, pady=2)

        # ─── Eventos ────────────────────────────────────────────────────
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_move)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self._on_click)

        self._pan_start_x = 0
        self._pan_start_y = 0

    # ═════════════════════════════════════════════════════════════════════
    # COLORES JET
    # ═════════════════════════════════════════════════════════════════════

    def _jet_color(self, t):
        """Jet colormap: 0=azul, 0.25=cian, 0.5=verde, 0.75=amarillo, 1=rojo."""
        t = max(0.0, min(1.0, t))
        if t < 0.25:
            r, g, b = 0, t / 0.25, 1.0
        elif t < 0.5:
            r, g, b = 0, 1.0, 1.0 - (t - 0.25) / 0.25
        elif t < 0.75:
            r, g, b = (t - 0.5) / 0.25, 1.0, 0
        else:
            r, g, b = 1.0, 1.0 - (t - 0.75) / 0.25, 0
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def _value_to_color(self, value):
        """Convierte un valor al color jet basado en vmin/vmax."""
        if self.result_vmax == self.result_vmin:
            t = 0.5
        else:
            t = (value - self.result_vmin) / (self.result_vmax - self.result_vmin)
        return self._jet_color(t)

    # ═════════════════════════════════════════════════════════════════════
    # TRANSFORMACION DE COORDENADAS
    # ═════════════════════════════════════════════════════════════════════

    def world_to_screen(self, x, y):
        """Coordenadas del mundo -> pantalla."""
        sx = x * self.scale + self.offset_x
        sy = -y * self.scale + self.offset_y
        return sx, sy

    def screen_to_world(self, sx, sy):
        """Coordenadas de pantalla -> mundo."""
        x = (sx - self.offset_x) / self.scale
        y = -(sy - self.offset_y) / self.scale
        return x, y

    def _get_node_screen_pos(self, nid):
        """Retorna posicion de pantalla de un nodo (con deformada si activa)."""
        node = self.project.nodes.get(nid)
        if node is None:
            return 0, 0
        x, y = node.x, node.y
        if self.show_deformed and self.displacements is not None:
            idx = 2 * (nid - 1)
            if idx + 1 < len(self.displacements):
                x += self.deform_scale * self.displacements[idx]
                y += self.deform_scale * self.displacements[idx + 1]
        return self.world_to_screen(x, y)

    # ═════════════════════════════════════════════════════════════════════
    # DIBUJO
    # ═════════════════════════════════════════════════════════════════════

    def redraw(self):
        """Redibuja toda la malla."""
        self.canvas.delete("all")
        self._draw_grid()

        # Si deformada, dibujar malla original transparente
        if self.show_deformed and self.displacements is not None:
            self._draw_original_mesh_ghost()

        self._draw_elements()
        self._draw_nodes()

        if self.show_loads:
            self._draw_loads()
        if self.show_constraints:
            self._draw_constraints()

        self._draw_highlight()

        if self.result_values:
            self._draw_colorbar()

        # Ejes de referencia
        self._draw_axes()

    def _draw_grid(self):
        """Grilla de fondo sutil."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        spacing = max(30, int(50 * self.scale))
        if spacing > 200:
            spacing = 200

        for i in range(-20, 60):
            sx = i * spacing + (self.offset_x % spacing)
            if 0 <= sx <= w:
                self.canvas.create_line(
                    sx, 0, sx, h, fill=CANVAS_GRID_COLOR, width=1, dash=(2, 6)
                )
        for i in range(-20, 60):
            sy = i * spacing + (self.offset_y % spacing)
            if 0 <= sy <= h:
                self.canvas.create_line(
                    0, sy, w, sy, fill=CANVAS_GRID_COLOR, width=1, dash=(2, 6)
                )

    def _draw_axes(self):
        """Dibuja ejes X,Y en la esquina inferior izquierda."""
        margin = 40
        length = 35
        bx, by = margin, self.canvas.winfo_height() - margin

        # Eje X
        self.canvas.create_line(
            bx, by, bx + length, by, fill="#ef5350", width=2, arrow=tk.LAST
        )
        self.canvas.create_text(
            bx + length + 8, by, text="X", fill="#ef5350",
            font=("Segoe UI", 9, "bold"), anchor=W
        )
        # Eje Y
        self.canvas.create_line(
            bx, by, bx, by - length, fill="#4fc3f7", width=2, arrow=tk.LAST
        )
        self.canvas.create_text(
            bx, by - length - 8, text="Y", fill="#4fc3f7",
            font=("Segoe UI", 9, "bold"), anchor=S
        )

    def _draw_original_mesh_ghost(self):
        """Dibuja la malla original como lineas punteadas (cuando se muestra deformada)."""
        for elem in self.project.elements.values():
            coords = []
            valid = True
            for nid in elem.node_ids[:4]:
                node = self.project.nodes.get(nid)
                if node is None:
                    valid = False
                    break
                sx, sy = self.world_to_screen(node.x, node.y)
                coords.extend([sx, sy])
            if not valid or len(coords) < 8:
                continue
            coords.extend(coords[:2])  # cerrar
            self.canvas.create_line(
                *coords, fill="#444466", width=1, dash=(3, 5)
            )

    def _draw_elements(self):
        """Dibuja los elementos de la malla con colores si hay resultados."""
        for elem in self.project.elements.values():
            coords = []
            valid = True
            elem_values = []
            for nid in elem.node_ids[:4]:
                if nid not in self.project.nodes:
                    valid = False
                    break
                sx, sy = self._get_node_screen_pos(nid)
                coords.extend([sx, sy])
                if self.result_values and nid in self.result_values:
                    elem_values.append(self.result_values[nid])

            if not valid or len(coords) < 8:
                continue

            # Color del elemento
            fill_color = ""
            if self.result_values and elem_values:
                avg_val = np.mean(elem_values)
                fill_color = self._value_to_color(avg_val)

            outline_color = CANVAS_ELEMENT_COLOR
            if self.highlighted_element == elem.id:
                outline_color = CANVAS_SELECTED_COLOR

            edge_color = outline_color if self.show_mesh_edges else ""

            self.canvas.create_polygon(
                *coords,
                outline=edge_color,
                fill=fill_color,
                width=2 if self.highlighted_element == elem.id else 1.5,
                stipple="" if fill_color else "",
            )

            # Etiqueta del elemento en el centro
            if self.show_elem_labels:
                cx = sum(coords[::2]) / 4
                cy = sum(coords[1::2]) / 4
                text_color = "#222" if fill_color else "#aaaaaa"
                self.canvas.create_text(
                    cx, cy, text=str(elem.id),
                    fill=text_color,
                    font=("Segoe UI", CANVAS_FONT_SIZE, "bold"),
                    anchor=tk.CENTER
                )

    def _draw_nodes(self):
        """Dibuja los nodos."""
        r = CANVAS_NODE_RADIUS
        for nid, node in self.project.nodes.items():
            sx, sy = self._get_node_screen_pos(nid)
            color = CANVAS_NODE_COLOR
            if self.highlighted_node == nid:
                color = CANVAS_SELECTED_COLOR
                r_draw = r + 3
            else:
                r_draw = r

            self.canvas.create_oval(
                sx - r_draw, sy - r_draw, sx + r_draw, sy + r_draw,
                fill=color, outline=color, width=1
            )

            if self.show_node_labels:
                # Valor de resultado o ID
                if self.result_values and nid in self.result_values:
                    label = f"{nid}: {self.result_values[nid]:.2f}"
                else:
                    label = str(nid)
                self.canvas.create_text(
                    sx + r_draw + 6, sy - r_draw - 4,
                    text=label, fill=CANVAS_NODE_COLOR,
                    font=("Segoe UI", CANVAS_FONT_SIZE - 1),
                    anchor=tk.SW
                )

    def _draw_loads(self):
        """Dibuja flechas para las cargas nodales."""
        arrow_len = 40
        for load in self.project.nodal_loads.values():
            node = self.project.nodes.get(load.node_id)
            if node is None:
                continue
            sx, sy = self._get_node_screen_pos(load.node_id)

            if abs(load.fx) > 1e-10:
                d = 1 if load.fx > 0 else -1
                x_start = sx - d * arrow_len
                self.canvas.create_line(
                    x_start, sy, sx, sy,
                    fill=CANVAS_LOAD_COLOR, width=2, arrow=tk.LAST,
                    arrowshape=(10, 12, 5)
                )
                self.canvas.create_text(
                    x_start, sy - 12, text=f"Fx={load.fx:.0f}",
                    fill=CANVAS_LOAD_COLOR,
                    font=("Segoe UI", CANVAS_FONT_SIZE - 1), anchor=tk.S
                )

            if abs(load.fy) > 1e-10:
                d = -1 if load.fy > 0 else 1
                y_start = sy - d * arrow_len
                self.canvas.create_line(
                    sx, y_start, sx, sy,
                    fill=CANVAS_LOAD_COLOR, width=2, arrow=tk.LAST,
                    arrowshape=(10, 12, 5)
                )
                self.canvas.create_text(
                    sx + 14, y_start, text=f"Fy={load.fy:.0f}",
                    fill=CANVAS_LOAD_COLOR,
                    font=("Segoe UI", CANVAS_FONT_SIZE - 1), anchor=tk.W
                )

    def _draw_constraints(self):
        """Dibuja simbolos de restriccion."""
        size = 12
        for bc in self.project.boundary_conditions.values():
            node = self.project.nodes.get(bc.node_id)
            if node is None:
                continue
            sx, sy = self._get_node_screen_pos(bc.node_id)

            if bc.is_fixed:
                # Triangulo (empotramiento)
                self.canvas.create_polygon(
                    sx, sy + size,
                    sx - size, sy + size * 2,
                    sx + size, sy + size * 2,
                    outline=CANVAS_CONSTRAINT_COLOR, fill="", width=2
                )
                for i in range(4):
                    lx = sx - size + i * size * 2 / 3
                    self.canvas.create_line(
                        lx, sy + size * 2,
                        lx - 5, sy + size * 2.5,
                        fill=CANVAS_CONSTRAINT_COLOR, width=1
                    )
            elif bc.is_roller_x:
                self.canvas.create_polygon(
                    sx - size, sy,
                    sx - size * 2, sy - size,
                    sx - size * 2, sy + size,
                    outline=CANVAS_CONSTRAINT_COLOR, fill="", width=2
                )
            elif bc.is_roller_y:
                self.canvas.create_polygon(
                    sx, sy + size,
                    sx - size, sy + size * 2,
                    sx + size, sy + size * 2,
                    outline=CANVAS_CONSTRAINT_COLOR, fill="", width=2
                )
                self.canvas.create_oval(
                    sx - 4, sy + size * 2, sx + 4, sy + size * 2 + 8,
                    outline=CANVAS_CONSTRAINT_COLOR, fill="", width=1.5
                )

    def _draw_highlight(self):
        """Resaltado del nodo seleccionado."""
        if self.highlighted_node:
            if self.highlighted_node in self.project.nodes:
                sx, sy = self._get_node_screen_pos(self.highlighted_node)
                r = CANVAS_NODE_RADIUS + 8
                self.canvas.create_oval(
                    sx - r, sy - r, sx + r, sy + r,
                    outline=CANVAS_SELECTED_COLOR, fill="", width=2, dash=(4, 2)
                )

    def _draw_colorbar(self):
        """Dibuja barra de colores vertical en el canvas."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return

        bar_w = 20
        bar_h = min(250, h - 80)
        x0 = w - bar_w - 30
        y0 = 40
        n_steps = 50

        for i in range(n_steps):
            t = 1.0 - i / n_steps
            color = self._jet_color(t)
            yy = y0 + i * bar_h / n_steps
            self.canvas.create_rectangle(
                x0, yy, x0 + bar_w, yy + bar_h / n_steps + 1,
                fill=color, outline=""
            )

        # Borde
        self.canvas.create_rectangle(
            x0, y0, x0 + bar_w, y0 + bar_h,
            outline="#aaa", width=1
        )

        # Etiquetas de valores
        n_labels = 5
        for i in range(n_labels + 1):
            t = 1.0 - i / n_labels
            val = self.result_vmin + t * (self.result_vmax - self.result_vmin)
            yy = y0 + i * bar_h / n_labels
            self.canvas.create_text(
                x0 - 5, yy, text=f"{val:.2f}",
                fill="white", font=("Consolas", 7), anchor=tk.E
            )

        # Titulo
        self.canvas.create_text(
            x0 + bar_w / 2, y0 - 12, text=self.result_label,
            fill="white", font=("Segoe UI", 8, "bold"), anchor=tk.S
        )

    # ═════════════════════════════════════════════════════════════════════
    # EVENTOS
    # ═════════════════════════════════════════════════════════════════════

    def _on_mousewheel(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        mx, my = event.x, event.y
        self.offset_x = mx - factor * (mx - self.offset_x)
        self.offset_y = my - factor * (my - self.offset_y)
        self.scale *= factor
        self.redraw()

    def _on_pan_start(self, event):
        self._pan_start_x = event.x
        self._pan_start_y = event.y

    def _on_pan_move(self, event):
        dx = event.x - self._pan_start_x
        dy = event.y - self._pan_start_y
        self.offset_x += dx
        self.offset_y += dy
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self.redraw()

    def _on_resize(self, event):
        self.redraw()

    def _on_mouse_move(self, event):
        """Muestra coordenadas del mundo al mover el mouse."""
        wx, wy = self.screen_to_world(event.x, event.y)
        self.coord_label.config(text=f"x: {wx:.2f}  y: {wy:.2f}")

    def _on_click(self, event):
        """Click izquierdo: seleccionar nodo o elemento mas cercano."""
        wx, wy = self.screen_to_world(event.x, event.y)

        # Buscar nodo mas cercano
        min_dist = float("inf")
        closest_node = None
        for nid, node in self.project.nodes.items():
            dx = node.x - wx
            dy = node.y - wy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_node = nid

        threshold = 15 / self.scale  # umbral en coord mundo
        if closest_node and min_dist < threshold:
            self.highlight_node(closest_node)
            self.main_window.set_status(
                f"Nodo {closest_node} seleccionado "
                f"({self.project.nodes[closest_node].x:.2f}, "
                f"{self.project.nodes[closest_node].y:.2f})"
            )
            return

        # Buscar elemento (punto dentro de poligono)
        for elem in self.project.elements.values():
            nids = elem.node_ids[:4]
            pts = []
            valid = True
            for n in nids:
                if n not in self.project.nodes:
                    valid = False
                    break
                pts.append((self.project.nodes[n].x, self.project.nodes[n].y))
            if not valid:
                continue
            if self._point_in_quad(wx, wy, pts):
                self.highlight_element(elem.id)
                self.main_window.set_status(f"Elemento {elem.id} seleccionado")
                return

    def _point_in_quad(self, px, py, pts):
        """Verifica si un punto esta dentro de un cuadrilatero."""
        n = len(pts)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-15) + xi):
                inside = not inside
            j = i
        return inside

    # ═════════════════════════════════════════════════════════════════════
    # METODOS PUBLICOS
    # ═════════════════════════════════════════════════════════════════════

    def highlight_node(self, node_id):
        self.highlighted_node = node_id
        self.highlighted_element = None
        self.redraw()

    def highlight_element(self, elem_id):
        self.highlighted_element = elem_id
        self.highlighted_node = None
        self.redraw()

    def set_result_values(self, values, label="Resultado"):
        """Activa la visualizacion de resultados con mapa de colores.

        Parametros:
            values: dict {node_id: float} con valores en cada nodo.
            label: etiqueta para la barra de colores.
        """
        self.result_values = values
        self.result_label = label
        vals = list(values.values())
        self.result_vmin = min(vals) if vals else 0
        self.result_vmax = max(vals) if vals else 1
        if self.result_vmin == self.result_vmax:
            self.result_vmax = self.result_vmin + 1
        self.redraw()

    def set_deformed(self, displacements, scale=1.0):
        """Activa la visualizacion de malla deformada.

        Parametros:
            displacements: numpy array con desplazamientos u.
            scale: factor de escala para la deformacion.
        """
        self.displacements = displacements
        if displacements is not None:
            max_disp = np.max(np.abs(displacements))
            if max_disp > 0:
                coords = np.array([
                    [self.project.nodes[n].x, self.project.nodes[n].y]
                    for n in sorted(self.project.nodes.keys())
                ])
                model_size = max(
                    coords[:, 0].max() - coords[:, 0].min(),
                    coords[:, 1].max() - coords[:, 1].min()
                )
                self.deform_scale = model_size * 0.1 / max_disp * scale
            else:
                self.deform_scale = 0
            self.show_deformed = True
        else:
            self.show_deformed = False
            self.deform_scale = 0
        self.redraw()

    def clear_results(self):
        """Limpia la visualizacion de resultados."""
        self.result_values = None
        self.result_label = ""
        self.show_deformed = False
        self.displacements = None
        self.deform_scale = 0
        self.redraw()
        self.main_window.set_status("Resultados limpiados.")

    def fit_view(self):
        """Ajusta la vista para mostrar todo el modelo."""
        if not self.project.nodes:
            self.scale = 1.0
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            self.offset_x = w / 2
            self.offset_y = h / 2
            self.redraw()
            return

        xs = [n.x for n in self.project.nodes.values()]
        ys = [n.y for n in self.project.nodes.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        margin = 0.15
        range_x = max_x - min_x if max_x != min_x else 1
        range_y = max_y - min_y if max_y != min_y else 1
        range_x *= (1 + margin * 2)
        range_y *= (1 + margin * 2)

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        scale_x = w / range_x
        scale_y = h / range_y
        self.scale = min(scale_x, scale_y)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.offset_x = w / 2 - center_x * self.scale
        self.offset_y = h / 2 + center_y * self.scale

        self.redraw()
