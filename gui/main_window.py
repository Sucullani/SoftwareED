"""
MainWindow: Ventana principal del software educativo FEM.
Arquitectura: PanedWindow con Notebook a la izquierda y MeshCanvas a la derecha.

Filosofía de menús: "pocos e importantes". 3 menús (Archivo, Modelo, Ayuda).
Los módulos educativos viven en la pestaña PROCESO y se abren también vía
atajos Ctrl+1..7. La profundidad vive en diálogos pop-up autónomos que
pueden invocarse desde múltiples lugares.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import json
import os
import traceback

from config.settings import (
    APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    PROJECT_FILE_EXTENSION, PROJECT_FILE_DESCRIPTION,
    PHASE_PRE_COLOR, MENU_DISABLED_FG,
    FONT_UI, FONT_UI_LARGE, HEALTH_OK_COLOR,
    STATUS_BAR_BG_COLOR,
)
from config.settings import ELEMENT_Q9 as ELEMENT_Q9_LABEL
from config import recent_files
from models.project import ProjectModel
from models.mesh_utils import auto_expand_if_q9
from models.undo_stack import UndoStack

from gui.preprocessing.pre_tab import PreProcessTab
from gui.processing.proc_tab import ProcessTab
from gui.postprocessing.post_tab import PostProcessTab
from gui.preprocessing.mesh_canvas import MeshCanvas
from gui.scaling import center_on_parent, scaled, work_area
from gui.widgets.tooltip import ToolTip

from gui.dialogs.material_dialog import MaterialDialog
from gui.dialogs.about_dialog import AboutDialog
from gui.dialogs.element_type_dialog import ElementTypeDialog
from gui.dialogs.analysis_type_dialog import AnalysisTypeDialog
from gui.dialogs.units_dialog import UnitsDialog
from gui.dialogs.gravity_dialog import GravityDialog
from gui.dialogs.dxf_import_dialog import DxfImportDialog


class MainWindow:
    """Ventana principal de la aplicacion EduFEM."""

    def __init__(self):
        # ─── Crear ventana con tema oscuro ──────────────────────────────
        self.root = ttk.Window(
            title=f"{APP_NAME} v{APP_VERSION}",
            themename="darkly",
        )
        self._apply_minsize()
        # Arrancar maximizada. `state("zoomed")` es la via de Windows —la
        # plataforma de distribucion— pero en X11 y macOS Tk la rechaza con
        # TclError y la app moria en el constructor. Se degrada a los dos
        # equivalentes portables para que la GUI (y con ella los tests de
        # `run_gates --con-gui`, que hoy solo corrian en Windows) tambien
        # levante en un Linux con Xvfb.
        try:
            self.root.state("zoomed")
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", True)     # varios WM de X11
            except tk.TclError:
                _x, _y, _w, _h = work_area(self.root)
                self.root.geometry(f"{_w}x{_h}+{_x}+{_y}")
        self._is_fullscreen = False
        # Guard de una sola compilacion de la Memoria a la vez: el dialogo de
        # progreso NO hace grab_set a proposito (la GUI sigue viva mientras el
        # worker compila), asi que nada impedia volver a Exportar y arrancar un
        # segundo thread sobre el mismo .pdf destino. Ver `_on_export_pdf`.
        self._exportando_pdf = False

        # Icono de la app (Explorador, barra de tareas, titulo de ventana).
        # resource_path resuelve en dev y en el .exe empaquetado (sys._MEIPASS).
        try:
            from config.settings import resource_path
            _ico = resource_path("icons", "edufem.ico")
            if os.path.exists(_ico):
                self.root.iconbitmap(_ico)
        except Exception:
            pass

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
        # La barra de estado se empaqueta ANTES del layout principal: Tk le da
        # su tamaño a lo que se empaquetó primero y recorta lo último, asi que
        # construirla al final la volvia la primera victima cuando la ventana
        # no entraba en la pantalla (regla dura 23). El area central, que es
        # la que tiene `expand`, absorbe la diferencia.
        self._build_status_bar()
        self._build_main_layout()
        self._bind_shortcuts()

        # ─── Estado inicial ─────────────────────────────────────────────
        self._update_title()
        self._refresh_menu_state()
        self.set_status("Bienvenido a EduFEM. Cree un nuevo proyecto o cargue el ejemplo.")

        # ─── matplotlib mathtext con Computer Modern ────────────────────
        # Diferido con after_idle: importar matplotlib + pyplot cuesta ~0.5-1s
        # (backend + fontmanager). Hacerlo aqui en el constructor bloqueaba el
        # primer paint de la ventana. Ningun widget de arranque usa matplotlib
        # (post_tab y modulos lo importan a nivel de metodo), asi que la
        # ventana puede mostrarse y este setup corre apenas el loop queda idle,
        # mucho antes de que el usuario abra un modulo educativo.
        self.root.after_idle(self._init_matplotlib_style)

    def _apply_minsize(self):
        """Fija el tamaño mínimo de la ventana contra la pantalla real.

        El mínimo tiene que CRECER con el DPI —en un equipo con el escalado
        de Windows al 150 % las fuentes se dibujan 1,5 veces más grandes y el
        mismo layout necesita 1,5 veces más píxeles— pero sin pasarse nunca
        del escritorio disponible. Con `minsize=(1200, 700)` fijo, en un
        portátil de 1366x768 —área útil 1366x728 con la barra de tareas— la
        ventana maximizada no podía encogerse por debajo de esos 700 px y la
        barra de estado terminaba debajo de la barra de tareas; en una
        pantalla más chica se iba también el borde derecho.
        """
        area = work_area(self.root)
        self.root.minsize(
            min(scaled(self.root, WINDOW_MIN_WIDTH), max(640, area[2] - 40)),
            min(scaled(self.root, WINDOW_MIN_HEIGHT), max(480, area[3] - 40)),
        )

    def _init_matplotlib_style(self):
        """Configura mathtext (CM) y calienta el cache de fuentes.

        Diferido fuera del constructor (via after_idle). `configure_latex_style`
        importa matplotlib y fija rcParams en el hilo principal (antes de crear
        cualquier figura). El cold-start del fontmanager/parser se calienta
        TROCEADO en el hilo principal (2-3 expresiones por tick via
        `after_idle`), evitando el cruce de hilos del antiguo daemon thread
        (pyplot/fontmanager no son thread-safe respecto al main loop de Tk).
        """
        try:
            from config.matplotlib_config import (
                configure_latex_style, MATHTEXT_WARMUP_EXPRESSIONS,
            )
            configure_latex_style()
            self._mathtext_warmup_queue = list(MATHTEXT_WARMUP_EXPRESSIONS)
            self.root.after_idle(self._warmup_mathtext_chunk)
        except Exception:
            pass

    def _warmup_mathtext_chunk(self):
        """Calienta el cache mathtext de a 3 expresiones por tick idle, en el
        hilo principal. Reagenda hasta vaciar la cola."""
        queue = getattr(self, "_mathtext_warmup_queue", None)
        if not queue:
            return
        chunk, self._mathtext_warmup_queue = queue[:3], queue[3:]
        try:
            from config.matplotlib_config import warmup_mathtext_chunk
            warmup_mathtext_chunk(chunk)
        except Exception:
            pass
        if self._mathtext_warmup_queue:
            self.root.after_idle(self._warmup_mathtext_chunk)

    # ═════════════════════════════════════════════════════════════════════
    # LAYOUT PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════

    def _build_main_layout(self):
        """Construye el layout principal con Notebook + Canvas compartido."""
        self.main_paned = ttk.Panedwindow(self.root, orient=HORIZONTAL)
        self.main_paned.pack(fill=BOTH, expand=YES, padx=3, pady=(3, 0))

        # ─── Panel izquierdo: Notebook con 3 pestanas ───────────────────
        self.left_panel = ttk.Frame(self.main_paned,
                                    width=scaled(self.root, 420))
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

        # Conectar paneles de modulos educativos (Pre/Proc/Post) al canvas
        # para reaccionar a la seleccion (iluminacion + chip #N).
        for tab in (self.pre_tab, self.proc_tab, self.post_tab):
            if hasattr(tab, "wire_canvas"):
                try:
                    tab.wire_canvas()
                except Exception:
                    # Sin cableado, el panel de modulos de esa fase no
                    # reacciona a la seleccion (nunca aparece el chip #N).
                    traceback.print_exc()

        # Fijar ancho inicial del panel lateral a 1/3 del ancho de pantalla.
        # El `width=420` del left_panel es ignorado por Panedwindow al
        # maximizar; sin `sashpos` el ratio weight=2:3 dejaria ~40% al
        # panel izquierdo. Diferimos via `after` para que el Panedwindow
        # ya este mapeado tras `state("zoomed")`.
        self.root.after(150, self._set_initial_sash)

    def _set_initial_sash(self):
        """Fija la posicion del sash del Panedwindow en 1/3 del ancho util.
        Idempotente: si el Panedwindow aun no tiene ancho real (el
        `state('zoomed')` puede tardar un par de ticks en propagar el
        resize), reagenda."""
        try:
            self.main_paned.update_idletasks()
            paned_width = self.main_paned.winfo_width()
            # Si el Panedwindow aun no tiene tamano util, reagendar.
            # `sashpos` con paned_width ≈ 1 resulta en sash en posicion 0,
            # lo que se ve como "panel lateral nulo" al iniciar en blanco.
            if paned_width < 100:
                self.root.after(80, self._set_initial_sash)
                return
            # 1/3 del ancho REAL del Panedwindow, no de la pantalla: en un
            # escritorio chico (o con la ventana sin maximizar) un tercio de
            # la pantalla se comia el canvas entero.
            x = max(scaled(self.root, 320), paned_width // 3)
            # Clampear para que el sash no quede fuera de rango (deja al
            # menos 200 px de diseño al panel derecho).
            x = min(x, paned_width - scaled(self.root, 200))
            self.main_paned.sashpos(0, x)
        except (tk.TclError, IndexError):
            self.root.after(100, self._set_initial_sash)

    # ═════════════════════════════════════════════════════════════════════
    # BARRA DE MENU — 3 menús: Archivo, Modelo, Ayuda
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
        # Orden FEM (5 items): geometría (elemento) → cómo medimos (unidades)
        # → de qué está hecho (material) → qué fuerzas volumétricas actúan
        # (gravedad, depende de ρ) → qué problema resolvemos (análisis).
        # Gravedad va DESPUÉS de Materiales porque la fuerza volumétrica
        # F = ρ·g·V depende de la densidad — es una carga, no una unidad.
        # Análisis va al final porque la matriz D depende del material
        # seleccionado (D = D(E, ν, caso plano)).
        menu_modelo = tk.Menu(self.menubar, tearoff=0)
        menu_modelo.add_command(
            label="🔲  Tipo de Elemento…",
            command=self._open_element_type_dialog,
        )
        menu_modelo.add_command(
            label="📏  Unidades…",
            command=self._open_units_dialog,
        )
        menu_modelo.add_command(
            label="🧱  Materiales…",
            command=self._on_material_properties,
        )
        menu_modelo.add_command(
            label="🌍  Gravedad…",
            command=self._open_gravity_dialog,
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
        # Hub de teoría MEF — antes vivía como botón "?" dentro de cada
        # módulo educativo. Movido al menú principal (UX 2026): la teoría
        # es transversal, no de un módulo específico.
        menu_ayuda.add_command(
            label="📘  Teoría MEF",
            command=self._on_open_theory_hub,
        )
        menu_ayuda.add_separator()

        # Submenu con los tres casos de estudio del software, cada uno en
        # variantes Q4 y Q9. Vive en Ayuda porque los ejemplos son material
        # didactico, no archivos del usuario.
        example_menu = tk.Menu(menu_ayuda, tearoff=0)

        # ─── Cuadrado de validación (4 elementos, ejemplo canónico) ────
        canon_menu = tk.Menu(example_menu, tearoff=0)
        canon_menu.add_command(
            label="Q4 — cuadrilátero bilineal",
            accelerator="Ctrl+E",
            command=lambda: self._on_load_example("canon_q4"),
        )
        canon_menu.add_command(
            label="Q9 — cuadrilátero bicuadrático",
            command=lambda: self._on_load_example("canon_q9"),
        )
        example_menu.add_cascade(
            label="Cuadrado de validación (4 elementos)", menu=canon_menu)

        # ─── Viga de Timoshenko ───────────────────────────────────────
        timoshenko_menu = tk.Menu(example_menu, tearoff=0)
        timoshenko_menu.add_command(
            label="Q4 — bilineal (esperado: shear-locking)",
            command=lambda: self._on_load_example("timoshenko_q4"),
        )
        timoshenko_menu.add_command(
            label="Q9 — bicuadrático (error < 0,3% vs analítico)",
            command=lambda: self._on_load_example("timoshenko_q9"),
        )
        example_menu.add_cascade(
            label="Viga de Timoshenko (simple apoyada)",
            menu=timoshenko_menu)

        # ─── Membrana de Cook (benchmark trapezoidal 1974) ────────────
        cook_menu = tk.Menu(example_menu, tearoff=0)
        cook_menu.add_command(
            label="Q4 — bilineal (esperado: convergencia lenta)",
            command=lambda: self._on_load_example("cook_q4"),
        )
        cook_menu.add_command(
            label="Q9 — bicuadrático (converge a u_y ≈ 23,95)",
            command=lambda: self._on_load_example("cook_q9"),
        )
        example_menu.add_cascade(
            label="Membrana de Cook (benchmark histórico)",
            menu=cook_menu)

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
            bootstyle="inverse-dark", font=FONT_UI, padding=(10, 4),
        )
        self.status_label.pack(side=LEFT)

        # Indicador ORTHO (solo visible en modo dibujo + ortho activo).
        # Se muestra a la derecha del status_label con `pack(side=LEFT)`
        # tras el toggle correspondiente; oculto via pack_forget.
        self.ortho_indicator_label = tk.Label(
            self.status_frame, text="ORTHO",
            fg=PHASE_PRE_COLOR, bg=STATUS_BAR_BG_COLOR,
            font=("Segoe UI", 9, "bold"), padx=10, pady=4,
        )
        # No pack inicial — se gestiona desde _update_ortho_indicator.

        # (El breadcrumb glifico Ⓜ ① … ⑦ que vivia aca se fue el 2026-09-09:
        # la cadena del metodo es ahora la tira `N › J › B › D › kₑ › F › K`
        # del banner de Proceso — gui/widgets/method_strip.py —, siempre
        # visible en su fase y con nombre en cada chip.)

        self.info_label = ttk.Label(
            self.status_frame, text="",
            bootstyle="inverse-dark", font=FONT_UI, padding=(10, 4),
        )
        self.info_label.pack(side=RIGHT)

        self.analysis_label = ttk.Label(
            self.status_frame, text="",
            bootstyle="inverse-dark", font=FONT_UI, padding=(10, 4),
        )
        self.analysis_label.pack(side=RIGHT)

        # Badge de salud del modelo (✓/⚠/✗ + conteo). Click abre el
        # HealthReportDialog en modo solo-lectura. Se actualiza en cada
        # _update_status_info (modelo modificado, post-fix, etc.).
        # Uso `tk.Label` directo para poder pintar foreground por
        # severidad sin depender del bootstyle del tema.
        self.health_badge = tk.Label(
            self.status_frame, text="✓ Modelo sano",
            fg=HEALTH_OK_COLOR, bg=STATUS_BAR_BG_COLOR,
            font=("Segoe UI", 9, "bold"), padx=10, pady=4,
            cursor="hand2",
        )
        self.health_badge.pack(side=RIGHT)
        self.health_badge.bind("<Button-1>",
                               lambda _e: self._on_health_badge_click())
        # El badge tiene cursor de mano pero nada dice que se puede abrir.
        ToolTip(self.health_badge,
                text="Salud del modelo — click para ver el reporte completo")

        self._update_status_info()

    def set_status(self, message):
        """Actualiza el mensaje de la barra de estado."""
        self.status_label.config(text=f"  {message}")

    def _update_status_info(self):
        """Actualiza la informacion del modelo en la barra de estado.

        Los conteos van en terminos del sistema que la malla genera: `2N`
        GDL y cuantos quedan como incognitas tras aplicar las restricciones
        (el tamano de K_red), que es lo que el Proceso muestra en detalle.
        """
        at = self.project.analysis_type
        et = self.project.element_type.split(' ')[0]
        self.analysis_label.config(text=f"{at} | {et}")
        n_dof = self.project.total_dof
        try:
            n_free = n_dof - len(self.project.get_restrained_dofs())
        except Exception:
            n_free = n_dof
        self.info_label.config(
            text=f"Nodos: {self.project.num_nodes}  |  "
                 f"Elementos: {self.project.num_elements}  |  "
                 f"GDL: {n_dof} ({n_free} incógnitas)"
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
            # Badge congelado en el ultimo veredicto: dejar traza, sino el
            # alumno ve "Modelo sano" sobre un modelo que ya no se valido.
            traceback.print_exc()
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

        # Dos proyectos con el mismo nombre de archivo en carpetas
        # distintas (`viga.edufem` en dos trabajos prácticos) se veían
        # como dos entradas idénticas: no había forma de elegir. Solo en
        # ese caso se agrega la carpeta, para no ensanchar el menú cuando
        # el nombre ya alcanza.
        nombres = [os.path.basename(p) for p in paths]
        for i, path in enumerate(paths):
            nombre = nombres[i]
            if nombres.count(nombre) > 1:
                carpeta = os.path.basename(os.path.dirname(path)) or path
                etiqueta = f"{i + 1}. {nombre}   ({carpeta})"
            else:
                etiqueta = f"{i + 1}. {nombre}"
            self.recent_menu.add_command(
                label=etiqueta,
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
        # Ctrl+1..7 para módulos educativos en orden canónico FEM.
        # Mapeo: Ctrl+1=mod01 (mapeo) ... Ctrl+5=mod05 (rigidez K_e +
        # cuadratura de Gauss, fusionado) · Ctrl+6=mod06 (fuerzas) ·
        # Ctrl+7=mod07 (ensamblaje).
        _kbd_map = ["mod01", "mod02", "mod03", "mod04",
                     "mod05", "mod06", "mod07"]
        for i, mod_key in enumerate(_kbd_map, start=1):
            key = f"<Control-Key-{i}>"
            b(key, lambda e, mk=mod_key: self._open_education_module(mk))
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

    def _confirm_discard_changes(self, titulo: str, accion: str) -> bool:
        """Pregunta qué hacer con los cambios sin guardar antes de una
        acción que destruye el modelo en memoria (nuevo proyecto, cargar
        ejemplo, salir). Retorna True si se puede continuar.

        **Por qué existe**: los tres flujos preguntaban por separado, con
        redacciones distintas ("¿Desea guardar los cambios?" / "Se
        perderán los datos actuales. ¿Guardar?" / "¿Guardar cambios?") y,
        peor, los tres **seguían adelante igual** si el guardado no se
        completaba: contestar *Sí* y después cancelar el diálogo de
        *Guardar Como* —o que fallara la escritura— descartaba el modelo
        sin decir nada. Acá el guardado tiene que confirmar que ocurrió
        (`_on_save_project` devuelve bool) para que la acción siga.
        """
        if not self.project.is_modified:
            return True
        resp = messagebox.askyesnocancel(
            titulo,
            "El proyecto tiene cambios sin guardar.\n\n"
            f"Sí → Guardar y {accion}\n"
            f"No → {accion.capitalize()} descartando los cambios\n"
            "Cancelar → Volver al modelo",
        )
        if resp is None:
            self.set_status(f"{titulo}: cancelado, el modelo sigue abierto.")
            return False
        if resp and not self._on_save_project():
            # El guardado no llegó a disco (Guardar Como cancelado o error
            # de escritura). Abortar: descartar el modelo acá sería la
            # acción destructiva que el alumno justo pidió evitar.
            self.set_status(
                f"{titulo}: cancelado porque el proyecto no se guardó. "
                "El modelo sigue abierto."
            )
            return False
        return True

    def _on_new_project(self):
        if not self._confirm_discard_changes("Nuevo Proyecto", "crear el nuevo"):
            return

        self.project.reset()
        self.undo_stack.clear()
        self.mesh_canvas.project = self.project
        self.mesh_canvas.clear_results_overlay()
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
            traceback.print_exc()   # el mensaje es una linea; el traceback no
            messagebox.showerror("Error", f"No se pudo abrir el proyecto:\n{e}")

    def _on_load_example(self, variant: str = "canon_q4"):
        """Carga uno de los ejemplos didacticos del software.

        Variantes soportadas (atajo Ctrl+E carga "canon_q4"):
            "canon_q4" / "canon_q9" -- cuadrado de validacion (9 nodos, 4 elems)
            "timoshenko_q4" / "timoshenko_q9" -- viga simple apoyada
                                                 (docs/vyv/, comparable con
                                                 tesis/anexos/validacion_sap2000.pdf)
            "cook_q4" / "cook_q9" -- membrana trapezoidal de Cook (1974)
        """
        if not self._confirm_discard_changes("Cargar Ejemplo", "cargar el ejemplo"):
            return

        # Despacho por variante: cada bloque importa el loader perezosamente
        # y compone un mensaje informativo para la status bar.
        if variant == "canon_q9":
            from models.example_library import load_example_project_q9
            self.project = load_example_project_q9(P=1000.0)
            variant_msg = (
                "Ejemplo Q9: 9 nodos vértices + medios + centroides, "
                "4 elementos bicuadráticos, E=225000, ν=0.2, P=1000 N"
            )
        elif variant == "timoshenko_q4":
            from models.example_library import load_example_timoshenko_q4
            self.project = load_example_timoshenko_q4()
            variant_msg = (
                "Viga Timoshenko Q4 (14×4): L=14 m, H=1,20 m, "
                "E=217370 kgf/cm², q=5000 kgf/m. F5 para resolver."
            )
        elif variant == "timoshenko_q9":
            from models.example_library import load_example_timoshenko_q9
            self.project = load_example_timoshenko_q9()
            variant_msg = (
                "Viga Timoshenko Q9 (14×4 macro): error < 0,3% vs analítico "
                "para σ_x y δ_máx. Validada en docs/vyv/ con SAP2000."
            )
        elif variant == "cook_q4":
            from models.example_library import load_example_cook_q4
            self.project = load_example_cook_q4()
            variant_msg = (
                "Membrana de Cook Q4 (8×8): u_y(48,52) esperado ~22,08 "
                "(error -7,8% vs ref 23,95 — shear-locking parcial)."
            )
        elif variant == "cook_q9":
            from models.example_library import load_example_cook_q9
            self.project = load_example_cook_q9()
            variant_msg = (
                "Membrana de Cook Q9 (8×8 macro): u_y(48,52) esperado ~23,93 "
                "(error -0,10% vs ref 23,95)."
            )
        else:  # "canon_q4" o cualquier valor desconocido
            from models.example_library import load_example_project
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
        self.mesh_canvas.clear_results_overlay()
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

    def _on_save_project(self) -> bool:
        """Ctrl+S / Archivo ▸ Guardar. Retorna True si, al salir, el
        proyecto está a salvo en disco.

        El valor de retorno lo consume `_confirm_discard_changes`: sin él
        una acción destructiva seguía adelante aunque el guardado se
        hubiera cancelado.
        """
        if not self.project.is_modified:
            # El ítem de menú está gris en este estado, pero el atajo
            # Ctrl+S se dispara igual: una tecla que no hace nada y
            # tampoco lo dice es un callejón sin salida.
            self.set_status("No hay cambios para guardar.")
            return True
        if self.project.file_path is None:
            return self._on_save_as_project()
        return self._save_to_file(self.project.file_path)

    def _on_save_as_project(self) -> bool:
        """Archivo ▸ Guardar Como. Retorna True si se escribió el archivo."""
        filepath = filedialog.asksaveasfilename(
            title="Guardar Proyecto Como",
            defaultextension=PROJECT_FILE_EXTENSION,
            filetypes=[
                (PROJECT_FILE_DESCRIPTION, f"*{PROJECT_FILE_EXTENSION}"),
                ("Archivos JSON", "*.json"),
            ],
        )
        if not filepath:
            self.set_status("Guardado cancelado — el proyecto no se guardó.")
            return False
        return self._save_to_file(filepath)

    def _save_to_file(self, filepath) -> bool:
        try:
            # Delega en save_project (escritura atómica: tmp + fsync + replace).
            from file_io.project_io import save_project
            save_project(self.project, filepath)
            self.set_status(f"Proyecto guardado: {os.path.basename(filepath)}")

            recent_files.add(filepath)
            self._build_recent_menu()
            self._update_title()
            self._refresh_menu_state()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
            return False

    def _on_export_pdf(self):
        """Exporta la Memoria de Cálculo (PDF) — documento educativo paso
        a paso del análisis FEM, con fórmulas LaTeX, matrices y diagramas.

        Compila vía pylatex + pdflatex (requiere MiKTeX/TeX Live instalado).
        La compilación corre en un hilo aparte para no congelar la GUI;
        un diálogo de progreso indeterminado acompaña al usuario.

        **Guard `_exportando_pdf`** (mismo patrón que el `_solving` de
        `post_tab.auto_solve`): el `_PDFProgressDialog` no es modal a
        propósito, así que el alumno puede volver al menú y pedir otra
        Memoria con una compilación en curso. Sin el guard arrancaban dos
        threads y, si elegía el mismo destino, los dos escribían el mismo
        `.pdf`. Se libera en `_on_done`, que corre en el hilo principal.
        """
        if self._exportando_pdf:
            self.set_status(
                "Ya hay una Memoria de Cálculo compilándose — esperá a que "
                "termine antes de exportar otra."
            )
            return

        if not self.project.is_solved:
            messagebox.showwarning(
                "Aviso",
                "Debe resolver el modelo antes de exportar la Memoria de Cálculo.\n"
                "Abra la pestaña POST-PROCESO o pulse F5.",
            )
            return

        # Selección de estilo antes del filedialog — Cancelar aborta limpiamente.
        from gui.dialogs.memoria_style_dialog import MemoriaStyleDialog
        style_dlg = MemoriaStyleDialog(self.root)
        style = style_dlg.result
        if style is None:
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

        from file_io.memoria_calculo import (
            generate_memoria_calculo, MemoriaCalculoError,
        )
        from fem.stress import compute_all_stresses

        solution = self.post_tab.solution
        nodal_stresses = self.post_tab.nodal_stresses
        try:
            element_stresses, _ = compute_all_stresses(self.project, solution)
        except Exception:
            # La memoria sale sin las tensiones por elemento: dejar traza.
            traceback.print_exc()
            element_stresses = None

        # Snapshot inmutable del modelo: el progress dialog NO hace grab_set,
        # asi que el usuario puede seguir editando mientras el worker genera
        # el PDF. Sin la copia, el thread leeria un project mutandose (PDF
        # inconsistente o excepcion espuria).
        try:
            project_snapshot = ProjectModel.from_dict(self.project.to_dict())
        except Exception:
            # Sin copia el worker lee un project que el alumno puede estar
            # mutando: el PDF puede salir inconsistente. Dejar traza.
            traceback.print_exc()
            project_snapshot = self.project

        # Dialog de progreso (no bloqueante para la GUI; el thread worker
        # llama root.after(0, ...) para actualizarlo desde el otro hilo).
        progress = _PDFProgressDialog(self.root)

        # Estado del worker (escrito desde el thread, leido desde el main).
        result_state = {"path": None, "error": None}

        def _on_progress(stage: str, pct: float) -> None:
            self.root.after(0, progress.update_stage, stage, pct)

        def _worker():
            try:
                path = generate_memoria_calculo(
                    project_snapshot, solution, element_stresses,
                    nodal_stresses, filepath, style=style,
                    progress_callback=_on_progress,
                )
                result_state["path"] = path
            except Exception as e:
                result_state["error"] = e
            finally:
                self.root.after(0, _on_done)

        def _on_done():
            # Liberar el guard ANTES de cualquier diálogo: los messagebox de
            # abajo son modales y bloquean este handler hasta que el alumno
            # responde; si el flag se bajara al final, Exportar quedaría
            # bloqueado todo ese rato sin que nada esté compilando.
            self._exportando_pdf = False
            try:
                progress.close()
            except Exception:
                pass
            err = result_state["error"]
            path = result_state["path"]
            if err is not None:
                from file_io.memoria_calculo import PdflatexNotFoundError
                if isinstance(err, PdflatexNotFoundError):
                    # Falta LaTeX: ofrecer descarga en vez de un error seco.
                    from gui.dialogs.pdflatex_missing_dialog import (
                        show_pdflatex_missing_dialog,
                    )
                    show_pdflatex_missing_dialog(self.root)
                else:
                    messagebox.showerror(
                        "Error",
                        f"Error al generar la Memoria de Cálculo:\n{err}"
                    )
                return
            if path is None:
                messagebox.showerror(
                    "Error",
                    "La generación terminó sin producir archivo."
                )
                return
            self.set_status(
                f"Memoria de Cálculo exportada: {os.path.basename(path)}"
            )
            respuesta = messagebox.askyesno(
                "Memoria de Cálculo exportada",
                f"Documento guardado exitosamente en:\n{path}\n\n"
                f"¿Abrir el PDF ahora?",
            )
            if not respuesta:
                return
            # `os.startfile` solo existe en Windows —la plataforma de
            # distribucion—: en cualquier otra el AttributeError se comia
            # el "Si" del alumno sin abrir nada ni decir por que.
            try:
                os.startfile(path)      # noqa: attr-defined (solo Windows)
            except Exception:
                traceback.print_exc()
                self.set_status(
                    f"No se pudo abrir el PDF automáticamente. "
                    f"Está en: {path}"
                )

        import threading
        self._exportando_pdf = True
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

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
        if not self._confirm_discard_changes("Salir", "salir"):
            return
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
        # apuntar a items inexistentes. La logica vive en el canvas
        # (`prune_dead_selection`), que es quien conoce sus seis sets y el
        # unico que debe emitir `on_selection_changed`.
        try:
            self.mesh_canvas.prune_dead_selection()
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
            # Si el refresco falla, la UI sigue mostrando el modelo de
            # ANTES del undo: el Ctrl+Z parece no haber hecho nada.
            traceback.print_exc()

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — MODELO (5 diálogos pop-up autónomos en orden FEM:
    # elemento → unidades → materiales → gravedad → análisis)
    # ═════════════════════════════════════════════════════════════════════

    def _open_element_type_dialog(self):
        ElementTypeDialog(self.root, self.project, self)

    def _open_analysis_type_dialog(self):
        AnalysisTypeDialog(self.root, self.project, self)

    def _open_units_dialog(self):
        UnitsDialog(self.root, self.project, self)

    def _open_gravity_dialog(self):
        GravityDialog(self.root, self.project, self)

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

    def _on_open_theory_hub(self):
        """Abre el hub de teoría del MEF (Ayuda ▸ Teoría MEF).

        Reemplaza al botón '?' que cada módulo educativo tenía en su
        header. La teoría es transversal a los módulos y vive en un
        único documento navegable accesible desde cualquier parte del
        flujo, no solo cuando un módulo está abierto.
        """
        from gui.dialogs.theory_hub_dialog import open_theory_hub
        open_theory_hub(self.root)

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS — VISTA / ANALISIS
    # ═════════════════════════════════════════════════════════════════════

    def _on_solve(self):
        """Resuelve el modelo (F5). Delega en `post_tab.auto_solve`.

        **Una sola vía de validación**: acá no se chequea nada por
        cuenta propia. `auto_solve` corre
        `models.model_health.validate_project` y, si hay errores críticos,
        abre el `HealthReportDialog`, que nombra la causa, explica el "¿por
        qué?" y ofrece corrección automática y navegación al ítem
        (regla dura 16).

        Antes había dos pre-chequeos propios (sin elementos / sin
        restricciones) que cortaban el flujo con un `showwarning` seco:
        nombraban el problema pero no cómo resolverlo, no cubrían el resto
        de los errores críticos (restricciones insuficientes, elemento
        degenerado, referencia colgante) y dejaban al atajo F5 con **menos**
        diagnóstico que el simple cambio de pestaña — al revés de lo que
        describe la tesis (Anexo A, «Proceso: resolución y exploración
        didáctica»), que promete el comprobador de salud detrás de F5.
        """
        # Forzar la re-resolución: si el proyecto ya estaba resuelto,
        # `auto_solve` se limitaría a repintar.
        self.project.is_solved = False
        self.post_tab.solution = None
        # Tk entrega `<<NotebookTabChanged>>` DESPUÉS del `select()` (no
        # durante), así que resolvemos nosotros y el handler encolado
        # encuentra el modelo ya resuelto; si ya estábamos en Post el
        # evento no se dispara y esta llamada es la única. El guard de
        # reentrancia de `auto_solve` cubre el caso en que el diálogo de
        # salud quede abierto mientras se despacha el evento.
        self.notebook.select(2)
        self.post_tab.auto_solve()

    def _on_fit_view(self):
        try:
            self.mesh_canvas.fit_view()
        except Exception:
            traceback.print_exc()
            self.set_status("No se pudo ajustar la vista.")

    def _on_toggle_draw_mode(self):
        """Atajo D: delega al pre_tab para que aplique pre-flight de
        material y luego llame al canvas. Tambien navega a la pestana
        Pre-Proceso si no estamos ahi."""
        try:
            if self.notebook.index(self.notebook.select()) != 0:
                self.notebook.select(0)
            self.pre_tab._on_toggle_draw_mode()
        except Exception:
            # La tecla D es el acceso principal al dibujo: si falla, no
            # puede quedarse muda.
            traceback.print_exc()
            self.set_status("No se pudo activar el modo dibujo.")

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
        estado = "activado" if canvas.ortho_active else "desactivado"
        if canvas.draw_mode_active:
            self.set_status(f"ORTHO {estado}")
        else:
            # Fuera del modo dibujo el indicador de la barra no se muestra
            # (solo tiene sentido mientras se dibuja), asi que el toggle
            # era COMPLETAMENTE invisible: el alumno pulsaba F8, no pasaba
            # nada en pantalla, y el estado aparecia recien al entrar en
            # modo dibujo. Se dice que queda armado y con que tecla se usa.
            self.set_status(
                f"ORTHO {estado} — se aplica al dibujar elementos (tecla D)"
            )

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
        3) Si modo consulta (probe) activo con pines -> limpiar pines
        4) Si hay seleccion en canvas -> limpiarla (asi desaparecen las
           filas fantasma de las sub-pestañas)
        5) Sino -> no pasa nada
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
            traceback.print_exc()
        # 3) Consulta interactiva: si hay pines, limpiarlos. Si no hay
        # pines pero el modo esta activo, dejar que la cascada siga (el
        # usuario puede querer limpiar tambien una seleccion residual).
        try:
            probe = getattr(self.post_tab, "probe_overlay", None)
            if probe is not None and probe.active and probe.has_pinned():
                probe.clear_pinned()
                self.set_status("Probes limpiadas")
                return
        except Exception:
            traceback.print_exc()
        # 4) Selecciones en canvas (limpia tambien las filas fantasma
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
        """F11: pantalla completa. El flag se actualiza SOLO si Tk aceptó
        el cambio — si no, quedaba desincronizado y el siguiente F11
        intentaba lo contrario de lo que se ve en pantalla.

        En pantalla completa desaparece la barra de menús, que es donde
        está escrito el atajo: por eso el aviso nombra la tecla de salida.
        """
        objetivo = not self._is_fullscreen
        try:
            self.root.attributes("-fullscreen", objetivo)
        except tk.TclError:
            self.set_status(
                "Pantalla completa no disponible en este sistema de ventanas."
            )
            return
        self._is_fullscreen = objetivo
        if objetivo:
            self.set_status("Pantalla completa — F11 para volver a la ventana")
        else:
            self.set_status("Pantalla completa desactivada")

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
        """F1 / Ayuda ▸ Manual de Usuario.

        Antes decía «Manual de usuario próximamente» y mandaba a los
        atajos: un ítem de menú que promete algo y no lo da. Los atajos
        ya tienen su propia ventana (Ctrl+/) y no son un manual — no
        dicen en qué orden se arma un modelo ni dónde vive cada cosa.
        Acá va ese recorrido, que es lo que le falta al alumno que abre
        el programa por primera vez. Cada línea nombra dónde está la
        acción en la interfaz real (los 3 menús, las 3 fases).
        """
        manual = (
            "CÓMO SE USA EDUFEM\n"
            "─────────────────────────────\n"
            "El flujo son las tres pestañas de la izquierda, en orden.\n\n"
            "① PRE-PROCESO — armar el modelo\n"
            "  • Ayuda ▸ Cargar Ejemplo (Ctrl+E) trae un caso listo:\n"
            "    es la forma más rápida de ver todo funcionando.\n"
            "  • Tecla D dibuja elementos clickeando en el lienzo\n"
            "    (F8 = ORTHO; Backspace borra el último vértice).\n"
            "  • Las 5 tablas (Nodos, Elementos, Cargas, Restricciones,\n"
            "    Carg. Superf.) se editan con doble-click, aceptan pegado\n"
            "    desde Excel con Ctrl+V y borran la selección con Supr.\n"
            "  • Menú Modelo: tipo de elemento (Q4/Q9), unidades,\n"
            "    materiales, gravedad y tipo de análisis (TP/DP).\n\n"
            "② PROCESO — entender el cálculo\n"
            "  • Clickeá un elemento en el lienzo y abrí los módulos\n"
            "    M1…M7 (Ctrl+1 … Ctrl+7): mapeo, Jacobiano, B, D,\n"
            "    rigidez y cuadratura de Gauss, fuerzas y ensamblaje.\n"
            "  • Se dibujan sobre la malla real, no sobre un dibujito.\n\n"
            "③ POST-PROCESO — leer los resultados\n"
            "  • F5 resuelve. Antes valida el modelo: si falta algo, el\n"
            "    comprobador de salud dice qué y ofrece corregirlo.\n"
            "  • Deformada, campos de tensión, isolíneas, consulta\n"
            "    interactiva sobre el lienzo y Vista 3D.\n"
            "  • Ctrl+C copia la tabla o el punto consultado (pegable\n"
            "    en Excel).\n\n"
            "GUARDAR Y EXPORTAR\n"
            "  • Archivo ▸ Guardar (Ctrl+S) escribe un .edufem.\n"
            "  • Archivo ▸ Exportar ▸ Memoria de Cálculo (PDF) genera el\n"
            "    documento paso a paso del análisis ya resuelto.\n"
            "  • Archivo ▸ Importar acepta geometría DXF y modelos en\n"
            "    Excel/CSV.\n\n"
            "SI ALGO SALE MAL\n"
            "  • Ctrl+Z deshace; el badge de la barra inferior (✓/⚠/✗)\n"
            "    abre el reporte de salud del modelo.\n\n"
            "MÁS AYUDA\n"
            "  • Ayuda ▸ Teoría MEF — la teoría detrás de cada paso.\n"
            "  • Ayuda ▸ Atajos de Teclado (Ctrl+/) — la lista completa."
        )
        messagebox.showinfo("Manual de Usuario", manual)

    def _on_shortcuts(self):
        shortcuts = (
            "ATAJOS DE TECLADO\n"
            "─────────────────────────────\n"
            "Archivo\n"
            "  Ctrl+N           Nuevo Proyecto\n"
            "  Ctrl+O           Abrir Proyecto\n"
            "  Ctrl+S           Guardar\n"
            "  Ctrl+Shift+S     Guardar Como\n"
            "  Ctrl+Q           Salir\n\n"
            "Edición\n"
            "  Ctrl+Z           Deshacer\n"
            "  Ctrl+Y           Rehacer\n"
            "  Ctrl+Shift+Z     Rehacer (alternativo)\n"
            "  Supr             Borrar la selección (lienzo y tablas)\n"
            "  Esc              Cancelar / limpiar la selección\n\n"
            "Tablas del Pre-Proceso\n"
            "  Doble click      Editar la celda\n"
            "  Ctrl+C           Copiar las filas seleccionadas (TSV)\n"
            "  Ctrl+V           Pegar filas desde Excel (TSV)\n\n"
            "Análisis\n"
            "  F5               Resolver modelo\n\n"
            "Post-Proceso\n"
            "  Ctrl+C           Copiar la tabla o el punto consultado\n"
            "  Ctrl+A           Seleccionar toda la tabla de resultados\n\n"
            "Educación\n"
            "  Ctrl+1           M1 · Mapeo iso + funciones N\n"
            "  Ctrl+2           M2 · Jacobiano det J\n"
            "  Ctrl+3           M3 · Matriz B\n"
            "  Ctrl+4           M4 · Matriz Constitutiva D\n"
            "  Ctrl+5           M5 · Rigidez K_e + Cuadratura de Gauss\n"
            "  Ctrl+6           M6 · Fuerzas Equivalentes\n"
            "  Ctrl+7           M7 · Ensamblaje K, F + BCs\n\n"
            "Vista\n"
            "  F                Ajustar Vista\n"
            "  F11              Pantalla Completa\n"
            "  Ctrl+Tab         Siguiente Pestaña\n"
            "  Ctrl+Shift+Tab   Pestaña Anterior\n\n"
            "Modelado (estilo AutoCAD)\n"
            "  D                Dibujar elemento (toggle, click en el lienzo)\n"
            "  F8               ORTHO toggle (Shift = override instantáneo)\n"
            "  Backspace        Borrar el último vértice del elemento parcial\n"
            "  Esc              Cancelar elemento parcial / salir del modo\n"
            "  En el Entry:\n"
            "    100            Coord relativa al último vértice (default)\n"
            "    #150           Coord absoluta (override)\n"
            "    @30            Relativa explícita (no-op tolerado)\n"
            "    100,50         Coma = separador X -> Y\n"
            "    8 + Enter (Y vacío + ORTHO) = distancia directa sobre\n"
            "    el eje del cursor (DDE estilo AutoCAD)\n\n"
            "Ayuda\n"
            "  F1               Manual de Usuario\n"
            "  Ctrl+E           Cargar Ejemplo\n"
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
        # La barra de estado dice que hace el metodo en la fase que se abre,
        # con los numeros del modelo actual, en vez de repetir el nombre de
        # la pestana ("Pestaña activa: Proceso").
        self.set_status(self._phase_message(tab_index))

        if tab_index == 0:
            # Volver a Pre-Proceso: el canvas debe mostrar solo geometria,
            # no la deformada / mapa de colores / isolineas que dejo Post.
            # Tambien desactivar el probe overlay y la vista 3D cuyos
            # bindings/vistas no tienen sentido fuera de Post.
            self.post_tab.deactivate_probe_overlay()
            self.post_tab.deactivate_advanced_views()
            self.mesh_canvas.clear_results_overlay()
            self.mesh_canvas.set_phase("pre")
            self.pre_tab.refresh()
        elif tab_index == 1:
            # Modo dibujo no tiene sentido fuera de Pre-Proceso.
            if self.mesh_canvas.is_draw_mode_active():
                self.mesh_canvas.disable_draw_mode()
            self.post_tab.deactivate_probe_overlay()
            self.post_tab.deactivate_advanced_views()
            self.mesh_canvas.clear_results_overlay()
            self.mesh_canvas.set_phase("proc")
            self.proc_tab.refresh()
        elif tab_index == 2:
            if self.mesh_canvas.is_draw_mode_active():
                self.mesh_canvas.disable_draw_mode()
            # Limpiar cualquier seleccion arrastrada desde Pre/Proc: en Post no
            # hay seleccion de elementos y su relleno taparia el contorno
            # (interferencia reportada por el usuario 2026-05-31).
            self.mesh_canvas.clear_highlights()
            self.post_tab.auto_solve()
            # Reactivar probe si el usuario lo dejo ON en una visita previa
            self.post_tab.maybe_reactivate_probe_overlay()
            self.mesh_canvas.set_phase("post")

        self.mesh_canvas.redraw()
        self._refresh_menu_state()

    def _phase_message(self, tab_index):
        """Mensaje de la barra de estado al entrar a una fase: que hace el
        metodo ahi, con los numeros del modelo actual."""
        p = self.project
        n_dof = p.total_dof
        try:
            n_res = len(p.get_restrained_dofs())
        except Exception:
            n_res = 0
        if tab_index == 0:
            if not p.elements:
                return ("Pre-Proceso: discretizá el dominio — tecla D dibuja "
                        "elementos, Ctrl+E carga un ejemplo")
            return (f"Pre-Proceso: {p.num_nodes} nodos · {p.num_elements} "
                    f"elementos → {n_dof} GDL ({n_dof - n_res} incógnitas) · "
                    f"el badge de salud dice qué falta")
        if tab_index == 1:
            k = 18 if p.element_type == ELEMENT_Q9_LABEL else 8
            return (f"Proceso: cada elemento aporta su kₑ ({k}×{k}) a "
                    f"K ({n_dof}×{n_dof}); {n_res} GDL restringidos dejan "
                    f"{n_dof - n_res} incógnitas · F5 resuelve K·u = F")
        return ("Post-Proceso: de u salen ε = B·u y σ = D·ε en cada "
                "elemento; los apoyos devuelven R = K·u − F")

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


# ═════════════════════════════════════════════════════════════════════════
# Dialogo de progreso para la compilacion del PDF (Memoria de Calculo).
# ═════════════════════════════════════════════════════════════════════════

class _PDFProgressDialog:
    """Toplevel minimalista con label + Progressbar indeterminado.

    Pensado para acompañar la compilacion de la Memoria de Calculo (que
    corre en un thread aparte). El thread llama `update_stage` via
    `main_window.after(0, ...)` para evitar tocar Tk desde otro hilo.

    No es modal con grab_set: la GUI sigue interactiva, pero el dialog
    queda topmost y subordinado a la ventana padre.
    """

    def __init__(self, parent):
        self._parent = parent
        try:
            self.top = tk.Toplevel(parent)
            self.top.title("Generando Memoria de Cálculo")
            self.top.transient(parent)
            # Sin `resizable(False, False)`: esta ventana se ajusta a su
            # contenido, pero si la etapa que muestra el label es más larga
            # que la pantalla, el alumno tiene que poder agrandarla.
            # No grab_set — el usuario puede seguir mirando la GUI.
            frame = ttk.Frame(self.top, padding=16)
            frame.pack(fill=BOTH, expand=YES)
            self._lbl = ttk.Label(
                frame,
                text="Inicializando…",
                font=FONT_UI_LARGE,
            )
            self._lbl.pack(anchor="w", pady=(0, 8))
            self._bar = ttk.Progressbar(
                frame, mode="indeterminate", length=320,
                bootstyle="info",
            )
            self._bar.pack(fill="x")
            self._bar.start(12)
            # Centrar respecto al padre, dentro del area util.
            center_on_parent(self.top, parent)
            # Bloquear cierre con la X (hasta que termine).
            self.top.protocol("WM_DELETE_WINDOW", lambda: None)
        except Exception:
            self.top = None
            self._lbl = None
            self._bar = None

    def update_stage(self, stage: str, pct: float) -> None:
        if self._lbl is None:
            return
        try:
            self._lbl.config(text=stage)
        except Exception:
            pass

    def close(self) -> None:
        if self.top is None:
            return
        try:
            self._bar.stop()
        except Exception:
            pass
        try:
            self.top.destroy()
        except Exception:
            pass
        self.top = None
