"""
Módulo 5b — Cuadratura de Gauss (overlay)

Sigue la narrativa de M5 (Matriz K_e). Donde M5 muestra la forma
analítica y declara la integral imposible, M5b muestra LA SOLUCIÓN
NUMÉRICA: evaluar el integrando en puntos de Gauss y sumar con pesos.

        k_e = Σ_{p}  w_p · Bᵀ(ξ_p, η_p) · D · B(ξ_p, η_p)
                       · |det J(ξ_p, η_p)| · t

**Interacción 2026-05**: el alumno *es* la cuadratura. Cada PG aparece
como punto interactivo sobre el elemento del canvas. Click sobre un
PG lo suma a k_e (heatmap crece); re-click lo quita. Cero botones,
cero scrubber — la cuadratura se construye gesto a gesto sobre la
geometría real.

Narrativa:
    ← M5 :  "vimos que la integral es imposible"
    M5b (este) : "VOS aproximás eligiendo qué PGs sumás"
    → M7 :  "el k_e completo se ensambla en K global"
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from education.overlay_module import CanvasOverlayModule
from education.components import natural_to_physical, GaussCoordReadout
from education.components.gauss_glyph import (
    draw_gauss_base, draw_gauss_ghost, draw_gauss_halo,
    GAUSS_ACTIVE,
)
from education.components.latex_image import LatexMatrixImage

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix
from fem.gauss_quadrature import get_gauss_points_2d
from config.settings import (
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    ELEMENT_Q4, ELEMENT_Q9,
    HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR,
    EDU_FIG_BG, EDU_AXES_BG, EDU_FG, EDU_FG_MUTED,
)


_TAG = "edu_m5b_pg"
_SNAP_PX = 14


class GaussQuadratureModule(CanvasOverlayModule):
    """M5b overlay: el alumno clickea PGs sobre el elemento para sumarlos."""

    TITLE = "⑤′  Cuadratura de Gauss"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (600, 24)
    # Width = None → el overlay auto-fitea al ancho real del K widget.
    # K_e Q4 (8x8) y Q9 (18x18) son matrices "fat": forzar 520 px clipea
    # el corchete derecho (`\right]`) y la matriz luce mutilada.
    OVERLAY_WIDTH = None
    OVERLAY_HEIGHT = None
    REQUIRES_ELEMENT = False

    def build_overlay(self, body):
        # Estado
        self._order = 2
        self._selected_pgs: set = set()
        self._contributions: list = []
        # Click consumer (bound method) — el MeshCanvas lo consulta antes
        # de su hit-test estándar. Si toggleamos un PG, consumimos el click
        # (return True) y la selección del elemento se preserva.
        self._click_consumer = self._on_canvas_click_consume

        # Banner: bridge desde M5.
        ttk.Label(
            body,
            text=("← Como vimos en M5, la integral es imposible.\n"
                  "    APROXIMÁS eligiendo PGs sobre el elemento:"),
            font=("Segoe UI", 9, "italic"),
            foreground="#90caf9", justify="left",
        ).pack(fill="x", padx=4, pady=(0, 2))

        ttk.Label(
            body,
            text=("k_e ≈ Σ  w_p · Bᵀ(ξ_p,η_p) D B(ξ_p,η_p) "
                  "|det J| t"),
            font=("Consolas", 10, "bold"),
            foreground="#ffd54f", justify="center",
        ).pack(fill="x", padx=4, pady=(0, 6))

        # Readout dual: pequeño cuadrado natural + (ξ,η) en forma cerrada
        # + (x,y) físico del último PG clickeado. Refuerza la dualidad
        # físico↔natural que distingue al método isoparamétrico.
        self._readout = GaussCoordReadout(
            body, order=self._order, etype=self._element_type(),
        )
        self._readout.pack(fill="x", padx=4, pady=(0, 4))

        # Chips: orden de cuadratura (define el grid de PGs disponible)
        chips = ttk.Frame(body)
        chips.pack(fill="x", pady=(0, 2))
        ttk.Label(chips, text="Cuadratura:",
                   font=("Segoe UI", 9), foreground=EDU_FG_MUTED,
                   ).pack(side="left", padx=(0, 4))
        self._var_order = tk.StringVar(value=f"{self._order}×{self._order}")
        for n in (1, 2, 3):
            ttk.Radiobutton(
                chips, text=f"{n}×{n}", value=f"{n}×{n}",
                variable=self._var_order,
                bootstyle="info-outline-toolbutton",
                command=self._on_order_change,
            ).pack(side="left", padx=1)

        # Warning hourglass / over-integration
        self._lbl_warning = tk.Label(
            body, text="", bg=EDU_AXES_BG,
            fg=HEALTH_ERROR_COLOR,
            font=("Segoe UI Semibold", 9), anchor="w",
        )
        self._lbl_warning.pack(fill="x", padx=4, pady=(2, 0))

        # Matriz k_e como LatexMatrixImage (mismo patron que B en M4):
        # widget Tk con PhotoImage, set_matrix re-renderea sin tocar
        # axes (ni recompute de zoom, ni movimiento de posicion al
        # cambiar el tamano). Vive en un frame propio para que el
        # placeholder ("Click PGs...") pueda reemplazarlo cuando no
        # hay seleccion.
        self._ax_natural = None   # compat: algunos metodos lo leen
        self._k_frame = ttk.Frame(body)
        self._k_frame.pack(fill="both", expand=True, pady=(2, 2))
        # Placeholder inicial: label centrado con la consigna.
        self._k_placeholder = tk.Label(
            self._k_frame,
            text="◎  Clickeá un elemento\ny luego los PGs del canvas",
            bg=EDU_AXES_BG, fg=EDU_FG_MUTED,
            font=("Segoe UI", 10),
            justify="center",
        )
        self._k_placeholder.pack(expand=True)
        self._mat_k: "Optional[LatexMatrixImage]" = None
        self._lbl_k_title = tk.Label(
            self._k_frame, text="", bg=EDU_AXES_BG, fg=EDU_FG,
            font=("Consolas", 9, "bold"), anchor="center",
        )
        # Se empaqueta on-demand cuando hay matriz.

        # Status (PGs seleccionados)
        self._lbl_status = tk.Label(
            body, text="", bg=EDU_AXES_BG, fg="#ffd54f",
            font=("Consolas", 9, "bold"), anchor="w",
        )
        self._lbl_status.pack(fill="x", padx=4)

        # Cross-reference clickeable a M7 (ensamblaje)
        self._pack_crossref(
            body, "mod07",
            "👉 K_e completo se ENSAMBLA en K global. Ver ⑦ Ensamblaje.",
            wraplength=500,
        )

        self._rebuild_contributions()
        # Estado inicial: TODOS los PGs sumados (la cuadratura "correcta").
        self._selected_pgs = set(range(len(self._contributions)))
        self._refresh_all()

    # ── Hooks de ciclo de vida ─────────────────────────────────────
    def on_activated(self):
        # Click consumer: el MeshCanvas nos consulta antes de su hit-test.
        # Si el click cae cerca de un PG del elemento bajo análisis,
        # toggleamos su selección y consumimos (return True) — el canvas
        # NO ejecuta select_element ni deselecciona el elemento bajo
        # análisis (era la causa del prendido/apagado del panel).
        self._mesh.add_click_consumer(self._click_consumer)
        self._mesh.redraw()

    def on_closed(self):
        try:
            self._mesh.remove_click_consumer(self._click_consumer)
        except Exception:
            pass

    def on_element_selected(self, elem_id):
        if elem_id == self.element_id:
            return
        self.element_id = elem_id
        self.element = self.project.elements.get(elem_id) if self.project else None
        self._rebuild_contributions()
        self._selected_pgs = set(range(len(self._contributions)))
        self._refresh_all()

    # ── Callbacks ──────────────────────────────────────────────────
    def _on_order_change(self):
        try:
            self._order = int(self._var_order.get().split("×")[0])
        except (ValueError, AttributeError):
            return
        self._rebuild_contributions()
        self._selected_pgs = set(range(len(self._contributions)))
        self._refresh_all()

    def _on_canvas_click_consume(self, event) -> bool:
        """Click consumer: hit-test contra los PGs del elemento bajo análisis.

        Si el click cae dentro de `_SNAP_PX` de un PG, toggle ese PG en
        `_selected_pgs` (suma o quita su contribución a k_e) y devuelve
        True (consumimos el click). Caso contrario False — el canvas
        ejecuta su hit-test estándar y el alumno puede cambiar de elemento.
        """
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
        best_idx = -1
        best_dpx = float("inf")
        et = self._element_type()
        for idx, (xi, eta) in enumerate(pts):
            xy = natural_to_physical(float(xi), float(eta), coords, et)
            sx, sy = self._mesh.world_to_screen(float(xy[0]), float(xy[1]))
            d = math.hypot(sx - event.x, sy - event.y)
            if d < best_dpx:
                best_dpx = d
                best_idx = idx
        if best_idx < 0 or best_dpx > _SNAP_PX:
            return False
        if best_idx in self._selected_pgs:
            self._selected_pgs.discard(best_idx)
        else:
            self._selected_pgs.add(best_idx)
        self._refresh_all()
        return True

    # ── Capa educativa sobre el canvas: PGs interactivos ───────────
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
        # Glifo unificado:
        #   • PG sumado a k_e → base dorado (GAUSS_ACTIVE).
        #   • PG excluido por la cuadratura activa → ghost gris dashed.
        # Sin labels `pgN`: la dicotomía dorado/gris-dashed comunica el
        # estado de cada PG de forma inequívoca. Repetir el texto en cada
        # PG saturaba la lectura del canvas (sobre todo en Q9 con 9 PGs).
        # El alumno identifica los PGs por su POSICIÓN dentro del elemento
        # — el orden canónico (pg1=lower-left, etc.) es estándar FEM.
        for idx, (xi, eta) in enumerate(pts):
            xy = natural_to_physical(float(xi), float(eta), coords, et)
            sx, sy = mesh.world_to_screen(float(xy[0]), float(xy[1]))
            if idx in self._selected_pgs:
                draw_gauss_base(
                    mesh.canvas, sx, sy, label=None, tag=_TAG,
                    color=GAUSS_ACTIVE,
                )
            else:
                draw_gauss_ghost(mesh.canvas, sx, sy, tag=_TAG)

    # ── Cómputo de contribuciones individuales ─────────────────────
    def _element_type(self) -> str:
        """Constante canónica del project (`ELEMENT_Q4`/`ELEMENT_Q9`)."""
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
                "detJ": float(detJ),
                "contrib": contrib,
            })
        self._contributions = contribs

    def _node_coords(self) -> Optional[np.ndarray]:
        if self.project and self.element:
            try:
                return np.array([
                    [self.project.nodes[nid].x, self.project.nodes[nid].y]
                    for nid in self.element.node_ids
                ], dtype=float)
            except KeyError:
                return None
        return None

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

    # ── Render ─────────────────────────────────────────────────────
    def _refresh_all(self):
        self._refresh_warning()
        # Cuadrado natural matplotlib eliminado — el GaussCoordReadout
        # arriba ya cumple ese rol con su inset 96px.
        # K_e ahora es un widget Tk (LatexMatrixImage) — sin tight_layout
        # ni draw_idle del canvas mpl (eliminado).
        self._refresh_k_heatmap()
        self._refresh_status()
        self._refresh_readout()
        # Repintar la capa overlay sobre el canvas (PGs cambian de color).
        try:
            self._mesh.redraw()
        except Exception:
            pass

    def _refresh_readout(self):
        """Actualiza el cuadrado natural inset + readout de coords con el
        último PG clickeado por el usuario. Si no hay ninguno seleccionado,
        muestra estado vacío."""
        if getattr(self, "_readout", None) is None:
            return
        if not self._selected_pgs or not self._contributions:
            self._readout.set_state(
                order=self._order, etype=self._element_type(),
                selected_index=None, xi=0.0, eta=0.0, physical=None,
            )
            return
        idx = max(self._selected_pgs)
        c = self._contributions[idx]
        xi, eta = c["xi"], c["eta"]
        # Físico (x, y) del PG bajo el mapeo del elemento actual.
        physical = None
        coords = self._node_coords()
        if coords is not None and self.element is not None:
            try:
                n_nodes = self.element.num_nodes
                xy = natural_to_physical(
                    xi, eta, coords[:n_nodes], self._element_type(),
                )
                physical = (float(xy[0]), float(xy[1]))
            except Exception:
                physical = None
        self._readout.set_state(
            order=self._order, etype=self._element_type(),
            selected_index=idx, xi=xi, eta=eta, physical=physical,
        )

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
            elif n_sel == 0:
                self._lbl_warning.configure(
                    text="◎ Clickeá los PGs sobre el elemento para sumarlos",
                    fg=EDU_FG_MUTED,
                )
            else:
                self._lbl_warning.configure(text="")
        except tk.TclError:
            pass

    def _refresh_k_heatmap(self):
        """Render de k_e como `LatexMatrixImage`. Para Q4 (8x8) la matriz
        sale tipo "documento LaTeX"; para Q9 (18x18) el auto-shrink de
        `render_matrix_image` reduce el fontsize y agrega thin spacing
        para que entre.

        Esta version usa el widget Tk (mismo patron que `B` en M4) en
        lugar de un axes matplotlib + `OffsetImage`: el widget mantiene
        su POSICION estable entre updates (el axes movia la matriz a
        cada cambio de contribuciones por el zoom-fit recomputado)."""
        n_pg = len(self._contributions)
        n_sel = len(self._selected_pgs)

        # Estado vacio / sin seleccion → mostrar placeholder, sacar matriz.
        if self.element is None or not self._contributions \
                or n_sel == 0:
            placeholder_text = (
                "◎  Clickeá un elemento\ny luego los PGs del canvas"
                if (self.element is None or not self._contributions)
                else "k_e = 0\nClickeá PGs sobre el elemento"
            )
            self._show_k_placeholder(placeholder_text)
            return

        K = self._k_from_selection()
        if K is None:
            self._show_k_placeholder("k_e = 0")
            return

        # Sin factoring 10^n: el alumno ve los valores raw de k_e (mas
        # honesto pedagogicamente y no introduce escalas confusas que
        # convierten 180 -> "1.8e+02"). Formato `{:.0f}` mantiene
        # numeros enteros sin notacion cientifica para cualquier escala
        # razonable de K_e (kN/m, N/m, etc.).
        prefix = r"\mathbf{k}_e = "
        fs_base = 14 if K.shape[0] <= 12 else 11
        title = f"k_e  ·  {n_sel}/{n_pg} pg"
        self._show_k_matrix(K, prefix=prefix, fs=fs_base, title=title)

    def _show_k_placeholder(self, text: str) -> None:
        """Muestra el label-placeholder y oculta la matriz."""
        if self._mat_k is not None:
            try:
                self._mat_k.pack_forget()
            except tk.TclError:
                pass
        try:
            self._lbl_k_title.pack_forget()
        except tk.TclError:
            pass
        try:
            self._k_placeholder.configure(text=text)
            if not self._k_placeholder.winfo_ismapped():
                self._k_placeholder.pack(expand=True)
        except tk.TclError:
            pass

    def _show_k_matrix(self, Kn: np.ndarray, *, prefix: str,
                       fs: int, title: str) -> None:
        """Muestra (o re-muestra) la matriz k_e con `set_matrix`. Crea
        el widget la primera vez; despues solo actualiza in-place."""
        try:
            self._k_placeholder.pack_forget()
        except tk.TclError:
            pass
        if self._mat_k is None:
            # Lazy create: la primera vez que hay matriz. `{:.0f}` mantiene
            # los valores raw de k_e como enteros (sin factor 10^n y sin
            # notacion cientifica) - mas honesto pedagogicamente.
            self._mat_k = LatexMatrixImage(
                self._k_frame, matrix=Kn,
                fmt="{:.0f}", fontsize=fs, prefix=prefix,
                cache_values=False,
            )
        else:
            # Actualizacion in-place — el widget mantiene su posicion.
            self._mat_k.set_style(fontsize=fs)
            self._mat_k.set_matrix(Kn, prefix=prefix)
        try:
            if not self._lbl_k_title.winfo_ismapped():
                self._lbl_k_title.pack(fill="x", pady=(2, 0))
            self._lbl_k_title.configure(text=title)
            if not self._mat_k.winfo_ismapped():
                self._mat_k.pack(anchor="center", pady=(4, 4))
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
                self._lbl_status.configure(
                    text=f"Σ 0/{n_total} pg"
                )
        except tk.TclError:
            pass
