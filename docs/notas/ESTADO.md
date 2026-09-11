# Estado del trabajo

**Última actualización**: 2026-09-09

> Lo primero que lee un agente al entrar. Qué está en curso, qué quedó a medias y qué
> decisión espera al autor. Se edita; lo que deja de aplicar se borra.
> Convención: [README.md](README.md).

## Contexto del proyecto

EduFEM está **funcional y empaquetado**: la GUI corre, el motor pasa su batería de tests,
hay `.exe` (`dist/EduFEM/`, onedir) e instalador (`installer/EduFEM.iss` → `EduFEM-Setup.exe`).
El trabajo activo no es construir features nuevas, sino **pulir** el software y **cerrar la
tesis** (`tesis/`, 130 páginas, compila limpio).

## En curso

| Tema | Dónde | Estado |
|---|---|---|
| Cierre de la tesis | `tesis/` | Compila limpio. Abiertas las 5 observaciones bloqueantes de la revisión del 2026-06-10 — ver [ESTADO_AUDITORIAS.md](../auditorias/ESTADO_AUDITORIAS.md) §*Abierto — revisión de la tesis*. Varias son **decisiones de autor**, no fixes mecánicos |
| Deuda técnica de la auditoría 2026-06-10 | repo | **Cerrada el 2026-09-06** (Top-10 + medios y bajos de §1, §2, §5 y §6). Único pendiente: decidir si se cablea `TheoryDoc.margin_formula()` en la memoria — cambia el layout del PDF, así que necesita validación visual del autor |
| Mejora continua del software | `docs/rutina/` | **Activa desde el 2026-09-08**: rutina horaria de claude.ai que trabaja directo sobre `main`, una área por sesión con rotación de 14. Qué hizo cada sesión: [../rutina/BITACORA.md](../rutina/BITACORA.md); qué falta y qué espera al autor: [../rutina/BACKLOG.md](../rutina/BACKLOG.md) |
| Distribución del `.exe` | `installer/` | Vía principal decidida: instalador Inno Setup por usuario, sin admin. Sin firma de código (decisión tomada). Empaquetado **onedir** desde el 2026-09-10 (arranque 3 s en vez de 12; el entregable sigue siendo un solo archivo) |

## Decisiones abiertas (esperan al autor)

- **Tabla 1.1 (`tab:comparativa`) reescrita como matriz de atributos (2026-09-10)**: los
  recursos pasaron a columnas y los atributos a filas, y se agregaron cuatro diferenciadores
  —memoria de cálculo automática, fenómenos numéricos observables, V&V publicada con la
  herramienta y requisitos de ejecución—. Las celdas de los otros recursos salen de
  `tesis/respaldo_citas/` y de los PDF de `tesis/bibliografia/`: donde la fuente no
  documenta el atributo dice **«No consta»**, y las categorías de propósito general llevan
  raya en V&V (criterio de armado del propio texto). De paso se aplicaron dos correcciones
  que el respaldo de citas tenía pendientes para Bishay: «1D/2D» → «2D/3D (barras)» y
  licencia «Libre» → «No declarada (código MATLAB)». Compila limpio, sin overfull. Está
  **sin commit**. El autor decide si conserva «No consta» como valor de celda (es honesto
  pero visible) y si actualiza la copia de esta tabla en `tesis/presentacion/guion.json`,
  que sigue con las columnas viejas.
- **Probar el instalador nuevo en un equipo limpio (2026-09-10)**: el entregable pasó a ser
  un instalador terminado (versión en el `.exe`, licencia, imágenes propias del asistente,
  asociación de `.edufem` con icono propio, detección de la app abierta, App Paths,
  desinstalación limpia). Está **sin commit**. Qué comprobar, idealmente en una PC **sin
  MiKTeX** y con un usuario de Windows con **tilde o espacio** en el nombre —el asistente debe
  proponer `C:\ProgramData\EduFEM`—: los accesos directos, que el icono anclado a la barra de
  tareas siga siendo el del acceso directo, el doble clic sobre un `.edufem`, la Memoria de
  Cálculo en PDF y la desinstalación. Falta decidir si **sube `APP_VERSION`** más allá de
  1.0.0 antes de la defensa. Detalle:
  [2026-09-10_instalador-profesional.md](2026-09-10_instalador-profesional.md).
  **Al commitear**: `installer/assets/*.bmp` y `resources/icons/edufem_doc.ico` están sin
  versionar y el `.iss` los necesita — `git add -u` no los toma y el repositorio quedaría sin
  poder compilar el instalador.
- **Auditoría de distribución (2026-09-10)**, encima de lo anterior y también **sin commit**:
  el empaquetado pasó a **onedir**, con lo que el programa instalado abre en **3 s** en vez de
  los 11-15 s que tardaba *siempre* el autoextraíble, ya no deja 189 MB en `%TEMP%` por cada
  cierre anormal y el `EduFEM-Setup.exe` bajó de 126,4 a **95,5 MB**. Aparte, los seis
  `filedialog` no declaraban `initialdir`: el primer «Guardar Como» del alumno dejaba su modelo
  **dentro de la carpeta del programa**, en `AppData`; ahora abren en `Documentos\EduFEM` y
  recuerdan la última usada. Se verificó sobre el paquete instalado (arranque, doble clic sobre
  un `.edufem`, registro, accesos directos, Memoria PDF con el TeX instalado). Qué mirar:
  que «Guardar Como» proponga `Documentos\EduFEM` y el nombre del proyecto. Detalle y lo que
  quedó abierto: [2026-09-10_un-solo-archivo-que-funcione.md](2026-09-10_un-solo-archivo-que-funcione.md).
- **Presentación de la tesis en APA 7 (2026-09-10)**: la tesis pasó a formato APA en su
  presentación (márgenes 2,54 cm, doble espacio, sangría 1,27 cm, texto sin justificar,
  paginación arriba a la derecha, títulos y rótulos APA) y **sigue citando en Vancouver**.
  131 hojas → 143. Está commiteado y en `origin/main`. Quedan dos cosas que decide el autor:
  (a) si el interlineado se queda en **doble** (norma, 143 hojas) o baja a **1,5** (120
  hojas; es una línea en `preambulo.tex`); (b) si los ~90 títulos pasan a **Title Case**,
  que es lo que pide APA pero contradice la ortografía del español. Qué se aplicó, qué no y
  por qué: [2026-09-10_apa-presentacion.md](2026-09-10_apa-presentacion.md).
- **Validación visual del dimensionado de ventanas (2026-09-10)**: se arregló el reporte
  *"la app se descuadra en otros equipos, los botones no se ven o quedan cortados"*. La
  causa no era la que parecía: la app corre **con** conciencia de DPI (`ttk.Window(hdpi=True)`
  llama a `SetProcessDPIAware`), así que con el escalado de Windows al 125-150 % las fuentes
  —y con ellas los widgets— crecen 1,25-1,5× dentro de ventanas cuyo tamaño estaba escrito
  en píxeles fijos, y Tk recorta lo último empaquetado: la barra de botones. `AboutDialog` y
  `MaterialDialog` ya se recortaban **al 100 %**. Ahora todo Toplevel pasa por
  [gui/scaling.py](../../gui/scaling.py) (regla dura 23) y las barras de botones se
  empaquetan primero. Está **sin commit**. Qué mirar: *Modelo → Tipo de Elemento* y *Tipo de
  Análisis* (el video ahora es la pieza elástica) y *Modelo → Materiales* (abre ~740 px de
  ancho, el que su contenido siempre pidió). Para reproducir otro equipo:
  `set EDUFEM_AREA_UTIL=1280x680 && python main.py`. Detalle en
  [2026-09-10_ventanas-contra-la-pantalla-real.md](2026-09-10_ventanas-contra-la-pantalla-real.md).
- **Validación visual del rediseño de la capa visual y de la pasada sobre los módulos
  (2026-09-09)**: cuadrícula anclada al mundo, franja lectora, lente de Proceso (índices de
  GDL, numeración local + ejes ξη + PG del elemento seleccionado), tira del método en el
  banner de Proceso, reacciones en el Post; y en los módulos: esqueleto de K + cabecera del
  sistema en **M7** (donde el autor pidió que viviera la lectura del sistema, que había nacido
  como panel propio de Proceso), ejes ξη con los mismos colores en el cuadrado natural y sobre
  el elemento en M1/M2/M3/M5, unidades y `fmt` en M6, descripciones del panel de módulos sin
  recortes. Está **sin commit**; el guion de qué abrir y qué mirar está en
  [../rutina/BACKLOG.md](../rutina/BACKLOG.md) (*Pendientes visuales*, primer ítem) y el
  razonamiento y las alternativas descartadas en
  [2026-09-09_rediseno-capa-visual.md](2026-09-09_rediseno-capa-visual.md). Dos decisiones
  chicas van adentro: si los visitados de la tira se limpian con *Nuevo Proyecto* (hoy no) y
  si la capa de GDL debe quedar prendida también en Pre por default (hoy solo Proceso).
- **Validación visual de la Memoria de Cálculo rediseñada (2026-09-09)**: sin índice impreso
  ni hojas apaisadas, portada de una hoja (ficha a dos columnas + diagrama del modelo + mapa
  del cálculo), contornos en grilla 2×2, matrices anchas en bloques de columnas y tablas
  topeadas con muestreo. Medido sobre PDFs reales: llenado 95–97 %, 0 hojas flojas, 0 overfull,
  0 apaisadas; Cook Q9 32×32 pasó de **493 hojas a 24**. Aparecieron y se corrigieron ocho
  bugs de producto, seis de ellos **preexistentes**: la Memoria **no compilaba** para mallas
  de 11–12 nodos; la tabla de recuperación imprimía **ε = 0 junto a σ ≠ 0**; la verificación
  de equilibrio ignoraba las cargas superficiales y declaraba **roto con residuo del 100 %**
  el ejemplo Cook del propio menú Ayuda; el `κ₂` se medía sobre la `K` sin restricciones
  —singular por construcción— y marcaba **`Crítico` en todos los modelos**; el formato
  factorizado imprimía **64 celdas de 324 como `0.00`** en la `kₑ` del Q9, que no tiene ni un
  cero; las tablas recortadas mandaban al alumno a una **exportación que no tiene resultados**;
  la flecha de carga se dibujaba fuera de la figura. Está **sin commit**; el guion de
  qué exportar y qué mirar está en [../rutina/BACKLOG.md](../rutina/BACKLOG.md)
  (*Pendientes visuales*) y el razonamiento y lo descartado en
  [2026-09-09_memoria-aprovecha-la-hoja.md](2026-09-09_memoria-aprovecha-la-hoja.md).
- **Marco metodológico de la tesis** frente al canon del tribunal (UATF): objeto/campo,
  formulación del problema como interrogante, 3 vs. 4 capítulos, preliminares. Ver
  `tesis/README.md`.
- **Redundancia transversal** en la tesis y el criterio del 0,3 % en la validación contra
  SAP2000: pendientes de criterio del autor según la revisión del 06-10.
- **Validación visual del Post-Proceso y de la Memoria** tras la vectorización y tras la
  corrección de la extrapolación Q4 (2026-09-07): el autor debe abrir la GUI con el ejemplo
  canónico Q4 y con Cook 32×32 Q9 (gradiente, isolíneas, crudo, probe, 3D) y generar una
  Memoria de Cálculo. **Todas las tensiones nodales Q4 cambian** (el VM máximo del ejemplo
  canónico pasa de 977,46 a 864,70); Q9 no cambia. El diagrama de malla ya no rotula elementos
  demasiado chicos para el texto. **Sumar a esa validación** (rutina, sesión 04, 2026-09-08):
  la **Vista 3D en modo Crudo** —que hasta ahora dibujaba el campo transpuesto dentro de cada
  elemento— y su **nueva escala de color**. **Sumar también** (rutina, sesión 11, 2026-09-09):
  las **figuras de la Memoria en una malla real** (con Cook Q9, el diagrama del modelo y la
  deformada ya no son una mancha de discos: los nodos siguen el LOD del canvas), la colorbar
  del contorno con **símbolo y unidad** (`σVM [MPa]`) y las **tablas con unidades**; el
  ejemplo canónico debe salir igual que antes. El detalle de qué mirar está en
  [../rutina/BACKLOG.md](../rutina/BACKLOG.md), *Pendientes visuales*.
- **Editar un material ya invalida la solución** (rutina, sesión 08, 2026-09-09). Hasta este
  commit, cambiar E, ν o ρ desde *Modelo ▸ Material* no ponía `is_solved = False`, así que
  `F5` cortaba con el fast-path de `post_tab._auto_solve` y devolvía **las tensiones del
  material anterior**, con *Exportar Memoria PDF* habilitado sobre esa corrida vieja. Si en
  algún momento se anotó un resultado después de tocar la librería de materiales **sin
  reabrir el proyecto**, ese número hay que regenerarlo. Las cifras de la tesis **no** están
  afectadas: salen de `tests/vv_*.py` y de `tesis/figuras/gen_anexo_calculo.py`, que arman el
  proyecto desde cero y no pasan por el diálogo.
- **Tesis, párrafo sobre el defecto corregido**: `04_resultados.tex` (§MMS, análisis) declara
  que la matriz E_Q4 estuvo mal hasta la revisión final y que por eso se agregó la prueba de
  reproducción polinómica. Es honestidad de V&V; el autor decide si lo conserva.
- **Validación del autor del TeX Live embebido (2026-09-08)**: (1) abrir la GUI y exportar
  una Memoria (Q4 canónico y Cook Q9, ambos estilos) y la Teoría MEF: debería verse idéntica
  a la de MiKTeX (mismas fuentes Latin Modern, mismo pdfTeX); (2) probar el instalador nuevo
  `installer/Output/EduFEM-Setup.exe` (126 MB) en una PC **sin MiKTeX** y, si se puede, con un
  usuario de Windows con tilde o espacio en el nombre (el instalador debe proponer
  `C:\ProgramData\EduFEM`); (3) decidir si sube `MyAppVersion` (1.0.0) en el `.iss`; (4) la
  tesis afirma en `06_anexos.tex` (Anexo A, párrafos "Es la vía recomendada…" y "El núcleo
  numérico…") que la Memoria requiere MiKTeX instalado: ya no es cierto, hay que reescribirlo.
- **Dictamen 2026-09-07** (artifact "Dictamen EduFEM"): quedan abiertos los hallazgos MAYOR y
  MENOR no mecánicos (objeto de estudio vs. población, hipótesis circular, preliminares,
  estado del arte, etc.). Los bloqueantes están cerrados (ver abajo).

## Convenciones que conviene tener presentes

- El canon está partido: [../../CLAUDE.md](../../CLAUDE.md) tiene las reglas duras y el
  ruteo; el detalle vive en [../convenciones/](../convenciones/) y se lee **según lo que
  vayas a tocar**.
- Antes de agregar algo que "falta", pasá por
  [no-reintroducir.md](../convenciones/no-reintroducir.md): la mayoría de las ausencias son
  decisiones tomadas.
- Rutas que no se pueden mover: [../MAPA.md](../MAPA.md) §3.
- La validación **visual** la hace el autor abriendo la GUI. Un agente puede correr smoke
  tests headless (`MainWindow` + `root.withdraw()`, sin `mainloop`), pero no debe declarar
  que algo "se ve bien".

## Hecho recientemente

- **2026-09-11** — **Presentación de defensa y video narrado** en
  [tesis/presentacion/](../../tesis/presentacion/): `Defensa_EduFEM.pptx` (38 diapositivas,
  editable, con notas del orador; también en PDF) se construye con `build_deck.py` a partir
  de `guion.json`, sigue el orden y los tiempos del Taller 6 de la UATF y toma todas las
  cifras de los `.tex` (actualizada tras la reestructuración de `tab:comparativa`).
  `video/Defensa_EduFEM.mp4` (25:31, 1080p) narra la defensa completa en primera persona con
  voz neuronal `es-BO-MarceloNeural` (edge-tts + ffmpeg, `video/hacer_video.py`), con el
  guion cronometrado en `video/guion_video.md` y una copia del `.pptx` con la narración
  embebida. `tesis/main.pdf` recompilado (149 hojas). Sin commit; los binarios (`.mp4`,
  `.pptx` narrado) pesan ~60 MB, el autor decide si los versiona. Pendiente del autor:
  revisar el video (voz, ritmo, pronunciación de las cifras) y ensayar los tiempos en vivo.

- **2026-09-10** — **Instalador profesional: un archivo que deja todo listo.** El `.exe` ya
  lleva datos de versión (Windows lo mostraba sin Descripción ni Empresa, que es además una
  señal que miran los filtros de reputación) y la versión pasó a tener **una sola fuente**,
  `config/settings.py::APP_VERSION`, que leen `build.spec` y el preprocesador del `.iss`. El
  asistente estrena imágenes propias, licencia MIT y un texto de bienvenida que dice lo que
  importa; declara `MinVersion` y arquitectura; deja registro en `%TEMP%` para diagnosticar
  instalaciones fallidas; registra `App Paths` (Win+R ▸ `edufem`); y **asocia los `.edufem`**
  con su propio icono (`resources/icons/edufem_doc.ico`, nuevo en `make_icon.py`), de modo que
  un proyecto se abre con doble clic: `main.py` recibe la ruta como argumento y
  `MainWindow(project_path=...)` la abre. `main.py` además fija el **AppUserModelID** (sin él,
  el icono anclado a la barra de tareas se desprende del acceso directo) y crea el **mutex**
  que le permite al asistente ver que EduFEM está abierto en vez de copiar sobre un `.exe` en
  uso; las tres constantes viven en `config/settings.py` y `tests/test_distribucion.py` (12
  checks, en el gate) verifica que el `.iss` no se desincronice. `tools/build_all.ps1` quedó
  en cuatro pasos, con la carpeta portable como opción (`-Portable`) en vez de armarla en cada
  build: `dist/` queda con solo `EduFEM.exe`, y `docs/MAPA.md` §2 explica cuál de las carpetas
  generadas es el entregable y cuál se puede borrar. **El `.exe` adelgazó 3,9 MB**: apareció
  `lxml` en el bundle, que entra porque `fontTools` lo prefiere si está en el entorno y que
  nadie en EduFEM importa; excluido en `build.spec`. Actualizados el LEEME, `README.md`,
  `CLAUDE.md`, `docs/MAPA.md`, `tools/README.md`, `requirements.txt`,
  `.claude/rules/empaquetado.md` y la **tesis** (Anexo A y §3: el manual ya no pide instalar
  MiKTeX). Gate verde. **Sin commit** (el autor prueba el instalador). Detalle y trampas del
  `.iss`: [2026-09-10_instalador-profesional.md](2026-09-10_instalador-profesional.md).
- **2026-09-09** — **Las tres fuentes que el autor no tiene, resueltas; `.bib` ajustado a sus
  ejemplares.** `roache1998verification` → **`oberkampf2010vv`** (que sí tiene);
  `perezsantiago2023fem` se retiró y **volvió el mismo día**, porque el autor consiguió el PDF:
  las cuatro fuentes que lo habían reemplazado se dieron de baja por inflar la bibliografía; `cook1974membrane` → atribución en prosa, porque **Cook 2002 no
  contiene la membrana de Cook** (verificado). Además se corrigieron las **9 entradas que
  declaraban una edición distinta de la que el autor tiene** y **30 pasajes de prosa** cuya
  fuente no los sostenía: la contradicción de `tab:comparativa` (los simuladores de Lee pasan a
  licencia «Comercial» y a «2D/3D»: están embebidos en VisualFEA), «modos propios de vibración»
  → «de la matriz de rigidez», el umbral de Verdict (**es 0,30, no 0,50**), la paleta jet, el
  ordenamiento de mínimo grado y el «0,05 %» de la nota de Cook, que no salía de ningún GCI
  calculado. 25 entradas, 132 páginas, cero citas indefinidas.
  El `.bib` queda en **22 entradas**, todas con el ejemplar en mano salvo Roache y Cook 1974,
  que se sustituyeron. Detalle en
  [2026-09-08_bibliografia-tesis.md](2026-09-08_bibliografia-tesis.md).

- **2026-09-09** — **Bibliografía: Vancouver puro en el cuerpo + respaldo documental
  verificado.** Se retiraron los localizadores de página de las citas (decisión del autor: el
  cuerpo queda `[7]` a secas) y se trasladaron a **`tesis/respaldo_citas/respaldo_citas.pdf`**
  (44 pág.), que registra por cada cita el ejemplar consultado, la página impresa y el pasaje
  textual que la sostiene. Auditoría multiagente de los 22 PDF de `tesis/bibliografia/`
  (42 agentes, 147 respaldos localizados); copias con los pasajes resaltados en
  `tesis/bibliografia/resaltados/` (gitignorado, copyright). **Dos resultados que esperan al
  autor**: (1) el `.bib` declara **ediciones que no son las que él tiene** — Zienkiewicz
  7.ª/2013 vs. **6.ª/2005**, Bathe 2.ª/2014 vs. **Prentice Hall 1996**, Strang 2.ª/2008 vs.
  **1.ª/1973**, Timoshenko 3.ª/1970 vs. **2.ª/1951**, Hughes Dover 2000 vs. **Prentice-Hall
  1987**; (2) **contradicciones internas** en `tab:comparativa` (los simuladores de Lee
  figuran con licencia «Libre» pero están embebidos en VisualFEA, que el propio párrafo
  llama «cerrados y de pago»; y como «2D» cuando el artículo documenta sólidos 3D de 20
  nodos). Detalle en [2026-09-08_bibliografia-tesis.md](2026-09-08_bibliografia-tesis.md).
  Faltan en la carpeta **Roache 1998 y Cook 1974**: no se pudieron verificar.

- **2026-09-09** — **Rediseño de la capa visual, el lienzo y la interacción: "la interfaz
  enseña el método"** (pedido del autor con libertad total; sin commit, espera validación
  visual). El mismo modelo se mira con **tres lentes** según la fase: (a) *geometría* en Pre,
  con la **cuadrícula anclada al mundo** (serie 1-2-5, ejes X=0/Y=0 rotulados, paso en el
  readout) y una **franja lectora** al pie del lienzo que describe en términos del MEF lo que
  hay bajo el cursor (nodo: coordenadas, índices de GDL, restricción, carga, elementos que lo
  comparten; elemento: conectividad antihoraria, material, espesor, área, GDL → tamaño de kₑ)
  o la pista de gesto de la fase; (b) *sistema discreto* en Proceso: los dos **índices de GDL
  en K** junto a cada nodo (los restringidos tachados), la **lente del elemento seleccionado**
  (numeración local 1..4, ejes ξη según la convención del motor, puntos de Gauss físicos), el
  banner con la **tira del método** `N › J › B › D › kₑ › F › K` (chips clickeables 1:1 con
  M1..M7, con estado inactivo/visitado/activo; reemplaza al breadcrumb de la barra de estado);
  (c) *campo* en Post: contorno + **reacciones en los apoyos** (`R = K·u − F`, flechas que
  llegan al nodo desde afuera con rótulo en la cola, toggle en el panel del Post). Además:
  subtítulos de banner con el orden del método, barra de estado con `GDL: 18 (12 incógnitas)`
  y mensajes por fase con los números del modelo. **Segunda tanda, módulos educativos** (pedido
  del autor): la vista viva del sistema K·u = F que había nacido como panel propio de Proceso
  **se fundió en M7** (esqueleto gris de K bajo el heatmap —la forma que la malla decide, que
  cada kₑ rellena— + cabecera `2N GDL · restringidos → incógnitas · bloques ≠ 0 · semiancho`;
  lógica pura en `education/components/system_structure.py`); los ejes ξη del cuadrado natural
  de M1/M2/M3/M5 pasaron a flechas naranja/violeta y esos módulos dibujan los mismos ejes sobre
  el elemento real con el glifo compartido `gui/preprocessing/canvas_glyphs.py`; M6 rotula con
  `fmt` y unidades (cierra el ítem [8] del BACKLOG); el panel de módulos envuelve las
  descripciones al ancho real. Lógica pura en `canvas_logic.py`; widget nuevo
  `method_strip.py`; tests `test_canvas_lens` (sin display) y `test_canvas_lens_gui` (Tk, abre
  M7 de verdad) en el gate. Gate verde. Nota:
  [2026-09-09_rediseno-capa-visual.md](2026-09-09_rediseno-capa-visual.md).
- **2026-09-08** — **Bibliografía de la tesis auditada, saneada y con los vacíos cerrados**
  (23 entradas, todas con ≥2 citas; se retiró `oberkampf2010verification` y se sumaron las tres
  del **material docente de la carrera**, que estaba en `tesis/Material docente/` y es la fuente
  normativa que le faltaba al capítulo metodológico). La bibliografía **no** sobraba: el
  problema era de cobertura. Los demás huecos se cerraron **sin entradas nuevas** —
  redirigiendo a fuentes ya presentes, volviendo autosuficientes las afirmaciones (Cook 23,96
  por extrapolación propia; invariancia frente a $E$ en Timoshenko) y cambiando apelaciones a
  autoridad ausente por el argumento técnico. Ver
  [2026-09-08_bibliografia-tesis.md](2026-09-08_bibliografia-tesis.md).
- **2026-09-09** — **Las citas al material docente se reemplazaron por sus fuentes de origen**:
  Álvarez de Zayas (objeto/campo/problema), Hernández-Sampieri y Mendoza 2018 (enfoque
  cuantitativo, variables, muestra dirigida) y García-Córdoba 2005 (investigación tecnológica).
  Motivo: los tres decks de cátedra **no tienen bibliografía** y uno de los docentes integra el
  tribunal. Siguen 23 entradas. **Hechos también los localizadores de página** (8 citas con
  `p.~NN`, verificados abriendo cada libro: el desfase PDF↔impresa no es constante).
  **Pendientes del autor**: la monografía de Álvarez no trae pie de imprenta (se cita sin año);
  y `tesis/bibliografia/Elast2DOñante.pdf` más los ocho PDF de `tesis/Material docente/` siguen
  **trackeados en un repo público** siendo material ajeno — decidir si se sacan de HEAD (ya están
  en el historial). Los libros nuevos sí quedaron gitignorados.
- **2026-09-08** — **TeX Live recortado embebido: la Memoria y la Teoría ya no dependen de
  MiKTeX.** Motivo: en PCs de usuarios, MiKTeX básico abría un diálogo de instalación por cada
  paquete faltante (booktabs, tcolorbox, pgf, babel-spanish, listings…) y sin internet fallaba;
  medido con `pdflatex -recorder`, los cuatro documentos reales consumen 263 archivos (19,2 MB,
  de los que 13,3 MB son el `.fmt` de MiKTeX). Implementado: (a) `tools/build_texlive.py`
  genera `vendor/texlive` (gitignored) desde TinyTeX-0 v2026.09 (TeX Live 2026) + `tlmgr
  install` de la lista fija `PACKAGES` contra el snapshot `texlive.info/tlnet-archive/2026/09/07`
  + formato pdflatex con silabeo español + poda (Perl, Ghostscript, docs, OpenType, motores Lua)
  + `ls-R` regenerados; valida compilando Memoria Q4 educativo/directo, Memoria Q9 y Theory Hub
  antes y después de podar. Resultado: **50,9 MB / 4180 archivos**; el instalador pasa de 102 a
  **126 MB**. Hallazgos del build: `ec` es obligatorio (pylatex carga `fontenc[T1]` antes de
  `lmodern` y LaTeX pide `ecrm1095.tfm`), `l3backend` ya vive en `l3kernel`, y en TL 2026
  `pdflatex.exe` es un lanzador de 6 KB que carga `pdftex.dll`. (b) Nuevo
  `education/components/latex_runtime.py`: resuelve el compilador (`EDUFEM_TEXLIVE_DIR` →
  `texlive/` hermana del `.exe` o `vendor/texlive` → PATH, donde MiKTeX recibe
  `-enable-installer`), compila en un temporal con ruta ASCII sin ventana de consola, dos
  pasadas, y mueve el PDF al destino; `TheoryDoc.compile_to` y `TheoryViewer` pasan por ahí
  (adiós `Document.generate_pdf` y `latexmk`). La Memoria guarda sus figuras en ese `workdir` y
  las referencia por nombre relativo. (c) `installer/EduFEM.iss` copia `vendor/texlive` a
  `{app}\texlive`, y `[Code]` elige `C:\ProgramData\EduFEM` como carpeta por defecto si el
  perfil del usuario tiene tildes o espacios (TeX Live no resuelve rutas no ASCII).
  (d) `tools/build_all.ps1` arma el bundle si falta; LEEME, README, CLAUDE.md, MAPA, reglas y
  convenciones actualizados. Verificado: `test_memoria_calculo` 23/23 y nuevo
  `test_latex_runtime` 7/7 con el bundle (incluye PDF en destino con tilde y espacio), bundle
  copiado a otra ruta con espacio compila, `.exe` recompilado (`dist/EduFEM.exe`, 106 MB) e
  instalador compilado (`installer/Output/EduFEM-Setup.exe`). **Sin commit** (el autor revisa);
  pendientes del autor en *Decisiones abiertas*.
- **2026-09-07** — **Bug real corregido: extrapolación Q4 Gauss→nodos.** `fem/stress.py`
  tenía `_Q4_EXTRAP` escrita a mano para OTRO orden de puntos de Gauss que el que produce
  `get_gauss_points_2d(2)` ((-,-),(-,+),(+,-),(+,+)): columnas de los PG 3 y 4 intercambiadas,
  desde el primer commit (2026-02-27). No reproducía ni un campo lineal. Ahora Q4 y Q9 se
  construyen igual (`_build_extrapolation_matrix`: E = inv(M), M_ji = N_i(ξ_j, η_j) con los
  puntos reales). Copias a mano eliminadas en `file_io/memoria_calculo.py` y
  `tesis/figuras/gen_anexo_calculo.py` (fuente única `fem.stress.extrapolation_matrix`).
  Guard: `tests/test_vv_extensions` [7/7] exige reproducción exacta de campos polinómicos en Q4 y
  Q9. Por qué nadie lo vio: el MMS mide desplazamientos, Timoshenko usa Q9, Cook mide flecha; y en
  mallas finas uniformes los errores nodales se cancelan por simetría (en el ejemplo canónico de 4
  elementos el VM de algunos nodos estaba 2–4× mal). Regresión 81/81 OK, batería completa en verde.
  **MMS ampliado** (`tests/vv_mms.py`): 4 configuraciones {unitario, distorsionado} ×
  {tensión plana, deformación plana} + norma L² del campo de tensiones recuperado
  (`fem.error_norms.compute_stress_recovery_error`); tasas: desplazamiento teóricas en las 4;
  σ* O(h^1,5) Q4 / O(h²) Q9. CSV nuevos `mms_*_{dist_tp,unif_dp,dist_dp}.csv` + `mms_resumen.csv`;
  figura `mms_convergence_stress.png`. **Tesis**: Anexo G regenerado (`anexo_calculo_data.tex`,
  `mem_contorno_vm.png`); eq:extrap-q4 con el orden real de PG; cotas de error honestas ("0,05 %
  en tensiones" → 0,04 % en σx, 2,9 % en τxy, 0,26 % flecha; vs SAP2000 0,21 %/0,56 %); Barlow
  corregido para Q9; regla "p+1" → "un punto más por dirección"; criterios de aceptación explícitos
  en §2.1; tab:mms con columna σ*, nueva tab:mms-configs y fig:convergencia-tension; tabla de
  componentes de Timoshenko con columna de error.
  **Segunda tanda del mismo día**: (1) **von Mises correcto en deformación plana** en todas las
  rutas (`fem/batch.py::principal_and_vm_batch(stress, sigma_z)`, `out_of_plane_factor`,
  `sigma_z_from`; `fem/stress.py`; `fem/probe_query.py` raw/smooth/grids; memoria; oráculo
  de regresión) con `sigma_z = nu (sx+sy)`; guard `test_vv_extensions` [8/8]; eq:principales-vm
  de la tesis con `\sigma_z`. (2) **Jacobiano escalado por FILAS** (tangentes) en
  `fem/mesh_quality._jacobian_samples` (antes columnas: cantidad distinta); tesis: eq:jacobiano
  con la convención del motor (filas ξ,η), eq:scaled-jacobian por filas, umbrales Verdict vs.
  UI y estado de 4 métricas documentados. (3) **Cook**: `U_Y_REF = 23.96` en `vv_cook.py`
  (antes 23.95), CSV/figura regenerados, tabla y textos con los errores nuevos e incertidumbre
  de la referencia (Richardson ≈ 23,97). (4) **`tests/bench_timing.py`** mide COLAMD vs
  MMD_AT_PLUS_A (1,7×/2,0×/2,9× a 2178/8450/33 282 GDL); tab:tiempos remedida hoy. (5) Nuevo
  **`tests/test_interop.py`** (CSV/ZIP ida y vuelta + DXF idempotente) citado en §3.3 y en
  tab:vyv-repro (objetivo 5 con evidencia). (6) Mecánicos: portada con tildes, `\markboth` en
  Introducción/Resumen/Conclusiones, `\appendixautorefname` vía `\extrasspanish` (ya no
  "Apéndice"), `sec:metodologia`, artículos ante `\autoref{eq:}`, "Cap. 3", palabras clave 6,
  bib (organization {{}}, Lee = "Jae Young Lee" + Ryu, issue 2 y 5, {van der Walt}), 21,32 GPa y
  origen de E, pdflatex en Anexo A, fila `orphan_free_node`, DXF→Q9 automático y unidades,
  Anexo G "condensada", rango 0..2N−1, Anexo E en la lista de anexos, doble "variable
  independiente", PyMuPDF, CALFEM, cobertura del canal. Compila limpio, 128 páginas. Batería
  completa en verde (regresión 81/81, vv_extensions 8/8, interop, fem, memoria 23/23, probe,
  canvas). **Sin commit** (el autor revisa).
  **Tercera tanda (pedido del autor)**: §2.1 reestructurado de 10 subtítulos de diseño
  experimental (control, repetición, protocolo…) a 6 que siguen el diagrama del Taller 4 del
  tribunal (modelo de simulación numérica · variables · matriz de consistencia · casos de
  estudio y criterio de selección · procedimiento, instrumentos y reproducibilidad · criterios
  de aceptación y contraste de la hipótesis); la parte de software pasó a ser §2.2 «Diseño e
  implementación de EduFEM» con sus antiguas secciones como subsecciones (2.2.1–2.2.9).
  Etiquetas conservadas: `sec:metodologia`, `sec:proceso-met`, `sec:variables-met`,
  `sec:matriz-consistencia`, `sec:poblacion`, `sec:validacion-datos`,
  `sec:validacion-resultados`; nueva `sec:diseno-edufem`; borradas (sin referencias)
  `sec:hipotesis-met`, `sec:sistema-control`, `sec:sistema-repeticion`,
  `sec:protocolo-calculo`. Frases de la Introducción que enumeraban los subtítulos viejos
  actualizadas. Compila limpio, 127 páginas.
  **Cuarta tanda (2026-09-08, pedido del autor tras analizar el material del tribunal):**
  coherencia Introducción ↔ Cap. 2 ↔ Cap. 3 ↔ Conclusiones según el esquema
  problema–objeto–campo–objetivo–hipótesis–tríada. (a) **Objeto de estudio técnico** («el
  análisis de medios continuos en elasticidad lineal plana por el MEF») y **campo de acción
  pedagógico** («su enseñanza: el software que expone el canal y la memoria»), como en el
  ejemplo del propio catedrático (objeto = losas, campo = costos); así población, variables y
  resultados quedan dentro del objeto. (b) **Problema científico** reformulado como
  respondible: VI = forma de exponer el canal (transparencia, interactividad,
  verificabilidad); VD = observabilidad y contrastabilidad del procedimiento; «apoyo a la
  comprensión» pasa a ser el para qué. (c) **Delimitación** institucional (Carrera de Ing.
  Civil UATF como destinataria), espacial (aula y equipo del estudiante), temporal (gestión
  2026) y disciplinar. (d) **Sexto objetivo específico**: nuevo OE1 «Fundamentar
  teóricamente…» (cubre el Cap. 1) + fila en `tab:consistencia`; el instrumental pasa a ser
  el sexto (01, 02b, 04:95, 05). (e) **Hipótesis**: puente de tres variables en la intro,
  coherente con las variables del problema. (f) **Tríada**: cada conclusión nombra su
  capítulo; conclusión nueva para el Cap. 1; recomendaciones ancladas por capítulo + nueva
  «Ampliación de la batería de validación» (caso civil en deformación plana). (g) §3.8
  responde explícitamente al problema y al objeto. Compila limpio, 130 páginas. Sin commit.
- **2026-09-06** — **Cerradas las tres decisiones abiertas del post-proceso.**
  (a) **Invariantes nodales**: σ1, σ2 y von Mises ya no se extrapolan ni se promedian; se
  extrapolan y promedian las tres componentes cartesianas y las invariantes se recomputan desde
  ellas (`fem/stress.py` + `fem.batch.principal_and_vm_batch`). Las componentes no cambian ni un
  bit y **ningún CSV de V&V se movió**; sí cambia el VM nodal mostrado: +3,0 % en el máximo de
  Cook Q9 32×32 y +8,3 % en el ejemplo canónico. Corrige una incoherencia real — el nodo 8 del
  Anexo F mostraba VM = 8,96 con σx = −54,23, σy = −11,55 y τxy = −84,65, cuyo VM coherente con
  esas componentes es 154,74 (componentes que, a su vez, eran incorrectas por el bug de
  extrapolación Q4 corregido el 2026-09-07; hoy el nodo 8 da σx = 39,34, σy = −74,16,
  τxy = 107,67, VM = 211,52). El marco teórico de la tesis (§2, extrapolación) **ya describía este comportamiento**;
  ahora el código lo cumple. `tesis/figuras/anexo_calculo_data.tex` regenerado con
  `gen_anexo_calculo.py`.
  (b) **RCM eliminado**: medido, solo gana por encima de ~8500 GDL (7–19 %) y por debajo pierde;
  a ese tamaño el resto de la app tarda segundos. Se borraron `SOLVER_USE_RCM`,
  `SOLVER_RCM_MIN_DOF` y la rama de permutación. Queda `SOLVER_PERMC_SPEC = "MMD_AT_PLUS_A"`,
  remedido: 1,6× a 2178 GDL y 2,1× a 8450 y 33 282 GDL (la constante citaba mal la malla).
  Menciones a RCM quitadas de la tesis (nomenclatura, marco teórico, conclusiones).
  (c) **`figure_export._fill_field` vectorizado** sobre `canvas_raster.rasterize_triangles`:
  el contorno de la memoria pasó de 16,7 s a 0,51 s en 1024 elementos y de 47,6 s a 1,26 s en
  4096, con **0 píxeles distintos** (`test_canvas_raster.test_figure_export_field`). En el
  ejemplo canónico de 4 elementos hay una regresión de ~100 ms (155 → 245 ms) por el overhead
  del camino por lotes: irrelevante frente a los segundos de `pdflatex`. `render_mesh_diagram`
  ya no rotula elementos más chicos que el texto (ilegibles y caros): 1,65 s → 0,83 s en 1024
  elementos. Lo que queda caro ahí es Pillow, una llamada de dibujo por elemento.

- **2026-09-06** — **Motor vectorizado por lotes y retiro de numba.** Nuevo `fem/batch.py`
  (geometría J/det J/B, rigidez, scatter COO y tensiones de todos los elementos a la vez con
  `einsum`/`matmul`); `fem/assembly.py`, `fem/stress.py`, `fem/probe_query.compute_raw_grids`,
  `fem/mesh_quality` y `fem/error_norms` lo usan. Solucionador con `SOLVER_PERMC_SPEC =
  "MMD_AT_PLUS_A"` (SuperLU sobre CSC). Canvas: `gui/preprocessing/canvas_raster.py`
  (rasterizado Gouraud e isolíneas vectorizados, paridad píxel a píxel). Borrados
  `fem/_numba_compat.py`, los 17 kernels `@njit` y el warm-up de numba; `build.spec` excluye
  `numba`/`llvmlite`. Motivo: el `.exe` nunca tuvo numba (onefile extrae a una carpeta
  aleatoria y el cache del JIT jamás acertaba) y los kernels escalares corrían en Python puro.
  Cook Q9 32×32 (8450 GDL) sin numba: ensamblaje 3,35 s → 0,054 s, tensiones 0,50 s → 0,06 s,
  contorno crudo 2,95 s → 0,04 s, isolíneas 51 s → ~0,1 s; 33 k GDL: solve 0,73 s (antes 2,2 s
  con numba). Versión legible de `fem/` intacta como oráculo de `tests/test_solver_regression.py`
  (81 checks ≤ 1e-9); `tests/test_canvas_raster.py` (paridad); batería completa y V&V en verde
  con CSV idénticos; tabla `tab:tiempos` de la tesis regenerada. **Pendiente del autor:
  validación visual** del Post-Proceso (gradiente, isolíneas, crudo, probe, 3D) — debería verse
  idéntico y responder en < 1 s en Cook 32×32 Q9 — y rebuild del `.exe` + instalador.
- **2026-09-06** — Reorganización del repositorio y espacio de trabajo para agentes:
  `docs/` estructurado (`convenciones/`, `notas/`, `auditorias/`, `teoria/`), auditorías
  consolidadas, `CLAUDE.md` reducido de 909 a ~230 líneas, `README.md` y `AGENTS.md`
  creados, insumos de distribución movidos a `installer/dist_extra/`. Detalle:
  [2026-09-06_reorganizacion-repo.md](2026-09-06_reorganizacion-repo.md).
- **2026-09-06** — Segunda tanda de la auditoría 2026-06-10 (medios y bajos): traza en los
  listeners de undo y en el error de `auto_solve`; guard de `det J` en `error_norms`; el
  snapshot de undo del cambio Q4↔Q9 pasó a después del `askyesno`; guards de `winfo_exists`
  en los `after()` de tres diálogos; `memoria_style_dialog` y `about_dialog` usan
  `center_dialog`; tolerancias `1e-10` reemplazadas por `NUMERICAL_TOLERANCE`; eliminados
  5 constantes sin consumidor, `highlight_node`/`highlight_element` y 6 llamadas redundantes
  a `_refresh_menu_state`; comentarios de paleta y de módulos M8/M9 corregidos;
  `recompute_q9_midnodes` por índice inverso; `test_draw_mode` con guard de Tk.
- **2026-09-06** — Cerrado el Top-10 de la auditoría 2026-06-10. P0: `change_element_id`
  ahora sincroniza `_node_to_elements` (reg. en `test_node_cascade`) y `assembly` ignora la
  carga nodal huérfana en vez de romper el solve. P1: autofix de cargas superficiales por
  identidad de objeto; `_check_orphan_free_nodes` nuevo (con autofix e hint) y
  `nodes_in_elements` deja de contar los sets vacíos que `remove_element` deja al preservar
  huérfanos. P2: `capture()` antes de los autofixes, snapshot inmutable del project para el
  worker del PDF, y `to_float_flex` para la coma decimal de Excel. P3: `mod06` usa
  `redraw_overlays_only()`; `.gitattributes` creado. Batería completa + V&V en verde.
- **2026-09-06** — Auditoría del canon de instrucciones: corregidas 21 afirmaciones obsoletas
  en `docs/convenciones/` (orden `Ctrl+1..7` que daba `D, B` en vez de `B, D`; chips
  `Q4 · 8 DOF` → `GDL`; `AnalysisTypeDialog` con dos videos inexistentes y la matriz D
  atribuida a M3; fallback a `simpledialog`, botón Reset y sub-pestaña de Educación en el Post,
  los tres inexistentes; contrato `BaseEducationalModule` / `GaussCoordReadout` descrito en
  presente; bullet duplicado en M4; `pdf_report`). `CLAUDE.md` 229 → 187 líneas quitando
  duplicación interna, y `.claude/rules/` (5 archivos con `paths:`) hace que cada capítulo se
  cargue solo al tocar su área.
- **2026-06-10** — Auditoría general del repo + revisión profesional de la tesis
  (diagnóstico, sin fixes) y comando `/schedule`.
- **2026-06-01** — Implementadas las recomendaciones P0–P2 de la auditoría integral del
  2026-05-31 (incluido el bug de `node_index_map` stale).
