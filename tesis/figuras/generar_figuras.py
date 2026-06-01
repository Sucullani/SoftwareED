# -*- coding: utf-8 -*-
"""
generar_figuras.py — Diagramas CONCEPTUALES de la tesis de EduFEM.

División de responsabilidades de las figuras de la tesis:

  1. Capturas de la GUI real (lienzo, módulo educativo, post-proceso,
     contornos sobre la malla) → tesis/figuras/gui_capture.py
     (lanza la aplicación y captura el lienzo oscuro tal cual lo ve el
     usuario, con PrintWindow). Son las figuras que CORRESPONDEN a la GUI.

  2. Gráficos de V&V (convergencia MMS, convergencia de Cook, perfiles de
     tensión, campos del MMS) → se generan con los scripts del proyecto
     `python -m tests.vv_mms`, `tests.vv_timoshenko`, `tests.vv_cook`
     (matplotlib, fondo blanco) y se copian desde docs/vyv/figuras/.

  3. Diagramas CONCEPTUALES que no existen como pantalla del software
     (elementos isoparamétricos Q4/Q9; arquitectura por capas) → ESTE script
     (matplotlib).

Reproducible (desde la raíz del repositorio):

    .venv\\Scripts\\python.exe tesis\\figuras\\generar_figuras.py

Genera: fig_isoparametricos.png, fig_arquitectura.png en tesis/figuras/.
NO toca las capturas de GUI ni los gráficos de V&V.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from config.settings import (
    PHASE_PRE_COLOR, PHASE_PROC_COLOR, PHASE_POST_COLOR,
    CANVAS_NODE_COLOR, CANVAS_NODE_MID_COLOR, CANVAS_NODE_CENTER_COLOR,
)

OUT = _HERE
DPI = 150

C_PRE = PHASE_PRE_COLOR     # azul   #0d6efd
C_PROC = PHASE_PROC_COLOR   # naranja #fd7e14
C_POST = PHASE_POST_COLOR   # verde  #198754
C_TXT = "#212529"
C_MUTED = "#6c757d"


def _save_fig(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=DPI, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print(f"  [OK] {name}")


# ════════════════════════════════════════════════════════════════════════════
# fig_isoparametricos — elementos Q4 y Q9 + mapeo + función de forma
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
    axc.set_title(r"(c) Mapeo isoparamétrico · $N_1$", fontsize=11, color=C_TXT)
    phys = np.array([(0.2, 0.3), (3.1, 0.0), (3.6, 2.6), (0.6, 2.2)])
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
# fig_arquitectura — capas alrededor de ProjectModel
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
                color=tc, fontweight=("bold" if bold else "normal"), zorder=3)

    box(5, 3.5, 2.7, 1.15, "ProjectModel\n(estado del análisis)",
        "#212529", C_TXT, fs=12)

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
        arr = FancyArrowPatch((cx, cy), (5, 3.5), arrowstyle="-|>",
                              mutation_scale=14, color=C_MUTED, lw=1.4,
                              zorder=1, shrinkA=42, shrinkB=46)
        ax.add_patch(arr)

    ax.text(5, 6.7, "Arquitectura por capas centrada en el modelo de proyecto",
            ha="center", fontsize=12.5, color=C_TXT, fontweight="bold")
    ax.text(5, 0.35,
            "Cada capa depende solo de las inferiores; el motor (fem/) no "
            "importa la interfaz.",
            ha="center", fontsize=9, color=C_MUTED, style="italic")
    _save_fig(fig, "fig_arquitectura.png")


def main():
    print("Generando diagramas conceptuales de la tesis en:", OUT)
    print("-" * 60)
    for name, fn in [("isoparametricos", fig_isoparametricos),
                     ("arquitectura", fig_arquitectura)]:
        print(f"[{name}]")
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            import traceback
            print(f"  [ERROR] {name}: {e}")
            traceback.print_exc()
    print("-" * 60)
    print("Listo. (GUI: gui_capture.py · V&V: tests/vv_*.py)")


if __name__ == "__main__":
    main()
