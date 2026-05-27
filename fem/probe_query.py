"""
Consulta de resultados FEM en cualquier punto de la malla.

Modulo puro NumPy (sin imports de Tk / matplotlib / ttkbootstrap). Es
reusable desde la UI, scripts headless, Jupyter o un futuro frontend web.

API principal:
    - inverse_iso_map_NR(x, y, node_coords, element_type)
          Newton-Raphson clasico para hallar (xi, eta) tal que
          T(xi, eta) = (x, y). Sin line search, sin multi-start: el
          validador `model_health` filtra elementos patologicos antes
          del solve, asi que el centroide es semilla suficiente.

    - compute_raw(project, solution, elem_id, xi, eta)
          Esfuerzo CRUDO en (xi, eta) via sigma = D * B(xi, eta) * u_e.
          Discontinuo entre elementos (naturaleza C0 del MEF Galerkin).

    - compute_smooth(project, nodal_stresses, elem_id, xi, eta)
          Esfuerzo SUAVIZADO via sigma = sum N_i(xi, eta) * sigma_i_avg.
          Continuo entre elementos. Coincide con el contorno renderizado.

    - displacement_at(project, solution, elem_id, xi, eta)
          (ux, uy) interpolados via N_i(xi, eta).

    - gauss_physical_coords(project, elem_id, element_stresses)
          Coordenadas fisicas (x, y) de los puntos de Gauss del elemento
          + valores oficiales del solver en cada uno. Usado para el
          render de marcadores y el snap-to-Gauss.

Referencias:
    - Hua, C. (1990). "An inverse transformation for quadrilateral
      isoparametric elements: analysis and application".
      Finite Elements in Analysis and Design 7(2), 159-166.
    - Bathe, K-J. (2014). Finite Element Procedures, 2nd ed. Cap. 5.
    - Barlow, J. (1976). "Optimal stress locations in finite element
      models". IJNME 10(2), 243-251. -- justifica gauss_physical_coords.
    - Hinton, E. & Campbell, J. S. (1974). "Local and global smoothing
      of discontinuous finite element functions using a least squares
      method". IJNME 8(3), 461-480. -- base de compute_smooth.
"""

from __future__ import annotations

import math
import numpy as np

from config.settings import NUMERICAL_TOLERANCE, JACOBIAN_MIN_DETERMINANT
from fem.shape_functions import get_shape_functions
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix
from fem._numba_compat import njit


@njit(cache=True)
def _compute_raw_grid_njit(dN_at_grid, coords_used, D, u_e):
    """Kernel JIT de `compute_raw_grid`: evalua sigma en cada (xi, eta)
    de la grilla (side x side) sin allocations intermedias.

    Parametros:
        dN_at_grid: (side, side, 2, n_nodes) — derivadas naturales en cada
            punto de la grilla (precomputadas).
        coords_used: (n_nodes, 2) — coords (x, y) de los nodos.
        D: (3, 3) — matriz constitutiva.
        u_e: (2 * n_nodes,) — desplazamientos del elemento.

    Retorna (sx_g, sy_g, txy_g, s1_g, s2_g, vm_g), cada uno (side, side).

    Optimizacion: en vez de armar B (3 x 2*n_nodes) y hacer B @ u, calcula
    strain directamente desde dN_phys y u (B es solo un reorden, no aporta
    aritmetica). Ahorra ~6*n_nodes alloca/iter y elimina el `B[:] = 0.0`.
    """
    side = dN_at_grid.shape[0]
    n_nodes = coords_used.shape[0]

    sx_g = np.zeros((side, side))
    sy_g = np.zeros((side, side))
    txy_g = np.zeros((side, side))
    s1_g = np.zeros((side, side))
    s2_g = np.zeros((side, side))
    vm_g = np.zeros((side, side))

    for i in range(side):
        for j in range(side):
            dN_nat = dN_at_grid[i, j]

            # J = dN_nat @ coords_used (2x2)
            J00 = 0.0; J01 = 0.0; J10 = 0.0; J11 = 0.0
            for k in range(n_nodes):
                J00 += dN_nat[0, k] * coords_used[k, 0]
                J01 += dN_nat[0, k] * coords_used[k, 1]
                J10 += dN_nat[1, k] * coords_used[k, 0]
                J11 += dN_nat[1, k] * coords_used[k, 1]
            det_J = J00 * J11 - J01 * J10
            if abs(det_J) < JACOBIAN_MIN_DETERMINANT:
                continue

            inv_d = 1.0 / det_J
            invJ00 =  J11 * inv_d
            invJ01 = -J01 * inv_d
            invJ10 = -J10 * inv_d
            invJ11 =  J00 * inv_d

            # Strain = B @ u_e desplegado: B[0,:]=[dphx_k, 0, ...],
            # B[1,:]=[0, dphy_k, ...], B[2,:]=[dphy_k, dphx_k, ...].
            ex = 0.0; ey = 0.0; gxy = 0.0
            for k in range(n_nodes):
                dphx = invJ00 * dN_nat[0, k] + invJ01 * dN_nat[1, k]
                dphy = invJ10 * dN_nat[0, k] + invJ11 * dN_nat[1, k]
                u_x = u_e[2 * k]
                u_y = u_e[2 * k + 1]
                ex  += dphx * u_x
                ey  += dphy * u_y
                gxy += dphy * u_x + dphx * u_y

            # sigma = D @ strain
            sx = D[0, 0] * ex + D[0, 1] * ey + D[0, 2] * gxy
            sy = D[1, 0] * ex + D[1, 1] * ey + D[1, 2] * gxy
            txy = D[2, 0] * ex + D[2, 1] * ey + D[2, 2] * gxy

            sigma_avg = 0.5 * (sx + sy)
            R = math.sqrt(0.25 * (sx - sy) * (sx - sy) + txy * txy)
            s1 = sigma_avg + R
            s2 = sigma_avg - R
            vm = math.sqrt(s1 * s1 - s1 * s2 + s2 * s2)

            sx_g[i, j] = sx
            sy_g[i, j] = sy
            txy_g[i, j] = txy
            s1_g[i, j] = s1
            s2_g[i, j] = s2
            vm_g[i, j] = vm

    return sx_g, sy_g, txy_g, s1_g, s2_g, vm_g


# Cache de dN evaluado en la grilla (n+1, n+1) por (element_type, n).
# La grilla es fija — para n=6 cada elemento la consume identica.
_DN_AT_GRID_CACHE: dict = {}


def _get_dN_at_grid(element_type, n):
    """Retorna dN_at_grid shape (side, side, 2, n_nodes) — derivadas
    naturales evaluadas en cada punto de la grilla (n+1) x (n+1).
    Cacheado por (element_type, n).
    """
    key = (element_type, n)
    cached = _DN_AT_GRID_CACHE.get(key)
    if cached is not None:
        return cached

    _, dN_func = get_shape_functions(element_type)
    side = n + 1
    xis = np.linspace(-1.0, 1.0, side)
    etas = np.linspace(-1.0, 1.0, side)
    # Evaluar una vez para obtener n_nodes.
    dN_first = dN_func(0.0, 0.0)
    n_nodes_full = dN_first.shape[1]

    dN_at_grid = np.empty((side, side, 2, n_nodes_full))
    for i, xi in enumerate(xis):
        for j, eta in enumerate(etas):
            dN_at_grid[i, j] = dN_func(xi, eta)

    _DN_AT_GRID_CACHE[key] = dN_at_grid
    return dN_at_grid


__all__ = [
    "inverse_iso_map_NR",
    "compute_raw",
    "compute_raw_grid",
    "compute_smooth",
    "crude_values_at_node",
    "displacement_at",
    "gauss_physical_coords",
    "locate_point",
    "principal_and_vm",
]


def locate_point(project, x: float, y: float, tol: float = 1e-6):
    """Halla el elemento que contiene el punto fisico (x, y) y devuelve
    (elem_id, xi, eta). None si el punto no esta dentro de ningun elemento.

    Estrategia: loop sobre elementos, intenta `inverse_iso_map_NR`. Si
    converge a (xi, eta) en [-1-tol, 1+tol]^2, devuelve el primer hit.
    """
    if not project.elements:
        return None
    element_type = project.element_type
    for elem_id, elem in project.elements.items():
        coords = np.array(
            [[project.nodes[nid].x, project.nodes[nid].y]
             for nid in elem.node_ids],
            dtype=float,
        )
        result = inverse_iso_map_NR(x, y, coords, element_type)
        if result is None:
            continue
        xi, eta = result
        if -1.0 - tol <= xi <= 1.0 + tol and -1.0 - tol <= eta <= 1.0 + tol:
            return elem_id, float(xi), float(eta)
    return None


# ─── Inversion isoparametrica (Newton-Raphson clasico) ─────────────────────

# Flags internos para el kernel JIT (Numba no maneja strings bien).
_FLAG_Q4 = 0
_FLAG_Q9 = 1


@njit(cache=True)
def _inverse_iso_map_q4_njit(x_p, y_p, coords, tol, max_iter):
    """Newton-Raphson para Q4. Returns (success, xi, eta).

    success=False indica no-convergencia / singular / fuera del maestro.
    """
    xi = 0.0
    eta = 0.0
    for _ in range(max_iter):
        # N(xi, eta) y Fx, Fy
        N0 = 0.25 * (1.0 - xi) * (1.0 - eta)
        N1 = 0.25 * (1.0 + xi) * (1.0 - eta)
        N2 = 0.25 * (1.0 + xi) * (1.0 + eta)
        N3 = 0.25 * (1.0 - xi) * (1.0 + eta)
        Fx = (N0 * coords[0, 0] + N1 * coords[1, 0]
              + N2 * coords[2, 0] + N3 * coords[3, 0]) - x_p
        Fy = (N0 * coords[0, 1] + N1 * coords[1, 1]
              + N2 * coords[2, 1] + N3 * coords[3, 1]) - y_p

        if math.sqrt(Fx * Fx + Fy * Fy) < tol:
            if abs(xi) > 1.05 or abs(eta) > 1.05:
                return False, 0.0, 0.0
            return True, xi, eta

        # dN/dxi, dN/deta (4 entries cada uno)
        dNx0 = -0.25 * (1.0 - eta)
        dNx1 =  0.25 * (1.0 - eta)
        dNx2 =  0.25 * (1.0 + eta)
        dNx3 = -0.25 * (1.0 + eta)
        dNe0 = -0.25 * (1.0 - xi)
        dNe1 = -0.25 * (1.0 + xi)
        dNe2 =  0.25 * (1.0 + xi)
        dNe3 =  0.25 * (1.0 - xi)

        # J = dN @ coords. Fila 0: dx/dxi, dy/dxi. Fila 1: dx/deta, dy/deta.
        J00 = (dNx0 * coords[0, 0] + dNx1 * coords[1, 0]
               + dNx2 * coords[2, 0] + dNx3 * coords[3, 0])
        J01 = (dNx0 * coords[0, 1] + dNx1 * coords[1, 1]
               + dNx2 * coords[2, 1] + dNx3 * coords[3, 1])
        J10 = (dNe0 * coords[0, 0] + dNe1 * coords[1, 0]
               + dNe2 * coords[2, 0] + dNe3 * coords[3, 0])
        J11 = (dNe0 * coords[0, 1] + dNe1 * coords[1, 1]
               + dNe2 * coords[2, 1] + dNe3 * coords[3, 1])

        det_J = J00 * J11 - J01 * J10
        if abs(det_J) < JACOBIAN_MIN_DETERMINANT:
            return False, 0.0, 0.0

        inv_det = 1.0 / det_J
        d_xi  = -inv_det * ( J11 * Fx - J10 * Fy)
        d_eta = -inv_det * (-J01 * Fx + J00 * Fy)
        xi += d_xi
        eta += d_eta

        if abs(xi) > 5.0 or abs(eta) > 5.0:
            return False, 0.0, 0.0

    return False, 0.0, 0.0


def inverse_iso_map_NR(
    x_p: float,
    y_p: float,
    node_coords: np.ndarray,
    element_type: str,
    tol: float = NUMERICAL_TOLERANCE,
    max_iter: int = 25,
):
    """Resuelve T(xi, eta) = (x_p, y_p) por Newton-Raphson clasico.

    Inicializacion: centroide del maestro (0, 0). Sufijo `_NR` solo para
    distinguir esta version robusta de la legacy en
    `education/components/iso_inverse.py` (que se mantiene para fines
    didacticos en M0..M9, ver convencion del CLAUDE.md).

    Para Q4 usa el kernel JIT `_inverse_iso_map_q4_njit` (sin allocations).
    Para Q9 cae al path NumPy con `get_shape_functions` (uso poco frecuente,
    no justifica un kernel separado).

    Parametros:
        x_p, y_p: punto fisico consultado.
        node_coords: array (n_nodes, 2) con coords de los nodos en el
            orden de element.node_ids. n_nodes = 4 (Q4) o 9 (Q9).
        element_type: cadena ELEMENT_Q4 o ELEMENT_Q9.
        tol: criterio de convergencia ||F|| < tol.
        max_iter: tope de iteraciones (25 holgado para convergencia
            cuadratica).

    Retorna:
        (xi, eta) si converge dentro del maestro [-1.05, 1.05]^2 (margen
        5% para tolerar clicks sobre el borde). None si:
            - no converge en max_iter
            - el jacobiano se vuelve singular
            - la solucion se va lejos (|xi| > 5 o |eta| > 5)
            - la solucion converge pero cae fuera del maestro
    """
    coords = np.asarray(node_coords, dtype=float)
    N_func, dN_func = get_shape_functions(element_type)

    # Numero de nodos que la funcion de forma considera (4 o 9). Si
    # node_coords incluye mas filas (caller paso un slice mas largo),
    # nos quedamos con las primeras n.
    n_test = len(N_func(0.0, 0.0))
    coords = np.ascontiguousarray(coords[:n_test])

    # Fast path Q4: kernel JIT sin allocations.
    if n_test == 4:
        ok, xi, eta = _inverse_iso_map_q4_njit(
            float(x_p), float(y_p), coords, float(tol), int(max_iter)
        )
        if ok:
            return (xi, eta)
        return None

    # Slow path Q9: NumPy puro (uso poco frecuente vs Q4).
    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N = N_func(xi, eta)
        Fx = float(N @ coords[:, 0]) - x_p
        Fy = float(N @ coords[:, 1]) - y_p

        if math.hypot(Fx, Fy) < tol:
            if abs(xi) > 1.05 or abs(eta) > 1.05:
                return None
            return (xi, eta)

        dN = dN_func(xi, eta)
        J = dN @ coords
        det_J = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
        if abs(det_J) < JACOBIAN_MIN_DETERMINANT:
            return None

        inv_det = 1.0 / det_J
        d_xi  = -inv_det * ( J[1, 1] * Fx - J[1, 0] * Fy)
        d_eta = -inv_det * (-J[0, 1] * Fx + J[0, 0] * Fy)
        xi += d_xi
        eta += d_eta

        if abs(xi) > 5.0 or abs(eta) > 5.0:
            return None

    return None


# ─── Calculo de campos en (xi, eta) ────────────────────────────────────────

def principal_and_vm(sigma_x: float, sigma_y: float, tau_xy: float):
    """Esfuerzos principales y Von Mises desde las componentes cartesianas.

    Usado tanto por compute_raw como por compute_smooth (en este ultimo
    sigma_1 / sigma_2 / VM NO se interpolan: se recomputan desde las
    componentes interpoladas, para mantener coherencia).
    """
    sigma_avg = 0.5 * (sigma_x + sigma_y)
    R = math.sqrt(0.25 * (sigma_x - sigma_y) ** 2 + tau_xy ** 2)
    s1 = sigma_avg + R
    s2 = sigma_avg - R
    vm = math.sqrt(s1 * s1 - s1 * s2 + s2 * s2)
    return s1, s2, vm


def _get_node_coords(project, elem) -> np.ndarray:
    """Coords ORIGINALES de los nodos del elemento (sin deformacion).

    Formulacion Lagrangiana total: B se construye en coords de referencia.
    """
    return np.array(
        [[project.nodes[nid].x, project.nodes[nid].y]
         for nid in elem.node_ids],
        dtype=float,
    )


def displacement_at(project, solution, elem_id: int, xi: float, eta: float):
    """Interpola (ux, uy) en (xi, eta) usando las funciones de forma.

    Retorna tupla (ux, uy) en floats.
    """
    elem = project.elements[elem_id]
    N_func, _ = get_shape_functions(project.element_type)
    N = N_func(xi, eta)
    u = solution["u"]
    idx_map = project.node_index_map

    ux = 0.0
    uy = 0.0
    for i, nid in enumerate(elem.node_ids[:len(N)]):
        base = 2 * idx_map[nid]
        ux += float(N[i]) * float(u[base])
        uy += float(N[i]) * float(u[base + 1])
    return ux, uy


@njit(cache=True)
def _compute_raw_at_point_njit(dN_nat, node_coords, D, u_e):
    """Kernel JIT: calcula (sx, sy, txy) en un punto (xi, eta) dado dN.

    Replica el computo de `compute_raw` sin allocations de B / inv_J.
    Retorna (sx, sy, txy, ok). `ok=False` si el Jacobiano es singular.
    """
    n_nodes = node_coords.shape[0]

    # J = dN_nat @ node_coords
    J00 = 0.0; J01 = 0.0; J10 = 0.0; J11 = 0.0
    for k in range(n_nodes):
        J00 += dN_nat[0, k] * node_coords[k, 0]
        J01 += dN_nat[0, k] * node_coords[k, 1]
        J10 += dN_nat[1, k] * node_coords[k, 0]
        J11 += dN_nat[1, k] * node_coords[k, 1]
    det_J = J00 * J11 - J01 * J10
    if abs(det_J) < JACOBIAN_MIN_DETERMINANT:
        return 0.0, 0.0, 0.0, False

    inv_d = 1.0 / det_J
    invJ00 =  J11 * inv_d
    invJ01 = -J01 * inv_d
    invJ10 = -J10 * inv_d
    invJ11 =  J00 * inv_d

    # strain = B @ u_e (sin armar B explicito — solo dot products)
    ex = 0.0; ey = 0.0; gxy = 0.0
    for k in range(n_nodes):
        dphx = invJ00 * dN_nat[0, k] + invJ01 * dN_nat[1, k]
        dphy = invJ10 * dN_nat[0, k] + invJ11 * dN_nat[1, k]
        ux_k = u_e[2 * k]
        uy_k = u_e[2 * k + 1]
        ex  += dphx * ux_k
        ey  += dphy * uy_k
        gxy += dphy * ux_k + dphx * uy_k

    # stress = D @ strain
    sx = D[0, 0] * ex + D[0, 1] * ey + D[0, 2] * gxy
    sy = D[1, 0] * ex + D[1, 1] * ey + D[1, 2] * gxy
    txy = D[2, 0] * ex + D[2, 1] * ey + D[2, 2] * gxy
    return sx, sy, txy, True


def compute_raw(project, solution, elem_id: int, xi: float, eta: float):
    """Esfuerzo CRUDO en (xi, eta): sigma = D * B(xi, eta) * u_e.

    Discontinuo entre elementos -- es la verdad del MEF Galerkin C0
    (los desplazamientos son C0; sus derivadas, no).

    Retorna dict con:
        sigma_x, sigma_y, tau_xy, sigma_1, sigma_2, von_mises, ux, uy
    o None si los datos no estan disponibles.
    """
    if solution is None or elem_id not in project.elements:
        return None

    elem = project.elements[elem_id]
    node_coords = _get_node_coords(project, elem)
    _, dN_func = get_shape_functions(project.element_type)

    material = project.materials.get(elem.material_name)
    if material is None:
        material = next(iter(project.materials.values()), None)
        if material is None:
            return None
    D = constitutive_matrix(material.E, material.nu, project.analysis_type)

    # DOFs ordinales (NO 2*(nid-1)). Soporta IDs no contiguos.
    dof_idx = elem.get_dof_indices(project)
    u_e = np.ascontiguousarray(solution["u"][dof_idx])

    dN_nat = np.ascontiguousarray(dN_func(xi, eta))
    coords_arr = np.ascontiguousarray(node_coords[:dN_nat.shape[1]])
    sx, sy, txy, ok = _compute_raw_at_point_njit(dN_nat, coords_arr, D, u_e)
    if not ok:
        return None
    s1, s2, vm = principal_and_vm(sx, sy, txy)
    ux, uy = displacement_at(project, solution, elem_id, xi, eta)

    return {
        "sigma_x": float(sx), "sigma_y": float(sy), "tau_xy": float(txy),
        "sigma_1": s1, "sigma_2": s2, "von_mises": vm,
        "ux": ux, "uy": uy,
        "mode": "raw",
    }


def compute_smooth(
    project, solution, nodal_stresses, elem_id: int, xi: float, eta: float
):
    """Esfuerzo SUAVIZADO: sigma = sum N_i(xi, eta) * sigma_i_promediado.

    Continuo entre elementos. Coincide con el contorno renderizado.
    Pierde fidelidad cerca de discontinuidades fisicas reales
    (interfaces bimaterial, cargas concentradas).

    nodal_stresses: dict {node_id: {sigma_x, sigma_y, tau_xy, ...}}
        tal como lo retorna fem.stress.compute_all_stresses (segundo
        retorno).

    Retorna dict con la misma estructura que compute_raw, o None si
    los datos no estan disponibles.
    """
    if not nodal_stresses or elem_id not in project.elements:
        return None

    elem = project.elements[elem_id]
    N_func, _ = get_shape_functions(project.element_type)
    N = N_func(xi, eta)

    sx = sy = txy = 0.0
    for i, nid in enumerate(elem.node_ids[:len(N)]):
        ns = nodal_stresses.get(nid)
        if ns is None:
            # Nodo Q9 mid/center que el solver no extrapolo: fallback 0.
            continue
        w = float(N[i])
        sx += w * float(ns.get("sigma_x", 0.0))
        sy += w * float(ns.get("sigma_y", 0.0))
        txy += w * float(ns.get("tau_xy", 0.0))

    # sigma_1, sigma_2, VM NO se interpolan: se recomputan desde las
    # componentes interpoladas (consistencia con compute_raw).
    s1, s2, vm = principal_and_vm(sx, sy, txy)
    ux, uy = displacement_at(project, solution, elem_id, xi, eta)

    return {
        "sigma_x": sx, "sigma_y": sy, "tau_xy": txy,
        "sigma_1": s1, "sigma_2": s2, "von_mises": vm,
        "ux": ux, "uy": uy,
        "mode": "smooth",
    }


# ─── Valores CRUDOS por elemento en un nodo compartido ────────────────────

# Mapeo nodo natural por elemento type. Q4: orden CCW de N1..N4 -> (xi, eta).
# Q9: tambien los mid-edges (N5..N8) y el centro (N9).
_Q4_NODE_NATURAL = [(-1.0, -1.0), (+1.0, -1.0), (+1.0, +1.0), (-1.0, +1.0)]
_Q9_NODE_NATURAL = [
    (-1.0, -1.0), (+1.0, -1.0), (+1.0, +1.0), (-1.0, +1.0),  # N1..N4 corners
    (0.0, -1.0), (+1.0, 0.0), (0.0, +1.0), (-1.0, 0.0),       # N5..N8 mid-edges
    (0.0, 0.0),                                                # N9 centroide
]


def crude_values_at_node(project, solution, node_id):
    """Evalua compute_raw en un nodo compartido, una vez por cada elemento
    que lo contiene. Devuelve la lista de valores discontinuos -- materializa
    la naturaleza C0 del MEF Galerkin.

    En modo SUAVIZADO el nodo tiene un solo valor (promedio). En modo CRUDO
    el mismo nodo puede tener N valores distintos, uno por elemento. Este
    helper expone esos N valores -- usado por ProbeOverlay para enseñar la
    discontinuidad al snappear a un nodo.

    Parametros:
        node_id: id del nodo a consultar.

    Retorna:
        list[dict] con un dict por elemento que contiene el nodo. Cada
        dict tiene: elem_id, role (corner/mid/center), sigma_x, sigma_y,
        tau_xy, sigma_1, sigma_2, von_mises. Lista vacia si el nodo no
        esta en ningun elemento o si los datos no estan disponibles.
    """
    if solution is None or node_id not in project.nodes:
        return []

    # Tabla de coords naturales segun element type
    natural_table = (_Q4_NODE_NATURAL if project.element_type.startswith("Q4")
                     else _Q9_NODE_NATURAL)

    results = []
    for eid, elem in project.elements.items():
        if node_id not in elem.node_ids:
            continue
        # Indice ORDINAL del nodo dentro del elemento (0..n_nodes-1)
        local_idx = elem.node_ids.index(node_id)
        if local_idx >= len(natural_table):
            continue
        xi, eta = natural_table[local_idx]

        vals = compute_raw(project, solution, eid, xi, eta)
        if vals is None:
            continue

        # Rol del nodo segun su posicion local
        if local_idx < 4:
            role = "corner"
        elif local_idx < 8:
            role = "mid"
        else:
            role = "center"

        results.append({
            "elem_id": eid,
            "role": role,
            "sigma_x": vals["sigma_x"],
            "sigma_y": vals["sigma_y"],
            "tau_xy":  vals["tau_xy"],
            "sigma_1": vals["sigma_1"],
            "sigma_2": vals["sigma_2"],
            "von_mises": vals["von_mises"],
        })
    return results


# ─── Evaluacion vectorizada en grilla (modo CRUDO para contorno) ──────────

def compute_raw_grid(project, solution, elem_id: int, n: int = 6):
    """Evalua sigma = D * B(xi, eta) * u_e vectorizado en una grilla
    (n+1, n+1) de puntos (xi, eta) dentro del elemento maestro.

    Para visualizacion del contorno CRUDO necesitamos evaluar el campo en
    MUCHOS puntos -- no solo los 4 corners -- porque sigma no es bilineal
    en (xi, eta) (B contiene inv(J(xi,eta))) y VM es no lineal en sigma_1
    y sigma_2. La interpolacion bilineal de 4 corner-values daba errores
    de hasta 800% para VM en elementos distorsionados.

    Una sola pasada arma: shape functions, jacobianos, B y sigmas para
    toda la grilla. Retorna TODOS los campos en un dict (compartiendo la
    fase mas cara, que es construir B). post_tab elige cual mostrar.

    Parametros:
        elem_id: id del elemento.
        n: subdivisiones por lado -> grilla (n+1, n+1). Debe coincidir con
            la subdivision interna del render del MeshCanvas (actualmente
            n=6, dando grilla 7x7).

    Retorna:
        dict con 6 claves -> ndarray (n+1, n+1):
            "sigma_x", "sigma_y", "tau_xy", "sigma_1", "sigma_2", "von_mises"
        o None si los datos no estan disponibles.
    """
    if solution is None or elem_id not in project.elements:
        return None

    elem = project.elements[elem_id]
    node_coords = _get_node_coords(project, elem)
    n_nodes = elem.num_nodes if elem.num_nodes in (4, 9) else 4
    coords_used = node_coords[:n_nodes]

    material = project.materials.get(elem.material_name)
    if material is None:
        material = next(iter(project.materials.values()), None)
        if material is None:
            return None
    D = constitutive_matrix(material.E, material.nu, project.analysis_type)

    dof_idx = elem.get_dof_indices(project)
    u_e = np.ascontiguousarray(solution["u"][dof_idx])   # (2 * n_nodes,)

    # dN evaluado en la grilla (cacheado por element_type + n) — evita
    # `dshape_functions_q*` por punto en cada llamada.
    dN_at_grid = _get_dN_at_grid(project.element_type, n)
    # Truncar a las primeras n_nodes derivadas si el caller pidio Q4 sobre
    # un proyecto Q9 (no deberia pasar, defensivo).
    if dN_at_grid.shape[3] > n_nodes:
        dN_at_grid = np.ascontiguousarray(dN_at_grid[:, :, :, :n_nodes])

    sx_g, sy_g, txy_g, s1_g, s2_g, vm_g = _compute_raw_grid_njit(
        dN_at_grid, np.ascontiguousarray(coords_used), D, u_e
    )

    return {
        "sigma_x": sx_g, "sigma_y": sy_g, "tau_xy": txy_g,
        "sigma_1": s1_g, "sigma_2": s2_g, "von_mises": vm_g,
    }


# ─── Puntos de Gauss (Barlow superconvergente) ─────────────────────────────

def gauss_physical_coords(project, elem_id: int, element_stresses):
    """Posiciones fisicas + valores oficiales de los puntos de Gauss.

    Cada elemento integra con 2x2 (Q4) o 3x3 (Q9) puntos de Gauss. Esas
    posiciones son los puntos OPTIMOS de muestreo de esfuerzos segun el
    Teorema de Superconvergencia de Barlow (1976). Las usa el probe para:
        1) Renderizar marcadores sobre el canvas (cuadrados azules).
        2) Hacer snap cuando el cursor se acerca (mostrando valores
           oficiales del solver, no interpolados).

    element_stresses: dict {elem_id: {gauss_stresses, nodal_stresses}}
        tal como lo retorna fem.stress.compute_all_stresses (primer
        retorno).

    Retorna lista de dicts (uno por punto de Gauss del elemento):
        [{xi, eta, x, y, sigma_x, sigma_y, tau_xy, sigma_1, sigma_2,
          von_mises, gp_idx, elem_id}, ...]
    o lista vacia si los datos no estan disponibles.
    """
    if not element_stresses or elem_id not in element_stresses:
        return []
    if elem_id not in project.elements:
        return []

    elem = project.elements[elem_id]
    node_coords = _get_node_coords(project, elem)
    N_func, _ = get_shape_functions(project.element_type)

    gp_data = element_stresses[elem_id].get("gauss_stresses", [])
    result = []
    for gp_idx, gp in enumerate(gp_data):
        xi_g = float(gp["xi"])
        eta_g = float(gp["eta"])
        N = N_func(xi_g, eta_g)
        x = float(N @ node_coords[:len(N), 0])
        y = float(N @ node_coords[:len(N), 1])
        result.append({
            "elem_id": elem_id,
            "gp_idx": gp_idx,
            "xi": xi_g, "eta": eta_g,
            "x": x, "y": y,
            "sigma_x": float(gp["sigma_x"]),
            "sigma_y": float(gp["sigma_y"]),
            "tau_xy":  float(gp["tau_xy"]),
            "sigma_1": float(gp["sigma_1"]),
            "sigma_2": float(gp["sigma_2"]),
            "von_mises": float(gp["von_mises"]),
        })
    return result
