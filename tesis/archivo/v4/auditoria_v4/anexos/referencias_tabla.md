# Anexo del eje «referencias» — aparato de citas de `main_v4`

Base: `tesis_txt/pistas_citas_tex.txt` (orden de la lista compuesta = numeración Vancouver
del PDF), `tesis/bibliografia/referencias.bib` (25 entradas) y comprobación de 20 fragmentos
con `ubicar.py`. La lista de referencias arranca en el folio 94 (PDF 109).

## Recuento global

| Magnitud | Valor |
|---|---|
| Entradas en la lista | 25 |
| Llamadas de cita en el cuerpo | 174 |
| Con localizador de página | 137 (79 %) |
| Sin localizador | 37 (21 %) |
| — de ellas, **exigen** localizador según la regla declarada (folio 11) | **22**, en 12 puntos del texto |
| — de ellas, de encuadre (correctas sin localizador) | 15 |
| Entradas citadas que no están en el `.bib` | 0 |
| Entradas del `.bib` que no se citan | 0 |

La regla que la tesis declara en la Introducción (folio 11): Vancouver, numeración por orden
de primera mención, corchetes, títulos de revista completos, conjunción antes del último
autor y **localizador de página en toda cita que sostenga una ecuación, un valor numérico,
un umbral, una definición o una atribución concreta**, omitido en citas de encuadre.

## Tabla por entrada

`Citas` = llamadas en el cuerpo; `C/loc` = con localizador; `Exigen` = llamadas sin
localizador que, por lo que sostienen, sí lo requieren.

| N.º | Clave | Citas | C/loc | Exigen | Defectos |
|---:|---|---:|---:|---:|---|
| 1 | zienkiewicz2013fem | 8 | 5 | 1 | Clave `2013` frente a entrada de 2005 (6.ª ed.): verificar que pp. 38, 69-71, 147, 161, 476-477 sean de la edición declarada. Falta localizador en «generalizables a tres dimensiones» (folio 9). |
| 2 | cook2002concepts | 18 | 14 | 2 | Falta localizador en la definición de los fenómenos numéricos (folio 27) y en «la presentación clásica de la literatura» (folio 75). |
| 3 | perezsantiago2023fem | 17 | 16 | 1 | Falta localizador en «el software didáctico como puente» (folio 13). Además, en Conclusiones (folio 89) el «consenso publicado de 67 expertos» aparece **sin número de cita**. |
| 4 | bathe2014fem | 16 | 10 | 5 | Clave `2014` frente a entrada de 1996. Es la entrada con más citas sin localizador exigible (folios 2, 9, 27, 75, 92). Sin campo `edition` pese a ser revisión de la obra de 1982 (decisión documentada en el `.bib`). |
| 5 | reddy2006introduction | 3 | 1 | 2 | Falta localizador en «sucesión algebraica» (folio 2) y en «elementos triangulares y de transición» (folio 92). ISBN mal formado: `007-124473-5` por `0-07-124473-5` (no se imprime en Vancouver). |
| 6 | suarez1998edelas2d | 5 | 3 | 0 | Correcta: las 2 sin localizador son identificación de la obra y encabezado de la Tabla 1.1. |
| 7 | garciacordoba2005tecnologica | 3 | 3 | 0 | Sin defectos. |
| 8 | alvarez_metodologia | 4 | 4 | 0 | **Inédito sin lugar, editorial ni año**, declarados entre corchetes. Sostiene con pp. 7, 8, 13 y 21 el marco metodológico (objeto/campo, problema, hipótesis, variables) y no es recuperable por el lector. |
| 9 | lee2015interactive | 14 | 11 | 2 | Falta localizador en «el software didáctico como puente» y en «Lee desarrolla simuladores interactivos» (folio 13). |
| 10 | lee2015eigenmodes | 5 | 3 | 1 | Falta localizador donde se definen los modos espurios (hourglass) y el bloqueo por cortante (folio 13). |
| 11 | bishay2020teaching | 11 | 9 | 1 | Falta localizador en «el software didáctico como puente» (folio 13). |
| 12 | rutten2012learning | 4 | 4 | 0 | Sin defectos. |
| 13 | harris2020numpy | 2 | 0 | 0 | Ninguna de sus dos citas lleva localizador, pero ambas son de encuadre (identificación de la biblioteca): correcto. |
| 14 | virtanen2020scipy | 4 | 2 | 0 | Las dos sin localizador son de encuadre: correcto. |
| 15 | timoshenko1970elasticity | 6 | 6 | 0 | Clave `1970` frente a entrada de 1951 (2.ª ed.): verificar que «art. 21, pp. 39-43» sea de la edición declarada. Sin ISBN (admisible en una obra de 1951). |
| 16 | hughes2000fem | 16 | 14 | 2 | Clave `2000` frente a entrada de 1987. Falta localizador en la definición de los fenómenos numéricos (folio 27) y en SRI/B-bar (folio 92). |
| 17 | onate2009structural | 3 | 2 | 1 | Falta localizador en «elementos triangulares y de transición» (folio 92). Coedición CIMNE/Springer reducida a un editor (decisión documentada). |
| 18 | csi2017sap2000 | 4 | 2 | 1 | Falta localizador donde respalda a toda la familia de «paquetes comerciales de análisis estructural» (folio 13). Manual distribuido en línea sin URL ni fecha de consulta. |
| 19 | chi2014icap | 3 | 3 | 0 | Sin defectos. |
| 20 | atkinson2000learning | 3 | 3 | 0 | Sin defectos. |
| 21 | stimpson2007verdict | 6 | 6 | 0 | Sin defectos (DOI, URL y fecha de consulta completos). |
| 22 | oberkampf2010vv | 9 | 7 | 2 | Falta localizador en la definición de la verificación por soluciones manufacturadas (folio 42) y en el criterio de selección de casos de prueba (folio 43). |
| 23 | salari2000mms | 4 | 3 | 1 | Falta localizador (folio 42). Informe Sandia sin DOI, URL ni fecha de consulta, a diferencia de su gemelo `stimpson2007verdict`. |
| 24 | strang2008analysis | 2 | 2 | 0 | Clave `2008` frente a entrada de 1973 (Prentice-Hall): verificar que pp. 106-107 sean de la edición declarada. |
| 25 | sampieri2018metodologia | 4 | 4 | 0 | Sin defectos. |

## Las 22 llamadas sin localizador que la regla declarada exige (12 puntos del texto)

| # | Archivo | Contexto | Cita | Folio |
|---:|---|---|---|---|
| 1 | 01_introduccion | «…aparecen como pasos de una sucesión algebraica cuya conexión con la geometría…» | [4, 5] | ~2 |
| 2 | 01_introduccion | «…la cuadratura de Gauss y el ensamblaje son directamente generalizables a tres dimensiones» | [1, 4] | 9 |
| 3 | 02_marco_teorico | «…propone el software específicamente didáctico como puente entre ambos extremos» | [3, 9, 11] | 13 |
| 4 | 02_marco_teorico | «Lee desarrolla simuladores interactivos del procesamiento de las ecuaciones…» | [9] | 13 |
| 5 | 02_marco_teorico | «…modos espurios de energía nula (hourglass) y bloqueo por cortante, no modos de vibración» | [10] | 13 |
| 6 | 02_marco_teorico | «…los paquetes comerciales de análisis estructural, que operan como cajas negras» | [18] | 13 |
| 7 | 02_marco_teorico | «…cuya comprensión resulta esencial para interpretar correctamente los resultados» | [2, 4, 16] | 27 |
| 8 | 02b_diseno_metodologico | «…verificación de código por el método de soluciones manufacturadas y contrastación…» | [22, 23] | ~42 |
| 9 | 02b_diseno_metodologico | «…antes que por su realismo físico» (criterio de selección de casos) | [22] | 43 |
| 10 | 04_resultados | «…en consonancia con la presentación clásica de la literatura» | [2, 4] | 75 |
| 11 | 05_conclusiones | «…la integración reducida selectiva (SRI) o la formulación B-bar» | [4, 16] | 92 |
| 12 | 05_conclusiones | «…elementos triangulares (lineales y cuadráticos) y cuadriláteros de transición» | [5, 17] | 92 |

## Las 15 llamadas sin localizador que son de encuadre (correctas)

`01_introduccion`: «El MEF constituye una de las herramientas centrales del análisis
estructural» [1, 2]; «bibliotecas numéricas de código abierto» [13, 14]. ·
`02_marco_teorico`: «Su solidez teórica está documentada en los textos clásicos de la
disciplina» [1, 2, 4]; identificación de ED-Elas2D [6]; los cinco encabezados de columna de
la Tabla 1.1 [6], [11], [9], [10], [18]. · `03_diseno_implementacion`: «NumPy, que provee el
álgebra densa, y SciPy, que provee las matrices dispersas» [13, 14].

## Citas narrativas: comprobación específica

Se verificaron con `ubicar.py` siete pasajes en que la prosa nombra al autor. **En los siete
el número Vancouver está en la misma oración**, de modo que este aspecto de la norma se
cumple; lo que falta en dos de ellos es el localizador de página, no el número:

| Pasaje | Folio / PDF | Cita en la misma oración |
|---|---|---|
| «Bishay propone un constructor y un analizador de reticulados…» | 13 / 28 | [11, pp. 5-6] |
| «Lee desarrolla simuladores interactivos…» | 13 / 28 | [9] — sin página |
| «…y de la visualización de los modos propios…» | 13 / 28 | [10] — sin página |
| «Lee vincula bidireccionalmente cada entrada de la matriz…» | 18 / 33 | [9, pp. 158, 163, 166, 168; 10, p. 874] |
| «Bishay hace que los estudiantes construyan por etapas…» | 19 / 34 | [11, pp. 4-5, 13, 17] |
| «…y Cook advierte que el promediado nodal simple no mejora…» | 64 / 79 | [2, p. 231] |
| «…con que Bishay midió el efecto de sus herramientas» | 94 / 109 | [11, pp. 4-5, 13] |

## Comprobaciones que descartaron hallazgos brutos

- **Valor de referencia 23,96 de la membrana de Cook** (folio 71, PDF 86): la nota al pie 1
  de esa misma página declara que el caso no tiene solución analítica cerrada, que el valor
  «es un límite de convergencia y no un dato exacto, por lo que conviene tratarlo como tal y
  no como una constante tomada de una fuente», lo corrobora con extrapolación de Richardson
  propia [22, pp. 309-312] y acota su incertidumbre. La cifra no necesita fuente externa.
- **Sobreintegración 3 × 3 en Q4** (folio 26-27): el texto ya trae la justificación que el
  hallazgo bruto proponía añadir («el integrando solo es polinómico en los elementos no
  distorsionados, y en los distorsionados la diferencia es marginal»).
- **Ubicación de «en consonancia con la presentación clásica de la literatura»**: está en el
  folio 75 (PDF 90), no en el folio 74 (PDF 89) como reportó el lector de unidad.
