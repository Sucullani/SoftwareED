"""
Ensamblaje de la matriz de rigidez global K y vector de fuerzas F.
"""

import numpy as np

from fem.stiffness import element_stiffness


def assemble_global_system(project):
    """
    Ensambla la matriz de rigidez global K y el vector de fuerzas F.

    Parámetros:
        project: ProjectModel con nodos, elementos, cargas, etc.

    Retorna:
        K: array (n_dof, n_dof) - Matriz de rigidez global.
        F: array (n_dof,) - Vector de fuerzas global.
        element_data: dict {elem_id: {ke, gauss_data, dof_indices}}
    """
    n_dof = project.total_dof
    K = np.zeros((n_dof, n_dof))
    F = np.zeros(n_dof)

    element_data = {}

    for elem_id, elem in project.elements.items():
        # Obtener coordenadas de los nodos del elemento
        node_coords = np.array([
            [project.nodes[nid].x, project.nodes[nid].y]
            for nid in elem.node_ids
        ])

        # Material del elemento
        material = project.materials.get(elem.material_name)
        if material is None:
            material = list(project.materials.values())[0]

        # Calcular matriz de rigidez del elemento
        ke, gauss_data = element_stiffness(
            node_coords,
            material.E,
            material.nu,
            elem.thickness,
            project.analysis_type,
            project.element_type,
        )

        # Índices de GDL del elemento
        dof_indices = elem.get_dof_indices()

        # Ensamblar en la matriz global
        for i_local, i_global in enumerate(dof_indices):
            for j_local, j_global in enumerate(dof_indices):
                K[i_global, j_global] += ke[i_local, j_local]

        # Guardar datos del elemento
        element_data[elem_id] = {
            "ke": ke,
            "gauss_data": gauss_data,
            "dof_indices": dof_indices,
            "node_coords": node_coords,
        }

    # Ensamblar vector de fuerzas nodales
    for load in project.nodal_loads.values():
        dof_x = 2 * (load.node_id - 1)
        dof_y = 2 * (load.node_id - 1) + 1
        F[dof_x] += load.fx
        F[dof_y] += load.fy

    return K, F, element_data
