# Version 2 de la tesis: cuerpo en Arial 12, formulas en LaTeX

**Fecha**: 2026-09-16 · **Estado**: implementado y verificado, sin commit

Pedido del autor: *«una version 2 de mi documento con fuente arial 12, las formulas
que se queden en latex»*. Decisiones tomadas con el autor: **Arial real** (no un clon
de Helvetica) y **archivo aparte** (no reemplazar la v1).

## Como quedo

| | v1 | v2 |
|---|---|---|
| Fuente | `main.tex` → Latin Modern 12 pt | `main_v2.tex` → **Arial 12 pt** |
| Motor | `pdflatex` + biber | **`xelatex`** + biber |
| Formulas | Latin Modern Math | **Latin Modern Math (identicas)** |
| Paginas | 158 | 161 |

`main_v2.tex` **no duplica nada**: define `\tesisFuenteArial` y carga el mismo
`preambulo.tex`, los mismos `capitulos/` y la misma bibliografia. Editar un capitulo
actualiza las dos versiones. Verificado: los dos PDF tienen las mismas 90 entradas de
indice, 31 figuras, 31 tablas y 29 ecuaciones numeradas, y v1 quedo **intacta en su
texto, pagina por pagina**, despues de los cambios al preambulo compartido.

Va con xelatex porque es lo unico que puede usar la Arial de `C:\Windows\Fonts`.
Comprobado en el PDF: las fuentes embebidas son `ArialMT`, `Arial-BoldMT` y
`Arial-ItalicMT`, y junto a ellas siguen `LMMathItalic12`, `LMMathSymbols10` y
`LMMathItalic10-Bold`, que son las formulas.

## Tres cosas que hubo que arreglar, y que no son obvias

### 1. babel-spanish rompe los \caption con formulas bajo XeLaTeX

`! Argument of \es@a has an extra }.` — abortaba la compilacion en el Anexo B.
babel-spanish redefine `\max`, `\min`, `\lim` e `\inf` para que impriman **acentuados**
("max", "min"...), y elige la implementacion segun el motor. La que reserva para XeLaTeX
(`\es@op@ac@TU`, activada porque ahi existe el primitivo `\Umathchar`) no sobrevive a la
expansion que hace `\caption` al escribir el rotulo en el `.lof`. La rama base —la que
usa pdflatex, o sea la que ya produce `main.pdf`— si.

El parche esta en `preambulo.tex`, condicionado a `\ifdefined\XeTeXversion`. Medido: con
el `\let`, el texto extraido del PDF es **identico** al de pdflatex. La alternativa
`\unaccentedoperators` tambien evita el error, pero deja los operadores sin acento.

### 2. La monoespaciada NO puede ser Consolas

Con Consolas, el codigo del Anexo C sale con `U+2010 HYPHEN` en vez del guion ASCII, y
con `Ligatures=TeX` global ademas con `U+201D` en vez de la comilla recta: lo que el
tribunal copia del PDF **ya no es Python valido**. Se queda en **Latin Modern Mono**, la
misma de la v1, con la que el texto extraido no tiene un solo caracter espurio.
Corolario: `Ligatures=TeX` va solo en las familias de texto, nunca en la mono.

### 3. Los indices necesitan permiso de guion

Arial es mas ancha que Latin Modern y el preambulo prohibe los guiones (APA). En el
indice no hay bandera derecha que absorba el sobrante —el relleno de puntos llega hasta
el numero de pagina—, asi que a TeX solo le quedaba meter la palabra en el margen: 8 pt
(2,8 mm) la entrada del capitulo 2 y una de la lista de figuras. Se les permite el guion
dentro del `\@starttoc` parcheado, con los mismos valores que ya usaban las celdas `p{}`.
**Aplica a las dos versiones y se verifico que v1 no cambia** (TeX solo corta cuando lo
necesita, y con Latin Modern no lo necesitaba).

## Estado de margenes (medido sobre el PDF, no sobre los warnings del log)

| | v1 | v2 |
|---|---|---|
| Paginas con texto fuera del margen | 27 | **13** |
| Overfull > 5 pt | 0 | **0** |

v2 tiene **menos** invasiones que v1. Las 27 de v1 son casi todas el PDF de SAP2000 que
`pdfpages` embebe en el Anexo E, que trae sus propios margenes y no depende de la fuente.
Las unicas dos regresiones de v2 son de **2 pt (0,7 mm)**, en los rotulos "Tabla B.3" y
"Tabla D.1": invisibles a simple vista. Los 63 `Overfull` que quedan en el log de v2 son
todos de 1,4 pt (0,5 mm) y ninguno llega al margen.

## Pendiente

- **Revision visual del autor** sobre `main_v2.pdf`.
- Decidir cual de las dos versiones se entrega al tribunal. Si es la v2, conviene mirar
  si alguna figura conviene reescalar: el cuerpo crecio 3 hojas.
- `main_v2.pdf` esta en `.gitignore`, igual que `main.pdf` (los dos son regenerables).
