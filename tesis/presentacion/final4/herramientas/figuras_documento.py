"""
figuras_documento.py — las gráficas de la tesis, idénticas, para animarlas en la presentación.

La presentación no redibuja a su manera las gráficas de resultados: usa las MISMAS funciones de
dibujo que generan las figuras de la tesis (final4), con los mismos datos de docs/vyv/datos/:

  Figura 3.1 (a) y (b)  tests/vv_mms.py::plot_convergence     error frente a h, en escala log-log
  Figura 3.4            tests/vv_cook.py::plot_convergence    u_y frente a GDL totales
  Figura CR.2           tesis/figuras/generar_figuras_formulacion.py::fig_margen_criterios

Solo cambian tres cosas, ninguna del contenido:
  1. el formato: SVG con el texto convertido en trazos (se ve igual en cualquier equipo);
  2. la letra y los trazos de las Figuras 3.1 y 3.4, más grandes, para leerse proyectados
     (los ejes, las escalas, los rótulos, la leyenda y los datos son los del documento);
  3. cada serie lleva un identificador (gid) para que la presentación la dibuje por partes.

Salida:
  assets/data/figuras_doc.js     window.EDUFEM_FIGDOC = { mms_l2: '<svg…>', mms_h1, cook, margen_cr2 }
  herramientas/_trabajo/figuras_doc/*.png   las mismas figuras en PNG, para revisarlas a ojo

Uso (desde la raíz del repositorio):
  .venv\\Scripts\\python.exe tesis\\presentacion\\final4\\herramientas\\figuras_documento.py
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(AQUI)
RAIZ = os.path.abspath(os.path.join(FINAL, "..", "..", ".."))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tesis", "figuras"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.figure  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

DATOS = os.path.join(RAIZ, "docs", "vyv", "datos")
SALIDA_JS = os.path.join(FINAL, "assets", "data", "figuras_doc.js")
REVISION = os.path.join(AQUI, "_trabajo", "figuras_doc")

# ------------------------------------------------------------------ captura de savefig
# Las funciones de la tesis llaman fig.savefig(ruta_png) y cierran la figura. Se intercepta
# esa llamada: se etiqueta cada serie y se guarda en SVG (y una copia PNG para revisión).
_original_savefig = matplotlib.figure.Figure.savefig
_capturas: dict[str, str] = {}
_destino = {"clave": None, "etiquetar": None}


def _savefig_capturado(self, fname, *args, **kwargs):
    clave = _destino["clave"]
    if clave is None:
        return _original_savefig(self, fname, *args, **kwargs)
    if _destino["etiquetar"]:
        _destino["etiquetar"](self)
    buf = io.StringIO()
    kw = {k: v for k, v in kwargs.items() if k not in ("format", "dpi")}
    _original_savefig(self, buf, *args, format="svg", **kw)
    _capturas[clave] = buf.getvalue()
    os.makedirs(REVISION, exist_ok=True)
    _original_savefig(self, os.path.join(REVISION, f"{clave}.png"), *args,
                      format="png", dpi=110, **kw)
    return None


matplotlib.figure.Figure.savefig = _savefig_capturado


def _etiquetar_series(fig):
    """MMS y Cook: una serie por elemento, más sus líneas de referencia."""
    ax = fig.axes[0]
    for ln in ax.get_lines():
        lab = (ln.get_label() or "").replace("$", "")
        if lab == "Q4":
            ln.set_gid("serie_q4")
        elif lab == "Q9":
            ln.set_gid("serie_q9")
        elif lab.startswith("referencia"):
            ln.set_gid("referencia")
        elif ln.get_color() in ("#0d6efd",) and ln.get_linestyle() == "--":
            ln.set_gid("pend_q4")
        elif ln.get_color() in ("#fd7e14",) and ln.get_linestyle() == "--":
            ln.set_gid("pend_q9")
    leg = ax.get_legend()
    if leg is not None:
        leg.set_gid("leyenda")


def _etiquetar_margen(fig):
    """Figura CR.2: por cada criterio, la barra gris (gid barra_k) y el punto (punto_k), de arriba abajo."""
    ax = fig.axes[0]
    k = 0
    lineas = ax.get_lines()
    for ln in lineas:
        xs = list(ln.get_xdata())
        if len(xs) == 2 and xs[0] == xs[1] == 1.0:
            ln.set_gid("umbral")
    i = 0
    while i < len(lineas):
        ln = lineas[i]
        if ln.get_marker() in ("None", None, "") and len(ln.get_xdata()) == 2 and i + 1 < len(lineas) \
                and lineas[i + 1].get_marker() == "o":
            ln.set_gid(f"barra_{k}")
            lineas[i + 1].set_gid(f"punto_{k}")
            k += 1
            i += 2
            continue
        i += 1


def _prefijar_ids(svg: str, clave: str) -> str:
    """Antepone la clave de la figura a cada id (y a sus referencias), para que dos figuras
    en la misma lámina no compartan identificadores: serie_q4 -> mms_l2__serie_q4."""
    import re
    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    for x in sorted(ids, key=len, reverse=True):
        nuevo = f"{clave}__{x}"
        svg = svg.replace(f'id="{x}"', f'id="{nuevo}"')
        svg = svg.replace(f'"#{x}"', f'"#{nuevo}"')
        svg = svg.replace(f"url(#{x})", f"url(#{nuevo})")
    # sin tamaño fijo: la lámina lo dimensiona por su contenedor
    svg = re.sub(r'<svg([^>]*?) width="[^"]+" height="[^"]+"', r'<svg\1', svg, count=1)
    return svg


# ------------------------------------------------------------------ estilo de proyección
def _estilo_proyeccion():
    """Letra y trazos más grandes en las Figuras 3.1 y 3.4 (el contenido no cambia)."""
    plt.rcdefaults()
    plt.rcParams.update({
        "font.size": 15,
        "axes.titlesize": 17,
        "axes.labelsize": 16,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 14,
        "lines.linewidth": 2.6,
        "lines.markersize": 9,
        "svg.fonttype": "path",
    })


# ------------------------------------------------------------------ datos
def _leer_csv(nombre):
    with open(os.path.join(DATOS, nombre), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _mms(nombre):
    filas = _leer_csv(nombre)
    return [{"N": int(r["N"]), "h": float(r["h"]), "L2_disp": float(r["L2_disp"]),
             "H1_semi": float(r["H1_semi"]), "L2_stress": float(r["L2_stress"])} for r in filas]


def _cook():
    filas = _leer_csv("cook.csv")
    q4 = [{"N": int(r["N"]), "ndof": int(r["ndof"]), "uy": float(r["uy"])} for r in filas if r["element_type"].upper() == "Q4"]
    q9 = [{"N": int(r["N"]), "ndof": int(r["ndof"]), "uy": float(r["uy"])} for r in filas if r["element_type"].upper() == "Q9"]
    return q4, q9


def main():
    from tests import vv_cook, vv_mms  # las funciones de dibujo de la tesis

    q4, q9 = _mms("mms_q4.csv"), _mms("mms_q9.csv")
    _estilo_proyeccion()
    _destino.update(clave="mms_l2", etiquetar=_etiquetar_series)
    vv_mms.plot_convergence(q4, q9, "mms_convergence_l2.png", "L2", "Convergencia en norma $L^2$ (MMS)")
    _estilo_proyeccion()
    _destino.update(clave="mms_h1", etiquetar=_etiquetar_series)
    vv_mms.plot_convergence(q4, q9, "mms_convergence_h1.png", "H1", "Convergencia en seminorma $H^1$ (MMS)")

    c4, c9 = _cook()
    _estilo_proyeccion()
    _destino.update(clave="cook", etiquetar=_etiquetar_series)
    vv_cook.plot_convergence(c4, c9, "cook_convergence.png")

    # Figura CR.2: el guion de la tesis, con su propio estilo (Times New Roman) y su comprobación
    # de cifras contra la Tabla 3.10 de final4.
    import generar_figuras_formulacion as gff
    plt.rcdefaults()
    gff.configurar_estilo()
    plt.rcParams["svg.fonttype"] = "path"
    d = gff.reunir_datos()
    gff.comprobar_veredicto(d, gff.leer_veredicto(os.path.join(RAIZ, "tesis", "capitulos_final4", "04_resultados.tex")))
    filas = gff.margenes(d)
    _destino.update(clave="margen_cr2", etiquetar=_etiquetar_margen)
    gff.fig_margen_criterios(REVISION, filas, "svg")
    etiquetas = [f for f, _ in filas]
    _destino.update(clave=None, etiquetar=None)

    faltan = [k for k in ("mms_l2", "mms_h1", "cook", "margen_cr2") if k not in _capturas]
    if faltan:
        raise SystemExit(f"No se capturaron: {faltan}")
    for k, s in _capturas.items():
        i = s.find("<svg")
        _capturas[k] = _prefijar_ids(s[i:], k)
    os.makedirs(os.path.dirname(SALIDA_JS), exist_ok=True)
    with open(SALIDA_JS, "w", encoding="utf-8") as f:
        f.write("/* Generado por herramientas/figuras_documento.py: las gráficas de la tesis (final4), en SVG.\n"
                "   No editar a mano. */\n")
        f.write("window.EDUFEM_FIGDOC = ")
        json.dump(_capturas, f, ensure_ascii=False)
        f.write(";\nwindow.EDUFEM_FIGDOC_MARGEN = ")
        json.dump(etiquetas, f, ensure_ascii=False)
        f.write(";\n")
    for k, s in _capturas.items():
        print(f"  [OK] {k}: {len(s) // 1024} KB")
    print("  ->", os.path.relpath(SALIDA_JS, RAIZ))


if __name__ == "__main__":
    main()
