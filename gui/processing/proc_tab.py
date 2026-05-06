"""
ProcessTab: Panel izquierdo de Proceso.

Contiene la sub-pestana "Modulos Educativos" con M1..M6 (mapeo, B, D, K,
ensamblaje, fuerzas equivalentes). La calidad de malla migro a un modulo
educativo de pre-proceso (M0).
"""

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

        self._build_panel()

    def _build_panel(self):
        # Banner colorido naranja (identidad visual de la fase PROCESO)
        build_phase_banner(
            self.frame,
            color=PHASE_PROC_COLOR,
            icon="⚙",
            title="PROCESO",
            subtitle="Modulos educativos del calculo FEM",
        )

        self.notebook = ttk.Notebook(self.frame, bootstyle=PHASE_PROC_BOOTSTYLE)
        self.notebook.pack(fill=BOTH, expand=YES)

        # Sub-tab unico: Modulos Educativos (M1..M6)
        self.edu_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.edu_frame, text="  🎓 Modulos Educativos  ")
        self._build_education_tab()

    def _build_education_tab(self):
        """Lista de modulos educativos de la fase de calculo."""
        from education.module_launcher import (
            list_modules_for_phase, open_module,
        )

        def _on_open(mod_key):
            ok = open_module(
                parent_tk=self.frame.winfo_toplevel(),
                project=self.project,
                mod_key=mod_key,
                mesh_canvas=self.main_window.mesh_canvas,
            )
            if ok:
                self.main_window.set_status(f"Modulo educativo abierto: {mod_key}")

        render_module_buttons(
            self.edu_frame,
            modules=list_modules_for_phase("proc"),
            on_open=_on_open,
            bootstyle=f"{PHASE_PROC_BOOTSTYLE}-outline",
            header_text="Modulos Educativos FEM",
            header_color=PHASE_PROC_COLOR,
            subtitle=("Explore interactivamente los conceptos del Metodo de\n"
                      "Elementos Finitos con datos de su modelo actual."),
        )

    def refresh(self):
        """Refresca la pestana de proceso (no-op: contenido independiente)."""
        pass
