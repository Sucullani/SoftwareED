"""
bench_timing.py - Benchmark de escalabilidad del motor numerico de EduFEM.

Mide el tiempo de pared del ensamblaje y de la solucion completa del sistema
disperso K u = F a refinamientos crecientes, junto con el numero de no-nulos de
K y la memoria que ocuparia en formato denso frente al disperso (CSR). Sirve
como evidencia cuantitativa de la escalabilidad reportada en la tesis
(Capitulo de resultados, subseccion de limitaciones).

Reutiliza el armado bien planteado de la membrana de Cook (geometria trapezoidal
+ empotramiento + traccion tangencial) a tamanos N x N crecientes, de modo que
cada caso es un problema solucionable y representativo.

Ejecutar:  python -m tests.bench_timing

Nota: los tiempos son indicativos y dependen del equipo. Se imprime la
identificacion de la maquina para contextualizar la medicion.
"""

import os
import platform
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q9
from scipy.sparse.linalg import spsolve

from fem.assembly import assemble_global_system
from fem.solver import apply_boundary_conditions, solve_system
from models.material import Material
from models.mesh_utils import boundary_node_ids, generate_structured_quad_mesh


CORNERS = [(0.0, 0.0), (48.0, 44.0), (48.0, 60.0), (0.0, 44.0)]
E_COOK = 1.0
NU_COOK = 1.0 / 3.0
THICKNESS = 1.0
Q_PER_LEN = 1.0 / 16.0


def build_project(N, element_type):
    project = generate_structured_quad_mesh(
        corners=CORNERS, nx=N, ny=N, element_type=element_type,
        material_name="Cook", thickness=THICKNESS,
        analysis_type=ANALYSIS_PLANE_STRESS,
    )
    project.materials["Cook"] = Material(
        name="Cook", E=E_COOK, nu=NU_COOK, density=0.0,
    )
    for nid in boundary_node_ids(project, "left"):
        project.set_boundary_condition(nid, True, True)
    tol = 1e-6
    for elem in project.elements.values():
        n2 = project.nodes[elem.node_ids[1]]
        n3 = project.nodes[elem.node_ids[2]]
        if abs(n2.x - 48.0) > tol or abs(n3.x - 48.0) > tol:
            continue
        project.add_surface_load(
            node_start=elem.node_ids[1], node_end=elem.node_ids[2],
            q_start=Q_PER_LEN, q_end=Q_PER_LEN, angle=90.0,
            element_id=elem.id,
        )
    return project


def _best(fn, repeats):
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best


def time_case(N, element_type, repeats=3):
    project = build_project(N, element_type)
    ndof = project.total_dof
    n_elem = len(project.elements)

    t_asm = _best(lambda: assemble_global_system(project), repeats)
    t_solve = _best(lambda: solve_system(project), repeats)

    K, F, _ed = assemble_global_system(project)
    nnz = int(K.nnz)
    dense_mb = ndof * ndof * 8 / 1e6
    sparse_mb = (K.data.nbytes + K.indices.nbytes + K.indptr.nbytes) / 1e6

    # Ordenamiento de columnas de SuperLU: el generico COLAMD frente al
    # MMD_AT_PLUS_A que usa el motor (aprovecha la simetria estructural de K).
    # Evidencia de la afirmacion de las conclusiones de la tesis.
    K_red, F_red, _free = apply_boundary_conditions(
        K, F, project.get_restrained_dofs())
    K_csc = K_red.tocsc()
    t_colamd = _best(lambda: spsolve(K_csc, F_red, permc_spec="COLAMD"), repeats)
    t_mmd = _best(lambda: spsolve(K_csc, F_red, permc_spec="MMD_AT_PLUS_A"), repeats)
    return {
        "N": N, "n_elem": n_elem, "ndof": ndof, "nnz": nnz,
        "t_asm": t_asm, "t_solve": t_solve,
        "dense_mb": dense_mb, "sparse_mb": sparse_mb,
        "t_colamd": t_colamd, "t_mmd": t_mmd,
    }


def main():
    print("=" * 78)
    print("  Benchmark de escalabilidad - membrana de Cook Q9")
    print(f"  Maquina : {platform.processor() or platform.machine()}")
    print(f"  Sistema : {platform.system()} {platform.release()}")
    print(f"  Python  : {platform.python_version()} | NumPy {np.__version__}")
    print("  Motor   : NumPy vectorizado por lotes (fem/batch.py), sin JIT")
    print("=" * 78)
    header = (f"{'N':>3} {'elem':>6} {'GDL':>7} {'nnz(K)':>9} "
              f"{'t_asm[s]':>9} {'t_solve[s]':>11} "
              f"{'densoK[MB]':>11} {'CSR[MB]':>9}")
    print(header)
    print("-" * 78)
    Ns = [8, 16, 24, 32, 48, 64]
    rows = []
    for N in Ns:
        r = time_case(N, ELEMENT_Q9)
        rows.append(r)
        print(f"{r['N']:>3} {r['n_elem']:>6} {r['ndof']:>7} {r['nnz']:>9} "
              f"{r['t_asm']:>9.3f} {r['t_solve']:>11.3f} "
              f"{r['dense_mb']:>11.1f} {r['sparse_mb']:>9.2f}")
    print("-" * 78)
    print("\nFilas LaTeX (GDL & t_asm & t_solve & densoK & CSR):")
    for r in rows:
        print(f"  {r['ndof']} & {r['t_asm']:.3f} & {r['t_solve']:.3f} & "
              f"{r['dense_mb']:.0f} & {r['sparse_mb']:.2f} \\\\")
    print("\nOrdenamiento de columnas (solo factorizacion + solucion del sistema reducido):")
    print(f"{'GDL':>7} {'COLAMD[s]':>10} {'MMD_AT+A[s]':>12} {'ratio':>6}")
    for r in rows:
        ratio = r["t_colamd"] / r["t_mmd"] if r["t_mmd"] > 0 else float("nan")
        print(f"{r['ndof']:>7} {r['t_colamd']:>10.3f} {r['t_mmd']:>12.3f} {ratio:>6.2f}")


if __name__ == "__main__":
    main()
