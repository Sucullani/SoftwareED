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

Nivel de detalle: las figuras del modelo y de la deformada deciden cuánto
dibujar con el MISMO criterio que el canvas (`_detail` → `canvas_logic.
lod_level` sobre `median_edge_length * scale`). En una malla densa un disco y
un número por nodo tapan lo que la figura tiene que mostrar; en mallas de
pocos elementos no se degrada nada. Ver `docs/convenciones/memoria-calculo.md`.

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
    fmt_escala,
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
    else:
        anchors = _JET_ANCHORS
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


# Fuentes TrueType candidatas, en orden. Las cuatro traen alfabeto griego
# (sigma, tau) y acentos, que es lo que necesitan los rotulos de campo. Si no
# hay ninguna se cae al bitmap default de Pillow, que NO tiene griego: en ese
# caso los rotulos degradan a ASCII (ver `_component_label`).
_TTF_CANDIDATES = ("DejaVuSans.ttf", "arial.ttf",
                   "LiberationSans-Regular.ttf", "segoeui.ttf")
_ttf_name: str | None = None
_ttf_resolved = False


def _resolve_ttf() -> str | None:
    """Nombre de la primera TrueType disponible (memoizado), o None."""
    global _ttf_name, _ttf_resolved
    if not _ttf_resolved:
        _ttf_resolved = True
        if HAS_PIL:
            for name in _TTF_CANDIDATES:
                try:
                    ImageFont.truetype(name, 12)
                except Exception:
                    continue
                _ttf_name = name
                break
    return _ttf_name


def _font(size: int):
    """Carga una fuente TrueType legible; cae al bitmap default si falta."""
    if not HAS_PIL:
        return None
    name = _resolve_ttf()
    if name is not None:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _tint(rgb: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    """Mezcla `rgb` con blanco: t=0 → rgb, t=1 → blanco. Para rellenos suaves."""
    return tuple(int(round(c + (255 - c) * t)) for c in rgb)


def _detail(project, view):
    """Nivel de detalle de la figura: `("far" | "mid" | "near", edge_px)`.

    Mismo criterio y mismos umbrales que el `MeshCanvas`
    (`canvas_logic.lod_level` sobre `median_edge_length * scale`): si la malla
    es lo bastante densa como para que los nodos, sus numeros y los simbolos
    de apoyo se pisen, se dibuja menos. Sin esto la figura del modelo y la
    deformada de un ejemplo real (Cook 32x32: 4225 nodos a ~8 px de
    separacion) salian como una mancha azul de discos superpuestos.

    Las mallas de <= `LOD_MIN_ELEMENTS_FOR_GATING` elementos nunca se
    degradan: el ejemplo canonico se ve exactamente igual que antes.
    """
    try:
        from models.mesh_utils import median_edge_length
        from gui.preprocessing.canvas_logic import lod_level
        med = median_edge_length(project)
        edge_px = None if med is None else float(med) * view.scale
        return lod_level(edge_px, len(project.elements)), edge_px
    except Exception:
        # Degradar a "near" deja la figura como era antes (todo dibujado), asi
        # que no rompe nada — pero si esto falla en una malla grande la figura
        # vuelve a ser una mancha y nadie sabria por que: dejar traza.
        import traceback
        traceback.print_exc()
        return "near", None


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

def _fill_field(img_arr, w, h, project, view, node_values, vmin, vmax, lut,
                *, deformed_coords=None, subdiv=6):
    """Pinta el gradiente de `node_values` sobre cada elemento (corners Q4).

    `deformed_coords`: dict {nid: (x, y)} con coords deformadas, o None para
    usar la geometría original.

    Vectorizado: arma de una sola vez los 2·subdiv² triángulos de TODOS los
    elementos y los pinta con `canvas_raster.rasterize_triangles`, el mismo
    kernel por lotes que usa el canvas interactivo. Antes había un loop
    Python por triángulo: 72 llamadas por elemento, 16,7 s en una malla de
    1024 elementos. La paridad píxel a píxel con esa versión la verifica
    `tests/test_canvas_raster.py` (test_figure_export_field).

    El orden de los triángulos se conserva (elemento por elemento, y dentro
    de cada uno celda por celda): el último pintado gana el píxel de borde
    compartido, así que alterarlo cambiaría la imagen.
    """
    import numpy as _np
    from gui.preprocessing.canvas_raster import (
        element_grid_points, element_grid_values, grid_triangles,
        rasterize_triangles,
    )

    n = subdiv
    corners, values = [], []
    for elem in project.elements.values():
        nids = elem.node_ids[:4]
        if not all(nid in project.nodes for nid in nids):
            continue
        if not all(nid in node_values for nid in nids):
            continue
        if deformed_coords is not None:
            corners.append([deformed_coords[nid] for nid in nids])
        else:
            corners.append([(project.nodes[nid].x, project.nodes[nid].y)
                            for nid in nids])
        values.append([float(node_values[nid]) for nid in nids])
    if not corners:
        return

    world = element_grid_points(_np.array(corners, dtype=float), n)   # (e, p, 2)
    vals = element_grid_values(_np.array(values, dtype=float), n)     # (e, p)
    sx = world[:, :, 0] * view.scale + view.offset_x
    sy = -world[:, :, 1] * view.scale + view.offset_y

    idx = grid_triangles(n)                                           # (2n², 3)
    tris = _np.empty((sx.shape[0], idx.shape[0], 3, 3))
    tris[:, :, :, 0] = sx[:, idx]
    tris[:, :, :, 1] = sy[:, idx]
    tris[:, :, :, 2] = vals[:, idx]
    rasterize_triangles(img_arr, tris.reshape(-1, 3, 3), vmin, vmax, lut)


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
        # Ticks con el MISMO formato que la colorbar del lienzo y la de la
        # Vista 3D (`config.settings.fmt_escala`, fuente unica de las tres
        # escalas): un esfuerzo en Pa se lee `2.50e+07`, no `2.5e+07` en una
        # pantalla y `25000000` en el PDF.
        draw.text((x0 + bar_w + 7, yy - 7), fmt_escala(val),
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

def _flechas_de_carga(project, width, height):
    """Vector unitario en pantalla y largo en píxeles de cada carga nodal.

    Devuelve `{id_nodo: (ux, uy, largo)}`. Se calcula ANTES de armar la
    vista porque la flecha se dibuja **desde afuera hacia el nodo**: la cola
    cae fuera del área que ocupa la malla, y hay que reservarle margen.
    """
    if not getattr(project, "nodal_loads", None):
        return {}
    magnitudes = {nid: (ld.fx ** 2 + ld.fy ** 2) ** 0.5
                  for nid, ld in project.nodal_loads.items()
                  if nid in project.nodes}
    max_mag = max(magnitudes.values(), default=0.0) or 1.0
    largo_max = 0.14 * min(width, height)
    flechas = {}
    for nid, mag in magnitudes.items():
        if mag <= 1e-12:
            continue
        ld = project.nodal_loads[nid]
        # +Y mundo es hacia arriba; en pantalla Y crece hacia abajo.
        flechas[nid] = (ld.fx / mag, -ld.fy / mag,
                        largo_max * (mag / max_mag))
    return flechas


def _margen_de_flechas(flechas):
    """Píxeles a reservar en cada borde para que las colas entren:
    `(izquierda, derecha, arriba, abajo)`."""
    izq = der = arriba = abajo = 0.0
    for ux, uy, largo in flechas.values():
        izq = max(izq, ux * largo)
        der = max(der, -ux * largo)
        arriba = max(arriba, uy * largo)
        abajo = max(abajo, -uy * largo)
    return izq, der, arriba, abajo


def render_mesh_diagram(project, *, width=900, height=680):
    """Geometría + nodos numerados + restricciones + cargas, estilo canvas
    sobre fondo blanco. Devuelve PIL.Image o None."""
    if not HAS_PIL or not project.nodes or not project.elements:
        return None
    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    # La malla deja lugar para las flechas de sus cargas. Sin esto, la carga
    # de un nodo del borde superior dibujaba una flecha cuya cola caía FUERA
    # de la imagen y cruzaba el título: en el ejemplo canónico la cola quedaba
    # 47 px arriba del borde a 900 px de ancho, y 11 px a 560 px. La flecha es
    # una de las cuatro cosas que esta figura tiene que mostrar.
    flechas = _flechas_de_carga(project, width, height)
    m_izq, m_der, m_arriba, m_abajo = _margen_de_flechas(flechas)
    view = _View(xs, ys, width, height,
                 pad_left=40 + m_izq, pad_right=40 + m_der,
                 pad_top=48 + m_arriba, pad_bottom=40 + m_abajo)

    img = Image.new("RGB", (width, height), _FIG_BG)
    draw = ImageDraw.Draw(img)
    font_id = _font(13)

    # Nivel de detalle (mismos umbrales que el canvas): en 'near' la figura es
    # identica a la de siempre; en mallas densas se recortan los numeros de
    # nodo, los nodos de andamiaje Q9 y el tamano de los simbolos de apoyo.
    lod, edge_px = _detail(project, view)

    # Relleno + aristas de elementos. El rotulo "EN" se dibuja solo si el
    # elemento mide en pantalla al menos lo que el texto: en mallas finas los
    # rotulos se pisan hasta volverse una mancha ilegible y ademas dominan el
    # render (una llamada a draw.text por elemento: 8 s en 4096 elementos).
    _, _, label_w, label_h = draw.textbbox((0, 0), "E000", font=font_id)
    for elem in project.elements.values():
        nids = elem.node_ids[:4]
        if not all(nid in project.nodes for nid in nids):
            continue
        pts = [view.w2s(project.nodes[n].x, project.nodes[n].y) for n in nids]
        draw.polygon(pts, fill=_ELEMENT_FACE, outline=_ELEMENT_EDGE)
        xs_px = [p[0] for p in pts]
        ys_px = [p[1] for p in pts]
        if max(xs_px) - min(xs_px) >= label_w and                 max(ys_px) - min(ys_px) >= label_h:
            draw.text((sum(xs_px) / len(pts), sum(ys_px) / len(pts)),
                      f"E{elem.id}", fill=_ELEMENT_EDGE, font=font_id,
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

    # Radios por nivel de detalle: el canvas encoge las decoraciones al alejar
    # y en 'far' deja de dibujar los nodos de andamiaje Q9 (mid/center), que a
    # esa escala son ruido puro. La figura va un paso mas alla porque es
    # estatica (no hay zoom que la rescate): en 'mid' solo esquinas, y en
    # 'far' ningun disco — la geometria la cuentan los elementos.
    r_corner = {"near": 5, "mid": 3}.get(lod, 0)
    r_mid = {"near": 4}.get(lod, 0)
    if r_mid:
        for nid in mid:
            _dot(nid, _RGB_NODE_MID, r_mid)
        for nid in center:
            _dot(nid, _RGB_NODE_CENTER, r_mid)
    if r_corner:
        for nid in corner:
            _dot(nid, _RGB_NODE_CORNER, r_corner)
    # Numeracion global: solo en 'near', igual que
    # `canvas_logic.label_globally_visible` en modo "auto". Con 4225 nodos a
    # 8 px los numeros se pisaban hasta tapar el modelo entero.
    if lod == "near":
        for nid, n in project.nodes.items():
            sx, sy = view.w2s(n.x, n.y)
            draw.text((sx + 6, sy - 14), str(nid), fill=_ELEMENT_EDGE,
                      font=font_id)

    # Escala característica para símbolos de restricción, acotada por la
    # separacion entre nodos: en un borde con 33 apoyos, un simbolo de 24 px
    # cada 8 px es una mancha naranja donde no se distingue ni el tipo de
    # apoyo ni la malla que hay debajo.
    bbox_extent = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
    bc_px = max(view.scale * 0.04 * bbox_extent, 10)
    if edge_px:
        node_px = edge_px / 2.0 if is_q9 else edge_px
        bc_px = max(min(bc_px, 0.5 * node_px), 6)
    for nid, bc in project.boundary_conditions.items():
        if nid not in project.nodes or not (bc.restrain_x or bc.restrain_y):
            continue
        n = project.nodes[nid]
        sx, sy = view.w2s(n.x, n.y)
        _draw_bc_marker(draw, sx, sy, bc, bc_px)

    # Flechas de cargas nodales (apuntando al nodo). La geometría ya se
    # calculó arriba: es la misma que reservó el margen.
    for nid, (ux, uy, largo) in flechas.items():
        n = project.nodes[nid]
        sx, sy = view.w2s(n.x, n.y)
        _draw_arrow(draw, sx - ux * largo, sy - uy * largo, sx, sy,
                    _RGB_LOAD, width=3)

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

# Simbolos de los componentes de tension. Los mismos que la colorbar del
# lienzo y la de la Vista 3D (`post_tab._update_canvas_result`): el alumno
# tiene que reconocer en la Memoria el mismo campo que vio en pantalla, no una
# key interna (`sigma_x`). Sin subindices unicode (se rinden como cajas).
_COMPONENT_LABELS = {
    "sigma_x": "σx",
    "sigma_y": "σy",
    "tau_xy": "τxy",
    "von_mises": "σVM",
}
# Degradacion para el bitmap default de Pillow, que no trae griego.
_COMPONENT_LABELS_ASCII = {
    "sigma_x": "sigma_x",
    "sigma_y": "sigma_y",
    "tau_xy": "tau_xy",
    "von_mises": "sigma_VM",
}


def _component_label(component: str) -> str:
    """Simbolo visible del componente (griego si la fuente lo soporta)."""
    table = (_COMPONENT_LABELS if _resolve_ttf() is not None
             else _COMPONENT_LABELS_ASCII)
    return table.get(component, component)


def _stress_unit(project) -> str:
    """Unidad de esfuerzo del sistema del proyecto (`MPa`, `Pa`, `ksi`...).

    Misma fuente que las tablas del Post y la colorbar del lienzo
    (`config.units.get_unit_labels`). Cadena vacia si no se puede resolver."""
    try:
        from config.units import get_unit_labels
        return get_unit_labels(project.unit_system).get("esfuerzo", "") or ""
    except Exception:
        return ""


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
    # Rotulo de la escala: simbolo + unidad del sistema del proyecto, igual
    # que la colorbar del lienzo y la de la Vista 3D. Era el unico campo de
    # resultados que llegaba al alumno sin decir en que unidad esta.
    sym = _component_label(component)
    unit = _stress_unit(project)
    _draw_colorbar(draw, height, lut, vmin, vmax,
                   f"{sym} [{unit}]" if unit else sym,
                   x0=width - cbar_w + 8)
    suffix = "  (malla deformada)" if deformed else ""
    _title(draw, f"Contorno de {sym}{suffix}", width)
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
    # Nodos solo cuando se distinguen (mismo criterio que el canvas): con la
    # malla densa los discos se solapan y tapan por completo la deformada
    # verde, que es justamente lo que la figura tiene que mostrar.
    lod, _edge_px = _detail(project, view)
    if lod == "near":
        for nid, (wx, wy) in deformed_coords.items():
            sx, sy = view.w2s(wx, wy)
            draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3],
                         fill=_RGB_NODE_CORNER, outline=(0, 0, 0))
    _title(draw, f"Configuración deformada  (escala ×{sc:.3g})", width)
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
    _title(draw, "Patrón de no-nulos de K (estructura de banda)", size, y=8)
    return img
