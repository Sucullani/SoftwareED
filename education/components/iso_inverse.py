"""
iso_inverse: mapeo inverso (x,y) -> (xi,eta) por Newton-Raphson y mapeo
directo (xi,eta) -> (x,y) usando las funciones de forma.

Implementación autosuficiente — no depende de widgets de UI. Reusable desde
cualquier módulo educativo o componente que necesite resolver
isoparametría inversa (M1, M2, ...).
"""

from __future__ import annotations

import numpy as np

from config.settings import NUMERICAL_TOLERANCE
from fem.shape_functions import get_shape_functions
from fem.jacobian import compute_jacobian


def in_natural_domain(xi: float, eta: float, margin: float = 0.0) -> bool:
    """¿(xi, eta) está dentro del cuadrado natural [-1,1]^2 (con margen)?"""
    return abs(xi) <= 1.0 + margin and abs(eta) <= 1.0 + margin


def _physical_to_natural(
    x: float,
    y: float,
    node_coords: np.ndarray,
    element_type: str = "Q4",
    tol: float = NUMERICAL_TOLERANCE,
    max_iter: int = 50,
):
    """Newton-Raphson para invertir el mapeo isoparamétrico.

    Retorna (xi, eta) si converge, None si no.
    """
    N_fn, dN_fn = get_shape_functions(element_type)

    # Determinar cuántos nodos usar (4 para Q4, 9 para Q9).
    n_test = len(N_fn(0.0, 0.0))
    coords = np.asarray(node_coords, dtype=float)[:n_test]

    # Inicialización: centroide del elemento físico mapeado a (0, 0).
    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N = N_fn(xi, eta)
        xy = N @ coords
        residual = np.array([x - xy[0], y - xy[1]])
        if np.linalg.norm(residual) < tol:
            return float(xi), float(eta)
        dN_nat = dN_fn(xi, eta)
        # J^T mapea (dxi, deta) -> (dx, dy); necesitamos invertirlo.
        try:
            J, detJ, _ = compute_jacobian(dN_nat, coords)
        except Exception:
            return None
        if abs(detJ) < 1e-14:
            return None
        # J^T es 2x2: filas son [dx/dxi, dy/dxi] y [dx/deta, dy/deta].
        Jt = J.T
        try:
            delta = np.linalg.solve(Jt, residual)
        except np.linalg.LinAlgError:
            return None
        xi += float(delta[0])
        eta += float(delta[1])
        # Bail-out si nos vamos muy lejos.
        if abs(xi) > 5.0 or abs(eta) > 5.0:
            return None
    return None


def iso_inverse_map(
    x: float,
    y: float,
    node_coords: np.ndarray,
    element_type: str = "Q4",
    tol: float = NUMERICAL_TOLERANCE,
    max_iter: int = 50,
):
    """Mapea un punto físico (x, y) al dominio natural (xi, eta).

    Retorna (xi, eta) o None si Newton-Raphson no converge o el punto cae
    fuera del elemento (con un pequeño margen para tolerar clicks de borde).
    """
    result = _physical_to_natural(
        x, y, node_coords, element_type, tol=tol, max_iter=max_iter
    )
    if result is None:
        return None
    xi, eta = result
    if not in_natural_domain(xi, eta, margin=0.05):
        return None
    return xi, eta


def natural_to_physical(xi: float, eta: float, node_coords: np.ndarray,
                        element_type: str = "Q4") -> np.ndarray:
    """Mapeo directo (xi, eta) -> (x, y) via N_i(xi, eta) · coords_i."""
    N_fn, _ = get_shape_functions(element_type)
    N = N_fn(xi, eta)
    # La longitud de N (4 o 9) define cuántas filas de node_coords participan.
    return N @ np.asarray(node_coords, dtype=float)[: len(N)]


def element_coords(project, element):
    """Coords [N×2] de los nodos de `element` desde `project.nodes`, o None
    si el elemento referencia un nodo inexistente.

    Helper compartido — antes estaba duplicado byte-a-byte en M1
    (_element_coords), M2/M4 (_coords_macro), M5 (_node_coords) y M7 (inline)
    con el mismo try/except KeyError. Centralizarlo evita el drift y respeta
    la separación identidad/índice (usa element.node_ids, no `2*(nid-1)`).
    """
    if project is None or element is None:
        return None
    try:
        return np.array(
            [[project.nodes[nid].x, project.nodes[nid].y]
             for nid in element.node_ids],
            dtype=float,
        )
    except KeyError:
        return None


__all__ = [
    "iso_inverse_map", "natural_to_physical", "in_natural_domain",
    "element_coords",
]
