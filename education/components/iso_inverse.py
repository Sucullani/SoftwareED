"""
iso_inverse: mapeo inverso (x,y) -> (xi,eta) por Newton-Raphson.

Reexporta las funciones ya implementadas en element_picker para mantener
un solo punto de verdad, pero accesible desde los módulos nuevos sin
importar el widget ElementPicker.
"""

from __future__ import annotations

import numpy as np

from .element_picker import (
    physical_to_natural as _physical_to_natural,
    in_natural_domain,
)


def iso_inverse_map(
    x: float,
    y: float,
    node_coords: np.ndarray,
    element_type: str = "Q4",
    tol: float = 1e-10,
    max_iter: int = 50,
):
    """Mapea un punto físico (x,y) al dominio natural (xi,eta).

    Retorna (xi, eta) o None si Newton-Raphson no converge o el punto cae
    fuera del elemento (con un pequeño margen).
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
    """Mapeo directo (xi,eta) -> (x,y) via N_i(xi,eta) · coords_i."""
    from fem.shape_functions import get_shape_functions
    N_fn, _ = get_shape_functions(element_type)
    n_nodes = 4 if element_type == "Q4" or "4 nodos" in str(element_type) else 9
    N = N_fn(xi, eta)
    return N @ node_coords[:n_nodes]


__all__ = ["iso_inverse_map", "natural_to_physical", "in_natural_domain"]
