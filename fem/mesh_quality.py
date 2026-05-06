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

import numpy as np

from fem.shape_functions import get_shape_functions
from fem.gauss_quadrature import get_gauss_points_for_element
from fem.jacobian import compute_jacobian
from config.settings import ELEMENT_Q4, ELEMENT_Q9


# --------------------------------------------------------------------------- #
# METRICAS BASADAS EN EL JACOBIANO                                             #
# --------------------------------------------------------------------------- #

def _jacobian_samples(node_coords, element_type):
    """Evalua det(J) y las columnas de J en todos los puntos de Gauss del
    elemento. Retorna (dets, col_norms) donde:
        dets[g]      = det(J) en el punto g
        col_norms[g] = (||J[:,0]||, ||J[:,1]||) en el punto g
    Si algun Jacobiano es no definido, retorna (None, None).
    """
    _, dN_func = get_shape_functions(element_type)
    gauss_pts, _ = get_gauss_points_for_element(element_type)
    dets = []
    col_norms = []
    for xi, eta in gauss_pts:
        dN = dN_func(xi, eta)
        try:
            J, det_J, _ = compute_jacobian(dN, node_coords)
        except ValueError:
            return None, None
        dets.append(det_J)
        c1 = float(np.linalg.norm(J[:, 0]))
        c2 = float(np.linalg.norm(J[:, 1]))
        col_norms.append((c1, c2))
    return dets, col_norms


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
        if denom <= 1e-15:
            return 0.0
        vals.append(det_J / denom)
    return min(vals)


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
        cos_a = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-15)
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
    if lo <= 1e-15:
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
    if n1_sq <= 1e-15 or n2_sq <= 1e-15:
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
    if min(lengths) < 1e-15:
        return float("inf")
    return max(lengths) / min(lengths)


# Alias deprecado para backwards-compat con llamadores antiguos.
robinson_stretch = edge_aspect_ratio


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
        if abs(cross) < 1e-15:
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
        if L <= 1e-15:
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
    if avg_edge <= 1e-15:
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

        # Metricas universales
        q_sj = scaled_jacobian(node_coords, element_type)
        r_j = jacobian_ratio(node_coords, element_type)
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
