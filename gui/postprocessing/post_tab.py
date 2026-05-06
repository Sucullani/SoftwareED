"""
PostProcessTab: Panel izquierdo de Post-Proceso.
Se resuelve automaticamente al activar la pestana.
Radio buttons actualizan la visualizacion en tiempo real.
Usa el MeshCanvas compartido con gradiente e isolineas.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import numpy as np

from config.settings import (
    DECIMALS_FORCE, DECIMALS_STRESS, DECIMALS_DISPLACEMENT, fmt,
    PHASE_POST_COLOR, PHASE_POST_BOOTSTYLE,
    HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR, LABEL_BG,
)
from gui.widgets.phase_banner import build_phase_banner
from gui.widgets.module_launcher_panel import render_module_buttons
from models.model_health import validate_project, Severity


class PostProcessTab:
    """Panel de Post-Proceso con auto-solve y visualizacion reactiva."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)

        # Estado de resultados
        self.solution = None
        self.nodal_stresses = None

        self._build_panel()

    def _build_panel(self):
        """Construye el panel con sub-pestanas."""
        # Banner colorido verde (identidad visual de POST-PROCESO)
        build_phase_banner(
            self.frame,
            color=PHASE_POST_COLOR,
            icon="📊",
            title="POST-PROCESO",
            subtitle="Resultados · esfuerzos · interpretacion pedagogica",
        )

        # Banner de salud del modelo (warnings). Solo se muestra cuando
        # hay warnings tras validar; los errores criticos abren el modal
        # bloqueante en su lugar. Construye y oculta -- se rellena cuando
        # auto_solve detecta warnings.
        self._build_health_banner()

        self.notebook = ttk.Notebook(self.frame, bootstyle=PHASE_POST_BOOTSTYLE)
        self.notebook.pack(fill=BOTH, expand=YES)

        # Sub-tab 1: Visualizacion
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="  Visualización  ")
        self._build_visualization_tab()

        # Sub-tab 2: Resultados numericos
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="  Resultados  ")
        self._build_results_tab()

        # Sub-tab 3: Modulos educativos (M7 discontinuidad, M8 principales)
        self.education_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.education_frame, text="  🎓 Educacion  ")
        self._build_education_tab()

    def _build_education_tab(self):
        """Modulos educativos del POST-PROCESO."""
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
            self.education_frame,
            modules=list_modules_for_phase("post"),
            on_open=_on_open,
            bootstyle=f"{PHASE_POST_BOOTSTYLE}-outline",
            header_text="Modulos Educativos · Post-Proceso",
            header_color=PHASE_POST_COLOR,
            subtitle=("Interpretacion de resultados: continuidad de esfuerzos,\n"
                      "direcciones principales y circulo de Mohr.\n"
                      "Requieren modelo resuelto (F5)."),
        )

    # ═════════════════════════════════════════════════════════════════════
    # SUB-TAB: VISUALIZACION
    # ═════════════════════════════════════════════════════════════════════

    def _build_visualization_tab(self):
        """Controles de visualizacion con auto-update."""
        # Scroll container
        scroll_canvas = tk.Canvas(self.viz_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.viz_frame, orient=VERTICAL,
                                  command=scroll_canvas.yview)
        container = ttk.Frame(scroll_canvas)
        container.bind(
            "<Configure>",
            lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        )
        scroll_canvas.create_window((0, 0), window=container, anchor=NW)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        scroll_canvas.pack(side=LEFT, fill=BOTH, expand=YES)

        # ─── Estado del analisis ─────────────────────────────────────────
        self.status_frame = ttk.Labelframe(container, text="Estado del Análisis",
                                           bootstyle="success")
        self.status_frame.pack(fill=X, padx=10, pady=(10, 5))

        self.solve_status = ttk.Label(
            self.status_frame, text="Estado: Sin resolver",
            font=("Segoe UI", 10, "bold"), foreground="#ffa726",
        )
        self.solve_status.pack(padx=10, pady=5, anchor=W)

        self.model_info = ttk.Label(
            self.status_frame, text="",
            font=("Consolas", 8), foreground="#aaa", wraplength=360,
        )
        self.model_info.pack(padx=10, pady=(0, 5), anchor=W)

        # ─── Tipo de Resultado ───────────────────────────────────────────
        result_frame = ttk.Labelframe(container, text="Tipo de Resultado",
                                      bootstyle="danger")
        result_frame.pack(fill=X, padx=10, pady=5)

        self.result_var = tk.StringVar(value="VM")

        results = [
            ("Desplazamiento Ux", "Ux"),
            ("Desplazamiento Uy", "Uy"),
            ("Magnitud |U|", "Umag"),
            ("Esfuerzo Normal σx", "Sx"),
            ("Esfuerzo Normal σy", "Sy"),
            ("Esfuerzo Cortante τxy", "Txy"),
            ("Esfuerzo Principal σ1", "S1"),
            ("Esfuerzo Principal σ2", "S2"),
            ("Von Mises", "VM"),
        ]

        for text, value in results:
            ttk.Radiobutton(
                result_frame, text=text, value=value,
                variable=self.result_var, bootstyle="danger",
                command=self._on_result_changed,
            ).pack(anchor=W, padx=15, pady=1)

        # ─── Opciones de Deformada ───────────────────────────────────────
        deform_frame = ttk.Labelframe(container, text="Malla Deformada",
                                      bootstyle="info")
        deform_frame.pack(fill=X, padx=10, pady=5)

        self.show_deformed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            deform_frame, text="Mostrar malla deformada",
            variable=self.show_deformed_var, bootstyle="round-toggle",
            command=self._on_result_changed,
        ).pack(anchor=W, padx=15, pady=5)

        scale_row = ttk.Frame(deform_frame)
        scale_row.pack(fill=X, padx=15, pady=(0, 5))
        ttk.Label(scale_row, text="Factor de escala:").pack(side=LEFT)
        self.scale_var = tk.DoubleVar(value=1.0)
        scale_entry = ttk.Entry(scale_row, textvariable=self.scale_var, width=8)
        scale_entry.pack(side=LEFT, padx=5)
        scale_entry.bind("<Return>", lambda e: self._on_result_changed())

        # ─── Opciones de Isolineas ───────────────────────────────────────
        iso_frame = ttk.Labelframe(container, text="Isolíneas / Curvas de Nivel",
                                   bootstyle="warning")
        iso_frame.pack(fill=X, padx=10, pady=5)

        self.show_isolines_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            iso_frame, text="Mostrar isolíneas",
            variable=self.show_isolines_var, bootstyle="round-toggle",
            command=self._on_result_changed,
        ).pack(anchor=W, padx=15, pady=5)

        count_row = ttk.Frame(iso_frame)
        count_row.pack(fill=X, padx=15, pady=(0, 5))
        ttk.Label(count_row, text="Número de niveles:").pack(side=LEFT)
        self.isoline_count_var = tk.IntVar(value=10)
        iso_spin = ttk.Spinbox(
            count_row, from_=3, to=30, width=5,
            textvariable=self.isoline_count_var,
            command=self._on_result_changed,
        )
        iso_spin.pack(side=LEFT, padx=5)
        iso_spin.bind("<Return>", lambda e: self._on_result_changed())

    # ═════════════════════════════════════════════════════════════════════
    # SUB-TAB: RESULTADOS NUMERICOS
    # ═════════════════════════════════════════════════════════════════════

    def _build_results_tab(self):
        """Tabla de resultados numericos."""
        container = ttk.Frame(self.results_frame)
        container.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        ttk.Label(
            container, text="Tabla de Resultados Numéricos",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, padx=10, pady=(10, 5))

        sel_frame = ttk.Frame(container)
        sel_frame.pack(fill=X, padx=10, pady=5)

        ttk.Label(sel_frame, text="Mostrar:").pack(side=LEFT)
        self.table_type_var = tk.StringVar(value="Desplazamientos")
        ttk.Combobox(
            sel_frame, textvariable=self.table_type_var,
            values=["Desplazamientos", "Esfuerzos", "Reacciones"],
            state="readonly", width=18
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            sel_frame, text="Actualizar", bootstyle="danger-outline",
            command=self._update_table
        ).pack(side=LEFT, padx=5)

        table_frame = ttk.Frame(container)
        table_frame.pack(fill=BOTH, expand=YES, padx=10, pady=5)

        columns = ("node", "v1", "v2", "v3", "v4", "v5", "v6")
        self.results_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            bootstyle="danger", height=15, selectmode="extended",
        )
        self.results_tree.heading("node", text="Nodo", anchor=CENTER)
        self.results_tree.heading("v1", text="Ux", anchor=CENTER)
        self.results_tree.heading("v2", text="Uy", anchor=CENTER)
        self.results_tree.heading("v3", text="|U|", anchor=CENTER)
        self.results_tree.heading("v4", text="", anchor=CENTER)
        self.results_tree.heading("v5", text="", anchor=CENTER)
        self.results_tree.heading("v6", text="", anchor=CENTER)
        for col in columns:
            self.results_tree.column(col, width=60, anchor=CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL,
                                  command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        self.results_tree.pack(fill=BOTH, expand=YES, side=LEFT)
        scrollbar.pack(fill=Y, side=RIGHT)

        # Atajos de copiado (TSV al portapapeles, pegable en Excel)
        self.results_tree.bind("<Control-c>", self._copy_results_tsv)
        self.results_tree.bind("<Control-C>", self._copy_results_tsv)
        self.results_tree.bind("<Control-a>", self._select_all_results)
        self.results_tree.bind("<Control-A>", self._select_all_results)

    # ═════════════════════════════════════════════════════════════════════
    # AUTO-SOLVE (se llama al activar la pestana Post-Proceso)
    # ═════════════════════════════════════════════════════════════════════

    def _build_health_banner(self):
        """Construye el banner de warnings (oculto por defecto). Aparece
        cuando `auto_solve` detecta warnings no-criticos. Es no-bloqueante:
        solo informa, el usuario puede cerrarlo con la X."""
        self.health_banner = tk.Frame(
            self.frame, bg=LABEL_BG, highlightthickness=1,
            highlightbackground=HEALTH_WARNING_COLOR,
        )
        # No hace pack -> queda oculto hasta que se llame
        # `_show_health_banner`.
        self._health_banner_visible = False

        inner = tk.Frame(self.health_banner, bg=LABEL_BG)
        inner.pack(fill=X, padx=10, pady=8)

        # Icono + texto
        tk.Label(
            inner, text="⚠", fg=HEALTH_WARNING_COLOR, bg=LABEL_BG,
            font=("Segoe UI", 14, "bold"),
        ).pack(side=LEFT, padx=(0, 10))

        self.health_banner_text = tk.Label(
            inner, text="", fg="#e8e8ea", bg=LABEL_BG,
            font=("Segoe UI", 9), justify=LEFT, anchor=W, wraplength=600,
        )
        self.health_banner_text.pack(side=LEFT, fill=X, expand=YES)

        # Botones de accion (a la derecha)
        btn_frame = tk.Frame(inner, bg=LABEL_BG)
        btn_frame.pack(side=RIGHT)

        ttk.Button(
            btn_frame, text="Ver detalle",
            bootstyle="warning-outline",
            command=self._on_show_health_details,
        ).pack(side=LEFT, padx=(0, 4))

        ttk.Button(
            btn_frame, text="✕", bootstyle="secondary-link", width=3,
            command=self._hide_health_banner,
        ).pack(side=LEFT)

    def _show_health_banner(self, report):
        """Muestra el banner con el resumen de warnings del report."""
        self._last_report = report
        n = len(report.warnings)
        if n == 1:
            txt = f"1 advertencia detectada: {report.warnings[0].message}"
        else:
            txt = (f"{n} advertencias en el modelo. "
                   f"El analisis procedera, pero conviene revisar.")
        self.health_banner_text.config(text=txt)
        if not self._health_banner_visible:
            self.health_banner.pack(fill=X, before=self.notebook,
                                    padx=8, pady=(0, 6))
            self._health_banner_visible = True

    def _hide_health_banner(self):
        if self._health_banner_visible:
            self.health_banner.pack_forget()
            self._health_banner_visible = False

    def _on_show_health_details(self):
        """Abre el HealthReportDialog con el ultimo report (modal pero
        sin bloquear el solve, porque ya se resolvio o se va a resolver).
        """
        if not hasattr(self, "_last_report") or self._last_report is None:
            return
        from gui.dialogs.health_report_dialog import HealthReportDialog
        dlg = HealthReportDialog(
            self.frame.winfo_toplevel(), self._last_report, self.project,
            main_window=self.main_window, allow_continue=False,
        )
        dlg.show()
        # Si el usuario aplico fixes, re-validar y refrescar el banner
        if dlg.fixes_applied > 0:
            new_report = validate_project(self.project)
            if new_report.has_warnings():
                self._show_health_banner(new_report)
            else:
                self._hide_health_banner()
            self._last_report = new_report

    def auto_solve(self):
        """Resuelve automaticamente si hay modelo valido y no esta resuelto.

        Antes del solve, ejecuta `validate_project` (panel de salud):
          - errores criticos -> abre HealthReportDialog modal y bloquea
            hasta que el usuario los corrija o decida "resolver de todos
            modos"
          - solo warnings -> muestra banner no-bloqueante arriba del
            notebook y procede con el solve
          - modelo sano -> oculta el banner y resuelve directo
        """
        # Si ya esta resuelto, solo actualizar display (no re-validar para
        # evitar abrir el modal en cada cambio de tab post-solve).
        if self.solution is not None and self.project.is_solved:
            return

        # ─── Validacion previa ────────────────────────────────────────
        report = validate_project(self.project)

        if report.has_errors():
            # Modal bloqueante. El usuario puede aplicar fixes y/o
            # continuar/cancelar. Tras cerrar, re-validamos: si fixes
            # resolvieron todos los errores, seguimos al solve; si no,
            # respetamos la decision del usuario.
            from gui.dialogs.health_report_dialog import HealthReportDialog
            dlg = HealthReportDialog(
                self.frame.winfo_toplevel(), report, self.project,
                main_window=self.main_window, allow_continue=True,
            )
            result = dlg.show()
            # Re-validar tras posibles auto-fixes
            report = validate_project(self.project)
            if report.has_errors() and result != "continue":
                # Usuario cancelo y aun hay errores. Lo regresamos al
                # Pre-Proceso para que pueda corregirlos.
                self.solve_status.config(
                    text=f"✗ {len(report.errors)} error(es) sin resolver — "
                         f"corrija desde Pre-Proceso",
                    foreground=HEALTH_ERROR_COLOR,
                )
                self._hide_health_banner()
                self._last_report = report
                try:
                    self.main_window.notebook.select(0)
                    self.main_window.set_status(
                        "Corrija los errores antes de resolver"
                    )
                except Exception:
                    pass
                return
            # Si quedaron warnings tras los fixes, mostrar banner
            if report.has_warnings():
                self._show_health_banner(report)
            else:
                self._hide_health_banner()
        elif report.has_warnings():
            self._show_health_banner(report)
            self._last_report = report
        else:
            self._hide_health_banner()
            self._last_report = report

        # Chequeos de pre-requisitos minimos (redundantes con el
        # validador, pero el usuario puede haber clickeado "continuar
        # igual" en el modal -> respetar su decision aqui significa
        # intentar resolver y dejar que el solver tire una excepcion
        # explicita si no puede).
        if not self.project.elements:
            self.solve_status.config(
                text="Sin modelo — defina nodos y elementos",
                foreground=HEALTH_ERROR_COLOR,
            )
            return

        if not self.project.boundary_conditions:
            self.solve_status.config(
                text="Sin restricciones — defina condiciones de contorno",
                foreground=HEALTH_ERROR_COLOR,
            )
            return

        self.solve_status.config(text="Resolviendo...", foreground="#4fc3f7")
        self.frame.update_idletasks()

        try:
            from fem.solver import solve_system
            from fem.stress import compute_all_stresses

            self.solution = solve_system(self.project)
            _, self.nodal_stresses = compute_all_stresses(
                self.project, self.solution
            )

            self.project.is_solved = True
            self.project.displacements = self.solution["u"]
            self.project.global_K = self.solution["K"]
            self.project.global_F = self.solution["F"]

            u = self.solution["u"]
            R = self.solution["reactions"]
            restrained = self.solution["restrained_dofs"]

            max_ux = max(abs(u[i]) for i in range(0, len(u), 2))
            max_uy = max(abs(u[i]) for i in range(1, len(u), 2))

            info = (
                f"GDL: {len(u)} total, "
                f"{len(self.solution['free_dofs'])} libres, "
                f"{len(restrained)} restringidos\n"
                f"Max |Ux|: {max_ux:.{DECIMALS_DISPLACEMENT}e}   "
                f"Max |Uy|: {max_uy:.{DECIMALS_DISPLACEMENT}e}"
            )
            self.model_info.config(text=info)
            self.solve_status.config(
                text="✓ RESUELTO — Seleccione resultado para visualizar",
                foreground="#81c784"
            )
            self.main_window.set_status("Análisis completado automáticamente.")
            self.main_window._update_status_info()
            # Refrescar estado del menú/toolbar (habilitar Exportar, etc.)
            if hasattr(self.main_window, "_refresh_menu_state"):
                self.main_window._refresh_menu_state()

            # Auto-visualizar Von Mises
            self._on_result_changed()
            self._update_table()

        except Exception as e:
            self.solve_status.config(
                text=f"✗ Error: {str(e)[:60]}",
                foreground="#ef5350"
            )
            messagebox.showerror("Error al resolver", str(e))

    # ═════════════════════════════════════════════════════════════════════
    # VISUALIZACION REACTIVA (auto-update al cambiar radio buttons)
    # ═════════════════════════════════════════════════════════════════════

    def _on_result_changed(self):
        """Callback: actualiza visualizacion al cambiar cualquier opcion."""
        if not self.solution:
            return

        result_type = self.result_var.get()
        u = self.solution["u"]
        node_values = {}

        labels = {
            "Ux": "Ux", "Uy": "Uy", "Umag": "|U|",
            "Sx": "σx", "Sy": "σy", "Txy": "τxy",
            "S1": "σ1", "S2": "σ2", "VM": "Von Mises",
        }

        for nid in sorted(self.project.nodes.keys()):
            ux = u[2 * (nid - 1)]
            uy = u[2 * (nid - 1) + 1]

            if result_type == "Ux":
                node_values[nid] = ux
            elif result_type == "Uy":
                node_values[nid] = uy
            elif result_type == "Umag":
                node_values[nid] = np.sqrt(ux**2 + uy**2)
            elif result_type in ("Sx", "Sy", "Txy", "S1", "S2", "VM"):
                stress_key = {
                    "Sx": "sigma_x", "Sy": "sigma_y", "Txy": "tau_xy",
                    "S1": "sigma_1", "S2": "sigma_2", "VM": "von_mises"
                }[result_type]
                if self.nodal_stresses and nid in self.nodal_stresses:
                    node_values[nid] = self.nodal_stresses[nid][stress_key]
                else:
                    node_values[nid] = 0.0

        label = labels.get(result_type, result_type)
        canvas = self.main_window.mesh_canvas

        # Configurar isolineas
        canvas.set_isolines(
            self.show_isolines_var.get(),
            self.isoline_count_var.get()
        )

        # Configurar deformada
        if self.show_deformed_var.get():
            canvas.displacements = u
            max_disp = np.max(np.abs(u))
            if max_disp > 0:
                coords = np.array([
                    [self.project.nodes[n].x, self.project.nodes[n].y]
                    for n in sorted(self.project.nodes.keys())
                ])
                model_size = max(
                    coords[:, 0].max() - coords[:, 0].min(),
                    coords[:, 1].max() - coords[:, 1].min()
                )
                canvas.deform_scale = model_size * 0.1 / max_disp * self.scale_var.get()
            canvas.show_deformed = True
        else:
            canvas.show_deformed = False
            canvas.displacements = None

        # Actualizar resultados (esto redibuja el canvas)
        canvas.set_result_values(node_values, label)
        self.main_window.set_status(f"Visualizando: {label}")

    # ═════════════════════════════════════════════════════════════════════
    # TABLA DE RESULTADOS
    # ═════════════════════════════════════════════════════════════════════

    def _update_table(self):
        self.results_tree.delete(*self.results_tree.get_children())
        if not self.solution:
            return

        table_type = self.table_type_var.get()
        u = self.solution["u"]

        if table_type == "Desplazamientos":
            self.results_tree.heading("v1", text="Ux")
            self.results_tree.heading("v2", text="Uy")
            self.results_tree.heading("v3", text="|U|")
            self.results_tree.heading("v4", text="")
            self.results_tree.heading("v5", text="")
            self.results_tree.heading("v6", text="")
            for nid in sorted(self.project.nodes.keys()):
                ux = u[2 * (nid - 1)]
                uy = u[2 * (nid - 1) + 1]
                umag = np.sqrt(ux**2 + uy**2)
                self.results_tree.insert(
                    "", END,
                    values=(nid,
                            f"{ux:.{DECIMALS_DISPLACEMENT}e}",
                            f"{uy:.{DECIMALS_DISPLACEMENT}e}",
                            f"{umag:.{DECIMALS_DISPLACEMENT}e}",
                            "", "", "")
                )

        elif table_type == "Esfuerzos":
            self.results_tree.heading("v1", text="σx")
            self.results_tree.heading("v2", text="σy")
            self.results_tree.heading("v3", text="τxy")
            self.results_tree.heading("v4", text="σ1")
            self.results_tree.heading("v5", text="σ2")
            self.results_tree.heading("v6", text="VM")
            if self.nodal_stresses:
                for nid in sorted(self.nodal_stresses.keys()):
                    s = self.nodal_stresses[nid]
                    self.results_tree.insert(
                        "", END,
                        values=(
                            nid,
                            fmt(s['sigma_x'], "stress"),
                            fmt(s['sigma_y'], "stress"),
                            fmt(s['tau_xy'], "stress"),
                            fmt(s['sigma_1'], "stress"),
                            fmt(s['sigma_2'], "stress"),
                            fmt(s['von_mises'], "stress"),
                        )
                    )

        elif table_type == "Reacciones":
            self.results_tree.heading("v1", text="Rx")
            self.results_tree.heading("v2", text="Ry")
            self.results_tree.heading("v3", text="")
            self.results_tree.heading("v4", text="")
            self.results_tree.heading("v5", text="")
            self.results_tree.heading("v6", text="")
            R = self.solution["reactions"]
            for bc in sorted(self.project.boundary_conditions.values(),
                             key=lambda b: b.node_id):
                nid = bc.node_id
                rx = R[2 * (nid - 1)] if bc.restrain_x else 0
                ry = R[2 * (nid - 1) + 1] if bc.restrain_y else 0
                self.results_tree.insert(
                    "", END, values=(nid, fmt(rx, "force"),
                                     fmt(ry, "force"), "", "", "", "")
                )

    # ─── Copiado al portapapeles (TSV) ─────────────────────────────────
    def _select_all_results(self, event=None):
        children = self.results_tree.get_children()
        if children:
            self.results_tree.selection_set(children)
        return "break"

    def _copy_results_tsv(self, event=None):
        """Copia las filas seleccionadas (o todas si no hay selección) al
        portapapeles en formato TSV. Solo se incluyen columnas con header
        no vacío para que el pegado en Excel quede limpio según la vista
        activa (Desplazamientos / Esfuerzos / Reacciones)."""
        items = self.results_tree.selection()
        if not items:
            items = self.results_tree.get_children()
        if not items:
            return "break"

        cols = self.results_tree["columns"]
        # Solo columnas con header no vacío (la vista activa puede dejar
        # v4..v6 sin texto).
        visible = [
            (c, self.results_tree.heading(c, "text"))
            for c in cols
            if self.results_tree.heading(c, "text")
        ]
        if not visible:
            return "break"

        lines = ["\t".join(h for _, h in visible)]
        for iid in items:
            values = self.results_tree.item(iid, "values")
            col_to_val = dict(zip(cols, values))
            lines.append("\t".join(str(col_to_val.get(c, "")) for c, _ in visible))

        text = "\n".join(lines)
        self.frame.clipboard_clear()
        self.frame.clipboard_append(text)
        self.main_window.set_status(
            f"Copiado al portapapeles: {len(items)} fila(s) en formato TSV"
        )
        return "break"

    # ═════════════════════════════════════════════════════════════════════
    # REFRESH
    # ═════════════════════════════════════════════════════════════════════

    def refresh(self):
        """Refresca la pestana de post-proceso."""
        if not self.project.is_solved:
            self.solution = None
            self.nodal_stresses = None
            if hasattr(self, 'solve_status'):
                self.solve_status.config(
                    text="Estado: Sin resolver", foreground="#ffa726"
                )
