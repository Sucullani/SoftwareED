"""
Gate de verificacion de EduFEM: una sola orden que la rutina de mejora continua
(docs/rutina/RUTINA.md) debe pasar antes de commitear.

    python -m tests.run_gates              # gate rapido (~1 min, sin pantalla)
    python -m tests.run_gates --con-latex  # + memoria PDF y runtime de LaTeX
    python -m tests.run_gates --con-vv     # + verificacion y validacion (lento)
    python -m tests.run_gates --con-gui    # + tests que necesitan un Tk real

Devuelve 0 si todo pasa y 1 si algo falla, asi que sirve de condicion dura:
sin salida 0 no se pushea.

Los tres niveles existen porque el entorno decide que se puede correr:
- El gate rapido no toca Tk ni pdflatex: corre en cualquier sandbox headless.
- --con-latex necesita el TeX Live embebido (vendor/texlive) o un pdflatex en PATH.
- --con-gui necesita un display: en Windows directo; en Linux,
  `xvfb-run -a python -m tests.run_gates --con-gui`.
Lo que el gate NO puede juzgar es como se VE la aplicacion. Eso queda para el
autor y se anota como pendiente visual en docs/rutina/BACKLOG.md.
"""

import argparse
import importlib
import io
import os
import re
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAQUETES = ("config", "models", "fem", "file_io", "gui", "education")

# Suite sin pantalla ni pdflatex: es el gate obligatorio de toda sesion.
TESTS_RAPIDOS = [
    "tests.test_solver_regression",   # regla dura 21
    "tests.test_fem",                 # regla dura 21
    "tests.test_serialization",
    "tests.test_undo_stack",
    "tests.test_node_cascade",
    "tests.test_noncontiguous_ids",
    "tests.test_unit_conversion",
    "tests.test_q9_q4_cycle",
    "tests.test_probe_query",
    "tests.test_pick_ghost",
    "tests.test_canvas_delete",
    "tests.test_pre_tab_delete",
    "tests.test_canvas_visualization",
    "tests.test_canvas_raster",       # el mas lento del grupo (~26 s)
    "tests.test_vv_extensions",
    "tests.test_interop",
]
TESTS_LATEX = ["tests.test_latex_runtime", "tests.test_memoria_calculo"]
TESTS_VV = ["tests.vv_mms", "tests.vv_timoshenko", "tests.vv_cook"]
TESTS_GUI = ["tests.test_draw_mode", "tests.test_selection_integration"]


def _listar_modulos():
    """Todo modulo .py importable de los paquetes de produccion."""
    mods = set()
    for paquete in PAQUETES:
        for carpeta, _dirs, archivos in os.walk(os.path.join(RAIZ, paquete)):
            if "__pycache__" in carpeta:
                continue
            for archivo in archivos:
                if not archivo.endswith(".py"):
                    continue
                ruta = os.path.relpath(os.path.join(carpeta, archivo), RAIZ)
                nombre = ruta.replace(os.sep, ".")[:-3]
                mods.add(nombre[:-9] if nombre.endswith(".__init__") else nombre)
    return sorted(mods)


def gate_imports():
    """Importa cada modulo del proyecto. No necesita display: los modulos de
    `gui/` y `education/` solo construyen widgets dentro de sus clases.

    Es el gate mas barato y el que atrapa la rotura mas frecuente: una constante
    renombrada en config/settings.py, un import circular nuevo, un typo."""
    fallos = []
    modulos = _listar_modulos()
    for nombre in modulos:
        try:
            importlib.import_module(nombre)
        except Exception as exc:                      # noqa: BLE001 - se reporta
            fallos.append((nombre, f"{type(exc).__name__}: {exc}"))
    return len(modulos), fallos


def gate_hex():
    """Regla dura 2: cero hex literales en codigo ejecutable de gui/ y education/.

    El canon SI admite el hex en comentarios y docstrings (documentar de que color
    se hablaba), asi que el filtro tiene que ser exacto y no heuristico: en Python
    un `#RRGGBB` solo puede vivir dentro de un string o de un comentario, de modo
    que se recorren los tokens, se descartan los COMMENT y los STRING que `ast`
    marca como docstring o string suelto, y lo que queda es codigo de verdad."""
    import ast
    import tokenize

    patron = re.compile(r"#[0-9a-fA-F]{3,8}")
    hallazgos = []
    for paquete in ("gui", "education"):
        for carpeta, _dirs, archivos in os.walk(os.path.join(RAIZ, paquete)):
            if "__pycache__" in carpeta:
                continue
            for archivo in sorted(archivos):
                if not archivo.endswith(".py"):
                    continue
                ruta = os.path.join(carpeta, archivo)
                rel = os.path.relpath(ruta, RAIZ).replace(os.sep, "/")
                with open(ruta, encoding="utf-8") as fh:
                    fuente = fh.read()
                try:
                    arbol = ast.parse(fuente, filename=rel)
                except SyntaxError as exc:
                    hallazgos.append(f"{rel}:{exc.lineno}: no parsea ({exc.msg})")
                    continue
                # Lineas ocupadas por docstrings y strings sueltos usados como nota.
                lineas_doc = set()
                for nodo in ast.walk(arbol):
                    if (isinstance(nodo, ast.Expr)
                            and isinstance(nodo.value, ast.Constant)
                            and isinstance(nodo.value.value, str)):
                        lineas_doc.update(
                            range(nodo.value.lineno, (nodo.value.end_lineno or nodo.value.lineno) + 1))
                for tok in tokenize.generate_tokens(io.StringIO(fuente).readline):
                    if tok.type != tokenize.STRING:
                        continue          # los COMMENT quedan fuera por definicion
                    if tok.start[0] in lineas_doc:
                        continue          # docstring: permitido
                    if patron.search(tok.string):
                        hallazgos.append(f"{rel}:{tok.start[0]}: {tok.line.strip()[:90]}")
    return hallazgos


def _correr(modulo, timeout):
    inicio = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", modulo],
            cwd=RAIZ, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
        return proc.returncode, time.time() - inicio, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, time.time() - inicio, f"TIMEOUT tras {timeout} s"


def main():
    ap = argparse.ArgumentParser(description="Gate de verificacion de EduFEM")
    ap.add_argument("--con-latex", action="store_true", help="suma memoria PDF y LaTeX")
    ap.add_argument("--con-vv", action="store_true", help="suma V&V (lento)")
    ap.add_argument("--con-gui", action="store_true", help="suma tests que abren un Tk")
    ap.add_argument("--timeout", type=int, default=900, help="segundos por test")
    args = ap.parse_args()

    print("=" * 70)
    print("  GATE DE EduFEM")
    print("=" * 70)

    fallas = []

    print("\n[1] Importacion de todos los modulos")
    total, fallos_import = gate_imports()
    if fallos_import:
        print(f"  FALLO  {len(fallos_import)}/{total} modulos no importan")
        for nombre, err in fallos_import:
            print(f"         {nombre} -> {err}")
        fallas.append("imports")
    else:
        print(f"  OK     {total}/{total} modulos importan")

    print("\n[2] Auditoria de color (regla dura 2: cero hex fuera de config/)")
    hex_hits = gate_hex()
    if hex_hits:
        print(f"  FALLO  {len(hex_hits)} hex literales en codigo ejecutable")
        for hit in hex_hits[:20]:
            print(f"         {hit}")
        fallas.append("hex")
    else:
        print("  OK     0 hex literales en gui/ y education/")

    suite = list(TESTS_RAPIDOS)
    if args.con_latex:
        suite += TESTS_LATEX
    if args.con_vv:
        suite += TESTS_VV
    if args.con_gui:
        suite += TESTS_GUI

    print(f"\n[3] Suite de tests ({len(suite)} modulos)")
    for modulo in suite:
        rc, seg, salida = _correr(modulo, args.timeout)
        estado = "OK    " if rc == 0 else "FALLO "
        print(f"  {estado} {modulo:<34} {seg:6.1f} s")
        if rc != 0:
            fallas.append(modulo)
            for linea in salida.strip().splitlines()[-15:]:
                print(f"         | {linea}")

    print("\n" + "=" * 70)
    if fallas:
        print(f"  GATE ROJO: {len(fallas)} fallo(s) -> {', '.join(fallas)}")
        print("  NO se commitea ni se pushea con el gate en rojo.")
        print("=" * 70)
        return 1
    print("  GATE VERDE: todo paso.")
    print("  Recorda que esto NO valida como se VE la app: el chequeo visual")
    print("  es del autor (docs/rutina/BACKLOG.md, seccion Pendientes visuales).")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
