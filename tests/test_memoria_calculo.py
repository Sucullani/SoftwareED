"""
Test del generador de Memoria de Calculo (PDF/LaTeX) — reformulado 2026-05.

Estilo printout (no usa pytest), consistente con el resto de tests/.
Skip elegante si no hay compilador LaTeX (ni vendor/texlive ni pdflatex en el PATH).

Cobertura (sincronizada con las funciones reales; ver el bloque __main__):
  - test_memoria_minima_q4 / _q9: compila el PDF (skip sin pdflatex).
  - test_error_pdflatex_faltante: la excepcion accionable existe.
  - test_factored_matrix_helpers: helpers de factorizacion (sin pdflatex).
  - test_no_plus_en_positivos: las celdas de matrices/vectores no llevan '+'.
  - test_tex_estructura_educativo: capitulos + jerarquia FEM del estilo
    'educativo' (default). Sin compilar.
  - test_tex_solver_lu_sin_internals: el Cap. de solucion describe LU directa
    en abstracto, sin mencionar internals (spsolve/SuperLU/etc.).
  - test_tex_ensamblaje_lm: el ensamblaje describe el mapeo LM.
  - test_tex_sin_cross_refs_circulares: la Memoria no remite al Hub.
  - test_tex_solo_dos_estilos: STYLES == ('educativo', 'directo').
  - test_tex_educativo_glosario_sin_volcado / test_tex_directo_sin_narrativa /
    test_tex_directo_paso_a_paso.
  - test_mesh_diagram_es_pil: render_mesh_diagram devuelve una PIL.Image.
  - test_contornos_pil_blanco: los contornos son PIL con fondo blanco.
  - test_longtable_cuenta_columnas_de_parrafo: `p{4.3cm}` es UNA columna
    (el glosario y la tabla de diagnostico perdian su columna de parrafo).
  - test_tablas_con_unidades: los encabezados dicen la unidad del sistema.
  - test_contorno_rotulo_con_simbolo_y_unidad: la colorbar del contorno usa
    el simbolo del campo + su unidad, con los ticks de `fmt_escala`.
  - test_figuras_lod_en_malla_densa: los nodos de las figuras siguen el LOD
    del canvas (la deformada de una malla densa era una mancha de discos).
  - test_pipeline_map_es_pil / test_compila_directo_q4.
  - test_tex_sin_indice_ni_apaisado: sin sumario impreso ni `landscape`.
  - test_tex_portada_en_una_hoja: ficha a dos columnas + diagrama del modelo
    en AMBOS estilos, sin `\\newpage` dentro de la portada.
  - test_tex_contornos_en_grilla: los 4 contornos en 2 filas de 2.
  - test_tex_sin_duplicar_D_ni_isoparametrico: la D numerica y la caja del
    isoparametrico se emiten una sola vez.
  - test_max_matrix_cols_cubre_la_matriz_mas_ancha: `MaxMatrixCols` declarado
    >= la bmatrix mas ancha (pasarse aborta la compilacion, no avisa).
  - test_recuperacion_epsilon_reproduce_sigma: la tabla eps = B*u_e ->
    sigma = D*eps cierra contra las sigma del solver (imprimia eps = 0).
  - test_tablas_topeadas_en_malla_grande: ninguna tabla vuelca la malla
    entera (Cook Q9 32x32 daba un PDF de 493 hojas).
  - test_flechas_de_carga_entran_en_la_figura: la figura del modelo reserva
    margen para las colas de sus flechas de carga (caian fuera de la imagen
    y cruzaban el titulo).
  - test_matrices_sin_ceros_falsos: ninguna entrada real de K, k_e o de los
    vectores globales se imprime como cero (el formato factorizado aplastaba
    64 celdas de 324 en la k_e 18x18 del Q9).
  - test_vector_compacto_entra_en_el_renglon: las entradas por renglon del
    vector salen del ancho de celda, no de un 12 fijo.
  - test_equilibrio_cuenta_las_cargas_superficiales: el residuo de
    equilibrio usa el vector F del solver (sumar solo las cargas nodales
    daba residuo del 100 % en la membrana de Cook).
  - test_condicionamiento_se_mide_sobre_K_ff: el kappa_2 con veredicto va
    sobre K_ff; la K sin restricciones es singular y marcaba 'Critico'
    en todos los modelos.
  - test_maqueta_sin_desbordes_ni_hojas_flojas: compila Q4 educativo y
    Q9 directo y mide el PDF: 0 Overfull hbox, 0 hojas apaisadas y una
    cota de hojas. Es el unico test que mira la MAQUETACION.
  - test_notas_mandan_al_lugar_correcto: una tabla recortada no manda al
    CSV del modelo, que no lleva resultados; los desplazamientos,
    tensiones y reacciones van a la tabla del Post-Proceso.
  - test_hub_*: chequeos del Theory Hub (post-proceso, numeracion M3=B/M4=D,
    rangos de calidad, LU sin internals, sin Mohr,
    BCs por eliminacion, TOC clickeable, sin bibliografia).
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np

from functools import lru_cache

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
    """TeX Live embebido (vendor/texlive o EDUFEM_TEXLIVE_DIR) o pdflatex del PATH.

    Con `--sin-compilar` devuelve False a propósito, y los cuatro tests que
    compilan un PDF se saltan solos. Es lo que usa el gate RÁPIDO: los otros
    38 tests sólo generan el `.tex` y corren en segundos, así que las
    invariantes del documento (sin índice, sin apaisadas, sin ceros falsos,
    equilibrio, condicionamiento) quedaban fuera de la condición de push por
    culpa de los cuatro que sí necesitan compilador.
    """
    if "--sin-compilar" in sys.argv:
        return False
    from education.components.latex_runtime import find_latex_runtime
    return find_latex_runtime() is not None


def _solved_example():
    project = load_example_project()
    solution = solve_system(project)
    project.is_solved = True
    es, ns = compute_all_stresses(project, solution)
    return project, solution, es, ns


@lru_cache(maxsize=None)
def _tex(style: str = "educativo") -> str:
    """El .tex del ejemplo canonico Q4. MEMOIZADO: media docena de tests
    lo piden y construir el documento entero cuesta segundos."""
    project, solution, es, ns = _solved_example()
    mem = MemoriaCalculo(project, solution, es, ns, style=style)
    mem.build()
    return mem.tex_source()


@lru_cache(maxsize=None)
def _tex_q9(style: str = "educativo"):
    """El .tex del ejemplo Q9, o None si el loader no esta.

    Los chequeos estructurales corrian SOLO sobre Q4, y los dos casos
    que el rediseno vino a arreglar —las hojas apaisadas de la B 3x18 y
    la k_e 18x18— son Q9-only: el test que prohibe `landscape` nunca
    veia el documento que lo tenia.
    """
    project = _load_q9_o_none()
    if project is None:
        return None
    solution = solve_system(project)
    project.is_solved = True
    es, ns = compute_all_stresses(project, solution)
    mem = MemoriaCalculo(project, solution, es, ns, style=style)
    mem.build()
    return mem.tex_source()


def _tex_todos(style: str):
    """[(etiqueta, tex)] de Q4 y Q9 en el estilo pedido."""
    casos = [(f"Q4/{style}", _tex(style))]
    tex_q9 = _tex_q9(style)
    if tex_q9 is not None:
        casos.append((f"Q9/{style}", tex_q9))
    return casos


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


def test_nada_se_sale_de_la_hoja() -> bool:
    r"""Ninguna tabla ni formula se imprime fuera del ancho de la hoja.

    El reporte de campo (2026-09-16) llego con capturas del PDF: las dos
    tablas de tensiones —ocho y siete columnas, cada una rotulada
    `$\sigma$ [kgf/cm2]`— se cortaban por la derecha. `pdflatex` ya lo
    denuncia en su log (`Overfull \hbox ... too wide`), solo que nadie lo
    miraba.

    Se usa el ejemplo de Timoshenko y NO el canonico porque el desborde
    depende del sistema de unidades: con `MPa` el encabezado entra, con
    `kgf/cm\textsuperscript{2}` no. El canonico nunca lo habria mostrado.

    Medido antes de los arreglos de esa fecha: 8 desbordes, el peor de 89,9
    pt (margenes de 2,2 cm) y de 50,0 pt ya con los 1,5 cm; mas una entrada
    simbolica `K_11` de 566,2 pt en los modelos Q4. Ahora: cero.
    """
    print("test_nada_se_sale_de_la_hoja ...")
    if not _has_pdflatex():
        print("  SKIP: pdflatex no encontrado en PATH")
        return True
    import re
    import subprocess
    from education.components.latex_runtime import find_latex_runtime
    from models.example_library import load_example_timoshenko_q9

    project = load_example_timoshenko_q9()
    solution = solve_system(project)
    project.is_solved = True
    es, ns = compute_all_stresses(project, solution)
    memoria = MemoriaCalculo(project, solution, es, ns, style="educativo")
    memoria.build()
    runtime = find_latex_runtime()
    with tempfile.TemporaryDirectory() as tmpdir:
        tex = os.path.join(tmpdir, "documento.tex")
        with open(tex, "w", encoding="utf-8") as f:
            f.write(memoria.tex_source())
        for _ in range(2):      # dos pasadas: indice y referencias
            subprocess.run(
                [runtime.pdflatex, "-interaction=nonstopmode",
                 "-file-line-error", "documento.tex"],
                cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        log_path = os.path.join(tmpdir, "documento.log")
        if not os.path.exists(log_path):
            print("  FAIL: pdflatex no dejo log")
            return False
        with open(log_path, encoding="utf-8", errors="replace") as f:
            log = f.read()
    anchos = [float(x) for x in
              re.findall(r"Overfull .hbox \(([0-9.]+)pt too wide\)", log)]
    if anchos:
        print(f"  FAIL: {len(anchos)} caja(s) fuera de la hoja, la peor de "
              f"{max(anchos):.1f} pt")
        return False
    print("  OK: ninguna tabla ni formula se sale de la hoja")
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


def test_longtable_cuenta_columnas_de_parrafo() -> bool:
    """`p{4.3cm}` es UNA columna, no ocho caracteres.

    `_longtable` descartaba el preambulo cuando `len(col_align) != n_cols`:
    el glosario (`lp{10cm}`) y la tabla de diagnostico
    (`lp{4.3cm}p{6.2cm}`) caian al `l` por defecto, que no corta linea. Las
    recomendaciones del validador se salian **673 pt** del margen derecho
    (medido con pdflatex sobre Cook Q9), o sea fuera de la hoja."""
    print("test_longtable_cuenta_columnas_de_parrafo ...")
    cuenta = MemoriaCalculo._count_col_specs
    casos = [("rrrr", 4), ("lp{10cm}", 2), ("lp{4.3cm}p{6.2cm}", 3),
             ("ccrrrrrr", 8), ("l|r", 2), ("m{2cm}b{3cm}c", 3)]
    for spec, esperado in casos:
        got = cuenta(spec)
        if got != esperado:
            print(f"  FAIL: '{spec}' cuenta {got} columnas, no {esperado}")
            return False
    tex = _tex("educativo")
    if r"\begin{longtable}{lp{10cm}}" not in tex:
        print("  FAIL: el glosario perdio su columna de parrafo p{10cm}")
        return False
    # Tabla de diagnostico: solo aparece si el modelo tiene hallazgos.
    from models.material import Material
    project, solution, es, ns = _solved_example()
    project.materials["Sin usar"] = Material("Sin usar", 210000.0, 0.3)
    mem = MemoriaCalculo(project, solution, es, ns, style="directo")
    mem.build()
    tex_diag = mem.tex_source()
    if r"\begin{longtable}{lp{4.3cm}p{6.2cm}}" not in tex_diag:
        print("  FAIL: la tabla de diagnostico perdio sus columnas p{}")
        return False
    print("  OK: glosario y diagnostico conservan sus columnas de parrafo")
    return True


def test_tablas_con_unidades() -> bool:
    """Los encabezados dicen en que unidad estan los numeros.

    Es el mismo rotulado que las tablas del Pre (`X [mm]`, `q Inicio
    [N/mm]`) y del Post (`sigma_x [MPa]`): la Memoria era el unico lugar
    donde los valores llegaban al alumno sin unidad.

    La unidad va APILADA bajo el simbolo (`_th_unidad`), no en la misma
    linea. Con seis columnas de tensiones, repetir `[kgf/cm2]` en linea es lo
    que empujaba las dos tablas de tensiones fuera de la hoja: 89,9 pt con
    margenes de 2,2 cm y 50 pt aun con los 1,5 cm de ahora. Apilada, la
    columna mide lo que mide la unidad y la tabla entra, sin perder el
    rotulo, que `longtable` repite en cada hoja. El formato se escribe aca
    literal —y no llamando a `_th_unidad`— para que el test siga siendo un
    control externo del `.tex` y no un espejo del codigo que lo genera.
    """
    print("test_tablas_con_unidades ...")
    from config.units import get_unit_labels
    project = load_example_project()
    u = get_unit_labels(project.unit_system)
    L, F, S = u["longitud"], u["fuerza"], u["esfuerzo"]

    def apilado(simbolo: str, unidad: str) -> str:
        return (r"\shortstack{" + simbolo + r"\\[1pt]{\scriptsize ["
                + unidad + "]}}")

    for style in ("educativo", "directo"):
        tex = _tex(style)
        esperados = [
            apilado("$X$", L), apilado("$Y$", L), apilado("Espesor", L),
            apilado("$F_x$", F), apilado("$R_x$", F), apilado("$u_x$", L),
            apilado(r"$\sigma_x$", S), apilado(r"$\sigma_{VM}$", S),
            apilado("$E$", S),
        ]
        faltan = [e for e in esperados if e not in tex]
        if faltan:
            print(f"  FAIL ({style}): encabezados sin unidad apilada: {faltan}")
            return False
        # Y que no haya quedado ninguno en linea: mezclar los dos formatos
        # deja dos estilos de encabezado conviviendo en la misma hoja.
        en_linea = [e for e in (f"$X$ [{L}]", f"$F_x$ [{F}]",
                                f"$\\sigma_x$ [{S}]") if e in tex]
        if en_linea:
            print(f"  FAIL ({style}): encabezados en linea sin apilar: "
                  f"{en_linea}")
            return False
    print(f"  OK: encabezados apilados con [{L}] / [{F}] / [{S}] en ambos "
          f"estilos")
    return True


def test_contorno_rotulo_con_simbolo_y_unidad() -> bool:
    """La colorbar del contorno dice el simbolo del campo y su unidad.

    Era el unico resultado que llegaba al alumno sin unidad y con la key
    interna (`sigma_x`) como rotulo, mientras la colorbar del lienzo y la de
    la Vista 3D muestran `sigma_x [MPa]`."""
    print("test_contorno_rotulo_con_simbolo_y_unidad ...")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("  SKIP: Pillow no disponible")
        return True
    from file_io import figure_export as fx
    from config.units import get_unit_labels
    project = load_example_project()
    if fx._resolve_ttf() is None:
        print("  SKIP: sin fuente TrueType (los rotulos degradan a ASCII)")
        return True
    esperado = {"sigma_x": "σx", "sigma_y": "σy",
                "tau_xy": "τxy", "von_mises": "σVM"}
    for comp, sym in esperado.items():
        got = fx._component_label(comp)
        if got != sym:
            print(f"  FAIL: rotulo de {comp} es '{got}', se esperaba '{sym}'")
            return False
    unidad = fx._stress_unit(project)
    esperada = get_unit_labels(project.unit_system)["esfuerzo"]
    if unidad != esperada:
        print(f"  FAIL: unidad '{unidad}' != '{esperada}' del sistema "
              f"'{project.unit_system}'")
        return False
    # Los ticks de la escala comparten formato con la colorbar del lienzo.
    from config.settings import fmt_escala
    import inspect
    src = inspect.getsource(fx._draw_colorbar)
    if "fmt_escala" not in src:
        print("  FAIL: los ticks de la colorbar no pasan por fmt_escala")
        return False
    if fmt_escala(2.5e7) != "2.50e+07":
        print("  FAIL: fmt_escala no da el formato esperado")
        return False
    print(f"  OK: rotulos griegos + unidad '{unidad}' + ticks fmt_escala")
    return True


def test_figuras_lod_en_malla_densa() -> bool:
    """En una malla densa la deformada muestra la deformada, no una mancha.

    `render_deformed` dibujaba un disco por nodo a cualquier escala: con Cook
    16x16 Q9 (1089 nodos) los discos tapaban por completo la malla verde, que
    es lo unico que la figura tiene que mostrar. Ahora los nodos siguen el
    mismo LOD que el canvas (`canvas_logic.lod_level`) y las mallas de pocos
    elementos se ven exactamente igual que antes."""
    print("test_figuras_lod_en_malla_densa ...")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("  SKIP: Pillow no disponible")
        return True
    from file_io import figure_export as fx
    from models.example_library import load_example_cook_q9

    # (a) El ejemplo canonico (4 elementos) nunca se degrada.
    project = load_example_project()
    view = fx._View([n.x for n in project.nodes.values()],
                    [n.y for n in project.nodes.values()],
                    900, 680, pad_left=36, pad_right=36,
                    pad_top=48, pad_bottom=36)
    lod, _ = fx._detail(project, view)
    if lod != "near":
        print(f"  FAIL: el ejemplo canonico degrado a '{lod}' (debe ser near)")
        return False

    # (b) Malla densa: la deformada verde tiene que verse.
    dense = load_example_cook_q9(N=16)
    solution = solve_system(dense)
    img = fx.render_deformed(dense, solution)
    if img is None:
        print("  FAIL: render_deformed devolvio None")
        return False
    arr = np.asarray(img.convert("RGB"), dtype=int)
    verde = int((np.abs(arr - np.array(fx._RGB_DEFORMED)).sum(axis=2)
                 < 30).sum())
    # Medido: 14 590 px con un disco por nodo, 30 252 px sin ellos. El piso
    # deja margen de sobra y falla si vuelven los discos.
    if verde < 22000:
        print(f"  FAIL: solo {verde} px de malla deformada visibles "
              f"(los discos de nodo la estan tapando)")
        return False
    print(f"  OK: canonico='near'; Cook 16x16 con {verde} px de deformada")
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


def test_hub_tiene_post_proceso() -> bool:
    """La seccion de post-proceso cubre la cadena PG -> nodo -> invariantes.

    Antes pedia el literal "M8": esa seccion se llamaba "M8 . Post-proceso",
    pero el ex-M8 fue consolidado en el Post-Proceso nativo en 2026-05 y el
    Post no tiene ningun modulo educativo, asi que el numero nombraba un
    modulo inexistente. Hoy la seccion no lleva prefijo de modulo (como la de
    convergencia) y el chequeo pide el titulo real.
    """
    print("test_hub_tiene_post_proceso ...")
    tex = _build_hub_tex()
    required = ["Post-proceso", "Extrapolación", "Promediado", "principales",
                "Mises", "Barlow"]
    missing = [s for s in required if s not in tex]
    if missing:
        print(f"  FAIL: faltan en el post-proceso del Hub: {missing}")
        return False
    for phantom in ("M8", "M9"):
        if phantom in tex:
            print(f"  FAIL: el Hub nombra un modulo inexistente: {phantom}")
            return False
    print("  OK: Hub post-proceso cubre PG/extrapolación/promediado/"
          "principales/VM, sin M8 ni M9")
    return True


def test_hub_numeracion_modulos() -> bool:
    """M3 = matriz B y M4 = matriz D, igual que Ctrl+3 y Ctrl+4 en la app.

    Estaban cruzadas desde el swap B<->D de 2026-05: el Hub titulaba
    "M3 . Matriz constitutiva D" y "M4 . Matriz B", asi que un alumno que
    leia la seccion M4 y apretaba Ctrl+4 se encontraba con otra matriz.
    """
    print("test_hub_numeracion_modulos ...")
    tex = _build_hub_tex()
    idx_b = tex.find("Matriz B (deformaci")
    idx_d = tex.find("Matriz constitutiva D")
    if idx_b < 0 or idx_d < 0:
        print("  FAIL: no se encontraron las secciones de B y D")
        return False
    # El numero pegado a cada titulo (el Hub numera las secciones con el
    # modulo que las ilustra).
    if "M3 · Matriz B" not in tex:
        print("  FAIL: la matriz B no esta numerada como M3")
        return False
    if "M4 · Matriz constitutiva D" not in tex:
        print("  FAIL: la matriz D no esta numerada como M4")
        return False
    if idx_b > idx_d:
        print("  FAIL: D aparece antes que B (el pipeline es N -> J -> B -> D)")
        return False
    print("  OK: M3 = B y M4 = D, en el orden del pipeline")
    return True


def test_hub_rango_metricas_calidad() -> bool:
    """M0 del Hub no puede decir que las dos metricas viven en [0,1].

    El Jacobiano escalado se presenta en [-1,1] (rango completo de Verdict,
    el signo distingue la validez) y la compacidad en [0,1]; ademas los
    umbrales aceptables son distintos (0,50 y 0,25). El Hub afirmaba las dos
    cosas contrarias en la misma seccion, y contradecia la barra que el
    alumno ve en M0.
    """
    print("test_hub_rango_metricas_calidad ...")
    tex = _build_hub_tex()
    if "ambas normalizadas al rango $[0,1]$" in tex:
        print("  FAIL: el Hub sigue diciendo que ambas metricas viven en [0,1]")
        return False
    if "Ambas métricas viven en $[0,1]$" in tex:
        print("  FAIL: el Hub sigue igualando los rangos de las dos metricas")
        return False
    if "$[-1,1]$" not in tex:
        print("  FAIL: el Hub no menciona el rango [-1,1] del Jacobiano")
        return False
    print("  OK: rangos y umbrales por metrica, coherentes con M0")
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


# ─── Aprovechamiento de la hoja (2026-09-09) ───────────────────────────────

def test_tex_sin_indice_ni_apaisado() -> bool:
    """El indice impreso y las hojas apaisadas se quitaron a pedido del autor.

    El sumario eran dos hojas que nadie lee (para navegar estan los
    marcadores del PDF, que hyperref sigue generando) y cada `landscape`
    hace `\\clearpage` antes Y despues: una matriz apaisada costaba tres
    hojas, dos de ellas casi vacias.
    """
    print("test_tex_sin_indice_ni_apaisado ...")
    ok = True
    for style in ("educativo", "directo"):
        for etiqueta, tex in _tex_todos(style):
            if r"\tableofcontents" in tex:
                print(f"  FAIL: {etiqueta} reintrodujo el indice impreso")
                ok = False
            if "landscape" in tex:
                print(f"  FAIL: {etiqueta} reintrodujo hojas apaisadas")
                ok = False
    if ok:
        print("  OK: sin sumario impreso ni hojas apaisadas, en Q4 y Q9")
    return ok


def test_tex_portada_en_una_hoja() -> bool:
    """Ficha + diagrama del modelo + mapa del calculo comparten la portada.

    Antes eran tres hojas al 30-45 %: ficha a una columna, mapa solo y
    diagrama solo. Ademas el diagrama estaba detras de `if self._prose`, asi
    que el estilo 'directo' no tenia NINGUNA vista del modelo aunque todas
    sus tablas citan numeros de nodo.
    """
    print("test_tex_portada_en_una_hoja ...")
    ok = True
    for style in ("educativo", "directo"):
        tex = _tex(style)
        if "fig:mesh" not in tex:
            print(f"  FAIL: {style} sin diagrama del modelo")
            ok = False
        # Ficha a dos columnas: cuatro columnas de tabular (clave/valor x2).
        if r"lr@{\hspace{1.1cm}}lr" not in tex:
            print(f"  FAIL: {style} volvio a la ficha de una sola columna")
            ok = False
        # Nada de saltos forzados entre el titulo y el primer capitulo.
        cuerpo = tex.split(r"\maketitle", 1)[-1]
        portada = cuerpo.split(r"\section{", 1)[0]
        if r"\newpage" in portada:
            print(f"  FAIL: {style} parte la portada con \\newpage")
            ok = False
    if r"¿Qué resuelve el MEF y cómo?" not in _tex("educativo"):
        print("  FAIL: el mapa del calculo perdio su encabezado")
        ok = False
    if ok:
        print("  OK: portada de una hoja, con diagrama del modelo en ambos "
              "estilos")
    return ok


def test_tex_contornos_en_grilla() -> bool:
    """Los cuatro contornos van en grilla 2x2, no uno debajo del otro.

    Apilados a 0,82\\textwidth ocupaban dos hojas al 85 %. La grilla los
    mete en una y, como el render tambien se achica en la misma proporcion,
    los rotulos de la escala quedan igual de legibles.
    """
    print("test_tex_contornos_en_grilla ...")
    ok = True
    for style in ("educativo", "directo"):
        for etiqueta, tex in _tex_todos(style):
            n_sub = tex.count(r"\begin{subfigure}")
            if n_sub != 4:
                print(f"  FAIL: {etiqueta} tiene {n_sub} subfiguras de "
                      f"contorno, esperaba 4")
                ok = False
            n_fig = tex.count("fig:contornos")
            if n_fig != 2:
                print(f"  FAIL: {etiqueta} tiene {n_fig} filas de contornos, "
                      f"esperaba 2")
                ok = False
    if ok:
        print("  OK: 4 contornos en 2 filas de 2, en ambos estilos")
    return ok


def test_tex_sin_duplicar_D_ni_isoparametrico() -> bool:
    """Ni la D numerica ni la caja del isoparametrico se imprimen dos veces.

    La D numerica salia en el capitulo 1 y otra vez en la formulacion
    elemental; la caja "las mismas N_i interpolan geometria y
    desplazamiento" estaba palabra por palabra en la subseccion 1.1 y en
    "Funciones de forma en los puntos de Gauss".
    """
    print("test_tex_sin_duplicar_D_ni_isoparametrico ...")
    ok = True
    # Marcador REAL, verificado contra el .tex: el anterior ("eso es")
    # daba 0 ocurrencias, o sea que el assert `n_iso > 1` no medía nada.
    marca_iso = r"Las mismas $N_i$ interpolan geometría \emph{y} "
    marca_iso += "desplazamiento"
    for style in ("educativo", "directo"):
        tex = _tex(style)
        # La D numerica es la unica bmatrix rotulada \mathbf{D} con numeros;
        # la simbolica lleva el factor E/(1-nu^2) delante.
        n_d = tex.count(r"\mathbf{D} = \begin{bmatrix}")
        if n_d != 1:
            print(f"  FAIL: {style} emite {n_d} veces la D numerica, "
                  f"esperaba 1")
            ok = False
        if r"\frac{E}" not in tex:
            print(f"  FAIL: {style} perdio la D simbolica")
            ok = False
        # `== 1` en educativo, no `> 1`: con `> 1` un marcador que dejara de
        # existir haria pasar el test sin medir nada, que es exactamente lo
        # que pasaba antes. En `directo` no hay cajas, asi que debe ser 0.
        n_iso = tex.count(marca_iso)
        esperado = 1 if style == "educativo" else 0
        if n_iso != esperado:
            print(f"  FAIL: {style} emite {n_iso} veces la caja del "
                  f"isoparametrico, esperaba {esperado}")
            ok = False
    # El enunciado de las N_i sigue estando (se mudo al capitulo donde estan
    # sus valores, no se borro).
    for style in ("educativo", "directo"):
        if r"N_i(\xi,\eta)" not in _tex(style):
            print(f"  FAIL: {style} perdio el enunciado de las N_i")
            ok = False
    if ok:
        print("  OK: D simbolica + D numerica una vez cada una, sin cajas "
              "repetidas")
    return ok


def test_max_matrix_cols_cubre_la_matriz_mas_ancha() -> bool:
    """`MaxMatrixCols` declarado >= la bmatrix mas ancha del documento.

    `amsmath` corta en 10 columnas por defecto y pasarse no avisa: aborta
    con `Extra alignment tab` y el alumno no recibe NINGUN PDF. Una K de 22
    columnas (malla Q4 de 11 nodos) hacia exactamente eso.
    """
    print("test_max_matrix_cols_cubre_la_matriz_mas_ancha ...")
    import re as _re
    ok = True
    for style in ("educativo", "directo"):
        tex = _tex(style)
        declarados = [int(n) for n in
                      _re.findall(r"\\setcounter\{MaxMatrixCols\}\{(\d+)\}",
                                  tex)]
        if not declarados:
            print(f"  FAIL: {style} no declara MaxMatrixCols")
            ok = False
            continue
        tope = max(declarados)
        peor = 0
        for cuerpo in _re.findall(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}",
                                  tex, _re.S):
            for fila in cuerpo.split(r"\\"):
                peor = max(peor, fila.count("&") + 1)
        if peor > tope:
            print(f"  FAIL: {style} emite una bmatrix de {peor} columnas con "
                  f"MaxMatrixCols={tope}")
            ok = False
    if ok:
        print(f"  OK: la bmatrix mas ancha entra en el MaxMatrixCols "
              f"declarado")
    return ok


def test_recuperacion_epsilon_reproduce_sigma() -> bool:
    """La tabla ε = B·u_e → σ = D·ε tiene que cerrar con las σ del solver.

    `gauss_stresses` no guarda la deformacion, y la tabla leia una clave
    inexistente: imprimia ε = 0 al lado de σ != 0, imposible y en
    contradiccion con la formula de la misma hoja — justo en la tabla que
    existe para verificar esa cadena.
    """
    print("test_recuperacion_epsilon_reproduce_sigma ...")
    from fem.constitutive import constitutive_matrix
    ok = True
    for nombre, loader in (("Q4", load_example_project),
                           ("Q9", _load_q9_o_none)):
        project = loader() if loader is not None else None
        if project is None:
            continue
        solution = solve_system(project)
        project.is_solved = True
        es, ns = compute_all_stresses(project, solution)
        mem = MemoriaCalculo(project, solution, es, ns)
        eid = mem._showcase_id()
        if eid is None:
            print(f"  SKIP {nombre}: sin elemento estrella")
            continue
        eps = mem._deformaciones_por_gauss(eid)
        if not eps:
            print(f"  FAIL {nombre}: no se recuperaron las deformaciones")
            ok = False
            continue
        if all(float(np.max(np.abs(e))) == 0.0 for e in eps):
            print(f"  FAIL {nombre}: todas las deformaciones son cero")
            ok = False
            continue
        elem = project.elements[eid]
        mat = project.materials[elem.material_name]
        D = constitutive_matrix(mat.E, mat.nu, project.analysis_type)
        gauss = es[eid]["gauss_stresses"]
        peor = 0.0
        for e, gs in zip(eps, gauss):
            sig = np.asarray(D) @ np.asarray(e).ravel()
            ref = np.array([gs["sigma_x"], gs["sigma_y"], gs["tau_xy"]])
            escala = max(float(np.max(np.abs(ref))), 1e-12)
            peor = max(peor, float(np.max(np.abs(sig - ref))) / escala)
        if peor > 1e-9:
            print(f"  FAIL {nombre}: D*eps no reproduce sigma "
                  f"(error relativo {peor:.2e})")
            ok = False
        else:
            print(f"  {nombre}: D*eps reproduce sigma, error {peor:.1e}")
    if ok:
        print("  OK: la cadena eps = B*u_e -> sigma = D*eps cierra")
    return ok


def test_maqueta_sin_desbordes_ni_hojas_flojas() -> bool:
    """Mide la MAQUETACION del PDF, no solo que compile.

    Todo el trabajo de aprovechamiento de hoja (portada de una hoja, sin
    indice, sin apaisadas, contornos en grilla, matrices en bloques, tablas
    topeadas) no tenia ningun assert: los tests solo miraban que el PDF
    pesara mas de 5 KB, dos ordenes de magnitud por debajo de los 600 KB
    reales. Este test compila y mide lo que el cambio prometio:

      - cero `Overfull \hbox` (texto impreso fuera de la hoja),
      - cero hojas apaisadas,
      - una cota de hojas por caso.

    Cubre ademas **Q9 + directo**, la unica de las cuatro combinaciones que
    no se compilaba nunca y la que mas `matrix_blocks` emite.
    """
    print("test_maqueta_sin_desbordes_ni_hojas_flojas ...")
    if not _has_pdflatex():
        print("  SKIP: pdflatex no encontrado en PATH")
        return True
    try:
        import fitz  # noqa: F401
    except ImportError:
        print("  SKIP: PyMuPDF no disponible")
        return True
    import re as _re
    import shutil

    try:
        from tests.example_data import load_example_project_q9
    except ImportError:
        print("  SKIP: load_example_project_q9 no disponible")
        return True

    # (nombre, loader, estilo, tope de hojas)
    casos = [
        ("Q4 educativo", load_example_project, "educativo", 22),
        ("Q9 directo", load_example_project_q9, "directo", 20),
    ]
    ok = True
    for nombre, loader, style, tope in casos:
        project = loader()
        solution = solve_system(project)
        project.is_solved = True
        es, ns = compute_all_stresses(project, solution)
        mem = MemoriaCalculo(project, solution, es, ns, style=style)
        mem.build()
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "maqueta")
            workdir = mem._ensure_tmpdir()
            try:
                mem._td.compile_to(base, keep_tex=True, workdir=workdir)
                for f in os.listdir(workdir):
                    if f.endswith(".log"):
                        shutil.copy(os.path.join(workdir, f), base + ".log")
                        break
            finally:
                mem._cleanup_tmpdir()
            if not Path(base + ".pdf").exists():
                print(f"  FAIL: {nombre}: no se genero el PDF")
                ok = False
                continue
            texto = ""
            if Path(base + ".log").exists():
                texto = Path(base + ".log").read_text(
                    encoding="utf-8", errors="replace")
            over = _re.findall(
                r"Overfull \\hbox \(([\d.]+)pt too wide\)", texto)
            if over:
                peor = max(float(x) for x in over)
                print(f"  FAIL: {nombre}: {len(over)} Overfull hbox "
                      f"(el peor, {peor:.1f} pt fuera de la hoja)")
                ok = False
            import fitz as _fitz
            doc = _fitz.open(base + ".pdf")
            paginas = doc.page_count
            apaisadas = sum(1 for pg in doc if pg.rect.width > pg.rect.height)
            doc.close()
            if apaisadas:
                print(f"  FAIL: {nombre}: {apaisadas} hojas apaisadas")
                ok = False
            if paginas > tope:
                print(f"  FAIL: {nombre}: {paginas} hojas (tope {tope})")
                ok = False
            if ok:
                print(f"  {nombre}: {paginas} hojas, 0 overfull, 0 apaisadas")
    if ok:
        print("  OK: la maquetacion entra en la hoja en los casos medidos")
    return ok


def test_notas_mandan_al_lugar_correcto() -> bool:
    """Una tabla recortada no puede mandar al alumno a un lugar vacio.

    `file_io.model_io.export_model_csv` exporta SOLO el modelo (nodos,
    elementos, materiales, cargas, restricciones, cargas superficiales): no
    lleva desplazamientos, ni tensiones, ni reacciones, ni metricas de
    calidad. La nota decia "Archivo, Exportar, Modelo Excel/CSV" debajo de
    las cinco tablas topeadas, asi que el alumno que buscaba el valor de un
    nodo recortado abria el ZIP y no encontraba ni un numero.

    Destinos correctos: desplazamientos, tensiones nodales y reacciones ->
    la tabla de Resultados Numericos del Post-Proceso (Ctrl+A, Ctrl+C copia
    todas las filas). Puntos de Gauss y calidad de malla -> ninguno, y
    entonces la nota no promete nada.
    """
    print("test_notas_mandan_al_lugar_correcto ...")
    import re as _re
    try:
        from models.example_library import load_example_cook_q9
    except Exception as exc:
        print(f"  SKIP: no se pudo cargar Cook Q9 ({exc})")
        return True
    project = load_example_cook_q9(N=8)
    solution = solve_system(project)
    project.is_solved = True
    es, ns = compute_all_stresses(project, solution)
    ok = True
    for style in ("educativo", "directo"):
        mem = MemoriaCalculo(project, solution, es, ns, style=style)
        mem.build()
        tex = mem.tex_source()
        notas = [" ".join(m.group(1).split()) for m in
                 _re.finditer(r"Se (?:listan|muestran) (.{0,340}?)\}", tex,
                              _re.S)]
        if not notas:
            print(f"  FAIL: {style}: no se encontro ninguna nota de "
                  f"muestreo; el test no esta midiendo nada")
            return False
        # Lo que NO puede pasar: una nota de resultados apuntando al CSV.
        RESULTADOS = ("desplazamiento", "tension", "tensiones", "reaccion",
                      "reacciones", "punto de Gauss", "puntos de Gauss",
                      "Jacobiano escalado")
        for nota in notas:
            if "Modelo Excel/CSV" not in nota:
                continue
            bajo = nota.lower()
            if any(p.lower() in bajo for p in RESULTADOS):
                print(f"  FAIL: {style}: una nota de resultados manda al CSV "
                      f"del modelo, que no los contiene: {nota[:110]}")
                ok = False
        n_csv = sum(1 for n in notas if "Modelo Excel/CSV" in n)
        n_post = sum(1 for n in notas if "Post-Proceso" in n)
        if n_post == 0:
            print(f"  FAIL: {style}: ninguna nota manda a la tabla del "
                  f"Post-Proceso, que es donde estan los resultados")
            ok = False
        if ok:
            print(f"  {style}: {len(notas)} notas, {n_csv} al CSV del modelo, "
                  f"{n_post} a la tabla del Post-Proceso")
    if ok:
        print("  OK: cada nota manda al lugar que si tiene el dato completo")
    return ok


def test_equilibrio_cuenta_las_cargas_superficiales() -> bool:
    """El equilibrio se verifica contra el vector F del solver.

    Sumaba solo `project.nodal_loads`, asi que cualquier modelo cargado por
    presion de borde salia con "Cargas aplicadas = 0" frente a las
    reacciones completas: **residuo del 100 %**. La membrana de Cook, un
    ejemplo del propio menu Ayuda, recibia el veredicto rojo 'Critico' en un
    modelo sano cuyo residuo real es 1e-13.
    """
    print("test_equilibrio_cuenta_las_cargas_superficiales ...")
    try:
        from models.example_library import load_example_cook_q9
    except Exception as exc:
        print(f"  SKIP: no se pudo importar Cook Q9 ({exc})")
        return True
    ok = True
    casos = [("Q4 canonico (cargas nodales)", load_example_project),
             ("Cook Q9 (carga superficial)", lambda: load_example_cook_q9(N=4))]
    for nombre, loader in casos:
        project = loader()
        solution = solve_system(project)
        project.is_solved = True
        es, ns = compute_all_stresses(project, solution)
        mem = MemoriaCalculo(project, solution, es, ns)
        res = mem._equilibrio_residuo_rel()
        if res is None:
            print(f"  FAIL: {nombre}: no se pudo calcular el residuo")
            ok = False
            continue
        if res > 1e-6:
            print(f"  FAIL: {nombre}: residuo relativo {res:.3e} en un modelo "
                  f"en equilibrio (deberia ser ~0)")
            ok = False
        else:
            print(f"  {nombre}: residuo relativo {res:.1e}")
    if ok:
        print("  OK: el equilibrio incluye las fuerzas equivalentes")
    return ok


def test_condicionamiento_se_mide_sobre_K_ff() -> bool:
    """El kappa_2 con veredicto se mide sobre K_ff, no sobre K.

    K sin restricciones es singular por construccion (3 modos de cuerpo
    rigido del plano), asi que su kappa_2 da ~1e17 en CUALQUIER modelo y el
    capitulo de diagnostico marcaba 'Critico' hasta en el ejemplo canonico,
    cuya K_ff tiene kappa_2 = 32,6. Un indicador que se enciende siempre no
    informa nada, y este vive donde el documento dice si confiar o no.
    """
    print("test_condicionamiento_se_mide_sobre_K_ff ...")
    ok = True
    for style in ("educativo", "directo"):
        tex = _tex(style)
        if r"$\kappa_2(\mathbf{K}_{ff})$ (estimado)" not in tex:
            print(f"  FAIL: {style} no reporta kappa_2 de K_ff en el "
                  f"diagnostico")
            ok = False
        # La K sin restricciones puede seguir mostrandose, pero rotulada.
        if r"$\kappa_2(\mathbf{K})$ (estimado)" in tex:
            print(f"  FAIL: {style} sigue rotulando la K singular como si "
                  f"fuera el indicador de condicionamiento")
            ok = False
    # Y el numero tiene que dar OK en un modelo sano.
    project, solution, es, ns = _solved_example()
    from file_io.memoria_calculo import _K_cond
    cond_ff = _K_cond(solution.get("K_red"))
    cond_k = _K_cond(solution.get("K"))
    if cond_ff is None:
        print("  FAIL: no se pudo estimar kappa_2(K_ff)")
        ok = False
    elif cond_ff >= 1e8:
        print(f"  FAIL: kappa_2(K_ff) = {cond_ff:.2e} en el ejemplo canonico "
              f"(deberia ser chico)")
        ok = False
    if ok:
        print(f"  OK: kappa_2(K_ff) = {cond_ff:.2e} (la K completa da "
              f"{cond_k:.2e}, singular)")
    return ok


def test_matrices_sin_ceros_falsos() -> bool:
    """Ninguna entrada real de K, k_e o de los vectores se imprime como cero.

    El formato factorizado fijaba `sig_digits - 1` decimales, asi que toda
    entrada por debajo del 0,5 % del maximo salia `0.00`, indistinguible de
    un cero estructural: 64 celdas de 324 en la k_e 18x18 del Q9 canonico,
    que NO tiene un solo cero de verdad, y 32 de 256 en una K de 16 GDL.
    En un documento que existe para verificar resultados eso no es un
    redondeo: es un numero equivocado. Ahora los decimales los elige
    `TheoryDoc._decidir_formato` a partir del rango dinamico real.

    El ruido de punto flotante SI puede imprimirse como cero: un 1e-18 al
    lado de un 1e+06 es un cero fisico. El criterio es `RELATIVE_ZERO`.
    """
    print("test_matrices_sin_ceros_falsos ...")

    def es_cero_impreso(celda: str) -> bool:
        limpio = celda.strip().replace("-", "").replace(".", "").replace("0", "")
        return limpio in ("", "e+", "e-")

    def falsos(A, sig_digits, umbral_rango=1e4):
        A = np.asarray(A, dtype=float)
        modo, p, dec = TheoryDoc._decidir_formato(
            A, sig_digits=sig_digits, dynamic_range_threshold=umbral_rango,
            tol=1e-30)
        abs_A = np.abs(A)
        if not abs_A.max():
            return modo, 0
        significativa = abs_A > abs_A.max() * TheoryDoc.RELATIVE_ZERO
        if modo == "cientifica":
            txt = np.vectorize(lambda x: f"{x:.{dec}e}")(A)
        elif modo == "factor":
            txt = np.vectorize(lambda x: f"{x:.{dec}f}")(A / (10.0 ** p))
        else:
            return modo, 0
        impreso_cero = np.vectorize(es_cero_impreso)(txt)
        return modo, int((impreso_cero & significativa).sum())

    from fem.assembly import assemble_global_system
    ok = True
    casos = [("Q4 canonico", load_example_project)]
    if _load_q9_o_none() is not None:
        casos.append(("Q9 canonico", _load_q9_o_none))
    for nombre, loader in casos:
        project = loader()
        K = assemble_global_system(project)[0]
        A = K.toarray() if hasattr(K, "toarray") else np.asarray(K)
        modo, n = falsos(A, 3)
        if n:
            print(f"  FAIL: {nombre}, K {A.shape[0]} GDL ({modo}): {n} celdas "
                  f"no nulas impresas como cero")
            ok = False
        solution = solve_system(project)
        datos = solution.get("element_data", {})
        if datos:
            eid = next(iter(datos))
            ke = np.asarray(datos[eid]["ke"], dtype=float)
            modo, n = falsos(ke, 3)
            if n:
                print(f"  FAIL: {nombre}, k_e {ke.shape} ({modo}): {n} celdas "
                      f"no nulas impresas como cero")
                ok = False
        for clave in ("u", "F", "R"):
            v = solution.get(clave)
            if v is None:
                continue
            modo, n = falsos(np.asarray(v).reshape(-1, 1), 3,
                             MemoriaCalculo._VECTOR_FACTOR_THRESHOLD)
            if n:
                print(f"  FAIL: {nombre}, vector {clave} ({modo}): {n} "
                      f"entradas no nulas impresas como cero")
                ok = False
    if ok:
        print("  OK: K, k_e y los vectores globales sin ceros falsos")
    return ok


def test_vector_compacto_entra_en_el_renglon() -> bool:
    """Las entradas por renglon salen del ancho de celda, no de un 12 fijo.

    Al subir los decimales para no imprimir ceros falsos, la celda del
    vector `u` del Q9 canonico paso de 6 a 7 caracteres y 12 columnas se
    salian 57,1 pt del margen.
    """
    print("test_vector_compacto_entra_en_el_renglon ...")
    ok = True
    for nombre, loader in (("Q4", load_example_project), ("Q9", _load_q9_o_none)):
        project = loader()
        if project is None:
            continue
        solution = solve_system(project)
        project.is_solved = True
        es, ns = compute_all_stresses(project, solution)
        mem = MemoriaCalculo(project, solution, es, ns)
        for clave in ("u", "F", "R"):
            v = solution.get(clave)
            if v is None:
                continue
            a = np.asarray(v).ravel()
            cols = mem._columnas_por_renglon(a)
            ancho = TheoryDoc.cell_width(
                a, sig_digits=3,
                dynamic_range_threshold=MemoriaCalculo._VECTOR_FACTOR_THRESHOLD)
            if cols * ancho > MemoriaCalculo._RENGLON_MAX_CARACTERES:
                print(f"  FAIL: {nombre} {clave}: {cols} columnas de {ancho} "
                      f"caracteres pasan el renglon "
                      f"({MemoriaCalculo._RENGLON_MAX_CARACTERES})")
                ok = False
    if ok:
        print("  OK: el renglon del vector se ajusta al ancho de la celda")
    return ok


def test_flechas_de_carga_entran_en_la_figura() -> bool:
    """La figura del modelo reserva lugar para las flechas de sus cargas.

    La flecha se dibuja desde AFUERA hacia el nodo, asi que la cola cae
    fuera del area que ocupa la malla. Sin reservar ese margen, la carga de
    un nodo del borde superior dibujaba una flecha cuya cola quedaba 47 px
    ARRIBA del borde de la imagen (a 900 px de ancho) y cruzaba el titulo:
    el alumno veia una linea roja entrando desde el borde, encima del texto.
    """
    print("test_flechas_de_carga_entran_en_la_figura ...")
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("  SKIP: Pillow no disponible")
        return True
    from file_io import figure_export as fx
    banda_titulo = 40   # px que ocupa el titulo arriba de la figura
    ok = True
    casos = [("Q4", load_example_project)]
    q9 = _load_q9_o_none
    casos.append(("Q9", q9))
    for nombre, loader in casos:
        project = loader()
        if project is None:
            continue
        for w, h in ((900, 680), (560, 420)):
            flechas = fx._flechas_de_carga(project, w, h)
            if not flechas:
                continue
            mi, md, ma, mb = fx._margen_de_flechas(flechas)
            view = fx._View([n.x for n in project.nodes.values()],
                            [n.y for n in project.nodes.values()], w, h,
                            pad_left=40 + mi, pad_right=40 + md,
                            pad_top=48 + ma, pad_bottom=40 + mb)
            for nid, (ux, uy, largo) in flechas.items():
                n = project.nodes[nid]
                sx, sy = view.w2s(n.x, n.y)
                x0, y0 = sx - ux * largo, sy - uy * largo
                if not (0 <= x0 <= w and 0 <= y0 <= h):
                    print(f"  FAIL: {nombre} {w}x{h}, nodo {nid}: la cola de "
                          f"la flecha cae en ({x0:.0f},{y0:.0f}), fuera de "
                          f"la imagen")
                    ok = False
                elif y0 < banda_titulo:
                    print(f"  FAIL: {nombre} {w}x{h}, nodo {nid}: la cola de "
                          f"la flecha invade la banda del titulo (y={y0:.0f})")
                    ok = False
    if ok:
        print("  OK: las colas de las flechas entran bajo el titulo, en los "
              "dos tamanos de render")
    return ok


def _load_q9_o_none():
    try:
        from tests.example_data import load_example_project_q9
        return load_example_project_q9()
    except Exception:
        return None


def test_tablas_topeadas_en_malla_grande() -> bool:
    """Ninguna tabla vuelca la malla entera.

    Cook Q9 32x32 (4225 nodos, un ejemplo del menu Ayuda) producia un PDF de
    493 hojas, de las cuales 468 eran volcado crudo: 24 184 filas de tabla.
    La Memoria se consulta para verificar un resultado; el censo completo es
    la exportacion a CSV.
    """
    print("test_tablas_topeadas_en_malla_grande ...")
    import re as _re
    try:
        from tests.example_data import load_example_cook_q9
        project = load_example_cook_q9(N=8)
    except Exception as exc:
        print(f"  SKIP: no se pudo cargar Cook Q9 ({exc})")
        return True
    solution = solve_system(project)
    project.is_solved = True
    es, ns = compute_all_stresses(project, solution)
    mem = MemoriaCalculo(project, solution, es, ns)
    mem.build()
    tex = mem.tex_source()
    tope = MemoriaCalculo._TABLA_MAX_FILAS
    ok = True
    peor = 0
    bloques = _re.findall(r"\\begin\{longtable\}.*?\\endfoot(.*?)"
                          r"\\end\{longtable\}", tex, _re.S)
    if not bloques:
        print("  FAIL: no se encontro ninguna longtable en el .tex")
        return False
    for cuerpo in bloques:
        # pylatex cierra cada linea con `%`, y las filas del control de
        # viudas terminan en `\\*`: contar solo `\\` perdia 4 por
        # tabla (la mas larga daba 36 cuando en realidad tiene 40).
        filas = [ln for ln in cuerpo.splitlines()
                 if ln.strip().rstrip("%").rstrip("*").endswith("\\\\")]
        peor = max(peor, len(filas))
    if peor == 0:
        print("  FAIL: se contaron 0 filas; el test no esta midiendo nada")
        return False
    if peor > tope:
        print(f"  FAIL: hay una tabla de {peor} filas, tope {tope}")
        ok = False
    if "Se listan" not in tex:
        print("  FAIL: falta la nota que dice cuantas filas se listan de "
              "cuantas")
        ok = False
    if ok:
        print(f"  OK: {project.num_nodes} nodos, tabla mas larga {peor} filas "
              f"(tope {tope}) + nota de muestreo")
    return ok


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
        test_longtable_cuenta_columnas_de_parrafo(),
        test_tablas_con_unidades(),
        test_contorno_rotulo_con_simbolo_y_unidad(),
        test_figuras_lod_en_malla_densa(),
        test_pipeline_map_es_pil(),
        test_tex_sin_indice_ni_apaisado(),
        test_tex_portada_en_una_hoja(),
        test_tex_contornos_en_grilla(),
        test_tex_sin_duplicar_D_ni_isoparametrico(),
        test_max_matrix_cols_cubre_la_matriz_mas_ancha(),
        test_recuperacion_epsilon_reproduce_sigma(),
        test_equilibrio_cuenta_las_cargas_superficiales(),
        test_condicionamiento_se_mide_sobre_K_ff(),
        test_matrices_sin_ceros_falsos(),
        test_maqueta_sin_desbordes_ni_hojas_flojas(),
        test_vector_compacto_entra_en_el_renglon(),
        test_flechas_de_carga_entran_en_la_figura(),
        test_tablas_topeadas_en_malla_grande(),
        test_notas_mandan_al_lugar_correcto(),
        test_compila_directo_q4(),
        test_hub_tiene_post_proceso(),
        test_hub_numeracion_modulos(),
        test_hub_rango_metricas_calidad(),
        test_hub_solver_lu_sin_internals(),
        test_hub_no_tiene_mohr(),
        test_hub_bcs_solo_eliminacion(),
        test_hub_toc_clickeable(),
        test_hub_no_tiene_bibliografia(),
        test_memoria_minima_q4(),
        test_memoria_minima_q9(),
        test_nada_se_sale_de_la_hoja(),
        test_error_pdflatex_faltante(),
    ]
    n_pass = sum(1 for r in results if r)
    n_total = len(results)
    print("=" * 60)
    print(f"Resultado: {n_pass}/{n_total} OK")
    sys.exit(0 if n_pass == n_total else 1)
