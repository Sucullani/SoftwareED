"""
Regresion de `education/components/` y del Theory Hub (area 9 de la rutina de
mejora continua). Sin display: lo que necesita Tk se verifica por inspeccion
de fuente (`ast` / substring), igual que `test_dialogs`; lo que es logica pura
(mapeo inverso, conversion unicode->LaTeX, formateo) se ejecuta de verdad.

Cubre:
  1. `TheoryViewer` no usa `bind_all` para la rueda (el visor NO es modal: con
     la Teoria abierta la rueda sobre el MeshCanvas hacia zoom Y scrolleaba el
     PDF, y el binding global sobrevivia al cierre de la ventana).
  2. `TheoryViewer` cierra con `Escape` via `bind_dialog_keys` y se centra con
     `center_dialog`.
  3. Sin `pdflatex`, el visor abre el MISMO dialogo con boton de descarga que
     la Memoria de Calculo (una sola via para la misma causa).
  4. `TheoryViewer` no le muestra al alumno el nombre-hash del PDF cacheado.
  5. `_hash_doc` no colapsa dos documentos distintos en la misma clave de
     cache cuando `dumps()` falla.
  6. `render_matrix_image` NO cachea su placeholder 1x1: cachearlo dejaba esa
     matriz en blanco para toda la sesion tras un fallo transitorio.
  7. Los `except` que dejaban al alumno sin diagnostico dejan traza.
  8. `Expander` usa `FONT_UI` (no el literal ("Segoe UI", 9) repetido 3 veces).
  9. Helpers puros de `latex_image` (unicode->LaTeX, celdas, shrink) y de
     `quality_bar` (`fmt_es`).
 10. `iso_inverse`: round-trip (xi,eta) -> (x,y) -> (xi,eta) sobre un elemento
     distorsionado, y `element_coords` con un nodo inexistente.

    python -m tests.test_edu_components
"""

import ast
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import numpy as np                                  # noqa: E402

fallos = []


def check(condicion, titulo, detalle=""):
    estado = "OK   " if condicion else "FALLO"
    print(f"  {estado}  {titulo}")
    if not condicion:
        if detalle:
            print(f"         {detalle}")
        fallos.append(titulo)


def _fuente(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8") as f:
        return f.read()


# ═════════════════════════════════════════════════════════════════════════
print("\n[1] TheoryViewer: la rueda NO se ata a toda la aplicacion")

src_viewer = _fuente("education/components/theory_viewer.py")

# Se busca la LLAMADA (`.bind_all(` / `.unbind_all(`), no la palabra: el
# comentario del archivo explica justamente por que no se usa.
check(".bind_all(" not in src_viewer and ".unbind_all(" not in src_viewer,
      "sin bind_all/unbind_all en el visor de Teoria",
      "el visor no es modal: bind_all escribe en el bindtag `all` de la app")
check('self.bind("<MouseWheel>"' in src_viewer,
      "la rueda va atada al Toplevel (cubre todos sus descendientes)")


# ═════════════════════════════════════════════════════════════════════════
print("\n[2] TheoryViewer: Escape cierra y la ventana se centra")

check("bind_dialog_keys" in src_viewer and "on_escape=self.destroy" in src_viewer,
      "Escape cierra, por el helper compartido (no un bind suelto)")
check("center_dialog(self, parent" in src_viewer,
      "se centra con center_dialog (regla dura 19)")
check("on_return" not in src_viewer,
      "NO ata Return: un visor de lectura no tiene accion primaria")


# ═════════════════════════════════════════════════════════════════════════
print("\n[3] Falta pdflatex: una sola via, la de la Memoria")

check("show_pdflatex_missing_dialog" in src_viewer,
      "el visor abre el dialogo con boton de descarga",
      "antes escribia su propio texto en un label del encabezado")

src_pdflatex = _fuente("gui/dialogs/pdflatex_missing_dialog.py")
check("documento: str = " in src_pdflatex,
      "el dialogo nombra el documento pedido (Memoria o Teoria)")
# Los textos que ve el alumno (labels) se arman con {documento}; el docstring
# del modulo sigue nombrando la Memoria como caso principal, y esta bien.
labels_fijos = [ln for ln in src_pdflatex.splitlines()
                if "text=" in ln and "Memoria de Cálculo" in ln]
check(not labels_fijos,
      "ningun label del dialogo dice 'Memoria de Calculo' fijo",
      f"lineas: {labels_fijos}")

arbol_v = ast.parse(src_viewer)
metodos = {n.name for n in ast.walk(arbol_v) if isinstance(n, ast.FunctionDef)}
check("_show_missing_latex" in metodos,
      "el camino de pdflatex faltante vive en su propio metodo")


# ═════════════════════════════════════════════════════════════════════════
print("\n[4] TheoryViewer: la barra de estado no muestra el hash del cache")

check('f"Teoría — {pdf_path.name}"' not in src_viewer,
      "no se muestra el nombre-hash del PDF cacheado",
      "el alumno leia algo como `Teoría — a3f2b9c1d4e5f607.pdf`")
check("página" in src_viewer and "Escape para cerrar" in src_viewer,
      "el estado dice cuantas paginas hay y como cerrar")


# ═════════════════════════════════════════════════════════════════════════
print("\n[5] _hash_doc: un fallo de dumps() no colapsa dos documentos")

from education.components.theory_viewer import _hash_doc   # noqa: E402


class _DocRoto:
    """TheoryDoc doble cuyo `dumps()` revienta."""

    class _Inner:
        @staticmethod
        def dumps():
            raise RuntimeError("dumps roto (a proposito)")

    doc = _Inner()


h1 = _hash_doc(_DocRoto())
h2 = _hash_doc(_DocRoto())
check(h1 != h2,
      "dos documentos que fallan al serializarse NO comparten clave de cache",
      f"{h1!r} == {h2!r}: el segundo mostraria el PDF del primero")


# ═════════════════════════════════════════════════════════════════════════
print("\n[6] latex_image: el placeholder de fallo NO se cachea")

src_latex = _fuente("education/components/latex_image.py")
arbol_l = ast.parse(src_latex)
fn_render = next(n for n in ast.walk(arbol_l)
                 if isinstance(n, ast.FunctionDef) and n.name == "render_matrix_image")
# El handler del except tiene que TERMINAR en un return (sale antes de la
# escritura del cache); si cae por abajo, guarda el 1x1 bajo la clave.
handlers = [h for n in ast.walk(fn_render) if isinstance(n, ast.Try)
            for h in n.handlers]
sale_por_return = any(isinstance(h.body[-1], ast.Return) for h in handlers)
check(sale_por_return,
      "render_matrix_image retorna el placeholder sin escribirlo en _CACHE",
      "cachearlo dejaba esa matriz en blanco para toda la sesion")
check("if cache and renderizo:" in src_latex,
      "render_expression_image tampoco cachea su ultimo recurso 1x1")


# ═════════════════════════════════════════════════════════════════════════
print("\n[7] Los except que dejaban sin diagnostico ahora dejan traza")

check("_trace_once" in src_latex and "_TRACED_FAILURES" in src_latex,
      "latex_image traza UNA vez por firma (las matrices live rendean por frame)")

src_fvb = _fuente("education/components/formula_value_blocks.py")
check(src_fvb.count("traceback.print_exc()") >= 3,
      "FormulaValueBlocksToggle traza el panel que no se construye y los "
      "callbacks de cambio de modo")

src_exp = _fuente("education/components/expander.py")
check("traceback.print_exc()" in src_exp,
      "Expander traza el on_toggle (el body se puebla perezosamente ahi)")


# ═════════════════════════════════════════════════════════════════════════
print("\n[8] Expander: la fuente del header sale de config/settings")

check('font=("Segoe UI"' not in src_exp,
      "ningun widget del Expander lleva la fuente escrita a mano")
check("from config.settings import FONT_UI" in src_exp,
      "usa FONT_UI, la constante que ya define esa fuente")

from education.components.expander import _HEADER_FONT, _HEADER_FONT_HOVER  # noqa: E402
from config.settings import FONT_UI                                        # noqa: E402

check(_HEADER_FONT == FONT_UI, "_HEADER_FONT es FONT_UI")
check(_HEADER_FONT_HOVER == (*FONT_UI, "underline"),
      "el hover solo agrega el subrayado")


# ═════════════════════════════════════════════════════════════════════════
print("\n[9] Helpers puros de latex_image y quality_bar")

from education.components.latex_image import (                  # noqa: E402
    _unicode_math_to_latex, _cell_for_substack_atom,
    _build_substack_matrix_expr, _matrix_to_strings,
    _fit_fontsize_for_shape, _normalize_prefix_fractions,
)
from education.components.quality_bar import fmt_es             # noqa: E402

check(_unicode_math_to_latex("∂N/∂ξ") == r"\partial N/\partial \xi ",
      "unicode math -> comandos LaTeX con separador",
      repr(_unicode_math_to_latex("∂N/∂ξ")))
check(r"\frac" in _unicode_math_to_latex(r"\tfrac{1}{2}"),
      "\\tfrac (que mathtext no conoce) se normaliza a \\frac")
check(_cell_for_substack_atom("") == r"\,",
      "celda vacia conserva la altura de fila")
check(_cell_for_substack_atom("-1.5") == "-1.5",
      "celda numerica pasa tal cual")
check(_cell_for_substack_atom("ux") == r"\mathrm{ux}",
      "texto plano no se italiza")
check(r"\begin{bmatrix}" not in _build_substack_matrix_expr(
          np.array([["1", "2"], ["3", "4"]], dtype=object)),
      "las matrices se arman con \\substack: mathtext no soporta bmatrix")
check(_normalize_prefix_fractions(r"\dfrac{a}{b}") == r"\frac{a}{b}",
      "el prefijo baja de \\dfrac a \\frac (alturas compatibles)")

cells = _matrix_to_strings(np.array([[1.0, -2.5], [0.0, 3.25]]), fmt="{:.3g}")
check(cells is not None and cells.shape == (2, 2) and cells[1, 1] == "3.25",
      "_matrix_to_strings formatea con el fmt pedido")
check(_fit_fontsize_for_shape(2, 4, 14) == 14
      and _fit_fontsize_for_shape(18, 18, 14) < 14,
      "el shrink solo achica las matrices anchas (Q9), no la J 2x2")

check(fmt_es(0.5, 2) == "0,50" and fmt_es(None) == "—",
      "fmt_es usa coma decimal y marca el valor ausente")


# ═════════════════════════════════════════════════════════════════════════
print("\n[10] iso_inverse: round-trip sobre un elemento distorsionado")

from education.components.iso_inverse import (                  # noqa: E402
    iso_inverse_map, natural_to_physical, in_natural_domain, element_coords,
)
from config.settings import ELEMENT_Q4, ELEMENT_Q9               # noqa: E402
from fem.shape_functions import get_shape_functions              # noqa: E402

# El default de element_type tiene que resolver a Q4 de verdad: escrito como
# el literal "Q4" no matcheaba ELEMENT_Q4 y get_shape_functions caia en Q9.
check(len(get_shape_functions(
          iso_inverse_map.__defaults__[0])[0](0.0, 0.0)) == 4,
      "el default de element_type resuelve a las N de Q4 (4 valores)",
      "con el literal 'Q4' devolvia las 9 funciones de forma de Q9")

# Q4 claramente no rectangular (para que el mapeo NO sea afin).
coords = np.array([[0.0, 0.0], [4.0, 0.5], [3.6, 3.2], [0.4, 2.4]])
peor = 0.0
for xi, eta in ((0.0, 0.0), (-0.5, 0.7), (0.9, -0.9), (0.577, 0.577)):
    xy = natural_to_physical(xi, eta, coords, ELEMENT_Q4)
    back = iso_inverse_map(float(xy[0]), float(xy[1]), coords, ELEMENT_Q4)
    if back is None:
        peor = float("inf")
        break
    peor = max(peor, abs(back[0] - xi), abs(back[1] - eta))
check(peor < 1e-9, "round-trip (xi,eta) -> (x,y) -> (xi,eta) exacto",
      f"peor error = {peor}")

fuera = iso_inverse_map(50.0, 50.0, coords, ELEMENT_Q4)
check(fuera is None, "un punto lejos del elemento devuelve None (no extrapola)")
check(in_natural_domain(1.02, 0.0, margin=0.05)
      and not in_natural_domain(1.2, 0.0),
      "in_natural_domain respeta el margen de tolerancia del click")


class _NodoFalso:
    def __init__(self, x, y):
        self.x, self.y = x, y


class _ElemFalso:
    def __init__(self, ids):
        self.node_ids = ids


class _ProyFalso:
    def __init__(self, nodes):
        self.nodes = nodes


proy = _ProyFalso({1: _NodoFalso(0, 0), 2: _NodoFalso(1, 0), 3: _NodoFalso(1, 1)})
check(element_coords(proy, _ElemFalso([1, 2, 3])).shape == (3, 2),
      "element_coords arma la matriz N x 2 desde project.nodes")
check(element_coords(proy, _ElemFalso([1, 2, 99])) is None,
      "element_coords devuelve None si el elemento apunta a un nodo borrado")
check(element_coords(None, None) is None, "element_coords tolera project/elem None")


# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
if fallos:
    print(f"  {len(fallos)} FALLO(S): {', '.join(fallos)}")
    sys.exit(1)
print("  Todos los chequeos de education/components/ pasaron.")
sys.exit(0)
