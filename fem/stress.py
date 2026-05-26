"""
Cálculo de esfuerzos en puntos de Gauss y extrapolación a nodos.
σ = D · B · uₑ
"""

from __future__ import annotations

import numpy as np

from fem.shape_functions import get_shape_functions, shape_functions_q9
from fem.gauss_quadrature import get_gauss_points_for_element, get_gauss_points_2d
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix


def compute_element_stresses(node_coords: np.ndarray, u_elem: np.ndarray,
                             E: float, nu: float, thickness: float,
                             analysis_type: str, element_type: str) -> "list[dict]":
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


def extrapolate_to_nodes_q4(gauss_stresses):
    """
    Extrapola esfuerzos de 4 puntos de Gauss (2×2) a 4 nodos del elemento Q4.
    Usa la matriz de extrapolación basada en los puntos de Gauss.

    Las coordenadas naturales de los nodos son (±1, ±1).
    Los puntos de Gauss están en (±1/√3, ±1/√3).
    Factor de extrapolación: √3.
    """
    s = np.sqrt(3.0)

    # Matriz de extrapolación (4 nodos × 4 puntos de Gauss)
    extrap = 0.25 * np.array([
        [(1 + s) * (1 + s), (1 - s) * (1 + s), (1 - s) * (1 - s), (1 + s) * (1 - s)],
        [(1 + s) * (1 - s), (1 - s) * (1 - s), (1 - s) * (1 + s), (1 + s) * (1 + s)],
        [(1 - s) * (1 - s), (1 + s) * (1 - s), (1 + s) * (1 + s), (1 - s) * (1 + s)],
        [(1 - s) * (1 + s), (1 + s) * (1 + s), (1 + s) * (1 - s), (1 - s) * (1 - s)],
    ])

    # Extraer componentes de esfuerzo de cada punto de Gauss
    stress_keys = ["sigma_x", "sigma_y", "tau_xy", "sigma_1", "sigma_2", "von_mises"]
    nodal_stresses = [{} for _ in range(4)]

    for key in stress_keys:
        gauss_values = np.array([gs[key] for gs in gauss_stresses])
        nodal_values = extrap @ gauss_values
        for i in range(4):
            nodal_stresses[i][key] = nodal_values[i]

    return nodal_stresses


# Cache de la matriz inversa Q9 (se computa una vez).
_Q9_EXTRAP_MATRIX = None


def _q9_extrapolation_matrix():
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


def extrapolate_to_nodes_q9(gauss_stresses):
    """
    Extrapola esfuerzos de 9 puntos de Gauss (3×3) a los 9 nodos del Q9.
    El orden de Gauss sigue get_gauss_points_2d(3); el orden de nodos es el
    canónico de shape_functions_q9 (4 esquinas, 4 medios, centro).
    """
    M_inv = _q9_extrapolation_matrix()
    stress_keys = ["sigma_x", "sigma_y", "tau_xy", "sigma_1", "sigma_2", "von_mises"]
    nodal_stresses = [{} for _ in range(9)]
    for key in stress_keys:
        gauss_values = np.array([gs[key] for gs in gauss_stresses])
        nodal_values = M_inv @ gauss_values
        for i in range(9):
            nodal_stresses[i][key] = nodal_values[i]
    return nodal_stresses


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

    # Acumuladores para promedio nodal
    stress_keys = ["sigma_x", "sigma_y", "tau_xy", "sigma_1", "sigma_2", "von_mises"]
    nodal_accum = {}  # {node_id: {key: [values]}}

    for elem_id, elem in project.elements.items():
        material = project.materials.get(elem.material_name)
        if material is None:
            material = next(iter(project.materials.values()))

        node_coords = element_data[elem_id]["node_coords"]
        dof_indices = element_data[elem_id]["dof_indices"]
        u_elem = u[dof_indices]

        # Esfuerzos en puntos de Gauss
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

    # Promediar esfuerzos en nodos compartidos
    nodal_avg_stresses = {}
    for nid, accum in nodal_accum.items():
        nodal_avg_stresses[nid] = {}
        for key in stress_keys:
            values = accum[key]
            if values:
                nodal_avg_stresses[nid][key] = np.mean(values)
            else:
                nodal_avg_stresses[nid][key] = 0.0

    return element_stresses, nodal_avg_stresses
