"""Glifos compartidos del lienzo (Tk) — rediseño 2026-09-09.

Los **ejes naturales (ξ, η)** de un elemento se dibujan igual en la lente de
Proceso del `MeshCanvas` y en las capas que los módulos M1/M2/M3/M5 pintan
sobre el elemento real, con los mismos colores que los ejes del cuadrado
natural de esos módulos (`edu_plot_style.draw_natural_axes_mpl`): una sola
gramática para "esta dirección sobre el elemento" y "este eje del cuadrado".
La geometría sale de `canvas_logic.element_local_frame` (ξ apunta al punto
medio de la arista N2–N3, η al de N3–N4: la convención isoparamétrica del
motor). Sin Tk en los imports: el `canvas` llega como argumento, así el
módulo se testea con un doble sin display.
"""

from __future__ import annotations

import math

from config.settings import (
    CANVAS_XI_AXIS_COLOR, CANVAS_ETA_AXIS_COLOR, CANVAS_FONT_SIZE,
)
from gui.preprocessing.canvas_logic import element_local_frame


def draw_natural_axes(canvas, to_screen, pts, *, factor=1.0, tags=(),
                      reach=0.55):
    """Flechas ξ y η desde el centroide del cuadrilátero `pts` (4 vértices
    en orden local, coordenadas del mundo), rotuladas en la punta.

    `to_screen(x, y) -> (sx, sy)` es la transformación del lienzo; `factor`
    el reescalado de decoraciones (1.0 = tamaño base); `tags` los tags Tk de
    los ítems creados. Devuelve la cantidad de ítems dibujados (0 si no hay
    4 vértices)."""
    frame = element_local_frame(pts, reach=reach)
    if frame is None:
        return 0
    f = factor
    cx, cy = to_screen(*frame["centroid"])
    n_items = 0
    for end, color, name in ((frame["xi_end"], CANVAS_XI_AXIS_COLOR, "ξ"),
                             (frame["eta_end"], CANVAS_ETA_AXIS_COLOR, "η")):
        ex, ey = to_screen(*end)
        canvas.create_line(
            cx, cy, ex, ey, fill=color, width=2 * f, arrow="last",
            arrowshape=(8 * f, 10 * f, 4 * f), tags=tags,
        )
        n_items += 1
        dx, dy = ex - cx, ey - cy
        L = math.hypot(dx, dy)
        if L > 0:
            canvas.create_text(
                ex + dx / L * 10 * f, ey + dy / L * 10 * f, text=name,
                fill=color, font=("Segoe UI", CANVAS_FONT_SIZE + 1, "bold"),
                anchor="center", tags=tags,
            )
            n_items += 1
    return n_items
