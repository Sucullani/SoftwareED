# -*- coding: utf-8 -*-
"""grabar_video_pptx.py — el video de la defensa hecho por PowerPoint (video_v2).

Toma la versión narrada del PowerPoint (construir_pptx.py --narrada: cada diapositiva avanza sola
y lleva la voz de sus pasos) y la exporta con el propio PowerPoint (Presentation.CreateVideo, por
COM): transiciones, animaciones, bucles y videos tal como los reproduce PowerPoint. Después le
agrega, sin volver a codificar la imagen, los subtítulos (pista seleccionable, desde la línea de
tiempo que dejó el constructor) y un capítulo por bloque, y escribe el .srt y el guion aparte.

    python herramientas/grabar_video_pptx.py [--pptx=../Defensa_EduFEM_final4_narrada.pptx]
                                             [--alto=1080] [--fps=30] [--calidad=90]

Requiere PowerPoint (Windows) y ffmpeg. Salida en ../video/: Defensa_EduFEM_final4_v2.mp4, .srt y
guion_video_final4_v2.md.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FINAL = AQUI.parent
DEST = FINAL / "video"
NOMBRE = "Defensa_EduFEM_final4_v2"


def abrir_powerpoint():
    """PowerPoint por COM, con la caché de win32com fuera del entorno virtual del repositorio."""
    import win32com
    gen = AQUI / "_trabajo" / "gen_py"
    gen.mkdir(parents=True, exist_ok=True)
    win32com.__gen_path__ = str(gen)
    sys.modules["win32com.gen_py"].__path__ = [str(gen)]
    from win32com.client import gencache
    return gencache.EnsureDispatch("PowerPoint.Application")


def exportar(pptx: Path, destino: Path, alto: int, fps: int, calidad: int) -> float:
    app = abrir_powerpoint()
    pres = None
    t0 = time.time()
    try:
        pres = app.Presentations.Open(str(pptx), True, False, False)
        pres.CreateVideo(str(destino), True, 5, alto, fps, calidad)
        while pres.CreateVideoStatus in (1, 2):      # en proceso / en cola
            time.sleep(3)
        if pres.CreateVideoStatus != 3:
            raise RuntimeError(f"CreateVideo terminó con estado {pres.CreateVideoStatus}")
    finally:
        if pres is not None:
            pres.Close()
        app.Quit()
    return time.time() - t0


def hms(s: float, sep: str = ",") -> str:
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s_, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s_:02d}{sep}{ms:03d}"


def duracion(mp4: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def fines_de_silencio(archivo: Path, minimo: float) -> list[tuple[float, float]]:
    """(inicio, fin) de cada silencio del audio (ffmpeg silencedetect, −40 dB)."""
    r = subprocess.run(["ffmpeg", "-i", str(archivo), "-af", f"silencedetect=n=-40dB:d={minimo}", "-f", "null", "-"],
                       capture_output=True, text=True)
    ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    fin = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(ini, fin))


def calibrar(linea: dict, crudo: Path, voces: Path) -> list[float]:
    """Corrimiento de cada lámina en el video exportado respecto de la línea de tiempo prevista.

    Un video en bucle cuyo ciclo es más largo que la lámina la retiene un poco (los separadores):
    lo previsto se va atrasando. Se mide con el audio: la voz de cada lámina arranca en su
    t0 + transición + el silencio inicial de su pista; se busca ese arranque en el video."""
    arranques = [f for _, f in fines_de_silencio(crudo, 0.25)]
    corr, previo = [], 0.0
    for L in linea["laminas"]:
        sil = fines_de_silencio(voces / f"{L['id']}.mp3", 0.05)
        lead = sil[0][1] if sil and sil[0][0] <= 0.01 else 0.0
        pred = L["t0"] + L["retraso"] + lead
        cand = [t for t in arranques if pred + previo - 0.8 <= t <= pred + previo + 8]
        previo = (cand[0] - pred) if cand else previo
        corr.append(previo)
    return corr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pptx", default=str(FINAL / "Defensa_EduFEM_final4_narrada.pptx"))
    ap.add_argument("--alto", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--calidad", type=int, default=90)
    ap.add_argument("--sin-exportar", action="store_true", help="usa el video crudo ya exportado")
    ap.add_argument("--crf", type=int, default=24, help="calidad de la recodificación con x264")
    a = ap.parse_args()
    pptx = Path(a.pptx).resolve()
    linea = json.loads(pptx.with_suffix(".linea.json").read_text(encoding="utf-8"))
    trabajo = AQUI / "_trabajo" / "video_pptx"
    trabajo.mkdir(parents=True, exist_ok=True)
    crudo = trabajo / "crudo.mp4"
    if not a.sin_exportar:
        seg = exportar(pptx, crudo, a.alto, a.fps, a.calidad)
        print(f"  exportado por PowerPoint en {seg / 60:.1f} min")
    total = duracion(crudo)
    ult = linea["laminas"][-1]
    previsto = ult["t0"] + ult["retraso"] + ult["dur"]
    print(f"  duración {total / 60:.2f} min (prevista {previsto / 60:.2f} min)")
    corr = calibrar(linea, crudo, AQUI / "_trabajo" / "pptx" / "narrada")
    print(f"  corrimiento medido con la voz: hasta {max(corr):+.2f} s (última lámina {corr[-1]:+.2f} s)")
    for L, c in zip(linea["laminas"], corr):
        L["t0"] = round(L["t0"] + c, 3)
    # subtítulos y guion desde la línea de tiempo del constructor, ya calibrada
    srt, guion, n = [], ["# Guion del video de la defensa, versión PowerPoint (final4)", "",
                         "Marcas de tiempo del video exportado por PowerPoint desde la versión narrada.", "",
                         "| Tiempo | Lámina | Paso | Texto |", "|---|---|---|---|"], 0
    for L in linea["laminas"]:
        for k, p in enumerate(L["pasos"]):
            t_paso = L["t0"] + L["retraso"] + p["t"]
            guion.append(f"| {hms(t_paso, ',')[3:8]} | {L['titulo']} | {k + 1} | {p['texto']} |")
            for c in p.get("subtitulos", []):
                n += 1
                srt += [str(n), f"{hms(t_paso + c['ini'])} --> {hms(t_paso + c['fin'])}", c["texto"], ""]
    DEST.mkdir(exist_ok=True)
    (DEST / f"{NOMBRE}.srt").write_text("\n".join(srt), encoding="utf-8")
    (DEST / "guion_video_final4_v2.md").write_text("\n".join(guion) + "\n", encoding="utf-8")
    # capítulos: un bloque del Taller 6 por capítulo
    meta = [";FFMETADATA1", "title=Defensa de tesis — EduFEM (versión PowerPoint)"]
    caps = []
    for L in linea["laminas"]:
        if not caps or caps[-1][1] != L["bloque_nombre"]:
            caps.append([L["t0"], L["bloque_nombre"]])
    for j, (t, nombre) in enumerate(caps):
        fin = caps[j + 1][0] if j + 1 < len(caps) else total
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(t * 1000)}", f"END={int(fin * 1000)}", f"title={nombre}"]
    (trabajo / "capitulos.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
    salida = DEST / f"{NOMBRE}.mp4"
    # PowerPoint codifica con poca compresión (unos 1,5 Mbit/s): se vuelve a codificar con x264,
    # que a igual calidad visual deja el archivo en una fracción
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(crudo), "-i", str(DEST / f"{NOMBRE}.srt"),
                        "-i", str(trabajo / "capitulos.txt"), "-map", "0:v", "-map", "0:a?", "-map", "1:s",
                        "-map_metadata", "2", "-map_chapters", "2",
                        "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "64k", "-ac", "1", "-c:s", "mov_text",
                        "-metadata:s:s:0", "language=spa", "-movflags", "+faststart", str(salida)])
    if r.returncode != 0:
        raise SystemExit("ffmpeg no pudo montar el video")
    print(f"[OK] {salida} · {salida.stat().st_size / 1e6:.1f} MB · {len(caps)} capítulos · {n} subtítulos")


if __name__ == "__main__":
    main()
