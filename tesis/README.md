# Tesis — EduFEM

Fuente LaTeX de la tesis sobre **EduFEM** (GUI educativa de elementos finitos 2D).
Formato de referencias: **Vancouver** (biblatex + biber). Idioma: español (babel).

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
