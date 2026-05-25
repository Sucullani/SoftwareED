"""
Test de round-trip ProjectModel.to_dict / from_dict.

Valida que serializar y deserializar un modelo no trivial reproduce el
estado exactamente. Sustento del UndoStack: si este round-trip falla,
undo/redo daria estados corruptos.
"""

import sys
import io

# Forzar UTF-8 en stdout para imprimir simbolos OK/FAIL en consola
# Windows cp1252 sin tirar UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from models.project import ProjectModel
from models.material import Material
from models.boundary import BoundaryCondition


def _build_complex_model():
    """Construye un modelo con todas las colecciones pobladas."""
    p = ProjectModel()
    # Geometria: 2 elementos Q4 vecinos compartiendo arista
    for i, (x, y) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1),
                                (2, 0), (2, 1)]):
        p.add_node(x, y)
    p.materials["MaterialA"] = Material("MaterialA", 210000.0, 0.3, 7850.0)
    p.add_element([1, 2, 3, 4], thickness=0.5, material_name="MaterialA")
    p.add_element([2, 5, 6, 3], thickness=0.5, material_name="MaterialA")
    # Cargas y BCs
    p.set_nodal_load(2, fx=100.0, fy=-50.0)
    p.set_nodal_load(5, fx=200.0, fy=0.0)
    p.boundary_conditions[1] = BoundaryCondition(1, True, True)
    p.boundary_conditions[4] = BoundaryCondition(4, True, False)
    # Surface load
    p.add_surface_load(node_start=5, node_end=6, q_start=10.0, q_end=20.0,
                       angle=0.0)
    # Configuracion global
    p.analysis_type = "Tensión Plana"
    p.element_type = "Q4 - Cuadrilátero 4 nodos"
    p.gravity_x = 0.0
    p.gravity_y = -9.81
    p.include_gravity = True
    return p


def _projects_equal(p1, p2):
    """Compara dos ProjectModel campo por campo (lo relevante para
    serialization). Retorna (bool, motivo)."""
    if p1.analysis_type != p2.analysis_type:
        return False, f"analysis_type: {p1.analysis_type} != {p2.analysis_type}"
    if p1.element_type != p2.element_type:
        return False, f"element_type: {p1.element_type} != {p2.element_type}"
    if p1.unit_system != p2.unit_system:
        return False, f"unit_system: {p1.unit_system} != {p2.unit_system}"
    if p1.gravity_x != p2.gravity_x:
        return False, f"gravity_x: {p1.gravity_x} != {p2.gravity_x}"
    if p1.gravity_y != p2.gravity_y:
        return False, f"gravity_y: {p1.gravity_y} != {p2.gravity_y}"
    if p1.include_gravity != p2.include_gravity:
        return False, f"include_gravity: {p1.include_gravity} != {p2.include_gravity}"
    # Nodos
    if set(p1.nodes.keys()) != set(p2.nodes.keys()):
        return False, f"nodes keys: {set(p1.nodes.keys())} != {set(p2.nodes.keys())}"
    for nid in p1.nodes:
        n1, n2 = p1.nodes[nid], p2.nodes[nid]
        if (n1.x, n1.y) != (n2.x, n2.y):
            return False, f"node {nid}: coords differ"
    # Elementos
    if set(p1.elements.keys()) != set(p2.elements.keys()):
        return False, "elements keys differ"
    for eid in p1.elements:
        e1, e2 = p1.elements[eid], p2.elements[eid]
        if e1.node_ids != e2.node_ids:
            return False, f"elem {eid}: node_ids differ"
        if e1.thickness != e2.thickness:
            return False, f"elem {eid}: thickness differs"
        if e1.material_name != e2.material_name:
            return False, f"elem {eid}: material differs"
    # Materiales
    if set(p1.materials.keys()) != set(p2.materials.keys()):
        return False, "materials keys differ"
    for mname in p1.materials:
        m1, m2 = p1.materials[mname], p2.materials[mname]
        if (m1.E, m1.nu) != (m2.E, m2.nu):
            return False, f"material {mname}: E or nu differ"
    # Cargas nodales
    if set(p1.nodal_loads.keys()) != set(p2.nodal_loads.keys()):
        return False, "nodal_loads keys differ"
    for nid, l1 in p1.nodal_loads.items():
        l2 = p2.nodal_loads[nid]
        if (l1.fx, l1.fy) != (l2.fx, l2.fy):
            return False, f"load {nid}: components differ"
    # BCs
    if set(p1.boundary_conditions.keys()) != set(p2.boundary_conditions.keys()):
        return False, "boundary_conditions keys differ"
    for nid, b1 in p1.boundary_conditions.items():
        b2 = p2.boundary_conditions[nid]
        if (b1.restrain_x, b1.restrain_y) != (b2.restrain_x, b2.restrain_y):
            return False, f"bc {nid}: restraints differ"
    # Surface loads
    if len(p1.surface_loads) != len(p2.surface_loads):
        return False, "surface_loads count differs"
    for s1, s2 in zip(p1.surface_loads, p2.surface_loads):
        if ((s1.node_start, s1.node_end, s1.q_start, s1.q_end, s1.angle)
                != (s2.node_start, s2.node_end, s2.q_start, s2.q_end, s2.angle)):
            return False, "surface load fields differ"
    return True, ""


def test_round_trip():
    """to_dict -> from_dict reproduce el modelo identicamente."""
    original = _build_complex_model()
    snap = original.to_dict()
    restored = ProjectModel.from_dict(snap)
    ok, motivo = _projects_equal(original, restored)
    assert ok, f"Round-trip failed: {motivo}"
    print("[OK] round_trip: to_dict -> from_dict reproduce el modelo")


def test_round_trip_in_place():
    """Verifica que `restore_from_dict` muta el proyecto in-place y
    reproduce el snapshot exactamente. Critico para UndoStack: el listener
    espera que self.project siga siendo el MISMO objeto tras un undo/redo
    para que las referencias en pre_tab/canvas/post_tab sigan validas."""
    original = _build_complex_model()
    snap = original.to_dict()
    original_id = id(original)  # tracking del objeto

    # Mutar el original
    original.add_node(99.0, 99.0)
    original.set_nodal_load(2, 0, 0)

    # Restaurar in-place
    original.restore_from_dict(snap)

    # Verificar que sigue siendo el mismo objeto
    assert id(original) == original_id, \
        "restore_from_dict no puede crear nueva instancia"

    # Tras restore_from_dict, debe coincidir con el snapshot
    expected = ProjectModel.from_dict(snap)
    ok, motivo = _projects_equal(original, expected)
    assert ok, f"In-place restore failed: {motivo}"
    print("[OK] round_trip_in_place: restore_from_dict muta in-place "
          "y restaura el estado")


if __name__ == "__main__":
    test_round_trip()
    test_round_trip_in_place()
    print()
    print("Todos los tests de serializacion pasan.")
