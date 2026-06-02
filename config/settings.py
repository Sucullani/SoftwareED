"""
Configuración global del software educativo FEM.
Constantes, rutas y valores por defecto.
"""

import os
import sys

# ─── Información de la aplicación ───────────────────────────────────────────
APP_NAME = "EduFEM - Software Educativo de Elementos Finitos"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Tesis de Grado"

# ─── Rutas ──────────────────────────────────────────────────────────────────
def _base_dir() -> str:
    """Raíz para resolver recursos empaquetados. En desarrollo es la raíz del
    repo; en un bundle PyInstaller es ``sys._MEIPASS`` (la carpeta temporal /
    ``_internal`` donde se extraen ``resources/``). Espejo de la lógica de
    ``gui.fonts_loader._resources_root`` — mantener ambas en sync.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = _base_dir()
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")


def resource_path(*parts: str) -> str:
    """Ruta absoluta a un recurso bajo ``resources/``, válida tanto corriendo
    desde el repo como desde el ``.exe`` empaquetado. Usar SIEMPRE esto para
    videos/ejemplos/iconos — nunca rutas relativas al CWD (fallan en el bundle,
    cuyo directorio de trabajo no es la carpeta del programa).
    """
    return os.path.join(RESOURCES_DIR, *parts)

# ─── Tipos de análisis ─────────────────────────────────────────────────────
ANALYSIS_PLANE_STRESS = "Tensión Plana"
ANALYSIS_PLANE_STRAIN = "Deformación Plana"
ANALYSIS_TYPES = [ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN]

# ─── Tipos de elemento ─────────────────────────────────────────────────────
ELEMENT_Q4 = "Q4 - Cuadrilátero 4 nodos"
ELEMENT_Q9 = "Q9 - Cuadrilátero 9 nodos"
ELEMENT_TYPES = [ELEMENT_Q4, ELEMENT_Q9]

# ─── Puntos de Gauss por tipo de elemento ───────────────────────────────────
GAUSS_POINTS = {
    ELEMENT_Q4: 2,  # 2x2 = 4 puntos
    ELEMENT_Q9: 3,  # 3x3 = 9 puntos
}

# ─── Valores por defecto del proyecto ───────────────────────────────────────
DEFAULT_ANALYSIS_TYPE = ANALYSIS_PLANE_STRESS
DEFAULT_ELEMENT_TYPE = ELEMENT_Q4
DEFAULT_THICKNESS = 1.0

# ─── Configuración de la GUI ───────────────────────────────────────────────
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700
CANVAS_BG_COLOR = "#1e1e2e"
CANVAS_GRID_COLOR = "#333350"
CANVAS_NODE_COLOR = "#4fc3f7"
CANVAS_ELEMENT_COLOR = "#81c784"
CANVAS_LOAD_COLOR = "#ef5350"
CANVAS_CONSTRAINT_COLOR = "#ffa726"
CANVAS_SELECTED_COLOR = "#ffeb3b"
# Geometria "fantasma": malla base atenuada cuando un modulo overlay quiere que
# su capa propia sea la protagonista (M0: el X-ray de calidad distorsionado se
# confundia con la malla base de color normal al arrastrar). Gris azulado tenue,
# mas visible que la grilla pero claramente "inactivo".
CANVAS_GHOST_COLOR = "#4a5060"
CANVAS_NODE_RADIUS = 4
# Nodos extra de Q9 (medios de arista y centroide): más pequeños y de color
# distinto para diferenciarlos visualmente de los vértices.
CANVAS_NODE_MID_COLOR    = "#6fb8ff"   # Azul claro — medios de arista (N5..N8)
CANVAS_NODE_CENTER_COLOR = "#b86fff"   # Violeta — centroide (N9)
CANVAS_NODE_MID_RADIUS   = 3
# Nucleos oscuros de los nodos (efecto "anillo": oval exterior del color del
# rol + oval interior oscuro). Movidos desde mesh_canvas.py (eran hex literales
# inline que violaban la paleta congelada). El nucleo da profundidad al marcador
# sin cambiar su color de rol.
CANVAS_NODE_INNER_CORNER = "#0a2a44"   # Azul oscuro — vertices (corner)
CANVAS_NODE_INNER_MID    = "#18354a"   # Azul oscuro — medios de arista Q9
CANVAS_NODE_INNER_CENTER = "#301a44"   # Violeta oscuro — centroide N9
CANVAS_NODE_INNER_ORPHAN = "#2a2a32"   # Gris — nucleo de nodo huerfano
CANVAS_NODE_OUTLINE      = "#0a1a2a"   # Contorno fino del marcador de nodo
# Nodo huerfano preservado (sin elemento, con cargas/BCs/surface refs).
# Naranja desaturado (warning visual): se diferencia claramente del gris
# tenue `AUTO_NODE_FG` usado para los nodos Q9 medios/centro (read-only).
# Coherente con HEALTH_WARNING_COLOR: el huerfano es estado de advertencia
# (el modelo no podra resolver hasta que se conecte el nodo o se elimine).
# Aplica a cualquier rol (corner/mid/center) cuando es huerfano.
CANVAS_NODE_ORPHAN_COLOR = "#d68545"   # naranja desaturado
ORPHAN_NODE_FG           = "#d68545"   # foreground del tag tree de huerfanos
# Background tinted para la fila huerfana en el spreadsheet: ayuda a
# distinguir la fila completa, no solo el texto. Naranja muy oscuro
# para no chocar con el zebra striping pero ser perceptible.
ORPHAN_NODE_BG           = "#3a2418"
# Fila fantasma de pick desde canvas: aparece en sub-pestañas Cargas /
# Restricciones / Carg. Superf. cuando el usuario tiene seleccionados
# nodos / aristas en el canvas. Click confirma la fila (la sugerencia
# se vuelve real). Azul desaturado: distinto del placeholder (gris) y
# del huerfano (naranja).
PICK_GHOST_FG            = "#7fbfff"   # azul claro
PICK_GHOST_BG            = "#1a3050"   # azul oscuro desaturado
# Highlight de fila en spreadsheet cuando su id esta en el set
# `selected_*` del canvas (sync canvas -> spreadsheet via tag visual).
# DECOUPLED de CANVAS_SELECTED_COLOR a proposito: el canvas necesita un
# highlight brillante (amarillo) para destacar geometria sobre el fondo
# oscuro `#1e1e2e`, mientras que el spreadsheet necesita un gris sutil
# que no compita con orphan/ghost/placeholder. El gris `#555555` y el
# foreground blanco coinciden con `darkly.selectbg`/`selectfg`, asi el
# click directo en una fila (state nativo "selected" del tema) y el
# click en canvas (que aplica el tag `canvas_selected` via rebuild)
# producen visualmente el mismo gris sin necesidad de overridear el
# `style.map` del tema (que era fragil porque ttkbootstrap reaplica sus
# mappings al crear widgets y nuestros overrides quedaban pisados).
CANVAS_SELECTED_ROW_BG   = "#555555"
CANVAS_SELECTED_ROW_FG   = "#ffffff"
CANVAS_FONT_SIZE = 9

# ─── Realce de seleccion + hover (sistema de seleccion profesional) ───────
# Auditoria UX 2026-05 (docs/auditoria_canvas_ux.md): la seleccion por
# simple color-swap se perdia en mallas grandes. Se agrega un HALO (anillo
# claro mas ancho dibujado DEBAJO del item, tecnica del glow ya usada en
# cargas) para que el item seleccionado destaque de inmediato a cualquier
# escala. El hover (pre-seleccion) usa un cian distinto del amarillo de
# seleccion para no confundirse con ella.
CANVAS_SELECTED_HALO_COLOR = "#fff59d"   # amarillo palido: glow bajo la seleccion
CANVAS_HOVER_COLOR         = "#8be9fd"   # cian claro: item bajo el cursor (pre-seleccion)
# Relleno suave de la seleccion (rediseno 2026-05, pedido del usuario "color
# suave de relleno transparente que no cubra datos"). tk.Canvas NO soporta alpha
# vectorial, asi que se simula con un poligono `stipple="gray12"` (patron de
# puntos disperso que deja asomar la malla/datos debajo) RELLENO con este color.
# Es CANVAS_SELECTED_COLOR mezclado ~85% hacia el bg #1e1e2e (precalculado) ->
# amarillo apagado que llena area sin tapar. Acompaña (no reemplaza) al halo,
# que se afina pero se conserva (hallazgo I1: la seleccion se perdia en mallas
# grandes sin un realce de area).
CANVAS_SELECTED_FILL_COLOR = "#54521f"
# Silueta del dominio: las aristas del contorno exterior (las que pertenecen
# a un solo elemento) se realzan sobre las internas. Verde claro, misma
# familia que CANVAS_ELEMENT_COLOR — emfatiza el borde sin romper la paleta.
CANVAS_BOUNDARY_COLOR      = "#a5d6a7"
# Rellenos suaves de los simbolos de restriccion (oval/triangulo con interior
# tenue para que el simbolo se distinga del fondo oscuro sin saturar). Movidos
# desde mesh_canvas.py (eran hex literales inline).
CANVAS_CONSTRAINT_FIXED_FILL  = "#3a2a10"   # Marron oscuro — empotramiento
CANVAS_CONSTRAINT_ROLLER_FILL = "#1a3a4a"   # Azul oscuro — rodillos

# ─── Reescalado de decoraciones con el zoom (proporcional acotado) ─────────
# Pedido del usuario 2026-05: que los objetos (nodos, flechas, simbolos) se
# reescalen al hacer zoom. La geometria (elementos en coords mundo) ya escala;
# estas constantes hacen que las DECORACIONES tambien crezcan/encojan, pero
# CLAMPED para no explotar al acercar ni desaparecer al alejar (modelo
# "proporcional acotado", estilo GiD). El multiplicador es scale/reference_scale
# (reference_scale se fija en cada fit_view). Se clampa el FACTOR (no el px
# absoluto) para que sea uniforme entre glifos de distinta base: nodo r=4,
# flecha 44, restriccion 12. Ver mesh_canvas._decoration_factor.
DECORATION_SCALE_MIN_FACTOR = 0.6   # piso del multiplicador (al alejar)
DECORATION_SCALE_MAX_FACTOR = 2.5   # techo del multiplicador (al acercar)

# ─── Niveles de detalle (LOD) por zoom ────────────────────────────────────
# El canvas decide cuanto detalle dibujar segun los pixeles-por-arista-media
# (mediana de longitud de arista en mundo * scale). Reduce el ruido visual Y
# el arbol de items Tk en mallas grandes (la principal palanca de
# rendimiento — ver docs/auditoria_canvas_ux.md seccion E).
#   far  (< LOD_EDGE_PX_FAR):  solo silueta + corners como puntos, sin labels.
#   mid  (< LOD_EDGE_PX_NEAR): aristas + corners, mid/center atenuados, labels
#                              solo en el item seleccionado.
#   near (>=):                 todo + numeracion automatica.
LOD_EDGE_PX_FAR  = 14.0
LOD_EDGE_PX_NEAR = 55.0
# Mallas pequeñas (<= este umbral de elementos) NUNCA aplican gating: siempre
# se ven en modo "near" con toda la numeracion. Preserva la experiencia
# didactica del ejemplo canonico (4 elementos) — el LOD solo entra cuando la
# malla es lo bastante densa como para volverse ruidosa.
LOD_MIN_ELEMENTS_FOR_GATING = 12
# La silueta del borde (boundary overlay) y la atenuacion de contexto (focus)
# tampoco se activan por debajo de estos umbrales de elementos.
CANVAS_BOUNDARY_MIN_ELEMENTS = 12
CANVAS_FOCUS_MIN_ELEMENTS    = 60

# ─── Post / probes (consulta interactiva de resultados) ───────────────────
# Probes pinneadas: marcador 📍 con etiqueta P1, P2, ... sobre el canvas
# en la fase Post. Hover sobre la malla muestra tooltip flotante con
# valores de u y σ; click pina una probe persistente. Snap automatico
# a puntos de Gauss (cuadrados azules) cuando el cursor esta dentro de
# PROBE_GAUSS_SNAP_PX. Convencion cromatica:
#   - Probes pinneadas: naranja (warm, semantica de "marcador del usuario")
#   - Hover transitorio: amarillo desaturado (igual familia que selection)
#   - Gauss libres: azul claro discreto (parte de la malla, no destacan)
#   - Gauss snappeado: amarillo brillante (igual que CANVAS_SELECTED_COLOR)
PROBE_PIN_COLOR        = "#ff9933"   # naranja: marcador pinneado
PROBE_PIN_LABEL_FG     = "#ffd9a3"   # texto de etiqueta P1, P2, ...
PROBE_HOVER_COLOR      = "#ffe066"   # halo del cursor en hover
GAUSS_MARKER_COLOR     = "#5fa8ff"   # cuadrado azul de Gauss en reposo
GAUSS_SNAP_COLOR       = "#ffeb3b"   # cuadrado al snappear (=SELECTED)
GAUSS_MARKER_SIZE_PX   = 3           # mitad del lado del cuadrado
PROBE_GAUSS_SNAP_PX    = 8           # radio de snap en pixeles screen
PROBE_NODE_SNAP_PX     = 12          # radio de snap a nodos (mas generoso)
PROBE_THROTTLE_MS      = 60          # throttle del hover (16 fps efectivos)
PROBE_PIN_RADIUS_PX    = 5           # circulo del marcador pinneado
PROBE_PIN_DELETE_PX    = 10          # tolerancia para Ctrl+click sobre pin
PROBE_NODE_SNAP_COLOR  = "#5fa8ff"   # azul cyan -- snap a nodo activo
PROBE_NODE_RING_PX     = 8           # anillo de snap visible cuando enganchado

# ─── Post / analisis avanzado (Mohr inset del probe + 3D) ────────────────
# Constantes usadas por:
#   - gui/postprocessing/details_panel.py    (Mohr inset del clic derecho)
#   - gui/postprocessing/surface_3d_viewer.py      (vista 3D del campo)
#
# Convencion cromatica del estado principal (σ1/σ2) sobre el Mohr:
#   - σ1 traccion: azul (familia de "estable / positivo")
#   - σ2 compresion: rojo (familia de "alerta / negativo")
#   - Circulo de Mohr: azul claro coherente con paleta info
PRINCIPAL_TENSION_COLOR      = "#42a5f5"   # σ1 azul (traccion)
PRINCIPAL_COMPRESSION_COLOR  = "#ef5350"   # σ2 rojo (compresion)
MOHR_CIRCLE_COLOR            = "#90caf9"   # contorno del circulo
MOHR_POINT_COLOR             = "#ffd54f"   # punto (σx, τxy) sobre el circulo
MOHR_AXIS_COLOR              = "#bdbdbd"   # ejes σ / τ del Mohr
MOHR_BG                      = "#2c2c2c"   # fondo del axes Mohr (= EDU_AXES_BG, neutro)
MOHR_FG                      = "#dfdfdf"   # texto / ticks del Mohr
MOHR_GRID_COLOR              = "#404055"   # grilla tenue del Mohr (DetailsPanel)
SURFACE_3D_DEFAULT_GRID      = 8           # sub-grid por elemento en plot_surface
SURFACE_3D_DISC_THRESHOLD    = 0.10        # >10% del rango => arista discontinua

# ─── tk.Menu (barra de menus principal) ────────────────────────────────────
# Foreground del estado disabled. En tk.Menu nativo de Windows con tema
# oscuro el render por defecto del disabled hace doble pasada (texto
# "shadow" + texto "highlight") que en fondo oscuro se percibe como
# embossado / mas grueso en lugar de mas tenue. Forzar un color plano
# elimina el efecto y deja al disabled visiblemente atenuado.
# Aplicar via `root.option_add("*Menu.disabledForeground", MENU_DISABLED_FG)`.
MENU_DISABLED_FG = "#5a5d63"

# ─── Salud del modelo (badge en status bar + colores de severidad) ─────────
HEALTH_OK_COLOR       = "#4caf50"   # verde — todo en orden
HEALTH_WARNING_COLOR  = "#ffa726"   # naranja — warnings (no bloquean)
HEALTH_ERROR_COLOR    = "#ef5350"   # rojo — errores criticos (bloquean solve)
HEALTH_INFO_COLOR     = "#4fc3f7"   # azul — info / neutro

# ─── Identidad visual por fase (Pre/Proc/Post) ─────────────────────────────
# Paleta Azul / Naranja / Verde reutiliza bootstyles del tema darkly.
# Usar PHASE_*_BOOTSTYLE para widgets ttk; PHASE_*_COLOR para tk.Frame/banner.
PHASE_PRE_COLOR  = "#0d6efd"   # Azul
PHASE_PROC_COLOR = "#fd7e14"   # Naranja
PHASE_POST_COLOR = "#198754"   # Verde

PHASE_PRE_BOOTSTYLE  = "info"
PHASE_PROC_BOOTSTYLE = "warning"
PHASE_POST_BOOTSTYLE = "success"

# ─── Estética del canvas (sombras y labels) ────────────────────────────────
# Tk no soporta alpha real; el "glow" se simula con dos create_line
# superpuestos: una linea ancha del color SHADOW_* y otra encima con el
# color principal de la propiedad.
SHADOW_LOAD       = "#3a1818"
SHADOW_SURFACE    = "#2a1818"
SHADOW_CONSTRAINT = "#3a2a10"
LABEL_BG          = "#2a2d33"   # gris-azulado oscuro: contrasta con CANVAS_BG
LABEL_FG          = "#e8e8ea"
# Texto secundario / subtitulos / hints en dialogos (un escalon mas tenue
# que LABEL_FG, mas claro que MENU_DISABLED_FG que es para estado disabled).
# Usar para captions, descripciones bajo titulos, labels de ayuda.
TEXT_MUTED_FG     = "#9ea3aa"

# ─── Paleta unificada de módulos educativos (matplotlib + Tk overlays) ─────
# Alineada con el tema `darkly` del Toplevel chrome (#222222 puro neutral)
# para que las figuras matplotlib y los axes blendeen sin formar "bloques"
# de hue distinto contra el chrome. Tonos NEUTROS (sin tinte azul/violeta
# como los antiguos #1e1e2e o #222233) — pedagógicamente más profesional
# y visualmente más coherente con el resto del software.
#
# Jerarquía visual:
#   EDU_FIG_BG      = chrome (matches Toplevel bg) — la figura "desaparece"
#   EDU_AXES_BG     = un punto más claro → "data area" se separa del chrome
#   EDU_LABEL_BG    = un punto más oscuro que axes → boxes / legend resaltan
#
# Reusar SIEMPRE estas constantes desde education/. No reintroducir literales
# #1e1e2e / #222233 / #1a1a2c (purplish darks eliminados en UX 2026 pase 4).
EDU_FIG_BG    = "#222222"   # matplotlib Figure.facecolor (= darkly chrome)
EDU_AXES_BG   = "#2c2c2c"   # matplotlib Axes.facecolor (≈ chrome + 6% luz)
EDU_LABEL_BG  = "#1f1f1f"   # bbox de text boxes / legend dentro de axes
EDU_GRID      = "#404040"   # grilla / spines tenues
EDU_FG        = "#e8e8ea"   # alias semántico de LABEL_FG para context edu
EDU_FG_MUTED  = "#9ea3aa"   # alias semántico de TEXT_MUTED_FG

# ─── Puntos de Gauss + cuadrado natural (módulos educativos) ───────────────
# Fuente única de verdad de la paleta del glifo de PG y del cuadrado natural
# [-1,1]². Antes vivían como literales locales duplicados en gauss_glyph.py,
# gauss_inset.py y en cada módulo (mod01.._C_BLUE, mod02.._C_SURFACE_LO, el
# hex #d68a7a repetido 6 veces). `education/components/gauss_glyph.py` las
# re-exporta con sus nombres cortos (GAUSS_CANONICAL, ...) para compat.
GAUSS_CANONICAL_COLOR     = "#80deea"   # cian — PG neutral
GAUSS_ACTIVE_COLOR        = "#ffd54f"   # dorado — PG sumado / activo en cuadratura
GAUSS_HALO_COLOR          = "#ff8a65"   # naranja — selección del alumno (snap)
GAUSS_GHOST_COLOR         = "#7a7a85"   # gris — PG disponible no usado
GAUSS_LABEL_OUTLINE_COLOR = "#1f1f29"   # outline sutil del disco filled
# Cuadrado natural [-1,1]² — estilo de referencia de M1, compartido por el
# render matplotlib (mod01) y el tk.Canvas (GaussCoordReadout en M2/M4/M5).
EDU_NATURAL_OUTLINE_COLOR = "#4fa3ff"   # contorno del cuadrado natural
EDU_NATURAL_AXES_COLOR    = "#3a5278"   # ejes ξ, η (cruz en el origen)
EDU_FREE_POINT_COLOR      = "#d68a7a"   # marcador de punto LIBRE (no-Gauss)
EDU_MARKER_OUTLINE_COLOR  = "#ffffff"   # outline blanco de marcadores sobre fondo variable
EDU_SURFACE_LO_COLOR      = "#ff7043"   # naranja-rojo: det J cerca de 0 / negativo (M2)
# Anotaciones geometricas de M0 (calidad de malla) sobre el canvas: el arco
# del peor angulo y la arista/diagonal de Compacidad. Deben contrastar con el
# X-ray rojo/amarillo/verde (HEALTH_*) y con los nodos azul/cian/violeta, por
# eso NO reusan la paleta de salud (se camuflarian sobre el relleno del
# elemento — p.ej. una arista amarilla sobre un elemento amarillo).
EDU_M0_ANGLE_COLOR  = "#ce93d8"   # orquidea — arco del peor angulo (Jacobiano)
EDU_M0_LENGTH_COLOR = "#4dd0e1"   # cian-verdoso — arista Lmin / diagonal Dmax (Compacidad)

# Compatibilidad: MOHR_BG y _TOGGLE_BG_DARK (formula_value_toggle) se
# rebindean a EDU_FIG_BG para unificar el "bloque oscuro" del Mohr inset
# del Post con el de los módulos educativos — todos comparten chrome.

# ─── Overlay flotante (CanvasOverlayModule) ────────────────────────────────
# Fuente unica de verdad del fondo de los paneles flotantes de modulos.
# Antes vivia en gui/widgets/canvas_overlay.py como literal — movido a
# settings para que cualquier widget child del overlay (LatexExpressionImage,
# LatexMatrixImage, status labels) pueda matchear el bg SIN re-importar
# desde gui/.
# CRITICO: OVERLAY_BG alineado con el bg REAL del ttk.Frame en tema darkly
# (#222222, descubierto via ttk.Style().lookup("TFrame", "background")).
# Antes era #252535 y producia un mismatch sutil pero visible entre el
# body del Toplevel y los Frames internos. Cambio en 2026-05.
OVERLAY_BG       = "#222222"   # Fondo del body del CanvasOverlay (= ttk darkly)
OVERLAY_BORDER   = "#3a3a55"   # Borde sutil
OVERLAY_TITLE_FG = "#ffffff"   # Foreground del titulo del header
# Accentos del cuerpo del overlay (usados por los modulos para hints,
# fórmulas secundarias, captions). Pre-cacheados en el warmup para evitar
# misses en los modulos que cambian color.
OVERLAY_ACCENT_BLUE  = "#90caf9"   # Material Blue 200 — formulas secundarias
OVERLAY_ACCENT_MUTED = "#9aa6b5"   # Gris azulado — hints / captions
OVERLAY_ACCENT_AMBER = "#ffd54f"   # Amber 300 — bridge / cross-references

# ─── Tolerancias numéricas ──────────────────────────────────────────────────
NUMERICAL_TOLERANCE = 1e-10
JACOBIAN_MIN_DETERMINANT = 1e-12

# ─── Solucionador ──────────────────────────────────────────────────────────
# Reordenamiento Reverse Cuthill-McKee (RCM) antes de factorizar K_red.
# Reduce el fill-in 2-5x en mallas estructuradas. DESACTIVADO por defecto:
# con el flag en False el output es bit-a-bit idéntico al solver clásico
# (la permutación + despermutación son una identidad numérica). Activarlo
# para comparar rendimiento en mallas grandes (M9).
SOLVER_USE_RCM = False

# ─── Formato de archivos ───────────────────────────────────────────────────
PROJECT_FILE_EXTENSION = ".edufem"
PROJECT_FILE_DESCRIPTION = "Proyecto EduFEM"

# ─── Configuración de usuario (persistencia entre sesiones) ────────────────
USER_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".edufem")
RECENT_FILES_PATH = os.path.join(USER_CONFIG_DIR, "recent.json")
RECENT_FILES_MAX = 10

# ─── Gravedad por defecto ──────────────────────────────────────────────────
DEFAULT_GRAVITY = 9.81

# ─── Decimales por tipo de magnitud ────────────────────────────────────────
# Coherencia visual entre display (tablas, canvas) y editor flotante.
# Defaults pensados para SI N·m / N·mm; ajustar via constante si el caso
# de uso lo requiere. NO exponer como configuracion (decision de UX:
# minimizar opciones; el usuario educativo no las necesita).
DECIMALS_LENGTH       = 3   # X, Y, espesor (coords geometricas)
DECIMALS_FORCE        = 2   # Fx, Fy, q (cargas y reacciones)
DECIMALS_STRESS       = 2   # σ, τ, von Mises (suelen ser grandes)
DECIMALS_DISPLACEMENT = 5   # u, v (siempre pequeños — necesitan precision)
DECIMALS_ANGLE        = 1   # θ en grados


def fmt(value, kind="length"):
    """Formatea un valor numerico con los decimales adecuados a su tipo.

    kind in {"length", "force", "stress", "displacement", "angle"}.
    Si kind no se reconoce, usa 4 decimales como fallback.
    """
    decimals_map = {
        "length": DECIMALS_LENGTH,
        "force": DECIMALS_FORCE,
        "stress": DECIMALS_STRESS,
        "displacement": DECIMALS_DISPLACEMENT,
        "angle": DECIMALS_ANGLE,
    }
    n = decimals_map.get(kind, 4)
    try:
        return f"{float(value):.{n}f}"
    except (TypeError, ValueError):
        return str(value)


# === Constantes migradas del barrido de hex (auditoria 2026-05) ============
# Literales hex que vivian en strings de gui/ y education/ y se centralizaron
# aqui (regla #1: cero hex fuera de settings.py). Agrupadas por dominio.
# -- EDU --
EDU_MAT_ALUMINUM_COLOR    = "#fff176"   # Chip de material de referencia 'aluminio' (nu~0.35) en el...
EDU_MAT_POLYMER_COLOR     = "#ffb74d"   # Chip de material de referencia 'polimero' (nu~0.45) en el...
EDU_MAT_RUBBER_COLOR      = "#ef9a9a"   # Chip de material de referencia 'caucho' (nu~0.49, cuasi-i...
EDU_M1_VERTEX_NODE_COLOR  = "#ff9f43"   # Nodos vertice (corner) del cuadrado natural en M1 (identi...
EDU_M1_CENTER_NODE_COLOR  = "#ce93d8"   # Nodo centroide (N9) del cuadrado natural en M1; mismo val...
EDU_MATRIX_TEXT_COLOR     = "#dcdcdc"   # Texto claro sobre matrices/etiquetas numericas en overlay...
EDU_M6_EDGE_COLOR         = "#ff9f43"   # Naranja de la arista de carga superficial resaltada en el...
EDU_STATUS_FG_COLOR       = "#cfd2d8"   # Gris claro del label de estado (Consolas) en overlays edu...
EDU_PLOT_TICK_COLOR       = "#7a7e88"   # Chrome de plots edu: color de ticks (gris medio). edu_plo...
EDU_PLOT_LABEL_COLOR      = "#a8acb4"   # Chrome de plots edu: color de labels de ejes (gris claro)...
EDU_PLOT_AXIS_COLOR       = "#3a3d44"   # Chrome de plots edu: spines / grid / panes 3D. edu_plot_s...
EDU_PLOT_TITLE_COLOR      = OVERLAY_ACCENT_BLUE  # Color de titulos de ejes en plots edu (acento azul, coherente con los titulos de formula). Consumido por mod07_assembly via edu_plot_style.
QUALITY_BAR_NEUTRAL_COLOR = "#5a5e66"   # Gris neutro de la frontera (cero) en el modo bipolar de Q...
QUALITY_BAR_INK_COLOR     = "#1a1c20"   # Tinta oscura del marcador/badge/ticks de QualityBar (badg...
EDU_INTEGRAND_TEXT_COLOR  = "#dcdcdc"   # Texto del integrando simbolico / ventana de expresion com...
ELEMENT_Q4_DOT_COLOR      = "#cdd2d8"   # Gris claro del mini-icono de nodos Q4 (matchea la columna...
# -- CANVAS --
CANVAS_AXIS_X_COLOR              = "#ef5350"   # Color del eje X del indicador de orientacion del canvas (...
CANVAS_AXIS_Y_COLOR              = "#4fc3f7"   # Color del eje Y del indicador de orientacion del canvas (...
CANVAS_DEFORM_GHOST_COLOR        = "#444466"   # Color de la malla original (fantasma punteado) cuando se ...
CANVAS_ELEM_LABEL_ON_FIELD_COLOR = "#222"   # Color (oscuro) de la etiqueta numerica de elemento cuando...
CANVAS_ELEM_LABEL_COLOR          = "#aaaaaa"   # Color (gris claro) de la etiqueta numerica de elemento so...
CANVAS_COLORBAR_BORDER_COLOR     = "#aaa"   # Color del borde del rectangulo contenedor de la colorbar ...
# -- SURFACE_3D --
SURFACE_3D_EDGE_RAW_COLOR    = "#ffe082"   # Color de las aristas (bordes de las 'tejas') de la superf...
SURFACE_3D_EDGE_SMOOTH_COLOR = "#dddddd"   # Color de las aristas de la superficie 3D en modo SUAVIZAD...
SURFACE_3D_MODE_RAW_COLOR    = "#ffb74d"   # Color del titulo/etiqueta de modo CRUDO en el visor 3D de...
SURFACE_3D_Z0_PLANE_COLOR    = "#5c5c70"   # Color de relleno del plano de referencia z=0 ('horizonte'...
SURFACE_3D_Z0_EDGE_COLOR     = "#888899"   # Color del borde del plano de referencia z=0 del visor 3D ...
# -- TREE/EDITOR/POPUP --
EDITOR_ENTRY_BG           = "#ffffff"   # Fondo blanco del Entry flotante de edicion de celda (alto...
EDITOR_ENTRY_FG           = "#000000"   # Texto/caret negro del Entry flotante de edicion de celda
EDITOR_FOCUS_BORDER_COLOR = "#3399ff"   # Borde de foco (highlight) azul del Entry flotante de edic...
POPUP_BG                  = "#3a3d42"   # Fondo del Toplevel overlay del dropdown custom de combobo...
POPUP_LIST_BG             = "#1c1e22"   # Fondo del Listbox del dropdown custom de combobox (cohere...
POPUP_SELECT_BG           = "#1f6feb"   # Fondo de la opcion seleccionada en el Listbox del dropdow...
TREE_ROW_BG_COLOR         = "#1c1e22"   # Fondo plano uniforme de filas/campo de los Treeview de pr...
TREE_PLACEHOLDER_BG       = "#15161a"   # Fondo de la fila placeholder ('+ doble-click para anadir'...
TREE_PLACEHOLDER_FG       = "#6a6d75"   # Foreground gris desaturado del hint de la fila placeholde...
AUTO_NODE_FG              = "#7a7d85"   # Foreground atenuado de filas read-only de nodos Q9 medios...
# -- HEALTH/DXF --
DXF_PREVIEW_BG_COLOR        = "#222233"   # Fondo del tk.Canvas de preview del DxfImportDialog
DXF_PREVIEW_ELEM_FILL_COLOR = "#2c3e5c"   # Relleno de los Q4 en el preview del DxfImportDialog
DIALOG_MUTED_FG_COLOR       = "#aaa"   # Texto secundario/atenuado en dialogos (nombre de archivo,...
HEALTH_ERROR_LIGHT_COLOR    = "#ef9a9a"   # Texto de error claro sobre fondo oscuro (mensaje 'sin pol...
ABOUT_INFO_FG_COLOR         = "#ccc"   # Texto informativo del AboutDialog
HEALTH_SUBTITLE_FG          = "#a0a0a8"   # Subtitulo gris del header del HealthReportDialog
HEALTH_CARD_BORDER_COLOR    = "#3a3d42"   # Borde (highlightbackground) de las tarjetas de issue del ...
HEALTH_HINT_FG              = "#b0b0b8"   # Texto del hint educativo colapsable del HealthReportDialog
# -- WIDGETS/DIALOGOS --
THEORY_VIEWER_BG_COLOR         = "#2b2b3c"   # Fondo del tk.Canvas que muestra el PDF de teoria en Theor...
DETAILS_NAT_FG_COLOR           = "#aaaaaa"   # Color del texto de la linea de coordenadas naturales (Nat...
RESULT_CELL_HIGHLIGHT_FG       = "#000000"   # Color del texto (negro) del overlay amarillo que resalta ...
PROBE_TOOLTIP_BORDER_COLOR     = "#555"   # Color de borde por defecto del tooltip del probe (ProbeTo...
STATUS_BAR_BG_COLOR            = "#1c1e22"   # Fondo de los widgets tk.Label de la barra de estado (ORTH...
BREADCRUMB_VISITED_FG_COLOR    = "#ffffff"   # Foreground del chip del breadcrumb del pipeline FEM cuand...
BREADCRUMB_INACTIVE_FG_COLOR   = "#555"   # Foreground del chip del breadcrumb no visitado / inactivo...
OVERLAY_CLOSE_HOVER_COLOR      = "#c0392b"   # Fondo rojo del boton cerrar del CanvasOverlay al pasar el...
PHASE_BANNER_TITLE_FG_COLOR    = "#ffffff"   # Foreground del titulo del banner de fase (texto blanco so...
PHASE_BANNER_SUBTITLE_FG_COLOR = "#f0f0f0"   # Foreground del subtitulo del banner de fase (gris muy cla...
TOOLTIP_BG_COLOR               = "#2a2a3a"   # Fondo del Toplevel de ToolTip.
TOOLTIP_FG_COLOR               = "#e4e4e4"   # Foreground (texto) del ToolTip.
MODULE_HEADER_FG_COLOR         = "#dddddd"   # Foreground por defecto del titulo del panel de modulos ed...
MODULE_DESC_FG_COLOR           = "#888"   # Foreground de la descripcion/subtitulo de cada modulo en ...
MODULE_EMPTY_FG_COLOR          = "#666"   # Foreground del mensaje de estado vacio (sin modulos dispo...
WEBP_PLAYER_BG_COLOR           = "#1a1a1a"   # Color de fondo por defecto del widget WebpPlayer (letterb...

# ─── Tipografía global ─────────────────────────────────────────────────────
# Dual coherente: Segoe UI para UI/texto + Consolas para código/monoespacio.
# El editor flotante de celdas hereda FONT_UI_LARGE para que NO cambie de
# tamaño al pasar de "vista" a "edición".
FONT_UI         = ("Segoe UI", 9)               # Default UI
FONT_UI_LARGE   = ("Segoe UI", 10)              # Treeview body / editores
FONT_UI_BOLD    = ("Segoe UI Semibold", 9)      # Treeview headings, labels
FONT_MONO       = ("Consolas", 10)              # Código / monoespacio
FONT_MONO_SMALL = ("Consolas", 9)               # Coordenadas canvas, hints
TREE_ROW_HEIGHT = 22                            # Altura de fila Treeview (compacto, evita overflow)
