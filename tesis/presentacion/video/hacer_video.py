"""Monta el video narrado de la defensa a partir de los PNG de las láminas y del guion.

Uso:
    python hacer_video.py narracion.json carpeta_frames carpeta_trabajo salida.mp4 [--rate +8%] [--forzar]

Etapas (cada una se salta si su salida ya existe, salvo --forzar):
  1. Voz: una pista MP3 por lámina con edge-tts (voz neuronal de Microsoft, es-BO por defecto).
  2. Medición: duración real de cada pista con mutagen.
  3. Pistas WAV con la pausa de silencio al final (ffmpeg apad) y lista de concatenación.
  4. Video: concat de imágenes con la duración de su pista + pista de audio única (ffmpeg, H.264 + AAC).
  5. Guion con marcas de tiempo (guion_video.md) junto al MP4.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys

import edge_tts
from mutagen.mp3 import MP3

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
FLAGS = [a for a in sys.argv[1:] if a.startswith("--")]
if len(ARGS) < 4:
    print(__doc__)
    sys.exit(2)
NARR, FRAMES, WORK, OUT = [os.path.abspath(a) for a in ARGS[:4]]
FORZAR = "--forzar" in FLAGS
RATE_OVERRIDE = next((f.split("=", 1)[1] for f in FLAGS if f.startswith("--rate=")), None)

FFMPEG = shutil.which("ffmpeg")
if not FFMPEG:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

with open(NARR, encoding="utf-8") as fh:
    G = json.load(fh)
VOZ = G.get("voz", "es-BO-MarceloNeural")
RATE = RATE_OVERRIDE or G.get("rate", "+0%")
PAUSA = float(G.get("pausa_s", 0.8))
LAMINAS = G["laminas"]

AUDIO = os.path.join(WORK, "audio")
os.makedirs(AUDIO, exist_ok=True)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(f"fallo: {' '.join(cmd[:3])} …")
    return r


# ---------------------------------------------------------------- 1. voz
def firma(texto):
    return hashlib.sha1(f"{VOZ}|{RATE}|{texto}".encode("utf-8")).hexdigest()[:12]


async def sintetizar(lam, sem):
    mp3 = os.path.join(AUDIO, f"s{lam['n']:02d}.mp3")
    sig = os.path.join(AUDIO, f"s{lam['n']:02d}.sig")
    f = firma(lam["texto"])
    if not FORZAR and os.path.isfile(mp3) and os.path.isfile(sig) and open(sig).read().strip() == f:
        return
    async with sem:
        for intento in range(4):
            try:
                com = edge_tts.Communicate(lam["texto"], VOZ, rate=RATE)
                await com.save(mp3)
                break
            except Exception as exc:  # red inestable: reintento
                if intento == 3:
                    raise
                await asyncio.sleep(2 + 3 * intento)
    with open(sig, "w") as fh:
        fh.write(f)
    print(f"  voz {lam['n']:02d} ok")


async def voz_todas():
    sem = asyncio.Semaphore(3)
    await asyncio.gather(*(sintetizar(l, sem) for l in LAMINAS))


print(f"Voz {VOZ}, rate {RATE}, {len(LAMINAS)} láminas")
asyncio.run(voz_todas())

# ---------------------------------------------------------------- 2. duraciones
dur = {}
for lam in LAMINAS:
    mp3 = os.path.join(AUDIO, f"s{lam['n']:02d}.mp3")
    dur[lam["n"]] = MP3(mp3).info.length
total_voz = sum(dur.values())
print(f"voz total: {total_voz/60:.1f} min  (+ pausas {len(LAMINAS)*PAUSA:.0f} s)")

# ---------------------------------------------------------------- 3. wav con pausa
wavs = []
for lam in LAMINAS:
    n = lam["n"]
    mp3 = os.path.join(AUDIO, f"s{n:02d}.mp3")
    wav = os.path.join(AUDIO, f"s{n:02d}.wav")
    if FORZAR or not os.path.isfile(wav) or os.path.getmtime(wav) < os.path.getmtime(mp3):
        run([FFMPEG, "-y", "-loglevel", "error", "-i", mp3, "-af", f"apad=pad_dur={PAUSA}",
             "-ar", "44100", "-ac", "2", wav])
    wavs.append(wav)

# duración exacta de cada wav (cabecera PCM: bytes / (44100*2*2))
segs = []
for lam, wav in zip(LAMINAS, wavs):
    nbytes = os.path.getsize(wav) - 44
    segs.append(max(0.5, nbytes / (44100 * 2 * 2)))
total = sum(segs)
print(f"video total: {total/60:.2f} min")

lista_v = os.path.join(WORK, "slides.txt")
lista_a = os.path.join(WORK, "audio.txt")
with open(lista_v, "w", encoding="utf-8") as fv, open(lista_a, "w", encoding="utf-8") as fa:
    for lam, wav, d in zip(LAMINAS, wavs, segs):
        png = os.path.join(FRAMES, f"s{lam['n']:02d}.png").replace("\\", "/")
        if not os.path.isfile(png):
            raise SystemExit(f"falta el frame {png}")
        fv.write(f"file '{png}'\nduration {d:.3f}\n")
        fa.write(f"file '{wav.replace(chr(92), '/')}'\n")
    fv.write(f"file '{png}'\n")  # el concat demuxer ignora la última duración si no se repite el archivo

# ---------------------------------------------------------------- 4. video
fade_out = max(0.0, total - 1.5)
vf = f"scale=1920:1080:flags=lanczos,format=yuv420p,fade=t=in:st=0:d=0.8,fade=t=out:st={fade_out:.2f}:d=1.5"
af = f"afade=t=in:st=0:d=0.5,afade=t=out:st={fade_out:.2f}:d=1.5"
run([FFMPEG, "-y", "-loglevel", "error", "-stats",
     "-f", "concat", "-safe", "0", "-i", lista_v,
     "-f", "concat", "-safe", "0", "-i", lista_a,
     "-vf", vf, "-af", af,
     "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "21", "-r", "25",
     "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", OUT])
print("video:", OUT, round(os.path.getsize(OUT) / 1e6, 1), "MB")

# ---------------------------------------------------------------- 5. guion con tiempos
def mmss(t):
    m, s = divmod(int(round(t)), 60)
    return f"{m:02d}:{s:02d}"

md = os.path.join(os.path.dirname(OUT), "guion_video.md")
t = 0.0
lines = ["# Guion del video de defensa — EduFEM", "",
         f"Voz: {VOZ} (Microsoft Edge TTS, rate {RATE}) · duración {mmss(total)} · {len(LAMINAS)} láminas.", "",
         "| Lámina | Inicio | Duración | Título |", "|---:|---:|---:|---|"]
for lam, d in zip(LAMINAS, segs):
    lines.append(f"| {lam['n']} | {mmss(t)} | {int(round(d))} s | {lam['titulo']} |")
    t += d
lines.append("")
t = 0.0
for lam, d in zip(LAMINAS, segs):
    lines += [f"## {lam['n']}. {lam['titulo']}  ·  {mmss(t)}", "", lam["texto"], ""]
    t += d
with open(md, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("guion:", md)
