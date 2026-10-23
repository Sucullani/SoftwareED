# -*- coding: utf-8 -*-
"""
generar_figuras_formulacion.py — Figuras de la formulación de la tesis.

Tres figuras que nacieron con final3 (observaciones del Ing. Julio Saúl
Miranda, 2026-09-25) y que final4 rehízo (tribunal, defensa de borrador):

  fig_relacion_variables.pdf   §2.1.2. Relación entre las variables: el diagrama
                               de círculos de sus láminas (causa → efecto, con la
                               solución que cierra el ciclo).
  fig_contraste_hipotesis.pdf  Conclusiones. La hipótesis, parte por parte: cada
                               tramo del enunciado con lo que se comprobó y su
                               veredicto.
  fig_margen_criterios.pdf     Conclusiones. Qué fracción de su umbral consume
                               cada criterio numérico de la cláusula (b).

Las cifras se leen de docs/vyv/datos/*.csv, los mismos datos de las tablas del
Cap. 3. Antes de dibujar, el guion aísla la tabla de veredicto de la tesis
(tab:veredicto, 04_resultados.tex) y comprueba, fila por fila, que cada cifra
impresa coincide con la del CSV, que la cláusula (a) tiene sus seis criterios y
la (b) sus nueve, y que todos dicen «Se cumple». Si algo no coincide, termina
con error y no escribe ninguna figura.

Las figuras se escriben en PDF vectorial al ancho de la caja de texto (15,92 cm)
y se incluyen a ese ancho: el cuerpo de letra que fija este guion es el que se
imprime (APA pide entre 8 y 14 puntos dentro de las figuras). La letra es la
Times New Roman del texto, con DejaVu Sans de respaldo para el signo ✓.

Reproducible (desde la raíz del repositorio):

    .venv\\Scripts\\python.exe tesis\\figuras\\generar_figuras_formulacion.py --version final4

Lee tesis/capitulos_<version>/04_resultados.tex y escribe en
tesis/capitulos_<version>/figuras/ (la salida se cambia con --out DIR).
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
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
VERSION_DEFECTO = "final4"
ANCHO_CM = 15.92          # caja de texto: A4 menos dos márgenes de 2,54 cm
CM = 1 / 2.54             # pulgadas por centímetro

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


def configurar_estilo():
    """Times New Roman como el texto de la tesis; DejaVu Sans solo para los
    signos que la Times no tiene (✓). Fórmulas en Computer Modern, como las de
    la tesis (Latin Modern). Fuentes TrueType incrustadas en el PDF."""
    plt.rcParams.update({
        "font.family": ["Times New Roman", "DejaVu Sans"],
        "mathtext.fontset": "cm",
        "font.size": 9,
        "pdf.fonttype": 42,
        "axes.unicode_minus": False,
    })


class ErrorGuarda(SystemExit):
    pass


def _fallar(msg):
    raise ErrorGuarda(f"[guarda] {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Datos y comprobación contra la tesis
# ─────────────────────────────────────────────────────────────────────────────

def _leer(nombre):
    with open(os.path.join(DATOS, nombre), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _coma(x, nd):
    """Número con coma decimal, como lo escribe la tesis en el texto."""
    return f"{x:.{nd}f}".replace(".", ",")


def _coma_tex(x, nd):
    """Número como lo escribe la tesis dentro de una fórmula: 0{,}26."""
    return f"{x:.{nd}f}".replace(".", "{,}")


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
            if round(v, 2) != p:
                _fallar(f"tasa {el} {col} = {v:.4f}, la tesis dice {p:.2f}")
        peor = max(valores, key=lambda v: abs(v - p))
        tasas[(el, col)] = (peor, p)

    flecha = float(_leer("timoshenko_deflexion.csv")[0]["err_pct"])
    tension = _leer("timoshenko_stress.csv")
    sx_anal = max(float(f["err_anal_pct"]) for f in tension)
    sx_sap = max(float(f["err_sap_pct"]) for f in tension)
    residuo = float(_leer("timoshenko_equilibrio.csv")[0]["residuo_relativo"])
    cook = next(f for f in _leer("cook.csv")
                if f["element_type"] == "Q9" and int(f["N"]) == 8)
    cook_q4 = next(f for f in _leer("cook.csv")
                   if f["element_type"] == "Q4" and int(f["N"]) == 8)
    return {"tasas": tasas, "flecha": flecha, "sx_anal": sx_anal,
            "sx_sap": sx_sap, "residuo": residuo,
            "cook_err": abs(float(cook["error_pct"])),
            "cook_q9": float(cook["uy"]), "cook_q4": float(cook_q4["uy"])}


def leer_veredicto(ruta_cap3):
    """Aísla el longtable de tab:veredicto y devuelve sus filas de criterio,
    agrupadas por cláusula: {"a": [[celdas]], "b": [[celdas]]}."""
    if not os.path.exists(ruta_cap3):
        _fallar(f"no existe {ruta_cap3}")
    with open(ruta_cap3, encoding="utf-8") as fh:
        cap3 = fh.read()
    i = cap3.find(r"\label{tab:veredicto}")
    if i < 0:
        _fallar("no se encuentra \\label{tab:veredicto} en 04_resultados.tex")
    j = cap3.find(r"\end{longtable}", i)
    tabla = cap3[i:j]
    grupos, actual = {"a": [], "b": []}, None
    for trozo in re.split(r"\\\\\*?", tabla):
        trozo = trozo.strip()
        m = re.search(r"Cláusula \((a|b)\)", trozo)
        if m and "&" not in trozo:
            actual = m.group(1)
            continue
        if actual is None or trozo.count("&") != 4:
            continue
        celdas = [c.strip() for c in trozo.split("&")]
        celdas[0] = re.sub(r"\\(midrule|bottomrule|endfoot|endhead)\s*", "", celdas[0]).strip()
        grupos[actual].append(celdas)
    return grupos


def comprobar_veredicto(d, grupos):
    """Cada cifra de la figura, en la fila de la tabla de veredicto que la
    imprime; seis criterios en (a), nueve en (b), todos «Se cumple»."""
    a, b = grupos["a"], grupos["b"]
    if len(a) != 6 or len(b) != 9:
        _fallar(f"tab:veredicto tiene {len(a)} criterios en (a) y {len(b)} en (b); "
                "se esperaban 6 y 9")
    for fila in a + b:
        if fila[4] != "Se cumple":
            _fallar(f"criterio sin «Se cumple»: {fila[0]!r} -> {fila[4]!r}")

    def observado(grupo, clave):
        filas = [f for f in grupo if clave in f[0]]
        if len(filas) != 1:
            _fallar(f"{len(filas)} filas de tab:veredicto contienen {clave!r}")
        return filas[0][2]

    esperados_a = {"módulo educativo": "7 de 7", "desarrollo en la memoria": "9 de 9",
                   "post-proceso": "Ambas", "mismo lienzo": "3 de 3",
                   "universo de contenido": "18 de 18", "CSV": "Sin pérdida y sin error"}
    for clave, texto in esperados_a.items():
        if texto not in observado(a, clave):
            _fallar(f"(a) {clave}: la tabla no imprime {texto!r}")

    t = d["tasas"]
    esperados_b = {
        "norma $L^2$": f"Q4: {_coma(t[('q4', 'L2_disp')][1], 2)}; "
                       f"Q9: {_coma(t[('q9', 'L2_disp')][1], 2)}",
        "seminorma $H^1$": f"Q4: {_coma(t[('q4', 'H1_semi')][1], 2)}; "
                           f"Q9: {_coma(t[('q9', 'H1_semi')][1], 2)}",
        "flecha central": _coma_tex(d["flecha"], 2),
        "solución analítica, tres": _coma_tex(d["sx_anal"], 2),
        "SAP2000": _coma_tex(d["sx_sap"], 2),
        "equilibrio": f"{_coma_tex(d['residuo'] * 1e13, 1)}\\times10^{{-13}}",
        "Cook": _coma_tex(d["cook_err"], 3),
        "bloqueo": f"{_coma_tex(d['cook_q4'], 3)} < {_coma_tex(d['cook_q9'], 3)}",
        "memoria": "Todas",
    }
    for clave, texto in esperados_b.items():
        if texto not in observado(b, clave):
            _fallar(f"(b) {clave}: la tabla no imprime {texto!r} "
                    f"(imprime {observado(b, clave)!r})")
    return {"a": (len(a), 6), "b": (len(b), 9)}


def margenes(d):
    """(rótulo, observado/umbral) de cada criterio numérico de la cláusula (b)."""
    t = d["tasas"]
    filas = []
    for el, col, nombre in [("q4", "L2_disp", "Tasa $L^2$, Q4"),
                            ("q9", "L2_disp", "Tasa $L^2$, Q9"),
                            ("q4", "H1_semi", "Tasa $H^1$, Q4"),
                            ("q9", "H1_semi", "Tasa $H^1$, Q9")]:
        v, p = t[(el, col)]
        filas.append((f"{nombre}: desvío de {_coma(abs(v - p), 4)} "
                      f"(margen ± 0,5)", abs(v - p) / 0.5))
    filas += [
        (f"Flecha, Timoshenko: {_coma(d['flecha'], 2)} % (umbral < 3 %)",
         d["flecha"] / 3.0),
        (f"$\\sigma_x$ frente a la analítica: {_coma(d['sx_anal'], 2)} % "
         f"(umbral < 1 %)", d["sx_anal"] / 1.0),
        (f"$\\sigma_x$ frente a SAP2000: {_coma(d['sx_sap'], 2)} % (umbral < 1 %)",
         d["sx_sap"] / 1.0),
        (f"Residuo de equilibrio: {_coma(d['residuo'] * 1e13, 1)}"
         f"$\\times10^{{-13}}$ (umbral < $10^{{-8}}$)", d["residuo"] / 1e-8),
        (f"Cook, Q9 con $N = 8$: {_coma(d['cook_err'], 3)} % (umbral < 1,5 %)",
         d["cook_err"] / 1.5),
    ]
    for rotulo, r in filas:
        if not 0 < r < 1:
            _fallar(f"criterio fuera de su umbral: {rotulo} (cociente {r:.3g})")
    return filas


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de dibujo (coordenadas en centímetros, letra en puntos)
# ─────────────────────────────────────────────────────────────────────────────

def _lienzo(alto_cm, ancho_cm=ANCHO_CM):
    fig = plt.figure(figsize=(ancho_cm * CM, alto_cm * CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, ancho_cm); ax.set_ylim(0, alto_cm); ax.axis("off")
    return fig, ax


def _guardar(fig, carpeta, nombre, formato):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{nombre}.{formato}")
    # Sin bbox_inches="tight": el ancho del archivo es el de la caja de texto y la
    # letra se imprime al cuerpo fijado aquí.
    fig.savefig(ruta, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] {os.path.basename(ruta)}")
    return ruta


def _caja(ax, x, y, w, h, color, relleno=0.07, lw=1.4, estilo="solid", radio=0.18):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={radio}",
                                linewidth=lw, edgecolor=color, linestyle=estilo,
                                facecolor=matplotlib.colors.to_rgba(color, relleno),
                                zorder=2))


def _flecha(ax, a, b, color=C_MUTED, rad=0.0, lw=1.2, escala=11):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=escala,
                                 color=color, lw=lw, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))


# ─────────────────────────────────────────────────────────────────────────────
# Figura 2.1 — relación entre las variables
# ─────────────────────────────────────────────────────────────────────────────

def fig_relacion_variables(carpeta, formato):
    # Alto contenido (8,5 cm): con el rótulo, la figura ocupa menos de la mitad de la
    # hoja y puede ir arriba con texto debajo, en lugar de quedar sola en una hoja.
    alto = 8.5
    fig, ax = _lienzo(alto)
    cy, r = 5.55, 2.0             # centro y radio de los dos círculos
    for cx, color, rotulo, texto, niveles in [
        (2.55, C_VI, "Variable independiente (causa)",
         "Transparencia\ndel procedimiento\nde cálculo", "niveles:\ncaja negra | a la vista"),
        (13.37, C_VD, "Variable dependiente (efecto)",
         "Trazabilidad y\nverificabilidad del\nprocedimiento\nde cálculo", "niveles:\nbaja | alta"),
    ]:
        ax.add_patch(Circle((cx, cy), r, linewidth=1.5, edgecolor=color,
                            facecolor=matplotlib.colors.to_rgba(color, 0.07), zorder=2))
        ax.text(cx, cy + r + 0.42, rotulo, ha="center", va="center", fontsize=10,
                color=C_TXT, fontweight="bold")
        ax.text(cx, cy + 0.42, texto, ha="center", va="center", fontsize=10,
                color=C_TXT, fontweight="bold", linespacing=1.15, zorder=3)
        ax.text(cx, cy - 1.0, niveles, ha="center", va="center",
                fontsize=8, color=C_MUTED, linespacing=1.15, zorder=3)

    # Problema: la causa en su nivel de caja negra incide en el efecto.
    _flecha(ax, (4.5, cy + 0.95), (11.42, cy + 0.95), color=C_MAL, rad=-0.16, lw=1.4)
    ax.text(7.96, cy - 0.2, "Problema:\nla escasa transparencia\n(caja negra) incide en\n"
            "la baja trazabilidad\ny verificabilidad", ha="center", va="center",
            fontsize=9, color=C_TXT, linespacing=1.2)

    # Solución: EduFEM, desarrollado bajo un método de diseño, actúa sobre la causa
    # (ciclo inferior, como en la lámina del tribunal).
    _caja(ax, 3.56, 0.15, 8.8, 1.55, C_INT)
    ax.text(7.96, 1.38, "Variable interviniente (solución)", ha="center",
            va="center", fontsize=9, color=C_TXT)
    ax.text(7.96, 0.93, "EduFEM", ha="center", va="center", fontsize=11.5,
            color=C_TXT, fontweight="bold")
    ax.text(7.96, 0.48, "desarrollado bajo un método de diseño de software educativo",
            ha="center", va="center", fontsize=9, color=C_TXT)
    _flecha(ax, (13.2, cy - r - 0.1), (12.46, 0.95), rad=-0.3)
    _flecha(ax, (3.46, 0.95), (2.72, cy - r - 0.1), rad=-0.3)
    # No se rotula «Hipótesis»: su enunciado literal está en el texto. Aquí van los
    # papeles: la intervención (premisa) y el efecto que la hipótesis predice.
    ax.text(7.96, 2.55, "Intervención: el desarrollo de EduFEM pone el procedimiento\n"
            "a la vista. La hipótesis predice que permitirá mejorar\n"
            "la trazabilidad y la verificabilidad del análisis",
            ha="center", va="center", fontsize=9, color=C_TXT, linespacing=1.25)
    return _guardar(fig, carpeta, "fig_relacion_variables", formato)


# ─────────────────────────────────────────────────────────────────────────────
# Figura CR.1 — la hipótesis, parte por parte
# ─────────────────────────────────────────────────────────────────────────────

def fig_contraste_hipotesis(carpeta, d, conteos, formato):
    (na, ta), (nb, tb) = conteos["a"], conteos["b"]
    # Cada caja nombra una parte de la hipótesis, en el orden de su enunciado, sin
    # copiarlo: el enunciado literal está en la Introducción, §2.1.3 y §3.8 (el
    # autor pidió no repetirlo en las Conclusiones). El veredicto global lo da el
    # texto que acompaña a la figura.
    partes = [
        # (color, papel, parte, qué se comprobó, veredicto)
        (C_INT, "Condición · variable interviniente",
         "método de diseño de software educativo",
         "Ciencia del diseño, aplicada en sus seis\nactividades: requisitos tomados de los\n"
         "antecedentes y decisiones de diseño trazadas\na cuatro principios.",
         "✓ Respaldada"),
        (C_INT, "Intervención · variable interviniente",
         "desarrollo de EduFEM",
         "De caja negra a procedimiento a la vista:\nmódulos educativos, post-proceso y "
         "memoria\nde cálculo sobre el modelo del usuario.",
         "✓ Respaldada"),
        (C_VD, "Efecto (a) · variable dependiente",
         "trazabilidad del análisis",
         "Antes: ningún resultado se sigue etapa\npor etapa. Con EduFEM: 7 de 7 etapas con\n"
         "módulo, 9 de 9 en la memoria, 3 de 3 fases\nen un lienzo y 18 de 18 contenidos.",
         f"✓ Se cumple\n{na} de {ta} criterios"),
        (C_VD, "Efecto (b) · variable dependiente",
         "verificabilidad del análisis",
         "Antes: solo se comprueba el resultado final.\nCon EduFEM: tasas teóricas, solución\n"
         "analítica, SAP2000, equilibrio, membrana de\nCook y memoria reproducible a mano.",
         f"✓ Se cumple\n{nb} de {tb} criterios"),
        (C_VI, "Antecedente · variable independiente",
         "escasa transparencia del software\nde análisis",
         "Software comercial de análisis: cálculo paso\na paso «Baja (caja negra)», "
         "informes sin\nel desarrollo matricial.",
         "✓ Respaldado"),
    ]
    # Alto de cada fila según su contenido: la parte lleva además el renglón de
    # su papel; 0,40 cm por renglón de 9-9,5 pt con interlineado 1,2.
    def _renglones(s):
        return s.count("\n") + 1
    altos = [0.40 * max(_renglones(tramo) + 1, _renglones(prueba)) + 0.45
             for _, _, tramo, prueba, _ in partes]
    sep, cab, pie = 0.16, 0.75, 0.0
    alto = cab + sum(altos) + sep * len(partes) + pie + 0.1
    fig, ax = _lienzo(alto)
    x1, w1 = 0.05, 6.25          # parte de la hipótesis
    x2, w2 = 6.85, 6.25          # qué se comprobó
    x3, w3 = 13.35, 2.52         # veredicto
    ytop = alto - cab
    for x, texto in [(x1, "Parte de la hipótesis"), (x2, "Evidencia"),
                     (x3, "Veredicto")]:
        ax.text(x + 0.1, ytop + 0.35, texto, ha="left", va="center", fontsize=9,
                color=C_MUTED, fontweight="bold")
    y_cursor = ytop
    for i, (color, papel, tramo, prueba, veredicto) in enumerate(partes):
        alto_fila = altos[i]
        y0 = y_cursor - alto_fila
        y_cursor = y0 - sep
        _caja(ax, x1, y0, w1, alto_fila, color)
        # El papel y el tramo van centrados como bloque en la altura de la caja.
        arriba = y0 + alto_fila / 2 + 0.40 * (_renglones(tramo) + 1) / 2
        ax.text(x1 + 0.2, arriba - 0.20, papel, ha="left", va="center",
                fontsize=8.5, color=color if color != C_INT else "#b35c00",
                fontweight="bold")
        ax.text(x1 + 0.2, arriba - 0.44, tramo, ha="left", va="top",
                fontsize=9.5, color=C_TXT, linespacing=1.2)
        _flecha(ax, (x1 + w1 + 0.06, y0 + alto_fila / 2),
                (x2 - 0.06, y0 + alto_fila / 2), lw=1.1)
        ax.text(x2 + 0.05, y0 + alto_fila / 2, prueba, ha="left", va="center",
                fontsize=9, color=C_TXT, linespacing=1.2)
        ax.text(x3 + 0.1, y0 + alto_fila / 2, veredicto, ha="left", va="center",
                fontsize=9.5, color=C_OK, fontweight="bold", linespacing=1.2)
    return _guardar(fig, carpeta, "fig_contraste_hipotesis", formato)


# ─────────────────────────────────────────────────────────────────────────────
# Figura CR.2 — margen de cada criterio numérico
# ─────────────────────────────────────────────────────────────────────────────

def fig_margen_criterios(carpeta, filas, formato):
    # Rótulos a 11,5 pt: así los exponentes y subíndices (al 70 %) no bajan de 8 pt.
    fig = plt.figure(figsize=(ANCHO_CM * CM, 9.0 * CM))
    ax = fig.add_axes([0.57, 0.16, 0.42, 0.81])
    ys = list(range(len(filas)))[::-1]
    x0 = 1e-6
    for y, (_, r) in zip(ys, filas):
        ax.plot([x0, r], [y, y], color=C_GRID, lw=1.2, zorder=1,
                solid_capstyle="round")
        ax.plot([r], [y], "o", ms=6.5, color=C_VI, mec="white", mew=1.5,
                zorder=3)
    ax.axvline(1.0, color=C_TXT, lw=1.1, zorder=2)
    ax.axvspan(1.0, 100.0, color="#f1f3f5", zorder=0)
    ax.text(1.25, len(filas) - 0.55, "umbral", ha="left", va="center",
            fontsize=9, color=C_TXT)
    ax.text(1.25, len(filas) - 1.15, "no cumple\na la derecha", ha="left",
            va="top", fontsize=8.5, color=C_MUTED, linespacing=1.15)
    ax.set_xscale("log")
    ax.set_xlim(x0, 100.0)
    ax.set_xticks([1e-6, 1e-4, 1e-2, 1.0])   # sin marca en 10², que el borde cortaba
    ax.set_ylim(-0.6, len(filas) - 0.2)
    ax.set_yticks(ys)
    ax.set_yticklabels([f for f, _ in filas], fontsize=11.5, color=C_TXT)
    ax.set_xlabel("Observado ÷ umbral (escala logarítmica)", fontsize=9.5, color=C_TXT)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=C_MUTED, labelsize=11.5)
    ax.grid(axis="x", which="major", color=C_GRID, lw=0.6)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(C_GRID)
    for yy in (4.5, 0.5):       # separa MMS | Timoshenko | Cook
        ax.axhline(yy, color=C_GRID, lw=0.7, zorder=0)
    return _guardar(fig, carpeta, "fig_margen_criterios", formato)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--version", default=VERSION_DEFECTO,
                    help="versión de la tesis: lee y escribe en tesis/capitulos_<version>/")
    ap.add_argument("--out", default=None, help="carpeta de salida (por defecto, la figuras/ de la versión)")
    ap.add_argument("--formato", default="pdf", choices=("pdf", "png"))
    ap.add_argument("--solo-comprobar", action="store_true",
                    help="comprueba las cifras contra la tesis y no dibuja nada")
    args = ap.parse_args(argv)
    tesis = os.path.join(_ROOT, "tesis", f"capitulos_{args.version}")
    if not os.path.isdir(tesis):
        _fallar(f"no existe la carpeta de la versión: {tesis}")
    salida = args.out or os.path.join(tesis, "figuras")

    configurar_estilo()
    print("Comprobando las cifras contra docs/vyv/datos/ y la tabla de veredicto...")
    d = reunir_datos()
    conteos = comprobar_veredicto(d, leer_veredicto(os.path.join(tesis, "04_resultados.tex")))
    filas = margenes(d)
    print(f"  cifras coinciden con tab:veredicto ({args.version}): "
          f"(a) {conteos['a'][0]} criterios, (b) {conteos['b'][0]} criterios")
    if args.solo_comprobar:
        return 0
    print("Generando figuras en:", salida)
    fig_relacion_variables(salida, args.formato)
    fig_contraste_hipotesis(salida, d, conteos, args.formato)
    fig_margen_criterios(salida, filas, args.formato)
    return 0


if __name__ == "__main__":
    sys.exit(main())
