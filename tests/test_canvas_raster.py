"""
test_canvas_raster.py - Paridad del rasterizador e isolineas vectorizados
(gui/preprocessing/canvas_raster.py) contra los kernels escalares que tenia
mesh_canvas.py (copiados aqui como oraculo, en Python puro).

Chequea pixel a pixel el gradiente Gouraud + LUT, el conjunto de segmentos
de marching squares y el mapeo bilineal de la grilla, sobre mallas
aleatorias. Incluye el contorno de la Memoria de Calculo
(file_io/figure_export._fill_field), que reusa el mismo kernel por lotes.
Corre sin Tk.

Ejecutar: python -m tests.test_canvas_raster
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.colormaps import JET_LUT
from gui.preprocessing.canvas_raster import (
    MARCHING_SEG_TABLE, element_grid_points, element_grid_values,
    grid_triangles, marching_squares_batch, rasterize_triangles,
)

_checks = []


def check(name, cond):
    _checks.append((name, bool(cond)))
    print(f"  [{'OK' if cond else 'FAIL'}] {name}")


# ─── Oraculos: kernels escalares originales ─────────────────────────────────

def _rasterize_triangle_ref(img, W, H, sx0, sy0, v0, sx1, sy1, v1,
                            sx2, sy2, v2, vmin, vmax, lut):
    min_x = max(0, int(min(sx0, sx1, sx2)))
    max_x = min(W - 1, int(max(sx0, sx1, sx2)) + 1)
    min_y = max(0, int(min(sy0, sy1, sy2)))
    max_y = min(H - 1, int(max(sy0, sy1, sy2)) + 1)
    if min_x >= max_x or min_y >= max_y:
        return
    denom = (sy1 - sy2) * (sx0 - sx2) + (sx2 - sx1) * (sy0 - sy2)
    if abs(denom) < 1e-6:
        return
    inv_denom = 1.0 / denom
    vrange = vmax - vmin
    if vrange < 1e-15:
        vrange = 1e-15
    inv_vrange = 1.0 / vrange
    for iy in range(min_y, max_y + 1):
        py = float(iy)
        for ix in range(min_x, max_x + 1):
            px = float(ix)
            lam0 = ((sy1 - sy2) * (px - sx2) + (sx2 - sx1) * (py - sy2)) * inv_denom
            lam1 = ((sy2 - sy0) * (px - sx2) + (sx0 - sx2) * (py - sy2)) * inv_denom
            lam2 = 1.0 - lam0 - lam1
            if lam0 < -0.001 or lam1 < -0.001 or lam2 < -0.001:
                continue
            val = lam0 * v0 + lam1 * v1 + lam2 * v2
            t = (val - vmin) * inv_vrange
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            idx = int(t * 255.0)
            idx = 0 if idx < 0 else (255 if idx > 255 else idx)
            img[iy, ix, 0] = lut[idx, 0]
            img[iy, ix, 1] = lut[idx, 1]
            img[iy, ix, 2] = lut[idx, 2]
            img[iy, ix, 3] = 255


def _marching_squares_ref(gx, gy, gv, levels, seg_table):
    """Kernel original: gx/gy/gv indexados [cj, ci] (transpuestos)."""
    n_grid = gx.shape[0]
    segs = []
    for level in levels:
        for ci in range(n_grid - 1):
            for cj in range(n_grid - 1):
                v00 = gv[cj, ci]
                v10 = gv[cj, ci + 1]
                v11 = gv[cj + 1, ci + 1]
                v01 = gv[cj + 1, ci]
                case = 0
                if v00 >= level: case |= 1
                if v10 >= level: case |= 2
                if v11 >= level: case |= 4
                if v01 >= level: case |= 8
                if case == 0 or case == 15:
                    continue
                ept = {}

                def edge(k, va, vb, xa, ya, xb, yb):
                    if (va >= level) != (vb >= level):
                        dv = vb - va
                        t = (level - va) / dv if abs(dv) > 1e-15 else 0.5
                        if t < 0.0: t = 0.0
                        elif t > 1.0: t = 1.0
                        ept[k] = (xa + t * (xb - xa), ya + t * (yb - ya))

                edge(0, v00, v10, gx[cj, ci], gy[cj, ci], gx[cj, ci + 1], gy[cj, ci + 1])
                edge(1, v10, v11, gx[cj, ci + 1], gy[cj, ci + 1], gx[cj + 1, ci + 1], gy[cj + 1, ci + 1])
                edge(2, v11, v01, gx[cj + 1, ci + 1], gy[cj + 1, ci + 1], gx[cj + 1, ci], gy[cj + 1, ci])
                edge(3, v01, v00, gx[cj + 1, ci], gy[cj + 1, ci], gx[cj, ci], gy[cj, ci])
                for s in range(2):
                    ea = seg_table[case, 2 * s]
                    eb = seg_table[case, 2 * s + 1]
                    if ea < 0 or eb < 0 or ea not in ept or eb not in ept:
                        continue
                    segs.append((*ept[ea], *ept[eb]))
    return np.array(segs).reshape(-1, 4)


def _gxgy_ref(nc, n_grid):
    gx = np.empty((n_grid, n_grid))
    gy = np.empty((n_grid, n_grid))
    for ci in range(n_grid):
        xi = -1.0 + 2.0 * ci / (n_grid - 1)
        for cj in range(n_grid):
            eta = -1.0 + 2.0 * cj / (n_grid - 1)
            N0 = (1.0 - xi) * (1.0 - eta) * 0.25
            N1 = (1.0 + xi) * (1.0 - eta) * 0.25
            N2 = (1.0 + xi) * (1.0 + eta) * 0.25
            N3 = (1.0 - xi) * (1.0 + eta) * 0.25
            gx[cj, ci] = N0 * nc[0, 0] + N1 * nc[1, 0] + N2 * nc[2, 0] + N3 * nc[3, 0]
            gy[cj, ci] = N0 * nc[0, 1] + N1 * nc[1, 1] + N2 * nc[2, 1] + N3 * nc[3, 1]
    return gx, gy


# ─── Casos ──────────────────────────────────────────────────────────────────

def _random_quads(rng, n_elem, span):
    """Cuadrilateros convexos (cuadrados perturbados) en una grilla."""
    side = int(np.ceil(np.sqrt(n_elem)))
    quads = []
    for k in range(n_elem):
        i, j = k % side, k // side
        x0, y0 = 10 + i * span, 10 + j * span
        base = np.array([[x0, y0], [x0 + span, y0], [x0 + span, y0 + span],
                         [x0, y0 + span]], dtype=float)
        quads.append(base + rng.uniform(-0.2 * span, 0.2 * span, size=(4, 2)))
    return np.array(quads)


def test_grid_mapping():
    print("\n[1/3] mapeo bilineal de la grilla vs kernel escalar")
    rng = np.random.default_rng(1)
    corners = _random_quads(rng, 5, 30.0)
    for n_grid in (7, 16):
        pts = element_grid_points(corners, n_grid - 1)     # (e, p, 2), layout [i, j]
        ok = True
        for e in range(corners.shape[0]):
            gx_ref, gy_ref = _gxgy_ref(corners[e], n_grid)  # layout [cj, ci]
            gx = pts[e, :, 0].reshape(n_grid, n_grid).T
            gy = pts[e, :, 1].reshape(n_grid, n_grid).T
            ok &= np.array_equal(gx, gx_ref) and np.array_equal(gy, gy_ref)
        check(f"grilla {n_grid}x{n_grid}: coordenadas identicas bit a bit", ok)
    vals = rng.uniform(-3, 5, size=(5, 4))
    grid = element_grid_values(vals, 6)
    ref = np.empty_like(grid)
    for e in range(5):
        for i in range(7):
            xi = -1 + 2 * i / 6
            for j in range(7):
                eta = -1 + 2 * j / 6
                N = [(1 - xi) * (1 - eta) * 0.25, (1 + xi) * (1 - eta) * 0.25,
                     (1 + xi) * (1 + eta) * 0.25, (1 - xi) * (1 + eta) * 0.25]
                ref[e, i * 7 + j] = (N[0] * vals[e, 0] + N[1] * vals[e, 1]
                                     + N[2] * vals[e, 2] + N[3] * vals[e, 3])
    check("valores bilineales identicos bit a bit", np.array_equal(grid, ref))


def test_rasterizer():
    print("\n[2/3] rasterizado Gouraud + LUT vs kernel escalar")
    rng = np.random.default_rng(2)
    W, H = 260, 180
    lut = np.ascontiguousarray(np.asarray(JET_LUT, dtype=np.uint8))
    for n_elem, span, chunk in ((6, 40.0, 500_000), (12, 25.0, 700)):
        corners = _random_quads(rng, n_elem, span)
        # Un elemento parcialmente fuera de la imagen (recorte del bbox).
        corners[0] -= 25.0
        n = 6
        vals = element_grid_values(rng.uniform(-1, 2, size=(n_elem, 4)), n)
        pts = element_grid_points(corners, n)
        P = np.concatenate([pts, vals[..., None]], axis=-1)   # (e, p, 3)
        tris = P[:, grid_triangles(n)].reshape(-1, 3, 3)
        vmin, vmax = -0.5, 1.5

        img = np.zeros((H, W, 4), dtype=np.uint8)
        rasterize_triangles(img, tris, vmin, vmax, lut, chunk=chunk)
        ref = np.zeros((H, W, 4), dtype=np.uint8)
        for tr in tris:
            _rasterize_triangle_ref(ref, W, H, *tr[0], *tr[1], *tr[2], vmin, vmax, lut)
        diff = int((img != ref).any(axis=-1).sum())
        painted = int((ref[..., 3] > 0).sum())
        check(f"{len(tris)} triangulos, chunk={chunk}: {diff} pixeles distintos "
              f"de {painted} pintados", diff == 0 and painted > 0)

    # Rango degenerado (vmax == vmin) y triangulo degenerado no deben fallar.
    img = np.zeros((H, W, 4), dtype=np.uint8)
    tris = np.array([[[10, 10, 1.0], [50, 10, 1.0], [50, 50, 1.0]],
                     [[60, 60, 0.0], [70, 70, 0.0], [80, 80, 0.0]]])
    rasterize_triangles(img, tris, 1.0, 1.0, lut)
    check("rango y triangulo degenerados: sin excepcion", True)


def test_marching_squares():
    print("\n[3/3] marching squares vs kernel escalar")
    rng = np.random.default_rng(3)
    corners = _random_quads(rng, 8, 30.0)
    for n_grid in (7, 16):
        n = n_grid - 1
        pts = element_grid_points(corners, n)
        gv = rng.uniform(0.0, 1.0, size=(8, n_grid * n_grid))
        # Valores repetidos para forzar aristas planas (t = 0.5) y casos ambiguos.
        gv[:, ::5] = 0.5
        levels = np.linspace(0.05, 0.95, 10)
        X = pts[:, :, 0].reshape(8, n_grid, n_grid)
        Y = pts[:, :, 1].reshape(8, n_grid, n_grid)
        V = gv.reshape(8, n_grid, n_grid)
        segs = marching_squares_batch(X, Y, V, levels)
        ref = [_marching_squares_ref(X[e].T, Y[e].T, V[e].T, levels, MARCHING_SEG_TABLE)
               for e in range(8)]
        ref = np.concatenate(ref, axis=0)
        same_count = segs.shape[0] == ref.shape[0]
        a = segs[np.lexsort(segs.T[::-1])] if segs.size else segs
        b = ref[np.lexsort(ref.T[::-1])] if ref.size else ref
        same = same_count and np.array_equal(a, b)
        check(f"grilla {n_grid}x{n_grid}: {ref.shape[0]} segmentos, mismo conjunto "
              f"bit a bit", same and ref.shape[0] > 0)


# --- Paridad del contorno de la Memoria de Calculo -------------------------
# `file_io/figure_export._fill_field` pintaba el gradiente con un loop Python
# por triangulo (72 llamadas por elemento: 16,7 s en una malla de 1024). Ahora
# arma todos los triangulos y llama al mismo `rasterize_triangles` del canvas.
# El oraculo es aquel loop escalar, copiado literal.

def _fill_field_ref(img_arr, w, h, project, view, node_values, vmin, vmax, lut,
                    *, deformed_coords=None, subdiv=6):
    """Version original de figure_export._fill_field, con doble loop Python."""
    v_range = max(vmax - vmin, 1e-15)
    n = subdiv

    npts = (n + 1) * (n + 1)
    Nmat = np.empty((npts, 4))
    k = 0
    for i in range(n + 1):
        xi = -1 + 2 * i / n
        for j in range(n + 1):
            eta = -1 + 2 * j / n
            Nmat[k, 0] = (1 - xi) * (1 - eta) * 0.25
            Nmat[k, 1] = (1 + xi) * (1 - eta) * 0.25
            Nmat[k, 2] = (1 + xi) * (1 + eta) * 0.25
            Nmat[k, 3] = (1 - xi) * (1 + eta) * 0.25
            k += 1

    stride = n + 1
    for elem in project.elements.values():
        nids = elem.node_ids[:4]
        if not all(nid in project.nodes for nid in nids):
            continue
        if not all(nid in node_values for nid in nids):
            continue
        nv = np.array([float(node_values[nid]) for nid in nids])
        if deformed_coords is not None:
            nc = np.array([deformed_coords[nid] for nid in nids], dtype=float)
        else:
            nc = np.array(
                [(project.nodes[nid].x, project.nodes[nid].y) for nid in nids],
                dtype=float,
            )
        world = Nmat @ nc
        vals = Nmat @ nv
        sx = world[:, 0] * view.scale + view.offset_x
        sy = -world[:, 1] * view.scale + view.offset_y

        for i in range(n):
            for j in range(n):
                k00 = i * stride + j
                k10 = (i + 1) * stride + j
                k11 = (i + 1) * stride + (j + 1)
                k01 = i * stride + (j + 1)
                for a, b, c in ((k00, k10, k11), (k00, k11, k01)):
                    _rasterize_triangle_ref(
                        img_arr, w, h, sx[a], sy[a], vals[a],
                        sx[b], sy[b], vals[b], sx[c], sy[c], vals[c],
                        vmin, vmin + v_range, lut)


def _lienzo_figura(w, h, bg):
    arr = np.empty((h, w, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3] = bg[0], bg[1], bg[2], 255
    return arr


def _campo_nodal(project, deformada):
    """Reproduce el setup de figure_export.render_contour."""
    from fem.solver import solve_system
    from fem.stress import compute_all_stresses
    from file_io import figure_export as fx

    sol = solve_system(project)
    _, nodal = compute_all_stresses(project, sol)
    nid_list = sorted(project.nodes.keys())
    values = {nid: float(nodal.get(nid, {}).get("von_mises", 0.0))
              for nid in nid_list}
    presentes = [v for nid, v in values.items() if nid in nodal]
    vmin, vmax = float(min(presentes)), float(max(presentes))
    if abs(vmax - vmin) < 1e-12:
        vmax = vmin + 1.0

    dc = None
    if deformada:
        sc = fx._deformed_scale(project, sol, nid_list)
        u, idx = sol["u"], project.node_index_map
        dc = {nid: (project.nodes[nid].x + sc * u[2 * idx[nid]],
                    project.nodes[nid].y + sc * u[2 * idx[nid] + 1])
              for nid in nid_list}
        xs = [c[0] for c in dc.values()]
        ys = [c[1] for c in dc.values()]
    else:
        xs = [project.nodes[n].x for n in nid_list]
        ys = [project.nodes[n].y for n in nid_list]
    return values, vmin, vmax, dc, xs, ys


def test_figure_export_field():
    """Contorno de la Memoria: mismos pixeles que el rasterizado escalar."""
    from file_io import figure_export as fx
    from tests.bench_timing import build_project
    from tests.example_data import load_example_project, load_example_project_q9

    casos = [
        ("Ejemplo Q4, malla original", load_example_project(), False, 920, 680, 6),
        ("Ejemplo Q4, malla deformada", load_example_project(), True, 920, 680, 6),
        ("Ejemplo Q9, malla deformada", load_example_project_q9(), True, 920, 680, 6),
        ("Cook Q4 8x8, deformada", build_project(8, "Q4"), True, 920, 680, 6),
        ("Cook Q9 16x16, original", build_project(16, "Q9"), False, 920, 680, 6),
        ("Cook Q4 8x8, subdiv=3", build_project(8, "Q4"), True, 920, 680, 3),
        ("Cook Q4 8x8, lienzo 320x240", build_project(8, "Q4"), True, 320, 240, 6),
    ]
    lut = fx._colormap_lut("jet")
    for nombre, project, deformada, w, h, subdiv in casos:
        values, vmin, vmax, dc, xs, ys = _campo_nodal(project, deformada)
        view = fx._View(xs, ys, w, h, pad_left=30, pad_right=150,
                        pad_top=46, pad_bottom=30)
        ref = _lienzo_figura(w, h, fx._FIG_BG)
        _fill_field_ref(ref, w, h, project, view, values, vmin, vmax, lut,
                        deformed_coords=dc, subdiv=subdiv)
        new = _lienzo_figura(w, h, fx._FIG_BG)
        fx._fill_field(new, w, h, project, view, values, vmin, vmax, lut,
                       deformed_coords=dc, subdiv=subdiv)
        distintos = int(np.count_nonzero(np.any(ref != new, axis=2)))
        pintados = int(np.count_nonzero(
            np.any(ref != _lienzo_figura(w, h, fx._FIG_BG), axis=2)))
        check(f"contorno memoria - {nombre}: {distintos} pixeles distintos de "
              f"{pintados} pintados", distintos == 0 and pintados > 0)


def main():
    print("=" * 66)
    print("  test_canvas_raster: paridad rasterizado / isolineas vectorizados")
    print("=" * 66)
    test_grid_mapping()
    test_rasterizer()
    test_marching_squares()
    test_figure_export_field()
    failed = [n for n, ok in _checks if not ok]
    print("\n" + "=" * 66)
    print(f"  Resumen: {len(_checks) - len(failed)}/{len(_checks)} checks OK")
    print("=" * 66)
    if failed:
        for n in failed:
            print(f"  [FAIL] {n}")
        sys.exit(1)
    print("Test completado exitosamente.")


if __name__ == "__main__":
    main()
