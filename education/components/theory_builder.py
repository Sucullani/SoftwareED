"""
TheoryDoc: helper sobre pylatex.Document con preámbulo estandarizado y
utilidades para secciones, ecuaciones, matrices y tablas de valores.
"""

from __future__ import annotations

from typing import Iterable, Optional

import numpy as np
from pylatex import (
    Document,
    Section,
    Subsection,
    Command,
    NoEscape,
    Package,
)
from pylatex.utils import escape_latex


class TheoryDoc:
    """Envuelve pylatex.Document con helpers para los módulos educativos."""

    def __init__(self, title: str, subtitle: str = ""):
        geometry_options = {
            "margin": "2.2cm",
            "headheight": "14pt",
        }
        self.doc = Document(
            geometry_options=geometry_options,
            documentclass="article",
            document_options=["11pt", "a4paper"],
        )
        self._packages_added: set[str] = set()
        for pkg in ("amsmath", "amssymb", "amsfonts", "bm",
                    "xcolor", "booktabs", "hyperref"):
            self.doc.preamble.append(Package(pkg))
            self._packages_added.add(pkg)
        self.doc.preamble.append(NoEscape(r"\hypersetup{colorlinks=true, linkcolor=blue!60!black}"))
        self.doc.preamble.append(Command("title", NoEscape(title)))
        if subtitle:
            self.doc.preamble.append(Command("author", NoEscape(subtitle)))
        self.doc.preamble.append(Command("date", NoEscape(r"\today")))
        self.doc.append(NoEscape(r"\maketitle"))

    # ---------- estructura ----------
    def section(self, title: str) -> None:
        """Seccion sin numerar (no aparece en TOC por defecto)."""
        self.doc.append(NoEscape(rf"\section*{{{title}}}"))

    def section_numbered(self, title: str) -> None:
        """Seccion numerada automaticamente por LaTeX, aparece en TOC."""
        self.doc.append(NoEscape(rf"\section{{{title}}}"))

    def subsection(self, title: str) -> None:
        """Subseccion sin numerar."""
        self.doc.append(NoEscape(rf"\subsection*{{{title}}}"))

    def subsection_numbered(self, title: str) -> None:
        """Subseccion numerada automaticamente (X.Y), aparece en TOC.

        Usar siempre que la subseccion forme parte del flujo principal
        del documento: el numero permite referencias cruzadas estables y
        permite reordenar capitulos sin reescribir titulos.
        """
        self.doc.append(NoEscape(rf"\subsection{{{title}}}"))

    def para(self, text: str) -> None:
        self.doc.append(NoEscape(text))
        self.doc.append(NoEscape(r"\par\medskip"))

    # ---------- ecuaciones ----------
    def equation(self, latex: str) -> None:
        self.doc.append(NoEscape(r"\begin{equation*}"))
        self.doc.append(NoEscape(latex))
        self.doc.append(NoEscape(r"\end{equation*}"))

    def align(self, lines: Iterable[str]) -> None:
        self.doc.append(NoEscape(r"\begin{align*}"))
        self.doc.append(NoEscape(r" \\ ".join(lines)))
        self.doc.append(NoEscape(r"\end{align*}"))

    # ---------- matrices ----------
    # Convencion de formato: los positivos NO llevan prefijo '+' (solo el '-'
    # de los negativos). La alineacion de columnas la garantiza el entorno
    # bmatrix (cada celda separada por '&' es una columna centrada), no el
    # signo. Ver CLAUDE.md §Memoria de Calculo (formateo numerico).
    @staticmethod
    def matrix_tex(M: np.ndarray, fmt: str = "{:.4g}", name: Optional[str] = None) -> str:
        rows = [" & ".join(fmt.format(x) for x in row) for row in np.asarray(M)]
        body = r" \\ ".join(rows)
        m = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
        if name:
            return rf"{name} = {m}"
        return m

    def matrix(self, M: np.ndarray, name: Optional[str] = None, fmt: str = "{:.4g}") -> None:
        self.equation(self.matrix_tex(M, fmt=fmt, name=name))

    # ---------- matrices y vectores con exponente factorizado ----------
    @staticmethod
    def matrix_factored_tex(
        M: np.ndarray,
        *,
        name: Optional[str] = None,
        sig_digits: int = 3,
        dynamic_range_threshold: float = 1e4,
        tol: float = 1e-30,
    ) -> str:
        """LaTeX de M con un exponente comun 10^p factorizado al frente.

        Pensado para resolver overflow horizontal en matrices con valores
        de magnitud uniforme (K, k_e, vectores de fuerza/desplazamiento).

        Si el rango dinamico max(|x|)/min(|x_nonzero|) supera
        `dynamic_range_threshold`, cae al fallback de notacion cientifica
        por entrada (preserva precision).

        Salida tipica:
            name = 10^{p} \\cdot \\begin{bmatrix} ... \\end{bmatrix}
        """
        A = np.asarray(M, dtype=float)
        if A.ndim == 1:
            A = A.reshape(-1, 1)
        abs_A = np.abs(A)
        mask = abs_A > tol
        if not mask.any():
            body = r" \\ ".join(
                " & ".join("0" for _ in row) for row in A
            )
            m = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
            return rf"{name} = {m}" if name else m

        max_val = float(abs_A[mask].max())
        min_val = float(abs_A[mask].min())
        dyn_range = max_val / min_val if min_val > 0 else float("inf")

        # Fallback: rango dinamico alto -> notacion cientifica por entrada.
        # Sin prefijo '+' en positivos (solo '-' en negativos).
        if dyn_range > dynamic_range_threshold:
            fmt_sci = f"{{:.{sig_digits}e}}"
            rows = [
                " & ".join(fmt_sci.format(float(x)) for x in row)
                for row in A
            ]
            body = r" \\ ".join(rows)
            m = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
            return rf"{name} = {m}" if name else m

        # Factorizacion: elegir p tal que el max normalizado caiga en [1, 10).
        p = int(np.floor(np.log10(max_val)))
        scale = 10.0 ** p
        norm = A / scale
        # Formato con sig_digits decimales (no notacion cientifica - todos
        # los valores normalizados estan en (-10, 10) aprox). Sin '+'.
        decimals = max(0, sig_digits - 1)
        fmt_fixed = f"{{:.{decimals}f}}"
        rows = [
            " & ".join(fmt_fixed.format(float(x)) for x in row)
            for row in norm
        ]
        body = r" \\ ".join(rows)
        bm = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
        # Manejo de p == 0 (sin factor visible) y p == 1 (10 explicit).
        if p == 0:
            inner = bm
        else:
            inner = rf"10^{{{p}}} \cdot {bm}"
        return rf"{name} = {inner}" if name else inner

    def matrix_factored(
        self,
        M: np.ndarray,
        *,
        name: Optional[str] = None,
        sig_digits: int = 3,
        dynamic_range_threshold: float = 1e4,
    ) -> None:
        self.equation(self.matrix_factored_tex(
            M, name=name, sig_digits=sig_digits,
            dynamic_range_threshold=dynamic_range_threshold,
        ))

    @staticmethod
    def vector_factored_tex(
        v: np.ndarray,
        *,
        name: Optional[str] = None,
        sig_digits: int = 3,
        dynamic_range_threshold: float = 1e4,
        transpose: bool = True,
        max_cols_per_line: int = 12,
        tol: float = 1e-30,
    ) -> str:
        """LaTeX de un vector con exponente factorizado.

        Si `transpose=True` muestra el vector como fila + `^T` (compacto,
        ideal para u y F: ocupa 1 linea en vez de N). Si es False, lo
        muestra como columna `[bmatrix]` tradicional.

        Si la cantidad de entradas excede `max_cols_per_line` (default 12),
        chunk-ea el vector en multiples filas de esa anchura — necesario
        para vectores Q9 grandes (50+ GDLs) que de otro modo excederian
        el limite `MaxMatrixCols` de amsmath y romperian la compilacion.

        Comparte la logica de factorizacion con `matrix_factored_tex`.
        """
        a = np.asarray(v, dtype=float).reshape(-1)
        n = a.size
        abs_a = np.abs(a)
        mask = abs_a > tol

        def _build_body(entries: list[str]) -> str:
            """Une `entries` en una sola fila (transpose=True/cor[ Tpdfta)
            o las chunk-ea en multiples filas si exceden el max_cols_per_line.
            Retorna SOLO el body interno del bmatrix (sin envoltura)."""
            if transpose:
                # Una sola fila si entra; chunkear si no.
                if len(entries) <= max_cols_per_line:
                    return " & ".join(entries)
                # Chunkear en filas de max_cols_per_line. Padding con celdas
                # vacias en la ultima para que pylatex no se queje.
                rows: list[str] = []
                for i in range(0, len(entries), max_cols_per_line):
                    chunk = entries[i:i + max_cols_per_line]
                    if len(chunk) < max_cols_per_line:
                        chunk = chunk + [""] * (max_cols_per_line - len(chunk))
                    rows.append(" & ".join(chunk))
                return r" \\ ".join(rows)
            else:
                # Columna tradicional: una entrada por fila.
                return r" \\ ".join(entries)

        def _wrap(body: str) -> str:
            bm = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
            # ^T solo cuando es realmente una fila visualmente (chunkeado o no,
            # mantenemos la convencion de notacion vector-columna).
            if transpose:
                bm = bm + r"^T"
            return bm

        # Caso 1: vector cero.
        if not mask.any():
            entries = ["0" for _ in a]
            m = _wrap(_build_body(entries))
            return rf"{name} = {m}" if name else m

        max_val = float(abs_a[mask].max())
        min_val = float(abs_a[mask].min())
        dyn_range = max_val / min_val if min_val > 0 else float("inf")

        # Caso 2: rango dinamico alto -> notacion cientifica por entrada.
        # Sin prefijo '+' en positivos (solo '-' en negativos).
        if dyn_range > dynamic_range_threshold:
            fmt_sci = f"{{:.{sig_digits}e}}"
            entries = [fmt_sci.format(float(x)) for x in a]
            m = _wrap(_build_body(entries))
            return rf"{name} = {m}" if name else m

        # Caso 3: factorizacion comun de 10^p. Sin '+'.
        p = int(np.floor(np.log10(max_val)))
        scale = 10.0 ** p
        norm = a / scale
        decimals = max(0, sig_digits - 1)
        fmt_fixed = f"{{:.{decimals}f}}"
        entries = [fmt_fixed.format(float(x)) for x in norm]
        bm = _wrap(_build_body(entries))
        if p == 0:
            inner = bm
        else:
            inner = rf"10^{{{p}}} \cdot {bm}"
        return rf"{name} = {inner}" if name else inner

    def vector_factored(
        self,
        v: np.ndarray,
        *,
        name: Optional[str] = None,
        sig_digits: int = 3,
        dynamic_range_threshold: float = 1e4,
        transpose: bool = True,
    ) -> None:
        self.equation(self.vector_factored_tex(
            v, name=name, sig_digits=sig_digits,
            dynamic_range_threshold=dynamic_range_threshold,
            transpose=transpose,
        ))

    # ---------- bloques pedagogicos (educational_box, educational_teaser) ----------
    def educational_teaser(
        self,
        body: str,
        *,
        cross_ref: Optional[str] = None,
        phase: str = "proc",
    ) -> None:
        """Mini-banner pedagogico (1-2 lineas) con una idea clave.

        Caja chica con barra de color de fase a la izquierda. El cuerpo es
        autocontenido: explica el `por que' directamente, sin remitir a otro
        documento. `cross_ref` quedo como parametro opcional por
        compatibilidad — si se pasa, agrega un puntero en italic, pero el
        diseño reformulado (2026-05) NO usa referencias cruzadas circulares.

        Args:
            body: contenido LaTeX de 1-2 lineas. Puede incluir formulas inline.
            cross_ref: opcional. Puntero textual (p.ej. otra seccion). Si es
                       None (recomendado), el teaser se cierra en si mismo.
            phase: "pre" | "proc" | "post" | "info". Controla el color.
        """
        self.package("tcolorbox", options="most")
        if not getattr(self, "_edu_colors_defined", False):
            self.doc.preamble.append(NoEscape(
                r"\definecolor{edufemPre}{HTML}{0D6EFD}"
                r"\definecolor{edufemProc}{HTML}{FD7E14}"
                r"\definecolor{edufemPost}{HTML}{198754}"
                r"\definecolor{edufemInfo}{HTML}{6c757d}"
            ))
            self._edu_colors_defined = True
        color_map = {
            "pre": "edufemPre",
            "proc": "edufemProc",
            "post": "edufemPost",
            "info": "edufemInfo",
        }
        col = color_map.get(phase, "edufemProc")
        # Caja chica (left bar mas grueso para identidad de fase + padding minimo).
        # Sin titulo: el icono lampara hace de marker visual.
        self.doc.append(NoEscape(
            rf"\begin{{tcolorbox}}[enhanced, colback={col}!4!white, "
            rf"colframe={col}!4!white, leftrule=2.5pt, "
            rf"toprule=0pt, bottomrule=0pt, rightrule=0pt, "
            rf"left=8pt, right=6pt, top=3pt, bottom=3pt, "
            rf"borderline west={{2.5pt}}{{0pt}}{{{col}}}]"
        ))
        # Cuerpo autocontenido. Si se pasa cross_ref (legacy), se agrega un
        # puntero textual en italic; el diseño reformulado lo omite.
        tail = ""
        if cross_ref:
            tail = (rf" \, \emph{{\textcolor{{{col}!70!black}}{{$\rightarrow$ "
                    rf"{cross_ref}}}}}")
        self.doc.append(NoEscape(
            rf"\small \textbf{{\textcolor{{{col}}}{{\textsf{{i}}}}}}\,\, "
            rf"{body}{tail}"
        ))
        self.doc.append(NoEscape(r"\end{tcolorbox}"))

    def educational_box(
        self,
        body: str,
        *,
        title: str = r"\textbf{¿Por qué?}",
        phase: str = "proc",
    ) -> None:
        """Banner pedagogico coloreado por fase del MEF.

        Encapsula la pregunta tipica del alumno "¿por que estamos haciendo
        esto?" en una caja `tcolorbox`. Las fases siguen la paleta del
        proyecto (pre/proc/post de `config.settings`).

        Args:
            body: contenido LaTeX del cuerpo (puede incluir formulas).
            title: titulo de la caja (default "¿Por que?").
            phase: "pre" | "proc" | "post" | "info". Controla el color.
        """
        self.package("tcolorbox", options="most")
        # Definicion lazy de los colores en el preambulo.
        if not getattr(self, "_edu_colors_defined", False):
            self.doc.preamble.append(NoEscape(
                r"\definecolor{edufemPre}{HTML}{0D6EFD}"
                r"\definecolor{edufemProc}{HTML}{FD7E14}"
                r"\definecolor{edufemPost}{HTML}{198754}"
                r"\definecolor{edufemInfo}{HTML}{6c757d}"
            ))
            self._edu_colors_defined = True
        color_map = {
            "pre": "edufemPre",
            "proc": "edufemProc",
            "post": "edufemPost",
            "info": "edufemInfo",
        }
        col = color_map.get(phase, "edufemProc")
        self.doc.append(NoEscape(
            rf"\begin{{tcolorbox}}[colback={col}!5!white, "
            rf"colframe={col}!75!black, title={{{title}}}, "
            rf"fonttitle=\bfseries\small, boxrule=0.6pt, "
            rf"left=6pt, right=6pt, top=4pt, bottom=4pt]"
        ))
        self.doc.append(NoEscape(body))
        self.doc.append(NoEscape(r"\end{tcolorbox}"))

    # ---------- valores tabulados ----------
    def values(self, rows: list[tuple[str, str]]) -> None:
        self.doc.append(NoEscape(r"\begin{center}\begin{tabular}{ll}\toprule"))
        for k, v in rows:
            self.doc.append(NoEscape(rf"{k} & {v} \\"))
        self.doc.append(NoEscape(r"\bottomrule\end{tabular}\end{center}"))

    # ---------- acceso al Document ----------
    def document(self) -> Document:
        return self.doc

    # ---------- extensiones para Memoria de Calculo ----------
    def package(self, name: str, options: Optional[str] = None) -> None:
        """Agrega un paquete LaTeX al preambulo si no fue agregado antes.

        Idempotente: llamadas repetidas con el mismo `name` no duplican la
        entrada en el preambulo (pdflatex acepta duplicados con warning,
        pero conviene mantenerlo limpio).
        """
        if name in self._packages_added:
            return
        if options is not None:
            self.doc.preamble.append(Package(name, options=options))
        else:
            self.doc.preamble.append(Package(name))
        self._packages_added.add(name)

    def raw(self, latex: str) -> None:
        """Inserta LaTeX literal sin escape (escape hatch para chapter,
        appendix, newpage, landscape, etc.)."""
        self.doc.append(NoEscape(latex))

    def toc(self) -> None:
        """Inserta tabla de contenidos seguida de salto de pagina."""
        self.doc.append(NoEscape(r"\tableofcontents"))
        self.doc.append(NoEscape(r"\newpage"))

    def figure(self, image_path: str, caption: str = "", label: str = "",
               width: str = r"0.85\textwidth") -> None:
        """Inserta una figura con caption y label opcionales.

        `image_path` debe ser absoluto. Se normaliza a forward-slash porque
        pdflatex bajo Windows interpreta backslash como inicio de macro.
        """
        self.package("graphicx")
        self.package("float")
        path_tex = image_path.replace("\\", "/")
        self.doc.append(NoEscape(r"\begin{figure}[H]\centering"))
        self.doc.append(NoEscape(rf"\includegraphics[width={width}]{{{path_tex}}}"))
        if caption:
            self.doc.append(NoEscape(rf"\caption{{{caption}}}"))
        if label:
            self.doc.append(NoEscape(rf"\label{{{label}}}"))
        self.doc.append(NoEscape(r"\end{figure}"))

    def compile_to(self, filepath_no_ext: str, *, keep_tex: bool = False) -> None:
        """Compila el documento a PDF usando pdflatex.

        `filepath_no_ext` no debe llevar la extension `.pdf` (pylatex la
        agrega). Si la compilacion falla, propaga la excepcion (el caller
        debe atrapar `pylatex.errors.CompilerError` o `FileNotFoundError`
        si pdflatex no esta en el PATH).
        """
        self.doc.generate_pdf(
            filepath_no_ext,
            clean_tex=not keep_tex,
            compiler="pdflatex",
            compiler_args=["-interaction=nonstopmode", "-halt-on-error"],
        )

    @staticmethod
    def escape(s) -> str:
        """Escapa caracteres especiales LaTeX para strings provenientes
        del modelo (project_name, nombres de material, etc.). NO usar
        sobre formulas o LaTeX literal."""
        if s is None:
            return ""
        return escape_latex(str(s))
