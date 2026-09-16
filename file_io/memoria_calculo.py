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
    resume en UNA idea clave (teaser de 1 línea), con tarjetas "entra ·
    fórmula · salida" por capítulo, mapa del cálculo, fórmulas al margen,
    barra de fase en el encabezado, diagnóstico comentado, interpretación
    de resultados y glosario final. Solo 2 cajas "¿por qué?" en todo el
    documento (Gauss y promediado).
  - 'directo': el MISMO procedimiento matricial paso a paso de inicio a fin
    (N → u=Na → J → B → D → integrando → kₑ por elemento, ensamblaje,
    partición de BCs, resolución, recuperación ε→σ por punto de Gauss,
    extrapolación, principales/von Mises con sustitución, diagnóstico y
    resumen), pero SECO: encabezados + fórmula + matriz + resultado clave,
    sin párrafos ni cajas.

El pipeline tiene 9 capítulos (mapean a las fases pre/proc/post, en eco a
los 9 módulos educativos M0..M9): ① Planteo → ② Discretización →
③ Calidad → ④ Formulación elemental → ⑤ Ensamblaje → ⑥ Condiciones de
contorno y solución → ⑦ Post-proceso → ⑧ Diagnóstico y validación →
⑨ Resumen e interpretación.

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
    fmt, fmt_escala,
)

# Tolerancia para considerar "no nulo" en estadísticas de K (nnz, banda).
NUMERICAL_TOLERANCE_K = max(NUMERICAL_TOLERANCE, 1e-9)

from education.components.theory_builder import TheoryDoc


class MemoriaCalculoError(RuntimeError):
    """Error elevado por el generador con un mensaje accionable para el usuario."""


class PdflatexNotFoundError(MemoriaCalculoError):
    """Subtipo específico: no se encontró ``pdflatex`` en el PATH.

    La GUI lo distingue de un fallo de compilación genérico para ofrecer un
    diálogo con botón de descarga de MiKTeX (ver
    ``gui.dialogs.pdflatex_missing_dialog``). Hereda de ``MemoriaCalculoError``
    para que los ``except MemoriaCalculoError`` existentes lo sigan capturando.
    """


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
                             style=style)

    _progress("Construyendo capítulos", 0.15)
    memoria.build()

    _progress("Compilando con pdflatex", 0.55)
    try:
        memoria.compile(filepath_no_ext, keep_tex=keep_tex)
    except FileNotFoundError as e:
        import platform
        _os = platform.system()
        if _os == "Windows":
            _hint = ("Reinstalá EduFEM con el instalador completo (trae su "
                     "propio TeX) o instalá MiKTeX desde https://miktex.org")
        elif _os == "Darwin":
            _hint = "Instalá MacTeX desde https://tug.org/mactex/"
        else:
            _hint = ("Instalá TeX Live (en Debian/Ubuntu: "
                     "sudo apt install texlive-latex-base texlive-latex-extra)")
        raise PdflatexNotFoundError(
            "No se encontró pdflatex: falta la carpeta 'texlive' que acompaña "
            "al programa y no hay una distribución TeX en el PATH.\n"
            f"{_hint} y volvé a exportar.\n"
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

    # Tope de GDL para mostrar K literal. Por encima va el patrón de
    # dispersión. NO subirlo: lo que manda no es `MaxMatrixCols` sino el
    # ancho de la hoja — una K de 22 o 24 columnas se sale del papel aun en
    # `\tiny` (ver `_mostrar_matriz_K`).
    _K_LITERAL_MAX_DOF = 18

    # Ancho máximo de una matriz emitida de una sola pieza. Por encima se
    # parte en bloques de columnas (`TheoryDoc.matrix_blocks`): 18 columnas
    # no entran en A4 portrait ni con el `arraycolsep` al mínimo.
    _MATRIX_INLINE_MAX_COLS = 12

    # Umbral de rango dinámico de los vectores globales (F, u, R). Alto a
    # propósito: ver `_vector_compacto`.
    _VECTOR_FACTOR_THRESHOLD = 1e12

    # Tope de GDL para emitir un vector global ENTERO. Por encima se muestra
    # un extracto. `equation*` NO admite salto de página, así que un vector
    # de 8450 GDL (Cook Q9 32×32, un ejemplo del propio menú Ayuda) se
    # convertía en una caja indivisible de 705 renglones: pdflatex reportaba
    # `Overfull \vbox (6010 pt too high)`, unos 2,1 m de números impresos
    # fuera de la hoja, invisibles e irrecuperables. El límite medido son
    # ~68 renglones de 12 entradas (~820 GDL); 120 deja margen de sobra.
    _VECTOR_LITERAL_MAX_DOF = 120

    # Tope de filas de las tablas de volcado. Ver `_longtable_topeada`.
    _TABLA_MAX_FILAS = 40

    # Margen lateral de la hoja. Más angosto que el de la Teoría (2,2 cm):
    # acá el ancho lo piden las tablas. Ver `_configure_preamble`.
    MARGEN_LATERAL = "1.5cm"

    def __init__(self, project, solution, element_stresses, nodal_stresses,
                 *, mesh_diagram=None, contour_figures=None,
                 style: str = "educativo"):
        self._project = project
        self._solution = solution
        self._element_stresses = element_stresses or {}
        self._nodal_stresses = nodal_stresses or {}
        self._mesh_diagram = mesh_diagram
        self._contour_figures = dict(contour_figures) if contour_figures else {}
        self._style = style if style in self.STYLES else "educativo"
        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None
        # Caches: la calidad de malla y la validación se consultan en varios
        # capítulos (calidad, diagnóstico, resumen). Memoizar evita recorrer
        # los elementos / re-validar 3-4 veces.
        self._mq_cache = None
        self._health_cache = None
        self._units_cache = None
        # Elemento estrella memoizado: las tablas de los capítulos 2 y 3 lo
        # necesitan para priorizar sus nodos (`_nodos_de_interes`) y esos
        # capítulos se construyen ANTES de la formulación elemental.
        self._showcase_cache = -1
        self._compact_cache = -1

        title = TheoryDoc.escape(self.TITLE)
        subtitle = TheoryDoc.escape(
            self.SUBTITLE_TEMPLATE.format(name=project.project_name)
        )
        # Márgenes laterales de 1,5 cm en vez de los 2,2 cm de la Teoría: este
        # documento lo gobiernan las TABLAS de volcado, no la prosa. La caja
        # de texto pasa de 16,6 a 18 cm (472 -> 512 pt), y esos 40 pt son los
        # que hacían que las tablas de tensiones —ocho columnas con unidades
        # en el encabezado— se salieran por la derecha de la hoja.
        self._td = TheoryDoc(title=title, subtitle=subtitle,
                             margen_lateral=self.MARGEN_LATERAL)
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
        # Q9 tiene B (3×18) y kₑ (18×18); subimos el límite de columnas de
        # amsmath. `matrix_blocks` sube el suyo solo, pero la K literal y las
        # matrices emitidas de una pieza no pasan por ahí: este piso es el que
        # las cubre. El tope real de la K lo pone `_K_LITERAL_MAX_DOF`.
        td.ensure_matrix_cols(26)
        td.raw(r"\pagestyle{fancy}")
        td.raw(r"\fancyhf{}")
        proj_name_safe = TheoryDoc.escape(proj.project_name)
        td.raw(r"\fancyhead[L]{\small Memoria de Cálculo}")
        td.raw(rf"\fancyhead[R]{{\small {proj_name_safe}}}")
        td.raw(r"\fancyfoot[C]{\small \thepage}")
        # Estilo de la ÚLTIMA hoja: el mismo encabezado más el colofón sobre
        # el número de página. Ver `_build_pie`.
        colofon = (rf"\emph{{Documento generado por "
                   rf"{TheoryDoc.escape(APP_NAME)} v{APP_VERSION}.}}")
        td.raw(r"\fancypagestyle{edufemUltima}{"
               r"\fancyhf{}"
               r"\fancyhead[L]{\small Memoria de Cálculo}"
               rf"\fancyhead[R]{{\small {proj_name_safe}}}"
               rf"\fancyfoot[C]{{\scriptsize {colofon}\\[2pt]\small \thepage}}"
               r"}")
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
        # SIN indice impreso (pedido del autor, 2026-09-09): son dos hojas
        # que el alumno no lee. La Memoria se consulta para verificar un
        # numero o seguir un paso, y para eso sirven los marcadores del PDF
        # (hyperref los sigue generando: el visor los muestra al costado y
        # son navegables) y los encabezados de cada hoja, no un sumario
        # impreso. No reintroducir `self._td.toc()`.
        self._build_cap_problema()
        self._build_cap_discretizacion()
        self._build_cap_calidad()
        # `_showcase_id()`, no `_select_showcase_element()`: el memoizado ya
        # corrió en el capítulo 1 y además envuelve el cálculo en un guard.
        # La llamada directa lo repetía —recorriendo todos los elementos por
        # segunda vez— y, si levantaba, la excepción salía de `build()`, que
        # está FUERA del `try` que la traduce a `MemoriaCalculoError`: el
        # alumno recibía la traza cruda en vez del mensaje accionable.
        showcase_id = self._showcase_id()
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
        # ⑧ Diagnóstico y ⑨ Resumen: ambos estilos (datos + veredictos). El
        # educativo añade la prosa/interpretación; el directo, solo las tablas.
        self._build_cap_diagnostico()
        self._build_cap_resumen(showcase_id)
        if self._prose:
            # Glosario de símbolos: subsección final, solo educativo.
            self._build_glosario()
        self._build_pie()

    # ------------------------------------------------------------------
    # Cachés compartidos (calidad de malla + validación del modelo)
    # ------------------------------------------------------------------

    def _mesh_quality(self) -> dict:
        """Evaluación de calidad por elemento, memoizada (la consumen los
        capítulos de calidad, diagnóstico y resumen)."""
        if self._mq_cache is None:
            try:
                from fem.mesh_quality import evaluate_mesh_quality
                self._mq_cache = evaluate_mesh_quality(self._project)
            except Exception:
                self._mq_cache = {}
        return self._mq_cache

    # Superindices de las unidades tecnicas (kgf/cm2, tonf/m2) en LaTeX: el
    # `²` literal es no-ASCII en un string del .tex (regla dura 20).
    _UNIT_TEX = {"²": r"\textsuperscript{2}", "³": r"\textsuperscript{3}"}

    def _units(self) -> dict:
        """Etiquetas de unidad del sistema del proyecto, memoizadas. Misma
        fuente que las tablas del Post y la colorbar del lienzo."""
        if self._units_cache is None:
            try:
                from config.units import get_unit_labels
                self._units_cache = get_unit_labels(self._project.unit_system)
            except Exception:
                self._units_cache = {}
        return self._units_cache

    def _th_unidad(self, simbolo: str, unidad: str) -> str:
        r"""Encabezado de columna con la unidad DEBAJO del símbolo.

        Las dos tablas de tensiones tienen seis columnas rotuladas con un
        símbolo corto —$\sigma_x$— y una unidad tres veces más ancha
        —[kgf/cm\textsuperscript{2}]—. Puestas en línea, esas seis
        repeticiones eran las que empujaban la tabla fuera de la hoja: con
        márgenes de 2,2 cm se salía 89,9 pt y aun con los 1,5 cm de ahora
        seguían sobrando 50. Apilada, la columna mide lo que mide la unidad
        en `\scriptsize` y la tabla entra entera, sin perder el rótulo: el
        encabezado es el que `longtable` repite en cada hoja, así que la
        unidad viaja con la tabla aunque se parta.

        Si el sistema de unidades no define la magnitud, `_u` devuelve
        cadena vacía y el encabezado queda como el símbolo pelado.
        """
        unidad = (unidad or "").strip()
        if not unidad:
            return simbolo
        return (r"\shortstack{" + simbolo + r"\\[1pt]{\scriptsize "
                + unidad + r"}}")

    def _u(self, kind: str) -> str:
        """Sufijo de unidad para un encabezado de tabla: `` [MPa]``.

        `kind` es una clave de `config.units` (`longitud`, `fuerza`,
        `esfuerzo`). Cadena vacia si el sistema no la define — el encabezado
        queda como estaba y la tabla nunca se rompe. Las tablas del Post
        rotulan asi (`sigma_x [MPa]`): sin esto la Memoria era el unico lugar
        donde los numeros llegaban al alumno sin decir en que unidad estan."""
        label = str(self._units().get(kind, "") or "")
        if not label:
            return ""
        for raw, tex in self._UNIT_TEX.items():
            label = label.replace(raw, tex)
        return rf" [{label}]"

    def _u_lineal(self) -> str:
        """Sufijo de la carga superficial: `` [N/mm]`` (fuerza por unidad de
        longitud, igual que el encabezado `q Inicio [N/mm]` del Pre-Proceso)."""
        fuerza = str(self._units().get("fuerza", "") or "")
        longitud = str(self._units().get("longitud", "") or "")
        if not (fuerza and longitud):
            return ""
        return rf" [{fuerza}/{longitud}]"

    def _health(self):
        """HealthReport del modelo, memoizado. None si el validador falla."""
        if self._health_cache is None:
            try:
                from models.model_health import validate_project
                self._health_cache = validate_project(self._project)
            except Exception:
                self._health_cache = None
        return self._health_cache

    def compile(self, filepath_no_ext: str, *, keep_tex: bool = False) -> None:
        """Compila en el mismo directorio temporal (ruta ASCII) donde se
        guardaron las figuras; el PDF se mueve al destino al final."""
        try:
            self._td.compile_to(filepath_no_ext, keep_tex=keep_tex,
                                workdir=self._ensure_tmpdir())
        finally:
            self._cleanup_tmpdir()

    def tex_source(self) -> str:
        """Retorna el código .tex generado (para depuración / inspección)."""
        return self._td.document().dumps()

    # ------------------------------------------------------------------
    # Infraestructura de figuras (PIL)
    # ------------------------------------------------------------------

    def _ensure_tmpdir(self) -> str:
        """Directorio de trabajo con ruta ASCII (figuras + compilación).
        Ver `latex_runtime.safe_workdir_root`: `%TEMP%` lleva el nombre del
        usuario y TeX Live no resuelve rutas con tildes."""
        if self._tmpdir is None:
            from education.components.latex_runtime import make_workdir
            self._tmpdir = make_workdir("edufem_memoria_")
        return self._tmpdir.name

    def _cleanup_tmpdir(self) -> None:
        if self._tmpdir is not None:
            try:
                self._tmpdir.cleanup()
            except Exception:
                pass
            self._tmpdir = None

    def _save_figure(self, img, name: str) -> Optional[str]:
        """Guarda una imagen PIL en el directorio de trabajo y retorna su
        nombre de archivo (relativo: el .tex se compila en ese mismo
        directorio, así ninguna ruta absoluta entra al documento). None si
        falla."""
        if img is None:
            return None
        try:
            tmpdir = self._ensure_tmpdir()
            filename = f"{name}.png"
            img.save(os.path.join(tmpdir, filename))
            return filename
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

        # Ficha a DOS columnas: la de una sola columna gastaba media hoja y
        # obligaba a mandar el mapa del cálculo y el diagrama del modelo a
        # dos hojas más, las tres al 30-45 % de ocupación (medido).
        n_sup = len(getattr(proj, "surface_loads", []) or [])
        info = [
            ("Proyecto", TheoryDoc.escape(proj.project_name)),
            ("Análisis", TheoryDoc.escape(proj.analysis_type)),
            ("Elemento", TheoryDoc.escape(proj.element_type)),
            ("Unidades", TheoryDoc.escape(proj.unit_system)),
            ("Nodos", str(proj.num_nodes)),
            ("Elementos", str(proj.num_elements)),
            ("GDL", str(proj.total_dof)),
            ("Restricciones", str(len(proj.boundary_conditions))),
            ("Cargas nodales", str(len(proj.nodal_loads))),
            ("Cargas superficiales", str(n_sup) if n_sup else "ninguna"),
            ("Fecha", datetime.now().strftime("%d/%m/%Y %H:%M")),
            ("Modelo", rf"\texttt{{{digest}}}"),
        ]
        td.values_2col(info)
        if self._prose:
            td.para(
                r"\emph{Desarrollo paso a paso del análisis por Elementos "
                r"Finitos de este modelo, con la formulación isoparamétrica "
                r"clásica. La teoría es la habitual de los textos del MEF; "
                r"los números son los del modelo.}"
            )
        # El diagrama del modelo y el mapa del cálculo COMPARTEN esta hoja con
        # la ficha (antes cada uno tenía la suya, las tres al 30-45 %). Primero
        # el modelo — es la continuación natural de la ficha — y después el
        # mapa, que hace de puente al capítulo 1.
        self._insertar_diagrama_modelo()
        if self._prose:
            self._insertar_mapa_calculo()
        # SIN `\newpage`: el capítulo 1 arranca donde termine la portada. El
        # salto forzado dejaba media hoja en blanco y no compra nada en un
        # documento que se consulta, no se hojea.

    def _insertar_mapa_calculo(self) -> None:
        """Mapa del cálculo: el gancho de tres líneas más la infografía del
        recorrido. Va EN la portada, no en hoja propia: solo ocupaba el 30 %
        de una hoja. Es además el índice visual que reemplaza al sumario
        impreso que se quitó."""
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
                              r"\boldsymbol\sigma$). Cada estación es un "
                              r"capítulo de esta memoria.",
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

    def _insertar_diagrama_modelo(self) -> None:
        """Diagrama de la malla con nodos, apoyos y cargas. Se emite en los
        DOS estilos: es la única vista del modelo que tiene el lector para
        ubicar los números de nodo que citan todas las tablas, y el
        `directo` la necesita tanto como el `educativo` (antes solo la
        recibía el educativo, y encima en hoja propia al 45 %)."""
        # Tamaño según cuánto hay que meter adentro. Las fuentes de
        # `figure_export` son de tamaño ABSOLUTO en píxeles, así que el cuerpo
        # con que se imprime un número de nodo es `13 px * ancho_pt / ancho_px`:
        # encoger el render Y el ancho de impresión en la misma proporción deja
        # el texto igual de legible (~6,8 pt, el cuerpo del pie de figura) y
        # ahorra alto de hoja. Lo que NO se puede es mostrar el render grande en
        # poco ancho: los números caen a 3,5 pt.
        #   - malla chica: render y figura chicos, comparte hoja con la ficha.
        #   - malla densa: ancho completo, que los rótulos no se pisen.
        chica = self._project.num_nodes <= 40
        px = (560, 420) if chica else (900, 680)
        ancho = r"0.62\textwidth" if chica else r"\textwidth"
        img = self._compacta(self._mesh_diagram) if chica else self._mesh_diagram
        if img is None:
            try:
                from file_io.figure_export import render_mesh_diagram
                img = render_mesh_diagram(self._project,
                                          width=px[0], height=px[1])
            except Exception:
                img = None
        path = self._save_figure(img, "mesh_diagram")
        if path is None:
            return
        self._td.figure(path,
                        caption="Discretización del modelo: nodos, elementos, "
                                "restricciones y cargas aplicadas. Los números "
                                "de nodo son los que citan todas las tablas.",
                        label="fig:mesh", width=ancho)

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
            td.para(
                rf"\textbf{{Hipótesis del modelo}}: material isótropo y "
                rf"homogéneo, comportamiento lineal elástico (ley de Hooke "
                rf"$\boldsymbol\sigma=\mathbf{{D}}\,\boldsymbol\varepsilon$), "
                rf"pequeñas deformaciones y estado de {caso.lower()}. "
                rf"Sistema de unidades: "
                rf"\textbf{{{TheoryDoc.escape(proj.unit_system)}}}."
            )
        else:
            # Directo: hipótesis + tipo de elemento como dato seco (2 filas).
            td.values([("Hipótesis", caso), ("Elemento", elem_desc)])

        self._matriz_D_teorica()
        # La D NUMÉRICA se imprime una sola vez, en la formulación elemental
        # (§ "Matriz constitutiva D del material asignado"), junto a la
        # $\mathbf{k}_e$ que la usa. Acá se emite sólo si ese capítulo no se
        # va a construir, para que el documento nunca quede sin ella.
        if not self._habra_formulacion_elemental():
            self._matriz_D_numerica_si_unico_material()

        # SIN subsección "1.1 Funciones de forma": era el enunciado de las
        # $N_i$ más una caja idéntica, palabra por palabra, a la de la
        # formulación elemental. La fórmula se emite ahora donde están sus
        # números, en "Funciones de forma en los puntos de Gauss".

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
            td.educational_teaser(
                r"Un \textbf{nodo} es un punto donde se calculan los "
                r"desplazamientos (las incógnitas del MEF); un "
                r"\textbf{elemento} es la región sobre la que esas "
                r"incógnitas se interpolan entre sus nodos.",
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
        self._longtable(
            headers=["Material",
                     self._th_unidad("$E$", self._u("esfuerzo")),
                     r"$\nu$",
                     r"$\rho$"],
            rows=rows, col_align="lrrr")

    def _tabla_nodos(self) -> None:
        proj = self._project
        if not proj.nodes:
            self._td.para(r"\emph{Sin nodos definidos.}")
            return
        claves = sorted(proj.nodes.keys())
        rows = [[str(nid), fmt(proj.nodes[nid].x, "length"),
                 fmt(proj.nodes[nid].y, "length")] for nid in claves]
        u = self._u("longitud")
        self._longtable_topeada(
            headers=["ID", self._th_unidad("$X$", u),
                     self._th_unidad("$Y$", u)], rows=rows, col_align="rrr",
            claves=claves, destacadas=self._nodos_de_interes(), que="nodos")

    def _tabla_elementos(self) -> None:
        proj = self._project
        if not proj.elements:
            self._td.para(r"\emph{Sin elementos definidos.}")
            return
        is_q9 = proj.element_type == ELEMENT_Q9
        if is_q9:
            headers = ["ID", "N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8",
                       "N9",
                       self._th_unidad("Espesor", self._u("longitud")),
                       "Material"]
            col_align = "r" * 10 + "rl"
            n_cols = 9
        else:
            headers = ["ID", "N1", "N2", "N3", "N4",
                       self._th_unidad("Espesor", self._u("longitud")),
                       "Material"]
            col_align = "rrrrrrl"
            n_cols = 4
        claves = sorted(proj.elements.keys())
        rows = []
        for eid in claves:
            elem = proj.elements[eid]
            nids = list(elem.node_ids)
            while len(nids) < n_cols:
                nids.append("—")
            row = [str(eid)] + [str(n) for n in nids[:n_cols]]
            row.append(fmt(elem.thickness, "length"))
            row.append(TheoryDoc.escape(elem.material_name))
            rows.append(row)
        # Elementos destacados: el que el documento desarrolla paso a paso y
        # los que tocan el nodo mas solicitado.
        destacados = set()
        eid_star = self._showcase_id()
        if eid_star is not None:
            destacados.add(eid_star)
        _v, n_vmax, _m = self._max_vm()
        if n_vmax is not None:
            destacados.update(e for e, el in proj.elements.items()
                              if n_vmax in el.node_ids)
        # Q9: 12 columnas rozan el ancho de A4 portrait (con la unidad del
        # espesor en el encabezado se pasaban 5,7 pt) -> scriptsize, el mismo
        # tratamiento que la tabla de N en puntos de Gauss.
        if is_q9:
            self._td.raw(r"{\scriptsize")
        self._longtable_topeada(headers=headers, rows=rows,
                                col_align=col_align, compacta=is_q9,
                                claves=claves, destacadas=destacados,
                                que="elementos",
                                criterio="el elemento desarrollado y los que "
                                         "tocan el nodo de mayor von Mises",
                                # En Q9 el CSV del modelo escribe
                                # solo N1..N4: no recupera la
                                # conectividad completa.
                                donde=(None if is_q9
                                       else self._DONDE_MODELO))
        if is_q9:
            self._td.raw(r"}")

    def _tabla_cargas_nodales(self) -> None:
        proj = self._project
        if not proj.nodal_loads:
            self._td.para(r"\emph{Sin cargas nodales definidas.}")
            return
        claves = sorted(proj.nodal_loads.keys())
        rows = [[str(nid), fmt(proj.nodal_loads[nid].fx, "force"),
                 fmt(proj.nodal_loads[nid].fy, "force")]
                for nid in claves]
        u = self._u("fuerza")
        self._longtable_topeada(
            headers=["Nodo", self._th_unidad("$F_x$", u),
                     self._th_unidad("$F_y$", u)], rows=rows,
            col_align="rrr", claves=claves,
            destacadas=self._nodos_de_interes(),
            que="nodos cargados",
            criterio="los del elemento desarrollado, los apoyos y los "
                     "valores extremos")

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
        u = self._u_lineal()
        self._longtable(
            headers=[r"\#", "N inicio", "N fin",
                     self._th_unidad(r"$q_{inicio}$", u),
                     self._th_unidad(r"$q_{fin}$", u), r"$\theta$ (°)"],
            rows=rows, col_align="rrrrrr")

    def _tabla_restricciones(self) -> None:
        proj = self._project
        if not proj.boundary_conditions:
            self._td.para(r"\emph{Sin restricciones definidas. El sistema "
                          r"sería singular sin ellas.}")
            return
        claves = sorted(proj.boundary_conditions.keys())
        rows = [[str(nid),
                 "Sí" if proj.boundary_conditions[nid].restrain_x else "No",
                 "Sí" if proj.boundary_conditions[nid].restrain_y else "No"]
                for nid in claves]
        self._longtable_topeada(
            headers=["Nodo", "Restringe X", "Restringe Y"],
            rows=rows, col_align="rcc", claves=claves,
            destacadas=self._nodos_de_interes(), que="apoyos",
            criterio="los del elemento desarrollado y los puntos de "
                     "carga")

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
        results = self._mesh_quality()
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
        # Orden por calidad ASCENDENTE cuando la malla es grande: el
        # diagnóstico no se lee como censo, y los elementos que pueden
        # invalidar el modelo son los peores. En mallas chicas el orden por
        # id se conserva (el tope no se activa).
        claves = sorted(results.keys())
        if len(claves) > self._TABLA_MAX_FILAS:
            claves = sorted(claves,
                            key=lambda e: results[e]["scaled_jacobian"])
        rows = []
        for eid in claves:
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
        if len(rows) > self._TABLA_MAX_FILAS and self._prose:
            td.para(
                r"\emph{Ordenada por Jacobiano escalado ascendente: los "
                r"primeros son los elementos más distorsionados, que son los "
                r"que pueden invalidar el modelo.}"
            )
        self._longtable_topeada(
            headers=headers, rows=rows, col_align=col_align, claves=claves,
            destacadas={self._showcase_id()}, que="elementos",
            criterio="los más distorsionados (la tabla va ordenada por "
                     "Jacobiano escalado ascendente) y el elemento "
                     "desarrollado",
            donde=None)

    # ------------------------------------------------------------------
    # Capítulo 4: formulación elemental (showcase de UN elemento)
    # ------------------------------------------------------------------

    def _showcase_id(self) -> Optional[int]:
        """`_select_showcase_element` memoizado (se consulta desde varios
        capítulos, incluidos los que se construyen antes)."""
        if self._showcase_cache == -1:
            try:
                self._showcase_cache = self._select_showcase_element()
            except Exception:
                self._showcase_cache = None
        return self._showcase_cache

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

        El element_data del solve productivo viene del motor por lotes
        (`fem/batch.py`) y guarda por elemento solo ke, dof_indices,
        node_coords, B y det_J — sin J, inv_J ni dN. Para el paso-a-paso
        necesitamos la versión completa, que se recalcula aquí solo para
        este único elemento (costo despreciable).

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

    def _habra_formulacion_elemental(self) -> bool:
        """¿El documento va a tener capítulo de formulación elemental?

        La pregunta no es sólo si hay un elemento elegido: `_build_cap_showcase`
        se va sin emitir NADA —ni el encabezado— cuando `_recompute_showcase`
        falla, y ese capítulo es el único que imprime la $\\mathbf{D}$
        numérica. Preguntando sólo por `_showcase_id()` había un caso en que
        el PDF quedaba sin capítulo 4 **y** sin ninguna D con números.
        """
        if self._compact_showcase_ids() is not None:
            return True
        eid = self._showcase_id()
        return eid is not None and self._recompute_showcase(eid) is not None

    def _compact_showcase_ids(self) -> Optional[list[int]]:
        """Si el modelo cabe en modo compacto, devuelve la lista ordenada de
        IDs a desarrollar; si no, devuelve None (modo showcase de un solo
        elemento). El criterio depende del tipo de elemento.

        Memoizado: el capítulo 1 lo consulta para decidir si emite la
        $\\mathbf{D}$ numérica, y recomputar el showcase de cada elemento
        para responder dos veces lo mismo no tiene sentido.
        """
        if self._compact_cache != -1:
            return self._compact_cache
        self._compact_cache = self._calcular_compact_showcase_ids()
        return self._compact_cache

    def _calcular_compact_showcase_ids(self) -> Optional[list[int]]:
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
        # Enunciado de las N_i: SIEMPRE (es la base del isoparamétrico). Vivía
        # en una subsección del capítulo 1, dos páginas antes de sus valores.
        if n_nodes <= 4:
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
                r"$\mathbf{u}=\sum N_i\mathbf{u}_i$). En los puntos de "
                r"Gauss dan el muestreo que arma la integral.",
                phase="proc",
            )
        if gauss_data:
            self._tabla_N_en_gauss(gauss_data, n_nodes, proj.element_type)
        else:
            td.para(r"\emph{Datos de Gauss no disponibles.}")

        # 2b. Campo de desplazamientos interpolado u = N·u_e — base de la
        # relación deformación–desplazamiento ε = B·u_e (paso siguiente).
        heading(r"Campo de desplazamientos interpolado "
                r"$\mathbf{u}=\mathbf{N}\,\mathbf{u}_e$")
        td.equation(
            r"\mathbf{u}(\xi,\eta)=\mathbf{N}(\xi,\eta)\,\mathbf{u}_e,\qquad "
            r"\mathbf{N}=\begin{bmatrix}"
            r"N_1 & 0 & N_2 & 0 & \cdots & N_n & 0\\"
            r"0 & N_1 & 0 & N_2 & \cdots & 0 & N_n\end{bmatrix}"
        )
        td.equation(
            r"\boldsymbol\varepsilon=\partial\mathbf{u}=\mathbf{B}\,"
            r"\mathbf{u}_e,\qquad "
            r"\mathbf{u}_e=[\,u_{x1},u_{y1},\dots,u_{xn},u_{yn}\,]^{T}."
        )
        if self._prose:
            td.educational_teaser(
                r"Las mismas $N_i$ interpolan el desplazamiento dentro del "
                r"elemento a partir de los valores nodales $\mathbf{u}_e$. "
                r"La deformación es su derivada espacial, y el operador que "
                r"la calcula es justamente $\mathbf{B}$.",
                phase="proc",
            )

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
            # `k_e` tambien es singular (los mismos 3 modos de cuerpo
            # rigido), asi que su kappa_2 es ~1e18 en cualquier elemento
            # sano: el rotulo lo dice para que no se lea como un defecto.
            (r"$\kappa_2(\mathbf{k}_e)$ (singular: modos de cuerpo "
             r"rígido)", self._cond_str(ke)),
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
        # Q9: 13 columnas desbordan A4 portrait aun en `\scriptsize` (21,4 pt),
        # así que además va `compacta=True` (tabcolsep 3 pt).
        wide = n_nodes > 4
        if wide:
            self._td.raw(r"{\scriptsize")
        self._longtable(headers=headers, rows=rows,
                        col_align="rrrr" + "r" * n_nodes, compacta=wide)
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
            # Q9: B es 3x18. Hasta el 2026-09-09 iba en hoja APAISADA, una
            # por punto de Gauss: tres hojas al 10 % de ocupacion, y encima
            # `pdflscape` hace `\clearpage` antes y despues, asi que cortaba
            # tambien la hoja portrait anterior. Peor: partia la cadena del
            # paso a paso (J^-1 y dN/dx quedaban en una hoja y la B en otra).
            # Ahora va PARTIDA POR GRUPOS DE NODOS, en portrait y en
            # \scriptsize (mas grande que el \tiny de antes): columnas 1-8 =
            # los 4 nodos de esquina, 9-18 = los 5 nodos internos. El corte
            # es fisico, no aritmetico, y cada par de columnas sigue siendo
            # un nodo (lo dice el teaser del capitulo).
            td.matrix_blocks(B, name=rf"\mathbf{{B}}_{{PG{idx}}}",
                             block_cols=[8, 10], fmt="{:.3g}",
                             size=r"\scriptsize")
        else:
            td.raw(r"{\scriptsize")
            td.matrix(B, name=rf"\mathbf{{B}}_{{PG{idx}}}", fmt="{:.4g}")
            td.raw(r"}")

    def _mostrar_matriz_ke(self, ke: np.ndarray, *, name: str) -> None:
        """kₑ con exponente factorizado, SIEMPRE en portrait.

        La kₑ de Q9 (18×18) iba en hoja apaisada hasta el 2026-09-09, y
        encima no entraba ni ahí: con el rango dinámico disparado por el
        ruido numérico caía a notación científica por entrada y se salía
        185 pt del papel. Corregido el disparador (`RELATIVE_ZERO` en
        `matrix_factored_tex`), con `\\scriptsize` + `arraycolsep` de 2 pt
        mide 427 pt contra los 472 disponibles: entra, se lee más grande
        que el `\\tiny` de antes y queda en la misma hoja que la fórmula de
        cuadratura que la produce, que es lo que el alumno compara.
        """
        td = self._td
        if ke.shape[0] <= self._MATRIX_INLINE_MAX_COLS:
            td.raw(r"{\scriptsize")
            td.matrix_factored(ke, name=name, sig_digits=3)
            td.raw(r"}")
        else:
            # 18 columnas no entran ni con `arraycolsep` al mínimo (medido:
            # 506 pt contra 472 en el ejemplo canónico, y 980 pt en Cook,
            # cuyo rango dinámico real la manda a notación científica). Va
            # partida por mitades de columnas, con UN exponente común para
            # las dos (así se comparan entre sí).
            td.matrix_blocks(ke, name=name, block_cols=9,
                             size=r"\scriptsize", factored=True, sig_digits=3)

    def _integrando_simbolico_q4(self, elem, node_coords, material) -> None:
        td = self._td
        try:
            from fem.symbolic_integrand import SymbolicIntegrandQ4, podar_ruido
            import sympy as sp
        except Exception as e:
            td.para(rf"\emph{{No se pudo cargar la capa simbólica: "
                    rf"{TheoryDoc.escape(str(e))}}}")
            return
        try:
            sim = SymbolicIntegrandQ4(
                E=material.E, nu=material.nu, t=elem.thickness,
                coords=[[float(x), float(y)] for x, y in node_coords[:4]],
            )
            expr = sim.integrand_entry(0, 0, self._project.analysis_type)
            # Poda del ruido de redondeo ANTES de pasarlo a LaTeX. Las
            # coordenadas entran como flotantes, así que en un elemento
            # rectangular —donde la teoría dice cero— sympy arrastraba
            # términos como `1.07e-13*eta` que además le impedían plegar los
            # paréntesis. Medido en Timoshenko Q4: la entrada K_11 pasa de 659
            # a 86 caracteres de LaTeX, o sea de **566 pt impresos fuera de la
            # hoja** dentro de un `equation*` —que no admite corte de línea, y
            # por lo tanto era texto invisible— a un renglón que entra y se
            # lee. `sp.N(..., 6)` recorta de paso los 15 dígitos con que
            # sympy escribe cada coeficiente.
            expr = podar_ruido(expr)
            latex_expr = sp.latex(sp.N(expr, 6))
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
                    rf"{TheoryDoc.escape(str(e))}. Se procede con la "
                    rf"cuadratura numérica.}}")

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
        self._vector_compacto(F, name=r"\mathbf{F}")
        self._desglose_F(F)

    def _mostrar_matriz_K(self, K) -> None:
        """K literal si es chica; patrón de dispersión (PIL) + stats si no.

        El umbral de la rama literal es `_K_LITERAL_MAX_DOF` = 18, **no 24**
        (2026-09-09). Con 24 la Memoria de un modelo Q4 de 11 o 12 nodos —
        22 o 24 GDL, un caso perfectamente normal — emitía un `bmatrix` de
        más de 20 columnas y **pdflatex abortaba**: el alumno no podía
        exportar y recibía el error genérico de compilación (verificado:
        malla 5×1 Q4, 12 nodos, falla; 4×1, 10 nodos, compila). 18 es
        además el techo del modo compacto Q9 (un elemento = 18 GDL), así
        que ninguna matriz del documento pasa de 18 columnas.
        """
        td = self._td
        n_dof = _K_dimension(K)
        if n_dof <= self._K_LITERAL_MAX_DOF:
            if self._prose:
                td.para(r"Por su tamaño moderado se muestra literal, con el "
                        r"exponente común factorizado:")
            if n_dof <= self._MATRIX_INLINE_MAX_COLS:
                td.raw(r"{\scriptsize")
                td.matrix_factored(_K_to_dense(K), name=r"\mathbf{K}",
                                   sig_digits=3)
                td.raw(r"}")
            else:
                td.matrix_blocks(_K_to_dense(K), name=r"\mathbf{K}",
                                 block_cols=9, size=r"\scriptsize",
                                 factored=True, sig_digits=3)
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
            # Rotulo explicito: en este punto del documento K todavia no
            # tiene restricciones, asi que es SINGULAR y su kappa_2 es
            # enorme a proposito. Sin decirlo, el numero parece un
            # defecto del modelo. El que tiene sentido, kappa_2(K_ff),
            # esta en el capitulo de diagnostico.
            rows.append((
                r"$\kappa_2(\mathbf{K})$ antes de restricciones "
                r"(singular: 3 modos de cuerpo rígido)",
                f"{cond:.3e}"))
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
        u = self._u("fuerza")
        self._longtable(
            headers=["Fuente", self._th_unidad(r"$\sum F_x$", u),
                     self._th_unidad(r"$\sum F_y$", u)],
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
        self._vector_compacto(u, name=r"\mathbf{u}",
                              donde=self._DONDE_RESULTADOS)
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
        self._vector_compacto(R, name=r"\mathbf{R}",
                              donde=self._DONDE_RESULTADOS)
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
        claves = sorted(proj.nodes.keys())
        rows = []
        for nid in claves:
            base = 2 * idx_map[nid]
            ux, uy = float(u[base]), float(u[base + 1])
            umag = float(np.hypot(ux, uy))
            rows.append([str(nid), f"{ux:.5e}", f"{uy:.5e}", f"{umag:.5e}"])
        # `uni`, no `u`: en este metodo `u` es el vector de desplazamientos.
        uni = self._u("longitud")
        self._longtable_topeada(
            headers=["Nodo", self._th_unidad("$u_x$", uni),
                     self._th_unidad("$u_y$", uni),
                     self._th_unidad("$|u|$", uni)],
            rows=rows, col_align="rrrr", claves=claves,
            destacadas=self._nodos_de_interes(), que="nodos",
            donde=self._DONDE_RESULTADOS)

    def _tabla_reacciones(self, R) -> None:
        proj = self._project
        if not proj.boundary_conditions:
            self._td.para(r"\emph{Sin reacciones (no hay restricciones).}")
            return
        idx_map = proj.node_index_map
        R = np.asarray(R)
        rows = []
        sum_rx = sum_ry = 0.0
        claves = sorted(proj.boundary_conditions.keys())
        for nid in claves:
            bc = proj.boundary_conditions[nid]
            base = 2 * idx_map[nid]
            rx = float(R[base]) if bc.restrain_x else 0.0
            ry = float(R[base + 1]) if bc.restrain_y else 0.0
            sum_rx += rx
            sum_ry += ry
            rows.append([str(nid), fmt(rx, "force"), fmt(ry, "force")])
        u = self._u("fuerza")
        # La fila SUMA se emite aparte de la tabla topeada: es un total
        # sobre TODOS los apoyos, no una fila mas que se pueda muestrear.
        self._longtable_topeada(
            headers=["Nodo", self._th_unidad("$R_x$", u),
                     self._th_unidad("$R_y$", u)], rows=rows,
            col_align="rrr", claves=claves,
            destacadas=self._nodos_de_interes(), que="apoyos",
            criterio="los del elemento desarrollado, los puntos de "
                     "carga y los valores extremos",
            donde=self._DONDE_RESULTADOS)
        self._td.values([
            (rf"\textbf{{Suma de reacciones}} $R_x$ {u}".strip(),
             rf"\textbf{{{fmt(sum_rx, 'force')}}}"),
            (rf"\textbf{{Suma de reacciones}} $R_y$ {u}".strip(),
             rf"\textbf{{{fmt(sum_ry, 'force')}}}"),
        ])

    def _fuerzas_y_reacciones(self, R):
        """Suma de las fuerzas APLICADAS y de las reacciones, por eje.

        Las aplicadas salen del vector `F` del solver, **no** de
        `project.nodal_loads`: `F` incluye además las fuerzas nodales
        equivalentes de las cargas superficiales y las másicas, y es
        contra `F` que se calculan las reacciones (`R = K u - F`).

        Sumando sólo las cargas nodales, cualquier modelo cargado por
        presión de borde daba `Cargas aplicadas = 0` con las reacciones
        completas: **residuo del 100 %**. La membrana de Cook —un
        ejemplo del propio menú Ayuda— salía con el residuo relativo en
        `1.00e+00` y el veredicto en rojo `Crítico`, o sea que el
        documento declaraba roto un modelo perfectamente sano. El
        residuo real de ese caso es `1.0e-13`. Encima el desglose de F,
        dos apartados antes en la misma hoja, ya imprimía el total
        correcto.
        """
        proj = self._project
        R = np.asarray(R).ravel()
        F = np.asarray(self._solution.get("F")).ravel()
        fx = float(F[0::2].sum())
        fy = float(F[1::2].sum())
        idx = proj.node_index_map
        rx = ry = 0.0
        for nid, bc in proj.boundary_conditions.items():
            base = 2 * idx[nid]
            if bc.restrain_x:
                rx += float(R[base])
            if bc.restrain_y:
                ry += float(R[base + 1])
        return fx, fy, rx, ry

    def _tabla_verificacion_equilibrio(self, R) -> None:
        Fx_aplicada, Fy_aplicada, Rx_total, Ry_total = \
            self._fuerzas_y_reacciones(R)
        rows = [
            ["X", fmt(Fx_aplicada, "force"), fmt(Rx_total, "force"),
             f"{Fx_aplicada + Rx_total:.3e}"],
            ["Y", fmt(Fy_aplicada, "force"), fmt(Ry_total, "force"),
             f"{Fy_aplicada + Ry_total:.3e}"],
        ]
        u = self._u("fuerza")
        self._longtable(
            headers=["Dirección",
                     self._th_unidad("Cargas aplicadas", u),
                     self._th_unidad("Reacciones", u),
                     self._th_unidad("Residuo", u)],
            rows=rows, col_align="crrr")

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
        # Sustitución ε → σ desarrollada en el elemento estrella (valores
        # numéricos por punto de Gauss): completa la cadena del paso a paso.
        if showcase_id is not None and showcase_id in self._element_stresses:
            self._tabla_recuperacion_showcase(showcase_id)
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
                td.para(r"Para Q4 (puntos de Gauss en $\pm 1/\sqrt{3}$, "
                        r"numerados $(-,-)$, $(-,+)$, $(+,-)$, $(+,+)$) la "
                        r"inversa tiene forma cerrada, con entradas "
                        r"$\tfrac{1}{4}(1\pm\sqrt{3})(1\pm\sqrt{3})$:")
            # Misma matriz que usa el motor (fuente unica: fem.stress). Una
            # copia a mano de E_Q4 aqui fue parte del bug corregido el
            # 2026-09-07.
            from fem.stress import extrapolation_matrix
            E_q4 = extrapolation_matrix(4)
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
        # Comparación cuantitativa sin/con promedio en un nodo compartido.
        self._tabla_comparacion_promedio()

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
        from config.settings import ANALYSIS_PLANE_STRAIN as _DP
        if self._project.analysis_type == _DP:
            if self._prose:
                td.para(
                    r"En deformación plana la tensión fuera del plano "
                    r"$\sigma_z=\nu(\sigma_x+\sigma_y)$ no es nula y es la "
                    r"tercera tensión principal: entra en la forma general "
                    r"de von Mises (omitirla subestimaría $\sigma_{VM}$)."
                )
            td.equation(
                r"\sigma_z=\nu(\sigma_x+\sigma_y), \qquad "
                r"\sigma_{VM}=\sqrt{\tfrac12\left[(\sigma_1-\sigma_2)^2"
                r"+(\sigma_2-\sigma_z)^2+(\sigma_z-\sigma_1)^2\right]}"
            )
        else:
            td.equation(
                r"\sigma_{VM}=\sqrt{\sigma_x^{\,2}-\sigma_x\sigma_y+\sigma_y^{\,2}"
                r"+3\tau_{xy}^{\,2}}=\sqrt{\sigma_1^{\,2}-\sigma_1\sigma_2"
                r"+\sigma_2^{\,2}}"
            )
        # Sustitución numérica de σ1, σ2, θp y σVM en el nodo más solicitado.
        self._sustitucion_principales_vm()

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
        deformed_img = self._compacta(self._contour_figures.get("deformed"))
        if deformed_img is None:
            try:
                from file_io.figure_export import render_deformed
                # 620x470 en vez de 900x680: se imprime a 0.62\textwidth y
                # las fuentes de `figure_export` son absolutas en píxeles
                # (ver `_insertar_diagrama_modelo`).
                deformed_img = render_deformed(proj, self._solution,
                                               width=620, height=470)
            except Exception:
                deformed_img = None
        path = self._save_figure(deformed_img, "deformed")
        if path is not None:
            td.figure(path,
                      caption=("Configuración deformada (escala automática). "
                               "Malla original en gris, deformada en verde."),
                      label="fig:deformed", width=r"0.62\textwidth")

        # Contornos
        td.subsection_numbered("Mapas de contornos de tensiones")
        if self._prose:
            td.para(
                r"Los contornos se dibujan con un gradiente bilineal sobre "
                r"cada elemento, a partir de los valores nodales "
                r"promediados. Convención de mapa: \emph{jet} (arcoíris "
                r"clásico de los programas de elementos finitos, ANSYS / "
                r"SAP2000) para todas las componentes — $\sigma_x$, "
                r"$\sigma_y$, $\tau_{xy}$ y $\sigma_{VM}$ —, de modo que "
                r"el contorno de la Memoria coincide con el del visor de "
                r"resultados de la aplicación."
            )
        self._insertar_contornos()

    def _tabla_nodal_stresses(self) -> None:
        claves = sorted(self._nodal_stresses.keys())
        rows = []
        for nid in claves:
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
        u = self._u("esfuerzo")
        self._longtable_topeada(
            headers=["Nodo"] + [self._th_unidad(sym, u) for sym in
                                (r"$\sigma_x$", r"$\sigma_y$",
                                 r"$\tau_{xy}$", r"$\sigma_1$",
                                 r"$\sigma_2$", r"$\sigma_{VM}$")],
            rows=rows, col_align="rrrrrrr", claves=claves,
            destacadas=self._nodos_de_interes(), que="nodos",
            donde=self._DONDE_RESULTADOS)

    # Ancho máximo (px) de una figura pre-renderizada para poder usarla tal
    # cual. Por encima, se re-renderiza al tamaño chico: las fuentes de
    # `figure_export` son absolutas en píxeles y una imagen de 920 px impresa
    # a 231 pt deja los rótulos de la escala en 3,3 pt.
    _FIG_ANCHO_COMPACTO = 640

    def _compacta(self, img):
        """Devuelve `img` si ya es lo bastante chica para imprimirse
        compacta, o None para que quien llama la re-renderice."""
        if img is None:
            return None
        try:
            return img if img.width <= self._FIG_ANCHO_COMPACTO else None
        except Exception:
            return None

    def _insertar_contornos(self) -> None:
        """Los cuatro contornos en una grilla 2x2, no uno debajo del otro.

        Apilados a 0,82\\textwidth ocupaban DOS hojas al 85 %, con los
        rótulos de la escala en 5,5 pt. En grilla entran en una sola hoja y,
        como el render también se achica (520 px en vez de 920 para 231 pt
        de ancho impreso en vez de 387), la resolución por punto tipográfico
        es la misma y los rótulos quedan un poco más grandes, no más chicos.

        Se emite fila por fila: cada `figures_row` es un bloque `[H]`, así
        que si la segunda fila no entra baja sola y el hueco que deja es de
        media figura, no de la grilla entera.
        """
        labels = {
            "sigma_x": r"$\sigma_x$", "sigma_y": r"$\sigma_y$",
            "tau_xy": r"$\tau_{xy}$", "von_mises": r"$\sigma_{VM}$ (von Mises)",
        }
        items = []
        for component in ("sigma_x", "sigma_y", "tau_xy", "von_mises"):
            img = self._compacta(self._contour_figures.get(component))
            if img is None:
                try:
                    from file_io.figure_export import render_contour
                    img = render_contour(self._project, self._solution,
                                         self._nodal_stresses, component,
                                         width=520, height=390)
                except Exception:
                    img = None
            path = self._save_figure(img, f"contour_{component}")
            if path is not None:
                items.append((path, labels[component], component))
        if not items:
            return
        for i in range(0, len(items), 2):
            fila = items[i:i + 2]
            simbolos = " y ".join(lbl for _p, lbl, _c in fila)
            self._td.figures_row(
                [(p, lbl) for p, lbl, _c in fila],
                caption=f"Contorno de {simbolos} (valores nodales "
                        f"promediados).",
                label=f"fig:contornos_{fila[0][2]}",
                width=0.49)

    # ------------------------------------------------------------------
    # Tensiones por punto de Gauss (post-proceso, ambos estilos)
    # ------------------------------------------------------------------

    def _tabla_gauss_stresses_completos(self) -> None:
        """Tensiones crudas por punto de Gauss (antes del promediado).

        Es la tabla más grande del documento y la de menor valor por fila:
        son valores en coordenadas naturales, sin (x, y) que los ubique en
        el modelo. En Cook Q9 32×32 eran 9216 filas, 181 páginas. Cuando la
        malla es grande se muestran el elemento desarrollado paso a paso
        —el único que el alumno puede cruzar contra el capítulo de
        formulación— y los puntos de mayor von Mises, que son los que
        gobiernan el diseño.
        """
        claves, rows = [], []
        for eid in sorted(self._element_stresses.keys()):
            es = self._element_stresses[eid]
            for gp_idx, gs in enumerate(es.get("gauss_stresses", []), start=1):
                claves.append(eid)
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
        # Con malla grande, priorizar el elemento estrella y los de mayor
        # von Mises (no un muestreo ciego: estas filas se leen por valor).
        destacados = {self._showcase_id()}
        if len(rows) > self._TABLA_MAX_FILAS:
            def _vm_max(eid):
                gsl = self._element_stresses[eid].get("gauss_stresses", [])
                return max((g.get("von_mises", 0.0) for g in gsl), default=0.0)
            peores = sorted(self._element_stresses, key=_vm_max,
                            reverse=True)[:3]
            destacados.update(peores)
        u = self._u("esfuerzo")
        self._longtable_topeada(
            headers=["Elem", "PG"] + [self._th_unidad(sym, u) for sym in
                                      (r"$\sigma_x$", r"$\sigma_y$",
                                       r"$\tau_{xy}$", r"$\sigma_1$",
                                       r"$\sigma_2$", r"$\sigma_{VM}$")],
            rows=rows, col_align="ccrrrrrr", claves=claves,
            destacadas=destacados, que="puntos de Gauss",
            criterio="los del elemento desarrollado y los de los tres "
                     "elementos de mayor von Mises",
            donde=None)

    # ------------------------------------------------------------------
    # Recuperación ε → σ y sustituciones numéricas del post-proceso
    # ------------------------------------------------------------------

    def _deformaciones_por_gauss(self, elem_id: int):
        """ε = B(ξ,η)·u_e en cada punto de Gauss del elemento, o None.

        `compute_all_stresses` NO guarda la deformación en `gauss_stresses`
        (solo σ y sus invariantes), así que se recalcula acá con la misma
        cadena que el resto del documento: la `B` de `element_stiffness` y
        los desplazamientos del elemento. Antes se leía `gs.get("strain",
        [0, 0, 0])`, una clave que no existe, y la tabla de recuperación
        imprimía **ε = 0 junto a σ ≠ 0** — matemáticamente imposible y
        contradictorio con la σ = D·ε de la misma página, justo en la tabla
        que existe para verificar esa cadena.
        """
        recomputed = self._recompute_showcase(elem_id)
        if recomputed is None:
            return None
        _ke, gauss_data, _material, _coords = recomputed
        dof_idx = (self._solution.get("element_data", {})
                   .get(elem_id, {}).get("dof_indices"))
        u = self._solution.get("u")
        if dof_idx is None or u is None:
            return None
        try:
            u_e = np.asarray(u)[list(dof_idx)]
            return [np.asarray(g["B"]) @ u_e for g in gauss_data]
        except Exception:
            return None

    def _tabla_recuperacion_showcase(self, elem_id: int) -> None:
        """Sustitución ε = B·u_e → σ = D·ε en cada punto de Gauss del
        elemento estrella. Muestra εx, εy, γxy y las σ resultantes — cierra
        con números la cadena que el capítulo de formulación desarrolló
        simbólicamente."""
        es = self._element_stresses.get(elem_id)
        if not es:
            return
        gauss = es.get("gauss_stresses", [])
        if not gauss:
            return
        deformaciones = self._deformaciones_por_gauss(elem_id)
        td = self._td
        if self._prose:
            td.para(
                rf"Sustitución desarrollada en el \textbf{{elemento {elem_id}}} "
                rf"(el de mayor energía de deformación): en cada punto de "
                rf"Gauss, la $\mathbf{{B}}$ ya calculada y los "
                rf"desplazamientos del elemento dan $\boldsymbol\varepsilon$, "
                rf"y la ley de Hooke la convierte en $\boldsymbol\sigma$."
            )
        # Sin deformaciones no se rellena con ceros: se emite la tabla SIN las
        # columnas de epsilon. Rellenar reintroducía exactamente el bug que
        # esta tabla vino a corregir — epsilon = 0 al lado de sigma != 0,
        # contradiciendo la sigma = D*epsilon de la misma hoja.
        hay_eps = bool(deformaciones) and len(deformaciones) >= len(gauss)
        u = self._u("esfuerzo")
        rows = []
        for k, gs in enumerate(gauss, start=1):
            fila = [f"PG{k}"]
            if hay_eps:
                strain = np.asarray(deformaciones[k - 1]).ravel()
                for i in range(3):
                    v = float(strain[i]) if strain.size > i else 0.0
                    fila.append(f"{v:.4e}")
            fila += [
                fmt(gs.get("sigma_x", 0.0), "stress"),
                fmt(gs.get("sigma_y", 0.0), "stress"),
                fmt(gs.get("tau_xy", 0.0), "stress"),
            ]
            rows.append(fila)
        # Las deformaciones son adimensionales; las tensiones llevan la
        # unidad del sistema del proyecto.
        headers = ["PG"]
        if hay_eps:
            headers += [r"$\varepsilon_x$", r"$\varepsilon_y$",
                        r"$\gamma_{xy}$"]
        headers += [self._th_unidad(r"$\sigma_x$", u),
                    self._th_unidad(r"$\sigma_y$", u),
                    self._th_unidad(r"$\tau_{xy}$", u)]
        self._longtable(headers=headers, rows=rows,
                        col_align="c" + "c" * (3 if hay_eps else 0) + "rrr")
        if not hay_eps and self._prose:
            td.para(
                r"\emph{No se pudieron recuperar las deformaciones de este "
                r"elemento, así que la tabla muestra sólo las tensiones. "
                r"La cadena $\boldsymbol\varepsilon=\mathbf{B}\,\mathbf{u}_e "
                r"\to \boldsymbol\sigma=\mathbf{D}\,\boldsymbol\varepsilon$ "
                r"es la del apartado anterior.}"
            )

    @staticmethod
    def _tension_en_ecuacion(v) -> str:
        """Una tensión que va DENTRO de una ecuación de sustitución.

        `fmt(v, "stress")` fija dos decimales, que es lo correcto en las
        tablas —todas llevan la unidad en el encabezado y así se comparan
        columna a columna—, pero dentro de una sustitución aplasta a
        `-0.00` cualquier tensión menor que 0,005. En un modelo
        adimensional como la membrana de Cook la ecuación salía
        `sigma_VM = sqrt((-0.00)^2-(-0.00)(-0.87)+(-0.87)^2) = 0.86`: un
        operando no nulo impreso como cero, en la fórmula que existe
        justamente para que el alumno rehaga la cuenta.

        Se sigue prefiriendo `fmt` (regla dura 8) y sólo se cae a
        `fmt_escala` —el otro formateador de `config.settings`, que
        conserva cifras significativas en cualquier magnitud— cuando
        `fmt` mentiría.
        """
        try:
            valor = float(v)
        except (TypeError, ValueError):
            return str(v)
        texto = fmt(valor, "stress")
        if valor != 0.0 and float(texto) == 0.0:
            return fmt_escala(valor)
        return texto

    def _sustitucion_principales_vm(self) -> None:
        """Sustitución numérica de σ1, σ2, θp y σVM en el nodo de mayor von
        Mises, a partir de sus componentes promediadas. Demuestra con números
        las fórmulas de los dos subcapítulos anteriores."""
        if not self._nodal_stresses:
            return
        nid = max(self._nodal_stresses,
                  key=lambda n: self._nodal_stresses[n].get("von_mises", 0.0))
        s = self._nodal_stresses[nid]
        sx = float(s.get("sigma_x", 0.0))
        sy = float(s.get("sigma_y", 0.0))
        txy = float(s.get("tau_xy", 0.0))
        avg = 0.5 * (sx + sy)
        R = float(np.hypot(0.5 * (sx - sy), txy))
        s1, s2 = avg + R, avg - R
        theta = 0.5 * float(np.degrees(np.arctan2(2.0 * txy, sx - sy)))
        # Deformacion plana: sigma_z = nu (sx + sy) entra en el von Mises
        # (nu del material del primer elemento que contiene al nodo).
        from config.settings import ANALYSIS_PLANE_STRAIN as _DP
        proj = self._project
        sz = 0.0
        if proj.analysis_type == _DP:
            elem = next((e for e in proj.elements.values()
                         if nid in e.node_ids), None)
            mat = (proj.materials.get(elem.material_name) if elem else None) \
                or next(iter(proj.materials.values()), None)
            sz = float(mat.nu) * (sx + sy) if mat is not None else 0.0
        vm = float(np.sqrt(max(0.5 * ((s1 - s2) ** 2 + (s2 - sz) ** 2
                                      + (sz - s1) ** 2), 0.0)))
        td = self._td
        if self._prose:
            td.para(
                rf"A modo de ejemplo, en el \textbf{{nodo {nid}}} (el de mayor "
                rf"von Mises) las componentes promediadas se sustituyen así:"
            )
        # El planteo y el resultado van en RENGLONES SEPARADOS, por la misma
        # razón que θp y σVM más abajo: `equation*` no parte la línea sola y
        # el `\Rightarrow` no da punto de corte, así que con los seis valores
        # a cuatro cifras y signo la línea se salía 24 pt del margen (medido
        # en Cook Q9). Los números pasan por `fmt(v, "stress")` — los mismos
        # decimales que la tabla de tensiones de la que salen, salvo
        # cuando eso los aplastaria a cero (ver `_tension_en_ecuacion`).
        _s = self._tension_en_ecuacion
        td.equation(
            rf"\sigma_{{1,2}}=\frac{{{_s(sx)}+({_s(sy)})}}{{2}}\pm\sqrt{{"
            rf"\left(\frac{{{_s(sx)}-({_s(sy)})}}{{2}}\right)^2"
            rf"+({_s(txy)})^2}}"
        )
        td.equation(
            rf"\Rightarrow\;\sigma_1={_s(s1)},\qquad \sigma_2={_s(s2)}"
        )
        if abs(sx - sy) > NUMERICAL_TOLERANCE:
            theta_expr = (
                rf"\theta_p=\tfrac12\arctan\!\frac{{2({_s(txy)})}}"
                rf"{{{_s(sx)}-({_s(sy)})}}={fmt(theta, 'angle')}^\circ"
            )
        else:
            theta_expr = rf"\theta_p={fmt(theta, 'angle')}^\circ"
        # theta_p y sigma_VM van en RENGLONES SEPARADOS: juntos con un \qquad
        # la linea se pasaba del margen derecho (Overfull \hbox de 44 pt en el
        # ejemplo canonico, con los cuatro valores a 4 cifras). El \qquad no
        # da punto de corte y `equation*` no parte la linea sola.
        if proj.analysis_type == _DP:
            td.equation(theta_expr + rf",\qquad \sigma_z={_s(sz)}")
            td.equation(
                rf"\sigma_{{VM}}=\sqrt{{\tfrac12\left[({_s(s1)}-({_s(s2)}))^2"
                rf"+({_s(s2)}-({_s(sz)}))^2+({_s(sz)}-({_s(s1)}))^2\right]}}"
                rf"={_s(vm)}"
            )
        else:
            td.equation(theta_expr)
            td.equation(
                rf"\sigma_{{VM}}=\sqrt{{({_s(s1)})^2"
                rf"-({_s(s1)})({_s(s2)})+({_s(s2)})^2}}={_s(vm)}"
            )

    def _tabla_comparacion_promedio(self) -> None:
        """Comparación sin/con promedio en el nodo más compartido: lista las
        k contribuciones extrapoladas, el promedio del pipeline real y el
        salto Δ = máx − mín (indicador de error de malla)."""
        proj = self._project
        if not self._element_stresses or not self._nodal_stresses:
            return
        # Nodo incidente en más elementos (el más compartido).
        incid: dict = {}
        for eid, elem in proj.elements.items():
            ns_list = self._element_stresses.get(eid, {}).get(
                "nodal_stresses", [])
            for nid in elem.node_ids[:len(ns_list)]:
                incid.setdefault(nid, []).append(eid)
        shared = {n: es for n, es in incid.items() if len(es) >= 2}
        td = self._td
        td.subsection_numbered("Comparación sin promedio vs. con promedio")
        if not shared:
            td.para(
                r"\emph{Ningún nodo es compartido por dos o más elementos "
                r"(malla mínima): no hay salto inter-elemental que "
                r"promediar.}")
            return
        nid = max(shared, key=lambda n: len(shared[n]))
        elems = sorted(shared[nid])
        if self._prose:
            td.para(
                rf"El \textbf{{nodo {nid}}} es compartido por {len(elems)} "
                rf"elementos. Cada uno extrapola su propia tensión a ese "
                rf"nodo; el salto entre ellas mide cuán bien la malla "
                rf"captura el gradiente local:")
        comps = (("sigma_x", r"$\sigma_x$"), ("sigma_y", r"$\sigma_y$"),
                 ("tau_xy", r"$\tau_{xy}$"), ("von_mises", r"$\sigma_{VM}$"))
        vals_by_comp = {c: [] for c, _ in comps}
        rows = []
        for eid in elems:
            elem = proj.elements[eid]
            ns_list = self._element_stresses.get(eid, {}).get(
                "nodal_stresses", [])
            try:
                li = list(elem.node_ids).index(nid)
            except ValueError:
                continue
            if li >= len(ns_list):
                continue
            ns_i = ns_list[li]
            row = [f"E{eid}"]
            for c, _ in comps:
                v = float(ns_i.get(c, 0.0))
                vals_by_comp[c].append(v)
                row.append(fmt(v, "stress"))
            rows.append(row)
        avg = self._nodal_stresses.get(nid, {})
        rows.append([r"\textbf{Promedio}"] + [
            rf"\textbf{{{fmt(float(avg.get(c, 0.0)), 'stress')}}}"
            for c, _ in comps])
        rows.append([r"Salto $\Delta$"] + [
            fmt((max(vs) - min(vs)) if vs else 0.0, "stress")
            for c, vs in ((c, vals_by_comp[c]) for c, _ in comps)])
        u = self._u("esfuerzo")
        self._longtable(
            headers=["Origen"] + [self._th_unidad(sym, u) for _, sym in comps],
            rows=rows, col_align="l" + "r" * len(comps))
        # Aviso en AMBOS estilos: es un hecho sobre los números de la tabla,
        # no prosa. La fila "Promedio" es la media aritmética de la columna
        # SOLO en las tres componentes; el $\sigma_{VM}$ se recalcula a
        # partir de esas componentes ya promediadas (no es lineal), así que
        # NO coincide con el promedio de su propia columna. Quien revisara la
        # cuenta encontraba una diferencia sin explicación: 310,06 contra
        # 278,58 en el ejemplo canónico.
        td.para(
            r"\emph{La fila \textbf{Promedio} es la media aritmética de la "
            r"columna en $\sigma_x$, $\sigma_y$ y $\tau_{xy}$. En "
            r"$\sigma_{VM}$ no: se recalcula a partir de las componentes ya "
            r"promediadas, porque von Mises no es una función lineal de "
            r"ellas (ver la fórmula más abajo). Promediar los $\sigma_{VM}$ "
            r"de cada elemento daría un valor distinto y equivocado.}"
        )
        if self._prose:
            td.educational_teaser(
                r"\textbf{Ventaja} del promedio: un único campo continuo, "
                r"apto para contornos. \textbf{Limitación}: oculta el salto "
                r"$\Delta$ — si es grande frente al valor, conviene refinar "
                r"la malla en esa zona.", phase="post")

    # ------------------------------------------------------------------
    # Capítulo 8: diagnóstico y validación del modelo
    # ------------------------------------------------------------------

    # Recomendación de nivel-libro por cada código del validador (sin
    # mencionar internals del software — ver CLAUDE.md).
    _DIAG_RECO = {
        "negative_jacobian":
            r"Reordenar los nodos en sentido antihorario o corregir la "
            r"geometría: con $\det\mathbf{J}\le 0$ el elemento está plegado "
            r"y su rigidez no es válida.",
        "degenerate_element":
            r"Área casi nula o nodos coincidentes; revisar las coordenadas "
            r"del elemento.",
        "no_restraints":
            r"Agregar apoyos: sin restricciones $\mathbf{K}$ es singular "
            r"(3 modos de cuerpo rígido en el plano).",
        "insufficient_restraints":
            r"Restringir al menos 3 GDL independientes para suprimir los "
            r"modos de cuerpo rígido.",
        "bc_orphan_node":
            r"El nodo restringido no pertenece a ningún elemento; eliminar "
            r"la restricción o conectarlo a la malla.",
        "elem_node_missing":
            r"El elemento referencia un nodo inexistente; corregir la "
            r"conectividad.",
        "elem_material_missing":
            r"Asignar un material válido al elemento.",
        "surface_node_missing":
            r"La carga superficial referencia un nodo inexistente; revisar "
            r"sus extremos.",
        "no_elements":
            r"El modelo no tiene elementos: no hay sistema que resolver.",
        "orphan_free_node":
            r"El nodo no pertenece a ningún elemento y conserva GDL libres; "
            r"conectarlo a la malla, restringirlo por completo o eliminarlo.",
        "non_positive_thickness":
            r"El espesor multiplica $\mathbf{k}_e$: con $t=0$ el elemento no "
            r"aporta rigidez y con $t<0$ la aporta con el signo cambiado. "
            r"Asignar un espesor mayor que cero.",
        "non_positive_young":
            r"El módulo de Young debe ser positivo: con $E\le 0$ la matriz "
            r"$\mathbf{D}$ no representa un sólido elástico.",
        "invalid_poisson":
            r"El coeficiente de Poisson de un material isótropo vive en "
            r"$(-1;\,0{,}5)$; en $\nu=0{,}5$ la deformación plana divide por "
            r"$1-2\nu=0$.",
        "negative_density":
            r"Densidad negativa con gravedad activa: la fuerza másica "
            r"$\rho\,\mathbf{g}$ queda invertida. Asignar densidad positiva "
            r"o desactivar la gravedad.",
        "load_orphan_node":
            r"La carga actúa sobre un nodo sin elementos; no contribuye a la "
            r"rigidez.",
        "unused_material":
            r"Material definido pero no asignado a ningún elemento; puede "
            r"eliminarse.",
        "zero_nodal_load":
            r"Carga nodal nula: no aporta al vector $\mathbf{F}$.",
        "zero_surface_load":
            r"Carga superficial nula: no aporta al vector $\mathbf{F}$.",
        "suspicious_young_modulus":
            r"El módulo $E$ cae fuera del rango usual de materiales "
            r"estructurales; verificar las unidades.",
        "suspicious_model_scale":
            r"La extensión del modelo es atípica; verificar el sistema de "
            r"unidades.",
        "gravity_no_density":
            r"Gravedad activa pero densidad nula: la fuerza másica "
            r"$\rho\,\mathbf{g}$ resulta nula.",
    }

    # Los mensajes del validador son los MISMOS que el alumno lee en el
    # reporte de salud en pantalla, donde "ρ·g·V" o "ν = 0,5" es lo que
    # corresponde escribir. Pero de ahi entran a este .tex, y pdflatex no
    # acepta griego ni simbolos matematicos sueltos en modo texto (regla
    # dura 20): un modelo con la gravedad activa y densidad cero generaba
    # un documento que NO compilaba — justo el alumno con un hallazgo era
    # el que no podia exportar su Memoria. La traduccion se hace aca, en
    # el borde, para no empobrecer el texto de la pantalla.
    _UNICODE_A_LATEX = {
        "α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$",
        "δ": r"$\delta$", "ε": r"$\varepsilon$", "θ": r"$\theta$",
        "κ": r"$\kappa$", "λ": r"$\lambda$", "μ": r"$\mu$", "ν": r"$\nu$",
        "ξ": r"$\xi$", "π": r"$\pi$", "ρ": r"$\rho$", "σ": r"$\sigma$",
        "τ": r"$\tau$", "φ": r"$\varphi$", "ω": r"$\omega$",
        "Δ": r"$\Delta$", "Σ": r"$\Sigma$", "Ω": r"$\Omega$",
        "·": r"$\cdot$", "×": r"$\times$", "→": r"$\to$",
        "≤": r"$\le$", "≥": r"$\ge$", "≠": r"$\neq$", "≈": r"$\approx$",
        "±": r"$\pm$", "∞": r"$\infty$", "∫": r"$\int$", "∂": r"$\partial$",
        "√": r"$\sqrt{\;}$", "²": r"\textsuperscript{2}",
        "³": r"\textsuperscript{3}", "°": r"\textdegree{}",
        "…": r"\ldots{}", "—": "---", "–": "--",
    }

    @classmethod
    def _texto_validador(cls, mensaje: str) -> str:
        """Escapa un mensaje del validador y traduce a LaTeX lo que pdflatex
        no sabe leer en modo texto. Las vocales acentuadas y la ñ pasan tal
        cual: `inputenc utf8` las resuelve."""
        texto = str(TheoryDoc.escape(mensaje))
        for caracter, latex in cls._UNICODE_A_LATEX.items():
            if caracter in texto:
                texto = texto.replace(caracter, latex)
        return texto

    @staticmethod
    def _verdict_cell(state: str) -> str:
        """Celda de veredicto coloreada (verde/ámbar/rojo)."""
        m = {"ok": ("edufemPost", "OK"),
             "warn": ("edufemProc", "Revisar"),
             "fail": ("red", "Crítico")}
        col, word = m.get(state, ("edufemInfo", "--"))
        return rf"\textcolor{{{col}}}{{{word}}}"

    def _build_cap_diagnostico(self) -> None:
        td = self._td
        td.section_numbered("Diagnóstico y validación del modelo")
        if self._prose:
            self._chapter_card(
                entra=r"Modelo + solución",
                formula=r"q_{SJ},\ \kappa_2(\mathbf{K}_{ff}),\ "
                        r"\text{equilibrio}",
                sale=r"Anomalías + recomendaciones",
                phase="pre",
            )
            td.educational_teaser(
                r"Un resultado solo es confiable si el modelo que lo produjo "
                r"es sano. Este capítulo reúne las verificaciones "
                r"automáticas: validez geométrica, condicionamiento y "
                r"equilibrio.", phase="pre")

        # (a) Hallazgos del validador.
        td.subsection_numbered("Verificaciones automáticas del modelo")
        report = self._health()
        if report is None:
            td.para(r"\emph{No se pudo ejecutar el validador del modelo.}")
        else:
            from models.model_health import Severity
            issues = report.errors + report.warnings
            if not issues:
                td.para(
                    r"\textcolor{edufemPost}{\textbf{Sin anomalías críticas "
                    r"ni advertencias.}} El modelo pasó todas las "
                    r"verificaciones automáticas.")
            else:
                rows = []
                for iss in issues:
                    is_err = iss.severity == Severity.ERROR
                    sev = r"\textcolor{red}{Error}" if is_err \
                        else r"\textcolor{edufemProc}{Advertencia}"
                    reco = self._DIAG_RECO.get(
                        iss.code, r"Revisar el item indicado.")
                    rows.append([sev, self._texto_validador(iss.message),
                                 reco])
                self._longtable(
                    headers=["Severidad", "Hallazgo", "Recomendación"],
                    rows=rows, col_align=r"lp{4.3cm}p{6.2cm}")

        # (b) Indicadores numéricos con veredicto.
        td.subsection_numbered("Indicadores numéricos")
        self._tabla_indicadores_numericos()

    def _tabla_indicadores_numericos(self) -> None:
        td = self._td
        sol = self._solution
        rows = []

        mq = self._mesh_quality()
        q_sj_vals = [r["scaled_jacobian"] for r in mq.values()]
        ar_vals = [r["robinson_aspect"] for r in mq.values()
                   if np.isfinite(r.get("robinson_aspect", np.inf))]
        if q_sj_vals:
            worst = min(q_sj_vals)
            state = "fail" if worst <= 0 else ("warn" if worst < 0.5 else "ok")
            rows.append([r"Peor Jacobiano escalado $q_{SJ}$", f"{worst:.3f}",
                         self._verdict_cell(state)])
        if ar_vals:
            worst_ar = max(ar_vals)
            state = "fail" if worst_ar > 10 else \
                ("warn" if worst_ar > 4 else "ok")
            rows.append([r"Peor relación de aspecto", f"{worst_ar:.2f}",
                         self._verdict_cell(state)])

        # Sobre K_ff (`K_red`), NO sobre K. La K sin restricciones es
        # singular por construcción —tiene los 3 modos de cuerpo rígido
        # del plano en su nucleo— asi que su kappa_2 da ~1e17 en
        # cualquier modelo y el veredicto salia 'Critico' SIEMPRE, aun
        # en los sanos: el ejemplo canonico Q4 daba 2.39e+17 en rojo
        # cuando su K_ff tiene kappa_2 = 32,6. Un indicador que se
        # enciende siempre no informa nada, y este vive justo en el
        # capitulo que le dice al alumno si puede confiar en el
        # resultado.
        cond = _K_cond(sol.get("K_red"))
        if cond is not None:
            state = "fail" if cond >= 1e12 else \
                ("warn" if cond >= 1e8 else "ok")
            rows.append([
                r"$\kappa_2(\mathbf{K}_{ff})$ (estimado)", f"{cond:.2e}",
                self._verdict_cell(state)])

        res_rel = self._equilibrio_residuo_rel()
        if res_rel is not None:
            state = "ok" if res_rel < 1e-6 else \
                ("warn" if res_rel < 1e-3 else "fail")
            rows.append([r"Residuo de equilibrio relativo", f"{res_rel:.2e}",
                         self._verdict_cell(state)])

        umax, umax_n = self._max_disp()
        if umax is not None:
            rows.append([rf"Desplazamiento máximo $|u|$ (nodo {umax_n})",
                         f"{umax:.4e}", self._verdict_cell("ok")])

        vmax, vmax_n, vmean = self._max_vm()
        if vmax is not None:
            rows.append([rf"$\sigma_{{VM}}$ máxima (nodo {vmax_n})",
                         fmt(vmax, "stress"), self._verdict_cell("ok")])
            if vmean and vmean > 0:
                ratio = vmax / vmean
                state = "warn" if ratio > 5 else "ok"
                rows.append([
                    r"Concentración $\sigma_{VM,\max}/\sigma_{VM,prom}$",
                    f"{ratio:.2f}", self._verdict_cell(state)])

        if not rows:
            td.para(r"\emph{Sin indicadores numéricos disponibles.}")
            return
        self._longtable(headers=["Indicador", "Valor", "Estado"],
                        rows=rows, col_align="lrc")
        if self._prose:
            td.educational_teaser(
                r"\textbf{OK} = dentro de rango usual; \textbf{Revisar} = "
                r"tolerable, conviene controlar o refinar; \textbf{Crítico} "
                r"= corregir antes de confiar en los resultados.",
                phase="pre")

    def _equilibrio_residuo_rel(self):
        """Residuo de equilibrio global relativo: $|\\sum F+\\sum R|/|\\sum F|$
        (o normalizado por las reacciones si no hay cargas externas)."""
        try:
            fx, fy, rx, ry = self._fuerzas_y_reacciones(
                self._solution["reactions"])
            num = float(np.hypot(fx + rx, fy + ry))
            den = float(np.hypot(fx, fy))
            if den < NUMERICAL_TOLERANCE:
                den = float(np.hypot(rx, ry))
            return num / den if den > NUMERICAL_TOLERANCE else None
        except Exception:
            return None

    def _max_disp(self):
        try:
            proj = self._project
            u = np.asarray(self._solution["u"])
            idx = proj.node_index_map
            best_n, best = None, -1.0
            for nid in proj.nodes:
                base = 2 * idx[nid]
                m = float(np.hypot(u[base], u[base + 1]))
                if m > best:
                    best, best_n = m, nid
            return (best, best_n) if best_n is not None else (None, None)
        except Exception:
            return (None, None)

    def _min_disp(self):
        try:
            proj = self._project
            u = np.asarray(self._solution["u"])
            idx = proj.node_index_map
            best_n, best = None, float("inf")
            for nid in proj.nodes:
                base = 2 * idx[nid]
                m = float(np.hypot(u[base], u[base + 1]))
                if m < best:
                    best, best_n = m, nid
            return (best, best_n) if best_n is not None else (None, None)
        except Exception:
            return (None, None)

    def _max_vm(self):
        if not self._nodal_stresses:
            return (None, None, None)
        try:
            vals = {n: float(s.get("von_mises", 0.0))
                    for n, s in self._nodal_stresses.items()}
            best_n = max(vals, key=vals.get)
            mean = float(np.mean(list(vals.values()))) if vals else 0.0
            return (vals[best_n], best_n, mean)
        except Exception:
            return (None, None, None)

    def _stress_extremes(self, comp: str):
        ns = self._nodal_stresses
        if not ns:
            return ((None, None), (None, None))
        vals = {n: float(s.get(comp, 0.0)) for n, s in ns.items()}
        nmax = max(vals, key=vals.get)
        nmin = min(vals, key=vals.get)
        return ((vals[nmax], nmax), (vals[nmin], nmin))

    def _mesh_quality_global(self):
        mq = self._mesh_quality()
        q = [r["scaled_jacobian"] for r in mq.values()]
        if not q:
            return None
        worst = min(q)
        if worst <= 0:
            return r"\textcolor{red}{Inválida (elemento plegado)}"
        if worst < 0.5:
            return r"\textcolor{edufemProc}{Aceptable con distorsión}"
        return r"\textcolor{edufemPost}{Buena}"

    # ------------------------------------------------------------------
    # Capítulo 9: resumen ejecutivo e interpretación
    # ------------------------------------------------------------------

    def _build_cap_resumen(self, showcase_id: Optional[int]) -> None:
        td = self._td
        td.section_numbered("Resumen e interpretación de resultados")
        if self._prose:
            self._chapter_card(
                entra=r"$\mathbf{u}$, $\boldsymbol\sigma$ + diagnóstico",
                formula=r"\max|u|,\ \max\sigma_{VM},\ \dots",
                sale=r"Tabla ejecutiva + zonas críticas",
                phase="post",
            )

        rows = []
        umax, umax_n = self._max_disp()
        if umax is not None:
            rows.append([r"Desplazamiento máximo $|u|$", f"{umax:.4e}",
                         f"nodo {umax_n}"])
        umin, umin_n = self._min_disp()
        if umin is not None:
            rows.append([r"Desplazamiento mínimo $|u|$", f"{umin:.4e}",
                         f"nodo {umin_n}"])
        if self._nodal_stresses:
            for comp, sym in (("sigma_x", r"$\sigma_x$"),
                              ("sigma_y", r"$\sigma_y$"),
                              ("tau_xy", r"$\tau_{xy}$"),
                              ("von_mises", r"$\sigma_{VM}$")):
                (vmx, nmx), (vmn, nmn) = self._stress_extremes(comp)
                if vmx is not None:
                    rows.append([rf"{sym} máximo", fmt(vmx, "stress"),
                                 f"nodo {nmx}"])
                    rows.append([rf"{sym} mínimo", fmt(vmn, "stress"),
                                 f"nodo {nmn}"])
        if showcase_id is not None:
            rows.append([r"Elemento crítico (máx. energía)",
                         f"E{showcase_id}", "--"])
        vmax, vmax_n, _ = self._max_vm()
        if vmax_n is not None:
            rows.append([r"Nodo crítico (máx. $\sigma_{VM}$)",
                         fmt(vmax, "stress"), f"nodo {vmax_n}"])
        report = self._health()
        if report is not None:
            rows.append([r"Errores detectados", str(len(report.errors)),
                         "--"])
            rows.append([r"Advertencias detectadas",
                         str(len(report.warnings)), "--"])
        mq_verdict = self._mesh_quality_global()
        if mq_verdict is not None:
            rows.append([r"Calidad global de la malla", mq_verdict, "--"])

        if rows:
            self._longtable(headers=["Magnitud", "Valor", "Ubicación"],
                            rows=rows, col_align="lrl")
        else:
            td.para(r"\emph{Sin resultados para resumir.}")

        if self._prose:
            partes = []
            if vmax_n is not None:
                partes.append(rf"la tensión equivalente máxima se concentra "
                              rf"en el entorno del \textbf{{nodo {vmax_n}}}")
            if umax_n is not None:
                partes.append(rf"el mayor desplazamiento ocurre en el "
                              rf"\textbf{{nodo {umax_n}}}")
            if partes:
                td.para(
                    r"\textbf{Interpretación}: " + "; ".join(partes) +
                    r". Esas son las zonas a vigilar: conviene revisar si "
                    r"coinciden con apoyos, cambios bruscos de sección o "
                    r"puntos de aplicación de carga, donde es esperable la "
                    r"concentración de esfuerzos.")

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
            # `$\to$`, no la flecha Unicode: regla dura 20. Era la única
            # cadena no-ASCII prohibida que quedaba en todo el documento.
            (r"$\mathbf{J}$", r"Jacobiano del mapeo natural $\to$ físico. "
                              r"Requiere "
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
        """Colofón al PIE de la última hoja, no en el cuerpo.

        Como texto del cuerpo era una raya más una línea en cursiva que, si
        el capítulo ⑨ terminaba cerca del borde inferior, no entraban y se
        llevaban una **hoja entera** para sí solas (medido: Cook Q9 directo,
        hoja 17 con una sola línea). En el pie no ocupa lugar en el flujo, y
        `\\thispagestyle` ejecutado al final del documento le pega a la hoja
        que se está armando, que es la última.
        """
        self._td.raw(r"\thispagestyle{edufemUltima}")

    def _nodos_de_interes(self) -> list:
        """Nodos que el alumno necesita para VERIFICAR, en orden de id.

        Cuando una tabla no entra entera (malla grande), estas son las filas
        que se muestran: los nodos del elemento que el documento desarrolla
        paso a paso, los apoyos, los nodos cargados y los extremos de los
        campos. Es el mismo conjunto para las tres tablas por nodo (nodos,
        desplazamientos y tensiones nodales) para que el alumno pueda cruzar
        coordenada, desplazamiento y tensión del mismo nodo sin buscarlo en
        tres listas distintas.
        """
        proj = self._project
        sel: set = set()
        eid = self._showcase_id()
        if eid is not None and eid in proj.elements:
            sel.update(proj.elements[eid].node_ids)
        sel.update(list(proj.boundary_conditions.keys())[:10])
        sel.update(list(proj.nodal_loads.keys())[:10])
        for sl in list(getattr(proj, "surface_loads", []) or [])[:5]:
            sel.update((sl.node_start, sl.node_end))
        _u, n_umax = self._max_disp()
        _v, n_vmax, _m = self._max_vm()
        sel.update(n for n in (n_umax, n_vmax) if n is not None)
        if self._nodal_stresses:
            for comp in ("sigma_x", "sigma_y", "tau_xy", "von_mises"):
                (_a, n_a), (_b, n_b) = self._stress_extremes(comp)
                sel.update(n for n in (n_a, n_b) if n is not None)
        return sorted(n for n in sel if n in proj.nodes)

    # Descripción por defecto del criterio de destacado: el de las tablas
    # por nodo (`_nodos_de_interes`). Las tablas con otro criterio pasan el
    # suyo por `criterio=`.
    _CRITERIO_NODOS = ("las del elemento desarrollado, los apoyos, los "
                       "puntos de carga y los valores extremos")

    # A dónde mandar al alumno cuando la tabla viene recortada. NO es el
    # mismo destino para todas: `file_io.model_io.export_model_csv` exporta
    # SÓLO el modelo (nodos, elementos, materiales, cargas, restricciones y
    # cargas superficiales). Los resultados no salen por ahí. La nota decía
    # "Archivo, Exportar, Modelo Excel/CSV" debajo de las cinco tablas, así
    # que el alumno que buscaba el desplazamiento de un nodo recortado abría
    # el ZIP y no encontraba ni un número.
    _DONDE_MODELO = ("El listado completo se exporta desde la aplicación "
                     "(Archivo, Exportar, Modelo Excel/CSV)")
    _DONDE_RESULTADOS = ("El listado completo está en la pestaña "
                         "Post-Proceso, en la tabla de Resultados "
                         "Numéricos: Ctrl+A y Ctrl+C la copian entera, "
                         "pegable en una planilla")
    # `donde=None` = esta tabla NO tiene ninguna vista completa en el
    # programa (tensiones por punto de Gauss, métricas de calidad). En ese
    # caso la nota no promete nada: es preferible a mandar a un lugar vacío.

    def _longtable_topeada(self, *, headers: list[str], rows: list[list[str]],
                           col_align: str, claves: list, destacadas,
                           compacta: bool = False,
                           que: str = "filas",
                           criterio: str = _CRITERIO_NODOS,
                           donde: Optional[str] = _DONDE_MODELO) -> None:
        """Tabla que se acota sola cuando la malla es grande.

        `rows` va alineada con `claves` (el id de nodo o elemento de cada
        fila). Si hay más de `_TABLA_MAX_FILAS`, se emiten las filas cuya
        clave está en `destacadas` — las que sirven para verificar — más un
        muestreo uniforme del resto hasta llenar el tope, y una nota que
        dice cuántas se listan de cuántas y dónde está la tabla completa.

        Sin esto, Cook Q9 32×32 (4225 nodos, un ejemplo del menú Ayuda)
        producía un PDF de **493 páginas**, de las cuales 468 eran volcado
        crudo: 24 184 filas de tabla. El documento se consulta para
        verificar un resultado y aprender el procedimiento; para el censo
        completo está la exportación a CSV de la aplicación.
        """
        if len(rows) <= self._TABLA_MAX_FILAS:
            self._longtable(headers=headers, rows=rows, col_align=col_align,
                            compacta=compacta)
            return
        destacadas = set(destacadas or ())
        idx_dest = [i for i, k in enumerate(claves) if k in destacadas]
        idx_dest = idx_dest[:self._TABLA_MAX_FILAS]
        faltan = self._TABLA_MAX_FILAS - len(idx_dest)
        elegidos = set(idx_dest)
        if faltan > 0:
            restantes = [i for i in range(len(rows)) if i not in elegidos]
            if restantes:
                paso = max(1, len(restantes) // faltan)
                elegidos.update(restantes[::paso][:faltan])
        orden = sorted(elegidos)
        self._longtable(headers=headers, rows=[rows[i] for i in orden],
                        col_align=col_align, compacta=compacta)
        # El criterio lo describe QUIEN LLAMA (`criterio`), porque no es el
        # mismo en todas las tablas: las tres tablas por nodo destacan apoyos
        # y puntos de carga (`_nodos_de_interes`), pero la de calidad destaca
        # sólo el elemento desarrollado y la de puntos de Gauss ese más los
        # tres de mayor von Mises. Un texto fijo le decía al alumno que
        # estaba viendo filas que no estaban.
        nota = (rf"Se listan {len(orden)} de {len(rows)} {que}: {criterio}, "
                rf"más un muestreo uniforme del resto.")
        if donde:
            nota += f" {donde}."
        self._td.para(rf"\emph{{{nota}}}")

    # Ancho útil de un renglón de `bmatrix` en `\scriptsize`, en caracteres
    # de celda (sin contar el rótulo `u = 10^{-2} \cdot`, que se lleva unos
    # 60 pt). Calibrado midiendo: 12 columnas de 7 caracteres = 84 caracteres
    # se salían 57,1 pt de los 472 pt de la caja de texto, o sea 73,8
    # caracteres de tope. 72 deja margen.
    _RENGLON_MAX_CARACTERES = 72

    def _columnas_por_renglon(self, v) -> int:
        """Cuántas entradas del vector entran por renglón.

        No es un número fijo: desde que los decimales se eligen para que
        ninguna entrada se imprima como cero (`TheoryDoc._decidir_formato`),
        una celda puede medir 5 o 9 caracteres según el modelo, y 12 columnas
        de las anchas se salen del papel.
        """
        ancho = self._td.cell_width(
            np.asarray(v).ravel(), sig_digits=3,
            dynamic_range_threshold=self._VECTOR_FACTOR_THRESHOLD)
        return max(6, min(12, self._RENGLON_MAX_CARACTERES // max(ancho, 1)))

    def _vector_compacto(self, v, *, name: str,
                         donde: Optional[str] = None) -> None:
        """Vista compacta de un vector global (F, u, R) que SIEMPRE entra.

        Los tres vectores del documento se emiten con el exponente común
        factorizado. La factorización se fuerza (`dynamic_range_threshold`
        alto) porque el fallback a notación científica por entrada — 9
        caracteres contra 5 — es justamente el formato que no cabe: el
        vector `u` de un Q9 de 25 nodos se salía **259 pt** del papel, o sea
        que un tercio de cada renglón se imprimía fuera de la hoja.

        Las entradas por renglón NO son 12 fijas: las decide
        `_columnas_por_renglon` según lo que mida la celda, porque los
        decimales se eligen para que ninguna entrada real se imprima como
        cero y una celda ancha entra menos veces.

        El detalle por nodo que sigue (`_tabla_desplazamientos`,
        `_tabla_reacciones`) viene **topeado** en mallas grandes, y detrás
        de `F` lo que hay es un desglose agregado, no una tabla por GDL. Por
        eso el destino del listado completo lo pasa quien llama (`donde`):
        para `u` y `R` es la tabla del Post-Proceso; para `F` **no hay
        ninguno**, y entonces la nota no promete nada.
        """
        a = np.asarray(v).ravel()
        td = self._td
        cols = self._columnas_por_renglon(a)
        if a.size > self._VECTOR_LITERAL_MAX_DOF:
            # Extracto: primeras y últimas 12 entradas. El vector completo no
            # cabe en una hoja y `equation*` no se puede partir; el valor de
            # cada GDL vive en la tabla por nodo que sigue.
            k = 12
            td.raw(r"{\scriptsize")
            # Dos bloques cortos, cada uno por `vector_factored` (que
            # factoriza y trocea): 24 entradas en una sola linea manual se
            # salian 137 pt del margen.
            td.vector_factored(
                a[:k], name=rf"{name}_{{1..{k}}}", sig_digits=3,
                transpose=True,
                dynamic_range_threshold=self._VECTOR_FACTOR_THRESHOLD,
                max_cols_per_line=cols)
            td.equation(rf"\cdots\quad ({a.size}\ \text{{GDL en total}})")
            td.vector_factored(
                a[-k:], name=rf"{name}_{{{a.size - k + 1}..{a.size}}}",
                sig_digits=3, transpose=True,
                dynamic_range_threshold=self._VECTOR_FACTOR_THRESHOLD,
                max_cols_per_line=cols)
            td.raw(r"}")
            if self._prose:
                # NO prometer "la tabla por nodo que sigue": detrás de F hay
                # un desglose de tres filas agregadas, y la de u y R viene
                # topeada en mallas grandes (`_longtable_topeada`). Lo que sí
                # está siempre completo es la exportación a CSV.
                nota = (rf"Se muestran las primeras y las últimas {k} "
                        rf"entradas de las {a.size}: alcanzan para ver el "
                        rf"orden de magnitud y dónde están los ceros.")
                if donde:
                    nota += f" {donde}."
                td.para(rf"\emph{{{nota}}}")
            return
        td.raw(r"{\scriptsize")
        td.vector_factored(
            a, name=name, sig_digits=3, transpose=True,
            dynamic_range_threshold=self._VECTOR_FACTOR_THRESHOLD,
            max_cols_per_line=cols,
        )
        td.raw(r"}")

    @staticmethod
    def _count_col_specs(col_align: str) -> int:
        """Cantidad de COLUMNAS que declara un preámbulo de tabla LaTeX.

        No es `len(col_align)`: una columna de párrafo ocupa varios
        caracteres (`p{4.3cm}`) y los separadores (`|`) no ocupan ninguna.
        Contarlas por longitud descartaba en silencio todo preámbulo con
        `p{...}` — el glosario (`lp{10cm}`) y la tabla de diagnóstico
        (`lp{4.3cm}p{6.2cm}`) caían al `l` por defecto, que **no corta
        línea**: sus celdas de texto largo se salían del margen derecho
        (5 `Overfull \\hbox` de hasta 73 pt en la Memoria del ejemplo
        canónico).
        """
        n, i = 0, 0
        while i < len(col_align):
            c = col_align[i]
            if c in "lcr":
                n += 1
                i += 1
            elif c in "pmb" and i + 1 < len(col_align) \
                    and col_align[i + 1] == "{":
                depth, j = 0, i + 1
                while j < len(col_align):
                    if col_align[j] == "{":
                        depth += 1
                    elif col_align[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                n += 1
                i = j + 1
            else:
                i += 1          # separadores (`|`, espacios): no son columna
        return n

    def _longtable(self, *, headers: list[str], rows: list[list[str]],
                   col_align: str, compacta: bool = False) -> None:
        """Tabla larga con encabezado repetido en cada hoja.

        `compacta=True` aprieta la separación entre columnas (`tabcolsep`
        de 6 pt a 3 pt) para las tablas anchas de Q9: la de funciones de
        forma en los 9 puntos de Gauss tiene 13 columnas y se salía del
        margen **aun en `\\scriptsize`** (21,4 pt, cuatro veces por tabla —
        `longtable` mide por separado el encabezado de la primera hoja, el
        de las siguientes, el pie y el cuerpo). Con 3 pt mide 409 pt contra
        los 472 disponibles y el cuerpo sigue en `\\scriptsize`, legible.
        """
        td = self._td
        td.package("longtable")
        td.package("booktabs")
        n_cols = len(headers)
        if any(len(r) != n_cols for r in rows):
            raise ValueError(
                f"longtable: filas con columnas inconsistentes (esperado "
                f"{n_cols}).")
        if self._count_col_specs(col_align) != n_cols:
            col_align = "l" * n_cols
        head_row = " & ".join(rf"\textbf{{{h}}}" for h in headers) + r" \\"
        # El grupo `{` acota el `tabcolsep` a esta tabla. `longtable` ya se
        # centra solo (LTleft/LTright = fill): el `center` que envolvía la
        # tabla no aportaba centrado y sí sumaba `topsep` arriba y abajo de
        # cada una de las ~18 tablas del documento.
        td.raw(r"{" + (r"\setlength{\tabcolsep}{3pt}" if compacta else ""))
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
        # Control de viudas y huérfanas. `longtable` parte donde llegue: la
        # tabla de calidad de un modelo de 4 elementos salía 1 fila al pie de
        # una hoja y 3 en la siguiente, y la de 9 nodos 3 y 6. `\\*` prohíbe
        # el salto DESPUÉS de esa fila, así que vedando los dos primeros y los
        # dos últimos puntos de corte ninguna hoja se queda con menos de tres
        # filas — y en una tabla de hasta 4 filas se vedan todos, o sea que no
        # se parte. No cuesta espacio: el salto se corre un par de filas, no
        # desaparece.
        n_filas = len(rows)
        sin_corte = {0, 1, n_filas - 3, n_filas - 2}
        for i, r in enumerate(rows):
            cierre = r" \\*" if i in sin_corte else r" \\"
            td.raw(" & ".join(r) + cierre)
        td.raw(r"\end{longtable}")
        td.raw(r"}")
