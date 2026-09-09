"""
Regresion de los modulos educativos M0..M3 y de su clase base
(`education/overlay_module.py`) — area 7 de la rutina de mejora continua.

Sin display: los modulos se instancian con `object.__new__` + dobles minimos
(igual que `test_dialogs`, `test_main_window`, `test_post_inspection`), y los
invariantes de codigo se verifican leyendo la fuente.

Cubre:
  1. Estado «esperando elemento»: con `element is None`, M2 y M3 NO muestran
     los numeros del elemento anterior ni una `J` de relleno (era la matriz
     IDENTIDAD, que se leia como un Jacobiano valido), y el titulo del panel
     nombra el estado + el gesto que lo resuelve.
  2. `on_element_deselected` esta sobrescrito en M1, M2 y M3: sin eso, el
     overlay seguia mostrando el elemento que el alumno acababa de
     deseleccionar (y M2, su aviso rojo de elemento degenerado).
  3. `JacobianModule._refresh_warning` BORRA el aviso cuando no hay elemento.
  4. La nota de remision de M2 ya no manda a M4 (que desde el swap B<->D de
     2026-05 es la matriz D y no tiene ninguna derivada de N).
  5. Cero literales de color con NOMBRE ("white" / "black") en los 5 archivos
     del area (regla dura 2; `run_gates.gate_hex` solo ve los `#RRGGBB`).
  6. Las coords (x, y) del marcador fisico de M2 pasan por `fmt` (regla dura 8).
  7. M0 no le habla al alumno en ingles ("hover").
  8. `overlay_module` deja traza en los `except` que dejaban al modulo inerte,
     y la traza de la capa de dibujo esta acotada a UNA por instancia (M3
     redibuja a ~30 fps).

    python -m tests.test_edu_modules_m0_m3
"""

import os
import sys

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from config.settings import ELEMENT_Q4                     # noqa: E402
from education.mod01_iso_mapping import IsoMappingModule    # noqa: E402
from education.mod02_jacobian import JacobianModule        # noqa: E402
from education.mod03_b_matrix import BMatrixModule         # noqa: E402
from education.mod00_mesh_quality import MeshQualityModule  # noqa: E402
from education.overlay_module import CanvasOverlayModule   # noqa: E402

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

class MatrizFalsa:
    """Doble de LatexMatrixImage / ScrollableMatrixImage."""

    def __init__(self, inicial=None):
        self.matriz = inicial

    def set_matrix(self, matriz, **_kw):
        self.matriz = matriz


class LabelFalso:
    def __init__(self):
        self.texto = None
        self.fg = None

    def configure(self, **kw):
        if "text" in kw:
            self.texto = kw["text"]
        if "fg" in kw:
            self.fg = kw["fg"]
        if "foreground" in kw:
            self.fg = kw["foreground"]


class MallaFalsa:
    """MeshCanvas minimo: solo cuenta los redraw pedidos."""

    def __init__(self):
        self.redraws = 0

    def redraw(self):
        self.redraws += 1


class ProyectoFalso:
    element_type = ELEMENT_Q4

    def __init__(self):
        self.elements = {}
        self.nodes = {}


def _m2_sin_elemento():
    """JacobianModule en estado «esperando elemento», sin Tk."""
    m = object.__new__(JacobianModule)
    m.project = ProyectoFalso()
    m.element = None
    m.element_id = None
    m._xi = m._eta = 0.0
    m._gauss_index = None
    m._free_point = False
    m._mesh = MallaFalsa()
    m._ax_nat = None
    m._ax_3d = None
    m._canvas_mpl = None
    m._surf_cache = None
    m._surf_cache_key = None
    m._xe_element_id = 7           # un elemento "anterior"
    m._lbl_values_title = LabelFalso()
    m._lbl_warning = LabelFalso()
    m._mat_dN = MatrizFalsa(np.full((2, 4), 9.0))
    m._mat_Xe = MatrizFalsa(np.full((4, 2), 9.0))
    m._mat_values = MatrizFalsa(np.full((2, 2), 9.0))
    return m


def _m3_sin_elemento():
    """BMatrixModule en estado «esperando elemento», sin Tk."""
    m = object.__new__(BMatrixModule)
    m.project = ProyectoFalso()
    m.element = None
    m.element_id = None
    m._xi = m._eta = 0.0
    m._gauss_index = None
    m._free_point = False
    m._mesh = MallaFalsa()
    m._ax_nat = None
    m._canvas_mpl = None
    m._lbl_values_title = LabelFalso()
    m._mat_dN_nat = MatrizFalsa(np.full((2, 4), 9.0))
    m._mat_invJ = MatrizFalsa(np.full((2, 2), 9.0))
    m._mat_dN_phys = MatrizFalsa(np.full((2, 4), 9.0))
    m._mat_values = MatrizFalsa(np.full((3, 8), 9.0))
    m._mat_formula = None
    return m


# ═════════════════════════════════════════════════════════════════════════
print("\n=== 1. Estado «esperando elemento»: M2 no miente ===")

m2 = _m2_sin_elemento()
m2._refresh_all()

check(np.allclose(m2._mat_values.matriz, 0.0),
      "sin elemento, la J del panel Valores queda en CEROS",
      f"J -> {m2._mat_values.matriz}")
check(np.allclose(m2._mat_dN.matriz, 0.0) and np.allclose(m2._mat_Xe.matriz, 0.0),
      "sin elemento, dN y Xe tampoco conservan los numeros anteriores")
check(m2._lbl_values_title.texto is not None
      and "sin elemento" in m2._lbl_values_title.texto
      and "lienzo" in m2._lbl_values_title.texto,
      "el titulo nombra el estado y el gesto (no «centro del elemento»)",
      f"titulo -> {m2._lbl_values_title.texto!r}")
check("centro del elemento" not in (m2._lbl_values_title.texto or ""),
      "el titulo NO habla del centro de un elemento inexistente")

fuente_m2 = _fuente("education/mod02_jacobian.py")
check("np.eye(2)" not in fuente_m2,
      "el placeholder de J ya no es la matriz IDENTIDAD",
      "una J = I de relleno se lee como un Jacobiano valido (det J = 1)")


print("\n=== 2. El aviso de elemento degenerado se borra ===")

m2b = _m2_sin_elemento()
m2b._lbl_warning.texto = ("⚠ Elemento degenerado: det J ≤ 0 en pg1 (-0.5). "
                          "Reordená los nodos en CCW o corregí la geometría.")
m2b._refresh_warning()
check(m2b._lbl_warning.texto == "",
      "_refresh_warning BORRA el aviso cuando no hay elemento",
      f"aviso -> {m2b._lbl_warning.texto!r}")


print("\n=== 3. Estado «esperando elemento»: M3 no miente ===")

m3 = _m3_sin_elemento()
m3._refresh_all()

check(all(np.allclose(w.matriz, 0.0) for w in
          (m3._mat_dN_nat, m3._mat_invJ, m3._mat_dN_phys, m3._mat_values)),
      "sin elemento, la cadena dN_xieta / J^-1 / dN_xy / B queda en CEROS")
check(m3._lbl_values_title.texto is not None
      and "sin elemento" in m3._lbl_values_title.texto,
      "el titulo de B nombra el estado",
      f"titulo -> {m3._lbl_values_title.texto!r}")


print("\n=== 4. on_element_deselected sobrescrito en M1, M2 y M3 ===")

for nombre, cls in (("M1", IsoMappingModule), ("M2", JacobianModule),
                    ("M3", BMatrixModule)):
    propio = ("on_element_deselected" in vars(cls))
    check(propio,
          f"{nombre} sobrescribe on_element_deselected",
          "sin eso el overlay sigue mostrando el elemento deseleccionado")

# El efecto, medido: M3 con un elemento "anterior" vuelve a ceros y a estado.
m3b = _m3_sin_elemento()
m3b.element_id, m3b.element = 3, object()
m3b._gauss_index, m3b._free_point = 1, False
m3b._xi, m3b._eta = 0.577, -0.577
m3b.on_element_deselected()
check(m3b.element is None and m3b.element_id is None
      and m3b._gauss_index is None and not m3b._free_point
      and m3b._xi == 0.0 and m3b._eta == 0.0,
      "M3.on_element_deselected limpia elemento, punto y PG")
check(all(np.allclose(w.matriz, 0.0) for w in
          (m3b._mat_dN_nat, m3b._mat_invJ, m3b._mat_dN_phys, m3b._mat_values)),
      "y deja las cuatro matrices en ceros (no los valores del elemento ido)")

m1 = object.__new__(IsoMappingModule)
m1.project = ProyectoFalso()
m1.element_id, m1.element = 3, object()
m1._mode = "snap_node"
m1._node_idx = 3
m1._sel_xi, m1._sel_eta = -1.0, 1.0
m1._lbl_mode = LabelFalso()
m1._ax_nat = None          # _redraw corta temprano sin Tk
m1._mesh = MallaFalsa()
m1.on_element_deselected()
check(m1._mode == "init" and m1.element is None,
      "M1.on_element_deselected vuelve al modo inicial")
check(m1._lbl_mode.texto is not None and "Clickeá" in m1._lbl_mode.texto,
      "y la linea de estado vuelve a la invitacion (no «nodo 3»)",
      f"estado -> {m1._lbl_mode.texto!r}")


print("\n=== 5. Notas de remision: el modulo que se nombra existe ===")

check("las formulas de dNi/dxi se ven en M1 y M4" not in fuente_m2,
      "M2 ya no manda las formulas de dNi/dxi a M4 (hoy es la matriz D)")
check("ver ① Mapeo iso" in fuente_m2,
      "M2 nombra el modulo con la etiqueta que el alumno ve en el boton")
fuente_m3 = _fuente("education/mod03_b_matrix.py")
check("ver ① Mapeo iso" in fuente_m3,
      "M3 usa la misma remision que M2 (una sola forma de nombrar el modulo)")


print("\n=== 6. Regla dura 2: cero literales de color con nombre ===")

ARCHIVOS_AREA = (
    "education/mod00_mesh_quality.py",
    "education/mod01_iso_mapping.py",
    "education/mod02_jacobian.py",
    "education/mod03_b_matrix.py",
    "education/overlay_module.py",
)
for rel in ARCHIVOS_AREA:
    src = _fuente(rel)
    sucios = [lit for lit in ('"white"', "'white'", '"black"', "'black'")
              if lit in src]
    check(not sucios, f"{rel}: sin literales de color con nombre",
          f"quedan {sucios}")

check("EDU_NODE_INDEX_FG_COLOR" in _fuente("config/settings.py"),
      "la constante del numero de nodo vive en config/settings.py")


print("\n=== 7. Regla dura 8: las coords (x, y) de M2 pasan por fmt ===")

check("fmt(xy_sel[0], 'length')" in fuente_m2,
      "el marcador fisico de M2 formatea (x, y) con fmt(..., 'length')")
check('f"(x, y) = ({xy_sel[0]:.3g}' not in fuente_m2,
      "ya no usa el :.3g local (decimales distintos a los del lienzo)")


print("\n=== 8. Espanol en los strings del alumno ===")

fuente_m0 = _fuente("education/mod00_mesh_quality.py")
check("(hover sobre un elemento" not in fuente_m0,
      "M0 no le dice «hover» al alumno")
check("Pasá el cursor sobre un elemento" in fuente_m0,
      "lo dice en espanol")


print("\n=== 9. overlay_module: los except que dejaban el modulo inerte ===")

fuente_ov = _fuente("education/overlay_module.py")
check("import traceback" in fuente_ov,
      "overlay_module importa traceback")
# Contrato: los hooks del ciclo de vida y de la cadena de seleccion trazan.
bloques = fuente_ov.split("except Exception")
mudos = sum(1 for b in bloques[1:] if b.lstrip(":\n ").startswith("pass"))
check(mudos <= 6,
      "la mayoria de los except del ciclo de vida dejan traza",
      f"quedan {mudos} mudos (antes 17)")
for nombre in ("self.on_activated()", "self.on_closed()",
               "_self.on_element_selected(eid)",
               "_self.on_element_deselected()",
               "open_module(self.main_window"):
    idx = fuente_ov.find(nombre)
    cola = fuente_ov[idx: idx + 900] if idx >= 0 else ""
    check(idx >= 0 and "traceback.print_exc()" in cola,
          f"deja traza el except de {nombre}")

check("_layer_error_traced" in fuente_ov,
      "la traza de la capa de dibujo esta acotada a UNA por instancia",
      "draw_canvas_layer corre en cada redraw y M3 lo llama a ~30 fps")

# El guard existe antes de que la capa pueda correr (se fija en __init__).
src_init = fuente_ov.split("def __init__", 1)[1].split("\n    # ──", 1)[0]
check("_layer_error_traced = False" in src_init,
      "el guard se inicializa en __init__ (la capa se registra ahi mismo)")


print("\n=== 10. El contrato del area no se movio ===")

check(MeshQualityModule.OVERLAY_WIDTH == 470 and MeshQualityModule.PHASE == "pre",
      "M0 conserva 470 px y fase pre")
check(IsoMappingModule.OVERLAY_WIDTH == 500
      and JacobianModule.OVERLAY_WIDTH == 740
      and BMatrixModule.OVERLAY_WIDTH == 720,
      "M1/M2/M3 conservan sus anchos (500 / 740 / 720)")
check(all(c.PHASE == "proc" for c in
          (IsoMappingModule, JacobianModule, BMatrixModule)),
      "M1/M2/M3 siguen en la fase proc")
check(all(c.OVERLAY_INITIAL_POS == (24, 24) for c in
          (MeshQualityModule, IsoMappingModule, JacobianModule, BMatrixModule)),
      "los cuatro abren en (24, 24)")
check(all(issubclass(c, CanvasOverlayModule) for c in
          (MeshQualityModule, IsoMappingModule, JacobianModule, BMatrixModule)),
      "los cuatro siguen siendo overlays (no Toplevel)")
check(BMatrixModule.TITLE.startswith("③") and JacobianModule.TITLE.startswith("②")
      and IsoMappingModule.TITLE.startswith("①"),
      "la numeracion visible sigue siendo M1=iso, M2=Jacobiano, M3=B")
for rel in ARCHIVOS_AREA[:4]:
    src = _fuente(rel)
    check("mesh.canvas.delete(_TAG)" in src or "canvas.delete(_TAG)" in src,
          f"{rel}: draw_canvas_layer sigue borrando su propio tag")


# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
if fallos:
    print(f"  {len(fallos)} FALLO(S): {', '.join(fallos)}")
    sys.exit(1)
print("  Todos los chequeos de los modulos educativos M0..M3 pasaron.")
sys.exit(0)
