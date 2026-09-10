# Canvas y spreadsheet de Pre-Proceso

> Capitulo del canon de EduFEM. Indice: [../../CLAUDE.md](../../CLAUDE.md) - mapa del repo: [../MAPA.md](../MAPA.md) - prohibiciones: [no-reintroducir.md](no-reintroducir.md).

**Leelo antes de tocar** `gui/preprocessing/` (`pre_tab.py`, `mesh_canvas.py`, `canvas_logic.py`) o `gui/postprocessing/`.

---

## Spreadsheet de Pre-Proceso ([gui/preprocessing/pre_tab.py](../../gui/preprocessing/pre_tab.py))

5 tablas (`Nodos`, `Elementos`, `Cargas`, `Restricciones`, `Carg. Superf.`) en `ttk.Notebook`. Helpers en [_table_helpers.py](../../gui/preprocessing/_table_helpers.py).

**Tabla de Elementos siempre muestra N1..N4** (incluso en Q9). Los nodos 5..9 se generan automáticamente — **no añadir columnas N5..N9 ni edición manual**.

### Interacción minimalista

Solo 3 atajos en tablas:
- `Delete` / `Supr` → eliminar **la selección completa** (`selectmode="extended"`)
- `Ctrl+C` → copiar TSV
- `Ctrl+V` → pegar TSV

**No reintroducir**: Insert, F2, Ctrl+G/R/M/L/U/I/Shift+D/D, hint `<FocusIn>`, menú contextual.

**Edición de celda**: solo doble-click. `start_cell_editor` bindea Return/KP_Enter/FocusOut → commit, Escape → cancel. Sin Tab/Shift-Tab/arrow keys (`on_commit(text)` recibe un solo argumento).

**Números: `to_float_flex`, no `float()`**, tanto en los `_paste_*` como en los editores de celda (X/Y, espesor, Fx/Fy, q y ángulo). Tipear `1,5` a mano daba "valor inválido" mientras que pegar `1,5` funcionaba: dos vías para lo mismo con reglas distintas. Los errores de celda salen por `_error_numero(texto, campo)` / `_error_nodo_inexistente(nid)`, que nombran la celda, el valor rechazado y el formato aceptado — **no reintroducir** los genéricos `"Valor invalido"` / `"Valor numerico invalido"`, que no decían ni qué celda ni qué se esperaba.

**El paste dice qué descartó y por qué** (`_mensaje_pegado(ok, total, motivos)`): los parsers saltan filas con un `continue` silencioso, así que `"0/5 fila(s) pegada(s)"` dejaba al alumno sin ninguna pista. Cada `continue` etiqueta su motivo (nodo inexistente, valor no numérico, faltan columnas) y el resumen los agrega con `Counter`.

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
- `canvas.prune_dead_selection() → bool` — saca de los 6 sets los ids que ya no existen en el modelo y emite el callback si algo cambió. **Fuente única**: la usan el borrado desde el canvas y `MainWindow._on_state_restored` (antes esa lógica estaba duplicada ahí). Ojo: los índices de `selected_surfaces` son posicionales, así que tras borrar una carga superficial el saneo no alcanza y hay que vaciar el set
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

Canvas con `takefocus=1` y `<Enter>` → `focus_set()`. Teclas `Delete` / `BackSpace` borran **la selección actual**, en el orden de prioridad del hit-test: carga > restricción > superficial > elemento > nodo. Se borra el conjunto completo del primer tipo que tenga algo seleccionado. `on_canvas_delete(kind, target_id)` refresca todas las tablas; `target_id` es el id borrado, o la **lista** de ids si fueron varios (el único consumidor, `pre_tab`, lo ignora y refresca todo).

`_on_delete_key` lee los **sets** `selected_*`, no los espejos `highlighted_*`: estos valen `None` cuando hay más de un ítem, así que leerlos hacía que `Supr` no hiciera nada —ni lo dijera— con multi-selección. **No reintroducir** el despacho por `highlighted_*`.

Cada tipo tiene su helper `_delete_selected_<tipo>()`: filtra los ids que siguen vivos, captura **un solo** snapshot de undo (regla dura 4), muta, llama `prune_dead_selection()` y avisa una vez. Los previews en cascada son los mismos que usa el spreadsheet (`pre_tab._remove_node` / `_remove_element`), para que las dos vías se comporten igual.

Los índices de `selected_surfaces` son **posicionales**: al borrar una carga superficial los posteriores se corren, así que el borrado múltiple va de mayor a menor y el set se **vacía** entero (conservarlo dejaba resaltada una carga distinta de la borrada). Las regresiones están en [test_canvas_delete.py](../../tests/test_canvas_delete.py) (sin display: instancia el canvas con `object.__new__`).

**Sin selección, `Supr` lo dice** en la barra de estado ("Nada seleccionado — clickeá un nodo, elemento…"): una tecla que no hace nada ni explica por qué es un callejón sin salida.

Confirmación:
- **Carga / restricción / surface load**: borrado directo, sin modal.
- **Elemento**: modal `askyesno` con preview (`_preview_element_cleanup` calcula sin mutar) — cuántos nodos auto-eliminar vs preservar. Tras aceptar, `remove_element` ejecuta el cleanup en cascada.
- **Nodo huérfano sin datos**: borrado directo.
- **Nodo huérfano con cargas/BCs/surface**: modal de confirmación (al borrar se pierden esos datos).
- **Nodo en uno o más elementos**: modal `askyesno` con preview (`preview_node_cascade` calcula sin mutar) — cuántos elementos eliminar, cuántos nodos auxiliares borrar, cuántos preservar como huérfanos. Tras aceptar, `remove_node_with_cascade` ejecuta el cascade simétrico al de elementos. **No hay jerarquía** — el usuario no necesita borrar el elemento primero.

**Multi-select unificado**: cuando hay >1 ítem seleccionado de un tipo, `Delete` borra todos en el orden de prioridad del hit-test, con **una** confirmación modal agregada (cuenta de elementos/nodos en cascada) y **un** snapshot de undo. Spreadsheet también soporta multi-select para borrado masivo (ya con `selectmode="extended"`).

### Delete desde el spreadsheet: el mismo cierre que el del lienzo

Los cinco `pre_tab._remove_*` terminan igual que sus pares del canvas, y por el mismo motivo: eran **la misma acción del alumno por dos caminos, comportándose distinto**.

- **`_sync_selection_after_delete(freed_nodes=…, surfaces_shifted=…)`** sanea la selección del canvas. Seleccionar una fila la propaga al canvas (`_on_*_select`), así que **todo** borrado desde una tabla dejaba ids muertos en los seis sets, y de esos sets salen las filas fantasma, el tag `canvas_selected` y el realce del lienzo. Se veía como: una fantasma azul de un nodo que ya no existe (y que al clickearla no hacía nada ni lo decía); la carga/restricción recién borrada **reapareciendo** como fantasma con ceros en su mismo lugar (porque `_on_load_select` mete el nodo en `selected_nodes` para el halo); y en superficiales, el índice posicional viejo resaltando **otra** carga. Delega en `MeshCanvas.prune_dead_selection()` —fuente única— y agrega lo que ese saneo no puede saber: los nodos que siguen vivos pero cuya selección era el reflejo de la fila borrada, y el vaciado de `selected_surfaces`.
- **`_nothing_selected(tabla)`**: `Supr` sin filas seleccionadas lo dice en la barra de estado, igual que en el lienzo. El placeholder y las fantasmas no cuentan como selección.
- **`_update_status_info()` + `_update_title()`**: el badge de salud y el ● de "modificado" se refrescan también por esta vía. Antes solo lo hacía el borrado desde el lienzo (vía `on_canvas_delete`), así que borrar la última restricción desde la tabla dejaba el badge diciendo "✓ Modelo sano".
- **Resumen concreto en la barra de estado**: "Nodo 3 eliminado. 2 elemento(s) en cascada." en vez del viejo `"Nodo(s) eliminado(s)."`, que no distinguía 1 de 30.

Regresiones en [test_pre_tab_delete.py](../../tests/test_pre_tab_delete.py) (sin display: `PreProcessTab` con `object.__new__` y un doble mínimo de Treeview).

**Las filas fantasma salen siempre de `_get_pick_ghost_node_ids` / `_get_pick_ghost_edges`**, que filtran los nodos que ya no existen. `_build_loads_visual_list` y `_build_constraints_visual_list` las recalculaban aparte (`selected_nodes - project_keys`, sin chequear existencia) y por eso podían proponer una fila de un nodo borrado. **No reintroducir** el cálculo paralelo.

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
- **Barra del viewport + menú de capas (reformulada 2026-05)**: minimalista y consciente de la fase. La barra es solo el **título-menú** `Modelo MEF ▾` (izq, patrón Rhino — el título ES el menú) + el readout de coords (der, `TEXT_MUTED_FG`, no hex; desde el 2026-09-09 lleva la **unidad de longitud** del proyecto y el **paso vigente de la cuadrícula**: `x: 7.000  y: 4.000 mm · cuadrícula 1 mm`, vía `_update_coord_readout`). El glifo del título indica la fase activa (`set_phase("pre"|"proc"|"post")` desde `MainWindow._on_tab_changed`: 📐/⚙/📊). El menú del título es un **panel de capas (visibilidad)** que arma `_build_view_menu`: `🧹 Vista limpia (solo malla)` (aísla la geometría en un click — esconde Números/Cargas/Restricciones/Cuadrícula y restaura al desmarcar, vía `_toggle_clean_view` + snapshot `_clean_view_prev`) · checkbuttons **`Números`** (nodos+elementos, `auto`↔`never`) · **`🔵 Nodos`** (`show_nodes`) · **`🟧 Cargas`** (`show_loads`, cubre nodales+superficiales) · **`🔺 Restricciones`** (`show_constraints`) · **`Cuadrícula`** (`show_grid`) · **`GDL (índices en K·u = F)`** (`show_dofs`, la capa de la lente del sistema — ver *Lentes por fase*; Proceso la enciende sola en `set_phase`, acá se prende en cualquier fase) · y por último **`Ajustar vista`** (encuadre, accel. `F`). Helpers: `_set_layer(attr,value)` (setea el flag + sale de Vista limpia + redraw), `_set_labels_visible`, `_sync_layer_vars`. Los glifos 🔵🟧🔺 son pistas-leyenda del color del símbolo en el canvas. `show_loads`/`show_constraints` ya existían y condicionaban el `redraw`; se sumaron `show_nodes`/`show_grid` (guards en `redraw`). **`Elementos` NO es toggleable** a propósito (ocultar la malla deja nodos/cargas flotando). **Eliminados del menú/barra**: `Limpiar Resultados` (botón) — redundante con la navegación (Pre/Proc ya invoca `clear_results_overlay()`; se borró el wrapper `clear_results` y sus 2 callers `Nuevo`/`Cargar Ejemplo` usan `clear_results_overlay()` directo); `Ajustar` como **botón** (ahora vive dentro del menú); y los toggles `Atenuar contexto al seleccionar` y `Resaltar silueta del borde` — solo gatillan en mallas grandes (≥60 / ≥12 elementos) → invisibles en modelos didácticos, quedan en automático interno (`focus_mode="auto"` / `boundary_emphasis=True`; sus setters/atributos siguen como API). **No reintroducir**: el botón `Limpiar Resultados`, el método `clear_results`, el menubutton "Vista" separado, el botón `Ajustar` en la barra (vive en el menú), los toggles de foco/silueta en el menú, un toggle de `Elementos`, ni controles de resultado (deformada/escala, VM·σx·σy·τxy, isolíneas, 🧊 3D) en esta barra — **viven en el panel del Post** ([post_tab.py](../../gui/postprocessing/post_tab.py), regla "una sola vía"). El **clic derecho NO hostea menús de visualización**: hace pan (drag, en las 3 fases — redundante con el botón central para mouses sin rueda-click) y en Post abre el `DetailsPanel` del probe (`probe_overlay._on_right_click`); overloadearlo rompería el pan y chocaría con el probe.

**Colormap de resultados** (**jet para TODO desde 2026-05-31**): el canvas usa **jet** (`config/colormaps.py`, LUTs en numpy puro sin matplotlib). `set_result_values`/`set_element_result_grid` eligen el LUT via `_select_colormap`: **jet** (arcoíris clásico ANSYS/SAP2000) para **todo** — magnitudes no negativas (VM, |u|) Y campos con signo (σx/σy/τxy/Ux/Uy). Los campos con signo se re-centran `vmin/vmax` simétricamente (verde = cero, azul = compresión, rojo = tracción; `is_diverging_range` usa umbral **relativo** — VM con ruido numérico negativo NO se re-centra). **Jet reemplazó a turbo Y a coolwarm** (pedido del usuario "cambia todo a JET" — un solo arcoíris para todos los campos, como ANSYS). Jet NO es perceptualmente uniforme — la ex-regla "no jet" queda **sobrescrita por decisión del usuario** (documentada en `config/colormaps.py`). `coolwarm`, `turbo` y `viridis` se conservan definidos pero ya NO se usan en los campos de resultado (`coolwarm`/`turbo` sin uso ahí; `viridis`/`coolwarm` solo en superficies pedagógicas de módulos educativos como M2). El rasterizador vectorizado (`gui/preprocessing/canvas_raster.py`, sin Tk ni JIT; paridad píxel a píxel con `tests/test_canvas_raster.py`) indexa el LUT. **La vista 3D del Post** ([gui/postprocessing/surface_3d_viewer.py](../../gui/postprocessing/surface_3d_viewer.py)) **y la Memoria de Cálculo** ([file_io/figure_export.py](../../file_io/figure_export.py)) siguen al canvas con el MISMO jet — coherencia cromática 2D↔3D↔PDF. Desde el 2026-09-06 la memoria además comparte el **kernel**: `figure_export._fill_field` llama a `canvas_raster.rasterize_triangles` (mismo orden de triángulos, 0 píxeles distintos; el test lo cubre en `test_figure_export_field`). Es la única dependencia de `file_io/` hacia `gui/`, y es deliberada: `canvas_raster.py` es NumPy puro sin Tk y duplicar el rasterizador sería peor. La **colorbar** (`_draw_colorbar`) muestra la unidad del sistema activo entre corchetes (`Von Mises [Pa]`, vía `result_unit` que `post_tab` pasa a los setters) y formatea los ticks con notación científica para magnitudes grandes/chicas (`_fmt_colorbar_value`: `2.5e7` en vez de `25000000.00`). Su texto usa `CANVAS_COLORBAR_TEXT_COLOR` y las isolíneas `CANVAS_ISOLINE_COLOR` — antes eran el literal `"white"`, que esquivaba la auditoría de hex pero incumplía igual la regla dura 2.

**Convención de índices de la grilla por elemento** (`G[i_ξ, j_η]`, o sea `np.meshgrid(..., indexing="ij")`): la comparten `fem/probe_query.py::compute_raw_grids` / `_get_dN_at_grid` (de donde sale el campo crudo), `gui/preprocessing/canvas_raster.py` (el contorno 2D) y `gui/postprocessing/surface_3d_viewer.py` (la superficie 3D, vía `natural_grid` / `shape_matrix_at_grid` / `element_grid_xy`). **Cualquier vista nueva que consuma una grilla del motor usa esa convención**: el visor 3D armaba su geometría con el `indexing="xy"` por defecto (`[j_η, i_ξ]`) mientras la Z venía indexada `[i_ξ, j_η]`, así que en modo **crudo** dibujaba el campo **transpuesto dentro de cada elemento** — invisible en un campo simétrico y grosero en cualquier otro (el modo suavizado no lo sufría porque X, Y y Z salían del mismo `meshgrid`). Regresión en [test_post_inspection.py](../../tests/test_post_inspection.py), que compara geometría y campo contra `compute_raw` punto por punto y verifica que la transpuesta *sí* difiera (si no, el test no distinguiría el bug del arreglo). `shape_matrix_at_grid` cachea la N de la grilla por `(tipo, n)` —es la misma para todos los elementos— y evalúa las funciones de forma una vez por malla en vez de `(n+1)²` veces por elemento: 0,156 s → 0,003 s en Cook 16×16 Q9 por repintado.

**Escala de color de la vista 3D**: `Surface3DViewer._draw_colorbar` dibuja una colorbar con `<campo> [<unidad del proyecto>]` y los ticks de `config.settings.fmt_escala`, **el mismo formateador** que los de la colorbar del lienzo (`MeshCanvas._fmt_colorbar_value` delega ahí; es la fuente única). Sin ella el 3D era la única vista de resultados sin referencia numérica del color, y la tesis apoya la elección de *jet* justamente en que «se compensa con la escala numérica graduada junto al contorno». La decisión de **ejes limpios** (sin ticks, sin números, sin paneles) sigue en pie: vale para el cubo 3D, no para la leyenda. `_clear_colorbar` la retira antes de cada repintado — `ax.clear()` no la borra y cada refresco apilaba un eje nuevo. El readout del header usa `fmt_escala` por la misma razón (antes era `{v:.3g}` inline y sin unidad).

**Controles numéricos del panel del Post**: `Factor de escala` y `Número de niveles` se leen con `_leer_factor_escala` / `_leer_niveles_isolineas`, **nunca** con `DoubleVar.get()` / `IntVar.get()` directo — sus variables son `StringVar`. Con las variables tipadas, escribir `2,5` (la coma decimal de un Excel en español), `abc` o dejar el campo vacío levantaba `TclError` **dentro del callback de Tk**: el traceback iba a la consola, el alumno no veía nada y el control quedaba mostrando un valor que no se estaba usando. Los lectores toleran la coma (`to_float_flex`, la misma vía que los editores de celda del Pre-Proceso), acotan los niveles a `ISOLINE_COUNT_MIN`/`MAX` de `config/settings.py`, avisan en la barra de estado nombrando el valor rechazado y el formato aceptado, y **devuelven el control al último valor bueno** para que lo que se ve sea lo que se usa. Cualquier control numérico nuevo del Post sigue ese patrón.

**Ctrl+C del probe**: `ProbeOverlay.tsv_headers` arma los encabezados en español y con la unidad del sistema activo (`σx [MPa]`, `Von Mises [MPa]`), igual que los de la tabla de resultados —el otro `Ctrl+C` del Post—; antes eran las claves internas en inglés y sin unidad (`sigma_x`, `von_mises`). Los **números** del TSV sí van con toda la precisión disponible y no con `fmt`: lo que se pega en una planilla se usa para recalcular, no solo para leer. `Ctrl+C` fuera de la malla o sin solución lo dice en la barra de estado en vez de no hacer nada.

**`result_kind`**: junto a `label` y `unit`, `set_result_values` / `set_element_result_grid` reciben la **magnitud** del campo activo (`"stress"` o `"displacement"`) y el canvas la usa en `fmt(value, kind)` para la etiqueta de valor del nodo (regla dura 8). Con el `'stress'` fijo que había antes, los desplazamientos —del orden de 1e-5 m— se rotulaban todos `0.00`. `post_tab._on_result_changed` la deriva del mismo `is_stress` que ya elige la unidad.

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

### Lentes por fase — el lienzo enseña el método (rediseño 2026-09-09)

El mismo modelo se mira con **tres lentes**, una por fase, y el cambio de pestaña cambia lo
que el lienzo dibuja: geometría (Pre), sistema discreto (Proceso) y campo (Post).
`MeshCanvas.set_phase` fija los defaults de cada lente; `redraw()` documenta en un comentario
la **pila de capas** completa, de abajo hacia arriba (cuadrícula del mundo → malla original
fantasma → campo → elementos → nodos → índices de GDL → cargas → superficiales →
restricciones → reacciones → realce de aristas → lente del elemento → isolíneas → colorbar →
icono de ejes → preview del dibujo → capas educativas → franja lectora). Lógica pura y
testeable sin Tk en [canvas_logic.py](../../gui/preprocessing/canvas_logic.py); regresiones en
[tests/test_canvas_lens.py](../../tests/test_canvas_lens.py) (sin display) y
[tests/test_canvas_lens_gui.py](../../tests/test_canvas_lens_gui.py) (Tk real, `--con-gui`).

- **Cuadrícula anclada al mundo** (`_draw_grid`, todas las fases). Dejó de ser un empapelado
  en píxeles de pantalla: el paso es de la serie **1-2-5 en unidades del modelo**
  (`grid_step`, elegido para medir ~`GRID_TARGET_PX` = 70 px), cada `GRID_MAJOR_EVERY` = 5
  pasos hay una línea mayor **rotulada con su valor sobre los ejes X=0 / Y=0**, y los ejes se
  dibujan más marcados (`CANVAS_GRID_MAJOR_COLOR`, `CANVAS_GRID_ORIGIN_COLOR`,
  `CANVAS_GRID_LABEL_COLOR`). Las líneas llevan tag `world` (viajan con el pan y escalan con
  el zoom junto a la malla; el redraw del fin de interacción re-elige el paso) y cubren el
  viewport + el margen del culling. Motivo: el alumno tipea coordenadas en la tabla de Nodos y
  en el Entry del modo dibujo, y la cuadrícula vieja no caía en valores redondos ni ubicaba
  el origen. Si el origen queda fuera de pantalla los rótulos se van con él (el readout del
  cursor sigue diciendo dónde estamos). **No reintroducir** la cuadrícula en píxeles de
  pantalla (`spacing = clamp(50·scale)`, tag `screen`).
- **Capa de GDL** (`show_dofs`, `_draw_dof_tags`, tag `dofs`): junto a cada nodo, los dos
  índices globales de sus GDL en K (`u → 2i`, `v → 2i+1`, con `i` el ordinal de
  `node_index_map`, o sea el rango `0..2N−1` de la tesis). El GDL **restringido va tachado**
  (fuente `overstrike`) y en `CANVAS_DOF_FIXED_COLOR` = color de las restricciones: es la fila
  y la columna que se eliminan al reducir el sistema. Default por fase: **Proceso la
  enciende**, Pre y Post la apagan (`set_phase`); el menú del título la prende donde sea. Solo
  en LOD `near` y, en mallas más grandes que `LOD_MIN_ELEMENTS_FOR_GATING`, recién cuando la
  arista media mide `DOF_TAGS_MIN_EDGE_PX` = 90 px (duplican el texto de cada nodo y a zoom
  medio saturaban Cook 8×8). Vista limpia la apaga y la restaura como a las otras capas.
- **Lente del elemento seleccionado** (`_draw_element_lens`, tag `lens`, solo en Proceso con
  UN elemento seleccionado y **sin overlay educativo activo** — cuando hay uno, el módulo
  dibuja su propia versión con sus tags `edu_*`): numeración local **1..4** en discos
  amarillos desplazados hacia adentro (el número global del nodo va hacia afuera), los **ejes
  naturales ξ y η** desde el centroide (`element_local_frame`: ξ apunta al punto medio de la
  arista N2–N3, η al de N3–N4 — la convención isoparamétrica de `fem/shape_functions.py`;
  `CANVAS_XI_AXIS_COLOR` / `CANVAS_ETA_AXIS_COLOR`) y los **puntos de Gauss** en coordenadas
  físicas (`gauss_physical_points`: `x = Σ Nᵢ(ξ_p, η_p) xᵢ` con las N y los PG del motor, 2×2
  en Q4 y 3×3 en Q9; `GAUSS_CANONICAL_COLOR`). Las decoraciones de la lente escalan con el
  zoom con techo propio `LENS_SCALE_MAX_FACTOR` = 1,6 (con el 2,5 general los discos tapaban
  los nodos vecinos).
- **Franja lectora** (`_draw_inspector`, tags `screen` + `inspector`, siempre arriba de todo y
  al pie del lienzo, `CANVAS_INSPECTOR_*`): describe **en términos del MEF** lo que hay bajo
  el cursor. Elemento: `Elemento 3 · Q4 — nodos 4→5→8→7 (antihorario) · material · t · A ·
  GDL 6 7 8 9 14 15 12 13 → kₑ 8×8` (Q9: 8 GDL y `… (+10)`, `kₑ 18×18`, `+ 5 internos`).
  Nodo: `Nodo 5 — (7.000, 4.000) mm · GDL u₅→8, v₅→9 · libre | empotrado | rodillo · F = (…) N ·
  compartido por 4 elementos`. Sin nada debajo, la **pista de gesto de la fase**
  (`phase_hint`: Pre, Pre sin malla, dibujando, Proceso, Post). Textos en
  `canvas_logic.node_summary` / `element_summary` / `phase_hint`, con `fmt` y la unidad del
  proyecto. Hit-test en `_update_inspector`: nodo (radio 10 px, `nearest_node` sobre un cache
  numpy `_node_xy_cache` que `redraw` invalida) antes que elemento (`_hover_highlight_eid` si
  el hover está habilitado, si no `_hit_test_element_at`). **En Post no consulta** (la sonda
  manda: muestra la pista), tampoco dibujando ni con el viewport en movimiento, ni por encima
  de 3000 elementos. `_set_inspector_target` repinta SOLO la franja y avisa a los
  `hover_listeners`.
- **Reacciones en los apoyos** (`_draw_reactions`, tag `reactions`, Post con solución):
  `R = K·u − F` en cada GDL restringido (`solution["reactions"]`, que `post_tab` pasa con
  `set_reactions` en `_on_result_changed`), como flecha que **llega al nodo desde afuera con la
  punta en el nodo** — la misma gramática que las cargas: la punta de una fuerza está en su
  punto de aplicación, como en un diagrama de cuerpo libre — en `CANVAS_REACTION_COLOR` y con
  rótulo `Rx=` / `Ry=` en la cola, que queda del lado de afuera del modelo. Toggle `Mostrar
  reacciones en los apoyos` en *Inspección del campo* del panel del Post (default on; los
  controles de resultado viven ahí, regla "una sola vía"). `clear_results_overlay` la
  descarta al volver a Pre/Proc. **No reintroducir** la flecha con la cola en el nodo (los
  rótulos caían sobre los del valor nodal y sobre la colorbar).
- **Glifo compartido de los ejes ξη** ([canvas_glyphs.py](../../gui/preprocessing/canvas_glyphs.py),
  `draw_natural_axes(canvas, to_screen, pts, *, factor, tags)`): lo usan la lente de arriba y
  las capas de M1/M2/M3/M5 cuando están abiertas (la lente se retira y el módulo dibuja los
  mismos ejes con el mismo glifo), y sus dos colores son los de los ejes del cuadrado natural
  de esos módulos (`edu_plot_style.draw_natural_axes_mpl`). Sin Tk en los imports: recibe el
  canvas como argumento y se testea con un doble en `test_canvas_lens`. Es la única pieza de
  dibujo de `gui/preprocessing/` que `education/` importa, a propósito: duplicar la flecha en
  cinco lugares era peor.

### Identidad visual por fase

| Fase | Icono | Color | Bootstyle |
|---|---|---|---|
| PRE-PROCESO | 📐 | `PHASE_PRE_COLOR` `#0d6efd` | `info` |
| PROCESO | ⚙ | `PHASE_PROC_COLOR` `#fd7e14` | `warning` |
| POST-PROCESO | 📊 | `PHASE_POST_COLOR` `#198754` | `success` |

Banner con `gui/widgets/phase_banner.py::build_phase_banner`. Los subtítulos son **el método de la fase**, no una lista de cosas: Pre `Malla → material → apoyos → cargas`, Post `u → ε = B·u → σ = D·ε → R = K·u − F`; el de Proceso es la **tira del método** (`subtitle=None` + `gui/widgets/method_strip.py`, ver [arquitectura.md](arquitectura.md)). Pre-Proceso tiene su sub-pestaña "🎓 Educación" (la crea `pre_tab`) y Proceso monta su panel de módulos directo en el frame; **el Post no tiene módulos educativos**.
