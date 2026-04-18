"""
MainWindow: Ventana principal del software educativo FEM.
Arquitectura: PanedWindow con Notebook a la izquierda y MeshCanvas a la derecha.

Filosofía de menús: "pocos e importantes". 4 menús (Archivo, Modelo, Educación,
Ayuda) + toolbar con emoji Unicode. La profundidad vive en diálogos pop-up
autónomos que pueden invocarse desde múltiples lugares.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import json
import os

from config.settings import (
    APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    PROJECT_FILE_EXTENSION, PROJECT_FILE_DESCRIPTION,
)
from config import recent_files
from models.project import ProjectModel

from gui.preprocessing.pre_tab import PreProcessTab
from gui.processing.proc_tab import ProcessTab
from gui.postprocessing.post_tab import PostProcessTab
from gui.preprocessing.mesh_canvas import MeshCanvas

from gui.dialogs.material_dialog import MaterialDialog
from gui.dialogs.about_dialog import AboutDialog
from gui.dialogs.analysis_element_dialog import AnalysisElementDialog
from gui.dialogs.units_gravity_dialog import UnitsGravityDialog

from gui.widgets.tooltip import ToolTip


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
        self._is_fullscreen = False

        # ─── Modelo de datos ────────────────────────────────────────────
        self.project = ProjectModel()

        # ─── Variables de control (sincronizadas con project) ───────────
        self.analysis_type_var = tk.StringVar(value=self.project.analysis_type)
        self.element_type_var = tk.StringVar(value=self.project.element_type)
        self.unit_system_var = tk.StringVar(value=self.project.unit_system)

        # Referencias a items de menú para enable/disable
        self._menu_items = {}
        self._toolbar_items = {}

        # ─── Construir interfaz ─────────────────────────────────────────
        self._build_menu_bar()
        self._build_toolbar()
        self._build_main_layout()
        self._build_status_bar()
        self._bind_shortcuts()

        # ─── Estado inicial ─────────────────────────────────────────────
        self._update_title()
        self._refresh_menu_state()
        self.set_status("Bienvenido a EduFEM. Cree un nuevo proyecto o cargue el ejemplo.")

    # ═════════════════════════════════════════════════════════════════════
    # LAYOUT PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════

    def _build_main_layout(self):
        """Construye el layout principal con Notebook + Canvas compartido."""
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

        self.mesh_canvas = MeshCanvas(self.right_panel, self.project, self)
        self.mesh_canvas.pack(fill=BOTH, expand=YES)

    # ═════════════════════════════════════════════════════════════════════
    # BARRA DE MENU — 4 menús: Archivo, Modelo, Educación, Ayuda
    # ═════════════════════════════════════════════════════════════════════

    def _build_menu_bar(self):
        """Construye la barra de menu principal (filosofía minimalista)."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # ─── Menu Archivo ────────────────────────────────────────────────
        menu_archivo = tk.Menu(self.menubar, tearoff=0)
        menu_archivo.add_command(
            label="📄  Nuevo Proyecto", accelerator="Ctrl+N",
            command=self._on_new_project,
        )
        menu_archivo.add_command(
            label="📂  Abrir Proyecto…", accelerator="Ctrl+O",
            command=self._on_open_project,
        )

        # Submenu de recientes
        self.recent_menu = tk.Menu(menu_archivo, tearoff=0)
        menu_archivo.add_cascade(label="🕒  Abrir Recientes", menu=self.recent_menu)

        menu_archivo.add_command(
            label="🧪  Cargar Ejemplo", accelerator="Ctrl+E",
            command=self._on_load_example,
        )
        menu_archivo.add_separator()
        menu_archivo.add_command(
            label="💾  Guardar", accelerator="Ctrl+S",
            command=self._on_save_project,
        )
        self._menu_items["save"] = (menu_archivo, menu_archivo.index("end"))

        menu_archivo.add_command(
            label="💾  Guardar Como…", accelerator="Ctrl+Shift+S",
            command=self._on_save_as_project,
        )
        menu_archivo.add_separator()
        menu_archivo.add_command(
            label="📊  Exportar Reporte PDF…",
            command=self._on_export_pdf,
        )
        self._menu_items["export_pdf"] = (menu_archivo, menu_archivo.index("end"))

        menu_archivo.add_command(
            label="📑  Exportar Resultados CSV…",
            command=self._on_export_csv,
        )
        self._menu_items["export_csv"] = (menu_archivo, menu_archivo.index("end"))

        menu_archivo.add_separator()
        menu_archivo.add_command(
            label="🚪  Salir", accelerator="Ctrl+Q",
            command=self._on_exit,
        )
        self.menubar.add_cascade(label="Archivo", menu=menu_archivo)

        self._build_recent_menu()

        # ─── Menu Modelo ─────────────────────────────────────────────────
        menu_modelo = tk.Menu(self.menubar, tearoff=0)
        menu_modelo.add_command(
            label="🔬  Análisis y Elemento…",
            command=self._open_analysis_element_dialog,
        )
        menu_modelo.add_command(
            label="📏  Unidades y Gravedad…",
            command=self._open_units_gravity_dialog,
        )
        menu_modelo.add_command(
            label="🧱  Materiales…",
            command=self._on_material_properties,
        )
        self.menubar.add_cascade(label="Modelo", menu=menu_modelo)

        # ─── Menu Educación ──────────────────────────────────────────────
        menu_edu = tk.Menu(self.menubar, tearoff=0)
        edu_items = [
            ("🧭  M1 · Mapeo Isoparamétrico",       "Ctrl+1", "mod01"),
            ("🧮  M2 · Matriz B",                    "Ctrl+2", "mod02"),
            ("🔧  M3 · Matriz Constitutiva D",       "Ctrl+3", "mod03"),
            ("📊  M4 · Rigidez + Cuadratura Gauss",  "Ctrl+4", "mod04"),
            ("🏗  M5 · Ensamblaje Global",           "Ctrl+5", "mod05"),
            ("⚡  M6 · Fuerzas Equivalentes",         "Ctrl+6", "mod06"),
        ]
        for label, accel, mod_key in edu_items:
            menu_edu.add_command(
                label=label, accelerator=accel,
                command=lambda k=mod_key: self._open_education_module(k),
            )
        self.menubar.add_cascade(label="Educación", menu=menu_edu)

        # ─── Menu Ayuda ──────────────────────────────────────────────────
        menu_ayuda = tk.Menu(self.menubar, tearoff=0)
        menu_ayuda.add_command(
            label="📖  Manual de Usuario", accelerator="F1",
            command=self._on_help,
        )
        menu_ayuda.add_command(
            label="⌨  Atajos de Teclado", accelerator="Ctrl+/",
            command=self._on_shortcuts,
        )
        menu_ayuda.add_separator()
        menu_ayuda.add_command(
            label="ℹ  Acerca de…",
            command=self._on_about,
        )
        self.menubar.add_cascade(label="Ayuda", menu=menu_ayuda)

    # ═════════════════════════════════════════════════════════════════════
    # TOOLBAR (emoji)
    # ═════════════════════════════════════════════════════════════════════

    def _build_toolbar(self):
        """Construye la barra de herramientas debajo del menú."""
        self.toolbar = ttk.Frame(self.root, bootstyle="dark")
        self.toolbar.pack(fill=X, side=TOP, padx=0, pady=(2, 0))

        items = [
            ("📄", "Nuevo (Ctrl+N)",           "new",        self._on_new_project),
            ("📂", "Abrir (Ctrl+O)",           "open",       self._on_open_project),
            ("💾", "Guardar (Ctrl+S)",         "save",       self._on_save_project),
            None,
            ("🧪", "Cargar Ejemplo (Ctrl+E)",  "example",    self._on_load_example),
            ("▶",  "Resolver (F5)",            "solve",      self._on_solve),
            None,
            ("📊", "Exportar Reporte PDF",     "export_pdf", self._on_export_pdf),
            ("📑", "Exportar Resultados CSV",  "export_csv", self._on_export_csv),
            None,
            ("🎯", "Ajustar Vista (F)",        "fit",        self._on_fit_view),
            ("🔳", "Pantalla Completa (F11)",  "fullscreen", self._on_fullscreen),
        ]

        for item in items:
            if item is None:
                ttk.Separator(
                    self.toolbar, orient=VERTICAL
                ).pack(side=LEFT, fill=Y, padx=5, pady=5)
                continue
            icon, tip, key, cb = item
            btn = ttk.Button(
                self.toolbar, text=icon, bootstyle="dark",
                command=cb, width=3, takefocus=0,
            )
            btn.pack(side=LEFT, padx=1, pady=3)
            ToolTip(btn, text=tip)
            self._toolbar_items[key] = btn

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
    # TITULO, SMART ENABLE/DISABLE Y RECIENTES
    # ═════════════════════════════════════════════════════════════════════

    def _update_title(self):
        """Actualiza el título de la ventana con indicador ● si hay cambios."""
        if self.project.file_path:
            base = f"{os.path.basename(self.project.file_path)} — {APP_NAME}"
        else:
            base = f"{APP_NAME} v{APP_VERSION}"
        prefix = "● " if self.project.is_modified else ""
        self.root.title(f"{prefix}{base}")

    def _refresh_menu_state(self):
        """Habilita o deshabilita items de menú y toolbar según el estado del proyecto."""
        save_state = "normal" if self.project.is_modified else "disabled"
        export_state = "normal" if self.project.is_solved else "disabled"
        solve_state = "normal" if (
            self.project.num_elements > 0
            and len(self.project.boundary_conditions) > 0
        ) else "disabled"

        for key, state in (
            ("save", save_state),
            ("export_pdf", export_state),
            ("export_csv", export_state),
        ):
            menu, idx = self._menu_items.get(key, (None, None))
            if menu is not None:
                try:
                    menu.entryconfig(idx, state=state)
                except tk.TclError:
                    pass

        for key, state in (
            ("save", save_state),
            ("export_pdf", export_state),
            ("export_csv", export_state),
            ("solve", solve_state),
        ):
            btn = self._toolbar_items.get(key)
            if btn is not None:
                try:
                    btn.configure(state=state)
                except tk.TclError:
                    pass

    def _build_recent_menu(self):
        """Repuebla el submenu de archivos recientes."""
        self.recent_menu.delete(0, "end")
        paths = recent_files.load()

        if not paths:
            self.recent_menu.add_command(
                label="(sin proyectos recientes)", state="disabled",
            )
            return

        for i, path in enumerate(paths):
            label = f"{i + 1}. {os.path.basename(path)}"
            self.recent_menu.add_command(
                label=label,
                command=lambda p=path: self._open_recent(p),
            )

        self.recent_menu.add_separator()
        self.recent_menu.add_command(
            label="Limpiar lista",
            command=self._on_clear_recent,
        )

    def _open_recent(self, path):
        """Abre un proyecto desde la lista de recientes."""
        if not os.path.exists(path):
            messagebox.showwarning(
                "Archivo no encontrado",
                f"El archivo ya no existe y se quitará de la lista:\n{path}",
            )
            recent_files.remove(path)
            self._build_recent_menu()
            return
        self._load_project_from_path(path)

    def _on_clear_recent(self):
        recent_files.clear()
        self._build_recent_menu()
        self.set_status("Lista de archivos recientes borrada.")

    # ═════════════════════════════════════════════════════════════════════
    # ATAJOS DE TECLADO
    # ═════════════════════════════════════════════════════════════════════

    def _bind_shortcuts(self):
        """Registra todos los atajos de teclado (sincronizar con _on_shortcuts)."""
        b = self.root.bind
        b("<Control-n>", lambda e: self._on_new_project())
        b("<Control-o>", lambda e: self._on_open_project())
        b("<Control-s>", lambda e: self._on_save_project())
        b("<Control-Shift-S>", lambda e: self._on_save_as_project())
        b("<Control-e>", lambda e: self._on_load_example())
        b("<Control-q>", lambda e: self._on_exit())
        b("<F1>", lambda e: self._on_help())
        b("<F5>", lambda e: self._on_solve())
        b("<F11>", lambda e: self._on_fullscreen())
        b("<f>", lambda e: self._on_fit_view() if not self._is_entry_focused() else None)
        b("<F>", lambda e: self._on_fit_view() if not self._is_entry_focused() else None)
        b("<Control-slash>", lambda e: self._on_shortcuts())
        b("<Control-Tab>", lambda e: self._on_next_tab())
        b("<Control-Shift-Tab>", lambda e: self._on_prev_tab())
        # Ctrl+1..6 para módulos educativos
        for i in range(1, 7):
            key = f"<Control-Key-{i}>"
            b(key, lambda e, idx=i: self._open_education_module(f"mod0{idx}"))

    def _is_entry_focused(self):
        """Evita disparar atajos de letra simple si el foco está en un Entry."""
        try:
            w = self.root.focus_get()
            if w is None:
                return False
            cls = w.winfo_class()
            return cls in ("TEntry", "Entry", "TCombobox", "Spinbox", "TSpinbox", "Text")
        except Exception:
            return False

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — ARCHIVO
    # ═════════════════════════════════════════════════════════════════════

    def _on_new_project(self):
        if self.project.is_modified:
            resp = messagebox.askyesnocancel(
                "Nuevo Proyecto", "¿Desea guardar los cambios?"
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
        self._update_title()
        self._refresh_menu_state()

    def _on_open_project(self):
        filepath = filedialog.askopenfilename(
            title="Abrir Proyecto",
            filetypes=[
                (PROJECT_FILE_DESCRIPTION, f"*{PROJECT_FILE_EXTENSION}"),
                ("Archivos JSON", "*.json"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not filepath:
            return
        self._load_project_from_path(filepath)

    def _load_project_from_path(self, filepath):
        """Carga un proyecto desde una ruta dada. Reutilizable por Abrir y Recientes."""
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

            recent_files.add(filepath)
            self._build_recent_menu()
            self._update_title()
            self._refresh_menu_state()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el proyecto:\n{e}")

    def _on_load_example(self):
        """Carga el ejemplo de prueba (9 nodos, 4 elementos Q4)."""
        if self.project.is_modified:
            resp = messagebox.askyesnocancel(
                "Cargar Ejemplo", "Se perderán los datos actuales. ¿Guardar?"
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
            "E=225000, ν=0.2, P=1000 N en nodo 7"
        )
        self._update_title()
        self._refresh_menu_state()

    def _update_all_project_refs(self):
        """Actualiza la referencia al proyecto en todos los componentes."""
        self.mesh_canvas.project = self.project
        self.pre_tab.project = self.project
        self.proc_tab.project = self.project
        self.post_tab.project = self.project

    def _on_save_project(self):
        if not self.project.is_modified:
            # Nada que guardar
            return
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
            ],
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

            recent_files.add(filepath)
            self._build_recent_menu()
            self._update_title()
            self._refresh_menu_state()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _on_export_pdf(self):
        """Exporta un reporte PDF con los resultados del analisis."""
        if not self.project.is_solved:
            messagebox.showwarning(
                "Aviso",
                "Debe resolver el modelo antes de exportar el reporte PDF.\n"
                "Use F5 o el botón ▶ del toolbar.",
            )
            return

        filepath = filedialog.asksaveasfilename(
            title="Exportar Reporte PDF",
            defaultextension=".pdf",
            filetypes=[
                ("Documento PDF", "*.pdf"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not filepath:
            return

        try:
            import importlib
            pdf_module = importlib.import_module("file_io.pdf_report")
            generate_pdf_report = pdf_module.generate_pdf_report

            solution = self.post_tab.solution
            nodal_stresses = self.post_tab.nodal_stresses

            generate_pdf_report(
                self.project, solution, nodal_stresses,
                filepath, contour_figure=None,
            )

            self.set_status(f"Reporte PDF exportado: {os.path.basename(filepath)}")
            messagebox.showinfo(
                "PDF Exportado",
                f"Reporte guardado exitosamente en:\n{filepath}",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF:\n{e}")

    def _on_export_csv(self):
        """Exporta los resultados del analisis a CSV."""
        if not self.project.is_solved:
            messagebox.showwarning(
                "Aviso",
                "Debe resolver el modelo antes de exportar resultados.\n"
                "Use F5 o el botón ▶ del toolbar.",
            )
            return

        filepath = filedialog.asksaveasfilename(
            title="Exportar Resultados CSV",
            defaultextension=".csv",
            filetypes=[
                ("Archivo CSV", "*.csv"),
                ("Todos los archivos", "*.*"),
            ],
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
                f"Resultados exportados ({count} nodos) en:\n{filepath}",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar CSV:\n{e}")

    def _on_exit(self):
        if self.project.is_modified:
            resp = messagebox.askyesnocancel("Salir", "¿Guardar cambios?")
            if resp is None:
                return
            if resp:
                self._on_save_project()
        self.root.destroy()

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — MODELO (3 diálogos pop-up autónomos)
    # ═════════════════════════════════════════════════════════════════════

    def _open_analysis_element_dialog(self):
        AnalysisElementDialog(self.root, self.project, self)

    def _open_units_gravity_dialog(self):
        UnitsGravityDialog(self.root, self.project, self)

    def _on_material_properties(self):
        MaterialDialog(self.root, self.project)
        self._update_title()
        self._refresh_menu_state()

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — EDUCACION
    # ═════════════════════════════════════════════════════════════════════

    def _open_education_module(self, mod_key):
        """Abre un módulo educativo directamente desde el menú."""
        from education.module_launcher import open_module
        open_module(
            parent_tk=self.root,
            project=self.project,
            mod_key=mod_key,
            mesh_canvas=self.mesh_canvas,
        )

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — VISTA / ANALISIS
    # ═════════════════════════════════════════════════════════════════════

    def _on_solve(self):
        """Resuelve el modelo (delega en post_tab.auto_solve)."""
        if self.project.num_elements == 0:
            messagebox.showwarning(
                "Aviso", "Defina al menos un elemento antes de resolver."
            )
            return
        if not self.project.boundary_conditions:
            messagebox.showwarning(
                "Aviso",
                "Defina al menos una restricción (BC) antes de resolver.",
            )
            return
        # Cambiar a post-proceso dispara auto_solve automáticamente
        self.notebook.select(2)
        # Si ya estaba ahí, forzar la resolución
        self.project.is_solved = False
        self.post_tab.solution = None
        self.post_tab.auto_solve()

    def _on_fit_view(self):
        try:
            self.mesh_canvas.fit_view()
        except Exception:
            pass

    def _on_fullscreen(self):
        self._is_fullscreen = not self._is_fullscreen
        try:
            self.root.attributes("-fullscreen", self._is_fullscreen)
        except tk.TclError:
            pass

    def _on_next_tab(self):
        n = self.notebook.index("end")
        idx = self.notebook.index(self.notebook.select())
        self.notebook.select((idx + 1) % n)

    def _on_prev_tab(self):
        n = self.notebook.index("end")
        idx = self.notebook.index(self.notebook.select())
        self.notebook.select((idx - 1) % n)

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — AYUDA
    # ═════════════════════════════════════════════════════════════════════

    def _on_help(self):
        messagebox.showinfo(
            "Manual de Usuario",
            "Manual de usuario próximamente.\n\n"
            "Mientras tanto, use Ayuda ▸ Atajos de Teclado (Ctrl+/) "
            "para ver las acciones disponibles.",
        )

    def _on_shortcuts(self):
        shortcuts = (
            "ATAJOS DE TECLADO\n"
            "─────────────────────────────\n"
            "Archivo\n"
            "  Ctrl+N           Nuevo Proyecto\n"
            "  Ctrl+O           Abrir Proyecto\n"
            "  Ctrl+E           Cargar Ejemplo\n"
            "  Ctrl+S           Guardar\n"
            "  Ctrl+Shift+S     Guardar Como\n"
            "  Ctrl+Q           Salir\n\n"
            "Análisis\n"
            "  F5               Resolver modelo\n\n"
            "Educación\n"
            "  Ctrl+1           M1 · Mapeo Isoparamétrico\n"
            "  Ctrl+2           M2 · Matriz B\n"
            "  Ctrl+3           M3 · Matriz Constitutiva D\n"
            "  Ctrl+4           M4 · Rigidez + Gauss\n"
            "  Ctrl+5           M5 · Ensamblaje\n"
            "  Ctrl+6           M6 · Fuerzas Equivalentes\n\n"
            "Vista\n"
            "  F                Ajustar Vista\n"
            "  F11              Pantalla Completa\n"
            "  Ctrl+Tab         Siguiente Pestaña\n"
            "  Ctrl+Shift+Tab   Pestaña Anterior\n\n"
            "Ayuda\n"
            "  F1               Manual de Usuario\n"
            "  Ctrl+/           Esta ventana\n"
        )
        messagebox.showinfo("Atajos de Teclado", shortcuts)

    def _on_about(self):
        AboutDialog(self.root)

    # ═════════════════════════════════════════════════════════════════════
    # EVENTOS DE PESTANA
    # ═════════════════════════════════════════════════════════════════════

    def _on_tab_changed(self, _event):
        """Callback cuando se cambia de pestana."""
        tab_index = self.notebook.index(self.notebook.select())
        tab_names = ["Pre-Proceso", "Proceso", "Post-Proceso"]
        if tab_index < len(tab_names):
            self.set_status(f"Pestaña activa: {tab_names[tab_index]}")

        if tab_index == 0:
            self.pre_tab.refresh()
        elif tab_index == 1:
            self.proc_tab.refresh()
        elif tab_index == 2:
            self.post_tab.auto_solve()

        self.mesh_canvas.redraw()
        self._refresh_menu_state()

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
