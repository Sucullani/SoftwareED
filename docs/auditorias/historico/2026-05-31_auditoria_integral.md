# Auditoría Integral del Proyecto EduFEM — 2026-05-31

> Auditoría exhaustiva (estructura, calidad, dependencias, recursos, rendimiento, seguridad, consistencia, mantenibilidad).
> Metodología: 17 agentes de análisis (11 por subsistema + 6 transversales repo-wide) + 23 verificaciones adversariales independientes (grep/diff/lectura). Cada hallazgo se basa en evidencia citada; los de mayor severidad fueron re-verificados intentando refutarlos.

---

## 1. Resumen ejecutivo

EduFEM es un proyecto **maduro y de buena calidad de fondo**, especialmente en su núcleo: el motor `fem/` es NumPy/SciPy puro (pureza verificada: cero `tk`/`matplotlib`, cero `eval`/`exec`/`pickle`/`subprocess`, cero hex literales, tolerancias centralizadas), con kernels `@njit`, ensamblaje sparse y cachés bien diseñados; la capa `models/` es cohesiva; la postura de **seguridad es sólida** para una app de escritorio (sin secretos, JSON en vez de pickle, `pdflatex` sin `shell=True` ni `-shell-escape`, escape LaTeX de inputs de usuario). El árbol de **dependencias está limpio**: las 9 deps de runtime se usan, no hay fantasmas ni faltantes.

La deuda se concentra en cuatro frentes:

| Frente | Síntesis |
|---|---|
| **1 bug crítico** | La caché `node_index_map` no se invalida al borrar nodos (3 caminos) → `solve` crashea o ensambla mal. Reabre la clase de bug que el proyecto creía cerrada. |
| **God objects** | `mesh_canvas.py` (4 184 LOC/128 métodos), `pre_tab.py` (2 818/96), `memoria_calculo.py` (2 612/74), `main_window.py` (1 666/66) concentran responsabilidades mezcladas. |
| **Consistencia (paleta congelada)** | ~110+ hex literales fuera de `config/settings.py` en `gui/` + `education/`, varios duplicando constantes existentes — la auditoría pre-merge que CLAUDE.md declara "0 hits" está incumplida. |
| **Higiene del repo** | ~5 MB de artefactos Manim versionados, artefactos LaTeX versionados pese a `.gitignore`, un `.webp` huérfano de 838 KB en el instalador, scripts/temporales basura, módulos muertos (`controllers/`, `config/latex_cache.py`, `gauss_inset.py`). |

### Métricas

- **122 archivos `.py`**, ~46 800 LOC (sin `.venv`). **380 archivos versionados**, `.git` ≈ 41 MB.
- **Hallazgos brutos:** 164 (17 agentes). Tras deduplicar solapes entre agentes y descartar 1 refutado → **≈ 95 hallazgos únicos**.
- **Distribución por severidad** (verificada): **1 Crítico · 16 Alto · ~38 Medio · ~105 Bajo**.
- **Verificación adversarial:** 22/23 confirmados; **1 refutado** (la "inconsistencia JET" — es un override deliberado y documentado del usuario, no un defecto); varias severidades de "código muerto" corregidas de Medio → Bajo (es inerte).

### Veredicto

Ningún problema compromete la corrección numérica del motor ni la seguridad. **El único bloqueante real es el bug crítico de `node_index_map`** (fix de pocas líneas). Lo demás es higiene, consistencia y refactor estructural — alto valor de mantenibilidad, bajo riesgo de regresión si se aborda incrementalmente.

---

## 2. Hallazgo crítico

### C-1 · La caché `node_index_map` no se invalida al borrar nodos → `solve` falla

- **Categoría:** Calidad de código / Corrección · **Severidad:** **Crítico** (confirmado end-to-end)
- **Ubicación:** [models/project.py](../../../models/project.py) — `remove_element` (~l.361), `remove_node_with_cascade` (~l.170); [models/mesh_utils.py](../../../models/mesh_utils.py) — `shrink_q9_to_q4` (~l.340)
- **Problema:** `_node_index_map_cache` solo se invalida en `add_node`, `remove_node`, `change_node_id` y `restore_from_dict`. Los **tres caminos que borran nodos directamente** (`del self.nodes[...]` en el cleanup de `remove_element`, en `remove_node_with_cascade`, y en `shrink_q9_to_q4`) **no setean `_node_index_map_cache = None`**. Verificado en vivo: tras `remove_element`, `node_index_map` devuelve entradas stale; un solve de dos Q4 adyacentes (borrar un elemento → resolver) produce `IndexError/scipy ValueError` (índice fuera de rango al construir la COO en `assembly.py:288`), o peor, un **ensamblaje silenciosamente incorrecto** si el índice stale cae en rango.
- **Impacto:** Borrar un elemento, borrar un nodo en cascada o convertir Q9→Q4 y luego resolver (cambiar a Post auto-resuelve) → crash o resultado erróneo. Reabre exactamente el bug que el patrón `node_index_map` debía cerrar (documentado en CLAUDE.md). Afecta flujos de borrado muy comunes en la GUI.
- **Solución:** Invalidar la caché tras cada eliminación de nodo. Lo más robusto: que `rebuild_node_to_elements()` (punto común que llaman expand/subdivide/shrink) **también** invalide el index map.
- **Ejemplo:**
  ```python
  # models/project.py — remove_element cleanup y remove_node_with_cascade
  del self.nodes[nid]
  self._node_to_elements.pop(nid, None)
  self._node_index_map_cache = None        # <-- FALTA

  # models/mesh_utils.py — shrink_q9_to_q4, tras el loop de orphans
  project.rebuild_node_to_elements()
  project._node_index_map_cache = None     # <-- FALTA
  ```
- **Regresión:** añadir test "borrar elemento que orfana nodos + solve" y "shrink_q9_to_q4 + solve".

---

## 3. Hallazgos importantes (Alto)

> Nota de verificación: el ex-hallazgo "el canvas usa JET contra el estándar" fue **REFUTADO**. JET es un override **deliberado, documentado y aplicado consistentemente** (pedido del usuario 2026-05-31, look ANSYS/SAP2000; CLAUDE.md y memoria del proyecto ya lo legitiman). **No es defecto.** Lo que SÍ queda como deuda es la *documentación interna desincronizada* (comentarios que aún dicen "viridis"/"turbo") y los LUT ahora muertos — ver A-7 y la sección de código muerto.

| ID | Categoría | Severidad | Ubicación | Resumen |
|---|---|---|---|---|
| A-1 | Estructura | Alto | gui↔education | **Acoplamiento bidireccional de paquetes** resuelto con imports diferidos (workaround de ciclo). |
| A-2 | Estructura | Alto | file_io/memoria_calculo.py:1396 | `file_io/` importa `SymbolicIntegrandQ4` desde un módulo overlay de `education/` que arrastra todo el stack Tk/matplotlib. |
| A-3 | Estructura | Alto | gui/main_window.py:114,857-892 | Código de producción (feature "Cargar Ejemplo") importa loaders desde `tests/`. |
| A-4 | Calidad | Alto | gui/preprocessing/mesh_canvas.py | God object: 4 184 LOC / 128 métodos; render + selección + hit-test + modo dibujo + orquestación de borrado con modales. |
| A-5 | Calidad | Alto | gui/preprocessing/pre_tab.py | God object: 2 818 LOC / 96 métodos; 5 tablas con 5 ciclos CRUD casi idénticos en una clase. |
| A-6 | Calidad | Alto | file_io/memoria_calculo.py:237 | God object: 2 612 LOC / 74 métodos; mezcla recomputación FEM + generación LaTeX + compilación. |
| A-7 | Consistencia | Alto | education/ (~71 hex) | ~71 hex literales hardcodeados en `education/` violan la paleta congelada; varios duplican constantes. |
| A-8 | Consistencia | Alto | gui/dialogs/ (~16 hex) | ~16 hex literales fuera de `config/settings.py`; varios duplican `CANVAS_NODE_COLOR`, `ORPHAN_NODE_FG`, `LABEL_FG`, `TEXT_MUTED_FG`. |
| A-9 | Duplicación | Alto→Bajo* | education/ ('#ffd54f' ×9) | `#ffd54f` repetido 9+ veces ya existe como `OVERLAY_ACCENT_AMBER`; idem `#4fa3ff`, `#90caf9`, `#ffffff`. (*Verificador: severidad real Bajo — duplicación cosmética.) |
| A-10 | Código muerto | Alto | education/components/gauss_inset.py | `GaussCoordReadout` (532 LOC) + `latex_status_label.py` (transitivo): exportados pero **nunca instanciados**. |
| A-11 | Código muerto | Alto | config/latex_cache.py | Módulo completo (374 LOC, pipeline pdflatex→PNG) **huérfano** tras migrar a mathtext. |
| A-12 | Calidad (tests) | Alto | tests/test_fem.py | El test núcleo del solver **nunca falla**: 0 `assert`, 0 `sys.exit(1)`; siempre exit 0. |
| A-13 | Calidad (tests) | Alto | tests/vv_cook.py, vv_mms.py, vv_timoshenko.py | Los 3 benchmarks de validación de tesis **no asertan tolerancia** (solo imprimen %). |
| A-14 | Archivos | Alto | tools/render_*_manim/media/ | ~5 MB / 181 archivos de artefactos Manim intermedios versionados en git. |
| A-15 | Archivos | Alto | resources/videos/cantilever_q4_q91.webp | `.webp` huérfano duplicado (838 KB), sin referencias, **empaquetado en el instalador**. |
| A-16 | Archivos | Alto | docs/mesh_quality_worked_example.{aux,fls,...} | 7 artefactos LaTeX versionados pese a estar en `.gitignore` (regenerables del `.tex`). |

### Detalle de los Alto estructurales

**A-1 · Ciclo de paquetes gui ↔ education.** `education/overlay_module.py:56` importa `gui.widgets.canvas_overlay.CanvasOverlay`; `mod09:51` importa `gui.postprocessing.result_image_renderer`; `latex_image.py:668` importa `gui.widgets.tooltip` (diferido). En sentido inverso, `gui/` importa `education.module_launcher`/`overlay_module` **todos diferidos dentro de funciones** (main_window.py:535,1314; proc_tab.py:52; pre_tab.py:350; post_tab.py:87) — huella clásica de workaround de import circular. **Solución:** invertir la dirección — `education/` no debe depender de `gui/`. Extraer los widgets neutrales (`CanvasOverlay`, `ToolTip`, `render_result_to_pil`) a una capa base (`ui_kit/` o `gui/widgets/` sin dependencias hacia arriba) y `edu_plot_style`/`TheoryViewer` a un paquete compartido. Meta: `education → {fem, models, config, ui_kit}`; `gui → {education, fem, models, config, ui_kit}`. Con eso todos los imports diferidos vuelven a top-level.

**A-2 · file_io → education (vía SymbolicIntegrandQ4).** `memoria_calculo.py:1396` hace `from education.mod05_stiffness import SymbolicIntegrandQ4`, pero `mod05_stiffness.py:38-45` importa `tkinter`, `ttkbootstrap`, `FigureCanvasTkAgg`, `CanvasOverlayModule`. La clase es **pura SymPy/NumPy**. El propio CLAUDE.md lo anticipa ("mover a `fem/` si se reusa" — y sí se reusa). **Solución:** extraer a `fem/symbolic_integrand.py` e importarla desde ambos. Esfuerzo bajo, alto valor (la generación de PDF deja de arrastrar el toolkit gráfico).

**A-3 · Producción importa de tests/.** `main_window.py` importa 7× desde `tests.example_data` (loaders de Cuadrado/Timoshenko/Cook Q4/Q9), que alimentan **Ayuda ▸ Cargar Ejemplo** — feature de producto, no fixtures. Si `tests/` no se empaqueta (PyInstaller), "Cargar Ejemplo" rompe en el `.exe`. **Solución:** mover `example_data.py` (o sus loaders) a `models/example_library.py` o `resources/examples/`; los `tests/vv_*` importan desde ahí (tests → producto es la dirección correcta). Verificar inclusión en `build.spec`.

---

## 4. Código muerto detectado (verificado repo-wide)

> Deduplicado entre agentes. Todos confirmados con grep repo-wide (excluyendo `.venv`, `__pycache__` y la def propia), atentos a dispatch dinámico/callbacks/tests.

### Módulos / directorios muertos

| Ubicación | Qué | LOC | Acción |
|---|---|---|---|
| `controllers/` | Solo `__init__.py` (21 B, comentario `# Controladores MVC`); **0 imports** repo-wide. | — | Eliminar el directorio (o materializarlo con los servicios del refactor). |
| `config/latex_cache.py` | Pipeline pdflatex→PNG + cache disco + threading + warmup; **0 importadores**. Reemplazado por mathtext (`matplotlib_config.py`). | 374 | Eliminar (arrastra el bloque `LATEX_*` de settings y la única `subprocess` de `config/`). |
| `education/components/gauss_inset.py` (`GaussCoordReadout`) | Solo en su docstring + comentarios "ex GaussCoordReadout"; **0 instanciaciones**. M2/M4/M5 migraron a matplotlib. | 532 | Eliminar + quitar re-export de `components/__init__.py:20,35`. |
| `education/components/latex_status_label.py` (`LatexStatusLabel`) | Instanciado **solo** dentro de `gauss_inset.py` → muerto transitivo. | 197 | Eliminar junto con `gauss_inset.py`. |

### Funciones / métodos / constantes muertos

| Ubicación | Símbolo | Severidad |
|---|---|---|
| fem/stress.py:159 | `_N_STRESS` (nunca usado) | Bajo |
| fem/mesh_quality.py:106-123 | `scaled_jacobian()` (Gauss) y `jacobian_ratio()` sin uso en producción (solo en `.tex`) | Bajo |
| fem/mesh_quality.py:242 | alias deprecado `robinson_stretch = edge_aspect_ratio` sin callers | Bajo |
| fem/error_norms.py:22 | imports `compute_jacobian`, `compute_dN_physical` sin uso | Bajo |
| gui/preprocessing/mesh_canvas.py:335-339 + pre_tab.py:309-323 | callbacks `on_*_select` (5) que el canvas **nunca dispara** (dead wiring) + `_select_in_tree` | Bajo |
| gui/preprocessing/mesh_canvas.py:3056-3072, 3050-3054 + pre_tab.py:2788-2802 | `highlight_load/constraint/surface_load`, `_safe_highlight_*` sin callers | Bajo |
| gui/preprocessing/mesh_canvas.py:3395-3424 | `center_on_node/center_on_element` sin callers | Bajo |
| gui/preprocessing/pre_tab.py:1612 | `_on_constraint_click` (no-op nunca bindeado) | Bajo |
| gui/preprocessing/pre_tab.py:69 | `TREE_BORDER_COLOR` sin uso | Bajo |
| gui/preprocessing/_table_helpers.py:221-258, 319-361 | `make_context_menu`, `bind_fill_down` (features eliminadas) | Bajo |
| gui/widgets/probe_tooltip.py:108-125 | rama de acento `"details"` muerta (la consume `DetailsPanel`) | Bajo |
| education/components/latex_image.py:888,40 | `place_matrix_in_axes` (~82 LOC) + `_ax_face_hex` | Bajo |
| education/components/latex_image.py:408,430,1012,1061 | 4 helpers del pipeline async retirado | Bajo |
| education/components/latex_image.py:1052 + latex_status_label.py:197 | `clear_cache()` sin callers | Bajo |
| education/components/edu_plot_style.py:147,168 | `apply_edu_style_polar`, `style_title` sin callers | Bajo |
| education/components/theory_builder.py:49,57,80 | `section()`, `subsection()`, `align()` sin callers | Bajo |
| education/components/quality_bar.py | modo `bipolar` (siempre `False`; CLAUDE.md prohíbe reintroducirlo) | Bajo |
| education/module_launcher.py:238-240 | rama Toplevel `else` inalcanzable (todas las clases son Overlay) | Bajo (documentar como defensiva) |
| education/overlay_module.py:275 | docstring de `on_node_selected` cita M8 (eliminado) | Bajo (actualizar doc) |
| config/matplotlib_config.py:166,88 | `warmup_mathtext()`, `is_configured()` sin callers | Bajo |
| config/settings.py:325-339 | bloque `LATEX_*` (5 constantes) nunca importado | Bajo |
| config/settings.py:16-18 | `ICONS_DIR`, `HELP_DIR`, `MATERIALS_DB_PATH` → rutas inexistentes, sin uso | Bajo |
| config/settings.py:356,289 | `CSV_DELIMITER`, `EDU_NATURAL_FILL_COLOR` sin uso | Bajo |
| file_io/figure_export.py:88-92 | `_VIRIDIS_ANCHORS` rama inalcanzable | Bajo |
| file_io/memoria_calculo.py:152-255 | parámetro `scope` muerto (reservado, nunca leído) | Bajo |
| tests/vv_cook.py:227-229 | `target_results` computado y nunca usado | Bajo |

**Nota:** `theory_hub_dialog.py` (996 LOC) y `MODULE_MAP`/rama defensiva del launcher **NO son código muerto** (contenido teórico legítimo / dispatch dinámico) — verificado.

---

## 5. Archivos duplicados

| Tipo | Detalle | Acción |
|---|---|---|
| **Recurso duplicado** | `resources/videos/cantilever_q4_q91.webp` (838 KB, md5 `4765c91a…`) ≠ `cantilever_q4_q9.webp` (714 KB, md5 `48d092b4…`): versión vieja con sufijo `1`, **0 referencias** en código; se empaqueta en el instalador (`build.spec:29`). | `git rm` el `_q91`. |
| **Método verbatim** | `_preview_element_cleanup` copiado letra por letra en `pre_tab.py:1395-1433` y `mesh_canvas.py:3343-3378` (el propio docstring lo admite). | Mover a `ProjectModel.preview_element_cleanup()`. |
| **Cálculo replicado** | σ₁/σ₂/R + von Mises inline en 4 kernels njit (`probe_query`, `stress`); `DetailsPanel` los reimplementa; θₚ en 3 sitios (`details_panel`, `principal_cross_layer`, `memoria_calculo`). | Helpers `_principal_vm_scalar` (njit) y `principal_angle()` en `fem/probe_query`. |
| **Ciclo de vida WebpPlayer** | `_build_video`/`_load_video`/`_show_missing_video` casi verbatim en `analysis_type_dialog.py` y `element_type_dialog.py`. | `_VideoDialogMixin` compartido. |
| **Modal de cascada** | Construcción del `messagebox` de borrado en cascada repetida en 4 sitios (`pre_tab` ×2, `mesh_canvas` ×2). | Helper `build_cascade_confirm_message()`. |
| **`_center()` / footer / captura undo** | 8 diálogos reimplementan `_center()`; footer Cancelar/Aceptar y bloque de undo repetidos. | `ModelDialogBase` ligera. |
| **Modelos V&V** | `vv_cook.build_project` y `vv_timoshenko.build_project` reconstruyen lo que `example_data` ya provee; `save_csv` ×3, `plot_deformed` ×2, `body_force` MMS ×2. | Importar loaders + `tests/_vv_common.py`. |
| **Lista de claves σ** | `_STRESS_KEYS` (módulo) re-declarada local en `stress.py:283`. | Reusar la de módulo. |

---

## 6. Dependencias

**Estado: limpio.** Las 9 deps de runtime (`numpy, scipy, sympy, matplotlib, ttkbootstrap, pylatex, PyMuPDF, Pillow, ezdxf`) se importan y usan; `PyInstaller` (dev) se usa en `build.spec`. **No hay deps declaradas-sin-uso ni terceros-importados-sin-declarar.** Reglas duras cumplidas: `matplotlib` NO se importa en `fem/` ni en `figure_export.py`; `reportlab`/`av`/`tkvideoplayer` no reaparecen; `numba` y `manim` correctamente no declarados (opcional con fallback / prerender offline).

| Hallazgo | Severidad | Acción |
|---|---|---|
| `Pillow>=10.0.0` sin cota superior (única inconsistente; resto acota por major; venv tiene 12.2.0) | Bajo | `Pillow>=10.0.0,<14`. |
| `pdflatex`/MiKTeX (binario externo, usado por la Memoria vía pylatex) no documentado en `requirements.txt` | Bajo | Bloque comentado (estilo numba) indicando la dep de sistema opcional + fallback mathtext. |
| Imports sin uso (no son deps, son symbols): `typing.Optional` (details_panel:27); `EDU_AXES_BG, EDU_FG` (formula_value_blocks:56); ver §4 | Bajo | Limpiar. |

---

## 7. Archivos eliminables / basura

| Archivo(s) | Estado git | Seguro borrar | Acción |
|---|---|---|---|
| `tools/render_q4q9_manim/media/`, `tools/render_tp_dp_manim/media/` (~5 MB, 181 archivos: 152 `.mp4` parciales, SVG, TeX) | **versionado** | Sí (regenerable de los `.py`) | `git rm -r --cached` + `.gitignore: tools/**/media/`. El `.webp` final vive en `resources/videos/`. |
| `resources/videos/cantilever_q4_q91.webp` (838 KB) | versionado | Sí (huérfano) | `git rm`. |
| `docs/mesh_quality_worked_example.{aux,fdb_latexmk,fls,log,out,synctex.gz,toc}` (252 KB) | versionado (¡pese a `.gitignore`!) | Sí (regenerable del `.tex`) | `git rm --cached`. |
| `docs/vyv/main.bcf`, `docs/vyv/main.run.xml` | versionado | Sí (biber/biblatex) | `git rm --cached` + `.gitignore: *.bcf, *.run.xml`. |
| `_m3_check.py` (585 B, script throwaway de M3) | **versionado** | Sí | `git rm` (o migrar a `tests/` si tiene valor). |
| `temp_ttkbootstrap_imports.txt` (error de FINDSTR) | untracked | Sí | `rm` + `.gitignore: temp_*`. |
| `file_io/figure_export.py.tmp.<pid>.<hash>` (escritura atómica abortada) | untracked | Sí | `rm` + `.gitignore: *.tmp.*`. |
| `compile_output*.txt`, `Example.{aux,log,out,pdf,toc}` (raíz, ~700 KB) | gitignored (local) | Sí (local) | `rm` opcional. |
| `resources/videos/README.txt` | versionado | — (corregir) | Desactualizado: menciona MP4 y `constitutive_intro.mp4` inexistentes. Actualizar a los `.webp` reales. |

**`.gitignore` recomendado (añadir):** `*.tmp`, `*.tmp.*`, `temp_*`, `tools/**/media/`, `*.bcf`, `*.run.xml`.

**Conservados a propósito** (CLAUDE.md): `tools/render_q4q9/`, `tools/render_cantilever/` (pipelines legacy de referencia). Opcional podar sus `screenshots/`/`chats/` si no aportan.

---

## 8. Problemas de arquitectura

1. **God objects** (A-4..A-6 + `main_window`): `mesh_canvas` 4 184 / `pre_tab` 2 818 / `memoria_calculo` 2 612 / `main_window` 1 666 LOC. Recomendación:
   - `mesh_canvas` → separar *render*, *SelectionController*, *hit-testing*, *DeletionService* (compartido con `pre_tab`, elimina duplicado), *modo dibujo* (mixin).
   - `pre_tab` → `SpreadsheetTableController` base parametrizado por entidad (Node/Element/Load/Constraint/Surface); `PreProcessTab` queda como coordinador.
   - `memoria_calculo` → `MemoriaDataModel` (puro fem+models, testeable sin LaTeX) + `MemoriaRenderer` (TeX) + `LatexCompiler`.
   - `main_window` → `MenuBuilder`, widgets `StatusBar`/`HealthBadge`/`Breadcrumb`, y un servicio de archivo.
2. **Ciclo gui ↔ education** (A-1): romper con una capa `ui_kit/` neutral.
3. **file_io → education** (A-2): extraer `SymbolicIntegrandQ4` a `fem/`.
4. **Producción → tests/** (A-3): mover loaders de ejemplo a producto.
5. **`controllers/` vacío**: o eliminar, o materializar con los servicios (`DeletionService`, `SolveService`) del refactor.
6. **Orquestación de solve duplicada** (`post_tab.py:474-497` ↔ `main_window.py:114-119`): extraer `solve_and_store(project) → SolutionResult`.

---

## 9. Problemas de rendimiento

> El motor `fem/` está genuinamente bien optimizado (njit, sparse, spsolve, cachés de dN). Las oportunidades están en la **capa de render** y son de impacto Medio/Bajo.
>
> **Corrección post-verificación (importante):** un agente afirmó "Numba 0.63.1 instalado en el venv" — **es falso**. Verificado en `.venv/Scripts/python.exe`: `numba` NO está instalado y `numpy` es `2.4.6` (fuera del pin `<2.0` de `requirements.txt`). Por lo tanto los kernels `@njit` **caen a no-op puro-Python** (`fem/_numba_compat.py`) en el entorno actual: la optimización JIT existe en el código pero está **latente, no activa**. Para activarla hay que reconciliar versiones (numba requiere `numpy<2.x` compatible) — decisión pendiente. Las mejoras de render de abajo aplican igual; pero el solve real corre hoy sin JIT.

| ID | Ubicación | Problema | Acción | Esfuerzo |
|---|---|---|---|---|
| P-1 | mesh_canvas.py:2435-2449 (modo dibujo) | `redraw()` global (`delete("all")` + raster de toda la malla) en **cada** `<Motion>` con punto pendiente. | Refrescar solo tag `draw_preview` / `redraw_overlays_only()`. | Medio |
| P-2 | gravity_dialog.py:147-164 | `redraw()` completo del canvas por **cada tecla** en gx/gy (solo cambia la flecha overlay). | `redraw_overlays_only()`. | Bajo |
| P-3 | result_image_renderer.py:45-88 | Rasterizador NumPy+meshgrid (allocations/triángulo) cuando ya existe `_rasterize_triangle_njit`. | Extraer el kernel njit a módulo compartido y reusar. | Bajo |
| P-4 | surface_3d_viewer.py:299-329 | `Z_smooth` se computa en doble bucle y **se descarta** en modo crudo; `N_func` por punto. | Calcular `Z_smooth` solo si `not is_raw`; precomputar `N` en grilla por `element_type`. | Bajo |
| P-5 | dxf_io.py:81-87,214 | Dedup de nodos **O(n²)** (escaneo lineal por vértice). | Dict por coord cuantizada → O(n). | Medio |
| P-6 | assembly.py:144-145 | `list(materials.values())[0]` materializa la lista por elemento sin material. | `next(iter(...))`. | Bajo |

**Por diseño (no tocar):** `figure_export.py` rasteriza con Pillow puro (sin numba) deliberadamente, por portabilidad del instalador.

---

## 10. Problemas de seguridad

> **Riesgo global: bajo** (app de escritorio local). Sin secretos, sin `eval/exec/pickle/yaml.load`, JSON para `.edufem`, `pdflatex` con arg-list (sin `shell=True`, sin `-shell-escape`), inputs de usuario escapados con `escape_latex`, ZIP leído en memoria sin `extractall` (sin Zip-Slip), DXF vía `ezdxf`.

| ID | Ubicación | Problema | Severidad | Acción |
|---|---|---|---|---|
| S-1 | file_io/model_io.py:117-183 | **CSV/Formula injection**: `mat.name`/`material_name` se escriben crudos; un nombre que empiece con `= + - @` se interpreta como fórmula al abrir el CSV en Excel/LibreOffice. | Bajo-Medio | Prefijar `'` los campos de texto que empiecen con `=+-@` al exportar. |
| S-2 | theory_viewer.py:138 | Cache de PDF en `tempfile.gettempdir()/edufem_theory/{hash}.pdf` (nombre predecible) — en %TEMP% compartido, riesgo teórico de pre-creación por otro usuario local. | Bajo | Usar `~/.edufem/theory_cache` (consistente con el resto). |
| S-3 | config/latex_cache.py:194 | Única `subprocess` de `config/` (pdflatex) — riesgo de inyección bajo (path de `shutil.which`, args fijos), pero vive en **módulo muerto**. | Bajo | Se resuelve al eliminar `latex_cache.py` (§4). |

---

## 11. Notas técnicas (corrección numérica)

- **von Mises con σ_z = 0 en deformación plana** (`probe_query.py:359-371`, `stress.py:57-61`): todas las rutas usan `vm = √(σ₁² − σ₁σ₂ + σ₂²)`, válido cuando σ_z=0 (**tensión plana**). En **deformación plana** σ_z = ν(σ_x+σ_y) ≠ 0, por lo que el von Mises "verdadero" difiere. Se aplica uniformemente sin documentarlo. **Decisión del autor:** ¿se quiere el von Mises 3D correcto en DP, o se mantiene la forma 2D documentándola? Relevante porque la herramienta soporta DP explícitamente. (Severidad Bajo, pero es una decisión pedagógica/de corrección a tomar conscientemente.)
- `error_norms.py:226-251`: `grad_u_exact_all` se crea con shape `(0,0,2,2)` y se reasigna — lógica confusa, simplificable a un solo `np.zeros((n_elem,n_gp,2,2))`.

---

## 12. Consistencia (paleta congelada y tipografía)

La regla #1 ("cero hex literales fuera de `config/settings.py`", con auditoría pre-merge "0 hits") está **incumplida de forma sistemática**:

| Área | Hex literales | Notas |
|---|---|---|
| `education/` | ~71 (13 archivos) | mod03/04/05/06/07/09; varios = `OVERLAY_ACCENT_AMBER`, `EDU_NATURAL_OUTLINE_COLOR`, `PHASE_PRE_COLOR`. Hay un `TODO(hex)` reconociendo la deuda. |
| `gui/dialogs/` | ~16 | varios = `CANVAS_NODE_COLOR`, `ORPHAN_NODE_FG`, `LABEL_FG`, `TEXT_MUTED_FG`. |
| `gui/main_window.py` + `gui/widgets/` | ~varios | status bar/breadcrumb/badge, tooltip, webp_player. |
| `gui/preprocessing/mesh_canvas.py` | ~9+ | ejes X/Y, ghost (debería usar `CANVAS_GHOST_COLOR`), colorbar. |
| `gui/postprocessing/` (surface_3d, details_panel) | ~12 | edges 3D, Mohr grid; existe `MOHR_FG`. |
| `education/components/` | ~varios (5/12 archivos) | quality_bar, expander, edu_plot_style, formula_value_blocks, theory_viewer. |

**Fonts:** 30 ocurrencias de `("Segoe UI", N)` en 8 diálogos; solo `memoria_style_dialog.py` usa `FONT_UI`/`FONT_UI_BOLD`. CLAUDE.md exige importarlas, no hardcodear.

**Doc-rot del colormap:** comentarios en `mesh_canvas.py:4,194-195`, `figure_export.py` y prosa en `memoria_calculo.py:1957` aún dicen "viridis"/"perceptualmente uniforme a diferencia de JET" mientras el código usa JET (que es lo correcto por decisión del usuario). **Alinear los comentarios al JET real**, y limpiar `VIRIDIS_LUT`/`TURBO_LUT` (ahora sin consumidor de producción; `coolwarm` sí se usa para campos con signo).

**`except Exception` pervasivo:** 141 bloques en `gui/`, 154 en `education/` (vs 0 en `fem/`), muchos `pass` silenciosos. No eliminar en masa (algunos protegen el event-loop de Tk), pero **loguear** en vez de tragar.

---

## 13. Plan de mejora priorizado

| # | Acción | Beneficio esperado | Complejidad | Prioridad | Riesgo |
|---|---|---|---|---|---|
| 1 | **Invalidar `node_index_map` en los 3 caminos de borrado de nodo** (C-1) | Elimina crash/ensamblaje erróneo en flujos de borrado comunes | Baja | **P0** | Bajo |
| 2 | Añadir asserts de tolerancia a `test_fem`, `vv_cook/mms/timoshenko`, `test_q9_q4_cycle` (A-12, A-13) | Protege el fix #1 y el motor de regresiones silenciosas | Media | **P0** | Bajo |
| 3 | Purgar basura del repo: `git rm` Manim media, artefactos LaTeX/biber, `cantilever_q4_q91.webp`, `_m3_check.py`; arreglar `.gitignore` (A-14/15/16, §7) | −~6 MB versionados, instalador más liviano, diffs limpios | Baja | **P0** | Bajo |
| 4 | Eliminar módulos muertos: `controllers/`, `config/latex_cache.py` + `LATEX_*`, `gauss_inset.py` + `latex_status_label.py` (§4) | −~1 100 LOC muertas; claridad del pipeline LaTeX | Baja | **P1** | Bajo |
| 5 | Extraer `SymbolicIntegrandQ4` → `fem/symbolic_integrand.py` (A-2) | Desacopla `file_io` del stack GUI; PDF headless-puro | Baja | **P1** | Bajo |
| 6 | Mover loaders de ejemplo `tests/example_data` → producto (A-3) | "Cargar Ejemplo" robusto en el `.exe`; capas correctas | Media | **P1** | Medio |
| 7 | Barrer hex literales → constantes de `config/settings.py` (A-7/8/9, §12); fonts → `FONT_*` | Restaura la paleta congelada y la auditoría pre-merge | Media | **P1** | Bajo |
| 8 | Limpiar funciones/constantes/imports muertos menores (§4) | −superficie de mantenimiento; menos confusión | Baja | **P1** | Bajo |
| 9 | Sincronizar docstrings/comentarios obsoletos (JET/viridis, M8, BaseEducationalModule, README videos, test docstrings) | Doc fiable; código y comentarios coherentes | Baja | **P1** | Bajo |
| 10 | Dedup: `preview_element_cleanup` → `ProjectModel`; `principal_angle`/`_principal_vm_scalar` en `fem`; `DetailsPanel` reusa `principal_and_vm` | DRY; una sola fuente de verdad numérica | Media | **P2** | Bajo |
| 11 | Optimizar render: `redraw_overlays_only` (modo dibujo + gravity), kernel njit compartido, `Z_smooth` condicional, dedup DXF O(n)→O(n) (P-1..P-6) | Menos lag en interacción; render más rápido | Media | **P2** | Bajo |
| 12 | `ModelDialogBase` + `_VideoDialogMixin` + helper de modal de cascada (§5) | Elimina duplicación entre diálogos | Media | **P2** | Bajo |
| 13 | Sanitizar CSV-injection en export; mover cache de teoría a `~/.edufem` (S-1, S-2) | Cierra los 2 vectores de seguridad reales | Baja | **P2** | Bajo |
| 14 | Decidir/documentar von Mises σ_z en deformación plana (§11) | Corrección/transparencia pedagógica en DP | Baja | **P2** | Bajo |
| 15 | Descomponer god objects: `mesh_canvas`, `pre_tab`, `memoria_calculo`, `main_window` (A-4/5/6, §8) | Testabilidad, escalabilidad, SRP | Alta | **P3** | Medio-Alto |
| 16 | Romper ciclo gui↔education con capa `ui_kit/` (A-1) | Grafo de capas limpio; imports top-level | Alta | **P3** | Medio |
| 17 | Acotar `Pillow<14`; nota de `pdflatex` en requirements (§6) | Builds reproducibles | Baja | **P3** | Bajo |

**Orden sugerido:** P0 (1-3) en una sola sesión — bajo riesgo, alto impacto, desbloquea todo. P1 (4-9) como limpieza consolidada. P2 (10-14) como mejoras DRY/perf/seguridad. P3 (15-17) como refactor estructural planificado (idealmente con tests de caracterización antes de tocar los god objects).

---

*Generado por auditoría multi-agente con verificación adversarial. Cada hallazgo es trazable a evidencia en el código citada en su ubicación.*
