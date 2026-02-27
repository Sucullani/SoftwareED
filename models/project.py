"""
Clase ProjectModel: Modelo central que contiene todos los datos del proyecto FEM.
Actúa como la capa de datos del patrón MVC.
"""

from config.settings import (
    DEFAULT_ANALYSIS_TYPE, DEFAULT_ELEMENT_TYPE, DEFAULT_THICKNESS
)
from config.units import DEFAULT_UNIT_SYSTEM
from models.node import Node
from models.element import Element
from models.material import Material
from models.load import NodalLoad, SurfaceLoad
from models.boundary import BoundaryCondition


class ProjectModel:
    """Modelo central del proyecto FEM. Almacena todos los datos del modelo."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reinicia el proyecto a valores por defecto."""
        # Configuración del análisis
        self.project_name = "Nuevo Proyecto"
        self.analysis_type = DEFAULT_ANALYSIS_TYPE
        self.element_type = DEFAULT_ELEMENT_TYPE
        self.unit_system = DEFAULT_UNIT_SYSTEM
        self.default_thickness = DEFAULT_THICKNESS

        # Datos del modelo
        self.nodes = {}              # {id: Node}
        self.elements = {}           # {id: Element}
        self.materials = {}          # {name: Material}
        self.nodal_loads = {}        # {node_id: NodalLoad}
        self.surface_loads = []      # [SurfaceLoad, ...]
        self.boundary_conditions = {}  # {node_id: BoundaryCondition}

        # Resultados (se llenan tras el análisis)
        self.is_solved = False
        self.displacements = None     # Vector de desplazamientos u
        self.global_K = None          # Matriz de rigidez global
        self.global_F = None          # Vector de fuerzas global
        self.stresses = {}            # {elem_id: {gauss_stresses, nodal_stresses}}

        # Inicializar librería de materiales por defecto
        self.materials = Material.get_default_library()

        # Ruta del archivo actual
        self.file_path = None
        self.is_modified = False

    # ─── Gestión de nodos ───────────────────────────────────────────────

    def add_node(self, x, y, node_id=None):
        """Agrega un nodo. Si node_id es None, asigna el siguiente ID."""
        if node_id is None:
            node_id = self._next_node_id()
        node = Node(node_id, x, y)
        self.nodes[node_id] = node
        self.is_modified = True
        self.is_solved = False
        return node

    def remove_node(self, node_id):
        """Elimina un nodo y todas sus referencias."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            # Eliminar cargas nodales del nodo
            if node_id in self.nodal_loads:
                del self.nodal_loads[node_id]
            # Eliminar restricciones del nodo
            if node_id in self.boundary_conditions:
                del self.boundary_conditions[node_id]
            self.is_modified = True
            self.is_solved = False

    def _next_node_id(self):
        """Retorna el siguiente ID de nodo disponible."""
        if not self.nodes:
            return 1
        return max(self.nodes.keys()) + 1

    # ─── Gestión de elementos ───────────────────────────────────────────

    def add_element(self, node_ids, thickness=None, material_name=None, elem_id=None):
        """Agrega un elemento."""
        if elem_id is None:
            elem_id = self._next_element_id()
        if thickness is None:
            thickness = self.default_thickness
        if material_name is None:
            material_name = list(self.materials.keys())[0]
        elem = Element(elem_id, node_ids, thickness, material_name)
        self.elements[elem_id] = elem
        self.is_modified = True
        self.is_solved = False
        return elem

    def remove_element(self, elem_id):
        """Elimina un elemento."""
        if elem_id in self.elements:
            del self.elements[elem_id]
            self.is_modified = True
            self.is_solved = False

    def _next_element_id(self):
        if not self.elements:
            return 1
        return max(self.elements.keys()) + 1

    # ─── Gestión de cargas ──────────────────────────────────────────────

    def set_nodal_load(self, node_id, fx, fy):
        """Agrega o actualiza una carga nodal."""
        self.nodal_loads[node_id] = NodalLoad(node_id, fx, fy)
        self.is_modified = True
        self.is_solved = False

    def remove_nodal_load(self, node_id):
        if node_id in self.nodal_loads:
            del self.nodal_loads[node_id]
            self.is_modified = True
            self.is_solved = False

    def add_surface_load(self, element_id, node_start, node_end,
                         q_start, q_end, angle=0.0):
        """Agrega una carga superficial."""
        load = SurfaceLoad(element_id, node_start, node_end,
                           q_start, q_end, angle)
        self.surface_loads.append(load)
        self.is_modified = True
        self.is_solved = False
        return load

    # ─── Gestión de restricciones ───────────────────────────────────────

    def set_boundary_condition(self, node_id, restrain_x, restrain_y):
        """Agrega o actualiza una restricción de desplazamiento."""
        self.boundary_conditions[node_id] = BoundaryCondition(
            node_id, restrain_x, restrain_y
        )
        self.is_modified = True
        self.is_solved = False

    def remove_boundary_condition(self, node_id):
        if node_id in self.boundary_conditions:
            del self.boundary_conditions[node_id]
            self.is_modified = True
            self.is_solved = False

    # ─── Propiedades del modelo ─────────────────────────────────────────

    @property
    def num_nodes(self):
        return len(self.nodes)

    @property
    def num_elements(self):
        return len(self.elements)

    @property
    def total_dof(self):
        """Total de grados de libertad del modelo."""
        return self.num_nodes * 2

    def get_restrained_dofs(self):
        """Retorna la lista de todos los GDL restringidos (0-indexed)."""
        dofs = []
        for bc in self.boundary_conditions.values():
            dofs.extend(bc.get_restrained_dofs())
        return sorted(dofs)

    def get_free_dofs(self):
        """Retorna la lista de GDL libres."""
        restrained = set(self.get_restrained_dofs())
        return [i for i in range(self.total_dof) if i not in restrained]

    # ─── Serialización ──────────────────────────────────────────────────

    def to_dict(self):
        """Serializa todo el proyecto a un diccionario."""
        return {
            "project_name": self.project_name,
            "analysis_type": self.analysis_type,
            "element_type": self.element_type,
            "unit_system": self.unit_system,
            "default_thickness": self.default_thickness,
            "nodes": {str(k): v.to_dict() for k, v in self.nodes.items()},
            "elements": {str(k): v.to_dict() for k, v in self.elements.items()},
            "materials": {k: v.to_dict() for k, v in self.materials.items()},
            "nodal_loads": {str(k): v.to_dict()
                           for k, v in self.nodal_loads.items()},
            "surface_loads": [sl.to_dict() for sl in self.surface_loads],
            "boundary_conditions": {str(k): v.to_dict()
                                    for k, v in self.boundary_conditions.items()},
        }

    @classmethod
    def from_dict(cls, data):
        """Reconstruye el proyecto desde un diccionario."""
        project = cls()
        project.project_name = data.get("project_name", "Proyecto")
        project.analysis_type = data.get("analysis_type", DEFAULT_ANALYSIS_TYPE)
        project.element_type = data.get("element_type", DEFAULT_ELEMENT_TYPE)
        project.unit_system = data.get("unit_system", DEFAULT_UNIT_SYSTEM)
        project.default_thickness = data.get("default_thickness", DEFAULT_THICKNESS)

        # Reconstituir objetos
        project.nodes = {
            int(k): Node.from_dict(v) for k, v in data.get("nodes", {}).items()
        }
        project.elements = {
            int(k): Element.from_dict(v)
            for k, v in data.get("elements", {}).items()
        }
        project.materials = {
            k: Material.from_dict(v)
            for k, v in data.get("materials", {}).items()
        }
        project.nodal_loads = {
            int(k): NodalLoad.from_dict(v)
            for k, v in data.get("nodal_loads", {}).items()
        }
        project.surface_loads = [
            SurfaceLoad.from_dict(sl)
            for sl in data.get("surface_loads", [])
        ]
        project.boundary_conditions = {
            int(k): BoundaryCondition.from_dict(v)
            for k, v in data.get("boundary_conditions", {}).items()
        }
        return project

    def __repr__(self):
        return (f"ProjectModel('{self.project_name}', "
                f"{self.num_nodes} nodos, {self.num_elements} elems)")
