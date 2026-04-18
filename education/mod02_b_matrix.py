"""
Módulo 2 — Matriz B (relación deformación-desplazamiento)

    ε = B · u

Interfaz: arriba 1×2 (elemento físico / natural) + abajo: B(ξ,η) en LaTeX.

Snap a puntos de Gauss: al hacer click en el elemento físico, si el cursor
(en coordenadas naturales) cae cerca de un punto de Gauss, se hace snap
automático. El combobox permite además seleccionar explícitamente
centro, pg1..pgN o modo libre.
"""

from __future__ import annotations

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from education.base_module import BaseEducationalModule
from education.components import (
    PlotPanel, TheoryDoc,
    iso_inverse_map, natural_to_physical,
    render_matrix_latex,
)
from education.components.plot_panel import _theme_colors

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian
from fem.b_matrix import compute_b_matrix
from fem.gauss_quadrature import get_gauss_points_for_element


class BMatrixModule(BaseEducationalModule):
    TITLE = "② Matriz B  (ε = B · u)"
    HAS_ANIMATION = False

    SNAP_THRESHOLD = 0.18   # distancia en coord. natural para snap a pg

    def __init__(self, parent, project, element_id):
        self._element_type = "Q4"
        self._n_nodes = 4
        if project and project.elements.get(element_id):
            et = project.elements[element_id].element_type
            if "Q9" in str(et) or "9 nodos" in str(et):
                self._element_type = "Q9"
                self._n_nodes = 9

        # Punto natural actual
        self._xi = 0.0
        self._eta = 0.0
        self._is_gauss = True  # el (0,0) es "centro" → se marca como destacado
        self._sel_mode = "centro"

        super().__init__(parent, project, element_id, width=1320, height=860)

    # ---------- controles ----------
    def build_controls(self, parent):
        ttk.Label(parent, text="Matriz B",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        ttk.Label(parent, wraplength=260, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "B relaciona desplazamientos nodales con deformaciones. "
                       "Se obtiene derivando las funciones de forma respecto a "
                       "(x,y) usando la inversa del Jacobiano:"
                       "\n"
                       "   ∂Nᵢ/∂x = J⁻¹ · ∂Nᵢ/∂ξ"
                   )).pack(anchor="w", pady=(0, 8))

        ttk.Separator(parent).pack(fill="x", pady=6)

        # Elemento
        ttk.Label(parent, text="Elemento",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.var_elem = tk.StringVar(value=self._element_type)
        ttk.Combobox(parent, textvariable=self.var_elem, state="readonly",
                      values=["Q4", "Q9"],
                      bootstyle="info").pack(fill="x", pady=(0, 8))
        self.var_elem.trace_add("write", lambda *a: self._on_element_changed())

        # Selector de punto
        ttk.Label(parent, text="Punto de evaluación",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.var_mode = tk.StringVar(value=self._sel_mode)
        self.cb_mode = ttk.Combobox(
            parent, textvariable=self.var_mode, state="readonly",
            values=self._mode_values(),
            bootstyle="info",
        )
        self.cb_mode.pack(fill="x", pady=(0, 8))
        self.var_mode.trace_add("write", lambda *a: self._on_mode_changed())

        ttk.Label(parent, wraplength=260, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "Click libre en el elemento físico o natural. Si el "
                       "cursor cae cerca de un punto de Gauss se hace snap "
                       "automático."
                   )).pack(anchor="w", pady=(0, 8))

        ttk.Separator(parent).pack(fill="x", pady=6)

        ttk.Label(parent, text="Estado",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.lbl_status = ttk.Label(parent, text="",
                                      font=("Consolas", 9),
                                      justify="left", anchor="w")
        self.lbl_status.pack(anchor="w", pady=(0, 6))

    def _mode_values(self) -> list[str]:
        n_pg = 4 if self._element_type == "Q4" else 9
        return ["centro"] + [f"pg{i}" for i in range(1, n_pg + 1)] + ["libre"]

    # ---------- visualización ----------
    def build_visualization(self, parent):
        parent.rowconfigure(0, weight=3)
        parent.rowconfigure(1, weight=2)
        parent.columnconfigure(0, weight=1)

        # Arriba: físico + natural
        self.top_panel = PlotPanel(
            parent, figsize=(10.5, 4.2),
            subplots=(1, 2), show_toolbar=False,
        )
        self.top_panel.grid(row=0, column=0, sticky="nsew")
        self.top_panel.bind_click(self._on_click)

        # Abajo: B como LaTeX
        self.bot_panel = PlotPanel(
            parent, figsize=(10.5, 3.0),
            subplots=(1, 1), show_toolbar=False,
        )
        self.bot_panel.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        self._redraw()

    # ---------- callbacks ----------
    def _on_element_changed(self) -> None:
        self._element_type = self.var_elem.get()
        self._n_nodes = 4 if self._element_type == "Q4" else 9
        self.cb_mode.configure(values=self._mode_values())
        self._sel_mode = "centro"
        self.var_mode.set("centro")
        self._xi, self._eta = 0.0, 0.0
        self._is_gauss = True
        self._redraw()

    def _on_mode_changed(self) -> None:
        mode = self.var_mode.get()
        self._sel_mode = mode
        if mode == "centro":
            self._xi, self._eta = 0.0, 0.0
            self._is_gauss = True
        elif mode.startswith("pg"):
            try:
                k = int(mode[2:]) - 1
            except ValueError:
                return
            pts, _ = get_gauss_points_for_element(self._element_type)
            if 0 <= k < len(pts):
                self._xi, self._eta = float(pts[k, 0]), float(pts[k, 1])
                self._is_gauss = True
        # "libre" no cambia el punto actual: se mueve por click
        self._redraw()

    def _on_click(self, event) -> None:
        if event.inaxes is None or event.xdata is None:
            return
        ax_phys = self.top_panel.axes[0]
        ax_nat = self.top_panel.axes[1]

        if event.inaxes is ax_phys:
            result = iso_inverse_map(event.xdata, event.ydata,
                                       self._node_coords(),
                                       self._element_type)
            if result is None:
                return
            xi, eta = result
        elif event.inaxes is ax_nat:
            xi, eta = float(event.xdata), float(event.ydata)
            if abs(xi) > 1.05 or abs(eta) > 1.05:
                return
        else:
            return

        # Snap a punto de Gauss
        snapped, k = self._snap_to_gauss(xi, eta)
        if snapped is not None:
            self._xi, self._eta = snapped
            self._is_gauss = True
            self._sel_mode = f"pg{k + 1}"
            self.var_mode.set(self._sel_mode)
        else:
            self._xi, self._eta = xi, eta
            self._is_gauss = False
            self._sel_mode = "libre"
            self.var_mode.set("libre")

        self._redraw()

    def _snap_to_gauss(self, xi: float, eta: float):
        pts, _ = get_gauss_points_for_element(self._element_type)
        d = np.hypot(pts[:, 0] - xi, pts[:, 1] - eta)
        k = int(np.argmin(d))
        if d[k] < self.SNAP_THRESHOLD:
            return (float(pts[k, 0]), float(pts[k, 1])), k
        return None, -1

    # ---------- dibujo ----------
    def _node_coords(self) -> np.ndarray:
        if self.project and self.element:
            return np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in self.element.node_ids
            ], dtype=float)
        return np.array(
            [[0, 0], [4, 0.2], [4.2, 3.2], [0.1, 3.0]],
            dtype=float,
        )

    def _redraw(self) -> None:
        colors = _theme_colors()
        self.top_panel.clear()

        coords = self._node_coords()[: self._n_nodes]
        ax_phys, ax_nat = self.top_panel.axes[0], self.top_panel.axes[1]

        self._draw_physical(ax_phys, coords, colors)
        self._draw_natural(ax_nat, colors)

        # marcador del punto actual
        xy = natural_to_physical(self._xi, self._eta, coords,
                                   self._element_type)
        self._mark(ax_phys, xy[0], xy[1], self._is_gauss)
        self._mark(ax_nat, self._xi, self._eta, self._is_gauss)

        self.top_panel.redraw()

        # Matriz B en LaTeX
        self._draw_b_matrix(coords, colors)

        self._update_status(xy)

    def _draw_physical(self, ax, coords, colors) -> None:
        ax.set_title("Elemento físico (x, y)", color=colors["fg"],
                     fontsize=11, pad=4)
        boundary = self._sample_boundary(coords)
        ax.plot(boundary[:, 0], boundary[:, 1], color="#4fa3ff", lw=1.8)
        ax.fill(boundary[:, 0], boundary[:, 1], color="#4fa3ff", alpha=0.10)

        corners = coords[:4]
        ax.scatter(corners[:, 0], corners[:, 1], s=70, c="#ff9f43",
                   edgecolors=colors["fg"], zorder=5)
        for i, (x, y) in enumerate(corners):
            ax.annotate(str(i + 1), (x, y),
                         textcoords="offset points", xytext=(6, 6),
                         color=colors["fg"], fontsize=9)

        # puntos de Gauss proyectados a físico
        pts, _ = get_gauss_points_for_element(self._element_type)
        gx = []
        gy = []
        for p in pts:
            pt = natural_to_physical(p[0], p[1], coords, self._element_type)
            gx.append(pt[0]); gy.append(pt[1])
        ax.scatter(gx, gy, s=90, marker="x", c="#e74c3c", lw=2.0,
                   zorder=6, label="puntos de Gauss")

        pad = 0.15 * max(
            float(np.ptp(coords[:, 0])) or 1.0,
            float(np.ptp(coords[:, 1])) or 1.0,
        )
        ax.set_xlim(coords[:, 0].min() - pad, coords[:, 0].max() + pad)
        ax.set_ylim(coords[:, 1].min() - pad, coords[:, 1].max() + pad)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])

    def _draw_natural(self, ax, colors) -> None:
        ax.set_title("Dominio natural (ξ, η)", color=colors["fg"],
                     fontsize=11, pad=4)
        sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        ax.plot(sq[:, 0], sq[:, 1], color="#4fa3ff", lw=1.8)
        ax.fill(sq[:, 0], sq[:, 1], color="#4fa3ff", alpha=0.10)
        ax.axhline(0, color=colors["grid"], lw=0.4)
        ax.axvline(0, color=colors["grid"], lw=0.4)

        corners = sq[:4]
        ax.scatter(corners[:, 0], corners[:, 1], s=60, c="#ff9f43",
                   edgecolors=colors["fg"], zorder=5)
        for i, (xi, eta) in enumerate(corners):
            ax.annotate(str(i + 1), (xi, eta),
                         textcoords="offset points", xytext=(6, 6),
                         color=colors["fg"], fontsize=9)

        # puntos de Gauss + etiquetas
        pts, _ = get_gauss_points_for_element(self._element_type)
        ax.scatter(pts[:, 0], pts[:, 1], s=90, marker="x", c="#e74c3c",
                   lw=2.0, zorder=6)
        for i, p in enumerate(pts):
            ax.annotate(f"pg{i + 1}", (p[0], p[1]),
                         textcoords="offset points", xytext=(6, 4),
                         color="#e74c3c", fontsize=8)

        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])

    def _sample_boundary(self, coords, n: int = 40) -> np.ndarray:
        N_fn, _ = get_shape_functions(self._element_type)
        ts = np.linspace(-1, 1, n)
        pts = []
        for eta in [-1, 1]:
            seq = ts if eta == -1 else ts[::-1]
            for xi in seq:
                pts.append(N_fn(xi, eta) @ coords[: self._n_nodes])
        for xi in [1, -1]:
            seq = ts if xi == 1 else ts[::-1]
            for eta in seq:
                pts.append(N_fn(xi, eta) @ coords[: self._n_nodes])
        return np.array(pts)

    def _mark(self, ax, x: float, y: float, is_gauss: bool) -> None:
        if is_gauss:
            ax.scatter([x], [y], s=220, facecolors="none",
                       edgecolors="#ffd54f", lw=2.4, zorder=9)
            ax.scatter([x], [y], s=55, c="#ffd54f", zorder=10)
        else:
            ax.scatter([x], [y], s=160, facecolors="none",
                       edgecolors="#e74c3c", lw=2.0, zorder=9)
            ax.scatter([x], [y], s=32, c="#e74c3c", zorder=10)

    def _compute_b(self, coords) -> np.ndarray:
        _, dN_fn = get_shape_functions(self._element_type)
        dN_nat = dN_fn(self._xi, self._eta)
        J, detJ, invJ = compute_jacobian(dN_nat, coords[: self._n_nodes])
        dN_phys = invJ @ dN_nat
        return compute_b_matrix(dN_phys)

    def _draw_b_matrix(self, coords, colors) -> None:
        try:
            B = self._compute_b(coords)
        except Exception as exc:
            ax = self.bot_panel.ax
            ax.clear()
            ax.set_xticks([]); ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.text(0.5, 0.5, f"Error calculando B: {exc}",
                     ha="center", va="center", color="#e74c3c",
                     transform=ax.transAxes, fontsize=10)
            self.bot_panel.redraw()
            return

        point_tag = (f"pg{self._gauss_index() + 1}"
                      if self._is_gauss and self._gauss_index() >= 0
                      else f"ξ={self._xi:+.3f}, η={self._eta:+.3f}")
        title = f"Matriz B  (3 × {2 * self._n_nodes})   en  {point_tag}"
        fs = 12 if self._n_nodes == 4 else 9
        render_matrix_latex(self.bot_panel.ax, B,
                            fmt="{:+.3g}", fontsize=fs,
                            color=colors["fg"], title=title,
                            prefix=r"\mathbf{B}=")
        self.bot_panel.redraw()

    def _gauss_index(self) -> int:
        pts, _ = get_gauss_points_for_element(self._element_type)
        d = np.hypot(pts[:, 0] - self._xi, pts[:, 1] - self._eta)
        k = int(np.argmin(d))
        return k if d[k] < 1e-6 else -1

    def _update_status(self, xy: np.ndarray) -> None:
        if not hasattr(self, "lbl_status"):
            return
        tag = self._sel_mode
        self.lbl_status.configure(text=(
            f"modo = {tag}\n"
            f"ξ  = {self._xi:+.4f}\n"
            f"η  = {self._eta:+.4f}\n"
            f"x  = {xy[0]:+.4f}\n"
            f"y  = {xy[1]:+.4f}"
        ))

    # ---------- teoría ----------
    def build_theory(self, doc: TheoryDoc, ctx: dict) -> None:
        doc.section("Matriz deformación-desplazamiento B")
        doc.para(
            r"Para un elemento 2D con desplazamientos $\mathbf{u}="
            r"[u_1,v_1,\dots,u_n,v_n]^T$, las deformaciones se obtienen como "
            r"$\boldsymbol{\varepsilon}=\mathbf{B}\,\mathbf{u}$, con"
        )
        doc.equation(
            r"\mathbf{B}=\begin{bmatrix}"
            r"\partial N_1/\partial x & 0 & \cdots & \partial N_n/\partial x & 0 \\"
            r"0 & \partial N_1/\partial y & \cdots & 0 & \partial N_n/\partial y \\"
            r"\partial N_1/\partial y & \partial N_1/\partial x & \cdots & "
            r"\partial N_n/\partial y & \partial N_n/\partial x"
            r"\end{bmatrix}"
        )
        doc.subsection("De ξ,η a x,y")
        doc.para(
            r"Las funciones de forma están definidas en coordenadas naturales. "
            r"La regla de la cadena convierte sus derivadas:"
        )
        doc.equation(
            r"\begin{bmatrix}\partial N_i/\partial x \\ "
            r"\partial N_i/\partial y\end{bmatrix}"
            r"=\mathbf{J}^{-1}"
            r"\begin{bmatrix}\partial N_i/\partial \xi \\ "
            r"\partial N_i/\partial \eta\end{bmatrix}"
        )
        doc.subsection("¿Por qué destacar los puntos de Gauss?")
        doc.para(
            r"La matriz de rigidez se obtiene por integración numérica; "
            r"$\mathbf{B}$ sólo se evalúa en los puntos de Gauss. Además "
            r"existe el fenómeno de \emph{superconvergencia}: las tensiones "
            r"calculadas en los puntos de Gauss tienen mayor precisión que en "
            r"cualquier otro punto del elemento."
        )
