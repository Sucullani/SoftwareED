"""Estructura del sistema K·u = F que la malla genera — logica pura, sin Tk.

Rediseño 2026-09-09 ("la interfaz enseña el metodo"): M7 (Ensamblaje)
muestra, antes de ensamblar nada, la FORMA de K que la malla ya decidio, y
en su cabecera los numeros del sistema. Este modulo calcula, a partir del
`ProjectModel`:

- el **patron de bloques no nulos** de K a nivel de nodo (cada bloque es un
  2x2 de GDL; dos nodos comparten bloque si algun elemento los contiene a
  ambos), listo para dibujarse como imagen de `size` x `size` pixeles
  (bineada cuando hay mas nodos que pixeles);
- que nodos tienen algun GDL **restringido** (sus filas y columnas son las
  que se eliminan al reducir el sistema);
- un **resumen numerico** (GDL totales, restringidos, incognitas, bloques
  no nulos, semiancho de banda);
- los bloques que aporta **un elemento** o toca **un nodo**.

Solo aritmetica + numpy: `tests/test_canvas_lens.py` lo ejercita sin
pantalla. Consumidor: `education/mod07_assembly.py` (esqueleto de K +
cabecera). Nacio como `gui/processing/system_view_logic.py` para un panel
propio de la fase Proceso que el autor decidio fundir en M7.
"""

from __future__ import annotations

import numpy as np


def node_block_pairs(project):
    """(n, i, j): cantidad de nodos y dos arrays alineados con los indices
    ordinales de los pares (i, j) que tienen bloque no nulo en K —
    incluidos los diagonales (i, i) y los dos sentidos (i, j) y (j, i).
    Sin duplicados. Los nodos que ningun elemento contiene aportan solo su
    bloque diagonal (fila y columna vacias fuera de el, como en K)."""
    n = project.num_nodes
    if n == 0:
        return 0, np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    idx_map = project.node_index_map
    rows = [np.arange(n)]
    cols = [np.arange(n)]
    for elem in project.elements.values():
        ids = [idx_map[nid] for nid in elem.node_ids if nid in idx_map]
        if len(ids) < 2:
            continue
        a = np.asarray(ids, dtype=int)
        ii, jj = np.meshgrid(a, a, indexing="ij")
        rows.append(ii.ravel())
        cols.append(jj.ravel())
    r = np.concatenate(rows)
    c = np.concatenate(cols)
    flat = np.unique(r * n + c)
    return n, flat // n, flat % n


def restrained_node_indices(project):
    """Indices ordinales de los nodos con al menos un GDL restringido."""
    idx_map = project.node_index_map
    out = set()
    for bc in project.boundary_conditions.values():
        i = idx_map.get(bc.node_id)
        if i is None:
            continue
        if bc.restrain_x or bc.restrain_y:
            out.add(i)
    return out


def system_summary(project):
    """Numeros del sistema que la malla genera, en terminos del MEF."""
    n = project.num_nodes
    n_dof = project.total_dof
    n_res = len(project.get_restrained_dofs())
    _n, i, j = node_block_pairs(project)
    n_blocks = int(len(i))
    bandwidth_nodes = int(np.max(np.abs(i - j))) if n_blocks else 0
    return {
        "n_nodes": n,
        "n_dof": n_dof,
        "n_restrained": n_res,
        "n_free": n_dof - n_res,
        "n_blocks": n_blocks,
        "n_blocks_total": n * n,
        # Semiancho de banda en GDL: el bloque mas lejano de la diagonal esta
        # a `bandwidth_nodes` nodos; en GDL son 2 por nodo, mas el propio 2x2.
        "half_bandwidth_dof": (2 * bandwidth_nodes + 1) if n else 0,
        "n_elements": project.num_elements,
    }


def element_block_pairs(project, eid):
    """Pares (i, j) de indices ordinales que el elemento `eid` aporta a K."""
    elem = project.elements.get(eid)
    if elem is None:
        return []
    idx_map = project.node_index_map
    ids = sorted({idx_map[nid] for nid in elem.node_ids if nid in idx_map})
    return [(a, b) for a in ids for b in ids]


def node_ordinal(project, nid):
    """Indice ordinal del nodo (fila/columna de bloque) o None."""
    return project.node_index_map.get(nid)


def render_pattern(n, rows, cols, size, *, restrained=(),
                   bg=(21, 22, 28), block=(154, 84, 18), diag=(253, 126, 20),
                   dim=0.42, grid=None):
    """Imagen RGB (size, size, 3) uint8 del patron de bloques.

    Cada nodo ocupa `size / n` pixeles por lado (bineado cuando n > size:
    varios nodos caen en el mismo pixel y basta con que uno tenga bloque).
    Las filas y columnas de los nodos en `restrained` se multiplican por
    `dim`. `grid` (color o None) dibuja separadores entre bloques cuando
    hay lugar (>= 6 px por bloque)."""
    img = np.empty((size, size, 3), dtype=np.uint8)
    img[:, :] = np.asarray(bg, dtype=np.uint8)
    if n <= 0 or len(rows) == 0:
        return img
    scale = size / n
    r0 = np.floor(np.asarray(rows) * scale).astype(int)
    c0 = np.floor(np.asarray(cols) * scale).astype(int)
    r1 = np.maximum(np.floor((np.asarray(rows) + 1) * scale).astype(int), r0 + 1)
    c1 = np.maximum(np.floor((np.asarray(cols) + 1) * scale).astype(int), c0 + 1)
    r1 = np.minimum(r1, size)
    c1 = np.minimum(c1, size)
    is_diag = np.asarray(rows) == np.asarray(cols)
    block_arr = np.asarray(block, dtype=np.uint8)
    diag_arr = np.asarray(diag, dtype=np.uint8)
    # Bloques grandes (n chico): rellenar rectangulo por rectangulo. Bloques
    # de 1-2 px (n grande): la asignacion por indice es suficiente y rapida.
    if scale >= 3.0:
        # Fuera de la diagonal primero, la diagonal encima.
        for k in np.flatnonzero(~is_diag):
            img[r0[k]:r1[k], c0[k]:c1[k]] = block_arr
        for k in np.flatnonzero(is_diag):
            img[r0[k]:r1[k], c0[k]:c1[k]] = diag_arr
    else:
        img[r0[~is_diag], c0[~is_diag]] = block_arr
        img[r0[is_diag], c0[is_diag]] = diag_arr
    if restrained:
        res = np.asarray(sorted(restrained), dtype=int)
        res = res[(res >= 0) & (res < n)]
        if len(res):
            p0 = np.floor(res * scale).astype(int)
            p1 = np.maximum(np.floor((res + 1) * scale).astype(int), p0 + 1)
            p1 = np.minimum(p1, size)
            mask = np.zeros(size, dtype=bool)
            for a, b in zip(p0, p1):
                mask[a:b] = True
            factor = np.ones((size, size, 1), dtype=float)
            factor[mask, :, :] = dim
            factor[:, mask, :] = dim
            img = (img.astype(float) * factor).astype(np.uint8)
    if grid is not None and scale >= 6.0:
        g = np.asarray(grid, dtype=np.uint8)
        for k in range(1, n):
            p = int(round(k * scale))
            if 0 < p < size:
                img[p, :] = g
                img[:, p] = g
    return img


def block_rect(i, j, n, size):
    """Rectangulo (x0, y0, x1, y1) en pixeles del bloque (fila i, columna j).
    Nunca mas angosto que 2 px, para que el realce se vea con n grande."""
    if n <= 0:
        return (0, 0, 0, 0)
    scale = size / n
    x0 = j * scale
    y0 = i * scale
    w = max(scale, 2.0)
    return (x0, y0, min(x0 + w, size), min(y0 + w, size))


def fingerprint(project):
    """Firma barata del estado que cambia el patron: nodos, conectividad y
    restricciones. Si no cambia, la vista no se regenera."""
    elems = tuple(sorted((eid, tuple(e.node_ids))
                         for eid, e in project.elements.items()))
    bcs = tuple(sorted((bc.node_id, bool(bc.restrain_x), bool(bc.restrain_y))
                       for bc in project.boundary_conditions.values()))
    return (tuple(sorted(project.nodes.keys())), elems, bcs)
