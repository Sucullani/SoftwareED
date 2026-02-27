"""
Clase BoundaryCondition: Restricciones de desplazamiento en un nodo.
"""


class BoundaryCondition:
    """Restricción de desplazamiento (apoyo) en un nodo."""

    def __init__(self, node_id, restrain_x=False, restrain_y=False):
        self.node_id = node_id
        self.restrain_x = bool(restrain_x)
        self.restrain_y = bool(restrain_y)

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

    def get_restrained_dofs(self):
        """
        Retorna la lista de GDL globales restringidos.
        Nodo i tiene GDL: [2*(i-1), 2*(i-1)+1] (0-indexed).
        """
        dofs = []
        if self.restrain_x:
            dofs.append(2 * (self.node_id - 1))
        if self.restrain_y:
            dofs.append(2 * (self.node_id - 1) + 1)
        return dofs

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "restrain_x": self.restrain_x,
            "restrain_y": self.restrain_y,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        rx = "X" if self.restrain_x else "·"
        ry = "Y" if self.restrain_y else "·"
        return f"BC(nodo={self.node_id}, [{rx},{ry}])"
