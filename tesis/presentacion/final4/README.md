# Defensa de EduFEM — presentación final (tesis final4)

Presentación de la defensa final, sincronizada con **final4** (`tesis/main_final4.pdf`, fuente
`tesis/main_final4.tex` + `tesis/capitulos_final4/`): la hipótesis que dictó el tribunal, su contraste en
cuatro partes (Tabla 3.11, Figura CR.1) y las conclusiones de final4. Reemplaza a la defensa de borrador
(final3), que queda como archivo en `../archivo/final3/`, solo en el disco del autor (no se sube al
repositorio).

| Archivo | Qué es |
|---|---|
| `Defensa_EduFEM_v2.html` · `Presentar_defensa_v2.bat` | **La presentación** (estilo PowerPoint: láminas blancas, títulos en azul marino, acento naranja). Se abre con doble clic en el `.bat`, a pantalla completa, sin internet y sin instalar nada |
| **`Defensa_EduFEM_v2_portable.html`** | **La misma presentación en un solo archivo** (26,6 MB). Lleva adentro estilos, letras, fórmulas, imágenes, videos y la voz, así que funciona sola en cualquier equipo y navegador. **Es el archivo que hay que copiar a otra laptop o a un USB.** `Defensa_EduFEM_v2.html`, en cambio, necesita la carpeta `assets/` al lado: copiada sola se ve como texto sin formato |
| `Defensa_EduFEM.html` · `Presentar_defensa.bat` | La misma, en tema oscuro (para salas oscuras; tecla **T** alterna claro/oscuro) |
| `Defensa_EduFEM_final4.pptx` | La presentación en **PowerPoint** (2019, 2021 o 365), editable: 31 láminas más los 11 respaldos, ocultos (se llega a ellos con los enlaces y el índice). Lleva un clic por paso, con entradas y salidas nativas, transiciones Transformación (Morph), enlaces entre láminas con «Volver» y la narración de cada paso en las notas del orador. Las regiones que en la HTML se animan sin fin van como imagen fija: la carátula, la malla de los separadores, la balanza de los trabajos virtuales y el recorrido de la demo |
| `Defensa_EduFEM_final4_narrada.pptx` | La misma, **narrada**: la voz va incrustada en cada lámina y avanza sola, como un video. Para ensayar escuchando |
| `audio/Defensa_EduFEM_final4_narracion.mp3` · `audio/indice_audio.md` | **La narración completa** (29,6 min) en un solo audio, para escucharla y ensayar, con el minuto en que empieza cada lámina |
| `video/` | Vacía: el video narrado **no se generó**, porque el autor pidió dejarlo y priorizar el PowerPoint y la HTML. Se puede grabar con `grabar_video.mjs` (ver «Regenerar») |
| `GUION.md` | El guion maestro: qué dice cada lámina, sus pasos, sus fuentes en la tesis y su narración |
| `laminas/` | Cada lámina en su propio archivo HTML (`NN_id.html`); `herramientas/armar_html.mjs` las une |
| `herramientas/` | Lo que genera las gráficas de la tesis, la voz, el video, el PowerPoint y los PDF (no hace falta para proyectar) |

## Qué cambió respecto de la defensa de borrador (final3)

- **31 láminas en vez de 60** (más 11 de respaldo para preguntas, fuera del recorrido). Cada idea se
  explica una sola vez.
- **Cinco bloques**: Introducción · Capítulo 1 (Fundamentar) · Capítulo 2 (Desarrollar) · Capítulo 3
  (Verificar y validar, con los resultados y su análisis juntos) · Conclusiones.
- **Alcance con énfasis**: dos láminas propias, «Qué se estudia y hasta dónde llega» (el embudo del
  alcance, con lo que queda fuera saliendo de escena; tensión y deformación plana; delimitación) y «¿Por
  qué el plano?» (barra, plano y sólido, con el tamaño real de sus matrices).
- **La formulación variacional**: lámina «el principio de los trabajos virtuales», animada (el
  desplazamiento virtual, el trabajo interno y el externo que se igualan, la cadena hasta K u = F).
- **El software sin tecnicismos**: fuera la arquitectura, el motor, la matriz dispersa y los índices; queda
  «un lienzo, tres fases, ocho módulos, una memoria de cálculo», más la demostración en vivo.
- **Gráficas iguales a las del documento**: las Figuras 3.1, 3.4 y CR.2 se insertan tal como las dibuja la
  tesis (`herramientas/figuras_documento.py` llama a sus mismas funciones de dibujo y las guarda en SVG) y
  se animan por series (`assets/js/viz/figdoc.js`). Por ejemplo, el error del MMS se grafica contra h,
  como en la tesis.
- **Conclusiones con más peso** (≈ 6 min): los objetivos, uno por uno, con su conclusión y su evidencia;
  el contraste de la hipótesis parte por parte, con el mismo código de color que en la introducción
  (azul la independiente, violeta la dependiente, naranja la interviniente) y su sello «comprobada»; el
  margen de cada criterio (Figura CR.2 animada); la respuesta al problema y a las dos preguntas; las
  recomendaciones por capítulo.
- **Presentar con el mouse**: clic derecho avanza, clic izquierdo retrocede, y la rueda elige y abre
  los botones. Así la HTML puede pasarse con un mouse inalámbrico, como un PowerPoint.
- **Retiradas**: «Motor: identidad ≠ índice y matriz dispersa», «Consistencia interna», «Lo que queda en
  la base de conocimiento», «Limitaciones, declaradas», «La tríada», «Q4 frente a Q9» (está en Cook),
  «Desempeño del solucionador» (pasa al respaldo), «Qué dicen los resultados y qué no» (sus límites van a
  la respuesta final).

## Cómo se presenta

| Tecla | Acción |
|---|---|
| → · Espacio · Av Pág | siguiente paso |
| ← · Re Pág | paso anterior |
| **M** · Esc | índice: todas las láminas y el respaldo para preguntas |
| **S** | vista del orador en otra ventana: narración del paso, lo que viene y cronómetro por bloque (objetivo: 30 min) |
| **A** | presentación narrada automática; **C** subtítulos |
| **L** puntero láser · **B** pantalla negra · **T** tema · **F** pantalla completa | |
| **Mouse**: clic derecho · clic izquierdo (en el fondo) | siguiente paso · paso anterior |
| **Mouse**: rueda · apretar la rueda | elegir un botón o enlace de la lámina (queda enmarcado) · abrirlo |

Un clic directo sobre un botón o un enlace lo abre como siempre; el clic izquierdo solo retrocede
cuando cae fuera de ellos.

**La demostración en vivo** va en el Capítulo 2: la lámina «EduFEM» sirve de mapa y la lámina
«Demostración en vivo» tiene el guion de cinco pasos (cargar el ejemplo guía, comprobar y resolver, abrir
un módulo, consultar un nodo con la sonda, generar la memoria). Si el equipo de la sala no tiene EduFEM, el
segundo paso de esa lámina muestra el recorrido con capturas reales.

**Respaldo para preguntas** (tecla M, al final del índice): el Jacobiano rehecho a mano, de dónde salen
los umbrales, «educativo» sin medir estudiantes, la deformación plana, los apoyos de la viga, el desempeño
con mallas grandes, la matriz de consistencia, la licencia, **el cortante de la viga** (τxy en B: 2,89 %,
declarado), **cómo se afirma la mejora** sin pretest ni grupo de control (la situación de partida se
documenta, no se mide), y **por qué 18 de los 49 contenidos** del consenso. Cada evidencia del contraste de la hipótesis también lleva, con un clic, a su
lámina; el botón «Volver» regresa.

## Regenerar

Desde la raíz del repositorio (requiere el `.venv` con `edge-tts` 7.3.1 o posterior y `mutagen`, Node.js,
`ffmpeg`, Chrome o Edge y, para el `.pptx`, PowerPoint):

```
cd tesis\presentacion\final4\herramientas && npm install && cd ..\..\..\..
.venv\Scripts\python.exe tesis\presentacion\final4\herramientas\figuras_documento.py     # gráficas de la tesis en SVG
node tesis\presentacion\final4\herramientas\armar_html.mjs                              # laminas/ -> Defensa_EduFEM.html
node tesis\presentacion\final4\herramientas\generar_v2.mjs                              # -> Defensa_EduFEM_v2.html
node tesis\presentacion\final4\herramientas\empaquetar_portable.mjs                     # -> Defensa_EduFEM_v2_portable.html (un solo archivo; después de sintetizar la voz)
.venv\Scripts\python.exe tesis\presentacion\final4\herramientas\armar_narracion.py       # narracion/*.json -> narracion_final4.json
.venv\Scripts\python.exe tesis\presentacion\final4\herramientas\sintetizar_voz.py        # voz (internet)
.venv\Scripts\python.exe tesis\presentacion\final4\herramientas\audio_completo.py        # -> audio/…_narracion.mp3
node tesis\presentacion\final4\herramientas\grabar_video.mjs --partes=1 --html=Defensa_EduFEM_v2.html   # --partes=2 solo con RAM de sobra
.venv\Scripts\python.exe tesis\presentacion\final4\herramientas\montar_video.py --trabajo=<las carpetas que imprime el paso anterior>
node tesis\presentacion\final4\herramientas\exportar_pdf.mjs --html=Defensa_EduFEM_v2.html
node tesis\presentacion\final4\herramientas\extraer_pptx.mjs --sin-bucles --sin-animaciones   # ~12 min (sin esos flags graba también los clips: más de 1 h en este equipo)
.venv\Scripts\python.exe tesis\presentacion\final4\herramientas\construir_pptx.py        # -> Defensa_EduFEM_final4.pptx
.venv\Scripts\python.exe tesis\presentacion\final4\herramientas\construir_pptx.py --narrada   # -> Defensa_EduFEM_final4_narrada.pptx
```

- **Cambiar una lámina**: su archivo en `laminas/` y, si anima, su código en `assets/js/viz/l4_*.js`; luego
  `armar_html.mjs` y `generar_v2.mjs`. Probar sin abrir el navegador:
  `node herramientas/armar_html.mjs --v2 --solo=<id> --salida=_prueba.html` y
  `node herramientas/foto.mjs <carpeta> <id>:0 <id>:1 --html=_prueba.html`.
- **Cambiar lo que se dice**: `herramientas/narracion/<grupo>.json` y repetir desde `armar_narracion.py`.
- **Una cifra de la tesis**: las gráficas salen solas de `docs/vyv/datos/` (`figuras_documento.py`); las
  cifras escritas en las láminas se copiaron de final4 y se cambian a mano.

## Fidelidad a la tesis

Cada lámina cita en su rótulo la sección, tabla o figura de final4 de la que sale; las citas llevan el
número de la lista de referencias de final4; las hojas del Anexo G son las de final4 (pp. 167–175,
`assets/img/l4/anexoG4_p*.png`). Se respetan las reglas de `tesis/capitulos_final4/CRITERIOS.md`: ningún
umbral se presenta como «fijado de antemano» (el veredicto descansa en el margen, Figura CR.2), el MMS no
se presenta como verificación de la matriz constitutiva, no se afirman efectos sobre el estudiante y se
dice «ejemplo guía».
