"""
Memoria de Cálculo: generador de PDF educativo paso-a-paso del análisis MEF.

Compila un documento LaTeX (vía pylatex + pdflatex) que describe EXACTAMENTE
el pipeline implementado en `fem/` para el proyecto resuelto: planteo del
problema, discretización, calidad de malla, formulación elemental detallada
(N → J → B → D → kₑ por cuadratura de Gauss), ensamblaje disperso, aplicación
de restricciones por eliminación, resolución con `scipy.sparse.linalg.spsolve`
(factorización LU dispersa), reacciones, verificación de equilibrio y
post-proceso (tensiones en puntos de Gauss → extrapolación M⁻¹ → promediado
nodal → principales / von Mises) con contornos renderizados al estilo del
MeshCanvas del Post-Proceso.

Reformulación 2026-05 (ver CLAUDE.md §Memoria de Cálculo):
  - Toda afirmación está verificada contra el código de `fem/`. En particular
    el solver es spsolve (LU dispersa), NO Cholesky; el indexado de GDL es
    ordinal vía `node_index_map` (soporta IDs no contiguos), NO 2·(id−1).
  - Las figuras de campo se dibujan con Pillow (file_io.figure_export), no con
    matplotlib, replicando el estilo del canvas con fondo blanco.
  - Sin referencias cruzadas circulares al Hub ni glosario duplicado en cada
    estilo. Los positivos en matrices/vectores no llevan prefijo '+'.
  - El invariante histórico "style=completo bit-a-bit idéntico" ya NO aplica.

Estilos (`MemoriaCalculo.STYLES`):
  - 'educativo' (default recomendado): narrativa completa y autocontenida del
    procedimiento + figuras + cajas "¿por qué?". Sin apéndices de volcado.
  - 'completo': el documento 'educativo' + apéndices (kₑ de todos los
    elementos, datos completos, glosario). Documento de archivo.
  - 'directo': solo tablas de datos, matrices (D, kₑ, K, F, u, R) y contornos.
    Sin párrafos narrativos.
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
    style : 'educativo' (default), 'completo' o 'directo'.
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
    STYLES = ("educativo", "completo", "directo")

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

    # ¿Incluir narrativa (párrafos, cajas pedagógicas)?
    @property
    def _prose(self) -> bool:
        return self._style in ("educativo", "completo")

    # ¿Incluir apéndices de volcado (kₑ de todos, datos completos, glosario)?
    @property
    def _appendices(self) -> bool:
        return self._style == "completo"

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

    def build(self) -> None:
        """Llena el documento según self._style."""
        if self._style == "directo":
            self._build_directo()
        else:
            self._build_narrativo()

    # ------------------------------------------------------------------
    # Pipeline narrativo (educativo / completo)
    # ------------------------------------------------------------------

    def _build_narrativo(self) -> None:
        self._build_cover()
        self._td.toc()
        self._build_intro()
        self._build_resumen_visual()
        self._build_cap_problema()
        self._build_cap_discretizacion()
        self._build_cap_calidad()
        showcase_id = self._select_showcase_element()
        if showcase_id is not None:
            self._build_cap_showcase(showcase_id)
        self._build_cap_ensamblaje()
        self._build_cap_bcs_solucion()
        self._build_cap_postproceso(showcase_id)
        if self._appendices:
            self._td.raw(r"\appendix")
            self._build_appendix_a_kes(showcase_id)
            self._build_appendix_b_datos()
            self._build_appendix_c_glosario()
        self._build_pie()

    # ------------------------------------------------------------------
    # Pipeline directo (solo datos + matrices + contornos)
    # ------------------------------------------------------------------

    def _build_directo(self) -> None:
        td = self._td
        self._build_cover()
        td.toc()

        td.section_numbered("Datos del modelo")
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

        td.section_numbered(r"Matriz constitutiva $\mathbf{D}$")
        self._matriz_D_teorica()
        self._matriz_D_numerica_si_unico_material()

        showcase_id = self._select_showcase_element()
        if showcase_id is not None:
            self._build_showcase_directo(showcase_id)

        self._build_sistema_global_directo()

        td.section_numbered("Condiciones de contorno y solución")
        self._valores_sistema_reducido()
        u = self._solution["u"]
        R = self._solution["reactions"]
        td.subsection_numbered("Desplazamientos")
        td.raw(r"{\scriptsize")
        td.vector_factored(np.asarray(u), name=r"\mathbf{u}", sig_digits=3,
                           transpose=True)
        td.raw(r"}")
        self._tabla_desplazamientos(u)
        td.subsection_numbered("Reacciones")
        td.raw(r"{\scriptsize")
        td.vector_factored(np.asarray(R), name=r"\mathbf{R}", sig_digits=3,
                           transpose=True)
        td.raw(r"}")
        self._tabla_reacciones(R)
        td.subsection_numbered("Equilibrio global")
        self._tabla_verificacion_equilibrio(R)

        td.section_numbered("Post-proceso")
        td.subsection_numbered("Tensiones nodales (promediadas)")
        if self._nodal_stresses:
            self._tabla_nodal_stresses()
        else:
            td.para(r"\emph{Tensiones nodales no disponibles.}")
        td.subsection_numbered("Contornos de tensiones")
        for component in ("sigma_x", "sigma_y", "tau_xy", "von_mises"):
            self._insertar_contorno(component)
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
                r"\emph{Este documento describe paso a paso el análisis MEF "
                r"realizado por EduFEM sobre este proyecto. Cada capítulo "
                r"combina el planteo con los valores numéricos concretos, "
                r"reproduciendo exactamente el procedimiento que ejecuta el "
                r"motor de cálculo del software — no un método genérico de "
                r"libro, sino el pipeline implementado en su código.}"
            )
        td.raw(r"\newpage")

    def _build_intro(self) -> None:
        td = self._td
        td.raw(r"\section*{¿Qué resuelve el MEF y cómo?}")
        td.raw(r"\addcontentsline{toc}{section}{¿Qué resuelve el MEF y cómo?}")
        td.para(
            r"El \textbf{Método de los Elementos Finitos (MEF)} discretiza un "
            r"problema elástico continuo en $N$ elementos: las incógnitas "
            r"pasan de un campo $\mathbf{u}(x,y)$ infinito-dimensional a un "
            r"vector $\mathbf{u}$ de $2\,N_{nodos}$ entradas (dos GDL por "
            r"nodo en 2D), y el equilibrio se reduce al sistema algebraico "
            r"$\mathbf{K}\,\mathbf{u} = \mathbf{F}$."
        )
        td.para(r"El cálculo de EduFEM sigue esta secuencia:")
        td.raw(r"\begin{enumerate}")
        td.raw(r"\item \textbf{Pre-proceso} — material(es), nodos, "
               r"conectividad, cargas, restricciones; auditoría de calidad "
               r"de la malla.")
        td.raw(r"\item \textbf{Formulación elemental} — para cada elemento: "
               r"funciones de forma $\mathbf{N}$, Jacobiano $\mathbf{J}$, "
               r"matriz $\mathbf{B}$, constitutiva $\mathbf{D}$ y rigidez "
               r"$\mathbf{k}_e$ por cuadratura de Gauss.")
        td.raw(r"\item \textbf{Ensamblaje} — las $\mathbf{k}_e$ y las cargas "
               r"se acumulan en $\mathbf{K}$ (matriz dispersa) y $\mathbf{F}$.")
        td.raw(r"\item \textbf{Restricciones + solución} — se eliminan los "
               r"GDL prescritos y se resuelve el sistema reducido.")
        td.raw(r"\item \textbf{Post-proceso} — desplazamientos, reacciones, "
               r"tensiones y contornos.")
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

        if self._prose:
            td.subsection_numbered("Hipótesis del análisis")
            td.para(self._narrativa_caso_plano())
            td.educational_teaser(
                r"Tensión plana = placas delgadas cargadas en su plano; "
                r"deformación plana = sólidos prismáticos largos. Elegir mal "
                r"no rompe el cálculo: resuelve otro problema con otra "
                r"$\mathbf{D}$.",
                phase="pre",
            )
        self._matriz_D_teorica()
        self._matriz_D_numerica_si_unico_material()

        if self._prose:
            td.subsection_numbered("Tipo de elemento finito")
            if proj.element_type == ELEMENT_Q4:
                td.para(
                    r"Se utiliza el cuadrilátero isoparamétrico de "
                    r"\textbf{4 nodos} (Q4). Las funciones de forma en "
                    r"coordenadas naturales $(\xi,\eta)\in[-1,1]^2$ son "
                    r"bilineales:"
                )
                td.equation(
                    r"N_i(\xi,\eta)=\tfrac{1}{4}(1+\xi_i\xi)(1+\eta_i\eta), "
                    r"\quad i=1,\dots,4"
                )
                td.para(
                    r"con $(\xi_i,\eta_i)$ las coordenadas naturales del nodo "
                    r"$i$. La rigidez se integra con cuadratura de Gauss "
                    r"$2\times 2$ (4 puntos), y las tensiones se evalúan en "
                    r"esos mismos 4 puntos."
                )
            else:
                td.para(
                    r"Se utiliza el cuadrilátero isoparamétrico de "
                    r"\textbf{9 nodos} (Q9, lagrangiano). Las funciones de "
                    r"forma en $(\xi,\eta)\in[-1,1]^2$ son productos tensoriales "
                    r"de polinomios de Lagrange cuadráticos:"
                )
                td.equation(
                    r"N_i(\xi,\eta)=L_a(\xi)\,L_b(\eta), \quad i=1,\dots,9"
                )
                td.para(
                    r"La rigidez se integra con cuadratura de Gauss "
                    r"$3\times 3$ (9 puntos), y las tensiones se evalúan en "
                    r"esos mismos 9 puntos."
                )

    def _narrativa_caso_plano(self) -> str:
        if self._project.analysis_type == ANALYSIS_PLANE_STRESS:
            return (
                r"El problema se resuelve bajo \textbf{tensión plana} "
                r"($\sigma_z=\tau_{xz}=\tau_{yz}=0$), válida para cuerpos "
                r"delgados cargados en su plano medio. La deformación fuera "
                r"del plano $\varepsilon_z$ no es nula pero se determina a "
                r"posteriori a partir del campo plano."
            )
        return (
            r"El problema se resuelve bajo \textbf{deformación plana} "
            r"($\varepsilon_z=\gamma_{xz}=\gamma_{yz}=0$), válida para "
            r"cuerpos prismáticos largos cuya sección y cargas no varían a "
            r"lo largo del eje. La tensión $\sigma_z=\nu(\sigma_x+\sigma_y)$ "
            r"no es nula."
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
            td.para(
                rf"Para el material \textbf{{{TheoryDoc.escape(mat_name)}}} "
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
            td.para(
                r"La discretización congela las decisiones del pre-proceso: "
                r"qué material compone el cuerpo, dónde están los nodos, cómo "
                r"se conectan en elementos, qué cargas externas actúan y dónde "
                r"se restringe el movimiento. El resto de la memoria opera "
                r"sobre este modelo discreto."
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

    def _build_cap_calidad(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Calidad de la malla")
        if self._prose:
            td.para(
                r"Antes de resolver, EduFEM audita la malla. Las métricas "
                r"evalúan cuánto se aleja cada elemento del cuadrado regular: "
                r"$q_{SJ}\approx 1$ y $R_J\approx 1$ indican un mapeo bien "
                r"condicionado; $q_{SJ}<0$ señala un elemento invertido "
                r"($\det\mathbf{J}<0$) que rompería la formulación."
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
                str(eid), f"{r['scaled_jacobian']:.3f}",
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

    def _build_cap_showcase(self, elem_id: int) -> None:
        td = self._td
        proj = self._project
        elem = proj.elements.get(elem_id)
        recomputed = self._recompute_showcase(elem_id)
        if elem is None or recomputed is None:
            return
        ke, gauss_data, material, node_coords = recomputed
        n_nodes = node_coords.shape[0]

        td.section_numbered(rf"Formulación elemental — Elemento {elem_id}")
        if self._prose:
            td.para(
                rf"Este capítulo desarrolla \emph{{paso a paso}} la matriz de "
                rf"rigidez del elemento $E_{{{elem_id}}}$ (el de mayor energía "
                rf"de deformación del modelo). El procedimiento es idéntico "
                rf"para los demás elementos y sigue la cadena de la "
                rf"formulación isoparamétrica: geometría $\to$ $\mathbf{{N}}$ "
                rf"$\to$ $\mathbf{{J}}$ $\to$ $\mathbf{{B}}$ $\to$ "
                rf"$\mathbf{{D}}$ $\to$ integración de Gauss. Para que todas "
                rf"las matrices quepan legibles, conviene partir de un modelo "
                rf"pequeño (ver nota al cierre del capítulo)."
            )

        # 4.1 Geometría
        td.subsection_numbered("Geometría y conectividad del elemento")
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

        gauss_to_show = self._select_gauss_to_display(gauss_data, n_nodes)

        # 4.2 Funciones de forma N en puntos de Gauss
        td.subsection_numbered(
            r"Funciones de forma $N_i(\xi,\eta)$ en los puntos de Gauss")
        if self._prose:
            td.para(
                r"Las $N_i$ interpolan geometría y desplazamientos "
                r"(formulación \emph{isoparamétrica}): $\mathbf{x}=\sum_i "
                r"N_i\mathbf{x}_i$ y $\mathbf{u}=\sum_i N_i\mathbf{u}_i$. "
                r"Evaluadas en cada punto de Gauss definen el muestreo que la "
                r"cuadratura usa para integrar."
            )
        if gauss_data:
            self._tabla_N_en_gauss(gauss_data, n_nodes, proj.element_type)
        else:
            td.para(r"\emph{Datos de Gauss no disponibles.}")

        # 4.3 Jacobiano
        td.subsection_numbered(
            r"Jacobiano $\mathbf{J}(\xi,\eta)$ y $\det\mathbf{J}$")
        if self._prose:
            td.para(
                r"El Jacobiano relaciona los diferenciales natural y físico: "
                r"$d\mathbf{x}=\mathbf{J}\,d\boldsymbol{\xi}$, con "
                r"$\mathbf{J}=\partial(x,y)/\partial(\xi,\eta)$. EduFEM lo "
                r"calcula como $\mathbf{J}=\partial\mathbf{N}\cdot "
                r"\mathbf{X}_e$. Su determinante escala el área en la "
                r"integración y debe ser $>0$ en todo el elemento."
            )
        if len(gauss_to_show) < len(gauss_data):
            td.para(rf"\emph{{Por compacidad se muestran {len(gauss_to_show)} "
                    rf"de los {len(gauss_data)} puntos de Gauss; el resto "
                    rf"sigue el mismo procedimiento.}}")
        for gp in gauss_to_show:
            self._mostrar_jacobiano_pg(gp)

        # 4.4 Matriz B
        td.subsection_numbered(r"Matriz de deformación $\mathbf{B}(\xi,\eta)$")
        if self._prose:
            td.para(
                r"$\mathbf{B}$ contiene las derivadas de las $N_i$ respecto de "
                r"$x,y$, obtenidas por la regla de la cadena "
                r"$\partial\mathbf{N}/\partial\mathbf{x}=\mathbf{J}^{-1}\,"
                r"\partial\mathbf{N}/\partial\boldsymbol{\xi}$, y relaciona "
                r"desplazamientos nodales con deformaciones: "
                r"$\boldsymbol{\varepsilon}=\mathbf{B}\,\mathbf{u}_e$."
            )
        for gp in gauss_to_show:
            self._mostrar_matriz_B_pg(gp)

        # 4.5 Constitutiva D
        td.subsection_numbered(
            r"Matriz constitutiva $\mathbf{D}$ del material asignado")
        from fem.constitutive import constitutive_matrix
        D = constitutive_matrix(material.E, material.nu, proj.analysis_type)
        if self._prose:
            td.para(
                r"$\mathbf{D}$ relaciona deformaciones con tensiones (ley de "
                rf"Hooke). Para \textbf{{{TheoryDoc.escape(material.name)}}} "
                rf"con $E={material.E:g}$, $\nu={material.nu:g}$, bajo "
                rf"{TheoryDoc.escape(proj.analysis_type).lower()}:"
            )
        td.matrix(D, name=r"\mathbf{D}", fmt="{:.4g}")

        # 4.6 Integrando simbólico (motivación de Gauss)
        td.subsection_numbered(r"Integrando simbólico $K_{ij}(\xi,\eta)$")
        if self._prose:
            td.educational_box(
                r"Aquí se ve por qué \textbf{no} integramos $\mathbf{k}_e$ "
                r"analíticamente: el integrando "
                r"$\mathbf{B}^T\mathbf{D}\,\mathbf{B}\,|\det\mathbf{J}|\,t$ "
                r"contiene $\mathbf{J}^{-1}$, que introduce $\det\mathbf{J}$ "
                r"en el denominador. Apenas el elemento se distorsiona, "
                r"$\det\mathbf{J}$ es polinómico en $(\xi,\eta)$ y el "
                r"integrando se vuelve \emph{racional} — sin primitiva "
                r"elemental. Esa es la motivación directa de la cuadratura "
                r"de Gauss: no es una opción más eficiente, es la única vía "
                r"práctica.",
                title=r"\textbf{¿Por qué cuadratura numérica y no analítica?}",
                phase="proc",
            )
        if proj.element_type == ELEMENT_Q4 and n_nodes == 4:
            self._integrando_simbolico_q4(elem, node_coords, material)
        else:
            td.para(
                r"\emph{La expansión simbólica del integrando para Q9 "
                r"(matrices $18\times 18$) excede la utilidad didáctica del "
                r"documento. Se muestra solo la sumatoria numérica de Gauss.}"
            )
            td.equation(
                r"\mathbf{k}_e=\int_{-1}^{1}\!\!\int_{-1}^{1}"
                r"\mathbf{B}^T\mathbf{D}\,\mathbf{B}\,|\det\mathbf{J}|\,t\,"
                r"d\xi\,d\eta"
            )

        # 4.7 Cuadratura -> ke
        td.subsection_numbered(
            r"Cuadratura de Gauss y matriz $\mathbf{k}_e$ resultante")
        if self._prose:
            ng = "4 ($2\\times 2$)" if proj.element_type == ELEMENT_Q4 \
                else "9 ($3\\times 3$)"
            td.para(
                rf"La integral se aproxima sumando la contribución "
                rf"$w_p\,\mathbf{{B}}_p^T\mathbf{{D}}\,\mathbf{{B}}_p\,"
                rf"|\det\mathbf{{J}}_p|\,t$ en cada uno de los {ng} puntos de "
                rf"Gauss:"
            )
        td.equation(
            r"\mathbf{k}_e \approx \sum_p w_p\,\mathbf{B}_p^T\mathbf{D}\,"
            r"\mathbf{B}_p\,|\det\mathbf{J}_p|\,t"
        )
        self._mostrar_matriz_ke(ke, name=r"\mathbf{k}_e")
        td.values([
            (r"Energía de deformación $U_e=\tfrac{1}{2}\mathbf{u}_e^T"
             r"\mathbf{k}_e\mathbf{u}_e$",
             self._energia_deformacion_str(elem_id, ke)),
            (r"$\|\mathbf{k}_e\|_F$", f"{float(np.linalg.norm(ke, 'fro')):.4g}"),
            (r"Condición $\kappa_2(\mathbf{k}_e)$", self._cond_str(ke)),
        ])
        if self._prose:
            td.educational_teaser(
                r"Para que el ensamblaje de $\mathbf{K}$ y los $\mathbf{k}_e$ "
                r"sean legibles a mano conviene un modelo mínimo: Q4 con "
                r"\textbf{2 elementos} (6 nodos, 12 GDL) basta para mostrar la "
                r"suma del ensamblaje; Q9 con \textbf{1 elemento} (18 GDL) ya "
                r"genera matrices grandes y no admite un segundo sin saturar.",
                phase="proc",
            )

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
        self._longtable(headers=headers, rows=rows,
                        col_align="rrrr" + "r" * n_nodes)

    def _mostrar_jacobiano_pg(self, gp: dict) -> None:
        td = self._td
        idx = self._gp_index(gp, 0)
        xi, eta = gp["xi"], gp["eta"]
        td.raw(rf"\paragraph{{PG{idx} — $(\xi,\eta)=({xi:.4f}, {eta:.4f})$}}")
        J = np.asarray(gp["J"])
        det_J = float(gp["det_J"])
        td.matrix(J, name=rf"\mathbf{{J}}_{{PG{idx}}}", fmt="{:.4g}")
        td.equation(rf"\det\mathbf{{J}}_{{PG{idx}}} = {det_J:.4g}")

    def _mostrar_matriz_B_pg(self, gp: dict) -> None:
        td = self._td
        # 'B' puede no estar si el gauss_data viene mínimo (no debería, porque
        # recomputamos con element_stiffness, pero protegemos por las dudas).
        B = gp.get("B")
        if B is None:
            return
        B = np.asarray(B)
        idx = self._gp_index(gp, 0)
        if B.shape[1] <= 8:
            td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}", fmt="{:.4g}")
        else:
            td.raw(rf"\paragraph{{PG{idx}}}")
            td.raw(r"{\scriptsize")
            td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}", fmt="{:.3g}")
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
            td.para(
                r"Calculada $\mathbf{k}_e$ de cada elemento, el ensamblaje "
                r"suma sus contribuciones en $\mathbf{K}$ y arma $\mathbf{F}$ "
                r"con las cargas externas, formando $\mathbf{K}\,\mathbf{u}="
                r"\mathbf{F}$ (aún sin restricciones). Por ser una sumatoria, "
                r"el orden de los elementos no altera el resultado."
            )

        K = sol["K"]
        F = np.asarray(sol["F"])
        n_dof = _K_dimension(K)

        td.subsection_numbered("Mapeo de grados de libertad")
        if self._prose:
            td.para(
                r"EduFEM indexa los GDL por la \emph{posición ordinal} del "
                r"nodo en el orden creciente de IDs (no por el ID en sí), de "
                r"modo que soporta IDs no contiguos tras borrados. Si $p(n)$ "
                r"es esa posición $0$-based, el nodo $n$ aporta los GDL "
                r"globales $2\,p(n)$ ($u_x$) y $2\,p(n)+1$ ($u_y$). Los "
                r"índices del elemento (su \emph{location matrix}) se obtienen "
                r"concatenando ese par por cada nodo del elemento, y el "
                r"ensamblaje suma $\mathbf{K}[\mathbf{LM}_e,\mathbf{LM}_e]"
                r"\mathrel{+}=\mathbf{k}_e$ y $\mathbf{F}[\mathbf{LM}_e]"
                r"\mathrel{+}=\mathbf{f}_e$. Internamente $\mathbf{K}$ se "
                r"construye como matriz \textbf{dispersa} (formato CSR): la "
                r"suma de entradas con el mismo índice global ES el scatter "
                r"local$\to$global del MEF."
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
                              caption=(r"Patrón de no-nulos de $\mathbf{K}$. La "
                                       r"concentración cerca de la diagonal es "
                                       r"la estructura de banda del MEF."),
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
            td.para(
                r"EduFEM aplica las restricciones por \textbf{eliminación}: "
                r"las filas y columnas de los GDL restringidos se quitan de "
                r"$\mathbf{K}$ y $\mathbf{F}$, formando el sistema reducido "
                r"$\mathbf{K}_{red}\,\mathbf{u}_{red}=\mathbf{F}_{red}$. Sin "
                r"restricciones $\mathbf{K}$ es singular (3 modos de cuerpo "
                r"rígido en 2D); la eliminación restaura la definida-"
                r"positividad de $\mathbf{K}_{red}$."
            )
            td.equation(r"\mathbf{K}_{red}\,\mathbf{u}_{red}=\mathbf{F}_{red}")
            td.educational_teaser(
                r"Si algún apoyo prescribe un desplazamiento no nulo "
                r"($u\neq 0$), EduFEM lo trata por condensación estática: "
                r"$\mathbf{F}_{red}\mathrel{-}=\mathbf{K}_{fr}\,\mathbf{u}_r$ "
                r"antes de resolver, preservando la simetría de "
                r"$\mathbf{K}_{red}$.",
                phase="proc",
            )

        self._valores_sistema_reducido()

        td.subsection_numbered("Método de resolución")
        if self._prose:
            td.para(
                r"El sistema reducido se resuelve con "
                r"\texttt{scipy.sparse.linalg.spsolve} sobre $\mathbf{K}_{red}$ "
                r"en formato disperso CSR. \texttt{spsolve} realiza una "
                r"\textbf{factorización LU dispersa} (SuperLU; UMFPACK si está "
                r"disponible) y dos sustituciones triangulares. Aunque "
                r"$\mathbf{K}_{red}$ es simétrica definida positiva, el "
                r"software usa el solver disperso de propósito general porque "
                r"escala bien con el tamaño del modelo y aprovecha la "
                r"dispersión de $\mathbf{K}$ (memoria $O(\text{nnz})$). Tras "
                r"resolver $\mathbf{u}_{red}$, los desplazamientos prescritos "
                r"se reinsertan en el vector global $\mathbf{u}$."
            )
            td.educational_teaser(
                r"Si $\mathbf{K}_{red}$ fuera singular (BCs insuficientes, "
                r"elemento invertido, $E/\nu$ fuera de rango), la solución "
                r"contiene NaN/Inf y el solver lo detecta y aborta — no "
                r"devuelve un resultado espurio.",
                phase="proc",
            )

        # Desplazamientos
        td.subsection_numbered("Vector de desplazamientos nodales")
        if self._prose:
            td.para(
                r"$\mathbf{u}$ contiene un par $(u_x,u_y)$ por nodo, ordenado "
                r"por índice ordinal ascendente. Compacto (exponente común) y "
                r"desagregado por nodo:"
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
            td.para(
                r"El post-proceso recorre la cadena $\mathbf{u}\to"
                r"\boldsymbol{\varepsilon}_{Gauss}\to"
                r"\boldsymbol{\sigma}_{Gauss}\to\boldsymbol{\sigma}_{nodo}\to"
                r"\boldsymbol{\sigma}_{prom}\to(\sigma_1,\sigma_2,\sigma_{VM})$ "
                r"para obtener las magnitudes con las que se juzga el diseño."
            )

        td.subsection_numbered("Tensiones en los puntos de Gauss")
        if self._prose:
            td.para(
                r"Para cada elemento, $\boldsymbol{\sigma}=\mathbf{D}\,"
                r"\mathbf{B}(\xi_p,\eta_p)\,\mathbf{u}_e$ en cada punto de "
                r"Gauss. EduFEM las calcula allí (y no directamente en los "
                r"nodos) porque los puntos de Gauss son los \emph{puntos "
                r"superconvergentes} de Barlow: la tensión calculada en ellos "
                r"converge un orden más rápido que en el resto del elemento."
            )

        td.subsection_numbered("Extrapolación de Gauss a nodos")
        if self._prose:
            td.para(
                r"Los valores en los puntos de Gauss se llevan a los nodos "
                r"mediante $\boldsymbol{\sigma}^{nodo}=\mathbf{E}\,"
                r"\boldsymbol{\sigma}^{Gauss}$, con $\mathbf{E}=\mathbf{N}_p^{-1}$ "
                r"(inversa de las funciones de forma evaluadas en los puntos "
                r"de Gauss)."
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
                r"Para Q9 ($3\times 3$ puntos de Gauss) no hay forma cerrada "
                r"simple: $\mathbf{E}_{Q9}$ es la inversa numérica de la "
                r"matriz $9\times 9$ de funciones de forma en los puntos de "
                r"Gauss, cacheada a nivel de módulo (misma para todo elemento "
                r"Q9, independiente de su geometría)."
            )

        td.subsection_numbered("Promediado nodal entre elementos adyacentes")
        if self._prose:
            td.para(
                r"Un nodo compartido por $k$ elementos recibe $k$ valores "
                r"extrapolados distintos (las tensiones MEF son discontinuas "
                r"entre elementos). EduFEM asigna el promedio aritmético:"
            )
            td.equation(
                r"\sigma_n^{\,prom}=\frac{1}{k_n}\sum_{e\in\mathcal{E}_n}"
                r"\sigma_n^{\,(e)}")
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
                r"$\sigma_1\geq\sigma_2$ son los autovalores del tensor de "
                r"tensiones 2D — las tensiones normales máxima y mínima sobre "
                r"los planos donde el corte se anula. EduFEM las recalcula "
                r"desde las componentes ya promediadas (no promedia "
                r"$\sigma_1/\sigma_2$ directamente, porque no son lineales):"
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

        # Contornos (PIL, estilo canvas)
        td.subsection_numbered("Mapas de contornos de tensiones")
        if self._prose:
            td.para(
                r"Los contornos se dibujan al estilo del Post-Proceso del "
                r"software (gradiente bilineal sobre cada elemento) con fondo "
                r"blanco. Convención de mapa: \emph{coolwarm} (divergente) "
                r"para $\sigma_x$, $\sigma_y$, $\tau_{xy}$ —donde el cero "
                r"separa tracción de compresión— y \emph{viridis} (secuencial) "
                r"para $\sigma_{VM}$, que es no negativo."
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
    # Showcase compacto (estilo directo)
    # ------------------------------------------------------------------

    def _build_showcase_directo(self, elem_id: int) -> None:
        td = self._td
        proj = self._project
        elem = proj.elements.get(elem_id)
        recomputed = self._recompute_showcase(elem_id)
        if elem is None or recomputed is None:
            return
        ke, _gauss_data, material, node_coords = recomputed
        n_nodes = node_coords.shape[0]

        td.section_numbered(rf"Formulación elemental — Elemento {elem_id}")
        rows = []
        for i, nid in enumerate(elem.node_ids[:n_nodes]):
            x, y = node_coords[i]
            rows.append([f"$N_{{{i+1}}}$", str(nid), fmt(x, "length"),
                         fmt(y, "length")])
        self._longtable(headers=["Nodo local", "Nodo global", r"$X$", r"$Y$"],
                        rows=rows, col_align="ccrr")
        td.values([
            ("Tipo", TheoryDoc.escape(proj.element_type)),
            ("Espesor $t$", fmt(elem.thickness, "length")),
            ("Material", TheoryDoc.escape(elem.material_name)),
        ])
        td.equation(
            r"\mathbf{k}_e=\int_{-1}^{1}\!\!\int_{-1}^{1}"
            r"\mathbf{B}^T\mathbf{D}\,\mathbf{B}\,|\det\mathbf{J}|\,t\,"
            r"d\xi\,d\eta \approx \sum_p w_p\,\mathbf{B}_p^T\mathbf{D}\,"
            r"\mathbf{B}_p\,|\det\mathbf{J}_p|\,t"
        )
        self._mostrar_matriz_ke(ke, name=r"\mathbf{k}_e")
        td.values([(r"$\|\mathbf{k}_e\|_F$",
                    f"{float(np.linalg.norm(ke, 'fro')):.4g}")])

    def _build_sistema_global_directo(self) -> None:
        td = self._td
        sol = self._solution
        K = sol["K"]
        F = np.asarray(sol["F"])
        n_dof = _K_dimension(K)
        td.section_numbered(r"Sistema global $\mathbf{K}\,\mathbf{u}=\mathbf{F}$")
        td.values([
            (r"Tamaño de $\mathbf{K}$", f"{n_dof} × {n_dof}"),
            (r"Tamaño de $\mathbf{F}$", f"{n_dof} × 1"),
        ])
        td.subsection_numbered(r"Matriz de rigidez global $\mathbf{K}$")
        self._mostrar_matriz_K(K)
        td.subsection_numbered(r"Vector de fuerzas globales $\mathbf{F}$")
        td.raw(r"{\scriptsize")
        td.vector_factored(F, name=r"\mathbf{F}", sig_digits=3, transpose=True)
        td.raw(r"}")
        self._desglose_F(F)

    # ------------------------------------------------------------------
    # Apéndices (solo estilo 'completo')
    # ------------------------------------------------------------------

    def _build_appendix_a_kes(self, showcase_id: Optional[int]) -> None:
        td = self._td
        proj = self._project
        elem_data = self._solution.get("element_data", {})
        td.section_numbered("Matrices de rigidez elementales")
        td.para(
            r"Matrices $\mathbf{k}_e$ del resto de los elementos (la del "
            r"elemento desarrollado en la formulación elemental no se repite)."
        )
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
            self._mostrar_matriz_ke(ke, name=rf"\mathbf{{k}}_{{{eid}}}")
        if not any_shown:
            td.para(r"\emph{El modelo posee un único elemento; no hay matrices "
                    r"adicionales para listar.}")

    def _build_appendix_b_datos(self) -> None:
        td = self._td
        td.section_numbered("Datos completos del análisis")
        td.subsection_numbered(
            "Tensiones por punto de Gauss (todos los elementos)")
        if not self._element_stresses:
            td.para(r"\emph{Datos por punto de Gauss no disponibles.}")
        else:
            self._tabla_gauss_stresses_completos()
        td.subsection_numbered("Vector de desplazamientos completo")
        u = np.asarray(self._solution["u"])
        td.raw(r"{\scriptsize")
        td.vector_factored(u, name=r"\mathbf{u}", sig_digits=4, transpose=True)
        td.raw(r"}")
        rows = [[str(i), f"{float(v):.5e}"] for i, v in enumerate(u)]
        self._longtable(headers=["GDL", r"$u_i$"], rows=rows, col_align="rr")

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

    def _build_appendix_c_glosario(self) -> None:
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
