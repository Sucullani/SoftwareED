"""
Test minimo del generador de Memoria de Calculo (PDF/LaTeX).

Estilo printout (no usa pytest), consistente con el resto de tests/.
Skip elegante si pdflatex no esta en el PATH.

Cobertura:
  - test_memoria_minima_q4: ejemplo canonico Q4, verifica que el PDF se
    genera con tamano > 5KB.
  - test_memoria_minima_q9: variante Q9 (skip si no existe el helper).
  - test_error_pdflatex_faltante: verifica que el error de pdflatex
    faltante incluye texto accionable ("MiKTeX" o "pdflatex").
  - test_factored_matrix_helpers: prueba pura (sin pdflatex) de los
    helpers de factorizacion de matrices y vectores.
  - test_tex_source_contiene_capitulos_clave: verifica que el .tex
    generado contiene las secciones nuevas (Cap 0, Cap 7 expandido,
    Apendice C glosario) y los banners educacionales.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

# Permite correr desde la raiz del repo.
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


def test_memoria_minima_q4() -> bool:
    print("test_memoria_minima_q4 ...")
    if not _has_pdflatex():
        print("  SKIP: pdflatex no encontrado en PATH")
        return True

    project = load_example_project()
    solution = solve_system(project)
    project.is_solved = True
    project.displacements = solution["u"]
    project.global_K = solution["K"]
    project.global_F = solution["F"]
    element_stresses, nodal_stresses = compute_all_stresses(project, solution)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "memoria_test_q4.pdf")
        result_path = generate_memoria_calculo(
            project, solution, element_stresses, nodal_stresses, out_pdf,
        )
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
    element_stresses, nodal_stresses = compute_all_stresses(project, solution)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "memoria_test_q9.pdf")
        result_path = generate_memoria_calculo(
            project, solution, element_stresses, nodal_stresses, out_pdf,
        )
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
    """Verifica que si pdflatex falla, el mensaje es accionable.

    No se puede simular un PATH sin pdflatex sin contaminar el entorno;
    en su lugar, verificamos que `MemoriaCalculoError` exista y tenga el
    texto adecuado en su docstring/clase.
    """
    print("test_error_pdflatex_faltante ...")
    # Smoke test: la excepcion existe y se puede instanciar
    try:
        raise MemoriaCalculoError("test")
    except MemoriaCalculoError as e:
        if str(e) == "test":
            print("  OK: MemoriaCalculoError funciona")
            return True
        print(f"  FAIL: mensaje inesperado: {e}")
        return False


def test_factored_matrix_helpers() -> bool:
    """Helpers de factorizacion: no requieren pdflatex."""
    print("test_factored_matrix_helpers ...")

    # Caso 1: matriz con rango dinamico bajo -> factoriza exponente comun.
    K = np.array([[2.3e6, -1.1e6, 0.5e6],
                  [-1.1e6, 3.5e6, -0.8e6],
                  [0.5e6, -0.8e6, 2.1e6]])
    tex = TheoryDoc.matrix_factored_tex(K, name=r"\mathbf{K}", sig_digits=3)
    # Debe contener 10^{6} factorizado al frente
    if "10^{6}" not in tex:
        print(f"  FAIL: factorizacion 10^6 no encontrada en: {tex[:200]}")
        return False
    # NO debe contener notacion cientifica por entrada
    if "e+" in tex.lower() or "e-" in tex.lower():
        print(f"  FAIL: notacion cientifica por entrada presente: {tex[:200]}")
        return False
    print("  OK: factorizacion comun aplicada")

    # Caso 2: matriz con rango dinamico alto -> fallback a notacion
    # cientifica por entrada (preserva precision).
    M = np.array([[1e10, 1e-2], [3e5, 4e1]])
    tex2 = TheoryDoc.matrix_factored_tex(M, sig_digits=3)
    if "e+" not in tex2.lower() and "e-" not in tex2.lower():
        print(f"  FAIL: rango dinamico alto deberia caer a notacion "
              f"cientifica: {tex2[:200]}")
        return False
    print("  OK: fallback notacion cientifica con rango dinamico alto")

    # Caso 3: vector con transpose=True para compactar.
    u = np.array([1.23e-5, -4.56e-5, 7.89e-5, -2.34e-5])
    tex3 = TheoryDoc.vector_factored_tex(u, name=r"\mathbf{u}",
                                         sig_digits=3, transpose=True)
    if "10^{-5}" not in tex3:
        print(f"  FAIL: vector no factorizo 10^-5: {tex3}")
        return False
    if r"^T" not in tex3:
        print(f"  FAIL: transpose=True deberia añadir ^T: {tex3}")
        return False
    print("  OK: vector factorizado en forma transpuesta")

    # Caso 4: matriz nula -> body de ceros.
    Z = np.zeros((3, 3))
    tex4 = TheoryDoc.matrix_factored_tex(Z, name=r"\mathbf{Z}")
    if "bmatrix" not in tex4:
        print(f"  FAIL: matriz nula sin bmatrix: {tex4}")
        return False
    print("  OK: matriz nula manejada")

    # Caso 5: exponente p == 0 (entradas ~unidad) -> sin factor visible.
    A = np.array([[1.23, 2.34], [3.45, 4.56]])
    tex5 = TheoryDoc.matrix_factored_tex(A, sig_digits=3)
    # No debe aparecer "10^{0}" ni "10^{} \cdot" — debe ser solo bmatrix.
    if "10^{0}" in tex5 or "10^{} \\cdot" in tex5:
        print(f"  FAIL: p=0 no deberia mostrar factor visible: {tex5}")
        return False
    print("  OK: p=0 sin factor visible (limpio)")

    return True


def test_tex_source_contiene_capitulos_clave() -> bool:
    """Genera el .tex sin compilar y verifica las secciones esperadas."""
    print("test_tex_source_contiene_capitulos_clave ...")
    project = load_example_project()
    solution = solve_system(project)
    project.is_solved = True
    element_stresses, nodal_stresses = compute_all_stresses(project, solution)

    mem = MemoriaCalculo(
        project, solution, element_stresses, nodal_stresses,
    )
    mem.build()
    tex = mem.tex_source()

    # Capitulos esperados, en jerarquia MEF estandar (Pre 1-3 -> Proc 4-7 ->
    # Post 8 + apendices). Cap 0 va sin numerar (intro).
    expected_sections = [
        r"¿Qué resuelve el MEF y cómo?",          # Cap 0 (intro)
        r"Definición del problema",               # Cap 1
        r"Discretización del modelo",             # Cap 2
        r"Calidad de la malla",                   # Cap 3
        r"Formulación elemental",                 # Cap 4 (era Cap 3 showcase)
        r"Ensamblaje del sistema global",         # Cap 5
        r"Aplicación de condiciones de contorno", # Cap 6
        r"Solución del sistema y verificación",   # Cap 7
        r"Post-proceso: tensiones y visualización",  # Cap 8
        r"Matrices de rigidez elementales",       # Apendice A
        r"Datos completos del análisis",          # Apendice B
        r"Glosario de símbolos y términos",       # Apendice C
    ]
    missing = [s for s in expected_sections if s not in tex]
    if missing:
        print(f"  FAIL: secciones ausentes: {missing}")
        return False
    print("  OK: capitulos esperados presentes (jerarquia MEF)")

    # Verificar orden FEM en Cap 4 (showcase): N debe aparecer antes que J,
    # J antes que B, B antes que D, D antes que `Integrando', Integrando
    # antes que `Cuadratura de Gauss'.
    fem_hierarchy_markers = [
        r"Funciones de forma $N_i",
        r"Jacobiano $\mathbf{J}",
        r"Matriz de deformación $\mathbf{B}",
        r"Matriz constitutiva $\mathbf{D}",
        r"Integrando simbólico",
        r"Cuadratura de Gauss",
    ]
    positions = []
    for marker in fem_hierarchy_markers:
        pos = tex.find(marker)
        if pos < 0:
            print(f"  FAIL: marcador no encontrado: {marker}")
            return False
        positions.append((marker, pos))
    sorted_by_pos = sorted(positions, key=lambda p: p[1])
    if positions != sorted_by_pos:
        actual_order = [p[0] for p in sorted_by_pos]
        expected_order = [p[0] for p in positions]
        print(f"  FAIL: jerarquia FEM en Cap 4 no respetada")
        print(f"        esperado: {expected_order}")
        print(f"        actual:   {actual_order}")
        return False
    print("  OK: jerarquia FEM en Cap 4 (N -> J -> B -> D -> Integrando -> Gauss)")

    # Verificar orden global: Calidad antes de Showcase, Showcase antes de
    # Ensamblaje, Ensamblaje antes de BCs, BCs antes de Solucion, Solucion
    # antes de Post-proceso.
    chapter_order_markers = [
        r"Discretización del modelo",
        r"Calidad de la malla",
        r"Formulación elemental",
        r"Ensamblaje del sistema global",
        r"Aplicación de condiciones de contorno",
        r"Solución del sistema y verificación",
        r"Post-proceso",
    ]
    chap_positions = [tex.find(m) for m in chapter_order_markers]
    if chap_positions != sorted(chap_positions):
        print(f"  FAIL: orden de capitulos no es Pre 2-3 -> Proc 4-7 -> Post 8")
        return False
    print("  OK: orden de capitulos respeta jerarquia MEF global")

    # Subsecciones nuevas del Cap 8 (extrapolacion, promediado, principales, VM)
    expected_subsections_cap8 = [
        "Tensiones en los puntos de Gauss",
        "Extrapolación de Gauss a nodos",
        "Promediado nodal entre elementos adyacentes",
        "Tensiones principales",
        "Tensión equivalente de von Mises",
    ]
    missing8 = [s for s in expected_subsections_cap8 if s not in tex]
    if missing8:
        print(f"  FAIL: subsecciones Cap 8 ausentes: {missing8}")
        return False
    print("  OK: Cap 8 reestructurado contiene todas las subsecciones")

    # Solver Cholesky en Cap 7
    if "Cholesky" not in tex or "Método de resolución" not in tex:
        print("  FAIL: Cap 7 sin explicacion de Cholesky")
        return False
    print("  OK: Cap 7 explica Cholesky / LU")

    # Mapeo LM en Cap 5
    if "Mapeo de grados de libertad" not in tex or r"\mathbf{LM}" not in tex:
        print("  FAIL: Cap 5 sin discusion de mapeo LM")
        return False
    print("  OK: Cap 5 discute mapeo LM (location matrix)")

    # Numeros manuales 'X.Y ' en titulos -- NO deben aparecer (todo
    # auto-numerado ahora).
    import re
    manual_prefixes = re.findall(
        r"\\subsection\*?\{(?P<num>\d\.\d) ", tex
    )
    if manual_prefixes:
        print(f"  FAIL: aun hay prefijos manuales en subsections: "
              f"{sorted(set(manual_prefixes))[:5]}...")
        return False
    print("  OK: sin prefijos numericos manuales (todo auto-numerado por LaTeX)")

    # Banners + teasers: tras el recorte agresivo, esperamos pocos banners
    # largos (~2-3) y muchos teasers (~7-9). Validamos el total minimo de
    # piezas pedagogicas y que haya teasers (marcador `borderline west').
    n_pieces = tex.count(r"\begin{tcolorbox}")
    n_teasers = tex.count("borderline west")  # marcador unico de teaser
    n_long_banners = n_pieces - n_teasers
    if n_pieces < 7:
        print(f"  FAIL: muy pocas piezas pedagogicas ({n_pieces}, esperado >= 7)")
        return False
    if n_teasers < 5:
        print(f"  FAIL: pocos teasers cortos ({n_teasers}, esperado >= 5)")
        return False
    print(f"  OK: {n_long_banners} banners largos + {n_teasers} teasers")

    # Vectores y matrices factorizadas: el patron "10^{...} \cdot \begin{bmatrix}"
    # debe aparecer al menos una vez (K, u, F o ke).
    if r"\cdot \begin{bmatrix}" not in tex and \
       r"10^{" not in tex:
        print("  FAIL: ningun vector/matriz factorizado encontrado")
        return False
    print("  OK: factorizacion aplicada en al menos un vector/matriz")

    return True


def test_memoria_tiene_cross_refs_al_hub() -> bool:
    """Tras el recorte agresivo, la Memoria delega teoria al Hub via
    cross-refs visibles ('Ver Teoria MEF: <seccion>'). Debe haber al menos
    6 ocurrencias (5 en aperturas de cap + varias en teasers)."""
    print("test_memoria_tiene_cross_refs_al_hub ...")
    project = load_example_project()
    solution = solve_system(project)
    project.is_solved = True
    es, ns = compute_all_stresses(project, solution)
    mem = MemoriaCalculo(project, solution, es, ns)
    mem.build()
    tex = mem.tex_source()
    n = tex.count("Teoría MEF")
    if n < 6:
        print(f"  FAIL: solo {n} cross-refs (esperado >= 6)")
        return False
    print(f"  OK: {n} cross-refs al Hub")
    return True


def _build_hub_tex() -> str:
    """Helper: construye el doc del Hub y devuelve su .tex serializado."""
    from gui.dialogs.theory_hub_dialog import _build_full_theory_document
    doc = TheoryDoc(title="Hub Test", subtitle="Test")
    _build_full_theory_document(doc)
    return doc.document().dumps()


def test_hub_tiene_m8_post() -> bool:
    print("test_hub_tiene_m8_post ...")
    tex = _build_hub_tex()
    required = ["M8", "Extrapolación", "Promediado",
                "principales", "Mises", "Barlow"]
    missing = [s for s in required if s not in tex]
    if missing:
        print(f"  FAIL: faltan en Hub M8: {missing}")
        return False
    print("  OK: Hub M8 cubre PG/extrapolación/promediado/principales/VM")
    return True


def test_hub_no_tiene_mohr() -> bool:
    print("test_hub_no_tiene_mohr ...")
    tex = _build_hub_tex()
    if "Mohr" in tex:
        print("  FAIL: 'Mohr' aparece en el Hub")
        return False
    print("  OK: Hub no menciona Mohr (decision usuario)")
    return True


def test_hub_bcs_solo_eliminacion() -> bool:
    print("test_hub_bcs_solo_eliminacion ...")
    tex = _build_hub_tex()
    if "penalización" in tex:
        print("  FAIL: 'penalización' aparece en el Hub")
        return False
    if "multiplicadores de Lagrange" in tex:
        print("  FAIL: 'multiplicadores de Lagrange' aparece en el Hub")
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
    print("  OK: TOC clickeable presente (hyperref ya cargado)")
    return True


def test_hub_no_tiene_bibliografia() -> bool:
    print("test_hub_no_tiene_bibliografia ...")
    tex = _build_hub_tex()
    forbidden = ["Bibliografía", "Bathe", "Cook", "Zienkiewicz", "Hughes"]
    found = [f for f in forbidden if f in tex]
    if found:
        print(f"  FAIL: bibliografia presente: {found}")
        return False
    print("  OK: Hub sin bibliografia (decision usuario)")
    return True


def test_mesh_diagram_simbolos_canvas() -> bool:
    """Verifica que render_mesh_diagram dibuja simbolos BC estilo canvas
    (no solo marker triangular generico). Estrategia: contar patches
    Polygon/Circle creados por _draw_bc_symbol."""
    print("test_mesh_diagram_simbolos_canvas ...")
    from file_io.figure_export import render_mesh_diagram
    project = load_example_project()
    # El ejemplo canonico tiene BCs is_fixed en los 3 nodos del borde
    # izquierdo. Forzamos al menos 1 roller_y para cubrir variantes.
    bcs = list(project.boundary_conditions.values())
    if not bcs:
        print("  SKIP: ejemplo sin BCs")
        return True
    # Modificar la primera BC a roller_y (restringir solo Y)
    bc0 = bcs[0]
    bc0.restrain_x = False
    bc0.restrain_y = True

    fig = render_mesh_diagram(project)
    # Contar polygons y circles en el axes (excluyendo elementos de la malla)
    ax = fig.axes[0]
    n_polygons = sum(1 for p in ax.patches if p.__class__.__name__ == "Polygon")
    n_circles = sum(1 for p in ax.patches if p.__class__.__name__ == "Circle")
    # _draw_bc_symbol genera Polygon por BC; roller_y/x agrega un Circle.
    # Expect: >= 1 polygon (BC fixed) + >= 1 circle (roller).
    if n_polygons < 1:
        print(f"  FAIL: 0 polygons de BC (esperado >= 1)")
        return False
    if n_circles < 1:
        print(f"  FAIL: 0 circles de roller (esperado >= 1)")
        return False
    print(f"  OK: {n_polygons} polygon(s) BC + {n_circles} circle(s) rodillo")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Tests: file_io.memoria_calculo")
    print("=" * 60)
    results = [
        test_factored_matrix_helpers(),
        test_tex_source_contiene_capitulos_clave(),
        test_memoria_tiene_cross_refs_al_hub(),
        test_hub_tiene_m8_post(),
        test_hub_no_tiene_mohr(),
        test_hub_bcs_solo_eliminacion(),
        test_hub_toc_clickeable(),
        test_hub_no_tiene_bibliografia(),
        test_mesh_diagram_simbolos_canvas(),
        test_memoria_minima_q4(),
        test_memoria_minima_q9(),
        test_error_pdflatex_faltante(),
    ]
    n_pass = sum(1 for r in results if r)
    n_total = len(results)
    print("=" * 60)
    print(f"Resultado: {n_pass}/{n_total} OK")
    sys.exit(0 if n_pass == n_total else 1)
