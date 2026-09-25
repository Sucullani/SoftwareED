# -*- coding: utf-8 -*-
"""
generar_figuras_formulacion.py — Figuras de la formulación de la tesis (final3).

Tres figuras que nacieron con la versión final3, a partir de las observaciones
del Ing. Julio Saúl Miranda (tribunal, 2026-09-25):

  fig_relacion_variables.png   §2.1.2. Relación entre las variables: el diagrama
                               de círculos de sus láminas (causa → efecto, con la
                               solución que cierra el ciclo).
  fig_contraste_hipotesis.png  Conclusiones. La hipótesis contrastada: por
                               cláusula, sus indicadores y el veredicto.
  fig_margen_criterios.png     Conclusiones. Qué fracción de su umbral consume
                               cada criterio numérico de la cláusula (b).

Las cifras de las dos últimas se leen de docs/vyv/datos/*.csv, los mismos datos
de las tablas del Cap. 3, y el guion comprueba que, redondeadas como las imprime
la tabla de veredicto (tab:veredicto, 04_resultados.tex), coinciden con la tesis.
Si algo no coincide, termina con error antes de escribir ninguna figura.

Reproducible (desde la raíz del repositorio):

    .venv\\Scripts\\python.exe tesis\\figuras\\generar_figuras_formulacion.py

Escribe en tesis/capitulos_final3/figuras/ (se cambia con --out DIR).
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, _ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

from config.settings import PHASE_PRE_COLOR, PHASE_PROC_COLOR, PHASE_POST_COLOR

DATOS = os.path.join(_ROOT, "docs", "vyv", "datos")
TESIS = os.path.join(_ROOT, "tesis", "capitulos_final3")
OUT_DEFECTO = os.path.join(TESIS, "figuras")
DPI = 150

# Paleta: la de generar_figuras.py. Validada con el validador de la skill dataviz
# (azul, violeta y naranja como identidad: pasa las pruebas de daltonismo; el
# naranja tiene 2,5:1 de contraste, por eso ningún color va sin su rótulo).
C_VI = PHASE_PRE_COLOR        # azul    #0d6efd  variable independiente
C_VD = "#6f42c1"              # violeta           variable dependiente
C_INT = PHASE_PROC_COLOR      # naranja #fd7e14  variable interviniente (EduFEM)
C_OK = PHASE_POST_COLOR       # verde   #198754  estado «se cumple» (siempre con ✓ y texto)
C_MAL = "#b02a37"             # rojo              estado del problema (siempre con texto)
C_TXT = "#212529"
C_MUTED = "#6c757d"
C_GRID = "#dee2e6"


# ─────────────────────────────────────────────────────────────────────────────
# Datos y comprobación contra la tesis
# ─────────────────────────────────────────────────────────────────────────────

def _leer(nombre):
    with open(os.path.join(DATOS, nombre), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _coma(x, nd):
    """Número con coma decimal, como lo escribe la tesis."""
    return f"{x:.{nd}f}".replace(".", ",")


def _tasa(filas, col):
    """Tasa asintótica entre las dos mallas más finas (N = 16 y N = 32), con
    precisión completa: la columna rate_* del CSV viene redondeada a tres
    decimales y en el Q9 daría desviación 0, que no cabe en escala logarítmica."""
    por_n = {int(f["N"]): f for f in filas}
    a, b = por_n[16], por_n[32]
    return (math.log(float(a[col]) / float(b[col]))
            / math.log(float(a["h"]) / float(b["h"])))


def reunir_datos():
    configs = ["", "_dist_tp", "_unif_dp", "_dist_dp"]
    teoricas = {("q4", "L2_disp"): 2.0, ("q9", "L2_disp"): 3.0,
                ("q4", "H1_semi"): 1.0, ("q9", "H1_semi"): 2.0}
    tasas = {}
    for (el, col), p in teoricas.items():
        valores = [_tasa(_leer(f"mms_{el}{c}.csv"), col) for c in configs]
        # La tabla de veredicto imprime «Q4: 2,00; Q9: 3,00» (L2) y «Q4: 1,00;
        # Q9: 2,00» (H1) para las cuatro configuraciones.
        for v in valores:
            assert round(v, 2) == p, f"tasa {el} {col} = {v:.4f}, la tesis dice {p:.2f}"
        peor = max(valores, key=lambda v: abs(v - p))
        tasas[(el, col)] = (peor, p)

    flecha = float(_leer("timoshenko_deflexion.csv")[0]["err_pct"])
    tension = _leer("timoshenko_stress.csv")
    sx_anal = max(float(f["err_anal_pct"]) for f in tension)
    sx_sap = max(float(f["err_sap_pct"]) for f in tension)
    residuo = float(_leer("timoshenko_equilibrio.csv")[0]["residuo_relativo"])
    cook = next(f for f in _leer("cook.csv")
                if f["element_type"] == "Q9" and int(f["N"]) == 8)
    cook_err = abs(float(cook["error_pct"]))
    cook_q4 = next(f for f in _leer("cook.csv")
                   if f["element_type"] == "Q4" and int(f["N"]) == 8)

    # Lo que imprime tab:veredicto (04_resultados.tex).
    assert round(flecha, 2) == 0.26, flecha
    assert round(sx_anal, 2) == 0.04, sx_anal
    assert round(sx_sap, 2) == 0.21, sx_sap
    assert f"{residuo:.1e}" == "1.7e-13", residuo
    assert round(cook_err, 3) == 0.144, cook_err
    assert _coma(float(cook_q4["uy"]), 3) == "22,079", cook_q4["uy"]
    assert _coma(float(cook["uy"]), 3) == "23,925", cook["uy"]

    # Los criterios documentales de la cláusula (a) no salen de un CSV: se
    # comprueba que la tabla de veredicto de la tesis los imprima tal cual.
    with open(os.path.join(TESIS, "04_resultados.tex"), encoding="utf-8") as fh:
        cap3 = fh.read()
    for texto in ("7 de 7", "9 de 9", "3 de 3", "18 de 18"):
        assert texto in cap3, f"«{texto}» no está en 04_resultados.tex"

    return {"tasas": tasas, "flecha": flecha, "sx_anal": sx_anal,
            "sx_sap": sx_sap, "residuo": residuo, "cook_err": cook_err}


def _guardar(fig, carpeta, nombre):
    os.makedirs(carpeta, exist_ok=True)
    fig.savefig(os.path.join(carpeta, nombre), dpi=DPI, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print(f"  [OK] {nombre}")


def _caja(ax, x, y, w, h, color, relleno=0.07, lw=2.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.18",
                                linewidth=lw, edgecolor=color,
                                facecolor=matplotlib.colors.to_rgba(color, relleno),
                                zorder=2))


def _flecha(ax, a, b, color=C_MUTED, rad=0.0, lw=1.6):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=16,
                                 color=color, lw=lw, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))


# ─────────────────────────────────────────────────────────────────────────────
# Figura 2.1 — relación entre las variables
# ─────────────────────────────────────────────────────────────────────────────

def fig_relacion_variables(carpeta):
    fig, ax = plt.subplots(figsize=(10.0, 6.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7.6); ax.axis("off")

    cy = 4.45   # centro de los dos círculos
    for cx, color, rotulo, texto, niveles in [
        (2.4, C_VI, "Variable independiente (causa)",
         "Transparencia\ndel procedimiento\nde cálculo", "caja negra  |  a la vista"),
        (9.6, C_VD, "Variable dependiente (efecto)",
         "Trazabilidad y\nverificabilidad del\nprocedimiento\nde cálculo", "baja  |  alta"),
    ]:
        ax.add_patch(Circle((cx, cy), 1.75, linewidth=2.2, edgecolor=color,
                            facecolor=matplotlib.colors.to_rgba(color, 0.07), zorder=2))
        ax.text(cx, 7.1, rotulo, ha="center", va="center", fontsize=11,
                color=C_TXT, fontweight="bold")
        ax.text(cx, cy + 0.3, texto, ha="center", va="center", fontsize=11.5,
                color=C_TXT, fontweight="bold", linespacing=1.25, zorder=3)
        ax.text(cx, cy - 1.05, "niveles: " + niveles, ha="center", va="center",
                fontsize=8.4, color=C_MUTED, style="italic", zorder=3)

    # Problema: la causa en su nivel de caja negra incide en el efecto.
    _flecha(ax, (3.95, 5.55), (8.05, 5.55), color=C_MAL, rad=-0.2, lw=1.8)
    ax.text(6.0, 4.6, "Problema:\nla escasa transparencia\n(caja negra) incide en\n"
            "la baja trazabilidad\ny verificabilidad", ha="center", va="center",
            fontsize=9.3, color=C_TXT, linespacing=1.3)

    # Solución: EduFEM actúa sobre la causa (ciclo inferior, como en la lámina).
    _caja(ax, 4.35, 0.2, 3.3, 1.05, C_INT)
    ax.text(6.0, 0.97, "Variable interviniente (solución)", ha="center",
            va="center", fontsize=9.6, color=C_TXT)
    ax.text(6.0, 0.53, "EduFEM", ha="center", va="center", fontsize=12.5,
            color=C_TXT, fontweight="bold")
    _flecha(ax, (9.35, 2.72), (7.75, 0.75), rad=-0.25)
    _flecha(ax, (4.25, 0.75), (2.65, 2.72), rad=-0.25)
    ax.text(6.0, 2.2, "Hipótesis: EduFEM lleva la transparencia\n"
            "al nivel de procedimiento a la vista y eleva\n"
            "la trazabilidad y la verificabilidad", ha="center", va="center",
            fontsize=9.3, color=C_TXT, linespacing=1.3)
    _guardar(fig, carpeta, "fig_relacion_variables.png")


# ─────────────────────────────────────────────────────────────────────────────
# Figura CR.1 — contraste de la hipótesis
# ─────────────────────────────────────────────────────────────────────────────

def fig_contraste_hipotesis(carpeta, d):
    fig, ax = plt.subplots(figsize=(10.4, 6.8))
    ax.set_xlim(0, 13); ax.set_ylim(0, 8.5); ax.axis("off")

    # Causa: de la caja negra al procedimiento a la vista.
    _caja(ax, 0.2, 1.35, 3.6, 5.3, C_VI)
    ax.text(2.0, 6.25, "Transparencia del\nprocedimiento de cálculo", ha="center",
            va="center", fontsize=10.5, color=C_TXT, fontweight="bold")
    ax.text(2.0, 5.05, "Software comercial:\ncaja negra\n(solo datos y resultados)",
            ha="center", va="center", fontsize=9.2, color=C_TXT)
    _flecha(ax, (2.0, 4.35), (2.0, 3.55), color=C_INT, lw=2.0)
    ax.text(2.25, 3.95, "EduFEM", ha="left", va="center", fontsize=10,
            color=C_TXT, fontweight="bold")
    ax.text(2.0, 2.55, "Procedimiento a la vista:\nmódulos educativos,\n"
            "post-proceso y memoria\nde cálculo", ha="center", va="center",
            fontsize=9.2, color=C_TXT)

    _flecha(ax, (3.95, 4.0), (4.75, 5.15), rad=-0.1, lw=1.8)
    _flecha(ax, (3.95, 4.0), (4.75, 2.55), rad=0.1, lw=1.8)

    t = d["tasas"]
    clausulas = [
        (4.25, "(a) Trazabilidad", [
            "7 de 7 etapas con módulo educativo",
            "9 de 9 etapas desarrolladas en la memoria de cálculo",
            "solución y tensiones en el post-proceso (crudo y suavizado)",
            "3 de 3 fases sobre un mismo lienzo",
            "18 de 18 contenidos del consenso de expertos con instrumento",
            "intercambio de datos sin pérdida",
        ]),
        (0.25, "(b) Verificabilidad", [
            "tasas iguales a las teóricas: Q4 "
            f"{_coma(round(t[('q4','L2_disp')][0], 2), 2)} ($L^2$) y "
            f"{_coma(round(t[('q4','H1_semi')][0], 2), 2)} ($H^1$); Q9 "
            f"{_coma(round(t[('q9','L2_disp')][0], 2), 2)} y "
            f"{_coma(round(t[('q9','H1_semi')][0], 2), 2)}",
            f"Timoshenko: {_coma(d['sx_anal'], 2)} % en $\\sigma_x$ y "
            f"{_coma(d['flecha'], 2)} % en la flecha",
            f"SAP2000: {_coma(d['sx_sap'], 2)} % en $\\sigma_x$",
            f"equilibrio de reacciones: residuo "
            f"{_coma(d['residuo'] * 1e13, 1)}×10⁻¹³",
            f"Cook: {_coma(d['cook_err'], 3)} % con Q9 (N = 8) y bloqueo del Q4",
            "memoria del ejemplo canónico reproducible a mano",
        ]),
    ]
    for y0, titulo, items in clausulas:
        _caja(ax, 4.85, y0, 8.0, 3.45, C_VD)
        ax.text(5.1, y0 + 3.05, titulo, ha="left", va="center", fontsize=11,
                color=C_TXT, fontweight="bold")
        ax.text(12.6, y0 + 3.05, "✓ Se cumple", ha="right", va="center",
                fontsize=10.5, color=C_OK, fontweight="bold")
        for i, item in enumerate(items):
            ax.text(5.25, y0 + 2.55 - 0.44 * i, "•  " + item, ha="left",
                    va="center", fontsize=9.3, color=C_TXT)

    ax.text(6.5, 8.2, "La hipótesis queda comprobada en sus dos cláusulas, "
            "con criterios fijados de antemano", ha="center", va="center",
            fontsize=11, color=C_TXT, fontweight="bold")
    _guardar(fig, carpeta, "fig_contraste_hipotesis.png")


# ─────────────────────────────────────────────────────────────────────────────
# Figura CR.2 — margen de cada criterio numérico
# ─────────────────────────────────────────────────────────────────────────────

def fig_margen_criterios(carpeta, d):
    t = d["tasas"]
    filas = []   # (rótulo, observado/umbral)
    for el, col, nombre in [("q4", "L2_disp", "Tasa L², Q4"),
                            ("q9", "L2_disp", "Tasa L², Q9"),
                            ("q4", "H1_semi", "Tasa H¹, Q4"),
                            ("q9", "H1_semi", "Tasa H¹, Q9")]:
        v, p = t[(el, col)]
        filas.append((f"{nombre}: desvío de {_coma(abs(v - p), 4)} "
                      f"(umbral ± 0,5)", abs(v - p) / 0.5))
    filas += [
        (f"Flecha, Timoshenko: {_coma(d['flecha'], 2)} % (umbral < 3 %)",
         d["flecha"] / 3.0),
        (f"$\\sigma_x$ frente a la analítica: {_coma(d['sx_anal'], 2)} % "
         f"(umbral < 1 %)", d["sx_anal"] / 1.0),
        (f"$\\sigma_x$ frente a SAP2000: {_coma(d['sx_sap'], 2)} % (umbral < 1 %)",
         d["sx_sap"] / 1.0),
        (f"Residuo de equilibrio: {_coma(d['residuo'] * 1e13, 1)}×10⁻¹³ "
         f"(umbral < 10⁻⁸)", d["residuo"] / 1e-8),
        (f"Cook, Q9 con N = 8: {_coma(d['cook_err'], 3)} % (umbral < 1,5 %)",
         d["cook_err"] / 1.5),
    ]
    assert all(0 < r < 1 for _, r in filas), filas

    fig, ax = plt.subplots(figsize=(9.2, 4.9))
    ys = list(range(len(filas)))[::-1]
    x0 = 1e-6
    for y, (_, r) in zip(ys, filas):
        ax.plot([x0, r], [y, y], color=C_GRID, lw=1.4, zorder=1,
                solid_capstyle="round")
        ax.plot([r], [y], "o", ms=8.5, color=C_VI, mec="white", mew=2,
                zorder=3)
    ax.axvline(1.0, color=C_TXT, lw=1.3, zorder=2)
    ax.axvspan(1.0, 4.0, color="#f1f3f5", zorder=0)
    ax.text(1.12, len(filas) - 0.35, "umbral", ha="left", va="center",
            fontsize=9.5, color=C_TXT)
    ax.text(1.12, len(filas) - 0.95, "(no cumple\na la derecha)", ha="left",
            va="top", fontsize=8.3, color=C_MUTED)
    ax.set_xscale("log")
    ax.set_xlim(x0, 4.0)
    ax.set_ylim(-0.7, len(filas) - 0.1)
    ax.set_yticks(ys)
    ax.set_yticklabels([f for f, _ in filas], fontsize=9.3, color=C_TXT)
    ax.set_xlabel("Valor observado dividido por su umbral (escala logarítmica)",
                  fontsize=10, color=C_TXT)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=C_MUTED, labelsize=9)
    ax.grid(axis="x", which="major", color=C_GRID, lw=0.7)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(C_GRID)
    for yy in (4.5, 0.5):       # separa MMS | Timoshenko | Cook
        ax.axhline(yy, color=C_GRID, lw=0.8, zorder=0)
    _guardar(fig, carpeta, "fig_margen_criterios.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--out", default=OUT_DEFECTO)
    args = ap.parse_args()
    print("Comprobando las cifras contra docs/vyv/datos/ y la tesis...")
    d = reunir_datos()
    print("  cifras coinciden con tab:veredicto")
    print("Generando figuras en:", args.out)
    fig_relacion_variables(args.out)
    fig_contraste_hipotesis(args.out, d)
    fig_margen_criterios(args.out, d)


if __name__ == "__main__":
    main()
