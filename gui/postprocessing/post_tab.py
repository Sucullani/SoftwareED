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
        self.notebook = ttk.Notebook(self.frame, bootstyle="danger")
        self.notebook.pack(fill=BOTH, expand=YES)

        # Sub-tab 1: Visualizacion
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="  Visualización  ")
        self._build_visualization_tab()

        # Sub-tab 2: Resultados numericos
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="  Resultados  ")
        self._build_results_tab()

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
            bootstyle="danger", height=15
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

    # ═════════════════════════════════════════════════════════════════════
    # AUTO-SOLVE (se llama al activar la pestana Post-Proceso)
    # ═════════════════════════════════════════════════════════════════════

    def auto_solve(self):
        """Resuelve automaticamente si hay modelo valido y no esta resuelto."""
        if not self.project.elements:
            self.solve_status.config(
                text="Sin modelo — defina nodos y elementos",
                foreground="#ef5350"
            )
            return

        if not self.project.boundary_conditions:
            self.solve_status.config(
                text="Sin restricciones — defina condiciones de contorno",
                foreground="#ef5350"
            )
            return

        # Si ya esta resuelto, solo actualizar display
        if self.solution is not None and self.project.is_solved:
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
                f"Max |Ux|: {max_ux:.4e}   Max |Uy|: {max_uy:.4e}"
            )
            self.model_info.config(text=info)
            self.solve_status.config(
                text="✓ RESUELTO — Seleccione resultado para visualizar",
                foreground="#81c784"
            )
            self.main_window.set_status("Análisis completado automáticamente.")
            self.main_window._update_status_info()

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
                    values=(nid, f"{ux:.6e}", f"{uy:.6e}", f"{umag:.6e}", "", "", "")
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
                            nid, f"{s['sigma_x']:.2f}", f"{s['sigma_y']:.2f}",
                            f"{s['tau_xy']:.2f}", f"{s['sigma_1']:.2f}",
                            f"{s['sigma_2']:.2f}", f"{s['von_mises']:.2f}",
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
                    "", END, values=(nid, f"{rx:.2f}", f"{ry:.2f}", "", "", "", "")
                )

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
