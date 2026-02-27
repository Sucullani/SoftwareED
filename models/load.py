"""
Clases de cargas: NodalLoad y SurfaceLoad.
"""


class NodalLoad:
    """Carga puntual aplicada a un nodo."""

    def __init__(self, node_id, fx=0.0, fy=0.0):
        self.node_id = node_id
        self.fx = float(fx)
        self.fy = float(fy)

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "fx": self.fx,
            "fy": self.fy,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"NodalLoad(nodo={self.node_id}, Fx={self.fx}, Fy={self.fy})"


class SurfaceLoad:
    """Carga superficial trapezoidal en un borde de elemento."""

    def __init__(self, element_id, node_start, node_end,
                 q_start=0.0, q_end=0.0, angle=0.0):
        """
        Parámetros:
            element_id: ID del elemento al que pertenece el borde.
            node_start: Nodo inicial del borde cargado.
            node_end: Nodo final del borde cargado.
            q_start: Magnitud de la carga en el nodo inicial.
            q_end: Magnitud de la carga en el nodo final.
            angle: Ángulo de aplicación en grados (0° = normal al borde).
        """
        self.element_id = element_id
        self.node_start = node_start
        self.node_end = node_end
        self.q_start = float(q_start)
        self.q_end = float(q_end)
        self.angle = float(angle)

    def to_dict(self):
        return {
            "element_id": self.element_id,
            "node_start": self.node_start,
            "node_end": self.node_end,
            "q_start": self.q_start,
            "q_end": self.q_end,
            "angle": self.angle,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return (f"SurfaceLoad(elem={self.element_id}, "
                f"{self.node_start}→{self.node_end}, "
                f"q=[{self.q_start}, {self.q_end}], θ={self.angle}°)")
