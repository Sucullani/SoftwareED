"""
Importacion / exportacion unificada de TODO el modelo del proyecto.

Formato: archivo .zip que contiene un CSV por entidad
    nodes.csv, elements.csv, materials.csv,
    nodal_loads.csv, boundary_conditions.csv, surface_loads.csv

Cada CSV lleva en la primera linea un comentario con las unidades vigentes
(ej. "# Unidades: longitud=mm, fuerza=N, esfuerzo=MPa") para que el usuario
sepa en que sistema editara los valores en Excel. La segunda linea es el
encabezado real de columnas. La tercera en adelante son los datos.

No se exportan resultados — los resultados se copian directamente desde la
tabla del Post-Proceso con Ctrl+C (TSV al portapapeles).
"""

import csv
import io
import os
import tempfile
import zipfile

from config.units import get_unit_labels
from models.boundary import BoundaryCondition
from models.element import Element
from models.load import NodalLoad, SurfaceLoad
from models.material import Material
from models.node import Node


# ─── Helpers ────────────────────────────────────────────────────────────────

def _units_for(project):
    """Retorna dict {longitud, fuerza, esfuerzo} segun el sistema del proyecto."""
    return get_unit_labels(project.unit_system)


def _units_header(project):
    u = _units_for(project)
    return (f"# Unidades: longitud={u.get('longitud', '-')}, "
            f"fuerza={u.get('fuerza', '-')}, "
            f"esfuerzo={u.get('esfuerzo', '-')}")


def _sanitize_csv_cell(value):
    """Anti CSV/formula-injection: si una celda de TEXTO empieza con un
    caracter que Excel/LibreOffice interpretan como fórmula (= + - @, o
    tab/CR), se le antepone un apóstrofo para neutralizarla. Los valores
    numéricos pasan sin tocar. Defensa estándar al exportar datos que el
    usuario controla (p.ej. nombres de material) a un CSV abrible en planilla.
    """
    if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def _write_csv_to_zip(zf, name, header_comment, columns, rows):
    """Escribe un CSV dentro del zip con un comentario de unidades arriba."""
    buf = io.StringIO()
    buf.write(header_comment + "\n")
    writer = csv.writer(buf)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_sanitize_csv_cell(c) for c in row])
    zf.writestr(name, buf.getvalue())


def _read_csv_from_zip(zf, name):
    """Lee un CSV del zip, ignorando lineas que comienzan con '#'.
    Devuelve (columns, rows) o (None, []) si el archivo no existe."""
    if name not in zf.namelist():
        return None, []
    raw = zf.read(name).decode("utf-8")
    lines = [ln for ln in raw.splitlines() if not ln.lstrip().startswith("#")]
    if not lines:
        return None, []
    reader = csv.reader(lines)
    columns = next(reader, None)
    rows = [r for r in reader if any(c.strip() for c in r)]
    return columns, rows


def _to_int(s, default=None):
    try:
        return int(float(str(s).strip()))
    except (ValueError, TypeError):
        return default


def _to_float(s, default=0.0):
    try:
        return float(str(s).strip())
    except (ValueError, TypeError):
        return default


def _to_bool(s):
    t = str(s).strip().lower()
    return t in ("1", "true", "verdadero", "si", "sí", "yes", "y", "x", "☑", "v")


# ─── Exportacion ────────────────────────────────────────────────────────────

def export_model_csv(project, filepath):
    """Exporta TODO el modelo a un .zip con un CSV por entidad.

    Retorna dict con conteos: {nodes, elements, materials, nodal_loads,
    boundary_conditions, surface_loads}.
    """
    counts = {
        "nodes": 0,
        "elements": 0,
        "materials": 0,
        "nodal_loads": 0,
        "boundary_conditions": 0,
        "surface_loads": 0,
    }
    units_comment = _units_header(project)

    # Escritura atómica: el ZIP se construye en un temporal del mismo
    # directorio y se promueve con os.replace (rename atómico). Un fallo a
    # mitad de escritura no corrompe un export previo del mismo nombre.
    directory = os.path.dirname(os.path.abspath(filepath)) or "."
    fd, tmp = tempfile.mkstemp(suffix=".tmp", dir=directory)
    os.close(fd)  # zipfile abre el path por su cuenta
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            # ── nodes.csv ──────────────────────────────────────────────────
            rows = []
            for node in sorted(project.nodes.values(), key=lambda n: n.id):
                rows.append([node.id, node.x, node.y])
            _write_csv_to_zip(zf, "nodes.csv", units_comment,
                              ["ID", "X", "Y"], rows)
            counts["nodes"] = len(rows)

            # ── elements.csv ───────────────────────────────────────────────
            rows = []
            for elem in sorted(project.elements.values(), key=lambda e: e.id):
                nids = list(elem.node_ids) + [""] * max(0, 4 - len(elem.node_ids))
                rows.append([
                    elem.id, nids[0], nids[1], nids[2], nids[3],
                    elem.thickness, elem.material_name,
                ])
            _write_csv_to_zip(
                zf, "elements.csv", units_comment,
                ["ID", "N1", "N2", "N3", "N4", "Espesor", "Material"], rows,
            )
            counts["elements"] = len(rows)

            # ── materials.csv ──────────────────────────────────────────────
            rows = []
            for mat in project.materials.values():
                rows.append([mat.name, mat.E, mat.nu, mat.density])
            _write_csv_to_zip(
                zf, "materials.csv", units_comment,
                ["Nombre", "E", "nu", "densidad"], rows,
            )
            counts["materials"] = len(rows)

            # ── nodal_loads.csv ────────────────────────────────────────────
            rows = []
            for ld in project.nodal_loads.values():
                rows.append([ld.node_id, ld.fx, ld.fy])
            _write_csv_to_zip(
                zf, "nodal_loads.csv", units_comment,
                ["Nodo", "Fx", "Fy"], rows,
            )
            counts["nodal_loads"] = len(rows)

            # ── boundary_conditions.csv ────────────────────────────────────
            rows = []
            for bc in project.boundary_conditions.values():
                rows.append([
                    bc.node_id,
                    "1" if bc.restrain_x else "0",
                    "1" if bc.restrain_y else "0",
                ])
            _write_csv_to_zip(
                zf, "boundary_conditions.csv", units_comment,
                ["Nodo", "Restringe_X", "Restringe_Y"], rows,
            )
            counts["boundary_conditions"] = len(rows)

            # ── surface_loads.csv ──────────────────────────────────────────
            rows = []
            for sl in project.surface_loads:
                rows.append([
                    sl.node_start, sl.node_end,
                    sl.q_start, sl.q_end, sl.angle,
                ])
            _write_csv_to_zip(
                zf, "surface_loads.csv", units_comment,
                ["Nodo_Inicio", "Nodo_Final", "q_inicio", "q_final", "Angulo"], rows,
            )
            counts["surface_loads"] = len(rows)

        os.replace(tmp, filepath)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    return counts


# ─── Importacion ────────────────────────────────────────────────────────────

def import_model_csv(project, filepath, mode="replace"):
    """Importa un .zip con la estructura producida por export_model_csv.

    mode='replace' borra todo y carga nuevo. mode='merge' agrega manteniendo
    lo existente; los IDs en conflicto se reasignan automaticamente para
    nodos y elementos. Materiales en conflicto se sobreescriben por nombre.

    Retorna dict con conteos importados por entidad.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)

    counts = {
        "nodes": 0,
        "elements": 0,
        "materials": 0,
        "nodal_loads": 0,
        "boundary_conditions": 0,
        "surface_loads": 0,
    }

    with zipfile.ZipFile(filepath, "r") as zf:
        if mode == "replace":
            project.nodes = {}
            project.elements = {}
            project.nodal_loads = {}
            project.boundary_conditions = {}
            project.surface_loads = []

        # ── materiales (primero, para que los elementos los referencien) ──
        cols, rows = _read_csv_from_zip(zf, "materials.csv")
        if cols is not None:
            if mode == "replace":
                project.materials = {}
            for row in rows:
                # Backward-compat: el CSV legacy tenia 5 cols (incluyendo
                # `color`). Hoy son 4. Padear si vino mas corto, ignorar
                # cualquier columna >= 4 si vino mas largo.
                if len(row) < 4:
                    row = row + [""] * (4 - len(row))
                name = str(row[0]).strip()
                if not name:
                    continue
                try:
                    mat = Material(
                        name=name,
                        E=_to_float(row[1], 200000.0),
                        nu=_to_float(row[2], 0.3),
                        density=_to_float(row[3], 0.0),
                    )
                except Exception:
                    continue
                project.materials[name] = mat
                counts["materials"] += 1
            # Si quedamos sin materiales tras un replace vacio, restaurar la
            # libreria por defecto para no romper la creacion de elementos.
            if not project.materials:
                project.materials = Material.get_default_library()

        # ── nodos ─────────────────────────────────────────────────────────
        node_id_map = {}  # csv_id -> real_id (para merge con conflictos)
        cols, rows = _read_csv_from_zip(zf, "nodes.csv")
        if cols is not None:
            for row in rows:
                if len(row) < 3:
                    continue
                csv_id = _to_int(row[0])
                x = _to_float(row[1], 0.0)
                y = _to_float(row[2], 0.0)
                target_id = csv_id
                if mode == "merge" and csv_id in project.nodes:
                    target_id = None  # auto-asignar
                node = project.add_node(x, y, node_id=target_id)
                if csv_id is not None:
                    node_id_map[csv_id] = node.id
                counts["nodes"] += 1

        def _map_nid(nid):
            return node_id_map.get(nid, nid)

        # ── elementos ─────────────────────────────────────────────────────
        cols, rows = _read_csv_from_zip(zf, "elements.csv")
        if cols is not None:
            for row in rows:
                if len(row) < 5:
                    continue
                csv_id = _to_int(row[0])
                nids_raw = [_to_int(row[i]) for i in (1, 2, 3, 4)]
                nids = [_map_nid(n) for n in nids_raw if n is not None]
                if len(nids) < 4:
                    continue
                t = _to_float(row[5], project.default_thickness) if len(row) >= 6 else None
                mat = (str(row[6]).strip() if len(row) >= 7 else "") or None
                if mat is not None and mat not in project.materials:
                    mat = None  # caera al default del modelo
                target_id = csv_id
                if mode == "merge" and csv_id in project.elements:
                    target_id = None
                project.add_element(nids, thickness=t,
                                    material_name=mat, elem_id=target_id)
                counts["elements"] += 1

        # ── cargas nodales ────────────────────────────────────────────────
        cols, rows = _read_csv_from_zip(zf, "nodal_loads.csv")
        if cols is not None:
            for row in rows:
                if len(row) < 3:
                    continue
                nid = _map_nid(_to_int(row[0]))
                if nid is None or nid not in project.nodes:
                    continue
                project.set_nodal_load(nid,
                                       _to_float(row[1], 0.0),
                                       _to_float(row[2], 0.0))
                counts["nodal_loads"] += 1

        # ── restricciones ─────────────────────────────────────────────────
        cols, rows = _read_csv_from_zip(zf, "boundary_conditions.csv")
        if cols is not None:
            for row in rows:
                if len(row) < 3:
                    continue
                nid = _map_nid(_to_int(row[0]))
                if nid is None or nid not in project.nodes:
                    continue
                project.set_boundary_condition(nid,
                                               _to_bool(row[1]),
                                               _to_bool(row[2]))
                counts["boundary_conditions"] += 1

        # ── cargas superficiales ──────────────────────────────────────────
        cols, rows = _read_csv_from_zip(zf, "surface_loads.csv")
        if cols is not None:
            for row in rows:
                if len(row) < 5:
                    continue
                ns = _map_nid(_to_int(row[0]))
                ne = _map_nid(_to_int(row[1]))
                if ns is None or ne is None:
                    continue
                if ns not in project.nodes or ne not in project.nodes:
                    continue
                project.add_surface_load(ns, ne,
                                         _to_float(row[2], 0.0),
                                         _to_float(row[3], 0.0),
                                         _to_float(row[4], 0.0))
                counts["surface_loads"] += 1

    project.is_modified = True
    project.is_solved = False
    return counts
