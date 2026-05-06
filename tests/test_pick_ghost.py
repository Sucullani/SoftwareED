"""
Tests del sistema de fila fantasma (pick desde canvas) y de la
seleccion multiple bidireccional canvas <-> spreadsheet.

No abre Tk: testea solo la logica pura (filtros de set diff entre
selecciones y items existentes, y los flujos de `add_surface_load` /
`set_nodal_load` / `set_boundary_condition` que el commit del fantasma
invoca).
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from models.project import ProjectModel
from models.material import Material


def _new_project():
    p = ProjectModel()
    p.materials["acero"] = Material("acero", 200000, 0.3)
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_element([1, 2, 3, 4], 1.0, "acero")
    return p


def test_load_ghost_filters_existing():
    """Replica la logica de _get_pick_ghost_node_ids("load"): solo
    nodos sin carga aparecen como fantasma."""
    p = _new_project()
    p.set_nodal_load(1, 100, 0)  # nodo 1 ya tiene carga
    selected_nodes = {1, 2, 3}
    existing = set(p.nodal_loads.keys())
    ghosts = sorted(n for n in selected_nodes
                    if n in p.nodes and n not in existing)
    assert ghosts == [2, 3]
    print("[OK] load_ghost_filters_existing: nodos con carga ya creada se excluyen")


def test_constraint_ghost_filters_existing():
    p = _new_project()
    p.set_boundary_condition(1, True, True)  # ya empotrado
    selected_nodes = {1, 2, 3, 4}
    existing = set(p.boundary_conditions.keys())
    ghosts = sorted(n for n in selected_nodes
                    if n in p.nodes and n not in existing)
    assert ghosts == [2, 3, 4]
    print("[OK] constraint_ghost_filters_existing: nodos con BC ya creada se excluyen")


def test_surface_ghost_filters_existing():
    """Aristas con SurfaceLoad ya creada se excluyen del fantasma."""
    p = _new_project()
    p.add_surface_load(1, 2, 100, 100, 0)  # arista 1-2 ya tiene surface
    selected_edges = {
        frozenset({1, 2}),  # ya tiene
        frozenset({2, 3}),  # nueva
        frozenset({3, 4}),  # nueva
    }
    existing = {frozenset({sl.node_start, sl.node_end})
                for sl in p.surface_loads}
    ghosts = sorted(
        (e for e in selected_edges if e not in existing),
        key=lambda e: tuple(sorted(e)),
    )
    assert len(ghosts) == 2
    assert frozenset({2, 3}) in ghosts
    assert frozenset({3, 4}) in ghosts
    print("[OK] surface_ghost_filters_existing: aristas con surface ya creada se excluyen")


def test_commit_load_ghost_with_defaults():
    """El commit de un fantasma de carga crea NodalLoad(nid, 0, 0)."""
    p = _new_project()
    p.set_nodal_load(2, 0.0, 0.0)
    assert 2 in p.nodal_loads
    assert p.nodal_loads[2].fx == 0.0
    assert p.nodal_loads[2].fy == 0.0
    print("[OK] commit_load_ghost: NodalLoad creado con Fx=Fy=0 por default")


def test_commit_constraint_ghost_with_defaults():
    """El commit de un fantasma de restriccion crea BC empotrado."""
    p = _new_project()
    p.set_boundary_condition(2, True, True)
    assert 2 in p.boundary_conditions
    bc = p.boundary_conditions[2]
    assert bc.restrain_x is True
    assert bc.restrain_y is True
    print("[OK] commit_constraint_ghost: BC empotrado por default (rx=ry=True)")


def test_commit_surface_ghost_with_defaults():
    """El commit de un fantasma de surface crea SurfaceLoad con q=0."""
    p = _new_project()
    sl = p.add_surface_load(2, 3, 0.0, 0.0, 0.0)
    assert sl.q_start == 0.0
    assert sl.q_end == 0.0
    assert sl.angle == 0.0
    assert len(p.surface_loads) == 1
    print("[OK] commit_surface_ghost: SurfaceLoad creado con q=0, angle=0 por default")


def test_commit_all_loads_creates_n_items():
    """El commit masivo crea N cargas de una vez."""
    p = _new_project()
    nids = [1, 2, 3, 4]
    for nid in nids:
        p.set_nodal_load(nid, 0.0, 0.0)
    assert len(p.nodal_loads) == 4
    for nid in nids:
        assert nid in p.nodal_loads
    print("[OK] commit_all_loads: 4 cargas creadas en cascada con defaults")


def test_commit_all_constraints_creates_n_items():
    p = _new_project()
    nids = [1, 2, 3, 4]
    for nid in nids:
        p.set_boundary_condition(nid, True, True)
    assert len(p.boundary_conditions) == 4
    for nid in nids:
        assert p.boundary_conditions[nid].restrain_x
    print("[OK] commit_all_constraints: 4 BCs empotrados creados en cascada")


def test_commit_all_surfaces_creates_n_items():
    p = _new_project()
    edges = [(1, 2), (2, 3), (3, 4), (4, 1)]  # 4 aristas del cuadrado
    for n1, n2 in edges:
        p.add_surface_load(n1, n2, 0.0, 0.0, 0.0)
    assert len(p.surface_loads) == 4
    print("[OK] commit_all_surfaces: 4 cargas superficiales creadas en cascada")


def test_edge_frozenset_dedupe():
    """Aristas como frozenset se deduplican naturalmente: (1,2) y (2,1)
    son la misma. Importante para evitar duplicar surfaces al hacer
    multi-pick de aristas vecinas."""
    edge_a = frozenset({1, 2})
    edge_b = frozenset({2, 1})
    assert edge_a == edge_b
    s = {edge_a, edge_b}
    assert len(s) == 1
    print("[OK] edge_frozenset_dedupe: aristas (n1,n2) y (n2,n1) son la misma")


def test_shoelace_independent_of_order():
    """Para aristas, el orden de los nodos NO importa para identidad,
    pero SI importa para la direccion de la SurfaceLoad final. La
    convencion del proyecto: SurfaceLoad(n_start, n_end) define la
    direccion. El commit del fantasma usa sorted() para canonicalizar."""
    edge = frozenset({3, 1})
    n1, n2 = sorted(edge)
    assert n1 == 1 and n2 == 3
    print("[OK] shoelace_independent: sorted(edge) canonicaliza el orden")


if __name__ == "__main__":
    test_load_ghost_filters_existing()
    test_constraint_ghost_filters_existing()
    test_surface_ghost_filters_existing()
    test_commit_load_ghost_with_defaults()
    test_commit_constraint_ghost_with_defaults()
    test_commit_surface_ghost_with_defaults()
    test_commit_all_loads_creates_n_items()
    test_commit_all_constraints_creates_n_items()
    test_commit_all_surfaces_creates_n_items()
    test_edge_frozenset_dedupe()
    test_shoelace_independent_of_order()
    print("\nTodos los tests del pick-ghost pasan.")
