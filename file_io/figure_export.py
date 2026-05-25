"""
Generacion de figuras matplotlib off-screen para la Memoria de Calculo.

Diseñado para ejecutarse fuera del hilo principal de Tk: NO usa pyplot
(que mantiene estado global), construye Figure(...) directo y devuelve
el objeto. El caller hace `fig.savefig(path)` y borra los temporales.

Funciones expuestas:
  - render_mesh_diagram(project): geometria + nodos + BCs + cargas.
  - render_contour(project, solution, nodal_stresses, component): mapa
    de contornos para sigma_x / sigma_y / tau_xy / von_mises.
  - render_deformed(project, solution, scale=None): malla original
    superpuesta con la deformada (escala automatica si None).
  - render_mohr_circle(sigma_x, sigma_y, tau_xy, label=""): circulo de
    Mohr para un punto (showcase del Capitulo 3).
  - render_extrapolation_diagram(): esquema didactico Gauss -> nodos.
  - render_averaging_diagram(): esquema didactico promediado nodal.
  - render_fem_pipeline(): hoja de ruta del metodo (Cap 0).
  - render_principal_crosses(project, nodal_stresses): cruces sigma1/sigma2
    sobre la malla (consolidado del ex-modulo M8).

Convenciones:
  - Fondo blanco (las figuras viven en un PDF impreso, NO en la GUI dark).
  - Acentos (BCs, cargas, nodos por rol Q9, principales) usan la paleta
    semantica del proyecto definida en `config.settings` — asi el alumno
    reconoce los mismos codigos visuales que ve en el canvas de la GUI.
  - Colormaps cientificos (viridis, coolwarm) permanecen iguales a los
    del Post-Proceso para mantener consistencia interpretativa.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import (
    Circle as _Circle,
    FancyArrowPatch as _FancyArrowPatch,
    FancyBboxPatch as _FancyBboxPatch,
    Polygon as _Polygon,
)
from matplotlib.collections import PatchCollection
from matplotlib.tri import Triangulation

from config.settings import (
    CANVAS_NODE_COLOR,
    CANVAS_NODE_MID_COLOR,
    CANVAS_NODE_CENTER_COLOR,
    CANVAS_CONSTRAINT_COLOR,
    CANVAS_LOAD_COLOR,
    CANVAS_ELEMENT_COLOR,
    ELEMENT_Q9,
    PHASE_PRE_COLOR,
    PHASE_PROC_COLOR,
    PHASE_POST_COLOR,
)


_FIG_DPI = 150
_FIG_FACECOLOR = "white"

# Paleta semantica para figuras de la memoria. Importadas como hex (matplotlib
# acepta strings hex sin transformacion). Cumple la regla "cero hex literales
# fuera de config/settings.py" de CLAUDE.md.
_COLOR_NODE_CORNER = CANVAS_NODE_COLOR
_COLOR_NODE_MID = CANVAS_NODE_MID_COLOR
_COLOR_NODE_CENTER = CANVAS_NODE_CENTER_COLOR
_COLOR_CONSTRAINT = CANVAS_CONSTRAINT_COLOR
_COLOR_LOAD = CANVAS_LOAD_COLOR
_COLOR_ELEMENT_FACE = "#dde9f7"   # rellenos suaves (legibles en papel)
_COLOR_ELEMENT_EDGE = "#3a6fb5"
_COLOR_ELEMENT_LABEL = "#1a3a6b"
_COLOR_PRINCIPAL_TENSILE = "#1565c0"   # sigma_1 traccion (azul fuerte)
_COLOR_PRINCIPAL_COMPRESS = "#c62828"  # sigma_2 compresion (rojo fuerte)

# Rellenos suaves para simbolos BC sobre fondo blanco (versiones claras
# de los rellenos del canvas oscuro: #3a2a10 empotramiento, #1a3a4a roller).
_FILL_BC_FIXED = "#fce9d4"
_FILL_BC_ROLLER = "#dceaf2"


def _draw_bc_symbol(ax, x: float, y: float, bc_kind: str,
                    *, scale: float, color: str) -> None:
    """Dibuja un simbolo de restriccion replicando el lenguaje del canvas.

    Tres pictogramas distintos siguiendo la notacion estandar de mecanica
    estructural, EXACTAMENTE como los dibuja `gui/preprocessing/mesh_canvas.py`
    en la GUI (lineas 987-1100), pero adaptados a matplotlib + fondo blanco
    para que el alumno reconozca el mismo simbolo en la Memoria que ve
    interactivamente.

    Args:
        ax: matplotlib Axes destino.
        x, y: coordenadas del nodo (en unidades del dato).
        bc_kind: "fixed" (empotramiento), "roller_y" (rodillo horizontal),
                 "roller_x" (rodillo vertical), o "pin" (fallback generico).
        scale: tamano caracteristico del simbolo en unidades del dato
               (~5-10% del bbox de la malla).
        color: color del outline + hachuras (tipicamente CANVAS_CONSTRAINT_COLOR).
    """
    from matplotlib.patches import Polygon as MplPolygon, Circle as MplCircle
    from matplotlib.lines import Line2D

    s = scale
    lw = 1.2
    lw_hatch = 0.8

    if bc_kind == "fixed":
        # Triangulo apuntando ARRIBA al nodo + linea base + hachuras debajo.
        tri = MplPolygon(
            [(x, y), (x - s, y - 2 * s), (x + s, y - 2 * s)],
            closed=True, facecolor=_FILL_BC_FIXED, edgecolor=color,
            linewidth=lw, zorder=4,
        )
        ax.add_patch(tri)
        # Linea base (la "pared")
        ax.plot([x - s - 0.4 * s, x + s + 0.4 * s],
                [y - 2 * s, y - 2 * s],
                color=color, linewidth=lw + 0.3, zorder=4,
                solid_capstyle="round")
        # Hachuras (3 lineas inclinadas debajo)
        for i in range(3):
            lx = x - s + i * s
            ax.plot([lx, lx - 0.5 * s], [y - 2 * s, y - 2.5 * s],
                    color=color, linewidth=lw_hatch, zorder=4)

    elif bc_kind == "roller_x":
        # Restringe Δx -> apoyado a la izquierda del nodo.
        # Triangulo con vertice al nodo + rodillo (circulo) + pared vertical.
        tri_base_x = x - s
        tri_top_x = tri_base_x - s
        tri = MplPolygon(
            [(x, y), (tri_base_x, y - s), (tri_base_x, y + s)],
            closed=True, facecolor=_FILL_BC_ROLLER, edgecolor=color,
            linewidth=lw, zorder=4,
        )
        ax.add_patch(tri)
        # Rodillo
        roller_cx = tri_top_x - 0.3 * s
        circ = MplCircle((roller_cx, y), 0.35 * s,
                         facecolor=_FILL_BC_ROLLER, edgecolor=color,
                         linewidth=lw_hatch, zorder=4)
        ax.add_patch(circ)
        # Pared vertical
        wall_x = roller_cx - 0.55 * s
        ax.plot([wall_x, wall_x], [y - s - 0.4 * s, y + s + 0.4 * s],
                color=color, linewidth=lw + 0.3, zorder=4,
                solid_capstyle="round")
        # Hachuras (3 lineas inclinadas detras de la pared)
        for i in range(3):
            yy = y - s + i * s
            ax.plot([wall_x, wall_x - 0.5 * s], [yy, yy - 0.5 * s],
                    color=color, linewidth=lw_hatch, zorder=4)

    elif bc_kind == "roller_y":
        # Restringe Δy -> apoyado debajo del nodo.
        # Triangulo apuntando ABAJO al nodo + rodillo + linea horizontal.
        tri_base_y = y - s
        tri_top_y = tri_base_y - s
        tri = MplPolygon(
            [(x, y), (x - s, tri_base_y), (x + s, tri_base_y)],
            closed=True, facecolor=_FILL_BC_ROLLER, edgecolor=color,
            linewidth=lw, zorder=4,
        )
        ax.add_patch(tri)
        # Rodillo (circulo) entre triangulo y la superficie horizontal
        roller_cy = tri_top_y - 0.3 * s
        circ = MplCircle((x, roller_cy), 0.35 * s,
                         facecolor=_FILL_BC_ROLLER, edgecolor=color,
                         linewidth=lw_hatch, zorder=4)
        ax.add_patch(circ)
        # Superficie horizontal donde rueda
        surf_y = roller_cy - 0.55 * s
        ax.plot([x - s - 0.4 * s, x + s + 0.4 * s], [surf_y, surf_y],
                color=color, linewidth=lw + 0.3, zorder=4,
                solid_capstyle="round")
        # Hachuras debajo
        for i in range(3):
            xx = x - s + i * s
            ax.plot([xx, xx - 0.5 * s], [surf_y, surf_y - 0.5 * s],
                    color=color, linewidth=lw_hatch, zorder=4)

    else:
        # Fallback generico (pin): triangulo hueco simple.
        tri = MplPolygon(
            [(x, y), (x - s, y - 1.5 * s), (x + s, y - 1.5 * s)],
            closed=True, facecolor="none", edgecolor=color,
            linewidth=lw + 0.3, zorder=4,
        )
        ax.add_patch(tri)


def _classify_bc(bc) -> str:
    """Identifica el tipo de simbolo BC a dibujar.

    Replica la clasificacion del canvas: empotramiento si restringe ambas
    direcciones, rodillo Y si solo restringe Y (puede deslizar en X),
    rodillo X si solo restringe X.
    """
    if bc.restrain_x and bc.restrain_y:
        return "fixed"
    elif bc.restrain_y and not bc.restrain_x:
        return "roller_y"
    elif bc.restrain_x and not bc.restrain_y:
        return "roller_x"
    return "pin"


# ---------------------------------------------------------------------------
# Diagrama del modelo
# ---------------------------------------------------------------------------

def render_mesh_diagram(project) -> Figure:
    """Figura standalone con malla, nodos numerados, BCs y cargas.

    Aspecto pedagogico: ayuda al lector a ubicar geometricamente los
    nodos / elementos referenciados en las tablas.
    """
    fig = Figure(figsize=(7.0, 5.5), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="datalim")

    if not project.nodes:
        ax.text(0.5, 0.5, "Modelo sin nodos", ha="center", va="center",
                transform=ax.transAxes, color="gray")
        ax.set_axis_off()
        return fig

    # Polígonos de elementos
    patches = []
    for elem in project.elements.values():
        coords = []
        # Solo vertices macro (primeros 4) para Q4/Q9
        for nid in list(elem.node_ids)[:4]:
            if nid in project.nodes:
                node = project.nodes[nid]
                coords.append([node.x, node.y])
        if len(coords) >= 3:
            patches.append(_Polygon(coords, closed=True))
    if patches:
        pc = PatchCollection(patches, facecolor=_COLOR_ELEMENT_FACE,
                             edgecolor=_COLOR_ELEMENT_EDGE, linewidths=1.2,
                             alpha=0.9)
        ax.add_collection(pc)

    # Etiquetas de elementos en el centroide
    for eid, elem in project.elements.items():
        coords = [
            [project.nodes[nid].x, project.nodes[nid].y]
            for nid in list(elem.node_ids)[:4]
            if nid in project.nodes
        ]
        if len(coords) >= 3:
            cx = float(np.mean([c[0] for c in coords]))
            cy = float(np.mean([c[1] for c in coords]))
            ax.text(cx, cy, f"E{eid}", ha="center", va="center",
                    fontsize=9, color=_COLOR_ELEMENT_LABEL,
                    fontweight="bold")

    # Nodos diferenciados por rol Q9 (corner/mid/center) — mismo codigo
    # visual que el canvas. En Q4 todos son corner.
    is_q9 = getattr(project, "element_type", None) == ELEMENT_Q9
    corner_nids: set[int] = set()
    mid_nids: set[int] = set()
    center_nids: set[int] = set()
    if is_q9:
        for elem in project.elements.values():
            ids = list(elem.node_ids)
            if len(ids) >= 4:
                corner_nids.update(ids[:4])
            if len(ids) >= 8:
                mid_nids.update(ids[4:8])
            if len(ids) >= 9:
                center_nids.add(ids[8])
        # Resolver solapes: corner gana sobre mid/center
        mid_nids -= corner_nids
        center_nids -= corner_nids | mid_nids
    else:
        corner_nids = set(project.nodes.keys())

    def _scatter_group(nids: set[int], color: str, size: float):
        if not nids:
            return
        xs_g = [project.nodes[n].x for n in nids if n in project.nodes]
        ys_g = [project.nodes[n].y for n in nids if n in project.nodes]
        if xs_g:
            ax.scatter(xs_g, ys_g, s=size, c=color, zorder=3,
                       edgecolors="black", linewidths=0.4)

    _scatter_group(corner_nids, _COLOR_NODE_CORNER, 28)
    _scatter_group(mid_nids, _COLOR_NODE_MID, 18)
    _scatter_group(center_nids, _COLOR_NODE_CENTER, 18)

    for nid, n in project.nodes.items():
        ax.annotate(str(nid), (n.x, n.y), xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=8, color=_COLOR_ELEMENT_LABEL)

    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]

    # BCs: simbolos canvas (empotramiento + rodillos) en fondo blanco.
    # Escala derivada del bbox de la malla (mismo criterio que el canvas).
    if xs and ys:
        bbox_extent = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
        bc_scale = 0.025 * bbox_extent
    else:
        bc_scale = 0.05
    for nid, bc in project.boundary_conditions.items():
        if nid not in project.nodes:
            continue
        if not (bc.restrain_x or bc.restrain_y):
            continue
        n = project.nodes[nid]
        kind = _classify_bc(bc)
        _draw_bc_symbol(ax, n.x, n.y, kind,
                        scale=bc_scale, color=_COLOR_CONSTRAINT)

    # Cargas nodales (flechas)
    if project.nodal_loads:
        # Escalar las flechas al ~10% del rango de coords
        rng_x = (max(xs) - min(xs)) if len(xs) > 1 else 1.0
        rng_y = (max(ys) - min(ys)) if len(ys) > 1 else 1.0
        scale_ref = 0.12 * max(rng_x, rng_y, 1e-6)
        max_mag = max(
            (abs(ld.fx) ** 2 + abs(ld.fy) ** 2) ** 0.5
            for ld in project.nodal_loads.values()
        ) or 1.0
        for nid, ld in project.nodal_loads.items():
            if nid not in project.nodes:
                continue
            n = project.nodes[nid]
            mag = (ld.fx ** 2 + ld.fy ** 2) ** 0.5
            if mag <= 1e-12:
                continue
            ux = ld.fx / mag
            uy = ld.fy / mag
            length = scale_ref * (mag / max_mag)
            ax.annotate(
                "", xytext=(n.x - ux * length, n.y - uy * length),
                xy=(n.x, n.y),
                arrowprops=dict(arrowstyle="->", color=_COLOR_LOAD, lw=1.8),
            )

    ax.set_title("Modelo discretizado", fontsize=11)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, linestyle=":", alpha=0.4)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Contornos
# ---------------------------------------------------------------------------

_COMPONENT_LABELS = {
    "sigma_x": (r"$\sigma_x$", "coolwarm"),
    "sigma_y": (r"$\sigma_y$", "coolwarm"),
    "tau_xy":  (r"$\tau_{xy}$", "coolwarm"),
    "von_mises": (r"$\sigma_{VM}$", "viridis"),
}


def render_contour(project, solution, nodal_stresses, component: str,
                   *, deformed: bool = False, scale: Optional[float] = None) -> Figure:
    """Mapa de contornos para una componente nodal promediada.

    component ∈ {"sigma_x", "sigma_y", "tau_xy", "von_mises"}.
    Si `deformed=True`, evalua sobre la geometria deformada.
    """
    label, cmap = _COMPONENT_LABELS.get(
        component, (component, "viridis"))
    fig = Figure(figsize=(7.0, 5.5), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="datalim")

    if not nodal_stresses or not project.nodes or not project.elements:
        ax.text(0.5, 0.5, "Sin datos para contorno",
                ha="center", va="center", transform=ax.transAxes,
                color="gray")
        ax.set_axis_off()
        return fig

    # Triangulacion: dividimos cada Q4/Q9 macro en 2 triangulos por las
    # 4 esquinas (suficiente para isolineas; el detalle Q9 promediado ya
    # esta en nodal_stresses).
    nid_list = sorted(project.nodes.keys())
    nid_to_idx = {nid: i for i, nid in enumerate(nid_list)}

    coords_x = np.array([project.nodes[nid].x for nid in nid_list])
    coords_y = np.array([project.nodes[nid].y for nid in nid_list])

    if deformed and solution is not None:
        u = solution["u"]
        idx_map = project.node_index_map
        ux = np.array([u[2 * idx_map[nid]] for nid in nid_list])
        uy = np.array([u[2 * idx_map[nid] + 1] for nid in nid_list])
        if scale is None:
            extent = max(
                coords_x.max() - coords_x.min(),
                coords_y.max() - coords_y.min(),
                1e-9,
            )
            max_disp = max(np.abs(ux).max(), np.abs(uy).max(), 1e-12)
            scale = 0.10 * extent / max_disp
        coords_x = coords_x + scale * ux
        coords_y = coords_y + scale * uy

    triangles = []
    for elem in project.elements.values():
        nids = [n for n in list(elem.node_ids)[:4] if n in nid_to_idx]
        if len(nids) != 4:
            continue
        a, b, c, d = (nid_to_idx[n] for n in nids)
        triangles.append([a, b, c])
        triangles.append([a, c, d])
    if not triangles:
        ax.text(0.5, 0.5, "Triangulacion vacia",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return fig

    triang = Triangulation(coords_x, coords_y, triangles)
    values = np.array([
        nodal_stresses.get(nid, {}).get(component, 0.0)
        for nid in nid_list
    ])

    cf = ax.tricontourf(triang, values, levels=18, cmap=cmap)
    ax.tricontour(triang, values, levels=10, colors="k",
                  linewidths=0.4, alpha=0.4)

    # Borde de elementos (siluetas)
    for elem in project.elements.values():
        nids = [n for n in list(elem.node_ids)[:4] if n in project.nodes]
        if len(nids) < 3:
            continue
        xs = [project.nodes[n].x for n in nids] + [project.nodes[nids[0]].x]
        ys = [project.nodes[n].y for n in nids] + [project.nodes[nids[0]].y]
        if deformed and solution is not None:
            idx_map = project.node_index_map
            xs = [
                project.nodes[n].x + scale * solution["u"][2 * idx_map[n]]
                for n in nids
            ]
            ys = [
                project.nodes[n].y + scale * solution["u"][2 * idx_map[n] + 1]
                for n in nids
            ]
            xs.append(xs[0])
            ys.append(ys[0])
        ax.plot(xs, ys, color="black", linewidth=0.6, alpha=0.5)

    cbar = fig.colorbar(cf, ax=ax, shrink=0.85, pad=0.03)
    cbar.set_label(label)
    title = f"Contorno de {label}"
    if deformed:
        title += "  (sobre malla deformada)"
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Deformada
# ---------------------------------------------------------------------------

def render_deformed(project, solution, scale: Optional[float] = None) -> Figure:
    """Malla original (gris) + malla deformada (color)."""
    fig = Figure(figsize=(7.0, 5.5), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="datalim")

    if not project.elements or solution is None:
        ax.text(0.5, 0.5, "Sin datos",
                ha="center", va="center", transform=ax.transAxes,
                color="gray")
        ax.set_axis_off()
        return fig

    u = solution["u"]
    nid_list = list(project.nodes.keys())
    idx_map = project.node_index_map
    coords_x = np.array([project.nodes[nid].x for nid in nid_list])
    coords_y = np.array([project.nodes[nid].y for nid in nid_list])
    ux = np.array([u[2 * idx_map[nid]] for nid in nid_list])
    uy = np.array([u[2 * idx_map[nid] + 1] for nid in nid_list])

    if scale is None:
        extent = max(
            coords_x.max() - coords_x.min(),
            coords_y.max() - coords_y.min(),
            1e-9,
        )
        max_disp = max(np.abs(ux).max(), np.abs(uy).max(), 1e-12)
        scale = 0.10 * extent / max_disp

    # Malla original (gris discontinua: contexto)
    for elem in project.elements.values():
        nids = [n for n in list(elem.node_ids)[:4] if n in project.nodes]
        if len(nids) < 3:
            continue
        xs = [project.nodes[n].x for n in nids] + [project.nodes[nids[0]].x]
        ys = [project.nodes[n].y for n in nids] + [project.nodes[nids[0]].y]
        ax.plot(xs, ys, color="#aaaaaa", linewidth=0.8, linestyle="--",
                alpha=0.6)

    # Malla deformada (verde: post-proceso, consistente con fase canvas)
    nid_to_idx = {nid: i for i, nid in enumerate(nid_list)}
    for elem in project.elements.values():
        nids = [n for n in list(elem.node_ids)[:4] if n in nid_to_idx]
        if len(nids) < 3:
            continue
        xs_def = [coords_x[nid_to_idx[n]] + scale * ux[nid_to_idx[n]]
                  for n in nids]
        ys_def = [coords_y[nid_to_idx[n]] + scale * uy[nid_to_idx[n]]
                  for n in nids]
        xs_def.append(xs_def[0])
        ys_def.append(ys_def[0])
        ax.plot(xs_def, ys_def, color=PHASE_POST_COLOR, linewidth=1.4)

    # Nodos sobre la deformada (estilo canvas: puntos pequeños azul claro
    # en cada nodo de la malla deformada — mismo lenguaje visual que el
    # Post-tab cuando muestra la geometria deformada).
    xs_def_all = coords_x + scale * ux
    ys_def_all = coords_y + scale * uy
    ax.scatter(xs_def_all, ys_def_all, s=18, c=_COLOR_NODE_CORNER,
               zorder=4, edgecolors="black", linewidths=0.3)

    ax.set_title(f"Configuración deformada (escala $\\times {scale:.3g}$)",
                 fontsize=11)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, linestyle=":", alpha=0.4)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Circulo de Mohr
# ---------------------------------------------------------------------------

def render_K_heatmap(K: np.ndarray, *, log_scale: bool = True,
                     title: str = "Matriz de rigidez global $\\mathbf{K}$") -> Figure:
    """Heatmap de |K| (log-scale por defecto) para visualizar densidad y
    estructura de banda. Apropiado cuando K es demasiado grande para
    renderizarse literal (n_dof > 24)."""
    fig = Figure(figsize=(6.5, 5.5), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax = fig.add_subplot(111)
    M = np.asarray(K)
    if log_scale:
        eps = max(1e-30, float(np.abs(M).max()) * 1e-12)
        data = np.log10(np.abs(M) + eps)
        cmap = "viridis"
        cbar_label = r"$\log_{10} |K_{ij}|$"
    else:
        data = M
        cmap = "coolwarm"
        cbar_label = r"$K_{ij}$"
    im = ax.imshow(data, cmap=cmap, aspect="equal",
                   interpolation="nearest")
    cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.03)
    cbar.set_label(cbar_label)
    ax.set_xlabel("Columna (GDL)")
    ax.set_ylabel("Fila (GDL)")
    ax.set_title(title, fontsize=11)
    fig.tight_layout()
    return fig


def render_mohr_circle(sigma_x: float, sigma_y: float, tau_xy: float,
                       label: str = "") -> Figure:
    """Circulo de Mohr para un punto: muestra sigma_x, sigma_y, tau_xy
    y los principales sigma_1, sigma_2."""
    fig = Figure(figsize=(6.5, 5.5), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="datalim")

    cx = 0.5 * (sigma_x + sigma_y)
    R = float(np.sqrt(((sigma_x - sigma_y) / 2.0) ** 2 + tau_xy ** 2))
    sigma_1 = cx + R
    sigma_2 = cx - R

    # Circulo (color de fase Pre — analogos al diagrama nativo del Post)
    theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(cx + R * np.cos(theta), R * np.sin(theta),
            color=PHASE_PRE_COLOR, linewidth=1.6)

    # Estado actual: punto X (sigma_x, -tau_xy) y Y (sigma_y, +tau_xy)
    ax.scatter([sigma_x], [-tau_xy], s=44, color=_COLOR_PRINCIPAL_COMPRESS,
               zorder=5, label=r"$X = (\sigma_x, -\tau_{xy})$")
    ax.scatter([sigma_y], [tau_xy], s=44, color=PHASE_POST_COLOR,
               zorder=5, label=r"$Y = (\sigma_y, +\tau_{xy})$")
    ax.plot([sigma_x, sigma_y], [-tau_xy, tau_xy],
            color="#888888", linestyle="--", linewidth=1.0)

    # Principales: sigma_1 azul (traccion), sigma_2 rojo (compresion).
    # Mismo codigo del canvas y del overlay PrincipalCrossLayer.
    ax.scatter([sigma_1], [0], s=58, color=_COLOR_PRINCIPAL_TENSILE,
               zorder=5, label=r"$\sigma_1$ (tracción)")
    ax.scatter([sigma_2], [0], s=58, color=_COLOR_PRINCIPAL_COMPRESS,
               zorder=5, label=r"$\sigma_2$ (compresión)")
    ax.axvline(cx, color="#cccccc", linewidth=0.8, linestyle=":")
    ax.axhline(0, color="#888888", linewidth=0.8)

    ax.set_xlabel(r"$\sigma$")
    ax.set_ylabel(r"$\tau$")
    title = "Círculo de Mohr"
    if label:
        title += f"  ({label})"
    ax.set_title(title, fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Diagramas didacticos (Cap 0, Cap 7)
# ---------------------------------------------------------------------------

def render_fem_pipeline() -> Figure:
    """Hoja de ruta del Metodo de Elementos Finitos (Cap 0).

    Diagrama horizontal con 7 nodos del pipeline conectados por flechas,
    coloreados segun la fase del proyecto (pre/proc/post). Reemplaza al
    texto prosa-only de la introduccion: el alumno ve la arquitectura
    del metodo de un vistazo antes de leer cada capitulo.
    """
    fig = Figure(figsize=(9.5, 2.4), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 3)
    ax.set_aspect("equal")
    ax.axis("off")

    # Pipeline en 8 etapas alineadas con la estructura de capitulos:
    #   Cap 1+2 (Pre) -> Cap 3 (Pre) -> Cap 4 (Proc) -> Cap 5 (Proc) ->
    #   Cap 6 (Proc) -> Cap 7 (Proc) -> Cap 8 (Post).
    # BCs aparecen ENTRE ensamblaje y resolucion porque conceptualmente
    # operan sobre K/F ya ensamblados para reducir el sistema.
    steps = [
        ("Modelo\n(materiales,\nnodos, cargas)", PHASE_PRE_COLOR),
        ("Calidad de\nmalla\n(det J, AR)", PHASE_PRE_COLOR),
        ("Elemento\nN→J→B→D", PHASE_PROC_COLOR),
        ("kₑ por\ncuadratura\nde Gauss", PHASE_PROC_COLOR),
        ("Ensamblaje\nK, F", PHASE_PROC_COLOR),
        ("Aplicar\nBCs", PHASE_PROC_COLOR),
        ("Resolver\nK·u = F", PHASE_PROC_COLOR),
        ("σ, σ₁, σ₂,\nvon Mises", PHASE_POST_COLOR),
    ]
    n = len(steps)
    box_w = 1.45
    box_h = 1.4
    total_w = n * box_w
    gap = (14 - total_w) / (n + 1)
    for i, (text, color) in enumerate(steps):
        x0 = gap + i * (box_w + gap)
        y0 = 0.85
        rect = _FancyBboxPatch(
            (x0, y0), box_w, box_h,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            facecolor=color, edgecolor="black",
            linewidth=0.8, alpha=0.88,
        )
        ax.add_patch(rect)
        ax.text(x0 + box_w / 2, y0 + box_h / 2, text,
                ha="center", va="center", fontsize=7.5,
                color="white", fontweight="bold")
        if i < n - 1:
            arrow = _FancyArrowPatch(
                (x0 + box_w, y0 + box_h / 2),
                (x0 + box_w + gap, y0 + box_h / 2),
                arrowstyle="->", color="black", lw=1.3,
                mutation_scale=12,
            )
            ax.add_patch(arrow)

    # Etiquetas de fase debajo, agrupando los pasos correspondientes:
    #   Pasos 0-1 (Pre), 2-6 (Proc), 7 (Post)
    def _phase_center(i_start: int, i_end: int) -> float:
        x_start = gap + i_start * (box_w + gap)
        x_end = gap + i_end * (box_w + gap) + box_w
        return (x_start + x_end) / 2.0

    ax.text(_phase_center(0, 1), 0.4, "PRE-PROCESO",
            ha="center", fontsize=8, color=PHASE_PRE_COLOR,
            fontweight="bold")
    ax.text(_phase_center(2, 6), 0.4, "PROCESO",
            ha="center", fontsize=8, color=PHASE_PROC_COLOR,
            fontweight="bold")
    ax.text(_phase_center(7, 7), 0.4, "POST",
            ha="center", fontsize=8, color=PHASE_POST_COLOR,
            fontweight="bold")
    return fig


def render_lm_mapping(project, solution, elem_id: int) -> Figure:
    r"""Diagrama del mapeo LM (location matrix): k_e -> K para un elemento.

    Pedagogicamente clave en Cap.\ 5: hace visible como las contribuciones
    elementales se SUMAN en bloques especificos de la matriz global. El
    layout es 2 paneles lado-a-lado: izquierda muestra k_e (sparsity);
    derecha muestra K con los bloques que recibe contribucion del elemento
    resaltados con borde naranja.
    """
    elem_data = solution.get("element_data", {}).get(elem_id)
    if elem_data is None:
        # Figura placeholder
        fig = Figure(figsize=(7.5, 4.0), dpi=_FIG_DPI,
                     facecolor=_FIG_FACECOLOR)
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "Sin datos del elemento",
                ha="center", va="center", transform=ax.transAxes,
                color="gray")
        ax.axis("off")
        return fig

    ke = np.asarray(elem_data["ke"])
    dof_indices = list(elem_data["dof_indices"])
    K = np.asarray(solution["K"])
    n_e = ke.shape[0]
    n_g = K.shape[0]

    fig = Figure(figsize=(8.5, 4.2), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)

    # Panel izquierdo: k_e con grid y etiquetas locales 1..n_e
    mask_ke = (np.abs(ke) > 1e-12).astype(float)
    ax1.imshow(mask_ke, cmap="Greys", vmin=0, vmax=1, aspect="equal")
    ax1.set_title(rf"$\mathbf{{k}}_e$ del elemento $E_{{{elem_id}}}$",
                  fontsize=10)
    ax1.set_xlabel("GDL local")
    ax1.set_ylabel("GDL local")
    ax1.set_xticks(range(n_e))
    ax1.set_yticks(range(n_e))
    ax1.set_xticklabels([str(i + 1) for i in range(n_e)], fontsize=7)
    ax1.set_yticklabels([str(i + 1) for i in range(n_e)], fontsize=7)
    # Marco naranja alrededor de toda la k_e (origen de las contribuciones)
    ax1.add_patch(_FancyBboxPatch(
        (-0.5, -0.5), n_e, n_e,
        boxstyle="round,pad=0.0,rounding_size=0.0",
        facecolor="none", edgecolor=PHASE_PROC_COLOR,
        linewidth=2.5,
    ))

    # Panel derecho: K global (sparsity) con bloques destino resaltados
    mask_K = (np.abs(K) > 1e-12).astype(float)
    ax2.imshow(mask_K, cmap="Greys", vmin=0, vmax=1, aspect="equal")
    ax2.set_title(rf"$\mathbf{{K}}$ global "
                  rf"($\mathbf{{LM}}_e = {dof_indices}$)",
                  fontsize=10)
    ax2.set_xlabel("GDL global")
    ax2.set_ylabel("GDL global")
    # Resaltar los pares (i, j) ∈ LM × LM con cuadrados naranjas individuales
    for i in dof_indices:
        for j in dof_indices:
            ax2.add_patch(_FancyBboxPatch(
                (j - 0.5, i - 0.5), 1, 1,
                boxstyle="round,pad=0.0,rounding_size=0.0",
                facecolor=PHASE_PROC_COLOR, edgecolor="none",
                alpha=0.35,
            ))
    # Etiquetas tenues de GDL en los ejes (cada 2 si hay muchos)
    step = max(1, n_g // 12)
    ticks = list(range(0, n_g, step))
    ax2.set_xticks(ticks)
    ax2.set_yticks(ticks)
    ax2.set_xticklabels([str(t) for t in ticks], fontsize=7)
    ax2.set_yticklabels([str(t) for t in ticks], fontsize=7)

    # Flecha conceptual entre paneles
    fig.text(0.495, 0.5, r"$\xrightarrow{\mathbf{LM}_e}$",
             ha="center", va="center", fontsize=14,
             color=PHASE_PROC_COLOR)

    fig.tight_layout()
    return fig


def render_extrapolation_diagram() -> Figure:
    """Esquema didactico Q4 de extrapolacion Gauss -> nodos.

    Muestra un cuadrilatero con sus 4 nodos en los vertices y los 4
    puntos de Gauss interiores en (+-1/sqrt(3)). Las flechas indican
    que los valores `mas precisos' viven en los PG y se proyectan
    hacia afuera con el factor sqrt(3). Pedagogicamente: justifica la
    extrapolacion antes de mostrar la matriz numerica.
    """
    fig = Figure(figsize=(6.5, 5.5), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal")
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)

    # Cuadrilatero macro (cuadrado natural [-1, 1]^2)
    sq = _Polygon(
        [(-1, -1), (1, -1), (1, 1), (-1, 1)],
        closed=True, facecolor=_COLOR_ELEMENT_FACE,
        edgecolor=_COLOR_ELEMENT_EDGE, linewidth=1.4, alpha=0.85,
    )
    ax.add_patch(sq)

    # Nodos en las esquinas
    nodes = [(-1, -1, "N1"), (1, -1, "N2"), (1, 1, "N3"), (-1, 1, "N4")]
    for x, y, label in nodes:
        ax.scatter([x], [y], s=120, c=_COLOR_NODE_CORNER, zorder=4,
                   edgecolors="black", linewidths=0.8)
        ax.annotate(label, (x, y), xytext=(8 * np.sign(x or 1),
                                            8 * np.sign(y or 1)),
                    textcoords="offset points",
                    fontsize=10, color=_COLOR_ELEMENT_LABEL,
                    fontweight="bold")

    # Puntos de Gauss en (+-1/sqrt(3))
    g = 1.0 / np.sqrt(3.0)
    pgs = [(-g, -g, "PG1"), (g, -g, "PG2"), (g, g, "PG3"), (-g, g, "PG4")]
    for x, y, label in pgs:
        ax.scatter([x], [y], s=80, c=PHASE_PROC_COLOR, marker="s",
                   zorder=4, edgecolors="black", linewidths=0.6)
        ax.annotate(label, (x, y), xytext=(6, -10),
                    textcoords="offset points",
                    fontsize=8, color=PHASE_PROC_COLOR,
                    fontweight="bold")

    # Flechas de extrapolacion: cada PG -> nodo "exterior" mas cercano
    for (xpg, ypg, _), (xn, yn, _) in zip(pgs, nodes):
        ax.annotate("", xy=(xn, yn), xytext=(xpg, ypg),
                    arrowprops=dict(arrowstyle="->",
                                    color=PHASE_POST_COLOR,
                                    lw=1.3, alpha=0.7,
                                    connectionstyle="arc3,rad=0.0"))

    ax.text(0, -1.45,
            r"$\sigma^{\,\text{nodo}} = \mathbf{E}\,\sigma^{\,\text{Gauss}}$  "
            r"(factor de extrapolación $\sqrt{3}$)",
            ha="center", fontsize=10, color=_COLOR_ELEMENT_LABEL)
    ax.set_title("Extrapolación: Gauss → nodos (Q4)", fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    return fig


def render_averaging_diagram() -> Figure:
    """Esquema didactico de promediado nodal entre elementos adyacentes.

    Un nodo compartido por 4 elementos recibe 4 valores extrapolados,
    uno por elemento. El diagrama muestra ese nodo central + las 4
    contribuciones como barras de altura proporcional + el valor
    promediado como linea horizontal. Hace tangible la idea de que el
    salto entre contribuciones es indicador de error de malla.
    """
    fig = Figure(figsize=(8.5, 4.0), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax1 = fig.add_subplot(1, 2, 1)
    ax2 = fig.add_subplot(1, 2, 2)

    # Panel izquierdo: 4 elementos compartiendo un nodo central
    ax1.set_aspect("equal")
    ax1.set_xlim(-2.2, 2.2)
    ax1.set_ylim(-2.2, 2.2)
    ax1.axis("off")
    # 4 cuadrilateros alrededor del origen
    quads = [
        [(0, 0), (2, 0), (2, 2), (0, 2)],
        [(0, 0), (0, 2), (-2, 2), (-2, 0)],
        [(0, 0), (-2, 0), (-2, -2), (0, -2)],
        [(0, 0), (0, -2), (2, -2), (2, 0)],
    ]
    colors_q = [PHASE_PRE_COLOR, PHASE_PROC_COLOR,
                PHASE_POST_COLOR, "#9c27b0"]
    labels_q = ["E1", "E2", "E3", "E4"]
    for q, c, lbl in zip(quads, colors_q, labels_q):
        poly = _Polygon(q, closed=True, facecolor=c, alpha=0.25,
                        edgecolor=c, linewidth=1.2)
        ax1.add_patch(poly)
        cx = np.mean([p[0] for p in q])
        cy = np.mean([p[1] for p in q])
        ax1.text(cx, cy, lbl, ha="center", va="center", fontsize=11,
                 color=c, fontweight="bold")
    # Nodo compartido central
    ax1.scatter([0], [0], s=200, c=_COLOR_NODE_CORNER, zorder=5,
                edgecolors="black", linewidths=1.0)
    ax1.annotate("Nodo compartido\n(4 contribuciones)",
                 (0, 0), xytext=(15, 15),
                 textcoords="offset points", fontsize=9,
                 color=_COLOR_ELEMENT_LABEL,
                 arrowprops=dict(arrowstyle="->", color="black", lw=0.8))
    ax1.set_title("Nodo compartido por k elementos", fontsize=10)

    # Panel derecho: barras de las k contribuciones + promedio
    np.random.seed(42)
    vals = [120.0, 135.0, 108.0, 142.0]
    avg = np.mean(vals)
    ax2.bar(labels_q, vals, color=colors_q, alpha=0.7, edgecolor="black",
            linewidth=0.6)
    ax2.axhline(avg, color=PHASE_PROC_COLOR, linestyle="--", linewidth=1.6,
                label=f"Promedio = {avg:.1f}")
    ax2.set_ylabel(r"$\sigma_{VM}$ extrapolado")
    ax2.set_xlabel("Elemento contribuyente")
    ax2.set_title("Valores extrapolados y promedio nodal", fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    return fig


def render_principal_crosses(project, nodal_stresses) -> Figure:
    """Cruces principales sigma_1/sigma_2 superpuestas sobre la malla.

    Una cruz por centroide de elemento (no por nodo: satura). Brazo
    sigma_1 en azul (traccion), sigma_2 en rojo (compresion). Longitud
    proporcional a |sigma_i| normalizado. Consolida la pedagogia del
    ex-modulo M8 dentro de la memoria.
    """
    fig = Figure(figsize=(7.0, 5.5), dpi=_FIG_DPI, facecolor=_FIG_FACECOLOR)
    ax = fig.add_subplot(111)
    ax.set_aspect("equal", adjustable="datalim")

    if not project.elements or not nodal_stresses:
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center",
                transform=ax.transAxes, color="gray")
        ax.axis("off")
        return fig

    # Malla de fondo en gris claro
    for elem in project.elements.values():
        nids = [n for n in list(elem.node_ids)[:4] if n in project.nodes]
        if len(nids) < 3:
            continue
        xs = [project.nodes[n].x for n in nids] + [project.nodes[nids[0]].x]
        ys = [project.nodes[n].y for n in nids] + [project.nodes[nids[0]].y]
        ax.plot(xs, ys, color="#bbbbbb", linewidth=0.8, alpha=0.7)

    # Calcular centroide + cruces principales en cada elemento (promedio
    # nodal de sigma componentes -> recomputo principales para preservar
    # direccion theta_p, en vez de promediar sigma_1/sigma_2 directamente).
    centroids = []
    crosses = []
    max_mag = 1e-12
    for elem in project.elements.values():
        nids = [n for n in list(elem.node_ids)[:4] if n in project.nodes]
        if len(nids) < 3:
            continue
        sx_nodes, sy_nodes, txy_nodes = [], [], []
        for nid in nids:
            s = nodal_stresses.get(nid, {})
            sx_nodes.append(s.get("sigma_x", 0.0))
            sy_nodes.append(s.get("sigma_y", 0.0))
            txy_nodes.append(s.get("tau_xy", 0.0))
        sx = float(np.mean(sx_nodes))
        sy = float(np.mean(sy_nodes))
        txy = float(np.mean(txy_nodes))
        cx = float(np.mean([project.nodes[n].x for n in nids]))
        cy = float(np.mean([project.nodes[n].y for n in nids]))
        avg = 0.5 * (sx + sy)
        R = float(np.sqrt(((sx - sy) / 2.0) ** 2 + txy ** 2))
        sigma_1 = avg + R
        sigma_2 = avg - R
        theta_p = 0.5 * np.arctan2(2.0 * txy, (sx - sy) + 1e-30)
        centroids.append((cx, cy))
        crosses.append((sigma_1, sigma_2, theta_p))
        max_mag = max(max_mag, abs(sigma_1), abs(sigma_2))

    # Escala visual: brazo maximo = 30% de la diagonal del bbox
    xs_all = [n.x for n in project.nodes.values()]
    ys_all = [n.y for n in project.nodes.values()]
    extent = max(max(xs_all) - min(xs_all),
                 max(ys_all) - min(ys_all), 1e-9)
    L_max = 0.18 * extent

    for (cx, cy), (s1, s2, th) in zip(centroids, crosses):
        # Brazo sigma_1 en direccion theta_p
        L1 = L_max * (abs(s1) / max_mag)
        dx1 = L1 * np.cos(th)
        dy1 = L1 * np.sin(th)
        col1 = _COLOR_PRINCIPAL_TENSILE if s1 >= 0 \
            else _COLOR_PRINCIPAL_COMPRESS
        ax.plot([cx - dx1, cx + dx1], [cy - dy1, cy + dy1],
                color=col1, linewidth=2.0, solid_capstyle="round")
        # Brazo sigma_2 perpendicular
        L2 = L_max * (abs(s2) / max_mag)
        dx2 = L2 * np.cos(th + np.pi / 2)
        dy2 = L2 * np.sin(th + np.pi / 2)
        col2 = _COLOR_PRINCIPAL_TENSILE if s2 >= 0 \
            else _COLOR_PRINCIPAL_COMPRESS
        ax.plot([cx - dx2, cx + dx2], [cy - dy2, cy + dy2],
                color=col2, linewidth=2.0, solid_capstyle="round")

    # Leyenda manual (sin afectar layout)
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color=_COLOR_PRINCIPAL_TENSILE, lw=2.0,
               label=r"$\sigma > 0$ (tracción)"),
        Line2D([0], [0], color=_COLOR_PRINCIPAL_COMPRESS, lw=2.0,
               label=r"$\sigma < 0$ (compresión)"),
    ]
    ax.legend(handles=handles, loc="best", fontsize=9)
    ax.set_title("Direcciones principales por elemento (cruces σ₁ ⊥ σ₂)",
                 fontsize=11)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, linestyle=":", alpha=0.3)
    fig.tight_layout()
    return fig
