"""
Dimensionado de ventanas — verificacion con Tk REAL (necesita un display).

Contraparte de `tests/test_dpi_layout.py`: aquel mira el codigo, este ABRE
cada ventana del programa simulando la pantalla del equipo donde la
aplicacion se descuadraba, y comprueba tres cosas por ventana:

  1. entra entera en el area util (ancho Y alto);
  2. su contenido no queda recortado —lo que pide <= lo que tiene—, salvo
     que la ventana ya este contra el tope de la pantalla;
  3. la barra de botones —lo que el reporte decia que "no se ve"— queda
     entera dentro del alto visible de la ventana.

La pantalla se simula con `EDUFEM_AREA_UTIL=ANCHOxALTO`, que es la misma
palanca que sirve para reproducir un reporte a mano:

    set EDUFEM_AREA_UTIL=1280x680 && python main.py

Cada pantalla corre en un SUBPROCESO: ttkbootstrap no soporta dos raices Tk
en el mismo interprete (la segunda pierde los layouts de los estilos).

    python -m tests.test_dpi_layout_gui
"""

import os
import subprocess
import sys
import traceback

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import tkinter as tk
except ImportError:
    print("Tk no disponible — test omitido")
    sys.exit(0)

# Equipos donde se reporto el problema: (etiqueta, area util, tk scaling).
#
# `tk scaling` es lo que simula el escalado de Windows: la aplicacion corre
# con conciencia de DPI (ttkbootstrap llama a SetProcessDPIAware), asi que en
# un equipo al 150 % Tk recibe 144 dpi, `tk scaling` vale 2,0 y TODA fuente
# declarada en puntos se dibuja 1,5 veces mas grande. Ese es el mecanismo del
# bug: el contenido crecia y las ventanas, con su tamano en pixeles fijos, no.
# None = dejar la escala nativa de esta pantalla.
PANTALLAS = [
    ("1366x768 al 100 % (equipo de desarrollo)", 1366, 728, None),
    ("1920x1080 al 150 % -> 144 dpi, fuentes x1,5", 1896, 1016, 2.0),
    ("1600x900 al 125 % -> 120 dpi, fuentes x1,25", 1600, 856, 5 / 3),
    ("1366x768 al 125 % -> 120 dpi en un portatil chico", 1366, 728, 5 / 3),
]


# ═════════════════════════════════════════════════════════════════════════
# Modo hijo: mide todas las ventanas para UNA pantalla simulada
# ═════════════════════════════════════════════════════════════════════════

def _medir_pantalla(area_w, area_h, escala_tk=None):
    import ttkbootstrap as ttk
    from gui.main_window import MainWindow
    from gui.scaling import forget_screen_scale, screen_scale

    fallos = []

    def check(condicion, titulo, detalle=""):
        estado = "OK   " if condicion else "FALLO"
        print(f"  {estado}  {titulo}")
        if not condicion:
            if detalle:
                print(f"         {detalle}")
            fallos.append(titulo)

    # Los dialogos bloqueantes llaman `wait_window()` en su constructor: se
    # neutraliza para poder medirlos (no se corre ningun mainloop).
    tk.Toplevel.wait_window = lambda self, *a, **k: None
    ttk.Toplevel.wait_window = lambda self, *a, **k: None

    def barras_de_botones(win):
        """Frames cuyos hijos son todos botones: la barra del pie.

        No se entra a los `tk.Canvas`: lo que vive adentro de uno es una
        lista con scroll (la de issues del reporte de salud), y ahi quedar
        por debajo del borde es lo normal —se llega con la rueda—, no un
        recorte.
        """
        barras = []

        def visitar(w):
            if isinstance(w, tk.Canvas):
                return
            hijos = w.winfo_children()
            if hijos and all(isinstance(h, (ttk.Button, tk.Button))
                             for h in hijos):
                barras.append(w)
            for h in hijos:
                visitar(h)

        visitar(win)
        return barras

    def medir(nombre, win):
        win.deiconify()
        win.update()          # mapea la ventana: sin esto winfo_height() = 1
        w, h = win.winfo_width(), win.winfo_height()
        rw, rh = win.winfo_reqwidth(), win.winfo_reqheight()

        check(w <= area_w and h <= area_h,
              f"{nombre}: entra en la pantalla",
              f"mide {w}x{h} y el area util es {area_w}x{area_h}")

        # El contenido no puede pedir mas de lo que la ventana tiene, salvo
        # que la ventana ya este contra el tope de la pantalla: ahi manda el
        # encogido del area elastica y no hay nada mas que dar.
        tope_w = w >= area_w - 24
        tope_h = h >= area_h - 24
        check(rw <= w + 1 or tope_w,
              f"{nombre}: el contenido no queda cortado a lo ancho",
              f"pide {rw} px y tiene {w}")
        check(rh <= h + 1 or tope_h,
              f"{nombre}: el contenido no queda cortado a lo alto",
              f"pide {rh} px y tiene {h}")

        for barra in barras_de_botones(win):
            try:
                alto = barra.winfo_height()
                fondo = barra.winfo_rooty() - win.winfo_rooty() + alto
                etiquetas = " / ".join(
                    b.cget("text") for b in barra.winfo_children()
                    if b.cget("text"))
            except tk.TclError:
                continue
            if alto <= 1:
                detalle = ("Tk le dio 0 px de alto: la barra existe pero el "
                           "alumno no ve ningun boton")
            else:
                detalle = (f"su borde inferior cae en y={fondo} y la ventana "
                           f"mide {h}: queda por debajo del area visible")
            check(alto > 1 and fondo <= h,
                  f"{nombre}: la barra [{etiquetas}] queda visible", detalle)

    from gui.dialogs.about_dialog import AboutDialog
    from gui.dialogs.units_dialog import UnitsDialog
    from gui.dialogs.gravity_dialog import GravityDialog
    from gui.dialogs.material_dialog import MaterialDialog
    from gui.dialogs.element_type_dialog import ElementTypeDialog
    from gui.dialogs.analysis_type_dialog import AnalysisTypeDialog
    from gui.dialogs.memoria_style_dialog import MemoriaStyleDialog
    from gui.dialogs.health_report_dialog import HealthReportDialog
    from models.model_health import validate_project

    app = MainWindow()
    root = app.root
    if escala_tk is not None:
        # Simular el escalado de Windows: sube el dpi que ve Tk, con lo que
        # cada fuente en puntos —todas las del programa— crece, y con ella
        # cada widget. Es exactamente lo que pasa en el equipo del reporte.
        root.tk.call("tk", "scaling", escala_tk)
        forget_screen_scale(root)
        app._apply_minsize()
    root.update()
    print(f"  ---  dpi que ve Tk: {root.winfo_fpixels('1i'):.0f} | "
          f"factor de escala: {screen_scale(root):.2f}")

    # La ventana principal se maximiza sola: el `minsize` es lo que no la
    # dejaba bajar del tamano del escritorio disponible.
    mw, mh = root.minsize()
    check(mw <= area_w and mh <= area_h,
          f"MainWindow: el minsize ({mw}x{mh}) entra en {area_w}x{area_h}",
          "un minsize mayor que la pantalla deja la barra de estado y el "
          "borde derecho fuera del escritorio, sin forma de recuperarlos")
    check(app.status_frame.winfo_height() > 1
          and app.status_frame.winfo_rooty() - root.winfo_rooty()
          + app.status_frame.winfo_height() <= root.winfo_height(),
          "MainWindow: la barra de estado queda dentro de la ventana")

    proyecto = app.project
    for nombre, fabrica in [
        ("AboutDialog", lambda: AboutDialog(root)),
        ("UnitsDialog", lambda: UnitsDialog(root, proyecto, app)),
        ("GravityDialog", lambda: GravityDialog(root, proyecto, app)),
        ("MaterialDialog", lambda: MaterialDialog(root, proyecto, app)),
        ("ElementTypeDialog", lambda: ElementTypeDialog(root, proyecto, app)),
        ("AnalysisTypeDialog", lambda: AnalysisTypeDialog(root, proyecto, app)),
        ("MemoriaStyleDialog", lambda: MemoriaStyleDialog(root)),
        ("HealthReportDialog",
         lambda: HealthReportDialog(root, validate_project(proyecto),
                                    proyecto, app)),
    ]:
        try:
            dlg = fabrica()
            win = (getattr(dlg, "dialog", None) or getattr(dlg, "_top", None)
                   or getattr(dlg, "top", None))
            if win is None and isinstance(dlg, tk.Toplevel):
                win = dlg
            medir(nombre, win)
            try:
                win.grab_release()
            except tk.TclError:
                pass
            win.destroy()
        except Exception as exc:
            check(False, f"{nombre}: abre sin excepcion",
                  f"{type(exc).__name__}: {exc}")
            traceback.print_exc()

    root.destroy()
    return fallos


# ═════════════════════════════════════════════════════════════════════════
# Modo padre: una pantalla simulada por subproceso
# ═════════════════════════════════════════════════════════════════════════

def _correr_todas():
    total = 0
    for etiqueta, ancho, alto, escala in PANTALLAS:
        print(f"\n[{etiqueta}]")
        entorno = dict(os.environ, EDUFEM_AREA_UTIL=f"{ancho}x{alto}")
        orden = [sys.executable, "-m", "tests.test_dpi_layout_gui",
                 "--area", f"{ancho}x{alto}"]
        if escala is not None:
            orden += ["--escala", f"{escala:.6f}"]
        proc = subprocess.run(
            orden, cwd=RAIZ, env=entorno, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        print(proc.stdout.rstrip())
        if proc.returncode != 0:
            total += 1
            if proc.stderr.strip():
                print(proc.stderr.rstrip()[-1500:])
    print("\n" + "=" * 62)
    if total:
        print(f"  {total} pantalla(s) con ventanas fuera de lugar")
        return 1
    print(f"  Toda ventana entra y conserva sus botones "
          f"en las {len(PANTALLAS)} pantallas probadas")
    return 0


if __name__ == "__main__":
    if "--area" in sys.argv:
        crudo = sys.argv[sys.argv.index("--area") + 1]
        a_w, a_h = (int(v) for v in crudo.split("x"))
        os.environ["EDUFEM_AREA_UTIL"] = crudo
        esc = None
        if "--escala" in sys.argv:
            esc = float(sys.argv[sys.argv.index("--escala") + 1])
        sys.exit(1 if _medir_pantalla(a_w, a_h, esc) else 0)
    sys.exit(_correr_todas())
