# Auditoría de redacción — Tesis EduFEM

**Documento auditado** · `tesis/main_final.pdf` — 187 páginas PDF, 171 páginas impresas
(i–xv en romanos, 1–171 en arábigos). Compilado el 22 de septiembre de 2026.
**Título** · *Desarrollo de software educativo de elementos finitos para el análisis estructural
empleando el lenguaje de programación Python.*
**Autor** · Hedy Yhassmany Oyola Sucullani · Universidad Autónoma «Tomás Frías», Potosí.

**Normas verificadas contra el texto** · Vancouver (ICMJE/NLM) en la versión que el propio
documento declara en la página 11, y APA 7 para la presentación. A ellas se suma
`capitulos_final/CRITERIOS.md`, el reglamento editorial que el autor se impuso a sí mismo: sus
reglas se auditaron como normas, porque el documento las declara.

**Entregable acompañante** · `PLAN-CORRECCION-FINAL.md`, con las correcciones agrupadas en el
orden en que conviene hacerlas, el texto reformulado de cada hallazgo grave y las 38 preguntas
de defensa con su respuesta preparada.


## Índice

- [1. Veredicto](#1-veredicto)
- [2. Cómo leer este informe](#2-cómo-leer-este-informe)
- [3. Método, y las decisiones que se tomaron](#3-método-y-las-decisiones-que-se-tomaron)
- [4. Lo que está comprobado y correcto: no tocar](#4-lo-que-está-comprobado-y-correcto-no-tocar)
- [5. Los cinco problemas de mayor impacto](#5-los-cinco-problemas-de-mayor-impacto)
- [6. Patrones](#6-patrones)
- [7. Hallazgos de severidad alta que no pertenecen a ningún patrón](#7-hallazgos-de-severidad-alta-que-no-pertenecen-a-ningún-patrón)
- [8. Hallazgos de severidad media y baja](#8-hallazgos-de-severidad-media-y-baja)
- [9. Riesgo de defensa](#9-riesgo-de-defensa)
- [10. Cobertura](#10-cobertura)
- [11. Lo que se descartó, y por qué](#11-lo-que-se-descartó-y-por-qué)
- [12. Huecos de esta auditoría](#12-huecos-de-esta-auditoría)
- [13. Qué cambió el control final](#13-qué-cambió-el-control-final)
- [14. Estado de aplicación](#14-estado-de-aplicación)
- [Anexo de datos](#anexo-de-datos)

---

## 1. Veredicto

**El documento está en condiciones de defenderse. No necesita más investigación: necesita una
pasada de calibración y de disciplina léxica.**

Conviene decirlo antes que nada porque el volumen engaña. Esta auditoría reunió 354 hallazgos
que sobrevivieron a la verificación independiente. Al consolidarlos —fusionar los que eran el
mismo defecto visto por dos agentes, retirar los falsos positivos y agrupar en patrones lo que se
repetía— quedan **299 hallazgos vivos: 13 patrones que absorben 122, y 177 sueltos**. Un control
final a cargo de diez revisores que no habían participado reexaminó después los más graves y
rebajó seis de ellos. El resultado: **ninguno es de severidad crítica y solo diez son de severidad
alta** —siete sueltos y tres dentro de patrones—. Más de la mitad del volumen son instancias
sueltas de cinco o seis defectos de escritura repetidos.

Lo que se comprobó de forma determinista —no por juicio de un lector, sino rehaciendo las
cuentas— está sólido:

- **La aritmética del Anexo G cierra.** Se rehízo íntegra a mano: la matriz constitutiva a
  partir de *E* y ν, las derivadas de las funciones de forma, el Jacobiano, su determinante y su
  inversa, la suma de reacciones, el círculo de Mohr, la tensión de von Mises y la extrapolación
  nodal. **Catorce magnitudes, catorce coincidencias.** La matriz de extrapolación es la inversa
  exacta de **M**: el defecto que §3.7.2 relata haber encontrado y corregido está efectivamente
  corregido.
- **El orden de las citas es impecable.** Las referencias [1] a [26] aparecen en orden
  estrictamente correlativo de primera mención, sin una sola cita huérfana ni una sola entrada
  sin citar.
- **Las cifras del texto son coherentes de punta a punta.** Los 0,0414 % se redondean a
  0,04 %, los 0,2066 % a 0,21 %, los 0,2633 % a 0,26 %; todos los redondeos van en el sentido
  conservador, y la razón de errores Q4/Q9, que es 15,3, se enuncia como «más de diez veces».
  **Dos excepciones, ambas menores.** H-137: dos lecturas de SAP2000 difieren en la cuarta cifra
  decimal entre la Tabla 3.2 y las capturas del Anexo E —127,8514 frente a 127,8510 en el punto
  A, y −31,7852 frente a −31,7850 en el C—; el punto B coincide exacto, lo que descarta un
  problema sistemático y apunta a una transcripción puntual. Y H-310: §3.5 llama «coincidente»
  con el 0,05 % una distancia que vale 0,042 %. Ninguna de las dos altera un error relativo ni
  una conclusión.
- **La composición no tiene un solo desborde**: cero *overfull*, cero *underfull*, `microtype`
  activo.

Y hay pasajes de calibración ejemplar que el autor no debe tocar: el tratamiento de la membrana
de Cook —valor adoptado 23,96, publicado 23,965, extrapolación propia ≈ 23,97, incertidumbre
acotada en 0,05 %—; la nota de la Tabla 3.2, que distingue «diferencia» de «error» porque
SAP2000 no es patrón de exactitud; y el párrafo de §3.4 que declara sus propias debilidades,
incluido que el máximo sobre el dominio completo no se calculó.

**Lo que no está bien se concentra en cuatro sitios, y los cuatro son de redacción.**

1. **Lo que el documento anuncia como evidencia no siempre es lo que mide.** La reproducción
   manual de la memoria se declara indicador de la variable dependiente, familia de método y
   condición de refutación de la cláusula (b), mientras que el criterio que de verdad se aplica
   —Tabla 2.4— mide otra cosa: que cada etapa esté desarrollada y remitida a su ecuación. El
   criterio «9 de 9 etapas» se declara cumplido contra un anexo que, por llevar una sola carga
   nodal, no desarrolla la etapa 6. Y el «18 de 18» se mide contra un universo del que se
   apartó, declaradamente, el único ítem que el software no expone.
2. **El documento rompe su propio vocabulario.** §1.13 fija una acepción única de «validación» y
   el texto la usa otras diez veces para cosas que esa misma sección excluye. Peor: las
   Conclusiones llaman «errores» a las diferencias frente a SAP2000, justo lo que el capítulo 3
   se cuidó de negar.
3. **El caso de validación central no se puede rehacer con lo escrito.** §3.4 no dice cómo se
   apoyó la viga ni cómo se aplicó la carga en el continuo bidimensional, y del modelo de
   SAP2000 no consta ni la malla ni la versión. Es lo primero que preguntará el examinador
   estructuralista, que es el único que conoce SAP2000 de primera mano.
4. **La puerta del documento entra sin glosas y con alguna elipsis.** El Resumen es la única
   página que todo el tribunal lee entera, y en ella entran sin glosa «lienzo», «bloqueo por
   cortante» y «soluciones manufacturadas»; además, «los dieciocho contenidos que un consenso
   exige» son dieciocho de cuarenta y nueve, y falta el subíndice de σx que el cuerpo sí escribe.
   Son arreglos de una cláusula. El control final rebajó este frente: el cuerpo corrige por su
   cuenta casi todo lo que el Resumen abrevia.

Ninguno de los cuatro exige investigación nueva, y ninguno pide producir evidencia que no
exista: el más delicado —la discordancia sobre el cotejo manual— se resuelve alineando tres
frases con el criterio que la propia tesis aplica. **No** conviene añadir una recomputación a
mano: chocaría con la advertencia del Anexo G de que todo lo que publica es salida del motor, y
un cotejo del autor contra su propio motor no sería un patrón independiente.

**Esfuerzo total estimado: 31,5 a 32,5 horas de corrección, más dos de recompilación y
relectura.** Los tres primeros bloques del plan suman nueve horas y son los que cambian la
defensa.

---

## 2. Cómo leer este informe

**Identificadores.** `PAT-01` … `PAT-13` son patrones: defectos con más de tres apariciones,
reportados una sola vez con su recuento y tres ejemplos ubicados. `H-001` … `H-354` son
hallazgos sueltos. Los números son estables: el plan de corrección los usa tal cual, y no se
reciclan aunque un hallazgo se retire.

**Ubicaciones.** Siempre en dos numeraciones: *página impresa (PDF p. N)*. En el cuerpo,
**página impresa = página PDF − 16**. Las páginas PDF 2 a 16 llevan romanos.

**Severidad.**

| | Significado |
|---|---|
| **crítica** | Compromete la defensa. **No hay ninguna en este documento.** |
| **alta** | El tribunal lo va a preguntar, o el lector no especialista se pierde en un punto central. |
| **media** | Resta calidad; no compromete. |
| **baja** | Cosmético. |

**Qué NO es hallazgo aquí.** La notación matemática rota al extraer texto del PDF (es un
artefacto de la extracción, no del documento). La ausencia de prueba de campo con estudiantes
(es una decisión declarada del autor, y el documento está construido sobre ella). La repetición
funcional —resumen, matriz de consistencia, contraste de hipótesis, cifra recordada en
conclusiones—. Y las dos desviaciones del Vancouver estricto que el documento **declara** en la
página 11: títulos de revista completos y conjunción antes del último autor.

---

## 3. Método, y las decisiones que se tomaron

Se repartió el trabajo en tres oleadas sobre el PDF ya compilado, nunca sobre borradores.

**Oleada 1 — 25 lectores en paralelo.** Catorce leyeron el documento tramo por tramo, con las
187 páginas troceadas en unidades de entre 3 y 20 páginas; once cubrieron un eje cada uno sobre
el documento entero (trazabilidad, calibración con dos lentes distintas, redundancia,
consistencia, referencias, aparato formal, accesibilidad, claridad, riesgo de defensa y
tipografía). Se usaron modelos de distinta capacidad según la tarea: los de mayor capacidad para
los ejes argumentativos y para las unidades que deciden la defensa; los más rápidos para los
barridos mecánicos.

**Oleada 2 — verificación adversarial.** Un verificador independiente por unidad y por eje, que
no había participado en la lectura, revisó los hallazgos de severidad crítica y alta con el
encargo expreso de **descartarlos si no se sostenían**. Se descartaron 5 y se matizaron 107.

**Oleada 3 — consolidación y crítico de completitud.** Tres agentes fusionaron duplicados,
extrajeron patrones y construyeron la cobertura y las preguntas de defensa. Un cuarto, que no
había participado, buscó lo que nadie había mirado.

### Decisiones que se tomaron por el camino, y que conviene conocer

1. **Se auditó `CRITERIOS.md` como norma.** El autor se impuso reglas propias —tope de palabras
   por oración, términos canónicos, verbos por tipo de evidencia, una sola aparición canónica de
   cada explicación—. Incumplirlas se trató como defecto, porque el documento las declara.
2. **Se comprobó el código, no solo el texto.** Tres hallazgos afirmaban cosas sobre el
   software; los tres se verificaron en el repositorio. Uno resultó ser el hallazgo más limpio
   del eje de cobertura (la extrapolación de Richardson no existe en el código: `grep` sobre
   `fem/`, `gui/`, `models/`, `file_io/`, `education/`, `config/`, `tools/` y `tests/` devuelve
   cero).
3. **Se midió el documento como objeto impreso**, no solo como texto: márgenes reales de tinta
   página por página, altura en milímetros del texto dentro de las capturas de pantalla y
   resolución efectiva de las imágenes.
4. **Se leyeron las normas de la Carrera**, que están en el propio repositorio
   (`tesis/Material docente/`). De ahí salieron dos hallazgos que ningún lector del texto podía
   encontrar, y la confirmación de que la estructura de capítulos y la portada **cumplen** el
   formato oficial.
5. **Los índices auxiliares se corrigieron cuando fallaron.** El primer analizador de citas daba
   dos referencias fuera de orden; eran falsos positivos de localizadores múltiples
   (`[20, pp. 51, 57]`). El analizador corregido confirma que el orden es perfecto. Se deja
   constancia porque el índice defectuoso se distribuyó a los agentes.
6. **Se prefirió la acción concreta a la recomendación genérica.** Donde un hallazgo decía
   «matizar», se exigió la frase reformulada completa. El plan de corrección contiene texto listo
   para pegar, no instrucciones.
7. **Se degradaron 13 hallazgos y se retiraron 3** por sobrecorrección: pedían cambios que
   empeorarían el documento o reprochaban decisiones que el propio texto justifica. Están
   listados en §11.

---

## 4. Lo que está comprobado y correcto: no tocar

Esta sección importa tanto como las demás. Un autor que recibe una auditoría tiende a
sobrecorregir, y hay partes del documento que son buenas precisamente como están.

| | Comprobación | Resultado |
|---|---|---|
| 1 | Aritmética del Anexo G, rehecha a mano en 14 magnitudes | **Cierra entera** |
| 2 | Matriz de extrapolación **E** = **M**⁻¹ (valores 1 ± √3/2 y −½) | **Correcta** |
| 3 | Orden de primera mención de [1]–[26] | **Estrictamente correlativo** |
| 4 | Citas huérfanas / entradas huérfanas | **Cero / cero** |
| 5 | Coherencia de cifras entre resumen, cuerpo, tablas y conclusiones | **Dos excepciones, ambas menores** (H-137 y H-310) |
| 5b | Tabla 3.2 frente a las capturas de SAP2000 del Anexo E | Dos valores difieren en la 4.ª decimal (H-137) |
| 6 | Localizadores de página dentro del rango de su entrada | **128 de 134 correctos** |
| 7 | Composición: *overfull*, *underfull*, *vbox* | **0, 0, 0** |
| 8 | Leyendas de figuras y tablas (66) | **Autosuficientes salvo dos** |
| 9 | Estructura de capítulos frente al índice oficial de la Carrera | **Cumple** |
| 10 | Portada frente a `CARATULA.pdf` | **Cumple campo por campo** |
| 11 | Palabras clave en el resumen; *abstract* no exigido | **Cumple** |
| 12 | Anexo E: 11 páginas de 11 del original | **Completo** |

Y estos pasajes son ejemplares; el arreglo, cuando lo hay, consiste en **llevarlos a otras
páginas**, nunca en quitarlos de donde están:

- **La nota de la Tabla 3.2** (p. 81), que rotula la última columna «diferencia» y no «error»
  porque la formulación de cáscara de SAP2000 no es la misma que el continuo de tensión plana.
  Es la frase que tiene razón; la corrección va en sentido contrario, alineando las Conclusiones
  con ella.
- **El párrafo de §3.4** (p. 82) que declara el 0,94 % en σy, el 2,89 % en τxy y que «ese máximo
  sobre el dominio completo no se calculó».
- **El tratamiento de la membrana de Cook** (§3.5), con su incertidumbre acotada y su
  advertencia de no leer como exactitud los errores por debajo del 0,1 %. El razonamiento se
  conserva entero; solo se corrigen dos palabras dentro de él: el «coincide» de la p. 84 (H-310)
  y el «significativa» sin prueba de la p. 85 (H-277).
- **La disciplina de no afirmar efectos sobre el estudiante.** Se buscó expresamente y no
  aparece ninguno atribuido a EduFEM. Más aún: §1.2 lo niega por escrito —«No son evidencia de
  que la herramienta produzca un efecto de aprendizaje: ese efecto no se mide en este trabajo,
  y las fuentes citadas lo reportan de otras herramientas y en condiciones que sus propios
  autores acotan»—. Es una decisión sostenida con rigor a lo largo de 171 páginas, y no debe
  compensarse con nada. El único cabo suelto es H-007: la Justificación (p. 4) atribuye a «la
  literatura» que ciertas herramientas «favorecen la instrucción» **sin ninguna cita**, aunque
  remite a §1.2 para las salvedades.
- **Las 26 referencias.** Que sean 26 es un dato, no un defecto. No alargar la bibliografía para
  que parezca más académica.

---

## 5. Los cinco problemas de mayor impacto

Ordenados por lo que cambian en la lectura del tribunal, no por número de apariciones.

### 1. La comprobación manual que sostiene la cláusula (b) se anuncia tres veces y nunca se ejecuta

> **Por qué pesa.** Es la afirmación más repetida del trabajo —indicador de la variable dependiente, una de las cuatro familias de evaluación y condición declarada de refutación— y el Anexo G advierte que «cada matriz, vector y valor que sigue es la salida real del motor numérico», de modo que el tribunal que pregunte «¿dónde está el cálculo manual?» se queda sin respuesta en 187 páginas.

**Qué hacer.** Ejecutar y reportar el cotejo: añadir a §G.3 (o a §3.6.1) media página con la recomputación independiente de tres magnitudes —det J, un término de D y σVM en el punto de Gauss— hecha con calculadora, con la diferencia frente a la salida del motor. El orquestador ya lo hizo y cierra en las catorce magnitudes comprobables. Corregir «se demuestra que la memoria puede reproducirse a mano» (§2.1.4, p. 48) por «se reproduce a mano» una vez exista el cotejo, y acotar en el Resumen «una memoria de cálculo automática, reproducida a mano para el ejemplo canónico».

**Esfuerzo:** 3 h · **Hallazgos:** H-023, H-010, H-019, H-069, H-200, H-087

### 2. El caso de validación central no se puede rehacer con lo que el documento escribe

> **Por qué pesa.** §3.4 es la única validación contra referencias externas y un tribunal de ingeniería civil preguntará por lo primero que sabe mirar: cómo se apoyó una viga simplemente apoyada en un continuo bidimensional y cómo se aplicó la carga; ni el cuerpo, ni el Anexo D, ni el Anexo E lo dicen, y del modelo de SAP2000 no consta ni la malla ni la versión.

**Qué hacer.** Añadir a §3.4 un párrafo de datos del modelo: qué nodos o aristas se restringieron en cada apoyo, cómo se repartió la carga uniforme sobre el borde, y en el Anexo E la versión de SAP2000, el tipo y número de elementos shell, su tamaño y el espesor. Corregir de paso las erratas y la notación del preámbulo del Anexo E, y explicar en una línea por qué la flecha calculada supera a la analítica y a SAP2000.

**Esfuerzo:** 2 h · **Hallazgos:** H-021, H-026, H-235, H-199, H-193

### 3. Los criterios de cobertura se declaran cumplidos contra evidencia que no los cubre del todo

> **Por qué pesa.** Son los dos números que el Resumen y las Conclusiones repiten («9 de 9», «18 de 18») y los dos tienen un punto flojo verificable: la etapa 6 —fuerzas nodales equivalentes— no se desarrolla en el Anexo G porque el ejemplo lleva una sola carga nodal, y del universo de contenido se apartó FEM3 por ser «un desarrollo teórico que el software no expone», de modo que un ítem es verdadero por construcción.

**Qué hacer.** Para la etapa 6: declarar en §3.6.1 y en el Anexo G que en el ejemplo canónico la etapa 6 es degenerada —F se arma directamente de la carga nodal— y remitir a la memoria de un modelo con carga superficial, o reportar «8 de 9 en el ejemplo canónico, 9 de 9 en la memoria que el software genera». Para el universo: decir explícitamente que 18 de 19 ítems del alcance tienen instrumento y que FEM3 se apartó por no estar expuesto, en lugar de apartarlo del denominador. Corregir la fila FEA30 de la Tabla 3.7: la extrapolación de Richardson no está en el software.

**Esfuerzo:** 3 h · **Hallazgos:** H-022, H-025, H-004, H-006, H-239, H-248, H-012, H-232

### 4. «Validación» y «error» usados fuera de la acepción que el propio documento fija

> **Por qué pesa.** §1.13 declara una acepción única —contraste con la solución analítica y el modelo comercial— y el documento la rompe en una decena de sitios, incluido el quinto objetivo específico; peor aún, las Conclusiones llaman «errores» a las diferencias frente a SAP2000, que es exactamente lo que la nota de la Tabla 3.2 se cuidó de negar y lo que los Aportes escriben bien dos páginas después.

**Qué hacer.** Pasada de una palabra: en Conclusiones OE4, «frente al modelo de SAP2000, la diferencia fue de hasta el 0,21 % en σx». Reformular OE5 («Contrastar la propuesta…» o «Evaluar la propuesta…») con su eco en la Tabla 2.1, la Tabla 2.3 y las Conclusiones; cambiar el título de §3.1 y las cinco apariciones de §2.1.1, §3.7.4, el Anexo B y la apertura del capítulo 3. Dejar intacta la nota de la Tabla 3.2: es la que tiene razón.

**Esfuerzo:** 1,5 h · **Hallazgos:** H-016, H-015, H-071, H-079, H-096, H-090, H-139, H-144, H-304

### 5. La puerta del documento promete más de lo que el cuerpo sostiene y entra sin glosas

> **Por qué pesa.** El Resumen es la única página que todos los miembros del tribunal leen entera, y en ella el 0,04 % de σx se atribuye a «la tensión normal» —cuando σy da 0,94 % y τxy 2,89 %—, la memoria se presenta reproducible a mano sin acotarla al ejemplo canónico, el software se llama «libre» aunque la licencia «debe elegirse» según la nota de la Tabla 2.5, y entran sin glosa «lienzo», «bloqueo por cortante» y «soluciones manufacturadas».

**Qué hacer.** En el Resumen: «del 0,04 % en la tensión normal σx»; «una memoria de cálculo automática, reproducida a mano para el ejemplo canónico»; tres glosas de media línea. Nombrar la licencia concreta (el repositorio lleva MIT) en §2.2.2 y reemplazar la nota que dice que debe elegirse, o retirar «libre» de las seis afirmaciones que lo usan. Partir en dos el objetivo general, que con 100 palabras es la oración más larga del documento y la que el tribunal lee con más atención.

**Esfuerzo:** 2 h · **Hallazgos:** H-005, H-087, H-089, H-020, H-001, H-039, H-205, H-013

---

## 6. Patrones

Trece defectos con más de tres apariciones cada uno. Entre los trece absorben **122 de los 299 hallazgos vivos**: corregirlos como patrón, de una pasada, es mucho más barato que atacarlos uno a uno.

| ID | Patrón | Eje | Sev. | Aparic. | Esfuerzo |
|---|---|---|---|---|---|
| **PAT-01** | Términos técnicos usados muchas páginas antes de su glosa, o nunca glosad… | accesibilidad | alta | 16 | 2 h |
| **PAT-02** | Oraciones por encima del tope de ~60 palabras que el propio autor fijó | claridad | media | 96 | 2 h |
| **PAT-03** | Párrafos de 200 a 390 palabras que encadenan cuatro o cinco asuntos | claridad | media | 17 | 1 h |
| **PAT-04** | Muletillas de apertura y conectores únicos repetidos hasta la saturación | claridad | baja | 89 | 1,5 h |
| **PAT-05** | El impersonal oculta quién decidió, justo donde la decisión es el aporte | claridad | media | 11 | 45 min |
| **PAT-06** | Enumeraciones de cuatro o más elementos que siguen en prosa corrida | aparato formal | media | 27 | 1,5 h |
| **PAT-07** | Piezas del software reexplicadas desde cero entre el cuerpo y el Anexo B | redundancia | media | 12 | 1,5 h |
| **PAT-08** | Marco y método reexpuestos desde cero en el capítulo 3 y en las conclusio… | redundancia | media | 18 | 2 h |
| **PAT-09** | «Validación», «validar» y «error» fuera de la acepción que el documento d… | consistencia | alta | 11 | 1,5 h |
| **PAT-10** | Símbolos, precisión y formato numérico desparejos, y Nomenclatura incompl… | consistencia | media | 45 | 2 h |
| **PAT-11** | Atribuciones concretas sin localizador de página, y tres sin ninguna cita | referencias | alta | 15 | 1,5 h |
| **PAT-12** | El Anexo G, pieza que sostiene el argumento central, se presenta con desc… | aparato formal | alta | 18 | 2,5 h |
| **PAT-13** | Los índices reproducen leyendas completas y omiten quince secciones | aparato formal | baja | 34 | 1 h |

> **Cómo leer estas cifras.** La columna «Aparic.» cuenta cuántas veces aparece el defecto **en la tesis**, no cuántos hallazgos agrupa. Y las líneas «Absorbe:» de cada patrón nombran también los identificadores de los registros que se fusionaron con otro antes de consolidar: por eso suman 143 identificadores, mientras que los hallazgos **vivos** que los trece absorben son 122.

### Detalle

#### PAT-01 — Términos técnicos usados muchas páginas antes de su glosa, o nunca glosados

*accesibilidad · severidad alta · 16 apariciones · 2 h*

CRITERIOS.md exige media línea de glosa en la primera aparición de cada término técnico, y dieciséis términos la reciben decenas de páginas después o no la reciben nunca. El daño se concentra en las páginas que fijan el trabajo: el Resumen, los objetivos y las cláusulas de la hipótesis usan cinco de ellos, y el segundo lector declarado —un estudiante que aún no cursó el método— no puede juzgar allí si un resultado es bueno o malo.

**Tres ejemplos:**

- Resumen, p. i (PDF p. 2): «La membrana de Cook mostró el bloqueo por cortante del Q4 frente a la convergencia del Q9»; el fenómeno se define en §1.9, p. 27 (PDF p. 43), veintisiete páginas después
- «lienzo»: catorce apariciones desde el Resumen y desde el objetivo específico 3, p. 5 (PDF p. 21); la glosa llega en §2.2.1, p. 55 (PDF p. 71): «el lienzo, es decir, el área gráfica donde se dibuja el modelo»
- «guion»: treinta y dos apariciones, la primera en §1.13, p. 38 (PDF p. 54), sin glosa en ninguna; es el instrumento de medición de toda la tesis. Mismo caso de GDL, que nunca se define pese a sostener la comparación Q4-Q9

**Acción.** Una sola pasada por las primeras apariciones: media línea entre rayas o con «es decir» para lienzo, bloqueo por cortante, soluciones manufacturadas, ejemplo canónico, isoparamétrico, guion, GDL, punto de Gauss, biyectivo, restricciones de Dirichlet no homogéneas, inyección de fórmulas y verificación de solución. En el Resumen bastan tres. No crear un glosario nuevo: la Nomenclatura ya existe y solo hay que remitir a ella.

<sub>Absorbe: H-001, H-002, H-028, H-031, H-033, H-037, H-039, H-041, H-042, H-044, H-045, H-106, H-107, H-254, H-256</sub>

#### PAT-02 — Oraciones por encima del tope de ~60 palabras que el propio autor fijó

*claridad · severidad media · 96 apariciones · 2 h*

El documento tiene 96 oraciones de 55 palabras o más y 56 por encima de las 60 que CRITERIOS.md fija como tope. No es un defecto uniforme: la mayoría son enumeraciones técnicas legibles, pero una docena cae justo en los pasajes decisivos —el objetivo general, el contraste de la hipótesis, el veredicto de §3.5— donde el lector necesita detenerse.

**Tres ejemplos:**

- Introducción, «Objetivos», p. 5 (PDF p. 21): el objetivo general es una sola oración de 100 palabras, la más larga del documento (01_introduccion.tex:35)
- §3.5, p. 85 (PDF p. 101): 95 palabras encadenando tres razones de la comparación Q4/Q9 a igualdad de GDL (04_resultados.tex:94)
- §3.8, último párrafo, p. 101 (PDF p. 117): la oración que responde al problema científico tiene 73 palabras y separa sujeto y verbo por 55

**Acción.** Partir solo las que caen en lo que el tribunal lee con atención: objetivo general, hipótesis y cláusulas, cierre de §3.8, conclusiones por objetivo y los veredictos de §3.4 y §3.5. Son unas quince. Dejar las del capítulo 1 y de los anexos: partirlas todas es una pasada de cuatro horas con rendimiento decreciente.

<sub>Absorbe: H-013, H-104, H-108, H-118, H-120, H-122, H-126, H-288, H-046</sub>

#### PAT-03 — Párrafos de 200 a 390 palabras que encadenan cuatro o cinco asuntos

*claridad · severidad media · 17 apariciones · 1 h*

Diecisiete párrafos superan las 200 palabras y encadenan asuntos distintos sin punto y aparte. El caso extremo es el párrafo de apertura de §3.4, de 387 palabras y veinticuatro líneas impresas, que cruza el corte de página y mezcla geometría, material, malla, referencia analítica y protocolo de comparación.

**Tres ejemplos:**

- §3.4, pp. 80-81 (PDF pp. 96-97): párrafo único de 387 palabras (04_resultados.tex:111)
- §2.2.7 «Módulos educativos», p. 68 (PDF p. 84): 299 palabras (03_diseno_implementacion.tex:197)
- Conclusiones, objetivo específico 4, p. 104 (PDF p. 120): 247 palabras (05_conclusiones.tex:19)

**Acción.** Partir en dos o tres los seis párrafos de más de 240 palabras, uno por asunto, sin reescribir el contenido. El de §3.4 se parte solo: datos del modelo / solución de referencia / protocolo de comparación.

<sub>Absorbe: H-105, H-121</sub>

#### PAT-04 — Muletillas de apertura y conectores únicos repetidos hasta la saturación

*claridad · severidad baja · 89 apariciones · 1,5 h*

Tres fórmulas se han vuelto automáticas: «de modo que» cierra 42 oraciones y es prácticamente el único conector consecutivo del documento; «conviene + infinitivo» abre 25 párrafos, 9 de ellos en el capítulo 3, donde da al capítulo de resultados un aire de sucesión de descargos; y «de forma X / de manera X» aparece 22 veces pese a estar prohibido en CRITERIOS.md.

**Tres ejemplos:**

- Resumen, p. ii (PDF p. 2) y a lo largo de todo el cuerpo: «de modo que», 42 apariciones
- §3.6.2, p. 92 (PDF p. 108): «Conviene decir qué prueba y qué no prueba ese resultado»; 25 apariciones del giro
- §2.2.8 «Post-proceso», p. 70 (PDF p. 86): «de forma» / «de manera» + adjetivo, 22 apariciones

**Acción.** Sustitución con control manual: alternar «de modo que» con «así», «por eso», «con lo cual» o punto y seguido en la mitad de los casos; convertir «Conviene decir qué prueba…» en «Ese resultado prueba… y no prueba…»; eliminar «de forma/manera X» por el adverbio o por la reformulación directa. No hace falta llegar a cero.

<sub>Absorbe: H-114, H-115, H-280, H-287, H-291</sub>

#### PAT-05 — El impersonal oculta quién decidió, justo donde la decisión es el aporte

*claridad · severidad media · 11 apariciones · 45 min*

CRITERIOS.md pide «el autor adoptó / eligió» para las decisiones propias, y el documento usa impersonales precisamente donde narra lo que decidió: los criterios de aceptación, las tres decisiones generales de diseño y los umbrales. El efecto es doble: pierde el aporte y da al tribunal la impresión de que los criterios vinieron de fuera. A esto se suman cuatro frases que hablan a un revisor que sospecha en lugar de exponer.

**Tres ejemplos:**

- §2.1.6 «Criterios de aceptación», p. 53 (PDF p. 69): cinco impersonales seguidos en las frases que fijan los umbrales
- §2.2.1, p. 55 (PDF p. 71): «Tres decisiones generales concretan estos requisitos en la herramienta» (03_diseno_implementacion.tex:25), sin sujeto
- Introducción, «Planteamiento del problema», p. 2 (PDF p. 18): cuatro frases dirigidas al revisor y no al lector

**Acción.** Poner al autor como sujeto en las once frases: «el autor fijó», «el autor adoptó», «el autor eligió». Es la corrección más barata del informe y la que más refuerza la defensa, porque convierte decisiones anónimas en criterios asumidos.

<sub>Absorbe: H-095, H-112, H-086, H-117</sub>

#### PAT-06 — Enumeraciones de cuatro o más elementos que siguen en prosa corrida

*aparato-formal · severidad media · 27 apariciones · 1,5 h*

CRITERIOS.md manda a lista o tabla toda enumeración de cuatro elementos o más, y al menos veintisiete siguen en texto corrido. Se concentran en la Introducción y en las Conclusiones, que es donde el tribunal va a buscar qué se hizo y qué se obtuvo.

**Tres ejemplos:**

- Introducción, «Alcance y limitaciones», p. 10 (PDF p. 26): siete enumeraciones largas en prosa en la misma sección
- Introducción, «Estructura del documento», p. 10 (PDF p. 26)
- Conclusiones, objetivo específico 3, p. 104 (PDF p. 120): cinco enumeraciones de cuatro o más miembros

**Acción.** Sacar a lista las de la Introducción y las Conclusiones —unas doce— y dejar en prosa las del capítulo 1 y de los anexos, donde la enumeración es parte de una explicación continua y la lista la rompería.

<sub>Absorbe: H-059, H-068, H-113</sub>

#### PAT-07 — Piezas del software reexplicadas desde cero entre el cuerpo y el Anexo B

*redundancia · severidad media · 12 apariciones · 1,5 h*

El comprobador de salud y sus tres severidades, el catálogo de los ocho módulos, la descripción de los módulos como capa superpuesta con conmutador, la convención DXF y la justificación de embeber TeX Live se explican completos en dos, tres o cuatro lugares, contra la regla propia de una sola aparición canónica más \autoref. La glosa de «lienzo» llega a repetirse palabra por palabra.

**Tres ejemplos:**

- Comprobador de salud: canónica en §2.2.6, p. 65 (PDF p. 81); reexplicado en §2.1.5, p. 49 (PDF p. 65), §B.2, p. 119 (PDF p. 135) y §B.8, p. 130 (PDF p. 146)
- Catálogo de módulos: Tabla 2.8, §2.2.7, p. 67 (PDF p. 83) —canónica—; en prosa en §B.2, p. 120 (PDF p. 136); de nuevo en la Tabla B.2
- Convención DXF y forzado antihorario: §2.2.6, p. 66 (PDF p. 82); §B.1.1, p. 118 (PDF p. 134); §F.3, p. 162 (PDF p. 178)

**Acción.** Dejar la aparición canónica del cuerpo y, en las demás, una línea con \autoref. Excepción deliberada: el Anexo B es un manual de uso y debe poder leerse solo, así que allí se conserva la descripción operativa y se recorta únicamente la teoría ya dada en §2.2.

<sub>Absorbe: H-150, H-151, H-152, H-162, H-164, H-165, H-166, H-173, H-318, H-321, H-324, H-325</sub>

#### PAT-08 — Marco y método reexpuestos desde cero en el capítulo 3 y en las conclusiones

*redundancia · severidad media · 18 apariciones · 2 h*

El método de soluciones manufacturadas y sus tasas teóricas, la acepción de «validación», las cifras de Timoshenko, la anécdota del defecto de extrapolación, la conclusión del consenso de expertos, el argumento de los «dos extremos» y los cinco requisitos se reexponen completos, con las mismas citas y los mismos localizadores, en tres o cuatro sitios cada uno. No es la repetición funcional que el brief autoriza (resumen, matriz de consistencia, contraste): son reexplicaciones desde cero.

**Tres ejemplos:**

- §3.2, pp. 74-75 (PDF pp. 90-91) reexplica el MMS y las tasas teóricas que §1.13, p. 38 (PDF p. 54), ya estableció, con las mismas cinco citas
- La anécdota del defecto de extrapolación se cuenta en §3.7.2, p. 96, y dos veces más dentro de las Conclusiones: p. 105 (PDF p. 121) y «Aportes», p. 106 (PDF p. 122)
- Los cinco requisitos de la herramienta se enumeran íntegros en §1.1, p. 18; Tabla 2.1, p. 41; §2.2.1, pp. 54-55; y Conclusiones OE1, p. 103

**Acción.** Regla única: la primera aparición desarrolla, las siguientes remiten. Recortar §3.2 a una frase con \autoref a §1.13; dejar la anécdota de extrapolación solo en §3.7.2 y una línea en Aportes; enumerar los cinco requisitos completos solo en §1.1 y citarlos por número en los otros tres sitios.

<sub>Absorbe: H-149, H-153, H-154, H-155, H-156, H-157, H-158, H-159, H-160, H-161, H-163, H-168, H-169, H-170, H-171, H-172, H-174, H-175, H-319, H-320, H-322, H-323</sub>

#### PAT-09 — «Validación», «validar» y «error» fuera de la acepción que el documento declara

*consistencia · severidad alta · 11 apariciones · 1,5 h*

§1.13 fija que «validación» designa el contraste con referencias externas de exactitud conocida —la solución analítica y el modelo comercial— y el documento usa la palabra otras diez veces para cosas que esa misma sección excluye: la evaluación de laboratorio, el inventario de módulos, la tabla de cobertura, el comprobador de salud y la medición de los datos. El caso inverso es peor: las Conclusiones llaman «errores» a las diferencias frente a SAP2000.

**Tres ejemplos:**

- §2.1.1, p. 42 (PDF p. 58): «Esa evaluación es una validación de laboratorio», contra §1.13, p. 36 (PDF p. 52)
- Objetivo específico 5, p. 6 (PDF p. 22): «Validar la propuesta contrastando la cobertura…», y título de §3.1, p. 73 (PDF p. 89)
- Conclusiones, OE4, p. 104 (PDF p. 120): «los errores… frente al modelo de SAP2000, de hasta el 0,21 %», contra la nota de la Tabla 3.2, p. 81 (PDF p. 97): «se rotula “diferencia” y no “error”»

**Acción.** Reservar «validación» para Timoshenko y SAP2000. En los demás sitios: «evaluación», «comprobación», «cotejo» o «contraste de cobertura». Reformular el OE5 y propagarlo a la Tabla 2.1, la Tabla 2.3 y las Conclusiones. En las Conclusiones, «diferencia» donde el patrón es SAP2000.

<sub>Absorbe: H-015, H-016, H-071, H-079, H-090, H-096, H-139, H-144, H-304</sub>

#### PAT-10 — Símbolos, precisión y formato numérico desparejos, y Nomenclatura incompleta

*consistencia · severidad media · 45 apariciones · 2 h*

Una misma magnitud cambia de nombre y de símbolo entre tablas vecinas, la transposición se compone de tres maneras, el separador de miles aparece y desaparece dentro del mismo párrafo, los umbrales de calidad llevan uno o dos decimales según el párrafo, y la Nomenclatura registra un símbolo que no se usa nunca mientras omite cuatro que sí.

**Tres ejemplos:**

- Desplazamiento vertical: «flecha» en la Tabla 3.3, p. 82 (PDF p. 98), y u_y en la Tabla 3.4, p. 85 (PDF p. 101); u_y no figura en la Nomenclatura, p. xii (PDF p. 13)
- Tabla 3.9 y el párrafo que la sigue, p. 98 (PDF p. 114): la misma cifra con y sin separador de miles en la misma página
- Nomenclatura, p. xiii (PDF p. 14): κ₂ listada y nunca usada en 187 páginas; L con dos significados; b, H y q entran en §3.4 sin estar registrados

**Acción.** Pasada de uniformización sobre tablas y prosa: un nombre y un símbolo por magnitud, separador de miles siempre o nunca, mismo número de decimales dentro de cada tabla. Completar la Nomenclatura con u_y, b, H, q, JSON y ZIP, advertir los dos sentidos de L y borrar κ₂.

<sub>Absorbe: H-128, H-130, H-131, H-132, H-133, H-135, H-136, H-146, H-292, H-294, H-295, H-297, H-298, H-299, H-300, H-309, H-311, H-314, H-350</sub>

#### PAT-11 — Atribuciones concretas sin localizador de página, y tres sin ninguna cita

*referencias · severidad alta · 15 apariciones · 1,5 h*

De los 172 pares cita-clave del fuente, 38 van sin localizador; la mayoría son remisiones generales a obras completas, que Vancouver no obliga a localizar, pero unas doce sostienen atribuciones concretas —qué hizo un autor, en qué orden presenta la literatura una formulación, de dónde sale un umbral—, que la norma declarada en la p. 11 sí obliga. A ellas se suman tres afirmaciones con fuente nombrada y sin entrada bibliográfica.

**Tres ejemplos:**

- §3.6.1, p. 89 (PDF p. 105): «es el orden con que la literatura de referencia presenta la formulación isoparamétrica» con \autocite{bathe2014fem,cook2002concepts} sin páginas
- §3.4, p. 80 (PDF p. 96): se atribuye una expresión a la norma ACI 318, que no figura en las referencias
- §3.5, p. 84 (PDF p. 100): «El valor de uso extendido para ese desplazamiento, 23,96» sin fuente; la única entrada disponible, [26], publica 23,965

**Acción.** Añadir localizador solo a las citas que sostienen una atribución concreta —son unas doce, y el autor ya tiene los localizadores en el resto del documento—. Dar entrada bibliográfica a ACI 318 o reformular sin nombrarla. Para 23,96, escribir «valor de uso extendido en la literatura de verificación (cf. [26, p. 28], que publica 23,965)». No tocar las remisiones generales: añadirles páginas sería una sobrecorrección.

<sub>Absorbe: H-018, H-076, H-176, H-178, H-183, H-185, H-186, H-187, H-189, H-190, H-328</sub>

#### PAT-12 — El Anexo G, pieza que sostiene el argumento central, se presenta con descuido

*aparato-formal · severidad alta · 18 apariciones · 2,5 h*

El anexo cuya aritmética cierra a mano —la comprobación más importante de toda la auditoría— se imprime sin unidades en ninguna de sus seis tablas, con la misma magnitud a dos, tres, cuatro y siete cifras según la página, con rótulos internos sin tildes y con punto decimal, con una figura de apoyos recortada, con una tabla sin número y, sobre todo, con un sistema de unidades sugerido que vuelve el ejemplo físicamente imposible.

**Tres ejemplos:**

- Encabezado, p. 164 (PDF p. 180): «un sistema de unidades coherente y arbitrario (por ejemplo, kN y cm, con E en kN/cm²)» con E = 225 000 da 2 250 GPa, diez veces el módulo del acero; con kgf/cm² los mismos números son un hormigón (E ≈ 22 GPa, ν = 0,2)
- Tablas G.1 a G.6, pp. 165-170 (PDF pp. 181-186): ninguna declara unidades
- §G.2.6, p. 169 (PDF p. 185): ε con siete cifras significativas (1,924718 × 10⁻⁴) junto a σ con tres, B con cuatro y σVM con dos

**Acción.** Cambiar el ejemplo de unidades a kgf y cm y decir en una línea que los valores corresponden a un hormigón; poner unidades en los encabezados de las seis tablas; fijar la precisión por magnitud; numerar la tabla de reacciones; regenerar las tres figuras con tildes, coma decimal y los apoyos completos; y añadir el chequeo global de equilibrio que los datos ya permiten.

<sub>Absorbe: H-040, H-056, H-057, H-058, H-092, H-116, H-138, H-167, H-207, H-208, H-209, H-221, H-222, H-236, H-237, H-258, H-263, H-264, H-265, H-266, H-276, H-293, H-302, H-303, H-352</sub>

#### PAT-13 — Los índices reproducen leyendas completas y omiten quince secciones

*aparato-formal · severidad baja · 34 apariciones · 1 h*

Los índices de figuras y de tablas imprimen la leyenda entera —hasta seis líneas— en diecinueve entradas de los anexos, en lugar del título breve; el índice general no lista las quince secciones sin numerar de la Introducción y de las Conclusiones, que son justo las que el tribunal busca (Objetivos, Hipótesis, Alcance, Aportes, Limitaciones, Recomendaciones), ni los propios índices de figuras y tablas.

**Tres ejemplos:**

- Índice de figuras, pp. vi-viii (PDF pp. 7-9): entradas B.1 a G.4 con la leyenda completa y el número de página pegado al texto
- Índice general, pp. ii-v (PDF pp. 3-6): no aparecen las quince secciones de la Introducción y de las Conclusiones
- Índice general, p. ii (PDF p. 3): lista Resumen y Nomenclatura pero no los índices de figuras y de tablas

**Acción.** Poner título breve en el argumento opcional de \caption[…] de las diecinueve figuras y tablas de los anexos, y añadir \addcontentsline para las quince secciones sin numerar y para los dos índices. Es mecánico y se hace de una vez.

<sub>Absorbe: H-048, H-051, H-052, H-053, H-219, H-259, H-339</sub>

---

## 7. Hallazgos de severidad alta que no pertenecen a ningún patrón

Siete defectos individuales tras el control final, que rebajó seis de los trece que tenía la
primera versión (§13 explica cuáles y por qué). Cada uno tiene en el plan de corrección su
propuesta concreta, con el texto reformulado cuando la reformulación no es obvia.

Son: **H-004** y **H-012** (calibración del «18 de 18»), **H-014** (la PI-3 inexistente),
**H-017** (los localizadores de Bishay), **H-021** (el modelo de SAP2000 no es reproducible),
**H-022** (la etapa 6 en la memoria) y **H-024** (el OE3 sin su conclusión completa).

| ID | Eje | Ubicación | Defecto | Esf. |
|---|---|---|---|---|
| **H-014** | consistencia | Nomenclatura, «Abreviaturas y siglas», p. xv (PDF p. 16) | La Nomenclatura anuncia una PI-3 que no existe: el documento solo tiene PI-1 y PI-2 | 5 min |
| **H-017** | referencias | §1.2 «Fundamentos pedagógicos», p. 19 (PDF p.35) —… | Los seis localizadores de [16] Bishay caen fuera del rango de páginas que declara la en… | 30 min |
| **H-004** | calibración | §2.1.4, p. 49 (PDF p. 65) | El universo de contenido excluye el único ítem que el software no cubre, y luego se rep… | 30 min |
| **H-012** | calibración | Tabla 3.7, fila FEA30, p. 91 (PDF p.107) | FEA30 acredita como «Instrumento de EduFEM» una extrapolación de Richardson que el soft… | 15 min |
| **H-021** | riesgo de defensa | §3.4, pp. 80-81 (PDF pp. 96-97) | ¿Cómo modeló los apoyos de la viga y con qué discretización la resolvió en SAP2000? | 1 h |
| **H-022** | trazabilidad | §3.6.1, p. 87 (PDF p.103) | Criterio «9 de 9 etapas en la memoria»: la etapa 6 no aparece ni en el Anexo G ni en la… | 2 h+ |
| **H-024** | trazabilidad | Conclusiones, «Objetivo específico 3 —desarrollar—», pp… | La conclusión del OE3 omite el intercambio de datos que el propio objetivo promete | 15 min |

A ellos se suman **tres** hallazgos altos absorbidos por un patrón, que se corrigen con él y no
uno a uno: **H-001** en PAT-01 (términos sin glosa en el Resumen), **H-013** en PAT-02 (el
objetivo general, de 100 palabras) y **H-015** en PAT-09 («validación» en tres sentidos dentro
de §2.1). PAT-11 y PAT-12 son patrones de severidad alta por su impacto agregado, pero no
absorben ningún hallazgo alto individual.

---

## 8. Hallazgos de severidad media y baja

Ciento setenta hallazgos sueltos —112 de severidad media y 58 de severidad baja—, agrupados
por capítulo y ordenados por severidad dentro de cada uno. La
evidencia literal, el diagnóstico completo y la acción de cada uno están en el anexo de datos
(`HALLAZGOS_TODOS.json`, campo `n`); aquí va lo que hace falta para decidir si se atiende.

Los de severidad baja son, casi todos, trabajo de una sola pasada final: índices, leyendas,
tildes en las figuras, uniformidad de decimales. El plan los reúne en un único bloque (B12) para
hacerlos de golpe con el PDF recompilado al lado.


#### Introducción — 31 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-030 | accesibilidad | media | Introducción, «Estructura del documento», p. 10 (PDF p… | «Estructura del documento» no da ninguna guía de lectura al lector que no cur… | 30 min |
| H-060 | aparato formal | media | «Planteamiento del problema», p. 2 (PDF p.18) → Tabla… | La Tabla 1.1 sostiene la afirmación central del planteamiento, pero aparece c… | 15 min |
| H-006 | calibración | media | Resumen, p. i (PDF p.2) | «los dieciocho contenidos que un consenso de expertos exige» oculta que son 1… | 15 min |
| H-078 | calibración | media | Introducción, «Planteamiento del problema», p. 2-3 (PDF… | Premisa central sobre la práctica profesional enunciada dos veces sin ninguna… | 15 min |
| H-080 | calibración | media | Hipótesis, p. 6 (PDF p. 22) | La hipótesis afirma «mejorar» y «elevando» sin línea de base medida, y nunca… | 30 min |
| H-081 | calibración | media | OE5, p. 6 (PDF p. 22) y PI-1, p. 7 (PDF p. 23) —las dos… | «La literatura especializada exige» atribuye a toda una disciplina lo que rep… | 30 min |
| H-082 | calibración | media | Resumen, p. i (PDF p. 2) y Aportes del trabajo, p. 106… | El Resumen y las conclusiones dan solo las componentes primarias y omiten el… | 15 min |
| H-087 | calibración | media | Resumen, p. i (PDF p.2) | El Resumen presenta la memoria como reproducible a mano sin acotarla al ejemp… | 5 min |
| H-093 | calibración | media | «Planteamiento del problema», p. 2 (PDF p.18) | «Ninguno reúne» se apoya en celdas «No consta», que la nota de la Tabla 1.1 d… | 5 min |
| H-109 | claridad | media | Resumen, p. ii (PDF p.2) | El Resumen usa cinco veces «trazabilidad» y «verificabilidad» sin decir qué s… | 15 min |
| H-140 | consistencia | media | «Planteamiento del problema», p. 2 (PDF p.18) | El vacío del estado del arte son «tres atributos» en la Introducción y «ocho»… | 15 min |
| H-179 | referencias | media | «Objeto de estudio y campo de acción», p. 3 (PDF p.19) —… | [8] Álvarez de Zayas, monografía irrecuperable, sostiene los cuatro pilares d… | 2 h+ |
| H-181 | referencias | media | Introducción, «Estructura del documento», p. 11 (PDF p.27) | La norma declarada en p. 11 atribuye a ICMJE/NLM rasgos que no son suyos | 15 min |
| H-191 | riesgo de defensa | media | Introducción, «Planteamiento del problema» y… | ¿Qué dato tomó usted en la Carrera de la UATF para afirmar que allí existe el… | 1 h |
| H-195 | riesgo de defensa | media | Introducción, «Hipótesis y preguntas de investigación»… | La hipótesis dice «elevando la trazabilidad»: ¿elevándola respecto de qué med… | 1 h |
| H-197 | riesgo de defensa | media | Introducción, «Alcance y limitaciones», pp. 8-9 (PDF pp… | Usted ofrece el software para presas, muros y túneles, pero nunca validó defo… | 30 min |
| H-205 | riesgo de defensa | media | Resumen, p. i (PDF p.2) | El Resumen invoca «el alcance declarado» sin declararlo en ninguna parte del… | 15 min |
| H-228 | trazabilidad | media | Introducción, p. 2 (PDF p.18) | El diagnóstico del OE1 se enuncia con tres recuentos de atributos sin mapa en… | 15 min |
| H-229 | trazabilidad | media | Introducción, p. 3 (PDF p.19) | El campo de acción se declara una sola vez y nunca se retoma en el diseño ni… | 15 min |
| H-232 | trazabilidad | media | Objetivo específico 3, p. 5 (PDF p.21) | El OE3 promete «cada etapa» con modulo educativo; el criterio de aceptacion p… | 15 min |
| H-234 | trazabilidad | media | Resumen, p. i (PDF p.2) | El Resumen no nombra el método de investigación | 15 min |
| H-238 | trazabilidad | media | «Hipótesis», cláusula (a), p. 7 (PDF p.23) —la tercera… | La cláusula (a) exige cobertura de contenido, que no se sigue de la definició… | 15 min |
| H-257 | aparato formal | baja | Indice general, p. v (PDF p.6) | La entrada del Anexo E en el índice general choca contra el número de página | 5 min |
| H-260 | aparato formal | baja | Material preliminar, entre la portada y el Resumen (PDF… | El PDF compilado no incluye la declaración de originalidad ni los agradecimie… | 15 min |
| H-005 | calibración | baja | Resumen, p. i (PDF p.2) y §3.7.1 «Alcances», p. 96 (PDF… | El Resumen omite el subindice de la tension normal (sigma_x) que el cuerpo si… | 15 min |
| H-007 | calibración | baja | «Justificación», plano académico, p. 4 (PDF p.20) | «La literatura... reporta que... favorecen la instrucción»: afirmación de efe… | 15 min |
| H-281 | calibración | baja | «Alcance y limitaciones», p. 9 (PDF p.25) | «El plano es la mínima dimensión en la que aparece el carácter de continuo» e… | 5 min |
| H-330 | riesgo de defensa | baja | Introducción, «Alcance y limitaciones», p. 9 (PDF p. 25) | ¿Por qué Q4 y Q9, y no triángulos, elementos de orden superior o tres dimensi… | 5 min |
| H-334 | riesgo de defensa | baja | Introducción, «Hipótesis», p. 7 (PDF p. 23) | Su hipótesis: ¿qué habría tenido que pasar para que quedara refutada? | 5 min |
| H-340 | tipografía | baja | Resumen, p. i (PDF p.2) | El Resumen se aparta de APA 7 en tres puntos verificables sobre el PDF | 30 min |
| H-342 | tipografía | baja | «Alcance y limitaciones», p. 9 (PDF p.25) | La coma cumple dos funciones distintas dentro del mismo corchete de cita | 15 min |

#### Capítulo 1 — Marco teórico — 13 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-027 | accesibilidad | media | §1.6 a §1.13, pp. 25-39 (PDF pp. 41-55) | Quince páginas de formalismo (§1.6-§1.13) sin una sola figura ni tabla de apo… | 2 h+ |
| H-029 | accesibilidad | media | §1.8, p. 26 (PDF p. 42) | La Ecuación 1.15 (rigidez elemental) entra sin decir qué mide ke ni por qué B… | 15 min |
| H-032 | accesibilidad | media | §1.3, p. 21 (PDF p. 37) | La Ecuación 1.2 (trabajos virtuales) no se lee nunca en palabras: solo se nom… | 15 min |
| H-034 | accesibilidad | media | §1.12, p. 35 (PDF p. 51) | Tres páginas del capítulo 1 apilan de nueve a dieciséis símbolos nuevos cada… | 1 h |
| H-035 | accesibilidad | media | §1.4, p. 22 (PDF p. 38) | La matriz constitutiva D (Ecuaciones 1.4 y 1.5) entra sin una frase que diga… | 15 min |
| H-008 | calibración | media | §1.1, Tabla 1.1, p. 16-17 (PDF p. 32-33) | La Tabla 1.1 hace juicios de calidad didáctica que el propio texto promete no… | 30 min |
| H-094 | calibración | media | §1.13 Verificación y validación, p. 36 (PDF p. 52) | «Acepción corriente en la práctica del MEF» afirmada sin cita, justo en la de… | 15 min |
| H-218 | tipografía | media | §1.8, p. 26 (PDF p.42) | Espaciado vertical irregular alrededor de flotantes sueltos (huecos en blanco… | 1 h |
| H-267 | aparato formal | baja | §1.4 y §1.7-1.8, p. 22-26 (PDF p. 38-42) | Tres ecuaciones con label nunca se referencian desde ningún otro punto del do… | 5 min |
| H-279 | calibración | baja | Nota de la Tabla 1.1, §1.1, p. 17 (PDF p. 33) | Tabla 1.1 juzga ANSYS, Abaqus, CALFEM y FEniCS sin fuente, contra su propia n… | 1 h |
| H-286 | claridad | baja | §1.2 Principios que orientan la exposición del… | §1.2 presenta cuatro decisiones de diseño del autor como derivaciones lógicas… | 30 min |
| H-329 | riesgo de defensa | baja | §1.1, pp. 14-15 (PDF pp. 30-31) | ¿Qué aporta esto que no aporte ED-Elas2D, que existe desde 1998? | 5 min |
| H-332 | riesgo de defensa | baja | §1.13, p. 36 (PDF p. 52) | ¿Por qué SAP2000 es una referencia válida, si también es una aproximación num… | 5 min |

#### §2.1 — Diseño metodológico — 34 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-043 | accesibilidad | media | §2.1.6, Tabla 2.4, fila «Soluciones manufacturadas», p… | El único criterio numérico sin su valor: «Teórica ±0,5» no dice cuál es la ta… | 15 min |
| H-061 | aparato formal | media | §2.1.1, Tabla 2.1, p. 41 (PDF p.57) | La Tabla 2.1 se titula «Las seis actividades» y tiene siete filas | 15 min |
| H-062 | aparato formal | media | §2.1.2, Tabla 2.2, p. 45 (PDF p.61) | La leyenda de la Tabla 2.2 no explica la raya que separa las variables de las… | 15 min |
| H-009 | calibración | media | §2.1.6, Tabla 2.4, p. 52 (PDF p.68) | Los tres umbrales de exactitud (3 %, 1 % y 1,5 %) no se justifican en ninguna… | 30 min |
| H-111 | claridad | media | Capítulo 2, p. 40 (PDF p.56) | El título del capítulo 2 obliga al propio capítulo a desambiguar la palabra «… | 15 min |
| H-119 | claridad | media | §2.1.6, Tabla 2.4, p. 51 (PDF p.67) | El criterio del inventario cubre «etapas 1 a 7» de nueve sin decir en ningún… | 15 min |
| H-127 | consistencia | media | §2.1.4, p. 47 (PDF p. 63) frente a Anexo B §B.6, p. 123… | «Tres casos de estudio» designa dos conjuntos distintos según el capítulo | 15 min |
| H-134 | consistencia | media | §2.1.4, p. 49 (PDF p. 65) frente a la nota de la Tabla… | Los 18 ítems fuera del alcance disciplinar se enumeran en nueve grupos en la… | 5 min |
| H-141 | consistencia | media | §2.1.1, p. 43 (PDF p.59) y §2.1.4, p. 47 (PDF p.63) | La unidad de análisis se define dos veces y con dos formulaciones distintas | 15 min |
| H-142 | consistencia | media | §2.1.1, p. 41-42 (PDF p.57-58) | «Artefacto» aparece cuatro veces cuando CRITERIOS lo admite una sola vez en §… | 5 min |
| H-201 | riesgo de defensa | media | §2.1.5, p. 50 (PDF p. 66) | Los 18 contenidos los definieron expertos mexicanos de ingeniería mecánica: ¿… | 15 min |
| H-211 | riesgo de defensa | media | §2.1.2, p. 44 (PDF p.60) | No se argumenta por qué contar etapas expuestas mide la trazabilidad; el salt… | 15 min |
| H-023 | trazabilidad | media | §2.1.1, p. 42 (PDF p.58) | Tres formulaciones anuncian un cotejo manual ejecutado; el criterio que se ap… | 1 h |
| H-223 | trazabilidad | media | Tabla 2.4, p. 52 (PDF p.68), fila «Intercambio de datos»… | El intercambio de datos es objetivo y criterio, pero no cláusula, ni requisit… | 30 min |
| H-224 | trazabilidad | media | Tabla 2.3, p. 46 (PDF p.62), fila «3. Desarrollar el… | La matriz de consistencia cierra el OE3 con su propia descripción, sin ningún… | 15 min |
| H-225 | trazabilidad | media | Tabla 2.4, p. 52 (PDF p.68), última fila | El criterio del ejemplo canónico no recibe bloque de veredicto en el cuerpo y… | 30 min |
| H-226 | trazabilidad | media | Tabla 2.1, p. 41 (PDF p.57) frente a Tabla 2.3, p. 46… | La Tabla 2.1 y la Tabla 2.3 dan dos mapas distintos de objetivo a sección | 15 min |
| H-240 | trazabilidad | media | §2.1.2, p. 43 (PDF p.59) y §2.1.3, p. 46 (PDF p.62) | La hipótesis afirma «elevar» la variable dependiente, pero ningún indicador s… | 30 min |
| H-241 | trazabilidad | media | §2.1.3, p. 47 (PDF p.63) | El intercambio de datos es criterio de la cláusula (a) aunque §2.1.3 declara… | 30 min |
| H-242 | trazabilidad | media | §2.1.1, Tabla 2.1, fila «2. Definir los objetivos de la… | La Tabla 2.1 envía a buscar los requisitos donde no están: §2.2.1 es quien lo… | 5 min |
| H-243 | trazabilidad | media | §2.1.3, Tabla 2.3, p. 46 (PDF p.62) | La matriz de consistencia no lleva la hipótesis ni sus dos cláusulas, y en el… | 30 min |
| H-244 | trazabilidad | media | §2.1.6, p. 51 (PDF p.67) | «Quedaron fijados antes de las corridas» no cubre los criterios documentales,… | 15 min |
| H-245 | trazabilidad | media | §2.1.6, Tabla 2.4, p. 51-52 (PDF p.67-68) | La Tabla 2.4 declara trece criterios y la tabla de veredictos de §3.8 reporta… | 30 min |
| H-249 | trazabilidad | media | Tabla 2.4, §2.1.6, p. 52 (PDF p.68) —origen— y Tabla… | La Tabla 3.10 cuenta como criterio de la cláusula (a) el intercambio de datos… | 30 min |
| H-268 | aparato formal | baja | §2.1.6, Tabla 2.4 (continuación), p. 52 (PDF p.68) | En la continuación de la Tabla 2.4 la fila «Intercambio de datos» queda sin s… | 15 min |
| H-269 | aparato formal | baja | §2.1.6, Tabla 2.4, p. 52 (PDF p.68) | «Tres puntos de control» se usa como criterio sin definirlos ni remitir a don… | 5 min |
| H-270 | aparato formal | baja | §2.1.2, p. 43 → Tabla 2.2 en p. 45 (PDF p.59 → PDF p.61) | La Tabla 2.2 se llama en la p.43 y aparece dos páginas después | 15 min |
| H-290 | claridad | baja | §2.1.2, p. 44 (PDF p.60) | Relativa ambigua: «los expertos que tienen instrumento en el software» | 5 min |
| H-296 | consistencia | baja | §2.1.2, p. 43-44 (PDF p. 59-60) | «Nueve etapas… cada una en su sección», pero las nueve etapas ocupan siete se… | 5 min |
| H-306 | consistencia | baja | §2.1.3, p. 46 (PDF p.62) | El contrato editorial del autor dice «podrá afectar» y el documento dice «pod… | 5 min |
| H-196 | riesgo de defensa | baja | §2.1.1, p. 42 (PDF p. 58) | ¿Cómo sostiene que el software es «educativo» si no midió a ningún estudiante? | 30 min |
| H-203 | riesgo de defensa | baja | §2.1.1, «Unidad de análisis y versión evaluada», p. 43… | ¿Cómo se replica este trabajo si en dos años el software ya no compila? | 1 h |
| H-333 | riesgo de defensa | baja | §2.1.4, p. 47 (PDF p. 63) | ¿Cuál es la población y cuál la muestra de esta investigación? | 5 min |
| H-343 | tipografía | baja | §2.1.1, p. 41 (PDF p.57) | Los tres encabezados de párrafo de §2.1.1 salen impresos con dos puntos segui… | 5 min |

#### §2.2 — El software EduFEM — 9 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-036 | accesibilidad | media | §2.2.6 «Pre-proceso interactivo», pp. 63-67 (PDF pp… | §2.2.6 acumula decisiones de implementación sin el cierre de propósito que ti… | 30 min |
| H-070 | calibración | media | §2.2.3 «Motor de cálculo», p. 63 (PDF p.79) | «Ningún resultado procede de un elemento cuya geometría invalide el mapeo» co… | 5 min |
| H-143 | consistencia | media | §2.2.3 Arquitectura por capas, Figura 2.2 vs. Tabla 2.6… | La Figura 2.2 llama «validación» y «undo» a lo que la Tabla 2.6, en la misma… | 30 min |
| H-020 | riesgo de defensa | media | §2.2.2, nota de la Tabla 2.5, p. 57 (PDF p. 73) | La tesis llama libre al software sin nombrar nunca la licencia, y la nota la… | 1 h |
| H-271 | aparato formal | baja | §2.2.2 (sec:stack), p. 57 y §2.2.3 (sec:arquitectura), p… | Las secciones «Tecnologías empleadas» y «Arquitectura por capas» tienen label… | 15 min |
| H-275 | calibración | baja | §2.2.6 «Módulos educativos», p. 69 (PDF p.85) | «Garantiza» sin la fórmula «por construcción» que el propio CRITERIOS exige,… | 5 min |
| H-307 | consistencia | baja | §2.2.2 Tecnologías empleadas, nota de la Tabla 2.5, p. 57… | «Programa» se usa para nombrar a EduFEM, término prohibido salvo para softwar… | 5 min |
| H-338 | tipografía | baja | §2.2.9, p. 72 (PDF p.88) | Página casi vacía por el salto obligatorio de capítulo (una sola oración suel… | 15 min |
| H-353 | trazabilidad | baja | §2.2.7 Módulos educativos, p. 67 (PDF p. 85) | El requisito 4 (cobertura de contenido) es el único de los cinco que nunca se… | 5 min |

#### Capítulo 3 — Resultados — 50 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-063 | aparato formal | media | Tabla 3.2, p. 81 (PDF p.97) | Las columnas de error mezclan cuatro decimales con dos y declaran más precisi… | 30 min |
| H-064 | aparato formal | media | Tabla 3.1, p. 76 (PDF p.92) | La Tabla 3.1 no dice que sus normas son adimensionales ni remite a los errore… | 15 min |
| H-065 | aparato formal | media | Figura 3.5, p. 88 (PDF p.104) | La Figura 3.5, única evidencia del criterio «3 de 3 fases sobre el mismo lien… | 1 h |
| H-067 | aparato formal | media | Tabla 3.9, p. 98 (PDF p.114) | La Tabla 3.9 lleva su nota metodológica dentro de la leyenda y usa un filete… | 15 min |
| H-003 | calibración | media | §3.8, p. 100 (PDF p.116) | La memoria en PDF degrada su desarrollo por encima de cierto tamano, y el doc… | 1 h |
| H-011 | calibración | media | §3.8, p. 100 (PDF p.116) | El universal «Cada magnitud […] se comprobó contra un patrón independiente» l… | 15 min |
| H-072 | calibración | media | §3.6 «Cobertura de contenido», p. 90 (PDF p.106) | La tabla de cobertura «demuestra» lo que en realidad respalda: cotejo documen… | 15 min |
| H-074 | calibración | media | §3.3 «Consistencia interna del modelo de datos», p. 79… | Una prueba con un juego de identificadores «descarta los fallos» de indexació… | 5 min |
| H-075 | calibración | media | §3.1 «Medición de los datos y validación de la medición»… | «La confiabilidad de estas mediciones se asegura por tres vías»: tres precauc… | 5 min |
| H-077 | calibración | media | §3.7.4 «Limitaciones observadas», tab:tiempos y párrafo… | La leyenda de tiempos describe el protocolo peor de lo que es, y las razones… | 15 min |
| H-085 | calibración | media | Título de la Tabla 3.7, §3.6.2, p. 91 (PDF p.107) | La columna «Evidencia» de la tabla de cobertura dice «demuestra» donde solo r… | 15 min |
| H-088 | calibración | media | §3.7.4, p. 98 (PDF p.114) | Factores de aceleracion con una cifra decimal sobre corridas cuya variabilida… | 15 min |
| H-097 | calibración | media | §3.2, p. 76 (PDF p.92) | «Descarta» atribuye a dos pruebas un poder de exclusión que el propio capítul… | 15 min |
| H-099 | calibración | media | Leyenda de la Tabla 3.7, p. 91 (PDF p.107) | «demuestra» y «se cumple por construcción» infringen la tabla de verbos por t… | 15 min |
| H-100 | calibración | media | §3.7.1, primer párrafo, p. 93 (PDF p.109) | «Eso descarta errores de orden» se emite sin la salvedad que llega dos subsec… | 15 min |
| H-110 | claridad | media | §3.7 Interpretación de los resultados, p. 93 (PDF p.109) | §3.7 no tiene párrafo de apertura y sus dos primeros subtítulos no anuncian s… | 15 min |
| H-123 | claridad | media | §3.6.3, p. 93 (PDF p.109) | «el trabajo entre pares» aparece como límite declarado sin antecedente en nin… | 15 min |
| H-124 | claridad | media | §3.6.1, párrafo «Organización de la interfaz», p. 90 (PDF… | «Observado: 3 de 3» queda ambiguo tras una oración que habla de los tres caso… | 5 min |
| H-125 | claridad | media | §3.7.4, p. 97 (PDF p.113) | «limitan la aplicabilidad a casos de ingeniería más allá de los formativos» d… | 5 min |
| H-129 | consistencia | media | Tabla 3.1, p. 76 (PDF p. 92) frente a Tabla D.2, p. 140… | El mismo caso da dos errores distintos en el cuerpo y en el Anexo D porque un… | 15 min |
| H-145 | consistencia | media | Tabla 3.6 y párrafo siguiente, p. 89 (PDF p.105) | La Tabla 3.6 atribuye el conmutador a M1-M7 y el texto de la misma página sol… | 5 min |
| H-177 | referencias | media | Nota de la Tabla 3.7 «Tabla de cobertura de contenido»… | Cita en estilo autor-año (APA) dentro de un documento Vancouver, en la nota d… | 5 min |
| H-194 | riesgo de defensa | media | §3.8, Tabla 3.10, pp. 99-100 (PDF pp. 115-116) | Todos los criterios de trazabilidad dan 100 % y los verificó usted: ¿qué podí… | 30 min |
| H-198 | riesgo de defensa | media | §3.7.2, p. 96 (PDF p. 112) | Usted encontró un error en su propio software. ¿Cuántos más puede haber? | 1 h |
| H-212 | riesgo de defensa | media | §3.4, Tabla 3.3, p. 82 (PDF p.98) | La flecha calculada supera a la analítica y a SAP2000 y el documento no expli… | 30 min |
| H-213 | riesgo de defensa | media | §3.4, p. 82 (PDF p.98) | El 4,56 % de las componentes secundarias se reporta sin decir que queda fuera… | 15 min |
| H-214 | riesgo de defensa | media | Tabla 3.10, bloque «Cláusula (a)», p. 99 (PDF p.115) | La Tabla 3.10 muestra seis criterios donde umbral y observado coinciden, sin… | 15 min |
| H-231 | trazabilidad | media | §3.3, p. 80 (PDF p.96) y §3.6.1, p. 90 (PDF p.106) | El criterio del intercambio de datos recibe dos veredictos en dos secciones d… | 15 min |
| H-246 | trazabilidad | media | §3.3, p. 79 (PDF p.95) | §3.3 no declara a qué cláusula de la hipótesis responde, y §2.1.6 la asigna a… | 15 min |
| H-247 | trazabilidad | media | §3.6.2, p. 90-91 (PDF p.106-107), frente a §2.1.5, p. 50… | §3.6.2 reformula la regla de marcado más débil que como §2.1.5 la declara, y… | 1 h |
| H-250 | trazabilidad | media | §3.7.4, p. 98 (PDF p.114) | Tres factores de aceleración sostienen la respuesta sobre escalabilidad sin t… | 30 min |
| H-251 | trazabilidad | media | Tabla 3.10, columna «Dónde», p. 99 (PDF p.115) | Dos filas de la Tabla 3.10 remiten a un lugar que no contiene todo lo que la… | 5 min |
| H-066 | aparato formal | baja | §3.7.4, p. 97-99 (PDF p.113-115) | «Limitaciones observadas» dedica dos de sus tres páginas a exhibir el desempe… | 1 h |
| H-272 | aparato formal | baja | §3.6.1, p. 87-89 (PDF p.103-105) | La Tabla 3.6 se menciona antes que la Figura 3.5 pero se imprime después | 15 min |
| H-273 | aparato formal | baja | §3.7, p. 93 (PDF p.109) | El título de §3.7 queda pegado al de §3.7.1 sin texto intermedio | 15 min |
| H-277 | calibración | baja | §3.5 «Validación con la membrana de Cook», p. 85 (PDF… | «Significativa» sin prueba estadística en un trabajo que se declara de enfoqu… | 5 min |
| H-308 | consistencia | baja | Tabla 3.1, fila N = 16 del bloque Q4, p. 76 (PDF p.92) | La tasa H1 de 1,01 del Q4 no se recupera de los errores que muestra la misma… | 15 min |
| H-310 | consistencia | baja | §3.5, p. 84 (PDF p.100) | Se presenta como coincidente con 0,05 % una distancia que vale 0,04 % | 5 min |
| H-312 | consistencia | baja | Tabla 3.6, fila «Pre-proceso», p. 89 (PDF p.105) | La Tabla 3.6 asigna al pre-proceso una «etapa» que no está entre las nueve qu… | 15 min |
| H-313 | consistencia | baja | Figura 3.5, p. 88 (PDF p.104) | La leyenda de la Figura 3.5 usa «la aplicación», término que CRITERIOS.md pro… | 5 min |
| H-315 | consistencia | baja | Tabla 3.7, fila FEM8, p. 92 (PDF p.108) | FEM8, formulación isoparamétrica, se acredita con M4, que es la matriz consti… | 5 min |
| H-193 | riesgo de defensa | baja | §3.4, p. 80 (PDF p. 96) | Ese 0,04 %, ¿de qué malla sale? ¿Y qué habría dado con otra? | 2 h+ |
| H-215 | riesgo de defensa | baja | §3.8, p. 101 (PDF p.117) | El argumento de que la hipótesis no es tautológica descansa en una sola anécd… | 15 min |
| H-344 | tipografía | baja | Figuras 3.1(a), 3.1(b) y 3.2, p. 78 (PDF p.94) | El rótulo del eje de las figuras de convergencia va sin tilde: «tamaño caract… | 15 min |
| H-345 | tipografía | baja | Figura 3.3, p. 83 (PDF p.99) | La Figura 3.3 muestra las reacciones con punto decimal, contra la coma del do… | 15 min |
| H-346 | tipografía | baja | p. 78 (PDF p.94) | La página de las figuras de convergencia queda con una franja en blanco de un… | 30 min |
| H-347 | tipografía | baja | §3.6.1, p. 87 y p. 90 (PDF p.103 y p.106) | Punto doble al final de los tres títulos de párrafo de §3.6.1 | 5 min |
| H-348 | tipografía | baja | §3.8, p. 101 (PDF p.117) | Discordancia «las Subsección 3.6.1 y Subsección 3.6.2» por doble \autoref tra… | 5 min |
| H-349 | tipografía | baja | §3.6.1, p. 90 (PDF p.106) | Ruta de archivo partida por el guion bajo sin señal de continuación | 5 min |
| H-351 | trazabilidad | baja | §3.7.1, p. 95 (PDF p.111) | La cifra 0,16 % que sostiene una comparación no tiene celda en ninguna tabla | 30 min |

#### Conclusiones y recomendaciones — 19 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-047 | accesibilidad | media | Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) | Cuatro tasas de convergencia y «las dos normas del error» sin decir qué miden | 15 min |
| H-073 | calibración | media | Conclusiones, tercer párrafo, p. 102 (PDF p.118) | «Queda demostrado» en Conclusiones, donde la evidencia es cobertura documenta… | 5 min |
| H-083 | calibración | media | Conclusiones, p. 102 (PDF p. 118) | «Queda demostrado… y que EduFEM las tiene»: el verbo más fuerte del documento… | 15 min |
| H-101 | calibración | media | Limitaciones, último ítem, p. 108 (PDF p.124) | «su costo en memoria […] crece más que linealmente»: la Tabla 3.9 mide lo con… | 15 min |
| H-102 | calibración | media | Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) —… | Las cifras de Timoshenko se recuerdan sin las dos salvedades que el capítulo… | 15 min |
| H-103 | calibración | media | Conclusiones, tercer párrafo, p. 102 (PDF p.118) —… | «Queda demostrado» y «El trabajo lo establece» exceden el tipo de evidencia d… | 15 min |
| H-147 | consistencia | media | Conclusiones, contraste de hipótesis, p. 105 (PDF p.121) | «tres estudios de convergencia del desplazamiento»: recuento que el cuerpo no… | 5 min |
| H-148 | consistencia | media | Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) | «criterios de aceptación escritos en los propios guiones» contradice el lugar… | 5 min |
| H-216 | riesgo de defensa | media | Limitaciones y Recomendaciones, pp. 107-110 (PDF… | La tasa de 1,54 del campo de tensiones del Q4 no llega ni a limitaciones ni a… | 30 min |
| H-227 | trazabilidad | media | Conclusiones, primer párrafo, p. 102 (PDF p.118), frente… | El objetivo general se declara cumplido restituyendo solo sus medios, no su c… | 15 min |
| H-230 | trazabilidad | media | Conclusiones, «Limitaciones», p. 107 (PDF p.123), frente… | Una limitación declarada no recibe recomendación, pese a que el texto dice qu… | 30 min |
| H-252 | trazabilidad | media | Conclusiones, Objetivo específico 3, p. 103 (PDF p.119) | El intercambio de datos (CSV/DXF) es parte del OE3 y criterio de la Tabla 3.1… | 15 min |
| H-253 | trazabilidad | media | Recomendaciones y trabajo futuro, pp. 108-109 (PDF… | Dos de las ocho recomendaciones no se siguen de ninguna limitación de la list… | 15 min |
| H-283 | calibración | baja | Conclusiones, cierre del contraste de hipótesis, p. 105… | «El desarrollo de EduFEM mejoró…de caja negra a procedimiento a la vista»: co… | 15 min |
| H-284 | calibración | baja | Conclusiones, Objetivo específico 3, p. 104 (PDF p.120) | La trazabilidad depende de una decisión en el OE3 y de tres en los Aportes | 5 min |
| H-285 | calibración | baja | Recomendaciones, «Guía de uso en la cátedra», p. 109 (PDF… | «El manual del Anexo B enseña a operar el software»: verbo de enseñanza | 5 min |
| H-316 | consistencia | baja | Conclusiones, segundo párrafo, p. 102 (PDF p.118) | «medio de cálculo»: término inédito que responde al problema científico | 15 min |
| H-317 | consistencia | baja | Conclusiones, Objetivo específico 2, p. 103 (PDF p.119) | El segundo principio cambia de nombre respecto de §1.2 | 5 min |
| H-204 | riesgo de defensa | baja | Conclusiones, «Recomendaciones», «Guía de uso en la… | ¿Quién va a usar esto en la Carrera, y con qué compromiso? | 2 h+ |

#### Referencias bibliográficas — 5 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-180 | referencias | media | «Referencias bibliográficas», entrada [8], p. 111 (PDF… | La entrada [8] se compone como si fuera un artículo y con puntuación distinta… | 15 min |
| H-182 | referencias | media | «Referencias bibliográficas», entrada [26], p. 113 (PDF… | La única fuente publicada del caso de Cook es un preprint de arXiv sobre un e… | 30 min |
| H-261 | aparato formal | baja | Referencias bibliograficas, entrada [15], p. 112 (PDF p… | Orden confuso de subtitulo y volumen en la entrada [15] (Onate) | 30 min |
| H-301 | consistencia | baja | Referencias bibliograficas, entradas [8] y [26], p. 111 y… | Tratamiento tipografico distinto para dos fuentes igualmente no publicadas en… | 30 min |
| H-326 | referencias | baja | «Referencias bibliográficas», entradas [22] y [23], p… | Campos opcionales desparejos entre entradas hermanas: DOI ausente en [22] y s… | 15 min |

#### Anexos A-B — 2 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-049 | aparato formal | media | Anexo B, Figura B.6, p. 126 (PDF p.142) | La leyenda de la Figura B.6 (modulo M0) no traduce el color a estado de calid… | 15 min |
| H-050 | aparato formal | media | Anexo B, Figura B.11, p. 129 (PDF p.145) | La matriz k_e de la Figura B.11 (modulo M5) esta al limite de la legibilidad… | 30 min |

#### Anexos C-D — 4 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-054 | aparato formal | media | Anexo C, §§C.1-C.4, pp. 133-136 (PDF pp. 149-152) | Los listados del Anexo C no remiten con \autoref a la ecuación concreta del C… | 15 min |
| H-220 | tipografía | media | Anexo C.4, p. 136 (PDF p. 152): la página trae solo la… | Páginas con la mitad o más en blanco por colocación de flotantes en los Anexo… | 1 h |
| H-262 | aparato formal | baja | D.1, p. 137 (PDF p. 153) | La etiqueta sec:vyv-reproducibilidad (D.1) no se referencia con \autoref desd… | 5 min |
| H-289 | claridad | baja | D.1, p. 137 (PDF p. 153) | Frase que se autocorrige sobre dónde quedan las figuras del guion de V&V | 5 min |

#### Anexos E-F — 2 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-055 | aparato formal | media | Anexo F, Tabla F.1 p. 159 (PDF p. 175) y Tabla F.2 p. 161… | El campo element_id de surface_loads (JSON) no tiene columna equivalente en e… | 15 min |
| H-137 | consistencia | media | Anexo E, p. 149 (PDF p. 165) | σx de SAP2000 en los puntos A y C no coincide entre la Tabla 3.2 (Cap. 3) y l… | 15 min |

#### Anexo G — 1 hallazgos

| ID | Eje | Sev. | Ubicación | Defecto | Esf. |
|---|---|---|---|---|---|
| H-091 | calibración | media | Encabezado del Anexo G, p. 164 (PDF p.180) | «Ejemplo canónico de validación» contradice al Capítulo 2, que dice que ese e… | 5 min |

---

## 9. Riesgo de defensa

Un agente simuló el tribunal —un estructuralista con experiencia en SAP2000 pero sin formación
formal en elementos finitos, un docente de metodología y el director de carrera— y produjo las
preguntas que harían. Cada una se buscó en el documento.

| Estado | Preguntas | Qué significa |
|---|---|---|
| **RESPONDIDA** | 10 | El documento la responde y se sabe en qué página y con qué frase. |
| **PARCIAL** | 20 | La responde a medias: falta un dato, una cifra o una atribución. |
| **SIN RESPUESTA** | 8 | El documento no la responde. Seis se arreglan escribiendo; dos se contestan de viva voz. |

Las ocho sin respuesta son, en orden de riesgo: dónde está el cálculo manual que la cláusula (b)
promete; cómo se apoyó y se cargó la viga de Timoshenko; bajo qué licencia se publica el software
y de quién son los derechos; qué discretización tiene el modelo de SAP2000; por qué esos
umbrales y no otros; dónde se desarrolla la etapa 6 del procedimiento; por qué el universo de
contenido excluye el único ítem que el software no cubre; y qué dato se tomó en la Carrera para
afirmar que allí existe el problema.

| ID | Riesgo | Estado | Pregunta | Perfil |
|---|---|---|---|---|
| **PD-01** | alto | PARCIAL | Usted repite —en el resumen, en la hipótesis y en las conclusiones— que la memoria de cálculo «… | estructuralis… |
| **PD-02** | alto | PARCIAL | Usted sitúa el problema «en la Carrera de Ingeniería Civil de la Universidad Autónoma Tomás Frí… | director de c… |
| **PD-05** | alto | PARCIAL | Los umbrales del 3 %, del 1 % y del 1,5 % dicen «tolerancia de ingeniería fijada por el autor».… | metodologo |
| **PD-06** | alto | PARCIAL | Los seis criterios de trazabilidad dan el cien por ciento, sin una sola excepción. Quien defini… | metodologo |
| **PD-07** | alto | PARCIAL | El resumen dice «los dieciocho contenidos que un consenso publicado de expertos exige». ¿El con… | metodologo |
| **PD-09** | alto | PARCIAL | El título dice «software educativo». ¿Cómo sostiene ese adjetivo si no midió a ningún estudiant… | director de c… |
| **PD-12** | alto | PARCIAL | Usted ofrece la herramienta para secciones de presas, muros de contención y túneles, que son de… | estructuralis… |
| **PD-14** | alto | PARCIAL | ¿Qué recibe la Carrera con este trabajo? ¿Quién va a usar el programa, y con qué compromiso? | director de c… |
| **PD-15** | alto | PARCIAL | Su hipótesis dice «elevando la trazabilidad y la verificabilidad». ¿Elevándola respecto de qué… | metodologo |
| **PD-16** | alto | PARCIAL | Si el software está hecho para mostrar los pasos, ¿no es obvio que el análisis resulte trazable… | metodologo |
| **PD-10** | alto | RESPONDIDA | Tome la tiza. Saque usted, aquí, un número del Anexo G a partir de los datos del problema. | estructuralis… |
| **PD-03** | alto | SIN RESPUESTA | ¿Cómo impuso los apoyos y la carga de la viga en un continuo bidimensional? ¿Restringió un nodo… | estructuralis… |
| **PD-04** | alto | SIN RESPUESTA | ¿Bajo qué licencia concreta se publica EduFEM, y de quién son los derechos sobre un software de… | director de c… |
| **PD-08** | alto | SIN RESPUESTA | En la Tabla 3.7 usted acredita como «Instrumento de EduFEM» una extrapolación de Richardson. ¿D… | estructuralis… |
| **PD-11** | alto | SIN RESPUESTA | Usted dice que la memoria entrega «el procedimiento completo, con todas sus magnitudes intermed… | estructuralis… |
| **PD-13** | alto | SIN RESPUESTA | En el Anexo G propone leer las cifras en kN y cm. Eso da un módulo de 225 000 kN/cm², más de do… | estructuralis… |
| **PD-17** | medio | PARCIAL | Ese 0,04 % sale de una única malla de 56 × 8 elementos. ¿Qué habría dado con otra malla? ¿No es… | estructuralis… |
| **PD-18** | medio | PARCIAL | Usted mismo encontró un error en su programa. ¿Cuántos más puede haber? ¿De cuántas pruebas con… | estructuralis… |
| **PD-20** | medio | PARCIAL | Aquí hay un 4,56 %. Ésa es la cifra más alta de toda su validación. ¿Por qué no aparece en el r… | estructuralis… |
| **PD-27** | medio | PARCIAL | Su marco metodológico se apoya en una monografía inédita, sin editorial ni fecha. ¿Le parece un… | metodologo |
| **PD-29** | medio | PARCIAL | ¿Usted validó su software o lo verificó? Porque en el mismo capítulo emplea «validación» en más… | metodologo |
| **PD-32** | medio | PARCIAL | En el Anexo G habla de «apoyos empotrados» en tres nodos, pero los dibuja como articulaciones.… | estructuralis… |
| **PD-33** | medio | PARCIAL | ¿Qué es el «bloqueo por cortante» que su resumen presenta como resultado? Lo leo en la primera… | director de c… |
| **PD-34** | medio | PARCIAL | Dígame su objetivo general en una frase, sin leerlo. | director de c… |
| **PD-21** | medio | RESPONDIDA | ¿Por qué SAP2000 le sirve de referencia, si también es una aproximación numérica y puede equivo… | estructuralis… |
| **PD-22** | medio | RESPONDIDA | La membrana de Cook da 23,96. ¿De dónde sale ese número y quién lo respalda? ¿Es la solución ex… | estructuralis… |
| **PD-23** | medio | RESPONDIDA | ¿Cuál es la población y cuál la muestra de esta investigación? ¿Cuántos casos y por qué ésos? | metodologo |
| **PD-24** | medio | RESPONDIDA | Su hipótesis: ¿qué habría tenido que ocurrir para que quedara refutada? | metodologo |
| **PD-25** | medio | RESPONDIDA | ¿Qué aporta esto que no aporten ED-Elas2D, que existe desde 1998, o el propio SAP2000? | director de c… |
| **PD-26** | medio | RESPONDIDA | Esos dieciocho contenidos los definieron expertos mexicanos de ingeniería mecánica. ¿Por qué va… | metodologo |
| **PD-31** | medio | RESPONDIDA | El Anexo E, que sostiene la comparación con SAP2000, entra con erratas —«SAP200», «poison», «De… | estructuralis… |
| **PD-19** | medio | SIN RESPUESTA | Su flecha calculada es mayor que la analítica y que la de SAP2000, y su error en desplazamiento… | estructuralis… |
| **PD-28** | medio | SIN RESPUESTA | Busqué su referencia 16 en la revista y el artículo empieza en la página 1007. Usted cita la pá… | metodologo |
| **PD-30** | medio | SIN RESPUESTA | Su nomenclatura anuncia preguntas de investigación PI-1 a PI-3. ¿Dónde está la tercera? | metodologo |
| **PD-37** | bajo | PARCIAL | Cuando instalé el programa, Windows me advirtió que había protegido mi PC. ¿Es seguro? | director de c… |
| **PD-38** | bajo | PARCIAL | ¿Cómo se replica este trabajo si dentro de dos años el programa ya no compila? | metodologo |
| **PD-35** | bajo | RESPONDIDA | ¿Por qué Python y no MATLAB o un lenguaje compilado? ¿No es más lento? | estructuralis… |
| **PD-36** | bajo | RESPONDIDA | ¿Por qué solo Q4 y Q9? ¿Por qué no triángulos, elementos de orden superior o tres dimensiones? | estructuralis… |

> **El plan de corrección trae las 38 preguntas con la respuesta escrita**, apoyada en cifras y
> páginas concretas, lista para estudiar.

---

## 10. Cobertura

| Capítulo | Págs. | Hall. | Estado | Comentario |
|---|---|---|---|---|
| Resumen y preliminares | i-xv | 35 | requiere trabajo | Las cuatro altas caen en la primera página que lee el tribunal —«bloqueo por cortante» y «lienzo» sin glosa,… |
| Introduccion | 1-11 | 44 | requiere trabajo | Es la mayor densidad del documento (4,0 hallazgos por página) y el único capítulo sin ningún eje limpio: cali… |
| Cap. 1 Marco teorico | 12-39 | 27 | requiere trabajo | Densidad baja (≈1 por página) y trazabilidad limpia, pero la accesibilidad se hunde en una franja acotada —§1… |
| §2.1 Diseno metodologico | 40-52 | 44 | requiere trabajo | Trece hallazgos de trazabilidad, los más de todo el documento, y el hilo más caro de la auditoría nace aquí:… |
| §2.2 El software EduFEM | 53-72 | 22 | solido | Una sola alta —la licencia del software, que es MIT en el repositorio y no se nombra en ninguna página de la… |
| Cap. 3 Resultados | 73-101 | 97 | requiere trabajo | Concentra el 27 % de los hallazgos y 22 de los 57 de calibración, casi todos del mismo molde —un universal («… |
| Conclusiones y recomendaciones | 102-110 | 28 | requiere trabajo | Claridad y tipografía quedan limpias, pero el capítulo sube el tono de la evidencia con tres «queda demostrad… |
| Referencias | 111-113 | 7 | solido | Seis de los diez ejes limpios y ninguna alta, porque lo estructural está verificado de forma determinista (or… |
| Anexos A-B | 114-132 | 9 | solido | Sin altas y con seis ejes limpios: solo redundancia con §2.2 en cuatro bloques, dos figuras con leyenda o tam… |
| Anexos C-D | 133-144 | 7 | solido | Densidad mínima (0,6 por página) y cinco ejes limpios —incluida la trazabilidad, porque el auditor cruzó cada… |
| Anexos E-F | 145-163 | 5 | solido | Cinco hallazgos en 19 páginas, todos de severidad media y ninguno verificado, entre ellos el único conflicto… |
| Anexo G | 164-171 | 29 | requiere trabajo | La aritmética está rehecha a mano por el orquestador y cierra íntegra —es la comprobación más importante de l… |

| Eje | Hall. | Máx. sev. | Estado | Comentario |
|---|---|---|---|---|
| calibración | 57 | alta | requiere trabajo | Eje prioritario y el más poblado, con diez altas casi todas del mismo molde —un cuantificador universal («cada res… |
| consistencia | 51 | alta | requiere trabajo | Volumen alto pero mitad cosmético (26 de 51 son de severidad baja), y ninguna de las tres altas es una discrepanci… |
| trazabilidad | 41 | alta | requiere trabajo | Las cinco altas convergen en dos huecos concretos y cerrables —la etapa 6 (fuerzas nodales equivalentes) sin susti… |
| riesgo de defensa | 39 | alta | requiere trabajo | Tres preguntas que el tribunal hará casi con seguridad y que el documento hoy no responde —dónde está el cálculo m… |
| aparato formal | 38 | media | menor | Ninguna alta: los 63 flotantes se citan antes de aparecer, no hay referencias a etiquetas inexistentes, los siete… |
| redundancia | 35 | media | menor | Ninguna alta, y las repeticiones grandes están verificadas como funcionales y deliberadas; el trabajo real son cua… |
| claridad | 30 | alta | menor | La prosa está verificada como excepcionalmente limpia —cero muletillas de relleno, solo dos demostrativos pronomin… |
| accesibilidad | 26 | alta | requiere trabajo | El problema no está repartido sino concentrado en quince páginas (§1.6-§1.13, veinte ecuaciones y ninguna figura n… |
| referencias | 20 | alta | requiere trabajo | El aparato está verificado de forma determinista (orden correlativo, cero huérfanas en ambos sentidos, un solo pat… |
| tipografía | 17 | media | menor | El .log registra 0 overfull, 0 underfull y 0 overfull vbox, y la revisión visual de ~47 páginas renderizadas lo co… |

### Ejes que están limpios

Donde el documento está bien, y el autor no debe tocar nada:

- **Orden y completitud del aparato de citas.** Comprobado de forma determinista.
- **Coherencia numérica entre secciones.** Dos excepciones, ambas menores: H-137 (cuarta
  decimal, Tabla 3.2 frente a las capturas del Anexo E) y H-310 («coincidente» por 0,042 %).
- **Composición de línea y de párrafo.** Cero desbordes.
- **Corrección de la aritmética publicada.** El Anexo G cierra entero.
- **Disciplina sobre los efectos en el estudiante.** No hay ninguno atribuido a EduFEM, y §1.2
  los niega por escrito. El único cabo suelto es H-007, en la Justificación.
- **Estructura del documento y portada** frente a la norma de la Carrera.
- **Leyendas de figuras y tablas**, salvo dos del Anexo G.

---

## 11. Lo que se descartó, y por qué

Se retiran del informe. Se listan porque saber qué se examinó y se desestimó es parte del
diagnóstico, y porque impide que vuelvan a plantearse.

**Descartados por los verificadores independientes (5)**

| Hallazgo | Razón del descarte |
|---|---|
| «La premisa «la caja negra impide comprobar» es más fuerte que la práctica de la tesis» | La cita estaba leída fuera de su frase: el adverbial «paso a paso» rige la negación. |
| «La Justificación generaliza sin cita lo que §1.2 acota» | La evidencia estaba truncada justo donde el texto se salva: «…con las salvedades que examina la §1.2». |
| ««Referencias de exactitud conocida» incluye la membrana de Cook, que §3.5 declara no exacta» | La cita estaba cortada donde el documento resuelve la objeción. |
| Dos más, de menor entidad | Evidencia no localizable en el documento. |

**Retirados por el crítico de completitud (3)**

| Hallazgo | Razón |
|---|---|
| «La Nomenclatura no es alfabética» | El documento lo declara y lo justifica en la p. xi: los símbolos se agrupan por tema y, dentro del tema, por orden de aparición. Ninguna norma declarada dice nada sobre esto. |
| «La A de ensamblaje debería componerse de otro modo» | Es el operador estándar de la literatura del MEF, y el preámbulo lo declara así. La corrección alejaría la notación de la convención. |
| «κ₂ listada y no usada» (duplicado) | El defecto es real, pero estaba contado dos veces. Se conserva una sola vez. |

**Degradados por sobrecorrección (13).** Trece hallazgos bajaron de severidad en la
consolidación. Los motivos se repiten: la frase ya venía acotada en su contexto inmediato; la
acción propuesta era la más cara del informe con el menor rendimiento (ilustrar el capítulo 1
entero); o se reprochaba una decisión de composición que ninguna norma declarada prohíbe.

**Dos precisiones sobre hallazgos que sí se conservan**

- **H-308** («la tasa 1,01 sugiere errata») se conserva **solo en su mitad menor**. Rehecha la
  cuenta: log₂(3,578 × 10⁻¹ / 1,783 × 10⁻¹) = 1,0048, pero los errores se publican con cuatro
  cifras significativas, lo que deja al logaritmo un margen de ±4 × 10⁻⁴ que cruza el 1,005 donde
  cambia el redondeo. Con los valores sin redondear, 1,01 es compatible. Lo que queda es añadir a
  la leyenda que las tasas se calculan con los valores sin redondear.
- **H-259** se conserva, pero su evidencia trae un recuento mal hecho («diez páginas de material
  preliminar» son nueve). Y su hallazgo hermano **H-051** —el índice general omite las quince
  secciones sin numerar de la Introducción y de las Conclusiones, entre ellas *Objetivos* e
  *Hipótesis*— está calificado «media» y merece leerse como alta: es lo primero que un tribunal
  busca en un índice.

---

## 12. Huecos de esta auditoría

Lo que no se miró lo suficiente, y que conviene que el autor revise por su cuenta.

1. **Las cifras del capítulo 3 no se cotejaron contra la salida de los guiones.** Esta auditoría
   rehízo a mano el Anexo G, que es lo que sostiene el argumento central, pero nadie reejecutó
   `tests/vv_mms.py`, `vv_timoshenko.py` ni `vv_cook.py` para verificar que las Tablas 3.1 a 3.4
   y D.1 a D.6 reproducen los CSV que dicen reproducir. **Es la única comprobación de fondo que
   queda pendiente, y está al alcance del autor en una tarde.**
2. **Los Anexos C, D, E y F recibieron poca atención relativa**: 31 páginas impresas y 20
   menciones, frente a las 136 del capítulo 3. Se revisaron y no apareció nada de fondo, pero la
   comprobación fila a fila de las Tablas D.1–D.6 y F.1–F.3 contra el software no se hizo.
3. **Cinco leyendas del Anexo G quedaron fuera del censo** porque están hechas con `\captionof` y
   no con `\caption`: «Nodos.», «Elementos (conectividad y espesor).», «Parámetros globales del
   análisis.», «Tensiones en los puntos de Gauss (E3).» y «Tensiones extrapoladas a los nodos
   (E3).». Las cinco están por debajo de las quince palabras y se ven en el Índice de tablas.
4. **`referencias.bib` tiene 29 entradas y solo se citan 26.** `rutten2012learning`,
   `chi2014icap` y `atkinson2000learning` quedaron sin usar al pasar la tesis al eje tecnológico.
   No es un defecto del PDF —biblatex no las imprime— pero conviene saberlo antes de tocar §1.2.
5. **No se leyeron los documentos de los Talleres 2, 3, 4 y 6** de la Carrera. Se leyeron el 1 y
   el 5, de donde salieron dos hallazgos y la confirmación de que la estructura cumple.

---

## 13. Qué cambió el control final

Antes de entregar, diez revisores que no habían participado en la auditoría reexaminaron los
hallazgos de severidad alta, las afirmaciones deterministas de este informe y la coherencia
interna de los dos documentos. Emitieron 44 veredictos: **23 confirmaron, 18 matizaron y 3
tumbaron**. Se deja constancia de lo que cambiaron, porque una auditoría que no publica sus
propias correcciones no merece crédito.

### Hallazgos que bajaron de severidad o se retiraron

| | Antes | Ahora | Por qué |
|---|---|---|---|
| **H-005** | alta | **baja** | El hallazgo confundía τxy con una tensión normal —la Nomenclatura las distingue— y afirmaba que el cuerpo omitía el subíndice σx, cuando solo lo omite el Resumen. Queda como sugerencia editorial. |
| **H-025** | alta | **retirado** | Identificador huérfano: había quedado fusionado en H-022 y este informe lo seguía citando sin ficha propia. Defecto del informe, no de la tesis. |
| **H-023** | alta | **media** | El criterio que la tesis aplica y reporta es la reproducibilidad por construcción, no una recomputación ejecutada. Es una inconsistencia terminológica entre tres formulaciones y el criterio, no una promesa de evidencia incumplida. |
| **H-003** | alta | **media** | El universal de §3.8 está escrito sobre el software completo, donde sí se cumple; lo que falta es declarar los umbrales con que la memoria en PDF degrada su desarrollo. Omisión documental, no afirmación falsa. |
| **H-020** | alta | **media** | No hay contradicción interna: hay un dato faltante —la licencia nunca se nombra— y una nota desactualizada respecto del repositorio. |
| **H-006** | alta | **media** | La elipsis se limita al Resumen; §2.1.4 y la nota de la Tabla 3.7 declaran el filtro de forma auditable, y las Conclusiones ya escriben el matiz correcto. |
| **H-009** | alta | **media** | Se retira la objeción «procedencia frente a autoría»: declarar que el umbral lo fijó el autor **sí** es una procedencia, y más transparente que inventarle una fuente. Queda solo que los tres valores no se justifican. |
| **H-016** | alta | **baja** | Una sola elipsis en la p. 104. El Resumen, §3.7.1, la Tabla 2.4 y los Aportes respetan la salvedad de la Tabla 3.2: no hay contradicción de fondo. |
| **H-017** | alta | alta | El defecto se confirma entero. Lo que no se sostenía era la acción: una nota genérica no resuelve la contradicción, porque la lista seguiría mostrando 1007-1027 junto a un «p. 2». |

### Correcciones a las afirmaciones de este informe

- **La aritmética del Anexo G se volvió a rehacer**, por un revisor independiente y con los seis
  bloques por separado. **Confirmada entera**, incluida la matriz de extrapolación como inversa
  exacta de **M**.
- **El orden de las citas, las siete ecuaciones sin referenciar y la única contaminación APA**:
  confirmados.
- **Los localizadores fuera de rango**: confirmado que los seis son de [16] Bishay y que los de
  [3] Pérez-Santiago caen todos dentro. Se retira la cifra «134 localizadores»: depende de si un
  rango «pp. 4-5» cuenta como uno o como dos, y el informe no declaraba la convención.
- **Las unidades del Anexo G**: la aritmética del informe es correcta, pero el Anexo declara en
  la misma frase que el sistema es «coherente y arbitrario», y kN-cm **es** coherente. No es un
  error de unidades: es un ejemplo físicamente inverosímil y ajeno al sistema técnico que usa el
  resto de la tesis. El arreglo sigue siendo el mismo y sigue costando un minuto.
- **Los márgenes del Anexo E**: confirmados 0,46 cm y 0,76 cm. Precisión: los 2,54 cm son el
  margen del **cuerpo de la tesis**; las hojas apaisadas siguientes, con `scale=0.88`, quedan en
  1,5-1,75 cm.
- **H-137**: confirmado sobre las páginas renderizadas, con los tres valores.

### Defectos de este informe que el control encontró

1. **H-025 citado sin ficha** (corregido: retirado).
2. **La atribución de los hallazgos altos absorbidos** era errónea (corregido: son H-001, H-013 y
   H-015, no PAT-11 ni PAT-12).
3. **Las listas «Absorbe:» de los patrones** nombran 143 identificadores, de los cuales 21 son
   registros fusionados que ya no viven como hallazgo. Los hallazgos vivos absorbidos son 122.
4. **«Sin discrepancias» en la fila 5 del apartado 4** chocaba con H-310 (corregido: dos
   excepciones).
5. **El apartado 4 blindaba el pasaje de Cook** sin advertir que contiene H-310 y H-277
   (corregido).
6. **La suma de esfuerzos del plan** no cuadraba con el rango declarado (corregido).

---

## 14. Estado de aplicación

**La auditoría completa está implementada desde el 23 de septiembre de 2026 en una versión nueva,
final1** (`tesis/main_final1.tex` y `tesis/capitulos_final1/`, 194 páginas). `capitulos_final/`
volvió a ser exactamente el texto auditado, para poder comparar. La disposición de cada hallazgo
—aplicado, adaptado, cubierto, decidido por el autor o diferido, con su razón— está en
`IMPLEMENTACION-FINAL1.md`.

El autor revisó los cinco problemas de mayor impacto el 22 de septiembre de 2026 y decidió lo
siguiente. **Los problemas 4 y 5 se corrigieron ese día** con quince ediciones sobre seis
archivos, verificadas una a una sobre el PDF recompilado; el 23 de septiembre pasaron a final1
junto con el resto de la auditoría. El detalle, edición por edición, está en
`PLAN-CORRECCION-FINAL.md`, apartado «Estado de aplicación».

Sobre los otros tres:

- **Problema 1 (el cotejo manual).** El autor **tiene** el cálculo manual del ejemplo canónico y
  además verificó ese modelo contra otros programas al desarrollar el solucionador inicial. Nada
  de eso está escrito. Eso **mejora** la situación respecto de lo que este informe suponía: el
  contraste contra otro programa es un patrón independiente, que es justo lo que le faltaba al
  argumento. La recomendación pasa de «alinear las tres frases con el criterio» a «documentar la
  evidencia que ya existe».
- **Problema 2 (el modelo de SAP2000).** El autor lo conserva y lo describirá en la defensa si se
  lo piden. Decisión: no se escribe. Riesgo residual registrado.
- **Problema 3 (los criterios de cobertura).** El autor lo cubrirá oralmente. Decisión: sin
  cambios. H-022, H-004 y H-012 quedan abiertos para la defensa.

Los hallazgos corregidos **no se retiran de este informe**: se conservan con su evidencia, para
que quede el registro de qué se cambió y por qué.

## Anexo de datos

Los datos completos de la auditoría, por si el autor quiere consultar la evidencia literal o la
acción íntegra de un hallazgo concreto:

| Archivo | Contenido |
|---|---|
| `HALLAZGOS_TODOS.json` | Los 354 hallazgos con evidencia, diagnóstico, acción, veredicto del verificador y razón. Campo `n` = el número de `H-nnn`. |
| `SINTESIS.json` | Patrones, fusiones, degradaciones, orden de trabajo, cobertura, preguntas de defensa y crítico de completitud. |
| `VERIFICADO_POR_EL_ORQUESTADOR.md` | Las once comprobaciones deterministas, con sus cuentas. |
| `LO_QUE_ESTA_BIEN.md` | Las 289 observaciones de los lectores sobre lo que **no** hay que tocar. |
| `DESCARTADOS.md` | Los hallazgos tumbados por los verificadores, con la razón. |
