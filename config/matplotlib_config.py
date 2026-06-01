"""
matplotlib_config: configura rcParams al boot para que mathtext use
las fuentes Computer Modern bundleadas con matplotlib.

Motivacion:
    Antes del refactor 2026-05, EduFEM compilaba formulas LaTeX via
    pdflatex (MiKTeX) + cache PNG en disco. Esto producia tipografia
    de calidad documento pero introducia:
        - Dependencia MiKTeX (~200 MB) para el usuario
        - Lag de 2-3s por cold compile
        - Asset CMU Serif TTF para overlays parametric
        - Complejidad de async swap + cache disco + warmup background

    matplotlib ya trae Computer Modern bundleado en su `mpl-data/fonts/ttf/`:
        cmb10.ttf, cmex10.ttf, cmmi10.ttf, cmr10.ttf, cmss10.ttf,
        cmsy10.ttf, cmtt10.ttf — son las MISMAS fuentes que usa LaTeX.
    Tambien trae STIX (publication-grade serif math).

    Configurando `mathtext.fontset = "cm"`, el render mathtext produce
    tipografia visualmente equivalente a pdflatex (~30-100 ms por
    expresion, sincrono, sin cache disco). El unico subset NO soportado
    es `\\begin{bmatrix}` (sustituido por render manual con corchetes
    en `latex_image.render_matrix_image`).

API:
    configure_latex_style()  # llamar UNA vez al boot, antes de crear widgets

Despues de eso, cualquier `ax.text(..., r"$\\dfrac{a}{b}$")` o
`Figure(...)` saldra con Computer Modern automaticamente.
"""

from __future__ import annotations

import matplotlib


_CONFIGURED = False


def configure_latex_style() -> None:
    """Configura matplotlib para que mathtext y serif font usen Computer
    Modern (bundled en matplotlib, no requiere instalacion externa).

    Idempotente: llamadas repetidas no hacen nada.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    # Forzar backend Agg para los renders offscreen (tk-friendly).
    # Solo si no esta seteado ya (otros modulos pueden haberlo hecho).
    if matplotlib.get_backend().lower() not in ("agg", "tkagg"):
        matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    # Mathtext fontset: "cm" usa Computer Modern (LaTeX classic). "stix"
    # tambien es opcion buena (publication-grade, mas moderna). "cm" es
    # mas reconocible para un alumno acostumbrado a libros academicos.
    plt.rcParams["mathtext.fontset"] = "cm"

    # Fuente serif del texto plano (no math). Las strings de la matriz
    # se renderizan con `family="serif"` y heredan esta lista. Computer
    # Modern Serif (cmr10) viene bundled; STIX Two y DejaVu Serif son
    # fallbacks razonables si CM no esta instalada como fuente sistema.
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = [
        "CMU Serif",          # si el usuario lo tiene instalado, mejor
        "STIX Two Text",      # fallback bundled (publication-grade)
        "DejaVu Serif",       # default matplotlib
        "Times New Roman",    # ultimo recurso en Windows
        "serif",
    ]

    # Mathtext rm/it/bf usan la misma familia (cm fontset ya lo hace,
    # pero por defensiva forzamos por si el fontset cambia).
    plt.rcParams["mathtext.rm"] = "serif"
    plt.rcParams["mathtext.it"] = "serif:italic"
    plt.rcParams["mathtext.bf"] = "serif:bold"

    # Default text color para axes (los modulos ya overrideanlo por edu,
    # esto es defensiva para texts sueltos).
    plt.rcParams["text.color"] = "#e8e8ea"

    _CONFIGURED = True


# Expresiones canonicas precompiladas. Cubre los tokens de los modulos
# educativos para que el primer render real sea cache-hit. El parser
# mathtext cachea por string EXACTO (no por token), asi que el warmup
# debe incluir las strings reales que los modulos pasaran. Cubre los
# building-blocks de M2 (Jacobiano), M3 (D), M4 (B), M5 (k_e), M6
# (fuerzas), M7 (ensamblaje) y el Post.
MATHTEXT_WARMUP_EXPRESSIONS = [
    # M2: Jacobiano (celdas + det J)
    r"$\partial x/\partial \xi$",
    r"$\partial y/\partial \xi$",
    r"$\partial x/\partial \eta$",
    r"$\partial y/\partial \eta$",
    r"$\mathbf{J}=$",
    r"$\det\mathbf{J}$",
    r"$\dfrac{\partial x}{\partial \xi}$",
    r"$\dfrac{\partial y}{\partial \eta}$",
    # M3: matriz D
    r"$\nu$", r"$\nu = 0.200$",
    r"$\dfrac{E}{1-\nu^2}$",
    r"$\mathbf{D}=$",
    # M4: matriz B
    r"$\mathbf{B}=$", r"$\mathbf{B}_i$",
    r"$\partial N_i/\partial \xi$",
    r"$\partial N_i/\partial \eta$",
    r"$\sum_i$",
    # M5: rigidez
    r"$\mathbf{k}_e$", r"$|\det\mathbf{J}|$",
    r"$\int\!\!\int$",
    # Post: tensiones
    r"$\sigma_{vm}$", r"$\sigma_x$", r"$\sigma_y$", r"$\tau_{xy}$",
    r"$\sqrt{3}$", r"$-1/\sqrt{3}$", r"$+1/\sqrt{3}$",
    r"$\sqrt{\sigma_x^2 + 3\tau_{xy}^2}$",
    r"$(\xi, \eta)$", r"$(x, y)$", r"$\to$",
    # Numericos comunes
    r"$+1.000$", r"$-0.577$", r"$+0.577$",
]


def warmup_mathtext_chunk(expressions) -> None:
    """Calienta el cache del parser mathtext para un subconjunto de
    expresiones, usando la API orientada a objetos de matplotlib
    (`matplotlib.figure.Figure` + canvas Agg, SIN pyplot).

    Diseñado para correr troceado en el HILO PRINCIPAL via `after_idle`
    (2-3 expresiones por tick): evita el cruce de hilos del antiguo warmup
    en daemon thread (pyplot/fontmanager no son thread-safe respecto al
    main loop de Tk).

    Idempotente y defensivo: cualquier fallo de render se ignora.
    """
    if not expressions:
        return
    try:
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        configure_latex_style()

        fig = Figure(figsize=(0.01, 0.01), dpi=140)
        FigureCanvasAgg(fig)  # asocia un canvas Agg para forzar el draw
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        for expr in expressions:
            try:
                ax.text(0, 0, expr, fontsize=12, family="serif")
            except Exception:
                pass
        try:
            fig.canvas.draw()  # fuerza el parse mathtext + font cache
        except Exception:
            pass
    except Exception:
        pass
