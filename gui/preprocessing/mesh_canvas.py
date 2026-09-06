"""
MeshCanvas: Canvas interactivo compartido para visualizar la malla FEM.
Soporta zoom, pan, nodos, elementos, cargas, restricciones,
visualizacion de resultados con gradiente suave (jet) e isolineas.
"""

import math
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import numpy as np

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from gui.preprocessing.canvas_raster import (
    element_grid_points, element_grid_values, grid_triangles,
    marching_squares_batch, rasterize_triangles,
)

# Padding del raster del gradient como fraccion del viewport visible.
# Al rasterizar 50% extra por lado, el bitmap final es 2x ancho * 2x alto
# = 4x pixeles del viewport. Permite que el pan se sienta instantaneo
# sin re-rasterizar — el bitmap movido por canvas.move tiene tela de
# sobra antes de mostrar bordes negros. Costo: ~4x RAM por bitmap.
_GRADIENT_PAD_FRAC = 0.5


from config.settings import (
    NUMERICAL_TOLERANCE,
    CANVAS_BG_COLOR, CANVAS_GRID_COLOR, CANVAS_NODE_COLOR,
    CANVAS_ELEMENT_COLOR, CANVAS_LOAD_COLOR, CANVAS_CONSTRAINT_COLOR,
    CANVAS_SELECTED_COLOR, CANVAS_NODE_RADIUS, CANVAS_FONT_SIZE,
    CANVAS_NODE_MID_COLOR, CANVAS_NODE_CENTER_COLOR, CANVAS_NODE_MID_RADIUS,
    CANVAS_NODE_ORPHAN_COLOR, CANVAS_GHOST_COLOR,
    CANVAS_NODE_INNER_CORNER, CANVAS_NODE_INNER_MID, CANVAS_NODE_INNER_CENTER,
    CANVAS_NODE_INNER_ORPHAN, CANVAS_NODE_OUTLINE,
    CANVAS_CONSTRAINT_FIXED_FILL, CANVAS_CONSTRAINT_ROLLER_FILL,
    CANVAS_SELECTED_HALO_COLOR, CANVAS_SELECTED_FILL_COLOR,
    CANVAS_HOVER_COLOR, CANVAS_BOUNDARY_COLOR,
    CANVAS_BOUNDARY_MIN_ELEMENTS, CANVAS_FOCUS_MIN_ELEMENTS,
    DECORATION_SCALE_MIN_FACTOR, DECORATION_SCALE_MAX_FACTOR,
    DECIMALS_LENGTH, DECIMALS_FORCE, DECIMALS_STRESS, fmt,
    SHADOW_LOAD, SHADOW_SURFACE, SHADOW_CONSTRAINT, LABEL_BG, LABEL_FG,
    FONT_MONO_SMALL, TEXT_MUTED_FG,
    CANVAS_AXIS_X_COLOR, CANVAS_AXIS_Y_COLOR, CANVAS_DEFORM_GHOST_COLOR,
    CANVAS_ELEM_LABEL_ON_FIELD_COLOR, CANVAS_ELEM_LABEL_COLOR,
    CANVAS_COLORBAR_BORDER_COLOR,
)
from config.colormaps import (
    JET_LUT, t_to_hex, value_to_hex,
    is_diverging_range, symmetric_bounds,
)
from models.mesh_utils import (
    classify_nodes, classify_orphan_status, auto_expand_if_q9,
    median_edge_length, boundary_edges, focus_keep_sets,
)
from gui.preprocessing.canvas_logic import (
    lod_level, bbox_visible, point_visible, label_visible_for_item,
    label_globally_visible,
)
# Margen de culling = padding del raster del gradient (coherencia: el area
# que NO se rasteriza coincide con la que no se dibuja en vectores).
_CULL_MARGIN_FRAC = _GRADIENT_PAD_FRAC


class MeshCanvas(ttk.Frame):
    """Canvas interactivo compartido para la malla FEM con resultados."""

    def __init__(self, parent, project, main_window):
        super().__init__(parent)
        self.project = project
        self.main_window = main_window

        # Estado de vista
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        # Escala de referencia para el reescalado de decoraciones con el zoom
        # (proporcional acotado). Se fija en cada fit_view: con scale ==
        # _reference_scale el factor es 1.0 (decoraciones a tamano base). None
        # hasta el primer fit_view -> factor 1.0 por defecto. Ver
        # _decoration_factor.
        self._reference_scale = None
        # ─── Highlights "single" (compat) ──────────────────────────────
        # Estos atributos mantienen el "ultimo seleccionado individual"
        # para retrocompat con codigo que asume single-select. Su valor
        # es el unico elemento del set correspondiente cuando hay
        # exactamente uno seleccionado, o None si el set esta vacio o
        # tiene >1. Para el uso multi-select consultar `selected_*`.
        self.highlighted_node = None
        self.highlighted_element = None
        self.highlighted_load = None        # node_id
        self.highlighted_constraint = None  # node_id
        self.highlighted_surface = None     # idx en project.surface_loads
        # ─── Selecciones multi (set-based) ─────────────────────────────
        # Sets que sostienen TODOS los items seleccionados de cada tipo.
        # El render itera estos sets. Las modificaciones se hacen via
        # `select_*` / `add_to_selection_*` / `clear_selection`. Los
        # callbacks `on_selection_changed` notifican cambios.
        self.selected_nodes = set()
        self.selected_elements = set()
        # Aristas potenciales: pares de corner-node-ids representados
        # como `frozenset({n1, n2})`. La direccion del SurfaceLoad final
        # la define el commit del fantasma; aqui el orden no importa.
        self.selected_edges = set()
        self.selected_loads = set()         # set[int] de node_ids
        self.selected_constraints = set()   # set[int] de node_ids
        self.selected_surfaces = set()      # set[int] de idx en surface_loads
        # Track del ultimo nodo clickeado para Shift+Click range select.
        self._last_node_anchor = None

        # Callback de borrado desde canvas (tecla Supr/Delete sobre item
        # actualmente highlighted). El pre_tab lo registra en
        # _wire_canvas_callbacks. Recibe (kind, target_id) donde kind in
        # {"node", "element", "load", "constraint", "surface"} y se invoca
        # DESPUES de que el modelo ya fue mutado.
        self.on_canvas_delete = None      # callable(kind, target_id)
        # Callback unificado: dispara cada vez que CUALQUIER set de
        # seleccion cambia. La firma es `callable(selection_dict)` donde
        # selection_dict = {"nodes": set, "elements": set, "edges": set,
        #                   "loads": set, "constraints": set,
        #                   "surfaces": set}. El pre_tab lo usa para
        # reconstruir filas fantasma de las sub-pestañas.
        self.on_selection_changed = None  # callable(dict)

        # Estado de resultados
        self.result_values = None
        self.result_label = ""
        self.result_unit = ""        # unidad del resultado activo (colorbar)
        self.result_vmin = 0.0
        self.result_vmax = 1.0

        # Deformada
        self.show_deformed = False
        self.deform_scale = 0.0
        self.displacements = None

        # Opciones de dibujo (capas toggleables desde el menu del titulo).
        self.show_loads = True
        self.show_constraints = True
        self.show_mesh_edges = True
        self.show_nodes = True
        self.show_grid = True
        # Snapshot de capas previo a "Vista limpia" (para restaurar al toggle).
        self._clean_view_prev = None
        # ─── Visualizacion progresiva (auditoria UX 2026-05) ───────────────
        # Numeracion bajo demanda: modo por categoria (reemplaza a los ex
        # flags booleanos show_node_labels/show_elem_labels). "auto" = visible
        # solo en zoom cercano (LOD near) + siempre en el item seleccionado;
        # "always" = siempre; "never" = nunca. Default "auto": las mallas
        # chicas (<= LOD_MIN_ELEMENTS_FOR_GATING) se ven como antes (todo
        # numerado) y solo las densas se descongestionan hasta hacer zoom.
        self.node_label_mode = "auto"
        self.elem_label_mode = "auto"
        # Atenuacion de contexto al seleccionar (focus-and-context): "auto" =
        # se activa solo en mallas grandes con seleccion; "on"/"off" fuerzan.
        self.focus_mode = "auto"
        # Realce de la silueta del dominio (aristas de contorno mas marcadas).
        self.boundary_emphasis = True
        # Estado del realce de hover (id del elemento bajo el cursor con su
        # outline dibujado en la capa "hover"). None = sin hover activo.
        self._hover_highlight_eid = None
        # ─── Colormap activo (jet no-negativo / coolwarm con signo) ────────
        self._active_lut = JET_LUT
        self.result_diverging = False
        # Geometria "fantasma": cuando un modulo overlay lo activa (M0), la
        # malla base se dibuja atenuada (gris tenue, sin etiquetas) para que la
        # capa del modulo sea la protagonista. El modulo lo resetea al cerrar.
        self.ghost_geometry = False

        # Gradiente e isolineas
        self._gradient_photo = None  # referencia PIL para evitar GC
        # Cache de la imagen rasterizada del contorno. Key SIN offset_x/y:
        # el pan no invalida la cache (la imagen se reposiciona via el
        # delta `_gradient_photo_offset`). Solo invalida cuando cambia el
        # resultado, vmin/vmax, w/h, scale, deform o el modo n (3 vs 6).
        self._gradient_cache_key = None
        # Offset del viewport al momento de rasterizar el gradient. Al
        # reutilizar la PhotoImage tras paneos, el create_image se coloca
        # en (offset_actual - offset_raster) para que la imagen quede
        # alineada con la malla. Permite que el cache sobreviva al pan.
        self._gradient_photo_offset = (0.0, 0.0)
        # Padding (pad_x, pad_y) con el que se rasterizo el bitmap actual.
        # El raster es mas grande que el viewport para que el pan tenga
        # "tela de sobra" antes de mostrar bordes negros (truco SAP2000/
        # ANSYS/ParaView para que el pan se sienta instantaneo).
        self._gradient_photo_pad = (0, 0)
        # PIL Image original (pre-PhotoImage) del raster. Mantenerlo
        # permite hacer Image.resize() durante zoom suave (sin re-
        # rasterizar todo el campo desde cero). El bitmap se escala con
        # PIL en C — mucho mas rapido que iterar elementos y triangulos.
        self._gradient_pil_image = None
        # Scale al que se rasterizo el bitmap (para calcular el factor de
        # resize durante zoom interactivo).
        self._gradient_photo_scale = 1.0
        # PhotoImage del bitmap escalado durante zoom interactivo. Se
        # mantiene como atributo separado del _gradient_photo "verdadero"
        # para no perder la referencia (Tk libera la imagen si no hay
        # ref viva en Python).
        self._gradient_zoom_photo = None
        self.show_isolines = False
        self.isoline_count = 10

        # ─── Estado de interaccion (pan/zoom/resize) ────────────────────
        # Cuando _interacting=True, el render baja la resolucion del
        # gradient (n=3 vs n=6) y skip-ea isolineas — desplaza el costo
        # caro al "tick final" en after_idle/after(150ms), no a cada
        # evento. Sin esto, una rueda de mouse a 60Hz disparaba 60
        # rasterizaciones completas/seg en mallas medianas.
        self._interacting = False
        # ID del after() pendiente que marca el "fin de interaccion" y
        # lanza el redraw final de alta calidad. Cada nuevo evento de
        # zoom/resize lo reprograma para coalescer todos los ticks de
        # una sesion de interaccion en un solo redraw.
        self._interaction_end_after_id = None
        # ID de un redraw throttled pendiente (after_idle). Evita encolar
        # multiples redraws cuando varios eventos llegan en el mismo
        # frame (ej. <Configure> en serie durante un resize).
        self._redraw_pending = False
        # Flag de sesion de pan activa (entre ButtonPress y ButtonRelease
        # de Button-2/3). Usado por _on_pan_release para disparar el
        # redraw final que re-rasteriza el gradient con el offset nuevo.
        self._panning = False

        # ─── Capa educativa (overlay layers) ────────────────────────────
        # Lista de callables (canvas) -> None que se ejecutan al final de
        # redraw(), DESPUES del dibujo principal. Cada modulo educativo en
        # modo overlay registra su propia capa via add_overlay_layer() y la
        # quita en cleanup. Aisla la logica didactica (glow Gauss, cruces
        # principales, particle rain) sin contaminar el core del canvas.
        self._overlay_layers = []
        # ─── Click consumers (modulos educativos) ──────────────────────
        # Lista de callables (event) -> bool. Se invocan al INICIO de
        # _on_click, en orden de registro. Si alguno retorna True, el
        # hit-test estandar del canvas se OMITE — el consumer ya manejo
        # el click (ej. snap a punto Gauss, inicio de drag de nodo).
        # Patron uniforme para todos los modulos overlay con interaccion
        # de click: evita que select_element() dispare "second-click
        # deselects" cuando el alumno clickea sobre un Gauss del
        # elemento ya seleccionado por el modulo.
        self._click_consumers = []
        # Callback opcional: callable(elem_id|None) — notifica cuando el
        # cursor pasa sobre un elemento distinto. Lo usa M0 para mostrar el
        # radar flotante anclado al cursor.
        self.on_hover_element = None
        self._hover_elem_id = None

        # Modo "consulta interactiva" del Post-Proceso. Cuando esta activo,
        # gui/postprocessing/probe_overlay.py bindea sus propios handlers
        # con add="+"; el _on_click hace early-return para no crear
        # selecciones (el patron es espejo de draw_mode_active).
        self.probe_mode_active = False

        # Modo de contorno CRUDO (esfuerzos discontinuos entre elementos).
        # Cuando `element_result_grid` no es None, el render del filled
        # gradient usa estos valores per-element pre-computados en lugar
        # de `result_values` (nodal promediado). Materializa visualmente
        # la naturaleza C0 del MEF Galerkin: ε = ∂u/∂x salta en bordes,
        # asi que σ tambien.
        # Formato: {elem_id: ndarray(n+1, n+1)} donde grid[i,j] es el
        # valor en (xi=-1+2i/n, eta=-1+2j/n) ya evaluado con
        # σ = D·B(ξ,η)·u_e (no es interpolacion lineal -- es el campo
        # real del MEF). post_tab._compute_raw_grid lo arma.
        self.element_result_grid = None

        # ─── Toolbar ────────────────────────────────────────────────────
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, padx=2, pady=(2, 0))

        # Titulo del viewport = menu de visualizacion (patron Rhino: el titulo
        # del viewport ES el menu). Ocupa el espacio prime-izquierdo, muestra el
        # glifo de la fase activa (set_phase lo actualiza: 📐 Pre / ⚙ Proc /
        # 📊 Post) y al clickearse abre los overrides de display. Reemplaza al
        # ex-label "Modelo MEF" + ex-menubutton "Vista" (dos controles -> uno;
        # ademas elimina el "Vista" duplicado que chocaba con "Ajustar Vista").
        # Estado de capas (visibilidad). show_loads / show_constraints ya
        # existian y condicionaban el redraw; sumamos nodos y cuadricula.
        # 'Elementos' NO es toggleable a proposito (ocultar la malla deja
        # nodos/cargas flotando — confuso). El menu del titulo los expone.
        self._phase = "pre"
        self._title_mb = ttk.Menubutton(
            toolbar, text="📐  Modelo MEF", bootstyle="secondary-outline",
        )
        self._title_mb.pack(side=LEFT, padx=3)
        self._build_view_menu(self._title_mb)

        # Barra minimalista: titulo-menu (izq) + readout de coords (der).
        # 'Ajustar' vive DENTRO del menu (no como boton). 'Limpiar Resultados'
        # se elimino — volver a Pre/Proc ya llama clear_results_overlay() (ver
        # MainWindow._on_tab_changed), asi que era redundante con la navegacion.
        self.coord_label = ttk.Label(
            toolbar, text="x: --  y: --",
            font=("Consolas", 8), foreground=TEXT_MUTED_FG,
        )
        self.coord_label.pack(side=RIGHT, padx=10)

        # ─── Canvas ─────────────────────────────────────────────────────
        # takefocus=1 para que las teclas Delete/BackSpace lleguen al canvas
        # cuando el usuario clickea o pasa el mouse sobre el (focus_set en
        # <Enter>). Sin esto, los KeyPress se enrutan al widget que tenga
        # focus actualmente (probablemente un spreadsheet).
        self.canvas = tk.Canvas(
            self, bg=CANVAS_BG_COLOR, highlightthickness=0, takefocus=1,
        )
        self.canvas.pack(fill=BOTH, expand=YES, padx=2, pady=2)

        # ─── Eventos ────────────────────────────────────────────────────
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_release)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start)
        self.canvas.bind("<B3-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_release)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self._on_click)
        # Borrado bidireccional desde canvas. Tk Canvas no recibe focus
        # automaticamente -> bindeamos focus_set en hover para que
        # Delete/BackSpace funcionen sin click previo. Funciona en
        # Windows/Linux; en macOS BackSpace es la tecla "Delete" estandar.
        self.canvas.bind("<Enter>", lambda _e: self.canvas.focus_set())
        # Al salir del canvas, limpiar el realce de hover (pre-seleccion).
        self.canvas.bind("<Leave>", self._on_canvas_leave)
        self.canvas.bind("<KeyPress-Delete>", self._on_delete_key)
        self.canvas.bind("<KeyPress-BackSpace>", self._on_delete_key)
        # Escape cancela el elemento parcial cuando el modo dibujo esta
        # activo (sin entry abierto). Si no hay nada parcial, desactiva
        # el modo. Solo se enruta si el canvas tiene focus.
        self.canvas.bind("<KeyPress-Escape>", self._on_draw_escape)

        self._pan_start_x = 0
        self._pan_start_y = 0

        # ─── Estado modo dibujo de elementos ────────────────────────────
        # Lista de tuples (snapped_node_id|None, x_world, y_world).
        # Si snapped_node_id es int, el punto reusa un nodo existente y
        # x/y son las coords de ese nodo. Si es None, son coords nuevas
        # ingresadas por el Entry flotante o por click directo.
        self.draw_mode_active = False
        self.draw_pending = []
        self.draw_target_count = 4   # Q4/Q9 corners
        self.draw_snap_radius_px = 10
        self.draw_hover_snap = None  # node_id en hover dentro del snap radius
        self._last_cursor_xy = None  # (sx, sy) para preview de linea al cursor
        self._last_event_state = 0   # bitmask del ultimo evento (Shift override ortho)
        self._draw_entry = None      # Toplevel del entry flotante (o None)
        # Modo ORTHO (estilo AutoCAD F8): cuando esta activo y hay punto
        # previo, el preview y el commit se proyectan al eje H o V dominante
        # desde el ultimo vertice. Shift presionado actua como override
        # instantaneo (XOR con ortho_active).
        self.ortho_active = False
        # Callbacks: el caller (pre_tab) los registra para sincronizar el
        # estado del boton toggle y refrescar tablas tras cada elemento.
        self.on_draw_mode_changed = None    # callable(active: bool)
        self.on_draw_element_created = None  # callable(elem_id)
        self.on_ortho_changed = None        # callable(active: bool)

    # ═════════════════════════════════════════════════════════════════════
    # COLORES — LUT JET (arcoíris ANSYS/SAP2000, pedido del usuario 2026-05-31)
    # ═════════════════════════════════════════════════════════════════════
    #
    # El LUT activo (`self._active_lut`) es JET para TODO (pedido del usuario
    # 2026-05-31: "cambia todo a JET", look ANSYS/SAP2000). Magnitudes no
    # negativas (VM, |u|) y campos con signo (sigma_x/sigma_y/tau_xy) usan jet;
    # los con signo se centran simetricamente en 0 (azul=compresion, rojo=traccion).

    def _t_to_color(self, t):
        """t en [0,1] -> hex via el LUT activo."""
        return t_to_hex(max(0.0, min(1.0, t)), self._active_lut)

    def _value_to_color(self, value):
        if self.result_vmax == self.result_vmin:
            return self._t_to_color(0.5)
        return value_to_hex(value, self.result_vmin, self.result_vmax,
                            self._active_lut)

    def _decoration_factor(self):
        """Multiplicador de tamano de las decoraciones (nodos, flechas,
        simbolos) segun el zoom — reescalado proporcional ACOTADO.

        Pedido del usuario 2026-05: que los objetos se reescalen al hacer zoom.
        La geometria (coords mundo) ya escala; este factor hace que las
        decoraciones (dibujadas en px-pantalla) tambien crezcan/encojan, pero
        clamped entre [MIN, MAX] para no explotar al acercar ni desaparecer al
        alejar. Se clampa el FACTOR (no el px absoluto) -> uniforme entre
        glifos de distinta base (nodo 4, flecha 44, restriccion 12).

        Devuelve 1.0 si aun no hay escala de referencia (antes del primer
        fit_view): las decoraciones quedan a su tamano base.
        """
        if not self._reference_scale:
            return 1.0
        f = self.scale / self._reference_scale
        if f < DECORATION_SCALE_MIN_FACTOR:
            return DECORATION_SCALE_MIN_FACTOR
        if f > DECORATION_SCALE_MAX_FACTOR:
            return DECORATION_SCALE_MAX_FACTOR
        return f

    def _select_colormap(self):
        """Elige el LUT segun el rango del resultado actual.

        **JET para TODO** (pedido del usuario 2026-05-31: "cambia todo a JET",
        look arcoiris clasico ANSYS/SAP2000). Tanto magnitudes no negativas
        (VM, |u|) como campos con signo (sigma_x/sigma_y/tau_xy/Ux/Uy) usan jet.
        Para campos con signo se re-centra vmin/vmax simetricamente para que el
        cero fisico caiga en el medio del arcoiris (verde) — azul = compresion,
        rojo = traccion. Unificado con la Vista 3D del Post y la
        Memoria de Calculo.
        """
        self._active_lut = JET_LUT
        if is_diverging_range(self.result_vmin, self.result_vmax):
            self.result_diverging = True
            self.result_vmin, self.result_vmax = symmetric_bounds(
                self.result_vmin, self.result_vmax)
        else:
            self.result_diverging = False

    # ═════════════════════════════════════════════════════════════════════
    # VISUALIZACION PROGRESIVA — LOD por zoom + focus (auditoria UX 2026-05)
    # ═════════════════════════════════════════════════════════════════════

    def _median_edge_px(self):
        """Pixeles-por-arista-media: mediana de longitud de arista (mundo) por
        el `scale` actual. Base del LOD. None si no hay geometria."""
        med = median_edge_length(self.project)
        if med is None:
            return None
        return med * self.scale

    def _lod_level(self):
        """Nivel de detalle actual: 'far' | 'mid' | 'near'."""
        return lod_level(self._median_edge_px(), len(self.project.elements))

    def _focus_active(self):
        """True si la atenuacion de contexto debe aplicarse ahora.

        Requiere: modo distinto de 'off', alguna seleccion de nodo/elemento,
        y (en modo 'auto') una malla lo bastante grande como para que la
        atenuacion ayude. En 'on' se aplica con cualquier malla.
        """
        if self.focus_mode == "off":
            return False
        if self.ghost_geometry:
            return False
        if not (self.selected_nodes or self.selected_elements):
            return False
        if self.focus_mode == "on":
            return True
        return len(self.project.elements) >= CANVAS_FOCUS_MIN_ELEMENTS

    def _focus_keep(self):
        """(keep_elems, keep_nodes) para el modo focus, o (None, None) si no
        esta activo."""
        if not self._focus_active():
            return None, None
        return focus_keep_sets(self.project, self.selected_nodes,
                               self.selected_elements)

    # ─── Setters publicos de la barra de Vista ──────────────────────────

    def set_node_label_mode(self, mode):
        if mode in ("auto", "always", "never"):
            self.node_label_mode = mode
            self.redraw()

    def set_elem_label_mode(self, mode):
        if mode in ("auto", "always", "never"):
            self.elem_label_mode = mode
            self.redraw()

    def set_focus_mode(self, mode):
        if mode in ("auto", "on", "off"):
            self.focus_mode = mode
            self.redraw()

    def set_boundary_emphasis(self, enabled):
        self.boundary_emphasis = bool(enabled)
        self.redraw()

    _PHASE_GLYPH = {"pre": "📐", "proc": "⚙", "post": "📊"}

    def _build_view_menu(self, menubutton):
        """Puebla el menu de CAPAS colgado del titulo del viewport
        (`self._title_mb`): prende/apaga la visibilidad de cada objeto del
        canvas + un atajo 'Vista limpia' (aisla la malla en un click) +
        'Ajustar vista'. Vive en el titulo del viewport (patron Rhino).

        Diseno (auditoria UX 2026-05): 'Numeros' va primero porque el texto es
        lo que mas satura en mallas densas. Los glifos de color (🔵🟧🔺) son
        pistas-leyenda del simbolo correspondiente en el canvas. 'Elementos' NO
        es toggleable a proposito (ocultar la malla deja nodos/cargas flotando).
        La atenuacion de contexto y la silueta del borde se quitaron del menu
        (solo gatillan en mallas grandes >=60 / >=12 elementos — invisibles en
        modelos didacticos; quedan en automatico interno).
        """
        menu = tk.Menu(menubutton, tearoff=False)
        menubutton["menu"] = menu

        # Vars de capas (refs en self -> evitan GC del recolector Tcl).
        self._var_clean = tk.BooleanVar(value=False)
        self._var_labels = tk.BooleanVar(value=self.node_label_mode != "never")
        self._var_nodes = tk.BooleanVar(value=self.show_nodes)
        self._var_loads = tk.BooleanVar(value=self.show_loads)
        self._var_constraints = tk.BooleanVar(value=self.show_constraints)
        self._var_grid = tk.BooleanVar(value=self.show_grid)

        # Power-move: aislar la malla en un click (ideal para una captura).
        menu.add_checkbutton(
            label="🧹  Vista limpia (solo malla)", variable=self._var_clean,
            command=self._toggle_clean_view)
        menu.add_separator()

        menu.add_checkbutton(
            label="Números (nodos y elementos)", variable=self._var_labels,
            command=lambda: self._set_labels_visible(self._var_labels.get()))
        menu.add_checkbutton(
            label="🔵  Nodos", variable=self._var_nodes,
            command=lambda: self._set_layer("show_nodes",
                                            self._var_nodes.get()))
        menu.add_checkbutton(
            label="🟧  Cargas", variable=self._var_loads,
            command=lambda: self._set_layer("show_loads",
                                            self._var_loads.get()))
        menu.add_checkbutton(
            label="🔺  Restricciones", variable=self._var_constraints,
            command=lambda: self._set_layer("show_constraints",
                                            self._var_constraints.get()))
        menu.add_checkbutton(
            label="Cuadrícula", variable=self._var_grid,
            command=lambda: self._set_layer("show_grid",
                                            self._var_grid.get()))

        menu.add_separator()
        menu.add_command(label="Ajustar vista", accelerator="F",
                         command=self.fit_view)

    def _set_layer(self, attr, value):
        """Prende/apaga una capa (show_nodes/show_loads/show_constraints/
        show_grid) y redibuja. Tocar una capa a mano sale del indicador
        'Vista limpia' (que es un preset momentaneo, no un estado pegajoso)."""
        setattr(self, attr, bool(value))
        self._var_clean.set(False)
        self._clean_view_prev = None
        self.redraw()

    def _set_labels_visible(self, visible):
        """Numeros (nodos + elementos): marcado -> 'auto' (visible en mallas
        chicas, oculto al alejar en densas); desmarcado -> 'never'. Tocar sale
        de 'Vista limpia'."""
        mode = "auto" if visible else "never"
        self.node_label_mode = mode
        self.elem_label_mode = mode
        self._var_clean.set(False)
        self._clean_view_prev = None
        self.redraw()

    def _toggle_clean_view(self):
        """🧹 Vista limpia: un click esconde numeros, cargas, restricciones y
        cuadricula (deja malla + nodos) para una captura limpia; al desactivar
        restaura el estado previo de cada capa."""
        if self._var_clean.get():
            self._clean_view_prev = {
                "labels": self.node_label_mode != "never",
                "loads": self.show_loads,
                "constraints": self.show_constraints,
                "grid": self.show_grid,
            }
            self.node_label_mode = "never"
            self.elem_label_mode = "never"
            self.show_loads = False
            self.show_constraints = False
            self.show_grid = False
        else:
            prev = self._clean_view_prev or {}
            lbl_mode = "auto" if prev.get("labels", True) else "never"
            self.node_label_mode = lbl_mode
            self.elem_label_mode = lbl_mode
            self.show_loads = prev.get("loads", True)
            self.show_constraints = prev.get("constraints", True)
            self.show_grid = prev.get("grid", True)
            self._clean_view_prev = None
        self._sync_layer_vars()
        self.redraw()

    def _sync_layer_vars(self):
        """Refleja el estado real de las capas en los checkbuttons del menu."""
        self._var_labels.set(self.node_label_mode != "never")
        self._var_nodes.set(self.show_nodes)
        self._var_loads.set(self.show_loads)
        self._var_constraints.set(self.show_constraints)
        self._var_grid.set(self.show_grid)

    def set_phase(self, phase):
        """Actualiza el glifo del titulo del viewport segun la fase activa
        (📐 Pre / ⚙ Proc / 📊 Post): el titulo del canvas pasa a ser un
        indicador de fase ademas del menu de display. Invocado desde
        MainWindow._on_tab_changed en cada cambio de pestana.
        """
        self._phase = phase if phase in self._PHASE_GLYPH else "pre"
        self._title_mb.configure(
            text=f"{self._PHASE_GLYPH[self._phase]}  Modelo MEF")

    # ═════════════════════════════════════════════════════════════════════
    # TRANSFORMACION DE COORDENADAS
    # ═════════════════════════════════════════════════════════════════════

    def world_to_screen(self, x, y):
        sx = x * self.scale + self.offset_x
        sy = -y * self.scale + self.offset_y
        return sx, sy

    def screen_to_world(self, sx, sy):
        x = (sx - self.offset_x) / self.scale
        y = -(sy - self.offset_y) / self.scale
        return x, y

    def _get_node_screen_pos(self, nid):
        node = self.project.nodes.get(nid)
        if node is None:
            return 0, 0
        x, y = node.x, node.y
        if self.show_deformed and self.displacements is not None:
            ord_idx = self.project.node_index_map.get(nid)
            if ord_idx is not None:
                idx = 2 * ord_idx
                if idx + 1 < len(self.displacements):
                    x += self.deform_scale * self.displacements[idx]
                    y += self.deform_scale * self.displacements[idx + 1]
        return self.world_to_screen(x, y)

    def _get_node_world_deformed(self, nid):
        """Coordenadas mundo del nodo con deformacion aplicada."""
        node = self.project.nodes.get(nid)
        if node is None:
            return 0, 0
        x, y = node.x, node.y
        if self.show_deformed and self.displacements is not None:
            ord_idx = self.project.node_index_map.get(nid)
            if ord_idx is not None:
                idx = 2 * ord_idx
                if idx + 1 < len(self.displacements):
                    x += self.deform_scale * self.displacements[idx]
                    y += self.deform_scale * self.displacements[idx + 1]
        return x, y

    # ═════════════════════════════════════════════════════════════════════
    # DIBUJO PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════

    def redraw(self):
        """Redibuja toda la malla.

        Modo interaccion (`self._interacting=True`, durante zoom/resize):
        en vez de rasterizar el campo desde cero (~80-200ms en mallas
        medianas), escalamos el bitmap del ultimo raster con PIL.resize
        (~5-10ms). El zoom se ve suave — la malla, nodos y colorbar
        moviendose nitidos sobre el campo escalado. Las isolineas si se
        skipean (marching squares es caro y poco util en movimiento).
        Al detenerse 150ms, _exit_interaction_mode llama redraw() de
        nuevo (esta vez con _interacting=False) y regenera el campo a
        resolucion exacta.
        """
        self.canvas.delete("all")
        # El redraw completo borro la capa 'hover'; resetear su estado para
        # que el proximo <Motion> la regenere sobre el elemento bajo cursor.
        self._hover_highlight_eid = None
        if self.show_grid:
            self._draw_grid()

        if self.show_deformed and self.displacements is not None:
            self._draw_original_mesh_ghost()

        # Gradiente suave de resultados (debajo de aristas).
        # - Modo normal: rasteriza desde cero con baricentricas.
        # - Modo interaccion: escala bitmap previo con PIL.resize (suave
        #   y casi instantaneo). Si no hay bitmap previo (primer redraw),
        #   cae al path de rasterizado completo igual.
        if self.result_values or self.element_result_grid:
            painted = False
            if self._interacting:
                painted = self._draw_gradient_scaled()
            if not painted:
                self._draw_gradient_elements()

        # Clasificaciones puras computadas UNA vez por redraw y compartidas
        # entre las capas de dibujo (antes cada _draw_* las recomputaba:
        # classify_orphan_status corria 4x, classify_nodes 2x por frame).
        roles = classify_nodes(self.project)
        orphan_status = classify_orphan_status(self.project)

        # Contexto de visualizacion progresiva (auditoria UX 2026-05):
        # nivel de detalle por zoom + conjuntos a mantener nitidos en focus.
        # Se computan UNA vez y se pasan a las capas.
        lod = self._lod_level()
        keep_elems, keep_nodes = self._focus_keep()

        self._draw_elements(lod=lod, keep_elems=keep_elems)
        if self.show_nodes:
            self._draw_nodes(roles=roles, orphan_status=orphan_status,
                             lod=lod, keep_nodes=keep_nodes)

        if self.show_loads:
            self._draw_loads(orphan_status=orphan_status)
            # Cargas superficiales (trapezoide + flechitas distribuidas).
            # Visibles siempre que show_loads este activo, no solo al
            # seleccionar. El metodo dibuja su propio halo si highlighted.
            self._draw_surface_loads(orphan_status=orphan_status)
        if self.show_constraints:
            self._draw_constraints(orphan_status=orphan_status)

        self._draw_highlight()

        # Colorbar e isolineas: ambos modos los soportan (nodal o per-element).
        # Las isolineas se dibujan SIEMPRE (incluso si `_interacting` esta
        # activo). En el flujo de zoom no se llama redraw — se usa
        # canvas.scale para escalar las isolineas existentes con la malla.
        # En el flujo de redraw normal (cambio de resultado, fit_view,
        # release-de-pan), regeneramos las isolineas con el marching
        # squares vectorizado por lotes (canvas_raster).
        if self.result_values or self.element_result_grid:
            if self.show_isolines:
                self._draw_isolines()
            self._draw_colorbar()

        self._draw_axes()

        # Overlay del modo dibujo (polígono parcial + numeros + snap ring)
        # se renderiza arriba de todo para que sea siempre visible.
        if self.draw_mode_active:
            self._draw_pending_overlay()

        # Capas educativas registradas por modulos en modo overlay (M0/M2/
        # M3/M6/M8). Se renderizan al final para que se vean por encima de
        # todo el dibujo base. Cada layer es responsable de su propio
        # tagging (usar prefijo "edu_" + nombre del modulo) para que el
        # modulo pueda limpiar sus dibujos sin tocar nada mas.
        for layer in list(self._overlay_layers):
            try:
                layer(self)
            except Exception:
                # Una capa defectuosa NO debe romper el redraw global.
                pass

    def redraw_overlays_only(self):
        """Re-ejecuta SOLO las capas educativas registradas, sin tocar la
        base (no hace `canvas.delete("all")` ni redibuja grilla/malla/campo).

        Cada capa borra su propio tag `edu_*` al inicio de su callable, asi
        que re-ejecutarlas las refresca sin acumular dibujos. Pensado para
        los loops de animacion (~30 fps) de los modulos overlay (glow de M4,
        pulso de M7, hover de snap del probe): un `redraw()` completo por
        frame rasteriza toda la malla y el campo (~80-200ms), inutilizable a
        30 fps. PRECONDICION: un `redraw()` completo debe haber corrido antes
        (la base ya esta dibujada en el canvas)."""
        for layer in list(self._overlay_layers):
            try:
                layer(self)
            except Exception:
                # Una capa defectuosa NO debe romper la animacion.
                pass

    # ═════════════════════════════════════════════════════════════════════
    # GRILLA, EJES, GHOST
    # ═════════════════════════════════════════════════════════════════════

    def _draw_grid(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        spacing = max(30, int(50 * self.scale))
        if spacing > 200:
            spacing = 200
        # Iterar SOLO el rango visible (antes range(-20, 60) fijo: desperdicia
        # iteraciones fuera de pantalla y, peor, omite lineas en viewports
        # anchos cuando spacing es chico). Las lineas estan en
        # sx = i*spacing + (offset_x % spacing), fase en [0, spacing).
        phase_x = self.offset_x % spacing
        for i in range(0, math.ceil((w - phase_x) / spacing) + 1):
            sx = i * spacing + phase_x
            if 0 <= sx <= w:
                self.canvas.create_line(
                    sx, 0, sx, h, fill=CANVAS_GRID_COLOR, width=1, dash=(2, 6),
                    tags=("screen", "grid"),
                )
        phase_y = self.offset_y % spacing
        for i in range(0, math.ceil((h - phase_y) / spacing) + 1):
            sy = i * spacing + phase_y
            if 0 <= sy <= h:
                self.canvas.create_line(
                    0, sy, w, sy, fill=CANVAS_GRID_COLOR, width=1, dash=(2, 6),
                    tags=("screen", "grid"),
                )

    def _draw_axes(self):
        margin = 40
        length = 35
        bx, by = margin, self.canvas.winfo_height() - margin
        self.canvas.create_line(
            bx, by, bx + length, by, fill=CANVAS_AXIS_X_COLOR, width=2,
            arrow=tk.LAST,
            tags=("screen", "axes"),
        )
        self.canvas.create_text(
            bx + length + 8, by, text="X", fill=CANVAS_AXIS_X_COLOR,
            font=("Segoe UI", 9, "bold"), anchor=W,
            tags=("screen", "axes"),
        )
        self.canvas.create_line(
            bx, by, bx, by - length, fill=CANVAS_AXIS_Y_COLOR, width=2,
            arrow=tk.LAST,
            tags=("screen", "axes"),
        )
        self.canvas.create_text(
            bx, by - length - 8, text="Y", fill=CANVAS_AXIS_Y_COLOR,
            font=("Segoe UI", 9, "bold"), anchor=S,
            tags=("screen", "axes"),
        )

    def _draw_original_mesh_ghost(self):
        for elem in self.project.elements.values():
            coords = []
            valid = True
            for nid in elem.node_ids[:4]:
                node = self.project.nodes.get(nid)
                if node is None:
                    valid = False
                    break
                sx, sy = self.world_to_screen(node.x, node.y)
                coords.extend([sx, sy])
            if not valid or len(coords) < 8:
                continue
            coords.extend(coords[:2])
            self.canvas.create_line(
                *coords, fill=CANVAS_DEFORM_GHOST_COLOR, width=1, dash=(3, 5),
                tags=("world", "ghost"),
            )

    # ═════════════════════════════════════════════════════════════════════
    # GRADIENTE SUAVE (PIL pixel-perfect con mapeo bilineal inverso)
    # ═════════════════════════════════════════════════════════════════════

    def _get_grid_values(self, elem, n):
        """Devuelve una grilla (n+1, n+1) de valores en (xi, eta) para el
        render del gradient, segun el modo activo:

          - element_result_grid (modo CRUDO): grilla pre-computada por
            post_tab usando compute_raw en cada punto. Para invariantes
            (VM, σ1, σ2) interpola componentes y los compone POR PUNTO --
            unica forma fisicamente correcta de visualizar funciones no
            lineales del tensor de esfuerzos.

          - result_values (modo SUAVIZADO o U): valores nodales unicos.
            Se interpola bilinealmente con las 4 shape functions Q4.

        Retorna (grid_array_shape_n+1xn+1, ok) o (None, False).
        """
        nids = elem.node_ids[:4]
        # Modo CRUDO: la grilla ya viene pre-computada. Si el tamaño no
        # coincide con `n` del render hacemos resample por nearest -- caso
        # raro, normalmente post_tab pasa el mismo n que usa el canvas.
        if self.element_result_grid is not None:
            grid = self.element_result_grid.get(elem.id)
            if grid is None:
                return None, False
            if grid.shape == (n + 1, n + 1):
                return grid, True
            # Resample tosco si el tamaño difiere (no deberia pasar)
            from numpy import linspace
            gn = grid.shape[0] - 1
            out = np.zeros((n + 1, n + 1))
            for i in range(n + 1):
                for j in range(n + 1):
                    gi = int(round(i * gn / n))
                    gj = int(round(j * gn / n))
                    out[i, j] = grid[gi, gj]
            return out, True
        # Modo SUAVIZADO: interpolacion bilineal de los 4 valores nodales
        # promediados. EXACTO para componentes lineales (Sx, Sy, Txy en
        # Q4 alineado, Ux, Uy en cualquier Q4); aproximacion razonable
        # para invariantes (VM, σ1, σ2) porque el campo suavizado ya
        # absorbio las no-linealidades en el promedio nodal.
        if self.result_values is not None:
            if not all(nid in self.project.nodes
                       and nid in self.result_values for nid in nids):
                return None, False
            nv = [float(self.result_values[nid]) for nid in nids]
            grid = np.zeros((n + 1, n + 1))
            xs = np.linspace(-1.0, 1.0, n + 1)
            for i, xi in enumerate(xs):
                for j, eta in enumerate(xs):
                    N0 = (1 - xi) * (1 - eta) * 0.25
                    N1 = (1 + xi) * (1 - eta) * 0.25
                    N2 = (1 + xi) * (1 + eta) * 0.25
                    N3 = (1 - xi) * (1 + eta) * 0.25
                    grid[i, j] = N0*nv[0] + N1*nv[1] + N2*nv[2] + N3*nv[3]
            return grid, True
        return None, False

    def _gradient_cache_valid(self, w, h):
        """Comprueba si la imagen cacheada sigue siendo valida para el
        viewport y datos de resultado actuales.

        Clave SIN offset_x/offset_y: la traslacion del raster en pan se
        modela como desplazamiento del create_image (ver `_gradient_photo_offset`),
        no como invalidacion de cache. Esto permite reutilizar la PhotoImage
        rasterizada entre redraws cuando solo cambio el viewport (Pan).

        Si cambia scale (zoom), w/h (resize), vmin/vmax/resultado (nuevo solve),
        deform_scale o show_deformed, la cache se invalida y se re-rasteriza.
        El pan-release tambien invalida explicitamente (setea key=None) para
        rerasterizar y cubrir las zonas que entraron al viewport durante el
        drag.
        """
        rid = (id(self.result_values)
               if self.result_values is not None
               else id(self.element_result_grid))
        key = (
            rid,
            round(self.result_vmin, 9) if self.result_vmin is not None else None,
            round(self.result_vmax, 9) if self.result_vmax is not None else None,
            w, h,
            round(self.scale, 9),
            self.deform_scale,
            self.show_deformed,
        )
        return key == self._gradient_cache_key, key

    def _draw_gradient_elements(self):
        """Gradiente Gouraud: subdivision + rasterizacion de triangulos con PIL.

        Rasteriza a un bitmap mas grande que el viewport visible (padding
        del 50% en cada lado). Asi, durante un pan, la imagen movida por
        canvas.move tiene "tela de sobra" antes de mostrar el recorte —
        es la misma tecnica que usan SAP2000/ANSYS/ParaView en GPU para
        que el pan se sienta instantaneo sin re-rasterizar.

        Itera por elemento, genera grilla (n+1)x(n+1) de (sx, sy, val),
        subdivide en 2 triangulos por celda y los rasteriza con
        interpolacion baricentrica. Los `val` provienen de _get_grid_values
        (modo crudo: pre-computado con compute_raw real; modo suavizado:
        bilineal de corners nodales).
        """
        if not HAS_PIL:
            self._draw_gradient_polygons()
            return

        w = int(self.canvas.winfo_width())
        h = int(self.canvas.winfo_height())
        if w <= 1 or h <= 1:
            return

        # Reusar imagen cacheada si el viewport y los datos no cambiaron.
        # `_gradient_photo_offset` guarda el offset al que se rasterizo; al
        # reutilizarse, pintamos la imagen desplazada por (offset_actual -
        # offset_raster) para que el resultado quede alineado con la malla
        # tras paneos.
        cache_valid, new_key = self._gradient_cache_valid(w, h)
        if cache_valid and self._gradient_photo is not None:
            ox, oy = self._gradient_photo_offset
            pad_x, pad_y = self._gradient_photo_pad
            dx = self.offset_x - ox - pad_x
            dy = self.offset_y - oy - pad_y
            self.canvas.create_image(
                dx, dy, anchor=NW, image=self._gradient_photo,
                tags=("world", "gradient"),
            )
            return

        # Padding del raster: 50% del viewport en cada lado. Resultado:
        # imagen 2x ancho * 2x alto = 4x pixeles del viewport. Para
        # canvas tipico 1200x800 son ~10 MB RGBA — aceptable.
        pad_x = int(w * _GRADIENT_PAD_FRAC)
        pad_y = int(h * _GRADIENT_PAD_FRAC)
        W = w + 2 * pad_x
        H = h + 2 * pad_y

        img = np.zeros((H, W, 4), dtype=np.uint8)
        n = 6  # subdivisiones por arista (36 celdas = 72 triangulos/elemento)

        # Vectorizado por lotes (gui/preprocessing/canvas_raster.py): puntos
        # de grilla, valores y triangulos de TODOS los elementos a la vez, y
        # un unico rasterizado con baricentricas + LUT. Mismos pixeles que el
        # loop por triangulo que habia antes.
        nodes = self.project.nodes
        elems = [elem for elem in self.project.elements.values()
                 if all(nid in nodes for nid in elem.node_ids[:4])]
        elems, vals = self._grid_values_batch(elems, n)
        if elems:
            corners = self._corner_coords_deformed(elems)          # (e, 4, 2) mundo
            pts = element_grid_points(corners, n)                   # (e, p, 2) mundo
            # Coords pantalla SHIFTADAS por (pad_x, pad_y): el bitmap ocupa
            # (0..W, 0..H) y el viewport visible es (pad_x.., pad_y..).
            sx = pts[..., 0] * self.scale + self.offset_x + pad_x
            sy = -pts[..., 1] * self.scale + self.offset_y + pad_y
            P = np.stack([sx, sy, vals], axis=-1)                   # (e, p, 3)
            tris = P[:, grid_triangles(n)].reshape(-1, 3, 3)
            rasterize_triangles(img, tris, self.result_vmin, self.result_vmax,
                                self._active_lut)

        # Mostrar imagen en el canvas. Guardamos el PIL Image (no solo el
        # PhotoImage) para poder hacer Image.resize() durante zoom suave.
        pil_img = Image.fromarray(img, 'RGBA')
        old_photo = self._gradient_photo
        self._gradient_pil_image = pil_img
        self._gradient_photo = ImageTk.PhotoImage(pil_img)
        self._gradient_photo_pad = (pad_x, pad_y)
        self._gradient_photo_scale = self.scale
        # La imagen va anclada NW desplazada hacia arriba-izquierda por el
        # padding. Cuando offset_x/y cambian (pan), el delta se aplica al
        # crear_image y el bitmap "viaja" con la malla.
        self.canvas.create_image(
            -pad_x, -pad_y, anchor=NW, image=self._gradient_photo,
            tags=("world", "gradient"),
        )
        del old_photo  # libera la imagen anterior; evita leak acumulado por zoom/pan
        self._gradient_cache_key = new_key
        self._gradient_photo_offset = (self.offset_x, self.offset_y)

    def _draw_gradient_scaled(self):
        """Pinta el bitmap del gradient escalado al `scale` actual via
        PIL.Image.resize, sin re-rasterizar el campo desde cero.

        Tecnica usada por SAP2000/ANSYS/ParaView en GPU: durante zoom
        interactivo, escalar el bitmap existente es ~30x mas rapido que
        recomputar todos los triangulos. La calidad baja levemente
        (NEAREST sampling, pixeles agrandados al zoom in) pero la malla,
        outlines, nodos y colorbar siguen renderizando a la resolucion
        correcta — el ojo no nota la "blandura" del campo durante el
        movimiento. Al detenerse 150ms, redraw() llama
        _draw_gradient_elements y re-rasteriza a la resolucion exacta.

        Retorna True si pinto algo (habia bitmap previo), False si no
        (caller debe caer al path completo).
        """
        if (not HAS_PIL or self._gradient_pil_image is None
                or self._gradient_photo_scale <= 0):
            return False
        f = self.scale / self._gradient_photo_scale
        if abs(f - 1.0) < 0.005:
            # Mismo scale (delta < 0.5%): reusar PhotoImage original sin
            # re-resize. Importante porque `_request_redraw` se llama
            # tambien tras eventos no-zoom y queremos cero overhead.
            photo = self._gradient_photo
        else:
            pil = self._gradient_pil_image
            new_w = max(1, int(pil.width * f))
            new_h = max(1, int(pil.height * f))
            # NEAREST: ~5-10ms para bitmaps de ~10MP. BILINEAR seria
            # mas suave pero ~3x mas lento — durante interaccion priorizamos
            # latencia. El redraw final post-interaccion usa la calidad
            # full del rasterizador vectorizado (rasterize_triangles).
            scaled = pil.resize((new_w, new_h), Image.NEAREST)
            photo = ImageTk.PhotoImage(scaled)
            self._gradient_zoom_photo = photo  # ref viva para evitar GC

        # Posicionar el bitmap escalado en pantalla. Derivacion: el pixel
        # (x,y) del bitmap original representaba el punto mundo
        # ((-pad_x + x - ox) / scale_old, ...). En el viewport nuevo, ese
        # mismo punto mundo debe ir a (mundo * scale_new + offset_new).
        # Resolviendo para la esquina NW del bitmap escalado (pixel 0,0):
        #   B = offset_new - (pad + offset_raster) * f
        ox, oy = self._gradient_photo_offset
        pad_x, pad_y = self._gradient_photo_pad
        B_x = self.offset_x - (pad_x + ox) * f
        B_y = self.offset_y - (pad_y + oy) * f
        self.canvas.create_image(
            B_x, B_y, anchor=NW, image=photo,
            tags=("world", "gradient"),
        )
        # Z-order: el bitmap recien creado quedo al FRENTE por defecto (Tk
        # apila por orden de create_*). Lo bajamos para que las isolineas,
        # nodos, etiquetas y demas items "world" queden ENCIMA. El grid
        # (tag "screen", "grid") va aun mas al fondo para replicar el
        # orden del redraw normal: grid → gradient → resto.
        self.canvas.tag_lower("gradient")
        self.canvas.tag_lower("grid")
        return True

    def _corner_coords_deformed(self, elems):
        """Coords mundo (con deformacion si aplica) de los 4 corners de cada
        elemento: array (e, 4, 2)."""
        out = np.empty((len(elems), 4, 2))
        for k, elem in enumerate(elems):
            for c, nid in enumerate(elem.node_ids[:4]):
                out[k, c] = self._get_node_world_deformed(nid)
        return out

    def _grid_values_batch(self, elems, n):
        """Valores del campo activo en la grilla (n+1)x(n+1) de cada elemento,
        para todos a la vez: retorna (elems_validos, vals (e, (n+1)^2)).

        Misma semantica que `_get_grid_values`: modo CRUDO toma la grilla
        pre-computada (resampleo por elemento solo si el tamano no coincide);
        modo SUAVIZADO interpola bilinealmente los 4 valores nodales.
        """
        n_pts = (n + 1) * (n + 1)
        if self.element_result_grid is not None:
            kept, rows = [], []
            for elem in elems:
                grid = self.element_result_grid.get(elem.id)
                if grid is None:
                    continue
                if grid.shape != (n + 1, n + 1):
                    grid, ok = self._get_grid_values(elem, n)
                    if not ok:
                        continue
                kept.append(elem)
                rows.append(np.asarray(grid, dtype=float).ravel())
            vals = np.array(rows) if rows else np.zeros((0, n_pts))
            return kept, vals
        if self.result_values is not None:
            nodes = self.project.nodes
            rv = self.result_values
            kept, nv = [], []
            for elem in elems:
                nids = elem.node_ids[:4]
                if not all(nid in nodes and nid in rv for nid in nids):
                    continue
                kept.append(elem)
                nv.append([float(rv[nid]) for nid in nids])
            if not kept:
                return [], np.zeros((0, n_pts))
            return kept, element_grid_values(np.array(nv), n)
        return [], np.zeros((0, n_pts))

    def _draw_gradient_polygons(self):
        """Fallback: gradiente con sub-poligonos si PIL no esta disponible.

        Consume la misma grilla (n+1, n+1) que `_draw_gradient_elements`
        para que el modo crudo (con valores ya pre-computados) y el
        suavizado se vean coherentes incluso sin PIL.
        """
        n = 10
        for elem in self.project.elements.values():
            nids = elem.node_ids[:4]
            if not all(nid in self.project.nodes for nid in nids):
                continue
            grid, ok = self._get_grid_values(elem, n)
            if not ok:
                continue
            nc = []
            for nid in nids:
                x, y = self._get_node_world_deformed(nid)
                nc.append((x, y))
            for i in range(n):
                xi0 = -1 + 2 * i / n
                xi1 = -1 + 2 * (i + 1) / n
                for j in range(n):
                    eta0 = -1 + 2 * j / n
                    eta1 = -1 + 2 * (j + 1) / n
                    corners = [(xi0, eta0), (xi1, eta0),
                               (xi1, eta1), (xi0, eta1)]
                    # Indices del corner en la grilla (i, j) (i+1, j) etc.
                    corner_idx = [(i, j), (i + 1, j),
                                  (i + 1, j + 1), (i, j + 1)]
                    pts = []
                    val_sum = 0.0
                    for k, (xi, eta) in enumerate(corners):
                        N = [(1 - xi) * (1 - eta) / 4,
                             (1 + xi) * (1 - eta) / 4,
                             (1 + xi) * (1 + eta) / 4,
                             (1 - xi) * (1 + eta) / 4]
                        x = sum(N[m] * nc[m][0] for m in range(4))
                        y = sum(N[m] * nc[m][1] for m in range(4))
                        gi, gj = corner_idx[k]
                        v = float(grid[gi, gj])
                        sx, sy = self.world_to_screen(x, y)
                        pts.extend([sx, sy])
                        val_sum += v
                    color = self._value_to_color(val_sum / 4)
                    self.canvas.create_polygon(
                        *pts, fill=color, outline="",
                        tags=("world", "gradient"),
                    )

    # ═════════════════════════════════════════════════════════════════════
    # ISOLINEAS (Marching Squares)
    # ═════════════════════════════════════════════════════════════════════

    def _draw_isolines(self):
        """Dibuja curvas de nivel usando marching squares por elemento.

        En modo CRUDO (element_result_grid activo) las isolineas pueden
        saltar entre elementos vecinos -- es coherente con la naturaleza
        discontinua del campo. Cada elemento se evalua localmente con su
        propia grilla pre-computada.

        Nota: durante interaccion activa (zoom/resize) redraw() ya skip-ea
        esta funcion junto con el gradient, asi que aqui no hace falta
        guardar el flag. Solo se llama en redraws completos.
        """
        if not (self.result_values or self.element_result_grid):
            return

        n_levels = self.isoline_count
        levels = np.linspace(self.result_vmin, self.result_vmax,
                             n_levels + 2)[1:-1]

        # En modo CRUDO la grilla viene pre-computada por post_tab (típicamente
        # 7x7, n=6). Derivamos n_grid del tamaño nativo de cada grilla para
        # NO resamplear 7x7 -> 16x16 (doble loop Python por elemento). En modo
        # suavizado interpolamos sobre una grilla fina (16) para curvas lisas.
        raw_mode = self.element_result_grid is not None
        default_n_grid = 16
        scale = self.scale
        ox = self.offset_x
        oy = self.offset_y

        # Vectorizado por lotes: los elementos se agrupan por tamano de grilla
        # (modo CRUDO: la nativa de cada uno, tipicamente 7x7; suavizado: una
        # grilla fina de 16x16 para curvas lisas) y marching squares corre
        # sobre todos los elementos del grupo a la vez.
        nodes = self.project.nodes
        groups = {}
        for elem in self.project.elements.values():
            if not all(nid in nodes for nid in elem.node_ids[:4]):
                continue
            if raw_mode:
                native = self.element_result_grid.get(elem.id)
                if native is None:
                    continue
                n_grid = native.shape[0]  # puntos nativos (n+1)
            else:
                n_grid = default_n_grid
            groups.setdefault(n_grid, []).append(elem)

        for n_grid, group in groups.items():
            elems, vals = self._grid_values_batch(group, n_grid - 1)
            if not elems:
                continue
            corners = self._corner_coords_deformed(elems)
            pts = element_grid_points(corners, n_grid - 1)     # (e, p, 2) mundo
            e = len(elems)
            gx = pts[:, :, 0].reshape(e, n_grid, n_grid)
            gy = pts[:, :, 1].reshape(e, n_grid, n_grid)
            gv = vals.reshape(e, n_grid, n_grid)
            segs = marching_squares_batch(gx, gy, gv, levels)
            if segs.shape[0] == 0:
                continue
            # world_to_screen vectorizado sobre los segmentos.
            sx1 = segs[:, 0] * scale + ox
            sy1 = -segs[:, 1] * scale + oy
            sx2 = segs[:, 2] * scale + ox
            sy2 = -segs[:, 3] * scale + oy
            for k in range(segs.shape[0]):
                self.canvas.create_line(
                    sx1[k], sy1[k], sx2[k], sy2[k],
                    fill="white", width=1.2,
                    tags=("world", "isolines"),
                )

    # ═════════════════════════════════════════════════════════════════════
    # ELEMENTOS, NODOS, CARGAS, RESTRICCIONES
    # ═════════════════════════════════════════════════════════════════════

    def _draw_elements(self, *, lod="near", keep_elems=None):
        """Dibuja aristas y etiquetas de elementos con visualizacion
        progresiva (auditoria UX 2026-05):

        - LOD: en zoom lejano ('far') solo se dibuja la silueta del dominio
          (aristas de contorno) + los elementos seleccionados, sin etiquetas
          ni aristas internas — declutter + recorte del arbol Tk.
        - Silueta: las aristas de contorno se realzan sobre las internas.
        - Halo: el elemento seleccionado lleva un anillo claro debajo para
          destacar a cualquier escala.
        - Focus: si `keep_elems` no es None, los elementos fuera del conjunto
          se atenuan (gris fantasma) para que la seleccion gane por contraste.
        - Culling: los elementos fuera del viewport (+ margen) no se crean.
        """
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        # Canvas aun no realizado (winfo=1): no cullear (margen infinito) para
        # no dejar la primera pasada en blanco antes del <Configure>.
        margin = (float("inf") if (w <= 1 or h <= 1)
                  else max(w, h) * _CULL_MARGIN_FRAC)
        n_elems = len(self.project.elements)

        # Silueta del dominio: solo cuando vale la pena (malla no trivial y no
        # en modo fantasma). En 'far' es la unica geometria que se dibuja, asi
        # que ahi tambien se computa (salvo que el usuario apague las aristas).
        boundary = set()
        want_boundary = (self.boundary_emphasis and self.show_mesh_edges
                         and not self.ghost_geometry
                         and n_elems >= CANVAS_BOUNDARY_MIN_ELEMENTS)
        if (want_boundary or lod == "far") and self.show_mesh_edges \
                and not self.ghost_geometry:
            boundary = boundary_edges(self.project)

        # 1) Silueta de contorno PRIMERO (debajo de los outlines de elemento):
        #    una linea mas ancha y clara por arista de contorno -> el borde
        #    exterior se lee con claridad sobre las aristas internas.
        if boundary and not self.ghost_geometry:
            for edge in boundary:
                try:
                    n1, n2 = tuple(edge)
                except ValueError:
                    continue
                if n1 not in self.project.nodes or n2 not in self.project.nodes:
                    continue
                x1, y1 = self._get_node_screen_pos(n1)
                x2, y2 = self._get_node_screen_pos(n2)
                if not bbox_visible(min(x1, x2), min(y1, y2),
                                    max(x1, x2), max(y1, y2), w, h, margin):
                    continue
                self.canvas.create_line(
                    x1, y1, x2, y2, fill=CANVAS_BOUNDARY_COLOR,
                    width=2.5, capstyle=tk.ROUND,
                    tags=("world", "elements"),
                )

        elem_labels_global = label_globally_visible(
            self.elem_label_mode, lod, ghost=self.ghost_geometry)

        for elem in self.project.elements.values():
            coords = []
            valid = True
            min_sx = min_sy = float("inf")
            max_sx = max_sy = float("-inf")
            for nid in elem.node_ids[:4]:
                if nid not in self.project.nodes:
                    valid = False
                    break
                sx, sy = self._get_node_screen_pos(nid)
                coords.extend([sx, sy])
                min_sx, min_sy = min(min_sx, sx), min(min_sy, sy)
                max_sx, max_sy = max(max_sx, sx), max(max_sy, sy)
            if not valid or len(coords) < 8:
                continue
            # Culling por viewport.
            if not bbox_visible(min_sx, min_sy, max_sx, max_sy, w, h, margin):
                continue

            is_elem_selected = elem.id in self.selected_elements
            is_dim = (keep_elems is not None
                      and not is_elem_selected
                      and elem.id not in keep_elems)

            # En 'far' solo dibujamos el outline del elemento SELECCIONADO
            # (la silueta ya cubre el resto). Ahorra miles de poligonos.
            if lod == "far" and not is_elem_selected:
                continue

            if is_elem_selected:
                outline_color = CANVAS_SELECTED_COLOR
            elif self.ghost_geometry or is_dim:
                outline_color = CANVAS_GHOST_COLOR  # atenuado (ghost o focus)
            else:
                outline_color = CANVAS_ELEMENT_COLOR

            edge_color = outline_color if self.show_mesh_edges else ""
            line_w = (2.0 if is_elem_selected
                      else (1 if (self.ghost_geometry or is_dim) else 1.5))

            # Realce de seleccion (rediseno 2026-05, pedido del usuario): SOLO
            # un relleno punteado suave (stipple gray12) que llena el area pero
            # deja asomar la malla/los datos debajo — senal primaria, estilo
            # Abaqus/ANSYS (tk.Canvas no tiene alpha vectorial, se simula con el
            # patron de puntos). Va DEBAJO del outline. El HALO grueso fue
            # eliminado (pedido del usuario: "el borde grueso molesta"); el
            # relleno cubre area suficiente para no perderse en mallas grandes
            # (hallazgo I1) + el outline en color de seleccion lo remata.
            if is_elem_selected:
                self.canvas.create_polygon(
                    *coords, fill=CANVAS_SELECTED_FILL_COLOR, outline="",
                    stipple="gray12", tags=("world", "elements"),
                )

            self.canvas.create_polygon(
                *coords,
                outline=edge_color,
                fill="",
                width=line_w,
                tags=("world", "elements"),
            )

            # Etiqueta: politica de numeracion + realce por seleccion. Los
            # elementos atenuados (focus) no muestran numero salvo seleccion.
            show_label = (not self.ghost_geometry and not is_dim
                          and (elem_labels_global
                               or (is_elem_selected
                                   and self.elem_label_mode != "never")))
            if show_label:
                cx = sum(coords[::2]) / 4
                cy = sum(coords[1::2]) / 4
                text_color = (CANVAS_ELEM_LABEL_ON_FIELD_COLOR
                              if self.result_values
                              else CANVAS_ELEM_LABEL_COLOR)
                self.canvas.create_text(
                    cx, cy, text=str(elem.id),
                    fill=text_color,
                    font=("Segoe UI", CANVAS_FONT_SIZE, "bold"),
                    anchor=tk.CENTER,
                    tags=("world", "elements"),
                )

    def _classify_nodes(self):
        """Wrapper hacia `models.mesh_utils.classify_nodes` (single source
        of truth). Mantenido como metodo para no romper callers internos.
        """
        return classify_nodes(self.project)

    def _draw_nodes(self, roles=None, orphan_status=None,
                    lod="near", keep_nodes=None):
        # roles / orphan_status: clasificaciones puras opcionalmente
        # precomputadas por redraw() (evita recomputarlas 4-5x por frame).
        # lod / keep_nodes: visualizacion progresiva (auditoria UX 2026-05).
        if roles is None:
            roles = self._classify_nodes()
        if orphan_status is None:
            orphan_status = classify_orphan_status(self.project)
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        margin = (float("inf") if (w <= 1 or h <= 1)
                  else max(w, h) * _CULL_MARGIN_FRAC)
        f = self._decoration_factor()   # reescalado de decoraciones con el zoom

        for nid, node in self.project.nodes.items():
            sx, sy = self._get_node_screen_pos(nid)
            role = roles.get(nid, "corner")
            is_orphan = orphan_status.get(nid) == "orphan"
            is_selected = nid in self.selected_nodes
            is_corner = (role == "corner")

            # LOD: en 'far' solo se dibujan corners (los mid/center Q9 son
            # andamiaje auto-generado, puro ruido a esa escala) salvo que
            # esten seleccionados. En 'mid' los mid/center se dibujan pero
            # como punto simple (sin nucleo). El seleccionado SIEMPRE se ve.
            if lod == "far" and not is_corner and not is_selected:
                continue
            # Culling por viewport (el nodo seleccionado igual se omite si
            # esta fuera de pantalla — no aporta nada invisible).
            if not point_visible(sx, sy, w, h, margin):
                continue

            if role == "mid":
                base_color = CANVAS_NODE_MID_COLOR
                r = CANVAS_NODE_MID_RADIUS * f
                inner_color = CANVAS_NODE_INNER_MID
            elif role == "center":
                base_color = CANVAS_NODE_CENTER_COLOR
                r = CANVAS_NODE_MID_RADIUS * f
                inner_color = CANVAS_NODE_INNER_CENTER
            else:
                base_color = CANVAS_NODE_COLOR
                r = CANVAS_NODE_RADIUS * f
                inner_color = CANVAS_NODE_INNER_CORNER

            # Override por huerfano: gris tenue desaturado, sobreescribe el
            # color del rol pero mantiene el radio para no perder informacion
            # de jerarquia (un mid huerfano sigue siendo mas chico que un
            # corner huerfano).
            if is_orphan:
                base_color = CANVAS_NODE_ORPHAN_COLOR
                inner_color = CANVAS_NODE_INNER_ORPHAN

            # Atenuacion: modo fantasma (M0) o focus (nodo fuera del conjunto
            # a mantener). El seleccionado nunca se atenua.
            is_dim = ((self.ghost_geometry
                       or (keep_nodes is not None and nid not in keep_nodes))
                      and not is_selected)
            if is_dim:
                base_color = CANVAS_GHOST_COLOR
                inner_color = CANVAS_GHOST_COLOR
            color = CANVAS_SELECTED_COLOR if is_selected else base_color

            # Halo del nodo seleccionado: anillo claro mas grande DEBAJO ->
            # destaca a cualquier escala (auditoria UX 2026-05).
            if is_selected:
                hr = r + 4 * f
                self.canvas.create_oval(
                    sx - hr, sy - hr, sx + hr, sy + hr,
                    fill="", outline=CANVAS_SELECTED_HALO_COLOR, width=1.5,
                    tags=("world", "nodes"),
                )

            # En 'mid'/'far' los mid/center no seleccionados van como punto
            # simple (1 oval, sin nucleo) — menos items, menos ruido.
            simple_dot = (lod != "near" and not is_corner and not is_selected)

            self.canvas.create_oval(
                sx - r, sy - r, sx + r, sy + r,
                fill=color, outline=CANVAS_NODE_OUTLINE, width=1,
                tags=("world", "nodes"),
            )
            if not simple_dot:
                # Nucleo oscuro -> efecto "anillo" (rim mas fino que crece con
                # el zoom); o amarillo solido si esta seleccionado (disco
                # identico al bg de la fila resaltada del spreadsheet).
                ri = max(1.0, r - 1.4 * f)
                self.canvas.create_oval(
                    sx - ri, sy - ri, sx + ri, sy + ri,
                    fill=CANVAS_SELECTED_COLOR if is_selected else inner_color,
                    outline="",
                    tags=("world", "nodes"),
                )

            # Etiqueta: politica de numeracion + realce por seleccion. Los
            # nodos atenuados (focus/ghost) no muestran numero salvo seleccion.
            show_label = (not is_dim and label_visible_for_item(
                self.node_label_mode, lod,
                ghost=self.ghost_geometry, selected=is_selected))
            if show_label:
                if self.result_values and nid in self.result_values:
                    label = f"{nid}: {fmt(self.result_values[nid], 'stress')}"
                else:
                    label = str(nid)
                self.canvas.create_text(
                    sx + r + 6, sy - r - 4,
                    text=label, fill=base_color,
                    font=("Segoe UI", CANVAS_FONT_SIZE - 1),
                    anchor=tk.SW,
                    tags=("world", "nodes"),
                )

    def _draw_loads(self, orphan_status=None):
        f = self._decoration_factor()        # reescalado con el zoom
        arrow_len = 44 * f
        # Cabeza de flecha profesional (proporcion ~1:1.4, mas afilada que la
        # anterior (14,16,7)); escala con el zoom. La sombra/glow es un poco
        # mayor para asomar detras de la flecha real.
        head = (10 * f, 14 * f, 5 * f)
        head_shadow = (12 * f, 16 * f, 6 * f)
        ghost = self.ghost_geometry          # malla base atenuada (M0)
        shadow_col = "" if ghost else SHADOW_LOAD
        if orphan_status is None:
            orphan_status = classify_orphan_status(self.project)
        for load in self.project.nodal_loads.values():
            node = self.project.nodes.get(load.node_id)
            if node is None:
                continue
            sx, sy = self._get_node_screen_pos(load.node_id)
            highlighted = (load.node_id in self.selected_loads)
            is_orphan = orphan_status.get(load.node_id) == "orphan"
            # Color: highlight (amarillo) > huerfano (naranja) > normal (rojo).
            # Carga sobre nodo huerfano no contribuye al ensamblaje -> warning.
            if highlighted:
                color = CANVAS_SELECTED_COLOR
            elif is_orphan:
                color = CANVAS_NODE_ORPHAN_COLOR
            elif ghost:
                color = CANVAS_GHOST_COLOR
            else:
                color = CANVAS_LOAD_COLOR
            width = 3 if highlighted else 2
            lw = width * f                   # grosor del trazo, escala con zoom
            lw_shadow = lw + 3 * f

            if abs(load.fx) > NUMERICAL_TOLERANCE:
                d = 1 if load.fx > 0 else -1
                x_start = sx - d * arrow_len
                # Sombra/glow detras de la flecha
                self.canvas.create_line(
                    x_start, sy, sx, sy,
                    fill=shadow_col, width=lw_shadow, arrow=tk.LAST,
                    arrowshape=head_shadow,
                    tags=("world", "loads"),
                )
                # Flecha real encima
                self.canvas.create_line(
                    x_start, sy, sx, sy,
                    fill=color, width=lw, arrow=tk.LAST,
                    arrowshape=head,
                    tags=("world", "loads"),
                )
                if not ghost:
                    self._draw_label_with_bg(
                        x_start, sy - 14, f"Fx={fmt(load.fx, 'force')}",
                        fg=color, anchor=tk.S,
                        tags=("world", "loads"),
                    )

            if abs(load.fy) > NUMERICAL_TOLERANCE:
                d = -1 if load.fy > 0 else 1
                y_start = sy - d * arrow_len
                self.canvas.create_line(
                    sx, y_start, sx, sy,
                    fill=shadow_col, width=lw_shadow, arrow=tk.LAST,
                    arrowshape=head_shadow,
                    tags=("world", "loads"),
                )
                self.canvas.create_line(
                    sx, y_start, sx, sy,
                    fill=color, width=lw, arrow=tk.LAST,
                    arrowshape=head,
                    tags=("world", "loads"),
                )
                if not ghost:
                    self._draw_label_with_bg(
                        sx + 16, y_start, f"Fy={fmt(load.fy, 'force')}",
                        fg=color, anchor=tk.W,
                        tags=("world", "loads"),
                    )

    def _draw_label_with_bg(self, x, y, text, *, fg, anchor=tk.W,
                            font=None, padx=4, pady=2, tags=None):
        """Dibuja un texto con un rectangulo semi-opaco detras (mejora la
        legibilidad sobre el canvas oscuro). Retorna el id del text item.

        `tags`: tupla opcional aplicada a ambos items (texto y rectangulo).
        Tipicamente ("world", "loads") o similar para que el item viaje con
        el pan junto al resto de la malla.
        """
        if font is None:
            font = ("Segoe UI", CANVAS_FONT_SIZE - 1)
        tag_args = {"tags": tags} if tags else {}
        # Crear el text para medir bbox, luego rectangulo, luego mover el text al frente
        tid = self.canvas.create_text(
            x, y, text=text, fill=fg, font=font, anchor=anchor, **tag_args,
        )
        bb = self.canvas.bbox(tid)
        if bb is None:
            return tid
        x1, y1, x2, y2 = bb
        rid = self.canvas.create_rectangle(
            x1 - padx, y1 - pady, x2 + padx, y2 + pady,
            fill=LABEL_BG, outline=fg, width=1, **tag_args,
        )
        # Asegurar que el texto este encima del rectangulo
        self.canvas.tag_raise(tid, rid)
        return tid

    def _draw_constraints(self, orphan_status=None):
        """Dibuja simbolos de restriccion con notacion estandar:
        - is_fixed     : triangulo + hatching (empotramiento)
        - is_roller_y  : restringe Δy => triangulo apoyado en una superficie
                         horizontal con un rodillo (circulo) entre los dos.
                         El nodo puede moverse en X.
        - is_roller_x  : restringe Δx => mismo simbolo rotado 90deg, apoyado
                         contra una superficie vertical. El nodo puede moverse
                         en Y.
        Estetica: relleno suave (no hueco) para que el simbolo se distinga
        del fondo oscuro; outline en color de fase; hatching mas espaciado.
        """
        f = self._decoration_factor()        # reescalado con el zoom
        size = 14 * f                        # base 14 (era 12 fijo)
        roller_r = 0.36 * size               # radio del rodillo (~5 a f=1)
        if orphan_status is None:
            orphan_status = classify_orphan_status(self.project)
        for bc in self.project.boundary_conditions.values():
            node = self.project.nodes.get(bc.node_id)
            if node is None:
                continue
            sx, sy = self._get_node_screen_pos(bc.node_id)
            highlighted = (bc.node_id in self.selected_constraints)
            is_orphan = orphan_status.get(bc.node_id) == "orphan"
            # Color: highlight (amarillo) > huerfano (naranja) > normal (naranja
            # de constraint). Una BC sobre nodo huerfano es ERROR CRITICO (DOF
            # colgante restringido -> K_red singular). Marcarla en naranja
            # desaturado distingue claramente del naranja brillante normal.
            if highlighted:
                color = CANVAS_SELECTED_COLOR
            elif is_orphan:
                color = CANVAS_NODE_ORPHAN_COLOR
            elif self.ghost_geometry:
                color = CANVAS_GHOST_COLOR   # malla base atenuada (M0)
            else:
                color = CANVAS_CONSTRAINT_COLOR
            width = 3 if highlighted else 2
            # Relleno suave para mejorar visibilidad sin saturar (hueco en
            # modo fantasma para que el simbolo quede como silueta tenue).
            fill_fixed  = "" if self.ghost_geometry else CANVAS_CONSTRAINT_FIXED_FILL
            fill_roller = "" if self.ghost_geometry else CANVAS_CONSTRAINT_ROLLER_FILL

            if bc.is_fixed:
                # Triangulo (vertice arriba en el nodo)
                self.canvas.create_polygon(
                    sx, sy + size,
                    sx - size, sy + size * 2,
                    sx + size, sy + size * 2,
                    outline=color, fill=fill_fixed, width=width,
                    tags=("world", "constraints"),
                )
                # Linea base (la "pared" donde se empotra)
                self.canvas.create_line(
                    sx - size - 4, sy + size * 2,
                    sx + size + 4, sy + size * 2,
                    fill=color, width=max(2.5, width),
                    tags=("world", "constraints"),
                )
                # Hatching mas espaciado (3 lineas, no 4 amontonadas)
                for i in range(3):
                    lx = sx - size + i * size
                    self.canvas.create_line(
                        lx, sy + size * 2,
                        lx - 6, sy + size * 2 + 6,
                        fill=color, width=max(1, width - 1),
                        tags=("world", "constraints"),
                    )

            elif bc.is_roller_x:
                # Restringe Δx -> nodo se desplaza solo en Y. Pictograma:
                #   triangulo apuntando hacia el nodo (vertice = nodo) +
                #   rodillo (circulo) entre el triangulo y la superficie +
                #   superficie VERTICAL (linea) detras del rodillo.
                # Apoyo a la izquierda del nodo.
                tri_base_x = sx - size            # cara plana del triangulo
                tri_top_x  = tri_base_x - size    # vertice opuesto al nodo
                # Triangulo (vertice apunta hacia el nodo)
                self.canvas.create_polygon(
                    sx,           sy,
                    tri_base_x,   sy - size,
                    tri_base_x,   sy + size,
                    outline=color, fill=fill_roller, width=width,
                    tags=("world", "constraints"),
                )
                # Rodillo (circulo) entre triangulo y la "pared"
                roller_cx = tri_top_x - 4
                self.canvas.create_oval(
                    roller_cx - roller_r, sy - roller_r,
                    roller_cx + roller_r, sy + roller_r,
                    outline=color, fill=fill_roller, width=max(1, width - 1),
                    tags=("world", "constraints"),
                )
                # Superficie vertical (la "pared" donde rueda)
                wall_x = roller_cx - 6
                self.canvas.create_line(
                    wall_x, sy - size - 4,
                    wall_x, sy + size + 4,
                    fill=color, width=max(2, width),
                    tags=("world", "constraints"),
                )
                # Hatching detras de la pared
                for i in range(3):
                    yy = sy - size + i * size
                    self.canvas.create_line(
                        wall_x,     yy,
                        wall_x - 6, yy - 6,
                        fill=color, width=max(1, width - 1),
                        tags=("world", "constraints"),
                    )

            elif bc.is_roller_y:
                # Restringe Δy -> nodo se desplaza solo en X. Pictograma:
                #   triangulo + rodillo + superficie horizontal debajo.
                tri_base_y = sy + size
                tri_bot_y  = sy + size * 2
                # Triangulo (vertice apunta al nodo, base abajo)
                self.canvas.create_polygon(
                    sx,         sy,
                    sx - size,  tri_base_y,
                    sx + size,  tri_base_y,
                    outline=color, fill=fill_roller, width=width,
                    tags=("world", "constraints"),
                )
                # Rodillo (circulo) entre triangulo y superficie
                roller_cy = tri_base_y + 5
                self.canvas.create_oval(
                    sx - roller_r, roller_cy - roller_r,
                    sx + roller_r, roller_cy + roller_r,
                    outline=color, fill=fill_roller, width=max(1, width - 1),
                    tags=("world", "constraints"),
                )
                # Superficie horizontal donde rueda
                surf_y = roller_cy + 6
                self.canvas.create_line(
                    sx - size - 4, surf_y,
                    sx + size + 4, surf_y,
                    fill=color, width=max(2, width),
                    tags=("world", "constraints"),
                )
                # Hatching debajo de la superficie
                for i in range(3):
                    lx = sx - size + i * size
                    self.canvas.create_line(
                        lx,     surf_y,
                        lx - 6, surf_y + 6,
                        fill=color, width=max(1, width - 1),
                        tags=("world", "constraints"),
                    )

    def _draw_highlight(self):
        # Las aristas potenciales (para SurfaceLoad) no tienen render propio
        # fuera de las aristas del elemento contenedor: se superpone una linea
        # amarilla con HALO sobre la arista seleccionada.
        # (Nota: el realce de nodos/elementos/loads/etc se hace en sus
        # _draw_* respectivos con color + halo; ver auditoria UX 2026-05.)
        if not self.selected_edges:
            return
        f = self._decoration_factor()        # reescalado con el zoom
        for edge in self.selected_edges:
            try:
                n1, n2 = tuple(edge)
            except ValueError:
                continue
            if n1 not in self.project.nodes or n2 not in self.project.nodes:
                continue
            x1, y1 = self.world_to_screen(
                self.project.nodes[n1].x, self.project.nodes[n1].y)
            x2, y2 = self.world_to_screen(
                self.project.nodes[n2].x, self.project.nodes[n2].y)
            # Halo claro mas ancho debajo + linea de seleccion encima (afinados:
            # antes 8/4, ahora 6/2.5 — menos "fuerte", pedido del usuario).
            self.canvas.create_line(
                x1, y1, x2, y2, fill=CANVAS_SELECTED_HALO_COLOR, width=6 * f,
                capstyle=tk.ROUND, tags=("world", "highlight"),
            )
            self.canvas.create_line(
                x1, y1, x2, y2, fill=CANVAS_SELECTED_COLOR, width=2.5 * f,
                capstyle=tk.ROUND, tags=("world", "highlight"),
            )

    def _draw_surface_loads(self, orphan_status=None):
        """Dibuja todas las cargas superficiales como trapezoide + flechitas.

        Para cada SurfaceLoad:
        - Calcula la direccion de aplicacion (normal CCW de la tangente
          rotada por sl.angle, en mundo, luego convertida a render).
        - Traza la "linea superior" del trapezoide de carga conectando las
          puntas de las flechitas extremas (longitudes proporcionales a
          q_start y q_end, escaladas al maximo absoluto del modelo).
        - Distribuye flechitas a lo largo del borde con longitud lineal
          q(s) = q_start*(1-s) + q_end*s.
        - Si la carga esta highlighted, usa color SELECTED y dibuja halos
          en los nodos extremos.
        """
        if not self.project.surface_loads:
            return
        f = self._decoration_factor()        # reescalado con el zoom
        ghost = self.ghost_geometry          # malla base atenuada (M0)
        shadow_col = "" if ghost else SHADOW_SURFACE
        qmax = 0.0
        for sl in self.project.surface_loads:
            qmax = max(qmax, abs(sl.q_start), abs(sl.q_end))
        if qmax < 1e-12:
            qmax = 1.0
        arrow_max = 60 * f   # px maximo de flecha (escala con el zoom)
        # Cabeza unificada con las cargas nodales (proporcion ~1:1.3).
        head = (10 * f, 13 * f, 5 * f)
        head_shadow = (12 * f, 15 * f, 6 * f)
        n_arrows = 8     # cantidad de flechitas distribuidas
        if orphan_status is None:
            orphan_status = classify_orphan_status(self.project)

        for idx, sl in enumerate(self.project.surface_loads):
            if (sl.node_start not in self.project.nodes
                    or sl.node_end not in self.project.nodes):
                continue
            n_a = self.project.nodes[sl.node_start]
            n_b = self.project.nodes[sl.node_end]
            sx1, sy1 = self._get_node_screen_pos(sl.node_start)
            sx2, sy2 = self._get_node_screen_pos(sl.node_end)
            # Surface load colgada: si CUALQUIERA de los 2 extremos es
            # huerfano, la integracion no contribuye a F (no hay arista
            # ensamblada). Tintar en naranja para marcarla.
            is_orphan = (orphan_status.get(sl.node_start) == "orphan"
                         or orphan_status.get(sl.node_end) == "orphan")

            # Direccion en mundo (consistente con FEM): normal CCW de la
            # tangente, luego rotada por sl.angle. Despues conversion a
            # render invirtiendo Y (porque screen Y crece hacia abajo).
            wdx = n_b.x - n_a.x
            wdy = n_b.y - n_a.y
            Lw = math.hypot(wdx, wdy)
            if Lw < 1e-12:
                continue
            twx, twy = wdx / Lw, wdy / Lw
            nwx, nwy = -twy, twx  # normal CCW en mundo (angle=0)
            th = math.radians(sl.angle)
            c, s = math.cos(th), math.sin(th)
            dwx = c * nwx - s * nwy
            dwy = s * nwx + c * nwy
            rdx, rdy = dwx, -dwy  # direccion en render (Y invertida)

            is_h = (idx in self.selected_surfaces)
            # Color: highlight (amarillo) > huerfano (naranja) > normal (rojo).
            if is_h:
                col = CANVAS_SELECTED_COLOR
            elif is_orphan:
                col = CANVAS_NODE_ORPHAN_COLOR
            elif ghost:
                col = CANVAS_GHOST_COLOR
            else:
                col = CANVAS_LOAD_COLOR
            wid = (3 if is_h else 2) * f     # grosor del trazo, escala con zoom

            # Longitudes proporcionales en pantalla
            sa = 1 if sl.q_start >= 0 else -1
            sb = 1 if sl.q_end >= 0 else -1
            La = arrow_max * abs(sl.q_start) / qmax
            Lb = arrow_max * abs(sl.q_end)   / qmax

            # Linea superior del trapezoide (conecta las puntas)
            if La > 1.0 or Lb > 1.0:
                ax = sx1 + rdx * La * sa
                ay = sy1 + rdy * La * sa
                bx = sx2 + rdx * Lb * sb
                by = sy2 + rdy * Lb * sb
                self.canvas.create_line(
                    ax, ay, bx, by, fill=col, width=wid, dash=(4, 2),
                    tags=("world", "surfaces"),
                )

            # Flechitas distribuidas (apuntan desde el exterior hacia la arista)
            # Cada flecha lleva una "sombra" detras del color principal (glow).
            for k in range(n_arrows + 1):
                t = k / n_arrows
                px = sx1 + t * (sx2 - sx1)
                py = sy1 + t * (sy2 - sy1)
                q_loc = sl.q_start * (1.0 - t) + sl.q_end * t
                if abs(q_loc) < 1e-12:
                    continue
                slsign = 1 if q_loc >= 0 else -1
                L_loc = arrow_max * abs(q_loc) / qmax
                if L_loc < 3:
                    continue
                ex = px + rdx * L_loc * slsign
                ey = py + rdy * L_loc * slsign
                # Sombra detras
                self.canvas.create_line(
                    ex, ey, px, py, fill=shadow_col, width=wid + 2 * f,
                    arrow=tk.LAST, arrowshape=head_shadow,
                    tags=("world", "surfaces"),
                )
                # Flecha principal
                self.canvas.create_line(
                    ex, ey, px, py, fill=col, width=wid,
                    arrow=tk.LAST, arrowshape=head,
                    tags=("world", "surfaces"),
                )

            # Etiqueta con magnitudes
            mt = 0.5
            lab_off = max(arrow_max * 0.7,
                          arrow_max * (abs(sl.q_start) + abs(sl.q_end))
                          / (2.0 * qmax) + 14)
            cx = sx1 + mt * (sx2 - sx1) + rdx * lab_off
            cy = sy1 + mt * (sy2 - sy1) + rdy * lab_off
            label = f"q: {sl.q_start:g} → {sl.q_end:g}"
            if abs(sl.angle) > 1e-9:
                label += f"  ∠{sl.angle:g}°"
            if not ghost:
                self._draw_label_with_bg(
                    cx, cy, label, fg=col, anchor=tk.CENTER,
                    tags=("world", "surfaces"),
                )

            # Sin halo extra: el cambio de color ya indica la seleccion.

    def _draw_colorbar(self):
        """Dibuja la leyenda de color en la esquina derecha del canvas.

        TAGS ("screen", "colorbar"): el colorbar es un overlay anclado a
        pantalla — NO debe moverse durante pan/zoom. Como esta etiquetado
        como "screen", el pan rapido (canvas.move("all", ...) + move(
        "screen", -dx, -dy)) lo deja en su lugar sin re-dibujarlo.
        """
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return

        bar_w = 20
        bar_h = min(250, h - 80)
        x0 = w - bar_w - 30
        y0 = 40
        n_steps = 50

        for i in range(n_steps):
            t = 1.0 - i / n_steps
            color = self._t_to_color(t)
            yy = y0 + i * bar_h / n_steps
            self.canvas.create_rectangle(
                x0, yy, x0 + bar_w, yy + bar_h / n_steps + 1,
                fill=color, outline="",
                tags=("screen", "colorbar"),
            )

        self.canvas.create_rectangle(
            x0, y0, x0 + bar_w, y0 + bar_h,
            outline=CANVAS_COLORBAR_BORDER_COLOR, width=1,
            tags=("screen", "colorbar"),
        )

        n_labels = 5
        for i in range(n_labels + 1):
            t = 1.0 - i / n_labels
            val = self.result_vmin + t * (self.result_vmax - self.result_vmin)
            yy = y0 + i * bar_h / n_labels
            self.canvas.create_text(
                x0 - 5, yy, text=self._fmt_colorbar_value(val),
                fill="white", font=("Consolas", 7), anchor=tk.E,
                tags=("screen", "colorbar"),
            )

        # Titulo: resultado + unidad del sistema activo entre corchetes
        # (estilo profesional). El alumno lee la escala con su unidad real.
        title = self.result_label
        if self.result_unit:
            title = f"{title} [{self.result_unit}]"
        self.canvas.create_text(
            x0 + bar_w / 2, y0 - 12, text=title,
            fill="white", font=("Segoe UI", 8, "bold"), anchor=tk.S,
            tags=("screen", "colorbar"),
        )

    @staticmethod
    def _fmt_colorbar_value(val):
        """Formatea un valor de la colorbar de forma profesional: notacion
        cientifica para magnitudes grandes/chicas (un esfuerzo de 25 MPa en Pa
        es 2.5e7, ilegible como '25000000.00'), decimal compacto en el medio.
        """
        a = abs(val)
        if a != 0.0 and (a >= 1e5 or a < 1e-3):
            return f"{val:.2e}"
        return f"{val:.4g}"

    # ═════════════════════════════════════════════════════════════════════
    # EVENTOS — control de interaccion (pan/zoom/resize)
    # ═════════════════════════════════════════════════════════════════════
    #
    # Patron de viewport rapido:
    #
    # - PAN (Button-2/3 drag): _on_pan_move usa canvas.move("all", dx, dy)
    #   + canvas.move("screen", -dx, -dy). Cero rasterizacion, cero
    #   Python loops por evento. Lo unico que se recalcula es offset_x/y.
    #
    # - ZOOM (MouseWheel): _on_mousewheel entra en modo interaccion y
    #   hace un redraw a baja resolucion (n=3, sin isolineas). Tras
    #   150ms sin mas eventos, _exit_interaction_mode hace un redraw
    #   final de alta calidad. Multiples ticks coalescen en una sola
    #   rasterizacion completa.
    #
    # - RESIZE (<Configure>): _on_resize usa _request_redraw que coalesce
    #   varios eventos via after_idle en un solo redraw.
    #
    # - clear_results_overlay / set_displacements / etc. siguen llamando
    #   self.redraw() directo porque son acciones discretas, no rafagas.

    def _enter_interaction_mode(self):
        """Activa el modo "viewport en movimiento": el render baja la
        resolucion del gradient (n=3) y omite isolineas. Idempotente."""
        self._interacting = True

    def _exit_interaction_mode(self):
        """Sale del modo interaccion y dispara redraw final en alta
        calidad. Llamado por `_interaction_end_after_id`."""
        self._interaction_end_after_id = None
        self._interacting = False
        self.redraw()

    def _schedule_interaction_end(self, delay_ms=150):
        """Reprograma el "fin de interaccion": cancela el after pendiente
        si lo hay y agenda uno nuevo a `delay_ms`. Cada nuevo evento de
        zoom/resize que llame esto resetea el timer — solo cuando pasen
        `delay_ms` sin eventos se dispara el redraw final."""
        if self._interaction_end_after_id is not None:
            try:
                self.canvas.after_cancel(self._interaction_end_after_id)
            except Exception:
                pass
        self._interaction_end_after_id = self.canvas.after(
            delay_ms, self._exit_interaction_mode
        )

    def _request_redraw(self):
        """Encola un redraw via after_idle, coalesciendo multiples
        llamadas en una sola ejecucion. Util para handlers que se
        disparan en rafagas (resize, hover, etc.)."""
        if self._redraw_pending:
            return
        self._redraw_pending = True
        self.canvas.after_idle(self._do_pending_redraw)

    def _do_pending_redraw(self):
        self._redraw_pending = False
        self.redraw()

    def _on_mousewheel(self, event):
        """Zoom con la rueda. Estrategia (espejo del pan rapido):

        1. Actualiza offset/scale y entra en modo interaccion.
        2. **Sin redraw**. En su lugar:
           - `canvas.delete("gradient")` quita la imagen rasterizada vieja
             (no se puede escalar bitmap con canvas.scale, solo coords).
           - `canvas.scale("all", mx, my, factor, factor)` escala TODOS
             los items existentes hacia/desde el centro del cursor
             (isolineas, malla, nodos, cargas, BCs).
           - `canvas.scale("screen", mx, my, 1/factor, 1/factor)` deshace
             el escalado en los items anclados a pantalla (colorbar, ejes).
           - `_draw_gradient_scaled()` repinta el campo con PIL.Image.resize
             en la nueva posicion (sin re-rasterizar barycentricas).
        3. `_schedule_interaction_end(150)`: tras 150ms sin mas wheel,
           dispara redraw completo (regenera grid con nuevo spacing y
           re-rasteriza el campo a resolucion exacta).

        Resultado: isolineas + malla + nodos siempre visibles, escalando
        suavemente con la rueda. No hay parpadeo. Al detenerse, todo
        se afina a la resolucion correcta.
        """
        factor = 1.1 if event.delta > 0 else 0.9
        mx, my = event.x, event.y
        self.offset_x = mx - factor * (mx - self.offset_x)
        self.offset_y = my - factor * (my - self.offset_y)
        self.scale *= factor
        self._enter_interaction_mode()

        # Eliminamos el bitmap viejo: canvas.scale solo afecta coords, no
        # el tamaño de PhotoImages. Si lo dejamos, queda con su tamaño
        # original mientras la malla escala — visualmente roto.
        self.canvas.delete("gradient")

        # Escalar todo geometricamente hacia/desde el cursor.
        # Tk hace esto en C: muchisimo mas rapido que un redraw completo.
        self.canvas.scale("all", mx, my, factor, factor)
        # Deshacer el escalado en items de pantalla (colorbar, axes, grid).
        self.canvas.scale("screen", mx, my, 1.0 / factor, 1.0 / factor)

        # Repintar el campo escalado en su nueva posicion (PIL.Image.resize
        # del bitmap previo, sin re-rasterizar el campo desde cero).
        if self.result_values or self.element_result_grid:
            self._draw_gradient_scaled()

        self._schedule_interaction_end()

    def _on_pan_start(self, event):
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        # Marcar que estamos en una sesion de pan: el _on_pan_release
        # disparara un redraw final para re-rasterizar el gradient con
        # el offset nuevo (cubre los elementos que entraron al viewport
        # durante el drag y no estaban en la imagen cacheada).
        self._panning = True

    def _on_pan_move(self, event):
        """Pan rapido SIN redraw. Estrategia (Opcion B):

        - `canvas.move("all", dx, dy)` traslada TODOS los items existentes
          incluyendo la imagen rasterizada del gradient. Es O(items) en C,
          sin recomputar nada en Python.
        - `canvas.move("screen", -dx, -dy)` deshace el move sobre los items
          anclados a pantalla (colorbar, axes, grid) para que se queden en
          su lugar.
        - Actualiza offset_x/y para que el proximo redraw (cuando ocurra)
          coloque los items en la posicion correcta. El cache del gradient
          NO se invalida porque su key no depende del offset.

        El pan se siente instantaneo aun con mallas de >1000 elementos.
        El gradient queda "recortado" al area visible original mientras
        dura el drag — se completa en _on_pan_release re-rasterizando.
        """
        dx = event.x - self._pan_start_x
        dy = event.y - self._pan_start_y
        if dx == 0 and dy == 0:
            return
        self.offset_x += dx
        self.offset_y += dy
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self.canvas.move("all", dx, dy)
        # Re-anclar items de pantalla (colorbar, ejes, grid wallpaper) a
        # su posicion absoluta. Como Tk acumula el move sobre las coords
        # del item, deshacemos con el delta opuesto.
        self.canvas.move("screen", -dx, -dy)

    def _on_pan_release(self, event):
        """Al soltar el boton de pan, dispara un redraw completo.

        Razon: durante el drag el gradient se traslado con canvas.move
        pero su area rasterizada solo cubre lo que era visible cuando se
        rasterizo. Los elementos que entraron al viewport durante el pan
        quedan sin color (banda negra). Este redraw re-rasteriza con el
        offset acumulado y completa la imagen. Se invalida la cache
        forzando rerasterizacion (el offset cambio "lo suficiente").

        Tambien re-dibuja el grid wallpaper para que se alinee con el
        nuevo offset (la formula `offset_x % spacing` cambia la fase).
        """
        if not getattr(self, "_panning", False):
            return
        self._panning = False
        # Invalidar cache del gradient: ahora SI queremos rerasterizar
        # para cubrir las zonas que quedaron sin color tras el drag.
        self._gradient_cache_key = None
        self.redraw()

    def _on_resize(self, event):
        """Redraw al redimensionar la ventana, pero throttled con
        after_idle para coalescer rafagas de eventos <Configure> (Tk
        dispara uno por cada pixel durante un drag de resize)."""
        self._request_redraw()

    def _on_mouse_move(self, event):
        wx, wy = self.screen_to_world(event.x, event.y)
        self.coord_label.config(
            text=f"x: {fmt(wx, 'length')}  y: {fmt(wy, 'length')}"
        )
        # Hook educativo: si hay un listener de hover-elemento (M0 lo usa
        # para el radar flotante), notificar cuando el elemento bajo el
        # cursor cambia. Throttling implicito: solo emitimos cuando el id
        # cambia, no en cada pixel.
        if self.on_hover_element is not None:
            elem_under = self._hit_test_element_at(wx, wy)
            if elem_under != self._hover_elem_id:
                self._hover_elem_id = elem_under
                try:
                    self.on_hover_element(elem_under, event.x, event.y)
                except Exception:
                    pass

        # Realce de hover (pre-seleccion): outline del elemento bajo el cursor
        # en cian + su numero, aunque la numeracion global este apagada
        # (patron "query" de Abaqus/ANSYS). Auditoria UX 2026-05.
        self._update_hover_highlight(wx, wy)
        # Modo dibujo: detectar snap a corner existente y refrescar
        # preview. Throttling: solo redraw si cambia el snap candidate o
        # hay puntos pendientes (linea preview al cursor).
        if self.draw_mode_active:
            self._last_cursor_xy = (event.x, event.y)
            # Cachear el bitmask para que el preview pueda saber si Shift
            # esta presionado sin recibir el evento explicitamente.
            new_state = getattr(event, "state", 0) or 0
            state_changed = new_state != self._last_event_state
            self._last_event_state = new_state
            new_snap = self._draw_hit_test_corner(event.x, event.y)
            # Redraw si cambio el snap, hay puntos pendientes (linea preview
            # se mueve), o si Shift cambio mientras hay puntos pendientes
            # (la proyeccion ortho aparece/desaparece).
            if (new_snap != self.draw_hover_snap or self.draw_pending
                    or (state_changed and self.draw_pending)):
                self.draw_hover_snap = new_snap
                # Solo cambió el preview de dibujo (tag "draw_preview"): refrescar
                # SOLO esa capa en vez de rasterizar toda la malla por cada pixel
                # del cursor. _draw_pending_overlay() es autocontenido (polígono
                # parcial + línea al cursor + anillo de snap).
                self.canvas.delete("draw_preview")
                self._draw_pending_overlay()

    def _hover_enabled(self):
        """True si el realce de hover debe operar en el estado actual.

        Se inhibe durante modos que tienen su propia semantica de cursor o
        que no quieren ruido amarillo/cian sobre la malla: modo dibujo,
        consulta del Post (probe), overlays educativos (M0..M7), modo
        fantasma, y mientras el viewport esta en movimiento. Tambien en
        mallas enormes (> 3000 elem) para no pagar el hit-test por pixel.
        """
        if (self.draw_mode_active or self.probe_mode_active
                or self._phase == "post"      # Post no resalta elementos
                or self.ghost_geometry or self._overlay_layers
                or self._interacting or self._panning):
            return False
        return len(self.project.elements) <= 3000

    def _update_hover_highlight(self, wx, wy):
        """Dibuja/actualiza el outline del elemento bajo el cursor (capa
        'hover'). Solo redibuja la capa cuando el elemento cambia — cero
        costo de redraw global por pixel."""
        if not self._hover_enabled():
            if self._hover_highlight_eid is not None:
                self.canvas.delete("hover")
                self._hover_highlight_eid = None
            return
        # Fast-path: si el cursor sigue dentro del elemento ya resaltado, no
        # rehacer el hit-test global (O(n)) — un solo point-in-quad basta.
        # Hovering DENTRO de un elemento es el caso comun (muchos eventos).
        cur = self._hover_highlight_eid
        if cur is not None:
            elem = self.project.elements.get(cur)
            if elem is not None:
                try:
                    pts = [(self.project.nodes[n].x, self.project.nodes[n].y)
                           for n in elem.node_ids[:4]]
                    if self._point_in_quad(wx, wy, pts):
                        return
                except KeyError:
                    pass
        eid = self._hit_test_element_at(wx, wy)
        if eid == self._hover_highlight_eid:
            return
        self._hover_highlight_eid = eid
        self.canvas.delete("hover")
        if eid is None:
            return
        elem = self.project.elements.get(eid)
        if elem is None:
            return
        # No realzar el que ya esta seleccionado (su amarillo ya domina).
        if eid in self.selected_elements:
            return
        coords = []
        for nid in elem.node_ids[:4]:
            if nid not in self.project.nodes:
                return
            sx, sy = self._get_node_screen_pos(nid)
            coords.extend([sx, sy])
        self.canvas.create_polygon(
            *coords, outline=CANVAS_HOVER_COLOR, fill="", width=2,
            tags=("world", "hover"),
        )
        # Numero del elemento bajo el cursor (query), aunque la numeracion
        # global este apagada.
        cx = sum(coords[::2]) / 4
        cy = sum(coords[1::2]) / 4
        self.canvas.create_text(
            cx, cy, text=str(eid), fill=CANVAS_HOVER_COLOR,
            font=("Segoe UI", CANVAS_FONT_SIZE, "bold"), anchor=tk.CENTER,
            tags=("world", "hover"),
        )

    def _on_canvas_leave(self, _event):
        """Limpia el realce de hover al salir el cursor del canvas."""
        if self._hover_highlight_eid is not None:
            self.canvas.delete("hover")
            self._hover_highlight_eid = None

    # ─── Hit-tests para cargas / restricciones / surface ────────────────

    def _hit_test_load(self, sx, sy, tol_px=18):
        """Devuelve node_id si hay una carga cuyo nodo asociado este a < tol."""
        best = None
        best_d = float("inf")
        for load in self.project.nodal_loads.values():
            if load.node_id not in self.project.nodes:
                continue
            nsx, nsy = self._get_node_screen_pos(load.node_id)
            d = ((nsx - sx) ** 2 + (nsy - sy) ** 2) ** 0.5
            if d < tol_px and d < best_d:
                best_d = d
                best = load.node_id
        return best

    def _hit_test_constraint(self, sx, sy, tol_px=18):
        """Devuelve node_id de la restriccion mas cercana al click."""
        best = None
        best_d = float("inf")
        for bc in self.project.boundary_conditions.values():
            if bc.node_id not in self.project.nodes:
                continue
            nsx, nsy = self._get_node_screen_pos(bc.node_id)
            d = ((nsx - sx) ** 2 + (nsy - sy) ** 2) ** 0.5
            if d < tol_px and d < best_d:
                best_d = d
                best = bc.node_id
        return best

    def _hit_test_surface(self, sx, sy, tol_px=12):
        """Devuelve idx de surface_load cuyo segmento contenga al click."""
        best = None
        best_d = float("inf")
        for idx, sl in enumerate(self.project.surface_loads):
            if (sl.node_start not in self.project.nodes
                    or sl.node_end not in self.project.nodes):
                continue
            x1, y1 = self._get_node_screen_pos(sl.node_start)
            x2, y2 = self._get_node_screen_pos(sl.node_end)
            d = self._point_segment_distance(sx, sy, x1, y1, x2, y2)
            if d < tol_px and d < best_d:
                best_d = d
                best = idx
        return best

    def _hit_test_potential_edge(self, sx, sy, tol_px=10):
        """Devuelve `frozenset({n1, n2})` de la arista corner-to-corner
        mas cercana al click, o None. Itera todas las aristas de los
        elementos (deduplicadas por frozenset). Solo considera corners
        macro -- mid/center Q9 quedan fuera. Usado en sub-pestaña
        Carg. Superf. para detectar la arista a poner una surface load."""
        if not self.project.elements:
            return None
        roles = classify_nodes(self.project)
        seen_edges = set()
        best = None
        best_d = float("inf")
        for elem in self.project.elements.values():
            corners = [n for n in elem.node_ids[:4]
                       if roles.get(n, "corner") == "corner"]
            if len(corners) < 2:
                continue
            for i in range(len(corners)):
                a = corners[i]
                b = corners[(i + 1) % len(corners)]
                if a not in self.project.nodes or b not in self.project.nodes:
                    continue
                edge = frozenset({a, b})
                if edge in seen_edges:
                    continue
                seen_edges.add(edge)
                ax, ay = self.world_to_screen(
                    self.project.nodes[a].x, self.project.nodes[a].y)
                bx, by = self.world_to_screen(
                    self.project.nodes[b].x, self.project.nodes[b].y)
                d = self._point_segment_distance(sx, sy, ax, ay, bx, by)
                if d < tol_px and d < best_d:
                    best_d = d
                    best = edge
        return best

    def _edge_has_existing_surface(self, edge):
        """True si ya existe un SurfaceLoad sobre esa arista (en cualquier
        direccion). edge = frozenset({n1, n2})."""
        for sl in self.project.surface_loads:
            if frozenset({sl.node_start, sl.node_end}) == edge:
                return True
        return False

    @staticmethod
    def _point_segment_distance(px, py, x1, y1, x2, y2):
        """Distancia minima de (px,py) al segmento (x1,y1)-(x2,y2)."""
        dx = x2 - x1
        dy = y2 - y1
        L2 = dx * dx + dy * dy
        if L2 < 1e-9:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        t = ((px - x1) * dx + (py - y1) * dy) / L2
        t = max(0.0, min(1.0, t))
        cx = x1 + t * dx
        cy = y1 + t * dy
        return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5

    def _on_click(self, event):
        # Modo dibujo intercepta el click: snap a corner existente o
        # abrir Entry flotante para coord explicita.
        if self.draw_mode_active:
            self._on_draw_click(event)
            return

        # Post-Proceso: NO hay seleccion de elementos. La inspeccion del campo
        # es por probe (puntual — su propio handler add="+" pinea) y contorno,
        # nunca por seleccion de elemento — que ademas taparia el contorno con
        # su relleno. Decision 2026-05-31 (pedido del usuario: la seleccion en
        # Post "no cambiaba" e interferia). Vale para todo el Post, este o no
        # el probe activo.
        if self._phase == "post":
            return

        # Click consumers (modulos educativos: snap a Gauss, drag de
        # nodo). Iteramos sobre snapshot para que un consumer que se
        # auto-desregistra no rompa el loop. Si alguno consume, NO
        # ejecutamos el hit-test estandar — el modulo ya manejo el
        # click. Esto evita la oscilacion "se prende/apaga" del panel
        # de modulos cuando el alumno clickea sobre un punto Gauss del
        # elemento bajo analisis (select_element con was_only=True lo
        # deseleccionaba).
        for consumer in list(self._click_consumers):
            try:
                if consumer(event):
                    return
            except Exception:
                pass

        sx, sy = event.x, event.y
        wx, wy = self.screen_to_world(sx, sy)
        # Detectar modifiers: Ctrl agrega/quita del set, Shift extiende
        # rango (solo nodos). state bit 0x0004 = Control, 0x0001 = Shift.
        additive = bool(event.state & 0x0004)
        range_to = bool(event.state & 0x0001)

        # Determinar la sub-pestaña activa para priorizar el hit-test
        # de arista potencial (solo cuando estamos en Carg. Superf.).
        active_subtab = self._get_active_subtab_kind()

        # Si Carg. Superf. esta activa, priorizar arista potencial sobre
        # nodo (el contexto manda).
        if active_subtab == "surface":
            edge = self._hit_test_potential_edge(sx, sy)
            if edge is not None:
                # Si la arista YA tiene una surface existente, prefer
                # seleccionar la surface real (comportamiento normal).
                # Sino, marcar la arista como potencial (fantasma).
                if not self._edge_has_existing_surface(edge):
                    self.select_edge(edge, additive=additive)
                    self.main_window.set_status(
                        f"Arista {tuple(sorted(edge))} seleccionada "
                        f"(crea Carga Superficial)"
                    )
                    return

        # Prioridad 1: Carga (flecha visible — clickearla es lo natural)
        nid = self._hit_test_load(sx, sy)
        if nid is not None:
            # Para que el halo del nodo asociado se vea, lo agregamos
            # al set de nodos ANTES del emit. Un solo emit + redraw.
            if additive:
                if nid in self.selected_loads:
                    self.selected_loads.discard(nid)
                    self.selected_nodes.discard(nid)
                else:
                    self.selected_loads.add(nid)
                    self.selected_nodes.add(nid)
            else:
                # Click normal: si la carga ya era la unica seleccionada,
                # deseleccionar todo. Sino, reemplazar.
                was_only = (self.selected_loads == {nid})
                self._clear_all_sets_silent()
                if not was_only:
                    self.selected_loads.add(nid)
                    self.selected_nodes.add(nid)
            self._emit_selection_changed()
            self.redraw()
            self.main_window.set_status(f"Carga en nodo {nid} seleccionada")
            return

        # Prioridad 2: Restriccion
        nid = self._hit_test_constraint(sx, sy)
        if nid is not None:
            if additive:
                if nid in self.selected_constraints:
                    self.selected_constraints.discard(nid)
                    self.selected_nodes.discard(nid)
                else:
                    self.selected_constraints.add(nid)
                    self.selected_nodes.add(nid)
            else:
                was_only = (self.selected_constraints == {nid})
                self._clear_all_sets_silent()
                if not was_only:
                    self.selected_constraints.add(nid)
                    self.selected_nodes.add(nid)
            self._emit_selection_changed()
            self.redraw()
            self.main_window.set_status(
                f"Restriccion en nodo {nid} seleccionada")
            return

        # Prioridad 3: Carga superficial existente
        idx = self._hit_test_surface(sx, sy)
        if idx is not None:
            self.select_surface(idx, additive=additive)
            # NOTA: no llamamos `on_surface_select` legacy — disparaba
            # `tree.selection_set` que generaba virtualevent async sin
            # guard, causando rebote. El callback unificado
            # `on_selection_changed` ya gestiona el feedback.
            self.main_window.set_status(f"Carga superficial #{idx} seleccionada")
            return

        # Prioridad 4: Nodo
        min_dist = float("inf")
        closest_node = None
        for nid, node in self.project.nodes.items():
            dx = node.x - wx
            dy = node.y - wy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < min_dist:
                min_dist = dist
                closest_node = nid

        threshold = 15 / self.scale
        if closest_node and min_dist < threshold:
            self.select_node(closest_node, additive=additive,
                             range_to=range_to)
            self.main_window.set_status(
                f"Nodo {closest_node} seleccionado "
                f"({fmt(self.project.nodes[closest_node].x, 'length')}, "
                f"{fmt(self.project.nodes[closest_node].y, 'length')})"
            )
            return

        # Prioridad 5: Arista potencial (cuando NO estamos en Carg.
        # Superf., el hit-test de arista igual sirve para seleccionar
        # entre 2 corners visibles si nada mas le hizo match arriba —
        # pero solo si el contexto es coherente: por ahora, solo en
        # surface. En otras sub-pestañas, ignoramos.
        if active_subtab == "surface":
            edge = self._hit_test_potential_edge(sx, sy)
            if edge is not None and not self._edge_has_existing_surface(edge):
                self.select_edge(edge, additive=additive)
                self.main_window.set_status(
                    f"Arista {tuple(sorted(edge))} seleccionada"
                )
                return

        # Prioridad 6: Elemento (point-in-quad)
        for elem in self.project.elements.values():
            nids = elem.node_ids[:4]
            pts = []
            valid = True
            for n in nids:
                if n not in self.project.nodes:
                    valid = False
                    break
                pts.append((self.project.nodes[n].x, self.project.nodes[n].y))
            if not valid:
                continue
            if self._point_in_quad(wx, wy, pts):
                self.select_element(elem.id, additive=additive)
                self.main_window.set_status(f"Elemento {elem.id} seleccionado")
                return

        # Click en zona vacia: deselecciona todo (estandar file explorer).
        # Ctrl+Click y Shift+Click en vacio NO deseleccionan: el usuario
        # queria agregar al set, fallo el target — preservar la seleccion
        # actual es lo menos sorprendente.
        if not (additive or range_to):
            if any(self.get_selection().values()):
                self.clear_highlights()
                self.main_window.set_status("Seleccion limpiada")

    def _get_active_subtab_kind(self):
        """Retorna 'nodes' | 'elements' | 'loads' | 'constraints' |
        'surface' | None segun la sub-pestaña activa del data_notebook
        del pre_tab. None si no se puede determinar (ej. sub-pestaña
        Educacion o spreadsheet aun no construido)."""
        try:
            pre_tab = self.main_window.pre_tab
            current = pre_tab.data_notebook.select()
            if current == str(pre_tab.nodes_frame):
                return "nodes"
            if current == str(pre_tab.elements_frame):
                return "elements"
            if current == str(pre_tab.loads_frame):
                return "loads"
            if current == str(pre_tab.constraints_frame):
                return "constraints"
            if current == str(pre_tab.surface_frame):
                return "surface"
        except (AttributeError, tk.TclError):
            pass
        return None

    def _point_in_quad(self, px, py, pts):
        n = len(pts)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if ((yi > py) != (yj > py)) and \
               (px < (xj - xi) * (py - yi) / (yj - yi + 1e-15) + xi):
                inside = not inside
            j = i
        return inside

    def _hit_test_element_at(self, wx, wy):
        """Retorna elem_id bajo coords-mundo (wx, wy) o None.

        Solo considera los 4 vertices macro (Q4/Q9 igual). No itera nodos
        intermedios. Usado por el hook on_hover_element (M0 radar).
        """
        for elem in self.project.elements.values():
            nids = elem.node_ids[:4]
            try:
                pts = [(self.project.nodes[n].x, self.project.nodes[n].y)
                       for n in nids]
            except KeyError:
                continue
            if self._point_in_quad(wx, wy, pts):
                return elem.id
        return None

    # ═════════════════════════════════════════════════════════════════════
    # METODOS PUBLICOS
    # ═════════════════════════════════════════════════════════════════════

    # ─── API publica de seleccion (single + multi) ─────────────────────
    #
    # Todos los `highlight_*` legacy ahora delegan a `select_*` con
    # `additive=False` (replace), manteniendo el comportamiento single
    # de antes. `select_*(additive=True)` agrega/quita del set; con
    # `range_to=True` hace range-select entre el ultimo anchor y el
    # nuevo (solo nodos).
    # ──────────────────────────────────────────────────────────────────

    def _emit_selection_changed(self):
        """Sincroniza los `highlighted_*` singulares (compat) con los
        sets actuales y dispara el callback unificado."""
        # Sincronizar compat singulares: si hay >1, queda None (no hay
        # "uno seleccionado"); si hay 1, ese; si 0, None.
        def _single(s):
            return next(iter(s)) if len(s) == 1 else None
        self.highlighted_node = _single(self.selected_nodes)
        self.highlighted_element = _single(self.selected_elements)
        self.highlighted_load = _single(self.selected_loads)
        self.highlighted_constraint = _single(self.selected_constraints)
        self.highlighted_surface = _single(self.selected_surfaces)
        if self.on_selection_changed:
            try:
                self.on_selection_changed(self.get_selection())
            except Exception:
                pass

    def get_selection(self):
        """Retorna copia de todos los sets de seleccion como dict."""
        return {
            "nodes": set(self.selected_nodes),
            "elements": set(self.selected_elements),
            "edges": set(self.selected_edges),
            "loads": set(self.selected_loads),
            "constraints": set(self.selected_constraints),
            "surfaces": set(self.selected_surfaces),
        }

    # Click normal (no-additive, no-range) sobre un item que YA es el
    # unico seleccionado en su set deselecciona TODO. Si el set tenia
    # >1 item o el clickeado no estaba, reemplaza con solo ese.
    # Comportamiento estandar de file explorers (toggle por re-click).

    def select_node(self, node_id, *, additive=False, range_to=False):
        """Selecciona un nodo. Si `additive=True` (Ctrl+Click), togglea
        en el set. Si `range_to=True` (Shift+Click), agrega el rango.
        Sino (click normal): reemplaza el set, o deselecciona si el
        clickeado era el unico ya seleccionado."""
        if range_to and self._last_node_anchor is not None \
                and self._last_node_anchor in self.project.nodes \
                and node_id in self.project.nodes:
            lo = min(self._last_node_anchor, node_id)
            hi = max(self._last_node_anchor, node_id)
            range_ids = {nid for nid in self.project.nodes if lo <= nid <= hi}
            self.selected_nodes |= range_ids
        elif additive:
            if node_id in self.selected_nodes:
                self.selected_nodes.discard(node_id)
            else:
                self.selected_nodes.add(node_id)
        else:
            was_only = (self.selected_nodes == {node_id})
            self._clear_all_sets_silent()
            if not was_only:
                self.selected_nodes.add(node_id)
        self._last_node_anchor = node_id
        self._emit_selection_changed()
        self.redraw()

    def select_element(self, elem_id, *, additive=False):
        if additive:
            if elem_id in self.selected_elements:
                self.selected_elements.discard(elem_id)
            else:
                self.selected_elements.add(elem_id)
        else:
            was_only = (self.selected_elements == {elem_id})
            # Suprimir "second-click deselects" si hay un módulo overlay
            # educativo activo en este main_window. Mientras el módulo
            # vive, el elemento bajo análisis es el contrato implícito —
            # clickearlo de nuevo no debe perder el contexto. Para limpiar
            # explícitamente: Esc, click en zona vacía, o cerrar el módulo.
            # Import diferido para no acoplar el canvas al package education.
            if was_only:
                try:
                    from education.overlay_module import is_any_overlay_active
                    if is_any_overlay_active(self.main_window):
                        was_only = False
                except Exception:
                    pass
            self._clear_all_sets_silent()
            if not was_only:
                self.selected_elements.add(elem_id)
        self._emit_selection_changed()
        self.redraw()

    def select_edge(self, edge, *, additive=False):
        """edge = frozenset({n1, n2}). Selecciona una arista potencial."""
        if not isinstance(edge, frozenset):
            edge = frozenset(edge)
        if additive:
            if edge in self.selected_edges:
                self.selected_edges.discard(edge)
            else:
                self.selected_edges.add(edge)
        else:
            was_only = (self.selected_edges == {edge})
            self._clear_all_sets_silent()
            if not was_only:
                self.selected_edges.add(edge)
        self._emit_selection_changed()
        self.redraw()

    def select_load(self, node_id, *, additive=False):
        if additive:
            if node_id in self.selected_loads:
                self.selected_loads.discard(node_id)
            else:
                self.selected_loads.add(node_id)
        else:
            was_only = (self.selected_loads == {node_id})
            self._clear_all_sets_silent()
            if not was_only:
                self.selected_loads.add(node_id)
        self._emit_selection_changed()
        self.redraw()

    def select_constraint(self, node_id, *, additive=False):
        if additive:
            if node_id in self.selected_constraints:
                self.selected_constraints.discard(node_id)
            else:
                self.selected_constraints.add(node_id)
        else:
            was_only = (self.selected_constraints == {node_id})
            self._clear_all_sets_silent()
            if not was_only:
                self.selected_constraints.add(node_id)
        self._emit_selection_changed()
        self.redraw()

    def select_surface(self, idx, *, additive=False):
        if not (0 <= idx < len(self.project.surface_loads)):
            return
        if additive:
            if idx in self.selected_surfaces:
                self.selected_surfaces.discard(idx)
            else:
                self.selected_surfaces.add(idx)
        else:
            was_only = (self.selected_surfaces == {idx})
            self._clear_all_sets_silent()
            if not was_only:
                self.selected_surfaces.add(idx)
        self._emit_selection_changed()
        self.redraw()

    def replace_node_selection(self, node_ids):
        """Reemplaza la seleccion de nodos por el set dado (sin emitir
        callback recursivo si la fuente es un spreadsheet sync)."""
        self._clear_all_sets_silent()
        self.selected_nodes = set(int(n) for n in node_ids)
        self._emit_selection_changed()
        self.redraw()

    def replace_element_selection(self, elem_ids):
        self._clear_all_sets_silent()
        self.selected_elements = set(int(e) for e in elem_ids)
        self._emit_selection_changed()
        self.redraw()

    def _clear_all_sets_silent(self):
        """Vacia todos los sets sin emitir callback. Helper interno
        para los `select_*` no-additive."""
        self.selected_nodes.clear()
        self.selected_elements.clear()
        self.selected_edges.clear()
        self.selected_loads.clear()
        self.selected_constraints.clear()
        self.selected_surfaces.clear()

    # ─── Wrappers legacy single-select (compat) ────────────────────────

    def clear_highlights(self):
        """Limpia toda la seleccion (single + multi)."""
        self._clear_all_sets_silent()
        self._last_node_anchor = None
        self._emit_selection_changed()
        self.redraw()

    # ═════════════════════════════════════════════════════════════════════
    # CAPA EDUCATIVA — overlay layers + hooks
    # ═════════════════════════════════════════════════════════════════════
    #
    # Los modulos educativos en modo overlay (M0/M2/M3/M6) y vistas del
    # Post (probe_overlay) usan estos hooks para pintar capas SOBRE la
    # malla sin abrir ventana.
    # Reglas:
    #   - Cada modulo registra UN solo layer al activarse y lo quita al
    #     cerrar el overlay. El layer es un callable(canvas) que dibuja
    #     usando self.canvas.create_* con tags propios.
    #   - El modulo es responsable de borrar sus tags (ej. canvas.delete(
    #     "edu_m2")) ANTES de redibujar, o de simplemente dejar que el
    #     proximo redraw() global limpie todo (canvas.delete("all") en la
    #     primera linea de redraw).
    #   - Un solo modulo overlay activo a la vez es el patron tipico, pero
    #     la API soporta multiples capas concurrentes (apilamiento por
    #     orden de registro).
    # ═════════════════════════════════════════════════════════════════════

    def add_click_consumer(self, callback):
        """Registra un consumer de click. callable(event) -> bool.

        Se invoca al inicio de `_on_click` (en orden de registro). Si
        retorna True, el hit-test estandar del canvas NO se ejecuta —
        el consumer asumio responsabilidad sobre ese click.

        Uso tipico: modulos educativos en modo overlay que necesitan
        snap a punto Gauss / inicio de drag SIN disparar la rama
        "second-click deselects" de select_element() cuando el alumno
        clickea sobre el elemento ya seleccionado.

        Idempotente: no duplica registros.
        """
        if callback is not None and callback not in self._click_consumers:
            self._click_consumers.append(callback)

    def remove_click_consumer(self, callback):
        """Quita un click consumer registrado (no falla si no existia)."""
        if callback in self._click_consumers:
            self._click_consumers.remove(callback)

    def add_overlay_layer(self, layer):
        """Registra una capa de dibujo educativa.

        `layer` es callable(canvas) -> None. Se ejecuta al final de cada
        redraw(), despues del dibujo principal. Idempotente: si la capa
        ya esta registrada no se duplica.
        """
        if layer is None or layer in self._overlay_layers:
            return
        self._overlay_layers.append(layer)
        self.redraw()

    def remove_overlay_layer(self, layer):
        """Quita una capa registrada (no falla si no existia)."""
        if layer in self._overlay_layers:
            self._overlay_layers.remove(layer)
            self.redraw()

    def clear_overlay_layers(self):
        """Borra TODAS las capas educativas. Util cuando se cierran
        multiples overlays a la vez (cambio de fase, undo/redo)."""
        if self._overlay_layers:
            self._overlay_layers.clear()
            self.redraw()

    def _on_delete_key(self, event=None):
        """Handler de Supr/BackSpace sobre el canvas: elimina el item
        actualmente highlighted, en orden de prioridad load > constraint
        > surface > element > node (mismo orden que el hit-test del click).

        Caso especial AutoCAD-style: en modo dibujo con puntos pendientes,
        BackSpace pop-ea el ultimo vertice del elemento en construccion
        (equivalente al `U` de AutoCAD dentro de un comando). Solo aplica
        cuando el Entry flotante NO esta abierto (sino la tecla pertenece
        al Entry para borrar caracteres). Esc sigue siendo "cancelar
        elemento entero".
        """
        # Backspace durante modo dibujo: pop del ultimo punto pendiente.
        if (event is not None and getattr(event, "keysym", "") == "BackSpace"
                and self.draw_mode_active and self.draw_pending
                and self._draw_entry is None):
            self.draw_pending.pop()
            self.draw_hover_snap = None
            n_left = len(self.draw_pending)
            self.main_window.set_status(
                f"Punto {n_left + 1} descartado — vertice {n_left + 1}/"
                f"{self.draw_target_count} pendiente"
            )
            self.redraw()
            return "break"

        from tkinter import messagebox

        # Helper para capturar undo snapshot antes de mutar
        def _capture(label):
            try:
                stack = getattr(self.main_window, "undo_stack", None)
                if stack is not None:
                    stack.capture(label)
            except Exception:
                pass

        # Prioridad: lo mas especifico primero
        if self.highlighted_load is not None:
            nid = self.highlighted_load
            _capture(f"eliminar carga en nodo {nid} (canvas)")
            self.project.remove_nodal_load(nid)
            self.highlighted_load = None
            self._fire_delete_callback("load", nid,
                                       f"Carga en nodo {nid} eliminada.")
            return

        if self.highlighted_constraint is not None:
            nid = self.highlighted_constraint
            _capture(f"eliminar restriccion en nodo {nid} (canvas)")
            if hasattr(self.project, "remove_boundary_condition"):
                self.project.remove_boundary_condition(nid)
            elif nid in self.project.boundary_conditions:
                del self.project.boundary_conditions[nid]
                self.project.is_modified = True
                self.project.is_solved = False
            self.highlighted_constraint = None
            self._fire_delete_callback("constraint", nid,
                                       f"Restriccion en nodo {nid} eliminada.")
            return

        if self.highlighted_surface is not None:
            idx = self.highlighted_surface
            _capture(f"eliminar carga superficial #{idx} (canvas)")
            if 0 <= idx < len(self.project.surface_loads):
                del self.project.surface_loads[idx]
                self.project.is_modified = True
                self.project.is_solved = False
            self.highlighted_surface = None
            self._fire_delete_callback("surface", idx,
                                       f"Carga superficial #{idx} eliminada.")
            return

        if self.highlighted_element is not None:
            eid = self.highlighted_element
            elem = self.project.elements.get(eid)
            if elem is None:
                return
            # Pre-calcular el efecto del auto-cleanup para mostrar en el modal
            preview = self._preview_element_cleanup(eid)
            msg_parts = [f"¿Eliminar el elemento {eid}?"]
            if preview["nodes_to_delete"] or preview["nodes_to_preserve"]:
                msg_parts.append("")
                if preview["nodes_to_delete"]:
                    msg_parts.append(
                        f"  • Se auto-eliminaran {len(preview['nodes_to_delete'])} "
                        f"nodo(s) sin referencias: "
                        f"{preview['nodes_to_delete']}"
                    )
                if preview["nodes_to_preserve"]:
                    msg_parts.append(
                        f"  • Se preservaran {len(preview['nodes_to_preserve'])} "
                        f"nodo(s) huerfano(s) con cargas/restricciones: "
                        f"{preview['nodes_to_preserve']}"
                    )
            resp = messagebox.askyesno(
                "Eliminar elemento", "\n".join(msg_parts), parent=self.canvas,
            )
            if not resp:
                return
            _capture(f"eliminar elemento {eid} (canvas)")
            summary = self.project.remove_element(eid)
            self.highlighted_element = None
            parts = [f"Elemento {eid} eliminado"]
            if summary.get("nodes_deleted"):
                parts.append(
                    f"{len(summary['nodes_deleted'])} nodo(s) auto-eliminado(s)"
                )
            if summary.get("nodes_preserved"):
                parts.append(
                    f"{len(summary['nodes_preserved'])} nodo(s) preservado(s) "
                    f"como huerfano(s)"
                )
            self._fire_delete_callback("element", eid, ". ".join(parts) + ".")
            return

        if self.highlighted_node is not None:
            nid = self.highlighted_node
            # Cascade simetrico al de elementos: si el nodo pertenece a uno
            # o mas elementos, mostrar preview del impacto y pedir
            # confirmacion. Si esta huerfano y tiene datos, confirmar la
            # perdida de esos datos. Si esta limpio, borrar directo.
            preview = self.project.preview_node_cascade(nid)
            elements_to_delete = preview["elements_to_delete"]
            nodes_to_delete = preview["nodes_to_delete"]
            nodes_to_preserve = preview["nodes_to_preserve"]
            has_self_data = (
                nid in self.project.nodal_loads
                or nid in self.project.boundary_conditions
                or any(sl.node_start == nid or sl.node_end == nid
                       for sl in self.project.surface_loads)
            )

            if elements_to_delete:
                # Cascade no trivial: confirmar con preview detallado.
                lines = [
                    f"Borrar el nodo {nid} eliminara en cascada:",
                    f"  • {len(elements_to_delete)} elemento(s): "
                    f"{', '.join(str(e) for e in elements_to_delete)}",
                ]
                if nodes_to_delete:
                    lines.append(
                        f"  • {len(nodes_to_delete)} nodo(s) auxiliar(es) "
                        f"sin datos del usuario"
                    )
                if nodes_to_preserve:
                    lines.append(
                        f"  • {len(nodes_to_preserve)} nodo(s) se preservaran "
                        f"como huerfanos (tienen cargas / restricciones / "
                        f"surface refs)"
                    )
                if has_self_data:
                    lines.append(
                        f"  • Datos del nodo {nid} (cargas/BCs/surface) "
                        f"se perderan"
                    )
                lines.append("\n¿Continuar?")
                if not messagebox.askyesno(
                    "Confirmar borrado en cascada",
                    "\n".join(lines), parent=self.canvas,
                ):
                    return
            elif has_self_data:
                # Sin elementos pero con datos del usuario: confirmar perdida.
                if not messagebox.askyesno(
                    "Eliminar nodo",
                    f"El nodo {nid} tiene datos asociados (carga, "
                    f"restriccion o carga superficial). Al eliminarlo se "
                    f"perderan esos datos.\n\n¿Continuar?",
                    parent=self.canvas,
                ):
                    return

            _capture(f"eliminar nodo {nid} (canvas)")
            summary = self.project.remove_node_with_cascade(nid)
            self.highlighted_node = None
            self.highlighted_element = None  # podria haberse borrado
            parts = [f"Nodo {nid} eliminado"]
            if summary.get("elements_deleted"):
                parts.append(
                    f"{len(summary['elements_deleted'])} elemento(s) "
                    f"auto-eliminado(s)"
                )
            if summary.get("nodes_deleted") and len(summary["nodes_deleted"]) > 1:
                # > 1 porque el target ya cuenta. Reportamos los extras.
                extras = len(summary["nodes_deleted"]) - 1
                parts.append(f"{extras} nodo(s) auxiliar(es) auto-eliminado(s)")
            if summary.get("nodes_preserved"):
                parts.append(
                    f"{len(summary['nodes_preserved'])} nodo(s) preservado(s) "
                    f"como huerfano(s)"
                )
            self._fire_delete_callback("node", nid, ". ".join(parts) + ".")
            return

    def _preview_element_cleanup(self, elem_id):
        """Delega en `ProjectModel.preview_element_cleanup` (fuente única,
        antes duplicada verbatim aquí y en pre_tab; ahora O(1) por nodo via
        el índice inverso del modelo)."""
        return self.project.preview_element_cleanup(elem_id)

    def _fire_delete_callback(self, kind, target_id, status_msg):
        """Dispara `on_canvas_delete` (si esta registrado) y muestra el
        mensaje en la status bar del main_window. Centraliza el
        boilerplate de los handlers de borrado."""
        if self.on_canvas_delete is not None:
            try:
                self.on_canvas_delete(kind, target_id)
            except Exception:
                pass
        try:
            self.main_window.set_status(status_msg)
        except Exception:
            pass
        self.redraw()

    def set_result_values(self, values, label="Resultado", unit=""):
        """Modo SUAVIZADO (nodal): valores promediados por nodo.

        Apaga el modo crudo si estaba activo: ambos modos son mutuamente
        excluyentes en el render. `unit` es la unidad del sistema activo
        (esfuerzo o longitud segun el resultado) que se muestra en la colorbar.
        """
        self.result_values = values
        self.element_result_grid = None  # apagar modo crudo
        self.result_label = label
        self.result_unit = unit
        vals = list(values.values())
        self.result_vmin = min(vals) if vals else 0
        self.result_vmax = max(vals) if vals else 1
        if self.result_vmin == self.result_vmax:
            self.result_vmax = self.result_vmin + 1
        self._select_colormap()
        self.redraw()

    def set_element_result_grid(self, element_grids, label="Resultado", unit=""):
        """Modo CRUDO: grillas pre-computadas por elemento.

        element_grids: dict {elem_id: ndarray(n+1, n+1)} donde grid[i, j]
            es el valor escalar en (xi=-1+2i/n, eta=-1+2j/n) ya evaluado
            via fem.probe_query.compute_raw_grid (campo real del MEF, no
            interpolacion lineal de corners). Para invariantes (VM, σ1,
            σ2) los valores ya estan computados POR PUNTO con los
            componentes σx/σy/τxy correctos -- evita el error de 50-800%
            que tenia el path bilineal de 4 corners.

        El render del filled gradient muestra los saltos en bordes entre
        elementos -- es la verdad del campo σ del MEF Galerkin.
        """
        self.element_result_grid = element_grids
        self.result_values = None  # apagar modo suavizado
        self.result_label = label
        self.result_unit = unit
        all_vals = np.concatenate(
            [np.asarray(g).flatten() for g in element_grids.values()]
        ) if element_grids else np.array([0.0, 1.0])
        self.result_vmin = float(all_vals.min())
        self.result_vmax = float(all_vals.max())
        if self.result_vmin == self.result_vmax:
            self.result_vmax = self.result_vmin + 1
        self._select_colormap()
        self.redraw()

    def set_deformed(self, displacements, scale=1.0):
        self.displacements = displacements
        if displacements is not None:
            max_disp = np.max(np.abs(displacements))
            if max_disp > 0:
                coords = np.array([
                    [self.project.nodes[n].x, self.project.nodes[n].y]
                    for n in sorted(self.project.nodes.keys())
                ])
                model_size = max(
                    coords[:, 0].max() - coords[:, 0].min(),
                    coords[:, 1].max() - coords[:, 1].min()
                )
                self.deform_scale = model_size * 0.1 / max_disp * scale
            else:
                self.deform_scale = 0
            self.show_deformed = True
        else:
            self.show_deformed = False
            self.deform_scale = 0
        self.redraw()

    def set_isolines(self, show, count=10):
        """Activa/desactiva isolineas con el numero de niveles."""
        self.show_isolines = show
        self.isoline_count = count
        self.redraw()

    def clear_results_overlay(self):
        """Resetea el overlay de resultados (deformada, mapa de color,
        isolineas) sin tocar el status bar. Llamar al volver de Post a
        Pre/Proc para que el canvas vuelva a mostrar solo geometria."""
        self.result_values = None
        self.element_result_grid = None
        self.result_label = ""
        self.result_unit = ""
        self.show_deformed = False
        self.displacements = None
        self.deform_scale = 0
        self.show_isolines = False
        self._gradient_cache_key = None  # invalidar cache al limpiar resultados
        # Tambien liberamos el PIL Image del bitmap previo. Sin esto, un
        # zoom suave posterior (con `_interacting=True`) mostraria el campo
        # viejo escalado hasta que un redraw full lo regenere.
        self._gradient_pil_image = None
        self._gradient_zoom_photo = None
        self.redraw()

    def fit_view(self):
        if not self.project.nodes:
            self.scale = 1.0
            self._reference_scale = self.scale
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            self.offset_x = w / 2
            self.offset_y = h / 2
            self.redraw()
            return

        xs = [n.x for n in self.project.nodes.values()]
        ys = [n.y for n in self.project.nodes.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        margin = 0.15
        range_x = max_x - min_x if max_x != min_x else 1
        range_y = max_y - min_y if max_y != min_y else 1
        range_x *= (1 + margin * 2)
        range_y *= (1 + margin * 2)

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        scale_x = w / range_x
        scale_y = h / range_y
        self.scale = min(scale_x, scale_y)
        # Esta vista encuadrada es la referencia: decoraciones a tamano base.
        self._reference_scale = self.scale

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.offset_x = w / 2 - center_x * self.scale
        self.offset_y = h / 2 + center_y * self.scale

        self.redraw()

    # ═════════════════════════════════════════════════════════════════════
    # MODO DIBUJO DE ELEMENTOS (estilo AutoCAD)
    # ═════════════════════════════════════════════════════════════════════
    #
    # Activacion: el caller (pre_tab) llama enable_draw_mode() tras un
    # pre-flight de material. El usuario clickea N veces el canvas:
    #   - click sobre nodo corner existente (dentro del snap radius en
    #     pixeles) -> snap implicito, reusa el nodo, NO emerge Entry
    #   - click en zona vacia -> emerge Entry flotante con coord del
    #     cursor pre-llenada; Tab navega X<->Y, Enter confirma, Esc cancela
    #     este punto (no el modo)
    # Al completar 4 clicks: commit atomico con auto-CCW + auto-expand
    # Q9 + 1 snapshot de undo. El modo persiste para crear el siguiente.
    # Esc con elemento parcial -> cancelar puntos. Esc sin nada parcial
    # -> desactivar modo.
    # ═════════════════════════════════════════════════════════════════════

    def enable_draw_mode(self):
        """Activa el modo dibujo de elementos. Cambia el cursor a cross,
        muestra hint en status bar, y en cada click del canvas captura
        un vertice del nuevo elemento. Se mantiene activo hasta que el
        caller llame disable_draw_mode() o el usuario presione Esc sin
        puntos pendientes."""
        if self.draw_mode_active:
            return
        self.draw_mode_active = True
        self.draw_pending = []
        self.draw_hover_snap = None
        try:
            self.canvas.config(cursor="crosshair")
        except tk.TclError:
            pass
        self._notify_draw_mode_changed()
        self._update_draw_status()
        self.redraw()

    def disable_draw_mode(self):
        if not self.draw_mode_active:
            return
        self.draw_mode_active = False
        self.draw_pending = []
        self.draw_hover_snap = None
        self._close_draw_entry()
        try:
            self.canvas.config(cursor="")
        except tk.TclError:
            pass
        self._notify_draw_mode_changed()
        self.main_window.set_status("Modo dibujo desactivado")
        self.redraw()

    def is_draw_mode_active(self):
        return self.draw_mode_active

    def toggle_draw_mode(self):
        if self.draw_mode_active:
            self.disable_draw_mode()
        else:
            self.enable_draw_mode()

    # ─── Internals ──────────────────────────────────────────────────────

    def _notify_draw_mode_changed(self):
        if self.on_draw_mode_changed:
            try:
                self.on_draw_mode_changed(self.draw_mode_active)
            except Exception:
                pass

    def _update_draw_status(self):
        n = len(self.draw_pending)
        target = self.draw_target_count
        next_idx = n + 1
        self.main_window.set_status(
            f"Modo dibujo: vertice {min(next_idx, target)}/{target} — "
            f"click en canvas o sobre nodo (snap). Esc cancela."
        )

    def _draw_hit_test_corner(self, sx, sy):
        """Snap solo a nodos corner (no mid/center Q9). Distancia en
        pixeles para ser independiente del zoom. Retorna node_id o None."""
        if not self.project.nodes:
            return None
        roles = classify_nodes(self.project)
        best = None
        best_d = float("inf")
        for nid, node in self.project.nodes.items():
            if roles.get(nid, "corner") != "corner":
                continue
            nsx, nsy = self.world_to_screen(node.x, node.y)
            d = ((nsx - sx) ** 2 + (nsy - sy) ** 2) ** 0.5
            if d < self.draw_snap_radius_px and d < best_d:
                best_d = d
                best = nid
        return best

    def _on_draw_click(self, event):
        sx, sy = event.x, event.y
        # Si hay un Entry de coords abierto, este click lo cancela
        # (descarta lo que el usuario tuviera tipeado) y NO se procesa
        # como nuevo punto. Predecible: el primer click cierra, el
        # siguiente abre uno nuevo.
        if self._draw_entry is not None:
            self._close_draw_entry()
            self.main_window.set_status(
                "Entry de coords cerrado — clickea de nuevo para el punto"
            )
            return
        # 1) Snap: si hay corner cercano, agregar reusando ese nodo.
        snapped = self._draw_hit_test_corner(sx, sy)
        if snapped is not None:
            # Evitar duplicado del mismo vertice consecutivo (click 2 veces
            # sobre el mismo nodo): rompe el shoelace y crea elementos
            # degenerados. Ignorar silenciosamente.
            if self.draw_pending and self.draw_pending[-1][0] == snapped:
                self.main_window.set_status(
                    "Ese nodo ya es el ultimo vertice — elegi otro"
                )
                return
            self._draw_add_pending(snapped, None, None)
            return
        # 2) Sin snap: emerger Entry flotante.
        # Si ORTHO esta efectivamente activo y hay punto previo, el Entry
        # se abre en modo single (1 campo de distancia) y el cursor se
        # proyecta al eje H/V dominante para "click and place" coherente
        # con el rubber band del preview.
        wx, wy = self.screen_to_world(sx, sy)
        ortho_locked = bool(
            self.draw_pending
            and self._is_ortho_effective(getattr(event, "state", 0))
        )
        if ortho_locked:
            last_pt = self.draw_pending[-1]
            wx, wy = self._project_to_ortho(last_pt[1], last_pt[2], wx, wy)
        self._open_draw_entry(sx, sy, wx, wy, ortho_locked=ortho_locked)

    def _draw_add_pending(self, snapped_nid, x, y):
        if snapped_nid is not None:
            node = self.project.nodes.get(snapped_nid)
            if node is None:
                return
            x, y = node.x, node.y
        self.draw_pending.append((snapped_nid, x, y))
        if len(self.draw_pending) >= self.draw_target_count:
            self._draw_commit()
            return
        self._update_draw_status()
        self.redraw()

    def _draw_commit(self):
        """Crea nodos faltantes + elemento + auto-CCW + auto-expand Q9
        en una sola operacion atomica con 1 snapshot de undo. Resetea
        pending pero mantiene el modo activo para el siguiente elemento."""
        if len(self.draw_pending) != self.draw_target_count:
            return

        # Auto-CCW: shoelace negativo -> orden CW -> revertir.
        pts = [(x, y) for (_nid, x, y) in self.draw_pending]
        signed_area = self._shoelace_signed(pts)
        cw_corrected = signed_area < 0
        if cw_corrected:
            self.draw_pending = list(reversed(self.draw_pending))

        # Validar que tenemos materiales (defensivo: el pre-flight del
        # caller deberia haberlo garantizado).
        mat_names = list(self.project.materials.keys())
        if not mat_names:
            self.main_window.set_status(
                "Error: defina al menos un material antes de dibujar"
            )
            self.draw_pending = []
            self.redraw()
            return

        # Capturar undo del estado pre-creacion.
        if hasattr(self.main_window, "undo_stack"):
            try:
                self.main_window.undo_stack.capture("dibujar elemento (canvas)")
            except Exception:
                pass

        # Crear nodos faltantes (los snap reusan el ID existente).
        final_node_ids = []
        for (snapped_nid, x, y) in self.draw_pending:
            if snapped_nid is not None:
                final_node_ids.append(snapped_nid)
            else:
                new_node = self.project.add_node(x, y)
                final_node_ids.append(new_node.id)

        elem = self.project.add_element(
            final_node_ids,
            self.project.default_thickness,
            mat_names[0],
        )

        # Si proyecto Q9, generar mid-nodes / centroide automaticamente.
        try:
            auto_expand_if_q9(self.project)
        except Exception:
            pass

        # Reset pending pero mantener modo activo.
        self.draw_pending = []
        self.redraw()

        # Notificar al caller para que refresque tablas.
        if self.on_draw_element_created:
            try:
                self.on_draw_element_created(elem.id)
            except Exception:
                pass

        # Status bar: hint de orientacion corregida si aplico.
        if cw_corrected:
            self.main_window.set_status(
                f"Elemento {elem.id} creado (orientacion CW corregida a CCW). "
                f"Modo dibujo sigue activo (Esc para salir)."
            )
        else:
            self._update_draw_status()
            self.main_window.set_status(
                f"Elemento {elem.id} creado. Modo dibujo sigue activo "
                f"(Esc para salir)."
            )

    # ─── Helpers AutoCAD-style (ORTHO + parser de coords) ───────────────

    @staticmethod
    def _parse_coord_token(text, last_value):
        """Parsea un token del Entry de coords con prefijos AutoCAD-style.

        - Sin prefijo: relativo a `last_value` (default del proyecto). Si
          `last_value is None` (1er punto), se interpreta absoluto.
        - Prefijo `#`: absoluto, ignora `last_value`.
        - Prefijo `@`: relativo (no-op tolerado, equivalente a sin prefijo).
        - Vacio: retorna (None, False) — sentinela para fallback a cursor.

        Decimal: solo `.`. Si el texto contiene `,`, parsea como float
        directamente (Python lanzara ValueError; el caller lo maneja).

        Retorna (value: float | None, was_absolute: bool).
        Lanza ValueError si el texto no parsea como numero.
        """
        s = (text or "").strip()
        if not s:
            return (None, False)
        if s.startswith("#"):
            return (float(s[1:].strip()), True)
        if s.startswith("@"):
            rel = float(s[1:].strip())
            if last_value is None:
                # 1er punto con @: no tiene sentido relativo, tratar absoluto
                return (rel, False)
            return (last_value + rel, False)
        val = float(s)
        if last_value is None:
            return (val, False)
        return (last_value + val, False)

    def _is_ortho_effective(self, event_state=None):
        """Devuelve el estado ortho efectivo combinando toggle + Shift.

        Shift presionado invierte el toggle (XOR), igual que AutoCAD.
        Si event_state es None se usa el ultimo bitmask cacheado del
        movimiento del mouse.
        """
        state = self._last_event_state if event_state is None else event_state
        shift_held = bool(state & 0x0001)
        return self.ortho_active ^ shift_held

    @staticmethod
    def _project_to_ortho(last_x, last_y, target_x, target_y):
        """Proyecta (target_x, target_y) al eje H o V dominante respecto a
        (last_x, last_y). Retorna (proj_x, proj_y) en world coords."""
        dx = target_x - last_x
        dy = target_y - last_y
        if abs(dx) >= abs(dy):
            return (target_x, last_y)
        return (last_x, target_y)

    def set_ortho_active(self, active):
        """Setea el toggle persistente de ORTHO y notifica al main_window."""
        active = bool(active)
        if self.ortho_active == active:
            return
        self.ortho_active = active
        if self.on_ortho_changed:
            try:
                self.on_ortho_changed(active)
            except Exception:
                pass
        # Refrescar preview si el modo dibujo esta activo (la proyeccion
        # del rubber band cambia inmediatamente).
        if self.draw_mode_active:
            self.redraw()

    @staticmethod
    def _shoelace_signed(pts):
        """Area con signo del polígono. Positiva si CCW (orientacion
        canonica de la libreria), negativa si CW."""
        n = len(pts)
        s = 0.0
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            s += x1 * y2 - x2 * y1
        return s / 2.0

    def _on_draw_escape(self, _event=None):
        """Esc en modo dibujo: si hay puntos pendientes, los descarta
        (el modo sigue activo). Si no hay nada pendiente, desactiva el
        modo. Tambien cierra el Entry flotante si esta abierto."""
        if not self.draw_mode_active:
            return
        if self._draw_entry is not None:
            # El entry flotante captura su propio Esc, pero por las dudas.
            self._close_draw_entry()
            return
        if self.draw_pending:
            self.draw_pending = []
            self.draw_hover_snap = None
            self._update_draw_status()
            self.main_window.set_status(
                "Elemento parcial cancelado — modo dibujo sigue activo"
            )
            self.redraw()
            return
        # Sin nada pendiente: salir del modo.
        self.disable_draw_mode()

    # ─── Entry flotante (estilo AutoCAD coord input) ────────────────────

    def _open_draw_entry(self, sx, sy, x_init, y_init, ortho_locked=False):
        """Toplevel borderless con Entry de coords AutoCAD-style.

        Layout dinamico:
        - **Single entry** cuando `ortho_locked=True` y hay punto previo:
          1 campo de distancia con label que indica el eje + sentido del
          cursor (`d →`, `d ←`, `d ↑`, `d ↓`). Empty + Enter usa el cursor
          (ya proyectado).
        - **Dual entry** en cualquier otro caso:
            · 1er punto: labels `X:` `Y:` pre-llenadas con cursor.
            · 2do+ punto: labels `dX:` `dY:` vacias (relativo al ultimo).
          Prefijos `#` (absoluto) / `@` (relativo, no-op). Coma en X salta
          a Y con texto restante pegado.

        Tab navega entries, Enter / Space confirman, Esc cancela.
        """
        self._close_draw_entry()

        top = tk.Toplevel(self.canvas)
        top.overrideredirect(True)
        try:
            top.attributes("-topmost", True)
        except tk.TclError:
            pass
        rx = self.canvas.winfo_rootx() + sx + 14
        ry = self.canvas.winfo_rooty() + sy + 14
        top.geometry(f"+{rx}+{ry}")

        frame = tk.Frame(top, bg=LABEL_BG, highlightthickness=1,
                         highlightbackground=CANVAS_SELECTED_COLOR)
        frame.pack()
        inner = ttk.Frame(frame, padding=4)
        inner.pack()

        has_last = bool(self.draw_pending)

        # ─── Modo single-entry (ortho activo + punto previo) ──────────
        if ortho_locked and has_last:
            last_pt = self.draw_pending[-1]
            last_x_world, last_y_world = last_pt[1], last_pt[2]
            cur_sx, cur_sy = self._last_cursor_xy or (sx, sy)
            cur_wx, cur_wy = self.screen_to_world(cur_sx, cur_sy)
            dx_w = cur_wx - last_x_world
            dy_w = cur_wy - last_y_world
            is_x = abs(dx_w) >= abs(dy_w)
            sign = (1 if (dx_w if is_x else dy_w) >= 0 else -1)
            arrow = ("→" if sign > 0 else "←") if is_x else (
                "↑" if sign > 0 else "↓")

            var_d = tk.StringVar(value="")
            ttk.Label(inner, text=f"d {arrow}", font=FONT_MONO_SMALL).grid(
                row=0, column=0, padx=(0, 4))
            entry_d = ttk.Entry(inner, textvariable=var_d, width=10,
                                font=FONT_MONO_SMALL, bootstyle="info")
            entry_d.grid(row=0, column=1)

            def commit_single(_e=None):
                text = var_d.get().strip()
                if not text:
                    # Empty + Enter -> cursor ya proyectado al click
                    self._close_draw_entry()
                    self._draw_add_pending(None, x_init, y_init)
                    return "break"
                try:
                    # Tolerar prefijos por mero hábito muscular AutoCAD
                    d = float(text.lstrip("@").lstrip("#").strip())
                except ValueError:
                    self.main_window.set_status(
                        "Distancia invalida — punto descartado")
                    self._close_draw_entry()
                    return "break"
                if is_x:
                    new_x = last_x_world + sign * d
                    new_y = last_y_world
                else:
                    new_x = last_x_world
                    new_y = last_y_world + sign * d
                self._close_draw_entry()
                self._draw_add_pending(None, new_x, new_y)
                return "break"

            def cancel_single(_e=None):
                self._close_draw_entry()
                return "break"

            entry_d.bind("<Return>", commit_single)
            entry_d.bind("<KP_Enter>", commit_single)
            entry_d.bind("<space>", commit_single)
            entry_d.bind("<Escape>", cancel_single)
            entry_d.focus_set()
            self._draw_entry = top
            return

        # ─── Modo dual-entry ──────────────────────────────────────────
        if has_last:
            label_x_text = "dX:"
            label_y_text = "dY:"
            var_x = tk.StringVar(value="")
            var_y = tk.StringVar(value="")
            last_pt = self.draw_pending[-1]
            last_x_world = last_pt[1]
            last_y_world = last_pt[2]
        else:
            label_x_text = "X:"
            label_y_text = "Y:"
            var_x = tk.StringVar(value=f"{x_init:.{DECIMALS_LENGTH}f}")
            var_y = tk.StringVar(value=f"{y_init:.{DECIMALS_LENGTH}f}")
            last_x_world = None
            last_y_world = None

        ttk.Label(inner, text=label_x_text, font=FONT_MONO_SMALL).grid(
            row=0, column=0, padx=(0, 2))
        entry_x = ttk.Entry(inner, textvariable=var_x, width=10,
                            font=FONT_MONO_SMALL, bootstyle="info")
        entry_x.grid(row=0, column=1, padx=(0, 6))
        ttk.Label(inner, text=label_y_text, font=FONT_MONO_SMALL).grid(
            row=0, column=2, padx=(0, 2))
        entry_y = ttk.Entry(inner, textvariable=var_y, width=10,
                            font=FONT_MONO_SMALL, bootstyle="info")
        entry_y.grid(row=0, column=3)

        def on_comma_in_x(_event):
            """Coma en X = separador de campo (estilo AutoCAD dyn input).
            Splitea el contenido en la posicion del cursor, deja el lado
            izquierdo en X, mueve el lado derecho a Y, focus a Y."""
            try:
                cursor_pos = entry_x.index("insert")
            except tk.TclError:
                cursor_pos = len(var_x.get())
            full = var_x.get()
            left = full[:cursor_pos]
            right = full[cursor_pos:]
            var_x.set(left)
            var_y.set(right)
            entry_y.focus_set()
            try:
                entry_y.icursor(len(right))
            except tk.TclError:
                pass
            return "break"

        def commit(_e=None):
            text_x = var_x.get().strip()
            text_y = var_y.get().strip()

            # Caso 1: ambos vacios -> usar cursor (proyectado en single,
            # crudo en dual).
            if not text_x and not text_y:
                self._close_draw_entry()
                self._draw_add_pending(None, x_init, y_init)
                return "break"

            # Caso 2: Y vacio en dual mode -> error pedagogico.
            # (Para distancia directa, activar ORTHO antes del click.)
            if not text_y and last_x_world is not None:
                self.main_window.set_status(
                    "Falta dY — para distancia directa activa ORTHO (F8/Shift) "
                    "antes del click"
                )
                self._close_draw_entry()
                return "break"

            # Caso 3: parseo normal con prefijos.
            try:
                xv, _ = MeshCanvas._parse_coord_token(text_x, last_x_world)
                yv, _ = MeshCanvas._parse_coord_token(text_y, last_y_world)
            except ValueError:
                self.main_window.set_status(
                    "Coord invalida — punto descartado"
                )
                self._close_draw_entry()
                return "break"
            if xv is None:
                xv = last_x_world if last_x_world is not None else x_init
            if yv is None:
                yv = last_y_world if last_y_world is not None else y_init
            self._close_draw_entry()
            self._draw_add_pending(None, xv, yv)
            return "break"

        def cancel(_e=None):
            self._close_draw_entry()
            return "break"

        # Coma en X = jump a Y (solo X).
        entry_x.bind("<KeyPress-comma>", on_comma_in_x)
        # Enter / Space confirman (Space = convencion AutoCAD).
        # `return "break"` evita que el char espacio se inserte en el Entry.
        # Esc cancela este punto (no el modo).
        for ent in (entry_x, entry_y):
            ent.bind("<Return>", commit)
            ent.bind("<KP_Enter>", commit)
            ent.bind("<space>", commit)
            ent.bind("<Escape>", cancel)
        # NOTA: NO bindeamos <FocusOut> del Toplevel. En Windows + Tk
        # <FocusOut> se dispara espuriamente al Tab/click entre entries
        # internos, cerrando el dialogo antes de que el usuario pueda
        # editar Y. El cierre se da solo via Enter/Space/Esc o via
        # "click en canvas mientras hay entry abierto" (manejado en
        # _on_draw_click: el primer click cancela el entry).

        entry_x.select_range(0, tk.END)
        entry_x.focus_set()
        self._draw_entry = top

    def _close_draw_entry(self):
        if self._draw_entry is not None:
            try:
                self._draw_entry.destroy()
            except tk.TclError:
                pass
            self._draw_entry = None
        # Recuperar focus del canvas para que Esc / atajos sigan llegando.
        try:
            self.canvas.focus_set()
        except tk.TclError:
            pass

    # ─── Render preview ─────────────────────────────────────────────────

    def _draw_pending_overlay(self):
        """Dibuja el polígono parcial del elemento en construccion, los
        numeros 1..N en cada vertice, la linea preview al cursor, y
        resalta el snap candidate si lo hay."""
        # Snap candidate (anillo amarillo grueso sobre nodo existente).
        if self.draw_hover_snap is not None:
            node = self.project.nodes.get(self.draw_hover_snap)
            if node is not None:
                ssx, ssy = self.world_to_screen(node.x, node.y)
                self.canvas.create_oval(
                    ssx - 11, ssy - 11, ssx + 11, ssy + 11,
                    outline=CANVAS_SELECTED_COLOR, width=3, fill="",
                    tags="draw_preview",
                )

        if not self.draw_pending:
            return

        pts_screen = []
        for (_nid, x, y) in self.draw_pending:
            sx, sy = self.world_to_screen(x, y)
            pts_screen.append((sx, sy))

        # Aristas confirmadas (línea punteada amarilla).
        for i in range(len(pts_screen) - 1):
            x1, y1 = pts_screen[i]
            x2, y2 = pts_screen[i + 1]
            self.canvas.create_line(
                x1, y1, x2, y2, fill=CANVAS_SELECTED_COLOR,
                dash=(5, 3), width=2, tags="draw_preview",
            )

        # Línea preview del último vertice al cursor.
        if self._last_cursor_xy is not None:
            cx, cy = self._last_cursor_xy
            x_last, y_last = pts_screen[-1]
            # Si ORTHO esta efectivo (toggle XOR Shift), proyectar el
            # cursor al eje H/V dominante en world coords para que el
            # rubber band se "lockee" como en AutoCAD.
            if self._is_ortho_effective():
                last_world = self.draw_pending[-1]
                cur_wx, cur_wy = self.screen_to_world(cx, cy)
                proj_wx, proj_wy = self._project_to_ortho(
                    last_world[1], last_world[2], cur_wx, cur_wy
                )
                cx, cy = self.world_to_screen(proj_wx, proj_wy)
            self.canvas.create_line(
                x_last, y_last, cx, cy, fill=CANVAS_SELECTED_COLOR,
                dash=(2, 4), width=1, tags="draw_preview",
            )
            # Si tenemos 3 puntos, mostrar tambien el cierre tentativo
            # (linea al primer vertice) para que el usuario "vea" el
            # quad antes de clickear.
            if len(pts_screen) == 3:
                x0, y0 = pts_screen[0]
                self.canvas.create_line(
                    cx, cy, x0, y0, fill=CANVAS_SELECTED_COLOR,
                    dash=(2, 4), width=1, tags="draw_preview",
                )

        # Numeros 1..N en cada vertice confirmado (circulo + numero).
        for i, (sx, sy) in enumerate(pts_screen, start=1):
            self.canvas.create_oval(
                sx - 8, sy - 8, sx + 8, sy + 8,
                outline=CANVAS_SELECTED_COLOR, width=2,
                fill=CANVAS_BG_COLOR, tags="draw_preview",
            )
            self.canvas.create_text(
                sx, sy, text=str(i), fill=CANVAS_SELECTED_COLOR,
                font=("Segoe UI", 9, "bold"), tags="draw_preview",
            )
