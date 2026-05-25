"""
vv_cook.py - Validacion con la membrana de Cook (benchmark historico 1974).

Geometria trapezoidal:
    corners (CCW desde SW): (0,0), (48,44), (48,60), (0,44)
    El lado izquierdo (x=0) esta empotrado.
    Una traccion tangencial uniforme F_total=1.0 actua en el lado derecho
    (x=48, de y=44 a y=60). q distribuido = F_total / L_right = 1.0/16.0.

Material:
    E = 1.0,  nu = 1/3,  plane stress,  t = 1.0

Cantidad de interes:
    u_y en el punto (48, 52) -- centro del lado libre.

Valor de referencia (literatura, Cook 1974 / Cook+Malkus+Plesha 1989):
    u_y_ref ≈ 23.95 (Q4 finely refined)
    u_y_ref ≈ 23.96 (cuadraticos / referencia analitica)

Convergencia con N = 2, 4, 8, 16, 32 para Q4 y Q9.

Outputs:
  docs/vyv/datos/cook.csv
  docs/vyv/figuras/cook_convergence.png
  docs/vyv/figuras/cook_deformed.png

Ejecutar: python -m tests.vv_cook
"""

import csv
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q4, ELEMENT_Q9
from fem.probe_query import displacement_at, locate_point
from fem.solver import solve_system
from models.material import Material
from models.mesh_utils import boundary_node_ids, generate_structured_quad_mesh


# ─── Constantes ─────────────────────────────────────────────────────────────

CORNERS = [(0.0, 0.0), (48.0, 44.0), (48.0, 60.0), (0.0, 44.0)]
E_COOK = 1.0
NU_COOK = 1.0 / 3.0
THICKNESS = 1.0
F_TOTAL = 1.0
L_RIGHT = 16.0
Q_PER_LEN = F_TOTAL / L_RIGHT
PROBE_X, PROBE_Y = 48.0, 52.0
U_Y_REF = 23.95


# ─── Driver ─────────────────────────────────────────────────────────────────

def build_project(N, element_type):
    project = generate_structured_quad_mesh(
        corners=CORNERS, nx=N, ny=N, element_type=element_type,
        material_name="Cook", thickness=THICKNESS,
        analysis_type=ANALYSIS_PLANE_STRESS,
    )
    project.materials["Cook"] = Material(
        name="Cook", E=E_COOK, nu=NU_COOK, density=0.0,
    )
    # BC: empotrado en x=0
    for nid in boundary_node_ids(project, "left"):
        project.set_boundary_condition(nid, True, True)

    # Carga tangencial uniforme en el lado derecho (de y=44 a y=60).
    # Lado derecho recorrido CCW del elemento: N2(SE) -> N3(NE).
    # tangente N2->N3 = (0, +1). normal "exterior" = (ty, -tx) = (+1, 0).
    # Con angle=0 y q>0 la carga aplica en direccion +x.
    # Quiero carga tangencial +y. angle = +90 grados (CCW) rota la normal
    # (+1,0) a (0,+1). Verificado mas abajo.
    tol = 1e-6
    for elem in project.elements.values():
        n2 = project.nodes[elem.node_ids[1]]   # SE corner
        n3 = project.nodes[elem.node_ids[2]]   # NE corner
        if abs(n2.x - 48.0) > tol or abs(n3.x - 48.0) > tol:
            continue
        project.add_surface_load(
            node_start=elem.node_ids[1],   # SE
            node_end=elem.node_ids[2],     # NE
            q_start=Q_PER_LEN, q_end=Q_PER_LEN,
            angle=90.0,
            element_id=elem.id,
        )
    return project


def run_case(N, element_type):
    project = build_project(N, element_type)
    sol = solve_system(project)
    # Verificar que la suma de F aplicada en y sea ~1.0
    F = sol["F"]
    fy_sum = float(np.sum(F[1::2]))  # componentes y
    # Probe en (48, 52)
    loc = locate_point(project, PROBE_X, PROBE_Y)
    if loc is None:
        return None
    eid, xi, eta = loc
    ux, uy = displacement_at(project, sol, eid, xi, eta)
    return {
        "N": N, "ndof": project.total_dof,
        "ux": ux, "uy": uy, "fy_sum": fy_sum,
        "project": project, "sol": sol,
    }


def save_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def plot_convergence(results_q4, results_q9, out_path):
    fig, ax = plt.subplots(figsize=(7, 5))
    ndof_q4 = [r["ndof"] for r in results_q4]
    uy_q4 = [r["uy"] for r in results_q4]
    ndof_q9 = [r["ndof"] for r in results_q9]
    uy_q9 = [r["uy"] for r in results_q9]
    ax.semilogx(ndof_q4, uy_q4, "o-", color="#0d6efd", label="Q4")
    ax.semilogx(ndof_q9, uy_q9, "s-", color="#fd7e14", label="Q9")
    ax.axhline(U_Y_REF, color="#198754", linewidth=1.0, linestyle="--",
               label=f"referencia $u_y$ = {U_Y_REF}")
    ax.set_xlabel("GDL totales")
    ax.set_ylabel(r"$u_y$ en (48, 52)")
    ax.set_title("Convergencia - membrana de Cook")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_deformed(project, sol, out_path, scale=1.0):
    coords = np.array(
        [[n.x, n.y] for n in project.nodes.values()], dtype=float
    )
    node_ids = list(project.nodes.keys())
    idx_map = project.node_index_map
    u_global = sol["u"]
    disp = np.zeros((len(node_ids), 2))
    for i, nid in enumerate(node_ids):
        base = 2 * idx_map[nid]
        disp[i, 0] = u_global[base]
        disp[i, 1] = u_global[base + 1]
    deformed = coords + scale * disp

    fig, ax = plt.subplots(figsize=(7, 7))
    for elem in project.elements.values():
        ids = elem.node_ids[:4]
        idx = [node_ids.index(nid) for nid in ids]
        poly_o = np.vstack([coords[idx], coords[idx[0]]])
        poly_d = np.vstack([deformed[idx], deformed[idx[0]]])
        ax.plot(poly_o[:, 0], poly_o[:, 1], color="#bbb", linewidth=0.5)
        ax.plot(poly_d[:, 0], poly_d[:, 1], color="#198754", linewidth=0.8)
    # Marcar punto de probe
    ax.plot([PROBE_X], [PROBE_Y], "ro", markersize=6, label="punto (48, 52)")
    ax.set_aspect("equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"Membrana de Cook deformada (×{scale})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "vyv",
    )
    datos_dir = os.path.join(out_dir, "datos")
    figs_dir = os.path.join(out_dir, "figuras")
    os.makedirs(datos_dir, exist_ok=True)
    os.makedirs(figs_dir, exist_ok=True)

    Ns = [2, 4, 8, 16, 32]
    results = {"q4": [], "q9": []}
    print("=" * 70)
    print("  Cook membrane: convergencia Q4 vs Q9")
    print("=" * 70)
    print(f"{'N':>4}  {'tipo':>4}  {'ndof':>6}  {'u_y':>10}  {'fy_sum':>10}  {'err_vs_23.95':>14}")

    for et_key, et in [("q4", ELEMENT_Q4), ("q9", ELEMENT_Q9)]:
        for N in Ns:
            r = run_case(N, et)
            if r is None:
                print(f"  {N:>4}  {et_key:>4}: punto fuera de malla")
                continue
            err_pct = 100 * (r["uy"] - U_Y_REF) / U_Y_REF
            print(f"  {N:>4}  {et_key:>4}  {r['ndof']:>6}  "
                  f"{r['uy']:>10.5f}  {r['fy_sum']:>10.5f}  {err_pct:>13.3f}%")
            results[et_key].append(r)

    # CSV
    header = ["N", "element_type", "ndof", "uy", "ux", "fy_sum",
              "ref", "error_pct"]
    rows = []
    for et_key in ("q4", "q9"):
        for r in results[et_key]:
            err_pct = 100 * (r["uy"] - U_Y_REF) / U_Y_REF
            rows.append([r["N"], et_key.upper(), r["ndof"],
                         f"{r['uy']:.5f}", f"{r['ux']:.5f}",
                         f"{r['fy_sum']:.5f}", U_Y_REF,
                         f"{err_pct:.4f}"])
    save_csv(os.path.join(datos_dir, "cook.csv"), header, rows)

    # Figura de convergencia
    plot_convergence(results["q4"], results["q9"],
                     os.path.join(figs_dir, "cook_convergence.png"))

    # Figura deformada para N=8 Q9 si disponible
    target_results = {
        (r["N"], "q9") for r in results["q9"]
    }
    pick = None
    for r in results["q9"]:
        if r["N"] == 8:
            pick = r
            break
    if pick is not None:
        # Escala ~malla/(2*uy_max) para visualizar
        scale = 1.0
        plot_deformed(pick["project"], pick["sol"],
                      os.path.join(figs_dir, "cook_deformed.png"),
                      scale=scale)

    print(f"\nOutputs en {out_dir}")


if __name__ == "__main__":
    main()
