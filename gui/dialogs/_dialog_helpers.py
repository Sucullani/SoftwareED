"""
Helpers compartidos por los diálogos de gui/dialogs/.

Centraliza lógica que estaba duplicada verbatim en cada diálogo (auditoría
2026-05): centrado del Toplevel sobre el parent (`center_dialog`) y las
teclas `Escape` / `Return` (`bind_dialog_keys`).
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


def bind_dialog_keys(win, *, on_escape=None, on_return=None):
    """Ata `Escape` y `Return` a las acciones de un diálogo.

    Ningún diálogo del programa respondía a estas dos teclas, que el
    alumno da por sentadas en cualquier otro software: había que llevar el
    mouse hasta el botón o hasta la X para todo.

    **La semántica no es la misma en los diez diálogos**, y por eso esto
    es un helper con dos parámetros y no un comportamiento automático:

    - `Escape` = *salir sin cambiar nada*. Siempre lo mismo que la X del
      Toplevel — en `HealthReportDialog` la X navega al Pre-Proceso, así
      que Escape también.
    - `Return` = **la** acción primaria, solo cuando hay una sola y
      pulsarla sin querer no rompe nada. Los diálogos donde las dos
      opciones son decisiones opuestas (`HealthReportDialog`: corregir vs.
      resolver igual) o donde la acción principal se va de la aplicación
      (`pdflatex_missing_dialog`: abre el navegador) **no atan Return** —
      no hay default seguro que elegir por el alumno.

    El handler devuelve `"break"`: sin eso, el `Return` de un `Entry`
    seguiría subiendo por los bindtags después de haber aceptado.

    La tabla completa diálogo → (Escape, Return) está en
    `docs/convenciones/arquitectura.md`, junto a `center_dialog`.
    """
    def _wrap(callback):
        def _handler(_event=None):
            callback()
            return "break"
        return _handler

    if on_escape is not None:
        win.bind("<Escape>", _wrap(on_escape))
    if on_return is not None:
        handler = _wrap(on_return)
        win.bind("<Return>", handler)
        win.bind("<KP_Enter>", handler)    # Enter del teclado numérico
