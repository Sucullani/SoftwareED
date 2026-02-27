"""
Clase Node: Representa un nodo en la malla de elementos finitos.
"""


class Node:
    """Un nodo con coordenadas (x, y) en el espacio 2D."""

    def __init__(self, node_id, x=0.0, y=0.0):
        self.id = node_id
        self.x = float(x)
        self.y = float(y)

    @property
    def coords(self):
        """Retorna las coordenadas como tupla (x, y)."""
        return (self.x, self.y)

    def to_dict(self):
        """Serializa el nodo a diccionario para guardar proyecto."""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
        }

    @classmethod
    def from_dict(cls, data):
        """Crea un nodo desde un diccionario."""
        return cls(
            node_id=data["id"],
            x=data["x"],
            y=data["y"],
        )

    def __repr__(self):
        return f"Node({self.id}, x={self.x}, y={self.y})"
