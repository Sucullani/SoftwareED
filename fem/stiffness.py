"""
Matriz de rigidez del elemento.
kₑ = ∫∫ Bᵀ D B |det(J)| t dξ dη

Dos versiones:
- `element_stiffness(...)`: version "completa" que retorna ke + gauss_data
  con TODOS los intermedios (J, B, dN_phys, ke_contribution por GP). La
  consumen los modulos educativos (M5 — rigidez analitica) que necesitan
  inspeccionar cada paso. Esta NO esta JIT.
- `element_stiffness_fast(...)` + `_element_stiffness_kernel_njit(...)`:
  version optimizada del solve productivo. Solo retorna ke + B + det_J por
  GP — sin diccionarios, todo arrays. Usado por `assemble_global_system`.
  Speedup tipico ~5-15x vs version Python.
"""

import numpy as np

from fem.shape_functions import get_shape_functions
from fem.gauss_quadrature import (
    get_gauss_points_for_element,
    get_dN_at_gauss_points,
)
from fem.jacobian import compute_jacobian, compute_dN_physical, _JAC_MIN_DET
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix
from fem._numba_compat import njit


@njit(cache=True)
def _element_stiffness_kernel_njit(node_coords, dN_at_gps, gauss_wts, D, thickness):
    """Kernel JIT del calculo de ke. Devuelve ke + B + det_J por GP.

    Parametros:
        node_coords: (n_nodes, 2) — coords (x, y) de los nodos.
        dN_at_gps: (n_gp, 2, n_nodes) — derivadas naturales evaluadas en
            cada Gauss point (precomputadas via `get_dN_at_gauss_points`).
        gauss_wts: (n_gp,) — pesos w_i * w_j.
        D: (3, 3) — matriz constitutiva (ya armada por
            `_constitutive_matrix_njit`).
        thickness: float — espesor del elemento.

    Retorna:
        ke: (n_dof, n_dof) — matriz de rigidez (n_dof = 2 * n_nodes).
        B_at_gps: (n_gp, 3, n_dof) — matrices B en cada GP. Reusadas por
            `stress.py` para evitar recomputo en post-process.
        det_J_at_gps: (n_gp,) — det(J) en cada GP. Reusados por el
            ensamblaje de body forces y por el path crudo del post.

    Sin allocations de dicts, sin if/else sobre strings, todo loops C.
    """
    n_gp = dN_at_gps.shape[0]
    n_nodes = node_coords.shape[0]
    n_dof = 2 * n_nodes

    ke = np.zeros((n_dof, n_dof))
    B_at_gps = np.zeros((n_gp, 3, n_dof))
    det_J_at_gps = np.empty(n_gp)

    for gp in range(n_gp):
        dN_nat = dN_at_gps[gp]  # (2, n_nodes)

        # Jacobiano J = dN_nat @ node_coords, expandido para que Numba
        # genere SIMD sobre el loop interno (mas rapido que matmul 2x2).
        J00 = 0.0
        J01 = 0.0
        J10 = 0.0
        J11 = 0.0
        for k in range(n_nodes):
            J00 += dN_nat[0, k] * node_coords[k, 0]
            J01 += dN_nat[0, k] * node_coords[k, 1]
            J10 += dN_nat[1, k] * node_coords[k, 0]
            J11 += dN_nat[1, k] * node_coords[k, 1]

        det_J = J00 * J11 - J01 * J10
        if abs(det_J) < _JAC_MIN_DET:
            raise ValueError("Jacobiano singular en element_stiffness.")

        det_J_at_gps[gp] = det_J
        inv_d = 1.0 / det_J
        invJ00 =  J11 * inv_d
        invJ01 = -J01 * inv_d
        invJ10 = -J10 * inv_d
        invJ11 =  J00 * inv_d

        # B inline: para cada nodo k, dN_phys = inv_J @ dN_nat[:, k].
        # Llenamos directamente B_at_gps[gp] para evitar copias.
        B = B_at_gps[gp]
        for k in range(n_nodes):
            dN_phys_x = invJ00 * dN_nat[0, k] + invJ01 * dN_nat[1, k]
            dN_phys_y = invJ10 * dN_nat[0, k] + invJ11 * dN_nat[1, k]
            B[0, 2 * k]     = dN_phys_x
            B[1, 2 * k + 1] = dN_phys_y
            B[2, 2 * k]     = dN_phys_y
            B[2, 2 * k + 1] = dN_phys_x

        # ke += factor * B.T @ D @ B. Para Q9 (B es 3x18), DB es 3x18.
        # Numba inline matmul es eficiente en matrices chicas.
        DB = D @ B            # (3, n_dof)
        BDB = B.T @ DB        # (n_dof, n_dof)
        factor = abs(det_J) * thickness * gauss_wts[gp]
        for i in range(n_dof):
            for j in range(n_dof):
                ke[i, j] += BDB[i, j] * factor

    return ke, B_at_gps, det_J_at_gps


def element_stiffness_fast(node_coords, E, nu, thickness, analysis_type, element_type):
    """Wrapper rapido sobre `_element_stiffness_kernel_njit`.

    Resuelve dN_at_gps / gauss_wts (cacheados por element_type) + D, y
    llama al kernel JIT. Usado por `assemble_global_system` en el path
    productivo del solve.

    Retorna: (ke, B_at_gps, det_J_at_gps, gauss_wts).
    """
    D = constitutive_matrix(E, nu, analysis_type)
    dN_at_gps, gauss_pts, gauss_wts, _N_at_gps = get_dN_at_gauss_points(element_type)
    ke, B_at_gps, det_J_at_gps = _element_stiffness_kernel_njit(
        node_coords, dN_at_gps, gauss_wts, D, thickness
    )
    return ke, B_at_gps, det_J_at_gps, gauss_wts


def element_stiffness(node_coords, E, nu, thickness, analysis_type, element_type):
    """
    Calcula la matriz de rigidez del elemento usando cuadratura de Gauss.

    Version "completa" — genera `gauss_data` con todos los intermedios
    para que los modulos educativos (M5) puedan inspeccionar cada paso.
    El solve productivo usa `element_stiffness_fast` (JIT) en su lugar.

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
