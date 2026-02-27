"""
MeshCanvas: Canvas interactivo compartido para visualizar la malla FEM.
Soporta zoom, pan, nodos, elementos, cargas, restricciones,
visualizacion de resultados con gradiente suave (jet) e isolineas.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import numpy as np

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

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
        self.result_values = None
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

        # Gradiente e isolineas
        self._gradient_photo = None  # referencia PIL para evitar GC
        self.show_isolines = False
        self.isoline_count = 10

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
        if self.result_vmax == self.result_vmin:
            t = 0.5
        else:
            t = (value - self.result_vmin) / (self.result_vmax - self.result_vmin)
        return self._jet_color(t)

    # ═════════════════════════════════════════════════════════════════════
    # TRANSFORMACION DE COORDENADAS
    # ═════════════════════════════════════════════════════════════════════

    def world_to_screen(self, x, y):
        sx = x * self.scale + self.offset_x
        sy = -y * self.scale + self.offset_y
        return sx, sy

    def screen_to_world(self, sx, sy):
        x = (sx - self.offset_x) / self.scale
        y = -(sy - self.offset_y) / self.scale
        return x, y

    def _get_node_screen_pos(self, nid):
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

    def _get_node_world_deformed(self, nid):
        """Coordenadas mundo del nodo con deformacion aplicada."""
        node = self.project.nodes.get(nid)
        if node is None:
            return 0, 0
        x, y = node.x, node.y
        if self.show_deformed and self.displacements is not None:
            idx = 2 * (nid - 1)
            if idx + 1 < len(self.displacements):
                x += self.deform_scale * self.displacements[idx]
                y += self.deform_scale * self.displacements[idx + 1]
        return x, y

    # ═════════════════════════════════════════════════════════════════════
    # DIBUJO PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════

    def redraw(self):
        """Redibuja toda la malla."""
        self.canvas.delete("all")
        self._draw_grid()

        if self.show_deformed and self.displacements is not None:
            self._draw_original_mesh_ghost()

        # Gradiente suave de resultados (debajo de aristas)
        if self.result_values:
            self._draw_gradient_elements()

        self._draw_elements()
        self._draw_nodes()

        if self.show_loads:
            self._draw_loads()
        if self.show_constraints:
            self._draw_constraints()

        self._draw_highlight()

        if self.result_values:
            if self.show_isolines:
                self._draw_isolines()
            self._draw_colorbar()

        self._draw_axes()

    # ═════════════════════════════════════════════════════════════════════
    # GRILLA, EJES, GHOST
    # ═════════════════════════════════════════════════════════════════════

    def _draw_grid(self):
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
        margin = 40
        length = 35
        bx, by = margin, self.canvas.winfo_height() - margin
        self.canvas.create_line(
            bx, by, bx + length, by, fill="#ef5350", width=2, arrow=tk.LAST
        )
        self.canvas.create_text(
            bx + length + 8, by, text="X", fill="#ef5350",
            font=("Segoe UI", 9, "bold"), anchor=W
        )
        self.canvas.create_line(
            bx, by, bx, by - length, fill="#4fc3f7", width=2, arrow=tk.LAST
        )
        self.canvas.create_text(
            bx, by - length - 8, text="Y", fill="#4fc3f7",
            font=("Segoe UI", 9, "bold"), anchor=S
        )

    def _draw_original_mesh_ghost(self):
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
            coords.extend(coords[:2])
            self.canvas.create_line(
                *coords, fill="#444466", width=1, dash=(3, 5)
            )

    # ═════════════════════════════════════════════════════════════════════
    # GRADIENTE SUAVE (PIL pixel-perfect con mapeo bilineal inverso)
    # ═════════════════════════════════════════════════════════════════════

    def _jet_rgb_vectorized(self, t):
        """Jet colormap vectorizado para numpy arrays."""
        t = np.clip(t, 0, 1)
        r = np.zeros_like(t)
        g = np.zeros_like(t)
        b = np.zeros_like(t)
        m1 = t < 0.25
        m2 = (t >= 0.25) & (t < 0.5)
        m3 = (t >= 0.5) & (t < 0.75)
        m4 = t >= 0.75
        g[m1] = t[m1] / 0.25; b[m1] = 1.0
        g[m2] = 1.0; b[m2] = 1.0 - (t[m2] - 0.25) / 0.25
        r[m3] = (t[m3] - 0.5) / 0.25; g[m3] = 1.0
        r[m4] = 1.0; g[m4] = 1.0 - (t[m4] - 0.75) / 0.25
        return r, g, b

    def _draw_gradient_elements(self):
        """Gradiente Gouraud: subdivision + rasterizacion de triangulos con PIL."""
        if not HAS_PIL:
            self._draw_gradient_polygons()
            return

        w = int(self.canvas.winfo_width())
        h = int(self.canvas.winfo_height())
        if w <= 1 or h <= 1:
            return

        img = np.zeros((h, w, 4), dtype=np.uint8)
        n = 6  # subdivisiones por arista (pocas: los triangulos dan suavidad)

        for elem in self.project.elements.values():
            nids = elem.node_ids[:4]
            if not all(nid in self.project.nodes and nid in self.result_values
                       for nid in nids):
                continue

            nc = []
            nv = []
            for nid in nids:
                x, y = self._get_node_world_deformed(nid)
                nc.append((x, y))
                nv.append(self.result_values[nid])

            # Generar grilla de puntos en coords naturales
            pts_grid = {}  # (i,j) -> (sx, sy, val)
            for i in range(n + 1):
                xi = -1 + 2 * i / n
                for j in range(n + 1):
                    eta = -1 + 2 * j / n
                    N = [(1 - xi) * (1 - eta) / 4,
                         (1 + xi) * (1 - eta) / 4,
                         (1 + xi) * (1 + eta) / 4,
                         (1 - xi) * (1 + eta) / 4]
                    wx = sum(N[k] * nc[k][0] for k in range(4))
                    wy = sum(N[k] * nc[k][1] for k in range(4))
                    val = sum(N[k] * nv[k] for k in range(4))
                    sx, sy = self.world_to_screen(wx, wy)
                    pts_grid[(i, j)] = (sx, sy, val)

            # Subdividir en triangulos y rasterizar cada uno
            for i in range(n):
                for j in range(n):
                    p00 = pts_grid[(i, j)]
                    p10 = pts_grid[(i + 1, j)]
                    p11 = pts_grid[(i + 1, j + 1)]
                    p01 = pts_grid[(i, j + 1)]
                    # 2 triangulos por sub-quad
                    self._rasterize_triangle(img, w, h, p00, p10, p11)
                    self._rasterize_triangle(img, w, h, p00, p11, p01)

        # Mostrar imagen en el canvas (1 solo item)
        pil_img = Image.fromarray(img, 'RGBA')
        self._gradient_photo = ImageTk.PhotoImage(pil_img)
        self.canvas.create_image(0, 0, anchor=NW, image=self._gradient_photo)

    def _rasterize_triangle(self, img, w, h, p0, p1, p2):
        """Rasteriza un triangulo con interpolacion baricentrica de color.

        Cada p es (sx, sy, valor). El color se interpola suavemente
        entre los 3 vertices usando coordenadas baricentricas.
        """
        sx0, sy0, v0 = p0
        sx1, sy1, v1 = p1
        sx2, sy2, v2 = p2

        # Bounding box en pantalla
        min_x = max(0, int(min(sx0, sx1, sx2)))
        max_x = min(w - 1, int(max(sx0, sx1, sx2)) + 1)
        min_y = max(0, int(min(sy0, sy1, sy2)))
        max_y = min(h - 1, int(max(sy0, sy1, sy2)) + 1)
        if min_x >= max_x or min_y >= max_y:
            return

        # Grilla de pixeles
        px = np.arange(min_x, max_x + 1, dtype=np.float64)
        py = np.arange(min_y, max_y + 1, dtype=np.float64)
        PX, PY = np.meshgrid(px, py)

        # Coordenadas baricentricas vectorizadas
        denom = (sy1 - sy2) * (sx0 - sx2) + (sx2 - sx1) * (sy0 - sy2)
        if abs(denom) < 1e-6:
            return  # triangulo degenerado

        lam0 = ((sy1 - sy2) * (PX - sx2) + (sx2 - sx1) * (PY - sy2)) / denom
        lam1 = ((sy2 - sy0) * (PX - sx2) + (sx0 - sx2) * (PY - sy2)) / denom
        lam2 = 1.0 - lam0 - lam1

        # Mascara: dentro del triangulo
        inside = (lam0 >= -0.001) & (lam1 >= -0.001) & (lam2 >= -0.001)
        if not np.any(inside):
            return

        # Interpolar valor en cada pixel
        vals = lam0 * v0 + lam1 * v1 + lam2 * v2

        # Jet colormap
        vrange = max(self.result_vmax - self.result_vmin, 1e-15)
        t = np.clip((vals - self.result_vmin) / vrange, 0, 1)
        rc, gc, bc = self._jet_rgb_vectorized(t)

        # Pintar pixeles
        iy = PY[inside].astype(int)
        ix = PX[inside].astype(int)
        valid = (iy >= 0) & (iy < h) & (ix >= 0) & (ix < w)
        iy, ix = iy[valid], ix[valid]
        img[iy, ix, 0] = (rc[inside][valid] * 255).astype(np.uint8)
        img[iy, ix, 1] = (gc[inside][valid] * 255).astype(np.uint8)
        img[iy, ix, 2] = (bc[inside][valid] * 255).astype(np.uint8)
        img[iy, ix, 3] = 255

    def _draw_gradient_polygons(self):
        """Fallback: gradiente con sub-poligonos si PIL no esta disponible."""
        n = 10
        for elem in self.project.elements.values():
            nids = elem.node_ids[:4]
            if not all(nid in self.project.nodes and nid in self.result_values
                       for nid in nids):
                continue
            nc = []
            nv = []
            for nid in nids:
                x, y = self._get_node_world_deformed(nid)
                nc.append((x, y))
                nv.append(self.result_values[nid])
            for i in range(n):
                xi0 = -1 + 2 * i / n
                xi1 = -1 + 2 * (i + 1) / n
                for j in range(n):
                    eta0 = -1 + 2 * j / n
                    eta1 = -1 + 2 * (j + 1) / n
                    corners = [(xi0, eta0), (xi1, eta0),
                               (xi1, eta1), (xi0, eta1)]
                    pts = []
                    val_sum = 0.0
                    for xi, eta in corners:
                        N = [(1 - xi) * (1 - eta) / 4,
                             (1 + xi) * (1 - eta) / 4,
                             (1 + xi) * (1 + eta) / 4,
                             (1 - xi) * (1 + eta) / 4]
                        x = sum(N[k] * nc[k][0] for k in range(4))
                        y = sum(N[k] * nc[k][1] for k in range(4))
                        v = sum(N[k] * nv[k] for k in range(4))
                        sx, sy = self.world_to_screen(x, y)
                        pts.extend([sx, sy])
                        val_sum += v
                    color = self._value_to_color(val_sum / 4)
                    self.canvas.create_polygon(*pts, fill=color, outline="")

    # ═════════════════════════════════════════════════════════════════════
    # ISOLINEAS (Marching Squares)
    # ═════════════════════════════════════════════════════════════════════

    def _draw_isolines(self):
        """Dibuja curvas de nivel usando marching squares por elemento."""
        if not self.result_values:
            return

        n_levels = self.isoline_count
        levels = np.linspace(self.result_vmin, self.result_vmax,
                             n_levels + 2)[1:-1]

        # Tabla marching squares: caso -> [(edge_a, edge_b), ...]
        seg_table = {
            1: [(0, 3)], 2: [(0, 1)], 3: [(1, 3)], 4: [(1, 2)],
            5: [(0, 3), (1, 2)], 6: [(0, 2)], 7: [(2, 3)],
            8: [(2, 3)], 9: [(0, 2)], 10: [(0, 1), (2, 3)],
            11: [(1, 2)], 12: [(1, 3)], 13: [(0, 1)], 14: [(0, 3)],
        }

        n_grid = 16
        for elem in self.project.elements.values():
            nids = elem.node_ids[:4]
            if not all(nid in self.project.nodes and nid in self.result_values
                       for nid in nids):
                continue

            nc = []
            nv = []
            for nid in nids:
                x, y = self._get_node_world_deformed(nid)
                nc.append((x, y))
                nv.append(self.result_values[nid])

            # Crear grilla de coordenadas/valores
            xi_arr = np.linspace(-1, 1, n_grid)
            eta_arr = np.linspace(-1, 1, n_grid)
            gx = np.zeros((n_grid, n_grid))
            gy = np.zeros((n_grid, n_grid))
            gv = np.zeros((n_grid, n_grid))

            for ci in range(n_grid):
                xi = xi_arr[ci]
                for cj in range(n_grid):
                    eta = eta_arr[cj]
                    N = [(1 - xi) * (1 - eta) / 4,
                         (1 + xi) * (1 - eta) / 4,
                         (1 + xi) * (1 + eta) / 4,
                         (1 - xi) * (1 + eta) / 4]
                    gx[cj, ci] = sum(N[k] * nc[k][0] for k in range(4))
                    gy[cj, ci] = sum(N[k] * nc[k][1] for k in range(4))
                    gv[cj, ci] = sum(N[k] * nv[k] for k in range(4))

            for level in levels:
                for ci in range(n_grid - 1):
                    for cj in range(n_grid - 1):
                        v00 = gv[cj, ci]
                        v10 = gv[cj, ci + 1]
                        v11 = gv[cj + 1, ci + 1]
                        v01 = gv[cj + 1, ci]

                        case = 0
                        if v00 >= level: case |= 1
                        if v10 >= level: case |= 2
                        if v11 >= level: case |= 4
                        if v01 >= level: case |= 8

                        if case == 0 or case == 15 or case not in seg_table:
                            continue

                        x00, y00 = gx[cj, ci], gy[cj, ci]
                        x10, y10 = gx[cj, ci+1], gy[cj, ci+1]
                        x11, y11 = gx[cj+1, ci+1], gy[cj+1, ci+1]
                        x01, y01 = gx[cj+1, ci], gy[cj+1, ci]

                        # Puntos de cruce por arista
                        edge_pts = {}
                        pairs = [
                            (0, v00, x00, y00, v10, x10, y10),
                            (1, v10, x10, y10, v11, x11, y11),
                            (2, v11, x11, y11, v01, x01, y01),
                            (3, v01, x01, y01, v00, x00, y00),
                        ]
                        for eid, va, xa, ya, vb, xb, yb in pairs:
                            if (va >= level) != (vb >= level):
                                dv = vb - va
                                t = (level - va) / dv if abs(dv) > 1e-15 else 0.5
                                t = max(0.0, min(1.0, t))
                                edge_pts[eid] = (
                                    xa + t * (xb - xa),
                                    ya + t * (yb - ya)
                                )

                        for ea, eb in seg_table[case]:
                            if ea in edge_pts and eb in edge_pts:
                                px1, py1 = edge_pts[ea]
                                px2, py2 = edge_pts[eb]
                                s1x, s1y = self.world_to_screen(px1, py1)
                                s2x, s2y = self.world_to_screen(px2, py2)
                                self.canvas.create_line(
                                    s1x, s1y, s2x, s2y,
                                    fill="white", width=1.2
                                )

    # ═════════════════════════════════════════════════════════════════════
    # ELEMENTOS, NODOS, CARGAS, RESTRICCIONES
    # ═════════════════════════════════════════════════════════════════════

    def _draw_elements(self):
        """Dibuja aristas y etiquetas de elementos."""
        for elem in self.project.elements.values():
            coords = []
            valid = True
            for nid in elem.node_ids[:4]:
                if nid not in self.project.nodes:
                    valid = False
                    break
                sx, sy = self._get_node_screen_pos(nid)
                coords.extend([sx, sy])
            if not valid or len(coords) < 8:
                continue

            # Sin relleno — el gradiente maneja el color
            fill_color = ""

            outline_color = CANVAS_ELEMENT_COLOR
            if self.highlighted_element == elem.id:
                outline_color = CANVAS_SELECTED_COLOR

            edge_color = outline_color if self.show_mesh_edges else ""

            self.canvas.create_polygon(
                *coords,
                outline=edge_color,
                fill=fill_color,
                width=2 if self.highlighted_element == elem.id else 1.5,
            )

            if self.show_elem_labels:
                cx = sum(coords[::2]) / 4
                cy = sum(coords[1::2]) / 4
                text_color = "#222" if self.result_values else "#aaaaaa"
                self.canvas.create_text(
                    cx, cy, text=str(elem.id),
                    fill=text_color,
                    font=("Segoe UI", CANVAS_FONT_SIZE, "bold"),
                    anchor=tk.CENTER
                )

    def _draw_nodes(self):
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
        size = 12
        for bc in self.project.boundary_conditions.values():
            node = self.project.nodes.get(bc.node_id)
            if node is None:
                continue
            sx, sy = self._get_node_screen_pos(bc.node_id)

            if bc.is_fixed:
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
        if self.highlighted_node:
            if self.highlighted_node in self.project.nodes:
                sx, sy = self._get_node_screen_pos(self.highlighted_node)
                r = CANVAS_NODE_RADIUS + 8
                self.canvas.create_oval(
                    sx - r, sy - r, sx + r, sy + r,
                    outline=CANVAS_SELECTED_COLOR, fill="", width=2, dash=(4, 2)
                )

    def _draw_colorbar(self):
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

        self.canvas.create_rectangle(
            x0, y0, x0 + bar_w, y0 + bar_h,
            outline="#aaa", width=1
        )

        n_labels = 5
        for i in range(n_labels + 1):
            t = 1.0 - i / n_labels
            val = self.result_vmin + t * (self.result_vmax - self.result_vmin)
            yy = y0 + i * bar_h / n_labels
            self.canvas.create_text(
                x0 - 5, yy, text=f"{val:.2f}",
                fill="white", font=("Consolas", 7), anchor=tk.E
            )

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
        wx, wy = self.screen_to_world(event.x, event.y)
        self.coord_label.config(text=f"x: {wx:.2f}  y: {wy:.2f}")

    def _on_click(self, event):
        wx, wy = self.screen_to_world(event.x, event.y)
        min_dist = float("inf")
        closest_node = None
        for nid, node in self.project.nodes.items():
            dx = node.x - wx
            dy = node.y - wy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_node = nid

        threshold = 15 / self.scale
        if closest_node and min_dist < threshold:
            self.highlight_node(closest_node)
            self.main_window.set_status(
                f"Nodo {closest_node} seleccionado "
                f"({self.project.nodes[closest_node].x:.2f}, "
                f"{self.project.nodes[closest_node].y:.2f})"
            )
            return

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
        n = len(pts)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if ((yi > py) != (yj > py)) and \
               (px < (xj - xi) * (py - yi) / (yj - yi + 1e-15) + xi):
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
        self.result_values = values
        self.result_label = label
        vals = list(values.values())
        self.result_vmin = min(vals) if vals else 0
        self.result_vmax = max(vals) if vals else 1
        if self.result_vmin == self.result_vmax:
            self.result_vmax = self.result_vmin + 1
        self.redraw()

    def set_deformed(self, displacements, scale=1.0):
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

    def set_isolines(self, show, count=10):
        """Activa/desactiva isolineas con el numero de niveles."""
        self.show_isolines = show
        self.isoline_count = count
        self.redraw()

    def clear_results(self):
        self.result_values = None
        self.result_label = ""
        self.show_deformed = False
        self.displacements = None
        self.deform_scale = 0
        self.show_isolines = False
        self.redraw()
        self.main_window.set_status("Resultados limpiados.")

    def fit_view(self):
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
