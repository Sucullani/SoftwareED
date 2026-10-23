"""Crea una copia del .pptx con la narración embebida y avance automático (PowerPoint COM).

Uso: python narrar_pptx.py Defensa_EduFEM.pptx carpeta_audio salida_narrada.pptx [pausa_s]

Cada lámina recibe su MP3 (sNN.mp3) como objeto de audio oculto que se reproduce al entrar,
y la transición avanza sola cuando termina la pista más la pausa. Sirve para proyectar la
defensa sin operador y como fuente alternativa del video (Archivo > Exportar > Crear video).
"""
import os
import sys

import win32com.client
from mutagen.mp3 import MP3

src, audio_dir, dst = [os.path.abspath(a) for a in sys.argv[1:4]]
pausa = float(sys.argv[4]) if len(sys.argv) > 4 else 0.8

app = win32com.client.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(src, ReadOnly=False, Untitled=False, WithWindow=False)
n = pres.Slides.Count
for i in range(1, n + 1):
    mp3 = os.path.join(audio_dir, f"s{i:02d}.mp3")
    if not os.path.isfile(mp3):
        print("sin audio para la lámina", i)
        continue
    slide = pres.Slides(i)
    shp = slide.Shapes.AddMediaObject2(mp3, False, True, 20, 20, 40, 40)
    ps = shp.AnimationSettings.PlaySettings
    ps.PlayOnEntry = True
    ps.HideWhileNotPlaying = True
    ps.PauseAnimation = False
    tr = slide.SlideShowTransition
    tr.AdvanceOnClick = True
    tr.AdvanceOnTime = True
    tr.AdvanceTime = MP3(mp3).info.length + pausa
pres.SaveCopyAs(dst)
pres.Close()
try:
    if app.Presentations.Count == 0:
        app.Quit()
except Exception:
    pass
print("narrada:", dst, round(os.path.getsize(dst) / 1e6, 1), "MB")
