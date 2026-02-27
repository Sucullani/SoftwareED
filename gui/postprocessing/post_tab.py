"""
PostProcessTab: Panel izquierdo de Post-Proceso.
Organizado en sub-pestanas: Resolver, Resultados, Visualizacion.
Usa el MeshCanvas compartido (mismo canvas que Pre-Proceso y Proceso).
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import numpy as np


class PostProcessTab:
    """Panel de Post-Proceso con pestanas para resolver, resultados y visualizacion."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)

        # Estado de resultados
        self.solution = None
        self.nodal_stresses = None

        self._build_panel()

    def _build_panel(self):
        """Construye el panel con un Notebook de sub-pestanas."""
        self.notebook = ttk.Notebook(self.frame, bootstyle="danger")
        self.notebook.pack(fill=BOTH, expand=YES)

        # Sub-tab 1: Resolver
        self.solve_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.solve_frame, text="  Resolver  ")
        self._build_solve_tab()

        # Sub-tab 2: Resultados
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="  Resultados  ")
        self._build_results_tab()

        # Sub-tab 3: Visualizacion
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="  Visualización  ")
        self._build_visualization_tab()

    # ═════════════════════════════════════════════════════════════════════
    # SUB-TAB 1: RESOLVER
    # ═════════════════════════════════════════════════════════════════════

    def _build_solve_tab(self):
        """Contenido de la pestana Resolver."""
        container = ttk.Frame(self.solve_frame)
        container.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # Header
        ttk.Label(
            container, text="Análisis FEM",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, padx=10, pady=(10, 3))

        # Info del modelo
        self.model_info = ttk.Label(
            container,
            text="Cargue un modelo para comenzar.",
            font=("Segoe UI", 9), foreground="#888", wraplength=360,
        )
        self.model_info.pack(padx=15, pady=3, anchor=W)

        # Boton Resolver
        ttk.Button(
            container, text="  RESOLVER  K · u = F  ",
            bootstyle="success", command=self._on_solve,
        ).pack(pady=10, padx=10, fill=X)

        # Estado
        self.solve_status = ttk.Label(
            container, text="Estado: Sin resolver",
            font=("Segoe UI", 10, "bold"), foreground="#ffa726",
        )
        self.solve_status.pack(padx=15, pady=3, anchor=W)

        # Separador
        ttk.Separator(container).pack(fill=X, padx=10, pady=8)

        # Info detallada del resultado
        ttk.Label(
            container, text="Resumen de la Solución",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=W, padx=10, pady=(5, 3))

        self.solve_info = ttk.Label(
            container, text="",
            font=("Consolas", 8), foreground="#aaa",
            justify=LEFT, wraplength=360,
        )
        self.solve_info.pack(padx=15, pady=3, anchor=W, fill=X)

    # ═════════════════════════════════════════════════════════════════════
    # SUB-TAB 2: RESULTADOS (Tabla)
    # ═════════════════════════════════════════════════════════════════════

    def _build_results_tab(self):
        """Contenido de la pestana Resultados."""
        container = ttk.Frame(self.results_frame)
        container.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # Header
        ttk.Label(
            container, text="Tabla de Resultados Numéricos",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, padx=10, pady=(10, 5))

        # Selector de tipo
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

        # Tabla
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
    # SUB-TAB 3: VISUALIZACION
    # ═════════════════════════════════════════════════════════════════════

    def _build_visualization_tab(self):
        """Contenido de la pestana Visualizacion."""
        container = ttk.Frame(self.viz_frame)
        container.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # Header
        ttk.Label(
            container, text="Visualización de Resultados",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, padx=10, pady=(10, 3))

        ttk.Label(
            container,
            text="Seleccione el tipo de resultado y presione\n"
                 "'Visualizar' para ver el mapa de colores en el canvas.",
            font=("Segoe UI", 9), foreground="#aaa", wraplength=380,
        ).pack(anchor=W, padx=15, pady=(0, 8))

        # Selector de resultado
        ttk.Label(
            container, text="Tipo de Resultado",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=W, padx=10, pady=(5, 3))

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
                container, text=text, value=value,
                variable=self.result_var, bootstyle="danger",
            ).pack(anchor=W, padx=20, pady=1)

        # Separador
        ttk.Separator(container).pack(fill=X, padx=10, pady=8)

        # Opciones de deformacion
        ttk.Label(
            container, text="Opciones de Deformada",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor=W, padx=10, pady=(5, 3))

        self.show_deformed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            container, text="Mostrar malla deformada",
            variable=self.show_deformed_var, bootstyle="round-toggle",
        ).pack(anchor=W, padx=20, pady=2)

        scale_row = ttk.Frame(container)
        scale_row.pack(fill=X, padx=20, pady=2)
        ttk.Label(scale_row, text="Factor de escala:").pack(side=LEFT)
        self.scale_var = tk.DoubleVar(value=1.0)
        ttk.Entry(scale_row, textvariable=self.scale_var, width=8).pack(side=LEFT, padx=5)

        # Separador
        ttk.Separator(container).pack(fill=X, padx=10, pady=8)

        # Botones de accion
        ttk.Button(
            container, text="  Visualizar en Malla  ",
            bootstyle="danger", command=self._visualize_result,
        ).pack(pady=5, padx=10, fill=X)

        ttk.Button(
            container, text="  Limpiar Resultados  ",
            bootstyle="warning-outline", command=self._clear_results,
        ).pack(pady=3, padx=10, fill=X)

    # ═════════════════════════════════════════════════════════════════════
    # RESOLVER
    # ═════════════════════════════════════════════════════════════════════

    def _on_solve(self):
        """Ejecuta el analisis FEM completo."""
        if not self.project.elements:
            messagebox.showwarning("Aviso", "No hay elementos. Defina el modelo.")
            return
        if not self.project.boundary_conditions:
            messagebox.showwarning("Aviso", "No hay condiciones de contorno.")
            return

        self.solve_status.config(text="Estado: Resolviendo...", foreground="#4fc3f7")
        self.frame.update_idletasks()

        try:
            from fem.solver import solve_system
            from fem.stress import compute_all_stresses

            self.solution = solve_system(self.project)
            _, self.nodal_stresses = compute_all_stresses(self.project, self.solution)

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
                f"GDL totales: {len(u)}\n"
                f"GDL libres: {len(self.solution['free_dofs'])}\n"
                f"GDL restringidos: {len(restrained)}\n\n"
                f"Max |Ux|: {max_ux:.6e}\n"
                f"Max |Uy|: {max_uy:.6e}\n\n"
                "Reacciones:\n"
            )
            for dof in restrained:
                nid = dof // 2 + 1
                comp = "Rx" if dof % 2 == 0 else "Ry"
                info += f"  N{nid} {comp}: {R[dof]:.2f}\n"

            self.solve_info.config(text=info)
            self.solve_status.config(text="Estado: RESUELTO ✓", foreground="#81c784")
            self.main_window.set_status("Análisis completado. Visualice resultados.")
            self.main_window._update_status_info()

            # Auto-visualizar Von Mises en el canvas compartido
            self.result_var.set("VM")
            self._visualize_result()
            self._update_table()

            # Ir a la pestana de Visualizacion
            self.notebook.select(2)

        except Exception as e:
            self.solve_status.config(text="Estado: ERROR ✗", foreground="#ef5350")
            self.solve_info.config(text=str(e))
            messagebox.showerror("Error al resolver", str(e))

    # ═════════════════════════════════════════════════════════════════════
    # VISUALIZACION EN CANVAS COMPARTIDO (MeshCanvas)
    # ═════════════════════════════════════════════════════════════════════

    def _visualize_result(self):
        """Envia valores de resultado al MeshCanvas compartido."""
        if not self.solution:
            messagebox.showwarning("Aviso", "Ejecute el análisis primero (RESOLVER).")
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

        # Enviar al canvas de malla compartido
        canvas = self.main_window.mesh_canvas
        canvas.set_result_values(node_values, label)

        # Deformada
        if self.show_deformed_var.get():
            canvas.set_deformed(u, self.scale_var.get())
        else:
            canvas.show_deformed = False
            canvas.displacements = None
            canvas.redraw()

        self.main_window.set_status(f"Visualizando: {label}")

    def _clear_results(self):
        """Limpia la visualizacion de resultados del canvas."""
        self.main_window.mesh_canvas.clear_results()

    # ═════════════════════════════════════════════════════════════════════
    # TABLA DE RESULTADOS
    # ═════════════════════════════════════════════════════════════════════

    def _update_table(self):
        """Actualiza la tabla con resultados numericos."""
        self.results_tree.delete(*self.results_tree.get_children())

        if not self.solution:
            self.main_window.set_status("No hay resultados.")
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
            for bc in sorted(self.project.boundary_conditions.values(), key=lambda b: b.node_id):
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
        if hasattr(self, 'model_info'):
            info = (
                f"Nodos: {self.project.num_nodes}\n"
                f"Elementos: {self.project.num_elements}\n"
                f"GDL: {self.project.total_dof}\n"
                f"Análisis: {self.project.analysis_type}"
            )
            self.model_info.config(text=info)

        if not self.project.is_solved:
            self.solution = None
            self.nodal_stresses = None
            if hasattr(self, 'solve_status'):
                self.solve_status.config(text="Estado: Sin resolver", foreground="#ffa726")
            if hasattr(self, 'solve_info'):
                self.solve_info.config(text="")
