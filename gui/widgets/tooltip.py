"""
Tooltip simple para cualquier widget Tk.
Uso: ToolTip(button, text="Guardar (Ctrl+S)")
"""

import tkinter as tk


class ToolTip:
    """Muestra un pequeño Toplevel sin bordes al pasar el mouse sobre el widget."""

    def __init__(self, widget, text="", delay=450, wraplength=220):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self._tip_window = None
        self._after_id = None

        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event=None):
        self._schedule()

    def _on_leave(self, _event=None):
        self._unschedule()
        self._hide()

    def _schedule(self):
        self._unschedule()
        self._after_id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        except Exception:
            return

        self._tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        label = tk.Label(
            tw,
            text=self.text,
            background="#2a2a3a",
            foreground="#e4e4e4",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=8,
            pady=3,
            wraplength=self.wraplength,
            justify="left",
        )
        label.pack()

    def _hide(self):
        if self._tip_window is not None:
            try:
                self._tip_window.destroy()
            except Exception:
                pass
            self._tip_window = None

    def set_text(self, text):
        self.text = text
