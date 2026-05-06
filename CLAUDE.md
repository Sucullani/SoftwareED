# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Project

**EduFEM** — GUI educativa de elementos finitos 2D (plane stress / plane strain) con elementos Q4 y Q9. Stack: `tkinter` + `ttkbootstrap` (tema `darkly`). **User-facing strings, docstrings y comentarios en español** — mantener la convención.

## Running

```bash
python main.py                            # GUI
python -m tests.test_fem                  # validacion FEM (Q4, Q9, surface loads)
python -m tests.test_q9_q4_cycle          # ciclo Q4 -> Q9 -> Q4 sin drift
python -m tests.test_undo_stack           # undo/redo unit tests
python -m tests.test_serialization        # to_dict / restore_from_dict
python -m tests.test_node_cascade         # cascade simetrico de borrado de nodo
python -m tests.test_draw_mode            # modo dibujo: shoelace + snap + commit + auto-CCW
python -m tests.test_pick_ghost           # filas fantasma + filtros + commits con defaults
python -m tests.test_selection_integration # smoke: seleccion multi end-to-end (Tk withdrawn)
python -m tests.generate_example_dxf      # regenera ejemplo DXF
pip install -r requirements.txt
```

Sin pytest/lint — los tests son scripts tipo printout. Proyectos usan extensión `.edufem` (JSON via `ProjectModel.to_dict` / `from_dict`).

## Arquitectura

MVC-ish. La pieza central es `ProjectModel` — todo componente toma una referencia y la muta.

### Data layer — [models/](models/)

`ProjectModel` ([models/project.py](models/project.py)) contiene dicts de `Node`, `Element`, `Material`, `NodalLoad`/`SurfaceLoad`, `BoundaryCondition`, más estado de solución (`displacements`, `stresses`, `global_K`, `global_F`, `is_solved`). DOF de nodo `i` (1-indexed): `2*(i-1)` y `2*(i-1)+1`. Mutaciones deben setear `is_modified = True` y `is_solved = False` — los setters existentes ya lo hacen.

Config global del análisis vive en el project: `analysis_type`, `element_type`, `unit_system`, `gravity` (default `9.81`), `include_gravity`, `custom_units`. Todo serializado en `to_dict`/`from_dict` — campos nuevos van en ambos.

#### Undo / Redo ([models/undo_stack.py](models/undo_stack.py))

Snapshot-based via `to_dict` / `restore_from_dict`. `UndoStack` es pure model, instanciada en `MainWindow.__init__` como `self.undo_stack`. Cualquier mutación del usuario llama `self._capture(label)` (helper en `pre_tab`, `mesh_canvas`, diálogos) **antes** de mutar. Una acción del usuario = un snapshot, sin importar las mutaciones internas que dispare (paste de N filas, expansión Q4→Q9, cleanup en cascada).

Atajos: `Ctrl+Z` (undo), `Ctrl+Y` o `Ctrl+Shift+Z` (redo). Sin item de menú.

Reglas:
- **`restore_from_dict(data)`** muta in-place y resetea solución (`is_solved=False`, etc.). El `from_dict` (classmethod) sigue creando instancias nuevas — usado por save/load. **No** llamar `from_dict` desde flujos que esperan mutación in-place (rompería refs).
- **Listener** `MainWindow._on_state_restored` (registrado en stack) tras un undo/redo: limpia `pending_new` del pre_tab, `clear_highlights()` del canvas, invalida `post_tab.solution`, sincroniza vars (analysis/element/unit) y refresca todo.
- **Identidad del project**: tras restore el objeto sigue siendo el mismo. No reasignar refs.
- **Limpieza del stack**: `clear()` en New, `set_project()` en Open / Cargar Ejemplo / Importar Modelo (replace). Modo merge → `capture("importar modelo (merge)")`.
- **Snapshots livianos**: `to_dict` no incluye solución. ~5–50 KB típicos × 50 niveles ≈ 0.5–2.5 MB.
- **NO capturan**: helpers de mesh (`auto_expand_if_q9`, `recompute_q9_midnodes`, `expand_q4_to_q9`), solving (la solución no está en el snapshot), cambios de vista.
- **Si añadís un flujo de mutación nuevo** (diálogo, handler, importador): llamá `_capture(label)` al inicio, o esa acción no será reversible.

#### Auto-cleanup en cascada al borrar nodos o elementos

Las eliminaciones cascadean simétricamente para que el modelo nunca quede con referencias rotas. **No hay jerarquía de borrado** — el usuario puede borrar nodos o elementos en cualquier orden y el cascade se encarga.

- `remove_element(elem_id, *, cleanup_orphans=True)`: tras borrar el elemento, los nodos del elemento sin otras referencias se eliminan automáticamente *salvo que tengan datos del usuario* (cargas/BCs/surface refs). Esos se preservan como **huérfanos visibles** (naranja en canvas + tabla). Retorna `{"deleted", "nodes_deleted": [...], "nodes_preserved": [...]}`.
- `remove_node_with_cascade(node_id, *, cleanup_orphans=True)`: simétrico al anterior. Borra todos los elementos que contienen al nodo, propaga cleanup a mid/center nodes huérfanos resultantes (preservando los que tengan datos), y borra el nodo objetivo + sus refs (cargas/BC/surface). Retorna `{"node_deleted", "elements_deleted": [...], "nodes_deleted": [...], "nodes_preserved": [...]}`. **Reemplaza al `remove_node` legacy** en todos los flujos UI nuevos.
- `remove_node(node_id)` (legacy): solo borra el nodo + sus refs directas, deja elementos con node_ids inválidos. Equivalente a `remove_node_with_cascade(..., cleanup_orphans=False)`. Mantenido para `from_dict` y casos donde el caller ya garantiza consistencia.
- `preview_node_cascade(node_id) → dict` y `_preview_element_cleanup(elem_id) → dict` calculan el impacto sin mutar — usar para construir el modal de confirmación cuando el cascade afecta a > 1 elemento o preserva huérfanos.
- `is_node_referenced(node_id)` retorna True si el nodo tiene cualquier referencia. Reusado por el cleanup y por el validador.

**Confirmación modal**: tanto `pre_tab._remove_node` como `mesh_canvas._on_delete_key` calculan el preview y abren `messagebox.askyesno` cuando hay impacto no trivial (> 1 elemento, o nodos preservados, o pérdida de datos del usuario). Sin impacto cascade y sin datos → borrado directo.

#### Helpers de malla — [models/mesh_utils.py](models/mesh_utils.py)

- `expand_q4_to_q9(project)`: genera mid-nodes (deduplicados entre vecinos por coord) + centroide. Idempotente. Setea `element_type = ELEMENT_Q9`. Vía canónica para pasar a Q9 — **nunca** duplicar nodos manualmente.
- `shrink_q9_to_q4(project)`: inverso. Trunca a 4 vértices y elimina mid/center huérfanos (preserva los que tengan cargas/BCs/surface refs). Wired en `ElementTypeDialog._on_accept` con confirmación modal.
- `subdivide_q4_mesh(project, levels)`: refinamiento 2×2 (cada Q4 → 4 sub-Q4). Hereda material/espesor, interpola surface loads, hereda cargas/BCs en corners originales. Si encuentra Q9, los trunca antes. Usado por M9.
- `find_edge_midnode(elem, node_start, node_end) → int | None`: dado un Q9 y una arista (en cualquier orientación), retorna el mid-node correspondiente. Usado por `assembly.py` para surface loads Q9.
- `auto_expand_if_q9(project)`: safety net idempotente. En proyectos Q9, expande cualquier Q4 con 4 vértices distintos. Invocado desde `pre_tab` (placeholder + edit + paste + tab change), `dxf_import_dialog` (post-import) y `main_window._on_import_model`. **Cualquier flujo nuevo que cree elementos vía `add_element` debe llamarlo al final.**
- `recompute_q9_midnodes(project, elem)`: tras cambiar un vértice macro, recalcula coords de mid/center. Preserva IDs y datos.
- `classify_orphan_status(project) → dict[node_id → "active" | "orphan"]`: nodo huérfano = no aparece en ningún `element.node_ids`. Ortogonal a `classify_nodes` (corner/mid/center).

### Validador de salud — [models/model_health.py](models/model_health.py)

Función pura `validate_project(project) → HealthReport`. Sin dependencias UI. 3 severidades:

- **Errores críticos** (bloquean solve): `no_elements`, `no_restraints`, `insufficient_restraints` (<3 DOFs), `bc_orphan_node` (DOF colgante restringido), `elem_node_missing`, `elem_material_missing`, `surface_node_missing`, `degenerate_element`.
- **Warnings**: `load_orphan_node`, `unused_material`, `negative_jacobian` (CW), `zero_nodal_load`, `zero_surface_load`.
- **Info**: contadores generales.

Cada `HealthIssue` lleva `severity, code, message, target_kind, target_id, fixable, extra`. `apply_autofix(project, issue)` aplica la corrección para `fixable=True`.

UX:
- **`HealthReportDialog` (no-modal)** ([gui/dialogs/health_report_dialog.py](gui/dialogs/health_report_dialog.py)): se abre en post_tab si hay errores críticos. **Sin `grab_set`** — el usuario puede editar la GUI mientras el diálogo está abierto. `transient(parent)` mantiene subordinación visual. Cada issue tiene "🔧 Corregir" + "📍 Ir al item" (navega y reposiciona el diálogo a la esquina superior derecha) + hint educativo "🎓 ¿Por qué?". Footer con "🔄 Re-validar" (re-corre `validate_project` y reconstruye header + cards), "Volver al Pre-Proceso" (navega a tab 0) y "Resolver/Resolver de todos modos" cuando `allow_continue=True`. Devuelve `result ∈ {"continue", "cancel"}` y `fixes_applied`.
- **Banner en post_tab**: solo warnings, no bloquea. "Ver detalle" abre el dialog en modo solo-consulta.
- **Badge en status bar** ([main_window.py](gui/main_window.py) `_update_health_badge`): `✓ Modelo sano` / `⚠ N warning(s)` / `✗ N error(es)`. Click abre el dialog. Refresco en cada `_update_status_info`. Lazy-import del validador.

Hook en `post_tab.auto_solve`: corre `validate_project` antes del solve. Errores → modal; warnings → banner; sano → procede. Tras auto-fixes, re-valida.

**No duplicar la validación** — agregá `_check_xxx(project, report)` en `model_health.py` y un hint en `EDUCATIONAL_HINTS`.

### FEM engine — [fem/](fem/)

Pure NumPy/SciPy, sin GUI. Pipeline: `shape_functions` → `jacobian` → `b_matrix` → `constitutive` → `stiffness` → `assembly` → `solver` → `stress` / `mesh_quality`. Element type via strings de `config.settings` (`ELEMENT_Q4`/`ELEMENT_Q9`); `GAUSS_POINTS` mapea a 2×2 / 3×3.

**Cargas superficiales** ([fem/equivalent_forces.py](fem/equivalent_forces.py)):
- **Q4**: `surface_load_to_nodal_forces(p_start, p_end, q_start, q_end, angle)` — distribución lineal exacta en 2 nodos, `F1 = L/6·(2·q_s + q_e)`, `F2 = L/6·(q_s + 2·q_e)`.
- **Q9**: `surface_load_to_nodal_forces_q9(p_start, p_mid, p_end, ...)` — funciones 1D cuadráticas, Gauss 2-pts. Con q constante: `L/6, 4L/6, L/6`.

**Dirección de carga = normal EXTERIOR** del elemento (rotación −90° del tangente: `nx0, ny0 = ty, -tx`), asumiendo CCW. `angle=0` ⇒ presión hacia adentro. **No reintroducir** `nx0, ny0 = -ty, tx` (rotación +90°, daba normal interior y aplicaba al revés).

`assembly.assemble_global_system` itera `surface_loads`; en Q9 resuelve mid-node vía `find_edge_midnode`. **Usar `fem/equivalent_forces.py` siempre** — no duplicar desde el módulo educativo M6.

**Extrapolación de esfuerzos** ([fem/stress.py](fem/stress.py)): Q4 con matriz clásica 4×4 basada en `(±√3, ±√3)`. Q9 con `M⁻¹` (cache de módulo) construida evaluando las 9 shape functions en los 9 puntos Gauss 3×3.

**Métricas de calidad** ([fem/mesh_quality.py](fem/mesh_quality.py)): `jacobian_ratio` evalúa en Gauss 2×2/3×3 según element_type. `internal_angles` y `robinson_stretch` operan en las 4 esquinas macro.

### GUI — [gui/](gui/)

[main_window.py](gui/main_window.py): `PanedWindow` horizontal. Izquierda: 3 pestañas (`PreProcessTab`, `ProcessTab`, `PostProcessTab`). Derecha: **un único `MeshCanvas` compartido** — Post overlays resultados sobre el mismo canvas, no swap. `_update_all_project_refs()` rebindea project en todas las tabs/canvas tras cambios.

Switching a Post-Proceso auto-resuelve (`post_tab.auto_solve()` en `_on_tab_changed`). `_refresh_all_tabs()` + `mesh_canvas.redraw()` es el broadcast estándar de "datos cambiaron". Post-tab llama `_refresh_menu_state()` tras solve para habilitar Exportar. **Volver de Post a Pre/Proc** llama `mesh_canvas.clear_results_overlay()` desde `_on_tab_changed` para resetear `show_deformed`, `displacements`, `result_values`, `show_isolines` — el canvas vuelve a mostrar solo geometría (no requiere status).

**Trampa de orden**: las 3 pestañas se construyen **antes** que `MeshCanvas`. Cualquier wiring `*_tab → mesh_canvas` desde `__init__` falla. Solución: método público `_wire_canvas_callbacks()` invocado tardíamente desde `MainWindow._build_main_layout` tras crear el canvas.

#### Barra de menús (filosofía minimalista)

**3 menús únicamente** — decisión de diseño. **No añadir** *Editar*, *Ver*, *Análisis*, *Educación* ni toolbar. Módulos educativos por fase: M0 en pre, M1..M6 en proc, M7..M9 en post. `Ctrl+1..6` abren los módulos M1..M6. **M3 vive en proc** (no en el menú Modelo) porque la matriz D depende del material asignado a CADA elemento — la exploración por-elemento es natural en la fase de Proceso, junto a B/K/F. El submenú *Modelo > Tipo de Análisis* solo carga videos didácticos de TP/DP, sin la matriz D.

| Menú | Contenido |
|---|---|
| 📁 **Archivo** | Nuevo / Abrir / Recientes ▸ / Guardar / Guardar Como / **Importar ▸** (Geometría DXF, Modelo Excel/CSV) / **Exportar ▸** (Modelo Excel/CSV, Memoria de Cálculo PDF) / Salir |
| 📐 **Modelo** | Tipo de Elemento / Unidades y Gravedad / Materiales / Tipo de Análisis — 4 pop-ups autónomos en orden FEM |
| ❓ **Ayuda** | Manual / Atajos / **Cargar Ejemplo ▸ (Q4/Q9)** / Acerca de |

**Decisiones de etiquetado**:
- *Cargar Ejemplo* vive en **Ayuda** — los ejemplos son material didáctico, no archivos del usuario. Mantener el atajo `Ctrl+E` (compat histórica).
- *Importar/Exportar Modelo* lleva el sufijo `(Excel/CSV)` para distinguirlo de *Abrir/Guardar Proyecto* (`.edufem` JSON nativo, no editable a mano). El ZIP de CSVs es la vía editable en Excel para edición masiva.
- *Memoria de Cálculo (PDF)* — no "Reporte". Anticipa la expansión hacia un documento didáctico paso a paso (fórmulas, K, B, D, vectores, diagramas) alineado al espíritu de los módulos M1..M9. Hoy el output sigue siendo tabular (reportlab); el rename es deliberado para fijar la dirección.
- *Exportar Resultados CSV* fue **eliminado del menú** — los resultados se copian directamente desde la tabla del Post-Proceso con `Ctrl+C` (TSV al portapapeles, pegable en Excel). `selectmode="extended"` + `Ctrl+A` permiten seleccionar todo o subconjuntos. **No reintroducir** la entrada de menú.

**Orden FEM del menú Modelo**: Elemento → Unidades → Material → Análisis. Sigue el flujo lógico de definición de un problema FEM: primero la geometría discreta (Q4/Q9), después cómo se mide (sistema de unidades), después de qué está hecho (E, ν, ρ por material), y al final el tipo de problema (TP / DP), donde la matriz constitutiva D = D(E, ν, caso) combina material y análisis. **No reordenar** salvo que se replantee el flujo pedagógico.

Diálogos en [gui/dialogs/](gui/dialogs/): `(parent, project, main_window=None)`. Invocables desde menú o desde tabs sin acoplarse. `MaterialDialog` se **amplía** (`TYPICAL_MATERIALS`, color picker, vista previa) — no separar en librería externa.

**`ElementTypeDialog`** ([gui/dialogs/element_type_dialog.py](gui/dialogs/element_type_dialog.py)) soporta Q4↔Q9 en ambos sentidos: Q9 sobre Q4 → `expand_q4_to_q9`; Q4 sobre Q9 → `shrink_q9_to_q4` con confirmación modal. Tiene 2 pestañas: "Comparación visual" (Q4 vs Q9 lado a lado, matplotlib estático) y **"Transición Q4 ↔ Q9"** (WebP animado prerenderizado en Claude Design — `resources/videos/q4_q9_transition.webp`, 900×600, 7.0 s seamless loop, sobre un elemento distorsionado canónico — autoplay sin barra de controles vía `gui.widgets.WebpPlayer` directo). Banner superior enfatiza que el cambio es **bidireccional**. **NO muta el modelo** — la mutación real ocurre solo al Aceptar el `Radiobutton` Q4/Q9 del header. Si el archivo `.webp` no existe, degrada gracefully a un placeholder textual.

**`AnalysisTypeDialog`** ([gui/dialogs/analysis_type_dialog.py](gui/dialogs/analysis_type_dialog.py)) es **minimalista**: `Radiobutton` TP/DP + UNA SOLA ventana de video que se reasigna según la selección. Cambiar TP↔DP recarga `resources/videos/tension_plana.webp` o `resources/videos/deformacion_plana.webp` en el mismo widget `WebpPlayer` (autoplay, loop seamless, sin barra de controles). Si el `.webp` falta, el frame degrada a un mensaje informativo con la ruta esperada. **NO contiene la matriz D** — esa explora por-elemento desde el módulo M3 (Proceso > Educación) porque depende del material. **Hereda de `ttk.Toplevel`, NO de `BaseEducationalModule`** — es UI minimalista del menú, no un módulo educativo.

**Anti-pattern (no hacer)**: usar `FuncAnimation` sin guardar referencia persistente — el GC mata la animación y/o freeza el `Toplevel` modal. Patrón correcto: `self._anim = FuncAnimation(...)` + `self._anim.event_source.stop()` en cierre. Las animaciones del `ElementTypeDialog` migraron a WebP animado prerenderizado y el `AnalysisTypeDialog` usa solo WebP — el patrón sigue documentado por si se reintroduce en algún módulo educativo nuevo.

**Reproductor de WebP animado** ([gui/widgets/webp_player.py](gui/widgets/webp_player.py)): widget `WebpPlayer(parent, scaled=True, background=...)` lightweight basado **solo en Pillow** (sin `PyAV`/FFmpeg → ahorra ~30 MB en el instalador PyInstaller). API: `load(path) → play() → stop()`. Loop seamless interno (no requiere bind `<<Ended>>`). Decoder on-the-fly por frame, sin cache (RAM constante). Expone `seek_frame`, `seek_ms`, `n_frames`, `current_time_ms`, `total_duration_ms` y callback opcional `on_frame_change(idx, cur_ms, total_ms)` para wrappers con scrubber (ver [education/components/video_player.py](education/components/video_player.py)). **Trampa**: el muxer libwebp de ffmpeg escribe `duration=0` por frame — `WebpPlayer.load` trata 0 como ausente y aplica 45 ms (~22 fps) por defecto, así que la duración total es coherente.

**Pipeline de generación de videos** (Claude Design → WebP): el script [tools/render_q4q9/record.mjs](tools/render_q4q9/record.mjs) usa Chrome headless + DevTools Protocol (WebSocket nativo de Node 24+, sin instalar paquetes) + ffmpeg. Pasos: descargar bundle tar.gz desde Claude Design, levantar `python -m http.server`, capturar JPGs vía `Page.startScreencast`, recortar a `frames_per_loop = duration_loop * fps_real` para loop seamless, componer con `ffmpeg -framerate <real> -frames:v <N> -c:v libx264 out.mp4` y luego convertir a WebP animado: `ffmpeg -i out.mp4 -vcodec libwebp -filter:v "fps=22,scale=900:600:flags=lanczos" -lossless 0 -compression_level 6 -q:v 75 -loop 0 -an -vsync 0 out.webp`. Reusable para futuras animaciones generadas en Claude Design. **No reintroducir** la dependencia `tkvideoplayer` ni `av`/`PyAV` — la migración a WebP es deliberada (instalador PyInstaller más liviano, sin DLLs FFmpeg que disparan falsos positivos de antivirus).

**`DxfImportDialog`** ([gui/dialogs/dxf_import_dialog.py](gui/dialogs/dxf_import_dialog.py)): file picker en `main_window._on_import_dxf` se abre **antes** del Toplevel (cancelar = no diálogo). Layout minimalista: 2 combos + preview en `tk.Canvas` nativo + botones.

**Decisiones explícitas** (no reintroducir):
- Sin toolbar.
- Sin menú "Preferencias / Configuración" — defaults sanos hardcodeados en `config/settings.py` (tolerancias, decimales, colores). Cambiar la constante propaga a toda la UI.
- Separador decimal: `.`, pero los `_paste_*` deben tolerar `,` (Excel español): `try float(v); except float(v.replace(",", "."))`.

**Título dinámico**: prefijo `●` cuando `is_modified`. Llamar `_update_title()` tras mutaciones.

**Enable/disable inteligente** (`_refresh_menu_state`): Save según `is_modified`, Memoria de Cálculo (PDF) según `is_solved`. Sincronizado vía **`postcommand` del `menu_archivo`** — se dispara automáticamente al abrir el menú, así no hay que llamar `_refresh_menu_state` desde cada mutación del spreadsheet/canvas. Las flags `is_modified`/`is_solved` ya las setean los setters del `ProjectModel`; el postcommand solo sincroniza la UI cuando el usuario va a verla. **No reintroducir** llamadas explícitas a `_refresh_menu_state` tras mutaciones — duplica trabajo.

**Atajos** (en `_bind_shortcuts` y reflejados en `_on_shortcuts`):

| Atajo | Acción |
|---|---|
| Ctrl+N / O / S / Shift+S | Nuevo / Abrir / Guardar / Guardar Como |
| Ctrl+E | Cargar Ejemplo |
| Ctrl+Q | Salir |
| Ctrl+Z / Y / Shift+Z | Deshacer / Rehacer / Rehacer alt — ver `models/undo_stack.py` |
| Ctrl+1..6 | Módulos educativos M1..M6 (M3 = matriz D, opera por elemento) |
| F5 | Resolver |
| F11 / F | Pantalla completa / Ajustar vista |
| D | Toggle modo dibujo de elementos (canvas-driven, ver `mesh_canvas.py`) |
| Ctrl+Click / Shift+Click | (canvas) selección múltiple (toggle / range) |
| Esc | Cascada: cancela elemento parcial → cierra cell editor → limpia selección |
| Ctrl+Tab / Shift+Tab | Pestaña sig / ant |
| Ctrl+/ / F1 | Atajos / Manual |

`_is_entry_focused()` corta atajos de una sola tecla cuando el foco está en `Entry`/`Combobox`. Atajos nuevos van en `_bind_shortcuts` Y `_on_shortcuts` — deben coincidir.

**Archivos recientes**: persistencia JSON en `~/.edufem/recent.json` ([config/recent_files.py](config/recent_files.py), `RECENT_FILES_MAX = 10`). `recent_files.add(path)` tras guardar/abrir + `_build_recent_menu()`.

### Módulos educativos — [education/](education/)

9 módulos distribuidos por fase. Registro centralizado en [education/module_launcher.py](education/module_launcher.py): `MODULE_MAP` (mod_key → clase), `MODULE_PHASE` (`pre/proc/post → list`), `MODULE_META` (label + descripción), `_GLOBAL_MODULES` (no requieren elemento seleccionado), `list_modules_for_phase(phase)`, `open_module(...)`. **Si añadís un módulo, registralo en los 4 dicts.**

#### Dos modos de presentación (rediseño UX 2026)

A partir de la propuesta UX, los módulos se dividen en dos modos de presentación según la naturaleza pedagógica del concepto que enseñan:

| Modo | Patrón base | Cuándo |
|---|---|---|
| **Toplevel** | hereda de [BaseEducationalModule](education/base_module.py) | módulos amplios, comparación lado-a-lado independiente del modelo, vista 3D pantalla completa, sandbox |
| **Overlay** | hereda de [CanvasOverlayModule](education/overlay_module.py) | concepto que vive *sobre* la malla real (glow, cruces, coloreado, drag de nodo); el alumno NO debe perder el contexto del modelo |

El despacho lo hace `module_launcher.open_module(...)` automáticamente: si la clase tiene un `classmethod activate(main_window, project, elem_id)` se abre como Overlay; si no, se instancia como Toplevel. **No mezclar herencias** — cada módulo elige UNO solo.

#### Estado actual de los módulos

| ID | Fase | Modo | Concepto |
|----|------|------|----------|
| M0 | pre  | **Overlay** | Calidad geométrica: vista rayos X (verde/amarillo/rojo) + radar flotante en hover + drag de nodo distorsiona en vivo |
| M1 | proc | Toplevel | Coordenadas naturales, Nᵢ, Jacobiano (4 paneles 2×2) |
| M2 | proc | **Overlay** | Matriz B: glow pulsante en puntos Gauss del canvas + toggle Fórmula↔Valores |
| M3 | proc | **Overlay** | Matriz D(E,ν, caso): dial físico de Poisson + toggle Fórmula↔Valores. Caso plano se LEE del project (sin TP/DP local — está en Modelo ▸ Tipo de Análisis). Click en otro elemento del canvas → cambia el material. |
| M4 | proc | Toplevel | Integrando simbólico + cuadratura de Gauss |
| M5 | proc | Toplevel | Ensamblaje K/F + flying elements + sistema reducido |
| M6 | proc | Toplevel | Fuerzas equivalentes nodales |
| M7 | post | Toplevel | Discontinuidad σ vs promediado nodal |
| M8 | post | **Overlay** | Cruces principales σ1/σ2 sobre canvas + Mohr en panel flotante con doble vínculo bidireccional (drag del punto sobre Mohr → rota TODAS las cruces de la malla) |
| M9 | post | Toplevel | Sandbox Q4 vs Q9 con `subdivide_q4_mesh` |

#### Infraestructura del modo Overlay

Tres piezas reutilizables — **no duplicar**:

- **[gui/widgets/canvas_overlay.py](gui/widgets/canvas_overlay.py)** `CanvasOverlay`: panel flotante draggable/cerrable posicionado vía `place()` sobre un widget Tk (típicamente el `MeshCanvas`). Header con barra de color por fase + título + botón ×. Cuerpo expuesto como `self.body`. Drag por header (cualquier punto). `phase` ∈ `{"pre", "proc", "post"}` controla el color.
- **[education/components/formula_value_toggle.py](education/components/formula_value_toggle.py)** `FormulaValueToggle`: requerimiento del usuario. Segmented toggle `[ƒ Fórmula | 123 Valores]` + axes matplotlib embebido. Recibe dos callbacks `render_formula(ax)` y `render_values(ax)`. `refresh()` redibuja el modo activo (llamar tras cambiar datos). **Patrón canónico para overlays con LaTeX** — todos los modos B con fórmulas DEBEN usar este toggle, no embeber la fórmula directamente.
- **[education/overlay_module.py](education/overlay_module.py)** `CanvasOverlayModule`: base class. Singleton suave por `(main_window, cls)` (re-activar trae al frente en lugar de duplicar). Engancha callbacks del canvas (`on_element_select`, `on_node_select`, `on_hover_element`) y los restaura al cerrar. Registra una "capa educativa" via `mesh_canvas.add_overlay_layer(layer_callable)` que dibuja con tags propios (prefijo `edu_X`). El cleanup limpia capa + callbacks + slot del singleton.

Hooks que cada módulo Overlay sobrescribe:
- `build_overlay(self, body)` — poblar el panel flotante
- `draw_canvas_layer(self, mesh)` — dibujar la capa sobre el `MeshCanvas` (delete del tag propio + create_*)
- `on_element_selected(self, elem_id)` — click en elemento del canvas (default: cambia `self.element_id` y refresca)
- `on_node_selected(self, node_id)` — click en nodo del canvas (default: no-op)
- `refresh_overlay(self)` — llamado tras cambios (default: `mesh.redraw()`)

#### Reglas de oro del modo Overlay

1. **Click en MeshCanvas elige el target** — NUNCA un combobox interno duplica la selección. El módulo *consume* la selección.
2. **La iluminación se aplica al canvas REAL** vía `add_overlay_layer`, no a una copia auxiliar.
3. **Los datos extensos (matrices LaTeX, gráficos)** viven en el overlay flotante. Arrastrable, cerrable.
4. **Tags propios con prefijo `edu_X`** (donde X = módulo): `edu_m0`, `edu_m2`, etc. El primer paso de `draw_canvas_layer` es siempre `mesh.canvas.delete(_TAG)`.
5. **Pulsación / animación**: usar `mesh.after(33, callback)` para ~30 fps. Guardar el `after_id` para cancelarlo en `on_closed()`.
6. **No mutar el project sin confirmar** — el drag de M0 distorsiona la *visualización* pero NO el `project.nodes`. La mutación real requiere acción explícita del usuario.

#### Migración pendiente (M1 / M4 / M5 / M6 / M7 / M9)

Por riesgo creciente, según la propuesta UX:

**Fase 1 (riesgo bajo) — completada parcialmente.** M7 + M8 eran candidatos prioritarios (post-proceso, no tocan solver). M8 ya está migrado a Overlay. **M7** (discontinuidad σ) sigue pendiente: vista 3D rotable con slider gigante "Crudo ↔ Promediado" + chips de componente + detector de aristas con discontinuidad >10%. Permanece como Toplevel por la vista 3D ocupando pantalla completa, pero el slider gigante puede migrarse al footer del MeshCanvas como capa overlay.

**Fase 2 (riesgo medio) — completada.** M0 + M3 ya migrados.

**Fase 3 (riesgo alto) — pendiente.**
- **M1 (mapeo isoparamétrico)**: queda como Toplevel — split mirror animado (físico ↔ natural) requiere panel doble que no encaja en un overlay flotante. El selector Q4/Q9 local SE PRESERVA aquí (única excepción legítima: el módulo enseña la diferencia entre interpolación bilineal y bicuadrática, no muta el project).
- **M2 (matriz B)**: ya migrado.
- **M5 (ensamblaje K, F)**: candidato a Overlay con animación Bézier de "vuelo" del bloque kₑ → bloque destino en K. Pendiente — requiere canvas auxiliar con heatmap de K. Por ahora Toplevel.
- **M6 (fuerzas equivalentes)**: candidato a Overlay con drag-to-load + lluvia de partículas que caen a los nodos. La activación cambia el cursor sobre el canvas a "modo carga". Pendiente.
- **M9 (Q4 vs Q9 sandbox)**: queda como Toplevel — comparación lado-a-lado + plot de convergencia log-log requiere ventana propia con `deepcopy(self.project)` y `file_path = None`.

**Fase 4 (último) — M4** (rigidez + Gauss) por la complejidad de la "cinta transportadora" de PG. Queda como Toplevel.

Subclases Toplevel siguen el contrato existente de [BaseEducationalModule](education/base_module.py): `build_controls`, `build_visualization`, `build_theory` (opcional), `animate_step` (opcional con `StepAnimator`).

Componentes en [education/components/](education/components/): `PlotPanel`, `FourPanel`, `ParamInput`, `StepAnimator`, `TheoryViewer`, `TheoryDoc`, `FormulaValueToggle`, `render_matrix_latex` / `render_expression_latex`, `iso_inverse_map`. **No duplicar `fem/`** — los módulos solo visualizan.

**Convenciones módulos educativos**:
- **LaTeX matrices**: `render_matrix_latex` ahora hace renderizado MANUAL por celdas (con corchetes dibujados manualmente). matplotlib mathtext **NO soporta `\begin{bmatrix}`** — el código previo caía silenciosamente al fallback `str(numpy_array)` (ilegible). El renderizado manual acepta cells de `str` (símbolos), `float` (numérico), o `sympy` con `sp.pretty()`. **No reintroducir** `\begin{bmatrix}` en strings de mathtext.
- **LaTeX expresiones escalares** (fracciones, integrales, sumatorias): `render_expression_latex` con mathtext. Funciona bien para todo *excepto* matrices.
- **Subíndices Unicode**: usar sufijos ASCII (`N1x`, `N1y`) en lugar de subíndices Unicode tipográficos (`ᵧ` = U+1D67) — algunos no están en `DejaVu Sans Mono` y disparan warnings de glifo faltante.
- **Video / animación**: WebP animado vía [WebpPlayer](gui/widgets/webp_player.py) o [VideoPlayer](education/components/video_player.py). Assets en [resources/videos/](resources/videos/) con extensión `.webp`. Degradar a mensaje si falta. **No usar** `tkvideoplayer`/`av`.
- `SymbolicIntegrandQ4` / `SymbolicIntegrandQ9` viven en mod04; mover a `fem/` si se reusan.
- Soporte Q9: usar `get_shape_functions(project.element_type)` y `elem.num_nodes`/`elem.node_ids` (no `range(4)`). Métricas de contorno macro: `[:4]` con comentario explícito.
- **Sandbox modules (M9 y similares)**: `deepcopy(self.project)` + `file_path = None`. Nunca mutar el original.

### Otros archivos importantes

- [config/settings.py](config/settings.py): magic strings, colores, tolerancias, fonts, decimales. **Importar desde aquí, no hardcodear**.
- [config/units.py](config/units.py): 9 sistemas predefinidos + `Personalizado`.
- [gui/widgets/](gui/widgets/): `ToolTip`, `phase_banner.build_phase_banner`, `module_launcher_panel.render_module_buttons`.
- [file_io/](file_io/): CSV ([csv_io.py](file_io/csv_io.py) con columnas dinámicas Q4/Q9), PDF (reportlab/PyMuPDF/pylatex), JSON proyecto, ZIP modelo, DXF (ver sección dedicada).
- [tests/example_data.py](tests/example_data.py): canónico (E=225000, ν=0.2, t=0.8, P=1000). `load_example_project(P)` Q4 9-nodos, `load_example_project_q9(P)` 25-nodos.

## Importación DXF

Módulo [file_io/dxf_io.py](file_io/dxf_io.py) + diálogo [gui/dialogs/dxf_import_dialog.py](gui/dialogs/dxf_import_dialog.py).

**Dependencia `ezdxf>=1.0`** import diferido vía `_require_ezdxf()` — falla con mensaje detallado si falta. Caso Windows: `python -m pip install ezdxf` (bypasea launcher roto).

**Convención**: capa `FEM_ELEMENTS` con polilíneas cerradas de 4 vértices → Q4. Otras capas se ignoran. **No hay capa `FEM_NODES`**.

**Flujo**: file picker en `main_window._on_import_dxf` ANTES del Toplevel; cancelar = nada. `DxfImportDialog(parent, project, main_window, filepath=path)` carga capas + preview en `tk.Canvas` nativo.

**Diálogo**: 2 combos (Unidades del proyecto + Capa) + preview. Cambiar unidades dispara: (a) re-escala coords existentes (`old_m / new_m`), (b) setea `unit_system` al sistema canónico de esa longitud.

**Idempotencia**: dedupe topológico por `frozenset(elem.node_ids[:4])`. Re-importar el mismo DXF reporta `elements_skipped_duplicate = N` sin mutar. Replicar este patrón en otros importadores (STEP, IGES, JSON).

**Orden CCW forzado**: shoelace < 0 → invertir antes de crear el Q4.

`import_dxf(filepath, project, scale=1.0, layer_elements="FEM_ELEMENTS")` retorna `{"nodes_added", "elements_added", "elements_skipped_duplicate", "warnings", "q9_auto_expanded"}`.

## Tipografía y decimales

Fonts en [config/settings.py](config/settings.py) — **importar siempre, no hardcodear**:

| Constante | Valor | Uso |
|---|---|---|
| `FONT_UI` | Segoe UI 9 | Default UI |
| `FONT_UI_LARGE` | Segoe UI 10 | Treeview body + editor flotante |
| `FONT_UI_BOLD` | Segoe UI Semibold 9 | Headings, labels |
| `FONT_MONO` / `FONT_MONO_SMALL` | Consolas 10/9 | Código, coords canvas |
| `TREE_ROW_HEIGHT` | 22 | Compacto |

Decimales por magnitud — usar siempre `fmt(value, kind)`, no `f"{x:.4f}"`:

| Constante | Default | Uso |
|---|---|---|
| `DECIMALS_LENGTH` | 3 | X, Y, espesor |
| `DECIMALS_FORCE` | 2 | Fx, Fy, q, reacciones |
| `DECIMALS_STRESS` | 2 | σ, τ, von Mises |
| `DECIMALS_DISPLACEMENT` | 5 | u, v (científico `:.5e`) |
| `DECIMALS_ANGLE` | 1 | θ° |

**Trampa**: el editor flotante debe pre-llenar con el mismo string que la celda muestra (`current=fmt(raw, kind)`), no el float crudo — sino "salta" perdiendo decimales al abrir.

## Spreadsheet de Pre-Proceso ([gui/preprocessing/pre_tab.py](gui/preprocessing/pre_tab.py))

5 tablas (`Nodos`, `Elementos`, `Cargas`, `Restricciones`, `Carg. Superf.`) en `ttk.Notebook`. Helpers en [_table_helpers.py](gui/preprocessing/_table_helpers.py).

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

**Pre-flight de material** ([pre_tab._on_toggle_draw_mode](gui/preprocessing/pre_tab.py)): si `project.materials` está vacío al activar, abre `MaterialDialog` antes (mismo patrón que el placeholder de la tabla Elementos). Sin material → no entra al modo. El elemento creado usa `materials[0]` y `default_thickness`, editables después en el spreadsheet.

**Callbacks de sincronización** (`_wire_canvas_callbacks`):
- `canvas.on_draw_mode_changed = pre_tab._on_canvas_draw_mode_changed`: sincroniza el `bootstyle` del botón (`info-outline` → `info` cuando activo).
- `canvas.on_draw_element_created = pre_tab._on_canvas_draw_element_created`: refresca tablas Nodos + Elementos + título tras el commit.

**Auto-desactivación**: cambiar a Proc/Post o un undo/redo (vía `_on_state_restored`) desactiva el modo automáticamente — los puntos pendientes podrían referenciar nodos que ya no existen tras el restore.

**Lógica testeable**: `MeshCanvas._shoelace_signed(pts)` es `staticmethod` — los tests en [test_draw_mode.py](tests/test_draw_mode.py) reproducen el commit sin Tk usando solo `ProjectModel` + `auto_expand_if_q9`.

### Estilo Treeview

Fondo plano uniforme `ROW_BG = #1c1e22` — el zebra striping fue retirado: con 4 estados semánticos (`canvas_selected` amarillo, `orphan_node` naranja, `pending_pick` azul, `placeholder` gris) ya hay suficiente carga cromática; agregar zebra competía con ellos. **No reintroducir** `even`/`odd`. Bordes pixel-perfect no son posibles en `ttk.Treeview`. **No migrar a `tksheet`** (descartado).

`_apply_global_tree_style`: `rowheight = font.metrics("linespace") + 6`, layout con `sticky=""` en `Treeitem.text`, heading `relief="raised" padding=(8,4) anchor="center"`, body `relief="flat"`.

Tags estándar en `_configure_row_tags`:
- `placeholder`: gris desaturado para "+ doble-click..."
- `auto_node`: foreground gris (`AUTO_NODE_FG`) — Q9 mid/center read-only
- `orphan_node`: foreground naranja (`ORPHAN_NODE_FG`) + background tintado (`ORPHAN_NODE_BG`) — nodos huérfanos preservados

### Render del canvas

**Highlight uniforme** (decisión): cambio de color a `CANVAS_SELECTED_COLOR` sobre la geometría real, **NO** halos extra. Aplica a nodos, elementos, cargas, restricciones, surface loads. `_draw_highlight()` está intencionalmente vacío.

**Símbolos de restricción** (notación estándar, `_draw_constraints`):
- `is_fixed`: triángulo + línea base + 3 hachuras (empotramiento).
- `is_roller_y`: triángulo apoyado en círculo (rodillo) sobre superficie horizontal.
- `is_roller_x`: rotado 90° con pared vertical y rodillo entre ella y el triángulo.

**No** dibujar `is_roller_x` como triángulo lateral sin rodillo (era indistinguible del empotramiento).

**Glow simulado**: 2 `create_line` superpuestas (`width+3` con color `SHADOW_*`, encima la línea principal). Aplicado a `_draw_loads` y `_draw_surface_loads`.

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

Banner con `gui/widgets/phase_banner.py::build_phase_banner`. Cada fase tiene su sub-pestaña "🎓 Educación".

## Lineamientos de calidad

### Paleta congelada

Todos los colores viven en [config/settings.py](config/settings.py). Familias:
- Fases: `PHASE_PRE/PROC/POST_COLOR` y bootstyles asociados.
- Canvas geometría: `CANVAS_BG`, `CANVAS_GRID`, `CANVAS_NODE` (+ MID/CENTER/ORPHAN), `CANVAS_ELEMENT`.
- Canvas propiedades: `CANVAS_LOAD/CONSTRAINT/SELECTED_COLOR`.
- Sombras y labels: `SHADOW_*`, `LABEL_BG/FG`.
- Salud del modelo: `HEALTH_OK/WARNING/ERROR/INFO_COLOR`.

**Reglas no negociables**:
1. **Cero hex literales fuera de `config/settings.py`**. Nuevos colores → constante nombrada → import.
2. Naming `<DOMINIO>_<USO>_COLOR`. Agregar en sección comentada existente, no al final.
3. Mapas matplotlib: `viridis` o `coolwarm`. **No** `jet`/`hsv` — perceptualmente desiguales.
4. Estados de validación: verde = `PHASE_POST_COLOR` o `HEALTH_OK_COLOR`, naranja = warning, rojo = error.
5. Highlight: `CANVAS_SELECTED_COLOR` amarillo es el único — no reemplazar por color de propiedad.
6. Bootstyles dentro de pestañas de fase: heredar `PHASE_*_BOOTSTYLE`.
7. **Auditoría pre-merge**: `Grep` `#[0-9a-fA-F]{3,8}` sobre `gui/**` + `education/**` (excluir `config/`). Esperado: 0 hits.

La paleta cumple WCAG AA contra fondo `darkly` (#212529); azul/naranja/verde tiene significado pedagógico (modelado → análisis → resultado).

### Roadmap incremental del motor FEM

API pública `solve_system(project) → dict` queda fija para no obligar a tocar `post_tab`, `pdf_report`, M5, M9.

Prioridades sugeridas (mantener API estable):

1. **K sparse** (alta): `scipy.sparse.csr_matrix` vía COO incremental. Memoria O(nnz). Mantener rama densa solo para M5 (`K.toarray()`). El resto consume K vía operadores sparse-friendly.
2. **Solver SPD sparse** (alta): `scipy.sparse.linalg.spsolve` (UMFPACK) por default, opcional `sksparse.cholmod.cholesky` con import diferido (pattern `_require_cholmod()` igual que `ezdxf`).
3. **RCM** (media): `scipy.sparse.csgraph.reverse_cuthill_mckee` antes de factorizar. 2–5× menos fill-in en mallas estructuradas. Flag `SOLVER_USE_RCM` en settings para comparar en M9.
4. **Ensamblaje vectorizado** (media): `np.einsum("egki,kl,eglj,eg,g->eij", ...)` batch. **Mantener** la versión escalar como referencia pedagógica para M2/M4/M5. Decidir cuál usar según `VECTORIZED_THRESHOLD`.
5. **Cache de B/J por shape signature** (baja): solo si profiling muestra que domina.
6. **SRI / B-bar para volumetric locking** (baja, alto valor pedagógico): opt-in vía `Material.use_sri`. Excelente para un módulo M10 "Locking volumétrico".

**Reglas transversales**:
- **Pureza `fem/`**: cero imports de tk/matplotlib/ttkbootstrap. Debe correr sin GUI.
- **Tipado**: `from __future__ import annotations` + type hints en firmas públicas.
- **Tolerancias centralizadas**: `NUMERICAL_TOLERANCE = 1e-10`, `JACOBIAN_MIN_DETERMINANT = 1e-12` de settings. No introducir tolerancias locales ad-hoc.
- **Regresión numérica**: cualquier cambio en `assembly`/`solver`/`stress` debe pasar `test_fem` con `max |Δu| ≤ 1e-9`.
- **Profiling antes de optimizar**: `cProfile` + `snakeviz` sobre 500–1000 nodos. La intuición sobre dónde está el costo suele estar mal (típicamente ensamblaje en Python, no factorización).
- **Compatibilidad con M2/M4/M5**: si añadís variante optimizada, exponer también la legible vía `return_intermediate=True` o `fem/educational.py` paralelo. **No** sacrificar claridad pedagógica por velocidad.

## Flujo de revisión y mejora de código

En cada mensaje del usuario que implique revisar, modificar o extender código, aplicar este protocolo de cuatro pasos. Aplica a todo cambio — no solo a tareas explícitas de "review".

### 1. Detección de errores

Auditar los archivos tocados (y los que el cambio impacta lateralmente) buscando:

- **Errores funcionales**: lógica incorrecta, ramas inalcanzables, off-by-one, condiciones invertidas, race conditions en callbacks Tk, refs rotas tras mutaciones del `ProjectModel`.
- **Errores de flujo**: mutaciones sin `_capture()` previo (rompen undo), helpers de mesh sin `auto_expand_if_q9` al final, falta de `is_modified=True` / `is_solved=False`, hex literales fuera de `config/settings.py`, decimales hardcodeados sin `fmt(value, kind)`.
- **Ineficiencias**: loops O(n²) sobre nodos cuando hay dict lookup disponible, `K.toarray()` innecesario, recomputo de `B`/`J` cuando ya hay cache, redibujado completo del canvas cuando bastaría un overlay.
- **Malas prácticas**: imports de `tk`/`matplotlib` dentro de `fem/`, hex literales, tolerancias locales ad-hoc, duplicación de lógica de `fem/equivalent_forces.py` en módulos educativos, uso de `from_dict` cuando se requiere mutación in-place, `tree.selection_set` desde callback canvas → spreadsheet.

### 2. Corrección y mejora

- Aplicar las correcciones en el mismo cambio (no abrir un follow-up para cada error trivial).
- Sustituir implementaciones deficientes por algoritmos más eficientes/idiomáticos cuando el ratio costo/beneficio sea claro: dict en vez de búsqueda lineal, vectorización NumPy en lazos numéricos, `scipy.sparse` cuando aplica, `frozenset` para dedupe topológico.
- **Preservar la versión legible** cuando el código tiene valor pedagógico (M1..M9, `fem/` referencia para M2/M4/M5) — exponer la variante optimizada en paralelo, no reemplazar.
- Justificar cada mejora en una línea: `# vectorizado: O(n²) → O(n) en ensamblaje de surface loads`. Razón ∈ {rendimiento, claridad, mantenibilidad, consistencia con convención existente}.

### 3. Consistencia del documento

- Tras editar `CLAUDE.md`, releer el bloque modificado en contexto: ¿contradice una sección anterior? ¿duplica una regla ya enunciada? ¿deja una decisión ambigua?
- Si una nueva regla invalida una existente, **eliminar la vieja** — no acumular contradicciones marcadas con "actualización" o "ver también".
- Mantener la convención de español, los enlaces `[archivo](ruta)` clickeables, las tablas para enumeraciones tabulares y los **negritas** para reglas no negociables.

### 4. Registro de cambios

Al final de cada respuesta que modifique código (no aplica a respuestas puramente exploratorias), incluir un bloque `## Resumen de cambios` con:

- **Errores detectados**: bullet list, una línea por error con `archivo:línea` cuando aplique.
- **Cambios realizados**: bullet list de las modificaciones, agrupadas por archivo.
- **Algoritmos/enfoques mejorados**: solo si hubo sustitución no trivial — qué se reemplazó, por qué.
- **Impacto esperado**: rendimiento (orden de magnitud o medición), claridad, robustez, o "ninguno funcional, refactor de consistencia".

Si no hubo errores ni mejoras de algoritmo (típico en una edición pequeña), omitir el bloque entero — no inflarlo con "no se detectaron errores".
