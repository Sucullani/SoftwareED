"""
test_fem.py - Script de validacion del motor FEM con datos de ejemplo.
Ejecutar: python -m tests.test_fem
"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.example_data import load_example_project
from fem.solver import solve_system
from fem.stress import compute_all_stresses
from fem.mesh_quality import evaluate_mesh_quality


def main():
    print("=" * 60)
    print("  TEST: Motor FEM con ejemplo de validacion")
    print("=" * 60)

    # Cargar proyecto de ejemplo
    project = load_example_project(P=1000.0)
    print(f"\nProyecto: {project.project_name}")
    print(f"Tipo: {project.analysis_type}")
    print(f"Nodos: {project.num_nodes}")
    print(f"Elementos: {project.num_elements}")
    print(f"GDL totales: {project.total_dof}")
    print(f"GDL restringidos: {project.get_restrained_dofs()}")
    print(f"GDL libres:       {project.get_free_dofs()}")

    # Resolver
    print("\n--- Resolviendo sistema K*u = F ---")
    solution = solve_system(project)

    u = solution["u"]
    print(f"\nVector de desplazamientos u ({len(u)} GDL):")
    for i in range(0, len(u), 2):
        node_id = i // 2 + 1
        print(f"  Nodo {node_id}: Ux = {u[i]:12.6e},  Uy = {u[i+1]:12.6e}")

    # Reacciones
    R = solution["reactions"]
    restrained = solution["restrained_dofs"]
    print(f"\nReacciones en GDL restringidos:")
    for dof in restrained:
        node_id = dof // 2 + 1
        comp = "Rx" if dof % 2 == 0 else "Ry"
        print(f"  Nodo {node_id} ({comp}): R = {R[dof]:12.4f}")

    # Esfuerzos
    print("\n--- Esfuerzos nodales promedio ---")
    elem_stresses, nodal_stresses = compute_all_stresses(project, solution)
    for nid in sorted(nodal_stresses.keys()):
        s = nodal_stresses[nid]
        print(f"  Nodo {nid}: sx={s['sigma_x']:10.4f}  sy={s['sigma_y']:10.4f}"
              f"  txy={s['tau_xy']:10.4f}  VM={s['von_mises']:10.4f}")

    # Calidad de malla
    print("\n--- Calidad de la malla ---")
    quality = evaluate_mesh_quality(project)
    for eid, q in sorted(quality.items()):
        print(f"  Elem {eid}: Jacobiano={q['jacobian_ratio']:.4f}  "
              f"Angulos=[{q['min_angle']:.1f}, {q['max_angle']:.1f}]  "
              f"Robinson={q['robinson']:.2f}  {q['status']}")

    print("\nTest completado exitosamente.")


if __name__ == "__main__":
    main()
