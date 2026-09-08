"""
Tests del flujo de resolucion (fase Proceso): la tecla F5 y el auto-solve.

Sin display: `MainWindow` y `PostProcessTab` se instancian con
`object.__new__` y se les montan a mano los atributos que la ruta de
resolucion toca (project, un notebook de mentira, un frame de mentira).
Asi se ejercita el codigo REAL —no una copia— sin abrir ventana.

Regresiones que cubre:
  - F5 **no valida por su cuenta**: antes cortaba con dos `showwarning`
    secos (sin elementos / sin restricciones) que nombraban el problema
    pero no como resolverlo, y nunca llegaba al comprobador de salud. La
    tesis (Anexo A) promete el comprobador detras de F5 y la regla dura 16
    prohibe duplicar la validacion en la GUI.
  - F5 fuerza la re-resolucion (invalida `is_solved` y la solucion cacheada
    ANTES de llamar `auto_solve`).
  - Guard de reentrancia de `auto_solve`: el `HealthReportDialog` es no
    modal y su `wait_window()` corre el event loop, asi que el
    `<<NotebookTabChanged>>` que Tk encola al cambiar a Post volvia a
    entrar y **apilaba un segundo dialogo de salud** sobre el primero.
  - El solve exitoso pone y saca el cursor de espera.
  - Los mensajes del launcher de modulos no mandan al alumno a un menu que
    no existe (los ejemplos viven en Ayuda, no en Archivo).
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import tkinter                                   # noqa: F401
except ImportError:
    print("Tk no disponible — test omitido")
    sys.exit(0)

import gui.main_window as main_window_mod
from gui.main_window import MainWindow
from gui.postprocessing.post_tab import PostProcessTab
from models.example_library import load_example_project
from models.material import Material
from models.project import ProjectModel


# ── dobles minimos ───────────────────────────────────────────────────

class _NotebookStub:
    def __init__(self):
        self.selected = []

    def select(self, idx=None):
        if idx is None:
            return 0
        self.selected.append(idx)

    def index(self, _what):
        return self.selected[-1] if self.selected else 0


class _MessageBoxSpy:
    """Reemplazo de `messagebox` que registra en vez de abrir ventanas."""

    def __init__(self):
        self.calls = []

    def showwarning(self, titulo, mensaje, **_kw):
        self.calls.append(("warning", titulo, mensaje))

    def showerror(self, titulo, mensaje, **_kw):
        self.calls.append(("error", titulo, mensaje))

    def showinfo(self, titulo, mensaje, **_kw):
        self.calls.append(("info", titulo, mensaje))

    def askyesno(self, *_a, **_kw):
        self.calls.append(("askyesno",))
        return True


class _PostTabStub:
    """Doble del post_tab para los tests de `_on_solve`."""

    def __init__(self, project):
        self.project = project
        self.solution = "solucion-vieja"
        self.llamadas = []

    def auto_solve(self):
        # Registramos el estado tal como lo ve `auto_solve`: si F5 no
        # invalido antes, `auto_solve` se limitaria a repintar.
        self.llamadas.append((self.project.is_solved, self.solution))


class _ToplevelStub:
    def __init__(self):
        self.cursores = []

    def configure(self, **kw):
        if "cursor" in kw:
            self.cursores.append(kw["cursor"])


class _FrameStub:
    def __init__(self):
        self.top = _ToplevelStub()

    def winfo_toplevel(self):
        return self.top

    def update_idletasks(self):
        pass


class _MainWindowStub:
    def __init__(self, project):
        self.project = project
        self.notebook = _NotebookStub()
        self.status = []

    def set_status(self, msg):
        self.status.append(msg)

    def _update_status_info(self):
        pass


def _project_sin_restricciones():
    """Un Q4 valido pero sin BCs: error critico `no_restraints`."""
    p = ProjectModel()
    p.materials["acero"] = Material("acero", 200000, 0.3)
    p.add_node(0, 0, 1); p.add_node(1, 0, 2)
    p.add_node(1, 1, 3); p.add_node(0, 1, 4)
    p.add_element([1, 2, 3, 4], 1.0, "acero", 1)
    return p


def _main_window(project):
    mw = object.__new__(MainWindow)
    mw.project = project
    mw.notebook = _NotebookStub()
    mw.post_tab = _PostTabStub(project)
    return mw


def _post_tab(project, main_window=None):
    pt = object.__new__(PostProcessTab)
    pt.project = project
    pt.main_window = main_window or _MainWindowStub(project)
    pt.frame = _FrameStub()
    pt._solving = False
    pt.solution = None
    pt.nodal_stresses = None
    pt.element_stresses = None
    pt.probe_overlay = None
    pt.surface_3d_viewer = None
    pt._raw_grid_cache = None
    return pt


# ── tests de F5 ──────────────────────────────────────────────────────

def test_f5_sin_elementos_no_corta_con_showwarning():
    """F5 sobre un proyecto vacio delega en el comprobador de salud."""
    spy = _MessageBoxSpy()
    original = main_window_mod.messagebox
    main_window_mod.messagebox = spy
    try:
        mw = _main_window(ProjectModel())
        MainWindow._on_solve(mw)
    finally:
        main_window_mod.messagebox = original

    assert spy.calls == [], f"F5 abrio un modal propio: {spy.calls}"
    assert mw.notebook.selected == [2], "F5 no navego al Post-Proceso"
    assert len(mw.post_tab.llamadas) == 1, "F5 no llamo a auto_solve"
    print("[OK] F5 sin elementos delega en el validador (sin showwarning)")


def test_f5_sin_restricciones_no_corta_con_showwarning():
    spy = _MessageBoxSpy()
    original = main_window_mod.messagebox
    main_window_mod.messagebox = spy
    try:
        mw = _main_window(_project_sin_restricciones())
        MainWindow._on_solve(mw)
    finally:
        main_window_mod.messagebox = original

    assert spy.calls == [], f"F5 abrio un modal propio: {spy.calls}"
    assert len(mw.post_tab.llamadas) == 1
    print("[OK] F5 sin restricciones delega en el validador")


def test_f5_fuerza_la_re_resolucion():
    """Si el modelo ya estaba resuelto, F5 lo re-resuelve (no repinta)."""
    p = load_example_project(P=1000.0)
    p.is_solved = True
    mw = _main_window(p)
    MainWindow._on_solve(mw)

    assert mw.post_tab.llamadas == [(False, None)], (
        "auto_solve vio el modelo como ya resuelto: F5 no forzo el re-solve"
    )
    print("[OK] F5 invalida is_solved y la solucion cacheada antes de resolver")


# ── tests del guard de reentrancia ───────────────────────────────────

def test_guard_de_reentrancia_no_apila_dialogos_de_salud():
    """Reentrar en auto_solve mientras el dialogo esta abierto no lo duplica."""
    import gui.dialogs.health_report_dialog as hrd

    pt = _post_tab(_project_sin_restricciones())
    creados = []

    class _DialogoFalso:
        def __init__(self, *_a, **_kw):
            creados.append(1)
            self.fixes_applied = 0

        def show(self):
            # Esto es lo que hace Tk durante `wait_window()`: despachar el
            # `<<NotebookTabChanged>>` encolado, que llama a auto_solve.
            pt.auto_solve()
            return "cancel"

    original = hrd.HealthReportDialog
    hrd.HealthReportDialog = _DialogoFalso
    try:
        pt.auto_solve()
    finally:
        hrd.HealthReportDialog = original

    assert len(creados) == 1, (
        f"se apilaron {len(creados)} dialogos de salud en vez de 1"
    )
    assert pt.project.is_solved is False
    print("[OK] el guard de reentrancia deja un solo dialogo de salud")


def test_guard_libera_el_flag_aun_si_algo_falla():
    """El flag `_solving` se libera siempre: si no, F5 quedaria muerto."""
    pt = _post_tab(_project_sin_restricciones())

    def _explota():
        raise RuntimeError("fallo simulado")

    pt._auto_solve = _explota
    try:
        pt.auto_solve()
    except RuntimeError:
        pass
    assert pt._solving is False, "auto_solve quedo bloqueado para siempre"
    print("[OK] `_solving` se libera aunque el solve levante una excepcion")


def test_solve_exitoso_pone_y_saca_el_cursor_de_espera():
    p = load_example_project(P=1000.0)
    mw = _MainWindowStub(p)
    pt = _post_tab(p, mw)
    # El repintado y la tabla son responsabilidad del Post (ya cubiertos
    # por test_canvas_visualization): aca solo interesa el flujo del solve.
    pt._on_result_changed = lambda: None
    pt._update_table = lambda: None
    pt.maybe_reactivate_probe_overlay = lambda: None

    pt.auto_solve()

    assert p.is_solved is True, "el ejemplo canonico no se resolvio"
    assert pt.solution is not None
    assert pt.frame.top.cursores == ["watch", ""], (
        f"cursor de espera mal manejado: {pt.frame.top.cursores}"
    )
    assert any("Resuelto" in s for s in mw.status), mw.status
    print("[OK] el solve exitoso muestra y retira el cursor de espera")


# ── tests de los mensajes del launcher ───────────────────────────────

def test_el_launcher_manda_al_menu_que_existe():
    """Sin malla, el aviso apunta a Ayuda ▸ Cargar Ejemplo (no a Archivo)."""
    import education.module_launcher as launcher

    spy = _MessageBoxSpy()
    original = launcher.messagebox
    launcher.messagebox = spy
    try:
        ok = launcher.open_module(None, ProjectModel(), "mod03")
    finally:
        launcher.messagebox = original

    assert ok is False
    assert len(spy.calls) == 1
    _tipo, _titulo, mensaje = spy.calls[0]
    assert "Ayuda ▸ Cargar Ejemplo" in mensaje, mensaje
    assert "Archivo ▸ Cargar Ejemplo" not in mensaje
    assert launcher.module_label("mod03") in mensaje, (
        "el aviso no nombra el modulo que el alumno quiso abrir"
    )
    print("[OK] el aviso sin malla nombra el modulo y el menu correcto")


def test_module_label_devuelve_la_etiqueta_visible():
    from education.module_launcher import MODULE_META, module_label

    for key, (label, _desc) in MODULE_META.items():
        assert module_label(key) == label
    # Key desconocida: devolvemos la key, no una excepcion ni un vacio.
    assert module_label("modXX") == "modXX"
    print("[OK] module_label mapea las 8 keys y tolera una desconocida")


if __name__ == "__main__":
    print("=" * 62)
    print("  TEST: flujo de resolucion (F5, auto_solve, launcher)")
    print("=" * 62)
    test_f5_sin_elementos_no_corta_con_showwarning()
    test_f5_sin_restricciones_no_corta_con_showwarning()
    test_f5_fuerza_la_re_resolucion()
    test_guard_de_reentrancia_no_apila_dialogos_de_salud()
    test_guard_libera_el_flag_aun_si_algo_falla()
    test_solve_exitoso_pone_y_saca_el_cursor_de_espera()
    test_el_launcher_manda_al_menu_que_existe()
    test_module_label_devuelve_la_etiqueta_visible()
    print("=" * 62)
    print("  TODOS LOS TESTS PASARON [8/8]")
    print("=" * 62)
