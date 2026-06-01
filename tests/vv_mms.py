"""
vv_mms.py - Verificacion del solver EduFEM por el Metodo de Soluciones
Manufacturadas (MMS).

Solucion manufacturada en el cuadrado unitario [0,1]^2:
    u_M(x,y) = sin(pi*x) * sin(pi*y)
    v_M(x,y) = cos(pi*x) * cos(pi*y)

Material: E=1.0, nu=0.3, plane stress, t=1.0.
Body force: f = -div(sigma(u_M)) calculada analiticamente (ver derivacion
en `body_force_fn` mas abajo). BCs Dirichlet exactas en todo el borde.

Para cada N en {2,4,8,16,32}: arma malla NxN estructurada Q4 y Q9, calcula
desplazamientos, mide ||u_h - u_M||_L2 y ||grad(u_h - u_M)||_L2 con cuadratura
de Gauss un orden por encima del usado para K. Estima tasas asintoticas de
convergencia entre niveles consecutivos.

Outputs:
  docs/vyv/datos/mms_q4.csv
  docs/vyv/datos/mms_q9.csv
  docs/vyv/figuras/mms_convergence_l2.png
  docs/vyv/figuras/mms_convergence_h1.png
  docs/vyv/figuras/mms_field_u.png
  docs/vyv/figuras/mms_field_v.png

Ejecutar: python -m tests.vv_mms
"""

import csv
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q4, ELEMENT_Q9
from fem.error_norms import compute_error_norms
from fem.solver import solve_system
from models.material import Material
from models.mesh_utils import boundary_node_ids, generate_structured_quad_mesh


# ─── Solucion manufacturada y derivadas ─────────────────────────────────────

E_MMS = 1.0
NU_MMS = 0.3
PI = math.pi
# Plane stress: lambda_star = E*nu/(1-nu^2), mu = E/(2*(1+nu))
LAM = E_MMS * NU_MMS / (1.0 - NU_MMS * NU_MMS)
MU = E_MMS / (2.0 * (1.0 + NU_MMS))


def u_M(x, y):
    return (math.sin(PI * x) * math.sin(PI * y),
            math.cos(PI * x) * math.cos(PI * y))


def grad_u_M(x, y):
    sx, cx = math.sin(PI * x), math.cos(PI * x)
    sy, cy = math.sin(PI * y), math.cos(PI * y)
    return np.array([
        [PI * cx * sy, PI * sx * cy],     # du/dx, du/dy
        [-PI * sx * cy, -PI * cx * sy],   # dv/dx, dv/dy
    ])


def body_force_fn(x, y):
    """f = -div(sigma(u_M)) para plane stress.

    Derivacion (con sigma = lambda*tr(eps)*I + 2*mu*eps):
        div(sigma)_x = (lambda+2*mu)*u_xx + mu*u_yy + (lambda+mu)*v_xy
        div(sigma)_y = (lambda+mu)*u_xy + mu*v_xx + (lambda+2*mu)*v_yy
    Aqui u_xx = d2u/dx2, u_yy = d2u/dy2, u_xy = d2u/dxdy, idem v.

    Las segundas derivadas de u_M = sin(pi*x)*sin(pi*y) son:
        u_xx = -pi^2 sin(pi*x) sin(pi*y)
        u_yy = -pi^2 sin(pi*x) sin(pi*y)
        u_xy =  pi^2 cos(pi*x) cos(pi*y)
    Idem para v_M = cos(pi*x)*cos(pi*y):
        v_xx = -pi^2 cos(pi*x) cos(pi*y)
        v_yy = -pi^2 cos(pi*x) cos(pi*y)
        v_xy =  pi^2 sin(pi*x) sin(pi*y)

    Equilibrio: div(sigma) + b = 0  =>  b = -div(sigma).
    """
    sx, cx = math.sin(PI * x), math.cos(PI * x)
    sy, cy = math.sin(PI * y), math.cos(PI * y)
    pi2 = PI * PI

    u_xx = -pi2 * sx * sy
    u_yy = -pi2 * sx * sy
    u_xy = pi2 * cx * cy
    v_xx = -pi2 * cx * cy
    v_yy = -pi2 * cx * cy
    v_xy = pi2 * sx * sy

    div_sx = (LAM + 2 * MU) * u_xx + MU * u_yy + (LAM + MU) * v_xy
    div_sy = (LAM + MU) * u_xy + MU * v_xx + (LAM + 2 * MU) * v_yy
    return -div_sx, -div_sy


# ─── Driver ─────────────────────────────────────────────────────────────────

def run_case(N, element_type):
    project = generate_structured_quad_mesh(
        corners=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)],
        nx=N, ny=N, element_type=element_type,
        material_name="MMS", thickness=1.0,
        analysis_type=ANALYSIS_PLANE_STRESS,
    )
    project.materials["MMS"] = Material(
        name="MMS", E=E_MMS, nu=NU_MMS, density=0.0,
    )
    # Dirichlet exacto en todo el borde
    border = set()
    for edge in ("left", "right", "top", "bottom"):
        border.update(boundary_node_ids(project, edge))
    for nid in border:
        node = project.nodes[nid]
        ux, uy = u_M(node.x, node.y)
        project.set_boundary_condition(nid, True, True, ux, uy)

    sol = solve_system(project, body_force_fn=body_force_fn)
    norms = compute_error_norms(project, sol, u_M, grad_u_M)
    return project, sol, norms


def compute_rates(norms_list):
    """Tasa asintotica entre niveles consecutivos: rate = log(e_i-1 / e_i) / log(h_i-1 / h_i)."""
    rates_L2 = [None]
    rates_H1 = [None]
    for i in range(1, len(norms_list)):
        a, b = norms_list[i - 1], norms_list[i]
        rL2 = math.log(a["L2_disp"] / b["L2_disp"]) / math.log(a["h"] / b["h"])
        rH1 = math.log(a["H1_semi"] / b["H1_semi"]) / math.log(a["h"] / b["h"])
        rates_L2.append(rL2)
        rates_H1.append(rH1)
    return rates_L2, rates_H1


def save_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def plot_convergence(results_q4, results_q9, out_path, kind, title):
    """kind: 'L2' or 'H1'."""
    fig, ax = plt.subplots(figsize=(7, 5))
    key = "L2_disp" if kind == "L2" else "H1_semi"
    h_q4 = [r["h"] for r in results_q4]
    e_q4 = [r[key] for r in results_q4]
    h_q9 = [r["h"] for r in results_q9]
    e_q9 = [r[key] for r in results_q9]
    ax.loglog(h_q4, e_q4, "o-", color="#0d6efd", label="Q4")
    ax.loglog(h_q9, e_q9, "s-", color="#fd7e14", label="Q9")
    # Lineas de pendiente teorica
    h_ref = np.array([min(h_q4 + h_q9), max(h_q4 + h_q9)])
    if kind == "L2":
        c_q4 = e_q4[-1] / h_q4[-1] ** 2
        c_q9 = e_q9[-1] / h_q9[-1] ** 3
        ax.loglog(h_ref, c_q4 * h_ref ** 2, "--", color="#0d6efd", alpha=0.45,
                  label=r"O($h^2$)")
        ax.loglog(h_ref, c_q9 * h_ref ** 3, "--", color="#fd7e14", alpha=0.45,
                  label=r"O($h^3$)")
        ax.set_ylabel(r"$\|u_h - u_M\|_{L^2}$")
    else:
        c_q4 = e_q4[-1] / h_q4[-1] ** 1
        c_q9 = e_q9[-1] / h_q9[-1] ** 2
        ax.loglog(h_ref, c_q4 * h_ref, "--", color="#0d6efd", alpha=0.45,
                  label=r"O($h$)")
        ax.loglog(h_ref, c_q9 * h_ref ** 2, "--", color="#fd7e14", alpha=0.45,
                  label=r"O($h^2$)")
        ax.set_ylabel(r"$|u_h - u_M|_{H^1}$")
    ax.set_xlabel("h (tamaño caracteristico)")
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_field(project, sol, out_path, component, title):
    """Mapa de calor del campo u o v interpolado en una grilla."""
    # Construir grilla densa y evaluar u_h por elemento via probe_query.locate_point
    from fem.probe_query import displacement_at, locate_point

    n_grid = 80
    xs = np.linspace(0.0, 1.0, n_grid)
    ys = np.linspace(0.0, 1.0, n_grid)
    Z = np.zeros((n_grid, n_grid))
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            loc = locate_point(project, x, y)
            if loc is None:
                Z[j, i] = np.nan
                continue
            eid, xi, eta = loc
            ux, uy = displacement_at(project, sol, eid, xi, eta)
            Z[j, i] = ux if component == "u" else uy

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(Z, extent=(0, 1, 0, 1), origin="lower", cmap="viridis",
                   aspect="equal")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(title)
    plt.colorbar(im, ax=ax, label=component)
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
    projects = {"q4": {}, "q9": {}}

    for et_key, et in [("q4", ELEMENT_Q4), ("q9", ELEMENT_Q9)]:
        print(f"\n=== MMS sobre Q{4 if et_key == 'q4' else 9} ===")
        for N in Ns:
            project, sol, norms = run_case(N, et)
            projects[et_key][N] = (project, sol)
            results[et_key].append({
                "N": N, "h": norms["h"], "ndof": norms["ndof"],
                "L2_u": norms["L2_u"], "L2_v": norms["L2_v"],
                "L2_disp": norms["L2_disp"],
                "L2_disp_rel": norms["L2_disp_rel"] or 0.0,
                "H1_semi": norms["H1_semi"],
                "H1_semi_rel": norms["H1_semi_rel"] or 0.0,
                "n_gauss": norms["n_gauss"],
            })
            print(f"  N={N:2d}  ndof={norms['ndof']:5d}  "
                  f"L2={norms['L2_disp']:.4e}  H1={norms['H1_semi']:.4e}")

    # Tasas
    for et_key in ("q4", "q9"):
        rates_L2, rates_H1 = compute_rates(results[et_key])
        for r, rL2, rH1 in zip(results[et_key], rates_L2, rates_H1):
            r["rate_L2"] = rL2 if rL2 is not None else ""
            r["rate_H1"] = rH1 if rH1 is not None else ""

    # CSVs
    header = ["N", "h", "ndof", "L2_u", "L2_v", "L2_disp", "L2_disp_rel",
              "H1_semi", "H1_semi_rel", "rate_L2", "rate_H1", "n_gauss"]
    for et_key in ("q4", "q9"):
        rows = []
        for r in results[et_key]:
            rows.append([r["N"], f"{r['h']:.6f}", r["ndof"],
                         f"{r['L2_u']:.6e}", f"{r['L2_v']:.6e}",
                         f"{r['L2_disp']:.6e}", f"{r['L2_disp_rel']:.6e}",
                         f"{r['H1_semi']:.6e}", f"{r['H1_semi_rel']:.6e}",
                         f"{r['rate_L2']:.3f}" if r["rate_L2"] != "" else "",
                         f"{r['rate_H1']:.3f}" if r["rate_H1"] != "" else "",
                         r["n_gauss"]])
        save_csv(os.path.join(datos_dir, f"mms_{et_key}.csv"), header, rows)

    # Figuras de convergencia
    plot_convergence(results["q4"], results["q9"],
                     os.path.join(figs_dir, "mms_convergence_l2.png"),
                     "L2", "Convergencia en norma $L^2$ (MMS)")
    plot_convergence(results["q4"], results["q9"],
                     os.path.join(figs_dir, "mms_convergence_h1.png"),
                     "H1", "Convergencia en seminorma $H^1$ (MMS)")

    # Campos para N=16 Q9
    project_ref, sol_ref = projects["q9"][16]
    plot_field(project_ref, sol_ref,
               os.path.join(figs_dir, "mms_field_u.png"),
               "u", "Campo $u_h(x,y)$, malla Q9 16×16")
    plot_field(project_ref, sol_ref,
               os.path.join(figs_dir, "mms_field_v.png"),
               "v", "Campo $v_h(x,y)$, malla Q9 16×16")

    # Resumen final en consola
    print("\n=== Resumen final ===")
    for et_key in ("q4", "q9"):
        last = results[et_key][-1]
        print(f"  Q{4 if et_key == 'q4' else 9}: "
              f"L2 final {last['L2_disp']:.3e} (tasa~{last['rate_L2']}), "
              f"H1 final {last['H1_semi']:.3e} (tasa~{last['rate_H1']})")
    print(f"\nOutputs en {out_dir}")

    # ─── Verificacion automatica de regresion ──────────────────────────────
    # Las tasas de convergencia deben tender a las asintoticas teoricas:
    #   Q4 -> L2 O(h^2), H1 O(h^1);   Q9 -> L2 O(h^3), H1 O(h^2).
    # Tolerancia +-0.5 por la desviacion pre-asintotica de las mallas finitas.
    TOL = 0.5
    expected = {"q4": (2.0, 1.0), "q9": (3.0, 2.0)}
    checks = []
    for et_key in ("q4", "q9"):
        rL, rH = None, None
        for r in reversed(results[et_key]):
            if rL is None and r["rate_L2"] != "":
                rL = float(r["rate_L2"])
            if rH is None and r["rate_H1"] != "":
                rH = float(r["rate_H1"])
            if rL is not None and rH is not None:
                break
        exp_L, exp_H = expected[et_key]
        if rL is not None:
            checks.append((f"MMS {et_key.upper()} tasa L2~{exp_L} (obs {rL:.2f})",
                           abs(rL - exp_L) < TOL))
        if rH is not None:
            checks.append((f"MMS {et_key.upper()} tasa H1~{exp_H} (obs {rH:.2f})",
                           abs(rH - exp_H) < TOL))
    failed = [n for n, ok in checks if not ok]
    print("\n--- Verificacion ---")
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
