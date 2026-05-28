"""
Memoria de Cálculo de EduFEM — generador del PDF educativo del análisis MEF.

Compila un documento LaTeX (via pylatex + pdflatex) que documenta paso a
paso el análisis realizado por el motor `fem/`: datos del modelo,
formulación elemental, ensamblaje, aplicación de restricciones (eliminación),
solución (Cholesky LL^T), reacciones, post-proceso (Gauss → nodos →
promediado → principales / von Mises) y visualizaciones del campo.

Filosofía
=========
1. La memoria documenta EL SOFTWARE REAL. Cada afirmación tiene una
   contraparte directa en `fem/*.py`: nada de "métodos genéricos de libro"
   que el código no implementa. Si el código cambia, esta memoria cambia.
2. Las VISUALIZACIONES de campo (contornos, deformada, geometría, cruces
   principales) se renderizan con Pillow en `file_io/figure_export.py`,
   replicando el aspecto del `MeshCanvas` del Post pero con fondo blanco.
   Las figuras esquemáticas (Mohr, heatmap K, pipeline MEF) se mantienen
   en matplotlib.
3. Tres estilos seleccionables (`MemoriaCalculo.STYLES`):
   * **directo**: tablas + matrices clave + contornos. Sin narrativa,
     sin pedagogía. Para usuarios que ya conocen MEF y quieren los
     números.
   * **educativo** (DEFAULT): narrativa concisa + showcase de un elemento
     + ensamblaje + solución + post + visualización. Optimizada para
     que el alumno reproduzca el procedimiento a mano. ~25 páginas en
     proyectos con ≤ 4 elementos Q4 o 1 elemento Q9.
   * **completo**: educativo + apéndices con datos exhaustivos (k_e de
     todos los elementos, tensiones por punto de Gauss, vector u
     desagregado). Útil como registro de archivo o validación detallada.

El invariante histórico "completo = PDF bit-a-bit idéntico" YA NO APLICA:
toda la memoria fue reformulada en 2026-05 desde cero. Los archivos
generados por versiones previas no se pueden comparar.

API pública
===========
`generate_memoria_calculo(project, solution, element_stresses,
                          nodal_stresses, filepath, *, style='educativo',
                          progress_callback=None, keep_tex=False) -> str`
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from typing import Any, Callable, Optional

import numpy as np
from pylatex import NoEscape

from config.settings import (
    APP_NAME, APP_VERSION,
    ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN,
    ELEMENT_Q4, ELEMENT_Q9,
    NUMERICAL_TOLERANCE,
    fmt,
)
from education.components.theory_builder import TheoryDoc


NUMERICAL_TOLERANCE_K = max(NUMERICAL_TOLERANCE, 1e-9)


class MemoriaCalculoError(RuntimeError):
    """Error elevado por el generador con mensaje accionable."""


# ───────────────────────────────────────────────────────────────────────────
# API pública
# ───────────────────────────────────────────────────────────────────────────

def generate_memoria_calculo(
    project,
    solution: dict,
    element_stresses: Optional[dict],
    nodal_stresses: Optional[dict],
    filepath: str,
    *,
    style: str = "educativo",
    progress_callback: Optional[Callable[[str, float], None]] = None,
    keep_tex: bool = False,
    # Campos legacy preservados para no romper callers viejos.
    mesh_diagram: Any = None,
    contour_figures: Optional[dict] = None,
    scope: Optional[str] = None,
) -> str:
    """Compila la Memoria de Cálculo del proyecto resuelto a un PDF.

    Parámetros
    ----------
    project : ProjectModel
        Proyecto con `is_solved == True`.
    solution : dict
        Resultado de `fem.solver.solve_system`.
    element_stresses, nodal_stresses : dict | None
        Salida de `fem.stress.compute_all_stresses`. Si `None`, las
        secciones de post-proceso degradan elegantemente.
    filepath : str
        Ruta destino. Si no termina en `.pdf`, se añade la extensión.
    style : {"directo", "educativo", "completo"}
        Selecciona la profundidad del documento (ver módulo). Default
        `"educativo"`.
    progress_callback : callable(stage, pct) | None
        Reporta el progreso al caller (UI). `pct ∈ [0, 1]`.
    keep_tex : bool
        Si `True`, conserva el `.tex` intermedio junto al PDF.

    Retorna
    -------
    str : ruta absoluta del PDF generado.
    """
    if style not in MemoriaCalculo.STYLES:
        raise MemoriaCalculoError(
            f"Estilo desconocido: {style!r}. "
            f"Valores aceptados: {list(MemoriaCalculo.STYLES)}."
        )
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
                             style=style)

    _progress("Construyendo capítulos", 0.20)
    memoria.build()

    _progress("Compilando con pdflatex", 0.60)
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


# ───────────────────────────────────────────────────────────────────────────
# Clase generadora
# ───────────────────────────────────────────────────────────────────────────

class MemoriaCalculo:
    """Construye la Memoria paso-a-paso. Compone `TheoryDoc`."""

    TITLE = "Memoria de Cálculo"
    SUBTITLE_TEMPLATE = "Análisis MEF 2D — Proyecto: {name}"

    # Tres estilos pedagógicamente diferenciados (CLAUDE.md sección
    # "Memoria de Cálculo"). El default (`educativo`) es el caso de uso
    # típico del alumno.
    STYLES = ("directo", "educativo", "completo")

    # Umbral por encima del cual K se muestra como heatmap en vez de literal.
    # 16 GDL ≈ 8 nodos = malla 2×2 Q4 o 1 elemento Q9 (que tiene 18, igual
    # cae a heatmap). Por debajo: literal con exponente factorizado.
    _K_LITERAL_MAX_DIM = 16

    # k_e literal: Q4 (8×8) cabe en portrait, Q9 (18×18) requiere landscape.
    _KE_LITERAL_PORTRAIT_MAX = 8

    def __init__(self, project, solution, element_stresses, nodal_stresses,
                 *, style: str = "educativo"):
        if style not in self.STYLES:
            raise MemoriaCalculoError(f"Estilo desconocido: {style!r}.")
        self._project = project
        self._solution = solution
        self._element_stresses = element_stresses or {}
        self._nodal_stresses = nodal_stresses or {}
        self._style = style

        # Directorio temporal para PNGs (cleanup en compile()). Lazy.
        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None

        title = TheoryDoc.escape(self.TITLE)
        subtitle = TheoryDoc.escape(
            self.SUBTITLE_TEMPLATE.format(name=project.project_name)
        )
        self._td = TheoryDoc(title=title, subtitle=subtitle)
        self._configure_preamble()

    # ────── flags derivados del estilo ──────
    @property
    def _has_narrative(self) -> bool:
        return self._style != "directo"

    @property
    def _has_showcase(self) -> bool:
        return self._style != "directo"

    @property
    def _has_quality_chapter(self) -> bool:
        return self._style != "directo"

    @property
    def _has_appendices(self) -> bool:
        return self._style == "completo"

    # ────── preámbulo ──────
    def _configure_preamble(self) -> None:
        td = self._td
        proj = self._project
        td.package("babel", options="spanish")
        td.package("longtable")
        td.package("caption")
        td.package("fancyhdr")
        # Q9 tiene k_e 18×18 y B 3×18 — subir el límite de columnas.
        td.raw(r"\setcounter{MaxMatrixCols}{20}")
        td.raw(r"\pagestyle{fancy}")
        td.raw(r"\fancyhf{}")
        proj_name_safe = TheoryDoc.escape(proj.project_name)
        td.raw(rf"\fancyhead[L]{{\small Memoria de Cálculo}}")
        td.raw(rf"\fancyhead[R]{{\small {proj_name_safe}}}")
        td.raw(r"\fancyfoot[C]{\small \thepage}")
        td.raw(r"\renewcommand{\headrulewidth}{0.4pt}")
        td.raw(r"\setlength{\parskip}{4pt plus 1pt minus 1pt}")
        td.raw(r"\setlength{\parindent}{0pt}")

    # ────── construcción del documento ──────
    def build(self) -> None:
        """Llena el documento según el estilo activo.

        Estructura (estilo `educativo` y `completo`):
        ```
        Portada
        Resumen del análisis
        Datos del modelo
        Calidad de la malla              (omitido en `directo`)
        Procedimiento elemental          (omitido en `directo`)
        Ensamblaje                       (omitido en `directo`)
        Aplicación de restricciones      (omitido en `directo`)
        Solución y reacciones
        Tensiones                        (post-proceso)
        Visualización                    (deformada + contornos + cruces)
        Apéndices                        (solo `completo`)
        ```
        Estilo `directo` reduce a: portada + datos + solución + tensiones
        + visualización. Sin narrativa intermedia.
        """
        self._build_cover()
        self._td.toc()
        self._build_resumen()
        self._build_modelo()
        if self._has_quality_chapter:
            self._build_calidad()
        showcase_id = self._select_showcase_element()
        if self._has_showcase and showcase_id is not None:
            self._build_showcase(showcase_id)
        if self._has_narrative:
            self._build_ensamblaje(showcase_id)
            self._build_restricciones()
        self._build_solucion()
        self._build_post_proceso()
        self._build_visualizacion()
        if self._has_appendices:
            self._td.raw(r"\appendix")
            self._build_apendice_a_kes(showcase_id)
            self._build_apendice_b_gauss_stresses()
            self._build_apendice_c_vectores_completos()

    def compile(self, filepath_no_ext: str, *, keep_tex: bool = False) -> None:
        try:
            self._td.compile_to(filepath_no_ext, keep_tex=keep_tex)
        finally:
            self._cleanup_tmpdir()

    def tex_source(self) -> str:
        return self._td.document().dumps()

    # ────── helpers ──────
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

    def _save_figure(self, fig, name: str) -> Optional[str]:
        """Guarda una figura matplotlib o una `PIL.Image.Image` en disco.

        Inspecciona el tipo runtime (no requiere importar matplotlib/PIL
        si la figura no aplica). Retorna la ruta absoluta del PNG generado,
        o `None` si falla.
        """
        if fig is None:
            return None
        try:
            tmpdir = self._ensure_tmpdir()
            path = os.path.join(tmpdir, f"{name}.png")
            # Matplotlib Figure (tiene savefig); PIL.Image (tiene save).
            if hasattr(fig, "savefig"):
                fig.savefig(path, dpi=150, bbox_inches="tight",
                            facecolor="white")
            elif hasattr(fig, "save"):
                fig.save(path, "PNG")
            else:
                return None
            return path
        except Exception:
            return None

    def _longtable(self, *, headers: list[str], rows: list[list[str]],
                   col_align: str) -> None:
        """Tabla longtable con headers en negrita y booktabs."""
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

    @staticmethod
    def _fmt_signed(x: float, *, decimals: int = 5) -> str:
        """`'1.23e-04'` para positivos, `'-1.23e-04'` para negativos.

        Sin '+' prefijo en positivos (regla del proyecto: los positivos
        en vectores/matrices no llevan signo explícito).
        """
        s = f"{float(x):.{decimals}e}"
        return s

    # ───────────────────────────────────────────────────────────────────────
    # Portada
    # ───────────────────────────────────────────────────────────────────────

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
            ("Estilo de la memoria", TheoryDoc.escape(self._style)),
            ("Nodos", str(proj.num_nodes)),
            ("Elementos", str(proj.num_elements)),
            ("Grados de libertad", str(proj.total_dof)),
            ("Hash SHA-256 del modelo", rf"\texttt{{{digest}}}"),
            ("Generado por",
             f"{TheoryDoc.escape(APP_NAME)} v{APP_VERSION}"),
        ]
        td.values(info)
        if self._has_narrative:
            td.raw(r"\vspace{1em}")
            td.para(
                r"\emph{Este documento describe paso a paso el análisis "
                r"realizado por EduFEM sobre el modelo. Cada capítulo "
                r"corresponde a una etapa del pipeline del método de los "
                r"elementos finitos —tal como está implementado en el "
                r"motor }\texttt{fem/}\emph{ del software— combinando la "
                r"formulación con los valores numéricos del problema.}"
            )
        td.raw(r"\newpage")

    # ───────────────────────────────────────────────────────────────────────
    # Resumen del análisis
    # ───────────────────────────────────────────────────────────────────────

    def _build_resumen(self) -> None:
        """Vista panorámica (sin numerar): pipeline + diagrama del modelo.

        En estilo `directo` se reduce a una única página con el diagrama
        del modelo. En `educativo`/`completo` incluye el pipeline MEF
        coloreado por fase.
        """
        td = self._td
        td.raw(r"\section*{Resumen del análisis}")
        td.raw(r"\addcontentsline{toc}{section}{Resumen del análisis}")

        if self._has_narrative:
            proj = self._project
            n = proj.num_nodes
            ne = proj.num_elements
            ndof = proj.total_dof
            td.para(
                rf"El análisis discretiza el dominio en \textbf{{{ne}}} "
                rf"elementos {TheoryDoc.escape(proj.element_type)} unidos "
                rf"por \textbf{{{n}}} nodos, definiendo un sistema lineal "
                rf"$\mathbf{{K}}\,\mathbf{{u}} = \mathbf{{F}}$ con "
                rf"$\mathbf{{u}} \in \mathbb{{R}}^{{{ndof}}}$. El "
                rf"pipeline siguiente resume las etapas que recorre el "
                rf"motor para transformar los datos del pre-proceso en "
                rf"el campo de tensiones del post-proceso:"
            )
            try:
                from file_io.figure_export import render_fem_pipeline
                fig = render_fem_pipeline()
                p = self._save_figure(fig, "fem_pipeline")
                if p is not None:
                    td.figure(
                        p,
                        caption=("Pipeline del MEF en EduFEM. Las cajas "
                                 "azules son etapas del pre-proceso, las "
                                 "naranjas del proceso, la verde del "
                                 "post-proceso."),
                        label="fig:fem_pipeline",
                        width=r"0.96\textwidth",
                    )
            except Exception:
                pass

        # Diagrama del modelo (común a los 3 estilos).
        try:
            from file_io.figure_export import render_mesh_diagram
            fig = render_mesh_diagram(self._project)
            p = self._save_figure(fig, "mesh_diagram")
            if p is not None:
                td.figure(
                    p,
                    caption=("Discretización del modelo: elementos, nodos "
                             "numerados, símbolos de restricción y "
                             "cargas aplicadas."),
                    label="fig:mesh",
                    width=r"0.92\textwidth",
                )
        except Exception:
            pass
        td.raw(r"\newpage")

    # ───────────────────────────────────────────────────────────────────────
    # Datos del modelo
    # ───────────────────────────────────────────────────────────────────────

    def _build_modelo(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Datos del modelo")

        if self._has_narrative:
            td.para(
                r"Esta sección compila las entradas del pre-proceso que "
                r"definen el problema discreto: materiales, nodos, "
                r"conectividad de elementos, cargas y restricciones. "
                r"El resto de la memoria opera sobre estos datos."
            )

        td.subsection_numbered("Configuración del análisis")
        cfg_rows = [
            ("Tipo de análisis", TheoryDoc.escape(proj.analysis_type)),
            ("Tipo de elemento", TheoryDoc.escape(proj.element_type)),
            ("Cuadratura de Gauss",
             "2×2 (4 PG)" if proj.element_type == ELEMENT_Q4 else "3×3 (9 PG)"),
            ("Sistema de unidades", TheoryDoc.escape(proj.unit_system)),
            ("Gravedad activa", "Sí" if proj.include_gravity else "No"),
        ]
        if proj.include_gravity:
            cfg_rows.append(
                ("Vector $\\mathbf{g}$",
                 f"({fmt(proj.gravity_x, 'length')}, "
                 f"{fmt(proj.gravity_y, 'length')})")
            )
        td.values(cfg_rows)

        td.subsection_numbered("Materiales")
        self._tabla_materiales()

        td.subsection_numbered("Nodos")
        self._tabla_nodos()

        td.subsection_numbered("Conectividad de elementos")
        self._tabla_elementos()

        if proj.nodal_loads:
            td.subsection_numbered("Cargas nodales")
            self._tabla_cargas_nodales()
        if getattr(proj, "surface_loads", None):
            td.subsection_numbered("Cargas superficiales")
            self._tabla_cargas_superficiales()
        if proj.boundary_conditions:
            td.subsection_numbered("Condiciones de contorno (restricciones)")
            self._tabla_restricciones()

    def _tabla_materiales(self) -> None:
        proj = self._project
        usados = {e.material_name for e in proj.elements.values()}
        rows = []
        for name, mat in proj.materials.items():
            if usados and name not in usados:
                continue
            density = getattr(mat, "density", None)
            rows.append([
                TheoryDoc.escape(name),
                f"{mat.E:g}",
                f"{mat.nu:g}",
                f"{density:g}" if density else "—",
            ])
        if not rows:
            self._td.para(r"\emph{Sin materiales referenciados.}")
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
        is_q9 = proj.element_type == ELEMENT_Q9
        if is_q9:
            headers = ["ID"] + [f"N{i}" for i in range(1, 10)] + ["Espesor", "Material"]
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
        rows = []
        for nid in sorted(proj.boundary_conditions.keys()):
            bc = proj.boundary_conditions[nid]
            rx = "Sí" if bc.restrain_x else "No"
            ry = "Sí" if bc.restrain_y else "No"
            ux = fmt(getattr(bc, "ux_value", 0.0), "length")
            uy = fmt(getattr(bc, "uy_value", 0.0), "length")
            rows.append([str(nid), rx, ry, ux, uy])
        self._longtable(
            headers=["Nodo", "Restringe X", "Restringe Y",
                     r"$u_x$ prescrito", r"$u_y$ prescrito"],
            rows=rows,
            col_align="rccrr",
        )

    # ───────────────────────────────────────────────────────────────────────
    # Calidad de la malla
    # ───────────────────────────────────────────────────────────────────────

    def _build_calidad(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Calidad geométrica de la malla")
        td.para(
            r"EduFEM evalúa cuatro métricas sobre cada elemento, "
            r"computadas en \texttt{fem/mesh\_quality.py}, antes de "
            r"resolver. Un elemento con $\det\mathbf{J}\le 0$ "
            r"(\emph{Mala}) invalida el integrando de Gauss y no debe "
            r"resolverse; uno con \emph{Aceptable} produce solución "
            r"válida pero con mayor error local. La tabla siguiente "
            r"reporta los valores efectivos del modelo."
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
            headers = ["Elem", r"$q_{SJ}$", r"$R_J$", r"$AR$",
                       r"$T_R$", r"$\theta_{min}$", r"$\theta_{max}$", "Estado"]
        col_align = "rrrrrrrl"
        rows = []
        for eid in sorted(results.keys()):
            r = results[eid]
            fourth = (r.get("midside_admissibility") or {}).get("q_D") if is_q9 \
                else r.get("robinson_taper")
            fourth_str = (f"{fourth:.3f}"
                          if fourth is not None and np.isfinite(fourth)
                          else "—")
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

    # ───────────────────────────────────────────────────────────────────────
    # Procedimiento elemental (showcase)
    # ───────────────────────────────────────────────────────────────────────

    def _select_showcase_element(self) -> Optional[int]:
        """Elige el elemento de máxima energía de deformación.

        $U_e = \\tfrac12 \\mathbf{u}_e^T \\mathbf{k}_e \\mathbf{u}_e$.
        Fallback: argmax $\\|\\mathbf{k}_e\\|_F$.
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

    def _build_showcase(self, elem_id: int) -> None:
        td = self._td
        proj = self._project
        elem = proj.elements.get(elem_id)
        if elem is None:
            return
        sol = self._solution
        elem_data = sol.get("element_data", {}).get(elem_id)
        if elem_data is None:
            return

        td.section_numbered(rf"Procedimiento elemental — Elemento {elem_id}")
        td.para(
            rf"Este capítulo desarrolla en detalle el cálculo de la "
            rf"matriz de rigidez del elemento $E_{{{elem_id}}}$, el "
            rf"\emph{{elemento estrella}} del modelo (mayor energía de "
            rf"deformación). El procedimiento es idéntico para los "
            rf"demás elementos; sus resultados se resumen en la sección "
            rf"de ensamblaje."
        )
        td.para(
            r"La cadena que recorre el motor \texttt{fem/} es:"
            r"\quad geometría $\to$ $\mathbf{N}(\xi,\eta)$ "
            r"$\to$ $\mathbf{J}$, $\det\mathbf{J}$ "
            r"$\to$ $\mathbf{B}(\xi,\eta)$ "
            r"$\to$ $\mathbf{D}$ "
            r"$\to$ $\mathbf{k}_e = \sum_p w_p \mathbf{B}_p^T\mathbf{D}\,"
            r"\mathbf{B}_p\,|\det\mathbf{J}_p|\,t$."
        )

        # Geometría
        td.subsection_numbered("Geometría del elemento")
        node_coords = np.asarray(elem_data["node_coords"])
        n_nodes = node_coords.shape[0]
        rows = []
        for i, nid in enumerate(elem.node_ids[:n_nodes]):
            x, y = node_coords[i]
            rows.append([f"$N_{{{i+1}}}$", str(nid),
                         fmt(x, "length"), fmt(y, "length")])
        self._longtable(
            headers=["Local", "Global", r"$X$", r"$Y$"],
            rows=rows, col_align="ccrr",
        )
        td.values([
            ("Espesor $t$", fmt(elem.thickness, "length")),
            ("Material", TheoryDoc.escape(elem.material_name)),
        ])

        # Matriz constitutiva D
        td.subsection_numbered(r"Matriz constitutiva $\mathbf{D}$")
        material = proj.materials.get(elem.material_name)
        if material is None:
            td.para(r"\emph{Material no encontrado en el modelo.}")
            return
        from fem.constitutive import constitutive_matrix
        D = constitutive_matrix(material.E, material.nu, proj.analysis_type)
        if proj.analysis_type == ANALYSIS_PLANE_STRESS:
            td.para(
                rf"Bajo tensión plana, con $E={material.E:g}$ y "
                rf"$\nu={material.nu:g}$:"
            )
            td.equation(
                r"\mathbf{D} = \frac{E}{1-\nu^2}\begin{bmatrix}"
                r"1 & \nu & 0 \\ \nu & 1 & 0 \\ 0 & 0 & (1-\nu)/2"
                r"\end{bmatrix}"
            )
        else:
            td.para(
                rf"Bajo deformación plana, con $E={material.E:g}$ y "
                rf"$\nu={material.nu:g}$:"
            )
            td.equation(
                r"\mathbf{D} = \frac{E}{(1+\nu)(1-2\nu)}\begin{bmatrix}"
                r"1-\nu & \nu & 0 \\ \nu & 1-\nu & 0 \\ 0 & 0 & (1-2\nu)/2"
                r"\end{bmatrix}"
            )
        td.para("Evaluando con los valores del material:")
        td.matrix(D, name=r"\mathbf{D}", fmt="{:+.4g}")

        # Funciones de forma N y matriz B en los PG
        gauss_data = elem_data.get("gauss_data", [])
        gauss_to_show = self._select_gauss_to_display(gauss_data, n_nodes)

        td.subsection_numbered(
            r"Funciones de forma $N_i$ y matriz $\mathbf{B}$ en los PG"
        )
        td.para(
            r"En la formulación isoparamétrica las $N_i(\xi,\eta)$ "
            r"interpolan tanto la geometría "
            r"($x = \sum_i N_i x_i$, $y = \sum_i N_i y_i$) como el "
            r"campo de desplazamientos "
            r"($\mathbf{u}(\xi,\eta) = \sum_i N_i \mathbf{u}_i$). La "
            r"matriz $\mathbf{B}$ se construye con las derivadas "
            r"físicas $\partial N_i / \partial x = "
            r"\mathbf{J}^{-1}\,\partial N_i / \partial \boldsymbol{\xi}$ "
            r"(implementación: \texttt{fem/jacobian.py} + "
            r"\texttt{fem/b\_matrix.py})."
        )
        if not gauss_data:
            td.para(r"\emph{Datos de Gauss no disponibles.}")
            return
        # Tabla N en PGs
        self._tabla_N_en_gauss(gauss_data, n_nodes, proj.element_type)
        # Mostrar J, det J y B en los PGs representativos
        for gp in gauss_to_show:
            idx = gp["index"] + 1
            xi, eta = gp["xi"], gp["eta"]
            td.raw(rf"\paragraph{{PG{idx} — $(\xi,\eta) = "
                   rf"({xi:.4f}, {eta:.4f})$, $w_p = {gp['weight']:.4f}$}}")
            J = np.asarray(gp["J"])
            det_J = float(gp["det_J"])
            td.matrix(J, name=rf"\mathbf{{J}}_{{PG{idx}}}",
                      fmt="{:+.4g}")
            td.equation(rf"\det \mathbf{{J}}_{{PG{idx}}} = {det_J:.4g}")
            B = np.asarray(gp["B"])
            if B.shape[1] <= 8:
                td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}",
                          fmt="{:+.4g}")
            else:
                td.raw(r"{\scriptsize")
                td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}",
                          fmt="{:+.3g}")
                td.raw(r"}")
        if len(gauss_to_show) < len(gauss_data):
            td.para(
                rf"\emph{{(Se muestran {len(gauss_to_show)} de "
                rf"{len(gauss_data)} puntos de Gauss; el resto sigue el "
                rf"mismo procedimiento.)}}"
            )

        # Matriz k_e
        td.subsection_numbered(r"Matriz de rigidez elemental $\mathbf{k}_e$")
        td.para(
            r"La rigidez del elemento se obtiene por cuadratura de "
            r"Gauss-Legendre 2D — sumatoria de los integrandos en los "
            r"puntos $(\xi_p,\eta_p)$ con sus pesos $w_p$:"
        )
        td.equation(
            r"\mathbf{k}_e = \sum_p w_p\,\mathbf{B}_p^T\,\mathbf{D}\,"
            r"\mathbf{B}_p\,|\det\mathbf{J}_p|\,t"
        )
        ke = np.asarray(elem_data["ke"])
        if ke.shape[0] <= self._KE_LITERAL_PORTRAIT_MAX:
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
            (r"$\|\mathbf{k}_e\|_F$",
             f"{float(np.linalg.norm(ke, 'fro')):.4g}"),
            (r"$U_e = \tfrac12 \mathbf{u}_e^T \mathbf{k}_e \mathbf{u}_e$",
             self._energia_deformacion_str(elem_id, ke)),
        ])

    def _energia_deformacion_str(self, elem_id, ke: np.ndarray) -> str:
        sol = self._solution
        u = sol.get("u")
        elem_data = sol.get("element_data", {}).get(elem_id, {})
        dof_idx = elem_data.get("dof_indices")
        if u is None or dof_idx is None:
            return "—"
        try:
            u_e = np.asarray(u)[list(dof_idx)]
            return f"{0.5 * float(u_e @ ke @ u_e):.4g}"
        except Exception:
            return "—"

    @staticmethod
    def _select_gauss_to_display(gauss_data: list, n_nodes: int) -> list:
        """Para Q4 muestra los 4 PG. Para Q9 muestra 3 representativos."""
        if not gauss_data:
            return []
        if n_nodes <= 4:
            return list(gauss_data)
        n = len(gauss_data)
        if n <= 4:
            return list(gauss_data)
        idxs = sorted({0, n // 2, n - 1})
        return [gauss_data[i] for i in idxs if i < n]

    def _tabla_N_en_gauss(self, gauss_data, n_nodes, element_type) -> None:
        from fem.shape_functions import get_shape_functions
        N_func, _ = get_shape_functions(element_type)
        headers = ["PG", r"$\xi$", r"$\eta$", r"$w$"] + \
                  [rf"$N_{{{i+1}}}$" for i in range(n_nodes)]
        rows = []
        for gp in gauss_data:
            xi, eta = gp["xi"], gp["eta"]
            w = gp["weight"]
            N_vals = N_func(xi, eta)
            row = [
                f"PG{gp['index']+1}",
                f"{xi:.4f}",
                f"{eta:.4f}",
                f"{w:.4f}",
            ] + [f"{float(n):.4f}" for n in N_vals]
            rows.append(row)
        col_align = "rrrr" + "r" * n_nodes
        self._longtable(headers=headers, rows=rows, col_align=col_align)

    # ───────────────────────────────────────────────────────────────────────
    # Ensamblaje
    # ───────────────────────────────────────────────────────────────────────

    def _build_ensamblaje(self, showcase_id: Optional[int]) -> None:
        td = self._td
        proj = self._project
        sol = self._solution
        td.section_numbered("Ensamblaje del sistema global")
        td.para(
            r"EduFEM construye $\mathbf{K}$ y $\mathbf{F}$ por superposición "
            r"directa: cada elemento aporta su $\mathbf{k}_e$ a las filas "
            r"y columnas globales correspondientes a sus GDLs, y cada "
            r"carga nodal/superficial/másica aporta a $\mathbf{F}$ "
            r"(implementación: \texttt{fem/assembly.py})."
        )

        td.subsection_numbered("Indexación ordinal de GDLs")
        td.para(
            r"Los identificadores de nodo del usuario "
            r"(\texttt{node\_id}) pueden tener huecos tras borrados "
            r"(p.ej.\ $\{1, 5, 50\}$). Para evitar índices inválidos en "
            r"$\mathbf{K}$, EduFEM construye un mapa ordinal "
            r"\texttt{node\_index\_map}: cada \texttt{node\_id} se "
            r"asocia con su posición en \texttt{sorted(nodes.keys())}, "
            r"y los GDLs del nodo $n$ son:"
        )
        td.equation(
            r"\mathrm{GDL}_x(n) = 2 \cdot \mathrm{idx}(n), \qquad "
            r"\mathrm{GDL}_y(n) = 2 \cdot \mathrm{idx}(n) + 1"
        )
        td.para(
            rf"En este modelo, $\mathbf{{K}}$ tiene tamaño "
            rf"${proj.total_dof} \times {proj.total_dof}$ "
            rf"($2 \cdot N_{{\text{{nodos}}}}$), y \textbf{{no}} "
            rf"$2 \cdot \max(\text{{node\_id}})$. La tabla siguiente "
            rf"explicita la correspondencia para los nodos del modelo."
        )
        idx_map = proj.node_index_map
        rows = [
            [str(nid), str(idx_map[nid]),
             str(2 * idx_map[nid]), str(2 * idx_map[nid] + 1)]
            for nid in sorted(proj.nodes.keys())[:20]
        ]
        if len(proj.nodes) > 20:
            rows.append([r"\ldots", r"\ldots", r"\ldots", r"\ldots"])
        self._longtable(
            headers=[r"\texttt{node\_id}", "Índice ordinal",
                     r"GDL$_x$", r"GDL$_y$"],
            rows=rows, col_align="rrrr",
        )

        # Mapeo LM del showcase
        if showcase_id is not None:
            td.subsection_numbered(
                rf"Mapeo LM del elemento $E_{{{showcase_id}}}$"
            )
            elem_data = sol.get("element_data", {}).get(showcase_id, {})
            dof_indices = elem_data.get("dof_indices", [])
            elem = proj.elements.get(showcase_id)
            if elem is not None and dof_indices:
                td.para(
                    rf"El vector LM del elemento estrella enumera los "
                    rf"GDLs globales destino de cada GDL local. Su "
                    rf"contribución se suma como "
                    rf"$\mathbf{{K}}[\mathbf{{LM}}, \mathbf{{LM}}] "
                    rf"\mathrel{{+}}= \mathbf{{k}}_e$."
                )
                rows = []
                for i_loc, (nid, dof_g) in enumerate(
                        zip([n for n in elem.node_ids for _ in (0, 1)],
                            dof_indices)):
                    comp = "x" if i_loc % 2 == 0 else "y"
                    rows.append([
                        str(i_loc),
                        f"$N_{{{(i_loc // 2) + 1}}}$",
                        str(nid),
                        f"$u_{comp}$",
                        str(dof_g),
                    ])
                self._longtable(
                    headers=["Loc", "Nodo local", "Nodo global",
                             "Componente", "GDL global"],
                    rows=rows,
                    col_align="ccccc",
                )

        # Matriz K global
        td.subsection_numbered(r"Matriz de rigidez global $\mathbf{K}$")
        K = np.asarray(sol["K"])
        n_dof = K.shape[0]
        if n_dof <= self._K_LITERAL_MAX_DIM:
            td.para(
                r"La matriz se muestra literal con su exponente común "
                r"factorizado:"
            )
            td.raw(r"{\scriptsize")
            td.matrix_factored(K, name=r"\mathbf{K}", sig_digits=3)
            td.raw(r"}")
        else:
            td.para(
                rf"$\mathbf{{K}}$ tiene tamaño "
                rf"${n_dof}\times{n_dof}$, demasiado grande para "
                rf"mostrarse literalmente. Se grafica el patrón "
                rf"$\log_{{10}}|K_{{ij}}|$:"
            )
            try:
                from file_io.figure_export import render_K_heatmap
                fig = render_K_heatmap(K, log_scale=True)
                p = self._save_figure(fig, "K_heatmap")
                if p is not None:
                    td.figure(p,
                              caption=("Patrón de sparsity de "
                                       "$\\mathbf{K}$ en escala "
                                       "logarítmica."),
                              label="fig:K_heatmap",
                              width=r"0.75\textwidth")
            except Exception:
                pass
        # Estadísticas de K
        nnz = int(np.sum(np.abs(K) > NUMERICAL_TOLERANCE_K))
        density = nnz / (n_dof * n_dof) if n_dof > 0 else 0.0
        try:
            cond = float(np.linalg.cond(K))
            cond_str = f"{cond:.3e}" if np.isfinite(cond) else "—"
        except Exception:
            cond_str = "—"
        try:
            bandwidth = self._matrix_bandwidth(K)
        except Exception:
            bandwidth = "—"
        td.values([
            (r"Tamaño", f"{n_dof} × {n_dof}"),
            (r"Entradas no nulas ($|K_{ij}| > 10^{-9}$)", str(nnz)),
            (r"Densidad", f"{density * 100:.3f}\\%"),
            (r"Ancho de banda", str(bandwidth)),
            (r"$\kappa_2(\mathbf{K})$", cond_str),
        ])

        # Vector F
        td.subsection_numbered(r"Vector de fuerzas globales $\mathbf{F}$")
        F = np.asarray(sol["F"])
        td.para(
            r"$\mathbf{F}$ acumula cargas nodales puntuales, fuerzas "
            r"equivalentes de cargas superficiales (Q4: reparto lineal "
            r"$L/2$, $L/2$ para $q$ constante; Q9: reparto cuadrático "
            r"$L/6$, $4L/6$, $L/6$) y fuerzas másicas $\int N_i \rho "
            r"\mathbf{g}\,t\,dA$ si la gravedad está activa. Forma "
            r"compacta con exponente común factorizado:"
        )
        td.raw(r"{\scriptsize")
        td.vector_factored(F, name=r"\mathbf{F}", sig_digits=3, transpose=True)
        td.raw(r"}")
        self._desglose_F(F)

    @staticmethod
    def _matrix_bandwidth(M: np.ndarray) -> int:
        nz = np.argwhere(np.abs(M) > NUMERICAL_TOLERANCE_K)
        if nz.size == 0:
            return 0
        return int(np.max(np.abs(nz[:, 0] - nz[:, 1])))

    def _desglose_F(self, F: np.ndarray) -> None:
        td = self._td
        proj = self._project
        f_nodal_x = sum(ld.fx for ld in proj.nodal_loads.values())
        f_nodal_y = sum(ld.fy for ld in proj.nodal_loads.values())
        ftot_x = float(np.sum(F[0::2]))
        ftot_y = float(np.sum(F[1::2]))
        f_otros_x = ftot_x - f_nodal_x
        f_otros_y = ftot_y - f_nodal_y
        rows = [
            ["Cargas nodales puntuales",
             fmt(f_nodal_x, "force"), fmt(f_nodal_y, "force")],
            ["Otras (superficiales + másicas)",
             fmt(f_otros_x, "force"), fmt(f_otros_y, "force")],
            [r"\textbf{Suma global}",
             rf"\textbf{{{fmt(ftot_x, 'force')}}}",
             rf"\textbf{{{fmt(ftot_y, 'force')}}}"],
        ]
        self._longtable(
            headers=["Fuente", r"$\sum F_x$", r"$\sum F_y$"],
            rows=rows, col_align="lrr",
        )

    # ───────────────────────────────────────────────────────────────────────
    # Aplicación de restricciones (eliminación)
    # ───────────────────────────────────────────────────────────────────────

    def _build_restricciones(self) -> None:
        td = self._td
        sol = self._solution
        td.section_numbered("Aplicación de restricciones")
        td.para(
            r"EduFEM aplica las condiciones de contorno por el "
            r"\textbf{método de eliminación} (implementación: "
            r"\texttt{fem/solver.py::apply\_boundary\_conditions}). Los "
            r"GDLs restringidos se quitan de filas y columnas de "
            r"$\mathbf{K}$ y de $\mathbf{F}$, formando el sistema "
            r"reducido"
        )
        td.equation(r"\mathbf{K}_{red}\,\mathbf{u}_{red} = \mathbf{F}_{red}")
        td.para(
            r"Si algunas BCs tienen valores prescritos no nulos "
            r"($u_x$ o $u_y$ diferentes de cero), su contribución se "
            r"transfiere al lado derecho: $\mathbf{F}_{red} "
            r"\mathrel{-}= \mathbf{K}[\text{free}, \text{restr}]\,"
            r"\mathbf{u}_{pre}[\text{restr}]$. Esto preserva la simetría "
            r"y positividad de $\mathbf{K}_{red}$."
        )
        n_total = len(sol["u"])
        n_libres = len(sol["free_dofs"])
        n_restr = len(sol["restrained_dofs"])
        td.values([
            ("GDL totales", str(n_total)),
            ("GDL restringidos", str(n_restr)),
            ("GDL libres (resueltos)", str(n_libres)),
            (r"Tamaño de $\mathbf{K}_{red}$", f"{n_libres} × {n_libres}"),
        ])

    # ───────────────────────────────────────────────────────────────────────
    # Solución del sistema
    # ───────────────────────────────────────────────────────────────────────

    def _build_solucion(self) -> None:
        td = self._td
        proj = self._project
        sol = self._solution
        td.section_numbered("Solución del sistema y reacciones")

        if self._has_narrative:
            td.para(
                r"El sistema reducido se resuelve por factorización de "
                r"\textbf{Cholesky} $\mathbf{K}_{red} = \mathbf{L}\,"
                r"\mathbf{L}^T$ vía LAPACK POSV "
                r"(\texttt{scipy.linalg.solve} con "
                r"\texttt{assume\_a='pos'}). $\mathbf{K}_{red}$ es "
                r"simétrica definida positiva tras eliminar los GDLs "
                r"restringidos, condición que Cholesky aprovecha para "
                r"costar $\sim\!\tfrac{1}{6}n_{libres}^{\,3}$ flops "
                r"(la mitad que LU general) sin requerir pivoteo. Si "
                r"$\mathbf{K}_{red}$ no fuera SPD —p.ej.\ por elementos "
                r"plegados o restricciones insuficientes— la "
                r"factorización falla limpiamente."
            )
            try:
                K = np.asarray(sol["K"])
                kappa = float(np.linalg.cond(K))
                kappa_str = f"{kappa:.3e}"
            except Exception:
                kappa_str = "—"
            td.values([
                (r"Algoritmo", r"Cholesky $\mathbf{L}\mathbf{L}^T$ (LAPACK POSV)"),
                (r"Complejidad", r"$\sim \tfrac{1}{6}n_{libres}^{\,3}$ flops"),
                (r"$\kappa_2(\mathbf{K})$", kappa_str),
            ])

        u = sol["u"]
        R = sol["reactions"]
        n_total = len(u)

        td.subsection_numbered(
            "Vector de desplazamientos $\\mathbf{u}$"
        )
        if self._has_narrative:
            td.para(
                r"Tras resolver $\mathbf{u}_{red}$, EduFEM reconstruye "
                r"el vector global $\mathbf{u}$ reinsertando los valores "
                r"prescritos en los GDLs restringidos."
            )
        u_arr = np.asarray(u)
        td.raw(r"{\scriptsize")
        td.vector_factored(u_arr, name=r"\mathbf{u}", sig_digits=3,
                           transpose=True)
        td.raw(r"}")
        self._tabla_desplazamientos(u)

        td.subsection_numbered("Reacciones en los apoyos")
        if self._has_narrative:
            td.para(
                r"Las reacciones se calculan como "
                r"$\mathbf{R} = \mathbf{K}\,\mathbf{u} - \mathbf{F}$ y "
                r"son no nulas únicamente en los GDLs restringidos."
            )
        R_arr = np.asarray(R)
        td.raw(r"{\scriptsize")
        td.vector_factored(R_arr, name=r"\mathbf{R}", sig_digits=3,
                           transpose=True)
        td.raw(r"}")
        self._tabla_reacciones(R)

        td.subsection_numbered("Verificación de equilibrio global")
        if self._has_narrative:
            td.para(
                r"$\sum \mathbf{F}_{ext} + \sum \mathbf{R} = \mathbf{0}$ "
                r"debe cumplirse por dirección. Un residuo $>10^{-6}$ "
                r"relativo a las cargas sugiere mal condicionamiento, "
                r"BCs inconsistentes o tolerancia insuficiente."
            )
        self._tabla_verificacion_equilibrio(R)

    def _tabla_desplazamientos(self, u) -> None:
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
                self._fmt_signed(ux),
                self._fmt_signed(uy),
                f"{umag:.5e}",
            ])
        self._longtable(
            headers=["Nodo", r"$u_x$", r"$u_y$", r"$|u|$"],
            rows=rows, col_align="rrrr",
        )

    def _tabla_reacciones(self, R) -> None:
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
        rows.append([
            r"\textbf{Suma}",
            rf"\textbf{{{fmt(sum_rx, 'force')}}}",
            rf"\textbf{{{fmt(sum_ry, 'force')}}}",
        ])
        self._longtable(
            headers=["Nodo", r"$R_x$", r"$R_y$"],
            rows=rows, col_align="rrr",
        )

    def _tabla_verificacion_equilibrio(self, R) -> None:
        proj = self._project
        Fx_aplicada = sum(ld.fx for ld in proj.nodal_loads.values())
        Fy_aplicada = sum(ld.fy for ld in proj.nodal_loads.values())
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
             f"{residuo_x:.3e}"],
            ["Y", fmt(Fy_aplicada, "force"), fmt(Ry_total, "force"),
             f"{residuo_y:.3e}"],
        ]
        self._longtable(
            headers=["Dirección", "Cargas aplicadas", "Reacciones", "Residuo"],
            rows=rows, col_align="crrr",
        )

    # ───────────────────────────────────────────────────────────────────────
    # Post-proceso de tensiones
    # ───────────────────────────────────────────────────────────────────────

    def _build_post_proceso(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Tensiones (post-proceso)")
        if self._has_narrative:
            td.para(
                r"EduFEM recorre la cadena estándar de post-proceso "
                r"(implementación: \texttt{fem/stress.py}):"
            )
            td.equation(
                r"\mathbf{u} \to \boldsymbol{\varepsilon}_{PG} = "
                r"\mathbf{B}\,\mathbf{u}_e \to "
                r"\boldsymbol{\sigma}_{PG} = \mathbf{D}\,"
                r"\boldsymbol{\varepsilon}_{PG} \to "
                r"\boldsymbol{\sigma}_{nodo} = \mathbf{E}\,"
                r"\boldsymbol{\sigma}_{PG} \to "
                r"\boldsymbol{\sigma}_{prom} \to "
                r"(\sigma_1,\sigma_2,\sigma_{VM})"
            )
            td.para(
                r"Las tensiones se calculan primero en los \emph{puntos "
                r"de Gauss} (los mismos puntos donde se integra "
                r"$\mathbf{k}_e$) porque allí son \emph{superconvergentes} "
                r"—el error decae a $O(h^{p+1})$ frente a $O(h^p)$ del "
                r"resto del elemento (Barlow 1976)."
            )
            td.para(
                r"La matriz de extrapolación $\mathbf{E}$ es la "
                r"inversa de $\mathbf{N}_p$, evaluada con las funciones "
                r"de forma en los PG. Para Q4 existe forma cerrada con "
                r"factor $\sqrt{3}$; para Q9 se construye numéricamente "
                r"y se cachea a nivel de módulo "
                r"(\texttt{\_q9\_extrapolation\_matrix})."
            )
            td.para(
                r"Un nodo compartido por $k$ elementos recibe $k$ "
                r"tensiones extrapoladas distintas (el campo de tensiones "
                r"MEF es discontinuo entre elementos). EduFEM aplica "
                r"\textbf{promedio aritmético}:"
            )
            td.equation(
                r"\sigma_n^{\,prom} = \frac{1}{k_n}\sum_{e \in "
                r"\mathcal{E}_n} \sigma_n^{(e)}"
            )
            td.para(
                r"Las \textbf{tensiones principales} y la "
                r"\textbf{tensión equivalente de von Mises} se computan "
                r"por nodo a partir del tensor promediado:"
            )
            td.equation(
                r"\sigma_{1,2} = \frac{\sigma_x+\sigma_y}{2} \pm "
                r"\sqrt{\left(\frac{\sigma_x-\sigma_y}{2}\right)^2 + "
                r"\tau_{xy}^{\,2}}"
            )
            td.equation(
                r"\sigma_{VM} = \sqrt{\sigma_x^{\,2} - \sigma_x\sigma_y "
                r"+ \sigma_y^{\,2} + 3\,\tau_{xy}^{\,2}}"
            )

        td.subsection_numbered("Tensiones nodales promediadas")
        if not self._nodal_stresses:
            td.para(r"\emph{Tensiones nodales no disponibles.}")
            return
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
            rows=rows, col_align="rrrrrrr",
        )

    # ───────────────────────────────────────────────────────────────────────
    # Visualización (deformada + contornos + cruces principales)
    # ───────────────────────────────────────────────────────────────────────

    def _build_visualizacion(self) -> None:
        td = self._td
        proj = self._project
        td.section_numbered("Visualización del campo")
        if self._has_narrative:
            td.para(
                r"Los siguientes mapas y la configuración deformada "
                r"replican el aspecto del Post-Proceso interactivo de "
                r"EduFEM con el mismo \emph{colormap JET} sobre fondo "
                r"blanco. La rasterización Gouraud por triángulos (igual "
                r"al \texttt{MeshCanvas}) interpola suavemente los "
                r"valores nodales promediados."
            )

        # Deformada
        try:
            from file_io.figure_export import render_deformed
            self._project.displacements = self._solution["u"]
            fig = render_deformed(proj, self._solution)
            p = self._save_figure(fig, "deformed")
            if p is not None:
                td.subsection_numbered("Configuración deformada")
                td.figure(p,
                          caption=("Configuración deformada (escala "
                                   "automática). Gris discontinuo: "
                                   "geometría original. Verde: "
                                   "deformada."),
                          label="fig:deformed",
                          width=r"0.85\textwidth")
        except Exception:
            pass

        # Contornos: 4 componentes principales
        td.subsection_numbered("Mapas de contornos")
        try:
            from file_io.figure_export import render_contour
            for component in ("sigma_x", "sigma_y", "tau_xy", "von_mises"):
                fig = render_contour(proj, self._solution,
                                     self._nodal_stresses, component)
                p = self._save_figure(fig, f"contour_{component}")
                if p is None:
                    continue
                labels = {
                    "sigma_x": r"$\sigma_x$",
                    "sigma_y": r"$\sigma_y$",
                    "tau_xy": r"$\tau_{xy}$",
                    "von_mises": r"$\sigma_{VM}$",
                }
                td.figure(p,
                          caption=(f"Contorno de {labels[component]} "
                                   f"(valores nodales promediados)."),
                          label=f"fig:contour_{component}",
                          width=r"0.85\textwidth")
        except Exception:
            pass

        # Cruces principales
        td.subsection_numbered(r"Cruces principales $\sigma_1 \perp \sigma_2$")
        if self._has_narrative:
            td.para(
                r"Cada cruz indica la \emph{dirección principal} en el "
                r"centroide del elemento. El brazo $\sigma_1$ apunta en "
                r"$\theta_p$; el $\sigma_2$ es perpendicular. La longitud "
                r"de cada brazo es proporcional a $|\sigma_i|$ "
                r"normalizado al máximo del modelo. Azul: tracción; "
                r"rojo: compresión."
            )
        try:
            from file_io.figure_export import render_principal_crosses
            fig = render_principal_crosses(proj, self._nodal_stresses)
            p = self._save_figure(fig, "principal_crosses")
            if p is not None:
                td.figure(p,
                          caption=("Cruces principales por elemento; "
                                   "azul = tracción, rojo = compresión."),
                          label="fig:principal_crosses",
                          width=r"0.85\textwidth")
        except Exception:
            pass

    # ───────────────────────────────────────────────────────────────────────
    # Apéndices (solo en estilo 'completo')
    # ───────────────────────────────────────────────────────────────────────

    def _build_apendice_a_kes(self, showcase_id: Optional[int]) -> None:
        td = self._td
        proj = self._project
        sol = self._solution
        elem_data = sol.get("element_data", {})
        td.section_numbered("Matrices de rigidez elementales")
        td.para(
            r"Esta sección agrupa $\mathbf{k}_e$ de los elementos no "
            r"desarrollados en el capítulo de procedimiento. La columna "
            r"$\|\mathbf{k}_e\|_F$ permite comparar magnitudes."
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
            if ke.shape[0] > self._KE_LITERAL_PORTRAIT_MAX:
                td.raw(r"\begin{landscape}{\tiny")
                td.matrix_factored(ke, name=rf"\mathbf{{k}}_{{{eid}}}",
                                   sig_digits=2)
                td.raw(r"}\end{landscape}")
            else:
                td.raw(r"{\scriptsize")
                td.matrix_factored(ke, name=rf"\mathbf{{k}}_{{{eid}}}",
                                   sig_digits=3)
                td.raw(r"}")
        if not any_shown:
            td.para(
                r"\emph{El modelo solo tiene un elemento; ya fue "
                r"desarrollado en el capítulo de procedimiento.}"
            )

    def _build_apendice_b_gauss_stresses(self) -> None:
        td = self._td
        td.section_numbered("Tensiones por punto de Gauss")
        if not self._element_stresses:
            td.para(r"\emph{No disponible.}")
            return
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
            td.para(r"\emph{Sin tensiones por PG.}")
            return
        self._longtable(
            headers=["Elem", "PG", r"$\sigma_x$", r"$\sigma_y$",
                     r"$\tau_{xy}$", r"$\sigma_1$", r"$\sigma_2$",
                     r"$\sigma_{VM}$"],
            rows=rows, col_align="ccrrrrrr",
        )

    def _build_apendice_c_vectores_completos(self) -> None:
        td = self._td
        td.section_numbered("Vectores completos $\\mathbf{u}$ y $\\mathbf{R}$")
        u = np.asarray(self._solution["u"])
        R = np.asarray(self._solution["reactions"])
        td.subsection_numbered(r"$\mathbf{u}$ por GDL")
        rows = [[str(i), self._fmt_signed(float(v))] for i, v in enumerate(u)]
        self._longtable(
            headers=["GDL", r"$u_i$"],
            rows=rows, col_align="rr",
        )
        td.subsection_numbered(r"$\mathbf{R}$ por GDL")
        rows = [[str(i), self._fmt_signed(float(v))] for i, v in enumerate(R)]
        self._longtable(
            headers=["GDL", r"$R_i$"],
            rows=rows, col_align="rr",
        )
