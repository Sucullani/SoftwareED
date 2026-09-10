# Auditoría y saneamiento de la bibliografía de la tesis

**Fecha**: 2026-09-08 · **Autor**: Claude (agente) · **Estado**: terminado, con pendientes de autor

## Qué se pedía

El autor preguntó si convenía **reducir** la bibliografía a unas pocas referencias, y cuáles
podrían reemplazarse por otras ya presentes que cubren el mismo terreno (varios libros
generales de MEF se solapan). Se auditaron las 21 entradas por clúster temático con
verificación adversarial (3 refutadores por veredicto).

## Conclusión de la auditoría: NO reducir

Los números descartan la hipótesis de exceso:

- 21 entradas, 78 bloques `\autocite`, 146 instancias de clave.
- **Cero entradas huérfanas** y **cero citadas una sola vez** (el mínimo son 2).
- 18 de 21 aparecen en 3 o más capítulos.
- La bibliografía ocupa 3 páginas de 130 (~2 % del documento).

Recortar a ~13 entradas ahorra página y media y deja una lista visiblemente corta para una
tesis cuya afirmación central es **negativa** ("no existe una herramienta así en español"),
que se defiende con amplitud de revisión, no con concisión.

**Prueba dura del solapamiento**: de los siete libros generales de MEF, `cook2002concepts` es
el **único** con citas en solitario (3). Los otros seis (`bathe` 15, `hughes` 13,
`zienkiewicz` 9, `reddy` 3, `onate` 3, `strang` 2) aparecen **siempre** acompañados. Es decir:
quitar cualquiera de ellos no deja ninguna frase sin respaldo, solo baja el peso de autoridad.
Eso mide respaldo, no valor — por eso solo se retiró una.

## Qué se hizo

### Se retiró una sola referencia

`oberkampf2010verification` → sus 5 citas reasignadas a `roache1998verification`. Era la única
redundancia **total** del archivo: sus citas eran un subconjunto estricto de las de Roache,
nunca aparecía sola, nunca encabezaba, y lo que aporta de propio (cuantificación de
incertidumbre, métricas de validación) no se usa en ningún párrafo. Verdicto unánime de los
3 refutadores. Sitios tocados: `02_marco_teorico:381`, `02b:16`, `02b:74`, `04_resultados:5`,
`05_conclusiones:19`. Quedan **20 entradas**.

### Higiene del `.bib` (dos defectos eran visibles en el PDF)

- `csi2017sap2000` tenía `author` **y** `organization` con el mismo valor: el driver `@manual`
  imprimía la editorial dos veces. Se borró `organization`. Mayúsculas protegidas en el título.
- `perezsantiago2023fem`: `Perez` → `P{\'e}rez` (único apellido español sin escape).
- `journal` → `journaltitle` y `address` → `location` en todas las entradas (eran alias legacy
  de BibTeX; biber los aceptaba pero contradecían la convención del propio proyecto).
- `series` eliminado de `reddy` y `onate` (Vancouver no lo pide y ensuciaba la referencia).
- `onate2009structural`: el volumen salía del título → `subtitle` + `volume = {1}`.
- `bathe2014fem` y `strang2008analysis`: `note` explicando la autoedición y la reedición, para
  que no se lean como erratas (`hughes2000fem` ya tenía la suya).
- Partículas de apellido: `{van Kerkwijk}` y `{Fern{\'a}ndez del R{\'i}o}` entre llaves (biber
  las parseaba como prefijo + apellido, partiendo mal el nombre real del autor de NumPy).

### Citas mal dirigidas y afirmaciones sin respaldo (sin entradas nuevas)

- `01_introduccion:5` citaba a **Zienkiewicz y Cook para una afirmación curricular**; son
  tratados de MEF, no fuentes sobre planes de estudio. Se partió la oración: los dos libros
  respaldan "herramienta central del análisis estructural" y `perezsantiago2023fem` —que sí es
  un estudio sobre la enseñanza del MEF— respalda la parte curricular.
- **Extrapolación de Richardson** se nombraba dos veces sin cita (`02b:14` y la nota al pie de
  `04:150`): ancladas a `roache1998verification`, que es su fuente canónica y ya estaba.
- `02_marco_teorico:242`: "la regla de $m$ puntos integra exactamente polinomios de grado
  $2m-1$" era un teorema enunciado sin fuente. Se extendió la cita vecina.
- **Racimo decorativo de 5 claves** en `02_marco_teorico:4` reducido a 3, y `reddy` reubicado
  en `02:49` (principio de trabajos virtuales), donde hace trabajo real en vez de rellenar.

### Preámbulo y documentación

- Se quitaron dos opciones **inertes** de biblatex: `maxcitenames=2` (solo aplica a estilos con
  nombres en la cita; este es numérico) y `\DeclareNameAlias{sortname}` (solo aplica con orden
  alfabético; acá es `sorting=none`). El preámbulo prometía algo que no hacía.
- `tesis/README.md`: el estilo **no** es un estilo Vancouver cargado como tal, es
  `numeric-comp` + `sorting=none` + ajustes de nombres. Se declaró así, y se declaró la
  decisión de usar **títulos de revista completos** en vez de la abreviatura ISO del NLM.
- `.claude/skills/tesis-bibliografia/SKILL.md`: campos actualizados a los nombres de biblatex,
  regla nueva sobre `@manual` (author **o** organization, nunca los dos), y núcleo de
  referencias esperado sincronizado con el `.bib` real.

**Verificación**: `pdflatex` × 3 + `biber` → 20 citekeys, cero warnings de biblatex, cero
citas indefinidas, 130 páginas. Bibliografía revisada entrada por entrada en el PDF.

## Qué se descartó y por qué

- **Quitar `reddy2006introduction` y `onate2009structural`.** Son técnicamente los más
  sustituibles (3 citas cada uno, ningún tema propio, verdicto unánime SUSTITUIBLE), pero cada
  uno aporta un anclaje que se pierde: la pinza Bathe–Reddy en la introducción (el tratado
  avanzado *y* el texto explícitamente introductorio comparten el mismo grado de abstracción) y
  el vínculo con la escuela de la UPC, que es la de ED-Elas2D, el antecedente directo.
- **Quitar `zienkiewicz2013fem`, `bathe2014fem` o `strang2008analysis`.** Los 3 refutadores
  tumbaron el veredicto en los tres casos. Baja frecuencia ≠ baja carga probatoria: `strang`
  (2 citas) es la única fuente matemática del `.bib` y sostiene las tasas contra las que el
  Cap. 4 declara verificado el motor; `stimpson2007verdict` (2 citas) es sustitución numérica
  directa de umbrales.
- **Abreviar títulos de revista al ISO del NLM.** Habría que derivar 9 abreviaturas sin fuente
  que las confirme. Se declaró la decisión contraria en el README en vez de improvisarlas.

## Trampas encontradas

- El driver `@manual` de biblatex imprime `organization` en la posición de editorial. Si la
  entrada trae además `author` con el mismo valor, el nombre sale **dos veces** y no hay
  warning que lo avise. Solo se ve leyendo el PDF.
- `sorting=none` significa que el orden del `.bib` es irrelevante: la numeración sale del orden
  de aparición en el texto. Quitar una entrada renumera toda la lista sola.
- `biber` avisa "User/administrator updates are out-of-sync" en este MiKTeX; es ruido del
  entorno, no del documento — igual escribe el `.bbl`.

## Qué quedó pendiente

### 1. Localizadores de página — **no se hicieron: requieren los libros**

Cero de las 78 citas usan `\autocite[p.~NNN]{...}`. Es la mejora de mayor relación
beneficio/esfuerzo del documento (las 18 citas a Cook remiten hoy a un libro de ~700 páginas en
bloque), pero **no se puede completar sin los libros a mano**: inventar números de página está
prohibido por la propia skill del proyecto. Sitios donde más pesa (sustitución numérica, que es
lo que un tribunal pregunta):

| Cita | Sitio | Qué respalda |
|---|---|---|
| `cook2002concepts` | `01_introduccion:62` | tamaños $6\times6$, $6\times24$, $24\times24$ en 3D → justifica el alcance 2D |
| `cook2002concepts` | `02_marco_teorico:272` | reparto de cargas de arista $F_1=\tfrac{L}{6}(2q_s+q_e)$ |
| `cook2002concepts` | `02_marco_teorico:348` | pesos de extrapolación $a\approx1{,}866$, $c\approx0{,}134$ |
| `stimpson2007verdict` | `02_marco_teorico:362` | umbrales del Jacobiano escalado y del *stretch* |
| `timoshenko1970elasticity` | `02_marco_teorico:395`, `04:99` | campo tensional y flecha de la viga |
| `hughes2000fem` | `02_marco_teorico:257` | integración reducida selectiva y formulación $\bar{\bm B}$ |
| `strang2008analysis` + `hughes2000fem` | `02:393`, `04:16` | tasas $\mathcal{O}(h^{p+1})$ / $\mathcal{O}(h^{p})$ |

### 2. Vacíos bibliográficos — RESUELTOS en la segunda pasada (ver más abajo)

El problema real de esta bibliografía es de **cobertura**, no de exceso. Ordenados por
exposición ante el tribunal:

1. **El marco metodológico entero no tiene una sola cita.** `02b_diseno_metodologico.tex`
   tiene 2 `\autocite` en 90 líneas y ninguna de metodología. "Propositiva", "aplicada
   tecnológica", operacionalización de variables, matriz de consistencia: toda esa taxonomía
   es la que exige el reglamento y no es dominio de Zienkiewicz ni de Roache. Es el hueco más
   grande y el más barato de tapar (1–2 entradas).
2. **`E = 15000\sqrt{f'_c}` con `f'_c = 210` kgf/cm²** (`04_resultados:99`), presentado como
   "habitual en la práctica regional", sin norma. Es el único dato de ingeniería civil real de
   la tesis y fija el módulo de la viga de validación principal.
3. **El valor de referencia 23,96 de la membrana de Cook** se atribuye a "la literatura" en una
   nota al pie sin citarla, y gobierna toda la columna de error de `tab:cook`.
4. **CALFEM, FEniCS, VisualFEA, ANSYS y Abaqus** aparecen caracterizados en prosa y en dos filas
   de `tab:comparativa` **sin ninguna cita** — y esa tabla es la que produce la conclusión de
   "vacío" que justifica el trabajo.
5. **COLAMD, SuperLU, Cuthill-McKee, Cholesky** citados al *paper de SciPy*. Que Cholesky sea
   más rápido que LU es álgebra lineal numérica, no una propiedad de la biblioteca.
6. El fundamento pedagógico (minimalismo, foco único, carga cognitiva) se apoya solo en
   reportes de herramientas de MEF, no en teoría del aprendizaje.
7. La paleta *jet* se defiende con el manual de SAP2000 —que acredita el uso, no la
   conveniencia— sin reconocer la crítica conocida al arcoíris.
8. Métricas "de Robinson" y puntos "de Barlow" con apellido y sin obra; DXF documentado en
   anexo sin remitir a su especificación.

### 3. Dato menor corregido de paso

`ESTADO.md` decía "~102 páginas"; el `main.pdf` tenía **130** (tras la segunda pasada, 132).

---

# Segunda pasada (mismo día): cierre de los vacíos

El autor pidió resolverlos todos, con dos criterios propios: la fórmula del ACI no justifica
una entrada nueva, y las referencias puntuales de algoritmos tampoco. El principio que guió la
solución fue **cerrar cada hueco sin inflar la bibliografía**, por este orden: (a) redirigir a
una fuente ya presente, (b) reescribir la afirmación para que se sostenga sola, (c) sustituir
la apelación a una autoridad ausente por el argumento técnico que esa autoridad respaldaría,
(d) reconocer explícitamente un límite de la revisión, y solo (e) agregar entrada nueva.
Resultado: **23 entradas** (20 + 3), todas con dos citas o más.

## Las tres entradas nuevas: material docente de la carrera

`tesis/Material docente/` ya contenía la fuente que faltaba, y es la mejor posible: es el
material normativo de la propia carrera, en español, verificable y exactamente la rúbrica que
aplica el tribunal. Cierra de un golpe el hueco metodológico **y** la ausencia total de fuentes
en español o latinoamericanas.

| Clave | Documento | Sostiene |
|---|---|---|
| `barrios2021modelo` | Barrios JC, *Modelo de investigación*, CIV 400 Seminario de Grado II, 2021 | tipo y enfoque de la investigación, modelo de simulación numérica, población vs. selección intencional |
| `miranda2024objeto` | Miranda JS, *Metodología de la investigación: situación problemática, objeto de estudio y campo de acción* | situación problemática (01), objeto/campo (01) |
| `miranda2024problema` | Miranda JS, *Planteamiento del problema científico e hipótesis* | contradicción que origina el problema, hipótesis de diseño en vez de estadística |

**A verificar por el autor**: el año 2024 de los dos documentos de Miranda sale de la fecha de
creación del PDF, no de una portada (los de Barrios sí llevan «©2021» impreso). Y `Barrios,
Juan Carlos` omite la inicial del apellido materno que aparece en la diapositiva («Barrios C»).

**Ojo, aparte**: los ocho PDF de `tesis/Material docente/` están **trackeados en git** y el
repositorio es público. Es material de cátedra ajeno; conviene decidir si se `gitignore` +
`git rm --cached`, como se hizo con el PDF de ED-Elas2D. Ya están en el historial, así que
sacarlos de HEAD no los purga.

## Los demás huecos, resueltos sin entradas nuevas

- **`E = 15000√f'c`** — se nombra la norma ACI 318 en prosa (no hace falta entrada para una
  correlación de uso corriente) y, sobre todo, **se neutraliza la observación**: en elasticidad
  lineal con apoyos de desplazamiento nulo, escalar $E$ por $\alpha$ deja las tensiones
  intactas y divide los desplazamientos por $\alpha$; como las tres soluciones comparadas usan
  el mismo módulo, los errores relativos son invariantes ante ese valor. Se dice explícitamente
  que el hormigón realista es para que las magnitudes resulten familiares, no porque de él
  dependa el resultado. Se quitó «habitual en la práctica regional» (afirmación sobre práctica,
  sin fuente posible).
- **Cook 23,96** — el valor **no** procede del artículo de 1974 ni tiene un origen único
  citable (circula con variantes). En vez de elegir arbitrariamente un paper, la nota al pie se
  volvió **autosuficiente**: se explica que el caso no tiene solución cerrada y que su
  referencia es un límite de convergencia, y se corrobora con la extrapolación de Richardson de
  la propia secuencia Q9 del trabajo (→ 23,97), citando Roache, que ya estaba. Se eliminó la
  apelación a «la literatura cita valores entre 23,9 y 23,96».
- **Solucionadores** — no hacía falta retirar nada. Citar el *paper* de SciPy para «SciPy usa
  SuperLU con COLAMD» es **atribución correcta**: documenta lo que hace la biblioteca. La única
  afirmación mal atribuida era «Cholesky es más rápida que la LU general», que es álgebra
  lineal, no una propiedad de SciPy: se reemplazó por el argumento estructural (simetría +
  definición positiva ⟹ un solo triángulo y sin pivoteo ⟹ la mitad del trabajo), con reenvío a
  donde se establece que $\bm{K}_{ff}$ es definida positiva. Cuthill-McKee ya era resultado
  medido por el propio trabajo y no necesitaba fuente.
- **CALFEM / FEniCS / VisualFEA / ANSYS / Abaqus** — las afirmaciones pasaron de específicas
  del producto a **propiedades de la categoría** (una biblioteca no tiene interfaz gráfica por
  definición; un paquete comercial no expone las matrices intermedias), la fila comercial se
  ancló a `csi2017sap2000`, y se agregó el **criterio de armado** de `tab:comparativa` más una
  declaración de límite de la revisión: VisualFEA se consigna como no examinado de primera mano
  por ser cerrado y de pago. Reconocer el límite protege más que afirmar sin fuente.
- **Métricas «de Robinson»** — atribuirlas a Verdict habría sido un error de bulto y citar a
  Robinson exigía una obra que no se pudo verificar. Solución: **definirlas**. Se agregó
  `eq:descomposicion-bilineal` con los vectores $\bm{X}_1,\bm{X}_2,\bm{X}_3$ y las expresiones
  de $AR$ y $T_R$ tal como las implementa `fem/mesh_quality.py`, se acredita a Verdict la
  familia de métricas (cita ya presente) y se declara que los cuatro umbrales son convención de
  EduFEM. **De paso se corrigió una inconsistencia real**: el texto daba los umbrales del Q4
  (0,3 / 0,5) como si valieran también en Q9, donde la cuarta métrica es la desviación de nodos
  medios con cortes 0,10 / 0,25 (`fem/mesh_quality.py:400`).
- **Fundamento pedagógico** — se separó lo que la literatura sí sostiene (la interactividad,
  con Lee y Bishay) de lo que es decisión del autor (el minimalismo), y se dijo cuál es cuál.
  «Reduce la fricción cognitiva» y «la atención del alumno no se dispersa» —afirmaciones
  psicológicas sin fuente— se sustituyeron por propiedades verificables del diseño (el panel no
  puede mostrar un elemento distinto del resaltado; dos capas no compiten por el lienzo).
- **Paleta jet** — se conserva la decisión y se **reconoce la crítica** sin apelar a una
  literatura no citada: los mapas arcoíris no son perceptualmente uniformes y son hostiles al
  daltonismo; se privilegió la continuidad con la herramienta profesional y se explicita la
  mitigación (escala graduada + sonda puntual).
- **«Patrón estándar del software profesional»** (×2) — era autoridad sin autoridad. Se cambió
  por la razón técnica, que es más fuerte: la indirección cuesta una consulta a un diccionario
  y evita dimensionar $\bm{K}$ según el identificador máximo.
- **«Exactitud propia de un código establecido» / «en el rango del software comercial»** —
  comparaciones vagas contra un estándar nunca definido. Sustituidas por las cotas medidas:
  error < 0,3 % frente a la solución analítica y < 0,6 % frente a SAP2000 en las magnitudes
  primarias (verificado contra las cifras de `tab:timoshenko-stress` y `tab:timoshenko-defl`).
- **Anclajes menores añadidos a fuentes ya presentes** — Barlow/superconvergencia en el Cap. 4
  (Cook + Zienkiewicz), estimador por recuperación en el salto sin promediar (Zienkiewicz),
  $\bm{K}_{ff}$ definida positiva (Bathe), von Mises (Timoshenko + Cook), regla de $m$ puntos
  (Hughes + Zienkiewicz).
- **Pre-test/post-test** — las tres citas no eran fuentes de diseño cuasiexperimental. Ahora
  sostienen lo que sí pueden sostener («qué conceptos conviene poner a prueba») y se declara
  que la formulación del diseño excede el alcance del trabajo.
- **DXF y *shoelace*** — el anexo documenta la convención propia de EduFEM sobre un subconjunto
  del formato, leído con `ezdxf`, y no afirma nada sobre el formato en general: no necesita la
  especificación de Autodesk. Se agregó la expresión del área con signo para que la fórmula
  quede definida en el texto.

**Verificación**: `pdflatex` ×3 + `biber` → 23 citekeys, cero citas o referencias indefinidas,
132 páginas. Los 9 *overfull* que quedan son preexistentes (matrices anchas de
`07_anexo_memoria.tex`, la línea con `\texttt{ProjectModel}` del Cap. 3); los dos que introdujo
la ecuación nueva se corrigieron partiéndola en `aligned`.

---

# Tercera pasada (2026-09-09): las diapositivas salen, entran los libros

El autor observó que citar material docente era citar una fuente derivada, y que **Miranda es
miembro de su tribunal**. Verifiqué los tres decks completos: **ninguno tiene diapositiva de
bibliografía** (el único crédito en los tres es una nota al pie de Barrios a Kéry 2010, sobre
WinBUGS y ecología, ajena al tema). Es decir, eran material terciario sin fuentes. Se fue al
origen y **se retiraron `miranda2024objeto`, `miranda2024problema` y `barrios2021modelo`**.

## Las tres entradas que las reemplazan (siguen siendo 23)

Metadatos tomados de la portada y la página de créditos de cada ejemplar, no de la web:

| Clave | Referencia | Estado |
|---|---|---|
| `alvarez_metodologia` | Álvarez de Zayas C. *Metodología de la investigación científica*. | **Sin pie de imprenta**: la monografía (80 p.) no consigna editorial, ciudad ni año. Se cita así, con `note`. **Pendiente del autor**: si consigue una edición con pie de imprenta, completar |
| `sampieri2018metodologia` | Hernández-Sampieri R, Mendoza Torres CP. *Metodología de la investigación: las rutas cuantitativa, cualitativa y mixta*. Ciudad de México: McGraw-Hill Interamericana; 2018. ISBN 978-1-4562-6096-5 | completo |
| `garciacordoba2005tecnologica` | García-Córdoba F. *La investigación tecnológica: investigar, idear e innovar en ingenierías y ciencias sociales*. México, D.F.: Limusa; 2005. ISBN 968-18-6597-9 | completo |

**Mario Bunge, *La investigación científica* (Ariel, 2.ª ed., 1983) se dejó fuera** pese a estar
disponible: García-Córdoba cubre el mismo terreno (ciencia frente a tecnología, carácter
aplicado del trabajo) de forma más específica y dirigida a ingenierías, y una cuarta entrada de
metodología habría sido redundante con lo que la tesis realmente afirma.

## Localizadores de página: hechos (era el pendiente de la segunda pasada)

Ocho citas llevan ahora `\autocite[p.~NN]`. Las páginas se verificaron **abriendo cada libro**,
leyendo el número impreso en la página; no se calcularon por desplazamiento, porque el desfase
entre página del PDF y página impresa **no es constante** (en Sampieri va de −41 a −43; en
García-Córdoba, de −2 a −4).

| Fuente | p. | Qué sostiene | Dónde se cita |
|---|---|---|---|
| Álvarez de Zayas | 7 | definición de problema científico y de la contradicción que lo origina | `01:15` |
| Álvarez de Zayas | 9 | objeto de estudio | `01:17` |
| Álvarez de Zayas | 13 | campo de acción («concepto más estrecho que el de objeto, es una parte del mismo») | `01:17` |
| Álvarez de Zayas | 21 | modelo teórico como representación ideal del objeto | `02b:14` |
| García-Córdoba | 75 | cap. 3, la investigación tecnológica | `02b:4` |
| García-Córdoba | 83 | el problema tecnológico no se elige libremente: sale de un diagnóstico de la realidad | `01:11` |
| García-Córdoba | **85** | **la hipótesis tecnológica es la solución tentativa a un problema concreto, con lógica distinta a la científica y criterio de veracidad en la práctica** | `01:44` |
| Hernández-Sampieri | 7 | características del enfoque cuantitativo | `02b:4` |
| Hernández-Sampieri | 137 | definición operacional de una variable | `02b:21` |
| Hernández-Sampieri | 201 | muestra dirigida, no probabilística | `02b:74` |

La de **p. 85 es la más valiosa**: respalda literalmente que la tesis plantee una *hipótesis de
diseño* y no una hipótesis estadística, que es el punto que el tribunal puede cuestionar. Se
aprovechó para reforzar la redacción de `01:44` con ese argumento.

## Dos cambios técnicos que hicieron falta

- `\autocites` separaba las citas con coma, y con localizadores eso es ambiguo:
  `[6, p. 75, 23, p. 7]` se lee como cuatro números. Se redefinió `\multicitedelim` en
  `preambulo.tex` → `[6, p. 75; 23, p. 7]`.
- **`.gitignore`**: se agregó `tesis/bibliografia/*.pdf`. Los cuatro libros estaban sin ignorar
  en un repositorio público. Nunca llegaron a commitearse, así que basta la regla.
  **Pendiente**: `tesis/bibliografia/Elast2DOñante.pdf` (el paper de ED-Elas2D, Taylor & Francis,
  de pago) **sí está trackeado** y ya está en el historial; sacarlo de HEAD no lo purga. Lo mismo
  vale para los ocho PDF de `tesis/Material docente/`.

**Verificación**: `pdflatex` ×3 + `biber` → 23 citekeys, cero citas o referencias indefinidas,
132 páginas, los mismos 9 *overfull* preexistentes.

---

# Anexo: intento de descarga de tres fuentes (mismo día)

El autor pidió bajar los PDF de `roache1998verification`, `cook1974membrane` y
`perezsantiago2023fem`. **Ninguna de las tres tiene texto completo libre.** Comprobado con
Crossref, OpenAlex, Unpaywall y Semantic Scholar (los tres dan `is_oa: false`, `oa_status:
closed`, cero repositorios con full text), y con `curl` contra los PDF del editor: ASCE y Wiley
devuelven **403**. No se descargó nada: no hay copia legítima y las vías piratas quedan fuera.

| Referencia | Estado | Vía legítima |
|---|---|---|
| `roache1998verification` | Libro impreso, Hermosa Publishers, 464 pág., ISBN 978-0-913478-08-0. No está en Internet Archive (0 resultados) ni en ningún repositorio | Compra (Amazon / AbeBooks / Biblio, usado) o préstamo interbibliotecario vía [WorldCat](https://search.worldcat.org/oclc/40065186) |
| `cook1974membrane` | ASCE Library, de pago por artículo. Sin versión de autor en ningún lado; ni siquiera está indexado en Semantic Scholar | [doi.org/10.1061/JSDEAG.0003877](https://ascelibrary.org/doi/10.1061/JSDEAG.0003877), compra individual o biblioteca con suscripción ASCE |
| `perezsantiago2023fem` | Wiley, suscripción. Los autores tienen perfil en ResearchGate y Academia.edu: ahí se puede **solicitar el full text al autor** (Pérez-Santiago está en el Tec de Monterrey, [Research@Tec PID_24237](https://research.tec.mx/vivo-tec/display/PID_24237)) | Solicitud al autor por ResearchGate, o acceso institucional |

**Metadatos confirmados de paso** (Crossref): Cook 1974, *Journal of the Structural Division*
**100(9)**, 1851â€“1863 âœ“. Pérez-Santiago y Campos 2023, *CAEE* **31(5)**, 1159â€“1173 â€” el `.bib`
dice `number = {5}` y **está bien**; el número 2 que circula en algunas listas es incorrecto.

**Hallazgo lateral útil**: `cook2002concepts` (*Concepts and Applications of Finite Element
Analysis*) **sí está en Internet Archive en préstamo digital**
([conceptsapplicat0000cook](https://archive.org/details/conceptsapplicat0000cook) y
`conceptsapplicat0000cook_c2x7`). Es el libro que gobierna 18 de las 78 citas y los tres
localizadores de página más caros del pendiente 1 (tamaños 3D, reparto de cargas de arista,
pesos de extrapolación 1,866 / 0,134). Con una cuenta gratuita se puede leer y anotar los
números de página sin comprarlo.

---

# Cuarta pasada (2026-09-09): Vancouver puro + respaldo documental verificado

El autor aportó **los PDF de casi toda la bibliografía** en `tesis/bibliografia/` y pidió tres
cosas: decidir sobre los localizadores, renombrar los documentos y dejar un documento aparte
con fuente, página y contexto de cada cita, resaltando los pasajes en los propios PDF.

## Decisión: Vancouver puro en el cuerpo

Se retiraron los 9 localizadores de página del cuerpo (`\autocite[p.~NN]` â†’ `\autocite`), y
la multicita `\autocites` volvió a ser `\autocite{a,b}`. Se quitó del preámbulo la
redefinición de `\multicitedelim`, que quedaba sin uso. La tesis compila en 132 páginas, sin
citas indefinidas. **El localizador no se perdió: vive en el documento de respaldo.**

## Renombrado y limpieza

Los 22 PDF pasaron a `Autor AÑO - Título.pdf`, con el **año del ejemplar real**, no el que
declaraba el `.bib` (por eso el renombrado se hizo después de identificarlos, no antes).
Se eliminó un duplicado exacto de ED-Elas2D (verificado por MD5, no por nombre).

## Auditoría multiagente de las 22 fuentes

Workflow de 42 agentes (2 por documento: identificar contra el `.bib`, y localizar el pasaje
que respalda cada cita). Resultado: **147 respaldos localizados**, cada uno con su página
impresa leída del encabezado o pie de la propia página.

### Discrepancias de edición â€” 5 de gravedad alta

El `.bib` declara ediciones que **no son las que el autor tiene**:

| Clave | El `.bib` declara | El ejemplar es |
|---|---|---|
| `zienkiewicz2013fem` | 7.ª ed., 2013, ISBN 978-1-85617-633-0 | **6.ª ed., 2005**, ISBN 0 7506 6320 0 |
| `bathe2014fem` | *Finite Element Procedures*, 2.ª ed., 2014, ed. del autor | **Prentice Hall, 1996**, ISBN 0-13-301458-4 |
| `strang2008analysis` | 2.ª ed., 2008, Wellesley-Cambridge | **1.ª ed., 1973, Prentice-Hall**, ISBN 0-13-032946-0 |
| `timoshenko1970elasticity` | 3.ª ed., 1970 | **2.ª ed., 1951**, sin ISBN impreso |
| `hughes2000fem` | Dover, 2000 (reimpresión) | **Prentice-Hall, 1987**, ISBN 0-13-317025-X |

Menores: `csi2017sap2000` (media â€” «Berkeley, CA» no figura impreso en ninguna de las 569
páginas), `onate2009structural` (Barcelona/CIMNE-Springer, no Dordrecht; el DOI no figura
impreso), `cook2002concepts` («New York» no figura; la única ciudad impresa es Hoboken),
`reddy2006introduction` (el ejemplar es la *International Edition*, con otro ISBN).

**Esperan decisión del autor**: o se ajusta el `.bib` a los ejemplares consultados â€”lo
honesto: se cita lo que se leyóâ€” o se consiguen las ediciones declaradas. Con Vancouver puro
el riesgo baja (no hay páginas que contrastar), pero la referencia sigue describiendo un libro
distinto del que se usó.

### Contradicciones internas de la tesis (hallazgo no buscado)

La verificación destapó afirmaciones que la fuente citada **no sostiene**:

- **`tab:comparativa`, fila «Simuladores interactivos»**: la columna *Licencia* dice «Libre»,
  pero los simuladores de Lee están **embebidos en VisualFEA**, que el propio párrafo de
  `02_marco_teorico.tex:11` califica de «cerrados y de pago». La tabla se contradice con su
  propio texto introductorio, cuatro renglones antes.
- **Misma fila, columna 2D**: el artículo documenta sólidos 3D de 20 nodos, placas y láminas
  degeneradas. La celda debería decir «2D y 3D».
- **«visualización de los modos propios de vibración»** (`02_marco_teorico.tex:11` y
  `04_resultados.tex:223`): el artículo trata autovalores de la **matriz de rigidez** (modos de
  cuerpo rígido, hourglass, shear locking); los modos de vibración aparecen solo como
  extensión. Conviene decir «modos propios de la matriz de rigidez».
- Otras afirmaciones marcadas sin respaldo localizable en su fuente: el mínimo
  `q_SJ >= 0,50` atribuido a Verdict, la paleta *jet* atribuida al manual de SAP2000, el
  ordenamiento de mínimo grado atribuido al artículo de SciPy, «la integral carece de primitiva
  elemental» atribuida a Hughes, y la identificación Q4 â†” puntos de Barlow en la regla 2×2
  atribuida a Zienkiewicz.

## Entregables

- **`tesis/respaldo_citas/respaldo_citas.tex` y `.pdf`** (44 páginas): estado de las 21
  fuentes, discrepancias de edición, afirmaciones sin respaldo y catálogo de los 147 respaldos
  con página impresa y pasaje textual en bloque amarillo. **Acompaña a la tesis, no forma parte
  de ella.** Se versiona.
- **`tesis/bibliografia/resaltados/`**: copia de cada PDF con los pasajes marcados â€”53
  resaltados en amarillo sobre el texto y 85 notas amarillas ancladas en las páginas
  escaneadas, donde no hay capa de texto que buscar; 138 de 142 pasajes quedaron marcados.
  Los originales no se tocan. **Gitignorado** (copyright).

## Trampas encontradas

- El desfase entre página del PDF y página impresa **no es constante dentro de un mismo
  ejemplar** (Sampieri va de âˆ’41 a âˆ’43; García-Córdoba de âˆ’2 a âˆ’4). Un localizador se verifica
  abriendo la página, nunca calculándolo.
- `babel-spanish` vuelve activa la comilla recta: un `"` del OCR se come la letra siguiente
  (`Inc.z` en vez de `Inc.,`). Hay que escaparla como `\textquotedbl{}`.
- `soul` (`\hl`) no tolera pasajes largos ni matemáticas; para resaltar bloques va `tcolorbox`.
- Las griegas sueltas del OCR (Ïƒ, Ï„) rompen la compilación igual que en la regla dura 20: el
  generador las manda a modo matemático.
- `fitz.search_for` no cruza saltos de línea: hay que partir el pasaje en frases cortas y
  probar en dos pasadas.

## Faltan dos fuentes

`roache1998verification` y `cook1974membrane` no están en la carpeta. Son las que sostienen
toda la V&V y el benchmark de la membrana: no se pudieron verificar ni resaltar.

---

# Quinta pasada (2026-09-09): las 3 fuentes ausentes, resueltas

El autor no dispone de tres fuentes citadas y los libros son caros. Se resolvieron con lo que
sí tiene o con acceso abierto. Workflow de 6 agentes (5 investigando en paralelo + 1
consolidador). El `.bib` pasa de 23 a **25 entradas**.

## Las tres sustituciones

| Baja | Alta | Razón |
|---|---|---|
| `roache1998verification` (7 citas) | **`oberkampf2010vv`** | El autor **sí tiene** Oberkampf y Roy 2010, que se había dado de baja el 2026-09-08 por redundante con Roache. Cubre las 8 citas; en 6 la prosa queda respaldada tal cual. |
| `perezsantiago2023fem` (9 citas) | **`linero2012pefica`** (español, acceso abierto) + `wulandana2024balancing`, `wheatley2020ethical`, `le2019teaching` (ASEE, texto completo gratuito) | Wiley, de pago. Las 9 citas sostenían tres afirmaciones distintas; ninguna fuente sola las cubre. |
| `cook1974membrane` (3 citas) | atribución en prosa + `cook2002concepts` | **Cook 2002 NO contiene la membrana de Cook** (verificado página por página sobre el escaneo). Sirve para el fenómeno, no para la atribución. Se reescribió para que la atribución viva en la prosa («debe su nombre a R. D. Cook») sin citar un artículo que no se consultó. |

## Correcciones de fondo que trajo la revisión

- **Terminología «validación».** Para Oberkampf y Roy la validación exige mediciones
  experimentales; esta tesis contrasta contra una solución analítica y contra SAP2000, que es
  comparación código a código — y el propio libro advierte que eso *no sustituye* a la
  verificación rigurosa del código. Se acotó el alcance en el marco teórico y en las
  conclusiones. **No** se barrieron los usos laxos del resto del Cap. 4: sería una campaña
  terminológica mayor y tocaría labels con referencias cruzadas. Queda a criterio del autor.
- **El umbral `q_SJ >= 0,50` no es de Verdict.** Verdict fija **0,30** para el cuadrilátero;
  0,50 es el del triángulo y el hexaedro. Se reescribió declarando que EduFEM eleva el corte
  por prudencia pedagógica. Era un dato numérico mal atribuido.
- **El «0,05 %» de la nota al pie de Cook no sale de ningún cálculo declarado**:
  `tests/vv_cook.py` no computa GCI (verificado). Se suavizó a lo que la evidencia propia
  sostiene. Si el autor quiere el número, hay que calcular el GCI y declarar el procedimiento.
- **Contradicción de `tab:comparativa`, resuelta**: los simuladores de Lee pasan de licencia
  «Libre» a **«Comercial»** y de «2D» a **«2D/3D»** — están embebidos en VisualFEA, que el
  propio párrafo llama «cerrados y de pago», y el artículo documenta sólidos de 20 nodos.
- **«modos propios de vibración» → «modos propios de la matriz de rigidez»** en los dos
  lugares donde aparecía.
- **La paleta jet** ya no se atribuye al manual de SAP2000, que no habla de paletas de color.
- **El ordenamiento de mínimo grado** ya no se atribuye al artículo de SciPy: se declara como
  elección de EduFEM (`MMD_AT_PLUS_A`) sobre la interfaz que SciPy expone de SuperLU.
- **«la integral carece de primitiva elemental»** ya no se atribuye a Hughes, que no lo dice.

Total: **30 ediciones de prosa**, cada una con verificación de que el texto viejo aparecía
exactamente una vez en su archivo. Y las **9 entradas del `.bib` corregidas al ejemplar real**
(Zienkiewicz 6.ª/2005, Bathe 1996, Strang 1973, Timoshenko 1951, Hughes 1987, más los campos
menores de `csi`, `onate`, `cook` y `reddy`).

**Verificación**: 25 citekeys, cero citas indefinidas, 132 páginas, 8 *overfull* (uno menos que
antes). `respaldo_citas` regenerado a 46 páginas, con las 9 entradas ya marcadas COINCIDE.

## Pendiente crítico del autor

**Las 4 fuentes nuevas de enseñanza no están descargadas ni leídas.** Sus metadatos vienen de
CrossRef y del sitio del editor, no de un ejemplar en mano; en el documento de respaldo figuran
como `NO_VERIFICABLE`. Si no se descargan y se leen, se reproduce exactamente el problema que
esta campaña intenta cerrar. Enlaces (`peer.asee.org` devuelve 403 a clientes automatizados:
hay que bajarlos desde un navegador):

- Linero y Garzón 2012 — https://educacioneningenieria.org/index.php/edi/article/view/242
- Wulandana 2024 — doi 10.18260/1-2--49428
- Wheatley 2020 — doi 10.18260/1-2--34161
- Le, Roberts y Duva 2019 — doi 10.18260/1-2--33348

Si al abrirlos alguno no sostiene lo que se le atribuye, hay que repuntear esa cita.

## Trampa encontrada

Un `cat >> nota.md <<'EOF'` desde Git Bash en esta máquina escribe el heredoc en **cp1252**, no
en UTF-8, y corrompe el archivo a medias. Para anexar a un `.md` con acentos, usar Python con
`encoding='utf-8'` explícito. La sección de la cuarta pasada se reparó al detectarlo.

---

# Sexta pasada (2026-09-09): Pérez-Santiago vuelve, las cuatro sustituciones se van

El autor pidió **una sola fuente** en lugar de las cuatro que habían reemplazado a
Pérez-Santiago —con razón: inflaban la bibliografía— y, mientras se buscaba ese sustituto
único, **consiguió el artículo original**. Eso vuelve innecesaria toda la sustitución.

## Qué se hizo

- **Alta de `perezsantiago2023fem`**, con los datos leídos del propio PDF: la cita del editor
  impresa en el artículo es `Comput Appl Eng Educ. 2023;31:1159-1173`, DOI `10.1002/cae.22627`.
  **El número de fascículo no figura en el ejemplar**, así que la entrada no lo declara (el
  `.bib` viejo traía `number = {5}`, que venía del catálogo, no de la fuente).
- **Bajas de `linero2012pefica`, `wulandana2024balancing`, `wheatley2020ethical` y
  `le2019teaching`.** No llegaron a defenderse nunca: el autor no las había leído.
- **8 citas repunteadas** de vuelta a la clave única.
- El PDF quedó como
  `tesis/bibliografia/Perez-Santiago y Campos 2023 - FEM Education in Undergraduate Studies.pdf`.

El `.bib` queda en **22 entradas** (25 − 4 + 1), y la tesis en **131 páginas**, sin citas
indefinidas.

## Verificación del respaldo, ahora sí contra el ejemplar

Con el PDF en mano se comprobaron las tres afirmaciones. Desfase: **página impresa = página del
PDF + 1158**.

| Afirmación | p. | Pasaje |
|---|---|---|
| El MEF es parte del currículo | 1160 | «this work may also support other undergraduate degree programs where FEM/FEA is part of the curriculum» |
| El software comercial como caja negra | 1160 | «Other authors are concerned about learners using commercial software like a "black box"» |
| Se privilegia lo práctico sobre lo conceptual | 1159 (resumen) | «specialists agree on the importance of including a mixture of theoretical and applied topics in the syllabus **but prefer practical skills over fundamental concepts**» |
| Unir fundamento y operación es el objetivo formativo | 1168 | «This would allow the student to connect the theoretical fundamentals with the operation of FEA codes» |

**Dos precisiones que la lectura del artículo obligó a hacer en la prosa:**

1. La afirmación de la «caja negra» el artículo la **reporta de otros autores** (su ref. 28), no
   la enuncia como hallazgo propio. Es un uso legítimo como estado de la cuestión, pero la
   tesis no debe presentarlo como resultado del estudio.
2. La tesis decía que la carencia conceptual «dificulta diagnosticar resultados anómalos o
   evaluar la calidad de una malla». **Esa formulación no está en el artículo.** Lo que sí
   dice, y es más fuerte, es que los expertos consultados prefieren las destrezas prácticas
   sobre los conceptos fundamentales y que el egresado debe saber **planificar, verificar y
   validar** su análisis. La prosa de `02_marco_teorico.tex:9` y `04_resultados.tex` se
   reescribió a eso. De paso, «Estudios con perspectiva industrial» pasó a «Un estudio que
   recoge la opinión de expertos de la industria y de la academia»: es un solo estudio, no
   varios, y decirlo en plural exageraba la base.

## Lección para la próxima

Antes de salir a buscar sustitutos de una fuente cara, conviene preguntar al autor si puede
conseguirla: la sustitución costó dos pasadas y terminó revertida. La regla de la skill —agotar
(a) redirigir, (b) reescribir, (c) argumento propio, (d) declarar el límite, antes de (e) entrada
nueva— debería incluir un paso previo: **(0) preguntar si el autor puede conseguir el ejemplar.**


---

# Septima pasada (2026-09-09): las fuentes que se habian quedado sin resaltar

El autor detecto que Alvarez y Oberkampf no tenian copia marcada. No era que
faltaran los pasajes —los dos estaban documentados en el respaldo— sino que el
script de resaltado **los saltaba en silencio**. Al abrirlo aparecieron cuatro
defectos encadenados, y los cuatro afectaban a todo el corpus, no solo a esas dos.

## Los cuatro defectos

1. **Alvarez nunca se abrio.** La ficha proponia el nombre `Alvarez de Zayas sf - ...`
   y el archivo en disco se llama `Alvarez de Zayas (sin fecha) - ...`. El script hacia
   `if not os.path.exists(...): continue`, sin decir nada.
2. **Oberkampf no tenia pagina de PDF.** Los ocho respaldos traian la pagina *impresa*
   en prosa ("13 (Seccion 1.2.3.3); 14 (aforismo de Blottner); ...") y el campo
   `pagina_pdf` vacio, asi que ningun respaldo llegaba a marcarse y el archivo ni
   siquiera se guardaba.
3. **Solo se usaba la primera pagina de cada respaldo.** El campo suele traer rangos y
   listas (`'161-163, 179'`, `'477, 480, 481, 483'`) y el lector tomaba el primer
   numero con `re.search(r'\d+')`. Todo pasaje repartido en varias paginas quedaba
   marcado a un tercio.
4. **La busqueda era literal.** `search_for` no encuentra `definitions` cuando el PDF
   trae la ligadura `deﬁnitions`, ni atraviesa los guiones de corte de linea.

## Que se hizo

- `tesis/respaldo_citas/resaltar.py` **pasa a estar versionado** (antes vivia en un
  temporal de sesion) y ahora **informa al final todo lo que no pudo marcar**. Ese
  silencio era la causa de que el problema durara seis pasadas.
- `tesis/respaldo_citas/paginas.py`, nuevo: construye el mapa pagina impresa <-> pagina
  del PDF **leyendo el folio de cada pagina**, no calculando un desfase. En Oberkampf
  el desfase es +16 hasta la impresa 370 y **+24 desde la 371**; suponerlo constante
  mandaba la marca de la p. 749 a la 741. Cada pagina aporta varios numeros candidatos
  (folio, numero de capitulo) y se elige el que concuerda con sus vecinas.
- Coincidencia por **secuencia de palabras normalizadas** cuando la busqueda literal
  falla: atraviesa ligaduras, guiones de corte y saltos de columna.
- `gen_respaldo.py` tambien lee ahora el `verificado.json` versionado. Los tres scripts
  del directorio quedan reproducibles sin el scratchpad.
- Escritura tolerante: se guarda aparte y se reemplaza, para no perder el trabajo de una
  fuente entera cuando el PDF esta abierto en un visor.

## Resultado

De **20 a 22 PDF marcados**, y de 68 a **98 resaltados** (las notas amarillas bajan de
87 a 57). Alvarez queda con 5 resaltados sobre 5 pasajes; Oberkampf con 7 de 8.

Las 57 notas restantes **no son fallos**: 44 caen en los cinco libros que son escaneo
puro sin capa de texto (Bathe, Cook, Garcia-Cordoba, Hughes, Reddy) y 6 en las paginas
3-12 de Suarez, que es un PDF hibrido —sus paginas 1, 2 y 13 tienen texto y el resto son
imagen—. En una pagina sin texto no hay nada que resaltar: la nota amarilla en la esquina
es lo unico posible.

## Verificacion, que era el encargo real

Los 8 pasajes de Oberkampf y los 5 de Alvarez se comprobaron **contra el ejemplar**, no
contra la ficha. En Oberkampf, 51 de 53 paginas quedaron confirmadas por el folio impreso
en el encabezado; las dos restantes se leyeron a mano (la p. 208 es apertura de capitulo y
lleva el folio al pie; la p. 749 estaba mal mapeada y se corrigio). En Alvarez las cinco
paginas —7, 8, 13, 21 y 22— contienen literalmente el pasaje declarado.

Un hallazgo de paso: en Zienkiewicz el pasaje de la p. impresa 147 estaba anotado en la
pagina 161 del PDF cuando esta en la 163. La pagina impresa del respaldo era correcta; el
numero de PDF estaba corrido en dos, asi que la marca caia en la pagina equivocada.

## Leccion

Un script que salta lo que no entiende no tiene errores: tiene huecos invisibles. El
resumen final que enumera lo no marcado vale mas que cualquiera de los cuatro arreglos.

---

# Octava pasada (2026-09-10): auditoría con 60 agentes, dos bugs corregidos, cero bajas

El autor pidió volver a cotejar las 22 entradas contra los ejemplares y evaluar si la
bibliografía podía reducirse. Se orquestó un workflow de cuatro fases: cotejo por entrada,
análisis de solape, refutación adversarial de cada baja propuesta (tres lentes: sustituto,
pérdida, tribunal) y síntesis. Informe completo en
[2026-09-09_diagnostico-bibliografia.md](2026-09-09_diagnostico-bibliografia.md).

## Resultado del cotejo

**20 COINCIDE, 1 DISCREPA, 1 NO_VERIFICABLE.** Ninguna entrada está mal identificada. Dos
errores de hecho, ambos corregidos:

1. **`perezsantiago2023fem` no declaraba el fascículo, y el comentario decía que no figuraba
   en el ejemplar. Era falso.** La cita del editor impresa no lo trae, pero la marca de agua
   de descarga de Wiley, en 14 de las 15 páginas, dice `10990542, 2023, 5`. Se agregó
   `number = {5}`. Este error lo había introducido yo en la sexta pasada, mirando solo la
   cita impresa.
2. **`02_marco_teorico.tex:406` atribuía a Salari y Knupp la cláusula sobre integrar las
   normas de error con un punto de Gauss más por dirección.** El informe SAND2000-1444 no
   contiene «Gauss» ni «quadrature» ni una vez. El respaldo real es Oberkampf y Roy p. 320:
   «the numerical approximations used in its evaluation must be of at least the same order of
   accuracy as the underlying discretization scheme» y «the errors due to the numerical
   quadrature can interact with the numerical errors in the discrete solution and adversely
   impact the observed order of accuracy». Se cambió la cita y se explicitó el motivo técnico,
   que antes quedaba implícito.

`salari2000mms` queda con 4 citas y `oberkampf2010vv` con 11. Total: 160 citas, 131 páginas,
cero citas indefinidas.

## Reducción: se propusieron 5 bajas, sobrevivieron 2, no se ejecutó ninguna

`salari2000mms` (ninguna lente la refutó) y `reddy2006introduction` (una). Se descartaron
`strang2008analysis`, `onate2009structural` y `bathe2014fem`, refutadas 2 de 3 cada una.

Lo interesante es por qué cayeron Strang y Oñate: sus citas sí son redirigibles, pero
quitarlas dejaría una tesis de MEF sin análisis numérico puro y sin encuadre de ingeniería
civil. Se refutaron por perfil de bibliografía, no por cobertura. Ese es el argumento si el
tribunal pregunta por qué están.

**Decisión del autor: no dar de baja nada, «quizá en un futuro».** No reabrir sin que lo pida.

## Un descarte que conviene registrar

Se evaluó `02_marco_teorico.tex:298`, donde von Mises co-cita a Timoshenko y a Cook. En
Timoshenko «Mises» aparece una sola vez y en una nota bibliográfica al pie, así que parecía
un segundo error. **No lo es**: la oración es compuesta —tensiones principales y von Mises— y
Timoshenko cubre las principales (Arts. 9 y 68). Además, la búsqueda de texto sobre el PDF de
Cook devuelve cero para cualquier término, porque son 733 páginas de escaneo sin capa de
texto: eso no prueba ausencia.

## Dos defectos de mi propio andamiaje

- El agente de síntesis escribió que la frase de Gauss «queda respaldada por el co-citado», y
  esa línea citaba a Salari **sola**. Corregido en el informe.
- La primera versión del informe declaró cuatro entradas «sin ficha en el lote» y dedujo un
  dato «por diferencia». Fue culpa mía: pasé el JSON de la síntesis con `.slice(0, 90000)` y
  se cortó. Se rehízo la síntesis con los datos completos y un control explícito de que la
  tabla debe tener 22 filas. **Truncar la entrada de un agente sin que el agente lo sepa
  produce alucinaciones con forma de dato faltante.**

La corrida también se cortó a mitad por límite de sesión (26 de 54 agentes). El
`resumeFromRunId` replayó los completos desde caché y solo rehizo los 28 que faltaban.
