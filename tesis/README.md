# Tesis — EduFEM

Fuente LaTeX de la tesis sobre **EduFEM** (GUI educativa de elementos finitos 2D).
Idioma: español (babel).

**Versión vigente: `main_final4.tex` + `capitulos_final4/`** (2026-10-20, 191 páginas). **El
archivo final, por ahora, es [`main_final4.pdf`](main_final4.pdf)**, en esta misma carpeta. Aplica
las observaciones del tribunal tras la **defensa de borrador**:
- la hipótesis que dictó el tribunal, con su contraste por partes (§2.1.6 y §3.8);
- Conclusiones sin «Aportes del trabajo» ni «Limitaciones» y sin los rótulos «Conclusión N»;
- títulos de tablas y figuras en redonda;
- número de página al pie, con el capítulo y un filete;
- «ejemplo guía» en lugar de «ejemplo canónico».

Corrige además la redacción de los hallazgos H1 y H4 de la auditoría general.
**Se compila con XeLaTeX**: `latexmk -xelatex main_final4.tex` desde esta carpeta. Los archivos
auxiliares van a `build/` (lo fija `latexmkrc`) y en la raíz solo queda el PDF. Registro de cada
cambio: [auditoria_final/IMPLEMENTACION-FINAL4.md](auditoria_final/IMPLEMENTACION-FINAL4.md). Cómo
se numeran las versiones y qué queda como archivo: [Versiones](#versiones-final-final1-final2).

**La defensa de final4** (presentación HTML interactiva, su versión estilo PowerPoint y una copia
en un solo archivo para llevar a otro equipo, el PowerPoint editable y el narrado, y el audio
completo de la narración) está en [presentacion/final4/](presentacion/final4/README.md); índice:
[presentacion/README.md](presentacion/README.md). La defensa de borrador de final3 quedó como
archivo solo en el disco del autor: no se sube al repositorio.

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
- **Presentación del documento: APA 7.ª ed., con cinco excepciones declaradas.** Se toman de
  APA los márgenes de 2,54 cm, el interlineado doble, la sangría de 1,27 cm, la jerarquía de
  títulos de cinco niveles y los rótulos de tablas y figuras con el número en negrita encima del
  contenido. Las excepciones:
  - capítulos y secciones numerados;
  - papel A4;
  - **desde final3**, texto **justificado** con partición silábica;
  - **desde final4**, el **título de tablas y figuras en redonda**, no en cursiva;
  - **desde final4**, el **número de página al pie**, a la derecha, con el nombre corto del
    capítulo a la izquierda y un filete fino; APA lo pone arriba a la derecha.

  Las tres últimas las pidió el tribunal. Las notas al pie van fijas al fondo de la hoja.
  La fuente es **Times New Roman 12** (la real del sistema, por eso XeLaTeX), que APA admite;
  las fórmulas siguen en Latin Modern y las celdas de las tablas van a la izquierda. Hasta
  final2 el texto iba a la izquierda sin justificar, en Latin Modern. Qué se aplicó de APA y
  por qué: [docs/notas/2026-09-10_apa-presentacion.md](../docs/notas/2026-09-10_apa-presentacion.md).

Las dos no chocan: APA no dice nada sobre cómo se escribe una referencia numérica y
Vancouver no dice nada sobre el interlineado.

## Estado y decisiones (formulación final, 2026-09-21; ajustada en final3, 2026-09-25, y en final4, 2026-10-20)

Rigen sobre la versión vigente. Las decisiones de las versiones archivadas que contradigan a
estas quedan sin efecto; los criterios editoriales completos, con la tabla de términos
canónicos y los enunciados formales exactos, están en el `CRITERIOS.md` de la versión vigente
([capitulos_final4/CRITERIOS.md](capitulos_final4/CRITERIOS.md)).

- **Título** (`\tituloTesis`, alimenta la portada): el del perfil defendido, *«Desarrollo de
  software educativo de elementos finitos para el análisis estructural empleando el lenguaje
  de programación Python»*. La formulación final se eligió, entre otras razones, porque es la
  que mejor corresponde a ese título: es tecnológico —verbo, qué, cómo— y nunca prometió medir
  aprendizaje. **No hace falta cambiarlo.**
- **«Análisis estructural» acotado:** en *Alcance y limitaciones* se define como análisis de
  tensiones y deformaciones de medios continuos 2D en elasticidad plana, y excluye pórticos y
  cerchas, placas, cáscaras y 3D. No reintroducir el término sin esa acotación.
- **Problema, variables e hipótesis** (final3; hipótesis de final4): causa = la **transparencia
  del procedimiento de cálculo** (niveles: caja negra o procedimiento a la vista); efecto = la
  **trazabilidad y verificabilidad del procedimiento de cálculo** (niveles: baja o alta),
  atributos de la unidad de análisis que se miden sobre el software; interviniente = EduFEM,
  desarrollado bajo un método de diseño de software educativo (la ciencia del diseño). El
  problema dice «escasa» transparencia (no «nula»: la Tabla 1.1 registra «Baja (caja negra)») y
  sigue el molde «¿De qué manera… podrá incidir en…?». La **hipótesis es la que dictó el
  tribunal** tras la defensa de borrador, con «dada»: «Bajo la aplicación de un método de diseño
  de software educativo, el desarrollo de EduFEM permitirá mejorar la trazabilidad y la
  verificabilidad del análisis por el Método de los Elementos Finitos en elasticidad plana, dada
  la escasa transparencia con que el software expone su procedimiento de cálculo». Su «análisis»
  y el «procedimiento de cálculo» del problema nombran la misma unidad; el problema y el
  objetivo general no cambiaron (decisión del autor). Se contrasta **en cuatro partes**:
  condición, intervención, efecto (cláusulas (a) trazabilidad y (b) verificabilidad, con los
  criterios de §2.1.6) y antecedente; las premisas se respaldan con evidencia documental y la
  regla de decisión es conjuntiva (§2.1.6; se aplica en §3.8, Tabla 3.11). La universidad **no** figura en el problema,
  el objetivo general ni la hipótesis: la tesis es general, y la Carrera aparece solo como
  destinataria en la delimitación. **No** volver a una variable dependiente que viva en el
  estudiante ni a tres cláusulas. «Bajo la aplicación de un método…» es el molde de la lámina
  de hipótesis del Ing. Miranda, no la «hipótesis de diseño» condicional de v1/v2, que no vuelve.
- **Objeto y campo:** objeto = el análisis de medios continuos en elasticidad plana por el MEF
  (técnico); campo = los medios de cálculo con que ese análisis se enseña. **No** volver al
  objeto «proceso de enseñanza-aprendizaje».
- **Tres objetivos específicos, uno por capítulo** (final3, por indicación del Ing. Miranda):
  Fundamentar, Desarrollar, y Verificar y validar. **El título de cada capítulo es su objetivo,
  sustantivado y completo** (verbo, qué, cómo y para qué), aunque sea largo: así lo pidió el
  tribunal («tus objetivos definen tus capítulos»). Si cambia un objetivo, cambia su título.
  «Diagnosticar» **no** es objetivo (en su lámina, la tesis de grado va «sin diagnóstico»): el
  análisis de los antecedentes es parte de la fundamentación. Dos preguntas de investigación,
  una por cláusula, en apartado propio. Conclusiones en **tríada**: una conclusión y sus
  recomendaciones por capítulo, **sin** los rótulos «Conclusión N» ni «Recomendación N» y sin
  las secciones «Aportes del trabajo» y «Limitaciones» (final4, tribunal: redundantes con la
  Introducción; lo único que decían pasó a §3.7.5 y a los párrafos de las Conclusiones). **No**
  volver a cinco o seis objetivos ni a tres preguntas.
- **Método: ciencia del diseño** (Hevner 2004, Peffers 2007, Wieringa 2014), declarado en la
  Introducción y desarrollado en §2.1.1 con la tabla de las seis actividades. Es también el
  argumento contra «esto es un proyecto de grado» (junto con los Art. 6, 8 y 9 del Reglamento
  frente al Art. 57 y 61).
- **Validación: contra referencias externas.** El eje es la verificación y validación numérica
  (soluciones manufacturadas, Timoshenko frente a la solución analítica y a SAP2000, Cook), con
  criterios de aceptación explícitos reunidos en la tabla de §2.1.6. No se escribe que los
  criterios se fijaron «de antemano»: ninguno precede a las primeras corridas, y la tesis lo
  declara (H4). La cobertura de
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
tecnológico» (ahora «tecnologías empleadas»), «ejemplo canónico» y «orden canónico» (ahora
«ejemplo guía» y «el orden del cálculo», desde final4, por pedido del tribunal de evitar
términos muy técnicos). Tampoco se afirma ningún efecto sobre el estudiante. Formulación completa y argumentario de defensa:
[alternativas/formulacion_final.pdf](alternativas/formulacion_final.pdf); detalle de la
construcción: [docs/notas/2026-09-21_tesis-final.md](../docs/notas/2026-09-21_tesis-final.md).

## Versiones: final, final1, final2…

La tesis mejora por versiones sucesivas, y **cada una deja intacta a la anterior**:

| Versión | Fuente | Qué es |
|---|---|---|
| **final4** (vigente) | `main_final4.tex` + `capitulos_final4/` → **`main_final4.pdf`** | Observaciones del tribunal tras la defensa de borrador (2026-10-20): hipótesis del tribunal con «dada» y contraste en cuatro partes (§2.1.6; §3.8 con la Tabla 3.11 nueva); Conclusiones rehechas sin «Aportes del trabajo», «Limitaciones» ni los rótulos «Conclusión N» y «Recomendación N» (Figura CR.1 nueva, la hipótesis parte por parte; Figura CR.2; Tabla CR.1, la tríada con flechas); lo único de esas secciones pasó a §3.7.5; rótulos en redonda; número de página al pie con el capítulo y un filete; notas al pie fijas al fondo; «ejemplo guía» en vez de «ejemplo canónico»; figuras de la formulación en PDF vectorial con letra legible; redacción de H1 y H4 corregida. Registro: [auditoria_final/IMPLEMENTACION-FINAL4.md](auditoria_final/IMPLEMENTACION-FINAL4.md) |
| final3 | [archivo/final3/](archivo/README.md) | Observaciones del Ing. Miranda (2026-09-25), adaptadas al contenido: problema, objetivo general e hipótesis en el molde del tribunal y sin la universidad; tres objetivos específicos, uno por capítulo, que dan el título a cada capítulo; Introducción por apartados; Conclusiones en tríada con las Figuras CR.1-CR.2 y la Tabla CR.1; Figura 2.1 nueva; Times New Roman 12 justificado (XeLaTeX). Lleva también el retiro de PyMuPDF de final2. Es la versión de la defensa de borrador. Diagnóstico: [observaciones_miranda/](observaciones_miranda/README.md). Registro: [auditoria_final/IMPLEMENTACION-FINAL3.md](auditoria_final/IMPLEMENTACION-FINAL3.md) |
| final2 | [archivo/final2/](archivo/README.md) | Segunda iteración (2026-09-25): verificación de final1 y nueva revisión por unidades, cada hallazgo contrastado con el código o la fuente antes de aplicarlo. Incluye un cambio posterior del mismo día, aplicado en el lugar por decisión del autor: el retiro de PyMuPDF del software (Tabla 2.5 y su nota, Anexo A, «Versión evaluada»). Registro: [auditoria_final/IMPLEMENTACION-FINAL2.md](auditoria_final/IMPLEMENTACION-FINAL2.md) |
| final1 | [archivo/final1/](archivo/README.md) | La versión final con la auditoría de redacción implementada (2026-09-23). Registro de cada cambio: [auditoria_final/IMPLEMENTACION-FINAL1.md](auditoria_final/IMPLEMENTACION-FINAL1.md) |
| final | [archivo/final/](archivo/README.md) | La versión entregada el 2026-09-21 y auditada el 22 (commit `ee7b5a6`). Se conserva exactamente así, como base de comparación |

Las versiones anteriores (final, final1, final2 y, desde el 2026-10-20, final3, cada una con su
`.tex` principal, su carpeta de capítulos y su PDF) están en [archivo/](archivo/README.md), junto
a las v1 a v4: en la raíz de `tesis/` queda solo la versión vigente. Cómo recompilar una
archivada, si hiciera falta: [archivo/README.md](archivo/README.md).

Para abrir la siguiente mejora (**final5**), se copia la vigente y se trabaja solo sobre la copia:

1. `capitulos_final4/` → `capitulos_final5/` (con su `preambulo.tex`, `referencias.bib`,
   `CRITERIOS.md` y `figuras/`), y `main_final4.tex` → `main_final5.tex`.
2. En la copia, cambiar las rutas que nombran la versión: los `\input{capitulos_final4/...}` de
   `main_final5.tex`, el comentario de cabecera, el `\graphicspath`, el `\addbibresource` y el
   `\errmessage` de su `preambulo.tex`. Las figuras de la formulación se regeneran con
   `figuras/generar_figuras_formulacion.py --version final5`, que lee la tabla de veredicto de
   esa versión y escribe en su carpeta.
3. Compilar la copia sin otro cambio y anotar la línea base (páginas, etiquetas, avisos).
4. Actualizar la tabla de arriba, la primera línea de este README y los demás archivos que nombran
   la versión vigente: el `CRITERIOS.md` de la copia, las tres skills `tesis-*`, `docs/MAPA.md`,
   `docs/notas/ESTADO.md`, `latexmkrc`, `.gitignore`, `presentacion/README.md` y, al archivar la
   anterior, `archivo/README.md` (una búsqueda de `final4` fuera de `archivo/` los encuentra).

Cada versión lleva **su propio preámbulo, su bibliografía y sus figuras rehechas** dentro de su
carpeta: así corregir una no altera la anterior. Al terminar la nueva, la anterior pasa a
`archivo/finalN/` (su `.tex`, su carpeta y su PDF) y en la raíz queda solo la vigente. Las
figuras que no cambian se siguen leyendo de `figuras/` (el `\graphicspath` busca primero en la
carpeta de la versión). Lo que comparten todas es `portada/`, `figuras/`, `anexos/` y los
ejemplares de `bibliografia/`.

Las versiones anteriores (final, final1, final2 y final3, y antes v1, v2, v3 y v4, con sus
capítulos, sus PDF compilados y la auditoría de la v4) están en [archivo/](archivo/README.md) y
**no se mantienen**.

## Estructura

```
tesis/
├── main_final4.tex          # VERSION VIGENTE (XeLaTeX): lee solo capitulos_final4/
├── main_final4.pdf          # EL ARCHIVO FINAL (por ahora)
├── capitulos_final4/        # sus 11 capitulos + preambulo.tex, referencias.bib, CRITERIOS.md
│   └── figuras/             # figuras rehechas para esta version (tienen prioridad)
├── latexmkrc                # manda los auxiliares de compilacion a build/
├── build/                   # auxiliares de compilacion (gitignored; se puede borrar)
├── portada/
│   ├── portada.tex          # portada (usa los datos que define cada main_*.tex)
│   └── CARATULA.pdf         # formato oficial de caratula de la UATF que reproduce portada.tex
├── figuras/                 # imagenes compartidas, generar_figuras.py y generar_figuras_formulacion.py
├── anexos/                  # PDF que se incluyen tal cual (validacion_sap2000.pdf, Anexo E)
├── bibliografia/
│   ├── referencias.bib      # bibliografia de la version final archivada (final1+ llevan su copia)
│   └── *.pdf                # ejemplares consultados (gitignored: copyright)
├── presentacion/            # defensa: final3/ (defensa de borrador: HTML, PowerPoint, video y PDF) y archivo/
├── observaciones_miranda/   # diagnostico de las observaciones del Ing. Miranda (base de final3)
├── auditoria_final/         # auditorias de la final y registros de final1, final2, final3 y final4
├── defensa_metodologica/    # estudio para defender el caracter tecnologico de la tesis
├── normas/                  # las dos normas que rigen el documento
│   ├── guia_vancouver.tex/.pdf   # citas y referencias (propia, se versiona)
│   └── Tavares 2020 - ...pdf     # guia APA de terceros (gitignored: copyright)
├── respaldo_citas/          # que pagina respalda cada cita + scripts
├── alternativas/            # documentos de trabajo: formulacion_final.pdf (eje y defensa)
├── Material docente/        # talleres y normas de la Carrera
├── archivo/                 # versiones anteriores: final, final1, final2, final3 y v1 a v4 (no se mantienen)
└── .gitignore               # ignora artefactos de compilacion
```

## Compilar (MiKTeX en Windows)

Desde la carpeta `tesis/`:

```
latexmk -xelatex main_final4.tex  # version vigente (Times New Roman real: SOLO con XeLaTeX)
```

> Usa **biber** (no bibtex); latexmk lo llama solo. El `latexmkrc` de esta carpeta manda los
> archivos auxiliares (`.aux`, `.bbl`, `.log`, `.toc`, `.xdv`…) a `build/`: en la raíz solo
> cambia `main_final4.pdf`. Para empezar de cero, borrar `build/`. Si las citas salen como `[?]`,
> faltó correr biber o la clave no existe en `capitulos_final4/referencias.bib`.
> `main_final4.tex` con `latexmk -pdf` se detiene con un mensaje que pide XeLaTeX. Si el PDF está
> abierto en un visor que lo bloquea, la compilación falla al escribirlo: hay que cerrarlo antes.
> Las versiones archivadas se recompilan sobre una copia: [archivo/README.md](archivo/README.md).

## Antes de entregar

1. **Personalizar los preliminares** en `capitulos_final4/00_preliminares.tex`: la dedicatoria
   y los agradecimientos, y activar su `\input` en `main_final4.tex` (hoy comentado: la
   predefensa los lleva fuera). Ahí está también, comentado, el párrafo opcional de declaración
   de uso de herramientas de inteligencia artificial: actívalo o bórralo según lo que admita el
   Reglamento de Graduación.
2. **Revisar los datos de portada** en `main_final4.tex` (`\universidad`, `\autorTesis`,
   `\carrera`, `\gradoTesis`, `\ciudadTesis`, `\anioTesis`, hoy «octubre de 2026»: ajustarlo
   al mes de la entrega) y comprobar en el Reglamento si la carátula debe consignar tutor o asesor: hoy no lo
   lleva.
3. Comprobar que no quede ningún `% DATO PENDIENTE` ni `\pendiente{...}`.
4. Repasar lo que dejan en manos del autor
   [auditoria_final/IMPLEMENTACION-FINAL1.md](auditoria_final/IMPLEMENTACION-FINAL1.md) (su segunda
   sección), [auditoria_final/IMPLEMENTACION-FINAL2.md](auditoria_final/IMPLEMENTACION-FINAL2.md)
   («Cambios de fondo», «Decisiones que quedan para el autor» y «Observaciones sobre el software»),
   [auditoria_final/IMPLEMENTACION-FINAL3.md](auditoria_final/IMPLEMENTACION-FINAL3.md) («Lo
   que queda para el autor»: interlineado y márgenes según el Reglamento, láminas de defensa,
   hash de la revisión del instalador) y
   [auditoria_final/IMPLEMENTACION-FINAL4.md](auditoria_final/IMPLEMENTACION-FINAL4.md) («Lo que
   queda para el autor»).

## Skills de ayuda (Claude Code)

- `tesis-redactar` — redactar/ampliar secciones en español claro y natural.
- `tesis-revisar` — revisar y pulir borradores (claridad, terminología, citas, LaTeX).
- `tesis-bibliografia` — agregar/gestionar referencias Vancouver correctamente.
