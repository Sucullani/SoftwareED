"""
Panel reutilizable para listar modulos educativos por fase con scroll.

Cada modulo se renderiza como un boton + descripcion al lado. Reusado por
las pestanas Pre, Proc y Post para evitar triplicar la logica de creacion.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.settings import FONT_UI


def render_module_buttons(parent, modules, on_open, *, bootstyle="info-outline",
                          header_text=None, header_color=None,
                          subtitle=None):
    """Renderiza la lista de modulos en `parent` con scroll vertical.

    parent       : Frame contenedor.
    modules      : list[(mod_key, label, descripcion)]  (de list_modules_for_phase).
    on_open(key) : callback al click; recibe el mod_key.
    bootstyle    : estilo del boton (typicamente del color de la fase).
    header_text  : titulo opcional arriba del scroll.
    header_color : color opcional del titulo.
    subtitle     : texto opcional bajo el titulo.
    """
    canvas = tk.Canvas(parent, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient=VERTICAL, command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=inner, anchor=NW)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=YES)

    # Soporte rueda del raton sobre el canvas
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-event.delta / 120), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")

    if header_text:
        ttk.Label(
            inner, text=header_text,
            font=("Segoe UI", 11, "bold"),
            foreground=header_color or "#dddddd",
        ).pack(anchor=W, padx=10, pady=(10, 3))

    if subtitle:
        ttk.Label(
            inner, text=subtitle,
            font=FONT_UI, foreground="#888", wraplength=380,
        ).pack(anchor=W, padx=15, pady=(0, 10))

    if not modules:
        ttk.Label(
            inner,
            text="(sin modulos disponibles para esta fase)",
            font=FONT_UI, foreground="#666",
        ).pack(anchor=W, padx=15, pady=20)
        return

    for mod_key, label, desc in modules:
        row = ttk.Frame(inner)
        row.pack(fill=X, padx=15, pady=4)

        ttk.Button(
            row, text=label, bootstyle=bootstyle,
            command=lambda k=mod_key: on_open(k),
        ).pack(side=LEFT, fill=X, expand=YES)

        ttk.Label(
            row, text=desc, font=("Segoe UI", 8),
            foreground="#888", wraplength=160,
        ).pack(side=RIGHT, padx=5)
