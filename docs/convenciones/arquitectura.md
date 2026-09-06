# Arquitectura de EduFEM

> Capitulo del canon de EduFEM. Indice: [../../CLAUDE.md](../../CLAUDE.md) - mapa del repo: [../MAPA.md](../MAPA.md) - prohibiciones: [no-reintroducir.md](no-reintroducir.md).

**Leelo antes de tocar** `models/`, `fem/`, `file_io/`, `gui/main_window.py`, `gui/dialogs/` o los importadores.

---

## Arquitectura

MVC-ish. La pieza central es `ProjectModel` — todo componente toma una referencia y la muta.

### Data layer — [models/](../../models/)

`ProjectModel` ([models/project.py](../../models/project.py)) contiene dicts de `Node`, `Element`, `Material`, `NodalLoad`/`SurfaceLoad`, `BoundaryCondition`, más estado de solución (`displacements`, `stresses`, `global_K`, `global_F`, `is_solved`). Mutaciones deben setear `is_modified = True` y `is_solved = False` — los setters existentes ya lo hacen.

**DOF indexing — separación identidad/índice**: los `node_id` son identidad pública (visibles en GUI/CSV/PDF/DXF, pueden tener gaps tras borrados, ej. `{1, 5, 50}`). El índice de fila/columna en `K`, `F`, `u` es ordinal `0..N-1` y se obtiene vía `project.node_index_map` (**cacheado en `_node_index_map_cache`**: se recomputa desde `sorted(nodes.keys())` solo cuando se invalida — `add_node`, `remove_node`, `remove_node_with_cascade`, `change_node_id`, las mutaciones masivas de malla (`expand_q4_to_q9`/`shrink_q9_to_q4`/`subdivide`) y `restore_from_dict` setean el cache a `None`; O(N log N) al invalidar, O(1) en accesos posteriores dentro de la misma operación, p. ej. el ensamblaje que recorre todos los elementos). **Auditoría 2026-06**: la versión previa recomputaba on-demand pero un cache stale tras borrar nodos provocaba `IndexError` en el solve — invalidar en cada mutación lo corrige. Para loops, capturar el dict en variable local antes de iterar; para single-shot usar `project.dof_x(nid)` / `project.dof_y(nid)`. `Element.get_dof_indices(project)` recibe el project y resuelve los índices del elemento. **Nunca usar `2*(nid-1)` directo** — fallaba con `IndexError` cuando el usuario borraba nodos (los IDs quedaban no contiguos pero el código indexaba como si lo fueran). `K` se dimensiona como `2*num_nodes`, **no** `2*max(node_id)`. Patrón estándar de software FEM profesional (ABAQUS, ANSYS, FEniCS). Tests de regresión: [tests/test_noncontiguous_ids.py](../../tests/test_noncontiguous_ids.py).

Config global del análisis vive en el project: `analysis_type`, `element_type`, `unit_system`, `gravity_x` / `gravity_y` (vector con default `(0, -9.81)`), `include_gravity`. Todo serializado en `to_dict`/`from_dict` — campos nuevos van en ambos. Backward-compat en `ProjectModel.from_dict`: (1) `gravity: 9.81` (escalar legacy) → `(gravity_x=0, gravity_y=-gravity)`; (2) `unit_system: "Personalizado"` (modo eliminado en 2026-05) → `DEFAULT_UNIT_SYSTEM`, descartando `custom_units` (era solo rótulos sin factores reales). **No reintroducir** el modo Personalizado — los 8 sistemas predefinidos cubren SI/Imperial/Técnico (kgf/tonf), y la opción rompía la consistencia de conversión y health checks.

#### Undo / Redo ([models/undo_stack.py](../../models/undo_stack.py))

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

#### Helpers de malla — [models/mesh_utils.py](../../models/mesh_utils.py)

- `expand_q4_to_q9(project)`: genera mid-nodes (deduplicados entre vecinos por coord) + centroide. Idempotente. Setea `element_type = ELEMENT_Q9`. Vía canónica para pasar a Q9 — **nunca** duplicar nodos manualmente.
- `shrink_q9_to_q4(project)`: inverso. Trunca a 4 vértices y elimina mid/center huérfanos (preserva los que tengan cargas/BCs/surface refs). Wired en `ElementTypeDialog._on_accept` con confirmación modal.
- `subdivide_q4_mesh(project, levels)`: refinamiento 2×2 (cada Q4 → 4 sub-Q4). Hereda material/espesor, interpola surface loads, hereda cargas/BCs en corners originales. Si encuentra Q9, los trunca antes. **Sin consumidor activo tras eliminar el ex-M9 (2026-05)** — era su única llamada; se conserva como utilidad de refinamiento h.
- `find_edge_midnode(elem, node_start, node_end) → int | None`: dado un Q9 y una arista (en cualquier orientación), retorna el mid-node correspondiente. Usado por `assembly.py` para surface loads Q9.
- `auto_expand_if_q9(project)`: safety net idempotente. En proyectos Q9, expande cualquier Q4 con 4 vértices distintos. Invocado desde `pre_tab` (placeholder + edit + paste + tab change), `dxf_import_dialog` (post-import) y `main_window._on_import_model`. **Cualquier flujo nuevo que cree elementos vía `add_element` debe llamarlo al final.**
- `generate_structured_quad_mesh(corners, nx, ny, *, element_type, material_name, thickness, analysis_type) → ProjectModel`: malla estructurada de `nx*ny` elementos sobre el cuadrilátero (4 corners CCW) mediante mapeo bilineal desde el cuadrado lógico. Admite cuadriláteros generales (trapecio de Cook, rectángulo de Timoshenko, cuadrado de MMS). Si `element_type=ELEMENT_Q9`, llama `expand_q4_to_q9` al final. Usado por los scripts V&V; **no** invocado desde la GUI (los usuarios construyen mallas via canvas/DXF/CSV).
- `boundary_node_ids(project, edge, *, tol=None) → list[int]`: nodos del bounding box ordenados por la arista `"left" | "right" | "top" | "bottom"`. Tolerancia default `1e-9 * extent`. Helper hermano del generador estructurado.
- `recompute_q9_midnodes(project, elem)`: tras cambiar un vértice macro, recalcula coords de mid/center. Preserva IDs y datos.
- `classify_orphan_status(project) → dict[node_id → "active" | "orphan"]`: nodo huérfano = no aparece en ningún `element.node_ids`. Ortogonal a `classify_nodes` (corner/mid/center).

### Validador de salud — [models/model_health.py](../../models/model_health.py)

Función pura `validate_project(project) → HealthReport`. Sin dependencias UI. 3 severidades:

- **Errores críticos** (bloquean solve): `no_elements`, `no_restraints`, `insufficient_restraints` (<3 DOFs), `bc_orphan_node` (DOF colgante restringido), `elem_node_missing`, `elem_material_missing`, `surface_node_missing`, `degenerate_element`.
- **Warnings**: `load_orphan_node`, `unused_material`, `negative_jacobian` (CW), `zero_nodal_load`, `zero_surface_load`.
- **Info**: contadores generales.

Cada `HealthIssue` lleva `severity, code, message, target_kind, target_id, fixable, extra`. `apply_autofix(project, issue)` aplica la corrección para `fixable=True`.

UX:
- **`HealthReportDialog` (no-modal)** ([gui/dialogs/health_report_dialog.py](../../gui/dialogs/health_report_dialog.py)): se abre en post_tab si hay errores críticos. **Sin `grab_set`** — el usuario puede editar la GUI mientras el diálogo está abierto. `transient(parent)` mantiene subordinación visual. Cada issue tiene "🔧 Corregir" + "📍 Ir al item" (navega y reposiciona el diálogo a la esquina superior derecha) + hint educativo "🎓 ¿Por qué?". Footer con "🔄 Re-validar" (re-corre `validate_project` y reconstruye header + cards), "Volver al Pre-Proceso" (navega a tab 0) y "Resolver/Resolver de todos modos" cuando `allow_continue=True`. Devuelve `result ∈ {"continue", "cancel"}` y `fixes_applied`.
- **Banner en post_tab**: solo warnings, no bloquea. "Ver detalle" abre el dialog en modo solo-consulta.
- **Badge en status bar** ([main_window.py](../../gui/main_window.py) `_update_health_badge`): `✓ Modelo sano` / `⚠ N warning(s)` / `✗ N error(es)`. Click abre el dialog. Refresco en cada `_update_status_info`. Lazy-import del validador.

Hook en `post_tab.auto_solve`: corre `validate_project` antes del solve. Errores → modal; warnings → banner; sano → procede. Tras auto-fixes, re-valida.

**No duplicar la validación** — agregá `_check_xxx(project, report)` en `model_health.py` y un hint en `EDUCATIONAL_HINTS`.

### FEM engine — [fem/](../../fem/)

Pure NumPy/SciPy, sin GUI. Pipeline: `shape_functions` → `jacobian` → `b_matrix` → `constitutive` → `stiffness` → `assembly` → `solver` → `stress` / `mesh_quality`. Element type via strings de `config.settings` (`ELEMENT_Q4`/`ELEMENT_Q9`); `GAUSS_POINTS` mapea a 2×2 / 3×3. `gauss_quadrature.GAUSS_POINTS_1D` soporta también n=4 (Gauss-Legendre 4-pt) para integrar normas de error en Q9 con orden p+1 (evita aliasing del error con la cuadratura).

**Body forces distribuidas** ([fem/assembly.py](../../fem/assembly.py)): `assemble_global_system(project, *, body_force_fn=None)` acepta una callable `f(x, y) -> (bx, by)` que se integra como `∫ N_i · b dΩ` en cada elemento con Gauss. Si `body_force_fn=None`, compone una desde gravedad (`project.include_gravity + material.density`) — esto **conecta por primera vez** la gravedad al ensamblaje (antes el campo `include_gravity` existía pero era no-op). Usado por MMS para inyectar `f = -∇·σ(u_M)`. Si el caller pasa `body_force_fn` explícito Y `include_gravity=True`, el explícito gana con un warning.

**Dirichlet no homogéneo** (`u ≠ 0` en el borde): `BoundaryCondition` extendida con `ux_value` / `uy_value` ([models/boundary.py](../../models/boundary.py)). `solve_system` automáticamente compone `u_prescribed = project.get_prescribed_displacement_vector()` y `apply_boundary_conditions(K, F, restrained_dofs, u_prescribed)` aplica la sustitución estática `F_red -= K[free, restrained] @ u_prescribed[restrained]`. Backward-compat: `BoundaryCondition.from_dict` rellena `ux_value` / `uy_value=0.0` si faltan en archivos `.edufem` legacy; `set_boundary_condition(nid, rx, ry)` con 3 argumentos sigue funcionando (defaults `ux_value=uy_value=0.0`). Si todos los BCs tienen valores nulos, la rama clásica del solver no se altera — test de regresión `test_dirichlet_zero_backward_compat` garantiza output bit-a-bit idéntico al pre-2026-05.

**Normas de error L2 y H1** ([fem/error_norms.py](../../fem/error_norms.py)): `compute_error_norms(project, solution, u_exact_fn, grad_u_exact_fn=None, *, n_gauss=None) → dict` con `L2_u, L2_v, L2_disp, L2_disp_rel, H1_semi, H1_semi_rel, h, ndof, n_gauss`. Default `n_gauss = p+1` (3 para Q4, 4 para Q9) — **no** usar el mismo orden que K porque subestima el error a `O(h^{p+2})` artificial.

**Localización inversa global** ([fem/probe_query.py](../../fem/probe_query.py)): `locate_point(project, x, y) → (elem_id, xi, eta) | None` itera todos los elementos llamando `inverse_iso_map_NR` y retorna el primer hit con `(xi, eta) ∈ [-1, 1]²`. Usado por los benchmarks V&V que necesitan probar puntos no-nodales (Cook en `(48, 52)`, Timoshenko en A/B/C).

**Cargas superficiales** ([fem/equivalent_forces.py](../../fem/equivalent_forces.py)):
- **Q4**: `surface_load_to_nodal_forces(p_start, p_end, q_start, q_end, angle)` — distribución lineal exacta en 2 nodos, `F1 = L/6·(2·q_s + q_e)`, `F2 = L/6·(q_s + 2·q_e)`.
- **Q9**: `surface_load_to_nodal_forces_q9(p_start, p_mid, p_end, ...)` — funciones 1D cuadráticas, Gauss 2-pts. Con q constante: `L/6, 4L/6, L/6`.

**Dirección de carga = normal EXTERIOR** del elemento (rotación −90° del tangente: `nx0, ny0 = ty, -tx`), asumiendo CCW. `angle=0` ⇒ presión hacia adentro. **No reintroducir** `nx0, ny0 = -ty, tx` (rotación +90°, daba normal interior y aplicaba al revés).

`assembly.assemble_global_system` itera `surface_loads`; en Q9 resuelve mid-node vía `find_edge_midnode`. **Usar `fem/equivalent_forces.py` siempre** — no duplicar desde el módulo educativo M6.

**Extrapolación de esfuerzos** ([fem/stress.py](../../fem/stress.py)): Q4 con matriz clásica 4×4 basada en `(±√3, ±√3)`. Q9 con `M⁻¹` (cache de módulo) construida evaluando las 9 shape functions en los 9 puntos Gauss 3×3.

**Métricas de calidad** ([fem/mesh_quality.py](../../fem/mesh_quality.py)): `jacobian_ratio` evalúa en Gauss 2×2/3×3 según element_type. `internal_angles` y `robinson_stretch` operan en las 4 esquinas macro.

### GUI — [gui/](../../gui/)

[main_window.py](../../gui/main_window.py): `PanedWindow` horizontal. Izquierda: 3 pestañas (`PreProcessTab`, `ProcessTab`, `PostProcessTab`). Derecha: **un único `MeshCanvas` compartido** — Post overlays resultados sobre el mismo canvas, no swap. `_update_all_project_refs()` rebindea project en todas las tabs/canvas tras cambios.

Switching a Post-Proceso auto-resuelve (`post_tab.auto_solve()` en `_on_tab_changed`). `_refresh_all_tabs()` + `mesh_canvas.redraw()` es el broadcast estándar de "datos cambiaron". Post-tab llama `_refresh_menu_state()` tras solve para habilitar Exportar. **Volver de Post a Pre/Proc** llama `mesh_canvas.clear_results_overlay()` desde `_on_tab_changed` para resetear `show_deformed`, `displacements`, `result_values`, `show_isolines` — el canvas vuelve a mostrar solo geometría (no requiere status).

**Trampa de orden**: las 3 pestañas se construyen **antes** que `MeshCanvas`. Cualquier wiring `*_tab → mesh_canvas` desde `__init__` falla. Solución: método público `_wire_canvas_callbacks()` invocado tardíamente desde `MainWindow._build_main_layout` tras crear el canvas.

#### Barra de menús (filosofía minimalista)

**La barra tiene exactamente 3 menús**: Archivo, Modelo y Ayuda. Toda acción nueva entra en uno de esos tres; no hay toolbar ni menús *Editar* / *Ver* / *Análisis* / *Educación*. Módulos educativos por fase: M0 en pre, M1..M7 en proc; **el Post no tiene módulos educativos** (ex-M9 eliminado en 2026-05). `Ctrl+1..7` abren los módulos M1..M7 en orden canónico FEM (mapeo → Jacobiano → **B → D** → K+Gauss → fuerzas → ensamblaje). **El orden M3=B / M4=D fue intercambiado en 2026-05** (antes M3=D, M4=B): B = J⁻¹·∂N se deriva directamente de N (M1) y J (M2), así la cadena cinemática N→J→B queda sin cortes y ε=B·u (deformación) precede a σ=D·ε (constitución), igual que en Bathe/Cook/Zienkiewicz y en la Memoria de Cálculo. **M4 (matriz D) vive en proc** (no en el menú Modelo) porque la matriz D depende del material asignado a CADA elemento — la exploración por-elemento es natural en la fase de Proceso, junto a B/K/F. El submenú *Modelo > Tipo de Análisis* solo carga videos didácticos de TP/DP, sin la matriz D. **El ex-M7 (discontinuidad) y ex-M8 (estado tensional puntual) fueron consolidados** en el flujo nativo del Post (botón `🧊 Vista 3D` y panel Detalles del probe con Mohr inset) — ver sección "Vistas avanzadas del Post" más abajo. **Las cruces principales σ₁/σ₂ (toggle) fueron eliminadas en 2026-05** (ruido visual; el contorno + el Mohr del probe ya cubren el estado principal).

| Menú | Contenido |
|---|---|
| 📁 **Archivo** | Nuevo / Abrir / Recientes ▸ / Guardar / Guardar Como / **Importar ▸** (Geometría DXF, Modelo Excel/CSV) / **Exportar ▸** (Modelo Excel/CSV, Memoria de Cálculo PDF) / Salir |
| 📐 **Modelo** | Tipo de Elemento / Unidades / Materiales / Gravedad / Tipo de Análisis — 5 pop-ups autónomos en orden FEM |
| ❓ **Ayuda** | Manual / Atajos / **Cargar Ejemplo ▸** (3 casos × Q4/Q9) / Acerca de |

**Decisiones de etiquetado**:
- *Cargar Ejemplo* vive en **Ayuda** — los ejemplos son material didáctico, no archivos del usuario. Mantener el atajo `Ctrl+E` (compat histórica; carga el caso canónico Q4).
- El submenú *Cargar Ejemplo* tiene **tres cascadas de segundo nivel** ([models/example_library.py](../../models/example_library.py)), cada una con variantes Q4 y Q9: (1) **Cuadrado de validación** — `load_example_project[_q9]`, 9 nodos / 4 elementos macro, el caso histórico del proyecto; (2) **Viga de Timoshenko** — `load_example_timoshenko_q4/q9`, simple apoyada L=14m / H=1,20m / E=217370 kgf/cm² en sistema técnico kgf/cm, validada contra solución analítica de Timoshenko-Goodier y modelo Shell de SAP2000 en [docs/vyv/](../../docs/vyv/) (error < 0,3% para Q9 14×4); (3) **Membrana de Cook** — `load_example_cook_q4/q9`, benchmark trapezoidal adimensional de Cook (1974), N=8×8, ilustra empíricamente shear-locking en Q4 (u_y → 22 en lugar de 23,95) vs convergencia rápida en Q9. **Todos los loaders usan `generate_structured_quad_mesh` + `set_boundary_condition` + `add_surface_load` con la API canónica** — sirven como ejemplos de referencia para scripts headless que construyen modelos sin pasar por la GUI.
- *Importar/Exportar Modelo* lleva el sufijo `(Excel/CSV)` para distinguirlo de *Abrir/Guardar Proyecto* (`.edufem` JSON nativo, no editable a mano). El ZIP de CSVs es la vía editable en Excel para edición masiva.
- *Memoria de Cálculo (PDF)* — no "Reporte". Es un documento didáctico paso a paso (fórmulas, K, B, D, vectores, diagramas) alineado al espíritu de los módulos M1..M7. Se genera como **documento LaTeX vía `pylatex` + `pdflatex`** (requiere MiKTeX/TeX Live instalado; `PyMuPDF`/`fitz` renderiza el PDF para verlo en la app). **A diferencia de las fórmulas in-app de los módulos/Theory Hub (backend dual con fallback a mathtext), la Memoria PDF NO tiene fallback** — `pdflatex` es obligatorio. Si falta, `memoria_calculo.compile` eleva `PdflatexNotFoundError` (subclase de `MemoriaCalculoError`) y `main_window._on_export_pdf` abre [gui/dialogs/pdflatex_missing_dialog.py](../../gui/dialogs/pdflatex_missing_dialog.py) (`show_pdflatex_missing_dialog`) — un diálogo con **botón de descarga** a la página oficial (MiKTeX/MacTeX/TeX Live según la plataforma vía `platform.system()`), en vez de un `showerror` seco. **No reintroducir** el `messagebox.showerror` para el caso de pdflatex faltante. **`reportlab` fue eliminado** (2026-05-31): era dependencia declarada pero sin un solo import en el código — la generación es 100% pylatex. **No reintroducir `reportlab`**; si alguna vez se quiere un PDF sin pdflatex, sería migrar a un único motor (reportlab/fpdf2) + math vía matplotlib mathtext, pero es una migración grande y **NO está aprobada**.
- *Exportar Resultados CSV* fue **eliminado del menú** — los resultados se copian directamente desde la tabla del Post-Proceso con `Ctrl+C` (TSV al portapapeles, pegable en Excel). `selectmode="extended"` + `Ctrl+A` permiten seleccionar todo o subconjuntos. **No reintroducir** la entrada de menú.

**Orden FEM del menú Modelo**: Elemento → Unidades → Material → **Gravedad** → Análisis. Sigue el flujo lógico de definición de un problema FEM: primero la geometría discreta (Q4/Q9), después cómo se mide (sistema de unidades), después de qué está hecho (E, ν, ρ por material), después qué cargas volumétricas actúan (gravedad, depende de ρ para `F = ρ·g·V`), y al final el tipo de problema (TP / DP), donde la matriz constitutiva D = D(E, ν, caso) combina material y análisis. **La gravedad va después de Materiales** porque conceptualmente es una CARGA (no una unidad) y depende de la densidad — moverla antes rompe la jerarquía pedagógica. **No reordenar** salvo que se replantee el flujo.

**`GravityDialog`** ([gui/dialogs/gravity_dialog.py](../../gui/dialogs/gravity_dialog.py)): layout minimalista (440×260 px) — header + 2 entries `gx`/`gy` + toggle `include_gravity` + footer Cancelar/Aceptar. **Sin Labelframes**, **sin subtítulo descriptivo** (la fórmula `F = ρ·g·V` es info del solver, no del input), **sin labels "(unidad coherente con el sistema activo)"** junto a cada Entry (redundante con el sistema activo del proyecto), **sin botón preset "(0, -9.81)"** (el usuario lo tipea sin esfuerzo) y **sin hint** debajo del toggle. Mientras está abierto, registra una capa overlay sobre `MeshCanvas` via `add_overlay_layer` que dibuja una flecha desde el centro del bbox del modelo (o del canvas si está vacío) en dirección `(gx, -gy)` (flip Y por inversión screen). Color `PHASE_PROC_COLOR` cuando `include_gravity=True`, `TEXT_MUTED_FG` cuando está off. La capa lee `self._gx_live`/`self._gy_live` y se refresca en cada `canvas.redraw()` disparado por el trace de los Entry. La capa se desregistra en Aceptar/Cancelar. **No reintroducir** Labelframes "Componentes"/"Aplicacion", botón preset, labels de unidad junto a los Entry, ni hints debajo del toggle — la flecha en vivo sobre el canvas hace todo el trabajo pedagógico.

**`UnitsDialog` con conversión automática** ([gui/dialogs/units_dialog.py](../../gui/dialogs/units_dialog.py)): layout minimalista (440×180 px) — solo un combobox con los 8 sistemas + footer. Sin Labelframe, sin subtítulo, sin banner explicativo, **sin chip-line de unidades derivadas** (redundante con el nombre del sistema en el combobox: `SI (N, mm, MPa)` ya enumera las tres unidades), **sin modal de confirmación** (la conversión de valores se aplica automáticamente al aceptar — el usuario nota el cambio en los headers de tablas y en los valores numéricos; pedagógicamente, ver `1.0 m → 1000.0 mm` refuerza la relación entre unidades). Los factores vienen de `config.units.get_conversion_factors(from_sys, to_sys)` y se aplican a: coords de nodos, espesor (default y override), E de los materiales, fuerzas nodales, cargas distribuidas (factor compuesto force/length), y vector gravedad (factor acceleration = length). **Densidad y ν no se convierten** — la masa no está en nuestra 3-tupla (L, F, σ). Solo `gx`/`gy` (aceleración) escalan con length porque comparten dimensión L/T². Tras `convert_units` la solución (`is_solved`, K, F, u, stresses) se invalida porque K depende de E. Status bar reporta `Unidades: X (valores convertidos)`. **Compensación de cámara del `MeshCanvas`**: tras la conversión, `units_dialog._on_accept` divide `mesh_canvas.scale` por `factors["length"]`. Razón: `world_to_screen` calcula `sx = x · scale + offset_x`; si las coords mundo se multiplicaron por `f`, dividir `scale` por `f` mantiene la posición en pantalla de cada nodo invariante (el origen world (0,0) mapea siempre a `(offset_x, offset_y)` independientemente de `scale`, así que los offsets no cambian). El modelo NO salta ni cambia de tamaño visualmente — solo cambian los números que el usuario lee en tablas/headers. **No reintroducir** un `fit_view()` automático tras conversión (rompía el pan/zoom del usuario, era visualmente disruptivo). **No reintroducir** el modo Personalizado, el chip-line de unidades derivadas, ni el modal `askyesnocancel` — todos eliminados como ruido visual.

**Chequeos de consistencia de unidades** ([models/model_health.py](../../models/model_health.py)): tres warnings heurísticos en `validate_project` que detectan mismatch numérico ↔ unidad. (1) `SUSPICIOUS_YOUNG_MODULUS`: convierte E del material a Pa y avisa si está fuera de `[1e8, 5e11]` Pa (rango de materiales estructurales típicos, desde maderas hasta cerámicas). (2) `SUSPICIOUS_MODEL_SCALE`: convierte la extensión del modelo a metros y avisa si está fuera de `[0.1 mm, 10 km]`. (3) `GRAVITY_NO_DENSITY`: si `include_gravity=True` pero la densidad del material asignado es ≤ 0. Los tres se skip-ean si `unit_system` no está en `UNIT_SYSTEMS` (caso defensivo, archivo corrupto). Test de regresión: [tests/test_unit_conversion.py](../../tests/test_unit_conversion.py).

Diálogos en [gui/dialogs/](../../gui/dialogs/): `(parent, project, main_window=None)`. Invocables desde menú o desde tabs sin acoplarse. **Centrado del Toplevel** vía `center_dialog(win, parent, *, clamp_screen=False)` ([gui/dialogs/_dialog_helpers.py](../../gui/dialogs/_dialog_helpers.py), auditoría 2026-06): centraliza las ~7 copias verbatim de `_center()` que vivían en cada diálogo. `clamp_screen=True` además clampa contra el tamaño de pantalla (margen inferior ~50 px) — para los diálogos altos con video (`ElementType`/`Analysis`/`Gravity`). **No reintroducir** un `_center()` local en un diálogo nuevo — usar este helper.

**`MaterialDialog`** ([gui/dialogs/material_dialog.py](../../gui/dialogs/material_dialog.py)): master-detail compacto (680×460 px). Panel izquierdo: lista de materiales (**solo nombres**, sin swatch ni meta) + botones **Nuevo / Eliminar**. Scroll de la lista **exclusivamente con la rueda del mouse** (`<MouseWheel>` enlazado a canvas, frame interno y cada row) — **sin scrollbar visible**, alineado con el patrón del spreadsheet del pre/post-proc. Panel derecho: form con 4 entries (Nombre, E, ν, ρ) + botón Guardar. **Sin footer de 'Cerrar'** — la X nativa del Toplevel cierra y no hay commit global que justifique un 'Aceptar' (cada material se guarda con su propio Guardar del panel derecho); agregar un botón de footer aquí sería ruido sin acción nueva. **Sin selector de color** — el atributo `Material.color` fue eliminado en 2026-05 (no era consumido por solver ni canvas, solo aparecía en este diálogo). Sin Labelframe "Vista previa", sin status label, sin hints, sin contador, sin Duplicar. Validación live deshabilita Guardar si: E≤0, ν fuera de `(-1, 0.5)`, ρ<0, o nombre vacío. Cambio de nombre cascadea a `element.material_name`. Captura undo antes de cada mutación. **Librería default** (`Material.get_default_library()`): solo **Acero Estructural** y **Concreto f'c=21 MPa**. **Backward-compat**: `Material.from_dict` ignora silenciosamente el campo `color` de archivos `.edufem` legacy; `model_io._import_materials` ignora la 5ta columna (color) si aparece en CSV legacy y rellena con `""` si la fila viene con <4 columnas. **No reintroducir** `Material.color`, swatch/paleta/picker de color, scrollbar visible en la lista, botón Duplicar, footer con botón Cerrar/Aceptar, `TYPICAL_MATERIALS`, ni el colorchooser nativo. Si en el futuro se requiere `color`, agregarlo como campo opcional en `Material.__init__` con default `None` y reintroducir el selector (preferentemente la paleta 3×8 curada que estaba antes de este pase).

**`ElementTypeDialog`** ([gui/dialogs/element_type_dialog.py](../../gui/dialogs/element_type_dialog.py)) soporta Q4↔Q9 en ambos sentidos: Q9 sobre Q4 → `expand_q4_to_q9`; Q4 sobre Q9 → `shrink_q9_to_q4` con confirmación modal. **Layout idéntico a `AnalysisTypeDialog`** (760×660 px, video arriba 720×480 + toolbutton radios grid 50/50 + hint + footer): el cantilever Q4 vs Q9 (`resources/videos/cantilever_q4_q9.webp`, 900×600 escalado a 720×480, autoplay seamless via `WebpPlayer`) ocupa la mitad superior y los dos toolbuttons abajo se alinean con sus columnas — Q4 chip bajo la columna izquierda, Q9 chip bajo la derecha. **Tres toques creativos aprovechando que el video tiene identidad cromática por columna** (Q4=gris, Q9=naranja): (1) cada chip color-matches su columna → Q4 chip `secondary-toolbutton` gris, Q9 chip `warning-toolbutton` naranja (a diferencia de `AnalysisTypeDialog` que usa `info-toolbutton` para ambos, porque TP/DP no tiene identidad cromática equivalente); (2) cada chip incluye un mini-icono PIL del layout de nodos del elemento (4 puntos 2×2 para Q4, 9 puntos 3×3 para Q9) generado on-the-fly con `PIL.ImageDraw` — previsualización visual del concepto que el chip representa, refs anti-GC en `self._icon_q4` y `self._icon_q9`; (3) el texto de cada chip incluye el conteo de GDL (`Q4 · 8 GDL`, `Q9 · 18 GDL`) como información de decisión costo/precisión. El **hint operacional de Q9** (*"En Q9, los 5 nodos internos (medios + centroide) se generan automáticamente"*) se conserva como única línea italic muted entre los toolbuttons y el footer — info no obvia que previene confusión cuando el alumno ve nodos aparecer al cambiar de tipo. `AnalysisTypeDialog` NO tiene equivalente porque TP/DP no tiene una sutileza operacional análoga. La bidireccionalidad NO se explicita textualmente: la UI binaria + el modal de confirmación Q9→Q4 ya la comunican. **No reintroducir**: header con pregunta `¿Qué precisión necesitás?` (el título del Toplevel ya implica la pregunta, ningún diálogo del menú Modelo tiene pregunta-header), subtítulo descriptivo, radios verticales `info`, banner *"↔ Configuración bidireccional"*, tiles (`_ElementTile`), mini-gráfico (`_MiniElementGraphic`) — todos eliminados o consolidados en iteraciones previas. Si el `.webp` no existe, degrada a placeholder textual.

**`AnalysisTypeDialog`** ([gui/dialogs/analysis_type_dialog.py](../../gui/dialogs/analysis_type_dialog.py)) es **minimalista**: `Radiobutton` TP/DP + **un único video**, `resources/videos/tension_deformacion_plana.webp` (constante `VIDEO_PATH`), que muestra TP y DP lado a lado en un `WebpPlayer` (autoplay, loop seamless, sin barra de controles). Cambiar TP↔DP **no recarga nada**: la animación ya cubre los dos casos. Si el `.webp` falta, el frame degrada a un mensaje informativo con la ruta esperada. **NO contiene la matriz D** — esa se explora por-elemento desde el módulo **M4** (Proceso > Educación) porque depende del material. Hereda de `ttk.Toplevel`: es UI del menú, no un módulo educativo.

**Anti-pattern (no hacer)**: usar `FuncAnimation` sin guardar referencia persistente — el GC mata la animación y/o freeza el `Toplevel` modal. Patrón correcto: `self._anim = FuncAnimation(...)` + `self._anim.event_source.stop()` en cierre. Las animaciones del `ElementTypeDialog` migraron a WebP animado prerenderizado y el `AnalysisTypeDialog` usa solo WebP — el patrón sigue documentado por si se reintroduce en algún módulo educativo nuevo.

**Reproductor de WebP animado** ([gui/widgets/webp_player.py](../../gui/widgets/webp_player.py)): widget `WebpPlayer(parent, scaled=True, background=...)` lightweight basado **solo en Pillow** (sin `PyAV`/FFmpeg → ahorra ~30 MB en el instalador PyInstaller). API: `load(path) → play() → stop()`. Loop seamless interno (no requiere bind `<<Ended>>`). Decoder on-the-fly por frame, sin cache (RAM constante). Expone `seek_frame`, `seek_ms`, `n_frames`, `current_time_ms`, `total_duration_ms` y callback opcional `on_frame_change(idx, cur_ms, total_ms)` por si se quisiera un wrapper con scrubber (el ex `education/components/video_player.py` fue **eliminado en la auditoría 2026-06** — quedó sin instanciar; `WebpPlayer` es el único reproductor vivo). **Trampa**: el muxer libwebp de ffmpeg escribe `duration=0` por frame — `WebpPlayer.load` trata 0 como ausente y aplica 45 ms (~22 fps) por defecto, así que la duración total es coherente.

**Pipelines de generación de videos**: dos rutas, ambas terminan en un `.webp` animado en `resources/videos/`.

(1) **Manim → WebP** (preferido, activo): `tools/render_tp_dp_manim/` para `tension_deformacion_plana.webp` y `tools/render_q4q9_manim/` para `cantilever_q4_q9.webp`. Cada uno es una clase `Scene` en Python (`tpvsdp.py`, `q4_vs_q9.py`) que define geometría y timeline; render con `manim -qh script.py SceneName`, conversión a WebP con `ffmpeg -vcodec libwebp -filter:v "fps=22,scale=900:600:flags=lanczos" -q:v 75 -loop 0 -an -vsync 0`. Output determinístico, 1 sola dependencia (manim), coherencia visual entre videos (paleta sincronizada con `config/settings.py`, mismo layout 2 columnas con separadores, misma estrategia de loop seamless basada en `set_opacity(0)` del `dynamic_group` al inicio + fade-out simétrico al final).

(2) **Claude Design + Chrome → WebP** (legacy, conservado como referencia): `tools/render_q4q9/record.mjs` (eliminado del repo) usa Chrome headless + DevTools Protocol (WebSocket nativo de Node 24+, sin instalar paquetes) + ffmpeg. Pasos: descargar bundle tar.gz desde Claude Design, levantar `python -m http.server`, capturar JPGs vía `Page.startScreencast`, recortar a `frames_per_loop = duration_loop * fps_real` para loop seamless, componer con `ffmpeg -framerate <real> -frames:v <N> -c:v libx264 out.mp4`, luego convertir a WebP igual que arriba. Reusable para futuras animaciones generadas en Claude Design. **El video cantilever_q4_q9.webp fue migrado de este pipeline al Manim en 2026-05** y la carpeta `tools/render_q4q9/` **se borró del repo**; el render activo vive en `tools/render_q4q9_manim/`. El procedimiento queda descrito acá sólo por si hubiera que recrearlo.

**No reintroducir** la dependencia `tkvideoplayer` ni `av`/`PyAV` — la migración a WebP es deliberada (instalador PyInstaller más liviano, sin DLLs FFmpeg que disparan falsos positivos de antivirus).

**`DxfImportDialog`** ([gui/dialogs/dxf_import_dialog.py](../../gui/dialogs/dxf_import_dialog.py)): file picker en `main_window._on_import_dxf` se abre **antes** del Toplevel (cancelar = no diálogo). Layout minimalista: 2 combos + preview en `tk.Canvas` nativo + botones.

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
| Ctrl+1..7 | Módulos educativos M1..M7 en orden canónico FEM (mapeo, Jacobiano, **B**, **D**, K+Gauss, fuerzas, ensamblaje). M3 = matriz B (`mod03_b_matrix.py`), M4 = matriz D (`mod04_constitutive.py`) |
| F5 | Resolver |
| F11 / F | Pantalla completa / Ajustar vista |
| D | Toggle modo dibujo de elementos (canvas-driven, ver `mesh_canvas.py`) |
| Ctrl+Click / Shift+Click | (canvas) selección múltiple (toggle / range) |
| Esc | Cascada: cancela elemento parcial → cierra cell editor → limpia selección |
| Ctrl+Tab / Shift+Tab | Pestaña sig / ant |
| Ctrl+/ / F1 | Atajos / Manual |

`_is_entry_focused()` corta atajos de una sola tecla cuando el foco está en `Entry`/`Combobox`. Atajos nuevos van en `_bind_shortcuts` Y `_on_shortcuts` — deben coincidir.

**Archivos recientes**: persistencia JSON en `~/.edufem/recent.json` ([config/recent_files.py](../../config/recent_files.py), `RECENT_FILES_MAX = 10`). `recent_files.add(path)` tras guardar/abrir + `_build_recent_menu()`.
### Otros archivos importantes

- [config/settings.py](../../config/settings.py): magic strings, colores, tolerancias, fonts, decimales. **Importar desde aquí, no hardcodear**.
- [config/units.py](../../config/units.py): 8 sistemas predefinidos (SI ×4 + Imperial ×2 + Técnico kgf/tonf ×2) + factores `_LENGTH_TO_M / _FORCE_TO_N / _STRESS_TO_PA` para conversión real.
- [gui/widgets/](../../gui/widgets/): `ToolTip`, `phase_banner.build_phase_banner`, `module_launcher_panel.render_module_buttons`.
- [file_io/](../../file_io/): CSV/ZIP del modelo ([model_io.py](../../file_io/model_io.py) con columnas dinámicas Q4/Q9), PDF de la memoria (`pylatex`+`pdflatex` genera, `PyMuPDF`/`fitz` visualiza; **sin reportlab**), JSON proyecto ([project_io.py](../../file_io/project_io.py), escritura atómica tmp+fsync+replace), DXF (ver sección dedicada).
- [models/example_library.py](../../models/example_library.py): biblioteca de modelos de ejemplo de PRODUCTO (alimenta Ayuda ▸ Cargar Ejemplo y los scripts V&V). Canónico (E=225000, ν=0.2, t=0.8, P=1000). `load_example_project(P)` Q4 9-nodos, `load_example_project_q9(P)` 25-nodos, + Timoshenko/Cook Q4/Q9. **Movido desde `tests/example_data.py` en la auditoría 2026-06** (producción no debe depender de `tests/`); [tests/example_data.py](../../tests/example_data.py) quedó como shim de re-export para no romper imports existentes.
## Importación DXF

Módulo [file_io/dxf_io.py](../../file_io/dxf_io.py) + diálogo [gui/dialogs/dxf_import_dialog.py](../../gui/dialogs/dxf_import_dialog.py).

**Dependencia `ezdxf>=1.0`** import diferido vía `_require_ezdxf()` — falla con mensaje detallado si falta. Caso Windows: `python -m pip install ezdxf` (bypasea launcher roto).

**Convención**: capa `FEM_ELEMENTS` con polilíneas cerradas de 4 vértices → Q4. Otras capas se ignoran. **No hay capa `FEM_NODES`**.

**Flujo**: file picker en `main_window._on_import_dxf` ANTES del Toplevel; cancelar = nada. `DxfImportDialog(parent, project, main_window, filepath=path)` carga capas + preview en `tk.Canvas` nativo.

**Diálogo**: 2 combos (Unidades del proyecto + Capa) + preview. Cambiar unidades dispara: (a) re-escala coords existentes (`old_m / new_m`), (b) setea `unit_system` al sistema canónico de esa longitud.

**Idempotencia**: dedupe topológico por `frozenset(elem.node_ids[:4])`. Re-importar el mismo DXF reporta `elements_skipped_duplicate = N` sin mutar. Replicar este patrón en otros importadores (STEP, IGES, JSON).

**Orden CCW forzado**: shoelace < 0 → invertir antes de crear el Q4.

`import_dxf(filepath, project, scale=1.0, layer_elements="FEM_ELEMENTS")` retorna `{"nodes_added", "elements_added", "elements_skipped_duplicate", "warnings", "q9_auto_expanded"}`.
