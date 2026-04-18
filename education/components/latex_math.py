"""
LatexMath: Renderiza expresiones LaTeX cortas como imagen inline (ttk.Label).
Usa matplotlib.mathtext → PNG → PhotoImage. Cachea por (expr, fontsize, color).
Para ecuaciones largas/paso-a-paso usar TheoryViewer con pylatex.
"""

from __future__ import annotations

import io
from typing import Optional

import ttkbootstrap as ttk
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageTk


_CACHE: dict[tuple, ImageTk.PhotoImage] = {}


def render_latex_to_image(
    expr: str,
    fontsize: int = 14,
    color: str = "white",
    dpi: int = 140,
) -> ImageTk.PhotoImage:
    """Renderiza una expresión LaTeX a PhotoImage. Cachea el resultado."""
    key = (expr, fontsize, color, dpi)
    if key in _CACHE:
        return _CACHE[key]

    buf = io.BytesIO()
    try:
        fig, ax = plt.subplots(figsize=(0.01, 0.01), dpi=dpi)
        fig.patch.set_alpha(0)
        ax.axis("off")
        ax.text(0, 0, f"${expr}$", fontsize=fontsize, color=color)
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.05,
                    transparent=True, dpi=dpi)
        plt.close(fig)
    except Exception:
        plt.close("all")
        raise

    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    w, h = img.size
    img = img.resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    _CACHE[key] = photo
    return photo


class LatexMath(ttk.Label):
    """ttk.Label que muestra una expresión LaTeX como imagen."""

    def __init__(self, parent, expr: str = "", fontsize: int = 14,
                 color: Optional[str] = None, **kwargs):
        self._fontsize = fontsize
        self._color = color or "white"
        img = render_latex_to_image(expr, fontsize, self._color) if expr else None
        super().__init__(parent, text="", image=img, **kwargs)
        self._expr = expr
        self._image_ref = img  # mantener referencia

    def set_expr(self, expr: str) -> None:
        if expr == self._expr:
            return
        self._expr = expr
        img = render_latex_to_image(expr, self._fontsize, self._color)
        self.configure(image=img)
        self._image_ref = img
