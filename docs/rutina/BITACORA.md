# Bitácora de la rutina de mejora continua

Una entrada por sesión, **apilada al final**. Nunca se reescribe ni se resume una entrada
anterior: este archivo es la memoria entre agentes y su valor está en que sea fiel.

Las reglas de la rutina están en [RUTINA.md](RUTINA.md); la cola de trabajo, en
[BACKLOG.md](BACKLOG.md).

## Formato de cada entrada

```markdown
## Sesión NN — AAAA-MM-DD HH:MM — Área: <nombre del área>

**Commit**: <hash corto> · **Gates**: run_gates OK · (latex/vv si aplica)

### Qué se hizo y por qué
- `archivo.py:línea` — qué cambió. **Por qué**: el motivo, en términos de lo que el alumno
  ve o de la regla que se estaba incumpliendo.

### Errores encontrados y corregidos
- Descripción, cómo se detectó, cómo se arregló. (o "ninguno")

### DECISIÓN CONGELADA REVERTIDA
- Cuál, dónde estaba documentada, antes → después, y por qué. Capítulo y fila de
  `no-reintroducir.md` actualizados en el mismo commit. (o "ninguna")

### Pendientes visuales para el autor
- Qué abrir, con qué modelo, qué debería verse, cómo revertir si está mal. (máx. 3)

### Descartado
- Lo que se evaluó y NO se hizo, con el motivo. Evita que la próxima sesión lo reproponga.

### Área siguiente
- Nº y nombre.
```

---

## Sesión 00 — 2026-09-08 — Montaje de la rutina

**Commit**: (este) · **Gates**: `run_gates` verde (97/97 módulos, 0 hex, 14/14 tests)

### Qué se hizo y por qué

- Se puso `main` al día con `origin`: commit `53ddf11` con el TeX Live embebido, la
  corrección de la extrapolación Q4, la V&V ampliada y la bibliografía saneada. **Por qué**:
  la rutina trabaja sobre `origin/main`, así que no podía arrancar con 75 archivos sin
  commitear en el working tree del autor.
- `tests/run_gates.py` — nuevo. Un solo comando que importa los 97 módulos del proyecto,
  audita los hex literales de `gui/` y `education/` con `tokenize` + `ast` (exacto: descarta
  comentarios y docstrings, que el canon sí permite) y corre la suite headless completa,
  incluida la regresión numérica de la regla dura 21. Sale 0 o 1. **Por qué**: sin un gate
  ejecutable, "verificá antes de pushear" es una intención; con él es una condición.
  Medido: ~30 s, y `test_canvas_raster` se lleva 18 de esos 30.
- `docs/rutina/` — `RUTINA.md` (el prompt autoritativo), esta bitácora y `BACKLOG.md`.
  **Por qué**: el disparador de claude.ai solo lleva un resumen; el detalle vive en el repo
  para que se versione junto al código y cada sesión lo lea actualizado.

### Errores encontrados y corregidos

- La primera versión de la auditoría de color de `run_gates` marcaba 7 falsos positivos:
  filtraba docstrings por heurística (línea que empieza con comilla) y no veía los de varias
  líneas. Los 7 hits estaban dentro de docstrings legítimos —`webp_player.py` documentando su
  API, `gauss_glyph.py` documentando la paleta de puntos de Gauss—. Se reescribió con
  `tokenize` + `ast`: en Python un `#RRGGBB` solo puede vivir en un string o en un comentario,
  así que se recorren los tokens `STRING`, se descartan los que `ast` marca como docstring y
  lo que queda es código de verdad. Resultado: 0 hits, sin falsos positivos.

### DECISIÓN CONGELADA REVERTIDA

Ninguna.

### Pendientes visuales para el autor

Ninguno propio de esta sesión. Siguen abiertos los que ya listaba
[../notas/ESTADO.md](../notas/ESTADO.md): validación visual del Post-Proceso y de la Memoria
tras la vectorización y la corrección de la extrapolación Q4, y prueba del instalador con
TeX Live embebido en una PC sin MiKTeX.

### Descartado

- **Smoke test de la GUI completa** (construir `MainWindow`, recorrer pestañas y resolver, con
  `withdraw()` y sin `mainloop()`). No entra en el gate de la rutina: `MainWindow.__init__`
  llama a `root.state("zoomed")`, que en X11 no existe, así que fallaría en el sandbox Linux
  por un motivo que no es un defecto del software. Los dos tests que sí necesitan Tk
  (`test_draw_mode`, `test_selection_integration`) quedaron detrás de `--con-gui`, para que el
  autor los corra en Windows.

### Área siguiente

1 — Canvas del Pre-Proceso.

---

## Sesión 01 — 2026-09-08 19:37 UTC — Área: 1 — Canvas del Pre-Proceso

**Commit**: (este) · **Gates**: `run_gates` verde (97/97 módulos, 0 hex, **15**/15 tests) ·
además `xvfb-run … run_gates --con-gui` verde (17/17), que hasta hoy no corría en Linux

### Qué se hizo y por qué

- `gui/preprocessing/mesh_canvas.py::_on_delete_key` — reescrito para que **borre la
  selección completa**, no un solo ítem. **Por qué**: el handler despachaba por los espejos
  `highlighted_*`, que valen `None` cuando hay más de un ítem en el set. Con dos o más nodos
  seleccionados (Ctrl+Click, que el canvas soporta desde siempre y la tesis promete en
  `tab:atajos`), `Supr` **no hacía nada y no lo decía**. El canon
  ([canvas-preproceso.md](../convenciones/canvas-preproceso.md) §*Delete bidireccional*) ya
  describía el borrado múltiple como si existiera: era la implementación la que faltaba.
  Ahora lee los sets `selected_*`, mantiene el orden de prioridad del hit-test
  (carga > restricción > superficial > elemento > nodo) y delega en cinco helpers
  `_delete_selected_<tipo>()` que filtran ids vivos, capturan **un** snapshot de undo (regla
  dura 4), mutan, sanean la selección y avisan una vez. Los previews en cascada de elementos
  y nodos son los mismos que ya usaba el spreadsheet (`pre_tab._remove_element` /
  `_remove_node`): las dos vías de borrado dejaron de comportarse distinto.
- `mesh_canvas::_on_delete_key` (rama vacía) — `Supr` sin nada seleccionado ahora escribe
  "Nada seleccionado — clickeá un nodo, elemento, carga o restricción…". **Por qué**: una
  tecla que no hace nada ni explica por qué es un callejón sin salida (RUTINA §7).
- `mesh_canvas::prune_dead_selection()` — nuevo método público que saca de los seis sets los
  ids que ya no existen y emite el callback si algo cambió. `MainWindow._on_state_restored`
  pasó de 20 líneas de saneo duplicado a llamarlo. **Por qué**: fuente única, y el borrado
  desde el canvas necesitaba exactamente eso (ver el error de índices más abajo).
- `mesh_canvas::set_result_values` / `set_element_result_grid` + `post_tab._on_result_changed`
  — nuevo parámetro `kind` ("stress" | "displacement") que el canvas usa en
  `fmt(value, kind)`. **Por qué**: la etiqueta de valor del nodo formateaba **siempre** con
  `'stress'` (2 decimales), así que en el Post con Ux / Uy / |U| —del orden de 1e-5 m— todos
  los nodos rotulaban `0.00`. Regla dura 8: los decimales salen de la magnitud.
- `config/settings.py` + `mesh_canvas` — `CANVAS_ISOLINE_COLOR` y
  `CANVAS_COLORBAR_TEXT_COLOR` reemplazan al literal `"white"` de las isolíneas y de la
  colorbar. **Por qué**: regla dura 2. El nombre de color esquivaba la auditoría de hex
  (`#RRGGBB`) pero incumplía igual: era un color decidido en `gui/`.
- `mesh_canvas` — 9 `except Exception: pass` del área pasaron a dejar traza
  (`traceback.print_exc()`, la convención de `undo_stack` y `post_tab`): capas educativas
  (con guard de una traza por capa, porque el loop de animación las reejecuta a ~30 fps),
  click consumers, `on_selection_changed`, `on_canvas_delete`, `on_draw_element_created`,
  `on_draw_mode_changed`, `on_ortho_changed`, `on_hover_element` y las dos capturas de undo
  (ahora el helper `_capture_undo`). **Por qué**: todas son caminos que el alumno recorre y
  su fallo se manifestaba como "el módulo no dibuja", "la tabla no se actualiza" o "el
  Ctrl+Z no trae esto", sin ninguna pista. Se conservan mudos los legítimos: `after_cancel`,
  el import diferido de `education.overlay_module` y `set_status`.
- `mesh_canvas::_draw_commit` — si `auto_expand_if_q9` falla (regla dura 5), ya no se traga:
  deja traza y **avisa al alumno** que los nodos intermedios Q9 no se generaron y cómo
  recuperarlos. **Por qué**: si no, el elemento queda con 4 nodos y el error aparece mucho
  después, al resolver, con un mensaje que no apunta a esta causa.
- `mesh_canvas::_on_click` — eliminada la "Prioridad 5" (segunda pasada de arista potencial).
  **Por qué**: era inalcanzable. Solo se llegaba ahí con la sub-pestaña *Carg. Superf.*
  activa y una arista que ya tenía carga, y en ese caso la Prioridad 3 (tolerancia 12 px
  sobre el mismo segmento que la arista, 10 px) siempre matchea antes y retorna.
- `gui/main_window.py::__init__` — `root.state("zoomed")` con degradación portable
  (`attributes("-zoomed")` → `geometry(pantalla)`). **Por qué**: fuera de Windows lanzaba
  `TclError` y **mataba la app en el constructor**; por eso `run_gates --con-gui` solo podía
  correrse en Windows. Con el guard, `test_draw_mode` y `test_selection_integration` corren
  en el sandbox bajo `xvfb-run` y quedaron verdes — el gate de GUI dejó de ser una promesa.
- `tests/test_canvas_delete.py` — nuevo (11 casos, sin display: instancia el canvas con
  `object.__new__` y le monta el estado mínimo, así ejercita el código real y no una copia).
  Sumado a `run_gates`. Cubre el borrado múltiple de los 5 tipos, el snapshot único, la
  cancelación del modal, la prioridad carga > nodo, el aviso sin selección y
  `prune_dead_selection`.

### Errores encontrados y corregidos

- **`Supr` mudo con multi-selección** (el principal, arriba). Detectado leyendo el contrato
  del área contra el canon: `_on_delete_key` usaba `highlighted_*` y `_emit_selection_changed`
  los pone en `None` cuando el set tiene ≠ 1 elemento.
- **Índice stale de carga superficial**: al borrar la carga superficial #k, el código viejo
  ponía `highlighted_surface = None` pero **dejaba el k en `selected_surfaces`**. Como los
  índices son posicionales, ese k pasaba a señalar la carga siguiente: el canvas la pintaba
  amarilla y la tabla le ponía el tag `canvas_selected`, o sea que el alumno veía
  seleccionada una carga que nunca tocó. Mismo patrón (id muerto en el set) en los otros
  cuatro tipos. Corregido con `prune_dead_selection()` y, en superficiales, vaciando el set.
  Regresión en `test_canvas_delete.test_delete_de_superficial_no_deja_indice_stale`.
- **Desplazamientos rotulados `0.00`** en las etiquetas de nodo del Post (arriba).
- **La app no arranca fuera de Windows** por `root.state("zoomed")` sin guard (arriba). No
  afecta al `.exe` distribuido, pero bloqueaba el gate `--con-gui`.
- **Saneo de selección duplicado** entre `main_window` y lo que necesitaba el canvas; peor,
  en `_on_state_restored` corría **después** de `clear_highlights()`, o sea sobre sets ya
  vacíos: 20 líneas que no hacían nada y que el canon citaba como el mecanismo real.

### DECISIÓN CONGELADA REVERTIDA

Ninguna.

### Pendientes visuales para el autor

1. **Borrado múltiple desde el lienzo.** Abrir la GUI, `Ctrl+E` (ejemplo canónico), en
   Pre-Proceso seleccionar 2–3 nodos con **Ctrl+Click sobre el lienzo** y presionar `Supr`:
   debe salir **un** modal con la cuenta agregada de elementos/nodos en cascada; al aceptar,
   se borran todos, las 5 tablas se refrescan y **un solo `Ctrl+Z`** lo devuelve entero.
   Con nada seleccionado, `Supr` debe escribir "Nada seleccionado — clickeá un nodo…" en la
   barra de estado. Revertir: `git revert` de este commit.
2. **Etiquetas de nodo en el Post.** `F5`, pestaña Post, elegir **Ux / Uy / |U|**: cada nodo
   debe rotular su valor con 5 decimales (antes todos decían `0.00`). Con von Mises o σx debe
   seguir en 2 decimales. Las isolíneas y el texto de la colorbar deben verse **idénticos**
   (solo se movió el blanco a constante).
3. **Arranque maximizado en Windows.** La ventana debe seguir abriéndose maximizada: el
   `state("zoomed")` ahora está dentro de un `try`, y en Windows es la primera rama, así que
   no debería cambiar nada. Si arranca en tamaño chico, el guard falló y hay que revisarlo.

### Descartado

- **Anclar la cuadrícula al mundo con paso "lindo" (1-2-5)**: hoy `_draw_grid` es un
  empapelado en coordenadas de pantalla (`spacing = clamp(50·scale, 30, 200)`), no dice nada
  del modelo. Sería una mejora real hacia el look ANSYS/SAP2000, pero es un cambio puramente
  visual que el gate no puede juzgar y que se lleva media sesión bien hecho (paso, rótulo,
  interacción con el zoom interactivo). Queda anotado en el BACKLOG para el próximo turno del
  área 1, con el criterio ya escrito.
- **Corregir la tesis** (`tab:atajos` del Anexo A omite `F8`/ORTHO y `BackSpace`, y la fila
  de `Supr` dice "la entidad seleccionada" cuando ahora borra la selección completa): el
  sandbox no tiene `pdflatex` ni `latexmk`, y RUTINA §6 exige compilar antes de pushear. Va
  al BACKLOG para el área 14.
- **Barrer los literales de color con nombre de `education/` y `details_panel.py`** (17
  ocurrencias de `"white"` / `"black"`): mismo defecto que corregí en el canvas, pero son
  áreas 4, 7 y 8. Al BACKLOG, para que cada una lo cierre en su turno.
- **Hacer que el probe y el realce de arista sigan la malla deformada**: `_draw_highlight` y
  `_hit_test_potential_edge` usan `world_to_screen` sobre coords sin deformar, a diferencia
  del resto del canvas, que usa `_get_node_screen_pos`. Hoy es inocuo (en el Post no hay
  selección y `clear_highlights()` corre al entrar), así que tocarlo sería riesgo sin
  beneficio. Anotado en el BACKLOG por si el Post alguna vez recupera la selección.

### Área siguiente

2 — Spreadsheet y tablas (`gui/preprocessing/pre_tab.py`, `_table_helpers.py`).

---

## Sesión 02 — 2026-09-08 21:00 UTC — Área: 2 — Spreadsheet y tablas

**Commit**: (este) · **Gates**: `run_gates` verde (97/97 módulos, 0 hex, **16**/16 tests) ·
además `xvfb-run … run_gates --con-gui` verde (18/18)

### Qué se hizo y por qué

El hallazgo central es uno solo, repetido cinco veces: **borrar desde una tabla saneaba el
modelo pero no la selección del canvas**. Seleccionar una fila propaga la selección al canvas
(`_on_*_select`), y de los seis sets de `MeshCanvas` salen las filas fantasma, el tag
`canvas_selected` y el realce del lienzo. O sea que **todo** borrado desde el spreadsheet —el
camino normal, no un caso borde— dejaba ids muertos. Es el mismo defecto que la sesión 01
cerró para el lienzo; la vía del spreadsheet quedó abierta.

- `pre_tab::_sync_selection_after_delete()` — nuevo, lo llaman los cinco `_remove_*`.
  **Por qué**: sin él, (a) borrar un nodo dejaba una **fila fantasma azul de un nodo que ya
  no existe** en Cargas y Restricciones, y clickearla no hacía nada ni lo decía
  (`_commit_load_ghost` retorna temprano si el nodo no está en el modelo); (b) borrar una
  carga o una restricción hacía **reaparecer la fila borrada como fantasma con ceros, en su
  mismo lugar**, porque `_on_load_select` mete el nodo en `selected_nodes` para dibujar el
  halo; (c) borrar una carga superficial dejaba su índice —posicional— en
  `selected_surfaces`, que pasaba a señalar **otra** carga y la dejaba resaltada en amarillo.
  Delega en `MeshCanvas.prune_dead_selection()` (fuente única) y le agrega lo que ese saneo
  no puede saber: los nodos vivos cuya selección era el reflejo de la fila borrada, y el
  vaciado de `selected_surfaces`.
- `pre_tab::_nothing_selected()` — `Supr` sin filas seleccionadas ahora lo dice en la barra de
  estado, en las 5 tablas. **Por qué**: paridad con el lienzo (sesión 01) y RUTINA §7 — una
  tecla que no hace nada ni explica por qué es un callejón sin salida. El placeholder y las
  fantasmas se filtran explícitamente: no son selección.
- `_remove_load` / `_remove_constraint` / `_remove_surface_load` — ahora llaman
  `_update_status_info()` y dan un resumen en la barra de estado. **Por qué**: el badge de
  salud vive en `_update_status_info`; borrar la última restricción desde la tabla dejaba el
  modelo sin resolver y el badge diciendo "✓ Modelo sano". El borrado desde el lienzo sí lo
  refrescaba (vía `on_canvas_delete`); el de la tabla no. Y las tres eran mudas: borrabas y
  la barra de estado no confirmaba nada.
- `_remove_node` — el resumen pasó de `"Nodo(s) eliminado(s)."` a "Nodo 3 eliminado. 2
  elemento(s) en cascada. 1 nodo(s) preservado(s) como huérfano(s)." **Por qué**: el genérico
  no distinguía 1 de 30 ni decía qué se llevó puesto la cascada, que es justo lo que el
  alumno necesita confirmar.
- `pre_tab::_update_title()` — wrapper guardado (como `_update_status_info`) y usado en los
  borrados y en los 5 `_paste_*`. **Por qué**: el ● de "proyecto modificado" no se actualizaba
  en ninguna de esas vías; el título mentía hasta la próxima acción que sí lo refrescara.
- **Números: `to_float_flex` también en los editores de celda** (X/Y, espesor, Fx/Fy, q y
  ángulo). **Por qué**: los `_paste_*` toleran la coma decimal de Excel desde hace tiempo,
  pero tipear `1,5` a mano daba "Valor numerico invalido". Dos vías para lo mismo con reglas
  distintas, en un software en español.
- `_error_numero()` / `_error_nodo_inexistente()` — nuevos. **Por qué**: los mensajes eran
  `"Error" / "Valor invalido."` y `"El nodo 7 no existe."`, que no nombran ni la celda ni el
  formato aceptado ni el siguiente paso. Ahora dicen `Y: valor invalido — «hola» no es un
  numero. Usá punto o coma decimal` y, para nodos, listan los ids definidos (o explican cómo
  crear el primero si no hay ninguno).
- `_mensaje_pegado()` — el resumen del paste TSV dice **por qué** descartó cada fila (nodo
  inexistente / valor no numérico / faltan columnas, agregados con `Counter`). **Por qué**:
  los parsers descartan con un `continue` silencioso, así que un `"0/5 fila(s) pegada(s)"` no
  le daba al alumno ninguna pista de qué estaba mal en lo que acababa de pegar.
- `_build_loads_visual_list` / `_build_constraints_visual_list` / `_get_pick_ghost_edges` —
  las fantasmas salen ahora de `_get_pick_ghost_node_ids` / `_get_pick_ghost_edges`, que
  filtran los nodos inexistentes. **Por qué**: las dos primeras las recalculaban aparte
  (`selected_nodes - project_keys`, sin chequear existencia), así que eran una segunda fuente
  de verdad que podía proponer una fila imposible de confirmar. Defensa en profundidad sobre
  el saneo de arriba.
- **6 de los 22 `except Exception` del área** pasaron a dejar traza con
  `traceback.print_exc()` (la convención de `undo_stack` / `post_tab` / `mesh_canvas`):
  `_capture` (si el snapshot falla, la acción queda fuera del `Ctrl+Z` y nadie se entera —
  regla dura 4), `_safe_redraw` (el lienzo se queda con el modelo viejo), el refresco tras
  expandir a Q9 (síntoma: "los nodos internos no aparecen en la tabla"), y los 3 del panel de
  módulos educativos. Los otros 16 son legítimos (`set_status` y `nametowidget` en tests
  headless, guards de widgets destruidos).
- **Docstrings mentirosos y secciones muertas**. El encabezado de `pre_tab.py` anunciaba
  *fill-down `Ctrl+D`*, *navegación Tab/Shift-Tab/flechas en el editor*, *menú contextual con
  Insertar/Duplicar/Centrar/Eliminar* y *toggle por click simple* — las cuatro son
  **decisiones tomadas** que figuran en `no-reintroducir.md`. El de `_table_helpers.py` decía
  que `on_commit` recibe `(text, direction)`. Quedaban además 8 encabezados de sección vacíos
  (`FILL-DOWN`, `Acciones de menu contextual: …` ×5, `Navegacion teclado`, `Atajos de
  teclado`). Un agente que lee eso "restaura lo que falta" y revierte trabajo hecho: por eso
  se corrigieron los docstrings y se borraron los encabezados huecos.
- `tests/test_pre_tab_delete.py` — nuevo (12 casos, sin display: `PreProcessTab` con
  `object.__new__` y un doble mínimo de Treeview, igual que hizo la sesión 01 con el canvas).
  Sumado a `run_gates`. Verificado que **falla sin el arreglo**: con
  `_sync_selection_after_delete` anulado, los tres casos de selección stale rompen.
- `DOF` → `GDL` en un comentario de `_refresh_constraints_tree` (auditoría de terminología del
  área).

### Errores encontrados y corregidos

- **Selección stale tras borrar desde cualquiera de las 5 tablas** (el principal, arriba), con
  sus tres síntomas visibles: fantasma de un nodo inexistente, fila borrada que vuelve como
  fantasma, y carga superficial equivocada resaltada.
- **El badge de salud no se enteraba** de que se borró la última restricción / carga /
  superficial desde la tabla: quedaba en "✓ Modelo sano" sobre un modelo que ya no resuelve.
- **El título nunca marcaba ●** tras borrar o pegar desde el spreadsheet.
- **`1,5` rechazado a mano y aceptado al pegar** en las mismas celdas.
- **`_remove_surface_load` capturaba el snapshot de undo antes de saber si había algo válido
  que borrar**: con una selección de índices fuera de rango dejaba un snapshot vacío en la
  pila (un `Ctrl+Z` que no deshace nada).
- **`_remove_load` / `_remove_constraint` aceptaban filas fantasma** en la selección: el
  `int("__ghost__4")` levantaba `ValueError` que el `except` de turno se tragaba.
- Verificado con Tk real bajo `xvfb`: borrado de carga y de superficial desde la tabla, la
  fantasma legítima que sí debe aparecer al seleccionar un nodo en el lienzo, el aviso de
  `Supr` sin selección, y el editor de celda aceptando `3,25`.

### DECISIÓN CONGELADA REVERTIDA

Ninguna.

### Pendientes visuales para el autor

1. **Borrar desde las tablas del Pre-Proceso.** `Ctrl+E` (ejemplo canónico). En la sub-pestaña
   **Cargas**, clickear la fila de una carga y `Supr`: la fila debe **desaparecer**, no
   volverse una fila azul con `0 | 0`; la barra de estado dice "Carga en nodo N eliminada." y
   el badge de salud se recalcula. Lo mismo en **Restricciones** y en **Carg. Superf.** (acá,
   con 2–3 cargas superficiales, borrar la primera **no** debe dejar otra resaltada en
   amarillo). En **Nodos**, borrar un nodo con carga no debe dejar una fila fantasma con ese
   número en Cargas. Revertir: `git revert` de este commit.
2. **`Supr` sin selección, en las 5 tablas.** Con el foco en una tabla y ninguna fila
   seleccionada, `Supr` debe escribir "Nada seleccionado — elegí una o varias filas de …" en
   la barra de estado (antes no pasaba nada).
3. **Editar una celda numérica con coma.** Doble-click en X de un nodo, tipear `3,25`, Enter:
   debe guardar 3,25. Con `hola`, el modal debe decir "Y: valor invalido — «hola» no es un
   numero. Usá punto o coma decimal".

### Descartado

- **Darles a los `_on_load_select` / `_on_constraint_select` / `_on_surface_select` una API
  pública en el canvas** (`replace_load_selection`, etc.). Hoy manipulan los sets a mano
  (`_clear_all_sets_silent` + asignación + `_emit_selection_changed`), que es un patrón ya
  establecido en este archivo pero que roza el canon ("no setear `highlighted_*` directo").
  Agregar tres métodos a `MeshCanvas` es trabajo del área 1 y cambiar su API en la sesión del
  área 2 arriesga romper el lienzo por una mejora de forma. Al BACKLOG.
- **Unificar el modal de confirmación de borrado** entre `pre_tab` y `mesh_canvas`: los dos
  arman su texto por separado a partir del mismo preview, con redacciones distintas ("Borrar N
  nodo(s) eliminara en cascada" vs "¿Eliminar el elemento 3?"). Es una fuente doble real, pero
  moverla implica decidir dónde vive el texto (¿`models`? ¿un helper de `gui/`?) y toca las dos
  áreas. Al BACKLOG con la propuesta escrita.
- **Cambiar el placeholder de Elementos para que no cree el elemento con los 4 vértices
  iguales** (`[first_node] * 4`): es un elemento degenerado hasta que el alumno completa los
  vértices, y el validador de salud lo marca mientras tanto. Cambiarlo implica rediseñar el
  flujo del placeholder (que es una decisión tomada y documentada), así que no entra en una
  sesión de pulido. Al BACKLOG como propuesta.

### Área siguiente

3 — Proceso (`gui/processing/proc_tab.py`).

---

## Sesión 03 — 2026-09-08 21:31 UTC — Área: 3 — Proceso

**Commit**: (este) · **Gates**: `run_gates` verde (97/97 módulos, 0 hex, **17**/17 tests) ·
además smoke con Tk real bajo `xvfb` del flujo F5 (modelo sano y modelo con error crítico)

> Nota de entorno: este sandbox vino **sin el stack y sin `tkinter`** (el `python3.11` de la
> imagen no lo trae y su paquete `python3.11-tk` vive en un PPA que el proxy bloquea). El gate
> se corrió con un venv de `python3.12` del sistema —que sí tiene `tkinter`— más
> `pip install -r requirements.txt`. Sin tocar `requirements.txt` ni agregar librerías.

### Qué se hizo y por qué

El hallazgo central es de **coherencia con la tesis**, la prioridad 1 de la rutina. El Anexo A
(`06_anexos.tex`, §*Proceso: resolución y exploración didáctica*) afirma: «La tecla F5, o el
cambio a la pestaña de post-proceso, dispara la resolución, que antes valida el modelo con un
comprobador de salud […] los errores críticos se reportan con sugerencias de corrección». El
software **no lo cumplía por la vía de F5**.

- `gui/main_window.py::_on_solve` — borrados los dos pre-chequeos propios (`num_elements == 0`
  y `not boundary_conditions`) que abrían `messagebox.showwarning("Aviso", …)` y **retornaban
  antes del comprobador de salud**. Ahora F5 invalida `is_solved` / `post_tab.solution`, navega
  a Post y llama `post_tab.auto_solve()`: una sola vía de validación.
  **Por qué**: los dos casos más frecuentes de modelo incompleto —justo los del alumno que
  recién arma su malla— eran los únicos que **no** llegaban al `HealthReportDialog`. El alumno
  veía "Defina al menos una restricción (BC) antes de resolver", que nombra el problema pero no
  cómo resolverlo, en lugar del diálogo con el hint educativo («¿por qué?»), el botón
  **🔧 Corregir** y el **📍 Ir al ítem**. Peor: los pre-chequeos eran más pobres que el
  validador, así que un solo apoyo restringido en x (`insufficient_restraints`, error crítico)
  pasaba el filtro y terminaba igual en el diálogo — dos comportamientos distintos para la misma
  tecla según qué le faltara al modelo. Y es la regla dura 16 aplicada al flujo de resolución:
  la GUI muestra el reporte, no valida por su cuenta.
- `gui/postprocessing/post_tab.py::auto_solve` — **guard de reentrancia** (`_solving`): el
  cuerpo pasó a `_auto_solve()` y `auto_solve()` es el guard.
  **Por qué**: el `HealthReportDialog` es **no modal** y su `wait_window()` corre el event loop,
  así que mientras está abierto Tk sigue despachando eventos. `notebook.select(2)` **encola**
  el `<<NotebookTabChanged>>` (verificado: Tk lo entrega después del `select`, ni siquiera con
  `update_idletasks`), de modo que el handler de pestaña llamaba `auto_solve()` **con el diálogo
  abierto** y abría un segundo diálogo idéntico sobre el primero. El alumno tenía que cerrar dos
  reportes de salud para volver a su modelo. Reproducido con Tk real: sin el guard se cuentan
  dos Toplevels `⚕ Salud del modelo`; con el guard, uno.
- `post_tab::_set_busy_cursor` — cursor `watch` en el Toplevel durante el solve, retirado en un
  `finally`. **Por qué**: el solve es síncrono (Cook 32×32 Q9 ≈ 1 s entre solve y tensiones, y
  varios segundos en 33 k GDL) y el único aviso era el texto "Resolviendo..." en la barra de
  estado, fácil de no ver: la ventana parecía colgada. El `MeshCanvas` hereda el cursor (solo lo
  fija en modo dibujo, que no existe en el Post).
- `education/module_launcher.py` — nuevo `module_label(mod_key)` (fuente única de la etiqueta
  visible) y los 4 mensajes reescritos: (a) el aviso sin malla mandaba a **«Archivo ▸ Cargar
  Ejemplo»**, un menú donde los ejemplos no están (viven en **Ayuda**, decisión documentada), y
  ahora nombra el módulo, la tecla `D` y `Ayuda ▸ Cargar Ejemplo (Ctrl+E)`; (b) el error de
  overlay sin canvas mandaba al «menú Educación», que **no existe** (la barra tiene 3 menús);
  (c)+(d) los dos `except Exception` que abrían `"Error al abrir modulo"` ahora dejan traza con
  `traceback.print_exc()` — sin ella un import roto de un módulo era indepurable.
  **Por qué**: un mensaje que manda al alumno a un menú inexistente es un callejón sin salida.
- `gui/processing/proc_tab.py` + `gui/preprocessing/pre_tab.py` — la barra de estado decía
  `Modulo educativo abierto: mod03`, la **key interna** del launcher, que el alumno nunca vio en
  pantalla. Ahora dice la etiqueta del botón y, en Proceso, sobre qué elemento quedó abierto
  (`③ Matriz B (Deformacion) abierto sobre el elemento #3`) o que está esperando el click
  (`… abierto — clickeá un elemento en el lienzo para verlo sobre él`). El elemento efectivo se
  relee del canvas, así no se duplica la regla de auto-pick del launcher.
- `proc_tab` — subtítulo del panel: «Selecciona un elemento en el canvas para activar los
  modulos» → «Clickeá un elemento en el lienzo y los módulos se activan sobre él. También podés
  abrir uno primero y elegir el elemento después». **Por qué**: el botón gris **no** está
  deshabilitado —abre el módulo igual—, así que el texto viejo describía una precondición falsa.
- `gui/widgets/module_launcher_panel.py` — docstring corregido: decía que el click sin selección
  «abre un dialog de seleccion como fallback». Ese `simpledialog.askinteger` **fue eliminado a
  propósito** y está en `no-reintroducir.md`: el docstring invitaba a reponerlo.
- `proc_tab` — los 3 `except Exception: pass` del área pasaron a dejar traza
  (`traceback.print_exc()`, la convención de `undo_stack` / `post_tab` / `mesh_canvas`): el
  eslabón previo de la cadena `on_selection_changed` (si falla, las tablas del Pre quedan
  desincronizadas del lienzo), el estado inicial del chip y `_current_selected_element` (el
  módulo se abriría sin elemento sin decir por qué). Revisados 3 de los 3 del área.
- `tests/test_solve_flow.py` — nuevo (8 casos, sin display: `MainWindow` y `PostProcessTab` con
  `object.__new__` y dobles mínimos, igual que hicieron las sesiones 01 y 02). Sumado a
  `run_gates`. Cubre: F5 sin elementos y sin restricciones delegando en el validador (ningún
  modal propio), F5 forzando la re-resolución, el guard de reentrancia (un solo diálogo), la
  liberación del flag ante excepción, el cursor de espera puesto y retirado, y los mensajes del
  launcher (menú correcto + `module_label`). Verificado que **falla sin los arreglos**: entrando
  por `_auto_solve` se crean 2 diálogos, y el `_on_solve` viejo abría el modal y nunca llamaba a
  `auto_solve`.

### Errores encontrados y corregidos

- **F5 no pasaba por el comprobador de salud** en los dos casos más comunes (el principal,
  arriba). Incumplía la tesis y la regla dura 16.
- **Dos diálogos de salud apilados** por reentrancia de `auto_solve` durante el `wait_window()`
  del diálogo no modal. Reproducido y verificado con Tk real bajo `xvfb`.
- **Mensajes que mandan a menús inexistentes**: «Archivo ▸ Cargar Ejemplo» (está en Ayuda) y
  «menú Educación» (no existe; la barra tiene Archivo / Modelo / Ayuda).
- **Key interna `mod03` en la barra de estado** de las dos fases con módulos.
- **Subtítulo y docstring que describían un estado falso** (botón gris = deshabilitado, diálogo
  de selección como fallback).
- **Dos `except Exception` del launcher se comían el traceback** de un módulo que no abre.
- Verificado con Tk real: F5 sobre el ejemplo canónico resuelve, deja la pestaña Post, restaura
  el cursor y no deja `_solving` colgado; F5 sobre el mismo modelo sin restricciones abre **un**
  reporte de salud y, al cancelar, devuelve al Pre-Proceso con el aviso.

### DECISIÓN CONGELADA REVERTIDA

Ninguna.

### Pendientes visuales para el autor

1. **F5 con un modelo incompleto.** `Ctrl+E`, borrar todas las restricciones (tabla
   Restricciones, `Supr`) y pulsar **F5**: debe abrirse **un solo** diálogo *⚕ Salud del modelo*
   con el error «sin restricciones», su «🎓 ¿Por qué?» y el «🔧 Corregir» (antes salía un
   `Aviso` seco que no decía cómo arreglarlo). Al cancelar, la app vuelve al Pre-Proceso y la
   barra dice «Corrija los errores antes de resolver». Probar también con **una sola restricción
   en x** (error `insufficient_restraints`): antes ahí se apilaban **dos** diálogos idénticos.
   Revertir: `git revert` de este commit.
2. **Cursor de espera al resolver.** Cargar Cook 32×32 Q9 (Ayuda ▸ Cargar Ejemplo) y pulsar
   `F5`: durante el cálculo el puntero debe ser el reloj de espera y volver al normal al
   terminar. Si queda pegado en reloj, el `finally` de `auto_solve` falló.
3. **Barra de estado y subtítulo de Proceso.** En Proceso, clickear un elemento y abrir
   `③ Matriz B (Deformacion)`: la barra debe decir «③ Matriz B (Deformacion) abierto sobre el
   elemento #N» (antes: «Modulo educativo abierto: mod03»). Sin selección, «… abierto — clickeá
   un elemento en el lienzo…». El subtítulo del panel ahora ocupa 2 renglones: verificar que no
   empuje los botones fuera del panel en 1080p.

### Descartado

- **Un botón «Resolver» en el panel de Proceso.** La tesis describe exactamente dos disparadores
  (F5 y el cambio a Post) y `no-reintroducir.md` prohíbe la toolbar; agregar un tercer camino
  sería una vía más para lo mismo, justo lo que la rutina caza.
- **Un diálogo de progreso para el solve** (al estilo del `_PDFProgressDialog` de la Memoria).
  El solve es una llamada sincrónica a SciPy: para acompañarlo con una barra habría que moverlo
  a un thread y eso cambia el modelo de concurrencia de toda la fase. El cursor de espera cubre
  el 90 % del problema a coste cero. Si alguna vez se quiere, va como propuesta al autor.
- **Unificar el nombre de la sub-pestaña educativa** (Pre dice `🎓 Educacion`, Proceso dice
  `🎓 Modulos Educativos`, y en Proceso el Notebook tiene **una sola** pestaña, o sea un control
  que no controla nada). Es incoherencia real entre fases, pero es cambio puramente visual y ya
  gasté los 3 pendientes visuales de la sesión. Al BACKLOG.
- **Tocar el `.tex` del Anexo A**: acá la tesis tenía razón y el software estaba mal, así que no
  hubo nada que corregir del lado del documento. Las dos correcciones pendientes del Anexo A
  siguen en el BACKLOG para el área 14 (necesitan `pdflatex`, que este sandbox tampoco tiene).

### Área siguiente

4 — Post-Proceso (`gui/postprocessing/*`: panel de detalles, probe, vista 3D).

---

## Sesión 04 — 2026-09-08 22:40 UTC — Área: 4 — Post-Proceso

**Commit**: (este) · **Gates**: `run_gates` verde (97/97 módulos, 0 hex, **18**/18 tests) y
también `run_gates --con-gui` bajo `xvfb` (20/20, por el cambio en `mesh_canvas`) · además
smoke con Tk real del panel del Post, la Vista 3D (los 3 campos × los 2 modos, más la caída a
suavizado) y el `Ctrl+C` del probe

> Nota de entorno: igual que la sesión 03, el sandbox vino **sin el stack y sin `tkinter`**.
> Gate corrido con un venv de `python3.12` del sistema + `pip install -r requirements.txt`,
> según la receta de [RUTINA.md](RUTINA.md) §8. Sin tocar `requirements.txt`. **Tampoco hay
> `pdflatex` ni `latexmk`**, así que las correcciones de `tesis/` siguen sin poder tomarse
> (§6 exige compilar antes de pushear); se sumó una tercera al BACKLOG del área 14.

### Qué se hizo y por qué

El hallazgo central es un **error numérico visible**: la vista 3D dibujaba el campo crudo
transpuesto dentro de cada elemento.

- `gui/postprocessing/surface_3d_viewer.py` — **la grilla del visor se armaba con
  `np.meshgrid(xi, eta)`**, es decir el `indexing="xy"` por defecto, que indexa `[j_η, i_ξ]`.
  Pero la Z del **modo crudo** sale de `fem/probe_query.py::compute_raw_grids`, que indexa
  `[i_ξ, j_η]` (su `_get_dN_at_grid` llena `dN_at_grid[i, j]` con `i`→ξ y `j`→η), igual que
  el rasterizador del contorno 2D (`canvas_raster` usa `indexing="ij"` explícito).
  Resultado: en **Crudo** la superficie 3D mostraba el campo **transpuesto respecto de la
  geometría** dentro de cada elemento. Verificado en el ejemplo Cook Q4: los valores de la
  grilla coinciden con `compute_raw(ξ_i, η_j)` con error 2e-17, y con la convención vieja el
  desvío llegaba al 19 % del rango del elemento. El modo **suavizado no lo sufría** (X, Y y Z
  salían del mismo `meshgrid`), por eso pasaba desapercibido: hay que estar en crudo y con un
  campo no simétrico para verlo.
  **Por qué importa**: es justo el modo que la tesis destaca en el pie de la
  `\autoref{fig:vista3d}` y el que materializa la discontinuidad C⁰ del MEF — el alumno estaba
  mirando un campo que no era el de esa geometría.
  Arreglo: `natural_grid(n)` (`indexing="ij"`, con la convención documentada arriba del
  módulo), y toda la geometría pasa por `element_grid_xy`.
- `surface_3d_viewer` — **la N de la grilla se evalúa una vez por malla**
  (`shape_matrix_at_grid`, cacheada por `(tipo, n)`) en lugar de `(n+1)²` veces **por
  elemento**: las coordenadas naturales son las mismas para todos los elementos. El doble
  bucle Python `for r: for c: N_func(...)` desapareció de los dos renders.
  **Medido** en Cook 16×16 Q9 (256 elementos, n=8): **0,156 s → 0,003 s** por repintado solo
  en armar la geometría; en Cook 32×32 son ~83 000 llamadas a las funciones de forma que ya no
  se hacen. La versión legible elemento a elemento de `fem/` no se tocó (esto es `gui/`).
- `surface_3d_viewer::_draw_colorbar` — **escala de color graduada** al costado de la
  superficie, con `<campo> [<unidad del proyecto>]` y los ticks de `fmt_escala`.
  **Por qué**: el 3D era la **única** vista de resultados sin referencia numérica del color —
  el alumno veía el arcoíris y no podía decir cuánto vale el rojo. La tesis apoya la elección
  de *jet* precisamente en que «se compensa con la escala numérica graduada junto al contorno»
  (`03_diseno_implementacion`), así que la vista lo estaba incumpliendo. La decisión de **ejes
  limpios** sigue intacta: vale para el cubo 3D, no para la leyenda (por eso NO es una decisión
  congelada revertida). `_clear_colorbar` la retira antes de cada repintado: `ax.clear()` no la
  borra y cada refresco apilaba un eje nuevo, achicando la superficie.
- `config/settings.py::fmt_escala` — nuevo, y `MeshCanvas._fmt_colorbar_value` **delega** ahí.
  **Por qué**: la colorbar del lienzo y la del 3D formateaban el mismo número con reglas
  distintas si cada una traía la suya. Ahora es fuente única, al lado de `fmt` (la casa de los
  formatos numéricos, regla dura 8). El readout de rango del header del 3D pasó de
  `{v:.3g}` **sin unidad** a `fmt_escala` **con unidad**.
- `surface_3d_viewer` — **modo crudo sin datos ahora cae a suavizado y lo dice**. Antes
  mostraba «(sin datos para el campo activo)» sobre un visor vacío, mientras el contorno 2D
  —ante exactamente el mismo fallo— ya caía a suavizado (`post_tab._on_result_changed`). Dos
  respuestas distintas al mismo problema en la misma pantalla. Ahora el título dice
  «SUAVIZADO … (sin datos crudos disponibles)» y la barra de estado explica el siguiente paso.
- `gui/postprocessing/post_tab.py` — **`Factor de escala` y `Número de niveles` ya no revientan
  el callback**. Eran un `DoubleVar` y un `IntVar`: tipear `2,5` (la coma decimal de un Excel
  en español), `abc` o dejar el campo vacío hace que `.get()` levante `TclError` **dentro del
  handler de Tk** — el traceback iba a la consola, el alumno no veía nada, la deformada no
  cambiaba y el campo se quedaba mostrando un valor que no se estaba usando. Ahora son
  `StringVar` y se leen con `_leer_factor_escala` / `_leer_niveles_isolineas`: toleran la coma
  (`to_float_flex`, la **misma vía** que los editores de celda del Pre-Proceso desde la sesión
  02), acotan los niveles al rango del Spinbox (que era editable, así que `500` pasaba), avisan
  nombrando el valor rechazado y el formato aceptado, y **devuelven el control al último valor
  bueno**. Los dos controles se aplican además con `<FocusOut>`, no solo con Enter.
  **Por qué**: eran dos callejones sin salida con excepción tragada, en el único par de campos
  de texto de la fase, y contradecían la regla que la sesión 02 fijó para el resto del programa.
- `post_tab::_encolar_aviso` / `_estado_visualizacion` — el aviso de un control rechazado se
  emite al **final** del repintado, no en el lector. **Por qué**: los lectores corren al
  principio de `_on_result_changed` y el método **siempre** termina con un `Visualizando: …`,
  así que el `set_status` del aviso quedaba tapado en el mismo instante — el arreglo de arriba
  habría sido invisible en el flujo real. Detectado probando con Tk real, no leyendo el
  código: en el test unitario el lector se llama suelto y el aviso "se veía". Un valor
  rechazado importa más que el nombre del campo que se muestra, así que gana el aviso, y no se
  pega al repintado siguiente.
- `config/settings.py` — `ISOLINE_COUNT_MIN/MAX/DEFAULT`: el rango del control estaba escrito
  a mano en el `Spinbox` y el validador necesitaba la misma fuente.
- `gui/postprocessing/probe_overlay.py::tsv_headers` — el `Ctrl+C` del lienzo copiaba
  encabezados con las **claves internas en inglés y sin unidades** (`x`, `sigma_x`,
  `von_mises`), mientras la tabla de resultados —el otro `Ctrl+C` del Post— copia encabezados
  en español con la unidad del proyecto. Ahora dice `σx [MPa]`, `Von Mises [MPa]`, `Elemento`,
  `ξ`, `η`. Los **números** siguen con toda la precisión (no `fmt`): lo que se pega en una
  planilla se usa para recalcular.
- `probe_overlay` — **`Ctrl+C` dejó de ser mudo** cuando no hay nada que copiar: fuera de la
  malla, sin haber movido el cursor sobre el lienzo, o sin valores en el punto. La barra de
  estado anuncia «Ctrl+C: copiar» desde que se activa el probe, así que una tecla anunciada que
  no hace nada ni explica por qué es un callejón sin salida (RUTINA §7). El mensaje de éxito
  además nombra qué se copió (`Nodo N7` / `Punto de Gauss PG#3` / `Punto del elemento #4`).
- `gui/postprocessing/details_panel.py` — los **5 literales `"white"`** del círculo de Mohr
  (bordes de los marcadores de σ1, σ2, (σx,τxy) y del estado isótropo) pasaron a
  `MOHR_MARKER_EDGE_COLOR` en `config/settings.py`. Eran ítem del BACKLOG del área: esquivaban
  la auditoría de hex de `run_gates` (que busca `#RRGGBB`) pero incumplían igual la regla dura 2.
- **`except Exception` del área: revisados los 35, cambiados 8.** Dejan traza con
  `traceback.print_exc()` (convención de `undo_stack` / `post_tab` / `mesh_canvas`): los **3**
  del refresco de la Vista 3D en `post_tab` (`update_solution` tras re-solve, `refresh` al
  cambiar de campo, y el `lift`+`refresh` al reabrirla) — si fallaban en silencio, el visor
  seguía mostrando **la solución o el campo anteriores** sin decirlo, que es peor que estar
  cerrado, así que además avisan con `_avisar_3d_desactualizada`; el retorno al Pre-Proceso
  cuando se cancela el reporte de salud; el `compute_raw_grids` del visor; el
  `_copy_values_tsv`; el callback de cierre del `DetailsPanel` (es quien sincroniza
  `_details_open`: si falla mudo, el probe cree que el panel sigue abierto y deja el hover
  pausado para siempre); y `post_tab._get_units` visto desde el 3D. Los otros 27 son legítimos
  (`after_cancel`, `destroy`/`unbind` de teardown, `tooltip.hide`, `set_status` en tests
  headless, sondeo de la API privada de matplotlib para los paneles 3D, `tight_layout`).
- `gui/preprocessing/mesh_canvas.py::_draw_highlight` / `_hit_test_potential_edge` — el
  segundo ítem del BACKLOG que le tocaba al área (compartido con el área 1): los dos usaban
  `world_to_screen(node.x, node.y)` sobre las coordenadas **sin deformar** mientras el resto
  del lienzo usa `_get_node_screen_pos` (que aplica `deform_scale·u`). Ahora los dos usan
  `_get_node_screen_pos`. **Por qué**: hoy es inocuo —el Post no tiene selección y
  `_on_tab_changed` llama `clear_highlights()` al entrar— pero dejar dos criterios de
  posicionamiento conviviendo en el mismo archivo es la trampa que produjo el bug de la grilla
  transpuesta de esta misma sesión: una convención divergente que nadie ve hasta que alguien la
  consume. Cerrado, no anotado.
- `tests/test_post_inspection.py` — nuevo (11 casos, sin display: `PostProcessTab` y
  `ProbeOverlay` con `object.__new__` y dobles de las variables de Tk, como las sesiones 01–03).
  Sumado a `run_gates`. Cubre la convención de índices contra el motor real, el cacheo de la N
  por tipo de elemento, las dos lecturas validadas, los encabezados del TSV y la delegación de
  `fmt_escala`. Verificado que **falla sin el arreglo**: con `indexing="xy"` la comparación
  geometría↔campo se va a 1.2e+01 de error. El test además comprueba que la **transpuesta sí
  difiere** en el modelo elegido — si no, no distinguiría el bug del arreglo.

### Errores encontrados y corregidos

- **Campo crudo transpuesto en la vista 3D** (el principal, arriba). Error numérico visible,
  no cosmético: hasta 19 % del rango del elemento en el ejemplo Cook.
- **`TclError` tragado en los dos campos numéricos del Post**: `2,5`, `abc` o vacío mataban el
  callback sin ningún mensaje, y el control quedaba mintiendo sobre el valor en uso.
- **`500` niveles de isolíneas aceptados** por un Spinbox editable cuyo rango 3–30 no se
  validaba: isolíneas ilegibles y un marching squares carísimo en cada repintado.
- **La Vista 3D podía quedar mostrando la solución anterior** (o un campo distinto del que
  dice el panel) si un refresco fallaba: tres `except Exception: pass`.
- **`Ctrl+C` mudo** en el lienzo del Post cuando no había punto bajo el cursor, con la barra de
  estado anunciando ese mismo atajo.
- **La Vista 3D en crudo sin datos** mostraba «(sin datos)» donde el contorno 2D, ante el mismo
  fallo, ya caía a suavizado.
- **La colorbar del 3D no existía** y el rango se mostraba sin unidad y con formato propio.
- Verificado todo con Tk real bajo `xvfb`: los 3 tipos de campo × los 2 modos del visor, la
  caída a suavizado forzada, que la figura queda en 2 ejes tras 6 repintados (la colorbar no se
  apila), el cierre limpio del Toplevel, y los mensajes de los dos controles.

### DECISIÓN CONGELADA REVERTIDA

Ninguna. La colorbar del 3D **no** revierte la decisión de «ejes sin ruido visual»: esa regla
es sobre el cubo 3D (ticks, números, paneles de fondo, que siguen ocultos), no sobre la
leyenda del campo. `no-reintroducir.md` no tiene ninguna fila sobre la escala de color del
visor, y la tesis pide explícitamente esa escala graduada como contrapeso de *jet*. El
capítulo [canvas-preproceso.md](../convenciones/canvas-preproceso.md) lo deja escrito.

### Pendientes visuales para el autor

1. **Vista 3D en modo Crudo** (lo más importante de la sesión). `Ctrl+E` → `F5` → **🧊 Vista
   3D** → **σx** (no von Mises, que es casi simétrico) → **Crudo**: la superficie debería
   coincidir con el contorno 2D de σx del lienzo (mismos rojos donde el lienzo tiene rojos).
   Antes el relieve estaba **transpuesto dentro de cada elemento** respecto del contorno 2D.
   Comparar los dos lado a lado es la forma más rápida de verlo. Revertir: `git revert` de este
   commit.
2. **Escala de color de la Vista 3D**. En la misma ventana: a la derecha de la superficie debe
   aparecer una colorbar con `σx [MPa]` (la unidad del proyecto) y los ticks con el **mismo
   formato** que la colorbar del lienzo (`2.50e+07` para magnitudes grandes). Al cambiar de
   campo (VM ↔ σx ↔ Ux) o de modo, la superficie **no debe achicarse**: si se encoge un poco en
   cada cambio, `_clear_colorbar` no está retirando la anterior. El header dice ahora
   «rango: [-106.8, 160.8] MPa».
3. **Los dos campos numéricos del panel del Post**. Con la deformada activa, tipear `2,5` en
   *Factor de escala* y Enter → la deformada se amplifica (antes: «valor inválido» invisible y
   nada se movía). Tipear `abc` → la barra de estado dice «Factor de escala: valor inválido —
   «abc» no es un número positivo…» y el campo **vuelve solo** al último valor bueno. En
   *Número de niveles*, tipear `500` → queda en `30` y lo avisa.

### Descartado

- **Unificar el formato de los desplazamientos entre la tabla del Post y las etiquetas del
  lienzo.** La tabla usa notación científica (`5.12345e-04`, decisión documentada en el código
  por el ancho de columna) y el lienzo `fmt(v, "displacement")` (`0.00051`): el mismo número se
  lee distinto en dos vistas de la misma fase. Cambiar cualquiera de los dos es una decisión de
  presentación con impacto visual en toda la tabla, y ya gasté los 3 pendientes visuales. Al
  BACKLOG.
- **Corregir el pie de la `\autoref{fig:vista3d}` del Anexo A**, que dice que el control
  Crudo↔Suavizado «**interpola** entre los valores por punto de Gauss y el campo nodal
  promediado». Es falso: es un **toggle binario**, y el slider continuo fue eliminado a
  propósito («los estados intermedios confundían», documentado en el docstring del visor). Es
  el caso «tesis desactualizada» de §6, pero este sandbox no tiene `pdflatex` ni `latexmk` y §6
  exige compilar antes de pushear. Al BACKLOG del área 14, junto a las otras dos.
- **Cerrar la Vista 3D cuando un refresco falla.** Sería lo más honesto (una vista que miente
  es peor que una cerrada), pero cerrarle al alumno una ventana que abrió a propósito, por un
  fallo que puede ser transitorio, es peor UX que avisarle. Se avisa y se deja la decisión en
  sus manos.
- **Un `Ctrl+C` que copie el punto pinneado en vez del que está bajo el cursor.** Es el
  comportamiento documentado y hay un pin visible; cambiarlo sería una vía distinta para lo
  mismo. Solo se agregaron los mensajes que faltaban.

### Área siguiente

5 — Diálogos (`gui/dialogs/*`).

---

## Sesión 05 — 2026-09-09 00:35 UTC — Área: 5 — Diálogos

**Commit**: (este) · **Gates**: `run_gates` verde (97/97 módulos, **0 nombres sin definir**,
0 hex, **19**/19 tests) y también `run_gates --con-gui` bajo `xvfb` (21/21) · además smoke con
Tk real del `AboutDialog`, del `MaterialDialog` (validación live + preselección) y del
`HealthReportDialog` (rueda, Re-validar, cierre)

> Nota de entorno: igual que las sesiones 03 y 04, el sandbox vino **sin el stack y sin
> `tkinter`**. Gate corrido con un venv de `python3.12` del sistema + `pip install -r
> requirements.txt`, según la receta de [RUTINA.md](RUTINA.md) §8. Sin tocar
> `requirements.txt`. **Tampoco hay `pdflatex` ni `latexmk`**: las tres correcciones de
> `tesis/` siguen sin poder tomarse (§6 exige compilar antes de pushear).

### Qué se hizo y por qué

El hallazgo central es un **crash real en un ítem de menú** que ningún gate podía ver, y la
respuesta fue tanto arreglarlo como cerrar la clase entera de bug con un gate nuevo.

- `gui/dialogs/about_dialog.py` — **`center_dialog` se usaba sin importarlo**. `Ayuda ▸ Acerca
  de EduFEM` levantaba `NameError` en el callback de Tk: la ventana se armaba (los widgets se
  empaquetan antes) pero moría al centrarse, así que aparecía **descolgada en la posición por
  defecto** y el traceback iba a `stderr` — invisible en el `.exe`, que no tiene consola.
  **Por qué pasó desapercibido**: `gate_imports` importa el módulo y el módulo importa bien;
  el `NameError` solo existe cuando se ejecuta el cuerpo del `__init__`. Verificado con Tk
  real: ahora centra en `450x350+225+175`.
- `tests/run_gates.py::gate_nombres` — **gate nuevo [2]**: nombres globales usados y nunca
  definidos, en los 97 módulos. Usa `symtable` de la stdlib, así que el análisis es **exacto**
  y no heurístico — aplica las reglas de scoping reales de Python (locales, parámetros,
  comprehensions, `global`/`nonlocal`, cierres) y compara cada símbolo global no asignado
  contra `dir(modulo)` **ya importado**, que incluye lo que traiga un `import *` (`about_dialog`
  hace `from ttkbootstrap.constants import *`). **Cero falsos positivos** sobre el repo entero.
  **Por qué**: sin linter, este es el bug que más barato se cuela y más caro sale — un botón
  de menú que revienta y nadie lo ve hasta que lo aprieta el alumno. Verificado en negativo:
  borrando el import, el gate escupe
  `gui/dialogs/about_dialog.py: 'center_dialog' usado en __init__() y nunca definido`.
- `education/mod05_stiffness.py` — el gate nuevo encontró **3 usos de `sp.` sin `import sympy`**
  (`sp.latex`, `sp.expand`+`sp.Add.make_args`, `sp.pretty`). Los tres estaban dentro de un
  `except Exception`, así que **M5 degradaba en silencio**: el integrando simbólico se mostraba
  como el `repr` crudo de la expresión en vez de LaTeX renderizado, el contador decía siempre
  **"0 términos · 0 chars LaTeX"**, y la ventana del integrando completo caía a `str(expr)` en
  lugar del pretty-print. Es área 8, pero es un error visible y se arregla en la misma sesión
  (RUTINA §1.3). `sympy` ya es dependencia declarada (`fem/symbolic_integrand.py` la importa a
  nivel de módulo), así que el arreglo es la línea que faltaba. Medido después: la entrada
  K(1,1) del elemento unitario da **5 términos** y `sp.latex` devuelve
  `\frac{218750 (\eta - 1)^{2}}{13} + …`.
- `gui/dialogs/health_report_dialog.py` — **la rueda del mouse dejó de atarse a toda la
  aplicación**. Era `canvas.bind_all("<MouseWheel>", …)` + `unbind_all` al cerrar, y este
  diálogo **no es modal a propósito** (para que el alumno corrija ítems con la lista a la
  vista). Tres consecuencias, las tres reproducidas con Tk real: (a) con el reporte abierto, la
  rueda sobre el `MeshCanvas` hacía zoom **y** scrolleaba la lista de fondo; (b) `<Destroy>`
  sube por el bindtag del toplevel, así que destruir el footer dentro de **🔄 Re-validar**
  disparaba el `unbind_all` y **la rueda dejaba de scrollear la lista** (medido: `bind_all`
  vuelve `''` después de re-validar); (c) al cerrar borraba el `<MouseWheel>` global de
  cualquier otro componente — hoy el visor de Teoría. Ahora es
  `self.dialog.bind("<MouseWheel>", …)`: el bindtag del toplevel ya está en los bindtags de
  todos sus descendientes, así que cubre la ventana entera y nada más. El `MaterialDialog` ya
  usaba el patrón correcto.
- `health_report_dialog::_on_goto` — **"📍 Ir al ítem" era una decoración inerte** para los
  issues con `target_kind="material"`. El mapeo `kind → (frame, tree)` solo cubre las 5 tablas
  del Pre-Proceso y los materiales no viven en ninguna: el handler caía en un `return` mudo.
  Afecta a `UNUSED_MATERIAL`, `SUSPICIOUS_YOUNG_MODULUS` y `GRAVITY_NO_DENSITY`, y en las dos
  últimas —no fixables— **ese botón era el único de la tarjeta**. Ahora deriva a
  `MaterialDialog(..., seleccionar=<nombre>)`, que es donde el propio hint educativo manda
  ("Asigna densidad en Modelo > Materiales"). Cualquier `kind` que el mapeo no conozca, y la
  fila que ya no existe, lo dicen en la barra de estado en vez de no hacer nada.
- `health_report_dialog::_on_fix` — **el auto-fix fallido era mudo**: `apply_autofix` devolvía
  `False` y no pasaba absolutamente nada, ni en la tarjeta ni en la barra. Ahora explica y
  sugiere el camino manual. El caso exitoso también avisa y **nombra 🔄 Re-validar**, porque el
  header (chips de conteo) y el footer siguen mostrando el reporte con el que se abrió el
  diálogo: sin ese aviso, corregir los 2 errores dejaba la ventana diciendo "✗ Errores críticos
  detectados · 2 error(es)". `_on_revalidate` pasó de `except Exception: return` a decir que el
  validador falló, y **siempre** informa el resultado (aunque la lista quede igual: si no,
  apretar el botón "no hace nada").
- `health_report_dialog::_disable_widget_recursive` — al corregir un issue, la tarjeta se
  deshabilitaba entera **incluido el "🎓 ¿Por qué es un problema?"**. Es justo lo que el alumno
  quiere leer después de arreglarlo, y quedaba inaccesible. Ahora ese botón se saltea.
- `gui/dialogs/material_dialog.py` — **`to_float_flex` en la validación y en Guardar**. Con
  `float()`, escribir `0,3` en ν (la coma decimal de un Excel en español, que el resto del
  programa ya acepta desde la sesión 02 en el spreadsheet y la 04 en el Post) dejaba el botón
  **Guardar gris para siempre y sin explicación**. Y como el único feedback documentado era el
  estado del botón, el alumno no tenía **ninguna** forma de saber cuál de los 4 campos lo estaba
  bloqueando: ahora `campos_invalidos()` es la fuente única y `_validate_live` **marca en rojo
  el Entry culpable** (`bootstyle="danger"`, `"default"` al volver a ser válido). No se
  reintroduce el status label —esa decisión sigue en pie—: el feedback vive en el propio
  control. Verificado con Tk real: `0,3` → `TEntry` + Guardar `normal`; `0,9` → `danger.TEntry`
  + Guardar `disabled`.
- `material_dialog::_remove_material` — **la confirmación nombra la consecuencia**. Borrar el
  material que usan todos los elementos preguntaba solo "¿Eliminar 'Acero'?" y dejaba N
  elementos apuntando a un nombre inexistente; el alumno se enteraba recién al resolver, con un
  `ELEM_MATERIAL_MISSING` crítico. Ahora cuenta los elementos afectados, dice que van a quedar
  sin material y recuerda el `Ctrl+Z`.
- `material_dialog` — kwarg keyword-only `seleccionar=`, para que el "Ir al ítem" del reporte
  abra el diálogo ya posicionado. Keyword-only a propósito: los 3 llamadores posicionales
  existentes no cambian.
- `gui/dialogs/dxf_import_dialog.py::_on_import` — **`stack.capture("importar DXF")` movido
  ANTES de `_apply_project_unit()`** (regla dura 4). Ese método reescala las coordenadas de
  **todos** los nodos existentes y cambia `unit_system`; capturar después dejaba esa conversión
  fuera del `Ctrl+Z`: importar un DXF eligiendo otra unidad y deshacer devolvía los elementos
  pero las coordenadas quedaban multiplicadas por el factor **para siempre**. El contraejemplo
  correcto ya estaba en el repo: `ElementTypeDialog._on_accept` captura después de la
  confirmación modal y antes de mutar.
- `dxf_import_dialog::_collect_polylines` — **cacheado por capa**. `_refresh_preview` cuelga de
  `<Configure>`, así que arrastrar el borde del diálogo releía y parseaba el DXF entero desde el
  disco decenas de veces. Y su `except Exception: return []` hacía que un archivo ilegible se
  viera **exactamente igual** que una capa vacía: el preview decía "no hay polilíneas cerradas
  de 4 vértices en la capa X", un diagnóstico falso. Ahora deja traza y el preview distingue
  los dos casos.
- `gui/dialogs/gravity_dialog.py` — `to_float_flex` en lugar del `.replace(",", ".")` a mano
  (una sola regla de número en toda la app), y el error pasó de `"gx y gy deben ser numeros
  validos"` a **nombrar el campo y el texto rechazado** (`gx: «hola»`), como el resto del
  programa desde la sesión 02.
- `gui/dialogs/units_dialog.py` — cuando la conversión no se puede aplicar, el status decía
  `Unidades: X` a secas, indistinguible del caso convertido; ahora dice **"(solo la etiqueta:
  los valores no se pudieron convertir)"**.
- **`except Exception` del área: revisados los 33, cambiados 9.** Dejan traza con
  `traceback.print_exc()` (convención de `undo_stack` / `post_tab` / `mesh_canvas`): los 4
  `stack.capture` de `health_report`, `material_dialog`, `gravity_dialog`, `units_dialog` y
  `dxf_import_dialog` —si el snapshot falla, esa acción queda fuera del `Ctrl+Z` y el alumno
  tiene que saberlo—, los 3 refrescos de la ventana principal (`_refresh_all_tabs` mudo deja las
  tablas mostrando el modelo de antes de la corrección o los números del sistema de unidades
  viejo bajo el encabezado nuevo), el `notebook.select(0)` del "Volver al Pre-Proceso" (el botón
  promete una navegación) y el `readfile` del preview DXF. Los otros 24 son legítimos
  (`webbrowser.open`, `grab_set`, teardown de video, `tooltip`, guards de widgets destruidos).
  **Revisados: 110 de 274.**
- `tests/test_dialogs.py` — nuevo (26 casos, sin display: los diálogos con `object.__new__` y
  dobles de las variables de Tk, como las sesiones 01–04). Sumado a `run_gates`. Cubre el import
  de `center_dialog`, la coma decimal y el campo culpable del `MaterialDialog`, el conteo de
  elementos afectados por el borrado, la firma keyword-only de `seleccionar`, la derivación de
  los issues de material, los dos caminos de `_on_fix`, la ausencia de `bind_all`/`unbind_all`,
  el orden `capture` → `_apply_project_unit` y la coma decimal de la gravedad. Verificado que
  **falla sin los arreglos**.

### Errores encontrados y corregidos

- **`NameError` en `Ayuda ▸ Acerca de EduFEM`** (el principal): `center_dialog` sin importar.
  Crash real en un ítem de menú, invisible en el `.exe`.
- **M5 degradaba en silencio** por 3 usos de `sp.` sin `import sympy`, los tres tapados por un
  `except Exception`: LaTeX crudo en vez de renderizado y "0 términos" siempre.
- **La rueda del mouse del reporte de salud secuestraba toda la aplicación**, y su propia lista
  dejaba de scrollear después de 🔄 Re-validar.
- **"📍 Ir al ítem" no hacía nada** en los 3 issues de material — y en 2 de ellos era el único
  botón de la tarjeta.
- **"🔧 Corregir" y "🔄 Re-validar" mudos** en sus caminos de fallo.
- **El "🎓 ¿Por qué?" quedaba deshabilitado** justo después de corregir el issue.
- **`ν = 0,3` bloqueaba el `MaterialDialog` para siempre**, con un botón gris que no decía qué
  campo estaba mal.
- **Borrar un material en uso no avisaba** que dejaba N elementos sin material.
- **El `Ctrl+Z` del import DXF no revertía la conversión de unidades** (regla dura 4).
- **Un DXF ilegible se reportaba como "capa sin polilíneas"**, y el preview releía el archivo
  entero en cada evento de resize.

### DECISIÓN CONGELADA REVERTIDA

Ninguna. La marca en rojo del Entry inválido del `MaterialDialog` **no** revierte el "sin status
label": esa decisión es sobre no agregar un widget de texto al diálogo, y sigue en pie — el
feedback se puso en el propio control. La fila de `no-reintroducir.md` se actualizó para dejarlo
escrito.

### Pendientes visuales para el autor

1. **Diálogo de materiales con coma decimal** (lo más visible de la sesión). `Modelo ▸
   Materiales`, campo **ν**: tipear `0,3` → el botón **💾 Guardar cambios** debe quedar
   habilitado (antes: gris para siempre, sin explicación). Tipear `0,9` → el borde del Entry de
   ν se pone **rojo** y Guardar se apaga; volver a `0.3` y el borde vuelve a la normalidad.
   Probar los 4 campos. Revertir: `git revert` de este commit.
2. **Reporte de salud: la rueda y los botones**. `Ctrl+E`, borrar las restricciones, `F5` → en
   el diálogo *⚕ Salud del modelo*: (a) la rueda **sobre el lienzo de atrás** debe hacer solo
   zoom, sin mover la lista del reporte; (b) tocar **🔄 Re-validar** y comprobar que la rueda
   **sigue** scrolleando la lista (antes se moría ahí) y que la barra de estado dice cuántos
   errores quedan; (c) en un modelo con un material sin usar, **📍 Ir al ítem** debe abrir
   *Materiales* con ese material seleccionado (antes no hacía nada).
3. **M5 con el integrando simbólico**. Proceso → clickear un elemento **Q4** → `⑤ Rigidez`: la
   fórmula de K(i,j) debe verse **renderizada en LaTeX** y el contador decir un número real de
   términos (ej. `📏 K_(1,1): 5 términos · N chars LaTeX`). Antes salía el texto plano de la
   expresión Python y **siempre "0 términos"**.

### Descartado

- **Abrir el `MaterialDialog` como no-modal** para que conviva con el reporte de salud (que
  tampoco lo es). Hoy hace `grab_set` y funciona bien encima del reporte; quitarle el grab
  cambia el modelo de foco de un diálogo del menú Modelo por un caso de uso lateral.
- **Auto-revalidar el reporte después de cada 🔧 Corregir.** Reconstruiría la lista y haría
  desaparecer la tarjeta que el alumno está mirando en el mismo click. El diseño actual —tachar
  la tarjeta y dejar el botón Re-validar— es deliberado; solo faltaba **decir** que hay que
  tocarlo, y eso sí se agregó.
- **Descartar el snapshot de undo cuando `apply_autofix` devuelve `False`.** `UndoStack` no
  expone forma de tirar el último snapshot y agregarla es tocar `models/` (área 11) por un caso
  defensivo. Un nivel de undo de más pesa mucho menos que una mutación irreversible (regla dura
  4), y quedó anotado en el comentario.
- **Un `Escape` que cierre los diálogos y un `Return` que acepte.** Son 10 diálogos con
  semánticas distintas (el de salud es no modal, el `MaterialDialog` no tiene Aceptar, el de
  estilo de memoria devuelve `None` al cancelar) y ninguno lo tiene hoy: es una decisión de
  diseño transversal, no un fix. Al BACKLOG.
- **Unificar el `_LENGTH_DEFAULT_SYSTEM` del DXF con `config/units.py`.** El diccionario del
  diálogo duplica el mapeo longitud → sistema canónico, pero moverlo es área 13
  (interoperabilidad) y toca `config/`. Al BACKLOG.
- **Tocar `tesis/`**: el sandbox sigue sin `pdflatex` ni `latexmk` y §6 exige compilar antes de
  pushear. Las tres correcciones del Anexo A siguen en el BACKLOG del área 14.

### Área siguiente

6 — Ventana, menús, atajos, barra de estado (`gui/main_window.py`, `gui/widgets/*`).

---

## Sesión 06 — 2026-09-09 02:10 UTC — Área: 6 — Ventana, menús, atajos, barra de estado

**Commit**: (este) · **Gates**: `run_gates` verde (97/97 módulos, 0 nombres sin definir, 0 hex,
**20**/20 tests) y también `run_gates --con-gui` bajo `xvfb` (22/22) · además dos smokes con Tk
real: la ventana completa (F8, Ctrl+S, F5, breadcrumb, layout de Proceso) y las teclas
`Escape` / `Return` de seis diálogos

> Nota de entorno: igual que las sesiones 03–05, el sandbox vino **sin el stack y sin
> `tkinter`**. Gate corrido con un venv de `python3.12` del sistema + `pip install -r
> requirements.txt`, según la receta de [RUTINA.md](RUTINA.md) §8. Sin tocar
> `requirements.txt`. **Tampoco hay `pdflatex` ni `latexmk`**: las correcciones de `tesis/`
> siguen sin poder tomarse (§6 exige compilar antes de pushear) y esta sesión le sumó una
> cuarta al Anexo A.

### Qué se hizo y por qué

El hallazgo central es una **pérdida de datos**: los tres flujos que destruyen el modelo seguían
adelante aunque el guardado que el alumno acababa de pedir no hubiera ocurrido.

- `gui/main_window.py::_confirm_discard_changes` — **nuevo**, y `_on_new_project`,
  `_on_load_example` y `_on_exit` pasan por él. `_on_save_project`, `_on_save_as_project` y
  `_save_to_file` devuelven ahora `bool`.
  **Por qué**: los tres preguntaban «¿guardar los cambios?» por separado —con tres redacciones
  distintas— y los tres llamaban `self._on_save_project()` **ignorando el resultado**. Si el
  proyecto nunca se había guardado, ese método deriva en `_on_save_as_project`, y **cancelar el
  filedialog no guardaba nada**: el flujo seguía, `project.reset()` (o `root.destroy()`) corría
  igual y el modelo se perdía sin un solo mensaje. Lo mismo si fallaba la escritura: el
  `showerror` avisaba y a continuación se destruía el modelo de todos modos. Es la peor clase de
  acción destructiva —el alumno acababa de pedir explícitamente que no pasara— y es la regla 4
  del canon leída desde la UX: si no hay forma de volver, no puede pasar en silencio. La
  confirmación única usa el formato `Sí → / No → / Cancelar →` que ya usaba el import de modelo.
- `main_window::_on_save_project` — **`Ctrl+S` sin cambios dejó de ser mudo**. El ítem de menú
  está gris en ese estado (lo sincroniza el `postcommand`), pero el **atajo se dispara igual** y
  no pasaba absolutamente nada. Ahora lo dice.
- `main_window::_on_toggle_ortho` — **`F8` fuera del modo dibujo era completamente invisible**.
  El indicador `ORTHO` de la barra solo se muestra cuando además está activo el modo dibujo, así
  que el toggle no aparecía por ningún lado: el alumno pulsaba la tecla, la pantalla no cambiaba
  y el estado se revelaba recién al entrar en dibujo. Ahora siempre avisa, y fuera del dibujo
  agrega dónde se aplica («se aplica al dibujar elementos (tecla D)»). Es el ejemplo de manual
  del «estado invisible» de [RUTINA.md](RUTINA.md) §7.
- `main_window::_on_fullscreen` — el flag `_is_fullscreen` se invertía **antes** de que Tk
  aceptara el cambio: ante `TclError` quedaba desincronizado y el siguiente `F11` pedía lo
  contrario de lo que se ve. Ahora se actualiza solo si Tk aceptó, y el aviso nombra la tecla de
  salida **porque en pantalla completa desaparece la barra de menús**, que es donde está escrita.
- `main_window::_on_help` — **`F1` dejó de prometer un manual inexistente**. Decía «Manual de
  usuario próximamente» y derivaba a los atajos; los atajos no son un manual (no dicen en qué
  orden se arma un modelo ni dónde vive cada cosa). Ahora recorre las tres fases nombrando la
  ubicación real de cada acción (los 3 menús, la tecla D, F5, `Ctrl+Z`, el badge de salud). No es
  una feature nueva: es el ítem de menú que ya existía, cumpliendo lo que promete.
- `main_window::_on_shortcuts` — la ventana `Ctrl+/` **no listaba las teclas que el alumno más
  usa**: faltaban `Supr` (borrar la selección), `Esc`, `Ctrl+C`, `Ctrl+V` y `Ctrl+A`, que se
  bindean en el canvas y en las tablas y no en `main_window` — el canon solo pedía sincronizar
  `_bind_shortcuts` con `_on_shortcuts`, y por eso se colaron. Además `Ctrl+E` figuraba bajo
  **Archivo**, un menú donde *Cargar Ejemplo* no está (vive en **Ayuda**): la misma clase de
  error que la sesión 03 arregló en los mensajes del launcher. Y se acentuaron las palabras del
  bloque de modelado.
- `gui/dialogs/_dialog_helpers.py::bind_dialog_keys` — **nuevo**, y aplicado a los **10**
  diálogos: el ítem `[5 / 6]` del BACKLOG. Ninguno respondía a `Escape` ni a `Return`. La tabla
  completa quedó en `arquitectura.md`; el resumen: `Escape` = *salir sin cambiar nada*, siempre
  lo mismo que la X del Toplevel; `Return` = **la** acción primaria, y solo cuando hay una sola y
  pulsarla sin querer no rompe nada. Por eso `HealthReportDialog` y `pdflatex_missing_dialog`
  **no atan Return**: en el primero las dos salidas son decisiones opuestas (corregir vs.
  resolver igual) y en el segundo la acción principal abre el navegador. En `DxfImportDialog`
  Return solo importa si el botón está habilitado (arranca `disabled` hasta que se lee el DXF) y,
  si no, lo dice en el pie del preview. En `MaterialDialog` Return guarda **solo** si los 4
  campos son válidos, y si no repinta el rojo y **nombra el campo culpable** en la barra de
  estado (`_FIELD_LABELS` pasó a ser fuente única del form y del aviso). El handler devuelve
  `"break"`: sin eso el `Return` de un `Entry` seguiría subiendo por los bindtags.
- `gui/processing/proc_tab.py` — el ítem `[3 / 6]`: **desapareció el `ttk.Notebook` de una sola
  pestaña**. Un Notebook con una pestaña es un control que no controla nada, y encima repetía
  «módulos educativos» **tres veces** en la misma pantalla (subtítulo del banner + pestaña +
  header del panel). Ahora el panel cuelga directo del frame de la fase, el subtítulo describe la
  **fase** —`Del elemento al sistema K·u = F · F5 resuelve`, que además era la única pantalla
  donde no estaba escrito cómo se resuelve— y el header del panel se queda con el nombre.
  `pre_tab` sí conserva su Notebook (ahí conviven 5 tablas + Educación) y su pestaña pasó a
  `🎓 Educación`, acentuada como el resto.
- `main_window::_build_status_bar` — **tooltips en los 8 chips del breadcrumb y en el badge de
  salud**. Los glifos `Ⓜ ① ② …` son clickeables y no decían qué abren; el nombre sale de
  `module_launcher.module_label` (nunca la key interna) y el tooltip agrega `Ctrl+N` para M1..M7,
  que M0 no tiene. Reusa `gui/widgets/tooltip.py`, que ya existía.
- `main_window::_build_recent_menu` — dos proyectos con el **mismo nombre de archivo** en
  carpetas distintas (`viga.edufem` de dos TPs) se veían como dos entradas idénticas: no había
  forma de elegir. Ahora, y **solo** en ese caso, la entrada nombra su carpeta.
- `main_window::_on_export_pdf` — el `os.startfile` del «¿Abrir el PDF ahora?» estaba **dentro
  del `try/except: pass` que envolvía también al `askyesno`**: en cualquier sistema que no sea
  Windows (y ante cualquier fallo del handler del `.pdf`) el «Sí» del alumno no abría nada ni
  decía por qué. Ahora la pregunta está fuera y el fallo de apertura deja traza y nombra la ruta.
- **`except Exception` del área: revisados los 43, cambiados 13.** Dejan traza con
  `traceback.print_exc()` (convención de `undo_stack` / `post_tab` / `mesh_canvas` / `dialogs`):
  el refresco final de `_on_state_restored` (si falla mudo, el `Ctrl+Z` **parece no haber hecho
  nada**: la UI sigue mostrando el modelo de antes), el `validate_project` del badge (que se
  queda diciendo «Modelo sano» sobre un modelo que ya no se validó), el `wire_canvas` de cada
  fase y la suscripción del breadcrumb (sin ellos los paneles educativos no reaccionan a la
  selección), las teclas que quedaban mudas (`F` de ajustar vista, `D` de dibujar —el acceso
  principal al modo dibujo—, los dos eslabones de la cascada de `Escape`, el chip del
  breadcrumb), los dos del PDF (snapshot del proyecto y tensiones por elemento), el
  `_load_project_from_path`, más el render del `WebpPlayer` (que ya paraba el loop, así que la
  traza sale **una** vez) y el `on_closed` de `CanvasOverlay` (si falla, el overlay se ve cerrado
  pero su loop de animación sigue repintando). Los otros 30 son legítimos (`iconbitmap`, warmup
  de mathtext, `focus_get`, teardown de Toplevels, `after_cancel`, el walk de widgets de
  terceros). **Revisados: 153 de 274.**
- `tests/test_main_window.py` — nuevo (20 casos, sin display: `MainWindow` con `object.__new__`
  y dobles mínimos, como las sesiones 01–05). Sumado a `run_gates`. Cubre los cuatro caminos de
  la confirmación de descarte (guardado OK / guardado cancelado / Cancelar / No), que los tres
  flujos destructivos comparten la puerta y que ninguno volvió a preguntar por su cuenta, que
  los tres métodos de guardado declaran `-> bool`, los avisos de `Ctrl+S` / `F8` / `F11`, la
  cobertura de la ventana de atajos contra las teclas reales, el `Ctrl+E` bajo Ayuda, que `F1`
  no vuelve a decir «próximamente», el contrato de `bind_dialog_keys`, que los 10 diálogos atan
  Escape y que los **dos sin default seguro no atan Return**, el Return guardado del
  `MaterialDialog`, la desambiguación de recientes y que no vuelva el Notebook de una pestaña.

### Errores encontrados y corregidos

- **Pérdida de datos al cancelar el guardado** (el principal, arriba): *Nuevo Proyecto*,
  *Cargar Ejemplo* y *Salir* destruían el modelo aunque el guardado que el alumno pidió no
  hubiera ocurrido.
- **`F8` invisible fuera del modo dibujo** y **`Ctrl+S` mudo sin cambios**: dos teclas que no
  producían ningún cambio en pantalla.
- **`F11` desincronizaba `_is_fullscreen`** si Tk rechazaba el atributo.
- **`F1` prometía un manual inexistente.**
- **La ventana `Ctrl+/` no listaba `Supr`, `Esc`, `Ctrl+C`, `Ctrl+V` ni `Ctrl+A`**, y ubicaba
  `Ctrl+E` en un menú donde *Cargar Ejemplo* no está.
- **Los 8 chips del breadcrumb y el badge de salud eran clickeables sin decir qué hacían.**
- **Dos recientes con el mismo nombre de archivo eran indistinguibles.**
- **El «¿Abrir el PDF ahora?» se comía el «Sí»** cuando `os.startfile` no existía o fallaba.
- **13 `except Exception` mudos** en caminos que el alumno recorre (arriba el detalle).
- Verificado todo con Tk real bajo `xvfb`: la ventana abre con el panel de Proceso sin Notebook,
  `Escape` cierra About / Unidades (sin convertir) / Materiales, `Return` acepta en Análisis
  (cambia TP↔DP) y en Gravedad (con `1,5` → `gx = 1.5`), `Escape` en el reporte de salud devuelve
  `result="cancel"`, y el Enter con `ν = 0,9` inválido escribe «Revisá Coef. de Poisson ν antes
  de guardar el material».

### DECISIÓN CONGELADA REVERTIDA

Ninguna. El `Notebook` de una sola pestaña de Proceso **no** era una decisión congelada (no tenía
fila en `no-reintroducir.md` ni motivo escrito en ningún capítulo); el ítem `[3 / 6]` del BACKLOG
pedía justamente decidirlo. Ahora sí tiene fila, para que nadie lo reponga. Tampoco se tocó la
regla de los **3 menús**: no se agregó ninguna entrada de menú en toda la sesión.

### Pendientes visuales para el autor

1. **Proceso sin Notebook.** Pestaña **⚙ PROCESO**: el panel de módulos M1…M7 debe arrancar
   pegado al banner, sin la pestaña `🎓 Modulos Educativos` encima. El subtítulo del banner ahora
   dice «Del elemento al sistema K·u = F · F5 resuelve». Verificar que los botones no queden
   apretados en 1080p. Revertir: `git revert` de este commit.
2. **Escape y Return en los diálogos.** En Unidades, Gravedad, Tipo de Elemento, Tipo de Análisis
   y Acerca de: Escape cierra sin aplicar, Enter acepta. En Materiales, Enter guarda y con un
   campo en rojo **no** guarda (lo dice nombrando el campo). En el reporte de salud, Escape
   vuelve al Pre-Proceso y **Enter no hace nada**, a propósito. De paso: con el modelo
   modificado, `Ctrl+N` → **Sí** → cancelar el *Guardar Como* debe **volver al modelo intacto**.
3. **Las dos ventanas de texto de Ayuda.** `F1` y `Ctrl+/` son `messagebox` largos y el sandbox
   no puede medirlos: verificar en 1080p que ninguno se corta ni se sale de la pantalla. Si el
   manual no entra, hay que partirlo o pasarlo a un Toplevel propio (decisión del autor).

### Descartado

- **Un guard `_exportando` en `_on_export_pdf`.** Nada impide lanzar dos compilaciones de la
  Memoria a la vez (el diálogo de progreso no hace `grab_set`, y eso es deliberado). Es una
  carrera real, pero el arreglo toca el flujo de la memoria (área 10) y hoy no produce ningún
  síntoma visible: cada worker trabaja sobre su propio snapshot. Al BACKLOG.
- **Limpiar `_breadcrumb_visited` en *Nuevo Proyecto*.** Los chips siguen marcados como
  visitados sobre un modelo vacío. Pero que el progreso sobreviva al cierre de un módulo es
  deliberado, y si es "progreso del alumno" o "progreso del modelo" no está decidido en ningún
  lado: **decide el autor**. Al BACKLOG.
- **Renombrar el ítem de menú *Manual de Usuario*.** Sería lo más honesto si el contenido fuera
  una guía rápida, pero la tabla `tab:atajos` del Anexo A de la tesis nombra `F1 → Manual`, y
  §6 exige compilar el `.tex` antes de pushear (este sandbox no tiene `pdflatex`). Se dejó el
  rótulo y se mejoró el contenido, que es la mitad que sí se puede verificar acá.
- **Tocar `tesis/`**: sigue sin haber `pdflatex` ni `latexmk`. Las tres correcciones del Anexo A
  siguen abiertas y ahora hay una cuarta: la ventana `Ctrl+/` lista más atajos que `tab:atajos`.
- **Un cuarto menú, una toolbar o un botón nuevo**: ni se evaluó. La barra sigue teniendo
  exactamente Archivo / Modelo / Ayuda, y esta sesión no agregó ninguna entrada.

### Área siguiente

7 — Módulos educativos M0–M3 (`education/mod00..mod03`, `overlay_module.py`).

---

## Sesión 07 — 2026-09-09 03:20 UTC — Área: 7 — Módulos educativos M0–M3

**Commit**: (este) · **Gates**: `run_gates` verde (97/97 módulos, 0 nombres sin definir, 0 hex,
**21**/21 tests) y también `run_gates --con-gui` bajo `xvfb` (23/23) · además un smoke con Tk
real que abre M0, M1, M2 y M3 sobre el ejemplo canónico Q4, deselecciona con el lienzo y
verifica el teardown (`ghost_geometry` restaurado, 0 click consumers, cadena de selección
desenganchada)

> Nota de entorno: igual que las sesiones 03–06, el sandbox vino **sin el stack y sin
> `tkinter`**. Gate corrido con un venv de `python3.12` del sistema + `pip install -r
> requirements.txt`, según la receta de [RUTINA.md](RUTINA.md) §8. Sin tocar
> `requirements.txt`. **Tampoco hay `pdflatex` ni `latexmk`** (ni `vendor/texlive`): las cuatro
> correcciones de `tesis/` siguen sin poder tomarse (§6 exige compilar antes de pushear).

### Qué se hizo y por qué

El hallazgo central es que **los overlays de M1, M2 y M3 seguían mostrando el elemento que el
alumno acababa de deseleccionar**, y que M2 además **fabricaba una `J = I`** cuando no había
ninguno. Las tres vistas que el alumno mira a la vez (lienzo, chip `#N` del panel de módulos y
overlay) se contradecían entre sí.

- `education/mod02_jacobian.py`, `mod03_b_matrix.py`, `mod01_iso_mapping.py` — **nuevo
  `on_element_deselected` en los tres**. El default de `CanvasOverlayModule` solo hace
  `set_element(None)` + `refresh_overlay()`, que es un `redraw()` del lienzo: la capa educativa
  se borra (su guard `if self.element is None: return`) pero **el overlay no se toca**. Click en
  zona vacía o `Esc` (las dos únicas vías, porque `is_any_overlay_active` suprime el
  second-click-deselects) apagaban el halo y el chip `#N`, y el overlay seguía mostrando la
  superficie det J, las matrices `∂N`/`Xₑ`/`J`, la cadena `∂N_ξη · J⁻¹ → ∂N_xy → B` y la línea
  `nodo 3` de un elemento que ya no estaba seleccionado. **Por qué importa**: es la definición
  de estado invisible de [RUTINA.md](RUTINA.md) §7 al revés — el estado cambió y la pantalla que
  el alumno está leyendo no. Medido con Tk real: los tres vuelven al estado «esperando
  elemento» y el teardown queda limpio.
- `mod02_jacobian._build_values_panel` — **el placeholder de J dejó de ser `np.eye(2)`**. El
  launcher abre los módulos **sin selección a propósito** (`Ctrl+2` con el lienzo limpio es un
  flujo normal: «cero diálogos modales», el módulo espera el click), y en ese estado el panel
  mostraba `J = [[1,0],[0,1]]` bajo el título `J en centro del elemento`: una identidad es un
  Jacobiano **perfectamente plausible**, con `det J = 1`, que nadie calculó, presentada como el
  valor en el centro de un elemento inexistente. Ahora el placeholder es **cero** y el título
  dice `sin elemento — clickeá uno en el lienzo` (muted), o sea el estado y el gesto que lo
  resuelve. Mismo tratamiento en el título de M3.
- `mod02._refresh_all` / `mod03._refresh_all` — **las matrices van a CERO cuando no se pueden
  calcular**, nunca se quedan con los números del elemento anterior. Era un `if mat is not None:
  set_matrix(mat)`: con `coords=None` el `set_matrix` no se llamaba y los valores quedaban
  **congelados** del elemento ido. Es la otra mitad del mismo defecto.
- `mod02._refresh_warning` — **borra el aviso de elemento degenerado cuando no hay elemento**.
  Salía por el guard `if ... or self.element is None: return` **sin limpiar el label**, así que
  el `⚠ Elemento degenerado: det J ≤ 0 en pg1 (…). Reordená los nodos en CCW` —un error
  accionable, que nombra una causa y un arreglo— quedaba en pantalla apuntando a nada.
- `mod02._build_formula_panel` — **la nota de remisión mandaba al alumno al módulo equivocado**.
  Decía `(las formulas de dNi/dxi se ven en M1 y M4)`: era cierto antes del **swap B↔D de
  2026-05** y es falso desde entonces — hoy **M4 es la matriz constitutiva D** (espectro de
  Poisson) y no muestra ninguna derivada de N. Ahora dice `(∂Nᵢ/∂ξ, ∂Nᵢ/∂η: ver ① Mapeo iso)`,
  idéntica a la de M3, con la **etiqueta visible del botón** y no la key interna — la misma
  regla que la sesión 03 aplicó a los mensajes del launcher. De paso deja de ser el único string
  del área sin acentos y con `dNi/dxi` en ASCII.
- `mod03_b_matrix.py` — la nota de M3 pasó de `(… ver M1)` a `(… ver ① Mapeo iso)`: una sola
  forma de nombrar un módulo en todo el área. Y el docstring de la clase + el comentario del tag
  decían **M4** (numeración previa al swap): corregidos, porque son la trampa que hace que el
  próximo agente busque la matriz B en el módulo de la D.
- `mod02` — **las coords `(x, y)` del marcador físico pasan por `fmt(..., "length")`** (regla
  dura 8). Usaban `:.3g` local, así que el mismo punto se leía `(2.5, 1.33)` en la etiqueta del
  overlay y `(2.500, 1.330)` en la barra de estado del lienzo y en la tabla de Nodos.
- `mod00_mesh_quality._set_no_element_state` — **el header le hablaba en inglés al alumno**:
  `(hover sobre un elemento para ver su calidad)`. Ahora `Pasá el cursor sobre un elemento para
  ver su calidad.`, como el resto del overlay («Arrastrá un nodo…»). Regla dura 1.
- `mod00_mesh_quality.py` (docstring) y, de paso, `gui/main_window.py:1428` +
  `modulos-educativos.md` + `no-reintroducir.md` — **el ítem de menú se llama `📘 Teoría MEF`**,
  no «Teoría FEM». Cuatro lugares del canon y del código nombraban un ítem que no existe con ese
  rótulo (y en inglés, contra la regla dura 1: `FEM` → **MEF** salvo la marca EduFEM y la capa
  DXF). Es un docstring, no un string del alumno, pero es la clase de trampa que manda al próximo
  agente a buscar un menú por un nombre equivocado. `main_window.py` es área 6: una palabra, cero
  riesgo, y la RUTINA pide corregir lo que aparece (§1.3).
- **Los 10 literales de color con NOMBRE del área, cerrados** (ítem del BACKLOG, regla dura 2):
  los 7 de `mod01` (4 `edgecolors="white"` + 3 `color="black"`), los 2 de `mod02` y el 1 de
  `mod03`. Los `"white"` son el outline de marcadores sobre fondo variable → la constante ya
  existía (`EDU_MARKER_OUTLINE_COLOR`, la misma que el disco del marcador de M1 en el lienzo);
  los `"black"` son el **número del nodo escrito DENTRO de su disco** en el cuadrado natural de
  M1 → constante nueva `EDU_NODE_INDEX_FG_COLOR` en `config/settings.py` con su comentario (es
  el único tono legible sobre el naranja, el azul y el violeta de los tres tipos de nodo).
  `gate_hex` no los veía (busca `#RRGGBB`); el test nuevo sí.
- **`except Exception` del área: revisados los 74, cambiados 13** — los 13 en
  `education/overlay_module.py`, que es la base de los **8** módulos. Dejan traza con
  `traceback.print_exc()` (convención de `undo_stack` / `post_tab` / `mesh_canvas` /
  `dialogs` / `main_window`): `on_activated()` (es donde los módulos registran su click
  consumer, el hover y los loops de animación: si falla mudo, **el overlay abre y no reacciona a
  nada** de lo que el alumno haga en el lienzo), `on_closed()` (donde se cancelan los `after` y
  se devuelve el lienzo: si falla, **M0 deja toda la malla en fantasma gris** y **M3 deja su
  loop de pulso repintando a 30 fps sobre un overlay cerrado**), los 3 hooks de la cadena de
  selección y su eslabón previo (si fallan, el módulo **deja de seguir al lienzo**), el
  `open_module` del `👉` del pie (es clickeable con `hand2`: fallaba y **no pasaba nada**), el
  `build_overlay` (el alumno ve el cartel, pero `str(exc)` sin traceback no ubica el fallo), el
  `refit_overlay` (sin refit el Toplevel borderless **recorta** lo que empuja el contenido
  nuevo), el `redraw` de `refresh_overlay`, el `cleanup()` de los widgets hijos (deja el
  `ToolTip` de `ScrollableMatrixImage` como Toplevel huérfano sobre el escritorio), el bloque de
  restauración de `_cleanup` (**el fallo más caro del ciclo de vida**: deja el lienzo con
  nuestro eslabón de la cadena y la capa registrada, o sea un módulo cerrado que sigue dibujando
  y filtrando clicks), el `inst.close()` de los otros overlays (su capa queda debajo del módulo
  nuevo) y el listener del breadcrumb. El de `_draw_layer_wrapper` traza **una sola vez por
  instancia** (`_layer_error_traced`): corre en cada redraw y M3 lo llama a ~30 fps, sin el
  guard un fallo persistente inundaría stderr. Los otros 61 quedaron mudos por legítimos
  (guards de widgets destruidos, `after_cancel`, `mpl` sin `set_zlabel`, `compute_jacobian` de
  un elemento degenerado dentro de un loop de 144 celdas, `lift()` de una instancia stale que el
  propio código maneja popeando el slot). **Revisados: 227 de 274.**
- `tests/test_edu_modules_m0_m3.py` — nuevo (47 chequeos, sin display: los módulos con
  `object.__new__` y dobles de las matrices y labels, como las sesiones 01–06). Sumado a
  `run_gates`. Cubre el estado «esperando elemento» de M2 y M3 (ceros, título, que no quede
  `np.eye`), el borrado del aviso de degenerado, los tres `on_element_deselected` (y su efecto
  medido), las dos notas de remisión, los 10 literales de color, el `fmt` de las coords, el
  español de M0, las 5 trazas clave de `overlay_module` + el guard de una-sola-traza, y **el
  contrato del área** (anchos 470/500/740/720, fase, posición inicial, herencia de
  `CanvasOverlayModule`, numeración visible ①②③ y el `delete(_TAG)` de cada capa). Verificado
  que **falla sin los arreglos**: 36 FALLOS con el código de antes.

### Errores encontrados y corregidos

- **M1, M2 y M3 seguían mostrando el elemento deseleccionado** (el principal), mientras el
  lienzo y el chip `#N` del panel decían lo contrario.
- **M2 fabricaba `J = identidad`** (y `det J = 1`) cuando no había elemento, bajo el título
  «J en centro del elemento».
- **Las matrices de M2 y M3 quedaban congeladas** con los valores del elemento anterior.
- **El aviso rojo «Elemento degenerado … Reordená los nodos» sobrevivía** a la deselección.
- **La nota de M2 mandaba las fórmulas de ∂Nᵢ/∂ξ a M4**, que desde el swap B↔D es la matriz D.
- **El header de M0 le decía «hover» al alumno.**
- **10 literales de color con nombre** fuera de `config/` (regla dura 2).
- **Las coords (x,y) de M2 no pasaban por `fmt`** (regla dura 8): tres decimales distintos a los
  del resto de la app para la misma magnitud.
- **Docstring y comentario de `mod03` con la numeración vieja (M4)**, la trampa que manda al
  próximo agente a buscar B en el módulo de la D.
- **Cuatro lugares nombraban el ítem de menú «Teoría FEM»**, que se llama **`📘 Teoría MEF`**.
- **13 `except Exception` mudos** en la base de los 8 overlays (arriba el detalle).

### DECISIÓN CONGELADA REVERTIDA

Ninguna. El texto `sin elemento — clickeá uno en el lienzo` **no** reintroduce los hints
«Click aquí para…» que la filosofía minimalista eliminó: esa fila es sobre hints **redundantes**
con un feedback visual que ya invita al gesto, y acá no hay nada que invite — el panel está
vacío de datos y el título decía algo falso. Es el mismo criterio con el que M1 ya conserva su
«Clickeá un nodo o cualquier punto interior del elemento.» Tampoco se tocó ningún widget de los
prohibidos (ni badge, ni combobox de elemento, ni botón Cerrar, ni `?`), ni se agregó una sola
línea de alto a los overlays: los cuatro conservan su ancho y su geometría.

### Pendientes visuales para el autor

1. **Deseleccionar con un módulo abierto** (lo más visible de la sesión). `Ctrl+E` → pestaña
   **⚙ PROCESO** → clickear un elemento → `Ctrl+2` (**② Jacobiano**) → ahora **clickear en zona
   vacía del lienzo** (o `Esc`): el halo se apaga y el overlay debe quedar en `sin elemento —
   clickeá uno en el lienzo`, con las matrices `∂N`/`Xₑ`/`J` en **ceros** y sin el aviso rojo
   (antes: la superficie det J y los números del elemento ido seguían ahí). Clickear otro
   elemento lo vuelve a poblar. Probar lo mismo en `Ctrl+3` (**③ Matriz B**) y en `Ctrl+1`
   (**① Mapeo iso**, donde la línea de estado debe volver a «Clickeá un nodo…»). Revertir:
   `git revert` del commit de esta sesión.
2. **`Ctrl+2` con el lienzo vacío.** *Archivo ▸ Nuevo Proyecto* → `Ctrl+2`: el panel Valores
   debe abrir con la **J en ceros** y el título del estado. Antes abría con la matriz
   **identidad** bajo «J en centro del elemento», que se lee como un Jacobiano válido.
3. **El cuadrado natural de M1 en Q9.** `Ctrl+E` con el ejemplo **Q9** → `Ctrl+1`: los 9 nodos
   del cuadrado natural llevan su número **en negro** dentro del disco y el **outline blanco**
   (antes eran los literales `"black"` / `"white"`, ahora constantes de `config/settings.py` con
   el mismo valor). Debe verse **idéntico** a antes; si algún número o borde cambió de color,
   revisar `EDU_NODE_INDEX_FG_COLOR` / `EDU_MARKER_OUTLINE_COLOR`.

### Descartado

- **Unificar el `_draw_natural_square` de M2 y M3** (son ~45 líneas casi idénticas, y M1 tiene
  una tercera variante). Tentador, pero las tres difieren en lo que marcan (M1 **nodos**, M2/M3
  **puntos de Gauss**), en el título y en los límites, y el capítulo documenta que se unifica el
  **estilo**, no el backend ni el widget. Un helper con 6 flags sería peor que las tres copias;
  si se hace, es una refactorización con su propio turno del área.
- **Pasar el heatmap de det J de M2 (`_HEATMAP_N=12` ⇒ 144 celdas × `compute_jacobian` + 169
  `natural_to_physical` por redraw) a `fem/batch.py`.** Es el punto más caro del área, pero hoy
  no produce ningún síntoma medible (el propio comentario mide <5 ms) y vectorizarlo es tocar
  `fem/` (área 12) por una optimización sin evidencia. Al BACKLOG como propuesta.
- **Mostrar un guion o un «—» en vez de ceros** en las matrices sin elemento. `LatexMatrixImage`
  acepta celdas `str`, así que se podría; pero el título ya dice que no hay elemento y una matriz
  de guiones invita a preguntarse qué significa cada guion. El cero es neutro y la vía más corta.
- **Avisar en la barra de estado al deseleccionar con un módulo abierto.** El lienzo ya escribe
  «Seleccion limpiada» y el overlay ahora lo dice en su propio título: un tercer mensaje para el
  mismo gesto es ruido.
- **Tocar `tesis/`**: sigue sin haber `pdflatex` ni `latexmk` ni `vendor/texlive`. Las cuatro
  correcciones del Anexo A siguen abiertas en el área 14.
- **Un cuarto menú, una toolbar o un botón nuevo**: ni se evaluó. Esta sesión no agregó ninguna
  entrada de menú ni ningún widget.

### Área siguiente

8 — Módulos educativos M4–M7 (`education/mod04..mod07`, `module_launcher.py`).
