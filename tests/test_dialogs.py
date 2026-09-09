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
print("\n[1] about_dialog: center_dialog importado")

arbol = ast.parse(_fuente("gui/dialogs/about_dialog.py"))
importados = set()
for nodo in ast.walk(arbol):
    if isinstance(nodo, (ast.Import, ast.ImportFrom)):
        for alias in nodo.names:
            importados.add(alias.asname or alias.name.split(".")[0])
check("center_dialog" in importados,
      "about_dialog importa center_dialog",
      "sin el import, Ayuda > Acerca de levanta NameError al centrarse")


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
print("\n[5] HealthReportDialog: '📍 Ir al item' de un material")

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
print("\n" + "=" * 62)
if fallos:
    print(f"  {len(fallos)} FALLO(S): {', '.join(fallos)}")
    sys.exit(1)
print("  Todos los chequeos de gui/dialogs/ pasaron.")
sys.exit(0)
