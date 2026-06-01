"""
Importacion de geometria desde archivos DXF (AutoCAD).

Convencion de capa:
    FEM_ELEMENTS (default, configurable): LWPOLYLINE o POLYLINE cerradas de
                 4 vertices. Cada polilinea se convierte en un elemento Q4.

Las coordenadas del DXF se toman literalmente; el significado fisico (mm, m,
in, etc.) lo define el `unit_system` del proyecto — estilo SAP2000. Si el DXF
declara `$INSUNITS`, el helper `detect_dxf_insunits(doc)` devuelve la longitud
inferida, lo que permite al dialogo de import preseleccionar un sistema de
unidades compatible.

Los vertices de cada polilinea se deduplican contra los nodos existentes del
proyecto usando NUMERICAL_TOLERANCE, de modo que elementos adyacentes
comparten nodos automaticamente.

Si la polilinea esta definida en orden horario (CW), se invierte para mantener
la convencion CCW del proyecto — sin CCW el Jacobiano seria negativo y el
elemento invalido.

API:
    import_dxf(filepath, project, layer_elements="FEM_ELEMENTS")
        -> {"nodes_added": int, "elements_added": int, "warnings": [str]}

    list_dxf_layers(filepath) -> [str, ...]

    detect_dxf_insunits(doc_or_filepath) -> str | None    # "mm"/"cm"/"m"/"in"/"ft"
"""

from __future__ import annotations

from typing import List, Optional, Union

from config.settings import NUMERICAL_TOLERANCE


# ezdxf $INSUNITS a string de longitud (subset que usa EduFEM).
_INSUNITS_MAP = {
    1: "in",
    2: "ft",
    4: "mm",
    5: "cm",
    6: "m",
}


def _require_ezdxf():
    """Importa ezdxf y devuelve el modulo. Lanza ImportError con mensaje claro
    si el paquete no esta instalado. Defer del import para que la falta de
    ezdxf no rompa el arranque de la app si el usuario no usa DXF.
    """
    try:
        import ezdxf
        return ezdxf
    except ImportError as exc:
        raise ImportError(
            "El paquete 'ezdxf' no esta instalado en este interprete de Python.\n"
            "Instalalo con uno de estos comandos segun tu entorno:\n\n"
            "   Terminal estandar / VSCode:   pip install ezdxf\n"
            "   Launcher py:                  py -m pip install ezdxf\n"
            "   Interprete especifico:        <ruta/al/python> -m pip install ezdxf\n\n"
            "Despues reinicia la aplicacion. En VSCode, reinicia la ventana con\n"
            "Ctrl+Shift+P → 'Developer: Reload Window'."
        ) from exc


def _shoelace_signed_area(pts) -> float:
    """Area con signo via shoelace. Positivo si los puntos estan en CCW."""
    n = len(pts)
    if n < 3:
        return 0.0
    a = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return 0.5 * a


def _build_coord_index(project, tol):
    """Índice espacial nodo→celda cuantizada (tamaño tol) para dedup O(1)
    amortizado en la importación. Sin esto, _find_or_create_node hacía un
    scan lineal O(n) por vértice → O(n²) total en mallas DXF grandes."""
    index: dict = {}
    inv = 1.0 / tol if tol > 0 else 0.0
    for nid, node in project.nodes.items():
        key = (int(round(node.x * inv)), int(round(node.y * inv)))
        index.setdefault(key, []).append(nid)
    return index


def _find_or_create_node(project, x, y, tol, coord_index):
    """Busca nodo existente con coords (x,y) dentro de tol; si no existe lo crea.

    Usa el índice espacial `coord_index` (celdas de lado tol): solo compara
    contra los nodos de las 9 celdas vecinas, preservando la semántica de
    tolerancia del scan lineal original pero en O(1) amortizado.
    """
    inv = 1.0 / tol if tol > 0 else 0.0
    cx, cy = int(round(x * inv)), int(round(y * inv))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for nid in coord_index.get((cx + dx, cy + dy), ()):
                node = project.nodes.get(nid)
                if node is not None and abs(node.x - x) <= tol and abs(node.y - y) <= tol:
                    return nid
    new_node = project.add_node(float(x), float(y))
    coord_index.setdefault((cx, cy), []).append(new_node.id)
    return new_node.id


def list_dxf_layers(filepath: str) -> List[str]:
    """Devuelve las capas declaradas en el DXF, ordenadas alfabeticamente."""
    ezdxf = _require_ezdxf()
    doc = ezdxf.readfile(filepath)
    return sorted(layer.dxf.name for layer in doc.layers)


def detect_dxf_insunits(doc_or_filepath) -> Optional[str]:
    """Inspecciona el header `$INSUNITS` del DXF y devuelve la unidad de
    longitud inferida ('mm', 'cm', 'm', 'in', 'ft'), o None si el DXF no
    declara unidades (INSUNITS=0) o el valor no esta mapeado.
    """
    ezdxf = _require_ezdxf()
    if isinstance(doc_or_filepath, str):
        doc = ezdxf.readfile(doc_or_filepath)
    else:
        doc = doc_or_filepath
    try:
        val = doc.header.get("$INSUNITS", 0)
    except Exception:
        return None
    return _INSUNITS_MAP.get(int(val))


def _extract_polyline_vertices(entity):
    """Extrae [(x, y), ...] de una LWPOLYLINE o POLYLINE. Retorna None si no
    es valido (no cerrada, menos de 3 vertices, etc.).
    """
    dxftype = entity.dxftype()
    if dxftype == "LWPOLYLINE":
        if not entity.closed:
            return None
        pts = [(p[0], p[1]) for p in entity.get_points("xy")]
    elif dxftype == "POLYLINE":
        if not entity.is_closed:
            return None
        pts = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
    else:
        return None

    # Algunos DXF repiten el primer vertice al final — eliminarlo si es el caso.
    if len(pts) >= 2:
        x0, y0 = pts[0]
        xn, yn = pts[-1]
        if abs(x0 - xn) < 1e-12 and abs(y0 - yn) < 1e-12:
            pts = pts[:-1]

    return pts if len(pts) >= 3 else None


def import_dxf(filepath: str,
               project,
               scale: float = 1.0,
               layer_elements: str = "FEM_ELEMENTS") -> dict:
    """Importa geometria desde DXF al `project` dado.

    Las coordenadas del DXF se multiplican por `scale` antes de insertarse.
    El factor lo calcula el dialogo de import en funcion de la unidad elegida
    por el usuario (combo de longitud: mm/cm/m/in/ft) respecto a la longitud
    del sistema de unidades del proyecto.

    Parametros:
        filepath: ruta al archivo .dxf.
        project: ProjectModel destino (se muta in-place).
        scale: factor multiplicativo aplicado a las coordenadas (default 1.0).
        layer_elements: capa con LWPOLYLINE cerradas de 4 vertices (cada una
                        se convierte en un Q4).

    Retorna:
        {"nodes_added": int, "elements_added": int, "warnings": [str]}
    """
    ezdxf = _require_ezdxf()
    from ezdxf.lldxf.const import DXFStructureError

    try:
        doc = ezdxf.readfile(filepath)
    except (IOError, DXFStructureError) as exc:
        raise ValueError(f"No se pudo leer el DXF: {exc}") from exc

    msp = doc.modelspace()
    tol = NUMERICAL_TOLERANCE * 1e6

    warnings: List[str] = []
    nodes_before = len(project.nodes)

    elems_added = 0
    elems_skipped_duplicate = 0
    default_material = next(iter(project.materials), None)
    if default_material is None:
        raise ValueError("El proyecto no tiene materiales definidos. Crea un "
                         "material antes de importar el DXF.")
    default_thickness = project.default_thickness

    # Firma topologica de los elementos existentes, para evitar duplicados al
    # re-importar el mismo DXF varias veces.
    existing_signatures = {
        frozenset(elem.node_ids[:4])
        for elem in project.elements.values()
    }

    # Índice espacial para dedup O(1) de vértices (seed desde nodos existentes).
    coord_index = _build_coord_index(project, tol)

    for poly in msp.query("LWPOLYLINE POLYLINE"):
        if poly.dxf.layer != layer_elements:
            continue

        raw_pts = _extract_polyline_vertices(poly)
        if raw_pts is None:
            warnings.append(
                f"Polilinea en {layer_elements} ignorada (no cerrada o "
                f"menos de 3 vertices)."
            )
            continue

        if len(raw_pts) != 4:
            warnings.append(
                f"Polilinea en {layer_elements} con {len(raw_pts)} vertices "
                f"(solo se aceptan cuadrilateros de 4 vertices)."
            )
            continue

        # Asegurar orden CCW (shoelace area positiva).
        if _shoelace_signed_area(raw_pts) < 0:
            raw_pts = list(reversed(raw_pts))

        scaled = [(x * scale, y * scale) for (x, y) in raw_pts]
        node_ids = [_find_or_create_node(project, x, y, tol, coord_index)
                    for (x, y) in scaled]

        if len(set(node_ids)) < 4:
            warnings.append(
                f"Polilinea en {layer_elements} degenerada (vertices "
                f"colapsados tras dedupe)."
            )
            continue

        sig = frozenset(node_ids)
        if sig in existing_signatures:
            elems_skipped_duplicate += 1
            continue

        project.add_element(
            node_ids=node_ids,
            thickness=default_thickness,
            material_name=default_material,
        )
        existing_signatures.add(sig)
        elems_added += 1

    project.is_modified = True
    project.is_solved = False

    return {
        "nodes_added": len(project.nodes) - nodes_before,
        "elements_added": elems_added,
        "elements_skipped_duplicate": elems_skipped_duplicate,
        "warnings": warnings,
    }
