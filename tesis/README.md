# Tesis — EduFEM

Fuente LaTeX de la tesis sobre **EduFEM** (GUI educativa de elementos finitos 2D).
Idioma: español (babel).

**Dos normas, para dos cosas distintas** (2026-09-10):

- **Citas y referencias: Vancouver** (ICMJE + NLM). Estilo numérico secuencial implementado
  con `biblatex/numeric-comp` + `sorting=none` + `terseinits` (no existe un estilo
  `vancouver` cargado como tal). Los títulos de revista se escriben **completos**, no con la
  abreviatura ISO del NLM, por legibilidad en un documento en español, y el último autor se
  separa con «y» en vez de coma: las dos son decisiones tomadas, no descuidos.
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
  **seis** objetivos específicos (OE1 = fundamentación teórica → Cap. 1). No volver al
  objeto «proceso de enseñanza-aprendizaje» ni a cinco objetivos sin decisión del autor.
- **Validación: por diseño.** El eje es la V&V numérica (MMS, Timoshenko vs. SAP2000, Cook);
  la dimensión pedagógica se fundamenta en la literatura. **No** se hace validación por
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
├── capitulos/
│   ├── 00_resumen.tex
│   ├── 01_introduccion.tex
│   ├── 02_marco_teorico.tex            # Capítulo 1
│   ├── 03_diseno_implementacion.tex    # Capítulo 2
│   ├── 04_resultados.tex               # Capítulo 3
│   ├── 05_conclusiones.tex
│   └── 06_anexos.tex
├── bibliografia/
│   ├── referencias.bib      # referencias en biblatex
│   └── *.pdf                # ejemplares consultados (gitignored: copyright)
├── normas/                  # las dos normas que rigen el documento
│   ├── guia_vancouver.tex/.pdf   # citas y referencias (propia, se versiona)
│   └── Tavares 2020 - ...pdf     # guía APA de terceros (gitignored: copyright)
├── respaldo_citas/          # qué página respalda cada cita + scripts
├── figuras/                 # imágenes (se versionan)
└── .gitignore               # ignora artefactos de compilación
```

## Compilar (MiKTeX en Windows)

Desde la carpeta `tesis/`:

```
pdflatex main
biber    main
pdflatex main
pdflatex main
```

O, más simple, con latexmk:

```
latexmk -pdf main.tex
```

> Usa **biber** (no bibtex). Si las citas salen como `[?]`, faltó correr biber o la
> clave no existe en `referencias.bib`.

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
