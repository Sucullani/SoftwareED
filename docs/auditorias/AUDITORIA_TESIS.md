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

**Última sesión**: 3 · 2026-09-16 · commit de la tesis auditado: `bdbf18d` (2026-09-11; sin
commits posteriores en `tesis/`).

| Bloque | Contenido | Estado |
|---|---|---|
| B0 | Inventario y norma de citación | **auditado** (sesión 1) |
| B1 | Introducción: problema, objetivos, hipótesis, justificación, alcance | **auditado** (sesión 1) |
| B2 | Marco teórico y metodología | **auditado** (sesión 2) |
| B3 | Resultados | **auditado** (sesión 2) |
| B4 | Conclusiones y recomendaciones | **auditado** (sesión 3) |
| B5 | Citación y referencias contra la norma de B0 | **en curso** (sesión 3: correspondencia cita↔referencia verificada, sin huérfanas; falta formato de citas, lista final y H-31; 4 hallazgos ya registrados desde B0: H-2, H-12 a H-14) |
| B6 | Forma: títulos, numeración, jerarquía, preliminares | pendiente |

**Hallazgos abiertos por severidad**: alta 1 · media 18 · baja 20 · **total 39** (H-1 a H-39). Resueltos: 0.

Lo que más pesa hoy: el **Reglamento de Graduación** que fija formato y referenciación no
está en el repositorio (H-1), la tesis **no declara en su texto la norma de citación** que
sigue (H-2), y la cadena problema → variables → medición sigue partida en dos: las variables
del problema científico no son las que la metodología mide (H-4) y la hipótesis se contrasta
«por diseño» (H-5). B2 y B3 añaden que **la metodología declara un procedimiento que uno de
los tres casos no sigue** (Timoshenko: un solo elemento y una sola malla, H-15), que **cuatro
de los seis objetivos no tienen indicador operacionalizado ni criterio de aceptación**
(H-17), que el marco teórico **anticipa resultados y decisiones de implementación** (H-18) y
**no fundamenta la dimensión pedagógica** que el objetivo general y la hipótesis reclaman
(H-19), y que el **cuarto objetivo se cumple solo hasta el ensamblaje** mientras la validación
de la hipótesis lo da por completo (H-25). B4 cierra la trazabilidad: **las conclusiones
declaran satisfechos los seis objetivos** sin reconocer el cumplimiento parcial de OE4 ni la
ausencia de resultado para OE1 y OE3 (H-32), **dos conclusiones se sostienen en descripciones
de diseño y en citas, no en resultados** (H-33, H-39), y **las recomendaciones introducen
mediciones y decisiones que ningún capítulo reporta** (Cuthill-McKee, 7-19 %, Cholesky; H-34).
Estado final de la trazabilidad: 2 objetivos completos (OE2, OE5, solapados entre sí), 3
débiles (OE1, OE3, OE6), 1 hueco (OE4) y la hipótesis débil.

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
- Evidencia adicional (sesión 2): cuarta formulación en `02_marco_teorico.tex:43`: «La brecha que lo motiva es, por tanto, la ausencia de un entorno integrado, libre y de código abierto, que recorra el canal de cálculo completo … haciendo observables los fenómenos numéricos del método, generando una memoria de cálculo trazable a ese modelo e incorporando verificación y validación rigurosas», que suma dos atributos más (fenómenos numéricos observables, V&V) a la lista de (c).
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
- Evidencia adicional (sesión 2): «cadena» también en `02_marco_teorico.tex:40` («recorre la cadena del MEF de extremo a extremo»), `:412` («la cadena de recuperación de tensiones») y `04_resultados.tex:207` («cada eslabón de la cadena de cálculo»); «canal» en `04_resultados.tex:5, 209, 258`.
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

### B2 — Marco teórico y metodología

**H-15**
- Bloque y sección: B2 · §2.1.4 Casos de estudio y §2.1.5 Procedimiento ↔ §3.4 Validación con la viga de Timoshenko
- Tipo: coherencia
- Severidad: media
- Evidencia: `02b_diseno_metodologico.tex:74`: «Cada uno se resuelve con ambos tipos de elemento (Q4 y Q9) sobre mallas de refinamiento creciente, lo que permite observar el comportamiento de las variables dependientes en función de las independientes». `:81`: «Dentro de cada caso solo se manipulan el tipo de elemento y la densidad de malla». `04_resultados.tex:99`: «Se empleó una malla Q9 estructurada de $56\times8$ elementos (448 elementos, 1921 nodos, 3842 GDL)». `04_resultados.tex:199` (tabla resumen): «Timoshenko $\sigma_x$ (error máx.) & --- & 0,0414\,\%» (columna Q4 vacía). Instrumento: `tests/vv_timoshenko.py:87-88, 133`: `NX = 56`, `NY = 8`, `element_type=ELEMENT_Q9`, sin bucle de refinamiento ni corrida Q4.
- Problema: la metodología enuncia un procedimiento común a los tres casos («cada uno … ambos tipos de elemento … mallas de refinamiento creciente») que el único caso con referencia analítica y comercial no sigue: una sola malla, un solo elemento. En ese caso la variable independiente «discretización» de la Tabla 2.1 no se manipula, no se observa convergencia ni se contrasta Q4 con Q9. Lo que el Cap. 3 aplica no es lo que §2.1 declara.
- Sugerencia: o correr Timoshenko con Q4 y con al menos tres mallas (el guion lo permite) o reescribir §2.1.4 diciendo que el refinamiento y la comparación Q4/Q9 se hacen en MMS y Cook, y que Timoshenko es un contraste puntual con Q9.
- Estado: abierto
- Sesión: 2

**H-16**
- Bloque y sección: B2 · §2.1.6 Criterios de aceptación ↔ instrumento `tests/vv_mms.py`
- Tipo: coherencia
- Severidad: media
- Evidencia: `02b_diseno_metodologico.tex:88`: «Los criterios de aceptación están fijados a priori en los propios guiones … tasas de convergencia observadas dentro de $\pm0{,}5$ de las teóricas en las cuatro configuraciones del MMS (desplazamiento y campo de tensiones recuperado)». `tests/vv_mms.py:439-443`: «# Campo de tensiones recuperado: O(h^1.5) Q4 (superconvergencia interior degradada por la capa de contorno) y O(h^2) Q9. # Tolerancia +-0.5 por la desviacion pre-asintotica … `expected = {"q4": (2.0, 1.0, 1.5), "q9": (3.0, 2.0, 2.0)}`». `02_marco_teorico.tex:412`: «el error de las magnitudes derivadas debe verificarse por separado, y su orden puede ser menor que el de la solución primaria» (sin valor). `04_resultados.tex:58` explica el 1,54 a posteriori: «que no alcance $\mathcal{O}(h^{2})$ se debe a la capa de contorno».
- Problema: para el campo de tensiones recuperado del Q4 no existe tasa «teórica» en el marco teórico ni en la literatura citada; el 1,5 del guion es el valor observado realimentado como expectativa, y el intervalo ±0,5 a su alrededor (1,0–2,0) acepta también el orden del gradiente crudo. El criterio no está «fijado a priori» para ese indicador y, además, es demasiado laxo para detectar una regresión en la extrapolación de tensiones.
- Sugerencia: reservar el criterio de «tasa teórica» a $L^2$ y $H^1$ del desplazamiento, y para $\sigma^*$ enunciar el criterio como cota empírica (≥ 1,4 en Q4, ≥ 1,9 en Q9) declarada como tal.
- Estado: abierto
- Sesión: 2

**H-17**
- Bloque y sección: B2 · §2.1.2 Variables ↔ §2.1.3 Matriz de consistencia ↔ §2.1.6 Criterios
- Tipo: coherencia
- Severidad: media
- Evidencia: indicadores de la matriz (`02b_diseno_metodologico.tex:56-61`): OE1 «Canal de cálculo cubierto», OE3 «Organización de la interfaz; flujo de trabajo», OE4 «Cobertura del canal de cálculo», OE6 «Trazabilidad del cálculo». Ninguno figura en la Tabla 2.1 (`:27-38`), cuyas filas son «definición del modelo», «discretización», «respuesta estructural», «exactitud de la solución» y «controladas». §2.1.6 (`:88-90`) fija criterios numéricos solo para MMS, Timoshenko y Cook y despacha el resto: «la organización de la interfaz y de los módulos (PI-2) se documenta en la \autoref{sec:diseno-edufem}». Taller 4, p. 10: «Definición y operacionalización de las variables, Procedimientos a seguir, Técnicas e instrumentos de medición, Plan de análisis o valoración de los resultados obtenidos».
- Problema: cuatro de los seis objetivos tienen un indicador nominal en la matriz pero ningún instrumento ni criterio con el que el Cap. 3 pueda declararlos cumplidos o no. El resultado es que «cobertura del canal» se juzga sin escala (y en `04_resultados.tex:209` resulta parcial sin que nada lo califique de incumplimiento, H-25). Complementa H-4 (variable efecto sin indicador) y H-5 (hipótesis por diseño).
- Sugerencia: agregar a la Tabla 2.1 una fila «atributos del artefacto» con indicadores contables (etapas del canal con módulo / con memoria; fases con lienzo compartido; formatos con prueba de ida y vuelta) y su umbral en §2.1.6.
- Estado: abierto
- Sesión: 2

**H-18**
- Bloque y sección: B2 · Cap. 1 Marco teórico (§1.5, §1.9, §1.10, §1.11)
- Tipo: coherencia
- Severidad: media
- Evidencia: `02_marco_teorico.tex:182`: «EduFEM impone un umbral mínimo ($\texttt{JACOBIAN\_MIN\_DETERMINANT}$) para detectar y rechazar esas geometrías antes de resolver». `:302`: «EduFEM selecciona el ordenamiento de columnas de mínimo grado sobre $\bm{K}^{T}+\bm{K}$ (opción \texttt{MMD\_AT\_PLUS\_A} de \texttt{scipy.sparse.linalg.splu} …)». `:321`: «la verificación del \autoref{cap:resultados} muestra que el campo recuperado converge de todos modos a $\mathcal{O}(h^{2})$». `:395`: «se exige $q_{SJ} \ge 0{,}7$, $R_J \ge 0{,}5$, $AR \le 3$ y $T_R \le 0{,}3$ … para «buena», y $0{,}3$, $0{,}2$, $5$ y $0{,}5$ … para «aceptable»». `:414`: «EduFEM la reproduce con errores inferiores al $0{,}3\,\%$ en las magnitudes primarias —tensión normal y flecha—, que el \autoref{cap:resultados} cuantifica en detalle». «EduFEM» aparece 25 veces en el capítulo. Taller 1, p. 20: «Capítulo 1 MARCO TEÓRICO DE …» separado de «Capítulo 2 DISEÑO E IMPLEMENTACIÓN DEL MODELO A DESARROLLAR» y «Capítulo 3 PRESENTACIÓN DE RESULTADOS».
- Problema: el marco teórico adelanta resultados del Cap. 3 (0,3 %, $\mathcal{O}(h^{2})$) y fija decisiones de implementación (constantes del programa, opción del solucionador, umbrales de la interfaz) que son materia del Cap. 2 §2.2. El lector encuentra las cifras de validación antes de la metodología que las produce, y la fundamentación deja de ser independiente del artefacto que debería sustentar.
- Sugerencia: dejar en el Cap. 1 la teoría y las referencias bibliográficas de cada umbral; mover a §2.2 las elecciones de EduFEM y al Cap. 3 toda cifra medida.
- Estado: abierto
- Sesión: 2

**H-19**
- Bloque y sección: B2 · Cap. 1 Marco teórico ↔ objetivo general e hipótesis
- Tipo: coherencia
- Severidad: media
- Evidencia: objetivo general (`01_introduccion.tex:29`): «como apoyo a la enseñanza y el aprendizaje del MEF». Hipótesis (`:44`): «esa transparencia constituye un apoyo plausible al aprendizaje de sus fundamentos». Metodología (`:56`): «los criterios de diseño pedagógico se fundamentan cualitativamente en la literatura sobre enseñanza del MEF». Cap. 1: §1.1 «Antecedentes y estado del arte» (revisión de software) y §1.2–§1.11, todas numéricas; las palabras «aprendizaje», «pedagógico», «didáctico» y «enseñanza» aparecen solo en `02_marco_teorico.tex:4-43` (antecedentes), `:263` y `:382`. OE1 (`01_introduccion.tex:34`) enumera únicamente contenidos numéricos.
- Problema: la finalidad del objetivo general y la segunda cláusula de la hipótesis descansan en una afirmación pedagógica (la transparencia del cálculo apoya el aprendizaje) que el marco teórico no fundamenta: no hay sección sobre por qué hacer visibles los pasos intermedios favorece la comprensión, ni sobre qué principio guía el conmutador Fórmula↔Valores, el lienzo único o el orden M0–M7. Las citas de Lee y Bishay se usan como antecedentes de software, no como marco. Taller 5, p. 3: «Cada dimensión o indicador debe tener el contraste de la teoría y los antecedentes».
- Sugerencia: una sección «Fundamentos de la enseñanza del MEF» en el Cap. 1 (o quitar «aprendizaje» del objetivo general y de la hipótesis y dejarlo en la justificación).
- Estado: abierto
- Sesión: 2

**H-20**
- Bloque y sección: B2 · §1.11 Verificación y validación ↔ OE5, §2.1.6 y títulos del Cap. 3
- Tipo: coherencia
- Severidad: baja
- Evidencia: `02_marco_teorico.tex:400`: «en su acepción estricta la validación exige el contraste con mediciones experimentales, y este trabajo no realiza campaña experimental propia. … el contraste corresponde a verificación de solución y a comparación código a código». Pese a ello: OE5 (`01_introduccion.tex:38`) «Verificar y validar el software»; `02b_diseno_metodologico.tex:88` «la validación exige que los desplazamientos y las tensiones concuerden»; `04_resultados.tex:97` «\section{Validación con la viga de Timoshenko}», `:148` «\section{Validación con la membrana de Cook…}»; `06_anexos.tex:655` «\chapter{Modelo de validación en SAP2000…}».
- Problema: el documento adopta la definición de Oberkampf, reconoce que según ella no valida, y sigue titulando «validación» al contraste en el objetivo, la metodología y los resultados. Mismo concepto, dos términos, con la definición estricta en contra.
- Sugerencia: «contraste con referencias» o «verificación de solución» en OE5, §2.1.6 y títulos, dejando «validación» solo con la salvedad enunciada una vez.
- Estado: abierto
- Sesión: 2

**H-21**
- Bloque y sección: B2 · §2.1.1 Tipo de investigación y modelo de simulación numérica
- Tipo: coherencia
- Severidad: baja
- Evidencia: título de `02b_diseno_metodologico.tex:11`: «\subsection{Tipo de investigación y modelo de simulación numérica}». El cuerpo (`:14-16`) trata solo el modelo; el tipo de investigación está fuera de §2.1, en la apertura del capítulo (`:4`: «Por su finalidad, el trabajo es de carácter \emph{propositivo} … \emph{investigación aplicada} de tipo \emph{tecnológico} … con enfoque \emph{cuantitativo}»). Taller 4, p. 4, nombra los tipos de modelo: «Desarrollo teórico · Modelación teórica · Modelación experimental · Modelación de simulación teórica»; la tesis lo llama «modelo de simulación numérica» (`:14`) sin mapearlo a esa lista.
- Problema: la subsección que promete el tipo de investigación no lo contiene (se lee antes, en la introducción del capítulo), y el modelo se nombra con un término que el material del tribunal no usa. Se suma a H-10 (nivel descriptivo/comparativo ausente).
- Sugerencia: mover el párrafo de `:4` a §2.1.1 y decir «modelación de simulación teórica —aquí, numérica— en la clasificación del Taller 4».
- Estado: abierto
- Sesión: 2

**H-22**
- Bloque y sección: B2 · §2.1.4 Casos de estudio y criterio de selección ↔ Taller 4 (población y muestra)
- Tipo: coherencia
- Severidad: baja
- Evidencia: Taller 4, p. 5: «Muestra: Es una parte representativa que contienen todas las características de la Población. Seleccionada por procedimientos aleatorios/probabilísticos»; p. 6: «Adecuada: Cuantitativamente, debe ser suficientemente grande»; p. 13: «Es importante establecer la población y la muestra, sobre la cual se aplicará el modelo especificado». `02b_diseno_metodologico.tex:74`: «El conjunto de casos que sigue no es una muestra estadística de ese universo, sino una selección \emph{intencional} por valor probatorio —una muestra dirigida, no probabilística». `04_resultados.tex:251`: «una batería más amplia de casos de referencia reforzaría la confianza en el comportamiento del software ante geometrías y condiciones de carga más diversas».
- Problema: el apartamiento del muestreo probabilístico está justificado (Sampieri, Oberkampf), pero la «adecuación» (tamaño) no se argumenta en §2.1.4: tres casos, uno de ellos con una sola malla (H-15), y el propio Cap. 3 admite que son pocos. Lo que debía sostenerse en la metodología queda como limitación en los resultados.
- Sugerencia: decir en §2.1.4 qué término del modelo ejercita cada caso (fuente volumétrica + Dirichlet no homogéneo; carga superficial + apoyos; distorsión + cortante) y por qué con eso la cobertura es suficiente.
- Estado: abierto
- Sesión: 2

**H-23**
- Bloque y sección: B2 · Tabla 2.1 (indicadores) ↔ §2.1.5 instrumentos y §2.1.6 criterios
- Tipo: coherencia
- Severidad: baja
- Evidencia: Tabla 2.1 (`02b_diseno_metodologico.tex:33-34`): indicadores «$\varepsilon_x,\varepsilon_y,\gamma_{xy}$; $u,v$ nodales; reacciones en los apoyos» y «error relativo (\%) en $\sigma_x$ y en deflexión frente al analítico y a SAP2000». §2.1.6 (`:88`) solo fija: tasas MMS, «flecha central de la viga de Timoshenko dentro del $3\,\%$ de la solución analítica» y los dos criterios de Cook. En el Cap. 3, «reacciones» aparece una sola vez (`04_resultados.tex:10`, como magnitud que «se registra») y las deformaciones ninguna; no hay criterio para $\sigma_x$ ni para la comparación con SAP2000.
- Problema: la operacionalización declara indicadores que ni los instrumentos miden ni los criterios juzgan ni el Cap. 3 reporta. En particular, la comparación con SAP2000 —parte literal de OE5— no tiene umbral de aceptación.
- Sugerencia: podar la Tabla 2.1 a lo que se mide, o añadir criterios para $\sigma_x$ (analítico y SAP2000) y reportar reacciones al menos en Timoshenko (equilibrio global, que es además pedagógico).
- Estado: abierto
- Sesión: 2

**H-24**
- Bloque y sección: B2 · §2.1.3 Matriz de consistencia, fila OE3
- Tipo: coherencia
- Severidad: baja
- Evidencia: `02b_diseno_metodologico.tex:58`: «Diseñar la interfaz pre/proceso/post & PI-2 & Organización de la interfaz; flujo de trabajo & Diseño centrado en un lienzo único compartido & \S\ref{sec:pre-proceso}». Existen `03_diseno_implementacion.tex:94` «\subsection{Pre-proceso interactivo}» y `:150` «\subsection{Post-proceso}»; la fila cita solo la primera.
- Problema: el objetivo abarca tres fases y la evidencia que la matriz le asigna cubre una. Un lector que siga la matriz no llega al post-proceso ni al lienzo compartido entre fases.
- Sugerencia: «\S\ref{sec:pre-proceso}–\S\ref{sec:post-proceso}».
- Estado: abierto
- Sesión: 2

### B3 — Resultados

**H-25**
- Bloque y sección: B3 · §3.6 Cobertura del canal de cálculo ↔ OE4 ↔ §3.9 Validación de la hipótesis
- Tipo: coherencia
- Severidad: media
- Evidencia: OE4 (`01_introduccion.tex:37`): «Desarrollar módulos educativos que expongan, paso a paso y sobre el modelo real, cada etapa del canal de cálculo del MEF». `04_resultados.tex:209`: «La cobertura del canal de cálculo por los módulos es completa hasta el ensamblaje; la recuperación de tensiones, último eslabón del canal, no tiene un módulo propio y se expone en el post-proceso mediante la sonda puntual …, la vista tridimensional y la memoria de cálculo». `04_resultados.tex:258`: «queda confirmada al verificarse … : el motor recorre la cadena completa …, los módulos educativos la exponen paso a paso». `05_conclusiones.tex:17`: «cada etapa del canal de cálculo del MEF, del mapeo isoparamétrico al ensamblaje global».
- Problema: el resultado de OE4 es parcial (ni la resolución del sistema ni la recuperación de tensiones tienen módulo) y el Cap. 3 lo dice en §3.6, pero tres párrafos después la validación de la hipótesis lo da por completo y la conclusión reescribe «cada etapa» como «hasta el ensamblaje». El objetivo, el resultado y su lectura no dicen lo mismo. Taller 5, p. 21: «Mostrar si hay o no respuesta a los objetivos planteados».
- Sugerencia: o reformular OE4 («cada etapa hasta el ensamblaje; la recuperación de tensiones mediante el post-proceso y la memoria») o declarar en §3.9 y en Conclusiones el cumplimiento parcial.
- Estado: abierto
- Sesión: 2

**H-26**
- Bloque y sección: B3 · §3.6 Resultados del software ↔ OE1, OE3 ↔ Estructura del documento
- Tipo: coherencia
- Severidad: media
- Evidencia: `01_introduccion.tex:69`: «El \autoref{cap:resultados} presenta y analiza los resultados: expone el producto final, mide los datos…». §3.6 (`04_resultados.tex:205-213`) no contiene figura, tabla ni medida: las cinco figuras del capítulo (`:66, 72, 81, 143, 180`) y sus siete tablas son de V&V; el texto de `:211-213` («Cada módulo que exhibe formulación matemática incorpora un conmutador Fórmula~$\leftrightarrow$~Valores…», «La fase de post-proceso ofrece…») repite lo descrito en §2.2. OE1 no tiene resultado en el Cap. 3 (la matriz, `02b:56`, remite al Cap. 1). Taller 5, p. 3: «Deben responder a los objetivos planteados … Se presentan en tablas, gráficas que sean fáciles de entender».
- Problema: dos objetivos (OE1, OE3) no tienen resultado en el capítulo de resultados, y el «producto final» que la Introducción anuncia para el Cap. 3 no se muestra allí (las capturas de la aplicación están en el Cap. 2 y en el Anexo B). §3.6 es prosa de diseño, no un resultado.
- Sugerencia: para OE3, una figura de la aplicación con las tres fases sobre el mismo lienzo y una tabla «fase → operaciones disponibles → módulo»; para OE1, aceptar que el Cap. 1 es su producto y decirlo en §3.9, o reformular OE1 como fundamentación que «se materializa» y no como objetivo con resultado.
- Estado: abierto
- Sesión: 2

**H-27**
- Bloque y sección: B3 · §3.8.1 Alcances y §3.9 ↔ Anexo D
- Tipo: coherencia
- Severidad: baja
- Evidencia: `04_resultados.tex:219`: «de hasta el $2{,}9\,\%$ en la tensión cortante … Frente a SAP2000 las diferencias son del $0{,}21\,\%$ en $\sigma_x$ y de hasta el $0{,}56\,\%$ en desplazamientos; en la componente cortante el modelo de cáscara queda más cerca de la solución analítica ($0{,}16\,\%$) que EduFEM»; `:260` repite «hasta el $0{,}56\,\%$ frente a SAP2000». Esas cifras no están en ninguna tabla del Cap. 3 (`tab:timoshenko-stress` solo $\sigma_x$; `tab:timoshenko-defl` solo analítico); provienen de `06_anexos.tex:580-595` (`tab:tim-componentes`) y de la tabla de desplazamientos del Anexo D. Taller 5, p. 4: «Se utilizan tablas y figuras para enriquecer los datos, no duplicarlos y con un texto que explique».
- Problema: la interpretación y la validación de la hipótesis se apoyan en datos que el capítulo no presenta; el lector del Cap. 3 no puede verificar el 2,9 % ni el 0,56 % sin ir al anexo, y el capítulo los interpreta antes de mostrarlos.
- Sugerencia: añadir a `tab:timoshenko-stress` las columnas de $\sigma_y$ y $\tau_{xy}$ (o una fila de máximos) y a `tab:timoshenko-defl` la columna SAP2000.
- Estado: abierto
- Sesión: 2

**H-28**
- Bloque y sección: B3 · §3.2–§3.5 ↔ §3.8 Interpretación de los resultados
- Tipo: forma
- Severidad: baja
- Evidencia: Taller 5, p. 4: «Solo se debe describir y no interpretar o hacer comentarios de los resultados». El Cap. 3 tiene una sección propia de interpretación (§3.8) y, sin embargo, interpreta en cada sección de datos: `04_resultados.tex:120`: «no permite afirmar la superioridad de una herramienta sobre la otra»; `:137`: «Este detalle es pedagógicamente significativo … Este contraste ilustra, además, la importancia de seleccionar la referencia analítica adecuada»; `:174`: «La comparación a igualdad de grados de libertad es el argumento pedagógico central … Esta evidencia empírica permite al estudiante constatar de primera mano»; `:58`: relato del defecto de $\bm{E}_{\text{Q4}}$ «detectado y corregido durante el desarrollo».
- Problema: descripción e interpretación van mezcladas, y §3.8 queda como segunda interpretación (repite las cifras de §3.4–§3.5). El material docente pide separarlas.
- Sugerencia: dejar en §3.2–§3.6 tablas, figuras y descripción en pasado; concentrar juicios y lecciones pedagógicas en §3.8.
- Estado: abierto
- Sesión: 2

**H-29**
- Bloque y sección: B3 · §3.8.3 Limitaciones observadas (`tab:tiempos`) ↔ §2.1 metodología
- Tipo: coherencia
- Severidad: baja
- Evidencia: `04_resultados.tex:231-251`: tabla `tab:tiempos` con «$t_{\text{ensamblaje}}$ (s) & $t_{\text{solución}}$ (s) & $\bm{K}$ densa (MB) & $\bm{K}$ dispersa (MB)» medidos con `tests/bench_timing.py` y comparación de ordenamientos («se reduce 1,7 veces con 2178 GDL, 2,0 veces con 8450 GDL y 2,9 veces con 33\,282 GDL»). En `02b_diseno_metodologico.tex` no aparecen «tiempo», «memoria (MB)» ni `bench_timing` como variable, indicador o instrumento (0 ocurrencias); la Tabla 2.1 no tiene fila de desempeño.
- Problema: el Cap. 3 reporta una medición (rendimiento del solucionador) que la metodología no planificó: sin variable, sin instrumento declarado, sin criterio. Resultado que no responde a ningún objetivo ni pregunta (el criterio de B3 lo señala expresamente).
- Sugerencia: o añadir «desempeño» como variable controlada/observada en la Tabla 2.1 con su instrumento, o mover `tab:tiempos` al Anexo D como dato complementario.
- Estado: abierto
- Sesión: 2

**H-30**
- Bloque y sección: B3 · §3.8.2 Comparación cualitativa con herramientas existentes ↔ §1.1 Antecedentes
- Tipo: coherencia
- Severidad: baja
- Evidencia: `04_resultados.tex:223`: «En relación con las herramientas educativas reportadas en la literatura ---simuladores de armaduras, visualizadores de los modos propios de la matriz de rigidez o entornos de procesamiento interactivo de ecuaciones del MEF \autocite{bishay2020teaching,lee2015interactive,lee2015eigenmodes}---, la contribución distintiva de EduFEM es la cobertura integral del canal de cálculo …». Es el contenido de `02_marco_teorico.tex:11-43` y de `tab:comparativa`, sin dato nuevo del Cap. 3 y sin referencia a esa tabla.
- Problema: una subsección de «resultados» que no presenta resultado alguno: repite la comparación cualitativa del marco teórico. Si la intención es contrastar los resultados con los antecedentes (Taller 5, p. 3: «Cada dimensión o indicador debe tener el contraste de la teoría y los antecedentes»), debería confrontar cifras (p. ej. los errores de Cook con los publicados por Cook/Hughes) y no repetir la tabla de atributos.
- Sugerencia: reducir §3.8.2 a un párrafo que remita a `tab:comparativa` y añada lo que el Cap. 3 aporta a esa tabla (la fila «V\&V publicada»).
- Estado: abierto
- Sesión: 2

**H-31**
- Bloque y sección: B3 · §3.5 Membrana de Cook (nota al pie) ↔ §1.11
- Tipo: coherencia
- Severidad: baja
- Evidencia: `02_marco_teorico.tex:414`: «el desplazamiento del extremo converge al valor de referencia de uso convencional, $23{,}96$, … \autocites[p.~98]{cook2002concepts}[p.~221]{hughes2000fem}». `04_resultados.tex:150` (nota): «su valor de referencia es un límite de convergencia y no un dato exacto, por lo que conviene tratarlo como tal y no como una constante tomada de una fuente. En lugar de descansar en el valor convencional, este trabajo lo corrobora con evidencia propia».
- Problema: el marco teórico atribuye el 23,96 a dos fuentes con página; el Cap. 3 dice que no debe tratarse como constante tomada de una fuente. El lector no sabe si el valor está respaldado bibliográficamente o solo por la extrapolación de Richardson propia. B5 debe comprobar que Cook p. 98 y Hughes p. 221 efectivamente dan 23,96 (`tesis/respaldo_citas/verificado.json`).
- Sugerencia: una sola procedencia: «valor convencional citado por Cook y Hughes y corroborado aquí por extrapolación de Richardson».
- Estado: abierto
- Sesión: 2

### B4 — Conclusiones y recomendaciones

**H-32**
- Bloque y sección: B4 · Conclusiones, veredicto global (`05_conclusiones.tex:23`) ↔ §3.6 ↔ OE1, OE3, OE4
- Tipo: coherencia
- Severidad: media
- Evidencia: `05_conclusiones.tex:23`: «En conjunto, los resultados confirman que EduFEM satisface los seis objetivos específicos y, con ello, el objetivo general. … hace observable y contrastable cada etapa del procedimiento, que es la respuesta al problema científico planteado». `04_resultados.tex:209`: «La cobertura del canal de cálculo por los módulos es completa hasta el ensamblaje; la recuperación de tensiones, último eslabón del canal, no tiene un módulo propio». OE1 y OE3 no tienen resultado en el Cap. 3 (H-26). Taller 5, p. 21: «Mostrar si hay o no respuesta a los objetivos planteados por el investigador · Señalar falencias o debilidades en la investigación».
- Problema: el único lugar donde la tesis emite un veredicto sobre los seis objetivos los da todos por satisfechos, sin matiz, cuando el propio Cap. 3 declara parcial la cobertura de OE4 y no aporta resultado para OE1 ni OE3. La sección «Limitaciones» (`05:35-37`) tampoco recoge esa parcialidad: habla de alcance físico, biblioteca de elementos, solucionador, bloqueo y validación pedagógica, no de las etapas del canal sin módulo. El material del tribunal pide decir «si hay o no respuesta»; el texto responde «sí» a todo. Amplía a `05:23` lo que H-25 registró para `05:17`.
- Sugerencia: «satisface los objetivos específicos, con el cuarto cumplido hasta el ensamblaje y la recuperación de tensiones cubierta por el post-proceso y la memoria», y anotar esa parcialidad en Limitaciones.
- Estado: abierto
- Sesión: 3

**H-33**
- Bloque y sección: B4 · Conclusiones OE1 (`05:11`) y OE3 (`05:15`) ↔ Cap. 2 §2.2 ↔ Cap. 3
- Tipo: coherencia
- Severidad: media
- Evidencia: `05_conclusiones.tex:15`: «se logró una aplicación organizada en las tres fases canónicas … que comparten un único lienzo interactivo. … La interfaz soporta selección bidireccional entre las tablas de datos y el lienzo, deshacer y rehacer sobre el modelo completo, y validación automática de la salud del modelo previa a la resolución». Esas tres propiedades provienen de la descripción de diseño: `03_diseno_implementacion.tex:108` («La sincronización entre lienzo y tabla es bidireccional»), `:110` («Las acciones del usuario son reversibles mediante un mecanismo de deshacer y rehacer»), `02b_diseno_metodologico.tex:79` (validador de salud); ninguna aparece en `04_resultados.tex` (0 ocurrencias de «bidireccional», «deshacer», «salud del modelo»). `05:11`: «se sistematizó el MEF … anclado a la literatura clásica de la disciplina \autocite{zienkiewicz2013fem,bathe2014fem,hughes2000fem,cook2002concepts}», con remisión únicamente al Cap. 1. Taller 5, p. 21: «Vincular respecto a la metodología aplicada o al instrumento de medición»; «Se presenta de manera sintetizada lo planteado por el investigador respecto a los resultados, dejando claras las evidencias».
- Problema: dos de las seis conclusiones no cierran sobre un resultado: la de OE3 enumera funcionalidades tomadas del capítulo de diseño (lo que se construyó, no lo que se midió u observó) y la de OE1 resume el capítulo teórico. Ninguna de las dos pasa por instrumento, criterio ni dato del Cap. 3, así que el lector no puede distinguir «se diseñó» de «se comprobó». Es la contraparte en B4 de H-26 (sin resultado) y de H-17 (sin criterio).
- Sugerencia: para OE3, cerrar sobre lo que sí se observó (las tres fases operando sobre el mismo lienzo en los casos de V&V, o la figura/tabla que H-26 sugiere); para OE1, reformular como «se estableció la base teórica que el motor, los módulos y la memoria comparten» sin presentarla como resultado.
- Estado: abierto
- Sesión: 3

**H-34**
- Bloque y sección: B4 · Recomendaciones, «Optimización del solucionador» (`05:43`) ↔ Cap. 2 y Cap. 3
- Tipo: coherencia
- Severidad: media
- Evidencia: `05_conclusiones.tex:43`: «Durante el desarrollo se evaluó además una reordenación de Cuthill-McKee inverso previa a la factorización y se descartó: solo compensó el costo de permutar en sistemas por encima de unos ocho mil grados de libertad, con ganancias del 7 al 19\,\%, un tamaño en el que el tiempo de resolución ya no es el factor limitante». Ídem: «la definición positiva vuelve innecesario el pivoteo, de modo que el trabajo aritmético se reduce aproximadamente a la mitad del de una factorización LU general». Búsqueda en `tesis/capitulos/*.tex`: «Cuthill» 0 ocurrencias fuera de `05:43`; «Cholesky» 0 ocurrencias fuera de `05:43`; «7 al 19» 0; «ocho mil» 0. El Cap. 3 (`04:251`) solo reporta el ordenamiento de mínimo grado frente a COLAMD (1,7–2,9 veces). Taller 5, p. 21: la conclusión «describe los resultados más relevantes, teniendo en cuenta la estructura del trabajo».
- Problema: la recomendación reporta una medición (ensayo de Cuthill-McKee inverso, umbral de ocho mil GDL, ganancia del 7-19 %) y un argumento teórico (coste de Cholesky) que no están en el marco teórico, en la metodología ni en los resultados. Es información nueva en el capítulo que debe derivar de lo anterior; además, la medición carece de instrumento y de tabla, a diferencia de `tab:tiempos`. Se suma a H-29 (desempeño medido sin planificar).
- Sugerencia: llevar el ensayo de Cuthill-McKee a §3.8.3 junto a `tab:tiempos` (con su guion) y el argumento de Cholesky a §1.9 o §2.2.4; dejar en la recomendación solo la línea de trabajo.
- Estado: abierto
- Sesión: 3

**H-35**
- Bloque y sección: B4 · Recomendaciones, «Ampliación de la batería de validación» (`05:49`) ↔ §3.2, §3.3, §3.4
- Tipo: coherencia
- Severidad: baja
- Evidencia: `05_conclusiones.tex:49`: «Se recomienda incorporar … un caso con carga superficial variable y peso propio, de modo que la validación externa cubra el estado plano que la práctica civil emplea con más frecuencia y las cargas que hoy solo se verifican por consistencia interna». §3.3 «Consistencia interna del modelo de datos» (`04:86-95`) verifica el ciclo Q4→Q9→Q4, los identificadores no contiguos y la interoperabilidad; no menciona cargas. El peso propio (fuerza de volumen) se verifica por MMS en §3.2 (`04:25`: «cuyo término fuente … se inyecta como fuerza de volumen»), y la carga superficial uniforme se valida externamente en Timoshenko (`04:99`: «sometida a una carga uniforme»; `tests/vv_timoshenko.py:167-170`: `add_surface_load(… q_start=Q_NM, q_end=Q_NM`). La carga superficial variable no se verifica en ningún lugar del Cap. 3.
- Problema: la recomendación atribuye a «consistencia interna» una verificación de cargas que esa sección no contiene, y describe como pendiente de validación externa una carga (uniforme) que Timoshenko ya valida y otra (peso propio) que el MMS verifica. La carencia real —carga superficial variable sin verificación reportada— queda sin nombrar. La recomendación no deriva con exactitud del resultado que invoca.
- Sugerencia: «un caso con carga superficial linealmente variable, que el Cap. 3 no verifica, y un caso civil en deformación plana con peso propio».
- Estado: abierto
- Sesión: 3

**H-36**
- Bloque y sección: B4 · Recomendaciones (`05:41-51`) ↔ Limitaciones (`05:35-37`) ↔ tríada capítulo–conclusión–recomendación
- Tipo: coherencia
- Severidad: baja
- Evidencia: `05_conclusiones.tex:41`: «cada una anclada en el capítulo del que deriva: la ampliación de la formulación (tratamiento del bloqueo, más tipos de elemento) en el \autoref{cap:marco_teorico}; la del software (solucionador, extensión a tres dimensiones) en el \autoref{cap:diseno}; y la de la evidencia (más casos de referencia y validación pedagógica) en el \autoref{cap:resultados}». `05:47`: una sola recomendación «Más tipos de elemento y extensión a tres dimensiones» junta el ítem asignado al Cap. 1 con el asignado al Cap. 2. `05:49` (batería de validación) deriva de `04:251` («una batería más amplia de casos de referencia reforzaría la confianza»), pero la sección Limitaciones de las Conclusiones (`05:35-37`) no enuncia el número de casos como limitación. Material docente («Cómo se construye el objetivo general», p. 15): «LA TRIADA: CAPITULO 1 → CONCLUSIÓN 1 → RECOMENDACIÓN 1 · CAPITULO 2 → … · CAPITULO 3 → …». `01_introduccion.tex:70`: «con la conclusión y la recomendación que corresponden a cada capítulo».
- Problema: el texto promete un anclaje por capítulo (y la Introducción, una conclusión y una recomendación por capítulo) que la estructura no cumple: hay seis conclusiones (por objetivo), cinco recomendaciones (por tema) y una de ellas cruza dos capítulos según el propio reparto de `05:41`. Una recomendación deriva de una limitación que las Conclusiones no declaran.
- Sugerencia: reagrupar las recomendaciones en tres (una por capítulo, con sub-ítems) o quitar de `05:41` y de `01:70` la promesa de correspondencia por capítulo; añadir a Limitaciones la frase de `04:251`.
- Estado: abierto
- Sesión: 3

**H-37**
- Bloque y sección: B4 · Conclusiones, conclusión general (`05:7`) ↔ Planteamiento del problema
- Tipo: coherencia
- Severidad: baja
- Evidencia: `05_conclusiones.tex:7`: «El trabajo regresa así a la contradicción que lo originó: la doble brecha entre la abstracción de los textos clásicos del MEF y la opacidad del software profesional como caja negra». `01_introduccion.tex:11`: «La brecha, en consecuencia, es doble: existe una dificultad de aprendizaje genuina vinculada a la naturaleza abstracta del método, y una insuficiencia de herramientas que la atiendan». `01_introduccion.tex:15`: «La insuficiencia de una herramienta con esos atributos es la contradicción que origina el trabajo».
- Problema: la conclusión cierra sobre el problema, como pide el Taller 5 («Vincular la respuesta a la pregunta problema»), pero redefine sus dos términos: en la Introducción la «doble brecha» es (dificultad de aprendizaje) + (insuficiencia de herramientas) y la «contradicción» es solo el segundo término; en las Conclusiones la «doble brecha» es (abstracción de textos) + (opacidad del software) y se identifica con la «contradicción». El lector que compare ambos pasajes no encuentra el mismo problema.
- Sugerencia: repetir en `05:7` la formulación de `01:11` y `01:15` con los mismos dos términos.
- Estado: abierto
- Sesión: 3

**H-38**
- Bloque y sección: B4 · Limitaciones (`05:35-37`) ↔ «Alcance y limitaciones» (`01:66`) ↔ §3.8.3 (`04:227-229`)
- Tipo: coherencia
- Severidad: baja
- Evidencia: las limitaciones se enuncian en tres lugares con tres conjuntos distintos. `05:35`: «sin mallado automático: el estudiante construye la malla manualmente, mediante importación DXF o por generación estructurada en los casos de validación» («mallado automático»: 0 ocurrencias en `01_introduccion.tex` y `04_resultados.tex`). `01:66`: «El catálogo de materiales se restringe a comportamiento elástico, isótropo y lineal» («isótrop»: 0 ocurrencias en `05_conclusiones.tex`). `05:37` y `04:231-251`: limitación de escalabilidad del solucionador, ausente en `01:66`. `05:37`: «no se realizó una validación empírica del impacto educativo», presente en `01:66` y `04:264`.
- Problema: cada sección agrega o quita limitaciones sin que ninguna sea la lista completa. La de las Conclusiones, que debería recoger las «falencias o debilidades» (Taller 5, p. 21), omite el material isótropo y, como señala H-32, la cobertura parcial del canal, mientras estrena una (mallado) que el alcance de la Introducción no había delimitado.
- Sugerencia: una sola lista en «Alcance y limitaciones»; en Conclusiones, remitir a ella y agregar solo lo que se descubrió al hacer el trabajo (escalabilidad, cobertura parcial, pocos casos).
- Estado: abierto
- Sesión: 3

**H-39**
- Bloque y sección: B4 · Conclusiones (`05:15, 17, 23`) ↔ resultados propios
- Tipo: coherencia
- Severidad: baja
- Evidencia: `05_conclusiones.tex:15`: «en línea con la evidencia sobre el valor de la interactividad en la enseñanza del método \autocite{lee2015interactive,bishay2020teaching}». `05:17`: «Este enfoque materializa el aporte pedagógico central del trabajo: hacer visible y manipulable lo que en la enseñanza tradicional permanece como una caja negra … \autocite{lee2015eigenmodes,perezsantiago2023fem}». `05:23`: «su valor como apoyo a la enseñanza y el aprendizaje del MEF se sostiene por diseño y en la literatura». El capítulo contiene 9 comandos de cita (8 `\autocite`, 16 claves); 5 de ellas sostienen afirmaciones pedagógicas. Taller 5, p. 21: la conclusión presenta «lo planteado por el investigador respecto a los resultados, dejando claras las evidencias».
- Problema: donde el trabajo no tiene resultado propio (la dimensión pedagógica: H-5, H-19), la conclusión sustituye la evidencia por citas de terceros y lo dice expresamente («se sostiene … en la literatura»). Una conclusión que descansa en la bibliografía no concluye nada del trabajo; y la literatura citada tampoco fue presentada en el marco teórico como fundamento pedagógico (H-19), solo como antecedentes de software.
- Sugerencia: reservar las citas para el marco teórico y formular las conclusiones pedagógicas como lo que son: decisiones de diseño fundamentadas en el Cap. 1, con su contraste empírico pendiente (`05:51`).
- Estado: abierto
- Sesión: 3

### B5 — Citación y referencias (registrados en sesión 1 desde B0; bloque en curso desde la sesión 3)

Comprobación mecánica de la sesión 3 (sin hallazgo): las 22 entradas de
`tesis/bibliografia/referencias.bib` se citan al menos una vez y las 22 claves citadas en
`tesis/capitulos/*.tex` existen en el `.bib`; no hay `\nocite`. Total: 100 comandos de cita
(`02_marco_teorico` 47, `01_introduccion` 18, `04_resultados` 15, `05_conclusiones` 9,
`02b_diseno_metodologico` 8, `03_diseno_implementacion` 3; 0 en anexos, resumen y
nomenclatura). La correspondencia cita↔referencia se cumple en ambos sentidos.

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
| 2 | 2026-09-15 | B2 (auditado) · B3 (auditado) | H-15 a H-31 (0 altas, 7 medias, 10 bajas); evidencia adicional en H-3 y H-9 | `bdbf18d` (sin cambios en `tesis/` desde la sesión 1: `git log bdbf18d..HEAD -- tesis/` vacío) | B2 y B3 completos. Se leyeron `02_marco_teorico.tex`, `02b_diseno_metodologico.tex`, `01_introduccion.tex`, `04_resultados.tex`, `05_conclusiones.tex` (solo como evidencia de H-25; B4 no auditado), encabezados de `03_diseno_implementacion.tex` y `06_anexos.tex`, Taller 4 y Taller 5 completos, y los instrumentos `tests/vv_mms.py`, `tests/vv_timoshenko.py`, `tests/vv_cook.py` (criterios codificados). Los PDF del material docente se leen con `pymupdf` (`pip install pymupdf`; el `Read` del PDF falla sin poppler) | **B4**: `05_conclusiones.tex` (52 líneas): una conclusión por objetivo (`:11-21`) → verificar contra la columna «Resultado» de la trazabilidad; atención a `:23` («satisface los seis objetivos») frente a H-25/H-26, a la cifra «0,6 %» de `:29` (no está en el Cap. 3, ver H-27), a información nueva en `:43` (Cuthill-McKee, 7-19 %, no aparece en el Cap. 3) y a si cada recomendación (`:43-51`) deriva de una limitación de `:35-37`. Completar la columna «Conclusión» y el estado definitivo de la trazabilidad. Luego B5 con `tesis/respaldo_citas/verificado.json` (incluye comprobar H-31) |
| 3 | 2026-09-16 | B4 (auditado) · B5 (en curso) | H-32 a H-39 (0 altas, 3 medias, 5 bajas) | `bdbf18d` (sin cambios en `tesis/` desde la sesión 1: `git log bdbf18d..HEAD -- tesis/` vacío) | B4 completo: se leyó `05_conclusiones.tex` entero y se contrastó cada cifra con `04_resultados.tex` y `06_anexos.tex:578-615`; se leyeron Taller 5 p. 3-4 y 21, «Cómo se construye el objetivo general» p. 12-15 (tríada) y las líneas de `03_diseno_implementacion.tex` que las conclusiones parafrasean (`:97, 108, 110, 148, 167`). B5 iniciado solo con la correspondencia cita↔referencia (22/22 en ambos sentidos, sin huérfanas; anotado en la cabecera de B5). **Punto de retoma de B5**: formato de las citas en el texto contra `tesis/normas/guia_vancouver.tex` y Taller 2 p. 18-19 (corchetes vs. superíndice ya en H-12; falta: 28 de los 100 comandos llevan página o artículo (`[p.~n]`, `[pp.~a-b]`, `[art.~21]`, una con «pp.~21 y 26») y 72 no; decidir contra la guía si la cita de libro exige página; citas múltiples con `\autocites`; citas de cita); después la lista final entrada por entrada (`referencias.bib`, 22 entradas: campos obligatorios por tipo, ediciones más recientes de H-14, `alvarez_metodologia` sin año) y H-31 (Cook p. 98 y Hughes p. 221 en `tesis/respaldo_citas/verificado.json`) | **B5** desde el punto anotado; si sobra tiempo, **B6** con `tesis/main.tex:43-78`, `00_preliminares.tex` y el índice del Taller 1 p. 20 (ya transcrito en §2.4 de este archivo) |
