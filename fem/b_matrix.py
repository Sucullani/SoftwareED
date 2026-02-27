"""
Matriz de deformación-desplazamiento B.
Relaciona desplazamientos nodales con deformaciones: ε = B · u
"""

import numpy as np


def compute_b_matrix(dN_phys):
    """
    Construye la matriz B a partir de las derivadas físicas de N.

    B = [[∂N1/∂x,   0,     ∂N2/∂x,   0,     ...],
         [  0,    ∂N1/∂y,    0,     ∂N2/∂y,  ...],
         [∂N1/∂y, ∂N1/∂x,  ∂N2/∂y, ∂N2/∂x,  ...]]

    Parámetros:
        dN_phys: array (2, n_nodes) - [∂N/∂x; ∂N/∂y]

    Retorna:
        B: array (3, 2*n_nodes) - Matriz deformación-desplazamiento
    """
    n_nodes = dN_phys.shape[1]
    B = np.zeros((3, 2 * n_nodes))

    for i in range(n_nodes):
        B[0, 2 * i] = dN_phys[0, i]       # ∂Ni/∂x → εx
        B[1, 2 * i + 1] = dN_phys[1, i]   # ∂Ni/∂y → εy
        B[2, 2 * i] = dN_phys[1, i]       # ∂Ni/∂y → γxy
        B[2, 2 * i + 1] = dN_phys[0, i]   # ∂Ni/∂x → γxy

    return B
