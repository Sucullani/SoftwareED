"""
Glifo unificado para puntos Gauss en los módulos educativos.

Antes cada módulo (M2, M4, M5b) dibujaba sus puntos Gauss con geometría,
colores, tamaños y fuentes distintos — el alumno no reconocía que
"el punto Gauss aquí" y "el punto Gauss allá" son la MISMA entidad
matemática. Ahora todos comparten:

    - Misma geometría base (radios, offsets de label, fuente).
    - Misma paleta semántica.
    - Mismo lenguaje de superposición (halo de selección, anillo dashed
      para "disponible no usado", etc.).

Cada módulo aporta SU semántica propia encima del glifo base:

    M2:  cada PG se PINTA por valor del campo (det J) — la decisión
         pedagógica es "lo importante es el valor, no la posición".
    M4:  glifo base + ripple animado (energía de muestreo) +
         halo si el alumno snapeó este PG.
    M5b: glifo dorado si el PG suma a k_e; ghost gris dashed si está
         disponible pero excluido por la cuadratura activa.

La paleta sigue la convención global del proyecto:

    cian  (#80deea) — PG neutral (color canónico de Gauss en el proyecto)
    dorado(#ffd54f) — PG activo / sumado en cuadratura
    naranja(#ff8a65) — selección explícita del alumno (snap)
    gris  (#7a7a85) — PG disponible pero no usado
"""

from __future__ import annotations

from typing import Optional

from config.settings import (
    CANVAS_BG_COLOR,
    GAUSS_CANONICAL_COLOR, GAUSS_ACTIVE_COLOR, GAUSS_HALO_COLOR,
    GAUSS_GHOST_COLOR, GAUSS_LABEL_OUTLINE_COLOR,
    EDU_FREE_POINT_COLOR, EDU_MARKER_OUTLINE_COLOR,
)


# ─── Geometría compartida ────────────────────────────────────────────
GAUSS_R_INNER = 4.0      # radio del disco interior
GAUSS_R_OUTER = 9.0      # radio del anillo base
GAUSS_R_SELECT_EXTRA = 5.0  # halo de selección: r_outer + extra
GAUSS_LABEL_DX = 11
GAUSS_LABEL_DY = -11
GAUSS_LABEL_FONT = ("Consolas", 8, "bold")

# ─── Paleta canónica (re-export desde config/settings.py) ────────────
# Las constantes viven en settings (regla: cero hex fuera de config/). Acá
# se re-exportan con los nombres cortos históricos para no romper los ~6
# módulos que hacen `from ...gauss_glyph import GAUSS_CANONICAL`.
GAUSS_CANONICAL     = GAUSS_CANONICAL_COLOR      # cian — PG neutral
GAUSS_ACTIVE        = GAUSS_ACTIVE_COLOR         # dorado — sumado / activo
GAUSS_HALO          = GAUSS_HALO_COLOR           # naranja — selección del alumno
GAUSS_GHOST         = GAUSS_GHOST_COLOR          # gris — disponible no usado
GAUSS_LABEL_OUTLINE = GAUSS_LABEL_OUTLINE_COLOR  # outline sutil del disco filled


# ─── Animación: parámetros del ripple compartido ─────────────────────
# Dos intensidades para que el ripple sea reusable en distintos contextos
# sin saturar visualmente cuando hay múltiples PGs animados:
#
#   "strong"  — M4: ripple SOBRE TODOS los PGs (el módulo está dedicado
#               a B y sus PGs). 2 anillos, r_max amplio.
#   "subtle"  — M2/M5b: ripple solo sobre EL PG ACTIVO (seleccionado o
#               sumado) para llamar la atención sin contaminar el resto
#               de la lectura del canvas. 1 anillo, r_max acotado.
RIPPLE_R_MIN          = 8.0
RIPPLE_R_MAX_STRONG   = 22.0
RIPPLE_R_MAX_SUBTLE   = 15.0
RIPPLE_RINGS_STRONG   = 2
RIPPLE_RINGS_SUBTLE   = 1


# ═══════════════════════════════════════════════════════════════════
# DIBUJADORES PRIMITIVOS
# ═══════════════════════════════════════════════════════════════════

def draw_gauss_base(canvas, sx: float, sy: float, label: Optional[str], *,
                     tag: str, color: str = GAUSS_CANONICAL,
                     ring_width: float = 1.6) -> None:
    """Glifo BASE: disco interior pequeño + anillo + etiqueta.

    Es el aspecto canónico del PG. Otros helpers SUPERPONEN sobre éste
    (halo de selección, ripple, etc.) — no lo reemplazan.
    """
    canvas.create_oval(
        sx - GAUSS_R_OUTER, sy - GAUSS_R_OUTER,
        sx + GAUSS_R_OUTER, sy + GAUSS_R_OUTER,
        outline=color, width=ring_width, tags=tag,
    )
    canvas.create_oval(
        sx - GAUSS_R_INNER, sy - GAUSS_R_INNER,
        sx + GAUSS_R_INNER, sy + GAUSS_R_INNER,
        fill=color, outline="", tags=tag,
    )
    if label:
        canvas.create_text(
            sx + GAUSS_LABEL_DX, sy + GAUSS_LABEL_DY,
            text=label, fill=color, font=GAUSS_LABEL_FONT, tags=tag,
        )


def draw_gauss_filled_by_value(canvas, sx: float, sy: float,
                                label: Optional[str], *, tag: str,
                                color: str) -> None:
    """Variante usada por M2: disco filled completo (la posición del PG
    queda secundaria, el COLOR ES la información). El label suele ser el
    valor numérico del campo, no `pgN`.
    """
    canvas.create_oval(
        sx - GAUSS_R_OUTER, sy - GAUSS_R_OUTER,
        sx + GAUSS_R_OUTER, sy + GAUSS_R_OUTER,
        fill=color, outline=GAUSS_LABEL_OUTLINE, width=1.2, tags=tag,
    )
    if label:
        canvas.create_text(
            sx + GAUSS_LABEL_DX, sy + GAUSS_LABEL_DY,
            text=label, fill=color, font=GAUSS_LABEL_FONT, tags=tag,
        )


def draw_gauss_ghost(canvas, sx: float, sy: float, *, tag: str,
                      color: str = GAUSS_GHOST) -> None:
    """Variante "disponible pero no usado" (M5b unselected): anillo
    dashed + disco interior muy pequeño y opaco. Invita visualmente a
    clickearlo sin pretender ser el foco."""
    canvas.create_oval(
        sx - GAUSS_R_OUTER, sy - GAUSS_R_OUTER,
        sx + GAUSS_R_OUTER, sy + GAUSS_R_OUTER,
        outline=color, width=1.4, dash=(3, 3), tags=tag,
    )
    canvas.create_oval(
        sx - 2.5, sy - 2.5, sx + 2.5, sy + 2.5,
        fill=color, outline="", tags=tag,
    )


def draw_gauss_halo(canvas, sx: float, sy: float, *, tag: str,
                     color: str = GAUSS_HALO,
                     extra: float = GAUSS_R_SELECT_EXTRA,
                     width: float = 2.4,
                     dash: Optional[tuple] = None) -> None:
    """Halo de selección. Se DIBUJA SOBRE un glifo base ya existente.

    Pasar `dash=(4, 3)` para variante "punto libre" (no-Gauss exacto).
    """
    r = GAUSS_R_OUTER + extra
    kwargs = {"outline": color, "width": width, "tags": tag}
    if dash is not None:
        kwargs["dash"] = dash
    canvas.create_oval(sx - r, sy - r, sx + r, sy + r, **kwargs)


def draw_gauss_free_point(canvas, sx: float, sy: float, *, tag: str,
                           color: Optional[str] = None,
                           label: Optional[str] = None) -> None:
    """Marcador de PUNTO LIBRE (no-Gauss): halo dashed + disco interior con
    outline blanco para legibilidad sobre cualquier fondo.

    Encapsula el patrón que antes estaba duplicado a mano en M1/M2/M4 (dos
    `create_oval` + el literal `#d68a7a` repetido). Un único helper, color
    desde `config.settings.EDU_FREE_POINT_COLOR` (default si `color=None`).
    """
    if color is None:
        color = EDU_FREE_POINT_COLOR
    canvas.create_oval(sx - 11, sy - 11, sx + 11, sy + 11,
                       outline=color, width=2.0, dash=(4, 3), tags=tag)
    canvas.create_oval(sx - 4, sy - 4, sx + 4, sy + 4,
                       fill=color, outline=EDU_MARKER_OUTLINE_COLOR,
                       width=1.0, tags=tag)
    if label:
        canvas.create_text(sx + GAUSS_LABEL_DX, sy + GAUSS_LABEL_DY,
                           text=label, fill=color,
                           font=GAUSS_LABEL_FONT, tags=tag)


def draw_gauss_ripple(canvas, sx: float, sy: float, *, tag: str,
                       phase: float, color_fg: str = GAUSS_CANONICAL,
                       color_bg: str = CANVAS_BG_COLOR,
                       intensity: str = "strong") -> None:
    """Ripple animado: N anillos concéntricos emanando del PG con fade
    radial (color interpolado fg → bg conforme se expanden).

    `phase` ∈ [0, 1) avanza con el loop del módulo (~30 fps típico).
    Cada anillo está phase-offset por 1/n_rings para flujo continuo.

    `intensity`:
        "strong" — M4: 2 anillos, r_max amplio. Sobre todos los PGs.
        "subtle" — M2/M5b: 1 anillo, r_max acotado. Sólo en el PG activo.

    Tkinter no soporta alpha real — el "fade" se logra interpolando el
    color de outline hacia el bg del canvas, que da la sensación visual
    equivalente sobre fondos oscuros homogéneos.
    """
    if intensity == "subtle":
        n_rings = RIPPLE_RINGS_SUBTLE
        r_max = RIPPLE_R_MAX_SUBTLE
    else:
        n_rings = RIPPLE_RINGS_STRONG
        r_max = RIPPLE_R_MAX_STRONG
    r_min = RIPPLE_R_MIN
    for k in range(n_rings):
        t = (phase + k / float(n_rings)) % 1.0
        r = r_min + (r_max - r_min) * t
        col = lerp_hex(color_fg, color_bg, t)
        w = max(0.6, 2.0 * (1.0 - t))
        canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r,
            outline=col, width=w, tags=tag,
        )


# ═══════════════════════════════════════════════════════════════════
# HELPERS DE COLOR (públicos — fuente única de la interpolación HEX)
# ═══════════════════════════════════════════════════════════════════

def hex_to_rgb(h: str) -> tuple:
    """`#rrggbb` -> (r, g, b) enteros 0..255."""
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def lerp_hex(c1: str, c2: str, t: float) -> str:
    """Interpolación lineal entre dos colores HEX `#rrggbb`.

    Fuente ÚNICA de la rgb-lerp del proyecto educativo. Antes estaba
    triplicada (este helper privado + mod02._lerp_color + quality_bar._lerp).
    """
    t = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# Alias retrocompat por si algún módulo importó el nombre privado.
_lerp_hex = lerp_hex
