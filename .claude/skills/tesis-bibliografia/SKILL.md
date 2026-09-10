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

- `@book`: author, title, **location**, publisher, year; (edition, isbn si se confirman).
- `@article`: author, title, journaltitle, year, volume, number, pages; (doi si se confirma).
- `@inproceedings`: author, title, booktitle, year, pages; (publisher, location).
- `@techreport`: author, title, **location**, institution, year, number.
- `@manual`: author (la organizacion), title, **organization** (la misma, otra vez),
  location, year.

`location` es **obligatorio** en libros, informes y manuales: Vancouver exige el lugar de
edicion. Si la portada no lo trae, buscalo en la pagina de creditos del ejemplar.

En `@manual` la organizacion va **dos veces**: en `author` y en `organization`. Es lo que
pide Vancouver/NLM cuando una entidad publica su propia obra ("Chicago: The Association");
sin `organization` la referencia sale sin editorial. La regla vieja decia lo contrario
--nunca los dos-- y estaba mal: se corrigio el 2026-09-10 al auditar el .bib contra la norma.

Cuando el ejemplar no consigna un dato obligatorio, Vancouver no permite omitirlo en
silencio: se declara entre corchetes (`[lugar desconocido]`, `[editorial desconocida]`,
`[fecha desconocida]`). La fecha no puede ir en `year` --biber la parsea y la descarta con
aviso--: se pega a `publisher`, que es lo que la cierra en el renglon correcto.

Usa los nombres de campo de biblatex, no los alias legacy de BibTeX: `journaltitle` (no
`journal`) y `location` (no `address`).

## Reglas

- **No inventes DOIs, ISBNs ni numeros de pagina.** Si no podes confirmarlos, omite el campo.
  Es preferible una entrada con menos campos pero correcta.
- **El fasciculo de un articulo puede no estar en la cita del editor y estar igual en el PDF.**
  En Perez-Santiago la cita impresa dice solo "Comput Appl Eng Educ. 2023;31:1159-1173", pero
  la marca de agua de descarga de Wiley, en 14 de sus 15 paginas, dice "10990542, 2023, 5".
  Antes de declarar que un campo "no figura en el ejemplar", buscalo tambien en la marca de
  agua y en los metadatos del PDF (`fitz.open(x).metadata`). Se dio por ausente una vez y era
  falso.
- **Cuidado con concluir ausencia por busqueda de texto.** Cinco ejemplares son escaneo puro
  sin capa de texto (Bathe, Cook, Garcia-Cordoba, Hughes, Reddy) y Suarez es hibrido: ahi
  `get_text()` devuelve cero para cualquier termino y eso no prueba nada. Verifica el numero
  de caracteres del PDF antes de afirmar que algo no esta, y si es escaneo, rasteriza la
  pagina y leela como imagen.
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
V&V: **Oberkampf & Roy 2010** y MMS (Salari & Knupp). Calidad de malla: reporte
Verdict (Sandia). Stack cientifico: Harris et al. (NumPy), Virtanen et al. (SciPy).
Educacion en ingenieria: Bishay, Lee (x2), Suarez (ED-Elas2D) y Perez-Santiago & Campos 2023.

**Bajas del 2026-09-09, por no disponer del ejemplar. No reintroducir sin conseguirlo:**
`roache1998verification` (lo cubre Oberkampf & Roy, que el autor si tiene) y
`cook1974membrane` (la atribucion de la membrana vive ahora en la prosa: **Cook 2002 NO
contiene ese caso**, se verifico pagina por pagina).

`perezsantiago2023fem` estuvo de baja unas horas y **volvio**: el autor consiguio el PDF. Las
cuatro fuentes que lo habian reemplazado (Linero 2012 y tres ponencias ASEE) se retiraron —
inflaban la bibliografia sin necesidad. **No reintroducirlas.**

**Las entradas del .bib describen el ejemplar que el autor tiene**, no la edicion mas reciente:
Zienkiewicz es la 6.a de 2005, Bathe la de Prentice Hall 1996, Strang la de Prentice-Hall 1973,
Timoshenko la 2.a de 1951 y Hughes la de Prentice-Hall 1987. Las claves conservan el ano viejo
(`zienkiewicz2013fem`, `bathe2014fem`...) a proposito, para no tocar las 78 citas; con estilo
numerico el lector nunca ve la clave. **No las "corrijas" al ano de la clave.**
Validacion: manual de SAP2000 (CSI). Metodologia (unicas fuentes en espanol del .bib):
Alvarez de Zayas (objeto de estudio, campo de accion, problema cientifico, modelo teorico),
Hernandez-Sampieri y Mendoza 2018 (enfoque cuantitativo, variables, muestra dirigida) y
Garcia-Cordoba 2005 (investigacion tecnologica en ingenierias; la **hipotesis tecnologica**
de su p. 85 es la que sostiene que esta tesis plantee hipotesis de diseno y no estadistica).

**No volver a citar el material docente de la carrera** (`tesis/Material docente/`): se uso el
2026-09-08 y se retiro el 2026-09-09. Son diapositivas sin bibliografia —material terciario sin
fuentes— y uno de los dos docentes integra el tribunal del autor. El marco se cita en su origen.

Los PDF de los libros viven en `tesis/bibliografia/` con el nombre `Autor ANO - Titulo.pdf` y
estan **gitignorados** (material con copyright, repo publico). Sacar de ahi los metadatos:
portada y pagina de creditos, nunca la web.

**Las citas del cuerpo van en Vancouver puro: `\autocite{clave}`, sin `[p.~NN]`** (decision del
autor, 2026-09-09). La pagina y el pasaje que respalda cada cita viven en
`tesis/respaldo_citas/respaldo_citas.tex`, un documento aparte que acompana a la tesis. Si se
agrega o cambia una cita, actualizar ahi el respaldo. **No reintroducir localizadores en el
cuerpo** sin decision del autor.

Si alguna vez hiciera falta una pagina, **abrir el libro y leer el numero impreso**: el desfase
entre pagina del PDF y pagina impresa no es constante dentro de un mismo ejemplar (en Sampieri
va de -41 a -43; en Garcia-Cordoba, de -2 a -4; en Oberkampf salta de +16 a +24 en la pagina
impresa 371). Para eso esta `tesis/respaldo_citas/paginas.py`, que construye el mapa leyendo el
folio de cada pagina en vez de suponer un desfase: `python paginas.py <ruta.pdf> 13 749`.

## Pipeline del respaldo de citas

Tres scripts versionados en `tesis/respaldo_citas/`, todos leen el `verificado.json` de ahi
mismo (no de un temporal de sesion):

- `paginas.py` --- mapa pagina impresa <-> pagina del PDF.
- `resaltar.py` --- marca en amarillo los pasajes dentro de copias en
  `tesis/bibliografia/resaltados/` (gitignorado), dejando intactos los originales.
- `gen_respaldo.py` --- genera `respaldo_citas.tex` (luego `pdflatex` dos veces).

**Leer siempre el bloque `SIN MARCAR` que imprime `resaltar.py` al final.** Alvarez y Oberkampf
estuvieron seis pasadas sin copia marcada porque la version anterior saltaba en silencio las
fuentes cuyo archivo no encontraba y los respaldos sin pagina.

Cinco fuentes son **escaneo sin capa de texto** (Bathe, Cook, Garcia-Cordoba, Hughes, Reddy) y
Suarez es hibrido (texto en las paginas 1, 2 y 13; imagen en las 3-12). Ahi no se puede resaltar:
reciben una nota amarilla en la esquina. Eso es correcto, no un fallo que haya que arreglar.

**Antes de agregar una entrada nueva, agota este orden** (regla del 2026-09-08): (a) redirigir
la afirmacion a una fuente que ya esta en el .bib; (b) reescribirla para que se sostenga sola
—definir la formula en el texto, corroborar el dato con evidencia propia del trabajo—;
(c) sustituir la apelacion a una autoridad ausente por el argumento tecnico que esa autoridad
respaldaria; (d) reconocer explicitamente el limite de la revision. Solo si nada de eso aplica,
entrada nueva. La bibliografia de esta tesis es corta a proposito y cada entrada tiene >= 2 citas.

**Atribucion corregida el 2026-09-10** (auditoria de 60 agentes, informe en
`docs/notas/2026-09-09_diagnostico-bibliografia.md`): la clausula de `02_marco_teorico.tex:406`
sobre integrar las normas de error con un punto de Gauss mas por direccion citaba a
`salari2000mms`, y ese informe **no contiene las palabras "Gauss" ni "quadrature" ni una sola
vez**. El respaldo real es Oberkampf y Roy p. 320. La misma auditoria decidio NO reducir la
bibliografia: se propusieron 5 bajas, sobrevivieron 2 (`salari2000mms` y
`reddy2006introduction`) y el autor decidio **no ejecutarlas** ("quiza en un futuro").
No las reabras sin que lo pida.

Oberkampf & Roy (2010) estuvo de baja unas horas el 2026-09-08 y **volvio el 2026-09-09**,
como sustituto de Roache 1998 (que el autor no tiene). Hoy es una de las entradas mas
citadas del .bib, con 11 citas, y sostiene la distincion verificacion/validacion, el MMS, la
extrapolacion de Richardson y la cautela sobre las comparaciones codigo a codigo.
