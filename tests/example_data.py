"""
Ejemplo de prueba para el motor FEM.
Datos del caso de validacion:
  - Tension plana, Q4, 4 elementos, 9 nodos.
  - E = 225000, nu = 0.2, t = 0.8, rho = 0.2447, g = 9.8079
"""

from models.project import ProjectModel
from models.material import Material
from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q4


def load_example_project(P=1000.0):
    """
    Carga el problema de ejemplo en un ProjectModel.

    Problema:
      - Tension plana
      - E = 225000, nu = 0.2, t = 0.8, rho = 0.2447
      - g = 9.8079 (almacenado como propiedad)
      - 9 nodos, 4 elementos Q4
      - Fuerza: Fy = -P en nodo 7
      - Restricciones: nodos 1, 3, 6 empotrados (Dx=1, Dy=1)

    Esquema de la malla:
      7(5,8) --- 8(7,8) --- 9(9,8)
      |   E3   |   E4   |
      4(2,3) --- 5(7,4) --- 6(11,4)
      |   E1   |   E2   |
      1(0,0) --- 2(5,0) --- 3(8,0)

    Parametros:
        P: Magnitud de la fuerza (default 1000.0).

    Retorna:
        ProjectModel configurado con datos eficientes (float64).
    """
    project = ProjectModel()
    project.project_name = "Ejemplo Validacion Q4"
    project.analysis_type = ANALYSIS_PLANE_STRESS
    project.element_type = ELEMENT_Q4
    project.default_thickness = 0.8
    project.gravity = 9.8079  # Aceleracion de la gravedad

    # ─── Material ────────────────────────────────────────────────────────
    project.materials = {}
    mat = Material(
        name="Material Ejemplo",
        E=225000.0,       # Modulo de elasticidad
        nu=0.2,           # Coeficiente de Poisson
        density=0.2447,   # Densidad del material
    )
    project.materials[mat.name] = mat

    # ─── Nodos (coordenadas float64) ─────────────────────────────────────
    #     ID: (x, y)
    node_data = [
        (1,  0.0,  0.0),
        (2,  5.0,  0.0),
        (3,  8.0,  0.0),
        (4,  2.0,  3.0),
        (5,  7.0,  4.0),
        (6, 11.0,  4.0),
        (7,  5.0,  8.0),
        (8,  7.0,  8.0),
        (9,  9.0,  8.0),
    ]
    for nid, x, y in node_data:
        project.add_node(float(x), float(y), node_id=int(nid))

    # ─── Elementos Q4 (conectividad int) ─────────────────────────────────
    #     ID: [N1, N2, N3, N4]
    elem_data = [
        (1, [1, 2, 5, 4]),
        (2, [2, 3, 6, 5]),
        (3, [4, 5, 8, 7]),
        (4, [5, 6, 9, 8]),
    ]
    for eid, nids in elem_data:
        project.add_element(
            node_ids=[int(n) for n in nids],
            thickness=0.8,
            material_name="Material Ejemplo",
            elem_id=int(eid)
        )

    # ─── Fuerzas nodales ─────────────────────────────────────────────────
    #     [Nudo, Fx, Fy]
    project.set_nodal_load(7, 0.0, float(-P))

    # ─── Condiciones de contorno (1=restringido) ─────────────────────────
    #     [Nudo, Dx, Dy]
    project.set_boundary_condition(1, True, True)   # Empotrado
    project.set_boundary_condition(3, True, True)   # Empotrado
    project.set_boundary_condition(6, True, True)   # Empotrado

    project.is_modified = False
    return project
