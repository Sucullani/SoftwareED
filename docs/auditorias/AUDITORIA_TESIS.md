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

**Última sesión**: 7 · 2026-09-16 · **implementación de los hallazgos** por el autor (vía agente) sobre
el commit `bdbf18d`: 45 hallazgos resueltos, 1 parcial (H-13) y 1 abierto (H-1, el Reglamento de
Graduación, que solo el autor puede conseguir). La tesis compila limpia (158 hojas, 0 errores,
0 referencias o citas indefinidas, biber sin avisos, 0 desbordes). **La siguiente sesión programada
debe reauditar**: `git log bdbf18d..HEAD -- tesis/` ya no está vacío. Revisar, bloque por bloque,
que cada «Resolución» anotada bajo su hallazgo esté efectivamente en el texto, y anotar lo que no
cierre como hallazgo nuevo (H-48 en adelante), sin reabrir lo resuelto salvo evidencia.

| Bloque | Contenido | Estado |
|---|---|---|
| B0 | Inventario y norma de citación | **auditado** (sesión 1) |
| B1 | Introducción: problema, objetivos, hipótesis, justificación, alcance | **auditado** (sesión 1) |
| B2 | Marco teórico y metodología | **auditado** (sesión 2) |
| B3 | Resultados | **auditado** (sesión 2) |
| B4 | Conclusiones y recomendaciones | **auditado** (sesión 3) |
| B5 | Citación y referencias contra la norma de B0 | **auditado** (sesiones 3-4: correspondencia cita↔referencia, orden de numeración, formato de las 100 citas, lista impresa entrada por entrada y respaldo de las citas cuestionadas) |
| B6 | Forma: títulos, numeración, jerarquía, preliminares | **auditado** (sesión 4) |

**Estado tras la sesión 7**: 47 hallazgos (H-1 a H-47): **45 resueltos**, **1 parcial** (H-13:
la lista ya se titula «Referencias bibliográficas»; la segunda lista alfabética depende del
Reglamento) y **1 abierto** (H-1, alta: el Reglamento de Graduación). Cada hallazgo lleva bajo su
«Estado» una línea «Resolución» que dice dónde y cómo se cerró; el detalle de lo aplicado está en
`docs/notas/ESTADO.md` (2026-09-16). Lo que sigue en esta sección es el diagnóstico original de las
sesiones 1-4, conservado como registro.

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
resumen y la introducción. Contrastado en B6 (sesión 4): ver la cabecera de esa sección y
H-46, H-47.

## 3. Tabla de trazabilidad

Objetivos tomados de `tesis/capitulos/01_introduccion.tex:33-40` (sesión 1). Columnas de
metodología y resultado completadas en la sesión 2 (B2 y B3); columna de conclusión y estado
definitivo cerrados en la sesión 3 (B4). Referencias de sección: §2.1.x =
`02b_diseno_metodologico.tex`, §3.x = `04_resultados.tex`, `05:n` = línea de
`05_conclusiones.tex`.

| # | Objetivo específico (abreviado) | Metodología que lo atiende (B2) | Resultado que lo responde (B3) | Conclusión que lo cierra (B4) | Estado |
|---|---|---|---|---|---|
| OE1 | Fundamentar teóricamente el MEF en elasticidad plana con Q4/Q9 (formulación, mapeo, integración, ensamblaje, tensiones, calidad de malla, criterios de V&V) | Solo la fila 1 de la matriz de consistencia (§2.1.3: «Revisión de la literatura clásica del MEF y de la V&V», evidencia Cap. 1). Sin variable en la Tabla 2.1 ni criterio en §2.1.6. El Cap. 1 (§1.2–1.11) cubre los siete ítems enunciados; no cubre la dimensión pedagógica (H-19) | Ninguno en el Cap. 3: el Cap. 1 es el producto (H-26) | `05:11`: «se sistematizó el MEF … anclado a la literatura clásica»; remite solo al Cap. 1 y a cuatro citas. Ningún resultado detrás (H-33) | **débil**: objetivo de fundamentación cerrado por una conclusión que describe el capítulo, no un resultado |
| OE2 | Implementar un motor MEF 2D Q4/Q9 «verificado numéricamente» | §2.1.1 (desarrollo iterativo + regresión), §2.1.5 (procedimiento e instrumentos), §2.1.6 (criterio MMS ±0,5). La misma evidencia que OE5 (H-8) | §3.2 MMS (`tab:mms`, `tab:mms-configs` en Anexo D) y §3.3 consistencia interna (Q4→Q9→Q4, ids no contiguos) | `05:13`: enumera el canal implementado y reporta las tasas MMS (2,00/1,00; 3,00/2,00; σ* 1,5 y 2). Cifras coinciden con `tab:mms`. Repite el MMS que `05:19` vuelve a atribuir a OE5 (H-8 confirmado) | **completo** (solapado con OE5) |
| OE3 | Diseñar una interfaz interactiva pre/proceso/post con un único lienzo | Solo la fila 3 de la matriz («Organización de la interfaz; flujo de trabajo» → «Diseño centrado en un lienzo único», evidencia §2.2.6 pre-proceso únicamente). Sin variable en la Tabla 2.1, sin instrumento ni criterio (H-17, H-24) | §3.6, prosa (`04:211-213`: conmutador Fórmula↔Valores, selección en el lienzo, post-proceso). Sin figura, tabla ni medida (H-26) | `05:15`: «se logró una aplicación organizada en las tres fases … único lienzo»; sus atributos (selección bidireccional, deshacer/rehacer, salud del modelo, minimalismo) vienen de `03:108, 110, 148` (descripción de diseño) y de dos citas, no del Cap. 3 (H-33, H-39) | **débil**: conclusión sin resultado, apoyada en la descripción del Cap. 2 |
| OE4 | Desarrollar módulos educativos que expongan paso a paso cada etapa del canal de cálculo | Fila 4 de la matriz («Cobertura del canal de cálculo» → «Capas interactivas superpuestas a la malla real»). Sin instrumento ni criterio de cobertura (H-17) | §3.6 (`04:209`): cobertura «completa hasta el ensamblaje»; la recuperación de tensiones «no tiene un módulo propio». El objetivo pedía *cada etapa* (H-25) | `05:17`: «cada etapa del canal de cálculo del MEF, del mapeo isoparamétrico al ensamblaje global»; `05:23`: «satisface los seis objetivos». El cumplimiento parcial de `04:209` no se declara (H-25, H-32) | **hueco**: resultado parcial presentado como completo en la conclusión |
| OE5 | Verificar y validar con MMS, viga de Timoshenko y membrana de Cook, contra soluciones analíticas y SAP2000 | §2.1.4 casos, §2.1.5 instrumentos (`tests/vv_*.py`, CSV), §2.1.6 criterios (MMS ±0,5 en 4 configuraciones; Timoshenko flecha < 3 %; Cook Q9 N=8 < 1,5 % y Q4 < Q9). Pero Timoshenko no sigue el procedimiento declarado (H-15), el criterio de σ* no es teórico (H-16) y no hay criterio para σx ni para SAP2000 (H-23) | §3.2 (`tab:mms`), §3.4 (`tab:timoshenko-stress`, `tab:timoshenko-defl`), §3.5 (`tab:cook`), `tab:resumen-q4q9`; componentes secundarias y desplazamientos solo en Anexo D (H-27) | `05:19`: «batería de tres niveles»; 0,04 % σx, 0,26 % flecha, 2,9 % cortante, 0,21 % y 0,56 % frente a SAP2000, Cook −0,044 % vs −0,594 %. Todas las cifras coinciden con `04:113-115, 132, 166-167, 219` y `06:593, 611`; el 2,9 % y el 0,56 % siguen viniendo del Anexo D (H-27). Incluye la salvedad de «validación» (H-20) | **completo con reservas** (H-15, H-27) |
| OE6 | Generar memoria de cálculo automática en PDF y ofrecer interoperabilidad DXF/CSV | Fila 6 de la matriz («Trazabilidad del cálculo» → «Generación de PDF; importación/exportación DXF y CSV»), sin pregunta (H-7); §2.1.5 anuncia la regresión de interoperabilidad. Sin criterio (H-17) | §3.3 tercer párrafo (`04:95`: ida y vuelta CSV/ZIP, DXF idempotente, `test_memoria_calculo.py`) y §3.6 último párrafo (memoria, prosa); Anexo G | `05:21`: memoria «en dos estilos (educativo y directo)» (de `03:167`) e interoperabilidad «verificado por ida y vuelta y por idempotencia» (remite a `sec:consistencia-interna`). La parte de interoperabilidad cierra sobre un resultado; la memoria, sobre la descripción del Cap. 2 | **débil** (la memoria, diferenciador principal según la Justificación, solo tiene una mención de test y prosa) |
| H | Hipótesis de diseño: es factible construir un software que exponga el canal de cálculo completo de forma transparente, interactiva, numéricamente verificable y coherente con el flujo profesional; esa transparencia es «un apoyo plausible al aprendizaje» | §2.1.6: «se contrasta por diseño»; solo PI-1 y PI-3 tienen criterio numérico; PI-2 «se documenta» (H-5, H-17) | §3.9 (`04:258`): «queda confirmada al verificarse … cada uno de esos atributos»; PI-1 y PI-3 con cifras; PI-2 «por diseño». Afirma que los módulos «la exponen paso a paso» pese a `04:209` (H-25) | `05:23`: «Confirman también la hipótesis de diseño … La verificación de esa hipótesis se estableció por diseño»; el apoyo al aprendizaje «se sostiene por diseño y en la literatura» (H-5, H-39). La cláusula pedagógica se traslada a Limitaciones (`05:37`) y a la recomendación final (`05:51`) | **débil**: no falsable (H-5); su segunda cláusula se declara no contrastada y aun así «confirmada» |

**Estado de la trazabilidad tras la sesión 7**: OE1 → fundamento declarado como tal en §3.9 y
Conclusiones (ya no se presenta como resultado); OE2 → completo (sin «verificado numéricamente»);
OE3 → completo (Tabla 3.6 y Figura 3.5 en §3.6; conclusión sobre lo observado); OE4 → completo en
sus términos reformulados (módulos hasta el ensamblaje; post-proceso y memoria completan), con la
cobertura contada 7/7 y 9/9; OE5 → completo (procedimiento real declarado; criterios para σx,
SAP2000 y equilibrio; 0,56 % en el capítulo); OE6 → completo (PI-2, indicador propio, memoria
generada para Q4 y Q9); H → hipótesis condicional comprobable, contrastada cláusula por cláusula.

Lo que la propia Introducción declara sobre dónde se cumple cada uno
(`01_introduccion.tex:69`): OE1 → Cap. 1; OE2, OE3, OE4, OE6 → Cap. 2; OE5 → Cap. 3;
la hipótesis se contrasta en el Cap. 3 y se discute en Conclusiones. B2 y B3 lo verificaron:
el reparto se cumple, pero el Cap. 3 no aporta resultado propio para OE1 ni OE3 (H-26) y el
de OE4 es parcial (H-25). B4 confirmó que las Conclusiones siguen ese mismo orden (una
conclusión por objetivo, `05:11-21`) y que el veredicto global (`05:23`) declara los seis
cumplidos sin matiz (H-32). Las Conclusiones no añaden cifras ajenas al Cap. 3 (todas las
comprobadas están en `04_resultados.tex` o en el Anexo D); la información nueva aparece en las
Recomendaciones (H-34, H-35).

## 4. Hallazgos

### B0 — Inventario y norma

**H-1**
- Bloque y sección: B0 · documentos de referencia
- Tipo: forma
- Severidad: **alta**
- Evidencia: el Taller 1 (p. 18) enumera lo que fija el «REGLAMENTO DE GRADUACIÓN DE LA CARRERA DE INGENIERÍA CIVIL»: «Formatos · Tamaño de hoja · Márgenes admitidos · Tipo de letra · Interlineado · Componentes generales del documento · Referenciación · Estructura de listas · Contenido sugerido · Estructura de la bibliografía». Ese reglamento no está en `tesis/`, `tesis/normas/` ni `tesis/Material docente/` (solo extractos de los arts. 2, 6, 8, 9 y 40 en el Taller 1, p. 2-4). La auditoría del 2026-09-11 ya lo anotó: «Reglamento de la UATF: … No se cotejó».
- Problema: la norma de presentación vigente (APA 7, adoptada el 2026-09-10 según `tesis/README.md`) y la de citación (Vancouver) se eligieron sin el documento que, según el propio material del tribunal, regula formato, interlineado, referenciación y estructura de la bibliografía. B5 y B6 solo pueden contrastar contra los resúmenes de los talleres.
- Sugerencia: conseguir el Reglamento de Graduación (texto completo) y dejarlo en `tesis/normas/` o anotar en `tesis/README.md` que no existe versión escrita accesible.
- Estado: **abierto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): el Reglamento de Graduación no está en el repositorio y solo el autor puede conseguirlo; queda como única acción pendiente del autor. Lo que dependía de él y sí se podía decidir (H-2, H-12, H-13) se resolvió contra los talleres.
- Sesión: 1

**H-2**
- Bloque y sección: B0 · norma de citación
- Tipo: citación
- Severidad: media
- Evidencia: Taller 2, p. 20: «Exponer la normativa que utiliza, para el desarrollo de su investigación para su graduación (tesis, proyecto de grado)». En la tesis, la única declaración de la norma está en un comentario LaTeX invisible: `tesis/main.tex:70` «% ----- Bibliografia (estilo Vancouver) -----». Búsqueda de «Vancouver», «APA» y «norma» en `tesis/capitulos/*.tex`: 0 resultados en texto visible.
- Problema: el tribunal no puede saber contra qué norma juzgar las citas ni por qué la lista es numérica por orden de aparición. El material docente pide exponerlo explícitamente; el documento lo omite.
- Evidencia adicional (sesión 4): la única frase de la tesis que alude a la norma tampoco la nombra —`00_preliminares.tex:11`: «se encuentran debidamente referenciados conforme a la norma de citación adoptada en este documento»— y ese archivo está desactivado en `main.tex:41` («% \input{capitulos/00_preliminares}»). Además, los dos desvíos deliberados de Vancouver (títulos de revista completos, «y» antes del último autor) viven solo en `tesis/README.md:10-12`, invisible al tribunal, mientras el Taller 2 (p. 19) recomienda expresamente lo contrario: «Los títulos de las revistas deben abreviarse según el estilo que utiliza la normativa de referenciación». La frase que declare la norma debe declarar también esos dos desvíos.
- Sugerencia: una frase en la Introducción (en «Estructura del documento») o al pie de la Bibliografía: «Las citas y referencias siguen la norma Vancouver (ICMJE/NLM), con títulos de revista completos y conjunción antes del último autor; la presentación, APA 7.ª ed.».
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): `01_introduccion.tex`, «Estructura del documento»: frase que declara la norma Vancouver (ICMJE/NLM), la numeración por orden de primera mención, los corchetes (justificados: permiten acompañar el número con la página), los dos desvíos (títulos de revista completos, «y» ante el último autor), la regla de los localizadores y la presentación APA 7. `00_preliminares.tex` nombra Vancouver; la lista pasó a titularse «Referencias bibliográficas».
- Sesión: 1

### B1 — Introducción

**H-3**
- Bloque y sección: B1 · Planteamiento del problema (y su eco en §2.1.3)
- Tipo: coherencia
- Severidad: media
- Evidencia: el problema se formula tres veces y de tres maneras. (a) `01_introduccion.tex:13`: «¿cómo apoyar la comprensión de los fundamentos del MEF mediante una herramienta de software que exponga, sobre un modelo concreto y de manera interactiva, cada etapa del procedimiento de cálculo…?». (b) `01_introduccion.tex:15`: «el problema científico … ¿cómo debe construirse un software educativo para que exponga de forma transparente, interactiva y numéricamente verificable el canal de cálculo completo del MEF en elasticidad plana…?». (c) `02b_diseno_metodologico.tex:43`: «El problema general —la ausencia de un entorno educativo libre y de código abierto, en español, que exponga de forma transparente, interactiva y verificable el canal de cálculo completo del MEF en elasticidad plana y genere una memoria de cálculo trazable al modelo del alumno—».
- Problema: (a) pregunta por cómo apoyar la comprensión (el «para qué», que `tesis/README.md` dice que no es lo medido); (b) pregunta por cómo construir el software; (c) ya no es una interrogante sino una carencia, y añade atributos que el problema científico no contiene («libre y de código abierto», «en español», «memoria de cálculo»). El planteamiento del tribunal (Miranda, p. 3) pide una sola interrogante con dos variables; la matriz de consistencia debería partir de la misma formulación que la Introducción.
- Evidencia adicional (sesión 2): cuarta formulación en `02_marco_teorico.tex:43`: «La brecha que lo motiva es, por tanto, la ausencia de un entorno integrado, libre y de código abierto, que recorra el canal de cálculo completo … haciendo observables los fenómenos numéricos del método, generando una memoria de cálculo trazable a ese modelo e incorporando verificación y validación rigurosas», que suma dos atributos más (fenómenos numéricos observables, V&V) a la lista de (c).
- Sugerencia: dejar (b) como problema científico único, reescribir (a) como pregunta orientadora subordinada o quitarla, y que §2.1.3 cite (b) textualmente.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): la pregunta orientadora de `01:13` se eliminó; el problema científico queda como formulación única, y la Introducción lo dice; `02b` §2.1.3 lo cita textualmente; la «brecha» del Cap. 1 remite al problema y trata los atributos restantes (licencia, idioma, memoria, fenómenos, V&V) como requisitos de §2.2.1.
- Sesión: 1

**H-4**
- Bloque y sección: B1 · Planteamiento del problema → §2.1.2 Variables
- Tipo: coherencia
- Severidad: media
- Evidencia: `01_introduccion.tex:15`: «La variable causa es la forma en que la herramienta expone ese canal —transparencia, interactividad y verificabilidad numérica—; la variable efecto es la observabilidad y contrastabilidad del procedimiento intermedio que el software profesional encapsula». `02b_diseno_metodologico.tex:21`: «La variable independiente reúne la definición del modelo estructural … y las decisiones de discretización … La variable dependiente es la respuesta estructural calculada … junto con su exactitud». `02b_diseno_metodologico.tex:90`: «estos tres elementos no deben confundirse con las variables del experimento numérico de la Tabla 2.1, que son las que efectivamente se miden». Material docente (Miranda, p. 5): «Las variables son los aspectos del objeto de estudio que serán medidos».
- Problema: la variable efecto del problema científico («observabilidad y contrastabilidad») no aparece en la Tabla 2.1 ni tiene indicador ni instrumento; lo que se mide (errores, tasas de convergencia) responde a otra pareja VI/VD. La tesis lo reconoce y lo declara fuera de medición, con lo que el problema científico queda sin variable medida. Reincidente de la revisión del 2026-06-10 («variable independiente con dos significados»); es decisión del autor del 2026-09-08 (`tesis/README.md`), pero el hueco sigue en el texto.
- Sugerencia: dar a la variable efecto un indicador observable en la Tabla 2.1 (p. ej. «cobertura del canal de cálculo: etapas con módulo + memoria», que la matriz ya usa para OE4) o renombrar las de la Tabla 2.1 como «variables del experimento numérico» sin llamarlas independiente/dependiente.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): la Tabla 2.1 abre con la fila «Atributos del artefacto (variables del problema científico)» con indicadores contables —etapas con módulo y con desarrollo en la memoria, fases que comparten el lienzo, formatos con ida y vuelta— e instrumentos; §2.1.6 fija sus criterios y §3.6 los reporta (7/7, 9/9, tres fases, formatos).
- Sesión: 1

**H-5**
- Bloque y sección: B1 · Hipótesis o preguntas de investigación
- Tipo: coherencia
- Severidad: media
- Evidencia: `01_introduccion.tex:44`: «La hipótesis de diseño sostiene que es factible construir un software educativo que exponga el canal de cálculo completo del MEF … La verificación de esta hipótesis es, en consecuencia, por diseño: se establece comprobando que la herramienta cumple esos atributos». Título de la sección (`01_introduccion.tex:42`): «Hipótesis o preguntas de investigación». Material docente (Miranda, p. 12-14): la hipótesis «Es una proposición que necesita ser verificado», «Debe ser formulado en términos afirmativos», «debe estar en tiempo Futuro», y el flujograma exige responder «¿SE PUEDE COMPROBAR LA HIPÓTESIS?».
- Problema: «es factible construir X» se comprueba construyendo X: la hipótesis no puede resultar falsa una vez que el software existe (reincidente de la revisión del 2026-06-10, «hipótesis circular»). Su segunda cláusula —«esa transparencia constituye un apoyo plausible al aprendizaje»— se declara no contrastable. El título con «o» deja abierto si el trabajo tiene hipótesis o solo preguntas. Es decisión documentada del autor («validación por diseño»), pero el material del tribunal exige comprobabilidad.
- Sugerencia: formular la hipótesis sobre lo que sí se mide («el motor reproducirá las tasas teóricas de convergencia y errores < 3 % frente a Timoshenko/SAP2000, y evidenciará el bloqueo del Q4») y dejar el «apoyo al aprendizaje» como supuesto fundamentado, no como hipótesis; titular «Hipótesis y preguntas de investigación».
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): hipótesis de diseño reescrita en forma condicional comprobable con tres cláusulas —(a) tasas teóricas y errores < 3 % flecha / < 1 % σx frente a Timoshenko y SAP2000; (b) bloqueo del Q4 frente al Q9; (c) cada etapa observable en módulo o memoria— con criterios a priori en §2.1.6; el apoyo al aprendizaje pasa a «supuesto» declarado no contrastado; título «Hipótesis y preguntas de investigación»; §3.9 y Conclusiones la contrastan cláusula por cláusula. Se conserva la figura de hipótesis de diseño (García-Córdoba p. 85), decisión del autor.
- Sesión: 1

**H-6**
- Bloque y sección: B1 · Objetivos (objetivo general) ↔ título
- Tipo: coherencia
- Severidad: media
- Evidencia: título (`tesis/main.tex:20`): «Desarrollo de software educativo de elementos finitos para el análisis estructural **empleando el lenguaje de programación Python**». Objetivo general (`01_introduccion.tex:29`): «desarrollar EduFEM, un software educativo de escritorio para el análisis por el Método de los Elementos Finitos (MEF) de problemas bidimensionales de elasticidad lineal … que integre la formulación matemática, la construcción y visualización interactiva del modelo y la verificación numérica, como apoyo a la enseñanza y el aprendizaje del MEF». La palabra «Python» no aparece en toda la Introducción (0 ocurrencias en `01_introduccion.tex`). Material docente («Cómo se construye el objetivo general», p. 2-4): el OG lleva «Un verbo en modo infinitivo · Un ¿Qué cosa? · Un ¿Cómo? · Un ¿Para qué?».
- Problema: el «cómo» del título (Python) no está en el objetivo general ni en ningún lugar de la Introducción; el OG tiene verbo, qué y para qué, pero el «cómo» que enuncia («que integre…») no es el del título. Título y OG deben hablar del mismo alcance con los mismos términos.
- Sugerencia: «…desarrollar, en el lenguaje de programación Python y con bibliotecas numéricas de código abierto, EduFEM, un software…», o quitar «empleando … Python» del título (decisión pendiente del autor según `tesis/README.md`).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): el objetivo general dice «desarrollar, en el lenguaje de programación Python y sobre bibliotecas numéricas de código abierto, EduFEM…»; la conclusión general lo repite.
- Sesión: 1

**H-7**
- Bloque y sección: B1 · Objetivos específicos (OE6) ↔ §2.1.3 matriz de consistencia
- Tipo: coherencia
- Severidad: baja
- Evidencia: `01_introduccion.tex:39`: «Generar documentación de cálculo automática (memoria de cálculo en PDF) **y** ofrecer interoperabilidad de datos (DXF, CSV)». `02b_diseno_metodologico.tex:61`: fila de la matriz con «Pregunta asociada: ---»; `:69`: «El sexto objetivo específico … es de carácter instrumental: no deriva de una pregunta de investigación propia».
- Problema: un objetivo con dos productos distintos (memoria de cálculo; importación/exportación) y sin pregunta de investigación. La memoria de cálculo es, según la Justificación (`01_introduccion.tex:23`), el diferenciador principal frente a los antecedentes; la interoperabilidad es un accesorio. Juntarlos diluye el primero y deja un objetivo que la matriz no puede trazar a ninguna pregunta.
- Sugerencia: separar (OE6 memoria de cálculo, ligado a PI-2; interoperabilidad como requisito del software en §2.2) o justificar en la matriz por qué un objetivo sin pregunta sigue siendo objetivo.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): OE6 reordenado: la memoria de cálculo es lo principal y la interoperabilidad su complemento instrumental; la matriz le asocia PI-2, un indicador («etapas con desarrollo numérico en la memoria; formatos con ida y vuelta») y evidencia (§2.2.9, Anexo G, §3.3); el párrafo de justificación se reescribió.
- Sesión: 1

**H-8**
- Bloque y sección: B1 · Objetivos específicos (OE2 y OE5)
- Tipo: coherencia
- Severidad: baja
- Evidencia: OE2 (`01_introduccion.tex:35`): «Implementar un motor de cálculo MEF 2D … **verificado numéricamente**». OE5 (`:38`): «**Verificar y validar** el software mediante el método de soluciones manufacturadas (MMS) y casos de referencia clásicos…». Matriz (`02b_diseno_metodologico.tex:57,60`): OE2 → evidencia «Cap. 3 (MMS)»; OE5 → evidencia «Cap. 3».
- Problema: la verificación numérica figura como atributo de OE2 y como objetivo propio en OE5, y la misma evidencia (MMS) responde a los dos. B3 no podrá asignar un resultado exclusivo a cada uno.
- Sugerencia: quitar «verificado numéricamente» de OE2 (la verificación es OE5).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): «verificado numéricamente» retirado de OE2 y de su fila en la matriz.
- Sesión: 1

**H-9**
- Bloque y sección: B1 · terminología (Introducción ↔ §2.1)
- Tipo: coherencia
- Severidad: baja
- Evidencia: «canal de cálculo» en `01_introduccion.tex:15, 17, 37, 44` y `02b_diseno_metodologico.tex:16, 43, 59, 90`; «cadena de cálculo» en `01_introduccion.tex:50` («exponer la cadena de cálculo del MEF») y `02b_diseno_metodologico.tex:67` («expone la cadena de cálculo de forma transparente»); «cadena algebraica» en `01_introduccion.tex:9`; «cada etapa del cálculo» en `00_resumen.tex:5`.
- Problema: el concepto central de la tesis (la secuencia mapeo → J → B → D → K → ensamblaje → solución → tensiones) se nombra con dos términos en la propia definición de PI-2 y en su reformulación de §2.1.3. El criterio de coherencia pide los mismos términos entre secciones.
- Evidencia adicional (sesión 2): «cadena» también en `02_marco_teorico.tex:40` («recorre la cadena del MEF de extremo a extremo»), `:412` («la cadena de recuperación de tensiones») y `04_resultados.tex:207` («cada eslabón de la cadena de cálculo»); «canal» en `04_resultados.tex:5, 209, 258`.
- Sugerencia: «canal de cálculo» en todo el documento (es el que usan el problema científico, el objeto y la hipótesis).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): «canal de cálculo» en todo el documento (incluida PI-2 y la nota de la Tabla 1.1); «cadena» queda solo en «regla de la cadena» (matemática) y «cadena de texto» (formato); la recuperación de tensiones y la sustitución numérica se llaman «secuencia».
- Sesión: 1

**H-10**
- Bloque y sección: B1 · Metodología de la investigación ↔ §2.1.1
- Tipo: coherencia
- Severidad: baja
- Evidencia: `01_introduccion.tex:56`: «Según su nivel u objetivo, la investigación es **descriptiva** y **comparativa**: caracteriza el comportamiento numérico del modelo y contrasta…». `01_introduccion.tex:58`: «El diseño metodológico … se desarrolla en detalle en la Sección 2.1». En `02b_diseno_metodologico.tex` no aparecen «descriptiva» ni «comparativa» (0 ocurrencias); §2.1.1 solo retoma «propositivo», «aplicada de tipo tecnológico» y «cuantitativo».
- Problema: la sección que dice desarrollar «en detalle» la tipificación de la Introducción omite uno de sus cuatro ejes (el nivel). Un lector del Cap. 2 no encuentra el sustento de «descriptiva y comparativa».
- Sugerencia: repetir el nivel en §2.1.1 con su cita, o quitarlo de la Introducción.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): §2.1.1 incorpora el nivel descriptivo y comparativo junto con finalidad, naturaleza y enfoque.
- Sesión: 1

**H-11**
- Bloque y sección: B1 · Hipótesis ↔ §2.1.6
- Tipo: coherencia
- Severidad: baja
- Evidencia: `01_introduccion.tex:44`: «En la nomenclatura de tres variables del diseño clásico de investigación, el aporte es EduFEM; el atributo manipulado, la transparencia, interactividad y verificabilidad con que se expone el canal de cálculo; y el efecto esperado, la observabilidad y contrastabilidad del procedimiento como apoyo a la comprensión de sus fundamentos, en correspondencia con las variables del problema científico. Esa correspondencia se desarrolla en la Sección 2.1.6». `02b_diseno_metodologico.tex:90`: «En la nomenclatura del diseño clásico de investigación, el aporte es EduFEM, el atributo manipulado es la transparencia e interactividad con que se presenta el canal de cálculo, frente a la opacidad del software profesional y la abstracción de los textos clásicos, y el efecto esperado es la observabilidad y contrastabilidad del procedimiento, como apoyo a la comprensión de los fundamentos del MEF, en correspondencia con las variables del problema científico».
- Problema: la Introducción promete que §2.1.6 «desarrolla» la correspondencia, pero §2.1.6 la repite casi palabra por palabra sin añadir nada. Además, el «atributo manipulado» pierde la «verificabilidad» entre una versión y otra (Intro: «transparencia, interactividad y verificabilidad»; §2.1.6: «transparencia e interactividad»).
- Sugerencia: dejar el párrafo en un solo lugar y unificar los tres atributos.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): el puente de tres variables se enuncia en la Introducción con los tres atributos (transparencia, interactividad, verificabilidad) y remite; §2.1.6 lo desarrolla de verdad: liga cada elemento a las decisiones de §2.2 y a los indicadores de la Tabla 2.1.
- Sesión: 1

### B2 — Marco teórico y metodología

**H-15**
- Bloque y sección: B2 · §2.1.4 Casos de estudio y §2.1.5 Procedimiento ↔ §3.4 Validación con la viga de Timoshenko
- Tipo: coherencia
- Severidad: media
- Evidencia: `02b_diseno_metodologico.tex:74`: «Cada uno se resuelve con ambos tipos de elemento (Q4 y Q9) sobre mallas de refinamiento creciente, lo que permite observar el comportamiento de las variables dependientes en función de las independientes». `:81`: «Dentro de cada caso solo se manipulan el tipo de elemento y la densidad de malla». `04_resultados.tex:99`: «Se empleó una malla Q9 estructurada de $56\times8$ elementos (448 elementos, 1921 nodos, 3842 GDL)». `04_resultados.tex:199` (tabla resumen): «Timoshenko $\sigma_x$ (error máx.) & --- & 0,0414\,\%» (columna Q4 vacía). Instrumento: `tests/vv_timoshenko.py:87-88, 133`: `NX = 56`, `NY = 8`, `element_type=ELEMENT_Q9`, sin bucle de refinamiento ni corrida Q4.
- Problema: la metodología enuncia un procedimiento común a los tres casos («cada uno … ambos tipos de elemento … mallas de refinamiento creciente») que el único caso con referencia analítica y comercial no sigue: una sola malla, un solo elemento. En ese caso la variable independiente «discretización» de la Tabla 2.1 no se manipula, no se observa convergencia ni se contrasta Q4 con Q9. Lo que el Cap. 3 aplica no es lo que §2.1 declara.
- Sugerencia: o correr Timoshenko con Q4 y con al menos tres mallas (el guion lo permite) o reescribir §2.1.4 diciendo que el refinamiento y la comparación Q4/Q9 se hacen en MMS y Cook, y que Timoshenko es un contraste puntual con Q9.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): §2.1.4 describe el procedimiento real: refinamiento y comparación Q4/Q9 en MMS y Cook (N = 2…32); Timoshenko con una única malla fina Q9 como contraste puntual de exactitud; §2.1.5, §3.4 y la nota de la Tabla 3.5 lo reiteran.
- Sesión: 2

**H-16**
- Bloque y sección: B2 · §2.1.6 Criterios de aceptación ↔ instrumento `tests/vv_mms.py`
- Tipo: coherencia
- Severidad: media
- Evidencia: `02b_diseno_metodologico.tex:88`: «Los criterios de aceptación están fijados a priori en los propios guiones … tasas de convergencia observadas dentro de $\pm0{,}5$ de las teóricas en las cuatro configuraciones del MMS (desplazamiento y campo de tensiones recuperado)». `tests/vv_mms.py:439-443`: «# Campo de tensiones recuperado: O(h^1.5) Q4 (superconvergencia interior degradada por la capa de contorno) y O(h^2) Q9. # Tolerancia +-0.5 por la desviacion pre-asintotica … `expected = {"q4": (2.0, 1.0, 1.5), "q9": (3.0, 2.0, 2.0)}`». `02_marco_teorico.tex:412`: «el error de las magnitudes derivadas debe verificarse por separado, y su orden puede ser menor que el de la solución primaria» (sin valor). `04_resultados.tex:58` explica el 1,54 a posteriori: «que no alcance $\mathcal{O}(h^{2})$ se debe a la capa de contorno».
- Problema: para el campo de tensiones recuperado del Q4 no existe tasa «teórica» en el marco teórico ni en la literatura citada; el 1,5 del guion es el valor observado realimentado como expectativa, y el intervalo ±0,5 a su alrededor (1,0–2,0) acepta también el orden del gradiente crudo. El criterio no está «fijado a priori» para ese indicador y, además, es demasiado laxo para detectar una regresión en la extrapolación de tensiones.
- Sugerencia: reservar el criterio de «tasa teórica» a $L^2$ y $H^1$ del desplazamiento, y para $\sigma^*$ enunciar el criterio como cota empírica (≥ 1,4 en Q4, ≥ 1,9 en Q9) declarada como tal.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): el criterio de σ* es ahora una cota empírica mínima declarada como tal (≥ 1,4 en Q4, ≥ 1,9 en Q9) en §2.1.6 y en `tests/vv_mms.py`; el guion se corrió: las 8 combinaciones (4 configuraciones × 2 elementos) pasan (obs. 1,53–1,55 y 2,00).
- Sesión: 2

**H-17**
- Bloque y sección: B2 · §2.1.2 Variables ↔ §2.1.3 Matriz de consistencia ↔ §2.1.6 Criterios
- Tipo: coherencia
- Severidad: media
- Evidencia: indicadores de la matriz (`02b_diseno_metodologico.tex:56-61`): OE1 «Canal de cálculo cubierto», OE3 «Organización de la interfaz; flujo de trabajo», OE4 «Cobertura del canal de cálculo», OE6 «Trazabilidad del cálculo». Ninguno figura en la Tabla 2.1 (`:27-38`), cuyas filas son «definición del modelo», «discretización», «respuesta estructural», «exactitud de la solución» y «controladas». §2.1.6 (`:88-90`) fija criterios numéricos solo para MMS, Timoshenko y Cook y despacha el resto: «la organización de la interfaz y de los módulos (PI-2) se documenta en la \autoref{sec:diseno-edufem}». Taller 4, p. 10: «Definición y operacionalización de las variables, Procedimientos a seguir, Técnicas e instrumentos de medición, Plan de análisis o valoración de los resultados obtenidos».
- Problema: cuatro de los seis objetivos tienen un indicador nominal en la matriz pero ningún instrumento ni criterio con el que el Cap. 3 pueda declararlos cumplidos o no. El resultado es que «cobertura del canal» se juzga sin escala (y en `04_resultados.tex:209` resulta parcial sin que nada lo califique de incumplimiento, H-25). Complementa H-4 (variable efecto sin indicador) y H-5 (hipótesis por diseño).
- Sugerencia: agregar a la Tabla 2.1 una fila «atributos del artefacto» con indicadores contables (etapas del canal con módulo / con memoria; fases con lienzo compartido; formatos con prueba de ida y vuelta) y su umbral en §2.1.6.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): ver H-4: fila «Atributos del artefacto» en la Tabla 2.1, criterios en §2.1.6, matriz con indicador y evidencia por objetivo, §3.6 con el conteo.
- Sesión: 2

**H-18**
- Bloque y sección: B2 · Cap. 1 Marco teórico (§1.5, §1.9, §1.10, §1.11)
- Tipo: coherencia
- Severidad: media
- Evidencia: `02_marco_teorico.tex:182`: «EduFEM impone un umbral mínimo ($\texttt{JACOBIAN\_MIN\_DETERMINANT}$) para detectar y rechazar esas geometrías antes de resolver». `:302`: «EduFEM selecciona el ordenamiento de columnas de mínimo grado sobre $\bm{K}^{T}+\bm{K}$ (opción \texttt{MMD\_AT\_PLUS\_A} de \texttt{scipy.sparse.linalg.splu} …)». `:321`: «la verificación del \autoref{cap:resultados} muestra que el campo recuperado converge de todos modos a $\mathcal{O}(h^{2})$». `:395`: «se exige $q_{SJ} \ge 0{,}7$, $R_J \ge 0{,}5$, $AR \le 3$ y $T_R \le 0{,}3$ … para «buena», y $0{,}3$, $0{,}2$, $5$ y $0{,}5$ … para «aceptable»». `:414`: «EduFEM la reproduce con errores inferiores al $0{,}3\,\%$ en las magnitudes primarias —tensión normal y flecha—, que el \autoref{cap:resultados} cuantifica en detalle». «EduFEM» aparece 25 veces en el capítulo. Taller 1, p. 20: «Capítulo 1 MARCO TEÓRICO DE …» separado de «Capítulo 2 DISEÑO E IMPLEMENTACIÓN DEL MODELO A DESARROLLAR» y «Capítulo 3 PRESENTACIÓN DE RESULTADOS».
- Problema: el marco teórico adelanta resultados del Cap. 3 (0,3 %, $\mathcal{O}(h^{2})$) y fija decisiones de implementación (constantes del programa, opción del solucionador, umbrales de la interfaz) que son materia del Cap. 2 §2.2. El lector encuentra las cifras de validación antes de la metodología que las produce, y la fundamentación deja de ser independiente del artefacto que debería sustentar.
- Sugerencia: dejar en el Cap. 1 la teoría y las referencias bibliográficas de cada umbral; mover a §2.2 las elecciones de EduFEM y al Cap. 3 toda cifra medida.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): el umbral `JACOBIAN_MIN_DETERMINANT`, la opción `MMD_AT_PLUS_A` y los cortes de calidad (0,50 / 0,80 / estado global) se movieron a §2.2.5 y §2.2.6; el Cap. 1 conserva la teoría y los mínimos bibliográficos de Verdict; se retiraron el O(h²) anticipado y el 0,3 % de la sección de V&V; Cholesky queda como teoría en la sección de resolución del sistema.
- Sesión: 2

**H-19**
- Bloque y sección: B2 · Cap. 1 Marco teórico ↔ objetivo general e hipótesis
- Tipo: coherencia
- Severidad: media
- Evidencia: objetivo general (`01_introduccion.tex:29`): «como apoyo a la enseñanza y el aprendizaje del MEF». Hipótesis (`:44`): «esa transparencia constituye un apoyo plausible al aprendizaje de sus fundamentos». Metodología (`:56`): «los criterios de diseño pedagógico se fundamentan cualitativamente en la literatura sobre enseñanza del MEF». Cap. 1: §1.1 «Antecedentes y estado del arte» (revisión de software) y §1.2–§1.11, todas numéricas; las palabras «aprendizaje», «pedagógico», «didáctico» y «enseñanza» aparecen solo en `02_marco_teorico.tex:4-43` (antecedentes), `:263` y `:382`. OE1 (`01_introduccion.tex:34`) enumera únicamente contenidos numéricos.
- Problema: la finalidad del objetivo general y la segunda cláusula de la hipótesis descansan en una afirmación pedagógica (la transparencia del cálculo apoya el aprendizaje) que el marco teórico no fundamenta: no hay sección sobre por qué hacer visibles los pasos intermedios favorece la comprensión, ni sobre qué principio guía el conmutador Fórmula↔Valores, el lienzo único o el orden M0–M7. Las citas de Lee y Bishay se usan como antecedentes de software, no como marco. Taller 5, p. 3: «Cada dimensión o indicador debe tener el contraste de la teoría y los antecedentes».
- Sugerencia: una sección «Fundamentos de la enseñanza del MEF» en el Cap. 1 (o quitar «aprendizaje» del objetivo general y de la hipótesis y dejarlo en la justificación).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): nueva §1.2 «Fundamentos pedagógicos de la enseñanza del MEF»: cuatro principios (visibilidad del procedimiento, interactividad con vínculo al modelo, construcción paso a paso, conexión fundamento–operación) citados con página y con sus límites (Lee cualitativo, Bishay atribuye la mejora a la autoría del alumno); referida desde §2.2.1 y Conclusiones.
- Sesión: 2

**H-20**
- Bloque y sección: B2 · §1.11 Verificación y validación ↔ OE5, §2.1.6 y títulos del Cap. 3
- Tipo: coherencia
- Severidad: baja
- Evidencia: `02_marco_teorico.tex:400`: «en su acepción estricta la validación exige el contraste con mediciones experimentales, y este trabajo no realiza campaña experimental propia. … el contraste corresponde a verificación de solución y a comparación código a código». Pese a ello: OE5 (`01_introduccion.tex:38`) «Verificar y validar el software»; `02b_diseno_metodologico.tex:88` «la validación exige que los desplazamientos y las tensiones concuerden»; `04_resultados.tex:97` «\section{Validación con la viga de Timoshenko}», `:148` «\section{Validación con la membrana de Cook…}»; `06_anexos.tex:655` «\chapter{Modelo de validación en SAP2000…}».
- Problema: el documento adopta la definición de Oberkampf, reconoce que según ella no valida, y sigue titulando «validación» al contraste en el objetivo, la metodología y los resultados. Mismo concepto, dos términos, con la definición estricta en contra.
- Sugerencia: «contraste con referencias» o «verificación de solución» en OE5, §2.1.6 y títulos, dejando «validación» solo con la salvedad enunciada una vez.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): «validación» se define una sola vez en la sección de V&V del Cap. 1 (contraste con referencias externas de exactitud conocida, distinto de la validación experimental) y se usa con ese sentido en OE5, §2.1.6 y los títulos; renombrar los títulos sigue siendo alternativa abierta del autor (decisión pendiente desde la auditoría del 09-11).
- Sesión: 2

**H-21**
- Bloque y sección: B2 · §2.1.1 Tipo de investigación y modelo de simulación numérica
- Tipo: coherencia
- Severidad: baja
- Evidencia: título de `02b_diseno_metodologico.tex:11`: «\subsection{Tipo de investigación y modelo de simulación numérica}». El cuerpo (`:14-16`) trata solo el modelo; el tipo de investigación está fuera de §2.1, en la apertura del capítulo (`:4`: «Por su finalidad, el trabajo es de carácter \emph{propositivo} … \emph{investigación aplicada} de tipo \emph{tecnológico} … con enfoque \emph{cuantitativo}»). Taller 4, p. 4, nombra los tipos de modelo: «Desarrollo teórico · Modelación teórica · Modelación experimental · Modelación de simulación teórica»; la tesis lo llama «modelo de simulación numérica» (`:14`) sin mapearlo a esa lista.
- Problema: la subsección que promete el tipo de investigación no lo contiene (se lee antes, en la introducción del capítulo), y el modelo se nombra con un término que el material del tribunal no usa. Se suma a H-10 (nivel descriptivo/comparativo ausente).
- Sugerencia: mover el párrafo de `:4` a §2.1.1 y decir «modelación de simulación teórica —aquí, numérica— en la clasificación del Taller 4».
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): el párrafo del tipo de investigación se movió de la apertura del capítulo a §2.1.1; el modelo se describe como modelación teórica ejercitada por simulación numérica, no experimental.
- Sesión: 2

**H-22**
- Bloque y sección: B2 · §2.1.4 Casos de estudio y criterio de selección ↔ Taller 4 (población y muestra)
- Tipo: coherencia
- Severidad: baja
- Evidencia: Taller 4, p. 5: «Muestra: Es una parte representativa que contienen todas las características de la Población. Seleccionada por procedimientos aleatorios/probabilísticos»; p. 6: «Adecuada: Cuantitativamente, debe ser suficientemente grande»; p. 13: «Es importante establecer la población y la muestra, sobre la cual se aplicará el modelo especificado». `02b_diseno_metodologico.tex:74`: «El conjunto de casos que sigue no es una muestra estadística de ese universo, sino una selección \emph{intencional} por valor probatorio —una muestra dirigida, no probabilística». `04_resultados.tex:251`: «una batería más amplia de casos de referencia reforzaría la confianza en el comportamiento del software ante geometrías y condiciones de carga más diversas».
- Problema: el apartamiento del muestreo probabilístico está justificado (Sampieri, Oberkampf), pero la «adecuación» (tamaño) no se argumenta en §2.1.4: tres casos, uno de ellos con una sola malla (H-15), y el propio Cap. 3 admite que son pocos. Lo que debía sostenerse en la metodología queda como limitación en los resultados.
- Sugerencia: decir en §2.1.4 qué término del modelo ejercita cada caso (fuente volumétrica + Dirichlet no homogéneo; carga superficial + apoyos; distorsión + cortante) y por qué con eso la cobertura es suficiente.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): §2.1.4 dice qué términos del modelo ejercita cada caso, qué cubre el conjunto y la excepción declarada (carga superficial linealmente variable, sin caso de referencia), enlazada con la recomendación.
- Sesión: 2

**H-23**
- Bloque y sección: B2 · Tabla 2.1 (indicadores) ↔ §2.1.5 instrumentos y §2.1.6 criterios
- Tipo: coherencia
- Severidad: baja
- Evidencia: Tabla 2.1 (`02b_diseno_metodologico.tex:33-34`): indicadores «$\varepsilon_x,\varepsilon_y,\gamma_{xy}$; $u,v$ nodales; reacciones en los apoyos» y «error relativo (\%) en $\sigma_x$ y en deflexión frente al analítico y a SAP2000». §2.1.6 (`:88`) solo fija: tasas MMS, «flecha central de la viga de Timoshenko dentro del $3\,\%$ de la solución analítica» y los dos criterios de Cook. En el Cap. 3, «reacciones» aparece una sola vez (`04_resultados.tex:10`, como magnitud que «se registra») y las deformaciones ninguna; no hay criterio para $\sigma_x$ ni para la comparación con SAP2000.
- Problema: la operacionalización declara indicadores que ni los instrumentos miden ni los criterios juzgan ni el Cap. 3 reporta. En particular, la comparación con SAP2000 —parte literal de OE5— no tiene umbral de aceptación.
- Sugerencia: podar la Tabla 2.1 a lo que se mide, o añadir criterios para $\sigma_x$ (analítico y SAP2000) y reportar reacciones al menos en Timoshenko (equilibrio global, que es además pedagógico).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): Tabla 2.1 podada (sin deformaciones; reacciones como equilibrio global); §2.1.6 fija σx < 1 % frente al analítico y a SAP2000 y equilibrio con residuo < 1e-8; `tests/vv_timoshenko.py` los evalúa (corrido: 0,041 %, 0,207 %, residuo 1,7e-13) y escribe `timoshenko_equilibrio.csv`; §3.4 reporta el equilibrio.
- Sesión: 2

**H-24**
- Bloque y sección: B2 · §2.1.3 Matriz de consistencia, fila OE3
- Tipo: coherencia
- Severidad: baja
- Evidencia: `02b_diseno_metodologico.tex:58`: «Diseñar la interfaz pre/proceso/post & PI-2 & Organización de la interfaz; flujo de trabajo & Diseño centrado en un lienzo único compartido & \S\ref{sec:pre-proceso}». Existen `03_diseno_implementacion.tex:94` «\subsection{Pre-proceso interactivo}» y `:150` «\subsection{Post-proceso}»; la fila cita solo la primera.
- Problema: el objetivo abarca tres fases y la evidencia que la matriz le asigna cubre una. Un lector que siga la matriz no llega al post-proceso ni al lienzo compartido entre fases.
- Sugerencia: «\S\ref{sec:pre-proceso}–\S\ref{sec:post-proceso}».
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): fila OE3 de la matriz: «§2.2.6–§2.2.8; Tabla 3.6 (fases)» e indicador «fases que comparten el lienzo; sincronización lienzo–tabla».
- Sesión: 2

### B3 — Resultados

**H-25**
- Bloque y sección: B3 · §3.6 Cobertura del canal de cálculo ↔ OE4 ↔ §3.9 Validación de la hipótesis
- Tipo: coherencia
- Severidad: media
- Evidencia: OE4 (`01_introduccion.tex:37`): «Desarrollar módulos educativos que expongan, paso a paso y sobre el modelo real, cada etapa del canal de cálculo del MEF». `04_resultados.tex:209`: «La cobertura del canal de cálculo por los módulos es completa hasta el ensamblaje; la recuperación de tensiones, último eslabón del canal, no tiene un módulo propio y se expone en el post-proceso mediante la sonda puntual …, la vista tridimensional y la memoria de cálculo». `04_resultados.tex:258`: «queda confirmada al verificarse … : el motor recorre la cadena completa …, los módulos educativos la exponen paso a paso». `05_conclusiones.tex:17`: «cada etapa del canal de cálculo del MEF, del mapeo isoparamétrico al ensamblaje global».
- Problema: el resultado de OE4 es parcial (ni la resolución del sistema ni la recuperación de tensiones tienen módulo) y el Cap. 3 lo dice en §3.6, pero tres párrafos después la validación de la hipótesis lo da por completo y la conclusión reescribe «cada etapa» como «hasta el ensamblaje». El objetivo, el resultado y su lectura no dicen lo mismo. Taller 5, p. 21: «Mostrar si hay o no respuesta a los objetivos planteados».
- Sugerencia: o reformular OE4 («cada etapa hasta el ensamblaje; la recuperación de tensiones mediante el post-proceso y la memoria») o declarar en §3.9 y en Conclusiones el cumplimiento parcial.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): OE4 reformulado a lo construido (módulos hasta el ensamblaje; post-proceso y memoria completan solución y tensiones); §3.6, §3.9 y Conclusiones declaran la cobertura exacta (7/7 etapas con módulo, 9/9 en la memoria) y Limitaciones la recoge. El módulo de tensiones no se recomienda: ex-M7/ex-M8 se consolidaron en el Post por decisión de diseño (`no-reintroducir.md`).
- Sesión: 2

**H-26**
- Bloque y sección: B3 · §3.6 Resultados del software ↔ OE1, OE3 ↔ Estructura del documento
- Tipo: coherencia
- Severidad: media
- Evidencia: `01_introduccion.tex:69`: «El \autoref{cap:resultados} presenta y analiza los resultados: expone el producto final, mide los datos…». §3.6 (`04_resultados.tex:205-213`) no contiene figura, tabla ni medida: las cinco figuras del capítulo (`:66, 72, 81, 143, 180`) y sus siete tablas son de V&V; el texto de `:211-213` («Cada módulo que exhibe formulación matemática incorpora un conmutador Fórmula~$\leftrightarrow$~Valores…», «La fase de post-proceso ofrece…») repite lo descrito en §2.2. OE1 no tiene resultado en el Cap. 3 (la matriz, `02b:56`, remite al Cap. 1). Taller 5, p. 3: «Deben responder a los objetivos planteados … Se presentan en tablas, gráficas que sean fáciles de entender».
- Problema: dos objetivos (OE1, OE3) no tienen resultado en el capítulo de resultados, y el «producto final» que la Introducción anuncia para el Cap. 3 no se muestra allí (las capturas de la aplicación están en el Cap. 2 y en el Anexo B). §3.6 es prosa de diseño, no un resultado.
- Sugerencia: para OE3, una figura de la aplicación con las tres fases sobre el mismo lienzo y una tabla «fase → operaciones disponibles → módulo»; para OE1, aceptar que el Cap. 1 es su producto y decirlo en §3.9, o reformular OE1 como fundamentación que «se materializa» y no como objetivo con resultado.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): §3.6 incorpora la Tabla 3.6 `tab:fases` (fase → operaciones → etapas expuestas → instrumento) y la Figura 3.5 `fig:fases-lienzo` (las tres fases sobre el mismo lienzo y modelo; composición de capturas reales, generada por `tesis/figuras/generar_figuras.py`); §3.9 declara que OE1 no tiene resultado medido y por qué.
- Sesión: 2

**H-27**
- Bloque y sección: B3 · §3.8.1 Alcances y §3.9 ↔ Anexo D
- Tipo: coherencia
- Severidad: baja
- Evidencia: `04_resultados.tex:219`: «de hasta el $2{,}9\,\%$ en la tensión cortante … Frente a SAP2000 las diferencias son del $0{,}21\,\%$ en $\sigma_x$ y de hasta el $0{,}56\,\%$ en desplazamientos; en la componente cortante el modelo de cáscara queda más cerca de la solución analítica ($0{,}16\,\%$) que EduFEM»; `:260` repite «hasta el $0{,}56\,\%$ frente a SAP2000». Esas cifras no están en ninguna tabla del Cap. 3 (`tab:timoshenko-stress` solo $\sigma_x$; `tab:timoshenko-defl` solo analítico); provienen de `06_anexos.tex:580-595` (`tab:tim-componentes`) y de la tabla de desplazamientos del Anexo D. Taller 5, p. 4: «Se utilizan tablas y figuras para enriquecer los datos, no duplicarlos y con un texto que explique».
- Problema: la interpretación y la validación de la hipótesis se apoyan en datos que el capítulo no presenta; el lector del Cap. 3 no puede verificar el 2,9 % ni el 0,56 % sin ir al anexo, y el capítulo los interpreta antes de mostrarlos.
- Sugerencia: añadir a `tab:timoshenko-stress` las columnas de $\sigma_y$ y $\tau_{xy}$ (o una fila de máximos) y a `tab:timoshenko-defl` la columna SAP2000.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): `tab:timoshenko-stress` incorpora σy y τxy en el punto B con error analítico y frente a SAP2000 (4,56 % y 2,72 %, antes no reportados); `tab:timoshenko-defl` incorpora la columna SAP2000 en A, B y C (0,3912 / 0,5592 / 0,4744 %). El «0,56 %» ya está en el capítulo.
- Sesión: 2

**H-28**
- Bloque y sección: B3 · §3.2–§3.5 ↔ §3.8 Interpretación de los resultados
- Tipo: forma
- Severidad: baja
- Evidencia: Taller 5, p. 4: «Solo se debe describir y no interpretar o hacer comentarios de los resultados». El Cap. 3 tiene una sección propia de interpretación (§3.8) y, sin embargo, interpreta en cada sección de datos: `04_resultados.tex:120`: «no permite afirmar la superioridad de una herramienta sobre la otra»; `:137`: «Este detalle es pedagógicamente significativo … Este contraste ilustra, además, la importancia de seleccionar la referencia analítica adecuada»; `:174`: «La comparación a igualdad de grados de libertad es el argumento pedagógico central … Esta evidencia empírica permite al estudiante constatar de primera mano»; `:58`: relato del defecto de $\bm{E}_{\text{Q4}}$ «detectado y corregido durante el desarrollo».
- Problema: descripción e interpretación van mezcladas, y §3.8 queda como segunda interpretación (repite las cifras de §3.4–§3.5). El material docente pide separarlas.
- Sugerencia: dejar en §3.2–§3.6 tablas, figuras y descripción en pasado; concentrar juicios y lecciones pedagógicas en §3.8.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): §3.2–§3.5 quedan descriptivos; los juicios (superioridad de herramientas, significado pedagógico de la corrección de cortante, argumento a igualdad de GDL) y la lección de E_Q4 se concentran en §3.8.1.
- Sesión: 2

**H-29**
- Bloque y sección: B3 · §3.8.3 Limitaciones observadas (`tab:tiempos`) ↔ §2.1 metodología
- Tipo: coherencia
- Severidad: baja
- Evidencia: `04_resultados.tex:231-251`: tabla `tab:tiempos` con «$t_{\text{ensamblaje}}$ (s) & $t_{\text{solución}}$ (s) & $\bm{K}$ densa (MB) & $\bm{K}$ dispersa (MB)» medidos con `tests/bench_timing.py` y comparación de ordenamientos («se reduce 1,7 veces con 2178 GDL, 2,0 veces con 8450 GDL y 2,9 veces con 33\,282 GDL»). En `02b_diseno_metodologico.tex` no aparecen «tiempo», «memoria (MB)» ni `bench_timing` como variable, indicador o instrumento (0 ocurrencias); la Tabla 2.1 no tiene fila de desempeño.
- Problema: el Cap. 3 reporta una medición (rendimiento del solucionador) que la metodología no planificó: sin variable, sin instrumento declarado, sin criterio. Resultado que no responde a ningún objetivo ni pregunta (el criterio de B3 lo señala expresamente).
- Sugerencia: o añadir «desempeño» como variable controlada/observada en la Tabla 2.1 con su instrumento, o mover `tab:tiempos` al Anexo D como dato complementario.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): «desempeño» figura como variable observada en la Tabla 2.1 con su instrumento (`bench_timing.py`) y §2.1.6 declara que no tiene criterio de aceptación.
- Sesión: 2

**H-30**
- Bloque y sección: B3 · §3.8.2 Comparación cualitativa con herramientas existentes ↔ §1.1 Antecedentes
- Tipo: coherencia
- Severidad: baja
- Evidencia: `04_resultados.tex:223`: «En relación con las herramientas educativas reportadas en la literatura ---simuladores de armaduras, visualizadores de los modos propios de la matriz de rigidez o entornos de procesamiento interactivo de ecuaciones del MEF \autocite{bishay2020teaching,lee2015interactive,lee2015eigenmodes}---, la contribución distintiva de EduFEM es la cobertura integral del canal de cálculo …». Es el contenido de `02_marco_teorico.tex:11-43` y de `tab:comparativa`, sin dato nuevo del Cap. 3 y sin referencia a esa tabla.
- Problema: una subsección de «resultados» que no presenta resultado alguno: repite la comparación cualitativa del marco teórico. Si la intención es contrastar los resultados con los antecedentes (Taller 5, p. 3: «Cada dimensión o indicador debe tener el contraste de la teoría y los antecedentes»), debería confrontar cifras (p. ej. los errores de Cook con los publicados por Cook/Hughes) y no repetir la tabla de atributos.
- Sugerencia: reducir §3.8.2 a un párrafo que remita a `tab:comparativa` y añada lo que el Cap. 3 aporta a esa tabla (la fila «V\&V publicada»).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): §3.8.2 reducido a un párrafo que remite a la Tabla 1.1 y aporta lo que el Cap. 3 suma (la fila de V&V publicada).
- Sesión: 2

**H-31**
- Bloque y sección: B3 · §3.5 Membrana de Cook (nota al pie) ↔ §1.11
- Tipo: coherencia
- Severidad: baja
- Evidencia: `02_marco_teorico.tex:414`: «el desplazamiento del extremo converge al valor de referencia de uso convencional, $23{,}96$, … \autocites[p.~98]{cook2002concepts}[p.~221]{hughes2000fem}». `04_resultados.tex:150` (nota): «su valor de referencia es un límite de convergencia y no un dato exacto, por lo que conviene tratarlo como tal y no como una constante tomada de una fuente. En lugar de descansar en el valor convencional, este trabajo lo corrobora con evidencia propia».
- Problema: el marco teórico atribuye el 23,96 a dos fuentes con página; el Cap. 3 dice que no debe tratarse como constante tomada de una fuente. El lector no sabe si el valor está respaldado bibliográficamente o solo por la extrapolación de Richardson propia. B5 debe comprobar que Cook p. 98 y Hughes p. 221 efectivamente dan 23,96 (`tesis/respaldo_citas/verificado.json`).
- Comprobación (sesión 4): **ninguna de las dos páginas contiene el valor ni el caso**. El respaldo documental lo dice para Cook («La membrana de Cook no aparece en el índice de materias … ni en §8.10 “Tests of Element Quality” (pp. 293-295) … la co-cita de cook2002concepts … sólo puede sostener el mecanismo del bloqueo por cortante (pp. 98-99), no el caso de prueba ni su valor de referencia») y para Hughes («Ni el caso de la membrana de Cook ni ninguna de las cifras (23,96 / 22,08 / 7,9 %) aparecen en este libro: el indice alfabetico no tiene entrada ‘Cook’ ni ‘membrane’»). La contradicción entre §1.12 y §3.5 queda así resuelta a favor del Cap. 3: el 23,96 no tiene fuente en la bibliografía. El error de citación resultante se registra como H-40.
- Sugerencia: una sola procedencia: «valor convencional citado por Cook y Hughes y corroborado aquí por extrapolación de Richardson».
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): la sección de V&V del Cap. 1 dice que el 23,96 no procede de las obras citadas y remite a la extrapolación de Richardson de §3.5 (`sec:cook`).
- Sesión: 2

### B4 — Conclusiones y recomendaciones

**H-32**
- Bloque y sección: B4 · Conclusiones, veredicto global (`05_conclusiones.tex:23`) ↔ §3.6 ↔ OE1, OE3, OE4
- Tipo: coherencia
- Severidad: media
- Evidencia: `05_conclusiones.tex:23`: «En conjunto, los resultados confirman que EduFEM satisface los seis objetivos específicos y, con ello, el objetivo general. … hace observable y contrastable cada etapa del procedimiento, que es la respuesta al problema científico planteado». `04_resultados.tex:209`: «La cobertura del canal de cálculo por los módulos es completa hasta el ensamblaje; la recuperación de tensiones, último eslabón del canal, no tiene un módulo propio». OE1 y OE3 no tienen resultado en el Cap. 3 (H-26). Taller 5, p. 21: «Mostrar si hay o no respuesta a los objetivos planteados por el investigador · Señalar falencias o debilidades en la investigación».
- Problema: el único lugar donde la tesis emite un veredicto sobre los seis objetivos los da todos por satisfechos, sin matiz, cuando el propio Cap. 3 declara parcial la cobertura de OE4 y no aporta resultado para OE1 ni OE3. La sección «Limitaciones» (`05:35-37`) tampoco recoge esa parcialidad: habla de alcance físico, biblioteca de elementos, solucionador, bloqueo y validación pedagógica, no de las etapas del canal sin módulo. El material del tribunal pide decir «si hay o no respuesta»; el texto responde «sí» a todo. Amplía a `05:23` lo que H-25 registró para `05:17`.
- Sugerencia: «satisface los objetivos específicos, con el cuarto cumplido hasta el ensamblaje y la recuperación de tensiones cubierta por el post-proceso y la memoria», y anotar esa parcialidad en Limitaciones.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): veredicto global matizado («en los términos en que fueron enunciados: el primero como fundamento…, el cuarto con módulos hasta el ensamblaje…»); Limitaciones recogen la cobertura parcial por módulos y la batería reducida.
- Sesión: 3

**H-33**
- Bloque y sección: B4 · Conclusiones OE1 (`05:11`) y OE3 (`05:15`) ↔ Cap. 2 §2.2 ↔ Cap. 3
- Tipo: coherencia
- Severidad: media
- Evidencia: `05_conclusiones.tex:15`: «se logró una aplicación organizada en las tres fases canónicas … que comparten un único lienzo interactivo. … La interfaz soporta selección bidireccional entre las tablas de datos y el lienzo, deshacer y rehacer sobre el modelo completo, y validación automática de la salud del modelo previa a la resolución». Esas tres propiedades provienen de la descripción de diseño: `03_diseno_implementacion.tex:108` («La sincronización entre lienzo y tabla es bidireccional»), `:110` («Las acciones del usuario son reversibles mediante un mecanismo de deshacer y rehacer»), `02b_diseno_metodologico.tex:79` (validador de salud); ninguna aparece en `04_resultados.tex` (0 ocurrencias de «bidireccional», «deshacer», «salud del modelo»). `05:11`: «se sistematizó el MEF … anclado a la literatura clásica de la disciplina \autocite{zienkiewicz2013fem,bathe2014fem,hughes2000fem,cook2002concepts}», con remisión únicamente al Cap. 1. Taller 5, p. 21: «Vincular respecto a la metodología aplicada o al instrumento de medición»; «Se presenta de manera sintetizada lo planteado por el investigador respecto a los resultados, dejando claras las evidencias».
- Problema: dos de las seis conclusiones no cierran sobre un resultado: la de OE3 enumera funcionalidades tomadas del capítulo de diseño (lo que se construyó, no lo que se midió u observó) y la de OE1 resume el capítulo teórico. Ninguna de las dos pasa por instrumento, criterio ni dato del Cap. 3, así que el lector no puede distinguir «se diseñó» de «se comprobó». Es la contraparte en B4 de H-26 (sin resultado) y de H-17 (sin criterio).
- Sugerencia: para OE3, cerrar sobre lo que sí se observó (las tres fases operando sobre el mismo lienzo en los casos de V&V, o la figura/tabla que H-26 sugiere); para OE1, reformular como «se estableció la base teórica que el motor, los módulos y la memoria comparten» sin presentarla como resultado.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): conclusión OE1 reformulada como fundamento que el motor, los módulos y la memoria comparten; conclusión OE3 cierra sobre lo observado (los tres casos de V&V sobre el mismo lienzo, Tabla 3.6).
- Sesión: 3

**H-34**
- Bloque y sección: B4 · Recomendaciones, «Optimización del solucionador» (`05:43`) ↔ Cap. 2 y Cap. 3
- Tipo: coherencia
- Severidad: media
- Evidencia: `05_conclusiones.tex:43`: «Durante el desarrollo se evaluó además una reordenación de Cuthill-McKee inverso previa a la factorización y se descartó: solo compensó el costo de permutar en sistemas por encima de unos ocho mil grados de libertad, con ganancias del 7 al 19\,\%, un tamaño en el que el tiempo de resolución ya no es el factor limitante». Ídem: «la definición positiva vuelve innecesario el pivoteo, de modo que el trabajo aritmético se reduce aproximadamente a la mitad del de una factorización LU general». Búsqueda en `tesis/capitulos/*.tex`: «Cuthill» 0 ocurrencias fuera de `05:43`; «Cholesky» 0 ocurrencias fuera de `05:43`; «7 al 19» 0; «ocho mil» 0. El Cap. 3 (`04:251`) solo reporta el ordenamiento de mínimo grado frente a COLAMD (1,7–2,9 veces). Taller 5, p. 21: la conclusión «describe los resultados más relevantes, teniendo en cuenta la estructura del trabajo».
- Problema: la recomendación reporta una medición (ensayo de Cuthill-McKee inverso, umbral de ocho mil GDL, ganancia del 7-19 %) y un argumento teórico (coste de Cholesky) que no están en el marco teórico, en la metodología ni en los resultados. Es información nueva en el capítulo que debe derivar de lo anterior; además, la medición carece de instrumento y de tabla, a diferencia de `tab:tiempos`. Se suma a H-29 (desempeño medido sin planificar).
- Sugerencia: llevar el ensayo de Cuthill-McKee a §3.8.3 junto a `tab:tiempos` (con su guion) y el argumento de Cholesky a §1.9 o §2.2.4; dejar en la recomendación solo la línea de trabajo.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): la medición de Cuthill-McKee (7–19 %, ocho mil GDL) y el argumento aritmético de Cholesky salieron de las recomendaciones; Cholesky va como teoría en la sección de resolución del Cap. 1; §3.8.3 menciona el ensayo de Cuthill-McKee sin cifras, porque el instrumento ya no existe (`SOLVER_USE_RCM` eliminado el 2026-09-06).
- Sesión: 3

**H-35**
- Bloque y sección: B4 · Recomendaciones, «Ampliación de la batería de validación» (`05:49`) ↔ §3.2, §3.3, §3.4
- Tipo: coherencia
- Severidad: baja
- Evidencia: `05_conclusiones.tex:49`: «Se recomienda incorporar … un caso con carga superficial variable y peso propio, de modo que la validación externa cubra el estado plano que la práctica civil emplea con más frecuencia y las cargas que hoy solo se verifican por consistencia interna». §3.3 «Consistencia interna del modelo de datos» (`04:86-95`) verifica el ciclo Q4→Q9→Q4, los identificadores no contiguos y la interoperabilidad; no menciona cargas. El peso propio (fuerza de volumen) se verifica por MMS en §3.2 (`04:25`: «cuyo término fuente … se inyecta como fuerza de volumen»), y la carga superficial uniforme se valida externamente en Timoshenko (`04:99`: «sometida a una carga uniforme»; `tests/vv_timoshenko.py:167-170`: `add_surface_load(… q_start=Q_NM, q_end=Q_NM`). La carga superficial variable no se verifica en ningún lugar del Cap. 3.
- Problema: la recomendación atribuye a «consistencia interna» una verificación de cargas que esa sección no contiene, y describe como pendiente de validación externa una carga (uniforme) que Timoshenko ya valida y otra (peso propio) que el MMS verifica. La carencia real —carga superficial variable sin verificación reportada— queda sin nombrar. La recomendación no deriva con exactitud del resultado que invoca.
- Sugerencia: «un caso con carga superficial linealmente variable, que el Cap. 3 no verifica, y un caso civil en deformación plana con peso propio».
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): recomendación reescrita: carga superficial linealmente variable (sin caso de referencia) y caso civil en deformación plana con peso propio; ya no atribuye a «consistencia interna» una verificación de cargas.
- Sesión: 3

**H-36**
- Bloque y sección: B4 · Recomendaciones (`05:41-51`) ↔ Limitaciones (`05:35-37`) ↔ tríada capítulo–conclusión–recomendación
- Tipo: coherencia
- Severidad: baja
- Evidencia: `05_conclusiones.tex:41`: «cada una anclada en el capítulo del que deriva: la ampliación de la formulación (tratamiento del bloqueo, más tipos de elemento) en el \autoref{cap:marco_teorico}; la del software (solucionador, extensión a tres dimensiones) en el \autoref{cap:diseno}; y la de la evidencia (más casos de referencia y validación pedagógica) en el \autoref{cap:resultados}». `05:47`: una sola recomendación «Más tipos de elemento y extensión a tres dimensiones» junta el ítem asignado al Cap. 1 con el asignado al Cap. 2. `05:49` (batería de validación) deriva de `04:251` («una batería más amplia de casos de referencia reforzaría la confianza»), pero la sección Limitaciones de las Conclusiones (`05:35-37`) no enuncia el número de casos como limitación. Material docente («Cómo se construye el objetivo general», p. 15): «LA TRIADA: CAPITULO 1 → CONCLUSIÓN 1 → RECOMENDACIÓN 1 · CAPITULO 2 → … · CAPITULO 3 → …». `01_introduccion.tex:70`: «con la conclusión y la recomendación que corresponden a cada capítulo».
- Problema: el texto promete un anclaje por capítulo (y la Introducción, una conclusión y una recomendación por capítulo) que la estructura no cumple: hay seis conclusiones (por objetivo), cinco recomendaciones (por tema) y una de ellas cruza dos capítulos según el propio reparto de `05:41`. Una recomendación deriva de una limitación que las Conclusiones no declaran.
- Sugerencia: reagrupar las recomendaciones en tres (una por capítulo, con sub-ítems) o quitar de `05:41` y de `01:70` la promesa de correspondencia por capítulo; añadir a Limitaciones la frase de `04:251`.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): recomendaciones reagrupadas en tres subsecciones, una por capítulo (formulación; software; evidencia), con sus ítems; Introducción y Conclusiones ya no prometen «una conclusión y una recomendación por capítulo»; Limitaciones incluyen la batería reducida.
- Sesión: 3

**H-37**
- Bloque y sección: B4 · Conclusiones, conclusión general (`05:7`) ↔ Planteamiento del problema
- Tipo: coherencia
- Severidad: baja
- Evidencia: `05_conclusiones.tex:7`: «El trabajo regresa así a la contradicción que lo originó: la doble brecha entre la abstracción de los textos clásicos del MEF y la opacidad del software profesional como caja negra». `01_introduccion.tex:11`: «La brecha, en consecuencia, es doble: existe una dificultad de aprendizaje genuina vinculada a la naturaleza abstracta del método, y una insuficiencia de herramientas que la atiendan». `01_introduccion.tex:15`: «La insuficiencia de una herramienta con esos atributos es la contradicción que origina el trabajo».
- Problema: la conclusión cierra sobre el problema, como pide el Taller 5 («Vincular la respuesta a la pregunta problema»), pero redefine sus dos términos: en la Introducción la «doble brecha» es (dificultad de aprendizaje) + (insuficiencia de herramientas) y la «contradicción» es solo el segundo término; en las Conclusiones la «doble brecha» es (abstracción de textos) + (opacidad del software) y se identifica con la «contradicción». El lector que compare ambos pasajes no encuentra el mismo problema.
- Sugerencia: repetir en `05:7` la formulación de `01:11` y `01:15` con los mismos dos términos.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): la conclusión general repite los dos términos de la brecha de la Introducción (dificultad de aprendizaje + insuficiencia de herramientas) y la contradicción.
- Sesión: 3

**H-38**
- Bloque y sección: B4 · Limitaciones (`05:35-37`) ↔ «Alcance y limitaciones» (`01:66`) ↔ §3.8.3 (`04:227-229`)
- Tipo: coherencia
- Severidad: baja
- Evidencia: las limitaciones se enuncian en tres lugares con tres conjuntos distintos. `05:35`: «sin mallado automático: el estudiante construye la malla manualmente, mediante importación DXF o por generación estructurada en los casos de validación» («mallado automático»: 0 ocurrencias en `01_introduccion.tex` y `04_resultados.tex`). `01:66`: «El catálogo de materiales se restringe a comportamiento elástico, isótropo y lineal» («isótrop»: 0 ocurrencias en `05_conclusiones.tex`). `05:37` y `04:231-251`: limitación de escalabilidad del solucionador, ausente en `01:66`. `05:37`: «no se realizó una validación empírica del impacto educativo», presente en `01:66` y `04:264`.
- Problema: cada sección agrega o quita limitaciones sin que ninguna sea la lista completa. La de las Conclusiones, que debería recoger las «falencias o debilidades» (Taller 5, p. 21), omite el material isótropo y, como señala H-32, la cobertura parcial del canal, mientras estrena una (mallado) que el alcance de la Introducción no había delimitado.
- Sugerencia: una sola lista en «Alcance y limitaciones»; en Conclusiones, remitir a ella y agregar solo lo que se descubrió al hacer el trabajo (escalabilidad, cobertura parcial, pocos casos).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): lista única en «Alcance y limitaciones» (ahora incluye el mallado manual); las Limitaciones de las Conclusiones remiten a ella y agregan solo lo descubierto (cobertura por módulos, bloqueo, escalabilidad, pocos casos, sin validación empírica).
- Sesión: 3

**H-39**
- Bloque y sección: B4 · Conclusiones (`05:15, 17, 23`) ↔ resultados propios
- Tipo: coherencia
- Severidad: baja
- Evidencia: `05_conclusiones.tex:15`: «en línea con la evidencia sobre el valor de la interactividad en la enseñanza del método \autocite{lee2015interactive,bishay2020teaching}». `05:17`: «Este enfoque materializa el aporte pedagógico central del trabajo: hacer visible y manipulable lo que en la enseñanza tradicional permanece como una caja negra … \autocite{lee2015eigenmodes,perezsantiago2023fem}». `05:23`: «su valor como apoyo a la enseñanza y el aprendizaje del MEF se sostiene por diseño y en la literatura». El capítulo contiene 9 comandos de cita (8 `\autocite`, 16 claves); 5 de ellas sostienen afirmaciones pedagógicas. Taller 5, p. 21: la conclusión presenta «lo planteado por el investigador respecto a los resultados, dejando claras las evidencias».
- Problema: donde el trabajo no tiene resultado propio (la dimensión pedagógica: H-5, H-19), la conclusión sustituye la evidencia por citas de terceros y lo dice expresamente («se sostiene … en la literatura»). Una conclusión que descansa en la bibliografía no concluye nada del trabajo; y la literatura citada tampoco fue presentada en el marco teórico como fundamento pedagógico (H-19), solo como antecedentes de software.
- Sugerencia: reservar las citas para el marco teórico y formular las conclusiones pedagógicas como lo que son: decisiones de diseño fundamentadas en el Cap. 1, con su contraste empírico pendiente (`05:51`).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): las conclusiones ya no citan bibliografía (las citas quedan en las recomendaciones, como encuadre de líneas futuras); las afirmaciones pedagógicas se presentan como decisiones de diseño fundamentadas en §1.2.
- Sesión: 3

### B5 — Citación y referencias (H-2, H-12 a H-14 registrados en sesión 1 desde B0; bloque cerrado en la sesión 4)

Comprobación mecánica de la sesión 3 (sin hallazgo): las 22 entradas de
`tesis/bibliografia/referencias.bib` se citan al menos una vez y las 22 claves citadas en
`tesis/capitulos/*.tex` existen en el `.bib`; no hay `\nocite`. Total: 100 comandos de cita
(`02_marco_teorico` 47, `01_introduccion` 18, `04_resultados` 15, `05_conclusiones` 9,
`02b_diseno_metodologico` 8, `03_diseno_implementacion` 3; 0 en anexos, resumen y
nomenclatura). La correspondencia cita↔referencia se cumple en ambos sentidos.

Comprobaciones de la sesión 4 (sin hallazgo, salvo lo que se registra abajo):

- **Fuente de la lista impresa**: `tesis/main.pdf` (151 páginas, fecha interna
  2026-09-11 13:51, un minuto anterior al commit `bdbf18d`), pp. 79-81. Es el PDF del texto
  auditado, no una versión vieja.
- **Orden de numeración**: las 22 referencias salen en el orden de su primera mención en el
  texto (`[1]` Zienkiewicz y `[2]` Cook en `01_introduccion.tex:5` … `[22]` Sampieri en
  `02b_diseno_metodologico.tex:4`), incluidas las cinco citas que viven en cabeceras de la
  Tabla 1.1 (`02_marco_teorico.tex:26`), como exige el Taller 2 (p. 18: «en el texto, en las
  tablas y en las leyendas de las figuras»).
- **Citas de cita**: ninguna. Búsqueda de «citado en», «citado por», «apud» y «cit.» en
  `tesis/capitulos/*.tex`: 0 resultados (Taller 2, p. 18: «no se deben hacer citas de cita»).
- **Autocitas**: ninguna. El repositorio propio va en tres notas al pie
  (`01_introduccion.tex:23`, `06_anexos.tex:10, 335`) y no entra en la numeración, forma que la
  guía propia admite (`guia_vancouver.tex:426-428`).
- **Identidad de los ejemplares**: las 22 entradas del `.bib` dan «COINCIDE» contra el
  ejemplar consultado en `verificado.json` (autores, título, edición, editorial, año).
- **Ya corregido por la auditoría del 2026-09-11 y verificado hoy en el texto**: la Tabla 1.1
  ya dice «Comercial» para los simuladores de VisualFEA y «No declarada (código MATLAB)» para
  Bishay; `02_marco_teorico.tex:11` distingue «modos propios de la matriz de rigidez … no
  modos de vibración»; la frase de las integrales de error (`:412`) ya no cita a Salari-Knupp;
  el ordenamiento de mínimo grado (`:302`) ya no se atribuye a SciPy; von Mises (`:304`) va a
  Cook p. 117 y no a Timoshenko; el umbral de Verdict (`:382`) ya dice 0,30 y declara el 0,50
  como endurecimiento de EduFEM; el minimalismo (`05_conclusiones.tex:15`) ya no se atribuye a
  la literatura. No se repiten como hallazgo.
- **Desvíos documentados no registrados**, por la decisión de B0 (§2.3): títulos de revista
  completos y «y» ante el último autor; y el formato que `numeric-comp` impone a artículos y
  pie de imprenta («En: … 31.5 (2023), págs. 1159-1173»; «Oxford: …, 2005» en vez de «; 2005»),
  que la guía propia (`guia_vancouver.tex:522-543, 571-579`) reconoce como limitación del
  estilo y `tesis/README.md` documenta. Se anota que el Taller 2 (p. 19) recomienda la
  abreviatura; la obligación de declararlo va en H-2.

**H-40**
- Bloque y sección: B5 · §1.12 Verificación y validación (`02_marco_teorico.tex:414`) ↔ §3.5
- Tipo: citación
- Severidad: **alta**
- Evidencia: `02_marco_teorico.tex:414`: «el desplazamiento del extremo converge al valor de referencia de uso convencional, $23{,}96$, pero el elemento Q4 lo subestima sensiblemente en las mallas gruesas por el bloqueo por cortante (\emph{shear-locking}) descrito en la \autoref{sec:locking}; el elemento Q9, de orden superior, lo evita y converge con rapidez \autocites[p.~98]{cook2002concepts}[p.~221]{hughes2000fem}». Respaldo documental (`tesis/respaldo_citas/verificado.json`, clave `cook2002concepts`, «sin_respaldo» 2): «el valor de referencia u_y^ref = 23,96 de la membrana de Cook … NO figura en esta obra. La membrana de Cook no aparece en el índice de materias … ni en §8.10 “Tests of Element Quality” (pp. 293-295), ni en los problemas del capítulo 6». Ídem, clave `hughes2000fem`, respaldo de esta misma frase: «pagina_impresa: 243 (nota al pie 10) … respalda: PARCIAL … Ni el caso de la membrana de Cook ni ninguna de las cifras (23,96 / 22,08 / 7,9 %) aparecen en este libro». La p. 221 de Hughes es, según el mismo respaldo, la Tabla 4.4.1 («U2 2 x 2 uniform integration (= exact in present case)»), que sostiene la frase sobre la cuadratura $2\times2$/$3\times3$ de `02_marco_teorico.tex:248`, no esta. La nota de `docs/notas/2026-09-08_bibliografia-tesis.md:467` lo había advertido: «Cook 2002 NO contiene la membrana de Cook (verificado página por página sobre el escaneo). Sirve para el fenómeno, no para la atribución». El artículo original (`cook1974membrane`) se retiró del `.bib` por no haberse consultado.
- Problema: la oración que fija el valor de referencia que gobierna toda la columna de error de `tab:cook` y el comportamiento comparado Q4/Q9 cierra con dos localizadores de página, y ninguno de los dos contiene el caso, el valor ni la afirmación sobre el Q9 (la que Hughes sí hace está en la p. 243, nota 10). Un miembro del tribunal que abra Cook en la p. 98 no encuentra la membrana. La auditoría del 2026-09-11 (ítem 4.1, «mayor») pidió dejar el valor «sin cita»; se reescribió la prosa pero la cita quedó en el mismo lugar, y el localizador de Hughes se tomó de otra afirmación.
- Sugerencia: mover «\autocite[pp.~98-99]{cook2002concepts}» a continuación de «bloqueo por cortante», poner «\autocite[p.~243]{hughes2000fem}» tras «lo evita y converge con rapidez», y dejar el 23,96 sin cita, remitiendo a la nota de `04_resultados.tex:150` (o citar Cook 1974 solo si se consigue y verifica).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): Cook pp. 98-99 acompaña al bloqueo por cortante, Hughes p. 243 al comportamiento del Q9, y el 23,96 va sin cita, declarado como valor de la comunidad corroborado por Richardson.
- Sesión: 4

**H-41**
- Bloque y sección: B5 · §1.10 Recuperación de tensiones (`02_marco_teorico.tex:321`) y §3.2 (`04_resultados.tex:58`)
- Tipo: citación
- Severidad: media
- Evidencia: `02_marco_teorico.tex:321`: «En el elemento Q4 los puntos de la regla $2\times2$ coinciden con los \emph{puntos de Barlow}, ubicaciones donde las tensiones convergen con un orden superior al del resto del elemento (superconvergencia) \autocite[p.~231]{cook2002concepts}». `04_resultados.tex:58`: «Que el Q4 supere el orden $\mathcal{O}(h^{1})$ del gradiente crudo (seminorma $H^1$) refleja la superconvergencia del muestreo en los puntos de Barlow y del promediado nodal (\autoref{sec:resolucion-tensiones}) \autocite[p.~231]{cook2002concepts}». Respaldo documental (`verificado.json`, `cook2002concepts`): «El término “puntos de Barlow” NO aparece en esta obra: no figura en el índice de materias (p. 711 …)»; «en p. 230 Cook escribe “stresses at ξ = η = 0 in the Q4 element, and at Gauss points of a four-point rule in the Q8 element, are ‘superconvergent’”, situando el punto superconvergente del Q4 en el centro y no en los cuatro puntos de la regla 2×2»; y sobre el promediado: «en p. 231 Cook advierte para su ejemplo: “It is also too large at these locations in adjacent elements on either side, so that nodal averaging at shared nodes is of no benefit to accuracy.” … el aporte del promediado nodal a la tasa observada de O(h^1,54) no lo está en esta fuente». Cook atribuye la ganancia de orden a la recuperación por parches (p. 325, §9.9), no al promediado nodal simple que usa EduFEM.
- Problema: la única fuente que queda tras retirar a Zienkiewicz (auditoría del 2026-09-11, ítem 4.3) se cita con página para (a) un término que no contiene, (b) una localización del punto superconvergente que su p. 230 sitúa en otro lugar, y (c) en `04:58`, un efecto del promediado nodal que la misma p. 231 niega expresamente. La explicación del orden $\mathcal{O}(h^{1{,}54})$ —resultado propio y correcto en sus cifras— queda apoyada en una cita que dice lo contrario.
- Sugerencia: presentar la localización $2\times2$ y el efecto del promediado como observación propia verificada por el MMS («en este trabajo se observa que…»), citar a Cook pp. 230-231 solo para el concepto de superconvergencia en puntos de Gauss, y buscar Barlow (1976, *Int J Numer Methods Eng* 10:243-251) si se quiere el término con fuente.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): «puntos de Barlow» retirado (sin fuente en la bibliografía); Cook pp. 230-231 se cita por lo que dice (superconvergencia en puntos de Gauss; 2×2 óptimos en el Q9; centro en el Q4); el muestreo 2×2 del Q4 se declara decisión de implementación; el O(h^1,54) se presenta como observación propia y §3.2 cita Cook p. 231 por su advertencia sobre el promediado.
- Sesión: 4

**H-42**
- Bloque y sección: B5 · entrada `alvarez_metodologia` ↔ Introducción (`01_introduccion.tex:15, 17`) y §2.1.1 (`02b_diseno_metodologico.tex:14`)
- Tipo: citación
- Severidad: media
- Evidencia: `referencias.bib:200-204`: «@unpublished{alvarez_metodologia, author = {{\'A}lvarez de Zayas, Carlos}, title = {Metodolog{\'i}a de la investigaci{\'o}n cient{\'i}fica}, note = {Monograf{\'i}a in{\'e}dita de 80 p{\'a}ginas, de circulaci{\'o}n acad{\'e}mica en formato electr{\'o}nico; sin lugar, editorial ni fecha declarados. [lugar desconocido]: [editorial desconocida]; [fecha desconocida]}}». Impresa (`main.pdf` p. 79, [7]): «Álvarez de Zayas C. «Metodología de la investigación científica». Monografía inédita de 80 páginas, de circulación académica en formato electrónico; sin lugar, editorial ni fecha declarados. [lugar desconocido]: [editorial desconocida]; [fecha desconocida].» Es la única fuente de las cuatro categorías que estructuran el problema y el modelo: «La insuficiencia de una herramienta con esos atributos es la contradicción que origina el trabajo \autocite{alvarez_metodologia}» (`01:15`), «El \textbf{objeto de estudio} \autocite{alvarez_metodologia}» y «El \textbf{campo de acción} … \autocite{alvarez_metodologia}» (`01:17`), «una representación ideal del objeto … \autocite[p.~21]{alvarez_metodologia}» (`02b:14`). Guía propia, `guia_vancouver.tex:228-233`: la plantilla prevista es la de libro («Álvarez de Zayas C. Metodología de la investigación científica. [lugar desconocido]: [editorial desconocida]; [fecha desconocida].») y su inventario (`:238`, `:458-462`) la cuenta entre «12 libros», cuando el `.bib` tiene 11 `@book` y este `@unpublished`. Taller 1, p. 24, jerarquía de fuentes: «Nivel 1: … Artículos en revistas reconocidas (paper) · Nivel 2: Tesis publicadas · Nivel 3: Libros publicados con data no mayor a 10 años · Nivel 4: Publicaciones en revistas o documentos técnicos». La auditoría del 2026-09-11 (ítem 4.4, «mayor») pidió «Si circuló en la carrera, @unpublished con “Apuntes de la Carrera de Ingeniería Civil, UATF”».
- Problema: el marco metodológico completo (contradicción, objeto, campo, modelo) descansa en una sola fuente que no encaja en ningún nivel de la jerarquía del tribunal, no tiene fecha ni dato alguno de recuperación (institución, curso, URL), se imprime con un título entre comillas y una nota editorial de tres líneas que ninguna plantilla de la guía propia contempla, y la guía la describe como libro. El cambio de tipo aplicado tras la auditoría anterior resolvió la honestidad del pie de imprenta pero no la localizabilidad: un lector sigue sin poder obtener el documento. Las mismas categorías están en el material docente que sí está en el repositorio («Situación problemática, objeto de estudio y campo de acción», Ing. J. S. Miranda), que no se cita.
- Sugerencia: completar la nota con el dato de procedencia («Apuntes de la asignatura CIV 400, Carrera de Ingeniería Civil, UATF; documento electrónico, 2007 según metadatos») o sustituir/acompañar la cita con Hernández-Sampieri (ya en el `.bib`) para objeto y problema; actualizar el inventario de la guía.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): nota de procedencia en el `.bib` (monografía inédita, PDF fechado en 2007 según metadatos, empleada en la Carrera de Ingeniería Civil de la UATF como referencia del marco metodológico); localizadores en las cuatro citas (pp. 7, 8, 13, 21); guía con ficha E `@unpublished` y conteo 11 libros + 1 inédita. **Verificar por el autor**: la frase de procedencia se redactó a partir del uso que la carrera hace de la fuente, no de un dato impreso.
- Sesión: 4

**H-43**
- Bloque y sección: B5 · §2.2.1 Requisitos (`03_diseno_implementacion.tex:9`), Justificación (`01_introduccion.tex:21`), §3.6 (`04_resultados.tex:207`)
- Tipo: citación
- Severidad: media
- Evidencia: `03_diseno_implementacion.tex:9`: «El software educativo interactivo demuestra eficacia para consolidar conceptos abstractos del análisis estructural \autocite{lee2015interactive,bishay2020teaching,perezsantiago2023fem}». Respaldo documental (`verificado.json`): Lee 2015a, p. 168: «Lee dice expresamente que NO hay datos cuantitativos de eficacia y que su evaluación fue cualitativa y observacional, sobre sus propios cursos, sin grupo de control»; Bishay 2020, pp. 13 y 17: «Bishay si mide eficacia (mejora estadisticamente significativa, p = .048 …), pero en la p. 17 atribuye explicitamente esa mejora ‘principalmente’ a la actividad de generacion de tareas entre pares, no a las herramientas computacionales, que solo la ‘facilitaron’»; Pérez-Santiago 2023 es una encuesta a expertos (`02_marco_teorico.tex:9`: «Un estudio que recoge la opinión de expertos»), no un estudio de eficacia. `01_introduccion.tex:21`: «La literatura sobre enseñanza del método coincide en que la simulación interactiva … \autocite{lee2015interactive,lee2015eigenmodes,bishay2020teaching}» — Bishay: «la palabra ‘interactive’ no aparece en el articulo y las herramientas son scripts de MATLAB sin interfaz interactiva». `04_resultados.tex:207`: «Cada módulo es una \emph{capa superpuesta} interactiva que ilumina sobre la malla real el punto donde ocurre el cálculo, evitando la abstracción de una ventana desconectada del modelo \autocite{lee2015interactive,bishay2020teaching}» — Bishay: «no dice nada sobre superposicion de capas, resaltado sobre el modelo ni ventanas desconectadas; sus herramientas … producen graficos estaticos». La propia tesis fija el registro correcto en `01_introduccion.tex:56`: «los criterios de diseño pedagógico se fundamentan cualitativamente en la literatura».
- Problema: el verbo «demuestra eficacia» atribuye a tres fuentes una evidencia que la primera niega tener, la segunda asigna a otra causa y la tercera no mide; y dos citas de encuadre cargan a Bishay con atributos (interactividad, capas superpuestas) que su herramienta no tiene. Como la dimensión pedagógica no tiene resultado propio (H-5, H-19, H-39), estas citas son el único sustento de la finalidad del objetivo general, y están sobredimensionadas. Taller 1, p. 24: «Referenciar todo lo que se tome del material bibliográfico» supone tomar lo que la fuente dice.
- Sugerencia: «El software educativo interactivo se reporta como conducente a una mejor comprensión … \autocite[p.~168]{lee2015interactive}, y la construcción paso a paso de herramientas de cálculo con el alumno resulta eficaz \autocite[p.~17]{bishay2020teaching}»; en `01:21` y `04:207` dejar solo `lee2015interactive` (y `lee2015eigenmodes` donde corresponda).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): §2.2.1 reescrito con lo que cada fuente sostiene (Lee p. 168, cualitativo; Bishay p. 17, con la atribución a la autoría del alumno); Introducción, §3.6 y §2.2.7 citan a Lee (y Lee-Ryu) solamente; la hipótesis cita Lee p. 157 y Pérez-Santiago p. 1168.
- Sesión: 4

**H-44**
- Bloque y sección: B5 · formato de la cita en el texto (localizadores), todo el documento
- Tipo: citación
- Severidad: baja
- Evidencia: de los 100 comandos de cita, 28 llevan localizador y 72 no; la distribución no sigue el tipo de afirmación. Con localizador: `02b_diseno_metodologico.tex:4` «\autocite[pp.~90-92]{garciacordoba2005tecnologica}», `02_marco_teorico.tex:276` «\autocite[p.~265]{virtanen2020scipy}». Sin localizador, afirmaciones igual de concretas: `01_introduccion.tex:64` «la matriz constitutiva crece a $6\times6$, la de deformación-desplazamiento a $6\times24$ … y la rigidez elemental a $24\times24$ \autocite{cook2002concepts}» (el respaldo da p. 218: «La cita no lleva localizador; convendría añadir \autocite[p.~218]»), `04_resultados.tex:172` «\autocite{cook2002concepts,bathe2014fem}» para el bloqueo del Q4, las cuatro citas de `alvarez_metodologia` en la Introducción (`verificado.json`: «NINGUNA DE LAS CUATRO CITAS LLEVA LOCALIZADOR … Para las categorias del marco metodologico … el tribunal UATF suele exigir pagina»). El documento de respaldo declara lo contrario de lo que el texto hace: `tesis/respaldo_citas/respaldo_citas.tex:21`: «Las citas del cuerpo de la tesis siguen el estilo Vancouver puro, sin localizador de página; el localizador vive aquí». Formas no uniformes del localizador: «\autocites[pp.~21 y 26]{salari2000mms}» (`02:402`), «\autocite[art.~21, pp.~39-43]{timoshenko1970elasticity}» (`02:414`) frente a «\autocite[art.~21]{timoshenko1970elasticity}» (`04:137`). Guía propia, `guia_vancouver.tex:135`: la adaptación «no es un error, siempre que se aplique de forma uniforme».
- Problema: Vancouver admite el localizador en la cita, pero exige un criterio uniforme; hoy el lector no puede inferir por qué unas citas de valores o prescripciones lo llevan y otras no, y el documento anexo que debería explicar la convención afirma que no hay localizadores. La auditoría del 2026-09-11 (ítem 4.13) pidió agregarlos «al menos donde se cita una ecuación, un valor o una prescripción»; se aplicó en parte.
- Sugerencia: fijar la regla («localizador en toda cita de valor numérico, ecuación, umbral o definición; ninguno en citas de encuadre»), aplicarla a las 72 restantes o retirarla de las 28, corregir la frase de `respaldo_citas.tex:21` y unificar «pp.~21, 26».
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): regla única declarada en la Introducción y aplicada a las 100 citas (localizador en toda cita de ecuación, valor, umbral, definición o atribución concreta; ninguno en las de encuadre); «pp.~21, 26» y «art.~21, pp.~39-43» unificados; citas múltiples con página separadas por punto y coma (delimitador de `\parencites` redeclarado en el preámbulo; `utocite{k1,k2}` sigue con coma); la frase de `respaldo_citas.tex` corregida y el PDF regenerado; skill `tesis-bibliografia` actualizada.
- Sesión: 4

**H-45**
- Bloque y sección: B5 · lista final impresa (`main.pdf` pp. 79-81) ↔ `referencias.bib` ↔ `guia_vancouver.tex`
- Tipo: citación
- Severidad: baja
- Evidencia: cinco entradas se apartan de la plantilla de la guía propia o de lo que la guía dice haber corregido. (a) [17] impresa: «Computers & Structures, Inc. CSI Analysis Reference Manual for SAP2000, ETABS, SAFE and CSiBridge. Rev. 18. Computers & Structures, Inc. [Estados Unidos], 2017.» — la guía (`:516-519`) da por «Corregido» el pie «…: Computers \& Structures, Inc.; 2017» y su plantilla (`:354-355`) es «Lugar (Estado): Organización; año»; lo impreso invierte editorial y lugar y omite los dos puntos. (b) [5] impresa: «Reddy JN. An Introduction to the Finite Element Method. 3.a ed. International Edition. New York: McGraw-Hill, 2006.» — `referencias.bib:52` «note = {International Edition}», mientras el propio `.bib` (`:17-19`) borró la nota análoga de Bathe «porque Vancouver no contempla notas entre el titulo y el pie de imprenta». (c) [15] impresa: «Barcelona: CIMNE y Springer, 2009» — coedición con un solo lugar; NLM pide el primer editor o cada editor con su lugar. (d) [6] impresa: «México, D.F.: Limusa» frente al ejemplo de la guía (`:254-255`) «México (DF): Limusa». (e) [10] Bishay: «28.4 (2020), págs. 1007-1027» — `docs/notas/2026-09-09_diagnostico-bibliografia.md:110-114`: «El ejemplar es la versión *Early View* … paginada 1-21 y sin volumen ni fascículo impresos … `volume = {28}`, `number = {4}` y `pages = {1007--1027}` **no son verificables contra la copia que el autor tiene**»; el `.bib` no lo anota, a diferencia de `perezsantiago2023fem` (`:246-249`), y la guía (`:638-640`) manda: «¿Hay algún DOI, ISBN o número de página que no hayas leído del ejemplar? Si no lo confirmaste, el campo se borra». Además, la guía cuenta «12 libros» (`:238`) y el `.bib` tiene 11 (`alvarez_metodologia` es `@unpublished`).
- Problema: la guía es el instrumento con que el autor promete a la vez uniformidad y trazabilidad de cada dato; hoy describe un estado de la lista que el PDF no reproduce (manual, conteo) y tolera en una entrada lo que prohíbe en otra (nota de edición; campo no leído del ejemplar). Ninguno de los cinco puntos afecta la identificación de la fuente; afectan la coherencia entre norma declarada y norma aplicada.
- Sugerencia: para (a) usar `publisher` en vez de `organization` o un `\DeclareBibliographyDriver{manual}`; (b) quitar la nota o pasarla a `edition = {3, International}`; (c) «Barcelona: CIMNE; 2009» (con Springer en nota) ; (d) unificar; (e) anotar en el `.bib` la procedencia (Crossref) o comprobar en el fascículo, y corregir el conteo de la guía.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): (a) CSI con `publisher` (imprime «[Estados Unidos]: Computers & Structures, Inc., 2017»: biblatex 3.21 pone `organization` antes del pie de imprenta); (b) Reddy sin nota; (c) Oñate «Barcelona: CIMNE»; (d) García-Córdoba «México (DF)»; (e) Bishay con nota de procedencia (CrossRef, 2026-09-11); guía: conteo, ficha D con `publisher`, ficha E, corrección 4.
- Sesión: 4

### B6 — Forma: títulos, numeración, jerarquía, preliminares

Comprobado sin hallazgo (sesión 4): el orden de secciones de `tesis/main.tex:43-78` es el del
índice modelo del Taller 1 (p. 20): Resumen · Introducción · Capítulo 1 · Capítulo 2 · Capítulo 3
· Conclusiones y recomendaciones · Bibliografía · Anexos. La Introducción y las Conclusiones
van sin número (`\chapter*`), los tres capítulos con «Capítulo N» centrado (`preambulo.tex:233-235`)
y secciones `1.1`, `2.1.1`, los anexos como «Anexo A…G» (`main.tex:76`). Cap. 2 y Cap. 3 llevan
el nombre que el índice modelo prescribe («Diseño e implementación del modelo a desarrollar»,
«Presentación de resultados y análisis»). Entre el resumen y la introducción se intercalan
índice general, de figuras y de tablas, una nota de autoría de figuras y la nomenclatura, que
el índice modelo no lista pero tampoco excluye. La declaración de originalidad, la dedicatoria
y los agradecimientos existen (`00_preliminares.tex`) y están desactivados a propósito para el
borrador (`main.tex:40-41`); no es hallazgo, pero la versión final debe reactivarlos. El
modelo de investigación está en el Cap. 2 (§2.1), donde el Taller 4 lo ubica.

**H-46**
- Bloque y sección: B6 · título del Capítulo 1 y estructura interna del Capítulo 2
- Tipo: forma
- Severidad: baja
- Evidencia: Taller 1, p. 20, índice de una tesis: «Capítulo 1 MARCO TEÓRICO DE …… · Capítulo 2 DISEÑO E IMPLEMENTACION DEL MODELO A DESARROLLAR · Capítulo 3 PRESENTACION DE RESULTADOS Y ANÁLISIS DE LOS MISMO». `02_marco_teorico.tex:1`: «\chapter{Marco teórico}». Índice impreso (`main.pdf` p. iii): «1. Marco teórico». Capítulo 2: `02b_diseno_metodologico.tex:1` «\chapter{Diseño e implementación del modelo a desarrollar}», `:6` «\section{Diseño metodológico}» (seis subsecciones), `03_diseno_implementacion.tex:1` «\section{Diseño e implementación de EduFEM}» (nueve subsecciones); el capítulo tiene exactamente dos secciones.
- Problema: el índice modelo deja el Cap. 1 abierto a un complemento descriptivo («MARCO TEÓRICO DE ……») y fija los otros dos; la tesis completa los fijos al pie de la letra y deja el único que pedía completarse con la etiqueta genérica. En el Cap. 2, la sección 2.2 repite casi literalmente el título del capítulo («Diseño e implementación …») y la jerarquía queda desbalanceada: dos secciones que cargan quince subsecciones, con la matriz de consistencia, el software y la memoria de cálculo todos al mismo nivel `2.x.y`.
- Sugerencia: «Marco teórico del análisis por elementos finitos en elasticidad plana» (o el complemento que el tutor prefiera); en el Cap. 2, renombrar 2.2 («El software EduFEM») o ascender sus subsecciones principales (motor, pre-proceso, módulos, post-proceso, memoria) a secciones.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): Cap. 1 «Marco teórico del análisis por el Método de los Elementos Finitos en elasticidad plana»; §2.2 «El software EduFEM».
- Sesión: 4

**H-47**
- Bloque y sección: B6 · Anexo G (`07_anexo_memoria.tex:76-173`)
- Tipo: forma
- Severidad: baja
- Evidencia: `07_anexo_memoria.tex:74`: «\section{Procedimiento}»; `:76` «\subsection*{1. Matriz constitutiva}», `:88` «\subsection*{2. Rigidez del elemento}», `:124` «\subsection*{3. Ensamblaje}», `:141` «\subsection*{4. Restricciones y solución}», `:157` «\subsection*{5. Reacciones}», `:173` «\subsection*{6. Recuperación de tensiones}». En el resto de los anexos las subsecciones se numeran automáticamente («B.1.1 Definición de la geometría», `06_anexos.tex:71`) y en el cuerpo, `1.1`, `2.1.1`.
- Problema: dentro de un documento con numeración jerárquica automática (`G.2`), un tramo numera a mano «1.» a «6.» con subsecciones sin número, que además no aparecen en el índice; la jerarquía de encabezados deja de ser uniforme justo en el anexo que reproduce el documento generado por el software. La nota de presentación (`docs/notas/2026-09-10_apa-presentacion.md:25-28`) decidió conservar la numeración de títulos en todo el documento.
- Sugerencia: `\subsection{Matriz constitutiva}` … (numeradas como G.2.1–G.2.6) o, si se quiere imitar la memoria generada, envolver los seis pasos en una lista `enumerate` en vez de encabezados.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): Anexo G: los seis pasos son `\subsection` numeradas (G.2.1–G.2.6) y entran en el índice.
- Sesión: 4

**H-12**
- Bloque y sección: B5 · formato de la cita en el texto
- Tipo: citación
- Severidad: media
- Evidencia: Taller 2, p. 18: «Se recomienda que se utilicen números arábigos en superíndice y sin paréntesis». `tesis/preambulo.tex:267`: «style=numeric-comp,  % numerico con rangos comprimidos: [2-5]». Las 69 `\autocite` de los capítulos se imprimen entre corchetes: «[8, 10]», «[2]» (constatado en la auditoría del 2026-09-11, §2.6 y §4).
- Problema: el único documento del tribunal que habla del formato de la cita en texto recomienda superíndice sin paréntesis; la tesis usa corchetes. Vancouver admite ambas formas, así que no es error de norma, pero es un apartamiento de la recomendación explícita del material docente, no justificado en ningún lado.
- Sugerencia: `\usepackage[…,autocite=superscript]{biblatex}` (o dejar corchetes y justificarlo en la frase de H-2).
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): corchetes conservados y justificados en la frase de la norma (permiten el localizador junto al número); cambiar a superíndice con 28 localizadores produciría citas ilegibles.
- Sesión: 1

**H-13**
- Bloque y sección: B5 · lista final
- Tipo: citación
- Severidad: media
- Evidencia: Taller 1, p. 26: «El listado de bibliografía de referencia debe ser ordenado según su aparición en el documento, señalando nombre de autor, título de la publicación, Editorial, año y páginas de referencia. El listado de bibliografía utilizada en el documento de graduación, debe ser en orden alfabético, según: Nombre de autor o autores, título de la publicación, Editorial, país y año». `tesis/main.tex:72`: una sola lista, `\printbibliography[title={Bibliografía},heading=bibintoc]`, con `sorting=none`.
- Problema: el material docente distingue dos listados (referencias citadas, por orden de aparición; bibliografía consultada, alfabética). La tesis entrega uno solo, titulado «Bibliografía», ordenado por aparición, que en realidad es la lista de referencias. Falta decidir si el tribunal exige el segundo listado y, en cualquier caso, el título no corresponde al contenido.
- Evidencia adicional (sesión 4): el índice modelo del Taller 1 (p. 20) rotula esa sección simplemente «Bibliografía», así que el título de la tesis coincide con el índice esperado; lo que sigue sin resolverse es la distinción de la p. 26 entre las dos listas. El orden de la lista impresa (`main.pdf` del 2026-09-11, pp. 79-81) se verificó entrada por entrada contra la primera cita de cada clave en los `.tex`: las 22 están en orden de primera mención, como exige el Taller 2 (p. 18).
- Sugerencia: titular «Referencias» a la lista actual y, si el Reglamento (H-1) lo pide, añadir «Bibliografía» alfabética con las obras consultadas y no citadas (`\nocite`).
- Estado: **parcial** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): la lista pasó a titularse «Referencias bibliográficas» (`main.tex`), que es lo que contiene; la segunda lista alfabética de «bibliografía utilizada» queda sujeta a lo que diga el Reglamento (H-1).
- Sesión: 1

**H-14**
- Bloque y sección: B5 · jerarquía y antigüedad de fuentes
- Tipo: citación
- Severidad: baja
- Evidencia: Taller 1, p. 24: «Nivel 3: Libros publicados con data no mayor a 10 años»; Taller 2, p. 19: «Los documentos que se citen deben ser actuales, salvo por motivos históricos o si no encontrásemos referencias actualizadas». Campo `year` de `tesis/bibliografia/referencias.bib` anterior a 2016 en 15 de las 22 entradas: `zienkiewicz2013fem` (2005), `bathe2014fem` (1996), `cook2002concepts` (2002), `hughes2000fem` (1987), `reddy2006introduction` (2006), `onate2009structural` (2009), `timoshenko1970elasticity` (1951), `salari2000mms` (2000), `stimpson2007verdict` (2007), `suarez1998edelas2d` (1998), `lee2015interactive` y `lee2015eigenmodes` (2015), `garciacordoba2005tecnologica` (2005), `strang2008analysis` (1973), `oberkampf2010vv` (2010); `alvarez_metodologia` no tiene año.
- Problema: dos tercios de las fuentes superan los diez años que fija el material docente para libros; son los clásicos del MEF y la excepción «por motivos históricos» los ampara, pero la tesis no lo dice en ningún lugar. B5 debe comprobar si alguna tiene edición más reciente disponible (p. ej. Bathe 2014, Zienkiewicz 7.ª ed. 2013, que son justamente los años que sugieren las claves).
- Comprobación (sesión 4): existe edición más reciente para cinco de los libros y el propio repositorio lo documenta. `tesis/respaldo_citas/verificado.json` registra que el `.bib` declaraba, antes de la corrección del 2026-09-10, «edition = {2}, publisher = {K. J. Bathe}, location = {Watertown, MA}, year = {2014}» para Bathe, «edicion 7 (2013), ISBN 978-1-85617-633-0» para Zienkiewicz, «edition = {3}, year = {1970}» para Timoshenko-Goodier y «Dover Publications, Mineola, NY, 2000» para Hughes; la clave `strang2008analysis` apunta a la 2.ª ed. de 2008 (Wellesley-Cambridge) y de Reddy existe la 4.ª ed. (McGraw-Hill, 2019). Es decir: el autor consultó ediciones anteriores a las que él mismo conocía, corrigió el `.bib` al ejemplar en mano —lo correcto— y no dejó en el texto la justificación «por motivos históricos» que el Taller 2 (p. 19) exige para citar fuentes no actuales.
- Sugerencia: una frase en el marco teórico que justifique el uso de las ediciones clásicas.
- Estado: **resuelto** (2026-09-16)
- Resolución (implementación del 2026-09-16, sesión 7): frase en la apertura del Cap. 1 que justifica las ediciones clásicas «por motivos históricos» y reserva la literatura reciente para enseñanza, V&V y bibliotecas.
- Sesión: 1

## 5. Registro de sesiones

| Sesión | Fecha | Bloque(s) | Hallazgos añadidos | Commit de la tesis auditado | Punto donde se detuvo | Siguiente paso |
|---|---|---|---|---|---|---|
| 1 | 2026-09-15 | B0 (auditado) · B1 (auditado) | H-1 a H-14 (1 alta, 8 medias, 5 bajas) | `bdbf18d` (2026-09-11, «Tesis: aplicada la auditoría del 2026-09-11») | B1 completo. Se leyeron `01_introduccion.tex`, `02b_diseno_metodologico.tex`, `00_resumen.tex`, `main.tex` y los 8 PDF del material docente | **B2**: `02_marco_teorico.tex` (414 líneas) y `02b_diseno_metodologico.tex` (ya leído en sesión 1): comprobar que §2.1 sirve a los seis objetivos y que el procedimiento de §2.1.5-2.1.6 es el que aplica `04_resultados.tex`; completar la columna «Metodología» de la trazabilidad. Prestar atención a población/muestra (Taller 4, p. 13) frente a §2.1.4 |
| 2 | 2026-09-15 | B2 (auditado) · B3 (auditado) | H-15 a H-31 (0 altas, 7 medias, 10 bajas); evidencia adicional en H-3 y H-9 | `bdbf18d` (sin cambios en `tesis/` desde la sesión 1: `git log bdbf18d..HEAD -- tesis/` vacío) | B2 y B3 completos. Se leyeron `02_marco_teorico.tex`, `02b_diseno_metodologico.tex`, `01_introduccion.tex`, `04_resultados.tex`, `05_conclusiones.tex` (solo como evidencia de H-25; B4 no auditado), encabezados de `03_diseno_implementacion.tex` y `06_anexos.tex`, Taller 4 y Taller 5 completos, y los instrumentos `tests/vv_mms.py`, `tests/vv_timoshenko.py`, `tests/vv_cook.py` (criterios codificados). Los PDF del material docente se leen con `pymupdf` (`pip install pymupdf`; el `Read` del PDF falla sin poppler) | **B4**: `05_conclusiones.tex` (52 líneas): una conclusión por objetivo (`:11-21`) → verificar contra la columna «Resultado» de la trazabilidad; atención a `:23` («satisface los seis objetivos») frente a H-25/H-26, a la cifra «0,6 %» de `:29` (no está en el Cap. 3, ver H-27), a información nueva en `:43` (Cuthill-McKee, 7-19 %, no aparece en el Cap. 3) y a si cada recomendación (`:43-51`) deriva de una limitación de `:35-37`. Completar la columna «Conclusión» y el estado definitivo de la trazabilidad. Luego B5 con `tesis/respaldo_citas/verificado.json` (incluye comprobar H-31) |
| 3 | 2026-09-16 | B4 (auditado) · B5 (en curso) | H-32 a H-39 (0 altas, 3 medias, 5 bajas) | `bdbf18d` (sin cambios en `tesis/` desde la sesión 1: `git log bdbf18d..HEAD -- tesis/` vacío) | B4 completo: se leyó `05_conclusiones.tex` entero y se contrastó cada cifra con `04_resultados.tex` y `06_anexos.tex:578-615`; se leyeron Taller 5 p. 3-4 y 21, «Cómo se construye el objetivo general» p. 12-15 (tríada) y las líneas de `03_diseno_implementacion.tex` que las conclusiones parafrasean (`:97, 108, 110, 148, 167`). B5 iniciado solo con la correspondencia cita↔referencia (22/22 en ambos sentidos, sin huérfanas; anotado en la cabecera de B5). **Punto de retoma de B5**: formato de las citas en el texto contra `tesis/normas/guia_vancouver.tex` y Taller 2 p. 18-19 (corchetes vs. superíndice ya en H-12; falta: 28 de los 100 comandos llevan página o artículo (`[p.~n]`, `[pp.~a-b]`, `[art.~21]`, una con «pp.~21 y 26») y 72 no; decidir contra la guía si la cita de libro exige página; citas múltiples con `\autocites`; citas de cita); después la lista final entrada por entrada (`referencias.bib`, 22 entradas: campos obligatorios por tipo, ediciones más recientes de H-14, `alvarez_metodologia` sin año) y H-31 (Cook p. 98 y Hughes p. 221 en `tesis/respaldo_citas/verificado.json`) | **B5** desde el punto anotado; si sobra tiempo, **B6** con `tesis/main.tex:43-78`, `00_preliminares.tex` y el índice del Taller 1 p. 20 (ya transcrito en §2.4 de este archivo) |
| 4 | 2026-09-16 | B5 (auditado) · B6 (auditado) | H-40 a H-47 (1 alta, 3 medias, 4 bajas); comprobaciones y evidencia adicional en H-2, H-13, H-14 y H-31 | `bdbf18d` (sin cambios en `tesis/` desde la sesión 1: `git log bdbf18d..HEAD -- tesis/` vacío) | B5 y B6 completos. Se leyeron `guia_vancouver.tex` (678 líneas), `referencias.bib` (22 entradas), `preambulo.tex:255-295`, los 100 comandos de cita con su contexto, `respaldo_citas/verificado.json` entero (22 claves; se leyó cada respaldo NO/PARCIAL y cada bloque «sin_respaldo», y se comprobó contra el texto actual cuál persiste tras `bdbf18d`), la sección 4 de `docs/auditorias/2026-09-11_auditoria_tesis.md`, `docs/notas/2026-09-08_bibliografia-tesis.md` y `2026-09-09_diagnostico-bibliografia.md`, Taller 1 pp. 2-5, 18-26 y Taller 2 pp. 16-20 (con `pymupdf`), y la lista de referencias e índice general impresos en `tesis/main.pdf` (pp. 79-81 y iii; PDF del 2026-09-11, coincide con el commit). B6: encabezados de los 10 `.tex` (`grep '^\\chapter\|^\\section\|^\\subsection'`) contra el índice del Taller 1 p. 20 y el formato de `preambulo.tex:233-236` | **Ningún bloque pendiente.** La siguiente sesión: (1) `git log bdbf18d..HEAD -- tesis/`; si está vacío, no hay nada que auditar y la sesión termina anotándolo en este registro; si hay commits, revisar solo los archivos tocados contra los hallazgos abiertos del bloque correspondiente y anotar cuáles quedaron resueltos **sin cambiar su estado** (eso lo marca el autor). (2) Si el Reglamento de Graduación aparece en `tesis/normas/` (H-1), reabrir B5 y B6 para contrastar formato de citas, listas y estructura contra el texto completo. |
| 5 | 2026-09-16 | Ninguno (sin trabajo pendiente) | Ninguno; 47 abiertos (2 altas, 21 medias, 24 bajas), 0 resueltos | `bdbf18d` (sin cambios en `tesis/`: `git log bdbf18d..origin/main -- tesis/` vacío; `origin/main` = `9b4c662`, el commit de la sesión 4) | Sesión de verificación: se comprobó que los seis bloques siguen auditados, que `tesis/normas/` sigue con solo `guia_vancouver.tex/.pdf` (sin Reglamento de Graduación, H-1 sigue abierto) y que ningún hallazgo fue marcado `resuelto` por el autor. No se leyó ni reauditó ningún archivo de la tesis | Igual que la sesión 4: (1) `git log bdbf18d..HEAD -- tesis/`; si sigue vacío, anotar la sesión y terminar; si hay commits, revisar solo los archivos tocados contra los hallazgos abiertos del bloque correspondiente. (2) Si aparece el Reglamento, reabrir B5 y B6. Mientras la tesis no cambie, la rutina no tiene trabajo: conviene que el autor la pause o la reprograme para cuando retome la redacción. |
| 6 | 2026-09-16 | Ninguno (sin trabajo pendiente) | Ninguno; 47 abiertos (2 altas, 21 medias, 24 bajas), 0 resueltos | `bdbf18d` (sin cambios en `tesis/`: `git log bdbf18d..origin/main -- tesis/` vacío; `origin/main` = `6b0e35d`, el commit de la sesión 5) | Segunda sesión consecutiva de verificación sin trabajo: `tesis/normas/` sigue con solo `guia_vancouver.tex/.pdf` (H-1 abierto), ningún hallazgo marcado `resuelto`, el archivo de auditoría en `origin/main` es idéntico al de la sesión 5. No se leyó ni reauditó ningún archivo de la tesis | Igual que las sesiones 4 y 5: (1) `git log bdbf18d..HEAD -- tesis/`; si sigue vacío, anotar la sesión y terminar; si hay commits, revisar solo los archivos tocados contra los hallazgos abiertos del bloque correspondiente. (2) Si aparece el Reglamento, reabrir B5 y B6. Se notificó al autor que la rutina lleva dos sesiones sin trabajo y que conviene pausarla hasta retomar la redacción o cerrar hallazgos. |
| 7 | 2026-09-16 | Implementación (autor, vía agente; no es sesión de auditoría) | Ninguno; **45 resueltos, 1 parcial (H-13), 1 abierto (H-1)** | `bdbf18d` + cambios sin commit en `tesis/` (capítulos 01–07, `main.tex`, `preambulo.tex`, `referencias.bib`, `normas/guia_vancouver.tex`, `respaldo_citas/`, `figuras/`) y en `tests/vv_mms.py`, `tests/vv_timoshenko.py` | Se implementaron los 47 hallazgos salvo H-1 (Reglamento) y la mitad de H-13 que depende de él. Compila limpia: 158 hojas, 0 errores, 0 indefinidas, biber 0 avisos, 0 desbordes. Guiones de V&V corridos con los criterios nuevos: Timoshenko 5/5 OK, MMS 24/24 OK. Guía Vancouver y respaldo de citas regenerados | **Reauditar lo cambiado**: para cada bloque, contrastar la línea «Resolución» de cada hallazgo con el texto (`git diff bdbf18d -- tesis/`); si algo no cierra, anotarlo como H-48+ sin reabrir lo resuelto. Verificar en particular: la numeración de secciones del Cap. 1 (hay una §1.2 nueva y todo corrió un número), los `\autoref` a `sec:cobertura`, `tab:fases`, `fig:fases-lienzo`, `sec:cook`, y que la frase de procedencia de Álvarez (H-42) sea aceptable para el autor. H-1 sigue esperando el Reglamento. |
