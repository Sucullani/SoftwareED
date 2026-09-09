"""
Tests de la ventana principal: guardado, atajos y teclas de los dialogos.

Sin display: `MainWindow` se instancia con `object.__new__` y se le montan
a mano los atributos que cada camino toca (project, un stack de mentira,
un notebook de mentira), igual que hacen `test_solve_flow`,
`test_pre_tab_delete` y `test_dialogs`. Asi se ejercita el codigo REAL, no
una copia.

Regresiones que cubre:
  - **Perdida de datos al cancelar el guardado.** Nuevo Proyecto / Cargar
    Ejemplo / Salir preguntaban "¿guardar los cambios?" y, si el alumno
    contestaba que si y despues cancelaba el dialogo de *Guardar Como* (o
    fallaba la escritura), **seguian adelante igual** y destruian el
    modelo. Ahora `_on_save_project` devuelve si el proyecto quedo en
    disco y `_confirm_discard_changes` aborta si no.
  - `Ctrl+S` sin cambios ya no es mudo (el item de menu esta gris en ese
    estado, pero el atajo se dispara igual).
  - `F8` (ORTHO) fuera del modo dibujo ya no es invisible: el indicador de
    la barra solo se muestra dibujando, asi que el toggle no se veia por
    ningun lado.
  - `F11` sincroniza el flag solo si Tk acepto el cambio.
  - La ventana de atajos (`Ctrl+/`) nombra las teclas que el programa
    realmente tiene, y no ubica `Ctrl+E` en un menu donde no esta.
  - `bind_dialog_keys` ata Escape / Return donde corresponde y **no** ata
    Return donde no hay default seguro (reporte de salud, falta pdflatex).
  - **Dos Memorias compilandose a la vez.** El dialogo de progreso no es
    modal, asi que volver a *Exportar > Memoria de Calculo* con una
    compilacion en curso arrancaba un segundo thread sobre el mismo `.pdf`.
    Ahora hay un guard `_exportando_pdf` que avisa en la barra de estado.
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

import inspect

import gui.main_window as main_window_mod
from gui.main_window import MainWindow
from models.project import ProjectModel
from models.material import Material


# ── dobles minimos ───────────────────────────────────────────────────

class _MessageBoxSpy:
    """Reemplazo de `messagebox`: registra y devuelve lo que se le diga."""

    def __init__(self, askyesnocancel=None):
        self.calls = []
        self._respuesta = askyesnocancel

    def askyesnocancel(self, titulo, mensaje, **_kw):
        self.calls.append(("askyesnocancel", titulo, mensaje))
        return self._respuesta

    def showerror(self, titulo, mensaje, **_kw):
        self.calls.append(("error", titulo, mensaje))

    def showwarning(self, titulo, mensaje, **_kw):
        self.calls.append(("warning", titulo, mensaje))

    def showinfo(self, titulo, mensaje, **_kw):
        self.calls.append(("info", titulo, mensaje))


class _CanvasStub:
    def __init__(self):
        self.ortho_active = False
        self.draw_mode_active = False

    def set_ortho_active(self, valor):
        self.ortho_active = bool(valor)


class _RootStub:
    """Toplevel de mentira para `_on_fullscreen`."""

    def __init__(self, *, acepta=True):
        self.acepta = acepta
        self.atributos = []

    def attributes(self, nombre, valor):
        if not self.acepta:
            raise tkinter.TclError("no soportado")
        self.atributos.append((nombre, valor))


def _main_window(project=None):
    mw = object.__new__(MainWindow)
    mw.project = project if project is not None else ProjectModel()
    mw.status = []
    mw.set_status = mw.status.append
    return mw


def _project_modificado():
    p = ProjectModel()
    p.materials["acero"] = Material("acero", 200000, 0.3)
    p.add_node(0, 0, 1)
    p.is_modified = True
    return p


# ── 1. perdida de datos al cancelar el guardado ──────────────────────

def test_cancelar_guardar_como_aborta_la_accion_destructiva():
    """Si → Guardar Como cancelado ⇒ NO se descarta el modelo."""
    mw = _main_window(_project_modificado())
    guardados = []

    def _save_falla():
        guardados.append("intento")
        return False               # el alumno cerro el filedialog

    mw._on_save_project = _save_falla
    spy = _MessageBoxSpy(askyesnocancel=True)
    original = main_window_mod.messagebox
    main_window_mod.messagebox = spy
    try:
        seguir = MainWindow._confirm_discard_changes(mw, "Salir", "salir")
    finally:
        main_window_mod.messagebox = original

    assert guardados == ["intento"], "no se intento guardar"
    assert seguir is False, (
        "se seguia adelante con la accion destructiva aunque el proyecto "
        "no llego a guardarse: ese era el bug"
    )
    assert any("no se guardó" in m for m in mw.status), mw.status
    print("[OK] cancelar Guardar Como aborta la accion destructiva")


def test_guardado_exitoso_deja_continuar():
    mw = _main_window(_project_modificado())
    mw._on_save_project = lambda: True
    spy = _MessageBoxSpy(askyesnocancel=True)
    original = main_window_mod.messagebox
    main_window_mod.messagebox = spy
    try:
        assert MainWindow._confirm_discard_changes(
            mw, "Nuevo Proyecto", "crear el nuevo") is True
    finally:
        main_window_mod.messagebox = original
    print("[OK] con el guardado exitoso la accion sigue")


def test_cancelar_el_dialogo_aborta_y_descartar_sigue():
    """Cancelar (None) aborta; No (False) sigue sin guardar."""
    original = main_window_mod.messagebox

    mw = _main_window(_project_modificado())
    mw._on_save_project = lambda: (_ for _ in ()).throw(
        AssertionError("no debia intentar guardar"))
    main_window_mod.messagebox = _MessageBoxSpy(askyesnocancel=None)
    try:
        assert MainWindow._confirm_discard_changes(mw, "Salir", "salir") is False
    finally:
        main_window_mod.messagebox = original

    mw2 = _main_window(_project_modificado())
    mw2._on_save_project = lambda: (_ for _ in ()).throw(
        AssertionError("no debia intentar guardar"))
    main_window_mod.messagebox = _MessageBoxSpy(askyesnocancel=False)
    try:
        assert MainWindow._confirm_discard_changes(mw2, "Salir", "salir") is True
    finally:
        main_window_mod.messagebox = original
    print("[OK] Cancelar aborta y No descarta, sin intentar guardar")


def test_sin_cambios_no_pregunta_nada():
    mw = _main_window(ProjectModel())          # is_modified = False
    spy = _MessageBoxSpy(askyesnocancel=True)
    original = main_window_mod.messagebox
    main_window_mod.messagebox = spy
    try:
        assert MainWindow._confirm_discard_changes(mw, "Salir", "salir") is True
    finally:
        main_window_mod.messagebox = original
    assert spy.calls == [], "pregunto por cambios que no existen"
    print("[OK] sin cambios sin guardar no hay pregunta")


def test_los_tres_flujos_destructivos_usan_el_helper():
    """Nuevo / Cargar Ejemplo / Salir pasan por la misma puerta."""
    for nombre in ("_on_new_project", "_on_load_example", "_on_exit"):
        codigo = inspect.getsource(getattr(MainWindow, nombre))
        assert "_confirm_discard_changes" in codigo, (
            f"{nombre} decide por su cuenta que hacer con los cambios "
            f"sin guardar"
        )
        assert "askyesnocancel" not in codigo, (
            f"{nombre} volvio a preguntar por su cuenta (tres redacciones "
            f"distintas para la misma decision)"
        )
    print("[OK] los 3 flujos destructivos comparten la confirmacion")


def test_guardar_devuelve_bool_en_los_tres_metodos():
    for nombre in ("_on_save_project", "_on_save_as_project", "_save_to_file"):
        firma = inspect.signature(getattr(MainWindow, nombre))
        assert firma.return_annotation is bool, (
            f"{nombre} no declara que devuelve si el proyecto quedo en disco"
        )
    print("[OK] los 3 metodos de guardado informan si escribieron")


# ── 2. atajos que no decian nada ─────────────────────────────────────

def test_ctrl_s_sin_cambios_avisa():
    mw = _main_window(ProjectModel())
    assert MainWindow._on_save_project(mw) is True
    assert mw.status and "No hay cambios" in mw.status[-1], mw.status
    print("[OK] Ctrl+S sin cambios lo dice en la barra de estado")


def test_f8_fuera_del_modo_dibujo_avisa():
    mw = _main_window()
    mw.mesh_canvas = _CanvasStub()
    mw._update_ortho_indicator = lambda: None

    MainWindow._on_toggle_ortho(mw)
    assert mw.mesh_canvas.ortho_active is True
    assert mw.status, "F8 fuera del modo dibujo no decia absolutamente nada"
    assert "ORTHO activado" in mw.status[-1]
    assert "tecla D" in mw.status[-1], (
        "el aviso no dice donde se aplica el toggle"
    )

    MainWindow._on_toggle_ortho(mw)
    assert mw.mesh_canvas.ortho_active is False
    assert "ORTHO desactivado" in mw.status[-1]
    print("[OK] F8 fuera del modo dibujo explica que queda armado")


def test_f8_en_modo_dibujo_mantiene_el_mensaje_corto():
    mw = _main_window()
    mw.mesh_canvas = _CanvasStub()
    mw.mesh_canvas.draw_mode_active = True
    mw._update_ortho_indicator = lambda: None
    MainWindow._on_toggle_ortho(mw)
    assert mw.status[-1] == "ORTHO activado", mw.status
    print("[OK] dibujando, el mensaje de ORTHO sigue siendo el corto")


def test_exportar_memoria_no_lanza_dos_compilaciones():
    """Exportar con una Memoria compilandose avisa en vez de arrancar otra.

    El dialogo de progreso NO es modal (decision tomada: la GUI sigue viva
    mientras el worker compila), asi que nada impedia volver a
    *Archivo > Exportar > Memoria de Calculo* y disparar un segundo thread
    sobre el mismo `.pdf` destino."""
    mw = _main_window()
    mw._exportando_pdf = True
    espia = _MessageBoxSpy()
    original = main_window_mod.messagebox
    main_window_mod.messagebox = espia
    try:
        MainWindow._on_export_pdf(mw)
    finally:
        main_window_mod.messagebox = original
    assert not espia.calls, "la segunda exportacion abrio un dialogo"
    assert mw.status and "compilándose" in mw.status[-1], mw.status

    src = inspect.getsource(MainWindow._on_export_pdf)
    assert "self._exportando_pdf = True" in src, (
        "el guard nunca se arma: `_on_export_pdf` no lo pone en True"
    )
    assert "self._exportando_pdf = False" in src, (
        "el guard no se libera al terminar: Exportar quedaria muerto"
    )
    # Se libera ANTES de los messagebox modales del cierre; si se liberara al
    # final, Exportar quedaria bloqueado mientras el alumno lee el aviso.
    pos_false = src.index("self._exportando_pdf = False")
    pos_msg = src.index("askyesno")
    assert pos_false < pos_msg, (
        "el guard se libera despues de los dialogos modales de cierre"
    )
    print("[OK] Exportar Memoria no lanza dos compilaciones a la vez")


def test_f11_no_desincroniza_el_flag_si_tk_rechaza():
    mw = _main_window()
    mw._is_fullscreen = False
    mw.root = _RootStub(acepta=False)
    MainWindow._on_fullscreen(mw)
    assert mw._is_fullscreen is False, (
        "el flag se invertia aunque Tk rechazara el cambio: el siguiente "
        "F11 pedia lo contrario de lo que se ve"
    )
    assert mw.status and "no disponible" in mw.status[-1]

    mw2 = _main_window()
    mw2._is_fullscreen = False
    mw2.root = _RootStub(acepta=True)
    MainWindow._on_fullscreen(mw2)
    assert mw2._is_fullscreen is True
    assert mw2.root.atributos == [("-fullscreen", True)]
    assert "F11" in mw2.status[-1], "no dice como salir de pantalla completa"
    print("[OK] F11 sincroniza el flag solo si Tk acepto")


# ── 3. la ventana de atajos contra los binds reales ──────────────────

def test_la_ventana_de_atajos_nombra_las_teclas_que_existen():
    texto = inspect.getsource(MainWindow._on_shortcuts)
    for tecla in ("Ctrl+N", "Ctrl+O", "Ctrl+S", "Ctrl+Shift+S", "Ctrl+Q",
                  "Ctrl+Z", "Ctrl+Y", "Ctrl+Shift+Z", "F5", "F8", "F11",
                  "Ctrl+Tab", "Ctrl+/", "F1", "Ctrl+E", "Backspace",
                  "Supr", "Esc", "Ctrl+C", "Ctrl+V"):
        assert tecla in texto, f"la ventana de atajos no menciona {tecla}"
    print("[OK] la ventana de atajos cubre las teclas del programa")


def test_ctrl_e_figura_en_el_menu_donde_realmente_esta():
    """`Ctrl+E` carga un ejemplo, y los ejemplos viven en **Ayuda**."""
    texto = inspect.getsource(MainWindow._on_shortcuts)
    bloque_ayuda = texto.split('"Ayuda\\n"')[-1]
    assert "Ctrl+E" in bloque_ayuda, (
        "Ctrl+E seguia listado bajo 'Archivo', un menu donde Cargar "
        "Ejemplo no esta"
    )
    print("[OK] Ctrl+E figura bajo Ayuda, que es donde esta el ejemplo")


def test_el_manual_de_usuario_dejo_de_ser_una_promesa():
    texto = inspect.getsource(MainWindow._on_help)
    # El docstring del metodo SI puede nombrar el mensaje viejo (explica
    # por que se fue): lo que no puede volver es al cuerpo.
    cuerpo = texto.split('"""')[-1]
    assert "próximamente" not in cuerpo and "proximamente" not in cuerpo, (
        "F1 volvio a prometer un manual que no existe"
    )
    for hito in ("PRE-PROCESO", "PROCESO", "POST-PROCESO", "F5", "Ctrl+Z"):
        assert hito in texto, f"el manual no menciona {hito}"
    print("[OK] F1 explica el flujo en vez de anunciar un manual futuro")


# ── 4. Escape / Return de los dialogos ───────────────────────────────

def test_bind_dialog_keys_ata_solo_lo_pedido():
    from gui.dialogs._dialog_helpers import bind_dialog_keys

    class _WinSpy:
        def __init__(self):
            self.binds = {}

        def bind(self, secuencia, handler):
            self.binds[secuencia] = handler

    win = _WinSpy()
    llamadas = []
    bind_dialog_keys(win, on_escape=lambda: llamadas.append("esc"))
    assert set(win.binds) == {"<Escape>"}, win.binds
    assert win.binds["<Escape>"]() == "break", (
        "sin el 'break' el Return de un Entry sigue subiendo por bindtags"
    )
    assert llamadas == ["esc"]

    win2 = _WinSpy()
    bind_dialog_keys(win2, on_escape=lambda: None, on_return=lambda: None)
    assert set(win2.binds) == {"<Escape>", "<Return>", "<KP_Enter>"}, win2.binds
    print("[OK] bind_dialog_keys ata Escape/Return (y el Enter numerico)")


def test_los_diez_dialogos_responden_a_escape():
    import gui.dialogs.about_dialog as about
    import gui.dialogs.analysis_type_dialog as analysis
    import gui.dialogs.dxf_import_dialog as dxf
    import gui.dialogs.element_type_dialog as element
    import gui.dialogs.gravity_dialog as gravity
    import gui.dialogs.health_report_dialog as health
    import gui.dialogs.material_dialog as material
    import gui.dialogs.memoria_style_dialog as memoria
    import gui.dialogs.pdflatex_missing_dialog as pdflatex
    import gui.dialogs.units_dialog as units

    modulos = {
        "about": about, "analysis": analysis, "dxf": dxf, "element": element,
        "gravity": gravity, "health": health, "material": material,
        "memoria": memoria, "pdflatex": pdflatex, "units": units,
    }
    for nombre, mod in modulos.items():
        fuente = inspect.getsource(mod)
        assert "bind_dialog_keys(" in fuente, (
            f"el dialogo {nombre} no responde a Escape"
        )
        assert "on_escape=" in fuente, f"{nombre} no define que hace Escape"
    print(f"[OK] los {len(modulos)} dialogos cierran con Escape")


def test_los_dos_dialogos_sin_default_seguro_no_atan_return():
    """Reporte de salud y 'falta pdflatex' NO aceptan con Enter."""
    import gui.dialogs.health_report_dialog as health
    import gui.dialogs.pdflatex_missing_dialog as pdflatex

    for nombre, mod in (("reporte de salud", health),
                        ("falta pdflatex", pdflatex)):
        fuente = inspect.getsource(mod)
        assert "on_return=" not in fuente, (
            f"{nombre} ato Return: sus dos salidas son decisiones opuestas "
            f"(o se van de la aplicacion) y no hay default seguro"
        )
    print("[OK] los 2 dialogos sin default seguro no atan Return")


def test_material_dialog_no_guarda_con_enter_si_hay_campos_invalidos():
    from gui.dialogs.material_dialog import MaterialDialog

    dlg = object.__new__(MaterialDialog)
    dlg.main_window = _main_window()
    dlg.selected_name = "acero"
    dlg._entries = {}
    guardados = []
    dlg._save_material = lambda: guardados.append("guardado")
    dlg._validate_live = lambda: None

    dlg.campos_invalidos = lambda: ["nu", "density"]
    MaterialDialog._on_return(dlg)
    assert guardados == [], "guardo con campos invalidos"
    aviso = dlg.main_window.status[-1]
    assert "Poisson" in aviso and "Densidad" in aviso, aviso
    assert "  " not in aviso, f"el aviso arrastra el doble espacio: {aviso!r}"

    dlg.campos_invalidos = lambda: []
    MaterialDialog._on_return(dlg)
    assert guardados == ["guardado"]

    dlg.selected_name = None
    MaterialDialog._on_return(dlg)
    assert "Elegí primero" in dlg.main_window.status[-1]
    print("[OK] Enter en Materiales guarda solo si los 4 campos son validos")


# ── 5. recientes con nombres repetidos ───────────────────────────────

def test_recientes_desambigua_los_nombres_repetidos():
    class _MenuStub:
        def __init__(self):
            self.labels = []

        def delete(self, *_a):
            self.labels.clear()

        def add_command(self, label=None, **_kw):
            self.labels.append(label)

        def add_separator(self):
            pass

    mw = _main_window()
    mw.recent_menu = _MenuStub()
    rutas = ["/tp1/viga.edufem", "/tp2/viga.edufem", "/tp1/cook.edufem"]
    original = main_window_mod.recent_files.load
    main_window_mod.recent_files.load = lambda: rutas
    try:
        MainWindow._build_recent_menu(mw)
    finally:
        main_window_mod.recent_files.load = original

    labels = mw.recent_menu.labels
    assert "tp1" in labels[0] and "tp2" in labels[1], (
        f"dos 'viga.edufem' de carpetas distintas seguian indistinguibles: "
        f"{labels}"
    )
    assert "(" not in labels[2], (
        f"se ensancho el menu con una carpeta que no hacia falta: {labels[2]}"
    )
    print("[OK] los recientes con nombre repetido nombran su carpeta")


# ── 6. la sub-pestaña educativa que no controlaba nada ───────────────

def test_proceso_no_tiene_un_notebook_de_una_sola_pestana():
    import gui.processing.proc_tab as proc

    fuente = inspect.getsource(proc)
    assert "ttk.Notebook" not in fuente, (
        "volvio el Notebook de UNA pestana en Proceso: un control que no "
        "controla nada"
    )
    assert "Modulos Educativos  \"" not in fuente
    print("[OK] Proceso monta el panel de modulos sin Notebook")


def test_las_etiquetas_educativas_estan_acentuadas():
    import gui.preprocessing.pre_tab as pre
    import gui.processing.proc_tab as proc

    assert "🎓 Educación" in inspect.getsource(pre)
    for mod in (pre, proc):
        # Solo los strings visibles: el docstring de `proc_tab` cita la
        # etiqueta vieja para explicar por que se fue.
        for linea in inspect.getsource(mod).splitlines():
            if "header_text=" in linea or "notebook.add" in linea:
                assert "Modulos" not in linea, (
                    f"etiqueta sin acento visible para el alumno: {linea!r}"
                )
    print("[OK] las etiquetas educativas visibles van acentuadas")


if __name__ == "__main__":
    print("=" * 62)
    print("  TEST: ventana principal (guardado, atajos, teclas de dialogo)")
    print("=" * 62)
    test_cancelar_guardar_como_aborta_la_accion_destructiva()
    test_guardado_exitoso_deja_continuar()
    test_cancelar_el_dialogo_aborta_y_descartar_sigue()
    test_sin_cambios_no_pregunta_nada()
    test_los_tres_flujos_destructivos_usan_el_helper()
    test_guardar_devuelve_bool_en_los_tres_metodos()
    test_ctrl_s_sin_cambios_avisa()
    test_f8_fuera_del_modo_dibujo_avisa()
    test_f8_en_modo_dibujo_mantiene_el_mensaje_corto()
    test_exportar_memoria_no_lanza_dos_compilaciones()
    test_f11_no_desincroniza_el_flag_si_tk_rechaza()
    test_la_ventana_de_atajos_nombra_las_teclas_que_existen()
    test_ctrl_e_figura_en_el_menu_donde_realmente_esta()
    test_el_manual_de_usuario_dejo_de_ser_una_promesa()
    test_bind_dialog_keys_ata_solo_lo_pedido()
    test_los_diez_dialogos_responden_a_escape()
    test_los_dos_dialogos_sin_default_seguro_no_atan_return()
    test_material_dialog_no_guarda_con_enter_si_hay_campos_invalidos()
    test_recientes_desambigua_los_nombres_repetidos()
    test_proceso_no_tiene_un_notebook_de_una_sola_pestana()
    test_las_etiquetas_educativas_estan_acentuadas()
    print("=" * 62)
    print("  TODOS LOS TESTS PASARON [21/21]")
    print("=" * 62)
