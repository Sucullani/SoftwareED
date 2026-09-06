"""
Funciones de forma para elementos isoparamétricos Q4 y Q9.
En coordenadas naturales (ξ, η) ∈ [-1, 1] × [-1, 1].

Version legible, punto a punto: la usan los modulos educativos (M1..M5),
la memoria de calculo y las caches de `fem/gauss_quadrature.py` /
`fem/probe_query.py`, que las evaluan una sola vez por punto y reutilizan
los arrays resultantes en el motor vectorizado por lotes (`fem/batch.py`).
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
    N = np.empty(4)
    N[0] = 0.25 * (1.0 - xi) * (1.0 - eta)
    N[1] = 0.25 * (1.0 + xi) * (1.0 - eta)
    N[2] = 0.25 * (1.0 + xi) * (1.0 + eta)
    N[3] = 0.25 * (1.0 - xi) * (1.0 + eta)
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
    N = np.empty(9)
    # Nodos esquina
    N[0] = 0.25 * xi * (xi - 1.0) * eta * (eta - 1.0)
    N[1] = 0.25 * xi * (xi + 1.0) * eta * (eta - 1.0)
    N[2] = 0.25 * xi * (xi + 1.0) * eta * (eta + 1.0)
    N[3] = 0.25 * xi * (xi - 1.0) * eta * (eta + 1.0)
    # Nodos de lado
    N[4] = 0.5 * (1.0 - xi2) * eta * (eta - 1.0)
    N[5] = 0.5 * xi * (xi + 1.0) * (1.0 - eta2)
    N[6] = 0.5 * (1.0 - xi2) * eta * (eta + 1.0)
    N[7] = 0.5 * xi * (xi - 1.0) * (1.0 - eta2)
    # Nodo central
    N[8] = (1.0 - xi2) * (1.0 - eta2)
    return N


def dshape_functions_q4(xi, eta):
    """
    Derivadas de funciones de forma Q4 respecto a coordenadas naturales.

    Retorna: dN = [[∂N1/∂ξ, ∂N2/∂ξ, ∂N3/∂ξ, ∂N4/∂ξ],
                   [∂N1/∂η, ∂N2/∂η, ∂N3/∂η, ∂N4/∂η]]
             array (2, 4)
    """
    dN = np.empty((2, 4))
    # ∂N/∂ξ
    dN[0, 0] = -0.25 * (1.0 - eta)
    dN[0, 1] =  0.25 * (1.0 - eta)
    dN[0, 2] =  0.25 * (1.0 + eta)
    dN[0, 3] = -0.25 * (1.0 + eta)
    # ∂N/∂η
    dN[1, 0] = -0.25 * (1.0 - xi)
    dN[1, 1] = -0.25 * (1.0 + xi)
    dN[1, 2] =  0.25 * (1.0 + xi)
    dN[1, 3] =  0.25 * (1.0 - xi)
    return dN


def dshape_functions_q9(xi, eta):
    """
    Derivadas de funciones de forma Q9 respecto a coordenadas naturales.

    Retorna: dN array (2, 9)
    """
    xi2 = xi * xi
    eta2 = eta * eta
    dN = np.empty((2, 9))

    # ∂N/∂ξ
    dN[0, 0] = 0.25 * (2.0 * xi - 1.0) * eta * (eta - 1.0)
    dN[0, 1] = 0.25 * (2.0 * xi + 1.0) * eta * (eta - 1.0)
    dN[0, 2] = 0.25 * (2.0 * xi + 1.0) * eta * (eta + 1.0)
    dN[0, 3] = 0.25 * (2.0 * xi - 1.0) * eta * (eta + 1.0)
    dN[0, 4] = -xi * eta * (eta - 1.0)
    dN[0, 5] = 0.5 * (2.0 * xi + 1.0) * (1.0 - eta2)
    dN[0, 6] = -xi * eta * (eta + 1.0)
    dN[0, 7] = 0.5 * (2.0 * xi - 1.0) * (1.0 - eta2)
    dN[0, 8] = -2.0 * xi * (1.0 - eta2)

    # ∂N/∂η
    dN[1, 0] = 0.25 * xi * (xi - 1.0) * (2.0 * eta - 1.0)
    dN[1, 1] = 0.25 * xi * (xi + 1.0) * (2.0 * eta - 1.0)
    dN[1, 2] = 0.25 * xi * (xi + 1.0) * (2.0 * eta + 1.0)
    dN[1, 3] = 0.25 * xi * (xi - 1.0) * (2.0 * eta + 1.0)
    dN[1, 4] = 0.5 * (1.0 - xi2) * (2.0 * eta - 1.0)
    dN[1, 5] = -xi * (xi + 1.0) * eta
    dN[1, 6] = 0.5 * (1.0 - xi2) * (2.0 * eta + 1.0)
    dN[1, 7] = -xi * (xi - 1.0) * eta
    dN[1, 8] = -2.0 * eta * (1.0 - xi2)

    return dN


def get_shape_functions(element_type):
    """Retorna las funciones N y dN según el tipo de elemento."""
    from config.settings import ELEMENT_Q4
    if element_type == ELEMENT_Q4:
        return shape_functions_q4, dshape_functions_q4
    return shape_functions_q9, dshape_functions_q9
