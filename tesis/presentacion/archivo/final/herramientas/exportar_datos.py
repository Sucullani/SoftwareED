# -*- coding: utf-8 -*-
"""
exportar_datos.py -- Datos reales del motor de EduFEM para la presentacion interactiva.

Corre el MISMO motor que distribuye el software (fem/ + models/) sobre los casos de la
tesis y vuelca todo lo que las animaciones necesitan en un solo archivo JavaScript:

    tesis/presentacion/final/assets/data/datos_edufem.js   ->   window.EDUFEM_DATOS = {...}

Es un .js y no un .json porque la presentacion se abre con doble clic (file://), donde
el navegador no deja leer archivos con fetch(); un <script src> si funciona.

Que exporta:
  canonico    ejemplo canonico de la tesis (9 nodos, 4 Q4, P = 1000 en el nodo 7):
              por elemento y por punto de Gauss N, dN, J, det J, J^-1, B; D; k_e; K global
              18x18; F; u; reacciones; tensiones en Gauss, extrapoladas y promediadas;
              matriz de extrapolacion E correcta y la de la numeracion equivocada
              (el defecto de la seccion 3.7.2) con las tensiones nodales que produce.
  canonico_q9 la misma malla expandida a Q9 (ciclo Q4 -> Q9 -> Q4).
  cook        membrana de Cook, Q4 y Q9, N = 2, 4, 8, 16, 32: malla, u, von Mises.
  timoshenko  viga Q9 56x8: malla, u (cm), sigma (kgf/cm2); perfiles en A y B.
  mms         tablas de convergencia de las 4 configuraciones (docs/vyv/datos/*.csv)
              y campo de error por elemento sobre la malla distorsionada.
  gauss       rigidez de un elemento cuadrado con 1x1, 2x2 y 3x3 puntos: autovalores y
              energia de los modos de cuerpo rigido y de reloj de arena (hourglass).

Uso (Windows, desde la raiz del repositorio):
    .venv\\Scripts\\python.exe tesis\\presentacion\\final\\herramientas\\exportar_datos.py
"""
from __future__ import annotations

import csv
import datetime
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FINAL, "..", "..", ".."))
sys.path.insert(0, ROOT)

SALIDA = os.path.join(FINAL, "assets", "data", "datos_edufem.js")


# ---------------------------------------------------------------- redondeo
def r(x, sig=6):
    """Redondea a `sig` cifras significativas; -0 -> 0."""
    x = float(x)
    if not math.isfinite(x):
        return None
    if x == 0.0:
        return 0
    y = float(f"{x:.{sig}g}")
    return 0 if y == 0 else y


def arr(a, sig=6):
    a = np.asarray(a, dtype=float)
    if a.ndim == 0:
        return r(a, sig)
    return [arr(v, sig) for v in a]


def lim_ruido(M, rel=1e-12):
    """Pone a cero el ruido de redondeo (lo que la teoria dice que vale 0)."""
    M = np.array(M, dtype=float)
    tope = np.max(np.abs(M)) if M.size else 0.0
    M[np.abs(M) < rel * max(tope, 1e-300)] = 0.0
    return M


# ---------------------------------------------------------------- utilidades de malla
def malla_de(project):
    """Nodos (lista [x, y]) e indices de conectividad en el orden del node_index_map."""
    idx = project.node_index_map
    orden = sorted(idx, key=lambda nid: idx[nid])
    nodos = [[project.nodes[n].x, project.nodes[n].y] for n in orden]
    elems = [[idx[n] for n in e.node_ids] for _, e in sorted(project.elements.items())]
    return orden, nodos, elems


def campo_nodal(project, nodal_avg, clave):
    idx = project.node_index_map
    v = [0.0] * len(idx)
    for nid, d in nodal_avg.items():
        v[idx[nid]] = float(d.get(clave, 0.0))
    return v


# ---------------------------------------------------------------- ejemplo canonico
def exportar_canonico():
    from models.example_library import load_example_project, load_example_project_q9
    from fem.solver import solve_system
    from fem.stress import compute_all_stresses, extrapolation_matrix
    from fem.constitutive import constitutive_matrix
    from fem.shape_functions import get_shape_functions
    from fem.jacobian import compute_jacobian, compute_dN_physical
    from fem.b_matrix import compute_b_matrix
    from fem.gauss_quadrature import get_gauss_points_for_element

    project = load_example_project()
    sol = solve_system(project)
    elem_st, nodal_avg = compute_all_stresses(project, sol)

    mat = next(iter(project.materials.values()))
    E, nu, t = float(mat.E), float(mat.nu), float(project.default_thickness)
    D = constitutive_matrix(E, nu, project.analysis_type)
    N_fn, dN_fn = get_shape_functions(project.element_type)
    gpts, gwts = get_gauss_points_for_element(project.element_type)

    u = np.asarray(sol["u"], dtype=float)
    K = sol["K"]
    K = K.toarray() if hasattr(K, "toarray") else np.asarray(K, dtype=float)
    F = np.asarray(sol["F"], dtype=float)
    R = np.asarray(sol["reactions"], dtype=float)
    edata = sol["element_data"]
    idx = project.node_index_map

    Eex = extrapolation_matrix(4)
    # El defecto que delato la memoria de calculo (seccion 3.7.2): la matriz estaba
    # escrita para otra numeracion de los puntos de Gauss -- las columnas de los
    # puntos 3 y 4 intercambiadas respecto del orden que produce el motor.
    Eex_mal = Eex[:, [0, 1, 3, 2]]
    M_interp = np.array([N_fn(xi, eta) for (xi, eta) in gpts])  # sigma_g = M sigma_n

    elementos = {}
    energia = {}
    acum_bien = {nid: np.zeros(3) for nid in project.nodes}
    acum_mal = {nid: np.zeros(3) for nid in project.nodes}
    cuenta = {nid: 0 for nid in project.nodes}

    for eid, elem in sorted(project.elements.items()):
        nids = list(elem.node_ids)
        X = np.array([[project.nodes[n].x, project.nodes[n].y] for n in nids])
        dofs = list(edata[eid]["dof_indices"])
        ke = np.asarray(edata[eid]["ke"], dtype=float)
        ue = u[dofs]
        energia[eid] = 0.5 * float(ue @ ke @ ue)
        gs = elem_st[eid]["gauss_stresses"]
        ns = elem_st[eid]["nodal_stresses"]
        puntos = []
        for k, ((xi, eta), w) in enumerate(zip(gpts, gwts)):
            dN = dN_fn(xi, eta)
            J, detJ, invJ = compute_jacobian(dN, X)
            dNf = compute_dN_physical(dN, invJ)
            B = compute_b_matrix(dNf)
            eps = B @ ue
            sig = D @ eps
            contrib = B.T @ D @ B * abs(detJ) * t * w
            puntos.append({
                "xi": r(xi, 12), "eta": r(eta, 12), "w": r(w, 12),
                "x": arr(N_fn(xi, eta) @ X, 8),
                "N": arr(N_fn(xi, eta), 10),
                "dN": arr(dN, 10), "J": arr(J, 10), "detJ": r(detJ, 10),
                "invJ": arr(invJ, 10), "dNf": arr(dNf, 10), "B": arr(B, 10),
                "eps": arr(eps, 8), "sigma": arr(sig, 8),
                "vm": r(gs[k]["von_mises"], 8),
                "aporte": arr(lim_ruido(contrib), 8),
            })
        sg = np.array([[g["sigma_x"], g["sigma_y"], g["tau_xy"]] for g in gs])
        sn_bien = Eex @ sg
        sn_mal = Eex_mal @ sg
        for j, nid in enumerate(nids):
            acum_bien[nid] += sn_bien[j]
            acum_mal[nid] += sn_mal[j]
            cuenta[nid] += 1
        elementos[str(eid)] = {
            "nodos": nids, "X": arr(X, 10), "dofs": dofs,
            "gauss": puntos, "ke": arr(lim_ruido(ke), 8), "ue": arr(ue, 10),
            "energia": r(energia[eid], 8),
            "sigma_gauss": arr(sg, 8),
            "sigma_nodal": [[r(d["sigma_x"], 8), r(d["sigma_y"], 8), r(d["tau_xy"], 8),
                             r(d["von_mises"], 8)] for d in ns],
            "sigma_nodal_mal": arr(sn_mal, 8),
            # Cierre de la extrapolacion: volver a interpolar los valores nodales en los
            # puntos de Gauss. Con la E correcta reproduce sigma_gauss; con la mal escrita, no.
            "cierre_bien": arr(M_interp @ sn_bien, 8),
            "cierre_mal": arr(M_interp @ sn_mal, 8),
        }

    def vm_de(s):
        sx, sy, txy = s
        c = 0.5 * (sx + sy)
        rr = math.hypot(0.5 * (sx - sy), txy)
        s1, s2 = c + rr, c - rr
        return math.sqrt(s1 * s1 - s1 * s2 + s2 * s2)

    nodal = {}
    for nid in sorted(project.nodes):
        d = nodal_avg[nid]
        mal = acum_mal[nid] / max(cuenta[nid], 1)
        nodal[str(nid)] = {
            "sx": r(d["sigma_x"], 8), "sy": r(d["sigma_y"], 8), "txy": r(d["tau_xy"], 8),
            "s1": r(d["sigma_1"], 8), "s2": r(d["sigma_2"], 8), "vm": r(d["von_mises"], 8),
            "mal": arr(list(mal) + [vm_de(mal)], 8),
            "elementos": [e for e, el in sorted(project.elements.items()) if nid in el.node_ids],
        }

    show = max(energia, key=energia.get)
    nodos = [{"id": nid, "x": project.nodes[nid].x, "y": project.nodes[nid].y,
              "i": idx[nid]} for nid in sorted(project.nodes)]
    apoyos = sorted(project.boundary_conditions)
    Kd = lim_ruido(K)

    # Variante Q9 (ciclo Q4 -> Q9 -> Q4 de la seccion 3.3)
    p9 = load_example_project_q9()
    orden9, nodos9, elems9 = malla_de(p9)

    return {
        "E": E, "nu": nu, "t": t, "P": 1000.0, "tipo": "Tensión plana",
        "nodos": nodos,
        "elementos_conect": {str(e): list(el.node_ids) for e, el in sorted(project.elements.items())},
        "apoyos": apoyos,
        "carga": {"nodo": 7, "Fx": 0.0, "Fy": -1000.0},
        "D": arr(D, 10), "D_factor": r(E / (1 - nu * nu), 10),
        "gauss_pts": [[r(a, 12), r(b, 12)] for a, b in gpts],
        "gauss_w": [r(w, 12) for w in gwts],
        "elementos": elementos,
        "K": arr(Kd, 8), "F": arr(F, 8),
        "libres": [int(d) for d in sol["free_dofs"]],
        "restringidos": [int(d) for d in sol["restrained_dofs"]],
        "u": arr(u, 10), "R": arr(lim_ruido(R, 1e-9), 8),
        "nodal": nodal,
        "E_extrap": arr(Eex, 10), "E_extrap_mal": arr(Eex_mal, 10),
        "M_interp": arr(M_interp, 10),
        "showcase": show,
        "q9": {"ids": orden9, "nodos": arr(nodos9, 8), "elems": elems9},
    }


# ---------------------------------------------------------------- membrana de Cook
def exportar_cook():
    from tests import vv_cook
    from config.settings import ELEMENT_Q4, ELEMENT_Q9
    from fem.stress import compute_all_stresses

    casos = {}
    for et, nombre in ((ELEMENT_Q4, "Q4"), (ELEMENT_Q9, "Q9")):
        casos[nombre] = {}
        for N in (2, 4, 8, 16, 32):
            res = vv_cook.run_case(N, et)
            project, sol = res["project"], res["sol"]
            _, nodal_avg = compute_all_stresses(project, sol)
            orden, nodos, elems = malla_de(project)
            u = np.asarray(sol["u"], dtype=float).reshape(-1, 2)
            vm = campo_nodal(project, nodal_avg, "von_mises")
            empotrados = [i for i, (x, y) in enumerate(nodos) if abs(x) < 1e-9]
            casos[nombre][str(N)] = {
                "N": N, "gdl": int(project.total_dof),
                "uy": r(res["uy"], 8), "ux": r(res["ux"], 8),
                "error": r(100.0 * (res["uy"] - vv_cook.U_Y_REF) / vv_cook.U_Y_REF, 6),
                "nodos": arr(nodos, 7), "elems": elems,
                "u": arr(u, 6), "vm": arr(vm, 5),
                "empotrados": empotrados,
            }
            print(f"  Cook {nombre} N={N:2d}: uy={res['uy']:.5f}  gdl={project.total_dof}")
    return {
        "esquinas": vv_cook.CORNERS, "ref": vv_cook.U_Y_REF, "ref_publicada": 23.965,
        "sonda": [vv_cook.PROBE_X, vv_cook.PROBE_Y],
        # Stembera y Fussl (2019), p. 28: Q4 de cuatro nodos, mismo problema y refinamiento
        "stembera_q4": [11.845, 18.299, 22.079, 23.430, 23.818],
        "casos": casos,
    }


# ---------------------------------------------------------------- viga de Timoshenko
def exportar_timoshenko():
    from tests import vv_timoshenko as vt
    from fem.solver import solve_system
    from fem.stress import compute_all_stresses

    project = vt.build_project()
    sol = solve_system(project)
    _, nodal_avg = compute_all_stresses(project, sol)
    orden, nodos, elems = malla_de(project)
    u = np.asarray(sol["u"], dtype=float).reshape(-1, 2) * 100.0      # m -> cm
    pa = vt.KGF_CM2_TO_PA
    sx = [v / pa for v in campo_nodal(project, nodal_avg, "sigma_x")]
    sy = [v / pa for v in campo_nodal(project, nodal_avg, "sigma_y")]
    txy = [v / pa for v in campo_nodal(project, nodal_avg, "tau_xy")]
    vm = [v / pa for v in campo_nodal(project, nodal_avg, "von_mises")]

    # Perfiles de sigma_x en el peralte: FEM (nodos de la seccion) frente a la analitica.
    # Marco de la malla: y hacia arriba. La analitica se escribe en el de Timoshenko-Goodier
    # (y hacia la fibra traccionada = hacia abajo): y_ref = -y_fem.
    perfiles = {}
    for nombre, xs in (("A", 0.0), ("B", -4.5)):
        cand = [(i, p) for i, p in enumerate(nodos) if abs(p[0] - xs) < 1e-9]
        cand.sort(key=lambda ip: ip[1][1])
        ys = [p[1] for _, p in cand]
        fem = [sx[i] for i, _ in cand]
        yy = np.linspace(-vt.C, vt.C, 61)
        anal = [vt.sigma_x_analitico(xs, -y) / pa for y in yy]
        perfiles[nombre] = {"x": xs, "y_fem": arr(ys, 6), "sx_fem": arr(fem, 7),
                            "y_anal": arr(yy, 6), "sx_anal": arr(anal, 7)}

    apoyos = []
    for nid, bc in project.boundary_conditions.items():
        i = project.node_index_map[nid]
        apoyos.append({"i": i, "tipo": "fijo" if (bc.restrain_x and bc.restrain_y) else "movil"}
                      if hasattr(bc, "restrain_x") else {"i": i})

    def leer(nombre):
        with open(os.path.join(ROOT, "docs", "vyv", "datos", nombre), encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    print(f"  Timoshenko Q9 56x8: {project.num_nodes} nodos, {project.total_dof} GDL")
    return {
        "L": vt.L_TOTAL, "H": vt.H, "b": vt.B_THICKNESS, "E_kgfcm2": 217370.0, "nu": vt.NU,
        "q_kgfm": vt.Q_KGF_M, "nx": vt.NX, "ny": vt.NY,
        "nodos_n": project.num_nodes, "elementos_n": project.num_elements,
        "gdl": int(project.total_dof),
        "nodos": arr(nodos, 7), "elems": elems, "u": arr(u, 6),
        "sx": arr(sx, 6), "sy": arr(sy, 6), "txy": arr(txy, 6), "vm": arr(vm, 6),
        "apoyos": apoyos, "perfiles": perfiles,
        "csv_tensiones": leer("timoshenko_stress.csv"),
        "csv_desplaz": leer("timoshenko_disp.csv"),
        "csv_flecha": leer("timoshenko_deflexion.csv"),
        "csv_equilibrio": leer("timoshenko_equilibrio.csv"),
    }


# ---------------------------------------------------------------- MMS
def exportar_mms():
    from tests import vv_mms
    from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q4, ELEMENT_Q9
    from fem.shape_functions import get_shape_functions
    from fem.gauss_quadrature import get_gauss_points_2d

    tablas = {}
    datos = os.path.join(ROOT, "docs", "vyv", "datos")
    for cfg in ("unif_tp", "dist_tp", "unif_dp", "dist_dp"):
        tablas[cfg] = {}
        for el in ("q4", "q9"):
            nombre = f"mms_{el}.csv" if cfg == "unif_tp" else f"mms_{el}_{cfg}.csv"
            with open(os.path.join(datos, nombre), encoding="utf-8") as fh:
                filas = list(csv.DictReader(fh))
            tablas[cfg][el.upper()] = [{
                "N": int(f["N"]), "h": float(f["h"]), "gdl": int(f["ndof"]),
                "L2": float(f["L2_disp"]), "H1": float(f["H1_semi"]),
                "S": float(f["L2_stress"]),
                "tL2": float(f["rate_L2"]) if f["rate_L2"] else None,
                "tH1": float(f["rate_H1"]) if f["rate_H1"] else None,
                "tS": float(f["rate_stress"]) if f["rate_stress"] else None,
            } for f in filas]

    # Campo de error del desplazamiento por elemento, malla distorsionada en tension plana.
    campos = {}
    for et, nombre, Ns in ((ELEMENT_Q4, "Q4", (2, 4, 8, 16)), (ELEMENT_Q9, "Q9", (2, 4, 8))):
        N_fn, dN_fn = get_shape_functions(et)
        pts, wts = get_gauss_points_2d(3 if nombre == "Q4" else 4)
        campos[nombre] = {}
        for N in Ns:
            project, sol, norms = vv_mms.run_case(N, et, corners=vv_mms.CORNERS_DIST,
                                                  analysis_type=ANALYSIS_PLANE_STRESS)
            orden, nodos, elems = malla_de(project)
            u = np.asarray(sol["u"], dtype=float).reshape(-1, 2)
            X = np.array(nodos)
            err_e = []
            for con in elems:
                Xe, Ue = X[con], u[con]
                e2 = area = 0.0
                for (xi, eta), w in zip(pts, wts):
                    Nv = N_fn(xi, eta)
                    J = dN_fn(xi, eta) @ Xe
                    dj = abs(np.linalg.det(J))
                    xg, yg = Nv @ Xe
                    uh = Nv @ Ue
                    ue = np.array(vv_mms.u_M(xg, yg))
                    e2 += w * dj * float(np.sum((uh - ue) ** 2))
                    area += w * dj
                err_e.append(math.sqrt(e2 / area))
            campos[nombre][str(N)] = {
                "nodos": arr(nodos, 7), "elems": elems, "u": arr(u, 6),
                "err": arr(err_e, 5), "L2": r(norms.get("L2_disp", 0.0), 6),
            }
            print(f"  MMS {nombre} N={N:2d}: max err elem = {max(err_e):.3e}")
    return {"tablas": tablas, "campos": campos,
            "esquinas_dist": vv_mms.CORNERS_DIST, "esquinas_unif": vv_mms.CORNERS_UNIT}


# ---------------------------------------------------------------- cuadratura y modos espurios
def exportar_gauss():
    from config.settings import ANALYSIS_PLANE_STRESS, ELEMENT_Q4
    from fem.constitutive import constitutive_matrix
    from fem.shape_functions import get_shape_functions
    from fem.jacobian import compute_jacobian, compute_dN_physical
    from fem.b_matrix import compute_b_matrix
    from fem.gauss_quadrature import get_gauss_points_2d

    X = np.array([[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [-1.0, 1.0]])
    E, nu, t = 1.0, 0.3, 1.0
    D = constitutive_matrix(E, nu, ANALYSIS_PLANE_STRESS)
    _, dN_fn = get_shape_functions(ELEMENT_Q4)

    modos = {
        "Traslación x": [1, 0, 1, 0, 1, 0, 1, 0],
        "Traslación y": [0, 1, 0, 1, 0, 1, 0, 1],
        "Rotación": [1, -1, 1, 1, -1, 1, -1, -1],
        "Reloj de arena x": [1, 0, -1, 0, 1, 0, -1, 0],
        "Reloj de arena y": [0, 1, 0, -1, 0, 1, 0, -1],
        "Estiramiento x": [-1, 0, 1, 0, 1, 0, -1, 0],
    }
    out = {"reglas": {}, "modos": {k: v for k, v in modos.items()}}
    for n in (1, 2, 3):
        pts, wts = get_gauss_points_2d(n)
        ke = np.zeros((8, 8))
        for (xi, eta), w in zip(pts, wts):
            dN = dN_fn(xi, eta)
            J, detJ, invJ = compute_jacobian(dN, X)
            B = compute_b_matrix(compute_dN_physical(dN, invJ))
            ke += B.T @ D @ B * abs(detJ) * t * w
        lam = np.sort(np.linalg.eigvalsh(ke))
        tope = lam[-1]
        ceros = int(np.sum(np.abs(lam) < 1e-10 * tope))
        energias = {}
        for nom, v in modos.items():
            v = np.asarray(v, dtype=float)
            v = v / np.linalg.norm(v)
            energias[nom] = r(0.5 * float(v @ ke @ v), 6)
        out["reglas"][str(n)] = {
            "puntos": arr(pts, 10), "pesos": arr(wts, 10),
            "autovalores": arr(lim_ruido(lam), 6), "ceros": ceros,
            "rango": 8 - ceros, "energias": energias,
        }
        print(f"  Gauss {n}x{n}: autovalores nulos = {ceros}, rango = {8 - ceros}")
    return out


# ---------------------------------------------------------------- principal
def main():
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
    except OSError:
        rev = ""
    print("Ejemplo canonico ...")
    can = exportar_canonico()
    print("Membrana de Cook ...")
    cook = exportar_cook()
    print("Viga de Timoshenko ...")
    tim = exportar_timoshenko()
    print("Soluciones manufacturadas ...")
    mms = exportar_mms()
    print("Cuadratura y modos espurios ...")
    gau = exportar_gauss()

    datos = {
        "meta": {
            "generado": datetime.date.today().isoformat(),
            "revision_repositorio": rev,
            "version_evaluada": "EduFEM 1.0.0, revisión 91e3df0 (16 de septiembre de 2026)",
            "fuente": "Motor de EduFEM (fem/ y models/), ejecutado por herramientas/exportar_datos.py",
        },
        "canonico": can, "cook": cook, "timoshenko": tim, "mms": mms, "gauss": gau,
    }
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    # Los indices del motor son enteros de NumPy: `item()` los baja a int de Python.
    txt = json.dumps(datos, ensure_ascii=False, separators=(",", ":"),
                     default=lambda o: o.item() if hasattr(o, "item") else str(o))
    with open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write("/* Generado por herramientas/exportar_datos.py -- NO editar a mano.\n")
        fh.write("   Salida del motor de EduFEM sobre los casos de la tesis. */\n")
        fh.write("window.EDUFEM_DATOS = ")
        fh.write(txt)
        fh.write(";\n")
    print(f"\n[OK] {SALIDA}  ({os.path.getsize(SALIDA) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
