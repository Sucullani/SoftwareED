"""
Ensamblaje de la matriz de rigidez global K y vector de fuerzas F.

Desde 2026-05 soporta body forces f(x,y) arbitrarias via `body_force_fn`,
necesarias para el Método de Soluciones Manufacturadas (MMS) y para
conectar la gravedad existente (que estaba como variable del project pero
no se ensamblaba). Backward-compat: `body_force_fn=None` y sin gravedad
activa reproduce el comportamiento previo bit-a-bit.
"""

import warnings

import numpy as np

from config.settings import ELEMENT_Q9
from fem.stiffness import element_stiffness
from fem.shape_functions import get_shape_functions
from fem.equivalent_forces import (
    surface_load_to_nodal_forces,
    surface_load_to_nodal_forces_q9,
)
from models.mesh_utils import find_edge_midnode


def _resolve_body_force_fn(project, body_force_fn):
    """Decide la fuente de body force a usar en el ensamblaje.

    Prioridad: si el caller pasa `body_force_fn` explicito, gana. Si no, y
    el project tiene gravedad activa con materiales de densidad > 0, se
    compone un callback que retorna (rho*gx, rho*gy) por elemento. Si
    ninguna fuente aplica, retorna None (skip total del loop, comportamiento
    legacy).

    Retorna: dict {elem_id: callable(x,y)->(bx,by)} | None.
    Es un dict por-elemento porque la densidad puede variar por material.
    """
    if body_force_fn is not None:
        # Callback global del usuario: misma funcion para todos los elementos.
        if project.include_gravity:
            warnings.warn(
                "body_force_fn pasado explicito; include_gravity sera ignorado.",
                stacklevel=3,
            )
        return {eid: body_force_fn for eid in project.elements}

    if not project.include_gravity:
        return None

    gx, gy = project.gravity_x, project.gravity_y
    if gx == 0.0 and gy == 0.0:
        return None

    out = {}
    for eid, elem in project.elements.items():
        mat = project.materials.get(elem.material_name)
        if mat is None or mat.density <= 0.0:
            continue
        rho = mat.density
        # Capturar rho por valor (default-arg) para evitar late binding.
        out[eid] = lambda x, y, _rho=rho, _gx=gx, _gy=gy: (_rho * _gx, _rho * _gy)
    return out if out else None


def assemble_global_system(project, *, body_force_fn=None):
    """
    Ensambla la matriz de rigidez global K y el vector de fuerzas F.

    Parámetros:
        project: ProjectModel con nodos, elementos, cargas, etc.
        body_force_fn: callable (x: float, y: float) -> (bx, by). Si no es
            None, se ensambla ∫ N_i · b dΩ en cada elemento. Si es None,
            se compone desde gravedad del project (si include_gravity).

    Retorna:
        K: array (n_dof, n_dof) - Matriz de rigidez global.
        F: array (n_dof,) - Vector de fuerzas global.
        element_data: dict {elem_id: {ke, gauss_data, dof_indices}}
    """
    n_dof = project.total_dof
    K = np.zeros((n_dof, n_dof))
    F = np.zeros(n_dof)
    idx_map = project.node_index_map

    element_data = {}

    # Resolver fuente de body forces UNA VEZ antes del loop.
    bf_by_elem = _resolve_body_force_fn(project, body_force_fn)
    N_func, _ = get_shape_functions(project.element_type)

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
        dof_indices = elem.get_dof_indices(project)

        # Ensamblar en la matriz global
        for i_local, i_global in enumerate(dof_indices):
            for j_local, j_global in enumerate(dof_indices):
                K[i_global, j_global] += ke[i_local, j_local]

        # Ensamblar body force del elemento si corresponde.
        # ∫ N_i(ξ,η) · b(x(ξ,η), y(ξ,η)) · |det J| · t dξdη, Gauss 2D.
        if bf_by_elem is not None and elem_id in bf_by_elem:
            bf = bf_by_elem[elem_id]
            n_nodes = node_coords.shape[0]
            fe_body = np.zeros(2 * n_nodes)
            for gp in gauss_data:
                xi, eta = gp["xi"], gp["eta"]
                N_vals = N_func(xi, eta)
                # Coords fisicas del Gauss point: x = sum N_i * x_i
                x_gp = float(N_vals @ node_coords[:, 0])
                y_gp = float(N_vals @ node_coords[:, 1])
                bx, by = bf(x_gp, y_gp)
                factor = abs(gp["det_J"]) * elem.thickness * gp["weight"]
                for i in range(n_nodes):
                    fe_body[2 * i]     += N_vals[i] * bx * factor
                    fe_body[2 * i + 1] += N_vals[i] * by * factor
            for i_local, i_global in enumerate(dof_indices):
                F[i_global] += fe_body[i_local]

        # Guardar datos del elemento
        element_data[elem_id] = {
            "ke": ke,
            "gauss_data": gauss_data,
            "dof_indices": dof_indices,
            "node_coords": node_coords,
        }

    # Ensamblar vector de fuerzas nodales puntuales
    for load in project.nodal_loads.values():
        base = 2 * idx_map[load.node_id]
        F[base]     += load.fx
        F[base + 1] += load.fy

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
                base_a = 2 * idx_map[sl.node_start]
                base_m = 2 * idx_map[mid_nid]
                base_b = 2 * idx_map[sl.node_end]
                F[base_a]     += fx_a
                F[base_a + 1] += fy_a
                F[base_m]     += fx_m
                F[base_m + 1] += fy_m
                F[base_b]     += fx_b
                F[base_b + 1] += fy_b
                continue

        (fx_a, fy_a), (fx_b, fy_b) = surface_load_to_nodal_forces(
            (n_a.x, n_a.y), (n_b.x, n_b.y),
            sl.q_start, sl.q_end, sl.angle,
        )
        base_a = 2 * idx_map[sl.node_start]
        base_b = 2 * idx_map[sl.node_end]
        F[base_a]     += fx_a
        F[base_a + 1] += fy_a
        F[base_b]     += fx_b
        F[base_b + 1] += fy_b

    return K, F, element_data
