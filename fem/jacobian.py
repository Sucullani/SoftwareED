"""
Cálculo del Jacobiano para elementos isoparamétricos.
J = ∂(x,y)/∂(ξ,η)

Version legible para un punto (ξ, η): la usan M2/M3/M5, la memoria de
calculo, `compute_raw` y `element_stiffness`. El motor productivo calcula
J, det J y B de todos los elementos y puntos a la vez en `fem/batch.py`.
"""

import numpy as np

from config.settings import JACOBIAN_MIN_DETERMINANT


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

    Levanta ValueError si |det(J)| < JACOBIAN_MIN_DETERMINANT.
    """
    # J = dN_nat · node_coords; resultado (2, 2)
    J = dN_nat @ node_coords

    det_J = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]

    if abs(det_J) < JACOBIAN_MIN_DETERMINANT:
        raise ValueError("Jacobiano singular (det(J) demasiado chico).")

    # Inversa 2×2 exacta por cofactores (evita np.linalg.inv overhead).
    inv_J = np.empty((2, 2))
    inv_d = 1.0 / det_J
    inv_J[0, 0] =  J[1, 1] * inv_d
    inv_J[0, 1] = -J[0, 1] * inv_d
    inv_J[1, 0] = -J[1, 0] * inv_d
    inv_J[1, 1] =  J[0, 0] * inv_d

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
