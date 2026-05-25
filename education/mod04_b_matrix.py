"""
Módulo 4 — Matriz B (relación deformación-desplazamiento)

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

from education.overlay_module import CanvasOverlayModule
from education.components import (
    FormulaValueBlocksToggle, LatexMatrixImage, LatexExpressionImage,
    GaussCoordReadout, natural_to_physical,
)
from education.components.iso_inverse import iso_inverse_map
from education.components.gauss_glyph import (
    draw_gauss_base, draw_gauss_halo, draw_gauss_ripple,
    GAUSS_CANONICAL, GAUSS_HALO,
)

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian
from fem.b_matrix import compute_b_matrix
from fem.gauss_quadrature import get_gauss_points_for_element


# Tag canvas — identifica TODOS los items de M4 para borrarlos en cada
# redraw sin pisar tags de otros módulos.
_TAG = "edu_m4"


class BMatrixModule(CanvasOverlayModule):
    """M4 en modo Overlay: matriz B con toggle Fórmula/Valores y glow Gauss."""

    TITLE = "④  Matriz B  (ε = B · u)"
    PHASE = "proc"
    OVERLAY_INITIAL_POS = (24, 24)
    OVERLAY_WIDTH = 520
    OVERLAY_HEIGHT = None  # auto

    SNAP_PX = 24      # radio de snap a punto Gauss (en px de canvas)
    PULSE_PERIOD_MS = 1100   # periodo de pulsación del glow

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
        self._toggle: Optional[FormulaValueBlocksToggle] = None
        self._readout: Optional[GaussCoordReadout] = None
        self._mat_values: Optional[LatexMatrixImage] = None
        self._mat_formula: Optional[LatexMatrixImage] = None
        self._lbl_status: Optional[tk.Label] = None
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
    def build_overlay(self, body):
        # Sin chip narrativo: el título ("④ Matriz B (ε = B · u)") + el
        # toggle Fórmula (que muestra B y la relación con J⁻¹·∂N/∂ξ) + el
        # crossref al pie ya orientan al alumno.

        # ── Toggle Fórmula ↔ Valores (frames Tk, no axes compartido) ──
        # El nuevo toggle deja que cada panel maneje su propio layout con
        # widgets Tk — la matriz B se muestra como imagen PNG generada en
        # su propia figura matplotlib (sin solapes con el caption).
        self._toggle = FormulaValueBlocksToggle(
            body,
            build_formula=self._build_formula_panel,
            build_values=self._build_values_panel,
            initial=FormulaValueBlocksToggle.MODE_VALUES,
        )
        self._toggle.pack(fill="both", expand=True, pady=(2, 0))

        # ── Readout dual físico↔natural — AL PIE, no al tope ──────
        # Mismo orden pedagógico que M2: fórmula primero, "you-are-here"
        # justo arriba del crossref al siguiente módulo.
        self._readout = GaussCoordReadout(
            body, order=self._gauss_order(), etype=self.element_type,
        )
        self._readout.pack(fill="x", pady=(4, 2))

        # Cross-reference clickeable: B + D forman el integrando de k_e.
        self._pack_crossref(
            body, "mod05",
            "👉 B + D (③) construyen el integrando de k_e — "
            "ver ⑤ Matriz K_e y ⑤′ Cuadratura.",
            wraplength=500,
        )

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
            # Color según el origen del punto libre: rojo apagado si fue
            # un click físico (`_free_point=True`), naranja canónico si fue
            # un setteo por defecto (al cambiar de elemento, etc.).
            free_color = "#d68a7a" if self._free_point else GAUSS_HALO
            draw_gauss_halo(
                mesh.canvas, sel_sx, sel_sy, tag=_TAG,
                color=free_color, extra=5.0, width=2.2, dash=(4, 3),
            )
            # Disco interior pequeño para legibilidad sobre cualquier fondo.
            mesh.canvas.create_oval(
                sel_sx - 3, sel_sy - 3, sel_sx + 3, sel_sy + 3,
                fill=free_color, outline="#ffffff", width=1.0,
                tags=_TAG,
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

    # ── Refresh del overlay (tras cambio de selección/elemento) ────
    def _refresh_all(self) -> None:
        # Live-update de la matriz numérica (siempre, aunque esté en modo
        # fórmula — barato y mantiene el estado coherente al togglear).
        if self._mat_values is not None:
            try:
                B = self._compute_b()
                if B is not None:
                    self._mat_values.set_matrix(B)
            except Exception:
                pass
        # La fórmula simbólica solo se reconstruye si cambió el número
        # de nodos (Q4↔Q9) — el contenido depende solo de eso.
        if self._mat_formula is not None:
            try:
                self._mat_formula.set_matrix(self._formula_cells())
            except Exception:
                pass
        self._refresh_status()
        self._mesh.redraw()

    def _refresh_status(self) -> None:
        # Físico (x, y) del punto actual — alimenta el readout dual.
        physical = None
        try:
            coords = self._coords_macro()
            if coords is not None and len(coords) >= self.n_nodes:
                xy = natural_to_physical(
                    self._xi, self._eta, coords[: self.n_nodes],
                    self.element_type,
                )
                physical = (float(xy[0]), float(xy[1]))
        except Exception:
            physical = None

        if self._readout is not None:
            self._readout.set_state(
                order=self._gauss_order(),
                etype=self.element_type,
                selected_index=self._gauss_index,
                xi=self._xi, eta=self._eta,
                physical=physical,
            )
        if self._lbl_status is not None:
            eid = self.element_id if self.element_id is not None else "—"
            tag = (f"pg{self._gauss_index + 1}"
                   if self._gauss_index is not None else "libre")
            self._lbl_status.configure(
                text=f"Elemento {eid}   ·   punto: {tag}"
            )
        if self._lbl_values_title is not None:
            if self._gauss_index is not None:
                mode_tag = f"pg{self._gauss_index + 1}"
                fg = GAUSS_CANONICAL
            elif self._free_point:
                mode_tag = f"(ξ,η) = ({self._xi:+.3f}, {self._eta:+.3f})"
                fg = "#d68a7a"
            else:
                mode_tag = f"(ξ,η) = ({self._xi:+.3f}, {self._eta:+.3f})"
                fg = "#dcdcdc"
            n_cols = 2 * self.n_nodes
            self._lbl_values_title.configure(
                text=f"B  en  {mode_tag}     ·     3 × {n_cols}", fg=fg,
            )

    def _gauss_order(self) -> int:
        """Orden de cuadratura asociado al tipo de elemento (Q4→2, Q9→3)."""
        return 3 if self.n_nodes == 9 else 2

    # ── Pulse loop ──────────────────────────────────────────────────
    def _schedule_pulse(self):
        if self._mesh is None:
            return
        try:
            # Avanza la fase y redibuja la capa. ~30 fps suaves.
            self._pulse_phase = (self._pulse_phase + 0.18) % (2 * math.pi)
            self._mesh.redraw()
        except Exception:
            pass
        try:
            self._pulse_after_id = self._mesh.after(33, self._schedule_pulse)
        except tk.TclError:
            self._pulse_after_id = None

    # ── Cómputo de B ────────────────────────────────────────────────
    def _coords_macro(self) -> Optional[np.ndarray]:
        if self.project is None or self.element is None:
            return None
        try:
            coords = np.array([
                [self.project.nodes[nid].x, self.project.nodes[nid].y]
                for nid in self.element.node_ids
            ], dtype=float)
        except KeyError:
            return None
        return coords

    def _compute_b(self) -> Optional[np.ndarray]:
        coords = self._coords_macro()
        if coords is None or len(coords) < self.n_nodes:
            return None
        _, dN_fn = get_shape_functions(self.element_type)
        dN_nat = dN_fn(self._xi, self._eta)
        _, _, invJ = compute_jacobian(dN_nat, coords[: self.n_nodes])
        dN_phys = invJ @ dN_nat
        return compute_b_matrix(dN_phys)

    # ── Builders de los paneles del toggle (Tk widgets, no axes) ──
    def _formula_cells(self):
        """Celdas de la matriz B en forma simbólica para `LatexMatrixImage`.

        Notación compacta: `N1x` ≡ ∂N₁/∂x. Sufijos ASCII en vez de
        subíndices Unicode tipográficos (la fuente Consolas no cubre
        todos los U+1D6x y dispara warnings de glifo).
        """
        n = self.n_nodes
        if n == 4:
            row1 = ["N1x", "0", "N2x", "0", "N3x", "0", "N4x", "0"]
            row2 = ["0", "N1y", "0", "N2y", "0", "N3y", "0", "N4y"]
            row3 = ["N1y", "N1x", "N2y", "N2x",
                    "N3y", "N3x", "N4y", "N4x"]
        else:  # Q9 — mostramos columnas extremas + elipsis
            row1 = ["N1x", "0", "N2x", "0", "…", "N9x", "0"]
            row2 = ["0", "N1y", "0", "N2y", "…", "0", "N9y"]
            row3 = ["N1y", "N1x", "N2y", "N2x", "…", "N9y", "N9x"]
        return [row1, row2, row3]

    def _build_formula_panel(self, frame) -> None:
        """Construye el panel de la fórmula simbólica de B (UNA SOLA VEZ).

        Layout vertical: matriz (PNG independiente) + caption (mathtext en
        otra imagen). Tk hace el layout — sin solapes.
        """
        self._mat_formula = LatexMatrixImage(
            frame, matrix=self._formula_cells(),
            fmt="{}", fontsize=13, prefix=r"\mathbf{B}=",
            cache_values=True,
        )
        self._mat_formula.pack(anchor="center", pady=(4, 6))
        LatexExpressionImage(
            frame,
            expr=(r"N_{ix}=\dfrac{\partial N_i}{\partial x}\;\;\;"
                  r"\dfrac{\partial N_i}{\partial x} = "
                  r"\mathbf{J}^{-1}\,\dfrac{\partial N_i}{\partial \xi}"),
            fontsize=12, color="#90caf9",
        ).pack(anchor="center", pady=(0, 4))

    def _build_values_panel(self, frame) -> None:
        """Construye el panel de valores numéricos de B.

        Tres widgets verticales: matriz B (live-update en `_refresh_all`),
        título textual (tamaño/PG actual), label de status.
        """
        from config.settings import EDU_AXES_BG, EDU_FG_MUTED
        self._lbl_values_title = tk.Label(
            frame, text="", bg=EDU_AXES_BG, fg="#dcdcdc",
            font=("Consolas", 9, "bold"), anchor="center",
        )
        self._lbl_values_title.pack(fill="x", pady=(2, 2))
        # fontsize chico para Q9 (matriz 3×18 más ancha).
        # Para Q4 (3x8) damos `base=13` que el auto-shrink interpreta
        # como `n<=9 → max(10, 13-2)=11`; para Q9 (3x18) damos `base=12`
        # que cae a `n<=18 → max(7, 12-5)=7` y entra en el overlay.
        fs = 13 if self.n_nodes == 4 else 12
        B = self._compute_b()
        self._mat_values = LatexMatrixImage(
            frame, matrix=B if B is not None else np.zeros((3, 2 * self.n_nodes)),
            fmt="{:.3g}", fontsize=fs, prefix=r"\mathbf{B}=",
            cache_values=False,  # cambia con ξ,η — no cachear
        )
        self._mat_values.pack(anchor="center", pady=(0, 4))
        self._lbl_status = tk.Label(
            frame, text="", bg=EDU_AXES_BG, fg=EDU_FG_MUTED,
            font=("Consolas", 9), anchor="center",
        )
        self._lbl_status.pack(fill="x", pady=(0, 2))
