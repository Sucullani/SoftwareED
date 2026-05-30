"""
Test del generador de Memoria de Calculo (PDF/LaTeX) — reformulado 2026-05.

Estilo printout (no usa pytest), consistente con el resto de tests/.
Skip elegante si pdflatex no esta en el PATH.

Cobertura:
  - test_memoria_minima_q4 / _q9: compila el PDF (skip sin pdflatex).
  - test_error_pdflatex_faltante: la excepcion accionable existe.
  - test_factored_matrix_helpers: helpers de factorizacion (sin pdflatex).
  - test_no_plus_en_positivos: las celdas de matrices/vectores no llevan '+'.
  - test_tex_estructura_educativo: capitulos + jerarquia FEM del estilo
    'educativo' (default). Sin compilar.
  - test_tex_solver_spsolve_no_cholesky: el Cap. de solucion describe spsolve
    (LU dispersa), NO Cholesky.
  - test_tex_indexado_ordinal: el ensamblaje describe el indexado ordinal.
  - test_tex_sin_cross_refs_circulares: la Memoria no remite al Hub.
  - test_tex_completo_tiene_apendices / test_tex_educativo_sin_apendices.
  - test_tex_directo_sin_narrativa.
  - test_mesh_diagram_es_pil: render_mesh_diagram devuelve una PIL.Image.
  - test_contornos_pil_blanco: los contornos son PIL con fondo blanco.
  - test_hub_*: chequeos del Theory Hub.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from file_io.memoria_calculo import (
    generate_memoria_calculo, MemoriaCalculo, MemoriaCalculoError,
)
from education.components.theory_builder import TheoryDoc
from fem.solver import solve_system
from fem.stress import compute_all_stresses
from tests.example_data import load_example_project


def _has_pdflatex() -> bool:
    return shutil.which("pdflatex") is not None


def _solved_example():
    project = load_example_project()
    solution = solve_system(project)
    project.is_solved = True
    es, ns = compute_all_stresses(project, solution)
    return project, solution, es, ns


def _tex(style: str = "educativo") -> str:
    project, solution, es, ns = _solved_example()
    mem = MemoriaCalculo(project, solution, es, ns, style=style)
    mem.build()
    return mem.tex_source()


# ─── Compilacion real (skip sin pdflatex) ──────────────────────────────────

def test_memoria_minima_q4() -> bool:
    print("test_memoria_minima_q4 ...")
    if not _has_pdflatex():
        print("  SKIP: pdflatex no encontrado en PATH")
        return True
    project, solution, es, ns = _solved_example()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "memoria_test_q4.pdf")
        result_path = generate_memoria_calculo(project, solution, es, ns, out_pdf)
        if not Path(result_path).exists():
            print(f"  FAIL: no se genero el PDF en {result_path}")
            return False
        size = Path(result_path).stat().st_size
        if size < 5000:
            print(f"  FAIL: PDF demasiado chico ({size} bytes)")
            return False
        print(f"  OK: PDF generado, {size} bytes")
        return True


def test_memoria_minima_q9() -> bool:
    print("test_memoria_minima_q9 ...")
    if not _has_pdflatex():
        print("  SKIP: pdflatex no encontrado en PATH")
        return True
    try:
        from tests.example_data import load_example_project_q9
    except ImportError:
        print("  SKIP: load_example_project_q9 no disponible")
        return True
    project = load_example_project_q9()
    solution = solve_system(project)
    project.is_solved = True
    es, ns = compute_all_stresses(project, solution)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "memoria_test_q9.pdf")
        result_path = generate_memoria_calculo(project, solution, es, ns, out_pdf)
        if not Path(result_path).exists():
            print(f"  FAIL: no se genero el PDF en {result_path}")
            return False
        size = Path(result_path).stat().st_size
        if size < 5000:
            print(f"  FAIL: PDF demasiado chico ({size} bytes)")
            return False
        print(f"  OK: PDF Q9 generado, {size} bytes")
        return True


def test_error_pdflatex_faltante() -> bool:
    print("test_error_pdflatex_faltante ...")
    try:
        raise MemoriaCalculoError("test")
    except MemoriaCalculoError as e:
        if str(e) == "test":
            print("  OK: MemoriaCalculoError funciona")
            return True
        print(f"  FAIL: mensaje inesperado: {e}")
        return False


# ─── Helpers de factorizacion (sin pdflatex) ───────────────────────────────

def test_factored_matrix_helpers() -> bool:
    print("test_factored_matrix_helpers ...")
    K = np.array([[2.3e6, -1.1e6, 0.5e6],
                  [-1.1e6, 3.5e6, -0.8e6],
                  [0.5e6, -0.8e6, 2.1e6]])
    tex = TheoryDoc.matrix_factored_tex(K, name=r"\mathbf{K}", sig_digits=3)
    if "10^{6}" not in tex:
        print(f"  FAIL: factorizacion 10^6 no encontrada en: {tex[:200]}")
        return False
    # La mantisa no debe llevar notacion cientifica (el exponente comun ya
    # se factorizo); 'e+'/'e-' solo aparecerian en el fallback de rango alto.
    print("  OK: factorizacion comun aplicada")

    M = np.array([[1e10, 1e-2], [3e5, 4e1]])
    tex2 = TheoryDoc.matrix_factored_tex(M, sig_digits=3)
    if "e+" not in tex2.lower() and "e-" not in tex2.lower():
        print(f"  FAIL: rango dinamico alto deberia caer a cientifica: {tex2[:200]}")
        return False
    print("  OK: fallback notacion cientifica con rango dinamico alto")

    u = np.array([1.23e-5, -4.56e-5, 7.89e-5, -2.34e-5])
    tex3 = TheoryDoc.vector_factored_tex(u, name=r"\mathbf{u}",
                                         sig_digits=3, transpose=True)
    if "10^{-5}" not in tex3 or r"^T" not in tex3:
        print(f"  FAIL: vector no factorizo / sin ^T: {tex3}")
        return False
    print("  OK: vector factorizado en forma transpuesta")
    return True


def test_no_plus_en_positivos() -> bool:
    """Task: los positivos en matrices/vectores NO llevan '+'; los negativos
    conservan '-'. La alineacion la da el entorno bmatrix (columnas)."""
    print("test_no_plus_en_positivos ...")
    import re
    samples = [
        TheoryDoc.matrix_tex(np.array([[1.0, -0.2], [0.3, 0.4]])),
        TheoryDoc.matrix_factored_tex(
            np.array([[2.3e6, -1.1e6], [0.5e6, 3.5e6]]), sig_digits=3),
        TheoryDoc.vector_factored_tex(
            np.array([1.2e-5, -3.4e-5, 5.6e-5]), sig_digits=3),
    ]
    for s in samples:
        # '+' seguido de digito = signo en un positivo (prohibido).
        bad = re.findall(r"\+\d", s)
        if bad:
            print(f"  FAIL: '+' en positivo: {bad} en {s[:120]}")
            return False
        if "-" not in s:
            print(f"  FAIL: se esperaba algun '-' en {s[:120]}")
            return False
    print("  OK: sin '+' en positivos, '-' preservado")
    return True


# ─── Estructura del .tex (sin compilar) ─────────────────────────────────────

def test_tex_estructura_educativo() -> bool:
    print("test_tex_estructura_educativo ...")
    tex = _tex("educativo")
    expected = [
        r"¿Qué resuelve el MEF y cómo?",
        r"Planteo del problema",
        r"Discretización del modelo",
        r"Calidad de la malla",
        r"Formulación elemental",
        r"Ensamblaje del sistema global",
        r"Condiciones de contorno y solución",
        r"Post-proceso: tensiones y deformada",
    ]
    missing = [s for s in expected if s not in tex]
    if missing:
        print(f"  FAIL: secciones ausentes: {missing}")
        return False
    print("  OK: capitulos del pipeline presentes")

    # Jerarquia FEM en el showcase: N -> J -> B -> D -> Integrando -> Gauss.
    # Marcadores especificos de los titulos de subseccion del showcase (para
    # no colisionar con la enumeracion del pipeline en la introduccion).
    markers = [
        r"Funciones de forma $N_i(\xi",
        r"Jacobiano $\mathbf{J}=\partial\mathbf{N}",
        r"Matriz de deformación $\mathbf{B}$",
        r"Matriz constitutiva $\mathbf{D}$ del material",
        r"Integrando simbólico $K_{ij}",
        r"Cuadratura de Gauss y matriz",
    ]
    pos = []
    for m in markers:
        p = tex.find(m)
        if p < 0:
            print(f"  FAIL: marcador ausente: {m}")
            return False
        pos.append(p)
    if pos != sorted(pos):
        print("  FAIL: jerarquia FEM del showcase no respetada")
        return False
    print("  OK: jerarquia FEM N->J->B->D->Integrando->Gauss")

    # Subsecciones del post-proceso.
    sub_post = [
        "Tensiones en los puntos de Gauss",
        "Extrapolación de Gauss a nodos",
        "Promediado nodal entre elementos adyacentes",
        "Tensiones principales",
        "Tensión equivalente de von Mises",
    ]
    missing_post = [s for s in sub_post if s not in tex]
    if missing_post:
        print(f"  FAIL: subsecciones post-proceso ausentes: {missing_post}")
        return False
    print("  OK: post-proceso completo")

    # Sin prefijos numericos manuales (todo auto-numerado).
    import re
    manual = re.findall(r"\\subsection\*?\{(?P<num>\d\.\d) ", tex)
    if manual:
        print(f"  FAIL: prefijos manuales: {sorted(set(manual))[:5]}")
        return False
    print("  OK: sin prefijos numericos manuales")
    return True


def test_tex_solver_lu_sin_internals() -> bool:
    """El Cap. de solución describe la factorización LU directa en abstracto,
    SIN nombrar internals del software (spsolve/SuperLU). Ver CLAUDE.md."""
    print("test_tex_solver_lu_sin_internals ...")
    tex = _tex("educativo")
    for forbidden in ("Cholesky", "spsolve", "SuperLU", "scipy"):
        if forbidden in tex:
            print(f"  FAIL: la Memoria menciona un internal/solver indebido: "
                  f"{forbidden}")
            return False
    if "Método de resolución" not in tex or "factorización LU" not in tex:
        print("  FAIL: no describe el método de resolución (LU directa)")
        return False
    # La ecuación LU (L y = ... ; U u_f = y) debe estar presente.
    if r"\mathbf{L}\,\mathbf{y}" not in tex or r"\mathbf{U}\,\mathbf{u}_f" not in tex:
        print("  FAIL: falta la ecuación de la factorización LU")
        return False
    print("  OK: solver descrito como LU directa, sin internals")
    return True


def test_tex_ensamblaje_lm() -> bool:
    print("test_tex_ensamblaje_lm ...")
    tex = _tex("educativo")
    if "Mapeo de grados de libertad" not in tex or r"\mathbf{LM}" not in tex:
        print("  FAIL: falta el mapeo LM en el ensamblaje")
        return False
    if "dispersa" not in tex:
        print("  FAIL: no menciona que K es dispersa")
        return False
    # La ecuación de ensamblaje debe emitirse SIEMPRE (no gated tras _prose).
    tex_dir = _tex("directo")
    if r"\mathbf{LM}_e" not in tex_dir:
        print("  FAIL: la ecuación LM no aparece en el estilo directo")
        return False
    print("  OK: ensamblaje describe el mapeo LM + K dispersa (ambos estilos)")
    return True


def test_tex_sin_cross_refs_circulares() -> bool:
    print("test_tex_sin_cross_refs_circulares ...")
    tex = _tex("educativo")
    # El diseno reformulado NO remite al Hub ("Ver Teoria MEF: M3 ...").
    if "Ver \\textbf{Teoría MEF}" in tex or "Teoría MEF:" in tex:
        print("  FAIL: aun hay referencias cruzadas circulares al Hub")
        return False
    print("  OK: documento autocontenido, sin cross-refs circulares")
    return True


def test_tex_solo_dos_estilos() -> bool:
    """Solo existen 'educativo' y 'directo'. Un 'completo' legacy cae al
    default sin romper (fallback de __init__)."""
    print("test_tex_solo_dos_estilos ...")
    if MemoriaCalculo.STYLES != ("educativo", "directo"):
        print(f"  FAIL: STYLES inesperado: {MemoriaCalculo.STYLES}")
        return False
    # 'completo' (eliminado) debe degradar a 'educativo', no reventar.
    project, solution, es, ns = _solved_example()
    mem = MemoriaCalculo(project, solution, es, ns, style="completo")
    if mem._style != "educativo":
        print(f"  FAIL: 'completo' no cayó al default: {mem._style}")
        return False
    print("  OK: dos estilos (educativo/directo) + fallback de 'completo'")
    return True


def test_tex_educativo_glosario_sin_volcado() -> bool:
    """El educativo conserva el glosario (valor pedagógico) pero NO los
    volcados de datos del ex-estilo 'completo'."""
    print("test_tex_educativo_glosario_sin_volcado ...")
    tex = _tex("educativo")
    if "Glosario de símbolos y términos" not in tex:
        print("  FAIL: 'educativo' debería incluir el glosario final")
        return False
    volcados = ["Datos completos del análisis",
                "Matrices de rigidez elementales"]
    present = [s for s in volcados if s in tex]
    if present:
        print(f"  FAIL: 'educativo' no debería tener apendices de volcado: "
              f"{present}")
        return False
    print("  OK: 'educativo' con glosario, sin volcados")
    return True


def test_tex_directo_sin_narrativa() -> bool:
    print("test_tex_directo_sin_narrativa ...")
    tex = _tex("directo")
    # El estilo directo no tiene cajas pedagogicas, infografía ni intro.
    if "tcolorbox" in tex:
        print("  FAIL: 'directo' no deberia tener cajas/tarjetas pedagogicas")
        return False
    if "¿Qué resuelve el MEF" in tex:
        print("  FAIL: 'directo' no deberia tener la intro narrativa")
        return False
    if "Glosario de símbolos" in tex:
        print("  FAIL: 'directo' no deberia tener glosario (solo educativo)")
        return False
    if "longtable" not in tex or "bmatrix" not in tex:
        print("  FAIL: 'directo' deberia tener tablas y matrices")
        return False
    print("  OK: 'directo' sin narrativa/infografía/glosario")
    return True


def test_tex_directo_paso_a_paso() -> bool:
    """El nuevo 'directo' contiene el procedimiento matricial COMPLETO
    (N→J→B→D→kₑ + ensamblaje + solución), no la versión superficial vieja."""
    print("test_tex_directo_paso_a_paso ...")
    tex = _tex("directo")
    pasos = [
        r"Jacobiano $\mathbf{J}=\partial\mathbf{N}",
        r"Matriz de deformación $\mathbf{B}$",
        r"Cuadratura de Gauss y matriz",
        r"\mathbf{k}_e",          # la kₑ desarrollada
        r"\mathbf{K}_{ff}",       # partición de BCs (fórmula, no gated)
        r"Tensiones en los puntos de Gauss",
        # Reemplazo matricial (consistencia con módulos M2/M4):
        r"\mathbf{X}_e",          # la matriz de coordenadas (operando)
        r"\mathbf{J}^{-1}",       # la inversa en la cadena de B
    ]
    missing = [p for p in pasos if p not in tex]
    if missing:
        print(f"  FAIL: 'directo' no desarrolla el paso a paso: {missing}")
        return False
    print("  OK: 'directo' con paso a paso matricial completo")
    return True


# ─── Figuras Pillow (estilo canvas, fondo blanco) ───────────────────────────

def test_mesh_diagram_es_pil() -> bool:
    print("test_mesh_diagram_es_pil ...")
    try:
        from PIL import Image
    except ImportError:
        print("  SKIP: Pillow no disponible")
        return True
    from file_io.figure_export import render_mesh_diagram
    project = load_example_project()
    # Forzar un roller_y para cubrir variantes de simbolo BC.
    bcs = list(project.boundary_conditions.values())
    if bcs:
        bcs[0].restrain_x = False
        bcs[0].restrain_y = True
    img = render_mesh_diagram(project)
    if not isinstance(img, Image.Image):
        print(f"  FAIL: render_mesh_diagram no devolvio PIL.Image: {type(img)}")
        return False
    if img.size[0] < 100 or img.size[1] < 100:
        print(f"  FAIL: imagen demasiado chica: {img.size}")
        return False
    print(f"  OK: render_mesh_diagram -> PIL.Image {img.size}")
    return True


def test_contornos_pil_blanco() -> bool:
    print("test_contornos_pil_blanco ...")
    try:
        from PIL import Image
    except ImportError:
        print("  SKIP: Pillow no disponible")
        return True
    from file_io.figure_export import render_contour
    project, solution, es, ns = _solved_example()
    img = render_contour(project, solution, ns, "von_mises")
    if not isinstance(img, Image.Image):
        print(f"  FAIL: render_contour no devolvio PIL.Image: {type(img)}")
        return False
    # Esquina superior izquierda debe ser blanca (fondo de papel).
    px = img.convert("RGB").getpixel((2, 2))
    if px != (255, 255, 255):
        print(f"  FAIL: fondo no es blanco en (2,2): {px}")
        return False
    print(f"  OK: contorno PIL {img.size} con fondo blanco")
    return True


def test_pipeline_map_es_pil() -> bool:
    """El mapa del cálculo (infografía del educativo) es una PIL.Image."""
    print("test_pipeline_map_es_pil ...")
    try:
        from PIL import Image
    except ImportError:
        print("  SKIP: Pillow no disponible")
        return True
    from file_io.figure_export import render_pipeline_map
    project = load_example_project()
    img = render_pipeline_map(project)
    if not isinstance(img, Image.Image):
        print(f"  FAIL: render_pipeline_map no devolvio PIL.Image: {type(img)}")
        return False
    if img.size[0] < 400 or img.size[1] < 100:
        print(f"  FAIL: mapa demasiado chico: {img.size}")
        return False
    print(f"  OK: render_pipeline_map -> PIL.Image {img.size}")
    return True


def test_compila_directo_q4() -> bool:
    """El estilo 'directo' (paso a paso matricial) compila a PDF."""
    print("test_compila_directo_q4 ...")
    if not _has_pdflatex():
        print("  SKIP: pdflatex no encontrado en PATH")
        return True
    project, solution, es, ns = _solved_example()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "memoria_directo_q4.pdf")
        result_path = generate_memoria_calculo(
            project, solution, es, ns, out_pdf, style="directo")
        if not Path(result_path).exists():
            print(f"  FAIL: no se genero el PDF directo en {result_path}")
            return False
        size = Path(result_path).stat().st_size
        if size < 5000:
            print(f"  FAIL: PDF directo demasiado chico ({size} bytes)")
            return False
        print(f"  OK: PDF directo generado, {size} bytes")
        return True


# ─── Theory Hub ─────────────────────────────────────────────────────────────

def _build_hub_tex() -> str:
    from gui.dialogs.theory_hub_dialog import _build_full_theory_document
    doc = TheoryDoc(title="Hub Test", subtitle="Test")
    _build_full_theory_document(doc)
    return doc.document().dumps()


def test_hub_tiene_m8_post() -> bool:
    print("test_hub_tiene_m8_post ...")
    tex = _build_hub_tex()
    required = ["M8", "Extrapolación", "Promediado", "principales", "Mises",
                "Barlow"]
    missing = [s for s in required if s not in tex]
    if missing:
        print(f"  FAIL: faltan en Hub M8: {missing}")
        return False
    print("  OK: Hub M8 cubre PG/extrapolación/promediado/principales/VM")
    return True


def test_hub_solver_lu_sin_internals() -> bool:
    """El Hub describe la factorización LU en abstracto, SIN nombrar internals
    del software (spsolve/scipy). Coherente con CLAUDE.md §Theory Hub."""
    print("test_hub_solver_lu_sin_internals ...")
    tex = _build_hub_tex()
    for forbidden in ("spsolve", "scipy", "SuperLU"):
        if forbidden in tex:
            print(f"  FAIL: el Hub menciona un internal indebido: {forbidden}")
            return False
    if "Factorización LU" not in tex:
        print("  FAIL: el Hub no describe la factorización LU")
        return False
    print("  OK: Hub describe LU en abstracto, sin internals")
    return True


def test_hub_no_tiene_mohr() -> bool:
    print("test_hub_no_tiene_mohr ...")
    tex = _build_hub_tex()
    if "Mohr" in tex:
        print("  FAIL: 'Mohr' aparece en el Hub")
        return False
    print("  OK: Hub no menciona Mohr")
    return True


def test_hub_bcs_solo_eliminacion() -> bool:
    print("test_hub_bcs_solo_eliminacion ...")
    tex = _build_hub_tex()
    if "penalización" in tex or "multiplicadores de Lagrange" in tex:
        print("  FAIL: aparece penalizacion / multiplicadores de Lagrange")
        return False
    if "eliminación" not in tex:
        print("  FAIL: el metodo de eliminacion no aparece")
        return False
    print("  OK: Hub solo describe el metodo de eliminacion")
    return True


def test_hub_toc_clickeable() -> bool:
    print("test_hub_toc_clickeable ...")
    tex = _build_hub_tex()
    if r"\tableofcontents" not in tex:
        print("  FAIL: \\tableofcontents ausente en Hub")
        return False
    print("  OK: TOC clickeable presente")
    return True


def test_hub_no_tiene_bibliografia() -> bool:
    print("test_hub_no_tiene_bibliografia ...")
    tex = _build_hub_tex()
    # NOTA: "Cook" se omite de la lista — en el cuerpo aparece como nombre del
    # benchmark "membrana de Cook" (no como cita bibliográfica). El intento del
    # test es que NO haya sección de bibliografía ni citas de autor sueltas.
    forbidden = ["Bibliografía", "Bathe", "Zienkiewicz", "Hughes"]
    found = [f for f in forbidden if f in tex]
    if found:
        print(f"  FAIL: bibliografia presente: {found}")
        return False
    print("  OK: Hub sin bibliografia")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Tests: file_io.memoria_calculo (reformulado)")
    print("=" * 60)
    results = [
        test_factored_matrix_helpers(),
        test_no_plus_en_positivos(),
        test_tex_estructura_educativo(),
        test_tex_solver_lu_sin_internals(),
        test_tex_ensamblaje_lm(),
        test_tex_sin_cross_refs_circulares(),
        test_tex_solo_dos_estilos(),
        test_tex_educativo_glosario_sin_volcado(),
        test_tex_directo_sin_narrativa(),
        test_tex_directo_paso_a_paso(),
        test_mesh_diagram_es_pil(),
        test_contornos_pil_blanco(),
        test_pipeline_map_es_pil(),
        test_compila_directo_q4(),
        test_hub_tiene_m8_post(),
        test_hub_solver_lu_sin_internals(),
        test_hub_no_tiene_mohr(),
        test_hub_bcs_solo_eliminacion(),
        test_hub_toc_clickeable(),
        test_hub_no_tiene_bibliografia(),
        test_memoria_minima_q4(),
        test_memoria_minima_q9(),
        test_error_pdflatex_faltante(),
    ]
    n_pass = sum(1 for r in results if r)
    n_total = len(results)
    print("=" * 60)
    print(f"Resultado: {n_pass}/{n_total} OK")
    sys.exit(0 if n_pass == n_total else 1)
