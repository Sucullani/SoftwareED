# Implementación de la cuarta iteración: versión final4

Registro de la versión **final4**, hecha el 20-10-2026 a pedido del autor. Aplica las
observaciones del **tribunal tras la defensa de borrador** de final3, más las decisiones que el
autor tomó al revisar el plan. Plan aprobado:
`C:\Users\User\.claude\plans\pasted-content-id-24cc-dame-el-zippy-rabin.md`.

- Versión nueva: `tesis/main_final4.tex` + `tesis/capitulos_final4/` (con su `preambulo.tex`,
  `referencias.bib`, `CRITERIOS.md` y `figuras/`, donde las tres figuras de la formulación pasan
  a PDF vectorial).
- final3 no se modificó. Al terminar pasó entera a `tesis/archivo/final3/` (`git mv`).
- Para ver todo lo cambiado:
  `git diff --no-index tesis/archivo/final3/capitulos_final3 tesis/capitulos_final4`.
- **Se compila con XeLaTeX**: `latexmk -xelatex main_final4.tex`.
- Fuera de la tesis, entre los guiones, solo cambió `tesis/figuras/generar_figuras_formulacion.py`
  (versión como parámetro, guarda más estricta, PDF vectorial y letra legible). **No se tocó el
  software** ni los datos de verificación y validación. Cambiaron además el `\graphicspath` de
  `tesis/observaciones_miranda/diagnostico_miranda.tex` (por el traslado de final3), la fe de
  erratas de `AUDITORIA-GENERAL-FINAL3.md` y la documentación del repositorio: `tesis/README.md`,
  `tesis/archivo/README.md`, `tesis/presentacion/README.md`, `tesis/presentacion/final3/README.md`,
  `tesis/defensa_metodologica/README.md`, `tesis/observaciones_miranda/README.md`,
  `tesis/.gitignore`, `tesis/latexmkrc`, `docs/MAPA.md`, `docs/notas/ESTADO.md`,
  `docs/notas/2026-09-10_apa-presentacion.md`, las tres skills `tesis-*` y la nota
  `docs/notas/2026-10-20_tesis-final4-tribunal.md`. Se borraron cuatro restos de una prueba con
  pdflatex en la raíz de `tesis/` (`main_final4.aux`, `.fdb_latexmk`, `.fls` y `.log`).

## Estado final de final4

- Compila sin errores, sin desbordes y sin referencias ni citas indefinidas; biber sin avisos.
- Páginas: **191** (final3: 189). Las Conclusiones bajan de 8 páginas a 4 (pp. 109-112); la
  §3.8 crece unas 3 con el contraste por partes y la Tabla 3.11.
- Sin viudas, huérfanas ni palabras partidas entre dos hojas (penalizaciones a 10000, T-19).
- Etiquetas: las 157 de final3 siguen, más 2 nuevas (`sec:limitaciones-observadas`,
  `tab:componentes-hipotesis`). No hay claves bibliográficas nuevas.
- Avisos, frente a la línea base (la copia de final3 compilada sin cambios): el mismo renglón
  flojo (la nota al pie con `MMD_AT_PLUS_A`, ahora un poco más flojo por la sangría colgante de
  las notas), los mismos 8 avisos de `hypcap` y el mismo aviso de fuente de Latin Modern Mono.
- Comprobado sobre el PDF: ningún renglón de título de rótulo en cursiva; número de página al
  pie en todas las hojas salvo la portada; la marca del pie es la del capítulo en curso en todas
  las hojas, incluidas las de continuación de la Nomenclatura (XII a XV); las 8 notas al pie
  terminan en el fondo de la caja de texto (en final3, la de la p. 65 quedaba 3,2 cm más arriba
  y la de la p. 67, 1,5 cm); la Figura 2.1 ya no ocupa sola una hoja.
- La hipótesis literal aparece idéntica en la Introducción, en §2.1.3 y en §3.8. Las
  Conclusiones y la Figura CR.1 no la copian: dan su veredicto y nombran sus partes.

## Disposiciones

| ID | Observación o decisión | Disposición | Qué se hizo | Dónde |
|---|---|---|---|---|
| T-01 | Hipótesis nueva del tribunal | APLICADO | Texto literal del tribunal con «dada» y sin el paréntesis: «debido a» habría presentado la escasa transparencia como causa de la mejora; «dada» la presenta como la situación de partida | Intro «Hipótesis»; §2.1.3; §3.8 |
| T-02 | Variables (decisión del autor: no cambiarlas, ni el problema ni el objetivo general) | APLICADO | Puentes de una oración: la hipótesis atribuye la VD «al análisis por el MEF en elasticidad plana» («atribuye», no «predica», que es un tecnicismo: T-19), que se realiza mediante el procedimiento de cálculo (misma unidad); niveles de la VD, baja y alta, para que «mejorar» sea contrastable; la interviniente es EduFEM, desarrollado bajo un método de diseño de software educativo; «el software» del último tramo es el de análisis, no EduFEM; nivel de caja negra «de partida» | Intro «Variables»; §2.1.2; `tab:variables`; Figura 2.1 |
| T-03 | Contraste claro | APLICADO | Cuatro partes en el orden del enunciado (condición, intervención, efecto con sus cláusulas (a) y (b), antecedente); premisas «respaldadas» y «se cumple» solo para el efecto; regla de decisión conjuntiva (comprobada, parcial, no comprobada), enunciada sin decir que se fijó antes; `tab:criterios` sin criterios nuevos. §3.8 reescrita: la hipótesis en bloque, la Tabla 3.10 (criterios), la Tabla 3.11 nueva (partida frente a logro, parte por parte, con citas literales de la Tabla 1.1) y los párrafos «El efecto», «Las premisas», «La mejora frente a la situación de partida», «Veredicto» y «Respuesta al problema» | §2.1.6; §3.8; `tab:componentes-hipotesis` |
| T-04 | «Método de diseño de software educativo» | APLICADO | Se identifica con la ciencia del diseño aplicada a un software educativo: requisitos tomados de los antecedentes y decisiones trazadas a los principios de §1.2; sin bibliografía nueva. Párrafo nuevo en §2.1.1, leyenda de `tab:dsrm`, fila de la interviniente en `tab:variables`, método en `tab:consistencia`; §3.6.3 pasa a llamarse «Procedencia de las decisiones de diseño» y es la evidencia de la condición (la etiqueta no cambia) | §2.1.1; §2.1.2; §2.1.3; §3.6.3; Intro «Metodología» |
| T-05 | Retirar «Aportes del trabajo» y «Limitaciones» (pp. 105-108) | APLICADO | Se eliminan las dos secciones. Lo único se reubica: en §3.7.5, que recibe una etiqueta, van la evaluación hecha por el autor, la exposición opcional, la memoria de la factorización no medida y que la deformación plana no tiene contraste externo; en las Conclusiones, una oración de aporte en los párrafos de los Capítulos 2 y 3. La frase falsa «La deformación plana solo se verifica con el MMS» no se trasladó. Remisiones corregidas (líneas de final3): `02b:16`, `04:328`, `04:465`, `01:116` | §3.7.5; Conclusiones; §2.1.1; §3.6.2; §3.8; Intro |
| T-06 | Conclusiones claras, concisas y visuales, sin «Conclusión 1, 2, 3» | APLICADO | Reescritas en unas 650 palabras (eran unas 2290), en 4 páginas (eran 8). Apertura con el objetivo general y la respuesta al problema; veredicto de la hipótesis sin copiar su enunciado (decisión del autor); Figura CR.1 nueva (la hipótesis parte por parte); tres párrafos que abren con «De … (Capítulo N) se concluye que…» (decisión del autor); Figura CR.2; inconveniente y tres debilidades (Taller 5); Recomendaciones en tres grupos con entrada en negrita, sin «Recomendación N»; Tabla CR.1 (la tríada, con flechas). Se conservan las tres etiquetas | `05_conclusiones.tex` |
| T-07 | Títulos de figuras y tablas sin cursiva | APLICADO | `textfont=up`; los 15 títulos de grupo internos de las tablas pasan a negrita (como la Tabla 3.1) y los 4 avisos de continuación pierden la cursiva. «Nota.», «Palabras clave:» y los títulos de nivel 3 y 5 siguen en cursiva (decisión del autor: solo rótulos) | `preambulo.tex`; `00b`; `02b`; `04`; `06` |
| T-08 | Pie de página abajo y con mejor estilo | APLICADO | Número abajo a la derecha, nombre corto del capítulo a la izquierda y filete fino encima; la hoja de apertura lleva solo el número; `footskip` de 1,27 cm sin tocar la caja de texto. Los tres capítulos-objetivo fijan su nombre corto con `\chaptermark` tras su `\label`. Notas al pie fijas al fondo con `footmisc [bottom,hang]`, URL en la letra del texto y las tres notas del repositorio igualadas. Anexo E: sin el `offset` de final3; las hojas giradas llevan solo el número | `preambulo.tex`; `02`, `02b`, `04` (marca corta); `06` (Anexo E, notas) |
| T-09 | Declarar las excepciones a APA | APLICADO | «Normas de citación y presentación»: lista de cinco excepciones (numeración, A4, justificado, títulos de rótulo en redonda, número de página al pie con el capítulo) | Intro; comentarios del preámbulo |
| T-10 | «ejemplo canónico» → nombre más claro (pedido del autor; el tribunal recomendó evitar términos muy técnicos) | APLICADO | «ejemplo guía», glosado en su primera aparición («un modelo de nueve nodos y cuatro elementos Q4 que acompaña al lector por todo el procedimiento»); «orden canónico» → «el orden del cálculo»; «terminología canónica» → «terminología que el autor fijó». Se descartó «ejemplo de demostración»: en una tesis de verificación se lee como prueba matemática y chocaba con la actividad «Demostrar» del método. El menú del software sigue diciendo «Cuadrado de validación», como ya aclara el manual | 01, 02b, 03, 04, 05, 06, 07; CRITERIOS §2 |
| T-11 | H1: el MMS no distingue tensión plana de deformación plana | APLICADO (vía b, sin tocar código) | Con el campo manufacturado, tr(ε) = 0 y γ = 0: solo interviene D11 − D12 = E/(1 + ν), igual en los dos estados (verificado en `fem/constitutive.py` y `tests/vv_mms.py`). §2.1.4: los tres casos cubren la tensión plana (ya no «los dos estados planos»), y la deformación plana es la tercera excepción: solo interviene en el MMS, que no la distingue, y no tiene contraste externo; sus D11 y D12 los acota, junto con el MMS, la prueba de deformación uniaxial de `tests/test_vv_extensions.py` (8/8, Tabla D.1), que compara un solo escalar (la tensión de von Mises) y por eso no los fija por separado; su D33 no tiene prueba propia. §3.2: el término fuente es el mismo en los dos estados; la verificación no distinguiría las matrices; D33 de deformación plana solo puede comprobarse a mano, contra su ecuación, con su expresión en el listado del Anexo C o con los valores de D que muestran el módulo M4 y la memoria de cálculo (no «se comprueba en el código»; T-19). §1.13: alcanzar la tasa teórica no descarta errores en los términos que la solución elegida anula. §3.7.1, §3.7.5, la fila de la Tabla D.1 y la Nomenclatura ($D_{ij}$) lo acompañan. La recomendación de ampliar la batería suma una prueba propia de D33 | §1.13; §2.1.4; §3.2; §3.7.1; §3.7.5; Tabla D.1; Nomenclatura; Conclusiones |
| T-12 | H4: «criterios fijados de antemano» | APLICADO | §2.1.6: «Ningún umbral numérico se escribió antes de las primeras corridas, ni se calculó a partir de sus resultados»; los de la flecha, Cook y las tasas se incorporaron a los guiones al comienzo de la verificación, cuando estos ya imprimían esos errores (los guiones existen desde el 25 de mayo, `ed852bf`, sin umbrales; los umbrales entraron el 1 de junio, `c8885e0`); los de σx y del equilibrio, al final del desarrollo (`4a60eb2`, 16 de septiembre); el veredicto descansa en el margen (Figura CR.2), y §3.8 da el más ajustado (σx frente a SAP2000, 0,21 % con umbral de 1 %). Se retiró «tolerancias de ingeniería» como descripción general (el ±0,5 y el 10⁻⁸ no lo son), «criterio a priori» de §3.2 y «tolerancias fijadas» de la actividad 2 de la Tabla 2.1. En el resto: «tolerancia explícita», «criterios de aceptación explícitos» | §2.1.6; §3.2; §3.8; Tabla 2.1; Intro (VD, PI-2); Resumen; §1.13; §2.2.1; CRITERIOS; README |
| T-13 | Figuras de la formulación | APLICADO | El guion recibe la versión (`--version final4`), aísla la tabla de veredicto y comprueba fila por fila sus cifras contra los CSV (6 criterios en (a), 9 en (b), todos «Se cumple»), falla con `SystemExit` antes de escribir y escribe PDF vectorial al ancho de la caja en Times New Roman (letra de 8 a 11,5 pt; en final3 se imprimían a 4,9-9,3 pt). Figura 2.1: interviniente «EduFEM, desarrollado bajo un método de diseño de software educativo»; la flecha inferior rotula la intervención y la predicción de la hipótesis («permitirá mejorar»), sin presentar una paráfrasis como «Hipótesis»; sin cursiva; más compacta para no quedar sola en una hoja. CR.1: rehecha; nombra cada parte con su papel, su evidencia (columna «Evidencia», T-19) y su veredicto, sin reproducir el enunciado ni repetir el veredicto en una franja. CR.2: las mismas cifras, con los rótulos a 11,5 pt | `tesis/figuras/generar_figuras_formulacion.py`; `capitulos_final4/figuras/*.pdf` |
| T-14 | Hojas de flotantes con mucho blanco | APLICADO | En las Conclusiones y en §3.8, `\floatpagefraction`, `\topfraction` y `\textfraction` locales (en un grupo) para que las figuras CR.1 y CR.2 y la Tabla 3.11 vayan arriba de la hoja con texto debajo | `05`; `04` (§3.8) |
| T-15 | Resumen | APLICADO | La frase de la hipótesis con el sentido nuevo, sin alargarlo; «criterios de aceptación explícitos» | `00_resumen.tex` |
| T-16 | Revisión adversarial de final4 (51 veredictos: coherencia, H1/H4 y pedido del tribunal) | APLICADO lo confirmado y lo parcial, adaptado; 4 refutados sin cambio (H-14, H-16, H1.5, F18) | **Premisas**: las Conclusiones dicen «queda comprobada» y nombran las tres premisas como «respaldadas» (antes, «se comprueba en sus cuatro partes» y faltaba el antecedente); la intervención entra en la frase de las premisas de §2.1.6 y la regla define el caso de una premisa sin respaldo; la evidencia de las premisas está en los Capítulos 1 a 3. **Tabla 3.11**: cada celda de partida describe su parte (el nivel bajo de la VD para el efecto; la Tabla 1.1 para el antecedente), con las celdas citadas completas; «memoria reproducible a mano» (no «rehecha»). **Nivel alto de la VD** en modo posible («puede seguirse», «puede comprobarse») en la Intro y §3.8; «ejemplo guía, cuya memoria se desarrolla para que pueda rehacerse a mano» en §2.1.1. **SAP2000**: el «otro programa» de la definición, patrón de comparación y no de exactitud (§3.8 y nota de la Tabla 3.2). **No tautología** (§3.7.2 y §3.8): lo expuesto contenía un defecto; la trazabilidad lo hizo visible. **Antecedente** respaldado en la Tabla 1.1 por los rasgos de la categoría, sin la brecha de los recursos didácticos (que no es la premisa) y sin la cita de Pérez-Santiago p. 1160 (H9 de la auditoría general). Figura 2.1, CR.1 y sus leyendas, como en T-13. Remisiones de las Conclusiones a la Tabla 3.6 y la Figura 3.5 (la Tabla 2.8, de los módulos, no respaldaba lo que se le atribuía) | 01; 02b; 04; 05; 06; figuras |
| T-17 | Pie de las hojas de continuación de la Nomenclatura (decían «Índice de tablas») | APLICADO | Estilo de página `nomenclatura`, con el nombre fijo, activado **dentro de un grupo** en `00b`: con fancyhdr 5, `\pagestyle{nomenclatura}` reescribe los campos del estilo `fancy` y `\pagestyle{fancy}` no los restituye (la primera prueba dejó «Nomenclatura» en el pie de todo el cuerpo) | `preambulo.tex`; `00b_nomenclatura.tex` |
| T-18 | Detalles de composición | APLICADO | `\hyphenation{EduFEM}`: babel partía «Edu-FEM», incluso dentro del enunciado de la hipótesis. `\FloatBarrier` (paquete `placeins`) antes de «Recomendaciones»: la Figura CR.2 caía bajo ese título y partía en dos la primera recomendación; con las Conclusiones recortadas en T-19 ya no deja blanco | `preambulo.tex`; `05` |
| T-19 | Segunda revisión adversarial (cinco lentes; cada hallazgo, verificado por otro agente que intentó refutarlo; 73 hallazgos: 53 confirmados, 17 parciales y 3 refutados) | APLICADO lo confirmado y lo parcial, en su versión verificada. Refutados sin cambio: contraste-10 (el sujeto general de la «Respuesta al problema» es la decisión H-046 de final1), exactitud-05 (el orden N→J→B→D de los módulos es el original) y redaccion-25 («porqué» sustantivado es norma culta) | **Composición**: `\widowpenalty`, `\clubpenalty` y `\brokenpenalty` a 10000 (el objetivo general salía partido entre las pp. 4 y 5, y once palabras quedaban partidas entre dos hojas); Tabla 2.5 a `[htbp]` (criterio de H-218); `\hyphenation` de SAFE, software y Cambridge, y `\mbox{ED-Elas2D}`; un 0,04 % en modo matemático; ∈ unido a su intervalo en la Nomenclatura; `\needspace` en los grupos de Recomendaciones. **Contraste**: los criterios de la Tabla 2.4 miden la VD, no el nivel de la VI (§2.1.2); «mismo lienzo» solo para las tres fases (la memoria es un PDF); «La hipótesis no es una tautología» en lugar de «no se cumple por definición»; «se midió», «se contrasta» y «Evidencia» donde no se da el veredicto; memoria «reproducible a mano» en la operacionalización; la batería establece la verificabilidad, no la trazabilidad; el requisito 2 sirve a las dos dimensiones; la excepción del ejemplo guía en la cláusula (b), como la del intercambio de datos en la (a); la cláusula (a) con el mismo reparto que sus criterios; «cuatro configuraciones» en la leyenda de CR.2. **Exactitud**: §3.2 ya no atribuye el defecto de la extrapolación a la norma de σ*, que nació con su corrección (`53ddf11`); §2.1.1 ya no dice que cada componente tuvo su prueba antes de integrarse (el motor entró entero el 27-02, sin aserciones); el error de τxy no es solo de escala (§3.7.1, §2.1.6, Anexo D); SAP2000 fuera de las referencias «de exactitud conocida» (§1.13) y del título del Anexo E, que pasa a «Modelo en SAP2000 y solución analítica de Timoshenko» (la etiqueta no cambia); D33 de deformación plana comprobable a mano por tres vías; los desvíos de CR.2 no están en la Tabla 3.10; la seminorma H¹ mide gradientes, no deformaciones; «Versión evaluada» declara los seis decimales de SAP2000 (parte de H5). **Redacción**: el veredicto de las Conclusiones ya no repite las premisas ni el párrafo del Cap. 3 la cláusula; «no es una tautología» dicho en llano; dos aportes («un aporte», «otro aporte»); §3.8 sin la enumeración de columnas ni el episodio contado dos veces; «predica» → «atribuye»; referentes, concordancias y paralelismos. **Documentación**: skills sin reglas que contradigan CRITERIOS; índice de la defensa con el `.pptx` correcto; la defensa metodológica descrita como lo que es (sigue a `main_final`); fe de erratas también en D1; pendientes H6, H8 y H9 listados; `*.lnk` ignorado | 00b; 01; 02; 02b; 03; 04; 05; 06; preámbulo; figuras; documentación |

## Lo que queda para el autor

- **Revisar el PDF** `tesis/main_final4.pdf`, sobre todo la Introducción («Hipótesis»,
  «Variables», «Normas»), §2.1.6, §3.8 con la Tabla 3.11, las Conclusiones y el pie de página.
- **Material de defensa**: `tesis/presentacion/final3/` sigue a final3, con la hipótesis anterior,
  las «Conclusión 1, 2 y 3» y las páginas viejas; `tesis/defensa_metodologica/` sigue todavía a
  `main_final` (cinco objetivos, la hipótesis de entonces, «criterios fijados de antemano»,
  PyMuPDF en el binario y las páginas de `main_final.pdf`).
- **Menú del software**: el ejemplo guía se llama «Cuadrado de validación»
  (`gui/main_window.py:441`). Si se quiere alinear con la tesis, hay que cambiar el software (no
  se tocó).
- `\anioTesis` pasó a «octubre de 2026» (lo cambió el autor): ajustarlo al mes de la entrega.
  Los preliminares siguen fuera.
- **Comentario del guion `tests/vv_timoshenko.py:478-481`** (software, no se tocó): dice
  «Criterios de aceptacion fijados a priori (tesis, sec. 2.1.6)», y §2.1.6 dice lo contrario.
  Texto propuesto, para cuando se toque el software (anotarlo con H5 en «Versión evaluada»):
  «# Criterios de aceptacion de la tesis (sec. 2.1.6), escritos despues de las / # primeras
  corridas: flecha central dentro del 3 % de la analitica con / # correccion de cortante (desde
  2026-06-01); sigma_x dentro del 1 % de la / # analitica y de SAP2000 en A, B y C, y residuo
  de equilibrio < 1e-8 / # (desde 2026-09-16).»
- La auditoría general de final3 (`AUDITORIA-GENERAL-FINAL3.md`) llevaba dos datos falsos sobre
  H4 (que `c8885e0` fuera el primer commit y que los umbrales precedieran a los resultados); se
  le agregó una fe de erratas en H4 y en las respuestas A11 y D1, que preparaban al autor para afirmarlo
  ante el tribunal.
- `tesis/respaldo_citas/verificado.json` ubica la cita de Hevner p. 81 en «Conclusiones
  (Aportes)», que ya no existe; la cita sigue en §2.1.1.
- Pendientes de auditorías anteriores que esta versión no resolvió: H5 (hash de la revisión del
  instalador, `% DATO PENDIENTE` en §2.1.1), H6 (§2.2.1 declara dos rótulos en inglés y la
  interfaz tiene más; el 23,95 de Cook en el menú), H7, H8 (el deshacer no revierte la edición de
  un vértice; es del software), H9 (entre otros, la p. 1160 de Pérez-Santiago en la Situación
  problemática, la nota de VisualFEA de la Tabla 1.1 y los localizadores de Bishay y de
  Timoshenko-Goodier), H10 (entre otras precisiones, el Resumen de unas 310 palabras frente a las
  250 de APA) y H-1 (Reglamento de Graduación).
- **Docstring de `fem/error_norms.py:237-241`** (software, no se tocó): dice que la norma del
  campo de tensiones recuperado detecta la permutación de la matriz de extrapolación. Es falso:
  con la matriz vieja esa norma converge igual (verificado en T-19); solo la detecta la prueba
  7/8 de `tests/test_vv_extensions.py`.
- Lenguaje llano en general: el tribunal recomendó evitar términos muy técnicos; esta versión
  cambió «canónico» y «predica». Una pasada general sería otra tarea.
