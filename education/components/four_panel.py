"""
FourPanel: layout 2x2 de ejes matplotlib sin ticks/ejes visibles,
con marcos suaves alrededor de cada panel. Extiende PlotPanel.
"""

from __future__ import annotations

from typing import Optional, Sequence

from .plot_panel import PlotPanel, _theme_colors


class FourPanel(PlotPanel):
    """PlotPanel con grilla 2x2, ejes ocultos y bordes suaves.

    Acceso: fp.ax(0,0), fp.ax(0,1), fp.ax(1,0), fp.ax(1,1).
    Soporta mezclar proyecciones 2D y 3D via parámetro `projections`.
    """

    def __init__(
        self,
        parent,
        figsize: tuple[float, float] = (9.5, 7.0),
        dpi: int = 100,
        show_toolbar: bool = False,
        projections: Optional[Sequence[Optional[str]]] = None,
        hide_ticks: bool = True,
        frame_color: str = "#45475a",
        frame_width: float = 1.2,
        **kwargs,
    ):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import (
            FigureCanvasTkAgg, NavigationToolbar2Tk
        )
        import ttkbootstrap as ttk

        projections = list(projections or [None, None, None, None])
        if len(projections) != 4:
            raise ValueError("projections debe tener 4 entradas")

        ttk.Frame.__init__(self, parent, **kwargs)
        colors = _theme_colors()

        self.figure = Figure(figsize=figsize, dpi=dpi, facecolor=colors["bg"])
        self.axes = []
        for idx, proj in enumerate(projections):
            row = idx // 2
            col = idx % 2
            if proj == "3d":
                ax = self.figure.add_subplot(2, 2, idx + 1, projection="3d")
            else:
                ax = self.figure.add_subplot(2, 2, idx + 1)
            self._style_axes(ax, colors, proj)
            if hide_ticks and proj != "3d":
                ax.set_xticks([])
                ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_color(frame_color)
                    spine.set_linewidth(frame_width)
            if proj == "3d":
                try:
                    ax.set_xticklabels([])
                    ax.set_yticklabels([])
                    ax.set_zticklabels([])
                except Exception:
                    pass
            self.axes.append(ax)

        self.ax = self.axes[0]
        self.figure.subplots_adjust(
            left=0.04, right=0.98, bottom=0.04, top=0.94,
            wspace=0.14, hspace=0.18,
        )

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, side="top")

        if show_toolbar:
            self._toolbar_frame = ttk.Frame(self)
            self._toolbar_frame.pack(fill="x", side="bottom")
            self.toolbar = NavigationToolbar2Tk(
                self.canvas, self._toolbar_frame, pack_toolbar=False
            )
            self.toolbar.update()
            self.toolbar.pack(fill="x")

        self._click_cid = None
        self._anim = None
        self._projections = projections
        self._hide_ticks = hide_ticks
        self._frame_color = frame_color
        self._frame_width = frame_width

    def ax_at(self, row: int, col: int):
        """Accede al eje en posición (row, col) con row,col ∈ {0,1}."""
        return self.axes[row * 2 + col]

    def clear(self) -> None:
        """Limpia los 4 ejes conservando estilo y ticks ocultos."""
        for ax, proj in zip(self.axes, self._projections):
            ax.clear()
        colors = _theme_colors()
        for ax, proj in zip(self.axes, self._projections):
            self._style_axes(ax, colors, proj)
            if self._hide_ticks and proj != "3d":
                ax.set_xticks([])
                ax.set_yticks([])
                for spine in ax.spines.values():
                    spine.set_color(self._frame_color)
                    spine.set_linewidth(self._frame_width)
            if proj == "3d":
                try:
                    ax.set_xticklabels([])
                    ax.set_yticklabels([])
                    ax.set_zticklabels([])
                except Exception:
                    pass
