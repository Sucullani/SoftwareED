"""
FormulaValueBlocksToggle — variante de `FormulaValueToggle` basada en
**frames Tk** en lugar de un Axes matplotlib compartido.

Por qué existe:
    `FormulaValueToggle` da un `ax` a cada callback (formula/values). Si el
    callback necesita varios elementos (una matriz + un caption + un hint),
    todos compiten por el mismo Axes y se solapan — especialmente con
    matrices Q9 (3×18) que ocupan casi todo el ancho.

Esta variante invierte la relación: cada callback recibe un `ttk.Frame`
y lo pobla con widgets Tk (LatexMatrixImage, LatexExpressionImage, etiquetas,
etc.). Tk se encarga del layout (pack/grid) — sin solapes, sin auto-shrink
agresivo, fontsize legible incluso en Q9.

Ciclo de vida:
    - `__init__` invoca `build_formula(self._frame_formula)` y
      `build_values(self._frame_values)` UNA SOLA VEZ; ambos frames quedan
      construidos y se ocultan/muestran en cada toggle.
    - El caller debe poder UPDATE-AR los widgets construidos (la matriz
      cambia con ξ, η). Para eso retorna un dict de "refs" desde el builder
      que el caller guarda y muta:

          def _build_values(self, frame):
              self._mat = LatexMatrixImage(frame, matrix=self._compute_b())
              self._mat.pack(...)
              self._cap = ttk.Label(frame, text=self._status_text())
              self._cap.pack(...)

          # En refresh:
          self._mat.set_matrix(self._compute_b())
          self._cap.configure(text=self._status_text())

    Esto es equivalente al patrón de `FormulaValueToggle.refresh()` pero
    sin re-construir widgets cada vez — más rápido y más estable
    visualmente (no hay "parpadeo" de re-empaquetado).

Uso típico:

    toggle = FormulaValueBlocksToggle(
        body,
        build_formula = self._build_formula_panel,
        build_values  = self._build_values_panel,
        initial = FormulaValueBlocksToggle.MODE_VALUES,
    )
    toggle.pack(fill="both", expand=True, pady=(2, 0))
"""

from __future__ import annotations

from typing import Callable, Optional

import tkinter as tk
import ttkbootstrap as ttk

from config.settings import OVERLAY_BG, HEALTH_ERROR_COLOR, FONT_UI


class FormulaValueBlocksToggle(ttk.Frame):
    """Toggle Fórmula/Valores con frames Tk como contenedores.

    Args:
        parent: widget contenedor.
        build_formula: callable `(frame)->None` que pobla `frame` con
                       widgets para la versión simbólica.
        build_values:  callable `(frame)->None` que pobla `frame` con
                       widgets para la versión numérica.
        initial: modo inicial (MODE_FORMULA o MODE_VALUES).
        on_mode_change: callback opcional invocado tras cambiar modo.
    """

    MODE_FORMULA = "formula"
    MODE_VALUES = "values"

    def __init__(
        self,
        parent: tk.Widget,
        *,
        build_formula: Callable[[ttk.Frame], None],
        build_values: Callable[[ttk.Frame], None],
        initial: str = MODE_VALUES,
        on_mode_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._on_mode_change = on_mode_change
        self._mode = initial if initial in (self.MODE_FORMULA, self.MODE_VALUES) \
                              else self.MODE_VALUES

        # ── Toolbar superior con los dos radiobuttons segmented ────
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 4))

        self._var = tk.StringVar(value=self._mode)
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

        # ── Dos frames de contenido, solo uno visible a la vez ──
        # Usamos un container con grid y row/col 0,0 para ambos — el
        # que está activo lo elevamos al tope con `tkraise`. Esto evita
        # parpadeo de pack/forget.
        self._stack = ttk.Frame(self)
        self._stack.pack(fill="both", expand=True)
        self._stack.grid_rowconfigure(0, weight=1)
        self._stack.grid_columnconfigure(0, weight=1)

        self._frame_formula = ttk.Frame(self._stack)
        self._frame_values = ttk.Frame(self._stack)
        self._frame_formula.grid(row=0, column=0, sticky="nsew")
        self._frame_values.grid(row=0, column=0, sticky="nsew")

        # Construir contenido UNA SOLA VEZ
        try:
            build_formula(self._frame_formula)
        except Exception as exc:
            self._show_build_error(self._frame_formula, exc, "fórmula")
        try:
            build_values(self._frame_values)
        except Exception as exc:
            self._show_build_error(self._frame_values, exc, "valores")

        # Mostrar el frame inicial
        self._apply_mode()

    # ── API pública ────────────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in (self.MODE_FORMULA, self.MODE_VALUES):
            return
        if mode == self._mode:
            return
        self._mode = mode
        self._var.set(mode)
        self._apply_mode()
        if self._on_mode_change is not None:
            try:
                self._on_mode_change(mode)
            except Exception:
                pass

    @property
    def frame_formula(self) -> ttk.Frame:
        """Acceso al frame de la fórmula (para refrescos imperativos)."""
        return self._frame_formula

    @property
    def frame_values(self) -> ttk.Frame:
        """Acceso al frame de valores (para refrescos imperativos)."""
        return self._frame_values

    # ── Interno ────────────────────────────────────────────────────
    def _on_change(self) -> None:
        self._mode = self._var.get()
        self._apply_mode()
        if self._on_mode_change is not None:
            try:
                self._on_mode_change(self._mode)
            except Exception:
                pass

    def _apply_mode(self) -> None:
        if self._mode == self.MODE_FORMULA:
            self._frame_formula.tkraise()
        else:
            self._frame_values.tkraise()

    @staticmethod
    def _show_build_error(frame: ttk.Frame, exc: Exception, label: str) -> None:
        tk.Label(
            frame, text=f"Error al construir el panel de {label}:\n{exc}",
            bg=OVERLAY_BG, fg=HEALTH_ERROR_COLOR, font=FONT_UI,
            justify="left", anchor="w", wraplength=440,
        ).pack(fill="both", expand=True, padx=8, pady=8)
