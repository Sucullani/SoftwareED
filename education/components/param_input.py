"""
ParamInput: row compacto [label] [entry] [unit] con validación numérica.
Emite callback on_change al presionar Enter o perder foco. Basado en ttk.
"""

from __future__ import annotations

from typing import Callable, Optional

import tkinter as tk
import ttkbootstrap as ttk


class ParamInput(ttk.Frame):
    """Row: [label] [entry] [unit]."""

    def __init__(
        self,
        parent,
        label: str,
        value: float,
        unit: str = "",
        fmt: str = "{:g}",
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        on_change: Optional[Callable[[float], None]] = None,
        width_entry: int = 12,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._fmt = fmt
        self._vmin = vmin
        self._vmax = vmax
        self._on_change = on_change
        self._value = float(value)

        self.columnconfigure(1, weight=1)

        self.label = ttk.Label(self, text=label, anchor="w")
        self.label.grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.var = tk.StringVar(value=fmt.format(self._value))
        self.entry = ttk.Entry(self, textvariable=self.var, width=width_entry)
        self.entry.grid(row=0, column=1, sticky="ew")
        self.entry.bind("<Return>", self._commit)
        self.entry.bind("<FocusOut>", self._commit)

        if unit:
            self.unit_label = ttk.Label(self, text=unit, anchor="w")
            self.unit_label.grid(row=0, column=2, sticky="w", padx=(6, 0))

    def _commit(self, _event=None):
        raw = self.var.get().strip().replace(",", ".")
        try:
            v = float(raw)
        except ValueError:
            self.var.set(self._fmt.format(self._value))
            self._flash_error()
            return

        if self._vmin is not None and v < self._vmin:
            v = self._vmin
        if self._vmax is not None and v > self._vmax:
            v = self._vmax

        self._value = v
        self.var.set(self._fmt.format(v))
        if self._on_change:
            self._on_change(v)

    def _flash_error(self):
        try:
            self.entry.configure(bootstyle="danger")
            self.after(600, lambda: self.entry.configure(bootstyle="default"))
        except Exception:
            pass

    def get(self) -> float:
        return self._value

    def set(self, v: float, trigger: bool = False) -> None:
        self._value = float(v)
        self.var.set(self._fmt.format(self._value))
        if trigger and self._on_change:
            self._on_change(self._value)
