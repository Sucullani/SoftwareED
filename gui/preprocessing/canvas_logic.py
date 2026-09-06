"""Logica pura del MeshCanvas (sin Tk) — testeable headless.

Auditoria UX 2026-05 (docs/auditorias/historico/2026-05-30_auditoria_canvas_ux.md): el canvas no decidia
*cuanto* dibujar segun la escala. Aqui viven las decisiones puras de
visibilidad progresiva (LOD por zoom) y de culling por viewport, separadas
del widget Tk para poder testearlas sin display.

Ninguna funcion de este modulo importa tkinter — solo aritmetica + numpy +
constantes de config. El `MeshCanvas` las consume.
"""

from __future__ import annotations

from config.settings import (
    LOD_EDGE_PX_FAR, LOD_EDGE_PX_NEAR, LOD_MIN_ELEMENTS_FOR_GATING,
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
