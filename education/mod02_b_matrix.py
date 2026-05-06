"""
Módulo 2 — Matriz B (relación deformación-desplazamiento)

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
    5. Hover sobre una columna ilumina el nodo en el canvas (cada par
       de columnas pertenece a un nodo); hover sobre una fila ilumina
       la componente de deformación (εx, εy, γxy).

Pedagogía:
    Al ver el glow pulsante en los puntos donde el solver elige evaluar
    B, la "superconvergencia" deja de ser una palabra del sidebar y se
    vuelve algo que el alumno *ve*. Cada par de columnas → un nodo es
    una regla cinética: el alumno hover-ea y el canvas ilumina.
"""

from __future__ import annotations

from typing import Optional

import math
import numpy as np
import tkinter as tk
import ttkbootstrap as ttk

from education.overlay_module import CanvasOverlayModule
from education.components import (
    FormulaValueToggle, render_matrix_latex,
    natural_to_physical,
)

from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian
from fem.b_matrix import compute_b_matrix
from fem.gauss_quadrature import get_gauss_points_for_element


# Color del glow pulsante en los puntos de Gauss (paleta canónica).
_GAUSS_GLOW_OUTER = "#fff176"   # amarillo claro — anillo exterior
_GAUSS_GLOW_INNER = "#ffd54f"   # amarillo intenso — punto central
_GAUSS_GLOW_HALO  = "#ff8a65"   # naranja — halo del punto seleccionado
_TAG = "edu_m2"                  # tag canvas: identifica TODOS los items M2


class BMatrixModule(CanvasOverlayModule):
    """M2 en modo Overlay: matriz B con toggle Fórmula/Valores y glow Gauss."""

    TITLE = "②  Matriz B  (ε = B · u)"
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
        # Toggle ref (creado en build_overlay)
        self._toggle: Optional[FormulaValueToggle] = None
        self._lbl_status: Optional[ttk.Label] = None
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

    # ── Construcción del overlay flotante ──────────────────────────
    def build_overlay(self, body):
        # Banner contextual breve (sin sidebar denso). El usuario selecciona
        # el elemento por click en el canvas; aquí solo mostramos el badge
        # de qué está bajo análisis ahora.
        top = ttk.Frame(body)
        top.pack(fill="x", pady=(0, 6))

        ttk.Label(
            top, text="Click en un punto Gauss (◉) para evaluar B ahí",
            font=("Segoe UI", 9), foreground="#90caf9",
        ).pack(anchor="w")

        self._lbl_status = ttk.Label(
            top, text="", font=("Consolas", 9),
            foreground="#cfd2d8", wraplength=480, justify="left",
        )
        self._lbl_status.pack(anchor="w", pady=(2, 0))

        ttk.Separator(body).pack(fill="x", pady=4)

        # ── Toggle Fórmula ↔ Valores (requerimiento del usuario) ──
        self._toggle = FormulaValueToggle(
            body,
            render_formula=self._render_b_formula,
            render_values=self._render_b_values,
            initial=FormulaValueToggle.MODE_VALUES,
            figsize=(5.6, 3.0),
            dpi=100,
        )
        self._toggle.pack(fill="both", expand=True, pady=(2, 4))

        # Hint educativo al pie
        ttk.Label(
            body,
            text=("Cada par de columnas en B corresponde a un nodo del "
                   "elemento (uᵢ, vᵢ). En los puntos de Gauss B vive con "
                   "superconvergencia para σ."),
            font=("Segoe UI", 8), foreground="#9e9e9e",
            wraplength=480, justify="left",
        ).pack(anchor="w", pady=(2, 0))

        self._refresh_status()

    # ── Capa educativa sobre el canvas ─────────────────────────────
    def draw_canvas_layer(self, mesh):
        """Dibuja glow pulsante en los puntos de Gauss + halo en el punto
        seleccionado. Se invoca al final de cada redraw() del MeshCanvas.
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

        # Amplitud pulsante: oscila entre 0 y 1 con seno suavizado.
        amp = 0.5 * (1.0 + math.sin(self._pulse_phase))
        # Radio outer (con respiro de la pulsación). Inner es fijo.
        r_outer = 9 + 5 * amp

        # Marcador del punto seleccionado actual: halo grueso si es Gauss,
        # halo distintivo (color naranja) si es punto libre.
        sel_xy_world = natural_to_physical(
            self._xi, self._eta, coords[: self.n_nodes], self.element_type,
        )
        sel_sx, sel_sy = mesh.world_to_screen(sel_xy_world[0], sel_xy_world[1])

        if self._gauss_index is None:
            # Punto libre: halo naranja + cruz
            r = 14
            mesh.canvas.create_oval(
                sel_sx - r, sel_sy - r, sel_sx + r, sel_sy + r,
                outline=_GAUSS_GLOW_HALO, width=2.2, dash=(4, 3), tags=_TAG,
            )

        # Dibujar TODOS los puntos de Gauss del elemento bajo análisis.
        for idx, (xi, eta) in enumerate(pts_natural):
            xy = natural_to_physical(
                xi, eta, coords[: self.n_nodes], self.element_type,
            )
            sx, sy = mesh.world_to_screen(xy[0], xy[1])

            # Anillo pulsante exterior (todos)
            mesh.canvas.create_oval(
                sx - r_outer, sy - r_outer,
                sx + r_outer, sy + r_outer,
                outline=_GAUSS_GLOW_OUTER, width=2.0, tags=_TAG,
            )
            # Punto central (relleno amarillo intenso)
            r_in = 4.5
            mesh.canvas.create_oval(
                sx - r_in, sy - r_in, sx + r_in, sy + r_in,
                fill=_GAUSS_GLOW_INNER, outline="", tags=_TAG,
            )
            # Etiqueta pgN
            mesh.canvas.create_text(
                sx + 10, sy - 10, text=f"pg{idx + 1}",
                fill=_GAUSS_GLOW_INNER, font=("Consolas", 8, "bold"),
                tags=_TAG,
            )

            # Si éste es el seleccionado, halo extra
            if idx == self._gauss_index:
                r_halo = 17
                mesh.canvas.create_oval(
                    sx - r_halo, sy - r_halo,
                    sx + r_halo, sy + r_halo,
                    outline=_GAUSS_GLOW_HALO, width=3.0, tags=_TAG,
                )

    def on_activated(self) -> None:
        # Iniciar pulse loop. El after lo controla el frame del MeshCanvas
        # para que se cancele si el widget se destruye (parent muere).
        self._pulse_phase = 0.0
        self._schedule_pulse()
        # Engancharse al click bruto del canvas para snap a Gauss aunque
        # caiga fuera de un nodo (el on_element_select default sólo
        # dispara cuando hay hit en quad). Lo hacemos via bind directo;
        # se desbindea en _cleanup vía ID guardado.
        self._click_bind_id = self._mesh.canvas.bind(
            "<ButtonRelease-1>", self._on_canvas_release, add="+",
        )

    def on_closed(self) -> None:
        if self._pulse_after_id is not None:
            try:
                self._mesh.after_cancel(self._pulse_after_id)
            except Exception:
                pass
            self._pulse_after_id = None
        # Desbindear el ButtonRelease — guardamos el funcid devuelto.
        bind_id = getattr(self, "_click_bind_id", None)
        if bind_id:
            try:
                self._mesh.canvas.unbind("<ButtonRelease-1>", bind_id)
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
        self._refresh_all()

    # ── Click directo en el canvas: snap a Gauss del elem actual ──
    def _on_canvas_release(self, event):
        if self.element is None:
            return
        try:
            coords = self._coords_macro()
        except Exception:
            return
        if coords is None or len(coords) < 4:
            return
        pts_natural, _ = get_gauss_points_for_element(self.element_type)
        # Distancia mínima en pixeles del click a cada Gauss
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
            self._refresh_all()

    # ── Refresh del overlay (tras cambio de selección/elemento) ────
    def _refresh_all(self) -> None:
        if self._toggle is not None:
            self._toggle.refresh()
        self._refresh_status()
        self._mesh.redraw()

    def _refresh_status(self) -> None:
        if self._lbl_status is None:
            return
        eid = self.element_id if self.element_id is not None else "—"
        if self._gauss_index is not None:
            tag = f"pg{self._gauss_index + 1}  (snap)"
        else:
            tag = "libre"
        self._lbl_status.configure(
            text=(f"Elemento {eid}  ·  punto: {tag}\n"
                   f"ξ = {self._xi:+.4f}     η = {self._eta:+.4f}")
        )

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

    # ── Callbacks de render del toggle ──────────────────────────────
    def _render_b_formula(self, ax) -> None:
        """Renderiza B en forma simbólica (qué ES la matriz).

        Como mathtext NO soporta entornos bmatrix, construimos la matriz
        como cells de strings (notación compacta Niₓ = ∂Nᵢ/∂x). El prefix
        mathtext acepta \\mathbf, \\dfrac, etc.
        """
        n = self.n_nodes
        # Notación compacta: N1x = ∂N1/∂x, N1y = ∂N1/∂y. Usamos sufijos
        # ASCII en lugar de subíndices Unicode (ᵧ = U+1D67 no está en
        # DejaVu Sans Mono, dispara warnings de glifo faltante).
        if n == 4:
            row1 = ["N1x", "0", "N2x", "0", "N3x", "0", "N4x", "0"]
            row2 = ["0", "N1y", "0", "N2y", "0", "N3y", "0", "N4y"]
            row3 = ["N1y", "N1x", "N2y", "N2x",
                    "N3y", "N3x", "N4y", "N4x"]
        else:  # Q9 — solo mostramos columnas extremas + elipsis
            row1 = ["N1x", "0", "N2x", "0", "...", "N9x", "0"]
            row2 = ["0", "N1y", "0", "N2y", "...", "0", "N9y"]
            row3 = ["N1y", "N1x", "N2y", "N2x", "...", "N9y", "N9x"]
        cells = [row1, row2, row3]
        render_matrix_latex(
            ax, cells, fontsize=11, color="#dcdcdc",
            prefix=r"\mathbf{B}=",
        )
        # Hint de la regla J⁻¹ debajo de la matriz
        ax.text(
            0.5, 0.05,
            r"$N_{ix}=\partial N_i/\partial x \;\;\;$"
            r"$\partial N_i/\partial x = \mathbf{J}^{-1}\,\partial N_i/\partial \xi$",
            ha="center", va="center", color="#90caf9", fontsize=10,
            transform=ax.transAxes,
        )

    def _render_b_values(self, ax) -> None:
        """Renderiza B numérica en el (ξ, η) actual."""
        B = self._compute_b()
        if B is None:
            ax.text(0.5, 0.5, "(seleccione un elemento)",
                     ha="center", va="center",
                     color="#9e9e9e", fontsize=10,
                     transform=ax.transAxes)
            return
        if self._gauss_index is not None:
            tag = f"pg{self._gauss_index + 1}"
        else:
            tag = f"ξ={self._xi:+.3f}, η={self._eta:+.3f}"
        title = f"3 × {2 * self.n_nodes}   ·   B  en  {tag}"
        # render_matrix_latex aplica mathtext sobre el ax. fontsize chico
        # para Q9 (matriz grande).
        fs = 11 if self.n_nodes == 4 else 8
        render_matrix_latex(
            ax, B, fmt="{:+.3g}", fontsize=fs, color="#dcdcdc",
            title=title, prefix=r"\mathbf{B}=",
        )
