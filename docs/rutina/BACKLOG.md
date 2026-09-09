# Backlog de la rutina de mejora continua

Cola de trabajo entre sesiones. Cada sesión **empieza acá** y **termina acá**: toma el área
marcada como siguiente, drena primero los ítems que le pertenecen, y antes de cerrar suma lo
que encontró y no hizo.

Reglas del archivo, en [RUTINA.md](RUTINA.md) §4 y §9. Historial de lo hecho, en
[BITACORA.md](BITACORA.md).

---

## Área siguiente

> **9 — Componentes educativos y Teoría** (`education/components/*`,
> `gui/dialogs/theory_hub_dialog.py`). Capítulo a leer antes:
> [../convenciones/modulos-educativos.md](../convenciones/modulos-educativos.md) (la lista de
> componentes **VIVOS** vs. los **eliminados** en las limpiezas 2026-05 y 2026-06 —
> `LatexMath`, `LatexBlock`, `FormulaValueToggle`, `PlotPanel`/`FourPanel`, `ParamInput`,
> `StepAnimator`, `GaussCoordReadout`, `LatexStatusLabel`: **no recrearlos**— más las trampas
> de `latex_image.py`: `shrink=False`, `ScrollableMatrixImage` solo para las matrices que NO
> entran, la trampa de la rueda de `_consume_wheel_recursive`, el `cleanup()` que apaga el
> ToolTip, y que mathtext **no** soporta `\begin{bmatrix}`) y
> [../convenciones/memoria-calculo.md](../convenciones/memoria-calculo.md) para el Theory Hub,
> que comparte con la memoria el backend pdflatex y la regla de **ASCII** en los strings LaTeX;
> y siempre [../convenciones/no-reintroducir.md](../convenciones/no-reintroducir.md). Ítems del
> BACKLOG que le pertenecen y hay que drenar primero: **ninguno abierto** — es la primera vez
> que el área toca, así que después de revisar los hallazgos de
> [../auditorias/ESTADO_AUDITORIAS.md](../auditorias/ESTADO_AUDITORIAS.md) se busca material
> nuevo. Los `except Exception` de `education/components/` y de `theory_hub_dialog.py` son los
> que quedan sin revisar del ítem transversal (**6 de 274**).

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

- **[14] El pie de la `fig:vista3d` del Anexo A describe un control que no existe.**
  `tesis/capitulos/06_anexos.tex:121` dice que «El control **Crudo** ↔ **Suavizado**
  *interpola* entre los valores por punto de Gauss y el campo nodal promediado». Es falso por
  partida doble: (a) es un **toggle binario**, no un interpolador — el slider continuo se
  eliminó a propósito («los estados intermedios confundían», documentado en el docstring de
  `gui/postprocessing/surface_3d_viewer.py`); (b) el modo crudo no son «los valores por punto
  de Gauss» sino σ = D·B(ξ,η)·uₑ evaluado en una grilla por elemento. Es el caso «tesis
  desactualizada» de [RUTINA.md](RUTINA.md) §6: son dos frases del pie de figura, sin tocar el
  resto del Anexo A. **No se hizo en la sesión 04 porque el sandbox no tenía `pdflatex` ni
  `latexmk`** y §6 exige compilar antes de pushear. Verificar que haya LaTeX (o el
  `vendor/texlive`) antes de tomarlo, junto con las otras dos correcciones del Anexo A.

- **[14] Barrido pendiente, capítulo por capítulo.** Nadie contrastó todavía `tesis/` contra
  el software de forma sistemática. Cada vez que toque el área 14, tomá **una** sección que no
  esté marcada acá abajo, verificá cada afirmación comprobable contra el código, y anotá la
  sección como barrida con la fecha. Secciones barridas hasta ahora: *ninguna*.

### Interacción e incongruencias

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
  traceback de un módulo que no abre. Sesión 04, los 35 de `gui/postprocessing/` (los 4
  archivos): 8 pasaron a dejar traza —los 3 refrescos de la Vista 3D en `post_tab` (que además
  avisan con `_avisar_3d_desactualizada`: si fallan mudos, el visor sigue mostrando la solución
  o el campo **anteriores**), el retorno al Pre-Proceso al cancelar el reporte de salud, el
  `compute_raw_grids` del visor, el `_copy_values_tsv`, el callback de cierre del
  `DetailsPanel` y `_get_units` visto desde el 3D— y 27 quedaron mudos por legítimos
  (`after_cancel`, `destroy`/`unbind` de teardown, `tooltip.hide`, `set_status`, sondeo de la
  API privada de matplotlib para los paneles 3D, `tight_layout`). Sesión 05, los 33 de
  `gui/dialogs/` sin contar `theory_hub_dialog` (que es del área 9): 9 pasaron a dejar traza
  —los 5 `stack.capture` (si el snapshot falla, esa acción queda fuera del `Ctrl+Z`), los 3
  refrescos de la ventana principal (`_refresh_all_tabs` mudo deja las tablas con el modelo
  viejo o con los números del sistema de unidades anterior bajo el encabezado nuevo) y el
  `readfile` del preview DXF (un archivo ilegible se reportaba como "capa sin polilíneas")— y
  24 quedaron mudos por legítimos (`webbrowser.open`, `grab_set`, teardown de video,
  `tooltip`, guards de widgets destruidos). Sesión 06, los 43 del área 6 (30 de
  `gui/main_window.py` + 13 de `gui/widgets/`): 13 pasaron a dejar traza —los que dejaban la
  UI mintiendo (el refresco final de `_on_state_restored`, o sea el `Ctrl+Z` que parece no
  haber hecho nada; el `validate_project` del badge, que se queda diciendo «Modelo sano»; el
  `wire_canvas` de cada fase; la suscripción del breadcrumb), los que dejaban una tecla muda
  (`F` de ajustar vista, `D` de dibujar, los dos eslabones de la cascada de `Escape`, el chip
  del breadcrumb), los del PDF (el snapshot del proyecto y las tensiones por elemento) y el
  render del `WebpPlayer` más el `on_closed` de `CanvasOverlay` (si falla, el overlay se ve
  cerrado pero su loop sigue repintando)— y 30 quedaron mudos por legítimos (`iconbitmap`,
  warmup de mathtext, `focus_get`, teardown de Toplevels, `after_cancel`, walk de widgets de
  terceros). Además el `os.startfile` del «¿Abrir el PDF ahora?» dejó de estar dentro del
  `try` que se comía el «Sí» del alumno. **Revisados: 153 de 274.** Sesión 07, los 74 del área 7 (M0..M3 +
  `overlay_module.py`): **13 pasaron a dejar traza, los 13 en `overlay_module.py`**, que es la
  base de los 8 overlays — `on_activated` (sin él el overlay abre y no reacciona a ningún click
  del lienzo), `on_closed` (M0 deja la malla entera en fantasma gris, M3 deja su loop de pulso a
  30 fps sobre un overlay cerrado), los 3 hooks de la cadena de selección + su eslabón previo
  (el módulo deja de seguir al lienzo), el `open_module` del `👉` clickeable del pie, el
  `build_overlay` (el cartel que ve el alumno no ubicaba el fallo), `refit_overlay` (el Toplevel
  borderless recorta lo que empuja el contenido nuevo), el `redraw` de `refresh_overlay`, el
  `cleanup()` de los widgets hijos (ToolTip huérfano), el bloque de restauración de `_cleanup`
  (deja un módulo cerrado dibujando y filtrando clicks) y el `inst.close()` de los otros
  overlays; más el de `_draw_layer_wrapper`, acotado a **una traza por instancia**
  (`_layer_error_traced`) porque corre en cada redraw. Los otros 61 quedaron mudos por legítimos
  (guards de widgets destruidos, `after_cancel`, `set_zlabel` de matplotlib, `compute_jacobian`
  de un elemento degenerado dentro de un loop de 144 celdas, el `lift()` de una instancia stale
  que el propio código maneja). **Revisados: 227 de 274.** Sesión 09, los 41 del área 8 (`mod04`..`mod07` +
  `module_launcher.py`): **16 pasaron a dejar traza** — el `except: pass` de la capa de M4 se
  **eliminó** (se comía la excepción antes de que el `_draw_layer_wrapper` de la base la viera),
  los dos `set_matrix` de M4 (dejaban el panel con la D anterior), el `remove_click_consumer` de
  M5 (un módulo **cerrado** que se sigue comiendo los clicks del lienzo), el `redraw` de
  `_refresh_all` y el `draw_idle` del cuadrado natural de M5, el `sp.latex` y los dos de
  `_count_terms` (los que escondieron el `sympy` sin importar de la sesión 05: uno degradaba al
  `repr` y el otro devolvía el «0 términos»), el error de `SymbolicIntegrandQ4`, el
  `redraw_overlays_only` del loop de M6 (con guard de **una traza por instancia**, corre a ~60
  fps), y en M7 el `assemble_global_system` de la F de referencia, el `redraw` de su
  `on_element_deselected`, el eslabón previo de la cadena de **hover** y su restauración en
  `on_closed`; más el `replace_element_selection` de `module_launcher` (el overlay trabajaba
  sobre un elemento y el halo marcaba otro). Los 25 restantes quedaron mudos por legítimos
  (`after_cancel`, `destroy` de teardown, `subplots_adjust`/`suptitle` cosméticos,
  `get_gauss_points_2d` sobre un orden 1..3, los 3 `get_dof_indices` dentro de renders de
  hover). **Revisados: 268 de 274** — quedan los 6 de `education/components/` +
  `theory_hub_dialog.py`, que son del área 9.

- **[transversal] Ya no queda ningún literal de color con NOMBRE fuera de `config/`** (cerrado
  por la sesión 09; **lo que sigue abierto es la propuesta de gate**, abajo). Los `"white"` /
  `"black"` esquivaban la auditoría de hex de `run_gates` (que busca `#RRGGBB`) pero incumplían
  igual la regla dura 2: eran colores decididos en `gui/` y `education/`. Cada área cerró los
  suyos en su turno, con una constante de `config/settings.py`. Cerrados: los
  del canvas (sesión 01: `CANVAS_ISOLINE_COLOR`, `CANVAS_COLORBAR_TEXT_COLOR`), los **5 de
  `details_panel.py`** (sesión 04: `MOHR_MARKER_EDGE_COLOR`), los **10 de M1/M2/M3** (sesión
  07: `EDU_MARKER_OUTLINE_COLOR` para los outlines de marcador, que ya existía, y la nueva
  `EDU_NODE_INDEX_FG_COLOR` para el número del nodo dentro de su disco) y los **2 últimos**
  (sesión 09: el `edgecolors` del PG sumado del cuadrado natural de `mod05_stiffness.py` y el
  `outline` de la bolita nodal de `mod06_equivalent_forces.py`, los dos a
  `EDU_MARKER_OUTLINE_COLOR`). *Propuesta que sigue abierta*: ampliar el patrón de
  `run_gates.gate_hex` para que también detecte los literales con **nombre** — hoy solo ve los
  `#RRGGBB`; mientras tanto los vigilan `tests/test_edu_modules_m0_m3.py` (área 7) y
  `tests/test_edu_modules_m4_m7.py` (área 8).

- **[4 / 2] El mismo desplazamiento se lee distinto en la tabla del Post y en el lienzo.**
  `post_tab._update_table` formatea los desplazamientos en notación científica
  (`f"{ux:.{DECIMALS_DISPLACEMENT}e}"` → `5.12345e-04`, decisión documentada en el código por
  el ancho de columna), mientras las etiquetas de nodo del lienzo usan `fmt(v,
  "displacement")` (`0.00051`) y el header de la vista 3D usa `fmt_escala` (`5.12e-04`). Tres
  formatos para la misma magnitud en la misma fase; además el de la tabla es el único que no
  pasa por `fmt` (roza la regla dura 8, aunque el motivo está escrito). Unificar exige decidir
  cuál gana y tiene impacto visual en toda la tabla: **decide el autor** o una sesión del área
  4 que gaste un pendiente visual en esto.

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

- **[13 / 5] `_LENGTH_DEFAULT_SYSTEM` duplica el mapeo longitud → sistema canónico.**
  `gui/dialogs/dxf_import_dialog.py:50` mantiene su propio dict `{"mm": "SI (N, mm, MPa)", …}`
  y su propio `_LENGTH_TO_M`, en paralelo a `config/units.py`. Si se agrega un sistema de
  unidades, el importador DXF no se entera. Mover ambos a `config/units.py` es área 13
  (interoperabilidad) y toca `config/`, por eso no se hizo en la sesión 05.

- **[6 / 14] La ventana `Ctrl+/` ahora lista más atajos que la tabla `tab:atajos` de la
  tesis.** La sesión 06 le agregó `Supr`, `Esc`, `Ctrl+C`, `Ctrl+V`, `Ctrl+A` y las tres filas
  de edición de tabla, y movió `Ctrl+E` de «Archivo» a «Ayuda» (que es donde vive *Cargar
  Ejemplo*). El ítem del área 14 que pide completar `tab:atajos` con `F8` y `BackSpace` sigue
  abierto y ahora tiene **más** filas que sumar: tomarlos juntos, en la misma pasada por el
  Anexo A, cuando haya `pdflatex`.

- **[6] `_on_export_pdf` puede lanzar dos compilaciones a la vez.** El `_PDFProgressDialog`
  **no** hace `grab_set` (decisión tomada: la GUI sigue interactiva mientras el worker
  compila), pero nada impide volver a *Archivo ▸ Exportar ▸ Memoria de Cálculo* con una
  compilación en curso: arrancan dos threads y, si el alumno elige el mismo destino, los dos
  escriben el mismo `.pdf`. Hoy no revienta nada visible —cada worker trabaja sobre su propio
  snapshot— pero es una carrera real. El arreglo natural es un guard `_exportando` en el mismo
  estilo que el `_solving` de `auto_solve` (sesión 03); no se hizo acá para no tocar el flujo de
  la memoria (área 10) en una sesión de la ventana.

- **[6] `_on_new_project` no limpia el breadcrumb de módulos visitados.** `_breadcrumb_visited`
  acumula por sesión y sobrevive a *Nuevo Proyecto*: los chips siguen marcados como visitados
  sobre un modelo vacío. Es deliberado que sobreviva al **cierre** de un módulo (indicador de
  progreso de la sesión), pero no está decidido qué debe pasar al empezar un proyecto nuevo:
  **decide el autor** si el progreso es del alumno (se conserva) o del modelo (se limpia).

- **[8] `_refresh_status` y los chips de carga de M6 no pasan por `fmt(value, kind)`** (regla
  dura 8). Hoy son `f"N{nid}:  Fx={fx:+.2f}   Fy={fy:+.2f}"` y
  `q=[{sl.q_start:+.0f}, {sl.q_end:+.0f}]`: decimales hardcodeados y **sin unidades**, en el
  único módulo cuyo resultado es un vector de fuerzas con unidades del proyecto. Encontrado por
  la sesión 09, que no lo tomó porque cambia todas las líneas del panel y ya gastaba sus 3
  pendientes visuales en los dos hallazgos grandes del área. Es el próximo turno del área 8.

- **[7 / 12] El heatmap de det J de M2 recalcula 144 `compute_jacobian` + 169
  `natural_to_physical` por redraw.** `_draw_jacobian_heatmap` (`_HEATMAP_N=12`) es el punto más
  caro del área 7 y se ejecuta en cada `redraw()` del canvas mientras M2 está abierto. Hoy **no
  produce ningún síntoma medible** (el propio comentario del método lo mide en <5 ms) y
  vectorizarlo sobre `fem/batch.py` es tocar el motor (área 12) por una optimización sin
  evidencia, así que la sesión 07 no lo tomó. Si alguna vez se nota lag al arrastrar el canvas
  con M2 abierto, ése es el lugar (y bajar `N` a 8 ya da 64 quads con gradientes igual legibles).

- **[7] `_draw_natural_square` existe tres veces.** M2 y M3 tienen ~45 líneas casi idénticas y M1
  una tercera variante (`_draw_natural`). Unificarlas es tentador pero las tres difieren en lo
  que marcan (M1 **nodos**, M2/M3 **puntos de Gauss**), en el título y en los límites; el
  capítulo documenta que se unifica el **estilo**, no el widget ni el backend. Un helper con 6
  flags sería peor que las tres copias. Si se hace, es una refactorización con su propio turno
  del área 7 y conviene que salga con el estilo ya estabilizado.

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
- **Vista 3D en modo Crudo** (sesión 04, **el más importante**). `Ctrl+E` → `F5` → **🧊 Vista
  3D** → campo **σx** (no von Mises, casi simétrico) → **Crudo**: el relieve debe coincidir con
  el contorno 2D de σx del lienzo (rojos donde el lienzo tiene rojos). Antes el campo se
  dibujaba **transpuesto dentro de cada elemento**. Comparar las dos ventanas lado a lado es lo
  más rápido. Revertir: `git revert` del commit de la sesión 04.
- **Escala de color de la Vista 3D** (sesión 04). En esa misma ventana debe aparecer una
  colorbar a la derecha, con `σx [MPa]` (la unidad del proyecto) y ticks con el mismo formato
  que la del lienzo (`2.50e+07` en magnitudes grandes). Al cambiar de campo o de modo la
  superficie **no debe achicarse**: si se encoge en cada cambio, `_clear_colorbar` no está
  retirando la anterior.
- **Los dos campos numéricos del panel del Post** (sesión 04). Con la deformada activa, tipear
  `2,5` en *Factor de escala* + Enter → se amplifica (antes no pasaba nada). Tipear `abc` → la
  barra de estado lo explica y el campo **vuelve solo** al último valor bueno. En *Número de
  niveles*, `500` → queda en `30` y lo avisa.
- **Tests que necesitan un Tk real**: `run_gates --con-gui` (`test_draw_mode`,
  `test_selection_integration`) **ya corre en Linux** desde la sesión 01, con
  `xvfb-run -a python -m tests.run_gates --con-gui` (antes moría en `root.state("zoomed")`).
  Correrlo en Windows de vez en cuando sigue valiendo: Xvfb no reproduce el gestor de
  ventanas ni los diálogos nativos.
- **Materiales: la solución se invalida de verdad** (sesión 08, **el más importante**).
  `Ctrl+E` → `F5` → campo **|U|**, anotá el máximo (en el ejemplo canónico, **0,0130763**) →
  *Modelo ▸ Material* → bajá **E** a la décima parte → *Guardar cambios* → cerrá → `F5` →
  **|U|**: tiene que dar **10 veces más** (0,130763). Antes salía idéntico, y *Exportar
  Memoria PDF* generaba un documento con el material nuevo y la corrida vieja. **Mirá los
  desplazamientos, no von Mises**: con la carga impuesta del ejemplo, escalar E uniformemente
  no mueve las tensiones (VM máx = 864,70 en los dos casos), así que von Mises no distingue el
  bug del arreglo. La barra de estado debe decir «Material «…» guardado.». Probá también
  *Eliminar* sobre un material en uso: el badge de salud debe pasar a **✗ 1 error(es)** en el
  acto, sin cambiar de pestaña. Revertir: `git revert` del commit de la sesión 08.
- **Diálogo de materiales con coma decimal** (sesión 05). `Modelo ▸ Materiales`, campo **ν**:
  tipear `0,3` → **💾 Guardar cambios** debe habilitarse (antes: gris para siempre y sin
  explicación). Tipear `0,9` → el borde del Entry de ν se pone **rojo** y Guardar se apaga;
  volver a `0.3` y el borde vuelve a la normalidad. Probar los 4 campos. Revertir: `git revert`
  del commit de la sesión 05.
- **Reporte de salud: la rueda y los botones** (sesión 05). `Ctrl+E`, borrar las restricciones,
  `F5` → en *⚕ Salud del modelo*: (a) la rueda **sobre el lienzo de atrás** debe hacer solo
  zoom, sin mover la lista del reporte; (b) tocar **🔄 Re-validar** y comprobar que la rueda
  **sigue** scrolleando la lista (antes se moría ahí) y que la barra de estado dice cuántos
  errores quedan; (c) con un material sin usar, **📍 Ir al ítem** debe abrir *Materiales* con
  ese material seleccionado (antes no hacía nada).
- **M5 con el integrando simbólico** (sesión 05). Proceso → clickear un elemento **Q4** →
  `⑤ Rigidez`: la fórmula de K(i,j) debe verse **renderizada en LaTeX** y el contador decir un
  número real de términos (`📏 K_(1,1): 5 términos · N chars LaTeX`). Antes salía el texto
  plano de la expresión Python y **siempre "0 términos"**.

- **Proceso sin Notebook** (sesión 06). Ir a la pestaña **⚙ PROCESO**: el panel de módulos
  M1…M7 debe arrancar **pegado al banner**, sin la pestaña `🎓 Modulos Educativos` encima (era
  un Notebook de una sola pestaña). El subtítulo del banner ahora dice «Del elemento al sistema
  K·u = F · F5 resuelve». Verificar que el panel gana ese alto y que los botones no quedan
  apretados en 1080p. Revertir: `git revert` del commit de la sesión 06.
- **Escape y Return en los diálogos** (sesión 06). En `Modelo ▸ Unidades`, `Modelo ▸ Gravedad`,
  `Modelo ▸ Tipo de Elemento`, `Modelo ▸ Tipo de Análisis` y `Ayuda ▸ Acerca de`: **Escape**
  cierra sin aplicar nada y **Enter** acepta. En `Modelo ▸ Materiales`, Enter guarda el material
  abierto, y con un campo en rojo **no** guarda: lo dice en la barra de estado nombrando el
  campo. En el reporte de salud, Escape vuelve al Pre-Proceso y **Enter no hace nada** (a
  propósito: «corregir» y «resolver igual» son decisiones opuestas). De paso: con un modelo
  modificado, `Ctrl+N` → **Sí** → cancelar el *Guardar Como* debe **volver al modelo intacto**
  (antes lo descartaba igual).
- **Las dos ventanas de texto de Ayuda** (sesión 06). `F1` (Manual de Usuario) y `Ctrl+/`
  (Atajos): son `messagebox` largos y el sandbox no puede medirlos. Verificar en **1080p** que
  ninguno de los dos se corta ni se sale de la pantalla; si el manual no entra, hay que partirlo
  o pasarlo a un Toplevel propio (y eso ya es decisión del autor).
- **M4 sin elemento** (sesión 09, **el más importante**). `Ctrl+E` → pestaña **⚙ PROCESO** →
  **sin clickear nada**, `Ctrl+4` (**④ Matriz D**): el panel *Valores* debe abrir con la **D en
  ceros**, arriba `◎ sin elemento — clickeá uno en el lienzo para ver su D.` y el espectro
  **sin el ◆ dorado**. Antes abría con la D de `Material Ejemplo` (E = 225 000, `max|D| =
  234 375`) y un ◆ apuntando a su ν, como si perteneciera a algún elemento. Clickeá un
  elemento: la D se llena, vuelve el ◆ y el rótulo vuelve al `🧪 Deslizá o tocá…`. Clickeá en
  **zona vacía del lienzo** (o `Esc`): vuelve a ceros. La pestaña **ƒ Fórmula** debe seguir
  mostrando la D simbólica en los **tres** estados. Revertir: `git revert` del commit de la
  sesión 09.
- **M5 al deseleccionar** (sesión 09). `Ctrl+E` → clickeá un elemento → `Ctrl+5` (**⑤ Rigidez
  K_e**) → clickeá en **zona vacía del lienzo**: la kₑ debe volver a `◎ Clickeá un elemento y
  luego los PGs del canvas`, la línea `Σ 4/4 pg · último: pg4 …` debe **desaparecer** y los 4
  PGs del cuadrado natural deben quedar **huecos y punteados** (ghost), no dorados. Clickeá
  otro elemento y todo se repuebla con los 4 PGs sumados.
- **Los dos outlines blancos** (sesión 09; deben verse **idénticos**). En el cuadrado natural
  de `Ctrl+5`, el borde blanco de los PGs **dorados**; en `Ctrl+6` (**⑥ Fuerzas equivalentes**,
  con una carga superficial definida), el borde blanco de las **bolitas nodales** rojas. Eran
  los literales `"white"` y ahora son `EDU_MARKER_OUTLINE_COLOR`, con el mismo valor: si alguno
  cambió de color, revisar esa constante.
- **Deseleccionar con un módulo educativo abierto** (sesión 07, **el más importante**).
  `Ctrl+E` → pestaña **⚙ PROCESO** → clickear un elemento → `Ctrl+2` (*② Jacobiano*) → ahora
  **clickear en zona vacía del lienzo** (o `Esc`): el halo se apaga y el overlay debe quedar en
  `sin elemento — clickeá uno en el lienzo`, con `∂N`, `Xₑ` y `J` en **ceros** y **sin** el aviso
  rojo de elemento degenerado. Antes seguían ahí la superficie det J, las matrices y el aviso del
  elemento ya deseleccionado. Clickear otro elemento lo vuelve a poblar. Repetir en `Ctrl+3`
  (*③ Matriz B*) y en `Ctrl+1` (*① Mapeo iso*, cuya línea de estado debe volver a «Clickeá un
  nodo o cualquier punto interior del elemento.»). Revertir: `git revert` del commit de la
  sesión 07.
- **`Ctrl+2` con el lienzo vacío** (sesión 07). *Archivo ▸ Nuevo Proyecto* → `Ctrl+2`: el panel
  Valores abre con la **J en ceros** y el título del estado. Antes abría con la matriz
  **identidad** bajo «J en centro del elemento» — una J perfectamente plausible, con det J = 1,
  que nadie había calculado.
- **El cuadrado natural de M1 en Q9** (sesión 07). `Ctrl+E` con el ejemplo **Q9** → `Ctrl+1`: los
  9 nodos llevan su número **en negro** dentro del disco y el **outline blanco**. Eran los
  literales `"black"` / `"white"` y ahora son constantes de `config/settings.py` con el mismo
  valor, así que debe verse **idéntico**; si algún número o borde cambió de color, revisar
  `EDU_NODE_INDEX_FG_COLOR` / `EDU_MARKER_OUTLINE_COLOR`.

(*El centrado de `Ayuda ▸ Acerca de EduFEM`, que antes moría en `NameError`, no ocupa un
pendiente visual: se verificó con Tk real bajo `xvfb` — abre en `450x350+225+175`, centrado
sobre la ventana principal.*)

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
- **[4] La vista 3D dibujaba el campo CRUDO transpuesto dentro de cada elemento** — cerrado por
  la sesión 04. `surface_3d_viewer` armaba su geometría con `np.meshgrid` por defecto
  (`indexing="xy"` → `[j_η, i_ξ]`) mientras la Z venía de `compute_raw_grids`, que indexa
  `[i_ξ, j_η]` igual que el rasterizador del contorno 2D. El modo suavizado no lo sufría (X, Y
  y Z salían del mismo `meshgrid`), por eso pasó desapercibido. Hasta 19 % del rango del
  elemento en el ejemplo Cook. Convención documentada en `canvas-preproceso.md` y regresión en
  `tests/test_post_inspection.py` (que además verifica que la transpuesta *sí* difiera en el
  modelo elegido).
- **[4] `Factor de escala` y `Número de niveles` levantaban `TclError` dentro del callback de
  Tk** — cerrado por la sesión 04. Eran `DoubleVar`/`IntVar`: `2,5`, `abc` o vacío mataban el
  handler, el traceback iba a la consola y el alumno no veía nada. Ahora son `StringVar` leídas
  por `_leer_factor_escala` / `_leer_niveles_isolineas`, con `to_float_flex` (la misma
  tolerancia a la coma decimal que los editores de celda del Pre), acotado al rango del
  Spinbox, aviso en la barra de estado y reversión del control al último valor bueno.
- **[4] La Vista 3D no tenía escala de color** — cerrado por la sesión 04
  (`_draw_colorbar` + `fmt_escala` como fuente única con la colorbar del lienzo). Era la única
  vista de resultados sin referencia numérica del color, y la tesis apoya la elección de *jet*
  justamente en esa escala graduada.
- **[4] El `Ctrl+C` del probe copiaba encabezados en inglés y sin unidades**, y era mudo
  cuando no había nada que copiar — cerrado por la sesión 04 (`tsv_headers` + los tres
  mensajes que faltaban).
- **[4] Tres `except Exception: pass` dejaban la Vista 3D mostrando la solución anterior** —
  cerrado por la sesión 04: dejan traza y avisan con `_avisar_3d_desactualizada`.
- **[1 / 4] Realce y hit-test de arista no seguían la malla deformada** — cerrado por la
  sesión 04: `_draw_highlight` y `_hit_test_potential_edge` usan `_get_node_screen_pos` como
  el resto del lienzo.
- **[5] `Ayuda ▸ Acerca de EduFEM` levantaba `NameError`** — cerrado por la sesión 05.
  `about_dialog.py` llamaba `center_dialog(...)` sin importarlo (el archivo hace
  `from ttkbootstrap.constants import *`, que no lo provee). La ventana se armaba pero moría al
  centrarse, así que aparecía descolgada y el traceback iba a `stderr` — invisible en el `.exe`.
  El gate de imports no podía verlo: el módulo importa bien, el `NameError` solo existe al
  ejecutar el `__init__`. Nuevo `run_gates.gate_nombres` (`symtable`, exacto, 0 falsos
  positivos) para cerrar la clase entera.
- **[8] M5 mostraba el integrando simbólico crudo y contaba siempre "0 términos"** — cerrado
  por la sesión 05, encontrado por `gate_nombres`. `mod05_stiffness.py` usaba `sp.latex`,
  `sp.expand`/`sp.Add.make_args` y `sp.pretty` **sin `import sympy`**, y los tres estaban
  dentro de un `except Exception`: degradaba en silencio al `repr` de la expresión. `sympy` ya
  era dependencia declarada (`fem/symbolic_integrand.py`). Medido tras el arreglo: K(1,1) del
  elemento unitario da 5 términos y `sp.latex` renderiza.
- **[5] La rueda del reporte de salud se ataba a toda la aplicación** — cerrado por la sesión
  05. Era `bind_all`/`unbind_all` en un diálogo **no modal**: la rueda sobre el `MeshCanvas`
  hacía zoom y scrolleaba la lista de fondo, `<Destroy>` del footer al 🔄 Re-validar mataba el
  scroll de la propia lista, y al cerrar borraba el binding global de otros widgets. Ahora es
  `self.dialog.bind("<MouseWheel>", …)` sobre el Toplevel. Verificado con Tk real.
- **[5] "📍 Ir al ítem" no hacía nada en los issues de material** — cerrado por la sesión 05.
  El mapeo `kind → (frame, tree)` solo cubre las 5 tablas del Pre y `target_kind="material"`
  caía en un `return` mudo; en `SUSPICIOUS_YOUNG_MODULUS` y `GRAVITY_NO_DENSITY` (no fixables)
  era el único botón de la tarjeta. Ahora deriva a `MaterialDialog(..., seleccionar=…)`.
- **[5] "🔧 Corregir" y "🔄 Re-validar" mudos en sus caminos de fallo** — cerrado por la sesión
  05. Y el "🎓 ¿Por qué?" dejaba de ser clickeable justo después de corregir el issue.
- **[5] `ν = 0,3` bloqueaba el `MaterialDialog` para siempre** — cerrado por la sesión 05 con
  `to_float_flex` (la vía única del programa desde la sesión 02) más la marca en rojo del Entry
  culpable: el botón Guardar gris no decía cuál de los 4 campos lo bloqueaba.
- **[5] Borrar un material en uso no avisaba la consecuencia** — cerrado por la sesión 05: la
  confirmación cuenta los elementos que quedan sin material y recuerda el `Ctrl+Z`.
- **[5] El `Ctrl+Z` del import DXF no revertía la conversión de unidades** — cerrado por la
  sesión 05 (regla dura 4): `stack.capture` estaba **después** de `_apply_project_unit()`, que
  ya había reescalado todas las coordenadas y cambiado `unit_system`. Además el preview releía
  el DXF entero en cada `<Configure>` y reportaba un archivo ilegible como "capa sin
  polilíneas".
- **[5] Cambiar un material no invalidaba la solución** — cerrado por la sesión 08 con
  `MaterialDialog._mark_dirty()`. Los tres flujos seteaban `is_modified = True` pero **no**
  `is_solved = False` (regla dura 12), y la sesión 05 no lo tocó. `post_tab._auto_solve` corta
  con `if self.solution is not None and self.project.is_solved: return`, así que tras bajar E
  a la décima parte el **F5 devolvía las mismas tensiones** y *Exportar Memoria PDF* seguía
  habilitado sobre la corrida vieja. Era el único camino de mutación del proyecto sin la
  invalidación (el autofix de `UNUSED_MATERIAL` ya la hacía). Ahora queda **una sola**
  asignación de `is_modified` en el archivo, para que no se pueda volver a olvidar la otra
  mitad. Regresión: bloque `[10]` de `tests/test_dialogs.py`.
- **[5] El badge de salud mentía tras borrar un material en uso** — cerrado por la sesión 08:
  `_notify_main_window` llama `_update_status_info()`. Los elementos quedaban apuntando a un
  material inexistente (`ELEM_MATERIAL_MISSING`, error crítico) y el badge seguía en «✓ Modelo
  sano» hasta la siguiente acción en otra pestaña. De paso, era el único diálogo del menú
  Modelo que no decía nada en la barra de estado.
- **[5] El botón «Descargar MiKTeX» podía no hacer nada y no decirlo** — cerrado por la sesión
  08. `webbrowser.open` devuelve `False` cuando no encuentra navegador y ese retorno se
  ignoraba, en el único diálogo que aparece **porque el alumno ya está bloqueado**. Ahora
  muestra la URL para copiar a mano.
- **[6] Cancelar el guardado no cancelaba la acción destructiva** — cerrado por la sesión 06.
  *Nuevo Proyecto*, *Cargar Ejemplo* y *Salir* preguntaban «¿guardar los cambios?» y seguían
  adelante **igual** si el guardado no ocurría: contestar *Sí* y después cancelar el diálogo de
  *Guardar Como* (o que fallara la escritura) descartaba el modelo sin decir nada. Los tres
  métodos de guardado devuelven `bool` y los tres flujos pasan por
  `_confirm_discard_changes`. Regresión en `tests/test_main_window.py`.

- **[5 / 6] Ningún diálogo respondía a `Escape` ni a `Return`** — cerrado por la sesión 06 con
  el helper `bind_dialog_keys` y la tabla diálogo → (Escape, Return) documentada en
  `arquitectura.md`. Los 10 cierran con Escape; 8 aceptan con Return; el reporte de salud y el
  de `pdflatex` faltante **no atan Return** a propósito (sus dos salidas son decisiones
  opuestas o se van de la aplicación). Verificado con Tk real bajo `xvfb`.

- **[3 / 6] La sub-pestaña educativa se llamaba distinto en cada fase** — cerrado por la sesión
  06. El `Notebook` de **una sola** pestaña de Proceso desapareció (el panel va directo en el
  frame de la fase), el subtítulo del banner pasó a describir la fase y a nombrar `F5` —que no
  estaba escrito en ninguna parte de esa pantalla—, y las etiquetas visibles quedaron
  acentuadas (`🎓 Educación`, `Módulos Educativos`).

- **[6] `Ctrl+S` sin cambios y `F8` fuera del modo dibujo eran mudos** — cerrado por la sesión
  06. El ítem de menú gris no llega al atajo, y el indicador `ORTHO` solo se muestra dibujando:
  el toggle era **completamente invisible**. También `F11`, que invertía `_is_fullscreen` aunque
  Tk rechazara el cambio.

- **[6] `F1` prometía un manual que no existía** — cerrado por la sesión 06: *Ayuda ▸ Manual de
  Usuario* recorre el flujo real de las tres fases nombrando dónde está cada acción, en vez de
  anunciar «próximamente» y derivar a los atajos (que no son un manual).

- **[7] M1, M2 y M3 seguían mostrando el elemento DESELECCIONADO** — cerrado por la sesión 07
  con un `on_element_deselected` propio en los tres. El default de la base solo hace
  `set_element(None)` + `refresh_overlay()` (un `redraw()` del lienzo): la capa educativa
  desaparecía por su guard `element is None`, pero el overlay seguía con la superficie det J, las
  matrices `∂N`/`Xₑ`/`J`, la cadena `∂N_ξη · J⁻¹ → ∂N_xy → B` y la línea `nodo 3` del elemento
  ido — contradiciendo al halo del lienzo y al chip `#N` del panel de módulos, las otras dos
  vistas que el alumno mira a la vez. Verificado con Tk real bajo `xvfb`; regresión en
  `tests/test_edu_modules_m0_m3.py`.
- **[7] M2 fabricaba `J = identidad` cuando no había elemento** — cerrado por la sesión 07.
  `_build_values_panel` usaba `np.eye(2)` de placeholder, así que abrir `② Jacobiano` sin
  selección (un flujo normal: el launcher no pide elemento a propósito) mostraba una J
  perfectamente plausible con `det J = 1` bajo el título «J en centro del elemento». Ahora el
  placeholder es cero y el título nombra el estado y el gesto. Con él se cerró que las matrices
  de M2 y M3 quedaran **congeladas** con los números del elemento anterior (era un
  `if mat is not None: set_matrix(mat)`) y que el aviso rojo «Elemento degenerado … Reordená los
  nodos» sobreviviera a la deselección (`_refresh_warning` salía por el guard sin limpiar).
- **[7] La nota de M2 mandaba las fórmulas de ∂Nᵢ/∂ξ a M4** — cerrado por la sesión 07. Decía
  `(las formulas de dNi/dxi se ven en M1 y M4)`: cierto antes del swap B↔D de 2026-05 y falso
  desde entonces, porque M4 es la matriz **D** y no muestra ninguna derivada de N. Ahora
  `(∂Nᵢ/∂ξ, ∂Nᵢ/∂η: ver ① Mapeo iso)`, igual que M3, con la etiqueta visible del botón y no la
  key interna. Misma clase de error que la sesión 03 cerró en los mensajes del launcher.
- **[8] M4 mostraba una D completa y plausible sin ningún elemento seleccionado** — cerrado
  por la sesión 09. `_resolve_material` caía en `materials[0]` (etiquetado `"… (fallback)"`, una
  etiqueta que además no se muestra desde el rediseño del espectro) y, sin materiales, en un
  acero inventado (`_DEMO_E = 210e9`, `_DEMO_NU = 0.30`): abrir `Ctrl+4` sin selección llenaba
  el panel *Valores* con una D del orden de 10¹¹ que no era la de ningún elemento elegido — el
  `np.eye` de M2 pero con las unidades correctas. Ahora devuelve `(None, None, None)` y
  `E is None` es la señal del estado: D en ceros (`_current_d`), sin ◆ «tu material» en el
  espectro (ni como ancla de snap) y con el micro-rótulo nombrando el estado y el gesto. El
  espectro, el probe y la fórmula simbólica siguen vivos: son del concepto, no del elemento.
  Verificado con Tk real: `E = 200 GPa` → `E = None`, `max|D| = 0,0`.
- **[8] M5 seguía mostrando la kₑ del elemento DESELECCIONADO** — cerrado por la sesión 09 con
  un `on_element_deselected` propio, el mismo bug que la 07 cerró en M1/M2/M3. El default de la
  base apagaba los glifos de PG del lienzo pero dejaba tres vistas del elemento ido: la kₑ
  completa, el status `Σ 4/4 pg · último: pg4 · |det J|=4.34` y los PGs **dorados** del cuadrado
  natural. La raíz común es `_contributions`; el override la vacía e invalida el cache del
  integrando. Medido con Tk real: `k_e max = 205302,4` → placeholder, status → `''`, PGs
  sumados 4 → 0. Regresión en `tests/test_edu_modules_m4_m7.py`.
- **[8] M6 y M7 ya cumplían el contrato «esperando elemento»** — verificado por la sesión 09 y
  documentado por módulo en `no-reintroducir.md`: M6 opera sobre **cargas superficiales** y su
  `on_element_selected` es un no-op deliberado (**no** agregarle el hook), y M7 ya tenía el
  override (cancela el pulso de ensamblaje, que si no seguía parpadeando ~210 ms sobre el
  elemento deseleccionado).
- **[8] El label de M5 decía «k_e es 8×8 · Q4» en un proyecto Q9 sin selección** — cerrado por
  la sesión 09: `n_nodes` caía en un `4` fijo; ahora lo lee del project vía `_element_type()`.
- **[7] El header de M0 le decía «hover» al alumno** (regla dura 1) y **las coords (x,y) del
  marcador de M2 no pasaban por `fmt`** (regla dura 8, tres decimales distintos a los del lienzo
  para la misma magnitud) — cerrados por la sesión 07.

- **[2] Docstrings de `pre_tab.py` / `_table_helpers.py` que anunciaban features eliminadas**
  (fill-down `Ctrl+D`, navegación Tab/flechas, menú contextual, `on_commit(text, direction)`)
  más 8 encabezados de sección vacíos — cerrado por la sesión 02. Eran una trampa: invitaban a
  "restaurar lo que falta" contra `no-reintroducir.md`.

---

## Propuestas que esperan al autor

Cosas que la rutina **no** hace sin un OK explícito: cambios de alcance, dependencias nuevas,
o reversiones de decisiones congeladas cuya justificación no es evidente.

- *(vacío)*
