"""
Metricas de calidad de malla para elementos Q4 y Q9.

Framework unificado de 4 metricas que cubren las 5 dimensiones independientes
de calidad geometrica con minima redundancia:

  1. Scaled Jacobian (q_SJ) en los Gauss nativos del elemento
     -> Cubre forma angular en vertices + deteccion de inversion.
  2. Jacobian Ratio (R_J) en los Gauss nativos
     -> Cubre uniformidad del mapeo interior.
  3. Robinson Aspect (AR_R) sobre las 4 esquinas macro
     -> Cubre elongacion/aspect del sobre envolvente (bilineal puro).
  4. 4ta metrica dependiente del tipo de elemento:
     - Q4:  Robinson Taper (T_R)     -> sensibilidad trapezoidal (locking).
     - Q9:  Admisibilidad N5-N9 (q_D) + gates duros -> validez nodos internos.

Las 3 primeras aplican a ambos tipos. La 4ta detecta el modo de falla propio
de cada familia: Q4 es susceptible al trapezoidal locking; Q9 puede invalidarse
por nodos medios/centroide mal colocados (criterio del cuarto de arista y
envolvente convexa de los 4 nodos medios).

Ver docs/mesh_quality_theory.pdf para el desarrollo teorico completo.
"""

import math

import numpy as np

from fem.shape_functions import get_shape_functions
from fem.gauss_quadrature import (
    get_gauss_points_for_element,
    get_dN_at_gauss_points,
)
from fem.jacobian import compute_jacobian, _JAC_MIN_DET
from config.settings import ELEMENT_Q4, ELEMENT_Q9, JACOBIAN_MIN_DETERMINANT
from fem._numba_compat import njit


# --------------------------------------------------------------------------- #
# METRICAS BASADAS EN EL JACOBIANO                                             #
# --------------------------------------------------------------------------- #

@njit(cache=True)
def _jacobian_samples_njit(dN_at_gps, node_coords):
    """Kernel JIT: evalua det(J) y normas de columnas de J en cada GP.

    Retorna (dets, col_norms, ok). `ok=False` indica que algun Jacobiano
    fue singular (caller debe descartar el elemento).

    Sin allocations de J/inv_J por GP — calcula los 4 escalares (J00..J11)
    inline. Aplica al mismo array de dN precomputado que usa el assembly,
    no hay re-evaluacion de shape functions.
    """
    n_gp = dN_at_gps.shape[0]
    n_nodes = node_coords.shape[0]
    dets = np.empty(n_gp)
    col_norms = np.empty((n_gp, 2))

    for g in range(n_gp):
        dN_nat = dN_at_gps[g]
        J00 = 0.0; J01 = 0.0; J10 = 0.0; J11 = 0.0
        for k in range(n_nodes):
            J00 += dN_nat[0, k] * node_coords[k, 0]
            J01 += dN_nat[0, k] * node_coords[k, 1]
            J10 += dN_nat[1, k] * node_coords[k, 0]
            J11 += dN_nat[1, k] * node_coords[k, 1]
        det_J = J00 * J11 - J01 * J10
        if abs(det_J) < _JAC_MIN_DET:
            return dets, col_norms, False
        dets[g] = det_J
        # ||J[:, 0]|| = sqrt(J00^2 + J10^2); ||J[:, 1]|| = sqrt(J01^2 + J11^2)
        col_norms[g, 0] = math.sqrt(J00 * J00 + J10 * J10)
        col_norms[g, 1] = math.sqrt(J01 * J01 + J11 * J11)
    return dets, col_norms, True


def _jacobian_samples(node_coords, element_type):
    """Wrapper Python sobre `_jacobian_samples_njit`. Mantiene la API
    existente (retorna listas o `(None, None)` en caso singular).
    """
    dN_at_gps, _, _, _ = get_dN_at_gauss_points(element_type)
    node_coords = np.ascontiguousarray(np.asarray(node_coords, dtype=float))
    dets, col_norms, ok = _jacobian_samples_njit(dN_at_gps, node_coords)
    if not ok:
        return None, None
    return dets.tolist(), [(float(col_norms[g, 0]), float(col_norms[g, 1]))
                            for g in range(col_norms.shape[0])]


def jacobian_ratio(node_coords, element_type):
    """R_J = min_g det(J_g) / max_g det(J_g) sobre los puntos de Gauss
    nativos del elemento (2x2 para Q4, 3x3 para Q9).

    Ideal: 1.0 (mapeo casi afin).  Aceptable: > 0.3.  Inaceptable: <= 0.
    Convencion Abaqus/Patran (cociente en (0,1]).
    """
    dets, _ = _jacobian_samples(node_coords, element_type)
    if dets is None:
        return 0.0
    max_d = max(dets)
    if max_d <= 0:
        return 0.0
    return min(dets) / max_d


def scaled_jacobian(node_coords, element_type):
    """q_SJ = min_g det(J_g) / (||J[:,0]||_g * ||J[:,1]||_g).

    Es sin(angulo local entre las imagenes de los ejes naturales) y detecta
    inversion de forma robusta (valor <= 0 => elemento invalido).

    Ideal: 1.0 (mapeo ortogonal).  Aceptable: >= 0.5.  Invertido: <= 0.
    """
    dets, col_norms = _jacobian_samples(node_coords, element_type)
    if dets is None:
        return 0.0
    vals = []
    for det_J, (c1, c2) in zip(dets, col_norms):
        denom = c1 * c2
        if denom <= JACOBIAN_MIN_DETERMINANT:
            return 0.0
        vals.append(det_J / denom)
    return min(vals)


def _sj_and_rj_from_samples(node_coords, element_type):
    """Calcula scaled_jacobian Y jacobian_ratio con UNA sola evaluacion de
    `_jacobian_samples` (las funciones publicas la corren por separado, lo
    que duplica el muestreo de Gauss). Usado por evaluate_mesh_quality.
    Retorna (q_sj, r_j) con la misma semantica que las funciones publicas."""
    dets, col_norms = _jacobian_samples(node_coords, element_type)
    if dets is None:
        return 0.0, 0.0

    # scaled_jacobian
    sj_vals = []
    q_sj = 0.0
    invalid = False
    for det_J, (c1, c2) in zip(dets, col_norms):
        denom = c1 * c2
        if denom <= JACOBIAN_MIN_DETERMINANT:
            invalid = True
            break
        sj_vals.append(det_J / denom)
    q_sj = 0.0 if invalid else min(sj_vals)

    # jacobian_ratio
    max_d = max(dets)
    r_j = 0.0 if max_d <= 0 else min(dets) / max_d
    return q_sj, r_j


# --------------------------------------------------------------------------- #
# METRICAS GEOMETRICAS DE LA CARA MACRO                                        #
# --------------------------------------------------------------------------- #

def internal_angles(corner_coords):
    """Angulos internos (en grados) sobre las 4 esquinas macro.
    Ideal: todos 90 deg.  Aceptable: [30, 150] deg.
    """
    angles = []
    n = min(corner_coords.shape[0], 4)
    for i in range(n):
        p_prev = corner_coords[(i - 1) % 4]
        p_curr = corner_coords[i]
        p_next = corner_coords[(i + 1) % 4]
        v1 = p_prev - p_curr
        v2 = p_next - p_curr
        cos_a = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + JACOBIAN_MIN_DETERMINANT)
        cos_a = np.clip(cos_a, -1.0, 1.0)
        angles.append(np.degrees(np.arccos(cos_a)))
    return angles


def _robinson_vectors(corner_coords):
    """Descomposicion de Robinson (1987) para cuadrilateros bilineales.

    Retorna (X1, X2, X3) donde:
        X1 = 1/4 (-r1 + r2 + r3 - r4)  vector entre puntos medios eje xi
        X2 = 1/4 (-r1 - r2 + r3 + r4)  vector entre puntos medios eje eta
        X3 = 1/4 ( r1 - r2 + r3 - r4)  vector bilineal (taper/hourglass)

    Nota: vive en la proyeccion bilineal (las 4 esquinas) del elemento;
    para Q9 caracteriza el "sobre macro", no la curvatura interior.
    """
    r = corner_coords[:4]
    X1 = 0.25 * (-r[0] + r[1] + r[2] - r[3])
    X2 = 0.25 * (-r[0] - r[1] + r[2] + r[3])
    X3 = 0.25 * ( r[0] - r[1] + r[2] - r[3])
    return X1, X2, X3


def robinson_aspect(corner_coords):
    """AR_R = max(||X1||,||X2||) / min(||X1||,||X2||)  (Robinson 1987).
    Ideal: 1.0 (cuadrado/rombo).  Aceptable: <= 4.
    """
    X1, X2, _ = _robinson_vectors(corner_coords)
    n1 = float(np.linalg.norm(X1))
    n2 = float(np.linalg.norm(X2))
    lo = min(n1, n2)
    if lo <= JACOBIAN_MIN_DETERMINANT:
        return float("inf")
    return max(n1, n2) / lo


def robinson_taper(corner_coords):
    """T_R = max(|X3 . X1| / ||X1||^2, |X3 . X2| / ||X2||^2).
    Forma equivalente (Verdict) basada en longitudes de aristas opuestas.
    Ideal: 0 (paralelogramo).  Aceptable: <= 0.5.

    Detecta trapezoidal locking, el modo dominante de degradacion Q4.
    """
    X1, X2, X3 = _robinson_vectors(corner_coords)
    n1_sq = float(np.dot(X1, X1))
    n2_sq = float(np.dot(X2, X2))
    if n1_sq <= JACOBIAN_MIN_DETERMINANT or n2_sq <= JACOBIAN_MIN_DETERMINANT:
        return float("inf")
    t1 = abs(float(np.dot(X3, X1))) / n1_sq
    t2 = abs(float(np.dot(X3, X2))) / n2_sq
    return max(t1, t2)


def edge_aspect_ratio(corner_coords):
    """Relacion de aspecto basica por longitud de aristas: L_max / L_min.
    Metrica simple preservada por compatibilidad (antes llamada
    robinson_stretch, nombre que es incorrecto - la verdadera metrica de
    Robinson esta en robinson_aspect).
    Ideal: 1.0.  Aceptable: <= 4.0.
    """
    n = min(corner_coords.shape[0], 4)
    lengths = []
    for i in range(n):
        p1 = corner_coords[i]
        p2 = corner_coords[(i + 1) % n]
        lengths.append(np.linalg.norm(p2 - p1))
    if min(lengths) < JACOBIAN_MIN_DETERMINANT:
        return float("inf")
    return max(lengths) / min(lengths)


def stretch_metric(corner_coords):
    """Stretch de Verdict para cuadrilateros:  Q = sqrt(2) * L_min / D_max.

    Metrica normalizada por construccion en [0, 1] con 1 = cuadrado perfecto.
    Combina elongacion (via L_min, la arista mas corta) con distorsion angular
    (via D_max, la diagonal mas larga). Para un cuadrado de lado L:
        L_min = L,  D_max = L*sqrt(2)  =>  Q = 1
    Para elementos muy degenerados puede exceder 1 (diagonales colapsando);
    aplicamos clamp para mantener la convencion [0, 1].

    Ref: Stimpson et al., The Verdict geometric quality library,
    Sandia SAND2007-1751, Sec. 5.2 (Quad Stretch).

    Ideal: 1.0.  Aceptable: >= 0.5.  Critico: < 0.4.
    """
    corners = corner_coords[:4]
    if corners.shape[0] < 4:
        return 0.0
    # Longitud de las 4 aristas macro
    L = [float(np.linalg.norm(corners[(i + 1) % 4] - corners[i])) for i in range(4)]
    L_min = min(L)
    # Diagonales N1-N3 y N2-N4
    D1 = float(np.linalg.norm(corners[2] - corners[0]))
    D2 = float(np.linalg.norm(corners[3] - corners[1]))
    D_max = max(D1, D2)
    if D_max <= JACOBIAN_MIN_DETERMINANT:
        return 0.0
    q = math.sqrt(2.0) * L_min / D_max
    return min(1.0, q)


def scaled_jacobian_corners(corner_coords):
    """Scaled Jacobian por vertices (Verdict): min sobre los 4 corners de
        SJ_i = cross(L_{prev,i}, L_{next,i}) / (||L_prev|| * ||L_next||)
    donde L_{prev,i} = P_i - P_{i-1} y L_{next,i} = P_{i+1} - P_i.

    Equivale a sin(angulo_interno) para cuadrilateros convexos en sentido
    antihorario; preserva el signo (negativo = vertice reflejo, malla
    invertida o orientacion CW).

    A diferencia de `scaled_jacobian` (este modulo) que evalua en los
    puntos de Gauss interiores, esta version evalua en las esquinas: es
    mas estricta (toma el peor vertice) y matchea la formula que el alumno
    deriva a mano (sin theta_i). Se usa en el modulo educativo M0 para que
    el numero de la barra coincida con la formula del anclaje fisico.

    Ref: Stimpson et al., Verdict library, Sec. 5.1 Quad Scaled Jacobian.
    Ideal: 1.0.  Aceptable: >= 0.5.  Invalido: <= 0.
    """
    P = corner_coords[:4]
    if P.shape[0] < 4:
        return 0.0
    sjs = []
    for i in range(4):
        L_prev = P[i] - P[(i - 1) % 4]
        L_next = P[(i + 1) % 4] - P[i]
        cross = float(L_prev[0] * L_next[1] - L_prev[1] * L_next[0])
        denom = float(np.linalg.norm(L_prev) * np.linalg.norm(L_next))
        if denom <= JACOBIAN_MIN_DETERMINANT:
            return 0.0
        sjs.append(cross / denom)
    return min(sjs)


# --------------------------------------------------------------------------- #
# METRICA Q9: ADMISIBILIDAD DE NODOS MEDIOS Y CENTROIDE                        #
# --------------------------------------------------------------------------- #

# Indices de aristas Q9: cada entry es (corner_a, corner_b, midside) en
# numeracion 0-indexed. La arista N1-N2 lleva el nodo medio N5 (idx 4), etc.
_Q9_EDGES = (
    (0, 1, 4),  # N1 - N5 - N2
    (1, 2, 5),  # N2 - N6 - N3
    (2, 3, 6),  # N3 - N7 - N4
    (3, 0, 7),  # N4 - N8 - N1
)


def _point_in_convex_hull(p, polygon):
    """True si p esta estrictamente dentro del poligono convexo (ordenado
    CCW o CW, se detecta por el primer cross)."""
    n = len(polygon)
    sign = 0
    for i in range(n):
        a = polygon[i]
        b = polygon[(i + 1) % n]
        cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        if abs(cross) < JACOBIAN_MIN_DETERMINANT:
            return False  # sobre la arista: lo tratamos como fuera
        if sign == 0:
            sign = 1 if cross > 0 else -1
        elif (cross > 0) != (sign > 0):
            return False
    return True


def midside_center_admissibility(coords_q9):
    """Metrica q_D de admisibilidad de los nodos internos de un Q9.

    Entrada: coords_q9 con shape (9, 2), orden [N1..N4, N5..N8, N9].

    Retorna dict:
        'q_D'            : max(desviaciones d_i, d_9)  [ideal 0, aceptable <=0.15]
        's_min', 's_max' : extremos del parametro tangencial de los 4 nodos medios
        'gate_tangential': True si todos los s_i estan en (1/4, 3/4)
        'gate_convex'    : True si N9 esta dentro de la envolvente de N5..N8
        'gates_ok'       : ambos gates OK
    """
    corners = coords_q9[:4]
    mids    = coords_q9[4:8]
    center  = coords_q9[8]

    deviations = []
    s_vals = []
    for edge_idx, (a, b, m_idx) in enumerate(_Q9_EDGES):
        pa, pb = corners[a], corners[b]
        pm = mids[m_idx - 4]  # m_idx es 4..7 en coords, 0..3 en mids
        edge = pb - pa
        L = float(np.linalg.norm(edge))
        if L <= JACOBIAN_MIN_DETERMINANT:
            return {
                "q_D": float("inf"), "s_min": 0.0, "s_max": 1.0,
                "gate_tangential": False, "gate_convex": False, "gates_ok": False,
            }
        # Parametro tangencial s = proyeccion de (pm-pa) sobre edge / L
        s = float(np.dot(pm - pa, edge)) / (L * L)
        s_vals.append(s)
        # Desviacion normalizada d_i = ||pm - midpoint|| / L
        mid_ideal = 0.5 * (pa + pb)
        d_i = float(np.linalg.norm(pm - mid_ideal)) / L
        deviations.append(d_i)

    # Centroide: ideal = promedio de los 4 nodos medios
    center_ideal = 0.25 * (mids[0] + mids[1] + mids[2] + mids[3])
    # Normalizacion: media de largos de arista macro
    avg_edge = 0.25 * sum(
        float(np.linalg.norm(corners[(i + 1) % 4] - corners[i])) for i in range(4)
    )
    if avg_edge <= JACOBIAN_MIN_DETERMINANT:
        d_9 = float("inf")
    else:
        d_9 = float(np.linalg.norm(center - center_ideal)) / avg_edge
    deviations.append(d_9)

    q_D = max(deviations)
    s_min = min(s_vals)
    s_max = max(s_vals)
    gate_tangential = (s_min > 0.25 + 1e-9) and (s_max < 0.75 - 1e-9)
    gate_convex = _point_in_convex_hull(center, [mids[0], mids[1], mids[2], mids[3]])
    return {
        "q_D": q_D,
        "s_min": s_min,
        "s_max": s_max,
        "gate_tangential": gate_tangential,
        "gate_convex": gate_convex,
        "gates_ok": gate_tangential and gate_convex,
    }


# --------------------------------------------------------------------------- #
# EVALUACION GLOBAL: combina las 4 metricas por elemento y asigna status       #
# --------------------------------------------------------------------------- #

def _status_from_metrics(q_sj, r_j, ar, fourth_val, gates_ok, element_type):
    """Combina las 4 metricas en un status cualitativo {Buena|Aceptable|Mala}.

    Q4 usa T_R como 4ta metrica; Q9 usa q_D con gates duros."""
    if q_sj <= 0 or r_j <= 0:
        return "Mala"  # elemento invalido / invertido
    if element_type == ELEMENT_Q9 and not gates_ok:
        return "Mala"  # gate del 1/4-3/4 o convexidad violado
    if element_type == ELEMENT_Q4:
        if q_sj >= 0.7 and r_j >= 0.5 and ar <= 3.0 and fourth_val <= 0.3:
            return "Buena"
        if q_sj >= 0.3 and r_j >= 0.2 and ar <= 5.0 and fourth_val <= 0.5:
            return "Aceptable"
        return "Mala"
    # Q9
    if q_sj >= 0.7 and r_j >= 0.5 and ar <= 3.0 and fourth_val <= 0.10:
        return "Buena"
    if q_sj >= 0.3 and r_j >= 0.2 and ar <= 5.0 and fourth_val <= 0.25:
        return "Aceptable"
    return "Mala"


def evaluate_mesh_quality(project):
    """Evalua las 4 metricas del framework unificado para cada elemento.

    Retorna: dict {elem_id: {...}} con las claves:
        # Metricas universales (Q4 y Q9):
        'scaled_jacobian'   q_SJ en Gauss nativos
        'jacobian_ratio'    R_J en Gauss nativos
        'robinson_aspect'   AR_R sobre las 4 esquinas macro
        'min_angle', 'max_angle', 'angles'  (diagnostico geometrico)
        'edge_aspect'       L_max/L_min (metrica simple, retrocompat)
        # 4ta metrica dependiente del tipo:
        'robinson_taper'    solo Q4 (None en Q9)
        'midside_admissibility' solo Q9 (dict con q_D y gates) o None
        # Sintesis:
        'status'  'Buena' | 'Aceptable' | 'Mala'
        # Retrocompat con codigo existente:
        'robinson'  alias de edge_aspect (no confundir con robinson_aspect)
    """
    results = {}
    element_type = project.element_type

    for elem_id, elem in project.elements.items():
        try:
            node_coords = np.array([
                [project.nodes[nid].x, project.nodes[nid].y]
                for nid in elem.node_ids
            ])
        except KeyError:
            continue
        corner_coords = node_coords[:4]

        # Metricas universales (una sola evaluacion de _jacobian_samples).
        q_sj, r_j = _sj_and_rj_from_samples(node_coords, element_type)
        ar = robinson_aspect(corner_coords)
        ea = edge_aspect_ratio(corner_coords)
        angles = internal_angles(corner_coords)
        min_a = min(angles) if angles else 0.0
        max_a = max(angles) if angles else 180.0

        # 4ta metrica tipo-especifica
        if element_type == ELEMENT_Q4:
            taper = robinson_taper(corner_coords)
            admiss = None
            fourth_val = taper
            gates_ok = True  # no aplica
        else:  # ELEMENT_Q9
            taper = None
            if node_coords.shape[0] >= 9:
                admiss = midside_center_admissibility(node_coords[:9])
                fourth_val = admiss["q_D"]
                gates_ok = admiss["gates_ok"]
            else:
                # Proyecto marcado Q9 pero sin 9 nodos (malla inconsistente)
                admiss = None
                fourth_val = float("inf")
                gates_ok = False

        status = _status_from_metrics(q_sj, r_j, ar, fourth_val, gates_ok,
                                      element_type)

        results[elem_id] = {
            "scaled_jacobian":       q_sj,
            "jacobian_ratio":        r_j,
            "robinson_aspect":       ar,
            "robinson_taper":        taper,           # None en Q9
            "midside_admissibility": admiss,          # None en Q4
            "edge_aspect":           ea,
            "min_angle":             min_a,
            "max_angle":             max_a,
            "angles":                angles,
            "status":                status,
            # --- retrocompat (no romper llamadores antiguos) ---
            "robinson":              ea,  # antes apuntaba a edge_aspect
        }

    return results
