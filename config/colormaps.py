"""Colormaps perceptualmente uniformes para el canvas FEM (numpy puro).

Auditoria UX 2026-05 (docs/auditorias/historico/2026-05-30_auditoria_canvas_ux.md, hallazgo R1): el canvas
interactivo usaba JET inline en el kernel de rasterizado. JET no es
perceptualmente uniforme — crea bandas falsas (el amarillo aparenta un
maximo donde no lo hay), problema documentado en visualizacion cientifica,
y ademas violaba la regla #3 de la paleta congelada (`config/settings.py`:
"Mapas matplotlib: viridis o coolwarm. No jet/hsv"). Este modulo provee los
mismos mapas que ya usa la Memoria de Calculo (`file_io/figure_export.py`),
pero construidos en numpy puro desde puntos de anclaje hardcodeados — SIN
depender de matplotlib (el instalador PyInstaller y los tests headless no
siempre lo tienen disponible en el hot path del canvas).

Convencion de uso en el canvas (unificada en TODOS los renders de resultado:
canvas 2D, Vista 3D, mini-paneles M9, Memoria de Calculo):
  - jet      -> magnitudes NO negativas (von Mises, |desplazamiento|). Arcoiris
    clasico de los software FEM (ANSYS / SAP2000): azul -> cyan -> verde ->
    amarillo -> rojo. El usuario lo pidio explicitamente (2026-05-31) por el look
    reconocible de ingenieria estructural, sobrescribiendo la regla "no jet" de
    la paleta congelada (jet no es perceptualmente uniforme, pero el usuario
    prioriza el look clasico). Reemplazo a turbo, que habia reemplazado a viridis.
  - coolwarm -> magnitudes con SIGNO (sigma_x, sigma_y, tau_xy); el caller
    centra vmin/vmax simetricamente para que el cero fisico caiga en 0.5. El
    azul/rojo separa compresion de traccion (el cero queda neutro = blanco).
  - turbo / viridis -> conservados (turbo arcoiris perceptual, viridis para
    superficies pedagogicas de modulos educativos); ya NO son la paleta de los
    campos de resultado.

Los LUT son ndarray (256, 3) uint8 — indexables directo por `int(t*255)` en
el rasterizador vectorizado (mas rapido que el branching de JET) y convertibles a hex
para los items vectoriales (colorbar, fallback de poligonos sin PIL).
"""

from __future__ import annotations

import numpy as np

# Puntos de anclaje (posicion en [0,1] -> RGB en [0,1]). Muestreados de los
# mapas matplotlib del mismo nombre. Resolucion suficiente: el LUT final
# interpola linealmente a 256 niveles, indistinguible del original al ojo.
_VIRIDIS_ANCHORS = [
    (0.00, (0.267004, 0.004874, 0.329415)),
    (0.10, (0.282623, 0.140926, 0.457517)),
    (0.20, (0.253935, 0.265254, 0.529983)),
    (0.30, (0.206756, 0.371758, 0.553117)),
    (0.40, (0.163625, 0.471133, 0.558148)),
    (0.50, (0.127568, 0.566949, 0.550556)),
    (0.60, (0.134692, 0.658636, 0.517649)),
    (0.70, (0.266941, 0.748751, 0.440573)),
    (0.80, (0.477504, 0.821444, 0.318195)),
    (0.90, (0.741388, 0.873449, 0.149561)),
    (1.00, (0.993248, 0.906157, 0.143936)),
]

_COOLWARM_ANCHORS = [
    (0.00, (0.229800, 0.298700, 0.753700)),
    (0.25, (0.533300, 0.694100, 0.984300)),
    (0.50, (0.865400, 0.865400, 0.865400)),
    (0.75, (0.958200, 0.554600, 0.479100)),
    (1.00, (0.705700, 0.015600, 0.150200)),
]

# Turbo (Google AI, Mikhailov 2019): arcoiris PERCEPTUALMENTE UNIFORME. Es el
# reemplazo correcto de Jet — conserva el "look arcoiris" clasico de los
# software FEM (azul -> cyan -> verde -> amarillo -> naranja -> rojo) pero SIN
# los falsos contornos de Jet (la luminosidad crece monotona). Reemplaza a
# viridis para magnitudes no negativas (von Mises, |u|) en TODOS los renders de
# resultado del proyecto (canvas, Vista 3D, mini-paneles M9, Memoria de
# Calculo). coolwarm se mantiene para campos con signo. Muestreado de la tabla
# srgb oficial de Turbo.
_TURBO_ANCHORS = [
    (0.00, (0.18995, 0.07176, 0.23217)),
    (0.08, (0.27100, 0.24300, 0.62400)),
    (0.16, (0.25500, 0.43500, 0.87500)),
    (0.24, (0.18000, 0.62000, 0.97300)),
    (0.32, (0.09800, 0.77600, 0.87500)),
    (0.40, (0.09400, 0.90200, 0.67800)),
    (0.48, (0.21600, 0.96500, 0.44300)),
    (0.56, (0.45900, 0.98400, 0.22700)),
    (0.64, (0.71000, 0.95300, 0.20000)),
    (0.72, (0.89400, 0.83500, 0.22700)),
    (0.80, (0.98000, 0.67800, 0.16900)),
    (0.88, (0.96900, 0.45500, 0.09000)),
    (0.96, (0.87100, 0.22700, 0.04700)),
    (1.00, (0.47800, 0.01600, 0.01200)),
]

# Jet (arcoiris clasico de los software FEM — ANSYS / SAP2000). El usuario lo
# pidio explicitamente ("jet/arcoiris similar a Ansys o sap2000", 2026-05-31)
# como paleta de los campos de resultado no negativos: es el look reconocible
# azul -> cyan -> verde -> amarillo -> rojo. Reemplaza a turbo (que reemplazo a
# viridis) para los resultados. NOTA: jet NO es perceptualmente uniforme (la
# regla #3 de la paleta congelada lo desaconsejaba), pero el usuario sobrescribe
# esa regla a favor del look clasico de ingenieria estructural. Definicion
# clasica de matplotlib jet.
_JET_ANCHORS = [
    (0.0000, (0.0,    0.0,   0.5)),
    (0.0833, (0.0,    0.0,   0.878)),
    (0.1667, (0.0,    0.165, 1.0)),
    (0.2500, (0.0,    0.5,   1.0)),
    (0.3333, (0.0,    0.833, 1.0)),
    (0.4167, (0.215,  1.0,   0.753)),
    (0.5000, (0.484,  1.0,   0.484)),
    (0.5833, (0.753,  1.0,   0.215)),
    (0.6667, (1.0,    0.901, 0.0)),
    (0.7500, (1.0,    0.593, 0.0)),
    (0.8333, (1.0,    0.284, 0.0)),
    (0.9167, (0.879,  0.0,   0.0)),
    (1.0000, (0.5,    0.0,   0.0)),
]


def _build_lut(anchors) -> np.ndarray:
    """Construye un LUT (256, 3) uint8 interpolando linealmente los anclajes."""
    pos = np.array([p for p, _ in anchors], dtype=float)
    rgb = np.array([c for _, c in anchors], dtype=float)  # (k, 3)
    ts = np.linspace(0.0, 1.0, 256)
    lut = np.empty((256, 3), dtype=np.uint8)
    for ch in range(3):
        vals = np.interp(ts, pos, rgb[:, ch])
        lut[:, ch] = np.clip(np.round(vals * 255.0), 0, 255).astype(np.uint8)
    return lut


# LUT cacheados a nivel de modulo (se construyen una sola vez al importar).
VIRIDIS_LUT = _build_lut(_VIRIDIS_ANCHORS)
COOLWARM_LUT = _build_lut(_COOLWARM_ANCHORS)
TURBO_LUT = _build_lut(_TURBO_ANCHORS)
JET_LUT = _build_lut(_JET_ANCHORS)


def normalized_t(value, vmin, vmax) -> float:
    """Normaliza `value` a [0, 1] dado el rango [vmin, vmax] (clamp)."""
    if vmax is None or vmin is None or vmax == vmin:
        return 0.5
    t = (value - vmin) / (vmax - vmin)
    if t < 0.0:
        return 0.0
    if t > 1.0:
        return 1.0
    return t


def t_to_rgb(t, lut) -> tuple:
    """t en [0,1] -> (r, g, b) enteros 0..255 leidos del LUT."""
    idx = int(t * 255.0)
    if idx < 0:
        idx = 0
    elif idx > 255:
        idx = 255
    r, g, b = lut[idx]
    return int(r), int(g), int(b)


def t_to_hex(t, lut) -> str:
    """t en [0,1] -> string hex `#rrggbb` leido del LUT."""
    r, g, b = t_to_rgb(t, lut)
    return f"#{r:02x}{g:02x}{b:02x}"


def value_to_hex(value, vmin, vmax, lut) -> str:
    """Mapea un valor escalar a color hex via el LUT dado."""
    return t_to_hex(normalized_t(value, vmin, vmax), lut)


def is_diverging_range(vmin, vmax, rel=1e-6) -> bool:
    """True si el rango cruza el cero de forma significativa (justifica un mapa
    divergente centrado).

    Umbral RELATIVO a la magnitud del rango (`rel`): un campo no negativo con
    ruido numerico minusculo del lado negativo (p.ej. von Mises extrapolada =
    -1e-9) NO se clasifica como divergente — seguiria en viridis secuencial.
    Solo cuando ambos lados son una fraccion real del rango se considera con
    signo (sigma_x/sigma_y/tau_xy, Ux/Uy).
    """
    if vmin is None or vmax is None:
        return False
    m = max(abs(vmin), abs(vmax))
    if m <= 0.0:
        return False
    thr = rel * m
    return vmin < -thr and vmax > thr


def symmetric_bounds(vmin, vmax) -> tuple:
    """Devuelve (-M, +M) con M = max(|vmin|, |vmax|) para centrar el cero en
    el medio de un mapa divergente. Si el rango es degenerado, devuelve el
    original."""
    if vmin is None or vmax is None:
        return vmin, vmax
    m = max(abs(vmin), abs(vmax))
    if m <= 0.0:
        return vmin, vmax
    return -m, m
