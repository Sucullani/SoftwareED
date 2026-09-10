"""
ProcessTab: Panel izquierdo de Proceso.

La fase es "del elemento al sistema K·u = F", y desde el rediseño del
2026-09-09 el panel lo dice con dos piezas, de arriba hacia abajo:

1. **Banner con la tira del metodo** (`gui/widgets/method_strip.py`): los
   chips `N › J › B › D › kₑ › F › K` son los siete pasos del calculo, 1:1
   con los modulos ①..⑦. Cada chip abre su modulo y su color dice si el
   alumno ya paso por ese paso (blanco), lo tiene abierto (ambar) o no lo
   visito (atenuado). Reemplaza al breadcrumb glifico de la barra de
   estado.
2. **Panel de modulos** (`render_module_buttons`), directo en el frame de la
   fase: no hay Notebook (lo hubo, con UNA sola pestana, o sea un control
   que no controlaba nada). El Pre-Proceso si tiene Notebook porque ahi
   conviven las 5 tablas + Educacion.

La lectura estructural del sistema (forma de K que la malla decide, GDL
restringidos, incognitas) vive en **M7** (`education/mod07_assembly.py`):
vivio unas horas aca como panel propio y el autor decidio que pertenece
al modulo de ensamblaje, que es donde K se construye.

Iluminacion reactiva (propuesta UX 2026): los botones de modulos
por-elemento estan desaturados cuando no hay seleccion. Al clickear un
elemento en el MeshCanvas, los botones pasan a color de fase y muestran
un chip `#N` con el id del elemento. Tras abrir un modulo, queda un ✓
permanente en la sesion como indicador de progreso.
"""

import traceback

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config.settings import PHASE_PROC_COLOR, PHASE_PROC_BOOTSTYLE
from gui.widgets.phase_banner import build_phase_banner
from gui.widgets.method_strip import MethodStrip
from gui.widgets.module_launcher_panel import render_module_buttons


# Chips de la tira del metodo: (mod_key, texto). El tooltip sale de
# `module_label` (fuente unica del nombre visible) + el atajo Ctrl+N.
METHOD_STEPS = [
    ("mod01", "N"),
    ("mod02", "J"),
    ("mod03", "B"),
    ("mod04", "D"),
    ("mod05", "kₑ"),
    ("mod06", "F"),
    ("mod07", "K"),
]


class ProcessTab:
    """Panel de Proceso: tira del metodo + lanzador de modulos."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        self._panel = None
        self._canvas_cb_chain = None  # callback previo del canvas (para chain)
        self.method_strip = None

        self._build_panel()

    def _build_panel(self):
        banner = build_phase_banner(
            self.frame,
            color=PHASE_PROC_COLOR,
            icon="⚙",
            title="PROCESO",
            subtitle=None,          # a la derecha va la tira del metodo
        )
        self._build_method_strip(banner)

        # Panel de modulos directo en el frame de la fase (sin Notebook de
        # una sola pestana — ver el docstring del modulo).
        self.edu_frame = ttk.Frame(self.frame)
        self.edu_frame.pack(fill=BOTH, expand=YES)
        self._build_education_panel()

    def _build_method_strip(self, banner):
        try:
            from education.module_launcher import module_label
        except Exception:
            module_label = None
        steps = []
        for mod_key, text in METHOD_STEPS:
            tip = ""
            if module_label is not None:
                n = int(mod_key[3:])
                tip = f"Abrir {module_label(mod_key)}  (Ctrl+{n})"
            steps.append((mod_key, text, tip))
        self.method_strip = MethodStrip(
            banner, steps, bg=PHASE_PROC_COLOR, on_click=self._open_module,
        )
        self.method_strip.frame.pack(side=LEFT, padx=(12, 8))
        # El estado activo/visitado llega por el broadcast de overlays (vale
        # tambien para los que se abren con Ctrl+N o desde el menu).
        try:
            from education.overlay_module import subscribe_overlay_change
            subscribe_overlay_change(self._on_overlay_change)
        except Exception:
            # Sin la suscripcion la tira nunca se ilumina.
            traceback.print_exc()

    def _on_overlay_change(self, main_window, active_mod_keys):
        if main_window is not self.main_window:
            return
        if self.method_strip is not None:
            self.method_strip.set_active(active_mod_keys)

    def _open_module(self, mod_key):
        """Abre el modulo desde la tira (mismo camino que el boton)."""
        try:
            self._open_and_report(mod_key)
        except Exception:
            traceback.print_exc()
            self.main_window.set_status("No se pudo abrir el módulo educativo.")

    def _open_and_report(self, mod_key):
        from education.module_launcher import open_module, module_label

        # Si hay UN elemento seleccionado en el canvas lo pasamos directo;
        # si no, el modulo se abre igual y espera el click del alumno sobre
        # el lienzo (no hay dialogo intermedio).
        elem_id = self._current_selected_element()
        ok = open_module(
            parent_tk=self.frame.winfo_toplevel(),
            project=self.project,
            mod_key=mod_key,
            mesh_canvas=self.main_window.mesh_canvas,
            elem_id=elem_id,
        )
        if ok:
            # `open_module` puede haber elegido el elemento por su cuenta
            # (auto-pick cuando la malla tiene uno solo) y en ese caso lo
            # deja seleccionado en el canvas: releerlo de ahi evita duplicar
            # esa regla.
            target = self._current_selected_element()
            label = module_label(mod_key)
            if target is None:
                self.main_window.set_status(
                    f"{label} abierto — clickeá un elemento en el "
                    f"lienzo para verlo sobre él"
                )
            else:
                self.main_window.set_status(
                    f"{label} abierto sobre el elemento #{target}"
                )
            if self._panel is not None:
                self._panel.mark_visited(mod_key)
        return ok

    def _build_education_panel(self):
        """Lanzador de los modulos educativos de la fase de calculo."""
        from education.module_launcher import list_modules_for_phase, GLOBAL_MODULES

        self._panel = render_module_buttons(
            self.edu_frame,
            modules=list_modules_for_phase("proc"),
            on_open=self._open_and_report,   # el panel marca ✓ solo si abrio
            bootstyle=f"{PHASE_PROC_BOOTSTYLE}-outline",
            header_text="Módulos Educativos MEF",
            header_color=PHASE_PROC_COLOR,
            # El boton gris NO esta deshabilitado: abre el modulo igual y
            # este espera el click. Decirlo evita que el alumno crea que
            # necesita seleccionar antes de poder mirar nada.
            subtitle=("Clickeá un elemento en el lienzo y los módulos se "
                      "activan sobre él. También podés abrir uno primero y "
                      "elegir el elemento después."),
            global_modules=GLOBAL_MODULES,
        )

    # ── sincronizacion con MeshCanvas ─────────────────────────────────
    def wire_canvas(self):
        """Engancha el panel al MeshCanvas para reaccionar a la seleccion.

        Llamado tardiamente desde MainWindow._build_main_layout (despues
        de crear el canvas). Encadena con cualquier callback previo en
        `on_selection_changed` para no pisarlo.

        Idempotente: marcamos el wrapper con `_proc_edu_chain` para
        detectar re-invocaciones (set_project, etc.) y evitar duplicar
        la cadena.
        """
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None or self._panel is None:
            return
        prev = canvas.on_selection_changed
        if prev is not None and getattr(prev, "_proc_edu_chain", False):
            return  # ya cableado
        self._canvas_cb_chain = prev

        def _chained(sel: dict, _prev=prev):
            if _prev is not None:
                try:
                    _prev(sel)
                except Exception:
                    # El callback previo es el del pre_tab (filas fantasma,
                    # tag `canvas_selected`): si falla, las tablas quedan
                    # desincronizadas del lienzo. Traza a stderr, y seguimos
                    # con lo nuestro para no arrastrar el chip al fallo.
                    traceback.print_exc()
            self._on_selection_changed(sel)

        _chained._proc_edu_chain = True
        canvas.on_selection_changed = _chained
        # Estado inicial coherente con la seleccion actual del canvas.
        try:
            self._on_selection_changed(canvas.get_selection())
        except Exception:
            # Sin esto el chip `#N` arranca desfasado de la seleccion real.
            traceback.print_exc()

    def _on_selection_changed(self, sel: dict):
        """Refresca el chip `#N` segun la seleccion del canvas."""
        elems = sel.get("elements", set()) if sel else set()
        elem_id = next(iter(elems)) if len(elems) == 1 else None
        if self._panel is not None:
            self._panel.update_selection(elem_id)

    def _current_selected_element(self):
        """Retorna el unico elemento seleccionado en el canvas o None."""
        try:
            sel = self.main_window.mesh_canvas.get_selection()
            elems = sel.get("elements", set())
            return next(iter(elems)) if len(elems) == 1 else None
        except Exception:
            # El modulo se abriria sin elemento (esperando el click) y el
            # motivo real quedaria invisible: dejamos traza.
            traceback.print_exc()
            return None

    def refresh(self):
        """Refresca la pestana de proceso (no-op: contenido independiente)."""
        pass
