"""
Ejemplos de prueba para el motor FEM.

Tres familias:
  1. `load_example_project` / `load_example_project_q9`
        - Caso canonico de validacion: Q4/Q9, 4 elementos, 9 nodos.
        - Datos: E=225000, nu=0.2, t=0.8, rho=0.2447, g=9.8079.
  2. `load_example_timoshenko` (Q4/Q9)
        - Viga simplemente apoyada Timoshenko-Goodier en unidades tecnicas.
        - Documentada en docs/Timoshenko,sap2000.pdf y validada en
          docs/vyv/capitulo_vyv.tex con error < 0.05% vs analitico.
  3. `load_example_cook` (Q4/Q9)
        - Membrana trapezoidal de Cook (1974), benchmark adimensional clasico
          para evaluar shear-locking en dominios distorsionados.
"""

from models.project import ProjectModel
from models.material import Material
from models.mesh_utils import (
    boundary_node_ids, expand_q4_to_q9, generate_structured_quad_mesh,
)
from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q4, ELEMENT_Q9


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
    project.gravity_x = 0.0
    project.gravity_y = -9.8079  # Gravedad terrestre apuntando hacia -Y

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


def load_example_project_q9(P=1000.0):
    """Variante Q9 del ejemplo canónico.

    Construye la misma geometría/E/ν/t/cargas/BCs que `load_example_project`
    y ejecuta `expand_q4_to_q9` para generar los nodos medios y centroides,
    dejando el proyecto listo para validar el pipeline Q9 end-to-end.
    """
    project = load_example_project(P=P)
    project.project_name = "Ejemplo Validacion Q9"
    expand_q4_to_q9(project)
    project.element_type = ELEMENT_Q9
    project.is_modified = False
    project.is_solved = False
    return project


# ─── Viga Timoshenko (Timoshenko & Goodier, simple apoyada) ────────────────

def load_example_timoshenko(element_type=ELEMENT_Q9, nx=14, ny=4):
    """Viga rectangular simplemente apoyada en unidades técnicas (kgf, cm).

    Geometría (idéntica al caso documentado en docs/Timoshenko,sap2000.pdf):
        L = 1400 cm, H = 120 cm, b (espesor) = 40 cm
        E = 217370 kgf/cm², nu = 0.2
        q = 50 kgf/cm (= 5000 kgf/m) hacia -y sobre el borde superior
        Apoyos: pin en (-700, 0), rodillo en (+700, 0)

    Convencion: eje Y hacia arriba (estandar matematico). La fibra superior
    de la viga esta en y = +H/2; las tensiones de flexion en esa fibra son
    de compresion (sigma_x < 0). En el PDF de referencia, que usa la
    convencion clasica de Timoshenko (eje Y hacia abajo), los signos son
    opuestos -- vease docs/vyv/capitulo_vyv.tex (Seccion 4) para la
    discusion completa y la comparacion con SAP2000.

    Tras el solve se esperan, en la fibra inferior central (0, -60 cm):
        sigma_x ~ +127.85 kgf/cm^2  (traccion)
        delta_max(y=0, x=0) ~ -2.03 cm (deflexion hacia abajo)

    Parametros:
        element_type: ELEMENT_Q4 o ELEMENT_Q9 (default Q9).
        nx, ny: resolucion de malla. Default 14x4 -> 56 elementos macro
            (1 elem cada 100 cm horizontales, 1 cada 30 cm verticales).
            Mas refinada que un esquema didactico, pero todavia rapida en
            la GUI: ~261 nodos Q9 / ~75 nodos Q4.

    Retorna:
        ProjectModel listo para resolver.
    """
    L = 1400.0
    H = 120.0
    b_thickness = 40.0
    E = 217370.0
    nu = 0.2
    q_per_cm = 50.0           # kgf/cm sobre el borde superior

    project = generate_structured_quad_mesh(
        corners=[(-L / 2, -H / 2), (L / 2, -H / 2),
                 (L / 2,  H / 2), (-L / 2,  H / 2)],
        nx=nx, ny=ny, element_type=element_type,
        material_name="Hormigon (f'c=210 kgf/cm²)",
        thickness=b_thickness,
        analysis_type=ANALYSIS_PLANE_STRESS,
    )
    project.project_name = (
        f"Viga Timoshenko - apoyo simple ({element_type.split(' ')[0]})"
    )
    project.unit_system = "Técnico (kgf, cm, kgf/cm²)"
    project.materials["Hormigon (f'c=210 kgf/cm²)"] = Material(
        name="Hormigon (f'c=210 kgf/cm²)",
        E=E, nu=nu, density=2.4e-3,        # kgf/cm³ ~ 2400 kg/m³
    )

    # BCs: apoyos en (-L/2, 0) y (+L/2, 0). Como ny debe ser par para que
    # haya una fila de nodos en y=0, el bucle busca esos nodos por coords.
    tol = 1e-6 * L
    left_pin = right_roller = None
    for nid, node in project.nodes.items():
        if abs(node.y) < tol:
            if abs(node.x - (-L / 2)) < tol:
                left_pin = nid
            elif abs(node.x - L / 2) < tol:
                right_roller = nid
    if left_pin is None or right_roller is None:
        raise RuntimeError(
            "Viga Timoshenko: no se encontraron los nodos de apoyo. "
            "ny debe ser par para que haya una fila de nodos en y=0."
        )
    project.set_boundary_condition(left_pin, True, True)
    project.set_boundary_condition(right_roller, False, True)

    # Surface loads sobre el borde superior (y = +H/2), iterando elementos
    # cuya arista (N4=NW -> N3=NE) este en y_top. Con (node_start=N4,
    # node_end=N3) y q>0, la carga apunta hacia -y (la "normal exterior"
    # calculada con tangente +x es (0,-1)).
    y_top = +H / 2
    for elem in project.elements.values():
        n3 = project.nodes[elem.node_ids[2]]
        n4 = project.nodes[elem.node_ids[3]]
        if abs(n3.y - y_top) > tol or abs(n4.y - y_top) > tol:
            continue
        project.add_surface_load(
            node_start=elem.node_ids[3],   # NW
            node_end=elem.node_ids[2],     # NE
            q_start=q_per_cm, q_end=q_per_cm,
            angle=0.0,
            element_id=elem.id,
        )

    project.is_modified = False
    project.is_solved = False
    return project


def load_example_timoshenko_q9(nx=14, ny=4):
    """Variante Q9 explícita (la default ya es Q9, pero queda como alias
    simétrico de `load_example_project_q9` para el menú Ayuda)."""
    return load_example_timoshenko(element_type=ELEMENT_Q9, nx=nx, ny=ny)


def load_example_timoshenko_q4(nx=14, ny=4):
    """Variante Q4 de la viga Timoshenko. Esperado: mayor error de flexion
    que la Q9 con la misma resolucion (shear-locking)."""
    return load_example_timoshenko(element_type=ELEMENT_Q4, nx=nx, ny=ny)


# ─── Membrana de Cook (1974) ───────────────────────────────────────────────

def load_example_cook(element_type=ELEMENT_Q9, N=8):
    """Membrana trapezoidal de Cook -- benchmark adimensional clasico.

    Geometria (Cook 1974):
        Cuadrilatero CCW: (0,0), (48, 44), (48, 60), (0, 44)
        Borde izquierdo (x=0) empotrado.
        Traccion tangencial uniforme en el borde derecho, F_total = 1
        repartido sobre L_right = 16 (q = 1/16, direccion +y).
        Material adimensional: E = 1, nu = 1/3, t = 1, tension plana.

    Cantidad de interes: u_y en (48, 52) -- punto medio del lado libre.
    Valores de referencia (literatura): u_y ~ 23.95 (Q4 refinado),
                                         u_y ~ 23.96 (cuadraticos).

    Tras el solve, en el punto (48, 52):
        Q4 N=8  : u_y ~ 22.08 (error ~ -7.8%)
        Q9 N=8  : u_y ~ 23.93 (error ~ -0.1%)
    -- ilustracion empirica del shear-locking parcial de Q4 en dominios
    distorsionados.

    Parametros:
        element_type: ELEMENT_Q4 o ELEMENT_Q9 (default Q9).
        N: resolucion NxN (default 8 -> 64 elementos macro).

    Retorna:
        ProjectModel listo para resolver.
    """
    project = generate_structured_quad_mesh(
        corners=[(0.0, 0.0), (48.0, 44.0), (48.0, 60.0), (0.0, 44.0)],
        nx=N, ny=N, element_type=element_type,
        material_name="Cook (adimensional)",
        thickness=1.0,
        analysis_type=ANALYSIS_PLANE_STRESS,
    )
    project.project_name = (
        f"Membrana de Cook ({element_type.split(' ')[0]}, N={N})"
    )
    project.materials["Cook (adimensional)"] = Material(
        name="Cook (adimensional)", E=1.0, nu=1.0 / 3.0, density=0.0,
    )

    # BC: empotrado en x=0
    for nid in boundary_node_ids(project, "left"):
        project.set_boundary_condition(nid, True, True)

    # Carga tangencial uniforme +y sobre el lado derecho.
    # Lado derecho CCW del elemento: N2(SE) -> N3(NE), tangente = (0,+1),
    # normal "exterior" calculada = (+1, 0). angle=+90 rota la normal a
    # (0, +1) -- direccion tangencial +y. q = 1/16 da F_total = 1.
    L_right = 16.0
    q_per_len = 1.0 / L_right
    tol = 1e-6 * 48.0
    for elem in project.elements.values():
        n2 = project.nodes[elem.node_ids[1]]
        n3 = project.nodes[elem.node_ids[2]]
        if abs(n2.x - 48.0) > tol or abs(n3.x - 48.0) > tol:
            continue
        project.add_surface_load(
            node_start=elem.node_ids[1],   # SE
            node_end=elem.node_ids[2],     # NE
            q_start=q_per_len, q_end=q_per_len,
            angle=90.0,
            element_id=elem.id,
        )

    project.is_modified = False
    project.is_solved = False
    return project


def load_example_cook_q9(N=8):
    """Alias Q9 (default) para el menú Ayuda."""
    return load_example_cook(element_type=ELEMENT_Q9, N=N)


def load_example_cook_q4(N=8):
    """Variante Q4 de Cook. Mostrara convergencia lenta vs Q9."""
    return load_example_cook(element_type=ELEMENT_Q4, N=N)
