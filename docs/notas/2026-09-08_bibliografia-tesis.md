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
