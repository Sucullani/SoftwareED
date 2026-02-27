"""
Funciones de forma para elementos isoparamétricos Q4 y Q9.
En coordenadas naturales (ξ, η) ∈ [-1, 1] × [-1, 1].
"""

import numpy as np


def shape_functions_q4(xi, eta):
    """
    Funciones de forma para elemento Q4 (4 nodos).
    Nodos numerados en sentido antihorario:
      4 ---- 3
      |      |
      1 ---- 2

    Retorna: N = [N1, N2, N3, N4] array (4,)
    """
    N = 0.25 * np.array([
        (1 - xi) * (1 - eta),  # N1
        (1 + xi) * (1 - eta),  # N2
        (1 + xi) * (1 + eta),  # N3
        (1 - xi) * (1 + eta),  # N4
    ])
    return N


def shape_functions_q9(xi, eta):
    """
    Funciones de forma para elemento Q9 (9 nodos).
    Nodos numerados:
      4 -- 7 -- 3
      |    |    |
      8 -- 9 -- 6
      |    |    |
      1 -- 5 -- 2

    Retorna: N = [N1, ..., N9] array (9,)
    """
    xi2 = xi * xi
    eta2 = eta * eta

    N = np.array([
        # Nodos esquina
        0.25 * xi * (xi - 1) * eta * (eta - 1),   # N1
        0.25 * xi * (xi + 1) * eta * (eta - 1),   # N2
        0.25 * xi * (xi + 1) * eta * (eta + 1),   # N3
        0.25 * xi * (xi - 1) * eta * (eta + 1),   # N4
        # Nodos de lado
        0.5 * (1 - xi2) * eta * (eta - 1),         # N5
        0.5 * xi * (xi + 1) * (1 - eta2),          # N6
        0.5 * (1 - xi2) * eta * (eta + 1),         # N7
        0.5 * xi * (xi - 1) * (1 - eta2),          # N8
        # Nodo central
        (1 - xi2) * (1 - eta2),                     # N9
    ])
    return N


def dshape_functions_q4(xi, eta):
    """
    Derivadas de funciones de forma Q4 respecto a coordenadas naturales.

    Retorna: dN = [[∂N1/∂ξ, ∂N2/∂ξ, ∂N3/∂ξ, ∂N4/∂ξ],
                   [∂N1/∂η, ∂N2/∂η, ∂N3/∂η, ∂N4/∂η]]
             array (2, 4)
    """
    dN = 0.25 * np.array([
        [-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)],   # ∂N/∂ξ
        [-(1 - xi), -(1 + xi), (1 + xi),  (1 - xi)],      # ∂N/∂η
    ])
    return dN


def dshape_functions_q9(xi, eta):
    """
    Derivadas de funciones de forma Q9 respecto a coordenadas naturales.

    Retorna: dN array (2, 9
    """
    xi2 = xi * xi
    eta2 = eta * eta

    # ∂N/∂ξ
    dN_dxi = np.array([
        0.25 * (2 * xi - 1) * eta * (eta - 1),     # ∂N1/∂ξ
        0.25 * (2 * xi + 1) * eta * (eta - 1),     # ∂N2/∂ξ
        0.25 * (2 * xi + 1) * eta * (eta + 1),     # ∂N3/∂ξ
        0.25 * (2 * xi - 1) * eta * (eta + 1),     # ∂N4/∂ξ
        -xi * eta * (eta - 1),                       # ∂N5/∂ξ
        0.5 * (2 * xi + 1) * (1 - eta2),            # ∂N6/∂ξ
        -xi * eta * (eta + 1),                       # ∂N7/∂ξ
        0.5 * (2 * xi - 1) * (1 - eta2),            # ∂N8/∂ξ
        -2 * xi * (1 - eta2),                        # ∂N9/∂ξ
    ])

    # ∂N/∂η
    dN_deta = np.array([
        0.25 * xi * (xi - 1) * (2 * eta - 1),      # ∂N1/∂η
        0.25 * xi * (xi + 1) * (2 * eta - 1),      # ∂N2/∂η
        0.25 * xi * (xi + 1) * (2 * eta + 1),      # ∂N3/∂η
        0.25 * xi * (xi - 1) * (2 * eta + 1),      # ∂N4/∂η
        0.5 * (1 - xi2) * (2 * eta - 1),            # ∂N5/∂η
        -xi * (xi + 1) * eta,                        # ∂N6/∂η
        0.5 * (1 - xi2) * (2 * eta + 1),            # ∂N7/∂η
        -xi * (xi - 1) * eta,                        # ∂N8/∂η
        -2 * eta * (1 - xi2),                        # ∂N9/∂η
    ])

    dN = np.array([dN_dxi, dN_deta])
    return dN


def get_shape_functions(element_type):
    """Retorna las funciones N y dN según el tipo de elemento."""
    if element_type == "Q4" or "4 nodos" in str(element_type):
        return shape_functions_q4, dshape_functions_q4
    else:
        return shape_functions_q9, dshape_functions_q9
