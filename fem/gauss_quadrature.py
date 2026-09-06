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
    # Gauss-Legendre 4-pt: usado por compute_error_norms (orden p+1 para Q9).
    4: {
        "points": np.array([
            -0.8611363115940526,
            -0.3399810435848563,
             0.3399810435848563,
             0.8611363115940526,
        ]),
        "weights": np.array([
            0.3478548451374538,
            0.6521451548625461,
            0.6521451548625461,
            0.3478548451374538,
        ]),
    },
}

# Cache de producto tensorial 2D: los puntos/pesos solo dependen de n — se
# computan una sola vez y se reutilizan. Evita 48000+ llamadas redundantes
# en mallas grandes (una por elemento × 2 fases: ensamblaje + esfuerzos).
_GAUSS_2D_CACHE: dict = {}


def get_gauss_points_2d(n_points):
    """
    Genera los puntos de Gauss 2D (producto tensorial).

    Parámetros:
        n_points: Número de puntos por dirección (2 para Q4, 3 para Q9).

    Retorna:
        points: array (n_total, 2) - coordenadas (ξ, η)  [solo lectura]
        weights: array (n_total,) - pesos wᵢ×wⱼ         [solo lectura]
    """
    cached = _GAUSS_2D_CACHE.get(n_points)
    if cached is not None:
        return cached

    gp1d = GAUSS_POINTS_1D[n_points]
    pts_1d = gp1d["points"]
    wts_1d = gp1d["weights"]

    points = []
    weights = []

    for xi, wi in zip(pts_1d, wts_1d):
        for eta, wj in zip(pts_1d, wts_1d):
            points.append([xi, eta])
            weights.append(wi * wj)

    result = (np.array(points), np.array(weights))
    _GAUSS_2D_CACHE[n_points] = result
    return result


# Cache por tipo de elemento — delegado a get_gauss_points_2d (ya cacheado).
_GAUSS_FOR_ELEM_CACHE: dict = {}


def get_gauss_points_for_element(element_type):
    """
    Retorna los puntos de Gauss apropiados para el tipo de elemento.
    Q4 → 2×2 (4 puntos)
    Q9 → 3×3 (9 puntos)
    """
    cached = _GAUSS_FOR_ELEM_CACHE.get(element_type)
    if cached is not None:
        return cached

    from config.settings import ELEMENT_Q4
    result = get_gauss_points_2d(2 if element_type == ELEMENT_Q4 else 3)
    _GAUSS_FOR_ELEM_CACHE[element_type] = result
    return result


# Cache de dN/dξ, dN/dη evaluado en TODOS los puntos Gauss del elemento.
# Como los GPs son fijos para un tipo (Q4=2x2, Q9=3x3), las derivadas
# son constantes por tipo de elemento — se computan una vez. Esto evita
# millones de llamadas a dshape_functions_q*() en assembly + stress.
_DN_AT_GAUSS_CACHE: dict = {}


def get_dN_at_gauss_points(element_type):
    """Retorna (dN_at_gps, gauss_pts, gauss_wts, N_at_gps) precomputados.

    dN_at_gps: shape (n_gp, 2, n_nodes) — derivadas naturales en cada GP.
    gauss_pts: shape (n_gp, 2) — coords (xi, eta) de cada GP.
    gauss_wts: shape (n_gp,) — pesos w_i * w_j.
    N_at_gps:  shape (n_gp, n_nodes) — funciones de forma en cada GP.

    Usado por el ensamblaje por lotes (`fem/batch.py`: geometria, rigidez
    y fuerzas de cuerpo, que necesita N en cada GP). Cacheado por element_type.
    """
    cached = _DN_AT_GAUSS_CACHE.get(element_type)
    if cached is not None:
        return cached

    from fem.shape_functions import get_shape_functions
    N_func, dN_func = get_shape_functions(element_type)
    gauss_pts, gauss_wts = get_gauss_points_for_element(element_type)

    n_gp = len(gauss_pts)
    # Evaluamos una vez para conocer la forma (n_nodes).
    dN_first = dN_func(gauss_pts[0, 0], gauss_pts[0, 1])
    n_nodes = dN_first.shape[1]

    dN_at_gps = np.empty((n_gp, 2, n_nodes))
    N_at_gps = np.empty((n_gp, n_nodes))
    for i in range(n_gp):
        xi, eta = gauss_pts[i, 0], gauss_pts[i, 1]
        dN_at_gps[i] = dN_func(xi, eta)
        N_at_gps[i] = N_func(xi, eta)

    result = (dN_at_gps, gauss_pts, gauss_wts, N_at_gps)
    _DN_AT_GAUSS_CACHE[element_type] = result
    return result
