"""
Test del cascade simetrico de borrado de nodo
(`ProjectModel.remove_node_with_cascade` y `preview_node_cascade`).

Casos cubiertos:
- A) Nodo aislado sin datos -> borrado limpio
- B) Nodo aislado con datos del usuario (carga / BC) -> borrado borra datos
- C) Nodo en 1 elemento sin nodos hermanos con datos -> elemento + nodos
     hermanos sin datos se eliminan
- D) Nodo en 1 elemento con un hermano con carga -> hermano se preserva
     como huerfano
- E) Vertice Q9 en 1 elemento -> elemento + 8 nodos auxiliares se eliminan
- F) Vertice Q9 entre 2 elementos vecinos -> mid-node compartido se
     preserva (sigue en el otro elemento)
- G) preview_node_cascade(...) reporta lo mismo que el cascade real,
     sin mutar nada
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from models.project import ProjectModel
from models.material import Material
from models.boundary import BoundaryCondition
from models.load import NodalLoad
from models.mesh_utils import expand_q4_to_q9
import config.settings as cfg


def _new_project_with_material():
    p = ProjectModel()
    p.materials["acero"] = Material("acero", 200000, 0.3)
    return p


def test_isolated_node_no_data():
    p = _new_project_with_material()
    p.add_node(0, 0, 1)
    p.add_node(5, 5, 2)
    result = p.remove_node_with_cascade(2)
    assert result["node_deleted"] is True
    assert result["elements_deleted"] == []
    assert result["nodes_deleted"] == [2]
    assert result["nodes_preserved"] == []
    assert sorted(p.nodes.keys()) == [1]
    print("[OK] A. nodo aislado sin datos: borrado limpio")


def test_isolated_node_with_user_data():
    p = _new_project_with_material()
    p.add_node(0, 0, 1)
    p.boundary_conditions[1] = BoundaryCondition(1, True, True)
    p.nodal_loads[1] = NodalLoad(1, 50.0, 0.0)
    result = p.remove_node_with_cascade(1)
    assert result["node_deleted"] is True
    assert 1 not in p.nodes
    assert 1 not in p.boundary_conditions
    assert 1 not in p.nodal_loads
    print("[OK] B. nodo aislado con datos: datos se borran junto con el nodo")


def test_node_in_one_element_no_sibling_data():
    p = _new_project_with_material()
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_element([1, 2, 3, 4], 1.0, "acero")
    result = p.remove_node_with_cascade(1)
    assert result["node_deleted"] is True
    assert result["elements_deleted"] == [1]
    assert sorted(result["nodes_deleted"]) == [1, 2, 3, 4]
    assert result["nodes_preserved"] == []
    assert p.nodes == {}
    assert p.elements == {}
    print("[OK] C. nodo en 1 elemento, hermanos sin datos: cascade total")


def test_node_in_one_element_with_sibling_data():
    p = _new_project_with_material()
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_element([1, 2, 3, 4], 1.0, "acero")
    p.nodal_loads[3] = NodalLoad(3, 100.0, 0.0)  # hermano con carga
    result = p.remove_node_with_cascade(1)
    assert result["node_deleted"] is True
    assert result["elements_deleted"] == [1]
    assert 3 not in result["nodes_deleted"]
    assert result["nodes_preserved"] == [3]
    assert sorted(p.nodes.keys()) == [3]
    assert 3 in p.nodal_loads  # carga preservada
    print("[OK] D. hermano con carga: preservado como huerfano")


def test_q9_vertex_single_element():
    p = _new_project_with_material()
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_element([1, 2, 3, 4], 1.0, "acero")
    p.element_type = cfg.ELEMENT_Q9
    expand_q4_to_q9(p)
    assert len(p.nodes) == 9
    result = p.remove_node_with_cascade(1)
    assert result["node_deleted"] is True
    assert result["elements_deleted"] == [1]
    assert len(result["nodes_deleted"]) == 9  # vertice + 8 auxiliares
    assert p.nodes == {}
    assert p.elements == {}
    print("[OK] E. vertice Q9 single elem: elemento + 8 auxiliares borrados")


def test_q9_vertex_shared_midnode_preserved():
    p = _new_project_with_material()
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_node(2, 0, 5); p.add_node(2, 1, 6)
    p.add_element([1, 2, 3, 4], 1.0, "acero")
    p.add_element([2, 5, 6, 3], 1.0, "acero")
    p.element_type = cfg.ELEMENT_Q9
    expand_q4_to_q9(p)
    nodes_before = sorted(p.nodes.keys())
    elem1_nodes = list(p.elements[1].node_ids)
    elem2_nodes = list(p.elements[2].node_ids)
    # mid-node compartido en arista 2-3 deberia estar en ambos
    shared_in_both = set(elem1_nodes) & set(elem2_nodes)
    # Borramos vertice 5 (solo en elem 2)
    result = p.remove_node_with_cascade(5)
    assert result["elements_deleted"] == [2]
    assert 1 in p.elements  # elem 1 intacto
    # Todos los nodos del elem 1 siguen en el modelo
    for nid in elem1_nodes:
        assert nid in p.nodes, f"nodo {nid} del elem 1 desaparecio"
    # Los compartidos en particular siguen
    for nid in shared_in_both:
        assert nid in p.nodes, f"mid-node compartido {nid} desaparecio"
    print("[OK] F. mid-node compartido entre 2 elementos: preservado")


def test_preview_matches_cascade():
    p = _new_project_with_material()
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_element([1, 2, 3, 4], 1.0, "acero")
    p.nodal_loads[3] = NodalLoad(3, 100.0, 0.0)
    nodes_snap = dict(p.nodes)
    elems_snap = {eid: list(e.node_ids) for eid, e in p.elements.items()}
    loads_snap = dict(p.nodal_loads)
    preview = p.preview_node_cascade(1)
    # preview no muta
    assert dict(p.nodes) == nodes_snap
    assert {eid: list(e.node_ids) for eid, e in p.elements.items()} == elems_snap
    assert dict(p.nodal_loads) == loads_snap
    # Verificar consistencia preview vs ejecucion real
    assert preview["elements_to_delete"] == [1]
    assert preview["nodes_to_delete"] == [2, 4]
    assert preview["nodes_to_preserve"] == [3]
    real = p.remove_node_with_cascade(1)
    assert real["elements_deleted"] == preview["elements_to_delete"]
    # nodes_deleted del cascade incluye al objetivo, preview no
    assert sorted(real["nodes_deleted"]) == [1] + preview["nodes_to_delete"]
    assert real["nodes_preserved"] == preview["nodes_to_preserve"]
    print("[OK] G. preview no muta y coincide con cascade")


def test_legacy_no_cleanup():
    """Con cleanup_orphans=False, debe comportarse como remove_node legacy:
    borra el nodo y refs directas, deja elementos con node_ids invalidos."""
    p = _new_project_with_material()
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_element([1, 2, 3, 4], 1.0, "acero")
    result = p.remove_node_with_cascade(1, cleanup_orphans=False)
    assert result["node_deleted"] is True
    assert result["elements_deleted"] == []
    assert 1 in p.elements[1].node_ids  # elemento queda con ref invalida
    assert 1 not in p.nodes
    print("[OK] legacy mode (cleanup_orphans=False): comportamiento clasico")


if __name__ == "__main__":
    test_isolated_node_no_data()
    test_isolated_node_with_user_data()
    test_node_in_one_element_no_sibling_data()
    test_node_in_one_element_with_sibling_data()
    test_q9_vertex_single_element()
    test_q9_vertex_shared_midnode_preserved()
    test_preview_matches_cascade()
    test_legacy_no_cleanup()
    print("\nTodos los tests del cascade de nodos pasan.")
