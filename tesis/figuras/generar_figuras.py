# -*- coding: utf-8 -*-
"""
generar_figuras.py — Genera las figuras de la tesis de EduFEM.

Filosofía: las figuras que son *salida del software* (contornos de tensión,
deformada, diagrama de malla) se producen con el MISMO renderizador que usa
EduFEM para la Memoria de Cálculo ([file_io/figure_export.py], Pillow puro,
paleta jet, estilo del MeshCanvas). Los gráficos de *datos* (convergencia) se
trazan con matplotlib a partir de los CSV reales de V&V (docs/vyv/datos/),
producto de resolver los benchmarks con el motor MEF. Los *diagramas
conceptuales* (elementos isoparamétricos, arquitectura por capas) se dibujan
con matplotlib/Pillow.

Reproducible: desde la raíz del repositorio,

    .venv\\Scripts\\python.exe tesis\\figuras\\generar_figuras.py

Vuelca los .png en tesis/figuras/. Requiere el stack del proyecto
(numpy, scipy, Pillow, matplotlib) ya presente en el .venv.

Las figuras de la interfaz interactiva en vivo (modo dibujo del lienzo y capa
educativa flotante) se reconstruyen aquí de forma representativa con el propio
renderizador del software; para una captura de pantalla de la sesión real,
abrir EduFEM y reproducir el estado descrito en el pie de cada figura.
"""

from __future__ import annotations

import csv
import math
import os
import sys

# Raíz del repo en el path (este archivo vive en tesis/figuras/).
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle
from PIL import Image, ImageDraw

from config.settings import (
    ANALYSIS_PLANE_STRESS, ELEMENT_Q4, ELEMENT_Q9,
    PHASE_PRE_COLOR, PHASE_PROC_COLOR, PHASE_POST_COLOR,
    CANVAS_NODE_COLOR, CANVAS_NODE_MID_COLOR, CANVAS_NODE_CENTER_COLOR,
    CANVAS_SELECTED_COLOR, GAUSS_ACTIVE_COLOR,
)
from models.example_library import (
    load_example_project, load_example_timoshenko,
)
from models.material import Material
from models.mesh_utils import generate_structured_quad_mesh
from fem.solver import solve_system
from fem.stress import compute_all_stresses
import file_io.figure_export as fx


OUT = _HERE
DPI = 150

# Paleta coherente con la identidad por fase de EduFEM.
C_PRE = PHASE_PRE_COLOR     # azul   #0d6efd
C_PROC = PHASE_PROC_COLOR   # naranja #fd7e14
C_POST = PHASE_POST_COLOR   # verde  #198754
C_TXT = "#212529"
C_MUTED = "#6c757d"


def _save_pil(img, name):
    path = os.path.join(OUT, name)
    img.save(path)
    print(f"  [OK] {name}  ({img.size[0]}x{img.size[1]})")


def _save_fig(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  [OK] {name}")


def _read_csv(rel):
    path = os.path.join(_ROOT, "docs", "vyv", "datos", rel)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ════════════════════════════════════════════════════════════════════════════
# 1. fig_isoparametricos — elementos Q4 y Q9 + mapeo + función de forma
# ════════════════════════════════════════════════════════════════════════════

def _N_q4(xi, eta):
    return np.array([
        0.25 * (1 - xi) * (1 - eta),
        0.25 * (1 + xi) * (1 - eta),
        0.25 * (1 + xi) * (1 + eta),
        0.25 * (1 - xi) * (1 + eta),
    ])


def fig_isoparametricos():
    fig = plt.figure(figsize=(11.2, 4.2))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.15], wspace=0.32)

    # --- (a) Q4 en el cuadrado natural ---
    axa = fig.add_subplot(gs[0, 0])
    axa.set_title("(a) Q4 — cuadrado natural", fontsize=11, color=C_TXT)
    axa.add_patch(plt.Rectangle((-1, -1), 2, 2, fill=False,
                                edgecolor=C_PROC, lw=2))
    q4 = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for i, (x, y) in enumerate(q4, 1):
        axa.plot(x, y, "o", ms=11, color=CANVAS_NODE_COLOR,
                 markeredgecolor="k", zorder=3)
        axa.annotate(str(i), (x, y), color="k", fontsize=9, ha="center",
                     va="center", zorder=4, fontweight="bold")
    axa.annotate("", xy=(1.45, 0), xytext=(-1.45, 0),
                 arrowprops=dict(arrowstyle="->", color=C_MUTED))
    axa.annotate("", xy=(0, 1.45), xytext=(0, -1.45),
                 arrowprops=dict(arrowstyle="->", color=C_MUTED))
    axa.text(1.5, -0.18, r"$\xi$", fontsize=12, color=C_MUTED)
    axa.text(-0.22, 1.5, r"$\eta$", fontsize=12, color=C_MUTED)
    axa.text(0, -1.75, "4 nodos · 8 GDL · bilineal", ha="center",
             fontsize=9, color=C_TXT)
    axa.set_xlim(-1.9, 1.9); axa.set_ylim(-2.0, 1.9)
    axa.set_aspect("equal"); axa.axis("off")

    # --- (b) Q9 en el cuadrado natural ---
    axb = fig.add_subplot(gs[0, 1])
    axb.set_title("(b) Q9 — cuadrado natural", fontsize=11, color=C_TXT)
    axb.add_patch(plt.Rectangle((-1, -1), 2, 2, fill=False,
                                edgecolor=C_PROC, lw=2))
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    mids = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    center = [(0, 0)]
    order = corners + mids + center
    cols = ([CANVAS_NODE_COLOR] * 4 + [CANVAS_NODE_MID_COLOR] * 4
            + [CANVAS_NODE_CENTER_COLOR])
    for i, ((x, y), c) in enumerate(zip(order, cols), 1):
        r = 11 if i <= 4 else 9
        axb.plot(x, y, "o", ms=r, color=c, markeredgecolor="k", zorder=3)
        axb.annotate(str(i), (x, y), color="k", fontsize=8, ha="center",
                     va="center", zorder=4, fontweight="bold")
    axb.text(0, -1.75, "9 nodos · 18 GDL · bicuadrático", ha="center",
             fontsize=9, color=C_TXT)
    axb.set_xlim(-1.9, 1.9); axb.set_ylim(-2.0, 1.9)
    axb.set_aspect("equal"); axb.axis("off")

    # --- (c) Mapeo a la geometría física + curvas de nivel de N1 (Q4) ---
    axc = fig.add_subplot(gs[0, 2])
    axc.set_title(r"(c) Mapeo isoparamétrico · $N_1$",
                  fontsize=11, color=C_TXT)
    # Cuadrilátero físico distorsionado.
    phys = np.array([(0.2, 0.3), (3.1, 0.0), (3.6, 2.6), (0.6, 2.2)])
    # Grilla del campo N1 mapeada al físico.
    n = 40
    xi = np.linspace(-1, 1, n)
    eta = np.linspace(-1, 1, n)
    XI, ETA = np.meshgrid(xi, eta)
    PX = np.zeros_like(XI); PY = np.zeros_like(XI); N1 = np.zeros_like(XI)
    for a in range(n):
        for b in range(n):
            Nv = _N_q4(XI[a, b], ETA[a, b])
            PX[a, b] = Nv @ phys[:, 0]
            PY[a, b] = Nv @ phys[:, 1]
            N1[a, b] = Nv[0]
    cf = axc.contourf(PX, PY, N1, levels=12, cmap="jet", alpha=0.92)
    poly = np.vstack([phys, phys[0]])
    axc.plot(poly[:, 0], poly[:, 1], "-", color=C_TXT, lw=1.6)
    for i, (x, y) in enumerate(phys, 1):
        axc.plot(x, y, "o", ms=9, color=CANVAS_NODE_COLOR,
                 markeredgecolor="k", zorder=3)
        axc.annotate(str(i), (x, y), color="k", fontsize=8, ha="center",
                     va="center", zorder=4, fontweight="bold")
    axc.annotate(r"$(x,y)=\sum N_i(\xi,\eta)\,(x_i,y_i)$",
                 xy=(0.5, -0.02), xycoords="axes fraction",
                 ha="center", fontsize=9, color=C_TXT)
    cb = fig.colorbar(cf, ax=axc, fraction=0.046, pad=0.04)
    cb.set_label(r"$N_1$", fontsize=10)
    axc.set_aspect("equal"); axc.axis("off")

    _save_fig(fig, "fig_isoparametricos.png")


# ════════════════════════════════════════════════════════════════════════════
# 2. fig_arquitectura — capas alrededor de ProjectModel
# ════════════════════════════════════════════════════════════════════════════

def fig_arquitectura():
    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7)
    ax.axis("off")

    def box(cx, cy, w, h, text, fc, ec, fs=11, tc="white", bold=True):
        b = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                           boxstyle="round,pad=0.02,rounding_size=0.12",
                           linewidth=2, edgecolor=ec, facecolor=fc, zorder=2)
        ax.add_patch(b)
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
                color=tc, fontweight=("bold" if bold else "normal"),
                zorder=3)

    # Núcleo: ProjectModel.
    box(5, 3.5, 2.7, 1.15, "ProjectModel\n(estado del análisis)",
        "#212529", C_TXT, fs=12)

    # Capas alrededor.
    layers = [
        (2.0, 5.6, "models/\nentidades · validación · undo", C_PRE),
        (8.0, 5.6, "fem/\nmotor MEF (NumPy/SciPy)", C_PROC),
        (1.7, 3.5, "config/\nunidades · colores", C_MUTED),
        (8.3, 3.5, "file_io/\nproyecto · CSV · DXF · PDF", "#6f42c1"),
        (2.0, 1.4, "gui/\npre · lienzo · post", C_POST),
        (8.0, 1.4, "education/\nmódulos M0–M7", "#d63384"),
    ]
    for cx, cy, txt, col in layers:
        box(cx, cy, 2.9, 1.15, txt, col, col, fs=9.5)
        arr = FancyArrowPatch((cx, cy), (5, 3.5),
                              arrowstyle="-|>", mutation_scale=14,
                              color=C_MUTED, lw=1.4, zorder=1,
                              shrinkA=42, shrinkB=46,
                              connectionstyle="arc3,rad=0.0")
        ax.add_patch(arr)

    ax.text(5, 6.7, "Arquitectura por capas centrada en el modelo de proyecto",
            ha="center", fontsize=12.5, color=C_TXT, fontweight="bold")
    ax.text(5, 0.35,
            "Cada capa depende solo de las inferiores; el motor (fem/) no "
            "importa la interfaz.",
            ha="center", fontsize=9, color=C_MUTED, style="italic")
    _save_fig(fig, "fig_arquitectura.png")


# ════════════════════════════════════════════════════════════════════════════
# 3. fig_lienzo_lod — render del modelo (software) + overlay modo dibujo
# ════════════════════════════════════════════════════════════════════════════

def fig_lienzo_lod():
    W, H = 960, 700
    project = load_example_project()
    img = fx.render_mesh_diagram(project, width=W, height=H)
    if img is None:
        print("  [SKIP] render_mesh_diagram devolvió None")
        return
    draw = ImageDraw.Draw(img)
    f_small = fx._font(13)
    f_lbl = fx._font(14)

    # Reconstruir la vista para situar el overlay de "modo dibujo" en coords
    # de mundo coherentes con el render (mismos paddings que render_mesh_diagram).
    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    view = fx._View(xs, ys, W, H, pad_left=40, pad_right=40,
                    pad_top=48, pad_bottom=40)

    sel = fx._hex_to_rgb(CANVAS_SELECTED_COLOR)
    # Elemento "en dibujo" en la zona vacía inferior derecha (debajo de la
    # arista 3-6 del modelo). v1 se ancla (snap) al nodo 3 existente.
    n3 = project.nodes[3]
    placed_world = [(n3.x, n3.y), (10.5, 0.4), (10.8, 2.6)]  # v1,v2,v3 puestos
    cursor_world = (9.5, 1.0)                                # v4 = cursor
    spx = [view.w2s(x, y) for (x, y) in placed_world]
    cur = view.w2s(*cursor_world)

    def _dashed(p, q, col, seg=8):
        x0, y0 = p; x1, y1 = q
        d = math.hypot(x1 - x0, y1 - y0)
        if d < 1:
            return
        steps = max(int(d // seg), 1)
        for k in range(0, steps, 2):
            t0 = k * seg / d; t1 = min((k + 1) * seg / d, 1.0)
            draw.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                       (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)],
                      fill=col, width=2)

    # Anillo de snap amarillo sobre el nodo 3 (vértice anclado).
    sx0, sy0 = spx[0]
    draw.ellipse([sx0 - 12, sy0 - 12, sx0 + 12, sy0 + 12], outline=sel, width=3)

    # Polígono parcial punteado: v1→v2→v3→cursor + cierre tentativo.
    for a in range(len(spx) - 1):
        _dashed(spx[a], spx[a + 1], sel)
    _dashed(spx[-1], cur, sel)
    _dashed(cur, spx[0], (150, 150, 160))           # cierre tentativo gris

    for i, (sx, sy) in enumerate(spx, 1):
        draw.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=sel,
                     outline=(0, 0, 0))
        draw.text((sx, sy), str(i), fill=(0, 0, 0), anchor="mm", font=f_small)
    # Cruz de cursor (4º vértice tentativo).
    cx, cy = cur
    draw.line([(cx - 10, cy), (cx + 10, cy)], fill=sel, width=2)
    draw.line([(cx, cy - 10), (cx, cy + 10)], fill=sel, width=2)
    draw.text((cx + 12, cy + 6), "4", fill=sel, font=f_small)
    draw.text((sx0 + 14, sy0 - 26), "snap a nodo", fill=sel, font=f_small)

    # Banda de estado inferior (estilo barra de estado del software).
    band_h = 30
    draw.rectangle([0, H - band_h, W, H], fill=(28, 30, 34))
    draw.text((12, H - band_h + 8),
              "Modo dibujo: vertice 4/4 — click en canvas o sobre nodo (snap)."
              "   Esc cancela.",
              fill=(230, 230, 235), font=f_lbl)
    _save_pil(img, "fig_lienzo_lod.png")


# ════════════════════════════════════════════════════════════════════════════
# 4. fig_modulo_capa — capa educativa (matriz B) + Gauss sobre elemento real
# ════════════════════════════════════════════════════════════════════════════

def fig_modulo_capa():
    project = load_example_project()
    img = fx.render_mesh_diagram(project, width=1000, height=660)
    if img is None:
        print("  [SKIP] render_mesh_diagram devolvió None")
        return
    draw = ImageDraw.Draw(img)
    xs = [n.x for n in project.nodes.values()]
    ys = [n.y for n in project.nodes.values()]
    view = fx._View(xs, ys, 1000, 660, pad_left=40, pad_right=40,
                    pad_top=48, pad_bottom=40)

    # Elemento "seleccionado" (E1: nodos 1,2,5,4) — resaltado + Gauss glow.
    elem = project.elements[1]
    corners = [project.nodes[nid] for nid in elem.node_ids[:4]]
    cpx = [view.w2s(n.x, n.y) for n in corners]
    draw.polygon(cpx, outline=fx._hex_to_rgb(CANVAS_SELECTED_COLOR))
    # relleno punteado simulado: borde grueso amarillo
    poly = cpx + [cpx[0]]
    draw.line(poly, fill=fx._hex_to_rgb(CANVAS_SELECTED_COLOR), width=3)

    # Puntos de Gauss 2x2 mapeados al elemento (bilineal sobre corners).
    g = 1.0 / math.sqrt(3.0)
    gauss = [(-g, -g), (g, -g), (g, g), (-g, g)]
    nc = np.array([(n.x, n.y) for n in corners])
    glow = fx._hex_to_rgb(GAUSS_ACTIVE_COLOR)
    for (xi, eta) in gauss:
        Nv = _N_q4(xi, eta)
        wx, wy = Nv @ nc[:, 0], Nv @ nc[:, 1]
        sx, sy = view.w2s(wx, wy)
        for rr, al in ((9, glow), (5, (255, 255, 255))):
            draw.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=al)
        draw.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], outline=(0, 0, 0))

    # Fuentes TTF (la fuente bitmap por defecto de PIL no tiene ∂, ξ, η, ⁻¹).
    f_hd = fx._font(15)
    f_tx = fx._font(13)
    f_cell = fx._font(11)
    f_acc = fx._font(13)

    # Panel flotante (derecha) con la fórmula y los valores de B.
    px0, py0, px1, py1 = 632, 64, 984, 372
    draw.rounded_rectangle([px0, py0, px1, py1], radius=10,
                           fill=(248, 249, 251), outline=fx._hex_to_rgb(C_PROC),
                           width=2)
    draw.rectangle([px0, py0, px1, py0 + 32], fill=fx._hex_to_rgb(C_PROC))
    draw.text((px0 + 12, py0 + 8), "M3 · Matriz B  ·  elemento E1",
              fill=(255, 255, 255), font=f_hd)
    draw.text((px0 + 14, py0 + 46),
              "Relación deformación–desplazamiento", fill=(60, 60, 70),
              font=f_tx)
    # Arial (fuente del sistema) carece de ⁻ (superíndice); se usa J^-1 plano.
    draw.text((px0 + 14, py0 + 72),
              "[∂N/∂x ; ∂N/∂y] = J^-1 · [∂N/∂ξ ; ∂N/∂η]",
              fill=(30, 30, 40), font=f_tx)
    # Mini bloque de matriz B (3 x 8) esquemático.
    bx0, by0 = px0 + 16, py0 + 108
    cw, ch = 41, 24
    np.random.seed(7)
    for r in range(3):
        for cidx in range(8):
            v = (np.random.rand() - 0.5) * 0.6
            col = (235, 240, 248) if (r + cidx) % 2 == 0 else (224, 232, 244)
            draw.rectangle([bx0 + cidx * cw, by0 + r * ch,
                            bx0 + (cidx + 1) * cw - 2, by0 + (r + 1) * ch - 2],
                           fill=col)
            draw.text((bx0 + cidx * cw + 4, by0 + r * ch + 6),
                      f"{v:+.2f}", fill=(40, 40, 50), font=f_cell)
    draw.text((px0 + 14, by0 + 3 * ch + 14),
              "Conmutador  [ ƒ Fórmula | 123 Valores ]",
              fill=fx._hex_to_rgb(C_PROC), font=f_acc)
    draw.text((px0 + 14, by0 + 3 * ch + 38),
              "evaluada en el punto de Gauss seleccionado", fill=(90, 90, 100),
              font=f_tx)

    _save_pil(img, "fig_modulo_capa.png")


# ════════════════════════════════════════════════════════════════════════════
# 5. fig_postproceso — contorno von Mises (deformada) + círculo de Mohr
# ════════════════════════════════════════════════════════════════════════════

def fig_postproceso():
    project = load_example_project(P=1000.0)
    sol = solve_system(project)
    _, ns = compute_all_stresses(project, sol)

    contour = fx.render_contour(project, sol, ns, "von_mises",
                                deformed=True, width=720, height=560)
    if contour is None:
        print("  [SKIP] render_contour devolvió None")
        return

    # Punto de consulta: nodo de mayor von Mises.
    nid_probe = max(ns, key=lambda k: ns[k]["von_mises"])
    s = ns[nid_probe]
    sx, sy, txy = s["sigma_x"], s["sigma_y"], s["tau_xy"]
    s1, s2 = s["sigma_1"], s["sigma_2"]
    cc = 0.5 * (sx + sy)
    R = math.hypot(0.5 * (sx - sy), txy)
    th_p = 0.5 * math.degrees(math.atan2(2 * txy, (sx - sy) if abs(sx - sy) > 1e-12 else 1e-12))

    # Círculo de Mohr con matplotlib.
    figm, axm = plt.subplots(figsize=(4.6, 4.6))
    circ = Circle((cc, 0), R, fill=False, color=C_POST, lw=2)
    axm.add_patch(circ)
    axm.axhline(0, color=C_MUTED, lw=0.8)
    axm.plot([s1, s2], [0, 0], "o", color=C_PROC, ms=7)
    axm.annotate(r"$\sigma_1$", (s1, 0), textcoords="offset points",
                 xytext=(2, 8), color=C_PROC)
    axm.annotate(r"$\sigma_2$", (s2, 0), textcoords="offset points",
                 xytext=(2, 8), color=C_PROC)
    axm.plot([sx, sy], [txy, -txy], "-", color=C_PRE, lw=1.4)
    axm.plot([sx, sy], [txy, -txy], "s", color=C_PRE, ms=6)
    axm.annotate(r"$(\sigma_x,\tau_{xy})$", (sx, txy),
                 textcoords="offset points", xytext=(6, 4), color=C_PRE,
                 fontsize=9)
    axm.set_aspect("equal")
    axm.set_xlabel(r"$\sigma$"); axm.set_ylabel(r"$\tau$")
    axm.set_title(rf"Círculo de Mohr  ($\theta_p={th_p:.1f}^\circ$)",
                  fontsize=11)
    axm.grid(True, ls=":", alpha=0.5)
    figm.tight_layout()
    mohr_path = os.path.join(OUT, "_mohr_tmp.png")
    figm.savefig(mohr_path, dpi=DPI, facecolor="white")
    plt.close(figm)

    # Componer contorno (izq) + Mohr (der) en un lienzo blanco.
    mohr = Image.open(mohr_path).convert("RGB")
    h = max(contour.height, mohr.height)
    # escalar Mohr a la altura del contorno.
    new_w = int(mohr.width * h / mohr.height)
    mohr = mohr.resize((new_w, h))
    canvas = Image.new("RGB", (contour.width + new_w + 24, h), (255, 255, 255))
    canvas.paste(contour, (0, (h - contour.height) // 2))
    canvas.paste(mohr, (contour.width + 24, 0))
    _save_pil(canvas, "fig_postproceso.png")
    os.remove(mohr_path)


# ════════════════════════════════════════════════════════════════════════════
# 6. fig_convergencia — MMS L2 y H1 log-log (Q4/Q9) desde CSV reales
# ════════════════════════════════════════════════════════════════════════════

def fig_convergencia():
    q4 = _read_csv("mms_q4.csv")
    q9 = _read_csv("mms_q9.csv")
    h4 = np.array([float(r["h"]) for r in q4])
    h9 = np.array([float(r["h"]) for r in q9])
    L2_4 = np.array([float(r["L2_disp"]) for r in q4])
    L2_9 = np.array([float(r["L2_disp"]) for r in q9])
    H1_4 = np.array([float(r["H1_semi"]) for r in q4])
    H1_9 = np.array([float(r["H1_semi"]) for r in q9])

    fig, (axL, axH) = plt.subplots(1, 2, figsize=(11, 4.4))

    def slope_ref(ax, h, e_last, p, color, lbl):
        c = e_last / h[-1] ** p
        ax.loglog(h, c * h ** p, "--", color=color, alpha=0.4, label=lbl)

    # L2
    axL.loglog(h4, L2_4, "o-", color=C_PRE, label="Q4")
    axL.loglog(h9, L2_9, "s-", color=C_PROC, label="Q9")
    slope_ref(axL, h4, L2_4[-1], 2, C_PRE, r"$\mathcal{O}(h^2)$")
    slope_ref(axL, h9, L2_9[-1], 3, C_PROC, r"$\mathcal{O}(h^3)$")
    axL.set_xlabel(r"$h$ (tamaño característico de malla)")
    axL.set_ylabel(r"$\|u_h-u_M\|_{L^2}$")
    axL.set_title(r"(a) Norma $L^2$", fontsize=11)
    axL.grid(True, which="both", ls=":", alpha=0.5)
    axL.legend(fontsize=9)

    # H1
    axH.loglog(h4, H1_4, "o-", color=C_PRE, label="Q4")
    axH.loglog(h9, H1_9, "s-", color=C_PROC, label="Q9")
    slope_ref(axH, h4, H1_4[-1], 1, C_PRE, r"$\mathcal{O}(h)$")
    slope_ref(axH, h9, H1_9[-1], 2, C_PROC, r"$\mathcal{O}(h^2)$")
    axH.set_xlabel(r"$h$ (tamaño característico de malla)")
    axH.set_ylabel(r"$|u_h-u_M|_{H^1}$")
    axH.set_title(r"(b) Seminorma $H^1$", fontsize=11)
    axH.grid(True, which="both", ls=":", alpha=0.5)
    axH.legend(fontsize=9)

    fig.suptitle("Convergencia bajo refinamiento $h$ medida por MMS",
                 fontsize=12.5, y=1.02)
    _save_fig(fig, "fig_convergencia.png")


# ════════════════════════════════════════════════════════════════════════════
# 7. fig_timoshenko_contorno — render_contour σx deformada (software)
# ════════════════════════════════════════════════════════════════════════════

def fig_timoshenko_contorno():
    # Malla Q9 alineada con la validación (NX x NY). Usamos 28x4 para una
    # figura nítida y rápida; el patrón del campo es idéntico al 56x8.
    project = load_example_timoshenko(element_type=ELEMENT_Q9, nx=28, ny=4)
    sol = solve_system(project)
    _, ns = compute_all_stresses(project, sol)
    img = fx.render_contour(project, sol, ns, "sigma_x",
                            deformed=True, width=1100, height=420)
    if img is None:
        print("  [SKIP] render_contour devolvió None")
        return
    _save_pil(img, "fig_timoshenko_contorno.png")


# ════════════════════════════════════════════════════════════════════════════
# 8. fig_cook_convergencia — uy vs GDL (Q4/Q9) desde CSV real
# ════════════════════════════════════════════════════════════════════════════

def fig_cook_convergencia():
    rows = _read_csv("cook.csv")
    q4 = [r for r in rows if r["element_type"] == "Q4"]
    q9 = [r for r in rows if r["element_type"] == "Q9"]
    g4 = np.array([int(r["ndof"]) for r in q4])
    u4 = np.array([float(r["uy"]) for r in q4])
    g9 = np.array([int(r["ndof"]) for r in q9])
    u9 = np.array([float(r["uy"]) for r in q9])
    ref = float(q4[0]["ref"])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axhline(ref, color=C_MUTED, ls="--", lw=1.3,
               label=rf"referencia $u_y={ref}$")
    ax.semilogx(g4, u4, "o-", color=C_PRE, label="Q4 (bilineal)")
    ax.semilogx(g9, u9, "s-", color=C_PROC, label="Q9 (bicuadrático)")
    ax.set_xlabel("Grados de libertad (GDL)")
    ax.set_ylabel(r"$u_y$ en $(48,52)$")
    ax.set_title("Convergencia de la membrana de Cook")
    ax.grid(True, which="both", ls=":", alpha=0.5)
    ax.legend(fontsize=10)
    # Anotar el bloqueo del Q4 en la malla gruesa.
    ax.annotate("bloqueo por cortante\n(Q4 subestima)",
                xy=(g4[0], u4[0]), xytext=(g4[0] * 1.4, u4[0] + 4),
                fontsize=9, color=C_PRE,
                arrowprops=dict(arrowstyle="->", color=C_PRE))
    _save_fig(fig, "fig_cook_convergencia.png")


# ════════════════════════════════════════════════════════════════════════════

def main():
    print("Generando figuras de la tesis en:", OUT)
    print("-" * 60)
    gens = [
        ("isoparametricos", fig_isoparametricos),
        ("arquitectura", fig_arquitectura),
        ("lienzo_lod", fig_lienzo_lod),
        ("modulo_capa", fig_modulo_capa),
        ("postproceso", fig_postproceso),
        ("convergencia", fig_convergencia),
        ("timoshenko_contorno", fig_timoshenko_contorno),
        ("cook_convergencia", fig_cook_convergencia),
    ]
    for name, fn in gens:
        print(f"[{name}]")
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            import traceback
            print(f"  [ERROR] {name}: {e}")
            traceback.print_exc()
    print("-" * 60)
    print("Listo.")


if __name__ == "__main__":
    main()
