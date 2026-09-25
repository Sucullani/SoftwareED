# -*- coding: utf-8 -*-
"""
Cifras, tablas y figuras de `solucionador_disperso.tex`.

Todo número que el documento cita sale de este guion: se calcula con el propio
motor de EduFEM (`fem.assembly`, `fem.solver`, `fem.batch`) y con SciPy/NumPy,
y se escribe en `datos/cifras.tex` (macros `\\cifra{clave}`) y en las filas de
tabla `datos/tabla_*.tex`. Los ejemplos a mano del documento (cadena de
resortes, estrella, malla 2x2, barra en COO) se verifican en aritmética exacta
con `fractions.Fraction`: si una cifra del texto dejara de ser cierta, el guion
se detiene con AssertionError antes de escribir nada.

Uso, desde la raíz del repositorio y con el entorno del proyecto:

    python docs/teoria/solucionador/generar_datos.py           # todo (unos 5 min)
    python docs/teoria/solucionador/generar_datos.py --rapido  # sin el orden natural
                                                               # a 4704/8320 GDL ni la
                                                               # inversa densa de 4704

Después: `pdflatex solucionador_disperso.tex` dos veces en esta carpeta.

Los tiempos dependen del equipo y de su carga; se toma el mejor de varias
corridas. El documento cita las razones entre tiempos, más estables que los
valores absolutos.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import platform
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
import scipy  # noqa: E402
from scipy.sparse import csc_array  # noqa: E402
from scipy.sparse.linalg import splu, spsolve  # noqa: E402

from config.settings import ELEMENT_Q4, ELEMENT_Q9, SOLVER_PERMC_SPEC  # noqa: E402
from fem.assembly import assemble_global_system  # noqa: E402
from fem.batch import assemble_sparse  # noqa: E402
from fem.solver import apply_boundary_conditions, solve_system  # noqa: E402
from models.mesh_utils import generate_structured_quad_mesh  # noqa: E402
from tests.bench_timing import build_project  # noqa: E402

FIG = AQUI / "figuras"
DAT = AQUI / "datos"

# Paleta categórica validada (orden fijo; ver el skill de visualización).
AZUL, NARANJA, AGUA, AMARILLO = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
MAGENTA, VERDE = "#e87ba4", "#008300"
TINTA, TINTA2, TENUE = "#0b0b0b", "#52514e", "#898781"
GRILLA, EJE = "#e1e0d9", "#c3c2b7"

ORDENES = ["NATURAL", "COLAMD", "MMD_ATA", "MMD_AT_PLUS_A"]
COLOR = {"MMD_AT_PLUS_A": AZUL, "COLAMD": NARANJA, "MMD_ATA": AGUA, "NATURAL": AMARILLO}
MARCA = {"MMD_AT_PLUS_A": "o", "COLAMD": "s", "MMD_ATA": "^", "NATURAL": "D"}
ETIQUETA = {"MMD_AT_PLUS_A": "MMD_AT_PLUS_A (EduFEM)", "COLAMD": "COLAMD (defecto de SciPy)",
            "MMD_ATA": "MMD_ATA", "NATURAL": "NATURAL (sin reordenar)"}

NS_Q9 = [8, 16, 24, 32, 64]
NS_Q4 = [16, 32, 64]
NS_DENSO = [8, 16, 24]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 8.5,
    "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.edgecolor": EJE, "axes.labelcolor": TINTA2,
    "xtick.color": TINTA2, "ytick.color": TINTA2, "text.color": TINTA,
    "axes.titlecolor": TINTA, "pdf.fonttype": 42, "savefig.dpi": 300,
})


# ─── Formato de números (norma del español) ───────────────────────────────

def entero(n) -> str:
    """Sin separar hasta 9999; desde 10 000, grupos de tres con espacio fino."""
    s = str(abs(int(n)))
    if abs(int(n)) >= 10000:
        grupos = []
        while s:
            grupos.append(s[-3:])
            s = s[:-3]
        s = r"\,".join(reversed(grupos))
    return ("-" if int(n) < 0 else "") + s


def decimal(x: float, nd: int) -> str:
    return f"{x:.{nd}f}".replace(".", "{,}")


def sig(x: float, n: int = 2) -> str:
    """x con n cifras significativas y coma decimal."""
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    nd = n - 1 - e
    v = round(x, nd)
    if v != 0 and math.floor(math.log10(abs(v))) != e:   # 9,96 -> 10,0
        nd -= 1
        v = round(x, nd)
    return decimal(v, nd) if nd > 0 else entero(round(v))


def cientifico(x: float, nd: int = 1) -> str:
    m, e = f"{x:.{nd}e}".split("e")
    return rf"\ensuremath{{{m.replace('.', '{,}')}\times 10^{{{int(e)}}}}}"


def texto_plano(s: str) -> str:
    """Versión para matplotlib (sin macros de LaTeX)."""
    return s.replace(r"\,", "\u2009").replace("{,}", ",")


# ─── 1. Ejemplos a mano, en aritmética exacta ─────────────────────────────

def lu_exacta(A):
    """LU de Doolittle sin pivoteo. Devuelve L, U, posiciones de relleno y
    la matriz después de cada paso."""
    n = len(A)
    U = [[Fraction(x) for x in fila] for fila in A]
    L = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]
    relleno, pasos = [], []
    for k in range(n - 1):
        for i in range(k + 1, n):
            if U[i][k] == 0:
                continue
            l = U[i][k] / U[k][k]
            L[i][k] = l
            for j in range(k, n):
                antes = U[i][j]
                U[i][j] = U[i][j] - l * U[k][j]
                if antes == 0 and U[i][j] != 0:
                    relleno.append((i, j))
        pasos.append([fila[:] for fila in U])
    return L, U, relleno, pasos


def adelante(L, b):
    y = []
    for i in range(len(b)):
        y.append(Fraction(b[i]) - sum(L[i][j] * y[j] for j in range(i)))
    return y


def atras(U, y):
    n = len(y)
    x = [Fraction(0)] * n
    for i in reversed(range(n)):
        x[i] = (y[i] - sum(U[i][j] * x[j] for j in range(i + 1, n))) / U[i][i]
    return x


def F(s):
    return Fraction(s)


def verificar_ejemplos():
    # Ejemplo 1: cadena de tres resortes iguales (k = 1, P = 1).
    K = [[2, -1, 0], [-1, 2, -1], [0, -1, 1]]
    L, U, relleno, _ = lu_exacta(K)
    assert L == [[1, 0, 0], [F("-1/2"), 1, 0], [0, F("-2/3"), 1]]
    assert U == [[2, -1, 0], [0, F("3/2"), -1], [0, 0, F("1/3")]]
    assert relleno == []
    y = adelante(L, [0, 0, 1])
    x = atras(U, y)
    assert y == [0, 0, 1] and x == [1, 2, 3]
    inversa = [atras(U, adelante(L, [int(i == j) for i in range(3)])) for j in range(3)]
    assert [[inversa[j][i] for j in range(3)] for i in range(3)] == [[1, 1, 1], [1, 2, 2], [1, 2, 3]]
    D = [U[i][i] for i in range(3)]
    assert all(U[i][j] == D[i] * L[j][i] for i in range(3) for j in range(3))   # U = D L^T
    assert D[0] * D[1] * D[2] == 1                                               # det K

    # Ejemplo 2: estrella (nodo central 1 y tres hojas), central primero.
    S = [[4, -1, -1, -1], [-1, 3, 0, 0], [-1, 0, 3, 0], [-1, 0, 0, 3]]
    L, U, relleno, pasos = lu_exacta(S)
    assert sorted(relleno) == [(1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2)]
    a, b = F("11/4"), F("-1/4")
    assert [f[1:] for f in pasos[0][1:]] == [[a, b, b], [b, a, b], [b, b, a]]
    assert [f[2:] for f in pasos[1][2:]] == [[F("30/11"), F("-3/11")], [F("-3/11"), F("30/11")]]
    assert U == [[4, -1, -1, -1], [0, F("11/4"), F("-1/4"), F("-1/4")],
                 [0, 0, F("30/11"), F("-3/11")], [0, 0, 0, F("27/10")]]
    assert L == [[1, 0, 0, 0], [F("-1/4"), 1, 0, 0], [F("-1/4"), F("-1/11"), 1, 0],
                 [F("-1/4"), F("-1/11"), F("-1/10"), 1]]
    y = adelante(L, [1, 2, 2, 2])
    assert y == [1, F("9/4"), F("27/11"), F("27/10")] and atras(U, y) == [1, 1, 1, 1]
    # ... y central al final: ningún relleno.
    orden = [1, 2, 3, 0]
    S2 = [[S[i][j] for j in orden] for i in orden]
    L2, U2, relleno2, _ = lu_exacta(S2)
    assert relleno2 == []
    assert U2 == [[3, 0, 0, -1], [0, 3, 0, -1], [0, 0, 3, -1], [0, 0, 0, 3]]
    assert L2[3][:3] == [F("-1/3")] * 3
    y2 = adelante(L2, [2, 2, 2, 1])
    assert y2 == [2, 2, 2, 3] and atras(U2, y2) == [1, 1, 1, 1]

    # Ejemplo 4: barra de 3 nodos en COO, con la misma función del motor.
    dofs = np.array([[0, 1], [1, 2]])
    ke = np.array([[[1.0, -1.0], [-1.0, 1.0]]] * 2)
    filas = np.repeat(dofs, 2, axis=1).ravel()
    cols = np.tile(dofs, (1, 2)).ravel()
    assert filas.tolist() == [0, 0, 1, 1, 1, 1, 2, 2]
    assert cols.tolist() == [0, 1, 0, 1, 1, 2, 1, 2]
    assert ke.ravel().tolist() == [1, -1, -1, 1, 1, -1, -1, 1]
    Kb = assemble_sparse(dofs, ke, 3)
    assert Kb.indptr.tolist() == [0, 2, 5, 7]
    assert Kb.indices.tolist() == [0, 1, 0, 1, 2, 1, 2]
    assert Kb.data.tolist() == [1, -1, -1, 2, -1, -1, 1]
    Kc = Kb.tocsc()
    assert Kc.indptr.tolist() == [0, 2, 5, 7] and Kc.indices.tolist() == [0, 1, 0, 1, 2, 1, 2]
    print("  ejemplos a mano: verificados")


# ─── 2. Mínimo grado sobre la malla 2x2 de Q4 (grafo de 9 nodos) ─────────

POS = {v: ((v - 1) % 3, (v - 1) // 3) for v in range(1, 10)}


def grafo_malla_2x2():
    adj = {v: set() for v in POS}
    for j in range(2):
        for i in range(2):
            a = 1 + i + 3 * j
            elem = [a, a + 1, a + 4, a + 3]
            for p, q in itertools.combinations(elem, 2):
                adj[p].add(q)
                adj[q].add(p)
    return adj


def eliminar(adj, orden):
    """Relleno total de un orden y aristas nuevas."""
    g = {v: set(s) for v, s in adj.items()}
    nuevas = []
    for v in orden:
        for a, b in itertools.combinations(sorted(g[v]), 2):
            if b not in g[a]:
                g[a].add(b)
                g[b].add(a)
                nuevas.append((a, b))
        for a in g[v]:
            g[a].discard(v)
        del g[v]
    return nuevas


def minimo_grado(adj):
    """Mínimo grado con desempate por el número menor. Registra cada paso."""
    g = {v: set(s) for v, s in adj.items()}
    orden, pasos, relleno_acum = [], [], []
    while g:
        grados = {u: len(g[u]) for u in g}
        dmin = min(grados.values())
        v = min(u for u in g if grados[u] == dmin)
        pasos.append({"grafo": {u: set(s) for u, s in g.items()}, "grados": grados,
                      "elige": v, "relleno_previo": list(relleno_acum)})
        nuevas = []
        for a, b in itertools.combinations(sorted(g[v]), 2):
            if b not in g[a]:
                g[a].add(b)
                g[b].add(a)
                nuevas.append((a, b))
        relleno_acum += nuevas
        pasos[-1]["vecinos"] = sorted(g[v])
        pasos[-1]["nuevas"] = nuevas
        for a in g[v]:
            g[a].discard(v)
        del g[v]
        orden.append(v)
    return orden, pasos


def _arista(a, b, estilo):
    (xa, ya), (xb, yb) = POS[a], POS[b]
    if math.gcd(abs(xb - xa), abs(yb - ya)) > 1:     # pasa por encima de otro nodo
        return rf"\draw[{estilo}] (c{a}) to[bend left=30] (c{b});"
    return rf"\draw[{estilo}] (c{a}) -- (c{b});"


def tikz_panel(g, relleno, elige, grados, eliminados, mostrar_grados=True):
    out = [r"\begin{tikzpicture}[x=0.92cm,y=0.92cm]"]
    for v, (i, j) in POS.items():
        out.append(rf"\coordinate (c{v}) at ({i},{j});")
    rell = {tuple(sorted(e)) for e in relleno}
    aristas = sorted({tuple(sorted((a, b))) for a in g for b in g[a]})
    for a, b in aristas:
        out.append(_arista(a, b, "relleno" if (a, b) in rell else "arista"))
    for v in POS:
        estilo = "nodoelim" if v in eliminados else ("nodosig" if v == elige else "nodo")
        out.append(rf"\node[{estilo}] at (c{v}) {{{v}}};")
        if mostrar_grados and v not in eliminados:
            i, j = POS[v]
            out.append(rf"\node[grado] at ({i + 0.33},{j + 0.3}) {{{grados[v]}}};")
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


def tikz_completo(adj, relleno):
    g = {v: set(s) for v, s in adj.items()}
    for a, b in relleno:
        g[a].add(b)
        g[b].add(a)
    return tikz_panel(g, relleno, None, {}, set(), mostrar_grados=False)


def figuras_minimo_grado():
    adj = grafo_malla_2x2()
    assert sum(len(s) for s in adj.values()) // 2 == 20
    orden, pasos = minimo_grado(adj)
    assert orden == [1, 3, 2, 7, 4, 5, 6, 8, 9]
    rell_md = eliminar(adj, orden)
    rell_nat = eliminar(adj, list(range(1, 10)))
    rell_cen = eliminar(adj, [5, 1, 2, 3, 4, 6, 7, 8, 9])
    assert rell_md == [(4, 6)]
    assert sorted(rell_nat) == [(3, 4), (4, 6), (6, 7), (7, 9)]
    assert len(rell_cen) == 16
    t0 = time.perf_counter()
    optimo = min(len(eliminar(adj, list(p))) for p in itertools.permutations(range(1, 10)))
    assert optimo == 1
    print(f"  mínimo grado 2x2: óptimo por fuerza bruta = 1 ({time.perf_counter() - t0:.0f} s)")

    leyendas = [
        "Inicio: esquinas 3, lados 5, centro 8. Se elige 1.",
        "Sin 1 (sin relleno). Se elige 3.",
        "Sin 3 (sin relleno). Empate 2, 7, 9: se elige 2.",
        "Sin 2: aparece la arista 4--6. Se elige 7.",
        "Sin 7 (sin relleno). Se elige 4.",
        "Sin 4: 5, 6, 8 y 9 ya forman un bloque lleno.",
    ]
    paneles = []
    for k in range(6):
        p = pasos[k]
        eliminados = set(orden[:k])
        relleno = [e for e in p["relleno_previo"] if e[0] not in eliminados and e[1] not in eliminados]
        panel = tikz_panel(p["grafo"], relleno, p["elige"], p["grados"], eliminados)
        paneles.append(
            r"\begin{minipage}[t]{0.32\textwidth}\centering" + "\n" + panel + "\n"
            + rf"\par\smallskip{{\footnotesize ({'abcdef'[k]}) {leyendas[k]}}}\end{{minipage}}")
    (FIG / "md_pasos.tex").write_text(
        "% Generado por generar_datos.py: no editar a mano.\n"
        + (paneles[0] + "\\hfill\n" + paneles[1] + "\\hfill\n" + paneles[2] + "\n\n\\bigskip\n"
           + paneles[3] + "\\hfill\n" + paneles[4] + "\\hfill\n" + paneles[5] + "\n"),
        encoding="utf-8")

    comp = []
    for titulo, rell in [("Orden natural 1, 2, \\ldots, 9: 4 aristas nuevas", rell_nat),
                         ("Mínimo grado 1, 3, 2, 7, 4, \\ldots: 1 arista nueva", rell_md),
                         ("Centro primero 5, 1, 2, \\ldots: 16 aristas nuevas", rell_cen)]:
        comp.append(r"\begin{minipage}[t]{0.32\textwidth}\centering" + "\n"
                    + tikz_completo(adj, rell) + "\n"
                    + rf"\par\smallskip{{\footnotesize {titulo}}}\end{{minipage}}")
    (FIG / "md_comparacion.tex").write_text(
        "% Generado por generar_datos.py: no editar a mano.\n" + "\\hfill\n".join(comp) + "\n",
        encoding="utf-8")

    filas = []
    for k, p in enumerate(pasos[:6]):
        grados = ", ".join(f"{u}:{d}" for u, d in sorted(p["grados"].items()))
        nuevas = ", ".join(f"{a}--{b}" for a, b in p["nuevas"]) or "---"
        filas.append(rf"{k + 1} & {grados} & \textbf{{{p['elige']}}} & "
                     rf"{', '.join(map(str, p['vecinos']))} & {nuevas} \\")
    filas.append(r"7--9 & 6:2, 8:2, 9:2 $\to$ \ldots & 6, 8, 9 & --- & --- \\")
    (DAT / "tabla_md.tex").write_text("% Generado por generar_datos.py\n" + "\n".join(filas) + "\n",
                                      encoding="utf-8")


# ─── 3. Mediciones con el motor de EduFEM ─────────────────────────────────

def mejor(fn, repeticiones):
    b = float("inf")
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        fn()
        b = min(b, time.perf_counter() - t0)
    return b


def supernodos(L):
    """Tamaños de los supernodos fundamentales del factor L (CSC, diagonal
    unitaria incluida): columnas contiguas j-1, j con
    estructura(j-1) = {j-1} U estructura(j)."""
    L = L.tocsc()
    L.sort_indices()
    ip, ix = L.indptr, L.indices
    tam, actual = [], 1
    for j in range(1, L.shape[0]):
        a, b = ix[ip[j - 1]:ip[j]], ix[ip[j]:ip[j + 1]]
        if len(a) == len(b) + 1 and a[0] == j - 1 and np.array_equal(a[1:], b):
            actual += 1
        else:
            tam.append(actual)
            actual = 1
    tam.append(actual)
    return np.array(tam)


def operaciones_lu(lu):
    """Operaciones de punto flotante de la factorización, contadas sobre la
    estructura de los factores: en el paso j hay c_j divisiones y c_j * r_j
    actualizaciones (un producto y una resta), con c_j los no nulos de L bajo
    la diagonal en la columna j y r_j los de U a la derecha de la diagonal en
    la fila j. A diferencia del tiempo, no depende del equipo ni de su carga."""
    L = lu.L.tocsc()
    U = lu.U.tocsr()
    c = np.diff(L.indptr).astype(float) - 1.0     # L guarda la diagonal unitaria
    r = np.diff(U.indptr).astype(float) - 1.0     # U guarda la diagonal
    return float(np.sum(c + 2.0 * c * r))


def sistema(N, tipo):
    p = build_project(N, tipo)
    K, Fv, _ = assemble_global_system(p)
    restr = p.get_restrained_dofs()
    Kr, Fr, _ = apply_boundary_conditions(K, Fv, restr)
    return p, K, Fv, restr, Kr.tocsc(), Fr


def medir(N, tipo, rapido, denso):
    p, K, Fv, restr, A, b = sistema(N, tipo)
    n = A.shape[0]
    nn = len(next(iter(p.elements.values())).node_ids)
    AtA = (abs(A).T @ abs(A)).tocsr()
    r = {"N": N, "nodos": p.num_nodes, "elementos": p.num_elements, "gdl": p.total_dof,
         "restr": len(restr), "n": n, "tripletes": p.num_elements * (2 * nn) ** 2,
         "nnzK": int(K.nnz), "nnzKr": int(A.nnz), "maxfila": int(np.diff(A.indptr).max()),
         "nnzAtA": int(AtA.nnz), "maxfilaAtA": int(np.diff(AtA.indptr).max()),
         "bytesKr": int(A.data.nbytes + A.indices.nbytes + A.indptr.nbytes), "orden": {}}
    for spec in ORDENES:
        pesado = spec == "NATURAL" and tipo == ELEMENT_Q9 and N >= 24
        if spec == "NATURAL" and tipo == ELEMENT_Q9 and (N >= 64 or (rapido and pesado)):
            continue
        lu = splu(A, permc_spec=spec)
        o = {"nnzLU": int(lu.L.nnz + lu.U.nnz - n),
             "piv": int(np.count_nonzero(lu.perm_r != lu.perm_c)),
             # El equipo no está dedicado: el mejor de muchas corridas filtra el
             # ruido de los otros procesos, que solo puede sumar tiempo.
             "t": mejor(lambda: spsolve(A, b, permc_spec=spec),
                        1 if pesado else (15 if N <= 32 else 7))}
        o["relleno"] = o["nnzLU"] / r["nnzKr"]
        o["flops"] = operaciones_lu(lu)
        if spec == "MMD_AT_PLUS_A":
            o["nnzL"], o["nnzU"] = int(lu.L.nnz), int(lu.U.nnz)
            sn = supernodos(lu.L)
            o["sn_media"], o["sn_max"] = float(sn.mean()), int(sn.max())
            o["sn_mayor1"] = float(np.mean(sn >= 2))
            lu0 = splu(A, permc_spec=spec, diag_pivot_thresh=0.0)
            o["nnzLU_umbral0"] = int(lu0.L.nnz + lu0.U.nnz - n)
            o["piv_umbral0"] = int(np.count_nonzero(lu0.perm_r != lu0.perm_c))
        r["orden"][spec] = o
        del lu
    if denso and not (rapido and N >= 24):
        Kd = A.toarray()
        u_sp = spsolve(A, b, permc_spec="MMD_AT_PLUS_A")
        rep = 7 if N <= 8 else (4 if N <= 16 else 2)
        r["t_solve"] = mejor(lambda: np.linalg.solve(Kd, b), rep)
        r["t_inv"] = mejor(lambda: np.linalg.inv(Kd) @ b, rep)
        u_ds = np.linalg.solve(Kd, b)
        Kinv = np.linalg.inv(Kd)
        u_inv = Kinv @ b
        nb = np.linalg.norm(b)
        r["res_sp"] = float(np.linalg.norm(A @ u_sp - b) / nb)
        r["res_solve"] = float(np.linalg.norm(A @ u_ds - b) / nb)
        r["res_inv"] = float(np.linalg.norm(A @ u_inv - b) / nb)
        r["dif_inv"] = float(np.linalg.norm(u_inv - u_sp) / np.linalg.norm(u_sp))
        r["dens_inv"] = float(np.count_nonzero(Kinv) / n ** 2)
        r["ceros_inv"] = int(np.count_nonzero(Kinv == 0.0))
        if N <= 16:
            r["cond"] = float(np.linalg.cond(Kd))
        del Kd, Kinv
    return r


def traza_cook8():
    """Una resolución real, paso a paso, con la API pública del motor."""
    p = build_project(8, ELEMENT_Q9)
    res = solve_system(p)
    K, Fv, u, R = res["K"], res["F"], res["u"], res["reactions"]
    Kr, Fr = res["K_red"], res["F_red"]
    uf = u[np.asarray(res["free_dofs"])]
    # Punto de control de la verificación de la tesis (tests/vv_cook.py): el
    # centro del lado libre, (48, 52), que en esta malla es un nodo.
    nid_c = next(nid for nid, nd in p.nodes.items()
                 if abs(nd.x - 48.0) < 1e-9 and abs(nd.y - 52.0) < 1e-9)
    uy = float(u[p.dof_y(nid_c)])
    ref_vv = None
    csv = RAIZ / "docs" / "vyv" / "datos" / "cook.csv"
    if csv.exists():
        for linea in csv.read_text(encoding="utf-8").splitlines()[1:]:
            c = linea.split(",")
            if c[0] == "8" and c[1] == "Q9":
                assert abs(float(c[3]) - uy) < 1e-4, (c, uy)   # mismo valor que la V&V
                ref_vv = float(c[6])
    return {"uyC": uy, "uyRef": ref_vv,
            "resid": float(np.linalg.norm(Kr @ uf - Fr) / np.linalg.norm(Fr)),
            "sumRy": float(R[1::2].sum()), "sumFy": float(Fv[1::2].sum()),
            "sumRx": float(R[0::2].sum()), "sumFx": float(Fv[0::2].sum()),
            "formato_K": K.format, "formato_Kred": Kr.format}


# ─── 4. Figuras con matplotlib ────────────────────────────────────────────

def estilo_ejes(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(length=2.5, width=0.6)


def figura_malla_patron():
    p = generate_structured_quad_mesh(corners=[(0, 0), (3, 0), (3, 2), (0, 2)], nx=3, ny=2,
                                      element_type=ELEMENT_Q4)
    K, _, _ = assemble_global_system(p)
    Kc = K.tocoo()
    n = K.shape[0]
    foco = 6
    vecinos = set()
    for e in p.elements.values():
        if foco in e.node_ids:
            vecinos |= set(e.node_ids)
    idx = p.node_index_map
    filas_foco = {2 * idx[foco], 2 * idx[foco] + 1}
    assert K.nnz == 280 and len(vecinos) == 9
    assert all(len(K.tocsr()[i].indices) == 18 for i in filas_foco)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.3, 2.75), gridspec_kw={"width_ratios": [1.05, 1]})
    for e in p.elements.values():
        xs = [p.nodes[v].x for v in e.node_ids] + [p.nodes[e.node_ids[0]].x]
        ys = [p.nodes[v].y for v in e.node_ids] + [p.nodes[e.node_ids[0]].y]
        a1.plot(xs, ys, color=TINTA2, lw=1.0, zorder=1)
        cx, cy = np.mean(xs[:-1]), np.mean(ys[:-1])
        a1.text(cx, cy, f"e{e.id}", color=TENUE, fontsize=7.5, ha="center", va="center", style="italic")
    for nid, nd in p.nodes.items():
        if nid == foco:
            fc, ec, tc = NARANJA, NARANJA, "white"
        elif nid in vecinos:
            fc, ec, tc = "white", NARANJA, TINTA
        else:
            fc, ec, tc = "white", TINTA2, TINTA
        a1.add_patch(plt.Circle((nd.x, nd.y), 0.17, facecolor=fc, edgecolor=ec, lw=1.4, zorder=3))
        a1.text(nd.x, nd.y, str(nid), ha="center", va="center", fontsize=7.5, color=tc, zorder=4,
                fontweight="bold" if nid == foco else "normal")
    a1.set_aspect("equal")
    a1.set_xlim(-0.35, 3.35)
    a1.set_ylim(-0.35, 2.35)
    a1.axis("off")
    a1.set_title("Malla 3 × 2 Q4: 12 nodos, 24 GDL", pad=4)

    img = np.zeros((n, n))
    img[Kc.row, Kc.col] = 1
    for i in filas_foco:
        img[i, img[i] == 1] = 2
    cmap = ListedColormap(["white", AZUL, NARANJA])
    a2.imshow(img, cmap=cmap, vmin=0, vmax=2, interpolation="none", extent=(0, n, n, 0))
    for k in range(0, n + 1, 2):
        a2.axhline(k, color=GRILLA, lw=0.5)
        a2.axvline(k, color=GRILLA, lw=0.5)
    centros = np.arange(1, n, 2)
    nombres = [str(v) for v in sorted(idx, key=idx.get)]
    a2.set_xticks(centros, nombres)
    a2.set_yticks(centros, nombres)
    a2.tick_params(length=0, labelsize=6.5)
    a2.xaxis.tick_top()
    for s in a2.spines.values():
        s.set_color(EJE)
    a2.set_title(f"Patrón de K: {K.nnz} de {n * n} coeficientes", pad=16)
    a2.legend(handles=[Patch(color=AZUL, label="coeficiente no nulo"),
                       Patch(color=NARANJA, label="filas del nodo 6 (18 cada una)")],
              loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2, frameon=False,
              handlelength=1.0, columnspacing=1.0)
    fig.tight_layout(w_pad=1.5)
    fig.savefig(FIG / "malla_patron.pdf")
    plt.close(fig)
    return {"nnz": int(K.nnz), "ceros": int(K.nnz - np.count_nonzero(K.data))}


def figura_llenado_cook():
    p, K, Fv, restr, A, b = sistema(8, ELEMENT_Q9)
    n = A.shape[0]
    fig, axes = plt.subplots(2, 2, figsize=(6.3, 6.55))
    cmap = ListedColormap(["white", AZUL, NARANJA])
    info = {}
    for fila, spec in enumerate(["NATURAL", "MMD_AT_PLUS_A"]):
        lu = splu(A, permc_spec=spec)
        Pr = csc_array((np.ones(n), (lu.perm_r, np.arange(n))))
        Pc = csc_array((np.ones(n), (np.arange(n), lu.perm_c)))
        PAP = (Pr @ A @ Pc).tocoo()
        LU = (abs(lu.L) + abs(lu.U)).tocoo()
        img_a = np.zeros((n, n))
        img_a[PAP.row, PAP.col] = 1
        img_lu = np.zeros((n, n))
        img_lu[LU.row, LU.col] = 2
        img_lu[img_a == 1] = 1
        nnz_lu = int(lu.L.nnz + lu.U.nnz - n)
        assert nnz_lu == int(np.count_nonzero(img_lu))
        info[spec] = nnz_lu
        nombre = "orden natural de EduFEM" if spec == "NATURAL" else "reordenada con MMD_AT_PLUS_A"
        for col, (im, tit) in enumerate([
                (img_a, f"$K_{{ff}}$, {nombre}\n{texto_plano(entero(A.nnz))} no nulos"),
                (img_lu, f"$L+U$: {texto_plano(entero(nnz_lu))} coeficientes"
                         f" ({texto_plano(decimal(nnz_lu / A.nnz, 1))} × nnz($K_{{ff}}$))")]):
            ax = axes[fila, col]
            ax.imshow(im, cmap=cmap, vmin=0, vmax=2, interpolation="none")
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color(EJE)
                s.set_linewidth(0.6)
            ax.set_title(tit, fontsize=8, pad=4)
    fig.legend(handles=[Patch(color=AZUL, label="coeficiente de $K_{ff}$ (en su posición permutada)"),
                        Patch(color=NARANJA, label="llenado: cero en $K_{ff}$, no nulo en $L$ o $U$")],
               loc="lower center", ncol=2, frameon=False, handlelength=1.0, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.04, 1, 1), h_pad=1.2, w_pad=1.0)
    fig.savefig(FIG / "llenado_cook.pdf")
    plt.close(fig)
    return info


def figura_tiempos(q9):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.3, 2.95), sharey=True)
    for spec in ORDENES:
        xs = [q9[str(N)]["n"] for N in NS_Q9 if spec in q9[str(N)]["orden"]]
        ys = [q9[str(N)]["orden"][spec]["t"] for N in NS_Q9 if spec in q9[str(N)]["orden"]]
        a1.plot(xs, ys, color=COLOR[spec], marker=MARCA[spec], lw=1.4, ms=4.6, mec="white",
                mew=0.7, zorder=3, label=ETIQUETA[spec])
    a1.set_title("(a) Ordenamientos de SuperLU", loc="left")
    series_b = [("SuperLU + MMD_AT_PLUS_A", AZUL, "o", [q9[str(N)]["orden"]["MMD_AT_PLUS_A"]["t"] for N in NS_Q9],
                 [q9[str(N)]["n"] for N in NS_Q9]),
                ("LU densa (numpy.linalg.solve)", MAGENTA, "v",
                 [q9[str(N)]["t_solve"] for N in NS_DENSO if "t_solve" in q9[str(N)]],
                 [q9[str(N)]["n"] for N in NS_DENSO if "t_solve" in q9[str(N)]]),
                ("inversa densa, K⁻¹ F", VERDE, "X",
                 [q9[str(N)]["t_inv"] for N in NS_DENSO if "t_inv" in q9[str(N)]],
                 [q9[str(N)]["n"] for N in NS_DENSO if "t_inv" in q9[str(N)]])]
    for nombre, color, marca, ys, xs in series_b:
        a2.plot(xs, ys, color=color, marker=marca, lw=1.4, ms=4.8, mec="white", mew=0.7, zorder=3,
                label=nombre)
    a2.set_title("(b) Disperso frente a denso", loc="left")
    # Pendientes de referencia (guía de lectura en ejes log-log), recortadas al
    # área visible y rotuladas dentro de ella.
    Y_MAX = 3e2
    x0 = q9[str(NS_DENSO[0])]["n"]
    t0_inv = q9[str(NS_DENSO[0])]["t_inv"] * 1.6
    x_tope = x0 * (Y_MAX / t0_inv) ** (1 / 3)
    xr = np.array([x0, x_tope])
    a2.plot(xr, t0_inv * (xr / x0) ** 3, color=TENUE, lw=0.8, ls=(0, (2, 2)), zorder=1)
    x_lab = x0 * (25.0 / t0_inv) ** (1 / 3)
    a2.text(x_lab * 0.9, 25.0, r"$\propto n^{3}$", color=TENUE, fontsize=7.5, ha="right", va="center")
    t0_sp = q9[str(NS_Q9[0])]["orden"]["MMD_AT_PLUS_A"]["t"] * 0.45
    xs = np.array([x0, 45000.0])
    a2.plot(xs, t0_sp * (xs / x0) ** 1.5, color=TENUE, lw=0.8, ls=(0, (2, 2)), zorder=1)
    x_lab = 9000.0
    a2.text(x_lab, t0_sp * (x_lab / x0) ** 1.5 * 0.45, r"$\propto n^{3/2}$", color=TENUE, fontsize=7.5,
            ha="left", va="top")
    for ax in (a1, a2):
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(420, 45000)
        ax.set_ylim(8e-4, Y_MAX)
        ax.grid(True, which="major", color=GRILLA, lw=0.5)
        ax.set_axisbelow(True)
        estilo_ejes(ax)
        ax.set_xlabel("GDL libres, n")
        ns = [q9[str(N)]["n"] for N in NS_Q9]
        ax.set_xticks(ns, [texto_plano(entero(v)) for v in ns])
        ax.minorticks_off()
        ax.tick_params(axis="x", labelsize=6.5)
    a1.set_ylabel("tiempo de solución (s)")
    a1.set_yticks([1e-3, 1e-2, 1e-1, 1, 10, 100], ["0,001", "0,01", "0,1", "1", "10", "100"])
    h1, l1 = a1.get_legend_handles_labels()
    h2, l2 = a2.get_legend_handles_labels()
    fig.legend(h1 + h2[1:], l1 + l2[1:], loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(0.5, -0.01), handlelength=2.0, columnspacing=1.2)
    fig.tight_layout(rect=(0, 0.14, 1, 1), w_pad=1.2)
    fig.savefig(FIG / "tiempos.pdf")
    plt.close(fig)


# ─── 5. Escritura de cifras y tablas ──────────────────────────────────────

def escribir(med, traza, malla, llenado8):
    c = {}

    def put(k, v):
        c[k] = v

    put("scipy", scipy.__version__)
    put("numpy", np.__version__)
    put("python", platform.python_version())
    put("fecha", med["fecha"])
    put("permc", SOLVER_PERMC_SPEC.replace("_", r"\_"))
    for N in NS_Q9:
        r = med["q9"][str(N)]
        k = f"q9:{N}:"
        for campo in ("nodos", "elementos", "gdl", "restr", "n", "tripletes", "nnzK", "nnzKr",
                      "maxfila", "nnzAtA", "maxfilaAtA"):
            put(k + campo, entero(r[campo]))
        put(k + "duplicados", entero(r["tripletes"] - r["nnzK"]))
        put(k + "densK", decimal(100 * r["nnzK"] / r["gdl"] ** 2, 2))
        put(k + "densKr", decimal(100 * r["nnzKr"] / r["n"] ** 2, 2))
        put(k + "razonAtA", decimal(r["nnzAtA"] / r["nnzKr"], 1))
        put(k + "mbKr", sig(r["bytesKr"] / 1e6, 2))
        put(k + "mbDenso", sig(8 * r["n"] ** 2 / 1e6, 2))
        put(k + "gbInv", decimal(8 * r["n"] ** 2 / 1e9, 1))
        for spec, o in r["orden"].items():
            put(k + "lu:" + spec, entero(o["nnzLU"]))
            put(k + "rel:" + spec, decimal(o["relleno"], 1))
            put(k + "t:" + spec, sig(o["t"], 2))
            put(k + "ms:" + spec, sig(1000 * o["t"], 2))
            put(k + "piv:" + spec, entero(o["piv"]))
            if "flops" in o:
                put(k + "flops:" + spec, cientifico(o["flops"]))
        put(k + "flopsDensa", cientifico(2 * r["n"] ** 3 / 3))
        put(k + "flopsInv", cientifico(2 * r["n"] ** 3))
        m = r["orden"]["MMD_AT_PLUS_A"]
        if "flops" in m:
            put(k + "gflops", sig(m["flops"] / m["t"] / 1e9, 2))
            put(k + "xflopsDensa", sig(2 * r["n"] ** 3 / 3 / m["flops"], 2))
            for spec in ("NATURAL", "COLAMD", "MMD_ATA"):
                if spec in r["orden"] and "flops" in r["orden"][spec]:
                    put(k + "xflops:" + spec, decimal(r["orden"][spec]["flops"] / m["flops"], 1)
                        if r["orden"][spec]["flops"] / m["flops"] < 100
                        else entero(round(r["orden"][spec]["flops"] / m["flops"])))
        put(k + "mbLU", sig(12 * m["nnzLU"] / 1e6, 2))
        if "nnzL" in m:
            put(k + "nnzL", entero(m["nnzL"]))
            put(k + "nnzU", entero(m["nnzU"]))
            put(k + "LigualU", "sí" if m["nnzL"] == m["nnzU"] else "no")
        put(k + "sn:media", decimal(m["sn_media"], 1))
        put(k + "sn:max", entero(m["sn_max"]))
        put(k + "sn:mayor1", decimal(100 * m["sn_mayor1"], 0))
        put(k + "lu0", entero(m["nnzLU_umbral0"]))
        put(k + "piv0", entero(m["piv_umbral0"]))
        put(k + "pivpct", decimal(100 * m["piv"] / r["n"], 1))
        for spec in ("NATURAL", "COLAMD", "MMD_ATA"):
            if spec in r["orden"]:
                put(k + "x:" + spec, decimal(r["orden"][spec]["t"] / m["t"], 1)
                    if r["orden"][spec]["t"] / m["t"] < 100 else entero(round(r["orden"][spec]["t"] / m["t"])))
                put(k + "xlu:" + spec, decimal(r["orden"][spec]["nnzLU"] / m["nnzLU"], 1))
        if "t_solve" in r:
            put(k + "tsolve", sig(r["t_solve"], 2))
            put(k + "tinv", sig(r["t_inv"], 2))
            put(k + "xsolve", entero(round(r["t_solve"] / m["t"])))
            put(k + "xinv", entero(round(r["t_inv"] / m["t"])))
            put(k + "xinvsolve", decimal(r["t_inv"] / r["t_solve"], 1))
            put(k + "res:sp", cientifico(r["res_sp"]))
            put(k + "res:solve", cientifico(r["res_solve"]))
            put(k + "res:inv", cientifico(r["res_inv"]))
            put(k + "difinv", cientifico(r["dif_inv"]))
            put(k + "densInv", decimal(100 * r["dens_inv"], 0))
            put(k + "cerosInv", entero(r["ceros_inv"]))
        if "cond" in r:
            put(k + "cond", cientifico(r["cond"]))
    # Exponentes de crecimiento medidos: t ~ n^p entre la malla menor y la mayor.
    def expo(t1, t2, n1, n2):
        return math.log(t2 / t1) / math.log(n2 / n1)

    q, a, z = med["q9"], str(NS_Q9[0]), str(NS_Q9[-1])
    put("expo:MMD", decimal(expo(q[a]["orden"]["MMD_AT_PLUS_A"]["t"], q[z]["orden"]["MMD_AT_PLUS_A"]["t"],
                                 q[a]["n"], q[z]["n"]), 1))
    put("expo:relleno", decimal(expo(q[a]["orden"]["MMD_AT_PLUS_A"]["nnzLU"], q[z]["orden"]["MMD_AT_PLUS_A"]["nnzLU"],
                                     q[a]["n"], q[z]["n"]), 2))
    dz = str(max(N for N in NS_DENSO if "t_inv" in q[str(N)]))
    put("expo:inv", decimal(expo(q[a]["t_inv"], q[dz]["t_inv"], q[a]["n"], q[dz]["n"]), 1))
    put("expo:solve", decimal(expo(q[a]["t_solve"], q[dz]["t_solve"], q[a]["n"], q[dz]["n"]), 1))
    put("crece:n", entero(round(q[z]["n"] / q[a]["n"])))
    put("crece:t", entero(round(q[z]["orden"]["MMD_AT_PLUS_A"]["t"] / q[a]["orden"]["MMD_AT_PLUS_A"]["t"])))
    if "flops" in q[a]["orden"]["MMD_AT_PLUS_A"]:
        fa, fz = q[a]["orden"]["MMD_AT_PLUS_A"]["flops"], q[z]["orden"]["MMD_AT_PLUS_A"]["flops"]
        put("expo:flops", decimal(expo(fa, fz, q[a]["n"], q[z]["n"]), 2))
        put("crece:flops", entero(round(fz / fa)))
    put("equipo", med.get("equipo", "").replace("_", r"\_"))

    for N in NS_Q4:
        r = med["q4"][str(N)]
        k = f"q4:{N}:"
        for campo in ("n", "nnzKr", "maxfila", "nnzAtA", "maxfilaAtA"):
            put(k + campo, entero(r[campo]))
        put(k + "razonAtA", decimal(r["nnzAtA"] / r["nnzKr"], 1))
        for spec, o in r["orden"].items():
            put(k + "lu:" + spec, entero(o["nnzLU"]))
            put(k + "rel:" + spec, decimal(o["relleno"], 1))
            put(k + "t:" + spec, sig(o["t"], 2))
    put("traza:uyC", decimal(traza["uyC"], 2))
    put("traza:uyRef", decimal(traza["uyRef"], 2) if traza["uyRef"] is not None else "---")
    put("traza:resid", cientifico(traza["resid"]))
    put("traza:sumRy", decimal(traza["sumRy"], 4))
    put("traza:sumFy", decimal(traza["sumFy"], 4))
    put("traza:sumRx", cientifico(abs(traza["sumRx"])) if abs(traza["sumRx"]) > 0 else "0")
    put("malla:nnz", entero(malla["nnz"]))
    put("malla:ceros", entero(malla["ceros"]))
    put("q9:8:figLU:NATURAL", entero(llenado8["NATURAL"]))
    put("q9:8:figLU:MMD", entero(llenado8["MMD_AT_PLUS_A"]))

    lineas = ["% Generado por generar_datos.py: no editar a mano."]
    for k, v in c.items():
        lineas.append(rf"\expandafter\def\csname cifra:{k}\endcsname{{{v}}}")
    (DAT / "cifras.tex").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # Tabla de llenado y de tiempos (Q9, membrana de Cook).
    fl, ft = [], []
    for N in NS_Q9:
        r = med["q9"][str(N)]
        m = r["orden"]["MMD_AT_PLUS_A"]
        celdas_l, celdas_t = [], []
        for spec in ORDENES:
            o = r["orden"].get(spec)
            if o is None:
                celdas_l.append("---")
                celdas_t.append("---")
                continue
            fuerte = spec == "MMD_AT_PLUS_A"
            rel = decimal(o["relleno"], 1)
            celdas_l.append(rf"\textbf{{{rel}}}" if fuerte else rel)
            celdas_t.append(rf"\textbf{{{sig(o['t'], 2)}}}" if fuerte else sig(o["t"], 2))
        fl.append(f"{entero(r['n'])} & {entero(r['nnzKr'])} & " + " & ".join(celdas_l)
                  + f" & {entero(m['nnzLU'])} & {cientifico(m['flops'])}" + r" \\")
        ft.append(f"{entero(r['n'])} & " + " & ".join(celdas_t)
                  + f" & {decimal(r['orden']['COLAMD']['t'] / m['t'], 1)}" + r" \\")
    (DAT / "tabla_llenado_q9.tex").write_text("% Generado\n" + "\n".join(fl) + "\n", encoding="utf-8")
    (DAT / "tabla_tiempo_q9.tex").write_text("% Generado\n" + "\n".join(ft) + "\n", encoding="utf-8")

    fq = []
    for N in NS_Q4:
        r = med["q4"][str(N)]
        celdas = []
        for spec in ORDENES:
            o = r["orden"][spec]
            celdas.append(rf"\textbf{{{decimal(o['relleno'], 1)}}}" if spec == "MMD_AT_PLUS_A"
                          else decimal(o["relleno"], 1))
        rq9 = med["q9"][str(N // 2)]
        fq.append(f"{entero(r['n'])} & {entero(r['nnzKr'])} & " + " & ".join(celdas)
                  + f" & {decimal(rq9['orden']['NATURAL']['relleno'], 1) if 'NATURAL' in rq9['orden'] else '---'}"
                  + r" \\")
    (DAT / "tabla_q4.tex").write_text("% Generado\n" + "\n".join(fq) + "\n", encoding="utf-8")

    fd = []
    for N in NS_DENSO:
        r = med["q9"][str(N)]
        if "t_solve" not in r:
            continue
        fd.append(f"{entero(r['n'])} & {sig(r['orden']['MMD_AT_PLUS_A']['t'], 2)} & {sig(r['t_solve'], 2)} & "
                  f"{sig(r['t_inv'], 2)} & {cientifico(r['res_sp'])} & {cientifico(r['res_solve'])} & "
                  f"{cientifico(r['res_inv'])} & {decimal(100 * r['dens_inv'], 0)}\\,\\% \\\\")
    (DAT / "tabla_denso.tex").write_text("% Generado\n" + "\n".join(fd) + "\n", encoding="utf-8")


# ─── Programa principal ───────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rapido", action="store_true",
                    help="omite los casos de más de 10 s (orden natural grande, inversa de 4704 GDL)")
    ap.add_argument("--solo-figuras", action="store_true",
                    help="reusa datos/mediciones.json en vez de volver a medir")
    args = ap.parse_args()
    FIG.mkdir(exist_ok=True)
    DAT.mkdir(exist_ok=True)

    print("1) Ejemplos a mano")
    verificar_ejemplos()
    print("2) Mínimo grado en la malla 2x2")
    figuras_minimo_grado()

    ruta_json = DAT / "mediciones.json"
    if args.solo_figuras and ruta_json.exists():
        med = json.loads(ruta_json.read_text(encoding="utf-8"))
    else:
        print("3) Mediciones (membrana de Cook)")
        med = {"fecha": time.strftime("%Y-%m-%d"), "equipo": platform.processor(),
               "python": platform.python_version(), "scipy": scipy.__version__,
               "numpy": np.__version__, "q9": {}, "q4": {}}
        for N in NS_Q9:
            t0 = time.perf_counter()
            med["q9"][str(N)] = medir(N, ELEMENT_Q9, args.rapido, denso=N in NS_DENSO)
            print(f"   Q9 N={N:>2}: n={med['q9'][str(N)]['n']:>6}  ({time.perf_counter() - t0:.0f} s)")
        for N in NS_Q4:
            med["q4"][str(N)] = medir(N, ELEMENT_Q4, args.rapido, denso=False)
            print(f"   Q4 N={N:>2}: n={med['q4'][str(N)]['n']:>6}")
        ruta_json.write_text(json.dumps(med, indent=1), encoding="utf-8")

    print("4) Figuras")
    traza = traza_cook8()
    malla = figura_malla_patron()
    llenado8 = figura_llenado_cook()
    figura_tiempos(med["q9"])
    escribir(med, traza, malla, llenado8)
    print(f"Listo: {DAT / 'cifras.tex'} y {FIG}")


if __name__ == "__main__":
    main()
