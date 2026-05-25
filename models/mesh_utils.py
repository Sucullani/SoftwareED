"""
Utilidades de malla. Principalmente la expansión Q4 -> Q9: a partir de elementos
Q4 definidos por 4 vértices, genera los 5 nodos faltantes (4 medios de arista +
1 centro) reutilizando entre elementos vecinos vía dedupe por coordenada.

La operación inversa `shrink_q9_to_q4` trunca cada elemento Q9 a sus 4 vértices
y elimina los nodos medios/centroides que queden huérfanos (sin cargas ni BCs).
"""

import numpy as np

from config.settings import ELEMENT_Q4, ELEMENT_Q9, NUMERICAL_TOLERANCE


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


def auto_expand_if_q9(project):
    """Safety net: si el proyecto esta en modo Q9, expande cualquier
    elemento Q4 que tenga 4 vertices distintos. Idempotente -- llamarla
    varias veces no hace nada cuando todo ya esta consistente.

    Util tras flujos que crean elementos Q4 sin pasar por la conversion
    explicita Q4->Q9: paste TSV, importacion DXF, importacion de modelo
    desde ZIP/CSV. El criterio "4 vertices distintos" evita expandir
    elementos degenerados (con vertices repetidos) que generarian un
    Q9 invalido.

    No tiene efectos colaterales en la UI; el caller es responsable de
    refrescar tablas/canvas si lo necesita.

    Retorna:
        int: cantidad de elementos Q4 que se expandieron a Q9 (0 si no
             aplicaba o si no habia candidatos validos).
    """
    if getattr(project, "element_type", None) != ELEMENT_Q9:
        return 0
    candidates = [
        e for e in project.elements.values()
        if e.num_nodes == 4 and len(set(e.node_ids[:4])) == 4
    ]
    if not candidates:
        return 0
    expand_q4_to_q9(project)
    return len(candidates)


def subdivide_q4_mesh(project, levels=1):
    """Subdivide cada elemento Q4 en 4 sub-Q4 (refinamiento 2x2) `levels` veces.

    Cada elemento Q4 de vertices (N1,N2,N3,N4) en orden CCW se descompone en 4
    sub-cuadrilateros tomando los 4 puntos medios de arista + 1 centroide.
    Los puntos medios compartidos entre elementos vecinos se deduplican via
    `_find_or_create_node` para preservar conectividad.

    Transferencias preservadas:
    - Nodal loads y boundary conditions: heredan al mismo node_id original
      (los 4 vertices macro se mantienen).
    - Surface loads: cada carga sobre una arista (a,b) se divide en dos sub-
      cargas (a, m_ab) y (m_ab, b) con q_mid interpolado linealmente. La
      interpolacion es exacta para Q4 y Q9 porque el modelo SurfaceLoad guarda
      q_start/q_end como perfil lineal unicamente.
    - Material y espesor: heredados por los 4 sub-elementos.

    Idempotente si `levels <= 0` (retorna sin cambios). Elementos Q9 se
    truncan a sus 4 vertices antes de subdividir (se llama internamente a
    `shrink_q9_to_q4` si es necesario).

    Parametros:
        project: ProjectModel a mutar IN-PLACE.
        levels: numero de pasadas de subdivision 2x2 (0=nada, 1=4x elems,
                2=16x elems, ...).

    Retorna:
        project (el mismo objeto, por conveniencia encadenable).
    """
    if levels <= 0:
        return project

    if any(e.num_nodes == 9 for e in project.elements.values()):
        shrink_q9_to_q4(project)

    for _ in range(int(levels)):
        _subdivide_q4_once(project)

    project.element_type = ELEMENT_Q4
    project.is_modified = True
    project.is_solved = False
    return project


def _subdivide_q4_once(project):
    """Una pasada de subdivision 2x2 sobre todos los Q4 del project."""
    original_elements = [
        (e.id, list(e.node_ids), e.thickness, e.material_name)
        for e in project.elements.values() if e.num_nodes == 4
    ]
    original_surface_loads = list(project.surface_loads)

    project.elements.clear()
    project.surface_loads.clear()

    edge_to_mid = {}

    for _old_id, node_ids, thickness, mat_name in original_elements:
        n1, n2, n3, n4 = node_ids
        p1 = project.nodes[n1]
        p2 = project.nodes[n2]
        p3 = project.nodes[n3]
        p4 = project.nodes[n4]

        m12 = _find_or_create_node(project, (p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
        m23 = _find_or_create_node(project, (p2.x + p3.x) / 2, (p2.y + p3.y) / 2)
        m34 = _find_or_create_node(project, (p3.x + p4.x) / 2, (p3.y + p4.y) / 2)
        m41 = _find_or_create_node(project, (p4.x + p1.x) / 2, (p4.y + p1.y) / 2)

        edge_to_mid[frozenset((n1, n2))] = m12
        edge_to_mid[frozenset((n2, n3))] = m23
        edge_to_mid[frozenset((n3, n4))] = m34
        edge_to_mid[frozenset((n4, n1))] = m41

        cx = (p1.x + p2.x + p3.x + p4.x) / 4
        cy = (p1.y + p2.y + p3.y + p4.y) / 4
        cc = _find_or_create_node(project, cx, cy)

        for sub_ids in (
            [n1, m12, cc, m41],
            [m12, n2, m23, cc],
            [cc, m23, n3, m34],
            [m41, cc, m34, n4],
        ):
            project.add_element(
                node_ids=sub_ids,
                thickness=thickness,
                material_name=mat_name,
            )

    for sl in original_surface_loads:
        key = frozenset((sl.node_start, sl.node_end))
        mid = edge_to_mid.get(key)
        if mid is None:
            project.surface_loads.append(sl)
            continue
        q_mid = (sl.q_start + sl.q_end) / 2.0
        project.add_surface_load(
            node_start=sl.node_start, node_end=mid,
            q_start=sl.q_start, q_end=q_mid,
            angle=sl.angle, element_id=None,
        )
        project.add_surface_load(
            node_start=mid, node_end=sl.node_end,
            q_start=q_mid, q_end=sl.q_end,
            angle=sl.angle, element_id=None,
        )


def shrink_q9_to_q4(project):
    """
    Operacion inversa a `expand_q4_to_q9`: reduce cada elemento Q9 a sus 4
    vertices (los primeros 4 node_ids del elemento). Los nodos medios y
    centroides que queden huerfanos (no referenciados por ningun otro
    elemento/carga/BC/surface_load) se eliminan de `project.nodes`.

    Uso tipico: el usuario abre ElementTypeDialog, cambia el radio-button
    de Q9 a Q4 y pulsa Aceptar — entonces esta funcion "deshace" la expansion
    Q4→Q9 previa dejando el modelo consistente.

    Reglas de conservacion:
    - Un nodo interior (ex mid o ex center) con carga nodal, restriccion, o
      referenciado en algun SurfaceLoad.node_start/node_end NO se elimina,
      queda como nodo huerfano con sus datos asociados. El usuario puede
      revisarlo manualmente despues.
    - Los elementos conservan su ID, material y espesor.
    - `element_type` se pone en ELEMENT_Q4.

    Es idempotente: si ya es Q4, retorna (0, 0).

    Retorna:
        (num_elems_truncados, num_nodos_eliminados).
    """
    num_trunc = 0
    candidate_orphans = set()

    for elem in list(project.elements.values()):
        if elem.num_nodes != 9:
            continue
        extras = elem.node_ids[4:]
        candidate_orphans.update(extras)
        elem.node_ids = elem.node_ids[:4]
        num_trunc += 1

    if num_trunc == 0:
        if project.element_type != ELEMENT_Q4:
            project.element_type = ELEMENT_Q4
            project.is_modified = True
            project.is_solved = False
        return 0, 0

    still_referenced = set()
    for elem in project.elements.values():
        still_referenced.update(elem.node_ids)
    still_referenced.update(project.nodal_loads.keys())
    still_referenced.update(project.boundary_conditions.keys())
    for sl in project.surface_loads:
        still_referenced.add(sl.node_start)
        still_referenced.add(sl.node_end)

    orphans = [nid for nid in candidate_orphans if nid not in still_referenced]
    for nid in orphans:
        if nid in project.nodes:
            del project.nodes[nid]

    project.element_type = ELEMENT_Q4
    project.is_modified = True
    project.is_solved = False

    return num_trunc, len(orphans)


def classify_nodes(project):
    """Clasifica cada nodo de `project.nodes` segun su rol topologico:
    'corner' (vertice macro N1..N4), 'mid' (medio de arista N5..N8) o
    'center' (centroide N9).

    Si un mismo nodo aparece con roles distintos en elementos vecinos,
    gana el de mayor prioridad (corner > mid > center). Nodos huerfanos
    sin elemento asociado se tratan como 'corner'.

    Es la unica fuente de verdad: importarla desde GUI (mesh_canvas,
    pre_tab) en vez de duplicar la logica.

    Retorna:
        dict[node_id -> "corner" | "mid" | "center"].
    """
    priority = {"corner": 3, "mid": 2, "center": 1}
    role = {}
    for elem in project.elements.values():
        for i, nid in enumerate(elem.node_ids):
            if i < 4:
                new_role = "corner"
            elif i < 8:
                new_role = "mid"
            else:
                new_role = "center"
            current = role.get(nid)
            if current is None or priority[new_role] > priority[current]:
                role[nid] = new_role
    # Nodos huerfanos sin elemento asociado: default corner.
    for nid in project.nodes:
        role.setdefault(nid, "corner")
    return role


def classify_orphan_status(project):
    """Clasifica cada nodo de `project.nodes` como activo o huerfano.

    Un nodo es "huerfano" si NO aparece en `element.node_ids` de ningun
    elemento. Esos nodos no contribuyen al ensamblaje de K y, si tienen
    BC, generan un DOF colgante restringido (K_red singular). El panel
    de salud los flaggea como warning (con carga) o error (con BC).

    Esta clasificacion es ortogonal a `classify_nodes` (corner/mid/center):
    un mismo nodo puede ser "mid + activo", "corner + huerfano", etc.

    Retorna:
        dict[node_id -> "active" | "orphan"].
    """
    in_element = set()
    for elem in project.elements.values():
        in_element.update(elem.node_ids)
    return {
        nid: ("active" if nid in in_element else "orphan")
        for nid in project.nodes
    }


def recompute_q9_midnodes(project, elem):
    """Recalcula las coordenadas de N5..N9 de un elemento Q9 a partir de
    sus 4 vertices (N1..N4). Mid de arista = punto medio; centroide =
    promedio de los 4 vertices. Mismas formulas que `expand_q4_to_q9`.

    Si el elemento no es Q9, no hace nada. Solo muta `node.x` y `node.y`
    de los nodos interiores -- preserva ID, cargas, BCs y referencias en
    surface_loads. Setea `project.is_modified = True` e `is_solved = False`.

    Uso tipico: tras editar X/Y de un vertice macro, iterar los Q9 que lo
    contengan como corner y llamar a este helper para que los mid/center
    sigan siendo geometricamente coherentes (no aristas curvas).

    Retorna:
        set[node_id] de los nodos interiores cuyas coords se actualizaron.
    """
    if elem.num_nodes != 9:
        return set()

    n1, n2, n3, n4, n5, n6, n7, n8, n9 = elem.node_ids
    p1 = project.nodes[n1]
    p2 = project.nodes[n2]
    p3 = project.nodes[n3]
    p4 = project.nodes[n4]

    updates = {
        n5: ((p1.x + p2.x) / 2, (p1.y + p2.y) / 2),
        n6: ((p2.x + p3.x) / 2, (p2.y + p3.y) / 2),
        n7: ((p3.x + p4.x) / 2, (p3.y + p4.y) / 2),
        n8: ((p4.x + p1.x) / 2, (p4.y + p1.y) / 2),
        n9: ((p1.x + p2.x + p3.x + p4.x) / 4,
             (p1.y + p2.y + p3.y + p4.y) / 4),
    }

    touched = set()
    for nid, (x, y) in updates.items():
        node = project.nodes.get(nid)
        if node is None:
            continue
        if node.x != x or node.y != y:
            node.x = x
            node.y = y
            touched.add(nid)

    if touched:
        project.is_modified = True
        project.is_solved = False

    return touched


def generate_structured_quad_mesh(corners, nx, ny, *,
                                  element_type=ELEMENT_Q4,
                                  material_name=None,
                                  thickness=1.0,
                                  analysis_type=None):
    """Genera una malla estructurada de nx*ny elementos sobre el
    cuadrilatero definido por `corners` (4 vertices en CCW).

    Mapeo bilineal del cuadrado logico (s,t) in [0,1]^2 al cuadrilatero
    fisico usando las 4 funciones de forma Q4. Admite cuadrilateros
    generales (no solo rectangulos) -- usado para el dominio trapezoidal
    de la membrana de Cook.

    Si element_type == ELEMENT_Q9, tras generar los Q4 se llama
    `expand_q4_to_q9` para producir los mid/center nodes.

    Parametros:
        corners: lista de 4 (x, y) en CCW. Idealmente desde la esquina
            inferior-izquierda, pero el mapeo bilineal es invariante a
            rotaciones del orden de los corners (siempre se mapea
            corners[0] a (s=0,t=0), corners[1] a (1,0), corners[2] a (1,1),
            corners[3] a (0,1)).
        nx, ny: numero de elementos en cada direccion logica.
        element_type: ELEMENT_Q4 o ELEMENT_Q9.
        material_name: nombre del material a asignar a cada elemento.
            Si es None, se usa el primero de la libreria default.
        thickness: espesor por elemento.
        analysis_type: tipo de analisis. Si es None, usa el default del
            modelo.

    Retorna:
        project: ProjectModel con la malla generada.
    """
    from models.project import ProjectModel

    if len(corners) != 4:
        raise ValueError("Se requieren exactamente 4 esquinas.")
    if nx < 1 or ny < 1:
        raise ValueError("nx y ny deben ser >= 1.")

    project = ProjectModel()
    project.element_type = ELEMENT_Q4
    project.default_thickness = float(thickness)
    if analysis_type is not None:
        project.analysis_type = analysis_type

    if material_name is None:
        material_name = list(project.materials.keys())[0]
    elif material_name not in project.materials:
        # Crear material con defaults para que add_element no falle.
        from models.material import Material
        project.materials[material_name] = Material(name=material_name)

    # Bilinear mapping desde el cuadrado [0,1]^2 al cuadrilatero fisico.
    # P(s,t) = (1-s)(1-t)*c0 + s(1-t)*c1 + s*t*c2 + (1-s)t*c3
    c0, c1, c2, c3 = [np.asarray(c, dtype=float) for c in corners]

    def map_st(s, t):
        return ((1 - s) * (1 - t) * c0
                + s * (1 - t) * c1
                + s * t * c2
                + (1 - s) * t * c3)

    # Crear nodos en orden row-major (i = columna s, j = fila t)
    node_grid = {}  # (i, j) -> node_id
    for j in range(ny + 1):
        t = j / ny
        for i in range(nx + 1):
            s = i / nx
            xy = map_st(s, t)
            node = project.add_node(float(xy[0]), float(xy[1]))
            node_grid[(i, j)] = node.id

    # Crear elementos Q4 con conectividad CCW
    for j in range(ny):
        for i in range(nx):
            n_sw = node_grid[(i,     j)]
            n_se = node_grid[(i + 1, j)]
            n_ne = node_grid[(i + 1, j + 1)]
            n_nw = node_grid[(i,     j + 1)]
            project.add_element(
                node_ids=[n_sw, n_se, n_ne, n_nw],
                thickness=thickness,
                material_name=material_name,
            )

    if element_type == ELEMENT_Q9:
        expand_q4_to_q9(project)

    project.is_modified = False  # malla recien generada, no "modificada por usuario"
    return project


def boundary_node_ids(project, edge, *, tol=None):
    """Lista de node_ids ordenada que cae sobre la arista `edge` del
    bounding box del modelo. Util para fijar BCs en mallas estructuradas
    sin hardcodear IDs.

    edge: una de "left", "right", "top", "bottom".
    tol: tolerancia geometrica. Por defecto 1e-9 * extent del modelo.

    Para Q9 incluye los mid-nodes de las aristas exteriores (estan en
    el borde geometrico).
    """
    if edge not in ("left", "right", "top", "bottom"):
        raise ValueError(f"edge debe ser left/right/top/bottom, no {edge!r}")
    if not project.nodes:
        return []

    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    extent = max(x_max - x_min, y_max - y_min, 1.0)
    if tol is None:
        tol = 1e-9 * extent

    if edge == "left":
        target = x_min
        match = lambda n: abs(n.x - target) <= tol
        key = lambda n: n.y
    elif edge == "right":
        target = x_max
        match = lambda n: abs(n.x - target) <= tol
        key = lambda n: n.y
    elif edge == "bottom":
        target = y_min
        match = lambda n: abs(n.y - target) <= tol
        key = lambda n: n.x
    else:  # top
        target = y_max
        match = lambda n: abs(n.y - target) <= tol
        key = lambda n: n.x

    matching = [(key(n), nid) for nid, n in project.nodes.items() if match(n)]
    matching.sort()
    return [nid for _, nid in matching]


def find_edge_midnode(elem, node_start, node_end):
    """
    Dado un elemento Q9 y una arista identificada por (node_start, node_end),
    devuelve el node_id del nodo medio correspondiente (posiciones 4..7 en
    elem.node_ids). Acepta la arista en cualquier orientación.

    Mapeo canónico (posiciones en node_ids):
        (n1, n2) → n5 (índice 4)
        (n2, n3) → n6 (índice 5)
        (n3, n4) → n7 (índice 6)
        (n4, n1) → n8 (índice 7)

    Retorna None si el elemento no es Q9 o si el par no forma una arista válida.
    """
    if elem.num_nodes != 9:
        return None
    ids = elem.node_ids
    corner_pairs = [
        ((ids[0], ids[1]), ids[4]),
        ((ids[1], ids[2]), ids[5]),
        ((ids[2], ids[3]), ids[6]),
        ((ids[3], ids[0]), ids[7]),
    ]
    for (a, b), mid in corner_pairs:
        if (node_start == a and node_end == b) or (node_start == b and node_end == a):
            return mid
    return None
