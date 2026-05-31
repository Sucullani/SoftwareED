"""
Módulo 3 — Matriz B (relación deformación-desplazamiento)

    ε = B · u

REDISEÑADO: Modo Overlay sobre el MeshCanvas compartido (propuesta UX 2026).

Patología corregida:
    Antes era un Toplevel con sidebar denso + 2 paneles + matriz B abajo.
    El alumno perdía el contexto del modelo y la matriz competía por
    espacio con la geometría.

Diseño actual:
    1. NO abre Toplevel. Activa un overlay flotante (~480 px) sobre el
       MeshCanvas compartido. La malla real sigue visible debajo.
    2. Glow amarillo pulsante en los puntos de Gauss del elemento
       seleccionado (capa educativa, dibujada por el canvas).
    3. Click en cualquier punto del canvas: si cae cerca de un punto de
       Gauss del elemento bajo análisis → snap; si cae en otro elemento
       → el elemento bajo análisis cambia.
    4. El overlay muestra la matriz B con un toggle Fórmula ↔ Valores
       (requerimiento del usuario): la fórmula simbólica explica el
       concepto, los valores numéricos muestran B(ξ,η) en el punto
       Gauss seleccionado.

Pedagogía:
    Al ver el glow pulsante en los puntos donde el solver elige evaluar
    B, la "superconvergencia" deja de ser una palabra del sidebar y se
    vuelve algo que el alumno *ve*.
"""

from __future__ import annotations

from typing import Optional

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
    apply_edu_style_figure, apply_edu_style_2d,
)
from education.components.iso_inverse import iso_inverse_map
from education.components.gauss_glyph import (
    draw_gauss_base, draw_gauss_halo, draw_gauss_ripple, draw_gauss_free_point,
    GAUSS_CANONICAL, GAUSS_HALO,
)

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian
from fem.b_matrix import compute_b_matrix
from fem.gauss_quadrature import get_gauss_points_for_element

from config.settings import (
    EDU_FREE_POINT_COLOR, EDU_AXES_BG, EDU_FG, EDU_FG_MUTED, EDU_LABEL_BG,
    EDU_NATURAL_OUTLINE_COLOR, EDU_NATURAL_AXES_COLOR, OVERLAY_ACCENT_BLUE,
)


# Tag canvas — identifica TODOS los items de M4 para borrarlos en cada
# redraw sin pisar tags de otros módulos.
_TAG = "edu_m3"
# Marcador/PG seleccionado en naranja (halo unificado), PGs no seleccionados
# en cian canónico — mismo lenguaje cromático que M2.
_C_MARKER = GAUSS_HALO
_C_SURFACE_HI = GAUSS_CANONICAL


class BMatrixModule(CanvasOverlayModule):
    """M4 en modo Overlay: matriz B con toggle Fórmula/Valores y glow Gauss."""

    TITLE = "③  Matriz B  (ε = B · u)"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    # Ancho fijo: el cuadrado natural (matplotlib, compacto, centrado) va
    # arriba y la B numérica —ANCHA (3×8 ~840 px en Q4, 3×18 en Q9)— debajo
    # en scroll horizontal. 720 da viewport `_mat_vw=680` para la B y deja la
    # B simbólica (\dfrac, ~493 px en Q4) entera como label.
    OVERLAY_WIDTH = 720
    OVERLAY_HEIGHT = None  # auto

    SNAP_PX = 24      # radio de snap a punto Gauss (en px de canvas)
    PULSE_PERIOD_MS = 1100   # periodo de pulsación del glow
    # Tolerancia de snap a PG dentro del cuadrado natural, en coords (ξ,η).
    _SNAP_NAT = 0.16
    # Fuente del panel FÓRMULA (relación + B simbólica) — uniforme en tamaño y
    # color (azul de acento); del panel VALORES (B numérica), reducida.
    _FS = 14
    _FS_VAL = 12

    def __init__(self, main_window, project, element_id):
        # Punto natural actual (centro inicial). El render decide si es
        # un punto de Gauss exacto o "libre".
        self._xi = 0.0
        self._eta = 0.0
        self._gauss_index: Optional[int] = None  # 0..n-1 si es Gauss, sino None
        # Estado del pulso (oscilación 0..1 sinusoidal). El after-loop lo
        # actualiza para que el glow lata visualmente.
        self._pulse_phase = 0.0
        self._pulse_after_id: Optional[str] = None
        # Widgets construidos en build_overlay
        self._fig: Optional[Figure] = None
        self._ax_nat = None       # subplot 2D: cuadrado natural (interactivo)
        self._canvas_mpl: Optional[FigureCanvasTkAgg] = None
        self._toggle: Optional[FormulaValueBlocksToggle] = None
        # `fit_matrix_widget` devuelve LatexMatrixImage (entra) o
        # ScrollableMatrixImage (scroll); ambos exponen set_matrix. La CADENA
        # numérica de Valores (replicable en Excel, paralelo a M2):
        # ∂N_ξη (naturales) · J⁻¹ → ∂N_xy (físicas) → B.
        self._mat_dN_nat: Optional[LatexMatrixImage | ScrollableMatrixImage] = None
        self._mat_invJ: Optional[LatexMatrixImage | ScrollableMatrixImage] = None
        self._mat_dN_phys: Optional[LatexMatrixImage | ScrollableMatrixImage] = None
        self._mat_values: Optional[LatexMatrixImage | ScrollableMatrixImage] = None
        self._mat_formula: Optional[LatexMatrixImage | ScrollableMatrixImage] = None
        self._lbl_values_title: Optional[tk.Label] = None
        # Narrativa de transformación: estado del último click (snap a PG
        # vs libre físico). Determina color del lbl_values_title.
        self._free_point = False
        # Click consumer (bound method para identidad estable al deregister).
        self._click_consumer = self._on_canvas_click_consume
        super().__init__(main_window, project, element_id)

    # ── Determinación de tipo de elemento (auto) ───────────────────
    @property
    def element_type(self) -> str:
        if self.element is not None and getattr(self.element, "num_nodes", 0) == 9:
            from config.settings import ELEMENT_Q9
            return ELEMENT_Q9
        return getattr(self.project, "element_type", None) or self._fallback_etype()

    def _fallback_etype(self) -> str:
        from config.settings import ELEMENT_Q4
        return ELEMENT_Q4

    @property
    def n_nodes(self) -> int:
        from config.settings import ELEMENT_Q9
        return 9 if self.element_type == ELEMENT_Q9 else 4

    # ── Construcción del overlay (compacto UX 2026) ───────────────
    def _mat_vw(self) -> int:
        """Ancho máximo de viewport (del overlay) — tope para matrices anchas."""
        return max(440, self.OVERLAY_WIDTH - 40)

    def build_overlay(self, body):
        # Sin chip narrativo ni descripción del mapeo: el título ("③ Matriz B
        # (ε = B · u)") + el cuadrado natural + el toggle + el crossref al pie
        # ya orientan al alumno. La antigua línea "(ξ,η)=… → mapeo → (x,y)=…"
        # se eliminó (ruido: el marcador del cuadrado ya muestra ξ,η).

        # ── Cuadrado natural interactivo (matplotlib, CENTRADO) — AL TOPE ──
        # B se evalúa en (ξ,η). El alumno fija el punto clickeando AQUÍ o sobre
        # el elemento físico del canvas: dos espacios, un mismo punto; el
        # marcador se mueve en ambos. Mismo estilo/figura que M2 (sin la
        # superficie 3D vecina → el cuadrado queda centrado). El subplot 2D
        # reemplaza al ex `GaussCoordReadout` tk (interacción pobre).
        plot_frame = ttk.Frame(body)
        plot_frame.pack(pady=(2, 2))  # sin fill → frame centrado en el body
        self._fig = Figure(figsize=(3.4, 2.7), dpi=100)
        apply_edu_style_figure(self._fig)
        self._ax_nat = self._fig.add_subplot(111)
        apply_edu_style_2d(self._ax_nat, show_spines=False)
        self._fig.subplots_adjust(left=0.04, right=0.96, top=0.86, bottom=0.06)
        self._canvas_mpl = FigureCanvasTkAgg(self._fig, master=plot_frame)
        self._canvas_mpl.get_tk_widget().pack()
        self._canvas_mpl.mpl_connect("button_press_event",
                                     self._on_natural_pick_mpl)

        # ── Toggle Fórmula ↔ Valores (frames Tk, no axes compartido) ──
        self._toggle = FormulaValueBlocksToggle(
            body,
            build_formula=self._build_formula_panel,
            build_values=self._build_values_panel,
            initial=FormulaValueBlocksToggle.MODE_VALUES,
        )
        self._toggle.pack(fill="both", expand=True, pady=(2, 0))

        # Cross-reference clickeable: B se combina con D (④) en el integrando.
        self._pack_crossref(
            body, "mod04",
            "👉 B se combina con la matriz constitutiva D (④) en el "
            "integrando BᵀDB de k_e — ver ⑤ Rigidez K_e + Gauss.",
            wraplength=500,
        )

        self._draw_natural_square(self._ax_nat)
        self._refresh_status()

    # ── Capa educativa sobre el canvas ─────────────────────────────
    def draw_canvas_layer(self, mesh):
        """Dibuja el glifo unificado de Gauss + ripple animado + halo en
        el punto seleccionado. Se invoca al final de cada redraw().

        Mejora UX vs. la versión previa: en lugar de un solo anillo que
        crece/encoge (visualmente "saltón"), ahora 2 anillos concéntricos
        emanan continuamente del PG con fade radial — efecto "ripple" que
        comunica la idea de un MUESTREO que irradia, en línea con la
        semántica pedagógica del PG como sitio de evaluación de B.
        """
        # Limpiar nuestros tags previos (defensa por si el redraw global
        # no los removió — siempre seguro).
        mesh.canvas.delete(_TAG)

        if self.element is None or self.project is None:
            return
        try:
            coords = self._coords_macro()
        except Exception:
            return
        if coords is None or len(coords) < 4:
            return

        pts_natural, _ = get_gauss_points_for_element(self.element_type)

        # Fase normalizada [0, 1) — el ripple compartido la consume.
        phase = (self._pulse_phase / (2.0 * math.pi)) % 1.0

        # Marcador del punto LIBRE en físico (modo continuo, bidireccional
        # canvas↔overlay). Visualizar dónde cayó el inverse map sobre el
        # elemento real refuerza la dualidad físico↔natural: el alumno
        # ve la posición del click + el valor de B en el toggle simultáneamente.
        sel_xy_world = natural_to_physical(
            self._xi, self._eta, coords[: self.n_nodes], self.element_type,
        )
        sel_sx, sel_sy = mesh.world_to_screen(sel_xy_world[0], sel_xy_world[1])

        if self._gauss_index is None:
            # Glifo unificado de punto LIBRE. Color según el origen: rojo
            # apagado (default EDU_FREE_POINT_COLOR) si fue un click físico
            # (`_free_point=True`), naranja canónico si fue un setteo por
            # defecto (al cambiar de elemento, ξ=η=0).
            draw_gauss_free_point(
                mesh.canvas, sel_sx, sel_sy, tag=_TAG,
                color=None if self._free_point else GAUSS_HALO,
            )

        # Dibujar TODOS los puntos de Gauss del elemento bajo análisis.
        # Orden de capas: ripple PRIMERO (queda atrás), glifo base ENCIMA,
        # halo de selección al final.
        # Reducción de ruido: el label `pgN` se muestra SOLO en el PG
        # seleccionado (el alumno ya sabe que los demás son pg2, pg3, etc.
        # por su posición; repetir el texto en cada PG saturaba la lectura
        # del canvas, sobre todo en Q9 con 9 PGs).
        for idx, (xi, eta) in enumerate(pts_natural):
            xy = natural_to_physical(
                xi, eta, coords[: self.n_nodes], self.element_type,
            )
            sx, sy = mesh.world_to_screen(xy[0], xy[1])
            is_selected = (idx == self._gauss_index)

            draw_gauss_ripple(
                mesh.canvas, sx, sy, tag=_TAG, phase=phase,
                color_fg=GAUSS_CANONICAL, intensity="strong",
            )
            draw_gauss_base(
                mesh.canvas, sx, sy,
                label=f"pg{idx + 1}" if is_selected else None,
                tag=_TAG, color=GAUSS_CANONICAL,
            )
            if is_selected:
                draw_gauss_halo(
                    mesh.canvas, sx, sy, tag=_TAG, color=GAUSS_HALO,
                )

    def on_activated(self) -> None:
        # Iniciar pulse loop. El after lo controla el frame del MeshCanvas
        # para que se cancele si el widget se destruye (parent muere).
        self._pulse_phase = 0.0
        self._schedule_pulse()
        # Click consumer: el MeshCanvas nos consulta primero. Si el click
        # cae cerca de un Gauss del elemento bajo análisis, consumimos
        # (return True) y el canvas omite su hit-test — la selección se
        # preserva y el panel de módulos no oscila prendido/apagado.
        self._mesh.add_click_consumer(self._click_consumer)

    def on_closed(self) -> None:
        if self._pulse_after_id is not None:
            try:
                self._mesh.after_cancel(self._pulse_after_id)
            except Exception:
                pass
            self._pulse_after_id = None
        try:
            self._mesh.remove_click_consumer(self._click_consumer)
        except Exception:
            pass

    def on_element_selected(self, elem_id):
        """Override: cambiar elemento NO snapea automáticamente — mantiene
        ξ,η actuales y deja que el alumno re-clickee si quiere snap.
        """
        if elem_id == self.element_id:
            return
        self.element_id = elem_id
        self.element = self.project.elements.get(elem_id) if self.project else None
        # Reset al centro tras cambio de elemento (más predecible que
        # mantener ξ,η antiguos sobre un elemento distinto).
        self._xi, self._eta = 0.0, 0.0
        self._gauss_index = None
        self._free_point = False
        self._refresh_all()

    # ── Click consumer: snap a Gauss + free point en físico ─────
    def _on_canvas_click_consume(self, event) -> bool:
        """Consumer registrado en MeshCanvas. Cascada:

        1. **Snap a PG**: si cae dentro de `SNAP_PX` → snap, modo discreto.
        2. **Free probe físico**: si no hay snap pero cae DENTRO del
           elemento (Newton-R converge) → free point, modo continuo.
           Pulso del chip narrativo para "ver" al Jacobiano traduciendo.
        3. **Miss**: fall-through al canvas (cambio de elemento, etc.)."""
        if self.element is None:
            return False
        try:
            coords = self._coords_macro()
        except Exception:
            return False
        if coords is None or len(coords) < 4:
            return False

        # 1) Snap a PG.
        pts_natural, _ = get_gauss_points_for_element(self.element_type)
        best_idx = -1
        best_dpx = float("inf")
        for idx, (xi, eta) in enumerate(pts_natural):
            xy = natural_to_physical(xi, eta, coords[: self.n_nodes],
                                       self.element_type)
            sx, sy = self._mesh.world_to_screen(xy[0], xy[1])
            d = math.hypot(sx - event.x, sy - event.y)
            if d < best_dpx:
                best_dpx = d
                best_idx = idx
        if best_idx >= 0 and best_dpx < self.SNAP_PX:
            xi, eta = pts_natural[best_idx]
            self._xi, self._eta = float(xi), float(eta)
            self._gauss_index = best_idx
            self._free_point = False
            self._refresh_all()
            return True

        # 2) Free probe en físico: inverse map por Newton-R.
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

    # ── Cuadrado natural (subplot 2D matplotlib, estilo M2) ────────
    def _draw_natural_square(self, ax) -> None:
        """Dibuja el cuadrado natural (ξ,η) estilo M2/M1: contorno azul, ejes,
        ±1, los PUNTOS DE GAUSS del elemento (donde se evalúa B) y el marcador
        del punto seleccionado con su (ξ,η) pegada. El PG seleccionado se pinta
        naranja. Reemplaza al ex readout tk."""
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
            pts_natural, _ = get_gauss_points_for_element(self.element_type)
            for i, (gx, gy) in enumerate(pts_natural):
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
        ax.set_title("B se evalúa en el cuadrado natural  (ξ, η)",
                      color=EDU_NATURAL_OUTLINE_COLOR, fontsize=9,
                      fontweight="bold", pad=4)
        ax.set_xticks([]); ax.set_yticks([])
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
        (en coords ξ,η) o punto libre. Bidireccional con el canvas físico."""
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

    # ── Refresh del overlay (tras cambio de selección/elemento) ────
    def _refresh_all(self) -> None:
        # Live-update de TODA la cadena numérica (∂N_ξη, J⁻¹, ∂N_xy, B) —
        # siempre, aunque esté en modo fórmula (barato, mantiene coherencia al
        # togglear). Un único _compute_b devuelve los cuatro.
        try:
            B, dN_nat, invJ, dN_phys = self._compute_b(return_intermediate=True)
            for w, mat in ((self._mat_dN_nat, dN_nat), (self._mat_invJ, invJ),
                           (self._mat_dN_phys, dN_phys), (self._mat_values, B)):
                if w is not None and mat is not None:
                    w.set_matrix(mat)
        except Exception:
            pass
        # La fórmula simbólica solo se reconstruye si cambió el número
        # de nodos (Q4↔Q9) — el contenido depende solo de eso.
        if self._mat_formula is not None:
            try:
                self._mat_formula.set_matrix(self._formula_cells())
            except Exception:
                pass
        # Redibujar el cuadrado natural (mueve el marcador / recolorea el PG).
        if self._ax_nat is not None and self._canvas_mpl is not None:
            try:
                self._draw_natural_square(self._ax_nat)
                self._canvas_mpl.draw_idle()
            except Exception:
                pass
        self._refresh_status()
        self._mesh.redraw()

    def _refresh_status(self) -> None:
        # Título minimalista del panel Valores: SOLO el modo (criterio de M2).
        # Sin descripción de mapeo, sin "Elemento N", sin "3 × N" — el cuadrado
        # natural ya muestra (ξ,η) y la propia matriz muestra su tamaño.
        if self._lbl_values_title is not None:
            if self._gauss_index is not None:
                mode_tag = f"pg{self._gauss_index + 1}"
                fg = GAUSS_CANONICAL
            elif self._free_point:
                mode_tag = "punto libre"
                fg = EDU_FREE_POINT_COLOR
            else:
                mode_tag = "centro del elemento"
                fg = EDU_FG
            self._lbl_values_title.configure(text=f"B  en  {mode_tag}", fg=fg)

    # ── Pulse loop ──────────────────────────────────────────────────
    def _schedule_pulse(self):
        if self._mesh is None:
            return
        try:
            # Avanza la fase y redibuja SOLO las capas overlay. ~30 fps
            # suaves: un redraw() completo rasterizaria toda la malla por
            # frame. La base ya esta dibujada (redraw completo previo).
            self._pulse_phase = (self._pulse_phase + 0.18) % (2 * math.pi)
            self._mesh.redraw_overlays_only()
        except Exception:
            pass
        try:
            self._pulse_after_id = self._mesh.after(33, self._schedule_pulse)
        except tk.TclError:
            self._pulse_after_id = None

    # ── Cómputo de B ────────────────────────────────────────────────
    def _coords_macro(self) -> Optional[np.ndarray]:
        # Delega al helper compartido (antes duplicado en M1/M2/M4/M5/M7).
        return element_coords(self.project, self.element)

    def _compute_b(self, *, return_intermediate: bool = False):
        """B(ξ,η) en el punto actual. Con `return_intermediate=True` devuelve
        la CADENA completa `(B, dN_nat, invJ, dN_phys)` que un alumno replica
        en Excel: dN_nat (2×n naturales) → invJ (2×2) → dN_phys = invJ·dN_nat
        (2×n físicas) → B (3×2n). Cero cómputo extra: estos intermedios YA se
        calculan acá. Default (B sola) preserva los callers existentes."""
        coords = self._coords_macro()
        if coords is None or len(coords) < self.n_nodes:
            return (None, None, None, None) if return_intermediate else None
        _, dN_fn = get_shape_functions(self.element_type)
        dN_nat = dN_fn(self._xi, self._eta)
        _, _, invJ = compute_jacobian(dN_nat, coords[: self.n_nodes])
        dN_phys = invJ @ dN_nat
        B = compute_b_matrix(dN_phys)
        if return_intermediate:
            return B, dN_nat, invJ, dN_phys
        return B

    # ── Builders de los paneles del toggle (Tk widgets, no axes) ──
    def _formula_cells(self):
        """Celdas de la matriz B en forma simbólica con las derivadas como
        FRACCIONES `\\dfrac` (notación estándar de derivada parcial; reemplaza
        la notación compacta `N1x` por pedido del usuario — coherente con la
        ∂N de M2). Q4: las 8 columnas completas; Q9: columnas extremas +
        elipsis (3×18 completo excede el ancho del overlay)."""
        def dx(i):
            return rf"\dfrac{{\partial N_{{{i}}}}}{{\partial x}}"

        def dy(i):
            return rf"\dfrac{{\partial N_{{{i}}}}}{{\partial y}}"

        n = self.n_nodes
        if n == 4:
            row1, row2, row3 = [], [], []
            for i in range(1, 5):
                row1 += [dx(i), "0"]
                row2 += ["0", dy(i)]
                row3 += [dy(i), dx(i)]
        else:  # Q9 — columnas extremas + elipsis
            row1 = [dx(1), "0", dx(2), "0", r"\cdots", dx(9), "0"]
            row2 = ["0", dy(1), "0", dy(2), r"\cdots", "0", dy(9)]
            row3 = [dy(1), dx(1), dy(2), dx(2), r"\cdots", dy(9), dx(9)]
        return [row1, row2, row3]

    def _build_formula_panel(self, frame) -> None:
        """Panel FÓRMULA: la relación VECTORIAL que origina cada entrada física
        de B (puente con M2: el J) + la B simbólica con derivadas en fracciones.
        Fuente uniforme `_FS` y azul de acento → imágenes homogéneas (M2)."""
        # Relación MATRICIAL correcta: el VECTOR 2×1 de derivadas físicas sale
        # del VECTOR 2×1 de derivadas naturales vía J⁻¹ (2×2). La forma escalar
        # anterior `∂Nᵢ/∂x = J⁻¹·∂Nᵢ/∂ξ` era matricialmente malformada (escalar
        # = 2×2·escalar, y omitía la componente η). `\substack` apila el vector
        # columna (mathtext NO soporta `bmatrix`). Verificado bit-a-bit contra
        # el solver: dN_phys = invJ @ dN_nat (ver fem/jacobian.py).
        LatexExpressionImage(
            frame,
            expr=(r"\left[\substack{\dfrac{\partial N_i}{\partial x} \\ "
                  r"\dfrac{\partial N_i}{\partial y}}\right]"
                  r"=\mathbf{J}^{-1}\,"
                  r"\left[\substack{\dfrac{\partial N_i}{\partial \xi} \\ "
                  r"\dfrac{\partial N_i}{\partial \eta}}\right]"),
            fontsize=self._FS, color=OVERLAY_ACCENT_BLUE,
        ).pack(anchor="center", pady=(2, 2))
        # Matriz B SIMBÓLICA (\dfrac). Entra como label (Q4 ~493, Q9 ~432 px).
        self._mat_formula = fit_matrix_widget(
            frame, self._formula_cells(), prefix=r"\mathbf{B}=", fmt="{}",
            fontsize=self._FS, color=OVERLAY_ACCENT_BLUE,
            max_width=self._mat_vw(),
        )
        self._mat_formula.pack(anchor="center", pady=(0, 2))
        ttk.Label(
            frame, text="(∂Nᵢ/∂ξ, ∂Nᵢ/∂η: ver M1)",
            foreground=EDU_FG_MUTED, font=("Consolas", 8), anchor="center",
        ).pack(fill="x", pady=(0, 2))

    def _build_values_panel(self, frame) -> None:
        """Panel VALORES: la CADENA numérica COMPLETA de B, replicable en una
        hoja de cálculo (pedido del usuario, paralelo a M2):
            ∂N_ξη (2×n naturales) · J⁻¹ (2×2) → ∂N_xy = J⁻¹·∂N_ξη (2×n físicas)
            → B (3×2n ensamblada).
        Título minimalista (solo el modo). ∂N_ξη/∂N_xy son 2×n (en Q9 anchas →
        `force_scroll`); J⁻¹ es 2×2 (entra como label); B siempre ancha
        (`force_scroll`). Todo a fuente reducida `_FS_VAL`."""
        self._lbl_values_title = tk.Label(
            frame, text="", bg=EDU_AXES_BG, fg=EDU_FG,
            font=("Consolas", 9, "bold"), anchor="center",
        )
        self._lbl_values_title.pack(fill="x", pady=(2, 4))

        B, dN_nat, invJ, dN_phys = self._compute_b(return_intermediate=True)
        n = self.n_nodes
        wide = (n >= 9)  # las 2×n de Q9 se ensanchan en los PGs → scroll
        mvw = self._mat_vw()

        # ① ∂N naturales: la ENTRADA (derivadas en el cuadrado natural).
        self._mat_dN_nat = fit_matrix_widget(
            frame, dN_nat if dN_nat is not None else np.zeros((2, n)),
            prefix=r"\partial\mathbf{N}_{\xi\eta}=", fmt="{:.3g}",
            fontsize=self._FS_VAL, max_width=mvw, force_scroll=wide,
        )
        self._mat_dN_nat.pack(pady=(0, 3))
        # ② J⁻¹: el PUENTE natural→físico (2×2, entra como label).
        self._mat_invJ = fit_matrix_widget(
            frame, invJ if invJ is not None else np.zeros((2, 2)),
            prefix=r"\mathbf{J}^{-1}=", fmt="{:.3g}",
            fontsize=self._FS_VAL, max_width=mvw,
        )
        self._mat_invJ.pack(pady=(0, 3))
        # ③ ∂N físicas = J⁻¹·∂N_ξη: lo que alimenta directamente a B.
        self._mat_dN_phys = fit_matrix_widget(
            frame, dN_phys if dN_phys is not None else np.zeros((2, n)),
            prefix=r"\partial\mathbf{N}_{xy}=\mathbf{J}^{-1}\partial\mathbf{N}_{\xi\eta}=",
            fmt="{:.3g}", fontsize=self._FS_VAL, max_width=mvw, force_scroll=wide,
        )
        self._mat_dN_phys.pack(pady=(0, 3))
        # ④ B ensamblada desde ∂N_xy (3×2n, siempre ancha → scroll).
        self._mat_values = fit_matrix_widget(
            frame, B if B is not None else np.zeros((3, 2 * n)),
            prefix=r"\mathbf{B}=", fmt="{:.3g}", fontsize=self._FS_VAL,
            max_width=mvw, force_scroll=True,
        )
        self._mat_values.pack(pady=(0, 4))
