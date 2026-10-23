# Criterios editoriales de la tesis

Decisiones que gobiernan **todos** los capítulos de la versión que contiene este archivo
(hoy `capitulos_final4/`, compilada con `main_final4.tex` y XeLaTeX). Salen de la formulación metodológica
final (`tesis/alternativas/formulacion_final.pdf`) y de los patrones de la auditoría de
redacción de la v4 (`tesis/archivo/v4/auditoria_v4/`). Quien edite un capítulo las aplica sin excepción.

## 1. Formulación (no se discute en ningún capítulo)

Formulación de final3 (observaciones del Ing. Miranda, 2026-09-25, adaptadas al contenido; el
diagnóstico de cada observación está en `tesis/observaciones_miranda/`), con la **hipótesis que
el tribunal dictó tras la defensa de borrador** (final4, 2026-10-20). Los cuatro enunciados
formales se escriben **idénticos** dondequiera que se citen (la hipótesis: Introducción, §2.1.3
y §3.8; las Conclusiones no la copian, para no repetirla: la Figura CR.1 nombra sus partes sin
reproducir el enunciado):

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
- **Hipótesis** (texto del tribunal, con «dada»; no «debido a», que presentaría la escasa
  transparencia como causa de la mejora): Bajo la aplicación de un método de diseño de software
  educativo, el desarrollo de EduFEM permitirá mejorar la trazabilidad y la verificabilidad del
  análisis por el Método de los Elementos Finitos en elasticidad plana, dada la escasa
  transparencia con que el software expone su procedimiento de cálculo. «Bajo la aplicación de
  un método…» es el molde de la lámina de hipótesis de Miranda, **no** la «hipótesis de diseño»
  condicional de v1/v2. En la Introducción, el apartado «Hipótesis» lleva solo el enunciado.
- **Contraste, en cuatro partes y en el orden del enunciado** (§2.1.6, §3.8): **condición** (el
  método de diseño aplicado: `tab:dsrm`, `tab:principios`), **intervención** (el desarrollo de
  EduFEM: la variable independiente a la vista), **efecto** (la variable dependiente, en dos
  cláusulas, (a) trazabilidad y (b) verificabilidad, con los criterios de `tab:criterios`) y
  **antecedente** (la variable independiente en su nivel de partida: `tab:comparativa`). Las
  tres premisas se declaran **respaldadas**; «se cumple» queda para el efecto. **Regla de
  decisión** conjuntiva: comprobada si se respaldan las premisas y se cumplen las dos cláusulas;
  parcial si se cumple una; no comprobada si ninguna; si una premisa no se respalda, el efecto
  no se juzga. No se agregan criterios a `tab:criterios`
  después de las corridas. La tabla de partida y logro vive en §3.8
  (`tab:componentes-hipotesis`) y la Figura CR.1 la resume: no se repite como tabla en las
  Conclusiones.
- **Variable independiente (causa)**: la transparencia del procedimiento de cálculo, es decir,
  la exposición que el software hace de ese procedimiento, con sus magnitudes intermedias. Dos
  niveles: *caja negra* (datos y resultados), que es el **de partida** que la hipótesis da por
  establecido («dada…»), y *procedimiento a la vista* (cada etapa con sus magnitudes
  intermedias). No se la llama «grado»: la comparación es de presencia frente a ausencia
  (§2.1.2). En la hipótesis, «el software» de ese tramo es el software de análisis de uso
  corriente, no EduFEM: la Introducción lo glosa.
- **Variable dependiente (efecto)**: la trazabilidad y la verificabilidad del procedimiento de
  cálculo. *Trazabilidad*: cada resultado puede seguirse hacia atrás, etapa por etapa, hasta los
  datos del modelo. *Verificabilidad*: cada magnitud puede comprobarse contra un patrón
  independiente (cálculo manual, solución analítica, otro programa) y la comprobación da
  conforme dentro de una tolerancia explícita, que no depende del valor observado. Dos niveles:
  *baja* (el análisis solo puede seguirse y comprobarse en sus datos y sus resultados finales)
  y *alta* (cada resultado puede seguirse hasta sus datos y cada magnitud puede comprobarse;
  siempre en modo posible, como la definición); «mejorar» es pasar de una a otra, y la partida
  se documenta, no se mide. La hipótesis las atribuye «al análisis por el MEF en elasticidad
  plana» (se escribe «atribuye», no «predica», que es un tecnicismo): el objeto de estudio, que se
  realiza mediante el procedimiento de cálculo. «Análisis» y «procedimiento de cálculo» nombran
  la misma unidad; el problema y el objetivo general **no** se cambiaron (decisión del autor,
  2026-10-20). Las dos variables son atributos de la unidad de análisis, el procedimiento de
  cálculo del software.
- **Variable interviniente (solución)**: EduFEM, desarrollado bajo un método de diseño de
  software educativo: la ciencia del diseño (§2.1.1, «El método de diseño de la hipótesis»),
  con requisitos tomados de los antecedentes y decisiones trazadas a los principios de §1.2.
  Sin bibliografía nueva.
- **Preguntas de investigación**: dos, PI-1 (trazabilidad) y PI-2 (verificabilidad), en su
  propio apartado de la Introducción.
- **La universidad no figura en el problema, el objetivo general ni la hipótesis**: la tesis
  es general. La Carrera de Ingeniería Civil de la UATF aparece solo como destinataria en la
  delimitación institucional y como contexto de aplicación en §2.1.4.
- **Conclusiones en tríada** (final4, tribunal): una conclusión y sus recomendaciones por
  capítulo, **sin** los rótulos «Conclusión N» ni «Recomendación N» y sin la fórmula «Objetivo
  específico N —verbo—»: cada conclusión es un párrafo que abre con su capítulo y con la
  fórmula de conclusión, una sola vez por párrafo («De la fundamentación teórica (Capítulo 1)
  se concluye que…»; decisión del autor, 2026-10-20). La apertura y el párrafo de debilidades
  no la llevan. Orden: apertura con el objetivo general y la respuesta
  al problema; el veredicto de la hipótesis, sin copiar su enunciado; Figura CR.1 (la hipótesis, parte por
  parte, sin su enunciado literal); los tres párrafos; Figura CR.2 (margen de los criterios); inconveniente y debilidades
  (Taller 5: «señalar falencias o debilidades»), con remisión a §3.7.5; Recomendaciones en tres
  grupos con entrada en negrita; Tabla CR.1 (la tríada, con flechas). **No** vuelven las
  secciones «Aportes del trabajo» ni «Limitaciones» (redundantes con la Introducción, según el
  tribunal): el aporte va en una oración en los párrafos de los Cap. 2 y 3, y las limitaciones
  descubiertas, en §3.7.5 (`sec:limitaciones-observadas`). Las cifras van en los visuales, no
  repetidas en la prosa.
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
| **ejemplo guía** | ejemplo canónico | El modelo de nueve nodos y cuatro elementos Q4 (Anexo G). Primera aparición: «un modelo de nueve nodos y cuatro elementos Q4 que acompaña al lector por todo el procedimiento». El menú del software lo rotula «Cuadrado de validación»: la tesis solo cita ese rótulo, en `\textsf`, donde el manual dice cómo cargarlo (Anexo B), y no lo usa como nombre, porque este ejemplo no mide exactitud (final4, pedido del tribunal de evitar términos muy técnicos) |
| **el orden del cálculo** | orden canónico | Mismo motivo |

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
  externas; **se cumple / cumple** para un criterio con umbral explícito; en lo demás,
  «respalda», «es coherente con», «reporta». No se escribe que los criterios se fijaron «de
  antemano» (hallazgo H4): ningún umbral numérico precede a las primeras corridas (25-05,
  `ed852bf`); los de la flecha, Cook y las tasas entraron a los guiones el 01-06 (`c8885e0`) y
  los de σx y del equilibrio el 16-09 (`4a60eb2`), y §2.1.6 lo declara.
- Cobertura de la deformación plana (hallazgo H1): las soluciones manufacturadas usan un campo
  con traza de la deformación y distorsión angular nulas, así que solo ven $D_{11}-D_{12}$, igual
  en los dos estados planos. No se escribe que «cubren los dos estados planos» ni que comprueban
  la matriz constitutiva. $D_{11}$ y $D_{12}$ de la deformación plana los acota, junto con ellas,
  la prueba de deformación uniaxial de `tests/test_vv_extensions.py` (Tabla D.1); su $D_{33}$ no
  tiene prueba propia, y la tesis lo declara (§2.1.4, §3.2, §3.7.5).
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

- Presentación: se compila con XeLaTeX (`latexmk -xelatex main_final4.tex`); el texto
  va en Times New Roman de 12 puntos, justificado y con partición silábica; las fórmulas siguen
  en Latin Modern; las celdas `p{}` de las tablas se componen a la izquierda. Los símbolos
  Unicode de los listados de código se mapean en el preámbulo (`newunicodechar`).
- Rótulos (final4, tribunal): número en negrita y **título en redonda** (`textfont=up`). Los
  títulos internos de las tablas (grupos de filas) van en negrita, nunca en cursiva; «Nota.» y
  «Palabras clave:» siguen en cursiva (APA: no son títulos). La cursiva queda para términos en
  otro idioma y variables, también dentro de un rótulo.
- Pie de página (final4, tribunal): número abajo a la derecha, nombre corto del capítulo a la
  izquierda y filete fino encima; la hoja de apertura de capítulo lleva solo el número. Los tres
  capítulos cuyo título es el objetivo completo fijan su nombre corto con `\chaptermark{...}`
  justo después de su `\label`. Notas al pie fijas al fondo (`footmisc [bottom,hang]`).
- Figuras generadas (`tesis/figuras/generar_figuras_formulacion.py --version final4`): PDF
  vectorial al ancho de la caja (15,92 cm), Times New Roman, letra de 8 pt o más, sin títulos ni
  cursivas dentro de la imagen; las cifras salen solo del guion, que las comprueba contra
  `tab:veredicto`. Se incluyen con su extensión (`fig_x.pdf`).
- Las figuras y tablas de las Conclusiones se numeran «CR.n» (grupo con contadores propios en
  `05_conclusiones.tex`).
- No se cambia ninguna `\label` (agregar una nueva sí se permite). Las remisiones internas van
  con `\autoref` a la sección, tabla o figura concreta; a las secciones sin número de la
  Introducción y las Conclusiones se remite por su nombre en cursiva (*Alcance y limitaciones*).
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
