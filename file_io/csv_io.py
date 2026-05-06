"""
Funciones de importación/exportación de datos en formato CSV.
Para nodos, elementos, cargas y restricciones.
"""

import csv


def import_nodes_csv(filepath, project):
    """
    Importa nodos desde un archivo CSV.

    Formato esperado:
        X, Y [, ID]
        La primera fila se asume como encabezado y se salta.

    Parámetros:
        filepath: ruta del archivo CSV.
        project: ProjectModel donde agregar los nodos.

    Retorna:
        int: número de nodos importados.
    """
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Saltar encabezado
        for row in reader:
            if len(row) >= 2:
                x = float(row[0].strip())
                y = float(row[1].strip())
                nid = int(row[2].strip()) if len(row) >= 3 else None
                project.add_node(x, y, node_id=nid)
                count += 1
    return count


def export_nodes_csv(filepath, project):
    """
    Exporta nodos a un archivo CSV.

    Formato de salida:
        X, Y, ID

    Parámetros:
        filepath: ruta del archivo CSV.
        project: ProjectModel con los nodos.

    Retorna:
        int: número de nodos exportados.
    """
    count = 0
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["X", "Y", "ID"])
        for node in sorted(project.nodes.values(), key=lambda n: n.id):
            writer.writerow([node.x, node.y, node.id])
            count += 1
    return count


def import_elements_csv(filepath, project, thickness=None, material_name=None):
    """
    Importa elementos desde un archivo CSV.

    Formato esperado (header dinámico):
        Q4 → ID, N1, N2, N3, N4 [, Espesor] [, Material]
        Q9 → ID, N1, ..., N9 [, Espesor] [, Material]
    La cantidad de nodos se detecta contando las columnas "N*" del header.

    Retorna:
        int: número de elementos importados.
    """
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        n_nodes = 4
        has_id_col = False
        if header is not None:
            cols = [c.strip().upper() for c in header]
            n_nodes = sum(1 for c in cols if c.startswith("N") and c[1:].isdigit())
            if n_nodes == 0:
                n_nodes = 4
            has_id_col = len(cols) > 0 and cols[0] == "ID"

        node_start = 1 if has_id_col else 0
        extras_start = node_start + n_nodes

        for row in reader:
            if len(row) < node_start + n_nodes:
                continue
            nids = [int(row[node_start + i].strip()) for i in range(n_nodes)]
            t = (float(row[extras_start].strip())
                 if len(row) > extras_start and row[extras_start].strip() else thickness)
            mat = (row[extras_start + 1].strip()
                   if len(row) > extras_start + 1 else material_name)
            project.add_element(nids, t, mat)
            count += 1
    return count


def export_elements_csv(filepath, project):
    """
    Exporta elementos a un archivo CSV con columnas dinámicas según
    project.element_type (Q4 → N1..N4, Q9 → N1..N9).

    Retorna:
        int: número de elementos exportados.
    """
    from config.settings import ELEMENT_Q9
    n_cols = 9 if project.element_type == ELEMENT_Q9 else 4

    count = 0
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["ID"] + [f"N{i+1}" for i in range(n_cols)] + ["Espesor", "Material"]
        writer.writerow(header)
        for elem in sorted(project.elements.values(), key=lambda e: e.id):
            nids = list(elem.node_ids)
            while len(nids) < n_cols:
                nids.append("")
            writer.writerow(
                [elem.id] + nids[:n_cols] + [elem.thickness, elem.material_name]
            )
            count += 1
    return count


