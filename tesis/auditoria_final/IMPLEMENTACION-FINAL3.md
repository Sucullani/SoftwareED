# Implementación de la tercera iteración: versión final3

Registro de la versión **final3**, hecha el 25-09-2026 a pedido del autor. Aplica las
observaciones del Ing. Julio Saúl Miranda (tribunal), **adaptadas al contenido de la tesis** y no
al pie de la letra. El autor lo pidió así: *«no que sea el mismo; aplica según tu recomendación y
que esté alineado a la coherencia y contenido de la tesis»*.

- Versión nueva: `tesis/main_final3.tex` + `tesis/capitulos_final3/` (con su `preambulo.tex`,
  `referencias.bib`, `CRITERIOS.md` y tres figuras nuevas en `figuras/`).
- Diagnóstico de cada observación, para el autor:
  [`../observaciones_miranda/diagnostico_miranda.pdf`](../observaciones_miranda/diagnostico_miranda.pdf).
- Este trabajo no modificó `capitulos_final2/`. Otra sesión, a pedido del autor, aplicó sobre final2 el
  retiro de PyMuPDF (R2-Z01..Z05 en `IMPLEMENTACION-FINAL2.md`), y final3 lleva esas ediciones con
  la misma redacción (M-12).
- Para ver todo lo cambiado: `git diff --no-index tesis/capitulos_final2 tesis/capitulos_final3`.
- **Se compila con XeLaTeX**: `latexmk -xelatex main_final3.tex`.

## Estado final de final3

- Compila sin errores, sin desbordes y sin referencias ni citas indefinidas: **189 páginas** (final2:
  197). Eran 188 antes de los títulos largos de capítulo. Caracteres faltantes: 0. Destinos duplicados de hyperref: 0. Queda un renglón flojo: la
  nota al pie de §2.2 con el identificador `MMD_AT_PLUS_A`.
- Fuentes del PDF (`pdffonts`): Times New Roman en el texto (normal, negrita, cursiva y negrita
  cursiva), Arial en `\textsf`, Latin Modern en las fórmulas y Latin Modern Mono en el código.
- Etiquetas: las 153 de final2 siguen, más 4 nuevas (`fig:variables`, `fig:contraste-hipotesis`,
  `fig:margen-criterios`, `tab:triada`). No hay claves bibliográficas nuevas.
- Las 18 cifras clave siguen presentes. Oraciones de más de 60 palabras: bajan de 24 a 19, medidas
  con el mismo método en las dos versiones.
- Enunciados formales idénticos en la Introducción, en §2.1.3 y en `CRITERIOS.md`: problema (32
  palabras), objetivo general (41), hipótesis (29). Los objetivos específicos tienen 29, 28 y 34.

## Disposiciones

| ID | Observación | Disposición | Qué se hizo | Dónde |
|---|---|---|---|---|
| M-01 | Causa = transparencia/exposición; efecto = trazabilidad y verificabilidad del proceso interno | ADAPTADO | VI «transparencia del procedimiento de cálculo» (definida como la *exposición* que el software hace del procedimiento; no «grado», porque §2.1.2 dice que la comparación es de presencia frente a ausencia). VD «trazabilidad y verificabilidad del procedimiento de cálculo» («proceso» → «procedimiento», término canónico). Dimensión «Transparencia» de la VI → «Exposición de las etapas» | Intro «Variables»; §2.1.2; `tab:variables`; §3.1; Resumen |
| M-02 | Problema «¿Cómo una nula transparencia… genera…?» | ADAPTADO | Molde de PP 10 («¿De qué manera… podrá incidir en…?»); «escasa» y no «nula» (la Tabla 1.1 dice «Baja (caja negra)»; ED-Elas2D expone matrices); un solo término; «en la gestión 2026» | Intro «Formulación del problema»; §2.1.3; CRITERIOS |
| M-03 | Quitar la universidad | APLICADO (extendido) | Fuera del problema, del OG, de la hipótesis y de las Conclusiones (sale el descargo «la Carrera es el contexto…»). Queda en la delimitación institucional (destinataria) y en §2.1.4 | Intro; §2.1.3; §2.2.1 («al alcance del estudiante»); §3.8; Conclusiones |
| M-04 | OG «Desarrollar… por la nula transparencia… para que mejore…» | ADAPTADO | Las cuatro partes de OG 2, con el «¿cómo?» que faltaba («empleando el lenguaje de programación Python»): el OG contiene el título (OG 6). «debido a» (OG 5), «para mejorar». 41 palabras | Intro «Objetivo general»; §2.1.3; §2.2.1 (paráfrasis) |
| M-05 | «Diagnosticar» no corresponde como objetivo | APLICADO | Se funde con «Fundamentar» (OG 13, «Caso I: sin diagnóstico»). El contenido de §1.1 no cambia; ese análisis ya no se llama «diagnóstico» | Intro; §1.1 (línea del cierre); §2.2.1; `tab:consistencia` |
| M-06 | OE breves que nombren los capítulos | ADAPTADO | Tres OE, uno por capítulo (Fundamentar / Desarrollar / Verificar y validar); «verificar», repetido en dos capítulos, queda solo en el Cap. 3. **El título de cada capítulo es su OE sustantivado y completo** (verbo, qué, cómo y para qué), a pedido del autor («tus objetivos definen tus capítulos») y como deriva Miranda el título de la tesis del OG (OG 6). Hubo una primera versión con títulos cortos, solo del verbo, que se reemplazó ese mismo día. La Introducción lo declara («Cada capítulo lleva por título su objetivo»), y la «Estructura del documento» dice que los capítulos corresponden al índice de la Carrera (T1 20) | Intro; títulos de los tres capítulos; aperturas del Cap. 2 y del Cap. 3; `tab:dsrm` (columna OE); `tab:consistencia` (3 filas); §1.13 (el doble sentido de «validar», antes del OE5, ahora del OE3); §1.13 cierre («primer objetivo»); Nomenclatura (OE) |
| M-07 | Enunciados concisos; lo demás a otros apartados; PI con subtítulo | APLICADO | Introducción en apartados, cada uno solo con su enunciado. Las cláusulas (a)/(b) y la refutabilidad pasan a §2.1.6, y se suma a la (b) el equilibrio de reacciones, que era criterio pero faltaba en el texto. La cita de García-Córdoba pasa a «Metodología». PI en su propio apartado, más cortas | Intro; §2.1.6 |
| M-08 | Conclusiones visuales y directas | APLICADO | Tríada (OG 15): «Conclusión 1, 2 y 3» con el hallazgo en negrita; Figura CR.1 (contraste de la hipótesis), Figura CR.2 (margen de cada criterio), Tabla CR.1 (tríada). Las cifras pasan de la prosa a los visuales. Responde PI-1 y PI-2 (antes no las nombraba). Recomendaciones «1, 2 y 3», una por capítulo | `05_conclusiones.tex` (reescrito); numeración «CR» en un grupo |
| M-09 | Times New Roman 12 y justificado | APLICADO | XeLaTeX con la Times New Roman real; fórmulas en Latin Modern (decisión del autor); justificado con partición silábica; `\emergencystretch`; rótulos y notas justificados; celdas `p{}` a la izquierda. Tercera excepción a APA declarada | `preambulo.tex`; `main_final3.tex` (sin `\pdfminorversion`); Intro «Normas» |
| M-10 | (técnico) Símbolos Unicode en los listados | APLICADO | Bajo XeLaTeX, `listings` no aplica `literate` por encima de U+00FF: 34 «Missing character» en el Anexo C (∂, ε, γ, σ). Se mapean con `newunicodechar` a su símbolo matemático, como hacía `literate` con pdflatex. Probado aparte antes de aplicarlo | `preambulo.tex` |
| M-11 | (nuevo) Figura de las variables | APLICADO | Figura 2.1, «Relación entre las variables», con el esquema de círculos de PP 9 y 15; la Introducción remite a ella | §2.1.2 |
| M-12 | Retiro de PyMuPDF (otra sesión, pedido del autor) | APLICADO | Las cinco ediciones R2-Z01..Z05 de final2, con la misma redacción: Tabla 2.5 sin PyMuPDF, nota de licencias, párrafo del visor, A.3 y «Versión evaluada» (con su `% DATO PENDIENTE` del hash) | §2.2.2; Anexo A.3; §2.1.1 |
| M-13 | (coherencia) «variable independiente/dependiente» de Wieringa | APLICADO | Pasa a «factor/respuesta», para no confundirla con la VI y la VD de la tesis | §2.1.1 |
| M-14 | (coherencia) Referencias al OE3 viejo | APLICADO | «el tercer objetivo específico» (intercambio de datos) → «el criterio de intercambio de datos de la cláusula (a)» | §3.3; Anexo D |

## Figuras nuevas y cómo se regeneran

`tesis/figuras/generar_figuras_formulacion.py` escribe en `capitulos_final3/figuras/`:

- `fig_relacion_variables.png` (Figura 2.1);
- `fig_contraste_hipotesis.png` (CR.1);
- `fig_margen_criterios.png` (CR.2).

Lee las cifras de `docs/vyv/datos/*.csv`. Las tasas del MMS las recalcula con precisión completa
entre N = 16 y N = 32, porque la columna del CSV viene redondeada y el Q9 daría desvío 0 en escala
logarítmica. Antes de dibujar comprueba que coinciden con `tab:veredicto`, y si no coinciden
termina con error. La paleta (azul, violeta y naranja) pasó el validador de la skill `dataviz`; el
naranja tiene 2,5:1 de contraste, así que ningún color va sin su rótulo.

## Lo que queda para el autor

1. **Revisar `main_final3.pdf`**, sobre todo:
   - la Introducción (pp. 1-10 del cuerpo);
   - la Figura 2.1 y la matriz de consistencia (§2.1.2-2.1.3);
   - las Conclusiones (Figuras CR.1 y CR.2, Tabla CR.1).
2. **Confirmar con el Reglamento de Graduación** (H-1) el interlineado y los márgenes; hoy siguen
   APA (doble espacio, 2,54 cm).
3. **Presentación y video de defensa**: siguen `main_final.tex` y no reflejan ni final2 ni final3.
   Rehacer las láminas de problema, objetivos, hipótesis, títulos y conclusiones.
4. **Hash de la revisión del instalador** (`% DATO PENDIENTE` en §2.1.1) cuando se haga el commit.
5. Siguen abiertas, sin cambios: la decisión del MMS (λ, D33), el largo del Resumen y las demás de
   `docs/notas/ESTADO.md`.

## Archivos tocados

- Nuevos:
  - `tesis/main_final3.tex`, `tesis/capitulos_final3/` (copia de final2 más los cambios de
    arriba);
  - `tesis/figuras/generar_figuras_formulacion.py`;
  - `tesis/observaciones_miranda/` (diagnóstico y README);
  - este registro.
- Unificación del PDF de final2 (pedido del autor): `main_final2_build.*` → `main_final2.*`. El
  PDF bueno, de 197 páginas, reemplazó a una compilación vieja de 194; la otra sesión lo recompiló
  después.
- Estado del repositorio: `tesis/README.md`, `docs/MAPA.md`, las tres skills `tesis-*`,
  `docs/notas/ESTADO.md` y la nota `docs/notas/2026-09-25_observaciones-miranda-final3.md`.
- **Sin commit.**
