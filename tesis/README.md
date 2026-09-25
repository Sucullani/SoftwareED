# Tesis — EduFEM

Fuente LaTeX de la tesis sobre **EduFEM** (GUI educativa de elementos finitos 2D).
Idioma: español (babel).

**Versión vigente: `main_final3.tex` + `capitulos_final3/`** (2026-09-25, 189 páginas): aplica
las observaciones del Ing. Miranda (tribunal), adaptadas al contenido: formulación en el molde
del tribunal, tres objetivos específicos (uno por capítulo), Introducción por apartados,
Conclusiones en tríada con figuras y tabla, y el texto en Times New Roman 12 justificado.
**Se compila con XeLaTeX**: `latexmk -xelatex main_final3.tex` desde esta carpeta. Diagnóstico
de cada observación: [observaciones_miranda/](observaciones_miranda/README.md). Cómo se numeran
las versiones y qué queda como archivo: [Versiones](#versiones-final-final1-final2).

**Dos normas, para dos cosas distintas** (2026-09-10):

- **Citas y referencias: Vancouver** (ICMJE + NLM). Estilo numérico secuencial implementado
  con `biblatex/numeric-comp` + `sorting=none` + `terseinits` (no existe un estilo
  `vancouver` cargado como tal). Los títulos de revista se escriben **completos**, no con la
  abreviatura ISO del NLM, por legibilidad en un documento en español, y el último autor se
  separa con «y» en vez de coma: las dos son decisiones tomadas, no descuidos. Los **localizadores de página** siguen una
  regla única, declarada en la Introducción («Normas de citación y presentación»): llevan
  página las citas que sostienen una ecuación, un valor, un umbral, una definición o una
  atribución concreta; las de encuadre van sin página (regla del 2026-09-16, que reemplaza al
  «Vancouver puro sin página» del 09-09). Dentro de un corchete, el punto y coma separa las
  referencias cuando alguna lleva localizador, y la lista se titula **«Referencias
  bibliográficas»**. Los asientos siguen la puntuación de `biblatex` (título entre comillas,
  «En:», «31.5 (2023)»), y la Introducción lo declara.
  Guía completa con plantilla y ejemplo por tipo de fuente:
  [normas/guia_vancouver.pdf](normas/guia_vancouver.pdf).
- **Presentación del documento: APA 7.ª ed., con tres excepciones declaradas.** Márgenes de
  2,54 cm, interlineado doble, sangría de 1,27 cm, número de página arriba a la derecha,
  jerarquía de títulos de cinco niveles y rótulos de tablas y figuras con el número en negrita
  y el título en cursiva encima del contenido. Las excepciones: capítulos y secciones
  numerados, papel A4 y, **desde final3**, texto **justificado** con partición silábica, por
  pedido del tribunal. La fuente es **Times New Roman 12** (la real del sistema, por eso
  XeLaTeX), que APA admite; las fórmulas siguen en Latin Modern y las celdas de las tablas van a
  la izquierda. Hasta final2 el texto iba a la izquierda sin justificar, en Latin Modern. Qué se
  aplicó de APA y por qué:
  [docs/notas/2026-09-10_apa-presentacion.md](../docs/notas/2026-09-10_apa-presentacion.md).

Las dos no chocan: APA no dice nada sobre cómo se escribe una referencia numérica y
Vancouver no dice nada sobre el interlineado.

## Estado y decisiones (formulación final, 2026-09-21; ajustada en final3, 2026-09-25)

Rigen sobre la versión vigente. Las decisiones de las versiones archivadas que contradigan a
estas quedan sin efecto; los criterios editoriales completos, con la tabla de términos
canónicos y los enunciados formales exactos, están en el `CRITERIOS.md` de la versión vigente
([capitulos_final3/CRITERIOS.md](capitulos_final3/CRITERIOS.md)).

- **Título** (`\tituloTesis`, alimenta la portada): el del perfil defendido, *«Desarrollo de
  software educativo de elementos finitos para el análisis estructural empleando el lenguaje
  de programación Python»*. La formulación final se eligió, entre otras razones, porque es la
  que mejor corresponde a ese título: es tecnológico —verbo, qué, cómo— y nunca prometió medir
  aprendizaje. **No hace falta cambiarlo.**
- **«Análisis estructural» acotado:** en *Alcance y limitaciones* se define como análisis de
  tensiones y deformaciones de medios continuos 2D en elasticidad plana, y excluye pórticos y
  cerchas, placas, cáscaras y 3D. No reintroducir el término sin esa acotación.
- **Problema, variables e hipótesis** (final3): causa = la **transparencia del procedimiento de
  cálculo** (niveles: caja negra o procedimiento a la vista); efecto = la **trazabilidad y
  verificabilidad del procedimiento de cálculo**, atributos de la unidad de análisis que se
  miden sobre el software; interviniente = EduFEM. El problema dice «escasa» transparencia (no
  «nula»: la Tabla 1.1 registra «Baja (caja negra)») y sigue el molde «¿De qué manera… podrá
  incidir en…?». Dos cláusulas, (a) trazabilidad y (b) verificabilidad, enunciadas en §2.1.6 y
  comprobadas en el Capítulo 3. La universidad **no** figura en el problema, el objetivo
  general ni la hipótesis: la tesis es general, y la Carrera aparece solo como destinataria en
  la delimitación. **No** volver a una variable dependiente que viva en el estudiante, ni a la
  «hipótesis de diseño» condicional, ni a tres cláusulas.
- **Objeto y campo:** objeto = el análisis de medios continuos en elasticidad plana por el MEF
  (técnico); campo = los medios de cálculo con que ese análisis se enseña. **No** volver al
  objeto «proceso de enseñanza-aprendizaje».
- **Tres objetivos específicos, uno por capítulo** (final3, por indicación del Ing. Miranda):
  Fundamentar, Desarrollar, y Verificar y validar. **El título de cada capítulo es su objetivo,
  sustantivado y completo** (verbo, qué, cómo y para qué), aunque sea largo: así lo pidió el
  tribunal («tus objetivos definen tus capítulos»). Si cambia un objetivo, cambia su título.
  «Diagnosticar» **no** es objetivo (en su lámina, la tesis de grado va «sin diagnóstico»): el
  análisis de los antecedentes es parte de la fundamentación. Dos preguntas de investigación,
  una por cláusula, en apartado propio. Conclusiones en **tríada**: una conclusión y una
  recomendación por capítulo. **No** volver a cinco o seis objetivos ni a tres preguntas.
- **Método: ciencia del diseño** (Hevner 2004, Peffers 2007, Wieringa 2014), declarado en la
  Introducción y desarrollado en §2.1.1 con la tabla de las seis actividades. Es también el
  argumento contra «esto es un proyecto de grado» (junto con los Art. 6, 8 y 9 del Reglamento
  frente al Art. 57 y 61).
- **Validación: contra referencias externas.** El eje es la verificación y validación numérica
  (soluciones manufacturadas, Timoshenko frente a la solución analítica y a SAP2000, Cook), con
  criterios de aceptación fijados de antemano y reunidos en la tabla de §2.1.6. La cobertura de
  contenido se coteja contra el consenso publicado de expertos, y el documento declara que ese
  cotejo lo hace el autor. **No** se hace validación por juicio de expertos ni prueba de campo,
  y la versión final **no las nombra**: con la variable dependiente en el análisis, no son un
  eslabón pendiente de la cadena.
- **Idioma:** español neto, en registro llano y neutro para un tribunal de ingeniería civil que
  domina el análisis matricial de pórticos pero no el MEF. Se permiten glosas con el término
  inglés entre paréntesis y en cursiva la primera vez. Terminología canónica (GDL, MEF): ver la
  tabla del `CLAUDE.md` de la raíz del repo.
- **Defensas:** dos instancias, borrador y limpio (final).

**Términos que la versión final NO usa** (y que no deben reintroducirse): «canal de cálculo»
(ahora «procedimiento de cálculo»), «validez de contenido» y «tabla de especificaciones»
(ahora «cobertura de contenido»), «prueba de campo», «en esta etapa», «validador de salud»
(ahora «comprobador de salud»), «módulo interactivo» (ahora «módulo educativo»), «stack
tecnológico» (ahora «tecnologías empleadas»). Tampoco se afirma ningún efecto sobre el
estudiante. Formulación completa y argumentario de defensa:
[alternativas/formulacion_final.pdf](alternativas/formulacion_final.pdf); detalle de la
construcción: [docs/notas/2026-09-21_tesis-final.md](../docs/notas/2026-09-21_tesis-final.md).

## Versiones: final, final1, final2…

La tesis mejora por versiones sucesivas, y **cada una deja intacta a la anterior**:

| Versión | Fuente | Qué es |
|---|---|---|
| **final3** (vigente) | `main_final3.tex` + `capitulos_final3/` | Observaciones del Ing. Miranda (2026-09-25), adaptadas al contenido: problema, objetivo general e hipótesis en el molde del tribunal y sin la universidad; tres objetivos específicos, uno por capítulo, que dan el título a cada capítulo; Introducción por apartados; Conclusiones en tríada con las Figuras CR.1-CR.2 y la Tabla CR.1; Figura 2.1 nueva; Times New Roman 12 justificado (XeLaTeX). Lleva también el retiro de PyMuPDF de final2. Diagnóstico: [observaciones_miranda/](observaciones_miranda/README.md). Registro: [auditoria_final/IMPLEMENTACION-FINAL3.md](auditoria_final/IMPLEMENTACION-FINAL3.md) |
| final2 | `main_final2.tex` + `capitulos_final2/` | Segunda iteración (2026-09-25): verificación de final1 y nueva revisión por unidades, cada hallazgo contrastado con el código o la fuente antes de aplicarlo. Incluye un cambio posterior del mismo día, aplicado en el lugar por decisión del autor: el retiro de PyMuPDF del software (Tabla 2.5 y su nota, Anexo A, «Versión evaluada»). Registro: [auditoria_final/IMPLEMENTACION-FINAL2.md](auditoria_final/IMPLEMENTACION-FINAL2.md) |
| final1 | `main_final1.tex` + `capitulos_final1/` | La versión final con la auditoría de redacción implementada (2026-09-23). Registro de cada cambio: [auditoria_final/IMPLEMENTACION-FINAL1.md](auditoria_final/IMPLEMENTACION-FINAL1.md) |
| final | `main_final.tex` + `capitulos_final/` | La versión entregada el 2026-09-21 y auditada el 22 (commit `ee7b5a6`). Se conserva exactamente así, como base de comparación |

Para abrir la siguiente mejora (**final4**), se copia la vigente y se trabaja solo sobre la copia:

1. `capitulos_final3/` → `capitulos_final4/` (con su `preambulo.tex`, `referencias.bib`,
   `CRITERIOS.md` y `figuras/`), y `main_final3.tex` → `main_final4.tex`.
2. En la copia, cambiar las rutas que nombran la versión: los `\input{capitulos_final3/...}` de
   `main_final4.tex`, el comentario de cabecera, el `\graphicspath` y el `\addbibresource` de
   su `preambulo.tex`, y la ruta de salida por defecto de
   `figuras/generar_figuras_formulacion.py` si se rehacen sus figuras.
3. Actualizar la tabla de arriba y la primera línea de este README.

Cada versión lleva **su propio preámbulo, su bibliografía y sus figuras rehechas** dentro de su
carpeta: así corregir una no altera la anterior. Las figuras que no cambian se siguen leyendo de
`figuras/` (el `\graphicspath` busca primero en la carpeta de la versión). Lo que comparten
todas es `portada/`, `figuras/`, `anexos/` y los ejemplares de `bibliografia/`.

Las versiones anteriores a la final (v1, v2, v3 y v4, con sus capítulos, sus PDF compilados y la
auditoría de la v4) están en [archivo/](archivo/README.md) y **no se mantienen**.

## Estructura

```
tesis/
├── main_final3.tex          # VERSION VIGENTE (XeLaTeX): lee solo capitulos_final3/
├── capitulos_final3/        # sus 11 capitulos + preambulo.tex, referencias.bib, CRITERIOS.md
│   └── figuras/             # figuras rehechas para esta version (tienen prioridad)
├── main_final2.tex          # segunda iteracion (no se edita)
├── capitulos_final2/        # idem, con su preambulo, bibliografia y figuras
├── main_final1.tex          # primera iteracion (no se edita)
├── capitulos_final1/        # idem, con su preambulo, bibliografia y figuras
├── main_final.tex           # version final auditada (base de comparacion, no se edita)
├── capitulos_final/         # sus 11 capitulos + CRITERIOS.md
├── preambulo.tex            # preambulo de main_final.tex (cada version final1+ lleva el suyo)
├── portada/
│   └── portada.tex          # portada (usa los datos que define cada main_*.tex)
├── bibliografia/
│   ├── referencias.bib      # bibliografia de main_final.tex (final1 lleva su copia)
│   └── *.pdf                # ejemplares consultados (gitignored: copyright)
├── figuras/                 # imagenes, generar_figuras.py y generar_figuras_formulacion.py (final3)
├── observaciones_miranda/   # diagnostico de las observaciones del Ing. Miranda (base de final3)
├── anexos/                  # PDF que se incluyen tal cual (validacion_sap2000.pdf, Anexo E)
├── auditoria_final/         # auditoria de redaccion de main_final + registro de su implementacion
├── normas/                  # las dos normas que rigen el documento
│   ├── guia_vancouver.tex/.pdf   # citas y referencias (propia, se versiona)
│   └── Tavares 2020 - ...pdf     # guia APA de terceros (gitignored: copyright)
├── respaldo_citas/          # que pagina respalda cada cita + scripts
├── alternativas/            # documentos de trabajo: formulacion_final.pdf (eje y defensa)
├── defensa_metodologica/    # estudio para defender el caracter tecnologico de la tesis
├── presentacion/            # defensa: presentacion interactiva final/ y video (ver su README)
├── Material docente/        # talleres y normas de la Carrera
├── archivo/                 # versiones v1 a v4 (no se mantienen; ver su README)
└── .gitignore               # ignora artefactos de compilacion
```

## Compilar (MiKTeX en Windows)

Desde la carpeta `tesis/`:

```
latexmk -xelatex main_final3.tex  # version vigente (Times New Roman real: SOLO con XeLaTeX)
latexmk -pdf main_final2.tex      # segunda iteracion, para comparar
latexmk -pdf main_final1.tex      # primera iteracion, para comparar
latexmk -pdf main_final.tex       # version auditada, para comparar
```

> Usa **biber** (no bibtex); latexmk lo llama solo. Si las citas salen como `[?]`, faltó
> correr biber o la clave no existe en el `referencias.bib` de esa versión. `main_final3.tex`
> con `latexmk -pdf` se detiene con un mensaje que pide XeLaTeX. Si el PDF está abierto en un
> visor que lo bloquea, la compilación falla al escribirlo: hay que cerrarlo antes.

## Antes de entregar

1. **Personalizar los preliminares** en `capitulos_final3/00_preliminares.tex`: la dedicatoria
   y los agradecimientos, y activar su `\input` en `main_final3.tex` (hoy comentado: la
   predefensa los lleva fuera). Ahí está también, comentado, el párrafo opcional de declaración
   de uso de herramientas de inteligencia artificial: actívalo o bórralo según lo que admita el
   Reglamento de Graduación.
2. **Revisar los datos de portada** en `main_final3.tex` (`\universidad`, `\autorTesis`,
   `\carrera`, `\gradoTesis`, `\ciudadTesis`, `\anioTesis`) y comprobar en el Reglamento si
   la carátula debe consignar tutor o asesor: hoy no lo lleva.
3. Comprobar que no quede ningún `% DATO PENDIENTE` ni `\pendiente{...}`.
4. Repasar lo que dejan en manos del autor
   [auditoria_final/IMPLEMENTACION-FINAL1.md](auditoria_final/IMPLEMENTACION-FINAL1.md) (su segunda
   sección), [auditoria_final/IMPLEMENTACION-FINAL2.md](auditoria_final/IMPLEMENTACION-FINAL2.md)
   («Cambios de fondo», «Decisiones que quedan para el autor» y «Observaciones sobre el software»)
   y [auditoria_final/IMPLEMENTACION-FINAL3.md](auditoria_final/IMPLEMENTACION-FINAL3.md) («Lo
   que queda para el autor»: interlineado y márgenes según el Reglamento, láminas de defensa,
   hash de la revisión del instalador).

## Skills de ayuda (Claude Code)

- `tesis-redactar` — redactar/ampliar secciones en español claro y natural.
- `tesis-revisar` — revisar y pulir borradores (claridad, terminología, citas, LaTeX).
- `tesis-bibliografia` — agregar/gestionar referencias Vancouver correctamente.
