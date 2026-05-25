"""
Solver: Aplicación de condiciones de contorno y resolución del sistema K·u = F.

Desde 2026-05 soporta:
  - body_force_fn (callable f(x,y)→(bx,by)) propagada al ensamblaje.
  - Desplazamientos prescritos no-cero (Dirichlet no homogeneos) via
    `BoundaryCondition.ux_value/uy_value`. La sustracción `K_fr · u_r` se
    aplica antes de resolver, preservando simetría de K_red.

Backward-compat: con `body_force_fn=None` y todas las BC en ux_value=uy_value=0,
el output es bit-a-bit idéntico al solver pre-2026-05.
"""

import numpy as np
from scipy.linalg import solve


def apply_boundary_conditions(K, F, restrained_dofs, u_prescribed=None):
    """
    Aplica condiciones de contorno por eliminación de filas/columnas.

    Si `u_prescribed` es None o todo cero, F_red = F[free]. En caso
    contrario, F_red = F[free] - K[free, restrained] @ u_pre[restrained]
    (substitucion estatica del bloque de Dirichlet no homogeneo).

    Parámetros:
        K: array (n_dof, n_dof) - Matriz de rigidez global.
        F: array (n_dof,) - Vector de fuerzas.
        restrained_dofs: list - Índices de GDL restringidos (0-indexed).
        u_prescribed: array (n_dof,) | None - Vector con valores en los
            DOFs restringidos (0 en el resto). Si None, se asume ceros.

    Retorna:
        K_red: array - Matriz reducida.
        F_red: array - Vector reducido.
        free_dofs: list - Índices de GDL libres.
    """
    n_dof = len(F)
    restrained_set = set(restrained_dofs)
    free_dofs = [i for i in range(n_dof) if i not in restrained_set]

    K_red = K[np.ix_(free_dofs, free_dofs)]
    F_red = F[free_dofs].copy()

    if u_prescribed is not None and len(restrained_dofs) > 0:
        u_r = u_prescribed[restrained_dofs]
        if np.any(u_r != 0.0):
            K_fr = K[np.ix_(free_dofs, restrained_dofs)]
            F_red -= K_fr @ u_r

    return K_red, F_red, free_dofs


def solve_system(project, *, body_force_fn=None):
    """
    Resuelve el sistema completo: ensamblaje + condiciones de borde + solución.

    Parámetros:
        project: ProjectModel con toda la información del modelo.
        body_force_fn: callable (x, y) -> (bx, by) opcional. Si se pasa,
            se propaga al ensamblaje como fuerza de cuerpo distribuida. Si
            None, el ensamblaje usa la gravedad del project (si esta activa).

    Retorna dict con:
        u, K, F, K_red, F_red, free_dofs, restrained_dofs, reactions,
        element_data
    """
    from fem.assembly import assemble_global_system

    # 1. Ensamblar sistema global (con body_force_fn si aplica)
    K, F, element_data = assemble_global_system(
        project, body_force_fn=body_force_fn
    )

    # 2. Obtener GDL restringidos
    restrained_dofs = project.get_restrained_dofs()
    free_dofs_list = project.get_free_dofs()

    if len(free_dofs_list) == 0:
        raise ValueError("Todos los GDL están restringidos. No hay nada que resolver.")

    if len(restrained_dofs) == 0:
        raise ValueError(
            "No hay restricciones definidas. El sistema es singular "
            "(mecanismo de cuerpo rígido)."
        )

    # 3. Vector de desplazamientos prescritos (None si todos los BCs son u=0)
    u_prescribed = project.get_prescribed_displacement_vector()

    # 4. Aplicar condiciones de contorno
    K_red, F_red, free_dofs = apply_boundary_conditions(
        K, F, restrained_dofs, u_prescribed
    )

    # 5. Resolver K_red · u_free = F_red
    u_free = solve(K_red, F_red)

    # 6. Reconstruir vector completo de desplazamientos.
    #    En DOFs libres: valor calculado. En DOFs restringidos: valor prescrito.
    u = np.zeros(project.total_dof)
    for i, dof in enumerate(free_dofs):
        u[dof] = u_free[i]
    if u_prescribed is not None:
        for dof in restrained_dofs:
            u[dof] = u_prescribed[dof]

    # 7. Calcular reacciones: R = K · u - F
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
