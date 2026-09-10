# La tesis se presenta en APA 7 y sigue citando en Vancouver

**2026-09-10** · Toca `tesis/preambulo.tex`, `tesis/bibliografia/referencias.bib`,
`tesis/normas/`, `.claude/skills/tesis-bibliografia/SKILL.md`.

## Qué se decidió

Dos normas distintas gobiernan dos cosas distintas, y no chocan:

| Qué | Norma | Dónde vive |
|---|---|---|
| Citas y lista de referencias | **Vancouver** (ICMJE + NLM) | bloque biblatex de `preambulo.tex` |
| Presentación del documento | **APA 7.ª ed.** | bloque APA de `preambulo.tex` |

APA no dice nada sobre cómo se escribe una referencia numérica; Vancouver no dice nada
sobre márgenes ni interlineado. La guía de las citas es
[tesis/normas/guia_vancouver.pdf](../../tesis/normas/guia_vancouver.pdf).

## Lo que APA pide y NO se aplicó, con su motivo

Son decisiones del autor. **No las "corrijas" a la letra de APA sin preguntarle.**

- **Papel A4, no carta.** APA especifica 21,59 × 27,94 cm. Se conserva A4: es el papel de
  la región y el de la carátula ya impresa. Los márgenes sí son los de APA.
- **Títulos numerados.** APA dice «no etiquete los títulos y subtítulos con números o
  letras». La tesis conserva `Capítulo 1`, `1.1`, `1.1.1` porque tiene ~50 referencias
  cruzadas `\autoref{cap:...}` y porque el tribunal espera capítulos numerados. Lo que se
  adoptó es la **tipografía** de cada nivel, no la supresión del número.
- **Latin Modern 12, no Times New Roman 12.** APA acepta «Computer Modern normal (10 pt),
  la fuente predeterminada en LaTeX»; a 12 pt no es literal la norma, pero es la familia
  admitida y no toca ni una fórmula. `newtx` está instalado si alguna vez se quiere Times
  con matemática a juego.
- **Títulos en mayúscula de oración, no en Title Case.** APA pide «Cada Palabra Iniciando
  en Mayúscula». En español eso contradice la ortografía de la RAE, y son ~90 títulos.
  Queda como decisión abierta del autor.

## Trampas encontradas

- **`ragged2e` pone `\parindent` en cero.** Al activar `\RaggedRight` la sangría de primera
  línea desaparece, que es justo lo contrario de lo que pide APA. Se restituye con
  `\setlength{\RaggedRightParindent}{1.27cm}`, no con `\setlength{\parindent}{...}`.
- **Los rótulos de figura no hacen falta moverlos a mano.** APA los quiere arriba de la
  imagen y los 29 entornos `figure` de los capítulos traen el `\caption` al final.
  `\floatstyle{plaintop}` + `\restylefloat{figure}` lo resuelve desde el preámbulo. No
  editar los capítulos para esto.
- **El doble espacio costó 12 hojas, no 45.** Medido: original 131 · APA a 1,5 → 120 ·
  APA a doble → 143. El margen de 2,54 cm ensancha la caja de texto y compensa casi todo.
  El interlineado es una línea en `preambulo.tex` si el autor quiere volver a 1,5.
- **Tablas, `longtable` y `lstlisting` van a espacio sencillo** vía
  `\AtBeginEnvironment`. APA admite la excepción para tablas y figuras; el código se sumó
  por el mismo motivo (a doble espacio un fragmento de Python es ilegible).

## Vancouver: lo que se corrigió el mismo día

Auditadas las 22 entradas del `.bib` contra la norma. Tres defectos reales:

1. **`Bathe K.-J.` y `Ryu H.-R.`** en vez de `KJ` y `HR`. `biblatex` define
   `\bibinithyphendelim` como `.-` y los dos `\renewcommand` que había no lo alcanzaban.
   Lo cubre la opción **`terseinits=true`**, que fija los tres delimitadores.
2. **Faltaba `location`** en `cook2002concepts` (→ `Hoboken (NJ)`, leído de la página de
   créditos), `csi2017sap2000` (→ `[Estados Unidos]`, inferido y entre corchetes porque el
   manual no trae ciudad) y `alvarez_metodologia` (→ los tres corchetes de dato
   desconocido). Además los estados de EE.UU. pasaron a paréntesis, que es la forma NLM:
   `Upper Saddle River (NJ)`, no `Upper Saddle River, NJ`.
3. **El manual de CSI salía sin editorial.** En `@manual` biblatex imprime `organization`,
   no `author`. La organización va ahora dos veces, que es lo que pide el NLM cuando una
   entidad publica su propia obra. La regla vieja de la skill decía lo contrario y se
   corrigió.

Lo que **no** se tocó, por ser decisión documentada: títulos de revista completos en vez de
abreviados, y «y» como último separador de autores en lugar de coma.

## El PDF de APA que trajo el autor

`tesis/normas/Tavares 2020 - Guia Normas APA 7a edicion (normas-apa.org).pdf` **no es la
norma oficial**: es una compilación de `normas-apa.org` (Word 2016, mayo de 2020, autor de
metadatos «Pedro Tavares»). Se coteja punto por punto contra `apastyle.apa.org` y coincide
en todo lo de formato; el único desfase es que su lista de fuentes admitidas no incluye
**Aptos 12**, que APA agregó después de 2020. Está gitignorado por copyright, igual que los
papers de `tesis/bibliografia/`.
