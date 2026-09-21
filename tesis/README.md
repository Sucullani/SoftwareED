# Tesis — EduFEM

Fuente LaTeX de la tesis sobre **EduFEM** (GUI educativa de elementos finitos 2D).
Idioma: español (babel).

**Dos normas, para dos cosas distintas** (2026-09-10):

- **Citas y referencias: Vancouver** (ICMJE + NLM). Estilo numérico secuencial implementado
  con `biblatex/numeric-comp` + `sorting=none` + `terseinits` (no existe un estilo
  `vancouver` cargado como tal). Los títulos de revista se escriben **completos**, no con la
  abreviatura ISO del NLM, por legibilidad en un documento en español, y el último autor se
  separa con «y» en vez de coma: las dos son decisiones tomadas, no descuidos. Los **localizadores de página** siguen una
  regla única, declarada en la Introducción («Estructura del documento»): llevan página las
  citas que sostienen una ecuación, un valor, un umbral, una definición o una atribución
  concreta; las de encuadre van sin página (regla del 2026-09-16, que reemplaza al «Vancouver
  puro sin página» del 09-09). Las citas múltiples con página se separan con punto y coma y
  la lista se titula **«Referencias bibliográficas»**.
  Guía completa con plantilla y ejemplo por tipo de fuente:
  [normas/guia_vancouver.pdf](normas/guia_vancouver.pdf).
- **Presentación del documento: APA 7.ª ed.** Márgenes de 2,54 cm, interlineado doble,
  sangría de 1,27 cm, texto a la izquierda sin justificar ni cortar palabras, número de
  página arriba a la derecha, jerarquía de títulos de cinco niveles y rótulos de tablas y
  figuras con el número en negrita y el título en cursiva encima del contenido. Qué se
  aplicó, qué no y por qué:
  [docs/notas/2026-09-10_apa-presentacion.md](../docs/notas/2026-09-10_apa-presentacion.md).

Las dos no chocan: APA no dice nada sobre cómo se escribe una referencia numérica y
Vancouver no dice nada sobre el interlineado.

## Estado y decisiones (versión final, 2026-09-21)

Rigen sobre `main_final.tex` y `capitulos_final/`. Las decisiones de las versiones anteriores
que contradigan a estas quedan sin efecto; los criterios editoriales completos, con la tabla
de términos canónicos, están en [capitulos_final/CRITERIOS.md](capitulos_final/CRITERIOS.md).

- **Título** (`\tituloTesis`, alimenta la portada): el del perfil defendido, *«Desarrollo de
  software educativo de elementos finitos para el análisis estructural empleando el lenguaje
  de programación Python»*. La formulación final se eligió, entre otras razones, porque es la
  que mejor corresponde a ese título: es tecnológico —verbo, qué, cómo— y nunca prometió medir
  aprendizaje. **No hace falta cambiarlo.**
- **«Análisis estructural» acotado:** en *Alcance y limitaciones* se define como análisis de
  tensiones y deformaciones de medios continuos 2D en elasticidad plana, y excluye pórticos y
  cerchas, placas, cáscaras y 3D. No reintroducir el término sin esa acotación.
- **Problema, variables e hipótesis:** causa = la forma en que el software expone el
  procedimiento de cálculo (caja negra o procedimiento a la vista); efecto = la **trazabilidad
  y verificabilidad del análisis**, que es una propiedad del medio de cálculo y se mide sobre
  el software; interviniente = EduFEM. Dos cláusulas, (a) trazabilidad y (b) verificabilidad,
  ambas comprobadas en el Capítulo 3. **No** volver a una variable dependiente que viva en el
  estudiante, ni a la «hipótesis de diseño» condicional, ni a tres cláusulas.
- **Objeto y campo:** objeto = el análisis de medios continuos en elasticidad plana por el MEF
  (técnico); campo = los medios de cálculo con que ese análisis se enseña. **No** volver al
  objeto «proceso de enseñanza-aprendizaje».
- **Cinco objetivos específicos** en la escalera de la guía del tribunal: diagnosticar,
  fundamentar, desarrollar, verificar y validar. Dos preguntas de investigación, una por
  cláusula. **No** volver a seis objetivos ni a tres preguntas.
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

## Estructura

```
tesis/
├── main_final.tex           # VERSION DE ENTREGA: autocontenida, lee solo capitulos_final/
├── capitulos_final/         # los 11 capitulos de la version final + CRITERIOS.md
├── main.tex                 # documento maestro de la v1 (metadatos de portada + \input de todo)
├── preambulo.tex            # paquetes y configuración (presentación APA + biblatex Vancouver)
├── portada/
│   └── portada.tex          # portada (usa los placeholders de main.tex)
├── main_v2.tex              # misma tesis en Arial (xelatex); lee capitulos/
├── main_v3.tex              # eje pedagógico (alternativa C); lee capitulos_v3/ + capitulos/
├── main_v4.tex              # eje «caja negra -> bajo criterio»; lee capitulos_v4/ + capitulos/
├── capitulos/
│   ├── 00_resumen.tex
│   ├── 01_introduccion.tex
│   ├── 02_marco_teorico.tex            # Capítulo 1
│   ├── 02b_diseno_metodologico.tex     # Capítulo 2, §2.1
│   ├── 03_diseno_implementacion.tex    # Capítulo 2, §2.2
│   ├── 04_resultados.tex               # Capítulo 3
│   ├── 05_conclusiones.tex
│   ├── 06_anexos.tex
│   └── 07_anexo_memoria.tex
├── capitulos_v3/            # capitulos que reescribe la v3 (archivo, no se mantiene)
├── capitulos_v4/            # capitulos que reescribe la v4 (archivo, no se mantiene)
├── bibliografia/
│   ├── referencias.bib      # referencias en biblatex (todas las versiones)
│   ├── referencias_v3.bib   # 16 entradas que solo carga main_v3.tex (ejemplares pendientes)
│   └── *.pdf                # ejemplares consultados (gitignored: copyright)
├── normas/                  # las dos normas que rigen el documento
│   ├── guia_vancouver.tex/.pdf   # citas y referencias (propia, se versiona)
│   └── Tavares 2020 - ...pdf     # guía APA de terceros (gitignored: copyright)
├── respaldo_citas/          # qué página respalda cada cita + scripts
├── figuras/                 # imágenes (se versionan)
├── alternativas/            # documentos de trabajo: formulacion_final.pdf (eje y defensa)
├── auditoria_v4/            # auditoría de redacción que alimentó la versión final
├── presentacion/            # defensa: guion.json + build_deck.py -> Defensa_EduFEM.pptx (ver su README)
└── .gitignore               # ignora artefactos de compilación
```

## La versión final y las cuatro anteriores

**`main_final.tex` es la versión de entrega (2026-09-21).** Es **autocontenida**: todos sus
capítulos viven en `capitulos_final/` y no lee nada de `capitulos/` ni de `capitulos_v4/`.
Comparte con las versiones anteriores el `preambulo.tex`, la `portada/`, las `figuras/` y
`bibliografia/referencias.bib`.

Su eje es **tecnológico**, no pedagógico. Causa: el uso del software de análisis como caja
negra. Efecto: la baja **trazabilidad y verificabilidad** del análisis por el MEF —una
propiedad del análisis, que se mide sobre el software y no sobre personas—. Interviniente:
EduFEM. La hipótesis tiene dos cláusulas, (a) trazabilidad y (b) verificabilidad, y **las dos
se comprueban dentro del documento**: no queda ninguna afirmación diferida a una prueba de
campo. Cinco objetivos específicos en escalera y dos preguntas de investigación. El método es
la **ciencia del diseño** (Hevner 2004, Peffers 2007, Wieringa 2014, las tres en
`referencias.bib` con ejemplar y respaldo), que es también la respuesta a «esto es un proyecto
de grado». Formulación completa y argumentario de defensa:
[alternativas/formulacion_final.pdf](alternativas/formulacion_final.pdf); criterios
editoriales que rigen todos los capítulos:
[capitulos_final/CRITERIOS.md](capitulos_final/CRITERIOS.md); detalle de la construcción:
[docs/notas/2026-09-21_tesis-final.md](../docs/notas/2026-09-21_tesis-final.md).

**Términos que la versión final NO usa** (y que no deben reintroducirse): «canal de cálculo»
(ahora «procedimiento de cálculo»), «validez de contenido» y «tabla de especificaciones»
(ahora «cobertura de contenido»), «prueba de campo», «en esta etapa», «validador de salud»
(ahora «comprobador de salud»), «módulo interactivo» (ahora «módulo educativo»), «stack
tecnológico» (ahora «tecnologías empleadas»). Tampoco se afirma ningún efecto sobre el
estudiante. Rutten 2012, Chi y Wylie 2014 y Atkinson 2000 siguen en el `.bib` porque la v4 las
cita, pero **la versión final no las cita**: sostenían la plausibilidad de un efecto que ya no
se afirma, y lo que queda lo cubren Lee, Bishay y Pérez-Santiago.

Las cuatro versiones anteriores quedan como archivo y **no se mantienen**.

**La v4 (2026-09-19)** aplica la alternativa 3 elegida
por el autor —problema «uso del software como caja negra → bajo criterio para interpretar la
respuesta estructural», con el molde de las guías del tribunal— sobre los capítulos de la v1,
con cinco objetivos específicos en escalera, tres preguntas, hipótesis en futuro afirmativo
comprobada en su parte de diseño y contenido, tabla de especificaciones contra el consenso de
expertos de Pérez-Santiago y Campos y matriz de los cuatro principios de §1.2. Tres
referencias nuevas (Rutten 2012, Chi y Wylie 2014, Atkinson 2000), ya en `referencias.bib`
con ejemplar y respaldo. `main_v4.tex` lee `capitulos_v4/` y, para lo que no cambia,
`capitulos/`. Detalle: [docs/notas/2026-09-19_tesis-v4-alternativa-3.md](../docs/notas/2026-09-19_tesis-v4-alternativa-3.md).
La v3 queda como archivo de referencia y no se mantiene.

Las dos primeras son tipografías del mismo texto. **Comparten todo**: los mismos
`capitulos/`, la misma `bibliografia/` y el mismo `preambulo.tex`. Editar un
capítulo actualiza las dos; lo único que cambia es la fuente del cuerpo.

| Fuente | Texto | Fórmulas | Motor | Salida |
|---|---|---|---|---|
| **`main_final.tex`** | Latin Modern (serif) 12 pt | LaTeX (Latin Modern Math) | `pdflatex` | **`main_final.pdf`** |
| `main.tex` | Latin Modern (serif) 12 pt | LaTeX (Latin Modern Math) | `pdflatex` | `main.pdf` |
| `main_v2.tex` | **Arial 12 pt** | LaTeX (Latin Modern Math) | `xelatex` | `main_v2.pdf` |
| `main_v3.tex` | Latin Modern 12 pt | LaTeX (Latin Modern Math) | `pdflatex` | `main_v3.pdf` |
| `main_v4.tex` | Latin Modern 12 pt | LaTeX (Latin Modern Math) | `pdflatex` | `main_v4.pdf` |

La **v3 (2026-09-18) es otra tesis, no otra tipografía**: aplica el **eje causa-efecto
pedagógico** (alternativa C elegida por el autor). La variable dependiente pasa a ser la
comprensión de los fundamentos del MEF por el estudiante, el objeto de estudio vuelve a ser
el proceso de enseñanza-aprendizaje, y el trabajo se organiza como **primer ciclo de
investigación basada en diseño**: contrasta relevancia, corrección, consistencia y
practicidad esperada con tres instrumentos documentales (tabla de especificaciones, mapa de
conjeturas con matriz de trazabilidad, evaluación heurística LORI) y deja diseñada la
prueba de campo del segundo ciclo. Siete objetivos específicos, cuatro preguntas. Sus
capítulos reescritos viven en `capitulos_v3/` (los que no cambian se leen de `capitulos/`)
y sus 16 referencias nuevas en `bibliografia/referencias_v3.bib`, que **solo** `main_v3.tex`
carga y cuyos ejemplares **están pendientes de conseguir** (20 localizadores marcados con
`% LOCALIZADOR PENDIENTE`). Detalle, decisiones y pendientes:
[docs/notas/2026-09-18_tesis-v3-eje-pedagogico.md](../docs/notas/2026-09-18_tesis-v3-eje-pedagogico.md).
Mientras el autor no decida cuál se entrega, **v1/v2 y v3 no se sincronizan entre sí**.

Las fórmulas son **idénticas en las dos**: Arial no tiene alfabeto matemático ni
símbolos de extensión, así que la matemática se compone siempre con las fuentes de
LaTeX. Lo mismo vale para los listados de código del Anexo C, que se quedan en
Latin Modern Mono para que el Python siga siendo copiable carácter por carácter.

El interruptor es una sola línea: `main_v2.tex` define `\tesisFuenteArial` antes
de cargar `preambulo.tex`. No dupliques el preámbulo.

## Compilar (MiKTeX en Windows)

Desde la carpeta `tesis/`. La versión de entrega se compila con:

```
latexmk -pdf main_final.tex
```

**v1 va con `pdflatex`; v2 va con `xelatex`** — v2 usa la
Arial real del sistema (`C:\Windows\Fonts\arial.ttf`), y eso `pdflatex` no lo sabe hacer.

```
pdflatex main            xelatex main_v2
biber    main            biber   main_v2
pdflatex main            xelatex main_v2
pdflatex main            xelatex main_v2
```

O, más simple, con latexmk:

```
latexmk -pdf     main.tex
latexmk -xelatex main_v2.tex
```

> Usa **biber** (no bibtex). Si las citas salen como `[?]`, faltó correr biber o la
> clave no existe en `referencias.bib`.
>
> v2 necesita Arial instalada. En Windows viene de fábrica; en Linux hay que poner
> las *core fonts* de Microsoft o cambiar el `\setmainfont` del preámbulo.

## Antes de entregar

1. **Personalizar los preliminares** en `capitulos_final/00_preliminares.tex`: la dedicatoria
   y los agradecimientos. Ahí está también, comentado, el párrafo opcional de declaración de
   uso de herramientas de inteligencia artificial: actívalo o bórralo según lo que admita el
   Reglamento de Graduación.
2. **Revisar los datos de portada** en `main_final.tex` (`\universidad`, `\autorTesis`,
   `\carrera`, `\gradoTesis`, `\ciudadTesis`, `\anioTesis`) y comprobar en el Reglamento si
   la carátula debe consignar tutor o asesor: hoy no lo lleva.
3. Comprobar que no quede ningún `% DATO PENDIENTE` ni `\pendiente{...}`.

## Skills de ayuda (Claude Code)

- `tesis-redactar` — redactar/ampliar secciones en español claro y natural.
- `tesis-revisar` — revisar y pulir borradores (claridad, terminología, citas, LaTeX).
- `tesis-bibliografia` — agregar/gestionar referencias Vancouver correctamente.
