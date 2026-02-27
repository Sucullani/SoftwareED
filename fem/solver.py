"""
Solver: Aplicación de condiciones de contorno y resolución del sistema K·u = F.
"""

import numpy as np
from scipy.linalg import solve


def apply_boundary_conditions(K, F, restrained_dofs):
    """
    Aplica condiciones de contorno por eliminación de filas/columnas.

    Parámetros:
        K: array (n_dof, n_dof) - Matriz de rigidez global.
        F: array (n_dof,) - Vector de fuerzas.
        restrained_dofs: list - Índices de GDL restringidos (0-indexed).

    Retorna:
        K_red: array - Matriz reducida.
        F_red: array - Vector reducido.
        free_dofs: list - Índices de GDL libres.
    """
    n_dof = len(F)
    restrained_set = set(restrained_dofs)
    free_dofs = [i for i in range(n_dof) if i not in restrained_set]

    # Extraer submatriz y subvector de GDL libres
    K_red = K[np.ix_(free_dofs, free_dofs)]
    F_red = F[free_dofs]

    return K_red, F_red, free_dofs


def solve_system(project):
    """
    Resuelve el sistema completo: ensamblaje + condiciones de borde + solución.

    Parámetros:
        project: ProjectModel con toda la información del modelo.

    Retorna:
        u: array (n_dof,) - Vector de desplazamientos completo.
        K: array - Matriz de rigidez global (completa).
        F: array - Vector de fuerzas (completo).
        element_data: dict - Datos de cada elemento.
        K_red: array - Matriz reducida.
        free_dofs: list - GDL libres.
        restrained_dofs: list - GDL restringidos.
    """
    from fem.assembly import assemble_global_system

    # 1. Ensamblar sistema global
    K, F, element_data = assemble_global_system(project)

    # 2. Obtener GDL restringidos
    restrained_dofs = project.get_restrained_dofs()
    free_dofs = project.get_free_dofs()

    if len(free_dofs) == 0:
        raise ValueError("Todos los GDL están restringidos. No hay nada que resolver.")

    if len(restrained_dofs) == 0:
        raise ValueError(
            "No hay restricciones definidas. El sistema es singular "
            "(mecanismo de cuerpo rígido)."
        )

    # 3. Aplicar condiciones de contorno
    K_red, F_red, free_dofs = apply_boundary_conditions(K, F, restrained_dofs)

    # 4. Resolver K_red · u_free = F_red
    u_free = solve(K_red, F_red)

    # 5. Reconstruir vector completo de desplazamientos
    u = np.zeros(project.total_dof)
    for i, dof in enumerate(free_dofs):
        u[dof] = u_free[i]

    # 6. Calcular reacciones: R = K · u - F
    reactions = K @ u - F

    return {
        "u": u,
        "K": K,
        "F": F,
        "K_red": K_red,
        "F_red": F_red,
        "free_dofs": free_dofs,
        "restrained_dofs": restrained_dofs,
        "reactions": reactions,
        "element_data": element_data,
    }
