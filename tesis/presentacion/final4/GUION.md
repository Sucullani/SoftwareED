# Guion maestro de la defensa final (final4)

Documento de trabajo: fija **qué dice cada lámina, en qué orden, con qué animación y con qué
narración**. Lo siguen los agentes que construyen las láminas y quien las revisa. La tesis que
manda es **final4**: `tesis/main_final4.pdf` (fuente `tesis/capitulos_final4/*.tex`; texto plano en
UTF-8 en `C:\Users\User\AppData\Local\Temp\claude\c--Tesis-Tesis-Software-SoftwareED\b4bc88ee-2aab-48d3-9be5-5f4fc02ff564\scratchpad\main_final4_utf8.txt`;
numeración de secciones, tablas, figuras y páginas en `...\scratchpad\etiquetas_final4.tsv`).

## 1. Qué pidió el autor y cómo se resuelve

| Pedido | Decisión |
|---|---|
| Pocas láminas, sin redundancias, las partes importantes de la tesis | 31 láminas principales (antes 60) + 8 de respaldo fuera del recorrido. Cada idea se explica **una sola vez**, en su lámina; las demás la nombran sin repetirla |
| Los alcances, dinámicos y con énfasis | Dos láminas propias en la introducción: **«Qué se estudia y hasta dónde llega»** (embudo animado del análisis estructural a EduFEM, con lo que queda fuera saliendo de escena; tensión y deformación plana; delimitación) y **«¿Por qué el plano?»** (barra · plano · sólido, con el tamaño real de sus matrices) |
| La formulación variacional elegida (trabajos virtuales), dinámica y fácil | Lámina **«Formulación variacional: el principio de los trabajos virtuales»**: del pórtico a la chapa, la forma fuerte, el desplazamiento virtual animado con la balanza «trabajo interno = trabajo externo», y la cadena N → B → D → kₑ → K u = F |
| Nada de programación ni código; que cualquiera entienda el software | Fuera: arquitectura por capas, motor, índices de GDL, matriz dispersa, JSON/CSV/ZIP, regresión, vectorización, SciPy. El software se cuenta como lo ve quien lo usa: **un lienzo, tres fases, ocho módulos, una memoria de cálculo** |
| Gráficas iguales a las del documento | Las Figuras 3.1, 3.4 y CR.2 se insertan **tal como las dibuja la tesis** (mismas funciones de dibujo, mismos datos, h en el eje horizontal, error hacia abajo al refinar), en SVG, y se animan por series: `assets/js/viz/figdoc.js` + `herramientas/figuras_documento.py` |
| Retirar las 5 láminas de las capturas | Fuera, sin respaldo: «Motor: identidad ≠ índice y matriz dispersa», «Consistencia interna: el modelo no deriva», «Lo que queda en la base de conocimiento», «Limitaciones, declaradas», «La tríada: capítulo, conclusión y recomendación» |
| El análisis de resultados era redundante | Se fusiona con los resultados en un solo bloque (Capítulo 3): cada caso muestra su dato **y** su lectura. Fuera: «Q4 frente a Q9» (está en Cook), «Desempeño del solucionador» (pasa a respaldo), «Qué dicen los resultados y qué no» (sus límites van, una sola vez, a la respuesta final) |
| Más presencia de la hipótesis y de las conclusiones, con animación | El bloque de conclusiones crece (≈ 6 min, antes ≈ 3): objetivos cumplidos uno por uno → **contraste de la hipótesis parte por parte con su sello «comprobada»** (el clímax) → margen de cada criterio (Figura CR.2 animada) → respuesta al problema y a las dos preguntas → recomendaciones. La hipótesis usa en la introducción y en las conclusiones **el mismo código de color**, para que el tribunal reconozca cada parte cuando vuelve |
| Mostrará el software en vivo | Una sola lámina «EduFEM» que hace de mapa de la demostración, más una lámina «Demostración en vivo» con el guion de la demo y un recorrido de respaldo con capturas reales (sirve para el video y por si el equipo de la sala falla). No se repiten en láminas las funciones que se mostrarán en vivo |
| Video de 30 minutos | Narración de ≈ 4300 palabras (presupuesto por lámina en el § 5); se mide después de sintetizar la voz y se ajusta |

## 2. Reglas de contenido (no negociables)

1. **Fidelidad a final4.** Toda cifra, cita, rótulo y afirmación sale del documento. Problema,
   objetivo general, objetivos específicos e hipótesis se escriben **idénticos** al documento
   (Introducción; `capitulos_final4/CRITERIOS.md`, § 1). Las cifras van con coma decimal y con las
   mismas decimales que las tablas.
2. **Prohibido** (CRITERIOS de final4):
   - decir que los criterios o umbrales se fijaron «de antemano» o «antes de medir» (hallazgo H4:
     ningún umbral precede a las primeras corridas; se dice «criterios con umbral explícito»,
     «escritos en los guiones de prueba», y el veredicto descansa en el **margen**);
   - decir que las soluciones manufacturadas verifican la matriz constitutiva o «los dos estados
     planos» (H1): sí se puede decir que las cuatro configuraciones (cuadrado y distorsionado, en
     tensión y en deformación plana) dan las mismas tasas;
   - afirmar efectos sobre el estudiante (aprende, comprende mejor, forma su criterio…): el
     estudiante solo aparece con verbos de posibilidad («puede seguir, comprobar, rehacer»);
   - «ejemplo canónico» (es **ejemplo guía**), «validez de contenido», «tabla de especificaciones»,
     «grado» de la transparencia, «Conclusión 1/2/3», «Aportes del trabajo» como sección,
     «predica» (es «atribuye»).
3. **Términos**: procedimiento de cálculo; módulo educativo; comprobador de salud; casos de
   estudio; cobertura de contenido; tensión (no esfuerzo); lienzo; memoria de cálculo (minúscula);
   GDL; MEF.
4. **Citas** con el número de la lista de final4: [1] Zienkiewicz, [2] Cook, [3] Pérez-Santiago y
   Campos, [4] Bathe, [5] Reddy, [6] ED-Elas2D (Suárez et al.), [7] García-Córdoba, [8] Álvarez de
   Zayas, [9] Lee, [10] Bishay, [13] Hevner, [14] Timoshenko y Goodier, [15] Hughes, [16] Oñate,
   [17] Lee y Ryu, [18] SAP2000 (CSI), [20] Oberkampf y Roy, [21] Salari y Knupp, [23]
   Hernández-Sampieri, [24] Peffers, [25] Wieringa, [26] Štembera y Füssl. Con página cuando la
   tesis la da.
5. **Rótulo de fuente** (`data-sec` del `.rotulo`): la sección, tabla o figura de **final4** de
   donde sale la lámina (numeración en `etiquetas_final4.tsv`): p. ej. «§ 3.5 · Tabla 3.4 ·
   Figura 3.4». El pie lo muestra como «Tesis: …».
6. **Lenguaje llano en el software**: ni una palabra de programación. Si hace falta decir que lo
   que muestran los módulos es lo que el motor calcula: «una versión del cálculo escrita para
   leerse paso a paso, que una prueba automática mantiene coincidente con la que resuelve» (la tesis
   dice «coincidente», con error relativo ≤ 10⁻⁹: no «idéntica»).
7. **Lenguaje del MEF**: los términos del método se usan (es una defensa de ingeniería), pero
   cada uno con media línea en llano la primera vez que aparece en la narración.

## 3. Diseño visual

- **Aspecto principal: versión 2** (estilo PowerPoint: lámina blanca, título azul marino en
  Calibri/Carlito, acento naranja; `assets/css/estilo_ppt.css`). La versión 1 (oscura) sale del
  mismo HTML y debe seguir leyéndose: colores siempre con variables CSS (`var(--texto)`,
  `var(--h-vi)`…), nunca hex sueltos en las láminas.
- **Código de color de la hipótesis y las variables** (`assets/css/l4_comun.css`), el mismo de las
  Figuras 2.1 y CR.1 de la tesis: `--h-vi` azul (variable independiente, antecedente), `--h-vd`
  violeta (variable dependiente, efecto), `--h-int` naranja (interviniente: condición e
  intervención, EduFEM), `--h-ok` verde (se cumple / respaldada), `--h-mal` rojo (el problema).
  Clases: `.h-vi .h-vd .h-int .h-ok .h-mal`, `.l4-sello` (`.grande`), `.l4-parte`.
- Lienzo de 1920 × 1080. Cabecera arriba (rótulo + título, la pone el HTML); pie abajo (lo pone
  el motor). El cuerpo útil va de y ≈ 200 px a y ≈ 1000 px.
- **Tamaños** (Taller 6: títulos ≥ 28 pt, texto ≥ 24 pt, en una lámina de 540 pt de alto = 2 px por
  pt): texto de lectura 36–48 px; secundario 28–32 px; rótulos de diagramas ≥ 24 px; nada por debajo
  de 22 px salvo notas de pie de figura.
- **Más visual, menos texto**: en pantalla, a lo sumo ~30 palabras nuevas por paso (salvo los
  enunciados formales). Lo que se dice en voz no se escribe entero en la lámina. Números grandes,
  íconos, diagramas, colores con significado.
- **Animación con sentido**: cada paso revela, traza, transforma o compara algo; nada de
  movimiento decorativo gratuito. Duración de una transición de paso: 0,6–3,5 s. Movimiento
  continuo (bucles) con `EF.bucle`, discreto y sin distraer de la voz.

## 4. Convenciones técnicas

**Motor**: el de final3, sin cambios salvo los bloques (`assets/js/deck.js`, documentado en su
cabecera). Pasos con `data-paso`, `data-hasta`, `data-solo`, `data-entrada`, `data-clase-paso`;
`data-pasos="N"` en la `<section>` cuando los pasos los maneja una visualización. Fórmulas con
`data-tex="…"` (KaTeX). Visualizaciones: `<div data-viz="nombre">` + `EF.registrarViz(nombre, f)`
que devuelve `{entrar(p, op), paso(k, op), salir(), redimensionar(), tema()}`.

**Toda animación pasa por `EF.tween` / `EF.bucle`** (`assets/js/nucleo.js`): el video se graba con
un reloj virtual. Prohibido `setTimeout`, `setInterval`, `requestAnimationFrame` propios,
transiciones o `@keyframes` CSS para lo que cambia en pantalla, y `Math.random()` en lo que se
dibuja.

**Archivos de cada grupo** (nadie edita los de otro grupo):

| Grupo | Láminas (archivos `laminas/NN_id.html`) | JS / CSS propios |
|---|---|---|
| intro | portada, sep-intro, caja-negra, problema, objetivos, metodo, sep-cap1, sep-cap2, sep-cap3, sep-conclusiones, cierre | `viz/l4_intro.js`, `l4_intro.css` |
| alcance | alcance, plano | `viz/l4_alcance.js`, `l4_alcance.css` |
| hipotesis | hipotesis, contraste | `viz/l4_hipotesis.js`, `l4_hipotesis.css` |
| formulacion | estado-arte, formulacion, procedimiento | `viz/l4_formulacion.js`, `l4_formulacion.css` |
| software | evaluacion, software, trazabilidad, demo | `viz/l4_software.js`, `l4_software.css` |
| resultados | mms, timoshenko, cook, cobertura, leccion | `viz/l4_resultados.js`, `l4_resultados.css` |
| conclusiones | objetivos-cumplidos, margen, respuesta, recomendaciones | `viz/l4_conclusiones.js`, `l4_conclusiones.css` |
| respaldo | r-calculo-manual, r-umbrales, r-educativo, r-deformacion-plana, r-apoyos, r-escalabilidad, r-consistencia, r-licencia | `viz/l4_respaldo.js`, `l4_respaldo.css` |

Imágenes nuevas: `assets/img/l4/<grupo>_*.png`. Ya están: `assets/img/l4/anexoG4_p167…p175.png`
(las hojas del Anexo G de final4) y todas las de `assets/img/` (capturas del software, módulos
M0–M7, `fig_fases_lienzo_ancho.png`, `fig_timoshenko_contorno.png`, `fig_postproceso.png`, logo,
escudo, QR). Videos: `assets/video/tension_deformacion_plana.mp4` y
`assets/video/cantilever_q4_q9.mp4` (viz `video`, `data-src`).

**Biblioteca heredada** (se puede leer y copiar, **no editar**): `assets/js/viz/comunes.js`
(`portada`, `separador`, `video`), `intro.js` (`cajanegra`, `relacion-variables`), `teoria.js`
(`portico`, `procedimiento`, `iso`, `jacobiano`, `gauss`, `recuperacion`, `convergencia-idea`),
`diseno.js` (`casos`, `criterios`, `ensamblaje`, `postproceso`, `memoria`, `trazar`),
`resultados.js` (`timoshenko`, `cook`, `cobertura49`), `analisis.js` (`leccion`, `margen-cr2`,
`calculo-manual`, `margenes`, `dp`). Una viz heredada se puede usar tal cual si sus pasos
coinciden con los de la lámina nueva; si no, se copia a la viz del grupo con otro nombre y se
adapta. Los datos del motor están en `assets/data/datos_edufem.js` (`window.EDUFEM_DATOS`: ejemplo
guía completo, Cook Q4/Q9 N = 2…32, Timoshenko, MMS). Las gráficas de la tesis, en
`assets/data/figuras_doc.js` con su viz `figdoc` (`assets/js/viz/figdoc.js`, documentada en su
cabecera).

**PowerPoint**: el `.pptx` se genera después desde la versión 2 (`extraer_pptx.mjs`): el texto
HTML pasa a formas editables, SVG y lienzos a imágenes, y lo que se anima en un paso se graba como
video de ese paso. Por eso: texto como HTML real (no dentro de SVG ni de canvas) cuando sea
lectura; botones o controles interactivos solo con clase `solo-vivo` (no salen en el video ni en
el PowerPoint) y sin que la lámina dependa de ellos.

**Probar** (desde `tesis/presentacion/final4/`):
```
node herramientas/armar_html.mjs --v2 --solo=<ids separados por coma> --salida=_prueba_<grupo>.html
node herramientas/foto.mjs <carpeta_del_scratchpad> <id>:0 <id>:1 ... --html=_prueba_<grupo>.html --escala=0.5
```
y mirar los PNG (herramienta Read). `foto.mjs` imprime al final los errores de la consola: deben
ser cero. Probar también la versión oscura (sin `--v2`). Borrar los `_prueba_*.html` al terminar.

## 5. Las láminas, una por una

Presupuesto de narración entre corchetes (palabras, ±10 %). Total ≈ 4300 palabras ≈ 30 min con
pausas y animaciones. La narración se escribe para el oído: frases cortas, primera persona del
autor cuando corresponde («comparé», «elegí»), sin leer la lámina. Un texto por paso (paso 0, 1,
2…): el número de textos de una lámina es `pasos + 1`. Los borradores de abajo fijan el mensaje y
los datos; cada grupo puede ajustarlos a su animación sin cambiar las cifras ni el sentido.

**La narración vigente es la de `herramientas/narracion/*.json`** (la arma `armar_narracion.py`). Los
borradores de abajo fueron el punto de partida: las dos olas de revisión los ajustaron, y donde
difieran manda el JSON.

### Carátula y agenda

**00 · portada** (grupo intro) · `data-sin-pie` · [60] · 1 texto.
Izquierda: escudo y «Universidad Autónoma «Tomás Frías» · Facultad de Ingeniería · Carrera de
Ingeniería Civil»; «Tesis de grado · Licenciatura en Ingeniería Civil»; título completo (con
«Python» resaltado); «Postulante: Hedy Yhassmany Oyola Sucullani»; «Potosí – Bolivia · octubre de
2026». Derecha: la membrana de Cook en von Mises con los datos del motor (viz heredada `portada`)
y la marca EduFEM con su lema «El procedimiento de cálculo, a la vista». Botones `solo-vivo`:
Comenzar, Índice.
> «Buenos días, señores miembros del tribunal. Mi nombre es Hedy Yhassmany Oyola Sucullani y
> presento la tesis «Desarrollo de software educativo de elementos finitos para el análisis
> estructural empleando el lenguaje de programación Python». Su producto es EduFEM: un software
> libre y en español que muestra, etapa por etapa, cómo se calcula una estructura por el método
> de los elementos finitos.»

**01 · sep-intro** (intro) · separador-agenda · [40].
El hilo conductor como una cadena animada de cinco eslabones: Introducción → Capítulo 1
«Fundamentar» → Capítulo 2 «Desarrollar» → Capítulo 3 «Verificar y validar» → Conclusiones
«Responder». Cada eslabón entra en orden; el de la introducción queda resaltado.
> «La exposición sigue el orden del documento: primero el problema, los objetivos y la hipótesis;
> después, un capítulo por cada objetivo específico; y al final las conclusiones, donde respondo a
> cada objetivo, a las preguntas y a la hipótesis.»

### 01 · Introducción

**02 · caja-negra** (intro) · rótulo «Situación problemática» · 4 pasos (0–3) · [150].
0. Datos (geometría y malla, material, cargas y apoyos) → **caja negra cerrada** → resultado (un
   contorno de colores). La caja «late» oscura.
1. Sobre el resultado aparecen dos preguntas: «¿De dónde sale esta tensión nodal?» y «¿Cierran las
   tensiones de los nodos con las del interior de los elementos?».
2. Dos citas breves: ED-Elas2D [6, p. 246] y el consenso de 67 expertos [3, pp. 1159, 1171].
3. «Un cálculo estructural se entrega con su memoria de cálculo» → **la caja se abre** y deja ver
   las nueve etapas numeradas (sin nombres técnicos todavía).
Se puede partir de la viz heredada `cajanegra`.
> 0 «Hoy, el software comercial de análisis funciona como una caja negra. Se le dan la geometría,
> el material y las cargas, y devuelve un resultado: un mapa de colores con las tensiones. Lo que
> pasa en medio no se ve.»
> 1 «Mirando el programa no se puede saber de dónde sale la tensión de un nodo, ni comprobar si
> coincide con la que se calculó dentro de los elementos.»
> 2 «El antecedente educativo más cercano, ED-Elas2D, lo señalaba ya en 1998: con los programas
> comerciales, el estudiante solo introduce datos e interpreta resultados. Y un consenso de 67
> expertos pide egresados que sepan verificar y validar sus análisis, no solo ejecutarlos.»
> 3 «En la práctica profesional, todo cálculo estructural se entrega con su memoria de cálculo,
> para que otro ingeniero pueda seguirlo y comprobarlo. Este trabajo abre la caja: deja a la
> vista las nueve etapas del cálculo.»

**03 · problema** (intro) · «Formulación del problema» · 3 pasos · [100].
0. El enunciado **exacto**, palabra por palabra: «¿De qué manera la escasa transparencia del
   procedimiento de cálculo del software de análisis por elementos finitos podrá incidir en la baja
   trazabilidad y verificabilidad de ese procedimiento, en la gestión 2026?».
1. Se colorean las variables: VI en **azul** (`--h-vi`) «la escasa transparencia del procedimiento
   de cálculo»; VD en **violeta** (`--h-vd`) «baja trazabilidad y verificabilidad de ese
   procedimiento». Dos fichas: «Causa · variable independiente: la transparencia del procedimiento
   de cálculo» y «Efecto · variable dependiente: la trazabilidad y la verificabilidad del
   procedimiento de cálculo».
2. Las dos definiciones con un ícono animado cada una: **Trazabilidad** (una flecha que recorre
   hacia atrás una cadena de etapas hasta «datos»): «cada resultado puede seguirse hacia atrás,
   etapa por etapa, hasta los datos del modelo»; **Verificabilidad** (un valor contra un patrón, con
   una banda de tolerancia): «cada magnitud puede comprobarse contra un patrón independiente
   —cálculo manual, solución analítica u otro programa— y da conforme dentro de una tolerancia
   explícita».
> 0 lee el problema completo, tal cual.
> 1 «La causa, en azul, es la transparencia del procedimiento de cálculo. El efecto, en violeta,
> es su trazabilidad y su verificabilidad. Esos colores vuelven en toda la exposición.»
> 2 «Trazable quiere decir que cada resultado puede seguirse hacia atrás, etapa por etapa, hasta
> los datos. Verificable, que cada número puede compararse con un patrón independiente —un
> cálculo a mano, una solución exacta u otro programa— y queda dentro de una tolerancia explícita.»

**04 · alcance** (alcance) · «Objeto de estudio y campo de acción · Delimitación · Alcance y
limitaciones» · 4 pasos · [210] · **lámina con énfasis**.
0. **Objeto de estudio** [8, p. 8]: «El análisis de medios continuos en elasticidad lineal plana por
   el MEF» (el procedimiento de cálculo que va del mapeo isoparamétrico a la recuperación de
   tensiones, con Q4 y Q9). **Campo de acción**: «Los medios de cálculo con que ese análisis se
   enseña: el software educativo y la memoria de cálculo».
1. **El embudo del alcance**, animado de lo general a lo particular. Cada nivel se angosta y lo que
   queda fuera sale de escena hacia una columna «Fuera del alcance» (tachado suave, gris):
   - Análisis estructural → solo **sólidos continuos en dos dimensiones** («acepción restringida:
     tensiones y deformaciones de elementos estructurales modelados como medios continuos 2D»).
     Fuera: sistemas de barras (pórticos, cerchas); placas y cáscaras; análisis tridimensional.
   - → **Elasticidad lineal estática**. Fuera: no linealidad del material o geométrica; efectos
     dinámicos o dependientes del tiempo.
   - → **Material elástico, lineal e isótropo** (E, ν).
   - → **Cuadriláteros isoparamétricos Q4 y Q9** (bilineal y bicuadrático). Fuera: triángulos y
     cuadriláteros de ocho nodos (quedan como recomendación).
   - → **EduFEM**: software de escritorio, educativo, en español.
   - Dos límites más en la columna: «malla manual (tablas, dibujo o DXF): sin mallado automático»;
     «validación contra soluciones analíticas, casos clásicos y un software comercial: sin ensayos
     físicos».
2. **Dos idealizaciones** dentro del dominio, con el video `tension_deformacion_plana.mp4`:
   **Tensión plana** (σz = 0): cuerpos delgados cargados en su plano — vigas de gran peralte, muros
   cargados en su plano. **Deformación plana** (εz = 0): cuerpos prismáticos largos — presas, muros
   de contención, túneles: «una rebanada representa todo el sólido».
3. **Delimitación en cuatro planos** (franja): disciplinar (elasticidad lineal plana con Q4 y Q9);
   institucional (formación de grado en ingeniería civil; la Carrera de Ingeniería Civil de la
   UATF, destinataria inmediata); espacial (el aula y la computadora personal, sin laboratorio ni
   licencias); temporal (desarrollo, verificación y validación en la gestión 2026).
> 0 «El objeto de estudio es el análisis de medios continuos en elasticidad lineal plana por el
> método de los elementos finitos. El campo de acción son los medios con que ese análisis se
> enseña: el software educativo y la memoria de cálculo.»
> 1 «El alcance se acota a propósito, para ganar profundidad. Del análisis estructural, el trabajo
> toma solo los sólidos continuos de dos dimensiones: quedan fuera los pórticos y las cerchas, las
> placas, las cáscaras y el análisis tridimensional. El material es elástico, lineal e isótropo, y
> el problema es estático, sin no linealidad ni efectos dinámicos. La malla se discretiza con
> cuadriláteros de cuatro y de nueve nodos, Q4 y Q9.»
> 2 «Dentro de ese dominio caben las dos idealizaciones clásicas: la tensión plana, para cuerpos
> delgados cargados en su plano, como una viga de gran peralte o un muro; y la deformación plana,
> para cuerpos largos como presas, muros de contención o túneles, donde una rebanada representa
> todo el sólido.»
> 3 «Y el problema se delimita en cuatro planos: el disciplinar, que es este dominio; el
> institucional, la formación de grado en ingeniería civil, con la Carrera de la Universidad
> Autónoma Tomás Frías como destinataria; el espacial, el aula y la computadora personal, sin
> licencias; y el temporal, la gestión 2026.»

**05 · plano** (alcance) · «Alcance y limitaciones» · 3 pasos · [110] · **lámina con énfasis**.
0. Tres columnas: **Barra (1D)** — punto de partida habitual; no muestra el mapeo entre
   coordenadas, el Jacobiano como matriz ni la cuadratura en dos direcciones. **Plano (2D)** —
   EduFEM. **Sólido (3D)** — tiene todos los conceptos, pero sus matrices los oscurecen.
1. **El tamaño real de las matrices**, dibujadas a escala como rejillas de celdas que crecen:
   plano, Q4: **D 3 × 3**, **B 3 × 8**, **kₑ 8 × 8**; sólido, hexaedro de ocho nodos: **D 6 × 6**,
   **B 6 × 24**, **kₑ 24 × 24** [2, p. 218]. La de 24 × 24 desborda: «impracticable seguirla paso a
   paso».
2. Remate: «El plano es la dimensión mínima en la que el Jacobiano ya es una matriz y la
   cuadratura recorre dos direcciones, con matrices que todavía se leen. La formulación que EduFEM
   expone en 2D es la misma que rige el 3D: un puente» [1, 4].
> 0 «¿Por qué el plano? Porque la barra, con la que suele empezar la enseñanza, no alcanza para
> mostrar los conceptos centrales del método: el mapeo entre un cuadrado de referencia y el
> elemento real, el Jacobiano o la integración en dos direcciones.»
> 1 «El sólido tridimensional sí los tiene, pero sus matrices los esconden: la rigidez de un solo
> hexaedro tiene veinticuatro por veinticuatro términos. En el plano, la del Q4 tiene ocho por
> ocho.»
> 2 «El plano es la dimensión mínima donde aparece toda la formulación con matrices que todavía
> se pueden leer. Y la formulación que EduFEM expone en el plano es la misma que rige el caso
> tridimensional.»

**06 · objetivos** (intro) · «Objetivos» · 3 pasos · [110].
0. Objetivo general en cuatro tarjetas: Qué «desarrollar un software educativo de elementos finitos
   para el análisis estructural»; Cómo «empleando el lenguaje de programación Python»; Por qué
   «debido a la escasa transparencia del procedimiento de cálculo del software de análisis» (azul);
   Para qué «para mejorar la trazabilidad y la verificabilidad del procedimiento de cálculo»
   (violeta).
1. El enunciado completo, con su primera parte resaltada: «el título de la tesis está dentro del
   objetivo general».
2. Tres objetivos específicos en escalera, cada uno con su capítulo: 1 **Fundamentar** (Cap. 1),
   2 **Desarrollar** (Cap. 2), 3 **Verificar y validar** (Cap. 3), con el texto completo de cada uno
   (Introducción, «Objetivos específicos»). Nota: «Cada capítulo lleva por título su objetivo».
> 0 «El objetivo general responde a cuatro preguntas: qué, desarrollar un software educativo de
> elementos finitos para el análisis estructural; cómo, empleando el lenguaje Python; por qué, por
> la escasa transparencia del procedimiento de cálculo del software de análisis; y para qué, para
> mejorar su trazabilidad y su verificabilidad.»
> 1 «Su primera parte es, palabra por palabra, el título de la tesis.»
> 2 «Tres objetivos específicos lo concretan, uno por capítulo: fundamentar el método y el estado
> del arte, para fijar los requisitos; desarrollar EduFEM, para exponer el procedimiento etapa por
> etapa; y verificarlo y validarlo, para establecer si ese procedimiento es trazable y verificable.»

**07 · hipotesis** (hipotesis) · «Hipótesis · Variables · Figura 2.1 · Preguntas de investigación»
· 4 pasos · [190] · **lámina con énfasis** (vuelve en 42 · contraste).
0. El enunciado **exacto**, entrando palabra por palabra: «Bajo la aplicación de un método de
   diseño de software educativo, el desarrollo de EduFEM permitirá mejorar la trazabilidad y la
   verificabilidad del análisis por el Método de los Elementos Finitos en elasticidad plana, dada
   la escasa transparencia con que el software expone su procedimiento de cálculo.»
1. Las **cuatro partes** se subrayan con su color y su rótulo (`.l4-parte`): **Condición**
   (naranja, interviniente) «Bajo la aplicación de un método de diseño de software educativo»;
   **Intervención** (naranja, interviniente) «el desarrollo de EduFEM»; **Efecto** (violeta,
   dependiente) «permitirá mejorar la trazabilidad (a) y la verificabilidad (b) del análisis…»;
   **Antecedente** (azul, independiente) «dada la escasa transparencia con que el software expone su
   procedimiento de cálculo». Nota pequeña: «el software» del antecedente es el de uso corriente,
   no EduFEM.
2. **Figura 2.1 animada** (la de la tesis, `tesis/capitulos_final4/figuras/fig_relacion_variables.pdf`;
   PNG de referencia en `...\scratchpad\figs\fig_relacion_variables.png`): círculo azul
   «Transparencia del procedimiento de cálculo» (niveles: caja negra | a la vista), círculo violeta
   «Trazabilidad y verificabilidad del procedimiento de cálculo» (niveles: baja | alta), flecha
   roja del problema («la escasa transparencia (caja negra) incide en la baja trazabilidad y
   verificabilidad»), caja naranja «EduFEM, desarrollado bajo un método de diseño de software
   educativo», flechas de la intervención; los niveles **conmutan**: caja negra → a la vista, baja →
   alta.
3. Las **dos preguntas** cuelgan de las dos cláusulas del efecto: **PI-1 (a) trazabilidad** «¿Qué
   organización del software permite seguir cada resultado hasta sus datos, etapa por etapa, sobre
   el modelo del usuario, y cubrir el contenido que exige un consenso publicado de expertos?»;
   **PI-2 (b) verificabilidad** «¿Reproduce el motor, dentro de tolerancias explícitas, las
   soluciones exactas, las referencias externas y los fenómenos numéricos que predice la teoría?».
   Remate: «El efecto es la parte que puede resultar falsa: cada cláusula lleva criterios con
   umbral».
> 0 «La hipótesis, en el enunciado que fijó el tribunal, dice: bajo la aplicación de un método de
> diseño de software educativo, el desarrollo de EduFEM permitirá mejorar la trazabilidad y la
> verificabilidad del análisis por el método de los elementos finitos en elasticidad plana, dada
> la escasa transparencia con que el software expone su procedimiento de cálculo.»
> 1 «Tiene cuatro partes. En naranja, la condición, que es el método de diseño, y la intervención,
> el desarrollo de EduFEM. En violeta, el efecto: mejorar la trazabilidad y la verificabilidad. Y en
> azul, el antecedente: la escasa transparencia del software de uso corriente.»
> 2 «Así se relacionan las tres variables. La caja negra incide en la baja trazabilidad y
> verificabilidad: ese es el problema. EduFEM, la variable interviniente, pone el procedimiento a la
> vista, y la hipótesis predice que con ello ambas propiedades pasan de bajas a altas.»
> 3 «De las dos cláusulas del efecto salen las dos preguntas de investigación: la primera, por la
> trazabilidad; la segunda, por la verificabilidad. Y como el efecto es la parte que puede resultar
> falsa, cada cláusula lleva criterios con un umbral explícito.»

**08 · metodo** (intro) · «Metodología de la investigación · § 2.1.1 · Tabla 2.1» · 2 pasos · [80].
0. Cuatro fichas: Finalidad **propositiva**; Naturaleza **investigación tecnológica** [7, p. 91];
   Enfoque **cuantitativo** [23, p. 6]; Nivel **descriptivo y comparativo**.
1. **Ciencia del diseño** [13, pp. 75, 83]: el ciclo de las seis actividades [24, pp. 52–56], que se
   recorre animado, con el OE de cada una (Tabla 2.1): 1 Identificar el problema — 2 Definir los
   objetivos de la solución (OE1: cinco requisitos) — 3 Diseñar y desarrollar (OE2) — 4 Demostrar
   (OE3: ejemplo guía y tres casos) — 5 Evaluar (OE3: criterios de aceptación y veredicto) — 6
   Comunicar (documento, repositorio, instalador); «Base de conocimiento: Capítulo 1 (OE1)». Remate:
   «Validación de laboratorio: escenarios controlados, sin sujetos [25, pp. 30–31]».
> 0 «Por su finalidad, el trabajo es propositivo; por su naturaleza, una investigación tecnológica;
> su enfoque es cuantitativo y su nivel, descriptivo y comparativo.»
> 1 «El método es el de la ciencia del diseño: el conocimiento se obtiene construyendo el producto
> y evaluándolo con rigor. Sus seis actividades ordenan el trabajo, y cada una responde a un
> objetivo específico. Es una validación de laboratorio: escenarios controlados, sin sujetos.»

### 02 · Capítulo 1 · Fundamentar

**10 · sep-cap1** (intro) · separador · [22]. «Capítulo 1 · Fundamentar» + el objetivo específico
1 completo, en pequeño. Que se vea en qué eslabón de la cadena del 01 estamos.
> «El primer capítulo cumple el primer objetivo: fundamentar el método y el estado del arte, para
> fijar los requisitos de la herramienta.»

**11 · estado-arte** (formulacion) · «§ 1.1 · Tabla 1.1 · § 2.2.1» · 4 pasos · [160].
0. La matriz de ocho atributos × cinco recursos (ED-Elas2D [6]; analizador de cerchas [10];
   VisualFEA, simuladores [9, 17]; bibliotecas CALFEM y FEniCS; software comercial SAP2000 [18],
   ANSYS, Abaqus), con íconos (✓ sí · ◐ parcial · ✗ no · «no consta» gris · raya) y un rótulo
   breve por celda. **Las celdas son exactamente las de la lámina `estado-arte` de final3**
   (`../archivo/final3/Defensa_EduFEM.html`, auditada contra la Tabla 1.1) — reutilizarlas.
1. Entra la columna **EduFEM** (todo ✓).
2. Se iluminan las dos filas del **vacío**: memoria de cálculo; verificación y validación
   publicada: «ningún recurso didáctico revisado documenta una memoria reproducible a mano ni una
   verificación y validación publicada con la herramienta».
3. La matriz se repliega y de ella salen los **cinco requisitos** (§ 2.2.1), cada uno con su
   dimensión: 1 procedimiento completo a la vista sobre el modelo del usuario (trazabilidad);
   2 memoria de cálculo reproducible a mano (trazabilidad y verificabilidad); 3 exactitud verificada
   y validada, publicada con la herramienta (verificabilidad); 4 cobertura del contenido que exige
   un consenso de expertos (trazabilidad del contenido); 5 libre y en español (los pone al alcance
   del estudiante). Franja final: los **cuatro principios** que orientan cómo exponer (§ 1.2):
   visibilidad del procedimiento · interactividad con vínculo al modelo · construcción paso a paso
   · conexión entre fundamento y operación.
> 0 «Comparé los recursos para enseñar el método en ocho atributos: idioma, licencia, continuo
> plano, cálculo paso a paso sobre el modelo, procedimiento completo, memoria de cálculo,
> fenómenos numéricos y verificación publicada. Cada recurso cubre algunos: ED-Elas2D, el continuo
> y el paso a paso; los simuladores de VisualFEA, también los fenómenos numéricos; las bibliotecas,
> la licencia libre. El software comercial es una caja negra.»
> 1 «Ninguno reúne los ocho. Esa es la brecha que EduFEM se propone cubrir.»
> 2 «El vacío se concentra en dos filas: ningún recurso didáctico revisado documenta una memoria
> de cálculo reproducible a mano ni una verificación y validación publicada junto con la
> herramienta.»
> 3 «De esa brecha salen cinco requisitos: el procedimiento completo a la vista, una memoria
> reproducible a mano, una exactitud verificada y publicada, la cobertura del contenido que exigen
> los expertos, y un software libre y en español. Y cuatro principios, tomados de la literatura,
> orientan cómo exponerlo.»

**12 · formulacion** (formulacion) · «§ 1.3» · 4 pasos · [300] · **lámina con énfasis**.
Lo que la tesis dice (§ 1.3, ecuaciones de equilibrio, de trabajos virtuales y del sistema
global): el MEF parte de la **forma débil o variacional**, que se obtiene multiplicando la
ecuación de equilibrio por un campo de **desplazamientos virtuales** δu admisible (nulo en los
apoyos) e integrando por partes; eso conduce al **principio de los trabajos virtuales**
[1, pp. 69–71; 15, pp. 77–79; 5, pp. 612–613]:
∫Ω δεᵀσ dΩ = ∫Ω δuᵀb dΩ + ∫Γt δuᵀt dΓ. «En palabras: el miembro izquierdo es el trabajo que
realizan las tensiones internas en una deformación virtual cualquiera, y el derecho, el que
realizan las cargas de volumen y de borde en el desplazamiento virtual que la produce. Exigir esa
igualdad para todo desplazamiento virtual admisible equivale a exigir el equilibrio en todo el
dominio.» La forma débil solo contiene derivadas primeras: basta un campo continuo entre
elementos; u ≈ N uₑ; sustituyendo y aprovechando la arbitrariedad de δu se llega a K u = F.
0. **Del pórtico a la chapa**: a la izquierda, un pórtico: cada barra con su rigidez «en forma
   cerrada» que entra a K (se puede partir de la viz heredada `portico`); a la derecha, una chapa
   dividida en elementos: «su rigidez no se escribe: se obtiene integrando sobre el área». Las dos
   terminan en **K u = F**.
1. **Equilibrio punto por punto (forma fuerte)**: ∇·σ + b = 0 en Ω, con un elemento diferencial
   cuyas tensiones se equilibran. Nota: «pide derivadas segundas continuas en todo el cuerpo».
2. **El desplazamiento virtual** (el corazón de la lámina): la chapa, con su apoyo y su carga, se
   deforma en un movimiento **imaginario** pequeño (contorno punteado que oscila), siempre nulo en
   el apoyo; dos medidores animados: **trabajo de las cargas** (externo, δuᵀ·carga) y **trabajo de
   las tensiones** (interno, δεᵀ·σ), que suben y bajan **juntos** mientras cambian varios
   desplazamientos virtuales; una balanza que siempre queda nivelada. Una viñeta pequeña de
   analogía: la palanca de la estática, P₁·δ₁ = P₂·δ₂, rotulada «analogía». Abajo, la ecuación de
   trabajos virtuales con los dos miembros coloreados como los medidores. Mensaje: «para cualquier
   desplazamiento virtual compatible con los apoyos, trabajo interno = trabajo externo ⇔
   equilibrio».
3. **Por qué conviene**: «solo derivadas primeras → basta interpolar dentro de cada elemento». La
   chapa se divide en elementos y se enciende la cadena: u ≈ N uₑ (funciones de forma) → ε = B uₑ →
   σ = D ε → kₑ = ∫ Bᵀ D B t dA → ensamblaje → **K u = F** (el mismo sistema del pórtico).
> 0 «El punto de partida es familiar para un ingeniero civil. En un pórtico, cada barra tiene una
> rigidez conocida, que se escribe con una fórmula cerrada; se ensamblan, y se resuelve K por u
> igual a F. Un trozo de chapa, en cambio, no tiene fórmula: su rigidez hay que obtenerla
> integrando sobre su área.»
> 1 «El equilibrio de un sólido se escribe primero punto por punto: es la forma fuerte. Pero exige
> que el desplazamiento tenga derivadas segundas continuas en todo el cuerpo, algo difícil de
> cumplir con una aproximación por trozos.»
> 2 «Por eso el método parte de la forma débil, que en elasticidad es el principio de los trabajos
> virtuales. La idea es la misma de la estática: se imagina un desplazamiento pequeño, compatible
> con los apoyos, y se exige que el trabajo de las tensiones internas iguale al trabajo de las
> cargas. Si esa igualdad se cumple para cualquier desplazamiento virtual, el cuerpo está en
> equilibrio en todo su dominio.»
> 3 «La ventaja es que solo pide derivadas primeras, y entonces basta interpolar el desplazamiento
> dentro de cada elemento con funciones de forma. De ahí salen la matriz B, que convierte
> desplazamientos en deformaciones; la matriz D, que las convierte en tensiones; y la rigidez de
> cada elemento, como la integral de B transpuesta por D por B. Al ensamblar los elementos se llega
> al mismo sistema del pórtico: K por u igual a F.»

**13 · procedimiento** (formulacion) · «§ 1.5 a § 1.11 · § 2.1.2» · 4 pasos · [180].
Una pista horizontal con las **nueve etapas** numeradas y su símbolo (1 N mapeo isoparamétrico ·
2 J Jacobiano · 3 B matriz de deformación · 4 D matriz constitutiva · 5 kₑ rigidez por cuadratura
de Gauss · 6 f fuerzas nodales equivalentes · 7 K ensamblaje · 8 u restricciones y solución · 9 σ
recuperación de tensiones). Arriba, un escenario grande que cambia por grupo de etapas, sobre el
**elemento E3 del ejemplo guía** (datos en `EDUFEM_DATOS`):
0. Etapas 1–3 (geometría): el cuadrado natural (ξ, η) se deforma hasta el elemento real; el
   Jacobiano como factor de área (det J); B, de desplazamientos a deformaciones.
1. Etapas 4–5 (material y rigidez): D según tensión o deformación plana; kₑ como suma de los
   aportes de los puntos de Gauss (2 × 2 en Q4, 3 × 3 en Q9), la matriz llenándose punto por punto.
2. Etapas 6–8 (del elemento a la estructura): una carga repartida que se convierte en fuerzas
   nodales; cada kₑ que cae en su lugar de K; los apoyos; u.
3. Etapa 9 (tensiones): de los puntos de Gauss a los nodos y el promedio entre vecinos. Debajo de
   cada etapa, una ficha de dónde se ve en EduFEM: M1…M7 para las siete primeras; post-proceso
   para 8 y 9; memoria para las nueve.
Partir de las viz heredadas `iso`, `gauss`, `ensamblaje`, `recuperacion` (copiándolas al grupo).
> 0 «Ese cálculo se organiza en nueve etapas. Las tres primeras son geométricas: el mapeo lleva un
> cuadrado de referencia al elemento real; el Jacobiano mide cuánto se estira y gira ese cuadrado;
> y la matriz B traduce desplazamientos en deformaciones.»
> 1 «Las dos siguientes traen el material y la rigidez. La matriz D depende de si el caso es de
> tensión o de deformación plana. Y la rigidez del elemento se integra numéricamente, sumando su
> aporte en los puntos de Gauss: dos por dos en el Q4 y tres por tres en el Q9.»
> 2 «Después, el cálculo pasa del elemento a la estructura: las cargas repartidas se convierten en
> fuerzas en los nodos, cada elemento entra en su lugar de la matriz global, se imponen los apoyos
> y se resuelve el sistema.»
> 3 «La última etapa recupera las tensiones: se calculan en los puntos de Gauss, se extrapolan a los
> nodos y se promedian entre los elementos vecinos. Cada una de las nueve etapas tiene en EduFEM un
> lugar donde verse.»

### 03 · Capítulo 2 · Desarrollar

**20 · sep-cap2** (intro) · separador · [20]. «Capítulo 2 · Desarrollar» + OE2.
> «El segundo capítulo cumple el segundo objetivo: desarrollar EduFEM. Primero, cómo se iba a
> contrastar la hipótesis; después, el software.»

**21 · evaluacion** (software) · «§ 2.1.2 a § 2.1.6 · Tablas 2.2 y 2.4» · 3 pasos · [190].
0. **Qué se mide**. VI (azul): dos niveles, caja negra ↔ procedimiento a la vista («presencia frente
   a ausencia»). VD (violeta) en sus dos dimensiones: **trazabilidad = contar lo expuesto** (etapas
   con módulo, etapas en la memoria, fases en un lienzo, contenidos de los expertos con
   instrumento, datos que entran y salen sin pérdida) con la imagen de una **cadena que se rompe
   en su eslabón más débil**; **verificabilidad = medir errores** (tasas de convergencia, error
   frente a la analítica, diferencia frente a SAP2000, equilibrio, Cook y bloqueo, memoria rehecha
   a mano).
1. **Los casos de estudio**, cuatro tarjetas con imagen: Soluciones manufacturadas (solución exacta
   construida; cuatro configuraciones; N = 2…32); Viga de Timoshenko (solución analítica [14] y
   SAP2000 [18]; Q9 56 × 8); Membrana de Cook (distorsión y bloqueo del Q4; referencia 23,96);
   Ejemplo guía (nueve nodos y cuatro elementos Q4; su memoria se rehace a mano, Anexo G).
2. **Los criterios** (Tabla 2.4): 15 criterios con umbral explícito — 6 de trazabilidad, 9 de
   verificabilidad —; los numéricos, escritos en los guiones de prueba, que terminan con error si
   uno falla; cada uno dice qué resultado lo refutaría. **Regla conjuntiva**: comprobada si las
   premisas se respaldan y se cumplen las dos cláusulas; parcial si se cumple una; no comprobada si
   ninguna. (Sin «fijados de antemano».)
> 0 «La variable independiente tiene dos niveles: caja negra o procedimiento a la vista. La
> trazabilidad se mide contando lo que queda expuesto, porque la cadena se rompe en su eslabón más
> débil: basta una etapa oculta para que el resultado ya no pueda seguirse hasta sus datos. La
> verificabilidad se mide con errores frente a referencias de exactitud conocida.»
> 1 «Para eso elegí tres casos de estudio, cada uno con una referencia distinta: las soluciones
> manufacturadas, una solución exacta construida a propósito; la viga de Timoshenko, con su
> solución analítica y un modelo en SAP2000; y la membrana de Cook, un clásico donde el Q4 se pone
> en aprietos. Se suma un ejemplo guía de cuatro elementos, cuya memoria se rehace a mano.»
> 2 «Cada cláusula se juzga con criterios de umbral explícito: seis para la trazabilidad y nueve
> para la verificabilidad. Los numéricos están escritos en los propios guiones de prueba, que fallan
> si uno no se cumple, y cada criterio dice qué resultado lo refutaría. La regla es conjuntiva: la
> hipótesis queda comprobada solo si sus premisas se respaldan y se cumplen las dos cláusulas.»

**22 · software** (software) · «§ 2.2 · Tabla 3.6 · Figura 3.5» · 3 pasos · [160] · **sin
tecnicismos de programación**.
0. **Un lienzo, tres fases** (la Figura 3.5: `assets/img/fig_fases_lienzo_ancho.png`, o las
   capturas por separado), con llamadas animadas: **Pre-proceso** — el modelo se dibuja o se
   escribe en tablas; el comprobador de salud revisa los datos antes de resolver. **Proceso** — los
   módulos educativos sobre el elemento elegido. **Post-proceso** — colores de tensión, deformada,
   sonda en cualquier punto con su círculo de Mohr, reacciones.
1. **Ocho módulos** (M0 calidad de malla, M1 mapeo isoparamétrico, M2 Jacobiano, M3 matriz B, M4
   matriz D, M5 rigidez y puntos de Gauss, M6 fuerzas equivalentes, M7 ensamblaje), en galería con
   sus capturas `assets/img/fig_modulo_m0…m7.png`, uno por etapa.
2. **La memoria de cálculo**: hojas que se abren en abanico (`assets/img/l4/anexoG4_p*.png`): «el
   cálculo completo en un PDF, con los números del modelo sustituidos paso a paso, para rehacerlo a
   mano o en una hoja de cálculo». Franja: libre · en español · instalador que no pide nada más.
> 0 «EduFEM organiza el análisis en las tres fases del software profesional, sobre un mismo
> lienzo. En el pre-proceso, el modelo se dibuja o se escribe en tablas, y un comprobador revisa los
> datos antes de resolver. En el proceso se abren los módulos educativos. Y en el post-proceso se
> leen los colores de tensión, la deformada y, con una sonda, el estado de tensión de cualquier
> punto, con su círculo de Mohr.»
> 1 «Los ocho módulos, de M0 a M7, se abren sobre el elemento que el usuario elige en su propio
> modelo: cada uno ilumina una etapa del cálculo, con los números de ese elemento.»
> 2 «Y la memoria de cálculo reconstruye todo el procedimiento en un PDF, con los valores del
> modelo sustituidos paso a paso, para rehacerlo a mano o en una hoja de cálculo, como la memoria
> que acompaña a cualquier proyecto. Todo es libre, está en español y se instala sin requisitos
> adicionales.»

**23 · trazabilidad** (software) · «§ 2.1.2 · Anexo G» · 4 pasos · [140].
Recorrido hacia atrás sobre el ejemplo guía (viz heredada `trazar`, adaptada a 4 pasos; **verificar
cada cifra contra el Anexo G de final4**, `assets/img/l4/anexoG4_p*.png` y el texto de la tesis):
0. El resultado: σ_VM en el nodo 7 = 864,70 (Tabla G.7).
1. El camino hacia atrás, animado etapa por etapa (9 → 1): tensiones en los puntos de Gauss ←
   desplazamientos ← sistema resuelto ← ensamblaje ← kₑ ← B ← J ← mapeo.
2. Los datos del modelo, al final del camino (material, espesor, carga P = 1000 en el nodo 7,
   apoyos en los nodos 1, 3 y 6 — confirmar con el Anexo G).
3. «La memoria lo deja por escrito»: las hojas del Anexo G (pp. 167–175) se apilan, con la que
   corresponde resaltada.
> 0 «Así se ve la trazabilidad en el ejemplo guía. Elijo un resultado: la tensión de von Mises del
> nodo 7, 864,70.»
> 1 «Y lo sigo hacia atrás, etapa por etapa: viene de las tensiones en los puntos de Gauss, que
> vienen de los desplazamientos, que salen del sistema resuelto; el sistema, del ensamblaje; y cada
> aporte, de la rigidez de su elemento, de su matriz B, de su Jacobiano y de su mapeo.»
> 2 «Al final del camino están los datos del modelo: el material, el espesor, la carga de mil en el
> nodo 7 y los apoyos. Ninguna etapa queda escondida.»
> 3 «La memoria de cálculo deja ese mismo camino por escrito, con los números sustituidos: es el
> Anexo G de la tesis, y puede rehacerse con lápiz y papel.»

**24 · demo** (software) · «Demostración» · 2 pasos · [75].
0. Guion de la demostración, cinco pasos numerados con ícono: cargar el ejemplo guía; comprobar y
   resolver; abrir un módulo sobre un elemento; consultar un nodo con la sonda; generar la memoria
   de cálculo. Botones `solo-vivo` hacia el respaldo.
1. **Recorrido de respaldo** (para el video y por si el equipo de la sala falla): capturas reales
   que se suceden con un acercamiento suave (pre-proceso `fig_lienzo_lod.png`, módulo
   `fig_modulo_capa.png`, post-proceso `fig_postproceso.png`, hojas de la memoria), cada una con su
   rótulo.
> 0 «Ahora lo muestro en el propio software: cargo el ejemplo guía, lo compruebo y lo resuelvo,
> abro un módulo sobre un elemento, consulto un nodo con la sonda y genero la memoria de cálculo.»
> 1 «En pantalla: el modelo en el pre-proceso, un módulo desplegado sobre el elemento elegido, el
> contorno de tensiones con la sonda en el nodo 7 y las hojas de la memoria que el programa
> genera.»

### 04 · Capítulo 3 · Verificar y validar (resultados y su análisis)

**30 · sep-cap3** (intro) · separador · [20]. «Capítulo 3 · Verificar y validar» + OE3.
> «El tercer capítulo cumple el tercer objetivo: verificar y validar EduFEM, para establecer si su
> procedimiento es trazable y verificable.»

**31 · mms** (resultados) · «§ 3.2 · Tabla 3.1 · Figura 3.1» · 4 pasos · [170].
0. **Verificar = ¿resuelve bien sus ecuaciones?** Idea en una imagen: una solución exacta fabricada
   (u = sen πx · sen πy, v = cos πx · cos πy) y la misma malla refinada N = 2, 4, 8, 16, 32 (mallas
   pequeñas que se dividen).
1. **Figura 3.1 (a), tal cual** (`figdoc`, clave `mms_l2`): se traza la serie Q4 (de la malla
   gruesa a la fina) y su pendiente de referencia O(h²). Llamada: «h ÷ 2 → error ÷ 4: pendiente
   2,00».
2. Se traza la serie Q9 y su O(h³). Llamada: «h ÷ 2 → error ÷ 8: pendiente 3,00».
3. **Figura 3.1 (b)** (`mms_h1`) junto a la (a): pendientes 1,00 (Q4) y 2,00 (Q9). Tabla breve de
   tasas asintóticas (N = 16 → 32): L² 2,00 / 3,00 · H¹ 1,00 / 2,00, con las teóricas. Ficha:
   «cuatro configuraciones (cuadrado y distorsionado, en tensión y en deformación plana): las mismas
   tasas, con diferencias menores que 0,01» (Tabla D.3). Sello: «teórica ± 0,5 · se cumple».
> 0 «Verificar es preguntar si el programa resuelve bien sus ecuaciones. Para eso se fabrica una
> solución exacta, se le pide a EduFEM que la reproduzca en mallas cada vez más finas, y se mide
> cuánto se equivoca.»
> 1 «Esta es la gráfica de la tesis: en el eje horizontal, el tamaño de los elementos; en el
> vertical, el error. Con el Q4, cada vez que el tamaño se reduce a la mitad, el error se divide
> por cuatro: la pendiente es 2,00, la que predice la teoría.»
> 2 «Con el Q9, el error se divide por ocho: pendiente 3,00, también la teórica.»
> 3 «En la seminorma H1, que mide el error de las deformaciones, las pendientes son 1,00 y 2,00,
> otra vez las teóricas. Y las cuatro configuraciones ensayadas, con elementos cuadrados y
> distorsionados, en tensión y en deformación plana, dan las mismas tasas, con diferencias menores
> que una centésima. El criterio, la tasa teórica más o menos medio orden, se cumple.»

**32 · timoshenko** (resultados) · «§ 3.4 · Tablas 3.2 y 3.3 · Figura 3.3» · 3 pasos · [150].
0. **Validar = ¿coincide con referencias externas?** La viga (Figura 3.3,
   `assets/img/fig_timoshenko_contorno.png`): simplemente apoyada, L = 14 m, H = 1,20 m, b = 0,40 m,
   q = 5000 kgf/m, E = 217 370 kgf/cm², ν = 0,20; Q9 56 × 8 (448 elementos, 3842 GDL). Dos
   referencias: solución analítica de Timoshenko y Goodier [14] y SAP2000 [18] (cáscara: «patrón de
   comparación, no de exactitud»). Puntos A, B, C marcados.
1. σx en A, B, C (Tabla 3.2): EduFEM 127,8825 / −37,3410 / −31,8077; analítica 127,8542 / −37,3255 /
   −31,7992; SAP2000 127,8514 / −37,2640 / −31,7852; error anal. 0,02 / 0,04 / 0,03 %; diferencia SAP
   0,02 / 0,21 / 0,07 %; barras contra el umbral del 1 %. Sello «< 1 % · se cumple».
2. Flecha central (Tabla 3.3): 2,03460 cm frente a 2,02926 cm → **0,26 %** (umbral 3 %); con
   Euler-Bernoulli sería 1,85 %. Equilibrio: ΣRy = qL = 70 000 kgf con residuo relativo
   **1,7 × 10⁻¹³** (umbral 10⁻⁸). Sellos.
> 0 «Validar es preguntar si los resultados coinciden con referencias externas. La primera es una
> viga de hormigón simplemente apoyada, de 14 metros de luz y 1,20 de peralte, con 5000 kilos por
> metro, modelada con 448 elementos Q9. Se compara con la solución analítica de Timoshenko y Goodier
> y con un modelo en SAP2000.»
> 1 «En los tres puntos de control, la tensión normal de EduFEM difiere de la analítica, como
> máximo, un 0,04 %, y de SAP2000, un 0,21 %. El umbral era del 1 %.»
> 2 «La flecha central difiere un 0,26 % de la solución que incluye la deformación por cortante;
> frente a la fórmula de Euler-Bernoulli, que la desprecia, la diferencia sería del 1,85 %. Y las
> reacciones equilibran la carga total con un residuo de diez a la menos trece: cero, a efectos
> numéricos.»

**33 · cook** (resultados) · «§ 3.5 · Tabla 3.4 · Figura 3.4» · 4 pasos · [180].
0. La membrana: trapecio (0;0)–(48;44)–(48;60)–(0;44), empotrado a la izquierda, carga tangencial
   unitaria a la derecha; se mide u_y en (48; 52). Referencia **23,96** (corroborada por la
   extrapolación de Richardson ≈ 23,97; publicada 23,965 [26, p. 28]). Malla y deformada con los
   datos del motor (`EDUFEM_DATOS`, viz heredada `cook` como punto de partida).
1. **Figura 3.4, tal cual** (`figdoc`, clave `cook`): con la línea de referencia, se traza la serie
   Q4: «se queda corto: −50,563 % con N = 2; −0,594 % con N = 32».
2. Se traza la serie Q9: «con N = 8: 23,925, error **0,144 %** (umbral 1,5 %)»; «a 578 GDL, el error
   del Q9 es **más de diez veces** menor que el del Q4». Sello.
3. **Por qué**: el bloqueo por cortante (video `cantilever_q4_q9.mp4`: el Q4 no puede curvarse); la
   flecha del Q4 es menor que la del Q9 en las cinco mallas (sello «se observa · se cumple»).
   Contraste externo: Štembera y Füssl [26, p. 28] publican para su cuadrilátero de cuatro nodos
   11,845 · 18,299 · 22,079 · 23,430 · 23,818 — «los mismos valores de EduFEM, hasta la última cifra».
> 0 «La segunda validación es la membrana de Cook: un trapecio empotrado a la izquierda y cargado
> en su borde derecho, que combina flexión, cortante y distorsión. Se mide el desplazamiento
> vertical en el punto medio de su borde derecho, el punto (48; 52), cuyo valor de referencia es 23,96.»
> 1 «Esta es la gráfica del documento. El Q4 se queda corto: con la malla más gruesa subestima la
> respuesta en más de la mitad, y se acerca muy despacio.»
> 2 «El Q9 llega casi enseguida: con ocho elementos por lado, su error es de 0,144 %, muy por
> debajo del umbral del 1,5 %. Con el mismo número de grados de libertad, su error es más de diez
> veces menor que el del Q4.»
> 3 «La razón es el bloqueo por cortante: los bordes del Q4 se mantienen rectos, no pueden
> curvarse, y el elemento resulta demasiado rígido en flexión. EduFEM lo reproduce tal como predice
> la teoría. Además, los cinco valores del Q4 coinciden, hasta la última cifra, con los que publican
> Štembera y Füssl para un elemento de cuatro nodos.»

**34 · cobertura** (resultados) · «§ 3.6 · Tablas 3.6 y 3.7» · 3 pasos · [120].
0. Contadores que suben: **7 de 7** etapas con módulo · **9 de 9** etapas en la memoria · **ambas**
   (solución y tensiones, sin promediar y promediadas) en el post-proceso · **3 de 3** fases en un
   lienzo · **sin pérdida** (el modelo sale y vuelve por hoja de cálculo y CAD; memoria para Q4 y
   Q9). Cada uno con su sello.
1. **18 de 18**: la rejilla de los 49 contenidos del consenso [3, pp. 1162–1163] (15 conceptos FEM, 34
   destrezas FEA); se separan los 31 que quedan fuera (18 fuera del alcance disciplinar, 12
   anteriores al procedimiento, 1 no expuesto: FEM3) y los 18 del universo se marcan uno a uno.
   Partir de la viz heredada `cobertura49`.
2. Nota honesta: «prueba cobertura, no suficiencia ni efecto sobre quien lo usa; el cotejo es del
   autor, con una regla de marcado explícita».
> 0 «Para la trazabilidad, el resultado es un inventario sin huecos: las siete primeras etapas
> tienen su módulo educativo; las nueve, su desarrollo en la memoria de cálculo; la solución y las
> tensiones se muestran en el post-proceso, sin promediar y promediadas; las tres fases comparten
> un lienzo, y el modelo entra y sale de la herramienta sin perder nada.»
> 1 «Y frente al consenso de expertos: de sus 49 contenidos, 18 pertenecen al procedimiento de
> cálculo y a su verificación dentro de este alcance. Los 18 tienen un instrumento en EduFEM.»
> 2 «Esto prueba cobertura, no suficiencia ni efecto sobre quien lo usa, y el cotejo lo hice yo,
> con una regla de marcado explícita.»

**35 · leccion** (resultados) · «§ 3.7.2» · 3 pasos · [110].
0. **Un defecto que las tasas no vieron**: la matriz que lleva las tensiones del Q4 de los puntos
   de Gauss a los nodos estaba escrita para otra numeración de esos puntos; los estudios de
   convergencia del desplazamiento no lo delataron (esa matriz no interviene en el desplazamiento).
1. **La memoria lo delató**: en la memoria del ejemplo guía, las tensiones de los nodos no cerraban
   con las de los puntos de Gauss (visual del elemento E3, con E correcta frente a E mal escrita;
   viz heredada `leccion` como punto de partida).
2. **Se corrigió**, y una prueba de reproducción exacta de campos polinómicos lo detectaría hoy.
   Remate: «Exponer el procedimiento no asegura que sea correcto: fue la trazabilidad la que hizo
   visible el defecto. Por eso la hipótesis no es una tautología».
> 0 «Hubo un inconveniente que vale la pena contar. La matriz que lleva las tensiones del Q4 a los
> nodos estaba escrita para otra numeración de los puntos de Gauss. Las pruebas de convergencia no
> lo vieron, porque esa matriz no interviene en los desplazamientos.»
> 1 «Lo delató la memoria de cálculo: al leerla, las tensiones de los nodos no cerraban con las de
> los puntos de Gauss.»
> 2 «Se corrigió, y hoy una prueba propia lo detectaría. La lección es doble: exponer el
> procedimiento no asegura que lo expuesto sea correcto, y fue precisamente poder leerlo paso a
> paso lo que hizo visible el error. Por eso la hipótesis no es una tautología.»

### 05 · Conclusiones y recomendaciones (el bloque que crece)

**40 · sep-conclusiones** (intro) · separador · [20]. «Conclusiones y recomendaciones» +
«Respuesta a los objetivos, a la hipótesis, al problema y a las preguntas».
> «Paso a las conclusiones, donde respondo a los objetivos, a la hipótesis, al problema y a las
> preguntas de investigación.»

**41 · objetivos-cumplidos** (conclusiones) · «Conclusiones» · 4 pasos · [200].
Tablero: el objetivo general arriba y los tres específicos en tres columnas (Capítulo 1, 2, 3).
Cada tarjeta entra como «objetivo», luego **se da vuelta** y muestra su conclusión breve, su
evidencia (chip) y un sello «cumplido». Contador «3 de 3» que se llena.
0. **Objetivo general — cumplido**: «EduFEM: software educativo de elementos finitos, libre, en
   español, en Python, que expone su procedimiento de cálculo en elasticidad plana con Q4 y Q9».
1. **OE1 Fundamentar**: «De la fundamentación teórica (Capítulo 1) se concluye que el software
   comercial opera como una caja negra y que ningún recurso revisado documenta a la vez los
   atributos que harían trazable y verificable el procedimiento» → chip «Tabla 1.1 → 5 requisitos
   (§ 2.2.1)».
2. **OE2 Desarrollar**: «Del desarrollo de EduFEM (Capítulo 2) se concluye que el software lleva su
   procedimiento a la vista: módulos sobre el modelo del usuario hasta el ensamblaje, post-proceso
   con sus medios de comprobación y memoria con sustitución numérica» → chip «Tabla 3.6 · Figura
   3.5»; aporte: «decisiones de diseño trazadas a sus principios (Tabla 3.8)».
3. **OE3 Verificar y validar**: «De la verificación y la validación (Capítulo 3) se concluye que ese
   procedimiento es trazable y verificable» → chip «Tabla 3.10: 15 de 15 criterios»; aporte: «la
   batería de verificación y validación, reproducible y publicada con el software».
> 0 «El objetivo general se cumplió: EduFEM es un software educativo de elementos finitos, libre,
> en español y escrito en Python, que expone su procedimiento de cálculo en elasticidad plana con
> elementos Q4 y Q9.»
> 1 «De la fundamentación teórica, el primer capítulo, se concluye que el software comercial opera
> como una caja negra y que ningún recurso revisado documenta a la vez los atributos que harían
> trazable y verificable el procedimiento. De esa brecha salieron los cinco requisitos.»
> 2 «Del desarrollo de EduFEM, el segundo capítulo, se concluye que el software lleva su
> procedimiento a la vista: los módulos lo exponen sobre el modelo del usuario hasta el
> ensamblaje, el post-proceso muestra la respuesta con sus medios de comprobación y la memoria
> reconstruye todo con los números sustituidos. Las decisiones de diseño que lo logran, trazadas a
> sus principios, son un aporte reutilizable.»
> 3 «Y de la verificación y la validación, el tercero, se concluye que ese procedimiento es trazable
> y verificable: se cumplen los quince criterios de aceptación. La batería de pruebas, reproducible
> y publicada con el software, es el otro aporte del trabajo.»

**42 · contraste** (hipotesis) · «§ 3.8 · Tabla 3.11 · Figura CR.1» · 5 pasos · [260] · **el
clímax**. Es la Figura CR.1 (PNG de referencia en `...\scratchpad\figs\fig_contraste_hipotesis.png`)
y la Tabla 3.11, animadas. Cinco filas, en el orden de la Figura CR.1, con el **mismo color** que en
la lámina 07: parte (variable) · **antes: caja negra** → **con EduFEM** · veredicto.
0. Aparecen las cinco partes coloreadas (sin el enunciado completo: la lámina 07 ya lo leyó; se puede
   mostrar la línea de la hipótesis en pequeño arriba, con sus partes subrayadas como en la 07).
1. **Premisas** (documentales): **Condición** (naranja) — «ciencia del diseño, aplicada en sus seis
   actividades; cinco requisitos tomados de los antecedentes; cuatro principios, cada uno con su
   decisión de diseño» (Tabla 2.1, § 2.2.1, Tabla 3.8) → **Respaldada**. **Intervención** (naranja)
   — «de caja negra a procedimiento a la vista: módulos M1 a M7, post-proceso y memoria de cálculo
   sobre el modelo del usuario» (Tabla 3.6) → **Respaldada**. **Antecedente** (azul) — en la
   comparación de recursos (Tabla 1.1) el software comercial figura con cálculo paso a paso «Baja
   (caja negra)» y memoria «Informes de resultados, sin el desarrollo matricial» → **Respaldado**.
2. **Efecto (a) trazabilidad** (violeta): antes «solo datos y resultados: ningún resultado se sigue
   etapa por etapa» → con EduFEM, seis criterios que se marcan uno a uno: 7 de 7 · 9 de 9 · ambas ·
   3 de 3 · 18 de 18 · sin pérdida → **Se cumple: 6 de 6**.
3. **Efecto (b) verificabilidad** (violeta): antes «solo se comprueban los resultados finales» → con
   EduFEM, nueve criterios que se marcan: tasa L² · tasa H¹ · flecha · σx analítica · σx SAP2000 ·
   equilibrio · Cook · bloqueo · memoria a mano → **Se cumple: 9 de 9**.
4. **Regla conjuntiva** (premisas respaldadas + (a) + (b)) → el sello grande **«Hipótesis
   comprobada»** cae sobre la lámina. Debajo, el alcance en una línea: «propiedades del software,
   no su uso por estudiantes · contraste externo en tensión plana · evaluación del autor».
> 0 «La hipótesis se contrasta parte por parte, con los mismos colores con que la presenté: la
> condición, la intervención, el efecto en sus dos cláusulas y el antecedente.»
> 1 «Las tres premisas se respaldan con evidencia documental. La condición: el método de la ciencia
> del diseño se aplicó en sus seis actividades, con requisitos tomados de los antecedentes y
> decisiones trazadas a cuatro principios. La intervención: EduFEM lleva el procedimiento de la caja
> negra a la vista. Y el antecedente: la comparación de recursos registra al software comercial como
> una caja negra, con informes sin el desarrollo matricial.»
> 2 «El efecto se juzga con criterios. Trazabilidad: antes, ningún resultado podía seguirse etapa
> por etapa; con EduFEM, siete de siete etapas con módulo, nueve de nueve en la memoria, tres de
> tres fases en un lienzo y dieciocho de dieciocho contenidos. Se cumplen los seis criterios.»
> 3 «Verificabilidad: antes, solo podía comprobarse el resultado final; con EduFEM, las tasas
> teóricas, la solución analítica, SAP2000, el equilibrio, la membrana de Cook, el bloqueo del Q4 y
> la memoria rehecha a mano. Se cumplen los nueve criterios.»
> 4 «Con la regla conjuntiva —premisas respaldadas y las dos cláusulas cumplidas—, la hipótesis
> queda comprobada. Dentro del alcance declarado: se midieron propiedades del software, no su uso
> por estudiantes; los contrastes externos son de tensión plana, y la evaluación la hice yo.»

**43 · margen** (conclusiones) · «Figura CR.2 · Tabla 3.10» · 3 pasos · [100].
0. **Figura CR.2, tal cual** (`figdoc`, clave `margen_cr2`), con los puntos ocultos: ejes, línea del
   umbral, zona «no cumple a la derecha».
1. Los nueve puntos **se deslizan desde el umbral hasta su valor**, uno tras otro (acción
   `deslizar` de `figdoc`).
2. Se resalta el más ajustado: «σx frente a SAP2000: 0,21 % frente a 1 %: consume la quinta parte de
   su umbral». Remate: «el veredicto no depende del valor exacto de cada umbral, sino del margen».
> 0 «Esta figura de las conclusiones muestra cuán lejos quedó cada criterio numérico de
> incumplirse: el valor observado dividido por su umbral, en escala logarítmica. Lo que queda a la
> izquierda de la línea, cumple.»
> 1 «Uno por uno, los nueve criterios quedan a la izquierda; las tasas y el equilibrio, a varios
> órdenes de magnitud.»
> 2 «El más ajustado, la diferencia de la tensión normal frente a SAP2000, consume apenas la quinta
> parte de su umbral. Por eso el veredicto no depende del valor exacto de cada umbral, sino del
> margen con que se cumple.»

**44 · respuesta** (conclusiones) · «§ 3.8 · Conclusiones» · 5 pasos · [225]. *(Ola 3: entre el
paso 2 y las debilidades entra un paso propio, «La mejora frente a la situación de partida · § 3.8»:
lo que la caja negra hacía imposible —que las tensiones de los nodos cierren con las de los
elementos— en EduFEM puede comprobarse en la memoria; las debilidades pasan al paso 4. La voz
vigente está en `herramientas/narracion/conclusiones.json`.)*
0. El problema (en pequeño, gris) → **la respuesta** (grande): «La escasa transparencia incide
   porque oculta las magnitudes intermedias: sin ellas, ningún resultado puede seguirse etapa por
   etapa hasta sus datos, y solo los resultados finales pueden comprobarse.»
1. «Un software educativo con **tres rasgos** revierte esa situación»: (1) expone su procedimiento,
   con una versión del cálculo escrita para leerse que una prueba mantiene coincidente con la que
   resuelve; (2) muestra la respuesta junto con su procedimiento y sus medios de comprobación;
   (3) somete su motor a verificación y validación con criterios explícitos.
2. **PI-1** (a) → «la organización: un módulo por cada una de las siete primeras etapas sobre el
   elemento elegido, una memoria con las nueve y un post-proceso con sus comprobaciones, sobre un
   mismo lienzo». **PI-2** (b) → «sí: dentro de las tolerancias, las soluciones exactas, la
   analítica, la referencia de Cook y SAP2000, y el bloqueo que predice la teoría».
3. **Necesario, no suficiente** (el defecto de la extrapolación) + **tres debilidades declaradas**
   (§ 3.7.5): la evaluación es del autor; la deformación plana no tiene contraste externo; la
   exposición es una posibilidad que el software ofrece, no un recorrido que imponga.
> 0 «La respuesta al problema es esta: la escasa transparencia del software de análisis incide en
> la baja trazabilidad y verificabilidad porque oculta las magnitudes intermedias. Sin ellas,
> ningún resultado puede seguirse etapa por etapa hasta sus datos, y solo los resultados finales
> pueden comprobarse.»
> 1 «Un software educativo con tres rasgos revierte esa situación: expone su procedimiento con una
> versión del cálculo escrita para leerse, que una prueba mantiene coincidente con la que resuelve;
> muestra la respuesta junto con sus medios de comprobación; y somete su motor a verificación y
> validación con criterios explícitos.»
> 2 «Con ello quedan respondidas las dos preguntas. La primera, con la organización del software:
> un módulo por cada una de las siete primeras etapas, una memoria de las nueve y un post-proceso
> con sus comprobaciones, sobre un mismo lienzo. La segunda, con las cifras: el motor reproduce,
> dentro de las tolerancias, las soluciones exactas, las referencias externas y el bloqueo que
> predice la teoría.»
> 3 «Exponer el procedimiento es necesario, pero no suficiente, como mostró el defecto de la
> extrapolación. Y quedan tres debilidades declaradas: la evaluación es del autor, la deformación
> plana no tiene contraste externo y la exposición es una posibilidad que el software ofrece, no un
> recorrido que imponga.»

**45 · recomendaciones** (conclusiones) · «Recomendaciones · Tabla CR.1» · 3 pasos · [110].
Una hoja de ruta en tres carriles, uno por capítulo, que se dibujan en orden (cada uno nace de la
debilidad o frontera que atiende):
0. **Para la fundamentación (Cap. 1)**: tratamiento del bloqueo — integración reducida selectiva o
   formulación B̄ [15, pp. 221, 232–234; 4, pp. 476–477], con un módulo que contraste la respuesta
   bloqueada y la corregida; más tipos de elemento — triángulos lineales y cuadráticos,
   cuadriláteros de ocho nodos y de transición [16, pp. 167–174, 194; 5].
1. **Para el desarrollo (Cap. 2)**: mallado automático sobre el contorno dibujado, controlado por M0;
   solucionador para mallas muy grandes; guía docente (rehacer a mano una etapa de la memoria del
   ejemplo guía); extensión a tres dimensiones (hexaedros y tetraedros, la misma base
   isoparamétrica).
2. **Para la verificación y la validación (Cap. 3)**: ampliar la batería — un caso civil en
   deformación plana con solución publicada, una carga superficial linealmente variable, una prueba
   propia del término de cortante de la matriz de deformación plana, el error de tensiones del Q4 sin
   la franja de contorno —; revisión independiente — la tabla de cobertura por docentes o
   especialistas y el código por terceros —. «El uso en el aula: una investigación educativa
   distinta.»
> 0 «Las recomendaciones nacen de esas debilidades y de las fronteras del alcance. Para la
> fundamentación: incorporar el tratamiento del bloqueo, con integración reducida selectiva o la
> formulación B barra, y más tipos de elemento.»
> 1 «Para el software: un mallado automático, un solucionador para mallas muy grandes, una guía
> docente con prácticas y la extensión a tres dimensiones.»
> 2 «Y para la verificación: un caso civil en deformación plana con solución publicada, cargas
> linealmente variables y una revisión independiente de la tabla de cobertura y del código. El uso
> de la herramienta en el aula queda para una investigación educativa distinta.»

**46 · cierre** (intro) · `data-sin-pie` · [40].
«Gracias». Mensaje: «Del resultado a sus datos, etapa por etapa: un procedimiento de cálculo por el
MEF que puede seguirse y comprobarse». Tres fichas: «Trazable · 6 de 6 criterios» (violeta),
«Verificable · 9 de 9 criterios» (violeta), «Hipótesis comprobada» (verde). QR del repositorio
`github.com/Sucullani/SoftwareED`. Botones `solo-vivo`: Índice para preguntas, Respaldo.
> «EduFEM deja a la vista lo que el software comercial oculta: cada resultado puede seguirse hasta
> sus datos y comprobarse paso a paso. Muchas gracias por su atención; quedo a disposición del
> tribunal para sus preguntas.»

### Respaldo para preguntas (fuera del recorrido, sin narración)

Láminas `data-respaldo`, a las que se llega desde el índice (tecla M). Se rehacen a partir de las de
final3 (`../archivo/final3/Defensa_EduFEM.html`), **puestas al día con final4**:

- **90 · r-calculo-manual** — el Jacobiano de E3 rehecho a mano, con las mismas cifras del Anexo G
  de final4 (det J = 4,7604 en el primer punto de Gauss, etc.; confirmar página con
  `anexoG4_p*.png`). Viz heredada `calculo-manual` o copia adaptada.
- **91 · r-umbrales** — de dónde sale cada umbral (Tabla 2.4, columna «Procedencia») y su margen
  observado. Con la redacción de final4: ningún umbral numérico se escribió antes de las primeras
  corridas ni se calculó a partir de sus resultados; los de la flecha, Cook y las tasas entraron a
  los guiones al comienzo de la verificación, los de σx y del equilibrio al final del desarrollo;
  por eso el veredicto descansa en el margen (Figura CR.2).
- **92 · r-educativo** — «educativo» califica el propósito de diseño; validación de laboratorio
  [25, pp. 30–31]; la tesis no afirma efectos sobre el estudiante; el uso en el aula queda para una
  investigación educativa distinta (Recomendaciones).
- **93 · r-deformacion-plana** — qué la verifica hoy: las mismas tasas en las configuraciones de
  deformación plana (Tabla D.3), pero el campo manufacturado tiene traza de la deformación y
  distorsión angular nulas y solo ve D₁₁ − D₁₂ (igual en los dos estados); D₁₁ y D₁₂ de la
  deformación plana los acota, junto con él, la prueba de deformación uniaxial (Tabla D.1); D₃₃ no
  tiene prueba propia; falta un contraste externo (recomendación).
- **94 · r-apoyos** — la viga: apoyos (fijo en x = −7 m, móvil en x = +7 m, en el eje neutro), carga
  como fuerzas nodales equivalentes, malla, puntos de control, SAP2000 como cáscara, equilibrio.
  Verificar cada dato contra § 3.4 y el Anexo E de final4.
- **95 · r-escalabilidad** — Tabla 3.9: 33 282 GDL en 0,721 s; K densa ≈ 8,9 GB frente a 12,77 MB
  guardando solo los valores no nulos; equipo de 2012. Sin jerga.
- **96 · r-consistencia** — la matriz de consistencia (Tabla 2.3), legible.
- **97 · r-licencia** — código MIT; dependencias libres; avisos en LICENCIAS-TERCEROS.txt.
- **98 · r-secundarias** — la Tabla 3.2 completa: σy y τxy en B (0,94 % y 2,89 % frente a la
  analítica); son 6 a 35 veces menores que σx y no entran en el criterio; el 2,89 % de τxy es error
  numérico de EduFEM, declarado (§ 3.7.1).
- **99 · r-antes** — cómo se afirma la mejora sin pretest ni grupo de control: la situación de
  partida no se mide, se documenta (Tabla 1.1, § 2.1.2); niveles baja/alta de la variable
  dependiente; investigación tecnológica [7, p. 85]; validar, en la ciencia del diseño, es
  justificar que la herramienta cumple sus requisitos [25, p. 31]; se mide el nivel que alcanza
  EduFEM (Tabla 2.4) y la Tabla 3.11 lo pone frente a la partida.
- **99 · r-universo** — por qué 18 de los 49 contenidos: 18 fuera del alcance, 12 anteriores al
  cálculo, 1 no expuesto (FEM3), con los códigos de la nota de la Tabla 3.7.

## 6. Presupuesto de tiempo (video)

| Bloque | Láminas | Palabras | ≈ min |
|---|---|---|---|
| Carátula y agenda | 00–01 | 100 | 0,8 |
| Introducción | 02–08 | 960 | 6,3 |
| Capítulo 1 | 10–13 | 660 | 4,5 |
| Capítulo 2 | 20–24 | 590 | 4,2 |
| Capítulo 3 | 30–35 | 750 | 5,4 |
| Conclusiones | 40–46 | 930 | 6,5 |
| **Total** | **31** | **≈ 4000–4300** | **≈ 28–30 + pausas** |

Después de sintetizar la voz se mide la duración real y se ajusta la narración hasta 30:00 ± 0:30.
