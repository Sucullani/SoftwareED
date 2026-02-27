"""
Clase Material: Propiedades mecánicas del material.
"""

# ─── Librería de materiales predefinidos ────────────────────────────────────
DEFAULT_MATERIALS = {
    "Acero Estructural": {
        "E": 200000.0,  # MPa
        "nu": 0.3,
        "density": 7850.0,  # kg/m³
        "color": "#4fc3f7",
    },
    "Aluminio 6061-T6": {
        "E": 68900.0,
        "nu": 0.33,
        "density": 2700.0,
        "color": "#81c784",
    },
    "Concreto f'c=21 MPa": {
        "E": 21538.0,
        "nu": 0.2,
        "density": 2400.0,
        "color": "#bdbdbd",
    },
    "Cobre": {
        "E": 117000.0,
        "nu": 0.34,
        "density": 8960.0,
        "color": "#ffb74d",
    },
    "Titanio Ti-6Al-4V": {
        "E": 113800.0,
        "nu": 0.342,
        "density": 4430.0,
        "color": "#ce93d8",
    },
}


class Material:
    """Material elástico lineal isótropo."""

    def __init__(self, name="Acero Estructural", E=200000.0, nu=0.3,
                 density=7850.0, color="#4fc3f7"):
        self.name = name
        self.E = float(E)           # Módulo de Young
        self.nu = float(nu)         # Coeficiente de Poisson
        self.density = float(density)  # Densidad
        self.color = color

    def validate(self):
        """Valida que las propiedades sean físicamente válidas."""
        errors = []
        if self.E <= 0:
            errors.append("El módulo de Young (E) debe ser positivo.")
        if not (-1.0 < self.nu < 0.5):
            errors.append("El coef. de Poisson (ν) debe estar entre -1 y 0.5.")
        if self.density < 0:
            errors.append("La densidad no puede ser negativa.")
        return errors

    def to_dict(self):
        return {
            "name": self.name,
            "E": self.E,
            "nu": self.nu,
            "density": self.density,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    @classmethod
    def get_default_library(cls):
        """Retorna la librería de materiales predefinidos como objetos Material."""
        return {
            name: cls(name=name, **props)
            for name, props in DEFAULT_MATERIALS.items()
        }

    def __repr__(self):
        return f"Material('{self.name}', E={self.E}, ν={self.nu})"
