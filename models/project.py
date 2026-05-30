"""
Clase ProjectModel: Modelo central que contiene todos los datos del proyecto FEM.
Actúa como la capa de datos del patrón MVC.
"""

from config.settings import (
    DEFAULT_ANALYSIS_TYPE, DEFAULT_ELEMENT_TYPE, DEFAULT_THICKNESS,
    DEFAULT_GRAVITY,
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
        # Gravedad como VECTOR (gx, gy) en m/s². Default (0, -DEFAULT_GRAVITY)
        # = gravedad terrestre estandar apuntando hacia -Y. Generaliza el
        # campo legacy `gravity` (escalar) — desde 2026-05-16 movido al
        # menu Modelo > Gravedad despues de Materiales (jerarquia FEM).
        # Backward-compat: `from_dict` migra `gravity: 9.81` -> `(0, -9.81)`.
        self.gravity_x = 0.0
        self.gravity_y = -DEFAULT_GRAVITY
        self.include_gravity = False

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

        # Cache del node_index_map: invalidado por add_node/remove_node/change_node_id.
        # None indica "stale": se recomputa en el primer acceso. O(N log N) solo
        # al invalidar, O(1) en todos los accesos posteriores dentro de la misma
        # operacion (e.g. ensamblaje que recorre todos los elementos).
        self._node_index_map_cache = None

        # Índice inverso nodo → conjunto de elementos que lo contienen.
        # Mantenido por add_element/remove_element. Permite is_node_referenced y
        # cascadas en O(1) en vez de O(E) por nodo.
        # NO se serializa en to_dict; se reconstruye en restore_from_dict/from_dict.
        self._node_to_elements: dict = {}

    # ─── Gestión de nodos ───────────────────────────────────────────────

    def add_node(self, x, y, node_id=None):
        """Agrega un nodo. Si node_id es None, asigna el siguiente ID."""
        if node_id is None:
            node_id = self._next_node_id()
        node = Node(node_id, x, y)
        self.nodes[node_id] = node
        self._node_index_map_cache = None
        self.is_modified = True
        self.is_solved = False
        return node

    def remove_node(self, node_id):
        """Elimina un nodo y TODAS sus referencias en el modelo:
        cargas nodales, restricciones y cargas superficiales que lo
        referencien como `node_start` o `node_end`.

        Si el nodo aparece en `element.node_ids` (es vertice de algun
        elemento), se elimina igual -- el elemento queda con un node_id
        invalido y el panel de salud lo flaggeara como error critico.
        El caller deberia usar `remove_element` para borrar el elemento
        primero o aceptar la inconsistencia.
        """
        if node_id not in self.nodes:
            return
        del self.nodes[node_id]
        self._node_index_map_cache = None
        # Mantener el indice inverso coherente (el nodo ya no existe).
        self._node_to_elements.pop(node_id, None)
        # Cargas nodales asociadas
        if node_id in self.nodal_loads:
            del self.nodal_loads[node_id]
        # Restricciones asociadas
        if node_id in self.boundary_conditions:
            del self.boundary_conditions[node_id]
        # Surface loads que referencien este nodo como extremo de arista
        self.surface_loads = [
            sl for sl in self.surface_loads
            if sl.node_start != node_id and sl.node_end != node_id
        ]
        self.is_modified = True
        self.is_solved = False

    def remove_node_with_cascade(self, node_id, *, cleanup_orphans=True):
        """Borra un nodo y cascadea simetricamente al de `remove_element`.

        El usuario pide "borrar este nodo". El cascade decide que mas
        debe irse para que el modelo no quede inconsistente:

        1) Borra todos los elementos que contienen al nodo.
        2) Por cada elemento eliminado, propaga el cleanup de mid/center
           nodes huerfanos (los que no quedan en ningun otro elemento ni
           tienen datos del usuario). Los nodos con datos del usuario se
           preservan como huerfanos visibles -- el panel de salud los
           flaggeara, pero no se pierden.
        3) Borra el nodo objetivo + sus cargas / BCs / surface refs.

        Si `cleanup_orphans=False` se comporta como `remove_node` legacy:
        borra solo el nodo y sus refs directas, dejando elementos con
        node_ids invalidos que el panel de salud flaggeara.

        Retorna:
            dict con cuatro claves:
                - "node_deleted": True/False
                - "elements_deleted": list[int] de element_ids eliminados
                - "nodes_deleted": list[int] de node_ids eliminados
                  (incluye al objetivo si fue borrado)
                - "nodes_preserved": list[int] de node_ids preservados
                  como huerfanos (tenian datos del usuario)
        """
        result = {
            "node_deleted": False,
            "elements_deleted": [],
            "nodes_deleted": [],
            "nodes_preserved": [],
        }
        if node_id not in self.nodes:
            return result

        if cleanup_orphans:
            # O(1) con el índice inverso en lugar de O(E) scan.
            # Snapshot (copia del set) porque vamos a mutar self.elements.
            elem_ids = list(self._node_to_elements.get(node_id, set()))
            for eid in elem_ids:
                sub = self.remove_element(eid, cleanup_orphans=True)
                if sub["deleted"]:
                    result["elements_deleted"].append(eid)
                result["nodes_deleted"].extend(sub["nodes_deleted"])
                result["nodes_preserved"].extend(sub["nodes_preserved"])

        # Borrado explicito del nodo objetivo + refs directas. Si el
        # cascade ya lo elimino (era huerfano sin datos al quedar fuera
        # del ultimo elemento), los `if` protegen.
        if node_id in self.nodes:
            del self.nodes[node_id]
            result["nodes_deleted"].append(node_id)
        if node_id in self.nodal_loads:
            del self.nodal_loads[node_id]
        if node_id in self.boundary_conditions:
            del self.boundary_conditions[node_id]
        before_sl = len(self.surface_loads)
        self.surface_loads = [
            sl for sl in self.surface_loads
            if sl.node_start != node_id and sl.node_end != node_id
        ]
        # node_deleted refleja el resultado neto: el nodo objetivo ya no
        # esta en el modelo (lo borro el cascade o el del explicito).
        result["node_deleted"] = node_id not in self.nodes
        # Si el target estaba en nodes_preserved (cuando el cascade lo
        # preservo por datos pero el usuario igualmente lo borra),
        # quitarlo del reporte para coherencia.
        result["nodes_preserved"] = [
            n for n in result["nodes_preserved"] if n != node_id
        ]
        # Dedupe + sort para reporte ordenado y predecible.
        result["nodes_deleted"] = sorted(set(result["nodes_deleted"]))
        result["nodes_preserved"] = sorted(set(result["nodes_preserved"]))
        result["elements_deleted"] = sorted(set(result["elements_deleted"]))

        if before_sl != len(self.surface_loads) or result["node_deleted"]:
            self.is_modified = True
            self.is_solved = False
        return result

    def preview_node_cascade(self, node_id):
        """Calcula sin mutar lo que pasaria con `remove_node_with_cascade`.

        Util para mostrar un modal de confirmacion con preview del impacto
        antes de borrar. Espejado de `_preview_element_cleanup`.

        Retorna dict con:
            - "elements_to_delete": list[int]
            - "nodes_to_delete": list[int] (sin contar el objetivo)
            - "nodes_to_preserve": list[int]
        """
        if node_id not in self.nodes:
            return {"elements_to_delete": [], "nodes_to_delete": [],
                    "nodes_to_preserve": []}

        # Elementos que contienen el nodo: lookup O(1) en el indice inverso.
        elements_to_delete = list(self._node_to_elements.get(node_id, set()))
        deleted_set = set(elements_to_delete)
        # Conjunto de nodos que estarian en los elementos eliminados,
        # excluyendo el objetivo (lo reportamos aparte).
        candidate_nodes = set()
        for eid in elements_to_delete:
            for nid in self.elements[eid].node_ids:
                if nid != node_id:
                    candidate_nodes.add(nid)

        nodes_to_delete = []
        nodes_to_preserve = []
        for nid in candidate_nodes:
            if nid not in self.nodes:
                continue
            # Sigue en algun elemento NO marcado para borrar? O(1) via indice.
            still_in_element = bool(
                self._node_to_elements.get(nid, set()) - deleted_set
            )
            if still_in_element:
                continue
            has_user_data = (
                nid in self.nodal_loads
                or nid in self.boundary_conditions
                or any(sl.node_start == nid or sl.node_end == nid
                       for sl in self.surface_loads)
            )
            if has_user_data:
                nodes_to_preserve.append(nid)
            else:
                nodes_to_delete.append(nid)

        return {
            "elements_to_delete": sorted(elements_to_delete),
            "nodes_to_delete": sorted(nodes_to_delete),
            "nodes_to_preserve": sorted(nodes_to_preserve),
        }

    def is_node_referenced(self, node_id):
        """Indica si un node_id esta referenciado por cualquier dato del
        modelo (carga, BC, surface load, o elemento). Util para distinguir
        nodos verdaderamente sin uso vs nodos con datos del usuario.

        No verifica `self.nodes` -- solo dependencias externas al propio
        registro de nodos. O(1) gracias al índice inverso _node_to_elements.
        """
        if node_id in self.nodal_loads:
            return True
        if node_id in self.boundary_conditions:
            return True
        for sl in self.surface_loads:
            if sl.node_start == node_id or sl.node_end == node_id:
                return True
        # O(1): índice inverso en lugar de O(E) scan de elementos.
        return bool(self._node_to_elements.get(node_id))

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
        # Mantener índice inverso nodo→elementos.
        for nid in node_ids:
            if nid not in self._node_to_elements:
                self._node_to_elements[nid] = set()
            self._node_to_elements[nid].add(elem_id)
        self.is_modified = True
        self.is_solved = False
        return elem

    def remove_element(self, elem_id, *, cleanup_orphans=True):
        """Elimina un elemento y aplica auto-cleanup de nodos huerfanos.

        Tras borrar el elemento, computa los nodos que quedaron sin
        ninguna referencia (via `is_node_referenced`) y los elimina.
        Los nodos que tienen datos del usuario (cargas, BCs, surface
        loads) se preservan como huerfanos -- el panel de salud los
        flaggeara, pero los datos no se pierden.

        Parametros:
            elem_id: ID del elemento a eliminar.
            cleanup_orphans: si False, deshabilita el cleanup automatico
                (modo legacy). Default True.

        Retorna:
            dict con tres claves:
                - "deleted": True/False (si se borro el elemento)
                - "nodes_deleted": list[int] de IDs eliminados por cleanup
                - "nodes_preserved": list[int] de IDs que quedaron como
                  huerfanos (estaban en el elemento pero tienen otras refs)
        """
        result = {"deleted": False, "nodes_deleted": [],
                  "nodes_preserved": []}
        if elem_id not in self.elements:
            return result
        # Snapshot de los nodos que el elemento usaba (incluye Q9 mid/center)
        elem = self.elements[elem_id]
        nodes_in_elem = set(elem.node_ids)
        del self.elements[elem_id]
        result["deleted"] = True
        self.is_modified = True
        self.is_solved = False

        # Actualizar índice inverso: quitar elem_id de cada nodo que usaba.
        for nid in nodes_in_elem:
            s = self._node_to_elements.get(nid)
            if s is not None:
                s.discard(elem_id)

        if not cleanup_orphans:
            return result

        # Auto-cleanup: para cada nodo que estaba en el elemento eliminado:
        #   1) si sigue en otro elemento (índice inverso O(1)) -> no es huerfano
        #   2) si tiene cargas/BCs/surface refs -> preservar (huerfano marcado)
        #   3) sin referencias -> eliminar definitivamente
        for nid in nodes_in_elem:
            if nid not in self.nodes:
                continue
            # O(1) con el índice inverso en lugar de O(E) con any(...)
            in_another_element = bool(self._node_to_elements.get(nid))
            if in_another_element:
                continue
            has_user_data = (
                nid in self.nodal_loads
                or nid in self.boundary_conditions
                or any(sl.node_start == nid or sl.node_end == nid
                       for sl in self.surface_loads)
            )
            if has_user_data:
                result["nodes_preserved"].append(nid)
                continue
            del self.nodes[nid]
            self._node_to_elements.pop(nid, None)
            result["nodes_deleted"].append(nid)

        result["nodes_deleted"].sort()
        result["nodes_preserved"].sort()
        return result

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

    def add_surface_load(self, node_start, node_end,
                         q_start=0.0, q_end=0.0, angle=0.0, element_id=None):
        """Agrega una carga superficial. element_id es opcional."""
        load = SurfaceLoad(node_start, node_end,
                           q_start, q_end, angle, element_id)
        self.surface_loads.append(load)
        self.is_modified = True
        self.is_solved = False
        return load

    # ─── Renombrado / cambio de ID con cascada ──────────────────────────

    def change_node_id(self, old_id, new_id):
        """Renumera un nodo y actualiza TODAS las referencias.

        Mueve el nodo de `nodes[old_id]` a `nodes[new_id]` y actualiza:
        - Su propio atributo `.id`.
        - `nodal_loads[old_id]` -> `nodal_loads[new_id]` (mantiene la carga).
        - `boundary_conditions[old_id]` -> idem.
        - Todos los `element.node_ids` que contengan `old_id`.
        - `surface_loads.node_start` / `node_end` que apunten a `old_id`.

        Lanza ValueError si `old_id` no existe o `new_id` ya esta en uso.
        """
        if old_id == new_id:
            return
        if old_id not in self.nodes:
            raise ValueError(f"Nodo {old_id} no existe")
        if new_id in self.nodes:
            raise ValueError(f"Nodo {new_id} ya existe")
        node = self.nodes.pop(old_id)
        node.id = new_id
        self.nodes[new_id] = node
        self._node_index_map_cache = None
        if old_id in self.nodal_loads:
            load = self.nodal_loads.pop(old_id)
            load.node_id = new_id
            self.nodal_loads[new_id] = load
        if old_id in self.boundary_conditions:
            bc = self.boundary_conditions.pop(old_id)
            bc.node_id = new_id
            self.boundary_conditions[new_id] = bc
        for elem in self.elements.values():
            elem.node_ids = [new_id if n == old_id else n
                             for n in elem.node_ids]
        # Actualizar índice inverso: mover old_id → new_id en el mapa.
        s = self._node_to_elements.pop(old_id, None)
        if s is not None:
            self._node_to_elements[new_id] = s
        for sl in self.surface_loads:
            if sl.node_start == old_id:
                sl.node_start = new_id
            if sl.node_end == old_id:
                sl.node_end = new_id
        self.is_modified = True
        self.is_solved = False

    def change_element_id(self, old_id, new_id):
        """Renumera un elemento y actualiza referencias en surface_loads."""
        if old_id == new_id:
            return
        if old_id not in self.elements:
            raise ValueError(f"Elemento {old_id} no existe")
        if new_id in self.elements:
            raise ValueError(f"Elemento {new_id} ya existe")
        elem = self.elements.pop(old_id)
        elem.id = new_id
        self.elements[new_id] = elem
        for sl in self.surface_loads:
            if sl.element_id == old_id:
                sl.element_id = new_id
        self.is_modified = True
        self.is_solved = False

    def rename_material(self, old_name, new_name):
        """Renombra un material y actualiza element.material_name en cascada."""
        if old_name == new_name:
            return
        if old_name not in self.materials:
            raise ValueError(f"Material '{old_name}' no existe")
        new_name = (new_name or "").strip()
        if not new_name:
            raise ValueError("El nombre del material no puede estar vacío")
        if new_name in self.materials:
            raise ValueError(f"Material '{new_name}' ya existe")
        mat = self.materials.pop(old_name)
        mat.name = new_name
        self.materials[new_name] = mat
        for elem in self.elements.values():
            if elem.material_name == old_name:
                elem.material_name = new_name
        self.is_modified = True
        self.is_solved = False

    # ─── Gestión de restricciones ───────────────────────────────────────

    def set_boundary_condition(self, node_id, restrain_x, restrain_y,
                               ux_value=0.0, uy_value=0.0):
        """Agrega o actualiza una restricción de desplazamiento.

        Los parametros opcionales `ux_value` / `uy_value` permiten imponer
        desplazamientos prescritos no-cero (necesario para MMS y similares).
        Si quedan en 0.0 (default), el comportamiento es el clasico:
        restraint == desplazamiento nulo.
        """
        self.boundary_conditions[node_id] = BoundaryCondition(
            node_id, restrain_x, restrain_y, ux_value, uy_value
        )
        self.is_modified = True
        self.is_solved = False

    def get_prescribed_displacement_vector(self):
        """Vector u_pre de tamano total_dof con valores prescritos en los
        DOFs restringidos y 0 en el resto. Si ninguna BC tiene valor no
        nulo, retorna None (signal de que la rama clasica del solver alcanza).
        """
        import numpy as np
        any_nonzero = any(bc.has_prescribed_displacement
                          for bc in self.boundary_conditions.values())
        if not any_nonzero:
            return None
        idx_map = self.node_index_map
        u_pre = np.zeros(self.total_dof)
        for bc in self.boundary_conditions.values():
            base = 2 * idx_map[bc.node_id]
            if bc.restrain_x:
                u_pre[base] = bc.ux_value
            if bc.restrain_y:
                u_pre[base + 1] = bc.uy_value
        return u_pre

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

    @property
    def node_index_map(self):
        """Mapping node_id -> indice ordinal (0-indexed) en el sistema lineal.

        Orden estable: sorted(self.nodes.keys()). Cacheado: O(N log N) solo al
        invalidar (add_node / remove_node / change_node_id / restore_from_dict);
        O(1) en accesos repetidos dentro de la misma operacion. Soporta IDs
        no contiguos (e.g. {1, 5, 50}) tras borrados.
        """
        if self._node_index_map_cache is None:
            self._node_index_map_cache = {
                nid: idx for idx, nid in enumerate(sorted(self.nodes.keys()))
            }
        return self._node_index_map_cache

    def rebuild_node_to_elements(self):
        """Reconstruye el índice inverso nodo→elementos desde cero.

        Llamar después de mutaciones masivas de `elem.node_ids` que no pasan
        por `add_element` / `remove_element` (e.g. expand_q4_to_q9,
        shrink_q9_to_q4, recompute_q9_midnodes en mesh_utils).
        """
        idx: dict = {}
        for eid, elem in self.elements.items():
            for nid in elem.node_ids:
                if nid not in idx:
                    idx[nid] = set()
                idx[nid].add(eid)
        self._node_to_elements = idx

    def dof_x(self, node_id):
        """Indice DOF global de Ux para node_id (0-indexed)."""
        return 2 * self.node_index_map[node_id]

    def dof_y(self, node_id):
        """Indice DOF global de Uy para node_id (0-indexed)."""
        return 2 * self.node_index_map[node_id] + 1

    def get_restrained_dofs(self):
        """Retorna la lista de todos los GDL restringidos (0-indexed)."""
        idx_map = self.node_index_map
        dofs = []
        for bc in self.boundary_conditions.values():
            base = 2 * idx_map[bc.node_id]
            if bc.restrain_x:
                dofs.append(base)
            if bc.restrain_y:
                dofs.append(base + 1)
        return sorted(dofs)

    def get_free_dofs(self):
        """Retorna la lista de GDL libres."""
        restrained = set(self.get_restrained_dofs())
        return [i for i in range(self.total_dof) if i not in restrained]

    # ─── Conversion de unidades ─────────────────────────────────────────

    def convert_units(self, factors):
        """Multiplica TODAS las cantidades dimensionales del proyecto por
        los factores dados — preservando el modelo fisico cuando el sistema
        de unidades cambia. NO cambia `unit_system` (eso es responsabilidad
        del caller, que tipicamente acaba de cambiarlo y llama aqui).

        `factors` es el dict devuelto por `config.units.get_conversion_factors`:
            length             — coords, espesor
            force              — fuerzas puntuales Fx, Fy
            stress             — Modulo de Young E
            force_per_length   — cargas distribuidas q
            acceleration       — gravedad (gx, gy)

        DENSIDAD (kg/m³ o equivalente) NO se convierte aqui — la unidad de
        masa no esta en nuestro sistema de 3-tupla (L, F, sigma). El usuario
        debe reingresar densidad manualmente si su nuevo sistema usa otra
        unidad de masa. La solucion existente (is_solved) se invalida porque
        la matriz K depende de E y la malla en unidades nuevas.
        """
        fl = factors["length"]
        ff = factors["force"]
        fs = factors["stress"]
        fql = factors["force_per_length"]
        fa = factors["acceleration"]

        # Coords nodales
        for node in self.nodes.values():
            node.x *= fl
            node.y *= fl
        # Espesor por defecto y override por elemento
        self.default_thickness *= fl
        for elem in self.elements.values():
            if getattr(elem, "thickness", None) is not None:
                elem.thickness *= fl
        # Material: solo E. Densidad y nu sin conversion.
        for mat in self.materials.values():
            mat.E *= fs
        # Cargas
        for load in self.nodal_loads.values():
            load.fx *= ff
            load.fy *= ff
        for sl in self.surface_loads:
            sl.q_start *= fql
            sl.q_end *= fql
        # Gravedad (aceleracion)
        self.gravity_x *= fa
        self.gravity_y *= fa
        # Invalidar solucion: K depende de E, F de cargas, todo cambio.
        self.is_solved = False
        self.displacements = None
        self.global_K = None
        self.global_F = None
        self.stresses = {}
        self.is_modified = True

    # ─── Serialización ──────────────────────────────────────────────────

    def to_dict(self):
        """Serializa todo el proyecto a un diccionario."""
        return {
            "project_name": self.project_name,
            "analysis_type": self.analysis_type,
            "element_type": self.element_type,
            "unit_system": self.unit_system,
            "default_thickness": self.default_thickness,
            "gravity_x": self.gravity_x,
            "gravity_y": self.gravity_y,
            "include_gravity": self.include_gravity,
            "nodes": {str(k): v.to_dict() for k, v in self.nodes.items()},
            "elements": {str(k): v.to_dict() for k, v in self.elements.items()},
            "materials": {k: v.to_dict() for k, v in self.materials.items()},
            "nodal_loads": {str(k): v.to_dict()
                           for k, v in self.nodal_loads.items()},
            "surface_loads": [sl.to_dict() for sl in self.surface_loads],
            "boundary_conditions": {str(k): v.to_dict()
                                    for k, v in self.boundary_conditions.items()},
        }

    def restore_from_dict(self, data):
        """Restaura el estado del proyecto IN-PLACE desde un diccionario.

        A diferencia de `from_dict` (que es classmethod y crea una nueva
        instancia), esta variante muta `self` reescribiendo todas las
        colecciones internas. Es la entrada que usa `UndoStack` para que
        las referencias `main_window.project`, `pre_tab.project`, etc.
        sigan apuntando al mismo objeto tras un undo/redo.

        Esquema de datos identico al de `from_dict` (ambos consumen el
        mismo `to_dict`).
        """
        # Reusar from_dict para parseo y luego copiar atributos: evita
        # duplicar la logica de deserializacion y mantiene un unico SoT.
        rebuilt = ProjectModel.from_dict(data)
        # Copiar TODOS los atributos serializables al self existente
        self.project_name = rebuilt.project_name
        self.analysis_type = rebuilt.analysis_type
        self.element_type = rebuilt.element_type
        self.unit_system = rebuilt.unit_system
        self.default_thickness = rebuilt.default_thickness
        self.gravity_x = rebuilt.gravity_x
        self.gravity_y = rebuilt.gravity_y
        self.include_gravity = rebuilt.include_gravity
        self.nodes = rebuilt.nodes
        self.elements = rebuilt.elements
        self.materials = rebuilt.materials
        self.nodal_loads = rebuilt.nodal_loads
        self.surface_loads = rebuilt.surface_loads
        self.boundary_conditions = rebuilt.boundary_conditions
        # Estado de solucion: invalidar (el snapshot no la incluye, asi
        # que tras restore quedaria inconsistente).
        self.is_solved = False
        self.displacements = None
        self.global_K = None
        self.global_F = None
        self.stresses = {}
        # Cache del node_index_map: invalidar ya que los nodes cambiaron.
        self._node_index_map_cache = None
        # Índice inverso: copiar del proyecto reconstruido.
        self._node_to_elements = rebuilt._node_to_elements
        # is_modified queda en True: el restore ES una modificacion logica
        # del estado actual (antes y despues son distintos).
        self.is_modified = True

    @classmethod
    def from_dict(cls, data):
        """Reconstruye el proyecto desde un diccionario."""
        project = cls()
        project.project_name = data.get("project_name", "Proyecto")
        project.analysis_type = data.get("analysis_type", DEFAULT_ANALYSIS_TYPE)
        project.element_type = data.get("element_type", DEFAULT_ELEMENT_TYPE)
        # Backward-compat: el modo "Personalizado" se eliminó en 2026-05.
        # Los .edufem legacy con ese sistema se migran al default y se
        # descarta `custom_units` (los strings personalizados eran solo
        # rotulos sin factores reales — no se pierde informacion fisica).
        loaded_us = data.get("unit_system", DEFAULT_UNIT_SYSTEM)
        if loaded_us == "Personalizado":
            loaded_us = DEFAULT_UNIT_SYSTEM
        project.unit_system = loaded_us
        project.default_thickness = data.get("default_thickness", DEFAULT_THICKNESS)
        # Gravedad como vector (gx, gy). Backward-compat: si el .edufem
        # legacy tiene `gravity` (escalar), migrarlo a (0, -gravity).
        if "gravity_x" in data or "gravity_y" in data:
            project.gravity_x = float(data.get("gravity_x", 0.0))
            project.gravity_y = float(data.get("gravity_y", -DEFAULT_GRAVITY))
        else:
            legacy = float(data.get("gravity", DEFAULT_GRAVITY))
            project.gravity_x = 0.0
            project.gravity_y = -legacy
        project.include_gravity = data.get("include_gravity", False)

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
        # Reconstruir índice inverso nodo→elementos (no se serializa).
        project._node_to_elements = {}
        for eid, elem in project.elements.items():
            for nid in elem.node_ids:
                if nid not in project._node_to_elements:
                    project._node_to_elements[nid] = set()
                project._node_to_elements[nid].add(eid)
        return project

    def __repr__(self):
        return (f"ProjectModel('{self.project_name}', "
                f"{self.num_nodes} nodos, {self.num_elements} elems)")
