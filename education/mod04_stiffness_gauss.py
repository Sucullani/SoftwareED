"""
Módulo 4 — Matriz de rigidez e integración de Gauss

Notebook con dos sub-pestañas:

    Tab 1 — Integrando simbólico
        Expresa K_ij(ξ,η) = [B^T D B det(J) t]_{ij} en forma simbólica y
        muestra la expresión en LaTeX + la superficie 3D |K_ij| sobre el
        cuadrado natural. Deja en evidencia que la integración analítica
        no es práctica y motiva la cuadratura.

    Tab 2 — Integración de Gauss
        Animación paso a paso de la suma k_e = Σ w_ij · B^T D B · det(J) · t.
        Compara órdenes de cuadratura (1×1, 2×2, 3×3).
"""

from __future__ import annotations

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk
import sympy as sp

from education.base_module import BaseEducationalModule
from education.components import (
    PlotPanel, TheoryDoc, render_expression_latex,
)
from education.components.plot_panel import _theme_colors

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix
from fem.gauss_quadrature import get_gauss_points_2d
from config.settings import ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN


# ───────────────────────── CAPA SIMBÓLICA ─────────────────────────

class SymbolicIntegrandQ4:
    """Construcción simbólica de [B^T D B |det J| t] para Q4.

    Migrado desde ModuloIntegrandoQ4.py, sin la capa de renderizado pylatex.
    """

    def __init__(self, E=225000.0, nu=0.2, t=0.8, coords=None):
        self.E = E
        self.nu = nu
        self.t = t
        self.coords = coords if coords is not None else [
            [0, 0], [5, 0], [7, 4], [2, 3]
        ]
        self.xi, self.eta = sp.symbols(r"\xi \eta", real=True)

    def _shape_functions(self):
        xi, eta = self.xi, self.eta
        return [
            sp.Rational(1, 4) * (1 - xi) * (1 - eta),
            sp.Rational(1, 4) * (1 + xi) * (1 - eta),
            sp.Rational(1, 4) * (1 + xi) * (1 + eta),
            sp.Rational(1, 4) * (1 - xi) * (1 + eta),
        ]

    def _jacobian(self, dN_dxi, dN_deta):
        c = self.coords
        dx_dxi = sum(dN_dxi[i] * c[i][0] for i in range(4))
        dy_dxi = sum(dN_dxi[i] * c[i][1] for i in range(4))
        dx_deta = sum(dN_deta[i] * c[i][0] for i in range(4))
        dy_deta = sum(dN_deta[i] * c[i][1] for i in range(4))
        return sp.Matrix([[dx_dxi, dy_dxi], [dx_deta, dy_deta]])

    def _b(self, dN_dxi, dN_deta, J):
        detJ = J.det()
        i11 = J[1, 1] / detJ
        i12 = -J[0, 1] / detJ
        i21 = -J[1, 0] / detJ
        i22 = J[0, 0] / detJ
        B_parts = []
        for i in range(4):
            dNx = i11 * dN_dxi[i] + i12 * dN_deta[i]
            dNy = i21 * dN_dxi[i] + i22 * dN_deta[i]
            B_parts.append(sp.Matrix([[dNx, 0], [0, dNy], [dNy, dNx]]))
        return sp.Matrix.hstack(*B_parts), detJ

    def _d(self, analysis):
        E = sp.Rational(self.E).limit_denominator(1_000_000)
        nu = sp.Rational(self.nu).limit_denominator(1000)
        if analysis == ANALYSIS_PLANE_STRESS:
            f = E / (1 - nu ** 2)
            return f * sp.Matrix([
                [1, nu, 0],
                [nu, 1, 0],
                [0, 0, (1 - nu) / 2],
            ])
        f = E / ((1 + nu) * (1 - 2 * nu))
        return f * sp.Matrix([
            [1 - nu, nu, 0],
            [nu, 1 - nu, 0],
            [0, 0, (1 - 2 * nu) / 2],
        ])

    def integrand_entry(self, i: int, j: int, analysis: str):
        """Devuelve K_ij(ξ,η) como expresión simbólica simplificada."""
        N = self._shape_functions()
        dN_dxi = [sp.diff(Ni, self.xi) for Ni in N]
        dN_deta = [sp.diff(Ni, self.eta) for Ni in N]
        J = self._jacobian(dN_dxi, dN_deta)
        B, detJ = self._b(dN_dxi, dN_deta, J)
        D = self._d(analysis)
        t = sp.Rational(self.t).limit_denominator(1000)
        expr = (B.T * D * B)[i, j] * detJ * t
        return sp.cancel(expr)


# ───────────────────────── MÓDULO ─────────────────────────

class StiffnessGaussModule(BaseEducationalModule):
    TITLE = "④ Rigidez del elemento  —  integrando + cuadratura de Gauss"
    HAS_ANIMATION = False

    def __init__(self, parent, project, element_id):
        self._element_type = "Q4"
        self._n_nodes = 4
        if project and project.elements.get(element_id):
            et = project.elements[element_id].element_type
            if "Q9" in str(et) or "9 nodos" in str(et):
                self._element_type = "Q9"
                self._n_nodes = 9

        self._E = 225_000.0
        self._nu = 0.2
        self._t = 0.8
        self._analysis = ANALYSIS_PLANE_STRESS
        self._order = 2
        self._i = 1
        self._j = 1
        self._current_gp = 0
        self._k_acum: np.ndarray | None = None
        super().__init__(parent, project, element_id, width=1380, height=880)

    # ---------- controles ----------
    def build_controls(self, parent):
        ttk.Label(parent, text="Rigidez del elemento",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        ttk.Label(parent, wraplength=260, justify="left",
                   font=("Segoe UI", 9), foreground="#aaa",
                   text=(
                       "kₑ = ∫∫ Bᵀ D B |det J| t dξ dη\n"
                       "Se obtiene con cuadratura de Gauss."
                   )).pack(anchor="w", pady=(0, 8))

        ttk.Separator(parent).pack(fill="x", pady=6)

        # Parámetros
        from education.components import ParamInput

        self.inp_E = ParamInput(parent, "E", self._E, unit="",
                                 fmt="{:.0f}",
                                 on_change=self._set_E)
        self.inp_E.pack(fill="x", pady=2)

        self.inp_nu = ParamInput(parent, "ν", self._nu, unit="",
                                  fmt="{:.3f}", vmin=-0.99, vmax=0.499,
                                  on_change=self._set_nu)
        self.inp_nu.pack(fill="x", pady=2)

        self.inp_t = ParamInput(parent, "t", self._t, unit="",
                                 fmt="{:.3f}", vmin=1e-6,
                                 on_change=self._set_t)
        self.inp_t.pack(fill="x", pady=2)

        ttk.Label(parent, text="Caso plano",
                   font=("Segoe UI", 9, "bold"),
                   foreground="#bbb").pack(anchor="w", pady=(6, 2))
        self.var_case = tk.StringVar(value=self._analysis)
        ttk.Combobox(parent, textvariable=self.var_case, state="readonly",
                      values=[ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN],
                      bootstyle="info").pack(fill="x", pady=(0, 6))
        self.var_case.trace_add("write", lambda *a: self._set_case())

        ttk.Separator(parent).pack(fill="x", pady=6)

        # Selección de (i,j) para tab 1
        ttk.Label(parent, text="Entrada K_{ij}(ξ,η)",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        row = ttk.Frame(parent); row.pack(fill="x", pady=(0, 4))
        ttk.Label(row, text="i").pack(side="left")
        self.var_i = tk.StringVar(value=str(self._i))
        self.sp_i = ttk.Spinbox(row, from_=1, to=2 * self._n_nodes,
                                 textvariable=self.var_i, width=4,
                                 command=self._on_ij_changed)
        self.sp_i.pack(side="left", padx=4)
        ttk.Label(row, text="j").pack(side="left", padx=(10, 0))
        self.var_j = tk.StringVar(value=str(self._j))
        self.sp_j = ttk.Spinbox(row, from_=1, to=2 * self._n_nodes,
                                 textvariable=self.var_j, width=4,
                                 command=self._on_ij_changed)
        self.sp_j.pack(side="left", padx=4)

        ttk.Button(parent, text="⚙ Recalcular expresión simbólica",
                    bootstyle="info-outline",
                    command=self._rebuild_symbolic).pack(fill="x", pady=(4, 8))

        ttk.Separator(parent).pack(fill="x", pady=6)

        # Orden de cuadratura para tab 2
        ttk.Label(parent, text="Orden de cuadratura",
                   font=("Segoe UI", 10, "bold"),
                   bootstyle="info").pack(anchor="w", pady=(0, 4))
        self.var_order = tk.StringVar(value="2")
        ttk.Combobox(parent, textvariable=self.var_order, state="readonly",
                      values=["1", "2", "3"],
                      bootstyle="info").pack(fill="x", pady=(0, 6))
        self.var_order.trace_add("write", lambda *a: self._on_order_changed())

        row2 = ttk.Frame(parent); row2.pack(fill="x", pady=(4, 4))
        ttk.Button(row2, text="◀", width=3, bootstyle="secondary-outline",
                    command=self._prev_gp).pack(side="left", padx=2)
        ttk.Button(row2, text="▶ Avanzar PG",
                    bootstyle="success", command=self._next_gp,
                    ).pack(side="left", padx=2, fill="x", expand=True)
        ttk.Button(row2, text="↺", width=3, bootstyle="warning-outline",
                    command=self._reset_acum).pack(side="left", padx=2)

        self.lbl_gp = ttk.Label(parent, text="", font=("Consolas", 9))
        self.lbl_gp.pack(anchor="w", pady=(4, 0))

    # ---------- visualización ----------
    def build_visualization(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.nb = ttk.Notebook(parent, bootstyle="info")
        self.nb.grid(row=0, column=0, sticky="nsew")

        self.tab_sym = ttk.Frame(self.nb)
        self.tab_gauss = ttk.Frame(self.nb)
        self.nb.add(self.tab_sym, text="Integrando simbólico")
        self.nb.add(self.tab_gauss, text="Integración de Gauss")

        self._build_tab_symbolic(self.tab_sym)
        self._build_tab_gauss(self.tab_gauss)

    def _build_tab_symbolic(self, tab):
        tab.rowconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        tab.columnconfigure(0, weight=1)

        self.panel_expr = PlotPanel(
            tab, figsize=(10.5, 3.2), subplots=(1, 1),
            show_toolbar=False,
        )
        self.panel_expr.grid(row=0, column=0, sticky="nsew")

        self.panel_surf = PlotPanel(
            tab, figsize=(10.5, 4.0), subplots=(1, 1),
            projection="3d", show_toolbar=False,
        )
        self.panel_surf.grid(row=1, column=0, sticky="nsew", pady=(4, 0))

        self._rebuild_symbolic()

    def _build_tab_gauss(self, tab):
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        self.panel_gauss = PlotPanel(
            tab, figsize=(10.5, 7.0), subplots=(2, 2),
            show_toolbar=False,
        )
        self.panel_gauss.grid(row=0, column=0, sticky="nsew")
        self._reset_acum()

    # ---------- callbacks parametros ----------
    def _set_E(self, v: float) -> None: self._E = float(v)
    def _set_nu(self, v: float) -> None: self._nu = float(v)
    def _set_t(self, v: float) -> None: self._t = float(v)
    def _set_case(self) -> None: self._analysis = self.var_case.get()

    def _on_ij_changed(self) -> None:
        try:
            self._i = max(1, min(2 * self._n_nodes, int(self.var_i.get())))
            self._j = max(1, min(2 * self._n_nodes, int(self.var_j.get())))
        except ValueError:
            return
        self._rebuild_symbolic()

    def _on_order_changed(self) -> None:
        try:
            self._order = int(self.var_order.get())
        except ValueError:
            return
        self._reset_acum()

    # ---------- SYMBOLIC TAB ----------
    def _rebuild_symbolic(self) -> None:
        coords = self._node_coords().tolist()
        sym = SymbolicIntegrandQ4(self._E, self._nu, self._t, coords)
        try:
            expr = sym.integrand_entry(self._i - 1, self._j - 1, self._analysis)
        except Exception as exc:
            self._show_expr_error(str(exc))
            return

        colors = _theme_colors()
        expr_latex = sp.latex(expr)
        # cabecera legible
        title_latex = rf"K_{{{self._i},{self._j}}}(\xi,\eta)\;=\;"
        # truncar para que mathtext no explote
        full = title_latex + self._truncate_latex(expr_latex, max_chars=450)
        render_expression_latex(
            self.panel_expr.ax, full, fontsize=11, color=colors["fg"],
            title=f"Integrando (i={self._i}, j={self._j})  —  {self._analysis}",
        )
        self.panel_expr.redraw()

        # superficie 3D
        self._draw_surface_kij(expr, sym)

    @staticmethod
    def _truncate_latex(s: str, max_chars: int = 450) -> str:
        if len(s) <= max_chars:
            return s
        return s[: max_chars - 12] + r"\;\ldots"

    def _draw_surface_kij(self, expr, sym: SymbolicIntegrandQ4) -> None:
        colors = _theme_colors()
        ax = self.panel_surf.ax
        ax.clear()
        ax.set_facecolor(colors["bg"])
        f = sp.lambdify((sym.xi, sym.eta), expr, "numpy")
        grid = 35
        xi = np.linspace(-0.999, 0.999, grid)
        eta = np.linspace(-0.999, 0.999, grid)
        XI, ET = np.meshgrid(xi, eta)
        try:
            Z = np.asarray(f(XI, ET), dtype=float)
        except Exception:
            # evaluar punto a punto si hay problemas
            Z = np.zeros_like(XI)
            for r in range(grid):
                for c in range(grid):
                    try:
                        Z[r, c] = float(f(XI[r, c], ET[r, c]))
                    except Exception:
                        Z[r, c] = np.nan
        Zabs = np.abs(Z)
        ax.plot_surface(XI, ET, Zabs, cmap="plasma", edgecolor="none",
                         alpha=0.9)
        ax.set_title(f"|K_{{{self._i},{self._j}}}(ξ,η)|   superficie",
                      color=colors["fg"], fontsize=11)
        try:
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_zticklabels([])
        except Exception:
            pass
        self.panel_surf.redraw()

    def _show_expr_error(self, msg: str) -> None:
        colors = _theme_colors()
        ax = self.panel_expr.ax
        ax.clear()
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.text(0.5, 0.5, f"No se pudo construir K_ij:\n{msg}",
                 ha="center", va="center", color="#e74c3c",
                 fontsize=10, transform=ax.transAxes)
        self.panel_expr.redraw()

    # ---------- GAUSS TAB ----------
    def _node_coords(self) -> np.ndarray:
        if self.project and self.element:
            return np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in self.element.node_ids
            ], dtype=float)
        return np.array(
            [[0, 0], [5, 0], [7, 4], [2, 3]],
            dtype=float,
        )

    def _reset_acum(self) -> None:
        n = 2 * self._n_nodes
        self._k_acum = np.zeros((n, n))
        self._current_gp = 0
        self._redraw_gauss()

    def _next_gp(self) -> None:
        coords = self._node_coords()[: self._n_nodes]
        pts, wts = get_gauss_points_2d(self._order)
        if self._current_gp >= len(pts):
            return
        D = constitutive_matrix(self._E, self._nu, self._analysis)
        _, dN_fn = get_shape_functions(self._element_type)
        xi, eta = pts[self._current_gp]
        w = wts[self._current_gp]
        dN_nat = dN_fn(xi, eta)
        J, detJ, invJ = compute_jacobian(dN_nat, coords)
        dN_phys = compute_dN_physical(dN_nat, invJ)
        B = compute_b_matrix(dN_phys)
        ke_contrib = B.T @ D @ B * abs(detJ) * self._t * w
        if self._k_acum is None:
            self._reset_acum()
        self._k_acum = self._k_acum + ke_contrib
        self._current_gp += 1
        self._redraw_gauss(last_contrib=ke_contrib)

    def _prev_gp(self) -> None:
        # Retrocede un paso reconstruyendo desde cero
        if self._current_gp <= 0:
            return
        target = self._current_gp - 1
        self._reset_acum()
        for _ in range(target):
            self._next_gp()

    def _redraw_gauss(self, last_contrib: np.ndarray | None = None) -> None:
        if not hasattr(self, "panel_gauss"):
            return
        colors = _theme_colors()
        self.panel_gauss.clear()
        axes = self.panel_gauss.axes
        pts, wts = get_gauss_points_2d(self._order)

        # (0,0) cuadrado natural + pg activo
        ax = axes[0]
        sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        ax.plot(sq[:, 0], sq[:, 1], color="#4fa3ff", lw=1.6)
        ax.fill(sq[:, 0], sq[:, 1], color="#4fa3ff", alpha=0.08)
        ax.scatter(pts[:, 0], pts[:, 1], s=70, c="#888", marker="x", lw=1.5)
        if 0 < self._current_gp <= len(pts):
            p = pts[self._current_gp - 1]
            ax.scatter([p[0]], [p[1]], s=160, facecolors="none",
                        edgecolors="#ffd54f", lw=2.4)
            ax.scatter([p[0]], [p[1]], s=55, c="#ffd54f", zorder=5)
        ax.set_xlim(-1.4, 1.4); ax.set_ylim(-1.4, 1.4); ax.set_aspect("equal")
        ax.set_title(f"Puntos de Gauss  —  {self._order}×{self._order}",
                      color=colors["fg"], fontsize=10)

        # (0,1) contribución en el pg actual
        ax = axes[1]
        if last_contrib is not None:
            self._heatmap(ax, last_contrib,
                           f"Contribución en pg{self._current_gp}", colors)
        else:
            ax.text(0.5, 0.5, "Presione ▶ Avanzar PG",
                     ha="center", va="center", color=colors["fg"],
                     transform=ax.transAxes, fontsize=11)
            ax.set_xticks([]); ax.set_yticks([])

        # (1,0) K_acum
        ax = axes[2]
        if self._k_acum is not None and np.any(self._k_acum):
            self._heatmap(ax, self._k_acum,
                           f"K_e acumulado  ({self._current_gp} pg)", colors)
        else:
            ax.text(0.5, 0.5, "K_e = 0",
                     ha="center", va="center", color=colors["fg"],
                     transform=ax.transAxes, fontsize=11)
            ax.set_xticks([]); ax.set_yticks([])

        # (1,1) comparación con otros órdenes
        ax = axes[3]
        self._draw_order_comparison(ax, colors)

        self.lbl_gp.configure(text=(
            f"pg actual = {self._current_gp} / {len(pts)}\n"
            f"orden     = {self._order}×{self._order}"
        ))
        self.panel_gauss.redraw()

    def _heatmap(self, ax, M: np.ndarray, title: str, colors) -> None:
        ax.set_facecolor(colors["bg"])
        im = ax.imshow(M, cmap="coolwarm",
                        vmin=-np.max(np.abs(M)) or -1,
                        vmax=np.max(np.abs(M)) or 1)
        ax.set_title(title, color=colors["fg"], fontsize=10)
        ax.set_xticks([]); ax.set_yticks([])

    def _draw_order_comparison(self, ax, colors) -> None:
        coords = self._node_coords()[: self._n_nodes]
        D = constitutive_matrix(self._E, self._nu, self._analysis)
        _, dN_fn = get_shape_functions(self._element_type)
        max_norms = []
        labels = []
        for n in (1, 2, 3):
            pts, wts = get_gauss_points_2d(n)
            K = np.zeros((2 * self._n_nodes, 2 * self._n_nodes))
            for (xi, eta), w in zip(pts, wts):
                dN_nat = dN_fn(xi, eta)
                _, detJ, invJ = compute_jacobian(dN_nat, coords)
                dN_phys = compute_dN_physical(dN_nat, invJ)
                B = compute_b_matrix(dN_phys)
                K += B.T @ D @ B * abs(detJ) * self._t * w
            max_norms.append(float(np.linalg.norm(K)))
            labels.append(f"{n}×{n}")
        ax.set_facecolor(colors["bg"])
        bars = ax.bar(labels, max_norms,
                       color=["#e74c3c", "#4fa3ff", "#a6e3a1"],
                       edgecolor=colors["fg"])
        ax.set_title("‖K_e‖  por orden de cuadratura",
                      color=colors["fg"], fontsize=10)
        ax.tick_params(colors=colors["fg"])
        for bar, v in zip(bars, max_norms):
            ax.text(bar.get_x() + bar.get_width() / 2, v,
                     f"{v:.2e}", ha="center", va="bottom",
                     color=colors["fg"], fontsize=8)

    # ---------- teoría ----------
    def build_theory(self, doc: TheoryDoc, ctx: dict) -> None:
        doc.section("Matriz de rigidez del elemento")
        doc.equation(
            r"\mathbf{k}_e = \int_{-1}^{1}\int_{-1}^{1}"
            r"\mathbf{B}^T(\xi,\eta)\,\mathbf{D}\,\mathbf{B}(\xi,\eta)\,"
            r"|\det\mathbf{J}(\xi,\eta)|\,t\,d\xi\,d\eta"
        )
        doc.subsection("Por qué no integramos analíticamente")
        doc.para(
            r"Para un elemento distorsionado, $\det\mathbf{J}(\xi,\eta)$ es "
            r"una función polinómica no trivial y aparece también en el "
            r"denominador dentro de $\mathbf{J}^{-1}$. Cada entrada "
            r"$K_{ij}(\xi,\eta)$ es una función racional de ξ y η de alto "
            r"grado; la primitiva cerrada no existe en general."
        )
        doc.subsection("Cuadratura de Gauss")
        doc.equation(
            r"\mathbf{k}_e \approx \sum_{p=1}^{n_g}"
            r"\mathbf{B}^T(\xi_p,\eta_p)\,\mathbf{D}\,\mathbf{B}(\xi_p,\eta_p)\,"
            r"|\det\mathbf{J}(\xi_p,\eta_p)|\,t\,w_p"
        )
        doc.para(
            r"Para Q4 con integrando de grado $\leq 3$ en cada variable, la "
            r"cuadratura $2\times 2$ es exacta. Para Q9 suele usarse "
            r"$3\times 3$. La regla $1\times 1$ queda \emph{sub-integrada} "
            r"y genera modos de hourglass."
        )
