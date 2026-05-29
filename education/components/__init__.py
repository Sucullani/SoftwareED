"""Componentes reutilizables para los módulos educativos.

Limpieza 2026-05: se eliminaron los componentes muertos (sin instanciaciones
reales fuera de este paquete) que sobrevivían a rediseños previos —
`LatexMath`, `ParamInput`, `PlotPanel`/`FourPanel`, `StepAnimator`,
`render_matrix_latex`/`render_expression_latex` (latex_figure),
`FormulaValueToggle`, `LatexBlock`/`make_variable_block`. Sus reemplazos
vivos son `LatexExpressionImage`/`LatexMatrixImage`/`ScrollableMatrixImage`
(latex_image) y `FormulaValueBlocksToggle` (formula_value_blocks). El helper
`_theme_colors` (ex-plot_panel) se movió a `edu_plot_style`.
"""

from .latex_image import (
    LatexMatrixImage, LatexExpressionImage, ScrollableMatrixImage,
    render_matrix_image, render_expression_image,
)
from .theory_builder import TheoryDoc
from .theory_viewer import TheoryViewer
from .formula_value_blocks import FormulaValueBlocksToggle
from .gauss_inset import GaussCoordReadout
from .latex_status_label import LatexStatusLabel
from .iso_inverse import iso_inverse_map, natural_to_physical, element_coords
from . import gauss_glyph

__all__ = [
    "LatexMatrixImage",
    "LatexExpressionImage",
    "ScrollableMatrixImage",
    "render_matrix_image",
    "render_expression_image",
    "TheoryDoc",
    "TheoryViewer",
    "FormulaValueBlocksToggle",
    "GaussCoordReadout",
    "LatexStatusLabel",
    "iso_inverse_map",
    "natural_to_physical",
    "element_coords",
]
