"""
Ensamblaje de la matriz de rigidez global K y del vector de fuerzas F.

Camino productivo vectorizado por lotes (`fem/batch.py`): la geometria
(J, det J, B) y la rigidez ke de TODOS los elementos se calculan de una vez
con `einsum` / `matmul`, y K se arma como tripletes COO -> CSR (la suma de
duplicados de `coo_matrix` es exactamente el scatter local -> global del
MEF). K nunca se materializa densa: memoria O(nnz).

La formulacion legible elemento a elemento vive en `fem/stiffness.py`
(`element_stiffness`, con todos los intermedios J, B y ke por punto de
Gauss) y es el oraculo de `tests/test_solver_regression.py`.

Fuerzas de cuerpo: `body_force_fn(x, y) -> (bx, by)` arbitraria (MMS) o la
gravedad del proyecto (rho * g por material). Con `body_force_fn=None` y sin
gravedad activa, F solo contiene cargas nodales y superficiales.
"""

import warnings

import numpy as np

from config.settings import ELEMENT_Q9
from fem.batch import (
    assemble_sparse, body_force_batch, gather_elements, geometry_at_points,
    physical_coords, stiffness_batch,
)
from fem.equivalent_forces import (
    surface_load_to_nodal_forces,
    surface_load_to_nodal_forces_q9,
)
from fem.gauss_quadrature import get_dN_at_gauss_points
from models.mesh_utils import find_edge_midnode


class ElementData(dict):
    """Datos por elemento del ensamblaje: `dict {elem_id: {...}}` mas el lote.

    Cada entrada tiene `ke`, `dof_indices`, `node_coords`, `B` y `det_J` como
    VISTAS de los arrays del lote (sin copias): las consumen la memoria de
    calculo (`ke`, `dof_indices`) y los scripts de la tesis. El post-proceso
    vectorizado (`fem.stress.compute_all_stresses`,
    `fem.probe_query.compute_raw_grids`) lee directamente el atributo
    `batch` (un `fem.batch.ElementBatch`).
    """

    __slots__ = ("batch",)

    def __init__(self, batch):
        super().__init__()
        self.batch = batch
        for i, eid in enumerate(batch.elem_ids):
            self[int(eid)] = {
                "ke": batch.ke[i],
                "dof_indices": batch.dofs[i],
                "node_coords": batch.coords[i],
                "B": batch.B[i],
                "det_J": batch.det_J[i],
            }


def _body_force_at_gauss_points(project, batch, N_at_gps, body_force_fn):
    """Fuerza de cuerpo b(x, y) evaluada en los puntos de Gauss: (e, p, 2).

    Prioridad: si el caller pasa `body_force_fn`, gana (se avisa si ademas
    hay gravedad activa). Si no, y el proyecto tiene gravedad activa con
    materiales de densidad > 0, b = rho * g por elemento. Si ninguna fuente
    aplica retorna None (F sin fuerzas de cuerpo, comportamiento clasico).
    """
    if batch.n_elements == 0:
        return None

    if body_force_fn is not None:
        if project.include_gravity:
            warnings.warn(
                "body_force_fn pasado explicito; include_gravity sera ignorado.",
                stacklevel=3,
            )
        # El callable es Python arbitrario (MMS): se evalua punto a punto
        # sobre las coordenadas fisicas de los GP. Son n_elem * n_gp
        # llamadas (~37 000 para 4096 Q9), despreciable frente al solve.
        xy = physical_coords(N_at_gps, batch.coords)                  # (e, p, 2)
        b = np.empty_like(xy)
        for e in range(xy.shape[0]):
            for g in range(xy.shape[1]):
                b[e, g] = body_force_fn(float(xy[e, g, 0]), float(xy[e, g, 1]))
        return b

    if not project.include_gravity:
        return None
    gx, gy = project.gravity_x, project.gravity_y
    if gx == 0.0 and gy == 0.0:
        return None
    rho = np.maximum(batch.density, 0.0)                              # (e,)
    if not np.any(rho > 0.0):
        return None
    b = np.empty((batch.n_elements, N_at_gps.shape[0], 2))
    b[..., 0] = (rho * gx)[:, None]
    b[..., 1] = (rho * gy)[:, None]
    return b


def assemble_global_system(project, *, body_force_fn=None):
    """
    Ensambla la matriz de rigidez global K y el vector de fuerzas F.

    Parametros:
        project: ProjectModel con nodos, elementos, cargas, etc.
        body_force_fn: callable (x: float, y: float) -> (bx, by). Si no es
            None, se ensambla la integral de N_i b sobre cada elemento. Si
            es None, se compone desde la gravedad del project (si esta
            activa).

    Retorna:
        K: scipy.sparse CSR (n_dof, n_dof) - Matriz de rigidez global.
        F: array (n_dof,) - Vector de fuerzas global.
        element_data: ElementData {elem_id: {ke, dof_indices, node_coords,
            B, det_J}} con el lote de arrays en `.batch`.
    """
    n_dof = project.total_dof
    F = np.zeros(n_dof)
    idx_map = project.node_index_map

    # Lote de elementos + geometria y rigidez de todos a la vez.
    batch = gather_elements(project)
    dN_at_gps, _gauss_pts, gauss_wts, N_at_gps = get_dN_at_gauss_points(
        project.element_type
    )
    n_gp, _, n_nodes = dN_at_gps.shape
    if batch.n_elements:
        _J, det_J, B = geometry_at_points(batch.coords, dN_at_gps, batch.elem_ids)
        ke = stiffness_batch(B, det_J, gauss_wts, batch.thickness, batch.D)
    else:
        det_J = np.zeros((0, n_gp))
        B = np.zeros((0, n_gp, 3, 2 * n_nodes))
        ke = np.zeros((0, 2 * n_nodes, 2 * n_nodes))
    batch.B, batch.det_J, batch.ke = B, det_J, ke

    K = assemble_sparse(batch.dofs, ke, n_dof)

    # Fuerzas de cuerpo (gravedad o callable) integradas con N en los GP.
    b_at_gps = _body_force_at_gauss_points(project, batch, N_at_gps, body_force_fn)
    if b_at_gps is not None:
        fe = body_force_batch(N_at_gps, det_J, gauss_wts, batch.thickness, b_at_gps)
        np.add.at(F, batch.dofs, fe)

    # Cargas nodales puntuales.
    for load in project.nodal_loads.values():
        idx = idx_map.get(load.node_id)
        if idx is None:
            # Carga sobre un node_id inexistente (p. ej. .edufem editado a
            # mano: from_dict no valida). Se ignora en vez de romper el solve
            # con un KeyError crudo; el validador de salud ya la reporta.
            continue
        base = 2 * idx
        F[base]     += load.fx
        F[base + 1] += load.fy

    # Cargas superficiales (trapezoidales lineales), fuente unica:
    # fem/equivalent_forces. Q4: arista de 2 nodos, integracion lineal.
    # Q9: arista de 3 nodos; se localiza el nodo medio en el elemento dueno
    # y la carga se reparte en los 3 nodos con funciones de forma cuadraticas.
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

    return K, F, ElementData(batch)
