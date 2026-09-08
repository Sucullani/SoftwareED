# Backlog de la rutina de mejora continua

Cola de trabajo entre sesiones. Cada sesión **empieza acá** y **termina acá**: toma el área
marcada como siguiente, drena primero los ítems que le pertenecen, y antes de cerrar suma lo
que encontró y no hizo.

Reglas del archivo, en [RUTINA.md](RUTINA.md) §4 y §9. Historial de lo hecho, en
[BITACORA.md](BITACORA.md).

---

## Área siguiente

> **4 — Post-Proceso** (`gui/postprocessing/*`: panel de detalles, probe, vista 3D).
> Capítulo a leer antes:
> [../convenciones/canvas-preproceso.md](../convenciones/canvas-preproceso.md) (sección de
> Post-Proceso: probe, contorno, vista 3D) y siempre
> [../convenciones/no-reintroducir.md](../convenciones/no-reintroducir.md). Ítems del BACKLOG
> que le pertenecen y hay que drenar primero: los **5 literales `"white"`/`"black"` de
> `details_panel.py`** y el realce/hit-test de arista sobre malla deformada (compartido con el
> área 1).

Al cerrar la sesión, reemplazá esta línea por el área que sigue en la rotación de
[RUTINA.md](RUTINA.md) §4 (1 → 2 → … → 14 → 1).

---

## Abierto

Formato: `[área Nº] descripción — evidencia — quién decide`.

### Coherencia con la tesis

- **[14] La tesis todavía dice que la memoria PDF necesita una distribución LaTeX
  instalada.** `tesis/capitulos/06_anexos.tex:14` ("La generación de la memoria de cálculo en
  PDF necesita, además, una distribución LaTeX instalada (MiKTeX o TeX Live) […] el programa
  abre un diálogo que explica cómo instalar MiKTeX") y `06_anexos.tex:46` ("Un único
  componente es opcional: una distribución LaTeX"). Desde el 2026-09-08 el instalador embebe
  un TeX Live recortado y `education/components/latex_runtime.py` lo resuelve antes que el
  PATH: la afirmación es falsa para la vía de instalación recomendada. `README.md:35` y
  `installer/dist_extra/LEEME.txt:48` ya están corregidos; la tesis no. **Corrige el `.tex`**
  (es el caso "tesis desactualizada" de [RUTINA.md](RUTINA.md) §6), sin tocar el resto del
  Anexo A. Ojo: el diálogo de fallback (`gui/dialogs/pdflatex_missing_dialog.py`) sigue
  existiendo y sigue siendo correcto para la versión portable sin la carpeta `texlive/`.

- **[14] `tab:atajos` del Anexo A está incompleta y una fila quedó vieja.**
  `tesis/capitulos/06_anexos.tex` dice que la tabla "reúne los atajos de teclado de la
  aplicación", pero omite **`F8` (ORTHO, con Shift como override)** y **`BackSpace` (borrar
  el último vértice del elemento parcial)**, que sí figuran en la ventana `Ctrl+/` de la app
  (`main_window._on_shortcuts`). Además la fila `Supr — Eliminar la entidad seleccionada`
  quedó vieja: desde la sesión 01 borra **la selección completa** (multi-selección). Son 2
  filas nuevas y una palabra; es el caso "tesis desactualizada" de [RUTINA.md](RUTINA.md) §6.
  **No se hizo en la sesión 01 porque el sandbox no tenía `pdflatex` ni `latexmk`** y §6 exige
  compilar antes de pushear. Verificar que haya LaTeX (o el `vendor/texlive`) antes de tomarlo.

- **[14] Barrido pendiente, capítulo por capítulo.** Nadie contrastó todavía `tesis/` contra
  el software de forma sistemática. Cada vez que toque el área 14, tomá **una** sección que no
  esté marcada acá abajo, verificá cada afirmación comprobable contra el código, y anotá la
  sección como barrida con la fecha. Secciones barridas hasta ahora: *ninguna*.

### Interacción e incongruencias

- **[3 / 6] La sub-pestaña educativa se llama distinto en cada fase, y en Proceso el Notebook
  tiene una sola pestaña.** Pre-Proceso: `  🎓 Educacion  ` (`pre_tab.py:286`); Proceso:
  `  🎓 Modulos Educativos  ` (`proc_tab.py`), y además el banner de fase ya dice «Modulos
  educativos del calculo MEF» y el header del panel «Modulos Educativos MEF»: la misma palabra
  tres veces en la misma pantalla, y un `ttk.Notebook` de una pestaña es un control que no
  controla nada. Es incoherencia entre fases (RUTINA §7) pero **puramente visual**: al tomarlo,
  decidir si el Notebook de Proceso desaparece (el panel iría directo en el frame de la fase) y
  anotarlo como pendiente visual con criterio de reversión. No se hizo en la sesión 03 porque ya
  había gastado los 3 pendientes visuales.

- **[3] `proc_tab.wire_canvas` solo detecta su propia cadena si es el callback más externo.**
  El guard es `getattr(prev, "_proc_edu_chain", False)` sobre `canvas.on_selection_changed`; si
  un overlay educativo encadenó encima (`_overlay_edu_chain`), una segunda llamada a
  `wire_canvas()` duplicaría la cadena de Proceso. Hoy es **inocuo**: `wire_canvas()` se llama
  una sola vez (`main_window._build_main_layout`) y `_update_all_project_refs` no la reinvoca,
  y el efecto duplicado sería idempotente (refrescar el chip dos veces). Si algún flujo futuro
  re-cablea las pestañas, recorrer la cadena en vez de mirar solo el tope.

- **[transversal] 274 `except Exception` en `gui/` + `education/`.** Algunos son legítimos
  (Tk destruyendo widgets durante el cierre, `iconbitmap` que puede no existir). Otros tragan
  un fallo en un camino que el alumno recorre y lo dejan sin saber qué pasó. **No hacer un
  barrido masivo**: cada sesión revisa los de **su** área, decide caso por caso, y anota
  acá cuántos revisó y cuántos cambió. Sesión 01, los
  15 de `gui/preprocessing/mesh_canvas.py`: 9 pasaron a dejar traza con
  `traceback.print_exc()`, 3 quedaron mudos por legítimos (`after_cancel`, import diferido de
  `education.overlay_module`, `set_status`) y 3 se fueron al refactorizar el borrado. Sesión
  02, los 22 de `gui/preprocessing/pre_tab.py`: 6 pasaron a dejar traza (`_capture` —si el
  snapshot falla la acción queda fuera del `Ctrl+Z`—, `_safe_redraw`, el refresco tras
  expandir a Q9 y los 3 del panel de módulos educativos) y 16 quedaron mudos por legítimos
  (`set_status`, `nametowidget`, guards de widgets destruidos). La convención es la de
  `models/undo_stack.py` y `post_tab`: traza a stderr, y mensaje al alumno solo si el fallo
  cambia lo que puede hacer. Sesión 03, los 3 de `gui/processing/proc_tab.py` (los 3 pasaron a
  dejar traza: eslabón previo de la cadena de selección, estado inicial del chip,
  `_current_selected_element`) más los 2 de `education/module_launcher.py` que se comían el
  traceback de un módulo que no abre. **Revisados: 42 de 274.**

- **[transversal] 17 literales de color con NOMBRE (`"white"` / `"black"`) fuera de
  `config/`.** Esquivan la auditoría de hex de `run_gates` (busca `#RRGGBB`) pero incumplen
  igual la regla dura 2: son colores decididos en `gui/` y `education/`. Reparto por área:
  **[4]** `gui/postprocessing/details_panel.py` (5) · **[7]** `education/mod01_iso_mapping.py`
  (7), `mod02_jacobian.py` (2), `mod03_b_matrix.py` (1) · **[8]** `mod05_stiffness.py` (1),
  `mod06_equivalent_forces.py` (1). Cada área cierra los suyos en su turno, con una constante
  en `config/settings.py` y su comentario. Los del canvas ya se cerraron (sesión 01:
  `CANVAS_ISOLINE_COLOR`, `CANVAS_COLORBAR_TEXT_COLOR`). *Propuesta para una sesión futura*:
  ampliar el patrón de `run_gates.gate_hex` para que también los detecte — hoy no los ve.

- **[1 / 4] Realce de arista y hit-test de arista no siguen la malla deformada.**
  `mesh_canvas._draw_highlight` y `_hit_test_potential_edge` usan `world_to_screen` sobre las
  coordenadas sin deformar, mientras el resto del canvas usa `_get_node_screen_pos` (que sí
  aplica `deform_scale·u`). Hoy es **inocuo**: la deformada solo existe en el Post, donde no
  hay selección y `MainWindow._on_tab_changed` llama `clear_highlights()` al entrar. Si
  alguna vez el Post recupera la selección de aristas, esto se vuelve un bug visible.

- **[1 / 2] Las tres tablas con selección "compuesta" manipulan los sets del canvas a mano.**
  `pre_tab._on_load_select` / `_on_constraint_select` / `_on_surface_select` hacen
  `canvas._clear_all_sets_silent()` + asignación directa de los sets + `_emit_selection_changed()`
  porque no existe un `replace_load_selection` / `replace_constraint_selection` /
  `replace_surface_selection` en `MeshCanvas` (sí existen los de nodos y elementos). Funciona
  —el `_emit` sincroniza los espejos `highlighted_*`— pero roza el canon ("no setear
  `highlighted_*` directo, usar `select_*` / `replace_*_selection`") y deja la responsabilidad
  del saneo repartida. Propuesta: agregar los tres métodos en el **área 1** (con el mismo
  contrato que `replace_node_selection`, incluido el `selected_nodes` asociado que las cargas
  y restricciones usan para el halo) y que el área 2 los consuma en su próximo turno.

- **[1 / 2] El texto del modal de borrado en cascada está escrito dos veces.**
  `pre_tab._remove_node` / `_remove_element` y `mesh_canvas._delete_selected_nodes` /
  `_delete_selected_elements` arman su mensaje por separado desde el **mismo** preview
  (`preview_node_cascade` / `preview_element_cleanup`), con redacciones distintas: "Borrar N
  nodo(s) eliminara en cascada:" vs "¿Eliminar el elemento 3?" + la lista de ids. El alumno ve
  dos diálogos distintos para la misma decisión según de dónde haya apretado `Supr`. Falta
  decidir dónde vive el texto (un helper de `gui/`, no `models/`: es UI) antes de unificarlo;
  por eso no se hizo en la sesión 02.

- **[2] El placeholder de Elementos crea un elemento degenerado.** `_on_element_double_click`
  hace `add_element([first_node] * 4, …)`: hasta que el alumno completa los 4 vértices, el
  modelo tiene un elemento con los cuatro nodos iguales, que el validador de salud marca y el
  canvas dibuja como un punto. El flujo del placeholder ("crear con defaults y completar
  después, sin bloqueo modal") es una decisión tomada y documentada, así que cambiarlo es una
  decisión de diseño, no un fix: **decide el autor**.

- **[1] La cuadrícula del canvas no está anclada al mundo.** `_draw_grid` es un empapelado en
  coordenadas de pantalla (`spacing = clamp(50·scale, 30, 200)` px, fase `offset % spacing`):
  las líneas no caen en valores redondos de X/Y, así que no ayudan a estimar una coordenada
  ni a ubicar el origen — y el alumno tipea coordenadas en la tabla de Nodos y en el Entry del
  modo dibujo. Propuesta para el próximo turno del área 1: paso en unidades del mundo de la
  serie 1-2-5 elegido para que caiga entre ~40 y ~120 px, línea del origen (X=0, Y=0) más
  marcada y el paso vigente rotulado junto al readout de coords. Es un cambio **visual**: va
  con pendiente visual y criterio de reversión.

### Heredado de otras revisiones

- **Hallazgos abiertos** de [../auditorias/ESTADO_AUDITORIAS.md](../auditorias/ESTADO_AUDITORIAS.md):
  antes de trabajar un área, mirá si ya tiene hallazgos ahí y cerralos en el mismo pase.
- **Dictamen del 2026-09-07**: quedan abiertos los hallazgos MAYOR y MENOR no mecánicos
  (objeto de estudio vs. población, hipótesis circular, preliminares, estado del arte). Son
  **decisiones de autor** sobre el marco metodológico: la rutina **no los toca**, están acá
  solo para que ninguna sesión crea que se olvidaron.

---

## Pendientes visuales para el autor

Lo que el gate no puede juzgar. Cada ítem dice qué abrir, qué mirar y cómo revertir.

- **Post-Proceso y Memoria tras la vectorización y la corrección de la extrapolación Q4**
  (abierto desde el 2026-09-07, ver [../notas/ESTADO.md](../notas/ESTADO.md)). Abrir la GUI
  con el ejemplo canónico Q4 y con Cook 32×32 Q9: gradiente, isolíneas, modo crudo, probe y
  vista 3D; después generar una Memoria de Cálculo. **Todas** las tensiones nodales Q4
  cambiaron (VM máximo del ejemplo canónico: 977,46 → 864,70); Q9 no cambió.
- **TeX Live embebido** (abierto desde el 2026-09-08). Exportar Memoria (Q4 canónico y Cook
  Q9, ambos estilos) y la Teoría MEF: deberían verse idénticas a las de MiKTeX. Probar
  `installer/Output/EduFEM-Setup.exe` en una PC **sin MiKTeX**.
- **Borrado múltiple desde el lienzo** (sesión 01). `Ctrl+E`, en Pre-Proceso seleccionar 2–3
  nodos con **Ctrl+Click sobre el canvas** y `Supr`: un solo modal con la cuenta agregada de
  la cascada, las 5 tablas refrescadas, y **un solo `Ctrl+Z`** que lo devuelve todo. Con nada
  seleccionado, `Supr` debe escribir "Nada seleccionado — clickeá un nodo…" en la barra de
  estado. Revertir: `git revert` del commit de la sesión 01.
- **Etiquetas de nodo del Post con desplazamientos** (sesión 01). `F5` → Post → **Ux / Uy /
  |U|**: cada nodo rotula su valor con **5 decimales** (antes todos decían `0.00`); con von
  Mises o σx sigue en 2. Isolíneas y texto de la colorbar deben verse idénticos.
- **Arranque maximizado en Windows** (sesión 01). `MainWindow.__init__` envolvió
  `root.state("zoomed")` en un `try` con degradación portable. En Windows es la primera rama,
  así que la ventana debe seguir abriéndose maximizada; si arranca chica, revisar el guard.
- **Borrar desde las tablas del Pre-Proceso** (sesión 02). `Ctrl+E`, sub-pestaña **Cargas**:
  clickear la fila de una carga y `Supr` → la fila **desaparece** (antes volvía como fila azul
  con `0 | 0`), la barra de estado dice "Carga en nodo N eliminada." y el badge de salud se
  recalcula. Igual en **Restricciones**. En **Carg. Superf.** con 2–3 cargas, borrar la
  primera **no** debe dejar otra resaltada en amarillo. En **Nodos**, borrar un nodo que tenía
  carga no debe dejar una fila fantasma con ese número en Cargas. Revertir: `git revert` del
  commit de la sesión 02.
- **`Supr` sin selección en las 5 tablas** (sesión 02). Foco en una tabla, ninguna fila
  seleccionada, `Supr` → "Nada seleccionado — elegí una o varias filas de …" en la barra de
  estado (antes no pasaba nada). El placeholder gris y las filas fantasma no cuentan.
- **Celdas numéricas con coma decimal** (sesión 02). Doble-click en X de un nodo, tipear
  `3,25`, Enter → guarda 3,25 (antes: "Valor numerico invalido"). Con `hola`, el modal debe
  decir "Y: valor invalido — «hola» no es un numero. Usá punto o coma decimal".
- **F5 con un modelo incompleto** (sesión 03). `Ctrl+E`, borrar todas las restricciones y `F5`:
  **un solo** diálogo *⚕ Salud del modelo* con el error, su «🎓 ¿Por qué?» y el «🔧 Corregir»
  (antes: un `Aviso` seco). Al cancelar vuelve al Pre-Proceso. Probar también con **una sola
  restricción en x** (`insufficient_restraints`): ahí antes se apilaban **dos** diálogos.
  Revertir: `git revert` del commit de la sesión 03.
- **Cursor de espera al resolver** (sesión 03). Cook 32×32 Q9 + `F5`: el puntero debe ser el
  reloj de espera durante el cálculo y volver al normal al terminar. Si queda pegado, revisar el
  `finally` de `auto_solve`.
- **Barra de estado y subtítulo de Proceso** (sesión 03). Abrir `③ Matriz B` con un elemento
  seleccionado: «③ Matriz B (Deformacion) abierto sobre el elemento #N» (antes: «Modulo educativo
  abierto: mod03»); sin selección, «… clickeá un elemento en el lienzo…». El subtítulo del panel
  pasó a 2 renglones: verificar que no empuje los botones fuera del panel en 1080p.
- **Tests que necesitan un Tk real**: `run_gates --con-gui` (`test_draw_mode`,
  `test_selection_integration`) **ya corre en Linux** desde la sesión 01, con
  `xvfb-run -a python -m tests.run_gates --con-gui` (antes moría en `root.state("zoomed")`).
  Correrlo en Windows de vez en cuando sigue valiendo: Xvfb no reproduce el gestor de
  ventanas ni los diálogos nativos.

---

## Cerrado

Se mueve acá lo resuelto, con la sesión que lo cerró. Se conserva: evita que una sesión
futura reabra algo ya decidido.

- **[1] `Supr` no borraba nada con multi-selección en el canvas** — cerrado por la sesión 01.
  El handler despachaba por `highlighted_*` (que valen `None` con >1 ítem). Ahora lee los sets
  `selected_*`; regresión en `tests/test_canvas_delete.py`.
- **[1] Índice stale tras borrar una carga superficial desde el canvas** — cerrado por la
  sesión 01. Los índices son posicionales: el que quedaba en `selected_surfaces` pasaba a
  señalar otra carga, que aparecía resaltada. Nuevo `MeshCanvas.prune_dead_selection()`.
- **[1 / 4] Etiqueta de valor del nodo formateada siempre como tensión** — cerrado por la
  sesión 01 con el parámetro `kind` de `set_result_values` / `set_element_result_grid`.
- **[6] La app moría fuera de Windows en `root.state("zoomed")`** — cerrado por la sesión 01
  con degradación portable; habilitó `run_gates --con-gui` bajo `xvfb-run`.
- **[2] Borrar desde una tabla dejaba la selección del canvas con ids muertos** — cerrado por
  la sesión 02 con `pre_tab._sync_selection_after_delete()`, que delega en
  `prune_dead_selection()`. Tres síntomas visibles: fantasma de un nodo inexistente, la fila
  borrada volviendo como fantasma con ceros, y otra carga superficial resaltada. Regresiones
  en `tests/test_pre_tab_delete.py`.
- **[2] El badge de salud y el ● del título no se actualizaban al borrar o pegar desde el
  spreadsheet** — cerrado por la sesión 02 (`_update_status_info` + el nuevo wrapper guardado
  `_update_title` en los 5 `_remove_*` y los 5 `_paste_*`).
- **[2] `Supr` sin selección en una tabla no decía nada** — cerrado por la sesión 02
  (`_nothing_selected`), en paridad con el lienzo.
- **[2] Los editores de celda rechazaban la coma decimal que el paste sí aceptaba** — cerrado
  por la sesión 02 con `to_float_flex` en las 4 rutas de edición numérica, más mensajes de
  error que nombran la celda y el formato aceptado.
- **[3 / 14] F5 no pasaba por el comprobador de salud** — cerrado por la sesión 03. Los dos
  pre-chequeos propios de `_on_solve` (sin elementos / sin restricciones) abrían un
  `showwarning` seco y retornaban antes de `validate_project`: el atajo tenía menos diagnóstico
  que el cambio de pestaña y contradecía el Anexo A de la tesis. Ahora F5 delega en
  `post_tab.auto_solve()` (una sola vía, regla dura 16). Regresión en `tests/test_solve_flow.py`.
- **[3 / 4] Dos diálogos de salud apilados al resolver con F5** — cerrado por la sesión 03 con el
  guard `_solving` de `auto_solve`. `notebook.select(2)` encola el `<<NotebookTabChanged>>` y el
  `wait_window()` del diálogo (que no es modal) lo despacha: el handler de pestaña reentraba y
  abría un segundo reporte idéntico. Verificado con Tk real bajo `xvfb` (2 Toplevels sin el
  guard, 1 con él).
- **[3 / 7] Mensajes del launcher de módulos que apuntaban a menús inexistentes** — cerrado por
  la sesión 03: «Archivo ▸ Cargar Ejemplo» (los ejemplos viven en **Ayuda**) y «menú Educación»
  (la barra tiene 3 menús). Además la barra de estado mostraba la key interna `mod03` en vez de
  la etiqueta del botón (nuevo `module_launcher.module_label`).
- **[2] Docstrings de `pre_tab.py` / `_table_helpers.py` que anunciaban features eliminadas**
  (fill-down `Ctrl+D`, navegación Tab/flechas, menú contextual, `on_commit(text, direction)`)
  más 8 encabezados de sección vacíos — cerrado por la sesión 02. Eran una trampa: invitaban a
  "restaurar lo que falta" contra `no-reintroducir.md`.

---

## Propuestas que esperan al autor

Cosas que la rutina **no** hace sin un OK explícito: cambios de alcance, dependencias nuevas,
o reversiones de decisiones congeladas cuya justificación no es evidente.

- *(vacío)*
