"""Componentes reutilizables para los módulos educativos."""

from .latex_math import LatexMath
from .latex_image import (
    LatexMatrixImage, LatexExpressionImage,
    render_matrix_image, render_expression_image,
)
from .param_input import ParamInput
from .plot_panel import PlotPanel
from .theory_builder import TheoryDoc
from .theory_viewer import TheoryViewer
from .step_animator import StepAnimator
from .four_panel import FourPanel
from .latex_figure import render_matrix_latex, render_expression_latex
from .iso_inverse import iso_inverse_map, natural_to_physical
from .formula_value_toggle import FormulaValueToggle
from .formula_value_blocks import FormulaValueBlocksToggle
from .gauss_inset import GaussCoordReadout
from .latex_block import LatexBlock, make_variable_block, cm_font, CMU_FONT_FAMILY
from .latex_status_label import LatexStatusLabel
from . import gauss_glyph

__all__ = [
    "LatexMath",
    "LatexMatrixImage",
    "LatexExpressionImage",
    "render_matrix_image",
    "render_expression_image",
    "ParamInput",
    "PlotPanel",
    "TheoryDoc",
    "TheoryViewer",
    "StepAnimator",
    "FourPanel",
    "FormulaValueToggle",
    "FormulaValueBlocksToggle",
    "GaussCoordReadout",
    "LatexBlock",
    "make_variable_block",
    "cm_font",
    "CMU_FONT_FAMILY",
    "LatexStatusLabel",
    "render_matrix_latex",
    "render_expression_latex",
    "iso_inverse_map",
    "natural_to_physical",
]
