# Observaciones del Ing. Miranda → tesis final3

**Fecha**: 2026-09-25 · **Autor**: agente (Claude Code), a pedido del autor · **Estado**: terminado (espera la revisión del autor)

## Qué se pedía

El Ing. Julio Saúl Miranda (tribunal) dejó sugerencias rápidas sobre causa y efecto, problema,
objetivo general, objetivos específicos, hipótesis, conclusiones y formato. Luego sumó otra:
«Diagnosticar» no corresponde como objetivo. El autor pidió un diagnóstico de cada una y
aplicarlas **adaptadas** al contenido de la tesis, no al pie de la letra, sobre la última versión
(final2). Pidió además documentos para revisar, unificar el PDF de final2 (`main_final2_build.pdf`
→ `main_final2.pdf`) y recoger en final3 el retiro de PyMuPDF que otra sesión hacía a la vez.

## Qué se hizo

- **final3** (`tesis/main_final3.tex` + `tesis/capitulos_final3/`). Qué cambió y por qué, fila
  por fila: `tesis/auditoria_final/IMPLEMENTACION-FINAL3.md` (M-01…M-14). Diagnóstico para el
  autor: `tesis/observaciones_miranda/diagnostico_miranda.pdf`. Los enunciados exactos están en
  `capitulos_final3/CRITERIOS.md` §1.
- Figuras nuevas con `tesis/figuras/generar_figuras_formulacion.py`, que lee `docs/vyv/datos/`
  y comprueba contra la tabla de veredicto antes de dibujar.
- Formato: XeLaTeX con la Times New Roman real del sistema (mecanismo de la versión Arial,
  [2026-09-16_tesis-version-arial.md](2026-09-16_tesis-version-arial.md)) y texto justificado.

## Qué se descartó y por qué

- **«nula» transparencia** (literal de Miranda): la Tabla 1.1 registra «Baja (caja negra)» y
  ED-Elas2D sí expone matrices; bastaría un contraejemplo para refutar el problema. Quedó
  «escasa».
- **«¿Cómo… genera…?»**: da la causalidad por supuesta. Quedó el molde de su propia lámina
  PP 10, «¿De qué manera… podrá incidir en…?».
- **Cuatro objetivos (Caso II literal, OG 14)**: llevaría la verificación al Cap. 2, sacaría el
  MMS del capítulo de resultados y partiría la evidencia de la cláusula (b). Quedaron tres, uno
  por capítulo.
- **Llamar a la VI «grado» de transparencia**: choca con §2.1.2, donde la comparación es de
  presencia frente a ausencia. Se la definió como la *exposición* que el software hace del
  procedimiento.
- **Títulos híbridos** (verbo del objetivo más la palabra del índice del Taller 1) y **títulos
  cortos solo del verbo** («Desarrollo de EduFEM»): el autor pidió después que cada título sea su
  objetivo completo, aunque sea largo, porque Miranda le dijo «tus objetivos definen tus
  capítulos». Es además su procedimiento en OG 6, que saca el título de la tesis del objetivo
  general entero. La correspondencia con el índice de Barrios se dice en una oración de la
  «Estructura del documento».
- **Fórmulas en Times (`newtxmath`)**: el autor eligió Latin Modern. Además, los mapas de fuentes
  de pdfTeX del usuario (`AppData/Local/MiKTeX/.../pdftex.map`, de abril) no tienen entradas de
  newtx: habría que correr `initexmf --mkmaps`.
- **pdflatex con un clon de Times (newtx)**: no es la Times New Roman que se pidió, y tiene el
  mismo problema de mapas.
- **Numerar los visuales de las Conclusiones «C.1»**: choca con el Anexo C. Quedó «CR.1».
- **Poner la Figura 2.1 en la Introducción**: en un `\chapter*` antes del Cap. 1 saldría «Figura
  0.1». Va en §2.1.2 y la Introducción remite a ella.

## Trampas encontradas

- **XeLaTeX + `listings`**: `literate` no se aplica a caracteres por encima de U+00FF. En el
  Anexo C salían 34 «Missing character» (∂, ε, γ, σ en Latin Modern Mono), es decir, símbolos en
  blanco. Se arregla con `newunicodechar` → `\ensuremath{…}`, cargado **después** del
  `\lstdefinestyle`: si los caracteres ya son activos al leer `literate`, su lista se rompe.
- **Quitar `ragged2e[document]` justifica también las celdas `p{}` sin `\raggedright`**
  (Nomenclatura, Anexos B y F): aparecieron 25 renglones flojos. Se parcheó
  `\@arrayparboxrestore` con `\RaggedRight`. En esta tesis el único `\parbox` es el de
  `\figpend`, que se centra solo.
- **Numeración «CR» en un `\chapter*`**: hay que redefinir también `\theHfigure` y `\theHtable`
  (destinos de hyperref), y encerrar el capítulo en un grupo. El primer `\chapter` de los Anexos
  vuelve a poner los contadores en cero.
- **Tasas del MMS en el gráfico logarítmico**: `mms_resumen.csv` trae el Q9 en 3,000 y la
  desviación daría 0. Se recalculan con precisión completa a partir de las normas del error, entre
  N = 16 y N = 32.
- **PDF bloqueado por el visor**: con `main_final2.pdf` abierto, latexmk falla al escribirlo. Por
  eso existía `main_final2_build.*`, que se unificó con `main_final2.*`.
- **Consola cp1252**: `grep` desde Bash no encuentra textos con tildes. Usar la herramienta Grep
  o Python.
- **Dos sesiones a la vez**: otra sesión editó `capitulos_final2/` (05:50-05:55) **después** de
  que se copiara a final3 (05:46). Se detectó al comparar la instantánea sha256 de final2, y se
  coordinó por mensajes entre sesiones. Las cinco ediciones (R2-Z01..Z05) se llevaron a final3
  con la misma redacción.

## Qué quedó pendiente

- **Revisión del autor** de `main_final3.pdf` y del diagnóstico; en particular, aceptar los
  cinco ajustes a las sugerencias.
- **Reglamento de Graduación (H-1)**: confirmar interlineado y márgenes, que siguen APA
  (doble espacio y 2,54 cm).
- **Presentación y video de defensa**: siguen `main_final.tex` y no tienen la formulación nueva.
- **Hash de la revisión del instalador** sin PyMuPDF: hay un `% DATO PENDIENTE` en §2.1.1.
- Sin commit.

## Verificación

- `latexmk -xelatex main_final3.tex`: 189 páginas con los títulos largos de capítulo (188 antes), 0 errores, 0 `Overfull`, 0 referencias o
  citas indefinidas, 0 `Missing character`, 0 destinos duplicados, 1 `Underfull` (nota al pie
  con `MMD_AT_PLUS_A`).
- `pdffonts`: TimesNewRomanPSMT (normal, negrita, cursiva y negrita cursiva), Arial en
  `\textsf`, LM Math y LM Mono.
- Script de coherencia (en el scratchpad de la sesión):
  - problema, objetivo general e hipótesis idénticos en la Introducción, §2.1.3 y `CRITERIOS.md`;
  - palabras: 32, 41 y 29, y 29/28/34 en los objetivos;
  - `tab:consistencia` con 3 filas y la columna OE de `tab:dsrm` en {1, 2, 3, ---};
  - 153 etiquetas intactas más 4 nuevas; sin claves bibliográficas nuevas; 18/18 cifras clave;
  - oraciones de más de 60 palabras: de 24 a 19.
- Revisión visual (`pdftoppm`) de la Introducción, la Figura 2.1, las Conclusiones, la Tabla CR.1
  y el índice de figuras. PyMuPDF no se usó: el autor lo está retirando.
- `pdflatex` sobre `main_final3.tex` se detiene con el mensaje que pide XeLaTeX (comprobado).
- `diagnostico_miranda.pdf`: 8 páginas, 0 errores, 0 desbordes.
