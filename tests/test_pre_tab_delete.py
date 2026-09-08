"""
Tests del borrado y del pegado desde las tablas del Pre-Proceso
(`PreProcessTab._remove_*`, `_sync_selection_after_delete`, `_paste_*`).

Sin display: se instancia el `PreProcessTab` con `object.__new__` y se le
montan a mano los atributos que esas rutas tocan (los Treeview se
reemplazan por un doble minimo con `selection()`, y el `MeshCanvas` por
otro `object.__new__` con sus seis sets). Asi se ejercita el codigo REAL
—no una copia— sin construir un widget Tk ni abrir ventana.

Regresiones que cubre:
  - Borrar desde una tabla saneaba el modelo pero NO la seleccion del
    canvas, de la que salen las filas fantasma y el tag `canvas_selected`:
      * borrar un nodo dejaba una fantasma azul de un nodo inexistente en
        Cargas y Restricciones (clickearla no hacia nada ni lo decia);
      * borrar una carga o restriccion hacia REAPARECER la fila borrada
        como fantasma con ceros, en el mismo lugar;
      * borrar una carga superficial dejaba su indice —posicional— en
        `selected_surfaces`, resaltando OTRA carga.
  - `Supr` sin filas seleccionadas no decia nada (callejon sin salida).
  - Un solo snapshot de undo por accion del usuario (regla dura 4).
  - El badge de salud / la info del modelo se refrescan al borrar desde la
    tabla, no solo al borrar desde el lienzo.
  - El paste TSV dice POR QUE descarto cada fila, y acepta la coma decimal.
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
from gui.preprocessing.pre_tab import PreProcessTab
from models.material import Material
from models.project import ProjectModel


class _UndoStubStack:
    def __init__(self):
        self.labels = []

    def capture(self, label):
        self.labels.append(label)


class _MainWindowStub:
    """Doble del MainWindow: barra de estado, undo y los dos refrescos de
    chrome que las rutas de borrado deben disparar."""

    def __init__(self):
        self.undo_stack = _UndoStubStack()
        self.mesh_canvas = None
        self.status = []
        self.status_info_calls = 0
        self.title_calls = 0

    def set_status(self, msg):
        self.status.append(msg)

    def _update_status_info(self):
        self.status_info_calls += 1

    def _update_title(self):
        self.title_calls += 1


class _TreeStub:
    """Lo unico que las rutas de borrado le piden a un Treeview."""

    def __init__(self, seleccion=()):
        self._sel = tuple(str(i) for i in seleccion)

    def selection(self):
        return self._sel


def _new_project():
    """Dos elementos Q4 lado a lado: nodos 1..6, elementos 1 y 2."""
    p = ProjectModel()
    p.materials["acero"] = Material("acero", 200000, 0.3)
    p.add_node(0, 0, 1); p.add_node(1, 0, 2); p.add_node(2, 0, 3)
    p.add_node(2, 1, 4); p.add_node(1, 1, 5); p.add_node(0, 1, 6)
    p.add_element([1, 2, 5, 6], 1.0, "acero", 1)
    p.add_element([2, 3, 4, 5], 1.0, "acero", 2)
    return p


def _new_canvas(project, main_window):
    c = object.__new__(MeshCanvas)
    c.project = project
    c.main_window = main_window
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
    c.redraw = lambda: None
    return c


def _new_tab(project, **selecciones):
    """PreProcessTab sin Tk. `selecciones` mapea nombre de tabla -> iids."""
    mw = _MainWindowStub()
    canvas = _new_canvas(project, mw)
    mw.mesh_canvas = canvas

    t = object.__new__(PreProcessTab)
    t.project = project
    t.main_window = mw
    t._pending_new = None
    t._suppress_pending_check = False
    t._syncing_from_canvas = False
    t._syncing_to_canvas = False
    t._last_canvas_sel = None
    t._loads_visual_order = []
    t._constraints_visual_order = []
    t._surfaces_visual_order = []
    for nombre in ("nodes", "elements", "loads", "constraints", "surface"):
        setattr(t, f"{nombre}_tree",
                _TreeStub(selecciones.get(nombre, ())))
    # Los refrescos de Treeview necesitan widgets reales: se anulan y en su
    # lugar se cuentan, que es lo unico que estos tests observan de ellos.
    t.refrescos = []
    for nombre in ("nodes", "elements", "loads", "constraints", "surface"):
        setattr(t, f"_refresh_{nombre if nombre != 'surface' else 'surface'}_tree",
                (lambda n=nombre, **kw: t.refrescos.append(n)))
    t._refresh_all_trees = lambda: t.refrescos.append("all")
    t._ensure_q9_consistency = lambda **kw: 0
    return t, canvas, mw


def _autoconfirm(value=True):
    original = messagebox.askyesno
    messagebox.askyesno = lambda *a, **k: value
    return original


# ─── Saneo de la seleccion tras borrar desde la tabla ───────────────────

def test_borrar_nodo_no_deja_fantasma_de_un_nodo_inexistente():
    """Regresion: seleccionar la fila propaga el nodo a `selected_nodes`.

    Si el borrado no lo saca, las sub-pestañas Cargas y Restricciones
    dibujan una fila fantasma azul de un nodo que ya no existe.
    """
    p = _new_project()
    t, canvas, mw = _new_tab(p, nodes=[3])
    canvas.selected_nodes = {3}

    original = _autoconfirm(True)
    try:
        t._remove_node()
    finally:
        messagebox.askyesno = original

    assert 3 not in p.nodes
    assert canvas.selected_nodes == set(), "id muerto en la seleccion"
    assert canvas.highlighted_node is None
    assert len(mw.undo_stack.labels) == 1
    assert mw.status and "Nodo 3 eliminado" in mw.status[-1]
    print("[OK] borrar un nodo desde la tabla no deja fantasmas muertas")


def test_borrar_carga_no_la_devuelve_como_fantasma():
    """Regresion: `_on_load_select` mete el nodo en `selected_nodes` para
    el halo. Sin soltarlo, la fila borrada reaparece como fantasma azul
    con Fx=Fy=0 en el mismo lugar."""
    p = _new_project()
    p.set_nodal_load(2, 100.0, -50.0)
    t, canvas, mw = _new_tab(p, loads=[2])
    canvas.selected_loads = {2}
    canvas.selected_nodes = {2}

    t._remove_load()

    assert p.nodal_loads == {}
    assert canvas.selected_loads == set()
    assert canvas.selected_nodes == set(), "el nodo vuelve como fantasma"
    assert len(mw.undo_stack.labels) == 1
    assert "Carga en nodo 2 eliminada." in mw.status
    print("[OK] borrar una carga no la devuelve como fila fantasma")


def test_borrar_restriccion_no_la_devuelve_como_fantasma():
    p = _new_project()
    p.set_boundary_condition(1, True, True)
    p.set_boundary_condition(6, True, False)
    t, canvas, mw = _new_tab(p, constraints=[1, 6])
    canvas.selected_constraints = {1, 6}
    canvas.selected_nodes = {1, 6}

    t._remove_constraint()

    assert p.boundary_conditions == {}
    assert canvas.selected_constraints == set()
    assert canvas.selected_nodes == set()
    assert len(mw.undo_stack.labels) == 1
    assert "2 restricciones eliminadas." in mw.status
    print("[OK] borrar restricciones no las devuelve como filas fantasma")


def test_borrar_superficial_desde_la_tabla_no_deja_indice_stale():
    """Regresion (el mismo defecto que ya se corrigio en el lienzo): los
    indices de `selected_surfaces` son posicionales, asi que el que queda
    pasa a señalar otra carga y el canvas la resalta en amarillo."""
    p = _new_project()
    p.add_surface_load(1, 2, 10.0, 10.0)
    p.add_surface_load(2, 3, 20.0, 20.0)
    p.add_surface_load(3, 4, 30.0, 30.0)
    t, canvas, mw = _new_tab(p, surface=[0])
    canvas.selected_surfaces = {0}

    t._remove_surface_load()

    assert [sl.q_start for sl in p.surface_loads] == [20.0, 30.0]
    assert canvas.selected_surfaces == set(), "indice stale tras el borrado"
    assert canvas.highlighted_surface is None
    assert "Carga superficial #0 eliminada." in mw.status
    print("[OK] borrar una superficial desde la tabla no deja indices stale")


def test_multi_borrado_de_superficiales_respeta_el_orden():
    p = _new_project()
    p.add_surface_load(1, 2, 10.0, 10.0)
    p.add_surface_load(2, 3, 20.0, 20.0)
    p.add_surface_load(3, 4, 30.0, 30.0)
    t, canvas, mw = _new_tab(p, surface=[0, 2])

    t._remove_surface_load()

    # De menor a mayor, el segundo `del` sacaria la carga equivocada.
    assert [sl.q_start for sl in p.surface_loads] == [20.0]
    assert len(mw.undo_stack.labels) == 1
    print("[OK] el borrado multiple de superficiales respeta los indices")


def test_borrar_elemento_sanea_la_seleccion():
    p = _new_project()
    t, canvas, mw = _new_tab(p, elements=[1])
    canvas.selected_elements = {1}

    original = _autoconfirm(True)
    try:
        t._remove_element()
    finally:
        messagebox.askyesno = original

    assert 1 not in p.elements
    assert canvas.selected_elements == set()
    assert canvas.highlighted_element is None
    print("[OK] borrar un elemento desde la tabla sanea la seleccion")


def test_un_id_muerto_no_genera_fila_fantasma():
    """Defensa en profundidad: aunque un id muerto sobreviva en los sets
    (undo/redo, una mutacion externa), las listas visuales no deben
    proponer una fantasma de algo que no existe — clickearla no crea nada
    y el alumno no entiende por que."""
    p = _new_project()
    t, canvas, mw = _new_tab(p)
    canvas.selected_nodes = {2, 404}
    canvas.selected_edges = {frozenset({1, 2}), frozenset({2, 404})}

    fantasmas_carga = [nid for kind, nid in t._build_loads_visual_list()
                       if kind == "ghost"]
    fantasmas_bc = [nid for kind, nid in t._build_constraints_visual_list()
                    if kind == "ghost"]
    fantasmas_sup = [val for kind, val in t._build_surfaces_visual_list()
                     if kind == "ghost"]

    assert fantasmas_carga == [2], fantasmas_carga
    assert fantasmas_bc == [2], fantasmas_bc
    assert fantasmas_sup == [frozenset({1, 2})], fantasmas_sup
    print("[OK] un id muerto en la seleccion no genera filas fantasma")


# ─── Avisos y refresco del chrome ───────────────────────────────────────

def test_supr_sin_seleccion_avisa_en_las_cinco_tablas():
    p = _new_project()
    p.set_nodal_load(1, 10, 0)
    p.set_boundary_condition(2, True, True)
    p.add_surface_load(1, 2, 5.0, 5.0)
    t, canvas, mw = _new_tab(p)

    for metodo in (t._remove_node, t._remove_element, t._remove_load,
                   t._remove_constraint, t._remove_surface_load):
        mw.status.clear()
        metodo()
        assert mw.status, f"{metodo.__name__} sin seleccion se queda mudo"
        assert "Nada seleccionado" in mw.status[-1]

    # Y nada se toco: ni el modelo ni la pila de undo.
    assert len(p.nodes) == 6 and len(p.elements) == 2
    assert p.nodal_loads and p.boundary_conditions and p.surface_loads
    assert mw.undo_stack.labels == []
    print("[OK] Supr sin seleccion explica que falta en las 5 tablas")


def test_placeholder_y_fantasma_no_cuentan_como_seleccion():
    p = _new_project()
    p.set_nodal_load(1, 10, 0)
    t, canvas, mw = _new_tab(p, loads=["__new__", "__ghost__4"])

    t._remove_load()

    assert p.nodal_loads, "la fila placeholder no debe borrar nada"
    assert "Nada seleccionado" in mw.status[-1]
    print("[OK] placeholder y fantasma no cuentan como seleccion")


def test_borrar_refresca_badge_de_salud_y_titulo():
    """El badge de salud vive en `_update_status_info`: quitar la ultima
    restriccion deja el modelo sin resolver y el badge tiene que enterarse.
    Antes solo el borrado desde el lienzo lo refrescaba."""
    p = _new_project()
    p.set_boundary_condition(1, True, True)
    t, canvas, mw = _new_tab(p, constraints=[1])

    t._remove_constraint()

    assert mw.status_info_calls == 1, "el badge de salud queda desactualizado"
    assert mw.title_calls == 1, "el ● de modificado queda desactualizado"
    print("[OK] borrar desde la tabla refresca el badge de salud y el titulo")


# ─── Paste TSV ──────────────────────────────────────────────────────────

def test_paste_dice_por_que_descarto_las_filas():
    p = _new_project()
    t, canvas, mw = _new_tab(p)
    t._check_pending_completion = lambda: True

    t._paste_loads([["1", "10", "0"],       # ok
                    ["99", "10", "0"],      # nodo inexistente
                    ["2", "x", "0"],        # no numerico
                    ["3", "5"]])            # faltan columnas

    assert p.nodal_loads.keys() == {1}
    msg = mw.status[-1]
    assert msg.startswith("1/4 fila(s) pegada(s).")
    assert "nodo inexistente" in msg
    assert "no numerico" in msg
    assert "faltar columnas" in msg
    print("[OK] el paste dice cuantas filas descarto y por que")


def test_paste_acepta_la_coma_decimal():
    p = _new_project()
    t, canvas, mw = _new_tab(p)
    t._check_pending_completion = lambda: True

    t._paste_loads([["1", "1,5", "-2,25"]])

    assert p.nodal_loads[1].fx == 1.5
    assert p.nodal_loads[1].fy == -2.25
    assert mw.status[-1] == "1/1 fila(s) pegada(s)."
    print("[OK] el paste sigue tolerando la coma decimal de Excel")


if __name__ == "__main__":
    print("=" * 62)
    print("  TEST: borrado y pegado desde las tablas del Pre-Proceso")
    print("=" * 62)
    test_borrar_nodo_no_deja_fantasma_de_un_nodo_inexistente()
    test_borrar_carga_no_la_devuelve_como_fantasma()
    test_borrar_restriccion_no_la_devuelve_como_fantasma()
    test_borrar_superficial_desde_la_tabla_no_deja_indice_stale()
    test_multi_borrado_de_superficiales_respeta_el_orden()
    test_borrar_elemento_sanea_la_seleccion()
    test_un_id_muerto_no_genera_fila_fantasma()
    test_supr_sin_seleccion_avisa_en_las_cinco_tablas()
    test_placeholder_y_fantasma_no_cuentan_como_seleccion()
    test_borrar_refresca_badge_de_salud_y_titulo()
    test_paste_dice_por_que_descarto_las_filas()
    test_paste_acepta_la_coma_decimal()
    print("=" * 62)
    print("  TODOS LOS TESTS PASARON [12/12]")
    print("=" * 62)
