# Auditoría de la tesis por sesiones — coherencia, citación y forma

> Archivo de continuidad de la rutina programada de auditoría de la tesis. Cada sesión la
> corre un agente distinto y sin memoria: **todo lo que la siguiente sesión necesita está
> acá**. Solo auditoría: ningún archivo de `tesis/` se edita desde esta rutina. Los
> hallazgos los cierra el autor (estado `resuelto`); las sesiones no reauditan un bloque
> `auditado` salvo que `git log -- tesis/` muestre commits posteriores al anotado en el
> registro, y en ese caso revisan solo lo que cambió.
>
> Complementa, no reemplaza, la [auditoría integral del 2026-09-11](2026-09-11_auditoria_tesis.md)
> (ya implementada salvo las exclusiones del autor). Lo que aquel informe cerró no se repite;
> lo que dejó como decisión abierta y sigue en el texto sí se registra, marcado como reincidente.

## 1. Resumen ejecutivo

**Última sesión**: 1 · 2026-09-15 · commit de la tesis auditado: `bdbf18d` (2026-09-11).

| Bloque | Contenido | Estado |
|---|---|---|
| B0 | Inventario y norma de citación | **auditado** (sesión 1) |
| B1 | Introducción: problema, objetivos, hipótesis, justificación, alcance | **auditado** (sesión 1) |
| B2 | Marco teórico y metodología | pendiente |
| B3 | Resultados | pendiente |
| B4 | Conclusiones y recomendaciones | pendiente |
| B5 | Citación y referencias contra la norma de B0 | pendiente (4 hallazgos ya registrados desde B0) |
| B6 | Forma: títulos, numeración, jerarquía, preliminares | pendiente |

**Hallazgos abiertos por severidad**: alta 1 · media 8 · baja 5 · **total 14** (H-1 a H-14). Resueltos: 0.

Lo que más pesa hoy: el **Reglamento de Graduación** que fija formato y referenciación no
está en el repositorio (H-1), la tesis **no declara en su texto la norma de citación** que
sigue (H-2), y la cadena problema → variables → medición sigue partida en dos: las variables
del problema científico no son las que la metodología mide (H-6) y la hipótesis se contrasta
«por diseño» (H-7).

## 2. Inventario (B0)

### 2.1 Archivos de la tesis

| Qué | Ruta |
|---|---|
| Documento maestro (metadatos de portada, orden de `\input`) | `tesis/main.tex` |
| Preámbulo (presentación APA 7 + bloque biblatex Vancouver) | `tesis/preambulo.tex` |
| Portada | `tesis/portada/portada.tex` (más `tesis/CARATULA.pdf`, carátula impresa) |
| Preliminares (comentados para el borrador), resumen, nomenclatura | `tesis/capitulos/00_preliminares.tex`, `00_resumen.tex`, `00b_nomenclatura.tex` |
| Introducción (sin numerar) | `tesis/capitulos/01_introduccion.tex` |
| Capítulo 1 · Marco teórico | `tesis/capitulos/02_marco_teorico.tex` |
| Capítulo 2 · Diseño e implementación (§2.1 diseño metodológico, §2.2 software) | `tesis/capitulos/02b_diseno_metodologico.tex` + `03_diseno_implementacion.tex` |
| Capítulo 3 · Resultados | `tesis/capitulos/04_resultados.tex` |
| Conclusiones y recomendaciones | `tesis/capitulos/05_conclusiones.tex` |
| Anexos A–G | `tesis/capitulos/06_anexos.tex`, `07_anexo_memoria.tex`, `tesis/anexos/validacion_sap2000.pdf` |
| Referencias (biblatex, 22 entradas) | `tesis/bibliografia/referencias.bib` |
| Respaldo página a página de cada cita | `tesis/respaldo_citas/verificado.json`, `respaldo_citas.pdf` |
| PDF compilado (gitignored; el del 2026-09-11 tenía 151 hojas) | `tesis/main.pdf` |

### 2.2 Documentos de referencia sobre norma de presentación y citación

| Documento | Ruta | Qué aporta |
|---|---|---|
| Taller 1 «Documento de graduación» (CIV 400 Seminario de Grado II, UATF, Ing. J. C. Barrios, 2021) | `tesis/Material docente/Taller 1 Documento de Gradación.pdf` | Extractos del Reglamento de Graduación (arts. 2, 6, 8, 9, 40); índice esperado de una TESIS (p. 20); jerarquía de fuentes (p. 24); estructura de la bibliografía (p. 26); lista de lo que el Reglamento fija sobre formato (p. 18) |
| Taller 2 «Normas de referenciación» (ídem) | `tesis/Material docente/Taller 2 Normas de referenciación.pdf` | Normas admitidas (p. 16-17), recomendaciones de referenciación (p. 18-19), mandato de exponer la norma que se usa (p. 20), «asumir una normativa única» (p. 25 del Taller 1) |
| Taller 4 «Modelo de investigación» | `tesis/Material docente/Taller 4 Modelo de Investigación.pdf` | Estructura del modelo científico; el modelo va en el Capítulo 2; población y muestra (p. 13) |
| Taller 5 «Comunicación de resultados» | `tesis/Material docente/Taller 5 Comunicación de resultados.pdf` | Qué debe tener el capítulo de resultados y las conclusiones (p. 3-4, 21) |
| Taller 6 «Defensa» | `tesis/Material docente/Taller 6 Defensa del trabajo de graduación.pdf` | Solo defensa oral; no se usa |
| «Planteamiento del problema científico e hipótesis» (Ing. J. S. Miranda) | `tesis/Material docente/PLANTEAMIENTO DEL PROBLEMA CIENTÍFICO É HIPOTESIS.pdf` | Siete pasos del problema (interrogante, VI/VD, delimitaciones); requisitos de la hipótesis (tres variables, tiempo futuro, comprobable) |
| «Cómo se construye el objetivo general» (ídem) | `tesis/Material docente/Como se construye el objetivo general.pdf` | OG = verbo + qué + cómo + para qué; OE por capítulo; tríada capítulo–conclusión–recomendación |
| «Situación problemática, objeto de estudio y campo de acción» (ídem) | `tesis/Material docente/Situacion Problematica - Objeto de Estudio y Campo de Accion.pdf` | Definiciones de objeto y campo |
| Guía Vancouver propia del proyecto | `tesis/normas/guia_vancouver.tex` / `.pdf` | Plantilla por tipo de fuente y revisión de las 22 referencias contra ICMJE + NLM *Citing Medicine* |
| Guía APA 7 de terceros (Tavares 2020, normas-apa.org) | `tesis/normas/` (**gitignored**, no está en el clon) | Presentación del documento |
| Decisiones del proyecto sobre normas | `tesis/README.md`, `docs/notas/2026-09-10_apa-presentacion.md`, `docs/notas/2026-09-08_bibliografia-tesis.md` | Vancouver para citas, APA 7 para presentación; qué de APA no se aplicó y por qué |

**No está en el repositorio**: el *Reglamento de Graduación de la Carrera de Ingeniería Civil
UATF* completo (solo extractos en los talleres) → H-1.

### 2.3 Norma de citación que exige el proyecto

- **Lo que dicen los documentos de referencia**: el Taller 2 no impone una norma. Enumera
  «HARVARD · VANCUVER · REGLAMENTO DE GRADUACION» (p. 16-17), manda «asumir una normativa
  única» (Taller 1, p. 25: «Cuando se desarrolle una investigación o proyecto de grado asumir
  una normativa única») y cierra con «Exponer la normativa que utiliza, para el desarrollo de
  su investigación para su graduación (tesis, proyecto de grado)» (Taller 2, p. 20). Sus
  recomendaciones generales (p. 18-19) son las de Vancouver: numeración consecutiva por orden
  de primera mención, «números arábigos en superíndice y sin paréntesis», sin citas de cita,
  títulos de revista abreviados «según el estilo que utiliza la normativa».
- **Lo que asumió el proyecto**: **Vancouver (ICMJE + NLM *Citing Medicine*)** para citas y
  referencias, implementado con `biblatex` `style=numeric-comp`, `sorting=none`,
  `terseinits=true` (`tesis/preambulo.tex:263-271`), con dos desvíos deliberados y
  documentados (`tesis/README.md`): títulos de revista completos y «y» antes del último
  autor. La presentación del documento sigue **APA 7.ª ed.** desde el 2026-09-10.
- **Contra qué audita B5**: Vancouver tal como lo fija `tesis/normas/guia_vancouver.tex`
  (fuente primaria: NLM *Sample References*) más las recomendaciones del Taller 2 p. 18-19 y
  la estructura de bibliografía del Taller 1 p. 26. Los dos desvíos documentados no se
  registran como hallazgo salvo que el Reglamento (cuando aparezca) los prohíba.

### 2.4 Estructura que el Taller 1 espera de una tesis (p. 20) — para B6

RESUMEN · INTRODUCCIÓN · Capítulo 1 MARCO TEÓRICO DE … · Capítulo 2 DISEÑO E IMPLEMENTACIÓN
DEL MODELO A DESARROLLAR · Capítulo 3 PRESENTACIÓN DE RESULTADOS Y ANÁLISIS DE LOS MISMOS ·
Conclusiones y Recomendaciones · Bibliografía · Anexos. La tesis sigue ese orden
(`tesis/main.tex:43-78`) y agrega índices, nota de autoría de figuras y nomenclatura entre el
resumen y la introducción.

## 3. Tabla de trazabilidad

Objetivos tomados de `tesis/capitulos/01_introduccion.tex:33-40` (sesión 1). Las columnas
de metodología, resultado y conclusión las completan B2, B3 y B4.

| # | Objetivo específico (abreviado) | Metodología que lo atiende (B2) | Resultado que lo responde (B3) | Conclusión que lo cierra (B4) | Estado |
|---|---|---|---|---|---|
| OE1 | Fundamentar teóricamente el MEF en elasticidad plana con Q4/Q9 (formulación, mapeo, integración, ensamblaje, tensiones, calidad de malla, criterios de V&V) | — | — | — | pendiente |
| OE2 | Implementar un motor MEF 2D Q4/Q9 «verificado numéricamente» | — | — | — | pendiente |
| OE3 | Diseñar una interfaz interactiva pre/proceso/post con un único lienzo | — | — | — | pendiente |
| OE4 | Desarrollar módulos educativos que expongan paso a paso cada etapa del canal de cálculo | — | — | — | pendiente |
| OE5 | Verificar y validar con MMS, viga de Timoshenko y membrana de Cook, contra soluciones analíticas y SAP2000 | — | — | — | pendiente |
| OE6 | Generar memoria de cálculo automática en PDF y ofrecer interoperabilidad DXF/CSV | — | — | — | pendiente |
| H | Hipótesis de diseño: es factible construir un software que exponga el canal de cálculo completo de forma transparente, interactiva, numéricamente verificable y coherente con el flujo profesional; esa transparencia es «un apoyo plausible al aprendizaje» | — | — | — | pendiente |

Lo que la propia Introducción declara sobre dónde se cumple cada uno
(`01_introduccion.tex:69`): OE1 → Cap. 1; OE2, OE3, OE4, OE6 → Cap. 2; OE5 → Cap. 3;
la hipótesis se contrasta en el Cap. 3 y se discute en Conclusiones. B2–B4 verifican si es así.

## 4. Hallazgos

### B0 — Inventario y norma

**H-1**
- Bloque y sección: B0 · documentos de referencia
- Tipo: forma
- Severidad: **alta**
- Evidencia: el Taller 1 (p. 18) enumera lo que fija el «REGLAMENTO DE GRADUACIÓN DE LA CARRERA DE INGENIERÍA CIVIL»: «Formatos · Tamaño de hoja · Márgenes admitidos · Tipo de letra · Interlineado · Componentes generales del documento · Referenciación · Estructura de listas · Contenido sugerido · Estructura de la bibliografía». Ese reglamento no está en `tesis/`, `tesis/normas/` ni `tesis/Material docente/` (solo extractos de los arts. 2, 6, 8, 9 y 40 en el Taller 1, p. 2-4). La auditoría del 2026-09-11 ya lo anotó: «Reglamento de la UATF: … No se cotejó».
- Problema: la norma de presentación vigente (APA 7, adoptada el 2026-09-10 según `tesis/README.md`) y la de citación (Vancouver) se eligieron sin el documento que, según el propio material del tribunal, regula formato, interlineado, referenciación y estructura de la bibliografía. B5 y B6 solo pueden contrastar contra los resúmenes de los talleres.
- Sugerencia: conseguir el Reglamento de Graduación (texto completo) y dejarlo en `tesis/normas/` o anotar en `tesis/README.md` que no existe versión escrita accesible.
- Estado: abierto
- Sesión: 1

**H-2**
- Bloque y sección: B0 · norma de citación
- Tipo: citación
- Severidad: media
- Evidencia: Taller 2, p. 20: «Exponer la normativa que utiliza, para el desarrollo de su investigación para su graduación (tesis, proyecto de grado)». En la tesis, la única declaración de la norma está en un comentario LaTeX invisible: `tesis/main.tex:70` «% ----- Bibliografia (estilo Vancouver) -----». Búsqueda de «Vancouver», «APA» y «norma» en `tesis/capitulos/*.tex`: 0 resultados en texto visible.
- Problema: el tribunal no puede saber contra qué norma juzgar las citas ni por qué la lista es numérica por orden de aparición. El material docente pide exponerlo explícitamente; el documento lo omite.
- Sugerencia: una frase en la Introducción (en «Estructura del documento») o al pie de la Bibliografía: «Las citas y referencias siguen la norma Vancouver (ICMJE/NLM); la presentación, APA 7.ª ed.».
- Estado: abierto
- Sesión: 1

### B1 — Introducción

**H-3**
- Bloque y sección: B1 · Planteamiento del problema (y su eco en §2.1.3)
- Tipo: coherencia
- Severidad: media
- Evidencia: el problema se formula tres veces y de tres maneras. (a) `01_introduccion.tex:13`: «¿cómo apoyar la comprensión de los fundamentos del MEF mediante una herramienta de software que exponga, sobre un modelo concreto y de manera interactiva, cada etapa del procedimiento de cálculo…?». (b) `01_introduccion.tex:15`: «el problema científico … ¿cómo debe construirse un software educativo para que exponga de forma transparente, interactiva y numéricamente verificable el canal de cálculo completo del MEF en elasticidad plana…?». (c) `02b_diseno_metodologico.tex:43`: «El problema general —la ausencia de un entorno educativo libre y de código abierto, en español, que exponga de forma transparente, interactiva y verificable el canal de cálculo completo del MEF en elasticidad plana y genere una memoria de cálculo trazable al modelo del alumno—».
- Problema: (a) pregunta por cómo apoyar la comprensión (el «para qué», que `tesis/README.md` dice que no es lo medido); (b) pregunta por cómo construir el software; (c) ya no es una interrogante sino una carencia, y añade atributos que el problema científico no contiene («libre y de código abierto», «en español», «memoria de cálculo»). El planteamiento del tribunal (Miranda, p. 3) pide una sola interrogante con dos variables; la matriz de consistencia debería partir de la misma formulación que la Introducción.
- Sugerencia: dejar (b) como problema científico único, reescribir (a) como pregunta orientadora subordinada o quitarla, y que §2.1.3 cite (b) textualmente.
- Estado: abierto
- Sesión: 1

**H-4**
- Bloque y sección: B1 · Planteamiento del problema → §2.1.2 Variables
- Tipo: coherencia
- Severidad: media
- Evidencia: `01_introduccion.tex:15`: «La variable causa es la forma en que la herramienta expone ese canal —transparencia, interactividad y verificabilidad numérica—; la variable efecto es la observabilidad y contrastabilidad del procedimiento intermedio que el software profesional encapsula». `02b_diseno_metodologico.tex:21`: «La variable independiente reúne la definición del modelo estructural … y las decisiones de discretización … La variable dependiente es la respuesta estructural calculada … junto con su exactitud». `02b_diseno_metodologico.tex:90`: «estos tres elementos no deben confundirse con las variables del experimento numérico de la Tabla 2.1, que son las que efectivamente se miden». Material docente (Miranda, p. 5): «Las variables son los aspectos del objeto de estudio que serán medidos».
- Problema: la variable efecto del problema científico («observabilidad y contrastabilidad») no aparece en la Tabla 2.1 ni tiene indicador ni instrumento; lo que se mide (errores, tasas de convergencia) responde a otra pareja VI/VD. La tesis lo reconoce y lo declara fuera de medición, con lo que el problema científico queda sin variable medida. Reincidente de la revisión del 2026-06-10 («variable independiente con dos significados»); es decisión del autor del 2026-09-08 (`tesis/README.md`), pero el hueco sigue en el texto.
- Sugerencia: dar a la variable efecto un indicador observable en la Tabla 2.1 (p. ej. «cobertura del canal de cálculo: etapas con módulo + memoria», que la matriz ya usa para OE4) o renombrar las de la Tabla 2.1 como «variables del experimento numérico» sin llamarlas independiente/dependiente.
- Estado: abierto
- Sesión: 1

**H-5**
- Bloque y sección: B1 · Hipótesis o preguntas de investigación
- Tipo: coherencia
- Severidad: media
- Evidencia: `01_introduccion.tex:44`: «La hipótesis de diseño sostiene que es factible construir un software educativo que exponga el canal de cálculo completo del MEF … La verificación de esta hipótesis es, en consecuencia, por diseño: se establece comprobando que la herramienta cumple esos atributos». Título de la sección (`01_introduccion.tex:42`): «Hipótesis o preguntas de investigación». Material docente (Miranda, p. 12-14): la hipótesis «Es una proposición que necesita ser verificado», «Debe ser formulado en términos afirmativos», «debe estar en tiempo Futuro», y el flujograma exige responder «¿SE PUEDE COMPROBAR LA HIPÓTESIS?».
- Problema: «es factible construir X» se comprueba construyendo X: la hipótesis no puede resultar falsa una vez que el software existe (reincidente de la revisión del 2026-06-10, «hipótesis circular»). Su segunda cláusula —«esa transparencia constituye un apoyo plausible al aprendizaje»— se declara no contrastable. El título con «o» deja abierto si el trabajo tiene hipótesis o solo preguntas. Es decisión documentada del autor («validación por diseño»), pero el material del tribunal exige comprobabilidad.
- Sugerencia: formular la hipótesis sobre lo que sí se mide («el motor reproducirá las tasas teóricas de convergencia y errores < 3 % frente a Timoshenko/SAP2000, y evidenciará el bloqueo del Q4») y dejar el «apoyo al aprendizaje» como supuesto fundamentado, no como hipótesis; titular «Hipótesis y preguntas de investigación».
- Estado: abierto
- Sesión: 1

**H-6**
- Bloque y sección: B1 · Objetivos (objetivo general) ↔ título
- Tipo: coherencia
- Severidad: media
- Evidencia: título (`tesis/main.tex:20`): «Desarrollo de software educativo de elementos finitos para el análisis estructural **empleando el lenguaje de programación Python**». Objetivo general (`01_introduccion.tex:29`): «desarrollar EduFEM, un software educativo de escritorio para el análisis por el Método de los Elementos Finitos (MEF) de problemas bidimensionales de elasticidad lineal … que integre la formulación matemática, la construcción y visualización interactiva del modelo y la verificación numérica, como apoyo a la enseñanza y el aprendizaje del MEF». La palabra «Python» no aparece en toda la Introducción (0 ocurrencias en `01_introduccion.tex`). Material docente («Cómo se construye el objetivo general», p. 2-4): el OG lleva «Un verbo en modo infinitivo · Un ¿Qué cosa? · Un ¿Cómo? · Un ¿Para qué?».
- Problema: el «cómo» del título (Python) no está en el objetivo general ni en ningún lugar de la Introducción; el OG tiene verbo, qué y para qué, pero el «cómo» que enuncia («que integre…») no es el del título. Título y OG deben hablar del mismo alcance con los mismos términos.
- Sugerencia: «…desarrollar, en el lenguaje de programación Python y con bibliotecas numéricas de código abierto, EduFEM, un software…», o quitar «empleando … Python» del título (decisión pendiente del autor según `tesis/README.md`).
- Estado: abierto
- Sesión: 1

**H-7**
- Bloque y sección: B1 · Objetivos específicos (OE6) ↔ §2.1.3 matriz de consistencia
- Tipo: coherencia
- Severidad: baja
- Evidencia: `01_introduccion.tex:39`: «Generar documentación de cálculo automática (memoria de cálculo en PDF) **y** ofrecer interoperabilidad de datos (DXF, CSV)». `02b_diseno_metodologico.tex:61`: fila de la matriz con «Pregunta asociada: ---»; `:69`: «El sexto objetivo específico … es de carácter instrumental: no deriva de una pregunta de investigación propia».
- Problema: un objetivo con dos productos distintos (memoria de cálculo; importación/exportación) y sin pregunta de investigación. La memoria de cálculo es, según la Justificación (`01_introduccion.tex:23`), el diferenciador principal frente a los antecedentes; la interoperabilidad es un accesorio. Juntarlos diluye el primero y deja un objetivo que la matriz no puede trazar a ninguna pregunta.
- Sugerencia: separar (OE6 memoria de cálculo, ligado a PI-2; interoperabilidad como requisito del software en §2.2) o justificar en la matriz por qué un objetivo sin pregunta sigue siendo objetivo.
- Estado: abierto
- Sesión: 1

**H-8**
- Bloque y sección: B1 · Objetivos específicos (OE2 y OE5)
- Tipo: coherencia
- Severidad: baja
- Evidencia: OE2 (`01_introduccion.tex:35`): «Implementar un motor de cálculo MEF 2D … **verificado numéricamente**». OE5 (`:38`): «**Verificar y validar** el software mediante el método de soluciones manufacturadas (MMS) y casos de referencia clásicos…». Matriz (`02b_diseno_metodologico.tex:57,60`): OE2 → evidencia «Cap. 3 (MMS)»; OE5 → evidencia «Cap. 3».
- Problema: la verificación numérica figura como atributo de OE2 y como objetivo propio en OE5, y la misma evidencia (MMS) responde a los dos. B3 no podrá asignar un resultado exclusivo a cada uno.
- Sugerencia: quitar «verificado numéricamente» de OE2 (la verificación es OE5).
- Estado: abierto
- Sesión: 1

**H-9**
- Bloque y sección: B1 · terminología (Introducción ↔ §2.1)
- Tipo: coherencia
- Severidad: baja
- Evidencia: «canal de cálculo» en `01_introduccion.tex:15, 17, 37, 44` y `02b_diseno_metodologico.tex:16, 43, 59, 90`; «cadena de cálculo» en `01_introduccion.tex:50` («exponer la cadena de cálculo del MEF») y `02b_diseno_metodologico.tex:67` («expone la cadena de cálculo de forma transparente»); «cadena algebraica» en `01_introduccion.tex:9`; «cada etapa del cálculo» en `00_resumen.tex:5`.
- Problema: el concepto central de la tesis (la secuencia mapeo → J → B → D → K → ensamblaje → solución → tensiones) se nombra con dos términos en la propia definición de PI-2 y en su reformulación de §2.1.3. El criterio de coherencia pide los mismos términos entre secciones.
- Sugerencia: «canal de cálculo» en todo el documento (es el que usan el problema científico, el objeto y la hipótesis).
- Estado: abierto
- Sesión: 1

**H-10**
- Bloque y sección: B1 · Metodología de la investigación ↔ §2.1.1
- Tipo: coherencia
- Severidad: baja
- Evidencia: `01_introduccion.tex:56`: «Según su nivel u objetivo, la investigación es **descriptiva** y **comparativa**: caracteriza el comportamiento numérico del modelo y contrasta…». `01_introduccion.tex:58`: «El diseño metodológico … se desarrolla en detalle en la Sección 2.1». En `02b_diseno_metodologico.tex` no aparecen «descriptiva» ni «comparativa» (0 ocurrencias); §2.1.1 solo retoma «propositivo», «aplicada de tipo tecnológico» y «cuantitativo».
- Problema: la sección que dice desarrollar «en detalle» la tipificación de la Introducción omite uno de sus cuatro ejes (el nivel). Un lector del Cap. 2 no encuentra el sustento de «descriptiva y comparativa».
- Sugerencia: repetir el nivel en §2.1.1 con su cita, o quitarlo de la Introducción.
- Estado: abierto
- Sesión: 1

**H-11**
- Bloque y sección: B1 · Hipótesis ↔ §2.1.6
- Tipo: coherencia
- Severidad: baja
- Evidencia: `01_introduccion.tex:44`: «En la nomenclatura de tres variables del diseño clásico de investigación, el aporte es EduFEM; el atributo manipulado, la transparencia, interactividad y verificabilidad con que se expone el canal de cálculo; y el efecto esperado, la observabilidad y contrastabilidad del procedimiento como apoyo a la comprensión de sus fundamentos, en correspondencia con las variables del problema científico. Esa correspondencia se desarrolla en la Sección 2.1.6». `02b_diseno_metodologico.tex:90`: «En la nomenclatura del diseño clásico de investigación, el aporte es EduFEM, el atributo manipulado es la transparencia e interactividad con que se presenta el canal de cálculo, frente a la opacidad del software profesional y la abstracción de los textos clásicos, y el efecto esperado es la observabilidad y contrastabilidad del procedimiento, como apoyo a la comprensión de los fundamentos del MEF, en correspondencia con las variables del problema científico».
- Problema: la Introducción promete que §2.1.6 «desarrolla» la correspondencia, pero §2.1.6 la repite casi palabra por palabra sin añadir nada. Además, el «atributo manipulado» pierde la «verificabilidad» entre una versión y otra (Intro: «transparencia, interactividad y verificabilidad»; §2.1.6: «transparencia e interactividad»).
- Sugerencia: dejar el párrafo en un solo lugar y unificar los tres atributos.
- Estado: abierto
- Sesión: 1

### B5 — Citación y referencias (registrados en sesión 1 desde B0; el bloque sigue pendiente)

**H-12**
- Bloque y sección: B5 · formato de la cita en el texto
- Tipo: citación
- Severidad: media
- Evidencia: Taller 2, p. 18: «Se recomienda que se utilicen números arábigos en superíndice y sin paréntesis». `tesis/preambulo.tex:267`: «style=numeric-comp,  % numerico con rangos comprimidos: [2-5]». Las 69 `\autocite` de los capítulos se imprimen entre corchetes: «[8, 10]», «[2]» (constatado en la auditoría del 2026-09-11, §2.6 y §4).
- Problema: el único documento del tribunal que habla del formato de la cita en texto recomienda superíndice sin paréntesis; la tesis usa corchetes. Vancouver admite ambas formas, así que no es error de norma, pero es un apartamiento de la recomendación explícita del material docente, no justificado en ningún lado.
- Sugerencia: `\usepackage[…,autocite=superscript]{biblatex}` (o dejar corchetes y justificarlo en la frase de H-2).
- Estado: abierto
- Sesión: 1

**H-13**
- Bloque y sección: B5 · lista final
- Tipo: citación
- Severidad: media
- Evidencia: Taller 1, p. 26: «El listado de bibliografía de referencia debe ser ordenado según su aparición en el documento, señalando nombre de autor, título de la publicación, Editorial, año y páginas de referencia. El listado de bibliografía utilizada en el documento de graduación, debe ser en orden alfabético, según: Nombre de autor o autores, título de la publicación, Editorial, país y año». `tesis/main.tex:72`: una sola lista, `\printbibliography[title={Bibliografía},heading=bibintoc]`, con `sorting=none`.
- Problema: el material docente distingue dos listados (referencias citadas, por orden de aparición; bibliografía consultada, alfabética). La tesis entrega uno solo, titulado «Bibliografía», ordenado por aparición, que en realidad es la lista de referencias. Falta decidir si el tribunal exige el segundo listado y, en cualquier caso, el título no corresponde al contenido.
- Sugerencia: titular «Referencias» a la lista actual y, si el Reglamento (H-1) lo pide, añadir «Bibliografía» alfabética con las obras consultadas y no citadas (`\nocite`).
- Estado: abierto
- Sesión: 1

**H-14**
- Bloque y sección: B5 · jerarquía y antigüedad de fuentes
- Tipo: citación
- Severidad: baja
- Evidencia: Taller 1, p. 24: «Nivel 3: Libros publicados con data no mayor a 10 años»; Taller 2, p. 19: «Los documentos que se citen deben ser actuales, salvo por motivos históricos o si no encontrásemos referencias actualizadas». Campo `year` de `tesis/bibliografia/referencias.bib` anterior a 2016 en 15 de las 22 entradas: `zienkiewicz2013fem` (2005), `bathe2014fem` (1996), `cook2002concepts` (2002), `hughes2000fem` (1987), `reddy2006introduction` (2006), `onate2009structural` (2009), `timoshenko1970elasticity` (1951), `salari2000mms` (2000), `stimpson2007verdict` (2007), `suarez1998edelas2d` (1998), `lee2015interactive` y `lee2015eigenmodes` (2015), `garciacordoba2005tecnologica` (2005), `strang2008analysis` (1973), `oberkampf2010vv` (2010); `alvarez_metodologia` no tiene año.
- Problema: dos tercios de las fuentes superan los diez años que fija el material docente para libros; son los clásicos del MEF y la excepción «por motivos históricos» los ampara, pero la tesis no lo dice en ningún lugar. B5 debe comprobar si alguna tiene edición más reciente disponible (p. ej. Bathe 2014, Zienkiewicz 7.ª ed. 2013, que son justamente los años que sugieren las claves).
- Sugerencia: una frase en el marco teórico que justifique el uso de las ediciones clásicas.
- Estado: abierto
- Sesión: 1

## 5. Registro de sesiones

| Sesión | Fecha | Bloque(s) | Hallazgos añadidos | Commit de la tesis auditado | Punto donde se detuvo | Siguiente paso |
|---|---|---|---|---|---|---|
| 1 | 2026-09-15 | B0 (auditado) · B1 (auditado) | H-1 a H-14 (1 alta, 8 medias, 5 bajas) | `bdbf18d` (2026-09-11, «Tesis: aplicada la auditoría del 2026-09-11») | B1 completo. Se leyeron `01_introduccion.tex`, `02b_diseno_metodologico.tex`, `00_resumen.tex`, `main.tex` y los 8 PDF del material docente | **B2**: `02_marco_teorico.tex` (414 líneas) y `02b_diseno_metodologico.tex` (ya leído en sesión 1): comprobar que §2.1 sirve a los seis objetivos y que el procedimiento de §2.1.5-2.1.6 es el que aplica `04_resultados.tex`; completar la columna «Metodología» de la trazabilidad. Prestar atención a población/muestra (Taller 4, p. 13) frente a §2.1.4 |
