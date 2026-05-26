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

    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N = N_func(xi, eta)
        Fx = float(N @ coords[:, 0]) - x_p
        Fy = float(N @ coords[:, 1]) - y_p

        if math.hypot(Fx, Fy) < tol:
            # Convergio: validar que esta dentro del maestro (con margen)
            if abs(xi) > 1.05 or abs(eta) > 1.05:
                return None
            return (xi, eta)

        dN = dN_func(xi, eta)             # (2, n_nodes)
        J = dN @ coords                    # (2, 2)
        det_J = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
        if abs(det_J) < JACOBIAN_MIN_DETERMINANT:
            return None

        # Resolucion 2x2 a mano (mas rapido que np.linalg.solve).
        # El Jacobiano de F = (x-x_p, y-y_p) respecto a (xi, eta) es:
        #     J_F = [[dx/dxi,  dx/deta],
        #            [dy/dxi,  dy/deta]]
        #         = J^T  (porque compute_jacobian arma J = dN @ coords con
        #                 dN apilado [dN/dxi; dN/deta], dando filas
        #                 [dx/dxi dy/dxi; dx/deta dy/deta]).
        # Para 2x2: J_F^-1 = (1/det_J) * [[J[1,1], -J[1,0]],
        #                                  [-J[0,1],  J[0,0]]]
        # Delta = -J_F^-1 @ F
        inv_det = 1.0 / det_J
        d_xi  = -inv_det * ( J[1, 1] * Fx - J[1, 0] * Fy)
        d_eta = -inv_det * (-J[0, 1] * Fx + J[0, 0] * Fy)
        xi += d_xi
        eta += d_eta

        # Bail-out: divergio
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

    dN_nat = dN_func(xi, eta)
    J = dN_nat @ node_coords
    det_J = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
    if abs(det_J) < JACOBIAN_MIN_DETERMINANT:
        return None
    # Inversa 2×2 exacta por cofactores (evita np.linalg.inv overhead en probe).
    inv_d = 1.0 / det_J
    inv_J = np.array([[ J[1, 1] * inv_d, -J[0, 1] * inv_d],
                      [-J[1, 0] * inv_d,  J[0, 0] * inv_d]])
    dN_phys = inv_J @ dN_nat
    B = compute_b_matrix(dN_phys)

    material = project.materials.get(elem.material_name)
    if material is None:
        material = next(iter(project.materials.values()), None)
        if material is None:
            return None
    D = constitutive_matrix(material.E, material.nu, project.analysis_type)

    # DOFs ordinales (NO 2*(nid-1)). Soporta IDs no contiguos.
    dof_idx = elem.get_dof_indices(project)
    u_e = solution["u"][dof_idx]

    strain = B @ u_e
    stress = D @ strain
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
    u_e = solution["u"][dof_idx]   # (2 * n_nodes,)

    from fem.shape_functions import get_shape_functions
    _, dN_func = get_shape_functions(project.element_type)

    side = n + 1
    xis = np.linspace(-1.0, 1.0, side)
    etas = np.linspace(-1.0, 1.0, side)

    sx_g = np.zeros((side, side), dtype=float)
    sy_g = np.zeros((side, side), dtype=float)
    txy_g = np.zeros((side, side), dtype=float)
    s1_g = np.zeros((side, side), dtype=float)
    s2_g = np.zeros((side, side), dtype=float)
    vm_g = np.zeros((side, side), dtype=float)

    # Loop sobre grilla (side^2 ≈ 49 iters). Loop puro Python pero el
    # trabajo interno es NumPy -- suficientemente rapido para n=6.
    for i, xi in enumerate(xis):
        for j, eta in enumerate(etas):
            dN_nat = dN_func(xi, eta)          # (2, n_nodes)
            J = dN_nat @ coords_used            # (2, 2)
            det_J = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
            if abs(det_J) < JACOBIAN_MIN_DETERMINANT:
                continue
            # Inversa 2×2 exacta (cofactores); ahorra np.linalg.inv en el loop.
            inv_d = 1.0 / det_J
            inv_J = np.array([[ J[1, 1] * inv_d, -J[0, 1] * inv_d],
                               [-J[1, 0] * inv_d,  J[0, 0] * inv_d]])
            dN_phys = inv_J @ dN_nat            # (2, n_nodes)

            # B (3, 2*n_nodes) ensamblada en vectorizado
            B = np.zeros((3, 2 * n_nodes))
            B[0, 0::2] = dN_phys[0, :]
            B[1, 1::2] = dN_phys[1, :]
            B[2, 0::2] = dN_phys[1, :]
            B[2, 1::2] = dN_phys[0, :]

            sigma = D @ (B @ u_e)
            sx = float(sigma[0])
            sy = float(sigma[1])
            txy = float(sigma[2])
            s1, s2, vm = principal_and_vm(sx, sy, txy)

            sx_g[i, j] = sx
            sy_g[i, j] = sy
            txy_g[i, j] = txy
            s1_g[i, j] = s1
            s2_g[i, j] = s2
            vm_g[i, j] = vm

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
