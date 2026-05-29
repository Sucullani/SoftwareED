"""
Módulo 2 — Jacobiano  J(ξ, η)  y su determinante  det J(ξ, η)

Modo Overlay sobre el MeshCanvas compartido (propuesta UX 2026).

Por qué este módulo es independiente:
    El Jacobiano es el concepto que articula M1 (mapeo) con M4 (matriz B)
    y M5 (rigidez K). Saber QUÉ es det J — y verlo como una SUPERFICIE
    sobre el cuadrado natural — es la herramienta más directa para
    diagnosticar elementos distorsionados / degenerados. M1 lo introdujo
    como apariencia; M2 lo trata como objeto en sí.

Diseño:
    1. Capa en el canvas: pinta cada punto de Gauss con un parche
       coloreado por det J en ese punto. Si det J cambia de signo, el
       elemento se marca con un anillo rojo (degenerado).
    2. Overlay flotante: superficie 3D de det J(ξ, η) arriba + toggle
       Fórmula ↔ Valores abajo (mismo patrón que M4 con la matriz B).
    3. Click en el canvas: si snapa a un Gauss del elemento bajo
       análisis, marca el punto rojo sobre la superficie 3D y refresca
       los valores numéricos (J, det J, J⁻¹).
    4. Cambio de elemento: click sobre otro elemento → el módulo cambia
       el target. El alumno compara distintas geometrías sin abrir y
       cerrar diálogos.

Pedagogía:
    El alumno SIENTE la distorsión: un elemento rectangular alineado
    produce una superficie plana (det J constante); un elemento muy
    distorsionado produce una superficie alabeada que en casos malos
    cruza el plano z=0. Esa última imagen es el diagnóstico más
    convincente para validar la calidad de la malla (relaciona con M0).
"""

from __future__ import annotations

from typing import Optional, Tuple

import math
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from education.overlay_module import CanvasOverlayModule
from education.components import (
    FormulaValueBlocksToggle, LatexMatrixImage, LatexExpressionImage,
    GaussCoordReadout, natural_to_physical, element_coords,
)
from education.components.iso_inverse import iso_inverse_map
from education.components.gauss_glyph import (
    draw_gauss_filled_by_value, draw_gauss_halo, draw_gauss_free_point,
    lerp_hex, GAUSS_CANONICAL, GAUSS_HALO,
)
from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian
from fem.gauss_quadrature import get_gauss_points_for_element
from config.settings import (
    ELEMENT_Q4, ELEMENT_Q9,
    JACOBIAN_MIN_DETERMINANT,
    HEALTH_OK_COLOR, HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR,
    EDU_FIG_BG, EDU_AXES_BG, EDU_LABEL_BG, EDU_SURFACE_LO_COLOR,
    EDU_FREE_POINT_COLOR,
)


_TAG = "edu_m2_jac"
# Paleta de la superficie 3D y del campo de PGs. El cian alto reusa la
# constante canónica del glifo (un solo color para "punto Gauss sano" en
# todo el proyecto); el naranja bajo es alarma de degeneración.
_C_SURFACE_HI = GAUSS_CANONICAL       # cian claro (det J grande sano)
_C_SURFACE_LO = EDU_SURFACE_LO_COLOR  # naranja-rojo (det J cerca de 0 o negativo)
_C_MARKER     = GAUSS_HALO            # naranja — punto seleccionado (halo unificado)


class JacobianModule(CanvasOverlayModule):
    """M2: superficie 3D de det J + toggle fórmula/valores + Gauss en canvas."""

    TITLE = "②  Jacobiano  det J(ξ, η)"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 540
    OVERLAY_HEIGHT = None  # auto

    SNAP_PX = 22
    GRID_RES = 28           # densidad de la superficie 3D

    def __init__(self, main_window, project, element_id):
        # Punto natural actual y, si corresponde, índice del Gauss snapped.
        self._xi = 0.0
        self._eta = 0.0
        self._gauss_index: Optional[int] = None

        # Widgets construidos en build_overlay
        self._fig: Optional[Figure] = None
        self._ax_3d = None
        self._canvas_mpl: Optional[FigureCanvasTkAgg] = None
        self._toggle: Optional[FormulaValueBlocksToggle] = None
        self._readout: Optional[GaussCoordReadout] = None
        self._mat_values: Optional[LatexMatrixImage] = None
        self._mat_formula: Optional[LatexMatrixImage] = None
        self._lbl_values_title: Optional[tk.Label] = None
        self._lbl_warning: Optional[ttk.Label] = None
        # Narrativa de transformación: estado del último click (snap a PG
        # vs libre). Determina color del title de valores.
        self._free_point = False    # True si el último click NO snapeó a PG

        # Click consumer registrado en el MeshCanvas para snap a Gauss
        # del elemento bajo análisis. Bound method (no closure) — el
        # registry de consumers compara por identidad para idempotencia
        # y deregister; bound methods son comparables por __self__ + __func__.
        self._click_consumer = self._on_canvas_click_consume
        # Handle del refresh debounced (cancelable).
        self._refresh_after_id: Optional[str] = None
        # Cache de la superficie det J(ξ,η): la malla Z solo depende del
        # ELEMENTO, no del punto (ξ,η) seleccionado. Cachearla permite que
        # el drag dentro del cuadrado natural (que mueve solo el marcador)
        # no recompute las 28×28 evaluaciones de det J en cada frame.
        # Clave: (id_elemento, hash de coords). Valor: (XI, ET, Z, zmax).
        self._surf_cache: Optional[tuple] = None
        self._surf_cache_key = None

        super().__init__(main_window, project, element_id)

    # ── Tipo de elemento (auto) ────────────────────────────────────
    @property
    def element_type(self) -> str:
        if self.element is not None and getattr(self.element, "num_nodes", 0) == 9:
            return ELEMENT_Q9
        return getattr(self.project, "element_type", None) or ELEMENT_Q4

    @property
    def n_nodes(self) -> int:
        return 9 if self.element_type == ELEMENT_Q9 else 4

    # ── Construcción del overlay flotante (compacto UX 2026) ───────
    def build_overlay(self, body):
        # Sin chip narrativo: el título del overlay ("② Jacobiano det J(ξ, η)")
        # + la fórmula del toggle + el crossref al pie ya orientan al alumno.
        # El warning aparece SOLO si algún det J ≤ 0 (sino vacío, sin chrome).

        # Aviso de elemento degenerado — vacío hasta que algún det J ≤ 0.
        self._lbl_warning = ttk.Label(
            body, text="", font=("Segoe UI", 9, "bold"),
            foreground=HEALTH_ERROR_COLOR, wraplength=500, justify="left",
        )
        self._lbl_warning.pack(anchor="w", pady=(0, 2))

        # ── Cuadrado natural interactivo — AL TOPE, posición estratégica ──
        # El alumno fija (ξ,η) clickeando AQUÍ o clickeando el elemento
        # físico del canvas: dos espacios, un mismo punto. Esto materializa
        # que J se evalúa SIEMPRE en el cuadrado natural (ξ,η), aunque el
        # elemento viva en (x,y). El marcador se mueve en ambos a la vez.
        # `marker_coords=True`: cuadrado natural CENTRADO, sin readout de
        # texto aparte — la coord (ξ,η) viaja pegada al marcador dentro del
        # cuadrado, y la (x,y) física se dibuja pegada al punto en el canvas
        # (ver `draw_canvas_layer`). Cada coordenada vive en su elemento.
        self._readout = GaussCoordReadout(
            body, order=self._gauss_order(), etype=self.element_type,
            interactive=True, on_pick=self._on_natural_pick,
            title="J se evalúa en el cuadrado natural (ξ, η):",
            marker_coords=True, side=140,
        )
        self._readout.pack(fill="x", pady=(0, 4))

        # ── Superficie 3D de det J(ξ, η) ──────────────────────────
        plot_frame = ttk.Frame(body)
        plot_frame.pack(fill="both", expand=True)

        # Altura reducida (antes 3.0 → 2.2): la superficie de det J suele ser
        # un rango angosto que dejaba mucho cubo 3D vacío y empujaba el mensaje
        # inferior (crossref) fuera de vista. Combinado con el `set_zlim`
        # ceñido de `_draw_surface_3d`, la superficie llena el panel y todo el
        # overlay (incluido el crossref) entra en pantalla.
        self._fig = Figure(figsize=(5.6, 2.2), dpi=100)
        self._ax_3d = self._fig.add_subplot(111, projection="3d")
        from education.components.edu_plot_style import (
            apply_edu_style_figure, apply_edu_style_3d,
        )
        apply_edu_style_figure(self._fig)
        apply_edu_style_3d(self._ax_3d)

        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=plot_frame)
        self._canvas_mpl.get_tk_widget().pack(fill="both", expand=True)

        # ── Toggle Fórmula ↔ Valores (frames Tk, no axes compartido) ──
        self._toggle = FormulaValueBlocksToggle(
            body,
            build_formula=self._build_formula_panel,
            build_values=self._build_values_panel,
            initial=FormulaValueBlocksToggle.MODE_VALUES,
        )
        self._toggle.pack(fill="x", pady=(2, 0))

        # Cross-reference clickeable a M4 (la matriz B).
        self._pack_crossref(
            body, "mod04",
            "👉 det J > 0 garantiza que la matriz B (④) sea computable "
            "en este elemento.",
            wraplength=500,
        )

        self._refresh_status()

    def _gauss_order(self) -> int:
        """Orden de cuadratura típica del element_type (Q4→2, Q9→3)."""
        return 3 if self.n_nodes == 9 else 2

    # Resolución del heatmap continuo (celdas por lado en el cuadrado
    # natural). 12 = 144 celdas: suficiente para mostrar gradientes
    # suaves en elementos distorsionados sin saturar el canvas tk.
    _HEATMAP_N = 12

    # ── Capa educativa sobre el canvas (heatmap continuo + PGs) ──
    def draw_canvas_layer(self, mesh):
        mesh.canvas.delete(_TAG)
        if self.element is None or self.project is None:
            return
        coords = self._coords_macro()
        if coords is None or len(coords) < 4:
            return

        pts_natural, _ = get_gauss_points_for_element(self.element_type)
        _, dN_fn = get_shape_functions(self.element_type)

        # ── 1) Heatmap continuo det J(x,y) sobre TODO el elemento ──
        # En lugar de mostrar det J solo en los 4-9 PGs (que se sienten
        # como muestras aisladas), pintamos el CAMPO completo det J(x,y)
        # como una grilla N×N de quads pequeños mapeados desde el
        # cuadrado natural. El alumno ve GRADIENTES de distorsión:
        # constante para Q4 rectangulares, suave para trapecios moderados,
        # con zonas rojas para elementos casi-degenerados.
        self._draw_jacobian_heatmap(mesh, coords, dN_fn)

        # ── 2) PGs sobre el heatmap (anclas discretas con valor numérico) ──
        dets = []
        for idx, (xi, eta) in enumerate(pts_natural):
            try:
                _, dJ, _ = compute_jacobian(dN_fn(xi, eta),
                                              coords[: self.n_nodes])
            except Exception:
                dJ = 0.0
            dets.append(dJ)

        dets_arr = np.array(dets, dtype=float)
        # Para el coloreado: normalizar contra el máximo positivo.
        d_max = max(float(dets_arr.max()), 1e-12)
        for idx, ((xi, eta), dJ) in enumerate(zip(pts_natural, dets)):
            xy = natural_to_physical(xi, eta, coords[: self.n_nodes],
                                       self.element_type)
            sx, sy = mesh.world_to_screen(xy[0], xy[1])
            # Color del parche según signo y magnitud relativa.
            if dJ <= JACOBIAN_MIN_DETERMINANT:
                color = _C_SURFACE_LO
            else:
                t = max(0.0, min(1.0, dJ / d_max))
                color = lerp_hex(_C_SURFACE_LO, _C_SURFACE_HI, t)
            # M2: variante "filled-por-valor" del glifo unificado. El COLOR
            # es el campo (det J); el label numérico refuerza la lectura.
            draw_gauss_filled_by_value(
                mesh.canvas, sx, sy, f"{dJ:.2g}", tag=_TAG, color=color,
            )
            if idx == self._gauss_index:
                # Halo de selección unificado (mismo naranja/cyan que M4/M5b).
                draw_gauss_halo(mesh.canvas, sx, sy, tag=_TAG, color=_C_MARKER)

        # Marcador del punto LIBRE en físico (modo continuo).
        # Bidireccionalidad canvas↔overlay: el alumno ve dónde cayó su
        # click en el canvas, y simultáneamente el toggle de la matriz J
        # muestra los valores en ese (ξ, η).
        if self._gauss_index is None and self._free_point:
            try:
                xy_free = natural_to_physical(
                    self._xi, self._eta, coords[: self.n_nodes],
                    self.element_type,
                )
                fx, fy = mesh.world_to_screen(float(xy_free[0]),
                                                float(xy_free[1]))
                # Glifo unificado de punto LIBRE (halo dashed + disco con
                # outline blanco) — distinto de los PGs (filled por valor) y
                # de la selección (halo cyan limpio). Color desde settings.
                draw_gauss_free_point(mesh.canvas, fx, fy, tag=_TAG)
            except Exception:
                pass

        # Coordenada (x, y) PEGADA al marcador físico del punto seleccionado.
        # Complementa la (ξ,η) que viaja con el marcador del cuadrado natural
        # del overlay: cada coordenada vive en su propio espacio, junto a su
        # punto. Caja de fondo para legibilidad sobre el heatmap.
        if (self._gauss_index is not None) or self._free_point:
            try:
                xy_sel = natural_to_physical(
                    self._xi, self._eta, coords[: self.n_nodes],
                    self.element_type,
                )
                px, py = mesh.world_to_screen(float(xy_sel[0]), float(xy_sel[1]))
                lbl_color = (_C_MARKER if self._gauss_index is not None
                             else EDU_FREE_POINT_COLOR)
                txt = f"(x, y) = ({xy_sel[0]:.3g}, {xy_sel[1]:.3g})"
                tid = mesh.canvas.create_text(
                    px + 12, py - 12, text=txt, fill=lbl_color,
                    font=("Consolas", 8, "bold"), anchor="w", tags=_TAG,
                )
                bb = mesh.canvas.bbox(tid)
                if bb:
                    mesh.canvas.create_rectangle(
                        bb[0] - 3, bb[1] - 1, bb[2] + 3, bb[3] + 1,
                        fill=EDU_LABEL_BG, outline=lbl_color, width=1, tags=_TAG,
                    )
                    mesh.canvas.tag_raise(tid)
            except Exception:
                pass

        # Si algún det J ≤ 0, marcar el elemento con un anillo rojo grueso.
        if any(d <= JACOBIAN_MIN_DETERMINANT for d in dets):
            # Borde del polígono macro del elemento (4 vértices).
            pts = []
            for i in range(4):
                sx, sy = mesh.world_to_screen(coords[i, 0], coords[i, 1])
                pts.extend([sx, sy])
            pts.extend(pts[:2])  # cerrar
            mesh.canvas.create_line(
                *pts, fill=HEALTH_ERROR_COLOR, width=2.6,
                dash=(5, 3), tags=_TAG,
            )

    # ── Heatmap continuo det J(x,y) ────────────────────────────────
    def _draw_jacobian_heatmap(self, mesh, coords, dN_fn) -> None:
        """Pinta el elemento físico como una grilla N×N de quads coloreados
        por det J interpolado. Mismo colormap divergente que la superficie
        3D del overlay (rojo = degenerado/bajo, cyan = sano) — el alumno
        cruza la mirada entre overlay y canvas con la misma paleta.

        Performance: N=12 ⇒ 144 quads × 4 mapeos = 576 evaluaciones de
        shape functions por redraw. <5 ms en hardware típico; aceptable
        para mantener el campo vivo en cada cambio de elemento. Si se
        necesita más velocidad, bajar N a 8 (64 quads, gradientes igual
        legibles)."""
        N = self._HEATMAP_N
        nn = self.n_nodes

        # Pre-computar det J en TODAS las celdas (centros) para
        # normalización global. Una sola pasada — sin esto el coloreado
        # depende del orden de visita y produce flicker entre redraws.
        cell_dets = np.zeros((N, N), dtype=float)
        for i in range(N):
            for j in range(N):
                xi_c  = -1.0 + (2.0 * (i + 0.5)) / N
                eta_c = -1.0 + (2.0 * (j + 0.5)) / N
                try:
                    _, dJ, _ = compute_jacobian(
                        dN_fn(xi_c, eta_c), coords[: nn]
                    )
                except Exception:
                    dJ = 0.0
                cell_dets[i, j] = dJ

        d_max_pos = float(cell_dets[cell_dets > 0].max()) \
            if (cell_dets > 0).any() else 1.0
        d_max_pos = max(d_max_pos, 1e-12)

        # Mapear las (N+1)² esquinas del grid natural al espacio físico
        # una sola vez (reuso entre celdas vecinas).
        xs_screen = np.zeros((N + 1, N + 1), dtype=float)
        ys_screen = np.zeros((N + 1, N + 1), dtype=float)
        for i in range(N + 1):
            for j in range(N + 1):
                xi  = -1.0 + 2.0 * i / N
                eta = -1.0 + 2.0 * j / N
                xy = natural_to_physical(
                    xi, eta, coords[: nn], self.element_type,
                )
                sx, sy = mesh.world_to_screen(float(xy[0]), float(xy[1]))
                xs_screen[i, j] = sx
                ys_screen[i, j] = sy

        # Dibujar quads coloreados. Stipple gray50 deja respirar la
        # geometría subyacente del MeshCanvas (BC symbols, loads, etc.)
        # — el heatmap es ambiente, no opaco.
        for i in range(N):
            for j in range(N):
                dJ = cell_dets[i, j]
                if dJ <= JACOBIAN_MIN_DETERMINANT:
                    color = _C_SURFACE_LO
                else:
                    t = max(0.0, min(1.0, dJ / d_max_pos))
                    color = lerp_hex(_C_SURFACE_LO, _C_SURFACE_HI, t)
                # Corners del quad en orden CCW para tk.Canvas
                x0 = xs_screen[i,     j];     y0 = ys_screen[i,     j]
                x1 = xs_screen[i + 1, j];     y1 = ys_screen[i + 1, j]
                x2 = xs_screen[i + 1, j + 1]; y2 = ys_screen[i + 1, j + 1]
                x3 = xs_screen[i,     j + 1]; y3 = ys_screen[i,     j + 1]
                mesh.canvas.create_polygon(
                    x0, y0, x1, y1, x2, y2, x3, y3,
                    fill=color, outline="", stipple="gray50",
                    tags=_TAG,
                )

    # ── Hooks de ciclo de vida ─────────────────────────────────────
    def on_activated(self):
        # Registramos un click consumer en el MeshCanvas. Cuando el alumno
        # clickee, el canvas nos pregunta PRIMERO si el click cae cerca de
        # un Gauss del elemento bajo análisis; si sí, consumimos (return
        # True) y el canvas NO ejecuta su hit-test estándar — la selección
        # del elemento se preserva, el panel de módulos no oscila.
        self._mesh.add_click_consumer(self._click_consumer)
        self._refresh_all()

    def on_closed(self):
        try:
            self._mesh.remove_click_consumer(self._click_consumer)
        except Exception:
            pass
        # Cancelar refresh debounced pendiente para no disparar render
        # sobre un overlay ya cerrado.
        if self._refresh_after_id is not None:
            try:
                self._mesh.canvas.after_cancel(self._refresh_after_id)
            except Exception:
                pass
            self._refresh_after_id = None

    def on_element_selected(self, elem_id):
        if elem_id == self.element_id:
            return
        self.element_id = elem_id
        self.element = self.project.elements.get(elem_id) if self.project else None
        self._xi, self._eta = 0.0, 0.0
        self._gauss_index = None
        self._free_point = False
        # Debounce: la superficie 3D de matplotlib es la operación más
        # cara del módulo (~150 ms). Si el alumno clickea varios elementos
        # rápido, encadenaríamos N render pesados. Diferimos via after()
        # cancelable: el último click gana.
        self._schedule_refresh()

    def _schedule_refresh(self, delay_ms: int = 80) -> None:
        """Cola un refresh debounced. Cancela el pendiente si lo hay."""
        if self._refresh_after_id is not None:
            try:
                self._mesh.canvas.after_cancel(self._refresh_after_id)
            except Exception:
                pass
            self._refresh_after_id = None
        try:
            self._refresh_after_id = self._mesh.canvas.after(
                delay_ms, self._do_refresh_all
            )
        except Exception:
            # Sin event loop disponible: caer a refresh sincrónico.
            self._do_refresh_all()

    def _do_refresh_all(self) -> None:
        """Punto de entrada del refresh diferido — limpia el handle."""
        self._refresh_after_id = None
        self._refresh_all()

    # ── Click consumer: snap a Gauss + free point en físico ─────
    def _on_canvas_click_consume(self, event) -> bool:
        """Consumer registrado en MeshCanvas. Dos modos en cascada:

        1. **Snap a PG**: si el click cae dentro de `SNAP_PX` de un PG del
           elemento bajo análisis → snap, modo "discreto" (cyan).
        2. **Free probe en físico**: si no hay snap pero el click cae
           DENTRO del elemento (Newton-R converge a `(ξ,η) ∈ [-1,1]²`) →
           free point, modo "continuo" (rojo apagado). Pedagógicamente:
           refuerza que J existe como función continua, no solo en PGs.
        3. **Miss**: cualquier otro caso → False, el canvas decide
           (cambio de elemento, deselección, etc.)."""
        if self.element is None:
            return False
        coords = self._coords_macro()
        if coords is None or len(coords) < 4:
            return False

        # 1) Snap a PG.
        pts_natural, _ = get_gauss_points_for_element(self.element_type)
        best_idx, best_dpx = -1, float("inf")
        for idx, (xi, eta) in enumerate(pts_natural):
            xy = natural_to_physical(xi, eta, coords[: self.n_nodes],
                                       self.element_type)
            sx, sy = self._mesh.world_to_screen(xy[0], xy[1])
            d = math.hypot(sx - event.x, sy - event.y)
            if d < best_dpx:
                best_dpx, best_idx = d, idx
        if best_idx >= 0 and best_dpx < self.SNAP_PX:
            xi, eta = pts_natural[best_idx]
            self._xi, self._eta = float(xi), float(eta)
            self._gauss_index = best_idx
            self._free_point = False
            self._refresh_all()
            return True

        # 2) Free probe en físico: convertir click → world → inverse map.
        wx, wy = self._mesh.screen_to_world(event.x, event.y)
        try:
            mapped = iso_inverse_map(
                wx, wy, coords[: self.n_nodes], self.element_type,
            )
        except Exception:
            mapped = None
        if mapped is None:
            return False
        xi, eta = mapped
        self._xi, self._eta = float(xi), float(eta)
        self._gauss_index = None
        self._free_point = True
        self._refresh_all()
        return True

    # ── Pick desde el cuadrado natural interactivo ─────────────────
    def _match_gauss_index(self, xi: float, eta: float,
                            tol: float = 1e-3) -> Optional[int]:
        """Índice del PG del elemento cuyas coords (ξ,η) matchean (xi,eta),
        o None. Matchea por COORDENADA (no por orden) — robusto al ordering
        del grid del widget vs el de fem.gauss_quadrature."""
        pts_natural, _ = get_gauss_points_for_element(self.element_type)
        for idx, (gx, gy) in enumerate(pts_natural):
            if abs(xi - gx) < tol and abs(eta - gy) < tol:
                return idx
        return None

    def _on_natural_pick(self, xi: float, eta: float) -> None:
        """El alumno clickeó/arrastró DENTRO del cuadrado natural del readout.

        El widget ya aplicó snap PRIORITARIO a PG: si (xi,eta) coincide con un
        punto de Gauss del elemento, lo tratamos como selección discreta de
        ese PG (mismo estado que clickear el PG en el canvas físico); si no,
        es un punto libre continuo. Bidireccionalidad total: el marcador y el
        halo del PG aparecen también sobre el elemento físico. La superficie
        3D NO se recomputa (cache); solo el marcador y la matriz J cambian."""
        self._xi, self._eta = float(xi), float(eta)
        idx = self._match_gauss_index(xi, eta)
        self._gauss_index = idx
        self._free_point = (idx is None)
        self._refresh_all()

    # ── Refresh general ─────────────────────────────────────────────
    def _refresh_all(self):
        self._draw_surface_3d()
        # Live-update de la matriz J numérica (sin re-construir widgets).
        if self._mat_values is not None:
            try:
                J = self._compute_jacobian_value()
                if J is not None:
                    self._mat_values.set_matrix(J)
            except Exception:
                pass
        # La matriz simbólica es estática — no requiere update.
        self._refresh_status()
        self._refresh_warning()
        self._mesh.redraw()

    def _refresh_status(self):
        coords = self._coords_macro()
        physical = None
        if coords is not None:
            try:
                xy = natural_to_physical(
                    self._xi, self._eta, coords[: self.n_nodes],
                    self.element_type,
                )
                physical = (float(xy[0]), float(xy[1]))
            except Exception:
                physical = None

        # Readout dual: cuadrado natural + coords + (x, y) — ÚNICO lugar donde
        # viven las coords (ξ,η)/(x,y) del punto.
        if self._readout is not None:
            self._readout.set_state(
                order=self._gauss_order(),
                etype=self.element_type,
                selected_index=self._gauss_index,
                xi=self._xi, eta=self._eta,
                physical=physical,
            )
        # Título de los valores: SOLO el modo. Las coords están en el readout
        # y det J en la etiqueta anclada al marcador 3D — sin repetir nada.
        if self._lbl_values_title is not None:
            if self._gauss_index is not None:
                mode_tag, fg = f"pg{self._gauss_index + 1}", GAUSS_CANONICAL
            elif self._free_point:
                mode_tag, fg = "punto libre", EDU_FREE_POINT_COLOR
            else:
                mode_tag, fg = "centro del elemento", "#dcdcdc"
            self._lbl_values_title.configure(text=f"J  en  {mode_tag}", fg=fg)

    def _refresh_warning(self):
        if self._lbl_warning is None or self.element is None:
            return
        coords = self._coords_macro()
        if coords is None:
            self._lbl_warning.configure(text="")
            return
        pts_natural, _ = get_gauss_points_for_element(self.element_type)
        _, dN_fn = get_shape_functions(self.element_type)
        bad = []
        all_dets = []
        for idx, (xi, eta) in enumerate(pts_natural):
            try:
                _, dJ, _ = compute_jacobian(dN_fn(xi, eta),
                                              coords[: self.n_nodes])
            except Exception:
                dJ = 0.0
            all_dets.append(dJ)
            if dJ <= JACOBIAN_MIN_DETERMINANT:
                bad.append((idx, dJ))
        if not bad:
            # Feedback positivo: el alumno aprende el invariante "det J > 0
            # en todos los PGs ⇒ mapeo inversible ⇒ B computable" recién
            # cuando lo ve afirmado. Antes el panel vacío se confundía con
            # "no hay nada que decir"; ahora dice activamente "todo bien".
            d_min = min(all_dets)
            d_max = max(all_dets)
            txt = (f"✓ det J > 0 en los {len(all_dets)} PGs  "
                   f"(min = {d_min:.3g} · max = {d_max:.3g})  "
                   f"— mapeo inversible.")
            self._lbl_warning.configure(text=txt,
                                          foreground=HEALTH_OK_COLOR)
        else:
            txt = ("⚠ Elemento degenerado: det J ≤ 0 en "
                    + ", ".join(f"pg{i+1} ({dJ:.2g})" for i, dJ in bad)
                    + ". Reordená los nodos en CCW o corregí la geometría.")
            self._lbl_warning.configure(text=txt,
                                          foreground=HEALTH_ERROR_COLOR)

    # ── Superficie 3D de det J(ξ, η) ───────────────────────────────
    def _draw_surface_3d(self):
        if self._ax_3d is None:
            return
        ax = self._ax_3d
        ax.clear()
        # Re-aplicar estilo edu (clear() resetea facecolor + ticks).
        from education.components.edu_plot_style import (
            apply_edu_style_3d, EDU_PLOT_LABEL_COLOR,
        )
        apply_edu_style_3d(ax)

        coords = self._coords_macro()
        if coords is None or len(coords) < 4:
            ax.text2D(0.5, 0.5, "(sin elemento)",
                       transform=ax.transAxes, ha="center", va="center",
                       color="#7a7e88", fontsize=9)
            self._canvas_mpl.draw_idle()
            return

        # Cache de la superficie por elemento+geometría: Z(ξ,η) NO depende
        # del punto seleccionado, así que el drag dentro del cuadrado
        # natural reusa la malla y solo re-pinta el marcador.
        cache_key = (self.element_id, self.element_type,
                     coords[: self.n_nodes].tobytes())
        if self._surf_cache is not None and self._surf_cache_key == cache_key:
            XI, ET, Z, zmax = self._surf_cache
        else:
            _, dN_fn = get_shape_functions(self.element_type)
            xi = np.linspace(-1, 1, self.GRID_RES)
            eta = np.linspace(-1, 1, self.GRID_RES)
            XI, ET = np.meshgrid(xi, eta)
            Z = np.zeros_like(XI)
            for r in range(XI.shape[0]):
                for c in range(XI.shape[1]):
                    try:
                        _, dJ, _ = compute_jacobian(
                            dN_fn(XI[r, c], ET[r, c]),
                            coords[: self.n_nodes],
                        )
                    except Exception:
                        dJ = 0.0
                    Z[r, c] = dJ
            # `coolwarm` divergente en 0 — azul = sano, rojo = problema.
            zmax = max(abs(float(Z.min())), abs(float(Z.max())), 1e-12)
            self._surf_cache = (XI, ET, Z, zmax)
            self._surf_cache_key = cache_key

        # Alpha bajado a 0.78 para que la superficie no domine el panel.
        ax.plot_surface(
            XI, ET, Z, cmap="coolwarm", vmin=-zmax, vmax=zmax,
            edgecolor="none", alpha=0.78, antialiased=True,
        )
        # Plano z=0 (frontera de validez) — linea fina, no agresiva.
        try:
            ax.contour(
                XI, ET, Z, levels=[0.0], zdir="z", offset=float(Z.min()),
                colors=HEALTH_ERROR_COLOR, linewidths=0.9,
            )
        except Exception:
            pass

        # Marcador del punto seleccionado + etiqueta de det J ANCLADA a él
        # (mismo criterio que M1): el valor flota encima del marcador, en vez
        # de vivir en una línea de texto aparte. Es el ÚNICO lugar donde vive
        # det J del punto. Color por modo (PG = naranja halo · libre = rojo).
        # `dN_fn` puede no existir si entramos por la rama de cache.
        z_lo, z_hi = float(Z.min()), float(Z.max())
        span = max(z_hi - z_lo, 1e-9)
        mk = _C_MARKER if self._gauss_index is not None else EDU_FREE_POINT_COLOR
        try:
            _, dN_fn_m = get_shape_functions(self.element_type)
            _, dJ_sel, _ = compute_jacobian(
                dN_fn_m(self._xi, self._eta), coords[: self.n_nodes],
            )
            dJ_sel = float(dJ_sel)
            ax.scatter([self._xi], [self._eta], [dJ_sel],
                        s=42, c=mk, edgecolors="white",
                        linewidths=0.8, depthshade=False, zorder=20)
            ax.text(
                self._xi, self._eta, dJ_sel + max(0.08 * span, 0.12),
                rf"$\det\mathbf{{J}} = {dJ_sel:.4g}$",
                color=mk, fontsize=10, ha="center", va="bottom", zorder=30,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=EDU_LABEL_BG,
                           edgecolor=mk, linewidth=0.8, alpha=0.88),
            )
        except Exception:
            pass

        # z-lim ceñido al rango real de det J (+ sitio arriba para la etiqueta):
        # evita el cubo 3D semivacío con la superficie hundida abajo.
        try:
            ax.set_zlim(z_lo - max(0.10 * span, 0.10),
                        z_hi + max(0.32 * span, 0.32))
        except Exception:
            pass

        ax.set_xlabel("ξ", color=EDU_PLOT_LABEL_COLOR)
        ax.set_ylabel("η", color=EDU_PLOT_LABEL_COLOR)
        try:
            ax.set_zlabel("det J", color=EDU_PLOT_LABEL_COLOR)
        except Exception:
            pass
        try:
            self._fig.tight_layout(pad=0.6)
        except Exception:
            pass
        self._canvas_mpl.draw_idle()

    # ── Builders del toggle (Tk widgets, no axes) ──────────────────
    def _build_formula_panel(self, frame) -> None:
        """Panel de la fórmula simbólica: matriz J + fórmula escalar de det J."""
        # Notación J = ∂(x,y)/∂(ξ,η) según fem.jacobian. Celdas en LaTeX
        # `\dfrac{...}{...}` para que cada derivada parcial salga como
        # fraccion real (numerador/denominador apilado), no como texto
        # plano `∂x/∂ξ`. Dentro del substack `_cell_for_substack_atom`
        # normaliza `\dfrac` → `\frac` para mantener altura compatible.
        cells = [
            [r"\dfrac{\partial x}{\partial \xi}",  r"\dfrac{\partial y}{\partial \xi}"],
            [r"\dfrac{\partial x}{\partial \eta}", r"\dfrac{\partial y}{\partial \eta}"],
        ]
        self._mat_formula = LatexMatrixImage(
            frame, matrix=cells, fmt="{}", fontsize=16,
            prefix=r"\mathbf{J}=", cache_values=True,
        )
        self._mat_formula.pack(anchor="center", pady=(2, 4))
        LatexExpressionImage(
            frame,
            expr=(r"\det\mathbf{J}=\dfrac{\partial x}{\partial \xi}\,"
                  r"\dfrac{\partial y}{\partial \eta}-"
                  r"\dfrac{\partial y}{\partial \xi}\,"
                  r"\dfrac{\partial x}{\partial \eta}"),
            fontsize=12, color="#90caf9",
        ).pack(anchor="center", pady=(0, 2))
        LatexExpressionImage(
            frame,
            expr=(r"\dfrac{\partial x}{\partial \xi}="
                  r"\sum_i \dfrac{\partial N_i}{\partial \xi}\,x_i"),
            fontsize=11, color="#9aa6b5",
        ).pack(anchor="center", pady=(0, 2))

    def _build_values_panel(self, frame) -> None:
        """Panel de valores numéricos: matriz J actualizada en cada cambio."""
        from config.settings import EDU_AXES_BG
        self._lbl_values_title = tk.Label(
            frame, text="", bg=EDU_AXES_BG, fg="#dcdcdc",
            font=("Consolas", 9, "bold"), anchor="center",
        )
        self._lbl_values_title.pack(fill="x", pady=(2, 2))
        J0 = self._compute_jacobian_value()
        self._mat_values = LatexMatrixImage(
            frame, matrix=J0 if J0 is not None else np.eye(2),
            fmt="{:.3g}", fontsize=16, prefix=r"\mathbf{J}=",
            cache_values=False,  # cambia con ξ,η
        )
        self._mat_values.pack(anchor="center", pady=(0, 4))

    def _compute_jacobian_value(self) -> Optional[np.ndarray]:
        """Calcula J(ξ, η) en el punto seleccionado, o None si imposible."""
        coords = self._coords_macro()
        if coords is None:
            return None
        try:
            _, dN_fn = get_shape_functions(self.element_type)
            J, _, _ = compute_jacobian(
                dN_fn(self._xi, self._eta), coords[: self.n_nodes],
            )
            return J
        except Exception:
            return None

    # ── Helpers ────────────────────────────────────────────────────
    def _coords_macro(self) -> Optional[np.ndarray]:
        # Delega al helper compartido (antes duplicado en M1/M2/M4/M5/M7).
        return element_coords(self.project, self.element)
