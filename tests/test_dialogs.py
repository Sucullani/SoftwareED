"""
Regresion de los dialogos de `gui/dialogs/` (area 5 de la rutina de mejora
continua). Sin display: los dialogos se instancian con `object.__new__` y
dobles minimos, igual que hacen `test_canvas_delete`, `test_pre_tab_delete`,
`test_solve_flow` y `test_post_inspection`.

Cubre:
  1. `about_dialog` importa `center_dialog` (Ayuda > Acerca de levantaba
     NameError en el callback de Tk).
  2. `MaterialDialog` acepta la coma decimal y dice CUAL campo esta mal.
  3. `MaterialDialog` cuenta los elementos que se quedan sin material.
  4. `MaterialDialog(seleccionar=...)` preselecciona el material del issue.
  5. `HealthReportDialog._on_goto` deriva los issues de material a Materiales
     en vez de quedarse mudo, y avisa cuando no sabe navegar.
  6. `HealthReportDialog._on_fix` avisa cuando el auto-fix no se aplica.
  7. `HealthReportDialog` no usa `bind_all` / `unbind_all` (el dialogo es
     no-modal: secuestraba la rueda de toda la aplicacion).
  8. `DxfImportDialog._on_import` captura el undo ANTES de reescalar las
     coordenadas por cambio de unidad (regla dura 4).
  9. `GravityDialog` acepta la coma decimal y nombra el campo rechazado.

    python -m tests.test_dialogs
"""

import ast
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from models.project import ProjectModel            # noqa: E402
from models.material import Material               # noqa: E402
from models.model_health import (                  # noqa: E402
    HealthIssue, HealthCode, Severity,
)

fallos = []


def check(condicion, titulo, detalle=""):
    estado = "OK   " if condicion else "FALLO"
    print(f"  {estado}  {titulo}")
    if not condicion:
        if detalle:
            print(f"         {detalle}")
        fallos.append(titulo)


# ─── Dobles ──────────────────────────────────────────────────────────────

class VarFalsa:
    """Reemplazo headless de tk.StringVar."""

    def __init__(self, valor=""):
        self._v = valor

    def get(self):
        return self._v

    def set(self, valor):
        self._v = valor


class BotonFalso:
    def __init__(self):
        self.estado = None

    def configure(self, **kw):
        if "state" in kw:
            self.estado = kw["state"]

    config = configure


class EntryFalso:
    def __init__(self):
        self.bootstyle = None

    def configure(self, **kw):
        self.bootstyle = kw.get("bootstyle", self.bootstyle)


class VentanaFalsa:
    """Doble de MainWindow: solo `undo_stack` y `set_status`."""

    def __init__(self):
        self.mensajes = []
        self.undo_stack = None
        self.root = None

    def set_status(self, texto):
        self.mensajes.append(texto)

    def _refresh_all_tabs(self):
        pass

    def _update_status_info(self):
        pass

    def _update_title(self):
        pass

    @property
    def ultimo(self):
        return self.mensajes[-1] if self.mensajes else ""


def proyecto_con_material():
    p = ProjectModel()
    p.materials = {"Acero": Material("Acero", 200000.0, 0.3, 7.85e-9)}
    p.add_node(0.0, 0.0)
    p.add_node(1.0, 0.0)
    p.add_node(1.0, 1.0)
    p.add_node(0.0, 1.0)
    p.add_element([1, 2, 3, 4], 1.0, "Acero")
    return p


def _fuente(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8") as fh:
        return fh.read()


# ═════════════════════════════════════════════════════════════════════════
print("\n[1] about_dialog: size_dialog importado")

arbol = ast.parse(_fuente("gui/dialogs/about_dialog.py"))
importados = set()
for nodo in ast.walk(arbol):
    if isinstance(nodo, (ast.Import, ast.ImportFrom)):
        for alias in nodo.names:
            importados.add(alias.asname or alias.name.split(".")[0])
check("size_dialog" in importados,
      "about_dialog importa size_dialog",
      "sin el import, Ayuda > Acerca de levanta NameError al dimensionarse")


# ═════════════════════════════════════════════════════════════════════════
print("\n[2] MaterialDialog: coma decimal y campo culpable")

from gui.dialogs.material_dialog import MaterialDialog       # noqa: E402

md = object.__new__(MaterialDialog)
md.project = proyecto_con_material()
md.main_window = VentanaFalsa()
md.selected_name = "Acero"
md._suppress_preview = False
md.var_name = VarFalsa("Acero")
md.var_E = VarFalsa("200000")
md.var_nu = VarFalsa("0,3")          # coma decimal de un Excel en español
md.var_density = VarFalsa("7.85e-9")
md.save_btn = BotonFalso()
md._entries = {c: EntryFalso() for c in ("name", "E", "nu", "density")}

check(md.campos_invalidos() == [],
      "nu = '0,3' se acepta (antes: Guardar gris para siempre)",
      f"campos_invalidos() -> {md.campos_invalidos()}")

md._validate_live()
check(md.save_btn.estado == "normal",
      "Guardar habilitado con la coma decimal")

md.var_nu.set("0,9")                 # fuera de (-1, 0.5): invalido de verdad
check(md.campos_invalidos() == ["nu"],
      "nu = 0,9 se rechaza y se nombra solo ese campo",
      f"campos_invalidos() -> {md.campos_invalidos()}")
md._validate_live()
check(md.save_btn.estado == "disabled",
      "Guardar deshabilitado con nu fuera de rango")
check(md._entries["nu"].bootstyle == "danger"
      and md._entries["E"].bootstyle != "danger",
      "solo el Entry culpable queda marcado en rojo",
      f"nu -> {md._entries['nu'].bootstyle}, E -> {md._entries['E'].bootstyle}")

md.var_nu.set("0.3")
md.var_E.set("-5")
check(md.campos_invalidos() == ["E"], "E <= 0 se rechaza")
md.var_E.set("hola")
check(md.campos_invalidos() == ["E"], "E no numerico se rechaza")
md.var_E.set("200000")
md.var_name.set("   ")
check(md.campos_invalidos() == ["name"], "nombre vacio se rechaza")


# ═════════════════════════════════════════════════════════════════════════
print("\n[3] MaterialDialog: el borrado nombra los elementos afectados")

fuente_mat = _fuente("gui/dialogs/material_dialog.py")
fuente_mat_12 = fuente_mat
check("e.material_name == self.selected_name" in fuente_mat,
      "_remove_material cuenta los elementos que usan el material")
check("sin material" in fuente_mat,
      "la confirmacion nombra la consecuencia del borrado")

p = proyecto_con_material()
en_uso = sum(1 for e in p.elements.values() if e.material_name == "Acero")
check(en_uso == 1, "el conteo de uso funciona sobre el modelo real",
      f"esperado 1, obtenido {en_uso}")


# ═════════════════════════════════════════════════════════════════════════
print("\n[4] MaterialDialog(seleccionar=...) preselecciona")

import inspect                                              # noqa: E402
firma = inspect.signature(MaterialDialog.__init__)
check("seleccionar" in firma.parameters,
      "MaterialDialog acepta `seleccionar`")
check(firma.parameters["seleccionar"].kind is inspect.Parameter.KEYWORD_ONLY,
      "`seleccionar` es keyword-only (no rompe los 3 llamadores posicionales)")


# ═════════════════════════════════════════════════════════════════════════
print("\n[5] HealthReportDialog: 'Ir al item' de un material")

from gui.dialogs.health_report_dialog import HealthReportDialog   # noqa: E402

abiertos = []


class SaludParaGoto(HealthReportDialog):
    def _abrir_materiales(self, nombre):
        abiertos.append(nombre)


hd = object.__new__(SaludParaGoto)
hd.project = proyecto_con_material()
hd.main_window = VentanaFalsa()
hd.parent = None
hd.fixes_applied = 0

issue_mat = HealthIssue(
    severity=Severity.WARNING, code=HealthCode.GRAVITY_NO_DENSITY,
    message="Gravedad activa pero el material 'Acero' tiene densidad = 0.",
    target_kind="material", target_id="Acero", fixable=False,
)
hd._on_goto(issue_mat)
check(abiertos == ["Acero"],
      "un issue de material abre Materiales (antes: el boton no hacia nada)",
      f"abiertos -> {abiertos}")

# Un kind desconocido tiene que avisar, no quedarse mudo.
hd.main_window = VentanaFalsa()


class NotebookFalso:
    def select(self, _i):
        pass


hd.main_window.notebook = NotebookFalso()
hd.main_window.pre_tab = object()
issue_raro = HealthIssue(
    severity=Severity.WARNING, code=HealthCode.SUMMARY,
    message="x", target_kind="galaxia", target_id=7,
)
hd._on_goto(issue_raro)
check("galaxia" in hd.main_window.ultimo,
      "un target_kind desconocido lo dice en la barra de estado",
      f"ultimo -> {hd.main_window.ultimo!r}")


# ═════════════════════════════════════════════════════════════════════════
print("\n[6] HealthReportDialog: el auto-fix que falla ya no es mudo")

import gui.dialogs.health_report_dialog as mod_salud          # noqa: E402

original_autofix = mod_salud.apply_autofix


class TarjetaFalsa:
    _hint_btn = None

    def winfo_children(self):
        return []

    def configure(self, **kw):
        pass


try:
    mod_salud.apply_autofix = lambda _p, _i: False
    hf = object.__new__(HealthReportDialog)
    hf.project = proyecto_con_material()
    hf.main_window = VentanaFalsa()
    hf.parent = None
    hf.fixes_applied = 0
    hf._on_fix(issue_mat, TarjetaFalsa())
    check(hf.fixes_applied == 0, "un fix fallido no incrementa el contador")
    check("No se pudo aplicar" in hf.main_window.ultimo,
          "un fix fallido lo explica en la barra de estado",
          f"ultimo -> {hf.main_window.ultimo!r}")

    mod_salud.apply_autofix = lambda _p, _i: True
    hf2 = object.__new__(HealthReportDialog)
    hf2.project = proyecto_con_material()
    hf2.main_window = VentanaFalsa()
    hf2.parent = None
    hf2.fixes_applied = 0
    hf2._on_fix(issue_mat, TarjetaFalsa())
    check(hf2.fixes_applied == 1, "un fix aplicado incrementa el contador")
    check("Re-validar" in hf2.main_window.ultimo,
          "tras corregir se nombra el boton que actualiza el reporte",
          f"ultimo -> {hf2.main_window.ultimo!r}")
finally:
    mod_salud.apply_autofix = original_autofix


# ═════════════════════════════════════════════════════════════════════════
print("\n[7] HealthReportDialog: la rueda no se ata a toda la aplicacion")

fuente_salud = _fuente("gui/dialogs/health_report_dialog.py")
check("bind_all(" not in fuente_salud,
      "sin bind_all: el dialogo es no-modal y secuestraba la rueda del canvas")
check("unbind_all(" not in fuente_salud,
      "sin unbind_all: al cerrar borraba el binding global de otros widgets")
check('self.dialog.bind("<MouseWheel>"' in fuente_salud,
      "la rueda se ata al Toplevel del dialogo (cubre sus descendientes)")


# ═════════════════════════════════════════════════════════════════════════
print("\n[8] DxfImportDialog: undo ANTES de reescalar las coordenadas")

fuente_dxf = _fuente("gui/dialogs/dxf_import_dialog.py")
cuerpo = fuente_dxf[fuente_dxf.index("def _on_import"):]
pos_capture = cuerpo.index('stack.capture("importar DXF")')
pos_convert = cuerpo.index("self._apply_project_unit()")
check(pos_capture < pos_convert,
      "stack.capture() precede a _apply_project_unit() (regla dura 4)",
      "capturar despues dejaba la reescala de unidades fuera del Ctrl+Z")

# `_apply_project_unit` es realmente una mutacion del modelo.
from gui.dialogs.dxf_import_dialog import _convert_project_coords  # noqa: E402

pd = proyecto_con_material()
antes = pd.nodes[2].x
factor = _convert_project_coords(pd, "m", "mm")
check(abs(factor - 1000.0) < 1e-9 and abs(pd.nodes[2].x - antes * 1000.0) < 1e-9,
      "_convert_project_coords muta las coordenadas de los nodos",
      f"factor {factor}, x {antes} -> {pd.nodes[2].x}")


# ═════════════════════════════════════════════════════════════════════════
print("\n[9] GravityDialog: coma decimal y campo nombrado")

from gui.dialogs.gravity_dialog import GravityDialog          # noqa: E402

gd = object.__new__(GravityDialog)
gd.project = proyecto_con_material()
gd.main_window = None
gd.gx_var = VarFalsa("0")
gd.gy_var = VarFalsa("-9,81")
gd.include_var = VarFalsa(True)
gd._gx_live = 0.0
gd._gy_live = 0.0


class CanvasNulo:
    def redraw_overlays_only(self):
        pass


gd._get_canvas = lambda: CanvasNulo()
gd._on_field_changed()
check(abs(gd._gy_live + 9.81) < 1e-12,
      "el preview en vivo lee gy = '-9,81' con coma",
      f"_gy_live -> {gd._gy_live}")

fuente_grav = _fuente("gui/dialogs/gravity_dialog.py")
check("to_float_flex" in fuente_grav,
      "gravity_dialog usa to_float_flex (una sola regla de numero en la app)")
check("float(self.gx_var.get().replace" not in fuente_grav,
      "no queda el parseo a mano con .replace(',', '.')")
check('f"{clave}: «{var.get()}»"' in fuente_grav,
      "el error nombra el campo y el texto rechazado")


# ═════════════════════════════════════════════════════════════════════════
print("\n[10] MaterialDialog: cambiar un material invalida la solucion")

# Regla dura 12. `post_tab._auto_solve` corta con
#   if self.solution is not None and self.project.is_solved: return
# asi que sin el `is_solved = False` el alumno bajaba E a la decima parte,
# apretaba F5 y veia EXACTAMENTE las mismas tensiones, sin ningun aviso; y
# "Exportar Memoria PDF" seguia habilitado (`_refresh_menu_state` mira
# `is_solved`) sobre esa corrida vieja.

class VentanaContadora(VentanaFalsa):
    """VentanaFalsa que ademas cuenta los refrescos."""

    def __init__(self):
        super().__init__()
        self.n_refresh = 0
        self.n_status_info = 0

    def _refresh_all_tabs(self):
        self.n_refresh += 1

    def _update_status_info(self):
        self.n_status_info += 1


class MessageboxFalso:
    def __init__(self, respuesta=True):
        self.respuesta = respuesta
        self.askyesno_calls = []

    def askyesno(self, titulo, mensaje, **_kw):
        self.askyesno_calls.append((titulo, mensaje))
        return self.respuesta

    def showerror(self, *a, **kw):
        pass

    def showwarning(self, *a, **kw):
        pass


def _material_headless(project, ventana):
    d = object.__new__(MaterialDialog)
    d.project = project
    d.main_window = ventana
    d.parent = None
    d.dialog = None
    d.selected_name = None
    d._suppress_preview = False
    d.var_name = VarFalsa()
    d.var_E = VarFalsa()
    d.var_nu = VarFalsa()
    d.var_density = VarFalsa()
    d.save_btn = BotonFalso()
    d._entries = {c: EntryFalso() for c in ("name", "E", "nu", "density")}
    d._row_widgets = {}
    d._populate_list = lambda: None      # necesita widgets reales
    return d


def _resuelto():
    proj = proyecto_con_material()
    proj.is_solved = True
    proj.is_modified = False
    return proj


# --- editar E ---
ventana = VentanaContadora()
proj = _resuelto()
med = _material_headless(proj, ventana)
med.selected_name = "Acero"
med.var_name.set("Acero")
med.var_E.set("20000")               # una decima parte: otra K
med.var_nu.set("0.3")
med.var_density.set("7.85e-9")

import gui.dialogs.material_dialog as _mat_mod                # noqa: E402
_mbox_original = _mat_mod.messagebox
_mat_mod.messagebox = MessageboxFalso()
try:
    med._save_material()
finally:
    _mat_mod.messagebox = _mbox_original

check(proj.materials["Acero"].E == 20000.0,
      "editar E guarda el valor nuevo",
      f"E -> {proj.materials['Acero'].E}")
check(proj.is_solved is False,
      "editar un material invalida la solucion (regla dura 12)",
      "is_solved quedo en True: F5 devolveria las tensiones del material viejo")
check(proj.is_modified is True, "editar un material marca el proyecto sucio")
check(ventana.n_status_info == 1,
      "el badge de salud se recalcula tras editar",
      f"_update_status_info llamado {ventana.n_status_info} vez/veces")
check(bool(ventana.mensajes),
      "la edicion se anuncia en la barra de estado",
      "era el unico dialogo del menu Modelo que no decia nada")

# --- agregar ---
proj = _resuelto()
_material_headless(proj, VentanaContadora())._add_material()
check(proj.is_solved is False and proj.is_modified is True,
      "agregar un material invalida la solucion",
      f"is_solved -> {proj.is_solved}")

# --- borrar ---
proj = _resuelto()
proj.materials["Suplente"] = Material("Suplente", 1000.0, 0.2, 1.0)
med = _material_headless(proj, VentanaContadora())
med.selected_name = "Suplente"
_mat_mod.messagebox = MessageboxFalso(respuesta=True)
try:
    med._remove_material()
finally:
    _mat_mod.messagebox = _mbox_original
check("Suplente" not in proj.materials, "borrar un material lo saca de la libreria")
check(proj.is_solved is False and proj.is_modified is True,
      "borrar un material invalida la solucion",
      f"is_solved -> {proj.is_solved}")

# --- los tres flujos pasan por _mark_dirty, no por is_modified suelto ---
check(fuente_mat_12.count("self.project.is_modified = True") == 1,
      "un solo lugar setea is_modified: _mark_dirty()",
      "quedan asignaciones sueltas que pueden volver a olvidar is_solved")
check("self.project.is_solved = False" in fuente_mat_12,
      "_mark_dirty invalida la solucion")


# ═════════════════════════════════════════════════════════════════════════
print("\n[11] pdflatex_missing_dialog: el boton de descarga no puede ser mudo")

fuente_tex = _fuente("gui/dialogs/pdflatex_missing_dialog.py")
check("abierto = webbrowser.open" in fuente_tex,
      "se mira el retorno de webbrowser.open (False = no abrio nada)")
check("if not abierto:" in fuente_tex and "showinfo" in fuente_tex,
      "si no abrio el navegador, muestra la URL para copiar a mano",
      "este dialogo aparece cuando el alumno YA esta bloqueado")


# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
if fallos:
    print(f"  {len(fallos)} FALLO(S): {', '.join(fallos)}")
    sys.exit(1)
print("  Todos los chequeos de gui/dialogs/ pasaron.")
sys.exit(0)
