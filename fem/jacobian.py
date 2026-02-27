"""
Cálculo del Jacobiano para elementos isoparamétricos.
J = ∂(x,y)/∂(ξ,η)
"""

import numpy as np


def compute_jacobian(dN_nat, node_coords):
    """
    Calcula la matriz Jacobiana en un punto (ξ, η).

    Parámetros:
        dN_nat: array (2, n_nodes) - Derivadas de N respecto a (ξ, η).
        node_coords: array (n_nodes, 2) - Coordenadas (x, y) de los nodos.

    Retorna:
        J: array (2, 2) - Matriz Jacobiana
        det_J: float - Determinante del Jacobiano
        inv_J: array (2, 2) - Inversa del Jacobiano
    """
    # J = dN_nat · node_coords
    # J = [[∂x/∂ξ, ∂y/∂ξ],
    #      [∂x/∂η, ∂y/∂η]]
    J = dN_nat @ node_coords  # (2, n_nodes) × (n_nodes, 2) = (2, 2)

    det_J = np.linalg.det(J)

    if abs(det_J) < 1e-15:
        raise ValueError(
            f"Jacobiano singular (det(J) = {det_J:.2e}). "
            "El elemento puede estar distorsionado o tener nodos coincidentes."
        )

    inv_J = np.linalg.inv(J)

    return J, det_J, inv_J


def compute_dN_physical(dN_nat, inv_J):
    """
    Convierte derivadas de coordenadas naturales a coordenadas físicas.

    dN_phys = J⁻¹ · dN_nat

    Parámetros:
        dN_nat: array (2, n_nodes) - ∂N/∂ξ, ∂N/∂η
        inv_J: array (2, 2) - Inversa del Jacobiano

    Retorna:
        dN_phys: array (2, n_nodes) - ∂N/∂x, ∂N/∂y
    """
    dN_phys = inv_J @ dN_nat
    return dN_phys
