"""
vv_mms.py - Verificacion del solver EduFEM por el Metodo de Soluciones
Manufacturadas (MMS).

Solucion manufacturada en el cuadrado unitario [0,1]^2:
    u_M(x,y) = sin(pi*x) * sin(pi*y)
    v_M(x,y) = cos(pi*x) * cos(pi*y)

Material: E=1.0, nu=0.3, t=1.0. Cuatro configuraciones:
    {cuadrado unitario, cuadrilatero distorsionado} x {tension plana,
    deformacion plana}.
Body force: f = -div(sigma(u_M)) calculada analiticamente (ver derivacion
en `make_body_force_fn`); la constante de Lame lambda depende del estado
plano. BCs Dirichlet exactas en todo el borde (deteccion topologica de las
aristas exteriores, valida para cualquier cuadrilatero).

Para cada N en {2,4,8,16,32}: arma malla NxN estructurada Q4 y Q9, calcula
desplazamientos, mide ||u_h - u_M||_L2, ||grad(u_h - u_M)||_L2 y el error
L2 del campo de tensiones RECUPERADO (Gauss -> nodos -> promedio -> N,
fem.error_norms.compute_stress_recovery_error) con cuadratura de Gauss un
orden por encima del usado para K. Estima tasas asintoticas de convergencia
entre niveles consecutivos.

Outputs:
  docs/vyv/datos/mms_q4.csv, mms_q9.csv            (unitario, tension plana)
  docs/vyv/datos/mms_{q4,q9}_{dist_tp,unif_dp,dist_dp}.csv
  docs/vyv/datos/mms_resumen.csv                    (tasas asintoticas, 4 configs)
  docs/vyv/figuras/mms_convergence_l2.png
  docs/vyv/figuras/mms_convergence_h1.png
  docs/vyv/figuras/mms_convergence_stress.png   (campo de tensiones recuperado)
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

from config.settings import (ANALYSIS_PLANE_STRAIN, ANALYSIS_PLANE_STRESS,
                             ELEMENT_Q4, ELEMENT_Q9)
from fem.error_norms import compute_error_norms, compute_stress_recovery_error
from fem.solver import solve_system
from models.material import Material
from models.mesh_utils import generate_structured_quad_mesh


# ─── Solucion manufacturada y derivadas ─────────────────────────────────────

E_MMS = 1.0
NU_MMS = 0.3
PI = math.pi
# Constantes de Lame. mu es comun; lambda depende del estado plano:
#   tension plana:     lambda* = E*nu/(1-nu^2)
#   deformacion plana: lambda  = E*nu/((1+nu)(1-2nu))
MU = E_MMS / (2.0 * (1.0 + NU_MMS))
LAM_TP = E_MMS * NU_MMS / (1.0 - NU_MMS * NU_MMS)
LAM_DP = E_MMS * NU_MMS / ((1.0 + NU_MMS) * (1.0 - 2.0 * NU_MMS))
LAM = LAM_TP   # compatibilidad: `body_force_fn` (abajo) es el caso de tension plana

# Dominios: cuadrado unitario y un cuadrilatero general (elementos
# distorsionados: Jacobiano no constante, mapeo inverso no trivial).
CORNERS_UNIT = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
CORNERS_DIST = [(0.0, 0.0), (1.0, 0.15), (0.85, 1.0), (0.1, 0.8)]

CONFIGS = [
    # clave, corners, tipo de analisis, etiqueta
    ("unif_tp", CORNERS_UNIT, ANALYSIS_PLANE_STRESS, "cuadrado unitario / tension plana"),
    ("dist_tp", CORNERS_DIST, ANALYSIS_PLANE_STRESS, "cuadrilatero distorsionado / tension plana"),
    ("unif_dp", CORNERS_UNIT, ANALYSIS_PLANE_STRAIN, "cuadrado unitario / deformacion plana"),
    ("dist_dp", CORNERS_DIST, ANALYSIS_PLANE_STRAIN, "cuadrilatero distorsionado / deformacion plana"),
]


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


def make_body_force_fn(analysis_type):
    """Devuelve f(x, y) = -div(sigma(u_M)) para el estado plano indicado.

    Solo cambia la constante lambda de la ley constitutiva
    sigma = lambda*tr(eps)*I + 2*mu*eps (misma derivacion que `body_force_fn`).
    """
    lam = LAM_DP if analysis_type == ANALYSIS_PLANE_STRAIN else LAM_TP

    def fn(x, y):
        sx, cx = math.sin(PI * x), math.cos(PI * x)
        sy, cy = math.sin(PI * y), math.cos(PI * y)
        pi2 = PI * PI
        u_xx = -pi2 * sx * sy
        u_yy = -pi2 * sx * sy
        u_xy = pi2 * cx * cy
        v_xx = -pi2 * cx * cy
        v_yy = -pi2 * cx * cy
        v_xy = pi2 * sx * sy
        div_sx = (lam + 2 * MU) * u_xx + MU * u_yy + (lam + MU) * v_xy
        div_sy = (lam + MU) * u_xy + MU * v_xx + (lam + 2 * MU) * v_yy
        return -div_sx, -div_sy

    return fn


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

def boundary_nodes_topological(project):
    """Nodos sobre aristas exteriores: aristas que pertenecen a un solo
    elemento. Vale para cualquier cuadrilatero (boundary_node_ids usa el
    bounding box y solo sirve para dominios rectangulares). En Q9 incluye
    el nodo medio de cada arista exterior (node_ids[4+k] esta sobre la
    arista (k, k+1))."""
    from collections import Counter
    count = Counter()
    for elem in project.elements.values():
        c = elem.node_ids[:4]
        for k in range(4):
            count[frozenset((c[k], c[(k + 1) % 4]))] += 1
    border = set()
    for elem in project.elements.values():
        c = elem.node_ids[:4]
        for k in range(4):
            if count[frozenset((c[k], c[(k + 1) % 4]))] == 1:
                border.add(c[k])
                border.add(c[(k + 1) % 4])
                if len(elem.node_ids) == 9:
                    border.add(elem.node_ids[4 + k])
    return border


def run_case(N, element_type, *, corners=CORNERS_UNIT,
             analysis_type=ANALYSIS_PLANE_STRESS):
    project = generate_structured_quad_mesh(
        corners=corners,
        nx=N, ny=N, element_type=element_type,
        material_name="MMS", thickness=1.0,
        analysis_type=analysis_type,
    )
    project.materials["MMS"] = Material(
        name="MMS", E=E_MMS, nu=NU_MMS, density=0.0,
    )
    # Dirichlet exacto en todo el borde
    for nid in boundary_nodes_topological(project):
        node = project.nodes[nid]
        ux, uy = u_M(node.x, node.y)
        project.set_boundary_condition(nid, True, True, ux, uy)

    sol = solve_system(project, body_force_fn=make_body_force_fn(analysis_type))
    norms = compute_error_norms(project, sol, u_M, grad_u_M)
    # Campo de tensiones recuperado (Gauss -> nodos -> promedio -> N): es lo
    # que muestra el post-proceso; las normas de desplazamiento no lo tocan.
    norms.update(compute_stress_recovery_error(project, sol, grad_u_M))
    return project, sol, norms


def compute_rates(norms_list):
    """Tasa asintotica entre niveles consecutivos: rate = log(e_i-1 / e_i) / log(h_i-1 / h_i)."""
    rates_L2 = [None]
    rates_H1 = [None]
    rates_S = [None]
    for i in range(1, len(norms_list)):
        a, b = norms_list[i - 1], norms_list[i]
        lh = math.log(a["h"] / b["h"])
        rates_L2.append(math.log(a["L2_disp"] / b["L2_disp"]) / lh)
        rates_H1.append(math.log(a["H1_semi"] / b["H1_semi"]) / lh)
        rates_S.append(math.log(a["L2_stress"] / b["L2_stress"]) / lh)
    return rates_L2, rates_H1, rates_S


def save_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def plot_convergence(results_q4, results_q9, out_path, kind, title):
    """kind: 'L2' or 'H1'."""
    fig, ax = plt.subplots(figsize=(7, 5))
    key = {"L2": "L2_disp", "H1": "H1_semi", "S": "L2_stress"}[kind]
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
    elif kind == "S":
        # Campo recuperado (Gauss -> nodos -> promedio): la superconvergencia
        # interior O(h^2) del Q4 se degrada en la capa de contorno (nodos con
        # promedio unilateral) y la norma global observa O(h^1.5); Q9 da O(h^2).
        c_q4 = e_q4[-1] / h_q4[-1] ** 1.5
        c_q9 = e_q9[-1] / h_q9[-1] ** 2
        ax.loglog(h_ref, c_q4 * h_ref ** 1.5, "--", color="#0d6efd", alpha=0.45,
                  label=r"O($h^{1.5}$)")
        ax.loglog(h_ref, c_q9 * h_ref ** 2, "--", color="#fd7e14", alpha=0.45,
                  label=r"O($h^2$)")
        ax.set_ylabel(r"$\|\sigma^*_h - \sigma_M\|_{L^2}$")
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

def _rate_last(rows, key):
    for r in reversed(rows):
        if r.get(key, "") != "":
            return float(r[key])
    return None


def _run_config(cfg_key, corners, analysis_type, Ns):
    results = {"q4": [], "q9": []}
    projects = {"q4": {}, "q9": {}}
    for et_key, et in [("q4", ELEMENT_Q4), ("q9", ELEMENT_Q9)]:
        print(f"\n=== MMS [{cfg_key}] sobre Q{4 if et_key == 'q4' else 9} ===")
        for N in Ns:
            project, sol, norms = run_case(N, et, corners=corners,
                                           analysis_type=analysis_type)
            projects[et_key][N] = (project, sol)
            results[et_key].append({
                "N": N, "h": norms["h"], "ndof": norms["ndof"],
                "L2_u": norms["L2_u"], "L2_v": norms["L2_v"],
                "L2_disp": norms["L2_disp"],
                "L2_disp_rel": norms["L2_disp_rel"] or 0.0,
                "H1_semi": norms["H1_semi"],
                "H1_semi_rel": norms["H1_semi_rel"] or 0.0,
                "n_gauss": norms["n_gauss"],
                "L2_stress": norms["L2_stress"],
                "L2_stress_rel": norms["L2_stress_rel"] or 0.0,
            })
            print(f"  N={N:2d}  ndof={norms['ndof']:5d}  "
                  f"L2={norms['L2_disp']:.4e}  H1={norms['H1_semi']:.4e}  "
                  f"L2(sigma*)={norms['L2_stress']:.4e}")
    for et_key in ("q4", "q9"):
        rates_L2, rates_H1, rates_S = compute_rates(results[et_key])
        for r, rL2, rH1, rS in zip(results[et_key], rates_L2, rates_H1, rates_S):
            r["rate_L2"] = rL2 if rL2 is not None else ""
            r["rate_H1"] = rH1 if rH1 is not None else ""
            r["rate_stress"] = rS if rS is not None else ""
    return results, projects


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
    header = ["N", "h", "ndof", "L2_u", "L2_v", "L2_disp", "L2_disp_rel",
              "H1_semi", "H1_semi_rel", "rate_L2", "rate_H1", "n_gauss",
              "L2_stress", "L2_stress_rel", "rate_stress"]

    all_results = {}
    base_projects = None
    for cfg_key, corners, analysis_type, label in CONFIGS:
        results, projects = _run_config(cfg_key, corners, analysis_type, Ns)
        all_results[cfg_key] = results
        if cfg_key == "unif_tp":
            base_projects = projects
        for et_key in ("q4", "q9"):
            rows = []
            for r in results[et_key]:
                rows.append([r["N"], f"{r['h']:.6f}", r["ndof"],
                             f"{r['L2_u']:.6e}", f"{r['L2_v']:.6e}",
                             f"{r['L2_disp']:.6e}", f"{r['L2_disp_rel']:.6e}",
                             f"{r['H1_semi']:.6e}", f"{r['H1_semi_rel']:.6e}",
                             f"{r['rate_L2']:.3f}" if r["rate_L2"] != "" else "",
                             f"{r['rate_H1']:.3f}" if r["rate_H1"] != "" else "",
                             r["n_gauss"],
                             f"{r['L2_stress']:.6e}", f"{r['L2_stress_rel']:.6e}",
                             f"{r['rate_stress']:.3f}" if r["rate_stress"] != "" else ""])
            suffix = "" if cfg_key == "unif_tp" else f"_{cfg_key}"
            save_csv(os.path.join(datos_dir, f"mms_{et_key}{suffix}.csv"), header, rows)

    # Resumen de tasas asintoticas (ultimo nivel) por configuracion y elemento
    resumen_rows = []
    for cfg_key, corners, analysis_type, label in CONFIGS:
        for et_key in ("q4", "q9"):
            rows = all_results[cfg_key][et_key]
            last = rows[-1]
            resumen_rows.append([
                cfg_key, label, "Q4" if et_key == "q4" else "Q9", last["ndof"],
                f"{_rate_last(rows, 'rate_L2'):.3f}",
                f"{_rate_last(rows, 'rate_H1'):.3f}",
                f"{_rate_last(rows, 'rate_stress'):.3f}",
                f"{last['L2_disp_rel']:.3e}", f"{last['H1_semi_rel']:.3e}",
                f"{last['L2_stress_rel']:.3e}",
            ])
    save_csv(os.path.join(datos_dir, "mms_resumen.csv"),
             ["config", "descripcion", "elemento", "ndof_final", "rate_L2",
              "rate_H1", "rate_stress", "L2_disp_rel_final", "H1_semi_rel_final",
              "L2_stress_rel_final"], resumen_rows)

    # Figuras de convergencia (configuracion base)
    results = all_results["unif_tp"]
    plot_convergence(results["q4"], results["q9"],
                     os.path.join(figs_dir, "mms_convergence_l2.png"),
                     "L2", "Convergencia en norma $L^2$ (MMS)")
    plot_convergence(results["q4"], results["q9"],
                     os.path.join(figs_dir, "mms_convergence_h1.png"),
                     "H1", "Convergencia en seminorma $H^1$ (MMS)")
    plot_convergence(results["q4"], results["q9"],
                     os.path.join(figs_dir, "mms_convergence_stress.png"),
                     "S", "Convergencia del campo de tensiones recuperado (MMS)")

    # Campos para N=16 Q9 (configuracion base)
    project_ref, sol_ref = base_projects["q9"][16]
    plot_field(project_ref, sol_ref,
               os.path.join(figs_dir, "mms_field_u.png"),
               "u", "Campo $u_h(x,y)$, malla Q9 16×16")
    plot_field(project_ref, sol_ref,
               os.path.join(figs_dir, "mms_field_v.png"),
               "v", "Campo $v_h(x,y)$, malla Q9 16×16")

    # Resumen final en consola
    print("\n=== Resumen final (tasas asintoticas) ===")
    for row in resumen_rows:
        print(f"  {row[0]:8s} {row[2]}: L2 {row[4]}  H1 {row[5]}  L2(sigma*) {row[6]}"
              f"   rel finales {row[7]} / {row[8]} / {row[9]}")
    print(f"\nOutputs en {out_dir}")

    # ─── Verificacion automatica de regresion ──────────────────────────────
    # Las tasas de convergencia deben tender a las asintoticas teoricas en
    # las cuatro configuraciones:
    #   Q4 -> L2 O(h^2), H1 O(h^1);   Q9 -> L2 O(h^3), H1 O(h^2).
    # Tolerancia +-0.5 por la desviacion pre-asintotica de las mallas finitas.
    # Campo de tensiones recuperado: la literatura consultada no fija una tasa
    # teorica para la cadena Gauss -> extrapolacion -> promediado nodal del
    # motor, asi que el criterio es una COTA EMPIRICA MINIMA, declarada como tal
    # en la tesis (sec. 2.1.6): tasa >= 1.4 en Q4 (observado ~1.54, la capa de
    # contorno degrada la superconvergencia interior) y >= 1.9 en Q9 (~2.00).
    # Antes se usaba 1.5 +- 0.5, que aceptaba tambien el orden del gradiente
    # crudo (1.0) y realimentaba el valor observado como expectativa.
    TOL = 0.5
    expected = {"q4": (2.0, 1.0), "q9": (3.0, 2.0)}
    stress_min = {"q4": 1.4, "q9": 1.9}
    checks = []
    for cfg_key, corners, analysis_type, label in CONFIGS:
        for et_key in ("q4", "q9"):
            rows = all_results[cfg_key][et_key]
            exp_L, exp_H = expected[et_key]
            for key, exp, name in (("rate_L2", exp_L, "L2"), ("rate_H1", exp_H, "H1")):
                obs = _rate_last(rows, key)
                if obs is not None:
                    checks.append((f"MMS [{cfg_key}] {et_key.upper()} tasa {name}~{exp} "
                                   f"(obs {obs:.2f})", abs(obs - exp) < TOL))
            obs_s = _rate_last(rows, "rate_stress")
            if obs_s is not None:
                checks.append((f"MMS [{cfg_key}] {et_key.upper()} tasa L2(sigma*) >= "
                               f"{stress_min[et_key]} (obs {obs_s:.2f})",
                               obs_s >= stress_min[et_key]))
    failed = [n for n, ok in checks if not ok]
    print("\n--- Verificacion ---")
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
