"""
generar_datos.py - Calcula todas las cifras del documento mms_paso_a_paso.tex.

El calculo usa solo la replica independiente (mms_independiente.py, en esta
misma carpeta) y NumPy: no importa nada de EduFEM. Al final, si el repositorio
esta disponible, contrasta las cifras con el motor de EduFEM y con
docs/vyv/datos/mms_q4.csv y mms_q9.csv, y aborta si alguna no coincide.

Salidas (en esta carpeta):
    datos.tex          macros \\dato{...} y cuerpos de tablas \\tabla{...}
    convergencia.dat   errores por malla para la figura de convergencia

Ejecutar:  python docs/vyv/mms_paso_a_paso/generar_datos.py
"""
import csv
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
sys.path.insert(0, AQUI)

import mms_independiente as R  # noqa: E402

E, NU, T, MU, D = R.E, R.NU, R.T, R.MU, R.D
PI = math.pi
C = E / (1.0 - NU ** 2)              # factor de la matriz D de tension plana
LAM = E * NU / (1.0 - NU ** 2)       # lambda* de tension plana
K2 = 2.0 * MU * PI ** 2              # b = K2 * u_M

datos = {}    # clave -> texto LaTeX (modo matematico)
tablas = {}   # clave -> filas LaTeX


# --- Formato: coma decimal, sin "-0" ----------------------------------------
def num(x, nd=6):
    s = f"{x:.{nd}f}"
    if float(s) == 0.0:
        s = f"{0.0:.{nd}f}"
    return s.replace(".", "{,}")


def sci(x, nd=6):
    if x == 0.0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    m = f"{x / 10 ** e:.{nd}f}"
    if abs(float(m)) >= 10.0:
        e += 1
        m = f"{x / 10 ** e:.{nd}f}"
    if e == 0:
        return m.replace(".", "{,}")
    return f"{m.replace('.', '{,}')}\\times10^{{{e}}}"


def exacto(x):
    """Valor prescrito sin el ruido de coma flotante (sin(pi) = 1,2e-16)."""
    r = round(x, 9)
    return str(int(r)) if r == int(r) else num(x)


def fila(*celdas):
    return " & ".join(celdas) + r" \\"


def m(x, nd=6):
    return f"${num(x, nd)}$"


# --- Constantes -----------------------------------------------------------------
datos.update({
    "E": num(E, 1), "nu": num(NU, 1), "t": num(T, 1),
    "c": num(C), "mu": num(MU), "dosmu": num(2 * MU), "lam": num(LAM),
    "K2": num(K2), "pi": num(PI), "pi2": num(PI ** 2),
    "D11": num(D[0, 0]), "D12": num(D[0, 1]), "D33": num(D[2, 2]),
    "DdifD": num(D[0, 0] - D[0, 1]),
    "bmuestra": num(K2 * 0.5),
})

# --- Caso a mano: Q4, N = 2, numeracion de EduFEM (fila por fila, desde abajo) --
NODOS = {}
for j in range(3):
    for i in range(3):
        NODOS[len(NODOS) + 1] = (0.5 * i, 0.5 * j)
ELEMS = {1: [1, 2, 5, 4], 2: [2, 3, 6, 5], 3: [4, 5, 8, 7], 4: [5, 6, 9, 8]}
LIBRE = 5
SIGNOS = [(-1, -1), (1, -1), (1, 1), (-1, 1)]       # nodos locales 1..4 del Q4
G2 = 1.0 / math.sqrt(3.0)
PG2 = [(-G2, -G2, 1.0), (G2, -G2, 1.0), (G2, G2, 1.0), (-G2, G2, 1.0)]


def N_q4(xi, eta):
    return np.array([(1 + a * xi) * (1 + c * eta) / 4 for a, c in SIGNOS])


def dN_q4(xi, eta):
    return np.array([[a * (1 + c * eta) / 4 for a, c in SIGNOS],
                     [c * (1 + a * xi) / 4 for a, c in SIGNOS]])


def geometria_q4(xy, xi, eta):
    dN = dN_q4(xi, eta)
    J = dN @ xy
    det_J = float(np.linalg.det(J))
    dNxy = np.linalg.solve(J, dN)
    B = np.zeros((3, 8))
    B[0, 0::2] = dNxy[0]
    B[1, 1::2] = dNxy[1]
    B[2, 0::2] = dNxy[1]
    B[2, 1::2] = dNxy[0]
    return J, det_J, B


def elemento(conn):
    xy = np.array([NODOS[n] for n in conn])
    ke = np.zeros((8, 8))
    fe = np.zeros(8)
    puntos = []
    for xi, eta, w in PG2:
        N = N_q4(xi, eta)
        J, det_J, B = geometria_q4(xy, xi, eta)
        ke += B.T @ D @ B * det_J * w * T
        x, y = N @ xy[:, 0], N @ xy[:, 1]
        bx, by = R.b(x, y)
        fe[0::2] += N * bx * det_J * w * T
        fe[1::2] += N * by * det_J * w * T
        puntos.append(dict(xi=xi, eta=eta, w=w, x=x, y=y, N=N, bx=bx, by=by,
                           det_J=det_J, J=J, B=B))
    return ke, fe, puntos


def gdl(conn):
    return np.ravel([[2 * (n - 1), 2 * (n - 1) + 1] for n in conn])


K = np.zeros((18, 18))
F = np.zeros(18)
por_elemento = {}
for e, conn in ELEMS.items():
    ke, fe, puntos = elemento(conn)
    K[np.ix_(gdl(conn), gdl(conn))] += ke
    F[gdl(conn)] += fe
    por_elemento[e] = (ke, fe, puntos)

ke1, _, puntos1 = por_elemento[1]
J1 = puntos1[0]["J"]
datos.update({"J11": num(J1[0, 0], 2), "detJ": num(puntos1[0]["det_J"], 4),
              "Jinv": num(1.0 / J1[0, 0], 0), "gdos": num(G2)})

# Comprobacion con las formulas cerradas del Q4 cuadrado de tension plana.
k_cerr = [0.5 - NU / 6, 0.125 + NU / 8, -0.25 - NU / 12, -0.125 + 3 * NU / 8,
          -0.25 + NU / 12, -0.125 - NU / 8, NU / 6, 0.125 - 3 * NU / 8]
PATRON = [[1, 2, 3, 4, 5, 6, 7, 8], [2, 1, 8, 7, 6, 5, 4, 3], [3, 8, 1, 6, 7, 4, 5, 2],
          [4, 7, 6, 1, 8, 3, 2, 5], [5, 6, 7, 8, 1, 2, 3, 4], [6, 5, 4, 3, 2, 1, 8, 7],
          [7, 4, 5, 2, 3, 8, 1, 6], [8, 3, 2, 5, 4, 7, 6, 1]]
ke_cerrada = C * np.array([[k_cerr[i - 1] for i in r] for r in PATRON])
assert np.allclose(ke1, ke_cerrada, atol=1e-14), "ke no coincide con la forma cerrada"
for i, k in enumerate(k_cerr, start=1):
    datos[f"k{i}"] = num(k, 4)
    datos[f"ck{i}"] = num(C * k)
for e, (ke, _, _) in por_elemento.items():
    assert np.allclose(ke, ke1, atol=1e-14), "los cuatro elementos deben tener la misma ke"

etiq = ["u_1", "v_1", "u_2", "v_2", "u_3", "v_3", "u_4", "v_4"]
tablas["ke"] = "\n".join(fila(f"${etiq[i]}$", *[m(ke1[i, j]) for j in range(8)]) for i in range(8))
B1 = puntos1[0]["B"]
tablas["B"] = "\n".join(fila(*[m(B1[i, j]) for j in range(8)]) for i in range(3))
datos["Bdiag"] = num(B1[0, 0])

# Valores prescritos y tabla de nodos.
u = np.zeros(18)
filas_nodos = []
for n, (x, y) in NODOS.items():
    if n == LIBRE:
        filas_nodos.append(fila(f"{n}", m(x, 1), m(y, 1), "libre",
                                r"\multicolumn{2}{c}{incógnitas $u_5,\ v_5$}"))
        continue
    ux, uy = R.u_M(x, y)
    u[2 * (n - 1):2 * n] = (ux, uy)
    filas_nodos.append(fila(f"{n}", m(x, 1), m(y, 1), "borde",
                            f"${exacto(ux)}$", f"${exacto(uy)}$"))
tablas["nodos"] = "\n".join(filas_nodos)

# Ecuaciones del nodo libre: bloques K_5j.
i5 = [2 * (LIBRE - 1), 2 * (LIBRE - 1) + 1]
filas_diag = []
for e, conn in ELEMS.items():
    loc = conn.index(LIBRE)
    ke = por_elemento[e][0]
    blk = ke[2 * loc:2 * loc + 2, 2 * loc:2 * loc + 2]
    filas_diag.append(fila(f"$e_{e}$", f"{loc + 1}", m(blk[0, 0]), m(blk[0, 1]), m(blk[1, 1])))
Kcc = K[np.ix_(i5, i5)]
filas_diag.append(r"\midrule")
filas_diag.append(fila(r"\multicolumn{2}{l}{Suma $=\bm{K}_{55}$}", m(Kcc[0, 0]), m(Kcc[0, 1]), m(Kcc[1, 1])))
tablas["Kdiag"] = "\n".join(filas_diag)
datos.update({"Kcc": num(Kcc[0, 0]), "Kccxy": num(Kcc[0, 1])})

vecinos = []
Kfr_ur = np.zeros(2)
suma_filas = Kcc.sum(axis=1).copy()
for n in NODOS:
    if n == LIBRE:
        continue
    j = [2 * (n - 1), 2 * (n - 1) + 1]
    blk = K[np.ix_(i5, j)]
    suma_filas += blk.sum(axis=1)
    if np.allclose(blk, 0.0):
        continue
    elems_n = [f"$e_{e}$" for e, conn in ELEMS.items() if n in conn and LIBRE in conn]
    assert abs(blk[0, 1] - blk[1, 0]) < 1e-14, f"bloque K_5{n} no simetrico: la tabla muestra solo xy"
    aporte = blk @ u[j]
    Kfr_ur += aporte
    vecinos.append(fila(f"{n}", ", ".join(elems_n), m(blk[0, 0]), m(blk[0, 1]), m(blk[1, 1]),
                        f"${exacto(u[j[0]])}$", f"${exacto(u[j[1]])}$", m(aporte[0]), m(aporte[1])))
vecinos.append(r"\midrule")
vecinos.append(fila(r"\multicolumn{7}{r}{Suma $=\bm{K}_{fr}\,\bm{u}_r$}", m(Kfr_ur[0]), m(Kfr_ur[1])))
tablas["vecinos"] = "\n".join(vecinos)
assert np.allclose(suma_filas, 0.0, atol=1e-13), "la fila de K del nodo libre debe sumar cero"
datos.update({"Kfrx": num(Kfr_ur[0]), "Kfry": num(Kfr_ur[1]),
              "nesq": num(abs(K[i5[0], 1])),        # |acoplamiento cruzado nodo 5 - nodo 1|
              "Kvecx": num(K[i5[0], 2]),            # K_xx nodo 5 - nodo 2 (medio de lado)
              "Kvecy": num(K[i5[0], 6])})           # K_xx nodo 5 - nodo 4 (medio de lado)

# Fuerza de cuerpo: detalle en e1 y aporte de cada elemento al nodo 5.
loc1 = ELEMS[1].index(LIBRE)
filas_b = []
sx = sy = 0.0
for g, p in enumerate(puntos1, start=1):
    Nc = p["N"][loc1]
    cx = Nc * p["bx"] * p["det_J"] * p["w"] * T
    cy = Nc * p["by"] * p["det_J"] * p["w"] * T
    sx += cx
    sy += cy
    filas_b.append(fila(f"$g_{g}$", m(p["x"]), m(p["y"]), m(Nc),
                        m(p["bx"]), m(p["by"]), m(cx), m(cy)))
filas_b.append(r"\midrule")
filas_b.append(fila(r"\multicolumn{6}{r}{Suma en $e_1$}", m(sx), m(sy)))
tablas["fuerzae1"] = "\n".join(filas_b)
filas_fe = []
for e, conn in ELEMS.items():
    loc = conn.index(LIBRE)
    fe = por_elemento[e][1]
    filas_fe.append(fila(f"$e_{e}$", f"{loc + 1}", m(fe[2 * loc]), m(fe[2 * loc + 1])))
filas_fe.append(r"\midrule")
filas_fe.append(fila(r"\multicolumn{2}{l}{Suma $=(F_9,\ F_{10})$}", m(F[i5[0]]), m(F[i5[1]])))
tablas["fuerzas"] = "\n".join(filas_fe)
p_cerca = puntos1[2]
datos.update({
    "gA": num(puntos1[0]["x"]), "gB": num(puntos1[2]["x"]),
    "sA": num(math.sin(PI * puntos1[0]["x"])), "sB": num(math.sin(PI * puntos1[2]["x"])),
    "Ncerca": num(p_cerca["N"][loc1]), "Nmixto": num(puntos1[1]["N"][loc1]),
    "Nlejos": num(puntos1[0]["N"][loc1]),
    "sumaNss": num(sx / (K2 * puntos1[0]["det_J"])),
    "fe1x": num(sx), "fe1y": num(sy), "F9": num(F[i5[0]]), "F10": num(F[i5[1]]),
})

# Sistema reducido y solucion.
libres = i5
restr = [i for i in range(18) if i not in libres]
Fred = F[libres] - K[np.ix_(libres, restr)] @ u[restr]
u5 = np.linalg.solve(Kcc, Fred)
u[libres] = u5
exacta5 = R.u_M(*NODOS[LIBRE])
datos.update({
    "Fredx": num(Fred[0]), "Fredy": num(Fred[1]),
    "u5": num(u5[0]), "v5": num(u5[1]),
    "erru5": num(u5[0] - exacta5[0]), "erru5pct": num(100 * abs(u5[0] - exacta5[0]), 2),
})

# Equilibrio global: las reacciones R = K u - F equilibran la fuerza de cuerpo.
reac = K @ u - F
assert abs(reac[0::2].sum() + F[0::2].sum()) < 1e-12 and abs(reac[1::2].sum() + F[1::2].sum()) < 1e-12
datos.update({"sumaFx": num(F[0::2].sum()), "sumaFy": num(F[1::2].sum()),
              "sumaRx": num(reac[0::2].sum()), "sumaRy": num(reac[1::2].sum())})

# Error en todo el dominio (Gauss 3x3), detalle en e1.
g3 = math.sqrt(0.6)
P3 = [(-g3, 5 / 9), (0.0, 8 / 9), (g3, 5 / 9)]
PG3 = [(xi, eta, wi * wj) for xi, wi in P3 for eta, wj in P3]


def errores_elemento(conn, detalle=False):
    xy = np.array([NODOS[n] for n in conn])
    ue = u[gdl(conn)].reshape(4, 2)
    sL2 = sH1 = sEx = 0.0
    filas_P, filas_L2, filas_H1 = [], [], []
    for g, (xi, eta, w) in enumerate(PG3, start=1):
        N = N_q4(xi, eta)
        J, det_J, B = geometria_q4(xy, xi, eta)
        dNxy = np.linalg.solve(J, dN_q4(xi, eta))
        x, y = N @ xy[:, 0], N @ xy[:, 1]
        uh = N @ ue
        ex = R.u_M(x, y)
        grad_h = np.array([[dNxy[0] @ ue[:, 0], dNxy[1] @ ue[:, 0]],
                           [dNxy[0] @ ue[:, 1], dNxy[1] @ ue[:, 1]]])
        grad_ex = R.grad_u_M(x, y)
        dA = det_J * w
        d2 = float(np.sum((uh - ex) ** 2))
        cL2 = d2 * dA
        e2 = float(np.sum((grad_h - grad_ex) ** 2))
        cH1 = e2 * dA
        sL2 += cL2
        sH1 += cH1
        sEx += float(np.sum(ex ** 2)) * dA
        if detalle:
            filas_P.append(fila(f"$p_{{{g}}}$", m(xi), m(eta), m(w), m(dA), m(x), m(y)))
            filas_L2.append(fila(f"$p_{{{g}}}$", m(uh[0]), m(ex[0]), m(uh[1]), m(ex[1]),
                                 m(d2), m(cL2)))
            filas_H1.append(fila(f"$p_{{{g}}}$", m(grad_h[0, 0]), m(grad_h[0, 1]),
                                 m(grad_h[1, 0]), m(grad_h[1, 1]), m(e2), m(cH1)))
            if xi == 0.0 and eta == 0.0:
                datos.update({
                    "cx": num(x, 2), "cy": num(y, 2),
                    "gux": num(grad_h[0, 0]), "guy": num(grad_h[0, 1]),
                    "gvx": num(grad_h[1, 0]), "gvy": num(grad_h[1, 1]),
                    "eux": num(grad_ex[0, 0]), "euy": num(grad_ex[0, 1]),
                    "evx": num(grad_ex[1, 0]), "evy": num(grad_ex[1, 1]),
                    "dux": num(grad_h[0, 0] - grad_ex[0, 0]), "dvx": num(grad_h[1, 0] - grad_ex[1, 0]),
                    "e2c": num(e2), "wc": num(w), "dAc": num(dA), "cH1c": num(cH1),
                    "uhc": num(uh[0]), "uMc": num(ex[0]), "vhc": num(uh[1]), "vMc": num(ex[1]),
                    "d2c": num(d2), "cL2c": num(cL2),
                })
    return sL2, sH1, sEx, filas_P, filas_L2, filas_H1


tot_L2 = tot_H1 = tot_Ex = 0.0
filas_elem = []
for e, conn in ELEMS.items():
    sL2, sH1, sEx, fP, fL2, fH1 = errores_elemento(conn, detalle=(e == 1))
    if e == 1:
        tablas["puntostres"] = "\n".join(fP)
        tablas["L2e1"] = "\n".join(fL2)
        tablas["H1e1"] = "\n".join(fH1)
        datos.update({"sL2e1": num(sL2), "sH1e1": num(sH1)})
    filas_elem.append(fila(f"$e_{e}$", m(sL2), m(sH1), m(sEx)))
    tot_L2 += sL2
    tot_H1 += sH1
    tot_Ex += sEx
filas_elem.append(r"\midrule")
filas_elem.append(fila("Suma", m(tot_L2), m(tot_H1), m(tot_Ex)))
tablas["erroreselem"] = "\n".join(filas_elem)
L2, H1, NEx = math.sqrt(tot_L2), math.sqrt(tot_H1), math.sqrt(tot_Ex)
datos.update({
    "totL2": num(tot_L2), "totH1": num(tot_H1), "totEx": num(tot_Ex),
    "L2": num(L2), "H1": num(H1), "normaEx": num(NEx),
    "L2rel": num(100 * L2 / NEx, 2),
})

# --- Refinamiento: replica completa, N = 2 ... 32, Q4 y Q9 ---------------------
NS = (2, 4, 8, 16, 32)
resultados = {1: [], 2: []}
for p in (1, 2):
    for N in NS:
        coords, elems, uu = R.resolver(N, p)
        h, eL2, eH1, _ = R.normas(coords, elems, uu, p)
        resultados[p].append(dict(N=N, h=h, gdl=len(uu), L2=eL2, H1=eH1))
    print(f"replica p = {p} lista")

assert abs(resultados[1][0]["L2"] - L2) < 1e-12 and abs(resultados[1][0]["H1"] - H1) < 1e-12, \
    "el calculo a mano de N = 2 debe coincidir con la replica"


def tasa(a, b_, clave):
    return math.log(a[clave] / b_[clave]) / math.log(a["h"] / b_["h"])


filas_ref, filas_tasas = [], []
for i, N in enumerate(NS):
    q4, q9 = resultados[1][i], resultados[2][i]
    filas_ref.append(fila(f"{N}", m(q4["h"], 5), f"{q4['gdl']}", f"${sci(q4['L2'])}$", f"${sci(q4['H1'])}$",
                          f"{q9['gdl']}", f"${sci(q9['L2'])}$", f"${sci(q9['H1'])}$"))
    if i > 0:
        a4, a9 = resultados[1][i - 1], resultados[2][i - 1]
        filas_tasas.append(fila(f"{NS[i - 1]} $\\to$ {N}",
                                m(a4["L2"] / q4["L2"], 3), m(tasa(a4, q4, "L2"), 3),
                                m(a4["H1"] / q4["H1"], 3), m(tasa(a4, q4, "H1"), 3),
                                m(a9["L2"] / q9["L2"], 3), m(tasa(a9, q9, "L2"), 3),
                                m(a9["H1"] / q9["H1"], 3), m(tasa(a9, q9, "H1"), 3)))
tablas["refinamiento"] = "\n".join(filas_ref)
tablas["tasas"] = "\n".join(filas_tasas)
a, b_ = resultados[1][3], resultados[1][4]
datos.update({
    "eL2dieciseis": sci(a["L2"]), "eL2treintaydos": sci(b_["L2"]),
    "cocienteL2": num(a["L2"] / b_["L2"]), "tasaL2": num(tasa(a, b_, "L2"), 4),
    "tasaQcuatroLdos": num(tasa(a, b_, "L2"), 3), "tasaQcuatroHuno": num(tasa(a, b_, "H1"), 3),
    "tasaQnueveLdos": num(tasa(resultados[2][3], resultados[2][4], "L2"), 3),
    "tasaQnueveHuno": num(tasa(resultados[2][3], resultados[2][4], "H1"), 3),
    "tasaPrimeraQcuatro": num(tasa(resultados[1][0], resultados[1][1], "L2"), 3),
})

with open(os.path.join(AQUI, "convergencia.dat"), "w", encoding="ascii") as fh:
    fh.write("h L2q4 H1q4 L2q9 H1q9\n")
    for q4, q9 in zip(resultados[1], resultados[2]):
        fh.write(f"{q4['h']:.6f} {q4['L2']:.6e} {q4['H1']:.6e} {q9['L2']:.6e} {q9['H1']:.6e}\n")

# Rectas de pendiente teorica, paralelas a cada serie y desplazadas por debajo
# (factor 0,4) para no taparla: C h^p con C ajustada en la malla mas fina.
fino4, fino9 = resultados[1][-1], resultados[2][-1]
REF = {"L2q4": (fino4["L2"], 2), "H1q4": (fino4["H1"], 1),
       "L2q9": (fino9["L2"], 3), "H1q9": (fino9["H1"], 2)}
with open(os.path.join(AQUI, "pendientes.dat"), "w", encoding="ascii") as fh:
    fh.write("h " + " ".join(REF) + "\n")
    for h in (NS[-1] ** -1, NS[0] ** -1):
        fh.write(f"{h:.6f} " + " ".join(f"{0.4 * e * (h / fino4['h']) ** p:.6e}" for e, p in REF.values()) + "\n")

datos.update({
    "dosmupi": num(2 * MU * PI), "lamDP": num(E * NU / ((1 + NU) * (1 - 2 * NU))),
    "sL2e1raiz": num(math.sqrt(tot_L2 / 4)),
})


# --- Contraste con EduFEM (si el repositorio esta disponible) ---------------------
def contrastar_con_edufem():
    csv_q4 = os.path.join(REPO, "docs", "vyv", "datos", "mms_q4.csv")
    if not os.path.isfile(csv_q4):
        print("Repositorio no disponible: se omite el contraste con EduFEM.")
        return "sin contraste"
    for p, nombre in ((1, "q4"), (2, "q9")):
        with open(os.path.join(REPO, "docs", "vyv", "datos", f"mms_{nombre}.csv"), encoding="utf-8") as fh:
            for fila_csv, rep in zip(csv.DictReader(fh), resultados[p]):
                for clave_csv, clave in (("L2_disp", "L2"), ("H1_semi", "H1")):
                    ref = float(fila_csv[clave_csv])
                    assert abs(rep[clave] - ref) <= 5e-7 * ref, (nombre, fila_csv["N"], clave_csv)
    sys.path.insert(0, REPO)
    from config.settings import ELEMENT_Q4
    from tests import vv_mms
    _, sol, norms = vv_mms.run_case(2, ELEMENT_Q4)
    assert np.allclose(sol["K_red"].toarray(), Kcc, atol=1e-12)
    assert np.allclose(sol["F_red"], Fred, atol=1e-12)
    assert np.allclose(sol["u"][[8, 9]], u5, atol=1e-12)
    assert abs(norms["L2_disp"] - L2) < 1e-12 and abs(norms["H1_semi"] - H1) < 1e-12
    print("Contraste con EduFEM: K_red, F_red, u_5, normas de N = 2 y los 20 valores de los CSV coinciden.")
    return "coincide"


datos["contraste"] = contrastar_con_edufem()

with open(os.path.join(AQUI, "datos.tex"), "w", encoding="utf-8") as fh:
    fh.write("% Generado por generar_datos.py: no editar a mano.\n")
    for clave, valor in datos.items():
        fh.write(f"\\expandafter\\def\\csname dato:{clave}\\endcsname{{{valor}}}\n")
    for clave, cuerpo in tablas.items():
        fh.write(f"\\expandafter\\def\\csname tabla:{clave}\\endcsname{{%\n{cuerpo}\n}}\n")
print(f"datos.tex: {len(datos)} datos y {len(tablas)} tablas. u5 = {u5}, L2 = {L2:.7f}, H1 = {H1:.6f}")
