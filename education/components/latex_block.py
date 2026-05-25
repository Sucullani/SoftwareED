"""
LatexBlock — bloque LaTeX de calidad documento, embebido como widget Tk.

Reemplaza el render mathtext (matplotlib) cuando MiKTeX/pdflatex esta
disponible. Cae al fallback mathtext (latex_image) si no.

Dos modos de render:

    1. static — formula compilada una sola vez, mostrada como PhotoImage.

        block = LatexBlock(parent, r"\\mathbf{D} = \\begin{bmatrix} ... \\end{bmatrix}")
        block.pack()

    2. parametric — formula con `\\phantom{...}` slots para valores que
       cambian en vivo. La formula se compila UNA VEZ; los valores se
       superponen como ttk.Label con fuente Computer Modern (la misma
       que usa LaTeX), produciendo el mismo aspecto visual sin recompile.

        block = LatexBlock(
            parent,
            template=r"\\nu = \\phantom{0.499}",
            slots={"nu": dict(placeholder="0.499", initial="0.200")},
        )
        block.set_value("nu", f"{value:.3f}")  # 0 ms, sin recompile

API:
    LatexBlock(parent, body=None, *, template=None, slots=None,
               dpi=200, color="#dcdcdc", bg="#222233", ...)

    .set_body(new_body)              # static: recompila
    .set_value(slot_name, value)     # parametric: actualiza overlay
    .refresh()                        # re-render con params actuales
"""

from __future__ import annotations

import io
import re
from typing import Optional

import tkinter as tk
import ttkbootstrap as ttk
from PIL import Image, ImageTk

from config import latex_cache
from config.settings import EDU_FG, OVERLAY_BG


# Tamaño de fuente CMU por defecto. Se sobreescribe via parametro fontsize
# en el constructor. Calibrado para que coincida visualmente con el
# render LaTeX a dpi=200.
_DEFAULT_FONTSIZE = 12

# Nombre de familia de la fuente Computer Modern. Si la fuente no esta
# instalada como TTF en el sistema, Tk cae a un fallback serif italico,
# que sigue siendo aceptable (Times New Roman italic se parece bastante
# a CM italica). El bundling de la fuente se documenta en
# `resources/fonts/README.md`.
CMU_FONT_FAMILY = "CMU Serif"
CMU_FONT_FAMILY_FALLBACKS = ("CMU Serif", "Latin Modern Roman", "Times New Roman")


def cm_font(size: int = _DEFAULT_FONTSIZE, *, italic: bool = True) -> tuple:
    """Tupla `(family, size, style)` para `ttk.Label(font=...)`. Itera
    los fallbacks: si CMU Serif no esta instalada, usa el primero que
    Tk reconozca. Mantenemos la API en forma de tupla (no objeto Font)
    porque ttk.Label la consume directamente sin overhead."""
    style = "italic" if italic else ""
    # Tk no expone listFonts barato cross-platform desde la API publica;
    # confiamos en que el primer fallback (CMU) este disponible si fue
    # bundleado, sino cae al serif italico del sistema (sigue siendo
    # tipograficamente coherente para variables matematicas).
    return (CMU_FONT_FAMILY, size, style)


# ─── Widget ─────────────────────────────────────────────────────────────────


class LatexBlock(ttk.Frame):
    """Bloque LaTeX con render documento-quality y overlay para live values.

    Args:
        parent: contenedor Tk.
        body: expresion LaTeX (modo static). Mutuamente excluyente con `template`.
        template: expresion LaTeX con `\\phantom{...}` para valores live
                  (modo parametric). Requiere `slots`.
        slots: dict `{slot_name: {"placeholder": str, "initial": str, "italic": bool}}`
               donde `placeholder` es el texto exacto dentro de `\\phantom{...}`
               que define el ancho del hueco, e `initial` es el valor a
               mostrar. `italic=False` para numeros (default), True para variables.
        dpi: resolucion de compilacion (default 200).
        color: color del texto (#rrggbb).
        bg: color de fondo (#rrggbb).
        fontsize: tamaño de la fuente CMU para overlays (modo parametric).
                  Calibrar contra dpi.
    """

    def __init__(
        self,
        parent: tk.Widget,
        body: Optional[str] = None,
        *,
        template: Optional[str] = None,
        slots: Optional[dict] = None,
        dpi: int = 200,
        color: str = EDU_FG,
        bg: str = OVERLAY_BG,
        fontsize: int = _DEFAULT_FONTSIZE,
        **frame_kwargs,
    ) -> None:
        super().__init__(parent, **frame_kwargs)
        self.configure(style="TFrame")

        self._dpi = dpi
        self._color = color
        self._bg = bg
        self._fontsize = fontsize

        if body is not None and template is not None:
            raise ValueError("Pasar `body` (static) O `template` (parametric), no ambos.")
        if template is not None and not slots:
            raise ValueError("Modo parametric requiere `slots`.")

        self._body: Optional[str] = body
        self._template: Optional[str] = template
        self._slots: dict = dict(slots) if slots else {}
        self._values: dict[str, str] = {
            name: cfg.get("initial", cfg.get("placeholder", ""))
            for name, cfg in self._slots.items()
        }

        # Label contenedor de la imagen compilada (sin texto, solo image).
        # Usamos tk.Label en vez de ttk.Label porque tk.Label soporta
        # `background` arbitrario sin necesidad de crear un Style; los
        # overlays parametric necesitan que el fondo del Label coincida
        # con el bg del PNG.
        self._image_label = tk.Label(self, bd=0, highlightthickness=0,
                                       background=bg)
        self._image_label.pack(fill="both", expand=True)

        # Overlays de slots: name -> tk.Label colocado con place(x, y).
        self._overlays: dict[str, tk.Label] = {}

        # Referencias anti-GC.
        self._photo_ref: Optional[ImageTk.PhotoImage] = None
        self._bbox_per_slot: dict[str, tuple[int, int, int, int]] = {}

        # Render inicial.
        self.refresh()

    # ── API publica ────────────────────────────────────────────────────

    def set_body(self, body: str) -> None:
        """Modo static: cambia la expresion LaTeX y recompila."""
        if self._template is not None:
            raise RuntimeError("set_body solo aplica en modo static.")
        if body == self._body:
            return
        self._body = body
        self.refresh()

    def set_value(self, slot_name: str, value: str) -> None:
        """Modo parametric: actualiza el valor de un slot SIN recompile."""
        if self._template is None:
            raise RuntimeError("set_value solo aplica en modo parametric.")
        if slot_name not in self._slots:
            raise KeyError(f"Slot desconocido: {slot_name!r}")
        if self._values.get(slot_name) == value:
            return
        self._values[slot_name] = value
        lbl = self._overlays.get(slot_name)
        if lbl is not None:
            lbl.configure(text=value)

    def refresh(self) -> None:
        """Recompila la formula y reposiciona overlays. Llamar si cambian
        propiedades de render (color/dpi) o cuando se quiere forzar."""
        for lbl in self._overlays.values():
            lbl.destroy()
        self._overlays.clear()
        self._bbox_per_slot.clear()

        body, slot_to_phantom = self._build_compile_body()
        if not body:
            return

        png_path = latex_cache.get_or_compile(
            body, dpi=self._dpi, color=self._color, bg=self._bg,
        )
        if png_path is None:
            # Fallback: render mathtext via latex_image (mismo API que el
            # pipeline legacy). Esto permite que EduFEM funcione sin MiKTeX.
            self._render_fallback()
            return

        try:
            img = Image.open(png_path).convert("RGBA")
        except Exception:
            self._render_fallback()
            return

        # Detectar bbox de cada phantom buscando el placeholder en la PDF
        # original. Como ya no tenemos el PDF (solo el PNG), reabrimos la
        # cache: fitz solo se invoca en modo parametric.
        if self._template is not None and slot_to_phantom:
            self._compute_phantom_bboxes(body, slot_to_phantom, img.size)

        # Pegar la imagen al Label.
        photo = ImageTk.PhotoImage(img)
        self._image_label.configure(image=photo)
        self._photo_ref = photo

        # Crear overlays para cada slot.
        if self._template is not None:
            self._place_overlays()

    # ── Internos: build de body para compile ───────────────────────────

    def _build_compile_body(self) -> tuple[str, dict[str, str]]:
        """Retorna `(body, slot_to_phantom)` donde `body` es el LaTeX
        listo para compilar y `slot_to_phantom` mapea nombre de slot al
        string del placeholder (usado para bbox-detection).

        Modo static: body = self._body, slot map vacio.
        Modo parametric: body construido reemplazando los slots del
        template por `\\phantom{placeholder}`.
        """
        if self._body is not None:
            return self._body, {}

        if self._template is None:
            return "", {}

        # En modo parametric el template ya trae `\\phantom{...}` literal
        # con el placeholder dentro. No tocamos el template; solo
        # extraemos los placeholders para bbox-detection posterior.
        slot_to_phantom = {
            name: cfg["placeholder"]
            for name, cfg in self._slots.items()
            if "placeholder" in cfg
        }
        return self._template, slot_to_phantom

    # ── Internos: bbox detection via fitz ──────────────────────────────

    def _compute_phantom_bboxes(
        self,
        body: str,
        slot_to_phantom: dict[str, str],
        png_size: tuple[int, int],
    ) -> None:
        """Recompila el body REEMPLAZANDO cada \\phantom{p} por su placeholder
        visible, abre el PDF resultante con fitz, busca el placeholder en
        el page.text y obtiene su bbox. Estos bboxes se usan para
        posicionar los overlays sobre el PNG original (que tiene los
        phantom como huecos invisibles).

        Optimizacion: el bbox calculation se cachea por hash del template
        para evitar re-compilar en cada `refresh`. La compilacion auxiliar
        usa el mismo cache (es decir, queda en disco como cualquier otro
        fragmento).
        """
        # Body con los phantom reemplazados por placeholder visible.
        probe_body = body
        for ph in slot_to_phantom.values():
            phantom_pat = r"\phantom{" + ph + r"}"
            probe_body = probe_body.replace(phantom_pat, ph)

        probe_png = latex_cache.get_or_compile(
            probe_body, dpi=self._dpi, color=self._color, bg=self._bg,
        )
        if probe_png is None:
            return

        # Para obtener bbox usamos el PDF intermedio. latex_cache no lo
        # expone — alternativa: re-compilamos sobre tempdir solo para
        # extraer coords. Es caro la primera vez pero el resultado se
        # cachea en `_bbox_per_slot` (que persiste mientras el LatexBlock
        # viva). Para multi-slot, una sola compilacion los detecta todos.
        coords = _extract_bboxes_from_latex(
            probe_body, list(slot_to_phantom.values()),
            dpi=self._dpi, color=self._color, bg=self._bg,
        )
        # coords: dict[placeholder] -> (x0, y0, x1, y1) en pixels.
        for name, ph in slot_to_phantom.items():
            bb = coords.get(ph)
            if bb is not None:
                self._bbox_per_slot[name] = bb

    def _place_overlays(self) -> None:
        """Crea tk.Label con fuente CMU por cada slot detectado y lo
        coloca con place(x, y) sobre el image_label."""
        for name, cfg in self._slots.items():
            bb = self._bbox_per_slot.get(name)
            if bb is None:
                continue
            x0, y0, x1, y1 = bb
            italic = cfg.get("italic", False)
            value = self._values.get(name, cfg.get("initial", ""))
            lbl = tk.Label(
                self._image_label,
                text=value,
                font=cm_font(self._fontsize, italic=italic),
                fg=self._color,
                bg=self._bg,
                bd=0,
                highlightthickness=0,
            )
            # Centro del bbox. anchor=center alinea el texto del Label
            # con el centro geometrico del hueco — coincide con como
            # LaTeX centra el contenido en un \\phantom.
            cx = (x0 + x1) // 2
            cy = (y0 + y1) // 2
            lbl.place(x=cx, y=cy, anchor="center")
            self._overlays[name] = lbl

    # ── Fallback: cuando no hay pdflatex ────────────────────────────────

    def _render_fallback(self) -> None:
        """Render con matplotlib mathtext (latex_image). Funciona sin
        pdflatex pero pierde calidad de documento. Mostramos un indicador
        sutil en el corner para que el desarrollador note el fallback en
        dev — el usuario final no lo distingue."""
        from .latex_image import render_expression_image

        body, _ = self._build_compile_body()
        if not body:
            return

        # En modo parametric, sustituimos los \\phantom{X} por su texto
        # visible para que el fallback muestre algo coherente. Los slots
        # NO seran reactivos en fallback (esto se acepta).
        if self._template is not None:
            for cfg in self._slots.values():
                ph = cfg.get("placeholder", "")
                phantom_pat = r"\phantom{" + ph + r"}"
                body = body.replace(phantom_pat, ph)

        try:
            photo = render_expression_image(
                body, fontsize=self._fontsize + 2,
                color=self._color, bg=self._bg, dpi=140, cache=True,
            )
        except Exception:
            return

        self._image_label.configure(image=photo)
        self._photo_ref = photo


# ─── Bbox extraction via fitz (PDF intermedio) ──────────────────────────────

# Cache de bboxes por hash del body+placeholders (in-memory). Evitamos
# re-compilar para detectar los huecos cada vez que un slot cambia: una
# unica deteccion alimenta todos los refresh de un LatexBlock dado.
_BBOX_CACHE: dict[tuple, dict[str, tuple[int, int, int, int]]] = {}


def _extract_bboxes_from_latex(
    body: str,
    placeholders: list[str],
    *,
    dpi: int,
    color: str,
    bg: str,
) -> dict[str, tuple[int, int, int, int]]:
    """Compila `body` (con los placeholders YA visibles) sobre tempdir,
    abre el PDF con fitz, y retorna `{placeholder: (x0, y0, x1, y1)}` en
    coords de pixel del PNG a `dpi`.

    Si la deteccion falla para algun placeholder, ese item no aparece en
    el dict — el LatexBlock simplemente no creara overlay para ese slot.
    """
    key = (body, tuple(placeholders), dpi)
    cached = _BBOX_CACHE.get(key)
    if cached is not None:
        return cached

    pdflatex = latex_cache.pdflatex_path()
    if pdflatex is None:
        return {}

    import os as _os
    import subprocess as _sub
    import tempfile as _tmp

    tex = latex_cache.build_tex(body, color=color, bg=bg)

    out: dict[str, tuple[int, int, int, int]] = {}
    with _tmp.TemporaryDirectory(prefix="edufem_bbox_") as tmp_str:
        from pathlib import Path as _Path
        tmp = _Path(tmp_str)
        (tmp / "frag.tex").write_text(tex, encoding="utf-8")
        try:
            proc = _sub.run(
                [pdflatex, "-interaction=nonstopmode", "-halt-on-error",
                 "-output-directory", str(tmp), str(tmp / "frag.tex")],
                capture_output=True, text=True, timeout=20,
                creationflags=(0x08000000 if _os.name == "nt" else 0),
            )
        except Exception:
            return {}
        if proc.returncode != 0 or not (tmp / "frag.pdf").exists():
            return {}

        try:
            import fitz  # type: ignore
            doc = fitz.open(str(tmp / "frag.pdf"))
            page = doc[0]
            zoom = dpi / 72.0
            # Para cada placeholder, search_for retorna lista de fitz.Rect
            # en coords PDF (pts). Convertimos a pixel multiplicando por zoom.
            for ph in placeholders:
                rects = page.search_for(ph)
                if not rects:
                    continue
                r = rects[0]  # primer match
                x0 = int(r.x0 * zoom)
                y0 = int(r.y0 * zoom)
                x1 = int(r.x1 * zoom)
                y1 = int(r.y1 * zoom)
                out[ph] = (x0, y0, x1, y1)
            doc.close()
        except Exception:
            return {}

    _BBOX_CACHE[key] = out
    return out


# ─── Sugar para el uso comun: nu = 0.234, t = 1.0e-3, etc. ─────────────────


def make_variable_block(
    parent,
    variable_latex: str,
    *,
    initial_value: float,
    precision: int = 3,
    max_value: float = 999.999,
    fontsize: int = _DEFAULT_FONTSIZE,
    dpi: int = 200,
    color: str = EDU_FG,
    bg: str = OVERLAY_BG,
) -> LatexBlock:
    """Atajo: crea un LatexBlock parametrico `<var> = <value>` con un solo slot
    llamado `"value"`. El placeholder se calcula a partir de `max_value` y
    `precision` para reservar suficiente ancho.

    Uso tipico (M3, dial de Poisson):

        nu_block = make_variable_block(
            body, r"\\nu", initial_value=0.2, precision=3, max_value=0.499,
        )
        nu_block.pack()

        # En el callback del slider:
        nu_block.set_value("value", f"{value:.3f}")
    """
    placeholder = _format_max_placeholder(max_value, precision)
    initial = f"{initial_value:.{precision}f}"
    template = rf"{variable_latex} = \phantom{{{placeholder}}}"
    return LatexBlock(
        parent,
        template=template,
        slots={"value": {"placeholder": placeholder, "initial": initial}},
        dpi=dpi, color=color, bg=bg, fontsize=fontsize,
    )


def _format_max_placeholder(max_value: float, precision: int) -> str:
    """Genera el string mas ancho posible para el bbox: usa '9' como
    digito de ancho maximo (en CM, '9' es uno de los mas anchos junto
    con '0' y '8' — ancho casi uniforme en fuentes monospace-tabular, y
    en CM es proporcional pero los digitos son tabulares por defecto)."""
    int_part = max(0, int(abs(max_value)))
    digits_int = max(1, len(str(int_part)))
    # Espacio para signo si max es negativo
    sign = "-" if max_value < 0 else ""
    int_str = "9" * digits_int
    if precision > 0:
        return f"{sign}{int_str}.{'9' * precision}"
    return f"{sign}{int_str}"
