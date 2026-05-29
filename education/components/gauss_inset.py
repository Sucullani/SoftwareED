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

Modo interactivo (M2, M4 — 2026-05):
    Pasando `interactive=True` + `on_pick=callable(xi, eta)`, el cuadrado
    natural se vuelve una SUPERFICIE DE ENTRADA: click o drag dentro del
    cuadrado fija (ξ, η) directamente y dispara `on_pick`. Esto materializa
    la dualidad de espacios — el alumno tiene DOS lugares donde fijar el
    mismo punto: el cuadrado natural (ξ,η) y el elemento físico del canvas
    (x,y). Ver el marcador moverse en ambos a la vez enseña que las
    matrices se evalúan en el espacio natural, no en el físico.
"""

from __future__ import annotations

import math
from typing import Callable, Optional, Tuple

import tkinter as tk
import ttkbootstrap as ttk

from config.settings import (
    ELEMENT_Q4, ELEMENT_Q9,
    EDU_AXES_BG, EDU_FG, EDU_FG_MUTED, EDU_LABEL_BG,
    OVERLAY_BG,
    EDU_NATURAL_OUTLINE_COLOR, EDU_NATURAL_AXES_COLOR,
)
from education.components.gauss_glyph import (
    GAUSS_CANONICAL, GAUSS_HALO, GAUSS_ACTIVE, GAUSS_GHOST,
)
from education.components.latex_status_label import LatexStatusLabel


# Tamaño por defecto del cuadrado natural en píxeles (lado). El modo
# interactivo usa un tamaño mayor (configurable via `side`) para que el
# alumno tenga un blanco cómodo de click/drag.
_INSET_SIDE = 96
_INSET_SIDE_INTERACTIVE = 150
_INSET_MARGIN = 16  # margen entre el borde del canvas y el cuadrado [-1, 1]²

# Colores del cuadrado natural — fuente única en config/settings.py
# (mismo estilo de referencia que el cuadrado matplotlib de M1).
_C_NATURAL_OUTLINE = EDU_NATURAL_OUTLINE_COLOR   # contorno del cuadrado [-1, 1]²
_C_NATURAL_AXES = EDU_NATURAL_AXES_COLOR         # ejes ξ, η (cruz en el origen)

# Tolerancia de snap (px del inset) para enganchar el click/drag al PG más
# cercano del grid activo. El snap a PG tiene PRIORIDAD sobre el punto libre.
_SNAP_TOL_PX = 13


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

    Modo interactivo: si `interactive=True`, el cuadrado captura click y
    drag, convierte la posición del cursor a (ξ, η) ∈ [-1, 1]² y dispara
    `on_pick(xi, eta)`. El caller decide qué hacer (típicamente: fijar un
    "punto libre" y refrescar la fórmula/matriz que se evalúa ahí).
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
        interactive: bool = False,
        on_pick: Optional[Callable[[float, float], None]] = None,
        title: Optional[str] = None,
        side: Optional[int] = None,
        marker_coords: bool = False,
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
        self._interactive = bool(interactive)
        self._on_pick = on_pick
        # Modo marcador (M2 2026-05): las coords (ξ,η) NO van en labels de
        # texto aparte sino PEGADAS al marcador dentro del cuadrado; el
        # cuadrado se centra y no hay panel lateral. La (x,y) física la pinta
        # el módulo en el canvas físico, también pegada a su punto.
        self._marker_coords = bool(marker_coords)
        self._selected_index: Optional[int] = None
        self._xi: float = 0.0
        self._eta: float = 0.0
        self._physical: Optional[Tuple[float, float]] = None
        # Highlight de PGs por coordenada (modo cuadratura, M5): lista de
        # (xi, eta) de los PGs "sumados". Si no es None, cada PG del grid
        # se pinta dorado (sumado) o ghost (excluido) — espeja el canvas
        # físico. Match por coordenada (tol) → desacopla del ordering de
        # cualquier generador de PGs. None = comportamiento clásico (todos
        # en color canónico).
        self._pg_highlight: Optional[list] = None
        # Tamano del cuadrado: explicito > default segun modo.
        self._side = int(side) if side else (
            _INSET_SIDE_INTERACTIVE if self._interactive else _INSET_SIDE
        )

        # ── Titulo opcional (header del widget, full-width arriba) ──
        # En modo interactivo enuncia la dualidad ("se evalua aqui, en
        # (ξ,η)") — el mensaje pedagogico clave de M2/M4.
        if title:
            tk.Label(
                self, text=title, bg=bg, fg=GAUSS_CANONICAL,
                font=("Segoe UI", 9, "bold"), anchor="w", justify="left",
            ).pack(side="top", fill="x", anchor="w", pady=(0, 3))

        if self._marker_coords:
            # Modo marcador: cuadrado natural CENTRADO, sin panel lateral ni
            # labels de texto. Las coords (ξ,η) se dibujan pegadas al marcador
            # (ver `_refresh_marker`). Más compacto y enfocado en el espacio
            # natural; la (x,y) física vive en el canvas físico del módulo.
            self._canvas = tk.Canvas(
                self, width=self._side, height=self._side,
                bg=bg, highlightthickness=0, bd=0,
                cursor="crosshair" if self._interactive else "",
            )
            self._canvas.pack(side="top", anchor="center")
            self._lbl_natural = None
            self._lbl_physical = None
        else:
            # Fila: cuadrado a la izquierda, readout dual a la derecha.
            row = ttk.Frame(self)
            row.pack(side="top", fill="x")
            self._canvas = tk.Canvas(
                row, width=self._side, height=self._side,
                bg=bg, highlightthickness=0, bd=0,
                cursor="crosshair" if self._interactive else "",
            )
            self._canvas.pack(side="left", padx=(0, 8))
            # ── Dual readout ────────────────────────────────────────
            # Lina 1: natural (ξ, η) con forma cerrada cuando aplica.
            # Lina 2: flecha →mapeo→ + físico (x, y) cuando disponible.
            # Renderizado con LatexStatusLabel: calidad documento (CMU),
            # math kerning real para ξ,η y sqrt. Fallback texto plano si
            # pdflatex no esta. Mismo bg que el overlay.
            right = ttk.Frame(row)
            right.pack(side="left", fill="both", expand=True)
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

        if self._interactive:
            self._canvas.bind("<Button-1>", self._on_canvas_pick)
            self._canvas.bind("<B1-Motion>", self._on_canvas_pick)

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

    def cleanup(self) -> None:
        """Desengancha los bindings de click/drag del canvas interno.
        Lo invoca `CanvasOverlayModule._cleanup` al cerrar el overlay
        (que hace withdraw, no destroy). Idempotente y silencioso."""
        if self._interactive:
            for evt in ("<Button-1>", "<B1-Motion>"):
                try:
                    self._canvas.unbind(evt)
                except Exception:
                    pass

    def set_pg_highlight(self, selected_coords: Optional[list]) -> None:
        """Modo cuadratura (M5): colorea los PGs del grid según estén
        "sumados" o no. `selected_coords` es una lista de (xi, eta) de los
        PGs sumados; cada PG del grid se pinta dorado si su (xi,eta) matchea
        alguno (tol 1e-3), ghost gris si no. Pasar None vuelve al coloreo
        canónico. Espeja exactamente el estado del canvas físico."""
        self._pg_highlight = selected_coords
        self._draw_inset()

    # ── Render del inset ───────────────────────────────────────────

    def _draw_inset(self) -> None:
        """Re-dibuja el cuadrado natural completo (frame + ejes + PGs).
        Se llama solo cuando cambia el orden de cuadratura."""
        c = self._canvas
        c.delete("all")

        s = self._side - 2 * _INSET_MARGIN
        cx = self._side / 2
        cy = self._side / 2

        # Contorno [-1, 1]² — línea fina, SIN relleno. M1 (matplotlib) usa
        # un relleno azul alpha 0.06 casi imperceptible; tk.Canvas no soporta
        # alpha real (solo stipple, descartado por "pesado"), así que acá el
        # cuadrado queda con contorno limpio. El COLOR del contorno y los ejes
        # es idéntico a M1 (EDU_NATURAL_OUTLINE_COLOR / EDU_NATURAL_AXES_COLOR
        # desde config/settings.py) — estilo unificado.
        c.create_rectangle(
            cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2,
            outline=_C_NATURAL_OUTLINE, width=1.0, fill="",
        )
        # Ejes ξ, η (cruz en el origen)
        c.create_line(cx - s / 2, cy, cx + s / 2, cy,
                      fill=_C_NATURAL_AXES, width=0.8)
        c.create_line(cx, cy - s / 2, cx, cy + s / 2,
                      fill=_C_NATURAL_AXES, width=0.8)
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

        # Puntos de Gauss del orden activo. En modo cuadratura
        # (_pg_highlight no None) cada PG se colorea dorado (sumado) o
        # ghost (excluido) — match por coordenada con la lista de sumados.
        pts = self._gauss_grid()
        for (xi, eta) in pts:
            sx, sy = self._nat_to_canvas(xi, eta)
            if self._pg_highlight is not None:
                summed = any(abs(xi - hx) < 1e-3 and abs(eta - hy) < 1e-3
                             for (hx, hy) in self._pg_highlight)
                if summed:
                    c.create_oval(sx - 3.5, sy - 3.5, sx + 3.5, sy + 3.5,
                                  fill=GAUSS_ACTIVE, outline="", tags="pg")
                else:
                    c.create_oval(sx - 3, sy - 3, sx + 3, sy + 3,
                                  fill="", outline=GAUSS_GHOST, width=1.0,
                                  dash=(2, 2), tags="pg")
            else:
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
        # Modo marcador: la coordenada (ξ,η) viaja PEGADA al marcador (no en
        # un label aparte). Se ubica del lado del marcador con más aire para
        # no salirse del cuadrado; sin signo `+` en positivos.
        if self._marker_coords:
            label = f"({self._xi:.3f}, {self._eta:.3f})"
            to_right = sx < self._side / 2
            tx = sx + (7 if to_right else -7)
            ty = max(7, min(self._side - 7, sy - 9))
            c.create_text(
                tx, ty, text=label, anchor=("w" if to_right else "e"),
                fill=GAUSS_HALO, font=("Consolas", 7, "bold"), tags="sel",
            )

    def _refresh_labels(self) -> None:
        """Refresca las dos líneas en LaTeX text-mode (math inline).

        Los `LatexStatusLabel` aceptan `\\textbf`/`\\text`/`$...$` y
        compilan en background. Mientras compilan muestran placeholder
        del bg del overlay (no parpadeo)."""
        # Modo marcador: no hay labels de texto — las coords van pegadas al
        # marcador (las dibuja `_refresh_marker`). Nada que refrescar acá.
        if self._lbl_natural is None:
            return
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
        s = self._side - 2 * _INSET_MARGIN
        cx = self._side / 2
        cy = self._side / 2
        sx = cx + (xi * s / 2)
        sy = cy - (eta * s / 2)
        return sx, sy

    def _canvas_to_nat(self, px: float, py: float) -> Tuple[float, float]:
        """Inverso de `_nat_to_canvas`: coords canvas (px) → (ξ, η) con
        clamp a [-1, 1]² (clicks fuera del cuadrado se anclan al borde)."""
        s = self._side - 2 * _INSET_MARGIN
        cx = self._side / 2
        cy = self._side / 2
        xi = (px - cx) / (s / 2)
        eta = -(py - cy) / (s / 2)   # flip Y
        xi = max(-1.0, min(1.0, xi))
        eta = max(-1.0, min(1.0, eta))
        return xi, eta

    def _nearest_gauss(self, px: float, py: float) -> Optional[int]:
        """Índice del PG del grid activo más cercano al cursor (en px del
        inset), o None si ninguno cae dentro de `_SNAP_TOL_PX`. El índice
        es local al grid del widget — el caller NO debe asumir que coincide
        con el ordering de fem.gauss_quadrature; el snap reporta las COORDS
        canónicas exactas (ver `_on_canvas_pick`), que el módulo matchea por
        coordenada (desacoplado del ordering)."""
        best_idx, best_d = None, float("inf")
        for idx, (gx, gy) in enumerate(self._gauss_grid()):
            sx, sy = self._nat_to_canvas(gx, gy)
            d = math.hypot(sx - px, sy - py)
            if d < best_d:
                best_d, best_idx = d, idx
        if best_idx is not None and best_d <= _SNAP_TOL_PX:
            return best_idx
        return None

    def _on_canvas_pick(self, event) -> None:
        """Click/drag dentro del cuadrado natural (modo interactivo).

        SNAP PRIORITARIO A PG: si el cursor cae dentro de `_SNAP_TOL_PX` de
        un punto de Gauss del grid activo, engancha a ese PG (coords
        canónicas exactas ±1/√3, ...) — modo discreto. Si no, fija un punto
        libre en (ξ, η) — modo continuo. En ambos casos actualiza el marcador
        local de inmediato (feedback sin latencia) y dispara `on_pick` para
        que el módulo padre re-evalúe la fórmula/matriz y refleje el punto en
        el canvas físico (bidireccionalidad).

        `on_pick(xi, eta)` recibe SIEMPRE las coords resultantes (snapped o
        libres). El módulo decide si son un PG matcheándolas por coordenada
        contra su propio grid — así el snap es robusto al ordering de PGs."""
        snap_idx = self._nearest_gauss(event.x, event.y)
        if snap_idx is not None:
            gx, gy = self._gauss_grid()[snap_idx]
            self._selected_index = snap_idx
            self._xi, self._eta = float(gx), float(gy)
        else:
            self._selected_index = None
            self._xi, self._eta = self._canvas_to_nat(event.x, event.y)
        self._refresh_marker()
        self._refresh_labels()
        if self._on_pick is not None:
            try:
                self._on_pick(self._xi, self._eta)
            except Exception:
                pass

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
