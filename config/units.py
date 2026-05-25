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
    "Técnico (kgf, cm, kgf/cm²)": {
        "longitud": "cm",
        "fuerza": "kgf",
        "esfuerzo": "kgf/cm²",
        "descripcion": "Sistema Técnico con kilogramo-fuerza"
    },
    "Técnico (tonf, m, tonf/m²)": {
        "longitud": "m",
        "fuerza": "tonf",
        "esfuerzo": "tonf/m²",
        "descripcion": "Sistema Técnico con tonelada-fuerza"
    },
}

DEFAULT_UNIT_SYSTEM = "SI (N, mm, MPa)"


def get_unit_system_names():
    """Retorna la lista de nombres de sistemas de unidades disponibles."""
    return list(UNIT_SYSTEMS.keys())


def get_unit_labels(system_name):
    """Retorna las etiquetas de unidades para un sistema dado."""
    return UNIT_SYSTEMS.get(system_name, UNIT_SYSTEMS[DEFAULT_UNIT_SYSTEM])


# ─── Conversion de unidades a SI base (N, m, Pa) ─────────────────────────
# Factores multiplicativos: valor_en_SI = valor_local * factor.
# Composicion entre sistemas: factor(from -> to) = factor_from / factor_to.

_LENGTH_TO_M = {
    "m":  1.0,
    "mm": 1.0e-3,
    "cm": 1.0e-2,
    "in": 0.0254,
    "ft": 0.3048,
}

_FORCE_TO_N = {
    "N":    1.0,
    "kN":   1.0e3,
    "lb":   4.4482216152605,
    "kip":  4448.2216152605,
    "kgf":  9.80665,
    "tonf": 9806.65,
}

_STRESS_TO_PA = {
    "Pa":      1.0,
    "kPa":     1.0e3,
    "MPa":     1.0e6,
    "GPa":     1.0e9,
    "psi":     6894.757293168,
    "ksi":     6_894_757.293168,
    "kgf/cm²": 98066.5,
    "tonf/m²": 9806.65,
}


def _factor(table, label):
    """Lookup tolerante: retorna el factor o None si la etiqueta no es
    convertible (etiqueta vacia o no canonica).
    """
    if not label or label == "-":
        return None
    return table.get(label)


def can_convert(from_system, to_system):
    """True si AMBOS sistemas estan en UNIT_SYSTEMS con etiquetas canonicas
    para length, force y stress. Si alguno es desconocido (e.g. un .edufem
    legacy con un nombre no presente), devuelve False.
    """
    if from_system == to_system:
        return False  # nada que convertir
    a = UNIT_SYSTEMS.get(from_system)
    b = UNIT_SYSTEMS.get(to_system)
    if not a or not b:
        return False
    for table, key in (
        (_LENGTH_TO_M, "longitud"),
        (_FORCE_TO_N,  "fuerza"),
        (_STRESS_TO_PA, "esfuerzo"),
    ):
        if _factor(table, a.get(key)) is None:
            return False
        if _factor(table, b.get(key)) is None:
            return False
    return True


def get_conversion_factors(from_system, to_system):
    """Devuelve los factores multiplicativos para llevar valores expresados
    en `from_system` a `to_system`. Cada cantidad fisica del modelo tiene
    un factor distinto:

        length              : longitudes (coords, espesor)
        force               : fuerzas puntuales (Fx, Fy)
        stress              : tensiones (E del material, sigma)
        force_per_length    : cargas distribuidas q
        acceleration        : gravedad g (L/s², solo escala length)

    Requiere que `can_convert(from_system, to_system)` sea True. Lanza
    `ValueError` en caso contrario.
    """
    if not can_convert(from_system, to_system):
        raise ValueError(
            f"No se puede convertir entre '{from_system}' y '{to_system}' "
            f"(uno de los sistemas no esta en UNIT_SYSTEMS o tiene etiquetas no canonicas)"
        )
    a = UNIT_SYSTEMS[from_system]
    b = UNIT_SYSTEMS[to_system]
    length_factor = _LENGTH_TO_M[a["longitud"]]  / _LENGTH_TO_M[b["longitud"]]
    force_factor  = _FORCE_TO_N[a["fuerza"]]    / _FORCE_TO_N[b["fuerza"]]
    stress_factor = _STRESS_TO_PA[a["esfuerzo"]] / _STRESS_TO_PA[b["esfuerzo"]]
    return {
        "length":           length_factor,
        "force":            force_factor,
        "stress":           stress_factor,
        "force_per_length": force_factor / length_factor,
        "acceleration":     length_factor,
    }
