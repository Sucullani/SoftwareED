"""
Cálculo de esfuerzos en puntos de Gauss, extrapolación a nodos y promedio nodal.
σ = D · B · uₑ

Dos versiones:
- `compute_element_stresses(...)`: legible, elemento a elemento y punto a
  punto (recalcula J y B con `fem/jacobian.py` y `fem/b_matrix.py`). Es la
  referencia pedagogica y el oraculo de `tests/test_solver_regression.py`;
  NO la usa el post-proceso productivo.
- `compute_all_stresses(project, solution)`: vectorizada por lotes
  (`fem/batch.py`) sobre las B y det J que dejo el ensamblaje
  (`ElementData.batch`), con extrapolacion matricial a nodos y promedio
  nodal por acumuladores NumPy. Devuelve los mismos dicts de siempre: la
  API es estable para probe, vista 3D, memoria de calculo y tests.

Las invariantes (sigma_1, sigma_2, von Mises) nunca se extrapolan ni se
promedian: se recomputan desde las componentes cartesianas ya extrapoladas
o ya promediadas. Son funciones no lineales de sigma_x/sigma_y/tau_xy, y
hacerlo al reves daba un VM nodal hasta 3,7 % distinto e incoherente con el
que reportan el probe (`fem.probe_query.compute_smooth`) y el modo crudo.
"""

import numpy as np

from fem.shape_functions import get_shape_functions, shape_functions_q9
from fem.gauss_quadrature import get_gauss_points_for_element, get_gauss_points_2d
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix
from fem.batch import principal_and_vm_batch, stress_at_points


# Orden canonico de las componentes en todos los arrays y dicts de salida.
_STRESS_KEYS = ["sigma_x", "sigma_y", "tau_xy", "sigma_1", "sigma_2", "von_mises"]


def compute_element_stresses(node_coords, u_elem, E, nu, thickness,
                              analysis_type, element_type):
    """
    Calcula esfuerzos en los puntos de Gauss de un elemento (version legible).

    σ = D · B · uₑ

    Retorna:
        gauss_stresses: list of dict con {xi, eta, sigma_x, sigma_y, tau_xy,
                                          sigma_1, sigma_2, von_mises}
    """
    D = constitutive_matrix(E, nu, analysis_type)
    _, dN_func = get_shape_functions(element_type)
    gauss_pts, _ = get_gauss_points_for_element(element_type)

    gauss_stresses = []

    for gp in gauss_pts:
        xi, eta = gp[0], gp[1]

        dN_nat = dN_func(xi, eta)
        J, det_J, inv_J = compute_jacobian(dN_nat, node_coords)
        dN_phys = compute_dN_physical(dN_nat, inv_J)
        B = compute_b_matrix(dN_phys)

        # Calcular esfuerzos
        strain = B @ u_elem
        stress = D @ strain

        sigma_x = stress[0]
        sigma_y = stress[1]
        tau_xy = stress[2]

        # Esfuerzos principales
        sigma_avg = (sigma_x + sigma_y) / 2.0
        R = np.sqrt(((sigma_x - sigma_y) / 2.0)**2 + tau_xy**2)
        sigma_1 = sigma_avg + R
        sigma_2 = sigma_avg - R

        # Von Mises
        von_mises = np.sqrt(sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2)

        gauss_stresses.append({
            "xi": xi,
            "eta": eta,
            "sigma_x": sigma_x,
            "sigma_y": sigma_y,
            "tau_xy": tau_xy,
            "sigma_1": sigma_1,
            "sigma_2": sigma_2,
            "von_mises": von_mises,
            "strain": strain.copy(),
            "stress": stress.copy(),
        })

    return gauss_stresses


# ─── Matrices de extrapolación (constantes de módulo) ──────────────────────
# Proyectan los valores en los puntos de Gauss a los nodos del elemento.
# Se construyen una sola vez.

def _build_q4_extrap():
    s = np.sqrt(3.0)
    return 0.25 * np.array([
        [(1 + s) * (1 + s), (1 - s) * (1 + s), (1 - s) * (1 - s), (1 + s) * (1 - s)],
        [(1 + s) * (1 - s), (1 - s) * (1 - s), (1 - s) * (1 + s), (1 + s) * (1 + s)],
        [(1 - s) * (1 - s), (1 + s) * (1 - s), (1 + s) * (1 + s), (1 - s) * (1 + s)],
        [(1 - s) * (1 + s), (1 + s) * (1 + s), (1 + s) * (1 - s), (1 - s) * (1 - s)],
    ])


_Q4_EXTRAP: np.ndarray = _build_q4_extrap()   # (4, 4) — computado una sola vez
_Q9_EXTRAP_MATRIX: np.ndarray | None = None   # lazy: se construye al primer uso


def _q9_extrapolation_matrix() -> np.ndarray:
    """
    Matriz 9x9 que proyecta 9 valores en puntos de Gauss 3x3 a 9 valores en
    nodos Q9. Se construye evaluando las 9 funciones de forma bicuadráticas
    en los 9 puntos de Gauss y se invierte: σ_nodes = M⁻¹ · σ_gauss.
    """
    global _Q9_EXTRAP_MATRIX
    if _Q9_EXTRAP_MATRIX is not None:
        return _Q9_EXTRAP_MATRIX
    gauss_pts, _ = get_gauss_points_2d(3)
    M = np.zeros((9, 9))
    for j, (xi, eta) in enumerate(gauss_pts):
        M[j, :] = shape_functions_q9(xi, eta)
    _Q9_EXTRAP_MATRIX = np.linalg.inv(M)
    return _Q9_EXTRAP_MATRIX


def extrapolation_matrix(n_nodes: int) -> np.ndarray:
    """Matriz (n_nodes, n_gp) de extrapolacion Gauss -> nodos segun el tipo."""
    if n_nodes == 4:
        return _Q4_EXTRAP
    if n_nodes == 9:
        return _q9_extrapolation_matrix()
    raise ValueError(f"Elemento de {n_nodes} nodos: solo se soportan Q4 y Q9.")


def _extrapolate_list(gauss_stresses: list, M: np.ndarray) -> list:
    # (n_gp, 3): fila = punto de Gauss, columna = componente cartesiana.
    gauss_mat = np.array([[gs[k] for k in _STRESS_KEYS[:3]]
                          for gs in gauss_stresses])
    nodal_mat = principal_and_vm_batch(M @ gauss_mat)
    return [dict(zip(_STRESS_KEYS, nodal_mat[i])) for i in range(M.shape[0])]


def extrapolate_to_nodes_q4(gauss_stresses: list) -> list:
    """Extrapola esfuerzos de 4 puntos de Gauss (2×2) a los 4 nodos del Q4.

    Un unico matmul (4,4)@(4,3) sobre las componentes cartesianas;
    σ1, σ2 y von Mises se recomputan desde las componentes ya
    extrapoladas: son no lineales y extrapolarlas por separado no es
    consistente con el probe ni con el modo crudo.
    """
    return _extrapolate_list(gauss_stresses, _Q4_EXTRAP)


def extrapolate_to_nodes_q9(gauss_stresses: list) -> list:
    """Extrapola esfuerzos de 9 puntos de Gauss (3×3) a los 9 nodos del Q9."""
    return _extrapolate_list(gauss_stresses, _q9_extrapolation_matrix())


def compute_all_stresses(project, solution):
    """
    Calcula esfuerzos para todos los elementos y promedia en nodos compartidos.

    Vectorizado por lotes: reutiliza las B y det J del ensamblaje
    (`solution["element_data"].batch`), evalua σ = D B uₑ en todos los
    puntos de Gauss de todos los elementos con un solo `einsum`, extrapola
    las componentes a nodos con un matmul por lote y las promedia con
    `np.add.at` + `bincount`. sigma_1 / sigma_2 / VM salen de las componentes
    ya extrapoladas (por elemento) y ya promediadas (nodal medio). Los dicts
    de salida se arman una sola vez al final.

    Retorna:
        element_stresses: dict {elem_id: {gauss_stresses, nodal_stresses}}
        nodal_avg_stresses: dict {node_id: {sigma_x, sigma_y, tau_xy, ...}}
    """
    u = np.asarray(solution["u"], dtype=float)
    element_data = solution["element_data"]
    batch = getattr(element_data, "batch", None)
    if batch is None or batch.B is None:
        raise TypeError(
            "solution['element_data'] debe ser el ElementData que retorna "
            "assemble_global_system (con el lote de arrays en .batch)."
        )

    idx_map = project.node_index_map
    n_nodes_total = len(idx_map)
    if batch.n_elements == 0:
        return {}, {}

    # σ en los puntos de Gauss: (e, p, 6).
    gauss = stress_at_points(batch.B, u[batch.dofs], batch.D)

    # Extrapolacion a nodos de las 3 componentes cartesianas: (e, n, 3).
    # Las invariantes se recomputan desde ellas, no se extrapolan.
    M = extrapolation_matrix(batch.n_nodes)
    nodal_comp = np.matmul(M, gauss[..., :3])
    nodal = principal_and_vm_batch(nodal_comp)                     # (e, n, 6)

    # Promedio nodal: acumular las componentes por ordinal de nodo, dividir
    # por el conteo y recien ahi calcular sigma_1 / sigma_2 / VM del promedio.
    conn_flat = batch.conn.ravel()
    accum = np.zeros((n_nodes_total, 3))
    np.add.at(accum, conn_flat, nodal_comp.reshape(-1, 3))
    count = np.bincount(conn_flat, minlength=n_nodes_total)
    nodal_avg = principal_and_vm_batch(accum / np.maximum(count, 1)[:, None])

    # Reconstruir los dicts (API compatible con probe, 3D, memoria, tests).
    gauss_pts, _ = get_gauss_points_for_element(project.element_type)
    xi_eta = gauss_pts.tolist()
    gauss_l = gauss.tolist()
    nodal_l = nodal.tolist()
    keys = _STRESS_KEYS
    element_stresses = {}
    for i, eid in enumerate(batch.elem_ids):
        element_stresses[int(eid)] = {
            "gauss_stresses": [
                {"xi": xe[0], "eta": xe[1], **dict(zip(keys, row))}
                for xe, row in zip(xi_eta, gauss_l[i])
            ],
            "nodal_stresses": [dict(zip(keys, row)) for row in nodal_l[i]],
        }

    avg_l = nodal_avg.tolist()
    nodal_avg_stresses = {
        nid: dict(zip(keys, avg_l[ordinal]))
        for nid, ordinal in sorted(idx_map.items(), key=lambda kv: kv[1])
        if count[ordinal] > 0
    }
    return element_stresses, nodal_avg_stresses
