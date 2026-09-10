"""
Helpers compartidos por los diálogos de gui/dialogs/.

Centraliza lógica que estaba duplicada verbatim en cada diálogo (auditoría
2026-05): dimensionado y centrado del Toplevel (`size_dialog`, `center_dialog`)
y las teclas `Escape` / `Return` (`bind_dialog_keys`).
"""

from __future__ import annotations

from gui.scaling import center_on_parent, fit_window


def center_dialog(win, parent):
    """Centra `win` (un Toplevel) sobre `parent`, dentro del área útil.

    Reemplaza las ~7 copias de `_center()` que vivían en cada diálogo.
    Es solo para recentrar una ventana que ya tiene su tamaño: los diálogos
    usan `size_dialog`, que dimensiona y centra en un paso.

    Ya no existe el parámetro `clamp_screen` (2026-09-10): elegía entre
    clampar contra coordenadas negativas o contra el borde inferior de la
    pantalla, y `gui.scaling.center_on_parent` clampa SIEMPRE contra el área
    útil del monitor —barra de tareas descontada, monitor correcto en
    multi-monitor—, que es lo que las dos variantes aproximaban.
    """
    center_on_parent(win, parent)


def size_dialog(win, parent, ancho, alto, *, minimo=None,
                redimensionable=True):
    """Dimensiona y centra un diálogo en un solo paso.

    `ancho`/`alto` son píxeles de diseño a 96 dpi (los mismos números que
    antes iban en `geometry("AxB")`). `gui.scaling.fit_window` los escala por
    el DPI de la pantalla, los agranda si el contenido pide más y los recorta
    al área útil real. Con el número fijo, en un equipo con el escalado de
    Windows al 150 % las fuentes crecían 1,5x dentro de un diálogo que no
    crecía y la barra de botones quedaba fuera.
    """
    return fit_window(win, ancho, alto, parent=parent, minimo=minimo,
                      redimensionable=redimensionable)


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
