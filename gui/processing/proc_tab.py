"""
ProcessTab: Panel izquierdo de Proceso.
Organizado en sub-pestanas: Calidad de Malla y Modulos Educativos.
El canvas de malla es compartido en main_window.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import numpy as np


class ProcessTab:
    """Panel de Proceso con pestanas para calidad de malla y modulos educativos."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)

        self._build_panel()

    def _build_panel(self):
        """Construye el panel con un Notebook de sub-pestanas."""
        self.notebook = ttk.Notebook(self.frame, bootstyle="warning")
        self.notebook.pack(fill=BOTH, expand=YES)

        # Sub-tab 1: Calidad de Malla
        self.quality_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.quality_frame, text="  Calidad de Malla  ")
        self._build_quality_tab()

        # Sub-tab 2: Modulos Educativos
        self.edu_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.edu_frame, text="  Módulos Educativos  ")
        self._build_education_tab()

    # ─── Sub-tab: Calidad de Malla ──────────────────────────────────────

    def _build_quality_tab(self):
        """Contenido de la pestana de calidad de malla."""
        container = ttk.Frame(self.quality_frame)
        container.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # Header
        ttk.Label(
            container, text="Análisis de Calidad de la Malla",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, padx=10, pady=(10, 3))

        ttk.Label(
            container,
            text="Evalúa la geometría de cada elemento:\n"
                 "Jacobiano, ángulos internos y estiramiento de Robinson.",
            font=("Segoe UI", 9), foreground="#aaa", wraplength=380,
        ).pack(anchor=W, padx=15, pady=(0, 8))

        ttk.Button(
            container, text="  Analizar Calidad  ",
            bootstyle="warning", command=self._analyze_quality
        ).pack(padx=10, pady=5, fill=X)

        # Tabla de calidad
        columns = ("elem", "jacobian", "min_ang", "max_ang", "robinson", "estado")
        self.quality_tree = ttk.Treeview(
            container, columns=columns, show="headings",
            bootstyle="warning", height=12
        )
        self.quality_tree.heading("elem", text="Elem", anchor=CENTER)
        self.quality_tree.heading("jacobian", text="Jacobiano", anchor=CENTER)
        self.quality_tree.heading("min_ang", text="Min Áng", anchor=CENTER)
        self.quality_tree.heading("max_ang", text="Max Áng", anchor=CENTER)
        self.quality_tree.heading("robinson", text="Robinson", anchor=CENTER)
        self.quality_tree.heading("estado", text="Estado", anchor=CENTER)
        for col in columns:
            self.quality_tree.column(col, width=65, anchor=CENTER)

        scrollbar = ttk.Scrollbar(container, orient=VERTICAL,
                                  command=self.quality_tree.yview)
        self.quality_tree.configure(yscrollcommand=scrollbar.set)

        self.quality_tree.pack(fill=BOTH, expand=YES, padx=10, pady=5, side=LEFT)
        scrollbar.pack(fill=Y, side=RIGHT, pady=5)

        # Info de referencia
        info_frame = ttk.Labelframe(self.quality_frame, text="Criterios de Calidad",
                                    bootstyle="warning")
        info_frame.pack(fill=X, padx=10, pady=(0, 10))

        criteria = (
            "• Jacobiano: >0.5 Buena, 0.3-0.5 Aceptable, <0.3 Mala\n"
            "• Ángulos: ideal 90°, rango aceptable 45°-135°\n"
            "• Robinson: <2.0 Buena, 2.0-3.0 Aceptable, >3.0 Mala"
        )
        ttk.Label(
            info_frame, text=criteria,
            font=("Segoe UI", 8), foreground="#888", wraplength=370, justify=LEFT
        ).pack(padx=10, pady=5)

    # ─── Sub-tab: Modulos Educativos ────────────────────────────────────

    def _build_education_tab(self):
        """Contenido de la pestana de modulos educativos."""
        # Scroll container
        canvas = tk.Canvas(self.edu_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.edu_frame, orient=VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=YES)

        # Header
        ttk.Label(
            scroll_frame, text="Módulos Educativos FEM",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, padx=10, pady=(10, 3))

        ttk.Label(
            scroll_frame,
            text="Explore interactivamente los conceptos del Método\n"
                 "de Elementos Finitos con datos de su modelo actual.\n"
                 "Seleccione un elemento para visualizar sus cálculos.",
            font=("Segoe UI", 9), foreground="#aaa", wraplength=380,
        ).pack(anchor=W, padx=15, pady=(0, 10))

        # Modulos organizados por categoria
        categories = [
            ("Geometría y Forma", [
                ("① Funciones de Forma", "Funciones N en coordenadas naturales", "mod01"),
                ("② Jacobiano y Transformación", "Mapeo físico ↔ natural", "mod02"),
            ]),
            ("Formulación del Elemento", [
                ("③ Matriz B (Deformación)", "Relación deformación-desplazamiento", "mod03"),
                ("④ Matriz Constitutiva D", "Relación esfuerzo-deformación", "mod04"),
                ("⑤ Matriz de Rigidez ke", "Rigidez del elemento individual", "mod05"),
                ("⑥ Integración de Gauss", "Cuadratura numérica en el elemento", "mod06"),
            ]),
            ("Sistema Global", [
                ("⑦ Vector de Cargas fe", "Cargas equivalentes nodales", "mod07"),
                ("⑧ Ensamblaje Global K,F", "Sistema global de ecuaciones", "mod08"),
                ("⑨ Condiciones de Contorno", "Restricciones y solución K·u=F", "mod09"),
            ]),
            ("Resultados", [
                ("⑩ Esfuerzos y Resultados", "Post-proceso: σ, Von Mises", "mod10"),
            ]),
        ]

        for cat_name, modules in categories:
            # Categoria header
            cat_label = ttk.Label(
                scroll_frame, text=cat_name,
                font=("Segoe UI", 10, "bold"), foreground="#ffa726",
            )
            cat_label.pack(anchor=W, padx=10, pady=(12, 4))

            for title, desc, mod_key in modules:
                btn_frame = ttk.Frame(scroll_frame)
                btn_frame.pack(fill=X, padx=15, pady=2)

                ttk.Button(
                    btn_frame, text=title, bootstyle="info-outline",
                    command=lambda k=mod_key: self._open_module(k)
                ).pack(side=LEFT, fill=X, expand=YES)

                ttk.Label(
                    btn_frame, text=desc, font=("Segoe UI", 8),
                    foreground="#888", wraplength=160
                ).pack(side=RIGHT, padx=5)

    # ═════════════════════════════════════════════════════════════════════
    # ACCIONES
    # ═════════════════════════════════════════════════════════════════════

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
