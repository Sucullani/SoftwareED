"""
GaussCoordReadout: widget compartido para enseñar la dualidad
físico ↔ natural en los puntos de Gauss.

Motivación pedagógica:
    El concepto más confuso del enfoque isoparamétrico es que los PGs
    tienen coordenadas constantes en (ξ, η) — `±1/√3`, `±√(3/5)`, 0 — pero
    aparecen en el canvas en posiciones físicas que dependen del elemento.
    El alumno termina pensando "PG1 está en (2.3, 1.7)" cuando en realidad
    "PG1 vive en (-1/√3, -1/√3) y se proyecta a (2.3, 1.7) bajo el mapeo".

    Este widget materializa la dualidad: un cuadrado natural [-1,1]² con
    los PGs marcados (you-are-here visual) + un readout dual textual.

Uso típico en un overlay (M2, M4, M5b):

    self._gauss_readout = GaussCoordReadout(body, order=2, etype=ELEMENT_Q4)
    self._gauss_readout.pack(fill="x", pady=(0, 4))

    # En set_element / on_canvas_click_consume:
    self._gauss_readout.set_state(
        order=self._order,
        etype=self.element_type,
        selected_index=self._gauss_index,   # 0..n-1, None si libre
        xi=self._xi, eta=self._eta,
        physical=(x, y),                     # opcional
    )

Diseño visual:
    [  cuadrado natural 90px  ]  ξ,η = (-0.577, -0.577) = (-1/√3, -1/√3)
    [  4/9 PGs como dots      ]  →mapeo→ x,y = (2.31, 1.74)
    [  selección iluminada    ]
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import tkinter as tk
import ttkbootstrap as ttk

from config.settings import (
    ELEMENT_Q4, ELEMENT_Q9,
    EDU_AXES_BG, EDU_FG, EDU_FG_MUTED, EDU_LABEL_BG,
    OVERLAY_BG,
)
from education.components.gauss_glyph import (
    GAUSS_CANONICAL, GAUSS_HALO, GAUSS_ACTIVE, GAUSS_GHOST,
)
from education.components.latex_status_label import LatexStatusLabel


# Tamaño del cuadrado natural en píxeles (lado).
_INSET_SIDE = 96
_INSET_MARGIN = 14  # margen entre el borde del canvas y el cuadrado [-1, 1]²


class GaussCoordReadout(ttk.Frame):
    """Inset del cuadrado natural + dual readout de coords.

    Compone dos widgets:
      - Un `tk.Canvas` cuadrado mostrando el cuadrado natural con los
        PGs del orden de cuadratura activo. El PG seleccionado se ilumina
        en naranja (GAUSS_HALO) y emite un anillo dashed.
      - Una etiqueta Tk con dos líneas: la (ξ, η) y la (x, y) cuando está
        disponible. La fila (ξ, η) incluye la forma cerrada (`±1/√3` o
        `±√(3/5)`) para reforzar que son constantes universales, no
        números arbitrarios.
    """

    # Forma cerrada de las coords naturales para cada orden. Match contra
    # el valor numérico con tolerancia 1e-3. Si no matchea, se muestra solo
    # el decimal.
    _CLOSED_FORMS_1D = {
        1: [(0.0, "0")],
        2: [(-1.0 / math.sqrt(3), "-1/√3"),
            ( 1.0 / math.sqrt(3),  "+1/√3")],
        3: [(-math.sqrt(3.0 / 5.0), "-√(3/5)"),
            ( 0.0,                  "0"),
            ( math.sqrt(3.0 / 5.0), "+√(3/5)")],
    }

    def __init__(
        self,
        parent: tk.Widget,
        *,
        order: int = 2,
        etype: str = ELEMENT_Q4,
        bg: Optional[str] = None,
    ):
        super().__init__(parent)
        # Inferir bg del parent (un ttk.Frame del tema darkly tiene bg
        # distinto a la constante OVERLAY_BG estatica). Sin esto, el
        # tk.Canvas del inset y los LatexStatusLabel mostrarian un
        # rectangulo de color distinto al overlay circundante.
        if bg is None:
            from education.components.latex_image import _infer_bg
            bg = _infer_bg(parent)
        self._order = max(1, min(3, order))
        self._etype = etype
        self._bg = bg
        self._selected_index: Optional[int] = None
        self._xi: float = 0.0
        self._eta: float = 0.0
        self._physical: Optional[Tuple[float, float]] = None

        # ── Inset del cuadrado natural ──────────────────────────
        self._canvas = tk.Canvas(
            self, width=_INSET_SIDE, height=_INSET_SIDE,
            bg=bg, highlightthickness=0, bd=0,
        )
        self._canvas.pack(side="left", padx=(0, 8))

        # ── Dual readout ────────────────────────────────────────
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)

        # Lina 1: natural (ξ, η) con forma cerrada cuando aplica.
        # Lina 2: flecha →mapeo→ + físico (x, y) cuando disponible.
        # Renderizado con LatexStatusLabel: calidad documento (CMU),
        # math kerning real para ξ,η y sqrt. Fallback texto plano si
        # pdflatex no esta. Mismo bg que el overlay para integracion visual.
        self._lbl_natural = LatexStatusLabel(
            right, text="", bg=bg, color=GAUSS_CANONICAL,
            fontsize=10, anchor="w",
        )
        self._lbl_natural.pack(fill="x", anchor="w")
        self._lbl_physical = LatexStatusLabel(
            right, text="", bg=bg, color=EDU_FG_MUTED,
            fontsize=10, anchor="w",
        )
        self._lbl_physical.pack(fill="x", anchor="w")

        self._draw_inset()
        self._refresh_labels()

    # ── API pública ────────────────────────────────────────────────

    def set_state(
        self,
        *,
        order: Optional[int] = None,
        etype: Optional[str] = None,
        selected_index: Optional[int] = -1,   # sentinel = no cambiar
        xi: Optional[float] = None,
        eta: Optional[float] = None,
        physical: Optional[Tuple[float, float]] = -1,  # sentinel = no cambiar
    ) -> None:
        """Actualiza el estado del readout. Solo los parámetros no-sentinel
        se reemplazan; permite refreshes parciales (ej. cambio de ξ,η sin
        tocar el orden de cuadratura)."""
        changed_grid = False
        if order is not None and order != self._order:
            self._order = max(1, min(3, order))
            changed_grid = True
        if etype is not None and etype != self._etype:
            self._etype = etype
            # Nota: el cuadrado natural NO cambia con el tipo de elemento
            # (Q4 y Q9 comparten [-1, 1]²); el grid de PGs sí cambia con
            # el orden, no con el etype. Mantenemos el flag por consistencia.

        # Sentinel para distinguir "no cambiar" vs "limpiar a None".
        if selected_index != -1:
            self._selected_index = selected_index
        if xi is not None:
            self._xi = float(xi)
        if eta is not None:
            self._eta = float(eta)
        if physical != -1:
            self._physical = physical

        if changed_grid:
            self._draw_inset()
        else:
            self._refresh_marker()
        self._refresh_labels()

    def clear(self) -> None:
        """Resetea el widget a estado vacío (sin PG seleccionado)."""
        self._selected_index = None
        self._xi, self._eta = 0.0, 0.0
        self._physical = None
        self._refresh_marker()
        self._refresh_labels()

    # ── Render del inset ───────────────────────────────────────────

    def _draw_inset(self) -> None:
        """Re-dibuja el cuadrado natural completo (frame + ejes + PGs).
        Se llama solo cuando cambia el orden de cuadratura."""
        c = self._canvas
        c.delete("all")

        s = _INSET_SIDE - 2 * _INSET_MARGIN
        cx = _INSET_SIDE / 2
        cy = _INSET_SIDE / 2

        # Marco [-1, 1]²
        c.create_rectangle(
            cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2,
            outline="#4fa3ff", width=1.4, fill="",
        )
        c.create_rectangle(
            cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2,
            outline="", fill="#4fa3ff", stipple="gray12",
        )
        # Ejes ξ, η (cruz en el origen)
        c.create_line(cx - s / 2, cy, cx + s / 2, cy,
                      fill="#3a5278", width=0.8)
        c.create_line(cx, cy - s / 2, cx, cy + s / 2,
                      fill="#3a5278", width=0.8)
        c.create_text(cx + s / 2 + 5, cy + 1,
                      text="ξ", fill=EDU_FG_MUTED,
                      font=("Consolas", 8, "bold"))
        c.create_text(cx + 1, cy - s / 2 - 6,
                      text="η", fill=EDU_FG_MUTED,
                      font=("Consolas", 8, "bold"))

        # Etiquetas ±1 para anclar la escala (sin saturar — solo esquinas)
        c.create_text(cx + s / 2, cy + s / 2 + 6,
                      text="+1", fill=EDU_FG_MUTED, font=("Consolas", 7))
        c.create_text(cx - s / 2, cy + s / 2 + 6,
                      text="-1", fill=EDU_FG_MUTED, font=("Consolas", 7))

        # Puntos de Gauss del orden activo
        pts = self._gauss_grid()
        for (xi, eta) in pts:
            sx, sy = self._nat_to_canvas(xi, eta)
            c.create_oval(sx - 3, sy - 3, sx + 3, sy + 3,
                          fill=GAUSS_CANONICAL, outline="", tags="pg")

        # Marcador de selección (se redibuja en _refresh_marker)
        self._refresh_marker()

    def _refresh_marker(self) -> None:
        """Repinta solo el marcador del PG seleccionado / punto libre.
        No toca el grid de PGs ni el frame — más barato que `_draw_inset`."""
        c = self._canvas
        c.delete("sel")
        if self._selected_index is None and self._xi == 0.0 and self._eta == 0.0:
            return

        sx, sy = self._nat_to_canvas(self._xi, self._eta)
        # Halo dashed para el punto seleccionado (PG snapped o libre)
        c.create_oval(sx - 6, sy - 6, sx + 6, sy + 6,
                      outline=GAUSS_HALO, width=1.8, dash=(3, 2), tags="sel")
        # Disco pequeño relleno encima del PG (refuerza la posición)
        c.create_oval(sx - 2.5, sy - 2.5, sx + 2.5, sy + 2.5,
                      fill=GAUSS_HALO, outline="", tags="sel")

    def _refresh_labels(self) -> None:
        """Refresca las dos líneas en LaTeX text-mode (math inline).

        Los `LatexStatusLabel` aceptan `\\textbf`/`\\text`/`$...$` y
        compilan en background. Mientras compilan muestran placeholder
        del bg del overlay (no parpadeo)."""
        # Línea 1: natural
        if self._selected_index is None and self._xi == 0.0 and self._eta == 0.0:
            self._lbl_natural.set_text(
                r"$(\xi, \eta)$ = libre $-$ click en un PG"
            )
            self._lbl_physical.set_text("")
            return

        xi_str, xi_closed = self._format_closed(self._xi)
        eta_str, eta_closed = self._format_closed(self._eta)
        xi_tex = _decimal_to_latex(xi_str)
        eta_tex = _decimal_to_latex(eta_str)
        if xi_closed and eta_closed and self._selected_index is not None:
            xi_clo_tex = _closed_to_latex(xi_closed)
            eta_clo_tex = _closed_to_latex(eta_closed)
            line1 = (rf"$(\xi, \eta) = ({xi_tex},\ {eta_tex})"
                     rf" \;=\; ({xi_clo_tex},\ {eta_clo_tex})$")
        else:
            line1 = rf"$(\xi, \eta) = ({xi_tex},\ {eta_tex})$"
        self._lbl_natural.set_text(line1)

        # Línea 2: físico (cuando disponible)
        if self._physical is not None:
            x, y = self._physical
            x_tex = _decimal_to_latex(f"{x:+.3f}")
            y_tex = _decimal_to_latex(f"{y:+.3f}")
            line2 = rf"$\to$ mapeo $\to$ $\;(x, y) = ({x_tex},\ {y_tex})$"
            self._lbl_physical.set_text(line2)
        else:
            self._lbl_physical.set_text("")

    # ── Helpers ────────────────────────────────────────────────────

    def _gauss_grid(self):
        """Devuelve [(ξ, η), ...] del orden activo (1×1, 2×2 o 3×3)."""
        if self._order not in self._CLOSED_FORMS_1D:
            return []
        coords_1d = [v for (v, _label) in self._CLOSED_FORMS_1D[self._order]]
        return [(xi, eta) for eta in coords_1d for xi in coords_1d]

    def _nat_to_canvas(self, xi: float, eta: float) -> Tuple[float, float]:
        """Mapea (ξ, η) ∈ [-1, 1]² → coords canvas (px). Flip Y: η positivo
        hacia arriba en pantalla."""
        s = _INSET_SIDE - 2 * _INSET_MARGIN
        cx = _INSET_SIDE / 2
        cy = _INSET_SIDE / 2
        sx = cx + (xi * s / 2)
        sy = cy - (eta * s / 2)
        return sx, sy

    def _format_closed(self, v: float) -> Tuple[str, Optional[str]]:
        """Retorna (string decimal, string forma cerrada o None).

        La forma cerrada solo se ofrece si v matchea contra alguna entrada
        de _CLOSED_FORMS_1D en el orden actual con tol 1e-3. Para puntos
        libres (drag manual) solo decimal.
        """
        dec = f"{v:+.3f}"
        if self._order in self._CLOSED_FORMS_1D:
            for val, label in self._CLOSED_FORMS_1D[self._order]:
                if abs(v - val) < 1e-3:
                    return dec, label
        return dec, None


# ─── Helpers de formateo LaTeX para LatexStatusLabel ───────────────────────


def _decimal_to_latex(s: str) -> str:
    """`+0.577` -> `+0.577` (math-safe). Los signos y digitos son tokens
    validos en math mode tal cual; solo proteccion contra strings vacios."""
    return s.strip() or "0"


def _closed_to_latex(s: str) -> str:
    """Mapea las formas cerradas Unicode usadas en `_CLOSED_FORMS_1D` a
    LaTeX puro (Computer Modern):
       `-1/√3`      -> `-1/\\sqrt{3}`
       `+1/√3`      -> `+1/\\sqrt{3}`
       `-√(3/5)`    -> `-\\sqrt{3/5}`
       `+√(3/5)`    -> `+\\sqrt{3/5}`
       `0`          -> `0`
    """
    if not s:
        return "0"
    s = s.replace("√(3/5)", r"\sqrt{3/5}")
    s = s.replace("√3", r"\sqrt{3}")
    return s
