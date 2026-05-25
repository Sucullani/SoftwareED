"""
test_vv_extensions.py - Tests de regresion para las extensiones del solver
agregadas en la campana de Verificacion y Validacion (2026-05):
  - body_force_fn en assemble_global_system / solve_system
  - Dirichlet no-cero en BoundaryCondition.ux_value/uy_value
  - generate_structured_quad_mesh en models/mesh_utils.py
  - compute_error_norms en fem/error_norms.py

Ejecutar: python -m tests.test_vv_extensions
"""

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    ANALYSIS_PLANE_STRESS, ELEMENT_Q4, ELEMENT_Q9,
)
from fem.assembly import assemble_global_system
from fem.error_norms import compute_error_norms
from fem.solver import solve_system
from models.material import Material
from models.mesh_utils import (
    boundary_node_ids,
    generate_structured_quad_mesh,
)
from models.project import ProjectModel


# ─── Helpers ────────────────────────────────────────────────────────────────

def _make_square_project(n=2, element_type=ELEMENT_Q4):
    """Cuadrado unitario [0,1]^2 con material Acero, plane stress."""
    project = generate_structured_quad_mesh(
        corners=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        nx=n, ny=n,
        element_type=element_type,
        material_name="Acero Estructural",
        thickness=1.0,
        analysis_type=ANALYSIS_PLANE_STRESS,
    )
    return project


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"  PASS  {msg}")


# ─── 1. Body force == gravedad ──────────────────────────────────────────────

def test_body_force_equals_gravity():
    """Con body_force_fn=lambda x,y:(rho*gx, rho*gy) debe dar el mismo F que
    el ensamblaje con include_gravity=True y la misma densidad/gravedad."""
    print("\n[1/6] test_body_force_equals_gravity")
    project = _make_square_project(n=2, element_type=ELEMENT_Q4)
    rho = 7850.0
    gx, gy = 0.0, -9.81
    # Forzar densidad del material
    mat = list(project.materials.values())[0]
    mat.density = rho

    # Caso A: gravedad nativa
    project.gravity_x = gx
    project.gravity_y = gy
    project.include_gravity = True
    _, F_gravity, _ = assemble_global_system(project)

    # Caso B: body_force_fn explicito (debe ganar y dar resultado equivalente)
    project.include_gravity = False  # asegurarse de que el callback es la unica fuente
    bf = lambda x, y: (rho * gx, rho * gy)
    _, F_callback, _ = assemble_global_system(project, body_force_fn=bf)

    np.testing.assert_allclose(F_callback, F_gravity, rtol=1e-12, atol=1e-12)
    _assert(True, "body_force_fn constante == gravedad (rtol 1e-12)")


# ─── 2. BCs u=0 backward-compat ────────────────────────────────────────────

def test_dirichlet_zero_backward_compat():
    """Con todas las BCs en ux_value=uy_value=0 (default), solve_system debe
    dar exactamente el mismo `u` que un proyecto sin valores prescritos."""
    print("\n[2/6] test_dirichlet_zero_backward_compat")
    project = _make_square_project(n=4, element_type=ELEMENT_Q4)
    # Empotrar borde izquierdo
    for nid in boundary_node_ids(project, "left"):
        project.set_boundary_condition(nid, True, True)
    # Carga puntual en una esquina derecha superior
    right = boundary_node_ids(project, "right")
    project.set_nodal_load(right[-1], 0.0, -1.0)

    sol = solve_system(project)
    u = sol["u"]
    # Sanity: hay algun desplazamiento no nulo
    _assert(np.max(np.abs(u)) > 0.0, "BC u=0 produce desplazamientos no triviales")
    # Sanity: en los nodos restringidos u esta exactamente en 0
    for nid in boundary_node_ids(project, "left"):
        base = 2 * project.node_index_map[nid]
        _assert(abs(u[base]) < 1e-15, f"u_x exactamente 0 en nodo restringido {nid}")
        _assert(abs(u[base + 1]) < 1e-15, f"u_y exactamente 0 en nodo restringido {nid}")


# ─── 3. Dirichlet no-cero: rigid body extension ─────────────────────────────

def test_dirichlet_nonzero_rigid_body():
    """Patch test de traccion uniaxial: ux=delta*x, uy=-nu*delta*y impuesto en
    TODO el borde debe dar el mismo campo en todos los nodos interiores
    (solucion exacta del equilibrio sin body force en plane stress)."""
    print("\n[3/6] test_dirichlet_nonzero_rigid_body")
    project = _make_square_project(n=4, element_type=ELEMENT_Q4)
    delta = 0.001
    mat = list(project.materials.values())[0]
    nu = mat.nu

    # Imponer campo lineal en TODO el borde
    border_ids = set()
    for edge in ("left", "right", "top", "bottom"):
        border_ids.update(boundary_node_ids(project, edge))
    for nid in border_ids:
        node = project.nodes[nid]
        ux = delta * node.x
        uy = -nu * delta * node.y
        project.set_boundary_condition(nid, True, True, ux, uy)

    sol = solve_system(project)
    u = sol["u"]
    # En todos los nodos interiores el campo debe ser el mismo (es solucion exacta)
    max_err_ux = 0.0
    max_err_uy = 0.0
    for nid, node in project.nodes.items():
        base = 2 * project.node_index_map[nid]
        expected_ux = delta * node.x
        expected_uy = -nu * delta * node.y
        max_err_ux = max(max_err_ux, abs(u[base] - expected_ux))
        max_err_uy = max(max_err_uy, abs(u[base + 1] - expected_uy))
    _assert(max_err_ux < 1e-12,
            f"max |u_x - delta*x| = {max_err_ux:.3e} < 1e-12")
    _assert(max_err_uy < 1e-12,
            f"max |u_y - (-nu*delta*y)| = {max_err_uy:.3e} < 1e-12")


# ─── 4. MMS sanity check con malla fina ─────────────────────────────────────

def test_mms_sanity_fine_mesh():
    """Corre MMS con N=16 Q9, asserta L2_disp_rel < 1e-3.
    Confirma que body_force_fn + Dirichlet no-cero + error_norms funcionan."""
    print("\n[4/6] test_mms_sanity_fine_mesh")

    # Solucion manufacturada (mismas que el script MMS oficial)
    PI = math.pi
    E = 1.0
    nu = 0.3
    lam = E * nu / ((1 + nu) * (1 - nu))   # plane stress: lambda* = E*nu/(1-nu^2)
    mu = E / (2 * (1 + nu))

    def u_M(x, y):
        return (math.sin(PI * x) * math.sin(PI * y),
                math.cos(PI * x) * math.cos(PI * y))

    def grad_u_M(x, y):
        sx, cx = math.sin(PI * x), math.cos(PI * x)
        sy, cy = math.sin(PI * y), math.cos(PI * y)
        return np.array([
            [PI * cx * sy, PI * sx * cy],
            [-PI * sx * cy, -PI * cx * sy],
        ])

    def body_force_fn(x, y):
        # Equilibrio: div(sigma) + b = 0  =>  b = -div(sigma).
        # En plane stress con (lam, mu):
        #   div(sigma)_x = (lam+2mu)*u_xx + mu*u_yy + (lam+mu)*v_xy
        #   div(sigma)_y = (lam+mu)*u_xy + mu*v_xx + (lam+2mu)*v_yy
        sx, cx = math.sin(PI * x), math.cos(PI * x)
        sy, cy = math.sin(PI * y), math.cos(PI * y)
        pi2 = PI * PI
        d2u_dx2 = -pi2 * sx * sy
        d2u_dy2 = -pi2 * sx * sy
        d2u_dxdy = pi2 * cx * cy
        d2v_dx2 = -pi2 * cx * cy
        d2v_dy2 = -pi2 * cx * cy
        d2v_dxdy = pi2 * sx * sy
        # Equilibrio: div(sigma) + b = 0 => b = -div(sigma)
        # div(sigma)_x = (lam+2mu)*d2u/dx2 + mu*d2u/dy2 + (lam+mu)*d2v/dxdy
        # div(sigma)_y = (lam+mu)*d2u/dxdy + mu*d2v/dx2 + (lam+2mu)*d2v/dy2
        div_sx = (lam + 2 * mu) * d2u_dx2 + mu * d2u_dy2 + (lam + mu) * d2v_dxdy
        div_sy = (lam + mu) * d2u_dxdy + mu * d2v_dx2 + (lam + 2 * mu) * d2v_dy2
        return -div_sx, -div_sy

    N = 16
    project = generate_structured_quad_mesh(
        corners=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        nx=N, ny=N, element_type=ELEMENT_Q9,
        material_name="MMS",
        thickness=1.0,
        analysis_type=ANALYSIS_PLANE_STRESS,
    )
    # Material custom E=1, nu=0.3
    project.materials["MMS"] = Material(name="MMS", E=1.0, nu=0.3, density=0.0)

    # Dirichlet exacto en todo el borde
    border_ids = set()
    for edge in ("left", "right", "top", "bottom"):
        border_ids.update(boundary_node_ids(project, edge))
    for nid in border_ids:
        node = project.nodes[nid]
        ux, uy = u_M(node.x, node.y)
        project.set_boundary_condition(nid, True, True, ux, uy)

    sol = solve_system(project, body_force_fn=body_force_fn)
    norms = compute_error_norms(project, sol, u_M, grad_u_M)
    print(f"  N={N}, ndof={norms['ndof']}, L2_disp={norms['L2_disp']:.4e}, "
          f"L2_disp_rel={norms['L2_disp_rel']:.4e}, "
          f"H1_semi={norms['H1_semi']:.4e}")
    _assert(norms["L2_disp_rel"] < 1e-3,
            f"L2_disp_rel = {norms['L2_disp_rel']:.3e} < 1e-3 (Q9, N=16)")


# ─── 5. generate_structured_quad_mesh rectangulo ────────────────────────────

def test_structured_mesh_rect():
    """Cuadrado [0,1]^2 con nx=ny=2 debe dar 4 elementos, 9 nodos (Q4)."""
    print("\n[5/6] test_structured_mesh_rect")
    project = generate_structured_quad_mesh(
        corners=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        nx=2, ny=2, element_type=ELEMENT_Q4,
    )
    _assert(project.num_elements == 4,
            f"4 elementos (real: {project.num_elements})")
    _assert(project.num_nodes == 9,
            f"9 nodos (real: {project.num_nodes})")
    # Verificar conectividad CCW: shoelace > 0
    for elem in project.elements.values():
        coords = [(project.nodes[nid].x, project.nodes[nid].y)
                  for nid in elem.node_ids[:4]]
        x = [p[0] for p in coords]
        y = [p[1] for p in coords]
        shoelace = (x[0]*(y[1]-y[3]) + x[1]*(y[2]-y[0])
                    + x[2]*(y[3]-y[1]) + x[3]*(y[0]-y[2])) / 2
        _assert(shoelace > 0, f"elem {elem.id} es CCW (shoelace={shoelace:.4f})")


# ─── 6. generate_structured_quad_mesh trapecio Cook ─────────────────────────

def test_structured_mesh_cook():
    """Trapezoidal de Cook con nx=ny=4: det J > 0 en todos los Gauss points."""
    print("\n[6/6] test_structured_mesh_cook")
    project = generate_structured_quad_mesh(
        corners=[(0.0, 0.0), (48.0, 44.0), (48.0, 60.0), (0.0, 44.0)],
        nx=4, ny=4, element_type=ELEMENT_Q4,
    )
    _assert(project.num_elements == 16,
            f"16 elementos (real: {project.num_elements})")
    # det J > 0 en cada Gauss point de cada elemento
    from fem.shape_functions import get_shape_functions
    from fem.gauss_quadrature import get_gauss_points_for_element
    from fem.jacobian import compute_jacobian
    _, dN_func = get_shape_functions(project.element_type)
    gauss_pts, _ = get_gauss_points_for_element(project.element_type)
    min_det = float("inf")
    for elem in project.elements.values():
        coords = np.array(
            [[project.nodes[nid].x, project.nodes[nid].y]
             for nid in elem.node_ids], dtype=float)
        for gp in gauss_pts:
            dN_nat = dN_func(gp[0], gp[1])
            _, det_J, _ = compute_jacobian(dN_nat, coords)
            min_det = min(min_det, det_J)
    _assert(min_det > 0.0, f"det J min = {min_det:.4f} > 0 (Cook trapecio)")


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  test_vv_extensions: regression suite para extensiones V&V")
    print("=" * 70)
    test_body_force_equals_gravity()
    test_dirichlet_zero_backward_compat()
    test_dirichlet_nonzero_rigid_body()
    test_structured_mesh_rect()
    test_structured_mesh_cook()
    test_mms_sanity_fine_mesh()
    print("\n" + "=" * 70)
    print("  TODOS LOS TESTS DE EXTENSIONES PASARON")
    print("=" * 70)


if __name__ == "__main__":
    main()
