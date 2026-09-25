# Auditoría general de la tesis final3

**Fecha**: 2026-09-25 · **Objeto**: `tesis/main_final3.pdf` (189 páginas) y sus fuentes,
`tesis/capitulos_final3/` · **Pedido del autor**: auditoría general y completa; reconocer lo
que está bien sin forzar errores; preguntas probables del tribunal.

## 1. Veredicto

La tesis está en condiciones de defenderse. Es coherente de punta a punta, es correcta en lo
técnico y es honesta sobre sus límites. Las cifras que recalculé a mano y las que los
verificadores contrastaron contra los datos y el código cuadran.

Encontré **una sola afirmación técnica falsa tal como está escrita**: la tesis atribuye al
método de soluciones manufacturadas (MMS) la verificación de la matriz constitutiva de los dos
estados planos, y el campo que eligió no puede detectar esa diferencia (H1). Ya estaba
anotada como decisión abierta en `docs/notas/ESTADO.md`. Hay que resolverla antes de la
defensa, porque una pregunta técnica bien dirigida la expone.

El resto no cambia ningún veredicto de la Tabla 3.10:
- precisiones que protegen la defensa (H2 a H5);
- tres observaciones nuevas sobre la interfaz, el PDF y el software (H6 a H8);
- ajustes de citas (H9);
- detalles de forma (H10).

**Qué hacer, en orden:**

| # | Acción | Hallazgo | Esfuerzo |
|---|---|---|---|
| 1 | Corregir las frases que atribuyen al MMS la verificación de la deformación plana, o cambiar el campo manufacturado | H1 | 1-2 h (frases) o 1 día (campo) |
| 2 | Matizar «criterios fijados de antemano» en σx y el equilibrio | H4 | 30 min; decides tú |
| 3 | Agregar `\XeTeXgenerateactualtext=1` al preámbulo y recompilar | H7 | 10 min |
| 4 | Completar «Versión evaluada» con `ec5876e` y `9232819` | H5 | 15 min |
| 5 | Traducir los rótulos en inglés y el 23,95 del software, o ajustar la frase de la p. 57 | H6 | 30 min |
| 6 | Corregir la cita de la p. 2, la nota de VisualFEA y citar FEM3 en p. 1164 | H9 | 30 min |
| 7 | Ensayar D3, D4 y D5 (MMS, τxy, flecha), y decidir si la flecha y τxy entran al texto | H2, H3 | ensayo |
| 8 | Corregir el deshacer del software, o no hacer esa demostración en vivo | H8 | 30 min |
| 9 | Precisiones menores | H10 | 1 h |
| 10 | Rehacer la presentación y el video con la formulación de final3 | §4 | lo que ya sabías |

## 2. Lo que está bien

Conviene defender estos puntos con seguridad; son fortalezas reales, no cortesía.

- **La formulación es una sola en todo el documento.** El problema, el objetivo general y la
  hipótesis son idénticos en la Introducción (pp. 2-5) y en la matriz de consistencia (§2.1.3,
  p. 46). Tres objetivos dan tres capítulos, tres conclusiones y tres recomendaciones, y la
  Tabla CR.1 (p. 110) cierra la tríada. Las dos preguntas de investigación responden a las dos
  cláusulas de la hipótesis.
- **La hipótesis es refutable.** La Tabla 2.4 (p. 53) da, para cada criterio, el umbral, su
  procedencia y «lo que lo refutaría». La tesis además explica por qué no es tautológica
  (p. 6) y lo muestra con un caso real (§3.7.2, p. 97).
- **Es honesta sobre sus límites.** Nunca afirma un efecto sobre estudiantes. Acota
  «validación» a su sentido estricto (§1.13, p. 35). Llama «diferencia», no «error», al
  contraste con SAP2000. Declara que el umbral de σ* se eligió después de observar el motor.
  Admite el 2,89 % de τxy y el defecto de la matriz de extrapolación. Da la incertidumbre de la
  referencia de Cook. Separa los límites fijados de antemano de los que aparecieron.
- **El marco teórico es correcto.** Comprobé:
  - las dos matrices constitutivas;
  - las funciones de forma del Q4 y del Q9, con Kronecker y partición de la unidad;
  - la convención del Jacobiano (Bathe, con J⁻¹ directo);
  - las entradas y el orden de la matriz de extrapolación del Q4 (a ≈ 1,866; b = −0,5;
    c ≈ 0,134);
  - las reglas de Gauss;
  - el ejemplo de von Mises en deformación plana (40 frente a 100);
  - el reparto qL/6, 4qL/6, qL/6;
  - las métricas de Verdict y la descomposición bilineal.
- **Las cifras son exactas y reproducibles.** Recalculé las soluciones analíticas de
  Timoshenko-Goodier en A, B y C (σx, σy, τxy), la flecha con corrección de cortante
  (2,02926 cm) y sin ella (1,9976 cm), E = 15 000√210 = 217 370 y 21,32 GPa. También la
  extrapolación de Richardson de Cook (≈ 23,97), las razones Q4/Q9 (15, 13 y 12), las tasas del
  MMS, todos los recuentos de GDL y la memoria de K densa y dispersa. El verificador de V&V
  reprodujo en memoria los CSV exactamente.
- **Lo que expone el software es lo que calcula.** La versión legible y la vectorizada del
  motor están atadas por una prueba de regresión (≤ 10⁻⁹), y la identidad del nodo está
  separada del índice de GDL. La revisión evaluada (`91e3df0`) existe, y los únicos cambios
  posteriores del software son el retiro de PyMuPDF.
- **El contraste externo de Cook es muy fuerte.** Los cinco valores Q4 coinciden con los
  publicados por Štembera y Füssl (p. 28, Tabla 5) hasta la última cifra.
- **La maquetación está limpia.** XeLaTeX sin errores ni referencias indefinidas. Los índices
  son correctos con los títulos largos, las figuras nuevas (2.1, CR.1 y CR.2) se leen bien y
  las 189 páginas no muestran desbordes a simple vista.

## 3. Hallazgos que conviene atender

Cada hallazgo se verificó contra el código, los datos o una corrida propia antes de anotarlo.

### H1 — El MMS no distingue tensión plana de deformación plana (prioridad alta)

**Qué pasa.** Con u = sin πx sin πy y v = cos πx cos πy (ec. 3.1), la traza de la
deformación y γxy son nulas en todo punto. Entonces σ = (D₁₁ − D₁₂)ε, y D₁₁ − D₁₂ = E/(1 + ν)
vale lo mismo en los dos estados planos. El término fuente y la tensión exacta son idénticos
en tensión y en deformación plana, y D₃₃ no interviene.

**Evidencia.** El verificador de V&V saboteó el motor en memoria:

| Sabotaje | Resultado |
|---|---|
| La rama de deformación plana devuelve la D de tensión plana | El MMS pasa 8/8, con filas idénticas |
| D₃₃ × 2 | El MMS pasa 8/8 |
| λ + 20 % | El MMS pasa 8/8 |
| Control: D₁₁ y D₂₂ × 1,1 | El MMS pasa 0/8, lo que confirma que el sabotaje funciona |

`test_vv_extensions` [8/8] detecta el intercambio TP/DP y el error en λ. Cook detecta D₃₃,
pero solo en tensión plana: **un error en el D₃₃ de la rama de deformación plana no lo
detectaría ninguna prueba**. El código está bien: el listado del Anexo C, p. 136, da
D₃₃ = E/[2(1 + ν)], que es correcto. Lo que falta es una prueba.

**Frases afectadas** (los números de línea son de `capitulos_final3/`):

| Archivo:línea (página) | Qué dice | Severidad |
|---|---|---|
| `04_resultados.tex:61` (p. 77) | «…descarta errores de orden en… la matriz constitutiva de ambos estados planos…» | falsa |
| `04_resultados.tex:363` (p. 96) | Repite la anterior por remisión («Eso descarta los errores… que enumera la §3.2») | falsa |
| `05_conclusiones.tex:66` (p. 107) | «La deformación plana solo se verifica con el método de soluciones manufacturadas» | falsa: el MMS no la verifica |
| `05_conclusiones.tex:49` (p. 106) | «…verificada por soluciones manufacturadas en ambos estados…» | imprecisa |
| `02b_diseno_metodologico.tex:144` (p. 48) | «Ejercita… las dos matrices constitutivas» | imprecisa |
| `02b_diseno_metodologico.tex:149` (p. 48) | «…quedan cubiertos… ambos estados planos» | imprecisa: sería una tercera excepción declarada |
| `04_resultados.tex:29` (p. 77) | «…término fuente deducido en cada caso de la ley constitutiva correspondiente» | cierta, pero induce a error |

**Qué hacer.** Hay dos caminos; la decisión ya estaba registrada en ESTADO.md.

- **(b) Corregir las frases**, el camino mínimo, de una o dos horas. Hay que decir que el MMS
  ejercita las dos ramas pero, con este campo, solo es sensible a D₁₁ − D₁₂. La matriz de
  deformación plana la comprueban la prueba de regresión de von Mises con σz y la inspección
  del código, y D₃₃ de tensión plana, Cook. Además, la deformación plana no tiene contraste
  externo, cosa que la tesis ya dice.
- **(a) Cambiar el campo**, el camino que hace verdadera la afirmación. Con
  v = cos πx cos 2πy el MMS conserva las tasas y detecta los errores (probado en
  `docs/vyv/mms_paso_a_paso/`). Exige regenerar los CSV, las Figuras 3.1, 3.2 y D.1, las Tablas
  3.1, D.2 y D.3 y la Figura CR.2.

Con tiempo, (a); con la defensa encima, (b). En cualquiera de los dos casos, conviene ensayar
la pregunta D3 del banco de la §5.

### H2 — La flecha de Timoshenko: el 0,26 % es sobre todo el apoyo puntual (prioridad media)

**Qué pasa.** Los apoyos son puntuales, en el eje neutro de las secciones extremas
(`tests/vv_timoshenko.py`, líneas 144-157). Timoshenko-Goodier reparte la reacción como
cortante en la sección, y una reacción puntual es una singularidad del continuo plano: bajo
ella el desplazamiento crece con ln(1/h). Resultado de las corridas de esta auditoría, que no
escriben en el repositorio:

| Malla Q9 | Flecha respecto del nodo de apoyo (lo que reporta la tesis) | Flecha respecto de la sección extrema media |
|---|---|---|
| 28×4 | +0,176 % | −0,031 % |
| 56×8 | **+0,263 %** | −0,029 % |
| 112×16 | +0,351 % | −0,029 % |
| 224×32 | +0,438 % | −0,028 % |

El error reportado **crece** al refinar, 0,00178 cm por refinamiento. Es exactamente
2P/(πEb)·ln 2, el hundimiento de Flamant bajo una fuerza puntual de borde, con P = 35 000 kgf
de reacción. Medida sin el hundimiento local del apoyo, la flecha coincide con la teoría
dentro del 0,03 % en todas las mallas. El criterio de < 3 % se cumple con cualquier malla
practicable.

**Por qué importa.** La tesis no afirma convergencia en este caso (p. 48), así que no hay
error de texto. Pero si el tribunal pregunta «¿y si refina la malla?», la respuesta intuitiva
(«baja») es falsa. Además, EduFEM es más exacto de lo que el 0,26 % sugiere.

**Qué hacer.** Como mínimo, ensayar la pregunta D5. Si quieres dejarlo en el texto, una
oración en §3.4 (p. 83) o en §3.7.1 (p. 97) explicaría que los apoyos son puntuales y que la
flecha así medida incluye un hundimiento local que crece levemente al refinar. Por la regla
de `CRITERIOS.md` («ninguna cifra sin respaldo en `tests/`»), las cifras nuevas exigirían
agregar la corrida de refinamiento a un guion del repositorio.

### H3 — τxy: el 2,89 % converge como debe (a favor de la tesis; prioridad media)

Al refinar, el error de τxy en B baja de 11,9 % (28×4) a 2,89 % (56×8), 0,72 % (112×16) y
0,18 % (224×32): orden h². Lo mismo ocurre con σy (3,61 %, 0,94 %, 0,24 %) y σx (0,159 %,
0,041 %, 0,010 %). Confirma lo que dice la p. 96: es error de discretización en una
componente secundaria, no un defecto. Es la mejor respuesta a «¿por qué SAP2000 da 0,16 % y
EduFEM 2,89 %?» (pregunta D4). Si se incorpora al texto, vale la misma advertencia sobre
`tests/` que en H2.

### H4 — «Criterios fijados de antemano»: matizar la redacción (prioridad media-alta)

**Qué pasa.** El historial de git distingue dos grupos de umbrales:
- **3 % en la flecha, 1,5 % en Cook y ±0,5 en las tasas.** Están escritos en los guiones desde
  el primer commit del proyecto (`c8885e0`, 1 de junio). Es el registro más antiguo, y no
  contradice que se fijaran de antemano.
- **< 1 % en σx, frente a la analítica y frente a SAP2000, y < 10⁻⁸ en el equilibrio.** Se
  agregaron a `tests/vv_timoshenko.py` el 16 de septiembre (`4a60eb2`). Para entonces la tesis
  ya reportaba desde junio los errores de σx que esos umbrales juzgan: 0,0414 % y 0,2066 %.

La frase de la p. 52 («quedaron fijados antes de las corridas que este documento reporta») es
literalmente cierta: las corridas reportadas se regeneraron después. Pero el Resumen («con
criterios fijados de antemano», p. I) y la Conclusión 3 («fijados de antemano», p. 104)
sugieren un *a priori* fuerte; la expresión se repite en las pp. 35, 102, 103 y 110. Por
contraste, que la tesis declare que *solo* el umbral de σ* se eligió después de observar hace
pensar que los demás no.

**Por qué importa.** Si un miembro del tribunal pregunta «¿fijó los umbrales antes de ver
los resultados?», la respuesta verdadera es «los de la flecha, Cook y las tasas, sí; los de σx
y el equilibrio los formalicé después, aunque como tolerancias de ingeniería independientes
del valor observado». Esa respuesta no debe contradecir el documento.

**Qué hacer.** Hay dos redacciones posibles:
- Tratar los criterios de σx y del equilibrio como la tesis ya trata el de σ*: declarar que se
  formalizaron durante el desarrollo.
- Redactar el conjunto así: «los umbrales son tolerancias de ingeniería, independientes del
  valor observado, y quedaron escritos en los guiones antes de las corridas definitivas; el
  veredicto no descansa en el valor exacto del umbral sino en el margen: lo observado queda
  entre 5 y 25 veces por debajo (Figura CR.2)».

La decisión es tuya: solo tú sabes con qué intención se eligió cada número (ESTADO.md ya te lo
pregunta).

### H5 — Versión evaluada: completar el hash y la revisión de los guiones (prioridad media)

- **El hash pendiente ya existe.** El comentario `% DATO PENDIENTE` de
  `02b_diseno_metodologico.tex:49` pide el hash del retiro de PyMuPDF: es **`ec5876e`**
  (25-09, 09:00). No se ve en el PDF (es un comentario), pero la oración de la p. 42 sigue
  sin hash.
- **La columna SAP2000 de la Tabla 3.2 no sale de `91e3df0`.** Imprime 127,8514 y −31,7852,
  que salen de `tests/vv_timoshenko.py` después del commit `9232819` (25-09: σx de SAP2000
  con los seis decimales de la captura). En `91e3df0` el guion da 127,8510 y −31,7850. Los
  porcentajes redondeados no cambian y los valores nuevos son los correctos según la captura.
  Aun así, «los datos se reproducen ejecutando los guiones sobre la versión identificada»
  (p. 75) no es exacto para esa columna.
- **Arreglo.** Una oración en «Versión evaluada» (p. 42), del tipo: «los guiones de
  verificación y validación que producen las cifras de este documento corresponden a la
  revisión `9232819`, que solo corrige la transcripción de σx de SAP2000 con seis decimales;
  el motor no cambia desde `91e3df0`». Actualizar también la fila «Interviniente» de la Tabla
  2.2 (p. 45).

### H6 — Quedan más rótulos en inglés de los que la tesis declara (prioridad media)

**Qué dice la tesis.** La p. 57 afirma que «en la versión evaluada quedan dos rótulos en
inglés»: «warning(s)» y «sparsity pattern».

**Qué hay en la interfaz** (verificado en el código):

| Rótulo | Dónde |
|---|---|
| «Q4 — bilineal (esperado: shear-locking)» | Ayuda ▸ Cargar Ejemplo (`gui/main_window.py:446`) |
| «Membrana de Cook (benchmark histórico)» | Ayuda ▸ Cargar Ejemplo (`gui/main_window.py:468`) |
| «ORTHO» | barra de estado (`gui/main_window.py:499`) |
| «toggle», «override» | diálogo de atajos (`gui/main_window.py:1691-1692`) |
| «↺ Reset» | M7 (`education/mod07_assembly.py:169`) |
| «BCs», «snap a Gauss», «Vuelo Bezier · sparsity pattern» | lanzador de módulos (`education/module_launcher.py:98, 105-106`) |
| «⚠ Locking volumétrico», «locking» | M4 (`education/mod04_constitutive.py:446, 487`) |

A eso se suman dos términos que no siguen el canon de la tesis:
- «Esfuerzo Normal σx…» en el selector de resultados del post-proceso
  (`gui/postprocessing/post_tab.py:118-122`);
- «condiciones de contorno» en la barra de estado (`post_tab.py:450`).

**Cifra vieja en la interfaz.** El menú de Cook dice «converge a u_y ≈ 23,95»
(`main_window.py:464`) y el mensaje del ejemplo, «vs ref 23,95» (`:908`). La tesis usa 23,96.
Si en la defensa abres el ejemplo de Cook, el tribunal lo verá.

**Qué hacer.** Traducir esos rótulos y actualizar el 23,95 en el software (es un cambio de
minutos), o reescribir la oración de la p. 57 para no fijar el número («quedan algunos
rótulos en inglés, como…»). Mientras tanto, «interfaz íntegramente en español» (pp. 4, 8, 16
y 56) queda algo fuerte.

### H7 — El PDF codifica el punto y coma como otro carácter (prioridad media; arreglo de una línea)

**Qué pasa.** Con XeLaTeX y la Times New Roman del sistema, 427 de los 454 «;» del PDF se
extraen como U+037E, el signo de interrogación griego, que se ve idéntico. El PDF de final2,
compilado con pdflatex, no tenía ninguno.

**Por qué importa.** No se nota al leer, pero sí al copiar o buscar texto («;» no encuentra
esos caracteres). Además, los detectores de plagio suelen marcar el reemplazo de caracteres
por homoglifos griegos o cirílicos como intento de manipulación. Si la Carrera pasa la tesis
por uno, es un riesgo evitable.

**Arreglo probado** (en un documento mínimo, fuera del repositorio): agregar
`\XeTeXgenerateactualtext=1` en `capitulos_final3/preambulo.tex`, después de cargar
`fontspec`. Con esa línea, la extracción devuelve «;» ASCII. Falta recompilar la tesis y
comprobar con `pdftotext` que el recuento de U+037E queda en cero.

### H8 — Observación sobre el software: el deshacer no revierte la edición de un vértice (prioridad media)

**Qué pasa.**
- `Element.to_dict` devuelve la lista viva `node_ids` (`models/element.py:56`).
- `UndoStack.capture` guarda `project.to_dict()` sin copiarla (`models/undo_stack.py:59`).
- La tabla de Elementos captura el estado y después modifica `elem.node_ids[ci-1]` en su lugar
  (`gui/preprocessing/pre_tab.py:1309-1312`), así que la instantánea queda modificada también.

Reproducido sin pantalla: [1, 2, 5, 4] → editar N1 → Ctrl+Z → [5, 2, 5, 4].

**Por qué importa.** La p. 66 dice que el deshacer copia el estado «a una estructura de datos
independiente», y para la conectividad no es así. Sobre todo, **no conviene editar un vértice
en la tabla y pulsar Ctrl+Z en una demostración en vivo**.

**Qué hacer.** Devolver una copia en `to_dict` (`"node_ids": list(self.node_ids)`) y agregar
el caso a `tests/test_undo_stack.py`. Queda como observación: esta auditoría no tocó código.

### H9 — Citas: la bibliografía está sana; hay tres ajustes de atribución (prioridad baja-media)

**Lo que está bien.**
- Las 26 claves citadas existen, y la lista numera de [1] a [26] por orden de mención.
- Ningún DOI, ISBN, fascículo ni página está inventado: los DOI coinciden con los ejemplares
  y con Crossref.
- De las 138 citas con localizador, 120 caen en páginas ya respaldadas en
  `tesis/respaldo_citas/`. De las 18 nuevas, 17 sostienen lo que se afirma.
- Unas cuarenta afirmaciones clave se contrastaron contra los PDF y cuadran: Oberkampf,
  Salari-Knupp, Štembera, Timoshenko art. 21, CSI p. 179, ED-Elas2D pp. 246 y 253, Bishay,
  Lee, Pérez-Santiago, Verdict y la metodología.

**Ajustes verificados en la fuente:**
- **Intro, p. 2 (`01_introduccion.tex:14`).** «Las herramientas comerciales no están
  diseñadas con un propósito didáctico explícito [3, p. 1160]». La p. 1160 de Pérez-Santiago
  y Campos no lo dice: solo recoge la preocupación de otros autores por el uso del software
  comercial «como una caja negra» y distingue los programas educativos del software
  comercial. Lo dicen de forma directa Suárez et al., p. 246, y Lee y Ryu, p. 872 («none of
  these offer educational features that disclose the basis of the computational
  procedures»), las dos ya en la bibliografía.
- **Tabla 1.1, p. 14.** La licencia «Comercial» de VisualFEA, y «programa comercial» o «cerrado
  y de pago» en las pp. 12-13, no constan en las dos publicaciones de Lee citadas en el
  encabezado: solo dicen que VisualFEA fue desarrollado por sus autores. Probablemente es
  cierto, pero la nota de la tabla dice que esa columna sale de esas publicaciones. Hay que
  ajustar la nota o declarar la procedencia del dato.
- **Localizadores incompletos:**
  - La fórmula de las tensiones principales (p. 29, `02_marco_teorico.tex:348`) es la ec. (16)
    de la p. 17 de Timoshenko-Goodier: el localizador debería ser «pp. 12-14, 17».
  - Los miniproyectos de Bishay (p. 12, `02_marco_teorico.tex:17`) están en la p. 1007 y en las
    pp. 1014-1016, no en las pp. 1011-1012.

**Mejora a favor tuya.** Pérez-Santiago y Campos, p. 1164, dicen que, según la mediana, los
especialistas consideran esenciales todas las competencias del cuestionario **excepto FEM3**.
FEM3 es justamente el único ítem que la tesis excluye por no exponerlo (pp. 49 y 93). Citarlo
convierte esa exclusión, que podría parecer conveniente, en una exclusión respaldada por la
propia fuente, y responde de antemano al «18 de 19».

**Formato** (menor):
- La lista usa «págs.» y el cuerpo, «p./pp.».
- Hay cortes de palabra «SA-FE» en [18] y «Cambrid-ge» en [20].
- El «doi:» de [26] va en minúscula.
- [8], Álvarez de Zayas, lleva una nota descriptiva que el propio `.bib` dice evitar.
- Tres citas de atribución concreta van sin página (pp. 8, 13 y 58).
- La p. 10 presenta el superíndice como la forma Vancouver, pero la recomendación ICMJE dice
  «números arábigos entre paréntesis»: la desviación real es corchetes en vez de paréntesis.
- Tres entradas del `.bib` no se citan (`rutten2012learning`, `chi2014icap`,
  `atkinson2000learning`). No salen en la lista, pero el comentario de
  `referencias.bib:273-280` sigue diciendo que sostienen la §1.2.

### H10 — Precisiones menores de coherencia y forma (prioridad baja)

- **Requisito 2 frente a la cláusula (b).** La p. 56 dice que «los dos primeros requisitos
  sirven a la trazabilidad y el tercero a su verificabilidad». Pero la reproducción a mano de
  la memoria, que es el requisito 2, es un criterio de la cláusula (b), verificabilidad (Tabla
  2.4). Basta con «el segundo, a las dos».
- **Figura 2.1** (p. 44). «niveles: caja negra | a la vista» pisa el borde del círculo
  izquierdo, y «Variable interviniente (solución)» toca los bordes de su recuadro. Hay que
  bajar el `fontsize` en `generar_figuras_formulacion.py:177` y `:188`. La flecha
  «dependiente → EduFEM» sigue el ciclo de la lámina del Ing. Miranda; para otros miembros del
  tribunal podría leerse como «el efecto causa a EduFEM». Si no se quiere explicar de palabra,
  un rótulo corto («motiva») lo evita.
- **Figura CR.2.** Dice «Tasa L², Q9: desvío de 0,0005»; con log₂ exacto es 0,0004. La causa
  es que el script usa el `h` redondeado a seis decimales del CSV del dominio distorsionado
  (`generar_figuras_formulacion.py:79-86`). Es cosmético.
- **Resumen.** Tiene 310 palabras, frente a 150-250 en APA 7. No hay *abstract* en inglés. Se
  decide con el Reglamento (H-1).
- **Fuentes no incrustadas.** Las páginas del Anexo E (pp. 148-158) usan Times New Roman sin
  incrustar, heredada del PDF de Word `anexos/validacion_sap2000.pdf`. En Windows se ve bien.
  Solo importa si la biblioteca exige PDF/A o si imprime en un equipo sin esa fuente.
- **Figura D.3** (p. 145). Ocupa sola un tercio de página y deja el resto en blanco.
- **La memoria y la versión legible.** La p. 73 («recalculada con la versión legible del
  motor»), la p. 91 («cada valor que la memoria muestra… lo recalcula con la versión
  legible») y la p. 104 («reconstruye todo el procedimiento con la versión legible») dicen más
  de lo que ocurre. El código recalcula con la versión legible solo el elemento que desarrolla
  (`file_io/memoria_calculo.py`, `_recompute_showcase`). K, u, las reacciones y las tensiones
  vienen del motor por lotes. Los valores coinciden gracias a la prueba de regresión, así que
  basta con decirlo así.
- **«Resolver de todos modos».** La p. 67 dice que la opción «no existe cuando faltan los
  elementos o las restricciones». En realidad el botón aparece, y la resolución se corta con
  un mensaje (`gui/postprocessing/post_tab.py:442-452`). El Anexo B (p. 119) lo describe bien
  («ni así»).
- **Anexo B, p. 120.** «Siete módulos educativos (M1 a M7)… recorren en orden el procedimiento
  de cálculo, es decir, la secuencia… que va de las funciones de forma a la recuperación de
  tensiones». Leída tal cual, sugiere que los módulos llegan a la recuperación de tensiones,
  pero llegan hasta el ensamblaje (pp. 91 y 107). Basta con «recorren en orden las etapas del
  procedimiento hasta el ensamblaje».
- **«Solo retira la biblioteca PyMuPDF»** (p. 42). El commit `ec5876e` también excluyó del
  paquete otros extras que se colaban desde el entorno (entre ellos `certifi`, MPL-2.0) y
  agregó `LICENCIAS-TERCEROS.txt`. Nada de eso cambia el cálculo, pero la oración puede decir
  «solo cambia el empaquetado».
- **«Licencias permisivas»** (p. 59). Las DLL de NumPy y SciPy traen `libgfortran`, GPL-3.0
  con la excepción de la biblioteca de ejecución de GCC. Figura en `LICENCIAS-TERCEROS.txt` y
  no afecta la licencia MIT, pero «permisivas —BSD, MIT o similares—» simplifica. Si preguntan
  por licencias, conviene saberlo.
- **Figuras del Anexo G** (`mem_*.png`). Son de una versión anterior del generador: sin
  tildes y «x84.1». Regenerarlas les pone tildes y «×» con la misma geometría (ya estaba
  anotado en ESTADO). Ojo: el ejemplo canónico del software está en «SI (N, mm, MPa)», así que
  la barra de color regenerada dirá MPa, mientras el anexo lo lee en kgf/cm². Conviene
  decidir la unidad antes de regenerarlas.

## 4. Pendientes que ya conocías (no son hallazgos nuevos)

- **Preliminares.** La declaración de originalidad, la dedicatoria y los agradecimientos están
  fuera para la predefensa. Para la entrega final falta descomentar la línea en
  `main_final3.tex`. También falta decidir el párrafo de uso de inteligencia artificial, que
  está comentado en `00_preliminares.tex` y del que depende la pregunta E10.
- **Reglamento de Graduación (H-1).** De él dependen los márgenes y el interlineado (hoy APA:
  2,54 cm y doble espacio), la extensión del resumen, el *abstract* y si la carátula lleva
  tutor.
- **Material de defensa desactualizado.** La presentación y el video siguen `main_final.tex`:
  no tienen la formulación de final3 (tres objetivos, problema en el molde del tribunal,
  variables renombradas) y la lámina de licencias nombra PyMuPDF. `contexto_defensa.pdf` cita
  páginas de `main_final`, y su respuesta PD-04 también nombra PyMuPDF.
- **Instalador sin PyMuPDF.** Falta probarlo en pantalla: la Teoría MEF tiene que abrirse en el
  visor del sistema.

## 5. Preguntas probables del tribunal

Las páginas son las del `main_final3.pdf` de 189 páginas. Las respuestas van en primera
persona, para decirlas tal cual, y son cortas a propósito: el detalle está en la página
citada. Marca **(difícil)**: la pregunta toca un punto donde la tesis es más vulnerable;
conviene ensayarla. Varias de las metodológicas ya tienen respuesta extendida en
`tesis/defensa_metodologica/contexto_defensa.pdf` (armado sobre `main_final`: sus números
de página no son los de final3, y su respuesta PD-04 sobre la licencia quedó vieja: ver E6).

### A. Formulación y metodología

**A1. «Su problema está en futuro ("podrá incidir") y fechado ("en la gestión 2026"). ¿La
relación entre transparencia y trazabilidad depende del año?»**
No: la fecha delimita el estudio, no la relación. El problema se atiende con el software
que desarrollé y evalué en 2026 (Delimitación, p. 3). Adopté el molde «¿De qué manera…
podrá incidir…?» de la lámina del Ing. Miranda.

**A2. (difícil) «Su problema pregunta cómo incide la escasa transparencia en la baja
trazabilidad. ¿Dónde midió la trazabilidad de un software de caja negra?»**
La variable independiente tiene dos niveles, de presencia o ausencia (§2.1.2, p. 42). El
nivel de caja negra está documentado en la Tabla 1.1 (p. 14): el software comercial
registra «Baja (caja negra)» en el cálculo paso a paso y «sin el desarrollo matricial» en
la memoria. Un programa que no expone ninguna etapa da cero en mis indicadores (7/7, 9/9).
La respuesta al problema está en las Conclusiones (p. 103): la opacidad deja un
procedimiento que no puede seguirse hasta sus datos; exponerlo, con su verificación, lo
vuelve trazable y verificable. Ejemplo oral: en SAP2000 no hay forma de ver de dónde sale
la tensión de un nodo; en EduFEM, M1 a M7 y la memoria la llevan hasta los datos (Anexo G).

**A3. (difícil) «Su hipótesis es obvia: si muestro el procedimiento, se puede seguir.»**
Mostrar no asegura que lo mostrado esté completo ni que sea correcto (p. 6 y §2.1.6,
p. 52). Podía fallar, y falló una vez: la matriz de extrapolación del Q4 estaba mal; los
estudios de convergencia no lo delataron y la memoria sí (§3.7.2, p. 97). Además, que lo
mostrado sea lo calculado no es automático: lo sostiene una prueba de regresión entre las
dos versiones del motor, con error ≤ 10⁻⁹ (§2.2.5, p. 64).

**A4. «¿Por qué EduFEM es una "variable interviniente"? En Hernández-Sampieri la
interviniente media entre la independiente y la dependiente.»**
Uso el esquema del Taller de la Carrera, donde la interviniente es la solución con que se
actúa sobre la causa (Figura 2.1, p. 44). En la ciencia del diseño es el artefacto: la
intervención cuyo efecto se evalúa.

**A5. «¿Cuál es su población y su muestra?»**
La unidad de análisis es el procedimiento de cálculo, no personas. Población: los
problemas de elasticidad lineal plana que pueden resolverse con cuadriláteros
isoparamétricos. Muestra dirigida por valor probatorio: soluciones manufacturadas,
Timoshenko y Cook, más el ejemplo canónico. El universo de contenido (9 etapas y 18 ítems)
se recorre completo, sin muestreo (§2.1.4, p. 46).

**A6. (difícil) «Es un software educativo: ¿por qué no lo probó con estudiantes, con
pretest y postest?»**
Porque mis preguntas son de cobertura y de exactitud, y esas se responden con simulación y
pruebas (Wieringa, Tabla 1.1, p. 5 de su libro). «Educativo» califica el propósito de
diseño, no un efecto medido (p. 1). Lo declaro como límite (p. 106) y dejo recomendada esa
investigación (p. 110).

**A7. «¿Esto es una tesis o un proyecto de grado?»**
Tesis tecnológica de carácter propositivo (García-Córdoba, p. 91): la hipótesis es la
solución tentativa y se prueba construyéndola y evaluándola (p. 6). Respaldo en
`contexto_defensa.pdf` (Manual de Procesos UATF, p. 93).

**A8. «¿Por qué ciencia del diseño y no el método experimental?»**
Porque el conocimiento se obtiene construyendo el producto y evaluándolo con rigor
(Hevner, pp. 75 y 83). Uso cuatro de sus cinco familias de evaluación (p. 40). Y sí hay
experimento, en el sentido de Wieringa (p. 247): los factores son el tipo de elemento y la
densidad de malla, y la respuesta es la exactitud (§2.1.1, p. 41).

**A9. (difícil) «Su OE2, "Desarrollar EduFEM", repite el objetivo general.»**
El objetivo general es el fin de toda la tesis: desarrollar para mejorar la trazabilidad y
la verificabilidad. El OE2 es solo la construcción, con sus cuatro componentes y su fin
propio: exponer cada etapa sobre el modelo del usuario. Construir no basta: el OE1 fija
qué construir (los requisitos) y el OE3 establece si se logró. El objetivo general se
cumple con los tres (Tabla CR.1, p. 110).

**A10. (difícil) «¿Por qué el diseño metodológico está dentro del Capítulo 2, que se titula
"Desarrollo de EduFEM"?»**
El índice de la Carrera tiene tres capítulos: marco teórico, diseño e implementación del
modelo y resultados (p. 9). El «modelo» tiene dos acepciones, que aclaro al abrir el
capítulo (p. 39): el de la investigación, con sus variables e instrumentos, y el numérico
que implementa el software. El primero encuadra al segundo, y por eso va antes.

**A11. (difícil) «¿Quién fijó los umbrales de 3 %, 1 % y 1,5 %? ¿Por qué esos y no
otros?»**
Los fijé yo, como tolerancias de ingeniería, y así lo declaro (Tabla 2.4, p. 53). El
veredicto no depende del valor exacto: lo observado queda un orden de magnitud por debajo, y
el criterio más cercano usa la quinta parte de su margen (Figura CR.2, p. 105). El ±0,5 de
las tasas tiene razón propia: separa el orden esperado del inmediato inferior, que es lo que
produce un error de programación. *Conviene llevar pensado por qué 3 % en la flecha y 1,5 %
en Cook. Si preguntan si los fijaste antes de ver resultados, responde con la verdad según
H4: los de la flecha, Cook y las tasas están en los guiones desde el primer commit; los de
σx y el equilibrio se formalizaron el 16-09.*

**A12. (difícil) «El 18 de 18 lo marcó usted. ¿No es autoevaluación?»**
Sí, y lo declaro (p. 106). Lo que no es mío es el universo: un consenso publicado de 67
expertos (Pérez-Santiago y Campos, pp. 1162-1163). La regla de marcado está escrita
(§2.1.5, p. 50) y cada celda remite a una función o una captura que cualquiera puede
comprobar. Recomiendo la revisión por docentes (p. 110). FEM3, el único ítem excluido por no
exponerlo, es también el único que los propios expertos no consideran esencial
(Pérez-Santiago y Campos, p. 1164; ver H9).

**A13. «El consenso es de expertos mexicanos de ingeniería mecánica. ¿Sirve para
ingeniería civil en Bolivia?»**
Los 18 ítems son del procedimiento del MEF —mallado, post-proceso, formulación
isoparamétrica, Gauss, verificación—, que es el mismo en las dos ingenierías. La tabla no
pondera importancia, solo registra si hay instrumento. Los ítems propios de una tipología
quedaron fuera (p. 51).

**A13b. «¿Es un "consenso" o una encuesta?»**
Es una encuesta Likert a 67 expertos de la industria y la academia. Llamo consenso al acuerdo
que reportan los autores: según la mediana de cada ítem, los especialistas consideran
esenciales todas las competencias, salvo FEM3 (p. 1164 del artículo). No es un método Delphi,
y no lo presento como tal.

**A13c. (difícil) «Según Álvarez de Zayas, que usted cita, el campo de acción es "parte del
objeto". ¿Su campo lo es?»**
*Prepararla: es la pregunta metodológica más fina que puede hacer un tribunal formado en
ese texto.* Álvarez (p. 13) define el campo como la parte del objeto formada por los aspectos,
propiedades y relaciones que se abstraen de él. La tesis define el objeto como el análisis
por el MEF, es decir, su procedimiento de cálculo, y el campo como «los medios de cálculo con
que ese análisis se enseña» (p. 3), sin cita. Respuesta posible: el campo es el aspecto del
objeto en que actúo, la exposición de ese procedimiento en el medio de cálculo; la
trazabilidad y la verificabilidad son propiedades del propio procedimiento. Fue una decisión
tomada con el marco del tribunal («objeto técnico, campo pedagógico»). Si quieres blindarla,
redacta el campo como aspecto del objeto y cita a Álvarez, p. 13.

**A14. «¿Cómo podría haber resultado falsa su hipótesis?»**
Con un solo caso en contra de cualquier criterio: una etapa sin módulo, una tasa fuera de
±0,5, un error por encima del umbral, un Q4 que no fuera más rígido que el Q9. Lo detalla
la columna «Lo refutaría» (Tabla 2.4, p. 53).

**A15. «¿Por qué "escasa" y no "nula" transparencia?»**
Porque «nula» se refuta con un contraejemplo: ED-Elas2D expone las matrices, y la Tabla 1.1
registra al software comercial como «Baja», no como inexistente.

**A16. «¿Qué aporta al conocimiento, además del programa?»**
Tres cosas (p. 105): el software; conocimiento de diseño reutilizable (módulos sobre el
modelo del usuario, memoria generada con la versión legible del motor, versión legible como
oráculo); y conocimiento de evaluación (batería de V&V reproducible, prueba de reproducción
polinómica, tabla de cobertura).

### B. Estado del arte y pertinencia para ingeniería civil

**B1. (difícil) «ED-Elas2D ya mostraba las matrices paso a paso en 1998. ¿Qué agrega
EduFEM?»**
La memoria de cálculo reproducible a mano, la verificación y validación publicada con la
herramienta, y un post-proceso que explica la respuesta: sonda cruda y suavizada, Mohr,
reacciones frente a la carga. Los propios autores de ED-Elas2D reconocen que su
post-proceso no explica el suavizado nodal (p. 253 de su artículo). Además, EduFEM es
libre, en español y se instala hoy en Windows 10/11 (p. 14 y Tabla 1.1).

**B2. «¿Por qué no tomó CALFEM, FEniCS u OpenSees y les puso una interfaz?»**
Para controlar qué se expone del motor y tener una versión legible, elemento a elemento,
que sirva a los módulos y a la memoria (p. 4 y §2.2.2, p. 60). Las bibliotecas exponen el
cálculo en código, no en una representación guiada sobre el modelo.

**B3. (difícil) «El título dice "análisis estructural", pero EduFEM no resuelve pórticos.»**
En el documento, «análisis estructural» tiene la acepción restringida de análisis de
tensiones y deformaciones de elementos modelados como continuos planos (p. 7): vigas de
gran peralte, muros cargados en su plano, secciones de presas, muros de contención y
túneles. El dominio plano es una decisión de diseño: es el mínimo donde aparecen el
Jacobiano y la cuadratura en dos direcciones (p. 8).

**B4. «¿Qué problema real puede resolver un ingeniero con EduFEM?»**
Los de la respuesta anterior, en régimen elástico lineal: sin fisuración, sin no linealidad
y sin 3D (p. 7). Su fin es formativo: aprender y comprobar el procedimiento, no reemplazar
al software de diseño (§3.7.3, p. 98).

**B5. «¿En qué asignatura de la Carrera se usaría?»**
*Prepararla con el plan de estudios en la mano.* La tesis propone tres prácticas (p. 109).

**B6. «¿Por qué sus textos clásicos son ediciones de hace más de diez años?»**
Lo que tomo de ellos es el núcleo consolidado del método, y son las ediciones que tuve en
mano para verificar cada página citada; la literatura reciente la uso para la enseñanza del
MEF, la V&V y las bibliotecas (p. 11).

**B7. «¿Revisó tesis o trabajos de la UATF o de Bolivia?»**
*Prepararla.* La revisión se declara no exhaustiva (p. 12). Si hay antecedentes locales,
conviene nombrarlos; si no los hay, decirlo.

### C. Teoría del MEF

**C1. «Explique el bloqueo por cortante. ¿Por qué lo sufre el Q4 y no el Q9?»**
El Q4 bilineal no puede curvarse en flexión pura sin generar una deformación cortante que
la solución exacta no tiene; esa energía parásita lo rigidiza. El Q9 bicuadrático sí
reproduce la curvatura (p. 26). Cook lo muestra: −7,85 % con el Q4 frente a −0,144 % con
el Q9 a 8 elementos por lado (Tabla 3.4, p. 86).

**C2. «¿El Q9 está libre del bloqueo volumétrico? ¿Qué pasa con ν → 0,5 en deformación
plana?»**
No está libre: con integración completa también bloquea (Hughes, p. 222). M4 advierte al
acercarse ν a 0,5 y el comprobador de salud rechaza ν fuera de (−1; 0,5) (Tabla B.3). La
corrección (integración reducida selectiva, B̄) queda recomendada (p. 108).

**C2b. «¿La formulación B̄ corrige también el bloqueo por cortante?»**
En la forma de Hughes (pp. 232-234), B̄ trata la parte volumétrica. Contra el cortante se usan
la integración reducida selectiva de los términos de corte o las deformaciones supuestas.
Ojo: la p. 27 y la Recomendación 1 (p. 108) presentan B̄ junto a los «dos bloqueos»;
conviene precisarlo en el texto o en la respuesta.

**C3. «¿Por qué integración completa? ¿Qué pasa con un solo punto de Gauss en el Q4?»**
Con un punto, la rigidez queda con rango deficiente y aparecen modos de energía nula, el
reloj de arena (p. 27). M5 permite quitar puntos y avisa de esos modos.

**C4. (difícil) «¿Qué pasa si el estudiante dibuja un cuadrilátero cóncavo o con los nodos
en sentido horario?»**
Horario: el modo dibujo y la importación DXF lo reordenan, el comprobador de salud avisa, y
como la rigidez se integra con |det J| el resultado sigue siendo correcto. Cóncavo: det J
puede ser negativo en algún punto; el motor solo se detiene si |det J| no supera el umbral
en los puntos de Gauss; lo señalan la calidad de malla (elemento «malo») y M0 en las
esquinas. No se detiene: se advierte (pp. 64 y 68).

**C5. «¿Por qué extrapola las tensiones desde los puntos de Gauss y no usa los puntos
superconvergentes?»**
Por una única ruta para Q4 y Q9, con M cuadrada, que conserva la variación del campo
dentro del elemento. El costo está declarado y el orden resultante se mide: 1,54 en Q4 y
2,00 en Q9 (pp. 30-31 y 79).

**C6. «¿Por qué la tensión del Q4 converge a 1,54 y no a 2?»**
Es una observación propia; la literatura no fija ese orden para esta secuencia. La
explicación plausible es la capa de contorno, donde los nodos promedian de un solo lado; no
la contrasté y dejo el experimento propuesto (pp. 78 y 109).

**C7. «Si K es simétrica y definida positiva, ¿por qué LU y no Cholesky?»**
SciPy trae la LU dispersa (SuperLU) y no una Cholesky dispersa; agregarla sumaría una
dependencia. Para tamaños educativos basta: 33 282 GDL en menos de un segundo (Tabla 3.9,
p. 98). Cholesky queda recomendada (p. 109).

**C8. «¿Qué es el reordenamiento de mínimo grado?»**
Renumera las incógnitas para reducir el llenado de los factores; frente a COLAMD acelera
entre 1,7 y 2,9 veces (p. 99).

**C9. «¿Por qué σz ≠ 0 en deformación plana y qué cambia en von Mises?»**
Por εz = 0, σz = ν(σx + σy). Omitirla cambia el resultado: con σx = σy = 100 y ν = 0,30, 40
en vez de 100 (p. 30). EduFEM la incluye en todas las rutas.

**C10. (difícil) «¿Tiene sentido mostrar von Mises para el hormigón? Es un criterio para
metales dúctiles.»**
EduFEM lo reporta como la medida escalar con que se resume el estado tensional, como hace
el software comercial (Cook, p. 117), no como criterio de falla: el análisis es elástico
lineal y no evalúa capacidad (Anexo E, p. 147). Para el hormigón, el post-proceso muestra
las tensiones principales σ₁ y σ₂ (p. 120).

**C11. «¿Qué significa det J y por qué se usa su valor absoluto?»**
Es el factor local de cambio de área entre el cuadrado de referencia y el elemento real
(p. 23): el área es positiva aunque la numeración sea horaria.

**C12. «¿Cómo se reparte una carga distribuida en una arista de Q9?»**
Con q constante, qL/6, 4qL/6 y qL/6: la mayor parte va al nodo medio (p. 28); M6 lo
muestra.

### D. Verificación y validación

**D1. «Si no hizo ensayos físicos, ¿por qué habla de validación?»**
En sentido estricto la validación exige experimentos, y lo digo (p. 35). Mi contraste es
verificación de solución y comparación código a código. En el OE3, «validar» cubre además
el sentido metodológico: comprobar que la solución cumple criterios fijados de antemano
(p. 35).

**D2. «Explique el MMS. ¿Qué verifica y qué no?»**
Elijo un campo exacto, deduzco la fuerza de cuerpo que lo produce y mido si el error baja
con la tasa teórica (pp. 36 y 76). Verifica ensamblaje, cuadratura, mapeo sobre elementos
distorsionados, fuerza de volumen y restricciones no homogéneas. No verifica la
extrapolación de tensiones: por eso hay una prueba aparte (p. 79).

**D3. (difícil) «¿Su solución manufacturada distingue tensión plana de deformación plana?»**
Hoy, no. Con u = sin πx sin πy y v = cos πx cos πy, la traza de la deformación y γxy son
nulas en todo punto, así que σ = (D₁₁ − D₁₂)ε, y D₁₁ − D₁₂ = E/(1 + ν) en los dos estados:
el término fuente es el mismo y D₃₃ no interviene. **Ver el hallazgo H1 del informe: la
tesis afirma lo contrario en varias frases, y hay que corregirlas antes de la defensa.**
Respuesta después de corregir: la matriz de deformación plana la comprueba la prueba de
regresión de von Mises con σz, y el término de corte, la membrana de Cook, que coincide con
un código publicado; un campo como v = cos πx cos 2πy volvería sensible al MMS.

**D4. (difícil) «¿Por qué EduFEM tiene 2,89 % de error en τxy y SAP2000 solo 0,16 %?»**
Es error de discretización en una componente secundaria, entre seis y treinta y cinco veces
menor que σx (p. 96), y converge como corresponde a un Q9: 11,9 % con 28×4, 2,89 % con
56×8 y 0,72 % con 112×16 (orden h², corrida de esta auditoría). El criterio de aceptación
está sobre σx porque es la magnitud primaria de la flexión (§2.1.6).

**D5. (difícil) «¿Cómo modeló los apoyos? ¿Qué pasa con la flecha si refina la malla?»**
Un apoyo fijo y uno móvil, puntuales, en el eje neutro de las secciones extremas
(`tests/vv_timoshenko.py`). Timoshenko-Goodier reparte la reacción como cortante en la
sección; una reacción puntual es una singularidad del continuo plano. Por eso la flecha
medida respecto del nodo de apoyo crece levemente al refinar (0,18 % con 28×4, 0,26 % con
56×8, 0,35 % con 112×16), mientras que respecto de la sección extrema completa es −0,03 %
en todas las mallas. El 0,26 % refleja sobre todo el apoyo puntual; la rigidez global
coincide con la teoría dentro del 0,03 % (corridas de esta auditoría; ver H2).

**D6. «¿Por qué una sola malla en Timoshenko?»**
Porque es un contraste puntual con dos referencias externas; la convergencia y la
comparación Q4-Q9 se estudian en el MMS y en Cook (p. 48). (Los datos de D4 y D5 muestran
que las tensiones convergen.)

**D7. «¿Por qué usó elementos Shell en SAP2000 y no el elemento Plane de tensión plana?»**
*Prepararla con tus razones.* La tesis dice que la respuesta en el plano del Shell es una
membrana isoparamétrica con giro de perforación (drilling), que no coincide con el continuo
de EduFEM, y por eso la columna se llama «diferencia» y no «error» (p. 82). Un modelo con
elementos Plane sería una comparación código a código más estricta.

**D8. «¿De dónde sale el 23,96 de Cook? ¿Qué es la extrapolación de Richardson?»**
Es el valor de uso extendido; Štembera y Füssl dan 23,965 con una malla de 192×128. Mi
Richardson con las tres mallas Q9 más finas da ≈ 23,97, con orden cercano a uno por las
singularidades del borde empotrado. La incertidumbre es del orden del 0,05 % (§3.5,
pp. 84-86).

**D9. «¿Que sus valores Q4 coincidan exactamente con los de Štembera no es sospechoso?»**
Coinciden en las cinco mallas hasta la última cifra publicada, y salen de
`tests/vv_cook.py`, que cualquiera puede correr. Muestra que EduFEM resuelve el caso como un
código independiente; no prueba que ambos sean correctos, porque un error de formulación
compartido se repetiría (p. 87).

**D10. (difícil) «¿Cómo detectó el error de la matriz de extrapolación? ¿Qué garantiza que
no haya otros?»**
En la memoria del ejemplo canónico, las tensiones nodales no cerraban con las de los
puntos de Gauss; los estudios de convergencia no lo veían porque el desplazamiento no usa
esa matriz (p. 97). Nada garantiza la ausencia de todo error: la V&V acota el riesgo, y
las rutas que no ejercita están declaradas. *Contarlo tal como ocurrió.*

**D11. «¿Por qué E = 1 y ν = 0,3, sin unidades, en el MMS y en Cook?»**
Porque verifican el código, no un material. Además, en elasticidad lineal escalar E deja
las tensiones iguales y divide los desplazamientos (p. 81).

**D12. «Que las reacciones equilibren la carga, ¿no es trivial?»**
Se sigue por construcción de R = Ku − F; no mide exactitud, pero delataría un error de
ensamblaje o un sistema mal resuelto, y así lo digo (p. 170).

**D13. «¿Por qué no validó con un caso civil en deformación plana, como una presa o un
túnel?»**
Es un límite declarado (p. 107) y la primera recomendación de la batería (p. 109).

### E. Software e implementación

**E1. «¿Por qué Python? ¿No es lento?»**
No exige licencia, reúne cálculo, interfaz y documentos en un lenguaje y se distribuye con
instalador (p. 4). El motor está vectorizado: 33 282 GDL en 0,72 s en un equipo de 2012
(Tabla 3.9).

**E2. «¿Cómo sé que lo que muestra un módulo es lo que calcula el motor?»**
El motor tiene dos versiones, una por lotes y una legible; una prueba de regresión exige
que coincidan de la rigidez a las tensiones con error relativo ≤ 10⁻⁹ (p. 64).

**E3. (difícil) «Si la memoria solo desarrolla un elemento en mallas grandes, ¿cada
resultado es trazable?»**
Sí, por dos vías: los módulos exponen el procedimiento sobre cualquier elemento que se
seleccione, y la memoria lo desarrolla completo en modelos pequeños y sobre el elemento de
mayor energía en los mayores, con el patrón de K (pp. 73-74 y 101).

**E4. «¿Puedo imponer un asentamiento de apoyo?»**
El motor sí admite desplazamientos prescritos no nulos (los usa el MMS), pero la interfaz
no los ofrece (p. 91). Es una extensión directa.

**E5. «¿Por qué no hay mallador automático?»**
Por alcance: la malla se construye por tabla, dibujo o DXF (p. 7). Queda recomendado
(p. 109).

**E6. «¿Qué licencia tiene? ¿Todo lo que trae es libre?»**
Código propio bajo MIT. Desde el 25-09 el paquete ya no lleva PyMuPDF (AGPL-3.0): la teoría
se abre con el visor del sistema, y los avisos de terceros van en `LICENCIAS-TERCEROS.txt`
(nota de la Tabla 2.5, p. 59). *Ojo: la respuesta PD-04 de `contexto_defensa.pdf` todavía
nombra PyMuPDF.*

**E7. «¿Por qué la paleta jet, si no es perceptualmente uniforme?»**
Por continuidad con el software profesional, sabiendo su defecto; lo compensan la escala
numérica y la sonda (p. 72).

**E8. «¿Por qué se puede "Resolver de todos modos" ante un error crítico?»**
Para que el estudiante vea la consecuencia. Si faltan elementos o restricciones, la
resolución se corta igual, con un mensaje (p. 119; ver H10 sobre la redacción de la p. 67).

**E9. «En el ejemplo canónico, el von Mises máximo está en el nodo de la carga puntual.
¿Tiene sentido físico?»**
Una carga puntual es una singularidad: ese valor depende de la malla. El ejemplo canónico
demuestra el procedimiento, no da un valor de diseño.

**E10. «¿Usó inteligencia artificial para programar o redactar?»**
*Decidirlo antes de la entrega final y responder con verdad.* El párrafo de declaración
está comentado en `00_preliminares.tex`. El argumento de fondo: todo lo que la tesis afirma
puede comprobarse de forma independiente reejecutando los guiones.

**E11. «¿Cómo obtiene la Carrera el software y quién lo mantiene?»**
Instalador para Windows sin licencias ni internet, manuales en los Anexos A y B y código
público en GitHub (p. 114); tres prácticas propuestas (p. 109).

**E12. «Dice que la interfaz está íntegramente en español, pero en el menú veo "benchmark" y
"shear-locking".»**
*Depende de si corriges H6 antes de la defensa.* Si no: «Son rótulos que quedaron de la
versión evaluada; la tesis declara algunos (p. 57) y el resto se corrige en la siguiente
revisión».

**E13. «Muéstrelo funcionando.»**
*Ensayar una demostración corta*: cargar el ejemplo canónico, abrir M3 sobre un elemento,
resolver con F5, sondear el nodo 7 con su círculo de Mohr y exportar la memoria. Mientras H8
no esté corregido, evitar editar un vértice en la tabla y pulsar Ctrl+Z.

### F. Forma

**F1. «¿Por qué cita en Vancouver si la presentación es APA?»**
Está declarado (p. 10): numeración por orden de mención con la página citada, y
presentación APA 7 con tres excepciones.

**F2. «¿Por qué los títulos de capítulo son tan largos?»**
Cada título es su objetivo específico completo: «los objetivos definen los capítulos», el
procedimiento del Ing. Miranda.

**F3. «El resumen pasa de 250 palabras y no hay abstract.»**
Tiene 310. Depende del Reglamento (H-1): si pide APA estricto o resumen en inglés, hay que
ajustarlo.

## 6. Cómo se verificó

- **Lectura.** Leí completas las fuentes de `capitulos_final3/`, del preámbulo a los anexos. El
  PDF lo revisé en miniaturas de sus 189 páginas y amplié la Figura 2.1, la CR.2, la Tabla
  CR.1 y el índice. El PDF del disco estaba desactualizado al empezar (188 páginas, de las
  06:16); otra sesión lo regeneró a las 08:54 y hoy coincide con las fuentes.
- **Compilación.** El `.log` no tiene errores ni referencias indefinidas. Tiene un *underfull*
  ya conocido y la sustitución de LM Mono negrita.
- **Cifras.** Recalculé a mano Timoshenko, Cook, las tasas del MMS, los GDL y la memoria de K.
  Un verificador independiente comparó cada cifra del Capítulo 3, las conclusiones y los
  anexos con los CSV de `docs/vyv/datos/`, rehízo las corridas en memoria y hizo el sabotaje
  del MMS.
- **Software.** Otro verificador contrastó cada afirmación sobre el software con el código:
  - los 22 chequeos, los 8 módulos, los menús y los atajos;
  - los formatos y el instalador;
  - las 36 pruebas, corridas en verde: regresión 81/81 y `test_fem` 14/14, entre otras;
  - el Anexo C, copia literal del código;
  - el Anexo G, regenerado idéntico byte a byte.
- **Citas.** El tercer verificador contrastó las citas y localizadores con el respaldo
  documental y con los PDF de `tesis/bibliografia/`.
- **Corridas propias** (en el *scratchpad*, sin escribir en el repositorio; `git status` quedó
  limpio): el refinamiento de Timoshenko (28×4 a 224×32), la flecha medida respecto de la
  sección extrema, el ejemplo del menú (14×4), el deshacer y el punto y coma con
  `\XeTeXgenerateactualtext`.
- **Historial.** Revisé en git cuándo entró cada umbral a los guiones.

**Qué no se verificó**:
- los tiempos absolutos de la Tabla 3.9, que dependen de la carga del equipo (salen del mismo
  orden, con la misma tendencia);
- el comportamiento visual de la interfaz y del instalador en pantalla;
- que el repositorio de GitHub sea público.
