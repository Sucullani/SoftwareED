"""
LatexStatusLabel — texto multi-linea con math inline, render mathtext
sincrono con Computer Modern.

Reemplaza `tk.Label(font=Consolas)` para textos status de overlays
educativos: titulos de elemento, coordenadas de Gauss, captions con
notacion mezclada texto+math.

Backend: matplotlib mathtext con fontset `cm` (configurado en
`config.matplotlib_config`). Sin pdflatex, sin cache disco, sin async.
Render ~30-100 ms cold, instantaneo con cache en memoria.

Sintaxis aceptada (mathtext de matplotlib):
    - Texto plano: tal cual
    - Math inline: `$\\xi, \\eta$`, `$\\sqrt{3}$`, `$\\dfrac{a}{b}$`
    - Multiples lineas: separadas por `\\\\` o `\\n`
    - NO soporta `\\textbf`, `\\text` (no-math) — usar Unicode si
      necesitas negrita

Uso tipico (sustituyendo un tk.Label en gauss_inset):

    lbl = LatexStatusLabel(
        parent,
        text=r"$(\\xi,\\eta)=(-0.577,-0.577)=(-1/\\sqrt{3},-1/\\sqrt{3})$",
        fontsize=10,
    )
    lbl.pack()
    lbl.set_text(r"$\\to$ mapeo $\\to$ $(x,y)=(+1.479, +0.679)$")
"""

from __future__ import annotations

import io
from typing import Optional

import tkinter as tk

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from PIL import Image, ImageTk

from config.settings import EDU_FG, OVERLAY_BG
from education.components.latex_image import _infer_bg, _unicode_math_to_latex


# Cache de PhotoImage por (text, fontsize, color, bg).
_STATUS_CACHE: dict = {}


class LatexStatusLabel(tk.Label):
    """tk.Label que renderiza texto LaTeX (con math inline) como imagen
    mathtext con Computer Modern.

    Args:
        parent: contenedor Tk.
        text: cuerpo. Mezcla texto plano + `$math$` inline. `\\\\` o `\\n`
              para nueva linea. Strings Unicode (∂, ξ) se convierten
              automaticamente a comandos LaTeX dentro de los math blocks.
        fontsize: tamaño base. Default 10.
        color: fg del texto/math. Default EDU_FG.
        bg: fondo de la imagen. Default: inferido del parent.
    """

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        *,
        fontsize: int = 10,
        color: str = EDU_FG,
        bg: Optional[str] = None,
        anchor: str = "center",
        **label_kwargs,
    ) -> None:
        if bg is None:
            bg = _infer_bg(parent)
        self._text = text
        self._fontsize = fontsize
        self._color = color
        self._bg = bg

        photo = _render_status_to_photo(
            text, fontsize=fontsize, color=color, bg=bg,
        )
        super().__init__(
            parent, image=photo, bd=0, bg=bg, anchor=anchor, **label_kwargs,
        )
        self._photo_ref = photo

    def set_text(self, text: str) -> None:
        if text == self._text:
            return
        self._text = text
        photo = _render_status_to_photo(
            text, fontsize=self._fontsize, color=self._color, bg=self._bg,
        )
        if photo is None:
            # Texto vacio: colapsar widget.
            try:
                self.configure(image="", text="")
            except tk.TclError:
                pass
            self._photo_ref = None
        else:
            self.configure(image=photo, text="")
            self._photo_ref = photo


# ─── Render helper ──────────────────────────────────────────────────────────


def _render_status_to_photo(
    text: str, *, fontsize: int, color: str, bg: str,
) -> Optional[ImageTk.PhotoImage]:
    """Render del text multi-linea a PhotoImage. None si text vacio."""
    if not text or not text.strip():
        return None

    # Cache hit (memoria, deduplicado por key exacta).
    key = (text, fontsize, color, bg)
    cached = _STATUS_CACHE.get(key)
    if cached is not None:
        return cached

    # Procesar text: separar por `\\` o `\n` en multiples lineas.
    # Cada linea puede tener `$math$` inline; matplotlib lo parsea OK.
    raw_lines = text.replace("\n", r"\\").split(r"\\")
    lines = [l.strip() for l in raw_lines if l.strip()]
    if not lines:
        return None

    # Convertir Unicode math en cada linea (dentro y fuera de math mode).
    # _unicode_math_to_latex es safe para ambos contextos.
    lines = [_unicode_math_to_latex(l) for l in lines]
    joined = "\n".join(lines)

    # Figura minima (figsize=0.01, dpi=140), bbox_inches="tight" recorta
    # al contenido. Multi-linea via `\n` en el string del text.
    try:
        fig = Figure(figsize=(0.01, 0.01), dpi=140, facecolor=bg)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_facecolor(bg)
        ax.axis("off")
        ax.text(0, 0, joined, fontsize=fontsize, color=color,
                family="serif", linespacing=1.3)
        photo = _fig_to_photo(fig, dpi=140)
    except Exception:
        # Fallback: texto plano sin parsing math (no crashea con
        # sintaxis no soportada).
        plain = _text_to_plain(text)
        try:
            fig = Figure(figsize=(0.01, 0.01), dpi=140, facecolor=bg)
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_facecolor(bg)
            ax.axis("off")
            ax.text(0, 0, plain, fontsize=fontsize, color=color,
                    family="serif", linespacing=1.3)
            photo = _fig_to_photo(fig, dpi=140)
        except Exception:
            img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
            photo = ImageTk.PhotoImage(img)

    _STATUS_CACHE[key] = photo
    return photo


def _fig_to_photo(fig: Figure, *, dpi: int) -> ImageTk.PhotoImage:
    """Figura -> PhotoImage con downscale 50% para anti-alias."""
    buf = io.BytesIO()
    try:
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.04,
                    facecolor=fig.get_facecolor(), dpi=dpi)
    finally:
        try:
            fig.clf()
        except Exception:
            pass
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    w, h = img.size
    img = img.resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS)
    return ImageTk.PhotoImage(img)


def _text_to_plain(text: str) -> str:
    """Fallback monospace-friendly: stripea `$`, comandos `\\textbf`,
    mantiene Unicode chars convertidos del original."""
    s = text.replace(r"\\", "\n").replace("$", "")
    import re
    s = re.sub(r"\\textbf\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\textit\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    return s


def clear_cache() -> int:
    """Vacia la cache en memoria. Util si cambia el tema (colores)."""
    n = len(_STATUS_CACHE)
    _STATUS_CACHE.clear()
    return n
