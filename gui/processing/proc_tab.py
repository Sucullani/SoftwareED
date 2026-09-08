"""
ProcessTab: Panel izquierdo de Proceso.

Contiene la sub-pestana "Modulos Educativos" con M1..M7 (mapeo+shape funcs,
Jacobiano, D, B, K+Gauss, fuerzas equivalentes, ensamblaje).

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
from gui.widgets.module_launcher_panel import render_module_buttons


class ProcessTab:
    """Panel de Proceso con la sub-pestana de modulos educativos."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        self._panel = None
        self._canvas_cb_chain = None  # callback previo del canvas (para chain)

        self._build_panel()

    def _build_panel(self):
        build_phase_banner(
            self.frame,
            color=PHASE_PROC_COLOR,
            icon="⚙",
            title="PROCESO",
            subtitle="Modulos educativos del calculo MEF",
        )

        self.notebook = ttk.Notebook(self.frame, bootstyle=PHASE_PROC_BOOTSTYLE)
        self.notebook.pack(fill=BOTH, expand=YES)

        self.edu_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.edu_frame, text="  🎓 Modulos Educativos  ")
        self._build_education_tab()

    def _build_education_tab(self):
        """Lista de modulos educativos de la fase de calculo."""
        from education.module_launcher import (
            list_modules_for_phase, open_module, module_label, GLOBAL_MODULES,
        )

        def _on_open(mod_key):
            # Si hay UN elemento seleccionado en el canvas lo pasamos
            # directo; si no, el modulo se abre igual y espera el click del
            # alumno sobre el lienzo (no hay dialogo intermedio).
            elem_id = self._current_selected_element()
            ok = open_module(
                parent_tk=self.frame.winfo_toplevel(),
                project=self.project,
                mod_key=mod_key,
                mesh_canvas=self.main_window.mesh_canvas,
                elem_id=elem_id,
            )
            if ok:
                # `open_module` puede haber elegido el elemento por su
                # cuenta (auto-pick cuando la malla tiene uno solo) y en
                # ese caso lo deja seleccionado en el canvas: releerlo de
                # ahi evita duplicar esa regla.
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
            return ok  # el panel marca ✓ solo si realmente abrio

        self._panel = render_module_buttons(
            self.edu_frame,
            modules=list_modules_for_phase("proc"),
            on_open=_on_open,
            bootstyle=f"{PHASE_PROC_BOOTSTYLE}-outline",
            header_text="Modulos Educativos MEF",
            header_color=PHASE_PROC_COLOR,
            # El boton gris NO esta deshabilitado: abre el modulo igual y
            # este espera el click. Decirlo evita que el alumno crea que
            # necesita seleccionar antes de poder mirar nada.
            subtitle=("Clickeá un elemento en el lienzo y los módulos se "
                      "activan sobre él.\nTambién podés abrir uno primero y "
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
