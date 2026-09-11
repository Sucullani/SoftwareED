# Presentación de defensa — EduFEM

| Archivo | Qué es |
|---|---|
| `Defensa_EduFEM.pptx` | Presentación editable (38 diapositivas, 16:9, Calibri + Cambria Math, notas del orador en todas) |
| `Defensa_EduFEM.pdf` | La misma presentación exportada a PDF desde PowerPoint |
| `guion.json` | Contenido de cada diapositiva; `build_deck.py` construye el `.pptx` a partir de él |
| `video/Defensa_EduFEM.mp4` | Defensa narrada completa (1080p, ~25 min), una lámina por bloque de narración |
| `video/guion_video.md` | Guion de la narración con la marca de tiempo de cada lámina |
| `video/narracion.json` | Texto que se narra en cada lámina, voz y velocidad (fuente del video) |
| `video/Defensa_EduFEM_narrada.pptx` | Copia del `.pptx` con la narración embebida y avance automático (se proyecta sola) |

## Regenerar la presentación

```
python tesis/presentacion/build_deck.py tesis/presentacion/guion.json tesis/presentacion/Defensa_EduFEM.pptx
python tesis/presentacion/exportar_pdf.py tesis/presentacion/Defensa_EduFEM.pptx tesis/presentacion/Defensa_EduFEM.pdf
python tesis/presentacion/exportar_png.py tesis/presentacion/Defensa_EduFEM.pptx <carpeta> 1920   # una imagen por lámina
```

Requiere `python-pptx`, `Pillow` y `pywin32` (los dos exportadores usan PowerPoint por COM).
Las figuras se toman de `tesis/figuras/` por nombre de archivo.

## Regenerar el video

```
python tesis/presentacion/video/hacer_video.py tesis/presentacion/video/narracion.json <frames_1920> <carpeta_trabajo> tesis/presentacion/video/Defensa_EduFEM.mp4
python tesis/presentacion/video/narrar_pptx.py tesis/presentacion/Defensa_EduFEM.pptx <carpeta_trabajo>/audio tesis/presentacion/video/Defensa_EduFEM_narrada.pptx
```

1. `exportar_png.py … 1920` produce los frames de cada lámina.
2. `hacer_video.py` sintetiza una pista por lámina con **edge-tts** (voces neuronales de
   Microsoft; necesita internet), mide su duración, añade la pausa entre láminas y monta el
   MP4 con **ffmpeg** (H.264 + AAC, fundido de entrada y salida). Escribe además
   `guion_video.md` con las marcas de tiempo. Las pistas ya sintetizadas se reutilizan si el
   texto, la voz y la velocidad no cambiaron; `--forzar` las regenera y `--rate=+5%` cambia
   la velocidad sin tocar el JSON.
3. `narrar_pptx.py` embebe esas mismas pistas en una copia del `.pptx` con transición
   automática, de modo que la presentación se proyecta sola con la narración.

Requiere `edge-tts`, `mutagen`, `pywin32` y un `ffmpeg` (el del PATH o el que trae
`imageio-ffmpeg`). Todo está instalado en el `.venv` del proyecto.

Para cambiar la voz basta editar `voz` en `narracion.json` (por ejemplo `es-BO-SofiaNeural`,
`es-ES-AlvaroNeural`, `es-MX-DaliaNeural`; `python -m edge_tts --list-voices` lista todas) y
volver a correr `hacer_video.py`.

## Estructura del guion de la presentación

Cada entrada de `diapositivas` declara un `layout` y los campos que ese layout usa:

| layout | campos | para qué |
|---|---|---|
| `portada` · `cierre` | `meta` (universidad, título, autor, fecha, repo) | carátula institucional y agradecimiento |
| `seccion` | `titulo`, `subtitulo` | separador de bloque; dibuja el hilo conductor (chips de los 6 bloques) |
| `bullets` | `bullets` (≤ 5), `remate` | viñetas; un `Prefijo:` al inicio se resalta en negrita |
| `dos_columnas` | `bullets` + `imagen`/`caption` (o `columna_derecha`, o `kpis`) | texto a la izquierda, figura a la derecha |
| `imagen` | `imagen`, `caption`, `remate` | figura grande |
| `tabla` | `tabla.cabeceras`, `tabla.filas` (≤ 6 col × 8 filas), `remate` | el tamaño de letra baja solo si no cabe |
| `kpi` | `kpis[{valor, etiqueta}]` (3–4) | tarjetas de cifra |
| `flujo` | `pasos[{etiqueta, sub}]` (3–8) | cadena de pasos (una o dos filas) |
| `comparacion` | `tarjetas[{titulo, lineas}]` (2) | Q4 vs Q9 y similares (colores de las curvas de la tesis) |
| `ecuaciones` | `ecuaciones[{nombre, texto}]` (2–4) | texto Unicode en Cambria Math, editable |
| `demo` | `imagen`, `bullets` (pasos) | guion de la demostración en vivo |

Campos comunes: `bloque` (rótulo del hilo conductor arriba a la derecha), `fuente` (sección
de la tesis, va al pie), `notas` (notas del orador), `remate` (barra de conclusión al pie).

## Decisiones de diseño

- Orden y tiempos del **Taller 6 de la UATF** (carátula → introducción → base teórica →
  diseño y desarrollo del modelo → presentación de resultados → análisis → conclusiones;
  40–45 min). El bloque «Diseño y desarrollo del modelo» incluye la demostración en vivo.
- Texto principal a **24 pt** (títulos 32 pt). El constructor solo baja el tamaño cuando el
  texto no cabe y lo avisa por consola; las tablas densas van a 18–20 pt y los pies,
  captions y etiquetas de chips son texto auxiliar (11–16 pt).
- Todas las cifras están copiadas de la tesis con su referencia (analítico, SAP2000,
  referencia 23,96) y verificadas contra los `.tex` al armar el guion.
- Paleta: azul marino (estructura), naranja (acentos y remates), Q4 en azul y Q9 en naranja,
  los mismos colores que las curvas de convergencia de la tesis.
- El video narra en primera persona, con tono académico; la voz por defecto es
  `es-BO-MarceloNeural` (español de Bolivia) a +8 % de velocidad para cerrar en ~25 min. Los
  números y símbolos van escritos en palabras dentro de `narracion.json` para que la voz los
  lea bien («norma L dos», «veintitrés coma noventa y seis»).
