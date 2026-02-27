"""
MainWindow: Ventana principal del software educativo FEM.
Arquitectura: PanedWindow con Notebook a la izquierda y MeshCanvas/ContourCanvas a la derecha.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import json
import os

from config.settings import (
    APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    ANALYSIS_TYPES, ELEMENT_TYPES, PROJECT_FILE_EXTENSION,
    PROJECT_FILE_DESCRIPTION
)
from config.units import get_unit_system_names
from models.project import ProjectModel
from gui.preprocessing.pre_tab import PreProcessTab
from gui.processing.proc_tab import ProcessTab
from gui.postprocessing.post_tab import PostProcessTab
from gui.preprocessing.mesh_canvas import MeshCanvas

from gui.dialogs.material_dialog import MaterialDialog
from gui.dialogs.about_dialog import AboutDialog


class MainWindow:
    """Ventana principal de la aplicacion EduFEM."""

    def __init__(self):
        # ─── Crear ventana con tema oscuro ──────────────────────────────
        self.root = ttk.Window(
            title=f"{APP_NAME} v{APP_VERSION}",
            themename="darkly",
            minsize=(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT),
        )
        self.root.state("zoomed")

        # ─── Modelo de datos ────────────────────────────────────────────
        self.project = ProjectModel()

        # ─── Variables de control ───────────────────────────────────────
        self.analysis_type_var = tk.StringVar(value=self.project.analysis_type)
        self.element_type_var = tk.StringVar(value=self.project.element_type)
        self.unit_system_var = tk.StringVar(value=self.project.unit_system)

        # ─── Construir interfaz ─────────────────────────────────────────
        self._build_menu_bar()
        self._build_main_layout()
        self._build_status_bar()

        # ─── Mensaje inicial ────────────────────────────────────────────
        self.set_status("Bienvenido a EduFEM. Cree un nuevo proyecto o cargue el ejemplo.")

    # ═════════════════════════════════════════════════════════════════════
    # LAYOUT PRINCIPAL: PanedWindow (Notebook izq + Canvas der)
    # ═════════════════════════════════════════════════════════════════════

    def _build_main_layout(self):
        """Construye el layout principal con Notebook + Canvas compartido."""
        # PanedWindow horizontal
        self.main_paned = ttk.Panedwindow(self.root, orient=HORIZONTAL)
        self.main_paned.pack(fill=BOTH, expand=YES, padx=3, pady=(3, 0))

        # ─── Panel izquierdo: Notebook con 3 pestanas ───────────────────
        self.left_panel = ttk.Frame(self.main_paned, width=420)
        self.main_paned.add(self.left_panel, weight=2)

        self.notebook = ttk.Notebook(self.left_panel, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=YES)

        # Tab 1: PRE-PROCESO
        self.pre_tab = PreProcessTab(self.notebook, self.project, self)
        self.notebook.add(self.pre_tab.frame, text="  PRE-PROCESO  ")

        # Tab 2: PROCESO
        self.proc_tab = ProcessTab(self.notebook, self.project, self)
        self.notebook.add(self.proc_tab.frame, text="  PROCESO  ")

        # Tab 3: POST-PROCESO
        self.post_tab = PostProcessTab(self.notebook, self.project, self)
        self.notebook.add(self.post_tab.frame, text="  POST-PROCESO  ")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # ─── Panel derecho: MeshCanvas compartido ────────────────────────
        self.right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel, weight=3)

        # Canvas de malla unificado (todas las pestanas)
        self.mesh_canvas = MeshCanvas(self.right_panel, self.project, self)
        self.mesh_canvas.pack(fill=BOTH, expand=YES)

    # ═════════════════════════════════════════════════════════════════════
    # BARRA DE MENU
    # ═════════════════════════════════════════════════════════════════════

    def _build_menu_bar(self):
        """Construye la barra de menu principal."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # ─── Menu Archivo ────────────────────────────────────────────────
        menu_archivo = tk.Menu(self.menubar, tearoff=0)
        menu_archivo.add_command(
            label="  Nuevo Proyecto", accelerator="Ctrl+N",
            command=self._on_new_project
        )
        menu_archivo.add_command(
            label="  Abrir Proyecto...", accelerator="Ctrl+O",
            command=self._on_open_project
        )
        menu_archivo.add_command(
            label="  Cargar Ejemplo de Prueba",
            command=self._on_load_example
        )
        menu_archivo.add_command(
            label="  Guardar", accelerator="Ctrl+S",
            command=self._on_save_project
        )
        menu_archivo.add_command(
            label="  Guardar Como...", accelerator="Ctrl+Shift+S",
            command=self._on_save_as_project
        )
        menu_archivo.add_separator()
        menu_archivo.add_command(
            label="  Exportar Reporte PDF...",
            command=self._on_export_pdf
        )
        menu_archivo.add_command(
            label="  Exportar Resultados CSV...",
            command=self._on_export_csv
        )
        menu_archivo.add_separator()
        menu_archivo.add_command(
            label="  Salir", accelerator="Alt+F4",
            command=self._on_exit
        )
        self.menubar.add_cascade(label="Archivo", menu=menu_archivo)

        # ─── Menu Modelo ─────────────────────────────────────────────────
        menu_modelo = tk.Menu(self.menubar, tearoff=0)

        menu_analysis = tk.Menu(menu_modelo, tearoff=0)
        for at in ANALYSIS_TYPES:
            menu_analysis.add_radiobutton(
                label=at, variable=self.analysis_type_var,
                value=at, command=self._on_analysis_type_changed
            )
        menu_modelo.add_cascade(label="  Tipo de Analisis", menu=menu_analysis)

        menu_units = tk.Menu(menu_modelo, tearoff=0)
        for unit in get_unit_system_names():
            menu_units.add_radiobutton(
                label=unit, variable=self.unit_system_var,
                value=unit, command=self._on_unit_system_changed
            )
        menu_modelo.add_cascade(label="  Sistema de Unidades", menu=menu_units)

        menu_modelo.add_command(
            label="  Propiedades de Material...",
            command=self._on_material_properties
        )
        menu_modelo.add_separator()

        menu_elem = tk.Menu(menu_modelo, tearoff=0)
        for et in ELEMENT_TYPES:
            menu_elem.add_radiobutton(
                label=et, variable=self.element_type_var,
                value=et, command=self._on_element_type_changed
            )
        menu_modelo.add_cascade(label="  Tipo de Elemento", menu=menu_elem)

        self.menubar.add_cascade(label="Modelo", menu=menu_modelo)

        # ─── Menu Ayuda ──────────────────────────────────────────────────
        menu_ayuda = tk.Menu(self.menubar, tearoff=0)
        menu_ayuda.add_command(
            label="  Manual de Usuario", accelerator="F1",
            command=self._on_help
        )
        menu_ayuda.add_command(
            label="  Atajos de Teclado", command=self._on_shortcuts
        )
        menu_ayuda.add_separator()
        menu_ayuda.add_command(
            label="  Acerca de...", command=self._on_about
        )
        self.menubar.add_cascade(label="Ayuda", menu=menu_ayuda)

        # Atajos de teclado
        self.root.bind("<Control-n>", lambda e: self._on_new_project())
        self.root.bind("<Control-o>", lambda e: self._on_open_project())
        self.root.bind("<Control-s>", lambda e: self._on_save_project())
        self.root.bind("<Control-Shift-S>", lambda e: self._on_save_as_project())
        self.root.bind("<F1>", lambda e: self._on_help())

    # ═════════════════════════════════════════════════════════════════════
    # BARRA DE ESTADO
    # ═════════════════════════════════════════════════════════════════════

    def _build_status_bar(self):
        """Construye la barra de estado inferior."""
        self.status_frame = ttk.Frame(self.root, bootstyle="dark")
        self.status_frame.pack(fill=X, side=BOTTOM, padx=0, pady=0)

        self.status_label = ttk.Label(
            self.status_frame, text="Listo",
            bootstyle="inverse-dark", font=("Segoe UI", 9), padding=(10, 4),
        )
        self.status_label.pack(side=LEFT)

        self.info_label = ttk.Label(
            self.status_frame, text="",
            bootstyle="inverse-dark", font=("Segoe UI", 9), padding=(10, 4),
        )
        self.info_label.pack(side=RIGHT)

        self.analysis_label = ttk.Label(
            self.status_frame, text="",
            bootstyle="inverse-dark", font=("Segoe UI", 9), padding=(10, 4),
        )
        self.analysis_label.pack(side=RIGHT)

        self._update_status_info()

    def set_status(self, message):
        """Actualiza el mensaje de la barra de estado."""
        self.status_label.config(text=f"  {message}")

    def _update_status_info(self):
        """Actualiza la informacion del modelo en la barra de estado."""
        at = self.project.analysis_type
        et = self.project.element_type.split(' ')[0]
        self.analysis_label.config(text=f"{at} | {et}")
        self.info_label.config(
            text=f"Nodos: {self.project.num_nodes}  |  "
                 f"Elementos: {self.project.num_elements}  |  "
                 f"GDL: {self.project.total_dof}"
        )

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS DE EVENTOS
    # ═════════════════════════════════════════════════════════════════════

    def _on_new_project(self):
        if self.project.is_modified:
            resp = messagebox.askyesnocancel(
                "Nuevo Proyecto", "Desea guardar los cambios?"
            )
            if resp is None:
                return
            if resp:
                self._on_save_project()

        self.project.reset()
        self.mesh_canvas.project = self.project
        self.mesh_canvas.clear_results()
        self._update_all_project_refs()
        self._refresh_all_tabs()
        self._update_status_info()
        self.set_status("Nuevo proyecto creado.")
        self.root.title(f"{APP_NAME} v{APP_VERSION}")

    def _on_open_project(self):
        filepath = filedialog.askopenfilename(
            title="Abrir Proyecto",
            filetypes=[
                (PROJECT_FILE_DESCRIPTION, f"*{PROJECT_FILE_EXTENSION}"),
                ("Archivos JSON", "*.json"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.project = ProjectModel.from_dict(data)
            self.project.file_path = filepath
            self.project.is_modified = False

            self.analysis_type_var.set(self.project.analysis_type)
            self.element_type_var.set(self.project.element_type)
            self.unit_system_var.set(self.project.unit_system)

            self._update_all_project_refs()
            self._refresh_all_tabs()
            self._update_status_info()
            self.root.after(100, self.mesh_canvas.fit_view)
            self.set_status(f"Proyecto abierto: {os.path.basename(filepath)}")
            self.root.title(f"{os.path.basename(filepath)} -- {APP_NAME}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el proyecto:\n{e}")

    def _on_load_example(self):
        """Carga el ejemplo de prueba (9 nodos, 4 elementos Q4)."""
        if self.project.is_modified:
            resp = messagebox.askyesnocancel(
                "Cargar Ejemplo", "Se perderan los datos actuales. Guardar?"
            )
            if resp is None:
                return
            if resp:
                self._on_save_project()

        from tests.example_data import load_example_project
        self.project = load_example_project(P=1000.0)

        self.analysis_type_var.set(self.project.analysis_type)
        self.element_type_var.set(self.project.element_type)
        self.unit_system_var.set(self.project.unit_system)

        self._update_all_project_refs()
        self.mesh_canvas.clear_results()
        self._refresh_all_tabs()
        self._update_status_info()
        self.root.after(100, self.mesh_canvas.fit_view)

        self.set_status(
            "Ejemplo cargado: 9 nodos, 4 elementos Q4, "
            "E=225000, v=0.2, P=1000 N en nodo 7"
        )
        self.root.title(f"Ejemplo Validacion Q4 -- {APP_NAME}")

    def _update_all_project_refs(self):
        """Actualiza la referencia al proyecto en todos los componentes."""
        self.mesh_canvas.project = self.project
        self.pre_tab.project = self.project
        self.proc_tab.project = self.project
        self.post_tab.project = self.project

    def _on_save_project(self):
        if self.project.file_path is None:
            self._on_save_as_project()
            return
        self._save_to_file(self.project.file_path)

    def _on_save_as_project(self):
        filepath = filedialog.asksaveasfilename(
            title="Guardar Proyecto Como",
            defaultextension=PROJECT_FILE_EXTENSION,
            filetypes=[
                (PROJECT_FILE_DESCRIPTION, f"*{PROJECT_FILE_EXTENSION}"),
                ("Archivos JSON", "*.json"),
            ]
        )
        if filepath:
            self._save_to_file(filepath)

    def _save_to_file(self, filepath):
        try:
            data = self.project.to_dict()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.project.file_path = filepath
            self.project.is_modified = False
            self.set_status(f"Proyecto guardado: {os.path.basename(filepath)}")
            self.root.title(f"{os.path.basename(filepath)} -- {APP_NAME}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _on_export_pdf(self):
        """Exporta un reporte PDF con los resultados del analisis."""
        if not self.project.is_solved:
            messagebox.showwarning(
                "Aviso",
                "Debe resolver el modelo antes de exportar el reporte PDF.\n"
                "Vaya a Post-Proceso y presione RESOLVER."
            )
            return

        filepath = filedialog.asksaveasfilename(
            title="Exportar Reporte PDF",
            defaultextension=".pdf",
            filetypes=[
                ("Documento PDF", "*.pdf"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not filepath:
            return

        try:
            import importlib
            pdf_module = importlib.import_module("file_io.pdf_report")
            generate_pdf_report = pdf_module.generate_pdf_report

            # Obtener datos de la solucion del post_tab
            solution = self.post_tab.solution
            nodal_stresses = self.post_tab.nodal_stresses

            generate_pdf_report(
                self.project, solution, nodal_stresses,
                filepath, contour_figure=None
            )

            self.set_status(f"Reporte PDF exportado: {os.path.basename(filepath)}")
            messagebox.showinfo(
                "PDF Exportado",
                f"Reporte guardado exitosamente en:\n{filepath}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF:\n{e}")

    def _on_export_csv(self):
        """Exporta los resultados del analisis a CSV."""
        if not self.project.is_solved:
            messagebox.showwarning(
                "Aviso",
                "Debe resolver el modelo antes de exportar resultados.\n"
                "Vaya a Post-Proceso y presione RESOLVER."
            )
            return

        filepath = filedialog.asksaveasfilename(
            title="Exportar Resultados CSV",
            defaultextension=".csv",
            filetypes=[
                ("Archivo CSV", "*.csv"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not filepath:
            return

        try:
            from file_io.csv_io import export_results_csv

            solution = self.post_tab.solution
            nodal_stresses = self.post_tab.nodal_stresses

            count = export_results_csv(
                filepath, self.project, solution, nodal_stresses
            )

            self.set_status(f"Resultados CSV exportados: {count} nodos")
            messagebox.showinfo(
                "CSV Exportado",
                f"Resultados exportados ({count} nodos) en:\n{filepath}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar CSV:\n{e}")

    def _on_exit(self):
        if self.project.is_modified:
            resp = messagebox.askyesnocancel("Salir", "Guardar cambios?")
            if resp is None:
                return
            if resp:
                self._on_save_project()
        self.root.destroy()

    def _on_analysis_type_changed(self):
        self.project.analysis_type = self.analysis_type_var.get()
        self.project.is_modified = True
        self.project.is_solved = False
        self._update_status_info()
        self.set_status(f"Tipo de analisis: {self.project.analysis_type}")

    def _on_element_type_changed(self):
        self.project.element_type = self.element_type_var.get()
        self.project.is_modified = True
        self._update_status_info()
        self.set_status(f"Tipo de elemento: {self.project.element_type}")

    def _on_unit_system_changed(self):
        self.project.unit_system = self.unit_system_var.get()
        self.project.is_modified = True
        self.set_status(f"Sistema de unidades: {self.project.unit_system}")

    def _on_material_properties(self):
        MaterialDialog(self.root, self.project)

    def _on_help(self):
        messagebox.showinfo("Ayuda", "Manual de usuario proximamente.")

    def _on_shortcuts(self):
        shortcuts = (
            "Atajos de teclado:\n\n"
            "Ctrl+N  --  Nuevo Proyecto\n"
            "Ctrl+O  --  Abrir Proyecto\n"
            "Ctrl+S  --  Guardar\n"
            "Ctrl+Shift+S  --  Guardar Como\n"
            "F1  --  Ayuda\n"
        )
        messagebox.showinfo("Atajos de Teclado", shortcuts)

    def _on_about(self):
        AboutDialog(self.root)

    def _on_tab_changed(self, event):
        """Callback cuando se cambia de pestana."""
        tab_index = self.notebook.index(self.notebook.select())
        tab_names = ["Pre-Proceso", "Proceso", "Post-Proceso"]
        if tab_index < len(tab_names):
            self.set_status(f"Pestaña activa: {tab_names[tab_index]}")

        # Refrescar pestana activa
        if tab_index == 0:
            self.pre_tab.refresh()
        elif tab_index == 1:
            self.proc_tab.refresh()
        elif tab_index == 2:
            # Auto-resolver al entrar a Post-Proceso
            self.post_tab.auto_solve()

        # El canvas siempre es MeshCanvas, solo redibujar
        self.mesh_canvas.redraw()

    def _refresh_all_tabs(self):
        """Refresca todas las pestanas con los datos actuales."""
        self.pre_tab.refresh()
        self.proc_tab.refresh()
        self.post_tab.refresh()
        self.mesh_canvas.redraw()

    # ═════════════════════════════════════════════════════════════════════
    # EJECUCION
    # ═════════════════════════════════════════════════════════════════════

    def run(self):
        """Inicia el bucle principal de la aplicacion."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)
        self.root.mainloop()
