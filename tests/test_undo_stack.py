"""
Test del UndoStack (models/undo_stack.py).

Cubre:
- capture / undo / redo basicos
- can_undo / can_redo
- Una nueva captura tras undo invalida el redo (estandar)
- max_depth (descarta el mas viejo al llenarse)
- clear vacia ambos stacks
- set_project reasigna y limpia
- Listener on_state_restored se dispara solo en undo/redo
- El project sigue siendo el MISMO objeto tras undo (id estable)
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from models.project import ProjectModel
from models.undo_stack import UndoStack


def test_capture_basic():
    p = ProjectModel()
    s = UndoStack(p)
    assert not s.can_undo()
    assert not s.can_redo()
    s.capture("primera accion")
    assert s.can_undo()
    assert not s.can_redo()
    print("[OK] capture_basic: estado inicial vacio, capture habilita undo")


def test_undo_redo_round_trip():
    p = ProjectModel()
    s = UndoStack(p)

    # Estado A: vacio
    s.capture("agregar nodo")
    p.add_node(1.0, 2.0)
    # Estado B: 1 nodo

    s.capture("agregar otro nodo")
    p.add_node(3.0, 4.0)
    # Estado C: 2 nodos

    assert len(p.nodes) == 2

    # Undo -> regresa a B
    label = s.undo()
    assert label == "agregar otro nodo"
    assert len(p.nodes) == 1
    assert s.can_undo() and s.can_redo()

    # Undo -> regresa a A
    s.undo()
    assert len(p.nodes) == 0
    assert not s.can_undo() and s.can_redo()

    # Redo -> vuelve a B
    s.redo()
    assert len(p.nodes) == 1

    # Redo -> vuelve a C
    s.redo()
    assert len(p.nodes) == 2
    assert s.can_undo() and not s.can_redo()
    print("[OK] undo_redo_round_trip: 2 capturas, undo*2, redo*2 vuelven al estado")


def test_new_capture_invalidates_redo():
    """Tras hacer undo, una nueva captura debe limpiar el redo stack."""
    p = ProjectModel()
    s = UndoStack(p)
    s.capture("a")
    p.add_node(1, 1)
    s.capture("b")
    p.add_node(2, 2)
    s.undo()
    assert s.can_redo()
    # Nueva accion -> redo invalidado
    s.capture("c")
    p.add_node(9, 9)
    assert not s.can_redo()
    print("[OK] new_capture_invalidates_redo: nueva accion limpia redo")


def test_max_depth():
    """Pushear mas alla de max_depth descarta el mas viejo silenciosamente."""
    p = ProjectModel()
    s = UndoStack(p, max_depth=3)
    for i in range(5):
        s.capture(f"accion {i}")
    # Solo 3 ultimas deben quedar
    undo_count, redo_count = s.depth()
    assert undo_count == 3, f"esperado 3, got {undo_count}"
    assert redo_count == 0
    print("[OK] max_depth: deque mantiene maximo configurado")


def test_clear():
    p = ProjectModel()
    s = UndoStack(p)
    s.capture("a")
    p.add_node(1, 1)
    s.capture("b")
    s.undo()
    assert s.can_undo() and s.can_redo()
    s.clear()
    assert not s.can_undo() and not s.can_redo()
    print("[OK] clear: vacia ambos stacks")


def test_set_project():
    p1 = ProjectModel()
    s = UndoStack(p1)
    s.capture("accion en p1")
    p2 = ProjectModel()
    s.set_project(p2)
    assert s.project is p2
    assert not s.can_undo() and not s.can_redo()
    print("[OK] set_project: reasigna y limpia historial")


def test_listener_on_undo_redo_only():
    """El listener `on_state_restored` se dispara en undo y redo, no en
    capture. Critico para que el UI no se refresque innecesariamente."""
    p = ProjectModel()
    s = UndoStack(p)
    calls = []
    s.on_state_restored.append(lambda: calls.append(True))

    s.capture("a")
    p.add_node(1, 1)
    assert len(calls) == 0, "listener NO debe disparar en capture"

    s.capture("b")
    p.add_node(2, 2)
    assert len(calls) == 0

    s.undo()
    assert len(calls) == 1, "listener debe disparar en undo"

    s.redo()
    assert len(calls) == 2, "listener debe disparar en redo"

    # undo sin nada en stack -> NO debe disparar listener
    s.undo()  # ahora stack esta en estado pre-A
    assert s.can_undo()  # aun queda 'a'
    s.undo()
    assert len(calls) == 4  # disparo dos veces mas
    s.undo()  # ahora ya no hay nada
    assert len(calls) == 4, "listener NO debe disparar en undo vacio"
    print("[OK] listener_on_undo_redo_only: listener solo en restores reales")


def test_project_identity_preserved():
    """El project sigue siendo el MISMO objeto tras undo/redo. Las
    referencias en main_window.project, pre_tab.project, etc. deben
    seguir validas sin reasignaciones."""
    p = ProjectModel()
    s = UndoStack(p)
    original_id = id(p)

    s.capture("a")
    p.add_node(1, 1)
    s.undo()
    assert id(s.project) == original_id, "id del project no debe cambiar"
    print("[OK] project_identity_preserved: same object reference tras undo")


def test_undo_restores_complex_state():
    """Undo restaura todas las colecciones, no solo nodos."""
    p = ProjectModel()
    s = UndoStack(p)

    p.add_node(0, 0)
    p.add_node(1, 0)
    p.add_node(1, 1)
    p.add_node(0, 1)
    s.capture("antes de agregar elemento + carga + bc")
    p.add_element([1, 2, 3, 4], 1.0)
    p.set_nodal_load(2, 100, 0)
    from models.boundary import BoundaryCondition
    p.boundary_conditions[1] = BoundaryCondition(1, True, True)

    assert len(p.elements) == 1
    assert len(p.nodal_loads) == 1
    assert len(p.boundary_conditions) == 1

    s.undo()
    assert len(p.elements) == 0
    assert len(p.nodal_loads) == 0
    assert len(p.boundary_conditions) == 0
    assert len(p.nodes) == 4  # los nodos siguen
    print("[OK] undo_restores_complex_state: elementos + cargas + BCs revertidos")


if __name__ == "__main__":
    test_capture_basic()
    test_undo_redo_round_trip()
    test_new_capture_invalidates_redo()
    test_max_depth()
    test_clear()
    test_set_project()
    test_listener_on_undo_redo_only()
    test_project_identity_preserved()
    test_undo_restores_complex_state()
    print()
    print("Todos los tests del UndoStack pasan.")
