"""
latex_image: Renderiza matrices y expresiones LaTeX como PhotoImages
embebibles en widgets Tk.

Backend único: matplotlib mathtext (UX 2026).
    Renderiza con corchetes manuales celda-por-celda (mathtext NO soporta
    `\\begin{bmatrix}`) + `\\substack` por columna. Tipografia Computer
    Modern via `config.matplotlib_config`. ~30-80 ms por render. No requiere
    pdflatex/MiKTeX (el antiguo pipeline pdflatex + cache en disco fue
    retirado en la limpieza 2026-05).

Componentes:
    - `render_matrix_image(matrix, ...)` -> PhotoImage de la matriz.
    - `render_expression_image(expr, ...)` -> PhotoImage de una expresion.
    - `LatexMatrixImage` -> ttk.Label con API `set_matrix(...)`.
    - `LatexExpressionImage` -> ttk.Label para expresiones escalares.

Caché:
    En memoria, por clave (cells/expr + fontsize + color + bg). Para
    matrices con valores que cambian (live update en M2/M4), el caller
    habilita `cache=False` para invalidar la memoria.
"""

from __future__ import annotations

import io
import math
from typing import Optional, Sequence, Union

import numpy as np
import ttkbootstrap as ttk
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from PIL import Image, ImageTk

from config.settings import EDU_FG, OVERLAY_BG


def _infer_bg(parent) -> str:
    """Intenta deducir el bg efectivo del widget parent. Necesario porque
    los modulos crean LatexMatrixImage/LatexExpressionImage dentro de
    `ttk.Frame`s del tema `darkly`, cuyo bg NO es `OVERLAY_BG` directo
    sino el del estilo del notebook/frame interno.

    Orden de fallback:
        1. parent.cget('background') / 'bg' (tk.Frame, tk.Label)
        2. ttk.Style().lookup(parent.winfo_class(), 'background')
        3. parent.winfo_rgb('background')
        4. OVERLAY_BG (constante)
    """
    if parent is None:
        return OVERLAY_BG
    # 1) tk widgets devuelven el color directo
    for opt in ("background", "bg"):
        try:
            val = parent.cget(opt)
            if val and isinstance(val, str) and val.startswith("#"):
                return val
        except Exception:
            pass
    # 2) ttk lookup del estilo
    try:
        import tkinter.ttk as _ttk
        style = _ttk.Style()
        cls = parent.winfo_class()
        val = style.lookup(cls, "background")
        if val and isinstance(val, str) and val.startswith("#"):
            return val
    except Exception:
        pass
    # 3) winfo_rgb (devuelve tupla 0..65535)
    try:
        r, g, b = parent.winfo_rgb("SystemButtonFace")
        return f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
    except Exception:
        pass
    # 4) ultima carta
    return OVERLAY_BG


# Tipado laxo: aceptamos numpy, sympy.Matrix, lista de listas, escalares.
MatrixLike = Union[np.ndarray, Sequence[Sequence], object]


_CACHE: dict = {}


# ─── API pública ────────────────────────────────────────────────────


def render_matrix_image(
    matrix: MatrixLike,
    *,
    fmt: str = "{:.3g}",
    fontsize: int = 14,
    color: str = EDU_FG,
    prefix: str = "",
    bg: Optional[str] = None,
    dpi: int = 140,
    cache: bool = True,
    shrink: bool = True,
) -> ImageTk.PhotoImage:
    """Renderiza una matriz como PhotoImage con corchetes NATIVOS LaTeX
    (`\\left[...\\right]`) usando `\\substack` por columna.

    Mathtext NO soporta `\\begin{bmatrix}` ni `\\matrix` (son AMS-LaTeX,
    requieren pdflatex). PERO `\\substack` SI esta y permite armar
    matrices visualmente equivalentes con corchetes nativos
    dimensionados automaticamente.

    Composicion: prefijo y cuerpo de la matriz se rendean como
    `TextArea` separados y se empaquetan con `HPacker(align="center")`
    para que sus centros geometricos coincidan verticalmente. Resuelve
    el quirk de mathtext donde `\\substack` se posiciona sobre el
    baseline (no sobre el eje matematico), que hacia que un render
    combinado `prefix + substack` dejara al prefijo abajo a la
    izquierda del bbox cropped.

    Compensacion de tamaño: `\\substack` rendea en subscript-style (~60%
    del normal). El factor `fs * 1.7` (calibrado en
    `_fit_fontsize_for_shape`) lo lleva a tamano "documento LaTeX".
    """
    if bg is None:
        bg = OVERLAY_BG

    cells = _matrix_to_strings(matrix, fmt=fmt)
    if cells is None or cells.size == 0:
        return render_expression_image("(matriz\\ vacía)", fontsize=fontsize,
                                       color=color, bg=bg, dpi=dpi)
    rows, cols = cells.shape

    if cache:
        key = ("matrix", _cells_key(cells), fontsize, color, prefix, bg, dpi, shrink)
        cached = _CACHE.get(key)
        if cached is not None:
            return cached

    try:
        photo = _render_matrix_via_packer_to_photoimage(
            cells, prefix=prefix, fontsize=fontsize, color=color,
            bg=bg, dpi=dpi, shrink=shrink,
        )
    except Exception:
        try:
            import matplotlib.pyplot as _plt
            _plt.close("all")
        except Exception:
            pass
        img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        photo = ImageTk.PhotoImage(img)

    if cache:
        _CACHE[key] = photo
    return photo


def _build_matrix_packer(
    cells: np.ndarray, *, prefix: str, fontsize: int, color: str,
    shrink: bool = True,
):
    """Construye un `HPacker` `(prefijo + matriz)` con vertical-center
    alignment. Usa `TextArea` para que el render sea matplotlib-nativo
    (mismo path que cualquier `ax.text` mathtext, sin composicion PIL
    ni resampling).

    `shrink=True` (default) aplica `_fit_fontsize_for_shape` que reduce el
    fontsize para matrices anchas (que el caller quiere que entren en un
    ancho fijo). `shrink=False` respeta el `fontsize` pedido tal cual — lo
    usa `ScrollableMatrixImage`, que muestra la matriz a tamano legible en
    un viewport con scroll/pan (el overflow lo resuelve el scroll, no el
    encogido de fuente).

    Returns the packer + the effective `fs_substack` (para que el
    caller pueda ajustar margenes/figsizes si lo necesita).
    """
    from matplotlib.offsetbox import TextArea, HPacker

    rows, cols = cells.shape
    fs = _fit_fontsize_for_shape(rows, cols, fontsize) if shrink else fontsize
    fs_substack = max(9, int(round(fs * 1.7)))

    matrix_expr = _build_substack_matrix_expr(cells, prefix="")
    children = []

    # Prefijo: limpiar thin spaces trailing (innecesarios al componer
    # via HPacker, eran para concatenacion mathtext) y normalizar
    # `\dfrac`/`\tfrac` -> `\frac` para que la altura sea compatible
    # con la del substack (subscript-style).
    norm_prefix = _normalize_prefix_fractions(prefix).strip()
    while norm_prefix.endswith(("\\,", "\\;", "\\!")):
        norm_prefix = norm_prefix[:-2].rstrip()
    if norm_prefix:
        children.append(TextArea(
            f"${norm_prefix}$",
            textprops=dict(fontsize=fs_substack, color=color, family="serif"),
        ))

    children.append(TextArea(
        matrix_expr,
        textprops=dict(fontsize=fs_substack, color=color, family="serif"),
    ))

    sep_pt = max(2, int(fs_substack * 0.25))
    packer = HPacker(children=children, align="center", pad=0, sep=sep_pt)
    return packer, fs_substack


def _render_matrix_via_packer_to_pil(
    cells: np.ndarray, *, prefix: str, fontsize: int, color: str,
    bg: str, dpi: int, shrink: bool = True,
) -> Image.Image:
    """Render del packer matplotlib-nativo a `PIL.Image` con bbox tight.

    Composicion 100% en matplotlib (HPacker + TextArea) — sin paste
    PIL, sin resampling intermedio. La PIL.Image final viene directa
    del PNG generado por Agg.
    """
    from matplotlib.offsetbox import AnchoredOffsetbox

    packer, _ = _build_matrix_packer(
        cells, prefix=prefix, fontsize=fontsize, color=color, shrink=shrink,
    )

    fig = Figure(figsize=(0.01, 0.01), dpi=dpi, facecolor=bg)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(bg)
    ax.axis("off")
    box = AnchoredOffsetbox(
        loc="center", child=packer, frameon=False, pad=0,
        bbox_to_anchor=(0.5, 0.5), bbox_transform=ax.transAxes,
    )
    ax.add_artist(box)

    buf = io.BytesIO()
    try:
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.04,
                    facecolor=bg, dpi=dpi)
    finally:
        try:
            fig.clf()
        except Exception:
            pass
    buf.seek(0)
    return Image.open(buf).convert("RGBA")


def _render_matrix_via_packer_to_photoimage(
    cells: np.ndarray, *, prefix: str, fontsize: int, color: str,
    bg: str, dpi: int, shrink: bool = True,
) -> ImageTk.PhotoImage:
    """Wrap del `PIL.Image` del packer como `PhotoImage` Tk. Aplica el
    downscale LANCZOS 50% estandar (super-sampling AA + tamano de
    widget coherente con el resto de la UI educativa)."""
    img = _render_matrix_via_packer_to_pil(
        cells, prefix=prefix, fontsize=fontsize, color=color,
        bg=bg, dpi=dpi, shrink=shrink,
    )
    w, h = img.size
    img = img.resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS)
    return ImageTk.PhotoImage(img)


# ─── Builders LaTeX para matrices via substack ─────────────────────────────


def _build_substack_matrix_expr(cells: np.ndarray, *, prefix: str = "") -> str:
    """Construye la expresion mathtext `$prefix \\left[ \\substack{col1}
    <SP> \\substack{col2> \\right]$`.

    Spacing auto: `\\quad` para matrices ≤ 9 cols, `\\,` (thin) para
    matrices anchas (Q9 18 cols).

    El prefix se normaliza: `\\dfrac` → `\\frac` para evitar
    superposicion vertical con la matriz substack (que esta en
    subscript-style).
    """
    rows, cols = cells.shape
    if rows == 0 or cols == 0:
        return "$\\left[\\,\\right]$"

    col_substacks = []
    for j in range(cols):
        items = [_cell_for_substack_atom(str(cells[i, j])) for i in range(rows)]
        body = r" \\ ".join(items)
        col_substacks.append(r"\substack{" + body + r"}")

    # Auto-spacing: `\quad` da mejor legibilidad para matrices educativas
    # ≤ 9 cols (Q4 8 GDLs, D 3×3, K_e 8×8). Para matrices muy anchas
    # (Q9 B 3×18) usar `\,` evita salirse del ancho del overlay.
    sep = r" \, " if cols > 9 else r" \quad "
    inner = sep.join(col_substacks)
    bracketed = r"\left[ " + inner + r" \right]"

    # Normalizacion del prefix: `\dfrac` (display-style) genera alturas
    # incompatibles con substack (subscript-style) → superposicion. Usar
    # `\frac` para mantener todo en una proporcion visual consistente.
    norm_prefix = _normalize_prefix_fractions(prefix)

    if norm_prefix:
        return f"${norm_prefix} {bracketed}$"
    return f"${bracketed}$"


def _normalize_prefix_fractions(prefix: str) -> str:
    """Convierte `\\dfrac` y `\\tfrac` a `\\frac` en el prefix.

    Razon: el prefix se renderiza al mismo fontsize que la matriz
    substack (que esta en subscript-style). Si el prefix usa `\\dfrac`
    (display-style), su altura visual es mucho mayor que la matriz y
    se superponen verticalmente. `\\frac` mantiene proporciones.
    """
    if not prefix:
        return prefix
    return prefix.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")


def _cell_for_substack_atom(raw: str) -> str:
    """Convierte una celda string a forma mathtext-ready DENTRO de un
    `\\substack{...}` (math mode).

    Reglas:
       - vacio → `\\,` (espacio thin para conservar altura de fila)
       - `...` → `\\ldots`
       - numericos (`+0.234`) → tal cual (math mode los acepta)
       - Unicode math (∂, ξ) → conversion a comandos LaTeX
       - sintaxis LaTeX explicita (`\\partial`) → tal cual
       - texto alfabetico plano → `\\mathrm{...}` (no italizar)
       - `\\dfrac` dentro de celdas → `\\frac` (mismo motivo que el prefix)
    """
    s = str(raw).strip()
    if not s:
        return r"\,"
    if s in ("...", "…"):
        return r"\ldots"
    if all(c.isdigit() or c in "+-.eE " for c in s):
        return s
    # Convertir Unicode primero.
    converted = _unicode_math_to_latex(s)
    # Normalizar fracciones para mantener altura consistente.
    converted = converted.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    if converted != s:
        return converted
    if "\\" in s:
        return s.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    return r"\mathrm{" + s + r"}"


def render_expression_image(
    expr: str,
    *,
    fontsize: int = 14,
    color: str = EDU_FG,
    bg: Optional[str] = None,
    dpi: int = 140,
    cache: bool = True,
) -> ImageTk.PhotoImage:
    """Renderiza una expresión LaTeX (mathtext) como PhotoImage. Render
    sincrono con Computer Modern (rcParams `mathtext.fontset = "cm"`).

    Soporta el subset mathtext de matplotlib: sub/super-indices, `\\dfrac`,
    `\\tfrac`, `\\sqrt`, `\\partial`, `\\sum`, `\\int`, griegas, etc.
    NO soporta `\\begin{bmatrix}` — para matrices usar `render_matrix_image`.

    Strings con Unicode math (∂, ξ, η, ...) se convierten a comandos
    LaTeX automaticamente — el caller puede pasar lo que sea legible.

    Latencia: ~30-150 ms cold, instantaneo con cache de memoria.
    """
    if bg is None:
        bg = OVERLAY_BG

    if not expr.strip():
        img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        return ImageTk.PhotoImage(img)

    # Convertir Unicode math a comandos LaTeX (idempotente si ya viene
    # en sintaxis LaTeX). Wrap en `$...$` si el caller no lo hizo.
    body = _unicode_math_to_latex(expr.strip("$").strip())
    text = f"${body}$"

    if cache:
        key = ("expr", text, fontsize, color, bg, dpi)
        cached = _CACHE.get(key)
        if cached is not None:
            return cached

    photo = _safe_render_mathtext_expression(text, body, fontsize=fontsize,
                                              color=color, bg=bg, dpi=dpi)
    if cache:
        _CACHE[key] = photo
    return photo


def _safe_render_mathtext_expression(
    text: str, raw_expr: str, *,
    fontsize: int, color: str, bg: str, dpi: int,
) -> ImageTk.PhotoImage:
    """Intenta render mathtext; si falla (sintaxis no soportada), cae a
    monospace plain. Garantiza retornar SIEMPRE un PhotoImage valido."""
    # Intento 1: mathtext con `$...$` y family=serif (CM).
    try:
        fig = Figure(figsize=(0.01, 0.01), dpi=dpi, facecolor=bg)
        fig.patch.set_alpha(1.0)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_facecolor(bg)
        ax.axis("off")
        ax.text(0, 0, text, fontsize=fontsize, color=color, family="serif")
        return _fig_to_photoimage(fig, dpi=dpi)
    except Exception:
        try:
            import matplotlib.pyplot as _plt
            _plt.close("all")
        except Exception:
            pass

    # Intento 2: texto plano monospace (sin parsing mathtext).
    try:
        fig = Figure(figsize=(0.01, 0.01), dpi=dpi, facecolor=bg)
        fig.patch.set_alpha(1.0)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_facecolor(bg)
        ax.axis("off")
        plain = raw_expr.replace("$", "")
        ax.text(0, 0, plain, fontsize=max(8, fontsize - 2),
                color=color, family="monospace")
        return _fig_to_photoimage(fig, dpi=dpi)
    except Exception:
        try:
            import matplotlib.pyplot as _plt
            _plt.close("all")
        except Exception:
            pass

    # Intento 3: placeholder transparente 1x1 (ultimo recurso).
    img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    return ImageTk.PhotoImage(img)


# ─── Widgets Tk ─────────────────────────────────────────────────────


class LatexMatrixImage(ttk.Label):
    """ttk.Label que muestra una matriz como imagen LaTeX.

    Reemplazo de `render_matrix_latex(ax, ...)` cuando se quiere que la
    matriz viva como widget Tk independiente (sin competir por el espacio
    de un Axes con captions u otras matrices). Tk hace el layout.

    Uso típico:
        widget = LatexMatrixImage(parent, matrix=B, prefix=r"\\mathbf{B}=",
                                  fontsize=11)
        widget.pack(fill="x", pady=2)
        # Más tarde, cuando ξ,η cambien:
        widget.set_matrix(new_B)
    """

    def __init__(
        self,
        parent,
        *,
        matrix: Optional[MatrixLike] = None,
        fmt: str = "{:.3g}",
        fontsize: int = 14,
        color: str = EDU_FG,
        prefix: str = "",
        bg: Optional[str] = None,
        dpi: int = 140,
        cache_values: bool = False,
        shrink: bool = True,  # True = auto-encoge la fuente en matrices anchas
                              # (default histórico). False = fuente plena (el
                              # caller garantiza que entra; el label se auto-
                              # dimensiona a la imagen → nunca se recorta).
        zoomable: bool = False,  # DEPRECADO: el pop-up MatrixZoom se eliminó
                                 # (era ruido). Aceptado y IGNORADO por compat;
                                 # para matrices anchas usar ScrollableMatrixImage.
        **label_kwargs,
    ):
        # Si no se especifica bg, inferir del parent para que el PNG
        # matchee EXACTAMENTE el fondo del ttk.Frame contenedor (cambia
        # segun el tema darkly del notebook/frame interno).
        if bg is None:
            bg = _infer_bg(parent)
        self._fmt = fmt
        self._fontsize = fontsize
        self._color = color
        self._prefix = prefix
        self._bg = bg
        self._dpi = dpi
        self._cache_values = cache_values
        self._shrink = shrink
        photo = (render_matrix_image(matrix, fmt=fmt, fontsize=fontsize,
                                     color=color, prefix=prefix, bg=bg, dpi=dpi,
                                     cache=cache_values, shrink=shrink)
                 if matrix is not None else None)
        super().__init__(parent, image=photo, background=bg, **label_kwargs)
        self._photo_ref = photo  # anti-GC

    def set_matrix(self, matrix: MatrixLike, *, prefix: Optional[str] = None) -> None:
        """Reemplaza la matriz mostrada. Si `prefix` se pasa explícitamente,
        actualiza también el prefijo (útil cuando cambia el caso TP↔DP)."""
        if prefix is not None:
            self._prefix = prefix
        photo = render_matrix_image(
            matrix, fmt=self._fmt, fontsize=self._fontsize, color=self._color,
            prefix=self._prefix, bg=self._bg, dpi=self._dpi,
            cache=self._cache_values, shrink=self._shrink,
        )
        self.configure(image=photo)
        self._photo_ref = photo

    def set_style(self, *, fontsize: Optional[int] = None,
                  color: Optional[str] = None, bg: Optional[str] = None) -> None:
        """Cambia parámetros de estilo (provoca re-render en próxima
        set_matrix)."""
        if fontsize is not None:
            self._fontsize = fontsize
        if color is not None:
            self._color = color
        if bg is not None:
            self._bg = bg
            try:
                self.configure(background=bg)
            except Exception:
                pass


class ScrollableMatrixImage(ttk.Frame):
    """Matriz LaTeX en un viewport de tamaño fijo con scroll + pan IN-FRAME.

    Reemplazo del pop-up `MatrixZoom` (eliminado por ruido). Para matrices
    anchas (B 3×18, k_e 18×18 en Q9) que en un `tk.Label` salían comprimidas
    a ~6-7 pt, este widget las renderiza a fontsize LEGIBLE (`shrink=False`,
    sin el encogido de `_fit_fontsize_for_shape`) y deja al alumno
    inspeccionarlas:
        • arrastrando con el mouse (pan, cursor `fleur`), y
        • con la rueda (scroll vertical; Shift+rueda = horizontal).

    API espejo de `LatexMatrixImage` (`set_matrix`, `cleanup`) para
    sustituirlo donde el corte era severo. Para matrices chicas (Q4) el
    contenido entra entero en el viewport y no hace falta scrollear — el
    widget funciona igual, sin pop-up ni segunda ventana.

    Implementación: `tk.Canvas` con `create_image` + `scrollregion`. NO abre
    ningún Toplevel — vive como hijo del `body` del overlay, así que NO toca
    el ciclo de vida frágil del `overrideredirect` (a diferencia del pop-up).

    Conflicto de rueda con el overlay: `CanvasOverlay._consume_wheel_recursive`
    bindea `<MouseWheel>→break` en TODOS los descendants al hacer `show()`
    (que corre DESPUÉS de construir el body), pisando cualquier bind de rueda
    hecho acá en `__init__`. Solución: re-bindeamos la rueda en `<Enter>` del
    canvas (corre en runtime, gana sobre el break) y la devolvemos a `break`
    en `<Leave>` (así fuera del canvas el wheel sigue protegido). El handler
    propio retorna `"break"`, de modo que el scroll NO se propaga a la
    MeshCanvas ni al FigureCanvasTkAgg vecino (regla de oro #3 preservada).
    """

    def __init__(
        self,
        parent,
        *,
        matrix: Optional[MatrixLike] = None,
        fmt: str = "{:.3g}",
        fontsize: int = 15,
        color: str = EDU_FG,
        prefix: str = "",
        bg: Optional[str] = None,
        dpi: int = 140,
        viewport: tuple = (440, 200),
        **frame_kwargs,
    ):
        if bg is None:
            bg = _infer_bg(parent)
        super().__init__(parent, **frame_kwargs)
        self._fmt = fmt
        self._fontsize = fontsize
        self._color = color
        self._prefix = prefix
        self._bg = bg
        self._dpi = dpi
        self._vw, self._vh = int(viewport[0]), int(viewport[1])
        self._photo = None  # anti-GC
        self._overflow_y = True  # eje de desborde (lo fija set_matrix)

        import tkinter as _tk
        # Cursor NORMAL por defecto: solo pasa a "fleur" (arrastrable) cuando
        # el contenido desborda (lo decide set_matrix). Antes era "fleur"
        # incondicional → señalaba "arrastrame" sobre valores estáticos.
        self._canvas = _tk.Canvas(
            self, width=self._vw, height=self._vh,
            bg=bg, highlightthickness=0, bd=0, cursor="",
        )
        self._canvas.pack(fill="both", expand=True)

        # Pan por arrastre (no afectado por el bloqueo de rueda del overlay).
        self._canvas.bind("<ButtonPress-1>",
                          lambda e: self._canvas.scan_mark(e.x, e.y))
        self._canvas.bind("<B1-Motion>",
                          lambda e: self._canvas.scan_dragto(e.x, e.y, gain=1))
        # Rueda: re-asertar en <Enter> (gana sobre el break del overlay) y
        # restaurar el break en <Leave>.
        self._canvas.bind("<Enter>", self._enable_wheel)
        self._canvas.bind("<Leave>", self._disable_wheel)

        # Tooltip on-hover EN VEZ del texto fijo "⤡ arrastrá / rueda" en la
        # esquina (que se solapaba con los valores = ruido). Informa solo al
        # pasar el mouse y SOLO cuando la matriz desborda (set_matrix actualiza
        # su texto). Aparece debajo del widget → no tapa los números.
        self._tooltip = None
        try:
            from gui.widgets.tooltip import ToolTip
            self._tooltip = ToolTip(self._canvas, text="", wraplength=210)
        except Exception:
            self._tooltip = None

        if matrix is not None:
            self.set_matrix(matrix)

    # ── Rueda (scroll) ─────────────────────────────────────────────
    def _enable_wheel(self, _e=None) -> None:
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._canvas.bind("<Shift-MouseWheel>", self._on_wheel_h)

    def _disable_wheel(self, _e=None) -> None:
        # Devolver el comportamiento "break" del overlay: fuera del canvas
        # la rueda NO debe llegar a la MeshCanvas ni al FigureCanvasTkAgg.
        self._canvas.bind("<MouseWheel>", lambda _ev: "break")
        self._canvas.bind("<Shift-MouseWheel>", lambda _ev: "break")

    def _on_wheel(self, e):
        # Si el contenido entra en alto (desborda SOLO en ancho, p.ej. ∂N 2×9),
        # la rueda simple cae a scroll HORIZONTAL — así "usá la rueda" del
        # tooltip es cierto para matrices anchas. Shift+rueda sigue siendo el
        # horizontal explícito; el drag paneа en ambos ejes.
        if getattr(self, "_overflow_y", True):
            self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        else:
            self._canvas.xview_scroll(int(-1 * (e.delta / 120)), "units")
        return "break"

    def _on_wheel_h(self, e):
        self._canvas.xview_scroll(int(-1 * (e.delta / 120)), "units")
        return "break"

    # ── API espejo de LatexMatrixImage ─────────────────────────────
    def set_matrix(self, matrix: MatrixLike, *, prefix: Optional[str] = None) -> None:
        if prefix is not None:
            self._prefix = prefix
        # shrink=False → fontsize pleno (el scroll resuelve el overflow, no
        # el encogido). cache=False → matrices live (cambian con ξ,η).
        photo = render_matrix_image(
            matrix, fmt=self._fmt, fontsize=self._fontsize, color=self._color,
            prefix=self._prefix, bg=self._bg, dpi=self._dpi,
            cache=False, shrink=False,
        )
        self._photo = photo  # anti-GC
        c = self._canvas
        c.delete("all")
        iw, ih = photo.width(), photo.height()
        # Centrar si la imagen es más chica que el viewport; sino anclar arriba-izq.
        ox = max(4, (self._vw - iw) // 2)
        oy = max(4, (self._vh - ih) // 2)
        c.create_image(ox, oy, image=photo, anchor="nw")
        c.configure(scrollregion=(0, 0, max(iw + 8, self._vw),
                                  max(ih + 8, self._vh)))
        # Afordancia de scroll SOLO si el contenido desborda el viewport: el
        # cursor pasa a "fleur" (arrastrable) y el tooltip on-hover informa.
        # Sin texto fijo en la esquina (ensuciaba los valores). Si entra, todo
        # queda limpio (cursor normal, sin tooltip).
        overflow = (iw > self._vw or ih > self._vh)
        # Eje en que desborda → gobierna el destino de la rueda simple.
        self._overflow_y = (ih > self._vh)
        try:
            c.configure(cursor="fleur" if overflow else "")
        except Exception:
            pass
        if self._tooltip is not None:
            self._tooltip.set_text(
                "Arrastrá o usá la rueda para ver toda la matriz"
                if overflow else ""
            )

    def set_style(self, *, fontsize: Optional[int] = None,
                  color: Optional[str] = None, bg: Optional[str] = None) -> None:
        if fontsize is not None:
            self._fontsize = fontsize
        if color is not None:
            self._color = color
        if bg is not None:
            self._bg = bg
            try:
                self._canvas.configure(bg=bg)
            except Exception:
                pass

    def cleanup(self) -> None:
        """Oculta y desagenda el tooltip on-hover (que abre un Toplevel
        transitorio vía `after()`). El overlay se cierra con `withdraw()` — NO
        `destroy()` —, así que sin esto un tooltip ya mostrado, o un `after`
        pendiente, sobreviviría como Toplevel huérfano sobre el escritorio (p.
        ej. al cerrar M2 con Ctrl+N sin sacar el cursor de la matriz). Invocado
        por `CanvasOverlayModule._cleanup_child_widgets`."""
        tip = getattr(self, "_tooltip", None)
        if tip is not None:
            try:
                tip._unschedule()
                tip._hide()
            except Exception:
                pass


def fit_matrix_widget(
    parent,
    matrix: MatrixLike,
    *,
    prefix: str = "",
    fmt: str = "{:.3g}",
    fontsize: int = 14,
    color: Optional[str] = None,
    max_width: int = 700,
    force_scroll: bool = False,
):
    """Devuelve el widget de matriz ADECUADO según si ENTRA en `max_width`,
    a fuente plena (`shrink=False`). Helper compartido por M2 y M4 (antes
    duplicado como `_fit_matrix` en cada uno).

    - **Entra** (`render.width ≤ max_width` y `not force_scroll`) →
      `LatexMatrixImage`, un `ttk.Label` que se AUTO-DIMENSIONA a la imagen:
      Tk lo ubica a su tamaño natural → es IMPOSIBLE que se recorte (a
      diferencia del canvas de ancho fijo de `ScrollableMatrixImage`, que bajo
      ciertas geometrías quedaba más angosto que la imagen y cortaba columnas).
    - **No entra** (o `force_scroll`) → `ScrollableMatrixImage` con viewport
      tope `max_width`: full-font + scroll/pan horizontal, sin encoger.

    `force_scroll` es para matrices LIVE cuyo ancho VARÍA con (ξ,η) (la ∂N de
    Q9 mide ~518 px en el centro pero ~920 px en los PGs; la B numérica es
    siempre ancha): decidir el widget por el render inicial daría un label que
    se desborda al moverse el punto. El caller hace `.pack(...)`.
    """
    kw = {} if color is None else {"color": color}
    try:
        ph = render_matrix_image(matrix, fmt=fmt, fontsize=fontsize,
                                 prefix=prefix, cache=False, shrink=False, **kw)
        iw, ih = ph.width(), ph.height()
    except Exception:
        iw, ih = max_width + 1, 60  # ante fallo, asumir overflow → scrollable
    if iw <= max_width and not force_scroll:
        return LatexMatrixImage(parent, matrix=matrix, fmt=fmt,
                                fontsize=fontsize, prefix=prefix, shrink=False,
                                cache_values=False, **kw)
    return ScrollableMatrixImage(parent, matrix=matrix, fmt=fmt,
                                 fontsize=fontsize, prefix=prefix,
                                 viewport=(max_width, ih + 10), **kw)


class LatexExpressionImage(ttk.Label):
    """ttk.Label que muestra una expresión mathtext (no-matriz) como imagen.

    Variante de `LatexMath` con la misma API pero usando la cache compartida
    de `latex_image`. Para usos nuevos preferir éste; `LatexMath` queda
    como compat retrocompat con módulos que ya lo importan.
    """

    def __init__(
        self,
        parent,
        expr: str = "",
        *,
        fontsize: int = 14,
        color: str = EDU_FG,
        bg: Optional[str] = None,
        dpi: int = 140,
        cache: bool = True,
        **label_kwargs,
    ):
        if bg is None:
            bg = _infer_bg(parent)
        self._fontsize = fontsize
        self._color = color
        self._bg = bg
        self._dpi = dpi
        self._cache = cache
        photo = (render_expression_image(expr, fontsize=fontsize, color=color,
                                         bg=bg, dpi=dpi, cache=cache)
                 if expr else None)
        super().__init__(parent, image=photo, background=bg, **label_kwargs)
        self._expr = expr
        self._photo_ref = photo

    def set_expression(self, expr: str) -> None:
        if expr == self._expr:
            return
        self._expr = expr
        photo = (render_expression_image(expr, fontsize=self._fontsize,
                                         color=self._color, bg=self._bg,
                                         dpi=self._dpi, cache=self._cache)
                 if expr else None)
        self.configure(image=photo)
        self._photo_ref = photo


# ─── Helpers ────────────────────────────────────────────────────────


def _fig_to_pil(fig: Figure, *, dpi: int) -> Image.Image:
    """Serializa una Figure a PNG (bbox_inches='tight') y la convierte
    a PIL.Image RGBA. Cierra la figura para liberar RAM. Reduce 50%
    para suavizado anti-alias (high-DPI render scaled down)."""
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
    # Reducción 50% — el render a 140 DPI con downscale a 70 DPI efectivo
    # produce anti-aliasing limpio sobre fondo oscuro.
    return img.resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS)


def _fig_to_photoimage(fig: Figure, *, dpi: int) -> ImageTk.PhotoImage:
    """Wrapper sobre `_fig_to_pil` para retornar `ImageTk.PhotoImage`."""
    return ImageTk.PhotoImage(_fig_to_pil(fig, dpi=dpi))


def _matrix_to_strings(matrix: MatrixLike, *, fmt: str) -> Optional[np.ndarray]:
    """Convierte una matriz heterogénea a un array 2D de strings."""
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
                # Truncado solo para texto plano largo. Si la celda tiene
                # sintaxis LaTeX (`\dfrac{1-\nu}{2}` = 18 chars), NO
                # truncar — rompe el parser mathtext. Umbral subido a 32
                # para acomodar expresiones tipicas tipo `\dfrac{a+b}{c}`.
                if "\\" not in s and len(s) > 32:
                    s = s[:31] + "…"
                out[i, j] = s
    return out


def _fit_fontsize_for_shape(rows: int, cols: int, base: int) -> int:
    """Heuristica de shrink calibrada para el factor de compensacion
    `1.7` aplicado en `render_matrix_image`.

    Matrices pequenas (Jacobiano 2x2, D 3x3, B Q4 3x8): conservan el
    `base` para que el render salga "documento LaTeX". Matrices anchas
    (B Q9 3x18, K Q9 18x18): bajan agresivamente para no salirse del
    overlay.
    """
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


def _cells_key(cells: np.ndarray) -> tuple:
    """Key cacheable para el contenido de la matriz."""
    return tuple(tuple(row) for row in cells)


# ─── Conversion de celdas a mathtext ───────────────────────────────────────


# Mapa Unicode math -> LaTeX. Cubre los chars que los modulos
# educativos pasan en strings de matriz (∂x/∂ξ, ξ, η, etc.) y en
# expresiones generales. Si un char no esta aqui, queda como esta y
# pdflatex lo intentara (puede fallar segun el paquete cargado).
_UNICODE_MATH_MAP = {
    # Letras griegas minusculas
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\varepsilon", "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta",
    "ι": r"\iota", "κ": r"\kappa", "λ": r"\lambda", "μ": r"\mu",
    "ν": r"\nu", "ξ": r"\xi", "π": r"\pi", "ρ": r"\rho",
    "σ": r"\sigma", "τ": r"\tau", "υ": r"\upsilon", "φ": r"\varphi",
    "ϕ": r"\phi", "χ": r"\chi", "ψ": r"\psi", "ω": r"\omega",
    # Letras griegas mayusculas
    "Α": "A", "Β": "B", "Γ": r"\Gamma", "Δ": r"\Delta",
    "Ε": "E", "Ζ": "Z", "Η": "H", "Θ": r"\Theta",
    "Ι": "I", "Κ": "K", "Λ": r"\Lambda", "Μ": "M",
    "Ν": "N", "Ξ": r"\Xi", "Ο": "O", "Π": r"\Pi",
    "Ρ": "P", "Σ": r"\Sigma", "Τ": "T", "Υ": r"\Upsilon",
    "Φ": r"\Phi", "Χ": "X", "Ψ": r"\Psi", "Ω": r"\Omega",
    # Operadores y simbolos comunes
    "∂": r"\partial", "∇": r"\nabla", "∞": r"\infty",
    "∫": r"\int", "∑": r"\sum", "∏": r"\prod",
    "√": r"\sqrt", "·": r"\cdot", "×": r"\times", "÷": r"\div",
    "±": r"\pm", "∓": r"\mp", "≈": r"\approx", "≠": r"\neq",
    "≤": r"\leq", "≥": r"\geq", "≪": r"\ll", "≫": r"\gg",
    "→": r"\to", "←": r"\leftarrow", "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow", "⇐": r"\Leftarrow", "⇔": r"\Leftrightarrow",
    "∈": r"\in", "∉": r"\notin", "⊂": r"\subset", "⊃": r"\supset",
    "∪": r"\cup", "∩": r"\cap", "∅": r"\emptyset",
    "°": r"^{\circ}",
}


# Comandos LaTeX comunes que matplotlib mathtext NO soporta, mapeados a
# su equivalente soportado. Evita que una expresión "casi válida" caiga al
# fallback de texto plano (se veía el LaTeX crudo en pantalla). matplotlib
# mathtext NO conoce: \lvert \rvert \lVert \rVert \tfrac (sí conoce \frac,
# \dfrac, \left| \right|, \|).
_MATHTEXT_UNSUPPORTED = (
    (r"\lvert", r"|"),
    (r"\rvert", r"|"),
    (r"\lVert", r"\|"),
    (r"\rVert", r"\|"),
    (r"\tfrac", r"\frac"),
)


def _sanitize_mathtext_commands(s: str) -> str:
    """Normaliza comandos LaTeX no soportados por mathtext a equivalentes
    válidos. Defensa para que expresiones con \\lvert/\\tfrac no caigan al
    fallback de texto crudo."""
    for bad, good in _MATHTEXT_UNSUPPORTED:
        if bad in s:
            s = s.replace(bad, good)
    return s


def _unicode_math_to_latex(s: str) -> str:
    """Reemplaza chars Unicode math por sus comandos LaTeX. Inserta
    espacios despues de comandos para evitar ambiguedad
    (`\\partial x` no `\\partialx`). Primero normaliza comandos LaTeX que
    mathtext no soporta (\\lvert, \\tfrac, ...) a equivalentes válidos."""
    if not s:
        return s
    s = _sanitize_mathtext_commands(s)
    out = []
    for ch in s:
        rep = _UNICODE_MATH_MAP.get(ch)
        if rep is None:
            out.append(ch)
        else:
            # Si el reemplazo termina en letra (`\partial`, `\xi`),
            # agregamos espacio para separar del char siguiente.
            if rep[-1].isalpha():
                out.append(rep + " ")
            else:
                out.append(rep)
    return "".join(out)
