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
from scipy.sparse.linalg import spsolve


def apply_boundary_conditions(K, F, restrained_dofs, u_prescribed=None):
    """
    Aplica condiciones de contorno por eliminación de filas/columnas.

    Si `u_prescribed` es None o todo cero, F_red = F[free]. En caso
    contrario, F_red = F[free] - K[free, restrained] @ u_pre[restrained]
    (substitucion estatica del bloque de Dirichlet no homogeneo).

    Parámetros:
        K: matriz de rigidez global (densa o scipy sparse CSR/CSC).
        F: array (n_dof,) - Vector de fuerzas.
        restrained_dofs: list - Índices de GDL restringidos (0-indexed).
        u_prescribed: array (n_dof,) | None - Vector con valores en los
            DOFs restringidos (0 en el resto). Si None, se asume ceros.

    Retorna:
        K_red: submatriz reducida en formato CSR (compatible con spsolve).
        F_red: array - Vector reducido.
        free_dofs: list - Índices de GDL libres.
    """
    n_dof = len(F)

    # Construir free_dofs via mascara booleana vectorizada (10-100x mas
    # rapido que la list comprehension Python para mallas con miles de
    # DOFs). Eliminamos el set() + list comprehension O(n) en favor de
    # un mask + np.where (loop C interno de NumPy).
    rest_arr = np.asarray(restrained_dofs, dtype=np.intp)
    mask = np.ones(n_dof, dtype=bool)
    if rest_arr.size > 0:
        mask[rest_arr] = False
    free_arr = np.where(mask)[0]
    free_dofs = free_arr.tolist()  # API legacy retorna list

    # Indexado por filas luego columnas — eficiente en CSR y correcto en denso.
    K_red = K[free_arr, :][:, free_arr]
    # spsolve requiere CSR o CSC; .tocsr() es no-op si ya es CSR.
    try:
        K_red = K_red.tocsr()
    except AttributeError:
        pass  # K denso (tests de backward-compat): se pasa directo a spsolve

    F_red = F[free_arr].copy()

    if u_prescribed is not None and rest_arr.size > 0:
        u_r = u_prescribed[rest_arr]
        if np.any(u_r != 0.0):
            K_fr = K[free_arr, :][:, rest_arr]
            F_red -= np.asarray(K_fr @ u_r).ravel()

    return K_red, F_red, free_dofs


def _solve_reduced(K_red, F_red):
    """Resuelve K_red · u = F_red con la factorizacion LU dispersa de SuperLU.

    El ordenamiento de columnas es `SOLVER_PERMC_SPEC` (config/settings):
    "MMD_AT_PLUS_A" aprovecha la simetria de K y reduce el llenado frente al
    default "COLAMD" (2,1x menos tiempo a 33 k GDL). Se factoriza en CSC,
    el formato nativo de SuperLU, para evitar la transposicion implicita.

    Tolera K densa (tests de backward-compat): spsolve la convierte.
    """
    from config.settings import SOLVER_PERMC_SPEC

    if not hasattr(K_red, "tocsc"):
        return spsolve(K_red, F_red)

    return spsolve(K_red.tocsc(), F_red, permc_spec=SOLVER_PERMC_SPEC)


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

    # Chequeo "todos restringidos" sin construir get_free_dofs() (O(n) lista):
    # basta el conteo total - restringidos.
    n_free = project.total_dof - len(restrained_dofs)
    if n_free == 0:
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

    # 5. Resolver K_red · u_free = F_red (spsolve acepta CSR/CSC y denso)
    u_free = _solve_reduced(K_red, F_red)
    if np.any(~np.isfinite(u_free)):
        raise ValueError(
            "El solver produjo valores NaN o Inf. Verifica que K no sea "
            "singular: modelo mal restringido, elemento degenerado o E/ν fuera "
            "de rango pueden causar este problema."
        )

    # 6. Reconstruir vector completo de desplazamientos.
    #    En DOFs libres: valor calculado. En DOFs restringidos: valor prescrito.
    # Fancy indexing vectorizado (no loop Python).
    u = np.zeros(project.total_dof)
    free_arr = np.asarray(free_dofs, dtype=np.intp)
    u[free_arr] = u_free
    if u_prescribed is not None and len(restrained_dofs) > 0:
        rest_arr = np.asarray(restrained_dofs, dtype=np.intp)
        u[rest_arr] = u_prescribed[rest_arr]

    # 7. Calcular reacciones: R = K · u - F, SOLO en los GDL restringidos.
    #    En los GDL libres R es ~0 (residuo numerico ~1e-12); ponerlo en 0
    #    exacto evita la multiplicacion densa K @ u completa (solo se evaluan
    #    las filas restringidas) y deja R limpio para lectura/reporte.
    reactions = np.zeros(project.total_dof)
    if len(restrained_dofs) > 0:
        rest = np.asarray(restrained_dofs, dtype=np.intp)
        reactions[rest] = np.asarray(K[rest, :] @ u).ravel() - F[rest]

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
