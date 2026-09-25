"""
experimento_sabotaje.py - Que errores de la matriz D detecta el MMS de EduFEM?

Introduce a proposito errores en fem.constitutive.constitutive_matrix (en
todos los modulos que la importaron por nombre) y corre el MMS con el criterio
de la tesis: tasa entre N = 16 y N = 32, |tasa - teorica| < 0,5 en L2 y H1 y
cota minima en el campo de tensiones recuperado (1,4 en Q4, 1,9 en Q9).

Parte A: la solucion manufacturada de la tesis (tests/vv_mms.py), 4 configs.
Parte B: una solucion alternativa con div(u) != 0 y gamma_xy != 0,
         u = sin(pi x) sin(pi y),  v = cos(pi x) cos(2 pi y).

Salida: datos_sabotaje.tex (en esta carpeta). Tarda unos 3 minutos.
Ejecutar:  python docs/vyv/mms_paso_a_paso/experimento_sabotaje.py
"""
import math
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, REPO)
os.chdir(REPO)

import numpy as np  # noqa: E402

import fem.batch  # noqa: E402
import fem.constitutive  # noqa: E402
import fem.probe_query  # noqa: E402
import fem.stiffness  # noqa: E402
import fem.stress  # noqa: E402
from config.settings import (ANALYSIS_PLANE_STRAIN, ANALYSIS_PLANE_STRESS,  # noqa: E402
                             ELEMENT_Q4, ELEMENT_Q9)
from fem.error_norms import compute_error_norms  # noqa: E402
from fem.solver import solve_system  # noqa: E402
from models.material import Material  # noqa: E402
from models.mesh_utils import generate_structured_quad_mesh  # noqa: E402
from tests import test_vv_extensions, vv_cook, vv_mms  # noqa: E402

ORIGINAL = fem.constitutive.constitutive_matrix
MODULOS = (fem.constitutive, fem.batch, fem.probe_query, fem.stiffness, fem.stress)
PI = math.pi
E, NU = vv_mms.E_MMS, vv_mms.NU_MMS
MU = E / (2 * (1 + NU))
LAM = {ANALYSIS_PLANE_STRESS: E * NU / (1 - NU ** 2),
       ANALYSIS_PLANE_STRAIN: E * NU / ((1 + NU) * (1 - 2 * NU))}
ESPERADA = {ELEMENT_Q4: (2.0, 1.0, 1.4), ELEMENT_Q9: (3.0, 2.0, 1.9)}


def instalar(fn):
    for mod in MODULOS:
        mod.constitutive_matrix = fn


def s1_dp_devuelve_tp(E_, nu, analysis_type):
    """La rama de deformacion plana devuelve la D de tension plana."""
    return ORIGINAL(E_, nu, ANALYSIS_PLANE_STRESS)


def s2_d33_doble(E_, nu, analysis_type):
    """Confusion clasica entre gamma_xy y eps_xy: D33 duplicado."""
    D = ORIGINAL(E_, nu, analysis_type).copy()
    D[2, 2] *= 2.0
    return D


def s3_d11_d22(E_, nu, analysis_type):
    """Control: D11 = D22 un 10 % mas grandes (cambia D11 - D12)."""
    D = ORIGINAL(E_, nu, analysis_type).copy()
    D[0, 0] *= 1.1
    D[1, 1] *= 1.1
    return D


SABOTAJES = [("orig", ORIGINAL), ("sa", s1_dp_devuelve_tp), ("sb", s2_d33_doble), ("sc", s3_d11_d22)]


def tasas(n16, n32, claves):
    lh = math.log(n16["h"] / n32["h"])
    return {k: math.log(n16[k] / n32[k]) / lh for k in claves}


# --- Parte A: solucion de la tesis ----------------------------------------------
def parte_a():
    res = {}
    for clave, fn in SABOTAJES:
        instalar(fn)
        casos = []
        for _, corners, at, _ in vv_mms.CONFIGS:
            for et in (ELEMENT_Q4, ELEMENT_Q9):
                n = [vv_mms.run_case(N, et, corners=corners, analysis_type=at)[2] for N in (16, 32)]
                r = tasas(n[0], n[1], ("L2_disp", "H1_semi", "L2_stress"))
                eL, eH, eS = ESPERADA[et]
                ok = abs(r["L2_disp"] - eL) < 0.5 and abs(r["H1_semi"] - eH) < 0.5 and r["L2_stress"] >= eS
                casos.append((et, r, ok))
        res[clave] = casos
        print(f"parte A {clave}: pasan {sum(ok for _, _, ok in casos)}/8")
    instalar(ORIGINAL)
    return res


# --- Parte B: solucion alternativa ------------------------------------------------
def u_alt(x, y):
    return (math.sin(PI * x) * math.sin(PI * y), math.cos(PI * x) * math.cos(2 * PI * y))


def grad_alt(x, y):
    sx, cx = math.sin(PI * x), math.cos(PI * x)
    sy, cy = math.sin(PI * y), math.cos(PI * y)
    return np.array([[PI * cx * sy, PI * sx * cy],
                     [-PI * sx * math.cos(2 * PI * y), -2 * PI * cx * math.sin(2 * PI * y)]])


def b_alt(analysis_type):
    """b = -div(sigma) derivada a mano con las constantes de Lame del estado plano."""
    lam = LAM[analysis_type]

    def fn(x, y):
        sx, cx = math.sin(PI * x), math.cos(PI * x)
        sy, cy = math.sin(PI * y), math.cos(PI * y)
        s2y, c2y = math.sin(2 * PI * y), math.cos(2 * PI * y)
        bx = PI ** 2 * ((lam + 3 * MU) * sx * sy - 2 * (lam + MU) * sx * s2y)
        by = PI ** 2 * ((4 * lam + 9 * MU) * cx * c2y - (lam + MU) * cx * cy)
        return bx, by
    return fn


def run_alt(N, et, at):
    p = generate_structured_quad_mesh(corners=vv_mms.CORNERS_UNIT, nx=N, ny=N, element_type=et,
                                      material_name="MMS", thickness=1.0, analysis_type=at)
    p.materials["MMS"] = Material(name="MMS", E=E, nu=NU, density=0.0)
    for nid in vv_mms.boundary_nodes_topological(p):
        nodo = p.nodes[nid]
        ux, uy = u_alt(nodo.x, nodo.y)
        p.set_boundary_condition(nid, True, True, ux, uy)
    sol = solve_system(p, body_force_fn=b_alt(at))
    return compute_error_norms(p, sol, u_alt, grad_alt)


def parte_b():
    res = {}
    for clave, fn in SABOTAJES[:3]:
        instalar(fn)
        casos = []
        for at in (ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN):
            for et in (ELEMENT_Q4, ELEMENT_Q9):
                n = [run_alt(N, et, at) for N in (16, 32)]
                r = tasas(n[0], n[1], ("L2_disp", "H1_semi"))
                eL, eH, _ = ESPERADA[et]
                ok = abs(r["L2_disp"] - eL) < 0.5 and abs(r["H1_semi"] - eH) < 0.5
                casos.append((at, et, r, ok))
        res[clave] = casos
        print(f"parte B {clave}: pasan {sum(c[3] for c in casos)}/4")
    instalar(ORIGINAL)
    return res


# --- Otros tests del repositorio frente a los mismos errores ----------------------
def otros_tests():
    out = {}
    instalar(s1_dp_devuelve_tp)
    try:
        test_vv_extensions.test_von_mises_plane_strain()
        out["vmsa"] = None
    except AssertionError as exc:
        hallado = re.search(r"err rel ([0-9.eE+-]+)", str(exc))
        out["vmsa"] = float(hallado.group(1)) if hallado else float("nan")
    instalar(s2_d33_doble)
    out["cooksb"] = vv_cook.run_case(16, ELEMENT_Q9)["uy"]
    instalar(ORIGINAL)
    out["cookorig"] = vv_cook.run_case(16, ELEMENT_Q9)["uy"]
    return out


def num(x, nd=2):
    s = f"{x:.{nd}f}"
    if float(s) == 0.0:
        s = f"{0.0:.{nd}f}"
    return s.replace(".", "{,}")


def rango(valores):
    lo, hi = min(valores), max(valores)
    return f"${num(lo)}$" if num(lo) == num(hi) else f"${num(lo)}$--${num(hi)}$"


def main():
    a = parte_a()
    b = parte_b()
    otros = otros_tests()
    datos, tablas = {}, {}
    filas = []
    nombres = {"orig": "Ninguno (código original)", "sa": "Rama DP devuelve la $\\bm{D}$ de TP",
               "sb": "$D_{33}$ duplicado", "sc": "$D_{11}$ y $D_{22}$ +10\\,\\% (control)"}
    for clave, _ in SABOTAJES:
        casos = a[clave]
        celdas = []
        for et in (ELEMENT_Q4, ELEMENT_Q9):
            rs = [r for e_, r, _ in casos if e_ == et]
            celdas += [rango([r["L2_disp"] for r in rs]), rango([r["H1_semi"] for r in rs])]
        n_ok = sum(ok for _, _, ok in casos)
        filas.append(" & ".join([nombres[clave]] + celdas + [f"{n_ok}/8"]) + r" \\")
        datos[f"pasaA{clave}"] = f"{n_ok}/8"
    tablas["sabotajeA"] = "\n".join(filas)

    filas = []
    for clave, _ in SABOTAJES[:3]:
        casos = b[clave]
        celdas = []
        for at in (ANALYSIS_PLANE_STRESS, ANALYSIS_PLANE_STRAIN):
            for et in (ELEMENT_Q4, ELEMENT_Q9):
                r, ok = [(c[2], c[3]) for c in casos if c[0] == at and c[1] == et][0]
                celdas.append(f"${num(r['L2_disp'])}$ / ${num(r['H1_semi'])}$" +
                              (r" \cmark" if ok else r" \xmark"))
        filas.append(" & ".join([nombres[clave]] + celdas) + r" \\")
        datos[f"pasaB{clave}"] = f"{sum(c[3] for c in casos)}/4"
    tablas["sabotajeB"] = "\n".join(filas)

    assert otros["vmsa"] is not None, "se esperaba que test_von_mises_plane_strain detectara el error"
    datos["vmsa"] = num(100 * otros["vmsa"], 1)
    datos["cooksb"] = num(otros["cooksb"])
    datos["cookorig"] = num(otros["cookorig"])

    with open(os.path.join(AQUI, "datos_sabotaje.tex"), "w", encoding="utf-8") as fh:
        fh.write("% Generado por experimento_sabotaje.py: no editar a mano.\n")
        for clave, valor in datos.items():
            fh.write(f"\\expandafter\\def\\csname dato:{clave}\\endcsname{{{valor}}}\n")
        for clave, cuerpo in tablas.items():
            fh.write(f"\\expandafter\\def\\csname tabla:{clave}\\endcsname{{%\n{cuerpo}\n}}\n")
    print("datos_sabotaje.tex escrito:", datos)


if __name__ == "__main__":
    main()
