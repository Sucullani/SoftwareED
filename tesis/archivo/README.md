# Archivo — versiones anteriores de la tesis

Versiones que precedieron a la vigente (**final4**, `../main_final4.tex` → `../main_final4.pdf`).
**No se mantienen**: se guardan como registro de cómo evolucionó el trabajo. Las v1 a v4 se movieron
aquí el 2026-09-23; las finales anteriores (final, final1 y final2), el 2026-09-27, y final3, el
2026-10-20, para que en `tesis/` quede solo la versión vigente.

| Carpeta | Versión | Fecha | Qué es | PDF |
|---|---|---|---|---|
| `final3/` | final3 (`main_final3.tex` + `capitulos_final3/`) | 2026-09-25 | Observaciones del Ing. Miranda; la versión de la **defensa de borrador**. Se compila con XeLaTeX. Registro: `../auditoria_final/IMPLEMENTACION-FINAL3.md` | `main_final3.pdf` (189 p.) |
| `final2/` | final2 (`main_final2.tex` + `capitulos_final2/`) | 2026-09-25 | Segunda iteración de mejora de la final: verificación de final1 y revisión por unidades, con el retiro de PyMuPDF. Registro: `../auditoria_final/IMPLEMENTACION-FINAL2.md` | `main_final2.pdf` (197 p.) |
| `final1/` | final1 (`main_final1.tex` + `capitulos_final1/`) | 2026-09-23 | La final con la auditoría de redacción implementada. Registro: `../auditoria_final/IMPLEMENTACION-FINAL1.md` | `main_final1.pdf` (194 p.) |
| `final/` | final (`main_final.tex` + `capitulos_final/` + `preambulo.tex`) | 2026-09-21 | La versión entregada y auditada (commit `ee7b5a6`), base de comparación de las iteraciones | `main_final.pdf` (187 p.) |
| `v4/` | v4 (`main_v4.tex`) | 2026-09-19 | «caja negra → bajo criterio» (alternativa 3); incluye su auditoría de redacción, `auditoria_v4/` | `main_v4.pdf` (168 p.) |
| `v3/` | v3 (`main_v3.tex`) | 2026-09-18 | pedagógico (alternativa C: comprensión del estudiante, investigación basada en diseño); `referencias_v3.bib` con sus 16 entradas propias | `main_v3.pdf` (178 p.) |
| `v1_v2/` | v1 (`main.tex`) y v2 (`main_v2.tex`, el mismo texto en Arial con `xelatex`) | anterior al 2026-09-18 | primera línea completa de la tesis; `capitulos/` es la base que v3 y v4 reutilizan | `main.pdf` (158 p.), `main_v2.pdf` (161 p.) |

Las notas de cada una siguen en `docs/notas/` (`2026-09-18_tesis-v3-eje-pedagogico.md`,
`2026-09-19_tesis-v4-alternativa-3.md`, `2026-09-21_tesis-final.md`,
`2026-09-25_observaciones-miranda-final3.md`). El diagnóstico de las observaciones del Ing. Miranda
(`../observaciones_miranda/diagnostico_miranda.tex`) lee sus figuras de
`final3/capitulos_final3/figuras/`.

## Recompilar una versión archivada

No hace falta: el PDF de cada una se conserva tal como se compiló. Si alguna vez hiciera falta, sus
rutas son relativas a `tesis/`, no a esta carpeta (`\input{portada/portada}`, `figuras/`,
`anexos/`…). La forma segura es trabajar sobre una copia de `tesis/`:

- **final1 y final2** son autocontenidas: copiar a la raíz de la copia su `.tex` principal y su
  carpeta de capítulos (que trae su propio `preambulo.tex`, su `referencias.bib` y sus figuras), y
  compilar con `latexmk -pdf`.
- **final3** se copia igual, pero se compila con `latexmk -xelatex main_final3.tex`: usa la Times
  New Roman real del sistema, y con `-pdf` se detiene con un mensaje que pide XeLaTeX.
- **final** usa además el `preambulo.tex` general y `bibliografia/referencias.bib`: copiar
  `final/main_final.tex`, `final/capitulos_final/` y `final/preambulo.tex` a la raíz de la copia.
- **v1 a v4** usan también ese `preambulo.tex` (hoy en `final/`), y v3 y v4 leen de `capitulos/`
  (hoy `v1_v2/capitulos/`) los capítulos que no reescriben: copiar también esa carpeta. El
  resultado puede no coincidir página a página con el PDF guardado.

La raíz de `tesis/` lleva un `latexmkrc` que manda los auxiliares a `build/`; en una copia vale
lo mismo.

`texput.log` es un registro de compilación suelto del 19 de septiembre, sin valor; git lo ignora.
