# tools/ — scripts de build y generación de recursos

Utilidades que **no** forman parte de la aplicación: generan el icono, empaquetan el
ejecutable y renderizan los videos de los diálogos. Nada de `tools/` se importa desde el
código de EduFEM.

## Contenido

| Script / carpeta | Qué hace | Cómo se corre |
|---|---|---|
| [build_all.ps1](build_all.ps1) | Cadena completa de empaquetado: icono → `.exe` (PyInstaller, onefile) → instalador (Inno Setup). Entregable: `installer/Output/EduFEM-Setup.exe` | `powershell -ExecutionPolicy Bypass -File tools\build_all.ps1` |
| [make_icon.py](make_icon.py) | Genera `resources/icons/edufem.ico` (birrete + malla MEF). Solo Pillow, determinista | `python tools/make_icon.py` |
| [render_logo_concept_5.py](render_logo_concept_5.py) | Render del concepto de logo del que salió el icono. Escribe en `tools/logo_concepts/` (no versionado) | `python tools/render_logo_concept_5.py` |
| [render_q4q9_manim/](render_q4q9_manim/) | Escena Manim → `resources/videos/cantilever_q4_q9.webp` (diálogo *Tipo de Elemento*) | ver su [README](render_q4q9_manim/README.md) |
| [render_tp_dp_manim/](render_tp_dp_manim/) | Escena Manim → `resources/videos/tension_deformacion_plana.webp` (diálogo *Tipo de Análisis*) | ver su [README](render_tp_dp_manim/README.md) |

## Reglas

- **`make_icon.py` y `build_all.ps1` deben quedar hermanos en `tools/`**: el `.ps1` resuelve
  el `.py` por ruta relativa a `$PSScriptRoot`. Ver `docs/MAPA.md` §3.
- **Los nombres de las carpetas `render_*_manim/` aparecen en mensajes de la GUI** (cuando
  falta el `.webp`, el diálogo indica dónde regenerarlo). Renombrarlas obliga a actualizar
  esos strings.
- **`tools/**/media/` no se versiona**: son los intermedios de Manim (cientos de `.mp4`
  parciales), regenerables desde los `.py` de escena. Lo versionado es el `.webp` final en
  `resources/videos/`.
- **Las dependencias de estos scripts no están en `requirements.txt`**: `manim` y `ffmpeg`
  solo hacen falta para regenerar los videos, e Inno Setup solo para el instalador. La
  aplicación no los necesita.

## Pipeline de video (resumen)

Escena Manim (`.py`) → `manim -qh escena.py Clase` → `.mp4` →
`ffmpeg -vcodec libwebp -filter:v "fps=22,scale=900:600:flags=lanczos" -q:v 75 -loop 0 -an -vsync 0`
→ `.webp` animado en `resources/videos/`.

El reproductor de la app es `gui/widgets/webp_player.py` (solo Pillow, sin FFmpeg ni PyAV:
mantiene liviano el instalador y evita falsos positivos de antivirus).
