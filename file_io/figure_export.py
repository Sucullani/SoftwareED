"""
Renderizado de figuras para la Memoria de Cálculo.

Estrategia híbrida:

* **Renders espaciales** (campos sobre la malla: contornos, deformada,
  diagrama del modelo, cruces principales) usan **Pillow** + rasterización
  Gouraud por triángulos, replicando el aspecto del `MeshCanvas` del
  Post-Proceso pero con FONDO BLANCO (el PDF es impreso). Más legibles
  y consistentes con el lenguaje visual del software interactivo.
* **Renders esquemáticos** (círculo de Mohr, heatmap de K, diagrama del
  pipeline) usan matplotlib porque son figuras abstractas sin coordenadas
  del modelo.

Todas las funciones públicas retornan o bien una `PIL.Image.Image` o
bien un `matplotlib.figure.Figure`. El caller (`MemoriaCalculo._save_figure`)
inspecciona el tipo y guarda en disco.

Convenciones de color (paleta semántica de `config.settings`):
  * Nodos: azul (corner), azul claro (mid), violeta (center) — igual canvas.
  * Cargas: rojo (vector flecha hacia el nodo).
  * Restricciones: naranja (símbolo según tipo: empotramiento / rodillo X / rodillo Y).
  * Mallas deformadas: verde (PHASE_POST_COLOR).
  * Tracción σ₁ > 0: azul; Compresión σ₂ < 0: rojo.
  * Colormap del campo: JET por defecto (matchea MeshCanvas).
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from matplotlib.figure import Figure
from matplotlib.patches import (
    FancyArrowPatch as _FancyArrowPatch,
    FancyBboxPatch as _FancyBboxPatch,
)

from config.settings import (
    CANVAS_NODE_COLOR,
    CANVAS_NODE_MID_COLOR,
    CANVAS_NODE_CENTER_COLOR,
    CANVAS_CONSTRAINT_COLOR,
    CANVAS_LOAD_COLOR,
    ELEMENT_Q9,
    PHASE_PRE_COLOR,
    PHASE_PROC_COLOR,
    PHASE_POST_COLOR,
    PRINCIPAL_TENSION_COLOR,
    PRINCIPAL_COMPRESSION_COLOR,
)


# ───────────────────────────────────────────────────────────────────────────
# Parámetros comunes
# ───────────────────────────────────────────────────────────────────────────

_FIG_DPI = 150
_BG_WHITE = (255, 255, 255, 255)
_PAPER_GRAY = (95, 95, 95)         # gris medio: aristas / ejes / leyendas
_PAPER_DARK = (40, 40, 40)         # casi-negro: texto, números, contornos
_PAPER_LIGHT_GRID = (215, 215, 215)


def _hex_to_rgb(hexstr: str) -> tuple[int, int, int]:
    """Convierte '#rrggbb' a (R, G, B) entero. Acepta '#rgb' también."""
    s = hexstr.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return (r, g, b)


def _load_font(size: int = 12):
    """Carga una fuente TTF si está disponible, sino fallback al default.

    El default de PIL es bitmap fixed-size: feo pero portable.
    """
    if not HAS_PIL:
        return None
    candidates = (
        "DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "Arial.ttf",
        "arial.ttf",
    )
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ───────────────────────────────────────────────────────────────────────────
# Colormaps (mismas formulas que MeshCanvas)
# ───────────────────────────────────────────────────────────────────────────

def _jet_rgb(t: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """JET colormap vectorizado, idéntico a `MeshCanvas._jet_rgb_vectorized`.

    Aplica al campo de tensiones por default — replica el lenguaje
    cromático del Post-Proceso interactivo.
    """
    t = np.clip(t, 0, 1)
    r = np.zeros_like(t)
    g = np.zeros_like(t)
    b = np.zeros_like(t)
    m1 = t < 0.25
    m2 = (t >= 0.25) & (t < 0.5)
    m3 = (t >= 0.5) & (t < 0.75)
    m4 = t >= 0.75
    g[m1] = t[m1] / 0.25
    b[m1] = 1.0
    g[m2] = 1.0
    b[m2] = 1.0 - (t[m2] - 0.25) / 0.25
    r[m3] = (t[m3] - 0.5) / 0.25
    g[m3] = 1.0
    r[m4] = 1.0
    g[m4] = 1.0 - (t[m4] - 0.75) / 0.25
    return r, g, b


def _jet_rgb_one(t: float) -> tuple[int, int, int]:
    """Versión escalar para drawing puntual (colorbar)."""
    t = max(0.0, min(1.0, t))
    if t < 0.25:
        r, g, b = 0.0, t / 0.25, 1.0
    elif t < 0.5:
        r, g, b = 0.0, 1.0, 1.0 - (t - 0.25) / 0.25
    elif t < 0.75:
        r, g, b = (t - 0.5) / 0.25, 1.0, 0.0
    else:
        r, g, b = 1.0, 1.0 - (t - 0.75) / 0.25, 0.0
    return (int(r * 255), int(g * 255), int(b * 255))


# ───────────────────────────────────────────────────────────────────────────
# Transform world ↔ screen (espacio Pillow)
# ───────────────────────────────────────────────────────────────────────────

class _ViewTransform:
    """Encapsula la conversion entre coordenadas mundo y píxeles imagen.

    Eje Y de pantalla invertido respecto a mundo (igual que MeshCanvas).
    """

    __slots__ = ("scale", "offset_x", "offset_y", "width", "height")

    def __init__(self, xs, ys, width: int, height: int, padding: int = 40):
        if not xs:
            self.scale = 1.0
            self.offset_x = width / 2
            self.offset_y = height / 2
            self.width = width
            self.height = height
            return
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        span_x = max(x_max - x_min, 1e-9)
        span_y = max(y_max - y_min, 1e-9)
        avail_w = width - 2 * padding
        avail_h = height - 2 * padding
        self.scale = min(avail_w / span_x, avail_h / span_y)
        used_w = span_x * self.scale
        used_h = span_y * self.scale
        self.offset_x = padding + (avail_w - used_w) / 2 - x_min * self.scale
        self.offset_y = padding + (avail_h - used_h) / 2 + y_max * self.scale
        self.width = width
        self.height = height

    def w2s(self, x: float, y: float) -> tuple[float, float]:
        return x * self.scale + self.offset_x, -y * self.scale + self.offset_y


# ───────────────────────────────────────────────────────────────────────────
# Rasterizacion Gouraud (igual al MeshCanvas)
# ───────────────────────────────────────────────────────────────────────────

def _rasterize_triangle(img: np.ndarray, w: int, h: int,
                        p0, p1, p2, vmin: float, vrange: float) -> None:
    """Rasteriza un triangulo con interpolacion baricentrica + JET.

    Cada p = (sx, sy, valor). Misma logica que `MeshCanvas._rasterize_triangle`
    pero el fondo es blanco (no se escribe alpha por afuera del triangulo).
    """
    sx0, sy0, v0 = p0
    sx1, sy1, v1 = p1
    sx2, sy2, v2 = p2

    min_x = max(0, int(min(sx0, sx1, sx2)))
    max_x = min(w - 1, int(max(sx0, sx1, sx2)) + 1)
    min_y = max(0, int(min(sy0, sy1, sy2)))
    max_y = min(h - 1, int(max(sy0, sy1, sy2)) + 1)
    if min_x >= max_x or min_y >= max_y:
        return

    px = np.arange(min_x, max_x + 1, dtype=np.float64)
    py = np.arange(min_y, max_y + 1, dtype=np.float64)
    PX, PY = np.meshgrid(px, py)

    denom = (sy1 - sy2) * (sx0 - sx2) + (sx2 - sx1) * (sy0 - sy2)
    if abs(denom) < 1e-6:
        return

    lam0 = ((sy1 - sy2) * (PX - sx2) + (sx2 - sx1) * (PY - sy2)) / denom
    lam1 = ((sy2 - sy0) * (PX - sx2) + (sx0 - sx2) * (PY - sy2)) / denom
    lam2 = 1.0 - lam0 - lam1

    inside = (lam0 >= -0.001) & (lam1 >= -0.001) & (lam2 >= -0.001)
    if not np.any(inside):
        return

    vals = lam0 * v0 + lam1 * v1 + lam2 * v2
    t = np.clip((vals - vmin) / vrange, 0, 1)
    rc, gc, bc = _jet_rgb(t)

    iy = PY[inside].astype(int)
    ix = PX[inside].astype(int)
    valid = (iy >= 0) & (iy < h) & (ix >= 0) & (ix < w)
    iy, ix = iy[valid], ix[valid]
    img[iy, ix, 0] = (rc[inside][valid] * 255).astype(np.uint8)
    img[iy, ix, 1] = (gc[inside][valid] * 255).astype(np.uint8)
    img[iy, ix, 2] = (bc[inside][valid] * 255).astype(np.uint8)
    img[iy, ix, 3] = 255


def _render_field_to_array(project, node_values: dict, vmin: float, vmax: float,
                           width: int, height: int, *, deformed: bool = False,
                           deform_scale: float = 0.0,
                           subdiv: int = 8) -> tuple[np.ndarray, _ViewTransform]:
    """Construye el buffer RGBA del campo nodal sobre la malla.

    Cada Q4/Q9 macro se subdivide en (subdiv × subdiv) sub-quads vía las
    funciones de forma Q4 bilineales sobre los 4 vértices macro y los
    valores se interpolan bilinealmente entre nodos. Cada sub-quad se
    rasteriza como 2 triángulos Gouraud.
    """
    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    if deformed:
        u = project.displacements
        idx_map = project.node_index_map
        if u is not None:
            for nid, node in project.nodes.items():
                base = 2 * idx_map[nid]
                xs.append(node.x + deform_scale * u[base])
                ys.append(node.y + deform_scale * u[base + 1])
    view = _ViewTransform(xs, ys, width, height, padding=46)

    img = np.full((height, width, 4), 255, dtype=np.uint8)
    vrange = max(vmax - vmin, 1e-15)
    idx_map = project.node_index_map
    u = project.displacements if deformed else None

    for elem in project.elements.values():
        nids = elem.node_ids[:4]
        if not all(nid in project.nodes for nid in nids):
            continue
        if not all(nid in node_values for nid in nids):
            continue

        nv = [float(node_values[nid]) for nid in nids]
        nc = []
        for nid in nids:
            node = project.nodes[nid]
            x, y = node.x, node.y
            if u is not None:
                base = 2 * idx_map[nid]
                if base + 1 < len(u):
                    x += deform_scale * u[base]
                    y += deform_scale * u[base + 1]
            nc.append((x, y))

        n = subdiv
        pts_grid = {}
        for i in range(n + 1):
            xi = -1.0 + 2.0 * i / n
            for j in range(n + 1):
                eta = -1.0 + 2.0 * j / n
                N0 = (1 - xi) * (1 - eta) * 0.25
                N1 = (1 + xi) * (1 - eta) * 0.25
                N2 = (1 + xi) * (1 + eta) * 0.25
                N3 = (1 - xi) * (1 + eta) * 0.25
                wx = N0 * nc[0][0] + N1 * nc[1][0] + N2 * nc[2][0] + N3 * nc[3][0]
                wy = N0 * nc[0][1] + N1 * nc[1][1] + N2 * nc[2][1] + N3 * nc[3][1]
                val = N0 * nv[0] + N1 * nv[1] + N2 * nv[2] + N3 * nv[3]
                sx, sy = view.w2s(wx, wy)
                pts_grid[(i, j)] = (sx, sy, val)

        for i in range(n):
            for j in range(n):
                p00 = pts_grid[(i, j)]
                p10 = pts_grid[(i + 1, j)]
                p11 = pts_grid[(i + 1, j + 1)]
                p01 = pts_grid[(i, j + 1)]
                _rasterize_triangle(img, width, height, p00, p10, p11, vmin, vrange)
                _rasterize_triangle(img, width, height, p00, p11, p01, vmin, vrange)

    return img, view


def _draw_wireframe(draw: "ImageDraw.ImageDraw", project, view: _ViewTransform,
                    *, color=_PAPER_DARK, width: int = 1,
                    deformed: bool = False, deform_scale: float = 0.0) -> None:
    """Dibuja los contornos macro de cada elemento (4 aristas)."""
    u = project.displacements if deformed else None
    idx_map = project.node_index_map if deformed else None
    for elem in project.elements.values():
        coords = []
        for nid in elem.node_ids[:4]:
            node = project.nodes.get(nid)
            if node is None:
                coords = []
                break
            x, y = node.x, node.y
            if u is not None and idx_map is not None:
                base = 2 * idx_map[nid]
                if base + 1 < len(u):
                    x += deform_scale * u[base]
                    y += deform_scale * u[base + 1]
            coords.append(view.w2s(x, y))
        if len(coords) < 4:
            continue
        for k in range(4):
            p0 = coords[k]
            p1 = coords[(k + 1) % 4]
            draw.line([p0, p1], fill=color, width=width)


def _draw_colorbar(draw: "ImageDraw.ImageDraw", x: int, y: int, w: int, h: int,
                   vmin: float, vmax: float, *, label: str = "",
                   font=None) -> None:
    """Colorbar vertical: gradiente JET + ticks + label."""
    n_steps = 96
    for i in range(n_steps):
        t = 1.0 - i / n_steps   # max arriba
        c = _jet_rgb_one(t)
        y0 = y + int(i * h / n_steps)
        y1 = y + int((i + 1) * h / n_steps) + 1
        draw.rectangle([x, y0, x + w, y1], fill=c)
    draw.rectangle([x, y, x + w, y + h], outline=_PAPER_DARK, width=1)
    n_labels = 5
    for i in range(n_labels + 1):
        t = 1.0 - i / n_labels
        val = vmin + t * (vmax - vmin)
        yy = y + int(i * h / n_labels)
        draw.line([(x + w + 2, yy), (x + w + 6, yy)],
                  fill=_PAPER_DARK, width=1)
        s = f"{val:.3g}"
        draw.text((x + w + 9, yy - 7), s, fill=_PAPER_DARK, font=font)
    if label:
        draw.text((x - 4, y - 18), label, fill=_PAPER_DARK, font=font)


def _draw_axes_indicator(draw: "ImageDraw.ImageDraw", width: int, height: int,
                         font=None) -> None:
    """Triada XY discreta en la esquina inferior izquierda."""
    margin = 26
    length = 30
    bx, by = margin, height - margin
    # X (rojo)
    draw.line([(bx, by), (bx + length, by)], fill=(200, 50, 50), width=2)
    draw.polygon([(bx + length, by), (bx + length - 6, by - 4),
                  (bx + length - 6, by + 4)], fill=(200, 50, 50))
    draw.text((bx + length + 4, by - 6), "X", fill=(200, 50, 50), font=font)
    # Y (azul)
    draw.line([(bx, by), (bx, by - length)], fill=(50, 100, 200), width=2)
    draw.polygon([(bx, by - length), (bx - 4, by - length + 6),
                  (bx + 4, by - length + 6)], fill=(50, 100, 200))
    draw.text((bx - 4, by - length - 14), "Y", fill=(50, 100, 200), font=font)


# ───────────────────────────────────────────────────────────────────────────
# Render: Mapa de contornos
# ───────────────────────────────────────────────────────────────────────────

_COMPONENT_LABELS = {
    "sigma_x":   r"σ_x",
    "sigma_y":   r"σ_y",
    "tau_xy":    r"τ_xy",
    "von_mises": r"σ_VM",
    "sigma_1":   r"σ_1",
    "sigma_2":   r"σ_2",
}


def render_contour(project, solution, nodal_stresses, component: str,
                   *, deformed: bool = False, scale: Optional[float] = None,
                   width: int = 900, height: int = 660) -> Optional["Image.Image"]:
    """Mapa de contornos JET sobre la malla, estilo MeshCanvas + fondo blanco.

    Component ∈ {"sigma_x", "sigma_y", "tau_xy", "von_mises", "sigma_1", "sigma_2"}.
    Si `deformed=True`, se renderiza sobre la geometría desplazada (escala
    automática si `scale=None`).
    """
    if not HAS_PIL:
        return None
    if not nodal_stresses or not project.nodes or not project.elements:
        return None

    node_values = {nid: float(nodal_stresses.get(nid, {}).get(component, 0.0))
                   for nid in project.nodes}
    if not node_values:
        return None
    vmin = min(node_values.values())
    vmax = max(node_values.values())
    if vmax - vmin < 1e-15:
        vmax = vmin + 1.0

    deform_scale = 0.0
    if deformed and solution is not None:
        u = solution.get("u")
        if u is not None:
            xs = np.array([n.x for n in project.nodes.values()])
            ys = np.array([n.y for n in project.nodes.values()])
            extent = max(xs.max() - xs.min(), ys.max() - ys.min(), 1e-9)
            u_arr = np.asarray(u)
            max_disp = max(np.abs(u_arr).max(), 1e-12)
            deform_scale = scale if scale is not None else 0.10 * extent / max_disp
            project.displacements = u_arr

    img_arr, view = _render_field_to_array(
        project, node_values, vmin, vmax, width, height,
        deformed=deformed, deform_scale=deform_scale, subdiv=10,
    )
    img = Image.fromarray(img_arr, "RGBA")
    draw = ImageDraw.Draw(img)
    _draw_wireframe(draw, project, view, color=_PAPER_DARK, width=1,
                    deformed=deformed, deform_scale=deform_scale)
    font_small = _load_font(11)
    font_title = _load_font(14)
    _draw_axes_indicator(draw, width, height, font=font_small)
    label = _COMPONENT_LABELS.get(component, component)
    _draw_colorbar(draw, x=width - 90, y=44, w=18, h=min(280, height - 110),
                   vmin=vmin, vmax=vmax, label=label, font=font_small)
    title = f"Contorno de {label}"
    if deformed:
        title += "  (sobre malla deformada)"
    draw.text((20, 12), title, fill=_PAPER_DARK, font=font_title)
    return img


# ───────────────────────────────────────────────────────────────────────────
# Render: Deformada
# ───────────────────────────────────────────────────────────────────────────

def render_deformed(project, solution, *, scale: Optional[float] = None,
                    width: int = 900, height: int = 660) -> Optional["Image.Image"]:
    """Superpone malla original (gris discontinuo) + deformada (verde post)."""
    if not HAS_PIL or not project.elements or solution is None:
        return None

    u = np.asarray(solution["u"])
    idx_map = project.node_index_map
    xs0 = np.array([n.x for n in project.nodes.values()])
    ys0 = np.array([n.y for n in project.nodes.values()])
    extent = max(xs0.max() - xs0.min(), ys0.max() - ys0.min(), 1e-9)
    max_disp = max(np.abs(u).max(), 1e-12)
    if scale is None:
        scale = 0.10 * extent / max_disp

    # Bounding box que incluye original + deformada para encuadre
    nid_list = list(project.nodes.keys())
    xs_def = [project.nodes[nid].x + scale * u[2 * idx_map[nid]]
              for nid in nid_list]
    ys_def = [project.nodes[nid].y + scale * u[2 * idx_map[nid] + 1]
              for nid in nid_list]
    xs_all = list(xs0) + xs_def
    ys_all = list(ys0) + ys_def
    view = _ViewTransform(xs_all, ys_all, width, height, padding=44)

    img = Image.new("RGBA", (width, height), _BG_WHITE)
    draw = ImageDraw.Draw(img)

    # Malla original: gris claro, línea discontinua (simulada con segmentos)
    for elem in project.elements.values():
        coords = []
        valid = True
        for nid in elem.node_ids[:4]:
            node = project.nodes.get(nid)
            if node is None:
                valid = False
                break
            coords.append(view.w2s(node.x, node.y))
        if not valid:
            continue
        for k in range(4):
            p0 = coords[k]
            p1 = coords[(k + 1) % 4]
            _dashed_line(draw, p0, p1, fill=(170, 170, 170), width=1,
                         dash_len=5, gap_len=4)

    # Deformada: verde post-proceso, línea continua gruesa
    post_rgb = _hex_to_rgb(PHASE_POST_COLOR)
    for elem in project.elements.values():
        coords = []
        valid = True
        for nid in elem.node_ids[:4]:
            node = project.nodes.get(nid)
            if node is None:
                valid = False
                break
            base = 2 * idx_map[nid]
            x = node.x + scale * u[base]
            y = node.y + scale * u[base + 1]
            coords.append(view.w2s(x, y))
        if not valid:
            continue
        for k in range(4):
            draw.line([coords[k], coords[(k + 1) % 4]],
                      fill=post_rgb, width=2)

    # Nodos deformados (puntos pequeños azules)
    node_rgb = _hex_to_rgb(CANVAS_NODE_COLOR)
    for nid in nid_list:
        base = 2 * idx_map[nid]
        x = project.nodes[nid].x + scale * u[base]
        y = project.nodes[nid].y + scale * u[base + 1]
        sx, sy = view.w2s(x, y)
        draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3],
                     fill=node_rgb, outline=_PAPER_DARK)

    font_small = _load_font(11)
    font_title = _load_font(14)
    _draw_axes_indicator(draw, width, height, font=font_small)
    title = f"Configuración deformada (escala × {scale:.3g})"
    draw.text((20, 12), title, fill=_PAPER_DARK, font=font_title)
    # Mini-leyenda: arriba a la derecha (no choca con axes indicator
    # que vive en la esquina inferior izquierda).
    x_leg = width - 220
    y_leg = 18
    draw.line([(x_leg, y_leg), (x_leg + 24, y_leg)],
              fill=(170, 170, 170), width=1)
    draw.text((x_leg + 28, y_leg - 7), "Original",
              fill=_PAPER_DARK, font=font_small)
    draw.line([(x_leg + 100, y_leg), (x_leg + 124, y_leg)],
              fill=post_rgb, width=2)
    draw.text((x_leg + 128, y_leg - 7), "Deformada",
              fill=_PAPER_DARK, font=font_small)
    return img


def _dashed_line(draw: "ImageDraw.ImageDraw", p0, p1, *,
                 fill, width: int, dash_len: int, gap_len: int) -> None:
    x0, y0 = p0
    x1, y1 = p1
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    ux = dx / length
    uy = dy / length
    pos = 0.0
    on = True
    while pos < length:
        seg = dash_len if on else gap_len
        end = min(pos + seg, length)
        if on:
            draw.line([(x0 + ux * pos, y0 + uy * pos),
                       (x0 + ux * end, y0 + uy * end)],
                      fill=fill, width=width)
        pos = end
        on = not on


# ───────────────────────────────────────────────────────────────────────────
# Render: Diagrama del modelo (geometría + BCs + cargas)
# ───────────────────────────────────────────────────────────────────────────

def render_mesh_diagram(project, *, width: int = 900,
                        height: int = 660) -> Optional["Image.Image"]:
    """Discretización del modelo: elementos, nodos numerados, BCs, cargas.

    Replica los símbolos del MeshCanvas (empotramiento / rodillo Y / rodillo X)
    sobre fondo blanco para el PDF.
    """
    if not HAS_PIL or not project.nodes:
        return None

    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    view = _ViewTransform(xs, ys, width, height, padding=58)
    bbox_extent = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
    sym_scale_world = 0.04 * bbox_extent

    img = Image.new("RGBA", (width, height), _BG_WHITE)
    draw = ImageDraw.Draw(img)
    font_small = _load_font(11)
    font_node = _load_font(10)
    font_elem = _load_font(13)
    font_title = _load_font(14)

    # 1) Polígonos de elementos (relleno azul suave + borde azul oscuro)
    fill_face = (218, 232, 248, 255)
    edge_color = (58, 105, 175)
    label_color = (26, 58, 107)
    for elem in project.elements.values():
        coords = []
        for nid in elem.node_ids[:4]:
            node = project.nodes.get(nid)
            if node is None:
                coords = []
                break
            coords.append(view.w2s(node.x, node.y))
        if len(coords) < 3:
            continue
        draw.polygon(coords, fill=fill_face, outline=edge_color)
        cx = sum(p[0] for p in coords) / len(coords)
        cy = sum(p[1] for p in coords) / len(coords)
        s = f"E{elem.id}"
        draw.text((cx - 8, cy - 7), s, fill=label_color, font=font_elem)

    # 2) Nodos por rol (corner / mid / center)
    is_q9 = getattr(project, "element_type", None) == ELEMENT_Q9
    corner_nids: set[int] = set()
    mid_nids: set[int] = set()
    center_nids: set[int] = set()
    if is_q9:
        for elem in project.elements.values():
            ids = list(elem.node_ids)
            if len(ids) >= 4:
                corner_nids.update(ids[:4])
            if len(ids) >= 8:
                mid_nids.update(ids[4:8])
            if len(ids) >= 9:
                center_nids.add(ids[8])
        mid_nids -= corner_nids
        center_nids -= (corner_nids | mid_nids)
    else:
        corner_nids = set(project.nodes.keys())

    def _draw_nodes(nids, hex_color, radius):
        rgb = _hex_to_rgb(hex_color)
        for nid in nids:
            node = project.nodes.get(nid)
            if node is None:
                continue
            sx, sy = view.w2s(node.x, node.y)
            draw.ellipse([sx - radius, sy - radius, sx + radius, sy + radius],
                         fill=rgb, outline=_PAPER_DARK)

    _draw_nodes(corner_nids, CANVAS_NODE_COLOR, 5)
    _draw_nodes(mid_nids, CANVAS_NODE_MID_COLOR, 3)
    _draw_nodes(center_nids, CANVAS_NODE_CENTER_COLOR, 3)

    for nid, node in project.nodes.items():
        sx, sy = view.w2s(node.x, node.y)
        draw.text((sx + 6, sy + 5), str(nid), fill=label_color, font=font_node)

    # 3) Símbolos de restricción
    bc_rgb = _hex_to_rgb(CANVAS_CONSTRAINT_COLOR)
    bc_fill_fixed = (252, 233, 212)
    bc_fill_roller = (220, 234, 242)
    for nid, bc in project.boundary_conditions.items():
        node = project.nodes.get(nid)
        if node is None:
            continue
        if not (bc.restrain_x or bc.restrain_y):
            continue
        sx, sy = view.w2s(node.x, node.y)
        kind = "fixed" if (bc.restrain_x and bc.restrain_y) \
               else ("roller_y" if bc.restrain_y else "roller_x")
        _draw_bc_symbol_pil(draw, sx, sy, kind,
                             scale_px=view.scale * sym_scale_world,
                             color=bc_rgb, fill_fixed=bc_fill_fixed,
                             fill_roller=bc_fill_roller)

    # 4) Cargas nodales (flechas rojas hacia el nodo)
    if project.nodal_loads:
        load_rgb = _hex_to_rgb(CANVAS_LOAD_COLOR)
        rng_x = (max(xs) - min(xs)) if len(xs) > 1 else 1.0
        rng_y = (max(ys) - min(ys)) if len(ys) > 1 else 1.0
        ref_world = 0.12 * max(rng_x, rng_y, 1e-6)
        max_mag = max(
            math.hypot(ld.fx, ld.fy) for ld in project.nodal_loads.values()
        ) or 1.0
        for nid, ld in project.nodal_loads.items():
            node = project.nodes.get(nid)
            if node is None:
                continue
            mag = math.hypot(ld.fx, ld.fy)
            if mag < 1e-12:
                continue
            ux = ld.fx / mag
            uy = ld.fy / mag
            length_w = ref_world * (mag / max_mag)
            x_tail = node.x - ux * length_w
            y_tail = node.y - uy * length_w
            sx_tail, sy_tail = view.w2s(x_tail, y_tail)
            sx_head, sy_head = view.w2s(node.x, node.y)
            draw.line([(sx_tail, sy_tail), (sx_head, sy_head)],
                      fill=load_rgb, width=2)
            _arrow_head(draw, sx_tail, sy_tail, sx_head, sy_head,
                        size=8, color=load_rgb)

    # 5) Cargas superficiales (trapezoide indicativo)
    if getattr(project, "surface_loads", None):
        surf_rgb = (220, 60, 60)
        for sl in project.surface_loads:
            n_a = project.nodes.get(sl.node_start)
            n_b = project.nodes.get(sl.node_end)
            if n_a is None or n_b is None:
                continue
            sax, say = view.w2s(n_a.x, n_a.y)
            sbx, sby = view.w2s(n_b.x, n_b.y)
            draw.line([(sax, say), (sbx, sby)], fill=surf_rgb, width=3)

    _draw_axes_indicator(draw, width, height, font=font_small)
    draw.text((20, 12), "Discretización del modelo",
              fill=_PAPER_DARK, font=font_title)
    return img


def _arrow_head(draw, x0, y0, x1, y1, *, size: int, color) -> None:
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return
    ux = dx / length
    uy = dy / length
    perp_x = -uy
    perp_y = ux
    bx = x1 - size * ux + (size * 0.4) * perp_x
    by = y1 - size * uy + (size * 0.4) * perp_y
    cx = x1 - size * ux - (size * 0.4) * perp_x
    cy = y1 - size * uy - (size * 0.4) * perp_y
    draw.polygon([(x1, y1), (bx, by), (cx, cy)], fill=color)


def _draw_bc_symbol_pil(draw: "ImageDraw.ImageDraw", x: float, y: float,
                       kind: str, *, scale_px: float, color, fill_fixed,
                       fill_roller) -> None:
    """Símbolo de restricción estilo MeshCanvas, en píxeles.

    `x, y` son coords pantalla del nodo; `scale_px` es el tamaño caracteristico
    en píxeles.
    """
    s = max(scale_px, 8.0)
    if kind == "fixed":
        tri = [(x, y), (x - s, y + 1.6 * s), (x + s, y + 1.6 * s)]
        draw.polygon(tri, fill=fill_fixed, outline=color)
        # Base
        draw.line([(x - 1.4 * s, y + 1.6 * s), (x + 1.4 * s, y + 1.6 * s)],
                  fill=color, width=2)
        # Hachuras
        for i in range(3):
            xx = x - s + i * s
            draw.line([(xx, y + 1.6 * s),
                       (xx - 0.5 * s, y + 2.1 * s)],
                      fill=color, width=1)
    elif kind == "roller_y":
        tri = [(x, y), (x - s, y + s), (x + s, y + s)]
        draw.polygon(tri, fill=fill_roller, outline=color)
        roller_cy = y + s + 0.4 * s
        r = 0.32 * s
        draw.ellipse([(x - r, roller_cy - r), (x + r, roller_cy + r)],
                     fill=fill_roller, outline=color)
        surf_y = roller_cy + 0.55 * s
        draw.line([(x - 1.4 * s, surf_y), (x + 1.4 * s, surf_y)],
                  fill=color, width=2)
        for i in range(3):
            xx = x - s + i * s
            draw.line([(xx, surf_y), (xx - 0.5 * s, surf_y + 0.5 * s)],
                      fill=color, width=1)
    elif kind == "roller_x":
        tri = [(x, y), (x - s, y - s), (x - s, y + s)]
        draw.polygon(tri, fill=fill_roller, outline=color)
        roller_cx = x - s - 0.4 * s
        r = 0.32 * s
        draw.ellipse([(roller_cx - r, y - r), (roller_cx + r, y + r)],
                     fill=fill_roller, outline=color)
        wall_x = roller_cx - 0.55 * s
        draw.line([(wall_x, y - 1.4 * s), (wall_x, y + 1.4 * s)],
                  fill=color, width=2)
        for i in range(3):
            yy = y - s + i * s
            draw.line([(wall_x, yy), (wall_x - 0.5 * s, yy + 0.5 * s)],
                      fill=color, width=1)


# ───────────────────────────────────────────────────────────────────────────
# Render: Cruces principales σ₁ / σ₂
# ───────────────────────────────────────────────────────────────────────────

def render_principal_crosses(project, nodal_stresses, *,
                              width: int = 900, height: int = 660
                              ) -> Optional["Image.Image"]:
    """Cruces σ₁/σ₂ en el centroide de cada elemento.

    Azul = tracción, rojo = compresión (igual MeshCanvas Post + capa de
    cruces). El brazo σ₁ va en la dirección θ_p y el σ₂ perpendicular,
    con longitudes proporcionales a |σᵢ|/máx.
    """
    if not HAS_PIL or not project.elements or not nodal_stresses:
        return None

    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    view = _ViewTransform(xs, ys, width, height, padding=46)
    img = Image.new("RGBA", (width, height), _BG_WHITE)
    draw = ImageDraw.Draw(img)
    font_small = _load_font(11)
    font_title = _load_font(14)

    # Malla en gris claro
    for elem in project.elements.values():
        coords = []
        ok = True
        for nid in elem.node_ids[:4]:
            node = project.nodes.get(nid)
            if node is None:
                ok = False
                break
            coords.append(view.w2s(node.x, node.y))
        if not ok:
            continue
        for k in range(4):
            draw.line([coords[k], coords[(k + 1) % 4]],
                      fill=(180, 180, 180), width=1)

    # Centroide y cruces por elemento
    centroids = []
    crosses = []
    max_mag = 1e-12
    for elem in project.elements.values():
        nids = [nid for nid in elem.node_ids[:4] if nid in project.nodes]
        if len(nids) < 3:
            continue
        sx_vals, sy_vals, txy_vals = [], [], []
        for nid in nids:
            s = nodal_stresses.get(nid, {})
            sx_vals.append(s.get("sigma_x", 0.0))
            sy_vals.append(s.get("sigma_y", 0.0))
            txy_vals.append(s.get("tau_xy", 0.0))
        sx_w = float(np.mean(sx_vals))
        sy_w = float(np.mean(sy_vals))
        txy_w = float(np.mean(txy_vals))
        cx = float(np.mean([project.nodes[n].x for n in nids]))
        cy = float(np.mean([project.nodes[n].y for n in nids]))
        avg = 0.5 * (sx_w + sy_w)
        R = float(np.sqrt(((sx_w - sy_w) / 2.0) ** 2 + txy_w ** 2))
        sigma_1 = avg + R
        sigma_2 = avg - R
        theta_p = 0.5 * np.arctan2(2.0 * txy_w, (sx_w - sy_w) + 1e-30)
        centroids.append((cx, cy))
        crosses.append((sigma_1, sigma_2, theta_p))
        max_mag = max(max_mag, abs(sigma_1), abs(sigma_2))

    extent = max(max(xs) - min(xs), max(ys) - min(ys), 1e-9)
    L_max = 0.16 * extent

    tens_rgb = _hex_to_rgb(PRINCIPAL_TENSION_COLOR)
    comp_rgb = _hex_to_rgb(PRINCIPAL_COMPRESSION_COLOR)

    for (cx, cy), (s1, s2, th) in zip(centroids, crosses):
        # σ₁
        L1 = L_max * (abs(s1) / max_mag)
        dx1 = L1 * math.cos(th)
        dy1 = L1 * math.sin(th)
        col1 = tens_rgb if s1 >= 0 else comp_rgb
        p0 = view.w2s(cx - dx1, cy - dy1)
        p1 = view.w2s(cx + dx1, cy + dy1)
        draw.line([p0, p1], fill=col1, width=2)
        # σ₂ perpendicular
        L2 = L_max * (abs(s2) / max_mag)
        dx2 = L2 * math.cos(th + math.pi / 2)
        dy2 = L2 * math.sin(th + math.pi / 2)
        col2 = tens_rgb if s2 >= 0 else comp_rgb
        p0 = view.w2s(cx - dx2, cy - dy2)
        p1 = view.w2s(cx + dx2, cy + dy2)
        draw.line([p0, p1], fill=col2, width=2)

    _draw_axes_indicator(draw, width, height, font=font_small)
    draw.text((20, 12),
              "Cruces principales por elemento  (σ₁ ⊥ σ₂)",
              fill=_PAPER_DARK, font=font_title)
    # Mini-leyenda: arriba a la derecha para no chocar con axes indicator.
    x_leg = width - 280
    y_leg = 18
    draw.line([(x_leg, y_leg), (x_leg + 24, y_leg)],
              fill=tens_rgb, width=3)
    draw.text((x_leg + 28, y_leg - 7), "σ > 0  tracción",
              fill=_PAPER_DARK, font=font_small)
    draw.line([(x_leg + 130, y_leg), (x_leg + 154, y_leg)],
              fill=comp_rgb, width=3)
    draw.text((x_leg + 158, y_leg - 7), "σ < 0  compresión",
              fill=_PAPER_DARK, font=font_small)
    return img


# ═══════════════════════════════════════════════════════════════════════════
# RENDERS ESQUEMÁTICOS — matplotlib
# ═══════════════════════════════════════════════════════════════════════════
#
# Las funciones siguientes generan figuras esquemáticas (sin coordenadas del
# modelo): Mohr circle, heatmap de K, pipeline MEF. Se mantienen en matplotlib
# porque su contenido es abstracto y la coherencia visual con el canvas no
# aplica.
#

_FIG_FACECOLOR_MPL = "white"


def render_mohr_circle(sigma_x: float, sigma_y: float, tau_xy: float,
                       label: str = "") -> Figure:
    """Círculo de Mohr para un punto material.

    Misma identidad cromática que el inset del DetailsPanel del Post:
    σ₁ azul, σ₂ rojo, círculo azul claro.
    """
    fig = Figure(figsize=(6.0, 5.0), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR_MPL)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="datalim")

    cx = 0.5 * (sigma_x + sigma_y)
    R = float(np.sqrt(((sigma_x - sigma_y) / 2.0) ** 2 + tau_xy ** 2))
    sigma_1 = cx + R
    sigma_2 = cx - R

    theta = np.linspace(0, 2 * np.pi, 240)
    ax.plot(cx + R * np.cos(theta), R * np.sin(theta),
            color=PHASE_PRE_COLOR, linewidth=1.6)
    ax.scatter([sigma_x], [-tau_xy], s=48,
               color=PRINCIPAL_COMPRESSION_COLOR, zorder=5,
               label=r"$X=(\sigma_x,-\tau_{xy})$")
    ax.scatter([sigma_y], [tau_xy], s=48,
               color=PHASE_POST_COLOR, zorder=5,
               label=r"$Y=(\sigma_y,+\tau_{xy})$")
    ax.plot([sigma_x, sigma_y], [-tau_xy, tau_xy],
            color="#888", linestyle="--", linewidth=1.0)
    ax.scatter([sigma_1], [0], s=64, color=PRINCIPAL_TENSION_COLOR,
               zorder=5, label=r"$\sigma_1$")
    ax.scatter([sigma_2], [0], s=64, color=PRINCIPAL_COMPRESSION_COLOR,
               zorder=5, label=r"$\sigma_2$")
    ax.axvline(cx, color="#cccccc", linewidth=0.8, linestyle=":")
    ax.axhline(0, color="#888888", linewidth=0.8)
    ax.set_xlabel(r"$\sigma$")
    ax.set_ylabel(r"$\tau$")
    title = "Círculo de Mohr"
    if label:
        title += f"  ({label})"
    ax.set_title(title, fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    return fig


def render_K_heatmap(K: np.ndarray, *, log_scale: bool = True,
                     title: str = r"Matriz de rigidez global $\mathbf{K}$"
                     ) -> Figure:
    """Heatmap log|K| para inspeccionar densidad/banda cuando K es grande."""
    fig = Figure(figsize=(6.0, 5.0), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR_MPL)
    ax = fig.add_subplot(111)
    M = np.asarray(K)
    if log_scale:
        eps = max(1e-30, float(np.abs(M).max()) * 1e-12)
        data = np.log10(np.abs(M) + eps)
        cmap = "viridis"
        cbar_label = r"$\log_{10}|K_{ij}|$"
    else:
        data = M
        cmap = "coolwarm"
        cbar_label = r"$K_{ij}$"
    im = ax.imshow(data, cmap=cmap, aspect="equal", interpolation="nearest")
    cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.03)
    cbar.set_label(cbar_label)
    ax.set_xlabel("Columna (GDL)")
    ax.set_ylabel("Fila (GDL)")
    ax.set_title(title, fontsize=11)
    fig.tight_layout()
    return fig


def render_fem_pipeline() -> Figure:
    """Pipeline MEF en 7 etapas, coloreado por fase del proyecto.

    Vista panorámica del método antes de entrar en los capítulos.
    """
    fig = Figure(figsize=(9.5, 2.4), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR_MPL)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 3)
    ax.set_aspect("equal")
    ax.axis("off")

    steps = [
        ("Modelo\n(nodos, mat,\ncargas, BCs)", PHASE_PRE_COLOR),
        ("Calidad\ngeometrica\nde la malla", PHASE_PRE_COLOR),
        ("Elemento\nN, J, B, D", PHASE_PROC_COLOR),
        ("k_e por\ncuadratura\nde Gauss", PHASE_PROC_COLOR),
        ("Ensamblaje\nK, F", PHASE_PROC_COLOR),
        ("Aplicar\nBCs + resolver\nK_red u = F_red", PHASE_PROC_COLOR),
        ("Post-proceso\nsigma, sigma_VM\ndeformada", PHASE_POST_COLOR),
    ]
    n = len(steps)
    box_w = 1.7
    box_h = 1.4
    total_w = n * box_w
    gap = (14 - total_w) / (n + 1)
    for i, (text, color) in enumerate(steps):
        x0 = gap + i * (box_w + gap)
        y0 = 0.85
        rect = _FancyBboxPatch(
            (x0, y0), box_w, box_h,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            facecolor=color, edgecolor="black",
            linewidth=0.8, alpha=0.88,
        )
        ax.add_patch(rect)
        ax.text(x0 + box_w / 2, y0 + box_h / 2, text,
                ha="center", va="center", fontsize=7.2,
                color="white", fontweight="bold")
        if i < n - 1:
            arrow = _FancyArrowPatch(
                (x0 + box_w, y0 + box_h / 2),
                (x0 + box_w + gap, y0 + box_h / 2),
                arrowstyle="->", color="black", lw=1.2,
                mutation_scale=12,
            )
            ax.add_patch(arrow)

    def _phase_center(i_start: int, i_end: int) -> float:
        x_start = gap + i_start * (box_w + gap)
        x_end = gap + i_end * (box_w + gap) + box_w
        return (x_start + x_end) / 2.0

    ax.text(_phase_center(0, 1), 0.38, "PRE-PROCESO",
            ha="center", fontsize=8, color=PHASE_PRE_COLOR,
            fontweight="bold")
    ax.text(_phase_center(2, 5), 0.38, "PROCESO",
            ha="center", fontsize=8, color=PHASE_PROC_COLOR,
            fontweight="bold")
    ax.text(_phase_center(6, 6), 0.38, "POST",
            ha="center", fontsize=8, color=PHASE_POST_COLOR,
            fontweight="bold")
    return fig
