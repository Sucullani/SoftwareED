"""
Regresion: el solver debe tolerar node_ids no contiguos.

Antes del fix, el codigo asumia IDs contiguos 1..N y usaba `2*(nid-1)`
como indice DOF directo. Tras borrar nodos quedaban gaps (ej. {1, 5, 50})
y el ensamblaje fallaba con `IndexError: index 50 is out of bounds for
axis 1 with size 22` porque K se dimensiona como `2*num_nodes`.

El fix introduce `ProjectModel.node_index_map` (mapping node_id -> indice
ordinal) y reemplaza todas las ocurrencias de `2*(nid-1)` por
`2*idx_map[nid]`. Este test verifica:

  1. Solve no lanza excepcion con IDs {1, 5, 50, 99}.
  2. Los desplazamientos resultantes coinciden con los del mismo problema
     planteado con IDs {1, 2, 3, 4} (equivalencia numerica < 1e-9).
  3. project.dof_x / dof_y / node_index_map devuelven indices validos.
"""

import numpy as np

from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q4
from fem.solver import solve_system
from models.material import Material
from models.project import ProjectModel


def _build_unit_square(node_ids):
    """Construye un Q4 unitario con los 4 IDs de nodo dados.

    Geometria: cuadrado [0,1] x [0,1], CCW desde (0,0).
    BCs: empotrado en n1, rodillo Y en n2 (apoyo simple lado inferior).
    Carga: F = -1000 en Y aplicada en n4 (esquina superior izquierda).
    """
    proj = ProjectModel()
    proj.analysis_type = ANALYSIS_PLANE_STRESS
    proj.element_type = ELEMENT_Q4
    proj.default_thickness = 1.0
    proj.materials["Mat"] = Material(name="Mat", E=210000.0, nu=0.30,
                                     density=7.85e-6)

    n1, n2, n3, n4 = node_ids
    proj.add_node(0.0, 0.0, node_id=n1)
    proj.add_node(1.0, 0.0, node_id=n2)
    proj.add_node(1.0, 1.0, node_id=n3)
    proj.add_node(0.0, 1.0, node_id=n4)

    proj.add_element(node_ids=[n1, n2, n3, n4],
                     thickness=1.0, material_name="Mat", elem_id=1)

    proj.set_boundary_condition(n1, True, True)   # empotrado
    proj.set_boundary_condition(n2, False, True)  # rodillo en Y
    proj.set_nodal_load(n4, 0.0, -1000.0)
    return proj


def test_no_index_error_with_gaps():
    """1. Solve no lanza con IDs no contiguos."""
    proj = _build_unit_square([1, 5, 50, 99])
    result = solve_system(proj)
    u = result["u"]
    assert len(u) == 2 * proj.num_nodes == 8, (
        f"u tiene {len(u)} entradas, esperado 8 (= 2*num_nodes). "
        "Sintoma del bug: K se dimensionaba con max(node_id) en lugar de "
        "len(nodes)."
    )
    print(f"  [OK] solve_system con IDs {{1,5,50,99}} sin IndexError")
    print(f"       len(u) = {len(u)}, total_dof = {proj.total_dof}")


def test_dof_indices_within_range():
    """3. dof_x / dof_y devuelven indices validos."""
    proj = _build_unit_square([1, 5, 50, 99])
    n_dof = proj.total_dof
    for nid in proj.nodes:
        ix = proj.dof_x(nid)
        iy = proj.dof_y(nid)
        assert 0 <= ix < n_dof, f"dof_x({nid}) = {ix} fuera de [0,{n_dof})"
        assert 0 <= iy < n_dof, f"dof_y({nid}) = {iy} fuera de [0,{n_dof})"
        assert iy == ix + 1
    # Mapeo unico: dos node_ids no comparten indice.
    indices = sorted(proj.node_index_map.values())
    assert indices == list(range(proj.num_nodes)), (
        f"node_index_map debe ser una permutacion 0..N-1, obtuve {indices}"
    )
    print(f"  [OK] node_index_map = {dict(proj.node_index_map)}")
    print(f"       Todos los DOFs caen en [0, {n_dof})")


def test_numerical_equivalence_contiguous_vs_gapped():
    """2. Mismo problema con IDs contiguos vs con gaps -> mismos u."""
    proj_a = _build_unit_square([1, 2, 3, 4])
    proj_b = _build_unit_square([1, 5, 50, 99])

    res_a = solve_system(proj_a)
    res_b = solve_system(proj_b)

    # Comparar nodo por nodo segun la *ubicacion fisica* (mismo (x,y)
    # tiene la misma etiqueta n1..n4 en ambos modelos, aunque sus IDs
    # numericos difieran).
    label_to_id_a = {1: 1, 2: 2, 3: 3, 4: 4}
    label_to_id_b = {1: 1, 2: 5, 3: 50, 4: 99}

    max_delta = 0.0
    for label in (1, 2, 3, 4):
        nid_a = label_to_id_a[label]
        nid_b = label_to_id_b[label]
        ux_a = res_a["u"][proj_a.dof_x(nid_a)]
        uy_a = res_a["u"][proj_a.dof_y(nid_a)]
        ux_b = res_b["u"][proj_b.dof_x(nid_b)]
        uy_b = res_b["u"][proj_b.dof_y(nid_b)]
        max_delta = max(max_delta, abs(ux_a - ux_b), abs(uy_a - uy_b))

    assert max_delta < 1e-9, (
        f"Desplazamientos divergen entre IDs contiguos y con gaps: "
        f"max|delta| = {max_delta:.3e} (esperado < 1e-9). "
        "El mapeo node_id -> dof_index esta inconsistente entre call sites."
    )
    print(f"  [OK] Equivalencia numerica: max|delta_u| = {max_delta:.3e}")


def test_reactions_and_total_dof_consistency():
    """Los DOFs restringidos y libres respetan la nueva indexacion."""
    proj = _build_unit_square([1, 5, 50, 99])
    rdofs = proj.get_restrained_dofs()
    fdofs = proj.get_free_dofs()
    assert sorted(rdofs + fdofs) == list(range(proj.total_dof))
    # n1 (1) empotrado -> ambos DOFs restringidos.
    # n2 (5) rodillo Y -> solo dof_y restringido.
    expected_rdofs = sorted([
        proj.dof_x(1), proj.dof_y(1),
        proj.dof_y(5),
    ])
    assert rdofs == expected_rdofs, (
        f"get_restrained_dofs() = {rdofs}, esperado {expected_rdofs}"
    )
    print(f"  [OK] restrained_dofs = {rdofs}, free_dofs = {fdofs}")


if __name__ == "__main__":
    print("=== Regresion: node_ids no contiguos ===\n")
    test_no_index_error_with_gaps()
    test_dof_indices_within_range()
    test_numerical_equivalence_contiguous_vs_gapped()
    test_reactions_and_total_dof_consistency()
    print("\nTodos los tests pasaron.")
