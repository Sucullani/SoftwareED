"""
Matriz de rigidez del elemento.
kₑ = ∫∫ Bᵀ D B |det(J)| t dξ dη
"""

import numpy as np

from fem.shape_functions import get_shape_functions
from fem.gauss_quadrature import get_gauss_points_for_element
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix


def element_stiffness(node_coords, E, nu, thickness, analysis_type, element_type):
    """
    Calcula la matriz de rigidez del elemento usando cuadratura de Gauss.

    kₑ = Σᵢ Σⱼ wᵢ wⱼ Bᵀ D B |det(J)| t

    Parámetros:
        node_coords: array (n_nodes, 2) - Coordenadas de los nodos del elemento.
        E: float - Módulo de Young.
        nu: float - Coeficiente de Poisson.
        thickness: float - Espesor del elemento.
        analysis_type: str - "Tensión Plana" o "Deformación Plana".
        element_type: str - Tipo de elemento.

    Retorna:
        ke: array (2*n_nodes, 2*n_nodes) - Matriz de rigidez del elemento.
        gauss_data: list of dict - Datos en cada punto de Gauss (para módulos educativos).
    """
    n_nodes = node_coords.shape[0]
    n_dof = 2 * n_nodes

    # Matriz constitutiva
    D = constitutive_matrix(E, nu, analysis_type)

    # Funciones de forma y derivadas
    _, dN_func = get_shape_functions(element_type)

    # Puntos de Gauss
    gauss_pts, gauss_wts = get_gauss_points_for_element(element_type)

    # Inicializar matriz de rigidez
    ke = np.zeros((n_dof, n_dof))

    # Datos para módulos educativos
    gauss_data = []

    for gp_idx, (gp, w) in enumerate(zip(gauss_pts, gauss_wts)):
        xi, eta = gp[0], gp[1]

        # Derivadas en coordenadas naturales
        dN_nat = dN_func(xi, eta)

        # Jacobiano
        J, det_J, inv_J = compute_jacobian(dN_nat, node_coords)

        # Derivadas en coordenadas físicas
        dN_phys = compute_dN_physical(dN_nat, inv_J)

        # Matriz B
        B = compute_b_matrix(dN_phys)

        # Contribución al integrando: Bᵀ D B |det(J)| t w
        ke_contrib = B.T @ D @ B * abs(det_J) * thickness * w

        ke += ke_contrib

        # Guardar datos del punto de Gauss
        gauss_data.append({
            "index": gp_idx,
            "xi": xi,
            "eta": eta,
            "weight": w,
            "J": J.copy(),
            "det_J": det_J,
            "inv_J": inv_J.copy(),
            "dN_nat": dN_nat.copy(),
            "dN_phys": dN_phys.copy(),
            "B": B.copy(),
            "ke_contribution": ke_contrib.copy(),
        })

    return ke, gauss_data
