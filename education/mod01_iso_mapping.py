"""
Módulo 1 — Coordenadas naturales, Funciones de forma (overlay)

**Rediseño 2026-05 (compactación)**: el overlay original (620×680) mostraba
un split 2×2 con panel físico + natural arriba y dos superficies 3D abajo
(natural limpia + pulled-back). El panel físico DUPLICABA lo que el canvas
real ya muestra y la superficie pulled-back agregaba carga visual sin
correspondencia pedagógica proporcional.

Diseño actual (compacto, ~480×560):
    1. Banner narrativo arriba: `(x,y) ⇄ (ξ,η)` con el Jacobiano (②) como
       traductor — chip clickeable que abre M2.
    2. Panel matplotlib: cuadrado natural (ξ, η) con marcadores de nodos
       + superficie 3D Nᵢ(ξ, η) limpia tensor-product.
    3. Click consumer en el MeshCanvas (modo overlay):
        - Click cerca de un NODO del elemento actual → ancla Nᵢ y posiciona
          el marcador en (ξ, η) del nodo.
        - Click en CUALQUIER PUNTO interior del elemento → inverse map
          Newton-Raphson → marcador en el (ξ, η) resultante (free probe).
        - Cualquiera de los dos casos PRESERVA la selección del elemento
          (el consumer consume el click → el canvas omite su hit-test
          estándar → el elemento queda fijo bajo el módulo).
        - Click fuera del elemento → fall-through al canvas (puede cambiar
          de elemento, deseleccionar, etc.).
    4. Click en el panel natural (matplotlib): snap a nodo natural si
       cerca; sino punto libre en (ξ, η) — sin pasar por el canvas, así
       no afecta la selección.
    5. Cross-reference al pie → M2 (Jacobiano).

**El "buttons turn off when clicking nodes" se corrige con el click
consumer**: antes, clickear un nodo en el canvas disparaba `select_node`
estándar que colapsaba la selección del elemento — el panel veía
`elements={}` y grizaba los botones. Ahora el consumer intercepta clicks
sobre nodos y puntos interiores del elemento bajo análisis, retorna True
y el canvas NO ejecuta su rama de selección — el elemento queda pinneado
mientras M1 esté activo (consistente con el resto de overlays M2/M4/M5b).
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from education.overlay_module import CanvasOverlayModule
from education.components.iso_inverse import (
    iso_inverse_map, natural_to_physical, element_coords,
)
from fem.shape_functions import get_shape_functions
from config.settings import (
    ELEMENT_Q4, ELEMENT_Q9,
    EDU_AXES_BG, EDU_LABEL_BG, EDU_FG_MUTED,
    EDU_NATURAL_OUTLINE_COLOR, EDU_NATURAL_AXES_COLOR,
    GAUSS_CANONICAL_COLOR, EDU_FREE_POINT_COLOR, EDU_MARKER_OUTLINE_COLOR,
)


# Colores del cuadrado natural — estilo de referencia, fuente única en
# config/settings.py (compartidos con el widget tk GaussCoordReadout).
_C_BLUE = EDU_NATURAL_OUTLINE_COLOR
_C_ORANGE = "#ff9f43"             # nodos vértice (identidad pedagógica de M1)
_C_RED = "#ef5350"                # marcador de punto libre (rojo M1)
_C_CYAN = GAUSS_CANONICAL_COLOR   # snap a nodo (modo "discreto")
_C_MUTED_RED = EDU_FREE_POINT_COLOR  # punto libre (modo "continuo")


# Snap radius para reconocer "click sobre un nodo" en el canvas real (px).
_SNAP_PX = 18

# Tag canvas — identifica TODOS los items de M1 para borrarlos en cada redraw.
_TAG = "edu_m1"


# Fórmulas LaTeX de las funciones de forma (idea 5). Espejan exactamente
# fem/shape_functions.py (shape_functions_q4 / shape_functions_q9). Se
# muestran simbólicamente en el módulo (el código sigue siendo la fuente
# de verdad). Reactivas al nodo seleccionado.
_N_FORMULAS_Q4 = {
    1: r"N_1(\xi,\eta) = \dfrac{1}{4}(1-\xi)(1-\eta)",
    2: r"N_2(\xi,\eta) = \dfrac{1}{4}(1+\xi)(1-\eta)",
    3: r"N_3(\xi,\eta) = \dfrac{1}{4}(1+\xi)(1+\eta)",
    4: r"N_4(\xi,\eta) = \dfrac{1}{4}(1-\xi)(1+\eta)",
}
_N_FORMULAS_Q9 = {
    1: r"N_1 = \dfrac{1}{4}\,\xi(\xi-1)\,\eta(\eta-1)",
    2: r"N_2 = \dfrac{1}{4}\,\xi(\xi+1)\,\eta(\eta-1)",
    3: r"N_3 = \dfrac{1}{4}\,\xi(\xi+1)\,\eta(\eta+1)",
    4: r"N_4 = \dfrac{1}{4}\,\xi(\xi-1)\,\eta(\eta+1)",
    5: r"N_5 = \dfrac{1}{2}\,(1-\xi^2)\,\eta(\eta-1)",
    6: r"N_6 = \dfrac{1}{2}\,\xi(\xi+1)(1-\eta^2)",
    7: r"N_7 = \dfrac{1}{2}\,(1-\xi^2)\,\eta(\eta+1)",
    8: r"N_8 = \dfrac{1}{2}\,\xi(\xi-1)(1-\eta^2)",
    9: r"N_9 = (1-\xi^2)(1-\eta^2)",
}


class IsoMappingModule(CanvasOverlayModule):
    """M1 overlay: cuadrado natural + superficie Nᵢ(ξ,η) + selección
    bidireccional físico↔natural."""

    TITLE = "①  Mapeo isoparamétrico  (x,y) ↔ (ξ,η)"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 500
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = False

    def build_overlay(self, body):
        # Estado: punto activo en coords naturales + índice de la Nᵢ activa
        # + modo de la última selección (snap-node / free-physical / free-
        # natural) para colorear la narrativa.
        self._sel_xi: float = 0.0
        self._sel_eta: float = 0.0
        self._node_idx = 1
        self._mode: str = "init"   # "snap_node" | "free_physical" | "free_natural" | "init"

        # Click consumer (bound method para identidad estable al deregister).
        self._click_consumer = self._on_canvas_click_consume

        self._refresh_explore_type()

        # NOTA: el chip `(x,y) ↔ (ξ,η)` fue eliminado — el título del overlay
        # (`①  Mapeo isoparamétrico  (x,y) ↔ (ξ,η)`) ya enuncia esa dualidad,
        # así que repetirla en el cuerpo era ruido redundante.

        # Línea de estado dinámica: indica el modo de la última selección.
        # Vacía hasta el primer click.
        self._lbl_mode = tk.Label(
            body, text="", bg=EDU_AXES_BG, fg=EDU_FG_MUTED,
            font=("Consolas", 9, "italic"), anchor="w", justify="left",
        )
        self._lbl_mode.pack(fill="x", padx=4, pady=(0, 2))

        # ── Figura 2×1: cuadrado natural + superficie 3D ─────────
        # La fórmula simbólica Nᵢ(ξ,η) es el TÍTULO de la superficie 3D
        # (la superficie ES esa función) y la evaluación numérica vive como
        # readout PINNEADO en una esquina del panel 3D — ambos dejaron de ser
        # widgets tk apilados abajo, lo que libera alto vertical para agrandar
        # la superficie (height_ratios favorece la fila del 3D).
        self._fig = Figure(figsize=(4.8, 5.5), dpi=100)
        from education.components.edu_plot_style import (
            apply_edu_style_figure, apply_edu_style_2d, apply_edu_style_3d,
        )
        apply_edu_style_figure(self._fig)
        gs = self._fig.add_gridspec(
            2, 1, height_ratios=[0.82, 1.5],
            hspace=0.30, left=0.06, right=0.94, top=0.93, bottom=0.03,
        )
        self._ax_nat = self._fig.add_subplot(gs[0, 0])
        self._ax_n3d = self._fig.add_subplot(gs[1, 0], projection="3d")
        apply_edu_style_2d(self._ax_nat, show_spines=False)
        apply_edu_style_3d(self._ax_n3d)

        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=body)
        self._canvas_mpl.get_tk_widget().pack(fill="both", expand=True,
                                                pady=(0, 2))
        # Click en el panel natural: selecciona Nᵢ por nodo o ancla punto libre.
        self._canvas_mpl.mpl_connect("button_press_event", self._on_click_natural)

        # Cross-reference clickeable al pie del overlay.
        self._pack_crossref(
            body, "mod02",
            "👉 La distorsión local del mapeo (det J) se explora en ② Jacobiano.",
            wraplength=480,
        )

        self._redraw()
        self._refresh_mode_label()

    # ── Hooks de ciclo de vida ─────────────────────────────────────
    def on_activated(self) -> None:
        # Registramos el click consumer en el MeshCanvas. Sin esto, clickear
        # un nodo en el canvas dispara `select_node` que colapsa la
        # selección del elemento — el panel de módulos griza los botones
        # porque ve `elements={}`. Con el consumer, M1 consume clicks dentro
        # del elemento bajo análisis y preserva la selección.
        self._mesh.add_click_consumer(self._click_consumer)
        # Forzar primer dibujo de la capa overlay (el punto físico actual).
        try:
            self._mesh.redraw()
        except Exception:
            pass

    # ── Capa educativa sobre el canvas físico (bidireccional) ──────
    def draw_canvas_layer(self, mesh) -> None:
        """Dibuja en el canvas FÍSICO el punto que estamos traduciendo.

        Bidireccionalidad: clickear en el panel natural del overlay actualiza
        `_sel_xi, _sel_eta` → este método dibuja la imagen física vía
        `natural_to_physical`. Click en el canvas físico → el consumer
        actualiza `_sel_xi, _sel_eta` (inverse map o snap) → este método
        repinta. La capa del overlay (panel natural) y la capa del canvas
        (este dibujo) referencian al MISMO `(ξ, η)` — siempre coherentes.

        El color del marcador comunica el modo:
            cyan    — snap a nodo (Nᵢ identidad geométrica)
            rojo    — punto libre (en cualquier panel)

        El canvas es el espacio FÍSICO: su único trabajo es mostrar DÓNDE
        cae el punto sobre la geometría real (marcador). El valor numérico
        Nᵢ vive SOLO en el overlay (bajo la fórmula) — no se repite acá
        para no duplicar el dato entre canvas y overlay.
        """
        mesh.canvas.delete(_TAG)
        if self.element is None or self.project is None:
            return
        coords = self._element_coords()
        if coords is None or len(coords) < self._explore_n:
            return

        try:
            xy = natural_to_physical(
                self._sel_xi, self._sel_eta,
                coords[: self._explore_n], self._explore_type,
            )
        except Exception:
            return
        sx, sy = mesh.world_to_screen(float(xy[0]), float(xy[1]))

        color = _C_CYAN if self._mode == "snap_node" else _C_RED

        # Halo exterior dashed — distingue del estilo de los nodos del
        # canvas (que son discos rellenos sin dashed).
        mesh.canvas.create_oval(
            sx - 11, sy - 11, sx + 11, sy + 11,
            outline=color, width=2.0,
            dash=(4, 3) if self._mode != "snap_node" else None,
            tags=_TAG,
        )
        # Disco interior con outline blanco (legibilidad sobre cualquier fondo).
        mesh.canvas.create_oval(
            sx - 4, sy - 4, sx + 4, sy + 4,
            fill=color, outline=EDU_MARKER_OUTLINE_COLOR, width=1.0,
            tags=_TAG,
        )
        # SIN label de valor sobre el canvas: el número Nᵢ vive solo en el
        # overlay (bajo la fórmula). El marcador es el ancla física.

    def on_closed(self) -> None:
        try:
            self._mesh.remove_click_consumer(self._click_consumer)
        except Exception:
            pass

    # ── Sincronización con la selección del canvas ────────────────
    def on_element_selected(self, elem_id):
        if elem_id == self.element_id:
            return
        self.element_id = elem_id
        self.element = self.project.elements.get(elem_id) if self.project else None
        self._refresh_explore_type()
        if self._node_idx > self._explore_n:
            self._node_idx = 1
        # Al cambiar de elemento volvemos al modo "init" — no hay una
        # selección activa que comunicar.
        self._mode = "init"
        self._sel_xi, self._sel_eta = 0.0, 0.0
        self._redraw()
        self._refresh_mode_label()

    # ── Click consumer: snap a nodo / free probe en físico ─────────
    def _on_canvas_click_consume(self, event) -> bool:
        """Consumer registrado en MeshCanvas. Retorna True para consumir
        el click (preserva selección del elemento bajo análisis).

        Reglas:
          1. Sin elemento bajo análisis → False (fall-through al canvas).
          2. Click cerca de un nodo del elemento (snap radius `_SNAP_PX`)
             → snap a ese nodo, modo "snap_node". Consume.
          3. Click en cualquier punto INTERIOR del elemento → inverse map
             a (ξ, η), modo "free_physical". Consume + pulso del chip
             para visualizar al Jacobiano "trabajando". Si Newton no
             converge → fall-through.
          4. Click fuera del polígono macro del elemento → False
             (fall-through; permite cambiar de elemento).
        """
        if self.element is None or self.project is None:
            return False
        coords = self._element_coords()
        if coords is None:
            return False

        # 1) Snap a nodo del elemento bajo análisis (TODOS los nodos —
        # corners y mid/center en Q9; cada uno tiene su Nᵢ).
        best_local, best_dpx = -1, float("inf")
        for i, nid in enumerate(self.element.node_ids[: self._explore_n]):
            node = self.project.nodes.get(nid)
            if node is None:
                continue
            sx, sy = self._mesh.world_to_screen(node.x, node.y)
            d = math.hypot(sx - event.x, sy - event.y)
            if d < best_dpx:
                best_dpx, best_local = d, i
        if best_local >= 0 and best_dpx < _SNAP_PX:
            self._node_idx = best_local + 1
            self._sel_xi, self._sel_eta = self._natural_coords_for_node(best_local)
            self._mode = "snap_node"
            self._redraw()
            self._refresh_mode_label()
            return True

        # 2) Free probe en físico: convertir click → world → inverse map.
        wx, wy = self._mesh.screen_to_world(event.x, event.y)
        try:
            mapped = iso_inverse_map(
                wx, wy, coords[: self._explore_n], self._explore_type,
            )
        except Exception:
            mapped = None
        if mapped is None:
            # Click cae fuera del elemento o Newton no convergió — no
            # consumimos, dejamos que el canvas decida (cambio de elemento,
            # deselección, etc.).
            return False
        xi, eta = mapped
        self._sel_xi, self._sel_eta = float(xi), float(eta)
        # En modo libre NO cambiamos `_node_idx` — el alumno explora
        # dónde está ese punto físico en el cuadrado natural y CUÁNTO
        # vale la Nᵢ que tiene anclada actualmente.
        self._mode = "free_physical"
        self._redraw()
        self._refresh_mode_label()
        return True

    def _element_coords(self) -> Optional[np.ndarray]:
        # Delega al helper compartido (antes duplicado en M1/M2/M4/M5/M7).
        return element_coords(self.project, self.element)

    # ── Label de modo (compacto, sin jerga) ───────────────────────
    def _refresh_mode_label(self) -> None:
        # Solo comunica el MODO de la última selección. Las coords (ξ,η) NO
        # se muestran acá — viven en la sustitución bajo la fórmula
        # (`N₁(-0.286, +0.190) = ...`), donde son el input de la evaluación.
        # Así cada dato textual aparece una sola vez en el overlay.
        if self._lbl_mode is None:
            return
        if self._mode == "init":
            self._lbl_mode.configure(
                text="Clickeá un nodo o cualquier punto interior del elemento.",
                fg=EDU_FG_MUTED,
            )
        elif self._mode == "snap_node":
            self._lbl_mode.configure(
                text=f"nodo {self._node_idx}", fg=_C_CYAN,
            )
        else:  # free_physical | free_natural
            self._lbl_mode.configure(
                text="punto libre", fg=_C_MUTED_RED,
            )

    # ── Tipo de elemento (auto desde project/element) ──────────────
    def _refresh_explore_type(self):
        is_q9 = False
        if self.element is not None and getattr(self.element, "num_nodes", 0) == 9:
            is_q9 = True
        elif self.project is not None and \
                getattr(self.project, "element_type", None) == ELEMENT_Q9:
            is_q9 = True
        self._explore_type = ELEMENT_Q9 if is_q9 else ELEMENT_Q4
        self._explore_n = 9 if is_q9 else 4

    # ── Click handler en el panel natural (matplotlib) ────────────
    def _on_click_natural(self, event):
        if event.button != 1:
            return
        if event.inaxes is not self._ax_nat:
            return
        if event.xdata is None or event.ydata is None:
            return
        # Snap a nodo natural si está cerca.
        nat_coords = self._natural_node_coords()
        ex, ey = event.x, event.y
        best_i, best_d = None, float("inf")
        for i, (xn, yn) in enumerate(nat_coords):
            dx, dy = self._ax_nat.transData.transform((xn, yn))
            d = ((dx - ex) ** 2 + (dy - ey) ** 2) ** 0.5
            if d < best_d:
                best_d, best_i = d, i
        if best_i is not None and best_d < 18.0:
            self._node_idx = best_i + 1
            self._sel_xi, self._sel_eta = self._natural_coords_for_node(best_i)
            self._mode = "snap_node"
            self._redraw()
            self._refresh_mode_label()
            return
        # Punto libre en el dominio natural.
        xi, eta = float(event.xdata), float(event.ydata)
        if abs(xi) > 1.05 or abs(eta) > 1.05:
            return
        self._sel_xi, self._sel_eta = xi, eta
        self._mode = "free_natural"
        self._redraw()
        self._refresh_mode_label()

    def _natural_node_coords(self) -> np.ndarray:
        if self._explore_type == ELEMENT_Q9:
            return np.array([
                [-1, -1], [1, -1], [1, 1], [-1, 1],
                [0, -1],  [1, 0], [0, 1], [-1, 0],
                [0, 0],
            ], dtype=float)
        return np.array([
            [-1, -1], [1, -1], [1, 1], [-1, 1],
        ], dtype=float)

    def _natural_coords_for_node(self, idx: int):
        nc = self._natural_node_coords()
        return float(nc[idx, 0]), float(nc[idx, 1])

    # ── Fórmula + evaluación de Nᵢ como LaTeX (mathtext) ───────────
    # Ya NO son widgets tk apilados bajo la figura: la fórmula es el TÍTULO
    # de la superficie 3D (`_draw_surface_n`) y la evaluación es un readout
    # pinneado en la esquina del panel 3D (`_draw_markers`). Estos helpers
    # construyen los strings mathtext que consumen esos dos métodos.
    def _shape_formula_latex(self) -> str:
        """`$N_i(ξ,η) = ...$` de la función activa (espeja shape_functions)."""
        table = (_N_FORMULAS_Q9 if self._explore_type == ELEMENT_Q9
                 else _N_FORMULAS_Q4)
        expr = table.get(self._node_idx)
        return f"${expr}$" if expr else ""

    def _shape_value_latex(self) -> str:
        """`$N_i(ξ,η) = valor$` sustituido en el (ξ,η) actual (mathtext)."""
        try:
            N_fn, _ = get_shape_functions(self._explore_type)
            val = float(N_fn(self._sel_xi, self._sel_eta)[self._node_idx - 1])
        except Exception:
            return ""
        return (rf"$N_{{{self._node_idx}}}({self._sel_xi:.3f},\,"
                rf"{self._sel_eta:.3f}) = {val:.4f}$")

    # ── Render ─────────────────────────────────────────────────────
    def _redraw(self):
        if self._ax_nat is None:
            return
        N_fn, _ = get_shape_functions(self._explore_type)
        self._draw_natural(self._ax_nat)
        self._draw_surface_n(self._ax_n3d, N_fn, self._node_idx)
        self._draw_markers(N_fn)
        try:
            self._canvas_mpl.draw_idle()
        except tk.TclError:
            pass
        # Repintar la capa del canvas físico (marcador del punto traducido).
        # Bidireccional: cualquier cambio en (ξ, η) — venga del panel natural
        # o del canvas físico — se refleja en ambos lados simultáneamente.
        try:
            self._mesh.redraw()
        except Exception:
            pass

    def _draw_natural(self, ax):
        # Estética UNIFICADA con el inset compartido (gauss_inset.py): mismo
        # contorno azul `#4fa3ff`, ejes `#3a5278` lw=0.8, ±1 en Consolas y
        # SIN spines (el "marco exterior" de matplotlib) — el único borde es
        # el cuadrado natural mismo, igual que en M2/M4/M5. Los nodos
        # (corners/mids/centroide) son SEMÁNTICAMENTE distintos a los PGs del
        # inset (acá el cuadrado del ELEMENTO de referencia, no los puntos de
        # cuadratura), así que la paleta de marcadores se mantiene.
        ax.clear()
        from education.components.edu_plot_style import apply_edu_style_2d
        apply_edu_style_2d(ax, show_spines=False)
        ax.set_aspect("equal")
        sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        ax.plot(sq[:, 0], sq[:, 1], color=_C_BLUE, lw=1.0)
        ax.fill(sq[:, 0], sq[:, 1], color=_C_BLUE, alpha=0.06)
        ax.axhline(0, color=EDU_NATURAL_AXES_COLOR, lw=0.8, alpha=0.85)
        ax.axvline(0, color=EDU_NATURAL_AXES_COLOR, lw=0.8, alpha=0.85)
        corners = sq[:4]
        ax.scatter(corners[:, 0], corners[:, 1], s=110,
                    c=_C_ORANGE, edgecolors="white", linewidths=1.2,
                    zorder=8)
        for i, (xi, eta) in enumerate(corners):
            ax.annotate(str(i + 1), (xi, eta),
                         textcoords="offset points", xytext=(0, 0),
                         color="black", fontsize=8, fontweight="bold",
                         ha="center", va="center")
        if self._explore_type == ELEMENT_Q9:
            mids = np.array([[0, -1], [1, 0], [0, 1], [-1, 0]])
            ax.scatter(mids[:, 0], mids[:, 1], s=60,
                        c="#90caf9", edgecolors="white", linewidths=0.8,
                        zorder=7)
            for i, (xi, eta) in enumerate(mids):
                ax.annotate(str(i + 5), (xi, eta),
                             textcoords="offset points", xytext=(0, 0),
                             color="black", fontsize=7,
                             ha="center", va="center")
            ax.scatter([0], [0], s=60, c="#ce93d8",
                        edgecolors="white", linewidths=0.8, zorder=7)
            ax.annotate("9", (0, 0),
                         textcoords="offset points", xytext=(0, 0),
                         color="black", fontsize=7,
                         ha="center", va="center")
        # Etiquetas ±1 + ξ / η: anclan la escala sin ejes numéricos
        # (mismo patrón que el inset). Consolas para coherencia con la
        # tipografía técnica del cuadrado natural compartido.
        ax.text( 1.0, -1.18, "+1", color=EDU_FG_MUTED,
                 fontsize=7, family="monospace", ha="center", va="top")
        ax.text(-1.0, -1.18, "-1", color=EDU_FG_MUTED,
                 fontsize=7, family="monospace", ha="center", va="top")
        ax.text( 1.30,  0.02, "ξ", color=EDU_FG_MUTED,
                 fontsize=9, family="monospace", fontweight="bold",
                 ha="left", va="center")
        ax.text( 0.02,  1.30, "η", color=EDU_FG_MUTED,
                 fontsize=9, family="monospace", fontweight="bold",
                 ha="left", va="center")
        ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4)
        ax.set_title("Cuadrado natural  (ξ, η)",
                      color=_C_BLUE, fontsize=9, fontweight="bold", pad=4)
        ax.set_xticks([]); ax.set_yticks([])

    def _draw_surface_n(self, ax, N_fn, node_idx):
        ax.clear()
        from education.components.edu_plot_style import apply_edu_style_3d
        apply_edu_style_3d(ax)
        XI, ET = self._xi_eta_grid(grid=25)
        Z = np.zeros_like(XI)
        for r in range(XI.shape[0]):
            for c in range(XI.shape[1]):
                Ns = N_fn(XI[r, c], ET[r, c])
                Z[r, c] = Ns[node_idx - 1]
        ax.plot_surface(XI, ET, Z, cmap="viridis",
                         edgecolor="none", alpha=0.78)
        try:
            ax.contour(XI, ET, Z, zdir="z", offset=Z.min() - 0.1,
                        cmap="viridis", levels=6, alpha=0.6)
        except Exception:
            pass
        # Título = la fórmula simbólica Nᵢ(ξ,η) en mathtext (reactiva al nodo).
        # La superficie ES esta función → su fórmula la rotula. Reemplaza al
        # antiguo `N{idx}(ξ,η)`, que duplicaba el lado izquierdo de la fórmula.
        ax.set_title(self._shape_formula_latex(),
                      color="#90caf9", fontsize=13, pad=8)
        try:
            ax.set_xticklabels([]); ax.set_yticklabels([])
        except Exception:
            pass

    def _draw_markers(self, N_fn):
        # Color del marcador según el modo de la última selección.
        marker_color = _C_CYAN if self._mode == "snap_node" else _C_RED

        # Punto sobre el panel natural.
        self._ax_nat.scatter([self._sel_xi], [self._sel_eta],
                              s=140, facecolors="none",
                              edgecolors=marker_color, linewidths=2.0,
                              zorder=10)
        self._ax_nat.scatter([self._sel_xi], [self._sel_eta],
                              s=30, c=marker_color, zorder=11)
        # Marcador 3D sobre la superficie Nᵢ (z = valor en el punto) + la
        # evaluación numérica ANCLADA al marcador: flota justo encima de él en
        # coords 3D (no pinneada a una esquina). Caja sutil para legibilidad
        # sobre el colormap. Es el ÚNICO lugar donde vive el valor numérico Nᵢ.
        try:
            ni_val = float(N_fn(self._sel_xi, self._sel_eta)[self._node_idx - 1])
            self._ax_n3d.scatter(
                [self._sel_xi], [self._sel_eta], [ni_val],
                s=60, c=marker_color, edgecolors="white", linewidths=1.2,
                zorder=20, depthshade=False,
            )
            val_tex = self._shape_value_latex()
            if val_tex:
                self._ax_n3d.text(
                    self._sel_xi, self._sel_eta, ni_val + 0.10, val_tex,
                    color=marker_color, fontsize=10,
                    ha="center", va="bottom", zorder=30,
                    bbox=dict(boxstyle="round,pad=0.3",
                               facecolor=EDU_LABEL_BG,
                               edgecolor=marker_color, linewidth=0.8,
                               alpha=0.88),
                )
        except Exception:
            pass

    def _xi_eta_grid(self, grid=25):
        xi = np.linspace(-1, 1, grid)
        eta = np.linspace(-1, 1, grid)
        return np.meshgrid(xi, eta)
