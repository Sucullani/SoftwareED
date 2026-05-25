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

from config.settings import CANVAS_BG_COLOR


# ─── Geometría compartida ────────────────────────────────────────────
GAUSS_R_INNER = 4.0      # radio del disco interior
GAUSS_R_OUTER = 9.0      # radio del anillo base
GAUSS_R_SELECT_EXTRA = 5.0  # halo de selección: r_outer + extra
GAUSS_LABEL_DX = 11
GAUSS_LABEL_DY = -11
GAUSS_LABEL_FONT = ("Consolas", 8, "bold")

# ─── Paleta canónica ────────────────────────────────────────────────
GAUSS_CANONICAL = "#80deea"      # cian — PG neutral
GAUSS_ACTIVE    = "#ffd54f"      # dorado — sumado / activo
GAUSS_HALO      = "#ff8a65"      # naranja — selección del alumno
GAUSS_GHOST     = "#7a7a85"      # gris — disponible no usado
GAUSS_LABEL_OUTLINE = "#1f1f29"  # outline sutil del disco filled


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
        col = _lerp_hex(color_fg, color_bg, t)
        w = max(0.6, 2.0 * (1.0 - t))
        canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r,
            outline=col, width=w, tags=tag,
        )


# ═══════════════════════════════════════════════════════════════════
# HELPERS INTERNOS
# ═══════════════════════════════════════════════════════════════════

def _lerp_hex(c1: str, c2: str, t: float) -> str:
    """Interpolación lineal entre dos colores HEX `#rrggbb`."""
    t = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"
