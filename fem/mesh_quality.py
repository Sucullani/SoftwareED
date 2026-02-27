"""
Métricas de calidad de malla:
- Ratio del Jacobiano
- Ángulos internos
- Estiramiento de Robinson
"""

import numpy as np

from fem.shape_functions import dshape_functions_q4
from fem.jacobian import compute_jacobian


def jacobian_ratio(node_coords):
    """
    Calcula el ratio del Jacobiano: min(det(J)) / max(det(J)).
    Evaluado en los 4 vértices del elemento.

    Ideal: 1.0 (elemento rectangular perfecto).
    Aceptable: > 0.3
    """
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    det_values = []

    for xi, eta in corners:
        dN = dshape_functions_q4(xi, eta)
        try:
            _, det_J, _ = compute_jacobian(dN, node_coords)
            det_values.append(det_J)
        except ValueError:
            return 0.0  # Jacobiano singular

    if max(det_values) == 0:
        return 0.0

    return min(det_values) / max(det_values)


def internal_angles(node_coords):
    """
    Calcula los ángulos internos del cuadrilátero (en grados).

    Ideal: todos 90°
    Retorna: list de 4 ángulos.
    """
    n = node_coords.shape[0]
    angles = []

    for i in range(min(n, 4)):
        p_prev = node_coords[(i - 1) % 4]
        p_curr = node_coords[i]
        p_next = node_coords[(i + 1) % 4]

        v1 = p_prev - p_curr
        v2 = p_next - p_curr

        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-15)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.degrees(np.arccos(cos_angle))
        angles.append(angle)

    return angles


def robinson_stretch(node_coords):
    """
    Estiramiento de Robinson: ratio entre el lado más largo y el más corto.

    Ideal: 1.0 (todos los lados iguales).
    Aceptable: < 4.0
    """
    n = min(node_coords.shape[0], 4)
    lengths = []

    for i in range(n):
        p1 = node_coords[i]
        p2 = node_coords[(i + 1) % n]
        lengths.append(np.linalg.norm(p2 - p1))

    if min(lengths) < 1e-15:
        return float("inf")

    return max(lengths) / min(lengths)


def evaluate_mesh_quality(project):
    """
    Evalúa la calidad de todos los elementos de la malla.

    Retorna: dict {elem_id: {jacobian_ratio, min_angle, max_angle, robinson, status}}
    """
    results = {}

    for elem_id, elem in project.elements.items():
        node_coords = np.array([
            [project.nodes[nid].x, project.nodes[nid].y]
            for nid in elem.node_ids[:4]
        ])

        jac_ratio = jacobian_ratio(node_coords)
        angles = internal_angles(node_coords)
        rob = robinson_stretch(node_coords)

        min_angle = min(angles)
        max_angle = max(angles)

        # Evaluar estado
        if jac_ratio > 0.5 and min_angle > 45 and max_angle < 135 and rob < 3:
            status = "Buena"
        elif jac_ratio > 0.2 and min_angle > 30:
            status = "Aceptable"
        else:
            status = "Mala"

        results[elem_id] = {
            "jacobian_ratio": jac_ratio,
            "min_angle": min_angle,
            "max_angle": max_angle,
            "robinson": rob,
            "angles": angles,
            "status": status,
        }

    return results
