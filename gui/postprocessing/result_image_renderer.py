"""
ResultImageRenderer: renderiza un campo nodal a una imagen PIL.

Replica el pipeline visual del MeshCanvas del Post-Proceso (LUT perceptual
viridis/coolwarm + gradiente bilineal Gouraud + wireframe blanco) pero
genera una imagen estatica (PIL.Image) en lugar de pintar sobre un
tk.Canvas interactivo.

Usado por:
  - education/mod09_q4_vs_q9_comparison.py: 8 mini-paneles del grid 2x4
    de comparacion Q4 vs Q9 -- cada panel reusa esta funcion para
    mostrar el mismo "look" que el canvas del Post.

Decision pedagogica: M9 usaba matplotlib pcolormesh para los 8 paneles,
lo cual cromaticamente no coincidia con el contorno del Post y agregaba
ticks/labels de matplotlib. Con esta funcion las 8 mini-vistas se ven
IDENTICAS al canvas principal -- el alumno reconoce los mismos colores.
Auditoria UX 2026-05: ambos migraron de JET a viridis/coolwarm; este
modulo sigue al canvas usando el mismo LUT (config/colormaps).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from config.colormaps import (
    VIRIDIS_LUT, COOLWARM_LUT, is_diverging_range, symmetric_bounds,
)

try:
    from PIL import Image  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _lut_rgb_u8(t: np.ndarray, lut):
    """t en [0,1] (array) -> canales (r, g, b) uint8 leidos del LUT."""
    idx = np.clip((t * 255.0).astype(np.int64), 0, 255)
    return lut[idx, 0], lut[idx, 1], lut[idx, 2]


def _rasterize_triangle(img, w, h, p0, p1, p2, vmin, v_range, lut):
    """Rasteriza un triangulo con interpolacion baricentrica + LUT.

    Cada p es (sx, sy, valor). Identica logica que MeshCanvas._rasterize_triangle.
    """
    sx0, sy0, v0 = p0
    sx1, sy1, v1 = p1
    sx2, sy2, v2 = p2

    min_x = max(0, int(min(sx0, sx1, sx2)))
    max_x = min(w - 1, int(max(sx0, sx1, sx2)) + 1)
    min_y = max(0, int(min(sy0, sy1, sy2)))
    max_y = min(h - 1, int(max(sy0, sy1, sy2)) + 1)
    if min_x >= max_x or min_y >= max_y:
        return

    px = np.arange(min_x, max_x + 1, dtype=np.float64)
    py = np.arange(min_y, max_y + 1, dtype=np.float64)
    PX, PY = np.meshgrid(px, py)

    denom = (sy1 - sy2) * (sx0 - sx2) + (sx2 - sx1) * (sy0 - sy2)
    if abs(denom) < 1e-6:
        return

    lam0 = ((sy1 - sy2) * (PX - sx2) + (sx2 - sx1) * (PY - sy2)) / denom
    lam1 = ((sy2 - sy0) * (PX - sx2) + (sx0 - sx2) * (PY - sy2)) / denom
    lam2 = 1.0 - lam0 - lam1

    inside = (lam0 >= -0.001) & (lam1 >= -0.001) & (lam2 >= -0.001)
    if not np.any(inside):
        return

    vals = lam0 * v0 + lam1 * v1 + lam2 * v2
    t = np.clip((vals - vmin) / v_range, 0, 1)
    rc, gc, bc = _lut_rgb_u8(t, lut)

    iy = PY[inside].astype(int)
    ix = PX[inside].astype(int)
    valid = (iy >= 0) & (iy < h) & (ix >= 0) & (ix < w)
    iy, ix = iy[valid], ix[valid]
    img[iy, ix, 0] = rc[inside][valid]
    img[iy, ix, 1] = gc[inside][valid]
    img[iy, ix, 2] = bc[inside][valid]
    img[iy, ix, 3] = 255


def render_result_to_pil(
    project,
    node_values: dict,
    vmin: float,
    vmax: float,
    width: int,
    height: int,
    *,
    padding: int = 12,
    wireframe: bool = True,
    bg_rgba=(34, 34, 51, 255),
) -> Optional["Image.Image"]:
    """Renderiza el campo `node_values` sobre `project` a una PIL.Image.

    Args:
        project: ProjectModel con nodes + elements.
        node_values: dict {node_id: float} con el valor del campo en cada nodo.
            (Modo SUAVIZADO -- promediado nodal. M9 no usa modo crudo en
            la vista panoramica para mantener la comparacion limpia.)
        vmin, vmax: rango del colormap. Si difieren <1e-12, se ajusta.
        width, height: dimensiones de la imagen resultante.
        padding: margen en pixeles alrededor del modelo (default 12).
        wireframe: si True, dibuja aristas macro en blanco sobre la imagen.
        bg_rgba: color de fondo (default azul oscuro coherente con MOHR_BG).

    Returns:
        PIL.Image en modo RGBA, o None si PIL no esta disponible o el
        proyecto no tiene elementos.
    """
    if not HAS_PIL:
        return None
    if not project.nodes or not project.elements:
        return None

    from PIL import Image, ImageDraw

    # ── 1. Calcular transform world -> screen ────────────────────────
    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    if not xs:
        return None
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    span_x = max(x_max - x_min, 1e-9)
    span_y = max(y_max - y_min, 1e-9)
    avail_w = width - 2 * padding
    avail_h = height - 2 * padding
    scale = min(avail_w / span_x, avail_h / span_y)
    # Centrar
    used_w = span_x * scale
    used_h = span_y * scale
    offset_x = padding + (avail_w - used_w) / 2 - x_min * scale
    offset_y = padding + (avail_h - used_h) / 2 + y_max * scale

    def w2s(x, y):
        return x * scale + offset_x, -y * scale + offset_y

    # ── 2. Setup buffer + rango de colormap ──────────────────────────
    img_arr = np.zeros((height, width, 4), dtype=np.uint8)
    img_arr[..., 0] = bg_rgba[0]
    img_arr[..., 1] = bg_rgba[1]
    img_arr[..., 2] = bg_rgba[2]
    img_arr[..., 3] = bg_rgba[3]

    # Colormap coherente con el canvas: coolwarm divergente (centrado en 0)
    # si el rango cruza el cero, viridis secuencial si no.
    if is_diverging_range(vmin, vmax):
        lut = COOLWARM_LUT
        vmin, vmax = symmetric_bounds(vmin, vmax)
    else:
        lut = VIRIDIS_LUT
    v_range = max(vmax - vmin, 1e-15)

    # ── 3. Render por elemento (mismo algoritmo que MeshCanvas) ──────
    n = 6  # subdivisiones por arista (igual que mesh_canvas._draw_gradient_elements)
    for elem in project.elements.values():
        nids = elem.node_ids[:4]
        if not all(nid in project.nodes for nid in nids):
            continue
        if not all(nid in node_values for nid in nids):
            continue

        nv = [float(node_values[nid]) for nid in nids]
        nc = [(project.nodes[nid].x, project.nodes[nid].y) for nid in nids]

        # Grilla (n+1, n+1) de puntos (sx, sy, val)
        pts_grid = {}
        for i in range(n + 1):
            xi = -1 + 2 * i / n
            for j in range(n + 1):
                eta = -1 + 2 * j / n
                N0 = (1 - xi) * (1 - eta) * 0.25
                N1 = (1 + xi) * (1 - eta) * 0.25
                N2 = (1 + xi) * (1 + eta) * 0.25
                N3 = (1 - xi) * (1 + eta) * 0.25
                wx = (N0 * nc[0][0] + N1 * nc[1][0]
                       + N2 * nc[2][0] + N3 * nc[3][0])
                wy = (N0 * nc[0][1] + N1 * nc[1][1]
                       + N2 * nc[2][1] + N3 * nc[3][1])
                sx, sy = w2s(wx, wy)
                val = N0 * nv[0] + N1 * nv[1] + N2 * nv[2] + N3 * nv[3]
                pts_grid[(i, j)] = (sx, sy, val)

        # Subdividir en triangulos
        for i in range(n):
            for j in range(n):
                p00 = pts_grid[(i, j)]
                p10 = pts_grid[(i + 1, j)]
                p11 = pts_grid[(i + 1, j + 1)]
                p01 = pts_grid[(i, j + 1)]
                _rasterize_triangle(img_arr, width, height, p00, p10, p11,
                                     vmin, v_range, lut)
                _rasterize_triangle(img_arr, width, height, p00, p11, p01,
                                     vmin, v_range, lut)

    img = Image.fromarray(img_arr, "RGBA")

    # ── 4. Wireframe (aristas macro en blanco) ───────────────────────
    if wireframe:
        draw = ImageDraw.Draw(img)
        for elem in project.elements.values():
            nids = elem.node_ids[:4]
            if not all(nid in project.nodes for nid in nids):
                continue
            coords = []
            for nid in nids:
                node = project.nodes[nid]
                coords.append(w2s(node.x, node.y))
            # Cerrar el poligono
            coords.append(coords[0])
            for k in range(4):
                draw.line([coords[k], coords[k + 1]],
                           fill=(255, 255, 255, 180), width=1)

    return img
