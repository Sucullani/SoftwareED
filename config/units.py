"""
Sistemas de unidades para el software educativo FEM.
Define unidades predefinidas y permite configuración personalizada.
"""


# ─── Sistemas de unidades predefinidos ──────────────────────────────────────
UNIT_SYSTEMS = {
    "SI (N, m, Pa)": {
        "longitud": "m",
        "fuerza": "N",
        "esfuerzo": "Pa",
        "descripcion": "Sistema Internacional"
    },
    "SI (kN, m, kPa)": {
        "longitud": "m",
        "fuerza": "kN",
        "esfuerzo": "kPa",
        "descripcion": "Sistema Internacional (kilo)"
    },
    "SI (N, mm, MPa)": {
        "longitud": "mm",
        "fuerza": "N",
        "esfuerzo": "MPa",
        "descripcion": "Sistema Internacional (milímetros)"
    },
    "SI (kN, mm, GPa)": {
        "longitud": "mm",
        "fuerza": "kN",
        "esfuerzo": "GPa",
        "descripcion": "Sistema Internacional (kilo-milímetros)"
    },
    "Imperial (lb, in, psi)": {
        "longitud": "in",
        "fuerza": "lb",
        "esfuerzo": "psi",
        "descripcion": "Sistema Imperial"
    },
    "Imperial (kip, in, ksi)": {
        "longitud": "in",
        "fuerza": "kip",
        "esfuerzo": "ksi",
        "descripcion": "Sistema Imperial (kilo-libras)"
    },
    "Personalizado": {
        "longitud": "-",
        "fuerza": "-",
        "esfuerzo": "-",
        "descripcion": "Definido por el usuario"
    },
}

DEFAULT_UNIT_SYSTEM = "SI (N, mm, MPa)"


def get_unit_system_names():
    """Retorna la lista de nombres de sistemas de unidades disponibles."""
    return list(UNIT_SYSTEMS.keys())


def get_unit_labels(system_name):
    """Retorna las etiquetas de unidades para un sistema dado."""
    return UNIT_SYSTEMS.get(system_name, UNIT_SYSTEMS[DEFAULT_UNIT_SYSTEM])
