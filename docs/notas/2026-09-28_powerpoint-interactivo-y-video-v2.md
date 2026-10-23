# PowerPoint de la defensa al máximo: animaciones de la HTML, botones que funcionan y video v2

**Fecha**: 2026-09-28 · **Autor**: agente (Claude) · **Estado**: terminado, **sin commit**

## Qué se pedía

«Mejorar la presentación de PowerPoint al máximo, con los botones y animaciones similares al HTML:
crear animaciones, ya que algunas se presentan como imagen (la distorsión, del pórtico al continuo,
el mapeo isoparamétrico, entre otros); la cobertura de contenido no tiene interacción con los
ítems; opciones más avanzadas; y un segundo video (video_v2) con la presentación del PowerPoint».
Continúa [2026-09-27_defensa-final3-y-orden-tesis.md](2026-09-27_defensa-final3-y-orden-tesis.md).

## Qué se hizo

- **Videos de paso** (`extraer_pptx.mjs` + `pptx_dom.js`): mientras cada paso se asienta, se
  comparan firmas del contenido cada 100 ms —píxeles reducidos de los lienzos, `innerHTML` de SVG
  y fórmulas, y una firma nativa (texto, clases, `src`) de cada visualización—. Lo que cambia se
  vuelve a disparar y se graba cuadro a cuadro (25 cps) con el reloj virtual, aislado y con los
  ancestros a opacidad plena (la aparición la pone PowerPoint). Un lienzo que cambia se graba solo
  (queda nítido lo nativo); si cambia el texto o las clases de una visualización, se graba la
  región entera. 41 videos, que PowerPoint reproduce una vez con el clic y deja en su último cuadro.
- **Laboratorios**: cada visualización con botones expone `pptx()` en `assets/js/viz/`
  (`via`, `base`, `controles`, `fijar`, `normalizar`, `regiones`); el extractor recorre los estados
  alcanzables desde el último paso (138). Los de dos dimensiones o con bucles (Cook, MMS, mapeo,
  Gauss, post-proceso: 74 estados) son diapositivas ocultas enlazadas con Morph; los de una (la
  cobertura con sus 49 ítems, las etapas, el Jacobiano, crudo/suavizado, la lección: 64 estados)
  son grupos con disparadores en la misma diapositiva. Las zonas sensibles aparecen con el último
  clic del paso.
- **Lupa** en las capturas ampliables, **secciones** por bloque, «Seguir ›» en las diapositivas
  de estado, notas del orador que explican los botones.
- **Versión narrada** (`construir_pptx.py --narrada`): un solo grupo automático por diapositiva
  con los clics en el instante de la voz, la voz como audio incrustado (mp3) y avance automático;
  escribe `..._narrada.linea.json` (dónde empieza cada lámina y cada paso).
  **`grabar_video_pptx.py`** la exporta con `CreateVideo` y le agrega subtítulos y capítulos.
- En la HTML: los botones de los laboratorios ya no se ocultan en el modo del conversor
  (`body.captura:not(.pptx)`), y en el estilo PowerPoint bajan a la franja libre bajo la regla del
  título (tapaban los puntos de avance, también en la v2 en vivo).

## Qué se descartó y por qué

- **Disparadores para los laboratorios de dos dimensiones**: un disparador no tiene estado, así que
  «N = 8» no sabe si está en Q4 o en Q9; hacerlo con capas de zonas sensibles por estado da miles de
  efectos (post-proceso: 36 estados × 13 botones). Se usaron diapositivas enlazadas.
- **Grabar todo como región**: taparía con video los textos nativos (menos nítidos). Solo se graba
  la región cuando cambia lo nativo; si solo cambia un lienzo, solo el lienzo.
- **Custom shows con «volver»** para salir de un estado con «siguiente»: al volver, PowerPoint
  reinicia la lámina de origen. Se dejó el botón «Seguir ›».

## Trampas encontradas (probadas con PowerPoint 16 por COM y en exportaciones)

- **Cuadros B**: con H.264 normal, PowerPoint arranca el video 160 ms tarde y nunca muestra los
  últimos 4 cuadros. Todos los videos se recodifican con `-bf 0` (`para_powerpoint()`).
- **Póster**: si no es exactamente el cuadro 0, el video exportado muestra durante ~1,8 s
  «póster + (cuadro − cuadro 0)» en los videos que arrancan solos. El póster sale del propio video.
- **Visibilidad inicial**: la decide el primer efecto de cada forma en orden de documento; un
  disparador ficticio (fuera de la diapositiva, primero) con entradas deja los grupos ocultos.
  Grupos sin `grpId` ni `bldP`.
- **Diapositivas ocultas**: «siguiente» desde una oculta va a la que sigue aunque esté oculta;
  `CreateVideo` las excluye.
- **Tiempos del video exportado**: lámina = transición + máx(advTm, fin de la línea automática,
  medios incluidos); `advTm`, el audio y los efectos cuentan desde el fin de la transición. Los
  grupos de clic se reparten en huecos iguales: para exportar hay que usar un solo grupo automático.
- **Audio con python-pptx**: se inserta como video y se convierte; la relación hay que crearla de
  nuevo (`relate_to` + `drop_rel`), porque el tipo queda fijado.
- **Office de este equipo**: Office LTSC 2021 **sin activar**; cualquier ventana visible de
  PowerPoint (una presentación) hace aparecer el asistente de activación a los 2 s. El trabajo sin
  ventana (COM, exportar) no se ve afectado. El autor tenía el `.pptx` abierto en **WPS Office**.

## Qué quedó pendiente

- **Nada en un commit** (el autor no lo pidió).
- **Del autor**: presentar el `.pptx` en el equipo de la sala con PowerPoint 2019, 2021 o 365
  **activado** (WPS no garantiza Morph, disparadores ni videos automáticos); probar a mano los
  botones de un laboratorio y la lupa; mirar el video v2.
- **Reemplazar el `.pptx`**: el autor tenía `Defensa_EduFEM_final3.pptx` abierto en WPS Office
  (archivo bloqueado), así que la versión nueva quedó como `final3/Defensa_EduFEM_final3_nuevo.pptx`.
  Al cerrar WPS: borrar el viejo y renombrar el nuevo sin «_nuevo» (el README ya usa ese nombre).

## Verificación

- COM: 141 diapositivas abren en 5 s; 109 disparadores, 1888 hipervínculos, 81 ocultas, 10
  secciones, 85 medios; un clic por paso en las 60 láminas. XML: ninguna forma inexistente como
  destino, ids únicos (`validar_xml.py` en el scratchpad de la sesión).
- Exportaciones de PowerPoint revisadas cuadro a cuadro: pórtico, Jacobiano (distorsión), Cook
  (malla y curvas), cobertura (marcado), carátula, separador, caja negra; la narrada coincide con su
  línea de tiempo (±0,5 s en 99 s).
- `probar_interaccion.mjs`: todo en orden tras los cambios en la HTML.
