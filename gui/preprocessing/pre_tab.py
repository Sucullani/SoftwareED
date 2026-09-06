"""
PreProcessTab: Panel izquierdo de Pre-Proceso.

Tablas tipo spreadsheet para Nodos, Elementos, Cargas, Restricciones y
Cargas Superficiales. El canvas de malla es compartido en main_window.

Caracteristicas:
- Tipografia coherente con `config.settings` (Segoe UI / Consolas).
- Edicion in-place con Entry/Combobox de alto contraste (helpers).
- Edicion de IDs con renombrado en cascada (`project.change_node_id`,
  `change_element_id`).
- Encabezados con la unidad activa del proyecto.
- Fila placeholder atenuada al final: doble-click crea registro pendiente
  que el usuario debe completar antes de cambiar de fila/pestana.
- Copy/Paste TSV compatible con Excel (Ctrl+C / Ctrl+V).
- Fill-down (Ctrl+D) tipo Excel.
- Navegacion teclado en editor: Tab/Shift-Tab/Enter/flechas.
- Sync bidireccional spreadsheet -> canvas para todas las tablas
  (nodos, elementos, cargas, restricciones, cargas superficiales).
- Menu contextual con acciones de dominio (Insertar, Duplicar, Centrar
  en canvas, Eliminar). Sin Copiar/Pegar (atajos cubren ese caso).
- Restricciones con glyph Unicode "checkbox" en celda (toggle por click).
- Materiales en Elementos via Combobox readonly en Toplevel overlay.
"""

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from config.settings import (
    FONT_UI_LARGE, FONT_UI_BOLD, TREE_ROW_HEIGHT,
    DECIMALS_LENGTH, DECIMALS_FORCE, DECIMALS_ANGLE, fmt,
    PHASE_PRE_COLOR, PHASE_PRE_BOOTSTYLE,
    ELEMENT_Q9,
    ORPHAN_NODE_FG, ORPHAN_NODE_BG,
    PICK_GHOST_FG, PICK_GHOST_BG,
    CANVAS_SELECTED_ROW_BG, CANVAS_SELECTED_ROW_FG,
    TREE_ROW_BG_COLOR, TREE_PLACEHOLDER_BG, TREE_PLACEHOLDER_FG,
    AUTO_NODE_FG,
)
from config.units import get_unit_labels
from gui.preprocessing._table_helpers import (
    start_cell_editor, start_combobox_editor,
    bind_clipboard, to_float_flex,
)
from gui.widgets.tooltip import ToolTip
from gui.dialogs.material_dialog import MaterialDialog
from gui.widgets.phase_banner import build_phase_banner
from gui.widgets.module_launcher_panel import render_module_buttons
from models.mesh_utils import (
    auto_expand_if_q9, classify_nodes, classify_orphan_status,
    expand_q4_to_q9, recompute_q9_midnodes,
)


PLACEHOLDER_IID = "__new__"
PLACEHOLDER_HINT = "+ doble-click para anadir"
GLYPH_ON = "\u2611"   # ☑
GLYPH_OFF = "\u2610"  # ☐
GLYPH_DROPDOWN = " \u25be"  # ▾  indicador visual de combobox en celda

# Fondo plano uniforme para todos los Treeview. El zebra striping fue
# retirado: con `canvas_selected` (amarillo), `orphan_node` (naranja),
# `pending_pick` (azul) y `placeholder` (gris) ya hay 4 estados
# semanticos; el zebra agregaba ruido cromatico que competia con ellos.
ROW_BG = TREE_ROW_BG_COLOR
PLACEHOLDER_BG = TREE_PLACEHOLDER_BG
PLACEHOLDER_FG = TREE_PLACEHOLDER_FG
TREE_FIELD_BG = TREE_ROW_BG_COLOR


def _parse_bool(text):
    """Parsea representaciones comunes de booleano en strings."""
    s = (text or "").strip().lower()
    return s in (GLYPH_ON, "si", "sí", "true", "yes", "y", "1", "x", "verdadero")


class PreProcessTab:
    """Panel de Pre-Proceso con tablas de datos (sin canvas propio)."""

    def __init__(self, parent, project, main_window):
        self.project = project
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        # Flags de loop-guard para sincronizacion bidireccional
        # canvas <-> spreadsheet. Cuando uno actualiza al otro, el otro
        # NO debe rebotar el cambio (sino se generaria un ping-pong
        # infinito de eventos <<TreeviewSelect>> y on_selection_changed).
        self._syncing_from_canvas = False
        self._syncing_to_canvas = False
        # Snapshot de la seleccion anterior del canvas (camino canvas→spreadsheet).
        # Si la nueva seleccion es identica, saltamos el rebuild de los 5 trees.
        self._last_canvas_sel = None

        # Registro pendiente de completar (ver _set_pending).
        self._pending_new = None
        self._suppress_pending_check = False  # reentrancia interna

        # ─── Orden visual unificado para tablas con filas fantasma ──────
        # Lista de tuplas que mezclan filas reales y fantasmas en el orden
        # exacto en que deben renderizarse. Permite que cuando una fantasma
        # se commitea, la nueva fila real ocupe el slot de la fantasma sin
        # jump visual — el ghost commit muta una entry ('ghost', X) ->
        # ('real', X) sin cambiar su posicion.
        # Las entries se filtran/sincronizan en _build_*_visual_list:
        #   - quita reales borradas, ghosts ya no seleccionadas, dups.
        #   - appendea reales nuevas (load creado fuera de ghost) y ghosts
        #     nuevas (selected_nodes crecio en canvas) al final.
        self._loads_visual_order = []         # [('real'|'ghost', node_id), ...]
        self._constraints_visual_order = []   # idem
        self._surfaces_visual_order = []      # [('real', SurfaceLoad obj) | ('ghost', frozenset({n1,n2})), ...]

        self._build_panel()

    # ═════════════════════════════════════════════════════════════════════
    # CONSTRUCCION DEL PANEL
    # ═════════════════════════════════════════════════════════════════════

    def _apply_global_tree_style(self):
        """Configura fuente, altura de fila y bordes para todos los Treeview.

        Centrado vertical: el cell renderer interno de ttk.Treeview centra
        usando ascent/descent dentro de rowheight, PERO si rowheight es
        mucho mayor que el linespace + descent, el texto queda visualmente
        anclado arriba. La solucion es row tight (linespace + ~4px) + layout
        explicito de Treeitem que fuerza sticky="" (centro) en lugar de "w".
        """
        import tkinter.font as tkfont

        style = ttk.Style()

        body_font = tkfont.Font(family=FONT_UI_LARGE[0], size=FONT_UI_LARGE[1])
        body_linespace = body_font.metrics("linespace")
        # Tight rowheight: poco padding extra forza centrado visual perfecto
        row_h = body_linespace + 6   # 3px arriba + 3px abajo

        head_font = tkfont.Font(family=FONT_UI_BOLD[0], size=FONT_UI_BOLD[1])
        head_linespace = head_font.metrics("linespace")
        # Heading con misma "razon de centrado" que el body
        head_pad = (8, 4)

        # Forzar layout que centra el contenido del item (sticky vacio = centro)
        try:
            style.layout("Treeview.Item", [
                ("Treeitem.padding", {
                    "sticky": "nswe",
                    "children": [
                        ("Treeitem.indicator", {"side": "left", "sticky": ""}),
                        ("Treeitem.image",     {"side": "left", "sticky": ""}),
                        ("Treeitem.focus",     {"side": "left", "sticky": "",
                                                "children": [
                            ("Treeitem.text", {"side": "left", "sticky": ""}),
                        ]}),
                    ],
                }),
            ])
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            font=FONT_UI_LARGE,
            rowheight=row_h,
            background=ROW_BG,
            fieldbackground=TREE_FIELD_BG,
            borderwidth=0,
            relief="flat",
            padding=0,
        )
        style.configure(
            "Treeview.Heading",
            font=FONT_UI_BOLD,
            relief="raised",       # linea visible entre columnas
            borderwidth=1,
            padding=head_pad,
            anchor="center",
        )
        # Seleccion nativa de ttk (click directo en fila): NO overrideamos
        # `style.map` para el state "selected". El tema darkly ya pinta gris
        # `#555555` para selected, que es exactamente el mismo hex de
        # `CANVAS_SELECTED_ROW_BG`. El highlight resulta visualmente identico
        # venga del canvas (via tag `canvas_selected`) o del click directo
        # (via state nativo del tema). Pelear con `style.map` desde fuera
        # del tema era fragil — el theme reaplica sus mappings en widget
        # creation y pisaba nuestros overrides. Solucion: alinear nuestros
        # constantes a los del tema en lugar de luchar contra ellos.

    def _configure_row_tags(self, tree):
        """Tags semanticos de fila para todos los Treeview.

        Prioridad de tags en ttk.Treeview = orden de `tag_configure`,
        primero-configurado gana (NO la posicion en la tupla del item).
        Por eso `canvas_selected` se configura PRIMERO: su background
        amarillo gana sobre `orphan_node`/`pending_pick`/`placeholder`.
        Define background Y foreground (negro) para asegurar legibilidad
        sobre el amarillo brillante; al estar seleccionada la fila, el
        estado naranja-huerfano o gris-auto queda en segundo plano (la
        seleccion gana, que es el comportamiento esperado).
        """
        # Highlight de seleccion desde canvas (PRIMERO -> mayor prioridad
        # de bg/fg). NO usa `tree.selection_set` (virtualevent async causaba
        # congelamiento -- ver CLAUDE.md "Sync asimetrico").
        tree.tag_configure("canvas_selected",
                           background=CANVAS_SELECTED_ROW_BG,
                           foreground=CANVAS_SELECTED_ROW_FG)
        tree.tag_configure("placeholder",
                           foreground=PLACEHOLDER_FG,
                           background=PLACEHOLDER_BG)
        # Mid/center de Q9: read-only, se recalculan al mover los vertices.
        tree.tag_configure("auto_node", foreground=AUTO_NODE_FG)
        # Nodo huerfano preservado (sin elemento, con cargas/BCs/surface refs):
        # naranja desaturado (warning) + fondo oscuro tintado, para que la
        # fila completa sea distinguible del gris tenue de auto_node (Q9
        # mid/center bloqueados, que es un estado totalmente distinto).
        tree.tag_configure("orphan_node",
                           foreground=ORPHAN_NODE_FG,
                           background=ORPHAN_NODE_BG)
        # Fila fantasma de pick desde canvas. Single-click sobre la fila
        # ghost confirma la sugerencia (crea el item con defaults, el
        # usuario edita despues). El color azul la diferencia del
        # placeholder gris y del huerfano naranja.
        tree.tag_configure("pending_pick",
                           foreground=PICK_GHOST_FG,
                           background=PICK_GHOST_BG)

    def _build_panel(self):
        self._apply_global_tree_style()

        # Banner colorido de la fase (identidad visual)
        build_phase_banner(
            self.frame,
            color=PHASE_PRE_COLOR,
            icon="📐",
            title="PRE-PROCESO",
            subtitle="Geometria · cargas · restricciones · materiales",
        )

        self.data_notebook = ttk.Notebook(self.frame, bootstyle=PHASE_PRE_BOOTSTYLE)
        self.data_notebook.pack(fill=BOTH, expand=YES, padx=2, pady=2)
        self.data_notebook.bind("<<NotebookTabChanged>>",
                                self._on_subtab_changed)

        # Hook al notebook principal para chequear pending al cambiar de
        # PRE-PROCESO a PROCESO/POST-PROCESO. Es un binding adicional;
        # convive con _on_tab_changed de MainWindow.
        if getattr(self.main_window, "notebook", None) is not None:
            self.main_window.notebook.bind(
                "<<NotebookTabChanged>>",
                lambda e: self._check_pending_completion(),
                add="+",
            )

        self.nodes_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.nodes_frame, text="  Nodos  ")
        self._build_nodes_panel()

        self.elements_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.elements_frame, text="  Elementos  ")
        self._build_elements_panel()

        self.loads_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.loads_frame, text="  Cargas  ")
        self._build_loads_panel()

        self.constraints_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.constraints_frame, text="  Restricciones  ")
        self._build_constraints_panel()

        self.surface_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.surface_frame, text="  Carg. Superf.  ")
        self._build_surface_loads_panel()

        # Sub-pestana de modulos educativos de pre-proceso (M0 calidad de malla)
        self.education_frame = ttk.Frame(self.data_notebook)
        self.data_notebook.add(self.education_frame, text="  🎓 Educacion  ")
        self._build_education_panel()

        # Cablear callbacks bidireccionales: click en canvas selecciona
        # la fila correspondiente del spreadsheet y cambia a la sub-pestana.
        self._wire_canvas_callbacks()

        # Inicializar headers con la unidad activa y poblar tablas
        self.update_unit_headers()
        self.refresh()

    def _wire_canvas_callbacks(self):
        """Registra los handlers reactivos en el MeshCanvas compartido.

        El canvas notifica al pre_tab ante borrados, cambios del modo dibujo
        y cambios de seleccion para mantener sincronizadas las tablas.
        """
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None:
            return

        def _on_canvas_delete(kind, _target_id):
            """Tras un borrado iniciado desde el canvas (Supr/BackSpace),
            refresca todas las tablas afectadas y ejecuta el safety net Q9
            si aplica. Item-agnostico: por simplicidad refresca todo, el
            costo es bajo y evita acoplar `kind` a tablas especificas."""
            self._refresh_all_trees()
            self._update_status_info()
            # En proyecto Q9, eliminar elementos puede dejar mid/center
            # huerfanos -- los marcamos en gris pero el safety net no los
            # re-expande (porque no son Q4 ahora). Llamada idempotente.
            self._ensure_q9_consistency(silent=True)
        canvas.on_canvas_delete = _on_canvas_delete

        # Modo dibujo: el canvas notifica al pre_tab cuando el modo se
        # activa/desactiva (para sincronizar el bootstyle del boton) y
        # cuando se completa un elemento (para refrescar tablas).
        canvas.on_draw_mode_changed = self._on_canvas_draw_mode_changed
        canvas.on_draw_element_created = self._on_canvas_draw_element_created

        # Cambio de seleccion en canvas: reconstruye filas fantasma en
        # las sub-pestañas relevantes (Cargas, Restricciones, Surface).
        canvas.on_selection_changed = self._on_canvas_selection_changed

    def _build_education_panel(self):
        """Sub-pestana con modulos educativos asociados al PRE-PROCESO."""
        from education.module_launcher import (
            list_modules_for_phase, open_module, GLOBAL_MODULES,
        )

        def _on_open(mod_key):
            ok = open_module(
                parent_tk=self.frame.winfo_toplevel(),
                project=self.project,
                mod_key=mod_key,
                mesh_canvas=getattr(self.main_window, "mesh_canvas", None),
            )
            if ok:
                self.main_window.set_status(f"Modulo educativo abierto: {mod_key}")
            return ok  # el panel marca ✓ solo si realmente abrio

        self._edu_panel = render_module_buttons(
            self.education_frame,
            modules=list_modules_for_phase("pre"),
            on_open=_on_open,
            bootstyle=f"{PHASE_PRE_BOOTSTYLE}-outline",
            header_text="Modulos Educativos · Pre-Proceso",
            header_color=PHASE_PRE_COLOR,
            subtitle=("Conceptos relacionados con la preparacion del modelo:\n"
                      "calidad geometrica de la malla, tipos de elemento."),
            global_modules=GLOBAL_MODULES,
        )

    def wire_canvas(self):
        """Inicializa el panel de modulos con la seleccion actual del canvas.

        El callback `on_selection_changed` del canvas ya esta cableado a
        `_on_canvas_selection_changed` por `_wire_canvas_callbacks` — ese
        handler tambien refresca el panel educativo. Aqui solo establecemos
        el estado inicial coherente."""
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None or getattr(self, "_edu_panel", None) is None:
            return
        try:
            sel = canvas.get_selection()
            elems = sel.get("elements", set())
            elem_id = next(iter(elems)) if len(elems) == 1 else None
            self._edu_panel.update_selection(elem_id)
        except Exception:
            pass

    # ─── Helpers de unidades ────────────────────────────────────────────

    def _get_units(self):
        return get_unit_labels(self.project.unit_system)

    def update_unit_headers(self):
        """Refresca los textos de columna con la unidad activa del proyecto."""
        u = self._get_units()
        L = u.get("longitud", "-")
        F = u.get("fuerza", "-")
        self.nodes_tree.heading("x", text=f"X [{L}]", anchor=CENTER)
        self.nodes_tree.heading("y", text=f"Y [{L}]", anchor=CENTER)
        self.elements_tree.heading("espesor", text=f"Espesor [{L}]", anchor=CENTER)
        self.loads_tree.heading("fx", text=f"Fx [{F}]", anchor=CENTER)
        self.loads_tree.heading("fy", text=f"Fy [{F}]", anchor=CENTER)
        self.surface_tree.heading("q_start", text=f"q Inicio [{F}/{L}]", anchor=CENTER)
        self.surface_tree.heading("q_end", text=f"q Final [{F}/{L}]", anchor=CENTER)
        self.surface_tree.heading("angle", text="Angulo [\u00b0]", anchor=CENTER)

    # ═════════════════════════════════════════════════════════════════════
    # PANELES
    # ═════════════════════════════════════════════════════════════════════

    # ─── Nodos ──────────────────────────────────────────────────────────

    def _build_nodes_panel(self):
        columns = ("id", "x", "y")
        self.nodes_tree = ttk.Treeview(
            self.nodes_frame, columns=columns, show="headings",
            bootstyle="info", height=18, selectmode="extended",
        )
        self.nodes_tree.heading("id", text="ID", anchor=CENTER)
        self.nodes_tree.column("id", width=60, anchor=CENTER)
        self.nodes_tree.column("x", width=110, anchor=CENTER)
        self.nodes_tree.column("y", width=110, anchor=CENTER)
        self._configure_row_tags(self.nodes_tree)

        # Scrollbar omitido: la rueda del mouse sobre Treeview es nativa en Tk.
        self.nodes_tree.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        self.nodes_tree.bind("<Double-1>", self._on_node_double_click)
        self.nodes_tree.bind("<<TreeviewSelect>>", self._on_node_select)
        self.nodes_tree.bind("<Delete>", lambda e: self._remove_node())
        bind_clipboard(self.nodes_tree, self._copy_node_row, self._paste_nodes)

    # ─── Elementos ──────────────────────────────────────────────────────

    def _build_elements_panel(self):
        # Mini banner superior con boton toggle "Dibujar elemento" — la
        # ruta rapida para crear elementos clickeando en el canvas.
        # Pre-flight de material: si no hay materiales definidos al
        # activarlo, abre MaterialDialog antes (mismo patron que el
        # placeholder doble-click).
        top_bar = ttk.Frame(self.elements_frame)
        top_bar.pack(side=TOP, fill=X, padx=5, pady=(5, 0))
        self.draw_btn = ttk.Button(
            top_bar, text="🖊  Dibujar",
            bootstyle="info-outline",
            command=self._on_toggle_draw_mode,
        )
        self.draw_btn.pack(side=LEFT)
        # Tooltip: descubrible al hover, sin ruido visual cuando no se
        # necesita. Cubre los atajos AutoCAD-style (D / F8 / Shift /
        # Backspace / Esc) y la sintaxis de coords del Entry flotante.
        ToolTip(
            self.draw_btn,
            text=(
                "Dibujar elemento (D)\n"
                "\n"
                "Click en canvas para colocar cada vertice. Snap "
                "automatico a nodos existentes (10 px).\n"
                "\n"
                "Coords precisas en el Entry flotante:\n"
                "  · 100        relativa al ultimo vertice (default)\n"
                "  · #150       absoluta (override)\n"
                "  · 100,50     coma = salto X → Y\n"
                "\n"
                "F8: ortho toggle (lock H/V dominante).\n"
                "Shift presionado: override temporal (XOR con F8).\n"
                "Con ortho activo, el Entry pasa a 1 campo de distancia.\n"
                "\n"
                "Backspace: descartar ultimo vertice del elemento parcial.\n"
                "Esc: cancelar elemento / salir del modo."
            ),
            wraplength=460,
        )

        columns = ("id", "n1", "n2", "n3", "n4", "espesor", "material")
        self.elements_tree = ttk.Treeview(
            self.elements_frame, columns=columns, show="headings",
            bootstyle="info", height=18, selectmode="extended",
        )
        self.elements_tree.heading("id", text="ID", anchor=CENTER)
        self.elements_tree.heading("n1", text="N1", anchor=CENTER)
        self.elements_tree.heading("n2", text="N2", anchor=CENTER)
        self.elements_tree.heading("n3", text="N3", anchor=CENTER)
        self.elements_tree.heading("n4", text="N4", anchor=CENTER)
        self.elements_tree.heading("material", text="Material", anchor=CENTER)
        for col in ("id", "n1", "n2", "n3", "n4"):
            self.elements_tree.column(col, width=50, anchor=CENTER)
        self.elements_tree.column("espesor", width=85, anchor=CENTER)
        self.elements_tree.column("material", width=140, anchor=CENTER)
        self._configure_row_tags(self.elements_tree)

        # Scrollbar omitido: la rueda del mouse sobre Treeview es nativa en Tk.
        self.elements_tree.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        self.elements_tree.bind("<Double-1>", self._on_element_double_click)
        self.elements_tree.bind("<<TreeviewSelect>>", self._on_element_select)
        self.elements_tree.bind("<Delete>", lambda e: self._remove_element())
        bind_clipboard(self.elements_tree, self._copy_element_row,
                       self._paste_elements)

    # ─── Cargas Nodales ─────────────────────────────────────────────────

    def _build_loads_panel(self):
        columns = ("node_id", "fx", "fy")
        self.loads_tree = ttk.Treeview(
            self.loads_frame, columns=columns, show="headings",
            bootstyle="info", height=18, selectmode="extended",
        )
        self.loads_tree.heading("node_id", text="Nodo", anchor=CENTER)
        self.loads_tree.column("node_id", width=110, anchor=CENTER)
        self.loads_tree.column("fx", width=110, anchor=CENTER)
        self.loads_tree.column("fy", width=110, anchor=CENTER)
        self._configure_row_tags(self.loads_tree)

        # Scrollbar omitido: la rueda del mouse sobre Treeview es nativa en Tk.
        self.loads_tree.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        self.loads_tree.bind("<Double-1>", self._on_load_double_click)
        self.loads_tree.bind("<<TreeviewSelect>>", self._on_load_select)
        self.loads_tree.bind("<Delete>", lambda e: self._remove_load())
        # Single-click sobre fila fantasma confirma con defaults.
        self.loads_tree.bind(
            "<Button-1>",
            lambda e: self._on_tree_button1(self.loads_tree, e),
            add="+",
        )
        bind_clipboard(self.loads_tree, self._copy_load_row, self._paste_loads)

    # ─── Restricciones ──────────────────────────────────────────────────

    def _build_constraints_panel(self):
        columns = ("node_id", "rx", "ry")
        self.constraints_tree = ttk.Treeview(
            self.constraints_frame, columns=columns, show="headings",
            bootstyle="info", height=18, selectmode="extended",
        )
        self.constraints_tree.heading("node_id", text="Nodo", anchor=CENTER)
        self.constraints_tree.heading("rx", text="Restringir X", anchor=CENTER)
        self.constraints_tree.heading("ry", text="Restringir Y", anchor=CENTER)
        self.constraints_tree.column("node_id", width=110, anchor=CENTER)
        self.constraints_tree.column("rx", width=110, anchor=CENTER)
        self.constraints_tree.column("ry", width=110, anchor=CENTER)
        self._configure_row_tags(self.constraints_tree)

        # Scrollbar omitido: la rueda del mouse sobre Treeview es nativa en Tk.
        self.constraints_tree.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # Solo doble-click edita: por consistencia con el resto de las
        # tablas. El toggle por click simple fue eliminado para evitar
        # toggles accidentales y unificar la UX (todas las tablas usan
        # doble-click para editar).
        self.constraints_tree.bind("<Double-1>", self._on_constraint_double_click)
        self.constraints_tree.bind("<<TreeviewSelect>>", self._on_constraint_select)
        self.constraints_tree.bind("<Delete>",
                                   lambda e: self._remove_constraint())
        self.constraints_tree.bind(
            "<Button-1>",
            lambda e: self._on_tree_button1(self.constraints_tree, e),
            add="+",
        )
        bind_clipboard(self.constraints_tree, self._copy_constraint_row,
                       self._paste_constraints)

    # ─── Cargas Superficiales (sin columna Elem) ────────────────────────

    def _build_surface_loads_panel(self):
        columns = ("n_start", "n_end", "q_start", "q_end", "angle")
        self.surface_tree = ttk.Treeview(
            self.surface_frame, columns=columns, show="headings",
            bootstyle="info", height=18, selectmode="extended",
        )
        self.surface_tree.heading("n_start", text="N. Inicio", anchor=CENTER)
        self.surface_tree.heading("n_end", text="N. Final", anchor=CENTER)
        # Anchos rebalanceados: los IDs de nodo son enteros cortos -> 70 px;
        # las cargas q llevan unidades en el header (ej. "q Inicio [kN/m]")
        # y valores con decimales -> 120 px; el angulo es corto -> 80 px.
        for col in ("n_start", "n_end"):
            self.surface_tree.column(col, width=70, anchor=CENTER)
        for col in ("q_start", "q_end"):
            self.surface_tree.column(col, width=100, anchor=CENTER)
        self.surface_tree.column("angle", width=80, anchor=CENTER)
        self._configure_row_tags(self.surface_tree)

        # Scrollbar omitido: la rueda del mouse sobre Treeview es nativa en Tk.
        self.surface_tree.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        self.surface_tree.bind("<Double-1>", self._on_surface_double_click)
        self.surface_tree.bind("<<TreeviewSelect>>", self._on_surface_select)
        self.surface_tree.bind("<Delete>",
                               lambda e: self._remove_surface_load())
        self.surface_tree.bind(
            "<Button-1>",
            lambda e: self._on_tree_button1(self.surface_tree, e),
            add="+",
        )
        bind_clipboard(self.surface_tree, self._copy_surface_row,
                       self._paste_surface_loads)

    # ═════════════════════════════════════════════════════════════════════
    # PENDING NEW: estado y diálogo de descarte
    # ═════════════════════════════════════════════════════════════════════

    def _set_pending(self, *, tree_name, tree, iid, discard, refresh,
                     required, completed=None, on_complete=None):
        self._pending_new = {
            "tree_name": tree_name,
            "tree": tree,
            "iid": iid,
            "discard": discard,
            "refresh": refresh,
            "required": set(required),
            "completed": set(completed or []),
            "on_complete": on_complete,
        }

    def _mark_completed(self, col_index):
        if not self._pending_new:
            return
        self._pending_new["completed"].add(col_index)
        if self._pending_new["completed"] >= self._pending_new["required"]:
            on_complete = self._pending_new.get("on_complete")
            self._pending_new = None
            if on_complete is not None:
                try:
                    on_complete()
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    try:
                        self.main_window.set_status(
                            f"Error al finalizar registro: {type(e).__name__}: {e}"
                        )
                    except Exception:
                        pass

    def _on_subtab_changed(self, _event=None):
        """Handler de cambio de sub-pestaña: libera lock pending y, si la
        pestaña activa es Elementos en un proyecto Q9, muestra un hint en la
        status bar indicando que los nodos 5..9 se generan automáticamente
        (la tabla sólo expone los 4 vértices por decisión de UX).
        """
        self._check_pending_completion()
        # Safety net Q9: catch-all por si quedo algun Q4 valido sin expandir
        # tras paste TSV, abandono completado a posteriori, etc.
        self._ensure_q9_consistency()
        try:
            current = self.data_notebook.nametowidget(self.data_notebook.select())
        except Exception:
            return
        if current is getattr(self, "elements_frame", None):
            if getattr(self.project, "element_type", None) == ELEMENT_Q9:
                msg = ("Proyecto Q9: la tabla sólo expone los 4 vértices. "
                       "Los 5 nodos adicionales (medios + centroide) se "
                       "generan automáticamente al crear el elemento.")
                try:
                    self.main_window.set_status(msg)
                except Exception:
                    pass

    def _check_pending_completion(self):
        """Libera el lock pending sin interrumpir al usuario.

        Si hay un registro pendiente con campos sin completar, en lugar de
        un modal askyesno bloqueante, simplemente se libera el lock: el
        registro queda con sus valores por defecto (0.0 en campos numericos,
        primer nodo disponible, etc.) y el usuario puede editarlo en cualquier
        momento con doble-click o eliminarlo con Supr. Se muestra una pista
        no-modal en la status bar.

        Siempre retorna True (la API se conserva por compatibilidad con los
        callers, pero ya no hay rama "el usuario eligio continuar editando").
        """
        if self._suppress_pending_check or self._pending_new is None:
            return True
        p = self._pending_new
        was_incomplete = p["completed"] < p["required"]
        self._pending_new = None
        if was_incomplete:
            # Mensaje especifico cuando es un elemento incompleto en proyecto
            # Q9: el usuario debe saber que el elemento queda como Q4 hasta
            # que termine de definir los 4 vertices.
            if (p.get("tree_name") == "Elementos"
                    and getattr(self.project, "element_type", None) == ELEMENT_Q9):
                msg = (
                    "Elementos: fila incompleta -- el elemento queda como Q4 "
                    "hasta que completes los 4 vertices. Doble-click para "
                    "editar o Supr para eliminar."
                )
            else:
                msg = (
                    f"{p['tree_name']}: fila creada con valores por defecto. "
                    f"Doble-click para editar o Supr para eliminar."
                )
            try:
                self.main_window.set_status(msg)
            except Exception:
                pass
        return True

    def _capture(self, label):
        """Helper: snapshot del estado actual del proyecto en el undo
        stack. Llamar ANTES de mutar el modelo. No-op si el undo_stack
        no esta disponible (modo headless o antes del wiring).
        """
        try:
            stack = getattr(self.main_window, "undo_stack", None)
            if stack is not None:
                stack.capture(label)
        except Exception:
            pass

    def _ensure_q9_consistency(self, *, silent=False):
        """Safety net UI: delega en `auto_expand_if_q9` (logica de modelo)
        y agrega refresco de tablas/canvas + mensaje en status bar.

        Cubre los casos donde el callback `on_complete` del placeholder no
        se disparo: paste TSV, abandono incompleto que despues se completa
        via dobles-clicks separados, edicion directa, etc.

        Si `silent=True`, no muestra mensaje en status bar (util cuando se
        llama desde refrescos automaticos o tras un import que ya muestra
        su propio mensaje).
        Retorna el numero de elementos expandidos.
        """
        # Snapshot de candidatos antes de expandir, para construir el mensaje
        candidates_ids = [
            e.id for e in self.project.elements.values()
            if e.num_nodes == 4 and len(set(e.node_ids[:4])) == 4
        ] if getattr(self.project, "element_type", None) == ELEMENT_Q9 else []

        try:
            num = auto_expand_if_q9(self.project)
        except Exception as exc:
            try:
                self.main_window.set_status(
                    f"Error expandiendo Q4->Q9: {type(exc).__name__}: {exc}"
                )
            except Exception:
                pass
            return 0

        if num == 0:
            return 0

        # Refrescar tablas y canvas para reflejar los nuevos mid/center nodes
        try:
            self._refresh_elements_tree()
            self._refresh_nodes_tree()
            self._safe_redraw()
        except Exception:
            pass
        if not silent:
            try:
                if num == 1:
                    msg = (f"Elemento {candidates_ids[0]}: nodos medios y "
                           f"centroide generados automaticamente (Q9).")
                else:
                    msg = (f"{num} elementos expandidos a Q9: "
                           f"nodos medios y centroides generados.")
                self.main_window.set_status(msg)
            except Exception:
                pass
        return num

    def _reselect_pending(self):
        if not self._pending_new:
            return
        p = self._pending_new
        try:
            p["tree"].selection_set(p["iid"])
            p["tree"].focus(p["iid"])
            p["tree"].see(p["iid"])
        except tk.TclError:
            pass

    # ═════════════════════════════════════════════════════════════════════
    # NODOS — handlers
    # ═════════════════════════════════════════════════════════════════════

    def _on_node_double_click(self, event):
        item = self.nodes_tree.identify_row(event.y)
        col = self.nodes_tree.identify_column(event.x)
        if not item or not col:
            return
        ci = int(col.replace("#", "")) - 1

        if item == PLACEHOLDER_IID:
            if not self._check_pending_completion():
                return
            self._capture("crear nodo")
            node = self.project.add_node(0.0, 0.0)
            self._refresh_nodes_tree()
            iid = str(node.id)
            self._set_pending(
                tree_name="Nodos", tree=self.nodes_tree, iid=iid,
                discard=lambda nid=node.id: self.project.remove_node(nid),
                refresh=self._refresh_nodes_tree,
                required={1, 2},
            )
            self._after_create_select(self.nodes_tree, iid, col)
            # Saltar el ID en placeholder: ir directo a X
            self._edit_node_cell(iid, "#2", 1)
            return

        self._edit_node_cell(item, col, ci)

    def _edit_node_cell(self, item, col, ci):
        node_id = int(item)
        node = self.project.nodes.get(node_id)
        if node is None:
            return

        # Q9 mid/center: read-only en TODAS las celdas (ID + X + Y). Estos
        # nodos se generan automaticamente desde los vertices macro y se
        # recalculan en cascada cuando el usuario mueve un vertice. Editar
        # su ID o coords manualmente romperia la consistencia interna del
        # elemento Q9.
        role = classify_nodes(self.project).get(node_id, "corner")
        if role in ("mid", "center"):
            etiqueta = "Nodo medio" if role == "mid" else "Centroide"
            try:
                self.main_window.set_status(
                    f"{etiqueta} de Q9 (auto, read-only): edita los vertices "
                    f"del elemento para reposicionarlo."
                )
            except Exception:
                pass
            return

        if ci == 0:
            current = node.id

            def _commit_id(text):
                try:
                    new_id = int(text.strip())
                except ValueError:
                    messagebox.showerror("ID invalido",
                                         "El ID debe ser un entero.")
                    return
                if new_id == node.id:
                    return
                self._capture(f"renombrar nodo {node.id} -> {new_id}")
                try:
                    self.project.change_node_id(node.id, new_id)
                except ValueError as e:
                    messagebox.showerror("ID en uso", str(e))
                    return
                # Refrescar todas las tablas que pueden contener referencias
                self._refresh_all_trees()
                self._safe_redraw()
            start_cell_editor(self.nodes_tree, item, col, current, _commit_id)
            return

        if ci == 1 and self._is_pending(item) and not self._is_done(1):
            current = ""
        else:
            current = fmt(node.x if ci == 1 else node.y, "length")

        def _commit(text):
            try:
                val = float(text)
            except ValueError:
                messagebox.showerror("Error", "Valor numerico invalido.")
                return
            axis = "X" if ci == 1 else "Y"
            self._capture(f"editar {axis} de nodo {node_id}")
            if ci == 1:
                node.x = val
            else:
                node.y = val
            self.project.is_modified = True
            self.project.is_solved = False
            # Si el nodo editado es vertice macro de algun Q9, recalcular sus
            # nodos medios y centroide para mantener la geometria coherente.
            # O(1) con el indice inverso en vez de recorrer todos los
            # elementos: solo los que contienen al nodo pueden verse afectados.
            for eid in self.project._node_to_elements.get(node_id, set()):
                elem = self.project.elements.get(eid)
                if (elem is not None and elem.num_nodes == 9
                        and node_id in elem.node_ids[:4]):
                    recompute_q9_midnodes(self.project, elem)
            self._mark_completed(ci)
            self._refresh_nodes_tree()
            self._safe_redraw()
        start_cell_editor(self.nodes_tree, item, col, current, _commit)


    def _on_node_select(self, event):
        if self._syncing_from_canvas:
            return
        # Filtrar placeholder y filas fantasma (no son nodos reales).
        sel = [iid for iid in self.nodes_tree.selection()
               if iid and iid != PLACEHOLDER_IID
               and not iid.startswith("__ghost__")]
        if not sel:
            return
        # Pending check solo para single-select clasico (multi-select
        # ignora el pending lock — caso de uso menor).
        if len(sel) == 1:
            iid = sel[0]
            if self._pending_new and self._pending_new["tree"] is self.nodes_tree \
                    and iid != self._pending_new["iid"]:
                if not self._check_pending_completion():
                    return
                sel = [iid for iid in self.nodes_tree.selection()
                       if iid and iid != PLACEHOLDER_IID
                       and not iid.startswith("__ghost__")]
                if not sel:
                    return
        try:
            node_ids = {int(iid) for iid in sel}
        except ValueError:
            return
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None:
            return
        self._syncing_to_canvas = True
        try:
            canvas.replace_node_selection(node_ids)
        finally:
            self._syncing_to_canvas = False
        if len(node_ids) == 1:
            nid = next(iter(node_ids))
            self.main_window.set_status(f"Nodo {nid} seleccionado")
        else:
            self.main_window.set_status(
                f"{len(node_ids)} nodos seleccionados"
            )

    # ─── Modo dibujo de elementos ───────────────────────────────────────

    def _on_toggle_draw_mode(self):
        """Activa/desactiva el modo dibujo del canvas. Pre-flight: si no
        hay materiales definidos, abre MaterialDialog antes de activar
        (mismo patron que el placeholder de la tabla de elementos)."""
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None:
            return
        if canvas.is_draw_mode_active():
            canvas.disable_draw_mode()
            return
        # Pre-flight de material.
        if not self.project.materials:
            messagebox.showinfo(
                "Sin materiales",
                "Defina al menos un material antes de dibujar elementos.",
            )
            MaterialDialog(self.frame.winfo_toplevel(),
                           self.project, self.main_window)
            if not self.project.materials:
                # Usuario cancelo el dialog.
                return
        # Cambiar a la sub-pestana de Elementos para dar contexto visual
        # del flujo (cada elemento creado aparece en la tabla).
        try:
            self.data_notebook.select(self.elements_frame)
        except tk.TclError:
            pass
        canvas.enable_draw_mode()

    def _on_canvas_draw_mode_changed(self, active):
        """Sincroniza el bootstyle del boton con el estado del modo, y
        refresca el indicador ORTHO en la status bar (solo visible cuando
        draw_mode + ortho activos)."""
        if hasattr(self, "draw_btn"):
            if active:
                self.draw_btn.config(
                    text="🖊  Dibujando", bootstyle="info",
                )
            else:
                self.draw_btn.config(
                    text="🖊  Dibujar", bootstyle="info-outline",
                )
        try:
            self.main_window._update_ortho_indicator()
        except AttributeError:
            pass

    def _on_canvas_draw_element_created(self, _elem_id):
        """Tras crear un elemento via modo dibujo, refrescar nodos +
        elementos (los nuevos vertices entran en la tabla de Nodos)."""
        self._refresh_nodes_tree()
        self._refresh_elements_tree()
        self._update_status_info()
        self.main_window._update_title()

    def _remove_node(self):
        selected = [iid for iid in self.nodes_tree.selection()
                    if iid and iid != PLACEHOLDER_IID]
        if not selected:
            return

        # Calcular el impacto agregado del cascade en TODOS los nodos
        # seleccionados antes de mutar nada. Si toca elementos o preserva
        # huerfanos, pedir confirmacion al usuario.
        node_ids = []
        for iid in selected:
            try:
                node_ids.append(int(iid))
            except ValueError:
                continue

        elements_total = set()
        nodes_del_total = set()
        nodes_pres_total = set()
        for nid in node_ids:
            preview = self.project.preview_node_cascade(nid)
            elements_total.update(preview["elements_to_delete"])
            nodes_del_total.update(preview["nodes_to_delete"])
            nodes_pres_total.update(preview["nodes_to_preserve"])

        if elements_total or nodes_pres_total:
            # Construir mensaje compacto.
            lines = [
                f"Borrar {len(node_ids)} nodo(s) eliminara en cascada:",
                f"  • {len(elements_total)} elemento(s)",
            ]
            if nodes_del_total:
                lines.append(
                    f"  • {len(nodes_del_total)} nodo(s) auxiliar(es) "
                    f"sin datos del usuario"
                )
            if nodes_pres_total:
                lines.append(
                    f"  • {len(nodes_pres_total)} nodo(s) se preservaran "
                    f"como huerfanos (tienen cargas / restricciones / "
                    f"surface refs)"
                )
            lines.append("\n¿Continuar?")
            if not messagebox.askyesno(
                "Confirmar borrado en cascada", "\n".join(lines)
            ):
                return

        self._capture(f"eliminar {len(node_ids)} nodo(s)")
        for nid in node_ids:
            try:
                self.project.remove_node_with_cascade(nid)
            except (ValueError, KeyError):
                pass
        # Borrar nodos puede invalidar elementos / cargas / BCs / surface refs
        self._refresh_all_trees()
        self._safe_redraw()
        self._update_status_info()
        self.main_window.set_status("Nodo(s) eliminado(s).")

    # ─── Acciones de menu contextual: Nodos ─────────────────────────────


    # ═════════════════════════════════════════════════════════════════════
    # ELEMENTOS — handlers
    # ═════════════════════════════════════════════════════════════════════

    def _on_element_double_click(self, event):
        item = self.elements_tree.identify_row(event.y)
        col = self.elements_tree.identify_column(event.x)
        if not item or not col:
            return
        ci = int(col.replace("#", "")) - 1

        if item == PLACEHOLDER_IID:
            if not self._check_pending_completion():
                return
            mat_names = list(self.project.materials.keys())
            if not mat_names:
                messagebox.showwarning(
                    "Sin materiales",
                    "Defina al menos un material antes de crear elementos."
                )
                MaterialDialog(self.frame.winfo_toplevel(),
                               self.project, self.main_window)
                mat_names = list(self.project.materials.keys())
                if not mat_names:
                    return
            first_node = next(iter(self.project.nodes), 1)
            self._capture("crear elemento")
            elem = self.project.add_element(
                [first_node] * 4,
                self.project.default_thickness,
                mat_names[0],
            )
            self._refresh_elements_tree()
            iid = str(elem.id)

            def _expand_if_q9(eid=elem.id):
                # Si el proyecto esta en Q9, generar mid/center nodes del
                # elemento recien creado. Delega al safety net global que
                # tambien cubre paste TSV y abandonos parciales.
                if self.project.element_type != ELEMENT_Q9:
                    return
                target = self.project.elements.get(eid)
                if target is None:
                    return
                # Guard: 4 vertices distintos para evitar Q9 degenerado
                if target.num_nodes == 4 and len(set(target.node_ids[:4])) != 4:
                    try:
                        self.main_window.set_status(
                            f"Elemento {eid}: vertices duplicados, no se "
                            f"expandio a Q9. Edita los nodos para que sean "
                            f"distintos y se generaran los nodos internos."
                        )
                    except Exception:
                        pass
                    return
                self._ensure_q9_consistency()

            self._set_pending(
                tree_name="Elementos", tree=self.elements_tree, iid=iid,
                discard=lambda eid=elem.id: self.project.remove_element(eid),
                refresh=self._refresh_elements_tree,
                required={1, 2, 3, 4},
                on_complete=_expand_if_q9,
            )
            self._after_create_select(self.elements_tree, iid, "#2")
            self._edit_element_cell(iid, "#2", 1)
            return

        self._edit_element_cell(item, col, ci)

    def _edit_element_cell(self, item, col, ci):
        elem = self.project.elements.get(int(item))
        if elem is None:
            return

        # ID editable
        if ci == 0:
            current = elem.id

            def _commit_id(text):
                try:
                    new_id = int(text.strip())
                except ValueError:
                    messagebox.showerror("ID invalido",
                                         "El ID debe ser un entero.")
                    return
                if new_id == elem.id:
                    return
                self._capture(f"renombrar elemento {elem.id} -> {new_id}")
                try:
                    self.project.change_element_id(elem.id, new_id)
                except ValueError as e:
                    messagebox.showerror("ID en uso", str(e))
                    return
                self._refresh_elements_tree()
                self._refresh_surface_tree()
                self._safe_redraw()
            start_cell_editor(self.elements_tree, item, col, current, _commit_id)
            return

        if ci == 6:  # material → combobox
            mat_names = list(self.project.materials.keys())
            if not mat_names:
                MaterialDialog(self.frame.winfo_toplevel(),
                               self.project, self.main_window)
                mat_names = list(self.project.materials.keys())
                if not mat_names:
                    return

            def _commit_mat(value):
                if value and value in self.project.materials:
                    if elem.material_name != value:
                        self._capture(
                            f"cambiar material de elemento {elem.id}"
                        )
                    elem.material_name = value
                    self.project.is_modified = True
                    self.project.is_solved = False
                    self._mark_completed(ci)
                    self._refresh_elements_tree()
                    self._safe_redraw()

            start_combobox_editor(self.elements_tree, item, col,
                                  elem.material_name, mat_names, _commit_mat)
            return

        if ci in (1, 2, 3, 4):
            current = elem.node_ids[ci - 1] if ci - 1 < len(elem.node_ids) else ""
        elif ci == 5:
            current = fmt(elem.thickness, "length")
        else:
            return

        def _commit(text):
            vertex_changed_on_q9 = False
            try:
                if ci in (1, 2, 3, 4):
                    val = int(text)
                    if val not in self.project.nodes:
                        messagebox.showerror(
                            "Error", f"El nodo {val} no existe.")
                        return
                    while len(elem.node_ids) < 4:
                        elem.node_ids.append(val)
                    old_val = elem.node_ids[ci - 1]
                    if old_val != val:
                        self._capture(
                            f"editar N{ci} de elemento {elem.id}"
                        )
                    elem.node_ids[ci - 1] = val
                    # Si el elemento es Q9 existente y cambio un vertice macro,
                    # los mid-nodes calculados sobre el vertice anterior quedan
                    # en posiciones geometricamente incorrectas. Se recalculan
                    # in-place via recompute_q9_midnodes (preserva IDs y datos
                    # del usuario en los mid-nodes; solo muta x/y para que la
                    # geometria del cuadrilatero curvo siga el cambio).
                    if elem.num_nodes == 9 and old_val != val:
                        recompute_q9_midnodes(self.project, elem)
                        vertex_changed_on_q9 = True
                else:
                    new_thick = float(text)
                    if elem.thickness != new_thick:
                        self._capture(
                            f"editar espesor de elemento {elem.id}"
                        )
                    elem.thickness = new_thick
            except ValueError:
                messagebox.showerror("Error", "Valor invalido.")
                return
            self.project.is_modified = True
            self.project.is_solved = False
            self._mark_completed(ci)
            self._refresh_elements_tree()
            if vertex_changed_on_q9:
                # Mid-nodes movidos -> tabla de Nodos refleja las nuevas coords
                self._refresh_nodes_tree()
                try:
                    self.main_window.set_status(
                        f"Elemento {elem.id}: vertice N{ci} actualizado, "
                        f"mid-nodes y centroide recalculados."
                    )
                except Exception:
                    pass
            self._safe_redraw()
            # Safety net: si el elemento quedo Q4 valido en proyecto Q9
            # (porque on_complete no se disparo o el elemento se edito
            # fuera del flujo de placeholder), expandir aqui.
            self._ensure_q9_consistency()
        start_cell_editor(self.elements_tree, item, col, current, _commit)


    def _on_element_select(self, event):
        if self._syncing_from_canvas:
            return
        sel_all = [iid for iid in self.elements_tree.selection()
                   if iid and iid != PLACEHOLDER_IID
                   and not iid.startswith("__ghost__")]
        if not sel_all:
            return
        if len(sel_all) > 1:
            try:
                eids = {int(iid) for iid in sel_all}
            except ValueError:
                return
            canvas = getattr(self.main_window, "mesh_canvas", None)
            if canvas is not None:
                self._syncing_to_canvas = True
                try:
                    canvas.replace_element_selection(eids)
                finally:
                    self._syncing_to_canvas = False
            self.main_window.set_status(
                f"{len(eids)} elementos seleccionados"
            )
            return
        # Single-select clasico: mantener pending check + highlight
        sel = sel_all
        iid = sel[0]
        if self._pending_new and self._pending_new["tree"] is self.elements_tree \
                and iid != self._pending_new["iid"]:
            if not self._check_pending_completion():
                return
            sel = self.elements_tree.selection()
            if not sel or sel[0] == PLACEHOLDER_IID:
                return
            iid = sel[0]
        try:
            eid = int(iid)
        except ValueError:
            return
        # IMPORTANTE: envolver la mutacion del canvas con `_syncing_to_canvas`
        # para cortocircuitar el callback `_on_canvas_selection_changed`. Sin
        # este guard, el callback dispara un rebuild completo del tree, lo
        # que borra y re-inserta las filas y PIERDE la seleccion nativa de
        # ttk. Resultado: la fila se ve highlighted (via tag) pero
        # `tree.selection()` queda vacio, y al apretar Supr `_remove_element`
        # no encuentra nada que borrar. El branch multi-select arriba ya
        # aplica el mismo guard — este branch lo replicaba via
        # `_safe_highlight_element` SIN el guard, que era el bug.
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is not None:
            self._syncing_to_canvas = True
            try:
                canvas.replace_element_selection({eid})
            finally:
                self._syncing_to_canvas = False
        self.main_window.set_status(f"Elemento {eid} seleccionado")

    def _remove_element(self):
        """Elimina los elementos seleccionados aplicando auto-cleanup
        de nodos huerfanos. Modal de confirmacion espejado del de
        `mesh_canvas._on_delete_key`: si el cleanup eliminara nodos
        auxiliares o preservara huerfanos con datos, agrega los previews
        de todos los seleccionados y pide confirmacion. Resumen final en
        status bar tras el borrado.
        Los nodos preservados se ven en gris en canvas + tabla Nodos.
        """
        selected = [iid for iid in self.elements_tree.selection()
                    if iid and iid != PLACEHOLDER_IID]
        if not selected:
            return

        # Calcular el impacto agregado del cleanup en TODOS los elementos
        # seleccionados antes de mutar nada. Si toca nodos auxiliares o
        # preserva huerfanos, pedir confirmacion al usuario. Patron
        # espejado de `_remove_node` para uniformidad UX.
        elem_ids = []
        for iid in selected:
            try:
                elem_ids.append(int(iid))
            except ValueError:
                continue

        nodes_del_total = set()
        nodes_pres_total = set()
        for eid in elem_ids:
            preview = self._preview_element_cleanup(eid)
            nodes_del_total.update(preview["nodes_to_delete"])
            nodes_pres_total.update(preview["nodes_to_preserve"])

        if nodes_del_total or nodes_pres_total:
            lines = [
                f"Borrar {len(elem_ids)} elemento(s) eliminara en cascada:",
                f"  • {len(elem_ids)} elemento(s)",
            ]
            if nodes_del_total:
                lines.append(
                    f"  • {len(nodes_del_total)} nodo(s) auxiliar(es) "
                    f"sin datos del usuario"
                )
            if nodes_pres_total:
                lines.append(
                    f"  • {len(nodes_pres_total)} nodo(s) se preservaran "
                    f"como huerfanos (tienen cargas / restricciones / "
                    f"surface refs)"
                )
            lines.append("\n¿Continuar?")
            if not messagebox.askyesno(
                "Confirmar borrado en cascada", "\n".join(lines)
            ):
                return

        self._capture(f"eliminar {len(elem_ids)} elemento(s)")
        total_deleted_nodes = []
        total_preserved_nodes = []
        elem_ids_removed = []
        for eid in elem_ids:
            try:
                summary = self.project.remove_element(eid)
                if summary.get("deleted"):
                    elem_ids_removed.append(eid)
                    total_deleted_nodes.extend(summary.get("nodes_deleted", []))
                    total_preserved_nodes.extend(summary.get("nodes_preserved", []))
            except (ValueError, KeyError):
                pass
        # Refrescar TODAS las tablas porque cleanup borra nodos y los nodos
        # eliminados pueden tener cargas/BCs/surface_loads asociadas (que
        # `remove_node` interno habria limpiado) -- aunque el auto-cleanup
        # justamente preserva los nodos con datos, asi que cargas/BCs
        # nunca se pierden por este flujo. Igual refresh todo por
        # consistencia (espacio en blanco de la fila, etc.).
        self._refresh_all_trees()
        self._safe_redraw()
        self._update_status_info()
        # Resumen contextual en status bar
        if elem_ids_removed:
            partes = [f"Elemento(s) {','.join(map(str, elem_ids_removed))} eliminado(s)"]
            if total_deleted_nodes:
                partes.append(
                    f"{len(total_deleted_nodes)} nodo(s) auto-eliminado(s) "
                    f"(sin referencias)"
                )
            if total_preserved_nodes:
                partes.append(
                    f"{len(total_preserved_nodes)} nodo(s) preservado(s) "
                    f"(con cargas/restricciones — quedan como huerfanos)"
                )
            try:
                self.main_window.set_status(". ".join(partes) + ".")
            except Exception:
                pass

    def _preview_element_cleanup(self, elem_id):
        """Delega en `ProjectModel.preview_element_cleanup` (fuente única,
        antes duplicada verbatim aquí y en mesh_canvas)."""
        return self.project.preview_element_cleanup(elem_id)

    # ─── Acciones de menu contextual: Elementos ─────────────────────────


    # ═════════════════════════════════════════════════════════════════════
    # CARGAS NODALES — handlers
    # ═════════════════════════════════════════════════════════════════════

    def _on_load_double_click(self, event):
        item = self.loads_tree.identify_row(event.y)
        col = self.loads_tree.identify_column(event.x)
        if not item or not col:
            return
        # Fila fantasma: confirmar la sugerencia (single-click style) y
        # abrir editor en la celda clickeada de la fila real recien
        # creada. Patron para los 3 trees con fantasma (loads/bc/surf).
        if item.startswith("__ghost__"):
            try:
                nid = int(item[len("__ghost__"):])
            except ValueError:
                return
            self._commit_load_ghost(nid)
            new_iid = str(nid)
            if new_iid in self.loads_tree.get_children():
                try:
                    ci_g = int(col.replace("#", "")) - 1
                except (ValueError, AttributeError):
                    ci_g = 0
                self._edit_load_cell(new_iid, col, ci_g)
            return
        ci = int(col.replace("#", "")) - 1

        if item == PLACEHOLDER_IID:
            if not self._check_pending_completion():
                return
            available = [nid for nid in sorted(self.project.nodes)
                         if nid not in self.project.nodal_loads]
            if not available:
                messagebox.showwarning(
                    "Sin nodos disponibles",
                    "Todos los nodos ya tienen carga o no existen nodos.\n"
                    "Cree primero un nodo en la pestana Nodos.")
                return
            nid = available[0]
            self._capture("crear carga nodal")
            self.project.set_nodal_load(nid, 0.0, 0.0)
            self._refresh_loads_tree()
            iid = str(nid)
            self._set_pending(
                tree_name="Cargas", tree=self.loads_tree, iid=iid,
                discard=lambda n=nid: self.project.remove_nodal_load(n),
                refresh=self._refresh_loads_tree,
                required={0, 1, 2},
            )
            first_col = "#1"
            self._after_create_select(self.loads_tree, iid, first_col)
            self._edit_load_cell(iid, first_col, 0)
            return

        # Filas reales: permitir editar cualquier celda (incluyendo Nodo, ci=0).
        # _edit_load_cell ya valida unicidad y maneja el rename via remove+set.
        self._edit_load_cell(item, col, ci)

    def _edit_load_cell(self, item, col, ci):
        load = self.project.nodal_loads.get(int(item))
        if load is None:
            return

        if ci == 0:
            current = load.node_id

            def _commit(text):
                try:
                    new_nid = int(text)
                except ValueError:
                    messagebox.showerror("Error", "Nodo invalido.")
                    return
                if new_nid not in self.project.nodes:
                    messagebox.showerror(
                        "Error", f"El nodo {new_nid} no existe.")
                    return
                if new_nid == load.node_id:
                    self._mark_completed(0)
                    return
                if new_nid in self.project.nodal_loads:
                    messagebox.showerror(
                        "Error", f"Ya existe una carga en el nodo {new_nid}.")
                    return
                self._capture(
                    f"mover carga nodo {load.node_id} -> {new_nid}"
                )
                self.project.remove_nodal_load(load.node_id)
                self.project.set_nodal_load(new_nid, load.fx, load.fy)
                if self._pending_new and self._pending_new["iid"] == str(load.node_id):
                    self._pending_new["iid"] = str(new_nid)
                    self._pending_new["discard"] = (
                        lambda n=new_nid: self.project.remove_nodal_load(n))
                self._mark_completed(0)
                self._refresh_loads_tree()
                self._safe_redraw()
            start_cell_editor(self.loads_tree, item, col, current, _commit)
            return

        current = fmt(load.fx if ci == 1 else load.fy, "force")

        def _commit(text):
            try:
                val = float(text)
            except ValueError:
                messagebox.showerror("Error", "Valor numerico invalido.")
                return
            comp = "Fx" if ci == 1 else "Fy"
            self._capture(f"editar {comp} de carga en nodo {load.node_id}")
            if ci == 1:
                load.fx = val
            else:
                load.fy = val
            self.project.is_modified = True
            self.project.is_solved = False
            self._mark_completed(ci)
            self._refresh_loads_tree()
            self._safe_redraw()
        start_cell_editor(self.loads_tree, item, col, current, _commit)


    def _on_load_select(self, event):
        if self._syncing_from_canvas:
            return
        sel = [iid for iid in self.loads_tree.selection()
               if iid and iid != PLACEHOLDER_IID
               and not iid.startswith("__ghost__")]
        if not sel:
            return
        try:
            nids = {int(iid) for iid in sel}
        except ValueError:
            return
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is not None:
            self._syncing_to_canvas = True
            try:
                # Reemplazo del set de loads + nodos asociados (para halo)
                canvas._clear_all_sets_silent()
                canvas.selected_loads = set(nids)
                canvas.selected_nodes = set(nids)
                canvas._emit_selection_changed()
                canvas.redraw()
            finally:
                self._syncing_to_canvas = False
        if len(nids) == 1:
            nid = next(iter(nids))
            self.main_window.set_status(f"Carga en nodo {nid} seleccionada")
        else:
            self.main_window.set_status(
                f"{len(nids)} cargas seleccionadas"
            )

    def _remove_load(self):
        selected = [iid for iid in self.loads_tree.selection()
                    if iid and iid != PLACEHOLDER_IID]
        if not selected:
            return
        self._capture(f"eliminar {len(selected)} carga(s) nodal(es)")
        for iid in selected:
            try:
                self.project.remove_nodal_load(int(iid))
            except (ValueError, KeyError):
                pass
        self._refresh_loads_tree()
        self._safe_redraw()

    # ─── Acciones de menu contextual: Cargas ────────────────────────────


    # ═════════════════════════════════════════════════════════════════════
    # RESTRICCIONES — handlers
    # ═════════════════════════════════════════════════════════════════════

    def _on_constraint_double_click(self, event):
        """Doble-click en cualquier celda de una restriccion:
        - Placeholder: crear nueva BC y abrir editor del Nodo.
        - Fila real, columna Nodo (ci=0): abrir editor del Nodo (cambiar
          la BC a otro nodo, manteniendo flags X/Y).
        - Fila real, columna X (ci=1): toggle restrain_x con capture undo.
        - Fila real, columna Y (ci=2): toggle restrain_y con capture undo.
        """
        item = self.constraints_tree.identify_row(event.y)
        col = self.constraints_tree.identify_column(event.x)
        if not item or not col:
            return
        # Fila fantasma: confirmar y abrir editor en la celda clickeada
        # de la fila real recien creada.
        if item.startswith("__ghost__"):
            try:
                nid = int(item[len("__ghost__"):])
            except ValueError:
                return
            self._commit_constraint_ghost(nid)
            new_iid = str(nid)
            if new_iid in self.constraints_tree.get_children():
                try:
                    ci_g = int(col.replace("#", "")) - 1
                except (ValueError, AttributeError):
                    ci_g = 0
                # ci=0 -> editar nodo; ci=1/2 -> toggle restrain_x/y.
                if ci_g == 0:
                    self._edit_constraint_node_cell(new_iid, col)
                elif ci_g in (1, 2):
                    bc = self.project.boundary_conditions.get(int(new_iid))
                    if bc is not None:
                        axis = "X" if ci_g == 1 else "Y"
                        self._capture(
                            f"toggle restriccion {axis} en nodo {bc.node_id}")
                        if ci_g == 1:
                            bc.restrain_x = not bc.restrain_x
                        else:
                            bc.restrain_y = not bc.restrain_y
                        self.project.is_modified = True
                        self.project.is_solved = False
                        self._refresh_constraints_tree()
                        self._safe_redraw()
            return
        ci = int(col.replace("#", "")) - 1

        if item == PLACEHOLDER_IID:
            if not self._check_pending_completion():
                return
            available = [nid for nid in self.project.nodes
                         if nid not in self.project.boundary_conditions]
            if not available:
                messagebox.showwarning(
                    "Sin nodos disponibles",
                    "Todos los nodos ya tienen restriccion o no existen nodos."
                )
                return
            nid = available[0]
            self._capture("crear restriccion")
            self.project.set_boundary_condition(nid, True, True)
            self._refresh_constraints_tree()
            iid = str(nid)
            self._set_pending(
                tree_name="Restricciones", tree=self.constraints_tree,
                iid=iid,
                discard=lambda n=nid: self.project.remove_boundary_condition(n),
                refresh=self._refresh_constraints_tree,
                required={0},
            )
            first_col = "#1"
            self._after_create_select(self.constraints_tree, iid, first_col)
            self._edit_constraint_node_cell(iid, first_col)
            return

        # Fila real: dispatch por columna.
        if ci == 0:
            self._edit_constraint_node_cell(item, col)
            return

        if ci in (1, 2):
            bc = self.project.boundary_conditions.get(int(item))
            if bc is None:
                return
            axis = "X" if ci == 1 else "Y"
            self._capture(f"toggle restriccion {axis} en nodo {bc.node_id}")
            if ci == 1:
                bc.restrain_x = not bc.restrain_x
            else:
                bc.restrain_y = not bc.restrain_y
            self.project.is_modified = True
            self.project.is_solved = False
            self._refresh_constraints_tree()
            self._safe_redraw()

    def _edit_constraint_node_cell(self, item, col):
        bc = self.project.boundary_conditions.get(int(item))
        if bc is None:
            return
        current = bc.node_id

        def _commit(text):
            try:
                new_nid = int(text)
            except ValueError:
                messagebox.showerror("Error", "Nodo invalido.")
                return
            if new_nid not in self.project.nodes:
                messagebox.showerror(
                    "Error", f"El nodo {new_nid} no existe.")
                return
            if new_nid == bc.node_id:
                self._mark_completed(0)
                return
            if new_nid in self.project.boundary_conditions:
                messagebox.showerror(
                    "Error", f"Ya existe restriccion en el nodo {new_nid}.")
                return
            self._capture(
                f"mover restriccion nodo {bc.node_id} -> {new_nid}"
            )
            self.project.remove_boundary_condition(bc.node_id)
            self.project.set_boundary_condition(new_nid, bc.restrain_x, bc.restrain_y)
            if self._pending_new and self._pending_new["iid"] == str(bc.node_id):
                self._pending_new["iid"] = str(new_nid)
                self._pending_new["discard"] = (
                    lambda n=new_nid: self.project.remove_boundary_condition(n))
            self._mark_completed(0)
            self._refresh_constraints_tree()
            self._safe_redraw()

        start_cell_editor(self.constraints_tree, item, col, current, _commit)

    def _on_constraint_select(self, event):
        if self._syncing_from_canvas:
            return
        sel = [iid for iid in self.constraints_tree.selection()
               if iid and iid != PLACEHOLDER_IID
               and not iid.startswith("__ghost__")]
        if not sel:
            return
        try:
            nids = {int(iid) for iid in sel}
        except ValueError:
            return
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is not None:
            self._syncing_to_canvas = True
            try:
                canvas._clear_all_sets_silent()
                canvas.selected_constraints = set(nids)
                canvas.selected_nodes = set(nids)
                canvas._emit_selection_changed()
                canvas.redraw()
            finally:
                self._syncing_to_canvas = False
        if len(nids) == 1:
            nid = next(iter(nids))
            self.main_window.set_status(
                f"Restriccion en nodo {nid} seleccionada")
        else:
            self.main_window.set_status(
                f"{len(nids)} restricciones seleccionadas")

    def _remove_constraint(self):
        selected = [iid for iid in self.constraints_tree.selection()
                    if iid and iid != PLACEHOLDER_IID]
        if not selected:
            return
        self._capture(f"eliminar {len(selected)} restriccion(es)")
        for iid in selected:
            try:
                self.project.remove_boundary_condition(int(iid))
            except (ValueError, KeyError):
                pass
        self._refresh_constraints_tree()
        self._safe_redraw()

    # ─── Acciones de menu contextual: Restricciones ─────────────────────


    # ═════════════════════════════════════════════════════════════════════
    # CARGAS SUPERFICIALES — handlers (sin columna Elem)
    # ═════════════════════════════════════════════════════════════════════

    def _on_surface_double_click(self, event):
        item = self.surface_tree.identify_row(event.y)
        col = self.surface_tree.identify_column(event.x)
        if not item or not col:
            return
        # Fila fantasma de surface: iid = "__ghost__N1_N2". Confirmar y
        # abrir editor sobre la nueva fila real (idx = ultimo append).
        if item.startswith("__ghost__"):
            suffix = item[len("__ghost__"):]
            try:
                ns, ne = (int(p) for p in suffix.split("_"))
            except (ValueError, AttributeError):
                return
            self._commit_surface_ghost(frozenset({ns, ne}))
            # El surface recien creado es el ULTIMO en la lista.
            new_idx = len(self.project.surface_loads) - 1
            if new_idx >= 0:
                new_iid = str(new_idx)
                if new_iid in self.surface_tree.get_children():
                    try:
                        ci_g = int(col.replace("#", "")) - 1
                    except (ValueError, AttributeError):
                        ci_g = 0
                    sl_new = self.project.surface_loads[new_idx]
                    self._edit_surface_cell(new_iid, col, ci_g, sl_new)
            return
        ci = int(col.replace("#", "")) - 1

        if item == PLACEHOLDER_IID:
            if not self._check_pending_completion():
                return
            first_node = next(iter(self.project.nodes), 1)
            second_node = first_node
            it = iter(self.project.nodes)
            try:
                next(it)
                second_node = next(it)
            except StopIteration:
                pass
            self._capture("crear carga superficial")
            sl = self.project.add_surface_load(
                first_node, second_node, 0.0, 0.0, 0.0, element_id=None)
            self._refresh_surface_tree()
            idx = len(self.project.surface_loads) - 1
            iid = str(idx)

            def _discard(target=sl):
                if target in self.project.surface_loads:
                    self.project.surface_loads.remove(target)
                    self.project.is_modified = True
                    self.project.is_solved = False

            self._set_pending(
                tree_name="Carg. Superficiales", tree=self.surface_tree,
                iid=iid,
                discard=_discard,
                refresh=self._refresh_surface_tree,
                required={0, 1, 2, 3, 4},
            )
            self._after_create_select(self.surface_tree, iid, col)
            self._edit_surface_cell(iid, col, ci, sl)
            return

        try:
            idx = int(item)
        except ValueError:
            return
        if idx < 0 or idx >= len(self.project.surface_loads):
            return
        sl = self.project.surface_loads[idx]
        self._edit_surface_cell(item, col, ci, sl)

    def _edit_surface_cell(self, item, col, ci, sl):
        attr_map = {0: "node_start", 1: "node_end",
                    2: "q_start", 3: "q_end", 4: "angle"}
        kind_map = {2: "force", 3: "force", 4: "angle"}
        attr = attr_map.get(ci)
        if attr is None:
            return
        raw = getattr(sl, attr)
        kind = kind_map.get(ci)
        current = fmt(raw, kind) if kind else raw

        def _commit(text):
            try:
                if ci in (0, 1):
                    val = int(text)
                    if val not in self.project.nodes:
                        messagebox.showerror(
                            "Error", f"El nodo {val} no existe.")
                        return
                else:
                    val = float(text)
            except ValueError:
                messagebox.showerror("Error", "Valor invalido.")
                return
            old_val = getattr(sl, attr)
            if old_val != val:
                self._capture(f"editar {attr} de carga superficial")
            setattr(sl, attr, val)
            self.project.is_modified = True
            self.project.is_solved = False
            self._mark_completed(ci)
            self._refresh_surface_tree()
            self._safe_redraw()
        start_cell_editor(self.surface_tree, item, col, current, _commit)


    def _on_surface_select(self, event):
        if self._syncing_from_canvas:
            return
        sel = [iid for iid in self.surface_tree.selection()
               if iid and iid != PLACEHOLDER_IID
               and not iid.startswith("__ghost__")]
        if not sel:
            return
        try:
            idxs = {int(iid) for iid in sel}
        except ValueError:
            return
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is not None:
            self._syncing_to_canvas = True
            try:
                canvas._clear_all_sets_silent()
                canvas.selected_surfaces = set(idxs)
                canvas._emit_selection_changed()
                canvas.redraw()
            finally:
                self._syncing_to_canvas = False
        if len(idxs) == 1:
            idx = next(iter(idxs))
            self.main_window.set_status(
                f"Carga superficial #{idx} seleccionada")
        else:
            self.main_window.set_status(
                f"{len(idxs)} cargas superficiales seleccionadas")

    def _remove_surface_load(self):
        selected = [iid for iid in self.surface_tree.selection()
                    if iid and iid != PLACEHOLDER_IID]
        if not selected:
            return
        self._capture(f"eliminar {len(selected)} carga(s) superficial(es)")
        indices = []
        for iid in selected:
            try:
                indices.append(int(iid))
            except ValueError:
                pass
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.project.surface_loads):
                del self.project.surface_loads[idx]
                self.project.is_modified = True
                self.project.is_solved = False
        self._refresh_surface_tree()
        self._safe_redraw()

    # ─── Acciones de menu contextual: Surface ───────────────────────────


    # ═════════════════════════════════════════════════════════════════════
    # COPY / PASTE TSV
    # ═════════════════════════════════════════════════════════════════════

    def _copy_node_row(self, iid):
        if iid == PLACEHOLDER_IID:
            return None
        vals = self.nodes_tree.item(iid)["values"]
        return list(vals) if vals else None

    def _copy_element_row(self, iid):
        if iid == PLACEHOLDER_IID:
            return None
        vals = self.elements_tree.item(iid)["values"]
        if not vals:
            return None
        out = list(vals)
        # Stripear el glifo ▾ del material para que el paste roundtrip funcione
        if len(out) >= 7 and isinstance(out[6], str):
            out[6] = out[6].replace(GLYPH_DROPDOWN, "").strip()
        return out

    def _copy_load_row(self, iid):
        if iid == PLACEHOLDER_IID:
            return None
        vals = self.loads_tree.item(iid)["values"]
        return list(vals) if vals else None

    def _copy_constraint_row(self, iid):
        if iid == PLACEHOLDER_IID:
            return None
        vals = self.constraints_tree.item(iid)["values"]
        return list(vals) if vals else None

    def _copy_surface_row(self, iid):
        if iid == PLACEHOLDER_IID:
            return None
        vals = self.surface_tree.item(iid)["values"]
        return list(vals) if vals else None

    def _paste_nodes(self, rows):
        if not self._check_pending_completion():
            return
        if rows:
            self._capture(f"pegar {len(rows)} fila(s) en Nodos")
        ok = 0
        for row in rows:
            try:
                if len(row) >= 3:
                    x, y = to_float_flex(row[1]), to_float_flex(row[2])
                elif len(row) == 2:
                    x, y = to_float_flex(row[0]), to_float_flex(row[1])
                else:
                    continue
                self.project.add_node(x, y)
                ok += 1
            except (ValueError, IndexError):
                continue
        self._refresh_nodes_tree()
        self._safe_redraw()
        self._update_status_info()
        self.main_window.set_status(f"{ok}/{len(rows)} fila(s) pegada(s).")

    def _paste_elements(self, rows):
        if not self._check_pending_completion():
            return
        if rows:
            self._capture(f"pegar {len(rows)} fila(s) en Elementos")
        ok = 0
        mat_default = next(iter(self.project.materials), "Acero")
        for row in rows:
            try:
                offset = 1 if len(row) >= 7 else 0
                n1 = int(row[offset])
                n2 = int(row[offset + 1])
                n3 = int(row[offset + 2])
                n4 = int(row[offset + 3])
                thickness = to_float_flex(row[offset + 4])
                material = (row[offset + 5].strip()
                            if offset + 5 < len(row) else mat_default)
                if material not in self.project.materials:
                    material = mat_default
                if any(n not in self.project.nodes for n in (n1, n2, n3, n4)):
                    continue
                self.project.add_element([n1, n2, n3, n4], thickness, material)
                ok += 1
            except (ValueError, IndexError):
                continue
        self._refresh_elements_tree()
        self._safe_redraw()
        self._update_status_info()
        self.main_window.set_status(f"{ok}/{len(rows)} fila(s) pegada(s).")
        # Safety net: en proyecto Q9, expandir los nuevos elementos Q4 pegados
        # (con vertices distintos validos). Idempotente.
        self._ensure_q9_consistency()

    def _paste_loads(self, rows):
        if not self._check_pending_completion():
            return
        if rows:
            self._capture(f"pegar {len(rows)} fila(s) en Cargas")
        ok = 0
        for row in rows:
            try:
                if len(row) < 3:
                    continue
                nid = int(row[0])
                fx = to_float_flex(row[1])
                fy = to_float_flex(row[2])
                if nid not in self.project.nodes:
                    continue
                self.project.set_nodal_load(nid, fx, fy)
                ok += 1
            except (ValueError, IndexError):
                continue
        self._refresh_loads_tree()
        self._safe_redraw()
        self.main_window.set_status(f"{ok}/{len(rows)} fila(s) pegada(s).")

    def _paste_constraints(self, rows):
        if not self._check_pending_completion():
            return
        if rows:
            self._capture(f"pegar {len(rows)} fila(s) en Restricciones")
        ok = 0
        for row in rows:
            try:
                if len(row) < 3:
                    continue
                nid = int(row[0])
                rx = _parse_bool(row[1])
                ry = _parse_bool(row[2])
                if nid not in self.project.nodes:
                    continue
                self.project.set_boundary_condition(nid, rx, ry)
                ok += 1
            except (ValueError, IndexError):
                continue
        self._refresh_constraints_tree()
        self._safe_redraw()
        self.main_window.set_status(f"{ok}/{len(rows)} fila(s) pegada(s).")

    def _paste_surface_loads(self, rows):
        if not self._check_pending_completion():
            return
        if rows:
            self._capture(f"pegar {len(rows)} fila(s) en Cargas Superf.")
        ok = 0
        for row in rows:
            try:
                if len(row) < 5:
                    continue
                ns = int(row[0])
                ne = int(row[1])
                qs = to_float_flex(row[2])
                qe = to_float_flex(row[3])
                ang = to_float_flex(row[4])
                if ns not in self.project.nodes or ne not in self.project.nodes:
                    continue
                self.project.add_surface_load(ns, ne, qs, qe, ang)
                ok += 1
            except (ValueError, IndexError):
                continue
        self._refresh_surface_tree()
        self._safe_redraw()
        self.main_window.set_status(f"{ok}/{len(rows)} fila(s) pegada(s).")

    # ═════════════════════════════════════════════════════════════════════
    # FILL-DOWN: get/set por columna
    # ═════════════════════════════════════════════════════════════════════


    # ═════════════════════════════════════════════════════════════════════
    # ORDEN VISUAL UNIFICADO (reales + fantasmas interleaved)
    # ═════════════════════════════════════════════════════════════════════

    def _build_loads_visual_list(self):
        """Sincroniza `_loads_visual_order` con el estado actual y
        retorna la lista de tuplas a renderizar. Preserva posiciones
        previas (clave para que el commit de un ghost no genere jump
        visual)."""
        canvas = getattr(self.main_window, "mesh_canvas", None)
        selected = getattr(canvas, "selected_nodes", set()) if canvas else set()
        project_keys = set(self.project.nodal_loads.keys())
        ghost_nids = selected - project_keys

        new_order = []
        seen = set()
        for entry in self._loads_visual_order:
            kind, nid = entry
            if (kind, nid) in seen:
                continue
            if kind == "real" and nid in project_keys:
                new_order.append(entry); seen.add((kind, nid))
            elif kind == "ghost" and nid in ghost_nids:
                new_order.append(entry); seen.add((kind, nid))
        # Reales nuevas (creadas fuera del flujo ghost — placeholder, undo, etc.)
        for nid in self.project.nodal_loads:
            if ("real", nid) not in seen:
                new_order.append(("real", nid)); seen.add(("real", nid))
        # Ghosts nuevas (canvas selecciono nodos sin carga)
        for nid in ghost_nids:
            if ("ghost", nid) not in seen:
                new_order.append(("ghost", nid)); seen.add(("ghost", nid))
        self._loads_visual_order = new_order
        return new_order

    def _build_constraints_visual_list(self):
        canvas = getattr(self.main_window, "mesh_canvas", None)
        selected = getattr(canvas, "selected_nodes", set()) if canvas else set()
        project_keys = set(self.project.boundary_conditions.keys())
        ghost_nids = selected - project_keys

        new_order = []
        seen = set()
        for entry in self._constraints_visual_order:
            kind, nid = entry
            if (kind, nid) in seen:
                continue
            if kind == "real" and nid in project_keys:
                new_order.append(entry); seen.add((kind, nid))
            elif kind == "ghost" and nid in ghost_nids:
                new_order.append(entry); seen.add((kind, nid))
        for nid in self.project.boundary_conditions:
            if ("real", nid) not in seen:
                new_order.append(("real", nid)); seen.add(("real", nid))
        for nid in ghost_nids:
            if ("ghost", nid) not in seen:
                new_order.append(("ghost", nid)); seen.add(("ghost", nid))
        self._constraints_visual_order = new_order
        return new_order

    def _build_surfaces_visual_list(self):
        """Surfaces: identidad por OBJETO (el SurfaceLoad mismo) en lugar
        de idx, porque idx se desplaza al borrar elementos del medio.
        Ghosts: identidad por edge (frozenset de 2 nodos)."""
        ghost_edges = list(self._get_pick_ghost_edges())  # set/list de frozensets
        ghost_edges_set = set(ghost_edges)
        existing_obj_ids = {id(s): s for s in self.project.surface_loads}

        new_order = []
        seen_real_obj_ids = set()
        seen_ghost_edges = set()
        for entry in self._surfaces_visual_order:
            kind, val = entry
            if kind == "real":
                obj_id = id(val)
                if obj_id in existing_obj_ids and obj_id not in seen_real_obj_ids:
                    new_order.append(entry); seen_real_obj_ids.add(obj_id)
            elif kind == "ghost":
                if val in ghost_edges_set and val not in seen_ghost_edges:
                    new_order.append(entry); seen_ghost_edges.add(val)
        for s in self.project.surface_loads:
            if id(s) not in seen_real_obj_ids:
                new_order.append(("real", s)); seen_real_obj_ids.add(id(s))
        for edge in ghost_edges:
            if edge not in seen_ghost_edges:
                new_order.append(("ghost", edge)); seen_ghost_edges.add(edge)
        self._surfaces_visual_order = new_order
        return new_order

    # ═════════════════════════════════════════════════════════════════════
    # REFRESH DE TABLAS
    # ═════════════════════════════════════════════════════════════════════

    def _refresh_all_trees(self):
        """Refresca las 5 tablas computando las clasificaciones puras
        (classify_nodes / classify_orphan_status) UNA sola vez y
        compartiendolas. Antes cada _refresh_*_tree las recomputaba ->
        classify_orphan_status corria 4x por refresh batch."""
        roles = classify_nodes(self.project)
        orphan_status = classify_orphan_status(self.project)
        self._refresh_nodes_tree(roles=roles, orphan_status=orphan_status)
        self._refresh_elements_tree()
        self._refresh_loads_tree(orphan_status=orphan_status)
        self._refresh_constraints_tree(orphan_status=orphan_status)
        self._refresh_surface_tree(orphan_status=orphan_status)

    def _refresh_nodes_tree(self, roles=None, orphan_status=None):
        self._suppress_pending_check = True
        try:
            self.nodes_tree.delete(*self.nodes_tree.get_children())
            canvas = getattr(self.main_window, "mesh_canvas", None)
            sel = getattr(canvas, "selected_nodes", set()) if canvas else set()
            if roles is None:
                roles = classify_nodes(self.project)
            if orphan_status is None:
                orphan_status = classify_orphan_status(self.project)
            for node in sorted(self.project.nodes.values(),
                               key=lambda n: n.id):
                tags = []
                if roles.get(node.id) in ("mid", "center"):
                    tags.append("auto_node")
                if orphan_status.get(node.id) == "orphan":
                    tags.append("orphan_node")
                # canvas_selected: prioridad mas alta de bg por orden de
                # tag_configure (configurado primero en _configure_row_tags).
                # Solo modifica bg; el fg cae a orphan_node/auto_node/default.
                if node.id in sel:
                    tags.append("canvas_selected")
                self.nodes_tree.insert(
                    "", END, iid=str(node.id),
                    values=(node.id, fmt(node.x, "length"),
                            fmt(node.y, "length")),
                    tags=tuple(tags),
                )
            self.nodes_tree.insert(
                "", END, iid=PLACEHOLDER_IID,
                values=(PLACEHOLDER_HINT, "", ""),
                tags=("placeholder",),
            )
            self._autoscroll_to_canvas_selected(self.nodes_tree, sel)
        finally:
            self._suppress_pending_check = False

    def _refresh_elements_tree(self):
        self._suppress_pending_check = True
        try:
            self.elements_tree.delete(*self.elements_tree.get_children())
            canvas = getattr(self.main_window, "mesh_canvas", None)
            sel = getattr(canvas, "selected_elements", set()) if canvas else set()
            for elem in sorted(self.project.elements.values(),
                               key=lambda e: e.id):
                nids = list(elem.node_ids)
                while len(nids) < 4:
                    nids.append("")
                tags = []
                if elem.id in sel:
                    tags.append("canvas_selected")
                self.elements_tree.insert(
                    "", END, iid=str(elem.id),
                    values=(elem.id, nids[0], nids[1], nids[2], nids[3],
                            fmt(elem.thickness, "length"),
                            f"{elem.material_name}{GLYPH_DROPDOWN}"),
                    tags=tuple(tags),
                )
            self.elements_tree.insert(
                "", END, iid=PLACEHOLDER_IID,
                values=(PLACEHOLDER_HINT, "", "", "", "", "", ""),
                tags=("placeholder",),
            )
            self._autoscroll_to_canvas_selected(self.elements_tree, sel)
        finally:
            self._suppress_pending_check = False

    def _refresh_loads_tree(self, orphan_status=None):
        self._suppress_pending_check = True
        try:
            self.loads_tree.delete(*self.loads_tree.get_children())
            canvas = getattr(self.main_window, "mesh_canvas", None)
            sel_loads = getattr(canvas, "selected_loads", set()) if canvas else set()
            if orphan_status is None:
                orphan_status = classify_orphan_status(self.project)
            # Render via orden visual unificado (reales + ghosts mezclados
            # segun la posicion previa). Asi un ghost commit muta la entry
            # in-place y la nueva fila real aparece en el mismo slot — sin
            # jump visual al editar tras click sobre fantasma.
            for kind, nid in self._build_loads_visual_list():
                if kind == "real":
                    load = self.project.nodal_loads[nid]
                    tags = []
                    # Nodo huerfano (no esta en ningun elemento): la carga
                    # no contribuye al analisis, tintar naranja.
                    if orphan_status.get(load.node_id) == "orphan":
                        tags.append("orphan_node")
                    if load.node_id in sel_loads:
                        tags.append("canvas_selected")
                    self.loads_tree.insert(
                        "", END, iid=str(load.node_id),
                        values=(load.node_id, fmt(load.fx, "force"),
                                fmt(load.fy, "force")),
                        tags=tuple(tags),
                    )
                else:  # ghost: nodo seleccionado sin carga existente
                    self.loads_tree.insert(
                        "", END, iid=f"__ghost__{nid}",
                        values=(nid, "0", "0"),
                        tags=("pending_pick",),
                    )
            self.loads_tree.insert(
                "", END, iid=PLACEHOLDER_IID,
                values=(PLACEHOLDER_HINT, "", ""),
                tags=("placeholder",),
            )
            self._autoscroll_to_canvas_selected(self.loads_tree, sel_loads)
        finally:
            self._suppress_pending_check = False

    def _refresh_constraints_tree(self, orphan_status=None):
        self._suppress_pending_check = True
        try:
            self.constraints_tree.delete(*self.constraints_tree.get_children())
            canvas = getattr(self.main_window, "mesh_canvas", None)
            sel_bcs = getattr(canvas, "selected_constraints", set()) if canvas else set()
            if orphan_status is None:
                orphan_status = classify_orphan_status(self.project)
            # Orden visual unificado (reales + ghosts mezclados): mismo
            # patron que loads — preserva slot del ghost al commitear.
            for kind, nid in self._build_constraints_visual_list():
                if kind == "real":
                    bc = self.project.boundary_conditions[nid]
                    rx = GLYPH_ON if bc.restrain_x else GLYPH_OFF
                    ry = GLYPH_ON if bc.restrain_y else GLYPH_OFF
                    tags = []
                    # BC sobre nodo huerfano: DOF colgante restringido —
                    # error critico (K_red singular).
                    if orphan_status.get(bc.node_id) == "orphan":
                        tags.append("orphan_node")
                    if bc.node_id in sel_bcs:
                        tags.append("canvas_selected")
                    self.constraints_tree.insert(
                        "", END, iid=str(bc.node_id),
                        values=(bc.node_id, rx, ry),
                        tags=tuple(tags),
                    )
                else:  # ghost: default empotramiento (restrain_x=restrain_y=True)
                    self.constraints_tree.insert(
                        "", END, iid=f"__ghost__{nid}",
                        values=(nid, GLYPH_ON, GLYPH_ON),
                        tags=("pending_pick",),
                    )
            self.constraints_tree.insert(
                "", END, iid=PLACEHOLDER_IID,
                values=(PLACEHOLDER_HINT, "", ""),
                tags=("placeholder",),
            )
            self._autoscroll_to_canvas_selected(self.constraints_tree, sel_bcs)
        finally:
            self._suppress_pending_check = False

    def _refresh_surface_tree(self, orphan_status=None):
        self._suppress_pending_check = True
        try:
            self.surface_tree.delete(*self.surface_tree.get_children())
            canvas = getattr(self.main_window, "mesh_canvas", None)
            sel_surf = getattr(canvas, "selected_surfaces", set()) if canvas else set()
            if orphan_status is None:
                orphan_status = classify_orphan_status(self.project)
            # Mapa obj_id -> idx actual para resolver la posicion del
            # SurfaceLoad en project.surface_loads (idx puede haber
            # cambiado tras inserciones/borrados).
            obj_to_idx = {id(s): i for i, s in enumerate(self.project.surface_loads)}
            # Orden visual unificado (reales + ghosts mezclados): preserva
            # slot del ghost al commitear, aun tras refreshes posteriores.
            for kind, val in self._build_surfaces_visual_list():
                if kind == "real":
                    sl = val
                    idx = obj_to_idx[id(sl)]
                    tags = []
                    # Surface load con cualquier extremo huerfano: la carga
                    # no se aplica correctamente -> tintar fila completa.
                    if (orphan_status.get(sl.node_start) == "orphan"
                            or orphan_status.get(sl.node_end) == "orphan"):
                        tags.append("orphan_node")
                    if idx in sel_surf:
                        tags.append("canvas_selected")
                    self.surface_tree.insert(
                        "", END, iid=str(idx),
                        values=(sl.node_start, sl.node_end,
                                fmt(sl.q_start, "force"),
                                fmt(sl.q_end, "force"),
                                fmt(sl.angle, "angle")),
                        tags=tuple(tags),
                    )
                else:  # ghost: arista seleccionada sin surface existente
                    edge = val
                    ns, ne = sorted(edge)
                    self.surface_tree.insert(
                        "", END, iid=f"__ghost__{ns}_{ne}",
                        values=(ns, ne, "0", "0", "0"),
                        tags=("pending_pick",),
                    )
            self.surface_tree.insert(
                "", END, iid=PLACEHOLDER_IID,
                values=(PLACEHOLDER_HINT, "", "", "", ""),
                tags=("placeholder",),
            )
            self._autoscroll_to_canvas_selected(self.surface_tree, sel_surf)
        finally:
            self._suppress_pending_check = False

    def refresh(self):
        """Refresca toda la pestana de pre-proceso (incluye headers)."""
        self.update_unit_headers()
        self._refresh_all_trees()


    # ═════════════════════════════════════════════════════════════════════
    # HELPERS INTERNOS
    # ═════════════════════════════════════════════════════════════════════

    def _is_pending(self, iid):
        return bool(self._pending_new) and self._pending_new.get("iid") == iid

    def _is_done(self, ci):
        return bool(self._pending_new) and ci in self._pending_new.get("completed", set())

    def _after_create_select(self, tree, iid, col):
        try:
            tree.see(iid)
            tree.selection_set(iid)
            tree.focus(iid)
        except tk.TclError:
            pass

    def _safe_redraw(self):
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is not None and hasattr(canvas, "redraw"):
            try:
                canvas.redraw()
            except Exception:
                pass

    # ─── Filas fantasma de pick desde canvas ────────────────────────────

    def _get_pick_ghost_node_ids(self, kind):
        """Retorna sorted list de node_ids seleccionados en canvas que
        NO tienen aun el item correspondiente en el modelo. Usado para
        decidir qué fantasmas insertar en el spreadsheet.
        kind: "load" o "constraint".
        """
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None or not getattr(canvas, "selected_nodes", None):
            return []
        if kind == "load":
            existing = set(self.project.nodal_loads.keys())
        elif kind == "constraint":
            existing = set(self.project.boundary_conditions.keys())
        else:
            return []
        ghosts = [nid for nid in canvas.selected_nodes
                  if nid in self.project.nodes and nid not in existing]
        return sorted(ghosts)

    def _get_pick_ghost_edges(self):
        """Retorna lista de aristas (frozenset) seleccionadas en canvas
        que NO tienen surface existente. Para fantasmas de Carg. Superf."""
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None or not getattr(canvas, "selected_edges", None):
            return []
        existing_edges = {frozenset({sl.node_start, sl.node_end})
                          for sl in self.project.surface_loads}
        ghosts = [edge for edge in canvas.selected_edges
                  if edge not in existing_edges]
        return sorted(ghosts, key=lambda e: tuple(sorted(e)))

    def _commit_load_ghost(self, node_id):
        """Confirma la fila fantasma de carga: crea NodalLoad(nid, 0, 0)
        y lo agrega al modelo. El usuario edita Fx/Fy en el spreadsheet."""
        if node_id not in self.project.nodes:
            return
        if node_id in self.project.nodal_loads:
            return
        self._capture(f"crear carga en nodo {node_id} (pick canvas)")
        self.project.set_nodal_load(node_id, 0.0, 0.0)
        # Mutar visual_order: la entry ('ghost', nid) se vuelve ('real', nid)
        # PRESERVANDO posicion. Se hace antes del refresh para que el
        # render use el nuevo orden — la fila real aparece exactamente
        # donde estaba la fantasma (sin jump visual).
        for i, entry in enumerate(self._loads_visual_order):
            if entry == ("ghost", node_id):
                self._loads_visual_order[i] = ("real", node_id)
                break
        # Quitar el nodo del set seleccionado del canvas (tambien para
        # que la fantasma desaparezca de otras vistas y la fila real sea
        # highlighteable).
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is not None:
            canvas.selected_nodes.discard(node_id)
            canvas._emit_selection_changed()
        self._refresh_loads_tree()
        self._safe_redraw()
        self.main_window.set_status(
            f"Carga en nodo {node_id} creada (Fx=Fy=0). "
            f"Edita los valores en el spreadsheet."
        )
        self.main_window._update_title()

    def _commit_constraint_ghost(self, node_id):
        """Confirma la fila fantasma de restriccion: crea BC(nid, True, True)
        (empotramiento). El usuario edita los flags despues."""
        if node_id not in self.project.nodes:
            return
        if node_id in self.project.boundary_conditions:
            return
        self._capture(f"crear restriccion en nodo {node_id} (pick canvas)")
        self.project.set_boundary_condition(node_id, True, True)
        # Mutar visual_order in-place (mismo patron que en loads).
        for i, entry in enumerate(self._constraints_visual_order):
            if entry == ("ghost", node_id):
                self._constraints_visual_order[i] = ("real", node_id)
                break
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is not None:
            canvas.selected_nodes.discard(node_id)
            canvas._emit_selection_changed()
        self._refresh_constraints_tree()
        self._safe_redraw()
        self.main_window.set_status(
            f"Restriccion en nodo {node_id} creada (empotramiento). "
            f"Edita los flags X/Y en el spreadsheet."
        )
        self.main_window._update_title()

    def _commit_surface_ghost(self, edge):
        """Confirma la fila fantasma de carga superficial: crea
        SurfaceLoad(node_start, node_end, q=0, q=0, angle=0). El usuario
        edita las magnitudes despues."""
        n1, n2 = sorted(edge)
        if n1 not in self.project.nodes or n2 not in self.project.nodes:
            return
        # Verificar que no exista ya (defensivo, _get_pick_ghost_edges ya filtra)
        for sl in self.project.surface_loads:
            if frozenset({sl.node_start, sl.node_end}) == frozenset(edge):
                return
        self._capture(
            f"crear carga superficial arista {n1}-{n2} (pick canvas)"
        )
        self.project.add_surface_load(n1, n2, 0.0, 0.0, 0.0)
        # Mutar visual_order: la entry ('ghost', edge) se reemplaza por
        # ('real', surface_load_obj) recien appendeado al project.
        # Identidad por OBJETO (no idx) porque idx se desplaza si se
        # borran surface loads del medio.
        new_obj = self.project.surface_loads[-1]
        edge_fs = frozenset(edge)
        for i, entry in enumerate(self._surfaces_visual_order):
            if entry[0] == "ghost" and entry[1] == edge_fs:
                self._surfaces_visual_order[i] = ("real", new_obj)
                break
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is not None:
            canvas.selected_edges.discard(edge_fs)
            canvas._emit_selection_changed()
        self._refresh_surface_tree()
        self._safe_redraw()
        self.main_window.set_status(
            f"Carga superficial en arista {n1}-{n2} creada (q=0). "
            f"Edita q_start/q_end/angle en el spreadsheet."
        )
        self.main_window._update_title()

    def _on_canvas_selection_changed(self, _selection_dict):
        """Callback registrado en `mesh_canvas.on_selection_changed`.

        Dos modos:

        - **Canvas -> spreadsheet** (`_syncing_to_canvas == False`):
          reconstruye los 5 trees con `_refresh_*_tree`. Cada refresh
          aplica el tag `canvas_selected` a las filas marcadas y hace
          auto-scroll a la primera fila visible.

        - **Spreadsheet -> canvas** (`_syncing_to_canvas == True`,
          guard activado por los `_on_*_select` antes de propagar):
          NO se puede reconstruir los trees porque eso destruiria la
          seleccion nativa de Tk (`tree.selection()`) que el usuario
          acaba de hacer y que es la fuente de verdad para `Delete`,
          copy/paste y otras operaciones. En cambio, sincronizamos
          los tags `canvas_selected` IN-PLACE via
          `_apply_canvas_selected_tags`, que solo togglea tags sin
          rebuild ni `<<TreeviewSelect>>` rebotado. Asi se eliminan
          tags stale (la fila A previa ya no aparece marcada) y se
          mantiene el highlight cruzado en otros trees (e.g., al
          clickear una carga, el nodo asociado se tinta tambien).

        Razon historica del guard: `tree.selection_set` desde un
        rebuild dispara `<<TreeviewSelect>>` ASINCRONICAMENTE, despues
        del callback. Cuando llega, `_syncing_from_canvas` ya esta
        OFF, el handler se ejecuta, propaga al canvas, y rebota ->
        degradacion que congela la GUI. Por eso `_apply_canvas_selected_tags`
        usa `tree.item(iid, tags=...)` que NO dispara el virtualevent.
        """
        canvas = getattr(self.main_window, "mesh_canvas", None)
        if canvas is None:
            return

        if self._syncing_to_canvas:
            # Sync in-place: no rebuild, preserva seleccion nativa Tk.
            self._apply_canvas_selected_tags(
                self.nodes_tree, canvas.selected_nodes)
            self._apply_canvas_selected_tags(
                self.elements_tree, canvas.selected_elements)
            self._apply_canvas_selected_tags(
                self.loads_tree, canvas.selected_loads)
            self._apply_canvas_selected_tags(
                self.constraints_tree, canvas.selected_constraints)
            self._apply_canvas_selected_tags(
                self.surface_tree, canvas.selected_surfaces)
            # Tambien refrescar el panel de modulos educativos.
            if getattr(self, "_edu_panel", None) is not None:
                try:
                    elems = canvas.selected_elements
                    eid = next(iter(elems)) if len(elems) == 1 else None
                    self._edu_panel.update_selection(eid)
                except Exception:
                    pass
            return

        # Guard: si la seleccion no cambio (mismo conjunto de ids en todos los
        # tipos), no reconstruir los 5 trees. El rebuild es O(N) en filas y
        # domina el tiempo percibido en mallas grandes con seleccion repetida.
        sel_key = (
            frozenset(canvas.selected_nodes),
            frozenset(canvas.selected_elements),
            frozenset(canvas.selected_loads),
            frozenset(canvas.selected_constraints),
            frozenset(canvas.selected_surfaces),
        )
        if sel_key == self._last_canvas_sel:
            return
        self._last_canvas_sel = sel_key

        self._syncing_from_canvas = True
        try:
            self._refresh_all_trees()
        finally:
            self._syncing_from_canvas = False

        # Sincronizar panel de modulos educativos con la seleccion.
        if getattr(self, "_edu_panel", None) is not None:
            try:
                elems = canvas.selected_elements
                elem_id = next(iter(elems)) if len(elems) == 1 else None
                self._edu_panel.update_selection(elem_id)
            except Exception:
                pass

    def _apply_canvas_selected_tags(self, tree, ids):
        """Togglea el tag `canvas_selected` en filas existentes sin
        reconstruirlas. Uso: sync spreadsheet -> canvas para evitar
        que la seleccion nativa de Tk se pierda con un rebuild.

        `ids` es un iterable de enteros (node_ids, elem_ids o indices
        de surface_loads). Las filas placeholder (`__new__`) y fantasma
        (`__ghost__*`) tienen iids no-numericos, asi que naturalmente
        nunca matchean y conservan su tag propio (`placeholder` /
        `pending_pick`). `tree.item(iid, tags=...)` NO dispara
        `<<TreeviewSelect>>`, por lo que no hay rebote al callback.
        """
        ids_str = {str(i) for i in ids}
        for iid in tree.get_children():
            tags = list(tree.item(iid, "tags") or [])
            has = "canvas_selected" in tags
            wants = iid in ids_str
            if wants and not has:
                tags.append("canvas_selected")
                tree.item(iid, tags=tuple(tags))
            elif not wants and has:
                tags.remove("canvas_selected")
                tree.item(iid, tags=tuple(tags))

    def _on_tree_button1(self, tree, event):
        """Single-click en cualquier Treeview: si la fila clickeada es
        una fila fantasma (iid empieza con __ghost__), la confirma con
        defaults. Si el click cayo en una columna de valor numerico
        (Fx/Fy en cargas, q_start/q_end/angle en surface), ademas abre
        el editor sobre la fila real recien creada para que el usuario
        tipee el valor sin doble-click. Sino, deja que el comportamiento
        normal de seleccion continue."""
        iid = tree.identify_row(event.y)
        if not iid or not iid.startswith("__ghost__"):
            return  # comportamiento normal
        col = tree.identify_column(event.x) or "#1"
        try:
            ci = int(col.replace("#", "")) - 1
        except (ValueError, AttributeError):
            ci = 0
        # Despachar segun el tree
        if tree is self.loads_tree:
            try:
                nid = int(iid[len("__ghost__"):])
            except ValueError:
                return
            self._commit_load_ghost(nid)
            # Fx (ci=1) o Fy (ci=2): abrir editor sobre la fila real.
            if ci in (1, 2):
                new_iid = str(nid)
                if new_iid in tree.get_children():
                    self._edit_load_cell(new_iid, col, ci)
        elif tree is self.constraints_tree:
            try:
                nid = int(iid[len("__ghost__"):])
            except ValueError:
                return
            self._commit_constraint_ghost(nid)
            # X (ci=1) e Y (ci=2) son toggles: el commit deja empotramiento
            # (rx=ry=True). Para invertir un eje, doble-click sobre la fila
            # real lo togglea — patron unificado con todas las demas tablas.
        elif tree is self.surface_tree:
            # iid = "__ghost__N1_N2"
            suffix = iid[len("__ghost__"):]
            try:
                ns, ne = (int(p) for p in suffix.split("_"))
            except (ValueError, AttributeError):
                return
            self._commit_surface_ghost(frozenset({ns, ne}))
            # q_start (ci=2), q_end (ci=3) o angle (ci=4): abrir editor
            # sobre la fila recien creada (idx = ultimo append).
            if ci in (2, 3, 4):
                new_idx = len(self.project.surface_loads) - 1
                if new_idx >= 0:
                    new_iid = str(new_idx)
                    if new_iid in tree.get_children():
                        sl = self.project.surface_loads[new_idx]
                        self._edit_surface_cell(new_iid, col, ci, sl)
        return "break"  # evita la seleccion del row ghost

    def _autoscroll_to_canvas_selected(self, tree, ids):
        """Scrolla el Treeview a la primera fila marcada con tag
        canvas_selected. NO modifica `tree.selection()` (eso disparaba
        virtualevents async y causaba congelamiento -- ver CLAUDE.md
        'Sync asimetrico')."""
        if not ids:
            return
        # Probar el id mas chico primero (representa la primera fila
        # ordenada). Para idx (surfaces) son enteros; para nodos/elementos
        # tambien. Convertir a str para matchear iids.
        try:
            first = str(min(ids))
        except (TypeError, ValueError):
            return
        try:
            if first in tree.get_children():
                tree.see(first)
        except tk.TclError:
            pass

    def _update_status_info(self):
        if hasattr(self.main_window, "_update_status_info"):
            try:
                self.main_window._update_status_info()
            except Exception:
                pass

    # Navegacion teclado: resuelve siguiente celda editable. Devuelve
    # (next_iid, next_ci) o None si no hay siguiente. PLACEHOLDER_IID se
    # devuelve sin filtrar (el caller decide si triggear creacion).


    # ─── Atajos de teclado: hint y edicion de celda activa ──────────────


