"""
MainWindow: Ventana principal del software educativo FEM.
Arquitectura: PanedWindow con Notebook a la izquierda y MeshCanvas a la derecha.

Filosofía de menús: "pocos e importantes". 3 menús (Archivo, Modelo, Ayuda).
Los módulos educativos viven en la pestaña PROCESO y se abren también vía
atajos Ctrl+1..6. La profundidad vive en diálogos pop-up autónomos que
pueden invocarse desde múltiples lugares.
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
    PHASE_PRE_COLOR, MENU_DISABLED_FG,
)
from config import recent_files
from models.project import ProjectModel
from models.mesh_utils import auto_expand_if_q9
from models.undo_stack import UndoStack

from gui.preprocessing.pre_tab import PreProcessTab
from gui.processing.proc_tab import ProcessTab
from gui.postprocessing.post_tab import PostProcessTab
from gui.preprocessing.mesh_canvas import MeshCanvas

from gui.dialogs.material_dialog import MaterialDialog
from gui.dialogs.about_dialog import AboutDialog
from gui.dialogs.element_type_dialog import ElementTypeDialog
from gui.dialogs.analysis_type_dialog import AnalysisTypeDialog
from gui.dialogs.units_gravity_dialog import UnitsGravityDialog
from gui.dialogs.dxf_import_dialog import DxfImportDialog


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

        # tk.Menu nativo Windows + tema oscuro: el render por defecto del
        # estado disabled hace doble pasada (shadow + highlight) que se
        # percibe como embossado/mas grueso. Forzar un foreground plano
        # elimina el efecto y deja al disabled visiblemente atenuado.
        self.root.option_add("*Menu.disabledForeground", MENU_DISABLED_FG)

        # ─── Modelo de datos ────────────────────────────────────────────
        self.project = ProjectModel()

        # ─── Undo/Redo stack ────────────────────────────────────────────
        # Snapshot-based via to_dict/from_dict. El listener limpia state
        # derivado (solucion cacheada, pending lock, highlights) y
        # refresca toda la UI tras un undo/redo.
        self.undo_stack = UndoStack(self.project)
        self.undo_stack.on_state_restored.append(self._on_state_restored)

        # ─── Variables de control (sincronizadas con project) ───────────
        self.analysis_type_var = tk.StringVar(value=self.project.analysis_type)
        self.element_type_var = tk.StringVar(value=self.project.element_type)
        self.unit_system_var = tk.StringVar(value=self.project.unit_system)

        # Referencias a items de menú para enable/disable
        self._menu_items = {}

        # ─── Construir interfaz ─────────────────────────────────────────
        self._build_menu_bar()
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
        self.notebook.add(self.pre_tab.frame, text="  📐  PRE-PROCESO  ")

        # Tab 2: PROCESO
        self.proc_tab = ProcessTab(self.notebook, self.project, self)
        self.notebook.add(self.proc_tab.frame, text="  ⚙  PROCESO  ")

        # Tab 3: POST-PROCESO
        self.post_tab = PostProcessTab(self.notebook, self.project, self)
        self.notebook.add(self.post_tab.frame, text="  📊  POST-PROCESO  ")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # ─── Panel derecho: MeshCanvas compartido ────────────────────────
        self.right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel, weight=3)

        self.mesh_canvas = MeshCanvas(self.right_panel, self.project, self)
        self.mesh_canvas.pack(fill=BOTH, expand=YES)

        # Cablear los callbacks bidireccionales del canvas al spreadsheet
        # del pre_tab. Hay que hacerlo aqui porque pre_tab se instancio
        # ANTES de que existiera mesh_canvas.
        if hasattr(self.pre_tab, "_wire_canvas_callbacks"):
            self.pre_tab._wire_canvas_callbacks()

    # ═════════════════════════════════════════════════════════════════════
    # BARRA DE MENU — 4 menús: Archivo, Modelo, Educación, Ayuda
    # ═════════════════════════════════════════════════════════════════════

    def _build_menu_bar(self):
        """Construye la barra de menu principal (filosofía minimalista)."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # ─── Menu Archivo ────────────────────────────────────────────────
        # `postcommand` refresca el state de los entries (Save / Memoria de
        # Cálculo) JUSTO antes de mostrar el menú. Esto evita tener que
        # llamar `_refresh_menu_state` desde cada mutacion del spreadsheet
        # o del canvas: las flags `is_modified`/`is_solved` del project ya
        # estan correctas, solo necesitamos sincronizar la UI cuando el
        # usuario abre el menu.
        menu_archivo = tk.Menu(
            self.menubar, tearoff=0,
            postcommand=self._refresh_menu_state,
        )
        menu_archivo.add_command(
            label="📄  Nuevo Proyecto", accelerator="Ctrl+N",
            command=self._on_new_project,
        )
        menu_archivo.add_command(
            label="📂  Abrir…", accelerator="Ctrl+O",
            command=self._on_open_project,
        )

        # Submenu de recientes
        self.recent_menu = tk.Menu(menu_archivo, tearoff=0)
        menu_archivo.add_cascade(label="🕒  Abrir Recientes", menu=self.recent_menu)

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

        # Submenu Importar (DXF + ZIP de CSVs)
        import_menu = tk.Menu(menu_archivo, tearoff=0)
        import_menu.add_command(
            label="📐  Geometría AutoCAD (DXF)…",
            command=self._on_import_dxf,
        )
        import_menu.add_command(
            label="📦  Modelo (Excel/CSV)…",
            command=self._on_import_model,
        )
        menu_archivo.add_cascade(label="📥  Importar", menu=import_menu)

        # Submenu Exportar (ZIP de CSVs + Memoria de Cálculo PDF)
        export_menu = tk.Menu(menu_archivo, tearoff=0)
        export_menu.add_command(
            label="📦  Modelo (Excel/CSV)…",
            command=self._on_export_model,
        )
        export_menu.add_command(
            label="📑  Memoria de Cálculo (PDF)…",
            command=self._on_export_pdf,
        )
        # Track la entrada PDF dentro del cascade Exportar para enable/disable
        # según is_solved.
        self._menu_items["export_pdf"] = (export_menu, export_menu.index("end"))
        menu_archivo.add_cascade(label="📤  Exportar", menu=export_menu)

        menu_archivo.add_separator()
        menu_archivo.add_command(
            label="🚪  Salir", accelerator="Ctrl+Q",
            command=self._on_exit,
        )
        self.menubar.add_cascade(label="Archivo", menu=menu_archivo)

        self._build_recent_menu()

        # ─── Menu Modelo ─────────────────────────────────────────────────
        # Orden FEM: geometría (elemento) → cómo medimos (unidades) →
        # de qué está hecho (material) → qué problema resolvemos (análisis).
        # El tipo de análisis va al final porque la matriz D depende del
        # material seleccionado (D = D(E, ν, caso plano)).
        menu_modelo = tk.Menu(self.menubar, tearoff=0)
        menu_modelo.add_command(
            label="🔲  Tipo de Elemento…",
            command=self._open_element_type_dialog,
        )
        menu_modelo.add_command(
            label="📏  Unidades y Gravedad…",
            command=self._open_units_gravity_dialog,
        )
        menu_modelo.add_command(
            label="🧱  Materiales…",
            command=self._on_material_properties,
        )
        menu_modelo.add_command(
            label="🔬  Tipo de Análisis…",
            command=self._open_analysis_type_dialog,
        )
        self.menubar.add_cascade(label="Modelo", menu=menu_modelo)

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

        # Submenu con las dos variantes del ejemplo canónico (Q4 y Q9).
        # Vive en Ayuda — los ejemplos son material didáctico, no archivos
        # del usuario.
        example_menu = tk.Menu(menu_ayuda, tearoff=0)
        example_menu.add_command(
            label="Q4 — cuadrilátero bilineal",
            accelerator="Ctrl+E",
            command=self._on_load_example,
        )
        example_menu.add_command(
            label="Q9 — cuadrilátero bicuadrático",
            command=lambda: self._on_load_example(q9=True),
        )
        menu_ayuda.add_cascade(label="🧪  Cargar Ejemplo", menu=example_menu)
        menu_ayuda.add_separator()

        menu_ayuda.add_command(
            label="ℹ  Acerca de…",
            command=self._on_about,
        )
        self.menubar.add_cascade(label="Ayuda", menu=menu_ayuda)

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

        # Indicador ORTHO (solo visible en modo dibujo + ortho activo).
        # Se muestra a la derecha del status_label con `pack(side=LEFT)`
        # tras el toggle correspondiente; oculto via pack_forget.
        self.ortho_indicator_label = tk.Label(
            self.status_frame, text="ORTHO",
            fg=PHASE_PRE_COLOR, bg="#1c1e22",
            font=("Segoe UI", 9, "bold"), padx=10, pady=4,
        )
        # No pack inicial — se gestiona desde _update_ortho_indicator.

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

        # Badge de salud del modelo (✓/⚠/✗ + conteo). Click abre el
        # HealthReportDialog en modo solo-lectura. Se actualiza en cada
        # _update_status_info (modelo modificado, post-fix, etc.).
        # Uso `tk.Label` directo para poder pintar foreground por
        # severidad sin depender del bootstyle del tema.
        self.health_badge = tk.Label(
            self.status_frame, text="✓ Modelo sano",
            fg="#4caf50", bg="#1c1e22",
            font=("Segoe UI", 9, "bold"), padx=10, pady=4,
            cursor="hand2",
        )
        self.health_badge.pack(side=RIGHT)
        self.health_badge.bind("<Button-1>",
                               lambda _e: self._on_health_badge_click())

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
        self._update_health_badge()

    def _update_health_badge(self):
        """Refresca el badge de salud del modelo. Lazy-import del
        validador para no impactar el arranque."""
        try:
            from models.model_health import validate_project
            from config.settings import (
                HEALTH_OK_COLOR, HEALTH_WARNING_COLOR, HEALTH_ERROR_COLOR,
            )
        except ImportError:
            return
        try:
            report = validate_project(self.project)
        except Exception:
            return
        self._last_health_report = report
        if report.has_errors():
            text = f"✗  {len(report.errors)} error(es)"
            color = HEALTH_ERROR_COLOR
        elif report.has_warnings():
            text = f"⚠  {len(report.warnings)} warning(s)"
            color = HEALTH_WARNING_COLOR
        else:
            text = "✓  Modelo sano"
            color = HEALTH_OK_COLOR
        try:
            self.health_badge.config(text=text, fg=color)
        except (tk.TclError, AttributeError):
            pass

    def _on_health_badge_click(self):
        """Abre el HealthReportDialog al clickear el badge. Modo
        consulta (allow_continue=False) -- es solo informativo desde
        aqui, no esta vinculado al solve."""
        report = getattr(self, "_last_health_report", None)
        if report is None:
            from models.model_health import validate_project
            report = validate_project(self.project)
        from gui.dialogs.health_report_dialog import HealthReportDialog
        dlg = HealthReportDialog(
            self.root, report, self.project, main_window=self,
            allow_continue=False,
        )
        dlg.show()
        # Si aplico fixes, refrescar todo
        if dlg.fixes_applied > 0:
            self._refresh_all_tabs()
            self._update_status_info()

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
        """Habilita o deshabilita items de menú según el estado del proyecto."""
        save_state = "normal" if self.project.is_modified else "disabled"
        export_state = "normal" if self.project.is_solved else "disabled"

        for key, state in (
            ("save", save_state),
            ("export_pdf", export_state),
        ):
            menu, idx = self._menu_items.get(key, (None, None))
            if menu is not None:
                try:
                    menu.entryconfig(idx, state=state)
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
        # F8 ORTHO toggle (estilo AutoCAD). Funciona siempre — el toggle
        # persiste como state UI, pero el indicador solo se muestra
        # durante el modo dibujo. Shift presionado durante dibujo actua
        # como override instantaneo (ver MeshCanvas._is_ortho_effective).
        b("<F8>", lambda e: self._on_toggle_ortho() if not self._is_entry_focused() else None)
        b("<F11>", lambda e: self._on_fullscreen())
        b("<f>", lambda e: self._on_fit_view() if not self._is_entry_focused() else None)
        b("<F>", lambda e: self._on_fit_view() if not self._is_entry_focused() else None)
        # 'D' / 'd' toggle del modo dibujo de elementos (canvas-driven).
        # Solo dispara si no hay Entry/Combobox enfocado para no chocar
        # con tipeo en celdas o coords.
        b("<d>", lambda e: self._on_toggle_draw_mode() if not self._is_entry_focused() else None)
        b("<D>", lambda e: self._on_toggle_draw_mode() if not self._is_entry_focused() else None)
        b("<Control-slash>", lambda e: self._on_shortcuts())
        b("<Control-Tab>", lambda e: self._on_next_tab())
        b("<Control-Shift-Tab>", lambda e: self._on_prev_tab())
        # Undo / Redo. Ctrl+Z y Ctrl+Y son convencion Windows; Ctrl+Shift+Z
        # es convencion macOS (lo agregamos como segundo binding para
        # compatibilidad de teclados).
        b("<Control-z>", lambda e: self._on_undo())
        b("<Control-y>", lambda e: self._on_redo())
        b("<Control-Shift-Z>", lambda e: self._on_redo())
        # Ctrl+1..6 para módulos educativos M1..M6 (M3 = matriz D, opera
        # por elemento porque depende del material asignado al elemento).
        for i in range(1, 7):
            key = f"<Control-Key-{i}>"
            b(key, lambda e, idx=i: self._open_education_module(f"mod0{idx}"))
        # Esc cascada global. Orden de prioridad:
        # 1) Modo dibujo (su handler ya gestiona puntos pendientes / salir)
        # 2) Cell editor abierto en spreadsheet (cierra el editor)
        # 3) Selecciones del canvas (las limpia)
        # Si nada aplica, no hace nada.
        b("<Escape>", lambda e: self._on_escape_global())

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
        self.undo_stack.clear()
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
            # Reasignar el undo_stack al nuevo project y limpiar historial
            self.undo_stack.set_project(self.project)

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

    def _on_load_example(self, q9: bool = False):
        """Carga el ejemplo de prueba (9 nodos, 4 elementos) en Q4 o Q9."""
        if self.project.is_modified:
            resp = messagebox.askyesnocancel(
                "Cargar Ejemplo", "Se perderán los datos actuales. ¿Guardar?"
            )
            if resp is None:
                return
            if resp:
                self._on_save_project()

        if q9:
            from tests.example_data import load_example_project_q9
            self.project = load_example_project_q9(P=1000.0)
            variant_msg = (
                "Ejemplo Q9: 9 nodos vértices + medios + centroides, "
                "4 elementos bicuadráticos, E=225000, ν=0.2, P=1000 N"
            )
        else:
            from tests.example_data import load_example_project
            self.project = load_example_project(P=1000.0)
            variant_msg = (
                "Ejemplo cargado: 9 nodos, 4 elementos Q4, "
                "E=225000, ν=0.2, P=1000 N en nodo 7"
            )

        self.analysis_type_var.set(self.project.analysis_type)
        self.element_type_var.set(self.project.element_type)
        self.unit_system_var.set(self.project.unit_system)

        # Reasignar el undo_stack al ejemplo recien cargado y limpiar
        # historial (el modelo anterior ya no es accesible).
        self.undo_stack.set_project(self.project)

        self._update_all_project_refs()
        self.mesh_canvas.clear_results()
        self._refresh_all_tabs()
        self._update_status_info()
        self.root.after(100, self.mesh_canvas.fit_view)

        self.set_status(variant_msg)
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
        """Exporta la Memoria de Cálculo (PDF) con los resultados del análisis."""
        if not self.project.is_solved:
            messagebox.showwarning(
                "Aviso",
                "Debe resolver el modelo antes de exportar la Memoria de Cálculo.\n"
                "Abra la pestaña POST-PROCESO o pulse F5.",
            )
            return

        filepath = filedialog.asksaveasfilename(
            title="Exportar Memoria de Cálculo (PDF)",
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

            self.set_status(
                f"Memoria de Cálculo exportada: {os.path.basename(filepath)}"
            )
            messagebox.showinfo(
                "Memoria de Cálculo exportada",
                f"Documento guardado exitosamente en:\n{filepath}",
            )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al generar la Memoria de Cálculo:\n{e}"
            )

    def _on_export_model(self):
        """Exporta TODO el modelo (nodos, elementos, materiales, cargas, BCs)
        a un .zip con un CSV por entidad — editable en Excel."""
        filepath = filedialog.asksaveasfilename(
            title="Exportar Modelo (Excel/CSV)",
            defaultextension=".zip",
            filetypes=[
                ("Modelo en Excel/CSV (ZIP)", "*.zip"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not filepath:
            return
        try:
            from file_io.model_io import export_model_csv
            counts = export_model_csv(self.project, filepath)
            resumen = ", ".join(f"{k}={v}" for k, v in counts.items() if v)
            self.set_status(f"Modelo exportado: {resumen or 'sin datos'}")
            messagebox.showinfo(
                "Exportación completada",
                f"Modelo exportado a:\n{filepath}\n\n{resumen or 'Sin datos'}",
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el modelo:\n{e}")

    def _on_import_dxf(self):
        """Importa geometría desde AutoCAD (DXF). El file picker se abre
        directamente desde el menu; si el usuario lo cancela no se muestra
        ningun dialogo. Luego, DxfImportDialog arranca con el archivo ya
        cargado (capas + preview) para una UX sin clicks intermedios.
        """
        path = filedialog.askopenfilename(
            title="Importar Geometría AutoCAD (DXF)",
            filetypes=[("Archivo DXF de AutoCAD", "*.dxf"),
                       ("Todos los archivos", "*.*")],
        )
        if not path:
            return
        try:
            DxfImportDialog(self.root, self.project, self, filepath=path)
        except Exception as exc:
            messagebox.showerror(
                "Error al abrir DXF",
                f"No se pudo abrir el archivo:\n{exc}"
            )

    def _on_import_model(self):
        """Importa TODO el modelo desde un .zip producido por Exportar Modelo."""
        filepath = filedialog.askopenfilename(
            title="Importar Modelo (Excel/CSV)",
            filetypes=[
                ("Modelo en Excel/CSV (ZIP)", "*.zip"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not filepath:
            return

        mode = "replace"
        if (self.project.num_nodes or self.project.num_elements
                or self.project.nodal_loads or self.project.boundary_conditions
                or self.project.surface_loads):
            resp = messagebox.askyesnocancel(
                "Importar Modelo (Excel/CSV)",
                "¿Reemplazar el modelo actual con los datos del archivo?\n\n"
                "Sí → Reemplazar todo\n"
                "No → Combinar con el modelo actual (IDs en conflicto se reasignan)\n"
                "Cancelar → No importar",
            )
            if resp is None:
                return
            mode = "replace" if resp else "merge"

        try:
            from file_io.model_io import import_model_csv
            # Undo: en modo merge capturamos el estado previo (el usuario
            # podria querer revertir el merge); en modo replace limpiamos
            # el stack porque el estado anterior ya no es accesible.
            if mode == "merge":
                self.undo_stack.capture("importar modelo (merge)")
            else:
                self.undo_stack.clear()
            counts = import_model_csv(self.project, filepath, mode=mode)
            # Safety net: si el proyecto esta en Q9 y el import trajo Q4
            # validos, expandir antes de refrescar la UI.
            num_expanded = auto_expand_if_q9(self.project)
            resumen = ", ".join(f"{k}={v}" for k, v in counts.items() if v)
            if num_expanded:
                resumen = (resumen + ", " if resumen else "") + \
                          f"q9_auto={num_expanded}"
            self._update_all_project_refs()
            self._refresh_all_tabs()
            self._update_status_info()
            self._update_title()
            self._refresh_menu_state()
            self.root.after(100, self.mesh_canvas.fit_view)
            self.set_status(f"Modelo importado ({mode}): {resumen or 'sin datos'}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar el modelo:\n{e}")

    def _on_exit(self):
        if self.project.is_modified:
            resp = messagebox.askyesnocancel("Salir", "¿Guardar cambios?")
            if resp is None:
                return
            if resp:
                self._on_save_project()
        self.root.destroy()

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — UNDO / REDO
    # ═════════════════════════════════════════════════════════════════════

    def _on_undo(self):
        """Ctrl+Z: deshace la ultima accion mutadora del usuario.
        Si no hay nada para deshacer, muestra mensaje en status bar."""
        if not self.undo_stack.can_undo():
            self.set_status("Nada para deshacer")
            return
        label = self.undo_stack.undo()
        # El listener `_on_state_restored` ya refresco toda la UI.
        if label:
            self.set_status(f"↶ Deshecho: {label}  (Ctrl+Y para rehacer)")
        else:
            self.set_status("↶ Deshecho  (Ctrl+Y para rehacer)")

    def _on_redo(self):
        """Ctrl+Y / Ctrl+Shift+Z: rehace la ultima accion deshecha."""
        if not self.undo_stack.can_redo():
            self.set_status("Nada para rehacer")
            return
        label = self.undo_stack.redo()
        if label:
            self.set_status(f"↷ Rehecho: {label}")
        else:
            self.set_status("↷ Rehecho")

    def _on_state_restored(self):
        """Listener invocado por UndoStack tras un undo o redo exitoso.
        Limpia state derivado (solucion, pending lock, highlights) y
        refresca toda la UI para reflejar el estado restaurado.

        IMPORTANTE: tras `from_dict`, el objeto `self.project` es el
        mismo (mutacion in-place de los dicts internos), asi que NO hay
        que reasignar refs en las pestañas. Solo refrescar.
        """
        # Invalidar solucion: el snapshot no la incluye, asi que tras
        # restore quedo inconsistente (puede ser de un estado pre-solve).
        self.project.is_solved = False
        self.project.displacements = None
        self.project.global_K = None
        self.project.global_F = None
        self.project.stresses = {}

        # Limpiar pending lock del pre_tab si quedo abierto
        try:
            self.pre_tab._pending_new = None
        except (AttributeError, Exception):
            pass

        # Limpiar highlights del canvas (pueden apuntar a items inexistentes)
        try:
            self.mesh_canvas.clear_highlights()
        except (AttributeError, Exception):
            pass

        # Si quedo un elemento parcial en construccion via modo dibujo,
        # descartarlo: el estado del modelo cambio y los puntos pendientes
        # podrian referenciar nodos que ya no existen.
        try:
            if self.mesh_canvas.is_draw_mode_active():
                self.mesh_canvas.disable_draw_mode()
        except (AttributeError, Exception):
            pass

        # Sanear sets de seleccion: quitar IDs que no existen en el
        # modelo restaurado. Sino, los renders y filas fantasma pueden
        # apuntar a items inexistentes.
        try:
            c = self.mesh_canvas
            c.selected_nodes = {n for n in c.selected_nodes
                                if n in self.project.nodes}
            c.selected_elements = {e for e in c.selected_elements
                                   if e in self.project.elements}
            c.selected_loads = {n for n in c.selected_loads
                                if n in self.project.nodal_loads}
            c.selected_constraints = {n for n in c.selected_constraints
                                      if n in self.project.boundary_conditions}
            c.selected_surfaces = {idx for idx in c.selected_surfaces
                                   if 0 <= idx < len(self.project.surface_loads)}
            # Aristas potenciales: ambos extremos deben existir
            c.selected_edges = {
                e for e in c.selected_edges
                if all(n in self.project.nodes for n in e)
            }
            c._emit_selection_changed()
        except (AttributeError, Exception):
            pass

        # Limpiar solution cacheada del post_tab
        try:
            self.post_tab.solution = None
            self.post_tab.nodal_stresses = None
        except (AttributeError, Exception):
            pass

        # Sincronizar variables de control y refrescar todo
        try:
            self.analysis_type_var.set(self.project.analysis_type)
            self.element_type_var.set(self.project.element_type)
            self.unit_system_var.set(self.project.unit_system)
        except (AttributeError, Exception):
            pass

        try:
            self._refresh_all_tabs()
            self._update_status_info()
            self._refresh_menu_state()
            self._update_title()
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — MODELO (3 diálogos pop-up autónomos)
    # ═════════════════════════════════════════════════════════════════════

    def _open_element_type_dialog(self):
        ElementTypeDialog(self.root, self.project, self)

    def _open_analysis_type_dialog(self):
        AnalysisTypeDialog(self.root, self.project, self)

    def _open_units_gravity_dialog(self):
        UnitsGravityDialog(self.root, self.project, self)

    def _on_material_properties(self):
        MaterialDialog(self.root, self.project, self)
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

    def _on_toggle_draw_mode(self):
        """Atajo D: delega al pre_tab para que aplique pre-flight de
        material y luego llame al canvas. Tambien navega a la pestana
        Pre-Proceso si no estamos ahi."""
        try:
            if self.notebook.index(self.notebook.select()) != 0:
                self.notebook.select(0)
            self.pre_tab._on_toggle_draw_mode()
        except Exception:
            pass

    def _on_toggle_ortho(self):
        """Atajo F8: toggle del modo ORTHO. El estado persiste en el
        canvas y el indicador en status bar solo se muestra cuando ademas
        el modo dibujo esta activo (sino el toggle queda 'armado' para la
        proxima activacion del dibujo)."""
        canvas = getattr(self, "mesh_canvas", None)
        if canvas is None:
            return
        canvas.set_ortho_active(not canvas.ortho_active)
        self._update_ortho_indicator()
        if canvas.draw_mode_active:
            estado = "activado" if canvas.ortho_active else "desactivado"
            self.set_status(f"ORTHO {estado}")

    def _update_ortho_indicator(self):
        """Muestra/oculta el indicador `ORTHO` en la status bar segun
        (draw_mode_active AND ortho_active). Idempotente."""
        canvas = getattr(self, "mesh_canvas", None)
        if canvas is None:
            return
        visible = bool(canvas.draw_mode_active and canvas.ortho_active)
        is_mapped = self.ortho_indicator_label.winfo_ismapped()
        if visible and not is_mapped:
            # Pack despues del status_label, antes del resto.
            self.ortho_indicator_label.pack(
                side=LEFT, after=self.status_label
            )
        elif not visible and is_mapped:
            self.ortho_indicator_label.pack_forget()

    def _on_escape_global(self):
        """Esc en cascada:
        1) Si el foco esta en un Entry/Combobox -> el widget maneja su
           Esc (cell editor, draw entry, dialogos). No interferimos.
        2) Si modo dibujo activo -> su handler (cancela puntos o desactiva)
        3) Si hay seleccion en canvas -> limpiarla (asi desaparecen las
           filas fantasma de las sub-pestañas)
        4) Sino -> no pasa nada
        """
        # 1) Si hay un Entry/Combobox enfocado, dejarlo manejar su Esc.
        if self._is_entry_focused():
            return
        # 2) Modo dibujo intercepta su propio Esc
        try:
            if self.mesh_canvas.is_draw_mode_active():
                self.mesh_canvas._on_draw_escape()
                return
        except Exception:
            pass
        # 3) Selecciones en canvas (limpia tambien las filas fantasma
        # via callback on_selection_changed)
        try:
            sel = self.mesh_canvas.get_selection()
            if any(sel.values()):
                self.mesh_canvas.clear_highlights()
                self.set_status("Seleccion limpiada")
                return
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
            "Edición\n"
            "  Ctrl+Z           Deshacer\n"
            "  Ctrl+Y           Rehacer\n"
            "  Ctrl+Shift+Z     Rehacer (alternativo)\n\n"
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
            "Modelado (estilo AutoCAD)\n"
            "  D                Dibujar elemento (toggle, click en canvas)\n"
            "  F8               ORTHO toggle (Shift = override instantaneo)\n"
            "  Backspace        Borrar ultimo vertice del elemento parcial\n"
            "  Esc              Cancelar elemento parcial / salir del modo\n"
            "  En el Entry:\n"
            "    100            Coord relativa al ultimo vertice (default)\n"
            "    #150           Coord absoluta (override)\n"
            "    @30            Relativa explicita (no-op tolerado)\n"
            "    100,50         Coma = separador X -> Y\n"
            "    8 + Enter (Y vacio + ORTHO) = distancia directa sobre\n"
            "    el eje del cursor (DDE estilo AutoCAD)\n\n"
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
            # Volver a Pre-Proceso: el canvas debe mostrar solo geometria,
            # no la deformada / mapa de colores / isolineas que dejo Post.
            self.mesh_canvas.clear_results_overlay()
            self.pre_tab.refresh()
        elif tab_index == 1:
            # Modo dibujo no tiene sentido fuera de Pre-Proceso.
            if self.mesh_canvas.is_draw_mode_active():
                self.mesh_canvas.disable_draw_mode()
            self.mesh_canvas.clear_results_overlay()
            self.proc_tab.refresh()
        elif tab_index == 2:
            if self.mesh_canvas.is_draw_mode_active():
                self.mesh_canvas.disable_draw_mode()
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
