# -*- coding: utf-8 -*-
"""
sintetizar_voz.py -- Narración de la defensa: una pista MP3 por paso de cada lámina.

Lee herramientas/narracion_final.json (texto con ortografía normal), lo convierte para la
voz (cifras en palabras, «Q4» -> «Q cuatro», «σx» -> «sigma equis», 10⁻¹³ -> «diez a la
menos trece»), lo sintetiza con edge-tts (voz neuronal de Microsoft; necesita internet) y
escribe:

  assets/audio/<lamina>__<paso>.mp3      una pista por paso
  assets/data/narracion.js               texto, pista, duración y subtítulos por frase
                                         (lo usan la vista del orador, el modo narrado y la
                                         captura del video)

Las pistas ya sintetizadas se reutilizan si no cambió el texto, la voz ni la velocidad.

Uso (desde la raíz del repositorio):
    .venv\\Scripts\\python.exe tesis\\presentacion\\final\\herramientas\\sintetizar_voz.py [--forzar] [--rate=+8%]
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys

import edge_tts
from mutagen.mp3 import MP3

AQUI = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(AQUI)
NARR = os.path.join(AQUI, "narracion_final.json")
AUDIO = os.path.join(FINAL, "assets", "audio")
SALIDA_JS = os.path.join(FINAL, "assets", "data", "narracion.js")

FORZAR = "--forzar" in sys.argv
RATE_ARG = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--rate=")), None)


# ---------------------------------------------------------------- números en palabras
_U = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
      "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho",
      "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro",
      "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_D = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_C = {2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos",
      7: "setecientos", 8: "ochocientos", 9: "novecientos"}


def _menor_mil(n: int) -> str:
    if n < 30:
        return _U[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _D[d] + ("" if u == 0 else " y " + _U[u])
    if n == 100:
        return "cien"
    c, r = divmod(n, 100)
    pre = "ciento" if c == 1 else _C[c]
    return pre + ("" if r == 0 else " " + _menor_mil(r))


def _apocope(s: str) -> str:
    if s.endswith("veintiuno"):
        return s[:-len("veintiuno")] + "veintiún"
    if s.endswith("uno"):
        return s[:-3] + "un"
    return s


def entero(n: int) -> str:
    if n < 1000:
        return _menor_mil(n)
    if n < 1_000_000:
        m, r = divmod(n, 1000)
        pre = "mil" if m == 1 else _apocope(_menor_mil(m)) + " mil"
        return pre + ("" if r == 0 else " " + _menor_mil(r))
    mm, r = divmod(n, 1_000_000)
    pre = "un millón" if mm == 1 else _apocope(entero(mm)) + " millones"
    return pre + ("" if r == 0 else " " + entero(r))


def decimal(ent: str, dec: str | None) -> str:
    s = entero(int(ent))
    if dec is None:
        return s
    if len(dec) > 4:  # decimales largos: cifra por cifra (2,03460 -> dos coma cero tres cuatro seis cero)
        return s + " coma " + " ".join(_U[int(c)] for c in dec)
    ceros = len(dec) - len(dec.lstrip("0"))
    resto = dec.lstrip("0")
    partes = ["cero"] * ceros + ([entero(int(resto))] if resto else [])
    return s + " coma " + " ".join(partes)


_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")

REEMPLAZOS = [
    ("«", ""), ("»", ""), ("—", ", "), ("·", ","), ("…", "."),
    ("Štembera", "Shtémbera"), ("Füssl", "Fússel"), ("Python", "Páiton"), ("von Mises", "fon Mises"),
    ("ED-Elas2D", "E D Elas dos D"), ("VisualFEA", "Visual F E A"), (" LU ", " L U "),
    ("SAP2000", "SAP dos mil"), ("σx", "sigma equis"), ("σy", "sigma ye"), ("τxy", "tau equis ye"),
    ("σ", "sigma"), ("τ", "tau"), ("ν", "nu"), ("ξ", "xi"), ("η", "eta"), ("ε", "épsilon"),
    ("±", " más o menos "), ("×", " por "), ("≈", " aproximadamente "), ("→", ", "),
    ("≤", " menor o igual que "), ("<", " menor que "), (">", " mayor que "), (" = ", " igual a "),
]


def para_voz(texto: str) -> str:
    t = texto
    for a, b in REEMPLAZOS:
        t = t.replace(a, b)
    # versiones: 1.0.0 -> uno punto cero punto cero
    t = re.sub(r"\b(\d+)\.(\d+)\.(\d+)\b", lambda m: " punto ".join(entero(int(x)) for x in m.groups()), t)
    # potencias de diez: 10⁻¹³
    t = re.sub(r"10([⁻]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: "diez a la " + ("menos " if "⁻" in m.group(1) else "") + entero(int(m.group(1).translate(_SUP).replace("-", ""))), t)
    # letra pegada a cifra y cifra pegada a letra: Q4 -> Q 4, 2i -> 2 i
    t = re.sub(r"(?<=[A-Za-zÁÉÍÓÚáéíóúñÑ])(?=\d)", " ", t)
    t = re.sub(r"(?<=\d)(?=[A-Za-zÁÉÍÓÚáéíóúñÑ])", " ", t)
    # porcentajes
    t = t.replace("%", " por ciento")
    # signo menos tipográfico delante de una cifra
    t = re.sub(r"−\s?(?=\d)", "menos ", t)

    # números: 33 282 · 0,0414 · 23,96 · 2026
    def num(m):
        ent = m.group(1).replace(" ", "").replace(" ", "")
        dec = m.group(2)
        s = decimal(ent, dec)
        # apócope delante de un sustantivo: «21 elementos» -> «veintiún elementos»
        sig = t[m.end():m.end() + 2]
        if dec is None and len(sig) == 2 and sig[0] == " " and sig[1].islower():
            s = _apocope(s)
        return s
    t = re.sub(r"(?<![\d,])(\d{1,3}(?:[  ]\d{3})+|\d+)(?:,(\d+))?(?![\d])", num, t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ---------------------------------------------------------------- subtítulos por frase
def frases(texto: str, largo_max: int = 118):
    """Parte el texto original en frases; las largas, en la coma más cercana al medio."""
    trozos = re.split(r"(?<=[.!?:])\s+(?=[A-ZÁÉÍÓÚÑ¿«0-9])", texto.strip())
    out = []
    for f in trozos:
        cola = [f]
        while cola:
            s = cola.pop(0)
            if len(s) <= largo_max:
                out.append(s)
                continue
            medio = len(s) // 2
            cortes = [m.start() for m in re.finditer(r"[,;] ", s)]
            if not cortes:
                out.append(s)
                continue
            c = min(cortes, key=lambda i: abs(i - medio))
            cola[:0] = [s[:c + 1].strip(), s[c + 1:].strip()]
    return [x for x in out if x]


def cues(texto: str, eventos: list, dur: float):
    """Asigna a cada frase del texto original el tiempo de sus palabras en la voz."""
    fr = frases(texto)
    if not eventos:
        return [{"ini": 0.0, "fin": dur, "texto": texto}]
    pesos = [max(1, len(para_voz(f).split())) for f in fr]
    total = sum(pesos)
    n = len(eventos)
    res, acum = [], 0
    for f, p in zip(fr, pesos):
        i0 = min(n - 1, round(acum / total * n))
        acum += p
        i1 = min(n - 1, max(i0, round(acum / total * n) - 1))
        ini = eventos[i0][0]
        fin = eventos[i1][0] + eventos[i1][1]
        res.append({"ini": round(ini, 3), "fin": round(fin + 0.25, 3), "texto": f})
    res[0]["ini"] = 0.0
    res[-1]["fin"] = round(max(res[-1]["fin"], dur), 3)
    return res


# ---------------------------------------------------------------- síntesis
async def sintetizar(texto_voz, voz, rate, mp3):
    eventos = []
    with open(mp3 + ".tmp", "wb") as fh:
        com = edge_tts.Communicate(texto_voz, voz, rate=rate, boundary="WordBoundary")
        async for ch in com.stream():
            if ch["type"] == "audio":
                fh.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                eventos.append((ch["offset"] / 1e7, ch["duration"] / 1e7))
    os.replace(mp3 + ".tmp", mp3)
    return eventos


async def principal():
    with open(NARR, encoding="utf-8") as fh:
        N = json.load(fh)
    voz = N.get("voz", "es-BO-MarceloNeural")
    rate = RATE_ARG or N.get("rate", "+0%")
    pausa = float(N.get("pausa_s", 0.6))
    os.makedirs(AUDIO, exist_ok=True)
    cache_p = os.path.join(AUDIO, "_indice.json")
    cache = {}
    if os.path.isfile(cache_p) and not FORZAR:
        with open(cache_p, encoding="utf-8") as fh:
            cache = json.load(fh)
    sem = asyncio.Semaphore(4)
    resultado = {"voz": voz, "rate": rate, "pausa_s": pausa, "laminas": {}}
    tareas = []

    async def uno(lid, k, texto):
        voz_txt = para_voz(texto)
        firma = hashlib.sha1(f"{voz}|{rate}|{voz_txt}".encode("utf-8")).hexdigest()[:16]
        nombre = f"{lid}__{k}.mp3"
        mp3 = os.path.join(AUDIO, nombre)
        c = cache.get(nombre)
        if c and c.get("firma") == firma and os.path.isfile(mp3):
            eventos = c["eventos"]
        else:
            async with sem:
                for intento in range(5):
                    try:
                        eventos = await sintetizar(voz_txt, voz, rate, mp3)
                        break
                    except Exception as exc:  # red inestable: reintento
                        if intento == 4:
                            raise
                        await asyncio.sleep(2 + 3 * intento)
            cache[nombre] = {"firma": firma, "eventos": eventos}
            print(f"  voz {nombre}")
        dur = MP3(mp3).info.length
        return lid, k, {"paso": k, "texto": texto, "voz": voz_txt, "audio": nombre, "dur": round(dur, 3),
                        "subtitulos": cues(texto, eventos, dur)}

    for lam in N["laminas"]:
        for k, texto in enumerate(lam["pasos"]):
            tareas.append(uno(lam["id"], k, texto))
    for lid, k, d in await asyncio.gather(*tareas):
        resultado["laminas"].setdefault(lid, {"pasos": []})["pasos"].append(d)
    for v in resultado["laminas"].values():
        v["pasos"].sort(key=lambda d: d["paso"])
    resultado["orden"] = [l["id"] for l in N["laminas"]]
    with open(cache_p, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False)
    with open(SALIDA_JS, "w", encoding="utf-8") as fh:
        fh.write("/* Generado por herramientas/sintetizar_voz.py -- NO editar a mano. */\n")
        fh.write("window.EDUFEM_NARRACION = ")
        fh.write(json.dumps(resultado, ensure_ascii=False, separators=(",", ":")))
        fh.write(";\n")
    total = sum(d["dur"] for v in resultado["laminas"].values() for d in v["pasos"])
    n = sum(len(v["pasos"]) for v in resultado["laminas"].values())
    palabras = sum(len(d["texto"].split()) for v in resultado["laminas"].values() for d in v["pasos"])
    print(f"\n{n} pistas · {palabras} palabras · voz {total/60:.1f} min (+ pausas {n*pausa/60:.1f} min)")
    print(f"[OK] {SALIDA_JS}")


if __name__ == "__main__":
    if "--probar" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8")
        for s in ["El error es de 0,0414 % y la flecha 2,03460 cm.", "Q4 y Q9, M7, E3, SAP2000, 1,7 por 10⁻¹³.",
                  "33 282 grados de libertad en 2026; 21 elementos; 2i y 2i más 1.", "EduFEM 1.0.0 · σx = −845,06 y τxy."]:
            print(s, "\n  ->", para_voz(s))
        sys.exit(0)
    asyncio.run(principal())
