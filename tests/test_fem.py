"""
test_fem.py - Script de validacion del motor FEM con datos de ejemplo.
Ejecutar: python -m tests.test_fem
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.example_data import load_example_project, load_example_project_q9
from fem.solver import solve_system
from fem.stress import compute_all_stresses
from fem.mesh_quality import evaluate_mesh_quality
from fem.assembly import assemble_global_system
from models.project import ProjectModel
from models.material import Material
from models.mesh_utils import expand_q4_to_q9
from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q4


def _run_case(project, header):
    print("=" * 60)
    print(f"  {header}")
    print("=" * 60)

    print(f"\nProyecto: {project.project_name}")
    print(f"Tipo analisis: {project.analysis_type}")
    print(f"Tipo elemento: {project.element_type}")
    print(f"Nodos: {project.num_nodes}")
    print(f"Elementos: {project.num_elements}")
    print(f"GDL totales: {project.total_dof}")
    print(f"GDL restringidos: {project.get_restrained_dofs()}")
    print(f"GDL libres:       {project.get_free_dofs()}")

    print("\n--- Resolviendo sistema K*u = F ---")
    solution = solve_system(project)

    u = solution["u"]
    print(f"\nVector de desplazamientos u ({len(u)} GDL):")
    for i in range(0, len(u), 2):
        node_id = i // 2 + 1
        print(f"  Nodo {node_id}: Ux = {u[i]:12.6e},  Uy = {u[i+1]:12.6e}")

    R = solution["reactions"]
    restrained = solution["restrained_dofs"]
    print(f"\nReacciones en GDL restringidos:")
    for dof in restrained:
        node_id = dof // 2 + 1
        comp = "Rx" if dof % 2 == 0 else "Ry"
        print(f"  Nodo {node_id} ({comp}): R = {R[dof]:12.4f}")

    print("\n--- Esfuerzos nodales promedio ---")
    _, nodal_stresses = compute_all_stresses(project, solution)
    for nid in sorted(nodal_stresses.keys()):
        s = nodal_stresses[nid]
        print(f"  Nodo {nid}: sx={s['sigma_x']:10.4f}  sy={s['sigma_y']:10.4f}"
              f"  txy={s['tau_xy']:10.4f}  VM={s['von_mises']:10.4f}")

    print("\n--- Calidad de la malla ---")
    quality = evaluate_mesh_quality(project)
    for eid, q in sorted(quality.items()):
        print(f"  Elem {eid}: Jacobiano={q['jacobian_ratio']:.4f}  "
              f"Angulos=[{q['min_angle']:.1f}, {q['max_angle']:.1f}]  "
              f"Robinson={q['robinson']:.2f}  {q['status']}")


def _build_surface_load_case(q=100.0):
    """Cuadrado unitario 1 elemento Q4 con carga superficial en arista 2->3.

    Nodos CCW:
        4(0,1) --- 3(1,1)
        |           |
        1(0,0) --- 2(1,0)

    BCs: nodos 1 y 4 empotrados (arista izquierda).
    SurfaceLoad q constante en arista 2->3 (lado derecho) con angle=0 ⇒
    normal exterior (+x). Fuerza total esperada: (Fx, Fy) = (q·L, 0) = (q, 0).
    """
    p = ProjectModel()
    p.project_name = "Carga superficial Q4 (cuadrado unitario)"
    p.analysis_type = ANALYSIS_PLANE_STRESS
    p.element_type = ELEMENT_Q4
    p.default_thickness = 1.0
    p.materials = {"Mat1": Material("Mat1", E=1.0e6, nu=0.3, density=0.0)}
    p.add_node(0.0, 0.0, node_id=1)
    p.add_node(1.0, 0.0, node_id=2)
    p.add_node(1.0, 1.0, node_id=3)
    p.add_node(0.0, 1.0, node_id=4)
    p.add_element(node_ids=[1, 2, 3, 4], thickness=1.0,
                  material_name="Mat1", elem_id=1)
    p.set_boundary_condition(1, True, True)
    p.set_boundary_condition(4, True, True)
    p.add_surface_load(node_start=2, node_end=3,
                       q_start=q, q_end=q, angle=0.0, element_id=1)
    p.is_modified = False
    return p


def _run_surface_load_case(tag, project, q, L=1.0):
    print("=" * 60)
    print(f"  {tag}")
    print("=" * 60)
    K, F, _ = assemble_global_system(project)
    Fx = float(np.sum(F[0::2]))
    Fy = float(np.sum(F[1::2]))
    print(f"Suma total de F aplicado: (Fx, Fy) = ({Fx:+.4f}, {Fy:+.4f})")
    print(f"Esperado (q*L, 0):        (Fx, Fy) = ({q*L:+.4f}, {0.0:+.4f})")
    ok = abs(Fx - q * L) < 1e-6 and abs(Fy) < 1e-6
    print(f"Match: {'OK' if ok else 'FAIL'}")

    sol = solve_system(project)
    u = sol["u"]
    # En un cuadrado con lado izq empotrado + carga en +x distribuida en lado
    # derecho, los nodos 2 y 3 se desplazan en +x simetricamente (Uy opuesto).
    u2x, u2y = u[2], u[3]
    u3x, u3y = u[4], u[5]
    sym_x = abs(u2x - u3x) < 1e-9
    sym_y = abs(u2y + u3y) < 1e-9
    pos_x = u2x > 0 and u3x > 0
    print(f"Ux nodo 2 = {u2x:+.4e}  Ux nodo 3 = {u3x:+.4e}  "
          f"(simetrico: {sym_x}, ambos +x: {pos_x})")
    print(f"Uy nodo 2 = {u2y:+.4e}  Uy nodo 3 = {u3y:+.4e}  "
          f"(antisimetrico: {sym_y})")


def main():
    _run_case(load_example_project(P=1000.0),
              "TEST Q4: motor FEM con ejemplo de validacion")
    print()
    _run_case(load_example_project_q9(P=1000.0),
              "TEST Q9: motor FEM con ejemplo expandido")
    print()
    _run_surface_load_case(
        "TEST carga superficial Q4 (hardcoded, cuadrado unitario)",
        _build_surface_load_case(q=100.0), q=100.0)
    print()
    p_q9 = _build_surface_load_case(q=100.0)
    expand_q4_to_q9(p_q9)
    _run_surface_load_case(
        "TEST carga superficial Q9 (cuadrado unitario expandido)",
        p_q9, q=100.0)
    print("\nTest completado exitosamente.")


if __name__ == "__main__":
    main()
