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
