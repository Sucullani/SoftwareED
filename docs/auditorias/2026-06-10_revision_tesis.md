# Informe II — Revisión profesional de la tesis

**Documento**: tesis/ (101 páginas compiladas, 11 capítulos/anexos) · **Fecha**: 2026-06-10
**Criterio**: revisión dura estilo jurado de tesis de ingeniería, alineada al canon del proyecto (skill `tesis-revisar`, CLAUDE.md). Se cruzó cada afirmación verificable contra el código real del repo, `docs/vyv/datos/*.csv` y los scripts `tests/vv_*`. **No se modificó ningún archivo** — todas las correcciones quedan propuestas para decisión del autor.

## Veredicto general

La tesis está **claramente por encima del promedio de un trabajo de grado**, y eso hay que decirlo primero: la formulación del MEF es esencialmente correcta y completa, el cruce bibliográfico es perfecto (0 citas huérfanas en ambos sentidos), la terminología española es disciplinada (0 violaciones del canon GDL/MEF en prosa), no hay una sola muletilla de IA en todo el documento, y —lo más infrecuente— casi cada afirmación sobre el software y cada cifra del capítulo de resultados es **trazable y fue verificada bit a bit** contra los scripts y datos archivados. El capítulo 04 es un ejercicio de V&V genuino, no una colección de capturas.

Dicho esto, un jurado exigente NO la dejaría pasar como está, por cinco razones concretas: (1) hay un **error matemático real en la ecuación central del marco teórico** — el Jacobiano impreso es la transpuesta del producto al que se lo iguala, y contradice la regla de la cadena enunciada tres páginas después; en una tesis cuyo argumento de venta es "exponer cada matriz con rigor", es una herida autoinfligida. (2) La **portada tiene faltas de ortografía en el nombre de la universidad y en el título** ("Tomas" sin tilde, "ANALISIS", "PROGRAMACION") — lo primero que el tribunal ve. (3) La **hipótesis es circular** ("es factible construir…" se verifica por haberlo construido) y el término "variable independiente" significa **dos cosas distintas** en el mismo capítulo metodológico. (4) Los anexos contienen **dos descripciones de comportamiento del software directamente falsas** (el fallback sin pdflatex y la conversión Q9 del importador DXF) que cualquier lector que instale el programa detecta en cinco minutos — y eso erosiona la credibilidad ganada con tanto esfuerzo en el resto. (5) El anexo de la memoria de cálculo dice "**reproduce**" un documento que en realidad condensa. Todo es corregible en **días, no meses**: el esqueleto es bueno; falta el pulido de precisión que el propio documento le exige al lector.

| Categoría | Mayores | Menores |
|---|---|---|
| Rigor matemático (marco teórico) | 2 | 6 |
| Metodología (hipótesis, variables) | 2 | 4 |
| Portada y preliminares | 2 | 4 |
| Alineación tesis↔software (anexos) | 3 | 3 |
| Resultados y conclusiones | 0 | 8 |
| Citas y bibliografía | 0 | 6 |
| Higiene LaTeX | 1 | 7 |
| Terminología y claridad | 1 | 9 |

<<<PAGEBREAK>>>

## 1. Rigor matemático y técnico (cap. 02)

| Ubicación | Sev. | Hallazgo | Corrección propuesta |
|---|---|---|---|
| 02_marco_teorico.tex:148-156 | **MAYOR** | La ecuación del Jacobiano es internamente inconsistente: la matriz exhibida (filas x,y / columnas ξ,η) es la **transpuesta** del producto ∂N·Xe al que se la iguala. La relación física↔natural de la línea 209 (con J⁻¹) solo vale con la convención de Bathe — que es además la que implementa el código (`compute_jacobian: J = dN @ node_coords`). Con la matriz tal como está impresa, correspondería J^(-T). Un tribunal con Bathe en la mano lo detecta en 2 minutos. | Cambiar la matriz exhibida a filas ξ,η (∂x/∂ξ, ∂y/∂ξ / ∂x/∂η, ∂y/∂η) y revisar el efecto dominó en eq:scaled-jacobian (las "columnas de J" pasan a ser filas). |
| 02:373 + 02b:98 | **MAYOR** | Contradicción interna: "cuadratura de orden p+1 —un orden por encima del usado para la rigidez—". Con p=1 (Q4, según la propia Nomenclatura), p+1=2 es el MISMO orden que la rigidez 2×2, no uno por encima. El código usa 3×3 (Q4) y 4×4 (Q9). | Escribir la regla explícita: "un punto más por dirección que la rigidez (3×3 para Q4, 4×4 para Q9)". |
| 02:285-293 | menor | σVM = √(σ1²−σ1σ2+σ2²) solo es la von Mises completa en **tensión plana**; en deformación plana σz = ν(σx+σy) ≠ 0 y la equivalente 3D difiere. Se presenta sin caveat en un capítulo que trata ambas idealizaciones. | Añadir el caveat y verificar/alinear con lo que `fem/stress.py` calcula realmente. |
| 02:235 | menor | "la integral carece de primitiva elemental" — falso en general (las racionales sí admiten primitivas). El argumento correcto es que el integrando racional no es polinómico y ninguna regla de Gauss finita lo integra exactamente. | Reformular en términos de exactitud de cuadratura. |
| 02:259 | menor | Mezcla de casos en fuerzas equivalentes: la fórmula L/6(2qs+qe) es del caso lineal, no "constante"; y la distribución Q9 "L/6, 4L/6, L/6" omite q (dimensionalmente es una longitud). | "carga linealmente variable" + "qL/6, 4qL/6, qL/6". |
| 02:344-347 | menor | eq:scaled-jacobian con subíndice g sugiere evaluación en puntos de Gauss; la implementación real (Verdict, `scaled_jacobian_corners`) evalúa en los 4 vértices (sin θi). | Escribir la métrica como la define Verdict, consistente con el código. |
| 02:356 | menor | Sobreclaim citado: atribuye a Verdict el corte "buena" (0,80/0,50), que es convención de la UI de EduFEM; de Verdict son solo los de admisibilidad (0,50/0,25). | Separar explícitamente qué umbral viene de cada fuente. |
| 02:11-37 | menor | Estado del arte con afirmaciones sin cita propia: VisualFEA/FEniCS/CALFEM sin referencia; el idioma "en inglés" de ED-Elas2D no está verificado (programa de la UPC — verificar contra el paper o suavizar); ED-Beams/ED-Frames citados con la referencia de un tercero. | Añadir entradas bib o suavizar los atributos no verificables. |

## 2. Metodología e hipótesis (caps. 01, 02b)

| Ubicación | Sev. | Hallazgo | Corrección propuesta |
|---|---|---|---|
| 02b:14-31 vs 02b:68 | **MAYOR** | "Variable independiente" designa **dos cosas distintas** en el mismo capítulo: en tab:variables es "definición del modelo + discretización (Q4/Q9, h)"; en la Hipótesis pasa a ser "la transparencia e interactividad del canal". La matriz de consistencia usa la primera acepción y la hipótesis la segunda. Es el flanco más débil ante un tribunal formado en el esquema problema-objeto-campo-hipótesis. | Separar léxicamente: variables del experimento numérico (mantener VI/VD) vs. elementos de la hipótesis de diseño ("aporte", "atributos del artefacto / efecto esperado"), con una frase puente explícita. |
| 01:42 + 02b:66-68 | **MAYOR** | Hipótesis circular/infalsable: "es factible construir un software que…" se cumple por el solo hecho de haberlo construido. El texto lo confiesa, pero confesar una debilidad no la corrige. | Reformular con criterios de aceptación a priori medibles que YA existen en el trabajo: tasas teóricas de convergencia dentro de tolerancia, error < 0,3 % vs Timoshenko/SAP2000, evidencia del bloqueo por cortante del Q4. La factibilidad pasa a ser conclusión, no hipótesis. |
| 01:54 vs 02b:4 | menor | La clasificación metodológica (propositivo/aplicada-tecnológica/cuantitativo/descriptivo-comparativo) se repite casi verbatim en ambos capítulos — y 02b:9 reconoce el solape… y aun así duplica. | Dejarla en un solo lugar con remisión. |
| 02b:24-25 | menor | Columna "Instrumento" floja: "Configuración del modelo" no es un instrumento de medición (repetido en 2 filas). | "Archivo de proyecto .edufem / guion de generación de malla". |
| 02b:1 | menor | Título "Diseño e implementación del modelo **a desarrollar**" — futuro de anteproyecto en una tesis terminada. | "Diseño metodológico e implementación de EduFEM". |
| 02b:73 | menor | "benchmark histórico" convive con "caso de referencia" y "banco clásico" — tres nombres para lo mismo. | Unificar en "caso de referencia". |

**En lo positivo**: la matriz de consistencia, los sistemas de control/repetición/validación y la justificación del 5.º objetivo instrumental son concretos y trazables a los guiones `tests/vv_*` — muy por encima del relleno habitual en esta sección.

<<<PAGEBREAK>>>

## 3. Portada, preliminares y resumen

| Ubicación | Sev. | Hallazgo | Corrección propuesta |
|---|---|---|---|
| main.tex:15 | **MAYOR** | "Universidad Autónoma «**Tomas** Frías»" — falta la tilde en el nombre de la propia universidad, en la portada. | "Tomás Frías". |
| portada/portada.tex:27-29 | **MAYOR** | Título en mayúsculas sin tildes: "ANALISIS", "PROGRAMACION" (la RAE exige tilde en mayúsculas). | "ANÁLISIS", "PROGRAMACIÓN". |
| main.tex:35-36 | menor | `00_preliminares` está **comentado**: la versión que compila hoy no incluye la Declaración de originalidad (Art. 9 del reglamento citado en el propio archivo) y dedicatoria/agradecimientos siguen con placeholder ">>> PERSONALIZAR <<<". | Checklist de versión final: descomentar y personalizar. |
| 00_resumen.tex:4 | menor | El resumen contiene 5 citas — la convención (y la mayoría de reglamentos) pide resumen autocontenido sin referencias. Además "errores inferiores al 0,2633 %": cuatro cifras significativas en una cota es absurdo (0,2633 % es EL error medido, no una cota). | Quitar las citas; "del 0,26 %" o "inferiores al 0,3 %". Partir las oraciones de 50+ palabras. Verificar si el reglamento exige Abstract en inglés. |
| 00_resumen.tex:6 | menor | 10 palabras clave (el doble de lo habitual), varias redundantes entre sí. | Reducir a 5-6. |
| 00_preliminares.tex:22-29 | menor | La Dedicatoria no tiene `\addcontentsline` mientras Declaración y Agradecimientos sí — inconsistencia en el índice. | Homogeneizar según reglamento. |
| portada/portada.tex:34 | menor | "Para optar: Título de Licenciatura…" — la fórmula usual es "PARA OPTAR AL TÍTULO DE…". | Cotejar con la carátula oficial. |

## 4. Alineación tesis ↔ software real (caps. 03, 06, 07)

**Lo que está bien — y es mucho**: los 8 módulos M0–M7 existen tal como se describen; la arquitectura por capas, la pureza de `fem/`, el ensamblaje COO→CSR, el solucionador y el flag RCM coinciden; la tabla de chequeos de salud del anexo es 1:1 con `model_health.py` (verificado código por código); las tablas de formatos coinciden columna a columna con `model_io.py`/`dxf_io.py`; el ejemplo canónico del anexo G reproduce `example_library.py` y el motor. Este nivel de trazabilidad es infrecuente y es el punto más fuerte de la tesis. Pero hay tres afirmaciones **falsas** sobre el comportamiento del software:

| Ubicación | Sev. | Hallazgo | Corrección propuesta |
|---|---|---|---|
| 06_anexos.tex:14,44 | **MAYOR** | "sin LaTeX la aplicación funciona igual y las fórmulas se rinden mediante un mecanismo alternativo": FALSO para la memoria — sin pdflatex NO se genera ningún PDF (`PdflatexNotFoundError` + diálogo de descarga). El fallback mathtext aplica solo a fórmulas en pantalla. | Reescribir distinguiendo fórmulas in-app (fallback) de Memoria PDF (pdflatex obligatorio). |
| 07_anexo_memoria.tex:14 | **MAYOR** | "Este anexo **reproduce** la Memoria de Cálculo que EduFEM genera" — no: la memoria real tiene 9 capítulos/2 estilos (así la describe el propio cap. 03); el anexo es una síntesis de 3 secciones. Agrava: existe `tesis/figuras/generar_memoria_anexo.py`, escrito para embeber el PDF real vía \includepdf, y no se usa. | Embeber el PDF real (como ya se hace con el anexo SAP2000) o reformular: "presenta en forma condensada… todos los valores son salida bit-exacta del motor". |
| 06_anexos.tex:718 | **MAYOR** | "el resultado de la importación DXF es **siempre** una malla Q4, que puede convertirse después a Q9 desde el menú" — en proyecto Q9, el importador expande automáticamente (`q9_auto_expanded` vía `auto_expand_if_q9`). | Añadir la salvedad del proyecto Q9. |
| 03:30 (tab:stack) | menor | `manim` listado en el stack sin aclarar que es herramienta de desarrollo (videos distribuidos prerenderizados; no está en requirements.txt). | Nota en la celda. |
| 06:451-486 | menor | La guía de reproducibilidad omite `test_noncontiguous_ids`, cuyo resultado SÍ se reporta en 04:81 (verificado: existe, mismos IDs y tolerancia). | Agregar la fila. |
| 03:94 | menor | Contradicción interna: "marca cuatro vértices en sentido antihorario… y si la orientación es horaria, la corrige automáticamente" — el código acepta cualquier orden (auto-CCW). | "marca cuatro vértices en cualquier orden; la orientación se fuerza a antihoraria". |

## 5. Resultados y conclusiones (caps. 04, 05)

**Resultados reales y verificados**: cada cifra de las tablas (MMS, Cook, Timoshenko, tiempos) coincide con `docs/vyv/datos/*.csv` y los parámetros de cada benchmark con los scripts. La aritmética interna (GDL, nodos, memoria densa) es correcta en todos los casos recalculados. El cruce objetivo↔conclusión está bien resuelto: los 5 objetivos tienen su párrafo en orden, ninguna conclusión excede lo demostrado y el impacto pedagógico se declara no contrastado dos veces (honestidad correcta).

| Ubicación | Sev. | Hallazgo | Corrección propuesta |
|---|---|---|---|
| 04:85 | menor | "E = 217 370 kgf/cm² (≈ 21,33 GPa)" — la conversión da **21,32** GPa; el propio `vv_timoshenko.py:10` dice 21.32. Única deriva numérica tesis↔código encontrada. | 21,32 GPa. |
| 05:40 | menor | El claim "Cholesky es más rápida para estas matrices" citado con los papers de SciPy/NumPy, que no establecen eso — cita decorativa mal dirigida. | Citar Golub & Van Loan o Davis (Direct Methods for Sparse Linear Systems). |
| 04:246 | menor | Las preguntas se responden en orden PI-1, PI-3, PI-2 sin justificación. | Reordenar o justificar. |
| 04:54 · 06:533 | menor | Registro autoevaluativo: "el análisis es concluyente", "la concordancia es nuevamente excelente" — el jurado decide qué es concluyente. | Sustituir por afirmaciones cuantificadas. |
| 04:5 | menor | Oración-río de apertura que enumera dos veces el recorrido del capítulo. | Fusionar. |
| 04:221 | menor | "procesador Intel (Ivy Bridge, circa 2012)" — dar modelo concreto y RAM para reproducibilidad. | Completar identificación del equipo. |
| 06:483 + 04:75 | menor | tab:vyv-repro remite el ciclo Q4→Q9→Q4 a `sec:medicion`, pero el resultado vive en "Consistencia interna" (04:75), que no tiene label — referencia que compila pero apunta mal. | Crear `sec:consistencia-interna` y corregir. |
| 05:16 | menor | "(shear-locking)" sin cursiva; cap. 04 lo escribe en `\emph`. | Unificar. |

<<<PAGEBREAK>>>

## 6. Citas Vancouver y bibliografía

**Cruce de claves: perfecto.** Las 21 entradas de referencias.bib están todas citadas y las 21 claves citadas están todas definidas — 0 huérfanas en ambos sentidos. Sin "% CITA PENDIENTE". La artillería teórica es la correcta (Zienkiewicz, Bathe, Cook, Hughes, Oñate, Strang-Fix, Roache, Oberkampf, Salari-Knupp) y está donde debe estar.

| Ubicación | Sev. | Hallazgo | Corrección propuesta |
|---|---|---|---|
| referencias.bib (DOIs) | menor | DOIs no verificados: Cook 1974 (10.1061/JSDEAG.0003877), Lee 2015 ×2 (10.1002/cae.21586, cae.21659 — confirmar también el nombre "Joo-Yong"), Pérez-Santiago 2023 (10.1002/cae.22627). La skill del proyecto prohíbe DOIs inventados. | Resolver cada DOI en doi.org antes de la versión final. |
| referencias.bib:205-212 | menor | strang2008analysis: única @book sin ISBN. | Añadir ISBN verificado (978-0-9802327-0-7). |
| referencias.bib:142-148 | menor | csi2017sap2000 sin versión del manual/software — poco trazable y relevante para la validación. | Agregar la versión usada, consistente con el anexo. |

## 7. Higiene LaTeX

**Limpio en lo estructural**: 0 labels duplicados, 0 \autoref/\ref rotos, todas las figuras referenciadas existen, los entornos math están bien formados y el documento compila (101 páginas).

| Ubicación | Sev. | Hallazgo | Corrección propuesta |
|---|---|---|---|
| 02b:7 + 01:56 | **mayor** | `\label{cap:metodologia}` sobre una `\section`: viola la convención de prefijos y "en el \autoref{...}" imprime "en el **sección** 2.1" — error de concordancia visible en el PDF. | Renombrar a `sec:metodologia` + "en la \autoref{...}". |
| 02:49,58,65,146,283,304 | menor | `\autoref{eq:...}` sin artículo: "multiplicando Ecuación 2.1" (mayúscula a mitad de oración). | "la \autoref{...}" o `\eqref` con "la ecuación~(…)". |
| preambulo.tex:26 | menor | Warning fancyhdr `\headheight too small` repetido en decenas de páginas. | `headheight=14.5pt` en geometry. |
| compile_run.txt:211 | menor | `destination with the same identifier (page.1)` — la portada colisiona con la página 1 del cuerpo al reiniciar la numeración. | `\hypersetup{pageanchor=false}` en la portada. |
| compile_run.txt:139 | menor | `Font shape T1/lmr/bx/sc undefined` — versalitas en negrita caen a sustituto silencioso. | Localizar el `\textsc`+`\bfseries` y relajar una demanda. |
| 06:602 | menor | `\includegraphics{figuras/fig_cook_deformed}` con prefijo redundante (graphicspath activo) — frágil. | Quitar el prefijo. |
| 07:176 | menor | La matriz de extrapolación se denota **E** en un anexo donde E es el módulo de elasticidad tres líneas más arriba — colisión notacional. | Renombrar (T_ext o P). |
| 00b_nomenclatura.tex:108-112 | menor | Comentario que justifica `\setcounter{table}{0}` con un comportamiento de longtable que no existe. | Borrar el bloque o corregir el comentario. |

## 8. Terminología y claridad

**Terminología MEF: impecable** — 0 hits del grep canónico en prosa en TODA la tesis; GDL/MEF/tensión/deformación/malla/restricción consistentes; extranjerismos (*shear-locking*, *hourglass*, *stretch*, *fill-in*) en cursiva con gloss español. **Muletillas de IA: 0 ocurrencias** en todo el documento. Voz impersonal consistente.

| Ubicación | Sev. | Hallazgo | Corrección propuesta |
|---|---|---|---|
| global (01:48, 04:193 vs resto) | **mayor** | El concepto central de la tesis tiene **dos nombres**: "canal de cálculo" (21+16 usos) vs "cadena de cálculo" (PI-2 de la Introducción, caption de tab:comparativa, 02b:59, 04:193). Además "canal" como traducción de pipeline es atípica (evoca hidráulica). | Elegir UNO (sugerencia: "cadena de cálculo", más natural en español técnico), unificar globalmente y definirlo en su primera aparición. |
| 01:10 vs 02:9 | mayor | Duplicación casi verbatim del planteamiento (caja negra / "diagnosticar resultados anómalos, evaluar la calidad de una malla") entre Introducción y Antecedentes — el argumento se cuenta tres veces (resumen, intro, marco). | Planteamiento completo solo en la Introducción; Antecedentes lo da por sentado en una frase con remisión. |
| 01:12-14 | menor | La pregunta de investigación se formula dos veces seguidas con redacciones casi idénticas. | Fusionar en una sola formulación. |
| 01:64-66 | menor | "Estructura del documento" enumera 5 anexos; la tesis tiene 7 (omite SAP2000 y memoria). | Completar. |
| 01:66 | menor | "el stack tecnológico" — anglicismo en prosa (también como título de sección en cap. 03). | "las tecnologías empleadas" (o stack en cursiva 1 vez). |
| 01:37 | menor | "soportar interoperabilidad" — calco de to support. | "ofrecer interoperabilidad de datos (DXF, CSV)". |
| 02:27-32 | menor | Concordancias en tab:comparativa: "Cálculo paso a paso: Alta/Media/Baja" (masculino) y "Licencia: Académico" (femenina). | "Exposición paso a paso" / "Académica". |
| 02:37 | menor | Oración-párrafo de ~110 palabras con tres niveles de subordinación. | Partir en tres oraciones. |
| 02:139 | menor | Caption redundante: "Elementos isoparamétricos… y el mapeo isoparamétrico…". | Simplificar. |

<<<PAGEBREAK>>>

## Top-15 consolidado (en orden de urgencia)

1. **02_marco_teorico.tex:148-156** — corregir la matriz del Jacobiano (transpuesta inconsistente con ∂N·Xe y con eq:fisica-natural); revisar efecto dominó en eq:scaled-jacobian.
2. **main.tex:15 + portada:27-29** — tildes de portada: "Tomás Frías", "ANÁLISIS", "PROGRAMACIÓN".
3. **02b:14-31 vs 02b:68** — resolver la doble definición de "variable independiente" con léxico separado.
4. **01:42 + 02b:66-68** — reformular la hipótesis circular con criterios de aceptación medibles a priori (las cifras ya existen en el propio trabajo).
5. **06_anexos.tex:14,44** — corregir la afirmación falsa del fallback sin pdflatex (no hay Memoria PDF sin LaTeX).
6. **07_anexo_memoria.tex:14** — "reproduce" → embeber el PDF real (el script `generar_memoria_anexo.py` ya existe) o reformular a "presenta en forma condensada".
7. **06_anexos.tex:718** — importación DXF en proyecto Q9: la expansión es automática, no "desde el menú".
8. **02:373 + 02b:98** — corregir "cuadratura de orden p+1" (contradice su propia definición de p): escribir 3×3 Q4 / 4×4 Q9.
9. **02b:7 + 01:56** — `cap:metodologia` → `sec:metodologia` y arreglar "en el sección" (visible en el PDF).
10. **Global** — unificar "canal de cálculo" vs "cadena de cálculo" (es el concepto central; no puede tener dos nombres).
11. **04:85** — 21,33 → 21,32 GPa (única deriva numérica tesis↔código).
12. **01:10 vs 02:9** — eliminar la duplicación verbatim del planteamiento entre Introducción y Antecedentes.
13. **02:285-293** — caveat de von Mises en deformación plana (σz ≠ 0) y alinear con `fem/stress.py`.
14. **00_resumen.tex** — quitar las 5 citas, corregir "0,2633 %" → "0,26 %", reducir palabras clave a 5-6.
15. **referencias.bib** — verificar los 4 DOIs no confirmados + ISBN de Strang + versión de SAP2000; checklist final: descomentar preliminares y personalizar placeholders.

## Fortalezas que conviene defender en el tribunal

- **Trazabilidad total**: cada cifra del cap. 04 se reproduce desde scripts versionados con datos archivados (`docs/vyv/`); la tabla de salud, los formatos y los listados son espejo verificado del código.
- **V&V genuina**: MMS con tasas asintóticas, dos validaciones independientes (analítica + SAP2000), benchmark de escalabilidad con hardware declarado, y honestidad metodológica explícita (nota 23,95/23,96; impacto pedagógico declarado como no medido).
- **Bibliografía sana**: 0 citas huérfanas, artillería teórica correcta y donde corresponde.
- **Disciplina lingüística**: terminología MEF española canónica sin fugas, sin muletillas de IA, voz impersonal estable.
- **Diseño metodológico con contenido real**: matriz de consistencia trazable a los guiones de V&V — muy por encima del relleno habitual.
