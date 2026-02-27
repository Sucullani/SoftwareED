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
CANVAS_FONT_SIZE = 9

# ─── Tolerancias numéricas ──────────────────────────────────────────────────
NUMERICAL_TOLERANCE = 1e-10
JACOBIAN_MIN_DETERMINANT = 1e-12

# ─── Formato de archivos ───────────────────────────────────────────────────
PROJECT_FILE_EXTENSION = ".edufem"
PROJECT_FILE_DESCRIPTION = "Proyecto EduFEM"
CSV_DELIMITER = ","
