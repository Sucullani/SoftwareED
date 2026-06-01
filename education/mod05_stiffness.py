"""
Módulo 5 — Matriz de Rigidez Elemental K_e + Cuadratura de Gauss (overlay)

FUSIÓN 2026-05 (ex-M5 + ex-M5b en un solo módulo). La narrativa que antes
estaba partida en dos overlays vecinos ("la integral es imposible" →
"por eso usamos Gauss") es ahora UN solo argumento contado de arriba
hacia abajo, con el salto conceptual ∫ → Σ como héroe visual:

        k_e = ∫∫ Bᵀ D B |det J| t dξ dη        (imposible a mano)
                            ≈
        k_e ≈ Σ_p  w_p · Bᵀ(ξ_p,η_p) D B |det J| t   (lo aproximamos en PGs)

Estructura del overlay (problema → solución, sin scroll forzado):
  1. Fórmula héroe: la integral analítica ≈ la suma de Gauss. El salto
     conceptual se ve de una sola lectura.
  2. Expander colapsable "▸ ¿Por qué no se puede integrar a mano?":
     oculta por defecto el "monstruo" simbólico K_(i,j)(ξ,η) — selector
     de entrada (i,j) + integrando LaTeX + ventana scrollable con la
     expresión completa. Cero ruido si el alumno no lo abre; evidencia
     contundente si lo abre.
  3. Cuadratura interactiva (acto principal, siempre visible): chips de
     orden 1×1/2×2/3×3 + PGs clickeables sobre el elemento real del
     canvas (sumar/quitar) + matriz k_e que CRECE con cada PG + warnings
     de hourglass (1 PG) / sobre-integración (3×3 en Q4).
  4. Cross-ref a ⑦ Ensamblaje.

`SymbolicIntegrandQ4` vive en `fem/symbolic_integrand.py` (SymPy puro). Tanto
este módulo como `file_io.memoria_calculo` la importan desde ahí.
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
from education.components import (
    LatexExpressionImage, natural_to_physical, element_coords,
)
from education.components.edu_plot_style import (
    apply_edu_style_figure, apply_edu_style_2d,
)
from education.components.expander import Expander
from education.components.latex_image import LatexMatrixImage, ScrollableMatrixImage
from education.components.gauss_glyph import (
    draw_gauss_base, draw_gauss_ghost, GAUSS_ACTIVE,
)

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix
from fem.gauss_quadrature import get_gauss_points_2d
from fem.symbolic_integrand import SymbolicIntegrandQ4

from config.settings import (
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    ELEMENT_Q4, ELEMENT_Q9,
    EDU_FIG_BG, EDU_AXES_BG, EDU_LABEL_BG, EDU_FG, EDU_FG_MUTED,
    EDU_NATURAL_OUTLINE_COLOR, EDU_NATURAL_AXES_COLOR,
    HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR,
    OVERLAY_ACCENT_AMBER, EDU_INTEGRAND_TEXT_COLOR,
)


# Tag de la capa overlay sobre el canvas (PGs interactivos).
_TAG = "edu_m5_pg"
# Radio de snap para togglear un PG con el click.
_SNAP_PX = 14


# La capa simbólica `SymbolicIntegrandQ4` vive ahora en
# `fem/symbolic_integrand.py` (SymPy puro) — se importa arriba. Se movió en
# 2026-05 para que la memoria PDF (file_io) no arrastre el stack Tk de este
# overlay solo para usarla.


# ══════════════ MÓDULO M5 OVERLAY (fusión K_e + Gauss) ══════════════


class StiffnessElementModule(CanvasOverlayModule):
    """M5 overlay fusionado: integral imposible (colapsable) + cuadratura
    de Gauss interactiva (acto principal). El alumno suma PGs clickeándolos
    sobre el elemento real y ve crecer k_e."""

    TITLE = "⑤  Rigidez K_e  —  de la integral a la suma de Gauss"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    # Ancho fijo (como M2/M4): la k_e —ANCHA (8×8 en Q4, 18×18 en Q9)— va en
    # scroll dentro de su viewport, sin estirar el overlay. El cuadrado natural
    # (matplotlib, compacto, centrado) y las fórmulas héroe entran holgadas.
    OVERLAY_WIDTH = 600
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = False
    # Tolerancia de snap a PG dentro del cuadrado natural (coords ξ,η).
    _SNAP_NAT = 0.16

    def build_overlay(self, body):
        # ── Estado: integrando simbólico (ex-M5) ──
        self._i = 1
        self._j = 1
        self._last_kij_expr = None
        self._last_kij_key = None
        self._full_window: Optional[tk.Toplevel] = None
        # Handle del refit diferido (cancelable) — evita el callback colgante
        # si el overlay se cierra dentro de la ventana de 120 ms (espeja M2).
        self._refit_after_id: Optional[str] = None
        # ── Estado: cuadratura (ex-M5b) ──
        self._order = 2
        self._selected_pgs: set = set()
        self._contributions: list = []
        self._click_consumer = self._on_canvas_click_consume

        bg = self._infer_bg(body)

        # ── 1) FÓRMULA HÉROE: el salto ∫ → Σ ──────────────────────
        # Es el CENTRO PEDAGÓGICO del módulo, así que va en LaTeX real
        # (LatexExpressionImage) — no en Consolas monospace. Arriba la
        # integral imposible (rojo), una línea de transición (texto, es
        # prosa), abajo la suma de Gauss que la aproxima (ámbar).
        hero = ttk.Frame(body)
        hero.pack(fill="x", padx=2, pady=(0, 2))
        LatexExpressionImage(
            hero,
            expr=(r"\mathbf{k}_e = \int\!\!\int \mathbf{B}^{T} \mathbf{D}\, "
                  r"\mathbf{B}\,\left|\det\mathbf{J}\right|\, t"
                  r"\;\; d\xi\, d\eta"),
            fontsize=13, color=HEALTH_ERROR_COLOR, bg=bg,
        ).pack(fill="x", pady=(0, 1))
        tk.Label(
            hero,
            text="≈   imposible a mano  →  la aproximamos en los PGs",
            bg=bg, fg=EDU_FG_MUTED, font=("Segoe UI", 9, "italic"),
            anchor="center",
        ).pack(fill="x", pady=(1, 1))
        LatexExpressionImage(
            hero,
            expr=(r"\mathbf{k}_e \approx \sum_{p} w_p\, \mathbf{B}^{T}(\xi_p,\eta_p)\, \mathbf{D}\,"
                  r"\mathbf{B}(\xi_p,\eta_p)\,\left|\det\mathbf{J}\right|\, t"),
            fontsize=13, color=OVERLAY_ACCENT_AMBER, bg=bg,
        ).pack(fill="x", pady=(1, 0))

        # ── 2) EXPANDER: el "monstruo" simbólico (ex-M5), colapsado ──
        self._exp = Expander(
            body, title="¿Por qué no se puede integrar a mano?",
            on_toggle=self._on_expander_toggle, bg=bg,
        )
        self._exp.pack(fill="x", padx=2, pady=(2, 2))
        self._build_integrand_panel(self._exp.body, bg)

        ttk.Separator(body, orient="horizontal").pack(fill="x", pady=(4, 4))

        # ── 3) CUADRATURA INTERACTIVA (ex-M5b), acto principal ───────
        tk.Label(
            body,
            text="Sumá los PGs clickeándolos — en el cuadrado o sobre el elemento:",
            bg=bg, fg=EDU_FG, font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", padx=2, pady=(0, 2))

        chips = ttk.Frame(body)
        chips.pack(fill="x", pady=(0, 2))
        ttk.Label(chips, text="Cuadratura:",
                  font=("Segoe UI", 9), foreground=EDU_FG_MUTED,
                  ).pack(side="left", padx=(2, 4))
        self._var_order = tk.StringVar(value=f"{self._order}×{self._order}")
        for n in (1, 2, 3):
            ttk.Radiobutton(
                chips, text=f"{n}×{n}", value=f"{n}×{n}",
                variable=self._var_order,
                bootstyle="info-outline-toolbutton",
                command=self._on_order_change,
            ).pack(side="left", padx=1)

        # ── Cuadrado natural (matplotlib, CENTRADO) — estilo M2/M4 ─────
        # M5 evalúa la cuadratura en los PGs del CUADRADO NATURAL (ξ,η). El
        # cuadrado MIRA la selección: PG sumado → dorado, excluido → ghost
        # dashed (espeja el canvas). Clickear un PG aquí lo toglea (igual que
        # sobre el elemento físico — bidireccional). SIN descripción de mapeo
        # (era ruido; el grid de PGs ya muestra el espacio (ξ,η)).
        plot_frame = ttk.Frame(body)
        plot_frame.pack(pady=(2, 2))  # sin fill → frame centrado en el body
        # Figura COMPACTA (2.6×2.0): el cuadrado solo muestra los PGs (sin
        # marcador/valor), así que no necesita altura — clave para no estirar
        # el overlay (la meta de "corregir altura").
        self._fig = Figure(figsize=(2.6, 2.0), dpi=100)
        apply_edu_style_figure(self._fig)
        self._ax_nat = self._fig.add_subplot(111)
        apply_edu_style_2d(self._ax_nat, show_spines=False)
        self._fig.subplots_adjust(left=0.05, right=0.95, top=0.82, bottom=0.05)
        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=plot_frame)
        self._canvas_mpl.get_tk_widget().pack()
        self._canvas_mpl.mpl_connect("button_press_event",
                                     self._on_natural_pick_mpl)

        # Warning hourglass / sobre-integración (vacío salvo casos límite).
        self._lbl_warning = tk.Label(
            body, text="", bg=bg, fg=HEALTH_ERROR_COLOR,
            font=("Segoe UI Semibold", 9), anchor="w",
        )
        self._lbl_warning.pack(fill="x", padx=2, pady=(2, 0))

        # Matriz k_e que crece con los PGs sumados. `fill="x"` (no expand): el
        # overlay shrink-wrappea (OVERLAY_HEIGHT=None) → no hay alto sobrante
        # que distribuir, y la altura está ACOTADA por el viewport de k_e.
        self._k_frame = ttk.Frame(body)
        self._k_frame.pack(fill="x", pady=(2, 2))
        self._k_placeholder = tk.Label(
            self._k_frame,
            text="◎  Clickeá un elemento\ny luego los PGs del canvas",
            bg=EDU_AXES_BG, fg=EDU_FG_MUTED, font=("Segoe UI", 10),
            justify="center",
        )
        self._k_placeholder.pack(expand=True)
        # k_e ya se rotula con su prefijo `\mathbf{k}_e=` en la matriz; el ex
        # `_lbl_k_title` ("k_e · n/n pg") era redundante → eliminado. El conteo
        # n/total vive solo en el status.
        self._mat_k: Optional[ScrollableMatrixImage] = None

        # Status (Σ n/total pg + último sumado).
        self._lbl_status = tk.Label(
            body, text="", bg=bg, fg=OVERLAY_ACCENT_AMBER,
            font=("Consolas", 9, "bold"), anchor="w",
        )
        self._lbl_status.pack(fill="x", padx=2)

        # ── 4) Cross-ref a ⑦ Ensamblaje ──────────────────────────
        self._pack_crossref(
            body, "mod07",
            "👉 k_e completo se ENSAMBLA en K global. Ver ⑦ Ensamblaje.",
            wraplength=520,
        )

        # Estado inicial: TODOS los PGs sumados (la cuadratura correcta).
        self._rebuild_contributions()
        self._selected_pgs = set(range(len(self._contributions)))
        self._refresh_all()

    @staticmethod
    def _infer_bg(widget) -> str:
        try:
            from education.components.latex_image import _infer_bg
            return _infer_bg(widget)
        except Exception:
            return EDU_AXES_BG

    # ── Panel del integrando (dentro del expander) ─────────────────
    def _build_integrand_panel(self, parent, bg) -> None:
        # Métrica de complejidad en vivo — CLICKEABLE (abre la expresión
        # completa, scrollable). Convierte "imposible" en evidencia.
        self._lbl_complexity = ttk.Label(
            parent, text="", font=("Consolas", 9, "bold"),
            foreground=OVERLAY_ACCENT_AMBER, wraplength=520, justify="left",
            cursor="hand2",
        )
        self._lbl_complexity.pack(fill="x", pady=(2, 2))
        self._lbl_complexity.bind(
            "<Button-1>", lambda _e: self._open_full_integrand_window()
        )

        # Selector de entrada K_(i,j).
        sel = ttk.Frame(parent)
        sel.pack(fill="x", pady=(0, 2))
        ttk.Label(sel, text="Entrada K_(i,j):",
                  font=("Segoe UI", 9), foreground=EDU_FG_MUTED,
                  ).pack(side="left", padx=(0, 4))
        n_dofs_init = 2 * (self.element.num_nodes if self.element else 4)
        self._var_i = tk.StringVar(value=str(self._i))
        # Refs guardadas para reconfigurar `to` al cambiar de elemento (Q4↔Q9):
        # sin esto, las flechas del spinner topaban en el GDL del elemento
        # INICIAL aunque k_e creciera a 18×18.
        self._spin_i = ttk.Spinbox(sel, from_=1, to=n_dofs_init, width=4,
                    textvariable=self._var_i, command=self._on_ij_change)
        self._spin_i.pack(side="left", padx=1)
        self._var_j = tk.StringVar(value=str(self._j))
        self._spin_j = ttk.Spinbox(sel, from_=1, to=n_dofs_init, width=4,
                    textvariable=self._var_j, command=self._on_ij_change)
        self._spin_j.pack(side="left", padx=1)
        ttk.Separator(sel, orient="vertical").pack(side="left",
                                                    fill="y", padx=8)
        self._lbl_dim = ttk.Label(sel, text="", font=("Segoe UI", 9),
                                  foreground=EDU_FG_MUTED)
        self._lbl_dim.pack(side="left")

        # Integrando simbólico como imagen LaTeX.
        self._integrand_container = tk.Frame(parent, bg=EDU_LABEL_BG,
                                             relief="solid", borderwidth=1)
        self._integrand_container.pack(fill="both", expand=True, pady=(2, 2))
        self._integrand_widget: Optional[LatexExpressionImage] = None
        self._integrand_placeholder = tk.Label(
            self._integrand_container,
            text="◎  Clickeá un elemento\nen el canvas",
            bg=EDU_LABEL_BG, fg=EDU_FG_MUTED, font=("Segoe UI", 11),
        )
        self._integrand_placeholder.pack(expand=True, fill="both",
                                         padx=8, pady=8)

    # ── Ciclo de vida ──────────────────────────────────────────────
    def on_activated(self):
        self._mesh.add_click_consumer(self._click_consumer)
        self._mesh.redraw()

    def on_closed(self):
        try:
            self._mesh.remove_click_consumer(self._click_consumer)
        except Exception:
            pass
        # Cancelar el refit diferido pendiente (si lo hay) para no disparar
        # refit_overlay() sobre el Toplevel ya withdrawn.
        if getattr(self, "_refit_after_id", None) is not None:
            try:
                self._mesh.after_cancel(self._refit_after_id)
            except Exception:
                pass
            self._refit_after_id = None
        # Cerrar la ventana de la expresión completa si quedó abierta.
        if self._full_window is not None:
            try:
                self._full_window.destroy()
            except Exception:
                pass
            self._full_window = None

    def _schedule_refit(self) -> None:
        """Re-ajusta el overlay ahora + difiere un segundo refit (captura el
        swap async de imágenes pdflatex). El handle diferido es cancelable en
        on_closed para no colgar un callback sobre un overlay ya cerrado."""
        self.refit_overlay()
        if getattr(self, "_refit_after_id", None) is not None:
            try:
                self._mesh.after_cancel(self._refit_after_id)
            except Exception:
                pass
        try:
            self._refit_after_id = self._mesh.after(120, self._do_deferred_refit)
        except Exception:
            self._refit_after_id = None

    def _do_deferred_refit(self) -> None:
        self._refit_after_id = None
        self.refit_overlay()

    def on_element_selected(self, elem_id):
        if elem_id == self.element_id:
            return
        self.element_id = elem_id
        self.element = self.project.elements.get(elem_id) if self.project else None
        # Invalida cache simbólico (coords cambiaron) y recontruye PGs.
        self._last_kij_expr = None
        self._last_kij_key = None
        # Reconfigurar el tope de los spinbox K_(i,j) al GDL del NUEVO elemento
        # (Q4→8, Q9→18): sin esto las flechas topaban en el GDL del inicial.
        n_dofs = 2 * (self.element.num_nodes if self.element else 4)
        for spin in (getattr(self, "_spin_i", None), getattr(self, "_spin_j", None)):
            if spin is not None:
                try:
                    spin.configure(to=n_dofs)
                except tk.TclError:
                    pass
        self._rebuild_contributions()
        self._selected_pgs = set(range(len(self._contributions)))
        self._refresh_all()

    def _on_expander_toggle(self):
        """Render perezoso del integrando: solo cuando el expander se abre.

        Tras togglear, el body cambia de alto y el overlay no crece solo
        (geometria fijada en show()) — re-ajustamos para que el integrando
        expandido no quede recortado. Inmediato + diferido (captura el swap
        async a pdflatex de la imagen del integrando)."""
        if self._exp is not None and self._exp.is_expanded:
            self._refresh_integrand()
        self._schedule_refit()

    # ── Callbacks de la cuadratura ─────────────────────────────────
    def _on_order_change(self):
        try:
            self._order = int(self._var_order.get().split("×")[0])
        except (ValueError, AttributeError):
            return
        self._rebuild_contributions()
        self._selected_pgs = set(range(len(self._contributions)))
        self._refresh_all()

    def _on_canvas_click_consume(self, event) -> bool:
        """Toggle del PG bajo el click (suma/quita su contribución a k_e).
        Consume el click (return True) si pegó en un PG; sino False y el
        canvas hace su hit-test estándar (cambio de elemento)."""
        if self.element is None or self.project is None:
            return False
        coords = self._node_coords()
        if coords is None:
            return False
        n_nodes = self.element.num_nodes
        coords = coords[:n_nodes]
        try:
            pts, _ = get_gauss_points_2d(self._order)
        except Exception:
            return False
        et = self._element_type()
        best_idx, best_dpx = -1, float("inf")
        for idx, (xi, eta) in enumerate(pts):
            xy = natural_to_physical(float(xi), float(eta), coords, et)
            sx, sy = self._mesh.world_to_screen(float(xy[0]), float(xy[1]))
            d = math.hypot(sx - event.x, sy - event.y)
            if d < best_dpx:
                best_dpx, best_idx = d, idx
        if best_idx < 0 or best_dpx > _SNAP_PX:
            return False
        if best_idx in self._selected_pgs:
            self._selected_pgs.discard(best_idx)
        else:
            self._selected_pgs.add(best_idx)
        self._refresh_all()
        return True

    # ── Capa overlay: PGs sobre el elemento ────────────────────────
    def draw_canvas_layer(self, mesh):
        mesh.canvas.delete(_TAG)
        if self.element is None or self.project is None:
            return
        coords = self._node_coords()
        if coords is None:
            return
        n_nodes = self.element.num_nodes
        coords = coords[:n_nodes]
        try:
            pts, _ = get_gauss_points_2d(self._order)
        except Exception:
            return
        et = self._element_type()
        # PG sumado → base dorado; PG excluido → ghost gris dashed.
        for idx, (xi, eta) in enumerate(pts):
            xy = natural_to_physical(float(xi), float(eta), coords, et)
            sx, sy = mesh.world_to_screen(float(xy[0]), float(xy[1]))
            if idx in self._selected_pgs:
                draw_gauss_base(mesh.canvas, sx, sy, label=None,
                                tag=_TAG, color=GAUSS_ACTIVE)
            else:
                draw_gauss_ghost(mesh.canvas, sx, sy, tag=_TAG)

    # ── Cálculo de contribuciones ──────────────────────────────────
    def _element_type(self) -> str:
        if self.element is not None and getattr(self.element, "num_nodes", 0) == 9:
            return ELEMENT_Q9
        if self.project is not None and \
                getattr(self.project, "element_type", None) == ELEMENT_Q9:
            return ELEMENT_Q9
        return ELEMENT_Q4

    def _rebuild_contributions(self):
        if self.element is None or self.project is None:
            self._contributions = []
            return
        coords = self._node_coords()
        if coords is None:
            self._contributions = []
            return
        n_nodes = self.element.num_nodes
        coords = coords[:n_nodes]
        E, nu, t = self._resolve_params()
        D = constitutive_matrix(E, nu, self._analysis_type())
        _, dN_fn = get_shape_functions(self._element_type())
        try:
            pts, wts = get_gauss_points_2d(self._order)
        except Exception:
            self._contributions = []
            return
        contribs = []
        for ((xi, eta), w) in zip(pts, wts):
            dN_nat = dN_fn(xi, eta)
            _, detJ, invJ = compute_jacobian(dN_nat, coords)
            dN_phys = compute_dN_physical(dN_nat, invJ)
            B = compute_b_matrix(dN_phys)
            contrib = B.T @ D @ B * abs(detJ) * t * w
            contribs.append({
                "xi": float(xi), "eta": float(eta), "w": float(w),
                "detJ": float(detJ), "contrib": contrib,
            })
        self._contributions = contribs

    def _node_coords(self) -> Optional[np.ndarray]:
        # Delega al helper compartido (antes duplicado en M1/M2/M4/M5/M7).
        return element_coords(self.project, self.element)

    def _resolve_params(self):
        E_def, nu_def, t_def = 225_000.0, 0.2, 0.8
        if self.project is None or self.element is None:
            return E_def, nu_def, t_def
        mat = self.project.materials.get(
            getattr(self.element, "material_name", None)
        )
        if mat is not None:
            return float(mat.E), float(mat.nu), float(self.element.thickness)
        return E_def, nu_def, t_def

    def _analysis_type(self) -> str:
        if self.project is not None:
            at = getattr(self.project, "analysis_type", None)
            if at in (ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN):
                return at
        return ANALYSIS_PLANE_STRESS

    def _k_from_selection(self) -> Optional[np.ndarray]:
        if not self._contributions:
            return None
        n_dof = self._contributions[0]["contrib"].shape[0]
        K = np.zeros((n_dof, n_dof))
        for idx in self._selected_pgs:
            if 0 <= idx < len(self._contributions):
                K = K + self._contributions[idx]["contrib"]
        return K

    # ── Render general ─────────────────────────────────────────────
    def _refresh_all(self):
        # Dim label del expander (depende del element_type).
        n_nodes = self.element.num_nodes if self.element else 4
        n_dof = 2 * n_nodes
        try:
            self._lbl_dim.configure(
                text=f"k_e es {n_dof}×{n_dof} · {'Q9' if n_nodes == 9 else 'Q4'}"
            )
        except (tk.TclError, AttributeError):
            pass
        # Integrando: solo si el expander está abierto (perezoso).
        if self._exp is not None and self._exp.is_expanded:
            self._refresh_integrand()
        self._refresh_warning()
        self._refresh_k_heatmap()
        self._refresh_natural_square()
        self._refresh_status()
        try:
            self._mesh.redraw()
        except Exception:
            pass

    # ── Cuadrado natural (subplot 2D matplotlib, estilo M2/M4) ─────
    def _draw_natural_square(self, ax) -> None:
        """Dibuja el cuadrado natural (ξ,η) con los PGs del orden activo:
        sumado → dorado (`GAUSS_ACTIVE`), excluido → ghost dashed. Espeja la
        selección del canvas físico. Sin marcador único (M5 es multi-PG)."""
        if ax is None:
            return
        ax.clear()
        apply_edu_style_2d(ax, show_spines=False)
        ax.set_aspect("equal")
        sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
        ax.plot(sq[:, 0], sq[:, 1], color=EDU_NATURAL_OUTLINE_COLOR, lw=1.0)
        ax.fill(sq[:, 0], sq[:, 1], color=EDU_NATURAL_OUTLINE_COLOR, alpha=0.06)
        ax.axhline(0, color=EDU_NATURAL_AXES_COLOR, lw=0.8, alpha=0.85)
        ax.axvline(0, color=EDU_NATURAL_AXES_COLOR, lw=0.8, alpha=0.85)
        try:
            pts, _ = get_gauss_points_2d(self._order)
        except Exception:
            pts = []
        for idx, (gx, gy) in enumerate(pts):
            if idx in self._selected_pgs:
                ax.scatter([gx], [gy], s=82, c=GAUSS_ACTIVE,
                            edgecolors="white", linewidths=0.9, zorder=8)
            else:
                ax.scatter([gx], [gy], s=64, facecolors="none",
                            edgecolors=EDU_FG_MUTED, linewidths=1.1,
                            linestyle=(0, (2, 2)), zorder=6)
        ax.text(1.0, -1.2, "+1", color=EDU_FG_MUTED, fontsize=7,
                 family="monospace", ha="center", va="top")
        ax.text(-1.0, -1.2, "-1", color=EDU_FG_MUTED, fontsize=7,
                 family="monospace", ha="center", va="top")
        ax.text(1.3, 0.02, "ξ", color=EDU_FG_MUTED, fontsize=9,
                 family="monospace", fontweight="bold", ha="left", va="center")
        ax.text(0.02, 1.3, "η", color=EDU_FG_MUTED, fontsize=9,
                 family="monospace", fontweight="bold", ha="left", va="center")
        ax.set_xlim(-1.45, 1.45); ax.set_ylim(-1.45, 1.45)
        ax.set_title("Cuadratura en el cuadrado natural  (ξ, η)",
                      color=EDU_NATURAL_OUTLINE_COLOR, fontsize=9,
                      fontweight="bold", pad=4)
        ax.set_xticks([]); ax.set_yticks([])

    def _on_natural_pick_mpl(self, event) -> None:
        """Click en un PG del cuadrado natural → toglea su contribución a k_e
        (idéntico a clickearlo sobre el elemento físico — bidireccional)."""
        if getattr(event, "button", None) != 1:
            return
        if event.inaxes is not self._ax_nat:
            return
        if event.xdata is None or event.ydata is None:
            return
        xi, eta = float(event.xdata), float(event.ydata)
        try:
            pts, _ = get_gauss_points_2d(self._order)
        except Exception:
            return
        best_idx, best_d = None, float("inf")
        for idx, (gx, gy) in enumerate(pts):
            d = math.hypot(xi - gx, eta - gy)
            if d < best_d:
                best_d, best_idx = d, idx
        if best_idx is None or best_d > self._SNAP_NAT:
            return
        if best_idx in self._selected_pgs:
            self._selected_pgs.discard(best_idx)
        else:
            self._selected_pgs.add(best_idx)
        self._refresh_all()

    def _refresh_natural_square(self):
        """Redibuja el cuadrado natural (orden de cuadratura + selección)."""
        if (getattr(self, "_ax_nat", None) is None
                or getattr(self, "_canvas_mpl", None) is None):
            return
        try:
            self._draw_natural_square(self._ax_nat)
            self._canvas_mpl.draw_idle()
        except Exception:
            pass

    # ── Render del integrando simbólico (ex-M5) ────────────────────
    def _is_q9(self) -> bool:
        return (self.element is not None
                and getattr(self.element, "num_nodes", 0) == 9)

    def _refresh_integrand(self):
        if self.element is None or self.project is None:
            self._show_placeholder("◎  Clickeá un elemento\nen el canvas")
            self._set_complexity("")
            return
        if self._is_q9():
            self._show_q9_notice()
            self._set_complexity(
                "Q9: B es 3×18 ⇒ cada K_(i,j) expande a 10³–10⁴ términos."
            )
            return
        coords = self._node_coords()
        if coords is None:
            self._show_placeholder("(sin coords)")
            self._set_complexity("")
            return
        E, nu, t = self._resolve_params()
        analysis = self._analysis_type()
        coords_list = coords[:4].tolist()
        cache_key = (self._i, self._j, analysis, tuple(map(tuple, coords_list)))
        if cache_key == self._last_kij_key and self._last_kij_expr is not None:
            expr = self._last_kij_expr
        else:
            try:
                sym = SymbolicIntegrandQ4(E, nu, t, coords_list)
                expr = sym.integrand_entry(self._i - 1, self._j - 1, analysis)
                self._last_kij_expr = expr
                self._last_kij_key = cache_key
            except Exception as exc:
                self._show_placeholder(
                    f"Error K_(i={self._i},j={self._j}):\n{exc}",
                    fg=HEALTH_ERROR_COLOR)
                self._set_complexity("")
                return
        try:
            latex_body = sp.latex(expr)
        except Exception:
            latex_body = str(expr)
        n_terms = self._count_terms(expr)
        n_chars = len(latex_body)
        pages = max(1, round(n_chars / 1500))
        cmp_txt = (f"📏 K_({self._i},{self._j}): {n_terms} términos · "
                   f"{n_chars:,} chars LaTeX · ≈{pages} pág impresas")
        self._set_complexity(cmp_txt.replace(",", "."))
        latex_body = self._truncate_latex(latex_body, max_chars=320)
        full = (f"K_{{{self._i},{self._j}}}(\\xi,\\eta) \\;=\\; " + latex_body)
        self._show_latex(full)

    def _on_ij_change(self):
        if self.element is None:
            return
        try:
            n_dofs = 2 * self.element.num_nodes
            i = max(1, min(n_dofs, int(self._var_i.get())))
            j = max(1, min(n_dofs, int(self._var_j.get())))
        except (tk.TclError, ValueError):
            return
        self._i, self._j = i, j
        self._var_i.set(str(i))
        self._var_j.set(str(j))
        self._refresh_integrand()

    def _set_complexity(self, text: str) -> None:
        try:
            self._lbl_complexity.configure(text=text)
        except (tk.TclError, AttributeError):
            pass

    @staticmethod
    def _count_terms(expr) -> int:
        try:
            expanded = sp.expand(expr)
        except Exception:
            return 0
        try:
            return len(sp.Add.make_args(expanded))
        except Exception:
            return 0

    def _open_full_integrand_window(self) -> None:
        if self._last_kij_expr is None:
            return
        if (self._full_window is not None
                and self._full_window.winfo_exists()):
            try:
                self._full_window.lift()
                self._full_window.focus_set()
                return
            except tk.TclError:
                self._full_window = None
        top = tk.Toplevel(self._mesh.canvas)
        top.title(f"Integrando K_({self._i},{self._j}) — expresión completa")
        top.geometry("900x700")
        top.configure(bg=EDU_AXES_BG)
        try:
            top.geometry(f"+{self._mesh.canvas.winfo_rootx() + 80}"
                         f"+{self._mesh.canvas.winfo_rooty() + 60}")
        except tk.TclError:
            pass
        try:
            latex_full = sp.latex(self._last_kij_expr)
        except Exception:
            latex_full = ""
        n_terms = self._count_terms(self._last_kij_expr)
        n_chars = len(latex_full)
        n_dofs = 2 * (self.element.num_nodes if self.element else 4)
        header = tk.Frame(top, bg=EDU_AXES_BG)
        header.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(
            header,
            text=(f"K_({self._i},{self._j})(ξ, η)  ·  {n_terms} términos  ·  "
                  f"{n_chars:,} chars LaTeX").replace(",", "."),
            bg=EDU_AXES_BG, fg=OVERLAY_ACCENT_AMBER,
            font=("Consolas", 12, "bold"), anchor="w",
        ).pack(fill="x")
        tk.Label(
            header,
            text=(f"Esta es UNA entrada de la matriz k_e ({n_dofs}×{n_dofs}). "
                  f"Hay {n_dofs * n_dofs} expresiones como esta — y todavía "
                  "falta integrarlas. Por eso Gauss."),
            bg=EDU_AXES_BG, fg=EDU_FG_MUTED,
            font=("Segoe UI", 9, "italic"),
            anchor="w", justify="left", wraplength=860,
        ).pack(fill="x", pady=(2, 2))
        body_frame = tk.Frame(top, bg=EDU_AXES_BG)
        body_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        text = tk.Text(
            body_frame, wrap="none", bg=EDU_LABEL_BG, fg=EDU_INTEGRAND_TEXT_COLOR,
            font=("Consolas", 9), insertbackground=EDU_INTEGRAND_TEXT_COLOR,
            relief="flat", borderwidth=0,
        )
        vscroll = ttk.Scrollbar(body_frame, orient="vertical",
                                command=text.yview)
        hscroll = ttk.Scrollbar(body_frame, orient="horizontal",
                                command=text.xview)
        text.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        body_frame.rowconfigure(0, weight=1)
        body_frame.columnconfigure(0, weight=1)
        try:
            pretty = sp.pretty(sp.expand(self._last_kij_expr),
                               num_columns=240, use_unicode=True)
        except Exception:
            pretty = str(self._last_kij_expr)
        text.insert("1.0", pretty)
        text.configure(state="disabled")
        footer = tk.Frame(top, bg=EDU_AXES_BG)
        footer.pack(fill="x", padx=10, pady=(0, 10))
        n_lines = pretty.count("\n") + 1
        tk.Label(
            footer,
            text=(f"📏 {n_lines:,} líneas tabuladas  ·  "
                  f"≈ {max(1, n_lines // 60)} páginas impresas "
                  "(Esc cierra)").replace(",", "."),
            bg=EDU_AXES_BG, fg=EDU_FG_MUTED,
            font=("Consolas", 9), anchor="w",
        ).pack(fill="x")

        def _close(_e=None):
            try:
                top.destroy()
            except tk.TclError:
                pass
            self._full_window = None
        top.protocol("WM_DELETE_WINDOW", _close)
        top.bind("<Escape>", _close)
        self._full_window = top

    def _show_placeholder(self, text: str, *, fg: str = EDU_FG_MUTED) -> None:
        if self._integrand_widget is not None:
            self._integrand_widget.destroy()
            self._integrand_widget = None
        try:
            self._integrand_placeholder.configure(text=text, fg=fg)
            if not self._integrand_placeholder.winfo_ismapped():
                self._integrand_placeholder.pack(expand=True, fill="both",
                                                 padx=8, pady=8)
        except tk.TclError:
            pass

    def _show_q9_notice(self) -> None:
        if self._integrand_widget is not None:
            self._integrand_widget.destroy()
            self._integrand_widget = None
        try:
            self._integrand_placeholder.configure(
                text=("K_(i,j)(ξ, η) = [Bᵀ D B]_(i,j) · |det J| · t\n\n"
                      "Q9: B es 3×18 → la expansión simbólica de K_(i,j)\n"
                      "excede el parser de mathtext.\n"
                      "La conclusión es la misma: imposible analíticamente."),
                fg=EDU_INTEGRAND_TEXT_COLOR,
            )
            if not self._integrand_placeholder.winfo_ismapped():
                self._integrand_placeholder.pack(expand=True, fill="both",
                                                 padx=8, pady=8)
        except tk.TclError:
            pass

    def _show_latex(self, expr: str) -> None:
        try:
            if self._integrand_placeholder.winfo_ismapped():
                self._integrand_placeholder.pack_forget()
        except tk.TclError:
            pass
        if self._integrand_widget is None:
            self._integrand_widget = LatexExpressionImage(
                self._integrand_container, expr=expr,
                fontsize=13, color=EDU_INTEGRAND_TEXT_COLOR, bg=EDU_LABEL_BG, cache=True,
            )
            self._integrand_widget.pack(expand=True, padx=8, pady=8)
        else:
            try:
                self._integrand_widget.set_expression(expr)
            except tk.TclError:
                pass

    @staticmethod
    def _truncate_latex(s: str, max_chars: int = 320) -> str:
        if len(s) <= max_chars:
            return s
        cut = max_chars - 12
        depth = 0
        last_safe = 0
        for i, ch in enumerate(s[:cut]):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth = max(0, depth - 1)
            elif depth == 0 and ch in "+-" and i > 0:
                last_safe = i
        if last_safe == 0:
            stub = s[:cut]
            opens = stub.count("{") - stub.count("}")
            return stub + "}" * max(0, opens) + r"\,\cdots"
        return s[:last_safe] + r"\,\cdots"

    # ── Render de la cuadratura (ex-M5b) ───────────────────────────
    def _refresh_warning(self):
        if self._lbl_warning is None:
            return
        try:
            n_sel = len(self._selected_pgs)
            n_total = len(self._contributions)
            et = self._element_type()
            if n_total > 0 and n_sel == 1:
                self._lbl_warning.configure(
                    text="⚠ 1 PG ⇒ SUB-INTEGRACIÓN: modos hourglass posibles",
                    fg=HEALTH_ERROR_COLOR,
                )
            elif (et == ELEMENT_Q4 and self._order == 3
                  and n_sel == n_total and n_total == 9):
                self._lbl_warning.configure(
                    text="ⓘ 3×3 sobre-integra Q4 (no daña, computa de más)",
                    fg=HEALTH_WARNING_COLOR,
                )
            else:
                # n_sel == 0 NO usa el warning: la instrucción fija de arriba
                # + el placeholder "k_e = 0" ya comunican el estado vacío (se
                # evita el triple mensaje redundante). El warning queda solo
                # para hourglass / sobre-integración.
                self._lbl_warning.configure(text="")
        except tk.TclError:
            pass

    def _refresh_k_heatmap(self):
        n_sel = len(self._selected_pgs)
        if self.element is None or not self._contributions or n_sel == 0:
            placeholder_text = (
                "◎  Clickeá un elemento\ny luego los PGs del canvas"
                if (self.element is None or not self._contributions)
                else "k_e = 0"  # estado de la matriz; la acción ya está arriba
            )
            self._show_k_placeholder(placeholder_text)
            return
        K = self._k_from_selection()
        if K is None:
            self._show_k_placeholder("k_e = 0")
            return
        prefix = r"\mathbf{k}_e = "
        fs_base = 14 if K.shape[0] <= 12 else 11
        self._show_k_matrix(K, prefix=prefix, fs=fs_base)

    def _show_k_placeholder(self, text: str) -> None:
        if self._mat_k is not None:
            try:
                self._mat_k.pack_forget()
            except tk.TclError:
                pass
        try:
            self._k_placeholder.configure(text=text)
            if not self._k_placeholder.winfo_ismapped():
                self._k_placeholder.pack(expand=True)
        except tk.TclError:
            pass

    def _show_k_matrix(self, Kn: np.ndarray, *, prefix: str, fs: int) -> None:
        try:
            self._k_placeholder.pack_forget()
        except tk.TclError:
            pass
        if self._mat_k is None:
            # k_e en viewport con scroll/pan IN-FRAME (sin pop-up). Render a
            # fontsize legible (shrink=False): Q4 (8×8) entra; Q9 (18×18) se
            # explora arrastrando o con la rueda, en vez de salir a ~6 pt.
            # Viewport ALTO ACOTADO (200) para que la 18×18 de Q9 NO estire el
            # overlay a pantalla completa — scrollea en vertical (antes 300 lo
            # hacía gigante). Ancho ceñido al overlay (600−60).
            self._mat_k = ScrollableMatrixImage(
                self._k_frame, matrix=Kn,
                fmt="{:.0f}", fontsize=fs, prefix=prefix,
                viewport=(self.OVERLAY_WIDTH - 60, 200),
            )
        else:
            self._mat_k.set_style(fontsize=fs)
            self._mat_k.set_matrix(Kn, prefix=prefix)
        try:
            newly_shown = not self._mat_k.winfo_ismapped()
            if newly_shown:
                self._mat_k.pack(fill="x", pady=(4, 4))
                # k_e aparece DESPUÉS de show() — re-ajustar el overlay una vez
                # para que el viewport entre completo. Idempotente; no se
                # redispara por click de PG (el widget ya queda mapeado).
                self._schedule_refit()
        except tk.TclError:
            pass

    def _refresh_status(self):
        if self._lbl_status is None:
            return
        n_sel = len(self._selected_pgs)
        n_total = len(self._contributions)
        try:
            if n_total == 0:
                self._lbl_status.configure(text="")
                return
            if n_sel > 0:
                idx = max(self._selected_pgs)
                c = self._contributions[idx]
                self._lbl_status.configure(
                    text=(f"Σ {n_sel}/{n_total} pg   "
                          f"último: pg{idx + 1}  w={c['w']:.3f}  "
                          f"|det J|={c['detJ']:.3g}")
                )
            else:
                self._lbl_status.configure(text=f"Σ 0/{n_total} pg")
        except tk.TclError:
            pass
