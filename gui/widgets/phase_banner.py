"""
Banner colorido para identificar visualmente cada fase (Pre/Proc/Post).

Frame de altura fija con fondo del color de la fase, icono grande, titulo
y subtitulo. Usa tk.Frame (no ttk) porque ttkbootstrap impone el background
del tema y aqui necesitamos un color solido independiente.
"""

import tkinter as tk

from config.settings import (
    FONT_UI, PHASE_BANNER_TITLE_FG_COLOR, PHASE_BANNER_SUBTITLE_FG_COLOR,
)


def build_phase_banner(parent, color, icon, title, subtitle, *, height=46):
    """Construye y empaqueta (top, fill=x) un banner de fase.

    parent     : widget padre (Frame de la pestana).
    color      : hex del color de la fase (PHASE_*_COLOR).
    icon       : emoji o glyph corto (ej. "PRE").
    title      : nombre de la fase (ej. "PRE-PROCESO").
    subtitle   : descripcion corta (ej. "Definir geometria...").
    height     : altura en px (default 46).

    Retorna el Frame creado por si el caller necesita mas customizacion.
    """
    banner = tk.Frame(parent, bg=color, height=height)
    banner.pack(side="top", fill="x")
    banner.pack_propagate(False)

    tk.Label(
        banner, text=f"{icon}  {title}",
        bg=color, fg=PHASE_BANNER_TITLE_FG_COLOR,
        font=("Segoe UI Semibold", 13),
    ).pack(side="left", padx=(14, 0), pady=8)

    tk.Label(
        banner, text=subtitle,
        bg=color, fg=PHASE_BANNER_SUBTITLE_FG_COLOR,
        font=FONT_UI,
    ).pack(side="left", padx=(10, 14), pady=8)

    return banner
