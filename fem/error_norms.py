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
from fem.jacobian import compute_jacobian, compute_dN_physical


__all__ = ["compute_error_norms"]


def _default_n_gauss(element_type):
    """Orden de cuadratura por defecto: p+1 (uno mas que el del solver)."""
    if element_type == ELEMENT_Q4:
        return 3
    # Q9: usamos 4 puntos por direccion (16 totales) para integrar errores
    # cuadraticos de un campo cuadratico (p=2 -> 2p=4 grado del error^2).
    return 4


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

    # Acumuladores cuadraticos
    sq_err_u = 0.0
    sq_err_v = 0.0
    sq_norm_u_exact = 0.0
    sq_norm_v_exact = 0.0
    sq_err_grad = 0.0
    sq_norm_grad_exact = 0.0
    area_total = 0.0

    for elem in project.elements.values():
        node_ids = elem.node_ids
        n_nodes = elem.num_nodes
        node_coords = np.array(
            [[project.nodes[nid].x, project.nodes[nid].y] for nid in node_ids],
            dtype=float,
        )
        # Vector de desplazamientos del elemento (2*n_nodes,)
        u_elem = np.zeros(2 * n_nodes)
        for i, nid in enumerate(node_ids):
            base = 2 * idx_map[nid]
            u_elem[2 * i]     = u_global[base]
            u_elem[2 * i + 1] = u_global[base + 1]

        for gp, w in zip(gauss_pts, gauss_wts):
            xi, eta = float(gp[0]), float(gp[1])
            N_vals = N_func(xi, eta)
            dN_nat = dN_func(xi, eta)
            J, det_J, inv_J = compute_jacobian(dN_nat, node_coords)
            absdJ = abs(det_J)
            area_total += absdJ * w

            # Coords fisicas del Gauss point
            x_gp = float(N_vals @ node_coords[:, 0])
            y_gp = float(N_vals @ node_coords[:, 1])

            # Solucion FEM interpolada
            ux_h = float(N_vals @ u_elem[0::2])
            uy_h = float(N_vals @ u_elem[1::2])

            # Solucion exacta
            ux_e, uy_e = u_exact_fn(x_gp, y_gp)
            ux_e = float(ux_e)
            uy_e = float(uy_e)

            # Errores cuadraticos en desplazamientos
            sq_err_u += (ux_h - ux_e) ** 2 * absdJ * w
            sq_err_v += (uy_h - uy_e) ** 2 * absdJ * w
            sq_norm_u_exact += ux_e ** 2 * absdJ * w
            sq_norm_v_exact += uy_e ** 2 * absdJ * w

            # Gradiente (opcional)
            if grad_u_exact_fn is not None:
                dN_phys = compute_dN_physical(dN_nat, inv_J)  # (2, n_nodes)
                # grad u_h = [[du/dx, du/dy], [dv/dx, dv/dy]]
                u_x = u_elem[0::2]   # (n_nodes,)
                u_y = u_elem[1::2]
                dux_dx = float(dN_phys[0] @ u_x)
                dux_dy = float(dN_phys[1] @ u_x)
                duy_dx = float(dN_phys[0] @ u_y)
                duy_dy = float(dN_phys[1] @ u_y)
                grad_h = np.array([[dux_dx, dux_dy], [duy_dx, duy_dy]])
                grad_e = np.asarray(grad_u_exact_fn(x_gp, y_gp), dtype=float)
                diff = grad_h - grad_e
                sq_err_grad += float(np.sum(diff * diff)) * absdJ * w
                sq_norm_grad_exact += float(np.sum(grad_e * grad_e)) * absdJ * w

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
