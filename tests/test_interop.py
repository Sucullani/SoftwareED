"""
test_interop.py - Verificacion de la interoperabilidad de datos (objetivo 5):
  - ida y vuelta CSV/ZIP del ejemplo canonico sin perdida de entidades
    (file_io.model_io.export_model_csv -> import_model_csv);
  - importacion del DXF de ejemplo (resources/examples/ejemplo_geometria.dxf):
    solo la capa FEM_ELEMENTS, orientacion antihoraria forzada, nodos
    compartidos, e idempotencia al reimportar (0 nodos nuevos, todos los
    elementos omitidos como duplicados).

Ejecutar: python -m tests.test_interop
"""

import math
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import resource_path
from file_io.dxf_io import import_dxf
from file_io.model_io import export_model_csv, import_model_csv
from models.example_library import load_example_project
from models.project import ProjectModel


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"  PASS  {msg}")


def _close(a, b, tol=1e-9):
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


# ─── 1. CSV/ZIP: ida y vuelta ───────────────────────────────────────────────

def test_csv_round_trip():
    print("\n[1/2] test_csv_round_trip")
    p1 = load_example_project()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "modelo.zip")
        counts_out = export_model_csv(p1, path)
        _assert(os.path.exists(path), "export_model_csv escribe el .zip")
        p2 = ProjectModel()
        counts_in = import_model_csv(p2, path, mode="replace")

    _assert(counts_out["nodes"] == len(p1.nodes) == len(p2.nodes),
            f"nodos: exportados {counts_out['nodes']}, importados {len(p2.nodes)}")
    _assert(counts_out["elements"] == len(p1.elements) == len(p2.elements),
            f"elementos: exportados {counts_out['elements']}, importados {len(p2.elements)}")
    _assert(len(p1.materials) == len(p2.materials),
            f"materiales: {len(p1.materials)} == {len(p2.materials)}")
    _assert(len(p1.nodal_loads) == len(p2.nodal_loads),
            f"cargas nodales: {len(p1.nodal_loads)} == {len(p2.nodal_loads)}")
    _assert(len(p1.boundary_conditions) == len(p2.boundary_conditions),
            f"restricciones: {len(p1.boundary_conditions)} == {len(p2.boundary_conditions)}")
    _assert(len(p1.surface_loads) == len(p2.surface_loads),
            f"cargas superficiales: {len(p1.surface_loads)} == {len(p2.surface_loads)}")

    for nid, n1 in p1.nodes.items():
        n2 = p2.nodes[nid]
        _assert(_close(n1.x, n2.x) and _close(n1.y, n2.y), f"nodo {nid}: coordenadas identicas") \
            if nid == min(p1.nodes) else None
        if not (_close(n1.x, n2.x) and _close(n1.y, n2.y)):
            raise AssertionError(f"nodo {nid}: coordenadas distintas")
    print("  PASS  todas las coordenadas nodales coinciden")

    for eid, e1 in p1.elements.items():
        e2 = p2.elements[eid]
        if list(e1.node_ids) != list(e2.node_ids) or not _close(e1.thickness, e2.thickness) \
                or e1.material_name != e2.material_name:
            raise AssertionError(f"elemento {eid}: conectividad/espesor/material distintos")
    print("  PASS  conectividad, espesor y material de todos los elementos coinciden")

    for name, m1 in p1.materials.items():
        m2 = p2.materials[name]
        if not (_close(m1.E, m2.E) and _close(m1.nu, m2.nu) and _close(m1.density, m2.density)):
            raise AssertionError(f"material {name}: propiedades distintas")
    print("  PASS  E, nu y densidad de todos los materiales coinciden")

    for nid, l1 in p1.nodal_loads.items():
        l2 = p2.nodal_loads[nid]
        if not (_close(l1.fx, l2.fx) and _close(l1.fy, l2.fy)):
            raise AssertionError(f"carga nodal {nid}: componentes distintas")
    print("  PASS  cargas nodales coinciden")

    for nid, b1 in p1.boundary_conditions.items():
        b2 = p2.boundary_conditions[nid]
        if (bool(b1.restrain_x), bool(b1.restrain_y)) != (bool(b2.restrain_x), bool(b2.restrain_y)):
            raise AssertionError(f"restriccion {nid}: banderas distintas")
    print("  PASS  restricciones coinciden")

    # Sistema resuelto identico tras la ida y vuelta.
    from fem.solver import solve_system
    u1 = solve_system(p1)["u"]
    p2.element_type = p1.element_type
    p2.analysis_type = p1.analysis_type
    u2 = solve_system(p2)["u"]
    diff = float(np.max(np.abs(u1 - u2)))
    _assert(diff < 1e-12, f"desplazamientos identicos tras la ida y vuelta (max|delta| = {diff:.1e})")


# ─── 2. DXF: importacion e idempotencia ─────────────────────────────────────

def _signed_area(project, elem):
    pts = [(project.nodes[n].x, project.nodes[n].y) for n in elem.node_ids[:4]]
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % 4][1] - pts[(i + 1) % 4][0] * pts[i][1]
                     for i in range(4))


def test_dxf_import_idempotent():
    print("\n[2/2] test_dxf_import_idempotent")
    path = resource_path("examples", "ejemplo_geometria.dxf")
    _assert(os.path.exists(path), "existe el DXF de ejemplo (tests/generate_example_dxf.py)")
    project = ProjectModel()
    summary = import_dxf(path, project)
    _assert(summary["elements_added"] == 6 and len(project.elements) == 6,
            f"6 cuadrilateros de la capa FEM_ELEMENTS importados ({summary['elements_added']})")
    _assert(summary["nodes_added"] == 12 and len(project.nodes) == 12,
            f"12 nodos con vertices compartidos deduplicados ({summary['nodes_added']})")
    _assert(all(_signed_area(project, e) > 0 for e in project.elements.values()),
            "todos los elementos quedan en sentido antihorario (area con signo > 0)")
    _assert(not summary["warnings"], f"sin advertencias ({len(summary['warnings'])})")

    again = import_dxf(path, project)
    _assert(again["nodes_added"] == 0 and again["elements_added"] == 0
            and again["elements_skipped_duplicate"] == 6,
            "reimportar el mismo DXF es idempotente (0 nodos, 0 elementos, 6 duplicados omitidos)")
    _assert(len(project.nodes) == 12 and len(project.elements) == 6,
            "el modelo no cambia tras la reimportacion")


def main():
    print("=" * 70)
    print("  test_interop: interoperabilidad CSV/ZIP y DXF")
    print("=" * 70)
    test_csv_round_trip()
    test_dxf_import_idempotent()
    print("\n" + "=" * 70)
    print("  TODOS LOS TESTS DE INTEROPERABILIDAD PASARON")
    print("=" * 70)


if __name__ == "__main__":
    main()
