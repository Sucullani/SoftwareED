"""
FormulaValueToggle — toggle Fórmula simbólica ↔ Valores numéricos.

Widget reusable para los overlays educativos cuyo concepto central es una
matriz/expresión que existe en dos formas pedagógicamente complementarias:

    • Fórmula simbólica   — D = E/(1-ν²) [...]    (qué ES la matriz)
    • Valores numéricos   — D = [[+0.31, ...], ...]  (qué VALE para este caso)

El alumno alterna entre ambas con un solo click, sin perder el contexto del
overlay. Implementado con dos `Radiobutton` toolbutton + área matplotlib
embebida que renderiza LaTeX vía mathtext. Sin compilador externo.

Uso:
    toggle = FormulaValueToggle(
        parent,
        render_formula = lambda ax: render_expression_latex(ax, expr_str),
        render_values  = lambda ax: render_matrix_latex(ax, D_numeric, ...),
        initial = FormulaValueToggle.MODE_VALUES,
    )
    toggle.pack(fill="both", expand=True)

    # Cuando los datos cambian (e.g. el usuario movió el dial de Poisson):
    toggle.refresh()

Notas:
    • Las dos callbacks reciben `ax` (matplotlib Axes) y son responsables
      de limpiarlo y dibujar lo que necesiten.
    • Si una callback lanza, el toggle muestra el error en el axes en lugar
      de propagar — los overlays siguen siendo "self-explaining" aunque
      falle un cómputo.
"""

from __future__ import annotations

from typing import Callable, Optional

import tkinter as tk
import ttkbootstrap as ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config.settings import EDU_FG, OVERLAY_BG


# Bg del toggle alineado con el OVERLAY_BG (=ttk darkly TFrame bg).
# Antes era EDU_AXES_BG = #2c2c2c, producia rectangulo visible sobre
# el OVERLAY_BG = #222222. Cambio en 2026-05.
_TOGGLE_BG_DARK = OVERLAY_BG
_TOGGLE_FG_FALLBACK = EDU_FG


class FormulaValueToggle(ttk.Frame):
    """Segmented toggle entre dos modos de renderizado de una expresión.

    Args:
        parent: widget Tk contenedor.
        render_formula: callable(ax) que dibuja la versión simbólica.
        render_values: callable(ax) que dibuja la versión numérica.
        initial: modo inicial (`MODE_FORMULA` o `MODE_VALUES`).
        figsize: tamaño de la figura matplotlib en pulgadas (w, h).
        dpi: resolución del canvas matplotlib.
        on_mode_change: callback opcional `callable(mode_str)` invocada
                        después de cada toggle.
    """

    MODE_FORMULA = "formula"
    MODE_VALUES = "values"

    def __init__(
        self,
        parent: tk.Widget,
        *,
        render_formula: Callable,
        render_values: Callable,
        initial: str = MODE_VALUES,
        figsize: tuple = (6.0, 2.6),
        dpi: int = 100,
        on_mode_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._render_formula = render_formula
        self._render_values = render_values
        self._on_mode_change = on_mode_change
        self._mode = initial if initial in (self.MODE_FORMULA, self.MODE_VALUES) \
                              else self.MODE_VALUES

        # ── Toolbar superior con los dos toolbuttons ─────────────────
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 4))

        self._var = tk.StringVar(value=self._mode)
        # bootstyle="info-outline-toolbutton" da apariencia de segmented
        # control (botones agrupados con borde, presionado = lleno).
        self._btn_formula = ttk.Radiobutton(
            bar, text="ƒ  Fórmula", value=self.MODE_FORMULA,
            variable=self._var, bootstyle="info-outline-toolbutton",
            command=self._on_change,
        )
        self._btn_formula.pack(side="left", padx=(0, 2))

        self._btn_values = ttk.Radiobutton(
            bar, text="123  Valores", value=self.MODE_VALUES,
            variable=self._var, bootstyle="info-outline-toolbutton",
            command=self._on_change,
        )
        self._btn_values.pack(side="left", padx=(0, 2))

        # ── Figura matplotlib embebida ───────────────────────────────
        self._fig = Figure(figsize=figsize, dpi=dpi)
        self._fig.patch.set_facecolor(_TOGGLE_BG_DARK)
        self._ax = self._fig.add_subplot(111)
        self._ax.set_facecolor(_TOGGLE_BG_DARK)

        self._canvas = FigureCanvasTkAgg(self._fig, master=self)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        # Render inicial
        self.refresh()

    # ── API pública ────────────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        """Cambia el modo programáticamente (sincroniza Radiobutton + render)."""
        if mode not in (self.MODE_FORMULA, self.MODE_VALUES):
            return
        if mode == self._mode:
            return
        self._mode = mode
        self._var.set(mode)
        self.refresh()
        if self._on_mode_change is not None:
            try:
                self._on_mode_change(mode)
            except Exception:
                pass

    def refresh(self) -> None:
        """Re-renderiza el modo actual. Llamar cuando los datos subyacentes
        cambian (e.g. el usuario movió el dial de Poisson en M3)."""
        self._ax.clear()
        self._ax.set_facecolor(_TOGGLE_BG_DARK)
        self._ax.set_xticks([])
        self._ax.set_yticks([])
        for spine in self._ax.spines.values():
            spine.set_visible(False)

        try:
            if self._mode == self.MODE_FORMULA:
                self._render_formula(self._ax)
            else:
                self._render_values(self._ax)
        except Exception as exc:  # noqa: BLE001 — UX: no propagar al overlay
            self._ax.text(
                0.5, 0.5,
                f"Error al renderizar:\n{exc}",
                ha="center", va="center",
                transform=self._ax.transAxes,
                color="#e74c3c", fontsize=10,
            )

        try:
            self._fig.tight_layout(pad=0.3)
        except Exception:
            pass
        self._canvas.draw_idle()

    # ── interno ────────────────────────────────────────────────────
    def _on_change(self) -> None:
        self._mode = self._var.get()
        self.refresh()
        if self._on_mode_change is not None:
            try:
                self._on_mode_change(self._mode)
            except Exception:
                pass
