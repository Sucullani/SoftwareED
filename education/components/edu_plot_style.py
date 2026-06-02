"""edu_plot_style — estilo unificado para gráficos matplotlib embebidos
en overlays educativos.

Objetivo: reducir el ruido visual. Antes del refactor, cada módulo
elegía su propio color de tick (`#dcdcdc`, `#dfdfdf`), su propio
linewidth (1.6, 2.0), su propio facecolor del axes (`EDU_AXES_BG`
distinto al overlay → rectángulo visible) — el resultado se sentía
"animado" en vez de profesional.

Reglas:
    - Fondo del axes = fondo del overlay (`OVERLAY_BG`): la figura
      "desaparece" en el overlay, no hay rectángulo visible.
    - Ticks finos y mutados (gris medio, sin gritar).
    - Spines invisibles por default (cleaner). Activables con
      `show_spines=True` si la chart los necesita semánticamente.
    - Grid sutil (alpha bajo, linewidth chico) cuando es necesario.

API:
    apply_edu_style_figure(fig)
    apply_edu_style_2d(ax, *, show_spines=False, grid=False)
    apply_edu_style_3d(ax)
"""

from __future__ import annotations

from config.settings import (
    OVERLAY_BG, EDU_AXES_BG, EDU_FIG_BG, EDU_GRID, EDU_FG, HEALTH_INFO_COLOR,
    EDU_PLOT_TICK_COLOR, EDU_PLOT_LABEL_COLOR, EDU_PLOT_AXIS_COLOR,
    EDU_PLOT_TITLE_COLOR,
)


# Paleta del tema oscuro para Figures matplotlib embebidas en diálogos
# (element_type / analysis_type). Migrado desde el ex-plot_panel.py (cuya
# clase PlotPanel quedó muerta tras el rediseño UX 2026); el helper
# `_theme_colors` seguía vivo en esos dos diálogos, así que vive acá ahora.
_DARK_THEME = {
    "bg":     EDU_AXES_BG,
    "fg":     EDU_FG,
    "grid":   EDU_GRID,
    "panel":  EDU_FIG_BG,
    "accent": HEALTH_INFO_COLOR,
}


def _theme_colors() -> dict:
    """Copia de la paleta oscura para Figures matplotlib en diálogos."""
    return dict(_DARK_THEME)


# Paleta neutra para el chrome de los plots edu. Los colores de los
# DATOS los elige cada módulo (semantica) — esto es solo el marco.
# (Los hex viven en config/settings.py; se importan arriba.)

EDU_PLOT_TICK_LABELSIZE = 7
EDU_PLOT_AXIS_LABELSIZE = 9
EDU_PLOT_TITLE_FONTSIZE = 9


def apply_edu_style_figure(fig) -> None:
    """Fondo de la `Figure` matplotlib = `OVERLAY_BG`. Sin rectángulo
    visible alrededor del axes (la figura se funde con el overlay)."""
    try:
        fig.patch.set_facecolor(OVERLAY_BG)
    except Exception:
        pass


def apply_edu_style_2d(ax, *, show_spines: bool = False,
                        grid: bool = False) -> None:
    """Estilo edu para axes 2D estándar."""
    try:
        ax.set_facecolor(OVERLAY_BG)
        ax.tick_params(
            colors=EDU_PLOT_TICK_COLOR,
            labelsize=EDU_PLOT_TICK_LABELSIZE,
            width=0.6, length=3, pad=2,
        )
        if show_spines:
            for spine in ax.spines.values():
                spine.set_color(EDU_PLOT_AXIS_COLOR)
                spine.set_linewidth(0.6)
        else:
            for spine in ax.spines.values():
                spine.set_visible(False)
        if grid:
            ax.grid(True, color=EDU_PLOT_AXIS_COLOR,
                    linewidth=0.4, alpha=0.6)
        # Labels de ejes mutados.
        try:
            ax.xaxis.label.set_color(EDU_PLOT_LABEL_COLOR)
            ax.xaxis.label.set_fontsize(EDU_PLOT_AXIS_LABELSIZE)
            ax.yaxis.label.set_color(EDU_PLOT_LABEL_COLOR)
            ax.yaxis.label.set_fontsize(EDU_PLOT_AXIS_LABELSIZE)
        except Exception:
            pass
    except Exception:
        pass


def apply_edu_style_3d(ax) -> None:
    """Estilo edu para axes 3D: panes transparentes, líneas finas,
    ticks mutados. Hace que la superficie 3D 'flote' sobre el overlay
    sin marco visible."""
    try:
        ax.set_facecolor(OVERLAY_BG)
        ax.tick_params(
            colors=EDU_PLOT_TICK_COLOR,
            labelsize=EDU_PLOT_TICK_LABELSIZE,
        )
        try:
            ax.tick_params(axis="z",
                            colors=EDU_PLOT_TICK_COLOR,
                            labelsize=EDU_PLOT_TICK_LABELSIZE)
        except Exception:
            pass
        # Panes (fondos de cada plano X-Y, X-Z, Y-Z): transparentes para
        # que el OVERLAY_BG se vea directo (no un rectangulo gris).
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            try:
                axis.set_pane_color((0, 0, 0, 0))
                axis.line.set_color(EDU_PLOT_AXIS_COLOR)
                axis.line.set_linewidth(0.6)
                axis.label.set_color(EDU_PLOT_LABEL_COLOR)
                axis.label.set_fontsize(EDU_PLOT_AXIS_LABELSIZE)
            except Exception:
                pass
        # Grid 3D fino y sutil.
        try:
            ax.xaxis._axinfo["grid"].update({
                "color": EDU_PLOT_AXIS_COLOR, "linewidth": 0.3,
            })
            ax.yaxis._axinfo["grid"].update({
                "color": EDU_PLOT_AXIS_COLOR, "linewidth": 0.3,
            })
            ax.zaxis._axinfo["grid"].update({
                "color": EDU_PLOT_AXIS_COLOR, "linewidth": 0.3,
            })
        except Exception:
            pass
    except Exception:
        pass
