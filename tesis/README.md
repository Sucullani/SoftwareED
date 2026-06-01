# Tesis — EduFEM

Fuente LaTeX de la tesis sobre **EduFEM** (GUI educativa de elementos finitos 2D).
Formato de referencias: **Vancouver** (biblatex + biber). Idioma: español (babel).

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
- **Metodología + Variables:** la introducción incluye *Metodología de la investigación*
  (aplicada · cuantitativa · explicativa; desarrollo iterativo-incremental + V&V) y
  *Variables* (tabla de operacionalización `tab:variables`).
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
├── preambulo.tex            # paquetes y configuración (biblatex Vancouver, \figpend, etc.)
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
│   └── referencias.bib      # referencias en biblatex
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
