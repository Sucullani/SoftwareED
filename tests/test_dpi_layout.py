"""
Dimensionado de ventanas contra la pantalla real (sin display).

Cubre la parte que NO necesita Tk del bug de campo 2026-09-09 —"en algunas
pantallas los botones no se ven o quedan cortados" al instalar la aplicacion
en otro equipo—. La causa: toda la GUI estaba dimensionada en pixeles fijos
elegidos sobre el monitor de desarrollo (1366x768 al 100 %), y en un equipo
con escalado de pantalla al 125-200 % Windows le entrega a la aplicacion
—que corre sin conciencia de DPI— un escritorio virtual mucho mas chico:

    1920x1080 al 150 %  ->  1280x720 (area util ~1280x680)
    1920x1080 al 175 %  ->  1097x617 (area util ~1097x577)

Contra eso, `minsize(1200, 700)` en la ventana principal y `geometry(
"760x720")` en ElementTypeDialog no entran, y lo primero que queda fuera de
pantalla es la barra de botones del pie.

Aca se verifica:
  1. La aritmetica pura de `gui.scaling` (`fit_size`, `fit_position`).
  2. Que ninguna ventana del programa fije su tamano a mano: todas pasan por
     el helper, que es el unico que sabe cuanta pantalla hay.
  3. Que ninguna ventana quede `resizable(False, False)` — con el tamano
     recortado, poder agrandarla es la ultima red del alumno.
  4. Que las barras de botones se empaqueten antes que el contenido
     elastico (Tk recorta lo ULTIMO que se empaqueto).

La contraparte con Tk real —abrir cada ventana simulando la pantalla del
equipo del reporte— vive en `tests/test_dpi_layout_gui.py`.

    python -m tests.test_dpi_layout
"""

import ast
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from gui.scaling import (                              # noqa: E402
    ALTO_MINIMO, ANCHO_MINIMO, MARGEN_PANTALLA, fit_position, fit_size,
)

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


# Pantallas reales de los equipos donde la aplicacion se descuadraba.
# (etiqueta, area util)
PANTALLAS = [
    ("1366x768 al 100 % (equipo de desarrollo)", (1366, 728)),
    ("1920x1080 al 150 % -> escritorio 1280x720", (1280, 680)),
    ("1920x1080 al 175 % -> escritorio 1097x617", (1097, 577)),
    ("1366x768 al 125 % -> escritorio 1093x614", (1093, 574)),
]

# Toda ventana del programa: (archivo, ancho, alto) en px de DISENO.
# Si se agrega una ventana nueva, su medida va aca.
VENTANAS = [
    ("gui/dialogs/about_dialog.py", 450, 350),
    ("gui/dialogs/units_dialog.py", 440, 180),
    ("gui/dialogs/gravity_dialog.py", 440, 260),
    ("gui/dialogs/material_dialog.py", 680, 460),
    ("gui/dialogs/element_type_dialog.py", 760, 720),
    ("gui/dialogs/analysis_type_dialog.py", 760, 660),
    ("gui/dialogs/health_report_dialog.py", 780, 620),
    ("gui/dialogs/dxf_import_dialog.py", 760, 500),
    ("gui/dialogs/memoria_style_dialog.py", 460, 210),
    ("education/mod05_stiffness.py", 900, 700),
    ("gui/postprocessing/surface_3d_viewer.py", 900, 700),
]

# Modulos que crean Toplevels y por lo tanto no pueden fijar tamano a mano.
MODULOS_CON_VENTANA = sorted({rel for rel, _, _ in VENTANAS} | {
    "gui/dialogs/pdflatex_missing_dialog.py",
    "gui/main_window.py",
})


# ═════════════════════════════════════════════════════════════════════════
print("\n[1] fit_size: recorta al area util, nunca agranda")

for etiqueta, (aw, ah) in PANTALLAS:
    peor = None
    for rel, ancho, alto in VENTANAS:
        w, h = fit_size(ancho, alto, 1.0, aw, ah)
        if w > aw - MARGEN_PANTALLA or h > ah - MARGEN_PANTALLA:
            peor = f"{rel}: {w}x{h} en un area de {aw}x{ah}"
            break
    check(peor is None, f"toda ventana entra en {etiqueta}", peor or "")

check(fit_size(440, 180, 1.0, 1920, 1040) == (440, 180),
      "una pantalla holgada NO agranda la ventana",
      "fit_size solo debe recortar; agrandar deforma los dialogos chicos")

check(fit_size(760, 720, 1.5, 2560, 1400) == (1140, 1080),
      "el factor de DPI escala las dos medidas",
      f"da {fit_size(760, 720, 1.5, 2560, 1400)}")

check(fit_size(900, 820, 1.0, 200, 150) == (ANCHO_MINIMO, ALTO_MINIMO),
      "por debajo del piso absoluto no se sigue encogiendo",
      f"da {fit_size(900, 820, 1.0, 200, 150)}")


# ═════════════════════════════════════════════════════════════════════════
print("\n[2] fit_position: la ventana entra ENTERA en el area util")

# Barra de tareas arriba: el area util no empieza en (0, 0).
area = (0, 48, 1280, 632)
check(fit_position(-200, -50, 400, 300, area) == (0, 48),
      "una ventana centrada sobre un padre fuera de pantalla se trae adentro")
check(fit_position(1200, 600, 400, 300, area) == (880, 380),
      "una ventana que se pasa por abajo/derecha se corre, no se corta",
      f"da {fit_position(1200, 600, 400, 300, area)}")
x, y = fit_position(100, 100, 2000, 2000, area)
check((x, y) == (0, 48),
      "una ventana mas grande que la pantalla se ancla al origen del area util",
      f"da {(x, y)}")


# ═════════════════════════════════════════════════════════════════════════
print("\n[3] Ninguna ventana fija su tamano a mano")

for rel in MODULOS_CON_VENTANA:
    arbol = ast.parse(_fuente(rel))
    culpables = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        fn = nodo.func
        nombre = fn.attr if isinstance(fn, ast.Attribute) else None
        if nombre not in ("geometry", "minsize", "maxsize"):
            continue
        if not nodo.args:
            continue
        arg = nodo.args[0]
        # `geometry("+x+y")` es reposicionar, no dimensionar: permitido.
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            if nombre == "geometry" and arg.value.startswith("+"):
                continue
            culpables.append(f"{nombre}({arg.value!r})")
        elif isinstance(arg, ast.JoinedStr):
            crudo = "".join(p.value for p in arg.values
                            if isinstance(p, ast.Constant))
            if nombre == "geometry" and crudo.startswith("+"):
                continue
            culpables.append(f"{nombre}(f-string)")
        elif nombre in ("minsize", "maxsize"):
            culpables.append(f"{nombre}(...)")
    if rel == "gui/main_window.py":
        # La ventana principal es la unica que se dimensiona SOLA: se
        # maximiza. Su `minsize(...)` y su `geometry(...)` de respaldo para
        # los WM que rechazan "zoomed" salen de `work_area`, asi que se
        # verifica que consulte el area util en vez de prohibirle medir.
        importados = {alias.name for nodo in ast.walk(arbol)
                      if isinstance(nodo, ast.ImportFrom)
                      and nodo.module == "gui.scaling"
                      for alias in nodo.names}
        check("work_area" in importados,
              "main_window mide contra el area util real",
              "sin work_area el minsize podia ser mayor que la pantalla")
        continue
    check(not culpables,
          f"{os.path.basename(rel)} dimensiona via gui.scaling",
          f"tamano fijado a mano: {culpables}. Usar size_dialog/fit_window: "
          f"son los unicos que saben cuanta pantalla hay.")


# ═════════════════════════════════════════════════════════════════════════
print("\n[4] Ninguna ventana se queda sin poder redimensionarse")

for rel in MODULOS_CON_VENTANA:
    arbol = ast.parse(_fuente(rel))
    congeladas = []
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "resizable"
                and len(nodo.args) == 2
                and all(isinstance(a, ast.Constant) and a.value is False
                        for a in nodo.args)):
            congeladas.append(nodo.lineno)
    check(not congeladas,
          f"{os.path.basename(rel)} no bloquea el redimensionado",
          f"resizable(False, False) en la(s) linea(s) {congeladas}: si el "
          f"tamano se recorta, el alumno no puede recuperar lo que falta.")


# ═════════════════════════════════════════════════════════════════════════
print("\n[5] Las barras de botones se empaquetan ANTES del contenido")

# Tk le da su tamano a lo que se empaqueto PRIMERO y recorta lo ultimo: una
# barra de botones al final del _build es justo lo primero que desaparece.
# (archivo, funcion que construye la ventana, lo fijo, lo elastico)
ORDEN_DE_EMPAQUETADO = [
    ("gui/dialogs/element_type_dialog.py", "_build",
     "_build_footer", "_build_video"),
    ("gui/dialogs/analysis_type_dialog.py", "_build",
     "_build_footer", "_build_video"),
    ("gui/main_window.py", "__init__",
     "_build_status_bar", "_build_main_layout"),
]

for rel, funcion, fijo, elastico in ORDEN_DE_EMPAQUETADO:
    arbol = ast.parse(_fuente(rel))
    llamadas = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.FunctionDef) and nodo.name == funcion:
            for hijo in ast.walk(nodo):
                if (isinstance(hijo, ast.Call)
                        and isinstance(hijo.func, ast.Attribute)
                        and hijo.func.attr.startswith("_build")):
                    llamadas.append(hijo.func.attr)
            break
    ok = (fijo in llamadas and elastico in llamadas
          and llamadas.index(fijo) < llamadas.index(elastico))
    check(ok, f"{os.path.basename(rel)}: {fijo} antes que {elastico}",
          f"orden actual: {llamadas}. Lo ultimo empaquetado es lo primero "
          f"que Tk recorta cuando la ventana no entra en la pantalla.")


# ═════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 62)
if fallos:
    print(f"  {len(fallos)} FALLO(S): " + ", ".join(fallos))
    sys.exit(1)
print("  Dimensionado de ventanas: todo OK")
