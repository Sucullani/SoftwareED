---
name: tesis-bibliografia
description: Agrega y gestiona referencias de la tesis de EduFEM en biblatex/Vancouver (convencion de claves, campos obligatorios por tipo, sin DOIs/ISBNs inventados, como citar y compilar). Usar al anadir o corregir bibliografia en tesis/bibliografia/referencias.bib.
---

# Bibliografia de la tesis (biblatex + biber, estilo Vancouver)

Todas las referencias viven en `tesis/bibliografia/referencias.bib`. El estilo es
**Vancouver**: citas numericas por orden de aparicion, lista de referencias numerada.
El preambulo (`tesis/preambulo.tex`) ya carga biblatex con biber.

## Convencion de claves

- Formato `apellidoAnoPalabra`, en minusculas: `zienkiewicz2013fem`, `cook1974membrane`,
  `harris2020numpy`, `timoshenko1970elasticity`.
- Unicas y estables: si cambias una clave, actualiza todas las `\autocite` que la usan.

## Campos por tipo (minimos correctos)

- `@book`: author, title, year, publisher; (edition, address, isbn si se confirman).
- `@article`: author, title, journaltitle, year, volume, number, pages; (doi si se confirma).
- `@inproceedings`: author, title, booktitle, year, pages; (publisher, address).
- `@techreport`: author, title, institution, year, number.
- `@manual`: title, organization/author, year; (version).

## Reglas

- **No inventes DOIs, ISBNs ni numeros de pagina.** Si no podes confirmarlos, omite el campo.
  Es preferible una entrada con menos campos pero correcta.
- Nombres completos de autores (`Apellido, Nombre and Apellido2, Nombre2`); biblatex se
  encarga del formato Vancouver (iniciales tras apellido, "et al." segun corresponda).
- Protege mayusculas significativas en titulos con llaves: `{NumPy}`, `{SciPy}`, `{MEF}`.
- Encoding UTF-8 en el `.bib`.

## Como citar en el texto

- `\autocite{clave}` para una cita; `\autocite{clave1,clave2}` para varias (biblatex las
  compacta en rango numerico, p.ej. [3-5]).
- Cita donde respalda una afirmacion (teoria, dato externo, metodo), no en cada oracion.

## Compilacion (MiKTeX/Windows)

Desde `tesis/`:

```
pdflatex main
biber main
pdflatex main
pdflatex main
```

Usa **biber**, no bibtex (biblatex moderno lo requiere). Si una cita sale como `[?]` o
`(autor desconocido)`, falta correr biber o la clave no existe en el `.bib`.

## Nucleo de referencias esperado

MEF: Zienkiewicz & Taylor, Bathe, Cook-Malkus-Plesha-Witt, Hughes, Reddy, Onate.
Elasticidad: Timoshenko & Goodier. V&V: Roache, Oberkampf & Roy, MMS (Salari & Knupp),
benchmark de Cook (1974). Calidad de malla: reporte Verdict (Sandia). Stack cientifico:
Harris et al. (NumPy), Virtanen et al. (SciPy). Educacion en ingenieria: 2-4 articulos
reales. Validacion: manual de SAP2000 (CSI).
