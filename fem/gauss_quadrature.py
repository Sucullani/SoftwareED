"""
Puntos y pesos de cuadratura de Gauss para integración numérica.
"""

import numpy as np


# ─── Puntos y pesos de Gauss 1D ────────────────────────────────────────────

GAUSS_POINTS_1D = {
    1: {
        "points": np.array([0.0]),
        "weights": np.array([2.0]),
    },
    2: {
        "points": np.array([-1.0 / np.sqrt(3), 1.0 / np.sqrt(3)]),
        "weights": np.array([1.0, 1.0]),
    },
    3: {
        "points": np.array([-np.sqrt(3.0 / 5.0), 0.0, np.sqrt(3.0 / 5.0)]),
        "weights": np.array([5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0]),
    },
}


def get_gauss_points_2d(n_points):
    """
    Genera los puntos de Gauss 2D (producto tensorial).

    Parámetros:
        n_points: Número de puntos por dirección (2 para Q4, 3 para Q9).

    Retorna:
        points: array (n_total, 2) - coordenadas (ξ, η)
        weights: array (n_total,) - pesos wᵢ×wⱼ
    """
    gp1d = GAUSS_POINTS_1D[n_points]
    pts_1d = gp1d["points"]
    wts_1d = gp1d["weights"]

    points = []
    weights = []

    for i, (xi, wi) in enumerate(zip(pts_1d, wts_1d)):
        for j, (eta, wj) in enumerate(zip(pts_1d, wts_1d)):
            points.append([xi, eta])
            weights.append(wi * wj)

    return np.array(points), np.array(weights)


def get_gauss_points_for_element(element_type):
    """
    Retorna los puntos de Gauss apropiados para el tipo de elemento.
    Q4 → 2×2 (4 puntos)
    Q9 → 3×3 (9 puntos)
    """
    if element_type == "Q4" or "4 nodos" in str(element_type):
        return get_gauss_points_2d(2)
    else:
        return get_gauss_points_2d(3)
