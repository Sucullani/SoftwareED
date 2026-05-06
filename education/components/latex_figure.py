"""
latex_figure: utilidades para renderizar matrices y expresiones LaTeX
en un eje matplotlib.

Implementación:
    - render_matrix_latex   → renderizado MANUAL por celdas individuales,
                              robusto independientemente de la versión de
                              matplotlib (mathtext NO soporta `\\begin{bmatrix}`
                              en versiones públicas; el fallback a str(array)
                              era ilegible).
    - render_expression_latex → mathtext (sin compilador externo) para
                              expresiones simples (fracciones, super/subíndices,
                              \\dfrac, \\sqrt, \\partial, etc.). NO incluir
                              entornos de matriz en estas expresiones.
"""

from __future__ import annotations

from typing import Optional

import numpy as np


# ─── Renderizado de matrices: celdas individuales + corchetes ──────────────


def render_matrix_latex(
    ax,
    matrix,
    fmt: str = "{:+.3g}",
    fontsize: int = 12,
    color: str = "white",
    title: Optional[str] = None,
    prefix: str = "",
) -> None:
    """Dibuja una matriz como una grilla de texto con corchetes a los lados.

    Cada celda se renderiza con `ax.text()` independientemente, así no
    dependemos del soporte de `\\begin{bmatrix}` en mathtext (matplotlib
    NO lo soporta — lo que rompía el fallback a numpy.str).

    Parámetros:
        ax: matplotlib Axes (idealmente vacío y sin ticks).
        matrix: NumPy array, lista de listas, o SymPy Matrix.
        fmt: formato de cada número (ignorado para SymPy: sp.latex).
        fontsize: tamaño base; se reduce automáticamente si la matriz es
                  grande (Q9: 3×18) para que no se desborde.
        color: color de los números, los corchetes y el prefijo.
        title: si se proporciona, va como título del eje.
        prefix: texto LaTeX antes de la matriz, p.ej. r'\\mathbf{D}=' .
                Se renderiza con mathtext junto a la izquierda.
    """
    ax.clear()
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Convertir a array de strings
    cells = _matrix_to_strings(matrix, fmt=fmt)
    if cells is None or cells.size == 0:
        ax.text(0.5, 0.5, "(matriz vacía)",
                 ha="center", va="center", color=color,
                 transform=ax.transAxes, fontsize=fontsize)
        if title:
            ax.set_title(title, color=color, fontsize=fontsize + 1, pad=6)
        return

    rows, cols = cells.shape
    # Auto-shrink fontsize en matrices grandes (Q9 B = 3×18)
    fs = _fit_fontsize_for_shape(rows, cols, fontsize)

    # Layout: el prefijo va a la izquierda, luego los corchetes envuelven
    # la grilla. Calculamos posiciones en unidades del axes (0..1).
    # Diseño: márgenes simétricos verticales, prefijo en x≈0.05, grilla
    # centrada, corchetes en los bordes de la grilla.

    # Estimación de ancho de columna en proporción al ancho del axes.
    # Una grilla de N columnas con strings de ~6 chars típicos cabe bien
    # con paso = 0.85/cols, dejando 0.075 de cada lado para corchetes y
    # prefijo. Para matrices muy anchas (Q9 B con 18 cols) el fontsize
    # reducido compensa.
    margin_left = 0.10 if prefix else 0.04
    margin_right = 0.04
    grid_left = margin_left
    grid_right = 1.0 - margin_right
    grid_width = grid_right - grid_left

    if cols == 1:
        col_xs = [0.5 * (grid_left + grid_right)]
    else:
        col_xs = [grid_left + grid_width * (j + 0.5) / cols
                  for j in range(cols)]

    if rows == 1:
        row_ys = [0.5]
    else:
        # de arriba (alto y) hacia abajo (bajo y). Margen vertical 0.18.
        row_top = 0.82
        row_bot = 0.18
        row_ys = [row_top - (row_top - row_bot) * (i / max(1, rows - 1))
                  for i in range(rows)]

    # Render del prefijo (mathtext) — lo dibujamos a la altura central de
    # la matriz, justo a la izquierda del corchete izquierdo.
    if prefix:
        try:
            ax.text(0.005, 0.5, f"${prefix}$",
                     ha="left", va="center", fontsize=fs + 1,
                     color=color, transform=ax.transAxes)
        except Exception:
            ax.text(0.005, 0.5, prefix.replace("\\mathbf", "")
                                       .replace("{", "").replace("}", ""),
                     ha="left", va="center", fontsize=fs, color=color,
                     family="monospace", transform=ax.transAxes)

    # Render de cada celda como texto plano (no mathtext: los números no
    # necesitan parsing y así evitamos el problema de '+' como operador)
    for i in range(rows):
        for j in range(cols):
            txt = cells[i, j]
            ax.text(col_xs[j], row_ys[i], txt,
                     ha="center", va="center",
                     fontsize=fs, color=color,
                     family="monospace",
                     transform=ax.transAxes)

    # Corchetes a los lados de la grilla — líneas L invertidas.
    # Tamaño vertical: cubre las filas con un pequeño extra arriba/abajo.
    if rows == 1:
        bracket_top = 0.62
        bracket_bot = 0.38
    else:
        bracket_top = max(row_ys) + 0.07
        bracket_bot = min(row_ys) - 0.07
    bracket_top = min(0.94, bracket_top)
    bracket_bot = max(0.06, bracket_bot)

    bracket_l_x = grid_left - 0.012
    bracket_r_x = grid_right + 0.012
    tick = 0.018  # longitud del "pie" del corchete

    # Corchete izquierdo: vertical + dos pies
    ax.plot([bracket_l_x, bracket_l_x],
             [bracket_top, bracket_bot],
             color=color, lw=1.6, transform=ax.transAxes,
             clip_on=False, solid_capstyle="butt")
    ax.plot([bracket_l_x, bracket_l_x + tick],
             [bracket_top, bracket_top],
             color=color, lw=1.6, transform=ax.transAxes, clip_on=False)
    ax.plot([bracket_l_x, bracket_l_x + tick],
             [bracket_bot, bracket_bot],
             color=color, lw=1.6, transform=ax.transAxes, clip_on=False)
    # Corchete derecho
    ax.plot([bracket_r_x, bracket_r_x],
             [bracket_top, bracket_bot],
             color=color, lw=1.6, transform=ax.transAxes, clip_on=False)
    ax.plot([bracket_r_x, bracket_r_x - tick],
             [bracket_top, bracket_top],
             color=color, lw=1.6, transform=ax.transAxes, clip_on=False)
    ax.plot([bracket_r_x, bracket_r_x - tick],
             [bracket_bot, bracket_bot],
             color=color, lw=1.6, transform=ax.transAxes, clip_on=False)

    if title:
        ax.set_title(title, color=color, fontsize=fontsize + 1, pad=6)


def render_expression_latex(
    ax,
    expr: str,
    fontsize: int = 14,
    color: str = "white",
    title: Optional[str] = None,
) -> None:
    """Renderiza una expresión LaTeX (mathtext) centrada en el eje.

    No usar entornos de matriz aquí — para matrices, llamá a
    `render_matrix_latex`. Esta función es para fórmulas escalares,
    fracciones, integrales, sumatorias, etc.
    """
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


# ─── Helpers ──────────────────────────────────────────────────────────────


def _matrix_to_strings(matrix, fmt: str = "{:+.3g}") -> Optional[np.ndarray]:
    """Convierte una matriz heterogénea (numpy / sympy / lista) a un array
    2D de strings listos para ax.text(). Maneja escalares y vectores 1D.
    """
    try:
        import sympy as sp
        if isinstance(matrix, sp.MatrixBase):
            r, c = matrix.shape
            out = np.empty((r, c), dtype=object)
            for i in range(r):
                for j in range(c):
                    out[i, j] = sp.pretty(matrix[i, j], use_unicode=False)
            return out
    except Exception:
        pass

    arr = np.asarray(matrix, dtype=object)
    if arr.ndim == 0:
        arr = arr.reshape(1, 1)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    if arr.ndim != 2:
        return None
    out = np.empty(arr.shape, dtype=object)
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            v = arr[i, j]
            if isinstance(v, (int, float, np.floating, np.integer)):
                out[i, j] = fmt.format(float(v))
            else:
                s = str(v)
                if len(s) > 14:
                    s = s[:13] + "…"
                out[i, j] = s
    return out


def _fit_fontsize_for_shape(rows: int, cols: int, base: int) -> int:
    """Heurística: matrices anchas (Q9 B con 18 cols) → fuente más chica
    para que quepa en el axes."""
    n = max(rows, cols)
    if n <= 4:
        return base
    if n <= 6:
        return max(9, base - 2)
    if n <= 9:
        return max(8, base - 3)
    if n <= 12:
        return max(7, base - 4)
    return max(6, base - 5)
