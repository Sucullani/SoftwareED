"""
Utilidades de malla. Principalmente la expansión Q4 -> Q9: a partir de elementos
Q4 definidos por 4 vértices, genera los 5 nodos faltantes (4 medios de arista +
1 centro) reutilizando entre elementos vecinos vía dedupe por coordenada.
"""

from config.settings import ELEMENT_Q9, NUMERICAL_TOLERANCE


def _find_or_create_node(project, x, y, tol=NUMERICAL_TOLERANCE * 1e6):
    """
    Busca un nodo existente con coordenadas cercanas a (x, y).
    Si existe, retorna su ID; si no, crea uno nuevo y retorna su ID.
    Tolerancia: 1e-4 (típicamente suficiente para malla en m/mm).
    """
    for nid, node in project.nodes.items():
        if abs(node.x - x) <= tol and abs(node.y - y) <= tol:
            return nid
    new_node = project.add_node(x, y)
    return new_node.id


def expand_q4_to_q9(project):
    """
    Para cada elemento con 4 nodos, genera los 5 nodos faltantes:
      - Nodos 5-8: medios de las aristas (1-2, 2-3, 3-4, 4-1)
      - Nodo 9: centro (promedio de los 4 vértices)
    Los puntos medios compartidos entre elementos vecinos se reutilizan.
    Actualiza project.nodes y project.elements[i].node_ids (4 -> 9).
    Setea project.element_type = ELEMENT_Q9.
    Es idempotente: si los elementos ya son Q9, no hace nada.

    Retorna:
        (num_mid_added, num_center_added): cantidad de nodos nuevos añadidos.
    """
    num_mid = 0
    num_center = 0

    for elem in list(project.elements.values()):
        if elem.num_nodes != 4:
            continue

        n1, n2, n3, n4 = elem.node_ids
        p1 = project.nodes[n1]
        p2 = project.nodes[n2]
        p3 = project.nodes[n3]
        p4 = project.nodes[n4]

        before = len(project.nodes)

        # Puntos medios de aristas (se reutilizan entre elementos vecinos)
        n5 = _find_or_create_node(project, (p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
        n6 = _find_or_create_node(project, (p2.x + p3.x) / 2, (p2.y + p3.y) / 2)
        n7 = _find_or_create_node(project, (p3.x + p4.x) / 2, (p3.y + p4.y) / 2)
        n8 = _find_or_create_node(project, (p4.x + p1.x) / 2, (p4.y + p1.y) / 2)

        mid_after = len(project.nodes)
        num_mid += mid_after - before

        # Centro: siempre es único al elemento (no dedupe)
        cx = (p1.x + p2.x + p3.x + p4.x) / 4
        cy = (p1.y + p2.y + p3.y + p4.y) / 4
        n9 = _find_or_create_node(project, cx, cy)

        num_center += len(project.nodes) - mid_after

        elem.node_ids = [n1, n2, n3, n4, n5, n6, n7, n8, n9]

    project.element_type = ELEMENT_Q9
    project.is_modified = True
    project.is_solved = False

    return num_mid, num_center
