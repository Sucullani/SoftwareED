"""
Test de conversion de unidades del menu Modelo > Unidades.

Validaciones:
  1. Factores SI consistentes: convertir de un sistema a si mismo no cambia
     ningun valor.
  2. Round-trip A -> B -> A preserva los valores numericos (tolerancia 1e-9).
  3. Caso conocido: SI(N,m,Pa) -> SI(N,mm,MPa) multiplica coords x1000, E
     dividido entre 1e6, gravedad x1000.
  4. Sistemas desconocidos no son convertibles (`can_convert` retorna False).
  5. Heuristicas de salud: un E fuera del rango fisico tipico dispara warning.

Patron de output: scripts tipo printout (sin pytest), igual que el resto
de tests/.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.units import (
    UNIT_SYSTEMS, can_convert, get_conversion_factors,
)
from models.project import ProjectModel
from models.element import Element
from models.material import Material
from models.load import NodalLoad, SurfaceLoad
from models.node import Node


# Tolerancia para comparaciones float
TOL = 1e-9


def _passed(name, ok, msg=""):
    status = "[OK]" if ok else "[FAIL]"
    if msg:
        print(f"{status} {name}: {msg}")
    else:
        print(f"{status} {name}")
    return ok


def test_can_convert_basic():
    """Sistemas predefinidos son convertibles; un sistema desconocido
    (legacy o corrupto) no lo es."""
    ok1 = can_convert("SI (N, m, Pa)", "SI (N, mm, MPa)")
    ok2 = not can_convert("Personalizado", "SI (N, m, Pa)")  # legacy
    ok3 = not can_convert("SI (N, m, Pa)", "SI (N, m, Pa)")  # mismo sistema
    return _passed("can_convert_basic", ok1 and ok2 and ok3)


def test_factors_identity():
    """Convertir de un sistema A -> A (via dos sistemas distintos
    intermedios y vuelta) tiene factores que componen a 1.0."""
    A = "SI (N, m, Pa)"
    B = "SI (N, mm, MPa)"
    f_ab = get_conversion_factors(A, B)
    f_ba = get_conversion_factors(B, A)
    composed = {k: f_ab[k] * f_ba[k] for k in f_ab}
    ok = all(abs(v - 1.0) < TOL for v in composed.values())
    return _passed("factors_identity_AB_BA",
                   ok, f"composed: {composed}")


def test_factors_si_to_mmMPa():
    """Caso conocido: SI(N,m,Pa) -> SI(N,mm,MPa).
       - length factor = 1000 (m -> mm)
       - force factor = 1 (N -> N)
       - stress factor = 1e-6 (Pa -> MPa)
       - force_per_length factor = 1 / 1000 = 1e-3 (N/m -> N/mm)
       - acceleration factor = 1000 (m/s² -> mm/s²)
    """
    f = get_conversion_factors("SI (N, m, Pa)", "SI (N, mm, MPa)")
    ok = (
        abs(f["length"] - 1000) < TOL
        and abs(f["force"] - 1.0) < TOL
        and abs(f["stress"] - 1.0e-6) < 1e-15
        and abs(f["force_per_length"] - 1.0e-3) < TOL
        and abs(f["acceleration"] - 1000) < TOL
    )
    return _passed("factors_si_to_mmMPa", ok, f"got: {f}")


def _build_minimal_project():
    """Proyecto minimo con un Q4 + carga + BC + gravedad, en SI(N,m,Pa)."""
    p = ProjectModel()
    p.unit_system = "SI (N, m, Pa)"
    p.materials = {"acero": Material(name="acero", E=2.1e11, nu=0.3, density=7850)}
    p.add_node(0.0, 0.0, node_id=1)
    p.add_node(1.0, 0.0, node_id=2)
    p.add_node(1.0, 1.0, node_id=3)
    p.add_node(0.0, 1.0, node_id=4)
    p.add_element([1, 2, 3, 4], thickness=0.1, material_name="acero", elem_id=1)
    p.set_nodal_load(3, fx=1000.0, fy=-500.0)
    p.add_surface_load(node_start=1, node_end=2,
                       q_start=200.0, q_end=300.0, angle=0.0)
    p.gravity_x = 0.0
    p.gravity_y = -9.81
    return p


def test_convert_units_round_trip():
    """Convertir A -> B -> A debe restaurar los valores originales."""
    p = _build_minimal_project()
    # Snapshot original
    orig = {
        "node1_x": p.nodes[1].x,
        "node2_x": p.nodes[2].x,
        "material_E": p.materials["acero"].E,
        "thickness": p.elements[1].thickness,
        "default_thickness": p.default_thickness,
        "load_fx": p.nodal_loads[3].fx,
        "load_fy": p.nodal_loads[3].fy,
        "q_start": p.surface_loads[0].q_start,
        "q_end": p.surface_loads[0].q_end,
        "gravity_y": p.gravity_y,
    }
    # A -> B
    f1 = get_conversion_factors("SI (N, m, Pa)", "SI (N, mm, MPa)")
    p.convert_units(f1)
    p.unit_system = "SI (N, mm, MPa)"
    # B -> A
    f2 = get_conversion_factors("SI (N, mm, MPa)", "SI (N, m, Pa)")
    p.convert_units(f2)
    p.unit_system = "SI (N, m, Pa)"

    new = {
        "node1_x": p.nodes[1].x,
        "node2_x": p.nodes[2].x,
        "material_E": p.materials["acero"].E,
        "thickness": p.elements[1].thickness,
        "default_thickness": p.default_thickness,
        "load_fx": p.nodal_loads[3].fx,
        "load_fy": p.nodal_loads[3].fy,
        "q_start": p.surface_loads[0].q_start,
        "q_end": p.surface_loads[0].q_end,
        "gravity_y": p.gravity_y,
    }
    ok = True
    diffs = []
    for k, v_orig in orig.items():
        v_new = new[k]
        denom = max(abs(v_orig), 1.0)
        if abs(v_new - v_orig) / denom > 1e-9:
            ok = False
            diffs.append(f"{k}: {v_orig} -> {v_new}")
    return _passed("convert_units_round_trip", ok,
                   "; ".join(diffs) if diffs else "valores preservados")


def test_convert_units_known_values():
    """Caso conocido: 1 m → 1000 mm, 2.1e11 Pa → 2.1e5 MPa, 9.81 m/s² → 9810 mm/s²."""
    p = _build_minimal_project()
    f = get_conversion_factors("SI (N, m, Pa)", "SI (N, mm, MPa)")
    p.convert_units(f)
    ok = (
        abs(p.nodes[2].x - 1000.0) < TOL
        and abs(p.nodes[3].y - 1000.0) < TOL
        and abs(p.materials["acero"].E - 210000.0) < TOL
        and abs(p.elements[1].thickness - 100.0) < TOL
        and abs(p.gravity_y - (-9810.0)) < TOL
        and abs(p.nodal_loads[3].fx - 1000.0) < TOL  # fuerza no cambia
        and abs(p.surface_loads[0].q_start - 0.2) < TOL  # 200 N/m -> 0.2 N/mm
    )
    return _passed(
        "convert_units_known_values", ok,
        f"node[2].x={p.nodes[2].x}, E={p.materials['acero'].E}, "
        f"thickness={p.elements[1].thickness}, gy={p.gravity_y}, "
        f"q_start={p.surface_loads[0].q_start}"
    )


def test_invalidates_solution():
    """Tras convert_units, is_solved debe ser False y la solucion None."""
    p = _build_minimal_project()
    p.is_solved = True
    p.displacements = [1.0, 2.0]  # fake
    p.stresses = {1: {"vm": [10.0]}}
    f = get_conversion_factors("SI (N, m, Pa)", "SI (N, mm, MPa)")
    p.convert_units(f)
    ok = (not p.is_solved and p.displacements is None
          and p.stresses == {} and p.is_modified)
    return _passed("invalidates_solution_after_convert", ok)


def test_health_suspicious_E():
    """Un material con E muy bajo dispara warning de consistencia."""
    from models.model_health import validate_project, HealthCode
    p = _build_minimal_project()
    # E muy chico para Pa (210 Pa ~ no es un material estructural)
    p.materials["acero"].E = 210.0
    report = validate_project(p)
    codes = [iss.code for iss in report.warnings]
    ok = HealthCode.SUSPICIOUS_YOUNG_MODULUS in codes
    return _passed("health_suspicious_E", ok,
                   f"warnings: {codes}")


def test_health_suspicious_scale():
    """Un modelo a escala 1e8 m (= 100 000 km) dispara warning."""
    from models.model_health import validate_project, HealthCode
    p = _build_minimal_project()
    # Coords gigantes (100 millones de metros = escala interplanetaria)
    for n in p.nodes.values():
        n.x *= 1e8
        n.y *= 1e8
    report = validate_project(p)
    codes = [iss.code for iss in report.warnings]
    ok = HealthCode.SUSPICIOUS_MODEL_SCALE in codes
    return _passed("health_suspicious_scale", ok,
                   f"warnings: {codes}")


def test_health_gravity_no_density():
    """include_gravity activa + densidad=0 dispara warning."""
    from models.model_health import validate_project, HealthCode
    p = _build_minimal_project()
    p.include_gravity = True
    p.materials["acero"].density = 0.0
    report = validate_project(p)
    codes = [iss.code for iss in report.warnings]
    ok = HealthCode.GRAVITY_NO_DENSITY in codes
    return _passed("health_gravity_no_density", ok,
                   f"warnings: {codes}")


def main():
    print("=" * 60)
    print("  TEST conversion de unidades")
    print("=" * 60)
    results = [
        test_can_convert_basic(),
        test_factors_identity(),
        test_factors_si_to_mmMPa(),
        test_convert_units_round_trip(),
        test_convert_units_known_values(),
        test_invalidates_solution(),
        test_health_suspicious_E(),
        test_health_suspicious_scale(),
        test_health_gravity_no_density(),
    ]
    print()
    if all(results):
        print(f"Todos los {len(results)} tests pasan.")
        sys.exit(0)
    else:
        n_fail = sum(1 for r in results if not r)
        print(f"FAIL: {n_fail}/{len(results)} tests fallaron.")
        sys.exit(1)


if __name__ == "__main__":
    main()
