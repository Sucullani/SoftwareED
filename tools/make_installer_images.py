"""Genera las imagenes del asistente de instalacion -> installer/assets/*.bmp

Inno Setup viste el asistente con dos imagenes: un panel vertical en las
paginas de Bienvenida y Finalizacion (`WizardImageFile`) y un sello chico en
la cabecera de las paginas intermedias (`WizardSmallImageFile`). Sin ellas el
instalador muestra el dibujo generico de Inno, que es lo que delata a un
instalador improvisado.

Formato obligatorio: **BMP de 24 bits** (Inno no lee PNG). Como Windows elige
la imagen segun el escalado de pantalla, se emite la serie completa de tamanos
que documenta Inno; el .iss los lista separados por coma y el instalador toma
el que corresponde al DPI del equipo.

Diseno: el panel repite la identidad del programa —fondo oscuro del tema
`darkly`, el icono birrete-malla, el nombre y una barra con el colormap JET,
que es la firma visual de los resultados— y el sello chico va sobre blanco,
que es el fondo de la cabecera del asistente en estilo moderno.

Regenerar:
    python tools/make_installer_images.py
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

# Tamanos que Inno Setup admite para cada imagen (ancho x alto), en el orden
# en que se listan en el .iss. El primero es el de referencia (100 % de DPI).
LARGE_SIZES = [(164, 314), (192, 386), (246, 459), (328, 604)]
SMALL_SIZES = [(55, 55), (83, 80), (110, 106), (138, 140), (164, 161)]

SS = 4                                  # supersampling del render

BG_TOP = (26, 32, 44)                   # panel: degradado del tema oscuro
BG_BOTTOM = (13, 17, 23)
TEXT = (245, 248, 252)
TEXT_MUTED = (150, 163, 180)
SMALL_BG = (255, 255, 255)              # cabecera del asistente moderno

TITLE = "EduFEM"
SUBTITLE = "Elementos Finitos 2D"
FOOT_1 = "Tensión y deformación plana"
FOOT_2 = "Elementos Q4 y Q9"


def jet(t: float) -> tuple[int, int, int]:
    """Colormap JET clasico (el mismo de los resultados) para t en [0, 1]."""
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)

    def ch(x: float) -> int:
        return int(max(0.0, min(1.0, x)) * 255)

    return (ch(1.5 - abs(4 * t - 3)),
            ch(1.5 - abs(4 * t - 2)),
            ch(1.5 - abs(4 * t - 1)))


def _font(size: int, bold: bool = False):
    """Segoe UI si esta (Windows); si no, la que haya. Nunca falla: la imagen
    con la fuente por defecto de Pillow sigue siendo legible."""
    for name in (("segoeuib.ttf", "seguibl.ttf") if bold else ("segoeui.ttf",)):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _vertical_gradient(size: tuple[int, int], top, bottom) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3)))
    return img


def _centered(d: ImageDraw.ImageDraw, y: int, text: str, font, fill, width: int):
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font)
    d.text(((width - (x1 - x0)) / 2 - x0, y), text, font=font, fill=fill)
    return y1 - y0


def build_large(size: tuple[int, int], icon: Image.Image) -> Image.Image:
    """Panel vertical de las paginas de Bienvenida y Finalizacion."""
    w, h = size[0] * SS, size[1] * SS
    img = _vertical_gradient((w, h), BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)

    # Bloque de marca (icono + nombre + subtitulo + barra JET) agrupado en la
    # mitad superior: el asistente de Inno superpone su propio texto sobre la
    # derecha del panel, y el bloque compacto lee mejor que repartido.
    ico = int(w * 0.46)
    scaled = icon.resize((ico, ico), Image.Resampling.LANCZOS)
    img.paste(scaled, (int((w - ico) / 2), int(h * 0.10)), scaled)

    y = int(h * 0.10 + ico + h * 0.030)
    y += _centered(d, y, TITLE, _font(int(w * 0.155), bold=True), TEXT, w) + int(h * 0.028)
    y += _centered(d, y, SUBTITLE, _font(int(w * 0.062)), TEXT_MUTED, w) + int(h * 0.034)

    # Barra JET: la firma visual de los resultados del programa.
    bar_h, margin = max(2, int(h * 0.016)), int(w * 0.16)
    for x in range(margin, w - margin):
        t = (x - margin) / max(1, (w - 2 * margin) - 1)
        d.line([(x, y), (x, y + bar_h)], fill=jet(t))

    # Pie: que cubre el problema que resuelve, en la zona que el asistente
    # deja libre debajo de su texto.
    foot = _font(int(w * 0.050))
    y = int(h * 0.885)
    y += _centered(d, y, FOOT_1, foot, TEXT_MUTED, w) + int(h * 0.014)
    _centered(d, y, FOOT_2, foot, TEXT_MUTED, w)

    return img.resize(size, Image.Resampling.LANCZOS)


def build_small(size: tuple[int, int], icon: Image.Image) -> Image.Image:
    """Sello de la cabecera de las paginas intermedias (fondo claro)."""
    w, h = size[0] * SS, size[1] * SS
    img = Image.new("RGB", (w, h), SMALL_BG)
    ico = int(min(w, h) * 0.86)
    scaled = icon.resize((ico, ico), Image.Resampling.LANCZOS)
    img.paste(scaled, (int((w - ico) / 2), int((h - ico) / 2)), scaled)
    return img.resize(size, Image.Resampling.LANCZOS)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.normpath(os.path.join(here, ".."))
    icon_png = os.path.join(root, "resources", "icons", "edufem_preview.png")
    if not os.path.exists(icon_png):
        raise SystemExit(
            f"Falta {icon_png}. Correr antes: python tools/make_icon.py")
    icon = Image.open(icon_png).convert("RGBA")

    out_dir = os.path.join(root, "installer", "assets")
    os.makedirs(out_dir, exist_ok=True)

    written = []
    for size in LARGE_SIZES:
        path = os.path.join(out_dir, f"wizard-{size[0]}x{size[1]}.bmp")
        build_large(size, icon).save(path, "BMP")
        written.append(path)
    for size in SMALL_SIZES:
        path = os.path.join(out_dir, f"wizard-small-{size[0]}x{size[1]}.bmp")
        build_small(size, icon).save(path, "BMP")
        written.append(path)

    for path in written:
        print("Imagen del asistente:", os.path.relpath(path, root),
              f"({os.path.getsize(path) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
