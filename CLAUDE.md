# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Project

**EduFEM** — GUI educativa de elementos finitos 2D (tensión plana / deformación plana) con elementos Q4 y Q9. Stack: `tkinter` + `ttkbootstrap` (tema `darkly`). **User-facing strings, docstrings y comentarios en español** — mantener la convención.

## Terminología técnica (UI/UX en español)

Todo string que termine siendo visible al alumno (labels de menú, chips de selección, mensajes de validación, banners de fase, captions de gráficos educativos, verdict labels en videos Manim, encabezados del PDF de memoria de cálculo, etc.) debe usar la traducción canónica española de los términos técnicos FEM. Esta tabla fija las traducciones obligatorias:

| Término inglés | Traducción canónica | Notas |
|---|---|---|
| DOF (Degree of Freedom) | **GDL** (Grado de Libertad) | Singular "GDL", plural "GDLs". Aplica al chip `Q4 · 8 GDL` / `Q9 · 18 GDL`, al eje X del log-log de M9, a los mensajes del validador de salud, al PDF de memoria de cálculo, etc. |
| FEM (Finite Element Method) | **MEF** (Método de Elementos Finitos) | Excepción: el brand **EduFEM** se mantiene como nombre del producto. La capa DXF `FEM_ELEMENTS` se mantiene como convención de formato del archivo. |
| Plane stress / strain | Tensión plana / Deformación plana | El menú Modelo → Tipo de Análisis ya usa estas formas; alinear el resto del código. |
| Boundary condition (BC) | Restricción | "Restricción" en singular, plural "restricciones". |
| Mesh | Malla | |
| Node | Nodo | |
| Element | Elemento | |
| Load | Carga | |
| Stress | Tensión | |
| Strain | Deformación | |
| Displacement | Desplazamiento | |
| Stiffness | Rigidez | |
| Shape function | Función de forma | |
| Solver | Solucionador | "Resolver" como verbo (botón F5 "Resolver") se mantiene. |
| Hourglass modes | Modos espurios (hourglass) | Mantener "hourglass" como aclaración entre paréntesis — es el término estándar de la literatura y el alumno se va a topar con él en otros textos. |

**Alcance — qué SÍ traducir**:
- Strings literales entre comillas que aparecen en `text=`, `label=`, `title=`, `subtitle=`, captions de plots, mensajes de status bar, verdict labels en `Text(...)` / `MathTex(...)` de Manim, `messagebox.askyesno` / `showerror`.
- Documentos LaTeX/PDF generados (`memoria_calculo.py`, `theory_hub_dialog.py`).
- Tooltips, hints, banners de fase.

**Alcance — qué NO traducir**:
- Nombres de variables, funciones, clases, atributos (`n_dof`, `total_restrained_dofs`, etc.).
- Magic strings internos que sirven de keys (`"stress"`, `"vm"` en dicts de resultados).
- Constantes del módulo (`ELEMENT_Q4 = "Q4 - Cuadrilátero 4 nodos"` — el value es user-facing español ✓, el name de la constante en inglés ✓).
- Nombres de archivos, paths, extensiones (`.edufem`, capa DXF `FEM_ELEMENTS`).
- Logs, debug prints, `print(...)` de scripts de test (developer-facing).
- Comentarios técnicos que usan abreviaturas en inglés por brevedad (`# Indice DOF global de Ux para node_id` está bien en docstring).

**Auditoría pre-merge**: tras tocar cualquier archivo `gui/`, `education/`, `models/model_health.py`, `file_io/memoria_calculo.py`, o `tools/render_*_manim/`:

```
Grep "DOF" --glob "**/*.py"
Grep "FEM" --glob "**/*.py"
```

Cualquier hit en STRING LITERAL que llegue al usuario (banner, label, mensaje, verdict, caption) debe convertirse a GDL / MEF. Hits en docstrings, comentarios, variable names, magic strings internos, brand name `EduFEM` y capa DXF `FEM_ELEMENTS` son OK y se ignoran.

**No reintroducir** texto en inglés en UI ni siglas inglesas para conceptos que ya tienen su traducción canónica. La regla anti-ruido es la misma que con el resto del proyecto: si la traducción al español ya existe y es comprensible para un estudiante hispanohablante de ingeniería, usarla.

## Running

```bash
python main.py                            # GUI
python -m tests.test_fem                  # validacion FEM (Q4, Q9, surface loads)
python -m tests.test_vv_extensions        # regresion V&V: body forces, Dirichlet no-cero, malla estructurada, normas L2/H1
python -m tests.vv_mms                    # MMS: convergencia Q4/Q9 -> tasas asintoticas teoricas
python -m tests.vv_timoshenko             # viga Timoshenko + cross-validation SAP2000
python -m tests.vv_cook                   # membrana de Cook (Q4 lento, Q9 rapido)
python -m tests.test_q9_q4_cycle          # ciclo Q4 -> Q9 -> Q4 sin drift
python -m tests.test_undo_stack           # undo/redo unit tests
python -m tests.test_serialization        # to_dict / restore_from_dict
python -m tests.test_unit_conversion      # conversion de unidades + health checks
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

`ProjectModel` ([models/project.py](models/project.py)) contiene dicts de `Node`, `Element`, `Material`, `NodalLoad`/`SurfaceLoad`, `BoundaryCondition`, más estado de solución (`displacements`, `stresses`, `global_K`, `global_F`, `is_solved`). Mutaciones deben setear `is_modified = True` y `is_solved = False` — los setters existentes ya lo hacen.

**DOF indexing — separación identidad/índice**: los `node_id` son identidad pública (visibles en GUI/CSV/PDF/DXF, pueden tener gaps tras borrados, ej. `{1, 5, 50}`). El índice de fila/columna en `K`, `F`, `u` es ordinal `0..N-1` y se obtiene vía `project.node_index_map` (recomputado on-demand desde `sorted(nodes.keys())`). Para loops, capturar el dict en variable local antes de iterar; para single-shot usar `project.dof_x(nid)` / `project.dof_y(nid)`. `Element.get_dof_indices(project)` recibe el project y resuelve los índices del elemento. **Nunca usar `2*(nid-1)` directo** — fallaba con `IndexError` cuando el usuario borraba nodos (los IDs quedaban no contiguos pero el código indexaba como si lo fueran). `K` se dimensiona como `2*num_nodes`, **no** `2*max(node_id)`. Patrón estándar de software FEM profesional (ABAQUS, ANSYS, FEniCS). Tests de regresión: [tests/test_noncontiguous_ids.py](tests/test_noncontiguous_ids.py).

Config global del análisis vive en el project: `analysis_type`, `element_type`, `unit_system`, `gravity_x` / `gravity_y` (vector con default `(0, -9.81)`), `include_gravity`. Todo serializado en `to_dict`/`from_dict` — campos nuevos van en ambos. Backward-compat en `ProjectModel.from_dict`: (1) `gravity: 9.81` (escalar legacy) → `(gravity_x=0, gravity_y=-gravity)`; (2) `unit_system: "Personalizado"` (modo eliminado en 2026-05) → `DEFAULT_UNIT_SYSTEM`, descartando `custom_units` (era solo rótulos sin factores reales). **No reintroducir** el modo Personalizado — los 8 sistemas predefinidos cubren SI/Imperial/Técnico (kgf/tonf), y la opción rompía la consistencia de conversión y health checks.

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
- `generate_structured_quad_mesh(corners, nx, ny, *, element_type, material_name, thickness, analysis_type) → ProjectModel`: malla estructurada de `nx*ny` elementos sobre el cuadrilátero (4 corners CCW) mediante mapeo bilineal desde el cuadrado lógico. Admite cuadriláteros generales (trapecio de Cook, rectángulo de Timoshenko, cuadrado de MMS). Si `element_type=ELEMENT_Q9`, llama `expand_q4_to_q9` al final. Usado por los scripts V&V; **no** invocado desde la GUI (los usuarios construyen mallas via canvas/DXF/CSV).
- `boundary_node_ids(project, edge, *, tol=None) → list[int]`: nodos del bounding box ordenados por la arista `"left" | "right" | "top" | "bottom"`. Tolerancia default `1e-9 * extent`. Helper hermano del generador estructurado.
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

Pure NumPy/SciPy, sin GUI. Pipeline: `shape_functions` → `jacobian` → `b_matrix` → `constitutive` → `stiffness` → `assembly` → `solver` → `stress` / `mesh_quality`. Element type via strings de `config.settings` (`ELEMENT_Q4`/`ELEMENT_Q9`); `GAUSS_POINTS` mapea a 2×2 / 3×3. `gauss_quadrature.GAUSS_POINTS_1D` soporta también n=4 (Gauss-Legendre 4-pt) para integrar normas de error en Q9 con orden p+1 (evita aliasing del error con la cuadratura).

**Body forces distribuidas** ([fem/assembly.py](fem/assembly.py)): `assemble_global_system(project, *, body_force_fn=None)` acepta una callable `f(x, y) -> (bx, by)` que se integra como `∫ N_i · b dΩ` en cada elemento con Gauss. Si `body_force_fn=None`, compone una desde gravedad (`project.include_gravity + material.density`) — esto **conecta por primera vez** la gravedad al ensamblaje (antes el campo `include_gravity` existía pero era no-op). Usado por MMS para inyectar `f = -∇·σ(u_M)`. Si el caller pasa `body_force_fn` explícito Y `include_gravity=True`, el explícito gana con un warning.

**Dirichlet no homogéneo** (`u ≠ 0` en el borde): `BoundaryCondition` extendida con `ux_value` / `uy_value` ([models/boundary.py](models/boundary.py)). `solve_system` automáticamente compone `u_prescribed = project.get_prescribed_displacement_vector()` y `apply_boundary_conditions(K, F, restrained_dofs, u_prescribed)` aplica la sustitución estática `F_red -= K[free, restrained] @ u_prescribed[restrained]`. Backward-compat: `BoundaryCondition.from_dict` rellena `ux_value` / `uy_value=0.0` si faltan en archivos `.edufem` legacy; `set_boundary_condition(nid, rx, ry)` con 3 argumentos sigue funcionando (defaults `ux_value=uy_value=0.0`). Si todos los BCs tienen valores nulos, la rama clásica del solver no se altera — test de regresión `test_dirichlet_zero_backward_compat` garantiza output bit-a-bit idéntico al pre-2026-05.

**Normas de error L2 y H1** ([fem/error_norms.py](fem/error_norms.py)): `compute_error_norms(project, solution, u_exact_fn, grad_u_exact_fn=None, *, n_gauss=None) → dict` con `L2_u, L2_v, L2_disp, L2_disp_rel, H1_semi, H1_semi_rel, h, ndof, n_gauss`. Default `n_gauss = p+1` (3 para Q4, 4 para Q9) — **no** usar el mismo orden que K porque subestima el error a `O(h^{p+2})` artificial.

**Localización inversa global** ([fem/probe_query.py](fem/probe_query.py)): `locate_point(project, x, y) → (elem_id, xi, eta) | None` itera todos los elementos llamando `inverse_iso_map_NR` y retorna el primer hit con `(xi, eta) ∈ [-1, 1]²`. Usado por los benchmarks V&V que necesitan probar puntos no-nodales (Cook en `(48, 52)`, Timoshenko en A/B/C).

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

**3 menús únicamente** — decisión de diseño. **No añadir** *Editar*, *Ver*, *Análisis*, *Educación* ni toolbar. Módulos educativos por fase: M0 en pre, M1..M7 en proc, M9 en post. `Ctrl+1..7` abren los módulos M1..M7 en orden canónico FEM (mapeo → Jacobiano → D → B → K+Gauss → fuerzas → ensamblaje). **M3 vive en proc** (no en el menú Modelo) porque la matriz D depende del material asignado a CADA elemento — la exploración por-elemento es natural en la fase de Proceso, junto a B/K/F. El submenú *Modelo > Tipo de Análisis* solo carga videos didácticos de TP/DP, sin la matriz D. **El ex-M7 (discontinuidad) y ex-M8 (cruces + Mohr) fueron consolidados** en el flujo nativo del Post (botón `🧊 Vista 3D`, toggle `Cruces principales σ₁/σ₂` y panel Detalles del probe con Mohr inset) — ver sección "Vistas avanzadas del Post" más abajo.

| Menú | Contenido |
|---|---|
| 📁 **Archivo** | Nuevo / Abrir / Recientes ▸ / Guardar / Guardar Como / **Importar ▸** (Geometría DXF, Modelo Excel/CSV) / **Exportar ▸** (Modelo Excel/CSV, Memoria de Cálculo PDF) / Salir |
| 📐 **Modelo** | Tipo de Elemento / Unidades / Materiales / Gravedad / Tipo de Análisis — 5 pop-ups autónomos en orden FEM |
| ❓ **Ayuda** | Manual / Atajos / **Cargar Ejemplo ▸** (3 casos × Q4/Q9) / Acerca de |

**Decisiones de etiquetado**:
- *Cargar Ejemplo* vive en **Ayuda** — los ejemplos son material didáctico, no archivos del usuario. Mantener el atajo `Ctrl+E` (compat histórica; carga el caso canónico Q4).
- El submenú *Cargar Ejemplo* tiene **tres cascadas de segundo nivel** ([tests/example_data.py](tests/example_data.py)), cada una con variantes Q4 y Q9: (1) **Cuadrado de validación** — `load_example_project[_q9]`, 9 nodos / 4 elementos macro, el caso histórico del proyecto; (2) **Viga de Timoshenko** — `load_example_timoshenko_q4/q9`, simple apoyada L=14m / H=1,20m / E=217370 kgf/cm² en sistema técnico kgf/cm, validada contra solución analítica de Timoshenko-Goodier y modelo Shell de SAP2000 en [docs/vyv/](docs/vyv/) (error < 0,3% para Q9 14×4); (3) **Membrana de Cook** — `load_example_cook_q4/q9`, benchmark trapezoidal adimensional de Cook (1974), N=8×8, ilustra empíricamente shear-locking en Q4 (u_y → 22 en lugar de 23,95) vs convergencia rápida en Q9. **Todos los loaders usan `generate_structured_quad_mesh` + `set_boundary_condition` + `add_surface_load` con la API canónica** — sirven como ejemplos de referencia para scripts headless que construyen modelos sin pasar por la GUI.
- *Importar/Exportar Modelo* lleva el sufijo `(Excel/CSV)` para distinguirlo de *Abrir/Guardar Proyecto* (`.edufem` JSON nativo, no editable a mano). El ZIP de CSVs es la vía editable en Excel para edición masiva.
- *Memoria de Cálculo (PDF)* — no "Reporte". Anticipa la expansión hacia un documento didáctico paso a paso (fórmulas, K, B, D, vectores, diagramas) alineado al espíritu de los módulos M1..M9. Hoy el output sigue siendo tabular (reportlab); el rename es deliberado para fijar la dirección.
- *Exportar Resultados CSV* fue **eliminado del menú** — los resultados se copian directamente desde la tabla del Post-Proceso con `Ctrl+C` (TSV al portapapeles, pegable en Excel). `selectmode="extended"` + `Ctrl+A` permiten seleccionar todo o subconjuntos. **No reintroducir** la entrada de menú.

**Orden FEM del menú Modelo**: Elemento → Unidades → Material → **Gravedad** → Análisis. Sigue el flujo lógico de definición de un problema FEM: primero la geometría discreta (Q4/Q9), después cómo se mide (sistema de unidades), después de qué está hecho (E, ν, ρ por material), después qué cargas volumétricas actúan (gravedad, depende de ρ para `F = ρ·g·V`), y al final el tipo de problema (TP / DP), donde la matriz constitutiva D = D(E, ν, caso) combina material y análisis. **La gravedad va después de Materiales** porque conceptualmente es una CARGA (no una unidad) y depende de la densidad — moverla antes rompe la jerarquía pedagógica. **No reordenar** salvo que se replantee el flujo.

**`GravityDialog`** ([gui/dialogs/gravity_dialog.py](gui/dialogs/gravity_dialog.py)): layout minimalista (440×260 px) — header + 2 entries `gx`/`gy` + toggle `include_gravity` + footer Cancelar/Aceptar. **Sin Labelframes**, **sin subtítulo descriptivo** (la fórmula `F = ρ·g·V` es info del solver, no del input), **sin labels "(unidad coherente con el sistema activo)"** junto a cada Entry (redundante con el sistema activo del proyecto), **sin botón preset "(0, -9.81)"** (el usuario lo tipea sin esfuerzo) y **sin hint** debajo del toggle. Mientras está abierto, registra una capa overlay sobre `MeshCanvas` via `add_overlay_layer` que dibuja una flecha desde el centro del bbox del modelo (o del canvas si está vacío) en dirección `(gx, -gy)` (flip Y por inversión screen). Color `PHASE_PROC_COLOR` cuando `include_gravity=True`, `TEXT_MUTED_FG` cuando está off. La capa lee `self._gx_live`/`self._gy_live` y se refresca en cada `canvas.redraw()` disparado por el trace de los Entry. La capa se desregistra en Aceptar/Cancelar. **No reintroducir** Labelframes "Componentes"/"Aplicacion", botón preset, labels de unidad junto a los Entry, ni hints debajo del toggle — la flecha en vivo sobre el canvas hace todo el trabajo pedagógico.

**`UnitsDialog` con conversión automática** ([gui/dialogs/units_dialog.py](gui/dialogs/units_dialog.py)): layout minimalista (440×180 px) — solo un combobox con los 8 sistemas + footer. Sin Labelframe, sin subtítulo, sin banner explicativo, **sin chip-line de unidades derivadas** (redundante con el nombre del sistema en el combobox: `SI (N, mm, MPa)` ya enumera las tres unidades), **sin modal de confirmación** (la conversión de valores se aplica automáticamente al aceptar — el usuario nota el cambio en los headers de tablas y en los valores numéricos; pedagógicamente, ver `1.0 m → 1000.0 mm` refuerza la relación entre unidades). Los factores vienen de `config.units.get_conversion_factors(from_sys, to_sys)` y se aplican a: coords de nodos, espesor (default y override), E de los materiales, fuerzas nodales, cargas distribuidas (factor compuesto force/length), y vector gravedad (factor acceleration = length). **Densidad y ν no se convierten** — la masa no está en nuestra 3-tupla (L, F, σ). Solo `gx`/`gy` (aceleración) escalan con length porque comparten dimensión L/T². Tras `convert_units` la solución (`is_solved`, K, F, u, stresses) se invalida porque K depende de E. Status bar reporta `Unidades: X (valores convertidos)`. **Compensación de cámara del `MeshCanvas`**: tras la conversión, `units_dialog._on_accept` divide `mesh_canvas.scale` por `factors["length"]`. Razón: `world_to_screen` calcula `sx = x · scale + offset_x`; si las coords mundo se multiplicaron por `f`, dividir `scale` por `f` mantiene la posición en pantalla de cada nodo invariante (el origen world (0,0) mapea siempre a `(offset_x, offset_y)` independientemente de `scale`, así que los offsets no cambian). El modelo NO salta ni cambia de tamaño visualmente — solo cambian los números que el usuario lee en tablas/headers. **No reintroducir** un `fit_view()` automático tras conversión (rompía el pan/zoom del usuario, era visualmente disruptivo). **No reintroducir** el modo Personalizado, el chip-line de unidades derivadas, ni el modal `askyesnocancel` — todos eliminados como ruido visual.

**Chequeos de consistencia de unidades** ([models/model_health.py](models/model_health.py)): tres warnings heurísticos en `validate_project` que detectan mismatch numérico ↔ unidad. (1) `SUSPICIOUS_YOUNG_MODULUS`: convierte E del material a Pa y avisa si está fuera de `[1e8, 5e11]` Pa (rango de materiales estructurales típicos, desde maderas hasta cerámicas). (2) `SUSPICIOUS_MODEL_SCALE`: convierte la extensión del modelo a metros y avisa si está fuera de `[0.1 mm, 10 km]`. (3) `GRAVITY_NO_DENSITY`: si `include_gravity=True` pero la densidad del material asignado es ≤ 0. Los tres se skip-ean si `unit_system` no está en `UNIT_SYSTEMS` (caso defensivo, archivo corrupto). Test de regresión: [tests/test_unit_conversion.py](tests/test_unit_conversion.py).

Diálogos en [gui/dialogs/](gui/dialogs/): `(parent, project, main_window=None)`. Invocables desde menú o desde tabs sin acoplarse.

**`MaterialDialog`** ([gui/dialogs/material_dialog.py](gui/dialogs/material_dialog.py)): master-detail compacto (680×460 px). Panel izquierdo: lista de materiales (**solo nombres**, sin swatch ni meta) + botones **Nuevo / Eliminar**. Scroll de la lista **exclusivamente con la rueda del mouse** (`<MouseWheel>` enlazado a canvas, frame interno y cada row) — **sin scrollbar visible**, alineado con el patrón del spreadsheet del pre/post-proc. Panel derecho: form con 4 entries (Nombre, E, ν, ρ) + botón Guardar. **Sin footer de 'Cerrar'** — la X nativa del Toplevel cierra y no hay commit global que justifique un 'Aceptar' (cada material se guarda con su propio Guardar del panel derecho); agregar un botón de footer aquí sería ruido sin acción nueva. **Sin selector de color** — el atributo `Material.color` fue eliminado en 2026-05 (no era consumido por solver ni canvas, solo aparecía en este diálogo). Sin Labelframe "Vista previa", sin status label, sin hints, sin contador, sin Duplicar. Validación live deshabilita Guardar si: E≤0, ν fuera de `(-1, 0.5)`, ρ<0, o nombre vacío. Cambio de nombre cascadea a `element.material_name`. Captura undo antes de cada mutación. **Librería default** (`Material.get_default_library()`): solo **Acero Estructural** y **Concreto f'c=21 MPa**. **Backward-compat**: `Material.from_dict` ignora silenciosamente el campo `color` de archivos `.edufem` legacy; `model_io._import_materials` ignora la 5ta columna (color) si aparece en CSV legacy y rellena con `""` si la fila viene con <4 columnas. **No reintroducir** `Material.color`, swatch/paleta/picker de color, scrollbar visible en la lista, botón Duplicar, footer con botón Cerrar/Aceptar, `TYPICAL_MATERIALS`, ni el colorchooser nativo. Si en el futuro se requiere `color`, agregarlo como campo opcional en `Material.__init__` con default `None` y reintroducir el selector (preferentemente la paleta 3×8 curada que estaba antes de este pase).

**`ElementTypeDialog`** ([gui/dialogs/element_type_dialog.py](gui/dialogs/element_type_dialog.py)) soporta Q4↔Q9 en ambos sentidos: Q9 sobre Q4 → `expand_q4_to_q9`; Q4 sobre Q9 → `shrink_q9_to_q4` con confirmación modal. **Layout idéntico a `AnalysisTypeDialog`** (760×660 px, video arriba 720×480 + toolbutton radios grid 50/50 + hint + footer): el cantilever Q4 vs Q9 (`resources/videos/cantilever_q4_q9.webp`, 900×600 escalado a 720×480, autoplay seamless via `WebpPlayer`) ocupa la mitad superior y los dos toolbuttons abajo se alinean con sus columnas — Q4 chip bajo la columna izquierda, Q9 chip bajo la derecha. **Tres toques creativos aprovechando que el video tiene identidad cromática por columna** (Q4=gris, Q9=naranja): (1) cada chip color-matches su columna → Q4 chip `secondary-toolbutton` gris, Q9 chip `warning-toolbutton` naranja (a diferencia de `AnalysisTypeDialog` que usa `info-toolbutton` para ambos, porque TP/DP no tiene identidad cromática equivalente); (2) cada chip incluye un mini-icono PIL del layout de nodos del elemento (4 puntos 2×2 para Q4, 9 puntos 3×3 para Q9) generado on-the-fly con `PIL.ImageDraw` — previsualización visual del concepto que el chip representa, refs anti-GC en `self._icon_q4` y `self._icon_q9`; (3) el texto de cada chip incluye el conteo de DOF (`Q4 · 8 DOF`, `Q9 · 18 DOF`) como información de decisión costo/precisión. El **hint operacional de Q9** (*"En Q9, los 5 nodos internos (medios + centroide) se generan automáticamente"*) se conserva como única línea italic muted entre los toolbuttons y el footer — info no obvia que previene confusión cuando el alumno ve nodos aparecer al cambiar de tipo. `AnalysisTypeDialog` NO tiene equivalente porque TP/DP no tiene una sutileza operacional análoga. La bidireccionalidad NO se explicita textualmente: la UI binaria + el modal de confirmación Q9→Q4 ya la comunican. **No reintroducir**: header con pregunta `¿Qué precisión necesitás?` (el título del Toplevel ya implica la pregunta, ningún diálogo del menú Modelo tiene pregunta-header), subtítulo descriptivo, radios verticales `info`, banner *"↔ Configuración bidireccional"*, tiles (`_ElementTile`), mini-gráfico (`_MiniElementGraphic`) — todos eliminados o consolidados en iteraciones previas. Si el `.webp` no existe, degrada a placeholder textual.

**`AnalysisTypeDialog`** ([gui/dialogs/analysis_type_dialog.py](gui/dialogs/analysis_type_dialog.py)) es **minimalista**: `Radiobutton` TP/DP + UNA SOLA ventana de video que se reasigna según la selección. Cambiar TP↔DP recarga `resources/videos/tension_plana.webp` o `resources/videos/deformacion_plana.webp` en el mismo widget `WebpPlayer` (autoplay, loop seamless, sin barra de controles). Si el `.webp` falta, el frame degrada a un mensaje informativo con la ruta esperada. **NO contiene la matriz D** — esa explora por-elemento desde el módulo M3 (Proceso > Educación) porque depende del material. **Hereda de `ttk.Toplevel`, NO de `BaseEducationalModule`** — es UI minimalista del menú, no un módulo educativo.

**Anti-pattern (no hacer)**: usar `FuncAnimation` sin guardar referencia persistente — el GC mata la animación y/o freeza el `Toplevel` modal. Patrón correcto: `self._anim = FuncAnimation(...)` + `self._anim.event_source.stop()` en cierre. Las animaciones del `ElementTypeDialog` migraron a WebP animado prerenderizado y el `AnalysisTypeDialog` usa solo WebP — el patrón sigue documentado por si se reintroduce en algún módulo educativo nuevo.

**Reproductor de WebP animado** ([gui/widgets/webp_player.py](gui/widgets/webp_player.py)): widget `WebpPlayer(parent, scaled=True, background=...)` lightweight basado **solo en Pillow** (sin `PyAV`/FFmpeg → ahorra ~30 MB en el instalador PyInstaller). API: `load(path) → play() → stop()`. Loop seamless interno (no requiere bind `<<Ended>>`). Decoder on-the-fly por frame, sin cache (RAM constante). Expone `seek_frame`, `seek_ms`, `n_frames`, `current_time_ms`, `total_duration_ms` y callback opcional `on_frame_change(idx, cur_ms, total_ms)` para wrappers con scrubber (ver [education/components/video_player.py](education/components/video_player.py)). **Trampa**: el muxer libwebp de ffmpeg escribe `duration=0` por frame — `WebpPlayer.load` trata 0 como ausente y aplica 45 ms (~22 fps) por defecto, así que la duración total es coherente.

**Pipelines de generación de videos**: dos rutas, ambas terminan en un `.webp` animado en `resources/videos/`.

(1) **Manim → WebP** (preferido, activo): `tools/render_tp_dp_manim/` para `tension_deformacion_plana.webp` y `tools/render_q4q9_manim/` para `cantilever_q4_q9.webp`. Cada uno es una clase `Scene` en Python (`tpvsdp.py`, `q4_vs_q9.py`) que define geometría y timeline; render con `manim -qh script.py SceneName`, conversión a WebP con `ffmpeg -vcodec libwebp -filter:v "fps=22,scale=900:600:flags=lanczos" -q:v 75 -loop 0 -an -vsync 0`. Output determinístico, 1 sola dependencia (manim), coherencia visual entre videos (paleta sincronizada con `config/settings.py`, mismo layout 2 columnas con separadores, misma estrategia de loop seamless basada en `set_opacity(0)` del `dynamic_group` al inicio + fade-out simétrico al final).

(2) **Claude Design + Chrome → WebP** (legacy, conservado como referencia): [tools/render_q4q9/record.mjs](tools/render_q4q9/record.mjs) usa Chrome headless + DevTools Protocol (WebSocket nativo de Node 24+, sin instalar paquetes) + ffmpeg. Pasos: descargar bundle tar.gz desde Claude Design, levantar `python -m http.server`, capturar JPGs vía `Page.startScreencast`, recortar a `frames_per_loop = duration_loop * fps_real` para loop seamless, componer con `ffmpeg -framerate <real> -frames:v <N> -c:v libx264 out.mp4`, luego convertir a WebP igual que arriba. Reusable para futuras animaciones generadas en Claude Design. **El video cantilever_q4_q9.webp del proyecto fue migrado de este pipeline al Manim** (1) **en 2026-05** — `tools/render_q4q9/` queda como referencia pero el render activo vive en `tools/render_q4q9_manim/`.

**No reintroducir** la dependencia `tkvideoplayer` ni `av`/`PyAV` — la migración a WebP es deliberada (instalador PyInstaller más liviano, sin DLLs FFmpeg que disparan falsos positivos de antivirus).

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
| Ctrl+1..7 | Módulos educativos M1..M7 en orden canónico FEM (mapeo, Jacobiano, D, B, K+Gauss, fuerzas, ensamblaje) |
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

9 módulos distribuidos por fase (M0 pre · M1..M7 proc con M5 fusionado K_e + Gauss · M9 post). Registro centralizado en [education/module_launcher.py](education/module_launcher.py): `MODULE_MAP` (mod_key → clase), `MODULE_PHASE` (`pre/proc/post → list`), `MODULE_META` (label + descripción), `GLOBAL_MODULES` (no requieren elemento seleccionado; expuesto como public para el panel educativo), `list_modules_for_phase(phase)`, `open_module(...)`. **Si añadís un módulo, registralo en los 4 dicts.**

**Flujo del launcher (UX agentiva unificada — overlays Y toplevels)**:
- **Cero diálogos modales**: el `simpledialog.askinteger` fue eliminado. Tanto overlays como toplevels se abren con `element_id=None` cuando no hay selección, y se actualizan automáticamente apenas el alumno clickee un elemento en el canvas. Razón: el modal de número rompe el flujo "click en canvas = single source of truth".
- **Overlays**: el módulo queda en estado "esperando elemento" en su panel; la cadena `on_selection_changed` del overlay base (`_overlay_edu_chain`) dispara `on_element_selected(eid)` al primer click válido. Cada módulo overlay debe tolerar `self.element is None` en su render — todos los activos del catálogo ya lo hacen vía guards tempranos del estilo `if self.element is None: return`.
- **Toplevels**: `BaseEducationalModule.__init__` cae a `_fallback_coords()` (placeholder demo) cuando no hay elemento. **Misma tecnología que los overlays**: el toplevel se engancha a `on_selection_changed` con un wrapper marcado `_toplevel_edu_chain=True`; al cambiar la selección a 1 elemento, el hook `on_element_selected(eid)` ejecuta el flujo `set self.element → _init_element_context → refresh_for_new_element` (default = `reset()` full rebuild de controles + viz). Las subclases pueden override `refresh_for_new_element` para refresh parcial más fluido. Limpieza determinista vía `protocol("WM_DELETE_WINDOW", ...)` Y `bind("<Destroy>", ...)` (cubre tanto X del WM como destroy programático).
- **Globales (M0, M9)**: no requieren elemento; auto-pick del primero del project.
- **Auto-pick cuando hay solo un elemento**: si `len(project.elements) == 1`, el launcher pasa ese eid directamente sin esperar selección.
- **Sincronización de selección al abrir**: el launcher usa `replace_element_selection({eid})` (idempotente) en vez de `highlight_element(eid)`. `highlight_element` → `select_element(elem_id, additive=False)` que tiene semántica "second-click deselects" — si el elemento ya era la única selección, **lo apagaba** (botón del módulo se ponía gris al abrirlo). **No reintroducir** `highlight_element` para sync al abrir módulo.

**Orden canónico de proc (reforma 2026-05)** alineado al pipeline FEM:

| Key | Label | Modo | Pedagogía |
|---|---|---|---|
| `mod01` | ① Mapeo iso + funciones N | **Overlay** | Split mirror físico↔natural + **comparación Nᵢ(ξ,η) vs Nᵢ(x,y) pulled-back** (motivación: por qué se usa el cuadrado natural). |
| `mod02` | ② Jacobiano det J | **Overlay** | **Cuadrado natural interactivo AL TOPE** (click/drag fija ξ,η — bidireccional con el canvas físico) + superficie 3D `coolwarm` divergente en 0 (cache por elemento) + toggle Fórmula/Valores + canvas: parches Gauss coloreados por det J + anillo rojo si det J ≤ 0. |
| `mod03` | ③ Matriz constitutiva D | **Overlay** | Dial de Poisson + toggle F/V + warning de locking. |
| `mod04` | ④ Matriz B | **Overlay** | **Cuadrado natural interactivo AL TOPE** (click/drag fija ξ,η — bidireccional con el canvas físico) + glow pulsante en Gauss + snap a Gauss + toggle F/V. |
| `mod05` | ⑤ Rigidez K_e + Gauss | **Overlay** | **Fusión K_e + cuadratura.** Fórmula héroe ∫ → Σ + expander colapsable "¿Por qué no se puede integrar a mano?" (integrando simbólico del ex-M5) + cuadratura interactiva: PGs clickeables sobre el elemento real (sumar/quitar) + matriz kₑ que crece + warnings hourglass/sobre-integración. |
| `mod06` | ⑥ Fuerzas equivalentes | **Overlay** | Drag-to-load + lluvia de partículas. |
| `mod07` | ⑦ Ensamblaje K, F + BCs | **Overlay** | **Vuelo Bézier desde el canvas real**: el kₑ despega del centroide real del elemento y sale por el borde del canvas más cercano al overlay flotante donde crece K. Trazas residuales acumuladas sobre el modelo + sparsity pattern adaptativo (scatter para K > 40×40, valores numéricos para K ≤ 16×16) + hover readout `K[i,j]` en el footer. **Click en un elemento del canvas lo manda al frente de la cola** (shortcut "ensámblame ESTE ahora"). |

**Cambios de nombre de archivo respecto a 2026-04**:
- ex-`mod02_b_matrix.py` → `mod04_b_matrix.py`
- ex-`mod04_stiffness_gauss.py` → `mod05_stiffness_gauss.py`
- ex-`mod05_assembly.py` → `mod07_assembly.py`
- **nuevo**: `mod02_jacobian.py` (extraído de M1: det J ya no vive en M1, M2 lo trata como objeto en sí).

Tags canvas: cada Overlay usa `edu_mN_<sufijo>` (`edu_m0`, `edu_m2_jac`, `edu_m4`, `edu_m6`, etc.). El primer paso de `draw_canvas_layer` es siempre `mesh.canvas.delete(_TAG)`.

#### Modo de presentación (rediseño UX 2026 → 2026-05)

> **Estado actual**: TODOS los módulos (M0..M7 + M9) heredan de `CanvasOverlayModule`. El "modo Toplevel" y su clase base `BaseEducationalModule` (`education/base_module.py`) **fueron eliminados** — la tabla y las secciones que los mencionan quedan como **referencia histórica** de la propuesta UX original. `module_launcher.open_module` conserva una rama Toplevel defensiva (instancia `cls(parent_tk, ...)`) que hoy es **inalcanzable** (las 9 clases exponen `activate` vía `CanvasOverlayModule`).

| Modo | Patrón base | Cuándo |
|---|---|---|
| **Toplevel** *(histórico, sin clases activas)* | ~~hereda de `BaseEducationalModule`~~ (eliminado) | módulos amplios, comparación lado-a-lado, vista 3D pantalla completa, sandbox |
| **Overlay** | hereda de [CanvasOverlayModule](education/overlay_module.py) | TODOS los módulos hoy; concepto que vive *sobre* la malla real (glow, cruces, coloreado, drag) y/o paneles flotantes amplios (M1, M9) |

El despacho lo hace `module_launcher.open_module(...)`: si la clase tiene `classmethod activate(...)` se abre como Overlay (caso de los 9). **No mezclar herencias** — cada módulo elige UNO solo.

#### Iluminación reactiva del panel de módulos (propuesta UX 2026)

El panel de botones de módulos educativos (Pre/Proc/Post) reacciona a la selección de elemento del MeshCanvas. Implementado en [gui/widgets/module_launcher_panel.py](gui/widgets/module_launcher_panel.py) (`ModuleButtonsPanel`).

Estados de cada botón:

| Estado | Bootstyle | Chip a la derecha |
|---|---|---|
| Global (M0, M9) — no requiere elemento | siempre `<fase>-outline` | vacío |
| Por-elemento, sin selección | `secondary-outline` (gris) | vacío |
| Por-elemento, con 1 elemento seleccionado | `<fase>-outline` (color) | `#N` |
| Por-elemento, visitado en esta sesión | (mantiene su estado actual) | `#N ✓` (o solo `✓` si está sin selección) |

Reglas:
- **No apagar tras uso** — el alumno reabre módulos para comparar elementos distintos. El ✓ es indicador de progreso, no de bloqueo.
- **Click siempre clickeable** — incluso en estado gris. Si no hay selección y el módulo lo requiere, el launcher cae al `simpledialog` clásico (fallback).
- **Multi-select de elementos**: el panel desactiva (queda gris) cuando hay >1 elemento seleccionado — la pedagogía opera UN elemento a la vez.
- **Modules globales**: se listan en `education.module_launcher.GLOBAL_MODULES` (público). Pasalo al panel para que NO los desactive.

Wiring (en [main_window.py](gui/main_window.py)._build_main_layout): tras crear el MeshCanvas se invoca `tab.wire_canvas()` en orden `pre_tab → proc_tab → post_tab`. Cada tab engancha al `mesh_canvas.on_selection_changed` encadenando con el callback previo (no lo pisa). `pre_tab` aprovecha que ya tiene `_on_canvas_selection_changed` y refresca el panel ahí dentro. `proc_tab` y `post_tab` insertan un wrapper chained.

**No reintroducir** scrollbar visible en el panel de módulos, badges textuales con el id de elemento dentro del botón (el chip a la derecha lo resuelve), ni "deshabilitar" botones globales por falta de selección (mod00 y mod09 no la necesitan).

#### Estado actual de los módulos (9/9 rediseñados)

| ID | Fase | Modo | Feature signature |
|----|------|------|-------------------|
| M0 | pre  | **Overlay** | Vista rayos X (celdas con **relleno tintado semitransparente** `gray50` que deja ver el fantasma + borde del color de calidad + nodos corner distorsionados, verde/amarillo/rojo por **peor clase por-métrica**) + **dos barras en sus rangos bibliográficos de Verdict** (Jacobiano `SJ ∈ [-1, 1]` valor crudo, Compacidad `Stretch ∈ [0, 1]`) con corte aceptable **literal de Verdict por métrica** (SJ 0,50 / Stretch 0,25, marcado con línea "acept.") + **anotaciones geométricas sobre el canvas** (arco del peor ángulo + θ, arista Lmín, diagonal Dmáx) + drag de vértice distorsiona en vivo (refresco solo-capa) |
| M1 | proc | **Overlay** | **Split mirror** físico ↔ natural + **dos superficies 3D**: Nᵢ(ξ,η) limpia + Nᵢ(x,y) pulled-back retorcida (motivación isoparamétrica). det J FUERA de M1 (vive en M2 dedicado). Cuadrado natural matplotlib con estilo unificado (mismas constantes `EDU_NATURAL_*` que el widget tk). |
| M2 | proc | **Overlay** | **Cuadrado natural interactivo AL TOPE** (click/drag fija ξ,η; bidireccional con el canvas) + superficie 3D `coolwarm` divergente en 0 de det J(ξ,η) (cache por elemento) + plano z=0 en rojo + parches Gauss coloreados sobre canvas + anillo rojo si degenerado + toggle F/V con la matriz J. **det J del punto = etiqueta anclada al marcador 3D** (ver dedup M2 abajo). |
| M3 | proc | **Overlay** | Dial físico de Poisson + toggle Fórmula↔Valores + warning de locking volumétrico cuando ν → 0.5 en DP. |
| M4 | proc | **Overlay** | **Cuadrado natural interactivo AL TOPE** (click/drag fija ξ,η; bidireccional con el canvas) + glow pulsante (~30 fps) en puntos Gauss + toggle Fórmula↔Valores + click snap a Gauss. |
| M5 | proc | **Overlay** | **Fusión K_e + Gauss.** Fórmula héroe ∫ → Σ + expander colapsable "¿Por qué no se puede integrar a mano?" (integrando simbólico) + cuadratura interactiva (PGs clickeables sobre el elemento, matriz kₑ que crece, warnings hourglass/sobre-integración). |
| M6 | proc | **Overlay** | Drag-to-load + lluvia de partículas. |
| M7 | proc | **Overlay** | **Vuelo Bézier desde el canvas real** (kₑ despega del centroide del elemento, sale por el borde más cercano al overlay flotante con K) + trazas residuales acumuladas sobre la malla + sparsity adaptativo (scatter K > 40 / imshow valores K ≤ 16) + hover readout `K[i,j]` + click-en-canvas adelanta el elemento clickeado al frente de la cola. |
| M9 | post | **Overlay** (grande) | Vista panorámica 2×4 Q4/Q9 + convergencia log-log. |

**ex-M7 (mod07_stress_discontinuity) y ex-M8 (mod08_principal_stresses) eliminados como módulos** — consolidados en el flujo nativo del Post-Proceso (ver "Vistas avanzadas del Post" abajo). El nuevo M7 es Ensamblaje (que era M5 en la numeración antigua).

#### Infraestructura del modo Overlay

Tres piezas reutilizables — **no duplicar**:

- **[gui/widgets/canvas_overlay.py](gui/widgets/canvas_overlay.py)** `CanvasOverlay`: **Toplevel borderless** (`overrideredirect(True)`) posicionado en coordenadas de pantalla. Header con barra de color por fase + título + botón ×. Cuerpo expuesto como `self.body`. Drag por header (cualquier punto). `phase` ∈ `{"pre", "proc", "post"}` controla el color. **Crítico**: NO es un `Frame` placed dentro del MeshCanvas — esa fue la implementación inicial (2026-04) y se descartó porque `place()` recorta al parent y el `_clamp` confinaba el panel dentro del canvas, **tapando elementos que el usuario quería clickear**. El Toplevel borderless permite arrastrar el panel a cualquier parte del escritorio (incluso sobre el spreadsheet o a un monitor secundario), liberando completamente la malla. Clamp suave contra los bordes de pantalla para que el header (≥80×24 px visibles) siga siendo agarrable. `initial_pos` se interpreta relativo al parent (típicamente `MeshCanvas`) y se traduce a coords de pantalla en `show()` vía `parent.winfo_rootx()`. Tamaño: si `OVERLAY_HEIGHT=None`, se usa `winfo_reqheight()` tras `update_idletasks()`.

  **Reglas no negociables del ciclo de vida** (lecciones aprendidas a costa de crashes y misbehavior):
    1. **`transient(root)` ES necesario** — sin él, Windows trata al Toplevel `overrideredirect=True` como un *popup* clásico y lo oculta al primer focus change al main window (el usuario percibe "el overlay desaparece al hacer hover/click sobre el canvas"). `transient` lo convierte en *tool window*, persiste visible mientras la app tenga focus.
    2. **NO registrar `protocol("WM_DELETE_WINDOW", ...)`** — para `overrideredirect=True` el WM no envía esos eventos y registrar el protocolo abre la puerta a propagación al root.
    3. **NO llamar `destroy()` al cerrar** — `close()` hace `withdraw()` únicamente. Destruir un Toplevel `overrideredirect=True + transient(root)` desde un handler de evento de un widget hijo del propio Toplevel dispara un WM_CLOSE al root en builds Tcl/Tk de Windows y mata la app. Como trade-off, el Toplevel queda como objeto Python retenido hasta que el módulo educativo se libere y el GC del intérprete Tcl lo recolecte. Bounded por la cantidad de clases overlay (singleton por clase) — unas decenas de KB.
    4. **El botón × se bindea a `<ButtonRelease-1>`, NO `<ButtonPress-1>`** — el release garantiza que Tk terminó de procesar el evento antes de invocar `close()`. Y el handler llama a `_request_close()` que difiere via `after_idle` para escapar del event loop frame del propio evento.
    5. **Las reglas 1-3 son interdependientes**: necesitamos `transient` (regla 1) pero `transient + destroy` crashea (regla 3), así que la única salida es `transient + withdraw-only` (cumpliendo 3). Cambiar una sin las otras rompe la app.
    6. **No reintroducir** la versión con `place()` ni el clamp contra el parent.
- **[education/components/formula_value_blocks.py](education/components/formula_value_blocks.py)** `FormulaValueBlocksToggle`: segmented toggle `[ƒ Fórmula | 123 Valores]` donde cada modo se construye con widgets Tk propios (via callbacks `build_formula(frame)` / `build_values(frame)`), NO un `ax` matplotlib compartido. **Patrón canónico para overlays con toggle Fórmula↔Valores** — usado por M2, M3, M4. (El ex `FormulaValueToggle`, basado en un `ax` compartido, se solapaba con matrices Q9 y fue **eliminado** en la limpieza 2026-05.)
- **[education/overlay_module.py](education/overlay_module.py)** `CanvasOverlayModule`: base class. Singleton suave por `(main_window, cls)` (re-activar trae al frente en lugar de duplicar). **Política de overlay único**: al abrir uno nuevo, `activate()` cierra automáticamente los OTROS overlays activos en el mismo main_window — evita que las capas de un módulo (p.ej. trazas de M7) queden visibles cuando el alumno abre otro. **Broadcast de selección**: se encadena a `mesh_canvas.on_selection_changed(dict)` (API moderna) con un wrapper marcado `_overlay_edu_chain=True`. El wrapper llama primero al callback previo (proc_tab/post_tab) y después decodifica la selección: single-element → `on_element_selected(eid)`, single-node → `on_node_selected(nid)`. Multi-select y deselección NO se propagan a los hooks de módulo (el alumno conserva el último contexto válido). **Las legacy `on_element_select` / `on_node_select` están MUERTAS** — el canvas no las dispara; no usarlas. Registra una "capa educativa" via `mesh_canvas.add_overlay_layer(layer_callable)` que dibuja con tags propios (prefijo `edu_X`). El cleanup desencadena el wrapper de selección, quita la capa, hace `redraw()` defensivo, y libera el slot del singleton.

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

#### Migración completada (9 módulos)

Tras la migración 2026-05: **los 9 módulos son Overlay** (M0..M7 + M9 heredan de `CanvasOverlayModule`). **`education/base_module.py` y la clase `BaseEducationalModule` ya NO existen** — fueron eliminados al migrar el último Toplevel. Las secciones de abajo que describen el "modo Toplevel" (`NO_SIDEBAR`, `build_visualization`, `build_controls`, `SHOW_PROJECT_BADGE`, `HAS_ANIMATION`) son **históricas**: ese contrato ya no está en el código. M9 (panorámico Q4 vs Q9) y M1 son overlays grandes, no Toplevels.

**Fusión de M5 + M5b (2026-05)** ([education/mod05_stiffness.py](education/mod05_stiffness.py)): el split previo (M5 integrando + M5b cuadratura, dos overlays vecinos) se reunió en UN solo overlay porque la narrativa "la integral es imposible → por eso usamos Gauss" es un único argumento; partirlo obligaba al alumno a abrir/cerrar para conectar las mitades. Estructura del módulo fusionado (problema → solución, sin scroll forzado):
- **Fórmula héroe**: dos líneas con el salto conceptual ∫ → Σ — arriba `k_e = ∫∫ BᵀDB |det J| t dξdη` (rojo, "imposible a mano"), abajo `k_e ≈ Σ_p w_p Bᵀ(ξ_p,η_p) D B |det J| t` (ámbar, "lo aproximamos en los PGs"). El salto se lee de una sola pasada.
- **Expander colapsable** "▸ ¿Por qué no se puede integrar a mano?" (`Expander` de [education/components/expander.py](education/components/expander.py)): oculta por defecto el "monstruo" simbólico K_(i,j)(ξ,η) — selector de entrada (i,j) + integrando LaTeX (render perezoso: solo cuando el expander está abierto) + label de complejidad clickeable que abre una ventana scrollable con la expresión completa. Cero ruido si no se abre; evidencia contundente si se abre. En Q9 muestra el notice (B es 3×18, expansión excede mathtext). **Contiene `SymbolicIntegrandQ4`** — importada por [file_io/memoria_calculo.py](file_io/memoria_calculo.py); no mover sin actualizar ese import.
- **Cuadratura interactiva** (acto principal, siempre visible): chips de orden 1×1/2×2/3×3 + PGs clickeables sobre el elemento REAL del canvas (sumar/quitar PG via click consumer; sumado → dorado, excluido → ghost) + matriz k_e que CRECE con cada PG sumado + warnings de hourglass (1 PG) y sobre-integración (3×3 en Q4). Estado inicial: todos los PGs sumados (la cuadratura correcta).
- Termina con `👉 k_e completo se ENSAMBLA en K global. Ver ⑦ Ensamblaje`.

**Cuadrado natural interactivo en M2/M4 (2026-05)**: el `GaussCoordReadout` ([education/components/gauss_inset.py](education/components/gauss_inset.py)) ganó un modo `interactive=True` + `on_pick(xi, eta)` + `title`. En M2 y M4 ahora vive AL TOPE del overlay (posición estratégica, no al pie) y es una **superficie de entrada**: click o drag dentro del cuadrado fija (ξ,η) directamente y dispara el pick. Esto materializa la dualidad de espacios — el alumno tiene DOS lugares donde fijar el mismo punto (el cuadrado natural ξ,η y el elemento físico x,y del canvas) y ve el marcador moverse en ambos a la vez. Resuelve la confusión pedagógica de que "la matriz se evalúa en (x,y)": el título lo dice ("J/B se evalúa en el cuadrado natural (ξ, η)") y la interacción lo demuestra. En M2 la superficie 3D de det J se **cachea por elemento** (`_surf_cache`) porque Z(ξ,η) no depende del punto seleccionado — el drag solo mueve el marcador, sin recomputar las 28×28 evaluaciones.

**Unificación del cuadrado natural + snap a Gauss bidireccional (2026-05, 3ª pasada)**: el estilo de M1 es ahora la **referencia única** para todos los módulos que usan el cuadrado natural (M1, M2, M4, M5). Los colores viven en `config/settings.py` (`EDU_NATURAL_OUTLINE_COLOR` #4fa3ff, `EDU_NATURAL_AXES_COLOR` #3a5278) y los consumen tanto el render matplotlib de M1 (`_draw_natural`) como el tk.Canvas `GaussCoordReadout` — **cero hex duplicados** (antes `_C_BLUE`/`_C_NATURAL_OUTLINE` eran copias del mismo literal). M1 sigue en matplotlib (acoplado a sus superficies 3D Nᵢ); el widget sigue en tk.Canvas (rápido para el drag) — se unifica el **estilo**, no el backend (el caveat semántico es legítimo: M1 marca **nodos**, M2/M4/M5 marcan **puntos Gauss** sobre el mismo cuadrado). El modo interactivo del widget ahora aplica **snap PRIORITARIO a PG**: si el click/drag cae dentro de `_SNAP_TOL_PX` de un PG del grid activo, engancha a sus coords canónicas exactas (±1/√3); si no, punto libre. El pick es **bidireccional**: M2/M4 matchean las coords devueltas contra su propio grid (`_match_gauss_index`, por coordenada — robusto al ordering) → fijar un PG en el cuadrado lo selecciona también en el canvas físico (halo) y viceversa. **No reintroducir** los literales `#4fa3ff`/`#3a5278` locales ni el marcador de punto libre dibujado a mano (usar `draw_gauss_free_point` de gauss_glyph, color `EDU_FREE_POINT_COLOR`). **Las flechas de ∇Nᵢ sobre el elemento (probadas y retiradas a pedido del usuario en 2026-05) NO se reintroducen** — el modo interactivo de M4 se queda en snap-a-PG + punto libre + B que actualiza.

**Refinamiento de módulos educativos (2026-05, segunda pasada)** — seis decisiones de diseño aplicadas tras feedback:

- **Cuadrado natural uniforme + sin frame pesado** ([gauss_inset.py](education/components/gauss_inset.py) `_draw_inset`): se eliminó el segundo `create_rectangle` (relleno `stipple=gray12`, el "frame que cerraba" el elemento) y el contorno bajó a `width=1.0`. Ahora el cuadrado natural de `GaussCoordReadout` (M2/M4/M5) es visualmente coherente con el de M1 (que ya usaba un contorno simple en matplotlib). **Decisión deliberada**: M1 conserva su backend matplotlib (su cuadrado está acoplado a la superficie 3D Nᵢ en la misma figura); no se fuerza un widget único — se unifica el ESTILO (mismo `#4fa3ff`, ejes `#3a5278`, sin relleno), no el backend.
- **LaTeX selectivo, NO universal** (idea "todo en LaTeX" matizada): las **fórmulas conceptuales estáticas** migraron a `LatexExpressionImage` — los 2 banners héroe de M5 (`∫∫BᵀDB|detJ|t` y `Σ wₚBᵀDB|J|t`), la ecuación `K·u=F` en la vista SISTEMA de M7 (mathtext `suptitle`). La fórmula `Nᵢ(ξ,η)` de M1 NO usa `LatexExpressionImage`: es el **título mathtext de la superficie 3D** (ver punto siguiente). **El chip de dualidad `(x,y) ↔ (ξ,η)` de M1 fue eliminado** (2026-05): el título del overlay `①  Mapeo isoparamétrico  (x,y) ↔ (ξ,η)` ya enuncia la dualidad; repetirla en el cuerpo era redundante. Con él se removió su pulso (`_pulse_chip`/`_reset_chip`). **No reintroducir** el chip ni el pulso. Los **readouts numéricos dinámicos** (que cambian con hover/drag: `det J = ...`, `Σ 2/4 pg`, `N₁(ξ,η) = 0.455`) **se mantienen en Consolas** — convertirlos a LaTeX agrega latencia (la caché no acierta con valores siempre distintos) sin ganancia pedagógica. Frontera: **fórmulas en LaTeX, números vivos en monospace**. `_unicode_math_to_latex()` ([latex_image.py:1069](education/components/latex_image.py#L1069)) auto-convierte unicode en los renderers, así que migrar es de bajo acoplamiento.
- **Fórmula + evaluación de Nᵢ DENTRO del panel 3D en M1** ([mod01_iso_mapping.py](education/mod01_iso_mapping.py) `_shape_formula_latex` / `_shape_value_latex`, consumidas por `_draw_surface_n` / `_draw_markers`): rediseño 2026-05 (3ª pasada). Ni la fórmula ni el valor son ya widgets tk apilados bajo la figura — **se movieron al interior de la superficie 3D** para liberar alto vertical y agrandar la superficie (`figsize=(4.8, 5.5)`, `height_ratios=[0.82, 1.5]`). (1) **La fórmula simbólica `Nᵢ(ξ,η)` es el TÍTULO mathtext de la superficie 3D** (reactiva al nodo, `fontsize=13`, color `#90caf9`, dicts `_N_FORMULAS_Q4`/`_N_FORMULAS_Q9` que espejan [fem/shape_functions.py](fem/shape_functions.py)). Reemplaza al antiguo título `N{idx}(ξ,η)`, que duplicaba el lado izquierdo de la fórmula. (2) **La evaluación `Nᵢ(ξ,η)=valor` es una etiqueta ANCLADA al marcador**: `ax.text(sel_xi, sel_eta, ni_val + 0.10, ...)` en coords 3D, flotando justo encima del marcador (no pinneada a una esquina — decisión del usuario 2026-05), mathtext, caja `boxstyle="round"` estilo tooltip (bg `EDU_LABEL_BG`, borde del color del modo) para legibilidad sobre el colormap. Es el ÚNICO lugar donde vive el valor numérico. (Caveat conocido: el texto 3D puede ocluirse con la superficie en ciertos ángulos de cámara — painter's algorithm de matplotlib; se aceptó el trade-off a cambio de tener el valor pegado al punto.) **Sin signo `+` en positivos**: coords y valor usan `{:.3f}`/`{:.4f}` (solo `-` para negativos). **Dedup canvas↔overlay y dentro del overlay**: el número `Nᵢ` aparece una sola vez (la etiqueta del marcador); las coords `(ξ,η)` solo en esa etiqueta (input de la evaluación). La **línea de estado** (`_lbl_mode`) muestra SOLO el modo (`punto libre` / `nodo N`). El **canvas** (`draw_canvas_layer`) dibuja solo el marcador físico (sin label de valor). **Roles de las dos vistas del overlay**: cuadrado natural 2D = POSICIÓN (ξ,η) + nodos (interactivo, `_on_click_natural`); superficie 3D = la FUNCIÓN + valor (altura del marcador + tooltip). El punto se ve en 3 vistas (canvas físico, cuadrado 2D, superficie 3D) — bidireccionalidad del mapeo, NO redundancia (cada vista un trabajo, ningún número repetido). **No reintroducir**: widgets tk de fórmula/valor bajo la figura, el título `N{idx}(ξ,η)` de la superficie, el label `Nᵢ=valor` sobre el canvas, las coords en la línea de estado, el readout pinneado en esquina vía `text2D` (el usuario lo prefirió anclado al marcador), el signo `+` en positivos, ni la caja de texto sobre el cuadrado natural.
- **Coordenadas como marcador + det J anclado + dedup en M2** ([mod02_jacobian.py](education/mod02_jacobian.py) `_draw_surface_3d` / `draw_canvas_layer`; [gauss_inset.py](education/components/gauss_inset.py) `marker_coords`): mismos criterios que M1 (2026-05, 4ª pasada). **Cada coordenada viaja PEGADA a su marcador, en su propio espacio** — no hay bloque de texto detached: (a) **(ξ,η)** se dibuja como etiqueta junto al marcador DENTRO del cuadrado natural (el `GaussCoordReadout` gana el flag opt-in **`marker_coords=True`**: centra el cuadrado, elimina los dos `LatexStatusLabel` laterales `_lbl_natural`/`_lbl_physical`, y `_refresh_marker` pinta `(ξ,η)` pegada al marcador, ubicada del lado con más aire + clamp); (b) **(x,y)** se dibuja como `create_text` con caja de fondo pegada al punto seleccionado en el MeshCanvas (`draw_canvas_layer`); (c) **det J** del punto es etiqueta anclada al marcador 3D (`ax.text(xi, eta, dJ_sel + max(0.08·span, 0.12), …)`, caja `boxstyle="round"`, color por modo: naranja `_C_MARKER` si snap a PG, rojo `EDU_FREE_POINT_COLOR` si libre). **`marker_coords` es opt-in** — M4/M5 siguen con el layout clásico (cuadrado izq + readout dual LaTeX der). **`set_zlim` ceñido** a `[Z.min, Z.max]` (+ margen) en vez del auto-pad: la superficie de det J (rango angosto) ya no queda hundida abajo. **`figsize` 3.0 → 2.2** + cuadrado `side=140`: el overlay entra completo (el crossref inferior ya no se corta). **Título de la tabla de valores = SOLO el modo** (`J en pgN` / `punto libre` / `centro del elemento`). **Banner verde** sin `B computable` (lo dice el crossref a M4). **Sin `+` en positivos** en displays M2-locales (banner, labels de PG, (x,y) del canvas, (ξ,η) del marcador → `{:.Nf}`/`{:.Ng}`). Removido el atributo muerto `_lbl_status`. **"en latex" — decisión**: el `(ξ,η)` del cuadrado y el `(x,y)` del canvas usan `create_text` (símbolos math, instantáneo), NO imagen-LaTeX: ambos viven en `tk.Canvas` y se repintan en cada frame del drag → una imagen LaTeX por frame laggea. (Caveats 3D text: la etiqueta de det J puede ocluirse en ciertos ángulos — trade-off aceptado.) Pendiente menor: el `GaussCoordReadout` en modo clásico (M4/M5) aún muestra `+` en positivos. **No reintroducir**: el bloque de texto `(ξ,η)`/`(x,y)` detached en M2 (las coords van pegadas a sus marcadores), det J o coords en el título de valores, el auto-zlim holgado, `B computable` en el banner, el `+` en positivos M2-locales, ni `_lbl_status`.
- **Cuadrado natural reinsertado en M5** ([mod05_stiffness.py](education/mod05_stiffness.py)): la fusión M5+M5b había dropeado el `GaussCoordReadout`; se reinsertó porque la cuadratura se evalúa en los PGs del **espacio natural** y faltaba ese ancla. Usa el nuevo `set_pg_highlight(selected_coords)`: los PGs sumados se pintan dorado (`GAUSS_ACTIVE`), los excluidos en ghost dashed — **espeja exactamente la selección del canvas físico**. El highlight matchea por coordenada (tol 1e-3), desacoplando del ordering de `get_gauss_points_2d`.
- **Matrices que se cortan → scroll/pan IN-FRAME, NO pop-up** (reformulado 2026-05, 3ª pasada): el ex `MatrixZoom` (pop-up `Toplevel` que abría `LatexMatrixImage(zoomable=True)`) fue **eliminado** — generaba ruido (segunda ventana flotante sobre el overlay borderless). Lo reemplaza **`ScrollableMatrixImage`** ([latex_image.py](education/components/latex_image.py)): un `tk.Canvas` con `create_image` + `scrollregion` que muestra la matriz a fontsize LEGIBLE (`render_matrix_image(..., shrink=False)`, sin el encogido de `_fit_fontsize_for_shape`) dentro de un viewport de tamaño fijo, con **pan por arrastre** (`scan_mark`/`scan_dragto`) y **rueda** (scroll vertical; Shift+rueda = horizontal). Vive como hijo del `body` del overlay → **NO** redimensiona el `Toplevel overrideredirect` (cero riesgo de ciclo de vida, a diferencia de un grip de resize, descartado). Aplicado a B (M4, 3×18 en Q9) y kₑ (M5, 18×18 en Q9). Q4 (chicas) entra entero en el viewport sin scrollear. M3 (D 3×3) y M2 (J 2×2) siguen con `LatexMatrixImage` simple (no se cortan). **Trampa de rueda**: `CanvasOverlay._consume_wheel_recursive` bindea `<MouseWheel>→break` en todos los descendants en `show()` (después de construir el body), pisando cualquier bind hecho en `__init__`; `ScrollableMatrixImage` re-asierta su handler de rueda en `<Enter>` del canvas (corre en runtime, gana) y lo devuelve a `break` en `<Leave>`, y su handler retorna `"break"` (el scroll NO se propaga a la MeshCanvas ni al FigureCanvasTkAgg vecino — regla de oro #3 preservada). **No reintroducir** el pop-up `MatrixZoom` ni `LatexMatrixImage(zoomable=True)` (el flag `zoomable` quedó como no-op deprecado por compat). El param `shrink=False` de `render_matrix_image` es la vía para render legible sin encoger (el scroll resuelve el overflow).
- **Expanders parcos, NO todo desplegable** (idea "todas las fórmulas desplegables" descartada): se mantiene el modelo de 3 capas — Capa 1 siempre visible (el concepto), Capa 2 toggle Fórmula↔Valores (M2/M3/M4), Capa 3 expander **excepcional** solo para "¿Por qué…?" / "Ver derivación" (M0, M5). Hacer todo colapsable destruiría la jerarquía visual y causaría parálisis de decisión. **No reintroducir** expanders para fórmulas que son el contenido principal de su módulo.

**Cross-references** entre módulos (UX 2026): al pie de cada overlay vive un label corto con el bridge al siguiente concepto del pipeline FEM. Cada label usa color `#ffd54f` (acento) y comienza con `👉` para distinguir narrativa del contenido principal:
- M1 `👉 La distorsión local del mapeo (det J) se explora en ② Jacobiano.`
- M2 `👉 det J > 0 garantiza que la matriz B (④) sea computable en este elemento.`
- M3 `👉 Esta D entra en  k_e = ∫ BᵀDB |det J| t  (ver ⑤ Rigidez K_e).`
- M4 `👉 B + D (③) construyen el integrando de k_e — ver ⑤ Rigidez K_e + Gauss.`
- M5 `👉 k_e completo se ENSAMBLA en K global. Ver ⑦ Ensamblaje.`
- M6 `👉 Estas fuerzas nodales se SUMAN al vector F global. Ver ⑦ Ensamblaje.`
- M7 `👉 Al aplicar BCs y resolver K·u = F, obtenemos desplazamientos + tensiones (📊 Post-Proceso).`

**Atajos Ctrl+1..7** (orden canónico FEM, M5 fusionado):
| Ctrl | Módulo |
|---|---|
| 1 | M1 — Mapeo iso |
| 2 | M2 — Jacobiano |
| 3 | M3 — Matriz D |
| 4 | M4 — Matriz B |
| 5 | M5 — Rigidez K_e + Cuadratura de Gauss |
| 6 | M6 — Fuerzas equivalentes |
| 7 | M7 — Ensamblaje |

**Refactor 2026-05: M0 — 2 métricas en sus rangos bibliográficos + anotaciones sobre el canvas** — el módulo de calidad usa dos métricas **ortogonales** (forma angular + validez vs proporción geométrica): **Jacobiano** (Scaled Jacobian por vértices `sin(θᵢ)`, [fem/mesh_quality.py](fem/mesh_quality.py) `scaled_jacobian_corners`) y **Compacidad** (Stretch de Verdict `√2·Lmín/Dmáx`, `stretch_metric`). Ambas se presentan en **sus rangos bibliográficos completos de Verdict**: Jacobiano `SJ ∈ [-1, 1]` con el **valor crudo** (negativo = invertido), Compacidad `Stretch ∈ [0, 1]`. MISMO mapeo cromático rojo→amarillo→verde, pero con **corte "aceptable" (rojo→amarillo) POR-MÉTRICA, literal de la bibliografía** (Verdict/Cubit, SAND2007-1751): Scaled Jacobian aceptable `≥ 0,50`, Stretch aceptable `≥ 0,25` (`_SJ_ACCEPT`/`_ST_ACCEPT`). El corte "bueno" (amarillo→verde, `_SJ_GOOD = 0,80` / `_ST_GOOD = 0,50`) es convención de la UI; en Stretch el `0,50` coincide con el "aceptable ≥ 0,5" del docstring de `fem/mesh_quality` (reconcilia ambas fuentes: `0,25` = mínimo admisible Verdict, `0,5` = ya buena calidad). Cada barra marca su umbral aceptable con una línea **"acept."** (`QualityBar(accept_cutoff=...)`) — son distintos a propósito (cada métrica tiene su tolerancia). **El color del elemento en el X-ray es la PEOR clase por-métrica** (`_tier(sj, …)` vs `_tier(st, …)`), NO `min(sj, st)` contra un umbral único — ese bug pintaba de rojo elementos aceptables cuyo Stretch caía en `[0,25; 0,5)` (reporte: E3 con SJ=0,74 y Stretch=0,40 quedaba rojo siendo aceptable). En el Jacobiano `[-1, 1]` el tramo **inválido `[-1, 0]` queda rojo sólido** (negativo = invertido, sin gradiente útil) y el válido `[0, 1]` lleva el gradiente rojo→amarillo→verde; la **inversión `SJ ≤ 0`** además levanta un banner de aviso que **diagnostica la causa REAL** (`_diagnose_invalid`, staticmethod testeable) en vez de listar todas las posibles: con el área con signo (shoelace) + el giro por vértice (misma cruz que `scaled_jacobian_corners`) distingue → *"Elemento invertido — nodos en orden horario…"* (área < 0), *"Vértice cóncavo — el nodo N{id} forma un ángulo > 180°"* (área > 0 con un giro negativo; **nombra el nodo culpable**), *"Geometría cruzada…"* (≥ 2 giros negativos) o *"Elemento degenerado — área casi nula…"* (área ≈ 0). En **español, sin "CCW"** y **sin repetir el valor del Jacobiano** (lo muestra la barra — se evita la redundancia barra↔mensaje). También pinta el elemento entero rojo en el X-ray. El banner se ubica **debajo de la barra del Jacobiano** (`pack(after=self._bar_jac)`) porque es sobre esa métrica. **El overlay hace UN solo `refit_overlay` al aparecer/desaparecer el banner** (`_update_warning` con guard `_warning_shown`): sin refit el banner empujaba y recortaba el cross-ref inferior (el Toplevel borderless no crece solo); el refit dispara SOLO en la transición de visibilidad. **No reintroducir el `refit` diferido (`after(50)`)**: encolaba resizes al cambiar de elemento y producía parpadeo (`refit()` ya hace `update_idletasks` antes de medir, basta uno). **Banner de Compacidad (complementario, mutuamente excluyente con el del Jacobiano)**: cuando el elemento es VÁLIDO (`SJ > 0`) pero `Stretch < 0,25` (inadmisible Verdict) — caso que el Jacobiano NO detecta, p.ej. un rectángulo 1×10 con `SJ = 1` —, aparece un banner **ámbar** (`HEALTH_WARNING_COLOR`, no rojo: es usable) debajo de la barra de Compacidad: *"⚠ Mal proporcionado — muy alargado o aplastado: es válido, pero degrada la precisión"* (`_CMP_LOW_MSG`, sin el valor de Stretch). **Prioridad por severidad para NO intersectarse**: si `SJ ≤ 0` se muestra SOLO el banner del Jacobiano (la validez se arregla primero; evita doble-marcar un degenerado, que dispararía ambos). Ambos banners se gestionan con el helper `_set_banner(label, flag, msg, after_widget)` (pack/forget bajo su barra + flag de transición, sin refit interno); el caller hace **UN solo `refit_overlay` combinado** (dos separados parpadearían). **No reintroducir** dos banners simultáneos, un refit por banner, ni el ex-`_update_warning` (reemplazado por `_set_banner`). **No reintroducir el coloreado bipolar gris-centro** (rojo→gris→verde con el `0` al medio): el `docs/mesh_quality_normalized_metrics.tex` lo desaconseja (hacía ilegible la frontera de validez). El rango `[-1, 1]` SÍ es el correcto — es el rango completo de Verdict para el Scaled Jacobian —, pero coloreado **por umbrales**, no por gris-centro. (Histórico: se probó `[0,1]` con `Q_SJ = max(0, SJ)` y se revirtió a pedido del usuario — el rango literal de la bibliografía es `[-1, 1]`.) **No reintroducir un umbral único compartido entre las dos métricas** (los cortes aceptables son distintos por la bibliografía). **Anotaciones geométricas sobre el canvas** (reemplazan los ex-expanders LaTeX "Ver derivación paso a paso", que duplicaban teoría del Theory Hub y mostraban números sin referente visual): para el elemento bajo cursor, `draw_canvas_layer` dibuja el **arco del peor ángulo** (mayor `|θ-90°|`) + etiqueta `θ`, la **arista Lmín** (sólida) y la **diagonal Dmáx** (punteada) con sus longitudes, usando coords distorsionadas (se mueven en vivo con el drag). Colores `EDU_M0_ANGLE_COLOR` / `EDU_M0_LENGTH_COLOR` (settings; fuera de la paleta de salud para no camuflarse sobre el relleno). El paso a paso simbólico completo vive en la Memoria de Cálculo y la teoría general en el Theory Hub (`_m0_mesh_quality`, alineado a estas 2 métricas) — M0 no lo repite. **X-ray con celdas de relleno tintado semitransparente** (`lerp_hex(color_calidad, CANVAS_BG_COLOR, t)` con `t=0,58` no-mostrado / `0,36` mostrado, + `stipple="gray50"`) **+ borde nítido del color de calidad puro**: el `gray50` deja asomar la malla fantasma entre el tinte (`gray75` más denso tapaba algunas líneas del fantasma), manteniendo el look de mapa de calor; el borde es la geometría distorsionada, así el drag nunca "pierde" las aristas. **Los nodos corner sí se dibujan en la capa** (`draw_canvas_layer`, color `CANVAS_NODE_COLOR`, en su posición DISTORSIONADA, deduplicados) — son los nodos "reales" interactivos sobre el fantasma (la base los atenúa); solo corners (`node_ids[:4]`, los mid/center Q9 no se mueven). El elemento mostrado destaca por tinte más saturado + borde más grueso (`2,4` vs `1,4`) + sus anotaciones — **sin** contorno blanco extra (se eliminó `OVERLAY_TITLE_FG` de M0). **No reintroducir** el relleno punteado denso/sucio ni el relleno 100% sólido (tapaba el fantasma). Mientras M0 está activo, **toda la malla base entra en modo fantasma** (`MeshCanvas.ghost_geometry = True`): elementos, nodos, **cargas, restricciones y cargas superficiales** se dibujan en `CANVAS_GHOST_COLOR` gris tenue, sin etiquetas, sin sombras/glow y con símbolos huecos (`_draw_elements`/`_draw_nodes`/`_draw_loads`/`_draw_constraints`/`_draw_surface_loads` lo respetan; la selección sigue resaltada en amarillo). Así el X-ray de calidad es la geometría protagonista y no se confunde con la malla original al arrastrar; `on_activated` lo activa y `on_closed` lo restaura. El flag es genérico del `MeshCanvas` (reutilizable por otros overlays). **No reintroducir** el render de la malla base a color normal bajo M0. **Hint de uso persistente**: un label muted bajo el header — **"✎ Arrastrá un nodo para distorsionar — no modifica tu malla"** — instrucción + tranquilidad en una línea (no se restablece, no genera ruido). **NO hay botón Reset** (eliminado a pedido del usuario): la distorsión se deshace arrastrando el nodo de vuelta o reabriendo el módulo (la distorsión es estado de instancia, se descarta al cerrar el overlay). La descripción del módulo en `MODULE_META['mod00']` es **"Jacobiano escalado · Compacidad (Stretch)"** (antes decía "aspect ratio · Robinson", métricas viejas). **No reintroducir** el botón Reset ni el aviso contextual atado a él. **Drag fluido**: el `<B1-Motion>` refresca SOLO la capa `edu_m0` vía `_refresh_layer_only()` (no `redraw()` completo, que hace `canvas.delete('all')` + raster de toda la malla por frame); `redraw()` completo solo al soltar (resincroniza + borra el anillo de drag). El drag opera **solo sobre vértices macro** (`node_ids[:4]`) — agarrar un mid/centroide Q9 daría drag "muerto" (las métricas usan `coords[:4]`). Widget de la barra: [education/components/quality_bar.py](education/components/quality_bar.py) `QualityBar` (tk.Canvas, gradiente nativo + ticks + badge; conserva el modo `bipolar` como capacidad general aunque M0 ya no lo use). **No reintroducir** el radar de 4 ejes, el histograma, la diferenciación Q4/Q9 en métricas, los expanders de derivación LaTeX (`Expander`/`LatexExpressionImage`) ni `self._last_derivation` en M0. Helper `fmt_es(value, digits)` formatea con coma decimal española — exportado por `quality_bar`.

**Refactor 2026-05: M1 ahora compara Nᵢ(ξ,η) vs Nᵢ(x,y)** — el panel inferior derecho que mostraba det J(ξ,η) ahora muestra la MISMA Nᵢ pulled-back al espacio físico vía `iso_inverse_map`. El alumno ve la función "retorcida" sobre el elemento real al lado de su versión limpia tensor-product en el cuadrado natural. det J vive en M2 dedicado para no duplicar.

**Refactor 2026-05: M7 migra de Toplevel a Overlay con vuelo desde el canvas** — antes, el "vuelo Bézier" de cada kₑ ocurría en figure-coords de matplotlib entre dos paneles decorativos (malla réplica + K). Ahora la malla real del MeshCanvas es el origen del vuelo: el kₑ despega del centroide REAL del elemento (con sus BCs, sus materiales, su posición exacta), arquea como Bézier cuadrática sobre el canvas, y sale por el borde más cercano al panel flotante donde crece K. Las trazas residuales se acumulan SOBRE el modelo — el "mapa de vuelos" es geometría del proyecto, no un esquema desconectado. Además, click sobre un elemento del canvas lo manda al frente de la cola (UX agentiva: el alumno elige el orden, demostrando que K final no depende de él). Implementación: tags `edu_m7_*` para la capa overlay (limpiada por `mesh.canvas.delete(_TAG_BASE)` en cada `draw_canvas_layer`); el tile volador es un par `create_rectangle` + `create_text` animado con `coords()`, fuera de la capa (los redraws globales no lo borran). Fade de trazas por interpolación HEX (`_fade_color`) ya que `tk.Canvas` no soporta alpha. El pulso de aterrizaje en K es un `mpatches.Rectangle` matplotlib que decae alpha 0.95→0 en 10 frames.

#### Vistas avanzadas del Post (consolidación de M7 + M8)

Las funcionalidades de los ex-módulos M7 (3D del campo + slider Crudo↔Suavizado) y M8 (cruces σ₁/σ₂ + círculo de Mohr) viven ahora en el flujo nativo del Post-Proceso, accesibles desde la toolbar de Visualización:

| Vista | Activación | Archivo |
|---|---|---|
| **🧊 Vista 3D del campo** | Botón en toolbar Post → Toplevel flotante (no-modal) con `matplotlib.mplot3d.plot_surface`. Slider Crudo↔Suavizado morphea `(1-t)·Z_raw + t·Z_smooth` (Z_raw via `compute_raw_grid`, Z_smooth via Σ Nᵢ·σᵢ̄). Detector de discontinuidades: aristas con varianza > 10% del rango en rojo grueso cuando t→crudo. Sincronizado con `post_tab.result_var`: cambiar VM↔σx repinta el 3D. | [gui/postprocessing/surface_3d_viewer.py](gui/postprocessing/surface_3d_viewer.py) |
| **Toggle `Cruces principales σ₁/σ₂`** | Checkbutton en toolbar Post → capa overlay sobre el canvas (NO Toplevel). Una cruz por elemento en el centroide (NO por nodo, que satura). σ₁ azul tracción / σ₂ rojo compresión. Grosor de brazo ∝ \|σᵢ\| / max\|σ\|. Sin rotación interactiva — el campo principal del solver no se rota arbitrariamente (decisión: la rotación drag-todo de M8 era visualmente impresionante pero pedagógicamente confusa). | [gui/postprocessing/principal_cross_layer.py](gui/postprocessing/principal_cross_layer.py) |
| **Panel "Detalles" del probe + Mohr inset** | Clic derecho sobre cualquier punto del probe → Toplevel borderless `DetailsPanel` con 10 valores numéricos a la izq + círculo de Mohr animado a la der (matplotlib embebido via `FigureCanvasTkAgg`). σ₁/σ₂ marcados sobre el eje σ; (σx, τxy) sobre el círculo; θₚ en el título. Reemplaza al `ProbeTooltip` text-only del modo `details`. | [gui/postprocessing/details_panel.py](gui/postprocessing/details_panel.py) |

**Razón pedagógica de la consolidación**:
- El **círculo de Mohr** describe el estado de tensión en UN PUNTO material — ponerlo en el panel Detalles del punto consultado refuerza esa naturaleza puntual. M8 lo tenía como módulo separado donde el alumno tenía que "imaginarse qué nodo está rotando".
- Las **cruces principales** son una propiedad del CAMPO σ(x,y), análoga al contorno de VM — pertenecen al canvas como otra capa, no como módulo aparte.
- La **vista 3D** es una representación alternativa del MISMO campo del contorno 2D — como botón de toolbar queda claro que es "el mismo dato visto diferente", no contenido nuevo.

**Reusos numéricos**:
- `Surface3DViewer` reusa `compute_raw_grid` y `compute_smooth` de [fem/probe_query.py](fem/probe_query.py) — un único pipeline para probe + 3D.
- `PrincipalCrossLayer` reusa `principal_and_vm` de [fem/probe_query.py](fem/probe_query.py) — sin duplicar.
- `DetailsPanel._draw_mohr` reusa `ProbeOverlay._gather_full_values` para los valores numéricos.

**Cleanup**: `main_window._on_tab_changed` al salir de Post llama `post_tab.deactivate_advanced_views()` → desactiva la capa de cruces y cierra el Toplevel 3D + DetailsPanel. `post_tab.refresh()` ante `is_solved=False` (geometría cambió) hace lo mismo y resetea el toggle del checkbutton.

**No reintroducir**:
- `mod07_stress_discontinuity.py` ni `mod08_principal_stresses.py` (borrados).
- La rotación global drag de las cruces (decisión documentada: ν).
- Toplevel separados para 3D / Mohr — todo vive en el Post nativo.

#### Convenciones del modo Toplevel

**Flag `NO_SIDEBAR = True`** en `BaseEducationalModule`: omite el sidebar de 280 px → la visualización ocupa todo el ancho. Activado en todos los Toplevels rediseñados. Los controles esenciales (chips, sliders) se ponen DENTRO de `build_visualization` como toolbar arriba o slider gigante en el footer. `build_controls` no se invoca cuando `NO_SIDEBAR = True`.

Subclases Toplevel siguen el contrato existente de [BaseEducationalModule](education/base_module.py): `build_visualization`, `build_theory` (opcional). En modo `NO_SIDEBAR`, `build_controls` queda obsoleto.

#### Filosofía minimalista de módulos educativos (UX 2026)

**Principio rector**: la visualización dinámica debe explicarse sola. Los textos auxiliares son anclas de 1 línea, no explicaciones. Si la gráfica/animación no comunica el concepto, mejorar la gráfica, NO agregar texto. Reglas no negociables que el código sigue y NO deben revertirse:

| Elemento | Regla | Razón |
|---|---|---|
| Botón **Cerrar** en header | **Eliminado** del header del `BaseEducationalModule`. La X nativa del Toplevel (esquina superior derecha del WM) ya cierra. Doble cierre = ruido. | Redundancia con OS. |
| Botón **? / Teoría** en header | **Eliminado** del header. La teoría vive en **Ayuda ▸ Teoría FEM** ([gui/dialogs/theory_hub_dialog.py](gui/dialogs/theory_hub_dialog.py)), accesible desde cualquier parte del flujo (no solo cuando un módulo está abierto). | La teoría es transversal a los módulos. |
| Botón **↻ Reset** | **Conservado** en el header, pero solo como icono de 3 chars `↻`. Algunos módulos lo ocultan dinámicamente cuando no hay nada que resetear (M0: visible-on-demand cuando hay distorsión activa). | Acción útil que no afecta visualización. |
| **Badge** Q4/Q9 + TP/DP + material | **`SHOW_PROJECT_BADGE = False`** por defecto en todas las familias (Geometry/Process/PostModule). El usuario definió esto, mostrárselo en cada toplevel es ruido. Los flags se mantienen por compat pero ningún módulo activo los enciende. | El alumno ya conoce su propio modelo. |
| Labels de **E, ν, ρ, t, material name** | **Eliminados** de los headers/chips/captions. El módulo los usa internamente (`_resolve_material`) pero NO los muestra. | El alumno definió esos valores en Modelo ▸ Materiales. |
| **Combobox de elemento** dentro del módulo | **Eliminado**. El elemento bajo análisis se pasa via `__init__(..., element_id)` desde el launcher. Para analizar otro, el alumno lo selecciona en el canvas y reabre el módulo (el panel de módulos muestra chip `#N` con el elemento activo). | Una sola vía de selección de elemento — el canvas. Sin duplicar UX. |
| **Combobox de Nᵢ** (M1) | **Eliminado**. El alumno clickea sobre cualquier nodo visible en los paneles 2D para seleccionar qué función de forma ver, y el marcador se ancla en ese nodo. Gesto único: "ver esta Nᵢ + marcador aquí". | Self-evident por la interacción canvas. |
| Hints textuales **"Click aquí para…"** | **Eliminados** cuando el feedback visual (puntos pulsantes, glow, marcador, color por estado) ya invita al gesto. Cada label cuesta una línea de espacio vertical y compite con la viz. | La invitación está en la animación. |
| Captions de **metadata** (caso plano, dimensiones, E, ν) bajo gráficos | **Eliminadas**. Si la fórmula sobre el gráfico ya dice qué es, repetir los valores numéricos es ruido. | La fórmula + valores de la matriz ya muestran el resultado. |
| **Padding** entre paneles | Bajado a `(2, 2)` para `viz_frame` y `(6, 2)` para header/footer. Sin `pady=(2, 8)` generosos. | Aire al contenido, no al chrome. |
| **Separadores** (`ttk.Separator`) entre secciones del overlay | Reducidos. Si dos widgets relacionados no necesitan separador, no lo agregamos. M3, M4, M6 quedaron sin separators internos. | El espacio en blanco + jerarquía tipográfica separan visualmente. |
| **Footer** del Toplevel | Se crea SOLO si `HAS_ANIMATION=True`. Antes se creaba siempre con un `ttk.Label("")` que ocupaba ~22 px de espacio muerto. | Aire para la viz. |

**Convenciones positivas**:
- **Status label**: si hace falta info contextual (qué punto Gauss está activo, ξ, η), una sola línea Consolas 9 sin caption ni subtítulo.
- **Warnings condicionales**: solo aparecen cuando aplica (det J ≤ 0 en M2, ν → 0.5 en DP en M3, 1×1 hourglass en M5). Cuando todo está bien, vacíos — sin ocupar espacio visual.
- **Toggles segmentados** (Fórmula/Valores, Arista/Gravedad): solo 2 valores mutuamente excluyentes, sin label "Modo:" arriba.

**Cómo añadir un módulo nuevo respetando esta filosofía**:
1. Empezá con el body vacío. Solo la gráfica/canvas.
2. Si la gráfica no comunica el concepto solo, mejorá la gráfica antes que agregar texto.
3. Si necesitás un input del usuario (param de carga, orden de cuadratura), poné el control SIN label si su valor visible ya lo identifica (p.ej. radio "2×2" no necesita label "Cuadratura:" si están agrupados).
4. Status info en 1 línea Consolas 9 cuando el contexto cambia mucho (M2 con ξ/η variable, M4 con índice Gauss).
5. **Nunca** badge de Q4/Q9, material, E, ν, ρ, t. **Nunca** combobox de elemento. **Nunca** botón Cerrar propio. **Nunca** botón `?` propio.

Si alguna vez se reintroduce algo de esta lista, documentar el motivo y la mejora pedagógica concreta — sino, está mal hecho.

Componentes VIVOS en [education/components/](education/components/): `LatexMatrixImage` / `LatexExpressionImage` / `ScrollableMatrixImage` / `render_matrix_image` / `render_expression_image` ([latex_image.py](education/components/latex_image.py)), `FormulaValueBlocksToggle`, `GaussCoordReadout` ([gauss_inset.py](education/components/gauss_inset.py)), `gauss_glyph` (glifo de PG + `lerp_hex`/`hex_to_rgb`/`draw_gauss_free_point`), `iso_inverse_map` / `natural_to_physical` / `element_coords` ([iso_inverse.py](education/components/iso_inverse.py)), `Expander`, `QualityBar` / `fmt_es`, `apply_edu_style_*` / `_theme_colors` ([edu_plot_style.py](education/components/edu_plot_style.py)), `LatexStatusLabel`, `TheoryDoc` / `TheoryViewer`. **Eliminados en la limpieza 2026-05** (eran código muerto): `LatexMath` (latex_math.py), `render_matrix_latex`/`render_expression_latex` (latex_figure.py), `LatexBlock` (latex_block.py), `FormulaValueToggle` (formula_value_toggle.py), `PlotPanel`/`FourPanel` (plot_panel.py/four_panel.py — `_theme_colors` migró a edu_plot_style), `ParamInput`, `StepAnimator`, y `education/latex_warmup.py`. **No duplicar `fem/`** — los módulos solo visualizan.

**Convenciones módulos educativos**:
- **LaTeX matrices**: usar el widget `LatexMatrixImage` (o `render_matrix_image`) de [latex_image.py](education/components/latex_image.py) — render como PhotoImage via packer matplotlib-nativo (`\substack` por columna + corchetes `\left[\right]`), con backend dual pdflatex/mathtext. Para matrices anchas (Q9) que se cortan, `ScrollableMatrixImage` (scroll/pan in-frame) + `render_matrix_image(..., shrink=False)`. Acepta cells `str` (símbolos), `float`, o `sympy`. matplotlib mathtext **NO soporta `\begin{bmatrix}`** — **no reintroducir** en strings de mathtext.
- **LaTeX expresiones escalares** (fracciones, integrales, sumatorias): `LatexExpressionImage` / `render_expression_image` con mathtext. Funciona bien para todo *excepto* matrices.
- **Subíndices Unicode**: usar sufijos ASCII (`N1x`, `N1y`) en lugar de subíndices Unicode tipográficos (`ᵧ` = U+1D67) — algunos no están en `DejaVu Sans Mono` y disparan warnings de glifo faltante.
- **Video / animación**: WebP animado vía [WebpPlayer](gui/widgets/webp_player.py) o [VideoPlayer](education/components/video_player.py). Assets en [resources/videos/](resources/videos/) con extensión `.webp`. Degradar a mensaje si falta. **No usar** `tkvideoplayer`/`av`.
- `SymbolicIntegrandQ4` vive en [mod05_stiffness.py](education/mod05_stiffness.py) (importada por [file_io/memoria_calculo.py](file_io/memoria_calculo.py)); mover a `fem/` si se reusa. **No existe** `SymbolicIntegrandQ9` (en Q9 el integrando simbólico se omite — mathtext no escala a B 3×18).
- **Coords nodales**: usar el helper compartido `element_coords(project, element)` de [iso_inverse.py](education/components/iso_inverse.py) — **no** reimplementar la extracción `np.array([[nodes[nid].x, .y] for nid in element.node_ids])` (antes duplicada en M1/M2/M4/M5).
- **Interpolación de color HEX**: usar `lerp_hex` / `hex_to_rgb` de [gauss_glyph.py](education/components/gauss_glyph.py) — fuente única (antes triplicada).
- Soporte Q9: usar `get_shape_functions(project.element_type)` y `elem.num_nodes`/`elem.node_ids` (no `range(4)`). Métricas de contorno macro: `[:4]` con comentario explícito.
- **Sandbox modules (M9 y similares)**: `deepcopy(self.project)` + `file_path = None`. Nunca mutar el original.

### Otros archivos importantes

- [config/settings.py](config/settings.py): magic strings, colores, tolerancias, fonts, decimales. **Importar desde aquí, no hardcodear**.
- [config/units.py](config/units.py): 8 sistemas predefinidos (SI ×4 + Imperial ×2 + Técnico kgf/tonf ×2) + factores `_LENGTH_TO_M / _FORCE_TO_N / _STRESS_TO_PA` para conversión real.
- [gui/widgets/](gui/widgets/): `ToolTip`, `phase_banner.build_phase_banner`, `module_launcher_panel.render_module_buttons`.
- [file_io/](file_io/): CSV ([csv_io.py](file_io/csv_io.py) con columnas dinámicas Q4/Q9), PDF (reportlab/PyMuPDF/pylatex), JSON proyecto, ZIP modelo, DXF (ver sección dedicada).
- [tests/example_data.py](tests/example_data.py): canónico (E=225000, ν=0.2, t=0.8, P=1000). `load_example_project(P)` Q4 9-nodos, `load_example_project_q9(P)` 25-nodos.

### Memoria de Cálculo — tres estilos + auto-detect de paso-a-paso (reformulada 2026-05)

`generate_memoria_calculo(..., style='educativo')` acepta tres valores. El default es `'educativo'`. Ver [file_io/memoria_calculo.py](file_io/memoria_calculo.py) (`MemoriaCalculo.STYLES = ("educativo", "completo", "directo")`).

| Estilo | Descripción | Cuándo usarlo |
|---|---|---|
| `'educativo'` | **Default.** Pipeline MEF completo con narrativa **textbook autocontenida** (teoría general de Zienkiewicz / Hughes / Bathe / Cook, SIN referencias a internals del software) + figuras de campo y cajas "¿por qué?". El capítulo de formulación elemental aplica auto-detect (compacto vs showcase). **Sin apéndices de volcado.** | Alumno que estudia el procedimiento; imprime el PDF para repasar. |
| `'completo'` | El documento `educativo` **+ apéndices**: A) las kₑ de los elementos NO desarrollados en el cuerpo principal, B) tensiones por punto de Gauss + vector u completo, C) glosario. | Documentación de archivo, revisión docente. |
| `'directo'` | Solo tablas de datos, matrices (D, kₑ, K, F, u, R) y contornos. Sin párrafos narrativos, sin intro, sin cajas `tcolorbox`. | Usuario que ya conoce MEF y solo necesita verificar valores. |

**Capítulos (educativo/completo)**: ① Planteo (hipótesis TP/DP + D, una sola vez) → ② Discretización → ③ Calidad de malla → ④ Formulación elemental (auto-detect compacto / showcase, ver abajo) → ⑤ Ensamblaje → ⑥ Condiciones de contorno y solución (fusionados) → ⑦ Post-proceso. BCs y solución están **fusionados** en un capítulo para no repetir la explicación.

**Teoría general, NO software-specific**: la narrativa sigue la formulación clásica del MEF (forma débil, isoparamétrico, Gauss-Legendre, factorización directa, extrapolación, promediado) sin mencionar librerías, factorizaciones específicas, ni nombres de funciones internas. Si vas a tocar el contenido textual de la memoria:
- **No** mencionar `scipy.sparse.linalg.spsolve`, `SuperLU`, `UMFPACK`, JIT, `node_index_map`, CSR/COO, `_K_to_dense`, ni rutas `fem/...`. La memoria es un documento que el alumno lee como cualquier texto de MEF: el solver es "factorización LU directa" en abstracto, las extrapolaciones son "la inversa de la matriz de funciones de forma evaluadas en los puntos de Gauss" sin decir dónde está cacheada, etc.
- **Sí** se conservan los hechos teóricos: simetría y definida-positividad de K_ff tras BCs, superconvergencia de Barlow, locking volumétrico en DP, hourglass en sub-integración. Esos son contenido didáctico, no detalles de implementación.
- La regla de oro: si la afirmación es útil para entender el MEF, va. Si solo describe **cómo está hecho el software**, no va.

**Auto-detect del capítulo de formulación elemental** (introducido 2026-05): el documento elige entre dos modos según el tamaño del modelo:

| Modo | Aplica cuando | Qué genera |
|---|---|---|
| **Compacto** (paso-a-paso completo) | Q4 con ≤ `_COMPACT_MAX_ELEMENTS_Q4 = 2` elementos, o Q9 con ≤ `_COMPACT_MAX_ELEMENTS_Q9 = 1` elemento | Un capítulo "Formulación elemental" con una `\subsection{Elemento N}` por cada elemento del modelo; cada uno desarrolla N → J → B → D → integrando → kₑ con `\paragraph{...}` para los pasos. La caja "¿por qué Gauss?" aparece solo en el primer elemento (no se repite). |
| **Showcase** (un solo elemento + nota) | Por encima de esos umbrales | Un capítulo "Formulación elemental — Elemento X" donde X es el elemento de **máxima energía de deformación** $U_e=\tfrac{1}{2}u_e^T k_e u_e$. Caja `educational_box` prominente que aclara: \"el modelo tiene N elementos; el procedimiento es exactamente el mismo para los demás, cambian solo las coordenadas nodales\". |

El despacho lo hace `_compact_showcase_ids()` (devuelve lista o `None`) y `_build_narrativo` ramifica a `_build_cap_showcase_compact(ids)` o `_build_cap_showcase(elem_id)`. Ambas funciones llaman al mismo helper `_develop_element_content(elem_id, *, use_subsections, show_motivation_box)` que produce el desarrollo paso-a-paso. **Si añadís un caso límite** (p. ej. permitir Q4 con 3 elementos cuando la malla es muy regular), elevá `_COMPACT_MAX_ELEMENTS_Q4` y documentá el motivo aquí.

**Apéndice A** (estilo `completo`): lista las kₑ de los elementos que NO se desarrollaron en el cuerpo principal. En modo compacto eso significa que el apéndice puede quedar vacío (todas las kₑ ya están en el capítulo principal), y la memoria muestra un mensaje al alumno. La firma `_build_appendix_a_kes(showcase_id, compact_ids)` recibe ambos para evitar duplicar.

**Razón de los umbrales**: en Q4, kₑ es 8×8 y K crece como 2·N_nodos × 2·N_nodos; con 2 elementos (6 nodos, 12 GDL) K es 12×12 y cabe portrait. En Q9, kₑ ya es 18×18 (un solo elemento llena una hoja apaisada); con 2 Q9 los 15 nodos dan 30 GDL en K, que satura. No subir los límites sin re-validar el render con `_mostrar_matriz_ke` y `_mostrar_matriz_K` (umbrales internos: literal portrait ≤ 12 GDL, apaisado 13–24, sparsity Pillow por encima).

**Figuras de campo = Pillow estilo canvas, NO matplotlib** ([file_io/figure_export.py](file_io/figure_export.py)). Ver sección dedicada abajo.

**Formateo numérico**: los positivos en celdas de matrices/vectores **NO** llevan prefijo `+` (solo el `-` de negativos). La alineación la da el entorno `bmatrix`. El helper es [education/components/theory_builder.py](education/components/theory_builder.py) (`matrix_tex`, `matrix_factored_tex`, `vector_factored_tex` usan `{:.Ng}`/`{:.Nf}`/`{:.Ne}`, sin `+`). **No reintroducir** `{:+...}` en celdas de matrices/vectores.

**Flujo UX**: antes del `filedialog.asksaveasfilename`, se abre `MemoriaStyleDialog` (3 radios, default `educativo`). Cancelar aborta sin abrir el selector. El estilo se pasa como `style=style`.

**Ya NO aplica** el invariante histórico "`style=completo` produce un PDF bit-a-bit idéntico" — el documento fue reformulado por completo. El flag `_cross_refs_enabled` fue eliminado (no hay referencias cruzadas circulares).

**`SymbolicIntegrandQ4`** sigue importándose desde [education/mod05_stiffness.py](education/mod05_stiffness.py) en el desarrollo paso-a-paso Q4 (motivación "por qué Gauss"). No mover sin actualizar ese import.

**Theory Hub** ([gui/dialogs/theory_hub_dialog.py](gui/dialogs/theory_hub_dialog.py)): documento teórico unificado accesible desde Ayuda. Sigue la misma filosofía textbook que la memoria — teoría general de los textos clásicos, NO menciones de internals del software. **No** reintroducir `scipy.sparse.linalg.spsolve`, `texttt{Element.get\_dof\_indices}`, ni rutas `fem/...` en sus secciones.

**No añadir** un cuarto estilo sin documentarlo aquí y en `MemoriaCalculo.STYLES`.

### Render de figuras de la Memoria — Pillow estilo canvas ([file_io/figure_export.py](file_io/figure_export.py))

Reformulado 2026-05: **figure_export NO importa matplotlib**. Las figuras de campo se dibujan con **Pillow**, replicando la técnica del MeshCanvas del Post-Proceso (gradiente bilineal Gouraud por elemento vía rasterizado baricéntrico de triángulos + wireframe), pero con **FONDO BLANCO** (el PDF se imprime). Razón: las gráficas matplotlib se veían pobres frente al canvas tkinter+Pillow.

Funciones (todas devuelven `PIL.Image` o `None`): `render_mesh_diagram` (geometría + nodos por rol Q9 + símbolos de restricción + flechas de carga), `render_contour` (Gouraud + wireframe + colorbar), `render_deformed` (malla gris + deformada verde), `render_principal_crosses` (cruces σ₁/σ₂ azul/rojo), `render_K_sparsity` (patrón de no-nulos, reemplaza al ex-heatmap matplotlib).

**Colormaps**: LUTs internas de `viridis` (secuencial → σVM, no negativo) y `coolwarm` (divergente → σx/σy/τxy, cero físico). **No `jet`** (a diferencia del canvas interactivo, que usa jet; en la memoria mantenemos los científicos perceptualmente uniformes por coherencia con CLAUDE.md y con el resto de los plots educativos). Acentos (nodos, restricciones, cargas, principales) desde la paleta semántica de `config/settings.py` (mismos códigos visuales que el canvas).

**matplotlib sigue siendo dependencia del proyecto** (lo usan los módulos educativos en `education/` y las vistas avanzadas del Post) — pero `file_io/figure_export.py` ya no lo importa. Las funciones de diagrama esquemático matplotlib (ex `render_fem_pipeline`, `render_lm_mapping`, `render_extrapolation_diagram`, `render_averaging_diagram`, `render_mohr_circle`, `render_K_heatmap`) fueron **eliminadas** — eran ilustraciones genéricas de libro o redundantes con el Hub/los módulos interactivos; el contenido se conserva en fórmulas y tablas. **No reintroducir** figuras matplotlib en `figure_export.py`.

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
