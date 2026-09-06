"""
Rasterizado del campo de resultados e isolineas del MeshCanvas, vectorizado
en NumPy y sin Tk (testeable headless: `tests/test_canvas_raster.py`).

Reemplaza los tres kernels escalares que tenia `mesh_canvas.py`
(`_rasterize_triangle_njit`, `_marching_squares_njit`, `_build_gxgy_q4_njit`)
por operaciones sobre TODOS los triangulos / celdas de la malla a la vez,
en trozos de memoria acotada. Reproduce exactamente los mismos pixeles y
los mismos segmentos que la version escalar: las formulas se aplican
elemento a elemento del array en el mismo orden de operaciones.

Convencion de grillas: cada elemento se subdivide en (n+1) x (n+1) puntos
(xi_i, eta_j) con i, j = 0..n; los arrays "de grilla" se indexan [i, j]
(i = indice de xi, j = indice de eta) y se aplanan en orden C
(p = i * (n+1) + j).
"""

from __future__ import annotations

import numpy as np


# Tabla marching squares como ndarray int32. Cada fila es un caso (0-15);
# columnas (ea1, eb1, ea2, eb2). -1 indica "sin segmento". Aristas:
# 0: v00 -> v10, 1: v10 -> v11, 2: v11 -> v01, 3: v01 -> v00.
MARCHING_SEG_TABLE = np.array([
    [-1, -1, -1, -1],   # 0:  todos abajo
    [ 0,  3, -1, -1],   # 1:  v00 arriba
    [ 0,  1, -1, -1],   # 2:  v10 arriba
    [ 1,  3, -1, -1],   # 3:  v00 + v10 arriba
    [ 1,  2, -1, -1],   # 4:  v11 arriba
    [ 0,  3,  1,  2],   # 5:  v00 + v11 — ambiguo, 2 segmentos
    [ 0,  2, -1, -1],   # 6:  v10 + v11
    [ 2,  3, -1, -1],   # 7
    [ 2,  3, -1, -1],   # 8:  v01 arriba
    [ 0,  2, -1, -1],   # 9
    [ 0,  1,  2,  3],   # 10: v10 + v01 — ambiguo
    [ 1,  2, -1, -1],   # 11
    [ 1,  3, -1, -1],   # 12
    [ 0,  1, -1, -1],   # 13
    [ 0,  3, -1, -1],   # 14
    [-1, -1, -1, -1],   # 15: todos arriba
], dtype=np.int32)

# Candidatos (pixeles de los bounding boxes de los triangulos) procesados
# por trozo. 500 k candidatos son ~60 MB de temporales float64; sin trozos,
# un viewport 2000x1400 lleno de malla superaba los 200 MB.
RASTER_CHUNK_CANDIDATES = 500_000

_SHAPE_CACHE: dict = {}
_TRI_CACHE: dict = {}


def bilinear_shape_functions(n: int) -> np.ndarray:
    """N4 (p, 4) del Q4 evaluadas en la grilla (n+1) x (n+1) de (xi, eta).

    Misma aritmetica que el kernel escalar: xi_i = -1 + 2 i / n y
    N0 = (1 - xi)(1 - eta) 0.25, etc. Cacheado por n.
    """
    N = _SHAPE_CACHE.get(n)
    if N is not None:
        return N
    xs = -1.0 + 2.0 * np.arange(n + 1) / n
    xi, eta = np.meshgrid(xs, xs, indexing="ij")
    xi = xi.ravel()
    eta = eta.ravel()
    N = np.empty((xi.size, 4))
    N[:, 0] = (1 - xi) * (1 - eta) * 0.25
    N[:, 1] = (1 + xi) * (1 - eta) * 0.25
    N[:, 2] = (1 + xi) * (1 + eta) * 0.25
    N[:, 3] = (1 - xi) * (1 + eta) * 0.25
    _SHAPE_CACHE[n] = N
    return N


def element_grid_points(corners: np.ndarray, n: int) -> np.ndarray:
    """Mapeo bilineal Q4 de los 4 corners a la grilla: (e, 4, 2) -> (e, p, 2).

    Suma explicita de los 4 terminos (no einsum) para conservar el orden de
    operaciones del kernel escalar y, con el, la paridad de pixeles.
    """
    corners = np.asarray(corners, dtype=float)
    N = bilinear_shape_functions(n)
    out = np.empty((corners.shape[0], N.shape[0], 2))
    for c in range(2):
        v = corners[:, :, c]                                   # (e, 4)
        out[:, :, c] = (N[None, :, 0] * v[:, None, 0]
                        + N[None, :, 1] * v[:, None, 1]
                        + N[None, :, 2] * v[:, None, 2]
                        + N[None, :, 3] * v[:, None, 3])
    return out


def element_grid_values(corner_values: np.ndarray, n: int) -> np.ndarray:
    """Interpolacion bilineal de 4 valores nodales a la grilla: (e, 4) -> (e, p)."""
    v = np.asarray(corner_values, dtype=float)
    N = bilinear_shape_functions(n)
    return (N[None, :, 0] * v[:, None, 0] + N[None, :, 1] * v[:, None, 1]
            + N[None, :, 2] * v[:, None, 2] + N[None, :, 3] * v[:, None, 3])


def grid_triangles(n: int) -> np.ndarray:
    """Indices (2 n^2, 3) de los triangulos de la grilla (n+1)^2, en el orden
    del kernel escalar: por celda (i, j), (p00, p10, p11) y (p00, p11, p01).
    El orden importa porque el ultimo triangulo pintado gana el pixel de
    borde compartido. Cacheado por n.
    """
    tris = _TRI_CACHE.get(n)
    if tris is not None:
        return tris
    idx = np.arange((n + 1) * (n + 1)).reshape(n + 1, n + 1)
    p00 = idx[:-1, :-1].ravel()
    p10 = idx[1:, :-1].ravel()
    p11 = idx[1:, 1:].ravel()
    p01 = idx[:-1, 1:].ravel()
    tris = np.empty((n * n, 2, 3), dtype=np.intp)
    tris[:, 0, 0], tris[:, 0, 1], tris[:, 0, 2] = p00, p10, p11
    tris[:, 1, 0], tris[:, 1, 1], tris[:, 1, 2] = p00, p11, p01
    tris = tris.reshape(-1, 3)
    _TRI_CACHE[n] = tris
    return tris


def rasterize_triangles(img: np.ndarray, tris: np.ndarray, vmin: float,
                        vmax: float, lut: np.ndarray,
                        chunk: int = RASTER_CHUNK_CANDIDATES) -> None:
    """Pinta triangulos con interpolacion baricentrica + LUT sobre `img`.

    Parametros:
        img: (H, W, 4) uint8 RGBA, se modifica in place.
        tris: (T, 3, 3) — por vertice (sx, sy, val) en pixeles de `img`.
        vmin, vmax: rango del campo -> t en [0, 1] -> lut[int(t * 255)].
        lut: (256, 3) uint8.

    Es la version vectorizada del kernel escalar: para cada triangulo se
    generan los pixeles de su bounding box (recortado a la imagen), se
    calculan las baricentricas y se descartan los de afuera con la misma
    tolerancia -0.001 (evita gaps entre triangulos vecinos). Los candidatos
    se procesan en trozos de `chunk` para acotar la memoria; el orden de
    triangulos se conserva, asi el ultimo pintado gana como en el loop.
    """
    T = np.asarray(tris, dtype=float)
    if T.size == 0:
        return
    H, W = img.shape[0], img.shape[1]
    lut = np.ascontiguousarray(lut, dtype=np.uint8)

    x = T[:, :, 0]
    y = T[:, :, 1]
    v = T[:, :, 2]
    # bbox como el kernel: int() trunca; luego se recorta a la imagen.
    min_x = np.maximum(0, np.trunc(x.min(axis=1)).astype(np.intp))
    max_x = np.minimum(W - 1, np.trunc(x.max(axis=1)).astype(np.intp) + 1)
    min_y = np.maximum(0, np.trunc(y.min(axis=1)).astype(np.intp))
    max_y = np.minimum(H - 1, np.trunc(y.max(axis=1)).astype(np.intp) + 1)

    x0, x1, x2 = x[:, 0], x[:, 1], x[:, 2]
    y0, y1, y2 = y[:, 0], y[:, 1], y[:, 2]
    denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    valid = (min_x < max_x) & (min_y < max_y) & (np.abs(denom) >= 1e-6)
    bw = np.where(valid, max_x - min_x + 1, 0)
    bh = np.where(valid, max_y - min_y + 1, 0)
    npix = bw * bh
    if not npix.any():
        return
    inv_denom = 1.0 / np.where(valid, denom, 1.0)

    vrange = vmax - vmin
    if vrange < 1e-15:
        vrange = 1e-15
    inv_vrange = 1.0 / vrange

    csum = np.cumsum(npix)
    n_tri = T.shape[0]
    start = 0
    while start < n_tri:
        base = csum[start - 1] if start > 0 else 0
        end = int(np.searchsorted(csum, base + chunk, side="right"))
        end = max(end, start + 1)
        _rasterize_chunk(img, start, end, npix, bw, min_x, min_y,
                         x0, x1, x2, y0, y1, y2, v[:, 0], v[:, 1], v[:, 2],
                         inv_denom, vmin, inv_vrange, lut)
        start = end


def _rasterize_chunk(img, start, end, npix, bw, min_x, min_y,
                     x0, x1, x2, y0, y1, y2, v0, v1, v2,
                     inv_denom, vmin, inv_vrange, lut):
    """Pinta los triangulos [start, end): expande sus bounding boxes a
    candidatos, evalua baricentricas y escribe los pixeles interiores."""
    n = npix[start:end]
    total = int(n.sum())
    if total == 0:
        return
    tri = np.repeat(np.arange(start, end), n)                 # (C,)
    starts = np.cumsum(n) - n
    off = np.arange(total) - np.repeat(starts, n)
    bwt = bw[tri]
    ix = min_x[tri] + off % bwt
    iy = min_y[tri] + off // bwt
    px = ix.astype(float)
    py = iy.astype(float)

    tx2 = x2[tri]
    ty2 = y2[tri]
    inv = inv_denom[tri]
    lam0 = ((y1 - y2)[tri] * (px - tx2) + (x2 - x1)[tri] * (py - ty2)) * inv
    lam1 = ((y2 - y0)[tri] * (px - tx2) + (x0 - x2)[tri] * (py - ty2)) * inv
    lam2 = 1.0 - lam0 - lam1
    inside = (lam0 >= -0.001) & (lam1 >= -0.001) & (lam2 >= -0.001)
    if not inside.any():
        return

    val = lam0 * v0[tri] + lam1 * v1[tri] + lam2 * v2[tri]
    t = (val - vmin) * inv_vrange
    np.clip(t, 0.0, 1.0, out=t)
    idx = (t * 255.0).astype(np.intp)
    np.clip(idx, 0, 255, out=idx)

    ix = ix[inside]
    iy = iy[inside]
    img[iy, ix, :3] = lut[idx[inside]]
    img[iy, ix, 3] = 255


def marching_squares_batch(gx: np.ndarray, gy: np.ndarray, gv: np.ndarray,
                           levels, seg_table: np.ndarray = MARCHING_SEG_TABLE):
    """Isolineas por marching squares sobre las grillas de todos los elementos.

    Parametros:
        gx, gy, gv: (e, m, m) coords mundo y valores en la grilla de cada
            elemento, layout [i, j] (i = xi, j = eta).
        levels: (n_levels,) niveles a contornear.

    Retorna segs (M, 4) con (x1, y1, x2, y2) en mundo. Mismos segmentos que
    el kernel escalar (cruce por arista interpolado, t recortado a [0, 1],
    0.5 si la arista es plana; casos ambiguos 5 y 10 con dos segmentos);
    el orden es por nivel, luego elemento, celda y segmento.
    """
    gx = np.asarray(gx, dtype=float)
    gy = np.asarray(gy, dtype=float)
    gv = np.asarray(gv, dtype=float)
    levels = np.asarray(levels, dtype=float)
    if gv.size == 0 or levels.size == 0 or gv.shape[1] < 2:
        return np.zeros((0, 4))

    # Esquinas de cada celda, aplanadas en orden C sobre (e, i, j): columnas
    # 00 = (i, j), 10 = (i+1, j), 11 = (i+1, j+1), 01 = (i, j+1). Shape (C, 4).
    def _cells(g):
        return np.stack([g[:, :-1, :-1], g[:, 1:, :-1], g[:, 1:, 1:], g[:, :-1, 1:]],
                        axis=-1).reshape(-1, 4)

    vals = _cells(gv)
    xs = _cells(gx)
    ys = _cells(gy)
    # Una celda produce segmentos solo si el nivel la cruza: min < L <= max
    # (equivale a caso != 0 y != 15). Comprimir a esas celdas por nivel es lo
    # que hace el algoritmo barato: tipicamente < 15 % de las celdas.
    cmin = vals.min(axis=1)
    cmax = vals.max(axis=1)
    # Arista k va de la esquina k a la k+1 (mod 4).
    edges = ((0, 1), (1, 2), (2, 3), (3, 0))
    out = []
    for level in levels:
        act = np.nonzero((cmin < level) & (cmax >= level))[0]
        if act.size == 0:
            continue
        va = vals[act]                                          # (A, 4)
        xa = xs[act]
        ya = ys[act]
        above = va >= level
        case = (above[:, 0].astype(np.int32) | (above[:, 1].astype(np.int32) << 1)
                | (above[:, 2].astype(np.int32) << 2) | (above[:, 3].astype(np.int32) << 3))

        n_act = act.size
        ept_x = np.empty((n_act, 4))
        ept_y = np.empty((n_act, 4))
        ept_ok = np.empty((n_act, 4), dtype=bool)
        for k, (a, b) in enumerate(edges):
            v_a = va[:, a]
            dv = va[:, b] - v_a
            flat = np.abs(dv) <= 1e-15
            t = np.where(flat, 0.5, (level - v_a) / np.where(flat, 1.0, dv))
            t = np.where(t < 0.0, 0.0, np.where(t > 1.0, 1.0, t))
            ept_x[:, k] = xa[:, a] + t * (xa[:, b] - xa[:, a])
            ept_y[:, k] = ya[:, a] + t * (ya[:, b] - ya[:, a])
            ept_ok[:, k] = above[:, a] != above[:, b]

        tab = seg_table[case]                                   # (A, 4)
        ea = tab[:, 0::2]                                       # (A, 2)
        eb = tab[:, 1::2]
        ok = (ea >= 0) & (eb >= 0)
        ea_c = np.clip(ea, 0, 3)
        eb_c = np.clip(eb, 0, 3)
        ok &= np.take_along_axis(ept_ok, ea_c, axis=1)
        ok &= np.take_along_axis(ept_ok, eb_c, axis=1)
        if not ok.any():
            continue
        seg = np.stack([
            np.take_along_axis(ept_x, ea_c, axis=1),
            np.take_along_axis(ept_y, ea_c, axis=1),
            np.take_along_axis(ept_x, eb_c, axis=1),
            np.take_along_axis(ept_y, eb_c, axis=1),
        ], axis=-1)                                             # (A, 2, 4)
        out.append(seg[ok])
    if not out:
        return np.zeros((0, 4))
    return np.concatenate(out, axis=0)
