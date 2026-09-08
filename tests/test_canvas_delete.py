"""
Tests del borrado desde el canvas con multi-seleccion (`MeshCanvas._on_delete_key`
y sus helpers `_delete_selected_*`).

Sin display: se instancia el `MeshCanvas` con `object.__new__` y se le montan a
mano los atributos que la ruta de borrado toca (los seis sets de seleccion, el
project y un main_window de mentira). Asi se ejercita el codigo REAL —no una
copia— sin construir un widget Tk ni abrir ventana.

Regresiones que cubre:
  - Con >1 item seleccionado, Supr borra TODOS (antes leia `highlighted_*`,
    que vale None con multi-seleccion, y la tecla no hacia nada ni lo decia).
  - Un solo snapshot de undo por accion del usuario (regla dura 4).
  - Los sets de seleccion se sanean tras el borrado: sin eso quedaban ids
    muertos y, en cargas superficiales, un indice viejo que pasaba a apuntar
    a OTRA carga (y el canvas la resaltaba como seleccionada).
  - Orden de prioridad carga > restriccion > superficial > elemento > nodo.
  - Sin nada seleccionado, la tecla explica que falta en vez de callarse.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import tkinter                                   # noqa: F401
    from tkinter import messagebox
except ImportError:
    print("Tk no disponible — test omitido")
    sys.exit(0)

from gui.preprocessing.mesh_canvas import MeshCanvas
from models.material import Material
from models.project import ProjectModel


class _UndoStubStack:
    def __init__(self):
        self.labels = []

    def capture(self, label):
        self.labels.append(label)


class _MainWindowStub:
    def __init__(self):
        self.undo_stack = _UndoStubStack()
        self.status = []

    def set_status(self, msg):
        self.status.append(msg)


def _new_project():
    """Dos elementos Q4 lado a lado: nodos 1..6, elementos 1 y 2."""
    p = ProjectModel()
    p.materials["acero"] = Material("acero", 200000, 0.3)
    p.add_node(0, 0, 1); p.add_node(1, 0, 2); p.add_node(2, 0, 3)
    p.add_node(2, 1, 4); p.add_node(1, 1, 5); p.add_node(0, 1, 6)
    p.add_element([1, 2, 5, 6], 1.0, "acero", 1)
    p.add_element([2, 3, 4, 5], 1.0, "acero", 2)
    return p


def _new_canvas(project):
    """MeshCanvas sin Tk: solo el estado que la ruta de borrado consulta."""
    c = object.__new__(MeshCanvas)
    c.project = project
    c.main_window = _MainWindowStub()
    c.selected_nodes = set()
    c.selected_elements = set()
    c.selected_edges = set()
    c.selected_loads = set()
    c.selected_constraints = set()
    c.selected_surfaces = set()
    c._last_node_anchor = None
    c.highlighted_node = None
    c.highlighted_element = None
    c.highlighted_load = None
    c.highlighted_constraint = None
    c.highlighted_surface = None
    c.on_canvas_delete = None
    c.on_selection_changed = None
    c.draw_mode_active = False
    c.draw_pending = []
    c._draw_entry = None
    c.canvas = None                      # solo se pasa como parent del modal
    c.redraw = lambda: None              # no hay widget que redibujar
    return c


def _autoconfirm(value=True):
    """Reemplaza askyesno por una respuesta fija y devuelve el original."""
    original = messagebox.askyesno
    messagebox.askyesno = lambda *a, **k: value
    return original


def test_multi_delete_de_cargas():
    p = _new_project()
    p.set_nodal_load(1, 100, 0)
    p.set_nodal_load(2, 0, -50)
    p.set_nodal_load(3, 10, 10)
    c = _new_canvas(p)
    c.selected_loads = {1, 2, 3}
    c.selected_nodes = {1, 2, 3}

    c._on_delete_key()

    assert p.nodal_loads == {}, p.nodal_loads
    assert c.selected_loads == set()
    # Un solo snapshot para toda la accion (regla dura 4).
    assert len(c.main_window.undo_stack.labels) == 1
    assert "3" in c.main_window.undo_stack.labels[0]
    assert "3 cargas nodales eliminadas." in c.main_window.status
    print("[OK] Supr borra las 3 cargas seleccionadas con 1 snapshot de undo")


def test_multi_delete_de_restricciones():
    p = _new_project()
    p.set_boundary_condition(1, True, True)
    p.set_boundary_condition(6, True, True)
    c = _new_canvas(p)
    c.selected_constraints = {1, 6}
    c.selected_nodes = {1, 6}

    c._on_delete_key()

    assert p.boundary_conditions == {}
    assert c.selected_constraints == set()
    assert len(c.main_window.undo_stack.labels) == 1
    print("[OK] Supr borra las 2 restricciones seleccionadas")


def test_delete_de_superficial_no_deja_indice_stale():
    """Regresion: los indices de `selected_surfaces` son posicionales.

    Borrando la #0 de tres cargas, la que era #1 pasa a ser la #0. Si el set
    conservara el 0, el canvas resaltaria una carga que el alumno nunca
    selecciono. El set tiene que quedar vacio.
    """
    p = _new_project()
    p.add_surface_load(1, 2, 10.0, 10.0)
    p.add_surface_load(2, 3, 20.0, 20.0)
    p.add_surface_load(3, 4, 30.0, 30.0)
    c = _new_canvas(p)
    c.selected_surfaces = {0}

    c._on_delete_key()

    assert len(p.surface_loads) == 2
    assert [sl.q_start for sl in p.surface_loads] == [20.0, 30.0]
    assert c.selected_surfaces == set(), "indice stale tras el borrado"
    assert c.highlighted_surface is None
    print("[OK] borrar una carga superficial no deja indices stale")


def test_multi_delete_de_superficiales_de_atras_para_adelante():
    p = _new_project()
    p.add_surface_load(1, 2, 10.0, 10.0)
    p.add_surface_load(2, 3, 20.0, 20.0)
    p.add_surface_load(3, 4, 30.0, 30.0)
    c = _new_canvas(p)
    c.selected_surfaces = {0, 2}

    c._on_delete_key()

    # Si se borrara de menor a mayor, el segundo `del` sacaria la equivocada.
    assert [sl.q_start for sl in p.surface_loads] == [20.0]
    print("[OK] el borrado multiple de superficiales respeta los indices")


def test_multi_delete_de_elementos_con_cascada():
    p = _new_project()
    c = _new_canvas(p)
    c.selected_elements = {1, 2}
    original = _autoconfirm(True)
    try:
        c._on_delete_key()
    finally:
        messagebox.askyesno = original

    assert p.elements == {}
    # Los 6 nodos quedan sin referencias -> el auto-cleanup los borra.
    assert p.nodes == {}
    assert c.selected_elements == set()
    assert len(c.main_window.undo_stack.labels) == 1
    print("[OK] Supr borra los 2 elementos seleccionados y limpia el set")


def test_cancelar_el_modal_no_borra_nada():
    p = _new_project()
    c = _new_canvas(p)
    c.selected_elements = {1, 2}
    original = _autoconfirm(False)
    try:
        c._on_delete_key()
    finally:
        messagebox.askyesno = original

    assert set(p.elements) == {1, 2}
    assert c.selected_elements == {1, 2}
    assert c.main_window.undo_stack.labels == [], "no debe capturar si cancela"
    print("[OK] cancelar el modal no muta el modelo ni la pila de undo")


def test_multi_delete_de_nodos_con_cascada():
    p = _new_project()
    p.set_nodal_load(3, 100, 0)
    c = _new_canvas(p)
    c.selected_nodes = {1, 6}          # los dos del borde izquierdo
    original = _autoconfirm(True)
    try:
        c._on_delete_key()
    finally:
        messagebox.askyesno = original

    # Ambos pertenecen al elemento 1: cae en cascada y el 2 sobrevive.
    assert 1 not in p.elements
    assert 2 in p.elements
    assert 1 not in p.nodes and 6 not in p.nodes
    assert c.selected_nodes == set()
    assert len(c.main_window.undo_stack.labels) == 1
    print("[OK] Supr borra los 2 nodos seleccionados con su cascada")


def test_prioridad_carga_sobre_nodo():
    """Clickear una carga agrega el nodo al set de nodos ademas del de cargas.
    Supr tiene que borrar la carga, NO el nodo (orden del hit-test)."""
    p = _new_project()
    p.set_nodal_load(1, 100, 0)
    c = _new_canvas(p)
    c.selected_loads = {1}
    c.selected_nodes = {1}

    c._on_delete_key()

    assert p.nodal_loads == {}
    assert 1 in p.nodes, "el nodo no se debe borrar junto con su carga"
    print("[OK] la prioridad carga > nodo se respeta")


def test_sin_seleccion_avisa_en_vez_de_callarse():
    p = _new_project()
    c = _new_canvas(p)

    c._on_delete_key()

    assert set(p.elements) == {1, 2} and len(p.nodes) == 6
    assert c.main_window.status, "Supr sin seleccion debe explicar que falta"
    assert "Nada seleccionado" in c.main_window.status[-1]
    print("[OK] Supr sin seleccion explica que hay que seleccionar algo")


def test_prune_dead_selection():
    p = _new_project()
    p.set_nodal_load(1, 100, 0)
    c = _new_canvas(p)
    c.selected_nodes = {1, 99}
    c.selected_elements = {1, 77}
    c.selected_loads = {1, 42}
    c.selected_constraints = {5}
    c.selected_surfaces = {0}
    c.selected_edges = {frozenset({1, 2}), frozenset({1, 99})}

    assert c.prune_dead_selection() is True
    assert c.selected_nodes == {1}
    assert c.selected_elements == {1}
    assert c.selected_loads == {1}
    assert c.selected_constraints == set()      # no hay BCs en el modelo
    assert c.selected_surfaces == set()         # no hay cargas superficiales
    assert c.selected_edges == {frozenset({1, 2})}
    # Idempotente: una segunda pasada ya no cambia nada.
    assert c.prune_dead_selection() is False
    print("[OK] prune_dead_selection saca los ids muertos y es idempotente")


if __name__ == "__main__":
    print("=" * 62)
    print("  TEST: borrado desde el canvas con multi-seleccion")
    print("=" * 62)
    test_multi_delete_de_cargas()
    test_multi_delete_de_restricciones()
    test_delete_de_superficial_no_deja_indice_stale()
    test_multi_delete_de_superficiales_de_atras_para_adelante()
    test_multi_delete_de_elementos_con_cascada()
    test_cancelar_el_modal_no_borra_nada()
    test_multi_delete_de_nodos_con_cascada()
    test_prioridad_carga_sobre_nodo()
    test_sin_seleccion_avisa_en_vez_de_callarse()
    test_prune_dead_selection()
    print("=" * 62)
    print("  TODOS LOS TESTS PASARON [10/10]")
    print("=" * 62)
