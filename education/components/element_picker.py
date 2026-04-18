"""
ElementPicker: panel con 2 vistas sincronizadas (física y natural) de un
elemento Q4/Q9. Click en cualquiera de las vistas selecciona un punto y
emite on_point_selected(xi, eta, x, y). También admite arrastre de nodos
físicos para deformar la geometría.

Usa Newton-Raphson para mapeo inverso (x,y) → (ξ,η).
"""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from matplotlib.patches import Polygon

from .plot_panel import PlotPanel, _theme_colors
from fem.shape_functions import (
    shape_functions_q4,
    get_shape_functions,
)


def _q4_boundary_xy(node_coords: np.ndarray, n: int = 40) -> np.ndarray:
    """Muestrea el borde del elemento recorriendo ξ=±1 y η=±1."""
    edges = []
    ts = np.linspace(-1, 1, n)
    for eta in [-1, 1]:
        for xi in ts if eta == -1 else ts[::-1]:
            N = shape_functions_q4(xi, eta)
            edges.append(N @ node_coords)
    for xi in [1, -1]:
        for eta in (ts if xi == 1 else ts[::-1]):
            N = shape_functions_q4(xi, eta)
            edges.append(N @ node_coords)
    return np.array(edges)


def physical_to_natural(
    x: float, y: float, node_coords: np.ndarray, element_type: str = "Q4",
    tol: float = 1e-10, max_iter: int = 50,
) -> Optional[tuple[float, float]]:
    """Newton-Raphson para invertir el mapeo isoparamétrico.

    Retorna (ξ, η) o None si no converge.
    """
    N_fn, dN_fn = get_shape_functions(element_type)
    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N = N_fn(xi, eta)
        dN = dN_fn(xi, eta)
        xy = N @ node_coords
        residual = np.array([xy[0] - x, xy[1] - y])
        if np.linalg.norm(residual) < tol:
            return xi, eta
        J = dN @ node_coords
        try:
            delta = np.linalg.solve(J, -residual)
        except np.linalg.LinAlgError:
            return None
        xi += delta[0]
        eta += delta[1]
        if abs(xi) > 5 or abs(eta) > 5:
            return None
    return None


def in_natural_domain(xi: float, eta: float, margin: float = 1e-6) -> bool:
    return -1 - margin <= xi <= 1 + margin and -1 - margin <= eta <= 1 + margin


class ElementPicker(PlotPanel):
    """PlotPanel con 2 subplots: elemento físico y dominio natural.

    Click en cualquiera selecciona un punto. Arrastrar nodos físicos deforma
    el elemento.
    """

    def __init__(
        self,
        parent,
        node_coords: np.ndarray,
        element_type: str = "Q4",
        on_point_selected: Optional[Callable[[float, float, float, float], None]] = None,
        on_geometry_changed: Optional[Callable[[np.ndarray], None]] = None,
        allow_drag: bool = True,
        show_gauss: bool = True,
        **kwargs,
    ):
        super().__init__(parent, subplots=(1, 2), figsize=(7.5, 3.8), **kwargs)
        self.node_coords = np.array(node_coords, dtype=float)
        self.element_type = element_type
        self.on_point_selected = on_point_selected
        self.on_geometry_changed = on_geometry_changed
        self.allow_drag = allow_drag
        self.show_gauss = show_gauss

        self.ax_phys, self.ax_nat = self.axes
        self.ax_phys.set_title("Elemento físico")
        self.ax_nat.set_title("Dominio natural (ξ, η)")
        self.ax_phys.set_aspect("equal")
        self.ax_nat.set_aspect("equal")

        self.selected_xi: Optional[float] = None
        self.selected_eta: Optional[float] = None
        self._drag_node_idx: Optional[int] = None

        self._draw_all()
        self.bind_click(self._on_click)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)

    # ---------- dibujo ----------
    def _draw_all(self) -> None:
        self.ax_phys.clear()
        self.ax_nat.clear()
        colors = _theme_colors()
        self._style_axes(self.ax_phys, colors, None)
        self._style_axes(self.ax_nat, colors, None)
        self.ax_phys.set_title("Elemento físico", color=colors["fg"])
        self.ax_nat.set_title("Dominio natural (ξ, η)", color=colors["fg"])
        self.ax_phys.set_aspect("equal")
        self.ax_nat.set_aspect("equal")

        # --- físico ---
        boundary = _q4_boundary_xy(self.node_coords[:4])
        self.ax_phys.plot(boundary[:, 0], boundary[:, 1], color="#4fa3ff", lw=1.8)
        self.ax_phys.fill(boundary[:, 0], boundary[:, 1], color="#4fa3ff", alpha=0.12)
        # nodos (solo los 4 esquineros como pickable)
        self.ax_phys.scatter(
            self.node_coords[:, 0], self.node_coords[:, 1],
            s=80, c="#ff9f43", edgecolors=colors["fg"], zorder=5, picker=6,
        )
        for i, (x, y) in enumerate(self.node_coords):
            self.ax_phys.annotate(
                str(i + 1), (x, y), textcoords="offset points", xytext=(6, 6),
                color=colors["fg"], fontsize=9,
            )

        # --- natural ---
        sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        self.ax_nat.plot(sq[:, 0], sq[:, 1], color="#4fa3ff", lw=1.8)
        self.ax_nat.fill(sq[:, 0], sq[:, 1], color="#4fa3ff", alpha=0.12)
        self.ax_nat.scatter(sq[:4, 0], sq[:4, 1], s=60, c="#ff9f43",
                            edgecolors=colors["fg"], zorder=5)
        for i, (xi, eta) in enumerate(sq[:4]):
            self.ax_nat.annotate(
                str(i + 1), (xi, eta), textcoords="offset points", xytext=(6, 6),
                color=colors["fg"], fontsize=9,
            )
        self.ax_nat.set_xlim(-1.3, 1.3)
        self.ax_nat.set_ylim(-1.3, 1.3)
        self.ax_nat.axhline(0, color=colors["grid"], lw=0.4)
        self.ax_nat.axvline(0, color=colors["grid"], lw=0.4)

        # Gauss points
        if self.show_gauss:
            from fem.gauss_quadrature import get_gauss_points_for_element
            gp, _ = get_gauss_points_for_element(self.element_type)
            self.ax_nat.scatter(gp[:, 0], gp[:, 1], s=35, c="#2ecc71",
                                marker="x", zorder=4, label="Gauss")
            # también en físico
            N_fn, _ = get_shape_functions(self.element_type)
            for xi, eta in gp:
                xy = N_fn(xi, eta) @ self.node_coords[: (4 if self.element_type == "Q4" else 9)]
                self.ax_phys.scatter(xy[0], xy[1], s=30, c="#2ecc71",
                                     marker="x", zorder=4)

        # Marcador del punto seleccionado
        if self.selected_xi is not None:
            N_fn, _ = get_shape_functions(self.element_type)
            xy = N_fn(self.selected_xi, self.selected_eta) @ \
                self.node_coords[: (4 if self.element_type == "Q4" else 9)]
            self.ax_phys.scatter(xy[0], xy[1], s=160, facecolors="none",
                                 edgecolors="#e74c3c", lw=2.2, zorder=6)
            self.ax_phys.scatter(xy[0], xy[1], s=20, c="#e74c3c", zorder=7)
            self.ax_nat.scatter(self.selected_xi, self.selected_eta, s=160,
                                facecolors="none", edgecolors="#e74c3c",
                                lw=2.2, zorder=6)
            self.ax_nat.scatter(self.selected_xi, self.selected_eta, s=20,
                                c="#e74c3c", zorder=7)

        # Pad físico
        margin = 0.2 * max(
            float(np.ptp(self.node_coords[:, 0])) or 1.0,
            float(np.ptp(self.node_coords[:, 1])) or 1.0,
        )
        self.ax_phys.set_xlim(self.node_coords[:, 0].min() - margin,
                              self.node_coords[:, 0].max() + margin)
        self.ax_phys.set_ylim(self.node_coords[:, 1].min() - margin,
                              self.node_coords[:, 1].max() + margin)

        self.redraw()

    # ---------- eventos ----------
    def _on_click(self, event) -> None:
        if event.inaxes not in (self.ax_phys, self.ax_nat):
            return

        # drag node?
        if event.inaxes is self.ax_phys and self.allow_drag:
            dists = np.linalg.norm(
                self.node_coords[:4] - np.array([event.xdata, event.ydata]), axis=1
            )
            # radio en coordenadas de datos
            xlim = self.ax_phys.get_xlim()
            pick_r = 0.05 * (xlim[1] - xlim[0])
            if dists.min() < pick_r:
                self._drag_node_idx = int(np.argmin(dists))
                return

        # click en dominio natural
        if event.inaxes is self.ax_nat:
            xi, eta = event.xdata, event.ydata
            if not in_natural_domain(xi, eta):
                return
            N_fn, _ = get_shape_functions(self.element_type)
            xy = N_fn(xi, eta) @ self.node_coords[: (4 if self.element_type == "Q4" else 9)]
            self._set_point(xi, eta, xy[0], xy[1])
            return

        # click en dominio físico → Newton-Raphson
        if event.inaxes is self.ax_phys:
            result = physical_to_natural(
                event.xdata, event.ydata, self.node_coords, self.element_type
            )
            if result is None:
                return
            xi, eta = result
            if not in_natural_domain(xi, eta, margin=0.02):
                return
            self._set_point(xi, eta, event.xdata, event.ydata)

    def _on_motion(self, event) -> None:
        if self._drag_node_idx is None:
            return
        if event.inaxes is not self.ax_phys or event.xdata is None:
            return
        self.node_coords[self._drag_node_idx] = [event.xdata, event.ydata]
        self._draw_all()

    def _on_release(self, _event) -> None:
        if self._drag_node_idx is not None:
            self._drag_node_idx = None
            if self.on_geometry_changed:
                self.on_geometry_changed(self.node_coords.copy())

    def _set_point(self, xi: float, eta: float, x: float, y: float) -> None:
        self.selected_xi = float(xi)
        self.selected_eta = float(eta)
        self._draw_all()
        if self.on_point_selected:
            self.on_point_selected(self.selected_xi, self.selected_eta, x, y)

    # ---------- api pública ----------
    def set_element_type(self, element_type: str) -> None:
        self.element_type = element_type
        self._draw_all()

    def set_nodes(self, node_coords: np.ndarray) -> None:
        self.node_coords = np.array(node_coords, dtype=float)
        self._draw_all()

    def set_marker(self, xi: float, eta: float) -> None:
        """Coloca el marcador en (ξ, η) sin emitir callback."""
        self.selected_xi = float(xi)
        self.selected_eta = float(eta)
        self._draw_all()
