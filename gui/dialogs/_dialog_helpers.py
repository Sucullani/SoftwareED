"""
Helpers compartidos por los diálogos de gui/dialogs/.

Centraliza lógica que estaba duplicada verbatim en cada diálogo (auditoría
2026-05). Por ahora: centrado del Toplevel sobre el parent.
"""

from __future__ import annotations


def center_dialog(win, parent, *, clamp_screen=False):
    """Centra `win` (un Toplevel) sobre `parent`.

    Reemplaza las ~7 copias de `_center()` que vivían en cada diálogo.

    clamp_screen=False: clampa solo a coords >= 0 (variante simple).
    clamp_screen=True: además clampa contra el tamaño de pantalla dejando
        ~50 px de margen inferior (variante usada por los diálogos altos
        con video, ElementType / Analysis... y Gravity).
    """
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    x = parent.winfo_x() + (parent.winfo_width() - w) // 2
    y = parent.winfo_y() + (parent.winfo_height() - h) // 2
    if clamp_screen:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h - 50))
    else:
        x = max(x, 0)
        y = max(y, 0)
    win.geometry(f"+{x}+{y}")
