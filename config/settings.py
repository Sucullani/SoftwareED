"""
Configuración global del software educativo FEM.
Constantes, rutas y valores por defecto.
"""

import os

# ─── Información de la aplicación ───────────────────────────────────────────
APP_NAME = "EduFEM - Software Educativo de Elementos Finitos"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Tesis de Grado"

# ─── Rutas ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
HELP_DIR = os.path.join(RESOURCES_DIR, "help")
MATERIALS_DB_PATH = os.path.join(RESOURCES_DIR, "materials_db.json")

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
CANVAS_NODE_RADIUS = 4
# Nodos extra de Q9 (medios de arista y centroide): más pequeños y de color
# distinto para diferenciarlos visualmente de los vértices.
CANVAS_NODE_MID_COLOR    = "#6fb8ff"   # Azul claro — medios de arista (N5..N8)
CANVAS_NODE_CENTER_COLOR = "#b86fff"   # Violeta — centroide (N9)
CANVAS_NODE_MID_RADIUS   = 3
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

# ─── Tolerancias numéricas ──────────────────────────────────────────────────
NUMERICAL_TOLERANCE = 1e-10
JACOBIAN_MIN_DETERMINANT = 1e-12

# ─── Formato de archivos ───────────────────────────────────────────────────
PROJECT_FILE_EXTENSION = ".edufem"
PROJECT_FILE_DESCRIPTION = "Proyecto EduFEM"
CSV_DELIMITER = ","

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
