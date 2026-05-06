"""
Ensamblaje de la matriz de rigidez global K y vector de fuerzas F.
"""

import numpy as np

from config.settings import ELEMENT_Q9
from fem.stiffness import element_stiffness
from fem.equivalent_forces import (
    surface_load_to_nodal_forces,
    surface_load_to_nodal_forces_q9,
)
from models.mesh_utils import find_edge_midnode


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

    # Ensamblar vector de fuerzas nodales puntuales
    for load in project.nodal_loads.values():
        dof_x = 2 * (load.node_id - 1)
        dof_y = 2 * (load.node_id - 1) + 1
        F[dof_x] += load.fx
        F[dof_y] += load.fy

    # Ensamblar contribucion de cargas superficiales (trapezoidales lineales).
    # Q4: arista de 2 nodos → integración lineal.
    # Q9: arista de 3 nodos → se localiza el nodo medio en el elemento dueño
    # y la carga se reparte en los 3 nodos con funciones de forma cuadráticas.
    for sl in project.surface_loads:
        n_a = project.nodes.get(sl.node_start)
        n_b = project.nodes.get(sl.node_end)
        if n_a is None or n_b is None:
            continue

        mid_nid = None
        if project.element_type == ELEMENT_Q9:
            elem = project.elements.get(sl.element_id) if sl.element_id is not None else None
            if elem is not None:
                mid_nid = find_edge_midnode(elem, sl.node_start, sl.node_end)
            if mid_nid is None:
                # Fallback: buscar en cualquier elemento que contenga la arista.
                for e in project.elements.values():
                    mid_nid = find_edge_midnode(e, sl.node_start, sl.node_end)
                    if mid_nid is not None:
                        break

        if mid_nid is not None:
            n_m = project.nodes.get(mid_nid)
            if n_m is not None:
                (fx_a, fy_a), (fx_m, fy_m), (fx_b, fy_b) = (
                    surface_load_to_nodal_forces_q9(
                        (n_a.x, n_a.y), (n_m.x, n_m.y), (n_b.x, n_b.y),
                        sl.q_start, sl.q_end, sl.angle,
                    )
                )
                F[2 * (sl.node_start - 1)]     += fx_a
                F[2 * (sl.node_start - 1) + 1] += fy_a
                F[2 * (mid_nid - 1)]           += fx_m
                F[2 * (mid_nid - 1) + 1]       += fy_m
                F[2 * (sl.node_end - 1)]       += fx_b
                F[2 * (sl.node_end - 1) + 1]   += fy_b
                continue

        (fx_a, fy_a), (fx_b, fy_b) = surface_load_to_nodal_forces(
            (n_a.x, n_a.y), (n_b.x, n_b.y),
            sl.q_start, sl.q_end, sl.angle,
        )
        F[2 * (sl.node_start - 1)]     += fx_a
        F[2 * (sl.node_start - 1) + 1] += fy_a
        F[2 * (sl.node_end - 1)]       += fx_b
        F[2 * (sl.node_end - 1) + 1]   += fy_b

    return K, F, element_data
