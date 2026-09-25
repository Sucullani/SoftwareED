# Archivo — versiones anteriores de la tesis

Versiones que precedieron a la final (2026-09-21). **No se mantienen**: se guardan como registro
de cómo evolucionó el trabajo. Se movieron aquí el 2026-09-23 para que en `tesis/` quede solo la
línea de versiones finales (`main_final.tex`, `main_final1.tex`, …; ver `../README.md`).

| Carpeta | Versión | Fecha | Eje | PDF |
|---|---|---|---|---|
| `v1_v2/` | v1 (`main.tex`) y v2 (`main_v2.tex`, el mismo texto en Arial con `xelatex`) | anterior al 2026-09-18 | primera línea completa de la tesis; `capitulos/` es la base que v3 y v4 reutilizan | `main.pdf` (158 p.), `main_v2.pdf` (161 p.) |
| `v3/` | v3 (`main_v3.tex`) | 2026-09-18 | pedagógico (alternativa C: comprensión del estudiante, investigación basada en diseño); `referencias_v3.bib` con sus 16 entradas propias | `main_v3.pdf` (178 p.) |
| `v4/` | v4 (`main_v4.tex`) | 2026-09-19 | «caja negra → bajo criterio» (alternativa 3); incluye su auditoría de redacción, `auditoria_v4/` | `main_v4.pdf` (168 p.) |

Las notas de cada una siguen en `docs/notas/` (`2026-09-18_tesis-v3-eje-pedagogico.md`,
`2026-09-19_tesis-v4-alternativa-3.md`) y el porqué del paso a la versión final, en
`docs/notas/2026-09-21_tesis-final.md`.

## Recompilar una versión archivada

No hace falta: el PDF de cada una se conserva tal como se compiló. Si alguna vez hiciera falta,
hay que tener en cuenta que sus rutas son relativas a `tesis/`, no a esta carpeta:
`\input{preambulo}`, `\input{portada/portada}`, `\input{capitulos/...}` y
`bibliografia/referencias.bib`. Además, v3 y v4 leen de `capitulos/` (hoy `v1_v2/capitulos/`)
los capítulos que no reescriben. La forma segura es trabajar sobre una copia de `tesis/`:
copiar a su raíz el `.tex` principal de la versión, su carpeta de capítulos y, para v3 y v4,
también `v1_v2/capitulos/`, y compilar desde allí. El `preambulo.tex` actual es el de la versión
final, así que el resultado puede no coincidir página a página con el PDF guardado.

`texput.log` es un registro de compilación suelto del 19 de septiembre, sin valor; git lo ignora.
