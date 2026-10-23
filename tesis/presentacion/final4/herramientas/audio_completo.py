"""audio_completo.py -- la narración entera de la defensa en un solo MP3, para escucharla y ensayar.

Une las pistas de assets/audio/ en el orden de la presentación, con la misma pausa entre pasos
que usa el modo narrado (pausa_s de assets/data/narracion.js), y escribe al lado un índice con
la marca de tiempo de cada lámina.

    .venv\\Scripts\\python.exe tesis\\presentacion\\final4\\herramientas\\audio_completo.py

Salida: tesis/presentacion/final4/audio/Defensa_EduFEM_final4_narracion.mp3 e indice_audio.md
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.dirname(AQUI)
AUDIO = os.path.join(FINAL, "assets", "audio")
SALIDA = os.path.join(FINAL, "audio")


def ffmpeg():
    return shutil.which("ffmpeg") or "ffmpeg"


def main():
    with open(os.path.join(FINAL, "assets", "data", "narracion.js"), encoding="utf-8") as fh:
        js = fh.read()
    datos = json.loads(js[js.index("{"):js.rindex("}") + 1])
    pausa = float(datos.get("pausa_s", 1.0))
    with open(os.path.join(AQUI, "narracion_final4.json"), encoding="utf-8") as fh:
        orden = json.load(fh)
    laminas = orden["laminas"] if isinstance(orden, dict) and "laminas" in orden else orden
    ids = [L["id"] for L in laminas] if isinstance(laminas, list) else list(laminas)
    os.makedirs(SALIDA, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="audio_defensa_")
    silencio = os.path.join(tmp, "silencio.mp3")
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", f"{pausa:.3f}", "-c:a", "libmp3lame", "-b:a", "48k", silencio], check=True)
    lista, indice, t = [], [], 0.0
    for n, lid in enumerate(ids, 1):
        pasos = datos["laminas"][lid]["pasos"]
        indice.append((t, n, lid))
        for p in pasos:
            ruta = os.path.join(AUDIO, p["audio"]) if not os.path.isabs(p["audio"]) else p["audio"]
            if not os.path.isfile(ruta):
                ruta = os.path.join(FINAL, p["audio"])
            lista.append(ruta)
            lista.append(silencio)
            t += float(p["dur"]) + pausa
    lst = os.path.join(tmp, "lista.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        for r in lista:
            fh.write("file '" + r.replace("\\", "/").replace("'", r"'\''") + "'\n")
    mp3 = os.path.join(SALIDA, "Defensa_EduFEM_final4_narracion.mp3")
    subprocess.run([ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:a", "libmp3lame", "-b:a", "64k", "-ac", "1",
                    "-metadata", "title=Defensa EduFEM (final4) - narración",
                    "-metadata", "artist=Hedy Yhassmany Oyola Sucullani", mp3], check=True)
    # el título de cada lámina, del atributo data-titulo de su archivo en laminas/
    titulos = {}
    carpeta = os.path.join(FINAL, "laminas")
    for nombre in os.listdir(carpeta):
        if nombre.endswith(".html") and not nombre.startswith("_"):
            with open(os.path.join(carpeta, nombre), encoding="utf-8") as fh:
                m = re.search(r'<section[^>]*\bid="([^"]+)"[^>]*\bdata-titulo="([^"]+)"', fh.read())
            if m:
                titulos[m.group(1)] = m.group(2)
    with open(os.path.join(SALIDA, "indice_audio.md"), "w", encoding="utf-8") as fh:
        fh.write("# Narración de la defensa — índice\n\n")
        fh.write(f"`Defensa_EduFEM_final4_narracion.mp3`: {t / 60:.1f} min, {len(lista) // 2} pasos, "
                 f"pausa de {pausa:g} s entre pasos.\n\n| Minuto | N.º | Lámina |\n|---|---|---|\n")
        for t0, n, lid in indice:
            fh.write(f"| {int(t0 // 60):02d}:{int(t0 % 60):02d} | {n} | {titulos.get(lid, lid)} |\n")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"[OK] {mp3}  ({t / 60:.1f} min, {os.path.getsize(mp3) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
