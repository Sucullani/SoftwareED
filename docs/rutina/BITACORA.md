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
- `tests/test_canvas_delete.py` — nuevo (10 casos, sin display: instancia el canvas con
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
