# Criterios editoriales de la versión final (`main_final.tex`)

Decisiones que gobiernan **todo** `capitulos_final/`. Salen de la formulación metodológica
final (`tesis/alternativas/formulacion_final.pdf`) y de los patrones de la auditoría de
redacción de la v4 (`tesis/auditoria_v4/`). Quien edite un capítulo las aplica sin excepción.

## 1. Formulación (no se discute en ningún capítulo)

- **Problema**: ¿de qué manera el uso del software de análisis estructural como caja negra
  podrá incidir en la baja trazabilidad y verificabilidad del análisis por el Método de los
  Elementos Finitos en elasticidad plana, en la Carrera de Ingeniería Civil de la Universidad
  Autónoma Tomás Frías, en la gestión 2026?
- **Variable independiente (causa)**: la forma en que el software expone el procedimiento de
  cálculo. Dos niveles: *caja negra* (datos y resultados) y *procedimiento a la vista* (cada
  etapa con sus magnitudes intermedias).
- **Variable dependiente (efecto)**: la trazabilidad y la verificabilidad del análisis.
  *Trazabilidad*: cada resultado puede seguirse hacia atrás, etapa por etapa, hasta los datos
  del modelo. *Verificabilidad*: cada magnitud puede comprobarse contra un patrón independiente
  (cálculo manual, solución analítica, otro programa) y la comprobación da conforme dentro de
  una tolerancia fijada de antemano.
- **Variable interviniente (solución)**: EduFEM.
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
