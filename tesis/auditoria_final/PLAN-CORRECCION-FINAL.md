# Plan de corrección — Tesis EduFEM

*Documento de trabajo. Pensado para tenerlo abierto al lado de la tesis.*
*Acompaña a `AUDITORIA-REDACCION-FINAL.md`, donde está el diagnóstico y la evidencia de cada
hallazgo. Los identificadores `H-nnn` y `PAT-nn` son los mismos en los dos documentos.*


## Índice

- [Diagnóstico ejecutivo](#diagnóstico-ejecutivo)
  - [Los cinco problemas de mayor impacto](#los-cinco-problemas-de-mayor-impacto)
  - [Esfuerzo](#esfuerzo)
- [Cómo usar este plan](#cómo-usar-este-plan)
  - [Dos comprobaciones que conviene hacer antes de tocar nada](#dos-comprobaciones-que-conviene-hacer-antes-de-tocar-nada)
- [Estado de aplicación](#estado-de-aplicación)
  - [Ya aplicado al documento](#ya-aplicado-al-documento)
  - [Decisiones del autor sobre los tres problemas restantes](#decisiones-del-autor-sobre-los-tres-problemas-restantes)
  - [Lo que sigue pendiente y es barato](#lo-que-sigue-pendiente-y-es-barato)
- [Los trece patrones](#los-trece-patrones)
- [Los bloques de corrección](#los-bloques-de-corrección)
  - [B1 — Calibrar el eje Resumen → §3.8 → Conclusiones](#b1-calibrar-el-eje-resumen-38-conclusiones)
  - [B2 — Cerrar las dos brechas de evidencia](#b2-cerrar-las-dos-brechas-de-evidencia)
  - [B3 — Hacer reproducible el caso de validación central](#b3-hacer-reproducible-el-caso-de-validación-central)
  - [B4 — Una palabra, un sentido](#b4-una-palabra-un-sentido)
  - [B5 — Trazabilidad fina de la matriz de consistencia y de los veredictos](#b5-trazabilidad-fina-de-la-matriz-de-consistencia-y-de-los-veredictos)
  - [B6 — Aparato de citas](#b6-aparato-de-citas)
  - [B7 — Legibilidad de las páginas que el tribunal lee de verdad](#b7-legibilidad-de-las-páginas-que-el-tribunal-lee-de-verdad)
  - [B8 — Glosas en la primera aparición](#b8-glosas-en-la-primera-aparición)
  - [B9 — Redundancia: dejar la aparición canónica](#b9-redundancia-dejar-la-aparición-canónica)
  - [B10 — Anexo G](#b10-anexo-g)
  - [B11 — Uniformidad de cifras, símbolos y nomenclatura](#b11-uniformidad-de-cifras-símbolos-y-nomenclatura)
  - [B12 — Cosmética agrupada](#b12-cosmética-agrupada)
  - [B13 — Reserva: correcciones que no encajan en ningún bloque anterior](#b13-reserva-correcciones-que-no-encajan-en-ningún-bloque-anterior)
- [Calibración de afirmaciones](#calibración-de-afirmaciones)
  - [Tabla de frases a calibrar](#tabla-de-frases-a-calibrar)
- [Preguntas de defensa](#preguntas-de-defensa)
  - [Riesgo alto](#riesgo-alto)
  - [Riesgo medio](#riesgo-medio)
  - [Riesgo bajo](#riesgo-bajo)
- [Sobrecorrecciones: lo que NO hay que tocar](#sobrecorrecciones-lo-que-no-hay-que-tocar)
- [Lista de comprobación final](#lista-de-comprobación-final)

---

## Diagnóstico ejecutivo

**El documento está en condiciones de defenderse.** Lo comprobable de forma determinista está
sólido: la aritmética del Anexo G se rehizo a mano y cierra en catorce magnitudes; las citas
[1]–[26] van en orden correlativo perfecto, sin huérfanas en ningún sentido; las cifras del texto
son coherentes de punta a punta; la composición no tiene un solo desborde. No hay ningún hallazgo
de severidad crítica. Lo que sigue es una pasada de calibración y de disciplina léxica, no una
reescritura.

### Los cinco problemas de mayor impacto

**1 · Tres formulaciones anuncian un cotejo manual ejecutado; el criterio que se aplica mide otra
cosa.** *(1 h — bloque B2)*
La tesis declara la reproducción manual de la memoria como indicador de la variable dependiente
(Tabla 2.2), como una de las cuatro familias de evaluación (§2.1.1) y como condición de
refutación de la hipótesis (p. 7). Pero el criterio que realmente se aplica —Tabla 2.4— y el que
se reporta —§3.8— miden otra cosa: que cada etapa esté desarrollada y remitida a su ecuación. Un
tribunal que pregunte *dónde está el cálculo manual* encontrará esa discordancia.
**La salida no es ejecutar el cotejo**, sino alinear las tres formulaciones con el criterio. Un
cotejo del autor contra su propio motor no sería un patrón independiente, y chocaría con la
advertencia del propio Anexo G de que todo lo que publica es salida del motor.

**2 · El caso de validación central no se puede rehacer con lo que el documento escribe.**
*(2 h — bloque B3)*
§3.4 es la única validación contra referencias externas, y no dice cómo se apoyó una viga
simplemente apoyada en un continuo bidimensional, ni cómo se aplicó la carga, ni qué malla ni qué
versión tiene el modelo de SAP2000. Es lo primero que mira el examinador estructuralista, que es
justamente el único que conoce SAP2000 de primera mano.

**3 · Los criterios de cobertura se declaran cumplidos contra evidencia que no los cubre del
todo.** *(3 h — bloque B2)*
«9 de 9» y «18 de 18» son los dos números que el Resumen y las Conclusiones repiten, y los dos
tienen un punto flojo verificable. La etapa 6 —fuerzas nodales equivalentes— no se desarrolla en
el Anexo G porque el ejemplo canónico lleva una sola carga nodal. Y del universo de contenido se
apartó FEM3 por ser «un desarrollo teórico que el software no expone», de modo que un ítem del
18 de 18 es verdadero por construcción. A ello se suma que la fila FEA30 acredita como
«instrumento de EduFEM» una extrapolación de Richardson **que no está en el código**.

**4 · «Validación» y «error» usados fuera de la acepción que el propio documento fija.**
*(1,5 h — bloque B4)*
§1.13 declara una acepción única y el texto la rompe en una decena de sitios, incluido el quinto
objetivo específico. Peor: las Conclusiones llaman «errores» a las diferencias frente a SAP2000,
que es exactamente lo que la nota de la Tabla 3.2 se cuidó de negar y lo que los Aportes escriben
bien dos páginas después.

**5 · La puerta del documento entra sin glosas y con alguna elipsis.**
*(2 h — bloques B1 y B8)*
El Resumen es la única página que todo el tribunal lee entera, y en ella entran sin glosa
«lienzo», «bloqueo por cortante» y «soluciones manufacturadas». Además, «los dieciocho
contenidos que un consenso exige» son dieciocho de cuarenta y nueve —el cuerpo lo declara de
forma auditable, el Resumen lo abrevia—, falta el subíndice de σx que el cuerpo sí escribe, y la
memoria se presenta reproducible a mano sin acotarla al ejemplo canónico. Son arreglos de una
cláusula cada uno. A esto se suma que el software se llama «libre» seis veces sin nombrar nunca
la licencia, y que la nota de la Tabla 2.5 la deja en futuro —el repositorio ya distribuye MIT,
dato comprobado en el **repositorio**, no en la tesis—.

### Esfuerzo

| | |
|---|---|
| **Total** | **31,5 a 32,5 h** de bloques, en cuatro o cinco jornadas, más dos horas de recompilación y relectura final: **33,5 a 34,5 h** |
| **B1 + B2 + B3** | **9 h** — es lo que cambia la defensa |
| **+ B4 + B5** | +4,5 h — cierra todo lo que un tribunal puede señalar como defecto de método |
| **B6 a B13** | 18 a 19 h — calidad de edición: mejora el documento, no lo salva ni lo hunde |

**Si el tiempo es escaso:** B1, B2, B3, B4, más los dos arreglos de cinco minutos que rinden
desproporcionadamente —la PI-3 inexistente de la Nomenclatura (H-014) y el sistema de unidades
del Anexo G (H-207)—. El resto puede esperar.

---

## Cómo usar este plan

Estos cinco frentes son los cuatro que el informe agrupa en su veredicto, con el de cobertura
desdoblado en dos por separarse el trabajo.

Los bloques están en el orden en que conviene hacerlos, y ese orden **no es por severidad**: es
por dependencia y por economía de pasadas.

- **Primero lo que arrastra.** Calibrar una frase del Resumen obliga a tocar su gemela en §3.8 y
  en las Conclusiones. Hacerlo de una vez evita volver tres veces sobre el mismo párrafo.
- **Después lo que exige producir algo nuevo** (B2 y B3), porque de su resultado dependen frases
  que B1 dejó a medio calibrar.
- **Luego lo estructural**, capítulo por capítulo.
- **Al final lo cosmético**, todo junto, en una sola sesión con el PDF recompilado al lado.

**Dentro de cada bloque**, los hallazgos en **negrita** son de severidad alta. La flecha `→` da
la acción concreta; cuando la reformulación no es obvia, trae el texto listo para pegar.

**Ojo con las entradas `PAT-nn`**: 117 de los 299 hallazgos se atienden en bloque dentro de un
patrón y no aparecen listados por su identificador. Es deliberado —corregir un patrón de una
pasada cuesta mucho menos que atacar sus apariciones una a una—, pero significa que el reparto
no es verificable hallazgo por hallazgo en esas entradas.

**Al imprimir**: las tablas de 5 y 6 columnas del informe y la tabla de frases a calibrar de este
plan llevan celdas largas. En A4 vertical se estrechan hasta ser ilegibles; conviene imprimirlas
en apaisado, o consultarlas en pantalla y llevar al papel solo las fichas.

**Antes de empezar, lee la lista de sobrecorrecciones** (al final de este documento). Un autor
que recibe una auditoría tiende a corregir de más, y hay pasajes que son buenos exactamente como
están.

### Dos comprobaciones que conviene hacer antes de tocar nada

1. **Reejecutar los guiones de verificación y validación** (`tests/vv_mms.py`,
   `vv_timoshenko.py`, `vv_cook.py`) y cotejar su salida contra las Tablas 3.1 a 3.4 y D.1 a D.6.
   Es la única comprobación de fondo que esta auditoría no hizo, y está al alcance en una tarde.
2. **Fijar la decisión sobre la licencia** (H-020). El repositorio lleva MIT; la nota de la Tabla
   2.5 dice que la licencia «debe elegirse»; y el propio documento advierte que PyMuPDF es
   AGPL-3.0, que es recíproca. Los dos primeros son un problema de redacción y se arreglan aquí.
   El tercero merece consultarse con el tutor antes de escribir nada: **esta auditoría señala la
   discrepancia, no emite un juicio legal.**

---

## Estado de aplicación

*Actualizado el 23 de septiembre de 2026.*

> **Este plan ya está aplicado entero, en la versión final1** (`tesis/main_final1.tex` y
> `tesis/capitulos_final1/`, 194 páginas, sin errores ni desbordes). `capitulos_final/` volvió a
> ser exactamente el texto auditado, para poder comparar. Qué se hizo con cada hallazgo —y por qué,
> cuando no se siguió la ficha al pie de la letra— está en `IMPLEMENTACION-FINAL1.md`, que empieza
> por lo que queda en manos del autor. Lo que sigue en este apartado es el estado del 22 de
> septiembre, anterior a esa implementación.

### Ya aplicado al documento

Quince ediciones sobre seis archivos, hechas el 22 de septiembre en `capitulos_final/` y
trasladadas el 23 a `capitulos_final1/`. **El documento recompilaba limpio: 187 páginas, cero
errores, cero desbordes**, y las quince se verificaron una a una sobre el PDF resultante.

**Problema 4 — «validación» y «error» dentro de la acepción declarada** *(ocho ediciones)*

| Dónde | Qué se hizo |
|---|---|
| §1.13 (`02_marco_teorico.tex`) | Se añadió la excepción explícita para el quinto objetivo: «Queda fuera de esta acepción, por último, el enunciado del quinto objetivo específico, «validar la propuesta»: allí el verbo se emplea en su sentido metodológico corriente —comprobar que la solución construida satisface los criterios fijados de antemano—, y no en el de contraste con una referencia externa de exactitud conocida.» |
| §1.13, cierre del capítulo | «los mismos criterios de verificación» → «de verificación **y validación**» |
| §3.1, título | «Medición de los datos y **validación** de la medición» → «y **confiabilidad** de la medición» |
| §3.4, veredicto (p. 83) | «error de σx inferior al 1 % frente a la solución analítica y frente a SAP2000… Observado: 0,0414 % y 0,2066 %» → «error … y **diferencia** inferior al 1 % frente a SAP2000… Observado: 0,0414 % **de error** y 0,2066 % **de diferencia**» |
| §3.7.4 (p. 99) | «la validación se apoya en tres casos» → «la **verificación y la validación se apoyan** en tres casos» |
| §3.8 (p. 100) | Se desalojó a SAP2000 del papel de patrón: ahora las referencias externas son tres clases, «a ellas se suma el modelo de SAP2000, que no actúa como patrón de exactitud —ninguna de las dos formulaciones lo es de la otra, según advierte la nota de la Tabla 3.2— sino como segunda aproximación numérica con la que comparar» |
| Conclusiones, OE4 (p. 104) | Se cerró la elipsis: «; **la diferencia frente al modelo de SAP2000 fue** de hasta el 0,21 % en σx» |
| Anexo B, §B.2 (p. 119) | «que antes **valida** el modelo con un comprobador de salud» → «que antes **revisa** el modelo…» |

**Problema 5 — la puerta del documento** *(siete ediciones)*

| Dónde | Qué se hizo |
|---|---|
| Resumen | Glosa de **lienzo**: «sobre un mismo lienzo —el área gráfica donde se dibuja el modelo—» |
| Resumen | Glosa de **soluciones manufacturadas**: «—campos exactos construidos a propósito para medir el error del programa—» |
| Resumen | Glosa de **bloqueo por cortante**: «—la rigidez excesiva que ese elemento exhibe bajo flexión—» |
| Resumen | «los dieciocho contenidos que un consenso publicado de expertos exige **dentro del alcance de este trabajo**» |
| Resumen | Subíndice de σx en sus dos apariciones: «0,04 % en la tensión normal **σx**» y «0,21 % en **σx**» |
| Resumen | «una memoria de cálculo automática **cuyo desarrollo** puede **rehacerse** a mano» |
| Tabla 1.1, §2.2.2 y Anexo A | Se nombra la licencia: fila «Licencia» → «Libre **(MIT)**, código abierto»; requisito 5 → «su código fuente disponible —el de EduFEM se publica bajo licencia **MIT**—»; y la nota de la Tabla 2.5 deja de dejarla en futuro |

> **Un punto que el autor debe cerrar por su cuenta.** La nota de la Tabla 2.5 dice ahora: «El
> código propio de EduFEM se publica bajo licencia MIT; la redistribución del paquete binario,
> que incorpora `PyMuPDF`, queda además sujeta a los términos de la AGPL-3.0 de esa biblioteca.»
> Es un enunciado **factual**, y deliberadamente no resuelve si esa combinación es la que el
> autor quiere. **Esta auditoría no emite un juicio legal**: conviene consultarlo con el tutor, y
> valorar si sustituir `PyMuPDF` por una alternativa permisiva simplifica el asunto.

### Decisiones del autor sobre los tres problemas restantes

**Problema 1 — el cotejo manual. La situación es mejor de lo que el informe suponía.**
El autor tiene el cálculo manual del ejemplo canónico, y además verificó ese modelo **contra
otros programas** cuando desarrollaba el solucionador inicial. Nada de eso está escrito.

Eso cambia la recomendación. El informe daba por supuesto que no existía evidencia y proponía
alinear las tres formulaciones con el criterio (opción conservadora). **Existiendo la evidencia,
hay una salida mejor**, porque el contraste contra otro programa **sí es un patrón
independiente**, que es justo lo que le faltaba al argumento:

1. Documentar el cotejo en el Anexo G o en §3.6.1: qué programa o programas, su versión, qué
   magnitudes se compararon y con qué diferencia. Media página.
2. Decir, donde se presenta el ejemplo canónico, que es un modelo construido por el autor para
   verificar el motor en sus primeras versiones —no un caso tomado de la literatura—, y que se
   contrastó contra otro programa. El Anexo B ya lo llama «el primer caso de prueba del
   proyecto», así que la frase encaja sin forzar nada.
3. Hecho eso, las tres formulaciones (§2.1.1, Tabla 2.2 y la cláusula de refutación de la p. 7)
   dejan de discordar con el criterio, porque el acto de comprobación **existió** y está
   reportado.

Si el autor prefiere no documentarlo, sigue en pie la opción conservadora que describe H-023:
alinear las tres frases con el criterio de la Tabla 2.4.

**Problema 2 — el modelo de SAP2000.** El autor conserva el modelo, lo llevará a la defensa si se
lo piden y puede describir cómo lo analizó. **Decisión: no se escribe en el documento.** Queda
constancia del riesgo residual: la pregunta se responderá de viva voz, no desde el texto, y el
examinador que más sabe del asunto es precisamente el que la hará. Cinco o seis renglones en
§3.4 la desactivarían del todo; la decisión es del autor.

**Problema 3 — los criterios de cobertura.** El autor lo cubrirá y no ve necesario cambiar el
documento por ahora. **Decisión: sin cambios.** Siguen abiertos, para la defensa oral, H-022 (la
etapa 6 no se desarrolla en el Anexo G), H-004 (FEM3 se apartó del universo por no estar expuesto
por el software) y H-012 (la fila FEA30 acredita como instrumento una extrapolación de Richardson
que no está en el código).

### Lo que sigue pendiente y es barato

Ninguno de estos entraba en los cinco problemas de mayor impacto, pero tres de ellos son de
severidad alta y dos se arreglan en cinco minutos:

| | Qué | Coste |
|---|---|---|
| **H-014** | La Nomenclatura anuncia «PI-1 a PI-3» y el documento solo tiene dos preguntas. Una celda. | 5 min |
| **H-207** | El Anexo G sugiere «kN y cm»: con E = 225 000 eso da 2250 GPa. Con kgf y cm son 22,1 GPa, un hormigón coherente con el de §3.4. Una palabra. | 5 min |
| **H-017** | Los seis localizadores de [16] Bishay citan pp. 2-17 de un artículo paginado 1007-1027. | 30 min |
| **H-024** | La conclusión del OE3 no recoge el intercambio de datos que el propio objetivo promete. | 15 min |
| **H-137** | Dos valores de SAP2000 difieren en la cuarta decimal entre la Tabla 3.2 y las capturas del Anexo E. | 15 min |
| **H-310** | §3.5 llama «coincidente» con el 0,05 % una distancia que vale 0,042 %. | 5 min |

---

---

## Los trece patrones

Cada uno es un defecto con más de tres apariciones. **Entre los trece absorben 122 de los 299 hallazgos vivos**: corregirlos de una pasada, con el buscador abierto, cuesta mucho menos que atacarlos uno a uno desde su bloque. La columna «Bloque» dice dónde cae el grueso de cada uno.

| ID | Patrón | Sev. | Aparic. | Esfuerzo | Bloque |
|---|---|---|---|---|---|
| **PAT-01** | Términos técnicos usados muchas páginas antes de su glosa, o nunca glosados | alta | 16 | 2 h | B8 |
| **PAT-02** | Oraciones por encima del tope de ~60 palabras que el propio autor fijó | media | 96 | 2 h | B7 |
| **PAT-03** | Párrafos de 200 a 390 palabras que encadenan cuatro o cinco asuntos | media | 17 | 1 h | B7 |
| **PAT-04** | Muletillas de apertura y conectores únicos repetidos hasta la saturación | baja | 89 | 1,5 h | B12 |
| **PAT-05** | El impersonal oculta quién decidió, justo donde la decisión es el aporte | media | 11 | 45 min | B7 |
| **PAT-06** | Enumeraciones de cuatro o más elementos que siguen en prosa corrida | media | 27 | 1,5 h | B7 |
| **PAT-07** | Piezas del software reexplicadas desde cero entre el cuerpo y el Anexo B | media | 12 | 1,5 h | B9 |
| **PAT-08** | Marco y método reexpuestos desde cero en el capítulo 3 y en las conclusiones | media | 18 | 2 h | B9 |
| **PAT-09** | «Validación», «validar» y «error» fuera de la acepción que el documento declara | alta | 11 | 1,5 h | aquí |
| **PAT-10** | Símbolos, precisión y formato numérico desparejos, y Nomenclatura incompleta | media | 45 | 2 h | B11 |
| **PAT-11** | Atribuciones concretas sin localizador de página, y tres sin ninguna cita | alta | 15 | 1,5 h | B6 |
| **PAT-12** | El Anexo G, pieza que sostiene el argumento central, se presenta con descuido | alta | 18 | 2,5 h | B10 |
| **PAT-13** | Los índices reproducen leyendas completas y omiten quince secciones | baja | 34 | 1 h | B12 |

La acción completa de cada patrón está en su bloque, que es donde se trabaja; aquí va una línea con lo que hay que hacer y el puntero.

**PAT-01 — Términos técnicos usados muchas páginas antes de su glosa, o nunca glosados** *(accesibilidad, 16 apariciones, 2 h)*
<br>→ Una sola pasada por las primeras apariciones: media línea entre rayas o con «es decir» para lienzo, bloqueo por cortante, soluciones manufacturadas, ejemplo canónico, isoparamétrico, guion, GDL, punto de Gauss, biyectivo, restricciones de… **Acción completa en B8.**

**PAT-02 — Oraciones por encima del tope de ~60 palabras que el propio autor fijó** *(claridad, 96 apariciones, 2 h)*
<br>→ Partir solo las que caen en lo que el tribunal lee con atención: objetivo general, hipótesis y cláusulas, cierre de §3.8, conclusiones por objetivo y los veredictos de §3.4 y §3.5. **Acción completa en B7.**

**PAT-03 — Párrafos de 200 a 390 palabras que encadenan cuatro o cinco asuntos** *(claridad, 17 apariciones, 1 h)*
<br>→ Partir en dos o tres los seis párrafos de más de 240 palabras, uno por asunto, sin reescribir el contenido. **Acción completa en B7.**

**PAT-04 — Muletillas de apertura y conectores únicos repetidos hasta la saturación** *(claridad, 89 apariciones, 1,5 h)*
<br>→ Sustitución con control manual: alternar «de modo que» con «así», «por eso», «con lo cual» o punto y seguido en la mitad de los casos; convertir «Conviene decir qué prueba…» en «Ese resultado prueba… y no prueba…»; eliminar «de… **Acción completa en B12.**

**PAT-05 — El impersonal oculta quién decidió, justo donde la decisión es el aporte** *(claridad, 11 apariciones, 45 min)*
<br>→ Poner al autor como sujeto en las once frases: «el autor fijó», «el autor adoptó», «el autor eligió». **Acción completa en B7.**

**PAT-06 — Enumeraciones de cuatro o más elementos que siguen en prosa corrida** *(aparato formal, 27 apariciones, 1,5 h)*
<br>→ Sacar a lista las de la Introducción y las Conclusiones —unas doce— y dejar en prosa las del capítulo 1 y de los anexos, donde la enumeración es parte de una explicación continua y la lista la rompería. **Acción completa en B7.**

**PAT-07 — Piezas del software reexplicadas desde cero entre el cuerpo y el Anexo B** *(redundancia, 12 apariciones, 1,5 h)*
<br>→ Dejar la aparición canónica del cuerpo y, en las demás, una línea con \autoref. **Acción completa en B9.**

**PAT-08 — Marco y método reexpuestos desde cero en el capítulo 3 y en las conclusiones** *(redundancia, 18 apariciones, 2 h)*
<br>→ Regla única: la primera aparición desarrolla, las siguientes remiten. **Acción completa en B9.**

**PAT-09 — «Validación», «validar» y «error» fuera de la acepción que el documento declara** *(consistencia, 11 apariciones, 1,5 h)*
<br>→ Reservar «validación» para Timoshenko y SAP2000. En los demás sitios: «evaluación», «comprobación», «cotejo» o «contraste de cobertura». Reformular el OE5 y propagarlo a la Tabla 2.1, la Tabla 2.3 y las Conclusiones. En las Conclusiones, «diferencia» donde el patrón es SAP2000.

**PAT-10 — Símbolos, precisión y formato numérico desparejos, y Nomenclatura incompleta** *(consistencia, 45 apariciones, 2 h)*
<br>→ Pasada de uniformización sobre tablas y prosa: un nombre y un símbolo por magnitud, separador de miles siempre o nunca, mismo número de decimales dentro de cada tabla. **Acción completa en B11.**

**PAT-11 — Atribuciones concretas sin localizador de página, y tres sin ninguna cita** *(referencias, 15 apariciones, 1,5 h)*
<br>→ Añadir localizador solo a las citas que sostienen una atribución concreta —son unas doce, y el autor ya tiene los localizadores en el resto del documento—. **Acción completa en B6.**

**PAT-12 — El Anexo G, pieza que sostiene el argumento central, se presenta con descuido** *(aparato formal, 18 apariciones, 2,5 h)*
<br>→ Cambiar el ejemplo de unidades a kgf y cm y decir en una línea que los valores corresponden a un hormigón; poner unidades en los encabezados de las seis tablas; fijar la precisión por magnitud; numerar la tabla de reacciones; regenerar… **Acción completa en B10.**

**PAT-13 — Los índices reproducen leyendas completas y omiten quince secciones** *(aparato formal, 34 apariciones, 1 h)*
<br>→ Poner título breve en el argumento opcional de \caption[…] de las diecinueve figuras y tablas de los anexos, y añadir \addcontentsline para las quince secciones sin numerar y para los dos índices. **Acción completa en B12.**


---

## Los bloques de corrección

### B1 — Calibrar el eje Resumen → §3.8 → Conclusiones

> **Por qué aquí.** Va primero porque arrastra: cada frase que se calibre en el Resumen obliga a tocar su gemela en §3.8 y en las Conclusiones, y al revés. Haciéndolo de una vez se tocan los tres pasajes en la misma sesión y no se vuelve sobre ellos. Además es donde está el mayor rendimiento por hora: son las páginas que todos los miembros del tribunal leen enteras.

**Esfuerzo del bloque: 3 h** · 26 correcciones

- H-087 · *media* · Resumen, p. i (PDF p.2) · 5 min
  **El Resumen presenta la memoria como reproducible a mano sin acotarla al ejemplo canónico**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-087**.

- H-006 · *media* · Resumen, p. i (PDF p.2) · 15 min
  **«los dieciocho contenidos que un consenso de expertos exige» oculta que son 18 de 49**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-006**.

- H-003 · *media* · §3.8, p. 100 (PDF p.116) · 1 h
  **La memoria en PDF degrada su desarrollo por encima de cierto tamano, y el documento no lo declara**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-003**.

- H-011 · *media* · §3.8, p. 100 (PDF p.116) · 15 min
  **El universal «Cada magnitud […] se comprobó contra un patrón independiente» lo refuta la propia tesis**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-011**.

- H-073 · *media* · Conclusiones, tercer párrafo, p. 102 (PDF p.118) · 5 min
  **«Queda demostrado» en Conclusiones, donde la evidencia es cobertura documental y casos numéricos**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-073**.

- H-083 · *media* · Conclusiones, p. 102 (PDF p. 118) · 15 min
  **«Queda demostrado… y que EduFEM las tiene»: el verbo más fuerte del documento para un cotejo propio**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-083**.

- H-082 · *media* · Resumen, p. i (PDF p. 2) y Aportes del trabajo, p. 106 (PDF p. 122) · 15 min
  **El Resumen y las conclusiones dan solo las componentes primarias y omiten el 2,89 % y el 4,56 %**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-082**.

- H-102 · *media* · Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) — instancia única · 15 min
  **Las cifras de Timoshenko se recuerdan sin las dos salvedades que el capítulo 3 declara**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-102**.

- H-103 · *media* · Conclusiones, tercer párrafo, p. 102 (PDF p.118) — instancia única · 15 min
  **«Queda demostrado» y «El trabajo lo establece» exceden el tipo de evidencia declarado**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-103**.

- H-100 · *media* · §3.7.1, primer párrafo, p. 93 (PDF p.109) · 15 min
  **«Eso descarta errores de orden» se emite sin la salvedad que llega dos subsecciones después**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-100**.

- H-097 · *media* · §3.2, p. 76 (PDF p.92) · 15 min
  **«Descarta» atribuye a dos pruebas un poder de exclusión que el propio capítulo desmiente**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-097**.

- H-074 · *media* · §3.3 «Consistencia interna del modelo de datos», p. 79 (PDF p.95) · 5 min
  **Una prueba con un juego de identificadores «descarta los fallos» de indexación en general**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-074**.

- H-075 · *media* · §3.1 «Medición de los datos y validación de la medición», p. 74 (PDF p.90) · 5 min
  **«La confiabilidad de estas mediciones se asegura por tres vías»: tres precauciones no aseguran**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-075**.

- H-077 · *media* · §3.7.4 «Limitaciones observadas», tab:tiempos y párrafo siguiente, p. 98 (PDF p.114) · 15 min
  **La leyenda de tiempos describe el protocolo peor de lo que es, y las razones van a dos cifras**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-077**.

- H-088 · *media* · §3.7.4, p. 98 (PDF p.114) · 15 min
  **Factores de aceleracion con una cifra decimal sobre corridas cuya variabilidad la tabla cifra en 50 %**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-088**.

- H-020 · *media* · §2.2.2, nota de la Tabla 2.5, p. 57 (PDF p. 73) · 1 h
  **La tesis llama libre al software sin nombrar nunca la licencia, y la nota la deja en futuro**
  <br>→ No hay contradiccion interna que resolver, sino un dato faltante y una nota desactualizada. (1) Nombrar la licencia donde se declara el requisito de software libre (03_diseno_implementacion.tex:18) y en la fila «Licencia» de la Tabla 1.1. (2) Cerrar la nota de la Tabla 2.5 indicando la licencia ado…

- H-205 · *media* · Resumen, p. i (PDF p.2) · 15 min
  **El Resumen invoca «el alcance declarado» sin declararlo en ninguna parte del Resumen**
  <br>→ Sustituir la última oración por: «La hipótesis queda comprobada con criterios fijados de antemano y dentro del alcance declarado: lo evaluado son propiedades del software y de sus resultados, no su uso por estudiantes, y el contraste con referencias externas se limita a la tensión plana.»

- H-234 · *media* · Resumen, p. i (PDF p.2) · 15 min
  **El Resumen no nombra el método de investigación**
  <br>→ Intercalar en 00_resumen.tex, tras la oración de la hipótesis: «El método es el de la ciencia del diseño: el conocimiento se obtiene construyendo el software y evaluándolo con criterios fijados de antemano.» Antes de aplicarlo, comprobar el límite de palabras del resumen que fije el reglamento: el…

- H-005 · *baja* · Resumen, p. i (PDF p.2) y §3.7.1 «Alcances», p. 96 (PDF p.112) · 15 min
  **El Resumen omite el subindice de la tension normal (sigma_x) que el cuerpo si escribe**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-005**.

- H-283 · *baja* · Conclusiones, cierre del contraste de hipótesis, p. 105 (PDF p.121) · 15 min
  **«El desarrollo de EduFEM mejoró…de caja negra a procedimiento a la vista»: comparación nunca hecha**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-283**.

- H-284 · *baja* · Conclusiones, Objetivo específico 3, p. 104 (PDF p.120) · 5 min
  **La trazabilidad depende de una decisión en el OE3 y de tres en los Aportes**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-284**.

- H-285 · *baja* · Recomendaciones, «Guía de uso en la cátedra», p. 109 (PDF p.125) · 5 min
  **«El manual del Anexo B enseña a operar el software»: verbo de enseñanza**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-285**.

- H-281 · *baja* · «Alcance y limitaciones», p. 9 (PDF p.25) · 5 min
  **«El plano es la mínima dimensión en la que aparece el carácter de continuo» es falso en sentido estricto**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-281**.

- H-016 · *baja* · Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) · 5 min
  **Una elipsis en las Conclusiones arrastra «errores» sobre la diferencia frente a SAP2000**
  <br>→ Cerrar la elipsis en la p. 104: «...y del 0,26 % en la flecha; la diferencia frente al modelo de SAP2000 fue de hasta el 0,21 % en sigma_x». Una sola ocurrencia.

- H-316 · *baja* · Conclusiones, segundo párrafo, p. 102 (PDF p.118) · 15 min
  **«medio de cálculo»: término inédito que responde al problema científico**
  <br>→ No sustituir el término (es el campo de acción declarado). Basta explicitar el enlace con la variable independiente en la primera aparición: «la incidencia está en el medio de cálculo, es decir, en la forma en que el software expone el procedimiento de cálculo». Dejar intacta la segunda oración sal…

- H-317 · *baja* · Conclusiones, Objetivo específico 2, p. 103 (PDF p.119) · 5 min
  **El segundo principio cambia de nombre respecto de §1.2**
  <br>→ Escribir «la interactividad con vínculo al modelo», literal de §1.2.


### B2 — Cerrar las dos brechas de evidencia

> **Por qué aquí.** Segundo porque es lo único del informe que exige producir algo nuevo —el cotejo manual ejecutado y el tratamiento de la etapa 6— y porque de su resultado dependen las frases que B1 dejó a medio calibrar. Si el cotejo se reporta, el Resumen puede afirmar «reproducida a mano» sin matices; si no, hay que rebajar las tres apariciones.

**Esfuerzo del bloque: 4 h** · 15 correcciones

- **H-004** · *alta* · §2.1.4, p. 49 (PDF p. 65) · 30 min
  **El universo de contenido excluye el único ítem que el software no cubre, y luego se reporta 18 de 18**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-004**.

- **H-012** · *alta* · Tabla 3.7, fila FEA30, p. 91 (PDF p.107) · 15 min
  **FEA30 acredita como «Instrumento de EduFEM» una extrapolación de Richardson que el software no implementa**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-012**.

- **H-022** · *alta* · §3.6.1, p. 87 (PDF p.103) · 2 h+
  **Criterio «9 de 9 etapas en la memoria»: la etapa 6 no aparece ni en el Anexo G ni en la memoria**
  <br>→ Opción preferente, y más barata que la propuesta: añadir en el Anexo G, dentro de G.2.3, un párrafo de cierre con la sustitución de la etapa 6 sobre una arista del mismo modelo —por ejemplo la arista 7-8 con q constante— aplicando F1 = L/6(2q1+q2) y F2 = L/6(q1+2q2), y declarando expresamente que esa carga no forma parte del modelo resuelto, para que el resto de las cifras del anexo siga siendo la corrida real. Numerar esa expresión en §1.10 (hoy va en línea, en `02_marco_teorico.tex` línea 334, con \tfrac y sin \label) para poder remitirla, como exige el criterio de la Tabla 2.4. Si el autor prefiere no tocar el anexo, la alternativa es declarar la limitación en los cuatro sitios a la vez —§3.6.1 p. 87, Tabla 2.4 p. 52, Tabla 3.10 pp. 99-100 y §3.8 p. 100—: «ocho de las nueve etapas se sustituyen numéricamente sobre el ejemplo canónico; la etapa 6 no interviene en él, porque su única carga es nodal, y se expone en el módulo M6 (Figura B.12) y en el desglose del vector F que la memoria emite cuando el modelo lleva carga superficial». No basta con corregir la Tabla 3.10: sin tocar la Tabla 2.4 quedarían un umbral y un veredicto en conflicto.

- H-072 · *media* · §3.6 «Cobertura de contenido», p. 90 (PDF p.106) · 15 min
  **La tabla de cobertura «demuestra» lo que en realidad respalda: cotejo documental del autor**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-072**.

- H-085 · *media* · Título de la Tabla 3.7, §3.6.2, p. 91 (PDF p.107) · 15 min
  **La columna «Evidencia» de la tabla de cobertura dice «demuestra» donde solo remite a una descripción**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-085**.

- H-009 · *media* · §2.1.6, Tabla 2.4, p. 52 (PDF p.68) · 30 min
  **Los tres umbrales de exactitud (3 %, 1 % y 1,5 %) no se justifican en ninguna página**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-009**.

- H-134 · *media* · §2.1.4, p. 49 (PDF p. 65) frente a la nota de la Tabla 3.7, p. 92 (PDF p. 108) · 5 min
  **Los 18 ítems fuera del alcance disciplinar se enumeran en nueve grupos en la Tabla 3.7 y en ocho en §2.1.4**
  <br>→ En `02b_diseno_metodologico.tex`, §2.1.4, insertar el grupo que falta: «… modelado en CAD, cargas tomadas de un análisis previo, elementos rígidos y contacto». (Comprobado: con ese grupo los códigos suman exactamente 18, y 18 + 12 + 1 = 31.)

- H-159 · *media* · §2.1.4, p. 49 (PDF p. 65), frente a la nota de la Tabla 3.7, p. 92 (PDF p. 108) · 15 min
  **Los 31 ítems excluidos del consenso se enumeran completos en §2.1.4 y en la nota de la Tabla 3.7**
  <br>→ Aparición canónica: la nota de la Tabla 3.7, p. 92 (PDF p. 108), que es la única que da los códigos FEM/FEA. En §2.1.4 (p. 49) borrar la enumeración de dominios y dejar: «Los 31 ítems restantes quedan fuera por tres motivos —alcance disciplinar (18), anterioridad al procedimiento de cálculo (12) y…

- H-201 · *media* · §2.1.5, p. 50 (PDF p. 66) · 15 min
  **Los 18 contenidos los definieron expertos mexicanos de ingeniería mecánica: ¿por qué valen para Potosí?**
  <br>→ Añadir a la nota de la Tabla 3.7 (p. 92) una oración de remisión: «La procedencia del universo, su recorte y el alcance de la advertencia de generalización de la fuente se discuten en la Subsección 2.1.5.» Y preparar esta respuesta oral: «Del estudio no tomo su ranking, que sí es local: tomo la lis…

- H-194 · *media* · §3.8, Tabla 3.10, pp. 99-100 (PDF pp. 115-116) · 30 min
  **Todos los criterios de trazabilidad dan 100 % y los verificó usted: ¿qué podía salir mal?**
  <br>→ No inventar un incumplimiento y NO usar el argumento de FEM3 como si hubiera sido un fallo detectado al medir: FEM3 se excluye del universo a priori en §2.1.4, y presentarlo de otro modo expone el flanco de la circularidad. (1) En §3.8, tras «La cláusula (a), trazabilidad, se cumple en todos sus cr…

- H-211 · *media* · §2.1.2, p. 44 (PDF p.60) · 15 min
  **No se argumenta por qué contar etapas expuestas mide la trazabilidad; el salto se asume**
  <br>→ Añadir tras esa frase: «El recuento es la medida adecuada porque la cadena de la trazabilidad se rompe en su eslabón más débil: basta con que una etapa quede oculta para que el resultado deje de poder seguirse hasta los datos. Por eso el indicador cuenta etapas expuestas y el umbral es la exhaustiv…

- H-023 · *media* · §2.1.1, p. 42 (PDF p.58) · 1 h
  **Tres formulaciones anuncian un cotejo manual ejecutado; el criterio que se aplica mide otra cosa**
  <br>→ Alinear las tres formulaciones con el criterio que realmente se aplica, que es el de la Tabla 2.4 («Etapas de la memoria desarrolladas con sustitucion numerica y remitidas a su ecuacion, de modo que puedan rehacerse a mano»). Concretamente: §2.1.1, p. 42 -> «Y es descriptiva en el ejemplo canonico,…

- H-232 · *media* · Objetivo específico 3, p. 5 (PDF p.21) · 15 min
  **El OE3 promete «cada etapa» con modulo educativo; el criterio de aceptacion pide 7 de 9**
  <br>→ Reescribir el OE3 así: «Desarrollar el motor de cálculo con elementos Q4 y Q9, la interfaz gráfica organizada en pre-proceso, proceso y post-proceso sobre un único lienzo, los módulos educativos que exponen sobre el modelo real las etapas del procedimiento hasta el ensamblaje, el post-proceso que e…

- H-240 · *media* · §2.1.2, p. 43 (PDF p.59) y §2.1.3, p. 46 (PDF p.62) · 30 min
  **La hipótesis afirma «elevar» la variable dependiente, pero ningún indicador se evalúa en el nivel de referencia**
  <br>→ Insertar en §2.1.2, tras «…se documenta con la matriz de atributos de la Tabla 1.1»: «En ese nivel de referencia la Tabla 1.1 registra, para el software comercial, un cálculo paso a paso ‹Baja (caja negra)›, un procedimiento completo ‹No (no didáctico)› y, como documentación, ‹Informes de resultado…

- H-215 · *baja* · §3.8, p. 101 (PDF p.117) · 15 min
  **El argumento de que la hipótesis no es tautológica descansa en una sola anécdota retrospectiva**
  <br>→ Rebajar el verbo y declarar la naturaleza del caso: «La Subsección 3.7.2 aporta un indicio, en un episodio del propio desarrollo, de que esa relación no es vacía: la lectura paso a paso de la memoria hizo visible un defecto de exactitud que las métricas agregadas no delataban, y ese defecto pudo co…


### B3 — Hacer reproducible el caso de validación central

> **Por qué aquí.** Tercero porque es autocontenido (§3.4 y Anexo E) y porque es la pregunta que un tribunal de ingeniería civil hace primero. No depende de nada anterior, pero conviene hacerlo antes de la pasada de redundancia, que también toca §3.4.

**Esfuerzo del bloque: 2 h** · 10 correcciones

- **H-021** · *alta* · §3.4, pp. 80-81 (PDF pp. 96-97) · 1 h
  **¿Cómo modeló los apoyos de la viga y con qué discretización la resolvió en SAP2000?**
  <br>→ Agregar en §3.4, tras la descripción de la malla Q9 de 56 × 8 (p. 80), cinco o seis renglones con: (a) los GDL restringidos en cada apoyo y sobre qué nodos —apoyo fijo y apoyo móvil, nodo único o arista completa—; (b) cómo se aplicó q = 5000 kgf/m, es decir, como carga superficial uniforme sobre la arista superior convertida a fuerzas nodales equivalentes según la Sección 1.10; y (c) el modelo de SAP2000: versión del programa, número y tamaño de los elementos shell, espesor y condiciones de apoyo —las capturas de la p. 147 ya los muestran, de modo que basta con contar y declarar lo que allí se ve—. Si algún apoyo es puntual, decir que introduce una singularidad local de tensiones y que los puntos A, B y C están alejados de ella. No declarar ningún dato que no pueda leerse del modelo o de las capturas.

- H-063 · *media* · Tabla 3.2, p. 81 (PDF p.97) · 30 min
  **Las columnas de error mezclan cuatro decimales con dos y declaran más precisión de la sostenible**
  <br>→ Unificar las cinco filas de cada columna de porcentaje a dos cifras significativas (0,022 · 0,041 · 0,027 · 0,94 · 2,89 y 0,025 · 0,21 · 0,072 · 4,6 · 2,7) y aplicar el mismo criterio a la Tabla 3.3 (0,26 · 0,39 · 0,56 · 0,47) y al texto que las comenta.

- H-064 · *media* · Tabla 3.1, p. 76 (PDF p.92) · 15 min
  **La Tabla 3.1 no dice que sus normas son adimensionales ni remite a los errores relativos del Anexo D**
  <br>→ Añadir a la leyenda de la Tabla 3.1: «Las magnitudes son adimensionales, por serlo el material de la configuración base (E = 1,0; t = 1,0). La Tabla D.2 reporta los mismos errores en forma relativa.» y citar \autoref{tab:mms-rel} en el párrafo que comenta la tabla.

- H-129 · *media* · Tabla 3.1, p. 76 (PDF p. 92) frente a Tabla D.2, p. 140 (PDF p. 156) · 15 min
  **El mismo caso da dos errores distintos en el cuerpo y en el Anexo D porque uno es absoluto y el otro relativo, pero la tabla del cuerpo no lo dice**
  <br>→ En la Tabla 3.1 rotular las columnas «error L2 abs.» y «error H1 abs.» y añadir a su nota al pie: «Los errores son absolutos; los relativos, para la misma configuración, están en la Tabla D.2.» Añadir también en §3.2, tras la tabla, una remisión con \autoref a la Tabla D.2.

- H-212 · *media* · §3.4, Tabla 3.3, p. 82 (PDF p.98) · 30 min
  **La flecha calculada supera a la analítica y a SAP2000 y el documento no explica por qué**
  <br>→ Añadir tras el comentario de la Tabla 3.3: «La flecha calculada supera en 0,26 % a la analítica. La diferencia es coherente con la forma en que el modelo bidimensional realiza los apoyos —dos nodos restringidos a la altura del eje neutro— frente a la distribución de cortante que la solución de Timo…

- H-213 · *media* · §3.4, p. 82 (PDF p.98) · 15 min
  **El 4,56 % de las componentes secundarias se reporta sin decir que queda fuera del criterio ni dónde se explica**
  <br>→ Añadir tras la enumeración: «Estas componentes se reportan pero no forman parte del criterio de aceptación, que se fija sobre σx por ser la magnitud primaria del problema de flexión (Subsección 2.1.6); la Sección 3.7 discute por qué su error relativo está dominado por la diferencia de escala.»

- H-308 · *baja* · Tabla 3.1, fila N = 16 del bloque Q4, p. 76 (PDF p.92) · 15 min
  **La tasa H1 de 1,01 del Q4 no se recupera de los errores que muestra la misma tabla**
  <br>→ Recomprobar esa celda contra el CSV del guion y corregirla a 1,00 si procede, o añadir a la leyenda que las tasas se calculan con los valores sin redondear.

- H-310 · *baja* · §3.5, p. 84 (PDF p.100) · 5 min
  **Se presenta como coincidente con 0,05 % una distancia que vale 0,04 %**
  <br>→ Cambiar «y coincide con la distancia» por «y es del mismo orden que la distancia (0,04 %)».

- H-193 · *baja* · §3.4, p. 80 (PDF p. 96) · 2 h+
  **Ese 0,04 %, ¿de qué malla sale? ¿Y qué habría dado con otra?**
  <br>→ Lo barato y suficiente es la respuesta oral, apoyada en lo ya reportado: «La malla de 56 × 8 se eligió antes de correr el caso; el caso no se planteó como estudio de convergencia porque esa función la cumplen las soluciones manufacturadas y la membrana de Cook, donde recorro cinco mallas y mido la…

- H-351 · *baja* · §3.7.1, p. 95 (PDF p.111) · 30 min
  **La cifra 0,16 % que sostiene una comparación no tiene celda en ninguna tabla**
  <br>→ Añadir a la Tabla D.4 (p. 142) una columna «Error SAP2000 frente a analítica (%)» con el valor 0,16 en la fila de τxy en B, y en §3.7.1 remitir a ella: «(0,16 %, Tabla D.4)».


### B4 — Una palabra, un sentido

> **Por qué aquí.** Cuarto porque el cambio del OE5 se propaga a la Tabla 2.1, a la matriz de consistencia, al título de §3.1 y a las Conclusiones: conviene hacerlo de una sola pasada y antes de tocar la trazabilidad fina, que trabaja sobre esas mismas tablas.

**Esfuerzo del bloque: 1,5 h** · 14 correcciones

- **H-015** · *alta* · §2.1.1, p. 42 (PDF p.58) · 30 min
  **«Validación» se usa en tres sentidos dentro de §2.1, contra la acepción única que el documento declara en §1.13**
  <br>→ Mantener (1) y (2) tal como se proponen. Sustituir (3) por lo siguiente: conservar «5. Validar la propuesta» en la Tabla 2.3 para que la matriz siga reproduciendo el enunciado literal del OE5, y añadir en §1.13, al final del párrafo que fija la acepción, una excepción explícita: «El enunciado del objetivo específico 5, ‹validar la propuesta›, emplea el verbo en su sentido metodológico corriente —contrastar la solución contra los criterios de aceptación fijados de antemano— y no en la acepción que esta sección fija.» Con eso quedan cubiertas las tres apariciones sin tocar la Introducción ni §3.8.

- H-127 · *media* · §2.1.4, p. 47 (PDF p. 63) frente a Anexo B §B.6, p. 123 (PDF p. 139) — ambas confirmadas · 15 min
  **«Tres casos de estudio» designa dos conjuntos distintos según el capítulo**
  <br>→ En `06_anexos.tex` línea 168 reemplazar «ofrece tres casos de estudio, cada uno en variante Q4 y Q9» por «ofrece tres modelos de ejemplo precargados, cada uno en variante Q4 y Q9», y dentro del paréntesis del primero escribir «el ejemplo canónico del trabajo» en lugar de «el primer caso de prueba d…

- H-141 · *media* · §2.1.1, p. 43 (PDF p.59) y §2.1.4, p. 47 (PDF p.63) · 15 min
  **La unidad de análisis se define dos veces y con dos formulaciones distintas**
  <br>→ Fijar una sola formulación —la de §2.1.4, que es la que sostiene la población— y borrar la de §2.1.1. En §2.1.1, retitular el párrafo como «Versión evaluada» y abrirlo con: «Las dos variables del problema científico se observan sobre el procedimiento de cálculo del software (Subsección 2.1.4), con…

- H-142 · *media* · §2.1.1, p. 41-42 (PDF p.57-58) · 5 min
  **«Artefacto» aparece cuatro veces cuando CRITERIOS lo admite una sola vez en §2.1.1**
  <br>→ Conservar la primera («el artefacto, en la terminología del método; aquí, EduFEM») y sustituir las otras tres: «estudia el uso del artefacto dentro de una organización» → «estudia el uso de la herramienta dentro de una organización»; «debe elegirse según el artefacto y según las métricas» → «debe e…

- H-143 · *media* · §2.2.3 Arquitectura por capas, Figura 2.2 vs. Tabla 2.6, p. 59 (PDF p. 75) · 30 min
  **La Figura 2.2 llama «validación» y «undo» a lo que la Tabla 2.6, en la misma página, llama «comprobación de salud» y «deshacer/rehacer»**
  <br>→ En tesis/figuras/generar_figuras.py:181 cambiar «models/\nentidades · validación · undo» por «models/\nentidades · salud · deshacer» y regenerar fig_arquitectura.png. Aprovechar para ensanchar el recuadro o reducir la fuente: en el PDF impreso el rótulo actual ya desborda la caja azul por ambos lad…

- H-145 · *media* · Tabla 3.6 y párrafo siguiente, p. 89 (PDF p.105) · 5 min
  **La Tabla 3.6 atribuye el conmutador a M1-M7 y el texto de la misma página solo a seis módulos**
  <br>→ Corregir la celda de la Tabla 3.6 a «M1 a M7: capas superpuestas; conmutador Fórmula ↔ Valores en M1 a M5 y M7».

- H-147 · *media* · Conclusiones, contraste de hipótesis, p. 105 (PDF p.121) · 5 min
  **«tres estudios de convergencia del desplazamiento»: recuento que el cuerpo no sostiene**
  <br>→ Borrar el numeral y alinear con §3.7.2: «Un defecto en la extrapolación de tensiones del elemento Q4 no lo delataron los estudios de convergencia del desplazamiento, porque esa matriz no interviene en el desplazamiento; lo delató la lectura de la memoria de cálculo, donde las tensiones nodales no c…

- H-148 · *media* · Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) · 5 min
  **«criterios de aceptación escritos en los propios guiones» contradice el lugar canónico §2.1.6**
  <br>→ Sustituir por: «Se aplicó una batería de tres casos de estudio, contra los criterios de aceptación fijados de antemano en la Subsección 2.1.6 y reproducidos en los guiones de verificación.»

- H-307 · *baja* · §2.2.2 Tecnologías empleadas, nota de la Tabla 2.5, p. 57 (PDF p. 73) · 5 min
  **«Programa» se usa para nombrar a EduFEM, término prohibido salvo para software de terceros**
  <br>→ Sustituir «la licencia del programa» por «la licencia del software» o «de la herramienta».

- H-313 · *baja* · Figura 3.5, p. 88 (PDF p.104) · 5 min
  **La leyenda de la Figura 3.5 usa «la aplicación», término que CRITERIOS.md prohíbe**
  <br>→ Escribir «Capturas de EduFEM.»

- H-296 · *baja* · §2.1.2, p. 43-44 (PDF p. 59-60) · 5 min
  **«Nueve etapas… cada una en su sección», pero las nueve etapas ocupan siete secciones**
  <br>→ Sustituir la frase introductoria por: «El procedimiento de cálculo se divide en nueve etapas, que desarrolla el Capítulo 1; la sección que trata cada una se indica entre paréntesis y algunas comparten sección:».

- H-306 · *baja* · §2.1.3, p. 46 (PDF p.62) · 5 min
  **El contrato editorial del autor dice «podrá afectar» y el documento dice «podrá incidir»**
  <br>→ Actualizar `tesis/capitulos_final/CRITERIOS.md` §1 sustituyendo «podrá afectar en» por «podrá incidir en», para que el contrato editorial reproduzca la redacción vigente del documento. No tocar los tres lugares del documento.

- H-312 · *baja* · Tabla 3.6, fila «Pre-proceso», p. 89 (PDF p.105) · 15 min
  **La Tabla 3.6 asigna al pre-proceso una «etapa» que no está entre las nueve que su leyenda invoca**
  <br>→ Bastaría con añadir a la leyenda de la Tabla 3.6: «La discretización y la calidad de malla anteceden a las nueve etapas y no se cuentan entre ellas». Si se prefiere tocar la celda, escribir «Previo a las nueve etapas: discretización y calidad de malla»; no hace falta renombrar la columna.

- H-315 · *baja* · Tabla 3.7, fila FEM8, p. 92 (PDF p.108) · 5 min
  **FEM8, formulación isoparamétrica, se acredita con M4, que es la matriz constitutiva**
  <br>→ Dejar «M1, M2 y M3» en la celda de instrumento de FEM8, o justificar la inclusión con una glosa: «M1, M2 y M3 (mapeo, Jacobiano y matriz B); M4 aporta la matriz constitutiva con que se completa la rigidez».


### B5 — Trazabilidad fina de la matriz de consistencia y de los veredictos

> **Por qué aquí.** Quinto: es trabajo de tabla contra tabla (Tabla 2.1, 2.3, 2.4, 3.10 y las conclusiones por objetivo) y solo tiene sentido cuando B2 y B4 ya fijaron qué criterios hay, cómo se llaman y cuántos son. Incluye el arreglo de cinco minutos de la PI-3.

**Esfuerzo del bloque: 3 h** · 28 correcciones

- **H-014** · *alta* · Nomenclatura, «Abreviaturas y siglas», p. xv (PDF p. 16) · 5 min
  **La Nomenclatura anuncia una PI-3 que no existe: el documento solo tiene PI-1 y PI-2**
  <br>→ En `00b_nomenclatura.tex`, línea 156, sustituir la celda por: «PI & Pregunta de investigación (PI-1 y PI-2) \\». Comprobar después que `grep -c "PI-3" capitulos_final/*.tex` devuelve 0.

- **H-024** · *alta* · Conclusiones, «Objetivo específico 3 —desarrollar—», pp. 103-104 (PDF pp.119-120) · 15 min
  **La conclusión del OE3 omite el intercambio de datos que el propio objetivo promete**
  <br>→ Añadir una oración al final del párrafo del OE3 (p. 104), después de «La memoria de cálculo en PDF reconstruye el procedimiento paso a paso con las mismas funciones del motor», empleando el vocabulario que la Sección 3.3 ya usa: «Y los formatos de intercambio cierran el recorrido fuera de la herramienta: el modelo exportado al paquete CSV/ZIP vuelve a ella sin pérdida de entidades y la importación del DXF es idempotente (Sección 3.3).» Evitar «repetible», que no es el término del reporte —§3.3 dice «idempotente»—, y no agregar cifras: las del ensayo ya están en §3.3 y repetirlas en la conclusión rompería la regla de una sola aparición canónica.

- H-060 · *media* · «Planteamiento del problema», p. 2 (PDF p.18) → Tabla 1.1, p. 16 (PDF p.32) · 15 min
  **La Tabla 1.1 sostiene la afirmación central del planteamiento, pero aparece catorce páginas después**
  <br>→ Reformular la remisión para que la afirmación se sostenga sola en su sitio y la tabla quede como comprobación: «Entre los recursos revisados en la Sección 1.1 —programas educativos, simuladores de un eslabón, bibliotecas de programación y software comercial—, ninguno documenta a la vez tres atribut…

- H-119 · *media* · §2.1.6, Tabla 2.4, p. 51 (PDF p.67) · 15 min
  **El criterio del inventario cubre «etapas 1 a 7» de nueve sin decir en ningún lugar de §2.1 por qué**
  <br>→ Añadir en §2.1.6, antes de la Tabla 2.4: «El inventario de módulos cubre las etapas 1 a 7 porque las dos últimas —la solución del sistema y la recuperación de tensiones— no se exponen en un módulo sino en el post-proceso, que la fila siguiente audita con su propio criterio; las nueve, en cambio, se…

- H-191 · *media* · Introducción, «Planteamiento del problema» y «Delimitación», pp. 2-3 (PDF pp. 18-19) · 1 h
  **¿Qué dato tomó usted en la Carrera de la UATF para afirmar que allí existe el problema?**
  <br>→ No tocar la formulación. (1) Opcional y solo si las fuentes existen: tres renglones tras el párrafo del problema (p. 2) con el anclaje documental de la premisa local —asignatura del plan de estudios vigente donde se aborda el análisis matricial o por elementos finitos, software y bibliografía en us…

- H-223 · *media* · Tabla 2.4, p. 52 (PDF p.68), fila «Intercambio de datos» dentro del bloque «Cláusula (a)… · 30 min
  **El intercambio de datos es objetivo y criterio, pero no cláusula, ni requisito, ni conclusión**
  <br>→ Una de dos, no las dos. (a) Si el intercambio se mantiene como criterio de la cláusula (a): añadirlo a la enumeración de §3.8, p. 100 —«…los dieciocho ítems del universo de contenido tienen instrumento y el modelo entra y sale de la herramienta sin pérdida»—, con lo que la prosa pasa de cinco a sei…

- H-224 · *media* · Tabla 2.3, p. 46 (PDF p.62), fila «3. Desarrollar el motor, la interfaz, los módulos y la… · 15 min
  **La matriz de consistencia cierra el OE3 con su propia descripción, sin ningún resultado**
  <br>→ En la celda «Evidencia» de la fila 3 de la Tabla 2.3 escribir «Sección 2.2; Sección 3.3; Subsección 3.6.1» y en la celda «Variable / indicador» añadir «etapas expuestas; formatos con ida y vuelta sin pérdida».

- H-225 · *media* · Tabla 2.4, p. 52 (PDF p.68), última fila · 30 min
  **El criterio del ejemplo canónico no recibe bloque de veredicto en el cuerpo y duplica al criterio a2**
  <br>→ Añadir al final del párrafo «Trazabilidad e intercambio de datos» de §3.6.1 (p. 90) un bloque: «Criterio fijado en la Subsección 2.1.6: todas las etapas de la memoria del ejemplo canónico desarrolladas y remitidas a su ecuación. Observado: todas, según el Anexo G. Se cumple». Y diferenciar el crite…

- H-226 · *media* · Tabla 2.1, p. 41 (PDF p.57) frente a Tabla 2.3, p. 46 (PDF p.62) · 15 min
  **La Tabla 2.1 y la Tabla 2.3 dan dos mapas distintos de objetivo a sección**
  <br>→ En la Tabla 2.1, cambiar la celda «Dónde» de la actividad 4 a «Sección 3.2 a Sección 3.5» con OE 4, y la de la actividad 5 a «Sección 3.6 a Sección 3.8» con OE 5; mover «Anexo G» a la fila de la actividad 5. Y alinear la celda de la actividad 2, hoy «Sección 1.1; Subsección 2.1.6», con la Tabla 2.3…

- H-227 · *media* · Conclusiones, primer párrafo, p. 102 (PDF p.118), frente a Introducción, «Objetivos», p… · 15 min
  **El objetivo general se declara cumplido restituyendo solo sus medios, no su cláusula de finalidad**
  <br>→ Cerrar el primer párrafo de las Conclusiones con: «La finalidad que el objetivo enuncia —que el análisis por el MEF resulte trazable y verificable paso a paso— queda establecida sobre el software y sus resultados, con los criterios de la Subsección 2.1.6; su efecto en la enseñanza de la Carrera no…

- H-228 · *media* · Introducción, p. 2 (PDF p.18) · 15 min
  **El diagnóstico del OE1 se enuncia con tres recuentos de atributos sin mapa entre ellos**
  <br>→ En la Introducción, p. 2, escribir «ninguno de los recursos revisados reúne a la vez los ocho atributos que la Sección 1.1 enumera; tres de ellos concentran el vacío: […]». En §2.2.1, p. 54, cortar la ambigüedad: «la produce el diagnóstico del Capítulo 1, que en la Tabla 1.1 identifica los ocho atr…

- H-229 · *media* · Introducción, p. 3 (PDF p.19) · 15 min
  **El campo de acción se declara una sola vez y nunca se retoma en el diseño ni en las conclusiones**
  <br>→ En el segundo párrafo de las Conclusiones, p. 102, nombrarlo explícitamente: «La incidencia está en el medio de cálculo, que es el campo de acción declarado en la Introducción: el software educativo que expone el procedimiento y la memoria de cálculo que lo documenta sobre el modelo del usuario».

- H-230 · *media* · Conclusiones, «Limitaciones», p. 107 (PDF p.123), frente a «Recomendaciones y trabajo… · 30 min
  **Una limitación declarada no recibe recomendación, pese a que el texto dice que las tres salen de ellas**
  <br>→ Añadir en «Sobre el software (Capítulo 2)» una recomendación breve: «Módulos para la solución y la recuperación de tensiones. Las etapas 8 y 9 se exponen hoy en el post-proceso y en la memoria; un módulo M8 sobre la partición Kff uf = Ff y un M9 sobre la extrapolación desde los puntos de Gauss comp…

- H-231 · *media* · §3.3, p. 80 (PDF p.96) y §3.6.1, p. 90 (PDF p.106) · 15 min
  **El criterio del intercambio de datos recibe dos veredictos en dos secciones distintas**
  <br>→ Conservar el bloque de §3.3, p. 80, como veredicto canónico (es donde están las cifras) y sustituir el de §3.6.1, p. 90, por una remisión: «La ida y vuelta CSV, la repetibilidad de la importación DXF y la generación de la memoria para Q4 y Q9 se contrastaron con su criterio en la Sección 3.3».

- H-241 · *media* · §2.1.3, p. 47 (PDF p.63) · 30 min
  **El intercambio de datos es criterio de la cláusula (a) aunque §2.1.3 declara que no deriva de ninguna pregunta**
  <br>→ Adoptar la opción recomendada, corregida en el destino: en §2.1.3 escribir «El intercambio de datos (DXF, CSV), incluido en el tercer objetivo, es un complemento instrumental de la trazabilidad: no origina una pregunta propia, pero sí un criterio de la cláusula (a), porque un modelo que no puede en…

- H-242 · *media* · §2.1.1, Tabla 2.1, fila «2. Definir los objetivos de la solución», p. 41 (PDF p.57) · 5 min
  **La Tabla 2.1 envía a buscar los requisitos donde no están: §2.2.1 es quien los enumera**
  <br>→ Cambiar la celda «Dónde» de la fila 2 por «Sección 1.1; Subsección 2.2.1» y, si se quiere conservar la remisión a los umbrales, escribir «Sección 1.1; Subsección 2.2.1 (requisitos); Subsección 2.1.6 (umbrales)».

- H-243 · *media* · §2.1.3, Tabla 2.3, p. 46 (PDF p.62) · 30 min
  **La matriz de consistencia no lleva la hipótesis ni sus dos cláusulas, y en el cuerpo la enuncia abreviada**
  <br>→ Añadir a la Tabla 2.3 una columna «Cláusula» entre «PI» y «Variable / indicador», con los valores: OE1 «(a) y (b)», OE2 «(a) y (b)», OE3 «(a)», OE4 «(b)», OE5 «(a) y (b)». Y en el cuerpo citar la hipótesis textualmente, como se hace con el problema: «Se contrasta con la hipótesis, enunciada en la I…

- H-244 · *media* · §2.1.6, p. 51 (PDF p.67) · 15 min
  **«Quedaron fijados antes de las corridas» no cubre los criterios documentales, que no tienen corridas**
  <br>→ Reescribir: «Unos y otros quedaron fijados antes de la evidencia que los juzga: los numéricos, antes de las corridas que este documento reporta; los documentales, antes del cotejo de la versión evaluada, y están escritos en la revisión 91e3df0 del repositorio junto con los guiones que los evalúan,…

- H-245 · *media* · §2.1.6, Tabla 2.4, p. 51-52 (PDF p.67-68) · 30 min
  **La Tabla 2.4 declara trece criterios y la tabla de veredictos de §3.8 reporta quince**
  <br>→ Desdoblar ya en la Tabla 2.4 las dos filas, para que las dos tablas tengan quince criterios y la correspondencia sea uno a uno: separar «Tasa de convergencia del desplazamiento, norma L² (cuatro configuraciones)» y «…seminorma H¹ (cuatro configuraciones)», y separar «Error de σx frente a la solució…

- H-246 · *media* · §3.3, p. 79 (PDF p.95) · 15 min
  **§3.3 no declara a qué cláusula de la hipótesis responde, y §2.1.6 la asigna a la equivocada**
  <br>→ Abrir §3.3 con «Esta sección reporta el criterio de intercambio de datos de la cláusula (a)» y corregir en §2.1.6 el tramo a «se contrasta en la Sección 3.2 y de la Sección 3.4 a la Sección 3.5».

- H-247 · *media* · §3.6.2, p. 90-91 (PDF p.106-107), frente a §2.1.5, p. 50 (PDF p.66) · 1 h
  **§3.6.2 reformula la regla de marcado más débil que como §2.1.5 la declara, y la aplica así**
  <br>→ Restituir la regla literal en 04_resultados.tex:278 («…y la \autoref{sec:diseno-edufem} o el \autoref{anexo:manual} lo describen») y comprobar fila por fila que los instrumentos de FEA14, FEA16, FEA17, FEA29, FEA30 y FEA34 están descritos en §2.2 o en el Anexo B; añadir esa remisión donde falte, y…

- H-249 · *media* · Tabla 2.4, §2.1.6, p. 52 (PDF p.68) —origen— y Tabla 3.10, bloque «Cláusula (a)», p. 99… · 30 min
  **La Tabla 3.10 cuenta como criterio de la cláusula (a) el intercambio de datos, que la cláusula no enuncia**
  <br>→ Corregir las DOS tablas de forma coherente: sacar la fila «Intercambio de datos» del bloque «Cláusula (a): trazabilidad» tanto en la Tabla 2.4 como en la Tabla 3.10 y ponerla al pie de cada una bajo el rótulo «Complemento instrumental (no deriva de una pregunta de investigación, \autoref{sec:pregun…

- H-250 · *media* · §3.7.4, p. 98 (PDF p.114) · 30 min
  **Tres factores de aceleración sostienen la respuesta sobre escalabilidad sin tabla ni reordenamiento nombrado**
  <br>→ Nombrar el reordenamiento y su procedencia («el reordenamiento por columnas de aproximación de grado mínimo que aplica la factorización dispersa de SciPy») y añadir las tres razones como columna de la Tabla 3.9 —«t_solución con ordenamiento genérico (s)»— o como una Nota al pie de esa tabla que ind…

- H-251 · *media* · Tabla 3.10, columna «Dónde», p. 99 (PDF p.115) · 5 min
  **Dos filas de la Tabla 3.10 remiten a un lugar que no contiene todo lo que la fila afirma**
  <br>→ Cambiar el «Dónde» de la fila de intercambio de datos a «Sección 3.3; Subsección 3.6.1» y el de la fila de las fases a «Subsección 3.6.1; Figura 3.5».

- H-252 · *media* · Conclusiones, Objetivo específico 3, p. 103 (PDF p.119) · 15 min
  **El intercambio de datos (CSV/DXF) es parte del OE3 y criterio de la Tabla 3.10, y no aparece en ninguna conclusión**
  <br>→ Añadir una sola oración, al final del párrafo del OE3: «El modelo se exporta e importa en paquete CSV/ZIP sin pérdida de entidades y admite geometría en DXF de forma idempotente (Sección 3.3).» No duplicarla en el OE5: CRITERIOS.md pide una sola aparición por lugar canónico, y el OE5 ya remite a la…

- H-253 · *media* · Recomendaciones y trabajo futuro, pp. 108-109 (PDF pp.124-125) · 15 min
  **Dos de las ocho recomendaciones no se siguen de ninguna limitación de la lista anterior**
  <br>→ Cambiar la apertura por: «A partir de las limitaciones anteriores y de las fronteras que la Introducción fijó de antemano se plantean tres líneas de continuación, una por capítulo.» Y cerrar con: «De las tres líneas, las dos primeras amplían el software y la tercera amplía la evidencia que lo respa…

- H-238 · *media* · «Hipótesis», cláusula (a), p. 7 (PDF p.23) —la tercera afirmación cae en la p. 7, no en… · 15 min
  **La cláusula (a) exige cobertura de contenido, que no se sigue de la definición de trazabilidad dada tres páginas antes**
  <br>→ Añadir al final del párrafo de trazabilidad de la p. 3 una sola oración de remisión, sin desarrollar la operacionalización (que es canónica de §2.1.2): «Así entendida, la trazabilidad se mide por cobertura: las etapas expuestas sobre el modelo del usuario, las fases que comparten el lienzo y los co…

- H-353 · *baja* · §2.2.7 Módulos educativos, p. 67 (PDF p. 85) · 5 min
  **El requisito 4 (cobertura de contenido) es el único de los cinco que nunca se cita por su número al retomarse**
  <br>→ Añadir «(requisito 4)» al final de la oración sobre cobertura de contenido en §2.2.7, igual que se hace con los demás requisitos.


### B6 — Aparato de citas

> **Por qué aquí.** Sexto porque es independiente de todo lo anterior y mecánico: se hace con el fuente y el .bib abiertos, de un tirón. Empezar por los seis localizadores de Bishay, que es el único defecto de referencias que cualquiera puede comprobar abriendo la revista.

**Esfuerzo del bloque: 2 h** · 18 correcciones

#### PAT-11 — Atribuciones concretas sin localizador de página, y tres sin ninguna cita

*15 apariciones · 1,5 h*

**Acción.** Añadir localizador solo a las citas que sostienen una atribución concreta —son unas doce, y el autor ya tiene los localizadores en el resto del documento—. Dar entrada bibliográfica a ACI 318 o reformular sin nombrarla. Para 23,96, escribir «valor de uso extendido en la literatura de verificación (cf. [26, p. 28], que publica 23,965)». No tocar las remisiones generales: añadirles páginas sería una sobrecorrección.

#### Correcciones sueltas de este bloque

- **H-017** · *alta* · §1.2 «Fundamentos pedagógicos», p. 19 (PDF p.35) — 02_marco_teorico.tex L93 (ejemplo… · 30 min
  **Los seis localizadores de [16] Bishay caen fuera del rango de páginas que declara la entrada**
  <br>→ Los seis localizadores son coherentes entre si con una paginacion interna 1..21 (el maximo citado es 17 y el articulo tiene 21 paginas), lo que indica que se consulto un ejemplar paginado desde 1 (Early View o manuscrito aceptado). El autor debe (a) confirmar que ejemplar uso y (b) o bien convertir los seis localizadores con ese desplazamiento, una vez verificado pagina por pagina en el PDF consultado (p. 2 -> p. 1008; pp. 4-5 -> pp. 1010-1011; pp. 5-6 -> pp. 1011-1012; p. 13 -> p. 1019; p. 17 -> p. 1023), o bien declararlo en el .bib con una nota explicita del tipo «los localizadores corresponden a la paginacion del ejemplar Early View, cuya p. 1 equivale a la p. 1007 de la version final». Lo que NO debe hacerse es anadir una nota generica y dar el punto por cerrado: la lista seguiria mostrando 1007-1027 junto a un «p. 2», y la nota sola documenta la inconsistencia en lugar de resolverla.

- H-177 · *media* · Nota de la Tabla 3.7 «Tabla de cobertura de contenido» (la tabla empieza en p. 91 · 5 min
  **Cita en estilo autor-año (APA) dentro de un documento Vancouver, en la nota de la Tabla 3.7**
  <br>→ En 04_resultados.tex L320 sustituir «Códigos e ítems según las Tablas 1 y 2 de Pérez-Santiago y Campos (2023), traducidos por el autor» por «Códigos e ítems según las tablas 1 y 2 del consenso de expertos \autocite[pp.~1162-1163]{perezsantiago2023fem}, traducidos por el autor», que imprime «[3, pp.…

- H-179 · *media* · «Objeto de estudio y campo de acción», p. 3 (PDF p.19) — 01_introduccion.tex L17 y L21 · 2 h+
  **[8] Álvarez de Zayas, monografía irrecuperable, sostiene los cuatro pilares del marco metodológico**
  <br>→ No duplicar las cuatro definiciones con [24] Hernández-Sampieri ni con una obra de Álvarez de Zayas que el autor no tenga delante. «Objeto de estudio» y «campo de acción» en la acepción que usa el documento pertenecen a la tradición metodológica de Álvarez; Hernández-Sampieri no los define así, y c…

- H-180 · *media* · «Referencias bibliográficas», entrada [8], p. 111 (PDF p.127) · 15 min
  **La entrada [8] se compone como si fuera un artículo y con puntuación distinta del resto de la lista**
  <br>→ En referencias.bib, cambiar el tipo de @unpublished a @book y trasladar el pie de imprenta a sus campos propios: location = {[lugar desconocido]}, publisher = {[editorial desconocida]}, year = {[fecha desconocida]}, dejando en note solo la descripción del ejemplar («Monografía inédita de 80 páginas…

- H-181 · *media* · Introducción, «Estructura del documento», p. 11 (PDF p.27) · 15 min
  **La norma declarada en p. 11 atribuye a ICMJE/NLM rasgos que no son suyos**
  <br>→ Reescribir la frase de p. 11 así: «Las citas y la lista de referencias siguen el principio de la norma Vancouver —numeración arábiga por orden de primera mención, con el número entre corchetes y no en superíndice, para poder acompañarlo de la página citada—, en una adaptación a las convenciones tip…

- H-182 · *media* · «Referencias bibliográficas», entrada [26], p. 113 (PDF p.129) · 30 min
  **La única fuente publicada del caso de Cook es un preprint de arXiv sobre un elemento de cáscara**
  <br>→ Comprobar en Finite Elements in Analysis and Design si el preprint ya salió publicado; si es así, sustituir la entrada por la versión publicada (con volumen, páginas y DOI) y reajustar los localizadores p. 27 y p. 28. Si sigue inédito, añadir en §3.5, tras «obtienen su referencia por vía numérica»,…

- H-007 · *baja* · «Justificación», plano académico, p. 4 (PDF p.20) · 15 min
  **«La literatura... reporta que... favorecen la instrucción»: afirmación de efecto, sin ninguna cita**
  <br>→ Texto calibrado en **«Calibración de afirmaciones», H-007**.

- H-301 · *baja* · Referencias bibliograficas, entradas [8] y [26], p. 111 y p. 113 (PDF p. 127 y p. 129) · 30 min
  **Tratamiento tipografico distinto para dos fuentes igualmente no publicadas en revista**
  <br>→ Unificar el tratamiento del titulo para material no publicado formalmente (por ejemplo, ambas entre comillas y en redondo, reservando la cursiva a obras publicadas) ajustando el campo o el driver de biblatex para @unpublished/@online.

- H-326 · *baja* · «Referencias bibliográficas», entradas [22] y [23], p. 113 (PDF p.129) · 15 min
  **Campos opcionales desparejos entre entradas hermanas: DOI ausente en [22] y serie solo en [23]**
  <br>→ Añadir a la entrada salari2000mms el DOI del informe en OSTI (SAND2000-1444, doi 10.2172/759450 — comprobar en osti.gov antes de imprimirlo) con su url y urldate, igual que stimpson2007verdict. Suprimir el campo series de strang2008analysis, ya que ninguna otra entrada de la lista imprime serie.


### B7 — Legibilidad de las páginas que el tribunal lee de verdad

> **Por qué aquí.** Séptimo: primera de las pasadas de estilo. Se limita a Introducción, §3.8 y Conclusiones —partir las quince oraciones largas y los seis párrafos de 240+ palabras, sacar a lista las enumeraciones, poner al autor como sujeto— y se hace después de B1 para no partir dos veces la misma frase.

**Esfuerzo del bloque: 3 h** · 26 correcciones

#### PAT-02 — Oraciones por encima del tope de ~60 palabras que el propio autor fijó

*96 apariciones · 2 h*

**Acción.** Partir solo las que caen en lo que el tribunal lee con atención: objetivo general, hipótesis y cláusulas, cierre de §3.8, conclusiones por objetivo y los veredictos de §3.4 y §3.5. Son unas quince. Dejar las del capítulo 1 y de los anexos: partirlas todas es una pasada de cuatro horas con rendimiento decreciente.

#### PAT-03 — Párrafos de 200 a 390 palabras que encadenan cuatro o cinco asuntos

*17 apariciones · 1 h*

**Acción.** Partir en dos o tres los seis párrafos de más de 240 palabras, uno por asunto, sin reescribir el contenido. El de §3.4 se parte solo: datos del modelo / solución de referencia / protocolo de comparación.

#### PAT-05 — El impersonal oculta quién decidió, justo donde la decisión es el aporte

*11 apariciones · 45 min*

**Acción.** Poner al autor como sujeto en las once frases: «el autor fijó», «el autor adoptó», «el autor eligió». Es la corrección más barata del informe y la que más refuerza la defensa, porque convierte decisiones anónimas en criterios asumidos.

#### PAT-06 — Enumeraciones de cuatro o más elementos que siguen en prosa corrida

*27 apariciones · 1,5 h*

**Acción.** Sacar a lista las de la Introducción y las Conclusiones —unas doce— y dejar en prosa las del capítulo 1 y de los anexos, donde la enumeración es parte de una explicación continua y la lista la rompería.

#### Correcciones sueltas de este bloque

- H-030 · *media* · Introducción, «Estructura del documento», p. 10 (PDF p. 26) · 30 min
  **«Estructura del documento» no da ninguna guía de lectura al lector que no cursó el método**
  <br>→ Añadir el párrafo propuesto al final de «Estructura del documento», con dos correcciones: (a) suprimir del diagnóstico la afirmación de que el documento declara dos lectores, que el texto no sostiene, y justificar la adición por su encaje en el lugar canónico del recorrido que fija CRITERIOS.md; (b…

- H-047 · *media* · Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) · 15 min
  **Cuatro tasas de convergencia y «las dos normas del error» sin decir qué miden**
  <br>→ Reescribir: «arrojó las tasas de convergencia que la teoría predice para el desplazamiento —es decir, el ritmo al que el error se reduce al refinar la malla—: 2,00 en la norma del desplazamiento y 1,00 en la de su gradiente para el Q4, y 3,00 y 2,00 para el Q9 (Tabla 3.1).»

- H-109 · *media* · Resumen, p. ii (PDF p.2) · 15 min
  **El Resumen usa cinco veces «trazabilidad» y «verificabilidad» sin decir qué significan**
  <br>→ Insertar en el Resumen, tras la primera mención, una glosa de media línea: «…elevando la trazabilidad del análisis —poder seguir cada resultado hacia atrás hasta los datos del modelo— y su verificabilidad —poder comprobar cada magnitud contra un patrón independiente—.» No repetirla después dentro d…

- H-110 · *media* · §3.7 Interpretación de los resultados, p. 93 (PDF p.109) · 15 min
  **§3.7 no tiene párrafo de apertura y sus dos primeros subtítulos no anuncian su contenido**
  <br>→ Añadir una línea de apertura en §3.7: «Esta sección interpreta lo que los tres casos de estudio respaldan, qué límite encontró la propia batería de verificación, cómo queda EduFEM frente a los recursos existentes y qué limitaciones dejó a la vista el desarrollo.» Renombrar «3.7.1 Alcances» → «3.7.1…

- H-111 · *media* · Capítulo 2, p. 40 (PDF p.56) · 15 min
  **El título del capítulo 2 obliga al propio capítulo a desambiguar la palabra «modelo»**
  <br>→ Retitular el capítulo como «Diseño metodológico e implementación del software» y suprimir del primer párrafo la frase «La palabra \emph{modelo} tiene aquí dos acepciones que conviene separar», que deja de ser necesaria; conservar sin cambios la \label del capítulo.

- H-124 · *media* · §3.6.1, párrafo «Organización de la interfaz», p. 90 (PDF p.106) · 5 min
  **«Observado: 3 de 3» queda ambiguo tras una oración que habla de los tres casos de estudio**
  <br>→ Escribir: «Criterio: las tres fases sobre el mismo lienzo. Observado: las tres —pre-proceso, proceso y post-proceso—, comprobadas en cada uno de los tres casos de estudio. Se cumple.»

- H-125 · *media* · §3.7.4, p. 97 (PDF p.113) · 5 min
  **«limitan la aplicabilidad a casos de ingeniería más allá de los formativos» dice lo contrario de lo que quiere decir**
  <br>→ Escribir: «Esas restricciones privilegian la claridad sobre la generalidad, y dejan fuera del alcance de la herramienta los casos de ingeniería que exceden lo formativo.»

- H-123 · *media* · §3.6.3, p. 93 (PDF p.109) · 15 min
  **«el trabajo entre pares» aparece como límite declarado sin antecedente en ninguna parte de la tesis**
  <br>→ Borrar la oración y reescribir el cierre con un solo límite: «Los cuatro principios tienen al menos una decisión de diseño que los concreta, y esa decisión es comprobable en el software. Queda a la vista un límite, y se declara: las destrezas de mallado se ejercitan sobre secuencias de mallas que e…

- H-290 · *baja* · §2.1.2, p. 44 (PDF p.60) · 5 min
  **Relativa ambigua: «los expertos que tienen instrumento en el software»**
  <br>→ Reescribir: «Se mide contando las etapas que el software expone, las fases que comparten el lienzo y, del contenido que los expertos exigen, los ítems que tienen instrumento en el software.»


### B8 — Glosas en la primera aparición

> **Por qué aquí.** Octavo porque, hechos B1 y B7, las frases de entrada ya están en su forma definitiva y la glosa se inserta sin volver a moverla. Es la corrección que más hace por el segundo lector declarado.

**Esfuerzo del bloque: 2 h** · 19 correcciones

#### PAT-01 — Términos técnicos usados muchas páginas antes de su glosa, o nunca glosados

*16 apariciones · 2 h*

**Acción.** Una sola pasada por las primeras apariciones: media línea entre rayas o con «es decir» para lienzo, bloqueo por cortante, soluciones manufacturadas, ejemplo canónico, isoparamétrico, guion, GDL, punto de Gauss, biyectivo, restricciones de Dirichlet no homogéneas, inyección de fórmulas y verificación de solución. En el Resumen bastan tres. No crear un glosario nuevo: la Nomenclatura ya existe y solo hay que remitir a ella.

#### Correcciones sueltas de este bloque

- H-029 · *media* · §1.8, p. 26 (PDF p. 42) · 15 min
  **La Ecuación 1.15 (rigidez elemental) entra sin decir qué mide ke ni por qué B^T D B**
  <br>→ No sustituir la frase introductoria por la analogía de la barra: ya está en §1.3, p. 20, y repetirla infringe la regla de lugar canónico. Ampliar la frase actual con la remisión y con la lectura del producto, que es lo único que falta: «La matriz de rigidez de un elemento es, para un trozo de chapa…

- H-032 · *media* · §1.3, p. 21 (PDF p. 37) · 15 min
  **La Ecuación 1.2 (trabajos virtuales) no se lee nunca en palabras: solo se nombran sus símbolos**
  <br>→ Añadir tras la Ecuación 1.2 solo la lectura de los dos miembros, sin repetir lo que el párrafo ya dice: «En palabras, la Ecuación 1.2 iguala dos trabajos: el miembro izquierdo es el que realizan las tensiones internas cuando el sólido sufre una deformación virtual cualquiera, y el derecho, el que r…

- H-035 · *media* · §1.4, p. 22 (PDF p. 38) · 15 min
  **La matriz constitutiva D (Ecuaciones 1.4 y 1.5) entra sin una frase que diga qué mide**
  <br>→ Insertar tras «ligadas por la ley constitutiva σ = D ε»: «La matriz constitutiva D es la única pieza del cálculo en la que entra el material: traduce deformaciones en tensiones y, en un material elástico, lineal e isótropo, queda determinada por solo dos números, el módulo de elasticidad E y el coe…

- H-043 · *media* · §2.1.6, Tabla 2.4, fila «Soluciones manufacturadas», p. 52 (PDF p.68) · 15 min
  **El único criterio numérico sin su valor: «Teórica ±0,5» no dice cuál es la tasa teórica ni dónde se define**
  <br>→ Cambiar la celda «Magnitud» por: «Tasa de convergencia del desplazamiento en la norma L² y en la seminorma H¹ (§1.13), cuatro configuraciones» y la celda «Umbral» por: «Tasa teórica ±0,5 (L²: 2 en Q4 y 3 en Q9; H¹: 1 en Q4 y 2 en Q9)».


### B9 — Redundancia: dejar la aparición canónica

> **Por qué aquí.** Noveno: podar es lo último que se hace sobre el texto, cuando ya se sabe cuál de las apariciones quedó mejor escrita tras B1-B8. Borrar antes obligaría a reescribir lo que se conserva.

**Esfuerzo del bloque: 2 h** · 26 correcciones

#### PAT-07 — Piezas del software reexplicadas desde cero entre el cuerpo y el Anexo B

*12 apariciones · 1,5 h*

**Acción.** Dejar la aparición canónica del cuerpo y, en las demás, una línea con \autoref. Excepción deliberada: el Anexo B es un manual de uso y debe poder leerse solo, así que allí se conserva la descripción operativa y se recorta únicamente la teoría ya dada en §2.2.

#### PAT-08 — Marco y método reexpuestos desde cero en el capítulo 3 y en las conclusiones

*18 apariciones · 2 h*

**Acción.** Regla única: la primera aparición desarrolla, las siguientes remiten. Recortar §3.2 a una frase con \autoref a §1.13; dejar la anécdota de extrapolación solo en §3.7.2 y una línea en Aportes; enumerar los cinco requisitos completos solo en §1.1 y citarlos por número en los otros tres sitios.


### B10 — Anexo G

> **Por qué aquí.** Décimo y en bloque propio porque toca un fuente distinto (07_anexo_memoria.tex y el generador de figuras) y porque parte de sus arreglos —unidades, precisión, figuras— se regeneran con un script. Empezar por el sistema de unidades: cinco minutos que evitan la observación más incómoda que un ingeniero civil puede hacer sobre este anexo.

**Esfuerzo del bloque: 2,5 h** · 25 correcciones

#### PAT-12 — El Anexo G, pieza que sostiene el argumento central, se presenta con descuido

*18 apariciones · 2,5 h*

**Acción.** Cambiar el ejemplo de unidades a kgf y cm y decir en una línea que los valores corresponden a un hormigón; poner unidades en los encabezados de las seis tablas; fijar la precisión por magnitud; numerar la tabla de reacciones; regenerar las tres figuras con tildes, coma decimal y los apoyos completos; y añadir el chequeo global de equilibrio que los datos ya permiten.


### B11 — Uniformidad de cifras, símbolos y nomenclatura

> **Por qué aquí.** Undécimo: es una pasada de buscar y reemplazar sobre un texto que ya no va a cambiar de contenido. Hacerla antes sería rehacerla.

**Esfuerzo del bloque: 2 h** · 15 correcciones

#### PAT-10 — Símbolos, precisión y formato numérico desparejos, y Nomenclatura incompleta

*45 apariciones · 2 h*

**Acción.** Pasada de uniformización sobre tablas y prosa: un nombre y un símbolo por magnitud, separador de miles siempre o nunca, mismo número de decimales dentro de cada tabla. Completar la Nomenclatura con u_y, b, H, q, JSON y ZIP, advertir los dos sentidos de L y borrar κ₂.


### B12 — Cosmética agrupada

> **Por qué aquí.** Al final y todo junto, en una sola sesión con el PDF recompilado al lado: índices, leyendas, flotantes, tildes en figuras, dobles puntos, filetes. Ninguno cambia una idea y todos se ven de golpe en el PDF terminado.

**Esfuerzo del bloque: 2,5 h** · 49 correcciones

#### PAT-04 — Muletillas de apertura y conectores únicos repetidos hasta la saturación

*89 apariciones · 1,5 h*

**Acción.** Sustitución con control manual: alternar «de modo que» con «así», «por eso», «con lo cual» o punto y seguido en la mitad de los casos; convertir «Conviene decir qué prueba…» en «Ese resultado prueba… y no prueba…»; eliminar «de forma/manera X» por el adverbio o por la reformulación directa. No hace falta llegar a cero.

#### PAT-13 — Los índices reproducen leyendas completas y omiten quince secciones

*34 apariciones · 1 h*

**Acción.** Poner título breve en el argumento opcional de \caption[…] de las diecinueve figuras y tablas de los anexos, y añadir \addcontentsline para las quince secciones sin numerar y para los dos índices. Es mecánico y se hace de una vez.

#### Correcciones sueltas de este bloque

- H-027 · *media* · §1.6 a §1.13, pp. 25-39 (PDF pp. 41-55) · 2 h+
  **Quince páginas de formalismo (§1.6-§1.13) sin una sola figura ni tabla de apoyo**
  <br>→ Corregir primero el diagnóstico: el tramo sin apoyo visual es §1.6-§1.13, pp. 25-39, no las treinta y dos páginas hasta la Figura 2.1. Ejecutar de inmediato las dos remisiones del punto (3), que son baratas y están verificadas: en §1.8, p. 27, tras «es la que adopta el motor (\autoref{sec:motor})»,…

- H-036 · *media* · §2.2.6 «Pre-proceso interactivo», pp. 63-67 (PDF pp. 79-83) · 30 min
  **§2.2.6 acumula decisiones de implementación sin el cierre de propósito que tienen sus hermanas**
  <br>→ Añadir al final de §2.2.6: «Todo el pre-proceso sirve a una misma condición: que el modelo sobre el que después se expone el procedimiento sea válido y sea del propio usuario. El deshacer por instantáneas permite explorar el modelo sin riesgo de arruinarlo; el comprobador de salud impide que un dat…

- H-054 · *media* · Anexo C, §§C.1-C.4, pp. 133-136 (PDF pp. 149-152) · 15 min
  **Los listados del Anexo C no remiten con \autoref a la ecuación concreta del Capítulo 1 que implementan**
  <br>→ Añadir \autoref{eq:N-q4} y \autoref{eq:N-q9} en la introducción de C.1, \autoref{eq:matriz-B} en C.2, \autoref{eq:D-tension-plana} y \autoref{eq:D-deformacion-plana} en C.3, y \autoref{eq:ensamblaje} en C.4.

- H-055 · *media* · Anexo F, Tabla F.1 p. 159 (PDF p. 175) y Tabla F.2 p. 161 (PDF p. 177) · 15 min
  **El campo element_id de surface_loads (JSON) no tiene columna equivalente en el CSV, sin explicarlo**
  <br>→ Añadir una frase en F.2 que explique cómo determina el importador el elemento de una carga superficial leída del CSV cuando falta element_id (p. ej., por la arista compartida entre node_start y node_end, análogamente a como F.3 explica la deduplicación de nodos del DXF).

- H-061 · *media* · §2.1.1, Tabla 2.1, p. 41 (PDF p.57) · 15 min
  **La Tabla 2.1 se titula «Las seis actividades» y tiene siete filas**
  <br>→ Separar el elemento de las actividades. Cambiar la leyenda a: «Las seis actividades del método de la ciencia del diseño [12, pp. 52-56] y la base de conocimiento sobre la que se apoyan: qué es cada una en este trabajo, dónde se desarrolla y a qué objetivo específico (OE) responde. La fila «Base de…

- H-062 · *media* · §2.1.2, Tabla 2.2, p. 45 (PDF p.61) · 15 min
  **La leyenda de la Tabla 2.2 no explica la raya que separa las variables de las magnitudes del experimento**
  <br>→ Ampliar la leyenda: «Operacionalización de las variables de la investigación: dimensiones, indicadores con que se mide cada una e instrumento que produce el dato. Sobre la raya, las tres variables del problema científico —independiente, dependiente e interviniente—. Bajo la raya, las magnitudes del…

- H-065 · *media* · Figura 3.5, p. 88 (PDF p.104) · 1 h
  **La Figura 3.5, única evidencia del criterio «3 de 3 fases sobre el mismo lienzo», es ilegible en papel**
  <br>→ No cambiar el ancho en LaTeX (ya es 0,95\linewidth): rehacer el montaje fig_fases_lienzo.png recortando cada captura a la región pertinente y con el lienzo ampliado, de modo que las tres ocupen el ancho completo del montaje y los índices de GDL, los rótulos de nodo y la barra de estado alcancen al…

- H-067 · *media* · Tabla 3.9, p. 98 (PDF p.114) · 15 min
  **La Tabla 3.9 lleva su nota metodológica dentro de la leyenda y usa un filete distinto al resto**
  <br>→ Dejar en la leyenda solo «Tiempo de ensamblaje y de solución del sistema, y memoria que ocupa la matriz de rigidez en formato denso frente al disperso, para la membrana de Cook con elementos Q9 a refinamientos crecientes.» y pasar el resto a un bloque «Nota.» bajo la tabla; sustituir los filetes po…

- H-049 · *media* · Anexo B, Figura B.6, p. 126 (PDF p.142) · 15 min
  **La leyenda de la Figura B.6 (modulo M0) no traduce el color a estado de calidad**
  <br>→ Agregar a la leyenda de la Figura B.6 la equivalencia color-estado, por ejemplo verde bueno, naranja aceptable, rojo malo, segun los cortes de la Tabla 2.7.

- H-050 · *media* · Anexo B, Figura B.11, p. 129 (PDF p.145) · 30 min
  **La matriz k_e de la Figura B.11 (modulo M5) esta al limite de la legibilidad impresa**
  <br>→ Recortar la captura para mostrar el panel de la matriz a mayor escala, o superponer la matriz tipeada en LaTeX junto a la captura, como ya se hace con las matrices del Anexo G.

- H-218 · *media* · §1.8, p. 26 (PDF p.42) · 1 h
  **Espaciado vertical irregular alrededor de flotantes sueltos (huecos en blanco no justificados)**
  <br>→ Revisar la colocación de estos cuatro flotantes/bloques (probar [!t], \FloatBarrier o \enlargethispage puntual en vez de dejar que el espacio se reparta como relleno vertical); si el efecto viene de \flushbottom, evaluar \raggedbottom para las páginas de solo-flotante y verificar que no rompa otras…

- H-220 · *media* · Anexo C.4, p. 136 (PDF p. 152): la página trae solo la línea «return coo_matrix(...)» y… · 1 h
  **Páginas con la mitad o más en blanco por colocación de flotantes en los Anexos C y D**
  <br>→ Reflujar el listado de C.4 (mover 2-3 líneas para que 'return' no quede solo en la página siguiente) y revisar la colocación de floats en D.2-D.4 (por ejemplo forzando [!htb] o compactando el texto entre Tabla D.2/D.3 y alrededor de la Figura D.3) para que ninguna página quede con más de un tercio…

- H-066 · *baja* · §3.7.4, p. 97-99 (PDF p.113-115) · 1 h
  **«Limitaciones observadas» dedica dos de sus tres páginas a exhibir el desempeño del motor**
  <br>→ Mover la Tabla 3.9 y los dos párrafos que la comentan a una subsección propia, «Desempeño del solucionador», colocada antes de las limitaciones, y dejar en «Limitaciones observadas» solo la oración que enuncia el límite real: «La limitación de escalabilidad no está en el almacenamiento ni en el ran…

- H-257 · *baja* · Indice general, p. v (PDF p.6) · 5 min
  **La entrada del Anexo E en el índice general choca contra el número de página**
  <br>→ Acortar el titulo del Anexo E en el indice (por ejemplo Validacion en SAP2000 y Timoshenko) o forzar el punteado de relleno en esa entrada.

- H-260 · *baja* · Material preliminar, entre la portada y el Resumen (PDF p.1-2) · 15 min
  **El PDF compilado no incluye la declaración de originalidad ni los agradecimientos**
  <br>→ Antes de la entrega final: descomentar la línea 52 de main_final.tex y personalizar la dedicatoria y los agradecimientos de capitulos_final/00_preliminares.tex. Recompilar y volver a verificar la paginación romana, que se correrá tres o cuatro páginas.

- H-261 · *baja* · Referencias bibliograficas, entrada [15], p. 112 (PDF p. 128) · 30 min
  **Orden confuso de subtitulo y volumen en la entrada [15] (Onate)**
  <br>→ Ajustar el renderizado de esta entrada (o el campo volumes/subtitle) para que quede '... Linear Statics, Vol. 1: Basis and Solids. Barcelona: CIMNE, 2009.', dejando claro que 'Basis and Solids' es el volumen 1.

- H-262 · *baja* · D.1, p. 137 (PDF p. 153) · 5 min
  **La etiqueta sec:vyv-reproducibilidad (D.1) no se referencia con \autoref desde ningún lugar**
  <br>→ Usar \autoref{sec:vyv-reproducibilidad} donde el Capítulo 3 o el Anexo A mencionen específicamente la reproducibilidad, en vez de \autoref{anexo:vyv} genérico, o eliminar la etiqueta si no se le va a dar uso.

- H-268 · *baja* · §2.1.6, Tabla 2.4 (continuación), p. 52 (PDF p.68) · 15 min
  **En la continuación de la Tabla 2.4 la fila «Intercambio de datos» queda sin su rótulo de cláusula**
  <br>→ Añadir al \endhead de la longtable, tras el \midrule, una fila de continuación: \multicolumn{5}{@{}l}{\emph{Cláusula (a): trazabilidad (continuación)}} \\ ; o, más simple, forzar el corte de página después de la fila «Intercambio de datos» con \pagebreak para que el bloque de la cláusula (a) quede…

- H-269 · *baja* · §2.1.6, Tabla 2.4, p. 52 (PDF p.68) · 5 min
  **«Tres puntos de control» se usa como criterio sin definirlos ni remitir a donde se definen**
  <br>→ Añadir la remisión en la celda: «…en los tres puntos de control de la Sección 3.4» y, en la cuarta precisión que se propone añadir tras la tabla, nombrarlos: «los tres puntos de control son uno en la fibra extrema del centro del vano y dos interiores».

- H-270 · *baja* · §2.1.2, p. 43 → Tabla 2.2 en p. 45 (PDF p.59 → PDF p.61) · 15 min
  **La Tabla 2.2 se llama en la p.43 y aparece dos páginas después**
  <br>→ Mover la llamada a la Tabla 2.2 al final de la subsección, tras el párrafo «Las magnitudes del experimento numérico no son variables del problema científico…», cerrando con «La Tabla 2.2 reúne la operacionalización completa». La frase de apertura de §2.1.2 pasa a ser: «Operacionalizar una variable…

- H-271 · *baja* · §2.2.2 (sec:stack), p. 57 y §2.2.3 (sec:arquitectura), p. 59 (PDF p. 73 y 75) · 15 min
  **Las secciones «Tecnologías empleadas» y «Arquitectura por capas» tienen label pero ningún otro capítulo las referencia**
  <br>→ Agregar un \autoref a sec:arquitectura (p. ej. en la Subsección 3.3, al hablar de ProjectModel) y a sec:stack donde corresponda, o dejarlas sin referencia si de verdad no hace falta retomarlas.

- H-272 · *baja* · §3.6.1, p. 87-89 (PDF p.103-105) · 15 min
  **La Tabla 3.6 se menciona antes que la Figura 3.5 pero se imprime después**
  <br>→ Adelantar el entorno de la Tabla 3.6 al párrafo que la llama, de modo que quede antes del entorno de la Figura 3.5 en el fuente y se impriman en el orden de mención.

- H-273 · *baja* · §3.7, p. 93 (PDF p.109) · 15 min
  **El título de §3.7 queda pegado al de §3.7.1 sin texto intermedio**
  <br>→ Insertar una entradilla de dos oraciones: «Esta sección interpreta lo que las tres baterías permiten afirmar y lo que no. Recorre primero el alcance de la exactitud comprobada, después un episodio que acota lo que una verificación por convergencia puede probar, la posición de EduFEM frente a los re…

- H-286 · *baja* · §1.2 Principios que orientan la exposición del procedimiento, pp. 19-20 (PDF pp. 35-36) · 30 min
  **§1.2 presenta cuatro decisiones de diseño del autor como derivaciones lógicas de la literatura**
  <br>→ Reducir la intervención a UNA sola aparición, la primera y la más fuerte (02_marco_teorico.tex:89): «De aquí se deriva que EduFEM exponga…» → «Sobre este principio el autor apoyó la decisión de que EduFEM exponga cada matriz sobre el modelo, en las mismas fases en que el análisis profesional las pr…

- H-196 · *baja* · §2.1.1, p. 42 (PDF p. 58) · 30 min
  **¿Cómo sostiene que el software es «educativo» si no midió a ningún estudiante?**
  <br>→ Agregar una definición operativa breve. En la Introducción, al final del primer párrafo (p. 1), o en §2.2.1 junto a los cinco requisitos (p. 54), insertar: «En este documento, software educativo designa un programa cuyo propósito de diseño es exponer el procedimiento de cálculo además de entregar s…

- H-203 · *baja* · §2.1.1, «Unidad de análisis y versión evaluada», p. 43 (PDF p. 59) · 1 h
  **¿Cómo se replica este trabajo si en dos años el software ya no compila?**
  <br>→ Dos líneas de acción. (1) Añadir al Anexo D.1, tras el primer párrafo, una oración: «Los archivos CSV con los datos crudos de todas las tablas y figuras del Capítulo 3 y de este anexo se distribuyen junto con el documento, de modo que las cifras reportadas son verificables aunque el código no vuelv…

- H-204 · *baja* · Conclusiones, «Recomendaciones», «Guía de uso en la cátedra», p. 109 (PDF p. 125) · 2 h+
  **¿Quién va a usar esto en la Carrera, y con qué compromiso?**
  <br>→ Antes de la defensa, hacer dos cosas concretas y poder nombrarlas. (1) Entregar formalmente el instalador y el manual del Anexo B a la Dirección de Carrera o al docente de la asignatura, y guardar la constancia. (2) Escribir las tres prácticas que la recomendación de la página 109 ya enumera —el ej…

- H-338 · *baja* · §2.2.9, p. 72 (PDF p.88) · 15 min
  **Página casi vacía por el salto obligatorio de capítulo (una sola oración suelta en la parte superior)**
  <br>→ Opcional: alargar en dos o tres líneas el párrafo de cierre de la Subsección 2.2.9 para que la página no quede con una sola oración, o dejarlo así si se acepta como artefacto normal de salto de capítulo.

- H-340 · *baja* · Resumen, p. i (PDF p.2) · 30 min
  **El Resumen se aparta de APA 7 en tres puntos verificables sobre el PDF**
  <br>→ Anteponer \noindent al párrafo del resumen; cambiar \textbf{Palabras clave:} por \textit{Palabras clave:} precedido de un \vspace{\baselineskip} y con sangría de 1,27 cm. Sobre las 280 palabras: primero aplicar las reformulaciones de calibración de este informe y solo después recortar, comprimiendo…

- H-342 · *baja* · «Alcance y limitaciones», p. 9 (PDF p.25) · 15 min
  **La coma cumple dos funciones distintas dentro del mismo corchete de cita**
  <br>→ Uniformar a punto y coma como único separador entre referencias cuando haya más de una en el corchete, también sin localizador: «[1; 2]», «[4; 5]». Alternativa de coste cero: dejarlo como está y añadir una línea a «Normas de citación y presentación» que explique que el punto y coma separa referenci…

- H-343 · *baja* · §2.1.1, p. 41 (PDF p.57) · 5 min
  **Los tres encabezados de párrafo de §2.1.1 salen impresos con dos puntos seguidos**
  <br>→ Quitar el punto del argumento en los tres casos: \paragraph{Método}, \paragraph{Modelo de simulación numérica}, \paragraph{Unidad de análisis y versión evaluada}. Verificar también \paragraph{Alcance de esta revisión.} (02_marco_teorico.tex L15) y los tres de 04_resultados.tex, que tienen el mismo…

- H-344 · *baja* · Figuras 3.1(a), 3.1(b) y 3.2, p. 78 (PDF p.94) · 15 min
  **El rótulo del eje de las figuras de convergencia va sin tilde: «tamaño caracteristico»**
  <br>→ Corregir la cadena en tests/vv_mms.py línea 270 a «h (tamaño característico)», regenerar las tres figuras y recompilar; revisar de paso las figuras homólogas del Anexo D.

- H-345 · *baja* · Figura 3.3, p. 83 (PDF p.99) · 15 min
  **La Figura 3.3 muestra las reacciones con punto decimal, contra la coma del documento**
  <br>→ Si el formateador del software admite locale, regenerar la captura con coma decimal; si no, añadir a la leyenda: «Las etiquetas de la captura conservan el punto decimal del programa.» Conviene señalar además que 35 000 + 35 000 = 70 000 kgf, que es la comprobación de equilibrio del texto.

- H-346 · *baja* · p. 78 (PDF p.94) · 30 min
  **La página de las figuras de convergencia queda con una franja en blanco de un cuarto de página**
  <br>→ Dar a la Figura 3.1 el ancho completo con los dos paneles a 0,48\linewidth y subir el tamaño de fuente de los ejes en el guion, o intercalar entre ambas figuras el párrafo que las llama.

- H-347 · *baja* · §3.6.1, p. 87 y p. 90 (PDF p.103 y p.106) · 5 min
  **Punto doble al final de los tres títulos de párrafo de §3.6.1**
  <br>→ Quitar el punto final del argumento de \paragraph en las tres apariciones de 04_resultados.tex (líneas 265, 271 y 273) y en las cuatro restantes del documento (02_marco_teorico.tex «Alcance de esta revisión.»; 02b_diseno_metodologico.tex «Método.», «Modelo de simulación numérica.», «Unidad de análi…

- H-348 · *baja* · §3.8, p. 101 (PDF p.117) · 5 min
  **Discordancia «las Subsección 3.6.1 y Subsección 3.6.2» por doble \autoref tras artículo plural**
  <br>→ Escribir «…y con la cobertura que reportan la \autoref{sec:cobertura-canal} y la \autoref{sec:contenido-didactico}».

- H-349 · *baja* · §3.6.1, p. 90 (PDF p.106) · 5 min
  **Ruta de archivo partida por el guion bajo sin señal de continuación**
  <br>→ Envolver la ruta con \mbox{} o escribirla con \path{tests/test_memoria_calculo.py} para que no se parta, como ya ocurre con \texttt{tests/bench\_timing.py} en la Tabla 3.9.


### B13 — Reserva: correcciones que no encajan en ningún bloque anterior

> **Por qué aquí.** Son correcciones independientes entre sí, de severidad media o baja, que no comparten archivo ni pasada con ningún otro bloque. Se listan para que no se pierda ninguna: atiéndelas sueltas cuando toques esa sección por otro motivo.

**Esfuerzo del bloque: 2–3 h** · 28 correcciones

- H-034 · *media* · §1.12, p. 35 (PDF p. 51) · 1 h
  **Tres páginas del capítulo 1 apilan de nueve a dieciséis símbolos nuevos cada una**
  <br>→ Partir la página en dos bloques y anteponer al segundo esta frase: «Las dos métricas anteriores bastan al comprobador de salud. El estado global que el programa muestra —bueno, aceptable o malo— se apoya, en cambio, en cuatro índices, porque un elemento puede fallar de cuatro maneras distintas: puede tener ángulos malos, puede estirarse de forma desigual de un extremo al otro, puede ser demasiado alargado y puede ser trapezoidal. Los dos primeros índices ya están definidos; los dos últimos se construyen sobre tres…

- H-008 · *media* · §1.1, Tabla 1.1, p. 16-17 (PDF p. 32-33) · 30 min
  **La Tabla 1.1 hace juicios de calidad didáctica que el propio texto promete no hacer para 2 de sus 6 columnas**
  <br>→ No poner rayas en esas filas: dejar «Procedimiento completo» o «Lectura de la respuesta» sin evaluar para el software comercial borraría justamente el contraste que la sección construye. Reescribir la frase de restricción (02_marco_teorico.tex L21) para que describa lo que la tabla hace, p. ej.: «Para estas dos categorías, las celdas de la Tabla 1.1 caracterizan la categoría a partir de lo que su naturaleza y su documentación declaran —interfaz, licencia, requisitos de ejecución, exposición del cálculo intermedio…

- H-070 · *media* · §2.2.3 «Motor de cálculo», p. 63 (PDF p.79) · 5 min
  **«Ningún resultado procede de un elemento cuya geometría invalide el mapeo» contradice lo dicho una página antes**
  <br>→ Sustituir por: «el umbral protege la verificabilidad, porque descarta antes de ensamblar los elementos cuya geometría invalida el mapeo en los puntos donde los tres controles lo evalúan». Preferir esta forma a la propuesta: «con el alcance que se acaba de declarar» es una remisión vaga y deja la frase apoyada en un antecedente que el lector debe reconstruir.

- H-078 · *media* · Introducción, «Planteamiento del problema», p. 2-3 (PDF p.18-19) · 15 min
  **Premisa central sobre la práctica profesional enunciada dos veces sin ninguna fuente**
  <br>→ Sustituir por: «Es lo que persigue la memoria de cálculo en la práctica profesional: un documento que permite a un revisor seguir el procedimiento y comprobarlo.» Si el autor dispone de una fuente normativa o de un manual de práctica que lo sostenga, citarla con localizador de página en esta misma oración y conservar entonces el verbo «sostiene».

- H-080 · *media* · Hipótesis, p. 6 (PDF p. 22) · 30 min
  **La hipótesis afirma «mejorar» y «elevando» sin línea de base medida, y nunca se declara**
  <br>→ El párrafo de cinco líneas que se propone repite lo que §2.1.2 ya dice y roza la regla de CRITERIOS.md de explicar cada cosa una sola vez. Sustituirlo por una sola oración al final del penúltimo párrafo de §3.8, antes de «Queda así respondido el problema científico»: «El nivel de partida de la variable independiente no se midió con estos mismos indicadores: se caracteriza documentalmente en la \autoref{tab:comparativa}, según se declara en la \autoref{sec:variables-met}. Lo que las cifras de este capítulo establec…

- H-081 · *media* · OE5, p. 6 (PDF p. 22) y PI-1, p. 7 (PDF p. 23) —las dos apariciones de «la literatura… · 30 min
  **«La literatura especializada exige» atribuye a toda una disciplina lo que reporta un solo estudio**
  <br>→ Sustituir en las SEIS apariciones es excesivo y rompería la regla de oraciones de hasta ~60 palabras de CRITERIOS.md. Corregir solo las dos que dicen «la literatura especializada», que son las que generalizan. En el OE5: «…la cobertura del procedimiento de cálculo y del contenido que un consenso publicado de expertos califica como necesario para el egresado, junto con los resultados de la verificación, contra los criterios de aceptación fijados de antemano, para establecer si el análisis resulta trazable y verific…

- H-091 · *media* · Encabezado del Anexo G, p. 164 (PDF p.180) · 5 min
  **«Ejemplo canónico de validación» contradice al Capítulo 2, que dice que ese ejemplo no mide exactitud**
  <br>→ En el Anexo G: «...el contenido de la Memoria de Calculo que EduFEM genera para el ejemplo canonico de trazabilidad —nueve nodos, cuatro elementos Q4, tension plana—, el caso sobre el que se demuestra que la memoria puede rehacerse a mano (Subseccion 2.1.3).» En el Anexo B, suprimir «de validacion» y dejar «sobre el ejemplo canonico». Comprobar de paso que ningun otro punto adjetive «de validacion» a este caso.

- H-093 · *media* · «Planteamiento del problema», p. 2 (PDF p.18) · 5 min
  **«Ninguno reúne» se apoya en celdas «No consta», que la nota de la Tabla 1.1 dice que no implican ausencia**
  <br>→ Cambiar el verbo en la Introducción: «ninguno de los recursos revisados documenta a la vez los tres atributos», o conservar «reúne» añadiendo «según las publicaciones consultadas». La frase de la p. 4 —«Esta capacidad no se documenta en los antecedentes de software educativo revisados»— ya está bien calibrada y sirve de modelo.

- H-094 · *media* · §1.13 Verificación y validación, p. 36 (PDF p. 52) · 15 min
  **«Acepción corriente en la práctica del MEF» afirmada sin cita, justo en la definición canónica de «validación»**
  <br>→ No usar la reformulación propuesta: «habitual en trabajos de verificación y validación en el MEF que comparan contra soluciones analíticas y software comercial» es la MISMA generalización sin respaldo, solo más larga, y añade un «El autor adopta» que CRITERIOS.md reserva a decisiones de diseño experimental. Suprimir la afirmación de currencia y dejar la convención como lo que es, una estipulación del documento. En `capitulos_final/02_marco_teorico.tex:460` reemplazar «Es la acepción corriente en la práctica del ME…

- H-099 · *media* · Leyenda de la Tabla 3.7, p. 91 (PDF p.107) · 15 min
  **«demuestra» y «se cumple por construcción» infringen la tabla de verbos por tipo de evidencia**
  <br>→ En la leyenda de la Tabla 3.7 y en §3.6.2 cambiar «que lo demuestra» por «que lo respalda»; en §3.6.1 escribir «…y esa coincidencia queda garantizada por construcción: ambos usan las mismas funciones (Subsección 2.1.5)».

- H-101 · *media* · Limitaciones, último ítem, p. 108 (PDF p.124) · 15 min
  **«su costo en memoria […] crece más que linealmente»: la Tabla 3.9 mide lo contrario**
  <br>→ Reescribir el ítem separando lo medido de lo no medido: «El solucionador es directo (Subsección 2.2.5). Es adecuado para los tamaños de modelo de un contexto educativo y para las mallas de decenas de miles de grados de libertad que mide la Tabla 3.9, donde el almacenamiento disperso de K crece de forma prácticamente lineal. Su límite está en el extremo de las mallas muy grandes: el tiempo de solución crece más rápido que el de ensamblaje a medida que la factorización se vuelve dominante (Subsección 3.7.3). La memo…

- H-137 · *media* · Anexo E, p. 149 (PDF p. 165) · 15 min
  **σx de SAP2000 en los puntos A y C no coincide entre la Tabla 3.2 (Cap. 3) y la captura del Anexo E**
  <br>→ Releer el valor exacto que muestra SAP2000 para los puntos A y C y unificar la cifra entre la Tabla 3.2 y la anotación de la captura del Anexo E, usando el punto B (que sí coincide) como control de que el resto de las cifras del anexo son correctas.

- H-140 · *media* · «Planteamiento del problema», p. 2 (PDF p.18) · 15 min
  **El vacío del estado del arte son «tres atributos» en la Introducción y «ocho» en la Sección 1.1**
  <br>→ Uniformar desde la Introducción: «Como muestra la Tabla 1.1, ninguno de los recursos revisados documenta a la vez los ocho atributos que enumera la Sección 1.1; tres de ellos definen el vacío que este trabajo aborda: la exposición del procedimiento de cálculo completo sobre el modelo del usuario, una memoria de cálculo reproducible a mano y una verificación y validación publicada junto con la herramienta.» Usar además el mismo rótulo del atributo en los dos lugares: hoy es «memoria de cálculo reproducible a mano»…

- H-195 · *media* · Introducción, «Hipótesis y preguntas de investigación», p. 6 (PDF p. 22) · 1 h
  **La hipótesis dice «elevando la trazabilidad»: ¿elevándola respecto de qué medición previa?**
  <br>→ No agregar a la Tabla 1.1 ni a la Tabla 3.6 una columna con cifras sobre productos que no se examinaron: contradiría la regla de §1.1 (p. 14) de dejar sin evaluar los atributos que exigirían examinar cada producto. En su lugar, una sola oración en §2.1.2, tras «El nivel de caja negra es el de referencia y se documenta con la matriz de atributos de la Tabla 1.1»: «Ese nivel se caracteriza por ausencia de los atributos, no por una medida: ninguno de los recursos revisados expone las matrices intermedias sobre el mod…

- H-197 · *media* · Introducción, «Alcance y limitaciones», pp. 8-9 (PDF pp. 24-25), con la enumeración en la… · 30 min
  **Usted ofrece el software para presas, muros y túneles, pero nunca validó deformación plana contra nada externo**
  <br>→ En el párrafo del Alcance (p. 8), añadir un inciso que remita al límite desde la primera mención: «...donde una rebanada representa todo el sólido; la verificación de ese estado se realizó con soluciones manufacturadas, y el contraste con referencias externas quedó restringido a la tensión plana (véase Limitaciones).» Respuesta oral: «La deformación plana no quedó sin verificar: se verificó con soluciones manufacturadas, en las cuatro configuraciones, incluida la malla distorsionada, y con las mismas tasas que la…

- H-198 · *media* · §3.7.2, p. 96 (PDF p. 112) · 1 h
  **Usted encontró un error en su propio software. ¿Cuántos más puede haber?**
  <br>→ Agregar al Anexo D.1, junto a la Tabla D.1, dos datos objetivos y verificables contra el repositorio: el número de guiones de prueba de la batería y, en una columna, los componentes del motor que cada uno ejercita. Tomar ambos del contenido real de la carpeta tests/ de la versión evaluada (EduFEM 1.0.0, revisión 91e3df0), no de una estimación, y decir explícitamente que es un recuento de guiones y no una medida de cobertura de código, para no prometer más de lo que el dato sostiene. Ensayar la respuesta oral ya es…

- H-214 · *media* · Tabla 3.10, bloque «Cláusula (a)», p. 99 (PDF p.115) · 15 min
  **La Tabla 3.10 muestra seis criterios donde umbral y observado coinciden, sin la columna que los vuelve refutables**
  <br>→ Añadir a la Tabla 3.10 una Nota: «Los seis criterios de la cláusula (a) son de exhaustividad: su umbral es el total del universo y los refutarían, respectivamente, una etapa sin módulo, una etapa sin desarrollo, una magnitud sin exposición, una fase en otra vista, un ítem sin instrumento o una entidad perdida (Tabla 2.9).»

- H-216 · *media* · Limitaciones y Recomendaciones, pp. 107-110 (PDF pp.123-126) · 30 min
  **La tasa de 1,54 del campo de tensiones del Q4 no llega ni a limitaciones ni a recomendaciones**
  <br>→ Añadir un ítem a Limitaciones: «El campo de tensiones recuperado del Q4 converge a O(h1,54) y no a O(h2). La explicación que el trabajo propone —la capa de contorno, donde cada nodo recibe el promedio de un solo lado— no se contrastó (Sección 3.2).» Y una frase a «Ampliación de la batería de validación»: «Conviene además recomputar la norma L2 del campo de tensiones excluyendo la franja de contorno, para contrastar esa explicación.»

- H-267 · *baja* · §1.4 y §1.7-1.8, p. 22-26 (PDF p. 38-42) · 5 min
  **Tres ecuaciones con label nunca se referencian desde ningún otro punto del documento**
  <br>→ Si el Anexo G o el Capitulo 3 desarrollan la relacion cinematica o la integral de rigidez antes de la aproximacion de Gauss, anadir ahi el \autoref correspondiente; si no hay donde, dejar las labels como estan.

- H-275 · *baja* · §2.2.6 «Módulos educativos», p. 69 (PDF p.85) · 5 min
  **«Garantiza» sin la fórmula «por construcción» que el propio CRITERIOS exige, en dos lugares**
  <br>→ Sustituir por: «la regla evita que dos representaciones compitan por el mismo lienzo y hace que, por construcción, lo resaltado sobre la malla corresponda siempre a un único análisis». En §2.2.8, sustituir «recalculada con las mismas funciones del motor para garantizar consistencia con los módulos educativos» por «recalculada con las mismas funciones del motor, lo que asegura por construcción su consistencia con los módulos educativos».

- H-277 · *baja* · §3.5 «Validación con la membrana de Cook», p. 85 (PDF p.101) · 5 min
  **«Significativa» sin prueba estadística en un trabajo que se declara de enfoque cuantitativo**
  <br>→ Sustituir por: «con 2178 GDL el error del Q9 cae por debajo del 0,1\,\% y la ventaja deja de ser apreciable frente a la incertidumbre de la propia referencia». Revisar que la nota correspondiente de \texttt{CRITERIOS.md} —«la razón de errores Q4/Q9 se declara no significativa a 2178 GDL»— se actualice en el mismo sentido, para no dejar dos reglas en conflicto.

- H-279 · *baja* · Nota de la Tabla 1.1, §1.1, p. 17 (PDF p. 33) · 1 h
  **Tabla 1.1 juzga ANSYS, Abaqus, CALFEM y FEniCS sin fuente, contra su propia nota**
  <br>→ Descartar la opción (a): citar manuales de ANSYS y Abaqus añadiría referencias que el documento no usa para nada más. No hace falta tampoco renombrar las columnas, porque el texto de la p. 14 ya acota qué se juzga de ellas. Basta con corregir la última cláusula de la nota de la Tabla 1.1, que hoy dice «y las demás, de las publicaciones citadas en cada encabezado», por: «las de ED-Elas2D, el analizador de cerchas y VisualFEA, de las publicaciones citadas en sus encabezados; y las dos categorías de propósito general…

- H-289 · *baja* · D.1, p. 137 (PDF p. 153) · 5 min
  **Frase que se autocorrige sobre dónde quedan las figuras del guion de V&V**
  <br>→ Reescribir como: «deposita los datos crudos en archivos CSV en docs/vyv/datos/ y las figuras en docs/vyv/figuras/».

- H-329 · *baja* · §1.1, pp. 14-15 (PDF pp. 30-31) · 5 min
  **¿Qué aporta esto que no aporte ED-Elas2D, que existe desde 1998?**
  <br>→ No tocar el texto. Llevar memorizada la respuesta corta: «ED-Elas2D confirma que esto tiene sentido; es mi antecedente más directo y lo digo así. La diferencia está en tres cosas que sus propios autores declaran que su programa no hace. Primera, la respuesta: ellos reconocen en la página 253 que su post-proceso es meramente descriptivo y no explica el suavizado nodal de tensiones; EduFEM lo abre con la sonda, que da el valor crudo del punto de Gauss y el promediado nodal, y con el contraste de reacciones. Segunda,…

- H-330 · *baja* · Introducción, «Alcance y limitaciones», p. 9 (PDF p. 25) · 5 min
  **¿Por qué Q4 y Q9, y no triángulos, elementos de orden superior o tres dimensiones?**
  <br>→ No tocar el texto. Respuesta oral, con las cifras a mano: «Porque el núcleo de la herramienta es que las matrices se puedan mirar. En el Q4 la matriz constitutiva es de 3 × 3 y la de deformación, de 3 × 8: caben en una pantalla y en una hoja. En un hexaedro de ocho nodos la constitutiva es de 6 × 6, la de deformación de 6 × 24 y la rigidez elemental de 24 × 24: son quinientas setenta y seis entradas que nadie sigue paso a paso. El par Q4–Q9 es el mínimo que permite contrastar dos órdenes de interpolación sin cambi…

- H-332 · *baja* · §1.13, p. 36 (PDF p. 52) · 5 min
  **¿Por qué SAP2000 es una referencia válida, si también es una aproximación numérica?**
  <br>→ No tocar el texto. Respuesta oral: «SAP2000 no es mi patrón y no lo presento como tal: por eso esa columna de la Tabla 3.2 se llama diferencia y no error, y lo explico en la nota. Mi patrón es la solución analítica de Timoshenko y Goodier, que es exacta dentro de la teoría de la elasticidad, y ahí el error es del 0,04 por ciento. SAP2000 entra como tercera opinión, con una formulación distinta —cáscara de Mindlin-Reissner frente a continuo de tensión plana—, y que dos formulaciones distintas coincidan con la soluc… *(Corregido el 2026-09-25: no es Mindlin-Reissner; ver la nota bajo PD-21.)*

- H-333 · *baja* · §2.1.4, p. 47 (PDF p. 63) · 5 min
  **¿Cuál es la población y cuál la muestra de esta investigación?**
  <br>→ No tocar el texto. Respuesta oral, que conviene tener lista porque es la pregunta de apertura típica del docente de metodología: «La unidad de análisis es el procedimiento de cálculo del software, no las personas. La población es el universo de problemas de elasticidad lineal plana resolubles con cuadriláteros isoparamétricos. La muestra no es probabilística sino dirigida, por valor probatorio, que es la práctica establecida en verificación de códigos de cálculo: los casos se eligen por su capacidad de ejercitar t…

- H-334 · *baja* · Introducción, «Hipótesis», p. 7 (PDF p. 23) · 5 min
  **Su hipótesis: ¿qué habría tenido que pasar para que quedara refutada?**
  <br>→ No tocar el texto, salvo por el ajuste del cálculo manual señalado en el hallazgo correspondiente. Respuesta oral: «Está escrito, criterio por criterio, en la última columna de la Tabla 2.4. La refutaba una etapa del procedimiento sin instrumento que la exponga; uno solo de los dieciocho contenidos sin cobertura; una fase que no operara sobre el mismo lienzo; una tasa de convergencia a más de medio orden de la teórica en cualquiera de las cuatro configuraciones; un error de la flecha por encima del tres por ciento…

---

## Calibración de afirmaciones

Es el eje prioritario de la auditoría y el que más pesa en la defensa. **Cuarenta y cinco
frases** cuyo verbo o cuyo alcance excede lo que su evidencia sostiene, cada una con su ubicación
y su versión calibrada. Es también el eje con más hallazgos de los diez.

**La regla que el propio autor se dio** (`CRITERIOS.md`), y que es el patrón contra el que se
juzga cada frase:

| Verbo | Solo para |
|---|---|
| **garantiza** | lo que se sigue por construcción o demostración — y hay que decir «por construcción» |
| **valida** | el contraste con referencias **externas** de exactitud conocida |
| **verifica** | el contraste del código contra una solución manufacturada o contra sí mismo |
| **se cumple** | un criterio numérico con umbral fijado **de antemano** |
| en lo demás | «respalda», «es coherente con», «reporta» |

**Tres advertencias antes de aplicar esta sección.**

1. **No sobrecorregir.** Buena parte de este documento ya está bien calibrada, y hay pasajes
   ejemplares. Calibrar no es atenuar: es hacer que el verbo diga exactamente el tipo de
   evidencia que hay detrás. Una frase que hoy dice «se cumple» sobre un criterio con umbral
   fijado de antemano está bien como está.
2. **Los universales son el patrón dominante.** «Cada resultado», «toda magnitud», «cada
   etapa»: la evidencia es de cobertura sobre casos ensayados, y sostiene un cuantificador más
   modesto o una vía explícita. La corrección casi nunca es quitar la afirmación, sino **decir
   por dónde se cumple**.
3. **Lo que la literatura reporta sobre otras herramientas se queda con su fuente.** No se
   traslada a EduFEM sin cita, y no se convierte en efecto sobre el estudiante.

### Tabla de frases a calibrar



| # | Dónde | Frase del documento | Sev. |
|---|---|---|---|
| H-012 | Tabla 3.7, fila FEA30, p. 91 (PDF p.107) | Columna «Instrumento de EduFEM»: «Secuencias de malla con la diferencia entre mallas sucesivas como regla de parada, y… | alta |
| H-004 | §2.1.4, p. 49 (PDF p. 65) | Literal, verificada en el fuente: «Y uno, la deducción de la matriz de rigidez por métodos alternativos (FEM3), es un d… | alta |
| H-091 | Encabezado del Anexo G, p. 164 (PDF p.180) | Anexo G: «el ejemplo canónico de validación». §2.1.3, p. 48 (PDF p.64): «A los tres casos se suma el ejemplo canónico —… | media |
| H-092 | §G.2.5, p. 169 (PDF p.185) | «La suma vertical 1000,00 equilibra exactamente la carga aplicada −1000, y la horizontal es nula: el modelo está en equ… | media |
| H-008 | §1.1, Tabla 1.1, p. 16-17 (PDF p. 32-33) | «...y no a juicios sobre la calidad didáctica de cada producto; los atributos que exigirían examinar cada producto en p… | media |
| H-094 | §1.13 Verificación y validación, p. 36 (PDF p. 52) | «Es la acepción corriente en la práctica del MEF y es distinta de la validación experimental en sentido estricto, que n… | media |
| H-003 | §3.8, p. 100 (PDF p.116) | Cita literal en 04_resultados.tex:451. Los límites del software están confirmados en el código: file_io/memoria_calculo… | media |
| H-011 | §3.8, p. 100 (PDF p.116) | «Cada magnitud que el software entrega en los casos ensayados se comprobó contra un patrón independiente: una solución… | media |
| H-072 | §3.6 «Cobertura de contenido», p. 90 (PDF p.106) | «con el instrumento de EduFEM que cubre cada uno y con la evidencia de este documento que lo demuestra» | media |
| H-074 | §3.3 «Consistencia interna del modelo de datos», p. 79 (PDF p.95) | «Este resultado comprueba el patrón de indexación adoptado y descarta los fallos por indexación directa que aparecían a… | media |
| H-075 | §3.1 «Medición de los datos y validación de la medición», p. 74 (PDF p.90) | «La confiabilidad de estas mediciones se asegura por tres vías.» | media |
| H-076 | §3.4 «Validación con la viga de Timoshenko», p. 80 (PDF p.96) | «la forma en que se escribe la expresión que la norma ACI 318 propone para hormigón de peso normal» | media |
| H-077 | §3.7.4 «Limitaciones observadas», tab:tiempos y párrafo siguiente, p. 98 (PDF p.114) | «Tiempos de una corrida representativa: varían con la carga del equipo y pueden resultar hasta un 50\,\% mayores.» … «e… | media |
| H-085 | Título de la Tabla 3.7, §3.6.2, p. 91 (PDF p.107) | «…el instrumento de EduFEM que lo cubre y la evidencia que lo demuestra en este documento.» Regla de marcado declarada:… | media |
| H-088 | §3.7.4, p. 98 (PDF p.114) | «el tiempo de factorización y solución se reduce 1,7 veces con 2178 grados de libertad, 2,0 veces con 8450 y 2,9 veces… | media |
| H-097 | §3.2, p. 76 (PDF p.92) | «no alteran el orden de convergencia, lo que descarta errores de orden en el ensamblaje, la integración por cuadratura… | media |
| H-099 | Leyenda de la Tabla 3.7, p. 91 (PDF p.107) | Leyenda: «…el instrumento de EduFEM que lo cubre y la evidencia que lo demuestra en este documento». §3.6.1, p. 90: «Ca… | media |
| H-100 | §3.7.1, primer párrafo, p. 93 (PDF p.109) | §3.7.1: «Eso descarta errores de orden en el ensamblaje […]». §3.7.2, p. 96: «las tasas de convergencia comprueban que… | media |
| H-073 | Conclusiones, tercer párrafo, p. 102 (PDF p.118) | «Queda demostrado que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene; queda fuera de lo med… | media |
| H-083 | Conclusiones, p. 102 (PDF p. 118) | Literal: «Queda demostrado que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene; queda fuera… | media |
| H-101 | Limitaciones, último ítem, p. 108 (PDF p.124) | Limitaciones, p. 108: «Es adecuado para los tamaños de modelo de un contexto educativo y para las mallas de decenas de… | media |
| H-102 | Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) — instancia única | §3.4, p. 82 (PDF p.98): «En las componentes secundarias, cuya magnitud es entre seis y treinta y cinco veces menor que… | media |
| H-103 | Conclusiones, tercer párrafo, p. 102 (PDF p.118) — instancia única | «Queda demostrado que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene; queda fuera de lo med… | media |
| H-006 | Resumen, p. i (PDF p.2) | «los dieciocho contenidos que un consenso publicado de expertos exige tienen instrumento en el software, según el cotej… | media |
| H-078 | Introducción, «Planteamiento del problema», p. 2-3 (PDF p.18-19) | «Son las dos propiedades que la memoria de cálculo asegura en la práctica profesional.» | media |
| H-080 | Hipótesis, p. 6 (PDF p. 22) | Hipótesis literal, verificada. Contraevidencia decisiva, también literal: «El nivel de caja negra es el de referencia y… | media |
| H-081 | OE5, p. 6 (PDF p. 22) y PI-1, p. 7 (PDF p. 23) —las dos apariciones de «la literatura… | OE5 literal: «Validar la propuesta contrastando la cobertura del procedimiento de cálculo y del contenido que la litera… | media |
| H-082 | Resumen, p. i (PDF p. 2) y Aportes del trabajo, p. 106 (PDF p. 122) | Resumen literal: «los errores frente a la solución analítica fueron del 0,04\,\% en la tensión normal y del 0,26\,\% en… | media |
| H-086 | Planteamiento del problema, p. 2 (PDF p.18) | «Es la única formulación del problema que el documento emplea: la Subsección 2.1.3 la retoma textualmente y la Sección… | media |
| H-087 | Resumen, p. i (PDF p.2) | «EduFEM reúne un motor de cálculo, una interfaz de pre-proceso, proceso y post-proceso sobre un mismo lienzo, ocho módu… | media |
| H-093 | «Planteamiento del problema», p. 2 (PDF p.18) | Introducción: «ninguno de los recursos revisados reúne a la vez tres atributos». Nota de la Tabla 1.1, p. 18 (PDF p.34)… | media |
| H-009 | §2.1.6, Tabla 2.4, p. 52 (PDF p.68) | «Error de la flecha central frente a la solución analítica │ < 3 % │ Tolerancia de ingeniería fijada por el autor». Idé… | media |
| H-070 | §2.2.3 «Motor de cálculo», p. 63 (PDF p.79) | Ambas literales y en el mismo apartado. 03_diseno_implementacion.tex:119: «el umbral protege la verificabilidad, porque… | media |
| H-095 | §2.2.1 Requisitos y decisiones de diseño, p. 55 (PDF p. 71), párrafo de las «tres… | »Tres decisiones generales concretan estos requisitos [...] La primera es el idioma [...] se redactan en español [...]… | media |
| H-276 | Anexo F/G, «Memoria de cálculo: ejemplo resuelto paso a paso», p. 169 (PDF p.185) | «La suma vertical $\RyTot$ equilibra exactamente la carga aplicada $-\valP$, y la horizontal es nula» | baja |
| H-279 | Nota de la Tabla 1.1, §1.1, p. 17 (PDF p. 33) | Encabezados sin cita, verificados. Contraevidencia literal, no considerada por el hallazgo: el párrafo de la p. 14 decl… | baja |
| H-277 | §3.5 «Validación con la membrana de Cook», p. 85 (PDF p.101) | «con 2178 GDL el error del Q9 cae por debajo del 0,1\,\% y la razón deja de ser significativa» | baja |
| H-280 | §3.6.2, p. 92 (PDF p.108) | «Conviene decir qué prueba y qué no prueba ese resultado» (p. 92); «Conviene acotar ese resultado» (p. 90); «Conviene p… | baja |
| H-283 | Conclusiones, cierre del contraste de hipótesis, p. 105 (PDF p.121) | «El desarrollo de EduFEM mejoró la forma en que el software expone el procedimiento de cálculo —de caja negra a procedi… | baja |
| H-284 | Conclusiones, Objetivo específico 3, p. 104 (PDF p.120) | «es la decisión de diseño de la que depende la trazabilidad» vs. Aportes, p. 106 (PDF p.122): «tres decisiones que hace… | baja |
| H-285 | Recomendaciones, «Guía de uso en la cátedra», p. 109 (PDF p.125) | «El manual del Anexo B enseña a operar el software. Conviene acompañarlo con una guía docente que proponga una secuenci… | baja |
| H-005 | Resumen, p. i (PDF p.2) y §3.7.1 «Alcances», p. 96 (PDF p.112) | «los errores frente a la solución analítica fueron del 0,04 % en la tensión normal y del 0,26 % en la flecha» | baja |
| H-007 | «Justificación», plano académico, p. 4 (PDF p.20) | «La literatura sobre enseñanza del método reporta que la simulación interactiva y la construcción paso a paso de las he… | baja |
| H-281 | «Alcance y limitaciones», p. 9 (PDF p.25) | «El plano es la mínima dimensión en la que aparece el carácter de continuo y, a la vez, conserva matrices de tamaño leg… | baja |
| H-275 | §2.2.6 «Módulos educativos», p. 69 (PDF p.85) | «la regla evita que dos representaciones compitan por el mismo lienzo y garantiza que lo resaltado sobre la malla corre… | baja |


#### H-012 · Tabla 3.7, fila FEA30, p. 91 (PDF p.107) · severidad alta

**FEA30 acredita como «Instrumento de EduFEM» una extrapolación de Richardson que el software no implementa**

- **Dice:** Columna «Instrumento de EduFEM»: «Secuencias de malla con la diferencia entre mallas sucesivas como regla de parada, y extrapolación de Richardson para estimar el límite».
- **Problema:** La regla de marcado exige que «el instrumento existe en la versión evaluada», pero la extrapolación de Richardson no está en el código de EduFEM —es un procedimiento que el autor aplicó a mano en §3.5 y en §1.10, y así lo dice el propio texto: «se corrobora en este trabajo con una extrapolación de…
- **Versión calibrada:** En 04_resultados.tex:309 dejar la celda de instrumento como «Secuencias de malla con la diferencia entre mallas sucesivas como regla de parada, que aplica el usuario» y mover Richardson a la evidencia: «Tabla 3.1; Sección 3.5 (extrapolación de Richardson aplicada por el autor, no por el software)»; y en el párrafo de salvedades de p.93 añadir Richardson junto a la regla de parada, ya que hoy solo menciona esta última.

#### H-004 · §2.1.4, p. 49 (PDF p. 65) · severidad alta

**El universo de contenido excluye el único ítem que el software no cubre, y luego se reporta 18 de 18**

- **Dice:** Literal, verificada en el fuente: «Y uno, la deducción de la matriz de rigidez por métodos alternativos (FEM3), es un desarrollo teórico que el software no expone» (02b_diseno_metodologico.tex:148) y «No expuesto por el software (1): la deducción de la matriz…
- **Problema:** El único criterio de contenido de la cláusula (a) se mide contra un universo cuya definición usó al propio software como filtro, de modo que el veredicto «18 de 18» es, en un ítem, verdadero por construcción y no por cobertura.
- **Versión calibrada:** La acción propuesta es correcta y se conserva, con un ajuste. Lo esencial es quitar el software del criterio de exclusión, no conceder un «18 de 19». En §2.1.4 escribir: «Y uno, la deducción de la matriz de rigidez por métodos alternativos (FEM3), queda fuera por ser un desarrollo teórico previo al procedimiento de cálculo, no una etapa de él. Se deja constancia de que es, además, el único de los 19 ítems que el software no expone: contado dentro del universo, la cobertura sería de 18 sobre 19.» En la nota de la Tabla 3.7 sustituir el rótulo «No expuesto por el software (1)» por «Previo al procedimiento de cálculo, por ser un desarrollo teórico (1): FEM3, que además es el único ítem que el software no expone». En la Tabla 3.10 basta la nota «18 de 18 sobre el universo definido en la Subsección 2.1.4»; el «18 de 19» ya queda dicho en §2.1.4 y repetirlo en la tabla de veredictos invita a confundir el criterio con su matiz.

#### H-091 · Encabezado del Anexo G, p. 164 (PDF p.180) · severidad media

**«Ejemplo canónico de validación» contradice al Capítulo 2, que dice que ese ejemplo no mide exactitud**

- **Dice:** Anexo G: «el ejemplo canónico de validación». §2.1.3, p. 48 (PDF p.64): «A los tres casos se suma el ejemplo canónico —nueve nodos y cuatro elementos Q4—, que no mide exactitud: es el escenario sobre el que se demuestra, en el Anexo G, que la memoria de cálcu…
- **Versión calibrada:** En el Anexo G: «...el contenido de la Memoria de Calculo que EduFEM genera para el ejemplo canonico de trazabilidad —nueve nodos, cuatro elementos Q4, tension plana—, el caso sobre el que se demuestra que la memoria puede rehacerse a mano (Subseccion 2.1.3).» En el Anexo B, suprimir «de validacion» y dejar «sobre el ejemplo canonico». Comprobar de paso que ningun otro punto adjetive «de validacion» a este caso.

#### H-092 · §G.2.5, p. 169 (PDF p.185) · severidad media

**«El modelo está en equilibrio» se presenta como resultado, cuando se sigue por construcción**

- **Dice:** «La suma vertical 1000,00 equilibra exactamente la carga aplicada −1000, y la horizontal es nula: el modelo está en equilibrio.»
- **Versión calibrada:** Reescribir: «La resultante vertical, 1000,00, iguala la carga aplicada y la horizontal es nula. Que las dos sumas cierren se sigue por construcción de R = K u − F, porque las filas de K tienen suma nula frente a una traslación de cuerpo rígido; por eso la comprobación no mide exactitud, sino que detecta un error de dispersión en el ensamblaje o un sistema mal resuelto.»

#### H-008 · §1.1, Tabla 1.1, p. 16-17 (PDF p. 32-33) · severidad media

**La Tabla 1.1 hace juicios de calidad didáctica que el propio texto promete no hacer para 2 de sus 6 columnas**

- **Dice:** «...y no a juicios sobre la calidad didáctica de cada producto; los atributos que exigirían examinar cada producto en particular se dejan sin evaluar y se marcan con una raya» (p. 14) frente a las celdas «No (no didáctico)» (fila Procedimiento completo) y «Si…
- **Versión calibrada:** No poner rayas en esas filas: dejar «Procedimiento completo» o «Lectura de la respuesta» sin evaluar para el software comercial borraría justamente el contraste que la sección construye. Reescribir la frase de restricción (02_marco_teorico.tex L21) para que describa lo que la tabla hace, p. ej.: «Para estas dos categorías, las celdas de la Tabla 1.1 caracterizan la categoría a partir de lo que su naturaleza y su documentación declaran —interfaz, licencia, requisitos de ejecución, exposición del cálculo intermedio y alcance del procedimiento—, sin examinar producto por producto y sin evaluar su calidad didáctica; los atributos que solo podrían establecerse producto por producto se marcan con…

#### H-094 · §1.13 Verificación y validación, p. 36 (PDF p. 52) · severidad media

**«Acepción corriente en la práctica del MEF» afirmada sin cita, justo en la definición canónica de «validación»**

- **Dice:** «Es la acepción corriente en la práctica del MEF y es distinta de la validación experimental en sentido estricto, que no se realiza.»
- **Versión calibrada:** No usar la reformulación propuesta: «habitual en trabajos de verificación y validación en el MEF que comparan contra soluciones analíticas y software comercial» es la MISMA generalización sin respaldo, solo más larga, y añade un «El autor adopta» que CRITERIOS.md reserva a decisiones de diseño experimental. Suprimir la afirmación de currencia y dejar la convención como lo que es, una estipulación del documento. En `capitulos_final/02_marco_teorico.tex:460` reemplazar «Es la acepción corriente en la práctica del MEF y es distinta de la validación experimental en sentido estricto, que no se realiza.» por: «Esta acepción se distingue de la validación experimental en sentido estricto, que este…

#### H-003 · §3.8, p. 100 (PDF p.116) · severidad media

**La memoria en PDF degrada su desarrollo por encima de cierto tamano, y el documento no lo declara**

- **Dice:** Cita literal en 04_resultados.tex:451. Los límites del software están confirmados en el código: file_io/memoria_calculo.py:1161-1162 `_COMPACT_MAX_ELEMENTS_Q4 = 2`, `_COMPACT_MAX_ELEMENTS_Q9 = 1`; :1078 «Elige el elemento estrella: máxima energía de deformaci…
- **Versión calibrada:** No recortar la afirmacion de §3.8: es correcta sobre el software completo. Lo que falta es declarar los umbrales de presentacion. (a) Anadir a las limitaciones, o a §2.2.9 donde se describe la memoria: «El desarrollo integro de todos los elementos se emite mientras el modelo no supere dos elementos Q4 o uno Q9; por encima de ese tamano la memoria desarrolla el elemento de mayor energia de deformacion y presenta la matriz global por su patron de dispersion y sus indicadores, en lugar de sus coeficientes.» (b) En §3.8, precisar que la trazabilidad etapa por etapa en el documento generado es exhaustiva en modelos pequenos y representativa por elemento en mallas mayores, sin perjuicio de la tra…

#### H-011 · §3.8, p. 100 (PDF p.116) · severidad media

**El universal «Cada magnitud […] se comprobó contra un patrón independiente» lo refuta la propia tesis**

- **Dice:** «Cada magnitud que el software entrega en los casos ensayados se comprobó contra un patrón independiente: una solución exacta construida, una solución analítica, un valor de referencia de uso extendido y un modelo comercial.»
- **Versión calibrada:** Sustituir por: «Las magnitudes que los casos ensayados ejercitan se comprobaron contra patrones independientes: el desplazamiento y el campo de tensiones recuperado contra una solución exacta construida (Sección 3.2), la tensión normal sigma_x y la flecha contra la solución analítica y contra un modelo comercial (Sección 3.4), y el desplazamiento del extremo contra un valor de referencia de uso extendido (Sección 3.5). Las reacciones se comprueban por el residuo de equilibrio global, que es una comprobación interna. Las componentes secundarias de tensión se reportan con su error pero no forman parte de los criterios (Subsección 2.1.6), y la tensión de von Mises y las tensiones principales s…

#### H-072 · §3.6 «Cobertura de contenido», p. 90 (PDF p.106) · severidad media

**La tabla de cobertura «demuestra» lo que en realidad respalda: cotejo documental del autor**

- **Dice:** «con el instrumento de EduFEM que cubre cada uno y con la evidencia de este documento que lo demuestra»
- **Versión calibrada:** Sustituir «que lo demuestra» por «que lo respalda» en las tres apariciones. En la leyenda de tab:especificaciones, el texto completo queda: «Tabla de cobertura de contenido. Por cada destreza o concepto que el consenso de expertos exige al egresado, dentro del alcance de este trabajo: el instrumento de EduFEM que lo cubre y la evidencia que lo respalda en este documento.»

#### H-074 · §3.3 «Consistencia interna del modelo de datos», p. 79 (PDF p.95) · severidad media

**Una prueba con un juego de identificadores «descarta los fallos» de indexación en general**

- **Dice:** «Este resultado comprueba el patrón de indexación adoptado y descarta los fallos por indexación directa que aparecían al eliminar nodos.»
- **Versión calibrada:** Sustituir por: «Este resultado es coherente con el patrón de indexación adoptado y, en la configuración ensayada, no reproduce los fallos por indexación directa que aparecían al eliminar nodos.»

#### H-075 · §3.1 «Medición de los datos y validación de la medición», p. 74 (PDF p.90) · severidad media

**«La confiabilidad de estas mediciones se asegura por tres vías»: tres precauciones no aseguran**

- **Dice:** «La confiabilidad de estas mediciones se asegura por tres vías.»
- **Versión calibrada:** Sustituir por: «La confiabilidad de estas mediciones se respalda por tres vías.»

#### H-076 · §3.4 «Validación con la viga de Timoshenko», p. 80 (PDF p.96) · severidad media

**Se atribuye una expresión a la norma ACI 318 sin referencia en la bibliografía**

- **Dice:** «la forma en que se escribe la expresión que la norma ACI 318 propone para hormigón de peso normal»
- **Versión calibrada:** Como CRITERIOS prohíbe agregar claves de bibliografía nuevas al capítulo, retirar la atribución nominal. Sustituir la frase por: «Ese módulo es el que arroja la correlación módulo--resistencia $E = 15\,000\sqrt{f'_c}$ en unidades técnicas, de uso corriente para hormigón de peso normal, evaluada en $f'_c = 210$~kgf/cm$^2$.» Si el autor prefiere conservar la atribución, debe añadir a \texttt{referencias.bib} la entrada de ACI 318 con año y editorial y citarla con el localizador de la sección correspondiente.

#### H-077 · §3.7.4 «Limitaciones observadas», tab:tiempos y párrafo siguiente, p. 98 (PDF p.114) · severidad media

**La leyenda de tiempos describe el protocolo peor de lo que es, y las razones van a dos cifras**

- **Dice:** «Tiempos de una corrida representativa: varían con la carga del equipo y pueden resultar hasta un 50\,\% mayores.» … «el tiempo de factorización y solución se reduce 1,7 veces con 2178 grados de libertad, 2,0 veces con 8450 y 2,9 veces con 33\,282»
- **Versión calibrada:** Sustituir el final de la leyenda por: «Cada tiempo es el menor de tres corridas consecutivas sobre el mismo modelo, según el protocolo de \texttt{tests/bench\_timing.py}; con el equipo cargado pueden resultar hasta un 50\,\% mayores.» Y en el párrafo siguiente: «frente al ordenamiento genérico, medido con el mismo guion sobre el sistema reducido y como el menor de tres corridas, el tiempo de factorización y solución se reduce alrededor de 1,7 veces con 2178 grados de libertad, 2,0 veces con 8450 y 2,9 veces con 33\,282.»

#### H-085 · Título de la Tabla 3.7, §3.6.2, p. 91 (PDF p.107) · severidad media

**La columna «Evidencia» de la tabla de cobertura dice «demuestra» donde solo remite a una descripción**

- **Dice:** «…el instrumento de EduFEM que lo cubre y la evidencia que lo demuestra en este documento.» Regla de marcado declarada: «un ítem se da por cubierto solo si el instrumento existe en la versión evaluada y el documento lo describe».
- **Versión calibrada:** Sustituir «la evidencia que lo demuestra en este documento» por «el lugar de este documento donde ese instrumento se describe o se ejercita» en las tres apariciones. En §2.1.5 (p. 50) queda: «Cruza cada ítem del universo de la Subsección 2.1.4 con el instrumento del software que lo cubre y con el lugar de este documento donde ese instrumento se describe o se ejercita.»

#### H-088 · §3.7.4, p. 98 (PDF p.114) · severidad media

**Factores de aceleracion con una cifra decimal sobre corridas cuya variabilidad la tabla cifra en 50 %**

- **Dice:** «el tiempo de factorización y solución se reduce 1,7 veces con 2178 grados de libertad, 2,0 veces con 8450 y 2,9 veces con 33 282». Nota de la Tabla 3.9, misma página: «Tiempos de una corrida representativa: varían con la carga del equipo y pueden resultar ha…
- **Versión calibrada:** Reemplazar por: «…el tiempo de factorización y solución se reduce en un factor que crece con el tamaño del problema: del orden de dos veces con 2178 y 8450 grados de libertad y de cerca de tres con 33 282, medido en corridas representativas y con la misma variabilidad que declara la nota de la Tabla 3.9.»

#### H-097 · §3.2, p. 76 (PDF p.92) · severidad media

**«Descarta» atribuye a dos pruebas un poder de exclusión que el propio capítulo desmiente**

- **Dice:** «no alteran el orden de convergencia, lo que descarta errores de orden en el ensamblaje, la integración por cuadratura de Gauss, el mapeo isoparamétrico sobre elementos no rectangulares, la matriz constitutiva de ambos estados planos y la imposición de restri…
- **Versión calibrada:** Reformular: «...no alteran el orden de convergencia, lo que descarta los errores capaces de degradar ese orden en el ensamblaje, la integración por cuadratura de Gauss, el mapeo isoparamétrico sobre elementos no rectangulares, la matriz constitutiva de ambos estados planos y la imposición de restricciones no homogéneas, sin que ello alcance a los defectos que la medida no recorre (§1.13).» Y en §3.3: «Este resultado respalda el patrón de indexación adoptado frente a los fallos por indexación directa que aparecían al eliminar nodos.»

#### H-099 · Leyenda de la Tabla 3.7, p. 91 (PDF p.107) · severidad media

**«demuestra» y «se cumple por construcción» infringen la tabla de verbos por tipo de evidencia**

- **Dice:** Leyenda: «…el instrumento de EduFEM que lo cubre y la evidencia que lo demuestra en este documento». §3.6.1, p. 90: «Cada valor que la memoria muestra coincide con el que calcula el motor, y eso se cumple por construcción».
- **Versión calibrada:** En la leyenda de la Tabla 3.7 y en §3.6.2 cambiar «que lo demuestra» por «que lo respalda»; en §3.6.1 escribir «…y esa coincidencia queda garantizada por construcción: ambos usan las mismas funciones (Subsección 2.1.5)».

#### H-100 · §3.7.1, primer párrafo, p. 93 (PDF p.109) · severidad media

**«Eso descarta errores de orden» se emite sin la salvedad que llega dos subsecciones después**

- **Dice:** §3.7.1: «Eso descarta errores de orden en el ensamblaje […]». §3.7.2, p. 96: «las tasas de convergencia comprueban que no hay errores de orden en los mecanismos que intervienen en el desplazamiento, no que el motor esté libre de todo error».
- **Versión calibrada:** Añadir la salvedad en el sitio: «Eso descarta errores de orden en los mecanismos que intervienen en el desplazamiento —ensamblaje, integración por cuadratura, mapeo isoparamétrico, matriz constitutiva de ambos estados planos e imposición de restricciones—, no que el motor esté libre de todo error (Subsección 3.7.2).»

#### H-073 · Conclusiones, tercer párrafo, p. 102 (PDF p.118) · severidad media

**«Queda demostrado» en Conclusiones, donde la evidencia es cobertura documental y casos numéricos**

- **Dice:** «Queda demostrado que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene; queda fuera de lo medido qué ocurre cuando ese medio se pone en manos de un curso.»
- **Versión calibrada:** Sustituir por: «Queda establecido, sobre el software construido y sobre los casos ensayados, que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene; queda fuera de lo medido qué ocurre cuando ese medio se pone en manos de un curso.»

#### H-083 · Conclusiones, p. 102 (PDF p. 118) · severidad media

**«Queda demostrado… y que EduFEM las tiene»: el verbo más fuerte del documento para un cotejo propio**

- **Dice:** Literal: «Queda demostrado que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene; queda fuera de lo medido qué ocurre cuando ese medio se pone en manos de un curso» (05_conclusiones.tex:11).
- **Versión calibrada:** La reformulación propuesta sirve, pero repite lo que las limitaciones dicen doce líneas después y alarga la oración por encima de las ~60 palabras de CRITERIOS.md. Ajustarla a: «Queda establecido, con los criterios fijados de antemano, que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene: la verificabilidad, con evidencia numérica contrastada contra referencias externas; la trazabilidad, con el inventario y el cotejo documental que describe la \autoref{sec:validacion-datos}. Queda fuera de lo medido qué ocurre cuando ese medio se pone en manos de un curso.» La autoría del cotejo no hace falta repetirla aquí: ya está en §2.1.5 y en las limitaciones.

#### H-101 · Limitaciones, último ítem, p. 108 (PDF p.124) · severidad media

**«su costo en memoria […] crece más que linealmente»: la Tabla 3.9 mide lo contrario**

- **Dice:** Limitaciones, p. 108: «Es adecuado para los tamaños de modelo de un contexto educativo y para las mallas de decenas de miles de grados de libertad que mide la Tabla 3.9, pero su costo en memoria y en tiempo crece más que linealmente con el número de grados de…
- **Versión calibrada:** Reescribir el ítem separando lo medido de lo no medido: «El solucionador es directo (Subsección 2.2.5). Es adecuado para los tamaños de modelo de un contexto educativo y para las mallas de decenas de miles de grados de libertad que mide la Tabla 3.9, donde el almacenamiento disperso de K crece de forma prácticamente lineal. Su límite está en el extremo de las mallas muy grandes: el tiempo de solución crece más rápido que el de ensamblaje a medida que la factorización se vuelve dominante (Subsección 3.7.3). La memoria que consume la propia factorización no se midió.»

#### H-102 · Conclusiones, Objetivo específico 4, p. 104 (PDF p.120) — instancia única · severidad media

**Las cifras de Timoshenko se recuerdan sin las dos salvedades que el capítulo 3 declara**

- **Dice:** §3.4, p. 82 (PDF p.98): «En las componentes secundarias, cuya magnitud es entre seis y treinta y cinco veces menor que la de σx, los errores relativos crecen: en el punto B, 0,94 % en σy y 2,89 % en τxy frente a la solución analítica, y 4,56 % y 2,72 % frente…
- **Versión calibrada:** Añadir en el OE4, tras las cifras, una sola oración: «Esos máximos se toman sobre los tres puntos de control; en las componentes secundarias, de magnitud entre seis y treinta y cinco veces menor, el error llega al 2,89 % frente a la solución analítica (Tabla 3.2).» Dejar el párrafo de los Aportes como está: ya nombra las dos magnitudes acotadas y coincide con la fórmula de §3.7.1.

#### H-103 · Conclusiones, tercer párrafo, p. 102 (PDF p.118) — instancia única · severidad media

**«Queda demostrado» y «El trabajo lo establece» exceden el tipo de evidencia declarado**

- **Dice:** «Queda demostrado que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene; queda fuera de lo medido qué ocurre cuando ese medio se pone en manos de un curso.»
- **Versión calibrada:** Sustituir solo el verbo y explicitar el tipo de evidencia como pide CRITERIOS.md: «Queda establecido, por construcción y por el cumplimiento de los criterios de la Tabla 3.10, que un medio de cálculo puede tener las dos propiedades y que EduFEM las tiene; queda fuera de lo medido qué ocurre cuando ese medio se pone en manos de un curso.» Dejar «El trabajo lo establece por la vía que le corresponde a una investigación tecnológica…» sin cambios: describe el método, no el grado de prueba.

#### H-006 · Resumen, p. i (PDF p.2) · severidad media

**«los dieciocho contenidos que un consenso de expertos exige» oculta que son 18 de 49**

- **Dice:** «los dieciocho contenidos que un consenso publicado de expertos exige tienen instrumento en el software, según el cotejo del autor»
- **Versión calibrada:** Arreglo de una clausula en el Resumen, tomando la redaccion que las propias Conclusiones ya usan: «los dieciocho contenidos que un consenso publicado de expertos exige dentro del alcance de este trabajo». No hace falta mas: §2.1.4 detalla los 49 items y de donde salen los 18, y la nota de la Tabla 3.7 enumera los 31 excluidos con sus tres motivos.

#### H-078 · Introducción, «Planteamiento del problema», p. 2-3 (PDF p.18-19) · severidad media

**Premisa central sobre la práctica profesional enunciada dos veces sin ninguna fuente**

- **Dice:** «Son las dos propiedades que la memoria de cálculo asegura en la práctica profesional.»
- **Versión calibrada:** Sustituir por: «Es lo que persigue la memoria de cálculo en la práctica profesional: un documento que permite a un revisor seguir el procedimiento y comprobarlo.» Si el autor dispone de una fuente normativa o de un manual de práctica que lo sostenga, citarla con localizador de página en esta misma oración y conservar entonces el verbo «sostiene».

#### H-080 · Hipótesis, p. 6 (PDF p. 22) · severidad media

**La hipótesis afirma «mejorar» y «elevando» sin línea de base medida, y nunca se declara**

- **Dice:** Hipótesis literal, verificada. Contraevidencia decisiva, también literal: «El nivel de caja negra es el de referencia y se documenta con la matriz de atributos de la \autoref{tab:comparativa}» (02b_diseno_metodologico.tex:55).
- **Versión calibrada:** El párrafo de cinco líneas que se propone repite lo que §2.1.2 ya dice y roza la regla de CRITERIOS.md de explicar cada cosa una sola vez. Sustituirlo por una sola oración al final del penúltimo párrafo de §3.8, antes de «Queda así respondido el problema científico»: «El nivel de partida de la variable independiente no se midió con estos mismos indicadores: se caracteriza documentalmente en la \autoref{tab:comparativa}, según se declara en la \autoref{sec:variables-met}. Lo que las cifras de este capítulo establecen es el estado alcanzado por la herramienta frente a los criterios fijados de antemano.» En las conclusiones (p. 105) basta con añadir a «mejoró la forma en que el software expone…

#### H-081 · OE5, p. 6 (PDF p. 22) y PI-1, p. 7 (PDF p. 23) —las dos apariciones de «la literatura… · severidad media

**«La literatura especializada exige» atribuye a toda una disciplina lo que reporta un solo estudio**

- **Dice:** OE5 literal: «Validar la propuesta contrastando la cobertura del procedimiento de cálculo y del contenido que la literatura especializada exige…». Salvedad ya presente en §2.1.5: «El propio estudio advierte que sus resultados, obtenidos con expertos mexicanos…
- **Versión calibrada:** Sustituir en las SEIS apariciones es excesivo y rompería la regla de oraciones de hasta ~60 palabras de CRITERIOS.md. Corregir solo las dos que dicen «la literatura especializada», que son las que generalizan. En el OE5: «…la cobertura del procedimiento de cálculo y del contenido que un consenso publicado de expertos califica como necesario para el egresado, junto con los resultados de la verificación, contra los criterios de aceptación fijados de antemano, para establecer si el análisis resulta trazable y verificable.» En PI-1: «…y cubre el contenido que un consenso publicado de expertos califica como necesario para el egresado?» Dejar «los expertos exigen» donde el referente ya está glosa…

#### H-082 · Resumen, p. i (PDF p. 2) y Aportes del trabajo, p. 106 (PDF p. 122) · severidad media

**El Resumen y las conclusiones dan solo las componentes primarias y omiten el 2,89 % y el 4,56 %**

- **Dice:** Resumen literal: «los errores frente a la solución analítica fueron del 0,04\,\% en la tensión normal y del 0,26\,\% en la flecha». Aportes literal: «el error de la tensión normal y de la flecha queda por debajo del $0{,}3\,\%$». Conclusiones OE4, en cambio:…
- **Versión calibrada:** Lo imprescindible es desambiguar la magnitud, no ampliar el resumen. En el Resumen escribir «del 0,04\,\% en la tensión normal longitudinal $\sigma_x$» y «del 0,21\,\% en $\sigma_x$». En Aportes, «el error de $\sigma_x$ y de la flecha queda por debajo del $0{,}3\,\%$». Opcionalmente, y solo en el Resumen, cerrar con «; en las componentes secundarias, de magnitud entre seis y treinta y cinco veces menor, los errores relativos llegan al 2,9\,\%», que es la cifra de la Tabla 3.2 y concuerda con la redacción de la p. 82. No tocar las conclusiones del OE4.

#### H-086 · Planteamiento del problema, p. 2 (PDF p.18) · severidad media

**El documento se dirige a un revisor y habla de si mismo en lugar de exponer**

- **Dice:** «Es la única formulación del problema que el documento emplea: la Subsección 2.1.3 la retoma textualmente y la Sección 3.8 la responde.»
- **Versión calibrada:** Borrar la frase entera y dejar que la remisión la haga el aparato: al final del enunciado del problema basta con «(véase la Subsección 2.1.3 y la Sección 3.8)». Aplicar el mismo criterio a «que se declaran para que la selección pueda auditarse» (dejar «Los 31 ítems restantes quedan fuera por tres motivos:») y a «Dos límites quedan a la vista y se declaran» (dejar «Quedan dos límites:»).

#### H-087 · Resumen, p. i (PDF p.2) · severidad media

**El Resumen presenta la memoria como reproducible a mano sin acotarla al ejemplo canónico**

- **Dice:** «EduFEM reúne un motor de cálculo, una interfaz de pre-proceso, proceso y post-proceso sobre un mismo lienzo, ocho módulos educativos y una memoria de cálculo automática que puede reproducirse a mano.» La cláusula (b), p. 7, dice «la memoria de cálculo del ej…
- **Versión calibrada:** Reemplazar el final de la frase por: «…y una memoria de cálculo automática que, en modelos de tamaño didáctico, puede reproducirse a mano: el Anexo G la rehace paso a paso sobre el ejemplo canónico.»

#### H-093 · «Planteamiento del problema», p. 2 (PDF p.18) · severidad media

**«Ninguno reúne» se apoya en celdas «No consta», que la nota de la Tabla 1.1 dice que no implican ausencia**

- **Dice:** Introducción: «ninguno de los recursos revisados reúne a la vez tres atributos». Nota de la Tabla 1.1, p. 18 (PDF p.34): «“No consta”: las publicaciones consultadas no documentan el atributo, lo que no implica que el recurso carezca de él»
- **Versión calibrada:** Cambiar el verbo en la Introducción: «ninguno de los recursos revisados documenta a la vez los tres atributos», o conservar «reúne» añadiendo «según las publicaciones consultadas». La frase de la p. 4 —«Esta capacidad no se documenta en los antecedentes de software educativo revisados»— ya está bien calibrada y sirve de modelo.

#### H-009 · §2.1.6, Tabla 2.4, p. 52 (PDF p.68) · severidad media

**Los tres umbrales de exactitud (3 %, 1 % y 1,5 %) no se justifican en ninguna página**

- **Dice:** «Error de la flecha central frente a la solución analítica | < 3 % | Tolerancia de ingeniería fijada por el autor». Idéntico para «< 1 %» (σx) y «< 1,5 %» (Cook).
- **Versión calibrada:** Anadir una frase en §2.1.6, o una nota al pie de la Tabla 2.4, que diga de donde sale cada orden de magnitud: por ejemplo, la practica habitual de contraste en verificacion y validacion, o el margen con que la literatura reporta la membrana de Cook. NO objetar la celda «Tolerancia de ingenieria fijada por el autor»: declarar que el umbral lo fijo el autor SI es una procedencia, y es mas transparente que atribuirlo a una fuente inexistente.

#### H-070 · §2.2.3 «Motor de cálculo», p. 63 (PDF p.79) · severidad media

**«Ningún resultado procede de un elemento cuya geometría invalide el mapeo» contradice lo dicho una página antes**

- **Dice:** Ambas literales y en el mismo apartado. 03_diseno_implementacion.tex:119: «el umbral protege la verificabilidad, porque ningún resultado procede de un elemento cuya geometría invalide el mapeo». 03_diseno_implementacion.tex:115: «evaluar el determinante en un…
- **Versión calibrada:** Sustituir por: «el umbral protege la verificabilidad, porque descarta antes de ensamblar los elementos cuya geometría invalida el mapeo en los puntos donde los tres controles lo evalúan». Preferir esta forma a la propuesta: «con el alcance que se acaba de declarar» es una remisión vaga y deja la frase apoyada en un antecedente que el lector debe reconstruir.

#### H-095 · §2.2.1 Requisitos y decisiones de diseño, p. 55 (PDF p. 71), párrafo de las "tres… · severidad media

**Voz impersonal que oculta al autor justo al narrar las decisiones de diseño, el aporte propio del trabajo**

- **Dice:** "Tres decisiones generales concretan estos requisitos [...] La primera es el idioma [...] se redactan en español [...] La segunda es la primacía de lo visual [...] La tercera es la independencia tecnológica: EduFEM se apoya..."
- **Versión calibrada:** Corregir donde el sujeto falta de verdad, no las tres cláusulas: (a) 02b_diseno_metodologico.tex:204 → «El autor eligió ese umbral después de observar el comportamiento del motor.»; (b) §2.2.1, p. 55 (PDF p. 71) → «El autor adoptó tres decisiones generales para concretar estos requisitos. La primera es el idioma: … La segunda es la primacía de lo visual: …», dejando intacta la tercera («La tercera es la independencia tecnológica: EduFEM se apoya…»), que ya tiene sujeto permitido. Añadir un tercer caso dentro de la unidad: §2.2.2, p. 57 (PDF p. 73), «Se evitó deliberadamente toda dependencia de bibliotecas multimedia pesadas» → «El autor evitó deliberadamente…». Recuento real: 3.

#### H-276 · Anexo F/G, «Memoria de cálculo: ejemplo resuelto paso a paso», p. 169 (PDF p.185) · severidad baja

**El Anexo dice «equilibra exactamente» donde el cuerpo reporta un residuo de 1,7 × 10⁻¹³**

- **Dice:** «La suma vertical $\RyTot$ equilibra exactamente la carga aplicada $-\valP$, y la horizontal es nula»
- **Versión calibrada:** Sustituir por: «La suma vertical $\RyTot$ equilibra la carga aplicada $-\valP$ dentro de la precisión con que se reportan los valores, y la horizontal es nula a precisión de máquina: el modelo está en equilibrio.»

#### H-279 · Nota de la Tabla 1.1, §1.1, p. 17 (PDF p. 33) · severidad baja

**Tabla 1.1 juzga ANSYS, Abaqus, CALFEM y FEniCS sin fuente, contra su propia nota**

- **Dice:** Encabezados sin cita, verificados. Contraevidencia literal, no considerada por el hallazgo: el párrafo de la p. 14 declara el criterio de evaluación de las dos categorías de propósito general, y la nota de la tabla remite a él («según el criterio enunciado en…
- **Versión calibrada:** Descartar la opción (a): citar manuales de ANSYS y Abaqus añadiría referencias que el documento no usa para nada más. No hace falta tampoco renombrar las columnas, porque el texto de la p. 14 ya acota qué se juzga de ellas. Basta con corregir la última cláusula de la nota de la Tabla 1.1, que hoy dice «y las demás, de las publicaciones citadas en cada encabezado», por: «las de ED-Elas2D, el analizador de cerchas y VisualFEA, de las publicaciones citadas en sus encabezados; y las dos categorías de propósito general, solo por los rasgos que se siguen de su naturaleza, según el criterio enunciado más arriba, sin examen de producto por producto.» Cinco minutos.

#### H-277 · §3.5 «Validación con la membrana de Cook», p. 85 (PDF p.101) · severidad baja

**«Significativa» sin prueba estadística en un trabajo que se declara de enfoque cuantitativo**

- **Dice:** «con 2178 GDL el error del Q9 cae por debajo del 0,1\,\% y la razón deja de ser significativa»
- **Versión calibrada:** Sustituir por: «con 2178 GDL el error del Q9 cae por debajo del 0,1\,\% y la ventaja deja de ser apreciable frente a la incertidumbre de la propia referencia». Revisar que la nota correspondiente de \texttt{CRITERIOS.md} —«la razón de errores Q4/Q9 se declara no significativa a 2178 GDL»— se actualice en el mismo sentido, para no dejar dos reglas en conflicto.

#### H-280 · §3.6.2, p. 92 (PDF p.108) · severidad baja

**El giro «Conviene + verbo» convierte el capítulo 3 en una sucesion de descargos**

- **Dice:** «Conviene decir qué prueba y qué no prueba ese resultado» (p. 92); «Conviene acotar ese resultado» (p. 90); «Conviene precisar el estado real del motor» (p. 97); «Conviene precisar el alcance de esa respuesta» (p. 102).
- **Versión calibrada:** Conservar todas las salvedades y variar la entrada en al menos seis de las nueve del capítulo 3: «Este resultado prueba cobertura y trazabilidad, y no prueba suficiencia…»; «El alcance de ese resultado es acotado: lo comprobado es que…»; «El estado real del motor es el siguiente:»; «El alcance de esa respuesta determina cómo debe leerse todo lo que sigue:». Dejar «conviene» a lo sumo dos veces por capítulo.

#### H-283 · Conclusiones, cierre del contraste de hipótesis, p. 105 (PDF p.121) · severidad baja

**«El desarrollo de EduFEM mejoró…de caja negra a procedimiento a la vista»: comparación nunca hecha**

- **Dice:** «El desarrollo de EduFEM mejoró la forma en que el software expone el procedimiento de cálculo —de caja negra a procedimiento a la vista— y, con ello, el análisis por el MEF en elasticidad plana resulta trazable y verificable, dentro del alcance declarado.»
- **Versión calibrada:** Cambio mínimo de verbo, conservando la cláusula final: «El desarrollo de EduFEM sitúa la forma en que el software expone el procedimiento de cálculo en el nivel “procedimiento a la vista” —frente al de caja negra que la Sección 1.1 documenta en los recursos revisados— y, con ello, el análisis por el MEF en elasticidad plana resulta trazable y verificable, dentro del alcance declarado.» No introducir la frase «no se ensayó aquí sobre un software propio»: alarga la oración y roza las expresiones que CRITERIOS.md proscribe.

#### H-284 · Conclusiones, Objetivo específico 3, p. 104 (PDF p.120) · severidad baja

**La trazabilidad depende de una decisión en el OE3 y de tres en los Aportes**

- **Dice:** «es la decisión de diseño de la que depende la trazabilidad» vs. Aportes, p. 106 (PDF p.122): «tres decisiones que hacen trazable un software de elementos finitos y que pueden reutilizarse»
- **Versión calibrada:** Borrar del OE3 el inciso «: es la decisión de diseño de la que depende la trazabilidad», que además es la aparición redundante señalada en el hallazgo sobre los módulos; el aporte segundo ya enuncia las tres decisiones.

#### H-285 · Recomendaciones, «Guía de uso en la cátedra», p. 109 (PDF p.125) · severidad baja

**«El manual del Anexo B enseña a operar el software»: verbo de enseñanza**

- **Dice:** «El manual del Anexo B enseña a operar el software. Conviene acompañarlo con una guía docente que proponga una secuencia de prácticas.»
- **Versión calibrada:** Sustituir por: «El manual del Anexo B describe la operación del software.»

#### H-005 · Resumen, p. i (PDF p.2) y §3.7.1 «Alcances», p. 96 (PDF p.112) · severidad baja

**El Resumen omite el subindice de la tension normal (sigma_x) que el cuerpo si escribe**

- **Dice:** «los errores frente a la solución analítica fueron del 0,04 % en la tensión normal y del 0,26 % en la flecha»
- **Versión calibrada:** Anadir el subindice en el Resumen: «del 0,04 % en la tension normal sigma_x». Nada mas. NO mencionar tau_xy: es tension CORTANTE, no normal, y la Nomenclatura (p. xi) las distingue; el 2,89 % es irrelevante para esta frase. El cuerpo ya esta bien: §3.7.1 (p. 95) escribe «0,04 % en la tension normal sigma_x ... y de hasta el 2,9 % en la tension cortante», y las Conclusiones (p. 104) tambien.

#### H-007 · «Justificación», plano académico, p. 4 (PDF p.20) · severidad baja

**«La literatura... reporta que... favorecen la instrucción»: afirmación de efecto, sin ninguna cita**

- **Dice:** «La literatura sobre enseñanza del método reporta que la simulación interactiva y la construcción paso a paso de las herramientas de cálculo favorecen la instrucción, con las salvedades que examina la Sección 1.2.»
- **Versión calibrada:** La reescritura propuesta sirve; conservar tal cual la remisión «con las salvedades que examina la \autoref{sec:fundamentos-pedagogicos}», que es lo que calibra la frase, y usar «\autocites[p.~157]{lee2015interactive}[p.~872]{lee2015eigenmodes}[p.~2]{bishay2020teaching}», los mismos localizadores del primer principio de §1.2.

#### H-281 · «Alcance y limitaciones», p. 9 (PDF p.25) · severidad baja

**«El plano es la mínima dimensión en la que aparece el carácter de continuo» es falso en sentido estricto**

- **Dice:** «El plano es la mínima dimensión en la que aparece el carácter de continuo y, a la vez, conserva matrices de tamaño legible»
- **Versión calibrada:** Sustituir por: «El plano es la mínima dimensión en la que aparecen el mapeo isoparamétrico, la matriz Jacobiana y la cuadratura en dos direcciones y, a la vez, conserva matrices de tamaño legible —D de 3x3 y B de 3x8 en el elemento Q4—, lo que permite exhibir cada operación.»

#### H-275 · §2.2.6 «Módulos educativos», p. 69 (PDF p.85) · severidad baja

**«Garantiza» sin la fórmula «por construcción» que el propio CRITERIOS exige, en dos lugares**

- **Dice:** «la regla evita que dos representaciones compitan por el mismo lienzo y garantiza que lo resaltado sobre la malla corresponda siempre a un único análisis»
- **Versión calibrada:** Sustituir por: «la regla evita que dos representaciones compitan por el mismo lienzo y hace que, por construcción, lo resaltado sobre la malla corresponda siempre a un único análisis». En §2.2.8, sustituir «recalculada con las mismas funciones del motor para garantizar consistencia con los módulos educativos» por «recalculada con las mismas funciones del motor, lo que asegura por construcción su consistencia con los módulos educativos».

---

## Preguntas de defensa

Treinta y ocho preguntas, ordenadas por riesgo. Cada una trae **dónde la responde el documento**
y **la respuesta preparada**, escrita y apoyada en cifras y páginas concretas, para estudiar.

| Estado | Nº | Qué hacer |
|---|---|---|
| **RESPONDIDA** | 10 | Aprenderse la página y la frase. La respuesta ya está escrita en la tesis. |
| **PARCIAL** | 20 | Falta un dato. Casi todas se cierran con las correcciones de B1 a B5. |
| **SIN RESPUESTA** | 8 | Seis se arreglan escribiendo; dos se contestan de viva voz. |

**Las tres que hay que tener preparadas palabra por palabra**, porque van al corazón del trabajo
y el documento hoy no las responde:

1. *«Usted dice que la memoria puede reproducirse a mano. ¿Dónde está el cálculo manual?»*
   Se cierra con B2. Mientras tanto, la respuesta honesta es que el Anexo G desarrolla cada
   etapa con su ecuación de origen de modo que **pueda** rehacerse, y que la comprobación
   efectiva se hizo: det **J** = 4,7604, las reacciones suman 1000,00 contra la carga aplicada, y
   la matriz de extrapolación es la inversa exacta de **M**.
2. *«¿Cómo modeló los apoyos y con qué discretización resolvió en SAP2000?»*
   Se cierra con B3. No hay manera de contestarla bien sin haberlo escrito antes.
3. *«¿Bajo qué licencia se publica EduFEM y de quién son los derechos?»*
   Se cierra con H-020. El repositorio ya lleva MIT; lo que falta es decirlo en la tesis y
   resolver la tensión con la AGPL de PyMuPDF.


### Riesgo alto

#### PD-03 · SIN RESPUESTA · *estructuralista*

> **¿Cómo impuso los apoyos y la carga de la viga en un continuo bidimensional? ¿Restringió un nodo, una arista? ¿Y con cuántos elementos shell y qué versión la resolvió en SAP2000?**

**Dónde está en el documento.** §3.4, pp. 80-81 (PDF pp. 96-97), describe geometría, material y malla —«una única malla Q9 estructurada de 56 × 8 elementos (448 elementos, 1921 nodos, 3842 GDL)»— pero no dice cómo se restringió ni cómo se aplicó la carga. El Anexo E, p. 145 (PDF p. 161) y p. 147 (PDF p. 163), solo declara «La estructura se modelo en el programa sap2000 con elementos Shell», sin número, tamañ…

**Qué falta.** Declarar en §3.4 los GDL restringidos en cada apoyo, la forma de aplicación de la carga, y —del modelo de SAP2000— versión, número, tamaño y espesor de los elementos shell. Las capturas del Anexo E ya lo muestran; falta la declaración numérica.

**Respuesta preparada.** El apoyo fijo restringe los dos grados de libertad del nodo del extremo izquierdo a la altura del eje neutro, y el apoyo móvil restringe solo el desplazamiento vertical del extremo derecho; la carga uniforme q = 5000 kgf/m se aplicó como carga superficial sobre la arista superior, convertida a fuerzas nodales equivalentes con la formulación de la Sección 1.10, que es la misma que usa el motor. La prueba de que la carga entró correctamente es el equilibrio: las reacciones verticales suman los 70 000 kgf de qL con un residuo relativo de 1,7 × 10⁻¹³, y la suma horizontal es nula a precisión de máquina; está en la página 82. Los tres puntos de control A, B y C están alejados de los apoyos, de modo que la singularidad local que introduce un apoyo puntual no los contamina. El modelo de SAP2000 está documentado en el Anexo E, páginas 145 a 147, con sus capturas, y admito que allí falta declarar por escrito el número de elementos shell y la versión del programa: es una carencia de reproducibilidad que corrijo con dos renglones.

#### PD-04 · SIN RESPUESTA · *director de carrera*

> **¿Bajo qué licencia concreta se publica EduFEM, y de quién son los derechos sobre un software desarrollado como trabajo de grado en esta Universidad?**

**Dónde está en el documento.** El documento afirma seis veces que el software es «libre y de código abierto» —Resumen p. i; §1.1 p. 15 (PDF p. 31); Tabla 1.1, fila «Licencia», p. 16 (PDF p. 32); §2.2.1 p. 53; Conclusiones p. 106— pero no nombra ninguna licencia en sus 187 páginas. La nota de la Tabla 2.5, p. 57 (PDF p. 73), deja el asunto en futuro: «una licencia recíproca como la AGPL condiciona los términ…

**Qué falta.** Nombrar la licencia en el documento, decir quién conserva los derechos y resolver por escrito la relación entre el código MIT y la AGPL de PyMuPDF en la distribución binaria.

**Respuesta preparada.** El código propio de EduFEM se publica bajo licencia MIT: está en el archivo LICENSE del repositorio público que cito en la página 4, de modo que la Carrera puede usarlo, modificarlo y redistribuirlo sin depender de mí. La nota de la Tabla 2.5, en la página 57, advierte que PyMuPDF se distribuye bajo AGPL-3.0 o licencia comercial, y por eso conviene distinguir dos cosas: el código que yo escribí, que es MIT, y el paquete binario que incorpora esa biblioteca, que queda sujeto además a sus términos. Ninguna dependencia exige pago ni licencia comercial al estudiante, que es lo que el requisito 5 pedía y lo que la fila «Licencia» de la Tabla 1.1 consigna. Reconozco que el documento dice que la licencia «debe elegirse» cuando en realidad ya está elegida, y lo correcto es nombrarla en la Tabla 1.1, en la nota de la Tabla 2.5 y en el Anexo A.

#### PD-08 · SIN RESPUESTA · *estructuralista*

> **En la Tabla 3.7 usted acredita como «Instrumento de EduFEM» una extrapolación de Richardson. ¿Dónde está esa función en el programa? ¿Me la puede mostrar?**

**Dónde está en el documento.** Tabla 3.7, fila FEA30, p. 91 (PDF p. 107): «Secuencias de malla con la diferencia entre mallas sucesivas como regla de parada, y extrapolación de Richardson para estimar el límite». El software no la implementa —comprobado en el repositorio: cero apariciones de «Richardson» en el código del proyecto—, y el propio documento lo dice en la p. 39 (PDF p. 55): «se corrobora en este…

**Qué falta.** Quitar «y extrapolación de Richardson para estimar el límite» de la celda de instrumento de FEA30 y moverla a la evidencia, declarando que la aplicó el autor.

**Respuesta preparada.** Tiene razón en la mitad de esa celda, y la corrijo. Lo que el software hace es generar las secuencias de malla y mostrar la diferencia entre mallas sucesivas, que es la regla de parada, y la aplica el usuario sobre su propio modelo: así lo declaro en la salvedad de la página 93. La extrapolación de Richardson la hice yo, fuera de la herramienta, y lo digo textualmente en la página 39 y en la página 84, donde la llamo «extrapolación de Richardson propia»; por tanto debe pasar a la columna de evidencia como procedimiento del autor, no figurar como instrumento del software. El ítem FEA30 sigue cubierto por lo que el software sí ejecuta: la secuencia de cinco mallas de la Tabla 3.4, con sus grados de libertad y sus errores. Es una corrección de un renglón, y es el único flanco real del «18 de 18».

#### PD-11 · SIN RESPUESTA · *estructuralista*

> **Usted dice que la memoria entrega «el procedimiento completo, con todas sus magnitudes intermedias». ¿También para el modelo de la viga, que tiene 448 elementos y 3842 grados de libertad?**

**Dónde está en el documento.** §2.2.8, p. 71 (PDF p. 87): «entrega el procedimiento completo, con todas sus magnitudes intermedias, en un documento que puede rehacerse a mano»; y §3.8, p. 100 (PDF p. 116): «Cada resultado que el software entrega puede seguirse hacia atrás, etapa por etapa, hasta los datos del modelo». El código impone límites que el documento no declara en ninguna página: el desarrollo ínte…

**Qué falta.** Declarar en §2.2.8 los límites reales del desarrollo íntegro (2 Q4 / 1 Q9, elemento de máxima energía por encima, K literal hasta 18 GDL) y acotar el universal de §3.8.

**Respuesta preparada.** No de esa manera, y ese límite debe estar escrito en el documento. La memoria desarrolla íntegramente todos los elementos mientras el modelo no supere dos elementos Q4 o uno Q9; por encima de ese tamaño desarrolla paso a paso el elemento de mayor energía de deformación, que es el más solicitado, y presenta la matriz global por su patrón de dispersión y sus indicadores en lugar de sus coeficientes, a partir de dieciocho grados de libertad. Es una decisión de diseño deliberada: una memoria que imprimiera literalmente una matriz de 3842 por 3842 dejaría de ser cotejable por nadie, y el propósito del documento es justamente que pueda seguirse. Lo que se conserva en un modelo grande es la cadena completa de las nueve etapas sobre un elemento representativo, recalculada con las mismas funciones del motor. La corrección es acotar la frase de la página 71 y declarar allí ese límite.

#### PD-13 · SIN RESPUESTA · *estructuralista*

> **En el Anexo G propone leer las cifras en kN y cm. Eso da un módulo de 225 000 kN/cm², más de dos millones de megapascales, y una tensión máxima de 8647 MPa. ¿Qué material es ése?**

**Dónde está en el documento.** Encabezado del Anexo G, p. 164 (PDF p. 180): «Las magnitudes se expresan en un sistema de unidades coherente y arbitrario (por ejemplo, kN y cm, con E en kN/cm2)», junto a E = 225000 en la Tabla G.3, p. 165 (PDF p. 181), y σVM,máx = 864,70 en la Tabla G.5, p. 170 (PDF p. 186). No hay ninguna aclaración posterior.

**Qué falta.** Sustituir el ejemplo «kN y cm» por «kgf y cm, con E en kgf/cm²: E = 225000 kgf/cm², del orden de un hormigón de resistencia media». No tocar ninguna cifra.

**Respuesta preparada.** El ejemplo de unidades que puse está mal elegido y lo corrijo: con kgf y cm, E = 225 000 kgf/cm² es del orden de un hormigón de resistencia media, y la tensión máxima de von Mises, 864,70 kgf/cm², resulta una cifra plausible. Ninguna cifra del anexo cambia, porque el modelo es dimensionalmente coherente y el propósito del ejemplo es mostrar la cadena de sustitución numérica etapa por etapa, no dimensionar una pieza. Por eso el texto dice «un sistema de unidades coherente y arbitrario»: lo que hay que cambiar es el paréntesis que da el ejemplo, un renglón de la página 164. Le agradezco la observación, porque el objetivo del anexo es precisamente que un ingeniero civil pueda leerlo sin tropiezos.

#### PD-01 · PARCIAL · *estructuralista*

> **Usted repite —en el resumen, en la hipótesis y en las conclusiones— que la memoria de cálculo «puede reproducirse a mano». ¿La reprodujo usted? ¿Dónde está ese cálculo manual y su cotejo con la salida del programa?**

**Dónde está en el documento.** La promesa está en el Resumen, p. i (PDF p. 2): «una memoria de cálculo automática que puede reproducirse a mano», y la condición de refutación en la Introducción, p. 7 (PDF p. 23): «…o una memoria que no cierre con el cálculo manual». El criterio que efectivamente se aplica es más débil: Tabla 2.4, p. 52 (PDF p. 68), «Etapas de la memoria desarrolladas con sustitución numéric…

**Qué falta.** El documento no reporta ningún cálculo manual ejecutado y cotejado. Hay que alinear la glosa de refutación de la p. 7 y el indicador de la Tabla 2.2 (p. 45, «reproducción manual de la memoria») con el criterio real de la Tabla 2.4, o bien añadir un apartado G.4 con una etapa rehecha a mano y su dif…

**Respuesta preparada.** Lo que mi criterio mide, fijado de antemano en la Tabla 2.4 de la página 52, es que cada etapa de la memoria esté desarrollada con sustitución numérica y remitida a su ecuación, de modo que pueda rehacerse a mano; eso es lo que verifico sobre el Anexo G y lo que reporto en la Tabla 3.10 de la página 100. Y puedo demostrarlo ahora: en la página 167, el Jacobiano del elemento E3 sale de sustituir las coordenadas de los nodos 4-5-8-7 y las derivadas de las funciones de forma en el punto de Gauss (−1/√3, −1/√3), y su determinante da 4,7604, que es el número impreso. Rehice a mano, para preparar esta defensa, la matriz constitutiva D, ese Jacobiano, la extrapolación a los nodos y el equilibrio de reacciones, y las cuatro cierran con las cifras del anexo. Reconozco que la frase de la página 7 —«una memoria que no cierre con el cálculo manual»— promete un acto de comprobación que el criterio no exige, y lo correcto es alinear esa frase con lo que la Tabla 2.4 ya dice.

#### PD-02 · PARCIAL · *director de carrera*

> **Usted sitúa el problema «en la Carrera de Ingeniería Civil de la Universidad Autónoma Tomás Frías, gestión 2026». ¿Qué dato tomó aquí? ¿Revisó el plan de estudios, habló con algún docente, vio qué software se usa?**

**Dónde está en el documento.** El planteamiento del problema, p. 2 (PDF p. 18), se respalda solo con fuentes externas: un consenso de expertos mexicanos [3, pp. 1159, 1171] y ED-Elas2D, Barcelona 1998 [6]. No hay un solo dato tomado en la Carrera. La respuesta sí está escrita, en tres lugares: Delimitación, p. 3 (PDF p. 19), «Ambas variables se observan en el software y en los casos de estudio, no en person…

**Qué falta.** Si existe documentación disponible —plan de estudios vigente, programa analítico de la asignatura donde se aborda el análisis matricial o por elementos finitos—, tres renglones de anclaje documental en la p. 2 cerrarían la pregunta. No debe inventarse el dato: el argumento no depende de él.

**Respuesta preparada.** El problema que formulo no es una carencia medida en la Carrera: es una propiedad del medio de cálculo —que el software de uso corriente devuelve el resultado sin el procedimiento—, y la documento con la matriz de la Tabla 1.1, en la página 16, y con la literatura que cito. La Carrera entra como destinataria y contexto de aplicación, y lo declaro expresamente tres veces: en la delimitación de la página 3, en la página 47 —«delimita el contexto de aplicación del trabajo; no es su población»— y en las conclusiones de la página 102. Por eso mis dos variables se observan sobre el software y sobre los tres casos de estudio, no sobre personas, y nunca afirmo un efecto sobre estudiantes. Medir qué ocurre cuando la herramienta entra en un curso es una investigación distinta, de carácter educativo, y la dejo recomendada en la página 110.

#### PD-05 · PARCIAL · *metodologo*

> **Los umbrales del 3 %, del 1 % y del 1,5 % dicen «tolerancia de ingeniería fijada por el autor». ¿En qué norma o referencia se apoyan esos valores? ¿No fijó usted la vara a la medida de lo que iba a saltar?**

**Dónde está en el documento.** Tabla 2.4 (continuación), p. 52 (PDF p. 68): las tres filas llevan en la columna «Procedencia del umbral» la leyenda «Tolerancia de ingeniería fijada por el autor». §2.1.6, p. 51 (PDF p. 67), sí declara la anterioridad: «Unos y otros quedaron fijados antes de las corridas que este documento reporta». Las Limitaciones, p. 107 (PDF p. 123), lo reconocen: «El motor, los guiones d…

**Qué falta.** Una nota al pie de la Tabla 2.4 que explique qué es una tolerancia de ingeniería —un umbral de aceptación fijado de antemano, no una estimación de exactitud— y por qué el escalonamiento entre 1 %, 1,5 % y 3 %.

**Respuesta preparada.** Los umbrales son criterios de aceptación, no estimaciones de exactitud, y lo que la metodología les exige es que se fijen antes de medir: lo declaro en la página 51 —«quedaron fijados antes de las corridas que este documento reporta»— y publico junto a cada uno la columna «Lo refutaría», que es la condición de falsación. Los valores están escalonados por la naturaleza de cada magnitud: 1 % para la tensión normal, que es la magnitud de diseño y se contrasta contra una solución analítica cerrada y contra un modelo comercial; 3 % para la flecha; y 1,5 % para Cook, cuya referencia no es exacta. Lo observado queda entre diez y veinticuatro veces por debajo —0,0414 % contra el 1 %, 0,2633 % contra el 3 % y 0,144 % contra el 1,5 %—, de modo que con umbrales de 0,5 % y 1 % los tres criterios seguirían cumpliéndose con los mismos datos. Y aclaro que el criterio del equilibrio, menor que 10⁻⁸, no es una tolerancia de ingeniería sino el orden del cero numérico del motor, y el observado fue 1,7 × 10⁻¹³.

#### PD-06 · PARCIAL · *metodologo*

> **Los seis criterios de trazabilidad dan el cien por ciento, sin una sola excepción. Quien definió el universo, construyó el instrumento y marcó las casillas es la misma persona. ¿Qué podía salir mal?**

**Dónde está en el documento.** Tabla 3.10, bloque «Cláusula (a)», pp. 99-100 (PDF pp. 115-116): seis filas en las que el umbral repite literalmente lo observado («7 de 7 | 7 de 7», «9 de 9 | 9 de 9», «18 de 18 | 18 de 18»). El documento ya acota el alcance en §3.6.2, p. 92 (PDF p. 108): «Conviene decir qué prueba y qué no prueba ese resultado», y en Limitaciones, p. 107 (PDF p. 123): «La tabla de cobertura…

**Qué falta.** Una nota en la Tabla 3.10 que recuerde que los seis criterios son de exhaustividad y qué refutaría a cada uno, remitiendo a la Tabla 2.4. No conviene usar FEM3 como si hubiera sido un fallo detectado al medir: se excluyó del universo a priori.

**Respuesta preparada.** Que los seis criterios se cumplan no se sigue de cómo los definí, y eso es lo que vuelve auditable el cotejo: las nueve etapas son las del Capítulo 1 y no se inventaron para la ocasión, los dieciocho ítems proceden de un consenso publicado de 67 expertos que es ajeno a mí, y la regla de marcado está escrita en la Subsección 2.1.5, de modo que un tercero puede rehacer el cotejo ítem por ítem y discrepar. Son criterios de exhaustividad: bastaba una etapa sin instrumento, un ítem sin cobertura o una fase fuera del lienzo para refutarlos, y la Tabla 2.4 lo enuncia criterio por criterio en la columna «Lo refutaría». Declaro además la limitación en la página 107: es un cotejo del autor, no el juicio de un panel independiente. Y donde el trabajo sí podía fallar contra un patrón ajeno a mí —las tasas de convergencia, Timoshenko-Goodier, el 23,965 de Štembera y Füssl— no falló, y esa es la cláusula (b).

#### PD-07 · PARCIAL · *metodologo*

> **El resumen dice «los dieciocho contenidos que un consenso publicado de expertos exige». ¿El consenso enumera dieciocho, o fue usted quien eligió dieciocho?**

**Dónde está en el documento.** Resumen, p. i (PDF p. 2): «los dieciocho contenidos que un consenso publicado de expertos exige tienen instrumento en el software, según el cotejo del autor». El recorte real sí se declara en §2.1.4, p. 49 (PDF p. 65) y en la nota de la Tabla 3.7, p. 92 (PDF p. 108), donde se lee «No expuesto por el software (1): la deducción de la matriz de rigidez por métodos alternativos (F…

**Qué falta.** El Resumen no dice 18 de 49, y el criterio de exclusión de FEM3 usa al propio software como filtro. Hay que declarar la proporción en el Resumen y reformular la exclusión de FEM3 por su carácter teórico, dejando constancia del 18 sobre 19.

**Respuesta preparada.** El consenso enumera 49 contenidos y yo retengo 18, con el recorte declarado ítem por ítem en la nota de la Tabla 3.7, página 92: 18 quedan fuera por alcance disciplinar —resortes, barras, placas, cáscaras—, 12 por ser previos al procedimiento de cálculo, y 1, FEM3, la deducción de la matriz de rigidez por métodos alternativos, por ser un desarrollo teórico y no una etapa del cálculo. Admito que FEM3 es además el único ítem que el software no expone: contado dentro del universo, la cobertura sería de 18 sobre 19, y así conviene decirlo para que la exclusión no dependa del propio software. El Capítulo 3 hace la declaración completa y auditable; lo que debe corregirse es la síntesis de la primera página, que debe decir «de los cuarenta y nueve contenidos que enumera el consenso, los dieciocho que corresponden al alcance de EduFEM tienen instrumento». La tabla no pondera importancia: solo registra si el ítem tiene o no instrumento identificable.

#### PD-09 · PARCIAL · *director de carrera*

> **El título dice «software educativo». ¿Cómo sostiene ese adjetivo si no midió a ningún estudiante?**

**Dónde está en el documento.** El adjetivo está en el título, en el Resumen y en las palabras clave (p. i, PDF p. 2) y aparece ocho veces en el documento sin definición operativa en ninguna. La decisión metodológica sí está fundada: §2.1.1, p. 42 (PDF p. 58), «Esa evaluación es una validación de laboratorio», con Wieringa [25, p. 30]; §1.2, p. 19 (PDF p. 35), acota las fuentes pedagógicas («con una evaluaci…

**Qué falta.** Una definición operativa breve de «software educativo» en la Introducción o en §2.2.1, que lo declare propiedad del producto y no efecto sobre el usuario.

**Respuesta preparada.** «Educativo» califica aquí al propósito de diseño del producto —exponer el procedimiento de cálculo además de entregar el resultado—; es una propiedad del software, verificable en él, y no un efecto medido sobre quien lo usa. Por eso lo que mido es qué expone la herramienta y con qué exactitud, y en ningún punto afirmo que el estudiante aprenda o comprenda mejor: al contrario, en la página 19 acoto que las fuentes pedagógicas que cito reportan evaluaciones cualitativas sobre sus propios cursos y sin grupo de comparación. Metodológicamente esto es lo que Wieringa llama validación de laboratorio, y lo declaro en la página 42; en la página 102 digo expresamente que queda fuera de lo medido qué ocurre cuando la herramienta se pone en manos de un curso. Medir el efecto exige un diseño con grupos y pre y post-test: es otra investigación, y la dejo recomendada en la página 110.

#### PD-12 · PARCIAL · *estructuralista*

> **Usted ofrece la herramienta para secciones de presas, muros de contención y túneles, que son deformación plana. ¿Validó alguno de esos casos contra una referencia externa?**

**Dónde está en el documento.** Alcance, p. 8 (PDF p. 24): «en deformación plana, las secciones de presas, de muros de contención y de túneles, donde una rebanada representa todo el sólido». Limitaciones, p. 108 (PDF p. 124): «La deformación plana solo se verifica con el método de soluciones manufacturadas: los dos casos de contraste externo son de tensión plana, y la viga de Timoshenko se resolvió únicament…

**Qué falta.** El párrafo del Alcance enumera las tres tipologías sin remitir al límite. Basta un inciso: «la verificación de ese estado se realizó con soluciones manufacturadas, y el contraste con referencias externas quedó restringido a la tensión plana (véase Limitaciones)».

**Respuesta preparada.** La deformación plana no quedó sin verificar: se verifica con el método de soluciones manufacturadas en las cuatro configuraciones ensayadas, incluida la malla distorsionada, y el motor alcanza allí las mismas tasas teóricas que en tensión plana, con diferencias por debajo de 0,01. Es la prueba más severa que existe, porque la solución exacta se conoce punto a punto y una tasa por debajo de la teórica delata un defecto de implementación. Lo que falta es el contraste con una referencia externa publicada en deformación plana, y lo declaro como limitación en la página 108 y lo convierto en recomendación concreta en la página 109: un caso civil con peso propio, una presa de gravedad o un muro de contención. Conviene tener presente que entre los dos estados planos cambia una sola matriz, la constitutiva D de la Ecuación 1.5, y esa matriz está verificada.

#### PD-14 · PARCIAL · *director de carrera*

> **¿Qué recibe la Carrera con este trabajo? ¿Quién va a usar el programa, y con qué compromiso?**

**Dónde está en el documento.** Recomendaciones, «Guía de uso en la cátedra», p. 109 (PDF p. 125): «El manual del Anexo B enseña a operar el software. Conviene acompañarlo con una guía docente que proponga una secuencia de prácticas», y enumera tres prácticas inmediatas. No hay constancia en el documento de entrega del software a la cátedra, ni de un plan de implantación: el aporte institucional queda enunci…

**Qué falta.** Entregar formalmente el instalador y el manual a la Dirección de Carrera o al docente de la asignatura antes de la defensa, y guardar la constancia; escribir las tres prácticas de la p. 109 como documento entregable.

**Respuesta preparada.** La Carrera recibe un producto terminado, no un prototipo: un instalador para Windows que no requiere privilegios de administrador, ni licencia, ni laboratorio, ni conexión a internet, y que lleva dentro el intérprete y todas las bibliotecas, de modo que se instala en la computadora de cada estudiante. Lo entrego junto con el manual de instalación del Anexo A, el manual de uso del Anexo B y el código fuente público bajo licencia libre, de modo que la Carrera puede mantenerlo y extenderlo sin depender de mí. En la página 109 propongo tres prácticas inmediatas: construir y resolver el ejemplo canónico y rehacer a mano una etapa de su memoria de cálculo; recorrer los módulos M1 a M7 sobre un elemento propio; y convertir un modelo de Q4 a Q9 y refinar la malla sobre la membrana de Cook para observar el bloqueo por cortante. Estoy en condiciones de entregar hoy mismo el instalador y esas tres prácticas a la Dirección de Carrera.

#### PD-15 · PARCIAL · *metodologo*

> **Su hipótesis dice «elevando la trazabilidad y la verificabilidad». ¿Elevándola respecto de qué medición previa? ¿Midió usted el nivel de partida?**

**Dónde está en el documento.** Hipótesis, p. 6 (PDF p. 22), y Resumen, p. i (PDF p. 2): «su desarrollo permitirá mejorar la forma en que el software expone el procedimiento de cálculo, elevando la trazabilidad y la verificabilidad del análisis». El nivel de referencia se declara pero no se cuantifica: §2.1.2, p. 43 (PDF p. 59), «El nivel de caja negra es el de referencia y se documenta con la matriz de atri…

**Qué falta.** Una oración en §2.1.2 que declare que la comparación es de presencia frente a ausencia y no de grado.

**Respuesta preparada.** El nivel de referencia es el de caja negra, está declarado en la página 43 y documentado con la matriz de atributos de la Tabla 1.1, en la página 16. Esa comparación es de presencia frente a ausencia, no de grado: ninguno de los recursos revisados expone las matrices intermedias sobre el modelo del propio usuario ni emite una memoria de cálculo que pueda rehacerse a mano, y las filas «Cálculo paso a paso» y «Memoria de cálculo» de esa tabla lo muestran producto por producto. No cuantifico esos programas con mis indicadores porque no los examiné de primera mano, y en la página 14 declaro expresamente que los atributos que exigirían examinar cada producto quedan sin evaluar; fabricar esa cifra sería menos defendible que la palabra «elevando». La elevación que la hipótesis enuncia es, por tanto, una propiedad del medio de cálculo, no un efecto sobre personas.

#### PD-16 · PARCIAL · *metodologo*

> **Si el software está hecho para mostrar los pasos, ¿no es obvio que el análisis resulte trazable? ¿No está usted comprobando una tautología?**

**Dónde está en el documento.** §3.8, p. 101 (PDF p. 117): «La Subsección 3.7.2 muestra que esa relación no es una tautología: la trazabilidad hizo visible un defecto de exactitud que las métricas agregadas no delataban, y ese defecto pudo corregirse». El respaldo es un episodio único del propio desarrollo, relatado en §3.7.2, p. 96 (PDF p. 112), y el verbo «muestra» lo presenta como demostración.

**Qué falta.** Rebajar el verbo «muestra» en §3.8 y declarar que es un caso único ocurrido durante el desarrollo, no una medición.

**Respuesta preparada.** No, y la prueba está dentro del propio trabajo: exponer el procedimiento no garantiza que lo expuesto sea correcto, y así lo digo ya en la página 7. Durante el desarrollo, la matriz de extrapolación de tensiones del elemento Q4 estaba escrita para otra numeración de los puntos de Gauss, y ese defecto pasó inadvertido para tres estudios de convergencia del desplazamiento; lo delató la lectura de la memoria de cálculo, al ver que las tensiones nodales no cerraban con las de los puntos de Gauss. Lo cuento en la Subsección 3.7.2, página 96, y por eso la batería incorpora hoy una prueba de reproducción exacta de campos polinómicos, que comprueba ese operador con independencia del tamaño de malla. En un software de caja negra ese defecto habría sido invisible para quien lo usa; aclaro que es un episodio único de mi propio desarrollo y lo presento como indicio fuerte, no como medición repetida.

#### PD-10 · RESPONDIDA · *estructuralista*

> **Tome la tiza. Saque usted, aquí, un número del Anexo G a partir de los datos del problema.**

**Dónde está en el documento.** Anexo G, pp. 164-171 (PDF pp. 180-187). En p. 167 (PDF p. 183): «J = ∂Nξη Xe = [[2,1830, 0,3943],[1,1830, 2,3943]], det J = 4,7604, J⁻¹ = [[0,50297, −0,08284],[−0,24851, 0,45858]]». La aritmética del anexo se rehízo íntegramente y cierra en todo lo comprobable a mano: E/(1−ν²) = 234 375, ΣRy = 1000,00, ΣRx = 0,00, radio de Mohr 200,817, σVM = 417,76, y la matriz de extrapolaci…

**Respuesta preparada.** Con gusto, y lo hago con el elemento E3 y el primer punto de Gauss, que es lo que cabe en la pizarra. Con E = 225 000 y ν = 0,20, E/(1−ν²) = 234 375, de donde D₁₁ = 234 375, D₁₂ = 46 875 y D₃₃ = 93 750, que es la matriz constitutiva impresa en el anexo. Sustituyendo las coordenadas de los nodos 4-5-8-7 y las derivadas de las funciones de forma evaluadas en (−1/√3, −1/√3) —que valen ±0,3943 y ±0,1057— obtengo el Jacobiano [[2,1830 0,3943],[1,1830 2,3943]], cuyo determinante es 4,7604, exactamente el número de la página 167. Y hay una comprobación global que puede hacerse sin calculadora: las tres reacciones verticales de la página 170 —334,24, 601,37 y 64,39— suman los 1000 de la carga aplicada, y las horizontales, 80,11, −209,93 y 129,82, suman cero.


### Riesgo medio

#### PD-19 · SIN RESPUESTA · *estructuralista*

> **Su flecha calculada es mayor que la analítica y que la de SAP2000, y su error en desplazamiento es diez veces el de la tensión. ¿Por qué? El método de los desplazamientos debería quedarse corto.**

**Dónde está en el documento.** Tabla 3.3, p. 82 (PDF p. 98): EduFEM da |v|(0;0) = 2,03460 frente a 2,02926 de la solución analítica, con 0,2633 % de error, y 2,03101 frente a 2,02310 de SAP2000, con 0,3912 %. El documento reporta las cifras pero no explica el signo de la diferencia. Nota: la advertencia sobre las componentes secundarias sí está declarada en la p. 82.

**Qué falta.** Una oración tras la Tabla 3.3 que explique el signo de la diferencia por la realización de los apoyos en el continuo bidimensional.

**Respuesta preparada.** La regla de que el método de los desplazamientos subestima la flecha vale para un modelo cuya cinemática sea más rígida que la exacta, y ese no es el caso aquí: la solución de Timoshenko y Goodier supone en los extremos una distribución de cortante determinada, mientras que en mi modelo bidimensional el apoyo se realiza sobre nodos a la altura del eje neutro, lo que introduce una flexibilidad local que la referencia no tiene. Por eso la diferencia es de 0,26 %, y es del mismo orden que la diferencia entre las dos referencias entre sí. El error en desplazamiento es mayor que el de la tensión porque son magnitudes distintas: la tensión en A se compara contra un valor grande, 127,88 kgf/cm², mientras que la flecha integra el comportamiento de toda la viga, incluidas las condiciones de contorno. En todo caso ambos quedan muy por debajo de los umbrales fijados de antemano, 3 % para la flecha y 1 % para la tensión.

#### PD-28 · SIN RESPUESTA · *metodologo*

> **Busqué su referencia 16 en la revista y el artículo empieza en la página 1007. Usted cita la página 17. ¿De dónde sacó esa página?**

**Dónde está en el documento.** Entrada [16] en Referencias, p. 112 (PDF p. 128): «Computer Applications in Engineering Education 28.4 (2020), págs. 1007-1027». Las seis citas del cuerpo usan la paginación del manuscrito: «[16, pp. 5-6]» (§1.2), «[16, p. 17]», «[16, p. 2]», «[16, pp. 4-5, 13, 17]» (p. 19, PDF p. 35), y otras dos en §2.2.1 y §3.7. Comprobados los 134 pares cita-localizador del documento: 128…

**Qué falta.** Declarar en el .bib el ejemplar consultado (Early View, paginado 1-21) y quitar el rango 1007-1027, o convertir los seis localizadores a la paginación de la revista si puede comprobarse.

**Respuesta preparada.** Tiene razón y es un error mío de localizador: mi ejemplar de ese artículo es la versión en línea anticipada, paginada de 1 a 21, y los localizadores que escribí remiten a esa paginación y no a la de la revista impresa. La corrección es declararlo en la propia entrada bibliográfica, indicando que se consultó la versión anticipada con su paginación, en lugar de prometer un rango de páginas que no corresponde a lo citado. El contenido de lo que atribuyo a esa fuente no cambia. Es el único caso del documento: comprobados los ciento treinta y cuatro pares de cita y localizador, los otros ciento veintiocho caen dentro del rango de su entrada.

#### PD-30 · SIN RESPUESTA · *metodologo*

> **Su nomenclatura anuncia preguntas de investigación PI-1 a PI-3. ¿Dónde está la tercera?**

**Dónde está en el documento.** Nomenclatura, p. xv (PDF p. 16): «PI — Pregunta de investigación (PI-1 a PI-3)». Es la única aparición de «PI-3» en las 187 páginas: la Introducción, p. 7 (PDF p. 23), formula solo dos —«De esta hipótesis se desprenden dos preguntas de investigación, una por cláusula»— y la matriz de consistencia y §2.1.6 también usan solo dos.

**Qué falta.** Corregir la celda de la nomenclatura a «(PI-1 y PI-2)».

**Respuesta preparada.** No hay una tercera: es una errata de la nomenclatura. Las preguntas son dos, una por cláusula de la hipótesis, y así se enuncian en la página 7: PI-1 sobre trazabilidad y PI-2 sobre verificabilidad. Las dos se responden en la Sección 3.8, páginas 100 y 101, y se cierran en las conclusiones. La entrada debe decir «PI-1 y PI-2».

#### PD-17 · PARCIAL · *estructuralista*

> **Ese 0,04 % sale de una única malla de 56 × 8 elementos. ¿Qué habría dado con otra malla? ¿No es un resultado afortunado?**

**Dónde está en el documento.** §3.4, p. 81 (PDF p. 97): «este caso es un contraste puntual de exactitud sobre una malla fina y no un estudio de convergencia, y el refinamiento y la comparación Q4 frente a Q9 se reportan en las secciones del MMS y de la membrana de Cook». Limitaciones, p. 108 (PDF p. 124): «la viga de Timoshenko se resolvió únicamente con elementos Q9». No hay en el documento un segundo valo…

**Qué falta.** Un segundo y un tercer valor de σx con otra densidad de malla, en una tabla de tres filas del Anexo D.

**Respuesta preparada.** La malla de 56 × 8 se fijó antes de correr el caso, y el caso no se planteó como estudio de convergencia: lo declaro en la página 81. Esa función la cumplen los otros dos casos de estudio, con cinco mallas cada uno: las soluciones manufacturadas, donde mido tasas de 2,00 en L2 para el Q4 y 3,00 para el Q9, y la membrana de Cook, donde la secuencia Q9 va de 23,289 a 23,961 al refinar. Además la malla de la viga es fina —448 elementos Q9, 1921 nodos, 3842 grados de libertad— y el contraste es de exactitud puntual en tres puntos de control, no un agregado sobre el dominio, cosa que también declaro en la página 82. Correr el mismo caso con 28 × 4 y con 112 × 16 y tabularlo en el Anexo D es cuestión de minutos y cerraría la pregunta por escrito.

#### PD-18 · PARCIAL · *estructuralista*

> **Usted mismo encontró un error en su programa. ¿Cuántos más puede haber? ¿De cuántas pruebas consta esa batería de regresión?**

**Dónde está en el documento.** §3.7.2, p. 96 (PDF p. 112): «Durante el desarrollo se detectó y corrigió un defecto en la matriz de extrapolación del elemento Q4… las tasas de convergencia comprueban que no hay errores de orden en los mecanismos que intervienen en el desplazamiento, no que el motor esté libre de todo error». El documento no reporta en ninguna parte el número de guiones de la batería ni la po…

**Qué falta.** El número de guiones de la batería de regresión y qué componentes ejercita cada uno, en el Anexo D.1, declarando que es un recuento de guiones y no una medida de cobertura de código.

**Respuesta preparada.** No puedo afirmar que el motor esté libre de todo error, y lo digo expresamente en la página 96: las tasas de convergencia comprueban que no hay errores de orden en los mecanismos que intervienen en el desplazamiento, no que el programa sea correcto en todo. Lo que puedo afirmar es qué se comprueba y contra qué: tasas teóricas de convergencia en cuatro configuraciones con soluciones manufacturadas, contraste contra una solución analítica exacta y contra un programa comercial, un valor de referencia publicado, equilibrio global de reacciones con residuo de 1,7 × 10⁻¹³, e ida y vuelta de los formatos de intercambio sin pérdida. Y a raíz de ese episodio la batería incorpora una prueba nueva, de reproducción exacta de campos polinómicos, que comprueba el operador de extrapolación con independencia del tamaño de malla. Contar el propio defecto es, además, lo que distingue una verificación honesta de una demostración: la primera recomendación de la página 110 es someter el código a revisión por terceros.

#### PD-20 · PARCIAL · *estructuralista*

> **Aquí hay un 4,56 %. Ésa es la cifra más alta de toda su validación. ¿Por qué no aparece en el resumen ni en las conclusiones?**

**Dónde está en el documento.** §3.4, p. 82 (PDF p. 98): «En las componentes secundarias, cuya magnitud es entre seis y treinta y cinco veces menor que la de σx, los errores relativos crecen: en el punto B, 0,94 % en σy y 2,89 % en τxy frente a la solución analítica, y 4,56 % y 2,72 % frente a SAP2000». El texto explica la escala, pero no dice que esas componentes queden fuera del criterio de aceptación. El…

**Qué falta.** Precisar σx en el Resumen y en §3.7.1, y declarar tras la enumeración de la p. 82 que las componentes secundarias se reportan pero no forman parte del criterio de aceptación.

**Respuesta preparada.** Esa cifra está en el documento porque yo la reporto, en la página 82, y la reporto con su explicación: las componentes secundarias σy y τxy tienen en ese punto una magnitud entre seis y treinta y cinco veces menor que σx, de modo que un error absoluto pequeño produce un error relativo grande; σy vale allí −1,06 kgf/cm² frente a los −37,34 de σx. El criterio de aceptación que fijé de antemano en la Subsección 2.1.6 se establece sobre σx, que es la magnitud de diseño en un problema de flexión, y así consta en la Tabla 2.4. Además, el 4,56 % es diferencia contra SAP2000, no error: la nota de la Tabla 3.2 explica que ninguna de las dos formulaciones es el patrón de la otra. Lo que sí debo corregir es el Resumen: debe decir «0,04 % en la tensión normal σx», porque σy también es una tensión normal.

#### PD-27 · PARCIAL · *metodologo*

> **Su marco metodológico se apoya en una monografía inédita, sin editorial ni fecha. ¿Le parece una fuente suficiente para una tesis?**

**Dónde está en el documento.** Referencias, entrada [8], p. 111 (PDF p. 127): «Álvarez de Zayas C. “Metodología de la investigación científica”. Monografía inédita de 80 páginas, en formato electrónico (PDF fechado en 2007 según sus metadatos), empleada en la Carrera de Ingeniería Civil de la UATF como referencia del marco metodológico; sin lugar, editorial ni fecha declarados. [lugar desconocido]: [editori…

**Qué falta.** Una nota en la primera aparición de [8] (p. 3) que declare que se emplea solo por la terminología y no por el método.

**Respuesta preparada.** Esa monografía la cito cuatro veces y siempre por lo mismo: por la terminología con que esta Carrera pide que se formulen sus trabajos de grado —objeto de estudio, campo de acción, contradicción—, y así se ve en la página 3. El método de la investigación no sale de ahí: sale de la ciencia del diseño, con Hevner en MIS Quarterly, Peffers en el Journal of Management Information Systems y Wieringa en Springer, que son las referencias 11, 12 y 25. Las técnicas de verificación y validación salen de Oberkampf y Roy, de Cambridge University Press, que es la referencia 21. Declaro con precisión qué es esa fuente y de dónde procede precisamente para que pueda juzgarse su peso, que es el que le doy: terminológico.

#### PD-29 · PARCIAL · *metodologo*

> **¿Usted validó su software o lo verificó? Porque en el mismo capítulo emplea «validación» en más de un sentido.**

**Dónde está en el documento.** §1.13, p. 36 (PDF p. 52), fija una acepción única: «En lo que sigue, y en el resto del documento, “validación” designa ese contraste con referencias externas de exactitud conocida, es decir, con la solución analítica y con el modelo comercial». Pero §2.1.1, p. 42 (PDF p. 58), dice «Esa evaluación es una validación de laboratorio» (Wieringa), y el objetivo específico 5 se enunc…

**Qué falta.** Una excepción explícita en §1.13 que aclare el sentido del verbo en el enunciado del OE5 y en «validación de laboratorio».

**Respuesta preparada.** Las dos cosas, y las distingo con cuidado. Verificación es comprobar que las ecuaciones se resuelven bien —tasas de convergencia con soluciones manufacturadas, equilibrio de reacciones, reproducción exacta de campos polinómicos—, y ocupa las Secciones 3.2 y 3.3. Validación, en la acepción que fijo en la página 36, es el contraste con referencias externas de exactitud conocida: la solución analítica de Timoshenko-Goodier y el modelo de SAP2000, en la Sección 3.4, y el valor de referencia de Cook, en la 3.5. Y cito a Oberkampf y Roy para advertir que la comparación código a código no sustituye a la verificación rigurosa. Reconozco que el enunciado del quinto objetivo, «validar la propuesta», usa el verbo en su sentido metodológico corriente y no en esa acepción restringida, y conviene decirlo en una línea para que no haya ambigüedad.

#### PD-32 · PARCIAL · *estructuralista*

> **En el Anexo G habla de «apoyos empotrados» en tres nodos, pero los dibuja como articulaciones. En elasticidad plana el nodo no tiene giro: ¿qué empotró usted?**

**Dónde está en el documento.** Pie de la Figura G.1 y Tabla G.3, p. 165 (PDF p. 181): «apoyos empotrados en los nodos 1, 3 y 6» y «Apoyos | Nodos 1, 3, 6 (empotrados)». En la figura renderizada, los tres apoyos se dibujan con el glifo de articulación fija. La Tabla G.3 sí deja claro que se fijan los dos GDL.

**Qué falta.** Sustituir «empotrados» por la formulación en términos de GDL restringidos en el pie de la Figura G.1, en la Tabla G.3 y en el índice de figuras.

**Respuesta preparada.** Restringí los dos grados de libertad de traslación de esos tres nodos, ux = uy = 0, que es lo que la Tabla G.3 consigna. Tiene razón en que «empotrado» es impreciso: en elasticidad plana el nodo no tiene grado de libertad de giro, de modo que fijar sus dos traslaciones lo restringe por completo y no hay nada más que empotrar. La palabra correcta es «nodos con los dos grados de libertad de traslación restringidos», y así debe decir el pie de la figura y la fila de la tabla. El dibujo, con el glifo de articulación, es el que corresponde a lo que efectivamente se impuso.

#### PD-33 · PARCIAL · *director de carrera*

> **¿Qué es el «bloqueo por cortante» que su resumen presenta como resultado? Lo leo en la primera página y no sé si es bueno o malo.**

**Dónde está en el documento.** Resumen, p. i (PDF p. 2): «La membrana de Cook mostró el bloqueo por cortante del Q4 frente a la convergencia del Q9», sin glosa. La definición llega veintisiete páginas después, en §1.9, p. 28 (PDF p. 44): «Bajo flexión pura, una sección debería curvarse sin desarrollar deformación de corte; sin embargo, el campo de desplazamientos bilineal del Q4 no puede representar esa cur…

**Qué falta.** Glosar «bloqueo por cortante» y «lienzo» en el Resumen, que es la primera página que lee el tribunal.

**Respuesta preparada.** Es un defecto conocido del elemento más simple, el Q4: bajo flexión, su campo de desplazamientos bilineal no puede curvarse sin generar deformaciones de corte que no existen en la realidad; esas deformaciones falsas absorben energía y vuelven al elemento artificialmente rígido, de modo que subestima los desplazamientos. En la membrana de Cook se ve con números: con la malla más gruesa el Q4 da 11,845 frente al valor de referencia 23,96, es decir, más de un 50 % por debajo, mientras que el Q9 con la misma malla ya da 23,289. Que el software reproduzca ese fenómeno es un resultado de verificación, no un fallo: significa que el elemento se comporta como la teoría predice, y el estudiante puede verlo por sí mismo cambiando el tipo de elemento sobre el mismo modelo. Lo explico en la Sección 1.9, página 28, y admito que el resumen debería traer esa glosa en media línea.

#### PD-34 · PARCIAL · *director de carrera*

> **Dígame su objetivo general en una frase, sin leerlo.**

**Dónde está en el documento.** Objetivos, p. 5 (PDF p. 21). Es la oración más larga del documento: 100 palabras, contra el tope de ~60 que el propio autor se fijó; encadena producto, dominio, elementos, lenguaje, método de evaluación, referencias y finalidad sin un punto intermedio.

**Qué falta.** Partir la oración del objetivo general en dos o tres, dentro del tope de ~60 palabras que fija CRITERIOS.md.

**Respuesta preparada.** Desarrollar EduFEM, un software educativo de elementos finitos que expone el procedimiento de cálculo del análisis de elasticidad lineal plana con elementos Q4 y Q9. Lo implemento en Python y lo verifico y valido contra tres clases de referencia: soluciones manufacturadas, la solución analítica de Timoshenko y Goodier con un modelo equivalente en SAP2000, y la membrana de Cook. El propósito es que el análisis por el método de los elementos finitos resulte trazable y verificable paso a paso: que cada resultado pueda seguirse hacia atrás hasta los datos del modelo. Reconozco que, escrito, el objetivo es una sola oración demasiado larga y conviene partirlo en dos.

#### PD-21 · RESPONDIDA · *estructuralista*

> **¿Por qué SAP2000 le sirve de referencia, si también es una aproximación numérica y puede equivocarse igual que su programa?**

**Dónde está en el documento.** §1.13, p. 36 (PDF p. 52): «el contraste corresponde a verificación de solución y a comparación código a código; esta última, según la propia literatura, no sustituye a la verificación rigurosa del código [21, pp. 173-174]». Nota de la Tabla 3.2, p. 81 (PDF p. 97): «La última columna se rotula “diferencia” y no “error” porque la formulación de cáscara de SAP2000 no es la misma…

**Respuesta preparada.** SAP2000 no es mi patrón y no lo presento como tal: por eso esa columna de la Tabla 3.2 se llama «diferencia» y no «error», y lo explico en su nota. Mi patrón es la solución analítica de Timoshenko y Goodier, que es exacta dentro de la teoría de la elasticidad, y frente a ella el error en σx es del 0,0414 %. SAP2000 entra como tercera opinión, con una formulación distinta —cáscara de Mindlin-Reissner frente al continuo de tensión plana—, y que dos formulaciones distintas coincidan con la solución exacta y entre sí dentro del 0,21 % es información valiosa. Lo respaldo metodológicamente en la página 36, con Oberkampf y Roy, que dicen expresamente que la comparación código a código no sustituye a la verificación rigurosa.

> **Corrección (2026-09-25, segunda iteración).** No digas «cáscara de Mindlin-Reissner»: en esta
> viga el elemento de cáscara de SAP2000 trabaja solo en su plano, como membrana isoparamétrica
> con un giro normal al plano (*drilling*); Mindlin/Reissner es su formulación de flexión de placa,
> que aquí no interviene (manual de CSI, p. 179; las capturas del Anexo E dan U2 = 0). Di: «una
> formulación distinta: membrana de cáscara con giro *drilling* frente al Q9 de tensión plana».
> La tesis ya lo dice así desde final2 (§3.4).

#### PD-22 · RESPONDIDA · *estructuralista*

> **La membrana de Cook da 23,96. ¿De dónde sale ese número y quién lo respalda? ¿Es la solución exacta?**

**Dónde está en el documento.** §3.5, p. 84 (PDF p. 100): «Štembera y Füssl advierten que este problema no tiene solución analítica disponible y obtienen su referencia por vía numérica, con una malla de 192 × 128 elementos, en 23,965 [26, p. 28]… La secuencia Q9 (23,925 → 23,949 → 23,961) todavía se mueve en la malla más fina, y su extrapolación de Richardson [21, pp. 309-312] apunta a ≈23,97». Tabla 3.4, p.…

**Respuesta preparada.** El 23,96 no es una solución exacta, y lo digo explícitamente: este problema no tiene solución analítica disponible. Es un límite de convergencia de uso extendido, y lo respaldo por dos vías independientes: la fuente, Štembera y Füssl, que publican 23,965 con una malla de 192 por 128 elementos, y mi propia evidencia, porque mi secuencia Q9 va de 23,925 a 23,961 y su extrapolación de Richardson apunta a 23,97. Los tres valores caen dentro de un intervalo del orden del 0,05 %, que es la incertidumbre que le asigno a la referencia y que declaro en la Tabla 3.4. Por eso advierto que un error por debajo del 0,1 % no debe leerse como exactitud del elemento: está dentro del ruido de la propia referencia.

#### PD-23 · RESPONDIDA · *metodologo*

> **¿Cuál es la población y cuál la muestra de esta investigación? ¿Cuántos casos y por qué ésos?**

**Dónde está en el documento.** §2.1.4, p. 47 (PDF p. 63): «La unidad de análisis es el procedimiento de cálculo del software, no las personas que lo usan. La población es… el universo de problemas de elasticidad lineal plana —en tensión o en deformación plana— que pueden resolverse con elementos cuadriláteros isoparamétricos. La Carrera de Ingeniería Civil delimita el contexto de aplicación del trabajo; no…

**Respuesta preparada.** La unidad de análisis es el procedimiento de cálculo del software, no las personas. La población es el universo de problemas de elasticidad lineal plana resolubles con cuadriláteros isoparamétricos, y la muestra no es probabilística sino dirigida, por valor probatorio, que es la práctica establecida en la verificación de códigos de cálculo: los casos se eligen por su capacidad de ejercitar todos los términos del modelo matemático, no por representatividad estadística. Los tres casos, entre sí, ejercitan cargas nodales, de volumen y superficiales uniformes, restricciones homogéneas y no homogéneas, los dos estados planos y los dos elementos. Y declaro expresamente lo que ninguno ejercita: la carga superficial linealmente variable, que por eso figura entre las recomendaciones de la página 109.

#### PD-24 · RESPONDIDA · *metodologo*

> **Su hipótesis: ¿qué habría tenido que ocurrir para que quedara refutada?**

**Dónde está en el documento.** Introducción, p. 7 (PDF p. 23): «Cada cláusula puede resultar falsa: la refutarían una etapa sin exposición, un contenido exigido sin instrumento, una tasa de convergencia fuera de margen, un error por encima del umbral o una memoria que no cierre con el cálculo manual». La Tabla 2.4, pp. 51-52 (PDF pp. 67-68), tiene una columna entera, «Lo refutaría», con la condición de fals…

**Respuesta preparada.** Está escrito criterio por criterio en la última columna de la Tabla 2.4, páginas 51 y 52. La refutaba una etapa del procedimiento sin instrumento que la exponga; uno solo de los dieciocho contenidos sin cobertura; una fase que no operara sobre el mismo lienzo; una tasa de convergencia a más de medio orden de la teórica en cualquiera de las cuatro configuraciones; un error de la flecha por encima del 3 % o de la tensión normal por encima del 1 %; un residuo de equilibrio por encima de 10⁻⁸; o que la flecha del Q4 no quedara por debajo de la del Q9 con la misma malla. Todos esos umbrales quedaron fijados antes de las corridas que el documento reporta, y lo declaro en la página 51. Y agrego algo que me importa: la hipótesis no es una tautología, porque exponer el procedimiento no garantiza que lo expuesto sea correcto, y este mismo trabajo encontró un defecto que lo prueba.

#### PD-25 · RESPONDIDA · *director de carrera*

> **¿Qué aporta esto que no aporten ED-Elas2D, que existe desde 1998, o el propio SAP2000?**

**Dónde está en el documento.** §1.1, pp. 14-15 (PDF pp. 30-31): «Los propios autores de ED-Elas2D reconocen que su post-proceso no explica conceptos clave como el suavizado nodal de tensiones y deformaciones, y que es una herramienta meramente descriptiva que muestra los resultados principales del análisis [6, p. 253]». La Tabla 1.1, p. 16 (PDF p. 32), sistematiza la comparación de seis recursos por atribut…

**Respuesta preparada.** ED-Elas2D es mi antecedente más directo y lo digo así: confirma que este tipo de herramienta tiene sentido. La diferencia está en tres cosas que sus propios autores declaran que su programa no hace y que la Tabla 1.1 sistematiza. Primera, la respuesta: ellos reconocen en la página 253 que su post-proceso es meramente descriptivo y no explica el suavizado nodal de tensiones; EduFEM lo abre con la sonda, que muestra el valor crudo del punto de Gauss junto al promediado nodal, y con el contraste de reacciones. Segunda, una memoria de cálculo automática con sustitución numérica sobre el modelo del propio usuario, que ningún antecedente revisado documenta. Y tercera, publicar la verificación y validación junto con la herramienta y distribuirla libre y en español, con un instalador que no exige privilegios de administrador.

#### PD-26 · RESPONDIDA · *metodologo*

> **Esos dieciocho contenidos los definieron expertos mexicanos de ingeniería mecánica. ¿Por qué valen para la ingeniería civil de Potosí?**

**Dónde está en el documento.** §2.1.5, p. 50 (PDF p. 66): «El propio estudio advierte que sus resultados, obtenidos con expertos mexicanos de ingeniería mecánica, no son generalizables a otros contextos [3, p. 1171]. Lo que ese contexto condiciona es la importancia relativa que los expertos dan a cada ítem, y la tabla no pondera: solo registra si el ítem tiene o no instrumento». La limitación se repite en C…

**Qué falta.** Una remisión desde la nota de la Tabla 3.7 (p. 92) a §2.1.5, para que quien llegue a la tabla tenga el argumento a la vista.

**Respuesta preparada.** Del estudio no tomo su ranking, que sí es local: tomo la lista de contenidos, y solo los dieciocho que pertenecen al procedimiento de cálculo del método. Mallar, refinar, leer tensiones nodales frente a las de punto de Gauss, comparar reacciones con cargas, contrastar con una referencia externa: eso es idéntico en ingeniería civil y en mecánica, porque es el método y no la tipología estructural. Los ítems ligados a una tipología —resortes, barras, placas, cáscaras— quedaron fuera por esa misma razón, y están declarados uno por uno en la nota de la Tabla 3.7. Mi tabla no pondera importancia: solo registra si el ítem tiene o no instrumento identificable, y por eso la advertencia de generalización de la fuente no la invalida; lo que falta, y lo recomiendo en la página 110, es someterla al juicio de los docentes de la asignatura.

#### PD-31 · RESPONDIDA · *estructuralista*

> **El Anexo E, que sostiene la comparación con SAP2000, entra con erratas —«SAP200», «poison», «Dezplazamiento»—, con punto decimal y con «esfuerzo» por «tensión». ¿Eso es descuido?**

**Dónde está en el documento.** Preámbulo del Anexo E, p. 145 (PDF p. 161): «Se reproduce tal como fue elaborado, sin rehacer su composición, y por eso conserva convenciones propias, distintas de las del resto del documento… Se conserva además su estilo tipográfico y ortográfico original —títulos en mayúsculas sin tilde, abreviaturas propias y erratas de digitación, como “SAP200”, “poison” o “Dezplazamiento”…

**Qué falta.** Corregir únicamente «SAP200» por «SAP2000» y retirarla entonces de la lista de erratas declaradas, para que la declaración del preámbulo siga siendo exacta.

**Respuesta preparada.** El Anexo E es el documento de cálculo original con que elaboré la referencia, y lo incorporo como evidencia documental, sin rehacerlo, para que se vea tal como fue producido y no como una reconstrucción posterior. Sus divergencias de notación están declaradas una por una al comienzo del anexo, en la página 145, incluidas esas tres erratas de digitación, y ninguna afecta a las cifras que el Capítulo 3 compara. Si lo hubiera recompuesto, la evidencia perdería precisamente su valor de trazabilidad, que es lo que un revisor exigente debería exigirme. Lo único que sí conviene corregir es «SAP200», porque puede leerse como un error de hecho sobre el programa empleado.


### Riesgo bajo

#### PD-37 · PARCIAL · *director de carrera*

> **Cuando instalé el programa, Windows me advirtió que había protegido mi PC. ¿Es seguro?**

**Dónde está en el documento.** Anexo A, §A.1, p. 115 (PDF p. 131): «Al no estar firmado con un certificado comercial, la primera ejecución del instalador puede mostrar el aviso de Microsoft Defender SmartScreen («Windows protegió su PC»), habitual en aplicaciones nuevas». El texto explica cómo continuar, pero no dice por qué no se firmó.

**Qué falta.** Añadir en §A.1 la razón por la que no se firmó (costo recurrente ajeno al alcance del proyecto).

**Respuesta preparada.** Sí, y el aviso está previsto y explicado en el Anexo A, página 115. Aparece porque el instalador no lleva un certificado de firma de código comercial, que exige un pago anual ajeno al alcance de un proyecto académico de distribución gratuita; es el aviso habitual para cualquier aplicación nueva sin reputación acumulada, no una detección de programa malicioso. El manual indica cómo continuar la instalación, y como el código fuente es público, cualquiera puede inspeccionarlo y reconstruir el instalador por su cuenta. Además se instala por usuario, sin privilegios de administrador, de modo que no modifica el sistema.

#### PD-38 · PARCIAL · *metodologo*

> **¿Cómo se replica este trabajo si dentro de dos años el programa ya no compila?**

**Dónde está en el documento.** §2.1.1, p. 43 (PDF p. 59): «La versión evaluada es EduFEM 1.0.0, revisión 91e3df0 del repositorio público citado en la Introducción (16 de septiembre de 2026), con las dependencias declaradas en su archivo requirements.txt. Es la versión que se distribuye con este documento mediante el instalador». El Anexo D.1, p. 137 (PDF p. 153), describe los guiones reejecutables y los CSV…

**Qué falta.** Depositar una copia del repositorio y de los CSV en un archivo con identificador permanente y citarlo en el Anexo D.1.

**Respuesta preparada.** La replicación tiene tres niveles y los tres están cubiertos. Primero, el instalador se entrega con la tesis y lleva dentro el intérprete y todas las bibliotecas, de modo que no depende de que nada se instale después. Segundo, el código está en un repositorio público con la revisión exacta identificada en la página 43 —EduFEM 1.0.0, revisión 91e3df0, del 16 de septiembre de 2026— y sus dependencias declaradas. Y tercero, los datos crudos de cada tabla y cada figura del Capítulo 3 quedan en archivos CSV que produce cada guion, de modo que las cifras pueden verificarse sin ejecutar una sola línea de código; lo que no puedo garantizar es que Python 3.13 siga instalándose dentro de diez años, y por eso el instalador es autocontenido.

#### PD-35 · RESPONDIDA · *estructuralista*

> **¿Por qué Python y no MATLAB o un lenguaje compilado? ¿No es más lento?**

**Dónde está en el documento.** Justificación, p. 4 (PDF p. 20): «La elección del lenguaje Python obedece a tres razones: no exige licencia al estudiante; reúne en un solo lenguaje el cálculo numérico, la interfaz gráfica y la generación de documentos; y…». Tabla 1.1, p. 16 (PDF p. 32), consigna que ED-Elas2D-CALFEM «Requiere MATLAB». El rendimiento se reporta en la Tabla 3.9, p. 98 (PDF p. 114).

**Respuesta preparada.** Por tres razones que declaro en la página 4: no exige licencia al estudiante, reúne en un solo lenguaje el cálculo numérico, la interfaz gráfica y la generación de documentos, y permite distribuir la herramienta sin que el usuario instale nada más. Ése es justamente el atributo que la Tabla 1.1 señala como limitación de otros recursos didácticos: CALFEM, por ejemplo, requiere MATLAB, que es una licencia comercial. En cuanto al rendimiento, el motor está vectorizado por lotes en NumPy y los tiempos están medidos en la Tabla 3.9, página 98: resuelve más de 33 000 grados de libertad en alrededor de un segundo sobre un equipo de más de una década de antigüedad, y la matriz dispersa ocupa menos de 13 MB donde la densa necesitaría cerca de 8,9 GB. Para los tamaños de modelo de un contexto educativo, el lenguaje no es la restricción.

#### PD-36 · RESPONDIDA · *estructuralista*

> **¿Por qué solo Q4 y Q9? ¿Por qué no triángulos, elementos de orden superior o tres dimensiones?**

**Dónde está en el documento.** Alcance y limitaciones, p. 9 (PDF p. 25): «La pareja Q4-Q9 es el par mínimo que contrasta dos órdenes de interpolación dentro de una sola familia de funciones de forma: el Q4 es bilineal y el Q9, bicuadrático… Mantener una sola familia conserva además las matrices del seguimiento paso a paso en un tamaño legible». La ampliación queda en Recomendaciones, p. 108 (PDF p. 124).

**Respuesta preparada.** Porque el núcleo de la herramienta es que las matrices puedan mirarse. En el Q4 la matriz constitutiva es de 3 × 3 y la de deformación, de 3 × 8: caben en una pantalla y en una hoja. En un hexaedro de ocho nodos la constitutiva pasa a 6 × 6, la de deformación a 6 × 24 y la rigidez elemental a 24 × 24, es decir, quinientas setenta y seis entradas que nadie sigue paso a paso. El par Q4-Q9 es el mínimo que permite contrastar dos órdenes de interpolación sin cambiar de familia de funciones de forma, y es lo que hace visible el bloqueo por cortante en la membrana de Cook. Los triángulos y el cuadrilátero de ocho nodos quedan como primera línea de ampliación, en la página 108, y la extensión a tres dimensiones, en la 109.


---

## Sobrecorrecciones: lo que NO hay que tocar

Léelo antes de empezar y vuelve a leerlo cuando lleves media tesis corregida. Todo lo que sigue
está bien como está, y cambiarlo empeoraría el documento.

1. **La nota de la Tabla 3.2** (p. 81), que rotula la última columna «diferencia» y no «error».
   Es la frase que tiene razón. La corrección va en sentido contrario: alinear las Conclusiones
   con ella.
2. **El tratamiento de la membrana de Cook** (§3.5): 23,96 adoptado, 23,965 publicado, ≈ 23,97
   por extrapolación propia, incertidumbre de 0,05 %, advertencia de no leer como exactitud los
   errores por debajo del 0,1 %. Es calibración ejemplar. Lo único que falta es la fuente del
   23,96.
3. **El párrafo de §3.4** (p. 82) que declara los tres puntos de control, el 0,94 % en σy y el
   2,89 % en τxy, y que el máximo sobre el dominio completo no se calculó. Ese párrafo es lo que
   salva la calibración del capítulo. El arreglo es **llevar esas salvedades al Resumen**, no
   quitarlas de donde están.
4. **El Anexo B no se vacía.** Es un manual de uso y tiene que poder leerse solo. El solapamiento
   con §2.2 es funcional salvo en la teoría —la glosa de «lienzo» y las tres severidades del
   comprobador—, que sí se recorta.
5. **No añadir localizadores a las remisiones generales** a obras completas (Zienkiewicz, Bathe,
   Reddy, NumPy, SciPy). Vancouver no los exige ahí, y llenarlas de páginas arbitrarias empeora
   el aparato de citas.
6. **No reordenar ni renumerar las citas.** El orden de primera mención es estrictamente
   correlativo y está comprobado. Cualquier retoque puede romperlo.
7. **No perseguir desbordes de línea ni mover flotantes buscando tipografía.** El registro de
   LaTeX declara cero *overfull*, cero *underfull* y `microtype` activo. Mover un flotante para
   tapar un hueco blanco suele crear otro peor.
8. **No tocar los números del Anexo G ni la matriz de extrapolación.** La aritmética se rehízo
   íntegra y cierra en las catorce magnitudes comprobables. Lo que se corrige es la presentación
   —unidades, precisión, figuras—, jamás los valores.
9. **No añadir afirmaciones que compensen la ausencia de prueba de campo**: ni sobre aprendizaje,
   ni sobre comprensión, ni sobre valor pedagógico. La disciplina del documento en este punto es
   una fortaleza.
10. **No ilustrar el capítulo 1 con una campaña de figuras nuevas.** Si se añade alguna, una
    sola: el mapeo ξη → xy en §1.5. Más figuras a esta altura mueven flotantes, referencias y
    páginas en un documento ya compuesto y verificado.
11. **No alargar la bibliografía** para que parezca más académica. Que sean 26 entradas es un
    dato, no un defecto. Solo se agrega fuente donde hay una atribución concreta que hoy no la
    tiene: ACI 318 y el 23,96 de Cook.
12. **No repetir la versión ni el hash del software en el Anexo D.1.** Están en §2.1.1, y
    `CRITERIOS.md` manda una sola aparición canónica con remisión por `\autoref`.
13. **No reintroducir la Nomenclatura en orden alfabético.** El documento declara y justifica en
    la p. xi que los símbolos se agrupan por tema y, dentro del tema, por orden de aparición.

---

## Lista de comprobación final

Antes de dar por cerrada la corrección:

- [ ] `grep -c "PI-3" capitulos_final/*.tex` devuelve **0**
- [ ] `grep -rn "ichardson" capitulos_final/04_resultados.tex` ya no aparece en la columna
      «Instrumento de EduFEM» de la fila FEA30
- [ ] El Anexo G declara **kgf y cm**, no kN y cm
- [ ] La palabra «MIT» aparece en la tesis
- [ ] Las Conclusiones dicen «diferencia» y no «error» al hablar de SAP2000
- [ ] El Resumen escribe «σx» donde antes decía «la tensión normal»
- [ ] El Resumen dice «de los cuarenta y nueve contenidos… los dieciocho que…»
- [ ] §3.4 declara los apoyos, la carga y el modelo de SAP2000
- [ ] El primer `\includepdf` del Anexo E lleva `scale=0.88`
- [ ] Los seis localizadores de [16] Bishay están resueltos (o la entrada declara la paginación
      del ejemplar consultado)
- [ ] Recompilar dos veces (`latexmk -pdf main_final.tex`) y comprobar que el registro sigue sin
      *overfull* ni *underfull*
- [ ] Releer el PDF terminado de principio a fin, en papel, con esta lista al lado

---

*Auditoría realizada el 22 de septiembre de 2026 sobre `tesis/main_final.pdf`, 187 páginas.*
*25 lectores en paralelo, un verificador independiente por unidad y por eje, y un crítico de*
*completitud que no participó en la lectura. 354 hallazgos brutos; 299 vivos tras fusionar,*
*retirar y agrupar; ninguno de severidad crítica.*
