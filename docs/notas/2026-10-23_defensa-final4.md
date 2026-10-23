# Defensa final sobre final4: presentación, video, PowerPoint y PDF

**Fecha**: 2026-10-23 · **Autor**: agente (Claude) · **Estado**: terminado (falta el ensayo del autor)

## Qué se pedía

El autor pidió la presentación final y última de la defensa, sobre final4, junto con el video, y que
la de final3 se guardara ordenada en `tesis/presentacion/`. Sus pedidos fueron estos:

- el alcance, mostrado de forma dinámica y con énfasis;
- la formulación variacional (trabajos virtuales), fácil de seguir;
- el software explicado sin tecnicismos ni programación;
- un video de 30 minutos;
- gráficas iguales a las del documento;
- fuera cinco láminas concretas: el motor y la matriz dispersa, la consistencia interna, la base de
  conocimiento, las limitaciones y la tríada;
- sin redundancia, sobre todo en los resultados;
- más presencia de la hipótesis y de las conclusiones.

Preguntó además, pidiendo una respuesta honesta, si los resultados debían presentarse en las
conclusiones.

## Qué se hizo

- Se archivó `tesis/presentacion/final3/` en `tesis/presentacion/archivo/final3/` y se rehízo el
  índice `tesis/presentacion/README.md`.
- `tesis/presentacion/final4/` reúne todo lo de la defensa:
  - 31 láminas más 11 de respaldo, cada una en su archivo `laminas/NN_id.html`, que une
    `herramientas/armar_html.mjs`;
  - las visualizaciones, en `assets/js/viz/l4_*.js`;
  - la narración, en `herramientas/narracion/*.json`;
  - el guion maestro, en `GUION.md`.
- Hay cinco bloques: Introducción (6,5 min), Cap. 1 (4,5), Cap. 2 (4,5), Cap. 3 (5,5) y
  Conclusiones (6,5).
- Las Figuras 3.1, 3.4 y CR.2 se dibujan con las mismas funciones que en la tesis
  (`herramientas/figuras_documento.py` → `assets/data/figuras_doc.js`) y se animan por series
  (`assets/js/viz/figdoc.js`).
- **Respuesta al autor sobre los resultados.** El Capítulo 3 muestra los datos una sola vez, y las
  conclusiones dan el veredicto. Responden a cada objetivo (Tabla CR.1), contrastan la hipótesis
  parte por parte con la regla conjuntiva, retoman el margen (Figura CR.2) y responden al problema,
  con su indicador, y a las dos preguntas. Los resultados vuelven ahí solo como evidencia: cada
  evidencia del contraste lleva con un clic a su lámina. Las conclusiones escritas de final4 no se
  tocaron.
- **La demostración en vivo** va en el Cap. 2. La lámina «EduFEM» sirve de mapa y la de la
  demostración tiene el guion de cinco pasos y, de respaldo, capturas reales. Las funcionalidades
  no se repiten en láminas.
- **Dos olas de revisión de solo lectura**, cuyas fichas se verificaron antes de aplicarlas:
  - la ola 1 dejó 55 hallazgos;
  - la ola 2, con las lentes de fidelidad de los Cap. 2 y 3, redundancia y lenguaje, y tribunal,
    dejó 25 + 11 + 18 hallazgos, con tres verificaciones adversariales.
  - Se descartaron dos fichas, refutadas por el verificador. La primera pedía meter SAP2000 entre
    las «referencias de exactitud conocida» de la lámina de evaluación. La segunda decía que en
    Cook se generalizaba el «diez veces menor»; no se generaliza, aunque igual se nombró el 578 en
    la voz.
- Correcciones de fondo de la ola 2:
  - el punto de control de Cook es (48; 52), el punto medio del borde derecho, y no la esquina;
  - M0 trabaja en el pre-proceso, sobre toda la malla;
  - la solución del MEF está en equilibrio en el sentido de los trabajos virtuales, no punto por
    punto;
  - de la arbitrariedad de δu sale una ecuación por GDL;
  - el indicador de que el problema se resolvió (§ 3.8) tiene lámina propia en la respuesta;
  - la variable dependiente pasa de nivel «baja» a «alta» en el contraste;
  - el OE3 trae su «15 de 15» y el objetivo general su «para qué».
- Respaldos nuevos: el cortante de la viga (τxy 2,89 %), cómo se afirma la mejora sin pretest ni
  grupo de control, y por qué 18 de los 49 contenidos.
- **Ola 3, sobre lo que cambió la ola 2.** La hicieron tres lectores de solo lectura, sin navegador,
  y refutadores para los hallazgos medios. Sus correcciones:
  - se quitó «punto por punto no lo está, y por eso sus tensiones saltan», que no está en la § 1.3;
  - el ejemplo guía se glosa en su primera mención;
  - D es «la del material»: no sale de las funciones de forma;
  - se ensamblan las rigideces, no las ecuaciones;
  - «la solución tentativa» en la variable interviniente;
  - el objetivo general va literal;
  - «caso clásico», no «problema de referencia»;
  - la prueba mantiene «coincidente» (≤ 10⁻⁹), no «idéntica»;
  - «queda juzgar», no «medir», el para qué, porque la partida se documenta y no se mide;
  - «puede comprobarse» (nivel alto en modo posible);
  - «tres debilidades declaradas», que cierra con la lámina;
  - el residuo es «del orden de» 10⁻¹³;
  - el respaldo pasó a llamarse «¿Cómo se afirma la mejora…?».
- La lámina de respuesta tiene ahora 5 pasos. El paso 3, «La mejora frente a la situación de
  partida · § 3.8», tiene la voz y el bloque sincronizados.
- **Último pedido del autor (mismo día):**
  - Fuera de las conclusiones, en pantalla y en voz: «De esa brecha salieron los cinco requisitos
    de la herramienta» y los dos «Aporte: …», el de las decisiones de diseño y el de la batería
    de V&V.
  - La lámina de respuesta, concisa: respuesta en una línea, rasgos en tres o cuatro palabras, el
    cartel reducido a «Problema respondido».
  - La HTML se maneja con el mouse: clic derecho, adelante; clic izquierdo en el fondo, atrás; la
    rueda elige un botón o enlace y apretarla lo abre (`deck.js`, `ratonYToque`; estilo
    `.sel-raton`).
  - **El video se dejó**, a pedido del autor. En su lugar va el audio completo,
    `audio/Defensa_EduFEM_final4_narracion.mp3`, que arma `herramientas/audio_completo.py`.
  - **PowerPoint**: `extraer_pptx.mjs --sin-bucles --sin-animaciones` tarda 11 min; con los clips
    no bajaba de una hora, porque la carátula sola llevó 7 min. Después, `construir_pptx.py` y
    `--narrada` dan `Defensa_EduFEM_final4.pptx` (43 diapositivas, 15,3 MB, con notas) y
    `…_narrada.pptx` (34,1 MB, con la voz incrustada). Se controlaron con python-pptx: 12 ocultas
    (los respaldos y el índice), 31 con notas y ninguno de los textos retirados. No hubo control
    visual por COM.
  - **HTML portable**: la HTML copiada sola a otro equipo se veía como texto sin formato, porque
    estilos, scripts, letras e imágenes se cargan desde `assets/`. `herramientas/empaquetar_portable.mjs`
    arma `Defensa_EduFEM_v2_portable.html`, de 26,6 MB, con 188 archivos y las 91 pistas de voz
    como data: URI. La voz pasa por `EF_ACTIVO()`, un parche que aplica el empaquetador a `deck.js`.
    Se probó copiado solo a una carpeta vacía: `probar_interaccion.mjs` dio todo en orden, con 0
    errores y la narración sonando, y las fotos muestran letras, KaTeX, figuras e imágenes.
  - **Trampa del entorno**: el hook `~/.claude/scripts/notify-stop.ps1` lee las últimas 400 líneas
    del transcript y las pasa por `ConvertFrom-Json`. En una sesión larga, cada aviso tarda
    minutos de CPU y se acumulan; llegó a haber ocho a la vez. Se cerraron a mano, y el autor
    decide si se acota el script.
- Voz: es-BO-MarceloNeural con edge-tts 7.3.1, a +0 % y con pausas de 1,0 s. Son 91 pistas,
  4503 palabras, 28,3 min de voz más 1,5 min de pausas.

## Qué se descartó y por qué

- **Poner «todas las tablas» en las conclusiones.** Repetiría el Cap. 3, y el autor pidió evitar
  la redundancia. El veredicto sí va con evidencia, como manda el Taller 6: criterio de
  cumplimiento de la hipótesis e indicador de resolución del problema.
- **Láminas de funcionalidades del software.** Duplicarían la demostración en vivo.
- **Constructores en paralelo con esfuerzo máximo y bucles de capturas.** En este equipo (dos
  núcleos, 7,9 GB de RAM, a menudo menos de 0,5 GB libres) se estancaban horas. Lo que funcionó
  fue esto: el orquestador integra, narra y arma; los agentes solo revisan, en modo lectura y con
  paquetes de contexto acotados.

## Trampas encontradas

- `armar_html.mjs --v2` **sin `--salida`** sobrescribe `Defensa_EduFEM.html` con el aspecto v2. La
  v2 oficial se arma con `generar_v2.mjs`.
- `armar_html.mjs` solo recoge `NN_id.html`, dos dígitos y un guion bajo: un archivo `99b_x.html`
  queda fuera sin aviso.
- Con poca memoria libre, Chrome tarda más de 30 s en cargar la página. Todos los `page.goto` de
  `herramientas/` llevan hoy `timeout: 180000`.
- Los heredoc del Bash tool van en cp1252: los scripts con tildes se escriben con Write.
- `probar_interaccion.mjs` comparaba la vista del orador con «paso 1» fijo. Ahora compara el
  estado de antes con el de después.
- **El capturador del video** (`capturar_video.mjs`) llamaba a la página en cada cuadro, aun quieto,
  y grababa a 0,15× tiempo real, unas 3,5 h para 30 min. Ahora, tras tres cuadros seguidos sin
  animaciones ni bucles (`r.ocioso`), escribe de una vez los cuadros que faltan de la voz. El
  tercer cuadro descarta una animación encadenada que arranque al resolverse la anterior.
  - Con eso pasó a 0,3×. El resto lo limitan la latencia de cada captura, de unos 0,45 s a
    1920 × 1080 con la memoria justa, y los bucles decorativos de la portada y los separadores.
  - La CPU quedaba al 40 %, y por eso `--partes=2` acelera, siempre que haya más de 1 GB
    disponible.
- **Una cifra de la tesis cambia una voz grabada.** Cualquier cambio de narración obliga a regrabar
  todo el video, porque las duraciones se fijan al empezar. Conviene cerrar las revisiones antes de
  grabar.

## Qué quedó pendiente

- **Del autor.** Ensayar con `Presentar_defensa_v2.bat` (S, vista del orador; A, narrada; o con el
  mouse) y escuchar el audio. El video narrado no se generó, por decisión del autor: si más adelante
  hace falta, `grabar_video.mjs --partes=2` y `montar_video.py` lo producen en una hora y media. Probar el `.pptx` en el equipo de la sala con PowerPoint 2019, 2021 o 365 activado: el
  Office de este equipo no está activado, y WPS no garantiza Morph ni los videos de paso.
- Nada queda en commit: el autor no lo pidió.

## Verificación

- `node herramientas/probar_interaccion.mjs --html=Defensa_EduFEM_v2.html` comprobó:
  - el recorrido completo, de 91 pasos;
  - los enlaces del contraste y el botón «Volver»;
  - el índice y el respaldo;
  - las series de la Figura 3.1;
  - la vista del orador y la narración automática;
  - 0 errores de JavaScript.
- Se fotografiaron una por una, en v2, las láminas cambiadas en las olas 2 y 3 y los tres
  respaldos nuevos: sin cortes ni solapes.
