"""
test_solver_regression.py - Regresion numerica del motor vectorizado contra la
formulacion legible elemento a elemento.

El oraculo es la version didactica de fem/ (la que ensenan M2/M3/M5/M7 y usa
la memoria de calculo): `element_stiffness` para ke con cuadratura punto a
punto, `compute_element_stresses` para sigma en los puntos de Gauss, y la
integracion explicita de las fuerzas de cuerpo. El camino productivo
(`assemble_global_system` / `solve_system` / `compute_all_stresses`) debe
reproducirlo con error relativo <= 1e-9 (CLAUDE.md, regla 21).

Ejecutar: python -m tests.test_solver_regression
"""

import os
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    ANALYSIS_PLANE_STRAIN, ANALYSIS_PLANE_STRESS, ELEMENT_Q4, ELEMENT_Q9,
)
from fem.equivalent_forces import (
    surface_load_to_nodal_forces, surface_load_to_nodal_forces_q9,
)
from fem.probe_query import principal_and_vm
from fem.shape_functions import get_shape_functions
from fem.solver import apply_boundary_conditions, solve_system
from fem.stiffness import element_stiffness
from fem.stress import (
    _STRESS_KEYS, compute_all_stresses, compute_element_stresses,
    extrapolate_to_nodes_q4, extrapolate_to_nodes_q9,
)
from models.mesh_utils import (
    boundary_node_ids, expand_q4_to_q9, find_edge_midnode,
    generate_structured_quad_mesh,
)
from tests.bench_timing import build_project as build_cook
from tests.example_data import load_example_project, load_example_project_q9
from tests.test_fem import _build_surface_load_case

REL_TOL = 1e-9


# ─── Casos ──────────────────────────────────────────────────────────────────

def _square(n, element_type, analysis_type=ANALYSIS_PLANE_STRESS):
    """Rectangulo 2x1 empotrado a la izquierda con una carga puntual."""
    p = generate_structured_quad_mesh(
        corners=[(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)],
        nx=n, ny=n, element_type=element_type,
        material_name="Acero Estructural", thickness=0.5,
        analysis_type=analysis_type,
    )
    for nid in boundary_node_ids(p, "left"):
        p.set_boundary_condition(nid, True, True)
    right = boundary_node_ids(p, "right")
    p.set_nodal_load(right[-1], 100.0, -250.0)
    return p


def _gravity_case():
    p = _square(4, ELEMENT_Q4)
    mat = next(iter(p.materials.values()))
    mat.density = 7850.0
    p.gravity_x, p.gravity_y, p.include_gravity = 1.5, -9.81, True
    return p


def _prescribed_case():
    p = _square(3, ELEMENT_Q9, ANALYSIS_PLANE_STRAIN)
    for nid in boundary_node_ids(p, "right"):
        node = p.nodes[nid]
        p.set_boundary_condition(nid, True, False, ux_value=1e-3 * node.y)
    return p


def _cases():
    yield "Q4 ejemplo (P=1000)", load_example_project(P=1000.0), None
    yield "Q9 ejemplo expandido", load_example_project_q9(P=1000.0), None
    yield "Q4 carga superficial", _build_surface_load_case(q=100.0), None
    p = _build_surface_load_case(q=100.0)
    expand_q4_to_q9(p)
    yield "Q9 carga superficial", p, None
    yield "Cook Q4 4x4 (trapecio)", build_cook(4, ELEMENT_Q4), None
    yield "Cook Q9 4x4 (trapecio)", build_cook(4, ELEMENT_Q9), None
    yield "Q4 gravedad (gx, gy)", _gravity_case(), None
    yield "Q9 prescrito, deformacion plana", _prescribed_case(), None
    yield "Q9 body_force_fn", _square(3, ELEMENT_Q9), (
        lambda x, y: (3.0 * x * y, -2.0 * x + 0.5))


# ─── Oraculo: formulacion legible ───────────────────────────────────────────

def _node_coords(project, elem):
    return np.array([[project.nodes[nid].x, project.nodes[nid].y]
                     for nid in elem.node_ids], dtype=float)


def _material(project, elem):
    mat = project.materials.get(elem.material_name)
    return mat if mat is not None else next(iter(project.materials.values()))


def _body_force(project, mat, body_force_fn):
    """Misma prioridad que fem.assembly: callable explicito > gravedad."""
    if body_force_fn is not None:
        return body_force_fn
    if (project.include_gravity and mat.density > 0.0
            and (project.gravity_x != 0.0 or project.gravity_y != 0.0)):
        rho, gx, gy = mat.density, project.gravity_x, project.gravity_y
        return lambda x, y: (rho * gx, rho * gy)
    return None


def _reference_system(project, body_force_fn=None):
    """K, F y ke por elemento con `element_stiffness` + scatter escalar."""
    n_dof = project.total_dof
    idx_map = project.node_index_map
    N_func, _ = get_shape_functions(project.element_type)
    rows, cols, data = [], [], []
    F = np.zeros(n_dof)
    ke_ref = {}

    for eid, elem in project.elements.items():
        coords = _node_coords(project, elem)
        mat = _material(project, elem)
        ke, gauss_data = element_stiffness(
            coords, mat.E, mat.nu, elem.thickness,
            project.analysis_type, project.element_type,
        )
        dofs = elem.get_dof_indices(project)
        ke_ref[eid] = ke
        for i, gi in enumerate(dofs):
            for j, gj in enumerate(dofs):
                rows.append(gi)
                cols.append(gj)
                data.append(ke[i, j])

        b_fn = _body_force(project, mat, body_force_fn)
        if b_fn is not None:
            # fe = sum_gp N^T b |det J| t w, punto a punto.
            fe = np.zeros(len(dofs))
            for gd in gauss_data:
                N = N_func(gd["xi"], gd["eta"])
                x = float(N @ coords[:, 0])
                y = float(N @ coords[:, 1])
                bx, by = b_fn(x, y)
                factor = abs(gd["det_J"]) * elem.thickness * gd["weight"]
                for k in range(len(N)):
                    fe[2 * k] += N[k] * bx * factor
                    fe[2 * k + 1] += N[k] * by * factor
            for i, gi in enumerate(dofs):
                F[gi] += fe[i]

    K = coo_matrix((data, (rows, cols)), shape=(n_dof, n_dof)).tocsr()

    for load in project.nodal_loads.values():
        idx = idx_map.get(load.node_id)
        if idx is None:
            continue
        F[2 * idx] += load.fx
        F[2 * idx + 1] += load.fy

    for sl in project.surface_loads:
        n_a = project.nodes[sl.node_start]
        n_b = project.nodes[sl.node_end]
        mid = None
        if project.element_type == ELEMENT_Q9:
            for e in project.elements.values():
                mid = find_edge_midnode(e, sl.node_start, sl.node_end)
                if mid is not None:
                    break
        if mid is not None:
            n_m = project.nodes[mid]
            forces = surface_load_to_nodal_forces_q9(
                (n_a.x, n_a.y), (n_m.x, n_m.y), (n_b.x, n_b.y),
                sl.q_start, sl.q_end, sl.angle,
            )
            targets = (sl.node_start, mid, sl.node_end)
        else:
            forces = surface_load_to_nodal_forces(
                (n_a.x, n_a.y), (n_b.x, n_b.y), sl.q_start, sl.q_end, sl.angle,
            )
            targets = (sl.node_start, sl.node_end)
        for nid, (fx, fy) in zip(targets, forces):
            F[2 * idx_map[nid]] += fx
            F[2 * idx_map[nid] + 1] += fy

    return K, F, ke_ref


def _reference_solve(project, K, F):
    restrained = project.get_restrained_dofs()
    u_pre = project.get_prescribed_displacement_vector()
    K_red, F_red, free = apply_boundary_conditions(K, F, restrained, u_pre)
    u = np.zeros(project.total_dof)
    u[np.asarray(free, dtype=np.intp)] = spsolve(K_red.tocsc(), F_red)
    if u_pre is not None and restrained:
        rest = np.asarray(restrained, dtype=np.intp)
        u[rest] = u_pre[rest]
    return u


def _reference_stresses(project, u):
    """sigma en Gauss con `compute_element_stresses`, extrapolacion nodal y
    promedio con acumuladores explicitos.

    Solo se promedian las 3 componentes cartesianas; sigma_1, sigma_2 y VM
    del nodo promedio salen de `principal_and_vm` (escalar, punto a punto)
    aplicada a ese promedio."""
    idx_map = project.node_index_map
    n = len(idx_map)
    accum = np.zeros((n, 3))
    count = np.zeros(n, dtype=int)
    gauss_ref, nodal_ref = {}, {}
    for eid, elem in project.elements.items():
        coords = _node_coords(project, elem)
        mat = _material(project, elem)
        dofs = elem.get_dof_indices(project)
        gs = compute_element_stresses(
            coords, u[dofs], mat.E, mat.nu, elem.thickness,
            project.analysis_type, project.element_type,
        )
        ns = (extrapolate_to_nodes_q4(gs) if elem.num_nodes == 4
              else extrapolate_to_nodes_q9(gs))
        gauss_ref[eid] = np.array([[g[k] for k in _STRESS_KEYS] for g in gs])
        nodal_ref[eid] = np.array([[d[k] for k in _STRESS_KEYS] for d in ns])
        for i, nid in enumerate(elem.node_ids[:len(ns)]):
            accum[idx_map[nid]] += nodal_ref[eid][i, :3]
            count[idx_map[nid]] += 1
    comp = accum / np.maximum(count, 1)[:, None]
    avg = np.array([[sx, sy, txy, *principal_and_vm(sx, sy, txy)]
                    for sx, sy, txy in comp])
    return gauss_ref, nodal_ref, avg, count


# ─── Comparacion ────────────────────────────────────────────────────────────

def _check(label, diff, scale):
    tol = REL_TOL * max(float(scale), 1e-300)
    ok = float(diff) <= tol
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: max|delta| = {float(diff):.2e}"
          f"  (tol {tol:.1e})")
    return label, ok


def _run_case(name, project, body_force_fn):
    print("=" * 66)
    print(f"  {name}  ({project.num_elements} elementos, {project.total_dof} GDL)")
    print("=" * 66)
    K_ref, F_ref, ke_ref = _reference_system(project, body_force_fn)
    u_ref = _reference_solve(project, K_ref, F_ref)
    rest = np.asarray(project.get_restrained_dofs(), dtype=np.intp)
    R_ref = np.zeros_like(u_ref)
    R_ref[rest] = np.asarray(K_ref[rest, :] @ u_ref).ravel() - F_ref[rest]
    gauss_ref, nodal_ref, avg_ref, count = _reference_stresses(project, u_ref)

    sol = solve_system(project, body_force_fn=body_force_fn)
    es, ns = compute_all_stresses(project, sol)
    edata = sol["element_data"]
    eids = list(project.elements)

    checks = [
        _check(f"{name} | K", abs(K_ref - sol["K"]).max(), abs(K_ref).max()),
        _check(f"{name} | F", np.abs(F_ref - sol["F"]).max(), np.abs(F_ref).max()),
        _check(f"{name} | ke por elemento",
               max(np.abs(ke_ref[e] - np.asarray(edata[e]["ke"])).max() for e in eids),
               max(np.abs(ke_ref[e]).max() for e in eids)),
        _check(f"{name} | u", np.abs(u_ref - sol["u"]).max(), np.abs(u_ref).max()),
        _check(f"{name} | reacciones", np.abs(R_ref - sol["reactions"]).max(),
               np.abs(R_ref).max()),
    ]

    g_new = np.array([[[g[k] for k in _STRESS_KEYS]
                       for g in es[e]["gauss_stresses"]] for e in eids])
    g_ref = np.array([gauss_ref[e] for e in eids])
    checks.append(_check(f"{name} | sigma en puntos de Gauss",
                         np.abs(g_new - g_ref).max(), np.abs(g_ref).max()))
    n_new = np.array([[[d[k] for k in _STRESS_KEYS]
                       for d in es[e]["nodal_stresses"]] for e in eids])
    n_ref = np.array([nodal_ref[e] for e in eids])
    checks.append(_check(f"{name} | sigma extrapolada a nodos",
                         np.abs(n_new - n_ref).max(), np.abs(n_ref).max()))
    idx_map = project.node_index_map
    ids_new = sorted(ns)
    ids_ref = sorted(nid for nid, i in idx_map.items() if count[i] > 0)
    same_ids = ids_new == ids_ref
    print(f"  [{'OK' if same_ids else 'FAIL'}] {name} | conjunto de nodos promediados")
    checks.append((f"{name} | conjunto de nodos promediados", same_ids))
    if same_ids:
        a_new = np.array([[ns[nid][k] for k in _STRESS_KEYS] for nid in ids_new])
        a_ref = np.array([avg_ref[idx_map[nid]] for nid in ids_new])
        checks.append(_check(f"{name} | sigma nodal promedio",
                             np.abs(a_new - a_ref).max(), np.abs(a_ref).max()))
    return checks


def main():
    checks = []
    for name, project, bf in _cases():
        checks += _run_case(name, project, bf)
        print()
    failed = [label for label, ok in checks if not ok]
    print("=" * 66)
    print(f"  Resumen: {len(checks) - len(failed)}/{len(checks)} checks OK"
          f"  (tolerancia relativa {REL_TOL:.0e})")
    print("=" * 66)
    if failed:
        print("FALLOS:")
        for label in failed:
            print(f"  [FAIL] {label}")
        sys.exit(1)
    print("Test completado exitosamente.")


if __name__ == "__main__":
    main()
