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

    Formato esperado:
        N1, N2, N3, N4 [, Espesor] [, Material]

    Parámetros:
        filepath: ruta del archivo CSV.
        project: ProjectModel donde agregar los elementos.
        thickness: espesor por defecto si no se especifica en el CSV.
        material_name: nombre del material por defecto.

    Retorna:
        int: número de elementos importados.
    """
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 4:
                nids = [int(row[i].strip()) for i in range(4)]
                t = float(row[4].strip()) if len(row) >= 5 else thickness
                mat = row[5].strip() if len(row) >= 6 else material_name
                project.add_element(nids, t, mat)
                count += 1
    return count


def export_elements_csv(filepath, project):
    """
    Exporta elementos a un archivo CSV.

    Parámetros:
        filepath: ruta del archivo CSV.
        project: ProjectModel con los elementos.

    Retorna:
        int: número de elementos exportados.
    """
    count = 0
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "N1", "N2", "N3", "N4", "Espesor", "Material"])
        for elem in sorted(project.elements.values(), key=lambda e: e.id):
            nids = list(elem.node_ids)
            while len(nids) < 4:
                nids.append("")
            writer.writerow([
                elem.id, nids[0], nids[1], nids[2], nids[3],
                elem.thickness, elem.material_name
            ])
            count += 1
    return count


def export_results_csv(filepath, project, solution, nodal_stresses):
    """
    Exporta los resultados del análisis a un archivo CSV.

    Parámetros:
        filepath: ruta del archivo CSV.
        project: ProjectModel.
        solution: dict con resultados del solver.
        nodal_stresses: dict con esfuerzos nodales.

    Retorna:
        int: número de filas exportadas.
    """
    import numpy as np

    count = 0
    u = solution["u"]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Nodo", "Ux", "Uy", "|U|",
            "sigma_x", "sigma_y", "tau_xy",
            "sigma_1", "sigma_2", "von_mises"
        ])

        for nid in sorted(project.nodes.keys()):
            ux = u[2 * (nid - 1)]
            uy = u[2 * (nid - 1) + 1]
            umag = np.sqrt(ux**2 + uy**2)

            if nodal_stresses and nid in nodal_stresses:
                s = nodal_stresses[nid]
                sx = s.get("sigma_x", 0)
                sy = s.get("sigma_y", 0)
                txy = s.get("tau_xy", 0)
                s1 = s.get("sigma_1", 0)
                s2 = s.get("sigma_2", 0)
                vm = s.get("von_mises", 0)
            else:
                sx = sy = txy = s1 = s2 = vm = 0

            writer.writerow([
                nid, f"{ux:.6e}", f"{uy:.6e}", f"{umag:.6e}",
                f"{sx:.4f}", f"{sy:.4f}", f"{txy:.4f}",
                f"{s1:.4f}", f"{s2:.4f}", f"{vm:.4f}"
            ])
            count += 1

    return count
