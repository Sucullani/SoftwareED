"""Construye la presentación de defensa de la tesis EduFEM (PowerPoint editable).

Uso:
    python build_deck.py guion.json salida.pptx

El guion es un JSON con la lista de diapositivas; cada una declara un `layout`
del vocabulario de abajo y los campos que ese layout necesita. Todo lo que se
dibuja son formas, cuadros de texto, tablas e imágenes nativas de PowerPoint,
así que la presentación queda íntegramente editable.

Layouts: portada · seccion · bullets · dos_columnas · imagen · tabla · kpi ·
flujo · comparacion · ecuaciones · demo · cierre
"""
from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Emu, Inches, Pt

# ---------------------------------------------------------------------------
# Sistema visual
# ---------------------------------------------------------------------------
NAVY = RGBColor(0x1B, 0x2A, 0x4A)       # títulos, bandas de sección
NAVY_DEEP = RGBColor(0x11, 0x1B, 0x33)  # fondo de sección/cierre
ACCENT = RGBColor(0xF2, 0x8C, 0x28)     # naranja: acentos, remates
INK = RGBColor(0x1F, 0x29, 0x37)        # texto principal
MUTED = RGBColor(0x5B, 0x65, 0x75)      # texto secundario
CARD = RGBColor(0xF3, 0xF4, 0xF6)       # tarjetas
LINE = RGBColor(0xD1, 0xD5, 0xDB)       # bordes
TINT = RGBColor(0xE9, 0xF0, 0xFB)       # fondo de remate
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ON_DARK = RGBColor(0xC7, 0xD2, 0xE8)    # texto secundario sobre navy
Q4_BLUE = RGBColor(0x1F, 0x77, 0xB4)    # mismo azul que las curvas de la tesis
Q9_ORANGE = RGBColor(0xFF, 0x7F, 0x0E)  # mismo naranja que las curvas de la tesis

FONT = "Calibri"
MATH = "Cambria Math"

SLIDE_W = 13.333
SLIDE_H = 7.5
MX = 0.6            # margen lateral
TITLE_Y = 0.42
CONTENT_Y = 1.62
CONTENT_H = 4.55    # hasta el remate
REMATE_Y = 6.28
REMATE_H = 0.58
FOOTER_Y = 7.02

ROOT = os.path.dirname(os.path.abspath(__file__))
FIGURAS = os.path.normpath(os.path.join(ROOT, "..", "figuras"))

AVISOS: list[str] = []


def aviso(msg: str) -> None:
    AVISOS.append(msg)
    print("  ! " + msg)


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------
def _set_lang(run) -> None:
    run._r.get_or_add_rPr().set("lang", "es-ES")


def _style_run(run, size, bold=False, color=INK, font=FONT, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font
    run.font.color.rgb = color
    _set_lang(run)


def add_text(slide, x, y, w, h, text, size, bold=False, color=INK, font=FONT,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False,
             line_spacing=1.05, margins=(0.05, 0.03, 0.05, 0.03)):
    """Cuadro de texto simple. `text` admite '\n' para varios párrafos."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = [Inches(m) for m in margins]
    for i, line in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        _style_run(r, size, bold, color, font, italic)
    return tb


def _add_bullet_xml(paragraph, color: RGBColor, level: int = 0, char: str = "•"):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("marL", str(int(Inches(0.38 + 0.38 * level))))
    pPr.set("indent", str(-int(Inches(0.38))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum", "a:buClr", "a:buSzPct", "a:buFont"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    hexa = "%02X%02X%02X" % (color[0], color[1], color[2])
    pPr.append(parse_xml(f'<a:buClr {nsdecls("a")}><a:srgbClr val="{hexa}"/></a:buClr>'))
    pPr.append(parse_xml(f'<a:buSzPct {nsdecls("a")} val="100000"/>'))
    pPr.append(parse_xml(f'<a:buFont {nsdecls("a")} typeface="Arial"/>'))
    pPr.append(parse_xml(f'<a:buChar {nsdecls("a")} char="{char}"/>'))


def est_lines(text: str, size_pt: float, width_in: float, char_w: float = 0.50) -> int:
    """Estimación conservadora de líneas que ocupa un texto en Calibri."""
    chars_per_line = max(1, int(width_in * 72 / (size_pt * char_w)))
    n = 0
    for para in str(text).split("\n"):
        n += max(1, math.ceil(len(para) / chars_per_line))
    return n


def fit_size(items, width_in, height_in, start, floor, line_h=1.18, gap_pt=10, indent_in=0.0):
    """Mayor tamaño de fuente (de `start` hacia `floor`, de a 1 pt) con el que cabe la lista."""
    for s in range(int(start), int(floor) - 1, -1):
        total = sum(est_lines(t, s, width_in - indent_in) for t in items) * s * line_h / 72
        total += max(0, len(items) - 1) * gap_pt / 72
        if total <= height_in:
            return s
    return int(floor)


def add_bullets(slide, x, y, w, h, items, size=24, color=INK, bullet_color=ACCENT,
                gap_pt=10, min_size=20, anchor=MSO_ANCHOR.TOP, bold_prefix=True):
    """Lista con viñetas reales (editables). Si `bold_prefix`, un 'Texto: resto' resalta 'Texto:'."""
    items = [str(i) for i in items if str(i).strip()]
    if not items:
        return None
    s = fit_size(items, w, h, size, min_size, gap_pt=gap_pt, indent_in=0.38)
    if s < size:
        aviso(f"viñetas reducidas a {s} pt para que quepan: {items[0][:40]}…")
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.12
        p.space_after = Pt(gap_pt)
        _add_bullet_xml(p, bullet_color)
        head, sep, tail = item.partition(":")
        if bold_prefix and sep and 0 < len(head) <= 32 and tail.strip():
            r1 = p.add_run()
            r1.text = head + ":"
            _style_run(r1, s, True, NAVY)
            r2 = p.add_run()
            r2.text = tail
            _style_run(r2, s, False, color)
        else:
            r = p.add_run()
            r.text = item
            _style_run(r, s, False, color)
    return tb


def add_rect(slide, x, y, w, h, fill=CARD, line=None, rounded=False, radius=0.06, line_w=0.75):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        shp.adjustments[0] = radius
    shp.shadow.inherit = False
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    shp.text_frame.text = ""
    return shp


def shape_text(shp, text, size, bold=False, color=WHITE, font=FONT, align=PP_ALIGN.CENTER,
               anchor=MSO_ANCHOR.MIDDLE, margins=(0.08, 0.04, 0.08, 0.04), line_spacing=1.0):
    tf = shp.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = [Inches(m) for m in margins]
    lines = str(text).split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run()
        r.text = line
        _style_run(r, size, bold, color, font)


def add_picture_fit(slide, path, x, y, w, h, border=True, align="center"):
    """Inserta la imagen manteniendo la proporción, centrada en la caja (x, y, w, h)."""
    if not os.path.isfile(path):
        aviso(f"imagen no encontrada: {path}")
        ph = add_rect(slide, x, y, w, h, fill=CARD, line=LINE)
        shape_text(ph, "[imagen no encontrada]\n" + os.path.basename(path), 16, color=MUTED)
        return ph
    with Image.open(path) as im:
        iw, ih = im.size
    ar = iw / ih
    if w / h > ar:
        ph_h = h
        ph_w = h * ar
    else:
        ph_w = w
        ph_h = w / ar
    px = x + (w - ph_w) / 2 if align == "center" else x
    py = y + (h - ph_h) / 2
    pic = slide.shapes.add_picture(path, Inches(px), Inches(py), Inches(ph_w), Inches(ph_h))
    if border:
        pic.line.color.rgb = LINE
        pic.line.width = Pt(0.75)
    return pic


def set_notes(slide, text):
    if text:
        slide.notes_slide.notes_text_frame.text = str(text)


def add_slide_number(slide, x, y, w, h, color=MUTED, size=12, align=PP_ALIGN.RIGHT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    hexa = "%02X%02X%02X" % (color[0], color[1], color[2])
    fld = parse_xml(
        f'<a:fld {nsdecls("a")} id="{{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}}" type="slidenum">'
        f'<a:rPr lang="es-ES" sz="{int(size * 100)}" dirty="0"><a:solidFill><a:srgbClr val="{hexa}"/></a:solidFill>'
        f'<a:latin typeface="{FONT}"/></a:rPr><a:t>1</a:t></a:fld>'
    )
    p._p.append(fld)
    return tb


# ---------------------------------------------------------------------------
# Marco común de las diapositivas de contenido
# ---------------------------------------------------------------------------
class Deck:
    def __init__(self, guion: dict):
        self.guion = guion
        self.prs = Presentation()
        self.prs.slide_width = Inches(SLIDE_W)
        self.prs.slide_height = Inches(SLIDE_H)
        self.blank = self.prs.slide_layouts[6]
        self.slides_data = guion["diapositivas"]
        # Bloques del hilo conductor: los títulos de las diapositivas "seccion", en orden.
        self.bloques = [d for d in self.slides_data if d.get("layout") == "seccion"]
        self.meta = guion.get("meta", {})

    # ---- piezas comunes -------------------------------------------------
    def new_slide(self, bg=None):
        s = self.prs.slides.add_slide(self.blank)
        if bg is not None:
            fill = s.background.fill
            fill.solid()
            fill.fore_color.rgb = bg
        return s

    def header(self, s, d, title_size=32):
        titulo = d.get("titulo", "")
        size = title_size if len(titulo) <= 44 else 28
        add_text(s, MX, TITLE_Y, SLIDE_W - 2 * MX - 3.2, 0.95, titulo, size, bold=True, color=NAVY,
                 anchor=MSO_ANCHOR.MIDDLE)
        # acento naranja bajo el título
        add_rect(s, MX + 0.05, TITLE_Y + 1.0, 1.1, 0.06, fill=ACCENT)
        # etiqueta del bloque (hilo conductor) arriba a la derecha
        bloque = d.get("bloque", "")
        if bloque:
            idx = self.bloque_index(bloque)
            label = f"{idx}  ·  {bloque}" if idx else bloque
            pill = add_rect(s, SLIDE_W - MX - 3.1, TITLE_Y + 0.22, 3.1, 0.46, fill=CARD, rounded=True, radius=0.5)
            shape_text(pill, label, 13, bold=True, color=NAVY)

    def bloque_index(self, bloque):
        for i, b in enumerate(self.bloques, start=1):
            if b.get("bloque") == bloque:
                return i
        return 0

    def footer(self, s, d):
        add_rect(s, MX, FOOTER_Y - 0.08, SLIDE_W - 2 * MX, 0.01, fill=LINE)
        add_text(s, MX, FOOTER_Y, 5.5, 0.32, self.meta.get("pie", "EduFEM · Defensa de tesis · Ingeniería Civil · UATF"),
                 12, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)
        fuente = d.get("fuente", "")
        if fuente:
            if len(fuente) > 72:
                fuente = fuente[:70].rstrip(" ,;") + "…"
            add_text(s, 4.4, FOOTER_Y, 5.9, 0.32, "Tesis: " + fuente, 12 if len(fuente) <= 58 else 11, color=MUTED,
                     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        add_slide_number(s, SLIDE_W - MX - 1.2, FOOTER_Y, 1.2, 0.32)

    @staticmethod
    def remate_geom(text):
        """(y, h, tamaño) de la barra de remate: crece a dos líneas si el texto lo pide."""
        if not text:
            return REMATE_Y, 0.0, 22
        w = SLIDE_W - 2 * MX - 0.35
        size = 22 if len(text) <= 95 else 20
        lines = est_lines(text, size, w, char_w=0.53)
        if lines <= 1:
            return REMATE_Y, REMATE_H, size
        h = 0.92
        return REMATE_Y + REMATE_H - h, h, size

    def remate(self, s, text):
        if not text:
            return
        y, h, size = self.remate_geom(text)
        x, w = MX, SLIDE_W - 2 * MX
        add_rect(s, x, y, w, h, fill=TINT)
        add_rect(s, x, y, 0.09, h, fill=ACCENT)
        add_text(s, x + 0.25, y, w - 0.35, h, text, size, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE,
                 line_spacing=1.0)

    def content_box(self, d):
        """(y, h) del área de contenido según haya remate o no, y de qué alto."""
        y, h, _ = self.remate_geom(d.get("remate"))
        if h:
            return CONTENT_Y, y - CONTENT_Y - 0.1
        return CONTENT_Y, REMATE_Y + REMATE_H - CONTENT_Y

    def fig(self, name):
        name = str(name or "").strip()
        if not name:
            return ""
        if not name.lower().endswith(".png"):
            name += ".png"
        return os.path.join(FIGURAS, name)

    # ---- layouts -----------------------------------------------------------
    def portada(self, d):
        s = self.new_slide(WHITE)
        add_rect(s, 0, 0, SLIDE_W, 0.32, fill=NAVY)
        add_rect(s, 0, 0.32, SLIDE_W, 0.05, fill=ACCENT)
        m = self.meta
        # Columna izquierda: encabezado institucional + título + autor
        add_text(s, 0.8, 0.75, 8.0, 0.5, m.get("universidad", "Universidad Autónoma «Tomás Frías»").upper(),
                 20, bold=True, color=NAVY)
        add_text(s, 0.8, 1.2, 8.0, 0.4, m.get("facultad", "Facultad de Ingeniería").upper(), 16, bold=True, color=MUTED)
        add_text(s, 0.8, 1.55, 8.0, 0.4, m.get("carrera", "Carrera de Ingeniería Civil").upper(), 16, bold=True, color=MUTED)
        add_rect(s, 0.85, 2.15, 1.1, 0.06, fill=ACCENT)
        titulo = m.get("titulo", d.get("titulo", ""))
        add_text(s, 0.8, 2.35, 8.3, 2.1, titulo.upper(), 28, bold=True, color=NAVY, anchor=MSO_ANCHOR.TOP,
                 line_spacing=1.08)
        add_text(s, 0.8, 4.55, 8.3, 0.45, "Tesis para optar al " + m.get("grado", "Título de Licenciatura en Ingeniería Civil"),
                 18, color=INK)
        add_text(s, 0.8, 5.25, 8.3, 0.45, "Autor:  " + m.get("autor", ""), 22, bold=True, color=NAVY)
        add_text(s, 0.8, 5.75, 8.3, 0.45, "Director:  " + m["director"] if m.get("director") else "", 18, color=INK)
        add_text(s, 0.8, 6.45, 8.3, 0.45, f"{m.get('ciudad', 'Potosí – Bolivia')}   ·   {m.get('fecha', '')}", 18, color=MUTED)
        # Columna derecha: escudo y logo de EduFEM
        add_picture_fit(s, self.fig("logo_universidad"), 9.55, 0.9, 3.0, 3.0, border=False)
        add_picture_fit(s, self.fig("fig_logo_edufem"), 9.9, 4.15, 2.3, 2.3, border=False)
        add_text(s, 9.3, 6.4, 3.5, 0.5, "EduFEM", 22, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        set_notes(s, d.get("notas"))
        return s

    def seccion(self, d):
        s = self.new_slide(NAVY_DEEP)
        idx = self.bloque_index(d.get("bloque", "")) or (self.bloques.index(d) + 1 if d in self.bloques else 0)
        add_text(s, 0.8, 1.55, 2.4, 2.0, f"{idx:02d}" if idx else "", 96, bold=True, color=ACCENT,
                 anchor=MSO_ANCHOR.MIDDLE)
        add_rect(s, 3.35, 1.85, 0.06, 1.45, fill=ACCENT)
        add_text(s, 3.7, 1.55, 9.0, 1.3, d.get("titulo", ""), 44, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        add_text(s, 3.7, 2.85, 9.0, 1.4, d.get("subtitulo", ""), 22, color=ON_DARK, anchor=MSO_ANCHOR.TOP,
                 line_spacing=1.15)
        if d.get("bullets"):
            add_bullets(s, 3.7, 3.7, 9.0, 2.2, d["bullets"], size=22, color=ON_DARK, bullet_color=ACCENT,
                        min_size=18, bold_prefix=False)
        # Hilo conductor: chips de todos los bloques, con el actual resaltado
        n = len(self.bloques)
        if n:
            gap = 0.12
            cw = (SLIDE_W - 2 * MX - gap * (n - 1)) / n
            y = 6.3
            for i, b in enumerate(self.bloques):
                x = MX + i * (cw + gap)
                actual = (b is d)
                pasado = self.bloques.index(b) < (self.bloques.index(d) if d in self.bloques else 0)
                fill = ACCENT if actual else (RGBColor(0x2A, 0x3B, 0x60) if pasado else RGBColor(0x1C, 0x28, 0x45))
                chip = add_rect(s, x, y, cw, 0.62, fill=fill, rounded=True, radius=0.25)
                shape_text(chip, f"{i + 1}. {b.get('bloque', b.get('titulo', ''))}", 12,
                           bold=actual, color=WHITE if (actual or pasado) else ON_DARK, margins=(0.05, 0.02, 0.05, 0.02))
        set_notes(s, d.get("notas"))
        return s

    def bullets(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        items = d.get("bullets", [])
        if d.get("subtitulo"):
            add_text(s, MX, y, SLIDE_W - 2 * MX, 0.5, d["subtitulo"], 20, color=MUTED, italic=True)
            y += 0.55
            h -= 0.55
        add_bullets(s, MX + 0.1, y + 0.1, SLIDE_W - 2 * MX - 0.2, h - 0.1, items, size=26 if len(items) <= 4 else 24,
                    gap_pt=14 if len(items) <= 4 else 10, anchor=MSO_ANCHOR.MIDDLE if not d.get("subtitulo") else MSO_ANCHOR.TOP)
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def dos_columnas(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        img = self.fig(d.get("imagen"))
        left_w = 5.75 if img else 5.9
        add_bullets(s, MX + 0.05, y + 0.05, left_w, h - 0.1, d.get("bullets", []), size=24, gap_pt=12,
                    min_size=19, anchor=MSO_ANCHOR.MIDDLE)
        rx = MX + left_w + 0.45
        rw = SLIDE_W - MX - rx
        if img:
            cap = d.get("caption", "")
            cap_h = 0.55 if cap else 0
            pic = add_picture_fit(s, img, rx, y, rw, h - cap_h - 0.05)
            if cap:
                # el caption va pegado al borde inferior real de la imagen
                bottom = (pic.top + pic.height) / 914400
                add_text(s, rx, bottom + 0.05, rw, cap_h, cap, 15, color=MUTED, align=PP_ALIGN.CENTER,
                         anchor=MSO_ANCHOR.TOP, italic=True)
        elif d.get("columna_derecha"):
            card = add_rect(s, rx, y, rw, h, fill=CARD, rounded=True, radius=0.04)
            add_bullets(s, rx + 0.2, y + 0.2, rw - 0.4, h - 0.4, d["columna_derecha"], size=22, gap_pt=10,
                        anchor=MSO_ANCHOR.MIDDLE, bullet_color=NAVY)
        elif d.get("kpis"):
            self._kpi_cards(s, d["kpis"], rx, y, rw, h, cols=1 if len(d["kpis"]) <= 3 else 2)
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def imagen(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        cap = d.get("caption", "")
        cap_h = 0.5 if cap else 0
        pic = add_picture_fit(s, self.fig(d.get("imagen")), MX, y, SLIDE_W - 2 * MX, h - cap_h - 0.05)
        if cap:
            bottom = (pic.top + pic.height) / 914400
            add_text(s, MX, bottom + 0.04, SLIDE_W - 2 * MX, cap_h, cap, 16, color=MUTED, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.TOP, italic=True)
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def tabla(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        t = d.get("tabla") or {}
        cab = [str(c) for c in t.get("cabeceras", [])]
        filas = [[str(c) for c in f] for f in t.get("filas", [])]
        ncols = max(len(cab), max((len(f) for f in filas), default=0))
        nrows = len(filas) + 1
        if ncols == 0 or nrows == 1:
            aviso(f"tabla vacía en la diapositiva {d.get('n')}")
        sub = d.get("subtitulo", "")
        if sub:
            add_text(s, MX, y, SLIDE_W - 2 * MX, 0.45, sub, 18, color=MUTED, italic=True)
            y += 0.5
            h -= 0.5
        size = 22 if nrows <= 5 else (20 if nrows <= 7 else 18)
        # ancho por columna proporcional al contenido, con un mínimo que no parte la palabra más larga
        table_w = SLIDE_W - 2 * MX
        cols_txt = []
        for c in range(ncols):
            cols_txt.append([cab[c] if c < len(cab) else ""] + [f[c] if c < len(f) else "" for f in filas])
        lens = [max(4, max(len(x) for x in col)) for col in cols_txt]
        longest_word = [max((len(w) for x in col for w in x.split()), default=4) for col in cols_txt]

        def widths_for(sz):
            tot = sum(lens)
            ws = []
            for L, lw in zip(lens, longest_word):
                minimum = max(1.1, lw * sz * 0.55 / 72 + 0.25)
                ws.append(max(minimum, table_w * L / tot))
            k = table_w / sum(ws)
            return [w * k for w in ws]

        def row_heights_for(sz, ws):
            hs = []
            for r in range(nrows):
                lines = 1
                for c in range(ncols):
                    txt = cols_txt[c][r]
                    lines = max(lines, est_lines(txt, sz, ws[c] - 0.16, char_w=0.52))
                hs.append(lines * sz * 1.2 / 72 + 0.14)
            return hs

        while True:
            widths = widths_for(size)
            row_hs = row_heights_for(size, widths)
            if sum(row_hs) <= h or size <= 15:
                break
            size -= 1
        if size < (22 if nrows <= 5 else (20 if nrows <= 7 else 18)):
            aviso(f"tabla de la diapositiva {d.get('n')} reducida a {size} pt")
        # si sobra alto, repartilo (filas más cómodas, tope 0,62 in)
        extra = max(0.0, h - sum(row_hs))
        row_hs = [min(0.62, rh + extra / nrows) for rh in row_hs]
        table_h = sum(row_hs)
        ty = y + (h - table_h) / 2
        gt = s.shapes.add_table(nrows, ncols, Inches(MX), Inches(ty), Inches(table_w), Inches(table_h))
        tbl = gt.table
        # sin estilo predefinido: pintamos las celdas nosotros
        tblPr = tbl._tbl.tblPr
        for attr in ("bandRow", "firstRow"):
            tblPr.set(attr, "0")
        for c, wdt in enumerate(widths):
            tbl.columns[c].width = Inches(wdt)
        for r in range(nrows):
            tbl.rows[r].height = Inches(row_hs[r])
            for c in range(ncols):
                cell = tbl.cell(r, c)
                if r == 0:
                    txt = cab[c] if c < len(cab) else ""
                else:
                    f = filas[r - 1]
                    txt = f[c] if c < len(f) else ""
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY if r == 0 else (WHITE if r % 2 else CARD)
                cell.margin_left = cell.margin_right = Inches(0.08)
                cell.margin_top = cell.margin_bottom = Inches(0.03)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf = cell.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
                run = p.add_run()
                run.text = txt
                _style_run(run, size, bold=(r == 0 or c == 0), color=WHITE if r == 0 else INK)
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def _kpi_cards(self, s, kpis, x, y, w, h, cols=None):
        n = len(kpis)
        cols = cols or n
        rows = math.ceil(n / cols)
        gap = 0.3
        cw = (w - gap * (cols - 1)) / cols
        ch = min(3.3, (h - gap * (rows - 1)) / rows)
        y0 = y + (h - (ch * rows + gap * (rows - 1))) / 2
        for i, k in enumerate(kpis):
            r, c = divmod(i, cols)
            cx = x + c * (cw + gap)
            cy = y0 + r * (ch + gap)
            add_rect(s, cx, cy, cw, ch, fill=CARD, rounded=True, radius=0.07)
            add_rect(s, cx + 0.25, cy + 0.3, 0.6, 0.07, fill=ACCENT)
            valor = str(k.get("valor", ""))
            vs = 44 if len(valor) <= 8 else (36 if len(valor) <= 12 else 28)
            add_text(s, cx + 0.2, cy + 0.45, cw - 0.4, 1.1, valor, vs, bold=True, color=NAVY,
                     anchor=MSO_ANCHOR.MIDDLE)
            etiqueta = str(k.get("etiqueta", ""))
            label_h = ch - 1.75
            es = 18 if est_lines(etiqueta, 18, cw - 0.4, char_w=0.5) * 18 * 1.15 / 72 <= label_h else 16
            add_text(s, cx + 0.2, cy + 1.6, cw - 0.4, label_h, etiqueta, es, color=MUTED,
                     anchor=MSO_ANCHOR.TOP, line_spacing=1.1)

    def kpi(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        kpis = d.get("kpis", [])
        if d.get("subtitulo"):
            add_text(s, MX, y, SLIDE_W - 2 * MX, 0.5, d["subtitulo"], 20, color=MUTED, italic=True)
            y += 0.55
            h -= 0.55
        cols = len(kpis) if len(kpis) <= 4 else 3
        self._kpi_cards(s, kpis, MX, y, SLIDE_W - 2 * MX, h, cols=cols)
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def flujo(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        pasos = d.get("pasos", [])
        n = len(pasos)
        if d.get("subtitulo"):
            add_text(s, MX, y, SLIDE_W - 2 * MX, 0.5, d["subtitulo"], 20, color=MUTED, italic=True)
            y += 0.55
            h -= 0.55
        per_row = n if n <= 5 else math.ceil(n / 2)
        rows = math.ceil(n / per_row)
        arrow_w = 0.42
        gap = 0.12
        cw = (SLIDE_W - 2 * MX - (per_row - 1) * (arrow_w + 2 * gap)) / per_row
        # alto del chip según lo que piden rótulo (≤ 2 líneas a 20 pt) y sublínea (≤ 2 líneas a 13 pt)
        any_sub = any(str(p.get("sub", "") or "") for p in pasos)
        ch = 1.55 if any_sub else 1.1
        total_h = rows * ch + (rows - 1) * 0.5
        y0 = y + (h - total_h) / 2
        for i, p in enumerate(pasos):
            r, c = divmod(i, per_row)
            cx = MX + c * (cw + arrow_w + 2 * gap)
            cy = y0 + r * (ch + 0.5)
            chip = add_rect(s, cx, cy, cw, ch, fill=NAVY, rounded=True, radius=0.12)
            label = str(p.get("etiqueta", ""))
            sub = str(p.get("sub", "") or "")
            ls = 20 if est_lines(label, 20, cw - 0.16, char_w=0.55) <= 1 else 17
            if sub:
                # rótulo arriba y sublínea abajo, cada uno en su propia caja: nunca se pisan
                add_text(s, cx, cy + 0.1, cw, 0.8, label, ls, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
                         anchor=MSO_ANCHOR.TOP, line_spacing=1.0, margins=(0.08, 0.02, 0.08, 0.02))
                ss = 13 if est_lines(sub, 13, cw - 0.16, char_w=0.5) <= 2 else 11
                add_text(s, cx, cy + ch - 0.62, cw, 0.55, sub, ss, color=ON_DARK, align=PP_ALIGN.CENTER,
                         anchor=MSO_ANCHOR.BOTTOM, line_spacing=1.0, margins=(0.08, 0.02, 0.08, 0.06))
            else:
                shape_text(chip, label, ls, bold=True, color=WHITE)
            if c < per_row - 1 and i < n - 1:
                ax = cx + cw + gap
                arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax), Inches(cy + ch / 2 - 0.16),
                                         Inches(arrow_w), Inches(0.32))
                arr.shadow.inherit = False
                arr.fill.solid()
                arr.fill.fore_color.rgb = ACCENT
                arr.line.fill.background()
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def comparacion(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        tarjetas = d.get("tarjetas", [])[:2]
        if d.get("subtitulo"):
            add_text(s, MX, y, SLIDE_W - 2 * MX, 0.5, d["subtitulo"], 20, color=MUTED, italic=True)
            y += 0.55
            h -= 0.55
        gap = 0.4
        cw = (SLIDE_W - 2 * MX - gap) / max(1, len(tarjetas))
        for i, t in enumerate(tarjetas):
            cx = MX + i * (cw + gap)
            titulo = str(t.get("titulo", ""))
            up = titulo.upper()
            head_fill = Q4_BLUE if up.startswith("Q4") else (Q9_ORANGE if up.startswith("Q9") else (NAVY if i == 0 else ACCENT))
            add_rect(s, cx, y, cw, h, fill=CARD, rounded=True, radius=0.05)
            add_rect(s, cx, y, cw, 0.66, fill=head_fill, rounded=True, radius=0.12)
            add_rect(s, cx, y + 0.36, cw, 0.30, fill=head_fill)  # cuadra la base de la cabecera
            ts = 24 if est_lines(titulo, 24, cw - 0.3, char_w=0.55) <= 1 else 20
            add_text(s, cx, y, cw, 0.66, titulo, ts, bold=True, color=WHITE, align=PP_ALIGN.CENTER,
                     anchor=MSO_ANCHOR.MIDDLE)
            add_bullets(s, cx + 0.25, y + 0.78, cw - 0.5, h - 0.9, t.get("lineas", []), size=22, gap_pt=9,
                        min_size=18, bullet_color=head_fill, anchor=MSO_ANCHOR.MIDDLE)
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def ecuaciones(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        eqs = d.get("ecuaciones", [])
        if d.get("subtitulo"):
            add_text(s, MX, y, SLIDE_W - 2 * MX, 0.5, d["subtitulo"], 20, color=MUTED, italic=True)
            y += 0.55
            h -= 0.55
        n = max(1, len(eqs))
        rh = min(1.35, h / n)
        y0 = y + (h - rh * n) / 2
        name_w = 3.7
        for i, e in enumerate(eqs):
            ry = y0 + i * rh
            add_rect(s, MX, ry + 0.12, SLIDE_W - 2 * MX, rh - 0.24, fill=CARD, rounded=True, radius=0.08)
            add_rect(s, MX, ry + 0.12, 0.09, rh - 0.24, fill=ACCENT)
            add_text(s, MX + 0.3, ry + 0.12, name_w - 0.3, rh - 0.24, str(e.get("nombre", "")), 19, bold=True,
                     color=MUTED, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05)
            txt = str(e.get("texto", ""))
            es = 30 if len(txt) <= 46 else (26 if len(txt) <= 64 else 22)
            add_text(s, MX + name_w, ry + 0.12, SLIDE_W - 2 * MX - name_w - 0.2, rh - 0.24, txt, es, color=NAVY,
                     font=MATH, anchor=MSO_ANCHOR.MIDDLE)
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def demo(self, d):
        s = self.new_slide(WHITE)
        self.header(s, d)
        y, h = self.content_box(d)
        img = self.fig(d.get("imagen") or "fig_app_completa")
        iw = 7.9
        add_picture_fit(s, img, MX, y, iw, h)
        rx = MX + iw + 0.4
        rw = SLIDE_W - MX - rx
        pasos = d.get("bullets") or [p.get("etiqueta", "") for p in d.get("pasos", [])]
        add_text(s, rx, y, rw, 0.5, d.get("subtitulo", "En vivo"), 20, bold=True, color=ACCENT)
        size = fit_size([str(p) for p in pasos], rw - 0.65, h - 0.7, 20, 16, line_h=1.15, gap_pt=22)
        py = y + 0.62
        for i, p in enumerate(pasos):
            step_h = est_lines(str(p), size, rw - 0.65) * size * 1.15 / 72 + 0.3
            circ = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(rx), Inches(py + 0.06), Inches(0.5), Inches(0.5))
            circ.shadow.inherit = False
            circ.fill.solid()
            circ.fill.fore_color.rgb = NAVY
            circ.line.fill.background()
            shape_text(circ, str(i + 1), 18, bold=True, color=WHITE, margins=(0, 0, 0, 0))
            add_text(s, rx + 0.65, py, rw - 0.65, step_h, str(p), size, color=INK, anchor=MSO_ANCHOR.TOP,
                     line_spacing=1.15)
            py += step_h
        self.remate(s, d.get("remate"))
        self.footer(s, d)
        set_notes(s, d.get("notas"))
        return s

    def cierre(self, d):
        s = self.new_slide(NAVY_DEEP)
        m = self.meta
        add_text(s, 0.8, 1.5, 8.0, 1.2, d.get("titulo", "Gracias"), 54, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        add_rect(s, 0.85, 2.75, 1.3, 0.07, fill=ACCENT)
        add_text(s, 0.8, 3.0, 8.2, 1.2, d.get("subtitulo", ""), 22, color=ON_DARK, line_spacing=1.15)
        if d.get("bullets"):
            add_bullets(s, 0.8, 4.1, 8.2, 1.6, d["bullets"], size=20, color=ON_DARK, bullet_color=ACCENT,
                        min_size=16, bold_prefix=False)
        add_text(s, 0.8, 5.75, 8.2, 0.5, m.get("autor", ""), 24, bold=True, color=WHITE)
        add_text(s, 0.8, 6.25, 8.2, 0.45, m.get("repo", "github.com/Sucullani/SoftwareED"), 20, color=ACCENT)
        add_picture_fit(s, self.fig("logo_universidad"), 9.6, 1.4, 2.6, 2.6, border=False)
        add_picture_fit(s, self.fig("fig_logo_edufem"), 9.75, 4.2, 2.3, 2.3, border=False)
        set_notes(s, d.get("notas"))
        return s

    # ---- construcción ----------------------------------------------------
    def build(self):
        builders = {
            "portada": self.portada, "seccion": self.seccion, "bullets": self.bullets,
            "dos_columnas": self.dos_columnas, "imagen": self.imagen, "tabla": self.tabla, "kpi": self.kpi,
            "flujo": self.flujo, "comparacion": self.comparacion, "ecuaciones": self.ecuaciones,
            "demo": self.demo, "cierre": self.cierre,
        }
        for d in self.slides_data:
            layout = d.get("layout", "bullets")
            fn = builders.get(layout)
            if fn is None:
                aviso(f"layout desconocido '{layout}' en la diapositiva {d.get('n')}; se usa bullets")
                fn = self.bullets
            print(f"  [{d.get('n'):>2}] {layout:<13} {d.get('titulo', '')[:60]}")
            fn(d)
        return self.prs


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as fh:
        guion = json.load(fh)
    out = sys.argv[2]
    deck = Deck(guion)
    prs = deck.build()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    prs.save(out)
    print(f"\nGuardado: {out}  ({len(prs.slides)} diapositivas)")
    if AVISOS:
        print(f"{len(AVISOS)} avisos de ajuste.")


if __name__ == "__main__":
    main()
