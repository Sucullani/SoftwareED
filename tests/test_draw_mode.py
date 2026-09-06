"""
Tests del modo dibujo de elementos (gui/preprocessing/mesh_canvas.py).

No abre Tk: testea solo la logica pura del commit del modo dibujo
(shoelace para auto-CCW + creacion atomica de nodos faltantes + reuso
de nodos snapped + auto-expand Q9 al final).

Cubre:
- Shoelace: signo positivo CCW, negativo CW (segun convencion del proyecto)
- Commit con todos los puntos nuevos -> 4 nodos + 1 elemento
- Commit con snap a 2 nodos existentes -> reusa, solo crea 2 nodos nuevos
- Commit en orden CW -> auto-revierte a CCW antes de crear el elemento
- Commit en proyecto Q9 -> auto-expand genera mid-nodes y centroide
- Snap entre 2 elementos: nodo compartido se reusa correctamente
- Parser de tokens AutoCAD-style (`#`/`@`, vacio, ValueError)
- Proyeccion ortho a eje H/V dominante
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from models.project import ProjectModel
from models.material import Material
from models.mesh_utils import auto_expand_if_q9
import config.settings as cfg

# MeshCanvas arrastra tkinter. La logica que se testea aca es pura
# (shoelace + snap + commit), asi que en un entorno headless se omiten solo
# los checks que necesitan el canvas en vez de abortar el modulo entero.
try:
    from gui.preprocessing.mesh_canvas import MeshCanvas
    HAS_TK = True
except Exception as _exc:  # ImportError o TclError sin display
    MeshCanvas = None
    HAS_TK = False
    print(f"[SKIP] MeshCanvas no disponible ({_exc}); "
          f"se corren solo los checks de logica pura.")


def _new_project():
    p = ProjectModel()
    p.materials["acero"] = Material("acero", 200000, 0.3)
    return p


def _commit_simulation(project, pending):
    """Replica la logica de MeshCanvas._draw_commit() sin Tk:
    1) resolver coords (snap lee del nodo existente),
    2) auto-CCW via shoelace,
    3) crear nodos faltantes (snap reusa),
    4) crear elemento,
    5) auto-expand Q9 si aplica.
    Retorna (elem_id, cw_corrected)."""
    # Resolver coords (mismo paso que _draw_add_pending hace al snapear)
    resolved = []
    for (snapped_nid, x, y) in pending:
        if snapped_nid is not None:
            node = project.nodes[snapped_nid]
            resolved.append((snapped_nid, node.x, node.y))
        else:
            resolved.append((None, x, y))
    # Auto-CCW
    pts = [(x, y) for (_nid, x, y) in resolved]
    signed = MeshCanvas._shoelace_signed(pts)
    cw_corrected = signed < 0
    if cw_corrected:
        resolved = list(reversed(resolved))
    # Crear nodos faltantes
    final_ids = []
    for (snapped_nid, x, y) in resolved:
        if snapped_nid is not None:
            final_ids.append(snapped_nid)
        else:
            new_node = project.add_node(x, y)
            final_ids.append(new_node.id)
    mat = list(project.materials.keys())[0]
    elem = project.add_element(final_ids, project.default_thickness, mat)
    auto_expand_if_q9(project)
    return elem.id, cw_corrected


def test_shoelace_ccw_positive():
    # Cuadrado unitario CCW
    pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
    s = MeshCanvas._shoelace_signed(pts)
    assert s > 0, f"CCW debe dar signo positivo, dio {s}"
    # Mismo cuadrado CW (orden invertido)
    pts_cw = [(0, 0), (0, 1), (1, 1), (1, 0)]
    s_cw = MeshCanvas._shoelace_signed(pts_cw)
    assert s_cw < 0, f"CW debe dar signo negativo, dio {s_cw}"
    print("[OK] shoelace_ccw_positive: signo coherente con convencion CCW")


def test_commit_all_new_nodes():
    p = _new_project()
    # 4 puntos nuevos en orden CCW
    pending = [
        (None, 0.0, 0.0),
        (None, 1.0, 0.0),
        (None, 1.0, 1.0),
        (None, 0.0, 1.0),
    ]
    elem_id, cw = _commit_simulation(p, pending)
    assert cw is False
    assert sorted(p.nodes.keys()) == [1, 2, 3, 4]
    assert p.elements[elem_id].node_ids == [1, 2, 3, 4]
    print("[OK] commit_all_new_nodes: 4 nodos + 1 elemento, sin reverso")


def test_commit_with_snap_reuses_existing():
    p = _new_project()
    # Pre-crear 2 nodos
    p.add_node(0.0, 0.0, 1)
    p.add_node(1.0, 0.0, 2)
    # Pending: snap a 1 y 2, luego 2 nuevos
    pending = [
        (1, None, None),     # snap a nodo 1
        (2, None, None),     # snap a nodo 2
        (None, 1.0, 1.0),    # nuevo
        (None, 0.0, 1.0),    # nuevo
    ]
    elem_id, cw = _commit_simulation(p, pending)
    assert cw is False
    # Solo 2 nodos nuevos, total 4
    assert len(p.nodes) == 4
    elem = p.elements[elem_id]
    assert elem.node_ids[0] == 1  # reuso
    assert elem.node_ids[1] == 2  # reuso
    print("[OK] commit_with_snap_reuses_existing: snap evita duplicar nodos")


def test_commit_cw_auto_corrects_to_ccw():
    p = _new_project()
    # Mismo cuadrado pero en orden CW
    pending = [
        (None, 0.0, 0.0),
        (None, 0.0, 1.0),
        (None, 1.0, 1.0),
        (None, 1.0, 0.0),
    ]
    elem_id, cw = _commit_simulation(p, pending)
    assert cw is True, "Debio detectarse CW y revertir"
    elem = p.elements[elem_id]
    # El elemento queda en CCW: nodos en orden inverso al input.
    # Verificamos via shoelace de las coords finales del elemento.
    coords = [(p.nodes[nid].x, p.nodes[nid].y) for nid in elem.node_ids]
    assert MeshCanvas._shoelace_signed(coords) > 0, \
        "Elemento creado quedo CW tras la 'correccion'"
    print("[OK] commit_cw_auto_corrects: orden CW se invierte a CCW")


def test_commit_q9_triggers_auto_expand():
    p = _new_project()
    p.element_type = cfg.ELEMENT_Q9
    pending = [
        (None, 0.0, 0.0),
        (None, 1.0, 0.0),
        (None, 1.0, 1.0),
        (None, 0.0, 1.0),
    ]
    elem_id, _ = _commit_simulation(p, pending)
    elem = p.elements[elem_id]
    assert elem.num_nodes == 9, f"Q9 debe tener 9 nodos, tiene {elem.num_nodes}"
    assert len(elem.node_ids) == 9
    assert len(p.nodes) == 9  # 4 corners + 4 mids + 1 center
    print("[OK] commit_q9_auto_expand: corners se expanden a Q9 completo")


def test_two_adjacent_elements_share_snap():
    p = _new_project()
    # Crear primer elemento: cuadrado izquierdo
    pending1 = [
        (None, 0.0, 0.0),
        (None, 1.0, 0.0),
        (None, 1.0, 1.0),
        (None, 0.0, 1.0),
    ]
    e1_id, _ = _commit_simulation(p, pending1)
    # Segundo elemento: cuadrado derecho que comparte arista 2-3 (nodos 2, 3)
    pending2 = [
        (2, None, None),     # snap a nodo 2 del primer elemento
        (None, 2.0, 0.0),    # nuevo
        (None, 2.0, 1.0),    # nuevo
        (3, None, None),     # snap a nodo 3 del primer elemento
    ]
    e2_id, _ = _commit_simulation(p, pending2)
    # Verificar que comparten nodos 2 y 3
    e1_nodes = set(p.elements[e1_id].node_ids)
    e2_nodes = set(p.elements[e2_id].node_ids)
    shared = e1_nodes & e2_nodes
    assert 2 in shared and 3 in shared
    # Solo se crearon 2 nodos nuevos (5, 6)
    assert sorted(p.nodes.keys()) == [1, 2, 3, 4, 5, 6]
    print("[OK] two_adjacent_elements_share_snap: snap conecta vecinos sin duplicar")


def test_parse_coord_token_relativo_default():
    # Sin prefijo, con last_value: relativo
    val, was_abs = MeshCanvas._parse_coord_token("100", 50.0)
    assert val == 150.0 and was_abs is False, f"got ({val}, {was_abs})"
    print("[OK] parse_coord_token: '100' relativo aplica al last_value")


def test_parse_coord_token_absoluto_override():
    # Prefijo `#`: absoluto, ignora last_value
    val, was_abs = MeshCanvas._parse_coord_token("#150", 50.0)
    assert val == 150.0 and was_abs is True, f"got ({val}, {was_abs})"
    # Negativo
    val, was_abs = MeshCanvas._parse_coord_token("#-25", 100.0)
    assert val == -25.0 and was_abs is True
    print("[OK] parse_coord_token: '#150' fuerza absoluto, ignora last_value")


def test_parse_coord_token_arroba_no_op():
    # Prefijo `@`: relativo (no-op tolerado)
    val, was_abs = MeshCanvas._parse_coord_token("@30", 10.0)
    assert val == 40.0 and was_abs is False, f"got ({val}, {was_abs})"
    # Equivalente a sin prefijo
    val_sin, _ = MeshCanvas._parse_coord_token("30", 10.0)
    assert val == val_sin, "@30 debe ser identico a 30 (mismo last_value)"
    print("[OK] parse_coord_token: '@30' es identico a '30' (no-op tolerado)")


def test_parse_coord_token_vacio_sentinela():
    # Vacio: retorna (None, False) para que el caller use el cursor
    val, was_abs = MeshCanvas._parse_coord_token("", 50.0)
    assert val is None and was_abs is False
    val, was_abs = MeshCanvas._parse_coord_token("   ", 50.0)
    assert val is None
    print("[OK] parse_coord_token: vacio = sentinela None (fallback a cursor)")


def test_parse_coord_token_primer_punto_absoluto():
    # last_value=None significa 1er punto, sin prefijo se interpreta absoluto
    val, was_abs = MeshCanvas._parse_coord_token("100", None)
    assert val == 100.0 and was_abs is False
    # @ con last_value None -> tratado absoluto (no tiene sentido relativo)
    val, was_abs = MeshCanvas._parse_coord_token("@50", None)
    assert val == 50.0
    print("[OK] parse_coord_token: 1er punto (last_value=None) absoluto por default")


def test_parse_coord_token_valueerror():
    # Texto invalido lanza ValueError (el caller lo captura y muestra status)
    raised = False
    try:
        MeshCanvas._parse_coord_token("abc", 0.0)
    except ValueError:
        raised = True
    assert raised, "Texto no numerico debe lanzar ValueError"
    # Coma como decimal -> ValueError (ya no se tolera en draw entry)
    raised = False
    try:
        MeshCanvas._parse_coord_token("1,5", 0.0)
    except ValueError:
        raised = True
    assert raised, "Coma decimal debe lanzar ValueError (separador es punto)"
    print("[OK] parse_coord_token: texto invalido / coma decimal lanzan ValueError")


def test_parse_coord_token_whitespace():
    # Whitespace tolerado dentro y alrededor
    val, _ = MeshCanvas._parse_coord_token("  100  ", 0.0)
    assert val == 100.0
    val, was_abs = MeshCanvas._parse_coord_token("# 50", 0.0)
    assert val == 50.0 and was_abs is True
    print("[OK] parse_coord_token: whitespace tolerado")


def test_project_to_ortho_eje_dominante():
    # Eje X domina: cursor mas lejos en X que en Y
    px, py = MeshCanvas._project_to_ortho(0.0, 0.0, 10.0, 3.0)
    assert px == 10.0 and py == 0.0, f"got ({px}, {py})"
    # Eje Y domina
    px, py = MeshCanvas._project_to_ortho(0.0, 0.0, 2.0, 7.0)
    assert px == 0.0 and py == 7.0
    # Empate: gana X (>=)
    px, py = MeshCanvas._project_to_ortho(0.0, 0.0, 5.0, 5.0)
    assert px == 5.0 and py == 0.0
    # Direccion negativa preservada
    px, py = MeshCanvas._project_to_ortho(10.0, 5.0, -3.0, 4.0)
    # dx = -13, dy = -1 -> X domina
    assert px == -3.0 and py == 5.0
    print("[OK] project_to_ortho: eje dominante con signo correcto")


if __name__ == "__main__":
    test_shoelace_ccw_positive()
    test_commit_all_new_nodes()
    test_commit_with_snap_reuses_existing()
    test_commit_cw_auto_corrects_to_ccw()
    test_commit_q9_triggers_auto_expand()
    test_two_adjacent_elements_share_snap()
    test_parse_coord_token_relativo_default()
    test_parse_coord_token_absoluto_override()
    test_parse_coord_token_arroba_no_op()
    test_parse_coord_token_vacio_sentinela()
    test_parse_coord_token_primer_punto_absoluto()
    test_parse_coord_token_valueerror()
    test_parse_coord_token_whitespace()
    test_project_to_ortho_eje_dominante()
    print("\nTodos los tests del modo dibujo pasan.")
