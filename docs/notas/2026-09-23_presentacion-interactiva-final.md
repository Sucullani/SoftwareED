# Presentación interactiva y video de la tesis final

**Fecha**: 2026-09-23 · **Autor**: agente (Claude) · **Estado**: terminado; espera el ensayo del autor

## Qué se pedía

Rehacer las diapositivas y el video de la defensa para la **tesis final** (`main_final.tex`),
«dinámicos, interactivos, con botones» para ir a datos del software, con animaciones hechas con
la tecnología que el agente eligiera, con un acabado profesional. Las versiones v1 y v2
(PowerPoint) seguían los ejes anteriores de la tesis.

## Qué se hizo

Todo vive en `tesis/presentacion/final/` (ver su README) y el video en
`tesis/presentacion/video/Defensa_EduFEM_final.*`.

- **Presentación HTML propia** (57 láminas + 6 de respaldo, 166 pasos), sin frameworks:
  `assets/js/nucleo.js` (reloj, animaciones, formato con coma decimal, jet), `deck.js` (pasos,
  navegación, índice, historial con «Volver», vista del orador, modo narrado, impresión, API de
  captura), `graficos.js` (SVG log-log), `mef.js` (funciones de forma Q4/Q9 y un lienzo que pinta
  mallas y campos interpolados dentro de cada elemento, Q9 curvo incluido), `viz/*.js` (una
  animación por lámina). KaTeX e Inter van en `assets/terceros/` (la carpeta no puede llamarse
  `vendor/` ni `lib/`: el `.gitignore` de la raíz las ignora en cualquier nivel).
- **Datos reales**: `herramientas/exportar_datos.py` corre el motor sobre el ejemplo canónico,
  Cook (Q4/Q9, N = 2 … 32), Timoshenko Q9 56×8, MMS y la rigidez de un cuadrado con 1×1/2×2/3×3
  → `assets/data/datos_edufem.js` (618 KB). Reproduce exactamente las cifras de la tesis (det J
  = 4,7604 en E3, ΣRy = 1000,00, σVM = 864,70 en el nodo 7, Cook Q9 N = 8 = 23,925…).
- **La lección de la extrapolación**, con datos: el exportador aplica también la E con las
  columnas de los puntos 3 y 4 intercambiadas (el defecto de la § 3.7.2) y muestra que las
  tensiones nodales dejan de «cerrar» al reinterpolarlas en los puntos de Gauss.
- **Voz**: `herramientas/narracion_final.json` (un texto por paso, ortografía normal) →
  `sintetizar_voz.py` (edge-tts, `es-BO-MarceloNeural`, +8 %) convierte cifras y símbolos para la
  voz, guarda una pista por paso en `assets/audio/` y subtítulos por frase alineados con las
  marcas por palabra de edge-tts. 4842 palabras, 29,8 min de voz.
- **Video**: la presentación se graba cuadro a cuadro con Chrome sin pantalla
  (`grabar_video.mjs` reparte la grabación en procesos paralelos → `capturar_video.mjs`) y
  `montar_video.py` une partes, voz, subtítulos `mov_text` y capítulos por bloque.
- **PDF de respaldo** (`exportar_pdf.mjs`), **lanzador** (`Presentar_defensa.bat`, Chrome o
  Edge en modo aplicación a pantalla completa) y **pruebas** (`probar_interaccion.mjs`: 19
  comprobaciones de teclado, enlaces, «Volver», índice, tema, vista del orador y narración
  automática).
- **Auditoría de fidelidad**: un agente independiente cotejó cada lámina y cada texto de la
  narración con `main_final.pdf`. Dejó 25 observaciones, todas aplicadas: cifras redondeadas de
  otra manera que en la tesis, páginas del Anexo G, citas con página, rótulos de sección, y
  afirmaciones que la tesis no hace (el MIT, por ejemplo; ver abajo).

## Qué versión de la tesis sigue

`main_final.tex` tal como está en el repositorio. Mientras se hacía la presentación, otra sesión
empezó una versión en mejora (`main_final1.tex` + `capitulos_final1/`) y devolvió
`capitulos_final/` a lo que estaba en el commit. Si `main_final1` reemplaza a la final, repasar
los rótulos, las páginas del Anexo G y los números de cita (el README de `final/` dice dónde
está cada uno).

**MMS** (hallazgo de otra sesión el mismo día, ver *Decisiones abiertas* en `ESTADO.md`): la
`u_M` tiene tr ε = 0 y γ = 0 y no distingue la D de los dos estados planos. La presentación
dejó de repetir las frases de la tesis que lo exageran: tarjeta de «Casos» (ya no «las dos
D»), «Alcances» («núcleo numérico»), las limitaciones en dos láminas y dos pasos de la
narración («deformación plana sin contraste externo»), y el respaldo de deformación plana,
reescrito como «qué la verifica hoy» con la prueba uniaxial de `test_vv_extensions` [8/8]. Esas
formas son ciertas con las dos opciones del autor; con la (a) hay que regenerar datos y rehacer
el respaldo.

**Licencia**: la tesis final no declara la licencia del código (Tabla 1.1: «Libre, código
abierto»; la nota de la Tabla 2.5 dice que la licencia «debe elegirse en consecuencia» con la
AGPL de PyMuPDF). El archivo `LICENSE` del repositorio sí es MIT. Por eso el MIT aparece solo en
la lámina de respaldo «Licencia del software», con el archivo como fuente; decidir si la tesis
lo declara es del autor.

## Versión 2 (estilo PowerPoint) y el .pptx

Pedido del autor el mismo día: «una versión 2 estilo PowerPoint con la misma tecnología» y
«también la versión en PowerPoint».

- **`Defensa_EduFEM_v2.html`**: el mismo motor, las mismas láminas y los mismos datos, con el
  traje de la plantilla de `build_deck.py` (láminas blancas, título azul marino en Calibri con
  acento naranja, puntos de avance, pie con la fuente en la tesis, separadores azul marino,
  transición de fundido). La genera `herramientas/generar_v2.mjs` desde la v1: agrega
  `data-estilo="ppt"` a `<html>`, que activa `assets/css/estilo_ppt.css` (todo cuelga de ese
  atributo, así la v1 no cambia) y en `nucleo.js`/`deck.js` las entradas pasan a fundido, el
  tema queda fijo en claro y se agregan la barra del rótulo, la regla bajo el título, los
  puntos de bloque con clic y el pie por lámina. Carlito (métricas de Calibri) va en
  `assets/terceros/` por si el equipo no tiene Calibri. Los separadores de las dos versiones
  ahora tienen los bloques como botones.
- **`Defensa_EduFEM_v2.pptx`**: conversión automática de la v2, paso por paso.
  `herramientas/extraer_pptx.mjs` recorre cada lámina y cada paso con el reloj virtual y, con
  `pptx_dom.js` inyectado, describe el DOM como cajas, textos (con las líneas que cortó el
  navegador), imágenes, regiones fotografiadas (SVG, lienzos, KaTeX) al doble de resolución,
  videos y enlaces; `construir_pptx.py` (python-pptx + XML propio) lo arma con una diapositiva
  por lámina, un clic por paso (entradas y salidas con «Desvanecer»), transición de fundido,
  hipervínculos, notas con la narración rotulada por clic, los dos videos de Manim en bucle,
  respaldo e índice ocultos. 17 MB.
- **Verificación**: `construir_pptx.py --pasos-separados` arma una diapositiva por paso;
  PowerPoint (COM, `exportar_png_pptx.ps1`) la exporta y se compara con `foto.mjs --pasos --pptx`
  de la HTML: 174 pasos, mediana de 0,6 % de píxeles distintos (antialiasing), sin diferencias
  locales fuera del texto grande. `inspeccionar_pptx.ps1` confirma que PowerPoint abre el
  archivo, cuenta efectos y clics (iguales a los pasos salvo dos que en la HTML tampoco cambian
  la pantalla), transiciones, enlaces y videos. `probar_interaccion.mjs`: 19 de 19 en las dos
  versiones; la v1 quedó idéntica (0,00x % frente a las fotos anteriores).

Trampas de la conversión:

- `page.screenshot({ clip })` de puppeteer cambia el tamaño de la ventana (captureBeyondViewport)
  y dispara `resize`: las láminas se redibujaban en su estado estático (el Jacobiano sin
  distorsionar, el campo del MMS con otra malla). Va con `captureBeyondViewport: false` y el
  extractor aborta si detecta un `resize`.
- Calibración Chrome → PowerPoint con interlineado exacto en Calibri: la primera línea de
  PowerPoint cae `0,24·L − 0,325·s` px más abajo (L interlineado, s tamaño); el ancho de las
  líneas coincide a ±1 px, así que los cortes de línea del navegador se copian tal cual.
- El fondo de un `<span>` resaltado va antes que el texto del párrafo (si no, lo tapa); una
  ficha en línea (inline-block) es un contenedor propio y parte la línea en tramos.
- Un contenedor con un SVG en línea no se fotografía entero salvo que el SVG comparta línea con
  texto; la foto de una región abarca lo que desborda y su sombra.
- Una animación que vuelve al estado inicial (la distorsión del Jacobiano) se captura en su
  punto medio con `data-pptx-captura="paso:ms"` en la `<section>`. Los bucles continuos se
  congelan en t = 4,5 s (`?pptx=1`).
- `Slide.Export` de PowerPoint ignora las animaciones (muestra todas las formas): por eso la
  verificación usa la versión de pasos separados. En la vista de edición del .pptx animado,
  los pasos que cambian un gráfico se ven superpuestos; en la presentación, de a uno.
- python-pptx: `Picture` no tiene `adjustments` (el redondeo va por XML) y `shadow.inherit =
  False` crea el `<a:effectLst>` donde después va la sombra.

## Qué se descartó y por qué

- **reveal.js**: sus transiciones son CSS y no se pueden fotografiar con un reloj virtual; el
  video habría salido con saltos. Un motor propio con todas las animaciones en JS permite que el
  video sea la misma presentación, determinista y sincronizada con la voz por paso.
- **Grabar con `Page.startScreencast` en tiempo real**: cuadros irregulares y dependientes de la
  carga del equipo (un i5 de 2012). El reloj virtual da 30 cps exactos.
- **Buscar el cuadro del MP4 en cada paso** para los videos de Manim del software: 0,10× tiempo
  real. Se extraen los cuadros a JPEG antes de grabar (`?cuadros=`), y va a 0,22×.
- **Actualizar el PowerPoint**: es estático por naturaleza; el PDF cubre el caso de respaldo.

## Trampas encontradas

- Los guiones de `herramientas/` se prueban mejor con archivos: en Git Bash, `$(...)` dentro de
  `node -e "..."` se ejecuta como sustitución de comandos y rompe el código en silencio.
- En la captura, un bucle decorativo que redibuja en cada cuadro obliga a fotografiar los 30
  cps: `EF.bucle(fn, { fps })` limita cuántas veces por segundo se redibuja en la grabación.
- Los rótulos de ejes rotados no aceptan bien subíndices con `baseline-shift`: se evitan.
- Con tres grabaciones en paralelo, Chrome puede tardar más de 30 s en arrancar: los guiones
  usan `timeout: 180000` en `puppeteer.launch`.
- El demuxer `concat` de ffmpeg resuelve las rutas de la lista respecto de la lista, no del
  directorio actual: `montar_video.py` las escribe absolutas.
- Las hojas del Anexo G se extraen por número de hoja del PDF (el anexo empieza en la 180),
  no por el número impreso (164).
- En `Presentar_defensa.bat`, codificar la URL (`\` → `/`, espacio → `%20`) dentro de un
  bloque necesita `EnableDelayedExpansion`; con `%VAR%` se rompe.
- Un texto corregido puede crecer una línea y pisar lo de abajo: después de tocar textos,
  fotografiar **todas** las láminas (`foto.mjs --todas`) antes de grabar, no solo las
  tocadas. La grabación completa tarda ~45 min y se pierde entera si una lámina queda mal.
- En Git Bash, `grep` con acentos en el patrón puede no encontrar nada aunque el texto exista
  (el patrón viaja en cp1252): para buscar en español, la herramienta Grep.

## Qué quedó pendiente

Del autor: mirar el video (ritmo, pronunciación de nombres propios como Štembera o Yhassmany),
ensayar con la vista del orador contra los 40–45 min del Taller 6 y probar
`Presentar_defensa.bat` en el equipo de la sala. Si cambia una cifra de la tesis, cambiarla en
`Defensa_EduFEM.html` o en la narración (las cifras impresas se copiaron; las animadas salen del
motor y se regeneran solas).

## Verificación

`probar_interaccion.mjs`: 19 de 19, sin errores de JavaScript. Fotos de las 63 láminas
revisadas en tema oscuro después de la auditoría (y 12 en tema claro antes). Video final:
31:22, 68,1 MB, H.264 1920 × 1080 a 30 cps, voz AAC, 378 subtítulos y 7 capítulos; se
revisaron cuadros del propio MP4 en las 14 láminas corregidas. PDF de respaldo: 63 hojas. Vocabulario
contrastado con `capitulos_final/CRITERIOS.md` con la herramienta Grep: 0 términos prohibidos;
«oráculo», que la tesis no usa, pasó a «patrón de comparación».
