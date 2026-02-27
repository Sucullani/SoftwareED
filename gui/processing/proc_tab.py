"""
ProcessTab: Panel izquierdo de Proceso.
Analisis de calidad de malla y modulos educativos interactivos.
El canvas de malla es compartido en main_window.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import numpy as np


class ProcessTab:
    """Panel de Proceso con calidad de malla y modulos educativos."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)

        self._build_panel()

    def _build_panel(self):
        """Construye el panel con dos secciones: calidad y modulos."""
        # Scroll container
        canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient=VERTICAL, command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)

        # Seccion 1: Calidad de Malla
        self._build_quality_section()

        # Separador
        ttk.Separator(self.scroll_frame).pack(fill=X, padx=10, pady=10)

        # Seccion 2: Modulos Educativos
        self._build_education_section()

    def _build_quality_section(self):
        """Seccion de analisis de calidad de malla."""
        ttk.Label(
            self.scroll_frame, text="Calidad de la Malla",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor=W, padx=10, pady=(10, 5))

        ttk.Button(
            self.scroll_frame, text="Analizar Calidad",
            bootstyle="warning", command=self._analyze_quality
        ).pack(padx=10, pady=5, fill=X)

        # Tabla de calidad
        columns = ("elem", "jacobian", "min_ang", "max_ang", "robinson", "estado")
        self.quality_tree = ttk.Treeview(
            self.scroll_frame, columns=columns, show="headings",
            bootstyle="warning", height=6
        )
        self.quality_tree.heading("elem", text="Elem", anchor=CENTER)
        self.quality_tree.heading("jacobian", text="Jacobiano", anchor=CENTER)
        self.quality_tree.heading("min_ang", text="Min Ang", anchor=CENTER)
        self.quality_tree.heading("max_ang", text="Max Ang", anchor=CENTER)
        self.quality_tree.heading("robinson", text="Robinson", anchor=CENTER)
        self.quality_tree.heading("estado", text="Estado", anchor=CENTER)
        for col in columns:
            self.quality_tree.column(col, width=60, anchor=CENTER)
        self.quality_tree.pack(fill=X, padx=10, pady=5)

    def _build_education_section(self):
        """Seccion de modulos educativos interactivos."""
        ttk.Label(
            self.scroll_frame, text="Modulos Educativos FEM",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor=W, padx=10, pady=(5, 5))

        ttk.Label(
            self.scroll_frame,
            text="Seleccione un modulo para explorar interactivamente\n"
                 "los conceptos del Metodo de Elementos Finitos.",
            font=("Segoe UI", 9), foreground="#aaa", wraplength=380,
        ).pack(anchor=W, padx=15, pady=(0, 10))

        modules = [
            ("1. Funciones de Forma", "Funciones N en coordenadas naturales", "mod01"),
            ("2. Jacobiano y Transformacion", "Mapeo fisico <-> natural", "mod02"),
            ("3. Matriz B (Deformacion)", "Relacion deformacion-desplazamiento", "mod03"),
            ("4. Matriz Constitutiva D", "Relacion esfuerzo-deformacion", "mod04"),
            ("5. Matriz de Rigidez ke", "Rigidez del elemento individual", "mod05"),
            ("6. Integracion de Gauss", "Cuadratura numerica en el elemento", "mod06"),
            ("7. Vector de Cargas fe", "Cargas equivalentes nodales", "mod07"),
            ("8. Ensamblaje Global K,F", "Sistema global de ecuaciones", "mod08"),
            ("9. Condiciones de Contorno", "Restricciones y solucion K*u=F", "mod09"),
            ("10. Esfuerzos y Resultados", "Post-proceso: sigma, Von Mises", "mod10"),
        ]

        for title, desc, mod_key in modules:
            btn_frame = ttk.Frame(self.scroll_frame)
            btn_frame.pack(fill=X, padx=10, pady=2)

            ttk.Button(
                btn_frame, text=title, bootstyle="info-outline",
                command=lambda k=mod_key: self._open_module(k)
            ).pack(side=LEFT, fill=X, expand=YES)

            ttk.Label(
                btn_frame, text=desc, font=("Segoe UI", 8),
                foreground="#888", wraplength=180
            ).pack(side=RIGHT, padx=5)

    # ─── Acciones ───────────────────────────────────────────────────────

    def _analyze_quality(self):
        """Ejecuta analisis de calidad de malla."""
        if not self.project.elements:
            messagebox.showwarning("Aviso", "No hay elementos. Defina el modelo primero.")
            return

        from fem.mesh_quality import evaluate_mesh_quality
        quality = evaluate_mesh_quality(self.project)

        self.quality_tree.delete(*self.quality_tree.get_children())
        for eid, q in sorted(quality.items()):
            self.quality_tree.insert(
                "", END,
                values=(
                    eid,
                    f"{q['jacobian_ratio']:.4f}",
                    f"{q['min_angle']:.1f}",
                    f"{q['max_angle']:.1f}",
                    f"{q['robinson']:.2f}",
                    q['status'],
                )
            )

        self.main_window.set_status(
            f"Calidad de malla analizada: {len(quality)} elementos evaluados."
        )

    def _open_module(self, mod_key):
        """Abre un modulo educativo interactivo."""
        if not self.project.elements:
            messagebox.showwarning(
                "Aviso", "Cargue un modelo primero (Archivo > Cargar Ejemplo)."
            )
            return

        # Seleccionar elemento
        elem_ids = sorted(self.project.elements.keys())
        if len(elem_ids) == 1:
            elem_id = elem_ids[0]
        else:
            from tkinter import simpledialog
            elem_id = simpledialog.askinteger(
                "Seleccionar Elemento",
                f"Ingrese el ID del elemento ({elem_ids[0]}-{elem_ids[-1]}):",
                initialvalue=elem_ids[0],
                minvalue=elem_ids[0],
                maxvalue=elem_ids[-1],
                parent=self.frame.winfo_toplevel()
            )
            if elem_id is None:
                return
            if elem_id not in self.project.elements:
                messagebox.showerror("Error", f"El elemento {elem_id} no existe.")
                return

        # Resaltar elemento en el canvas compartido
        self.main_window.mesh_canvas.highlight_element(elem_id)

        # Abrir modulo
        try:
            module_map = {
                "mod01": ("education.mod01_shape_functions", "ShapeFunctionsModule"),
                "mod02": ("education.mod02_jacobian", "JacobianModule"),
                "mod03": ("education.mod03_b_matrix", "BMatrixModule"),
                "mod04": ("education.mod04_constitutive", "ConstitutiveModule"),
                "mod05": ("education.mod05_stiffness", "StiffnessModule"),
                "mod06": ("education.mod06_gauss_integration", "GaussIntegrationModule"),
                "mod07": ("education.mod07_load_vector", "LoadVectorModule"),
                "mod08": ("education.mod08_assembly", "AssemblyModule"),
                "mod09": ("education.mod09_boundary_conditions", "BoundaryConditionsModule"),
                "mod10": ("education.mod10_stress", "StressModule"),
            }

            if mod_key in module_map:
                module_name, class_name = module_map[mod_key]
                import importlib
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name)
                cls(self.frame.winfo_toplevel(), self.project, elem_id)
                self.main_window.set_status(f"Modulo educativo abierto: {mod_key}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir modulo:\n{e}")

    def refresh(self):
        """Refresca la pestana de proceso."""
        pass
