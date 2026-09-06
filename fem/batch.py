"""
Geometria, rigidez y tensiones de elementos por lotes (NumPy vectorizado).

Es la variante optimizada del camino productivo: opera sobre TODOS los
elementos a la vez con `einsum` / `matmul`, sin loop Python por elemento ni
por punto de Gauss. La formulacion legible, elemento a elemento y punto a
punto (`fem/jacobian.py`, `fem/b_matrix.py`, `fem/stiffness.element_stiffness`,
`fem/stress.compute_element_stresses`), es la referencia pedagogica de
M2/M3/M5/M7 y de la memoria de calculo, y el oraculo de
`tests/test_solver_regression.py`: ambas versiones deben coincidir a 1e-9.

Convencion de shapes (e = elementos, p = puntos de evaluacion, n = nodos
por elemento, 2n = GDL por elemento):

    coords      (e, n, 2)       coordenadas (x, y) de los nodos
    dN_at_pts   (p, 2, n)       dN/dxi, dN/deta en cada punto (fijas por tipo)
    J           (e, p, 2, 2)    J = dN_nat . coords
    det_J       (e, p)
    B           (e, p, 3, 2n)   matriz deformacion-desplazamiento
    ke          (e, 2n, 2n)     rigidez elemental
    dofs        (e, 2n)         GDL globales [2 i0, 2 i0 + 1, 2 i1, ...]

Los indices de GDL salen siempre de `project.node_index_map` (soporta ids de
nodo no contiguos), nunca de `2 * (nid - 1)`.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import coo_matrix

from config.settings import ELEMENT_Q4, JACOBIAN_MIN_DETERMINANT
from fem.constitutive import constitutive_matrix


class ElementBatch:
    """Datos de un conjunto de elementos en arrays alineados por fila.

    Atributos (e = cantidad de elementos, n = nodos por elemento):
        elem_ids   (e,)        ids de elemento, en el orden de `project.elements`
        conn       (e, n)      indice ordinal de cada nodo (`node_index_map`)
        coords     (e, n, 2)   coordenadas (x, y) de los nodos
        dofs       (e, 2n)     GDL globales, igual que `Element.get_dof_indices`
        thickness  (e,)        espesor
        D          (e, 3, 3)   matriz constitutiva del material de cada elemento
        density    (e,)        densidad del material (0 si no aplica)
        B, det_J   (e, p, ...) geometria en los puntos de Gauss del ensamblaje
        ke         (e, 2n, 2n) rigidez elemental
    `B`, `det_J` y `ke` los completa `fem.assembly.assemble_global_system`.
    """

    __slots__ = ("elem_ids", "conn", "coords", "dofs", "thickness", "D",
                 "density", "B", "det_J", "ke")

    def __init__(self, elem_ids, conn, coords, dofs, thickness, D, density):
        self.elem_ids = elem_ids
        self.conn = conn
        self.coords = coords
        self.dofs = dofs
        self.thickness = thickness
        self.D = D
        self.density = density
        self.B = None
        self.det_J = None
        self.ke = None

    @property
    def n_elements(self) -> int:
        return int(self.conn.shape[0])

    @property
    def n_nodes(self) -> int:
        return int(self.conn.shape[1])

    def __len__(self) -> int:
        return self.n_elements


def gather_elements(project, elem_ids=None) -> ElementBatch:
    """Arma el lote de arrays de `project.elements` (o del subconjunto dado).

    Una sola pasada Python por nodo y por elemento; todo lo demas queda en
    arrays. Levanta ValueError con un mensaje claro si la malla mezcla Q4 y
    Q9 o si un elemento referencia un nodo inexistente.
    """
    idx_map = project.node_index_map
    if elem_ids is None:
        elem_ids = list(project.elements.keys())
    elems = [project.elements[eid] for eid in elem_ids]
    n_elem = len(elems)
    if n_elem:
        n_nodes = len(elems[0].node_ids)
    else:
        n_nodes = 4 if project.element_type == ELEMENT_Q4 else 9

    try:
        conn = np.array([[idx_map[nid] for nid in elem.node_ids] for elem in elems],
                        dtype=np.intp).reshape(n_elem, n_nodes)
    except (KeyError, ValueError):
        # Camino lento solo para diagnosticar cual elemento esta mal.
        for elem in elems:
            if len(elem.node_ids) != n_nodes:
                raise ValueError(
                    f"El elemento {elem.id} tiene {len(elem.node_ids)} nodos y el "
                    f"resto {n_nodes}: la malla mezcla elementos Q4 y Q9."
                )
            for nid in elem.node_ids:
                if nid not in idx_map:
                    raise ValueError(
                        f"El elemento {elem.id} usa el nodo {nid}, que no existe."
                    )
        raise

    # Tabla de coordenadas por ordinal (una pasada por nodo) y gather por
    # conectividad: coords[e, k] = (x, y) del k-esimo nodo del elemento e.
    xy = np.empty((len(idx_map), 2))
    nodes = project.nodes
    for nid, ordinal in idx_map.items():
        node = nodes[nid]
        xy[ordinal, 0] = node.x
        xy[ordinal, 1] = node.y
    coords = xy[conn]

    dofs = np.empty((n_elem, 2 * n_nodes), dtype=np.intp)
    dofs[:, 0::2] = 2 * conn
    dofs[:, 1::2] = 2 * conn + 1

    thickness = np.array([elem.thickness for elem in elems], dtype=float)

    # D por elemento (cacheada por material: casi siempre hay uno solo).
    # Fallback al primer material del proyecto, como el resto del motor.
    D = np.empty((n_elem, 3, 3))
    density = np.zeros(n_elem)
    D_by_material = {}
    fallback = next(iter(project.materials.values()), None)
    for i, elem in enumerate(elems):
        mat = project.materials.get(elem.material_name)
        if mat is None:
            mat = fallback
        if mat is None:
            raise ValueError("El proyecto no tiene materiales definidos.")
        Dm = D_by_material.get(id(mat))
        if Dm is None:
            Dm = constitutive_matrix(mat.E, mat.nu, project.analysis_type)
            D_by_material[id(mat)] = Dm
        D[i] = Dm
        density[i] = float(getattr(mat, "density", 0.0) or 0.0)

    return ElementBatch(np.asarray(elem_ids), conn, coords, dofs, thickness, D, density)


def geometry_at_points(coords, dN_at_pts, elem_ids=None, *, check=True):
    """Jacobiano, determinante y matriz B de todos los elementos en todos
    los puntos de evaluacion.

    Parametros:
        coords: (e, n, 2).
        dN_at_pts: (p, 2, n) derivadas naturales en cada punto.
        elem_ids: opcional, para nombrar el elemento en el error de
            Jacobiano singular.
        check: con True (ensamblaje) un Jacobiano singular levanta
            ValueError. Con False (grillas de visualizacion) no se levanta:
            en esos puntos B queda sin sentido y el caller debe enmascarar
            con `det_J`.

    Retorna (J (e, p, 2, 2), det_J (e, p), B (e, p, 3, 2n)).
    """
    coords = np.asarray(coords, dtype=float)
    dN = np.asarray(dN_at_pts, dtype=float)

    # J[e, p] = dN_nat[p] @ coords[e]  ->  J[a, b] = sum_k dN[p, a, k] x[e, k, b]
    J = np.einsum("pak,ekb->epab", dN, coords)
    det_J = J[..., 0, 0] * J[..., 1, 1] - J[..., 0, 1] * J[..., 1, 0]

    singular = np.abs(det_J) < JACOBIAN_MIN_DETERMINANT
    if singular.any():
        if check:
            e_bad = int(np.argmax(singular.any(axis=1)))
            label = elem_ids[e_bad] if elem_ids is not None else e_bad
            raise ValueError(
                f"Jacobiano singular en el elemento {label}: nodos mal ordenados "
                "o elemento degenerado."
            )
        safe_det = np.where(singular, 1.0, det_J)
    else:
        safe_det = det_J

    # Inversa 2x2 por cofactores (sin np.linalg.inv por lote).
    inv_J = np.empty_like(J)
    inv_J[..., 0, 0] = J[..., 1, 1]
    inv_J[..., 0, 1] = -J[..., 0, 1]
    inv_J[..., 1, 0] = -J[..., 1, 0]
    inv_J[..., 1, 1] = J[..., 0, 0]
    inv_J /= safe_det[..., None, None]

    # dN_phys[e, p] = inv_J[e, p] @ dN_nat[p]  ->  (e, p, 2, n)
    dN_phys = np.einsum("epal,plk->epak", inv_J, dN)

    n_elem, n_pts, _, n_nodes = dN_phys.shape
    B = np.zeros((n_elem, n_pts, 3, 2 * n_nodes))
    B[..., 0, 0::2] = dN_phys[..., 0, :]   # dNi/dx -> eps_x
    B[..., 1, 1::2] = dN_phys[..., 1, :]   # dNi/dy -> eps_y
    B[..., 2, 0::2] = dN_phys[..., 1, :]   # dNi/dy -> gamma_xy
    B[..., 2, 1::2] = dN_phys[..., 0, :]   # dNi/dx -> gamma_xy
    return J, det_J, B


def stiffness_batch(B, det_J, weights, thickness, D):
    """ke = sum_gp B^T D B |det J| t w, para todos los elementos a la vez.

    Parametros:
        B: (e, p, 3, 2n).  det_J: (e, p).  weights: (p,).  thickness: (e,).
        D: (3, 3) comun o (e, 3, 3) por elemento.

    Retorna ke (e, 2n, 2n). La suma sobre puntos de Gauss se hace dentro de
    un unico matmul apilando (p, 3) en una sola dimension.
    """
    B = np.asarray(B)
    n_elem, n_pts, _, n_dof = B.shape
    factor = (np.abs(det_J) * np.asarray(weights, dtype=float)[None, :]
              * np.asarray(thickness, dtype=float)[:, None])          # (e, p)
    D = np.asarray(D, dtype=float)
    if D.ndim == 2:
        DB = np.einsum("kl,eplj->epkj", D, B)
    else:
        DB = np.einsum("ekl,eplj->epkj", D, B)
    DB *= factor[..., None, None]
    Bs = B.reshape(n_elem, n_pts * 3, n_dof)
    DBs = DB.reshape(n_elem, n_pts * 3, n_dof)
    return np.matmul(Bs.transpose(0, 2, 1), DBs)


def assemble_sparse(dofs, ke, n_dof):
    """Scatter local -> global como tripletes COO y conversion a CSR.

    `coo_matrix` suma las entradas duplicadas en la misma (i, j): es
    exactamente la suma de contribuciones elementales del MEF. K nunca se
    materializa densa (memoria O(nnz)).
    """
    dofs = np.asarray(dofs, dtype=np.intp)
    n_dof_e = dofs.shape[1] if dofs.ndim == 2 else 0
    rows = np.repeat(dofs, n_dof_e, axis=1).ravel()   # [i0, i0, ..., i1, i1, ...]
    cols = np.tile(dofs, (1, n_dof_e)).ravel()        # [j0, j1, ..., j0, j1, ...]
    data = np.asarray(ke, dtype=float).ravel()
    return coo_matrix((data, (rows, cols)), shape=(n_dof, n_dof)).tocsr()


def physical_coords(N_at_pts, coords):
    """Coordenadas fisicas (x, y) de cada punto de evaluacion: (e, p, 2)."""
    return np.einsum("pi,eic->epc", np.asarray(N_at_pts, dtype=float),
                     np.asarray(coords, dtype=float))


def body_force_batch(N_at_pts, det_J, weights, thickness, b_at_pts):
    """fe = sum_gp N_i b |det J| t w para todos los elementos.

    Parametros:
        N_at_pts: (p, n).  det_J: (e, p).  weights: (p,).  thickness: (e,).
        b_at_pts: (e, p, 2) fuerza de cuerpo por unidad de volumen en cada
            punto de Gauss.

    Retorna fe (e, 2n) intercalado [f_x0, f_y0, f_x1, f_y1, ...].
    """
    factor = (np.abs(det_J) * np.asarray(weights, dtype=float)[None, :]
              * np.asarray(thickness, dtype=float)[:, None])          # (e, p)
    fe = np.einsum("pi,ep,epc->eic", np.asarray(N_at_pts, dtype=float),
                   factor, np.asarray(b_at_pts, dtype=float))          # (e, n, 2)
    return fe.reshape(fe.shape[0], -1)


def principal_and_vm_batch(stress):
    """Agrega sigma_1, sigma_2 y von Mises a un array (..., 3) de componentes
    cartesianas. Retorna (..., 6) en el orden
    [sigma_x, sigma_y, tau_xy, sigma_1, sigma_2, von_mises].

    Von Mises en su forma 2D sqrt(s1^2 - s1 s2 + s2^2) (sigma_z = 0), igual
    que en `fem.probe_query.principal_and_vm`.
    """
    stress = np.asarray(stress, dtype=float)
    sx, sy, txy = stress[..., 0], stress[..., 1], stress[..., 2]
    avg = 0.5 * (sx + sy)
    R = np.sqrt(((sx - sy) / 2.0) ** 2 + txy ** 2)
    s1 = avg + R
    s2 = avg - R
    vm = np.sqrt(s1 ** 2 - s1 * s2 + s2 ** 2)
    return np.stack([sx, sy, txy, s1, s2, vm], axis=-1)


def stress_at_points(B, u_elem, D):
    """sigma = D B u_e en todos los puntos de todos los elementos.

    Parametros:
        B: (e, p, 3, 2n).  u_elem: (e, 2n).  D: (3, 3) o (e, 3, 3).

    Retorna (e, p, 6): [sigma_x, sigma_y, tau_xy, sigma_1, sigma_2, von_mises].
    """
    strain = np.einsum("epkd,ed->epk", np.asarray(B, dtype=float),
                       np.asarray(u_elem, dtype=float))               # (e, p, 3)
    D = np.asarray(D, dtype=float)
    if D.ndim == 2:
        stress = strain @ D.T
    else:
        stress = np.einsum("ekl,epl->epk", D, strain)
    return principal_and_vm_batch(stress)
