"""
Normas de error L2 y H1-seminorma para Verificación por MMS.

Módulo puro NumPy. Dado un proyecto solucionado y una solución exacta
u_exact_fn(x, y) → (ux, uy) [y opcionalmente grad_u_exact_fn(x, y) → 2×2],
integra el error sobre todos los elementos usando cuadratura de Gauss y
retorna normas absolutas + relativas. La integracion esta vectorizada por
lotes (todos los elementos y puntos de Gauss a la vez); solo la evaluacion
de la solucion exacta (callables Python del usuario) recorre los puntos.

Trampa documentada: la cuadratura por defecto es de orden p+1 (i.e. 3×3
para Q4, 4×4 para Q9), una arriba del orden usado para K. Integrar con el
mismo orden subestima el error a O(h^{p+2}) artificial — Babuška &
Strouboulis 2001, sec. 5.
"""

from __future__ import annotations

import numpy as np

from config.settings import (
    ELEMENT_Q4, JACOBIAN_MIN_DETERMINANT,
)
from fem.shape_functions import get_shape_functions
from fem.gauss_quadrature import get_gauss_points_2d


__all__ = ["compute_error_norms"]


def _default_n_gauss(element_type):
    """Orden de cuadratura por defecto: p+1 (uno mas que el del solver)."""
    if element_type == ELEMENT_Q4:
        return 3
    # Q9: usamos 4 puntos por direccion (16 totales) para integrar errores
    # cuadraticos de un campo cuadratico (p=2 -> 2p=4 grado del error^2).
    return 4


def _accumulate_error_norms(
    node_coords_all,      # (n_elem, n_nodes, 2)
    u_elem_all,           # (n_elem, 2 * n_nodes)
    u_exact_all,          # (n_elem, n_gp, 2)
    grad_u_exact_all,     # (n_elem, n_gp, 2, 2)
    N_at_gps,             # (n_gp, n_nodes)
    dN_at_gps,            # (n_gp, 2, n_nodes)
    gauss_wts,            # (n_gp,)
    use_grad,             # bool
):
    """Integrales cuadraticas de L2 + H1 sobre todos los elementos, por lotes.

    Retorna (sq_err_u, sq_err_v, sq_norm_u_exact, sq_norm_v_exact,
    sq_err_grad, sq_norm_grad_exact, area_total).
    """
    # J[e, g] = dN_nat[g] @ coords[e]; dV = |det J| w.
    J = np.einsum("gak,ekb->egab", dN_at_gps, node_coords_all)
    det_J = J[..., 0, 0] * J[..., 1, 1] - J[..., 0, 1] * J[..., 1, 0]
    dV = np.abs(det_J) * gauss_wts[None, :]                          # (e, g)
    area_total = float(dV.sum())

    # Interpolacion de la solucion FEM en cada GP: u_h = sum_k N_k u_k.
    n_elem, n_nodes = node_coords_all.shape[:2]
    u_nodes = u_elem_all.reshape(n_elem, n_nodes, 2)                 # (e, k, c)
    u_h = np.einsum("gk,ekc->egc", N_at_gps, u_nodes)                # (e, g, 2)
    err = u_h - u_exact_all

    sq_err_u = float(np.sum(err[..., 0] ** 2 * dV))
    sq_err_v = float(np.sum(err[..., 1] ** 2 * dV))
    sq_norm_u_exact = float(np.sum(u_exact_all[..., 0] ** 2 * dV))
    sq_norm_v_exact = float(np.sum(u_exact_all[..., 1] ** 2 * dV))

    sq_err_grad = 0.0
    sq_norm_grad_exact = 0.0
    if use_grad:
        # Guard de determinante: un elemento degenerado metia inf/NaN en las
        # normas y arruinaba la tabla de convergencia entera; esos puntos se
        # excluyen de la seminorma (mismo criterio que el resto de fem/).
        ok = np.abs(det_J) >= JACOBIAN_MIN_DETERMINANT
        safe_det = np.where(ok, det_J, 1.0)
        inv_J = np.empty_like(J)
        inv_J[..., 0, 0] = J[..., 1, 1]
        inv_J[..., 0, 1] = -J[..., 0, 1]
        inv_J[..., 1, 0] = -J[..., 1, 0]
        inv_J[..., 1, 1] = J[..., 0, 0]
        inv_J /= safe_det[..., None, None]
        dN_phys = np.einsum("egal,glk->egak", inv_J, dN_at_gps)      # (e, g, 2, n)
        # grad u_h[r, c] = d u_r / d x_c = sum_k dN_phys[c, k] u[k, r]
        grad_h = np.einsum("egck,ekr->egrc", dN_phys, u_nodes)      # (e, g, 2, 2)
        diff = grad_h - grad_u_exact_all
        w = (dV * ok)[..., None, None]
        sq_err_grad = float(np.sum(diff ** 2 * w))
        sq_norm_grad_exact = float(np.sum(grad_u_exact_all ** 2 * w))

    return (sq_err_u, sq_err_v, sq_norm_u_exact, sq_norm_v_exact,
            sq_err_grad, sq_norm_grad_exact, area_total)


def compute_error_norms(project, solution, u_exact_fn,
                        grad_u_exact_fn=None, *, n_gauss=None):
    """Integra el error de la solucion FEM contra una solucion exacta.

    Parametros:
        project: ProjectModel ya solucionado.
        solution: dict retornado por solve_system (contiene "u").
        u_exact_fn: callable (x, y) -> (ux_exact, uy_exact).
        grad_u_exact_fn: callable (x, y) -> ndarray 2x2
            [[du/dx, du/dy], [dv/dx, dv/dy]]. Si es None, las normas
            asociadas al gradiente (H1_semi, L2_grad) se omiten.
        n_gauss: numero de puntos de Gauss por direccion. Por defecto
            p+1 (3 para Q4, 4 para Q9). Pasar un entero >= 1 para forzar.

    Retorna dict con claves:
        L2_u, L2_v          - ||u_h - u_exact||_L2, idem para v
        L2_disp             - sqrt(L2_u**2 + L2_v**2)
        L2_disp_rel         - L2_disp / ||u_exact||_L2 (None si exacta = 0)
        H1_semi             - ||grad(u - u_exact)||_L2 (solo si grad_u_exact_fn)
        L2_grad             - alias de H1_semi (claridad)
        H1_semi_rel         - H1_semi / ||grad u_exact||_L2
        h                   - tamano de malla medio (sqrt(area_total/n_elems))
        ndof                - 2 * num_nodes
        n_gauss             - orden de cuadratura usado
    """
    if solution is None or "u" not in solution:
        raise ValueError("solution debe ser el dict retornado por solve_system.")

    u_global = np.asarray(solution["u"], dtype=float)
    idx_map = project.node_index_map
    element_type = project.element_type
    N_func, dN_func = get_shape_functions(element_type)

    if n_gauss is None:
        n_gauss = _default_n_gauss(element_type)
    gauss_pts, gauss_wts = get_gauss_points_2d(n_gauss)
    n_gp = len(gauss_pts)

    elems = list(project.elements.values())
    n_elem = len(elems)
    if n_elem == 0:
        # Sin elementos: devolver dict con ceros (caso edge en tests).
        return {
            "L2_u": 0.0, "L2_v": 0.0, "L2_disp": 0.0,
            "L2_disp_rel": None,
            "H1_semi": None, "L2_grad": None, "H1_semi_rel": None,
            "h": 0.0, "area_total": 0.0,
            "ndof": project.total_dof, "n_gauss": int(n_gauss),
        }
    n_nodes = elems[0].num_nodes

    # Precomputar N y dN en cada GP (independientes del elemento).
    N_at_gps = np.empty((n_gp, n_nodes))
    dN_at_gps = np.empty((n_gp, 2, n_nodes))
    for g in range(n_gp):
        xi, eta = float(gauss_pts[g, 0]), float(gauss_pts[g, 1])
        N_at_gps[g] = N_func(xi, eta)
        dN_at_gps[g] = dN_func(xi, eta)

    # Arrays "flat" de todos los elementos.
    node_coords_all = np.empty((n_elem, n_nodes, 2))
    u_elem_all = np.empty((n_elem, 2 * n_nodes))
    for e, elem in enumerate(elems):
        for k, nid in enumerate(elem.node_ids):
            node = project.nodes[nid]
            node_coords_all[e, k, 0] = node.x
            node_coords_all[e, k, 1] = node.y
            base = 2 * idx_map[nid]
            u_elem_all[e, 2 * k]     = u_global[base]
            u_elem_all[e, 2 * k + 1] = u_global[base + 1]

    # Pre-evaluar la solucion exacta y opcionalmente su gradiente en CADA
    # (elem, GP): son callables Python del usuario, asi que es la unica
    # pasada que recorre los puntos uno a uno (< 5000 elem * 16 GP).
    xy_gps = np.einsum("gk,ekc->egc", N_at_gps, node_coords_all)     # (e, g, 2)
    u_exact_all = np.empty((n_elem, n_gp, 2))
    use_grad = grad_u_exact_fn is not None
    grad_u_exact_all = np.zeros((n_elem, n_gp, 2, 2))
    for e in range(n_elem):
        for g in range(n_gp):
            x_gp = float(xy_gps[e, g, 0])
            y_gp = float(xy_gps[e, g, 1])
            ux_e, uy_e = u_exact_fn(x_gp, y_gp)
            u_exact_all[e, g, 0] = float(ux_e)
            u_exact_all[e, g, 1] = float(uy_e)
            if use_grad:
                grad_u_exact_all[e, g] = np.asarray(grad_u_exact_fn(x_gp, y_gp),
                                                    dtype=float)

    (sq_err_u, sq_err_v, sq_norm_u_exact, sq_norm_v_exact,
     sq_err_grad, sq_norm_grad_exact, area_total) = (
        _accumulate_error_norms(
            node_coords_all, u_elem_all, u_exact_all, grad_u_exact_all,
            N_at_gps, dN_at_gps, gauss_wts, use_grad,
        )
    )

    L2_u = float(np.sqrt(sq_err_u))
    L2_v = float(np.sqrt(sq_err_v))
    L2_disp = float(np.sqrt(sq_err_u + sq_err_v))
    norm_disp_exact = float(np.sqrt(sq_norm_u_exact + sq_norm_v_exact))
    L2_disp_rel = (L2_disp / norm_disp_exact) if norm_disp_exact > 0 else None

    H1_semi = None
    H1_semi_rel = None
    if grad_u_exact_fn is not None:
        H1_semi = float(np.sqrt(sq_err_grad))
        norm_grad_exact = float(np.sqrt(sq_norm_grad_exact))
        H1_semi_rel = (H1_semi / norm_grad_exact) if norm_grad_exact > 0 else None

    h = float(np.sqrt(area_total / max(len(project.elements), 1)))

    return {
        "L2_u": L2_u,
        "L2_v": L2_v,
        "L2_disp": L2_disp,
        "L2_disp_rel": L2_disp_rel,
        "H1_semi": H1_semi,
        "L2_grad": H1_semi,
        "H1_semi_rel": H1_semi_rel,
        "h": h,
        "area_total": float(area_total),
        "ndof": project.total_dof,
        "n_gauss": int(n_gauss),
    }
