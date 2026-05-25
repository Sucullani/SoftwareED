"""
Clase Material: Propiedades mecánicas del material.

El atributo `color` fue eliminado en 2026-05 (no era consumido por el
solver ni por el canvas — solo aparecia en el MaterialDialog y en el
CSV export). Si se necesita reintroducir como mejora visual futura,
agregar como campo opcional en `__init__` con backward-compat en
`from_dict` (igual que se hizo con `gravity_x/gravity_y`).
"""

# ─── Librería de materiales predefinidos ────────────────────────────────────
# Solo Acero y Concreto: cubren ~90% de los problemas FEM de cursos de
# ingenieria estructural / mecanica (Aluminio, Cobre, Titanio retirados —
# el usuario los define con 'Nuevo' si los necesita).
DEFAULT_MATERIALS = {
    "Acero Estructural": {
        "E": 200000.0,  # MPa
        "nu": 0.3,
        "density": 7850.0,  # kg/m³
    },
    "Concreto f'c=21 MPa": {
        "E": 21538.0,
        "nu": 0.2,
        "density": 2400.0,
    },
}


class Material:
    """Material elástico lineal isótropo."""

    def __init__(self, name="Acero Estructural", E=200000.0, nu=0.3,
                 density=7850.0):
        self.name = name
        self.E = float(E)           # Módulo de Young
        self.nu = float(nu)         # Coeficiente de Poisson
        self.density = float(density)  # Densidad

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
        }

    @classmethod
    def from_dict(cls, data):
        # Backward-compat: ignorar `color` de archivos .edufem legacy.
        clean = {k: v for k, v in data.items()
                 if k in ("name", "E", "nu", "density")}
        return cls(**clean)

    @classmethod
    def get_default_library(cls):
        """Retorna la librería de materiales predefinidos como objetos Material."""
        return {
            name: cls(name=name, **props)
            for name, props in DEFAULT_MATERIALS.items()
        }

    def __repr__(self):
        return f"Material('{self.name}', E={self.E}, ν={self.nu})"
