"""
Cálculo de esfuerzos en puntos de Gauss y extrapolación a nodos.
σ = D · B · uₑ
"""

import numpy as np

from fem.shape_functions import get_shape_functions, shape_functions_q9
from fem.gauss_quadrature import get_gauss_points_for_element, get_gauss_points_2d
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix


def compute_element_stresses(node_coords, u_elem, E, nu, thickness,
                              analysis_type, element_type):
    """
    Calcula esfuerzos en los puntos de Gauss de un elemento.

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


# ─── Matrices de extrapolación precalculadas (constantes de módulo) ─────────
# Evita reconstruirlas en cada llamada (24000 veces por run Q4).

_STRESS_KEYS = ["sigma_x", "sigma_y", "tau_xy", "sigma_1", "sigma_2", "von_mises"]
_N_STRESS = len(_STRESS_KEYS)

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


def extrapolate_to_nodes_q4(gauss_stresses: list) -> list:
    """
    Extrapola esfuerzos de 4 puntos de Gauss (2×2) a 4 nodos del elemento Q4.

    Vectorizado: construye una matriz (4, 6) con todos los componentes de
    esfuerzo y hace un único matmul (4,4)@(4,6) en lugar de 6 productos
    vector separados — ~6× más rápido por llamada.
    """
    # (4, 6): fila = Gauss point, columna = componente de esfuerzo
    gauss_mat = np.array([[gs[k] for k in _STRESS_KEYS] for gs in gauss_stresses])
    nodal_mat = _Q4_EXTRAP @ gauss_mat  # (4, 6)
    return [dict(zip(_STRESS_KEYS, nodal_mat[i])) for i in range(4)]


def extrapolate_to_nodes_q9(gauss_stresses: list) -> list:
    """
    Extrapola esfuerzos de 9 puntos de Gauss (3×3) a los 9 nodos del Q9.

    Vectorizado con matmul (9,9)@(9,6) en lugar de 6 productos separados.
    """
    M_inv = _q9_extrapolation_matrix()
    gauss_mat = np.array([[gs[k] for k in _STRESS_KEYS] for gs in gauss_stresses])
    nodal_mat = M_inv @ gauss_mat  # (9, 6)
    return [dict(zip(_STRESS_KEYS, nodal_mat[i])) for i in range(9)]


def _gauss_stresses_from_precomputed(gauss_data_list, u_elem, D):
    """Calcula esfuerzos en puntos de Gauss reutilizando las matrices B ya
    almacenadas en gauss_data por element_stiffness.

    Elimina la re-computación de J, dN, B (~96 000 llamadas redundantes en
    mallas de 4800 elem Q4, equivalentes a ~0.85 s por solve).
    """
    gauss_stresses = []
    for gd in gauss_data_list:
        B = gd["B"]
        strain = B @ u_elem
        stress_vec = D @ strain

        sigma_x, sigma_y, tau_xy = stress_vec[0], stress_vec[1], stress_vec[2]
        sigma_avg = (sigma_x + sigma_y) * 0.5
        R = np.sqrt(((sigma_x - sigma_y) * 0.5) ** 2 + tau_xy ** 2)
        sigma_1 = sigma_avg + R
        sigma_2 = sigma_avg - R
        von_mises = np.sqrt(sigma_1 ** 2 - sigma_1 * sigma_2 + sigma_2 ** 2)

        # strain y stress_vec son arrays recién creados (B@u, D@strain) —
        # no se comparten con nada, no necesitan .copy().
        gauss_stresses.append({
            "xi": gd["xi"],
            "eta": gd["eta"],
            "sigma_x": sigma_x,
            "sigma_y": sigma_y,
            "tau_xy": tau_xy,
            "sigma_1": sigma_1,
            "sigma_2": sigma_2,
            "von_mises": von_mises,
            "strain": strain,
            "stress": stress_vec,
        })
    return gauss_stresses


def compute_all_stresses(project, solution):
    """
    Calcula esfuerzos para todos los elementos y promedia en nodos compartidos.

    Retorna:
        element_stresses: dict {elem_id: {gauss_stresses, nodal_stresses}}
        nodal_avg_stresses: dict {node_id: {sigma_x, sigma_y, tau_xy, ...}}
    """
    u = solution["u"]
    element_data = solution["element_data"]
    element_stresses = {}

    # Cache D por (E, nu, analysis_type) — evita recomputar constitutive_matrix
    # por cada elemento cuando el mismo material está asignado a muchos.
    D_cache: dict = {}

    # Acumuladores para promedio nodal: listas Python puras (más rápido que
    # np.mean en listas de 1-4 elementos que se dan en nodos compartidos).
    stress_keys = ["sigma_x", "sigma_y", "tau_xy", "sigma_1", "sigma_2", "von_mises"]
    nodal_accum: dict = {}

    for elem_id, elem in project.elements.items():
        material = project.materials.get(elem.material_name)
        if material is None:
            material = next(iter(project.materials.values()))

        dof_indices = element_data[elem_id]["dof_indices"]
        u_elem = u[dof_indices]

        # Reusar B pre-computado en gauss_data por element_stiffness.
        # Si por algún motivo gauss_data no tiene 'B' (código legacy o test
        # con element_data manual), cae al path lento como fallback.
        gd_list = element_data[elem_id].get("gauss_data")
        if gd_list and "B" in gd_list[0]:
            key_D = (material.E, material.nu, project.analysis_type)
            D = D_cache.get(key_D)
            if D is None:
                D = constitutive_matrix(material.E, material.nu,
                                        project.analysis_type)
                D_cache[key_D] = D
            gauss_stresses = _gauss_stresses_from_precomputed(gd_list, u_elem, D)
        else:
            # Fallback: calcula B/J desde cero (path lento, solo para casos sin
            # gauss_data o sin clave 'B' — no ocurre en flujos normales).
            node_coords = element_data[elem_id]["node_coords"]
            gauss_stresses = compute_element_stresses(
                node_coords, u_elem, material.E, material.nu,
                elem.thickness, project.analysis_type, project.element_type
            )

        # Extrapolar a nodos
        if elem.num_nodes == 4:
            nodal_stresses = extrapolate_to_nodes_q4(gauss_stresses)
        elif elem.num_nodes == 9:
            nodal_stresses = extrapolate_to_nodes_q9(gauss_stresses)
        else:
            nodal_stresses = gauss_stresses[:elem.num_nodes]

        element_stresses[elem_id] = {
            "gauss_stresses": gauss_stresses,
            "nodal_stresses": nodal_stresses,
        }

        # Acumular para promedio nodal
        for i, nid in enumerate(elem.node_ids[:len(nodal_stresses)]):
            if nid not in nodal_accum:
                nodal_accum[nid] = {key: [] for key in stress_keys}
            for key in stress_keys:
                if key in nodal_stresses[i]:
                    nodal_accum[nid][key].append(nodal_stresses[i][key])

    # Promediar esfuerzos en nodos compartidos.
    # sum()/len() en listas cortas (1-4 elems) es ~10x más rápido que
    # np.mean() que paga overhead de dispatch numpy completo cada llamada.
    nodal_avg_stresses = {}
    for nid, accum in nodal_accum.items():
        avg = {}
        for key in stress_keys:
            values = accum[key]
            avg[key] = sum(values) / len(values) if values else 0.0
        nodal_avg_stresses[nid] = avg

    return element_stresses, nodal_avg_stresses
