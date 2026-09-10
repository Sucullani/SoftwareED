# Diagnóstico de la bibliografía de la tesis (2026-09-09)

Pasada de revisión con ojos limpios sobre las 22 entradas de
`tesis/bibliografia/referencias.bib`. Cada entrada se cotejó contra el ejemplar que tiene
el autor, se analizó si otra entrada podría absorber sus citas, y cada baja propuesta pasó
por tres escépticos con lentes distintas (sustituto, pérdida, tribunal). Una baja sobrevive
si a lo sumo una lente la refutó.

## 1. Veredicto

La bibliografía **casi no se reduce**: de las 22 entradas se propusieron 5 bajas y solo 2
sobrevivieron al escrutinio (`reddy2006introduction` y `salari2000mms`), de modo que el
recorte posible es 22 → 20 entradas y 160 → 152 citas.
El cotejo contra los ejemplares no encontró ningún dato inventado: 20 entradas coinciden,
1 discrepa en un dato de fondo (`perezsantiago2023fem`, falta `number = {5}`) y 1 tiene
tres campos que su ejemplar no imprime (`bishay2020teaching`, versión *Early View*).

## 2. Las 22 entradas

| Clave | Citas | Carácter | Cotejo | Decisión |
|---|---:|---|---|---|
| `cook2002concepts` | 21 | de_apoyo | COINCIDE | Conservar |
| `bathe2014fem` | 16 | puntual | COINCIDE | Conservar (baja propuesta y refutada 2/3) |
| `hughes2000fem` | 13 | de_apoyo | COINCIDE | Conservar |
| `bishay2020teaching` | 13 | nuclear | NO_VERIFICABLE | Conservar; revisar volumen/fascículo/páginas |
| `zienkiewicz2013fem` | 12 | de_apoyo | COINCIDE | Conservar |
| `lee2015interactive` | 12 | nuclear | COINCIDE | Conservar |
| `oberkampf2010vv` | 10 | nuclear | COINCIDE | Conservar |
| `perezsantiago2023fem` | 9 | nuclear | DISCREPA | Conservar; corregir `number` y la tilde |
| `timoshenko1970elasticity` | 6 | nuclear | COINCIDE | Conservar |
| `salari2000mms` | 5 | puntual | COINCIDE | **Baja sobreviviente (0 refutaciones)** |
| `virtanen2020scipy` | 5 | nuclear | COINCIDE | Conservar |
| `csi2017sap2000` | 5 | nuclear | COINCIDE | Conservar |
| `lee2015eigenmodes` | 5 | de_apoyo | COINCIDE | Conservar |
| `harris2020numpy` | 4 | de_apoyo | COINCIDE | Conservar |
| `alvarez_metodologia` | 4 | nuclear | COINCIDE | Conservar |
| `reddy2006introduction` | 3 | puntual | COINCIDE | **Baja sobreviviente (1 refutación)** |
| `onate2009structural` | 3 | puntual | COINCIDE | Conservar (baja propuesta y refutada 2/3) |
| `stimpson2007verdict` | 3 | nuclear | COINCIDE | Conservar; retoque de estilo en el autor |
| `suarez1998edelas2d` | 3 | nuclear | COINCIDE | Conservar |
| `sampieri2018metodologia` | 3 | de_apoyo | COINCIDE | Conservar |
| `garciacordoba2005tecnologica` | 3 | nuclear | COINCIDE | Conservar |
| `strang2008analysis` | 2 | puntual | COINCIDE | Conservar (baja propuesta y refutada 2/3) |

Reparto por carácter: 11 nucleares, 6 de apoyo, 5 puntuales.

## 2 bis. Lo que ya se aplicó (2026-09-10)

Decisión del autor: **no dar de baja ninguna entrada** —«quizá en un futuro»— y corregir
solo los errores. El `.bib` sigue en 22 entradas. Se aplicaron los dos únicos hallazgos que
son errores de hecho, y nada más:

1. **`perezsantiago2023fem`**: se agregó `number = {5}` y se reescribió el comentario, que
   afirmaba falsamente que el fascículo no figura en el ejemplar. La bibliografía impresa
   ahora dice «Computer Applications in Engineering Education 31.5 (2023)».
2. **`02_marco_teorico.tex:406`**: la cláusula de la cuadratura pasó de `salari2000mms` a
   `oberkampf2010vv`, y se explicitó el motivo técnico que antes quedaba implícito («porque
   el error de la propia cuadratura puede interferir con el error de discretización y
   degradar el orden observado»). Se añadió el respaldo correspondiente al catálogo de
   `respaldo_citas` con el pasaje de la p. 320.

Efecto: `salari2000mms` baja de 5 a 4 citas y `oberkampf2010vv` sube de 10 a 11; el total
sigue en 160. La tesis compila en 131 páginas, sin errores ni citas indefinidas.

**Lo que NO se tocó**, por ser criterio y no error: las dos bajas sobrevivientes, la tilde de
Pérez-Santiago, los retoques de caja e iniciales, y los `volume`/`number`/`pages` de
`bishay2020teaching`.

Un descarte que conviene registrar: se evaluó también `02_marco_teorico.tex:298`, donde la
mención de von Mises co-cita a Timoshenko y a Cook. En el ejemplar de Timoshenko «Mises»
aparece una sola vez, y en una nota bibliográfica al pie. Pero la oración es compuesta
—tensiones principales **y** von Mises— y Timoshenko sí cubre las principales (Arts. 9 y 68),
de modo que el co-citado reparte bien la afirmación. **No es un error.** Conviene no
«corregirlo»: la búsqueda de texto sobre el PDF de Cook devuelve cero para cualquier término
porque es un escaneo sin capa de texto, y eso no prueba ausencia.

## 3. Correcciones al `.bib`

### 3.1 De fondo (una sola)

**`perezsantiago2023fem` — falta el fascículo.**

- Dice el `.bib`: la entrada no declara `number`, y el comentario que la acompaña afirma
  que «el fascículo (núm. 5) no figura en el ejemplar, por eso no se declara».
- Dice el ejemplar: la marca de agua lateral de Wiley Online Library, presente en 14 de sus
  15 páginas, dice `10990542, 2023, 5`. El fascículo **sí** figura.
- Corrección: agregar `number = {5}` y borrar el comentario, que es incorrecto.

El resto del núcleo de la entrada está confirmado: autoría, título, revista, volumen 31,
páginas 1159-1173, año 2023 y DOI `10.1002/cae.22627`.

### 3.2 De grafía y estilo (opcionales, todas de gravedad baja)

| Entrada | Dice el `.bib` | Dice el ejemplar |
|---|---|---|
| `perezsantiago2023fem` | `P{\'e}rez-Santiago` (con tilde) | «Perez-Santiago», sin tilde, 17 veces (3 en el cuerpo, 14 en el encabezado); con tilde, cero |
| `stimpson2007verdict` | `Knupp, Patrick` (único de los cinco con nombre de pila desarrollado) | «P. Knupp» en la firma de la portadilla (p. 3); «Patrick Knupp» solo en la lista de distribución (p. 108) |
| `timoshenko1970elasticity` | `Timoshenko, S. P.` | Portada: «By S. TIMOSHENKO»; índice de autores (p. 498): «Timoshenko, S.». La inicial «P.» no aparece en el ejemplar |
| `harris2020numpy` | `Array Programming with {NumPy}` | «Array programming with NumPy» (caja de oración, p. 357 y metadato `Title` del PDF) |
| `harris2020numpy` | `number = {7825}` | El ejemplar no declara fascículo; la cadena «7825» no aparece en sus 6 páginas. El encabezado dice solo «Nature \| Vol 585 \| 17 September 2020» |
| `virtanen2020scipy` | la lista de autores termina en «van Mulbregt, Paul» | la firma termina en «Paul van Mulbregt38 and SciPy 1.0 Contributors39» |
| `virtanen2020scipy` | `{SciPy} 1.0: Fundamental Algorithms for Scientific Computing in {Python}` | «SciPy 1.0: fundamental algorithms for scientific computing in Python» (caja de oración) |
| `virtanen2020scipy` | `number = {3}` | El pie dice solo «Nature Methods \| VOL 17 \| March 2020», sin fascículo |

Con estilo numérico tipo Vancouver, ninguno de estos retoques cambia lo que se imprime en
la página de bibliografía salvo la caja del título y la tilde del apellido.

### 3.3 Campos sin respaldo en el ejemplar (no son errores)

**`bishay2020teaching`.** El ejemplar es la versión *Early View*: ya compuesta, con
copyright y DOI, pero paginada 1-21 y sin volumen ni fascículo impresos («Comput Appl Eng
Educ. 2020;1-21.» en la portada y en el bloque *How to cite this article*, p. 19). Por lo
tanto `volume = {28}`, `number = {4}` y `pages = {1007--1027}` **no son verificables contra
la copia que el autor tiene**, pero tampoco están desmentidos: no deben reportarse como
erróneos ni corregirse a ciegas.

### 3.4 Fuera del `.bib`: una atribución que no se sostiene

En `02_marco_teorico.tex:406`, la frase sobre evaluar las integrales de error con un punto
de Gauss más por dirección que la rigidez ($3\times3$ para Q4, $4\times4$ para Q9) «para no
subestimar artificialmente el error» se atribuye a Salari y Knupp, **y esa cita va sola**:
la línea dice `\autocite{salari2000mms}`, sin co-citado. El informe SAND2000-1444 no
contiene las palabras «Gauss» ni «quadrature» ni una sola vez, de modo que no puede
sostener esa frase.

Dónde sí está el respaldo: Oberkampf y Roy, **p. impresa 320** (PDF 336), dice que «errors
due to the numerical quadrature can interact with the numerical errors in the discrete
solution and adversely impact the observed order of accuracy». Eso es exactamente el motivo
de usar una regla de cuadratura más fina para las integrales de error, y `oberkampf2010vv`
ya está en el `.bib` con 10 citas.

Corrección: reemplazar `\autocite{salari2000mms}` por `\autocite{oberkampf2010vv}` en esa
frase. Hay que hacerlo **aunque se decida conservar** `salari2000mms`, porque el problema no
es la entrada sino la atribución.

## 4. Análisis de reducción

Se propusieron cinco bajas. Dos sobrevivieron.

### 4.1 `salari2000mms` (5 citas) — baja sobreviviente, sin refutaciones

- **Propuesta:** absorber en `oberkampf2010vv`. En las 4 citas co-citadas basta borrar la
  clave y dejar `\autocite{oberkampf2010vv}`; la quinta (`02:406`) es la atribución
  errónea del punto anterior. Lo propio del informe —la taxonomía de errores de
  codificación, la batería de 21 pruebas ciegas del Anexo E, la distinción MES/MMS— la
  tesis no lo usa.
- **Lente del sustituto:** no refutó. Verificó cita por cita en el PDF de Oberkampf y Roy
  (791 pág.) que el pasaje concreto que cada afirmación necesita está allí, no solo el tema.
- **Lente de la pérdida:** no refutó. Cotejó cada pasaje que el propio `respaldo_citas.tex`
  ancla a Salari contra el PDF de Oberkampf y encontró equivalente en los cinco.
- **Lente del tribunal:** no refutó. Entró con el sesgo de sostener la entrada y no
  encontró con qué: un informe técnico de Sandia cuya materia está entera en el tratado que
  ya se cita no se echa de menos ni luce como aparato.

### 4.2 `reddy2006introduction` (3 citas) — baja sobreviviente, 1 refutación

- **Propuesta:** dar de baja y repartir las 3 citas, que nunca están solas: `01:9` queda con
  Bathe y Hughes; `02:49` con Zienkiewicz y Hughes; `05:47` con Oñate y Cook.
- **Lente del sustituto:** no refutó. Abrió los ejemplares absorbentes y encontró en cada
  uno el pasaje concreto que la afirmación necesita.
- **Lente de la pérdida:** no refutó. Buscó pérdida en las cuatro categorías y no halló
  ninguna; el único matiz propio de Reddy (el elemento de transición) está también en Cook.
- **Lente del tribunal: REFUTÓ.** Concede `02:49` —ahí Reddy es el tercer enunciado de lo
  mismo— pero sostiene que eso no alcanza para bajar la entrada, y que en `01:9` la
  propuesta invierte la función retórica de la cita.

Con una sola lente en contra, la baja sobrevive por regla, pero no es unánime.

### 4.3 `strang2008analysis` (2 citas) — baja refutada 2 de 3

- **Propuesta:** es el caso de manual de entrada puntual —2 citas, una sola afirmación (las
  tasas O(h^{p+1}) en L2 y O(h^p) en H1), siempre apilada con `hughes2000fem`—. Se
  ejecutaba en tres archivos sin tocar una palabra de prosa.
- **Sustituto:** no refutó. Hughes 1987, pp. 189-190, sostiene la afirmación de forma
  literal.
- **Pérdida: REFUTÓ.** Concede que el enunciado queda cubierto —verificó el Remark 3 de
  Hughes con el caso resuelto k = m = 1, `||e||_0 <= c h^2` y `||e||_1 <= c h`, que es el Q4
  literal— y aun así refuta la baja.
- **Tribunal: REFUTÓ.** «La baja es segura pero no está justificada»: concede que Hughes
  cubre el pasaje incluso mejor en notación (su k es el p de la tesis), pero el saldo ante
  el tribunal es negativo.

### 4.4 `onate2009structural` (3 citas) — baja refutada 2 de 3

- **Propuesta:** las 3 citas son co-citas y en los tres casos el acompañante ya presente
  sostiene la afirmación con texto verificado; lo propio de Oñate es de forma, no de fondo.
- **Sustituto:** no refutó. Leyó los absorbentes rasterizando páginas (Hughes, Bathe y
  Reddy son escaneos sin capa OCR) y halló las tres afirmaciones sostenidas literalmente.
- **Pérdida: REFUTÓ.** Los tres sustitutos son peores que el original y en dos casos la
  propuesta describe el sustituto de un modo que no resiste el cotejo con la página.
- **Tribunal: REFUTÓ.** La propuesta contesta bien una pregunta equivocada: audita sitios de
  cita, cuando el tribunal pregunta si la obra debe estar en la bibliografía de una tesis de
  ingeniería civil sobre un pre/postprocesador MEF.

### 4.5 `bathe2014fem` (16 citas) — baja refutada 2 de 3

- **Propuesta:** la única de las bajas que toca una entrada grande. Las 16 citas tienen
  sustituto verificado y en cuatro de ellas la redirección además corrige la atribución: 12
  se resuelven borrando la clave del `\autocite`, 2 requieren compañero nuevo y el resto es
  puntual. Aporte propio: casi nulo, 15 de 16 son co-citas.
- **Sustituto:** no refutó. Encontró en los cinco PDF absorbentes el pasaje de las 16.
- **Pérdida: REFUTÓ.** Lo que se gana (22 → 21 entradas) es trivial frente a lo que se
  pierde; el propio proponente describe el camino que conserva sus correcciones sin la baja.
- **Tribunal: REFUTÓ.** Es uno de los cuatro textos canónicos del MEF y el canónico de los
  *procedimientos*; la tesis es en lo sustantivo un solucionador y su capítulo 2 recorre el
  álgebra de K·u = F.

### 4.6 Las 17 entradas que nadie propuso bajar

Ninguna de las otras 17 llegó a proponerse como baja, por razones de tres tipos:

- **Únicas en su materia**, sin sustituto posible dentro del `.bib`: `stimpson2007verdict`
  (las fórmulas de calidad de malla que EduFEM implementa), `suarez1998edelas2d` (única
  fuente primaria sobre ED-Elas2D, el antecedente más directo), `timoshenko1970elasticity`
  (única solución analítica cerrada de la viga bajo carga uniforme), `csi2017sap2000`
  (única documentación de SAP2000, segunda referencia externa de contraste),
  `virtanen2020scipy` y `harris2020numpy` (únicas fuentes citables del stack numérico).
- **Portantes del marco metodológico** que exige el tribunal: `alvarez_metodologia`
  (categorías dialécticas del diseño), `garciacordoba2005tecnologica` (la investigación
  tecnológica como categoría propia, que es el argumento más expuesto de la tesis: por qué
  no hay hipótesis estadística) y `sampieri2018metodologia` (tipología de muestreo).
- **Estructurales en la taxonomía de antecedentes o en la cadena de V&V**:
  `bishay2020teaching` (8 de 13 citas irredirigibles), `lee2015interactive` (4 de 12),
  `perezsantiago2023fem` (2 de 9, ambas estructurales), `lee2015eigenmodes` (3 de 5),
  `oberkampf2010vv` (4 de 10).
- **Canónicas por su lugar, no por exclusividad de contenido**: `zienkiewicz2013fem` (12 de
  12 citas técnicamente redirigibles), `hughes2000fem` (11 de 13) y `cook2002concepts`
  (19 de 21). Se conservan por su papel en las nóminas de clásicos, no porque sostengan
  afirmaciones huérfanas.

## 5. Recomendación final

### 5.1 Decisión técnica (la evidencia ya la resolvió)

1. Agregar `number = {5}` a `perezsantiago2023fem` y borrar el comentario que dice que el
   fascículo no figura.
2. Corregir la atribución de `02_marco_teorico.tex:406`: dejar `\autocite{oberkampf2010vv}`,
   porque Salari y Knupp no contiene «Gauss» ni «quadrature».
3. No tocar `volume`, `number` ni `pages` de `bishay2020teaching` sin una comprobación
   externa al ejemplar.
4. No reabrir las bajas de `strang2008analysis`, `onate2009structural` ni `bathe2014fem`:
   dos lentes independientes las refutaron en cada caso.

### 5.2 DECISIÓN DE AUTOR (depende de su criterio o del tribunal)

1. **Ejecutar o no las dos bajas sobrevivientes.** `salari2000mms` es la más limpia: ninguna
   lente la refutó y su materia está entera en Oberkampf y Roy. `reddy2006introduction`
   sobrevive por regla, pero el tribunal la refutó: quien decida debe pesar si prefiere una
   bibliografía de 20 entradas o conservar a Reddy por su lugar en la nómina de clásicos.
   El ahorro material es de dos registros sobre 22; la bibliografía difícilmente baje de dos
   páginas por ese corte.
2. **La tilde de Pérez-Santiago.** El ejemplar la omite en las 17 apariciones; la grafía real
   del investigador la lleva. Apego literal al ejemplar o grafía correcta del nombre: es
   criterio, no evidencia.
3. **Los retoques de caja tipográfica y de iniciales** (`harris2020numpy`,
   `virtanen2020scipy`, `timoshenko1970elasticity`, `stimpson2007verdict`) y el autor
   colectivo «SciPy 1.0 Contributors». Ninguno cambia lo que ve el lector con estilo
   numérico; se hacen solo si el autor quiere fidelidad literal al ejemplar.
4. **Los `number` no impresos** de `harris2020numpy` (7825) y `virtanen2020scipy` (3):
   dejarlos apoyándose en la ficha del editor, o quitarlos por no constar en el ejemplar.

## 6. Cifras

- **Entradas:** 22 (11 nucleares, 6 de apoyo, 5 puntuales).
- **Citas:** 160 en total; media de 7,3 citas por entrada y mediana de 5. La entrada más
  citada es `cook2002concepts` con 21; la menos citada, `strang2008analysis` con 2.
- **Cotejo:** 20 COINCIDE, 1 DISCREPA, 1 NO_VERIFICABLE. Una sola corrección de fondo.
- **Bajas:** 5 propuestas, 2 sobrevivientes. Si se ejecutan ambas: 20 entradas y 152 citas,
  media de 7,6 citas por entrada.
- **Bibliografía impresa:** 2 páginas (65-66), que son las páginas 80-81 del PDF de 131.
