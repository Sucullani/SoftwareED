"""
vv_timoshenko.py - Validacion del solver EduFEM contra:
  (a) la solucion analitica de Timoshenko & Goodier para una viga
      simplemente apoyada bajo carga uniforme,
  (b) la cross-validation con el modelo Shell de SAP2000 documentado en
      docs/Timoshenko,sap2000.pdf.

Configuracion del problema (verbatim del PDF):
    L = 14 m, H = 1.20 m, b = 0.40 m, c = H/2 = 0.6 m
    E = 217370 kg/cm^2 ≈ 21.32 GPa,  nu = 0.2
    q = 5000 kg/m hacia -y  (49033.25 N/m)
    BCs: apoyo fijo (-7, 0), rodillo (+7, 0)
    Inercia: I = b*H^3/12 = 0.0576 m^4
    Semi-luz: l = L/2 = 7 m

Soluciones analiticas (Timoshenko & Goodier, ec. 24 sec. 21):
    sigma_x(x,y) = (q/2I)(l^2 - x^2) y + (q/2I)(2y^3/3 - 2c^2 y/5)
    sigma_y(x,y) = -(q/2I)(y^3/3 - c^2 y + 2c^3/3)
    tau_xy(x,y) = -(q/2I)(c^2 - y^2) x
    delta_max  = (5/24)(q l^4 / EI) [1 + (12 c^2 / 5 l^2)(4/5 + nu/2)]

Puntos de comparacion (PDF):
    A: (0, 0.6)       sigma_x_anal = 127.854 kg/cm^2,  sigma_x_SAP = 127.851
    B: (-4.5, -0.3)   sigma_x_anal = -37.326,           sigma_x_SAP = -37.264
    C: (-3.5, -0.2)   sigma_x_anal = -31.799,           sigma_x_SAP = -31.785

Unidades internas: SI (Pa, m, N/m). Conversion solo al reportar:
    1 kgf/cm^2 = 98066.5 Pa
    1 cm = 0.01 m
    1 kgf/m = 9.80665 N/m

Outputs:
  docs/vyv/datos/timoshenko_stress.csv
  docs/vyv/datos/timoshenko_disp.csv
  docs/vyv/datos/timoshenko_deflexion.csv
  docs/vyv/figuras/timoshenko_sigma_x_contour.png
  docs/vyv/figuras/timoshenko_perfil_x0.png
  docs/vyv/figuras/timoshenko_deformada.png

Ejecutar: python -m tests.vv_timoshenko
"""

import csv
import math
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q9
from fem.probe_query import (
    compute_smooth, displacement_at, locate_point,
)
from fem.solver import solve_system
from fem.stress import compute_all_stresses
from models.material import Material
from models.mesh_utils import generate_structured_quad_mesh


# ─── Constantes ─────────────────────────────────────────────────────────────

# Geometria (m)
L_TOTAL = 14.0
H = 1.20
B_THICKNESS = 0.40
C = H / 2.0
L_HALF = L_TOTAL / 2.0
I_VIGA = B_THICKNESS * H ** 3 / 12.0   # = 0.0576 m^4

# Material (SI)
KGF_CM2_TO_PA = 98066.5
KGF_M_TO_N_M = 9.80665
E_PA = 217370.0 * KGF_CM2_TO_PA       # ≈ 2.1318e10 Pa
NU = 0.2

# Carga distribuida (N/m, positiva hacia -y)
Q_KGF_M = 5000.0
Q_NM = Q_KGF_M * KGF_M_TO_N_M         # ≈ 49033.25 N/m

# Resolucion de malla
NX = 56
NY = 8


# ─── Soluciones analiticas ──────────────────────────────────────────────────

def sigma_x_analitico(x, y):
    """Pa. q en N/m, I en m^4, x,y,c,l en m."""
    return (Q_NM / (2 * I_VIGA)) * (L_HALF ** 2 - x ** 2) * y + \
           (Q_NM / (2 * I_VIGA)) * ((2.0 / 3.0) * y ** 3 - (2.0 / 5.0) * C ** 2 * y)


def sigma_y_analitico(x, y):
    return -(Q_NM / (2 * I_VIGA)) * (
        (1.0 / 3.0) * y ** 3 - C ** 2 * y + (2.0 / 3.0) * C ** 3
    )


def tau_xy_analitico(x, y):
    return -(Q_NM / (2 * I_VIGA)) * (C ** 2 - y ** 2) * x


def delta_max_analitico():
    """Maxima deflexion en el centro con correccion de cortante (m)."""
    base = (5.0 / 24.0) * (Q_NM * L_HALF ** 4) / (E_PA * I_VIGA)
    correction = 1.0 + (12.0 * C ** 2 / (5.0 * L_HALF ** 2)) * (4.0 / 5.0 + NU / 2.0)
    return base * correction


# ─── Datos SAP2000 (extraidos del PDF) ──────────────────────────────────────

SAP_DATA = {
    "A": {"x": 0.0,  "y": 0.6,  "sigma_x_kgcm2": 127.851, "sigma_y_kgcm2": -0.079029,
          "tau_xy_kgcm2": 0.0,        "u_cm":  0.0,     "v_cm": 2.0231},
    "B": {"x": -4.5, "y": -0.3, "sigma_x_kgcm2": -37.264, "sigma_y_kgcm2": -1.018163,
          "tau_xy_kgcm2": -5.281799,  "u_cm":  0.1133,  "v_cm": 1.0926},
    "C": {"x": -3.5, "y": -0.2, "sigma_x_kgcm2": -31.785, "sigma_y_kgcm2": -0.905408,
          "tau_xy_kgcm2": -4.877354,  "u_cm":  0.0624,  "v_cm": 1.4453},
}


# ─── Driver ─────────────────────────────────────────────────────────────────

def build_project():
    project = generate_structured_quad_mesh(
        corners=[(-L_HALF, -C), (L_HALF, -C), (L_HALF, C), (-L_HALF, C)],
        nx=NX, ny=NY, element_type=ELEMENT_Q9,
        material_name="Hormigon",
        thickness=B_THICKNESS,
        analysis_type=ANALYSIS_PLANE_STRESS,
    )
    project.materials["Hormigon"] = Material(
        name="Hormigon", E=E_PA, nu=NU, density=2400.0,
    )

    # BCs: apoyo fijo en (-L_HALF, 0), rodillo en (+L_HALF, 0)
    tol = 1e-6
    left_pin = None
    right_roller = None
    for nid, node in project.nodes.items():
        if abs(node.y) < tol:
            if abs(node.x - (-L_HALF)) < tol:
                left_pin = nid
            elif abs(node.x - L_HALF) < tol:
                right_roller = nid
    if left_pin is None or right_roller is None:
        raise RuntimeError("No se encontraron los nodos de apoyo en y=0.")
    project.set_boundary_condition(left_pin, True, True)         # pin
    project.set_boundary_condition(right_roller, False, True)    # roller

    # Surface loads sobre el borde superior. Iterar por elementos cuya arista
    # (N4=NW -> N3=NE) este en y=+C. Con (node_start=N4, node_end=N3) y q>0,
    # la carga apunta en direccion de la normal "exterior" calculada que aqui
    # es (0,-1) (porque el tangente N4->N3 = +x), o sea, hacia abajo.
    y_top = +C
    for elem in project.elements.values():
        n3 = project.nodes[elem.node_ids[2]]   # NE corner macro
        n4 = project.nodes[elem.node_ids[3]]   # NW corner macro
        if abs(n3.y - y_top) > tol or abs(n4.y - y_top) > tol:
            continue
        project.add_surface_load(
            node_start=elem.node_ids[3],   # NW
            node_end=elem.node_ids[2],     # NE
            q_start=Q_NM, q_end=Q_NM,
            angle=0.0,
            element_id=elem.id,
        )

    return project


def probe_at(project, sol, nodal_stresses, x, y):
    """Devuelve (sigma_x, sigma_y, tau_xy, ux, uy) en Pa y m."""
    loc = locate_point(project, x, y)
    if loc is None:
        return None
    eid, xi, eta = loc
    s = compute_smooth(project, sol, nodal_stresses, eid, xi, eta)
    u, v = displacement_at(project, sol, eid, xi, eta)
    return {
        "sigma_x": s["sigma_x"],
        "sigma_y": s["sigma_y"],
        "tau_xy": s["tau_xy"],
        "u": u,
        "v": v,
    }


def pa_to_kgcm2(p):
    return p / KGF_CM2_TO_PA


def m_to_cm(m):
    return m * 100.0


def save_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def plot_sigma_x_contour(project, sol, nodal_stresses, out_path):
    coords = np.array(
        [[n.x, n.y] for n in project.nodes.values()], dtype=float
    )
    node_ids = list(project.nodes.keys())
    nid_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    # Stress nodal medio (suavizado) en kg/cm^2
    sx_vals = np.zeros(len(node_ids))
    for nid in node_ids:
        ns = nodal_stresses.get(nid)
        if ns is not None:
            sx_vals[nid_to_idx[nid]] = pa_to_kgcm2(ns["sigma_x"])

    # Triangulacion sobre corners de elementos (ignoramos mid-nodes para tri)
    tris = []
    for elem in project.elements.values():
        i1 = nid_to_idx[elem.node_ids[0]]
        i2 = nid_to_idx[elem.node_ids[1]]
        i3 = nid_to_idx[elem.node_ids[2]]
        i4 = nid_to_idx[elem.node_ids[3]]
        tris.append([i1, i2, i3])
        tris.append([i1, i3, i4])
    triang = Triangulation(coords[:, 0], coords[:, 1], np.array(tris))

    fig, ax = plt.subplots(figsize=(11, 3))
    levels = 25
    cs = ax.tricontourf(triang, sx_vals, levels=levels, cmap="coolwarm")
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(r"Contorno $\sigma_x$ [kg/cm$^2$] - viga Timoshenko, FEM Q9 56x8")
    plt.colorbar(cs, ax=ax, label=r"$\sigma_x$ [kg/cm$^2$]")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_perfil_x0(project, sol, nodal_stresses, out_path):
    """Perfil sigma_x(y) en x=0: FEM (suavizado) vs analitico.

    Se grafica todo en convencion PDF (eje y hacia ABAJO). Para el FEM:
    se prueba el punto fisico equivalente (y_fem = -y_pdf) y se reporta el
    sigma_x medido (invariante al cambio de convencion) frente a y_pdf.
    """
    n_pts = 41
    ys_pdf = np.linspace(-C, C, n_pts)
    sigma_fem = []
    sigma_anal = []
    for y_pdf in ys_pdf:
        y_fem = -y_pdf
        result = probe_at(project, sol, nodal_stresses, 0.0, y_fem)
        if result is None:
            sigma_fem.append(np.nan)
        else:
            sigma_fem.append(pa_to_kgcm2(result["sigma_x"]))
        sigma_anal.append(pa_to_kgcm2(sigma_x_analitico(0.0, y_pdf)))

    fig, ax = plt.subplots(figsize=(5, 6))
    ax.plot(sigma_anal, ys_pdf, "-", color="#0d6efd",
            label="Analitico (Timoshenko)", linewidth=2)
    ax.plot(sigma_fem, ys_pdf, "o--", color="#fd7e14", markersize=5,
            label="FEM Q9 56x8")
    ax.axhline(0, color="gray", linewidth=0.6, linestyle=":")
    ax.axvline(0, color="gray", linewidth=0.6, linestyle=":")
    ax.set_xlabel(r"$\sigma_x$ [kg/cm$^2$]")
    ax.set_ylabel("y [m] (convencion PDF, eje hacia abajo)")
    ax.set_title(r"Perfil $\sigma_x(y)$ en $x=0$")
    ax.invert_yaxis()  # convencion PDF: y aumenta hacia abajo
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_deformada(project, sol, out_path, scale=20.0):
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

    fig, ax = plt.subplots(figsize=(11, 3))
    # Dibujar elementos como poligonos
    for elem in project.elements.values():
        ids = elem.node_ids[:4]
        idx = [node_ids.index(nid) for nid in ids]
        poly_o = np.vstack([coords[idx], coords[idx[0]]])
        poly_d = np.vstack([deformed[idx], deformed[idx[0]]])
        ax.plot(poly_o[:, 0], poly_o[:, 1], color="#666", linewidth=0.4)
        ax.plot(poly_d[:, 0], poly_d[:, 1], color="#198754", linewidth=0.6)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(f"Malla original (gris) vs deformada (verde, ×{scale:.0f})")
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

    print("=" * 70)
    print(f"  Timoshenko: viga simple apoyada Q9 {NX}x{NY}")
    print("=" * 70)

    project = build_project()
    print(f"Nodos: {project.num_nodes}, Elementos: {project.num_elements}, "
          f"GDL: {project.total_dof}")

    sol = solve_system(project)
    _, nodal_stresses = compute_all_stresses(project, sol)

    # Probe en A, B, C.
    # Convencion: el PDF y la solucion analitica Timoshenko-Goodier usan eje y
    # apuntando hacia ABAJO. Mi malla FEM usa eje y apuntando hacia ARRIBA
    # (convencion estandar matematica). Para localizar el mismo punto fisico,
    # uso y_fem = -y_pdf. Al comparar tau_xy y v (componentes que cambian
    # signo bajo reflexion en y), invierto el signo del FEM antes de mostrar.
    print("\n--- Tensiones en A, B, C [kg/cm^2] (coordenadas en conv. PDF) ---")
    print(f"{'Pt':>3}  {'x':>6} {'y':>6}  {'sx_FEM':>10} {'sx_anal':>10} "
          f"{'sx_SAP':>10}  {'%err_anal':>10} {'%err_SAP':>10}")

    rows_stress = []
    rows_disp = []
    for pt_name, pt_data in SAP_DATA.items():
        x_pdf, y_pdf = pt_data["x"], pt_data["y"]
        # Punto FEM equivalente
        x_fem, y_fem = x_pdf, -y_pdf
        result = probe_at(project, sol, nodal_stresses, x_fem, y_fem)
        if result is None:
            print(f"  {pt_name}: punto fuera de malla")
            continue
        # Conversion FEM -> convencion PDF:
        #   sigma_x, sigma_y: invariantes (escalares del tensor en su diagonal)
        #   tau_xy: cambia signo bajo reflexion en y
        #   u: invariante.  v: cambia signo
        sx_fem = pa_to_kgcm2(result["sigma_x"])
        sy_fem = pa_to_kgcm2(result["sigma_y"])
        txy_fem = -pa_to_kgcm2(result["tau_xy"])   # flip signo
        u_fem = m_to_cm(result["u"])
        v_fem = -m_to_cm(result["v"])              # flip signo
        sx_anal = pa_to_kgcm2(sigma_x_analitico(x_pdf, y_pdf))
        sy_anal = pa_to_kgcm2(sigma_y_analitico(x_pdf, y_pdf))
        txy_anal = pa_to_kgcm2(tau_xy_analitico(x_pdf, y_pdf))
        sx_sap = pt_data["sigma_x_kgcm2"]
        err_anal_pct = 100 * abs(sx_fem - sx_anal) / max(abs(sx_anal), 1e-12)
        err_sap_pct = 100 * abs(sx_fem - sx_sap) / max(abs(sx_sap), 1e-12)
        print(f"  {pt_name:>3}  {x_pdf:>6.2f} {y_pdf:>6.2f}  "
              f"{sx_fem:>10.3f} {sx_anal:>10.3f} {sx_sap:>10.3f}  "
              f"{err_anal_pct:>9.3f}% {err_sap_pct:>9.3f}%")

        rows_stress.append([
            pt_name, x_pdf, y_pdf,
            f"{sx_fem:.4f}", f"{sx_anal:.4f}", f"{sx_sap:.4f}",
            f"{err_anal_pct:.4f}", f"{err_sap_pct:.4f}",
            f"{sy_fem:.4f}", f"{sy_anal:.4f}", f"{pt_data['sigma_y_kgcm2']:.4f}",
            f"{txy_fem:.4f}", f"{txy_anal:.4f}", f"{pt_data['tau_xy_kgcm2']:.4f}",
        ])
        rows_disp.append([
            pt_name, x_pdf, y_pdf,
            f"{u_fem:.5f}", f"{pt_data['u_cm']:.5f}",
            f"{v_fem:.5f}", f"{pt_data['v_cm']:.5f}",
            f"{100*abs(v_fem - pt_data['v_cm'])/max(abs(pt_data['v_cm']),1e-12):.4f}",
        ])

    # Deflexion maxima en el centro y=0, x=0. En cualquier convencion (0,0)
    # es el mismo punto fisico. La deflexion FEM v sale negativa (-y en mi
    # convencion); la analitica/PDF la reporta positiva (+y hacia abajo en
    # PDF). Comparo |v_fem| con delta_anal.
    result_center = probe_at(project, sol, nodal_stresses, 0.0, 0.0)
    v_center_m = result_center["v"] if result_center else 0.0
    v_center_cm = -m_to_cm(v_center_m)             # flip a convencion PDF
    delta_anal_cm = m_to_cm(delta_max_analitico())
    err_pct = 100 * abs(v_center_cm - delta_anal_cm) / max(abs(delta_anal_cm), 1e-12)
    print(f"\n--- Deflexion maxima |v|(0,0) ---")
    print(f"  FEM    : {v_center_cm:>8.4f} cm")
    print(f"  Analit.: {delta_anal_cm:>8.4f} cm (con correccion de cortante)")
    print(f"  Error  : {err_pct:.3f}%")

    rows_defl = [[
        "v(0,0)",
        f"{v_center_cm:.5f}",
        f"{delta_anal_cm:.5f}",
        f"{err_pct:.4f}",
    ]]

    # CSVs
    save_csv(
        os.path.join(datos_dir, "timoshenko_stress.csv"),
        ["punto", "x", "y",
         "sigma_x_fem_kgcm2", "sigma_x_anal_kgcm2", "sigma_x_sap_kgcm2",
         "err_anal_pct", "err_sap_pct",
         "sigma_y_fem_kgcm2", "sigma_y_anal_kgcm2", "sigma_y_sap_kgcm2",
         "tau_xy_fem_kgcm2", "tau_xy_anal_kgcm2", "tau_xy_sap_kgcm2"],
        rows_stress,
    )
    save_csv(
        os.path.join(datos_dir, "timoshenko_disp.csv"),
        ["punto", "x", "y",
         "u_fem_cm", "u_sap_cm", "v_fem_cm", "v_sap_cm", "err_v_vs_sap_pct"],
        rows_disp,
    )
    save_csv(
        os.path.join(datos_dir, "timoshenko_deflexion.csv"),
        ["medicion", "v_fem_cm", "v_anal_cm", "err_pct"],
        rows_defl,
    )

    # Figuras
    plot_sigma_x_contour(
        project, sol, nodal_stresses,
        os.path.join(figs_dir, "timoshenko_sigma_x_contour.png"))
    plot_perfil_x0(
        project, sol, nodal_stresses,
        os.path.join(figs_dir, "timoshenko_perfil_x0.png"))
    plot_deformada(
        project, sol,
        os.path.join(figs_dir, "timoshenko_deformada.png"))

    print(f"\nOutputs en {out_dir}")

    # ─── Verificacion automatica de regresion ──────────────────────────────
    # La deflexion central FEM debe coincidir con la analitica (Timoshenko con
    # correccion de cortante) dentro de tolerancia. Antes solo se imprimia.
    checks = [
        ("Timoshenko: probe central (0,0) dentro de malla",
         result_center is not None),
        (f"Timoshenko: deflexion central converge a la analitica "
         f"(err={err_pct:.2f}% < 3%)", err_pct < 3.0),
    ]
    failed = [n for n, ok in checks if not ok]
    print("\n--- Verificacion ---")
    for name, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
