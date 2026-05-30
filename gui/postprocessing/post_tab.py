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
    CANVAS_SELECTED_COLOR,
)
from gui.widgets.phase_banner import build_phase_banner
from gui.widgets.module_launcher_panel import render_module_buttons
from models.model_health import validate_project


class PostProcessTab:
    """Panel de Post-Proceso con auto-solve y visualizacion reactiva."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)

        # Estado de resultados
        self.solution = None
        self.nodal_stresses = None
        self.element_stresses = None   # consumido por ProbeOverlay
        self.probe_overlay = None      # se instancia tras primer auto_solve

        # Vistas avanzadas (lazy, dependen de is_solved)
        self.surface_3d_viewer = None      # Toplevel 3D del campo
        self.principal_cross_layer = None  # capa de cruces σ1/σ2 (toggle)

        # Cache de las grillas crudas D·B·uₑ por elemento (TODOS los campos
        # σx/σy/τxy/σ1/σ2/VM evaluados en la grilla). Se computa una vez tras
        # el solve y se invalida al re-resolver. Evita re-evaluar D·B·uₑ al
        # cambiar de resultado (VM↔σx) o al togglear deformada/isolíneas.
        self._raw_grid_cache = None

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

        # Banner de salud removido del Post: el badge ✓/⚠/✗ del status bar
        # global y el HealthReportDialog modal antes del solve cubren todo
        # el feedback de warnings/errores. El modelo (validate_project)
        # sigue intacto y el dialogo se sigue abriendo bloqueante en
        # `auto_solve` cuando hay errores criticos.

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

        # Sub-tab 3: Modulos educativos (M9 convergencia Q4 vs Q9)
        self.education_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.education_frame, text="  🎓 Educacion  ")
        self._build_education_tab()

    def _build_education_tab(self):
        """Modulos educativos del POST-PROCESO."""
        from education.module_launcher import (
            list_modules_for_phase, open_module, GLOBAL_MODULES,
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
            return ok  # el panel marca ✓ solo si realmente abrio

        self._edu_panel = render_module_buttons(
            self.education_frame,
            modules=list_modules_for_phase("post"),
            on_open=_on_open,
            bootstyle=f"{PHASE_POST_BOOTSTYLE}-outline",
            header_text="Modulos Educativos · Post-Proceso",
            header_color=PHASE_POST_COLOR,
            subtitle=("Comparacion Q4 vs Q9 y convergencia h-refinement.\n"
                      "Las vistas 3D, cruces principales y circulo de Mohr\n"
                      "estan integradas en la toolbar y en el clic derecho\n"
                      "del probe. Requiere modelo resuelto (F5)."),
            global_modules=GLOBAL_MODULES,
        )

    def wire_canvas(self):
        """Conecta el panel educativo al canvas para iluminacion reactiva.

        El post solo tiene M9 (sandbox global, no requiere elemento) por
        ahora — el wiring es defensivo por si en el futuro se agrega un
        modulo por-elemento al post."""
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None or getattr(self, "_edu_panel", None) is None:
            return
        prev = canvas.on_selection_changed
        if prev is not None and getattr(prev, "_post_edu_chain", False):
            return  # ya cableado

        def _chained(sel: dict, _prev=prev):
            if _prev is not None:
                try:
                    _prev(sel)
                except Exception:
                    pass
            try:
                elems = sel.get("elements", set()) if sel else set()
                eid = next(iter(elems)) if len(elems) == 1 else None
                self._edu_panel.update_selection(eid)
            except Exception:
                pass

        _chained._post_edu_chain = True
        canvas.on_selection_changed = _chained
        try:
            self._edu_panel.update_selection(None)
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════
    # SUB-TAB: VISUALIZACION
    # ═════════════════════════════════════════════════════════════════════

    def _build_visualization_tab(self):
        """Controles de visualizacion con auto-update.

        Sin scroll: el contenido (Tipo de Resultado, Deformada, Isolineas,
        Inspeccion del campo) cabe en cualquier pantalla 1080p+ con el
        ancho actual del panel lateral. En pantallas mas chicas el
        contenido podria cortarse abajo (decision documentada).
        """
        container = self.viz_frame

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

        # ─── Inspeccion del campo (probe + Gauss + Vista 3D) ─────────────
        # Conjunto de herramientas para inspeccionar el campo de resultados
        # ya resuelto:
        #   - Crudo / Suavizado: cambia el metodo de calculo de σ tanto en
        #     el contorno como en el probe.
        #   - Mostrar puntos Gauss: marca los PG en el canvas (snap del probe).
        #   - Vista 3D: abre Toplevel con plot_surface del resultado activo.
        # El probe se activa automaticamente al entrar al Post (sin toggle
        # master); hover -> tooltip transitorio, click -> pin, click derecho
        # -> panel Detalles + circulo de Mohr. Ver probe_overlay.py.
        probe_frame = ttk.Labelframe(
            container, text="Inspección del campo",
            bootstyle="success",
        )
        probe_frame.pack(fill=X, padx=10, pady=5)

        # Modo de calculo + boton 3D en la misma fila para ahorrar vertical.
        # Default "smooth": preserva la apariencia historica del Post
        # (contorno continuo). El alumno cambia a "raw" conscientemente
        # cuando quiere ver los saltos C0 del MEF.
        mode_row = ttk.Frame(probe_frame)
        mode_row.pack(fill=X, padx=15, pady=(8, 4))
        ttk.Label(
            mode_row, text="σ:",
            font=("Segoe UI", 8),
        ).pack(side=LEFT, padx=(0, 6))
        self.probe_smooth_var = tk.StringVar(value="smooth")
        ttk.Radiobutton(
            mode_row, text="Crudo", value="raw",
            variable=self.probe_smooth_var, bootstyle="success-toolbutton",
            command=self._on_probe_mode_changed,
        ).pack(side=LEFT, padx=2)
        ttk.Radiobutton(
            mode_row, text="Suavizado", value="smooth",
            variable=self.probe_smooth_var, bootstyle="success-toolbutton",
            command=self._on_probe_mode_changed,
        ).pack(side=LEFT, padx=2)
        # Separador + boton Vista 3D pegados a los radios (side=LEFT).
        # Distincion visual del par Crudo/Suavizado:
        #   - Radios: verde toolbutton (toggle agrupado, modo del campo)
        #   - Boton: azul sólido (accion separada, abre Toplevel)
        # Separador vertical refuerza que es un grupo distinto.
        # Layout estable al cambiar el ancho del panel: el espacio sobrante
        # queda a la derecha del boton, no entre radios y boton.
        ttk.Separator(mode_row, orient=VERTICAL).pack(
            side=LEFT, fill=Y, padx=8, pady=2,
        )
        ttk.Button(
            mode_row, text="🧊 Vista 3D",
            bootstyle="info",
            command=self._on_open_surface_3d,
        ).pack(side=LEFT, padx=(0, 0))

        # Toggle Gauss
        self.probe_show_gauss_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            probe_frame, text="Mostrar puntos Gauss",
            variable=self.probe_show_gauss_var, bootstyle="info-round-toggle",
            command=self._on_probe_gauss_toggled,
        ).pack(anchor=W, padx=15, pady=(0, 8))

        # Toggle Cruces principales σ1/σ2 (capa overlay sobre el canvas).
        # Una cruz por elemento en su centroide: σ1 azul (tracción) / σ2 rojo
        # (compresión). Consolida la funcionalidad del ex-módulo M8.
        self.principal_crosses_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            probe_frame, text="Cruces principales σ₁/σ₂",
            variable=self.principal_crosses_var, bootstyle="info-round-toggle",
            command=self._on_toggle_principal_crosses,
        ).pack(anchor=W, padx=15, pady=(0, 8))

    # ═════════════════════════════════════════════════════════════════════
    # SUB-TAB: RESULTADOS NUMERICOS
    # ═════════════════════════════════════════════════════════════════════

    def _build_results_tab(self):
        """Tabla de resultados numericos.

        Patron heredado del Pre: headers con unidades del project, anchos
        de columna generosos para el formato cientifico de los
        desplazamientos, seleccion de celda individual para copiar UN
        valor sin modificarlo (read-only) via Ctrl+C.
        """
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
        table_combo = ttk.Combobox(
            sel_frame, textvariable=self.table_type_var,
            values=["Desplazamientos", "Esfuerzos", "Reacciones"],
            state="readonly", width=18
        )
        table_combo.pack(side=LEFT, padx=5)
        # Auto-update al cambiar la selección. El bind a <<ComboboxSelected>>
        # reemplaza al botón "Actualizar" eliminado.
        table_combo.bind("<<ComboboxSelected>>",
                         lambda _e: self._update_table())

        table_frame = ttk.Frame(container)
        table_frame.pack(fill=BOTH, expand=YES, padx=10, pady=5)

        columns = ("node", "v1", "v2", "v3", "v4", "v5", "v6")
        self.results_tree = ttk.Treeview(
            table_frame, columns=columns, show="headings",
            bootstyle="danger", height=15, selectmode="extended",
        )
        # Headers iniciales (se sobreescriben en _update_table con unidades).
        self.results_tree.heading("node", text="Nodo", anchor=CENTER)
        for col in ("v1", "v2", "v3", "v4", "v5", "v6"):
            self.results_tree.heading(col, text="", anchor=CENTER)
        # Anchos: ID corto (55px) + valores anchos (115px) para alojar el
        # formato cientifico de desplazamientos (ej. "5.12345e-04" ≈ 11 chars).
        self.results_tree.column("node", width=55, anchor=CENTER, stretch=False)
        for col in ("v1", "v2", "v3", "v4", "v5", "v6"):
            self.results_tree.column(col, width=115, anchor=CENTER, stretch=False)

        # Scrollbar omitido: la rueda del mouse sobre Treeview es nativa en Tk.
        self.results_tree.pack(fill=BOTH, expand=YES, side=LEFT)

        # ─── Selección de celda individual (read-only copyable) ──────────
        # Treeview no soporta seleccion de celda nativa; emulamos:
        #   - Click sobre celda guarda (iid, col_id, value) en _selected_cell
        #   - Un tk.Label amarillo se posiciona via place() encima de la
        #     celda como feedback visual (la fila sigue azul-seleccionada
        #     por el comportamiento nativo de Treeview).
        #   - Ctrl+C copia SOLO ese valor cuando hay celda activa; sin
        #     celda activa, copia las filas seleccionadas en TSV.
        self._selected_cell = None  # (iid, col_name, value) o None
        # Overlay amarillo lazy: se crea al primer click. Reutiliza el
        # mismo color amarillo que `CANVAS_SELECTED_COLOR` del canvas para
        # consistencia cromatica con el resto de la GUI.
        self._cell_highlight = tk.Label(
            self.results_tree,
            bg=CANVAS_SELECTED_COLOR, fg="#000000",
            font=("Segoe UI", 9, "bold"),
            anchor=CENTER, borderwidth=0, padx=0, pady=0,
        )
        self._cell_highlight.place_forget()
        self.results_tree.bind("<Button-1>", self._on_results_cell_click,
                               add="+")
        # Si la fila/scroll cambia, esconder el highlight (la celda puede
        # haberse desplazado o ya no existir).
        self.results_tree.bind("<<TreeviewSelect>>",
                               self._on_results_selection_changed, add="+")

        # Atajos de copiado
        self.results_tree.bind("<Control-c>", self._copy_results_tsv)
        self.results_tree.bind("<Control-C>", self._copy_results_tsv)
        self.results_tree.bind("<Control-a>", self._select_all_results)
        self.results_tree.bind("<Control-A>", self._select_all_results)

    # ═════════════════════════════════════════════════════════════════════
    # AUTO-SOLVE (se llama al activar la pestana Post-Proceso)
    # ═════════════════════════════════════════════════════════════════════

    def auto_solve(self):
        """Resuelve automaticamente si hay modelo valido y no esta resuelto.

        Antes del solve, ejecuta `validate_project`:
          - errores criticos -> abre HealthReportDialog modal y bloquea
            hasta que el usuario los corrija o decida "resolver de todos
            modos"
          - warnings o modelo sano -> resuelve directo. Los warnings se
            reflejan en el badge ⚠ del status bar global, y el usuario
            puede clickearlo para abrir el HealthReportDialog en modo
            consulta.
        """
        # Si ya esta resuelto, solo actualizar display (no re-validar para
        # evitar abrir el modal en cada cambio de tab post-solve). Hace
        # falta repintar porque el cambio Pre/Proc -> Post pasa por
        # clear_results_overlay() que vacia el canvas; sin el _on_result_changed
        # aqui se ve la malla sin colores. Tambien reactivamos el probe si
        # el usuario lo dejo ON en una visita previa.
        if self.solution is not None and self.project.is_solved:
            self._on_result_changed()
            self._update_table()
            self.maybe_reactivate_probe_overlay()
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
                self.main_window.set_status(
                    f"✗ {len(report.errors)} error(es) sin resolver — "
                    f"corrija desde Pre-Proceso"
                )
                try:
                    self.main_window.notebook.select(0)
                    self.main_window.set_status(
                        "Corrija los errores antes de resolver"
                    )
                except Exception:
                    pass
                return

        # Chequeos de pre-requisitos minimos (redundantes con el
        # validador, pero el usuario puede haber clickeado "continuar
        # igual" en el modal -> respetar su decision aqui significa
        # intentar resolver y dejar que el solver tire una excepcion
        # explicita si no puede).
        if not self.project.elements:
            self.main_window.set_status(
                "Sin modelo — defina nodos y elementos"
            )
            return

        if not self.project.boundary_conditions:
            self.main_window.set_status(
                "Sin restricciones — defina condiciones de contorno"
            )
            return

        self.main_window.set_status("Resolviendo...")
        self.frame.update_idletasks()

        try:
            from fem.solver import solve_system
            from fem.stress import compute_all_stresses

            self.solution = solve_system(self.project)
            self.element_stresses, self.nodal_stresses = compute_all_stresses(
                self.project, self.solution
            )
            # Invalidar el cache de grillas crudas: nueva solución.
            self._raw_grid_cache = None

            self.project.is_solved = True
            self.project.displacements = self.solution["u"]
            self.project.global_K = self.solution["K"]
            self.project.global_F = self.solution["F"]
            self.project.stresses = self.element_stresses

            self.main_window.set_status(
                "✓ Resuelto — seleccione un resultado para visualizar"
            )
            self.main_window._update_status_info()
            # Refrescar estado del menú/toolbar (habilitar Exportar, etc.)
            if hasattr(self.main_window, "_refresh_menu_state"):
                self.main_window._refresh_menu_state()

            # Auto-visualizar Von Mises
            self._on_result_changed()
            self._update_table()

            # Activacion automatica de la consulta interactiva: el
            # overlay se prende solo (no requiere checkbox master). Si
            # re-solve y el overlay ya estaba activo, refresca refs a
            # la nueva solucion (pines existentes se re-evaluan).
            self.maybe_reactivate_probe_overlay()

        except Exception as e:
            self.main_window.set_status(f"✗ Error al resolver: {str(e)[:60]}")
            messagebox.showerror("Error al resolver", str(e))

    # ═════════════════════════════════════════════════════════════════════
    # CONSULTA INTERACTIVA (probe overlay)
    # ═════════════════════════════════════════════════════════════════════

    def _ensure_probe_overlay(self):
        """Instancia el ProbeOverlay la primera vez que se necesita.

        Lazy-load para evitar import cycle al inicializar post_tab antes
        que el MeshCanvas (las pestañas se construyen antes del canvas).
        """
        if self.probe_overlay is None:
            from gui.postprocessing.probe_overlay import ProbeOverlay
            self.probe_overlay = ProbeOverlay(
                self.main_window.mesh_canvas, self, self.main_window,
            )
        # Mantener la referencia al project actualizada (si cambio via
        # New / Open / undo, el listener `_update_all_project_refs` lo
        # propaga; aqui solo aseguramos coherencia local).
        self.probe_overlay.project = self.project
        # Sincronizar modos actuales antes de activar (en caso de que el
        # usuario haya tocado los toggles antes del primer auto_solve).
        self.probe_overlay.smooth_mode = (
            self.probe_smooth_var.get() == "smooth"
        )
        self.probe_overlay.show_gauss = self.probe_show_gauss_var.get()

    def _on_probe_mode_changed(self):
        """Switch crudo <-> suavizado.

        Afecta DOS cosas:
          1) Probes pinneadas y tooltip del hover (recompute via probe_overlay).
          2) Contorno global del Post: en modo crudo se dibujan los esfuerzos
             discontinuos entre elementos (per-element-per-node); en suavizado
             el contorno usa los valores nodales promediados (clasico).
        """
        smooth = (self.probe_smooth_var.get() == "smooth")
        if self.probe_overlay is not None:
            self.probe_overlay.set_smooth_mode(smooth)
        # Refrescar contorno con el nuevo modo
        self._on_result_changed()

    def _on_probe_gauss_toggled(self):
        # El toggle puede pulsarse antes del primer auto_solve. En ese
        # caso solo recordamos el valor; al activar el overlay se aplica.
        if self.probe_overlay is not None:
            self.probe_overlay.set_show_gauss(self.probe_show_gauss_var.get())

    def deactivate_probe_overlay(self):
        """Llamado desde MainWindow._on_tab_changed al salir de Post.

        Apaga el modo. La consulta interactiva NO requiere toggle manual:
        al volver a Post se reactiva automaticamente via
        maybe_reactivate_probe_overlay.
        """
        if self.probe_overlay is not None and self.probe_overlay.active:
            self.probe_overlay.deactivate()

    def maybe_reactivate_probe_overlay(self):
        """Llamado tras auto_solve exitoso cuando se entra (o vuelve) a Post.

        Activacion automatica: si hay solucion valida, el overlay se
        prende. Sin checkbox master -- la consulta es siempre-on en Post.
        """
        if not self.solution:
            return
        self._ensure_probe_overlay()
        self.probe_overlay.activate(
            self.solution, self.element_stresses, self.nodal_stresses,
        )
        # Refrescar refs de las vistas avanzadas si estan abiertas
        # (cambio de project / re-solve sin perder estado UI).
        if self.surface_3d_viewer is not None:
            try:
                self.surface_3d_viewer.update_solution(
                    self.solution, self.nodal_stresses,
                )
            except Exception:
                pass
        # Refrescar la capa de cruces principales si esta activa (re-solve).
        if (self.principal_cross_layer is not None
                and self.principal_cross_layer.is_active()):
            try:
                self.principal_cross_layer.update_data(
                    self.project, self.nodal_stresses,
                )
            except Exception:
                pass

    # ═════════════════════════════════════════════════════════════════════
    # VISUALIZACION AVANZADA (Vista 3D)
    # ═════════════════════════════════════════════════════════════════════

    def _on_open_surface_3d(self):
        """Abre (o levanta) la Vista 3D del campo activo en el Post.

        El Toplevel es no-modal: el usuario sigue interactuando con la
        toolbar del post (cambiar de result_type, modo crudo/suavizado)
        y el 3D actualiza automaticamente.
        """
        if not self.solution or not self.nodal_stresses:
            self.main_window.set_status(
                "Resolvé el modelo (F5) antes de abrir la vista 3D"
            )
            return
        # Si ya esta abierto, traer al frente.
        if (self.surface_3d_viewer is not None
                and self.surface_3d_viewer.winfo_exists()):
            try:
                self.surface_3d_viewer.lift()
                self.surface_3d_viewer.focus_force()
                self.surface_3d_viewer.refresh()
            except Exception:
                pass
            return
        from gui.postprocessing.surface_3d_viewer import Surface3DViewer
        self.surface_3d_viewer = Surface3DViewer(
            self.frame.winfo_toplevel(),
            self.project, self.solution, self.nodal_stresses,
            self, self.main_window,
        )

    def _on_toggle_principal_crosses(self):
        """Activa/desactiva la capa de cruces principales σ1/σ2 sobre el
        canvas. La capa solo dibuja (no intercepta eventos), asi que coexiste
        con el probe overlay sin conflicto."""
        want = self.principal_crosses_var.get()
        if want:
            if not self.solution or not self.nodal_stresses:
                # Sin solucion: revertir el toggle y avisar.
                self.principal_crosses_var.set(False)
                self.main_window.set_status(
                    "Resolvé el modelo (F5) antes de mostrar las cruces principales"
                )
                return
            if self.principal_cross_layer is None:
                from gui.postprocessing.principal_cross_layer import (
                    PrincipalCrossLayer,
                )
                self.principal_cross_layer = PrincipalCrossLayer(
                    self.main_window.mesh_canvas, self.project,
                    self.nodal_stresses,
                )
            else:
                self.principal_cross_layer.update_data(
                    self.project, self.nodal_stresses,
                )
            self.principal_cross_layer.activate()
        else:
            if self.principal_cross_layer is not None:
                self.principal_cross_layer.deactivate()

    def deactivate_advanced_views(self):
        """Llamado desde MainWindow._on_tab_changed al salir de Post.

        Cierra el Toplevel 3D y desactiva la capa de cruces principales. La
        consulta del probe se gestiona aparte via `deactivate_probe_overlay`.
        """
        if (self.surface_3d_viewer is not None
                and self.surface_3d_viewer.winfo_exists()):
            try:
                self.surface_3d_viewer.destroy()
            except Exception:
                pass
            self.surface_3d_viewer = None

        # Capa de cruces principales: desactivar y resetear el toggle.
        if self.principal_cross_layer is not None:
            try:
                self.principal_cross_layer.deactivate()
            except Exception:
                pass
        try:
            self.principal_crosses_var.set(False)
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════
    # VISUALIZACION REACTIVA (auto-update al cambiar radio buttons)
    # ═════════════════════════════════════════════════════════════════════

    def _on_result_changed(self):
        """Callback: actualiza visualizacion al cambiar cualquier opcion.

        Dos rutas segun el modo de calculo de esfuerzos:
          - SUAVIZADO (default): valores nodales promediados -> contorno
            continuo entre elementos (convencion clasica).
          - CRUDO: valores per-element-per-node via compute_raw evaluado
            en los 4 corners -> el contorno muestra saltos en bordes,
            que es la naturaleza C0 del MEF Galerkin.

        El modo se controla con probe_smooth_var ("raw" o "smooth").
        Para Ux/Uy/|U| no hay diferencia (los desplazamientos son C0
        continuos) -- ambas rutas terminan en set_result_values.
        """
        if not self.solution:
            return

        result_type = self.result_var.get()
        u = self.solution["u"]
        canvas = self.main_window.mesh_canvas

        labels = {
            "Ux": "Ux", "Uy": "Uy", "Umag": "|U|",
            "Sx": "σx", "Sy": "σy", "Txy": "τxy",
            "S1": "σ1", "S2": "σ2", "VM": "Von Mises",
        }
        label = labels.get(result_type, result_type)
        is_stress = result_type in ("Sx", "Sy", "Txy", "S1", "S2", "VM")
        raw_mode = (
            hasattr(self, "probe_smooth_var")
            and self.probe_smooth_var.get() == "raw"
        )

        # Configurar isolineas y deformada antes (no dependen del modo).
        canvas.set_isolines(
            self.show_isolines_var.get(),
            self.isoline_count_var.get()
        )
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
                canvas.deform_scale = (
                    model_size * 0.1 / max_disp * self.scale_var.get()
                )
            canvas.show_deformed = True
        else:
            canvas.show_deformed = False
            canvas.displacements = None

        # ─ Ruta CRUDO (per-element pre-computada) para esfuerzos ─────────
        # Usa compute_raw_grid: evalua D·B(ξ,η)·u_e en una grilla 7x7 por
        # elemento. Para invariantes (VM, σ1, σ2) calcula los componentes
        # y compone el invariante POR PUNTO -- crucial: interpolar el
        # invariante entre corners da error 50-800% (Von Mises no lineal).
        if is_stress and raw_mode and self.element_stresses:
            element_grids = self._compute_raw_grid(result_type, n=6)
            if element_grids:
                canvas.set_element_result_grid(element_grids, label)
                self.main_window.set_status(
                    f"Visualizando: {label} (crudo, D·B·uₑ por punto)"
                )
                return
            # Si compute_raw_grid fallo (datos faltantes), caer a suavizado.

        # ─ Ruta SUAVIZADO (nodal promediado) ─────────────────────────────
        idx_map = self.project.node_index_map
        node_values = {}
        for nid in sorted(self.project.nodes.keys()):
            base = 2 * idx_map[nid]
            ux = u[base]
            uy = u[base + 1]
            if result_type == "Ux":
                node_values[nid] = ux
            elif result_type == "Uy":
                node_values[nid] = uy
            elif result_type == "Umag":
                node_values[nid] = np.sqrt(ux**2 + uy**2)
            elif is_stress:
                stress_key = {
                    "Sx": "sigma_x", "Sy": "sigma_y", "Txy": "tau_xy",
                    "S1": "sigma_1", "S2": "sigma_2", "VM": "von_mises"
                }[result_type]
                if self.nodal_stresses and nid in self.nodal_stresses:
                    node_values[nid] = self.nodal_stresses[nid][stress_key]
                else:
                    node_values[nid] = 0.0

        canvas.set_result_values(node_values, label)
        suffix = (
            " (suavizado, Σ Nᵢ·σᵢ̄)" if (is_stress and not raw_mode) else ""
        )
        self.main_window.set_status(f"Visualizando: {label}{suffix}")

        # Sincronizar Surface3DViewer si esta abierto. Cambiar VM↔σx en el
        # post repinta el 3D automaticamente -- el usuario no pierde
        # contexto. Refresh tardio (despues de set_result_values) para que
        # el 3D y el contorno 2D queden coherentes.
        if (self.surface_3d_viewer is not None
                and self.surface_3d_viewer.winfo_exists()):
            try:
                self.surface_3d_viewer.refresh()
            except Exception:
                pass

    def _get_raw_grids(self, n=6):
        """Devuelve {elem_id: all_grids_dict} con TODOS los campos crudos
        (σx/σy/τxy/σ1/σ2/VM) evaluados en la grilla (n+1, n+1) de cada
        elemento, cacheado tras el solve. Recomputar D·B·uₑ en cada cambio
        de resultado era el costo dominante; el cache lo hace una sola vez.

        Retorna {} (cacheado) si algun elemento no se pudo evaluar — el
        caller cae a suavizado.
        """
        if self._raw_grid_cache is not None:
            return self._raw_grid_cache
        from fem.probe_query import compute_raw_grid
        cache = {}
        for elem_id in self.project.elements:
            all_grids = compute_raw_grid(self.project, self.solution,
                                          elem_id, n=n)
            if all_grids is None:
                self._raw_grid_cache = {}  # marca: crudo no disponible
                return self._raw_grid_cache
            cache[elem_id] = all_grids
        self._raw_grid_cache = cache
        return cache

    def _compute_raw_grid(self, result_type, n=6):
        """Pre-computa la grilla (n+1, n+1) del campo de esfuerzo seleccionado
        en cada elemento, extrayendolo del cache crudo (`_get_raw_grids`).

        Returna {elem_id: ndarray(n+1, n+1)} con valores del campo `result_type`
        evaluados via D·B(ξ,η)·u_e en cada (ξ_i, η_j) ∈ [-1,1]².

        Para invariantes (VM, σ1, σ2) los valores ya estan calculados con
        los componentes σx/σy/τxy correctos POR PUNTO (no interpolando el
        invariante entre corners, que da error grosero por la no-linealidad).
        """
        stress_key = {
            "Sx": "sigma_x", "Sy": "sigma_y", "Txy": "tau_xy",
            "S1": "sigma_1", "S2": "sigma_2", "VM": "von_mises",
        }.get(result_type)
        if stress_key is None:
            return None

        grids = self._get_raw_grids(n=n)
        if not grids:
            return None
        return {eid: g[stress_key] for eid, g in grids.items()}

    # ═════════════════════════════════════════════════════════════════════
    # TABLA DE RESULTADOS
    # ═════════════════════════════════════════════════════════════════════

    def _get_units(self):
        """Espejo de pre_tab._get_units: devuelve {longitud, fuerza, esfuerzo}
        del proyecto."""
        from config.units import get_unit_labels
        return get_unit_labels(self.project.unit_system)

    def _update_table(self):
        self.results_tree.delete(*self.results_tree.get_children())
        # Limpiar celda seleccionada (y su overlay) al reconstruir contenido
        self._clear_cell_highlight()
        if not self.solution:
            return

        u_labels = self._get_units()
        L = u_labels.get("longitud", "-")
        F = u_labels.get("fuerza", "-")
        S = u_labels.get("esfuerzo", "-")

        table_type = self.table_type_var.get()
        u = self.solution["u"]

        if table_type == "Desplazamientos":
            self.results_tree.heading("v1", text=f"Ux [{L}]")
            self.results_tree.heading("v2", text=f"Uy [{L}]")
            self.results_tree.heading("v3", text=f"|U| [{L}]")
            self.results_tree.heading("v4", text="")
            self.results_tree.heading("v5", text="")
            self.results_tree.heading("v6", text="")
            idx_map = self.project.node_index_map
            for nid in sorted(self.project.nodes.keys()):
                base = 2 * idx_map[nid]
                ux = u[base]
                uy = u[base + 1]
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
            self.results_tree.heading("v1", text=f"σx [{S}]")
            self.results_tree.heading("v2", text=f"σy [{S}]")
            self.results_tree.heading("v3", text=f"τxy [{S}]")
            self.results_tree.heading("v4", text=f"σ1 [{S}]")
            self.results_tree.heading("v5", text=f"σ2 [{S}]")
            self.results_tree.heading("v6", text=f"VM [{S}]")
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
            self.results_tree.heading("v1", text=f"Rx [{F}]")
            self.results_tree.heading("v2", text=f"Ry [{F}]")
            self.results_tree.heading("v3", text="")
            self.results_tree.heading("v4", text="")
            self.results_tree.heading("v5", text="")
            self.results_tree.heading("v6", text="")
            R = self.solution["reactions"]
            idx_map = self.project.node_index_map
            for bc in sorted(self.project.boundary_conditions.values(),
                             key=lambda b: b.node_id):
                nid = bc.node_id
                base = 2 * idx_map[nid]
                rx = R[base] if bc.restrain_x else 0
                ry = R[base + 1] if bc.restrain_y else 0
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

    def _on_results_cell_click(self, event):
        """Detecta click sobre una celda y la marca como 'celda seleccionada'.

        Pinta un Label amarillo con el valor encima de la celda (feedback
        visual) y guarda `(iid, col_name, value)` en `self._selected_cell`
        para que `Ctrl+C` posterior copie solo ese valor (read-only — la
        celda no se edita).
        """
        region = self.results_tree.identify("region", event.x, event.y)
        if region != "cell":
            self._clear_cell_highlight()
            return
        iid = self.results_tree.identify_row(event.y)
        col_id = self.results_tree.identify_column(event.x)  # "#1", "#2", ...
        if not iid or not col_id:
            self._clear_cell_highlight()
            return
        try:
            col_idx = int(col_id.replace("#", "")) - 1
        except ValueError:
            self._clear_cell_highlight()
            return
        cols = self.results_tree["columns"]
        if not (0 <= col_idx < len(cols)):
            self._clear_cell_highlight()
            return
        col_name = cols[col_idx]
        header = self.results_tree.heading(col_name, "text") or col_name
        values = self.results_tree.item(iid, "values")
        value = values[col_idx] if col_idx < len(values) else ""
        if value == "":
            self._clear_cell_highlight()
            self.main_window.set_status(
                "Celda vacia — sin valor para copiar"
            )
            return
        self._selected_cell = (iid, col_name, value)
        self._show_cell_highlight(iid, col_id, value)
        self.main_window.set_status(
            f"Celda: {header} = {value}  (Ctrl+C para copiar)"
        )

    def _show_cell_highlight(self, iid, col_id, value):
        """Posiciona el Label overlay amarillo encima de la celda.

        Usa `Treeview.bbox(iid, col)` para obtener coords relativas al
        Treeview y `place()` para posicionar. El text del label espeja el
        valor de la celda para que el highlight no oculte el dato.
        """
        bbox = self.results_tree.bbox(iid, col_id)
        if not bbox:
            self._clear_cell_highlight()
            return
        x, y, w, h = bbox
        try:
            self._cell_highlight.config(text=str(value))
            self._cell_highlight.place(x=x, y=y, width=w, height=h)
            self._cell_highlight.lift()
        except tk.TclError:
            pass

    def _clear_cell_highlight(self):
        """Oculta el overlay y limpia _selected_cell."""
        self._selected_cell = None
        try:
            self._cell_highlight.place_forget()
        except (tk.TclError, AttributeError):
            pass

    def _on_results_selection_changed(self, _event=None):
        """Si el usuario cambia la fila seleccionada por teclado o
        Ctrl+Click, la celda anterior puede ya no ser la activa: limpiamos
        el highlight para evitar feedback estale."""
        if self._selected_cell is None:
            return
        # Si la fila del highlight sigue seleccionada (caso multi-fila),
        # mantener; sino limpiar.
        sel = self.results_tree.selection()
        iid = self._selected_cell[0]
        if iid not in sel:
            self._clear_cell_highlight()

    def _copy_results_tsv(self, event=None):
        """Ctrl+C en la tabla de resultados.

        Prioridad:
          1) Si hay una celda seleccionada via click -> copia SOLO ese
             valor (sin tabuladores ni headers).
          2) Sino, copia las filas seleccionadas en TSV (o todas si no hay
             seleccion). Pegable en Excel con headers de la vista activa.
        """
        # Caso 1: celda individual seleccionada
        if self._selected_cell is not None:
            _, _, value = self._selected_cell
            self.frame.clipboard_clear()
            self.frame.clipboard_append(str(value))
            self.main_window.set_status(
                f"Copiado al portapapeles: {value}"
            )
            return "break"

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
            self.element_stresses = None
            self._raw_grid_cache = None
            # Limpieza silenciosa del probe overlay: si la geometria
            # cambio (lo que invalida is_solved), la probe referenciaria
            # elem_ids que pueden ya no existir. Decision documentada en
            # CLAUDE.md. El overlay se reactiva automaticamente cuando
            # se vuelva a Post-Proceso con un solve exitoso.
            if (self.probe_overlay is not None
                    and self.probe_overlay.active):
                self.probe_overlay.deactivate()
            # Vista 3D queda ligada a is_solved: si la geometria cambia,
            # se cierra silenciosamente.
            if (self.surface_3d_viewer is not None
                    and self.surface_3d_viewer.winfo_exists()):
                try:
                    self.surface_3d_viewer.destroy()
                except Exception:
                    pass
                self.surface_3d_viewer = None
            # Cruces principales: misma logica -- la geometria cambio, los
            # esfuerzos ya no son validos. Desactivar capa + resetear toggle.
            if self.principal_cross_layer is not None:
                try:
                    self.principal_cross_layer.deactivate()
                except Exception:
                    pass
            try:
                self.principal_crosses_var.set(False)
            except Exception:
                pass
