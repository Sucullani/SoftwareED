"""
mms_independiente.py - Replica independiente del MMS de EduFEM.

No importa nada del repositorio: la malla, las funciones de forma, la rigidez,
la fuerza de cuerpo, las restricciones, la solucion y las normas de error estan
escritas desde cero con NumPy/SciPy, elemento por elemento. Si las cifras que
imprime coinciden con docs/vyv/datos/mms_q4.csv y mms_q9.csv, esta replica y
el motor de EduFEM coinciden.

Configuracion base de la tesis: cuadrado unitario, tension plana,
E = 1, nu = 0,3, t = 1, mallas N x N con N = 2, 4, 8, 16, 32.

Ejecutar:  python mms_independiente.py        (tarda unos 20 s)
"""
import math

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

E, NU, T = 1.0, 0.3, 1.0
MU = E / (2.0 * (1.0 + NU))
PI = math.pi

# Matriz constitutiva de tension plana.
D = E / (1.0 - NU ** 2) * np.array([[1.0, NU, 0.0],
                                    [NU, 1.0, 0.0],
                                    [0.0, 0.0, (1.0 - NU) / 2.0]])


# --- Paso 3: la solucion inventada, su gradiente y la carga que la produce ---
def u_M(x, y):
    return np.array([math.sin(PI * x) * math.sin(PI * y),
                     math.cos(PI * x) * math.cos(PI * y)])


def grad_u_M(x, y):
    """[[du/dx, du/dy], [dv/dx, dv/dy]]."""
    sx, cx = math.sin(PI * x), math.cos(PI * x)
    sy, cy = math.sin(PI * y), math.cos(PI * y)
    return np.array([[PI * cx * sy, PI * sx * cy],
                     [-PI * sx * cy, -PI * cx * sy]])


def b(x, y):
    """b = -div(sigma(u_M)). Con esta u_M, tr(eps) = 0 y gamma_xy = 0,
    de modo que sigma = 2 mu eps y b = 2 mu pi^2 u_M."""
    return 2.0 * MU * PI ** 2 * u_M(x, y)


# --- Funciones de forma de Lagrange (p = 1 -> Q4, p = 2 -> Q9) ---------------
def lagrange_1d(p, s):
    """Polinomios de Lagrange 1D en los nodos equiespaciados de [-1, 1] y sus derivadas."""
    nodos = np.linspace(-1.0, 1.0, p + 1)
    L = np.ones(p + 1)
    dL = np.zeros(p + 1)
    for i in range(p + 1):
        for j in range(p + 1):
            if j != i:
                L[i] *= (s - nodos[j]) / (nodos[i] - nodos[j])
        for k in range(p + 1):
            if k == i:
                continue
            termino = 1.0 / (nodos[i] - nodos[k])
            for j in range(p + 1):
                if j != i and j != k:
                    termino *= (s - nodos[j]) / (nodos[i] - nodos[j])
            dL[i] += termino
    return L, dL


def forma_2d(p, xi, eta):
    """N, dN/dxi, dN/deta; el nodo local (a, b) lleva el indice b*(p+1) + a."""
    Lx, dLx = lagrange_1d(p, xi)
    Ly, dLy = lagrange_1d(p, eta)
    return np.outer(Ly, Lx).ravel(), np.outer(Ly, dLx).ravel(), np.outer(dLy, Lx).ravel()


def puntos_gauss(n):
    """Producto tensorial de Gauss-Legendre n x n: lista de (xi, eta, peso)."""
    pts, wts = np.polynomial.legendre.leggauss(n)
    return [(xi, eta, wi * wj) for xi, wi in zip(pts, wts) for eta, wj in zip(pts, wts)]


def geometria(xy_e, dNxi, dNeta):
    """det J y derivadas fisicas dN/dx, dN/dy en un punto."""
    J = np.array([[dNxi @ xy_e[:, 0], dNxi @ xy_e[:, 1]],
                  [dNeta @ xy_e[:, 0], dNeta @ xy_e[:, 1]]])
    det_J = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
    dNx, dNy = np.linalg.solve(J, np.vstack([dNxi, dNeta]))
    return det_J, dNx, dNy


def gdl_de(nodos):
    return np.ravel([[2 * n, 2 * n + 1] for n in nodos])


# --- Malla estructurada N x N de [0,1]^2 ------------------------------------
def malla(N, p):
    m = p * N + 1                                  # nodos por lado
    coords = np.array([(i / (p * N), j / (p * N)) for j in range(m) for i in range(m)])
    elems = [[(ey * p + bb) * m + (ex * p + aa) for bb in range(p + 1) for aa in range(p + 1)]
             for ey in range(N) for ex in range(N)]
    borde = [j * m + i for j in range(m) for i in range(m) if i in (0, m - 1) or j in (0, m - 1)]
    return coords, np.array(elems), borde


# --- Paso 4: ensamblar, imponer u = u_M en el borde y resolver ---------------
def resolver(N, p):
    coords, elems, borde = malla(N, p)
    n_gdl = 2 * len(coords)
    # Gauss (p+1) x (p+1): 2x2 en Q4 y 3x3 en Q9, el mismo orden que la K del motor.
    gp = [(forma_2d(p, xi, eta), w) for xi, eta, w in puntos_gauss(p + 1)]
    filas, cols, vals = [], [], []
    F = np.zeros(n_gdl)
    for conn in elems:
        xy_e = coords[conn]
        gdl = gdl_de(conn)
        ke = np.zeros((len(gdl), len(gdl)))
        fe = np.zeros(len(gdl))
        for (N_, dNxi, dNeta), w in gp:
            det_J, dNx, dNy = geometria(xy_e, dNxi, dNeta)
            B = np.zeros((3, len(gdl)))
            B[0, 0::2] = dNx
            B[1, 1::2] = dNy
            B[2, 0::2] = dNy
            B[2, 1::2] = dNx
            ke += B.T @ D @ B * det_J * w * T
            bx, by = b(N_ @ xy_e[:, 0], N_ @ xy_e[:, 1])
            fe[0::2] += N_ * bx * det_J * w * T
            fe[1::2] += N_ * by * det_J * w * T
        filas.append(np.repeat(gdl, len(gdl)))
        cols.append(np.tile(gdl, len(gdl)))
        vals.append(ke.ravel())
        F[gdl] += fe
    K = coo_matrix((np.concatenate(vals), (np.concatenate(filas), np.concatenate(cols))),
                   shape=(n_gdl, n_gdl)).tocsr()

    # Restricciones de Dirichlet NO homogeneas: u = u_M en todos los nodos del borde.
    u = np.zeros(n_gdl)
    for n in borde:
        u[2 * n:2 * n + 2] = u_M(*coords[n])
    r = gdl_de(borde)
    f = np.setdiff1d(np.arange(n_gdl), r)
    # K_ff u_f = F_f - K_fr u_r   (sustitucion estatica del bloque restringido)
    u[f] = spsolve(K[f][:, f].tocsc(), F[f] - K[f][:, r] @ u[r])
    return coords, elems, u


# --- Paso 5: normas del error, con Gauss un orden por encima -----------------
def normas(coords, elems, u, p):
    """Norma L2 y seminorma H1 del error, y norma L2 de u_M (Gauss 3x3 en Q4, 4x4 en Q9)."""
    gp = [(forma_2d(p, xi, eta), w) for xi, eta, w in puntos_gauss(p + 2)]
    sq_L2 = sq_H1 = sq_exacta = area = 0.0
    for conn in elems:
        xy_e = coords[conn]
        u_e = u[gdl_de(conn)].reshape(-1, 2)          # (n_nodos, 2)
        for (N_, dNxi, dNeta), w in gp:
            det_J, dNx, dNy = geometria(xy_e, dNxi, dNeta)
            x, y = N_ @ xy_e[:, 0], N_ @ xy_e[:, 1]
            u_h = N_ @ u_e
            grad_h = np.array([[dNx @ u_e[:, 0], dNy @ u_e[:, 0]],
                               [dNx @ u_e[:, 1], dNy @ u_e[:, 1]]])
            dA = abs(det_J) * w
            sq_L2 += np.sum((u_h - u_M(x, y)) ** 2) * dA
            sq_H1 += np.sum((grad_h - grad_u_M(x, y)) ** 2) * dA
            sq_exacta += np.sum(u_M(x, y) ** 2) * dA
            area += dA
    h = math.sqrt(area / len(elems))
    return h, math.sqrt(sq_L2), math.sqrt(sq_H1), math.sqrt(sq_exacta)


# --- Paso 6: tasas de convergencia --------------------------------------------
if __name__ == "__main__":
    coords, elems, u = resolver(2, 1)
    print(f"Q4, N = 2: u en el nodo central = ({u[8]:.6f}, {u[9]:.6f})   exacta = (1, 0)")
    for p, nombre in ((1, "Q4"), (2, "Q9")):
        print(f"\n{nombre}    N        h     GDL        L2           H1     tasa L2  tasa H1")
        previo = None
        for N in (2, 4, 8, 16, 32):
            coords, elems, u = resolver(N, p)
            h, L2, H1, _ = normas(coords, elems, u, p)
            tasas = ""
            if previo is not None:
                lh = math.log(previo[0] / h)
                tasas = (f"{math.log(previo[1] / L2) / lh:8.3f} "
                         f"{math.log(previo[2] / H1) / lh:8.3f}")
            print(f"    {N:5d}  {h:.5f}  {len(u):6d}  {L2:.6e}  {H1:.6e} {tasas}")
            previo = (h, L2, H1)
