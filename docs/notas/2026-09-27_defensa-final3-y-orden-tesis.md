# Orden de `tesis/` y defensa de final3: HTML, PowerPoint dinámico y video

**Fecha**: 2026-09-27 · **Autor**: agente (Claude) · **Estado**: terminado, **sin commit**

## Qué se pedía

«Ordena los archivos de mi tesis; el archivo final por ahora será `tesis/main_final3.pdf`. Crea
la presentación en HTML y PowerPoint y el video de presentación de la tesis. Haz que el
PowerPoint sea más dinámico, con transiciones y animaciones avanzadas (bucles, etc.)».

## Qué se hizo

**Orden de `tesis/`.** En la raíz queda solo la versión vigente: `main_final3.tex`,
`main_final3.pdf` (el PDF de `origin/main`, sin recompilar), `capitulos_final3/` y las carpetas
compartidas. final, final1 y final2 pasaron con `git mv` a `archivo/final/`, `archivo/final1/` y
`archivo/final2/` (cada una con su `.tex`, su carpeta de capítulos y su PDF; final con el
`preambulo.tex` general, que también usan v1 a v4). Un `latexmkrc` nuevo manda los auxiliares a
`build/` (gitignored). `tesis/README.md` y `tesis/archivo/README.md` reescritos: qué es cada
versión y cómo recompilar una archivada (sobre una copia de `tesis/`, porque sus rutas son
relativas a esa carpeta). En `presentacion/`: la defensa de la final pasó a `archivo/final/`
(con su video) y las v1-v2 PowerPoint a `archivo/v1_v2/`; `presentacion/README.md` es el índice.

**Defensa de final3** (`tesis/presentacion/final3/`, detalle en su README): la presentación HTML
rehecha para final3 (60 láminas + 6 de respaldo: problema, objetivo general en cuatro tarjetas,
tres objetivos, hipótesis con la relación de variables, tríada de conclusiones, CR.1 con enlaces
a la evidencia, margen de CR.2 en escala logarítmica), narración nueva
(`narracion_final3.json`, 172 pistas), video de 36:47 con subtítulos y capítulos, PDF de
respaldo en los dos estilos, y el PowerPoint. Dos auditorías de fidelidad contra
`main_final3.pdf` (láminas y narración) quedaron aplicadas.

**PowerPoint dinámico.** Se construyó un catálogo del XML de animaciones y transiciones tal como
lo escribe PowerPoint 16 (efectos, bucles, trayectorias, texto por palabra, disparadores,
Morph, 102 transiciones), verificado por COM: `herramientas/plantillas_pptx.py`. Sobre él,
`construir_pptx.py` arma entradas por grupo con el efecto de su clase, salidas antes de
entradas, fundidos cruzados según el apilado, 67 énfasis en bucle, 18 trayectorias, 14 regiones
animadas grabadas como video en bucle (más los 2 videos del software) y transiciones Morph,
Galería, Cortinas, fundido a negro y Forma circular. El extractor (`pptx_dom.js`,
`extraer_pptx.mjs`) aprendió las pistas `data-pptx-*` que lo guían (tabla en el README de
`final3/`).

## Qué se descartó y por qué

- **Nombres por omisión (o únicos sin «!!») con Morph**: Morph empareja rectángulos de nombre
  distinto entre láminas y los hace volar por la pantalla durante la transición. Probado con tres
  variantes de dos diapositivas exportadas a video: solo con nombres únicos **con** «!!» se
  funden en su lugar. Por eso todo el cuerpo lleva `!!<lámina> <n>` y solo la cabecera y el pie
  comparten nombre.
- **Fundir a la vez la forma vieja y la nueva** cuando algo cambia entre pasos: a mitad de
  camino las dos están al 50 % y se ve el fondo (parpadeo). Se decide por el apilado: si la vieja
  queda encima, la nueva aparece de golpe debajo y la vieja se funde; si no, al revés.
- **Capturar los cuadros de un bucle con `screenshot({clip:{…, scale:0.5}})`**: con
  `deviceScaleFactor` 2 el recorte sale ampliado al doble. Se captura a resolución completa y se
  reduce en ffmpeg, sobre un fondo `lavfi` del tamaño real del PNG.
- **Repetir «hasta el final de la diapositiva» por COM**: `RepeatCount` rechaza negativos. Se
  escribe el XML (`repeatCount="indefinite"`), que PowerPoint lee como −2147483648.

## Trampas encontradas

- Sin ventana, PowerPoint **no pregunta si reparar**: abre o `Open` falla con E_FAIL. No abre si
  un efecto apunta a un `spid` inexistente, con un `nodeType` inválido, con dos transiciones en
  una diapositiva o con `mc:Ignorable` de un prefijo no declarado en la raíz. Y pierde en
  silencio: la transición si `<p:timing>` va antes; el arranque automático si `<p:tn val>`
  apunta mal; la secuencia principal (se vuelve disparador) si le faltan `prevCondLst` y
  `nextCondLst`.
- Imágenes, videos y conectores van **sin `grpId` ni `bldP`**; los cuadros de texto, con `bldP`
  **sin** `animBg`.
- `python-pptx.add_movie` escribe su propio `<p:timing>`: `plantillas_pptx.inyectar` lo
  reemplaza.
- Un paso cuya animación HTML vuelve al estado inicial no deja cambio en la captura y el clic se
  perdía: el post-proceso lleva `data-pptx-captura="3:1300"` (muestra el campo crudo) y, si igual
  no hay cambio (la suma de los aportes de Gauss), el constructor pulsa en cascada los gráficos
  de la lámina para que cada clic siga a su párrafo de la narración.
- `git mv` en Windows da «Permission denied» si el archivo está abierto (el MP4 viejo): cerrar
  el visor o reintentar.

## Qué quedó pendiente

- **Nada está en un commit**: el autor no lo pidió. `git status` muestra los renombres de
  `tesis/` y lo nuevo de `presentacion/`.
- **Del autor**: mirar el video, verificar la pronunciación, ensayar con la vista del orador,
  probar el lanzador y **pasar el PowerPoint entero en modo presentación en el equipo de la
  sala** (Morph pide PowerPoint 2019 o Microsoft 365; en versiones anteriores se ve un fundido).
- `tesis/defensa_metodologica/contexto_defensa.tex` (líneas 447 y 513) sigue diciendo que el
  binario lleva PyMuPDF: es el punto 4 de la decisión del retiro de PyMuPDF en `ESTADO.md`.
- Si el autor elige la opción (a) del MMS, regenerar los datos y rehacer el respaldo de
  deformación plana (ver el README de `final3/`).

## Verificación

- `node herramientas/probar_interaccion.mjs`: todo en orden (21 comprobaciones, 0 errores de
  JavaScript).
- PowerPoint 16 por COM: abre el `.pptx` en ~3 s sin reparar; 67 diapositivas, 2731 efectos, 67
  bucles, 18 trayectorias, 16 videos con inicio automático y en bucle, Morph en 52 láminas,
  Galería en 6; notas en las 60 principales; cada lámina con tantos clics como pasos de
  narración.
- Video exportado por PowerPoint (`CreateVideo`) de doce láminas de muestra, revisado cuadro a
  cuadro: bucles, trayectorias, palabra por palabra, Morph, Galería y Cortinas se mueven como
  se diseñó.
- PDF de respaldo: 66 láminas cada uno, revisados por muestreo.
