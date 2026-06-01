"""
QualityBar: barra horizontal de calidad con gradiente, ticks y marcador.

Widget self-contained `tk.Canvas` que renderiza una metrica de calidad
geometrica como una barra de gradiente con:
  - Gradiente cromatico continuo (rojo/amarillo/verde o rojo/gris/verde
    en modo bipolar).
  - Tick marks con valores numericos como anclas de escala.
  - Marcador (triangulo + linea + badge numerico) en el valor actual.

Disenado para los modulos educativos que reportan metricas normalizadas
(M0 inicial; reutilizable por futuros modulos de auditoria/verificacion).

Modos:
  - bipolar=True : rango con cero como centro (rojo a la izq, gris en
                   el origen, verde a la der). Ideal para Scaled Jacobian
                   in [-1, 1] donde 0 es la frontera de validez.
  - bipolar=False: rango unidireccional [0, max]. Rojo -> amarillo en
                   `thresholds[0]`, amarillo -> verde en `thresholds[1]`.
                   Ideal para metricas en [0, 1] con 1 = mejor.

API minima:
    bar = QualityBar(parent, range_min=-1, range_max=1, bipolar=True)
    bar.pack(fill="x")
    bar.set_value(0.95)   # mueve el marcador
    bar.set_value(None)   # oculta el marcador
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import tkinter as tk

from config.settings import (
    HEALTH_OK_COLOR, HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR,
    EDU_FG_MUTED, OVERLAY_BG, EDU_MARKER_OUTLINE_COLOR,
    QUALITY_BAR_NEUTRAL_COLOR, QUALITY_BAR_INK_COLOR,
)


# Gris neutro para el modo bipolar (la "frontera" en 0 del Jacobiano).
# No competimos con el amarillo del modo unipolar para que el alumno lea
# inmediatamente "esto no es bueno ni malo, es la frontera".
_NEUTRAL_GRAY = QUALITY_BAR_NEUTRAL_COLOR
_BADGE_BG = EDU_MARKER_OUTLINE_COLOR
_BADGE_FG = QUALITY_BAR_INK_COLOR
_MARKER_LINE = EDU_MARKER_OUTLINE_COLOR
_MARKER_TRI_OUTLINE = QUALITY_BAR_INK_COLOR
_TICK_LINE = QUALITY_BAR_INK_COLOR


def fmt_es(value: float, digits: int = 2) -> str:
    """Formatea un float al estilo decimal espanol (coma).

    Helper publico — reutilizable por los modulos educativos que necesiten
    presentar numeros con coma en lugar de punto. Mantiene la convencion
    sin importar el locale del sistema.
    """
    if value is None:
        return "—"
    if math.isnan(value) or math.isinf(value):
        return "—"
    return f"{value:.{digits}f}".replace(".", ",")


# Alias corto local — los modulos que solo necesitan formatear pueden
# importar `fmt_es` con su nombre completo desde fuera, pero dentro de
# este widget usamos `_es` para mantener las lineas cortas.
_es = fmt_es


# Interpolacion HEX: fuente única en gauss_glyph (antes triplicada acá +
# mod02._lerp_color + gauss_glyph). `_lerp` queda como alias local.
from education.components.gauss_glyph import lerp_hex as _lerp


class QualityBar(tk.Canvas):
    """Barra horizontal de calidad."""

    # Layout vertical (px):
    #   [0  ..  12]  badge del valor numerico (flota arriba del triangulo)
    #   [12 ..  18]  triangulo apuntando hacia abajo
    #   [18 ..  38]  barra de gradiente (20 px de alto)
    #   [38 ..  50]  tick labels (texto de los ticks)
    #   [50 ..  60]  marcador "acept." del umbral aceptable (si accept_cutoff)
    HEIGHT = 60
    _BAR_TOP = 18
    _BAR_BOT = 38
    _BAR_PAD_X = 14

    def __init__(
        self,
        parent: tk.Widget,
        *,
        range_min: float = 0.0,
        range_max: float = 1.0,
        ticks: Optional[Tuple[float, ...]] = None,
        thresholds: Tuple[float, float] = (0.4, 0.7),
        accept_cutoff: Optional[float] = None,
        bipolar: bool = False,
        decimals: int = 3,
        bg: Optional[str] = None,
        **kw,
    ):
        if bg is None:
            try:
                from education.components.latex_image import _infer_bg
                bg = _infer_bg(parent)
            except Exception:
                bg = OVERLAY_BG
        super().__init__(
            parent, height=self.HEIGHT, bg=bg,
            highlightthickness=0, bd=0, **kw,
        )
        self._rmin = float(range_min)
        self._rmax = float(range_max)
        self._bipolar = bool(bipolar)
        self._thresholds = thresholds
        # Umbral "aceptable" de la bibliografia (Verdict/Cubit): se marca con
        # una linea de referencia fija + rotulo "acept." para que el alumno
        # vea donde empieza lo admisible (distinto por metrica).
        self._accept_cutoff = accept_cutoff
        self._decimals = decimals
        self._ticks = ticks if ticks is not None else self._default_ticks()
        self._value: Optional[float] = None
        self._bg = bg
        # Cache del ancho ultimo para evitar re-render innecesario en
        # eventos <Configure> que no cambian el width (frecuente en Tk).
        self._cached_w = -1
        self.bind("<Configure>", self._on_resize)

    # ── API publica ────────────────────────────────────────────────
    def set_value(self, value: Optional[float]) -> None:
        """Posiciona el marcador en `value`. `None` lo oculta."""
        self._value = value
        self._redraw()

    # ── Implementacion ─────────────────────────────────────────────
    def _default_ticks(self) -> Tuple[float, ...]:
        if self._bipolar:
            return (-1.0, -0.5, 0.0, 0.5, 0.85, 1.0)
        return (0.0, 0.4, 0.7, 0.85, 1.0)

    def _on_resize(self, _ev) -> None:
        W = self.winfo_width()
        if W == self._cached_w:
            return
        self._cached_w = W
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        W = self.winfo_width()
        if W < 20:
            return

        bar_left = self._BAR_PAD_X
        bar_right = W - self._BAR_PAD_X
        bar_w = max(1, bar_right - bar_left)

        # ── 1) Gradiente: 1 linea vertical por px ──
        # Costo ~ O(bar_w) ≈ 200-400 lineas por refresh. <2 ms en hardware
        # tipico, no requiere cache PIL.
        for px in range(int(bar_w)):
            t = px / max(1, bar_w - 1)
            v = self._rmin + t * (self._rmax - self._rmin)
            color = self._color_at(v)
            self.create_line(
                bar_left + px, self._BAR_TOP,
                bar_left + px, self._BAR_BOT,
                fill=color,
            )

        # ── 2) Tick marks + labels ──
        for tv in self._ticks:
            tx = self._value_to_x(tv, bar_left, bar_right)
            self.create_line(
                tx, self._BAR_TOP - 1, tx, self._BAR_BOT + 1,
                fill=_TICK_LINE, width=1,
            )
            digits = 1 if (abs(tv) >= 1.0 or tv == 0.0) else 2
            self.create_text(
                tx, self._BAR_BOT + 3,
                text=_es(tv, digits),
                font=("Consolas", 7), fill=EDU_FG_MUTED, anchor="n",
            )

        # ── 2b) Umbral "aceptable" de la bibliografia (linea de referencia
        # fija, distinta del marcador de valor: dashed en vez de solida) ──
        if self._accept_cutoff is not None:
            ax = self._value_to_x(self._accept_cutoff, bar_left, bar_right)
            self.create_line(
                ax, self._BAR_TOP - 4, ax, self._BAR_BOT + 1,
                fill=_MARKER_LINE, width=1, dash=(2, 2),
            )
            self.create_text(
                ax, self._BAR_BOT + 13, text="acept.",
                font=("Consolas", 6), fill=EDU_FG_MUTED, anchor="n",
            )

        # ── 3) Marker (badge + triangulo + linea) ──
        if self._value is None or math.isnan(self._value):
            return

        v_clamped = max(self._rmin, min(self._rmax, self._value))
        mx = self._value_to_x(v_clamped, bar_left, bar_right)

        # Linea vertical blanca que cruza la barra
        self.create_line(
            mx, self._BAR_TOP - 1, mx, self._BAR_BOT + 1,
            fill=_MARKER_LINE, width=2,
        )
        # Triangulo apuntando hacia abajo
        self.create_polygon(
            mx - 5, self._BAR_TOP - 8,
            mx + 5, self._BAR_TOP - 8,
            mx, self._BAR_TOP - 1,
            fill=_MARKER_LINE, outline=_MARKER_TRI_OUTLINE, width=1,
        )
        # Badge con valor numerico
        text = _es(self._value, self._decimals)
        # Ancho del badge ~ 7 px por char + padding; minimo 36 px
        badge_half = max(18, 4 * len(text) + 4)
        badge_x0 = max(2, mx - badge_half)
        badge_x1 = min(W - 2, mx + badge_half)
        # Si el marcador esta cerca del borde, desplazar el badge para
        # que no se salga del canvas (mantener el ancho).
        if badge_x1 - badge_x0 < 2 * badge_half:
            if badge_x0 <= 2:
                badge_x1 = min(W - 2, badge_x0 + 2 * badge_half)
            elif badge_x1 >= W - 2:
                badge_x0 = max(2, badge_x1 - 2 * badge_half)
        self.create_rectangle(
            badge_x0, 0, badge_x1, 11,
            fill=_BADGE_BG, outline=_MARKER_TRI_OUTLINE, width=1,
        )
        self.create_text(
            (badge_x0 + badge_x1) / 2, 5.5,
            text=text, font=("Consolas", 8, "bold"),
            fill=_BADGE_FG, anchor="center",
        )

    def _color_at(self, v: float) -> str:
        if self._bipolar:
            # Modo bipolar: -1=rojo -> 0=gris -> +1=verde
            if v <= 0:
                # v en [rmin, 0] -> t en [0, 1] hacia el gris
                span = max(1e-9, abs(self._rmin))
                t = (v - self._rmin) / span
                return _lerp(HEALTH_ERROR_COLOR, _NEUTRAL_GRAY, t)
            else:
                t = v / max(1e-9, self._rmax)
                return _lerp(_NEUTRAL_GRAY, HEALTH_OK_COLOR, t)
        # Modo unipolar: 0=rojo -> t1=amarillo -> t2=verde
        t1, t2 = self._thresholds
        if v < t1:
            t = max(0.0, v) / max(1e-9, t1)
            return _lerp(HEALTH_ERROR_COLOR, HEALTH_WARNING_COLOR, t)
        if v < t2:
            t = (v - t1) / max(1e-9, t2 - t1)
            return _lerp(HEALTH_WARNING_COLOR, HEALTH_OK_COLOR, t)
        return HEALTH_OK_COLOR

    def _value_to_x(self, v: float, x0: float, x1: float) -> float:
        t = (v - self._rmin) / max(1e-9, self._rmax - self._rmin)
        return x0 + max(0.0, min(1.0, t)) * (x1 - x0)


__all__ = ["QualityBar", "fmt_es"]
