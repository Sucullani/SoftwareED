"""
Módulo 6 — Vector de fuerzas equivalentes nodales

Convierte cargas distribuidas (arista / peso propio) en fuerzas puntuales
equivalentes en los nodos, mediante:

    Arista:      F_i = ∫  N_i · q(s)  ds   sobre la arista
    Peso propio: F_i = ∫∫ N_i · ρ·g  dA    sobre el elemento

Animación: flechitas distribuidas migran a los nodos con tamaño
proporcional a la contribución integrada.
"""

from __future__ import annotations

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from education.base_module import BaseEducationalModule
from education.components import (
    PlotPanel, ParamInput, TheoryDoc,
)
from education.components.plot_panel import _theme_colors

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian
from fem.gauss_quadrature import (
    GAUSS_POINTS_1D, get_gauss_points_for_element,
)


MODE_EDGE = "Carga de arista q(s)"
MODE_BODY = "Peso propio (gravedad)"


class EquivalentForcesModule(BaseEducationalModule):
    TITLE = "⑥ Vector de fuerzas equivalentes nodales"
    HAS_ANIMATION = True
    ANIMATION_DURATION_MS = 2500

    EDGES_Q4 = {
        "1-2": (0, 1, 0),   # (i, j, edge_eta = -1)  → variable xi
        "2-3": (1, 2, 0),   # edge_xi = +1 → variable eta
        "3-4": (2, 3, 0),
        "4-1": (3, 0, 0),
    }

    def __init__(self, parent, project, element_id):
        self._element_type = "Q4"
        self._n_nodes = 4
        if project and project.elements.get(element_id):
            et = project.elements[element_id].element_type
            if "Q9" in str(et) or "9 nodos" in str(et):
                self._element_type = "Q9"
                self._n_nodes = 9

        self._mode = MODE_EDGE
        self._edge = "1-2"
        self._q = 1.0e4         # N/m (ejemplo)
        self._rho = 7800.0      # kg/m³
        self._g = 9.81          # m/s²
        self._theta = -90.0     # dirección de g [grados] (—90 = apunta -y)

        self._t_anim = 0.0       # 0..1 animación
        self._F = np.zeros(2 * self._n_nodes)
        super().__init__(parent, project, element_id, width=1320, height=840)

    # ---------- controles ----------
    def build_controls(self, parent):
        ttk.Label(parent, text="Fuerzas equivalentes",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        ttk.Label(parent, wraplength=260, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "Las cargas distribuidas se reparten en los nodos "
                       "ponderándolas con las funciones de forma N_i. La "
                       "integración numérica se hace con cuadratura de "
                       "Gauss."
                   )).pack(anchor="w", pady=(0, 8))

        ttk.Separator(parent).pack(fill="x", pady=6)

        ttk.Label(parent, text="Tipo de carga",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.var_mode = tk.StringVar(value=self._mode)
        for m in (MODE_EDGE, MODE_BODY):
            ttk.Radiobutton(parent, text=m, variable=self.var_mode, value=m,
                             bootstyle="info-toolbutton",
                             command=self._on_mode_changed,
                             ).pack(fill="x", pady=2)

        ttk.Separator(parent).pack(fill="x", pady=6)

        # Parámetros de arista
        self.frm_edge = ttk.Frame(parent)
        self.frm_edge.pack(fill="x", pady=(0, 4))
        ttk.Label(self.frm_edge, text="Arista",
                   font=("Segoe UI", 9, "bold"),
                   foreground="#bbb").pack(anchor="w", pady=(0, 2))
        self.var_edge = tk.StringVar(value=self._edge)
        ttk.Combobox(self.frm_edge, textvariable=self.var_edge,
                      state="readonly",
                      values=list(self.EDGES_Q4.keys()),
                      bootstyle="info").pack(fill="x", pady=(0, 4))
        self.var_edge.trace_add("write", lambda *a: self._on_edge_changed())
        self.inp_q = ParamInput(
            self.frm_edge, label="q", value=self._q, unit="N/m",
            fmt="{:.3g}", on_change=self._on_q_changed,
        )
        self.inp_q.pack(fill="x", pady=(2, 4))

        # Parámetros de peso propio
        self.frm_body = ttk.Frame(parent)
        self.frm_body.pack(fill="x", pady=(0, 4))
        self.inp_rho = ParamInput(
            self.frm_body, label="ρ", value=self._rho, unit="kg/m³",
            fmt="{:.3g}", vmin=0.0,
            on_change=self._on_rho_changed,
        )
        self.inp_rho.pack(fill="x", pady=(2, 2))
        self.inp_g = ParamInput(
            self.frm_body, label="g", value=self._g, unit="m/s²",
            fmt="{:.3g}",
            on_change=self._on_g_changed,
        )
        self.inp_g.pack(fill="x", pady=(2, 2))

        ttk.Separator(parent).pack(fill="x", pady=6)

        ttk.Label(parent, text="Fuerzas nodales (N)",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(4, 4))
        self.lbl_forces = ttk.Label(parent, text="",
                                      font=("Consolas", 9),
                                      justify="left", anchor="w")
        self.lbl_forces.pack(anchor="w", pady=(0, 6))

        self._apply_mode_visibility()

    def _apply_mode_visibility(self) -> None:
        if self._mode == MODE_EDGE:
            self.frm_edge.pack(fill="x", pady=(0, 4))
            self.frm_body.pack_forget()
        else:
            self.frm_edge.pack_forget()
            self.frm_body.pack(fill="x", pady=(0, 4))

    # ---------- visualización ----------
    def build_visualization(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        self.left_panel = PlotPanel(
            parent, figsize=(5.8, 5.0), subplots=(1, 1),
            show_toolbar=False,
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.right_panel = PlotPanel(
            parent, figsize=(5.2, 5.0), subplots=(1, 1),
            show_toolbar=False,
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        self._recompute()
        self._redraw()

    # ---------- callbacks ----------
    def _on_mode_changed(self) -> None:
        self._mode = self.var_mode.get()
        self._apply_mode_visibility()
        self._recompute(); self._redraw()

    def _on_edge_changed(self) -> None:
        self._edge = self.var_edge.get()
        self._recompute(); self._redraw()

    def _on_q_changed(self, v: float) -> None:
        self._q = float(v); self._recompute(); self._redraw()

    def _on_rho_changed(self, v: float) -> None:
        self._rho = float(v); self._recompute(); self._redraw()

    def _on_g_changed(self, v: float) -> None:
        self._g = float(v); self._recompute(); self._redraw()

    # ---------- cálculo ----------
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

    def _recompute(self) -> None:
        coords = self._node_coords()[: self._n_nodes]
        if self._mode == MODE_EDGE:
            self._F = self._edge_force(coords)
        else:
            self._F = self._body_force(coords)

    def _edge_force(self, coords: np.ndarray) -> np.ndarray:
        """F_i = ∫ N_i · t(s) ds sobre la arista seleccionada.
        La carga actúa en la dirección normal exterior a la arista."""
        N_fn, dN_fn = get_shape_functions(self._element_type)
        F = np.zeros(2 * self._n_nodes)

        # Parametrización: xi o eta varían en [-1, 1]; el otro es fijo.
        edge_fix = self._edge_fix_param()  # ("eta", -1) por ejemplo
        var_name, fixed_val = edge_fix

        # Cuadratura 1D 2 puntos
        gp = GAUSS_POINTS_1D[2]
        for s, w in zip(gp["points"], gp["weights"]):
            if var_name == "xi":
                xi, eta = fixed_val, s
            else:
                xi, eta = s, fixed_val
            Ns = N_fn(xi, eta)
            # d/ds de (x,y) a lo largo de la arista (para el jacobiano 1D)
            dN_nat = dN_fn(xi, eta)
            if var_name == "xi":
                # varía eta: derivada respecto a eta
                dx_ds = dN_nat[1] @ coords[: self._n_nodes, 0]
                dy_ds = dN_nat[1] @ coords[: self._n_nodes, 1]
            else:
                dx_ds = dN_nat[0] @ coords[: self._n_nodes, 0]
                dy_ds = dN_nat[0] @ coords[: self._n_nodes, 1]
            ds_len = float(np.hypot(dx_ds, dy_ds))
            # Dirección normal exterior (rota tangente 90° hacia fuera)
            tx, ty = dx_ds / (ds_len or 1.0), dy_ds / (ds_len or 1.0)
            nx, ny = self._outward_normal(tx, ty, var_name, fixed_val)
            # contribución
            for i in range(self._n_nodes):
                F[2 * i] += Ns[i] * self._q * nx * ds_len * w
                F[2 * i + 1] += Ns[i] * self._q * ny * ds_len * w
        return F

    def _edge_fix_param(self):
        # Q4: las 4 aristas del cuadrado natural
        mapping = {
            "1-2": ("xi", -1.0),   # nodo 1 a 2: eta = -1 → varía xi
            "2-3": ("eta", 1.0),   # varía eta, xi = +1
            "3-4": ("xi", 1.0),    # eta = +1
            "4-1": ("eta", -1.0),  # xi = -1
        }
        # key corregida: 1-2 está en eta=-1 (varía xi)
        corrected = {
            "1-2": ("eta", -1.0),
            "2-3": ("xi", 1.0),
            "3-4": ("eta", 1.0),
            "4-1": ("xi", -1.0),
        }
        return corrected[self._edge]

    @staticmethod
    def _outward_normal(tx: float, ty: float, var_name: str,
                         fixed_val: float) -> tuple[float, float]:
        # Normal exterior al cuadrado: depende del signo del borde fijo.
        # Rotación 90° CW de tangente → (-ty, tx) o (ty, -tx)
        if var_name == "eta" and fixed_val < 0:   # abajo
            return ty, -tx
        if var_name == "eta" and fixed_val > 0:   # arriba
            return -ty, tx
        if var_name == "xi" and fixed_val > 0:    # derecha
            return ty, -tx
        # xi = -1 (izquierda)
        return -ty, tx

    def _body_force(self, coords: np.ndarray) -> np.ndarray:
        """F_i = ∫∫ N_i · b dA, b = ρ g · (cos θ, sin θ)."""
        N_fn, dN_fn = get_shape_functions(self._element_type)
        F = np.zeros(2 * self._n_nodes)
        theta_rad = np.deg2rad(self._theta)
        bx = self._rho * self._g * np.cos(theta_rad)
        by = self._rho * self._g * np.sin(theta_rad)

        pts, wts = get_gauss_points_for_element(self._element_type)
        for (xi, eta), w in zip(pts, wts):
            Ns = N_fn(xi, eta)
            _, detJ, _ = compute_jacobian(dN_fn(xi, eta),
                                            coords[: self._n_nodes])
            for i in range(self._n_nodes):
                F[2 * i] += Ns[i] * bx * detJ * w
                F[2 * i + 1] += Ns[i] * by * detJ * w
        return F

    # ---------- dibujo ----------
    def _redraw(self) -> None:
        colors = _theme_colors()
        coords = self._node_coords()[: self._n_nodes]

        # ---- izquierda: elemento + flechitas distribuidas ----
        ax = self.left_panel.ax
        ax.clear()
        self._style_ax(ax, colors)

        # contorno elemento
        idx = list(range(self._n_nodes if self._n_nodes == 4 else 4)) + [0]
        ax.plot(coords[idx, 0], coords[idx, 1], color="#4fa3ff", lw=1.8)
        ax.fill(coords[idx, 0], coords[idx, 1], color="#4fa3ff", alpha=0.10)
        ax.scatter(coords[:4, 0], coords[:4, 1], s=80, c="#ff9f43",
                    edgecolors=colors["fg"], zorder=5)
        for i in range(4):
            ax.annotate(str(i + 1), (coords[i, 0], coords[i, 1]),
                         textcoords="offset points", xytext=(7, 7),
                         color=colors["fg"], fontsize=9)

        if self._mode == MODE_EDGE:
            ax.set_title(f"Carga distribuida q en arista {self._edge}",
                          color=colors["fg"], fontsize=11)
            self._draw_edge_load_arrows(ax, coords)
        else:
            ax.set_title("Peso propio b = ρ g",
                          color=colors["fg"], fontsize=11)
            self._draw_body_force_arrows(ax, coords)

        # flechas nodales equivalentes
        self._draw_nodal_arrows(ax, coords)

        pad = 0.22 * max(
            float(np.ptp(coords[:, 0])) or 1.0,
            float(np.ptp(coords[:, 1])) or 1.0,
        )
        ax.set_xlim(coords[:, 0].min() - pad, coords[:, 0].max() + pad)
        ax.set_ylim(coords[:, 1].min() - pad, coords[:, 1].max() + pad)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        self.left_panel.redraw()

        # ---- derecha: barras F_elem ----
        self._draw_force_bars(colors)
        self._update_forces_label()

    @staticmethod
    def _style_ax(ax, colors) -> None:
        ax.set_facecolor(colors["bg"])
        for spine in ax.spines.values():
            spine.set_color("#45475a")

    def _draw_edge_load_arrows(self, ax, coords) -> None:
        # posición inicial: puntos sobre la arista
        edge_fix = self._edge_fix_param()
        var_name, fixed_val = edge_fix
        n_arrows = 7
        ss = np.linspace(-0.95, 0.95, n_arrows)
        N_fn, dN_fn = get_shape_functions(self._element_type)
        starts = []
        normals = []
        for s in ss:
            if var_name == "xi":
                xi, eta = fixed_val, s
            else:
                xi, eta = s, fixed_val
            p = N_fn(xi, eta) @ coords[: self._n_nodes]
            dN = dN_fn(xi, eta)
            if var_name == "xi":
                dx = dN[1] @ coords[: self._n_nodes, 0]
                dy = dN[1] @ coords[: self._n_nodes, 1]
            else:
                dx = dN[0] @ coords[: self._n_nodes, 0]
                dy = dN[0] @ coords[: self._n_nodes, 1]
            ln = float(np.hypot(dx, dy)) or 1.0
            tx, ty = dx / ln, dy / ln
            nx, ny = self._outward_normal(tx, ty, var_name, fixed_val)
            starts.append(p)
            normals.append((nx, ny))
        starts = np.array(starts)

        # tamaño de flechita proporcional a q (signo)
        pad = 0.2 * max(float(np.ptp(coords[:, 0])) or 1.0,
                         float(np.ptp(coords[:, 1])) or 1.0)
        arr_len = pad * np.sign(self._q) * 0.6

        # Destinos: nodos extremos de la arista (para la animación)
        end_nodes = self._edge_end_nodes()
        end_points = coords[end_nodes]

        for p, (nx, ny) in zip(starts, normals):
            # interpolación: de p hacia el extremo más cercano
            d0 = np.linalg.norm(p - end_points[0])
            d1 = np.linalg.norm(p - end_points[1])
            target = end_points[0] if d0 < d1 else end_points[1]
            curr = (1 - self._t_anim) * p + self._t_anim * target
            ax.annotate("", xy=(curr[0] - nx * arr_len,
                                 curr[1] - ny * arr_len),
                         xytext=(curr[0], curr[1]),
                         arrowprops=dict(arrowstyle="->",
                                          color="#ffd54f", lw=1.4))

    def _draw_body_force_arrows(self, ax, coords) -> None:
        # grid de flechitas en el interior del elemento
        N_fn, _ = get_shape_functions(self._element_type)
        samples = np.linspace(-0.8, 0.8, 4)
        theta_rad = np.deg2rad(self._theta)
        bx = np.cos(theta_rad); by = np.sin(theta_rad)
        pad = 0.18 * max(float(np.ptp(coords[:, 0])) or 1.0,
                          float(np.ptp(coords[:, 1])) or 1.0)
        arr_len = pad * 0.7

        starts = []
        for xi in samples:
            for eta in samples:
                starts.append(N_fn(xi, eta) @ coords[: self._n_nodes])
        starts = np.array(starts)
        # destinos: nodos más cercanos
        for p in starts:
            d = np.linalg.norm(coords[:4] - p, axis=1)
            target = coords[int(np.argmin(d))]
            curr = (1 - self._t_anim) * p + self._t_anim * target
            ax.annotate("", xy=(curr[0] + bx * arr_len,
                                 curr[1] + by * arr_len),
                         xytext=(curr[0], curr[1]),
                         arrowprops=dict(arrowstyle="->",
                                          color="#ffd54f", lw=1.2))

    def _draw_nodal_arrows(self, ax, coords) -> None:
        # flechas grandes en los 4 nodos esquineros, escaladas
        Fx = self._F[0::2]
        Fy = self._F[1::2]
        fmax = float(np.max(np.hypot(Fx, Fy)))
        if fmax < 1e-12:
            return
        pad = 0.25 * max(float(np.ptp(coords[:, 0])) or 1.0,
                          float(np.ptp(coords[:, 1])) or 1.0)
        for i in range(4):
            fx, fy = Fx[i], Fy[i]
            mag = np.hypot(fx, fy)
            if mag < 1e-12:
                continue
            L = pad * (mag / fmax)
            ux, uy = fx / mag, fy / mag
            alpha = 0.3 + 0.7 * self._t_anim
            ax.annotate(
                "",
                xy=(coords[i, 0] + ux * L, coords[i, 1] + uy * L),
                xytext=(coords[i, 0], coords[i, 1]),
                arrowprops=dict(arrowstyle="-|>,head_width=0.35",
                                 color="#e74c3c", lw=2.2, alpha=alpha),
            )

    def _edge_end_nodes(self) -> list[int]:
        return {
            "1-2": [0, 1],
            "2-3": [1, 2],
            "3-4": [2, 3],
            "4-1": [3, 0],
        }[self._edge]

    def _draw_force_bars(self, colors) -> None:
        ax = self.right_panel.ax
        ax.clear()
        self._style_ax(ax, colors)
        ax.tick_params(colors=colors["fg"])
        ax.grid(True, color=colors["grid"], lw=0.4, alpha=0.6)

        n = 2 * self._n_nodes
        labels = []
        for i in range(self._n_nodes):
            labels += [f"Fx{i + 1}", f"Fy{i + 1}"]
        pos = np.arange(n)
        vals = self._F
        colors_bars = ["#4fa3ff" if (i % 2 == 0) else "#ff9f43"
                       for i in range(n)]
        ax.barh(pos, vals, color=colors_bars, edgecolor=colors["fg"])
        ax.set_yticks(pos)
        ax.set_yticklabels(labels, color=colors["fg"], fontsize=9)
        ax.invert_yaxis()
        ax.axvline(0, color=colors["fg"], lw=0.5)
        ax.set_xlabel("Fuerza (N)", color=colors["fg"])
        ax.set_title("F_elem", color=colors["fg"], fontsize=11)
        for p, v in zip(pos, vals):
            ax.text(v, p, f" {v:+.2e}",
                     va="center",
                     ha="left" if v >= 0 else "right",
                     color=colors["fg"], fontsize=8)
        self.right_panel.redraw()

    def _update_forces_label(self) -> None:
        if not hasattr(self, "lbl_forces"):
            return
        lines = []
        for i in range(self._n_nodes):
            fx = self._F[2 * i]
            fy = self._F[2 * i + 1]
            lines.append(f"n{i + 1}: ({fx:+.3e}, {fy:+.3e})")
        self.lbl_forces.configure(text="\n".join(lines))

    # ---------- animación ----------
    def animate_step(self, t: float) -> None:
        self._t_anim = float(t)
        self._redraw()

    # ---------- teoría ----------
    def build_theory(self, doc: TheoryDoc, ctx: dict) -> None:
        doc.section("Vector de fuerzas equivalentes")
        doc.para(
            r"El Principio de Trabajos Virtuales exige que las fuerzas "
            r"distribuidas y su equivalente nodal produzcan el mismo trabajo "
            r"virtual. De ahí resultan las integrales:"
        )
        doc.subsection("Carga de arista")
        doc.equation(
            r"\mathbf{F}_i = \int_{\Gamma_e} N_i(\xi,\eta)\,\mathbf{t}(s)\,ds"
        )
        doc.para(
            r"Para una carga constante $q$ normal a una arista recta de "
            r"longitud $L$, el resultado exacto para Q4 es "
            r"$F_i^n = q L / 2$ en cada nodo extremo."
        )
        doc.subsection("Peso propio")
        doc.equation(
            r"\mathbf{F}_i = \iint_{\Omega_e} N_i(\xi,\eta)\,\rho\,\mathbf{g}"
            r"\,|\det\mathbf{J}|\,d\xi\,d\eta"
        )
        doc.para(
            r"Para un elemento Q4 de área $A$ con $\rho g$ constante, la "
            r"fuerza en cada nodo vale $F_i^n = \rho g A / 4$."
        )
