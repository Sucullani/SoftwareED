# Rediseño de la capa visual, el lienzo y la interacción

**Fecha**: 2026-09-09 · **Autor**: agente (Claude), a pedido del autor · **Estado**: terminado, sin commit (espera validación visual)

## Qué se pedía

«Rediseñá la capa visual, el canvas y la interacción. Libertad total en estética,
arquitectura de render y UX. Quiero que la interfaz misma enseñe el método.»

## Qué se hizo

La idea rectora: **el lienzo es la pizarra del método**. El mismo modelo se mira con una
lente distinta en cada fase, y cada lente muestra lo que el MEF hace en ese momento.

| Fase | Lente | Qué enseña |
|---|---|---|
| Pre | geometría | La **cuadrícula anclada al mundo** (serie 1-2-5, ejes X=0/Y=0 rotulados, paso en el readout) es el sistema de coordenadas en el que el alumno tipea los nodos. La **franja lectora** al pie del lienzo describe lo que hay bajo el cursor en términos del MEF: un nodo son dos GDL con índice en K, una restricción, una carga y los elementos que lo comparten; un elemento es su conectividad antihoraria, material, espesor, área y ocho (o dieciocho) GDL que definen el tamaño de kₑ. |
| Proceso | sistema discreto | Cada nodo muestra sus **índices de GDL**; los restringidos van **tachados** (la fila y la columna que se eliminan). El elemento seleccionado muestra su **numeración local**, sus **ejes ξ, η** con la convención del motor y sus **puntos de Gauss**: el objeto sobre el que trabajan los módulos ①..⑦. El banner es la **tira del método** `N › J › B › D › kₑ › F › K`. Abajo, la **vista viva de K·u = F**: el patrón de bloques que la malla genera, con las filas restringidas atenuadas, y los números `2N · restringidos · incógnitas · bloques · semiancho`; sigue al hover y a la selección del lienzo (el mismo color en las dos vistas de la misma cosa). |
| Post | campo | Contorno + **reacciones en los apoyos**, `R = K·u − F`, con la misma gramática que las cargas (la punta en el punto de aplicación): el diagrama de cuerpo libre del alumno. |

Transversal: subtítulos de banner con el orden del método, barra de estado con
`GDL: 18 (12 incógnitas)` y un mensaje por fase con los números del modelo (`Proceso: cada
elemento aporta su kₑ (8×8) a K (18×18); 6 GDL restringidos dejan 12 incógnitas · F5 resuelve
K·u = F`).

**Arquitectura de render**: no se reescribió el `MeshCanvas` (4100 líneas con seis tests
encima). Se reformuló `redraw()` como una **pila de capas documentada** (cuadrícula → malla
fantasma → campo → elementos → nodos → GDL → cargas → superficiales → restricciones →
reacciones → realce → lente → isolíneas → colorbar → ejes → preview → capas educativas →
franja), con la lente fijada por `set_phase`, y se sumaron dos listas de listeners
(`hover_listeners`, `redraw_listeners`) para que otros paneles sigan al lienzo sin acoplarse.
Toda la lógica nueva es pura (`canvas_logic.py`, `system_view_logic.py`) y se testea sin Tk.

Detalle normativo en [canvas-preproceso.md](../convenciones/canvas-preproceso.md) (*Lentes por
fase*) y [arquitectura.md](../convenciones/arquitectura.md) (*Panel de Proceso*).

## Segunda tanda: los módulos educativos (mismo día, pedido del autor)

El autor pidió enfocarse en los módulos y opinó que la vista *Sistema K·u = F* del panel de
Proceso debía vivir en M7. Se le dio la razón, pero **sin duplicar K**: M7 ya tenía un
heatmap de K, y agregarle el patrón de bloques como segunda imagen hubiera hecho el overlay
más alto que una pantalla de 768 px y hubiera mostrado dos veces la misma matriz. En cambio:

- **M7 muestra el esqueleto de K** (`_build_skeleton_image`, sobre `render_pattern` de la
  lógica pura, ahora en `education/components/system_structure.py`) *debajo* del heatmap, y
  las celdas todavía nulas quedan transparentes (`np.ma.masked_where`) para que se vea: la
  forma de K la decide la malla, los valores los pone cada kₑ. En modo *Reducida* no hay
  esqueleto (esa vista es "lo que queda"). La cabecera lleva los números del sistema.
- **El panel de Proceso vuelve a tira + módulos.** Se borraron `gui/processing/system_view.py`
  y los `hover_listeners` / `redraw_listeners` del `MeshCanvas` que solo él consumía; las
  constantes `SYSTEM_VIEW_*` pasaron a `EDU_M7_SKELETON_*`.
- **Coherencia ξη**: la lente del lienzo y los módulos hablaban de los mismos ejes con
  glifos distintos (la lente con flechas naranja/violeta, los cuadrados naturales con una
  cruz gris igual para ambos). Ahora `gui/preprocessing/canvas_glyphs.draw_natural_axes`
  dibuja las flechas sobre el elemento tanto para la lente como para las capas de M1/M2/M3/M5,
  y `edu_plot_style.draw_natural_axes_mpl` pone los mismos colores en el cuadrado natural.
  `EDU_NATURAL_AXES_COLOR` se retiró.
- **M6** con `fmt` + unidades (ítem [8] del BACKLOG); **panel de módulos** con las
  descripciones envueltas al ancho real (el `<Configure>` de la fila leía el ancho del botón
  antes de mapearse); título del cuadrado natural de M5 acortado (se recortaba por los dos
  lados).

Capturas reales de M1, M2, M3, M5, M6, M7 (antes y después de dos ensamblajes) y del panel
de Proceso, revisadas.

## Qué se descartó y por qué

- **Incrustar el `SystemView` tal cual en M7, encima del heatmap.** Dos imágenes de K en el
  mismo overlay y ~800 px de alto; el esqueleto bajo el heatmap cuenta la misma historia con
  una sola imagen.
- **Reescribir el heatmap de M7 en `tk.Canvas`** para reusar el widget del panel. Se
  perdían los valores (coolwarm por magnitud, números con n ≤ 16), el toggle *Reducida* y la
  animación de tachado, todo sobre matplotlib.

- **Reescribir el render sobre un rasterizador Pillow único (todo bitmap) o sobre matplotlib.**
  Se perdería el hit-test por ítem de `tk.Canvas` (selección, hover, pan/zoom en C) que hoy
  sostiene seis tests, y matplotlib es un orden de magnitud más lento en interacción. El
  híbrido actual (raster para el campo + vectores para todo lo demás) ya es la arquitectura
  correcta; lo que faltaba era una pila de capas explícita y lentes por fase.
- **Un stepper de fases que reemplace al `Notebook` Pre/Proc/Post.** Las tres fases son el
  vocabulario de la tesis y de las reglas, y `notebook.select/index` está por todos lados
  (F5, salud, tests). La tira del método vive **dentro** de la fase que le corresponde.
- **Chips con conteos en el banner de Pre** (`9 nodos · 4 elem · 3 restr…`). Duplicaban las
  sub-pestañas que están justo debajo. El subtítulo pasó a ser el orden del método y los
  conteos van a la barra de estado.
- **Dos breadcrumbs** (el de la barra de estado y la tira). Una sola vía: la tira. El de la
  barra aparecía recién al abrir el primer módulo y sus glifos no decían qué eran.
- **Reacciones con la cola en el nodo** (flecha que "sale"). Se probó y se capturó: los
  rótulos caían sobre los del valor nodal y sobre la colorbar. Con la punta en el nodo y la
  cola afuera, el rótulo queda en zona libre y comparte gramática con las cargas.
- **Rótulos de la cuadrícula en el borde del viewport** (estilo plot). Con tags `screen` se
  desincronizan durante el pan hasta el redraw; con `world` se van del viewport junto con la
  línea. Se eligió rotular sobre los ejes del mundo (la cuadrícula ES el sistema de
  coordenadas); el readout del cursor cubre el caso del origen fuera de pantalla.
- **Índices de GDL siempre visibles.** Duplican el texto de cada nodo: en Cook 8×8 a zoom
  medio saturaban aunque la numeración se leyera. Van gateados por arista media en pantalla
  (`DOF_TAGS_MIN_EDGE_PX`) salvo en mallas didácticas.
- **Sobrescribir `on_hover_element` para la vista del sistema.** M0 y M7 lo toman y
  restauran; un tercer usuario lo pisaría. Se agregó una lista de listeners.

## Trampas encontradas

- `pack_propagate(False)` en el banner recorta un subtítulo largo **por los dos lados**
  (queda centrado y cortado): el subtítulo de Pre tiene que caber en ~270 px.
- Los rectángulos de realce de la vista del sistema con bloques de < 3 px son ruido: por
  debajo se marca el rango de filas/columnas que el elemento toca.
- `winfo_ismapped()` es `False` para todo con `root.withdraw()`: el listener de redraw marca
  la vista como sucia y la regenera `refresh()` de la pestaña (el mismo camino que al entrar
  a Proceso). El test lo contempla.
- El mensaje de fase del Post en la barra de estado lo pisan enseguida el `✓ Resuelto` y el
  aviso de la sonda; por eso la cadena `u → ε → σ → R` vive en el subtítulo del banner.

## Qué quedó pendiente

- **Validación visual del autor** (guion en [../rutina/BACKLOG.md](../rutina/BACKLOG.md),
  *Pendientes visuales*, primer ítem). Las capturas de esta sesión (PrintWindow, ejemplo
  canónico y Cook Q9) se miraron y se corrigieron cinco cosas, pero el juicio estético es
  del autor.
- Dos decisiones: si los visitados de la tira se limpian con *Nuevo Proyecto*
  (`MethodStrip.reset_visited()` existe; hoy sobreviven, como el ✓ del panel) y si la capa de
  GDL debe quedar prendida en Pre por default (hoy solo Proceso; el menú del título la
  prende).
- Regenerar las capturas de la tesis (`tesis/figuras/gui_capture.py`) cuando el rediseño esté
  validado: ítem [14] del BACKLOG.

## Verificación

`python -m tests.run_gates --con-gui`: **verde** — 100 módulos importan, 0 nombres sin definir,
0 hex fuera de `config/`, 28 tests OK (incluidos los nuevos `test_canvas_lens`, 90 checks sin
display, y `test_canvas_lens_gui`, Tk real). Capturas reales de la GUI con PrintWindow
(ventana 1366×740) en las tres fases con el ejemplo canónico y en Proceso con Cook Q9 8×8 a dos
zooms: se revisaron y se corrigieron el subtítulo recortado del Pre, la última línea truncada
de la vista del sistema, los rótulos de reacción encimados, la saturación de índices de GDL a
zoom medio y el tamaño de los discos de numeración local al acercar. Sin commit.
