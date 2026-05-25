"""
latex_warmup: lista canonica de expresiones LaTeX precompiladas al boot
de EduFEM.

El warmup persiste las PNG en `~/.edufem/latex_cache/` (ver `config/latex_cache.py`).
Reabrir EduFEM con las mismas formulas = render instantaneo. Tipico:
~40 expresiones, ~25 s la primera vez en background, 0 s todas las
siguientes.

Para agregar formulas nuevas al warmup, simplemente extender la lista
`_CANONICAL`. El cache se segmenta por SHA256(body+dpi+color+bg), asi
que cambiar la paleta invalida solo los affected.
"""

from __future__ import annotations

from typing import Optional

from config.settings import (
    LATEX_DPI, LATEX_COLOR_FG, LATEX_COLOR_BG,
    OVERLAY_ACCENT_BLUE, OVERLAY_ACCENT_MUTED, OVERLAY_ACCENT_AMBER,
)


# Variantes de color (fg) que el warmup precompila para CADA expresion
# canonica. Los modulos M1..M7 usan estos colores para distintos roles:
#   - LATEX_COLOR_FG          → fórmulas principales
#   - OVERLAY_ACCENT_BLUE     → fórmulas secundarias (det J en M2, etc.)
#   - OVERLAY_ACCENT_MUTED    → hints / captions
#   - OVERLAY_ACCENT_AMBER    → bridge / cross-references
# Sin precompilar estos, cada uno seria un cold compile en cold path.
_FG_VARIANTS = (
    LATEX_COLOR_FG,
    OVERLAY_ACCENT_BLUE,
    OVERLAY_ACCENT_MUTED,
    OVERLAY_ACCENT_AMBER,
)


# ─── Biblioteca canonica de los modulos M0..M9 ──────────────────────────────
#
# Cada item es el cuerpo LaTeX en modo matematico (sin `$...$` envolvente —
# el preambulo standalone lo agrega). Agrupado por modulo para mantenibilidad.

_CANONICAL: list[str] = [
    # ── M1: Mapeo isoparametrico ────────────────────────────────────────
    r"x(\xi,\eta) = \sum_{i=1}^{n} N_i(\xi,\eta)\,x_i",
    r"y(\xi,\eta) = \sum_{i=1}^{n} N_i(\xi,\eta)\,y_i",
    r"N_i^{Q4} = \tfrac{1}{4}(1 + \xi_i\xi)(1 + \eta_i\eta)",
    r"N_i^{Q9} = \tfrac{1}{4}\xi\eta(\xi + \xi_i)(\eta + \eta_i)",

    # ── M2: Jacobiano ───────────────────────────────────────────────────
    r"\mathbf{J} = \begin{bmatrix} \partial x/\partial \xi & \partial y/\partial \xi \\ \partial x/\partial \eta & \partial y/\partial \eta \end{bmatrix}",
    r"\det \mathbf{J} = \tfrac{\partial x}{\partial \xi}\,\tfrac{\partial y}{\partial \eta} - \tfrac{\partial x}{\partial \eta}\,\tfrac{\partial y}{\partial \xi}",
    r"\det \mathbf{J} > 0",

    # ── M3: Matriz constitutiva D ───────────────────────────────────────
    # Tension Plana
    r"\mathbf{D}_{TP} = \dfrac{E}{1-\nu^2}\begin{bmatrix} 1 & \nu & 0 \\ \nu & 1 & 0 \\ 0 & 0 & \tfrac{1-\nu}{2} \end{bmatrix}",
    # Deformacion Plana
    r"\mathbf{D}_{DP} = \dfrac{E}{(1+\nu)(1-2\nu)}\begin{bmatrix} 1-\nu & \nu & 0 \\ \nu & 1-\nu & 0 \\ 0 & 0 & \tfrac{1-2\nu}{2} \end{bmatrix}",
    r"\nu \to 0.5 \Rightarrow \text{locking volumetrico (DP)}",

    # ── M4: Matriz B ────────────────────────────────────────────────────
    r"\boldsymbol{\varepsilon} = \mathbf{B}\,\mathbf{u}^e",
    r"\mathbf{B}_i = \begin{bmatrix} \partial N_i/\partial x & 0 \\ 0 & \partial N_i/\partial y \\ \partial N_i/\partial y & \partial N_i/\partial x \end{bmatrix}",
    r"\begin{bmatrix} \partial N_i/\partial x \\ \partial N_i/\partial y \end{bmatrix} = \mathbf{J}^{-1} \begin{bmatrix} \partial N_i/\partial \xi \\ \partial N_i/\partial \eta \end{bmatrix}",

    # ── M5: Matriz K_e (rigidez analitica) ──────────────────────────────
    r"\mathbf{k}_e = \int\!\!\int_{\Omega_e} \mathbf{B}^T \mathbf{D} \mathbf{B}\,|\!\det \mathbf{J}|\,t\,d\xi\,d\eta",
    r"k_{e}^{(i,j)} = \int\!\!\int \mathbf{B}_i^T \mathbf{D} \mathbf{B}_j\,|\det \mathbf{J}|\,t\,d\xi\,d\eta",
    r"\text{Imposible de resolver analiticamente para Q4/Q9 generales}",

    # ── M5b: Cuadratura de Gauss ────────────────────────────────────────
    r"\int_{-1}^{1}\!\!\int_{-1}^{1} f(\xi,\eta)\,d\xi\,d\eta \approx \sum_{i=1}^{n}\sum_{j=1}^{n} w_i\,w_j\,f(\xi_i,\eta_j)",
    r"\mathbf{k}_e \approx \sum_{p=1}^{n_g} w_p\,\mathbf{B}_p^T\,\mathbf{D}\,\mathbf{B}_p\,|\!\det \mathbf{J}_p|\,t",
    r"n_g = 2 \times 2 \quad (\text{Q4 exacto})",
    r"n_g = 3 \times 3 \quad (\text{Q9 exacto})",
    r"n_g = 1 \times 1 \Rightarrow \text{modos espurios (hourglass)}",

    # ── M6: Fuerzas equivalentes ────────────────────────────────────────
    r"\mathbf{f}_e = \int_{\Gamma_e} \mathbf{N}^T \mathbf{t}\,t\,ds + \int_{\Omega_e} \mathbf{N}^T \mathbf{b}\,t\,dA",
    r"F_1 = \tfrac{L}{6}(2 q_s + q_e), \quad F_2 = \tfrac{L}{6}(q_s + 2 q_e)",

    # ── M7: Ensamblaje ──────────────────────────────────────────────────
    r"\mathbf{K} = \bigwedge_{e=1}^{n_e} \mathbf{k}_e, \qquad \mathbf{F} = \bigwedge_{e=1}^{n_e} \mathbf{f}_e",
    r"\mathbf{K}\,\mathbf{u} = \mathbf{F}",

    # ── M9: Convergencia ────────────────────────────────────────────────
    r"\|u - u_h\|_{L^2} \le C\,h^{p+1}",
    r"|u - u_h|_{H^1} \le C\,h^p",

    # ── Post: tensiones y deformaciones ─────────────────────────────────
    r"\sigma_{vm} = \sqrt{\sigma_x^2 - \sigma_x\sigma_y + \sigma_y^2 + 3\tau_{xy}^2}",
    r"\sigma_{1,2} = \dfrac{\sigma_x + \sigma_y}{2} \pm \sqrt{\left(\dfrac{\sigma_x - \sigma_y}{2}\right)^2 + \tau_{xy}^2}",
    r"\theta_p = \tfrac{1}{2}\arctan\left(\dfrac{2\tau_{xy}}{\sigma_x - \sigma_y}\right)",
]


def canonical_expressions(
    *,
    color: Optional[str] = None,
    bg: Optional[str] = None,
    dpi: Optional[int] = None,
    all_color_variants: bool = True,
) -> list[tuple[str, dict]]:
    """Retorna `[(body, kwargs)]` listo para `latex_cache.warmup(...)`.

    Defaults vienen de `config.settings.LATEX_*` para garantizar que el
    warmup precompile con los mismos parametros que usaran los LatexBlock
    en runtime (mismo hash de cache).

    `all_color_variants=True` (default): precompila CADA expresion con
    las 4 variantes de fg del catalogo (`_FG_VARIANTS`). Multiplica la
    cantidad de compiles por 4 (~120 total) pero garantiza que los
    modulos que usan acentos no sufran cold compiles.
    Tamaño total estimado en disco: ~600 KB (5 KB × 120).
    """
    eff_bg = bg if bg is not None else LATEX_COLOR_BG
    eff_dpi = dpi if dpi is not None else LATEX_DPI

    if not all_color_variants:
        eff_color = color if color is not None else LATEX_COLOR_FG
        kwargs = {"dpi": eff_dpi, "color": eff_color, "bg": eff_bg}
        return [(body, kwargs) for body in _CANONICAL]

    # Variantes para cada expresion x cada color del catalogo.
    out: list[tuple[str, dict]] = []
    colors = (color,) if color is not None else _FG_VARIANTS
    for body in _CANONICAL:
        for c in colors:
            out.append((body, {"dpi": eff_dpi, "color": c, "bg": eff_bg}))
    return out
