"""
Ensamblaje de la matriz de rigidez global K y vector de fuerzas F.

Desde 2026-05 soporta body forces f(x,y) arbitrarias via `body_force_fn`,
necesarias para el Método de Soluciones Manufacturadas (MMS) y para
conectar la gravedad existente (que estaba como variable del project pero
no se ensamblaba). Backward-compat: `body_force_fn=None` y sin gravedad
activa reproduce el comportamiento previo bit-a-bit.
"""

import warnings

import numpy as np
from scipy.sparse import coo_matrix

from config.settings import ELEMENT_Q9
from fem.stiffness import element_stiffness_fast
from fem.shape_functions import get_shape_functions
from fem.gauss_quadrature import get_dN_at_gauss_points
from fem.equivalent_forces import (
    surface_load_to_nodal_forces,
    surface_load_to_nodal_forces_q9,
)
from fem._numba_compat import njit
from models.mesh_utils import find_edge_midnode


@njit(cache=True)
def _assemble_body_force_njit(N_at_gps, det_J_at_gps, gauss_wts,
                                bx_vals, by_vals, thickness):
    """Acumula fe_body = sum_gp [ N_i(gp) * b(gp) * |det J| * t * w ].

    Recibe las coords de los Gauss points YA EVALUADAS por el caller
    (bx_vals, by_vals) porque la funcion body force es una callable
    Python — Numba no la puede inlinear, pero si puede operar sobre
    arrays precomputados.

    Retorna fe_body: (2*n_nodes,) — fuerzas equivalentes nodales.
    """
    n_gp = N_at_gps.shape[0]
    n_nodes = N_at_gps.shape[1]
    fe_body = np.zeros(2 * n_nodes)

    for gp in range(n_gp):
        factor = abs(det_J_at_gps[gp]) * thickness * gauss_wts[gp]
        bx_w = bx_vals[gp] * factor
        by_w = by_vals[gp] * factor
        for i in range(n_nodes):
            N_i = N_at_gps[gp, i]
            fe_body[2 * i]     += N_i * bx_w
            fe_body[2 * i + 1] += N_i * by_w

    return fe_body


def _resolve_body_force_fn(project, body_force_fn):
    """Decide la fuente de body force a usar en el ensamblaje.

    Prioridad: si el caller pasa `body_force_fn` explicito, gana. Si no, y
    el project tiene gravedad activa con materiales de densidad > 0, se
    compone un callback que retorna (rho*gx, rho*gy) por elemento. Si
    ninguna fuente aplica, retorna None (skip total del loop, comportamiento
    legacy).

    Retorna: dict {elem_id: callable(x,y)->(bx,by)} | None.
    Es un dict por-elemento porque la densidad puede variar por material.
    """
    if body_force_fn is not None:
        # Callback global del usuario: misma funcion para todos los elementos.
        if project.include_gravity:
            warnings.warn(
                "body_force_fn pasado explicito; include_gravity sera ignorado.",
                stacklevel=3,
            )
        return {eid: body_force_fn for eid in project.elements}

    if not project.include_gravity:
        return None

    gx, gy = project.gravity_x, project.gravity_y
    if gx == 0.0 and gy == 0.0:
        return None

    out = {}
    for eid, elem in project.elements.items():
        mat = project.materials.get(elem.material_name)
        if mat is None or mat.density <= 0.0:
            continue
        rho = mat.density
        # Capturar rho por valor (default-arg) para evitar late binding.
        out[eid] = lambda x, y, _rho=rho, _gx=gx, _gy=gy: (_rho * _gx, _rho * _gy)
    return out if out else None


def assemble_global_system(project, *, body_force_fn=None):
    """
    Ensambla la matriz de rigidez global K y el vector de fuerzas F.

    Parámetros:
        project: ProjectModel con nodos, elementos, cargas, etc.
        body_force_fn: callable (x: float, y: float) -> (bx, by). Si no es
            None, se ensambla ∫ N_i · b dΩ en cada elemento. Si es None,
            se compone desde gravedad del project (si include_gravity).

    Retorna:
        K: array (n_dof, n_dof) - Matriz de rigidez global.
        F: array (n_dof,) - Vector de fuerzas global.
        element_data: dict {elem_id: {ke, gauss_data, dof_indices}}
    """
    n_dof = project.total_dof
    F = np.zeros(n_dof)
    idx_map = project.node_index_map

    element_data = {}

    # Acumuladores COO para el ensamblaje sparse de K.
    # Usar listas Python para el loop (cada elemento agrega n_e^2 entradas);
    # al final se construye la CSR con sum_duplicates automatica de coo_matrix.
    # Para mallas grandes (500+ nodos) K sparse ahorra 90-99% de memoria vs
    # la version densa y acelera spsolve 10-100x (vs scipy.linalg.solve denso).
    coo_rows = []
    coo_cols = []
    coo_data = []

    # Resolver fuente de body forces UNA VEZ antes del loop.
    bf_by_elem = _resolve_body_force_fn(project, body_force_fn)
    # Precomputar dN_at_gps + N_at_gps + gauss_pts/wts una sola vez por
    # tipo de elemento (cacheado dentro de get_dN_at_gauss_points). Era un
    # hotspot oculto en el flow anterior: se computaban en cada elemento.
    dN_at_gps, gauss_pts, gauss_wts, N_at_gps = get_dN_at_gauss_points(
        project.element_type
    )
    n_gp = len(gauss_pts)

    for elem_id, elem in project.elements.items():
        # Obtener coordenadas de los nodos del elemento
        node_coords = np.array([
            [project.nodes[nid].x, project.nodes[nid].y]
            for nid in elem.node_ids
        ])

        # Material del elemento
        material = project.materials.get(elem.material_name)
        if material is None:
            material = list(project.materials.values())[0]

        # Calcular matriz de rigidez via kernel JIT.
        # Retorna ke + B + det_J por GP, sin dict gauss_data — armamos el
        # gauss_data minimal abajo desde los arrays (mucho mas rapido).
        ke, B_at_gps, det_J_at_gps, _wts = element_stiffness_fast(
            node_coords,
            material.E,
            material.nu,
            elem.thickness,
            project.analysis_type,
            project.element_type,
        )

        # gauss_data minimal: solo los campos que stress.py necesita para
        # `_gauss_stresses_from_precomputed` (xi, eta, B). Los modulos
        # educativos que requieren J, dN_phys, etc. siguen llamando a la
        # version no-JIT `element_stiffness(...)` directamente, no pasan
        # por este assembly path.
        gauss_data = [
            {
                "xi": float(gauss_pts[i, 0]),
                "eta": float(gauss_pts[i, 1]),
                "weight": float(gauss_wts[i]),
                "det_J": float(det_J_at_gps[i]),
                "B": B_at_gps[i],
            }
            for i in range(n_gp)
        ]

        # Índices de GDL del elemento
        dof_indices = elem.get_dof_indices(project)

        # Acumular triplete COO: cada entrada ke[i,j] → K[gi, gj].
        # repeat/tile evita el overhead de broadcast_arrays que meshgrid genera
        # internamente (~0.27s/run ahorrado en mallas de 4800 elem).
        idx = np.asarray(dof_indices, dtype=np.intp)
        n_e = len(idx)
        coo_rows.append(np.repeat(idx, n_e))   # [i0,i0,...,i1,i1,...] (n_e²)
        coo_cols.append(np.tile(idx, n_e))     # [j0,j1,...,j0,j1,...] (n_e²)
        coo_data.append(ke.ravel())

        # Ensamblar body force del elemento si corresponde.
        # Estrategia: evaluar bf(x, y) en cada GP por Python (porque bf es
        # una callable que Numba no puede inlinear), despues delegar la
        # cuadratura al kernel JIT `_assemble_body_force_njit`.
        if bf_by_elem is not None and elem_id in bf_by_elem:
            bf = bf_by_elem[elem_id]
            # Coords fisicas (x,y) en cada GP: vectorizado con N_at_gps.
            x_gps = N_at_gps @ node_coords[:, 0]
            y_gps = N_at_gps @ node_coords[:, 1]
            bx_vals = np.empty(n_gp)
            by_vals = np.empty(n_gp)
            for i in range(n_gp):
                bx_vals[i], by_vals[i] = bf(x_gps[i], y_gps[i])
            fe_body = _assemble_body_force_njit(
                N_at_gps, det_J_at_gps, gauss_wts,
                bx_vals, by_vals, elem.thickness,
            )
            for i_local, i_global in enumerate(dof_indices):
                F[i_global] += fe_body[i_local]

        # Guardar datos del elemento
        element_data[elem_id] = {
            "ke": ke,
            "gauss_data": gauss_data,
            "dof_indices": dof_indices,
            "node_coords": node_coords,
        }

    # Ensamblar vector de fuerzas nodales puntuales
    for load in project.nodal_loads.values():
        base = 2 * idx_map[load.node_id]
        F[base]     += load.fx
        F[base + 1] += load.fy

    # Ensamblar contribucion de cargas superficiales (trapezoidales lineales).
    # Q4: arista de 2 nodos → integración lineal.
    # Q9: arista de 3 nodos → se localiza el nodo medio en el elemento dueño
    # y la carga se reparte en los 3 nodos con funciones de forma cuadráticas.
    for sl in project.surface_loads:
        n_a = project.nodes.get(sl.node_start)
        n_b = project.nodes.get(sl.node_end)
        if n_a is None or n_b is None:
            continue

        mid_nid = None
        if project.element_type == ELEMENT_Q9:
            elem = project.elements.get(sl.element_id) if sl.element_id is not None else None
            if elem is not None:
                mid_nid = find_edge_midnode(elem, sl.node_start, sl.node_end)
            if mid_nid is None:
                # Fallback: buscar en cualquier elemento que contenga la arista.
                for e in project.elements.values():
                    mid_nid = find_edge_midnode(e, sl.node_start, sl.node_end)
                    if mid_nid is not None:
                        break

        if mid_nid is not None:
            n_m = project.nodes.get(mid_nid)
            if n_m is not None:
                (fx_a, fy_a), (fx_m, fy_m), (fx_b, fy_b) = (
                    surface_load_to_nodal_forces_q9(
                        (n_a.x, n_a.y), (n_m.x, n_m.y), (n_b.x, n_b.y),
                        sl.q_start, sl.q_end, sl.angle,
                    )
                )
                base_a = 2 * idx_map[sl.node_start]
                base_m = 2 * idx_map[mid_nid]
                base_b = 2 * idx_map[sl.node_end]
                F[base_a]     += fx_a
                F[base_a + 1] += fy_a
                F[base_m]     += fx_m
                F[base_m + 1] += fy_m
                F[base_b]     += fx_b
                F[base_b + 1] += fy_b
                continue

        (fx_a, fy_a), (fx_b, fy_b) = surface_load_to_nodal_forces(
            (n_a.x, n_a.y), (n_b.x, n_b.y),
            sl.q_start, sl.q_end, sl.angle,
        )
        base_a = 2 * idx_map[sl.node_start]
        base_b = 2 * idx_map[sl.node_end]
        F[base_a]     += fx_a
        F[base_a + 1] += fy_a
        F[base_b]     += fx_b
        F[base_b + 1] += fy_b

    # Construir K sparse CSR desde los acumuladores COO.
    # coo_matrix suma automaticamente entradas duplicadas en el mismo (i,j)
    # — exactamente el scatter de la suma local→global del MEF.
    # Mallas de 500 nodos: K es 1000×1000 = 10^6 entradas densas vs ~10^4
    # no-nulas (99% sparsity para Q4 estructurado). El factor de memoria
    # y tiempo de factorizacion mejora 10-100× con spsolve vs solve denso.
    if coo_rows:
        rows_arr = np.concatenate(coo_rows)
        cols_arr = np.concatenate(coo_cols)
        data_arr = np.concatenate(coo_data)
    else:
        rows_arr = np.array([], dtype=np.intp)
        cols_arr = np.array([], dtype=np.intp)
        data_arr = np.array([], dtype=float)
    K = coo_matrix((data_arr, (rows_arr, cols_arr)),
                   shape=(n_dof, n_dof)).tocsr()

    return K, F, element_data
