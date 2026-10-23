# -*- coding: utf-8 -*-
"""
montar_video.py -- Une el video mudo capturado con la narración, los subtítulos y los capítulos.

Entrada (de capturar_video.mjs):  <trabajo>/video_mudo.mp4 y <trabajo>/segmentos.json
Pistas de voz:                    tesis/presentacion/final/assets/audio/*.mp3
Salida:
  tesis/presentacion/video/Defensa_EduFEM_final.mp4   H.264 + AAC + subtítulos (pista seleccionable)
                                                      + capítulos por bloque del Taller 6
  tesis/presentacion/video/Defensa_EduFEM_final.srt   los mismos subtítulos, aparte
  tesis/presentacion/video/guion_video_final.md       guion con la marca de tiempo de cada lámina

Cada paso dura exactamente lo que duró en la captura: su pista de voz se completa con
silencio hasta esa duración, así la voz y la imagen no se desfasan nunca.

Uso:  .venv\\Scripts\\python.exe tesis\\presentacion\\final\\herramientas\\montar_video.py [--trabajo=<carpeta>]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(AQUI)
AUDIO = os.path.join(FINAL, "assets", "audio")
DEST = os.path.abspath(os.path.join(FINAL, "..", "video"))
TRABAJO = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--trabajo=")), os.path.join(AQUI, "_trabajo"))
NOMBRE = "Defensa_EduFEM_final"
SR = 48000
BLOQUES = {"intro": "01 · Introducción", "teoria": "02 · Base teórica", "diseno": "03 · Diseño y desarrollo del modelo",
           "resultados": "04 · Presentación de resultados", "analisis": "05 · Análisis de resultados",
           "conclusiones": "06 · Conclusiones y recomendaciones"}


def ffmpeg():
    return "ffmpeg"


def pcm_de(mp3: str) -> bytes:
    r = subprocess.run([ffmpeg(), "-v", "error", "-i", mp3, "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"],
                       capture_output=True, check=True)
    return r.stdout


def srt_t(s: float) -> str:
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    sg, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sg:02d},{ms:03d}"


def mmss(s: float) -> str:
    s = int(round(s))
    return f"{s // 60:02d}:{s % 60:02d}"


def unir_partes(dirs):
    """Varias partes capturadas en paralelo -> un solo video mudo y una lista de segmentos."""
    if len(dirs) == 1:
        with open(os.path.join(dirs[0], "segmentos.json"), encoding="utf-8") as fh:
            return json.load(fh), os.path.join(dirs[0], "video_mudo.mp4"), dirs[0]
    salida = os.path.join(os.path.dirname(dirs[0]), "completo")
    os.makedirs(salida, exist_ok=True)
    segs, t, man0 = [], 0.0, None
    lista = os.path.join(salida, "partes.txt")
    with open(lista, "w", encoding="utf-8") as fl:
        for d in dirs:
            with open(os.path.join(d, "segmentos.json"), encoding="utf-8") as fh:
                m = json.load(fh)
            man0 = man0 or m
            fps = m["fps"]
            for s in m["segmentos"]:
                s = dict(s)
                s["t0"] = round(t + s["t0"], 4)
                segs.append(s)
            # duración real de la parte: número exacto de cuadros / fps
            t += sum(round(s["dur"] * fps) for s in m["segmentos"]) / fps
            fl.write(f"file '{os.path.join(d, 'video_mudo.mp4').replace(os.sep, '/')}'\n")
    mudo = os.path.join(salida, "video_mudo.mp4")
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", mudo], check=True)
    man = dict(man0)
    man["segmentos"] = segs
    with open(os.path.join(salida, "segmentos.json"), "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)
    print(f"  {len(dirs)} partes unidas")
    return man, mudo, salida


def main():
    global TRABAJO
    # rutas absolutas: el demuxer concat de ffmpeg resuelve las relativas contra la lista
    dirs = [os.path.abspath(d) for d in TRABAJO.split(",") if d]
    man, mudo, TRABAJO = unir_partes(dirs)
    segs = man["segmentos"]
    total = segs[-1]["t0"] + segs[-1]["dur"]
    print(f"{len(segs)} pasos · {total / 60:.2f} min")

    # ---- pista de voz: cada paso rellenado con silencio hasta su duración capturada
    pcm_path = os.path.join(TRABAJO, "voz.pcm")
    with open(pcm_path, "wb") as out:
        escritos = 0
        for s in segs:
            objetivo = int(round((s["t0"] + s["dur"]) * SR)) * 4  # bytes acumulados al final del paso
            datos = pcm_de(os.path.join(AUDIO, s["audio"])) if s.get("audio") else b""
            falta = objetivo - escritos
            datos = datos[: max(0, falta)]
            out.write(datos)
            escritos += len(datos)
            if objetivo > escritos:
                out.write(b"\x00" * (objetivo - escritos))
                escritos = objetivo
    print("  voz lista")

    # ---- subtítulos
    srt = os.path.join(TRABAJO, f"{NOMBRE}.srt")
    n = 0
    with open(srt, "w", encoding="utf-8") as fh:
        for s in segs:
            for c in s.get("subtitulos") or []:
                ini = s["t0"] + c["ini"]
                fin = min(s["t0"] + min(c["fin"], s["dur"]), s["t0"] + s["dur"])
                if fin - ini < 0.3:
                    continue
                n += 1
                fh.write(f"{n}\n{srt_t(ini)} --> {srt_t(fin)}\n{c['texto']}\n\n")
    print(f"  {n} subtítulos")

    # ---- capítulos (bloques del Taller 6) y metadatos
    meta = os.path.join(TRABAJO, "capitulos.txt")
    caps = [("Carátula", 0.0)]
    visto = set()
    for s in segs:
        b = s.get("bloque")
        if b in BLOQUES and b not in visto:
            visto.add(b)
            caps.append((BLOQUES[b], s["t0"]))
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write(";FFMETADATA1\ntitle=Defensa de tesis — EduFEM\nartist=Hedy Yhassmany Oyola Sucullani\n"
                 "comment=Universidad Autónoma Tomás Frías · Carrera de Ingeniería Civil · 2026\n")
        for k, (titulo, ini) in enumerate(caps):
            fin = caps[k + 1][1] if k + 1 < len(caps) else total
            fh.write(f"\n[CHAPTER]\nTIMEBASE=1/1000\nSTART={int(ini * 1000)}\nEND={int(fin * 1000)}\ntitle={titulo}\n")

    # ---- unión
    os.makedirs(DEST, exist_ok=True)
    mp4 = os.path.join(DEST, f"{NOMBRE}.mp4")
    af = f"afade=t=in:st=0:d=0.3,afade=t=out:st={max(0.0, total - 1.5):.2f}:d=1.5"
    cmd = [ffmpeg(), "-y", "-v", "error", "-stats",
           "-i", mudo,
           "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", pcm_path,
           "-i", srt, "-i", meta,
           "-map", "0:v", "-map", "1:a", "-map", "2:s", "-map_metadata", "3", "-map_chapters", "3",
           "-c:v", "copy", "-af", af, "-c:a", "aac", "-ac", "1", "-b:a", "64k",
           "-c:s", "mov_text", "-metadata:s:s:0", "language=spa", "-metadata:s:a:0", "language=spa",
           "-movflags", "+faststart", mp4]
    subprocess.run(cmd, check=True)
    os.remove(pcm_path)  # ~12 MB por minuto de audio sin comprimir: ya no hace falta
    with open(srt, encoding="utf-8") as a, open(os.path.join(DEST, f"{NOMBRE}.srt"), "w", encoding="utf-8") as b:
        b.write(a.read())

    # ---- guion con tiempos
    md = os.path.join(DEST, "guion_video_final.md")
    lineas = ["# Guion del video de defensa — EduFEM (tesis final)", "",
              f"Duración {mmss(total)} · {len(segs)} pasos · voz {json.dumps(man.get('voz', ''))[1:-1] or 'es-BO-MarceloNeural'} · "
              "la imagen es la presentación interactiva grabada cuadro a cuadro.", "",
              "| Inicio | Lámina | Paso | Texto |", "|---:|---|---:|---|"]
    for s in segs:
        lineas.append(f"| {mmss(s['t0'])} | {s['titulo']} | {s['paso'] + 1} | {s['texto']} |")
    lineas += ["", "## Capítulos", ""] + [f"- {mmss(ini)} — {t}" for t, ini in caps]
    with open(md, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")
    print(f"[OK] {mp4}  ({os.path.getsize(mp4) / 1e6:.1f} MB, {total / 60:.2f} min)")
    print(f"[OK] {md}")


if __name__ == "__main__":
    main()
