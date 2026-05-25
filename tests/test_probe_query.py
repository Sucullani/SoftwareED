"""
Tests de regresion para fem/probe_query.py.

Ejecutar:
    python -m tests.test_probe_query

Sin pytest -- estilo printout coherente con el resto de la suite.
"""

import sys
import numpy as np

from config.settings import (
    ELEMENT_Q4, ELEMENT_Q9, NUMERICAL_TOLERANCE,
)
from fem.solver import solve_system
from fem.stress import compute_all_stresses
from fem.probe_query import (
    inverse_iso_map_NR, compute_raw, compute_smooth,
    displacement_at, gauss_physical_coords,
)
from tests.example_data import load_example_project, load_example_project_q9


# ─── Helpers ──────────────────────────────────────────────────────────────

PASS = "  [OK] "
FAIL = "  [FAIL] "

_failures = 0


def assert_close(actual, expected, tol, label):
    """Helper: |actual - expected| < tol. Reporta y lleva el contador."""
    global _failures
    diff = abs(float(actual) - float(expected))
    if diff < tol:
        print(f"{PASS}{label}: {actual:.6e} ~ {expected:.6e} (diff {diff:.2e})")
    else:
        _failures += 1
        print(f"{FAIL}{label}: {actual:.6e} vs {expected:.6e} (diff {diff:.2e}, tol {tol:.2e})")


def assert_true(cond, label):
    global _failures
    if cond:
        print(f"{PASS}{label}")
    else:
        _failures += 1
        print(f"{FAIL}{label}")


def section(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


# ─── Test 1: Newton-Raphson sobre vertices del Q4 ─────────────────────────

def test_newton_on_vertices_q4():
    section("Test 1: inverse_iso_map_NR sobre vertices Q4 -> xi,eta = +-1")
    project = load_example_project()
    # Tomamos el elemento 1: nodos 1, 2, 5, 4 (esquinas: (0,0), (5,0), (7,4), (2,3))
    elem = project.elements[1]
    coords = np.array(
        [[project.nodes[nid].x, project.nodes[nid].y]
         for nid in elem.node_ids],
        dtype=float,
    )

    expected = [(-1.0, -1.0), (+1.0, -1.0), (+1.0, +1.0), (-1.0, +1.0)]
    for i, (xi_exp, eta_exp) in enumerate(expected):
        x, y = coords[i]
        sol = inverse_iso_map_NR(x, y, coords, ELEMENT_Q4)
        assert_true(sol is not None,
                    f"  vertice N{elem.node_ids[i]} = ({x},{y}) converge")
        if sol is None:
            continue
        xi, eta = sol
        assert_close(xi, xi_exp, 1e-9, f"  xi en vertice N{elem.node_ids[i]}")
        assert_close(eta, eta_exp, 1e-9, f"  eta en vertice N{elem.node_ids[i]}")


# ─── Test 2: Newton fuera del elemento devuelve None ──────────────────────

def test_newton_outside_returns_none():
    section("Test 2: inverse_iso_map_NR para punto fuera -> None")
    project = load_example_project()
    elem = project.elements[1]
    coords = np.array(
        [[project.nodes[nid].x, project.nodes[nid].y]
         for nid in elem.node_ids],
        dtype=float,
    )
    # Punto bien afuera del bounding box del elemento.
    sol = inverse_iso_map_NR(1000.0, 1000.0, coords, ELEMENT_Q4)
    assert_true(sol is None, "punto lejano (1000, 1000) -> None")


# ─── Test 3: compute_raw en Gauss == valor oficial del solver ─────────────

def test_compute_raw_on_gauss_q4():
    section("Test 3: compute_raw en puntos de Gauss == valor oficial (Q4)")
    project = load_example_project(P=1000.0)
    solution = solve_system(project)
    element_stresses, _ = compute_all_stresses(project, solution)

    # Iteramos sobre todos los elementos y todos los Gauss
    for elem_id, data in element_stresses.items():
        for gp_idx, gp in enumerate(data["gauss_stresses"]):
            xi, eta = float(gp["xi"]), float(gp["eta"])
            result = compute_raw(project, solution, elem_id, xi, eta)
            assert_true(result is not None,
                        f"  elem {elem_id} PG#{gp_idx}: compute_raw retorna dato")
            if result is None:
                continue
            assert_close(result["sigma_x"], gp["sigma_x"], 1e-7,
                         f"  elem {elem_id} PG#{gp_idx} sigma_x")
            assert_close(result["sigma_y"], gp["sigma_y"], 1e-7,
                         f"  elem {elem_id} PG#{gp_idx} sigma_y")
            assert_close(result["tau_xy"], gp["tau_xy"], 1e-7,
                         f"  elem {elem_id} PG#{gp_idx} tau_xy")
            assert_close(result["von_mises"], gp["von_mises"], 1e-6,
                         f"  elem {elem_id} PG#{gp_idx} VM")


# ─── Test 4: compute_smooth en nodo == valor nodal promediado ─────────────

def test_compute_smooth_on_nodes_q4():
    section("Test 4: compute_smooth en nodo == nodal_avg_stresses[nodo] (Q4)")
    project = load_example_project(P=1000.0)
    solution = solve_system(project)
    _, nodal_avg = compute_all_stresses(project, solution)

    # Solo testeamos elementos donde TODOS los nodos del elemento
    # estan en nodal_avg (no compartidos con elementos faltantes).
    # En el ejemplo Q4 todos lo estan.
    # Coords de cada nodo del primer elemento, en coords naturales:
    elem = project.elements[1]
    nat_corners = [(-1.0, -1.0), (+1.0, -1.0), (+1.0, +1.0), (-1.0, +1.0)]
    for i, nid in enumerate(elem.node_ids):
        xi, eta = nat_corners[i]
        result = compute_smooth(project, solution, nodal_avg, 1, xi, eta)
        assert_true(result is not None,
                    f"  nodo {nid} (xi={xi}, eta={eta}): compute_smooth ok")
        if result is None:
            continue
        # Las shape functions cumplen N_i(node_j) = delta_ij, asi que
        # compute_smooth en el nodo recupera el valor nodal promediado.
        assert_close(result["sigma_x"], nodal_avg[nid]["sigma_x"], 1e-9,
                     f"  nodo {nid} sigma_x suavizado == avg")
        assert_close(result["sigma_y"], nodal_avg[nid]["sigma_y"], 1e-9,
                     f"  nodo {nid} sigma_y suavizado == avg")


# ─── Test 5: displacement_at en nodo == solution[dof] ─────────────────────

def test_displacement_at_on_nodes():
    section("Test 5: displacement_at en nodo == solution['u'][dof_x/dof_y]")
    project = load_example_project(P=1000.0)
    solution = solve_system(project)

    elem = project.elements[1]
    nat_corners = [(-1.0, -1.0), (+1.0, -1.0), (+1.0, +1.0), (-1.0, +1.0)]
    for i, nid in enumerate(elem.node_ids):
        xi, eta = nat_corners[i]
        ux, uy = displacement_at(project, solution, 1, xi, eta)
        ux_exp = solution["u"][project.dof_x(nid)]
        uy_exp = solution["u"][project.dof_y(nid)]
        assert_close(ux, ux_exp, 1e-12, f"  nodo {nid} ux interpolado")
        assert_close(uy, uy_exp, 1e-12, f"  nodo {nid} uy interpolado")


# ─── Test 6: Q9 -- repetir 3 y 4 ─────────────────────────────────────────

def test_q9_gauss_and_nodes():
    section("Test 6: Q9 -- compute_raw en Gauss y compute_smooth en nodos")
    project = load_example_project_q9(P=1000.0)
    solution = solve_system(project)
    element_stresses, nodal_avg = compute_all_stresses(project, solution)

    # 3a: compute_raw en algunos Gauss del primer elemento
    elem_id = next(iter(project.elements.keys()))
    data = element_stresses[elem_id]
    # Tomamos solo el primer y ultimo Gauss para no saturar el output
    for gp_idx in (0, len(data["gauss_stresses"]) - 1):
        gp = data["gauss_stresses"][gp_idx]
        xi, eta = float(gp["xi"]), float(gp["eta"])
        result = compute_raw(project, solution, elem_id, xi, eta)
        assert_close(result["sigma_x"], gp["sigma_x"], 1e-6,
                     f"  Q9 elem {elem_id} PG#{gp_idx} sigma_x")
        assert_close(result["von_mises"], gp["von_mises"], 1e-5,
                     f"  Q9 elem {elem_id} PG#{gp_idx} VM")

    # 6b: compute_smooth en los 4 nodos esquina del primer elemento (los
    # mid/center pueden tener nodal_stresses no calculados segun la
    # implementacion -- los corners siempre estan).
    elem = project.elements[elem_id]
    nat_corners = [(-1.0, -1.0), (+1.0, -1.0), (+1.0, +1.0), (-1.0, +1.0)]
    for i in range(4):
        xi, eta = nat_corners[i]
        nid = elem.node_ids[i]
        result = compute_smooth(project, solution, nodal_avg, elem_id, xi, eta)
        if result is None or nid not in nodal_avg:
            continue
        assert_close(result["sigma_x"], nodal_avg[nid]["sigma_x"], 1e-8,
                     f"  Q9 nodo esquina {nid} sigma_x suavizado")


# ─── Test 7: gauss_physical_coords devuelve coords y valores ──────────────

def test_gauss_physical_coords():
    section("Test 7: gauss_physical_coords (Q4) -- coords y valores oficiales")
    project = load_example_project(P=1000.0)
    solution = solve_system(project)
    element_stresses, _ = compute_all_stresses(project, solution)

    elem_id = 1
    gp_list = gauss_physical_coords(project, elem_id, element_stresses)
    assert_true(len(gp_list) == 4, "Q4 -> 4 puntos de Gauss")

    # Todos los Gauss deben caer dentro del bounding box del elemento.
    elem = project.elements[elem_id]
    coords = np.array(
        [[project.nodes[nid].x, project.nodes[nid].y]
         for nid in elem.node_ids],
        dtype=float,
    )
    xmin, xmax = coords[:, 0].min(), coords[:, 0].max()
    ymin, ymax = coords[:, 1].min(), coords[:, 1].max()
    for gp in gp_list:
        assert_true(xmin <= gp["x"] <= xmax,
                    f"  PG#{gp['gp_idx']} x dentro de [{xmin}, {xmax}]")
        assert_true(ymin <= gp["y"] <= ymax,
                    f"  PG#{gp['gp_idx']} y dentro de [{ymin}, {ymax}]")


# ─── Test 8: IDs no contiguos (regresion del bug 2*(nid-1)) ──────────────

def test_noncontiguous_ids():
    section("Test 8: IDs no contiguos -- compute_raw via get_dof_indices")
    project = load_example_project(P=1000.0)
    # Borrado de un nodo sin cascade (mas sencillo: este nodo no
    # esta en ningun elemento)... aqui todos los nodos del ejemplo
    # estan en algun elemento, asi que renumeramos para crear un gap.
    # En vez de borrar nodos, renombramos: nodo 5 -> 50.
    project.change_node_id(5, 50)

    solution = solve_system(project)
    element_stresses, _ = compute_all_stresses(project, solution)

    # Compute_raw debe funcionar en cualquier Gauss tras el renombrado.
    elem_id = 1  # contiene nodo 50 ahora
    data = element_stresses[elem_id]
    gp = data["gauss_stresses"][0]
    xi, eta = float(gp["xi"]), float(gp["eta"])
    result = compute_raw(project, solution, elem_id, xi, eta)
    assert_true(result is not None,
                "  IDs no contiguos: compute_raw retorna valor (no IndexError)")
    if result is not None:
        assert_close(result["sigma_x"], gp["sigma_x"], 1e-7,
                     "  sigma_x coincide con valor oficial tras rename")


# ─── Runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("test_probe_query.py -- regresion fem/probe_query.py")
    print("=" * 70)

    test_newton_on_vertices_q4()
    test_newton_outside_returns_none()
    test_compute_raw_on_gauss_q4()
    test_compute_smooth_on_nodes_q4()
    test_displacement_at_on_nodes()
    test_q9_gauss_and_nodes()
    test_gauss_physical_coords()
    test_noncontiguous_ids()

    print(f"\n{'=' * 70}")
    if _failures == 0:
        print("[OK] Todos los tests pasaron")
        sys.exit(0)
    else:
        print(f"[FAIL] {_failures} verificacion(es) fallaron")
        sys.exit(1)
