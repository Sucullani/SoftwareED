"""
test_q9_q4_cycle.py - valida el ciclo Q4 -> Q9 -> Q4 sin romper el modelo.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.mesh_utils import expand_q4_to_q9, shrink_q9_to_q4
from tests.example_data import load_example_project
from fem.solver import solve_system
from config.settings import ELEMENT_Q4, ELEMENT_Q9


def _summary(tag, project):
    print(f"[{tag}] tipo={project.element_type}  "
          f"nodos={project.num_nodes}  elems={project.num_elements}  "
          f"num_nodes_por_elem=" +
          ",".join(str(e.num_nodes) for e in project.elements.values()))


def main():
    p = load_example_project(P=1000.0)
    _summary("INICIAL Q4", p)
    u_q4_a = solve_system(p)["u"]

    expand_q4_to_q9(p)
    _summary("EXPANDIDO Q9", p)
    u_q9 = solve_system(p)["u"]

    m, n = shrink_q9_to_q4(p)
    _summary(f"REDUCIDO Q4 (truncados={m}, eliminados={n})", p)
    assert p.element_type == ELEMENT_Q4
    assert p.num_elements == 4
    for e in p.elements.values():
        assert e.num_nodes == 4, f"elem {e.id} todavia tiene {e.num_nodes} nodos"
    u_q4_b = solve_system(p)["u"]

    assert p.num_nodes == 9, f"quedaron {p.num_nodes} nodos, deberian 9"

    if len(u_q4_a) == len(u_q4_b):
        import numpy as np
        diff = float(np.max(np.abs(u_q4_a - u_q4_b)))
        print(f"\nMax |u_q4_inicial - u_q4_reducido| = {diff:.3e}")
        if diff < 1e-9:
            print("OK - Q4 -> Q9 -> Q4 regresa al estado numerico original.")
        else:
            print("FAIL - el ciclo altera los desplazamientos.")
    else:
        print(f"FAIL - tamanos distintos: {len(u_q4_a)} vs {len(u_q4_b)}")


if __name__ == "__main__":
    main()
