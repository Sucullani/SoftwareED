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

- `@book`: author, title, year, publisher; (edition, location, isbn si se confirman).
- `@article`: author, title, journaltitle, year, volume, number, pages; (doi si se confirma).
- `@inproceedings`: author, title, booktitle, year, pages; (publisher, location).
- `@techreport`: author, title, institution, year, number; (location).
- `@manual`: title, author **o** organization (nunca los dos: el driver imprime ambos y la
  editorial sale duplicada), year; (version).

Usa los nombres de campo de biblatex, no los alias legacy de BibTeX: `journaltitle` (no
`journal`) y `location` (no `address`).

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
Analisis matematico del metodo: Strang & Fix. Elasticidad: Timoshenko & Goodier.
V&V: Roache, MMS (Salari & Knupp), benchmark de Cook (1974). Calidad de malla: reporte
Verdict (Sandia). Stack cientifico: Harris et al. (NumPy), Virtanen et al. (SciPy).
Educacion en ingenieria: Bishay, Lee (x2), Perez-Santiago, Suarez (ED-Elas2D).
Validacion: manual de SAP2000 (CSI). Metodologia (unicas fuentes en espanol del .bib):
Alvarez de Zayas (objeto de estudio, campo de accion, problema cientifico, modelo teorico),
Hernandez-Sampieri y Mendoza 2018 (enfoque cuantitativo, variables, muestra dirigida) y
Garcia-Cordoba 2005 (investigacion tecnologica en ingenierias; la **hipotesis tecnologica**
de su p. 85 es la que sostiene que esta tesis plantee hipotesis de diseno y no estadistica).

**No volver a citar el material docente de la carrera** (`tesis/Material docente/`): se uso el
2026-09-08 y se retiro el 2026-09-09. Son diapositivas sin bibliografia —material terciario sin
fuentes— y uno de los dos docentes integra el tribunal del autor. El marco se cita en su origen.

Los PDF de los libros viven en `tesis/bibliografia/` y estan **gitignorados** (material con
copyright, repo publico). Sacar de ahi los metadatos: portada y pagina de creditos, nunca la web.
Para un localizador de pagina, **abrir el libro y leer el numero impreso**: el desfase entre
pagina del PDF y pagina impresa no es constante dentro de un mismo ejemplar.

**Antes de agregar una entrada nueva, agota este orden** (regla del 2026-09-08): (a) redirigir
la afirmacion a una fuente que ya esta en el .bib; (b) reescribirla para que se sostenga sola
—definir la formula en el texto, corroborar el dato con evidencia propia del trabajo—;
(c) sustituir la apelacion a una autoridad ausente por el argumento tecnico que esa autoridad
respaldaria; (d) reconocer explicitamente el limite de la revision. Solo si nada de eso aplica,
entrada nueva. La bibliografia de esta tesis es corta a proposito y cada entrada tiene >= 2 citas.

Oberkampf & Roy (2010) se retiro el 2026-09-08: sus 5 citas eran un subconjunto estricto de
las de Roache y no sostenia ninguna afirmacion propia. **No reintroducir** sin un pasaje que
use lo que aporta de distinto (cuantificacion de incertidumbre, metricas de validacion).
