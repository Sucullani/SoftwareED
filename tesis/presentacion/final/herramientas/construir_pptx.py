"""construir_pptx.py — arma la presentación en PowerPoint a partir de la escena que extrae
extraer_pptx.mjs de la versión 2 (estilo PowerPoint) de la defensa.

Cada paso de la presentación HTML se vuelve un clic: las formas que aparecen en ese paso
entran con «Desvanecer», las que se van salen igual. Todo lo que es texto, caja, tabla o
imagen es una forma nativa y editable (Calibri); los gráficos SVG, los lienzos del MEF y
las fórmulas son imágenes al doble de resolución. Lleva además la transición de fundido,
los hipervínculos (botones de bloque, filas de la matriz de consistencia, criterios del
veredicto, «Volver»), las notas del orador con la narración de cada paso, los dos videos
del software y un índice oculto.

    python herramientas/construir_pptx.py [--trabajo=_trabajo/pptx] [--salida=../Defensa_EduFEM_v2.pptx]
                                          [--pasos-separados]   # una diapositiva por paso, sin animación (revisión)
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE, MSO_PATTERN_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

AQUI = Path(__file__).resolve().parent
FINAL = AQUI.parent
PX = 6350                      # EMU por px de diseño: 1920 px = 13,333 in
NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def emu(v: float) -> Emu:
    return Emu(int(round(v * PX)))


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h.lstrip("#").upper())


def poner_alfa(elemento, alfa: float):
    """Agrega <a:alpha> a un <a:srgbClr> (transparencia de relleno, línea o texto)."""
    if alfa >= 0.995:
        return
    for c in elemento.iter(qn("a:srgbClr")):
        for viejo in c.findall(qn("a:alpha")):
            c.remove(viejo)
        etree.SubElement(c, qn("a:alpha")).set("val", str(int(round(max(0.0, alfa) * 100000))))


# ----------------------------------------------------------------------------- escena
def clave(it: dict) -> str:
    d = {k: v for k, v in it.items() if k not in ("orden", "entrada", "z", "rid")}
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def unir_pasos(pasos: list[dict]) -> tuple[list[dict], int]:
    """Une los pasos en una lista de formas con el paso en que aparecen y el último en que siguen.

    Una forma idéntica en pasos consecutivos es la misma forma; si desaparece y vuelve, es otra.
    El orden de apilado respeta el orden del DOM de cada paso (fusión estable)."""
    ocurrencias: list[dict] = []
    activas: dict[str, dict] = {}
    global_orden: list[dict] = []
    n = len(pasos)
    for p, paso in enumerate(pasos):
        vistas = set()
        previa = None
        for it in paso["items"]:
            k = clave(it)
            if k in vistas:          # duplicado exacto dentro del mismo paso
                continue
            vistas.add(k)
            oc = activas.get(k)
            if oc is None or oc["hasta"] != p - 1:
                oc = {"it": it, "desde": p, "hasta": p, "k": k}
                ocurrencias.append(oc)
                activas[k] = oc
                # insertar justo después de la forma que la precede en este paso
                if previa is not None:
                    global_orden.insert(global_orden.index(previa) + 1, oc)
                elif p > 0:
                    global_orden.insert(0, oc)
                else:
                    global_orden.append(oc)
            else:
                oc["hasta"] = p
            previa = oc
    # enlaces arriba de todo, y lo que tenga z-index positivo por encima del resto
    def llave(oc):
        it = oc["it"]
        return (2 if it["t"] == "enlace" else (1 if it.get("z", 0) > 0 else 0), it.get("z", 0), global_orden.index(oc))
    return sorted(global_orden, key=llave), n


# ----------------------------------------------------------------------------- formas
def forma_caja(slide, it: dict):
    x, y, w, h = it["x"], it["y"], it["w"], it["h"]
    lados = it["lados"]
    radios = it["radios"]
    alfa = it.get("alfa", 1)
    uniforme = all(lados) and len({(l["w"], l["c"]["hex"], l["estilo"]) for l in lados}) == 1
    bw = lados[0]["w"] if uniforme else 0
    # el borde de PowerPoint va centrado en el contorno; el de CSS, por dentro
    if uniforme:
        x, y, w, h = x + bw / 2, y + bw / 2, max(0.5, w - bw), max(0.5, h - bw)
    rmax = max(radios) if radios else 0
    rmin = min(radios) if radios else 0
    tipo = MSO_SHAPE.RECTANGLE
    girar = 0
    voltearV = False
    if rmax > 0.6:
        if abs(w - h) < 1 and rmin >= min(w, h) / 2 - 1:
            tipo = MSO_SHAPE.OVAL
        elif rmax - rmin <= 10 or rmin > 0.6:
            tipo = MSO_SHAPE.ROUNDED_RECTANGLE
        else:
            tl, tr, br, bl = radios
            if tl > 0.6 and tr > 0.6 and br < 0.6 and bl < 0.6:
                tipo = MSO_SHAPE.ROUND_2_SAME_RECTANGLE
            elif bl > 0.6 and br > 0.6 and tl < 0.6 and tr < 0.6:
                tipo, voltearV = MSO_SHAPE.ROUND_2_SAME_RECTANGLE, True
            else:
                tipo = MSO_SHAPE.ROUNDED_RECTANGLE
    shp = slide.shapes.add_shape(tipo, emu(x), emu(y), emu(w), emu(h))
    shp.shadow.inherit = False
    if tipo == MSO_SHAPE.ROUNDED_RECTANGLE:
        r = max(0.0, rmax - (bw / 2 if uniforme else 0))
        shp.adjustments[0] = min(0.5, r / max(1e-6, min(w, h)))
    elif tipo == MSO_SHAPE.ROUND_2_SAME_RECTANGLE:
        shp.adjustments[0] = min(0.5, rmax / max(1e-6, min(w, h)))
        shp.adjustments[1] = 0.0
        if voltearV:
            shp._element.spPr.get_or_add_xfrm().set("flipV", "1")
    if it.get("giro"):
        shp.rotation = it["giro"]
    # relleno
    fondo, grad = it.get("fondo"), it.get("grad")
    if grad and grad.get("rep"):
        p = [q for q in grad["paradas"] if q["c"]["a"] > 0]
        if len(p) >= 2:
            shp.fill.patterned()
            shp.fill.pattern = MSO_PATTERN_TYPE.WIDE_UPWARD_DIAGONAL
            shp.fill.fore_color.rgb = rgb(p[-1]["c"]["hex"])
            shp.fill.back_color.rgb = rgb(p[0]["c"]["hex"])
        elif fondo:
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(fondo["hex"])
        else:
            shp.fill.background()
    elif grad and len(grad["paradas"]) >= 2:
        paradas = grad["paradas"]
        # franja dura con el primer color transparente (resaltado tipo «mark»): solo la parte coloreada
        if paradas[0]["c"]["a"] == 0 and paradas[1]["pos"] is not None and len(paradas) == 2:
            f = paradas[1]["pos"] / 100.0
            shp.top = emu(y + h * f); shp.height = emu(h * (1 - f))
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(paradas[1]["c"]["hex"])
            poner_alfa(shp.fill._xPr, paradas[1]["c"]["a"] * alfa)
        else:
            shp.fill.gradient()
            shp.fill.gradient_angle = (grad["ang"] - 90) % 360
            # todas las paradas (la barra jet tiene muchas), con las posiciones de CSS
            largo = w if grad["ang"] % 180 == 90 else h
            pos = [None if q["pos"] is None else (q["pos"] / largo * 100 if q.get("px") else q["pos"]) for q in paradas]
            if pos[0] is None:
                pos[0] = 0.0
            if pos[-1] is None:
                pos[-1] = 100.0
            k = 0
            while k < len(pos):
                if pos[k] is None:
                    j = k
                    while pos[j] is None:
                        j += 1
                    for m in range(k, j):
                        pos[m] = pos[k - 1] + (pos[j] - pos[k - 1]) * (m - k + 1) / (j - k + 1)
                    k = j
                k += 1
            gs = shp.fill._xPr.find(qn("a:gradFill")).find(qn("a:gsLst"))
            for viejo in gs.findall(qn("a:gs")):
                gs.remove(viejo)
            for q, p in zip(paradas, pos):
                g_el = etree.SubElement(gs, qn("a:gs"))
                g_el.set("pos", str(int(round(max(0.0, min(100.0, p)) * 1000))))
                etree.SubElement(g_el, qn("a:srgbClr")).set("val", q["c"]["hex"].lstrip("#").upper())
                poner_alfa(g_el, q["c"]["a"] * alfa)
    elif fondo:
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(fondo["hex"])
        poner_alfa(shp.fill._xPr, fondo["a"] * alfa)
    else:
        shp.fill.background()
    # borde
    if uniforme:
        l = lados[0]
        shp.line.color.rgb = rgb(l["c"]["hex"])
        shp.line.width = Pt(max(0.25, l["w"] * 0.5))
        if l["estilo"] in ("dashed", "dotted"):
            shp.line.dash_style = MSO_LINE_DASH_STYLE.DASH if l["estilo"] == "dashed" else MSO_LINE_DASH_STYLE.ROUND_DOT
        poner_alfa(shp.line._ln, l["c"]["a"] * alfa)
    else:
        shp.line.fill.background()
    if it.get("sombra"):
        sombra_exterior(shp, it["sombra"], alfa)
    formas = [shp]
    if not uniforme:
        # bordes de un solo lado: barras o trazos por dentro de la caja
        X, Y, W, H = it["x"], it["y"], it["w"], it["h"]
        for k, l in enumerate(lados):
            if not l:
                continue
            bw = l["w"]
            if l["estilo"] in ("dashed", "dotted"):
                if k == 0: x1, y1, x2, y2 = X, Y + bw / 2, X + W, Y + bw / 2
                elif k == 1: x1, y1, x2, y2 = X + W - bw / 2, Y, X + W - bw / 2, Y + H
                elif k == 2: x1, y1, x2, y2 = X, Y + H - bw / 2, X + W, Y + H - bw / 2
                else: x1, y1, x2, y2 = X + bw / 2, Y, X + bw / 2, Y + H
                ln = slide.shapes.add_connector(1, emu(x1), emu(y1), emu(x2), emu(y2))
                ln.line.color.rgb = rgb(l["c"]["hex"])
                ln.line.width = Pt(max(0.25, bw * 0.5))
                ln.line.dash_style = MSO_LINE_DASH_STYLE.DASH if l["estilo"] == "dashed" else MSO_LINE_DASH_STYLE.ROUND_DOT
                poner_alfa(ln.line._ln, l["c"]["a"] * alfa)
                formas.append(ln)
                continue
            if k == 0: rx, ry, rw, rh = X, Y, W, bw
            elif k == 1: rx, ry, rw, rh = X + W - bw, Y, bw, H
            elif k == 2: rx, ry, rw, rh = X, Y + H - bw, W, bw
            else: rx, ry, rw, rh = X, Y, bw, H
            b = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(rx), emu(ry), emu(rw), emu(rh))
            b.shadow.inherit = False
            b.fill.solid(); b.fill.fore_color.rgb = rgb(l["c"]["hex"])
            poner_alfa(b.fill._xPr, l["c"]["a"] * alfa)
            b.line.fill.background()
            formas.append(b)
    return formas


def sombra_exterior(shp, s: dict, alfa: float = 1.0):
    """box-shadow difuminada de CSS -> <a:outerShdw> (distancia, dirección y difuminado en EMU)."""
    import math
    spPr = shp._element.spPr
    ef = spPr.find(qn("a:effectLst"))
    if ef is None:
        ef = etree.SubElement(spPr, qn("a:effectLst"))
        ln = spPr.find(qn("a:ln"))
        if ln is not None:
            ln.addnext(ef)
    for viejo in list(ef):
        ef.remove(viejo)
    dist = math.hypot(s["dx"], s["dy"])
    ang = (math.degrees(math.atan2(s["dy"], s["dx"])) % 360) if dist else 90.0
    sh = etree.SubElement(ef, qn("a:outerShdw"))
    sh.set("blurRad", str(int(s["blur"] * PX)))
    sh.set("dist", str(int(dist * PX)))
    sh.set("dir", str(int(ang * 60000)))
    sh.set("algn", "ctr")
    sh.set("rotWithShape", "0")
    c = etree.SubElement(sh, qn("a:srgbClr"))
    c.set("val", s["c"]["hex"].lstrip("#").upper())
    etree.SubElement(c, qn("a:alpha")).set("val", str(int(round(s["c"]["a"] * alfa * 100000))))


ALINEAR = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}


def forma_texto(slide, it: dict):
    L, s = it["interlineado"], it["tamBase"]
    # calibración Chrome ↔ PowerPoint (interlineado exacto, Calibri): la primera línea de
    # PowerPoint cae 0,24·L − 0,325·s px más abajo que la del navegador
    dy = 0.24 * L - 0.325 * s
    tb = slide.shapes.add_textbox(emu(it["x"]), emu(it["y"] - dy), emu(it["w"]), emu(it["h"]))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = ALINEAR.get(it["al"], PP_ALIGN.LEFT)
    pPr = p._p.get_or_add_pPr()
    ln = etree.SubElement(pPr, qn("a:lnSpc"))
    etree.SubElement(ln, qn("a:spcPts")).set("val", str(int(round(L / 2 * 100))))
    for s_ in ("a:spcBef", "a:spcAft"):
        e = etree.SubElement(pPr, qn(s_))
        etree.SubElement(e, qn("a:spcPts")).set("val", "0")
    alfa = it.get("alfa", 1)
    for k, linea in enumerate(it["lineas"]):
        for j, run in enumerate(linea):
            txt = run["txt"]
            if j == len(linea) - 1:
                txt = txt.rstrip()
            if not txt:
                continue
            r = p.add_run()
            r.text = txt
            e = run["e"]
            f = r.font
            f.name = e["f"]
            f.size = Pt(e["tam"] / 2)
            f.bold = bool(e["n"])
            f.italic = bool(e["i"])
            f.color.rgb = rgb(e["c"])
            rPr = r._r.get_or_add_rPr()
            if e.get("may"):
                rPr.set("cap", "all")
            if e.get("esp"):
                rPr.set("spc", str(int(round(e["esp"] * 50))))
            if e.get("desp") == "sub":
                rPr.set("baseline", "-25000")
            elif e.get("desp") == "sup":
                rPr.set("baseline", "30000")
            if e.get("sub"):
                rPr.set("u", "sng")
            poner_alfa(rPr, e.get("a", 1) * alfa)
    # los saltos van entre corridas: mover cada <a:br> a su lugar (python-pptx agrega las corridas al final)
    reordenar_saltos(p._p, it["lineas"])
    return [tb]


def reordenar_saltos(p_el, lineas):
    """Reconstruye el párrafo en orden: corridas de la línea 1, <a:br>, corridas de la línea 2…"""
    runs = p_el.findall(qn("a:r"))
    for br in p_el.findall(qn("a:br")):
        p_el.remove(br)
    for r in runs:
        p_el.remove(r)
    k = 0
    for i, linea in enumerate(lineas):
        if i > 0:
            p_el.append(etree.Element(qn("a:br")))
        n = sum(1 for j, run in enumerate(linea) if (run["txt"].rstrip() if j == len(linea) - 1 else run["txt"]))
        for _ in range(n):
            p_el.append(runs[k]); k += 1
    end = p_el.find(qn("a:endParaRPr"))
    if end is not None:
        p_el.remove(end); p_el.append(end)


def forma_imagen(slide, it: dict, raiz: Path):
    ruta = Path(it["ruta"])
    if not ruta.exists():
        print("  falta la imagen", ruta, file=sys.stderr)
        return []
    pic = slide.shapes.add_picture(str(ruta), emu(it["x"]), emu(it["y"]), emu(it["w"]), emu(it["h"]))
    rc = it.get("recorte") or {}
    pic.crop_left, pic.crop_right = rc.get("l", 0), rc.get("r", 0)
    pic.crop_top, pic.crop_bottom = rc.get("t", 0), rc.get("b", 0)
    if it.get("radio", 0) > 0.6:
        # esquinas redondeadas: geometría roundRect con su ajuste (python-pptx no lo expone en imágenes)
        geo = pic._element.spPr.find(qn("a:prstGeom"))
        geo.set("prst", "roundRect")
        av = geo.find(qn("a:avLst"))
        if av is None:
            av = etree.SubElement(geo, qn("a:avLst"))
        for g in list(av):
            av.remove(g)
        gd = etree.SubElement(av, qn("a:gd"))
        gd.set("name", "adj")
        gd.set("fmla", f"val {int(min(0.5, it['radio'] / min(it['w'], it['h'])) * 100000)}")
    if it.get("alfa", 1) < 0.995:
        blip = pic._element.find(".//" + qn("a:blip"))
        etree.SubElement(blip, qn("a:alphaModFix")).set("amt", str(int(it["alfa"] * 100000)))
    return [pic]


def forma_raster(slide, it: dict, img_dir: Path):
    ruta = img_dir / it["archivo"]
    if it.get("video"):
        mp4 = FINAL / it["video"]
        if mp4.exists():
            mov = slide.shapes.add_movie(str(mp4), emu(it["x"]), emu(it["y"]), emu(it["w"]), emu(it["h"]),
                                         poster_frame_image=str(ruta), mime_type="video/mp4")
            return [mov]
    pic = slide.shapes.add_picture(str(ruta), emu(it["x"]), emu(it["y"]), emu(it["w"]), emu(it["h"]))
    return [pic]


def hipervinculo(shape, accion: str | None = None, destino=None):
    if destino is not None:
        shape.click_action.target_slide = destino
        return
    cNvPr = shape._element.find(".//" + qn("p:cNvPr"))
    h = etree.SubElement(cNvPr, qn("a:hlinkClick"))
    h.set(qn("r:id"), "")
    h.set("action", accion)


def forma_enlace(slide, it: dict, destinos: dict):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(it["x"]), emu(it["y"]), emu(it["w"]), emu(it["h"]))
    shp.shadow.inherit = False
    # relleno 100 % transparente: invisible pero sensible al clic (sin relleno no lo sería)
    shp.fill.solid(); shp.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    poner_alfa(shp.fill._xPr, 0.0)
    shp.line.fill.background()
    shp.name = f"Enlace a {it['ir']}"
    ir = it["ir"]
    if ir == "__siguiente":
        hipervinculo(shp, "ppaction://hlinkshowjump?jump=nextslide")
    elif ir in destinos:
        hipervinculo(shp, destino=destinos[ir])
    else:
        return []
    return [shp]


# ----------------------------------------------------------------------------- animaciones
class Tiempos:
    """Arma el <p:timing> de una diapositiva: entradas automáticas, clics y videos."""

    def __init__(self):
        self.id = 2
        self.bld: set[tuple[int, int]] = set()

    def nid(self) -> int:
        self.id += 1
        return self.id

    def efecto(self, spid: int, tipo: str, nodo: str, retraso: int = 0, dur: int = 350, grp: int = 0, texto=True) -> str:
        if texto:
            self.bld.add((spid, grp))
        a = self.nid()
        if tipo == "entr":
            b, c = self.nid(), self.nid()
            return (f'<p:par><p:cTn id="{a}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="{grp}" nodeType="{nodo}">'
                    f'<p:stCondLst><p:cond delay="{retraso}"/></p:stCondLst><p:childTnLst>'
                    f'<p:set><p:cBhvr><p:cTn id="{b}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
                    f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
                    f'<p:to><p:strVal val="visible"/></p:to></p:set>'
                    f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{c}" dur="{dur}"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
                    f'</p:childTnLst></p:cTn></p:par>')
        b, c = self.nid(), self.nid()
        return (f'<p:par><p:cTn id="{a}" presetID="10" presetClass="exit" presetSubtype="0" fill="hold" grpId="{grp}" nodeType="{nodo}">'
                f'<p:stCondLst><p:cond delay="{retraso}"/></p:stCondLst><p:childTnLst>'
                f'<p:animEffect transition="out" filter="fade"><p:cBhvr><p:cTn id="{b}" dur="{dur}"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>'
                f'<p:set><p:cBhvr><p:cTn id="{c}" dur="1" fill="hold"><p:stCondLst><p:cond delay="{max(0, dur - 1)}"/></p:stCondLst></p:cTn>'
                f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
                f'<p:to><p:strVal val="hidden"/></p:to></p:set>'
                f'</p:childTnLst></p:cTn></p:par>')

    def reproducir(self, spid: int, nodo: str, dur_ms: int) -> str:
        a, b = self.nid(), self.nid()
        return (f'<p:par><p:cTn id="{a}" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="{nodo}">'
                f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                f'<p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="{b}" dur="{dur_ms}" fill="hold"/>'
                f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:cmd></p:childTnLst></p:cTn></p:par>')

    def xml(self, auto: list[str], clics: list[list[str]], videos: list[int]) -> str:
        cuerpo = ""
        if auto:
            a, b = self.nid(), self.nid()
            cuerpo += (f'<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
                       f'<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
                       f'<p:par><p:cTn id="{b}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                       + "".join(auto) + '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        for efectos in clics:
            if not efectos:
                efectos = []
            a, b = self.nid(), self.nid()
            cuerpo += (f'<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
                       f'<p:par><p:cTn id="{b}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                       + "".join(efectos) + '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        medios = ""
        for spid in videos:
            c = self.nid()
            medios += (f'<p:video><p:cMediaNode vol="80000"><p:cTn id="{c}" repeatCount="indefinite" fill="hold" display="0">'
                       f'<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
                       f'<p:endCondLst><p:cond evt="onStopAudio" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:endCondLst></p:cTn>'
                       f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cMediaNode></p:video>')
        secuencia = ""
        if cuerpo:
            secuencia = (f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{cuerpo}</p:childTnLst></p:cTn>'
                         f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
                         f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>')
        if not secuencia and not medios:
            return ""
        bld = "".join(f'<p:bldP spid="{s}" grpId="{g}" animBg="1"/>' for s, g in sorted(self.bld))
        return (f'<p:timing xmlns:p="{NS_P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
                f'{secuencia}{medios}</p:childTnLst></p:cTn></p:par></p:tnLst>'
                + (f'<p:bldLst>{bld}</p:bldLst>' if bld else "") + '</p:timing>')


def poner_tiempos(slide, xml: str):
    sld = slide._element
    for t in sld.findall(qn("p:timing")):
        sld.remove(t)
    if not xml:
        return
    el = etree.fromstring(xml)
    ext = sld.find(qn("p:extLst"))
    if ext is not None:
        ext.addprevious(el)
    else:
        sld.append(el)


def poner_transicion(slide, velocidad="med"):
    sld = slide._element
    for t in sld.findall(qn("p:transition")):
        sld.remove(t)
    tr = etree.fromstring(f'<p:transition xmlns:p="{NS_P}" spd="{velocidad}"><p:fade/></p:transition>')
    antes = sld.find(qn("p:timing"))
    if antes is None:
        antes = sld.find(qn("p:extLst"))
    if antes is not None:
        antes.addprevious(tr)
    else:
        sld.append(tr)


# ----------------------------------------------------------------------------- armado
def es_forma_con_texto(shape) -> bool:
    return shape._element.tag == qn("p:sp")


def notas(lamina: dict, con_cambio: list[bool] | None = None) -> str:
    """Guion de la lámina, un párrafo por paso, rotulado con el clic de PowerPoint que lo muestra.

    con_cambio[k] dice si el paso k+1 cambia algo en pantalla (si no, no consume clic)."""
    pasos = lamina.get("narracion") or []
    if not pasos:
        return ""
    if len(pasos) == 1:
        return pasos[0]
    partes, clic = [], 0
    for k, t in enumerate(pasos):
        if k == 0:
            rot = "Al entrar"
        elif con_cambio is None or (k - 1 < len(con_cambio) and con_cambio[k - 1]):
            clic += 1
            rot = f"Clic {clic}"
        else:
            rot = f"Sigue con el clic {clic}" if clic else "Sigue al entrar"
        partes.append(f"[{rot}] {t}")
    return "\n\n".join(partes)


def boton_nativo(slide, x, y, w, h, texto, relleno, color_txt, accion=None, destino=None, tam=21):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, emu(x), emu(y), emu(w), emu(h))
    shp.shadow.inherit = False
    shp.adjustments[0] = 0.2
    shp.fill.solid(); shp.fill.fore_color.rgb = rgb(relleno)
    shp.line.fill.background()
    tf = shp.text_frame
    tf.margin_left = tf.margin_right = emu(10); tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = texto
    r.font.name = "Calibri"; r.font.size = Pt(tam / 2); r.font.bold = True; r.font.color.rgb = rgb(color_txt)
    hipervinculo(shp, accion, destino)
    return shp


def construir(escena: dict, img_dir: Path, salida: Path, separados: bool):
    prs = Presentation()
    prs.slide_width, prs.slide_height = emu(1920), emu(1080)
    blanco = prs.slide_layouts[6]
    laminas = escena["laminas"]
    # 1) crear todas las diapositivas primero (los hipervínculos necesitan el destino)
    diapos: dict[str, object] = {}
    plan = []
    for L in laminas:
        ocs, n = unir_pasos(L["pasos"])
        if separados:
            for p in range(n):
                s = prs.slides.add_slide(blanco)
                diapos.setdefault(L["id"], s)
                plan.append((L, s, [oc for oc in ocs if oc["desde"] <= p <= oc["hasta"]], p))
        else:
            s = prs.slides.add_slide(blanco)
            diapos[L["id"]] = s
            plan.append((L, s, ocs, None))
    indice = prs.slides.add_slide(blanco)
    destinos = dict(diapos)
    destinos["__indice"] = indice
    objetivos_de_enlace = {oc["it"]["ir"] for _, _, ocs, _ in plan for oc in ocs if oc["it"]["t"] == "enlace"}
    # 2) llenar cada diapositiva
    for L, s, ocs, p_sep in plan:
        fondo = L["pasos"][0].get("fondo")
        if fondo:
            s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(fondo["hex"])
        tiempos = Tiempos()
        n = len(L["pasos"])
        auto, clics, videos = [], [[] for _ in range(max(0, n - 1))], []
        entradas_auto = []
        for oc in ocs:
            it = oc["it"]
            t = it["t"]
            if t == "caja":
                formas = forma_caja(s, it)
            elif t == "texto":
                formas = forma_texto(s, it)
            elif t == "img":
                formas = forma_imagen(s, it, FINAL)
            elif t == "raster":
                formas = forma_raster(s, it, img_dir)
            elif t == "enlace":
                formas = forma_enlace(s, it, destinos)
            else:
                formas = []
            if separados or not formas:
                continue
            for f in formas:
                spid = f.shape_id
                es_texto = es_forma_con_texto(f)
                if it.get("video") and f._element.tag == qn("p:pic"):
                    videos.append(spid)
                grp = 0
                if oc["desde"] > 0:
                    clics[oc["desde"] - 1].append(("entr", spid, es_texto, grp)); grp = 1
                elif it.get("entrada") is not None and t != "enlace":
                    entradas_auto.append((it["entrada"], spid, es_texto)); grp = 1
                if oc["hasta"] < n - 1:
                    clics[oc["hasta"]].append(("exit", spid, es_texto, grp))
        if not separados:
            # entradas automáticas al llegar a la lámina, por orden de data-entrada
            orden_e = sorted({e for e, _, _ in entradas_auto})
            for e, spid, es_texto in entradas_auto:
                k = orden_e.index(e)
                auto.append(tiempos.efecto(spid, "entr", "withEffect", retraso=120 + 110 * k, dur=450, texto=es_texto))
            for spid in videos:
                auto.append(tiempos.reproducir(spid, "withEffect", 60000))
            efectos_clic = []
            for grupo in clics:
                xmls = []
                # primero se va lo que sale, después entra lo nuevo (como en la versión HTML)
                sal = [g for g in grupo if g[0] == "exit"]
                ent = [g for g in grupo if g[0] == "entr"]
                for j, (_, spid, es_texto, grp) in enumerate(sal):
                    xmls.append(tiempos.efecto(spid, "exit", "clickEffect" if j == 0 else "withEffect", 0, 200, grp, es_texto))
                for j, (_, spid, es_texto, grp) in enumerate(ent):
                    nodo = "clickEffect" if (j == 0 and not sal) else "withEffect"
                    xmls.append(tiempos.efecto(spid, "entr", nodo, 200 if sal else 0, 400, grp, es_texto))
                if not xmls:
                    # un paso sin cambios visibles igual consume un clic
                    pass
                efectos_clic.append(xmls)
            poner_tiempos(s, tiempos.xml(auto, [c for c in efectos_clic if c], videos))
            poner_transicion(s)
        # notas del orador: la narración de cada paso
        if p_sep is None:
            txt = notas(L, None if separados else [bool(c) for c in efectos_clic])
        else:
            txt = (L.get("narracion") or [])[p_sep] if p_sep < len(L.get("narracion") or []) else ""
        if txt:
            s.notes_slide.notes_text_frame.text = txt
        # «Volver» en las láminas a las que se llega por un enlace y en el respaldo
        if not separados and (L["id"] in objetivos_de_enlace or L["respaldo"]) and not L.get("sinPie"):
            boton_nativo(s, 1480, 22, 170, 40, "↩ Volver", "#E8741A", "#FFFFFF",
                         accion="ppaction://hlinkshowjump?jump=lastslideviewed")
        if L["respaldo"] and not separados:
            s._element.set("show", "0")
    # 3) índice (oculto): un botón por lámina
    armar_indice(indice, laminas, diapos)
    indice._element.set("show", "0")
    poner_transicion(indice)
    prs.save(salida)
    return len(prs.slides._sldIdLst)


def armar_indice(s, laminas, diapos):
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb("#FFFFFF")
    tb = s.shapes.add_textbox(emu(89), emu(60), emu(1500), emu(80))
    p = tb.text_frame.paragraphs[0]
    r = p.add_run(); r.text = "Índice de la defensa"
    r.font.name = "Calibri"; r.font.size = Pt(30); r.font.bold = True; r.font.color.rgb = rgb("#1B2A4A")
    regla = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, emu(89), emu(150), emu(116), emu(6))
    regla.fill.solid(); regla.fill.fore_color.rgb = rgb("#E8741A"); regla.line.fill.background()
    principales = [L for L in laminas if not L["respaldo"]]
    respaldo = [L for L in laminas if L["respaldo"]]
    filas = principales + respaldo
    cols, alto = 3, 27
    por_col = (len(filas) + cols - 1) // cols
    for k, L in enumerate(filas):
        c, f = divmod(k, por_col)
        x, y = 89 + c * 590, 190 + f * (alto + 3)
        n = principales.index(L) + 1 if L in principales else None
        etiqueta = f"{n:>2}. {L['titulo']}" if n else f"R. {L['titulo']}"
        shp = s.shapes.add_textbox(emu(x), emu(y), emu(570), emu(alto))
        tf = shp.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        run = tf.paragraphs[0].add_run(); run.text = etiqueta
        run.font.name = "Calibri"; run.font.size = Pt(10.5)
        run.font.color.rgb = rgb("#1F2937" if n else "#1F77B4")
        shp.click_action.target_slide = diapos[L["id"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trabajo", default=str(AQUI / "_trabajo" / "pptx"))
    ap.add_argument("--salida", default=str(FINAL / "Defensa_EduFEM_v2.pptx"))
    ap.add_argument("--pasos-separados", action="store_true")
    a = ap.parse_args()
    trabajo = Path(a.trabajo)
    escena = json.loads((trabajo / "escena.json").read_text(encoding="utf-8"))
    n = construir(escena, trabajo / "img", Path(a.salida), a.pasos_separados)
    print(f"[OK] {a.salida} · {n} diapositivas · {Path(a.salida).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
