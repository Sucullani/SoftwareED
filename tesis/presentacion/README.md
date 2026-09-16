# Presentación de defensa — EduFEM

| Archivo | Qué es |
|---|---|
| `Defensa_EduFEM.pptx` | Presentación editable (39 diapositivas, 16:9, Calibri + Cambria Math, notas del orador en todas) |
| `Defensa_EduFEM.pdf` | La misma presentación exportada a PDF desde PowerPoint |
| `guion.json` | Contenido de cada diapositiva; `build_deck.py` construye el `.pptx` a partir de él |
| `video/Defensa_EduFEM.mp4` | Defensa narrada completa (1080p, 30:54), una lámina por bloque de narración |
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
| `tabla` | `tabla.cabeceras`, `tabla.filas` (≤ 6 col × 8 filas), `tabla.destacar_col` / `destacar_fila`, `remate` | el tamaño de letra baja solo si no cabe; la columna o fila destacada va en naranja claro y negrita |
| `kpi` | `kpis[{valor, etiqueta}]` (3–6) | tarjetas de cifra; con más de cuatro pasa a dos filas de tres |
| `flujo` | `pasos[{etiqueta, sub}]` (3–8) | cadena de pasos (una o dos filas) |
| `comparacion` | `tarjetas[{titulo, lineas, color}]` (2 o 3) | Q4 vs Q9, hipótesis vs preguntas, recomendaciones por capítulo; `color` ∈ navy, accent, slate, q4, q9 |
| `ecuaciones` | `ecuaciones[{nombre, texto}]` (2–4) | texto Unicode en Cambria Math, editable |
| `demo` | `imagen`, `bullets` (pasos) | guion de la demostración en vivo |

Campos comunes: `bloque` (rótulo del hilo conductor, arriba a la izquierda), `subtitulo`
(aclaración bajo el título), `fuente` (sección de la tesis, va al pie), `notas` (notas del
orador), `remate` (barra de conclusión al pie). El `cierre` acepta además `chips` (tres
etiquetas con las ideas que quedan).

## Decisiones de diseño

- Orden y tiempos del **Taller 6 de la UATF** (carátula → introducción → base teórica →
  diseño y desarrollo del modelo → presentación de resultados → análisis → conclusiones;
  40–45 min). El bloque «Diseño y desarrollo del modelo» incluye la demostración en vivo.
- Texto principal a **24 pt** (títulos 32 pt). El constructor solo baja el tamaño cuando el
  texto no cabe y lo avisa por consola; las tablas densas van a 15–20 pt y los pies,
  captions y etiquetas de chips son texto auxiliar (11–16 pt).
- **Cabecera**: rótulo del bloque en versalita naranja (`01  INTRODUCCIÓN`), título en azul
  marino, acento naranja debajo y, a la derecha, los seis puntos del hilo conductor con el
  bloque actual resaltado. El avance también se ve en los chips del pie de cada separador.
- **Tarjetas** de superficie clara con borde fino: las de flujo llevan barra superior azul,
  las de cifra un acento naranja sobre el número, y las figuras van dentro de una tarjeta
  ajustada a su tamaño real, sin franjas muertas alrededor.
- La carátula lleva un **panel oscuro** a la derecha con el escudo, el logotipo y la marca; el
  cierre repite ese fondo con tres chips de remate. Los separadores de bloque llevan de fondo
  una **malla de cuadriláteros** dibujada con formas, el motivo de marca del proyecto.
- Todas las cifras están copiadas de la tesis con su referencia (analítico, SAP2000,
  referencia 23,96) y verificadas contra los `.tex` al armar el guion.
- Paleta: azul marino (estructura), naranja (acentos y remates), Q4 en azul y Q9 en naranja,
  los mismos colores que las curvas de convergencia de la tesis.
- El video narra en primera persona, con tono académico; la voz por defecto es
  `es-BO-MarceloNeural` (español de Bolivia) a +11 % de velocidad. Los números y símbolos van
  escritos en palabras dentro de `narracion.json` para que la voz los lea bien («norma L
  dos», «veintitrés coma noventa y seis»).

## Correspondencia con la tesis

El guion está sincronizado con el `.tex` al **2026-09-16** (auditoría por sesiones): objetivos
específicos reformulados, hipótesis condicional de tres cláusulas con sus criterios a priori
(§2.1.6), Tabla 1.1 como matriz de atributos, Tabla 2.1 con los atributos del artefacto, §3.6
—cobertura del canal, 7/7 y 9/9— como lámina propia, componentes secundarias y equilibrio en
Timoshenko, y recomendaciones en tres grupos por capítulo. Al cambiar una cifra en la tesis hay
que cambiarla también acá: el `guion.json` es una copia, no una referencia.

La figura de las tres fases que usa la lámina de cobertura es `fig_fases_lienzo_ancho.png`
—versión apaisada de la Figura 3.5—, que produce `tesis/figuras/generar_figuras.py` a partir de
las mismas capturas.
