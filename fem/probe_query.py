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

    - compute_raw_grids(project, solution, n)
          El campo crudo en una grilla (n+1, n+1) de TODOS los elementos,
          vectorizado por lotes (`fem/batch.py`). `compute_raw_grid` es
          la version para un solo elemento.

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
from fem.jacobian import compute_jacobian, compute_dN_physical
from fem.b_matrix import compute_b_matrix
from fem.constitutive import constitutive_matrix
from fem.batch import gather_elements, geometry_at_points, stress_at_points
from fem.stress import _STRESS_KEYS


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
    "compute_raw_grids",
    "compute_smooth",
    "crude_values_at_node",
    "displacement_at",
    "gauss_physical_coords",
    "locate_point",
    "principal_and_vm",
    "principal_angle",
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

    Un unico camino para Q4 y Q9 con las funciones de forma del tipo: es
    una consulta por click, el costo es irrelevante.

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
    coords = coords[:n_test]
    x_p = float(x_p)
    y_p = float(y_p)

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

    NOTA (σz): el von Mises usa la forma 2D `sqrt(s1^2 - s1*s2 + s2^2)`, válida
    cuando σz = 0 (TENSIÓN PLANA). En DEFORMACIÓN PLANA σz = ν·(σx+σy) ≠ 0 y el
    von Mises "verdadero" incluiría términos con σz. La forma 2D se aplica
    uniformemente en todas las rutas (compute_raw, compute_raw_grids, los
    rutas por lotes de fem/batch.py). Es una simplificación deliberada y consistente; si
    se desea el von Mises 3D correcto en DP, habría que pasar ν/analysis_type
    a esta capa.
    """
    sigma_avg = 0.5 * (sigma_x + sigma_y)
    R = math.sqrt(0.25 * (sigma_x - sigma_y) ** 2 + tau_xy ** 2)
    s1 = sigma_avg + R
    s2 = sigma_avg - R
    vm = math.sqrt(s1 * s1 - s1 * s2 + s2 * s2)
    return s1, s2, vm


def principal_angle(sigma_x: float, sigma_y: float, tau_xy: float) -> float:
    """Ángulo principal θ_p (radianes) del tensor de tensiones 2D.

    θ_p = ½·atan2(2·τxy, σx − σy). Fuente única para el círculo de Mohr del
    DetailsPanel y las cruces principales (PrincipalCrossLayer), que antes lo
    recalculaban inline. Guard de estado isótropo: si σx≈σy y τxy≈0 el ángulo
    es indeterminado -> 0.0 (cualquier dirección es principal).
    """
    if abs(sigma_x - sigma_y) < 1e-12 and abs(tau_xy) < 1e-12:
        return 0.0
    return 0.5 * math.atan2(2.0 * tau_xy, sigma_x - sigma_y)


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


def compute_raw(project, solution, elem_id: int, xi: float, eta: float):
    """Esfuerzo CRUDO en (xi, eta): sigma = D * B(xi, eta) * u_e.

    Discontinuo entre elementos -- es la verdad del MEF Galerkin C0
    (los desplazamientos son C0; sus derivadas, no).

    Es un solo punto por consulta, asi que usa la cadena legible
    (`compute_jacobian` -> `compute_dN_physical` -> `compute_b_matrix`),
    la misma que ensenan M2/M3.

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
    u_e = np.asarray(solution["u"])[dof_idx]

    dN_nat = dN_func(xi, eta)
    n_nodes = dN_nat.shape[1]
    try:
        _J, _det_J, inv_J = compute_jacobian(dN_nat, node_coords[:n_nodes])
    except ValueError:
        return None  # Jacobiano singular
    B = compute_b_matrix(compute_dN_physical(dN_nat, inv_J))
    stress = D @ (B @ u_e[:2 * n_nodes])
    sx, sy, txy = float(stress[0]), float(stress[1]), float(stress[2])
    s1, s2, vm = principal_and_vm(sx, sy, txy)
    ux, uy = displacement_at(project, solution, elem_id, xi, eta)

    return {
        "sigma_x": sx, "sigma_y": sy, "tau_xy": txy,
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

def compute_raw_grids(project, solution, n: int = 6, elem_ids=None,
                      chunk_size: int = 1024):
    """Evalua sigma = D * B(xi, eta) * u_e en una grilla (n+1, n+1) de
    puntos (xi, eta) del elemento maestro, para TODOS los elementos a la
    vez (o para `elem_ids`), vectorizado por lotes con `fem/batch.py`.

    Para visualizacion del contorno CRUDO necesitamos evaluar el campo en
    MUCHOS puntos -- no solo los 4 corners -- porque sigma no es bilineal
    en (xi, eta) (B contiene inv(J(xi,eta))) y VM es no lineal en sigma_1
    y sigma_2. La interpolacion bilineal de 4 corner-values daba errores
    de hasta 800% para VM en elementos distorsionados.

    Los elementos se procesan en trozos de `chunk_size` para acotar la
    memoria de las B intermedias (e * p * 3 * 2n floats). Un punto con
    Jacobiano singular queda en 0.0 (el elemento entero se reporta en el
    validador de salud, no aqui).

    Parametros:
        n: subdivisiones por lado -> grilla (n+1, n+1). Debe coincidir con
            la subdivision interna del render del MeshCanvas (n=6, 7x7).
        elem_ids: subconjunto de ids; None = todos los elementos.

    Retorna:
        dict {elem_id: {"sigma_x", "sigma_y", "tau_xy", "sigma_1",
        "sigma_2", "von_mises"} -> ndarray (n+1, n+1)}, o None si los
        datos no estan disponibles (sin solucion, sin materiales, malla
        inconsistente).
    """
    if solution is None or not project.elements or not project.materials:
        return None
    if elem_ids is not None:
        elem_ids = [eid for eid in elem_ids if eid in project.elements]
        if not elem_ids:
            return {}
    try:
        batch = gather_elements(project, elem_ids)
    except ValueError:
        return None

    dN_at_grid = _get_dN_at_grid(project.element_type, n)
    side = n + 1
    dN_pts = dN_at_grid.reshape(side * side, 2, dN_at_grid.shape[3])
    # Usar los primeros nodos comunes a las funciones de forma y a la malla
    # (defensivo: proyecto Q9 con elementos de 4 nodos o viceversa).
    n_use = min(batch.n_nodes, dN_pts.shape[2])
    dN_pts = dN_pts[:, :, :n_use]
    coords = batch.coords[:, :n_use]
    dofs = batch.dofs[:, :2 * n_use]
    u = np.asarray(solution["u"], dtype=float)

    out = {}
    for start in range(0, batch.n_elements, chunk_size):
        sl = slice(start, start + chunk_size)
        _J, det_J, B = geometry_at_points(coords[sl], dN_pts, check=False)
        sig = stress_at_points(B, u[dofs[sl]], batch.D[sl])          # (e, p, 6)
        singular = np.abs(det_J) < JACOBIAN_MIN_DETERMINANT
        if singular.any():
            sig[singular] = 0.0
        sig = sig.reshape(-1, side, side, len(_STRESS_KEYS))
        for i, eid in enumerate(batch.elem_ids[sl]):
            out[int(eid)] = {
                key: np.ascontiguousarray(sig[i, :, :, j])
                for j, key in enumerate(_STRESS_KEYS)
            }
    return out


def compute_raw_grid(project, solution, elem_id: int, n: int = 6):
    """Grilla cruda (n+1, n+1) de UN elemento; ver `compute_raw_grids`.

    Retorna el dict de 6 campos del elemento, o None si no esta disponible.
    """
    if solution is None or elem_id not in project.elements:
        return None
    grids = compute_raw_grids(project, solution, n=n, elem_ids=[elem_id])
    if not grids:
        return None
    return grids.get(elem_id)


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
