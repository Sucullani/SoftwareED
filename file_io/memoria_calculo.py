"""
Memoria de Calculo: generador de PDF educativo paso-a-paso del analisis FEM.

Compila un documento LaTeX (via pylatex + pdflatex) que muestra el
procedimiento completo del analisis: definicion del problema, discretizacion,
showcase elemental detallado, ensamblaje global, aplicacion de BCs,
solucion, post-proceso y calidad de malla.

Reemplaza el reporte tabular previo (`pdf_report.py`) — output ahora es
publication-quality con matrices `\\begin{bmatrix}` reales, narrativa
pedagogica en espanol y diagramas matplotlib embebidos.

Roadmap incremental: este modulo crece por etapas. Paso 1 implementa
portada + capitulos 1, 2 y 6. Pasos 2-6 agregan showcase, figuras,
apendices, soporte Q9 y UX final.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any, Callable, Optional

import numpy as np
from pylatex import NoEscape, Package

from config.settings import (
    APP_NAME, APP_VERSION,
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    ELEMENT_Q4, ELEMENT_Q9,
    DECIMALS_LENGTH, DECIMALS_FORCE, DECIMALS_STRESS, DECIMALS_DISPLACEMENT,
    NUMERICAL_TOLERANCE,
    fmt,
)

# Tolerancia para considerar "no nulo" en estadisticas de K (nnz, banda).
# Usa la misma tolerancia global que el resto del pipeline FEM.
NUMERICAL_TOLERANCE_K = max(NUMERICAL_TOLERANCE, 1e-9)
from education.components.theory_builder import TheoryDoc


class MemoriaCalculoError(RuntimeError):
    """Error elevado por el generador con un mensaje accionable para el usuario."""


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------

def generate_memoria_calculo(
    project,
    solution: dict,
    element_stresses: Optional[dict],
    nodal_stresses: Optional[dict],
    filepath: str,
    *,
    mesh_diagram=None,
    contour_figures: Optional[dict] = None,
    scope: str = "showcase",
    progress_callback: Optional[Callable[[str, float], None]] = None,
    keep_tex: bool = False,
) -> str:
    """Genera el PDF educativo y retorna la ruta del archivo creado.

    Parametros
    ----------
    project : ProjectModel ya resuelto (`project.is_solved == True`).
    solution : dict retornado por `fem.solver.solve_system`.
    element_stresses, nodal_stresses : retornados por
        `fem.stress.compute_all_stresses`. Pueden ser None en versiones
        tempranas del roadmap (caps. de post-proceso degradan elegantemente).
    filepath : ruta destino, debe terminar en `.pdf`.
    mesh_diagram, contour_figures : figuras matplotlib (Paso 3 del roadmap).
    scope : 'showcase' (default) muestra un elemento detallado + resumen
        del resto. Otros valores se reservan para iteraciones futuras.
    progress_callback : callable(stage_label, pct_0_a_1) opcional.
    keep_tex : si True, conserva el `.tex` intermedio para depuracion.
    """
    if not filepath.lower().endswith(".pdf"):
        filepath = filepath + ".pdf"

    filepath_no_ext = filepath[:-4]

    def _progress(stage: str, pct: float) -> None:
        if progress_callback is not None:
            try:
                progress_callback(stage, pct)
            except Exception:
                pass

    _progress("Inicializando documento", 0.05)
    memoria = MemoriaCalculo(project, solution, element_stresses, nodal_stresses,
                             mesh_diagram=mesh_diagram,
                             contour_figures=contour_figures,
                             scope=scope)

    _progress("Construyendo capitulos", 0.15)
    memoria.build()

    _progress("Compilando con pdflatex", 0.55)
    try:
        memoria.compile(filepath_no_ext, keep_tex=keep_tex)
    except FileNotFoundError as e:
        raise MemoriaCalculoError(
            "No se encontro pdflatex en el PATH. "
            "Instalá MiKTeX (https://miktex.org) o TeX Live y reiniciá EduFEM. "
            f"Detalle: {e}"
        ) from e
    except Exception as e:
        # Conservar el .tex para depuracion
        fallback_tex = filepath_no_ext + ".tex"
        try:
            with open(fallback_tex, "w", encoding="utf-8") as f:
                f.write(memoria.tex_source())
        except Exception:
            pass
        raise MemoriaCalculoError(
            f"pdflatex fallo al compilar la Memoria de Calculo. "
            f"Se conservó el .tex en:\n  {fallback_tex}\n"
            f"para depuracion. Detalle: {e}"
        ) from e

    _progress("Listo", 1.0)
    return filepath


# ---------------------------------------------------------------------------
# Clase generadora
# ---------------------------------------------------------------------------

class MemoriaCalculo:
    """Construye el documento LaTeX paso-a-paso. Compone TheoryDoc."""

    TITLE = "Memoria de Cálculo"
    SUBTITLE_TEMPLATE = "Análisis MEF 2D — Proyecto: {name}"

    def __init__(self, project, solution, element_stresses, nodal_stresses,
                 *, mesh_diagram=None, contour_figures=None, scope: str = "showcase"):
        self._project = project
        self._solution = solution
        self._element_stresses = element_stresses or {}
        self._nodal_stresses = nodal_stresses or {}
        self._mesh_diagram = mesh_diagram
        self._contour_figures = dict(contour_figures) if contour_figures else {}
        self._scope = scope
        # Directorio temporal para PNGs (cleanup en compile()).
        # Se crea lazy via _ensure_tmpdir() para que tex_source() no lo necesite.
        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None

        title = TheoryDoc.escape(self.TITLE)
        subtitle = TheoryDoc.escape(
            self.SUBTITLE_TEMPLATE.format(name=project.project_name)
        )
        self._td = TheoryDoc(title=title, subtitle=subtitle)
        self._configure_preamble()

    def _configure_preamble(self) -> None:
        td = self._td
        proj = self._project
        # Idioma espanol: Capitulo en lugar de Chapter, etc.
        td.package("babel", options="spanish")
        td.package("longtable")
        td.package("caption")
        td.package("fancyhdr")
        # bmatrix limita a 10 columnas por defecto. Q9 tiene B (3x18) y
        # k_e (18x18); subimos el limite para que entren.
        td.raw(r"\setcounter{MaxMatrixCols}{20}")
        # Encabezado y pie de pagina coherentes en todas las paginas.
        td.raw(r"\pagestyle{fancy}")
        td.raw(r"\fancyhf{}")
        proj_name_safe = TheoryDoc.escape(proj.project_name)
        td.raw(rf"\fancyhead[L]{{\small Memoria de Cálculo}}")
        td.raw(rf"\fancyhead[R]{{\small {proj_name_safe}}}")
        td.raw(r"\fancyfoot[C]{\small \thepage}")
        td.raw(r"\renewcommand{\headrulewidth}{0.4pt}")
        # Espacio entre parrafos para mejorar lectura.
        td.raw(r"\setlength{\parskip}{4pt plus 1pt minus 1pt}")
        td.raw(r"\setlength{\parindent}{0pt}")
        # Ya inserta automaticamente float + graphicx cuando se llama figure()

    def build(self) -> None:
        """Llena el documento siguiendo la jerarquia MEF estandar:

        0. Introduccion conceptual + hoja de ruta del metodo (sin numerar)
        1. Definicion del problema (hipotesis, tipo de elemento)
        2. Discretizacion del modelo (geometria, materiales, BCs, cargas)
        3. Calidad de la malla (verificar antes de pesar el solve)
        4. Formulacion elemental (showcase: N -> J -> B -> D -> kₑ)
        5. Ensamblaje del sistema global (K, F)
        6. Aplicacion de condiciones de contorno (reduccion del sistema)
        7. Solucion del sistema (factorizacion + back-substitution)
        8. Post-proceso (Gauss -> nodos -> promediado -> principales -> VM)

        Apendices: A) kₑ de elementos restantes  B) datos completos  C) glosario.

        El orden replica el pipeline natural que sigue un ingeniero al
        ejecutar un analisis MEF, separando claramente las fases
        pre-proceso (Caps 1-3), proceso (Caps 4-7) y post-proceso (Cap 8).
        """
        self._build_cover()
        self._td.toc()
        # Cap 0: introduccion (no numerada, aparece como `Resumen' en TOC)
        self._build_chapter0_pipeline()
        # Cap 1-2: pre-proceso
        self._build_resumen_visual()
        self._build_chapter1_problema()
        self._build_chapter2_discretizacion()
        # Cap 3: calidad de malla -- antes del Cap 4 (showcase) porque
        # si la malla es deficiente, los k_e estaran condicionados.
        self._build_chapter3_calidad()
        # Cap 4-7: proceso
        showcase_id = self._select_showcase_element()
        if showcase_id is not None:
            self._build_chapter4_showcase(showcase_id)
        self._build_chapter5_ensamblaje()
        self._build_chapter6_bcs()
        self._build_chapter7_solucion()
        # Cap 8: post-proceso
        self._build_chapter8_postproceso(showcase_id)
        # Apendices
        self._td.raw(r"\appendix")
        self._build_appendix_a_kes(showcase_id)
        self._build_appendix_b_datos()
        self._build_appendix_c_glosario()
        self._build_pie()

    def compile(self, filepath_no_ext: str, *, keep_tex: bool = False) -> None:
        try:
            self._td.compile_to(filepath_no_ext, keep_tex=keep_tex)
        finally:
            # Cleanup de PNGs temporales (se hace despues de pdflatex —
            # pdflatex requiere los archivos presentes durante la compilacion).
            self._cleanup_tmpdir()

    def tex_source(self) -> str:
        """Retorna el codigo .tex generado (para depuracion / inspeccion)."""
        return self._td.document().dumps()

    def _ensure_tmpdir(self) -> str:
        """Inicializa (lazy) el directorio temporal para PNGs."""
        if self._tmpdir is None:
            self._tmpdir = tempfile.TemporaryDirectory(prefix="edufem_memoria_")
        return self._tmpdir.name

    def _cleanup_tmpdir(self) -> None:
        if self._tmpdir is not None:
            try:
                self._tmpdir.cleanup()
            except Exception:
                pass
            self._tmpdir = None

    def _save_figure(self, fig, name: str) -> Optional[str]:
        """Guarda `fig` en el tmpdir y retorna la ruta absoluta. None si falla.

        Cierra la figura con plt.close(fig) en un bloque finally para garantizar
        que matplotlib libere la memoria independientemente de excepciones. Sin
        este close, cada figura acumula ~250-500 KB en el registro interno de
        matplotlib y la exportacion de PDFs largos puede superar 500 MB de RAM.
        """
        if fig is None:
            return None
        try:
            tmpdir = self._ensure_tmpdir()
            path = os.path.join(tmpdir, f"{name}.png")
            fig.savefig(path, dpi=150, bbox_inches="tight",
                        facecolor="white")
            return path
        except Exception:
            return None
        finally:
            try:
                import matplotlib.pyplot as _plt
                _plt.close(fig)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Portada y secciones
    # ------------------------------------------------------------------

    def _build_cover(self) -> None:
        td = self._td
        proj = self._project
        # Hash determinista del modelo (reproducibilidad)
        try:
            payload = json.dumps(proj.to_dict(), sort_keys=True, default=str,
                                 ensure_ascii=False)
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
        except Exception:
            digest = "—"

        info = [
            ("Proyecto", TheoryDoc.escape(proj.project_name)),
            ("Fecha de generación", datetime.now().strftime("%d/%m/%Y %H:%M")),
            ("Tipo de análisis", TheoryDoc.escape(proj.analysis_type)),
            ("Tipo de elemento", TheoryDoc.escape(proj.element_type)),
            ("Sistema de unidades", TheoryDoc.escape(proj.unit_system)),
            ("Nodos", str(proj.num_nodes)),
            ("Elementos", str(proj.num_elements)),
            ("Grados de libertad", str(proj.total_dof)),
            ("Hash del modelo", rf"\texttt{{{digest}}}"),
            ("Generado por", f"{TheoryDoc.escape(APP_NAME)} v{APP_VERSION}"),
        ]
        td.values(info)
        td.raw(r"\vspace{1em}")
        td.para(
            r"\emph{Este documento describe paso a paso el análisis "
            r"realizado por el método de los elementos finitos. "
            r"Cada capítulo combina el planteo teórico con los valores "
            r"numéricos del problema concreto, replicando el procedimiento "
            r"que un ingeniero debería ejecutar a mano para validar la solución.}"
        )
        td.raw(r"\newpage")

    # ----- Capitulo 0: Hoja de ruta del MEF -----

    def _build_chapter0_pipeline(self) -> None:
        """Introduccion conceptual al MEF + diagrama de pipeline.

        Antes de mostrar numeros, el documento da una vista panoramica
        de lo que el metodo intenta resolver y como se compone. El
        alumno arranca con un mapa mental del pipeline.
        """
        td = self._td
        # Capitulo introductorio sin numerar -- no compite por el numero 1
        # con `Definicion del problema'. Se agrega manualmente al TOC.
        td.raw(r"\section*{¿Qué resuelve el MEF y cómo?}")
        td.raw(
            r"\addcontentsline{toc}{section}{¿Qué resuelve el MEF y cómo?}"
        )
        td.para(
            r"El \textbf{MEF} discretiza un problema elástico continuo en "
            r"$N$ elementos finitos: las incógnitas pasan de un campo "
            r"$\mathbf{u}(x,y)$ infinito-dimensional a un vector "
            r"$\mathbf{u}$ de $2\cdot N_{nodos}$ entradas, y el equilibrio "
            r"se reduce al sistema algebraico $\mathbf{K}\,\mathbf{u} = "
            r"\mathbf{F}$. Esta memoria documenta el análisis específico "
            r"de este proyecto siguiendo la jerarquía estándar del método: "
            r"\textbf{pre-proceso} (Caps.\ 1--3), \textbf{proceso} "
            r"(Caps.\ 4--7) y \textbf{post-proceso} (Cap.\ 8). El diagrama "
            r"siguiente resume el pipeline:"
        )
        try:
            from file_io.figure_export import render_fem_pipeline
            fig = render_fem_pipeline()
            path = self._save_figure(fig, "fem_pipeline")
            if path is not None:
                td.figure(
                    path,
                    caption=("Hoja de ruta del MEF: cada nodo del pipeline "
                             "está coloreado por la fase del proyecto donde "
                             "se ejecuta (azul = pre-proceso, naranja = "
                             "proceso, verde = post-proceso)."),
                    label="fig:fem_pipeline",
                    width=r"0.98\textwidth",
                )
        except Exception:
            pass
        td.educational_teaser(
            r"La derivación completa del MEF (forma débil, principio de "
            r"trabajos virtuales, espacio de aproximación) vive en el Hub.",
            cross_ref=r"Introducción + M0..M9",
            phase="info",
        )
        td.raw(r"\newpage")

    # ----- Resumen visual (diagrama del modelo) -----

    def _build_resumen_visual(self) -> None:
        """Inserta el diagrama del modelo como `Resumen visual'.
        Si no se pasó un mesh_diagram via constructor, lo genera."""
        td = self._td
        fig = self._mesh_diagram
        if fig is None:
            try:
                from file_io.figure_export import render_mesh_diagram
                fig = render_mesh_diagram(self._project)
            except Exception:
                fig = None
        if fig is None:
            return
        td.raw(r"\section*{Resumen visual del modelo}")
        path = self._save_figure(fig, "mesh_diagram")
        if path is not None:
            td.figure(path,
                      caption="Discretización del modelo: nodos, elementos, "
                              "restricciones y cargas aplicadas.",
                      label="fig:mesh", width=r"0.95\textwidth")
        td.raw(r"\newpage")

    # ----- Capitulo 1: Definicion del problema -----

    def _build_chapter1_problema(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Definición del problema")

        td.subsection_numbered("Hipótesis del análisis")
        td.para(self._narrativa_caso_plano())
        td.educational_teaser(
            r"Tensión plana = placas delgadas en su plano; "
            r"deformación plana = sólidos prismáticos largos. "
            r"Elegir mal no rompe el cálculo, da otro problema.",
            cross_ref=r"M3 §Tensión plana / §Deformación plana",
            phase="pre",
        )
        self._matriz_D_teorica()
        self._matriz_D_numerica_si_unico_material()

        td.subsection_numbered("Tipo de elemento finito")
        if proj.element_type == ELEMENT_Q4:
            td.para(
                r"Se utiliza el elemento isoparamétrico cuadrilátero de "
                r"\textbf{4 nodos} (Q4). Las funciones de forma en coordenadas "
                r"naturales $(\xi, \eta) \in [-1, 1]^2$ son bilineales:"
            )
            td.equation(
                r"N_i(\xi, \eta) = \tfrac{1}{4}(1 + \xi_i \xi)(1 + \eta_i \eta), "
                r"\quad i = 1, \dots, 4"
            )
            td.para(
                r"con $(\xi_i, \eta_i)$ las coordenadas naturales del nodo "
                r"$i$ del elemento maestro. La integración numérica usa "
                r"cuadratura de Gauss $2\times 2$ (4 puntos)."
            )
        else:
            td.para(
                r"Se utiliza el elemento isoparamétrico cuadrilátero de "
                r"\textbf{9 nodos} (Q9, también llamado Lagrangiano). "
                r"Las funciones de forma en coordenadas naturales "
                r"$(\xi, \eta) \in [-1, 1]^2$ son productos de polinomios de "
                r"Lagrange cuadráticos:"
            )
            td.equation(
                r"N_i(\xi, \eta) = L_a(\xi)\, L_b(\eta), "
                r"\quad i = 1, \dots, 9"
            )
            td.para(
                r"donde $L_a$ y $L_b$ son los polinomios de Lagrange "
                r"cuadráticos asociados al nodo. La integración numérica usa "
                r"cuadratura de Gauss $3\times 3$ (9 puntos)."
            )

    def _narrativa_caso_plano(self) -> str:
        proj = self._project
        if proj.analysis_type == ANALYSIS_PLANE_STRESS:
            return (
                r"El problema se resuelve bajo la hipótesis de "
                r"\textbf{tensión plana} ($\sigma_z = \tau_{xz} = \tau_{yz} = 0$), "
                r"válida para cuerpos delgados cargados en su plano medio. "
                r"La deformación fuera del plano $\varepsilon_z$ no es nula "
                r"pero se determina a posteriori a partir del campo plano."
            )
        else:
            return (
                r"El problema se resuelve bajo la hipótesis de "
                r"\textbf{deformación plana} ($\varepsilon_z = \gamma_{xz} = \gamma_{yz} = 0$), "
                r"válida para cuerpos prismáticos largos cuya sección "
                r"transversal y cargas no varían a lo largo del eje. "
                r"La tensión normal $\sigma_z$ no es nula y se calcula "
                r"como $\sigma_z = \nu(\sigma_x + \sigma_y)$."
            )

    def _matriz_D_teorica(self) -> None:
        td = self._td
        if self._project.analysis_type == ANALYSIS_PLANE_STRESS:
            td.equation(
                r"\mathbf{D} = \frac{E}{1 - \nu^2}\begin{bmatrix}"
                r"1 & \nu & 0 \\ "
                r"\nu & 1 & 0 \\ "
                r"0 & 0 & \tfrac{1 - \nu}{2}"
                r"\end{bmatrix}"
            )
        else:
            td.equation(
                r"\mathbf{D} = \frac{E}{(1+\nu)(1-2\nu)}\begin{bmatrix}"
                r"1-\nu & \nu & 0 \\ "
                r"\nu & 1-\nu & 0 \\ "
                r"0 & 0 & \tfrac{1 - 2\nu}{2}"
                r"\end{bmatrix}"
            )

    def _matriz_D_numerica_si_unico_material(self) -> None:
        """Si el modelo tiene un solo material referenciado por elementos,
        muestra la matriz D evaluada con sus valores. Si hay varios, deja
        nota indicando que cada elemento usa su propia D (cap. 3 muestra
        la del elemento estrella)."""
        td = self._td
        proj = self._project
        materials_used = {
            elem.material_name for elem in proj.elements.values()
        }
        if len(materials_used) == 1 and len(proj.materials) > 0:
            mat_name = next(iter(materials_used))
            mat = proj.materials.get(mat_name)
            if mat is None:
                return
            from fem.constitutive import constitutive_matrix
            try:
                D = constitutive_matrix(mat.E, mat.nu, proj.analysis_type)
            except Exception:
                return
            td.para(
                rf"Para el material \textbf{{{TheoryDoc.escape(mat_name)}}} "
                rf"con $E = {mat.E:g}$ y $\nu = {mat.nu:g}$, "
                rf"la matriz constitutiva evaluada es:"
            )
            td.matrix(D, name=r"\mathbf{D}", fmt="{:+.4g}")
        else:
            td.para(
                r"\emph{El modelo utiliza más de un material; cada elemento "
                r"emplea su propia matriz $\mathbf{D}$. El Capítulo 3 "
                r"(showcase elemental) desarrollará la matriz del material "
                r"asignado al elemento estrella.}"
            )

    # ----- Capitulo 2: Discretizacion -----

    def _build_chapter2_discretizacion(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Discretización del modelo")
        td.para(
            r"La discretización congela todas las decisiones del "
            r"pre-proceso: qué material(es) componen el cuerpo, dónde "
            r"están los nodos, cómo se conectan en elementos, qué "
            r"cargas externas actúan y dónde se restringe el "
            r"movimiento. A partir de aquí, el resto de la memoria "
            r"opera sobre el modelo discreto fijado en este capítulo."
        )

        td.subsection_numbered("Materiales")
        self._tabla_materiales()

        td.subsection_numbered("Nodos")
        self._tabla_nodos()

        td.subsection_numbered("Conectividad de elementos")
        self._tabla_elementos()

        td.subsection_numbered("Cargas nodales")
        self._tabla_cargas_nodales()

        td.subsection_numbered("Cargas superficiales")
        self._tabla_cargas_superficiales()

        td.subsection_numbered("Condiciones de contorno")
        self._tabla_restricciones()

    def _tabla_materiales(self) -> None:
        proj = self._project
        if not proj.materials:
            self._td.para(r"\emph{Sin materiales definidos.}")
            return
        # Solo mostramos los materiales referenciados por al menos un elemento
        usados = {e.material_name for e in proj.elements.values()}
        rows: list[list[str]] = []
        for name, mat in proj.materials.items():
            if usados and name not in usados:
                continue
            density = getattr(mat, "density", None)
            rows.append([
                TheoryDoc.escape(name),
                f"{mat.E:g}",
                f"{mat.nu:g}",
                f"{density:g}" if density is not None else "—",
            ])
        if not rows:
            self._td.para(r"\emph{Ningún material está referenciado por elementos.}")
            return
        self._longtable(
            headers=["Material", r"$E$", r"$\nu$", r"$\rho$"],
            rows=rows,
            col_align="lrrr",
        )

    def _tabla_nodos(self) -> None:
        proj = self._project
        if not proj.nodes:
            self._td.para(r"\emph{Sin nodos definidos.}")
            return
        rows = []
        for nid in sorted(proj.nodes.keys()):
            n = proj.nodes[nid]
            rows.append([str(nid), fmt(n.x, "length"), fmt(n.y, "length")])
        self._longtable(
            headers=["ID", r"$X$", r"$Y$"],
            rows=rows,
            col_align="rrr",
        )

    def _tabla_elementos(self) -> None:
        proj = self._project
        if not proj.elements:
            self._td.para(r"\emph{Sin elementos definidos.}")
            return
        # Mostramos N1..N4 (vertices macro) + extras Q9 si aplica
        is_q9 = proj.element_type == ELEMENT_Q9
        if is_q9:
            headers = ["ID", "N1", "N2", "N3", "N4",
                       "N5", "N6", "N7", "N8", "N9",
                       "Espesor", "Material"]
            col_align = "r" * 10 + "rl"
            n_cols = 9
        else:
            headers = ["ID", "N1", "N2", "N3", "N4", "Espesor", "Material"]
            col_align = "rrrrrrl"
            n_cols = 4
        rows = []
        for eid in sorted(proj.elements.keys()):
            elem = proj.elements[eid]
            nids = list(elem.node_ids)
            while len(nids) < n_cols:
                nids.append("—")
            row = [str(eid)] + [str(n) for n in nids[:n_cols]]
            row.append(fmt(elem.thickness, "length"))
            row.append(TheoryDoc.escape(elem.material_name))
            rows.append(row)
        self._longtable(headers=headers, rows=rows, col_align=col_align)

    def _tabla_cargas_nodales(self) -> None:
        proj = self._project
        if not proj.nodal_loads:
            self._td.para(r"\emph{Sin cargas nodales definidas.}")
            return
        rows = []
        for nid in sorted(proj.nodal_loads.keys()):
            ld = proj.nodal_loads[nid]
            rows.append([str(nid), fmt(ld.fx, "force"), fmt(ld.fy, "force")])
        self._longtable(
            headers=["Nodo", r"$F_x$", r"$F_y$"],
            rows=rows,
            col_align="rrr",
        )

    def _tabla_cargas_superficiales(self) -> None:
        proj = self._project
        if not getattr(proj, "surface_loads", None):
            self._td.para(r"\emph{Sin cargas superficiales definidas.}")
            return
        rows = []
        for idx, sl in enumerate(proj.surface_loads, start=1):
            angle = getattr(sl, "angle", 0.0)
            rows.append([
                str(idx),
                str(sl.node_start), str(sl.node_end),
                fmt(sl.q_start, "force"), fmt(sl.q_end, "force"),
                fmt(angle, "angle"),
            ])
        self._longtable(
            headers=[r"\#", "N inicio", "N fin",
                     r"$q_{inicio}$", r"$q_{fin}$", r"$\theta$ (°)"],
            rows=rows,
            col_align="rrrrrr",
        )

    def _tabla_restricciones(self) -> None:
        proj = self._project
        if not proj.boundary_conditions:
            self._td.para(r"\emph{Sin restricciones definidas. El sistema "
                          r"sería singular sin BCs.}")
            return
        rows = []
        for nid in sorted(proj.boundary_conditions.keys()):
            bc = proj.boundary_conditions[nid]
            rows.append([
                str(nid),
                "Sí" if bc.restrain_x else "No",
                "Sí" if bc.restrain_y else "No",
            ])
        self._longtable(
            headers=["Nodo", "Restringe X", "Restringe Y"],
            rows=rows,
            col_align="rcc",
        )

    # ----- Capitulo 3: Showcase elemental -----

    def _select_showcase_element(self) -> Optional[int]:
        """Elige el elemento estrella: maxima energia de deformacion
        U_e = 0.5 * u_e^T * k_e * u_e. Fallback: argmax ||k_e||_F.

        Retorna `None` si no hay elementos o no hay element_data.
        """
        proj = self._project
        sol = self._solution
        if not proj.elements:
            return None
        elem_data = sol.get("element_data") if sol else None
        if not elem_data:
            return None
        u = sol.get("u")
        best_id = None
        best_score = -1.0
        if u is not None:
            for eid, data in elem_data.items():
                ke = data.get("ke")
                dof_idx = data.get("dof_indices")
                if ke is None or dof_idx is None:
                    continue
                u_e = np.asarray(u)[list(dof_idx)]
                try:
                    energy = 0.5 * float(u_e @ ke @ u_e)
                except Exception:
                    continue
                if energy > best_score:
                    best_score = energy
                    best_id = eid
        if best_id is None:
            # Fallback: norma Frobenius de k_e
            for eid, data in elem_data.items():
                ke = data.get("ke")
                if ke is None:
                    continue
                try:
                    score = float(np.linalg.norm(ke, "fro"))
                except Exception:
                    continue
                if score > best_score:
                    best_score = score
                    best_id = eid
        return best_id

    def _build_chapter4_showcase(self, elem_id: int) -> None:
        td = self._td
        proj = self._project
        elem = proj.elements.get(elem_id)
        if elem is None:
            return
        sol = self._solution
        elem_data = sol.get("element_data", {}).get(elem_id)
        if elem_data is None:
            return

        td.section_numbered(rf"Formulación elemental — Elemento {elem_id}")
        td.para(
            rf"Este capítulo desarrolla \emph{{paso a paso}} el cálculo "
            rf"de la matriz de rigidez del elemento $E_{{{elem_id}}}$, "
            rf"seleccionado como `elemento estrella' por ser el de mayor "
            rf"energía de deformación. El procedimiento aplica idénticamente "
            rf"al resto de los elementos (sus matrices están en el Apéndice "
            rf"A). El orden sigue la jerarquía estándar de la formulación "
            rf"isoparamétrica: geometría $\to$ $\mathbf{{N}}$ $\to$ "
            rf"$\mathbf{{J}}$ $\to$ $\mathbf{{B}}$ $\to$ $\mathbf{{D}}$ "
            rf"$\to$ integración. Las derivaciones generales viven en "
            rf"\emph{{Teoría MEF: M1 Mapeo, M2 Jacobiano, M3 D, M4 B, M5 "
            rf"Rigidez+Gauss}}; este capítulo aplica esa cadena a los "
            rf"valores del proyecto."
        )

        # 4.1 Geometria
        td.subsection_numbered("Geometría y conectividad del elemento")
        node_coords = np.asarray(elem_data["node_coords"])
        n_nodes = node_coords.shape[0]
        rows = []
        for i, nid in enumerate(elem.node_ids[:n_nodes]):
            x, y = node_coords[i]
            rows.append([f"$N_{{{i+1}}}$", str(nid),
                         fmt(x, "length"), fmt(y, "length")])
        self._longtable(
            headers=["Nodo local", "Nodo global", r"$X$", r"$Y$"],
            rows=rows,
            col_align="ccrr",
        )
        td.values([
            ("Tipo de elemento", TheoryDoc.escape(proj.element_type)),
            ("Cantidad de nodos", str(n_nodes)),
            ("Espesor $t$", fmt(elem.thickness, "length")),
            ("Material", TheoryDoc.escape(elem.material_name)),
        ])

        # 4.2 Funciones de forma N en puntos de Gauss
        gauss_data = elem_data.get("gauss_data", [])
        td.subsection_numbered(
            r"Funciones de forma $N_i(\xi, \eta)$ en los puntos de Gauss"
        )
        td.para(
            r"Las funciones de forma $N_i$ interpolan tanto la geometría "
            r"como el campo de desplazamientos (formulación "
            r"\emph{isoparamétrica}): "
            r"$\mathbf{x}(\xi, \eta) = \sum_i N_i\,\mathbf{x}_i$ y "
            r"$\mathbf{u}(\xi, \eta) = \sum_i N_i\,\mathbf{u}_i$. Evaluadas "
            r"en cada punto de Gauss, definen el muestreo del elemento "
            r"que la cuadratura usará para integrar."
        )
        if gauss_data:
            self._tabla_N_en_gauss(gauss_data, n_nodes, proj.element_type)
        else:
            td.para(r"\emph{Datos de Gauss no disponibles.}")

        # 4.3 Jacobiano J y det J por punto Gauss
        gauss_to_show = self._select_gauss_to_display(gauss_data, n_nodes)
        td.subsection_numbered(
            r"Jacobiano $\mathbf{J}(\xi, \eta)$ y $\det \mathbf{J}$"
        )
        td.para(
            r"El Jacobiano relaciona los diferenciales en coordenadas "
            r"naturales y físicas: $d\mathbf{x} = \mathbf{J}\, d\boldsymbol{\xi}$, "
            r"con $\mathbf{J}_{ij} = \partial x_i / \partial \xi_j$. "
            r"Su determinante actúa como factor de escala del área en la "
            r"integración de Gauss y debe ser $> 0$ en todo el elemento "
            r"para que el mapeo natural→físico sea biyectivo."
        )
        if len(gauss_to_show) < len(gauss_data):
            td.para(
                rf"\emph{{Por compacidad se muestran {len(gauss_to_show)} "
                rf"de los {len(gauss_data)} puntos de Gauss del elemento; "
                rf"el resto sigue el mismo procedimiento.}}"
            )
        for gp in gauss_to_show:
            self._mostrar_jacobiano_pg(gp)

        # 4.4 Matriz B(xi, eta)
        td.subsection_numbered(
            r"Matriz de deformación $\mathbf{B}(\xi, \eta)$"
        )
        td.para(
            r"La matriz $\mathbf{B}$ contiene las derivadas de las "
            r"funciones de forma respecto de $x, y$ (obtenidas vía "
            r"$\partial N / \partial \mathbf{x} = \mathbf{J}^{-1}\,"
            r"\partial N / \partial \boldsymbol{\xi}$) y relaciona los "
            r"desplazamientos nodales con las deformaciones: "
            r"$\boldsymbol{\varepsilon} = \mathbf{B}\,\mathbf{u}_e$. "
            r"Es la pieza \emph{geométrica} del integrando."
        )
        for gp in gauss_to_show:
            self._mostrar_matriz_B_pg(gp)

        # 4.5 Matriz constitutiva D
        td.subsection_numbered(
            r"Matriz constitutiva $\mathbf{D}$ del material asignado"
        )
        material = proj.materials.get(elem.material_name)
        if material is not None:
            from fem.constitutive import constitutive_matrix
            D = constitutive_matrix(material.E, material.nu, proj.analysis_type)
            td.para(
                r"$\mathbf{D}$ es la pieza \emph{material} del integrando: "
                r"relaciona deformaciones con tensiones por la ley de Hooke "
                rf"generalizada. Para el material "
                rf"\textbf{{{TheoryDoc.escape(material.name)}}} "
                rf"con $E = {material.E:g}$ y $\nu = {material.nu:g}$, "
                rf"bajo {TheoryDoc.escape(proj.analysis_type).lower()}:"
            )
            td.matrix(D, name=r"\mathbf{D}", fmt="{:+.4g}")
        else:
            td.para(r"\emph{Material no encontrado en el modelo.}")

        # 4.6 Integrando simbolico (Q4 unicamente)
        td.subsection_numbered(
            r"Integrando simbólico $K_{ij}(\xi, \eta)$"
        )
        td.educational_box(
            r"Aquí se ve por qué \textbf{no} integramos la rigidez "
            r"elemental analíticamente: la expresión simbólica del "
            r"integrando $\mathbf{B}^T\mathbf{D}\,\mathbf{B}\,|\det \mathbf{J}|\,t$ "
            r"para una sola entrada $(i, j)$ del Q4 ya ocupa varias líneas. "
            r"Para Q9 cada entrada cubre páginas. Esa es la motivación "
            r"directa de la \emph{cuadratura de Gauss} —no es una "
            r"opción más eficiente, es la única vía práctica.",
            title=r"\textbf{¿Por qué cuadratura numérica y no analítica?}",
            phase="proc",
        )
        if proj.element_type == ELEMENT_Q4 and n_nodes == 4:
            self._integrando_simbolico_q4(elem, node_coords, material)
        else:
            td.para(
                r"\emph{La construcción simbólica del integrando completo "
                r"para Q9 (matrices $18\times 18$) excede la utilidad "
                r"didáctica del documento. Se muestra solo la sumatoria "
                r"numérica en la subsección siguiente.}"
            )
            td.equation(
                r"\mathbf{k}_e = \int_{-1}^{1}\!\int_{-1}^{1} "
                r"\mathbf{B}^T\mathbf{D}\,\mathbf{B}\, |\det \mathbf{J}|\, t\, "
                r"d\xi\, d\eta"
            )

        # 4.7 Cuadratura de Gauss -> ke
        td.subsection_numbered(
            r"Cuadratura de Gauss y matriz $\mathbf{k}_e$ resultante"
        )
        td.para(
            r"La integral se aproxima por cuadratura de Gauss-Legendre 2D. "
            r"Cada contribución elemental es "
            r"$w_p\,\mathbf{B}^T\mathbf{D}\,\mathbf{B}\,|\det\mathbf{J}|\,t$ "
            r"evaluada en el punto $\boldsymbol{\xi}_p$:"
        )
        td.equation(
            r"\mathbf{k}_e \approx \sum_p w_p\, \mathbf{B}_p^T\mathbf{D}\,"
            r"\mathbf{B}_p\,|\det\mathbf{J}_p|\,t"
        )
        ke = np.asarray(elem_data["ke"])
        # k_e completa con exponente factorizado: Q4 (8x8) cabe en portrait;
        # Q9 (18x18) requiere landscape + tiny.
        if ke.shape[0] <= 8:
            td.raw(r"{\scriptsize")
            td.matrix_factored(ke, name=r"\mathbf{k}_e", sig_digits=3)
            td.raw(r"}")
        else:
            td.package("pdflscape")
            td.raw(r"\begin{landscape}")
            td.raw(r"{\tiny")
            td.matrix_factored(ke, name=r"\mathbf{k}_e", sig_digits=2)
            td.raw(r"}")
            td.raw(r"\end{landscape}")
        td.values([
            (r"Energía de deformación $U_e = \tfrac{1}{2}\mathbf{u}_e^T\mathbf{k}_e\mathbf{u}_e$",
             self._energia_deformacion_str(elem_id, ke)),
            (r"$\|\mathbf{k}_e\|_F$",
             f"{float(np.linalg.norm(ke, 'fro')):.4g}"),
            ("Condición $\\kappa_2(\\mathbf{k}_e)$",
             self._cond_str(ke)),
        ])

    @staticmethod
    def _select_gauss_to_display(gauss_data: list, n_nodes: int) -> list:
        """Para Q4 (4 PG) muestra los 4. Para Q9 (9 PG) muestra solo
        3 representativos (esquina, centro, esquina opuesta) — el resto
        es analogo y la repeticion satura el documento."""
        if not gauss_data:
            return []
        if n_nodes <= 4:
            return list(gauss_data)
        # Q9: 3x3 = 9 PG. Indices 0 (esquina), 4 (centro), 8 (otra esquina).
        n = len(gauss_data)
        if n <= 4:
            return list(gauss_data)
        idxs = sorted({0, n // 2, n - 1})
        return [gauss_data[i] for i in idxs if i < n]

    def _tabla_N_en_gauss(self, gauss_data, n_nodes, element_type) -> None:
        """Evalua N_i en cada PG y muestra como tabla compacta."""
        from fem.shape_functions import get_shape_functions
        N_func, _ = get_shape_functions(element_type)
        headers = ["Punto", r"$\xi$", r"$\eta$", r"$w$"] + \
                  [rf"$N_{{{i+1}}}$" for i in range(n_nodes)]
        rows = []
        for gp in gauss_data:
            xi, eta = gp["xi"], gp["eta"]
            w = gp["weight"]
            N_vals = N_func(xi, eta)
            row = [
                f"PG{gp['index']+1}",
                f"{xi:+.4f}",
                f"{eta:+.4f}",
                f"{w:.4f}",
            ] + [f"{float(n):+.4f}" for n in N_vals]
            rows.append(row)
        col_align = "rrrr" + "r" * n_nodes
        self._longtable(headers=headers, rows=rows, col_align=col_align)

    def _mostrar_jacobiano_pg(self, gp: dict) -> None:
        td = self._td
        idx = gp["index"] + 1
        xi, eta = gp["xi"], gp["eta"]
        td.raw(rf"\paragraph{{PG{idx} — $(\xi,\eta) = ({xi:+.4f}, {eta:+.4f})$}}")
        J = np.asarray(gp["J"])
        det_J = float(gp["det_J"])
        td.matrix(J, name=rf"\mathbf{{J}}_{{PG{idx}}}", fmt="{:+.4g}")
        td.equation(rf"\det \mathbf{{J}}_{{PG{idx}}} = {det_J:+.4g}")

    def _mostrar_matriz_B_pg(self, gp: dict) -> None:
        td = self._td
        idx = gp["index"] + 1
        B = np.asarray(gp["B"])
        # B Q4: 3x8 — entra. B Q9: 3x18 — usar scriptsize.
        if B.shape[1] <= 8:
            td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}", fmt="{:+.4g}")
        else:
            td.raw(rf"\paragraph{{PG{idx}}}")
            td.raw(r"{\scriptsize")
            td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}", fmt="{:+.3g}")
            td.raw(r"}")

    def _integrando_simbolico_q4(self, elem, node_coords, material) -> None:
        """Muestra la entrada (1, 1) del integrando K(xi, eta) simbolico
        de Bᵀ D B |det J| t. Para entradas mas alla, el lector puede
        construir analogamente."""
        td = self._td
        if material is None:
            td.para(r"\emph{Material no disponible — se omite el simbólico.}")
            return
        try:
            from education.mod05_stiffness import SymbolicIntegrandQ4
            import sympy as sp
        except Exception as e:
            td.para(rf"\emph{{No se pudo cargar la capa simbólica: {e}}}")
            return
        try:
            sim = SymbolicIntegrandQ4(
                E=material.E, nu=material.nu, t=elem.thickness,
                coords=[[float(x), float(y)] for x, y in node_coords[:4]],
            )
            expr = sim.integrand_entry(0, 0, self._project.analysis_type)
            latex_expr = sp.latex(expr)
            td.para(
                r"La sumatoria de Gauss aproxima la integral exacta:"
            )
            td.equation(
                r"\mathbf{k}_e = \int_{-1}^{1}\!\int_{-1}^{1} "
                r"\mathbf{B}^T(\xi,\eta)\,\mathbf{D}\,\mathbf{B}(\xi,\eta)\,"
                r"|\det\mathbf{J}(\xi,\eta)|\,t\, d\xi\, d\eta"
            )
            td.para(
                r"A modo ilustrativo, la entrada $(1, 1)$ del integrando "
                r"$\mathbf{B}^T\mathbf{D}\,\mathbf{B}|\det\mathbf{J}|\,t$ "
                r"evaluada simbólicamente en $(\xi, \eta)$ es:"
            )
            # La expresion puede ser muy larga -- usar \scriptsize
            td.raw(r"{\scriptsize")
            td.equation(rf"K_{{11}}(\xi, \eta) = {latex_expr}")
            td.raw(r"}")
            td.para(
                r"\emph{Nota: el integrando exacto de las 64 entradas de "
                r"$\mathbf{k}_e$ se construye análogamente. Por compacidad "
                r"se muestra solo $K_{11}$.}"
            )
        except Exception as e:
            td.para(
                rf"\emph{{No se pudo construir el integrando simbólico: {e}. "
                rf"Se procede con la cuadratura numérica.}}"
            )

    def _energia_deformacion_str(self, elem_id, ke: np.ndarray) -> str:
        sol = self._solution
        u = sol.get("u")
        elem_data = sol.get("element_data", {}).get(elem_id, {})
        dof_idx = elem_data.get("dof_indices")
        if u is None or dof_idx is None:
            return "—"
        try:
            u_e = np.asarray(u)[list(dof_idx)]
            U = 0.5 * float(u_e @ ke @ u_e)
            return f"{U:.4g}"
        except Exception:
            return "—"

    @staticmethod
    def _cond_str(ke: np.ndarray) -> str:
        try:
            return f"{float(np.linalg.cond(ke)):.3e}"
        except Exception:
            return "—"

    # ----- Capitulo 4: Ensamblaje global -----

    def _build_chapter5_ensamblaje(self) -> None:
        td = self._td
        proj = self._project
        sol = self._solution
        td.section_numbered("Ensamblaje del sistema global")
        td.para(
            r"Una vez calculada $\mathbf{k}_e$ para cada elemento (Cap.\ 4), "
            r"el ensamblaje suma sus contribuciones en $\mathbf{K}$ y "
            r"construye $\mathbf{F}$ a partir de las cargas externas. El "
            r"resultado es el sistema lineal $\mathbf{K}\,\mathbf{u} = "
            r"\mathbf{F}$ — aún sin BCs (Cap.\ 6). El procedimiento general "
            r"y la definición formal del operador LM se desarrollan en "
            r"\emph{Teoría MEF: M7 Ensamblaje}."
        )

        K = np.asarray(sol["K"])
        F = np.asarray(sol["F"])
        n_dof = K.shape[0]

        td.subsection_numbered("Mapeo de grados de libertad (LM)")
        td.para(
            r"Cada nodo $i$ contribuye con dos grados de libertad globales: "
            r"$\mathrm{GDL}_x = 2(i-1)$ y $\mathrm{GDL}_y = 2(i-1)+1$. "
            r"La matriz $\mathbf{LM}$ (location matrix) de cada elemento "
            r"lista los $2 \cdot n_{nodos}$ GDL globales que le corresponden. "
            r"El ensamblaje recorre los elementos y suma "
            r"$\mathbf{K}[\mathbf{LM}_e, \mathbf{LM}_e]\mathrel{+}=\mathbf{k}_e$ "
            r"y $\mathbf{F}[\mathbf{LM}_e]\mathrel{+}=\mathbf{f}_e$. Por ser "
            r"sumatoria, el orden de los elementos no afecta el resultado."
        )
        td.values([
            ("Cantidad de nodos", str(proj.num_nodes)),
            ("Grados de libertad totales", str(n_dof)),
            (r"Tamaño de $\mathbf{K}$", f"{n_dof} × {n_dof}"),
            (r"Tamaño de $\mathbf{F}$", f"{n_dof} × 1"),
        ])

        # Diagrama LM mapping: ke -> K para el showcase
        try:
            from file_io.figure_export import render_lm_mapping
            showcase_id = self._select_showcase_element()
            if showcase_id is not None:
                fig_lm = render_lm_mapping(proj, sol, showcase_id)
                path = self._save_figure(fig_lm, "lm_mapping")
                if path is not None:
                    td.figure(
                        path,
                        caption=(rf"Mapeo LM del elemento estrella "
                                 rf"$E_{{{showcase_id}}}$ hacia la matriz "
                                 rf"global $\mathbf{{K}}$: cada bloque "
                                 rf"$2 \times 2$ de $\mathbf{{k}}_e$ se "
                                 rf"suma al par de filas/columnas global "
                                 rf"correspondiente."),
                        label="fig:lm_mapping",
                        width=r"0.95\textwidth",
                    )
        except Exception:
            pass

        td.subsection_numbered(r"Matriz de rigidez global $\mathbf{K}$")
        # Umbral 8x8: arriba de eso la matriz literal satura el ancho A4
        # incluso con factor. El heatmap es mas pedagogico para K grandes.
        if n_dof <= 8:
            td.para(
                r"Por su tamaño moderado, se muestra literal. El exponente "
                r"común se factoriza para mantener todas las entradas dentro "
                r"del ancho de página:"
            )
            td.raw(r"{\scriptsize")
            td.matrix_factored(K, name=r"\mathbf{K}", sig_digits=3)
            td.raw(r"}")
        else:
            td.para(
                rf"Su dimensión $({n_dof}\times{n_dof})$ excede lo razonable "
                rf"para una matriz literal. Se muestra el patrón en "
                rf"escala logarítmica de $|K_{{ij}}|$:"
            )
            try:
                from file_io.figure_export import render_K_heatmap
                fig = render_K_heatmap(K, log_scale=True)
                path = self._save_figure(fig, "K_heatmap")
                if path is not None:
                    td.figure(path,
                              caption=(r"Patrón de la matriz $\mathbf{K}$ "
                                       r"en escala logarítmica."),
                              label="fig:K_heatmap",
                              width=r"0.75\textwidth")
            except Exception as e:
                td.para(rf"\emph{{No se pudo generar el heatmap: {e}}}")
            # Estadisticas
            nnz = int(np.sum(np.abs(K) > NUMERICAL_TOLERANCE_K))
            density = nnz / (n_dof * n_dof) if n_dof > 0 else 0.0
            try:
                cond = float(np.linalg.cond(K))
            except Exception:
                cond = float("nan")
            try:
                bandwidth = self._matrix_bandwidth(K)
            except Exception:
                bandwidth = "—"
            td.values([
                (r"Entradas no nulas ($|K_{ij}| > 10^{-9}$)", str(nnz)),
                ("Densidad", f"{density * 100:.3f}\\%"),
                (r"Ancho de banda", str(bandwidth)),
                (r"$\kappa_2(\mathbf{K})$ (estimado)",
                 f"{cond:.3e}" if np.isfinite(cond) else "—"),
            ])

        td.subsection_numbered(r"Vector de fuerzas globales $\mathbf{F}$")
        td.para(
            r"$\mathbf{F}$ acumula las contribuciones de cargas nodales "
            r"puntuales, fuerzas equivalentes nodales de cargas superficiales "
            r"distribuidas y fuerzas másicas (gravedad si está activa). "
            r"Forma compacta con exponente común factorizado:"
        )
        td.raw(r"{\scriptsize")
        td.vector_factored(F, name=r"\mathbf{F}", sig_digits=3, transpose=True)
        td.raw(r"}")
        self._desglose_F(F)

    @staticmethod
    def _matrix_bandwidth(M: np.ndarray) -> int:
        """Ancho de banda de M (max |i - j| con M[i,j] != 0)."""
        nz = np.argwhere(np.abs(M) > NUMERICAL_TOLERANCE_K)
        if nz.size == 0:
            return 0
        return int(np.max(np.abs(nz[:, 0] - nz[:, 1])))

    def _desglose_F(self, F: np.ndarray) -> None:
        """Tabla resumen del desglose de F por fuente."""
        td = self._td
        proj = self._project
        # Cargas nodales: suma directa
        f_nodal_x = sum(ld.fx for ld in proj.nodal_loads.values())
        f_nodal_y = sum(ld.fy for ld in proj.nodal_loads.values())
        # F total
        ftot_x = float(np.sum(F[0::2]))
        ftot_y = float(np.sum(F[1::2]))
        # Surface + gravedad: residuo (sin recalcular para no duplicar fem/)
        f_otros_x = ftot_x - f_nodal_x
        f_otros_y = ftot_y - f_nodal_y
        rows = [
            ["Cargas nodales puntuales",
             fmt(f_nodal_x, "force"), fmt(f_nodal_y, "force")],
            [r"Otras (superficiales + másicas)",
             fmt(f_otros_x, "force"), fmt(f_otros_y, "force")],
            [r"\textbf{Suma global $\mathbf{F}$}",
             rf"\textbf{{{fmt(ftot_x, 'force')}}}",
             rf"\textbf{{{fmt(ftot_y, 'force')}}}"],
        ]
        self._longtable(
            headers=["Fuente", r"$\sum F_x$", r"$\sum F_y$"],
            rows=rows,
            col_align="lrr",
        )

    # ----- Capitulo 5: Aplicacion de BCs -----

    def _build_chapter6_bcs(self) -> None:
        td = self._td
        proj = self._project
        sol = self._solution
        td.section_numbered("Aplicación de condiciones de contorno")
        td.para(
            r"EduFEM implementa el \textbf{método de eliminación} (única "
            r"vía de aplicación de BCs en el software): las filas y "
            r"columnas de los GDLs restringidos se quitan de $\mathbf{K}$ "
            r"y $\mathbf{F}$, formando el sistema reducido:"
        )
        td.equation(
            r"\mathbf{K}_{red}\, \mathbf{u}_{red} = \mathbf{F}_{red}"
        )
        td.educational_teaser(
            r"Sin BCs, $\mathbf{K}$ es singular (3 modos rígidos en 2D). "
            r"La eliminación restaura definida-positividad de "
            r"$\mathbf{K}_{red}$, condición necesaria para Cholesky.",
            cross_ref=r"M7 §Condiciones de contorno (método de eliminación)",
            phase="proc",
        )
        n_total = len(sol["u"])
        n_libres = len(sol["free_dofs"])
        n_restr = len(sol["restrained_dofs"])
        td.values([
            ("Grados de libertad totales", str(n_total)),
            ("Grados de libertad restringidos", str(n_restr)),
            ("Grados de libertad libres (resueltos)", str(n_libres)),
            (r"Tamaño de $\mathbf{K}_{red}$", f"{n_libres} × {n_libres}"),
        ])
        td.para(
            r"Una vez resuelto $\mathbf{u}_{red}$, los desplazamientos "
            r"prescritos se reinsertan en el vector global $\mathbf{u}$, "
            r"y las reacciones se obtienen de "
            r"$\mathbf{R} = \mathbf{K}\,\mathbf{u} - \mathbf{F}$."
        )

    # ----- Capitulo 6: Solucion y verificacion -----

    def _build_chapter7_solucion(self) -> None:
        td = self._td
        proj = self._project
        sol = self._solution
        td.section_numbered("Solución del sistema y verificación")
        td.para(
            r"Con el sistema reducido $\mathbf{K}_{red}\,\mathbf{u}_{red} = "
            r"\mathbf{F}_{red}$ del Cap.\ 6, este capítulo resuelve $\mathbf{u}$, "
            r"reinserta los desplazamientos prescritos, calcula las reacciones "
            r"en los apoyos y verifica el equilibrio global como control "
            r"de calidad de la solución numérica."
        )

        u = sol["u"]
        R = sol["reactions"]
        n_total = len(u)
        n_libres = len(sol["free_dofs"])
        n_restr = len(sol["restrained_dofs"])

        td.subsection_numbered("Método de resolución")
        td.para(
            r"$\mathbf{K}_{red}$ es SPD y se factoriza con \textbf{Cholesky} "
            r"$\mathbf{K}_{red} = \mathbf{L}\,\mathbf{L}^T$, resolviendo "
            r"$\mathbf{u}_{red}$ en dos sustituciones triangulares."
        )
        try:
            K = np.asarray(sol["K"])
            kappa = float(np.linalg.cond(K))
            kappa_str = f"{kappa:.3e}"
        except Exception:
            kappa_str = "—"
        td.values([
            (r"Algoritmo", "Cholesky $\\mathbf{L}\\,\\mathbf{L}^T$ (SPD)"),
            (r"Complejidad", r"$\sim \tfrac{1}{6} n_{libres}^{\,3}$ flops"),
            (r"Condicionamiento $\kappa_2(\mathbf{K})$", kappa_str),
        ])
        td.educational_teaser(
            r"Cholesky es $\sim 2\times$ más rápido que LU general "
            r"explotando la simetría, no requiere pivoteo y falla "
            r"limpiamente si $\mathbf{K}_{red}$ no es SPD.",
            cross_ref=r"M7 §Solver Cholesky",
            phase="proc",
        )

        td.subsection_numbered("Dimensiones del sistema")
        td.values([
            ("Grados de libertad totales", str(n_total)),
            ("Grados de libertad libres", str(n_libres)),
            ("Grados de libertad restringidos", str(n_restr)),
        ])

        td.subsection_numbered("Vector de desplazamientos nodales")
        td.para(
            r"El vector global $\mathbf{u}$ contiene un par $(u_x, u_y)$ por "
            r"nodo, ordenado por índice nodal ascendente. Se muestra primero "
            r"compacto con su exponente factorizado y luego desagregado por nodo:"
        )
        u_arr = np.asarray(u)
        td.raw(r"{\scriptsize")
        td.vector_factored(u_arr, name=r"\mathbf{u}", sig_digits=3,
                           transpose=True)
        td.raw(r"}")
        self._tabla_desplazamientos(u)

        td.subsection_numbered("Reacciones en los apoyos")
        td.para(
            r"Las reacciones se calculan como $\mathbf{R} = \mathbf{K}\,\mathbf{u} - \mathbf{F}$ "
            r"y son no nulas sólo en los GDL restringidos. Vector global y "
            r"desglose por nodo:"
        )
        R_arr = np.asarray(R)
        td.raw(r"{\scriptsize")
        td.vector_factored(R_arr, name=r"\mathbf{R}", sig_digits=3,
                           transpose=True)
        td.raw(r"}")
        self._tabla_reacciones(R)

        td.subsection_numbered("Verificación de equilibrio global")
        td.para(
            r"$\sum \mathbf{F}_{ext} + \sum \mathbf{R} = \mathbf{0}$ debe "
            r"cumplirse en cada dirección. Un residuo > $10^{-6}$ relativo "
            r"a las cargas sugiere problema (mal condicionamiento, BCs "
            r"inconsistentes, tolerancia del solver)."
        )
        td.educational_teaser(
            r"El equilibrio global emerge \emph{automáticamente} de las "
            r"ecuaciones discretas. Es un control de calidad barato — "
            r"hacerlo siempre antes de creer las tensiones.",
            cross_ref=r"M7 §Ensamblaje (sparsity y conservación)",
            phase="proc",
        )
        self._tabla_verificacion_equilibrio(R)

    def _tabla_desplazamientos(self, u: np.ndarray) -> None:
        proj = self._project
        idx_map = proj.node_index_map
        rows = []
        for nid in sorted(proj.nodes.keys()):
            base = 2 * idx_map[nid]
            ux = float(u[base])
            uy = float(u[base + 1])
            umag = float(np.sqrt(ux * ux + uy * uy))
            rows.append([
                str(nid),
                f"{ux:+.5e}",
                f"{uy:+.5e}",
                f"{umag:.5e}",
            ])
        self._longtable(
            headers=["Nodo", r"$u_x$", r"$u_y$", r"$|u|$"],
            rows=rows,
            col_align="rrrr",
        )

    def _tabla_reacciones(self, R: np.ndarray) -> None:
        proj = self._project
        if not proj.boundary_conditions:
            self._td.para(r"\emph{Sin reacciones (no hay restricciones).}")
            return
        idx_map = proj.node_index_map
        rows = []
        sum_rx = 0.0
        sum_ry = 0.0
        for nid in sorted(proj.boundary_conditions.keys()):
            bc = proj.boundary_conditions[nid]
            base = 2 * idx_map[nid]
            rx = float(R[base]) if bc.restrain_x else 0.0
            ry = float(R[base + 1]) if bc.restrain_y else 0.0
            sum_rx += rx
            sum_ry += ry
            rows.append([str(nid), fmt(rx, "force"), fmt(ry, "force")])
        rows.append([r"\textbf{Suma}",
                     rf"\textbf{{{fmt(sum_rx, 'force')}}}",
                     rf"\textbf{{{fmt(sum_ry, 'force')}}}"])
        self._longtable(
            headers=["Nodo", r"$R_x$", r"$R_y$"],
            rows=rows,
            col_align="rrr",
        )

    def _tabla_verificacion_equilibrio(self, R: np.ndarray) -> None:
        proj = self._project
        # Suma de cargas externas aplicadas
        Fx_aplicada = sum(ld.fx for ld in proj.nodal_loads.values())
        Fy_aplicada = sum(ld.fy for ld in proj.nodal_loads.values())
        # Suma de reacciones en GDL restringidos
        idx_map = proj.node_index_map
        Rx_total = 0.0
        Ry_total = 0.0
        for nid, bc in proj.boundary_conditions.items():
            base = 2 * idx_map[nid]
            if bc.restrain_x:
                Rx_total += float(R[base])
            if bc.restrain_y:
                Ry_total += float(R[base + 1])
        residuo_x = Fx_aplicada + Rx_total
        residuo_y = Fy_aplicada + Ry_total
        rows = [
            ["X", fmt(Fx_aplicada, "force"), fmt(Rx_total, "force"),
             f"{residuo_x:+.3e}"],
            ["Y", fmt(Fy_aplicada, "force"), fmt(Ry_total, "force"),
             f"{residuo_y:+.3e}"],
        ]
        self._longtable(
            headers=["Dirección", "Cargas aplicadas",
                     "Reacciones", "Residuo"],
            rows=rows,
            col_align="crrr",
        )

    # ----- Capitulo 7: Post-proceso -----

    def _build_chapter8_postproceso(self, showcase_id: Optional[int]) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Post-proceso: tensiones y visualización")

        td.para(
            r"El post-proceso recorre la cadena $\mathbf{u} \to "
            r"\boldsymbol{\varepsilon} \to \boldsymbol{\sigma}_{Gauss} \to "
            r"\boldsymbol{\sigma}_{nodo} \to \boldsymbol{\sigma}_{promediado} "
            r"\to (\sigma_1, \sigma_2, \sigma_{VM})$ para obtener las "
            r"magnitudes con las que se juzga el diseño. La derivación "
            r"completa de cada paso vive en \emph{Teoría MEF: M8 Post-Proceso}; "
            r"aquí se aplica al modelo del proyecto."
        )

        # Tensiones en puntos de Gauss
        td.subsection_numbered("Tensiones en los puntos de Gauss")
        td.para(
            r"Para cada elemento, $\boldsymbol{\sigma}=\mathbf{D}\,\mathbf{B}(\xi_p,\eta_p)\,"
            r"\mathbf{u}_e$ en cada PG. Los PG son los \emph{puntos "
            r"superconvergentes} de Barlow: la tensión calculada allí "
            r"tiene un orden de convergencia mayor que en el resto del "
            r"elemento."
        )
        td.educational_teaser(
            r"$\boldsymbol{\sigma}$ se obtiene derivando $\mathbf{u}$, "
            r"que es solo $C^0$ — por eso es discontinua entre elementos. "
            r"Los PG son el mejor lugar para evaluarla antes de extrapolar.",
            cross_ref=r"M4 §Superconvergencia + M8 §Tensiones en los PG",
            phase="post",
        )

        # Extrapolacion Gauss -> nodos
        td.subsection_numbered("Extrapolación de Gauss a nodos")
        td.para(
            r"Los valores en PG se llevan a los nodos vía "
            r"$\boldsymbol{\sigma}^{\,nodo} = \mathbf{E}\,\boldsymbol{\sigma}^{\,Gauss}$, "
            r"con $\mathbf{E} = \mathbf{N}_p^{-1}$ (matriz de funciones de "
            r"forma evaluadas en los PG, invertida)."
        )
        is_q9 = proj.element_type == ELEMENT_Q9
        if not is_q9:
            td.para(
                r"Para Q4 (PG en $\pm 1/\sqrt{3}$) la matriz cerrada con "
                r"factor $\sqrt{3}$ es:"
            )
            s = np.sqrt(3.0)
            E_q4 = 0.25 * np.array([
                [(1 + s) * (1 + s), (1 - s) * (1 + s),
                 (1 - s) * (1 - s), (1 + s) * (1 - s)],
                [(1 + s) * (1 - s), (1 - s) * (1 - s),
                 (1 - s) * (1 + s), (1 + s) * (1 + s)],
                [(1 - s) * (1 - s), (1 + s) * (1 - s),
                 (1 + s) * (1 + s), (1 - s) * (1 + s)],
                [(1 - s) * (1 + s), (1 + s) * (1 + s),
                 (1 + s) * (1 - s), (1 - s) * (1 - s)],
            ])
            td.matrix(E_q4, name=r"\mathbf{E}_{Q4}", fmt="{:+.4f}")
        else:
            td.para(
                r"Para Q9 (3$\times$3 PG), $\mathbf{E}_{Q9}$ es la inversa "
                r"numérica de $\mathbf{N}_p$ (9$\times$9), cacheada a "
                r"nivel de módulo."
            )

        # Figura del esquema didactico
        try:
            from file_io.figure_export import render_extrapolation_diagram
            fig_extrap = render_extrapolation_diagram()
            path = self._save_figure(fig_extrap, "extrapolation_diagram")
            if path is not None:
                td.figure(
                    path,
                    caption=("Esquema de extrapolación Q4: los valores en "
                             "los 4 puntos de Gauss (cuadrados naranjas) se "
                             "proyectan hacia los 4 nodos del elemento "
                             "(círculos azules) con factor $\\sqrt{3}$."),
                    label="fig:extrap_diagram",
                    width=r"0.65\textwidth",
                )
        except Exception:
            pass

        # Promediado nodal
        td.subsection_numbered("Promediado nodal entre elementos adyacentes")
        td.para(
            r"Un nodo compartido por $k$ elementos recibe $k$ valores "
            r"extrapolados distintos (las tensiones del MEF son discontinuas "
            r"entre elementos). El promediado nodal asigna a cada nodo el "
            r"promedio aritmético de sus contribuciones:"
        )
        td.equation(
            r"\sigma_n^{\,promediado} = "
            r"\frac{1}{k_n} \sum_{e \in \mathcal{E}_n} \sigma_n^{\,(e)}"
        )
        td.para(
            r"donde $\mathcal{E}_n$ es el conjunto de elementos que "
            r"comparten el nodo $n$ y $k_n = |\mathcal{E}_n|$."
        )
        td.educational_box(
            r"\textbf{El salto antes del promediado es un indicador de "
            r"error de malla.} Si las $k$ contribuciones a un mismo nodo "
            r"difieren mucho entre sí, la malla es insuficiente para "
            r"capturar el gradiente local; refinarla allí debería "
            r"reducir el salto. Por eso muchos códigos comerciales "
            r"muestran opcionalmente el campo \emph{no promediado} junto "
            r"al promediado: la diferencia es una herramienta de "
            r"diagnóstico, no un detalle estético.",
            title=r"\textbf{¿Por qué importa el promediado?}",
            phase="post",
        )
        try:
            from file_io.figure_export import render_averaging_diagram
            fig_avg = render_averaging_diagram()
            path = self._save_figure(fig_avg, "averaging_diagram")
            if path is not None:
                td.figure(
                    path,
                    caption=("Promediado nodal: un nodo compartido por 4 "
                             "elementos recibe 4 valores extrapolados (barras); "
                             "el promedio aritmético (línea naranja) es el "
                             "valor reportado en el contorno final."),
                    label="fig:avg_diagram",
                    width=r"0.95\textwidth",
                )
        except Exception:
            pass

        # Tensiones principales
        td.subsection_numbered(
            r"Tensiones principales $\sigma_1$, $\sigma_2$ y dirección $\theta_p$"
        )
        td.para(
            r"En 2D el estado tensional en un punto se describe por "
            r"$(\sigma_x, \sigma_y, \tau_{xy})$. \textbf{Las tensiones "
            r"principales} $\sigma_1 \geq \sigma_2$ son los autovalores "
            r"del tensor de tensiones; corresponden a las tensiones "
            r"normales máxima y mínima sobre los planos donde el corte "
            r"se anula ($\tau = 0$). Su expresión cerrada es:"
        )
        td.equation(
            r"\sigma_{1,2} = \frac{\sigma_x + \sigma_y}{2} \pm "
            r"\sqrt{\left(\frac{\sigma_x - \sigma_y}{2}\right)^2 + \tau_{xy}^{\,2}}"
        )
        td.para(
            r"La dirección principal $\theta_p$ (ángulo del plano "
            r"perpendicular a $\sigma_1$ respecto del eje $x$) es:"
        )
        td.equation(
            r"\tan(2\theta_p) = \frac{2\,\tau_{xy}}{\sigma_x - \sigma_y}"
        )
        td.educational_teaser(
            r"$\sigma_1 > 0$ tracción (azul) y $\sigma_2 < 0$ compresión "
            r"(rojo) — mismo código del canvas. Las cruces sobre la malla "
            r"muestran el flujo de carga.",
            cross_ref=r"M8 §Tensiones principales",
            phase="post",
        )
        # Cruces principales sobre la malla
        if self._nodal_stresses:
            try:
                from file_io.figure_export import render_principal_crosses
                fig_pc = render_principal_crosses(proj, self._nodal_stresses)
                path = self._save_figure(fig_pc, "principal_crosses")
                if path is not None:
                    td.figure(
                        path,
                        caption=("Cruces principales por elemento sobre la "
                                 "malla: el brazo largo de cada cruz da la "
                                 "dirección y magnitud de $\\sigma_1$; el "
                                 "brazo corto perpendicular, las de "
                                 "$\\sigma_2$. Azul = tracción, rojo = "
                                 "compresión."),
                        label="fig:principal_crosses",
                        width=r"0.85\textwidth",
                    )
            except Exception:
                pass

        # Von Mises
        td.subsection_numbered(
            r"Tensión equivalente de von Mises $\sigma_{VM}$"
        )
        td.para(
            r"El criterio de von Mises convierte el estado tensional 2D "
            r"en un escalar comparable contra la tensión de fluencia "
            r"uniaxial $\sigma_y$ del material. Para problemas planos:"
        )
        td.equation(
            r"\sigma_{VM} = \sqrt{\sigma_x^{\,2} - \sigma_x\,\sigma_y + "
            r"\sigma_y^{\,2} + 3\,\tau_{xy}^{\,2}} = "
            r"\sqrt{\sigma_1^{\,2} - \sigma_1\,\sigma_2 + \sigma_2^{\,2}}"
        )
        td.educational_teaser(
            r"Plastifica si $\sigma_{VM} \geq \sigma_y$. Estándar en "
            r"diseño dúctil (metales, aceros). En frágiles (hormigón, "
            r"vidrio) subestima — usar criterios específicos para frágiles.",
            cross_ref=r"M8 §Criterio de von Mises",
            phase="post",
        )

        # Tabla de tensiones nodales promediadas
        td.subsection_numbered("Tensiones nodales (promediadas)")
        td.para(
            r"Aplicando la cadena $\sigma_{Gauss} \to \sigma_{nodo} \to "
            r"\sigma_{promediado} \to (\sigma_1, \sigma_2, \sigma_{VM})$ a cada "
            r"elemento del modelo se obtiene la tabla siguiente. Es el insumo "
            r"de los contornos de la subsección \ref{sec:contornos}."
        )
        if self._nodal_stresses:
            self._tabla_nodal_stresses()
        else:
            td.para(r"\emph{Esfuerzos nodales no disponibles.}")

        # Deformada
        td.subsection_numbered("Visualización de la deformada")
        deformed_fig = self._contour_figures.get("deformed")
        if deformed_fig is None:
            try:
                from file_io.figure_export import render_deformed
                deformed_fig = render_deformed(proj, self._solution)
            except Exception:
                deformed_fig = None
        if deformed_fig is not None:
            path = self._save_figure(deformed_fig, "deformed")
            if path is not None:
                td.figure(path,
                          caption=("Configuración deformada (escala "
                                   "automática). La malla original aparece "
                                   "en gris discontinuo, la deformada en "
                                   "verde."),
                          label="fig:deformed",
                          width=r"0.85\textwidth")

        # Mapas de contornos
        td.subsection_numbered("Mapas de contornos de tensiones")
        td.raw(r"\label{sec:contornos}")
        td.para(
            r"Los contornos siguen la convención perceptual estándar: "
            r"\emph{coolwarm} (divergente) para $\sigma_x$, $\sigma_y$ "
            r"y $\tau_{xy}$ —donde el cero tiene significado físico "
            r"(tracción vs.\ compresión)— y \emph{viridis} (secuencial) "
            r"para $\sigma_{VM}$, que es no negativo por construcción."
        )
        for component in ("sigma_x", "sigma_y", "tau_xy", "von_mises"):
            self._insertar_contorno(component)

        # 7.9 Mohr del showcase
        if showcase_id is not None:
            self._insertar_mohr_showcase(showcase_id)

    def _tabla_nodal_stresses(self) -> None:
        rows = []
        for nid in sorted(self._nodal_stresses.keys()):
            s = self._nodal_stresses[nid]
            rows.append([
                str(nid),
                fmt(s.get("sigma_x", 0.0), "stress"),
                fmt(s.get("sigma_y", 0.0), "stress"),
                fmt(s.get("tau_xy", 0.0), "stress"),
                fmt(s.get("sigma_1", 0.0), "stress"),
                fmt(s.get("sigma_2", 0.0), "stress"),
                fmt(s.get("von_mises", 0.0), "stress"),
            ])
        self._longtable(
            headers=["Nodo", r"$\sigma_x$", r"$\sigma_y$", r"$\tau_{xy}$",
                     r"$\sigma_1$", r"$\sigma_2$", r"$\sigma_{VM}$"],
            rows=rows,
            col_align="rrrrrrr",
        )

    def _insertar_contorno(self, component: str) -> None:
        td = self._td
        fig = self._contour_figures.get(component)
        if fig is None:
            try:
                from file_io.figure_export import render_contour
                fig = render_contour(self._project, self._solution,
                                     self._nodal_stresses, component)
            except Exception:
                fig = None
        if fig is None:
            return
        path = self._save_figure(fig, f"contour_{component}")
        if path is None:
            return
        labels = {
            "sigma_x": r"$\sigma_x$",
            "sigma_y": r"$\sigma_y$",
            "tau_xy": r"$\tau_{xy}$",
            "von_mises": r"$\sigma_{VM}$ (von Mises)",
        }
        label = labels.get(component, component)
        td.figure(path,
                  caption=f"Contorno de {label} (valores nodales promediados).",
                  label=f"fig:contour_{component}",
                  width=r"0.85\textwidth")

    def _insertar_mohr_showcase(self, showcase_id: int) -> None:
        td = self._td
        es = self._element_stresses.get(showcase_id)
        if not es:
            return
        gauss_stresses = es.get("gauss_stresses", [])
        if not gauss_stresses:
            return
        # Tomamos el primer punto de Gauss del elemento estrella
        gp0 = gauss_stresses[0]
        try:
            sx = float(gp0["sigma_x"])
            sy = float(gp0["sigma_y"])
            txy = float(gp0["tau_xy"])
        except Exception:
            return
        td.subsection_numbered(
            f"Círculo de Mohr — Elemento {showcase_id}, PG1"
        )
        td.para(
            rf"Estado tensional en el primer punto de Gauss del elemento "
            rf"estrella $E_{{{showcase_id}}}$: "
            rf"$\sigma_x = {sx:+.4g}$, $\sigma_y = {sy:+.4g}$, "
            rf"$\tau_{{xy}} = {txy:+.4g}$."
        )
        try:
            from file_io.figure_export import render_mohr_circle
            fig = render_mohr_circle(sx, sy, txy,
                                     label=f"E{showcase_id}, PG1")
            path = self._save_figure(fig, f"mohr_E{showcase_id}_PG1")
            if path is not None:
                td.figure(path,
                          caption=(rf"Círculo de Mohr para el elemento "
                                   rf"{showcase_id} en PG1."),
                          label=f"fig:mohr_e{showcase_id}",
                          width=r"0.7\textwidth")
        except Exception as e:
            td.para(rf"\emph{{No se pudo generar el círculo de Mohr: {e}}}")

    # ----- Capitulo 8: Calidad de malla -----

    def _build_chapter3_calidad(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Calidad de la malla")
        td.para(
            r"Antes de pesar el solve, EduFEM audita la malla. Las "
            r"métricas reportadas a continuación evalúan en qué medida "
            r"cada elemento se aleja del cuadrado regular: $q_{SJ}\approx 1$ "
            r"y $R_J\approx 1$ indican un mapeo bien condicionado; "
            r"$q_{SJ}<0$ señala un elemento invertido (det J < 0) que "
            r"romperá la formulación. La definición operativa de cada "
            r"métrica vive en \emph{Teoría MEF: M0 Calidad geométrica}."
        )
        td.educational_teaser(
            r"$\kappa_2(\mathbf{K})$ escala con el peor $\det \mathbf{J}$ "
            r"del modelo. Estado \emph{Pobre/Inválido} en la tabla = "
            r"refinar o reformular antes de creer las tensiones.",
            cross_ref=r"M0 §Razón de Jacobianos / §Aspect ratio",
            phase="pre",
        )
        try:
            from fem.mesh_quality import evaluate_mesh_quality
            results = evaluate_mesh_quality(proj)
        except Exception as e:
            td.para(rf"\emph{{No se pudo evaluar la calidad: {e}}}")
            return
        if not results:
            td.para(r"\emph{Sin elementos para evaluar.}")
            return
        is_q9 = proj.element_type == ELEMENT_Q9
        if is_q9:
            headers = ["Elem", r"$q_{SJ}$", r"$R_J$", r"$AR$", r"$q_D$",
                       r"$\theta_{min}$", r"$\theta_{max}$", "Estado"]
            col_align = "rrrrrrrl"
        else:
            headers = ["Elem", r"$q_{SJ}$", r"$R_J$", r"$AR$",
                       r"$T_R$", r"$\theta_{min}$", r"$\theta_{max}$", "Estado"]
            col_align = "rrrrrrrl"
        rows = []
        for eid in sorted(results.keys()):
            r = results[eid]
            fourth = (r.get("midside_admissibility") or {}).get("q_D") if is_q9 \
                else r.get("robinson_taper")
            fourth_str = f"{fourth:.3f}" if fourth is not None and \
                np.isfinite(fourth) else "—"
            rows.append([
                str(eid),
                f"{r['scaled_jacobian']:.3f}",
                f"{r['jacobian_ratio']:.3f}",
                f"{r['robinson_aspect']:.3f}",
                fourth_str,
                fmt(r["min_angle"], "angle"),
                fmt(r["max_angle"], "angle"),
                TheoryDoc.escape(r["status"]),
            ])
        self._longtable(headers=headers, rows=rows, col_align=col_align)

    # ----- Apendice A: ke de los demas elementos -----

    def _build_appendix_a_kes(self, showcase_id: Optional[int]) -> None:
        td = self._td
        proj = self._project
        sol = self._solution
        elem_data = sol.get("element_data", {})
        td.section_numbered("Matrices de rigidez elementales")
        td.para(
            r"Esta sección agrupa las matrices $\mathbf{k}_e$ del resto de "
            r"los elementos del modelo. La matriz del elemento estrella ya "
            r"fue desarrollada en el Capítulo 3."
        )
        # Para Q9 (k_e 18x18) usamos pdflscape para apaisado
        is_q9 = proj.element_type == ELEMENT_Q9
        if is_q9:
            td.package("pdflscape")
        any_shown = False
        for eid in sorted(proj.elements.keys()):
            if eid == showcase_id:
                continue
            data = elem_data.get(eid)
            if data is None:
                continue
            ke = np.asarray(data.get("ke"))
            if ke.size == 0:
                continue
            any_shown = True
            elem = proj.elements[eid]
            td.subsection(f"Elemento {eid}")
            td.values([
                ("Material", TheoryDoc.escape(elem.material_name)),
                ("Espesor", fmt(elem.thickness, "length")),
                (r"$\|\mathbf{k}_e\|_F$",
                 f"{float(np.linalg.norm(ke, 'fro')):.4g}"),
            ])
            if is_q9:
                # Apaisado para que entre la 18x18, factor de escala comun.
                td.raw(r"\begin{landscape}")
                td.raw(r"{\tiny")
                td.matrix_factored(ke, name=rf"\mathbf{{k}}_{{{eid}}}",
                                   sig_digits=2)
                td.raw(r"}")
                td.raw(r"\end{landscape}")
            else:
                td.raw(r"{\scriptsize")
                td.matrix_factored(ke, name=rf"\mathbf{{k}}_{{{eid}}}",
                                   sig_digits=3)
                td.raw(r"}")
        if not any_shown:
            td.para(
                r"\emph{El modelo posee un único elemento; no hay matrices "
                r"adicionales para listar.}"
            )

    # ----- Apendice B: Datos completos -----

    def _build_appendix_b_datos(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Datos completos del análisis")

        td.subsection_numbered(
            "Tensiones por punto de Gauss (todos los elementos)"
        )
        if not self._element_stresses:
            td.para(r"\emph{Datos de tensiones por punto Gauss no disponibles.}")
        else:
            self._tabla_gauss_stresses_completos()

        td.subsection_numbered("Vector de desplazamientos completo")
        u = np.asarray(self._solution["u"])
        td.para(
            r"Vector $\mathbf{u}$ completo con su exponente común factorizado "
            r"(orden ascendente por GDL global):"
        )
        td.raw(r"{\scriptsize")
        td.vector_factored(u, name=r"\mathbf{u}", sig_digits=4, transpose=True)
        td.raw(r"}")
        td.para(
            r"Desglose por GDL para inspección puntual:"
        )
        rows = [[str(i), f"{float(v):+.5e}"] for i, v in enumerate(u)]
        self._longtable(
            headers=["GDL", r"$u_i$"],
            rows=rows,
            col_align="rr",
        )

    def _tabla_gauss_stresses_completos(self) -> None:
        rows = []
        for eid in sorted(self._element_stresses.keys()):
            es = self._element_stresses[eid]
            for gp_idx, gs in enumerate(es.get("gauss_stresses", []), start=1):
                rows.append([
                    str(eid),
                    f"PG{gp_idx}",
                    fmt(gs.get("sigma_x", 0.0), "stress"),
                    fmt(gs.get("sigma_y", 0.0), "stress"),
                    fmt(gs.get("tau_xy", 0.0), "stress"),
                    fmt(gs.get("sigma_1", 0.0), "stress"),
                    fmt(gs.get("sigma_2", 0.0), "stress"),
                    fmt(gs.get("von_mises", 0.0), "stress"),
                ])
        if not rows:
            self._td.para(r"\emph{Sin tensiones por PG.}")
            return
        self._longtable(
            headers=["Elem", "PG", r"$\sigma_x$", r"$\sigma_y$",
                     r"$\tau_{xy}$", r"$\sigma_1$", r"$\sigma_2$",
                     r"$\sigma_{VM}$"],
            rows=rows,
            col_align="ccrrrrrr",
        )

    # ----- Apendice C: Glosario MEF -----

    def _build_appendix_c_glosario(self) -> None:
        """Glosario de simbolos y conceptos MEF.

        Tabla de referencia rapida para que el alumno pueda saltar a
        cualquier capitulo sin perderse en la notacion.
        """
        td = self._td
        td.section_numbered("Glosario de símbolos y términos")
        td.para(
            r"Referencia rápida de la notación usada en esta memoria. "
            r"Las definiciones siguen la convención del MEF estándar "
            r"(Bathe, Cook, Zienkiewicz)."
        )
        glosario = [
            (r"$\mathbf{u}$", "Vector de desplazamientos nodales globales "
                              "(2 entradas por nodo: $u_x$, $u_y$)."),
            (r"$\mathbf{F}$", "Vector de fuerzas nodales globales."),
            (r"$\mathbf{K}$", "Matriz de rigidez global del sistema. "
                              "Simétrica, dispersa, definida positiva tras "
                              "aplicar BCs."),
            (r"$\mathbf{R}$", "Vector de reacciones en GDLs restringidos. "
                              "Se calcula como $\\mathbf{K}\\,\\mathbf{u} - "
                              "\\mathbf{F}$."),
            (r"$\xi, \eta$", "Coordenadas naturales (paramétricas) del "
                             "elemento maestro. Dominio $[-1, 1]^2$."),
            (r"$N_i(\xi, \eta)$", "Funciones de forma del elemento. "
                                  "Interpolan tanto la geometría como el "
                                  "campo de desplazamientos "
                                  "(isoparamétrico)."),
            (r"$\mathbf{J}$", "Matriz Jacobiana del mapeo natural→físico. "
                              "$\\det \\mathbf{J} > 0$ requerido."),
            (r"$\mathbf{B}$", "Matriz deformación-desplazamiento "
                              "($\\boldsymbol{\\varepsilon} = "
                              "\\mathbf{B}\\,\\mathbf{u}_e$). Derivadas de "
                              "$N_i$ respecto de $x, y$."),
            (r"$\mathbf{D}$", "Matriz constitutiva del material. Relaciona "
                              "deformaciones con tensiones por la ley de "
                              "Hooke."),
            (r"$\mathbf{k}_e$", "Matriz de rigidez elemental. "
                                "$\\int \\mathbf{B}^T\\mathbf{D}\\,"
                                "\\mathbf{B}\\,|\\det \\mathbf{J}|\\,t\\,d\\Omega$."),
            (r"$w_p, (\xi_p, \eta_p)$", "Pesos y posiciones de los puntos "
                                        "de cuadratura de Gauss."),
            (r"$\boldsymbol{\varepsilon}$", "Vector de deformaciones "
                                            "$(\\varepsilon_x, "
                                            "\\varepsilon_y, "
                                            "\\gamma_{xy})$."),
            (r"$\boldsymbol{\sigma}$", "Vector de tensiones $(\\sigma_x, "
                                       "\\sigma_y, \\tau_{xy})$."),
            (r"$\sigma_1, \sigma_2$", "Tensiones principales (autovalores "
                                      "del tensor de tensiones 2D). "
                                      "$\\sigma_1 \\geq \\sigma_2$."),
            (r"$\theta_p$", "Ángulo de la dirección principal "
                            "($\\sigma_1$) respecto del eje $x$."),
            (r"$\sigma_{VM}$", "Tensión equivalente de von Mises. Métrica "
                               "escalar de plastificación para materiales "
                               "dúctiles."),
            (r"GDL", "Grado de libertad. Cada nodo aporta 2 GDLs en 2D."),
            ("Q4 / Q9", "Cuadriláteros isoparamétricos de 4 / 9 nodos. "
                        "Q4 lineal por arista, Q9 bicuadrático."),
            ("PG", "Punto de Gauss. Lugar donde la tensión es "
                   "superconvergente (Barlow 1976)."),
            ("BC", "Boundary Condition (restricción). Prescripción de "
                   "$u_x$ y/o $u_y$ en un nodo."),
        ]
        # Descripciones son LaTeX controlado (incluyen $...$ inline math) —
        # no escapar.
        self._longtable(
            headers=["Símbolo / término", "Significado"],
            rows=[[k, v] for k, v in glosario],
            col_align="lp{10cm}",
        )

    # ----- Pie -----

    def _build_pie(self) -> None:
        td = self._td
        td.raw(r"\vfill")
        td.raw(r"\begin{center}\rule{0.4\textwidth}{0.4pt}\end{center}")
        td.para(
            rf"\emph{{Documento generado por {TheoryDoc.escape(APP_NAME)} "
            rf"v{APP_VERSION}.}}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _longtable(self, *, headers: list[str], rows: list[list[str]],
                   col_align: str) -> None:
        """Construye una tabla long (multipagina) con headers en negrita."""
        td = self._td
        td.package("longtable")
        td.package("booktabs")
        n_cols = len(headers)
        if any(len(r) != n_cols for r in rows):
            raise ValueError(
                f"longtable: filas con cantidad de columnas inconsistente "
                f"(esperado {n_cols})."
            )
        if len(col_align) != n_cols:
            col_align = "l" * n_cols
        head_row = " & ".join(rf"\textbf{{{h}}}" for h in headers) + r" \\"
        td.raw(rf"\begin{{center}}")
        td.raw(rf"\begin{{longtable}}{{{col_align}}}")
        td.raw(r"\toprule")
        td.raw(head_row)
        td.raw(r"\midrule")
        td.raw(r"\endfirsthead")
        td.raw(r"\toprule")
        td.raw(head_row)
        td.raw(r"\midrule")
        td.raw(r"\endhead")
        td.raw(r"\bottomrule")
        td.raw(r"\endfoot")
        for r in rows:
            td.raw(" & ".join(r) + r" \\")
        td.raw(r"\end{longtable}")
        td.raw(r"\end{center}")
