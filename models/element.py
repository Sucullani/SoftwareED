"""
Clase Element: Representa un elemento cuadrilátero (Q4 o Q9) de la malla.
"""


class Element:
    """Elemento cuadrilátero isoparamétrico (Q4 o Q9)."""

    def __init__(self, elem_id, node_ids, thickness=1.0, material_name="Acero Estructural"):
        """
        Parámetros:
            elem_id: Identificador del elemento.
            node_ids: Lista de IDs de nodos de conectividad.
                      Q4: [n1, n2, n3, n4] (4 nodos, sentido antihorario)
                      Q9: [n1, n2, n3, n4, n5, n6, n7, n8, n9] (9 nodos)
            thickness: Espesor del elemento.
            material_name: Nombre del material asignado.
        """
        self.id = elem_id
        self.node_ids = list(node_ids)
        self.thickness = float(thickness)
        self.material_name = material_name

    @property
    def num_nodes(self):
        """Número de nodos del elemento (4 o 9)."""
        return len(self.node_ids)

    @property
    def element_type(self):
        """Retorna 'Q4' o 'Q9' según el número de nodos."""
        return "Q4" if self.num_nodes == 4 else "Q9"

    @property
    def num_dof(self):
        """Grados de libertad del elemento (2 por nodo)."""
        return self.num_nodes * 2

    def get_dof_indices(self):
        """
        Retorna los índices de GDL globales del elemento.
        Nodo i tiene GDL: [2*i - 2, 2*i - 1] (0-indexed).
        """
        dof = []
        for nid in self.node_ids:
            dof.append(2 * (nid - 1))      # ux del nodo
            dof.append(2 * (nid - 1) + 1)  # uy del nodo
        return dof

    def to_dict(self):
        return {
            "id": self.id,
            "node_ids": self.node_ids,
            "thickness": self.thickness,
            "material_name": self.material_name,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            elem_id=data["id"],
            node_ids=data["node_ids"],
            thickness=data["thickness"],
            material_name=data["material_name"],
        )

    def __repr__(self):
        return (f"Element({self.id}, {self.element_type}, "
                f"nodes={self.node_ids}, t={self.thickness})")
