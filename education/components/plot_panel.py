"""
PlotPanel: envoltura de FigureCanvasTkAgg + NavigationToolbar2Tk dentro de un
ttk.Frame coherente con el tema darkly de ttkbootstrap. Soporta click callbacks
y animaciones por frame.
"""

from __future__ import annotations

from typing import Callable, Optional

import ttkbootstrap as ttk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


# Paleta coherente con el tema 'darkly' de ttkbootstrap
_DARK_THEME = {
    "bg": "#222233",
    "fg": "#dfdfdf",
    "grid": "#404055",
    "panel": "#2b2b3c",
    "accent": "#4fa3ff",
}


def _theme_colors() -> dict[str, str]:
    return dict(_DARK_THEME)


class PlotPanel(ttk.Frame):
    """Panel con Figure matplotlib embebido. Accede a .figure y .ax."""

    def __init__(
        self,
        parent,
        figsize: tuple[float, float] = (5.5, 4.0),
        dpi: int = 100,
        show_toolbar: bool = True,
        subplots: tuple[int, int] = (1, 1),
        projection: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        colors = _theme_colors()

        self.figure = Figure(figsize=figsize, dpi=dpi, facecolor=colors["bg"])
        rows, cols = subplots
        self.axes = []
        for i in range(rows * cols):
            if projection == "3d":
                ax = self.figure.add_subplot(rows, cols, i + 1, projection="3d")
            else:
                ax = self.figure.add_subplot(rows, cols, i + 1)
            self._style_axes(ax, colors, projection)
            self.axes.append(ax)
        self.ax = self.axes[0]

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, side="top")

        if show_toolbar:
            self._toolbar_frame = ttk.Frame(self)
            self._toolbar_frame.pack(fill="x", side="bottom")
            self.toolbar = NavigationToolbar2Tk(self.canvas, self._toolbar_frame,
                                                pack_toolbar=False)
            try:
                self.toolbar.configure(background=colors["bg"])
                for child in self.toolbar.winfo_children():
                    try:
                        child.configure(background=colors["bg"])
                    except Exception:
                        pass
            except Exception:
                pass
            self.toolbar.update()
            self.toolbar.pack(fill="x")

        self._click_cid: Optional[int] = None
        self._anim = None

    @staticmethod
    def _style_axes(ax, colors, projection):
        ax.set_facecolor(colors["bg"])
        ax.tick_params(colors=colors["fg"])
        for spine in ax.spines.values():
            spine.set_color(colors["fg"])
        ax.xaxis.label.set_color(colors["fg"])
        ax.yaxis.label.set_color(colors["fg"])
        ax.title.set_color(colors["fg"])
        if projection != "3d":
            ax.grid(True, color=colors["grid"], linewidth=0.4, alpha=0.6)
        else:
            try:
                ax.zaxis.label.set_color(colors["fg"])
                ax.tick_params(axis="z", colors=colors["fg"])
            except Exception:
                pass

    def bind_click(self, callback: Callable) -> None:
        """Registra callback para button_press_event. callback(event)."""
        if self._click_cid is not None:
            self.canvas.mpl_disconnect(self._click_cid)
        self._click_cid = self.canvas.mpl_connect("button_press_event", callback)

    def bind_motion(self, callback: Callable) -> None:
        self.canvas.mpl_connect("motion_notify_event", callback)

    def redraw(self) -> None:
        self.canvas.draw_idle()

    def clear(self) -> None:
        for ax in self.axes:
            ax.clear()
        colors = _theme_colors()
        for ax in self.axes:
            projection = "3d" if hasattr(ax, "zaxis") else None
            self._style_axes(ax, colors, projection)
