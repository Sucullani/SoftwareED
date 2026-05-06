"""
Smoke test del sistema de seleccion bidireccional canvas <-> spreadsheet.
Usa Tk con root.withdraw() para no abrir ventana visible.

Cubre:
- Seleccion multi en canvas via select_node(additive=True)
- Sincronizacion de highlighted_* singulares con sets selected_*
- replace_node_selection desde spreadsheet -> canvas
- Filas fantasma se generan al cambiar la seleccion
- Esc / clear_highlights vacia todos los sets
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import tkinter as tk
except ImportError:
    print("Tk no disponible — smoke test omitido")
    sys.exit(0)


def test_canvas_selection_flow():
    from gui.main_window import MainWindow
    from models.material import Material

    # MainWindow construye toda la GUI; root.withdraw evita que se vea.
    mw = MainWindow()
    mw.root.withdraw()
    p = mw.project
    p.materials["acero"] = Material("acero", 200000, 0.3)
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_element([1, 2, 3, 4], 1.0, "acero")
    canvas = mw.mesh_canvas
    mw.root.update_idletasks()

    # 1) Single select via select_node
    canvas.select_node(1, additive=False)
    assert canvas.selected_nodes == {1}
    assert canvas.highlighted_node == 1  # compat singular sincronizado
    print("[OK] single select: set y highlighted_node sincronizados")

    # 2) Ctrl+Click acumulativo (additive)
    canvas.select_node(2, additive=True)
    canvas.select_node(3, additive=True)
    assert canvas.selected_nodes == {1, 2, 3}
    assert canvas.highlighted_node is None  # >1 elementos -> None
    print("[OK] additive: 3 nodos en set, highlighted_node None (>1)")

    # 3) Toggle del mismo nodo lo quita
    canvas.select_node(2, additive=True)
    assert canvas.selected_nodes == {1, 3}
    print("[OK] toggle: el nodo se removio del set")

    # 4) Range select
    canvas.clear_highlights()
    canvas.select_node(1, additive=False)
    canvas.select_node(4, range_to=True)
    assert canvas.selected_nodes == {1, 2, 3, 4}
    print("[OK] range select: nodos 1..4 en set")

    # 5) Esc/clear_highlights vacia todo
    canvas.clear_highlights()
    sel = canvas.get_selection()
    assert all(len(v) == 0 for v in sel.values())
    assert canvas.highlighted_node is None
    print("[OK] clear_highlights: todos los sets vacios")

    # 6) Edge selection (aristas potenciales)
    edge = frozenset({1, 2})
    canvas.select_edge(edge, additive=False)
    assert canvas.selected_edges == {edge}
    print("[OK] edge select: arista en set")

    # 7) Bidireccional spreadsheet -> canvas via replace_node_selection
    canvas.replace_node_selection({1, 3})
    assert canvas.selected_nodes == {1, 3}
    print("[OK] replace_node_selection: bidireccional spreadsheet->canvas")

    # 8) Pick ghost: con seleccion {1, 2}, en sub-pestaña Cargas
    # aparece fantasma para 1 y 2 (ninguno tiene carga)
    canvas.replace_node_selection({1, 2})
    pre_tab = mw.pre_tab
    ghosts = pre_tab._get_pick_ghost_node_ids("load")
    assert ghosts == [1, 2]
    print("[OK] pick_ghost_load: 2 fantasmas para 2 nodos sin carga")

    # 9) Tras crear carga en nodo 1, solo queda fantasma para 2
    p.set_nodal_load(1, 50, 0)
    ghosts = pre_tab._get_pick_ghost_node_ids("load")
    assert ghosts == [2]
    print("[OK] pick_ghost filtrado: nodo con carga ya creada no aparece como fantasma")

    # 10) commit del fantasma crea la carga
    pre_tab._commit_load_ghost(2)
    assert 2 in p.nodal_loads
    assert p.nodal_loads[2].fx == 0.0
    # El nodo 2 se quito del set tras commit
    assert 2 not in canvas.selected_nodes
    print("[OK] commit_load_ghost: NodalLoad creada y nodo removido del set")

    # 11) Second click deselecciona: click en N3 (set vacio) -> {3}
    canvas.clear_highlights()
    canvas.select_node(3, additive=False)
    assert canvas.selected_nodes == {3}
    # Click otra vez en N3 -> deselecciona todo
    canvas.select_node(3, additive=False)
    assert canvas.selected_nodes == set()
    print("[OK] second_click deselecciona nodo single-selected")

    # 12) Second click NO deselecciona en multi-select: si hay {3, 4}
    # y click en N3 (sin Ctrl), reemplaza con {3} (collapse)
    canvas.select_node(3, additive=False)
    canvas.select_node(4, additive=True)
    assert canvas.selected_nodes == {3, 4}
    canvas.select_node(3, additive=False)
    assert canvas.selected_nodes == {3}  # collapse, no deselect
    # Y un nuevo click en N3 -> deselect total
    canvas.select_node(3, additive=False)
    assert canvas.selected_nodes == set()
    print("[OK] second_click en multi-select hace collapse, despues deselect")

    # 13) Second click en arista
    edge = frozenset({1, 2})
    canvas.select_edge(edge, additive=False)
    assert canvas.selected_edges == {edge}
    canvas.select_edge(edge, additive=False)
    assert canvas.selected_edges == set()
    print("[OK] second_click deselecciona arista single-selected")

    # 14) Click en zona vacia del canvas deselecciona. Simulamos
    # construyendo un Event con coordenadas alejadas de cualquier nodo.
    canvas.select_node(1, additive=False)
    canvas.select_node(2, additive=True)
    assert canvas.selected_nodes == {1, 2}

    class _FakeEvent:
        def __init__(self, x, y, state=0):
            self.x = x; self.y = y; self.state = state

    # Las coords (5000, 5000) en pixeles del canvas estan lejos de los
    # nodos del modelo (que estan en ~[0, 1] en coords mundo, escalados).
    canvas._on_click(_FakeEvent(5000, 5000, state=0))
    assert canvas.selected_nodes == set(), \
        "click en vacio deberia deseleccionar"
    print("[OK] click_empty: click normal en zona vacia deselecciona todo")

    # 15) Ctrl+Click en vacio NO deselecciona (preserva)
    canvas.select_node(1, additive=False)
    canvas.select_node(2, additive=True)
    canvas._on_click(_FakeEvent(5000, 5000, state=0x0004))  # Ctrl
    assert canvas.selected_nodes == {1, 2}, \
        "Ctrl+Click en vacio debe preservar la seleccion"
    print("[OK] click_empty_with_ctrl: preserva la seleccion")

    # 16) Sync canvas -> spreadsheet via tag canvas_selected (no
    # selection_set). Seleccionar N3 en canvas debe agregar el tag
    # canvas_selected a la fila 3 del nodes_tree.
    canvas.replace_node_selection({3})
    mw.root.update_idletasks()  # forzar refresh del callback
    tags_3 = pre_tab.nodes_tree.item("3", "tags")
    assert "canvas_selected" in tags_3, \
        f"fila 3 deberia tener tag canvas_selected, tiene {tags_3}"
    # Y el set selection() del tree NO se modifica (sigue como estaba)
    print("[OK] sync_canvas_to_tree_via_tag: tag canvas_selected aplicado")

    # 17) Tras clear, el tag desaparece
    canvas.clear_highlights()
    mw.root.update_idletasks()
    tags_3 = pre_tab.nodes_tree.item("3", "tags")
    assert "canvas_selected" not in tags_3, \
        f"tag debe desaparecer tras clear, tiene {tags_3}"
    print("[OK] sync_canvas_to_tree_clear: tag se quita al limpiar seleccion")

    # 18b) Regresion: ghost commit en escenario multi-ghost preserva
    # el slot de la fantasma (no jump visual). Setup: seleccionar 3
    # nodos en canvas → 3 ghosts en loads_tree → commitear el del
    # medio → la fila real debe quedar en la posicion 2 (entre los
    # ghosts vecinos), no saltar al final del bloque "real".
    canvas.clear_highlights()
    # Estado limpio: borrar cargas pre-existentes y resetear visual_order.
    for nid in list(p.nodal_loads.keys()):
        p.remove_nodal_load(nid)
    pre_tab._loads_visual_order = []
    canvas.selected_nodes = {1, 2, 3}
    canvas._emit_selection_changed()
    mw.root.update_idletasks()
    children = pre_tab.loads_tree.get_children()
    ghost_iids = [c for c in children if c.startswith("__ghost__")]
    assert ghost_iids == ["__ghost__1", "__ghost__2", "__ghost__3"], \
        f"ghosts iniciales fuera de orden: {ghost_iids}"
    pos_ghost_2 = children.index("__ghost__2")
    pre_tab._commit_load_ghost(2)
    mw.root.update_idletasks()
    children_after = pre_tab.loads_tree.get_children()
    pos_real_2 = children_after.index("2")
    assert pos_real_2 == pos_ghost_2, (
        f"jump visual: ghost estaba en {pos_ghost_2}, "
        f"real quedo en {pos_real_2} (children: {children_after})")
    # Confirmar que ghosts vecinos siguen en sus slots originales.
    pos_ghost_1 = children_after.index("__ghost__1")
    pos_ghost_3 = children_after.index("__ghost__3")
    assert pos_ghost_1 == 0 and pos_ghost_3 == 2, \
        f"ghosts vecinos saltaron: 1→{pos_ghost_1}, 3→{pos_ghost_3}"
    print("[OK] ghost_commit_preserves_slot: real queda donde estaba el ghost")

    # 18) Regresion: cuando el sync va spreadsheet -> canvas (guard
    # `_syncing_to_canvas` activo), tags stale del estado anterior
    # deben limpiarse in-place SIN destruir la seleccion nativa Tk.
    # Setup: simular que la fila 1 quedo con tag canvas_selected (e.g.,
    # del estado anterior canvas->spreadsheet).
    canvas.replace_node_selection({1})
    mw.root.update_idletasks()
    assert "canvas_selected" in pre_tab.nodes_tree.item("1", "tags")

    # Ahora el usuario clickea fila 4 en spreadsheet (sin Ctrl). Esto
    # se simula seteando el guard y moviendo la seleccion del canvas
    # como hace _on_node_select.
    pre_tab._syncing_to_canvas = True
    try:
        canvas.replace_node_selection({4})
    finally:
        pre_tab._syncing_to_canvas = False
    mw.root.update_idletasks()
    # El tag stale en fila 1 debe haberse limpiado in-place.
    tags_1 = pre_tab.nodes_tree.item("1", "tags")
    tags_4 = pre_tab.nodes_tree.item("4", "tags")
    assert "canvas_selected" not in tags_1, \
        f"fila 1 (vieja) deberia perder tag stale, tiene {tags_1}"
    assert "canvas_selected" in tags_4, \
        f"fila 4 (nueva) deberia tener tag canvas_selected, tiene {tags_4}"
    print("[OK] sync_spreadsheet_to_canvas: tag stale se limpia in-place")

    mw.root.destroy()
    print("\nSmoke test de seleccion integrada: PASS")


if __name__ == "__main__":
    test_canvas_selection_flow()
