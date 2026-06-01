"""
Normas de error L2 y H1-seminorma para Verificación por MMS.

Módulo puro NumPy. Dado un proyecto solucionado y una solución exacta
u_exact_fn(x, y) → (ux, uy) [y opcionalmente grad_u_exact_fn(x, y) → 2×2],
integra el error sobre todos los elementos usando cuadratura de Gauss y
retorna normas absolutas + relativas.

Trampa documentada: la cuadratura por defecto es de orden p+1 (i.e. 3×3
para Q4, 4×4 para Q9), una arriba del orden usado para K. Integrar con el
mismo orden subestima el error a O(h^{p+2}) artificial — Babuška &
Strouboulis 2001, sec. 5.
"""

from __future__ import annotations

import numpy as np

from config.settings import ELEMENT_Q4, ELEMENT_Q9
from fem.shape_functions import get_shape_functions
from fem.gauss_quadrature import get_gauss_points_2d
from fem._numba_compat import njit


__all__ = ["compute_error_norms"]


def _default_n_gauss(element_type):
    """Orden de cuadratura por defecto: p+1 (uno mas que el del solver)."""
    if element_type == ELEMENT_Q4:
        return 3
    # Q9: usamos 4 puntos por direccion (16 totales) para integrar errores
    # cuadraticos de un campo cuadratico (p=2 -> 2p=4 grado del error^2).
    return 4


@njit(cache=True)
def _accumulate_error_norms_njit(
    node_coords_all,      # (n_elem, n_nodes, 2)
    u_elem_all,           # (n_elem, 2 * n_nodes)
    u_exact_all,          # (n_elem, n_gp, 2)
    grad_u_exact_all,     # (n_elem, n_gp, 2, 2) o array vacio (0,0,0,0) si no
    N_at_gps,             # (n_gp, n_nodes)
    dN_at_gps,            # (n_gp, 2, n_nodes)
    gauss_wts,            # (n_gp,)
    use_grad,             # bool
):
    """Kernel JIT: acumula los integrales cuadraticos de L2 + H1 sobre
    todos los elementos. Retorna (sq_err_u, sq_err_v, sq_norm_u_exact,
    sq_norm_v_exact, sq_err_grad, sq_norm_grad_exact, area_total).

    Sin allocations de B/inv_J por iteracion: el strain se computa
    directamente desde dN_nat + inv_J. La solucion exacta y su gradiente
    vienen pre-evaluados en `u_exact_all` y `grad_u_exact_all` porque las
    funciones de usuario son callables Python que Numba no puede inlinear.
    """
    n_elem = node_coords_all.shape[0]
    n_gp = gauss_wts.shape[0]
    n_nodes = node_coords_all.shape[1]

    sq_err_u = 0.0
    sq_err_v = 0.0
    sq_norm_u_exact = 0.0
    sq_norm_v_exact = 0.0
    sq_err_grad = 0.0
    sq_norm_grad_exact = 0.0
    area_total = 0.0

    for e in range(n_elem):
        for g in range(n_gp):
            N_vals = N_at_gps[g]
            dN_nat = dN_at_gps[g]
            w = gauss_wts[g]

            # J = dN_nat @ node_coords_all[e]
            J00 = 0.0; J01 = 0.0; J10 = 0.0; J11 = 0.0
            for k in range(n_nodes):
                J00 += dN_nat[0, k] * node_coords_all[e, k, 0]
                J01 += dN_nat[0, k] * node_coords_all[e, k, 1]
                J10 += dN_nat[1, k] * node_coords_all[e, k, 0]
                J11 += dN_nat[1, k] * node_coords_all[e, k, 1]
            det_J = J00 * J11 - J01 * J10
            absdJ = abs(det_J)
            area_total += absdJ * w

            # Interpolacion de la solucion FEM en el GP.
            ux_h = 0.0
            uy_h = 0.0
            for k in range(n_nodes):
                ux_h += N_vals[k] * u_elem_all[e, 2 * k]
                uy_h += N_vals[k] * u_elem_all[e, 2 * k + 1]

            ux_e = u_exact_all[e, g, 0]
            uy_e = u_exact_all[e, g, 1]

            sq_err_u += (ux_h - ux_e) * (ux_h - ux_e) * absdJ * w
            sq_err_v += (uy_h - uy_e) * (uy_h - uy_e) * absdJ * w
            sq_norm_u_exact += ux_e * ux_e * absdJ * w
            sq_norm_v_exact += uy_e * uy_e * absdJ * w

            if use_grad:
                # inv_J
                inv_d = 1.0 / det_J
                invJ00 =  J11 * inv_d
                invJ01 = -J01 * inv_d
                invJ10 = -J10 * inv_d
                invJ11 =  J00 * inv_d

                # grad u_h = [[du/dx, du/dy], [dv/dx, dv/dy]]
                dux_dx = 0.0; dux_dy = 0.0
                duy_dx = 0.0; duy_dy = 0.0
                for k in range(n_nodes):
                    dphx = invJ00 * dN_nat[0, k] + invJ01 * dN_nat[1, k]
                    dphy = invJ10 * dN_nat[0, k] + invJ11 * dN_nat[1, k]
                    u_x = u_elem_all[e, 2 * k]
                    u_y = u_elem_all[e, 2 * k + 1]
                    dux_dx += dphx * u_x
                    dux_dy += dphy * u_x
                    duy_dx += dphx * u_y
                    duy_dy += dphy * u_y

                # Error en gradiente: ||grad_h - grad_e||^2
                for r in range(2):
                    for c in range(2):
                        ge = grad_u_exact_all[e, g, r, c]
                        if r == 0 and c == 0:
                            gh = dux_dx
                        elif r == 0 and c == 1:
                            gh = dux_dy
                        elif r == 1 and c == 0:
                            gh = duy_dx
                        else:
                            gh = duy_dy
                        diff = gh - ge
                        sq_err_grad += diff * diff * absdJ * w
                        sq_norm_grad_exact += ge * ge * absdJ * w

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

    # Precomputar N y dN en cada GP (independientes del elemento).
    N_at_gps = np.empty((n_gp, 0))
    dN_at_gps = np.empty((n_gp, 2, 0))
    if project.elements:
        any_elem = next(iter(project.elements.values()))
        n_nodes_default = any_elem.num_nodes
        N_at_gps = np.empty((n_gp, n_nodes_default))
        dN_at_gps = np.empty((n_gp, 2, n_nodes_default))
        for g in range(n_gp):
            xi, eta = float(gauss_pts[g, 0]), float(gauss_pts[g, 1])
            N_at_gps[g] = N_func(xi, eta)
            dN_at_gps[g] = dN_func(xi, eta)

    # Construir arrays "flat" de todos los elementos para el kernel JIT.
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

    # Pre-evaluar la solucion exacta y opcionalmente su gradiente en
    # CADA (elem, GP). Es una sola pasada Python sobre n_elem * n_gp
    # GPs — para mallas tipicas (<5000 elem * 9 GP = 45k evals) es
    # mucho mas rapido que llamar al callable dentro del kernel.
    u_exact_all = np.empty((n_elem, n_gp, 2))
    use_grad = grad_u_exact_fn is not None
    grad_u_exact_all = np.zeros((n_elem if use_grad else 0,
                                  n_gp if use_grad else 0, 2, 2))

    for e in range(n_elem):
        for g in range(n_gp):
            N_vals = N_at_gps[g]
            x_gp = 0.0
            y_gp = 0.0
            for k in range(n_nodes):
                x_gp += float(N_vals[k]) * node_coords_all[e, k, 0]
                y_gp += float(N_vals[k]) * node_coords_all[e, k, 1]
            ux_e, uy_e = u_exact_fn(x_gp, y_gp)
            u_exact_all[e, g, 0] = float(ux_e)
            u_exact_all[e, g, 1] = float(uy_e)
            if use_grad:
                grad_e = np.asarray(grad_u_exact_fn(x_gp, y_gp), dtype=float)
                grad_u_exact_all[e, g] = grad_e

    # Asegurar contiguous para el kernel JIT.
    node_coords_all = np.ascontiguousarray(node_coords_all)
    u_elem_all = np.ascontiguousarray(u_elem_all)
    u_exact_all = np.ascontiguousarray(u_exact_all)
    # Numba exige consistencia de shapes; pasamos un array de ceros con
    # las shapes correctas (sin uso) si no se requiere gradiente.
    if not use_grad:
        grad_u_exact_all = np.zeros((n_elem, n_gp, 2, 2))

    (sq_err_u, sq_err_v, sq_norm_u_exact, sq_norm_v_exact,
     sq_err_grad, sq_norm_grad_exact, area_total) = (
        _accumulate_error_norms_njit(
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
