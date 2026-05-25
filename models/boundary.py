"""
Clase BoundaryCondition: Restricciones de desplazamiento en un nodo.

Desde 2026-05 admite valores prescritos no-cero (ux_value, uy_value) para
soportar el Método de Soluciones Manufacturadas (MMS), donde se impone
u(x,y) ≠ 0 en el borde del dominio. La serialización es backward-compat
con archivos .edufem legacy que no tienen esos campos.
"""


class BoundaryCondition:
    """Restricción de desplazamiento (apoyo) en un nodo.

    El comportamiento clasico (apoyos con desplazamiento cero) se obtiene
    dejando ux_value=0 y uy_value=0 (default). Solo MMS y similares fijan
    valores no-cero.
    """

    def __init__(self, node_id, restrain_x=False, restrain_y=False,
                 ux_value=0.0, uy_value=0.0):
        self.node_id = node_id
        self.restrain_x = bool(restrain_x)
        self.restrain_y = bool(restrain_y)
        self.ux_value = float(ux_value)
        self.uy_value = float(uy_value)

    @property
    def is_fixed(self):
        """Retorna True si ambas direcciones están restringidas (empotramiento)."""
        return self.restrain_x and self.restrain_y

    @property
    def is_roller_x(self):
        """Restringido solo en X (rodillo vertical)."""
        return self.restrain_x and not self.restrain_y

    @property
    def is_roller_y(self):
        """Restringido solo en Y (rodillo horizontal)."""
        return not self.restrain_x and self.restrain_y

    @property
    def has_prescribed_displacement(self):
        """True si algun DOF restringido tiene valor prescrito no nulo."""
        if self.restrain_x and self.ux_value != 0.0:
            return True
        if self.restrain_y and self.uy_value != 0.0:
            return True
        return False

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "restrain_x": self.restrain_x,
            "restrain_y": self.restrain_y,
            "ux_value": self.ux_value,
            "uy_value": self.uy_value,
        }

    @classmethod
    def from_dict(cls, data):
        # Backward-compat: archivos .edufem legacy no tienen ux_value/uy_value.
        return cls(
            node_id=data["node_id"],
            restrain_x=data.get("restrain_x", False),
            restrain_y=data.get("restrain_y", False),
            ux_value=data.get("ux_value", 0.0),
            uy_value=data.get("uy_value", 0.0),
        )

    def __repr__(self):
        rx = "X" if self.restrain_x else "·"
        ry = "Y" if self.restrain_y else "·"
        if self.has_prescribed_displacement:
            return (f"BC(nodo={self.node_id}, [{rx},{ry}], "
                    f"u=({self.ux_value:.4g},{self.uy_value:.4g}))")
        return f"BC(nodo={self.node_id}, [{rx},{ry}])"
