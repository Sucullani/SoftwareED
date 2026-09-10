"""Logica pura del MeshCanvas (sin Tk) — testeable headless.

Auditoria UX 2026-05 (docs/auditorias/historico/2026-05-30_auditoria_canvas_ux.md): el canvas no decidia
*cuanto* dibujar segun la escala. Aqui viven las decisiones puras de
visibilidad progresiva (LOD por zoom) y de culling por viewport, separadas
del widget Tk para poder testearlas sin display.

Ninguna funcion de este modulo importa tkinter — solo aritmetica + numpy +
constantes de config. El `MeshCanvas` las consume.
"""

from __future__ import annotations

import math

import numpy as np

from config.settings import (
    LOD_EDGE_PX_FAR, LOD_EDGE_PX_NEAR, LOD_MIN_ELEMENTS_FOR_GATING,
    GRID_TARGET_PX, GRID_MAJOR_EVERY, GRID_MAX_LINES,
    ELEMENT_Q4, ELEMENT_Q9, fmt, fmt_escala,
)


def lod_level(edge_px, n_elements,
              *, far=LOD_EDGE_PX_FAR, near=LOD_EDGE_PX_NEAR,
              min_elements=LOD_MIN_ELEMENTS_FOR_GATING):
    """Devuelve el nivel de detalle: ``"far" | "mid" | "near"``.

    `edge_px`: pixeles-por-arista-media (mediana de longitud de arista en
        mundo * scale). None o no positivo -> se trata como "near" (no hay
        informacion de escala util, no clutter por defecto).
    `n_elements`: cantidad de elementos del modelo. Mallas chicas
        (<= `min_elements`) NUNCA aplican gating: siempre "near" (preserva la
        experiencia didactica de los ejemplos pequeños).

    Umbrales: edge_px < far -> "far"; < near -> "mid"; >= near -> "near".
    """
    if n_elements is not None and n_elements <= min_elements:
        return "near"
    if edge_px is None or edge_px <= 0.0:
        return "near"
    if edge_px < far:
        return "far"
    if edge_px < near:
        return "mid"
    return "near"


def bbox_visible(min_sx, min_sy, max_sx, max_sy, w, h, margin):
    """True si el bbox en coords PANTALLA (sx, sy) intersecta el viewport
    [0, w] x [0, h] expandido por `margin` pixeles en cada lado.

    Usado para culling: los items cuyo bbox cae completamente fuera del
    viewport (+ margen) no se crean. El margen generoso evita "popping"
    durante paneos pequeños (el pan mueve items existentes con canvas.move;
    el redraw que recomputa el culling solo corre al soltar el pan).
    """
    if max_sx < -margin or min_sx > w + margin:
        return False
    if max_sy < -margin or min_sy > h + margin:
        return False
    return True


def point_visible(sx, sy, w, h, margin):
    """True si el punto pantalla (sx, sy) esta dentro del viewport + margen."""
    return (-margin <= sx <= w + margin) and (-margin <= sy <= h + margin)


# Politica de visibilidad de etiquetas (numeracion bajo demanda).
# `mode` in {"auto", "always", "never"}.

def label_globally_visible(mode, lod, *, ghost):
    """True si la numeracion GLOBAL (todos los items) debe verse.

    En modo "auto" la numeracion aparece solo en zoom cercano ("near"). En
    "always" siempre; en "never" nunca. En modo fantasma (overlay M0) nunca.
    El realce por seleccion se decide aparte (ver `label_visible_for_item`).
    """
    if ghost:
        return False
    if mode == "always":
        return True
    if mode == "never":
        return False
    return lod == "near"   # auto


def label_visible_for_item(mode, lod, *, ghost, selected):
    """True si la etiqueta de UN item concreto debe dibujarse.

    Combina la politica global con el realce por seleccion: el item
    seleccionado muestra su id a cualquier zoom (patron "query" de Abaqus),
    salvo que el modo sea "never" o estemos en modo fantasma.
    """
    if ghost or mode == "never":
        return False
    if label_globally_visible(mode, lod, ghost=ghost):
        return True
    return bool(selected)


# ═══════════════════════════════════════════════════════════════════════
# Cuadricula anclada al mundo (rediseño 2026-09-09)
# ═══════════════════════════════════════════════════════════════════════
#
# La cuadricula vive en coordenadas del modelo, no de la pantalla: sus
# lineas caen en valores redondos de X e Y, con un paso de la serie 1-2-5
# elegido para que en pantalla mida ~GRID_TARGET_PX. Enseña el sistema de
# coordenadas en el que el alumno tipea los nodos (tabla y modo dibujo).

def grid_step(scale, *, target_px=GRID_TARGET_PX):
    """Paso de la cuadricula en unidades del mundo: el valor de la serie
    {1, 2, 5} x 10^k cuyo tamano en pantalla (`paso * scale`) queda mas
    cerca de `target_px`. Con escala nula o invalida devuelve 1.0."""
    try:
        scale = float(scale)
    except (TypeError, ValueError):
        return 1.0
    if not math.isfinite(scale) or scale <= 0.0:
        return 1.0
    raw = target_px / scale                       # paso ideal en mundo
    if raw <= 0.0 or not math.isfinite(raw):
        return 1.0
    exponent = math.floor(math.log10(raw))
    best, best_err = 1.0, float("inf")
    for k in (exponent - 1, exponent, exponent + 1):
        for m in (1.0, 2.0, 5.0):
            cand = m * 10.0 ** k
            err = abs(math.log(cand * scale / target_px))
            if err < best_err:
                best, best_err = cand, err
    return best


def grid_range(lo, hi, step, *, max_lines=GRID_MAX_LINES):
    """Valores `k * step` (k entero) que cubren [lo, hi], incluidos los dos
    extremos redondeados hacia afuera. Acotado a `max_lines` valores: si el
    rango pedido es absurdo respecto del paso se devuelve una lista vacia
    (mejor sin cuadricula que con miles de lineas)."""
    if step <= 0 or hi < lo:
        return []
    k0 = math.floor(lo / step)
    k1 = math.ceil(hi / step)
    if k1 - k0 + 1 > max_lines:
        return []
    return [k * step for k in range(k0, k1 + 1)]


def is_major_line(value, step, *, every=GRID_MAJOR_EVERY):
    """True si `value` cae en una linea mayor (cada `every` pasos)."""
    if step <= 0:
        return False
    k = int(round(value / step))
    return k % every == 0


def grid_label(value):
    """Rotulo del valor de una linea mayor. `-0` se normaliza a `0` y los
    valores redondos no arrastran decimales (`5`, no `5.000`): es una escala,
    como la de la colorbar, y comparte su formateador."""
    if abs(value) < 1e-12:
        return "0"
    return fmt_escala(value)


# ═══════════════════════════════════════════════════════════════════════
# Lente del sistema: marco local del elemento y puntos de Gauss fisicos
# ═══════════════════════════════════════════════════════════════════════

def polygon_area(pts):
    """Area (positiva) del poligono `pts` = [(x, y), ...] por la formula del
    zapatero. Con menos de 3 puntos devuelve 0."""
    n = len(pts)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) * 0.5


def element_local_frame(pts, *, reach=0.55):
    """Centroide y extremos de los ejes naturales (ξ, η) de un cuadrilatero
    dado por sus 4 vertices en orden local (N1..N4).

    Convencion isoparametrica del motor (`fem/shape_functions.py`): la arista
    N2-N3 es ξ = +1 y la arista N3-N4 es η = +1. El eje ξ apunta del
    centroide al punto medio de N2-N3 y el eje η al de N3-N4; `reach` es la
    fraccion del camino que recorre la flecha (< 1 para no pisar la arista).
    Devuelve None si no hay 4 vertices."""
    if len(pts) < 4:
        return None
    x = [float(p[0]) for p in pts[:4]]
    y = [float(p[1]) for p in pts[:4]]
    cx = sum(x) / 4.0
    cy = sum(y) / 4.0
    mid_xi = ((x[1] + x[2]) * 0.5, (y[1] + y[2]) * 0.5)
    mid_eta = ((x[2] + x[3]) * 0.5, (y[2] + y[3]) * 0.5)
    return {
        "centroid": (cx, cy),
        "xi_end": (cx + reach * (mid_xi[0] - cx), cy + reach * (mid_xi[1] - cy)),
        "eta_end": (cx + reach * (mid_eta[0] - cx), cy + reach * (mid_eta[1] - cy)),
    }


def gauss_physical_points(node_pts, element_type):
    """Coordenadas fisicas (x, y) de los puntos de Gauss del elemento:
    x = Σ Nᵢ(ξ_p, η_p) xᵢ con las N y los PG del motor (2x2 en Q4, 3x3 en
    Q9). `node_pts` son las coordenadas de TODOS los nodos del elemento en
    orden local (4 o 9). Devuelve un array (n_pg, 2); vacio si faltan
    nodos."""
    from fem.shape_functions import get_shape_functions
    from fem.gauss_quadrature import get_gauss_points_for_element

    X = np.asarray(node_pts, dtype=float)
    etype = ELEMENT_Q9 if (element_type == ELEMENT_Q9 and X.shape[0] >= 9) \
        else ELEMENT_Q4
    n_needed = 9 if etype == ELEMENT_Q9 else 4
    if X.ndim != 2 or X.shape[0] < n_needed:
        return np.zeros((0, 2))
    X = X[:n_needed]
    N_func, _ = get_shape_functions(etype)
    gp, _w = get_gauss_points_for_element(etype)
    out = np.zeros((len(gp), 2))
    for k, (xi, eta) in enumerate(gp):
        N = np.asarray(N_func(float(xi), float(eta)), dtype=float).ravel()
        out[k] = N @ X
    return out


# ═══════════════════════════════════════════════════════════════════════
# Franja lectora: textos en terminos del MEF
# ═══════════════════════════════════════════════════════════════════════
#
# Devuelven (cabecera, cuerpo). La cabecera identifica la entidad; el cuerpo
# la describe con lo que el metodo hace con ella. Todo lo visible va en
# espanol y los numeros pasan por `fmt` (regla dura 8).

_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _sub(n):
    return str(n).translate(_SUB)


def restraint_words(bc):
    """Describe una restriccion: 'empotrado (x e y)', 'rodillo (solo y)'..."""
    if bc is None:
        return "libre"
    if bc.restrain_x and bc.restrain_y:
        return "empotrado (x e y)"
    if bc.restrain_x:
        return "restringido en x (rodillo)"
    if bc.restrain_y:
        return "restringido en y (rodillo)"
    return "libre"


def node_summary(project, nid, *, units=None):
    """(cabecera, cuerpo) del nodo `nid` para la franja lectora."""
    node = project.nodes.get(nid)
    if node is None:
        return (f"Nodo {nid}", "ya no existe")
    units = units or {}
    lu = units.get("longitud", "")
    fu = units.get("fuerza", "")
    idx = project.node_index_map.get(nid)
    parts = [f"({fmt(node.x, 'length')}, {fmt(node.y, 'length')}) {lu}".rstrip()]
    if idx is not None:
        base = 2 * idx
        parts.append(f"GDL u{_sub(nid)}→{base}, v{_sub(nid)}→{base + 1}")
    bc = project.boundary_conditions.get(nid)
    parts.append(restraint_words(bc))
    load = project.nodal_loads.get(nid)
    if load is not None:
        parts.append(
            f"F = ({fmt(load.fx, 'force')}, {fmt(load.fy, 'force')}) {fu}".rstrip())
    n_el = sum(1 for e in project.elements.values() if nid in e.node_ids)
    if n_el == 0:
        parts.append("sin elemento (huérfano)")
    elif n_el == 1:
        parts.append("en 1 elemento")
    else:
        parts.append(f"compartido por {n_el} elementos")
    return (f"Nodo {nid}", "  ·  ".join(parts))


def element_summary(project, eid, *, units=None):
    """(cabecera, cuerpo) del elemento `eid` para la franja lectora."""
    elem = project.elements.get(eid)
    if elem is None:
        return (f"Elemento {eid}", "ya no existe")
    units = units or {}
    lu = units.get("longitud", "")
    corners = elem.node_ids[:4]
    head = f"Elemento {eid} · {elem.element_type}"
    parts = ["nodos " + "→".join(str(n) for n in corners) + " (antihorario)"]
    if elem.num_nodes > 4:
        parts[-1] += f" + {elem.num_nodes - 4} internos"
    parts.append(elem.material_name or "sin material")
    parts.append(f"t = {fmt(elem.thickness, 'length')} {lu}".rstrip())
    pts = []
    for n in corners:
        node = project.nodes.get(n)
        if node is None:
            break
        pts.append((node.x, node.y))
    if len(pts) == 4:
        area = polygon_area(pts)
        parts.append(f"A = {fmt(area, 'length')} {lu}²" if lu
                     else f"A = {fmt(area, 'length')}")
    try:
        dofs = elem.get_dof_indices(project)
    except KeyError:
        dofs = []
    if dofs:
        shown = dofs[:8]
        txt = "GDL " + " ".join(str(d) for d in shown)
        if len(dofs) > 8:
            txt += f" … (+{len(dofs) - 8})"
        parts.append(f"{txt} → kₑ {elem.num_dof}×{elem.num_dof}")
    return (head, "  ·  ".join(parts))


def phase_hint(phase, *, draw_mode=False, has_elements=True):
    """Pista de gesto de la franja lectora cuando no hay nada bajo el cursor.
    Cada fase enseña el gesto que la hace avanzar."""
    if draw_mode:
        return ("Dibujando", "clic en el lienzo o sobre un nodo (snap) · "
                             "Enter confirma la coordenada · F8 ORTHO · Esc cancela")
    if phase == "proc":
        return ("Proceso", "cada elemento aporta su kₑ a K · clic en uno y "
                           "abrí ①…⑦ para ver cómo se construye")
    if phase == "post":
        return ("Post-Proceso", "cursor sobre el campo: consulta · clic: fijar "
                                "sonda · clic derecho: detalles y círculo de Mohr")
    if not has_elements:
        return ("Pre-Proceso", "tecla D dibuja elementos sobre el lienzo · "
                               "Ctrl+E carga un ejemplo")
    return ("Pre-Proceso", "clic: seleccionar · Ctrl+clic: sumar · "
                           "D: dibujar elemento · rueda: zoom · botón derecho: mover")


def nearest_node(xy, ids, wx, wy, tol):
    """Indice del nodo mas cercano a (wx, wy) dentro de `tol` (unidades del
    mundo) o None. `xy` es un array (n, 2) alineado con `ids`."""
    if xy is None or len(ids) == 0:
        return None
    d2 = (xy[:, 0] - wx) ** 2 + (xy[:, 1] - wy) ** 2
    k = int(np.argmin(d2))
    if d2[k] <= tol * tol:
        return ids[k]
    return None
