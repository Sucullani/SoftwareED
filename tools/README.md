# tools/ — scripts de build y generación de recursos

Utilidades que **no** forman parte de la aplicación: generan el icono, empaquetan el
ejecutable y renderizan los videos de los diálogos. Nada de `tools/` se importa desde el
código de EduFEM.

## Contenido

| Script / carpeta | Qué hace | Cómo se corre |
|---|---|---|
| [build_all.ps1](build_all.ps1) | Cadena completa de empaquetado, en cuatro pasos: TeX embebido (si falta) → iconos e imágenes del asistente → `dist/EduFEM/` (PyInstaller, onedir) → instalador (Inno Setup). Entregable: `installer/Output/EduFEM-Setup.exe`. Opciones: `-RehacerTeX`; `-Portable` deja además `dist/EduFEM/` como carpeta autónoma (~57 MB duplicados, no es la vía de distribución) | `powershell -ExecutionPolicy Bypass -File tools\build_all.ps1` |
| [make_installer_images.py](make_installer_images.py) | Genera `installer/assets/wizard*.bmp`: el panel vertical y el sello de cabecera del asistente de Inno, en la serie de tamaños que Windows elige según el DPI. BMP de 24 bits, que es lo único que Inno lee | `python tools/make_installer_images.py` |
| [build_texlive.py](build_texlive.py) | Genera `vendor/texlive` (gitignored): TinyTeX-0 (TeX Live 2026, versión fijada) + `tlmgr install` de la lista fija de paquetes desde un snapshot fechado de tlnet + formato pdflatex con silabeo español + poda (Perl, Ghostscript, docs, OpenType, otros motores) + regeneración de `ls-R`. Valida compilando la Memoria Q4/Q9 y el Theory Hub reales antes y después de podar. Necesita internet una vez | `python tools/build_texlive.py` (`--force` rehace, `--validate-only` solo comprueba) |
| [make_icon.py](make_icon.py) | Genera `resources/icons/edufem.ico` (birrete + malla MEF) y `edufem_doc.ico` (el mismo emblema sobre una hoja: es el icono de los archivos `.edufem`). Solo Pillow, determinista | `python tools/make_icon.py` |
| [render_logo_concept_5.py](render_logo_concept_5.py) | Render del concepto de logo del que salió el icono. Escribe en `tools/logo_concepts/` (no versionado) | `python tools/render_logo_concept_5.py` |
| [render_q4q9_manim/](render_q4q9_manim/) | Escena Manim → `resources/videos/cantilever_q4_q9.webp` (diálogo *Tipo de Elemento*) | ver su [README](render_q4q9_manim/README.md) |
| [render_tp_dp_manim/](render_tp_dp_manim/) | Escena Manim → `resources/videos/tension_deformacion_plana.webp` (diálogo *Tipo de Análisis*) | ver su [README](render_tp_dp_manim/README.md) |

## Reglas

- **`make_icon.py`, `build_texlive.py` y `build_all.ps1` deben quedar hermanos en `tools/`**:
  el `.ps1` resuelve los `.py` por ruta relativa a `$PSScriptRoot`. Ver `docs/MAPA.md` §3.
- **`build_texlive.py` escribe en `vendor/texlive`** y ese nombre lo leen
  `education/components/latex_runtime.py` (`DEV_BUNDLE_RELPATH`) e `installer/EduFEM.iss`.
  Cambiar la lista `PACKAGES` obliga a rehacer el bundle (`--force`) y a que pase la
  validación integrada.
- **Al subir la versión** se toca `config/settings.py` (`APP_VERSION`, única fuente: la leen
  `build.spec` y el `.iss`) y el texto de `installer/dist_extra/LEEME.txt`, que la nombra en
  la cabecera y en el pie. Nada más. `python -m tests.test_distribucion` verifica que el
  `.iss` siga pudiendo leerla.
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
