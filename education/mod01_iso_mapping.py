"""
Módulo 1 — Coordenadas naturales, Funciones de forma, Jacobiano

Interfaz: 4 paneles 2×2 sin ejes/ticks.
  (0,0) Elemento físico (x,y)      (0,1) Dominio natural (ξ,η)
  (1,0) Nᵢ(ξ,η) 3D o contornos     (1,1) det J(ξ,η) 3D o contornos

Click en cualquier panel → marcador sincronizado en los 4.
"""

from __future__ import annotations

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from education.base_module import BaseEducationalModule
from education.components import (
    FourPanel, ParamInput, TheoryDoc,
    iso_inverse_map, natural_to_physical,
)
from education.components.plot_panel import _theme_colors

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian


class IsoMappingModule(BaseEducationalModule):
    TITLE = "① Coordenadas, Funciones de forma y Jacobiano"
    HAS_ANIMATION = False

    VIZ_3D = "3D"
    VIZ_CONTOUR = "Contornos"

    def __init__(self, parent, project, element_id):
        # Determinar tipo y coordenadas del elemento
        self._element_type = "Q4"
        self._n_nodes = 4
        if project and project.elements.get(element_id):
            et = project.elements[element_id].element_type
            if "Q9" in str(et) or "9 nodos" in str(et):
                self._element_type = "Q9"
                self._n_nodes = 9

        self._viz_mode = self.VIZ_3D
        self._node_idx = 1        # 1-based: N_1..N_n
        self._grid = 40           # resolución de la grilla ξ,η
        self._sel_xi: float | None = None
        self._sel_eta: float | None = None

        super().__init__(parent, project, element_id, width=1280, height=820)

    # ---------- controles ----------
    def build_controls(self, parent):
        ttk.Label(parent, text="¿Por qué coordenadas naturales?",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        ttk.Label(parent, wraplength=250, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "Todo elemento distorsionado en (x,y) se mapea a un "
                       "cuadrado de referencia en (ξ,η) ∈ [-1,1]². Las "
                       "funciones de forma y la integración de Gauss se "
                       "definen UNA SOLA VEZ sobre ese cuadrado."
                   )).pack(anchor="w", pady=(0, 10))

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

        # Modo de visualización
        ttk.Label(parent, text="Visualización Nᵢ / det J",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.var_viz = tk.StringVar(value=self._viz_mode)
        ttk.Combobox(parent, textvariable=self.var_viz, state="readonly",
                      values=[self.VIZ_3D, self.VIZ_CONTOUR],
                      bootstyle="info").pack(fill="x", pady=(0, 8))
        self.var_viz.trace_add("write", lambda *a: self._on_viz_changed())

        # Selector de N_i
        ttk.Label(parent, text="Función Nᵢ a mostrar",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.var_ni = tk.StringVar(value=str(self._node_idx))
        self.cb_ni = ttk.Combobox(
            parent, textvariable=self.var_ni, state="readonly",
            values=[str(i) for i in range(1, self._n_nodes + 1)],
            bootstyle="info",
        )
        self.cb_ni.pack(fill="x", pady=(0, 8))
        self.var_ni.trace_add("write", lambda *a: self._on_ni_changed())

        ttk.Separator(parent).pack(fill="x", pady=8)

        ttk.Label(parent, text="Punto seleccionado",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.lbl_point = ttk.Label(parent, text="(sin selección)",
                                     font=("Consolas", 9),
                                     justify="left", anchor="w")
        self.lbl_point.pack(anchor="w", pady=(0, 6))

        ttk.Label(parent, wraplength=250, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "Haga click en el elemento físico o en el cuadrado "
                       "natural. El marcador aparece en los 4 paneles."
                   )).pack(anchor="w", pady=(4, 0))

    # ---------- visualización ----------
    def build_visualization(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.fp = FourPanel(
            parent,
            figsize=(10.5, 8.0),
            projections=[None, None, "3d", "3d"],
            hide_ticks=True,
            show_toolbar=False,
        )
        self.fp.grid(row=0, column=0, sticky="nsew")
        self.fp.bind_click(self._on_click)
        self._redraw()

    # ---------- callbacks ----------
    def _on_element_changed(self) -> None:
        et = self.var_elem.get()
        self._element_type = et
        self._n_nodes = 4 if et == "Q4" else 9
        self._node_idx = min(self._node_idx, self._n_nodes)
        self.cb_ni.configure(values=[str(i) for i in range(1, self._n_nodes + 1)])
        self.var_ni.set(str(self._node_idx))
        self._redraw()

    def _on_viz_changed(self) -> None:
        self._viz_mode = self.var_viz.get()
        self._rebuild_3d_panels()

    def _on_ni_changed(self) -> None:
        try:
            self._node_idx = int(self.var_ni.get())
        except ValueError:
            return
        self._redraw()

    def _on_click(self, event) -> None:
        if event.inaxes is None or event.xdata is None:
            return
        # Panel físico
        if event.inaxes is self.fp.ax_at(0, 0):
            result = iso_inverse_map(event.xdata, event.ydata,
                                       self._node_coords(),
                                       self._element_type)
            if result is None:
                return
            self._sel_xi, self._sel_eta = result
            self._redraw()
            return
        # Panel natural
        if event.inaxes is self.fp.ax_at(0, 1):
            xi = float(event.xdata)
            eta = float(event.ydata)
            if abs(xi) > 1.05 or abs(eta) > 1.05:
                return
            self._sel_xi, self._sel_eta = xi, eta
            self._redraw()
            return
        # Paneles 3D (N_i o J) — matplotlib no da xdata útil en 3D;
        # se ignora para evitar clicks inesperados.

    # ---------- dibujo ----------
    def _node_coords(self) -> np.ndarray:
        if self.project and self.element:
            coords = np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in self.element.node_ids
            ], dtype=float)
            return coords
        # fallback demo
        return np.array(
            [[0, 0], [4, 0.2], [4.2, 3.2], [0.1, 3.0]],
            dtype=float,
        )

    def _redraw(self) -> None:
        colors = _theme_colors()
        self.fp.clear()

        coords = self._node_coords()[: self._n_nodes]
        N_fn, dN_fn = get_shape_functions(self._element_type)

        # -- (0,0) elemento físico --
        ax_phys = self.fp.ax_at(0, 0)
        self._draw_element_physical(ax_phys, coords, colors)

        # -- (0,1) dominio natural --
        ax_nat = self.fp.ax_at(0, 1)
        self._draw_element_natural(ax_nat, colors)

        # -- (1,0) N_i  y  (1,1) det J --
        self._draw_surface_ni(self.fp.ax_at(1, 0), N_fn, colors)
        self._draw_surface_j(self.fp.ax_at(1, 1), dN_fn, coords, colors)

        # Marcador sincronizado
        if self._sel_xi is not None:
            xy = natural_to_physical(self._sel_xi, self._sel_eta,
                                       coords, self._element_type)
            self._mark_point(ax_phys, xy[0], xy[1])
            self._mark_point(ax_nat, self._sel_xi, self._sel_eta)
            self._mark_on_surfaces(N_fn, dN_fn, coords)
            self._update_point_label(xy)

        self.fp.redraw()

    def _draw_element_physical(self, ax, coords, colors) -> None:
        ax.set_title("Elemento físico (x, y)", color=colors["fg"],
                     fontsize=11, pad=4)
        # borde por muestreo del mapeo iso
        boundary = self._sample_boundary(coords)
        ax.plot(boundary[:, 0], boundary[:, 1],
                color="#4fa3ff", lw=1.8)
        ax.fill(boundary[:, 0], boundary[:, 1],
                color="#4fa3ff", alpha=0.10)
        # nodos esquineros
        corners = coords[:4]
        ax.scatter(corners[:, 0], corners[:, 1], s=70,
                   c="#ff9f43", edgecolors=colors["fg"], zorder=5)
        for i, (x, y) in enumerate(corners):
            ax.annotate(str(i + 1), (x, y),
                         textcoords="offset points", xytext=(6, 6),
                         color=colors["fg"], fontsize=9)
        # nodos intermedios Q9
        if self._element_type == "Q9" and len(coords) >= 9:
            ax.scatter(coords[4:, 0], coords[4:, 1], s=40,
                       c="#ffd470", edgecolors=colors["fg"], zorder=4)
        # márgenes
        pad = 0.15 * max(
            float(np.ptp(coords[:, 0])) or 1.0,
            float(np.ptp(coords[:, 1])) or 1.0,
        )
        ax.set_xlim(coords[:, 0].min() - pad, coords[:, 0].max() + pad)
        ax.set_ylim(coords[:, 1].min() - pad, coords[:, 1].max() + pad)
        ax.set_aspect("equal")

    def _draw_element_natural(self, ax, colors) -> None:
        ax.set_title("Dominio natural (ξ, η) ∈ [-1, 1]²",
                     color=colors["fg"], fontsize=11, pad=4)
        sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        ax.plot(sq[:, 0], sq[:, 1], color="#4fa3ff", lw=1.8)
        ax.fill(sq[:, 0], sq[:, 1], color="#4fa3ff", alpha=0.10)
        ax.axhline(0, color=colors["grid"], lw=0.4)
        ax.axvline(0, color=colors["grid"], lw=0.4)
        # esquinas
        corners = sq[:4]
        ax.scatter(corners[:, 0], corners[:, 1], s=60, c="#ff9f43",
                   edgecolors=colors["fg"], zorder=5)
        for i, (xi, eta) in enumerate(corners):
            ax.annotate(str(i + 1), (xi, eta),
                         textcoords="offset points", xytext=(6, 6),
                         color=colors["fg"], fontsize=9)
        # rótulos ξ/η
        ax.annotate("ξ=-1", (-1, 0), color="#aaa", fontsize=8,
                     textcoords="offset points", xytext=(-28, 0))
        ax.annotate("ξ=+1", (1, 0), color="#aaa", fontsize=8,
                     textcoords="offset points", xytext=(6, 0))
        ax.annotate("η=-1", (0, -1), color="#aaa", fontsize=8,
                     textcoords="offset points", xytext=(0, -14))
        ax.annotate("η=+1", (0, 1), color="#aaa", fontsize=8,
                     textcoords="offset points", xytext=(0, 8))

        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)
        ax.set_aspect("equal")

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

    def _xi_eta_grid(self):
        xi = np.linspace(-1, 1, self._grid)
        eta = np.linspace(-1, 1, self._grid)
        XI, ET = np.meshgrid(xi, eta)
        return XI, ET

    def _draw_surface_ni(self, ax, N_fn, colors) -> None:
        XI, ET = self._xi_eta_grid()
        Z = np.zeros_like(XI)
        for i in range(self._grid):
            for j in range(self._grid):
                Z[i, j] = N_fn(XI[i, j], ET[i, j])[self._node_idx - 1]

        title = f"Nᵢ(ξ,η)  —  i = {self._node_idx}"
        if self._viz_mode == self.VIZ_3D:
            self._surface_3d(ax, XI, ET, Z, title, colors, cmap="viridis")
        else:
            self._contour_2d(ax, XI, ET, Z, title, colors, cmap="viridis")

    def _draw_surface_j(self, ax, dN_fn, coords, colors) -> None:
        XI, ET = self._xi_eta_grid()
        Z = np.zeros_like(XI)
        for i in range(self._grid):
            for j in range(self._grid):
                try:
                    _, detJ, _ = compute_jacobian(
                        dN_fn(XI[i, j], ET[i, j]), coords[: self._n_nodes]
                    )
                except Exception:
                    detJ = 0.0
                Z[i, j] = detJ

        title = "det J(ξ,η)"
        if self._viz_mode == self.VIZ_3D:
            self._surface_3d(ax, XI, ET, Z, title, colors, cmap="plasma")
        else:
            self._contour_2d(ax, XI, ET, Z, title, colors, cmap="plasma")

    def _surface_3d(self, ax, XI, ET, Z, title, colors, cmap) -> None:
        ax.set_title(title, color=colors["fg"], fontsize=11, pad=4)
        ax.set_facecolor(colors["bg"])
        ax.plot_surface(XI, ET, Z, cmap=cmap, edgecolor="none",
                         antialiased=True, alpha=0.95)
        try:
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_zticklabels([])
            ax.xaxis.pane.set_edgecolor(colors["grid"])
            ax.yaxis.pane.set_edgecolor(colors["grid"])
            ax.zaxis.pane.set_edgecolor(colors["grid"])
            ax.xaxis.pane.fill = False
            ax.yaxis.pane.fill = False
            ax.zaxis.pane.fill = False
        except Exception:
            pass

    def _contour_2d(self, ax, XI, ET, Z, title, colors, cmap) -> None:
        # matplotlib mezcla mal contour sobre un 3D axes existente; lo
        # recreamos como axes 2D nuevo en la misma posición.
        fig = ax.figure
        pos = ax.get_position()
        fig.delaxes(ax)
        new_ax = fig.add_axes([pos.x0, pos.y0, pos.width, pos.height])
        # reemplazar en self.fp.axes para futuras actualizaciones
        for k, a in enumerate(self.fp.axes):
            if a is ax:
                self.fp.axes[k] = new_ax
                break
        new_ax.set_facecolor(colors["bg"])
        new_ax.set_title(title, color=colors["fg"], fontsize=11, pad=4)
        cs = new_ax.contourf(XI, ET, Z, levels=14, cmap=cmap)
        new_ax.contour(XI, ET, Z, levels=14, colors="#222233",
                        linewidths=0.4, alpha=0.5)
        new_ax.set_xticks([])
        new_ax.set_yticks([])
        for spine in new_ax.spines.values():
            spine.set_color("#45475a")
            spine.set_linewidth(1.2)
        new_ax.set_aspect("equal")

    def _rebuild_3d_panels(self) -> None:
        """Cuando el usuario cambia entre 3D y Contornos, los ejes 1,0/1,1
        deben recrearse con la proyección adecuada. Solución: reconstruir
        todo el FourPanel."""
        target_projs = [None, None,
                        "3d" if self._viz_mode == self.VIZ_3D else None,
                        "3d" if self._viz_mode == self.VIZ_3D else None]
        # destruir y reconstruir el widget
        parent = self.fp.master
        self.fp.destroy()
        self.fp = FourPanel(
            parent, figsize=(10.5, 8.0),
            projections=target_projs, hide_ticks=True, show_toolbar=False,
        )
        self.fp.grid(row=0, column=0, sticky="nsew")
        self.fp.bind_click(self._on_click)
        self._redraw()

    def _mark_point(self, ax, x: float, y: float) -> None:
        ax.scatter([x], [y], s=160, facecolors="none",
                   edgecolors="#e74c3c", lw=2.0, zorder=9)
        ax.scatter([x], [y], s=22, c="#e74c3c", zorder=10)

    def _mark_on_surfaces(self, N_fn, dN_fn, coords) -> None:
        if self._sel_xi is None:
            return
        xi, eta = self._sel_xi, self._sel_eta
        # N_i
        z_ni = N_fn(xi, eta)[self._node_idx - 1]
        ax_ni = self.fp.ax_at(1, 0)
        self._scatter_on_panel(ax_ni, xi, eta, z_ni)
        # det J
        try:
            _, detJ, _ = compute_jacobian(dN_fn(xi, eta), coords[: self._n_nodes])
        except Exception:
            detJ = 0.0
        ax_j = self.fp.ax_at(1, 1)
        self._scatter_on_panel(ax_j, xi, eta, detJ)

    def _scatter_on_panel(self, ax, xi: float, eta: float, z: float) -> None:
        if hasattr(ax, "zaxis"):
            try:
                ax.scatter([xi], [eta], [z], s=60, c="#e74c3c",
                           edgecolors="white", depthshade=False, zorder=10)
            except Exception:
                pass
        else:
            ax.scatter([xi], [eta], s=120, facecolors="none",
                       edgecolors="#e74c3c", lw=2.0, zorder=9)

    def _update_point_label(self, xy: np.ndarray) -> None:
        if not hasattr(self, "lbl_point"):
            return
        self.lbl_point.configure(text=(
            f"ξ  = {self._sel_xi:+.4f}\n"
            f"η  = {self._sel_eta:+.4f}\n"
            f"x  = {xy[0]:+.4f}\n"
            f"y  = {xy[1]:+.4f}"
        ))

    # ---------- teoría ----------
    def build_theory(self, doc: TheoryDoc, ctx: dict) -> None:
        doc.section("Mapeo isoparamétrico")
        doc.para(
            r"Un elemento físico con coordenadas $(x,y)$ se mapea al "
            r"cuadrado natural $(\xi,\eta)\in[-1,1]^2$ mediante las "
            r"mismas funciones de forma usadas para los desplazamientos:"
        )
        doc.equation(
            r"x(\xi,\eta) = \sum_i N_i(\xi,\eta)\, x_i, \quad "
            r"y(\xi,\eta) = \sum_i N_i(\xi,\eta)\, y_i"
        )

        doc.subsection("Jacobiano")
        doc.equation(
            r"\mathbf{J} = \begin{bmatrix} "
            r"\partial x/\partial \xi & \partial y/\partial \xi \\ "
            r"\partial x/\partial \eta & \partial y/\partial \eta "
            r"\end{bmatrix}"
        )
        doc.para(
            r"El signo de $\det\mathbf{J}$ indica orientación; su valor "
            r"absoluto es el factor de cambio de área entre el elemento "
            r"físico y el cuadrado natural. Si se anula o cambia de signo "
            r"el elemento es inválido."
        )
