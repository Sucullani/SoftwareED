# Implementación de la segunda iteración: versión final2

Registro de la segunda iteración de mejora continua de la tesis (**final1 → final2**), hecha el 25-09-2026 a pedido del autor: *«Puedes verificar tu trabajo. Cada rincón. Si encuentras algún error corrígelo. Revisa nuevamente la tesis como una segunda iteración.»*

- Versión nueva: `tesis/main_final2.tex` + `tesis/capitulos_final2/` (con su propio `preambulo.tex`, `referencias.bib`, `CRITERIOS.md` y la figura `fig_arquitectura.png` regenerada).
- Intactas: `capitulos_final/` (línea base auditada, commit `ee7b5a6`) y `capitulos_final1/` (primera iteración, registro en `IMPLEMENTACION-FINAL1.md`).
- Para ver todo lo cambiado: `git diff --no-index tesis/capitulos_final1 tesis/capitulos_final2`.

## Método

1. **Verificación de la iteración 1.** Cada unidad de revisión leyó, además del texto de final2, el diff de la iteración 1 en su tramo, para detectar lo que esa iteración hubiera roto o dejado a medias. A eso se sumó una verificación transversal propia (unidad X).
2. **Revisión por diez unidades (A a J)** que cubren el documento entero, de la portada al Anexo G. Cada unidad contrastó el texto con el código de EduFEM (revisión evaluada y actual), con las fuentes en PDF de `tesis/bibliografia/` (páginas renderizadas cuando el PDF es un escaneo) y con los datos de `docs/vyv/datos/`.
3. **Nueva verificación antes de aplicar.** Ningún hallazgo se aplicó por el solo informe de la unidad: cada uno se volvió a contrastar con la fuente, el código o un cálculo (por ejemplo, las tasas del MMS con la cuadratura de la rigidez, la extrapolación 1D del Q9, las capturas de M2, M3, M6, M7 y de la Fig. D.3, las licencias con `importlib.metadata`, la búsqueda web sobre la licencia de VisualFEA). Los que no se sostenían se descartaron o se adaptaron, y lo que afecta a decisiones del autor se dejó sin tocar.
4. **Lotes atómicos** B14 a B33 sobre `capitulos_final2/` (cada edición debe aparecer exactamente una vez; si una falla, no se escribe nada), más tres ediciones manuales: la nota de elaboración propia y el comentario de cabecera de `main_final2.tex`, y el pie de la Figura 2.2 en `tesis/figuras/generar_figuras.py` (regenerada solo en `capitulos_final2/figuras/`).

## Estado final de final2

- Compila sin errores, sin desbordes y sin referencias ni citas indefinidas: **197 páginas**.
- Etiquetas idénticas a final1 (153; CRITERIOS §4). Ninguna clave bibliográfica nueva; 26 referencias, numeradas por orden de primera mención.
- Las 18 cifras clave del documento siguen presentes. Continuaciones de oración tras ecuación: 0. Palabras repetidas, dobles espacios y comillas rectas: 0.
- Oraciones de más de 60 palabras: 15, todas preexistentes (las fórmulas fijas del problema, el objetivo general y la hipótesis, y nueve de 61 a 68 palabras que la iteración 1 ya había dejado). Las que alargó esta iteración se partieron (R2-L01).
- Páginas con más de un tercio en blanco: solo finales de capítulo.

## Resumen de disposiciones

256 disposiciones registradas:

- **APLICADO**: 236
- **APLICADO PARCIAL**: 1
- **ADAPTADO**: 1
- **YA APLICADO**: 7
- **CUBIERTO**: 1
- **DESCARTADO**: 2
- **DECISIÓN DEL AUTOR**: 8

«YA APLICADO» y «CUBIERTO» marcan hallazgos que otra unidad había resuelto antes; «APLICADO PARCIAL», los que se completan en otro lote (se indica cuál).

## Cambios de fondo que conviene que el autor revise

Son correcciones de hecho, verificadas, pero cambian afirmaciones que el autor puede tener que defender:

1. **ED-Elas2D sí expone las matrices, y su interfaz está en inglés** (R2-B01, R2-B02). Las figuras 9 y 10 de Suárez et al. (pp. 248-249) muestran el cálculo de k_e por punto de Gauss y el diagrama de siete pasos, y los menús están en inglés. En la Tabla 1.1 su «Cálculo paso a paso» pasa a «Alta», y el vacío que diagnostica la tesis se concentra ahora en la memoria de cálculo reproducible a mano y en la V&V publicada con la herramienta (01:14, 02:23-27, 02:72, 05:14). La conclusión «ninguno reúne los ocho atributos» se sostiene. Los simuladores de Lee (VisualFEA) tampoco se limitan a «un eslabón»: van de las funciones de forma a la solución del sistema (R2-B03).
2. **Dos versiones del motor** (R2-F01, R2-H03, R2-E03). El sistema se resuelve con el motor vectorizado por lotes (`fem/batch.py`); los módulos y la memoria usan la versión legible. La coherencia entre ambas la respalda `tests/test_solver_regression.py` (error relativo ≤ 1e-9), no la construcción. El texto canónico está en §2.2.5; «por construcción» solo queda donde es cierto (memoria y módulos comparten la versión legible).
3. **El motor no detiene un determinante Jacobiano negativo** (R2-F02). Solo rechaza |det J| < 1e-12 e integra con |det J|; un cuadrilátero cóncavo bien orientado se resuelve y lo señala la calidad de malla («Mala»).
4. **Los errores del comprobador de salud no bloquean en sentido estricto** (R2-F07, R2-I01): el diálogo ofrece «Resolver de todos modos»; solo la falta de elementos o de restricciones impide resolver.
5. **El caso de soluciones manufacturadas no puede hacerse en la interfaz** (R2-H01): su fuerza de volumen es una función del punto y sus desplazamientos impuestos no son nulos.
6. **La batería de V&V no viaja en el instalador** (R2-X05): se repite desde el repositorio público; el instalador lleva la memoria de cálculo, no los guiones.
7. **Tiempos de la Tabla 3.9** (R2-H04): la columna de solución ya incluye el ensamblaje; 8450 GDL se resuelven en unas 0,13 s y 33 282 GDL en menos de un segundo (el texto sumaba las dos columnas).
8. **Pérez-Santiago y Campos** (R2-A01, R2-B04): la fuente dice que los especialistas prefieren las destrezas prácticas, no que la formación las privilegie; se retira esa lectura de la Introducción y de §1.2.
9. **Normas de error** (R2-D01, R2-A18, R2-D12): integrar con la cuadratura de la rigidez no degrada el orden (medido: las tasas no cambian; el error L² baja 5-16 %); las normas no se dividen por el área, y sus unidades en la Nomenclatura se corrigen.

## Decisiones que quedan para el autor

| ID | Asunto |
|---|---|
| R2-B19 | Tabla 1.1: tras compilar con las celdas nuevas sigue repartida en tres páginas (3, 7 y 1 filas; pp. 16-18). Forzarla a página nueva dejaría vacía media p. 16; acortar celdas cambiaría contenido. Decide el autor. |
| R2-B22 | VisualFEA «comercial», «cerrado y de pago» (02:19, 02:21, celda Licencia): las publicaciones de Lee no lo dicen. Fuera de ellas consta como software propietario de Intuition Software (Corea del Sur), con una versión educativa (VisualFEA/CBT) distribuida por Wiley como complemento del libro de Cook; «de pago» como motivo para no examinarlo de primera mano es discutible. No se cambia: no hay clave bibliográfica que lo respalde. |
| R2-D25 | 02:469, «verificación de solución» para la viga de Timoshenko: Oberkampf p. 174 llama al contraste con solución exacta en una sola malla «the traditional method for code verification»; su definición de solution verification (p. 34) admite también la lectura de la tesis. |
| R2-E20 | Nota del revisor, verificada en la fuente (p. 1163): FEA34 dice «Correlating FEA results with actual testing» (ensayos reales); la Tabla 3.7 lo traduce «con referencias externas» y lo da por cubierto con el contraste analítico y SAP2000. Es de la misma clase que los criterios de cobertura que el autor decidió defender de viva voz (problema 3), y corregirlo cambia el 18/18: no se toca. |
| R2-H02 | Tabla 3.7, FEA34: la fuente dice «Correlating FEA results with actual testing» (p. 1163) y la tesis traduce «con referencias externas». Mismo asunto que R2-E20. Propuesta de la unidad H: traducir «con ensayos reales» y declarar que el contraste con la solución analítica y con SAP2000 lo sustituye sin equivaler a él (04:328, «Tres filas piden…»); si el autor decide que el sustituto no cubre el ítem, el universo queda en 17 y cambian la Tabla 2.4, la Tabla 3.10, el OE5 y el Resumen. No se aplica: el autor decidió no tocar los criterios de cobertura. |
| R2-H27 | 04:409, factores del reordenamiento (1,7 / 2,0 / 2,9): tres mediciones no concuerdan (unidad H con el equipo cargado: 3,01 / 1,86 / 2,31; control de la iteración 1: 2,9 / 2,2 / 3,6; docstring de solver.py: 2,1). Conviene volver a medir con el equipo en reposo o redondear a «entre dos y tres veces». |
| R2-I32 | M4 (06:238, 06:242): «la deformación del elemento» se dibuja sobre una probeta genérica del panel (mod04_constitutive.py:549-572); el elemento del lienzo solo recibe el contorno. Más ambiguo que erróneo. |
| R2-J28 | 06:779: en el diálogo DXF, la unidad «ft» reescala las coordenadas sin cambiar el sistema de unidades (dxf_import_dialog.py:56, 382-385); para esa opción no se cumple «el sistema de unidades del proyecto se actualiza». No verificado a fondo. |

Siguen además abiertas las decisiones anteriores registradas en `docs/notas/ESTADO.md`, entre ellas la del MMS que no distingue tensión plana de deformación plana (04:61 sigue diciendo que descarta errores en «la matriz constitutiva de ambos estados planos»).

## Observaciones sobre el software (no se tocó el código)

La iteración evalúa la tesis sobre la versión evaluada del software; estas discrepancias del código se documentan para que el autor decida si corregirlas (y, en ese caso, retirar las salvedades que la tesis declara):

1. `file_io/memoria_calculo.py:1010-1013`: la memoria dice que q_SJ < 0 «bloquea la solución hasta corregirlo»; el motor no lo bloquea (R2-F02).
2. Rótulos en inglés visibles: «N warning(s)» (`gui/main_window.py:590`, `gui/dialogs/health_report_dialog.py:312`) y «Vuelo Bezier · sparsity pattern» (`education/module_launcher.py:106`), que además describe una animación de M7 que ya no existe. La tesis los declara en 03:25 (R2-F13).
3. «Condiciones de contorno» en la memoria (`memoria_calculo.py:653, 1924, 1934`), en la teoría (`gui/dialogs/theory_hub_dialog.py:10, 661, 705, 707`) y en la barra de estado (`gui/postprocessing/post_tab.py:450`), frente a «restricción», que el software adopta como canónica.
4. El selector del post-proceso rotula «Esfuerzo Normal σx», «Esfuerzo Principal σ1»… (`post_tab.py:114-124`), aunque CRITERIOS §2 da «tensión» como término de la interfaz.
5. `load_orphan_node`: el mensaje (`models/model_health.py:530-533`, «la carga SÍ entra al vector F […] el sistema queda singular») y la pista del diálogo (`health_report_dialog.py:128-132`, «no afecta el resultado») se contradicen. La Tabla B.3 sigue ahora al código (R2-I31).
6. `bc_orphan_node`: su docstring (`model_health.py:498-501`, «K_red queda mal condicionada») contradice el comentario de `orphan_free_node` (`:552-555`, los GDL restringidos salen del sistema reducido). En el enum, `ORPHAN_FREE_NODE` figura bajo «# Warnings» pero se emite como error.
7. `negative_jacobian`: la pista del diálogo (`health_report_dialog.py:123-127`) dice que con los vértices en orden horario «la integración da signos incorrectos», pero el motor integra con |det J| (`fem/batch.py:221`) y el elemento horario se resuelve bien; el mensaje (`model_health.py:604-607`) usa además voseo («Reordená»).
8. `gui/postprocessing/details_panel.py:7`: la docstring llama «animado» al círculo de Mohr, que se dibuja una sola vez.
9. `fem/error_norms.py:11-14`: la docstring dice que integrar con el orden de la rigidez subestima el error «a O(h^{p+2})»; medido con `tests.vv_mms`, las tasas no cambian y el error L² baja entre un 5 y un 16 %.
10. `gui/dialogs/dxf_import_dialog.py:56, 382-385`: la unidad «ft» reescala las coordenadas sin cambiar el sistema de unidades del proyecto (no verificado a fondo; R2-J28).
11. `README.md:45` exige Python 3.11+; el Anexo A decía 3.10 y ahora dice 3.11 (R2-I04).

## Hallazgos por unidad

Cada fila da la disposición final, la nota de verificación y los lotes en que se tocó el hallazgo. Los identificadores `R2-Xnn` son de esta iteración (las unidades numeran sus hallazgos como X-nn en sus informes).

### Unidad A: Portada, Resumen, Nomenclatura e Introducción

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-A01 | APLICADO | 01:12. Pérez-Santiago y Campos p. 1159: «specialists […] prefer practical skills over fundamental concepts»; p. 1171 (2): «does not mean that theory should be removed». La fuente no dice que la formación privilegie la operación: se conserva solo lo que sí dice (planificar, verificar, validar, p. 1171 (3)). | B18 |
| R2-A02 | APLICADO | 01:5. La p. 1160 habla de programas de ingeniería mecánica y de «other undergraduate degree programs where FEM/FEA is part of the curriculum»; «civil» no aparece en el artículo. | B18 |
| R2-A03 | APLICADO | 01:18 y 01:28. Álvarez de Zayas p. 13: el campo de acción es «aquella parte del objeto»; la contradicción está en la p. 14, no en la 7. La glosa de la tesis es la del material docente de la Carrera (no citable, CRITERIOS §4): se retira la cita de la p. 13 y queda para el autor adoptar, si quiere, la definición de Álvarez. | B18 |
| R2-A04 | APLICADO | 01:35. memoria_calculo.py:1155-1162: todos los elementos solo con ≤ 2 Q4 o 1 Q9; en los demás, el de mayor energía. Se retira «elemento por elemento» y la enumeración de cuatro. | B18 |
| R2-A05 | APLICADO | 01:133. La lista impresa usa comillas, «En:» y «31.5 (2023)» (estilo numérico de biblatex): el párrafo lo declara; regla del punto y coma corregida para «[4, pp. 339-347; 2]». | B18 |
| R2-A06 | YA APLICADO | Nomenclatura de q, q1, q2: corregida en B14 (R2-C) antes de que llegara el informe. | B18 |
| R2-A07 | APLICADO | main_final2.tex: la nota de elaboración propia pasa tras el índice de figuras (en el de tablas dejaba tres renglones solos en la p. xi) y deja de ser exhaustiva. | B18 |
| R2-A08 | APLICADO | 01:133. Se declaran las excepciones a APA (títulos numerados, A4; preambulo.tex:99-101 y 286-290) y se desarrolla la sigla. | B18 |
| R2-A09 | APLICADO | Siglas: Q8 (02:23, 02:47) y APA (01:133); FEM y DOF sí aparecen en la prosa de 03:25. | B18 |
| R2-A10 | APLICADO | 01:66-67. Cláusula (a): se enuncia el criterio de intercambio de datos (Tabla 2.4, 02b:194). Cláusula (b): el criterio del MMS es la tasa ±0,5, no una tolerancia de coincidencia (02b:197-198). | B18 |
| R2-A11 | APLICADO | 01:70. Enumeración de cinco en línea repartida por cláusula; se añade la entidad perdida en el intercambio (A-10). | B18 |
| R2-A12 | APLICADO | 01:14. «los compara» era ambiguo; resuelto dentro de la reescritura de B-02. | B18 |
| R2-A13 | APLICADO | 01:18. Definición de trazabilidad partida en dos oraciones. | B18 |
| R2-A14 | APLICADO | 01:5 y 01:18. La glosa de «procedimiento de cálculo» pasa a su primera aparición. | B18 |
| R2-A15 | APLICADO | 01:91. Oración sin verbo unida a la anterior; «vigas de gran canto» (peninsular) → «de gran peralte», el término del resto del documento. | B18 |
| R2-A16 | APLICADO | 01:82 y 02b:16. Hevner p. 75 respalda «building and application»; la evaluación rigurosa es la Guideline 3 (Tabla 1, p. 83). | B18 |
| R2-A17 | APLICADO | Nomenclatura: u es campo continuo (02:111, 02:120, Ec. 1.28) y vector nodal (Ec. 1.2). | B18 |
| R2-A18 | APLICADO | Nomenclatura: fem/error_norms.py integra sin dividir por el área → ‖e‖_L2 en unidad × m y \|e\|_H1 en la unidad de la magnitud. | B18 |
| R2-A19 | APLICADO | Nomenclatura: ε_z, b, F_f/F_r; N también número de nodos (§2.2.4); g también gravedad (Tabla B.3). | B18 |
| R2-A20 | APLICADO | Nomenclatura: el orden «de aparición» no se cumplía (h, p y ρ antes que u). | B18 |
| R2-A21 | YA APLICADO | Palabras clave del PDF: corregidas en B17 (R2-X04). | B18 |
| R2-A22 | APLICADO | Leyendas de las Tablas 3.1 y D.3 (nota de la unidad A): el símbolo de la Nomenclatura es σ*_h en negrita; σ* queda como abreviatura de los encabezados. | B31 |

### Unidad B: Capítulo 1, §1.1 a §1.3: antecedentes, Tabla 1.1, principios y formulación variacional

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-B01 | APLICADO | 02:23 y celda Idioma. Suárez et al., figs. 1, 3, 8, 10 y 18 (pp. 244-253): menús y diálogos en inglés («File Edit View…», «Materials library», «Welcome to ED-Elas2D», «Stiffness matrix – Element 1»); en castellano solo el visor de Ayuda de Windows y rótulos sueltos. | B18 |
| R2-B02 | APLICADO | 02:25, 02:50, 02:72, 01:14, 05:14. Suárez et al. p. 248 (fig. 9, siete pasos de k_e a las reacciones) y p. 249 (fig. 10, K_ij = ΣΣ Bᵀ D B t\|J\| W por punto de Gauss): ED-Elas2D expone las matrices elemento por elemento → «Alta» y comparte los atributos 3-5. El vacío se concentra ahora en la memoria y la V&V; la conclusión «ninguno reúne los ocho» se sostiene. CAMBIO DE FONDO: lo revisa el autor. | B18 |
| R2-B03 | APLICADO | 02:19, 02:50-51, nota, 02:72. Lee 2015 p. 157 («from element modeling to equation solving») y p. 158 (cuatro pasos, de la función de forma a la solución del sistema global): no es «un eslabón»; no expone la recuperación de tensiones. | B18 |
| R2-B04 | APLICADO | 02:95. Mismo error que A-01; p. 1168 respalda el cuarto principio («connect the theoretical fundamentals with the operation of FEA codes»). | B18 |
| R2-B05 | APLICADO | 02:19 y celda. Lee y Ryu p. 881: el bloqueo por cortante «cannot be described in terms of eigenmodes»; lo que muestran es el bloqueo por falta de modos de sólido rígido (cáscaras curvas, Tabla 2). | B18 |
| R2-B06 | APLICADO | Celda de EduFEM. mod05_stiffness.py:942: solo la etiqueta «1 PG ⇒ SUB-INTEGRACIÓN: modos hourglass posibles»; no hay cálculo de rango ni de autovalores. | B18 |
| R2-B07 | APLICADO | 02:95. El universo toma 15 destrezas y 3 conceptos (02b:147-148), no cuatro categorías de destrezas. | B18 |
| R2-B08 | APLICADO | 02:25 y 02:27. Seis filas distintivas, no cinco; «la diferencia más pertinente» → «otra diferencia, pertinente». | B18 |
| R2-B09 | APLICADO | 03:23 (= F-03). Bishay p. 1023: «mainly because of the assignment-generation mini-projects idea»; también Lee: «sin datos cuantitativos» (p. 168), no «sin grupo de control». | B18 |
| R2-B10 | APLICADO | 02:6. Glosa de «procedimiento de cálculo» (CRITERIOS §2). | B18 |
| R2-B11 | APLICADO | 02:120. σ es tensor en la Ec. 1.1 y vector de Voigt en la 1.2; se advierte el cambio. La doble lectura de u se resuelve en la Nomenclatura (A-17). | B18 |
| R2-B12 | APLICADO | Nota de la Tabla 1.1: «programa» → «software» (CRITERIOS §2). | B18 |
| R2-B13 | DESCARTADO | «Cumplir un objetivo» es el uso corriente (lograrlo) y el documento lo emplea siete veces de modo uniforme (01:111, 01:115, 02:74, 02:497, 05:8, 05:31); CRITERIOS §3 regula los verbos de evidencia sobre criterios, no el logro de objetivos. | B18 |
| R2-B14 | APLICADO | 02:8, 02:93, 02:102. Enumeraciones de cuatro o más en línea; 02:8 resuelve además B-21. | B18 |
| R2-B15 | APLICADO | 02:91. Lee p. 168: contrasta con los años previos, «no quantitative data»; «conducive to enhancing the students' overall understanding and interest». | B18 |
| R2-B16 | APLICADO | 02:120. Hughes pp. 77-79: (W)⇔(S) incluye la condición natural en Γ_t. Se aclara además que la forma débil pide continuidad C0 entre elementos, no «de primer orden» (duda de la unidad B). | B18 |
| R2-B17 | APLICADO | 02:53 y 02:68: «subintegración», como §1.8-§1.9. | B18 |
| R2-B18 | APLICADO | Nota de la Tabla 1.1: oración que empezaba con un símbolo. | B18 |
| R2-B19 | DECISIÓN DEL AUTOR | Tabla 1.1: tras compilar con las celdas nuevas sigue repartida en tres páginas (3, 7 y 1 filas; pp. 16-18). Forzarla a página nueva dejaría vacía media p. 16; acortar celdas cambiaría contenido. Decide el autor. | B18 |
| R2-B20 | YA APLICADO | La celda «Media (pre/proc/post)» desaparece con B-02. | B18 |
| R2-B21 | APLICADO | 02:8: resuelto con B-14 (sin nombres de autores). | B18 |
| R2-B22 | DECISIÓN DEL AUTOR | VisualFEA «comercial», «cerrado y de pago» (02:19, 02:21, celda Licencia): las publicaciones de Lee no lo dicen. Fuera de ellas consta como software propietario de Intuition Software (Corea del Sur), con una versión educativa (VisualFEA/CBT) distribuida por Wiley como complemento del libro de Cook; «de pago» como motivo para no examinarlo de primera mano es discutible. No se cambia: no hay clave bibliográfica que lo respalde. | B18 |

### Unidad C: Capítulo 1, §1.4 a §1.10: elasticidad plana, elementos, Jacobiano, B, rigidez, bloqueo, ensamblaje

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-C01 | APLICADO | §1.9: el Capítulo 3 solo cuantifica el bloqueo por cortante (Cook); el volumétrico aparece como limitación cualitativa y los modos espurios no aparecen. Se quita «y reaparecen, ya cuantificados». | B14 |
| R2-C02 | APLICADO | §1.5: Hughes pp. 192 y 208 y Bathe pp. 476-477 tratan el bloqueo volumétrico y la integración reducida; lo que respalda que el Q9 capta campos de mayor orden y tolera la distorsión angular es Cook pp. 235-236 (verificado en la fuente). Hughes y Bathe ya se citan antes: la numeración no cambia. | B14 |
| R2-C03 | ADAPTADO | §1.6: J no convierte derivadas naturales en físicas (lo hace J⁻¹, Ec. 1.14, Bathe p. 346): «relaciona las derivadas…». Se prefirió el verbo neutro a remitir a la ecuación siguiente. | B14 |
| R2-C04 | APLICADO | §1.5 (texto de la iteración 1, H-028): un GDL es una componente de desplazamiento nodal; las incógnitas son los GDL no restringidos y el total fija el tamaño del sistema global K u = F (Ec. 1.3). Los recuentos de GDL de las tablas son 2 × nodos (cook.csv). | B14 |
| R2-C05 | APLICADO | §1.5: la partición de la unidad solo garantiza la traslación rígida; la rotación y los estados de deformación constante exigen además la isoparametría (Cook p. 237, verificado). | B14 |
| R2-C06 | APLICADO | §1.10: la glosa de «definida positiva» decía una propiedad de cualquier sólido elástico e invertía la consecuencia; ahora: todo desplazamiento no nulo de los GDL libres deforma el sólido, y de ahí la no singularidad y la unicidad (Bathe p. 726). | B14 |
| R2-C07 | APLICADO | §1.6: la convención del Jacobiano (ecs. 5.23-5.25) está en Bathe p. 346, no en la 345 (que trae la interpolación). Verificado en el render de ambas páginas. | B14 |
| R2-C08 | APLICADO | Figura 1.1: la leyenda describía «izquierda/derecha» y la figura tiene tres paneles (Q4 y Q9 en el cuadrado natural, y el mapeo de un Q4 coloreado por N₁). Leyenda y remisión de §1.5 reescritas; numeración del Q9 verificada en la figura. | B14 |
| R2-C09 | APLICADO | §1.9: «el programa» → «el software» (CRITERIOS §2). | B14 |
| R2-C10 | APLICADO | §1.8: la remisión a §2.2.5 prometía el orden de cuadratura, que esa subsección no da. | B14 |
| R2-C11 | APLICADO | §1.9: los modos espurios nacen de la integración (Cook p. 223), no solo de la interpolación. | B14 |
| R2-C12 | APLICADO | §1.8: la sobreintegración sí se recomienda con distorsiones muy grandes (Bathe p. 476, verificado); y «2×2/3×3» se desambigua («2×2 para Q4 y 3×3 para Q9», C-21). | B14 |
| R2-C13 | APLICADO | §1.10: los apoyos deben impedir los movimientos de cuerpo rígido («ninguna combinación de ellos permita…» decía lo contrario de lo que quería). | B14 |
| R2-C14 | APLICADO | §1.9: la explicación (el punto central no mide la deformación de los modos 7 y 8) y el patrón de reloj de arena están en Cook p. 224; localizador pp. 223-224. | B14 |
| R2-C15 | APLICADO | Nomenclatura: q es la carga por unidad de longitud sobre una arista (§1.10) y, en la viga, la carga uniforme; «esa arista» remitía a otra fila. | B14 |
| R2-C16 | APLICADO | Ec. 1.17: las cargas volumétricas elementales se ensamblan con el mismo operador que k_e (fem/assembly.py: np.add.at por dofs); Nomenclatura actualizada. | B14 |
| R2-C17 | APLICADO | §1.6: aclaración de que en la Ec. 1.10 N es la fila de funciones de forma, no la matriz de interpolación de 2×2n de §1.3. | B14 |
| R2-C18 | APLICADO | §1.6: J^{-𝖳} → J^{-T} (CRITERIOS §4). | B14 |
| R2-C19 | APLICADO | «sobre-condiciona» → «sobrecondiciona». | B14 |
| R2-C20 | APLICADO | «los dos primeros bloqueos» → «los dos bloqueos» (solo hay dos; el tercer fenómeno son los modos espurios). | B14 |
| R2-C21 | APLICADO | Incluido en R2-C12. | B14 |
| R2-C22 | APLICADO | \|det J\| con \lvert…\rvert en las tres apariciones (el espacio de \det se imprimía solo a la izquierda). | B14 |
| R2-C23 | APLICADO | Duda del revisor, verificada: «término de sustitución estática» no es terminología de las fuentes y se confunde con la condensación estática; se describe lo que hace la Ec. 1.19. | B14 |

### Unidad D: Capítulo 1, §1.11 a §1.13: tensiones, calidad de malla, verificación y validación

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-D01 | APLICADO | 02:491. Medido con tests.vv_mms (N = 8, 16, 32): con la cuadratura de la rigidez las tasas no cambian (Q4 L2 1,997 / H1 1,001; Q9 3,000 / 2,000) y el error L2 baja un 5 % (Q4) y un 16 % (Q9). El mecanismo («lo muestrea justo donde el error se anula») contradecía §1.11, y «degrada el orden» no ocurre. | B20 |
| R2-D02 | APLICADO | 02:475. La tasa es el exponente (vv_mms.py:210, log(e1/e2)/log(h1/h2)), no la proporción; se retira «la prueba más severa», que 02:489 ya acota. | B20 |
| R2-D03 | APLICADO | 02:412. La extrapolación 1D por tres puntos de Gauss tiene entradas (5±√15)/6, −2/3, 0 y 1 (comprobado); E_Q9 es su producto tensorial. | B20 |
| R2-D04 | APLICADO | 02:375. §2.2.5 no trata σ_z; la afirmación es correcta (batch.py, stress.py, probe_query.py, memoria) pero la remisión era vacía. | B20 |
| R2-D05 | APLICADO | 02:440. Solo M0 endurece el corte de q_SJ (mod00_mesh_quality.py:91-92); la memoria clasifica con el mínimo de Verdict. | B20 |
| R2-D06 | APLICADO | 02:433. mod00_mesh_quality.py:42-52: arco y θ en el peor vértice; «el paso a paso simbólico […] vive en la Memoria […]; M0 no lo repite». | B20 |
| R2-D07 | APLICADO | 02:469. Omitía el valor de referencia de Cook, que §1.13 y §3.5 usan. | B20 |
| R2-D08 | APLICADO | 02:471 y 02:475: «programa» por EduFEM (CRITERIOS §2). | B20 |
| R2-D09 | APLICADO | 02:473. Oración de 65 palabras partida en dos. | B20 |
| R2-D10 | APLICADO | 02:495. Oración de 66 palabras, «bloqueo por cortante» repetido y «comparar contra». | B20 |
| R2-D11 | APLICADO | 02:475. p es el grado del polinomio completo (Strang p. 106); el bilineal contiene ξη. | B20 |
| R2-D12 | APLICADO | 02:475. error_norms.py no divide por el área (el dominio distorsionado mide 0,726). | B20 |
| R2-D13 | APLICADO | 02:426. stretch_metric combina elongación y distorsión angular (mesh_quality.py:226-227). | B20 |
| R2-D14 | APLICADO | 02:433. Verdict p. 36: α_k ≤ 0 → degenerado (colineal o cóncavo). | B20 |
| R2-D15 | APLICADO | 02:451. X1 = ½[½(r2+r3) − ½(r1+r4)]: la mitad del vector entre puntos medios. | B20 |
| R2-D16 | APLICADO | 02:464. «Elemento macro» sin glosa; posición ideal según mesh_quality.py:346-363. | B20 |
| R2-D17 | APLICADO | 02:360. Cook p. 117: «the entire state of stress»; en deformación plana el estado es triaxial. | B20 |
| R2-D18 | APLICADO | 02:421. La dispersión aproxima el error (Zienkiewicz p. 477), no el tamaño de la malla. | B20 |
| R2-D19 | APLICADO | 02:377. En el Q9, cinco nodos no son esquinas. | B20 |
| R2-D20 | APLICADO | 02:412. Cadena «…, y …, y …» que dejó la iteración 1. | B20 |
| R2-D21 | APLICADO | 02:493. Repetición de la prueba de E, que se explica una sola vez en §1.11 (CRITERIOS §3). | B20 |
| R2-D22 | APLICADO | 17 continuaciones de oración tras una ecuación separadas por línea en blanco (02 y 04): LaTeX las componía como párrafo nuevo con sangría; se quita la línea en blanco. | B20 |
| R2-D23 | APLICADO | 02:487. Dentro de las integrales las barras dobles son la norma puntual, no la L2. | B20 |
| R2-D24 | APLICADO | 02:489 (duda de la unidad D). La §3.5 explica un orden ≈ 1 por una singularidad: la afirmación vale para solución suave. | B20 |
| R2-D25 | DECISIÓN DEL AUTOR | 02:469, «verificación de solución» para la viga de Timoshenko: Oberkampf p. 174 llama al contraste con solución exacta en una sola malla «the traditional method for code verification»; su definición de solution verification (p. 34) admite también la lectura de la tesis. | B20 |

### Unidad E: Capítulo 2, §2.1: diseño metodológico

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-E01 | APLICADO | §2.1.4: ningún guion de V&V aplica cargas nodales (vv_mms: fuerza de volumen; vv_timoshenko y vv_cook: carga superficial uniforme); solo el ejemplo canónico. Se declaran dos excepciones. El arrastre en la lista de limitaciones de las Conclusiones va con la unidad H. | B16 |
| R2-E02 | APLICADO | §2.1.5: los guiones llaman directamente a solve_system y no importan models/model_health (validate_project solo se llama desde la interfaz y la memoria). | B16 |
| R2-E03 | APLICADO | §2.1.5: el solucionador ensambla con el motor vectorizado (fem/assembly.py → fem/batch.py); los módulos y la memoria usan la versión legible (element_stiffness, compute_jacobian, compute_b_matrix); tests/test_solver_regression.py exige que coincidan (error relativo ≤ 1e-9). No es «por construcción». La formulación canónica va en §2.2.5 y las demás apariciones se corrigen con la unidad F. | B16 |
| R2-E04 | APLICADO | §2.1.1: las dos referencias externas son la solución analítica y SAP2000; Cook tiene su valor de referencia. | B16 |
| R2-E05 | APLICADO | §2.1.2: la imposición de restricciones se desarrolla en §1.10 (partición, Ecs. 1.18 y 1.19). | B16 |
| R2-E06 | APLICADO | Leyenda de la Tabla 2.2 (iteración 1): el problema científico tiene dos variables; la interviniente es la solución. | B16 |
| R2-E07 | APLICADO | §2.1.2 y §2.1.5: el MMS varía geometría y tipo de análisis entre sus cuatro configuraciones (tests/vv_mms.py:72-81); lo fijo es dentro de cada configuración. Tabla 2.2 ajustada. | B16 |
| R2-E08 | APLICADO | Tabla 2.2: «diferencia relativa» frente a SAP2000, como en el resto del documento. | B16 |
| R2-E09 | APLICADO | Tablas 2.1 y 2.3: el rango «§3.2 a §3.5» incluía §3.3 (consistencia interna), que no es V&V del motor. | B16 |
| R2-E10 | APLICADO | §2.1.4: el estudio reúne 71 ítems en cuatro categorías (Tabla 5, p. 1164: FEM 15, FEA 34, TYPE 7, SW 15); 49 son las dos de contenido. Verificado en el PDF. | B16 |
| R2-E11 | APLICADO | §2.1.4: el Top 3 de la fuente es planificación, mallado y V&V (p. 1165; Tabla 8, p. 1168); el post-proceso queda último. Verificado en el PDF. | B16 |
| R2-E12 | APLICADO | §2.1.5: los ítems proceden del consenso, pero la selección (18 de 49, con tres motivos) es del autor. | B16 |
| R2-E13 | APLICADO | §2.1.6: el criterio de intercambio de datos lo evalúan pruebas automáticas (test_interop termina con AssertionError); el del ejemplo canónico es documental. | B16 |
| R2-E14 | APLICADO | §2.1.6: el criterio del ejemplo canónico se contrasta en el Anexo G (Tabla 3.10). | B16 |
| R2-E15 | APLICADO | §2.1.1: «se lo expone» → «se la expone» (la iteración 1 cambió «el artefacto» por «la herramienta»). | B16 |
| R2-E16 | APLICADO | §2.1.3: el sujeto de «se comprueba» era el problema científico; es la hipótesis. | B16 |
| R2-E17 | APLICADO | §2.1.1: la fecha 16-09-2026 es de la revisión (git show 91e3df0), no de consulta. | B16 |
| R2-E18 | APLICADO | §2.1.6: solo tests/vv_mms.py lleva el umbral 1,4/1,9 (arrastre en §3.2 corregido en B15). | B15, B16 |
| R2-E19 | DESCARTADO | Rótulo fijo «Cláusula (b) (continuación)» en el \endhead de la Tabla 2.4: la continuación solo contiene filas de (b) y la leyenda dice «(continuación)», así que no hay la ambigüedad de H-268; un rótulo fijo en la cabecera mentiría si la compaginación cambiara. | B16 |
| R2-E20 | DECISIÓN DEL AUTOR | Nota del revisor, verificada en la fuente (p. 1163): FEA34 dice «Correlating FEA results with actual testing» (ensayos reales); la Tabla 3.7 lo traduce «con referencias externas» y lo da por cubierto con el contraste analítico y SAP2000. Es de la misma clase que los criterios de cobertura que el autor decidió defender de viva voz (problema 3), y corregirlo cambia el 18/18: no se toca. | B16 |
| R2-E21 | APLICADO | Nota de la Tabla 3.7 (arrastre de E-10 y H-05): los 49 son los ítems de contenido; el consenso tiene 71. | B30 |
| R2-E22 | APLICADO | 05:57 (arrastre de E-01): las cargas nodales solo intervienen en el ejemplo canónico (02b:143). | B30 |

### Unidad F: Capítulo 2, §2.2: el software EduFEM

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-F01 | APLICADO | 03:99, 03:113, 03:222 (y 02b:157, ya en B16). fem/assembly.py:4-12 y fem/batch.py: el motor ensambla por lotes; fem/jacobian.py:5-7 y memoria_calculo.py:1116-1151: módulos y memoria usan la versión legible. Comparten funciones de forma, regla de Gauss y D; tests/test_solver_regression.py compara K, F, k_e, u, reacciones y tensiones (REL_TOL = 1e-9). Texto canónico en §2.2.5; «por construcción» solo queda donde es cierto (memoria y módulos comparten la versión legible). | B19 |
| R2-F02 | APLICADO | 03:115 y 03:163. fem/batch.py:176 (np.abs(det_J) < JACOBIAN_MIN_DETERMINANT) y :221 (\|det J\| en la rigidez): un det J negativo en un punto de Gauss pasa. Prueba de la unidad F con un cóncavo antihorario: det J = −0,104 en un PG, se resuelve; mesh_quality lo clasifica «Mala» (q_SJ ≤ 0 → Mala, :388). | B19 |
| R2-F03 | YA APLICADO | = B-09 (lote B18). | B19 |
| R2-F04 | APLICADO | 03:70 y pie de la Fig. 2.2 (regenerada en capitulos_final2/figuras/). gui ↔ education se importan mutuamente y file_io importa de ambos; fem/ no importa la interfaz. | B19 |
| R2-F05 | APLICADO | Leyenda de la Fig. 2.2 y 03:70. config/ no toca el modelo; fem/ y education/ no lo mutan (búsqueda de asignaciones y mutadores: cero); la memoria trabaja sobre from_dict(to_dict()) (main_window.py:1069-1074). | B19 |
| R2-F06 | APLICADO | Tabla 2.5 y Tabla 2.6. requirements.txt; matplotlib en details_panel, surface_3d_viewer y mod01-07; sympy en fem/symbolic_integrand.py, mod05 y memoria_calculo.py. Licencias PSF y BSD: la nota sigue valiendo. | B19 |
| R2-F07 | APLICADO | 03:139 y 03:165. post_tab.py:405-451: con errores se abre el diálogo con «Resolver de todos modos»; solo la falta de elementos o de restricciones impide resolver; «restricciones insuficientes» = menos de 3 GDL restringidos (model_health.py:489). «Muchos» → «parte» (7 de 22 códigos con corrección automática). | B19 |
| R2-F08 | APLICADO | Leyenda de la Fig. 2.3 y 03:135. config/settings.py:192 (LOD_MIN_ELEMENTS_FOR_GATING = 12) y canvas_logic.py (≤ 12 elementos: nunca hay nivel de detalle). | B19 |
| R2-F09 | APLICADO | 03:215. details_panel.py:217-230 lista Pos, Nat, ux, uy, \|U\|, σx, σy, τxy, VM; el círculo se dibuja una vez (sin after). | B19 |
| R2-F10 | APLICADO | 03:21. 04_resultados.tex no menciona ningún requisito; los criterios de la Tabla 2.4 cubren los cuatro primeros. | B19 |
| R2-F11 | APLICADO | 03:226. memoria_calculo.py:1155-1162 (un elemento representativo) y patrón de K por encima de 18 GDL (03:222). | B19 |
| R2-F12 | APLICADO | Leyenda de la Fig. 2.4. FormulaValueBlocksToggle solo en mod02, mod03 y mod04. | B19 |
| R2-F13 | APLICADO | 03:25. «warning(s)» en main_window.py:590 y health_report_dialog.py:312; «Vuelo Bezier · sparsity pattern» en module_launcher.py:106; «Condiciones de contorno» en memoria_calculo.py:1924/1934 y theory_hub_dialog.py:661/705/707. Si el autor corrige esos rótulos en el software, la oración añadida puede retirarse. | B19 |
| R2-F14 | APLICADO | 03:104. models/project.py:444 (change_node_id), con propagación a las referencias. | B19 |
| R2-F15 | APLICADO PARCIAL | 03:222 pasa a lista con los rótulos reales de memoria_calculo.py (701…3088). Las demás enumeraciones en línea del §2.2 (03:4, 14, 70, 97, 113, 124, 220) se dejan: son recorridos o listas técnicas breves; a criterio del autor. | B19 |
| R2-F16 | APLICADO | 03:11. La Tabla 1.1 tiene once filas; los ocho atributos están en la lista que la sigue. | B19 |
| R2-F17 | APLICADO | Nota 1 de §2.2.4. El Anexo C nombra node_index_map en la prosa del ensamblaje (06:453), sin reproducir dof_x/dof_y. | B19 |
| R2-F18 | APLICADO | Nota del §2.2.5. fem/solver.py:15, 85: spsolve(..., permc_spec=SOLVER_PERMC_SPEC); splu no aparece en el código del software. | B19 |
| R2-F19 | APLICADO | 03:106. Con K de 2·máx(id) no hay índice fuera de rango: los huecos dejan filas y columnas nulas. | B19 |
| R2-F20 | APLICADO | 03:126. mesh_canvas.py:4066-4074: auto-CCW por área signada; el orden de los clics es libre. | B19 |
| R2-F21 | APLICADO | 03:25 y Tabla 2.5. build.spec en modo onedir (CLAUDE.md: lanzador + _internal/). | B19 |
| R2-F22 | APLICADO | 03:63. tools/build_texlive.py: la memoria y el Theory Hub se compilan con el TeX Live embebido. | B19 |
| R2-F23 | APLICADO | Nota del umbral. fem/ conserva tolerancias locales (probe_query.py:255, equivalent_forces.py:43/91, mesh_quality.py:369). | B19 |
| R2-F24 | APLICADO | Nota de la Tabla 2.5. importlib.metadata: PyInstaller «GPLv2-or-later with a special exception». | B19 |
| R2-F25 | APLICADO | 03:137. to_dict no guarda la solución: «copias completas» chocaba con la oración siguiente. | B19 |
| R2-F26 | APLICADO | 03:124. «planillas» → «hojas de cálculo», como 03:15 y 03:224. | B19 |
| R2-F27 | APLICADO | 03:215. Tic «de manera X» (CRITERIOS §3). | B19 |
| R2-F28 | APLICADO | 03:141, leyenda y encabezado de la Tabla 2.7: el software imprime «Buena/Aceptable/Mala» (mesh_quality.py:385-398). | B19 |
| R2-F29 | APLICADO | 03:21 y 03:170. Un único consenso no es «la disciplina»; M1-M7 salen de las etapas del procedimiento. | B19 |
| R2-F30 | APLICADO | 03:108. Antecedente de «trazabilidad», oración de 68 palabras y «entre medio». | B19 |
| R2-F31 | APLICADO | 03:224. model_io.py: seis CSV en un único ZIP. | B19 |
| R2-F32 | APLICADO | Tabla 2.5: glosa de WebP en su primera aparición. | B19 |
| R2-F33 | APLICADO | 03:206. mesh_canvas.py:1093-1110 y 1277-1289 (node_ids[:4]); post_tab.py:209-226: modo «smooth» por omisión. | B19 |
| R2-F34 | APLICADO | 03:201. overlay_module.py: un módulo a la vez; todos operan sobre el mismo análisis. | B19 |
| R2-F35 | APLICADO | 03:141 (nota de la unidad D). memoria_calculo.py:988-996 y 3070-3080: la memoria colorea q_SJ y califica la malla con el corte 0,50; «dos juegos de cortes» no era exacto. | B19 |

### Unidad G: Capítulo 3, §3.1 a §3.5: verificación y validación numérica

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-G01 | APLICADO | §3.5: «A igualdad de GDL, el error del Q9 es más de diez veces menor» es falso a 50 GDL (razón 8,4; cook.csv). Se ata a 578 GDL, como pide CRITERIOS §4 (a 162, 578 y 2178 GDL las razones son 15,6, 15,3 y 13,4). La iteración 1 había partido la oración y dejado suelta la afirmación general. | B15 |
| R2-G02 | APLICADO | §3.4: la cáscara homogénea de SAP2000 combina membrana isoparamétrica con giro drilling y flexión de placa (Kirchhoff o Mindlin/Reissner); en esta viga solo trabaja en su plano (capturas: U2 = 0, solo R2 ≠ 0). Atribuir la discrepancia a la formulación Mindlin-Reissner era incorrecto. Verificado en el manual de CSI, p. 179. La «respuesta preparada» del PLAN repetía el error: se anotó allí. | B15 |
| R2-G03 | APLICADO | §3.1: «seminorma H¹ de su gradiente» → seminorma H¹ del desplazamiento (norma L² de su gradiente, fem/error_norms.py); oración de 63 palabras partida; «normas L² y H¹» → «norma L² y seminorma H¹» en §3.2 y en la leyenda de la Tabla 3.1. | B15 |
| R2-G04 | CUBIERTO | Igual a R2-E06 (leyenda de la Tabla 2.2): se corrige allí. | B15 |
| R2-G05 | APLICADO | Nota de la Tabla 3.1 (iteración 1): la Tabla D.2 solo trae los relativos del desplazamiento; el de σ* en la malla más fina está en la Tabla D.3. | B15 |
| R2-G06 | APLICADO | §3.1: la Tabla 2.2 no tiene «indicadores de cobertura y organización» para la variable independiente; sus dimensiones son transparencia, interactividad y documentación. | B15 |
| R2-G07 | APLICADO | §3.2: una tasa se mide entre dos mallas: «1,82 en el primer refinamiento (N=2 a N=4) a 2,00 en el último (N=16 a N=32)». | B15 |
| R2-G08 | APLICADO | §3.4: ΣRx = −2,583×10⁻⁶ N, 3,8×10⁻¹² de qL (timoshenko_equilibrio.csv): orden del redondeo, no «precisión de máquina». | B15 |
| R2-G09 | APLICADO | Tabla 3.3: SAP2000 da cuatro decimales en los desplazamientos (capturas del Anexo E); el quinto «0» no estaba en la fuente. Los porcentajes no cambian. Ídem en la Tabla D.5 (R2-J). | B15 |
| R2-G10 | APLICADO | u_y^{ref} con \mathrm: dentro de las leyendas \text heredaba la cursiva. | B15 |
| R2-G11 | APLICADO | Figuras 3.2 y 3.4: se declara, como en la Figura 3.3, que las etiquetas generadas por el guion usan punto decimal. | B15 |
| R2-G12 | APLICADO | Leyenda de la Tabla 3.5: faltaba la fila «Comportamiento bajo distorsión». | B15 |
| R2-G13 | APLICADO | Tabla D.5 (arrastre de G-09): SAP_DATA de tests/vv_timoshenko.py da u y v con cuatro decimales; el quinto «0» no estaba en la fuente. Los porcentajes no cambian. | B30 |

### Unidad H: Capítulo 3, §3.6 a §3.8, y Conclusiones y recomendaciones

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-H01 | APLICADO | 04:275. models/project.py guarda solo gravedad uniforme; post_tab.py:466 llama solve_system sin body_force_fn; las llamadas de gui/ a set_boundary_condition pasan solo banderas (pre_tab.py:1766, 1827, 2245, 2713); models/boundary.py:15 «Solo MMS y similares fijan valores no-cero». | B22 |
| R2-H02 | DECISIÓN DEL AUTOR | Tabla 3.7, FEA34: la fuente dice «Correlating FEA results with actual testing» (p. 1163) y la tesis traduce «con referencias externas». Mismo asunto que R2-E20. Propuesta de la unidad H: traducir «con ensayos reales» y declarar que el contraste con la solución analítica y con SAP2000 lo sustituye sin equivaler a él (04:328, «Tres filas piden…»); si el autor decide que el sustituto no cubre el ítem, el universo queda en 17 y cambian la Tabla 2.4, la Tabla 3.10, el OE5 y el Resumen. No se aplica: el autor decidió no tocar los criterios de cobertura. | B22 |
| R2-H03 | YA APLICADO | = F-01 (lote B19). | B19, B22 |
| R2-H04 | APLICADO | Tabla 3.9 y 04:407. bench_timing.py:84-85: t_solve cronometra solve_system, que reensambla (solver.py:104-107); el texto sumaba las dos columnas (0,049 + 0,127 y 0,191 + 0,721). | B22 |
| R2-H05 | APLICADO | Nota de la Tabla 3.7. Pérez-Santiago y Campos: Tabla 4 (SW1–SW15) y «only 8 of the 71 items» (p. 1165). | B22 |
| R2-H06 | APLICADO | Leyenda de la Fig. 3.5. generar_figuras.py::fig_fases_lienzo compone fig_lienzo_lod, fig_modulo_capa y fig_postproceso, que son las Figs. 2.3, 2.4 y 2.5. | B22 |
| R2-H07 | APLICADO | Tabla 3.7, FEA13: la conversión Q4↔Q9 la describe el Anexo B (06:83), no §2.2.6. | B22 |
| R2-H08 | APLICADO | 04:365. SAP2000 queda a 0,16 % de la analítica en τxy y EduFEM a 2,89 %: la analítica es la del mismo continuo que discretiza EduFEM. | B22 |
| R2-H09 | APLICADO | 04:367. 04:159 dice que la viga es esbelta (luz-peralte 11,7); «canto» es peninsular. | B22 |
| R2-H10 | APLICADO | 04:371. Todas las componentes se recuperan con la misma secuencia; la razón que da 04:365 es la escala. | B22 |
| R2-H11 | APLICADO | 05:40. VisualFEA y ED-Elas2D reúnen motor, interfaz y funciones educativas en un solo programa (§1.1). | B22 |
| R2-H12 | APLICADO | 05:42. M0 opera sobre la malla (03:174); ningún módulo muestra el bloqueo (05:70); M5 solo avisa (mod05_stiffness.py:942). | B22 |
| R2-H13 | YA APLICADO | Lote B19. | B19, B22 |
| R2-H14 | APLICADO | 05:27 y 05:52. Una sola solución analítica; los valores publicados de Cook (Štembera y Füssl, 04:177 y 04:201) son contraste externo. | B22 |
| R2-H15 | APLICADO | 04:269. mod00_mesh_quality.py:91-92: compacidad 0,25, el mínimo de Verdict. | B22 |
| R2-H16 | APLICADO | Tabla 3.6. Los materiales se definen en un diálogo (gui/dialogs/material_dialog.py). | B22 |
| R2-H17 | APLICADO | 04:328. «Prueba» → «respalda» (CRITERIOS §3; la iteración 1 ya retiró «demuestra»). | B22 |
| R2-H18 | APLICADO | 04:238 y 04:359. Entradillas que no anunciaban §3.6.3 ni §3.7.4. | B22 |
| R2-H19 | APLICADO | 04:467 y Tabla 3.8. Siete de las nueve etapas tienen módulo. | B22 |
| R2-H20 | APLICADO | Tabla 3.10. En valor absoluto, 0,144 %; el bloqueo se observa en las cinco mallas (04:212). | B22 |
| R2-H21 | APLICADO | Nota de la Tabla 3.10. El criterio del ejemplo canónico también es de exhaustividad (02b:205). | B22 |
| R2-H22 | APLICADO | 05:33. «Esa matriz» sin antecedente. | B22 |
| R2-H23 | APLICADO | 05:27. El 0,26 % es el error en el centro de la luz, no un máximo sobre A, B y C. | B22 |
| R2-H24 | YA APLICADO | 05:14, «a la vez» (lote B18). | B22 |
| R2-H25 | APLICADO | 05:49. La §3.7 solo discute dos de los ocho ítems. | B22 |
| R2-H26 | APLICADO | 05:23. Enumeración de cuatro en línea; los principios se enuncian en §1.2. | B22 |
| R2-H27 | DECISIÓN DEL AUTOR | 04:409, factores del reordenamiento (1,7 / 2,0 / 2,9): tres mediciones no concuerdan (unidad H con el equipo cargado: 3,01 / 1,86 / 2,31; control de la iteración 1: 2,9 / 2,2 / 3,6; docstring de solver.py: 2,1). Conviene volver a medir con el equipo en reposo o redondear a «entre dos y tres veces». | B22 |

### Unidad I: Anexos A, B y C: instalación, manual de uso y listados

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-I01 | APLICADO | 06:107, leyenda de la Fig. B.4 y de la Tabla B.3 (y 02b:155 en B19). health_report_dialog.py:513-517 y post_tab.py:405-451: «Resolver de todos modos»; solo la falta de elementos o de restricciones impide resolver. «Elemento implicado» → «entidad implicada» (la captura apunta a un material). | B19, B23 |
| R2-I02 | APLICADO | Tabla B.3. model_health.py:740-761: ρ < 0 → negative_density (error); ρ = 0 → gravity_no_density. | B23 |
| R2-I03 | APLICADO | Leyenda de la Fig. B.5. surface_3d_viewer.py:23-31: conmutador binario; «crudo» = σ = D·B(ξ,η)·u_e en una grilla por elemento. | B23 |
| R2-I04 | APLICADO | 06:27. README.md:45: «Requiere Python 3.11+»; con 3.10 no consta ninguna corrida. | B23 |
| R2-I05 | APLICADO | Listados C.1 y C.2: el comentario de Q9 y dos líneas ejecutables realineadas no eran copia literal (fem/shape_functions.py:52; fem/b_matrix.py). | B23 |
| R2-I06 | APLICADO | Leyenda de la Fig. B.8: la captura dice «J en centro del elemento» y los cuatro PG llevan su det J (3,9; 4,6; 4,3; 3,6); ninguno está seleccionado. | B23 |
| R2-I07 | APLICADO | Nota de M3: la captura dice «B en centro del elemento» y el panel muestra cuatro matrices. | B23 |
| R2-I08 | APLICADO | Nota de M2: det J es constante en todo paralelogramo; la superficie plana no mide la distorsión angular. | B23 |
| R2-I09 | APLICADO | Listado C.2: la Ec. 1.13 da la estructura de B; ε = B u_e va sin numerar (02:256-266). | B23 |
| R2-I10 | APLICADO | Tabla B.3, invalid_poisson: la D de tensión plana es definida positiva para −1 < ν < 1 (autovalores E/(1−ν), E/(1+ν), E/(2(1+ν))). | B23 |
| R2-I11 | APLICADO | Tabla B.2, M5: la integral no es «imposible» (02:297, 03:201). | B23 |
| R2-I12 | APLICADO | 06:197 y \clearpage antes de §B.8: las Figs. B.11-B.13 flotaban tras el título del comprobador de salud. | B23 |
| R2-I13 | APLICADO | 06:131: «memoria de cálculo» en minúscula (CRITERIOS §2). | B23 |
| R2-I14 | APLICADO | 06:116 y 06:174: la glosa pasa a la primera aparición del anexo, con la redacción canónica. | B23 |
| R2-I15 | APLICADO | Tabla B.3, bc_orphan_node: los GDL restringidos salen del sistema reducido (solver.py:52; model_health.py:552-555). | B23 |
| R2-I16 | APLICADO | Tabla B.1: espacio ante la coma y fila de deshacer con tres teclas para dos acciones (main_window.py:734-736). | B23 |
| R2-I17 | APLICADO | 06:120: el selector ofrece también σ1 y σ2 (post_tab.py:114-124). | B23 |
| R2-I18 | APLICADO | 06:107: la pestaña de proceso no resuelve; la resolución se dispara con F5 o al pasar al post-proceso. | B23 |
| R2-I19 | APLICADO | 06:56: «lo» sin antecedente. | B23 |
| R2-I20 | APLICADO | 06:18: installer/EduFEM.iss:279-298: ProgramData solo si la ruta no es ASCII sin espacios. | B23 |
| R2-I21 | APLICADO | 06:16: correlación de tiempos. | B23 |
| R2-I22 | APLICADO | 06:50: fitz solo en theory_viewer.py; matplotlib en la vista 3D y el círculo de Mohr; sympy en la memoria. | B23 |
| R2-I23 | APLICADO | 06:168: la variante Q9 tiene 25 nodos; coma ante «y» en coordinación de dos miembros. | B23 |
| R2-I24 | APLICADO | 06:76: término inglés sin glosa; una sola fila por tabla; el registro se crea con doble clic (pre_tab.py:15-16, 68). | B23 |
| R2-I25 | APLICADO | 06:103: la carga de superficie admite ángulo (pre_tab.py:402; Cook usa tracción tangencial). | B23 |
| R2-I26 | APLICADO | 06:357: oración sin verbo; «lagrangiano» en minúscula. | B23 |
| R2-I27 | APLICADO | preambulo.tex: upquote=true en el estilo pyedufem (las comillas invertidas de `coo_matrix` salían tipográficas). | B23 |
| R2-I28 | APLICADO | Leyenda de la Fig. B.12: la carga q = 500 N/mm entre los nodos 7 y 8 no está en el ejemplo canónico (example_library.py:109-117). | B23 |
| R2-I29 | APLICADO | 06:14: cláusula repetida a cuatro renglones. | B23 |
| R2-I30 | APLICADO | Tabla B.2, leyenda y nota de M7 (nota de la unidad F): mod07_assembly.py:4-11, «vuelo Bézier» eliminado; la captura muestra el esqueleto de K, el elemento E1 resaltado y la cabecera «9 nodos → 2N = 18 GDL · 6 GDL restringidos → 12 incógnitas». | B23 |
| R2-I31 | APLICADO | Tabla B.3, load_orphan_node (duda de la unidad I): el software se contradice (mensaje: la carga «SÍ entra al vector F»; pista del diálogo: «no afecta el resultado»). Se describe lo que hace el código: la carga entra en F, el nodo no tiene rigidez; si tiene un GDL libre, orphan_free_node lo reporta como singular. La pista del diálogo (health_report_dialog.py:128-132) queda como observación para el software. | B23 |
| R2-I32 | DECISIÓN DEL AUTOR | M4 (06:238, 06:242): «la deformación del elemento» se dibuja sobre una probeta genérica del panel (mod04_constitutive.py:549-572); el elemento del lienzo solo recibe el contorno. Más ambiguo que erróneo. | B23 |

### Unidad J: Anexos D, E, F y G: V&V extendida, SAP2000, formatos y memoria paso a paso

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-J01 | APLICADO | 06:475: «cotejar con»; y la Fig. D.3 no la genera un guion (J-02). | B24 |
| R2-J02 | APLICADO | Tabla D.1 y 06:531. fig_timoshenko_contorno y fig_cook_deformed son capturas del post-proceso (barra «Post-Proceso»); vv_timoshenko.py y vv_cook.py generan otras figuras (timoshenko_sigma_x_contour.png, cook_deformed.png). | B24 |
| R2-J03 | APLICADO | 06:531. §3.8 cita test_noncontiguous_ids, test_serialization y test_memoria_calculo, y bench_timing produce la Tabla 3.9. | B24 |
| R2-J04 | APLICADO | Tabla D.1, test_vv_extensions: omitía la prueba de reproducción de campos por E (la salvaguarda del defecto del Q4) y la de von Mises con σ_z; «V\&V» sin presentar en los anexos. | B24 |
| R2-J05 | APLICADO | Tabla D.1, test_fem: test_fem.py:53-65 solo imprime tensiones y calidad; :67-86 comprueba u finito y equilibrio; :89-170, las cargas superficiales. | B24 |
| R2-J06 | APLICADO | 06:524 y 04:104. test_interop.py:123-124: 12 nodos en total; en una malla 3×2 los compartidos son 8. | B24 |
| R2-J07 | APLICADO | Tablas D.1 y F.2: el comando en dos renglones (python -m / módulo) y el nombre de archivo sin cortarse en el guion bajo; el comentario literal del CSV ya va en su propio renglón (B24). | B24, B32 |
| R2-J08 | APLICADO | 06:546. vv_mms.py:385-386: la configuración base se guarda en mms_q4.csv y mms_q9.csv. | B24 |
| R2-J09 | APLICADO | 06:609. timoshenko_stress.csv: σ_y en C = 0,03 %, igual que σ_x; el orden de recuperación no distingue componentes; §3.7 da como razón la escala. | B24 |
| R2-J10 | APLICADO | 06:648 y leyenda de la Fig. D.2: la referencia es la curva analítica trazada (vv_timoshenko.py:250-285, eje y invertido); «en consistencia con» → «coherente con». | B24 |
| R2-J11 | APLICADO | 06:689: el documento resuelve también σ_y, τ_xy y los desplazamientos (hojas 5, 6, 8 y 9); enumeración sin conjunción. | B24 |
| R2-J12 | APLICADO | 06:691: H, L y q (y ahora b, A-19) están en la Nomenclatura; dos enumeraciones en línea pasan a lista. | B24 |
| R2-J13 | APLICADO | 06:693: kgf/cm², como declara el párrafo anterior y escribe §3.4. | B24 |
| R2-J14 | APLICADO | 06:713. main_window.py: la carga del proyecto no resuelve; auto_solve al pasar al post-proceso o con F5. | B24 |
| R2-J15 | APLICADO | 06:745. models/project.py: from_dict solo reconstruye el índice nodo→elementos; node_index_map se construye bajo demanda (:597-609). | B24 |
| R2-J16 | APLICADO | 06:749 (y 06:78, 03:226, 01:66 en B19/B23). model_io.py: solo las seis entidades; las restricciones sin valores (:171-181, :335-337). | B19, B24 |
| R2-J17 | APLICADO | 06:773. model_io.py exporta todos los nodos y solo 4 ids por elemento; la expansión solo actúa si el proyecto es Q9 (mesh_utils.py:157-158). | B24 |
| R2-J18 | APLICADO | 06:751: correlación de tiempos; «planilla» → «hoja de cálculo». | B24 |
| R2-J19 | APLICADO | 06:790: calco de «in place». | B24 |
| R2-J20 | APLICADO | 07:141 y 07:152. §2.2.4 asigna 2i y 2i+1 desde 0 por ordinal; aquí vale 2n−1, 2n porque los identificadores son contiguos y se cuenta desde uno. | B24 |
| R2-J21 | APLICADO | 07:213: von Mises no es una componente ni se extrapola (lo dice la oración siguiente). | B24 |
| R2-J22 | APLICADO | 07:193. anexo_calculo_data.tex: σ en el PG1 y las principales con tres decimales; von Mises (417,76) y los vectores de la extrapolación con dos, como las tablas. | B24 |
| R2-J23 | APLICADO | 07:141 y leyenda de la Fig. G.2: «no nulos», como el cuerpo. | B24 |
| R2-J24 | APLICADO | 07:123 (macro redefinida en el propio anexo; figuras/anexo_calculo_data.tex es común a las versiones y no se toca) y 07:201: punto y coma entre valores con coma decimal. | B24 |
| R2-J25 | APLICADO | 07:245: «consistente» → «coherente» (CRITERIOS §3). | B24 |
| R2-J26 | APLICADO | 07:249: «promediadas» repetido. | B24 |
| R2-J27 | APLICADO | 06:784 (propio). El motor integra con \|det J\| (batch.py:221): un elemento horario se resuelve; el comprobador lo advierte (negative_jacobian). «El elemento resultaría inválido» no describía a EduFEM. | B24 |
| R2-J28 | DECISIÓN DEL AUTOR | 06:779: en el diálogo DXF, la unidad «ft» reescala las coordenadas sin cambiar el sistema de unidades (dxf_import_dialog.py:56, 382-385); para esa opción no se cumple «el sistema de unidades del proyecto se actualiza». No verificado a fondo. | B24 |

### Unidad X: Verificación transversal propia de la iteración 1

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-X02 | APLICADO | Entrada [8] (Álvarez de Zayas): «; [fecha desconocida]» → «, [fecha desconocida]», como separan el año todas las demás entradas de la lista. | B17 |
| R2-X03 | APLICADO | CRITERIOS.md: la cabecera, copiada de la versión final, decía que rige capitulos_final/ (la copia de final1 conserva ese texto; no se toca). | B17 |
| R2-X04 | APLICADO | Metadatos del PDF: las palabras clave no coincidían con las del Resumen (faltaba «trazabilidad»). | B17 |
| R2-X05 | APLICADO | 03:16, 03:67 y Tabla 3.8. build.spec e installer/EduFEM.iss no incluyen tests/: la memoria viaja en el instalador, la batería de V&V se repite desde el repositorio (Anexo D). | B22 |
| R2-X06 | APLICADO | 02b:139 y 05:40 (propio). Con D-07 y H-14, los valores publicados de Cook (04:177, 04:201) cuentan como contraste externo; «las dos referencias externas» sugería que eran las únicas. | B33 |

### Unidad L: Longitud de las oraciones (CRITERIOS §3)

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-L01 | APLICADO | Oraciones de más de 60 palabras que introdujo o alargó esta iteración (largas2.py), partidas: 01:133, 02:19, 02:453, 02:471, 03:65, 03:108, 03:208, 03:217, 03:240, 04:104, 06:50 y 06:169. Quedan las fórmulas fijas (01:16, 01:44, 01:50, 01:59) y otras preexistentes de 61 a 68 palabras (03:62, 03:222, 04:61, 04:265, 06:83, 06:355, 06:548, 06:713, 06:729), que la iteración 1 ya había dejado. | B26 |

### Unidad P: Maquetación

| ID | Estado | Nota | Lotes |
|---|---|---|---|
| R2-P01 | APLICADO | Maquetación: el último párrafo del Anexo F quedaba solo en la p. 173 (tres renglones); se compacta sin cambiar su contenido. | B29 |

## Cambio posterior: PyMuPDF retirado del software (25-09-2026)

Después de cerrar la iteración, el autor decidió resolver la decisión abierta sobre la licencia retirando **PyMuPDF** (AGPL-3.0 o licencia comercial de Artifex) del software, y aplicar el cambio **sobre esta misma versión** en lugar de abrir una final3. La Teoría MEF ya no se muestra dentro de la herramienta: se compila como antes y se abre con el visor de PDF del sistema, igual que la memoria de cálculo. Pillow y pylatex no pueden reemplazarlo (el primero solo escribe PDF; el segundo solo arma el `.tex`), y el autor eligió el visor del sistema frente a `pypdfium2` (BSD/Apache) para no sumar ninguna biblioteca. Detalle del cambio en el software, las alternativas y las mediciones: `docs/notas/2026-09-25_pymupdf-retirado.md`.

| ID | Estado | Nota |
|---|---|---|
| R2-Z01 | APLICADO | 03, Tabla 2.5 (`tab:stack`): sale la fila «Lectura de PDF» (`PyMuPDF`); la de «Generación de PDF» suma los documentos de teoría. |
| R2-Z02 | APLICADO | 03, nota de la Tabla 2.5: sin las frases de la AGPL. Las bibliotecas que viajan en el instalador son permisivas (lista verificada en el paquete armado: `installer/dist_extra/LICENCIAS-TERCEROS.txt`); PyInstaller, GPL-2.0 con excepción; TeX Live, programas aparte con licencias propias que no se extienden a EduFEM; los avisos van en `LICENCIAS-TERCEROS.txt`. |
| R2-Z03 | APLICADO | 03, párrafo que sigue a la tabla: la memoria y los documentos de teoría se abren con el visor del sistema; la herramienta no incorpora biblioteca de lectura de PDF. |
| R2-Z04 | APLICADO | 06, Anexo A, «Dependencias»: sin PyMuPDF; `pylatex` cubre la memoria y los documentos de teoría. |
| R2-Z05 | APLICADO | 02b, «Versión evaluada»: sigue siendo la 1.0.0, revisión `91e3df0`. La frase «Es la versión que se distribuye con este documento» dejó de ser cierta y se reemplaza: el instalador sale de una revisión posterior de la misma versión (25-09) que solo retira PyMuPDF, y la batería de V&V produce en ella los mismos datos (verificado: sumas de control de `docs/vyv/datos/` y `docs/vyv/figuras/` antes y después de correr `vv_mms`, `vv_timoshenko` y `vv_cook`). Queda un `% DATO PENDIENTE` para el hash de esa revisión, que existe recién con el commit. La fila «Interviniente» de la tabla de variables (02b:96, «Instalador y repositorio») se deja: lo que se observa —motor, módulos y memoria— es idéntico en el instalador nuevo, y el párrafo explica la diferencia. |

No se tocaron los demás capítulos: la Tabla 1.1 («Libre (MIT), código abierto») y el requisito 5 ya decían lo que ahora también cumple el paquete binario. El material de defensa (presentación, video, `.pptx`, documento de defensa metodológica) **no se actualizó**, por decisión del autor; lo que falta cambiar está en `docs/notas/ESTADO.md`.

## Archivos tocados

- `tesis/capitulos_final2/`: `00b_nomenclatura.tex`, `01_introduccion.tex`, `02_marco_teorico.tex`, `02b_diseno_metodologico.tex`, `03_diseno_implementacion.tex`, `04_resultados.tex`, `05_conclusiones.tex`, `06_anexos.tex`, `07_anexo_memoria.tex`, `preambulo.tex`, `referencias.bib`, `CRITERIOS.md` y `figuras/fig_arquitectura.png`.
- `tesis/main_final2.tex`: comentario de cabecera y nota de elaboración propia (tras el índice de figuras).
- `tesis/figuras/generar_figuras.py`: pie de la Figura 2.2 («El motor (fem/) no importa la interfaz.»). La figura de la línea base (`tesis/figuras/fig_arquitectura.png`) no se regeneró.
- No se tocó el software (`fem/`, `gui/`, `education/`, `models/`, `file_io/`, `tests/`).
- Cambio posterior R2-Z (25-09): `capitulos_final2/02b_diseno_metodologico.tex`, `03_diseno_implementacion.tex` y `06_anexos.tex`. Ese mismo cambio sí tocó el software y su empaquetado (el visor de la Teoría, pruebas, `requirements.txt`, `build.spec`, el instalador): ver `docs/notas/2026-09-25_pymupdf-retirado.md`.
