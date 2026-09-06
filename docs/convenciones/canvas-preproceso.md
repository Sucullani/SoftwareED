# Canvas y spreadsheet de Pre-Proceso

> Capitulo del canon de EduFEM. Indice: [../../CLAUDE.md](../../CLAUDE.md) - mapa del repo: [../MAPA.md](../MAPA.md) - prohibiciones: [no-reintroducir.md](no-reintroducir.md).

**Leelo antes de tocar** `gui/preprocessing/` (`pre_tab.py`, `mesh_canvas.py`, `canvas_logic.py`) o `gui/postprocessing/`.

---

## Spreadsheet de Pre-Proceso ([gui/preprocessing/pre_tab.py](../../gui/preprocessing/pre_tab.py))

5 tablas (`Nodos`, `Elementos`, `Cargas`, `Restricciones`, `Carg. Superf.`) en `ttk.Notebook`. Helpers en [_table_helpers.py](../../gui/preprocessing/_table_helpers.py).

**Tabla de Elementos siempre muestra N1..N4** (incluso en Q9). Los nodos 5..9 se generan automáticamente — **no añadir columnas N5..N9 ni edición manual**.

### Interacción minimalista

Solo 3 atajos en tablas:
- `Delete` / `Supr` → eliminar fila
- `Ctrl+C` → copiar TSV
- `Ctrl+V` → pegar TSV

**No reintroducir**: Insert, F2, Ctrl+G/R/M/L/U/I/Shift+D/D, hint `<FocusIn>`, menú contextual.

**Edición de celda**: solo doble-click. `start_cell_editor` bindea Return/KP_Enter/FocusOut → commit, Escape → cancel. Sin Tab/Shift-Tab/arrow keys (`on_commit(text)` recibe un solo argumento).

**Cambio de ID**: doble-click en columna ID dispara cascade rename atómico (`change_node_id` / `change_element_id` / `rename_material`) que valida unicidad y propaga a `nodal_loads`, `boundary_conditions`, `element.node_ids`, `surface_loads`.

**Material como dropdown**: celda muestra `Material ▾` (`GLYPH_DROPDOWN`). Doble-click abre `start_combobox_editor` (Toplevel + Listbox custom — **NO** `ttk.Combobox`, su popup se clipea con tema oscuro). El `▾` se quita en `_copy_element_row` para que paste roundtrip funcione.

**Placeholder**: última fila con `iid=PLACEHOLDER_IID = "__new__"`, hint en gris. Doble-click crea registro con defaults. Si navega sin completar, lock se libera silenciosamente con hint en status bar.

**Restricciones — dispatch por columna en doble-click**:
- ci=0 (Nodo) → editor del Nodo (cambia el BC a otro nodo libre).
- ci=1 (X) → toggle `restrain_x` con captura undo.
- ci=2 (Y) → toggle `restrain_y` con captura undo.

No hay toggle por single-click (eliminado para unificar UX: doble-click es la única vía de edición en todas las tablas).

**Q9 mid/center read-only**: si el rol del nodo es `mid` o `center`, **ninguna celda** abre editor (ID, X, Y todas bloqueadas). Estos nodos se recalculan automáticamente al mover vértices macro.

### Sync bidireccional spreadsheet ↔ canvas (con multi-select)

**Modelo unificado de selección**: `MeshCanvas` mantiene sets `selected_nodes`, `selected_elements`, `selected_edges` (aristas potenciales como `frozenset({n1, n2})`), `selected_loads`, `selected_constraints`, `selected_surfaces`. Los atributos legacy `highlighted_*` (singular) se sincronizan: contienen el único elemento del set si `len(set) == 1`, sino `None`. **No setear `highlighted_*` directo** — usar `select_*`/`replace_*_selection`.

**API de selección**:
- `canvas.select_node(nid, *, additive=False, range_to=False)` — replace, Ctrl+toggle, Shift+range
- `canvas.select_element(eid, *, additive)`, `select_edge(frozenset, *, additive)`, `select_load(nid, ...)`, `select_constraint(nid, ...)`, `select_surface(idx, ...)`
- `canvas.replace_node_selection(set)` / `replace_element_selection(set)` — sync desde spreadsheet
- `canvas.clear_highlights()` — limpia todo (compat retrocompat con el método existente)
- `canvas.get_selection() → dict` — copia de los 6 sets
- `canvas.on_selection_changed = callable(dict)` — dispara en cada cambio

**Click en canvas con modifiers**: click normal reemplaza; **Ctrl+Click** toggle (additive); **Shift+Click** range (solo nodos, ordenados por ID). El bit-mask del `event.state` se decodifica en `_on_click` (`0x0004=Ctrl`, `0x0001=Shift`).

**Second-click deselecciona**: click normal sobre un ítem que YA es el único en su set deselecciona TODO. Si el set tenía >1 ítem, click normal hace collapse (deja solo el clickeado); un segundo click sobre el mismo lo deselecciona. Patrón estándar de file explorers. Implementado en cada `select_*` con flag `was_only = (selected_X == {item})`.

**Click en zona vacía del canvas**: click normal deselecciona todo (`clear_highlights()`). **Ctrl+Click y Shift+Click en vacío preservan** la selección — el modificador implica intent aditivo, sería destructivo borrar lo acumulado solo porque el target falló. **`Esc` global** también deselecciona y además gestiona modo dibujo y cell editor en cascada (`MainWindow._on_escape_global`: modo dibujo > entry abierto > clear selection). El handler global ignora si hay focus en `Entry`/`Combobox` (deja que el widget maneje su propia Esc).

**Treeviews en `selectmode="extended"`**: `tree.selection()` retorna lista de iids. Multi-select con Ctrl+Click / Shift+Click nativo de Tk. Los handlers `_on_*_select` propagan al canvas vía `replace_*_selection` con loop-guard (`_syncing_to_canvas` / `_syncing_from_canvas` flags).

**Sync asimétrico spreadsheet ↔ canvas (vía tag visual)**: ambas direcciones funcionan, pero por mecanismos distintos:
- **Spreadsheet → canvas**: el handler `_on_*_select` llama `replace_*_selection(set)` en el canvas (síncrono, no rebota).
- **Canvas → spreadsheet**: el callback `_on_canvas_selection_changed` reconstruye los 5 trees y aplica el **tag visual `canvas_selected`** (background amarillo oscuro `CANVAS_SELECTED_ROW_BG`) a las filas cuyo id está en `canvas.selected_*`. Auto-scroll a la primera fila marcada via `tree.see(first_iid)`. **NO usa `tree.selection_set`** — eso disparaba el virtualevent `<<TreeviewSelect>>` async sin guard, generando degradación que congelaba la GUI bajo selecciones repetidas.

**Prioridad de tags en ttk.Treeview = orden de `tag_configure`** (primero-configurado gana, NO la posición en la tupla del item — verificado empíricamente). `canvas_selected` se configura **primero** en `_configure_row_tags` para que su background amarillo (`CANVAS_SELECTED_ROW_BG`, mismo hex que `CANVAS_SELECTED_COLOR`) gane sobre `orphan_node`/`pending_pick`/`placeholder`. Define background **y** foreground (`CANVAS_SELECTED_ROW_FG = #000000`): la selección gana sobre orphan/auto cuando coexisten. **No reintroducir** `tree.selection_set` desde el callback — usar tags visuales para todo sync canvas → spreadsheet.

**Highlight cromáticamente unificado**: la selección nativa de ttk (`style.map("Treeview", background=[("selected", ...)])`) usa el MISMO `CANVAS_SELECTED_ROW_BG` que el tag `canvas_selected`. Una sola identidad visual de "fila resaltada", venga del canvas o de la propia tabla. **No reintroducir** azul `#1f6feb` para selected — fragmenta el lenguaje cromático.

**Click en canvas**: hit-test prioriza por sub-pestaña activa. En *Carg. Superf.*, las aristas potenciales (corner-to-corner) se priorizan sobre nodos para que el click en una arista sin surface pre-llene una fantasma. En otras sub-pestañas, mantiene el orden histórico (load > constraint > surface > node > element).

iids: nodos/cargas/restricciones = `str(node_id)`, elementos = `str(elem_id)`, surface_loads = `str(idx)`. **iids fantasma**: `__ghost__N` (cargas/restricciones) o `__ghost__N1_N2` (surface). Los handlers excluyen iids ghost del flujo de selección normal.

### Delete bidireccional desde canvas

Canvas con `takefocus=1` y `<Enter>` → `focus_set()`. Teclas `Delete` / `BackSpace` borran el item highlighted (mismo orden que hit-test). `on_canvas_delete(kind, target_id)` callback refresca todas las tablas.

Confirmación:
- **Carga / restricción / surface load**: borrado directo, sin modal.
- **Elemento**: modal `askyesno` con preview (`_preview_element_cleanup` calcula sin mutar) — cuántos nodos auto-eliminar vs preservar. Tras aceptar, `remove_element` ejecuta el cleanup en cascada.
- **Nodo huérfano sin datos**: borrado directo.
- **Nodo huérfano con cargas/BCs/surface**: modal de confirmación (al borrar se pierden esos datos).
- **Nodo en uno o más elementos**: modal `askyesno` con preview (`preview_node_cascade` calcula sin mutar) — cuántos elementos eliminar, cuántos nodos auxiliares borrar, cuántos preservar como huérfanos. Tras aceptar, `remove_node_with_cascade` ejecuta el cascade simétrico al de elementos. **No hay jerarquía** — el usuario no necesita borrar el elemento primero.

**Multi-select unificado**: cuando hay >1 ítem seleccionado de un tipo, `Delete` borra todos en el orden de prioridad del hit-test (con confirmación modal por tipo). Spreadsheet también soporta multi-select para borrado masivo (ya con `selectmode="extended"`).

### Filas fantasma de pick desde canvas

Cuando el usuario selecciona algo en el canvas (uno o varios nodos / aristas), las sub-pestañas relevantes del spreadsheet muestran **filas fantasma** (azul desaturado, tag `pending_pick`) arriba del placeholder gris, una por cada ítem seleccionado que NO tiene aún el item correspondiente en el modelo:

| Sub-pestaña activa | Trigger | Fantasma muestra | Defaults al confirmar |
|---|---|---|---|
| Cargas | `selected_nodes` sin carga existente | `📍 N{id} \| 0 \| 0` | `NodalLoad(nid, Fx=0, Fy=0)` |
| Restricciones | `selected_nodes` sin BC existente | `📍 N{id} \| ✔ \| ✔` | `BC(nid, restrain_x=True, restrain_y=True)` (empotramiento) |
| Carg. Superf. | `selected_edges` sin surface existente | `📍 {n1} \| {n2} \| 0 \| 0 \| 0` | `SurfaceLoad(n1, n2, q=0, q=0, angle=0)` |

**Confirmación**: **single-click** sobre cualquier celda de la fila fantasma confirma (crea el ítem con defaults). El usuario edita los valores después con doble-click (igual que cualquier otra fila). Esto es distinto del placeholder gris que requiere doble-click — diseño deliberado: la fantasma viene con datos parciales pre-cargados, el single-click es comodidad.

**No hay "Aceptar todas con defaults"** (descartado): crear N items con valores nulos no resuelve el caso de uso real ("aplicar misma magnitud a varios nodos"). El usuario igual tiene que editar uno por uno después. Para creación masiva con valor real, paste TSV en el spreadsheet sigue siendo el camino. **No reintroducir** el botón.

**Reactividad**: `MeshCanvas.on_selection_changed` callback dispara `pre_tab._on_canvas_selection_changed()` que reconstruye los 3 trees (loads/constraints/surface) y refresca los action bars. Las filas fantasma persisten al cambiar de sub-pestaña — la nueva sub-pestaña ya muestra las suyas derivadas del mismo `selected_*` del canvas.

**Limpieza**: `Esc` (sin focus en Entry) → `clear_highlights()` → callback dispara → todas las fantasmas desaparecen. Tras un undo/redo, `_on_state_restored` sanea los sets quitando IDs muertos.

**Hit-test de arista potencial** (`mesh_canvas._hit_test_potential_edge`): itera todas las aristas corner-to-corner de los elementos (deduplicadas por `frozenset`), distancia point-to-segment con `tol_px=10`, mid/center Q9 excluidos. Solo se activa cuando la sub-pestaña *Carg. Superf.* está activa (decisión: en otras sub-pestañas el click en arista confunde).

### Modo dibujo de elementos (canvas-driven, estilo AutoCAD)

Botón `🖊 Dibujar elemento (D)` en el banner superior de la sub-pestaña **Elementos** del pre_tab. Atajo global `D` (cuando ningún Entry/Combobox tiene focus). Al activarse: cursor `crosshair`, status bar persistente `"Modo dibujo: vertice N/4 — click en canvas o sobre nodo (snap). Esc cancela."`.

**Flujo**:
- **Click en zona vacía**: emerge un `Toplevel` borderless junto al cursor con dos `Entry` pre-llenados (`X`, `Y`) usando la coord del cursor. `Tab` navega X↔Y, `Enter` confirma, `Esc` cancela ese punto (no el modo).
- **Click sobre nodo corner existente** (dentro de `draw_snap_radius_px = 10`): snap implícito, NO emerge Entry, ese vertice reusa el nodo (no se duplica). Hover sobre el snap muestra anillo amarillo grueso. Solo snap a corners — mid/center Q9 quedan excluidos via `classify_nodes`.
- **Render preview**: nodos pendientes con número 1..4 en círculo amarillo, polígono parcial en línea punteada, línea preview del último vertice al cursor (y al primero cuando hay 3 puntos para mostrar el cierre tentativo del quad).
- **Al 4to click**: commit atómico — auto-CCW (si `_shoelace_signed < 0`, revierte el orden), crea nodos faltantes con `add_node`, crea elemento con `add_element`, dispara `auto_expand_if_q9`. **1 snapshot undo** por elemento. Modo persiste para crear el siguiente.
- **`Esc` con elemento parcial**: descarta puntos pendientes, modo sigue activo. **`Esc` sin nada pendiente**: desactiva el modo.

**Pre-flight de material** ([pre_tab._on_toggle_draw_mode](../../gui/preprocessing/pre_tab.py)): si `project.materials` está vacío al activar, abre `MaterialDialog` antes (mismo patrón que el placeholder de la tabla Elementos). Sin material → no entra al modo. El elemento creado usa `materials[0]` y `default_thickness`, editables después en el spreadsheet.

**Callbacks de sincronización** (`_wire_canvas_callbacks`):
- `canvas.on_draw_mode_changed = pre_tab._on_canvas_draw_mode_changed`: sincroniza el `bootstyle` del botón (`info-outline` → `info` cuando activo).
- `canvas.on_draw_element_created = pre_tab._on_canvas_draw_element_created`: refresca tablas Nodos + Elementos + título tras el commit.

**Auto-desactivación**: cambiar a Proc/Post o un undo/redo (vía `_on_state_restored`) desactiva el modo automáticamente — los puntos pendientes podrían referenciar nodos que ya no existen tras el restore.

**Lógica testeable**: `MeshCanvas._shoelace_signed(pts)` es `staticmethod` — los tests en [test_draw_mode.py](../../tests/test_draw_mode.py) reproducen el commit sin Tk usando solo `ProjectModel` + `auto_expand_if_q9`.

### Estilo Treeview

Fondo plano uniforme `ROW_BG = #1c1e22` — el zebra striping fue retirado: con 4 estados semánticos (`canvas_selected` amarillo, `orphan_node` naranja, `pending_pick` azul, `placeholder` gris) ya hay suficiente carga cromática; agregar zebra competía con ellos. **No reintroducir** `even`/`odd`. Bordes pixel-perfect no son posibles en `ttk.Treeview`. **No migrar a `tksheet`** (descartado).

`_apply_global_tree_style`: `rowheight = font.metrics("linespace") + 6`, layout con `sticky=""` en `Treeitem.text`, heading `relief="raised" padding=(8,4) anchor="center"`, body `relief="flat"`.

Tags estándar en `_configure_row_tags`:
- `placeholder`: gris desaturado para "+ doble-click..."
- `auto_node`: foreground gris (`AUTO_NODE_FG`) — Q9 mid/center read-only
- `orphan_node`: foreground naranja (`ORPHAN_NODE_FG`) + background tintado (`ORPHAN_NODE_BG`) — nodos huérfanos preservados

### Render del canvas

**Visualización progresiva (LOD por zoom) + numeración bajo demanda** (auditoría UX 2026-05, [auditoría UX del canvas](../auditorias/historico/2026-05-30_auditoria_canvas_ux.md)). La política de visibilidad ya NO es "todo encendido, siempre" — el canvas decide *cuánto* dibujar según la escala y la selección. Lógica pura testeable headless en [gui/preprocessing/canvas_logic.py](../../gui/preprocessing/canvas_logic.py) (`lod_level`, `bbox_visible`, `label_visible_for_item`) + helpers de modelo en `models/mesh_utils.py` (`median_edge_length`, `boundary_edges`, `focus_keep_sets`). Tests: [tests/test_canvas_visualization.py](../../tests/test_canvas_visualization.py).

- **LOD por `edge_px`** (= `median_edge_length(project) * scale`, ver `_lod_level`): `far` (< `LOD_EDGE_PX_FAR`=14) dibuja **solo la silueta** del dominio + el item seleccionado, sin nodos mid/center ni labels; `mid` (< `LOD_EDGE_PX_NEAR`=55) aristas + corners + mid/center como punto simple, labels solo en el seleccionado; `near` todo + numeración automática. **Mallas ≤ `LOD_MIN_ELEMENTS_FOR_GATING`=12 elementos quedan SIEMPRE en `near`** (preserva la experiencia del ejemplo canónico — el gating solo entra cuando la malla es densa). **No reintroducir** la numeración global incondicional ni los flags `show_node_labels`/`show_elem_labels` (eliminados; reemplazados por `node_label_mode`/`elem_label_mode` ∈ `{"auto","always","never"}`).
- **Numeración bajo demanda**: modo por categoría (`set_node_label_mode`/`set_elem_label_mode`, default `"auto"`) + **realce por selección** (el item seleccionado muestra su id a cualquier zoom — patrón "query" de Abaqus) + **hover** (el elemento bajo el cursor muestra su outline cian `CANVAS_HOVER_COLOR` + número aunque la numeración global esté apagada). Control manual desde el **menú del título del viewport** (`📐/⚙/📊 Modelo MEF ▾`, patrón Rhino — el título ES el menú; lo construye `_build_view_menu`): un único checkbutton **`Números (nodos y elementos)`** (marcado → `auto`, desmarcado → `never`, vía `_set_labels_visible`) en lugar del ex submenú `Numeración ▸` con modos auto/siempre/nunca por categoría — ver el bullet "Barra del viewport + menú de capas" abajo.
- **Realce de selección (rediseño 2026-05, pedido del usuario "color suave de relleno que no cubra datos; el borde grueso molesta")**:
  - **Elementos**: SOLO un `create_polygon(fill=CANVAS_SELECTED_FILL_COLOR, stipple="gray12", outline="")` (relleno punteado que llena el área pero deja asomar la malla/los datos — `tk.Canvas` NO soporta alpha vectorial → se simula con `stipple`) + el outline propio del elemento en color de selección (`line_w=2.0`, antes 2.5). **El halo grueso del elemento fue ELIMINADO** (2026-05-31, pedido del usuario). El relleno es la señal primaria (estilo Abaqus/ANSYS) y cubre área suficiente para no perderse en mallas grandes (hallazgo I1 — el relleno reemplaza la función del halo).
  - **Nodos/aristas**: conservan un **anillo claro fino DEBAJO** (`CANVAS_SELECTED_HALO_COLOR`) — nodo `width=1.5`, arista halo `6` / línea `2.5` (afinados respecto del original 2 / 8 / 4). `_draw_highlight()` dibuja las aristas potenciales. Las anchuras escalan con `_decoration_factor()`.
  - **No reintroducir** el halo grueso del elemento (`line_w+2.5/+4`, era "muy fuerte"), ni eliminar el relleno punteado (es lo que evita perder la selección en mallas grandes, hallazgo I1).
- **Focus-and-context** (`focus_mode` ∈ `{"auto","on","off"}`, `_focus_active`/`_focus_keep`): al seleccionar en mallas grandes (≥ `CANVAS_FOCUS_MIN_ELEMENTS`=60, o forzado con `"on"`), el contexto NO seleccionado se **atenúa** a `CANVAS_GHOST_COLOR` (reusa la maquinaria `ghost_geometry`) — la selección + su anillo de vecinos quedan nítidos y destacan por contraste. En `"auto"` no afecta mallas chicas.
- **Silueta del dominio** (`boundary_emphasis`, default on): las aristas de contorno (`boundary_edges`, las que pertenecen a un solo elemento) se realzan en `CANVAS_BOUNDARY_COLOR` sobre las internas. Solo desde `CANVAS_BOUNDARY_MIN_ELEMENTS`=12.
- **Culling por viewport**: los items cuyo bbox cae fuera del viewport + margen (`_CULL_MARGIN_FRAC` = padding del gradient) no se crean — recorta el árbol Tk en mallas grandes (la principal palanca de rendimiento). Deshabilitado si el canvas aún no tiene tamaño (`winfo<=1`).
- **Barra del viewport + menú de capas (reformulada 2026-05)**: minimalista y consciente de la fase. La barra es solo el **título-menú** `Modelo MEF ▾` (izq, patrón Rhino — el título ES el menú) + el readout de coords (der, `TEXT_MUTED_FG`, no hex). El glifo del título indica la fase activa (`set_phase("pre"|"proc"|"post")` desde `MainWindow._on_tab_changed`: 📐/⚙/📊). El menú del título es un **panel de capas (visibilidad)** que arma `_build_view_menu`: `🧹 Vista limpia (solo malla)` (aísla la geometría en un click — esconde Números/Cargas/Restricciones/Cuadrícula y restaura al desmarcar, vía `_toggle_clean_view` + snapshot `_clean_view_prev`) · checkbuttons **`Números`** (nodos+elementos, `auto`↔`never`) · **`🔵 Nodos`** (`show_nodes`) · **`🟧 Cargas`** (`show_loads`, cubre nodales+superficiales) · **`🔺 Restricciones`** (`show_constraints`) · **`Cuadrícula`** (`show_grid`) · y por último **`Ajustar vista`** (encuadre, accel. `F`). Helpers: `_set_layer(attr,value)` (setea el flag + sale de Vista limpia + redraw), `_set_labels_visible`, `_sync_layer_vars`. Los glifos 🔵🟧🔺 son pistas-leyenda del color del símbolo en el canvas. `show_loads`/`show_constraints` ya existían y condicionaban el `redraw`; se sumaron `show_nodes`/`show_grid` (guards en `redraw`). **`Elementos` NO es toggleable** a propósito (ocultar la malla deja nodos/cargas flotando). **Eliminados del menú/barra**: `Limpiar Resultados` (botón) — redundante con la navegación (Pre/Proc ya invoca `clear_results_overlay()`; se borró el wrapper `clear_results` y sus 2 callers `Nuevo`/`Cargar Ejemplo` usan `clear_results_overlay()` directo); `Ajustar` como **botón** (ahora vive dentro del menú); y los toggles `Atenuar contexto al seleccionar` y `Resaltar silueta del borde` — solo gatillan en mallas grandes (≥60 / ≥12 elementos) → invisibles en modelos didácticos, quedan en automático interno (`focus_mode="auto"` / `boundary_emphasis=True`; sus setters/atributos siguen como API). **No reintroducir**: el botón `Limpiar Resultados`, el método `clear_results`, el menubutton "Vista" separado, el botón `Ajustar` en la barra (vive en el menú), los toggles de foco/silueta en el menú, un toggle de `Elementos`, ni controles de resultado (deformada/escala, VM·σx·σy·τxy, isolíneas, 🧊 3D) en esta barra — **viven en el panel del Post** ([post_tab.py](../../gui/postprocessing/post_tab.py), regla "una sola vía"). El **clic derecho NO hostea menús de visualización**: hace pan (drag, en las 3 fases — redundante con el botón central para mouses sin rueda-click) y en Post abre el `DetailsPanel` del probe (`probe_overlay._on_right_click`); overloadearlo rompería el pan y chocaría con el probe.

**Colormap de resultados** (**jet para TODO desde 2026-05-31**): el canvas usa **jet** (`config/colormaps.py`, LUTs en numpy puro sin matplotlib). `set_result_values`/`set_element_result_grid` eligen el LUT via `_select_colormap`: **jet** (arcoíris clásico ANSYS/SAP2000) para **todo** — magnitudes no negativas (VM, |u|) Y campos con signo (σx/σy/τxy/Ux/Uy). Los campos con signo se re-centran `vmin/vmax` simétricamente (verde = cero, azul = compresión, rojo = tracción; `is_diverging_range` usa umbral **relativo** — VM con ruido numérico negativo NO se re-centra). **Jet reemplazó a turbo Y a coolwarm** (pedido del usuario "cambia todo a JET" — un solo arcoíris para todos los campos, como ANSYS). Jet NO es perceptualmente uniforme — la ex-regla "no jet" queda **sobrescrita por decisión del usuario** (documentada en `config/colormaps.py`). `coolwarm`, `turbo` y `viridis` se conservan definidos pero ya NO se usan en los campos de resultado (`coolwarm`/`turbo` sin uso ahí; `viridis`/`coolwarm` solo en superficies pedagógicas de módulos educativos como M2). El rasterizador vectorizado (`gui/preprocessing/canvas_raster.py`, sin Tk ni JIT; paridad píxel a píxel con `tests/test_canvas_raster.py`) indexa el LUT. **La vista 3D del Post** ([gui/postprocessing/surface_3d_viewer.py](../../gui/postprocessing/surface_3d_viewer.py)) **y la Memoria de Cálculo** ([file_io/figure_export.py](../../file_io/figure_export.py)) siguen al canvas con el MISMO jet — coherencia cromática 2D↔3D↔PDF. Desde el 2026-09-06 la memoria además comparte el **kernel**: `figure_export._fill_field` llama a `canvas_raster.rasterize_triangles` (mismo orden de triángulos, 0 píxeles distintos; el test lo cubre en `test_figure_export_field`). Es la única dependencia de `file_io/` hacia `gui/`, y es deliberada: `canvas_raster.py` es NumPy puro sin Tk y duplicar el rasterizador sería peor. La **colorbar** (`_draw_colorbar`) muestra la unidad del sistema activo entre corchetes (`Von Mises [Pa]`, vía `result_unit` que `post_tab` pasa a los setters) y formatea los ticks con notación científica para magnitudes grandes/chicas (`_fmt_colorbar_value`: `2.5e7` en vez de `25000000.00`).

**Sin selección de elementos en Post-Proceso** (decisión 2026-05-31, pedido del usuario): en la fase Post la inspección del campo es por **probe** (puntual, su propio handler `add="+"` pinea) y **contorno** — NUNCA por selección de elemento. `_on_click` retorna temprano si `self._phase == "post"` (vale con el probe activo o no); el hover también se inhibe (`_hover_enabled`). Al entrar a Post, `MainWindow._on_tab_changed` llama `clear_highlights()` para borrar cualquier selección arrastrada desde Pre/Proc — su relleno punteado taparía el contorno (interferencia que reportó el usuario). **No reintroducir** selección de elementos en Post (no tiene target de edición ahí y su realce compite con el colormap).

**El probe SIGUE la malla deformada** (decisión 2026-05-31, pedido del usuario; **revierte** la ex-convención "Lagrangiano total / coords originales"): cuando `show_deformed` está activa, los marcadores del probe (puntos Gauss, anillo de snap, pin) se dibujan sobre la malla DEFORMADA y los hit-tests enganchan ahí — antes flotaban sobre la geometría sin deformar. En [probe_overlay.py](../../gui/postprocessing/probe_overlay.py): `_node_screen(nid)` delega en `MeshCanvas._get_node_screen_pos` (ya aplica `deform_scale·u`); `_natural_screen(elem,ξ,η,…)` interpola las coords deformadas vía `N(ξ,η)`; `_elem_coords_current` hace lo propio para el **inverse-map del hover libre** (`screen_to_world` da la posición en la malla deformada, así que `inverse_iso_map_NR` corre sobre coords deformadas → `(ξ,η)` del punto material correcto). Los **valores no cambian** — el esfuerzo se computa en config de referencia (`compute_raw`/`compute_smooth` con el mismo `(ξ,η)`); solo cambia DÓNDE se dibuja/engancha el marcador. **No reintroducir** el probe sobre coords sin deformar cuando la malla está deformada (los marcadores quedaban descolgados de la malla visible).

**"(promedio)" solo si el nodo es compartido** (`_show_node_tooltip`, 2026-05-31): el tooltip de esfuerzo nodal suavizado rotula `(promedio)` **solo** cuando el nodo pertenece a > 1 elemento; si está en un único elemento, el valor nodal ES el del elemento (no hay promediado entre vecinos) → sin sufijo. Cuenta `sum(1 for e in elements if nid in e.node_ids)`.

**Q4↔Q9 re-resuelve el Post automáticamente** (`ElementTypeDialog._on_accept`, 2026-05-31): tras cambiar el tipo de elemento (que invalida `is_solved`), si el usuario está en la pestaña Post-Proceso (`notebook.index(select()) == 2`) se llama `post_tab.auto_solve()` — re-resuelve con la malla nueva (K, u, σ cambian) y repinta. Sin esto el Post quedaba en blanco hasta navegar a otra pestaña y volver. `auto_solve` re-resuelve porque `is_solved` acaba de ponerse en `False`.

**Símbolos de restricción** (notación estándar, `_draw_constraints`):
- `is_fixed`: triángulo + línea base + 3 hachuras (empotramiento).
- `is_roller_y`: triángulo apoyado en círculo (rodillo) sobre superficie horizontal.
- `is_roller_x`: rotado 90° con pared vertical y rodillo entre ella y el triángulo.

**No** dibujar `is_roller_x` como triángulo lateral sin rodillo (era indistinguible del empotramiento).

**Glow simulado**: 2 `create_line` superpuestas (`width+3` con color `SHADOW_*`, encima la línea principal). Aplicado a `_draw_loads` y `_draw_surface_loads`. Cabeza de flecha unificada y más afilada (proporción ~1:1.4, `arrowshape (10,14,5)` cargas nodales / `(10,13,5)` superficiales — antes `(14,16,7)`/`(11,13,5)`/`(8,10,4)`).

**Reescalado de decoraciones con el zoom** (`_decoration_factor`, pedido del usuario 2026-05): la geometría (coords mundo) ya escala con el zoom; las **decoraciones** (radio de nodo, longitud+cabeza de flecha, tamaño de restricción, anchura de halos) también, vía un **multiplicador proporcional ACOTADO** `factor = clamp(scale/_reference_scale, DECORATION_SCALE_MIN_FACTOR=0.6, DECORATION_SCALE_MAX_FACTOR=2.5)`. `_reference_scale` se fija en cada `fit_view` (factor 1.0 = tamaño base); `None` antes del primer fit → factor 1.0. Se clampa el **FACTOR**, no el px absoluto, para ser uniforme entre glifos de distinta base (nodo 4, flecha 44, restricción 14). Modelo "proporcional acotado" estilo GiD (la mayoría del software FEM mantiene las decoraciones a tamaño de pantalla CONSTANTE; el usuario eligió que crezcan para una sensación más inmersiva en un visor educativo de un solo modelo). **El "snap-back" de 150 ms persiste** pero queda casi imperceptible (el tamaño tras el redraw coincide con el escalado en vivo del `canvas.scale("all")`, salvo en la zona de clamp). **No reintroducir** un clamp en px absoluto (rompe las flechas: base 44 capada a un techo pensado para nodos). Tamaños base de glifo en `config/settings.py` (`CANVAS_NODE_*_RADIUS`) y constantes inline movidas a config (`CANVAS_NODE_INNER_*`, `CANVAS_NODE_OUTLINE`, `CANVAS_CONSTRAINT_*_FILL`) — la auditoría `Grep #[0-9a-fA-F]{3,8}` sobre `gui/preprocessing/mesh_canvas.py` ya no debe encontrar esos 7 hex.

**Labels con fondo**: `_draw_label_with_bg(x, y, text, fg, anchor)` — texto + rectángulo `LABEL_BG` con outline del color del texto. Reusar para labels nuevos.

**Render de nodos Q9** (3 estilos según rol via `classify_nodes`):

| Rol | Color | Radio |
|---|---|---|
| Vértice (corner) | `CANVAS_NODE_COLOR` `#4fc3f7` azul claro | `CANVAS_NODE_RADIUS` (4 px) |
| Medio de arista | `CANVAS_NODE_MID_COLOR` `#6fb8ff` azul | `CANVAS_NODE_MID_RADIUS` (3 px) |
| Centroide (N9) | `CANVAS_NODE_CENTER_COLOR` `#b86fff` violeta | `CANVAS_NODE_MID_RADIUS` (3 px) |

Highlight amarillo aplica igual a los 3. **No** introducir aristas curvas — la GUI prioriza claridad del polígono macro.

**Nodos huérfanos preservados**: tras un cleanup en cascada, los nodos con datos del usuario quedan visibles pero marcados:
- **Canvas**: `_draw_nodes` consulta `classify_orphan_status` y override del color a `CANVAS_NODE_ORPHAN_COLOR` (`#d68545` naranja desaturado). Radio según rol.
- **Tabla de Nodos**: tag `orphan_node` (foreground naranja + background tintado).
- **Tablas de Cargas / Restricciones / Surface Loads**: el mismo tag `orphan_node` se aplica a las filas cuyo nodo asociado está huérfano. Una surface load se marca si CUALQUIERA de los 2 extremos es huérfano.
- **Sin badge textual** — el color comunica el estado.

### Identidad visual por fase

| Fase | Icono | Color | Bootstyle |
|---|---|---|---|
| PRE-PROCESO | 📐 | `PHASE_PRE_COLOR` `#0d6efd` | `info` |
| PROCESO | ⚙ | `PHASE_PROC_COLOR` `#fd7e14` | `warning` |
| POST-PROCESO | 📊 | `PHASE_POST_COLOR` `#198754` | `success` |

Banner con `gui/widgets/phase_banner.py::build_phase_banner`. Pre-Proceso y Proceso tienen su sub-pestaña "🎓 Educación" (la crea `pre_tab` / `proc_tab`); **el Post no la tiene** — no hay módulos educativos en esa fase.
