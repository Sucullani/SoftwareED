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
from education.components.iso_inverse import iso_inverse_map, natural_to_physical
from fem.shape_functions import get_shape_functions
from config.settings import (
    ELEMENT_Q4, ELEMENT_Q9,
    EDU_FIG_BG, EDU_AXES_BG, EDU_LABEL_BG, EDU_FG, EDU_FG_MUTED,
)


_C_BLUE = "#4fa3ff"
_C_ORANGE = "#ff9f43"
_C_RED = "#ef5350"
_C_CYAN = "#80deea"           # snap a nodo (modo "discreto")
_C_MUTED_RED = "#d68a7a"      # punto libre (modo "continuo")


# Snap radius para reconocer "click sobre un nodo" en el canvas real (px).
_SNAP_PX = 18

# Tag canvas — identifica TODOS los items de M1 para borrarlos en cada redraw.
_TAG = "edu_m1"


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

        # ── Chip de dualidad: única razón de su existencia es ENSEÑAR
        # que (x,y) y (ξ,η) son dos nombres del mismo punto.
        # NO navega — para eso está el crossref al pie. SÍ pulsa cuando
        # el alumno gatilla la traducción (click libre físico): el flash
        # amarillo es el "instante didáctico" de ver al mapeo trabajando.
        chip_frame = ttk.Frame(body)
        chip_frame.pack(fill="x", padx=4, pady=(0, 4))
        self._lbl_chip = tk.Label(
            chip_frame,
            text="(x, y)  ⇄  (ξ, η)",
            bg=EDU_LABEL_BG, fg=_C_CYAN,
            font=("Consolas", 11, "bold"),
            padx=8, pady=4,
        )
        self._lbl_chip.pack(fill="x")
        self._chip_after_id: Optional[str] = None

        # Línea de estado dinámica: indica el modo de la última selección.
        # Vacía hasta el primer click.
        self._lbl_mode = tk.Label(
            body, text="", bg=EDU_AXES_BG, fg=EDU_FG_MUTED,
            font=("Consolas", 9, "italic"), anchor="w", justify="left",
        )
        self._lbl_mode.pack(fill="x", padx=4, pady=(0, 2))

        # ── Figura 2×1: cuadrado natural + superficie 3D ─────────
        self._fig = Figure(figsize=(4.8, 5.0), dpi=100)
        from education.components.edu_plot_style import (
            apply_edu_style_figure, apply_edu_style_2d, apply_edu_style_3d,
        )
        apply_edu_style_figure(self._fig)
        gs = self._fig.add_gridspec(
            2, 1, height_ratios=[1, 1.05],
            hspace=0.18, left=0.08, right=0.96, top=0.93, bottom=0.04,
        )
        self._ax_nat = self._fig.add_subplot(gs[0, 0])
        self._ax_n3d = self._fig.add_subplot(gs[1, 0], projection="3d")
        apply_edu_style_2d(self._ax_nat, show_spines=True)
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
            fill=color, outline="#ffffff", width=1.0,
            tags=_TAG,
        )
        # Label compacto con la Nᵢ actual y su valor en este punto.
        try:
            N_fn, _ = get_shape_functions(self._explore_type)
            ni_val = float(N_fn(self._sel_xi, self._sel_eta)[self._node_idx - 1])
        except Exception:
            ni_val = 0.0
        mesh.canvas.create_text(
            sx + 14, sy - 12,
            text=f"N{self._node_idx}={ni_val:+.3f}",
            fill=color, font=("Consolas", 8, "bold"),
            anchor="w", tags=_TAG,
        )

    def on_closed(self) -> None:
        try:
            self._mesh.remove_click_consumer(self._click_consumer)
        except Exception:
            pass
        if self._chip_after_id is not None:
            try:
                self._mesh.after_cancel(self._chip_after_id)
            except Exception:
                pass
            self._chip_after_id = None

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
        self._pulse_chip()
        self._redraw()
        self._refresh_mode_label()
        return True

    def _element_coords(self) -> Optional[np.ndarray]:
        if self.project is None or self.element is None:
            return None
        try:
            return np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in self.element.node_ids
            ], dtype=float)
        except KeyError:
            return None

    # ── Chip narrativo: pulso al gatillar inverse map ──────────────
    def _pulse_chip(self) -> None:
        """Flash visual del chip narrativo: cyan → amarillo → cyan.
        Comunica "el Jacobiano acaba de traducir tu click físico"."""
        if self._lbl_chip is None:
            return
        try:
            self._lbl_chip.configure(fg="#ffd54f", bg="#3a3520")
        except tk.TclError:
            return
        if self._chip_after_id is not None:
            try:
                self._mesh.after_cancel(self._chip_after_id)
            except Exception:
                pass
        try:
            self._chip_after_id = self._mesh.after(
                450, self._reset_chip,
            )
        except tk.TclError:
            self._chip_after_id = None

    def _reset_chip(self) -> None:
        self._chip_after_id = None
        try:
            self._lbl_chip.configure(fg=_C_CYAN, bg=EDU_LABEL_BG)
        except tk.TclError:
            pass

    # ── Label de modo (compacto, sin jerga) ───────────────────────
    def _refresh_mode_label(self) -> None:
        if self._lbl_mode is None:
            return
        coord_str = f"(ξ, η) = ({self._sel_xi:+.3f}, {self._sel_eta:+.3f})"
        if self._mode == "init":
            self._lbl_mode.configure(
                text="Clickeá un nodo o cualquier punto interior del elemento.",
                fg=EDU_FG_MUTED,
            )
        elif self._mode == "snap_node":
            self._lbl_mode.configure(
                text=f"nodo {self._node_idx}   ·   {coord_str}", fg=_C_CYAN,
            )
        elif self._mode == "free_physical":
            self._lbl_mode.configure(
                text=f"punto libre   ·   {coord_str}", fg=_C_MUTED_RED,
            )
        elif self._mode == "free_natural":
            self._lbl_mode.configure(
                text=f"punto libre   ·   {coord_str}", fg=_C_MUTED_RED,
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
        # Estética alineada con el inset compartido (gauss_inset.py): mismo
        # marco azul `#4fa3ff` lw=1.4, ejes `#3a5278` lw=0.8, tipografía
        # Consolas en labels. Los nodos (corners/mids/centroide) son
        # SEMÁNTICAMENTE distintos a los PGs del inset — acá se grafica el
        # cuadrado natural del ELEMENTO de referencia, no los puntos de
        # cuadratura — así que la paleta de marcadores se mantiene.
        ax.clear()
        from education.components.edu_plot_style import apply_edu_style_2d
        apply_edu_style_2d(ax, show_spines=True)
        ax.set_aspect("equal")
        sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        ax.plot(sq[:, 0], sq[:, 1], color=_C_BLUE, lw=1.0)
        ax.fill(sq[:, 0], sq[:, 1], color=_C_BLUE, alpha=0.06)
        ax.axhline(0, color="#3a5278", lw=0.8, alpha=0.85)
        ax.axvline(0, color="#3a5278", lw=0.8, alpha=0.85)
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
        ax.set_title(f"N{node_idx}(ξ, η)",
                      color="#90caf9", fontsize=8, pad=2)
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
        try:
            ni_val = float(N_fn(self._sel_xi, self._sel_eta)[self._node_idx - 1])
            self._ax_n3d.scatter(
                [self._sel_xi], [self._sel_eta], [ni_val],
                s=60, c=marker_color, edgecolors="white", linewidths=1.2,
                zorder=20, depthshade=False,
            )
        except Exception:
            ni_val = 0.0
        try:
            self._ax_nat.text(
                0.02, 0.98,
                f"(ξ,η) = ({self._sel_xi:+.2f}, {self._sel_eta:+.2f})\n"
                f"N{self._node_idx} = {ni_val:+.3f}",
                transform=self._ax_nat.transAxes,
                color=marker_color, fontsize=7, family="monospace",
                va="top", ha="left",
                bbox=dict(facecolor=EDU_LABEL_BG,
                           edgecolor=marker_color, linewidth=0.8, alpha=0.8),
            )
        except Exception:
            pass

    def _xi_eta_grid(self, grid=25):
        xi = np.linspace(-1, 1, grid)
        eta = np.linspace(-1, 1, grid)
        return np.meshgrid(xi, eta)
