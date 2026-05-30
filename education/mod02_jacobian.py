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
    ScrollableMatrixImage, fit_matrix_widget, natural_to_physical, element_coords,
)
from education.components.edu_plot_style import (
    apply_edu_style_figure, apply_edu_style_2d, apply_edu_style_3d,
    EDU_PLOT_LABEL_COLOR,
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
    HEALTH_ERROR_COLOR,
    EDU_AXES_BG, EDU_LABEL_BG, EDU_FG, EDU_FG_MUTED,
    EDU_SURFACE_LO_COLOR, EDU_FREE_POINT_COLOR,
    EDU_NATURAL_OUTLINE_COLOR, EDU_NATURAL_AXES_COLOR,
    OVERLAY_ACCENT_BLUE,
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
    # Overlay ANCHO: el cuadrado natural (2D) y la superficie det J (3D) van
    # lado a lado en una sola figura matplotlib (gana altura), así que se
    # necesita más ancho para que la superficie 3D se vea bien. 740 px es
    # SIEMPRE < WINDOW_MIN_WIDTH (1200) → nunca supera la ventana principal,
    # y queda arrastrable, así que no tapa el canvas durante la interacción.
    OVERLAY_WIDTH = 740
    OVERLAY_HEIGHT = None  # auto

    SNAP_PX = 22
    GRID_RES = 28           # densidad de la superficie 3D
    # Tolerancia de snap a PG dentro del cuadrado natural, en coords (ξ,η).
    _SNAP_NAT = 0.16
    # Fuente del panel FÓRMULA (operador, ∂N simbólica, det J) — uniforme en
    # tamaño Y color (azul de acento `OVERLAY_ACCENT_BLUE`), pedido del usuario.
    _FS = 14
    # Fuente del panel VALORES (∂N, Xₑ, J numéricas) — reducida respecto a la
    # fórmula: los números son densos y un punto más chico evita saturar.
    _FS_VAL = 12

    def __init__(self, main_window, project, element_id):
        # Punto natural actual y, si corresponde, índice del Gauss snapped.
        self._xi = 0.0
        self._eta = 0.0
        self._gauss_index: Optional[int] = None

        # Widgets construidos en build_overlay
        self._fig: Optional[Figure] = None
        self._ax_nat = None      # subplot 2D: cuadrado natural (interactivo)
        self._ax_3d = None       # subplot 3D: superficie det J
        self._canvas_mpl: Optional[FigureCanvasTkAgg] = None
        self._toggle: Optional[FormulaValueBlocksToggle] = None
        # Factores numéricos del producto J = ∂N·Xₑ (toggle Valores):
        # ∂N(ξ,η) 2×n (live), Xₑ n×2 (estática), J 2×2 (live). `_fit_matrix`
        # devuelve LatexMatrixImage (si entra) o ScrollableMatrixImage (si no);
        # ambos exponen set_matrix → el refresh es agnóstico al tipo.
        self._mat_dN: Optional[LatexMatrixImage | ScrollableMatrixImage] = None
        self._mat_Xe: Optional[LatexMatrixImage | ScrollableMatrixImage] = None
        self._xe_element_id = None
        self._mat_values: Optional[LatexMatrixImage] = None
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

        # ── Figura: cuadrado natural (2D) | superficie det J (3D) ─────
        # LADO A LADO en una sola figura matplotlib (gana altura vs apilar).
        # El cuadrado natural reemplaza al readout tk: render estilo M1 +
        # selección por click (snap a PG / punto libre). Muestra los PUNTOS
        # DE GAUSS (donde se evalúa J), no los nodos. El alumno fija (ξ,η)
        # clickeando AQUÍ o clickeando el elemento físico del canvas — dos
        # espacios, un mismo punto; el marcador se mueve en ambos.
        plot_frame = ttk.Frame(body)
        plot_frame.pack(fill="both", expand=True)

        fig_w = max(5.4, (self.OVERLAY_WIDTH - 28) / 100.0)
        self._fig = Figure(figsize=(fig_w, 2.5), dpi=100)
        apply_edu_style_figure(self._fig)
        # bottom=0.10 (no 0.04): deja aire para el label del eje ξ del panel
        # 3D, que con el margen chico quedaba recortado contra el borde.
        gs = self._fig.add_gridspec(
            1, 2, width_ratios=[1.0, 1.55], wspace=0.04,
            left=0.04, right=0.97, top=0.90, bottom=0.10,
        )
        self._ax_nat = self._fig.add_subplot(gs[0, 0])
        self._ax_3d = self._fig.add_subplot(gs[0, 1], projection="3d")
        apply_edu_style_2d(self._ax_nat, show_spines=False)
        apply_edu_style_3d(self._ax_3d)

        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=plot_frame)
        self._canvas_mpl.get_tk_widget().pack(fill="both", expand=True)
        # Click en el subplot 2D = elegir el punto (snap a PG o libre).
        self._canvas_mpl.mpl_connect("button_press_event",
                                     self._on_natural_pick_mpl)

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

        # Dibujo inicial de ambos subplots (la malla del canvas la pinta
        # on_activated → _refresh_all tras registrar la capa overlay).
        self._draw_natural_square(self._ax_nat)
        self._draw_surface_3d()
        self._refresh_status()

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

    # ── Cuadrado natural (subplot 2D matplotlib, estilo M1) ────────
    def _draw_natural_square(self, ax) -> None:
        """Dibuja el cuadrado natural (ξ,η) estilo M1: contorno azul, ejes,
        ±1, los PUNTOS DE GAUSS del elemento (donde se evalúa J) y el marcador
        del punto seleccionado con su (ξ,η) pegada. Reemplaza al readout tk."""
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
        # Puntos de Gauss del orden activo (snap targets, donde se evalúa J).
        # El PG SELECCIONADO cambia de color (naranja `_C_MARKER`) al clickearlo
        # — feedback directo de cuál PG está activo; el resto en cian.
        try:
            pts_natural, _ = get_gauss_points_for_element(self.element_type)
            pn = np.array(pts_natural, dtype=float)
            for i, (gx, gy) in enumerate(pn):
                sel = (self._gauss_index == i)
                ax.scatter([gx], [gy], s=86 if sel else 64,
                            c=_C_MARKER if sel else _C_SURFACE_HI,
                            edgecolors="white", linewidths=1.0 if sel else 0.8,
                            zorder=9 if sel else 7)
        except Exception:
            pass
        ax.text(1.0, -1.2, "+1", color=EDU_FG_MUTED, fontsize=7,
                 family="monospace", ha="center", va="top")
        ax.text(-1.0, -1.2, "-1", color=EDU_FG_MUTED, fontsize=7,
                 family="monospace", ha="center", va="top")
        ax.text(1.3, 0.02, "ξ", color=EDU_FG_MUTED, fontsize=9,
                 family="monospace", fontweight="bold", ha="left", va="center")
        ax.text(0.02, 1.3, "η", color=EDU_FG_MUTED, fontsize=9,
                 family="monospace", fontweight="bold", ha="left", va="center")
        ax.set_xlim(-1.45, 1.45); ax.set_ylim(-1.45, 1.45)
        ax.set_title("Cuadrado natural  (ξ, η)",
                      color=EDU_NATURAL_OUTLINE_COLOR, fontsize=9,
                      fontweight="bold", pad=4)
        ax.set_xticks([]); ax.set_yticks([])
        # Marcador del punto seleccionado: halo ring (siempre) + disco SOLO
        # para punto libre (en un PG, el propio PG ya quedó coloreado arriba).
        if (self._gauss_index is not None) or self._free_point:
            mk = (_C_MARKER if self._gauss_index is not None
                  else EDU_FREE_POINT_COLOR)
            ax.scatter([self._xi], [self._eta], s=180, facecolors="none",
                        edgecolors=mk, linewidths=2.0, zorder=10)
            if self._free_point:
                ax.scatter([self._xi], [self._eta], s=32, c=mk, zorder=11)
            to_right = self._xi < 0
            ax.annotate(
                f"({self._xi:.3f}, {self._eta:.3f})", (self._xi, self._eta),
                textcoords="offset points",
                xytext=(8, 8) if to_right else (-8, 8),
                ha="left" if to_right else "right", va="bottom",
                color=mk, fontsize=8, family="monospace",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=EDU_LABEL_BG,
                           edgecolor=mk, linewidth=0.7, alpha=0.85),
            )

    def _on_natural_pick_mpl(self, event) -> None:
        """Click en el subplot 2D del cuadrado natural: snap al PG más cercano
        (en coords ξ,η) o punto libre. Bidireccional con el canvas físico.
        Click-based (como M1) — sin drag, para no re-renderizar la superficie
        3D en cada frame del arrastre."""
        if getattr(event, "button", None) != 1:
            return
        if event.inaxes is not self._ax_nat:
            return
        if event.xdata is None or event.ydata is None:
            return
        xi = max(-1.0, min(1.0, float(event.xdata)))
        eta = max(-1.0, min(1.0, float(event.ydata)))
        try:
            pts_natural, _ = get_gauss_points_for_element(self.element_type)
        except Exception:
            pts_natural = []
        best_idx, best_d = None, float("inf")
        for idx, (gx, gy) in enumerate(pts_natural):
            d = math.hypot(xi - gx, eta - gy)
            if d < best_d:
                best_d, best_idx = d, idx
        if best_idx is not None and best_d < self._SNAP_NAT:
            gx, gy = pts_natural[best_idx]
            self._xi, self._eta = float(gx), float(gy)
            self._gauss_index, self._free_point = best_idx, False
        else:
            self._xi, self._eta = xi, eta
            self._gauss_index, self._free_point = None, True
        self._refresh_all()

    def _dN_symbolic_cells(self):
        """Celdas LaTeX de la matriz ∂N simbólica (2×n): ∂Nᵢ/∂ξ arriba,
        ∂Nᵢ/∂η abajo, como FRACCIONES apiladas (`\\dfrac`, notación estándar
        de derivada parcial — no el slash inline). Es la ESTRUCTURA (cada
        celda mapea 1:1 con la numérica del toggle Valores); las fórmulas
        reales viven en M1/M4."""
        n = self.n_nodes
        row_xi = [rf"\dfrac{{\partial N_{{{i}}}}}{{\partial \xi}}"
                  for i in range(1, n + 1)]
        row_eta = [rf"\dfrac{{\partial N_{{{i}}}}}{{\partial \eta}}"
                   for i in range(1, n + 1)]
        return [row_xi, row_eta]

    # ── Refresh general ─────────────────────────────────────────────
    def _refresh_all(self):
        self._draw_natural_square(self._ax_nat)
        self._draw_surface_3d()
        # ∂N(ξ,η) y J = ∂N·Xₑ cambian con el punto → update live. Xₑ solo
        # cambia con el elemento → re-render únicamente al cambiar de elemento
        # (no en cada frame del drag, que re-renderizaría una matriz idéntica).
        if self._mat_dN is not None:
            try:
                dN = self._compute_dN_matrix()
                if dN is not None:
                    self._mat_dN.set_matrix(dN)
            except Exception:
                pass
        if self._mat_Xe is not None and self._xe_element_id != self.element_id:
            try:
                Xe = self._node_coords_matrix()
                if Xe is not None:
                    self._mat_Xe.set_matrix(Xe)
                    self._xe_element_id = self.element_id
            except Exception:
                pass
        if self._mat_values is not None:
            try:
                J = self._compute_jacobian_value()
                if J is not None:
                    self._mat_values.set_matrix(J)
            except Exception:
                pass
        self._refresh_status()
        self._refresh_warning()
        self._mesh.redraw()

    def _refresh_status(self):
        # Título de los valores: SOLO el modo. Las coords (ξ,η) viven pegadas
        # al marcador del cuadrado natural; det J en la etiqueta del marcador
        # 3D; (x,y) en el marcador del canvas físico — sin repetir nada.
        if self._lbl_values_title is None:
            return
        if self._gauss_index is not None:
            mode_tag, fg = f"pg{self._gauss_index + 1}", GAUSS_CANONICAL
        elif self._free_point:
            mode_tag, fg = "punto libre", EDU_FREE_POINT_COLOR
        else:
            mode_tag, fg = "centro del elemento", EDU_FG
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
        for idx, (xi, eta) in enumerate(pts_natural):
            try:
                _, dJ, _ = compute_jacobian(dN_fn(xi, eta),
                                              coords[: self.n_nodes])
            except Exception:
                dJ = 0.0
            if dJ <= JACOBIAN_MIN_DETERMINANT:
                bad.append((idx, dJ))
        # SIN banner verde de "todo bien" (pedido del usuario): un elemento
        # sano no muestra cartel — la validez ya se lee del campo det J > 0 en
        # el canvas / la superficie 3D. Se CONSERVA el aviso ROJO de elemento
        # degenerado (det J ≤ 0), que es un error accionable, no ruido.
        if bad:
            txt = ("⚠ Elemento degenerado: det J ≤ 0 en "
                    + ", ".join(f"pg{i+1} ({dJ:.2g})" for i, dJ in bad)
                    + ". Reordená los nodos en CCW o corregí la geometría.")
            self._lbl_warning.configure(text=txt,
                                          foreground=HEALTH_ERROR_COLOR)
        else:
            self._lbl_warning.configure(text="")

    # ── Superficie 3D de det J(ξ, η) ───────────────────────────────
    def _draw_surface_3d(self):
        if self._ax_3d is None:
            return
        ax = self._ax_3d
        ax.clear()
        # Re-aplicar estilo edu (clear() resetea facecolor + ticks).
        apply_edu_style_3d(ax)

        coords = self._coords_macro()
        if coords is None or len(coords) < 4:
            ax.text2D(0.5, 0.5, "(sin elemento)",
                       transform=ax.transAxes, ha="center", va="center",
                       color=EDU_FG_MUTED, fontsize=9)
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
        # Sin tight_layout: los márgenes del gridspec ya están fijados y
        # tight_layout se pelea con la mezcla de subplots 2D + 3D.
        self._canvas_mpl.draw_idle()

    # ── Builders del toggle (Tk widgets, no axes) ──────────────────
    # ── Helpers de las matrices (fuente uniforme `_FS`, viewport ceñido) ──
    def _mat_vw(self) -> int:
        """Ancho máximo de viewport (del overlay) — tope para matrices anchas."""
        return max(440, self.OVERLAY_WIDTH - 40)

    def _fit_matrix(self, frame, matrix, *, prefix, fmt="{:.3g}",
                    fontsize=None, color=None, force_scroll=False):
        """Crea la matriz a fuente plena (`shrink=False`), eligiendo el widget
        según si ENTRA en el ancho disponible:

        - **Entra** (`render.width ≤ _mat_vw` y `not force_scroll`; el caso
          normal: todas las Q4 y las estáticas de Q9) → `LatexMatrixImage`, un
          `ttk.Label` que se AUTO-DIMENSIONA a la imagen. Tk lo ubica a su
          tamaño natural → es IMPOSIBLE que se recorte (a diferencia del canvas
          de ancho fijo de `ScrollableMatrixImage`, que bajo ciertas geometrías
          quedaba más angosto que la imagen y cortaba columnas — el bug que
          reportó el usuario en la ∂N de Q4). Es el mismo widget que la J 2×2,
          que nunca se recortó.
        - **No entra** (render > `_mat_vw`) **o `force_scroll`** →
          `ScrollableMatrixImage` con viewport tope `_mat_vw`: full-font +
          scroll/pan horizontal, sin encoger la fuente.

        `force_scroll` es para matrices LIVE cuyo ancho VARÍA con (ξ,η): la
        ∂N de Q9 mide ~518 px en el centro pero ~920 px en los puntos de Gauss.
        Decidir el widget por el render inicial (centro) daría un label que, al
        moverse el punto, se desbordaría del overlay. Con `force_scroll=True`
        (cuando es Q9) usamos el scrollable desde el inicio.

        `fontsize` default = `_FS` (panel Fórmula); el panel Valores pasa
        `_FS_VAL` (menor). `color` opcional tiñe la matriz (la ∂N simbólica usa
        el azul de acento para igualar al operador/det J). Delega en el helper
        compartido `fit_matrix_widget` (M2 y M4)."""
        fs = self._FS if fontsize is None else fontsize
        w = fit_matrix_widget(frame, matrix, prefix=prefix, fmt=fmt,
                              fontsize=fs, color=color, max_width=self._mat_vw(),
                              force_scroll=force_scroll)
        w.pack(pady=(0, 2))
        return w

    def _build_formula_panel(self, frame) -> None:
        """Fórmula MATRICIAL de J: el producto `J = ∂N · Xₑ` que evalúa el
        solver (`compute_jacobian`: `J = dN @ node_coords`). El factor ∂N se
        muestra como matriz 2×n SIMBÓLICA (estructura `∂Nᵢ/∂ξ, ∂Nᵢ/∂η`) que
        mapea 1:1 con la numérica del toggle Valores; las fórmulas reales de
        las derivadas viven en M1/M4."""
        # Producto matricial (operador): J = (∂N/∂(ξ,η)) · Xₑ.
        LatexExpressionImage(
            frame,
            expr=(r"\mathbf{J} \;=\; "
                  r"\partial\mathbf{N}_{\xi\eta}\;\mathbf{X}_e"),
            fontsize=self._FS, color=OVERLAY_ACCENT_BLUE,
        ).pack(anchor="center", pady=(2, 1))
        # Matriz ∂N simbólica (estructura, 2×n). Viewport ceñido → entra
        # completa (sin recorte vertical de las `\dfrac`) a la MISMA fuente y
        # color azul que el operador y el det J → las 3 imágenes uniformes.
        self._fit_matrix(
            frame, self._dN_symbolic_cells(),
            prefix=r"\partial\mathbf{N}_{\xi\eta}=", fmt="{}",
            color=OVERLAY_ACCENT_BLUE,
        )
        # det J en términos de las entradas de la J 2×2 resultante.
        LatexExpressionImage(
            frame,
            expr=r"\det\mathbf{J}=J_{11}\,J_{22}-J_{12}\,J_{21}",
            fontsize=self._FS, color=OVERLAY_ACCENT_BLUE,
        ).pack(anchor="center", pady=(0, 1))
        ttk.Label(
            frame, text="(las formulas de dNi/dxi se ven en M1 y M4)",
            foreground=EDU_FG_MUTED, font=("Consolas", 8), anchor="center",
        ).pack(fill="x", pady=(0, 2))

    def _build_values_panel(self, frame) -> None:
        """Factores NUMÉRICOS del producto J = ∂N·Xₑ, replicables en Excel:
        ∂N(ξ,η) en el punto, Xₑ (coords de nodos) y el resultado J. En Q4 las
        matrices entran enteras → widget ESTÁTICO sin scroll/cursor/hint (sin
        ruido); en Q9 (∂N 2×9, Xₑ 9×2) van en viewport con scroll."""
        self._lbl_values_title = tk.Label(
            frame, text="", bg=EDU_AXES_BG, fg=EDU_FG,
            font=("Consolas", 9, "bold"), anchor="center",
        )
        self._lbl_values_title.pack(fill="x", pady=(2, 2))

        # Las tres a fuente reducida `_FS_VAL` (los números son densos),
        # viewport ceñido al contenido (full-font, entran sin scroll en el
        # overlay ancho; Xₑ 9×2 muestra las 9 filas a la altura; ∂N 2×n entra
        # completa).
        dN0 = self._compute_dN_matrix()
        # La ∂N es LIVE y su ancho varía con (ξ,η). En Q9 (2×9) llega a ~920 px
        # en los PGs → force_scroll para no desbordar el overlay al moverse el
        # punto (en Q4 2×4 siempre entra → label, sin scroll).
        self._mat_dN = self._fit_matrix(
            frame, dN0 if dN0 is not None else np.zeros((2, self.n_nodes)),
            prefix=r"\partial\mathbf{N}_{\xi\eta}=", fontsize=self._FS_VAL,
            force_scroll=(self.n_nodes >= 9),
        )
        Xe0 = self._node_coords_matrix()
        self._mat_Xe = self._fit_matrix(
            frame, Xe0 if Xe0 is not None else np.zeros((self.n_nodes, 2)),
            prefix=r"\mathbf{X}_e=", fontsize=self._FS_VAL,
        )
        self._xe_element_id = self.element_id

        # J = ∂N·Xₑ: 2×2 — resultado (cambia con ξ,η). Estática a `_FS_VAL` (no
        # auto-encoge a 2×2 → queda a la misma fuente que el resto del panel).
        J0 = self._compute_jacobian_value()
        self._mat_values = LatexMatrixImage(
            frame, matrix=J0 if J0 is not None else np.eye(2),
            fmt="{:.3g}", fontsize=self._FS_VAL,
            prefix=r"\mathbf{J}=\partial\mathbf{N}_{\xi\eta}\,\mathbf{X}_e=",
            cache_values=False,  # cambia con ξ,η
        )
        self._mat_values.pack(anchor="center", pady=(0, 3))

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

    def _compute_dN_matrix(self) -> Optional[np.ndarray]:
        """∂N(ξ,η): matriz 2×n de derivadas de las funciones de forma en el
        punto actual — el PRIMER factor de J = ∂N·Xₑ (cambia con ξ,η)."""
        coords = self._coords_macro()
        if coords is None:
            return None
        try:
            _, dN_fn = get_shape_functions(self.element_type)
            return dN_fn(self._xi, self._eta)
        except Exception:
            return None

    def _node_coords_matrix(self) -> Optional[np.ndarray]:
        """Xₑ: matriz n×2 de coords (x,y) de los nodos del elemento — el
        SEGUNDO factor de J = ∂N·Xₑ (estático por elemento)."""
        coords = self._coords_macro()
        if coords is None:
            return None
        return coords[: self.n_nodes]

    # ── Helpers ────────────────────────────────────────────────────
    def _coords_macro(self) -> Optional[np.ndarray]:
        # Delega al helper compartido (antes duplicado en M1/M2/M4/M5/M7).
        return element_coords(self.project, self.element)
