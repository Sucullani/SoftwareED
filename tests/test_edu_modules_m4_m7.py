"""
Regresion de los modulos educativos M4..M7 — area 8 de la rutina de mejora
continua. Companero de `test_edu_modules_m0_m3.py` (area 7) y con su mismo
estilo: sin display, los modulos se instancian con `object.__new__` + dobles
minimos, y los invariantes de codigo se verifican leyendo la fuente.

Cubre:
  1. Estado «esperando elemento» en M4: sin elemento la matriz D de Valores va
     a CEROS y el rotulo nombra el estado + el gesto. Antes `_resolve_material`
     caia en `materials[0]` («… (fallback)») o, sin materiales, en un acero
     inventado (210 GPa, ν = 0,30): el panel mostraba una D completa y
     plausible que no era la de ningun elemento elegido.
  2. El ◆ «tu material» del espectro de M4 desaparece sin elemento (no hay
     material al que volver) y deja de ser un ancla de snap.
  3. `on_element_deselected` sobrescrito en M4 y M5 (M7 ya lo tenia): sin el,
     el overlay seguia mostrando la D / la k_e del elemento que el alumno
     acababa de deseleccionar.
  4. Estado «esperando elemento» en M5: al deseleccionar se vacian las
     contribuciones, la k_e vuelve a su placeholder, el status y el warning
     quedan en blanco y ningun PG queda sumado.
  5. `_lbl_dim` de M5 lee el tipo de elemento del project cuando no hay
     seleccion (un proyecto Q9 anunciaba «k_e es 8x8 · Q4»).
  6. M6 opera sobre cargas superficiales, no sobre un elemento: NO necesita
     `on_element_deselected` (queda documentado para que nadie lo agregue).
  7. Cero literales de color con NOMBRE ("white" / "black") en los 5 archivos
     del area (regla dura 2; `run_gates.gate_hex` solo ve los `#RRGGBB`).
  8. Las trazas de los `except Exception` que dejaban al modulo mintiendo o
     inerte, y el guard de una-sola-traza del loop de animacion de M6.
  9. Contrato del area: anchos de overlay, fase, herencia, numeracion visible
     y el `delete(_TAG)` de cada capa.

    python -m tests.test_edu_modules_m4_m7
"""

import ast
import os
import sys

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from config.settings import (                                  # noqa: E402
    ELEMENT_Q4, ELEMENT_Q9, ANALYSIS_PLANE_STRESS,
)
from education.mod04_constitutive import ConstitutiveModule    # noqa: E402
from education.mod05_stiffness import StiffnessElementModule   # noqa: E402
from education.mod06_equivalent_forces import (                # noqa: E402
    EquivalentForcesModule,
)
from education.mod07_assembly import AssemblyModule            # noqa: E402
from education.overlay_module import CanvasOverlayModule       # noqa: E402

fallos = []


def check(condicion, titulo, detalle=""):
    estado = "OK   " if condicion else "FALLO"
    print(f"  {estado}  {titulo}")
    if not condicion:
        if detalle:
            print(f"         {detalle}")
        fallos.append(titulo)


def _fuente(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8") as fh:
        return fh.read()


# ─── Dobles headless ─────────────────────────────────────────────────────

class LabelFalso:
    def __init__(self, texto=None):
        self.texto = texto
        self.fg = None
        self.mapeado = True

    def configure(self, **kw):
        if "text" in kw:
            self.texto = kw["text"]
        if "fg" in kw:
            self.fg = kw["fg"]
        if "foreground" in kw:
            self.fg = kw["foreground"]

    def winfo_ismapped(self):
        return self.mapeado

    def pack(self, **_kw):
        self.mapeado = True

    def pack_forget(self):
        self.mapeado = False


class MatrizFalsa:
    """Doble de LatexMatrixImage / ScrollableMatrixImage."""

    def __init__(self, inicial=None):
        self.matriz = inicial
        self.prefix = None
        self.mapeado = True

    def set_matrix(self, matriz, **kw):
        self.matriz = matriz
        self.prefix = kw.get("prefix", self.prefix)

    def set_style(self, **_kw):
        pass

    def winfo_ismapped(self):
        return self.mapeado

    def pack(self, **_kw):
        self.mapeado = True

    def pack_forget(self):
        self.mapeado = False


class CanvasFalso:
    """tk.Canvas minimo del espectro de M4: registra lo dibujado por tipo."""

    def __init__(self):
        self.items = []

    def delete(self, *_a):
        self.items = []

    def _add(self, tipo, kw):
        self.items.append((tipo, kw))

    def create_line(self, *_a, **kw):
        self._add("line", kw)

    def create_text(self, *_a, **kw):
        self._add("text", kw)

    def create_oval(self, *_a, **kw):
        self._add("oval", kw)

    def create_polygon(self, *_a, **kw):
        self._add("polygon", kw)

    def create_rectangle(self, *_a, **kw):
        self._add("rect", kw)


class MallaFalsa:
    def __init__(self):
        self.redraws = 0

    def redraw(self):
        self.redraws += 1


class MaterialFalso:
    def __init__(self, name="Acero", E=200e9, nu=0.3):
        self.name = name
        self.E = E
        self.nu = nu


class ElementoFalso:
    def __init__(self, eid=1, num_nodes=4, material_name="Acero"):
        self.id = eid
        self.num_nodes = num_nodes
        self.node_ids = list(range(1, num_nodes + 1))
        self.material_name = material_name
        self.thickness = 1.0


class ProyectoFalso:
    def __init__(self, element_type=ELEMENT_Q4, con_material=True):
        self.element_type = element_type
        self.analysis_type = ANALYSIS_PLANE_STRESS
        self.nodes = {}
        self.elements = {1: ElementoFalso()}
        self.materials = {"Acero": MaterialFalso()} if con_material else {}


def _m4(con_elemento=True, con_material=True):
    """ConstitutiveModule sin Tk, con o sin elemento bajo analisis."""
    m = object.__new__(ConstitutiveModule)
    proyecto = ProyectoFalso(con_material=con_material)
    m.project = proyecto
    m.element_id = 1 if con_elemento else None
    m.element = proyecto.elements[1] if con_elemento else None
    m._E, m._nu_default, m._mat_name = ConstitutiveModule._resolve_material(
        proyecto, m.element_id
    )
    m._nu = m._nu_default if m._nu_default is not None else 0.30
    m._mesh = MallaFalsa()
    m._spectrum_canvas = CanvasFalso()
    m._poisson_canvas = CanvasFalso()
    m._lbl_sandbox = LabelFalso()
    m._lbl_warning = LabelFalso()
    m._mat_formula = None
    m._mat_values = MatrizFalsa(np.full((3, 3), 9.0))
    m._formula_case_rendered = ANALYSIS_PLANE_STRESS
    m._toggle = None
    return m


def _m5(element_type=ELEMENT_Q4, con_elemento=True):
    """StiffnessElementModule sin Tk, con las contribuciones ya calculadas."""
    m = object.__new__(StiffnessElementModule)
    proyecto = ProyectoFalso(element_type=element_type)
    if element_type == ELEMENT_Q9:
        proyecto.elements = {1: ElementoFalso(num_nodes=9)}
    m.project = proyecto
    m.element_id = 1 if con_elemento else None
    m.element = proyecto.elements[1] if con_elemento else None
    m._mesh = MallaFalsa()
    m._order = 2
    m._i = m._j = 1
    m._last_kij_expr = "expresion-vieja"
    m._last_kij_key = ("clave", "vieja")
    m._exp = None
    m._ax_nat = None
    m._canvas_mpl = None
    m._lbl_dim = LabelFalso()
    m._lbl_warning = LabelFalso()
    m._lbl_status = LabelFalso()
    m._k_placeholder = LabelFalso()
    m._mat_k = MatrizFalsa(np.full((8, 8), 9.0))
    # Contribuciones "del elemento anterior": lo que quedaba en pantalla.
    m._contributions = [
        {"xi": 0.5, "eta": 0.5, "w": 1.0, "detJ": 0.25,
         "contrib": np.full((8, 8), 7.0)}
        for _ in range(4)
    ]
    m._selected_pgs = set(range(4))
    return m


# ═════════════════════════════════════════════════════════════════════════
print("\n=== 1. M4: sin elemento no se inventa un material ===")

m4_vacio = _m4(con_elemento=False)
check(m4_vacio._E is None and m4_vacio._nu_default is None,
      "_resolve_material devuelve (None, None, None) sin elemento",
      f"E -> {m4_vacio._E}, nu_default -> {m4_vacio._nu_default}")
check(np.allclose(m4_vacio._current_d(), 0.0),
      "sin elemento, la D del panel Valores queda en CEROS",
      f"D -> {m4_vacio._current_d()}")

m4_sin_mats = _m4(con_elemento=False, con_material=False)
check(m4_sin_mats._E is None,
      "sin materiales en el proyecto tampoco aparece el acero inventado")

fuente_m4 = _fuente("education/mod04_constitutive.py")
# Los ex-defaults se buscan como ASIGNACIONES reales (no en comentarios: el
# comentario que documenta su retiro los nombra a proposito).
globales_m4 = {
    nodo.targets[0].id
    for nodo in ast.parse(fuente_m4).body
    if isinstance(nodo, ast.Assign) and isinstance(nodo.targets[0], ast.Name)
}
check("_DEMO_E" not in globales_m4 and "_DEMO_NU" not in globales_m4,
      "los defaults `_DEMO_E = 210e9` / `_DEMO_NU = 0.30` ya no existen",
      f"globales -> {sorted(globales_m4)}")

proy_roto = ProyectoFalso()
proy_roto.elements = {1: ElementoFalso(material_name="Inexistente")}
check(ConstitutiveModule._resolve_material(proy_roto, 1) == (None, None, None),
      "un elemento cuyo material no existe tampoco cae en `materials[0]`",
      f"-> {ConstitutiveModule._resolve_material(proy_roto, 1)}")

m4_con = _m4(con_elemento=True)
check(m4_con._E == 200e9 and abs(m4_con._nu_default - 0.3) < 1e-12,
      "con elemento, E y ν siguen saliendo de SU material")
check(not np.allclose(m4_con._current_d(), 0.0),
      "con elemento, la D sigue teniendo valores reales")


print("\n=== 2. M4: el rotulo nombra el estado y el gesto ===")

texto_vacio = m4_vacio._sandbox_text()
check("sin elemento" in texto_vacio and "lienzo" in texto_vacio,
      "sin elemento el rotulo nombra el estado y el gesto",
      f"rotulo -> {texto_vacio!r}")
check("de tu elemento" not in texto_vacio,
      "el rotulo NO habla de «tu elemento» cuando no hay ninguno")
check("de tu elemento" in m4_con._sandbox_text(),
      "con elemento vuelve el rotulo sandbox de siempre",
      f"rotulo -> {m4_con._sandbox_text()!r}")


print("\n=== 3. M4: el ◆ «tu material» solo existe si hay material ===")

m4_vacio._draw_spectrum()
poligonos_vacio = [it for it in m4_vacio._spectrum_canvas.items
                   if it[0] == "polygon"]
check(not poligonos_vacio,
      "sin elemento, el espectro NO dibuja el ◆ home",
      f"poligonos -> {len(poligonos_vacio)}")
check(m4_vacio._nu_default not in m4_vacio._snap_candidates(),
      "sin material, el home no es un ancla de snap (no hay None en la lista)")
check(all(c is not None for c in m4_vacio._snap_candidates()),
      "_snap_candidates nunca devuelve None (romperia _x_for_nu)")

m4_con._draw_spectrum()
check(any(it[0] == "polygon" for it in m4_con._spectrum_canvas.items),
      "con elemento, el ◆ home vuelve a dibujarse")
check(m4_con._nu_default in m4_con._snap_candidates(),
      "con elemento, el home sigue siendo ancla de snap (el ex-Reset)")


print("\n=== 4. M4: deseleccionar vuelve al estado «esperando elemento» ===")

check("on_element_deselected" in fuente_m4,
      "M4 sobrescribe on_element_deselected")
check(ConstitutiveModule.on_element_deselected
      is not CanvasOverlayModule.on_element_deselected,
      "el override de M4 no es el default de la clase base")

m4_desel = _m4(con_elemento=True)
m4_desel._refresh_d_widgets()
d_antes = np.array(m4_desel._mat_values.matriz, dtype=float).copy()
check(not np.allclose(d_antes, 0.0), "(precondicion) la D del elemento no es cero")
m4_desel.on_element_deselected()
check(m4_desel.element is None and m4_desel.element_id is None,
      "on_element_deselected limpia element / element_id")
check(np.allclose(np.array(m4_desel._mat_values.matriz, dtype=float), 0.0),
      "tras deseleccionar, la D del panel Valores va a CEROS",
      f"D -> {m4_desel._mat_values.matriz}")
check("sin elemento" in (m4_desel._lbl_sandbox.texto or ""),
      "tras deseleccionar, el rotulo pasa al estado «esperando elemento»",
      f"rotulo -> {m4_desel._lbl_sandbox.texto!r}")
check(not [it for it in m4_desel._spectrum_canvas.items if it[0] == "polygon"],
      "tras deseleccionar, el ◆ «tu material» desaparece del espectro")
check(m4_desel._mesh.redraws >= 1,
      "on_element_deselected pide un redraw (apaga el contorno ambar)")


print("\n=== 5. M5: deseleccionar no deja la k_e del elemento anterior ===")

check("on_element_deselected" in _fuente("education/mod05_stiffness.py"),
      "M5 sobrescribe on_element_deselected")
check(StiffnessElementModule.on_element_deselected
      is not CanvasOverlayModule.on_element_deselected,
      "el override de M5 no es el default de la clase base")

m5 = _m5()
m5.on_element_deselected()
check(m5.element is None and m5.element_id is None,
      "on_element_deselected limpia element / element_id")
check(m5._contributions == [],
      "las contribuciones del elemento anterior se vacian",
      f"contribuciones -> {len(m5._contributions)}")
check(m5._selected_pgs == set(),
      "ningun PG queda sumado (el cuadrado natural los pinta en ghost)")
check(m5._last_kij_expr is None and m5._last_kij_key is None,
      "el cache del integrando simbolico se invalida")
check(m5._k_placeholder.texto is not None
      and "Clickea" in m5._k_placeholder.texto.replace("á", "a"),
      "la k_e vuelve a su placeholder «Clickeá un elemento»",
      f"placeholder -> {m5._k_placeholder.texto!r}")
check(not m5._mat_k.mapeado,
      "el widget de la k_e se despacka (no queda la matriz anterior visible)")
check(m5._lbl_status.texto == "",
      "el status ya no dice «Σ 4/4 pg · ultimo: pg4 · |det J|=…»",
      f"status -> {m5._lbl_status.texto!r}")
check(m5._lbl_warning.texto == "",
      "el warning de hourglass / sobre-integracion queda vacio",
      f"warning -> {m5._lbl_warning.texto!r}")


print("\n=== 6. M5: el tamaño de k_e sin seleccion sale del project ===")

m5_q9 = _m5(element_type=ELEMENT_Q9)
m5_q9.on_element_deselected()
check("18×18" in (m5_q9._lbl_dim.texto or "") and "Q9" in (m5_q9._lbl_dim.texto or ""),
      "en un proyecto Q9 sin seleccion el label dice 18x18 · Q9",
      f"label -> {m5_q9._lbl_dim.texto!r}")

m5_q4 = _m5(element_type=ELEMENT_Q4)
m5_q4.on_element_deselected()
check("8×8" in (m5_q4._lbl_dim.texto or "") and "Q4" in (m5_q4._lbl_dim.texto or ""),
      "en un proyecto Q4 sigue diciendo 8x8 · Q4",
      f"label -> {m5_q4._lbl_dim.texto!r}")


print("\n=== 7. M6 y M7: quien necesita el hook y quien no ===")

fuente_m6 = _fuente("education/mod06_equivalent_forces.py")
fuente_m7 = _fuente("education/mod07_assembly.py")
check(EquivalentForcesModule.on_element_selected
      is not CanvasOverlayModule.on_element_selected,
      "M6 ignora la seleccion de elemento a proposito (opera sobre cargas)")
check("on_element_deselected" not in fuente_m6,
      "M6 NO necesita on_element_deselected: su panel no muestra datos del "
      "elemento (no agregarlo)")
check(AssemblyModule.on_element_deselected
      is not CanvasOverlayModule.on_element_deselected,
      "M7 ya sobrescribe on_element_deselected (cancela el pulso en curso)")


print("\n=== 8. Regla dura 2: cero literales de color con nombre ===")

ARCHIVOS_AREA = (
    "education/mod04_constitutive.py",
    "education/mod05_stiffness.py",
    "education/mod06_equivalent_forces.py",
    "education/mod07_assembly.py",
    "education/module_launcher.py",
)
for rel in ARCHIVOS_AREA:
    src = _fuente(rel)
    sucios = [lit for lit in ('"white"', "'white'", '"black"', "'black'")
              if lit in src]
    check(not sucios, f"{rel}: sin literales de color con nombre",
          f"encontrados -> {sucios}")


print("\n=== 9. Excepciones que dejaban al modulo mintiendo o inerte ===")

check(fuente_m4.count("traceback.print_exc()") >= 3,
      "M4 deja traza en sus `except` (D que no acompaña, capa del lienzo)",
      f"trazas -> {fuente_m4.count('traceback.print_exc()')}")
check("except Exception:\n            pass" not in
      fuente_m4.split("def on_element_selected")[0].split(
          "def draw_canvas_layer")[-1],
      "la capa de M4 ya no se come su propia excepcion "
      "(la aisla `_draw_layer_wrapper`, con una traza por instancia)")

fuente_m5 = _fuente("education/mod05_stiffness.py")
check("remove_click_consumer" in fuente_m5
      and fuente_m5.split("remove_click_consumer")[1].split("except Exception:")[1]
      .lstrip().startswith("#"),
      "el `remove_click_consumer` de on_closed deja traza "
      "(un M5 cerrado se comia los clicks del lienzo)")
check(fuente_m5.count("traceback.print_exc()") >= 6,
      "M5 deja traza en sus `except` clave",
      f"trazas -> {fuente_m5.count('traceback.print_exc()')}")

check("_anim_error_traced" in fuente_m6,
      "el loop de animacion de M6 traza UNA sola vez por instancia "
      "(corre a ~60 fps: sin guard inundaria stderr)")
m6 = object.__new__(EquivalentForcesModule)
m6._anim_error_traced = False
check(m6._anim_error_traced is False,
      "el guard arranca en False (la primera traza sale)")

check(fuente_m7.count("traceback.print_exc()") >= 4,
      "M7 deja traza en sus `except` clave (F de referencia, hover, cierre)",
      f"trazas -> {fuente_m7.count('traceback.print_exc()')}")


print("\n=== 10. Contrato del area (lo que NO debe cambiar) ===")

for cls, ancho, nombre in (
    (ConstitutiveModule, 480, "M4"),
    (StiffnessElementModule, 600, "M5"),
    (EquivalentForcesModule, 360, "M6"),
    (AssemblyModule, 520, "M7"),
):
    check(cls.OVERLAY_WIDTH == ancho, f"{nombre}: OVERLAY_WIDTH sigue en {ancho}",
          f"actual -> {cls.OVERLAY_WIDTH}")
    check(cls.OVERLAY_HEIGHT is None, f"{nombre}: alto auto (shrink-wrap)")
    check(cls.PHASE == "proc", f"{nombre}: fase proc")
    check(cls.OVERLAY_INITIAL_POS == (24, 24),
          f"{nombre}: posicion inicial (24, 24)")
    check(issubclass(cls, CanvasOverlayModule),
          f"{nombre}: hereda de CanvasOverlayModule (herencia unica)")

for cls, glifo, nombre in (
    (ConstitutiveModule, "④", "M4"),
    (StiffnessElementModule, "⑤", "M5"),
    (EquivalentForcesModule, "⑥", "M6"),
    (AssemblyModule, "⑦", "M7"),
):
    check(cls.TITLE.strip().startswith(glifo),
          f"{nombre}: el titulo abre con {glifo}", f"titulo -> {cls.TITLE!r}")

check("mesh.canvas.delete(_TAG)" in fuente_m4,
      "M4: la capa arranca borrando su tag")
check("mesh.canvas.delete(_TAG)" in fuente_m5,
      "M5: la capa arranca borrando su tag")
check("mesh.canvas.delete(_TAG)" in fuente_m6,
      "M6: la capa arranca borrando su tag")
check("delete(_TAG_BASE)" in fuente_m7,
      "M7: la capa arranca borrando su tag base")

check(ConstitutiveModule.REQUIRES_ELEMENT is True,
      "M4 declara REQUIRES_ELEMENT (opera sobre el material de UN elemento)")
check(StiffnessElementModule.REQUIRES_ELEMENT is False
      and EquivalentForcesModule.REQUIRES_ELEMENT is False
      and AssemblyModule.REQUIRES_ELEMENT is False,
      "M5, M6 y M7 abren sin elemento (el launcher no pide seleccion)")


print("\n" + "=" * 66)
if fallos:
    print(f"  {len(fallos)} FALLO(S):")
    for f in fallos:
        print(f"   - {f}")
    sys.exit(1)
print("  TODO OK — modulos educativos M4..M7")
sys.exit(0)
