# Criterios editoriales de la tesis

Decisiones que gobiernan **todos** los capítulos de la versión que contiene este archivo
(hoy `capitulos_final3/`, compilada con `main_final3.tex` y XeLaTeX). Salen de la formulación metodológica
final (`tesis/alternativas/formulacion_final.pdf`) y de los patrones de la auditoría de
redacción de la v4 (`tesis/auditoria_v4/`). Quien edite un capítulo las aplica sin excepción.

## 1. Formulación (no se discute en ningún capítulo)

Formulación de final3 (observaciones del Ing. Miranda, 2026-09-25, adaptadas al contenido; el
diagnóstico de cada observación está en `tesis/observaciones_miranda/`). Los cuatro enunciados
formales se escriben **idénticos** dondequiera que se citen (Introducción, §2.1.3):

- **Problema**: ¿De qué manera la escasa transparencia del procedimiento de cálculo del
  software de análisis por elementos finitos podrá incidir en la baja trazabilidad y
  verificabilidad de ese procedimiento, en la gestión 2026?
- **Objetivo general**: Desarrollar un software educativo de elementos finitos para el análisis
  estructural, empleando el lenguaje de programación Python, debido a la escasa transparencia
  del procedimiento de cálculo del software de análisis, para mejorar la trazabilidad y la
  verificabilidad del procedimiento de cálculo.
- **Objetivos específicos**: tres, uno por capítulo, y **el título de cada capítulo es su
  objetivo sustantivado y completo** (verbo, objeto, cómo y para qué), aunque sea largo: así
  deriva Miranda el título de la tesis del objetivo general (lámina OG 6), y así lo pidió
  («tus objetivos definen tus capítulos»). **Fundamentar** → Cap. 1 «Fundamentación teórica
  del Método de los Elementos Finitos en elasticidad plana con elementos Q4 y Q9, y del estado
  del arte del software para su enseñanza, para fijar los requisitos de la herramienta»;
  **Desarrollar** → Cap. 2 «Desarrollo de EduFEM en Python —motor de cálculo, interfaz, módulos
  educativos y memoria de cálculo— para exponer el procedimiento de cálculo etapa por etapa
  sobre el modelo del usuario»; **Verificar y validar** → Cap. 3 «Verificación y validación de
  EduFEM mediante la medición de la cobertura de su procedimiento de cálculo y de la exactitud
  de su motor frente a soluciones exactas y referencias externas, para establecer si ese
  procedimiento es trazable y verificable». Si cambia un objetivo, cambia el título de su
  capítulo, y al revés.
  «Diagnosticar» **no** es objetivo: el análisis de los antecedentes forma parte de la
  fundamentación, y la palabra «diagnóstico» no se usa para él.
- **Hipótesis**: El desarrollo de EduFEM permitirá mejorar la transparencia del procedimiento
  de cálculo por elementos finitos —de caja negra a procedimiento a la vista—, elevando su
  trazabilidad y su verificabilidad. Se comprueba en dos cláusulas, (a) trazabilidad y
  (b) verificabilidad, enunciadas en §2.1.6; en la Introducción, el apartado «Hipótesis» lleva
  solo el enunciado.
- **Variable independiente (causa)**: la transparencia del procedimiento de cálculo, es decir,
  la exposición que el software hace de ese procedimiento, con sus magnitudes intermedias. Dos
  niveles: *caja negra* (datos y resultados) y *procedimiento a la vista* (cada etapa con sus
  magnitudes intermedias). No se la llama «grado»: la comparación es de presencia frente a
  ausencia (§2.1.2).
- **Variable dependiente (efecto)**: la trazabilidad y la verificabilidad del procedimiento de
  cálculo. *Trazabilidad*: cada resultado puede seguirse hacia atrás, etapa por etapa, hasta los
  datos del modelo. *Verificabilidad*: cada magnitud puede comprobarse contra un patrón
  independiente (cálculo manual, solución analítica, otro programa) y la comprobación da
  conforme dentro de una tolerancia fijada de antemano. Las dos variables son atributos de la
  unidad de análisis, el procedimiento de cálculo del software.
- **Variable interviniente (solución)**: EduFEM.
- **Preguntas de investigación**: dos, PI-1 (trazabilidad) y PI-2 (verificabilidad), en su
  propio apartado de la Introducción.
- **La universidad no figura en el problema, el objetivo general ni la hipótesis**: la tesis
  es general. La Carrera de Ingeniería Civil de la UATF aparece solo como destinataria en la
  delimitación institucional y como contexto de aplicación en §2.1.4.
- **Conclusiones en tríada**: una conclusión y una recomendación por capítulo, sin la fórmula
  «Objetivo específico N —verbo—»; las cifras van en los visuales (Figuras CR.1 y CR.2, Tabla
  CR.1), no repetidas en la prosa.
- **La tesis evalúa el software, no a sus usuarios.** Prohibido en todo el documento:
  - afirmar efectos sobre el estudiante (aprende, comprende mejor, mejora o forma su
    criterio, facilita el aprendizaje, «valor pedagógico» afirmado como hecho);
  - las expresiones «prueba de campo», «pendiente de medición», «en esta etapa», «esta
    etapa», «criterio logrado», «efecto sobre el estudiante»;
  - «validez de contenido» y «tabla de especificaciones» (ahora: **cobertura de contenido**
    y **tabla de cobertura de contenido**); «coherencia con los principios de aprendizaje»
    como cláusula de la hipótesis.
- **Permitido**: el estudiante como sujeto de verbos de posibilidad —«el estudiante puede
  seguir, comprobar, reproducir»—, porque describen lo que el medio ofrece. El software es
  el medio, nunca el sujeto de verbos de enseñanza («ejercita», «enseña», «hace comprender»).
- Lo que la literatura reporta sobre **otras** herramientas se atribuye a esa literatura, con
  su cita, y no se traslada a EduFEM.

## 2. Términos canónicos (lenguaje llano, contexto boliviano)

| Usar | En lugar de | Nota |
|---|---|---|
| **procedimiento de cálculo** | canal de cálculo, canal del MEF, flujo del MEF, proceso de cálculo | «Canal abierto» es un término de hidráulica: confunde a un tribunal de ingeniería civil. Primera aparición por capítulo con glosa: «la secuencia de etapas que va de las funciones de forma a la recuperación de tensiones» |
| **EduFEM** / **el software** / **la herramienta** | aplicación, programa (salvo «programas comerciales»), recurso (salvo «recursos educativos existentes»), artefacto | «Artefacto» aparece una sola vez, en §2.1.1, como término de la ciencia del diseño |
| **estudiante** | alumno | «usuario» solo al describir la interacción con la interfaz y en los manuales |
| **módulo educativo** | módulo interactivo | |
| **casos de estudio** | casos de referencia, problemas de referencia, banco de prueba | «referencia» se reserva para la fuente externa contra la que se contrasta |
| **comprobador de salud** | validador de salud | Es el nombre de la interfaz |
| **cobertura de contenido** | validez de contenido | |
| **tensión** | esfuerzo | Primera aparición del cuerpo: «tensión (esfuerzo)». Es el término de la interfaz |
| **tecnologías empleadas** | stack tecnológico | |
| **intercambio de datos** | interoperabilidad | admite «interoperabilidad» una vez, glosada |
| **verificación y validación** | V\&V sin presentar | La sigla se presenta una vez por capítulo |
| **lienzo** | — | Primera aparición: «el lienzo, es decir, el área gráfica donde se dibuja el modelo» |
| **memoria de cálculo** | Memoria de Cálculo | Siempre en minúscula; el rótulo del menú, si se cita, en `\textsf` |

- «Validación» designa, según §1.13, el contraste con referencias externas de exactitud
  conocida. No se usa para nada más.
- Notación: compacidad `q_C`; peso de cuadratura `w_g`; la matriz de extrapolación conserva
  **E** en negrita con advertencia expresa frente al módulo de elasticidad `E`; índice `j` en
  el sumatorio de ensamblaje. Coordenadas con punto y coma: `(48; 52)`.
- Términos en inglés: cursiva y glosa en la primera aparición, redonda después.
- Todo término técnico lleva, en su primera aparición, media línea de glosa en llano.

## 3. Estilo

- Oraciones de hasta unas 60 palabras. Un solo inciso entre rayas por oración. Toda
  enumeración de cuatro elementos o más sale a lista o tabla.
- Verbos por tipo de evidencia: **garantiza** solo para lo que se sigue por construcción o
  demostración (decirlo: «por construcción»); **valida** para el contraste con referencias
  externas; **se cumple / cumple** para un criterio numérico con umbral fijado de antemano;
  en lo demás, «respalda», «es coherente con», «reporta».
- Sujetos: «el autor adoptó / eligió» para decisiones de diseño experimental; «EduFEM
  resuelve / reporta / recupera» para lo que hace el software; «la literatura predice» para lo
  tomado de fuentes. Evitar el impersonal que oculta quién decidió.
- Cada cosa se explica una sola vez, en su lugar canónico, y en los demás se remite con
  `\autoref`: el recorrido del documento (Introducción, «Estructura del documento»); la
  integración de las normas con un punto de Gauss más (§1.13); la separación entre identidad
  del nodo e índice de GDL (§2.2.4); el esquema del solucionador (§2.2.5); la membrana de
  Cook y su valor de referencia (§3.5).
- Evitar los tics «encarna», «de forma X», «de manera X».
- Registro: español académico claro, sin regionalismos rioplatenses ni peninsulares
  («computadora», no «ordenador»; «hormigón armado»).

## 4. Higiene LaTeX

- Presentación (final3): se compila con XeLaTeX (`latexmk -xelatex main_final3.tex`); el texto
  va en Times New Roman de 12 puntos, justificado y con partición silábica; las fórmulas siguen
  en Latin Modern; las celdas `p{}` de las tablas se componen a la izquierda. Los símbolos
  Unicode de los listados de código se mapean en el preámbulo (`newunicodechar`).
- Las figuras y tablas de las Conclusiones se numeran «CR.n» (grupo con contadores propios en
  `05_conclusiones.tex`).
- No se cambia ninguna `\label`. Las remisiones internas van con `\autoref` a la sección,
  tabla o figura concreta.
- No se agregan claves de bibliografía fuera de las que ya cita el capítulo; ningún dato,
  página o cifra nuevos sin respaldo en el propio documento o en `tests/`.
- Las leyendas de figuras y tablas son enunciados que se leen solos: qué se muestra, sobre
  qué modelo y cómo leerlo.
- Coma decimal; porcentajes con `\,\%`; cifras idénticas a las de las tablas.
- Separador de miles: espacio fino `\,` a partir de cinco cifras (`33\,282`); las de cuatro van sin
  separar (`2178`). Los cortes adimensionales, con dos decimales (`0{,}30`).
- Transpuesta: `^{T}` en todo el documento.
- El valor de referencia de la membrana de Cook (23,96) se presenta como valor de uso
  extendido que el trabajo corrobora con su propia extrapolación de Richardson (≈ 23,97), sin
  atribuirlo a «la práctica de la comunidad». La razón de errores Q4/Q9 se enuncia como «más
  de diez veces» a 578 GDL; a 2178 GDL se declara no informativa, porque el error del Q9 ya no se
  distingue de la incertidumbre de la referencia (la ventaja del Q9 sigue siendo clara: no se dice
  «no significativa» ni «no apreciable»).
