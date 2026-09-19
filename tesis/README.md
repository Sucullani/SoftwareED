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

## Estado y decisiones (actualizado jun. 2026)

- **Título** (`\tituloTesis` en `main.tex`, alimenta la portada): se usa el del **perfil
  defendido** — *"Desarrollo de software educativo de elementos finitos para el análisis
  estructural empleando el lenguaje de programación Python"*. Si el reglamento admite
  precisar, pueden sumarse `2D` y/o el brand `EduFEM`. **Pendiente del autor:** verificar
  el reglamento de cambio de título y obtener aval escrito del director.
- **"Análisis estructural" acotado:** el término del título se define en *Alcance y
  limitaciones* (cap. 01) como análisis tenso-deformacional de medios continuos 2D
  (elasticidad plana), excluyendo tipologías discretas (pórticos, reticulados), placas,
  cáscaras y 3D. No reintroducir el término como descriptor sin esa acotación.
- **Metodología + Variables:** la introducción resume la metodología (propositiva ·
  aplicada tecnológica · cuantitativa en V&V); el detalle vive en §2.1 con seis subsecciones
  que siguen el diagrama del modelo de investigación del tribunal (modelo de simulación
  numérica, variables `tab:variables`, matriz de consistencia `tab:consistencia`, casos de
  estudio, procedimiento e instrumentos, criterios de aceptación). **No reintroducir** los
  subtítulos de diseño experimental (sistema de control / repetición / protocolo): se
  quitaron el 2026-09-07 a pedido del autor. La parte de software es §2.2.
- **Objeto/campo, problema y delimitación (2026-09-08):** objeto de estudio = el análisis
  de medios continuos en elasticidad plana por el MEF (técnico); campo de acción = su
  enseñanza (software + memoria). El problema científico tiene VI (forma de exponer el
  canal) y VD (observabilidad y contrastabilidad del procedimiento); el «apoyo a la
  comprensión» es el para qué, no lo medido. Delimitación institucional (Carrera de Ing.
  Civil UATF), espacial, temporal (gestión 2026) y disciplinar está en la Introducción. Son
  **seis** objetivos específicos (OE1 = fundamentación teórica → Cap. 1). Desde el 2026-09-16: OE2 sin «verificado
  numéricamente», OE4 acotado a «hasta el ensamblaje, con post-proceso y memoria para solución y
  tensiones», OE6 con la memoria como principal e interoperabilidad instrumental, y el objetivo
  general nombra Python (el «cómo» del título). No volver al
  objeto «proceso de enseñanza-aprendizaje» ni a cinco objetivos sin decisión del autor.
- **Validación: por diseño.** El eje es la V&V numérica (MMS, Timoshenko vs. SAP2000, Cook);
  la dimensión pedagógica se fundamenta en la literatura (§1.2 «Fundamentos pedagógicos», desde
  el 2026-09-16). La **hipótesis de diseño** se enuncia desde esa fecha en forma condicional
  comprobable —tres cláusulas con criterios a priori en §2.1.6— y el «apoyo al aprendizaje» es
  un supuesto declarado, no contrastado. **No** se hace validación por
  juicio de expertos. Un **piloto con estudiantes** queda como contingencia solo si lo
  solicitan en la defensa final (limpio).
- **Idioma:** español neto. Se permiten glosas de términos técnicos con el inglés entre
  paréntesis/cursiva (*shear-locking*, *hourglass*, *stretch*, *fill-in*…). Terminología
  canónica (GDL, MEF, etc.): ver la tabla del `CLAUDE.md` de la raíz del repo.
- **Defensas:** dos instancias — **borrador** y **limpio** (final).

## Estructura

```
tesis/
├── main.tex                 # documento maestro (metadatos de portada + \input de todo)
├── preambulo.tex            # paquetes y configuración (presentación APA + biblatex Vancouver)
├── portada/
│   └── portada.tex          # portada (usa los placeholders de main.tex)
├── main_v2.tex              # misma tesis en Arial (xelatex); lee capitulos/
├── main_v3.tex              # tesis con eje pedagógico (alternativa C); lee capitulos_v3/ + capitulos/
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
├── capitulos_v3/            # solo los capítulos que la v3 reescribe (resumen, nomenclatura,
│                            # introducción, cap. 1, §2.1, cap. 3, conclusiones)
├── bibliografia/
│   ├── referencias.bib      # referencias en biblatex (v1, v2 y v3)
│   ├── referencias_v3.bib   # 16 entradas que solo carga main_v3.tex (ejemplares pendientes)
│   └── *.pdf                # ejemplares consultados (gitignored: copyright)
├── normas/                  # las dos normas que rigen el documento
│   ├── guia_vancouver.tex/.pdf   # citas y referencias (propia, se versiona)
│   └── Tavares 2020 - ...pdf     # guía APA de terceros (gitignored: copyright)
├── respaldo_citas/          # qué página respalda cada cita + scripts
├── figuras/                 # imágenes (se versionan)
├── presentacion/            # defensa: guion.json + build_deck.py -> Defensa_EduFEM.pptx (ver su README)
└── .gitignore               # ignora artefactos de compilación
```

## Cuatro versiones del mismo documento

**La v4 (2026-09-19) es la candidata a reemplazar a la v1**: aplica la alternativa 3 elegida
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

Desde la carpeta `tesis/`. **v1 va con `pdflatex`; v2 va con `xelatex`** — v2 usa la
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

1. **Completar los placeholders de portada** en `main.tex` (`\universidad`, `\autorTesis`,
   `\directorTesis`, `\carrera`, `\gradoTesis`, `\ciudadTesis`, `\anioTesis`, y el título
   si querés ajustarlo).
2. Reemplazar cada `\figpend{...}` por la figura real con
   `\includegraphics[width=...]{figuras/nombre}`.
3. Resolver los `% DATO PENDIENTE`, `% CITA PENDIENTE` y `\pendiente{...}`.

## Skills de ayuda (Claude Code)

- `tesis-redactar` — redactar/ampliar secciones en español claro y natural.
- `tesis-revisar` — revisar y pulir borradores (claridad, terminología, citas, LaTeX).
- `tesis-bibliografia` — agregar/gestionar referencias Vancouver correctamente.
