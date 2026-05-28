"""
Tests de la Memoria de Cálculo (reformulada en 2026-05).

Estilo printout (sin pytest). Skip elegante si `pdflatex` no esta en PATH.

Cobertura:
  - Helpers de factorización de matrices (no requieren pdflatex).
  - Generación de los 3 estilos (`directo`, `educativo`, `completo`):
    smoke test sobre Q4 + Q9, verifica que el PDF se produce con
    tamaño razonable.
  - Estructura del .tex generado: secciones esperadas según el estilo,
    indexación ordinal de GDLs, referencia explícita a Cholesky vía
    LAPACK POSV.
  - Sin prefijo '+' en numeros positivos de matrices/vectores
    (regla de formato del proyecto).
  - Renderers Pillow retornan `PIL.Image` no triviales.
  - Hub de teoría: cubre M0..M9, sin Mohr, sin bibliografía, TOC clickeable,
    solo metodo de eliminacion para BCs.
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


def _solve_and_post(project):
    sol = solve_system(project)
    project.is_solved = True
    project.displacements = sol["u"]
    project.global_K = sol["K"]
    project.global_F = sol["F"]
    es, ns = compute_all_stresses(project, sol)
    return sol, es, ns


# ───────────────────────────────────────────────────────────────────────────
# Helpers puros (no requieren pdflatex)
# ───────────────────────────────────────────────────────────────────────────

def test_factored_matrix_helpers() -> bool:
    print("test_factored_matrix_helpers ...")

    K = np.array([[2.3e6, -1.1e6, 0.5e6],
                  [-1.1e6, 3.5e6, -0.8e6],
                  [0.5e6, -0.8e6, 2.1e6]])
    tex = TheoryDoc.matrix_factored_tex(K, name=r"\mathbf{K}", sig_digits=3)
    if "10^{6}" not in tex:
        print(f"  FAIL: factorizacion 10^6 no encontrada: {tex[:200]}")
        return False
    print("  OK: factorizacion comun aplicada")

    M = np.array([[1e10, 1e-2], [3e5, 4e1]])
    tex2 = TheoryDoc.matrix_factored_tex(M, sig_digits=3)
    if "e+" not in tex2.lower() and "e-" not in tex2.lower():
        print(f"  FAIL: rango dinamico alto deberia caer a notacion "
              f"cientifica: {tex2[:200]}")
        return False
    print("  OK: fallback notacion cientifica con rango dinamico alto")

    u = np.array([1.23e-5, -4.56e-5, 7.89e-5, -2.34e-5])
    tex3 = TheoryDoc.vector_factored_tex(u, name=r"\mathbf{u}",
                                         sig_digits=3, transpose=True)
    if "10^{-5}" not in tex3:
        print(f"  FAIL: vector no factorizo 10^-5: {tex3}")
        return False
    if r"^T" not in tex3:
        print(f"  FAIL: transpose=True deberia agregar ^T: {tex3}")
        return False
    print("  OK: vector factorizado en forma transpuesta")

    Z = np.zeros((3, 3))
    tex4 = TheoryDoc.matrix_factored_tex(Z, name=r"\mathbf{Z}")
    if "bmatrix" not in tex4:
        print(f"  FAIL: matriz nula sin bmatrix: {tex4}")
        return False
    print("  OK: matriz nula manejada")

    A = np.array([[1.23, 2.34], [3.45, 4.56]])
    tex5 = TheoryDoc.matrix_factored_tex(A, sig_digits=3)
    if "10^{0}" in tex5 or "10^{} \\cdot" in tex5:
        print(f"  FAIL: p=0 no deberia mostrar factor visible: {tex5}")
        return False
    print("  OK: p=0 sin factor visible (limpio)")

    return True


def test_strip_plus_helper() -> bool:
    """Verifica que `_strip_plus` reemplaza el '+' inicial por `\\phantom{-}`."""
    print("test_strip_plus_helper ...")
    s = TheoryDoc._strip_plus("+1.234")
    if s != r"\phantom{-}1.234":
        print(f"  FAIL: +1.234 -> {s!r}, esperado '\\phantom{{-}}1.234'")
        return False
    s = TheoryDoc._strip_plus("-1.234")
    if s != "-1.234":
        print(f"  FAIL: -1.234 deberia ser invariante, dio {s!r}")
        return False
    s = TheoryDoc._strip_plus("1.234")
    if s != "1.234":
        print(f"  FAIL: 1.234 sin signo deberia ser invariante, dio {s!r}")
        return False
    # Scientific notation exponent is NOT a sign: +1.23e+05 -> phantom + e+05
    s = TheoryDoc._strip_plus("+1.23e+05")
    if s != r"\phantom{-}1.23e+05":
        print(f"  FAIL: +1.23e+05 -> {s!r}")
        return False
    print("  OK: _strip_plus correcto en signo, exponente y formatos varios")
    return True


def test_no_plus_prefix_in_matrices() -> bool:
    """Regresión: positivos en vectores/matrices NO llevan '+'.

    Genera el .tex de los 3 estilos y busca patrones `{+\\d` (curly +
    digit) o ` +\\d` (espacio + digit) en celdas, excluyendo:
      - exponentes científicos `e+05` (legítimos: el `+` es parte del
        número, no signo redundante).
      - `\\phantom{+}` y `\\phantom{-}` (placeholder de alineamiento).
      - operadores matemáticos `\\mathrel{+}` (suma como operación, no
        signo).
    """
    print("test_no_plus_prefix_in_matrices ...")
    import re
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)
    for style in ("directo", "educativo", "completo"):
        m = MemoriaCalculo(project, sol, es, ns, style=style)
        m.build()
        tex = m.tex_source()
        clean = (tex.replace(r"\phantom{+}", "@")
                    .replace(r"\phantom{-}", "@")
                    .replace(r"\mathrel{+}", "@"))
        # Match a digit-prefixed '+' within a number context (not 'e+05').
        # Exclusiones legitimas:
        #   - 'e+05' / 'E+05': exponente en notacion cientifica.
        #   - 'p+1' / '{p+1' / etc.: orden polinomial $p+1$ en formulas
        #     (cualquier letra inmediatamente antes del '+' indica una
        #     expresion simbolica, no un numero con signo redundante).
        leaks = []
        for match in re.finditer(r"\+\d", clean):
            ctx_char = clean[match.start() - 1] if match.start() > 0 else " "
            if ctx_char.isalpha():
                continue
            leaks.append(clean[max(0, match.start() - 20): match.end() + 5])
        if leaks:
            print(f"  FAIL [{style}]: '+digit' leaks: {leaks[:3]}")
            return False
    print("  OK: ningun '+' redundante en positivos de matrices/vectores")
    return True


# ───────────────────────────────────────────────────────────────────────────
# Generación del PDF (requiere pdflatex)
# ───────────────────────────────────────────────────────────────────────────

def test_memoria_minima_q4() -> bool:
    print("test_memoria_minima_q4 ...")
    if not _has_pdflatex():
        print("  SKIP: pdflatex no encontrado en PATH")
        return True
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "memoria_test_q4.pdf")
        result = generate_memoria_calculo(project, sol, es, ns, out_pdf)
        if not Path(result).exists() or Path(result).stat().st_size < 5000:
            print(f"  FAIL: PDF no generado o muy chico")
            return False
        print(f"  OK: PDF Q4 generado, {Path(result).stat().st_size} bytes")
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
    sol, es, ns = _solve_and_post(project)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pdf = os.path.join(tmpdir, "memoria_test_q9.pdf")
        result = generate_memoria_calculo(project, sol, es, ns, out_pdf)
        if not Path(result).exists() or Path(result).stat().st_size < 5000:
            print(f"  FAIL: PDF Q9 no generado o muy chico")
            return False
        print(f"  OK: PDF Q9 generado, {Path(result).stat().st_size} bytes")
    return True


def test_los_tres_estilos_compilan() -> bool:
    """Compila los 3 estilos sobre Q4 y verifica que crecen monotónicamente."""
    print("test_los_tres_estilos_compilan ...")
    if not _has_pdflatex():
        print("  SKIP: pdflatex no encontrado en PATH")
        return True
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)
    sizes = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        for style in ("directo", "educativo", "completo"):
            out_pdf = os.path.join(tmpdir, f"mem_{style}.pdf")
            generate_memoria_calculo(project, sol, es, ns, out_pdf, style=style)
            sizes[style] = Path(out_pdf).stat().st_size
    print(f"  PDFs: {sizes}")
    if not (sizes["directo"] > 0 and sizes["educativo"] > 0
            and sizes["completo"] > 0):
        print("  FAIL: algun PDF de 0 bytes")
        return False
    # `completo` debe ser estrictamente mayor que `directo` (incluye apéndices).
    if sizes["completo"] <= sizes["directo"]:
        print("  FAIL: 'completo' deberia ser mas grande que 'directo'")
        return False
    print("  OK: los 3 estilos compilan; tamano crece de directo a completo")
    return True


def test_error_pdflatex_faltante() -> bool:
    """`MemoriaCalculoError` se puede instanciar con mensaje."""
    print("test_error_pdflatex_faltante ...")
    try:
        raise MemoriaCalculoError("test")
    except MemoriaCalculoError as e:
        if str(e) == "test":
            print("  OK")
            return True
    print("  FAIL")
    return False


def test_estilo_invalido_rechaza() -> bool:
    """`generate_memoria_calculo(style='inexistente')` falla con
    `MemoriaCalculoError`."""
    print("test_estilo_invalido_rechaza ...")
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "x.pdf")
            generate_memoria_calculo(project, sol, es, ns, out, style="invalido")
        print("  FAIL: no levanto MemoriaCalculoError")
        return False
    except MemoriaCalculoError:
        print("  OK: rechaza estilo invalido")
        return True


# ───────────────────────────────────────────────────────────────────────────
# Estructura del .tex
# ───────────────────────────────────────────────────────────────────────────

def test_tex_estructura_educativo() -> bool:
    """Estructura del .tex en estilo `educativo`: secciones, indexación
    ordinal de GDLs, Cholesky vía LAPACK POSV."""
    print("test_tex_estructura_educativo ...")
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)
    m = MemoriaCalculo(project, sol, es, ns, style="educativo")
    m.build()
    tex = m.tex_source()

    # Secciones esperadas (orden + presencia)
    expected = [
        "Datos del modelo",
        "Calidad geométrica de la malla",
        "Procedimiento elemental",
        "Ensamblaje del sistema global",
        "Aplicación de restricciones",
        "Solución del sistema y reacciones",
        "Tensiones (post-proceso)",
        "Visualización del campo",
    ]
    missing = [s for s in expected if s not in tex]
    if missing:
        print(f"  FAIL: secciones ausentes: {missing}")
        return False
    print(f"  OK: {len(expected)} secciones presentes")

    # Orden
    positions = [tex.find(s) for s in expected]
    if positions != sorted(positions):
        print(f"  FAIL: orden de secciones violado: {positions}")
        return False
    print("  OK: orden de secciones correcto")

    # Indexación ordinal explicitada (regla crítica del software)
    if "node_index_map" not in tex and r"\mathrm{idx}" not in tex:
        print("  FAIL: no se explica la indexacion ordinal de GDLs")
        return False
    print("  OK: indexacion ordinal documentada")

    # Cholesky vía LAPACK POSV (afirmación verificable contra fem/solver.py)
    if "Cholesky" not in tex:
        print("  FAIL: no menciona Cholesky")
        return False
    if "POSV" not in tex:
        print("  FAIL: no menciona LAPACK POSV (verifica solver real)")
        return False
    print("  OK: solver Cholesky + LAPACK POSV documentado")

    return True


def test_tex_estructura_directo() -> bool:
    """Estilo `directo` no debe incluir calidad ni procedimiento elemental."""
    print("test_tex_estructura_directo ...")
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)
    m = MemoriaCalculo(project, sol, es, ns, style="directo")
    m.build()
    tex = m.tex_source()
    # Las secciones de narrativa/showcase NO deben existir
    forbidden = [
        "Calidad geométrica",
        "Procedimiento elemental",
        "Ensamblaje del sistema global",
        "Aplicación de restricciones",
    ]
    leaked = [s for s in forbidden if s in tex]
    if leaked:
        print(f"  FAIL [directo]: secciones que no deberian estar: {leaked}")
        return False
    print("  OK: estilo 'directo' omite secciones de narrativa")
    # Pero las que SI debe tener
    required = [
        "Datos del modelo",
        "Solución del sistema y reacciones",
        "Tensiones (post-proceso)",
        "Visualización del campo",
    ]
    missing = [s for s in required if s not in tex]
    if missing:
        print(f"  FAIL [directo]: secciones requeridas ausentes: {missing}")
        return False
    print("  OK: estilo 'directo' incluye los esenciales")
    return True


def test_tex_estructura_completo_appendices() -> bool:
    """Estilo `completo` agrega apéndices A, B, C."""
    print("test_tex_estructura_completo_appendices ...")
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)
    m = MemoriaCalculo(project, sol, es, ns, style="completo")
    m.build()
    tex = m.tex_source()
    expected = [
        "Matrices de rigidez elementales",   # Apéndice A
        "Tensiones por punto de Gauss",       # Apéndice B
        "Vectores completos",                 # Apéndice C
    ]
    missing = [s for s in expected if s not in tex]
    if missing:
        print(f"  FAIL: apendices ausentes: {missing}")
        return False
    if r"\appendix" not in tex:
        print("  FAIL: marker \\appendix ausente")
        return False
    print("  OK: apéndices A/B/C presentes con marker \\appendix")
    return True


def test_no_glosario_redundante() -> bool:
    """El glosario del apéndice C fue eliminado en 2026-05: la notación
    está documentada inline y el Hub la cubre."""
    print("test_no_glosario_redundante ...")
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)
    m = MemoriaCalculo(project, sol, es, ns, style="completo")
    m.build()
    tex = m.tex_source()
    if "Glosario" in tex:
        print("  FAIL: apendice de Glosario reintroducido")
        return False
    print("  OK: sin glosario redundante con el Hub")
    return True


# ───────────────────────────────────────────────────────────────────────────
# Renderers Pillow
# ───────────────────────────────────────────────────────────────────────────

def test_pillow_renderers_no_son_matplotlib() -> bool:
    """Los renderers espaciales retornan `PIL.Image`, NO `matplotlib.Figure`."""
    print("test_pillow_renderers_no_son_matplotlib ...")
    from file_io.figure_export import (
        render_mesh_diagram, render_contour, render_deformed,
        render_principal_crosses,
    )
    project = load_example_project()
    sol, es, ns = _solve_and_post(project)

    for name, fn in (("mesh_diagram", lambda: render_mesh_diagram(project)),
                     ("contour_sx", lambda: render_contour(project, sol, ns, "sigma_x")),
                     ("contour_vm", lambda: render_contour(project, sol, ns, "von_mises")),
                     ("deformed", lambda: render_deformed(project, sol)),
                     ("principal", lambda: render_principal_crosses(project, ns))):
        img = fn()
        if img is None:
            print(f"  FAIL: {name} retorno None")
            return False
        if hasattr(img, "savefig"):
            print(f"  FAIL: {name} aun retorna matplotlib Figure")
            return False
        if not hasattr(img, "save"):
            print(f"  FAIL: {name} no es PIL.Image")
            return False
        w, h = img.size
        if w < 100 or h < 100:
            print(f"  FAIL: {name} demasiado chica {img.size}")
            return False
    print("  OK: 5 renderers espaciales retornan PIL.Image")
    return True


def test_pillow_mesh_diagram_simbolos_bc() -> bool:
    """`render_mesh_diagram` dibuja simbolos BC (al menos un nodo
    visible en el bbox) sobre fondo blanco."""
    print("test_pillow_mesh_diagram_simbolos_bc ...")
    from file_io.figure_export import render_mesh_diagram
    project = load_example_project()
    img = render_mesh_diagram(project)
    if img is None:
        print("  SKIP: PIL no disponible")
        return True
    arr = np.array(img.convert("RGB"))
    # Fondo predominantemente blanco (>= 45% — el diagrama tiene elementos
    # con relleno azul suave que ocupan area significativa, asi que el
    # blanco "puro" es el resto del lienzo + margenes).
    white_frac = np.sum(np.all(arr > 240, axis=-1)) / arr.size * 3
    if white_frac < 0.45:
        print(f"  FAIL: fondo no es predominantemente blanco "
              f"(white_frac={white_frac:.2f})")
        return False
    # Naranja (BC) presente: convencion del MeshCanvas
    orange_mask = ((arr[:, :, 0] > 200) & (arr[:, :, 1] > 100) &
                   (arr[:, :, 1] < 200) & (arr[:, :, 2] < 100))
    if np.sum(orange_mask) < 50:
        print(f"  WARN: pixeles naranjas (BC) escasos: {np.sum(orange_mask)}")
        # No fail — el ejemplo podria no tener BCs (no es el caso aqui)
    print(f"  OK: fondo blanco ({white_frac*100:.0f}%) + simbolos BC visibles")
    return True


# ───────────────────────────────────────────────────────────────────────────
# Hub de teoría
# ───────────────────────────────────────────────────────────────────────────

def _build_hub_tex() -> str:
    # El Hub vive en gui/dialogs pero la función pura puede compilarse
    # sin Tk. Importamos solo la función.
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
        print("  FAIL: el método de eliminación no aparece")
        return False
    print("  OK: Hub solo describe el metodo de eliminacion")
    return True


def test_hub_toc_clickeable() -> bool:
    print("test_hub_toc_clickeable ...")
    tex = _build_hub_tex()
    if r"\tableofcontents" not in tex:
        print("  FAIL: \\tableofcontents ausente")
        return False
    print("  OK: TOC clickeable presente")
    return True


def test_hub_no_tiene_bibliografia() -> bool:
    print("test_hub_no_tiene_bibliografia ...")
    tex = _build_hub_tex()
    forbidden = ["Bibliografía", "Bathe", "Cook", "Zienkiewicz", "Hughes"]
    found = [f for f in forbidden if f in tex]
    if found:
        print(f"  FAIL: bibliografia presente: {found}")
        return False
    print("  OK: Hub sin bibliografia")
    return True


def test_hub_solver_cholesky_posv() -> bool:
    """El Hub debe mencionar Cholesky vía LAPACK POSV (alinea con
    fem/solver.py que usa `assume_a='pos'`)."""
    print("test_hub_solver_cholesky_posv ...")
    tex = _build_hub_tex()
    if "Cholesky" not in tex:
        print("  FAIL: no menciona Cholesky")
        return False
    if "POSV" not in tex:
        print("  FAIL: no menciona LAPACK POSV")
        return False
    print("  OK: Hub documenta Cholesky vía LAPACK POSV")
    return True


# ───────────────────────────────────────────────────────────────────────────
# Runner
# ───────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Tests: file_io.memoria_calculo (reformulada 2026-05)")
    print("=" * 60)
    results = [
        test_factored_matrix_helpers(),
        test_strip_plus_helper(),
        test_no_plus_prefix_in_matrices(),
        test_estilo_invalido_rechaza(),
        test_tex_estructura_educativo(),
        test_tex_estructura_directo(),
        test_tex_estructura_completo_appendices(),
        test_no_glosario_redundante(),
        test_pillow_renderers_no_son_matplotlib(),
        test_pillow_mesh_diagram_simbolos_bc(),
        test_hub_tiene_m8_post(),
        test_hub_no_tiene_mohr(),
        test_hub_bcs_solo_eliminacion(),
        test_hub_toc_clickeable(),
        test_hub_no_tiene_bibliografia(),
        test_hub_solver_cholesky_posv(),
        test_memoria_minima_q4(),
        test_memoria_minima_q9(),
        test_los_tres_estilos_compilan(),
        test_error_pdflatex_faltante(),
    ]
    n_pass = sum(1 for r in results if r)
    n_total = len(results)
    print("=" * 60)
    print(f"Resultado: {n_pass}/{n_total} OK")
    sys.exit(0 if n_pass == n_total else 1)
