"""Componentes reutilizables para los módulos educativos."""

from .latex_math import LatexMath
from .param_input import ParamInput
from .plot_panel import PlotPanel
from .element_picker import ElementPicker
from .theory_builder import TheoryDoc
from .theory_viewer import TheoryViewer
from .step_animator import StepAnimator
from .four_panel import FourPanel
from .latex_figure import render_matrix_latex, render_expression_latex
from .iso_inverse import iso_inverse_map, natural_to_physical
from .video_player import VideoPlayer

__all__ = [
    "LatexMath",
    "ParamInput",
    "PlotPanel",
    "ElementPicker",
    "TheoryDoc",
    "TheoryViewer",
    "StepAnimator",
    "FourPanel",
    "render_matrix_latex",
    "render_expression_latex",
    "iso_inverse_map",
    "natural_to_physical",
    "VideoPlayer",
]
