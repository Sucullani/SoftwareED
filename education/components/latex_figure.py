"""
latex_figure: utilidades para renderizar matrices y expresiones LaTeX
directamente en un eje matplotlib usando mathtext (sin compilador externo).
"""

from __future__ import annotations

from typing import Optional, Union

import numpy as np


def _matrix_to_latex(
    matrix,
    fmt: str = "{:+.3g}",
    max_term_len: int = 28,
) -> str:
    """Convierte una matriz (NumPy / SymPy / lista) a string LaTeX
    usando el entorno `bmatrix`. Para matrices SymPy usa sp.latex.
    """
    try:
        import sympy as sp
        if isinstance(matrix, sp.MatrixBase):
            return sp.latex(matrix, mat_delim="[")
    except Exception:
        pass

    arr = np.asarray(matrix, dtype=object)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    rows = []
    for i in range(arr.shape[0]):
        cells = []
        for j in range(arr.shape[1]):
            val = arr[i, j]
            if isinstance(val, (int, float, np.floating, np.integer)):
                s = fmt.format(float(val))
            else:
                s = str(val)
            if len(s) > max_term_len:
                s = s[: max_term_len - 1] + r"\!\ldots"
            cells.append(s)
        rows.append(" & ".join(cells))
    body = r" \\ ".join(rows)
    return r"\begin{bmatrix}" + body + r"\end{bmatrix}"


def render_matrix_latex(
    ax,
    matrix,
    fmt: str = "{:+.3g}",
    fontsize: int = 12,
    color: str = "white",
    title: Optional[str] = None,
    prefix: str = "",
) -> None:
    """Dibuja una matriz como LaTeX centrado en el eje. Oculta los ticks.

    Parámetros:
        ax: matplotlib Axes.
        matrix: NumPy array, SymPy Matrix, o lista de listas.
        fmt: formato de cada número (ignorado para SymPy).
        title: si se proporciona, se coloca como título del eje.
        prefix: texto LaTeX que precede a la matriz, p.ej. r'\\mathbf{D}=' .
    """
    ax.clear()
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    latex_body = _matrix_to_latex(matrix, fmt=fmt)
    expr = f"${prefix}{latex_body}$"

    fs = _fit_fontsize(matrix, fontsize)
    try:
        ax.text(
            0.5, 0.5, expr,
            ha="center", va="center",
            fontsize=fs, color=color, transform=ax.transAxes,
        )
    except Exception:
        # fallback si mathtext falla: mostrar texto plano
        import numpy as np
        arr = np.asarray(matrix)
        ax.text(0.5, 0.5, str(arr),
                 ha="center", va="center",
                 fontsize=max(8, fs - 2), color=color,
                 family="monospace", transform=ax.transAxes)

    if title:
        ax.set_title(title, color=color, fontsize=fontsize + 1, pad=6)


def render_expression_latex(
    ax,
    expr: str,
    fontsize: int = 14,
    color: str = "white",
    title: Optional[str] = None,
) -> None:
    """Renderiza una expresión LaTeX arbitraria centrada en el eje."""
    ax.clear()
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    text = expr if expr.startswith("$") else f"${expr}$"
    try:
        ax.text(0.5, 0.5, text,
                 ha="center", va="center",
                 fontsize=fontsize, color=color, transform=ax.transAxes)
    except Exception:
        ax.text(0.5, 0.5, expr.replace("$", ""),
                 ha="center", va="center",
                 fontsize=max(8, fontsize - 2), color=color,
                 family="monospace", transform=ax.transAxes)
    if title:
        ax.set_title(title, color=color, fontsize=fontsize + 1, pad=6)


def _fit_fontsize(matrix, base_fontsize: int) -> int:
    """Heurística: reduce la fuente cuando la matriz es grande."""
    try:
        import sympy as sp
        if isinstance(matrix, sp.MatrixBase):
            rows, cols = matrix.shape
        else:
            arr = np.asarray(matrix)
            if arr.ndim == 1:
                rows, cols = arr.shape[0], 1
            else:
                rows, cols = arr.shape
    except Exception:
        return base_fontsize

    size = max(rows, cols)
    if size <= 3:
        return base_fontsize
    if size <= 4:
        return max(9, base_fontsize - 2)
    if size <= 8:
        return max(8, base_fontsize - 4)
    return max(6, base_fontsize - 6)
