"""
Memoria de Cálculo: generador de PDF educativo paso-a-paso del análisis MEF.

Compila un documento LaTeX (vía pylatex + pdflatex) que describe el pipeline
clásico del Método de los Elementos Finitos aplicado al proyecto resuelto:
planteo del problema, discretización, calidad de malla, formulación
elemental detallada (N → J → B → D → kₑ por cuadratura de Gauss),
ensamblaje, aplicación de restricciones, resolución del sistema lineal,
reacciones, verificación de equilibrio y post-proceso (tensiones en puntos
de Gauss → extrapolación → promediado nodal → principales / von Mises) con
contornos y figuras de campo.

La narrativa se basa en la teoría general de los textos clásicos del MEF
(Zienkiewicz, Hughes, Bathe, Cook) y NO menciona detalles internos del
software (librerías, factorizaciones específicas, estructuras de datos):
es una memoria de cálculo educativa autocontenida.

Modo de presentación del paso-a-paso elemental (auto-detectado en función
del tamaño del modelo):
  - Modo "compacto" (todo el modelo paso a paso): aplica cuando
      * Q4 con <= 2 elementos / <= 12 GDL, o
      * Q9 con = 1 elemento / 18 GDL.
    En esos casos las matrices kₑ, B y J caben legibles para cada elemento
    del modelo y se muestran todas en el cuerpo principal.
  - Modo "showcase" (un solo elemento + nota): aplica cuando el modelo
    excede ese umbral. Se desarrolla con detalle el elemento de mayor
    energía de deformación, y se aclara que los restantes se obtienen
    siguiendo el mismo procedimiento.

Estilos (`MemoriaCalculo.STYLES`) — DOS, comparten un único pipeline; la
diferencia la gobierna la property `_prose`:
  - 'educativo' (default): infografía + narrativa mínima. Cada concepto se
    resume en UNA idea clave (teaser de 1 línea, dict `_INSIGHTS`), con
    tarjetas "entra · fórmula · salida" por capítulo, mapa del cálculo,
    fórmulas al margen, barra de fase en el encabezado y glosario final.
    Solo 2 cajas "¿por qué?" en todo el documento (Gauss y promediado).
  - 'directo': el MISMO procedimiento matricial paso a paso (N → J → B →
    D → integrando → kₑ por elemento, ensamblaje, partición de BCs,
    resolución, tensiones), pero SECO: encabezados + fórmula + matriz +
    resultado clave, sin párrafos ni cajas.

Regla de oro del pipeline compartido: las FÓRMULAS/MATRICES/ECUACIONES se
emiten SIEMPRE (incondicional); SOLO los párrafos narrativos y las cajas
pedagógicas van gateados tras `if self._prose:`. No volver a meter una
`td.equation`/`td.matrix` dentro de un `if self._prose` (desaparecería del
estilo directo, que es justamente el procedimiento matricial).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from typing import Callable, Optional

import numpy as np
from scipy.sparse import issparse

from config.settings import (
    APP_NAME, APP_VERSION,
    ANALYSIS_PLANE_STRESS,
    ELEMENT_Q4, ELEMENT_Q9,
    NUMERICAL_TOLERANCE,
    fmt,
)

# Tolerancia para considerar "no nulo" en estadísticas de K (nnz, banda).
NUMERICAL_TOLERANCE_K = max(NUMERICAL_TOLERANCE, 1e-9)

from education.components.theory_builder import TheoryDoc


class MemoriaCalculoError(RuntimeError):
    """Error elevado por el generador con un mensaje accionable para el usuario."""


# ---------------------------------------------------------------------------
# Helpers de matriz global (K puede ser scipy.sparse CSR o densa)
# ---------------------------------------------------------------------------

def _K_dimension(K) -> int:
    """Dimensión n de la matriz cuadrada K (densa o sparse)."""
    if issparse(K):
        return K.shape[0]
    A = np.asarray(K)
    return A.shape[0] if A.ndim == 2 else 0


def _K_to_dense(K) -> np.ndarray:
    """Devuelve K como np.ndarray densa (materializa si es sparse)."""
    if issparse(K):
        return K.toarray()
    return np.asarray(K, dtype=float)


def _K_nnz(K) -> int:
    """Cantidad de entradas con |K_ij| > tolerancia."""
    if issparse(K):
        data = K.tocoo().data
        return int(np.sum(np.abs(data) > NUMERICAL_TOLERANCE_K))
    A = np.asarray(K)
    return int(np.sum(np.abs(A) > NUMERICAL_TOLERANCE_K))


def _K_bandwidth(K) -> int:
    """Ancho de banda (máx |i−j| con K_ij ≠ 0). Sparse-friendly."""
    if issparse(K):
        coo = K.tocoo()
        mask = np.abs(coo.data) > NUMERICAL_TOLERANCE_K
        if not np.any(mask):
            return 0
        return int(np.max(np.abs(coo.row[mask] - coo.col[mask])))
    A = np.asarray(K)
    nz = np.argwhere(np.abs(A) > NUMERICAL_TOLERANCE_K)
    if nz.size == 0:
        return 0
    return int(np.max(np.abs(nz[:, 0] - nz[:, 1])))


def _K_cond(K, *, max_dense: int = 200) -> Optional[float]:
    """κ₂(K) estimado. Solo para K chica (SVD densa); None si es grande."""
    n = _K_dimension(K)
    if n == 0 or n > max_dense:
        return None
    try:
        return float(np.linalg.cond(_K_to_dense(K)))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# API pública
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
    style: str = "educativo",
    progress_callback: Optional[Callable[[str, float], None]] = None,
    keep_tex: bool = False,
) -> str:
    """Genera el PDF educativo y retorna la ruta del archivo creado.

    Parámetros
    ----------
    project : ProjectModel ya resuelto (`project.is_solved == True`).
    solution : dict retornado por `fem.solver.solve_system` (K es sparse CSR).
    element_stresses, nodal_stresses : retornados por
        `fem.stress.compute_all_stresses`. Pueden ser None (los capítulos de
        post-proceso degradan elegantemente).
    filepath : ruta destino, debe terminar en `.pdf`.
    mesh_diagram, contour_figures : imágenes PIL opcionales pre-renderizadas.
    scope : reservado para iteraciones futuras.
    style : 'educativo' (default) o 'directo'.
    progress_callback : callable(stage_label, pct_0_a_1) opcional.
    keep_tex : si True, conserva el `.tex` intermedio para depuración.
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
    memoria = MemoriaCalculo(project, solution, element_stresses,
                             nodal_stresses,
                             mesh_diagram=mesh_diagram,
                             contour_figures=contour_figures,
                             scope=scope, style=style)

    _progress("Construyendo capítulos", 0.15)
    memoria.build()

    _progress("Compilando con pdflatex", 0.55)
    try:
        memoria.compile(filepath_no_ext, keep_tex=keep_tex)
    except FileNotFoundError as e:
        raise MemoriaCalculoError(
            "No se encontró pdflatex en el PATH. "
            "Instalá MiKTeX (https://miktex.org) o TeX Live y reiniciá EduFEM. "
            f"Detalle: {e}"
        ) from e
    except Exception as e:
        fallback_tex = filepath_no_ext + ".tex"
        try:
            with open(fallback_tex, "w", encoding="utf-8") as f:
                f.write(memoria.tex_source())
        except Exception:
            pass
        raise MemoriaCalculoError(
            f"pdflatex falló al compilar la Memoria de Cálculo. "
            f"Se conservó el .tex en:\n  {fallback_tex}\n"
            f"para depuración. Detalle: {e}"
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

    # Estilos válidos. Ver docstring del módulo y CLAUDE.md.
    STYLES = ("educativo", "directo")

    def __init__(self, project, solution, element_stresses, nodal_stresses,
                 *, mesh_diagram=None, contour_figures=None,
                 scope: str = "showcase", style: str = "educativo"):
        self._project = project
        self._solution = solution
        self._element_stresses = element_stresses or {}
        self._nodal_stresses = nodal_stresses or {}
        self._mesh_diagram = mesh_diagram
        self._contour_figures = dict(contour_figures) if contour_figures else {}
        self._scope = scope
        self._style = style if style in self.STYLES else "educativo"
        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None

        title = TheoryDoc.escape(self.TITLE)
        subtitle = TheoryDoc.escape(
            self.SUBTITLE_TEMPLATE.format(name=project.project_name)
        )
        self._td = TheoryDoc(title=title, subtitle=subtitle)
        self._configure_preamble()

    # ¿Incluir narrativa (párrafos, cajas pedagógicas, infografía)?
    # True solo para 'educativo'. 'directo' = el mismo pipeline sin prosa.
    @property
    def _prose(self) -> bool:
        return self._style == "educativo"

    def _configure_preamble(self) -> None:
        td = self._td
        proj = self._project
        td.package("babel", options="spanish")
        td.package("longtable")
        td.package("caption")
        td.package("fancyhdr")
        # Q9 tiene B (3×18) y kₑ (18×18); subimos el límite de columnas.
        td.raw(r"\setcounter{MaxMatrixCols}{20}")
        td.raw(r"\pagestyle{fancy}")
        td.raw(r"\fancyhf{}")
        proj_name_safe = TheoryDoc.escape(proj.project_name)
        td.raw(r"\fancyhead[L]{\small Memoria de Cálculo}")
        td.raw(rf"\fancyhead[R]{{\small {proj_name_safe}}}")
        td.raw(r"\fancyfoot[C]{\small \thepage}")
        td.raw(r"\renewcommand{\headrulewidth}{0.4pt}")
        td.raw(r"\setlength{\parskip}{4pt plus 1pt minus 1pt}")
        td.raw(r"\setlength{\parindent}{0pt}")
        td.raw(r"\setlength{\marginparwidth}{2cm}")
        td.raw(r"\setlength{\marginparsep}{6pt}")
        # Colores de fase disponibles desde el preámbulo (cards, márgenes,
        # mapa del cálculo) aunque el estilo directo no use cajas.
        td.ensure_edu_colors()

    def _chapter_card(self, *, entra: str, formula: str, sale: str,
                      phase: str = "proc") -> None:
        """Tarjeta ENTRA→fórmula→SALE del capítulo (solo educativo).

        Delegado a `TheoryDoc.chapter_io_card`; punto único para envolver en
        guard defensivo (si fallara, el documento sigue compilando)."""
        try:
            self._td.chapter_io_card(entra, formula, sale, phase=phase)
        except Exception:
            pass

    def build(self) -> None:
        """Llena el documento. Pipeline ÚNICO compartido por ambos estilos;
        la prosa/infografía la gobierna `self._prose` (True en 'educativo')."""
        self._build_pipeline()

    # ------------------------------------------------------------------
    # Pipeline ÚNICO (educativo con _prose=True / directo con _prose=False)
    # ------------------------------------------------------------------

    def _build_pipeline(self) -> None:
        self._build_cover()
        self._td.toc()
        if self._prose:
            # Mapa del cálculo (one-pager) + recorrido visual: solo educativo.
            self._build_intro()
            self._build_resumen_visual()
        self._build_cap_problema()
        self._build_cap_discretizacion()
        self._build_cap_calidad()
        showcase_id = self._select_showcase_element()
        compact_ids = self._compact_showcase_ids()
        if compact_ids is not None:
            # Modo compacto: desarrollar TODOS los elementos paso a paso.
            self._build_cap_showcase_compact(compact_ids)
        elif showcase_id is not None:
            # Modo showcase: sólo el elemento estrella + nota.
            self._build_cap_showcase(showcase_id)
        self._build_cap_ensamblaje()
        self._build_cap_bcs_solucion()
        self._build_cap_postproceso(showcase_id)
        if self._prose:
            # Glosario de símbolos: subsección final, solo educativo.
            self._build_glosario()
        self._build_pie()

    def compile(self, filepath_no_ext: str, *, keep_tex: bool = False) -> None:
        try:
            self._td.compile_to(filepath_no_ext, keep_tex=keep_tex)
        finally:
            self._cleanup_tmpdir()

    def tex_source(self) -> str:
        """Retorna el código .tex generado (para depuración / inspección)."""
        return self._td.document().dumps()

    # ------------------------------------------------------------------
    # Infraestructura de figuras (PIL)
    # ------------------------------------------------------------------

    def _ensure_tmpdir(self) -> str:
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

    def _save_figure(self, img, name: str) -> Optional[str]:
        """Guarda una imagen PIL en el tmpdir y retorna la ruta. None si falla."""
        if img is None:
            return None
        try:
            tmpdir = self._ensure_tmpdir()
            path = os.path.join(tmpdir, f"{name}.png")
            img.save(path)
            return path
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Portada + introducción
    # ------------------------------------------------------------------

    def _build_cover(self) -> None:
        td = self._td
        proj = self._project
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
            ("Grados de libertad (GDL)", str(proj.total_dof)),
            ("Hash del modelo", rf"\texttt{{{digest}}}"),
            ("Generado por", f"{TheoryDoc.escape(APP_NAME)} v{APP_VERSION}"),
        ]
        td.values(info)
        if self._prose:
            td.raw(r"\vspace{1em}")
            td.para(
                r"\emph{Este documento desarrolla paso a paso el análisis "
                r"por Elementos Finitos del proyecto, siguiendo el "
                r"procedimiento clásico de la formulación isoparamétrica: "
                r"planteo del problema, discretización, formulación "
                r"elemental, ensamblaje, condiciones de contorno, "
                r"resolución del sistema lineal y post-proceso de "
                r"tensiones. La teoría utilizada es la habitual de los "
                r"textos del MEF; los valores numéricos corresponden al "
                r"modelo concreto del usuario.}"
            )
        td.raw(r"\newpage")

    def _build_intro(self) -> None:
        td = self._td
        td.raw(r"\section*{¿Qué resuelve el MEF y cómo?}")
        td.raw(r"\addcontentsline{toc}{section}{¿Qué resuelve el MEF y cómo?}")
        # Gancho de 3 líneas: la idea, sin la derivación verbosa.
        td.para(
            r"El \textbf{Método de los Elementos Finitos (MEF)} reemplaza la "
            r"ecuación de equilibrio elástico "
            r"$\nabla\cdot\boldsymbol\sigma+\mathbf{b}=\mathbf{0}$ — sin "
            r"solución analítica para geometrías generales — por su "
            r"\emph{forma débil} sobre una malla finita, reduciéndola al "
            r"sistema algebraico"
        )
        td.equation(r"\mathbf{K}\,\mathbf{u} = \mathbf{F}.")
        # Mapa del cálculo (infografía Pillow) = índice visual del documento.
        # Reemplaza el enumerate narrativo de 5 pasos.
        img = None
        try:
            from file_io.figure_export import render_pipeline_map
            img = render_pipeline_map(self._project)
        except Exception:
            img = None
        path = self._save_figure(img, "pipeline_map")
        if path is not None:
            td.figure(path,
                      caption=r"Recorrido del cálculo: el dato que viaja "
                              r"entre etapas (malla $\to \mathbf{k}_e \to "
                              r"\mathbf{K},\mathbf{F} \to \mathbf{u} \to "
                              r"\boldsymbol\sigma$).",
                      label="fig:pipeline_map", width=r"\textwidth")
        else:
            # Degradación: enumerate textual si Pillow falla.
            td.para(r"La secuencia de cálculo de esta memoria es:")
            td.raw(r"\begin{enumerate}")
            td.raw(r"\item \textbf{Pre-proceso} — nodos, elementos, cargas, "
                   r"restricciones; calidad de malla.")
            td.raw(r"\item \textbf{Formulación elemental} — $\mathbf{N}$, "
                   r"$\mathbf{J}$, $\mathbf{B}$, $\mathbf{D}$, "
                   r"$\mathbf{k}_e$.")
            td.raw(r"\item \textbf{Ensamblaje} — $\mathbf{K}$, $\mathbf{F}$.")
            td.raw(r"\item \textbf{Condiciones de contorno + solución} — "
                   r"$\mathbf{u}$, $\mathbf{R}$.")
            td.raw(r"\item \textbf{Post-proceso} — tensiones, principales, "
                   r"von Mises, contornos.")
            td.raw(r"\end{enumerate}")
        td.raw(r"\newpage")

    def _build_resumen_visual(self) -> None:
        td = self._td
        img = self._mesh_diagram
        if img is None:
            try:
                from file_io.figure_export import render_mesh_diagram
                img = render_mesh_diagram(self._project)
            except Exception:
                img = None
        if img is None:
            return
        td.raw(r"\section*{Resumen visual del modelo}")
        path = self._save_figure(img, "mesh_diagram")
        if path is not None:
            td.figure(path,
                      caption="Discretización del modelo: nodos, elementos, "
                              "restricciones y cargas aplicadas.",
                      label="fig:mesh", width=r"0.92\textwidth")
        td.raw(r"\newpage")

    # ------------------------------------------------------------------
    # Capítulo 1: planteo del problema
    # ------------------------------------------------------------------

    def _build_cap_problema(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Planteo del problema")

        caso = ("Tensión plana"
                if proj.analysis_type == ANALYSIS_PLANE_STRESS
                else "Deformación plana")
        is_q4 = proj.element_type == ELEMENT_Q4
        elem_desc = ("Q4 (bilineal, Gauss 2×2)" if is_q4
                     else "Q9 (bicuadrático, Gauss 3×3)")

        if self._prose:
            self._chapter_card(
                entra=r"Hipótesis del plano · $E$, $\nu$",
                formula=r"\boldsymbol\sigma=\mathbf{D}\,\boldsymbol\varepsilon",
                sale=r"Matriz constitutiva $\mathbf{D}$",
                phase="pre",
            )
            td.educational_teaser(
                r"La \textbf{hipótesis del plano} no es un detalle: cambia "
                r"la forma de $\mathbf{D}$ y, con ella, todas las tensiones. "
                r"\textbf{Tensión plana} = cuerpos delgados (placas); "
                r"\textbf{deformación plana} = prismas largos (presas, "
                r"túneles).",
                phase="pre",
            )
        else:
            # Directo: hipótesis + tipo de elemento como dato seco (2 filas).
            td.values([("Hipótesis", caso), ("Elemento", elem_desc)])

        self._matriz_D_teorica()
        self._matriz_D_numerica_si_unico_material()

        td.subsection_numbered("Funciones de forma")
        # Fórmula de las N_i: SIEMPRE (es la base del isoparamétrico).
        if is_q4:
            td.equation(
                r"N_i(\xi,\eta)=\tfrac{1}{4}(1+\xi_i\xi)(1+\eta_i\eta), "
                r"\quad i=1,\dots,4"
            )
        else:
            td.equation(
                r"N_i(\xi,\eta)=L_a(\xi)\,L_b(\eta), \quad i=1,\dots,9"
            )
        if self._prose:
            td.educational_teaser(
                r"Las mismas $N_i$ interpolan geometría \emph{y} "
                r"desplazamiento ($\mathbf{x}=\sum N_i\mathbf{x}_i$, "
                r"$\mathbf{u}=\sum N_i\mathbf{u}_i$): eso es "
                r"\emph{isoparamétrico}. La rigidez se integra con Gauss "
                + (r"$2\times2$." if is_q4 else r"$3\times3$."),
                phase="proc",
            )

    def _matriz_D_teorica(self) -> None:
        td = self._td
        if self._project.analysis_type == ANALYSIS_PLANE_STRESS:
            td.equation(
                r"\mathbf{D} = \frac{E}{1-\nu^2}\begin{bmatrix}"
                r"1 & \nu & 0 \\ \nu & 1 & 0 \\ 0 & 0 & \tfrac{1-\nu}{2}"
                r"\end{bmatrix}"
            )
        else:
            td.equation(
                r"\mathbf{D} = \frac{E}{(1+\nu)(1-2\nu)}\begin{bmatrix}"
                r"1-\nu & \nu & 0 \\ \nu & 1-\nu & 0 \\ "
                r"0 & 0 & \tfrac{1-2\nu}{2}\end{bmatrix}"
            )

    def _matriz_D_numerica_si_unico_material(self) -> None:
        td = self._td
        proj = self._project
        materials_used = {e.material_name for e in proj.elements.values()}
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
            if self._prose:
                td.para(
                    rf"Para el material "
                    rf"\textbf{{{TheoryDoc.escape(mat_name)}}} "
                    rf"con $E={mat.E:g}$ y $\nu={mat.nu:g}$, la matriz "
                    rf"constitutiva evaluada es:"
                )
            td.matrix(D, name=r"\mathbf{D}", fmt="{:.4g}")
        elif self._prose:
            td.para(
                r"\emph{El modelo usa más de un material; cada elemento emplea "
                r"su propia $\mathbf{D}$ a partir de sus $E$ y $\nu$. La "
                r"formulación elemental muestra la del elemento seleccionado.}"
            )

    # ------------------------------------------------------------------
    # Capítulo 2: discretización
    # ------------------------------------------------------------------

    def _build_cap_discretizacion(self) -> None:
        td = self._td
        td.section_numbered("Discretización del modelo")
        if self._prose:
            self._chapter_card(
                entra=r"Geometría · cargas · apoyos",
                formula=r"\Omega \;\approx\; \bigcup_e \Omega_e",
                sale=r"Modelo discreto (nodos, elementos)",
                phase="pre",
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
        td.subsection_numbered("Restricciones")
        self._tabla_restricciones()

    def _tabla_materiales(self) -> None:
        proj = self._project
        if not proj.materials:
            self._td.para(r"\emph{Sin materiales definidos.}")
            return
        usados = {e.material_name for e in proj.elements.values()}
        rows: list[list[str]] = []
        for name, mat in proj.materials.items():
            if usados and name not in usados:
                continue
            density = getattr(mat, "density", None)
            rows.append([
                TheoryDoc.escape(name), f"{mat.E:g}", f"{mat.nu:g}",
                f"{density:g}" if density is not None else "—",
            ])
        if not rows:
            self._td.para(r"\emph{Ningún material está referenciado por elementos.}")
            return
        self._longtable(headers=["Material", r"$E$", r"$\nu$", r"$\rho$"],
                        rows=rows, col_align="lrrr")

    def _tabla_nodos(self) -> None:
        proj = self._project
        if not proj.nodes:
            self._td.para(r"\emph{Sin nodos definidos.}")
            return
        rows = [[str(nid), fmt(proj.nodes[nid].x, "length"),
                 fmt(proj.nodes[nid].y, "length")]
                for nid in sorted(proj.nodes.keys())]
        self._longtable(headers=["ID", r"$X$", r"$Y$"], rows=rows,
                        col_align="rrr")

    def _tabla_elementos(self) -> None:
        proj = self._project
        if not proj.elements:
            self._td.para(r"\emph{Sin elementos definidos.}")
            return
        is_q9 = proj.element_type == ELEMENT_Q9
        if is_q9:
            headers = ["ID", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8",
                       "N9", "Espesor", "Material"]
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
        rows = [[str(nid), fmt(proj.nodal_loads[nid].fx, "force"),
                 fmt(proj.nodal_loads[nid].fy, "force")]
                for nid in sorted(proj.nodal_loads.keys())]
        self._longtable(headers=["Nodo", r"$F_x$", r"$F_y$"], rows=rows,
                        col_align="rrr")

    def _tabla_cargas_superficiales(self) -> None:
        proj = self._project
        if not getattr(proj, "surface_loads", None):
            self._td.para(r"\emph{Sin cargas superficiales definidas.}")
            return
        rows = []
        for idx, sl in enumerate(proj.surface_loads, start=1):
            angle = getattr(sl, "angle", 0.0)
            rows.append([str(idx), str(sl.node_start), str(sl.node_end),
                         fmt(sl.q_start, "force"), fmt(sl.q_end, "force"),
                         fmt(angle, "angle")])
        self._longtable(
            headers=[r"\#", "N inicio", "N fin", r"$q_{inicio}$", r"$q_{fin}$",
                     r"$\theta$ (°)"],
            rows=rows, col_align="rrrrrr")

    def _tabla_restricciones(self) -> None:
        proj = self._project
        if not proj.boundary_conditions:
            self._td.para(r"\emph{Sin restricciones definidas. El sistema "
                          r"sería singular sin ellas.}")
            return
        rows = [[str(nid),
                 "Sí" if proj.boundary_conditions[nid].restrain_x else "No",
                 "Sí" if proj.boundary_conditions[nid].restrain_y else "No"]
                for nid in sorted(proj.boundary_conditions.keys())]
        self._longtable(headers=["Nodo", "Restringe X", "Restringe Y"],
                        rows=rows, col_align="rcc")

    # ------------------------------------------------------------------
    # Capítulo 3: calidad de la malla
    # ------------------------------------------------------------------

    @staticmethod
    def _q_sj_colored(value: float) -> str:
        """q_SJ formateado con color por umbral (heatmap textual de calidad):
        rojo si invertido (≤0), ámbar si pobre (<0.5), verde si bueno."""
        s = f"{value:.3f}"
        if value <= 0.0:
            col = "red"
        elif value < 0.5:
            col = "edufemProc"
        else:
            col = "edufemPost"
        return rf"\textcolor{{{col}}}{{{s}}}"

    def _build_cap_calidad(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Calidad de la malla")
        if self._prose:
            self._chapter_card(
                entra=r"Geometría de los elementos",
                formula=r"q_{SJ},\,R_J,\,\theta_{\min/\max}",
                sale=r"Diagnóstico de validez",
                phase="pre",
            )
            td.educational_teaser(
                r"$q_{SJ}<0$ marca un elemento \textbf{invertido} "
                r"($\det\mathbf{J}<0$): bloquea la solución hasta "
                r"corregirlo. El resto de los valores son grados de "
                r"distorsión tolerables.",
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
        else:
            headers = ["Elem", r"$q_{SJ}$", r"$R_J$", r"$AR$", r"$T_R$",
                       r"$\theta_{min}$", r"$\theta_{max}$", "Estado"]
        col_align = "rrrrrrrl"
        rows = []
        for eid in sorted(results.keys()):
            r = results[eid]
            fourth = (r.get("midside_admissibility") or {}).get("q_D") if is_q9 \
                else r.get("robinson_taper")
            fourth_str = f"{fourth:.3f}" if fourth is not None and \
                np.isfinite(fourth) else "—"
            rows.append([
                str(eid), self._q_sj_colored(r['scaled_jacobian']),
                f"{r['jacobian_ratio']:.3f}", f"{r['robinson_aspect']:.3f}",
                fourth_str, fmt(r["min_angle"], "angle"),
                fmt(r["max_angle"], "angle"), TheoryDoc.escape(r["status"]),
            ])
        self._longtable(headers=headers, rows=rows, col_align=col_align)

    # ------------------------------------------------------------------
    # Capítulo 4: formulación elemental (showcase de UN elemento)
    # ------------------------------------------------------------------

    def _select_showcase_element(self) -> Optional[int]:
        """Elige el elemento estrella: máxima energía de deformación
        U_e = ½·uₑᵀ·kₑ·uₑ. Fallback: argmax ‖kₑ‖_F. None si no hay datos."""
        proj = self._project
        sol = self._solution
        if not proj.elements:
            return None
        elem_data = sol.get("element_data") if sol else None
        if not elem_data:
            return None
        u = sol.get("u")
        best_id, best_score = None, -1.0
        if u is not None:
            u_arr = np.asarray(u)
            for eid, data in elem_data.items():
                ke = data.get("ke")
                dof_idx = data.get("dof_indices")
                if ke is None or dof_idx is None:
                    continue
                try:
                    u_e = u_arr[list(dof_idx)]
                    energy = 0.5 * float(u_e @ ke @ u_e)
                except Exception:
                    continue
                if energy > best_score:
                    best_score, best_id = energy, eid
        if best_id is None:
            for eid, data in elem_data.items():
                ke = data.get("ke")
                if ke is None:
                    continue
                try:
                    score = float(np.linalg.norm(ke, "fro"))
                except Exception:
                    continue
                if score > best_score:
                    best_score, best_id = score, eid
        return best_id

    def _recompute_showcase(self, elem_id: int):
        """Recalcula la formulación COMPLETA del elemento (con todos los
        intermedios J, B, dN, etc.) vía `fem.stiffness.element_stiffness`.

        El element_data del solve productivo usa el kernel JIT y guarda un
        gauss_data mínimo (xi, eta, weight, det_J, B) — sin J ni índice. Para
        el paso-a-paso necesitamos la versión completa, que se recalcula aquí
        solo para este único elemento (costo despreciable).

        Retorna (ke, gauss_data_completo, material, node_coords) o None.
        """
        proj = self._project
        elem = proj.elements.get(elem_id)
        if elem is None:
            return None
        try:
            node_coords = np.array([
                [proj.nodes[nid].x, proj.nodes[nid].y] for nid in elem.node_ids
            ])
        except KeyError:
            return None
        material = proj.materials.get(elem.material_name)
        if material is None and proj.materials:
            material = next(iter(proj.materials.values()))
        if material is None:
            return None
        try:
            from fem.stiffness import element_stiffness
            ke, gauss_data = element_stiffness(
                node_coords, material.E, material.nu, elem.thickness,
                proj.analysis_type, proj.element_type,
            )
        except Exception:
            return None
        return ke, gauss_data, material, node_coords

    # ---------- auto-detección del modo de presentación ----------

    # Umbrales para que el desarrollo paso-a-paso de TODOS los elementos
    # quepa legible en el documento (matrices kₑ, B y K con tamaño razonable):
    #   Q4 ≤ 2 elementos (≤ 12 GDL en K, kₑ de 8×8)
    #   Q9 = 1 elemento  (18 GDL en K, kₑ de 18×18 ya apaisada)
    # Por encima de esos umbrales se desarrolla SÓLO el elemento de mayor
    # energía de deformación y se aclara que los demás se calculan igual.
    _COMPACT_MAX_ELEMENTS_Q4 = 2
    _COMPACT_MAX_ELEMENTS_Q9 = 1

    def _compact_showcase_ids(self) -> Optional[list[int]]:
        """Si el modelo cabe en modo compacto, devuelve la lista ordenada de
        IDs a desarrollar; si no, devuelve None (modo showcase de un solo
        elemento). El criterio depende del tipo de elemento."""
        proj = self._project
        n_elem = len(proj.elements)
        if n_elem == 0:
            return None
        if proj.element_type == ELEMENT_Q9:
            limit = self._COMPACT_MAX_ELEMENTS_Q9
        else:
            limit = self._COMPACT_MAX_ELEMENTS_Q4
        if n_elem > limit:
            return None
        # Verificar que para cada elemento se pueda recomputar el showcase
        # (material asignado, nodos válidos). Si alguno falla, degradar a
        # showcase clásico para no producir un capítulo a medias.
        ids = sorted(proj.elements.keys())
        for eid in ids:
            if self._recompute_showcase(eid) is None:
                return None
        return ids

    def _build_cap_showcase_compact(self, elem_ids: list[int]) -> None:
        """Capítulo de formulación elemental con TODOS los elementos del
        modelo desarrollados paso a paso (modo compacto)."""
        td = self._td
        td.section_numbered("Formulación elemental")
        if self._prose:
            if len(elem_ids) == 1:
                texto_intro = (
                    r"El modelo tiene un único elemento, así que este "
                    r"capítulo desarrolla \emph{paso a paso} su matriz de "
                    r"rigidez siguiendo la cadena clásica de la "
                    r"formulación isoparamétrica: geometría $\to$ "
                    r"$\mathbf{N}$ $\to$ $\mathbf{J}$ $\to$ $\mathbf{B}$ "
                    r"$\to$ $\mathbf{D}$ $\to$ integración de "
                    r"Gauss-Legendre $\to$ $\mathbf{k}_e$."
                )
            else:
                texto_intro = (
                    rf"El modelo tiene \textbf{{{len(elem_ids)} elementos}}, "
                    rf"así que este capítulo desarrolla \emph{{cada uno}} "
                    rf"paso a paso, siguiendo la cadena clásica de la "
                    rf"formulación isoparamétrica: geometría $\to$ "
                    rf"$\mathbf{{N}}$ $\to$ $\mathbf{{J}}$ $\to$ "
                    rf"$\mathbf{{B}}$ $\to$ $\mathbf{{D}}$ $\to$ "
                    rf"integración de Gauss-Legendre $\to$ $\mathbf{{k}}_e$."
                )
            td.para(texto_intro)
        for idx, eid in enumerate(elem_ids):
            td.subsection_numbered(rf"Elemento {eid}")
            # Sólo en el primer elemento mostramos la caja "¿por qué Gauss?";
            # repetirla en los siguientes sería redundante.
            self._develop_element_content(
                eid,
                use_subsections=False,
                show_motivation_box=(idx == 0),
            )

    def _build_cap_showcase(self, elem_id: int) -> None:
        td = self._td
        proj = self._project
        elem = proj.elements.get(elem_id)
        recomputed = self._recompute_showcase(elem_id)
        if elem is None or recomputed is None:
            return
        n_total = len(proj.elements)

        td.section_numbered(rf"Formulación elemental — Elemento {elem_id}")
        if self._prose:
            self._chapter_card(
                entra=r"$\mathbf{X}_e$, $E$, $\nu$, $t$",
                formula=r"\mathbf{k}_e=\!\int\! \mathbf{B}^T\mathbf{D}\mathbf{B}"
                        r"\,|\mathbf{J}|\,t",
                sale=r"Rigidez $\mathbf{k}_e$",
                phase="proc",
            )
            if n_total > 1:
                td.educational_teaser(
                    rf"De los \textbf{{{n_total} elementos}} se desarrolla "
                    rf"el de mayor \textbf{{energía de deformación}} "
                    rf"($U_e=\tfrac12\mathbf{{u}}_e^T\mathbf{{k}}_e"
                    rf"\mathbf{{u}}_e$). Para el resto el procedimiento es "
                    rf"idéntico: solo cambian las coordenadas nodales "
                    rf"$\mathbf{{X}}_e$.",
                    phase="proc",
                )
        elif n_total > 1:
            # Directo: la selección del elemento estrella, como dato seco.
            td.values([
                ("Elemento desarrollado", f"E{elem_id} (máxima energía)"),
                ("Resto del modelo",
                 f"{n_total - 1} elemento(s), mismo procedimiento"),
            ])
        self._develop_element_content(elem_id, use_subsections=True)

    # ---------- desarrollo paso-a-paso de UN elemento (helper) ----------

    def _develop_element_content(
        self, elem_id: int, *, use_subsections: bool,
        show_motivation_box: bool = True,
    ) -> None:
        """Desarrolla paso a paso un elemento (geometría → N → J → B → D →
        integrando → kₑ). Si `use_subsections=True`, cada paso es una
        \\subsection numerada (uso de showcase de un solo elemento). Si es
        False, cada paso usa \\paragraph (modo compacto: varios elementos
        compartiendo un mismo capítulo, sin saturar el TOC).

        `show_motivation_box`: si False, omite la caja pedagógica del paso
        6 (¿Por qué Gauss?). Útil para no repetirla en elementos
        sucesivos del modo compacto."""
        td = self._td
        proj = self._project
        elem = proj.elements.get(elem_id)
        recomputed = self._recompute_showcase(elem_id)
        if elem is None or recomputed is None:
            return
        ke, gauss_data, material, node_coords = recomputed
        n_nodes = node_coords.shape[0]

        def heading(title: str) -> None:
            if use_subsections:
                td.subsection_numbered(title)
            else:
                td.raw(rf"\paragraph{{{title}}}")

        # 1. Geometría — tabla de nodos + matriz de coordenadas X_e (n×2),
        # que es el operando físico del producto J = ∂N·X_e (pasos siguientes).
        heading("Geometría y conectividad del elemento")
        rows = []
        for i, nid in enumerate(elem.node_ids[:n_nodes]):
            x, y = node_coords[i]
            rows.append([f"$N_{{{i+1}}}$", str(nid),
                         fmt(x, "length"), fmt(y, "length")])
        self._longtable(headers=["Nodo local", "Nodo global", r"$X$", r"$Y$"],
                        rows=rows, col_align="ccrr")
        td.values([
            ("Tipo de elemento", TheoryDoc.escape(proj.element_type)),
            ("Cantidad de nodos", str(n_nodes)),
            ("Espesor $t$", fmt(elem.thickness, "length")),
            ("Material", TheoryDoc.escape(elem.material_name)),
        ])
        td.raw(r"{\scriptsize")
        td.matrix(np.asarray(node_coords), name=r"\mathbf{X}_e", fmt="{:.4g}")
        td.raw(r"}")

        gauss_to_show = self._select_gauss_to_display(gauss_data, n_nodes)
        # Cadena matricial por punto de Gauss (mismas funciones que el solver →
        # sustitución bit-a-bit consistente con los módulos M2/M4):
        #   ∂N(ξ,η) → J = ∂N·X_e → J⁻¹ → ∂N/∂x = J⁻¹·∂N → B.
        chain = self._build_pg_chain(gauss_to_show, node_coords,
                                     proj.element_type)
        wide = n_nodes > 4   # Q9: el producto ∂N·X_e desborda en una línea.

        # 2. Funciones de forma N en puntos de Gauss
        heading(r"Funciones de forma $N_i(\xi,\eta)$ en los puntos de Gauss")
        if self._prose:
            td.educational_teaser(
                r"Las mismas $N_i$ interpolan geometría \emph{y} "
                r"desplazamiento ($\mathbf{x}=\sum N_i\mathbf{x}_i$, "
                r"$\mathbf{u}=\sum N_i\mathbf{u}_i$). En los puntos de "
                r"Gauss dan el muestreo que arma la integral.",
                phase="proc",
            )
        if gauss_data:
            self._tabla_N_en_gauss(gauss_data, n_nodes, proj.element_type)
        else:
            td.para(r"\emph{Datos de Gauss no disponibles.}")

        # 3. Jacobiano — operador + reemplazo numérico por punto de Gauss.
        heading(r"Jacobiano $\mathbf{J}=\partial\mathbf{N}\,\mathbf{X}_e$ "
                r"y $\det\mathbf{J}$")
        td.equation(
            r"\mathbf{J}(\xi,\eta)=\frac{\partial(x,y)}{\partial(\xi,\eta)}"
            r"=\partial\mathbf{N}(\xi,\eta)\,\mathbf{X}_e, \qquad "
            r"\det\mathbf{J}=J_{11}J_{22}-J_{12}J_{21}."
        )
        if self._prose:
            td.educational_teaser(
                r"\textbf{$\det\mathbf{J}$ debe ser $>0$ en todo el "
                r"elemento}: si se anula o cambia de signo, está plegado "
                r"y la rigidez no significa nada.",
                phase="proc",
            )
        if len(gauss_to_show) < len(gauss_data):
            td.para(
                rf"\emph{{Por compacidad se muestran {len(gauss_to_show)} "
                rf"de los {len(gauss_data)} puntos de Gauss; el resto "
                rf"sigue el mismo procedimiento.}}"
            )
        for c in chain:
            self._mostrar_jacobiano_sub(c, np.asarray(node_coords), wide=wide)

        # 4. Matriz B — cadena de la regla de la cadena: J⁻¹ → ∂N/∂x → B.
        heading(r"Matriz de deformación $\mathbf{B}$ "
                r"($\partial\mathbf{N}/\partial\mathbf{x}=\mathbf{J}^{-1}"
                r"\partial\mathbf{N}$)")
        td.equation(
            r"\frac{\partial\mathbf{N}}{\partial\mathbf{x}}"
            r"=\mathbf{J}^{-1}\frac{\partial\mathbf{N}}{\partial(\xi,\eta)},"
            r"\qquad \boldsymbol\varepsilon=\mathbf{B}\,\mathbf{u}_e."
        )
        if self._prose:
            td.educational_teaser(
                r"Cada par de columnas $(2i{-}1,2i)$ de $\mathbf{B}$ es el "
                r"nodo $i$: $\partial N_i/\partial x$ y "
                r"$\partial N_i/\partial y$ reordenadas para "
                r"$(\varepsilon_x,\varepsilon_y,\gamma_{xy})$.",
                phase="proc",
            )
        for c in chain:
            self._mostrar_b_sub(c, wide=wide)

        # 5. Constitutiva D
        heading(r"Matriz constitutiva $\mathbf{D}$ del material asignado")
        from fem.constitutive import constitutive_matrix
        D = constitutive_matrix(material.E, material.nu, proj.analysis_type)
        if self._prose:
            td.para(
                rf"Ley de Hooke "
                rf"$\boldsymbol\sigma=\mathbf{{D}}\,\boldsymbol\varepsilon$ "
                rf"para \textbf{{{TheoryDoc.escape(material.name)}}} "
                rf"($E={material.E:g}$, $\nu={material.nu:g}$):"
            )
        td.matrix(D, name=r"\mathbf{D}", fmt="{:.4g}")

        # 6. Integrando simbólico (motivación de Gauss)
        heading(r"Integrando simbólico $K_{ij}(\xi,\eta)$")
        if self._prose and show_motivation_box:
            td.educational_box(
                r"La rigidez elemental es "
                r"$\mathbf{k}_e=\int_{-1}^{1}\!\!\int_{-1}^{1}"
                r"\mathbf{B}^T\mathbf{D}\,\mathbf{B}\,|\det\mathbf{J}|\,t\,"
                r"d\xi\,d\eta$. El integrando contiene $\mathbf{J}^{-1}$ "
                r"dentro de $\mathbf{B}$, lo que introduce $\det\mathbf{J}$ "
                r"en el denominador. En elementos rectos $\det\mathbf{J}$ "
                r"es constante y la integral cierra en forma cerrada, "
                r"pero apenas el elemento se distorsiona el integrando "
                r"se vuelve una expresión \emph{racional} en $(\xi,\eta)$, "
                r"sin primitiva elemental. Por eso se recurre a la "
                r"\textbf{cuadratura de Gauss-Legendre}: aproxima la "
                r"integral por una suma ponderada del integrando evaluado "
                r"en unos pocos puntos óptimamente elegidos.",
                title=r"\textbf{¿Por qué cuadratura numérica y no analítica?}",
                phase="proc",
            )
        if proj.element_type == ELEMENT_Q4 and n_nodes == 4:
            self._integrando_simbolico_q4(elem, node_coords, material)
        else:
            td.para(
                r"\emph{La expansión simbólica del integrando para Q9 "
                r"(matrices $18\times 18$) excede la utilidad didáctica "
                r"del documento. Se muestra sólo la sumatoria numérica "
                r"de Gauss.}"
            )
            td.equation(
                r"\mathbf{k}_e = \int_{-1}^{1}\!\!\int_{-1}^{1}"
                r"\mathbf{B}^T\mathbf{D}\,\mathbf{B}\,|\det\mathbf{J}|\,t\,"
                r"d\xi\,d\eta."
            )

        # 7. Cuadratura -> ke
        heading(r"Cuadratura de Gauss y matriz $\mathbf{k}_e$ resultante")
        if self._prose:
            ng = "4 ($2\\times 2$)" if proj.element_type == ELEMENT_Q4 \
                else "9 ($3\\times 3$)"
            td.para(
                rf"La integral se aproxima sumando la contribución "
                rf"$w_p\,\mathbf{{B}}_p^T\mathbf{{D}}\,\mathbf{{B}}_p\,"
                rf"|\det\mathbf{{J}}_p|\,t$ en cada uno de los {ng} "
                rf"puntos de Gauss:"
            )
        td.equation(
            r"\mathbf{k}_e \approx \sum_p w_p\,\mathbf{B}_p^T\,\mathbf{D}\,"
            r"\mathbf{B}_p\,|\det\mathbf{J}_p|\,t."
        )
        self._mostrar_matriz_ke(ke, name=r"\mathbf{k}_e")
        td.values([
            (r"Energía de deformación $U_e=\tfrac{1}{2}\mathbf{u}_e^T"
             r"\mathbf{k}_e\mathbf{u}_e$",
             self._energia_deformacion_str(elem_id, ke)),
            (r"$\|\mathbf{k}_e\|_F$",
             f"{float(np.linalg.norm(ke, 'fro')):.4g}"),
            (r"Condición $\kappa_2(\mathbf{k}_e)$", self._cond_str(ke)),
        ])

    @staticmethod
    def _select_gauss_to_display(gauss_data: list, n_nodes: int) -> list:
        """Q4 (4 PG): los 4. Q9 (9 PG): 3 representativos (esquina, centro,
        esquina opuesta) — el resto es análogo y satura el documento."""
        if not gauss_data:
            return []
        if n_nodes <= 4:
            return list(gauss_data)
        n = len(gauss_data)
        if n <= 4:
            return list(gauss_data)
        idxs = sorted({0, n // 2, n - 1})
        return [gauss_data[i] for i in idxs if i < n]

    @staticmethod
    def _gp_index(gp: dict, fallback: int) -> int:
        """Índice 1-based de un punto de Gauss, tolerando dicts sin 'index'."""
        return int(gp.get("index", fallback)) + 1

    def _tabla_N_en_gauss(self, gauss_data, n_nodes, element_type) -> None:
        from fem.shape_functions import get_shape_functions
        N_func, _ = get_shape_functions(element_type)
        headers = ["Punto", r"$\xi$", r"$\eta$", r"$w$"] + \
                  [rf"$N_{{{i+1}}}$" for i in range(n_nodes)]
        rows = []
        for k, gp in enumerate(gauss_data):
            xi, eta, w = gp["xi"], gp["eta"], gp["weight"]
            N_vals = N_func(xi, eta)
            row = [f"PG{self._gp_index(gp, k)}", f"{xi:.4f}", f"{eta:.4f}",
                   f"{w:.4f}"] + [f"{float(n):.4f}" for n in N_vals]
            rows.append(row)
        # Q9: 13 columnas desbordan A4 portrait → scriptsize (la tabla es
        # corta, no parte de página, así que el grupo de tamaño es seguro).
        wide = n_nodes > 4
        if wide:
            self._td.raw(r"{\scriptsize")
        self._longtable(headers=headers, rows=rows,
                        col_align="rrrr" + "r" * n_nodes)
        if wide:
            self._td.raw(r"}")

    def _build_pg_chain(self, gauss_to_show, node_coords, element_type):
        """Recalcula la cadena matricial por punto de Gauss con las MISMAS
        funciones del solver (consistencia bit-a-bit con los módulos M2/M4):
        ∂N(ξ,η) → J = ∂N·X_e → J⁻¹ → ∂N/∂x = J⁻¹·∂N → B. Devuelve una lista de
        dicts. Degrada a los valores de `gauss_data` si el recompute falla."""
        from fem.shape_functions import get_shape_functions
        from fem.jacobian import compute_jacobian, compute_dN_physical
        from fem.b_matrix import compute_b_matrix
        _, dN_func = get_shape_functions(element_type)
        Xe = np.ascontiguousarray(np.asarray(node_coords, dtype=float))
        chain = []
        for k, gp in enumerate(gauss_to_show):
            xi, eta = gp["xi"], gp["eta"]
            idx = self._gp_index(gp, k)
            dN_nat = inv_J = dN_phys = None
            try:
                dN_nat = np.ascontiguousarray(
                    np.asarray(dN_func(xi, eta), dtype=float))
                J, det_J, inv_J = compute_jacobian(dN_nat, Xe)
                dN_phys = compute_dN_physical(dN_nat, inv_J)
                B = compute_b_matrix(dN_phys)
            except Exception:
                J = np.asarray(gp.get("J"))
                det_J = float(gp.get("det_J", 0.0))
                B = gp.get("B")
            chain.append({
                "idx": idx, "xi": xi, "eta": eta,
                "dN_nat": dN_nat, "J": np.asarray(J), "det_J": float(det_J),
                "inv_J": inv_J, "dN_phys": dN_phys,
                "B": None if B is None else np.asarray(B),
            })
        return chain

    def _mostrar_jacobiano_sub(self, c: dict, Xe: np.ndarray, *,
                               wide: bool) -> None:
        """Jacobiano con REEMPLAZO matricial en el punto de Gauss:
        Q4 → producto explícito J = ∂N·X_e = [·][·] = [·]; Q9 → ∂N y J
        separados (el triple producto desborda). + det J numérico."""
        td = self._td
        mt = TheoryDoc.matrix_tex
        idx, J, det_J, dN = c["idx"], c["J"], c["det_J"], c["dN_nat"]
        td.raw(rf"\paragraph{{PG{idx} — "
               rf"$(\xi,\eta)=({c['xi']:.4f}, {c['eta']:.4f})$}}")
        if dN is not None and not wide:
            td.raw(r"{\scriptsize")
            td.equation(
                rf"\mathbf{{J}}_{{PG{idx}}} = "
                + mt(dN, fmt="{:.3g}") + r"\," + mt(Xe, fmt="{:.4g}")
                + " = " + mt(J, fmt="{:.4g}")
            )
            td.raw(r"}")
        elif dN is not None:
            td.raw(r"{\scriptsize")
            td.equation(rf"\partial\mathbf{{N}}_{{PG{idx}}} = "
                        + mt(dN, fmt="{:.3g}"))
            td.equation(rf"\mathbf{{J}}_{{PG{idx}}} = "
                        r"\partial\mathbf{N}\,\mathbf{X}_e = "
                        + mt(J, fmt="{:.4g}"))
            td.raw(r"}")
        else:
            td.matrix(J, name=rf"\mathbf{{J}}_{{PG{idx}}}", fmt="{:.4g}")
        j11, j12, j21, j22 = J[0, 0], J[0, 1], J[1, 0], J[1, 1]
        td.equation(
            rf"\det\mathbf{{J}}_{{PG{idx}}} = J_{{11}}J_{{22}}-J_{{12}}J_{{21}}"
            rf" = ({j11:.4g})({j22:.4g})-({j12:.4g})({j21:.4g}) = {det_J:.4g}"
        )
        if det_J <= 0.0:
            td.raw(
                r"\par\noindent\textbf{\textcolor{red}{"
                r"$\det\mathbf{J} \le 0 \Rightarrow$ elemento inválido "
                r"(plegado): la rigidez no es válida.}}\par"
            )

    def _mostrar_b_sub(self, c: dict, *, wide: bool) -> None:
        """Matriz B con REEMPLAZO: J⁻¹ → ∂N/∂x = J⁻¹·∂N → B."""
        td = self._td
        mt = TheoryDoc.matrix_tex
        idx, inv_J, dN_phys, B = c["idx"], c["inv_J"], c["dN_phys"], c["B"]
        td.raw(rf"\paragraph{{PG{idx}}}")
        if inv_J is not None and dN_phys is not None:
            td.raw(r"{\scriptsize")
            td.equation(rf"\mathbf{{J}}^{{-1}}_{{PG{idx}}} = "
                        + mt(np.asarray(inv_J), fmt="{:.4g}"))
            td.equation(
                r"\frac{\partial\mathbf{N}}{\partial\mathbf{x}} = "
                r"\mathbf{J}^{-1}\,\partial\mathbf{N} = "
                + mt(np.asarray(dN_phys), fmt="{:.3g}"))
            td.raw(r"}")
        if B is None:
            return
        B = np.asarray(B)
        if wide:
            # Q9: B es 3×18, desborda A4 portrait incluso en \tiny → apaisado
            # (igual que kₑ 18×18). Cabe holgado en landscape.
            td.package("pdflscape")
            td.raw(r"\begin{landscape}")
            td.raw(r"{\tiny")
            td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}", fmt="{:.3g}")
            td.raw(r"}")
            td.raw(r"\end{landscape}")
        else:
            td.raw(r"{\scriptsize")
            td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}", fmt="{:.4g}")
            td.raw(r"}")

    def _mostrar_matriz_ke(self, ke: np.ndarray, *, name: str) -> None:
        """kₑ con exponente factorizado: Q4 (8×8) portrait scriptsize;
        Q9 (18×18) landscape tiny."""
        td = self._td
        if ke.shape[0] <= 8:
            td.raw(r"{\scriptsize")
            td.matrix_factored(ke, name=name, sig_digits=3)
            td.raw(r"}")
        else:
            td.package("pdflscape")
            td.raw(r"\begin{landscape}")
            td.raw(r"{\tiny")
            td.matrix_factored(ke, name=name, sig_digits=2)
            td.raw(r"}")
            td.raw(r"\end{landscape}")

    def _integrando_simbolico_q4(self, elem, node_coords, material) -> None:
        td = self._td
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
            td.equation(
                r"\mathbf{k}_e=\int_{-1}^{1}\!\!\int_{-1}^{1}"
                r"\mathbf{B}^T(\xi,\eta)\,\mathbf{D}\,\mathbf{B}(\xi,\eta)\,"
                r"|\det\mathbf{J}(\xi,\eta)|\,t\,d\xi\,d\eta"
            )
            if self._prose:
                td.para(
                    r"A modo ilustrativo, la entrada $(1,1)$ del integrando "
                    r"evaluada simbólicamente en $(\xi,\eta)$ es:"
                )
            td.raw(r"{\scriptsize")
            td.equation(rf"K_{{11}}(\xi,\eta) = {latex_expr}")
            td.raw(r"}")
            if self._prose:
                td.para(
                    r"\emph{Las 64 entradas de $\mathbf{k}_e$ se construyen "
                    r"análogamente; por compacidad se muestra solo $K_{11}$.}"
                )
        except Exception as e:
            td.para(rf"\emph{{No se pudo construir el integrando simbólico: "
                    rf"{e}. Se procede con la cuadratura numérica.}}")

    def _energia_deformacion_str(self, elem_id, ke: np.ndarray) -> str:
        sol = self._solution
        u = sol.get("u")
        dof_idx = sol.get("element_data", {}).get(elem_id, {}).get("dof_indices")
        if u is None or dof_idx is None:
            return "—"
        try:
            u_e = np.asarray(u)[list(dof_idx)]
            return f"{0.5 * float(u_e @ ke @ u_e):.4g}"
        except Exception:
            return "—"

    @staticmethod
    def _cond_str(ke: np.ndarray) -> str:
        try:
            return f"{float(np.linalg.cond(ke)):.3e}"
        except Exception:
            return "—"

    # ------------------------------------------------------------------
    # Capítulo 5: ensamblaje
    # ------------------------------------------------------------------

    def _build_cap_ensamblaje(self) -> None:
        td = self._td
        proj = self._project
        sol = self._solution
        td.section_numbered("Ensamblaje del sistema global")
        if self._prose:
            self._chapter_card(
                entra=r"$\mathbf{k}_e$ + cargas externas",
                formula=r"\mathbf{K}\,\mathbf{u}=\mathbf{F}",
                sale=r"Sistema global $\mathbf{K}$, $\mathbf{F}$",
                phase="proc",
            )
            td.educational_teaser(
                r"El ensamblaje es \emph{contabilidad}: cada "
                r"$\mathbf{k}_e$ suma en las filas/columnas que el mapeo "
                r"$\mathbf{LM}$ le asigna. Los GDL compartidos acumulan "
                r"$\Rightarrow$ $\mathbf{K}$ queda dispersa y bandeada; "
                r"el orden no altera el resultado.",
                phase="proc",
            )

        K = sol["K"]
        F = np.asarray(sol["F"])
        n_dof = _K_dimension(K)

        td.subsection_numbered("Mapeo de grados de libertad (LM)")
        if self._prose:
            td.para(
                r"La \textbf{location matrix} $\mathbf{LM}_e$ traduce cada "
                r"GDL local del elemento al GDL global; con ella el "
                r"ensamblaje acumula en su posición:"
            )
        # Ecuación de ensamblaje: SIEMPRE (es procedimiento matricial).
        td.equation(
            r"\mathbf{K}[\mathbf{LM}_e,\mathbf{LM}_e]\,\mathrel{+}=\,"
            r"\mathbf{k}_e, \qquad "
            r"\mathbf{F}[\mathbf{LM}_e]\,\mathrel{+}=\,\mathbf{f}_e."
        )
        td.values([
            ("Cantidad de nodos", str(proj.num_nodes)),
            ("Grados de libertad totales", str(n_dof)),
            (r"Tamaño de $\mathbf{K}$", f"{n_dof} × {n_dof}"),
            (r"Tamaño de $\mathbf{F}$", f"{n_dof} × 1"),
        ])

        td.subsection_numbered(r"Matriz de rigidez global $\mathbf{K}$")
        self._mostrar_matriz_K(K)

        td.subsection_numbered(r"Vector de fuerzas globales $\mathbf{F}$")
        if self._prose:
            td.para(
                r"$\mathbf{F}$ acumula cargas nodales puntuales, fuerzas "
                r"equivalentes de cargas superficiales distribuidas y fuerzas "
                r"másicas (gravedad si está activa):"
            )
        td.raw(r"{\scriptsize")
        td.vector_factored(F, name=r"\mathbf{F}", sig_digits=3, transpose=True)
        td.raw(r"}")
        self._desglose_F(F)

    def _mostrar_matriz_K(self, K) -> None:
        """K literal si es chica; patrón de dispersión (PIL) + stats si no."""
        td = self._td
        n_dof = _K_dimension(K)
        if n_dof <= 12:
            if self._prose:
                td.para(r"Por su tamaño moderado se muestra literal, con el "
                        r"exponente común factorizado:")
            td.raw(r"{\scriptsize")
            td.matrix_factored(_K_to_dense(K), name=r"\mathbf{K}", sig_digits=3)
            td.raw(r"}")
        elif n_dof <= 24:
            if self._prose:
                td.para(r"Se muestra literal en formato apaisado (exponente "
                        r"común factorizado):")
            td.package("pdflscape")
            td.raw(r"\begin{landscape}")
            td.raw(r"{\tiny")
            td.matrix_factored(_K_to_dense(K), name=r"\mathbf{K}", sig_digits=2)
            td.raw(r"}")
            td.raw(r"\end{landscape}")
        else:
            if self._prose:
                td.para(
                    rf"Su dimensión $({n_dof}\times{n_dof})$ excede lo "
                    rf"razonable para una matriz literal. Se muestra el patrón "
                    rf"de entradas no nulas (estructura de banda):"
                )
            try:
                from file_io.figure_export import render_K_sparsity
                img = render_K_sparsity(K)
                path = self._save_figure(img, "K_sparsity")
                if path is not None:
                    td.figure(path,
                              caption=(r"Patrón de no-nulos de $\mathbf{K}$. "
                                       r"La concentración cerca de la "
                                       r"diagonal refleja la estructura de "
                                       r"banda característica del MEF: dos "
                                       r"GDL sólo interactúan si pertenecen "
                                       r"al menos a un elemento común."),
                              label="fig:K_sparsity", width=r"0.6\textwidth")
            except Exception:
                pass
        # Estadísticas (siempre).
        nnz = _K_nnz(K)
        density = nnz / (n_dof * n_dof) if n_dof > 0 else 0.0
        bw = _K_bandwidth(K)
        cond = _K_cond(K)
        rows = [
            (r"Entradas no nulas ($|K_{ij}|>10^{-9}$)", str(nnz)),
            ("Densidad", f"{density * 100:.3f}\\%"),
            (r"Ancho de banda", str(bw)),
        ]
        if cond is not None:
            rows.append((r"$\kappa_2(\mathbf{K})$ (estimado)", f"{cond:.3e}"))
        td.values(rows)

    def _desglose_F(self, F: np.ndarray) -> None:
        proj = self._project
        f_nodal_x = sum(ld.fx for ld in proj.nodal_loads.values())
        f_nodal_y = sum(ld.fy for ld in proj.nodal_loads.values())
        ftot_x = float(np.sum(F[0::2]))
        ftot_y = float(np.sum(F[1::2]))
        f_otros_x = ftot_x - f_nodal_x
        f_otros_y = ftot_y - f_nodal_y
        rows = [
            ["Cargas nodales puntuales", fmt(f_nodal_x, "force"),
             fmt(f_nodal_y, "force")],
            ["Otras (superficiales + másicas)", fmt(f_otros_x, "force"),
             fmt(f_otros_y, "force")],
            [r"\textbf{Suma global $\mathbf{F}$}",
             rf"\textbf{{{fmt(ftot_x, 'force')}}}",
             rf"\textbf{{{fmt(ftot_y, 'force')}}}"],
        ]
        self._longtable(headers=["Fuente", r"$\sum F_x$", r"$\sum F_y$"],
                        rows=rows, col_align="lrr")

    # ------------------------------------------------------------------
    # Capítulo 6: restricciones + solución (fusionado)
    # ------------------------------------------------------------------

    def _build_cap_bcs_solucion(self) -> None:
        td = self._td
        sol = self._solution
        td.section_numbered("Condiciones de contorno y solución")

        if self._prose:
            self._chapter_card(
                entra=r"$\mathbf{K}$, $\mathbf{F}$ + restricciones",
                formula=r"\mathbf{K}_{ff}\,\mathbf{u}_f=\mathbf{F}_f",
                sale=r"Desplazamientos $\mathbf{u}$, reacciones $\mathbf{R}$",
                phase="proc",
            )
            td.para(
                r"Las condiciones de contorno esenciales prescriben el "
                r"valor de ciertos GDL (típicamente $u=0$ en apoyos "
                r"perfectos). Separando los GDL libres ($f$) de los "
                r"restringidos ($r$), el sistema global se particiona:"
            )
        # Partición + sistema reducido: ecuaciones SIEMPRE (procedimiento).
        td.equation(
            r"\begin{bmatrix}\mathbf{K}_{ff}&\mathbf{K}_{fr}\\"
            r"\mathbf{K}_{rf}&\mathbf{K}_{rr}\end{bmatrix}"
            r"\begin{bmatrix}\mathbf{u}_f\\\mathbf{u}_r\end{bmatrix}="
            r"\begin{bmatrix}\mathbf{F}_f\\\mathbf{F}_r\end{bmatrix},"
            r"\qquad "
            r"\mathbf{K}_{ff}\,\mathbf{u}_f = \mathbf{F}_f - "
            r"\mathbf{K}_{fr}\,\mathbf{u}_r."
        )
        if self._prose:
            td.educational_teaser(
                r"Eliminar los GDL restringidos restaura la "
                r"definida-positividad de $\mathbf{K}_{ff}$: sin "
                r"restricciones $\mathbf{K}$ es singular por los 3 modos "
                r"de cuerpo rígido del plano. Si un apoyo prescribe un "
                r"desplazamiento $\neq 0$, el término "
                r"$\mathbf{K}_{fr}\,\mathbf{u}_r$ actúa como fuerza "
                r"equivalente (condensación estática).",
                phase="proc",
            )

        self._valores_sistema_reducido()

        td.subsection_numbered("Método de resolución (factorización LU directa)")
        if self._prose:
            td.para(
                r"$\mathbf{K}_{ff}$ se descompone como "
                r"$\mathbf{K}_{ff}=\mathbf{L}\,\mathbf{U}$ y los "
                r"desplazamientos salen en cascada por dos sistemas "
                r"triangulares:"
            )
        # Ecuación LU: SIEMPRE (procedimiento matricial).
        td.equation(
            r"\mathbf{L}\,\mathbf{y} = \mathbf{F}_f - "
            r"\mathbf{K}_{fr}\,\mathbf{u}_r, \qquad "
            r"\mathbf{U}\,\mathbf{u}_f = \mathbf{y}."
        )
        if self._prose:
            td.educational_teaser(
                r"\textbf{Síntomas de un sistema mal planteado}: si "
                r"$\mathbf{K}_{ff}$ es singular o mal condicionada "
                r"(BCs insuficientes, elemento invertido, $E$ o $\nu$ "
                r"fuera de rango físico), $\mathbf{u}$ trae NaN/Inf o "
                r"valores absurdos — revisar el modelo antes de creer "
                r"las tensiones.",
                phase="proc",
            )

        # Desplazamientos
        td.subsection_numbered("Vector de desplazamientos nodales")
        if self._prose:
            td.para(
                r"$\mathbf{u}$ contiene un par $(u_x,u_y)$ por nodo. Se "
                r"presenta primero en forma compacta (con un factor común "
                r"de escala) y luego desagregado nodo por nodo en una "
                r"tabla con la magnitud $|u|=\sqrt{u_x^{\,2}+u_y^{\,2}}$:"
            )
        u = sol["u"]
        td.raw(r"{\scriptsize")
        td.vector_factored(np.asarray(u), name=r"\mathbf{u}", sig_digits=3,
                           transpose=True)
        td.raw(r"}")
        self._tabla_desplazamientos(u)

        # Reacciones
        td.subsection_numbered("Reacciones en los apoyos")
        if self._prose:
            td.para(
                r"Las reacciones se obtienen como $\mathbf{R}=\mathbf{K}\,"
                r"\mathbf{u}-\mathbf{F}$ y son no nulas solo en los GDL "
                r"restringidos:"
            )
        R = sol["reactions"]
        td.raw(r"{\scriptsize")
        td.vector_factored(np.asarray(R), name=r"\mathbf{R}", sig_digits=3,
                           transpose=True)
        td.raw(r"}")
        self._tabla_reacciones(R)

        # Equilibrio
        td.subsection_numbered("Verificación de equilibrio global")
        if self._prose:
            td.para(
                r"$\sum\mathbf{F}_{ext}+\sum\mathbf{R}=\mathbf{0}$ debe "
                r"cumplirse en cada dirección. Un residuo grande relativo a "
                r"las cargas indicaría mal condicionamiento o BCs "
                r"inconsistentes. Es un control de calidad barato — hacerlo "
                r"siempre antes de creer las tensiones."
            )
        self._tabla_verificacion_equilibrio(R)

    def _valores_sistema_reducido(self) -> None:
        sol = self._solution
        n_total = len(sol["u"])
        n_libres = len(sol["free_dofs"])
        n_restr = len(sol["restrained_dofs"])
        self._td.values([
            ("Grados de libertad totales", str(n_total)),
            ("Grados de libertad restringidos", str(n_restr)),
            ("Grados de libertad libres (resueltos)", str(n_libres)),
            (r"Tamaño de $\mathbf{K}_{red}$", f"{n_libres} × {n_libres}"),
        ])

    def _tabla_desplazamientos(self, u) -> None:
        proj = self._project
        idx_map = proj.node_index_map
        u = np.asarray(u)
        rows = []
        for nid in sorted(proj.nodes.keys()):
            base = 2 * idx_map[nid]
            ux, uy = float(u[base]), float(u[base + 1])
            umag = float(np.hypot(ux, uy))
            rows.append([str(nid), f"{ux:.5e}", f"{uy:.5e}", f"{umag:.5e}"])
        self._longtable(headers=["Nodo", r"$u_x$", r"$u_y$", r"$|u|$"],
                        rows=rows, col_align="rrrr")

    def _tabla_reacciones(self, R) -> None:
        proj = self._project
        if not proj.boundary_conditions:
            self._td.para(r"\emph{Sin reacciones (no hay restricciones).}")
            return
        idx_map = proj.node_index_map
        R = np.asarray(R)
        rows = []
        sum_rx = sum_ry = 0.0
        for nid in sorted(proj.boundary_conditions.keys()):
            bc = proj.boundary_conditions[nid]
            base = 2 * idx_map[nid]
            rx = float(R[base]) if bc.restrain_x else 0.0
            ry = float(R[base + 1]) if bc.restrain_y else 0.0
            sum_rx += rx
            sum_ry += ry
            rows.append([str(nid), fmt(rx, "force"), fmt(ry, "force")])
        rows.append([r"\textbf{Suma}", rf"\textbf{{{fmt(sum_rx, 'force')}}}",
                     rf"\textbf{{{fmt(sum_ry, 'force')}}}"])
        self._longtable(headers=["Nodo", r"$R_x$", r"$R_y$"], rows=rows,
                        col_align="rrr")

    def _tabla_verificacion_equilibrio(self, R) -> None:
        proj = self._project
        R = np.asarray(R)
        Fx_aplicada = sum(ld.fx for ld in proj.nodal_loads.values())
        Fy_aplicada = sum(ld.fy for ld in proj.nodal_loads.values())
        idx_map = proj.node_index_map
        Rx_total = Ry_total = 0.0
        for nid, bc in proj.boundary_conditions.items():
            base = 2 * idx_map[nid]
            if bc.restrain_x:
                Rx_total += float(R[base])
            if bc.restrain_y:
                Ry_total += float(R[base + 1])
        rows = [
            ["X", fmt(Fx_aplicada, "force"), fmt(Rx_total, "force"),
             f"{Fx_aplicada + Rx_total:.3e}"],
            ["Y", fmt(Fy_aplicada, "force"), fmt(Ry_total, "force"),
             f"{Fy_aplicada + Ry_total:.3e}"],
        ]
        self._longtable(headers=["Dirección", "Cargas aplicadas", "Reacciones",
                                 "Residuo"], rows=rows, col_align="crrr")

    # ------------------------------------------------------------------
    # Capítulo 7: post-proceso
    # ------------------------------------------------------------------

    def _build_cap_postproceso(self, showcase_id: Optional[int]) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Post-proceso: tensiones y deformada")

        if self._prose:
            self._chapter_card(
                entra=r"Desplazamientos $\mathbf{u}$",
                formula=r"\boldsymbol\sigma=\mathbf{D}\,\mathbf{B}\,\mathbf{u}_e",
                sale=r"$\sigma_1,\sigma_2,\sigma_{VM}$ + contornos",
                phase="post",
            )
            td.para(
                r"El post-proceso transforma los desplazamientos nodales "
                r"$\mathbf{u}$ — la única incógnita directa del MEF — en "
                r"las magnitudes con las que un ingeniero juzga el diseño:"
            )
        # Cadena de cálculo: ecuación SIEMPRE (es el mapa del post-proceso).
        td.equation(
            r"\mathbf{u}\;\to\;\boldsymbol\varepsilon_{Gauss}\;\to\;"
            r"\boldsymbol\sigma_{Gauss}\;\to\;\boldsymbol\sigma_{nodo}\;\to\;"
            r"\boldsymbol\sigma_{prom}\;\to\;(\sigma_1,\sigma_2,\sigma_{VM})."
        )

        td.subsection_numbered("Tensiones en los puntos de Gauss")
        if self._prose:
            td.educational_teaser(
                r"Las tensiones se evalúan en los puntos de Gauss "
                r"\emph{(y no en los nodos)} por la superconvergencia de "
                r"Barlow: ahí ganan un orden de precisión.",
                phase="post",
            )
        # Reconstrucción ε→σ en PGs: ecuación SIEMPRE.
        td.equation(
            r"\boldsymbol\varepsilon(\xi_p,\eta_p)=\mathbf{B}(\xi_p,\eta_p)\,"
            r"\mathbf{u}_e, \qquad "
            r"\boldsymbol\sigma(\xi_p,\eta_p)=\mathbf{D}\,"
            r"\boldsymbol\varepsilon(\xi_p,\eta_p)."
        )
        # Tabla de tensiones por punto de Gauss: AMBOS estilos (verificación
        # de valores crudos, previa al promediado).
        if self._element_stresses:
            self._tabla_gauss_stresses_completos()

        td.subsection_numbered("Extrapolación de Gauss a nodos")
        if self._prose:
            td.para(
                r"Los valores en los puntos de Gauss se llevan a los nodos "
                r"con una matriz de extrapolación $\mathbf{E}$ = inversa de "
                r"las funciones de forma evaluadas en los puntos de Gauss:"
            )
        # Extrapolación: ecuación SIEMPRE.
        td.equation(
            r"(\mathbf{N}_p)_{ji} = N_i(\xi_p,\eta_p), \qquad "
            r"\boldsymbol\sigma^{\,nodo} = \mathbf{E}\,"
            r"\boldsymbol\sigma^{\,Gauss}, \qquad "
            r"\mathbf{E} = \mathbf{N}_p^{-1}."
        )
        is_q9 = proj.element_type == ELEMENT_Q9
        if not is_q9:
            if self._prose:
                td.para(r"Para Q4 (puntos de Gauss en $\pm 1/\sqrt{3}$), la "
                        r"matriz cerrada con $s=\sqrt{3}$ es:")
            s = np.sqrt(3.0)
            E_q4 = 0.25 * np.array([
                [(1 + s) * (1 + s), (1 - s) * (1 + s), (1 - s) * (1 - s),
                 (1 + s) * (1 - s)],
                [(1 + s) * (1 - s), (1 - s) * (1 - s), (1 - s) * (1 + s),
                 (1 + s) * (1 + s)],
                [(1 - s) * (1 - s), (1 + s) * (1 - s), (1 + s) * (1 + s),
                 (1 - s) * (1 + s)],
                [(1 - s) * (1 + s), (1 + s) * (1 + s), (1 + s) * (1 - s),
                 (1 - s) * (1 - s)],
            ])
            td.matrix(E_q4, name=r"\mathbf{E}_{Q4}", fmt="{:.4f}")
        elif self._prose:
            td.para(
                r"Para Q9 ($3\times 3$ puntos de Gauss) no existe forma "
                r"cerrada simple: $\mathbf{E}_{Q9}$ es la inversa numérica "
                r"de la matriz $9\times 9$ de funciones de forma evaluadas "
                r"en los 9 puntos de Gauss. Es la misma matriz para todos "
                r"los elementos Q9, independiente de su geometría física."
            )

        td.subsection_numbered("Promediado nodal entre elementos adyacentes")
        if self._prose:
            td.para(
                r"Un nodo compartido por $k$ elementos recibe $k$ valores "
                r"extrapolados distintos (las tensiones MEF son discontinuas "
                r"entre elementos). EduFEM asigna el promedio aritmético:"
            )
        # Promediado: ecuación SIEMPRE.
        td.equation(
            r"\sigma_n^{\,prom}=\frac{1}{k_n}\sum_{e\in\mathcal{E}_n}"
            r"\sigma_n^{\,(e)}")
        if self._prose:
            # Una de las DOS únicas cajas "¿por qué?" de todo el documento.
            td.educational_box(
                r"\textbf{El salto antes del promediado es un indicador de "
                r"error de malla.} Si las $k$ contribuciones a un mismo nodo "
                r"difieren mucho, la malla no captura el gradiente local; "
                r"refinar allí debería reducir el salto.",
                title=r"\textbf{¿Por qué importa el promediado?}",
                phase="post",
            )

        td.subsection_numbered(
            r"Tensiones principales $\sigma_1$, $\sigma_2$ y $\theta_p$")
        if self._prose:
            td.para(
                r"$\sigma_1\geq\sigma_2$ son los autovalores del tensor "
                r"de tensiones 2D: las tensiones normales máxima y "
                r"mínima sobre los planos donde el corte se anula. Se "
                r"recalculan a partir de las componentes ya promediadas "
                r"(promediar las principales directamente daría valores "
                r"incorrectos: no son funciones lineales de las "
                r"componentes):"
            )
        td.equation(
            r"\sigma_{1,2}=\frac{\sigma_x+\sigma_y}{2}\pm\sqrt{\left("
            r"\frac{\sigma_x-\sigma_y}{2}\right)^2+\tau_{xy}^{\,2}}, \qquad "
            r"\tan(2\theta_p)=\frac{2\tau_{xy}}{\sigma_x-\sigma_y}"
        )

        td.subsection_numbered(
            r"Tensión equivalente de von Mises $\sigma_{VM}$")
        if self._prose:
            td.para(
                r"Convierte el estado tensional 2D en un escalar comparable "
                r"contra la fluencia uniaxial del material:"
            )
        td.equation(
            r"\sigma_{VM}=\sqrt{\sigma_x^{\,2}-\sigma_x\sigma_y+\sigma_y^{\,2}"
            r"+3\tau_{xy}^{\,2}}=\sqrt{\sigma_1^{\,2}-\sigma_1\sigma_2"
            r"+\sigma_2^{\,2}}"
        )

        td.subsection_numbered("Tensiones nodales (promediadas)")
        if self._prose:
            td.para(
                r"Aplicando la cadena anterior a cada elemento se obtiene la "
                r"tabla siguiente, insumo de los contornos."
            )
        if self._nodal_stresses:
            self._tabla_nodal_stresses()
        else:
            td.para(r"\emph{Tensiones nodales no disponibles.}")

        # Deformada (PIL)
        td.subsection_numbered("Configuración deformada")
        deformed_img = self._contour_figures.get("deformed")
        if deformed_img is None:
            try:
                from file_io.figure_export import render_deformed
                deformed_img = render_deformed(proj, self._solution)
            except Exception:
                deformed_img = None
        path = self._save_figure(deformed_img, "deformed")
        if path is not None:
            td.figure(path,
                      caption=("Configuración deformada (escala automática). "
                               "Malla original en gris, deformada en verde."),
                      label="fig:deformed", width=r"0.82\textwidth")

        # Contornos
        td.subsection_numbered("Mapas de contornos de tensiones")
        if self._prose:
            td.para(
                r"Los contornos se dibujan con un gradiente bilineal sobre "
                r"cada elemento, a partir de los valores nodales "
                r"promediados. Convención de mapa: \emph{coolwarm} "
                r"(divergente) para $\sigma_x$, $\sigma_y$, $\tau_{xy}$ "
                r"— donde el cero separa tracción de compresión — y "
                r"\emph{viridis} (secuencial) para $\sigma_{VM}$, que es "
                r"no negativo."
            )
        for component in ("sigma_x", "sigma_y", "tau_xy", "von_mises"):
            self._insertar_contorno(component)

        # Cruces principales (PIL)
        if self._nodal_stresses:
            td.subsection_numbered("Direcciones principales sobre la malla")
            try:
                from file_io.figure_export import render_principal_crosses
                img = render_principal_crosses(proj, self._nodal_stresses)
                path = self._save_figure(img, "principal_crosses")
                if path is not None:
                    td.figure(
                        path,
                        caption=("Cruces principales por elemento: brazo largo "
                                 "= $\\sigma_1$, brazo corto perpendicular = "
                                 "$\\sigma_2$. Azul = tracción, rojo = "
                                 "compresión."),
                        label="fig:principal_crosses", width=r"0.8\textwidth")
            except Exception:
                pass

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
            rows=rows, col_align="rrrrrrr")

    def _insertar_contorno(self, component: str) -> None:
        td = self._td
        img = self._contour_figures.get(component)
        if img is None:
            try:
                from file_io.figure_export import render_contour
                img = render_contour(self._project, self._solution,
                                     self._nodal_stresses, component)
            except Exception:
                img = None
        path = self._save_figure(img, f"contour_{component}")
        if path is None:
            return
        labels = {
            "sigma_x": r"$\sigma_x$", "sigma_y": r"$\sigma_y$",
            "tau_xy": r"$\tau_{xy}$", "von_mises": r"$\sigma_{VM}$ (von Mises)",
        }
        td.figure(path,
                  caption=f"Contorno de {labels.get(component, component)} "
                          f"(valores nodales promediados).",
                  label=f"fig:contour_{component}", width=r"0.82\textwidth")

    # ------------------------------------------------------------------
    # Tensiones por punto de Gauss (post-proceso, ambos estilos)
    # ------------------------------------------------------------------

    def _tabla_gauss_stresses_completos(self) -> None:
        rows = []
        for eid in sorted(self._element_stresses.keys()):
            es = self._element_stresses[eid]
            for gp_idx, gs in enumerate(es.get("gauss_stresses", []), start=1):
                rows.append([
                    str(eid), f"PG{gp_idx}",
                    fmt(gs.get("sigma_x", 0.0), "stress"),
                    fmt(gs.get("sigma_y", 0.0), "stress"),
                    fmt(gs.get("tau_xy", 0.0), "stress"),
                    fmt(gs.get("sigma_1", 0.0), "stress"),
                    fmt(gs.get("sigma_2", 0.0), "stress"),
                    fmt(gs.get("von_mises", 0.0), "stress"),
                ])
        if not rows:
            self._td.para(r"\emph{Sin tensiones por punto de Gauss.}")
            return
        self._longtable(
            headers=["Elem", "PG", r"$\sigma_x$", r"$\sigma_y$", r"$\tau_{xy}$",
                     r"$\sigma_1$", r"$\sigma_2$", r"$\sigma_{VM}$"],
            rows=rows, col_align="ccrrrrrr")

    # ------------------------------------------------------------------
    # Glosario de símbolos (subsección final, solo educativo)
    # ------------------------------------------------------------------

    def _build_glosario(self) -> None:
        td = self._td
        td.section_numbered("Glosario de símbolos y términos")
        glosario = [
            (r"$\mathbf{u}$", "Vector de desplazamientos nodales globales "
                              "(2 entradas por nodo: $u_x$, $u_y$)."),
            (r"$\mathbf{F}$", "Vector de fuerzas nodales globales."),
            (r"$\mathbf{K}$", "Matriz de rigidez global. Simétrica, dispersa, "
                              "definida positiva tras aplicar restricciones."),
            (r"$\mathbf{R}$", "Vector de reacciones en GDL restringidos "
                              "($\\mathbf{K}\\,\\mathbf{u}-\\mathbf{F}$)."),
            (r"$\xi,\eta$", "Coordenadas naturales del elemento maestro "
                            "($[-1,1]^2$)."),
            (r"$N_i$", "Funciones de forma (isoparamétricas: interpolan "
                       "geometría y desplazamientos)."),
            (r"$\mathbf{J}$", "Jacobiano del mapeo natural→físico. Requiere "
                              "$\\det\\mathbf{J}>0$."),
            (r"$\mathbf{B}$", "Matriz deformación–desplazamiento "
                              "($\\boldsymbol{\\varepsilon}="
                              "\\mathbf{B}\\,\\mathbf{u}_e$)."),
            (r"$\mathbf{D}$", "Matriz constitutiva del material (ley de Hooke)."),
            (r"$\mathbf{k}_e$", "Rigidez elemental por cuadratura de Gauss."),
            (r"$\sigma_1,\sigma_2$", "Tensiones principales "
                                     "($\\sigma_1\\geq\\sigma_2$)."),
            (r"$\sigma_{VM}$", "Tensión equivalente de von Mises."),
            ("GDL", "Grado de libertad (2 por nodo en 2D)."),
            ("Q4 / Q9", "Cuadriláteros de 4 / 9 nodos (bilineal / "
                        "bicuadrático)."),
            ("Punto de Gauss", "Lugar de cuadratura; tensión superconvergente "
                               "(Barlow 1976)."),
        ]
        self._longtable(headers=["Símbolo / término", "Significado"],
                        rows=[[k, v] for k, v in glosario],
                        col_align="lp{10cm}")

    # ------------------------------------------------------------------
    # Pie + helper de tablas
    # ------------------------------------------------------------------

    def _build_pie(self) -> None:
        td = self._td
        td.raw(r"\vfill")
        td.raw(r"\begin{center}\rule{0.4\textwidth}{0.4pt}\end{center}")
        td.para(rf"\emph{{Documento generado por {TheoryDoc.escape(APP_NAME)} "
                rf"v{APP_VERSION}.}}")

    def _longtable(self, *, headers: list[str], rows: list[list[str]],
                   col_align: str) -> None:
        td = self._td
        td.package("longtable")
        td.package("booktabs")
        n_cols = len(headers)
        if any(len(r) != n_cols for r in rows):
            raise ValueError(
                f"longtable: filas con columnas inconsistentes (esperado "
                f"{n_cols}).")
        if len(col_align) != n_cols:
            col_align = "l" * n_cols
        head_row = " & ".join(rf"\textbf{{{h}}}" for h in headers) + r" \\"
        td.raw(r"\begin{center}")
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
