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
        self.doc.preamble.append(Package("amsmath"))
        self.doc.preamble.append(Package("amssymb"))
        self.doc.preamble.append(Package("amsfonts"))
        self.doc.preamble.append(Package("bm"))
        self.doc.preamble.append(Package("xcolor"))
        self.doc.preamble.append(Package("booktabs"))
        self.doc.preamble.append(Package("hyperref"))
        self.doc.preamble.append(NoEscape(r"\hypersetup{colorlinks=true, linkcolor=blue!60!black}"))
        self.doc.preamble.append(Command("title", NoEscape(title)))
        if subtitle:
            self.doc.preamble.append(Command("author", NoEscape(subtitle)))
        self.doc.preamble.append(Command("date", NoEscape(r"\today")))
        self.doc.append(NoEscape(r"\maketitle"))

    # ---------- estructura ----------
    def section(self, title: str) -> None:
        self.doc.append(NoEscape(rf"\section*{{{title}}}"))

    def subsection(self, title: str) -> None:
        self.doc.append(NoEscape(rf"\subsection*{{{title}}}"))

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
    @staticmethod
    def matrix_tex(M: np.ndarray, fmt: str = "{:+.4g}", name: Optional[str] = None) -> str:
        rows = [" & ".join(fmt.format(x) for x in row) for row in np.asarray(M)]
        body = r" \\ ".join(rows)
        m = rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"
        if name:
            return rf"{name} = {m}"
        return m

    def matrix(self, M: np.ndarray, name: Optional[str] = None, fmt: str = "{:+.4g}") -> None:
        self.equation(self.matrix_tex(M, fmt=fmt, name=name))

    # ---------- valores tabulados ----------
    def values(self, rows: list[tuple[str, str]]) -> None:
        self.doc.append(NoEscape(r"\begin{center}\begin{tabular}{ll}\toprule"))
        for k, v in rows:
            self.doc.append(NoEscape(rf"{k} & {v} \\"))
        self.doc.append(NoEscape(r"\bottomrule\end{tabular}\end{center}"))

    # ---------- acceso al Document ----------
    def document(self) -> Document:
        return self.doc
