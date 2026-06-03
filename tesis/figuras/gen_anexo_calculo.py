# -*- coding: utf-8 -*-
"""
gen_anexo_calculo.py — Genera los datos numericos y las figuras del
Anexo "Memoria de calculo: ejemplo resuelto paso a paso" de la tesis.

Resuelve el ejemplo canonico Q4 (load_example_project) con el MISMO motor
del software (solve_system + compute_all_stresses) y emite:

  1. tesis/figuras/anexo_calculo_data.tex
        Macros LaTeX (\newcommand) con TODAS las matrices/vectores/escalares
        formateados con coma decimal espanola, para incluir desde el anexo.
        Garantiza numeros bit-exactos con el software (cero transcripcion).

  2. Figuras estilo software (Pillow, fondo blanco, paleta jet del canvas),
        reusando file_io/figure_export.py:
        - mem_modelo.png        (render_mesh_diagram)
        - mem_Ksparsity.png     (render_K_sparsity)
        - mem_contorno_vm.png   (render_contour von Mises, malla deformada)
        - mem_deformada.png     (render_deformed)

Ejecutar (Windows, venv):
    .venv\\Scripts\\python.exe tesis\\figuras\\gen_anexo_calculo.py
"""

from __future__ import annotations

import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)

np.set_printoptions(suppress=True, linewidth=200)


# ─────────────────────────────────────────────────────────────────────────
#  Formateo con coma decimal espanola (convencion de la tesis)
# ─────────────────────────────────────────────────────────────────────────

def es(x, dec=4):
    """Numero -> string LaTeX con coma decimal. Limpia el -0."""
    x = float(x)
    if round(x, dec) == 0.0:
        x = 0.0
    s = f"{x:.{dec}f}"
    return s.replace(".", "{,}")


def es_sci(x, dec=4):
    """Notacion cientifica LaTeX con coma decimal: 1{,}23\\times10^{-3}."""
    x = float(x)
    if x == 0.0:
        return "0"
    mant, exp = f"{x:.{dec}e}".split("e")
    exp = int(exp)
    mant = mant.replace(".", "{,}")
    return f"{mant}\\times10^{{{exp}}}"


def es_auto(x, dec=4, sci_lo=1e-3, sci_hi=1e5):
    """Fijo si |x| esta en rango legible; cientifico si no."""
    ax = abs(float(x))
    if ax == 0.0 or (sci_lo <= ax < sci_hi):
        return es(x, dec)
    return es_sci(x, dec)


def bmat(M, dec=4, fmt=es):
    """Matriz numpy -> cuerpo \\begin{bmatrix}...\\end{bmatrix}."""
    M = np.atleast_2d(np.asarray(M, dtype=float))
    rows = [" & ".join(fmt(v, dec) for v in row) for row in M]
    body = " \\\\\n".join(rows)
    return "\\begin{bmatrix}\n" + body + "\n\\end{bmatrix}"


def bmat_scaled(M, factor, dec=4, fmt=es):
    """Matriz escalada: devuelve 'factor \\cdot bmatrix(M/factor)'."""
    M = np.asarray(M, dtype=float)
    return f"{fmt(factor, 0)}\\,\\cdot\\,{bmat(M / factor, dec, fmt)}"


def colvec(v, dec=4, fmt=es):
    v = np.asarray(v, dtype=float).ravel()
    body = " \\\\\n".join(fmt(x, dec) for x in v)
    return "\\begin{bmatrix}\n" + body + "\n\\end{bmatrix}"


# ─────────────────────────────────────────────────────────────────────────
#  Calculo
# ─────────────────────────────────────────────────────────────────────────

def main():
    from models.example_library import load_example_project
    from fem.solver import solve_system
    from fem.stress import compute_all_stresses
    from fem.constitutive import constitutive_matrix
    from fem.shape_functions import get_shape_functions
    from fem.jacobian import compute_jacobian, compute_dN_physical
    from fem.b_matrix import compute_b_matrix
    from fem.gauss_quadrature import get_gauss_points_for_element
    from config.settings import ELEMENT_Q4

    project = load_example_project()       # 9 nodos, 4 Q4, Fy=-1000 en N7
    sol = solve_system(project)
    elem_stresses, nodal_avg = compute_all_stresses(project, sol)

    u = sol["u"]
    K = sol["K"]
    F = sol["F"]
    reactions = sol["reactions"]
    edata = sol["element_data"]
    free_dofs = sol["free_dofs"]
    restr_dofs = sol["restrained_dofs"]
    idx_map = project.node_index_map

    mat = next(iter(project.materials.values()))
    E, nu, t = mat.E, mat.nu, project.default_thickness

    D = constitutive_matrix(E, nu, project.analysis_type)
    D_factor = E / (1.0 - nu * nu)

    # ─── Energia por elemento -> showcase = max energia ──────────────────
    energies = {}
    for eid, elem in project.elements.items():
        ke = edata[eid]["ke"]
        dof = edata[eid]["dof_indices"]
        ue = u[dof]
        energies[eid] = 0.5 * float(ue @ ke @ ue)
    show_id = max(energies, key=energies.get)
    show_elem = project.elements[show_id]
    show_nodes = list(show_elem.node_ids)

    print("=" * 64)
    print("EJEMPLO CANONICO Q4 — resumen")
    print("=" * 64)
    print(f"E={E}  nu={nu}  t={t}  D_factor=E/(1-nu^2)={D_factor}")
    print("Energias de deformacion por elemento Ue=1/2 ue^T ke ue:")
    for eid in sorted(energies):
        mark = "  <== showcase (max)" if eid == show_id else ""
        print(f"  E{eid} (nodos {project.elements[eid].node_ids}): "
              f"Ue={energies[eid]:.6g}{mark}")

    # ─── Cadena educativa del showcase en cada GP ────────────────────────
    node_coords = np.array(
        [[project.nodes[nid].x, project.nodes[nid].y] for nid in show_nodes]
    )
    _, dN_func = get_shape_functions(project.element_type)
    gpts, gwts = get_gauss_points_for_element(project.element_type)

    chain = []   # por GP: dict con dN_nat, J, detJ, invJ, dN_phys, B
    detJ_list = []
    for (xi, eta), w in zip(gpts, gwts):
        dN_nat = dN_func(xi, eta)
        J, detJ, invJ = compute_jacobian(dN_nat, node_coords)
        dN_phys = compute_dN_physical(dN_nat, invJ)
        B = compute_b_matrix(dN_phys)
        chain.append(dict(xi=xi, eta=eta, w=w, dN_nat=dN_nat, J=J,
                          detJ=detJ, invJ=invJ, dN_phys=dN_phys, B=B))
        detJ_list.append(detJ)

    ke_show = edata[show_id]["ke"]
    ue_show = u[edata[show_id]["dof_indices"]]

    g0 = chain[0]   # GP representativo: (-1/sqrt3, -1/sqrt3)
    # Recuperacion de tension en GP0: eps = B u_e, sigma = D eps
    eps0 = g0["B"] @ ue_show
    sig0 = D @ eps0

    print(f"\nShowcase: E{show_id}  nodos {show_nodes}")
    print(f"det J en los 4 GP: {[round(d,4) for d in detJ_list]}")
    print(f"GP0 (xi=eta=-1/sqrt3): eps={eps0}  sigma={sig0}")

    # ─── Tensiones del showcase (GP + nodal extrapolada) ─────────────────
    gs = elem_stresses[show_id]["gauss_stresses"]
    ns = elem_stresses[show_id]["nodal_stresses"]

    # ─── Displacements per node ──────────────────────────────────────────
    print("\nDesplazamientos nodales:")
    umax_abs, umax_node, umax_comp = 0.0, None, None
    for nid in sorted(project.nodes):
        ix = 2 * idx_map[nid]
        ux, uy = u[ix], u[ix + 1]
        print(f"  N{nid}: ux={ux: .6e}  uy={uy: .6e}")
        for comp, val in (("ux", ux), ("uy", uy)):
            if abs(val) > umax_abs:
                umax_abs, umax_node, umax_comp = abs(val), nid, comp
    mag = {nid: np.hypot(u[2 * idx_map[nid]], u[2 * idx_map[nid] + 1])
           for nid in project.nodes}
    umag_node = max(mag, key=mag.get)
    umag_val = mag[umag_node]

    # ─── Reacciones ──────────────────────────────────────────────────────
    print("\nReacciones (nodos restringidos):")
    Rx_tot = Ry_tot = 0.0
    for nid in sorted(project.boundary_conditions):
        ix = 2 * idx_map[nid]
        rx, ry = reactions[ix], reactions[ix + 1]
        Rx_tot += rx
        Ry_tot += ry
        print(f"  N{nid}: Rx={rx: .4f}  Ry={ry: .4f}")
    print(f"  Suma Rx={Rx_tot:.4f}  Ry={Ry_tot:.4f}  (equilibra Fy=-1000)")

    # ─── von Mises nodal (promedio) ──────────────────────────────────────
    vm_max, vm_node = 0.0, None
    for nid, d in nodal_avg.items():
        if d["von_mises"] > vm_max:
            vm_max, vm_node = d["von_mises"], nid
    print(f"\nvon Mises nodal max: {vm_max:.4f} en N{vm_node}")

    # ════════════════════════════════════════════════════════════════════
    #  MACROS LaTeX
    # ════════════════════════════════════════════════════════════════════
    M = {}

    # Datos escalares
    M["valE"] = es(E, 0)
    M["valNu"] = es(nu, 1)
    M["valT"] = es(t, 1)
    M["valP"] = "1000"
    M["valDfactor"] = es(D_factor, 0)
    M["showId"] = str(show_id)
    M["showNodes"] = ", ".join(str(n) for n in show_nodes)
    M["nFree"] = str(len(free_dofs))
    M["nRestr"] = str(len(restr_dofs))
    M["nDof"] = str(project.total_dof)

    # Celdas numericas envueltas en $...$ (convencion de las tablas de la
    # tesis: columnas planas, numeros en modo math para signo menos y coma).
    def m(s):
        return f"${s}$"

    # Tabla de nodos
    nrows = []
    for nid in sorted(project.nodes):
        n = project.nodes[nid]
        nrows.append(f"{nid} & {m(es(n.x,1))} & {m(es(n.y,1))}")
    M["nodosRows"] = " \\\\\n".join(nrows)

    # Tabla de elementos
    erows = []
    for eid in sorted(project.elements):
        e = project.elements[eid]
        conn = " & ".join(str(n) for n in e.node_ids)
        erows.append(f"E{eid} & {conn} & {m(es(e.thickness,1))}")
    M["elementosRows"] = " \\\\\n".join(erows)

    # D
    Dn = D / D_factor
    M["Dmat"] = bmat(D, 2)
    M["DmatNorm"] = bmat(Dn, 2)

    # Showcase: coords, cadena en GP0, ke
    M["Xemat"] = bmat(node_coords, 1)
    M["gpA"] = f"\\left(-\\tfrac{{1}}{{\\sqrt{{3}}}},\\,-\\tfrac{{1}}{{\\sqrt{{3}}}}\\right)"
    M["dNnatA"] = bmat(g0["dN_nat"], 4)
    M["Jmata"] = bmat(g0["J"], 4)
    M["detJa"] = es(g0["detJ"], 4)
    M["invJa"] = bmat(g0["invJ"], 5)
    M["dNphysA"] = bmat(g0["dN_phys"], 5)
    M["Bmata"] = bmat(g0["B"], 4)
    # k_e escalada por 10^3 para que la 8x8 entre en pagina con holgura.
    M["keMat"] = bmat(ke_show / 1e3, 1)
    M["keScale"] = "10^{3}"

    # det J en los 4 GP (para la suma de cuadratura)
    M["detJrow"] = " & ".join(es(d, 4) for d in detJ_list)
    M["detJinline"] = ",\\ ".join(es(d, 4) for d in detJ_list)  # uso inline (sin &)
    M["weightsRow"] = " & ".join(es(w, 0) for w in gwts)

    # Energias por elemento (tabla + version inline para el texto)
    en_rows = []
    en_inline = []
    for eid in sorted(energies):
        en_rows.append(f"E{eid} & {m(es_sci(energies[eid],3))}")
        en_inline.append(f"E{eid}\\ {m(es(energies[eid],2))}")
    M["energiaRows"] = " \\\\\n".join(en_rows)
    M["energiaInline"] = ";\\ ".join(en_inline)

    # Vector F reducido (12) — solo -1000 en la fila de N7-y
    Ff = F[np.asarray(free_dofs)]
    M["FfVec"] = colvec(Ff, 0)

    # Mapa GDL libres (texto)
    M["freeDofList"] = ", ".join(str(d) for d in free_dofs)
    M["restrDofList"] = ", ".join(str(d) for d in restr_dofs)

    # Recuperacion de tension en GP0
    M["epsA"] = colvec(eps0, 6, fmt=es_sci if max(abs(eps0)) < 1e-2 else es)
    M["sigA"] = colvec(sig0, 3)

    # Tensiones principales y von Mises en GP0 (cadena exacta del software:
    # s1,s2 = avg +/- R; vm = sqrt(s1^2 - s1*s2 + s2^2)).
    sx0, sy0, txy0 = float(sig0[0]), float(sig0[1]), float(sig0[2])
    savg0 = 0.5 * (sx0 + sy0)
    R0 = float(np.hypot(0.5 * (sx0 - sy0), txy0))
    s1_0, s2_0 = savg0 + R0, savg0 - R0
    vm0 = float(np.sqrt(s1_0 * s1_0 - s1_0 * s2_0 + s2_0 * s2_0))
    M["savgA"] = es(savg0, 3)
    M["radiusA"] = es(R0, 3)
    M["sigOneA"] = es(s1_0, 3)
    M["sigTwoA"] = es(s2_0, 3)
    M["vmA"] = es(vm0, 2)

    # Extrapolacion Q4: matriz constante 4x4 (basada en +/- sqrt 3) que lleva
    # los 4 PG a los 4 nodos. Misma matriz que fem.stress._build_q4_extrap.
    sq = np.sqrt(3.0)
    Eex = 0.25 * np.array([
        [(1+sq)*(1+sq), (1-sq)*(1+sq), (1-sq)*(1-sq), (1+sq)*(1-sq)],
        [(1+sq)*(1-sq), (1-sq)*(1-sq), (1-sq)*(1+sq), (1+sq)*(1+sq)],
        [(1-sq)*(1-sq), (1+sq)*(1-sq), (1+sq)*(1+sq), (1-sq)*(1+sq)],
        [(1-sq)*(1+sq), (1+sq)*(1+sq), (1+sq)*(1-sq), (1-sq)*(1-sq)],
    ])
    sigx_g = np.array([float(g["sigma_x"]) for g in gs])      # PG: orden 1..4
    sigx_n = Eex @ sigx_g                                     # nodos: orden 4,5,8,7
    M["Eextrap"] = bmat(Eex, 4)
    M["sigxGauss"] = colvec(sigx_g, 2)
    M["sigxNodal"] = colvec(sigx_n, 2)

    # Desplazamientos nodales (tabla, en notacion cientifica)
    drows = []
    for nid in sorted(project.nodes):
        ix = 2 * idx_map[nid]
        drows.append(f"{nid} & {m(es_sci(u[ix],4))} & {m(es_sci(u[ix+1],4))}")
    M["despRows"] = " \\\\\n".join(drows)

    # Reacciones (tabla)
    rrows = []
    for nid in sorted(project.boundary_conditions):
        ix = 2 * idx_map[nid]
        rrows.append(f"{nid} & {m(es(reactions[ix],2))} & {m(es(reactions[ix+1],2))}")
    M["reaccRows"] = " \\\\\n".join(rrows)
    M["RxTot"] = es(Rx_tot, 2)
    M["RyTot"] = es(Ry_tot, 2)

    # Tensiones en GP del showcase
    gsrows = []
    for k, gd in enumerate(gs, 1):
        gsrows.append(
            f"{k} & {m(es(gd['sigma_x'],2))} & {m(es(gd['sigma_y'],2))} & "
            f"{m(es(gd['tau_xy'],2))} & {m(es(gd['von_mises'],2))}")
    M["gaussStressRows"] = " \\\\\n".join(gsrows)

    # Tensiones nodales (extrapoladas) del showcase
    nsrows = []
    for nid, d in zip(show_nodes, ns):
        nsrows.append(
            f"{nid} & {m(es(d['sigma_x'],2))} & {m(es(d['sigma_y'],2))} & "
            f"{m(es(d['tau_xy'],2))} & {m(es(d['von_mises'],2))}")
    M["nodalStressShowRows"] = " \\\\\n".join(nsrows)

    # von Mises nodal promediado (todos los nodos)
    vmrows = []
    for nid in sorted(project.nodes):
        d = nodal_avg.get(nid, {})
        vmrows.append(
            f"{nid} & {m(es(d.get('sigma_x',0),2))} & {m(es(d.get('sigma_y',0),2))} & "
            f"{m(es(d.get('tau_xy',0),2))} & {m(es(d.get('von_mises',0),2))}")
    M["vmNodalRows"] = " \\\\\n".join(vmrows)

    # Tabla unificada de resultados nodales (desplazamientos + tensiones) —
    # una sola tabla a ancho completo evita el solapamiento de dos minipages.
    allrows = []
    for nid in sorted(project.nodes):
        ix = 2 * idx_map[nid]
        d = nodal_avg.get(nid, {})
        allrows.append(
            f"{nid} & {m(es_sci(u[ix],3))} & {m(es_sci(u[ix+1],3))} & "
            f"{m(es(d.get('sigma_x',0),2))} & {m(es(d.get('sigma_y',0),2))} & "
            f"{m(es(d.get('tau_xy',0),2))} & {m(es(d.get('von_mises',0),2))}")
    M["nodalAllRows"] = " \\\\\n".join(allrows)

    # Resumen final
    M["umaxMag"] = es_sci(umag_val, 4)
    M["umaxNode"] = str(umag_node)
    M["vmMax"] = es(vm_max, 2)
    M["vmMaxNode"] = str(vm_node)
    M["umaxComp"] = umax_comp
    M["umaxCompVal"] = es_sci(umax_abs, 4)
    M["umaxCompNode"] = str(umax_node)

    # ─── Escribir el archivo de macros ───────────────────────────────────
    out_tex = os.path.join(_HERE, "anexo_calculo_data.tex")
    with open(out_tex, "w", encoding="utf-8") as f:
        f.write("% Generado por gen_anexo_calculo.py — NO editar a mano.\n")
        f.write("% Numeros bit-exactos del motor de EduFEM (ejemplo Q4).\n\n")
        for name in sorted(M):
            val = M[name]
            f.write(f"\\newcommand{{\\{name}}}{{{val}}}\n")
    print(f"\n[OK] macros -> {out_tex}  ({len(M)} comandos)")

    # ════════════════════════════════════════════════════════════════════
    #  FIGURAS (estilo software, Pillow, fondo blanco, jet)
    # ════════════════════════════════════════════════════════════════════
    import file_io.figure_export as fx
    # Etiquetas limpias en los titulos baked-in de las figuras.
    fx._COMPONENT_LABELS["von_mises"] = "von Mises"

    project.is_solved = True
    project.displacements = u

    figs = {
        "mem_modelo.png": fx.render_mesh_diagram(project),
        "mem_Ksparsity.png": fx.render_K_sparsity(K),
        "mem_contorno_vm.png": fx.render_contour(
            project, sol, nodal_avg, "von_mises", deformed=True),
        "mem_deformada.png": fx.render_deformed(project, sol),
    }
    for fname, img in figs.items():
        if img is None:
            print(f"[WARN] figura None: {fname}")
            continue
        path = os.path.join(_HERE, fname)
        img.save(path)
        print(f"[OK] figura -> {path}  ({img.size[0]}x{img.size[1]})")

    print("\nListo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
