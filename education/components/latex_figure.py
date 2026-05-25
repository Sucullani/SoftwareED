"""
latex_figure: utilidades para renderizar matrices y expresiones LaTeX
en un eje matplotlib.

Backend dual (UX 2026):
    1. **pdflatex + fitz** (default cuando MiKTeX disponible): compila
       el body, rasteriza a PNG y lo `imshow`-ea en el axes. Calidad
       documento, `\\begin{bmatrix}` real.
    2. **mathtext manual** (fallback): renderizado por celdas con
       corchetes manuales. Robusto sin pdflatex.

Funciones:
    - render_matrix_latex     -> dibuja matriz en un ax (auto-upgrade).
    - render_expression_latex -> dibuja expresion escalar (auto-upgrade).

Si MiKTeX esta instalado, los modulos M1..M7 que usan estas funciones
heredan el upgrade SIN tocar su codigo (transparente).
"""

from __future__ import annotations

from typing import Optional

import numpy as np


# ─── Renderizado de matrices: celdas individuales + corchetes ──────────────


def render_matrix_latex(
    ax,
    matrix,
    fmt: str = "{:.3g}",
    fontsize: int = 14,
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

    # Backend: matplotlib nativo (vector). `place_matrix_in_axes` arma
    # un `HPacker(TextArea + TextArea, align="center")` y lo coloca con
    # `AnchoredOffsetbox(loc="center", bbox_to_anchor=(0.5, 0.5))` en
    # el axes. Sin rasterizacion intermedia, sin composicion PIL, sin
    # resampling — la calidad es la misma que un `ax.text` mathtext.
    # El `align="center"` del HPacker garantiza que prefijo y cuerpo
    # de la matriz tengan sus centros geometricos alineados (resuelve
    # el quirk de mathtext con `\substack`).
    try:
        from .latex_image import place_matrix_in_axes
        ok = place_matrix_in_axes(
            ax, matrix, fmt=fmt, fontsize=fontsize, color=color,
            prefix=prefix,
        )
    except Exception:
        ok = False

    if not ok:
        ax.text(0.5, 0.5, "(matriz vacía)",
                 ha="center", va="center", color=color,
                 transform=ax.transAxes, fontsize=fontsize)

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

    # Convertir Unicode math (∂, ξ, η, ...) a comandos LaTeX para que
    # mathtext con fontset=cm renderice con tipografia matematica real.
    try:
        from .latex_image import _unicode_math_to_latex
        body = _unicode_math_to_latex(expr.strip("$").strip())
    except Exception:
        body = expr.strip("$").strip()
    text = f"${body}$"

    try:
        ax.text(0.5, 0.5, text,
                 ha="center", va="center",
                 fontsize=fontsize, color=color,
                 family="serif", transform=ax.transAxes)
    except Exception:
        ax.text(0.5, 0.5, expr.replace("$", ""),
                 ha="center", va="center",
                 fontsize=max(8, fontsize - 2), color=color,
                 family="serif", transform=ax.transAxes)
    if title:
        ax.set_title(title, color=color, fontsize=fontsize + 1, pad=6)


# ─── Helpers ──────────────────────────────────────────────────────────────


def _matrix_to_strings(matrix, fmt: str = "{:.3g}") -> Optional[np.ndarray]:
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
                # No truncar si la celda tiene sintaxis LaTeX (\\dfrac,
                # \\sum, etc). Umbral 32 acomoda expresiones tipicas.
                if "\\" not in s and len(s) > 32:
                    s = s[:31] + "…"
                out[i, j] = s
    return out


def _fit_fontsize_for_shape(rows: int, cols: int, base: int) -> int:
    """Heuristica de shrink calibrada para el factor de compensacion
    `1.7` aplicado al substack (`fs_substack = fs * 1.7`). Matrices
    pequenas (D 3x3, Jacobiano 2x2) conservan el `base`; matrices
    anchas (Q9 B 3x18, K 18x18) bajan agresivamente para no salirse
    del axes."""
    n = max(rows, cols)
    if n <= 4:
        return base
    if n <= 6:
        return max(11, base - 1)
    if n <= 9:
        return max(10, base - 2)
    if n <= 12:
        return max(9, base - 3)
    if n <= 18:
        return max(7, base - 5)
    return max(6, base - 6)


# ─── Upgrade transparente: backend pdflatex via imshow ──────────────────────


def _ax_face_hex(ax) -> str:
    """Color de fondo del axes en formato hex `#rrggbb`. Defaults a un
    gris muy oscuro coherente con la paleta EDU si el ax no esta colored."""
    try:
        c = ax.get_facecolor()
        if isinstance(c, str):
            return c if c.startswith("#") else "#2c2c2c"
        # tupla (r, g, b, a) en 0..1
        r, g, b = int(c[0] * 255), int(c[1] * 255), int(c[2] * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return "#2c2c2c"


def _try_imshow_expression_pdflatex(
    ax, body: str, *, color: str, fontsize: int, title: Optional[str],
) -> bool:
    """Compila `body` via latex_cache y lo muestra como `imshow` sobre el
    ax. Retorna True si OK; False si pdflatex no esta disponible o
    compile fallo (el caller debe usar el fallback)."""
    try:
        from config import latex_cache
        from PIL import Image
    except Exception:
        return False

    if not latex_cache.is_latex_available():
        return False

    bg = _ax_face_hex(ax)
    # DPI proporcional al fontsize objetivo. Calibrado para mathtext
    # fontsize ~14 -> pdflatex dpi ~240 en CMU.
    target_dpi = max(160, int(fontsize * 17))
    try:
        png_path = latex_cache.get_or_compile(
            body, dpi=target_dpi, color=color, bg=bg,
        )
    except Exception:
        return False
    if png_path is None or not png_path.exists():
        return False

    try:
        img = Image.open(png_path).convert("RGB")
    except Exception:
        return False

    arr = np.asarray(img)
    # extent (0,1)x(0,1) coincide con set_xlim/set_ylim hechos arriba.
    # `aspect="auto"` evita que el axes recorte la imagen si la relacion
    # del bbox del axes no matchea exactamente el de la imagen.
    ax.imshow(arr, extent=(0, 1, 0, 1), aspect="auto", interpolation="lanczos")
    if title:
        ax.set_title(title, color=color, fontsize=fontsize + 1, pad=6)
    return True


def _try_imshow_matrix_pdflatex(
    ax, cells: np.ndarray, *, prefix: str, color: str,
    fontsize: int, title: Optional[str],
) -> bool:
    """Construye `<prefix> \\begin{bmatrix} ... \\end{bmatrix}` y lo
    `imshow`-ea en el ax. Reusa la calidad documento del pipeline pdflatex
    en vez del render manual celda-por-celda."""
    rows, cols = cells.shape
    if rows == 0 or cols == 0:
        return False

    rows_tex = [" & ".join(_cell_for_latex(c) for c in row) for row in cells]
    body_matrix = r"\begin{bmatrix} " + r" \\ ".join(rows_tex) + r" \end{bmatrix}"
    if prefix:
        body = f"{prefix} {body_matrix}"
    else:
        body = body_matrix

    return _try_imshow_expression_pdflatex(
        ax, body, color=color, fontsize=fontsize, title=title,
    )


def _cell_for_latex(cell) -> str:
    """Normaliza una celda para math-mode LaTeX. Misma logica que
    `latex_image._cell_for_latex` — duplicada para que `latex_figure` no
    dependa de `latex_image`."""
    s = str(cell)
    if s in ("...", "…"):
        return r"\ldots"
    if all(c.isdigit() or c in "+-.eE " for c in s):
        return s
    safe = (s.replace("\\", r"\textbackslash{}")
              .replace("&", r"\&")
              .replace("%", r"\%")
              .replace("$", r"\$")
              .replace("#", r"\#")
              .replace("_", r"\_")
              .replace("{", r"\{")
              .replace("}", r"\}"))
    return rf"\text{{{safe}}}"
