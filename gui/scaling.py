"""
Dimensionado de ventanas contra la pantalla REAL del equipo.

Motivo (bug de campo 2026-09-09): toda la GUI estaba dimensionada en pixeles
absolutos elegidos a mano sobre el monitor de desarrollo (1366x768 al 100 %).

La aplicacion SI tiene conciencia de DPI: `ttk.Window(hdpi=True)` —el valor
por defecto que usa `MainWindow`— llama a `SetProcessDPIAware()` antes de
crear el interprete Tk. Eso es correcto (texto nitido en pantallas HiDPI),
pero tiene una consecuencia que el codigo no contemplaba: Tk recibe el DPI
real del monitor y mide las FUENTES en puntos, asi que en un equipo con el
escalado de Windows al 150 % cada fuente —todas las del programa se declaran
en puntos, `("Segoe UI", 9)`— se dibuja 1,5 veces mas grande, y con ella
crece cada widget que la contiene:

    escalado de Windows    dpi que ve Tk    tk scaling    fuentes y widgets
    100 %                  96               1,33          x1,00
    125 %                  120              1,67          x1,25
    150 %                  144              2,00          x1,50
    175 %                  168              2,33          x1,75

Los tamanos de ventana, en cambio, estaban escritos como numeros fijos de
pixeles y no crecian. De ahi los dos modos de falla del reporte —"los
botones no se ven o quedan cortados"—, ninguno visible en el equipo de
desarrollo, que esta al 100 %:

  a) el contenido crece pero la ventana no, asi que Tk recorta lo ULTIMO que
     se empaqueto, que era justo la barra de botones del pie. Medido: el
     contenido de `AboutDialog` pide 390 px de alto a 96 dpi, 465 a 120 y
     530 a 144, dentro de un `geometry("450x350")` fijo; el de
     `MaterialDialog`, 740 / 914 / 1075 px de ancho dentro de 680.

  b) la ventana no entra en el escritorio: `ElementTypeDialog` fijaba
     760x720 px y era `resizable(False, False)`, y el area util de una
     pantalla de 1366x768 con la barra de tareas es 1366x728 — 8 px de
     margen en el equipo de desarrollo y numeros negativos en cualquier
     portatil mas chico o con la barra de tareas mas alta. La ventana
     principal, con `minsize(1200, 700)`, no podia siquiera encogerse.

Este modulo es la UNICA via para fijar el tamano de un Toplevel:

    from gui.scaling import fit_window
    fit_window(self.dialog, 760, 720, parent=parent, minimo=(560, 420))

Las medidas que se le pasan son **pixeles de diseno a 96 dpi** (los mismos
numeros que estaban hardcodeados). `fit_window`:

  1. los escala por el DPI real de la pantalla (`screen_scale`), para que la
     ventana crezca al mismo ritmo que las fuentes;
  2. toma ese tamano como PISO y lo agranda si el contenido pide mas;
  3. lo RECORTA al area util del monitor donde vive la ventana padre,
     dejando un margen contra el borde;
  4. deja la ventana redimensionable, porque un recorte siempre puede
     quedar justo y el alumno tiene que poder agrandarla.

Que NO hace: no toca la conciencia de DPI del proceso (ya la fija
ttkbootstrap) ni escala los glifos del canvas —radios de nodo, flechas,
grosores— ni las figuras matplotlib embebidas, que siguen midiendose en
pixeles y por lo tanto se ven algo mas chicos en una pantalla HiDPI. Es
ajuste fino de otro orden: no recorta nada ni esconde botones.
"""

from __future__ import annotations

import os
import sys

# Las medidas del codigo se escribieron mirando un monitor a 96 dpi.
DPI_DE_DISENO = 96.0

# Aire que se deja SIEMPRE entre la ventana y el borde del area util: sin el,
# una ventana clampeada queda pegada al borde y su sombra/marco se corta.
MARGEN_PANTALLA = 24

# Piso absoluto: por debajo de esto no tiene sentido encoger una ventana.
ANCHO_MINIMO = 320
ALTO_MINIMO = 240

# Variable de entorno de diagnostico: permite reproducir la pantalla de otro
# equipo sin cambiar el escalado de Windows. La consumen los tests
# (`tests/test_dpi_layout_gui.py`) y sirve para verificar a mano un reporte:
#     set EDUFEM_AREA_UTIL=1280x680 && python main.py
VAR_AREA_UTIL = "EDUFEM_AREA_UTIL"


# ─────────────────────────────────────────────────────────────────────────
# Escala de la pantalla
# ─────────────────────────────────────────────────────────────────────────

def forget_screen_scale(win) -> None:
    """Olvida la escala cacheada. La usa el test que simula otro DPI."""
    try:
        win.tk._edufem_escala = None
    except Exception:
        pass


def screen_scale(win) -> float:
    """Factor de escala de la pantalla: dpi real / 96.

    Se cachea en el interprete Tk (no en el widget): todas las ventanas de
    una misma aplicacion comparten pantalla, y `winfo_fpixels` cuesta un
    ida y vuelta al interprete.
    """
    try:
        cache = getattr(win.tk, "_edufem_escala", None)
        if cache is not None:
            return cache
        dpi = float(win.winfo_fpixels("1i"))
    except Exception:
        return 1.0
    escala = dpi / DPI_DE_DISENO
    # Windows reporta 96.11 dpi a 100 %: sin este redondeo el factor seria
    # 1.0011 y cada medida quedaria un pixel corrida respecto del diseno.
    escala = round(escala * 20) / 20.0
    # Nunca por debajo de 1.0: las fuentes tampoco encogen (Tk las mide en
    # puntos), asi que achicar los contenedores solo produce recortes.
    escala = min(max(escala, 1.0), 4.0)
    try:
        win.tk._edufem_escala = escala
    except Exception:
        pass
    return escala


def scaled(win, medida: float) -> int:
    """Convierte una medida de diseno (px a 96 dpi) a px de esta pantalla."""
    return int(round(medida * screen_scale(win)))


# ─────────────────────────────────────────────────────────────────────────
# Area util del monitor (pantalla menos la barra de tareas)
# ─────────────────────────────────────────────────────────────────────────

def _area_forzada():
    """Lee `EDUFEM_AREA_UTIL=ANCHOxALTO`. Devuelve None si no esta o no parsea."""
    crudo = os.environ.get(VAR_AREA_UTIL, "").strip().lower()
    if not crudo:
        return None
    try:
        ancho, alto = crudo.split("x")
        return (0, 0, max(ANCHO_MINIMO, int(ancho)), max(ALTO_MINIMO, int(alto)))
    except ValueError:
        return None


def _hwnd(win):
    """HWND del marco de un Toplevel Tk, o None si aun no esta mapeado."""
    try:
        return int(win.wm_frame(), 16)
    except Exception:
        return None


def _area_util_windows(win):
    """Area de trabajo del monitor donde esta `win`, via Win32.

    `MonitorFromWindow` + `GetMonitorInfoW` da el monitor CORRECTO en
    multi-monitor (SystemParametersInfo solo conoce el primario) y descuenta
    la barra de tareas este donde este —abajo, arriba o vertical.
    """
    import ctypes
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                    ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT),
                    ("rcWork", RECT), ("dwFlags", wintypes.DWORD)]

    user32 = ctypes.windll.user32
    handle = _hwnd(win)
    if handle:
        MONITOR_DEFAULTTONEAREST = 2
        monitor = user32.MonitorFromWindow(wintypes.HWND(handle),
                                           MONITOR_DEFAULTTONEAREST)
        if monitor:
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                r = info.rcWork
                return (r.left, r.top, r.right - r.left, r.bottom - r.top)
    # Sin ventana mapeada todavia: area util del monitor primario.
    SPI_GETWORKAREA = 0x0030
    r = RECT()
    if user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(r), 0):
        return (r.left, r.top, r.right - r.left, r.bottom - r.top)
    raise OSError("SystemParametersInfoW fallo")


def work_area(win):
    """`(x, y, ancho, alto)` del area util donde debe caber una ventana.

    Es la pantalla MENOS la barra de tareas. Se devuelve tambien el origen
    porque con la barra arriba o a la izquierda no es (0, 0), y una ventana
    centrada en (0, 0) quedaria debajo de ella.
    """
    forzada = _area_forzada()
    if forzada is not None:
        return forzada
    if sys.platform == "win32":
        try:
            return _area_util_windows(win)
        except Exception:
            pass
    # Linux/macOS o fallo del API: pantalla completa menos un mordisco
    # conservador para el panel/dock del escritorio.
    try:
        ancho = win.winfo_screenwidth()
        alto = win.winfo_screenheight()
    except Exception:
        return (0, 0, 1024, 768)
    return (0, 0, ancho, alto - 48)


# ─────────────────────────────────────────────────────────────────────────
# Calculo puro (testeable sin pantalla)
# ─────────────────────────────────────────────────────────────────────────

def fit_size(ancho, alto, escala, area_ancho, area_alto,
             *, margen=MARGEN_PANTALLA):
    """Tamano final de una ventana: `(ancho, alto)` de diseno escalados y
    recortados al area util. Funcion PURA — la testea `test_dpi_layout`.

    Solo recorta: si la pantalla sobra, la ventana conserva su tamano de
    diseno (una ventana no mejora por crecer hasta el borde del monitor).
    """
    tope_ancho = max(ANCHO_MINIMO, int(area_ancho) - margen)
    tope_alto = max(ALTO_MINIMO, int(area_alto) - margen)
    return (min(int(round(ancho * escala)), tope_ancho),
            min(int(round(alto * escala)), tope_alto))


def fit_position(x, y, ancho, alto, area):
    """Posicion final `(x, y)` de una ventana ya dimensionada: la mete
    entera dentro del area util. Funcion PURA.
    """
    ax, ay, aw, ah = area
    x = min(max(int(x), ax), ax + max(0, aw - ancho))
    y = min(max(int(y), ay), ay + max(0, ah - alto))
    return x, y


# ─────────────────────────────────────────────────────────────────────────
# API de ventanas
# ─────────────────────────────────────────────────────────────────────────

def fit_window(win, ancho, alto, *, parent=None, minimo=None,
               redimensionable=True, centrar=True,
               crecer_con_contenido=True):
    """Dimensiona `win` a `ancho x alto` px de diseno SIN salirse de la pantalla.

    - escala las dos medidas por el DPI real;
    - toma el tamano de diseno como PISO, no como valor exacto: si el
      contenido pide mas (fuente del sistema mas grande, textos mas largos
      que en el equipo de desarrollo), la ventana crece en vez de recortar
      —era el segundo modo de falla: `AboutDialog` fijaba 450x350 y su
      contenido pedia 390 px de alto, asi que el boton Cerrar quedaba a
      medias incluso a 96 dpi;
    - despues recorta al area util del monitor de `parent` (o de `win`);
    - fija un `minsize` que nunca supera ese tamano (un minsize mas grande
      que la pantalla es exactamente lo que dejaba los botones afuera);
    - centra sobre `parent` clampeando contra el area util;
    - deja la ventana redimensionable: si el recorte deja el contenido
      justo, el alumno todavia puede agrandarla o moverla.

    `minimo` va en px de diseno, igual que `ancho`/`alto`.
    """
    area = work_area(parent if parent is not None else win)
    escala = screen_scale(win)
    if crecer_con_contenido:
        try:
            win.update_idletasks()
            ancho = max(ancho * escala, win.winfo_reqwidth()) / escala
            alto = max(alto * escala, win.winfo_reqheight()) / escala
        except Exception:
            pass
    w, h = fit_size(ancho, alto, escala, area[2], area[3])
    try:
        win.geometry(f"{w}x{h}")
        win.resizable(bool(redimensionable), bool(redimensionable))
        if minimo is not None:
            # El minsize se clampea al tamano REAL: nunca puede obligar a la
            # ventana a ser mas grande que el area util.
            mw = min(int(round(minimo[0] * escala)), w)
            mh = min(int(round(minimo[1] * escala)), h)
            win.minsize(mw, mh)
    except Exception:
        return w, h
    if centrar and parent is not None:
        center_on_parent(win, parent, tamano=(w, h))
    return w, h


def clamp_window(win, *, parent=None, minimo=None):
    """Recorta una ventana que se dimensiono SOLA (shrink-wrap del contenido)
    para que no exceda el area util. Para los Toplevel sin `geometry` fija:
    su tamano sale de `winfo_req*`, que en un equipo con la fuente del
    sistema mas grande puede pasarse de pantalla.
    """
    try:
        win.update_idletasks()
        area = work_area(parent if parent is not None else win)
        w = max(win.winfo_reqwidth(), win.winfo_width())
        h = max(win.winfo_reqheight(), win.winfo_height())
        nw, nh = fit_size(w, h, 1.0, area[2], area[3])
        if (nw, nh) != (w, h):
            win.geometry(f"{nw}x{nh}")
        if minimo is not None:
            escala = screen_scale(win)
            win.minsize(min(int(round(minimo[0] * escala)), nw),
                        min(int(round(minimo[1] * escala)), nh))
        return nw, nh
    except Exception:
        return None


def center_on_parent(win, parent, *, tamano=None):
    """Centra `win` sobre `parent` sin que se salga del area util.

    Si `parent` no esta mapeado (o es la ventana raiz todavia sin geometria)
    cae a centrar sobre el area util.
    """
    try:
        if tamano is None:
            win.update_idletasks()
            w = max(win.winfo_width(), win.winfo_reqwidth())
            h = max(win.winfo_height(), win.winfo_reqheight())
        else:
            w, h = tamano
        area = work_area(parent if parent is not None else win)
        try:
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
            if pw <= 1 or ph <= 1:
                raise ValueError
        except Exception:
            px, py, pw, ph = area
        x, y = fit_position(px + (pw - w) // 2, py + (ph - h) // 2, w, h, area)
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass
