"""
Render de figuras de campo para la Memoria de Cálculo — Pillow puro.

Reformulado (2026-05): se eliminó la dependencia de matplotlib. Las figuras
de campo (contornos de tensión, deformada, diagrama del modelo) se dibujan
con Pillow replicando el ESTILO del MeshCanvas del
Post-Proceso — gradiente bilineal Gouraud por elemento + wireframe + colorbar
lateral — pero con FONDO BLANCO (el PDF se imprime en papel).

Razón del cambio: las gráficas matplotlib se veían pobres frente al canvas
interactivo (tkinter + Pillow) del software. Reusar la misma técnica de
rasterizado del canvas hace que el alumno reconozca en la Memoria los mismos
colores y la misma "lectura" del campo que ve en pantalla.

Paleta:
  - Acentos (nodos por rol Q9, restricciones, cargas) → paleta semántica de
    `config.settings` (mismos códigos visuales que el canvas de la GUI).
  - Mapas de campo: `jet` (arcoiris clasico ANSYS/SAP2000) para TODOS los
    componentes (σx, σy, τxy, σVM) — pedido del usuario "cambia todo a JET".
    Implementado como LUT interna; look reconocible de ingenieria estructural
    (ver CLAUDE.md). `coolwarm` queda sin uso en los resultados.

Funciones expuestas (todas retornan `PIL.Image.Image` o None si Pillow no
está disponible / el modelo no tiene datos suficientes):
  - render_mesh_diagram(project)
  - render_contour(project, solution, nodal_stresses, component, *, deformed)
  - render_deformed(project, solution, scale=None)
  - render_K_sparsity(K)  — patrón de no-nulos de K (reemplaza al heatmap).
"""

from __future__ import annotations

import numpy as np

try:
    from PIL import Image, ImageDraw, ImageFont  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

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
)


_FIG_BG = (255, 255, 255)          # fondo blanco (PDF impreso)
_WIREFRAME = (90, 90, 96)          # gris oscuro para aristas sobre blanco
_AXIS_TEXT = (40, 40, 50)          # texto de títulos / labels
_ELEMENT_FACE = (221, 233, 247)    # relleno suave de elementos (mesh diagram)
_ELEMENT_EDGE = (58, 111, 181)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Convierte '#rrggbb' a (r, g, b). Tolera formato corto '#rgb'."""
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# Acentos semánticos como RGB (importados de config como hex).
_RGB_NODE_CORNER = _hex_to_rgb(CANVAS_NODE_COLOR)
_RGB_NODE_MID = _hex_to_rgb(CANVAS_NODE_MID_COLOR)
_RGB_NODE_CENTER = _hex_to_rgb(CANVAS_NODE_CENTER_COLOR)
_RGB_CONSTRAINT = _hex_to_rgb(CANVAS_CONSTRAINT_COLOR)
_RGB_LOAD = _hex_to_rgb(CANVAS_LOAD_COLOR)
_RGB_DEFORMED = _hex_to_rgb(PHASE_POST_COLOR)


# ---------------------------------------------------------------------------
# Colormaps científicos (LUT pura, sin matplotlib)
# ---------------------------------------------------------------------------
# Anchors muestreados de los colormaps de matplotlib. Se interpolan
# linealmente a una LUT de 256 entradas al primer uso (cache de módulo).

_VIRIDIS_ANCHORS = np.array([
    (68, 1, 84), (72, 40, 120), (62, 74, 137), (49, 104, 142),
    (38, 130, 142), (31, 158, 137), (53, 183, 121), (110, 206, 88),
    (181, 222, 43), (253, 231, 37),
], dtype=float)

_COOLWARM_ANCHORS = np.array([
    (59, 76, 192), (98, 130, 234), (141, 176, 254), (184, 208, 249),
    (221, 221, 221), (245, 196, 173), (244, 154, 123), (222, 96, 77),
    (180, 4, 38),
], dtype=float)

# Jet (arcoiris clasico de los software FEM — ANSYS / SAP2000). Reemplaza a
# viridis/turbo para los campos no negativos (von Mises) — unifica la Memoria
# con el canvas/Vista 3D/M9, que usan el mismo jet (config/colormaps). Pedido
# del usuario (2026-05-31). Definicion clasica de matplotlib jet.
_JET_ANCHORS = np.array([
    (0, 0, 128), (0, 0, 224), (0, 42, 255), (0, 128, 255),
    (0, 212, 255), (55, 255, 192), (123, 255, 123), (192, 255, 55),
    (255, 230, 0), (255, 151, 0), (255, 72, 0), (224, 0, 0),
    (128, 0, 0),
], dtype=float)

_LUT_CACHE: dict[str, np.ndarray] = {}


def _colormap_lut(name: str) -> np.ndarray:
    """Devuelve una LUT (256, 3) uint8 del colormap pedido."""
    cached = _LUT_CACHE.get(name)
    if cached is not None:
        return cached
    if name == "coolwarm":
        anchors = _COOLWARM_ANCHORS
    elif name == "jet":
        anchors = _JET_ANCHORS
    else:
        anchors = _VIRIDIS_ANCHORS
    n_a = anchors.shape[0]
    t_anchors = np.linspace(0.0, 1.0, n_a)
    t_lut = np.linspace(0.0, 1.0, 256)
    lut = np.empty((256, 3), dtype=np.uint8)
    for c in range(3):
        lut[:, c] = np.clip(
            np.interp(t_lut, t_anchors, anchors[:, c]), 0, 255
        ).astype(np.uint8)
    _LUT_CACHE[name] = lut
    return lut


def _cmap_for(component: str) -> str:
    """jet (arcoiris clasico ANSYS/SAP) para TODOS los componentes — pedido del
    usuario "cambia todo a JET" (2026-05-31). Unificado con el canvas/Vista 3D/M9."""
    return "jet"


# ---------------------------------------------------------------------------
# Transform world -> screen (idéntico criterio que MeshCanvas / ResultImageRenderer)
# ---------------------------------------------------------------------------

class _View:
    """Encapsula el mapeo mundo→pantalla con fit + centrado y margen."""

    def __init__(self, xs, ys, width, height, *, pad_left, pad_right,
                 pad_top, pad_bottom):
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        span_x = max(x_max - x_min, 1e-9)
        span_y = max(y_max - y_min, 1e-9)
        avail_w = max(width - pad_left - pad_right, 1)
        avail_h = max(height - pad_top - pad_bottom, 1)
        self.scale = min(avail_w / span_x, avail_h / span_y)
        used_w = span_x * self.scale
        used_h = span_y * self.scale
        self.offset_x = pad_left + (avail_w - used_w) / 2 - x_min * self.scale
        self.offset_y = pad_top + (avail_h - used_h) / 2 + y_max * self.scale

    def w2s(self, x, y):
        return x * self.scale + self.offset_x, -y * self.scale + self.offset_y


def _font(size: int):
    """Carga una fuente TrueType legible; cae al bitmap default si falta."""
    if not HAS_PIL:
        return None
    for name in ("DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _tint(rgb: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """Mezcla `rgb` con blanco: t=0 → rgb, t=1 → blanco. Para rellenos suaves."""
    return tuple(int(round(c + (255 - c) * t)) for c in rgb)


# ---------------------------------------------------------------------------
# Mapa del cálculo — infografía del pipeline MEF (one-pager del educativo)
# ---------------------------------------------------------------------------

def render_pipeline_map(project):
    """Infografía horizontal del recorrido MEF: 5 estaciones conectadas por
    flechas con el dato que viaja entre etapas. Estilo canvas, fondo blanco;
    coloreada por fase (pre azul · proc naranja · post verde, paleta de
    config). Reemplaza la intro narrativa del estilo educativo.

    Devuelve PIL.Image o None si Pillow no está disponible.
    """
    if not HAS_PIL:
        return None
    try:
        n_nodes = project.num_nodes
        n_elem = project.num_elements
        is_q9 = project.element_type == ELEMENT_Q9
        n_dof = getattr(project, "total_dof", 2 * n_nodes)
    except Exception:
        n_nodes = n_elem = n_dof = 0
        is_q9 = False

    pre = _hex_to_rgb(PHASE_PRE_COLOR)
    proc = _hex_to_rgb(PHASE_PROC_COLOR)
    post = _hex_to_rgb(PHASE_POST_COLOR)
    elem_lbl = "Q9 · 3×3 Gauss" if is_q9 else "Q4 · 2×2 Gauss"

    # (color, título, líneas de cuerpo)
    stages = [
        (pre, "PRE-PROCESO",
         ["Geometría, material,", "cargas y apoyos",
          f"{n_nodes} nodos · {n_elem} elem"]),
        (proc, "FORMULACIÓN",
         ["N → J → B → D", "por elemento", elem_lbl]),
        (proc, "ENSAMBLAJE",
         ["Σ ke → K", "Σ fe → F", f"{n_dof} GDL"]),
        (proc, "BCs + SOLUCIÓN",
         ["Kff·uf = Ff", "factorización LU", "→ u, R"]),
        (post, "POST-PROCESO",
         ["σ = D·B·u", "σ1, σ2, σVM", "contornos"]),
    ]
    arrow_lbls = ["malla", "ke", "K, F", "u"]

    n = len(stages)
    box_w, box_h = 168, 132
    gap = 32                      # espacio para la flecha entre cajas
    pad_x = 24
    top = 54                      # deja lugar a un título arriba
    W = pad_x * 2 + n * box_w + (n - 1) * gap
    H = top + box_h + 40

    img = Image.new("RGB", (W, H), _FIG_BG)
    d = ImageDraw.Draw(img)

    f_title = _font(20)
    f_box_title = _font(15)
    f_body = _font(13)
    f_arrow = _font(12)

    # Título general.
    d.text((pad_x, 16), "Mapa del cálculo — recorrido del MEF",
           fill=_AXIS_TEXT, font=f_title)

    def _centered(cx, y, text, font, fill):
        try:
            l, t0, r, b = d.textbbox((0, 0), text, font=font)
            d.text((cx - (r - l) / 2, y), text, fill=fill, font=font)
        except Exception:
            d.text((cx, y), text, fill=fill, font=font)

    for i, (color, title, body) in enumerate(stages):
        x0 = pad_x + i * (box_w + gap)
        x1 = x0 + box_w
        y0, y1 = top, top + box_h
        fill = _tint(color, 0.86)
        try:
            d.rounded_rectangle([x0, y0, x1, y1], radius=9, fill=fill,
                                outline=color, width=2)
        except Exception:
            d.rectangle([x0, y0, x1, y1], fill=fill, outline=color, width=2)
        # Banda de título.
        try:
            d.rounded_rectangle([x0, y0, x1, y0 + 26], radius=9, fill=color)
            d.rectangle([x0, y0 + 14, x1, y0 + 26], fill=color)
        except Exception:
            d.rectangle([x0, y0, x1, y0 + 26], fill=color)
        cx = (x0 + x1) / 2
        _centered(cx, y0 + 5, title, f_box_title, (255, 255, 255))
        for j, line in enumerate(body):
            _centered(cx, y0 + 38 + j * 24, line, f_body, _AXIS_TEXT)

        # Flecha a la siguiente caja + etiqueta del dato.
        if i < n - 1:
            ax0 = x1 + 4
            ax1 = x1 + gap - 4
            ay = (y0 + y1) / 2
            d.line([ax0, ay, ax1 - 6, ay], fill=_AXIS_TEXT, width=2)
            d.polygon([(ax1, ay), (ax1 - 8, ay - 5), (ax1 - 8, ay + 5)],
                      fill=_AXIS_TEXT)
            _centered((ax0 + ax1) / 2, ay - 22, arrow_lbls[i], f_arrow,
                      _hex_to_rgb(PHASE_PROC_COLOR))

    return img


# ---------------------------------------------------------------------------
# Rasterizado de campo (Gouraud bilineal por triángulo) — estilo MeshCanvas
# ---------------------------------------------------------------------------

def _rasterize_triangle(img_arr, w, h, p0, p1, p2, vmin, v_range, lut):
    """Rasteriza un triángulo con interpolación baricéntrica + LUT colormap.

    Cada p es (sx, sy, valor). Misma lógica que MeshCanvas._rasterize_triangle
    pero con lookup en una LUT (viridis/coolwarm) en vez de jet inline.
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
    t = np.clip((vals - vmin) / v_range, 0.0, 1.0)
    idx = (t * 255).astype(np.int32)

    iy = PY[inside].astype(int)
    ix = PX[inside].astype(int)
    valid = (iy >= 0) & (iy < h) & (ix >= 0) & (ix < w)
    iy, ix = iy[valid], ix[valid]
    cols = lut[idx[inside][valid]]
    img_arr[iy, ix, 0] = cols[:, 0]
    img_arr[iy, ix, 1] = cols[:, 1]
    img_arr[iy, ix, 2] = cols[:, 2]
    img_arr[iy, ix, 3] = 255


def _fill_field(img_arr, w, h, project, view, node_values, vmin, vmax, lut,
                *, deformed_coords=None, subdiv=6):
    """Pinta el gradiente de `node_values` sobre cada elemento (corners Q4).

    `deformed_coords`: dict {nid: (x, y)} con coords deformadas, o None para
    usar la geometría original.
    """
    v_range = max(vmax - vmin, 1e-15)
    n = subdiv

    # Matriz de funciones de forma Q4 en la grilla (n+1)^2 x 4, precomputada
    # UNA vez (no depende del elemento). Antes se reevaluaban N0..N3 en un
    # doble loop Python por cada punto de cada elemento; ahora las coords
    # mundo y el valor salen de un producto matriz-vector (broadcasting).
    npts = (n + 1) * (n + 1)
    Nmat = np.empty((npts, 4))
    k = 0
    for i in range(n + 1):
        xi = -1 + 2 * i / n
        for j in range(n + 1):
            eta = -1 + 2 * j / n
            Nmat[k, 0] = (1 - xi) * (1 - eta) * 0.25
            Nmat[k, 1] = (1 + xi) * (1 - eta) * 0.25
            Nmat[k, 2] = (1 + xi) * (1 + eta) * 0.25
            Nmat[k, 3] = (1 - xi) * (1 + eta) * 0.25
            k += 1

    stride = n + 1
    for elem in project.elements.values():
        nids = elem.node_ids[:4]
        if not all(nid in project.nodes for nid in nids):
            continue
        if not all(nid in node_values for nid in nids):
            continue
        nv = np.array([float(node_values[nid]) for nid in nids])
        if deformed_coords is not None:
            nc = np.array([deformed_coords[nid] for nid in nids], dtype=float)
        else:
            nc = np.array(
                [(project.nodes[nid].x, project.nodes[nid].y) for nid in nids],
                dtype=float,
            )

        # world coords y valores por punto via broadcasting.
        world = Nmat @ nc            # (npts, 2)
        vals = Nmat @ nv             # (npts,)
        sx = world[:, 0] * view.scale + view.offset_x
        sy = -world[:, 1] * view.scale + view.offset_y

        for i in range(n):
            for j in range(n):
                k00 = i * stride + j
                k10 = (i + 1) * stride + j
                k11 = (i + 1) * stride + (j + 1)
                k01 = i * stride + (j + 1)
                p00 = (sx[k00], sy[k00], vals[k00])
                p10 = (sx[k10], sy[k10], vals[k10])
                p11 = (sx[k11], sy[k11], vals[k11])
                p01 = (sx[k01], sy[k01], vals[k01])
                _rasterize_triangle(img_arr, w, h, p00, p10, p11,
                                    vmin, v_range, lut)
                _rasterize_triangle(img_arr, w, h, p00, p11, p01,
                                    vmin, v_range, lut)


def _draw_wireframe(draw, project, view, *, deformed_coords=None,
                    color=_WIREFRAME, width=1):
    """Dibuja las aristas macro (4 vértices) de cada elemento."""
    for elem in project.elements.values():
        nids = elem.node_ids[:4]
        if not all(nid in project.nodes for nid in nids):
            continue
        pts = []
        for nid in nids:
            if deformed_coords is not None:
                wx, wy = deformed_coords[nid]
            else:
                wx, wy = project.nodes[nid].x, project.nodes[nid].y
            pts.append(view.w2s(wx, wy))
        pts.append(pts[0])
        draw.line(pts, fill=color, width=width)


def _draw_colorbar(draw, img_h, lut, vmin, vmax, label, *,
                   x0, bar_w=22, bar_top=46, bar_bottom_margin=46):
    """Dibuja una barra de color vertical con etiquetas min/medio/max."""
    bar_h = max(img_h - bar_top - bar_bottom_margin, 10)
    font = _font(13)
    font_lbl = _font(14)
    for i in range(bar_h):
        t = 1.0 - i / max(bar_h - 1, 1)
        r, g, b = lut[int(t * 255)]
        yy = bar_top + i
        draw.line([(x0, yy), (x0 + bar_w, yy)], fill=(int(r), int(g), int(b)))
    draw.rectangle([x0, bar_top, x0 + bar_w, bar_top + bar_h],
                   outline=(120, 120, 120), width=1)
    n_lbl = 5
    for k in range(n_lbl + 1):
        t = 1.0 - k / n_lbl
        val = vmin + t * (vmax - vmin)
        yy = bar_top + int(k / n_lbl * bar_h)
        draw.line([(x0 + bar_w, yy), (x0 + bar_w + 4, yy)],
                  fill=(120, 120, 120))
        draw.text((x0 + bar_w + 7, yy - 7), f"{val:.3g}",
                  fill=_AXIS_TEXT, font=font)
    if label:
        draw.text((x0 - 2, bar_top - 26), label, fill=_AXIS_TEXT, font=font_lbl)


def _title(draw, text, width, *, y=12):
    """Título centrado en la parte superior de la figura."""
    font = _font(17)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = len(text) * 8
    draw.text(((width - tw) / 2, y), text, fill=_AXIS_TEXT, font=font)


def _deformed_scale(project, solution, nid_list):
    """Escala de amplificación automática (~10% del extent / max desplaz.)."""
    u = solution["u"]
    idx_map = project.node_index_map
    xs = np.array([project.nodes[n].x for n in nid_list])
    ys = np.array([project.nodes[n].y for n in nid_list])
    ux = np.array([u[2 * idx_map[n]] for n in nid_list])
    uy = np.array([u[2 * idx_map[n] + 1] for n in nid_list])
    extent = max(xs.max() - xs.min(), ys.max() - ys.min(), 1e-9)
    max_disp = max(np.abs(ux).max(), np.abs(uy).max(), 1e-12)
    return 0.10 * extent / max_disp


# ---------------------------------------------------------------------------
# Diagrama del modelo (resumen visual)
# ---------------------------------------------------------------------------

def render_mesh_diagram(project, *, width=900, height=680):
    """Geometría + nodos numerados + restricciones + cargas, estilo canvas
    sobre fondo blanco. Devuelve PIL.Image o None."""
    if not HAS_PIL or not project.nodes or not project.elements:
        return None
    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    view = _View(xs, ys, width, height,
                 pad_left=40, pad_right=40, pad_top=48, pad_bottom=40)

    img = Image.new("RGB", (width, height), _FIG_BG)
    draw = ImageDraw.Draw(img)
    font_id = _font(13)

    # Relleno + aristas de elementos
    for elem in project.elements.values():
        nids = elem.node_ids[:4]
        if not all(nid in project.nodes for nid in nids):
            continue
        pts = [view.w2s(project.nodes[n].x, project.nodes[n].y) for n in nids]
        draw.polygon(pts, fill=_ELEMENT_FACE, outline=_ELEMENT_EDGE)
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        draw.text((cx, cy), f"E{elem.id}", fill=_ELEMENT_EDGE, font=font_id,
                  anchor="mm")

    # Clasificación de nodos por rol (Q9) — mismo código visual que el canvas.
    is_q9 = getattr(project, "element_type", None) == ELEMENT_Q9
    corner, mid, center = set(), set(), set()
    if is_q9:
        for elem in project.elements.values():
            ids = list(elem.node_ids)
            if len(ids) >= 4:
                corner.update(ids[:4])
            if len(ids) >= 8:
                mid.update(ids[4:8])
            if len(ids) >= 9:
                center.add(ids[8])
        mid -= corner
        center -= corner | mid
    else:
        corner = set(project.nodes.keys())

    def _dot(nid, color, r):
        n = project.nodes.get(nid)
        if n is None:
            return
        sx, sy = view.w2s(n.x, n.y)
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=color,
                     outline=(0, 0, 0))

    for nid in mid:
        _dot(nid, _RGB_NODE_MID, 4)
    for nid in center:
        _dot(nid, _RGB_NODE_CENTER, 4)
    for nid in corner:
        _dot(nid, _RGB_NODE_CORNER, 5)
    for nid, n in project.nodes.items():
        sx, sy = view.w2s(n.x, n.y)
        draw.text((sx + 6, sy - 14), str(nid), fill=_ELEMENT_EDGE, font=font_id)

    # Escala característica para símbolos de restricción.
    bbox_extent = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
    bc_px = max(view.scale * 0.04 * bbox_extent, 10)
    for nid, bc in project.boundary_conditions.items():
        if nid not in project.nodes or not (bc.restrain_x or bc.restrain_y):
            continue
        n = project.nodes[nid]
        sx, sy = view.w2s(n.x, n.y)
        _draw_bc_marker(draw, sx, sy, bc, bc_px)

    # Flechas de cargas nodales (apuntando al nodo).
    if project.nodal_loads:
        max_mag = max(
            (ld.fx ** 2 + ld.fy ** 2) ** 0.5
            for ld in project.nodal_loads.values()
        ) or 1.0
        arrow_max = 0.14 * min(width, height)
        for nid, ld in project.nodal_loads.items():
            if nid not in project.nodes:
                continue
            mag = (ld.fx ** 2 + ld.fy ** 2) ** 0.5
            if mag <= 1e-12:
                continue
            n = project.nodes[nid]
            sx, sy = view.w2s(n.x, n.y)
            # +Y mundo es hacia arriba; en pantalla Y crece hacia abajo.
            ux, uy = ld.fx / mag, -ld.fy / mag
            length = arrow_max * (mag / max_mag)
            x0, y0 = sx - ux * length, sy - uy * length
            _draw_arrow(draw, x0, y0, sx, sy, _RGB_LOAD, width=3)

    _title(draw, "Modelo discretizado", width)
    return img


def _draw_bc_marker(draw, sx, sy, bc, s):
    """Dibuja un símbolo de restricción (pantalla, Y hacia abajo)."""
    col = _RGB_CONSTRAINT
    if bc.restrain_x and bc.restrain_y:
        # Empotramiento: triángulo apuntando al nodo + base + hachuras.
        draw.polygon([(sx, sy), (sx - s, sy + 2 * s), (sx + s, sy + 2 * s)],
                     outline=col, fill=None)
        draw.line([(sx - 1.4 * s, sy + 2 * s), (sx + 1.4 * s, sy + 2 * s)],
                  fill=col, width=2)
        for i in range(3):
            lx = sx - s + i * s
            draw.line([(lx, sy + 2 * s), (lx - 0.5 * s, sy + 2.5 * s)],
                      fill=col, width=1)
    elif bc.restrain_y and not bc.restrain_x:
        # Rodillo Y: triángulo apuntando al nodo + círculo debajo.
        draw.polygon([(sx, sy), (sx - s, sy + 1.4 * s), (sx + s, sy + 1.4 * s)],
                     outline=col, fill=None)
        cy = sy + 1.4 * s + 0.4 * s
        draw.ellipse([sx - 0.4 * s, cy - 0.4 * s, sx + 0.4 * s, cy + 0.4 * s],
                     outline=col)
        draw.line([(sx - 1.4 * s, cy + 0.4 * s), (sx + 1.4 * s, cy + 0.4 * s)],
                  fill=col, width=2)
    else:
        # Rodillo X: triángulo apoyado a la izquierda + círculo + pared.
        draw.polygon([(sx, sy), (sx - 1.4 * s, sy - s), (sx - 1.4 * s, sy + s)],
                     outline=col, fill=None)
        cx = sx - 1.4 * s - 0.4 * s
        draw.ellipse([cx - 0.4 * s, sy - 0.4 * s, cx + 0.4 * s, sy + 0.4 * s],
                     outline=col)
        draw.line([(cx - 0.4 * s, sy - 1.4 * s), (cx - 0.4 * s, sy + 1.4 * s)],
                  fill=col, width=2)


def _draw_arrow(draw, x0, y0, x1, y1, color, *, width=2):
    """Línea de (x0,y0) a (x1,y1) con cabeza de flecha en (x1,y1)."""
    draw.line([(x0, y0), (x1, y1)], fill=color, width=width)
    dx, dy = x1 - x0, y1 - y0
    L = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / L, dy / L
    head = 9.0
    left = (x1 - head * (ux * 0.87 - uy * 0.5),
            y1 - head * (uy * 0.87 + ux * 0.5))
    right = (x1 - head * (ux * 0.87 + uy * 0.5),
             y1 - head * (uy * 0.87 - ux * 0.5))
    draw.polygon([(x1, y1), left, right], fill=color)


# ---------------------------------------------------------------------------
# Contornos de tensión
# ---------------------------------------------------------------------------

_COMPONENT_LABELS = {
    "sigma_x": "sigma_x",
    "sigma_y": "sigma_y",
    "tau_xy": "tau_xy",
    "von_mises": "sigma_VM",
}


def render_contour(project, solution, nodal_stresses, component, *,
                   deformed=False, scale=None, width=920, height=680):
    """Mapa de contorno (Gouraud bilineal + wireframe + colorbar) sobre fondo
    blanco para una componente nodal promediada. Devuelve PIL.Image o None.

    component ∈ {"sigma_x", "sigma_y", "tau_xy", "von_mises"}.
    """
    if not HAS_PIL or not nodal_stresses or not project.nodes \
            or not project.elements:
        return None

    nid_list = sorted(project.nodes.keys())
    values = {nid: float(nodal_stresses.get(nid, {}).get(component, 0.0))
              for nid in nid_list}
    present = [v for nid, v in values.items()
               if nid in nodal_stresses]
    if not present:
        return None
    vmin, vmax = float(min(present)), float(max(present))
    if abs(vmax - vmin) < 1e-12:
        vmax = vmin + 1.0

    # Coordenadas (deformadas si aplica).
    deformed_coords = None
    if deformed:
        sc = scale if scale is not None else _deformed_scale(
            project, solution, nid_list)
        u = solution["u"]
        idx_map = project.node_index_map
        deformed_coords = {
            nid: (project.nodes[nid].x + sc * u[2 * idx_map[nid]],
                  project.nodes[nid].y + sc * u[2 * idx_map[nid] + 1])
            for nid in nid_list
        }
        coords_x = [c[0] for c in deformed_coords.values()]
        coords_y = [c[1] for c in deformed_coords.values()]
    else:
        coords_x = [project.nodes[n].x for n in nid_list]
        coords_y = [project.nodes[n].y for n in nid_list]

    cbar_w = 110
    view = _View(coords_x, coords_y, width, height,
                 pad_left=30, pad_right=40 + cbar_w, pad_top=46, pad_bottom=30)
    lut = _colormap_lut(_cmap_for(component))

    arr = np.empty((height, width, 4), dtype=np.uint8)
    arr[..., 0] = _FIG_BG[0]
    arr[..., 1] = _FIG_BG[1]
    arr[..., 2] = _FIG_BG[2]
    arr[..., 3] = 255
    _fill_field(arr, width, height, project, view, values, vmin, vmax, lut,
                deformed_coords=deformed_coords)
    img = Image.fromarray(arr, "RGBA").convert("RGB")
    draw = ImageDraw.Draw(img)
    _draw_wireframe(draw, project, view, deformed_coords=deformed_coords)
    _draw_colorbar(draw, height, lut, vmin, vmax, _COMPONENT_LABELS.get(
        component, component), x0=width - cbar_w + 8)
    suffix = "  (malla deformada)" if deformed else ""
    _title(draw, f"Contorno de {_COMPONENT_LABELS.get(component, component)}"
                 f"{suffix}", width)
    return img


# ---------------------------------------------------------------------------
# Deformada
# ---------------------------------------------------------------------------

def render_deformed(project, solution, scale=None, *, width=900, height=680):
    """Malla original (gris) + malla deformada (verde) + nodos. PIL.Image."""
    if not HAS_PIL or not project.elements or solution is None:
        return None
    nid_list = sorted(project.nodes.keys())
    if not nid_list:
        return None
    sc = scale if scale is not None else _deformed_scale(
        project, solution, nid_list)
    u = solution["u"]
    idx_map = project.node_index_map
    deformed_coords = {
        nid: (project.nodes[nid].x + sc * u[2 * idx_map[nid]],
              project.nodes[nid].y + sc * u[2 * idx_map[nid] + 1])
        for nid in nid_list
    }
    # Vista que abarca original y deformada.
    xs = [project.nodes[n].x for n in nid_list] + \
         [c[0] for c in deformed_coords.values()]
    ys = [project.nodes[n].y for n in nid_list] + \
         [c[1] for c in deformed_coords.values()]
    view = _View(xs, ys, width, height,
                 pad_left=36, pad_right=36, pad_top=48, pad_bottom=36)

    img = Image.new("RGB", (width, height), _FIG_BG)
    draw = ImageDraw.Draw(img)
    # Malla original (gris claro, contexto).
    _draw_wireframe(draw, project, view, color=(180, 180, 188), width=1)
    # Malla deformada (verde, post-proceso).
    _draw_wireframe(draw, project, view, deformed_coords=deformed_coords,
                    color=_RGB_DEFORMED, width=2)
    for nid, (wx, wy) in deformed_coords.items():
        sx, sy = view.w2s(wx, wy)
        draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=_RGB_NODE_CORNER,
                     outline=(0, 0, 0))
    _title(draw, f"Configuracion deformada  (escala x{sc:.3g})", width)
    return img


# ---------------------------------------------------------------------------
# Patrón de dispersión de K (reemplaza al heatmap matplotlib)
# ---------------------------------------------------------------------------

def render_K_sparsity(K, *, size=620, tol=1e-9):
    """Patrón de no-nulos de la matriz global K (negro sobre blanco).

    Acepta K densa (np.ndarray) o scipy sparse. Útil cuando K es demasiado
    grande para mostrarse literal. Devuelve PIL.Image cuadrada."""
    if not HAS_PIL:
        return None
    try:
        from scipy.sparse import issparse
    except Exception:
        issparse = lambda m: False  # noqa: E731
    if issparse(K):
        coo = K.tocoo()
        n = K.shape[0]
        rows = coo.row[np.abs(coo.data) > tol]
        cols = coo.col[np.abs(coo.data) > tol]
    else:
        A = np.asarray(K)
        n = A.shape[0]
        nz = np.argwhere(np.abs(A) > tol)
        rows = nz[:, 0]
        cols = nz[:, 1]
    if n == 0:
        return None

    pad = 30
    avail = size - 2 * pad
    img = Image.new("RGB", (size, size), _FIG_BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([pad, pad, pad + avail, pad + avail],
                   outline=(150, 150, 150))
    cell = max(avail / n, 1.0)
    dot = max(int(cell), 1)
    for i, j in zip(rows, cols):
        x = pad + int(j * avail / n)
        y = pad + int(i * avail / n)
        draw.rectangle([x, y, x + dot - 1, y + dot - 1],
                       fill=(33, 33, 51))
    _title(draw, "Patron de no-nulos de K (estructura de banda)", size, y=8)
    return img
