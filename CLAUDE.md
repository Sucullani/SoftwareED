# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**EduFEM** — educational desktop GUI for 2D plane stress / plane strain Finite Element Analysis with Q4 and Q9 quadrilateral elements. Built with `tkinter` + `ttkbootstrap` (theme `darkly`). User-facing strings, docstrings, and comments are in **Spanish** — keep that convention when editing.

## Running

```bash
python main.py                 # launch the GUI
python -m tests.test_fem       # run the FEM engine validation against the 9-node Q4 example
pip install -r requirements.txt
```

There is no pytest/lint setup — `tests/test_fem.py` is a printout-style validation script, not a unit-test suite.

Project files use the `.edufem` extension and are plain JSON (see `ProjectModel.to_dict` / `from_dict`).

## Architecture

The app follows an MVC-ish split. The central piece is `ProjectModel` — virtually every component takes a `project` reference and mutates it.

### Data layer — [models/](models/)
`ProjectModel` ([models/project.py](models/project.py)) owns dicts of `Node`, `Element`, `Material`, `NodalLoad`/`SurfaceLoad`, `BoundaryCondition`, plus the solved state (`displacements`, `stresses`, `global_K`, `global_F`, `is_solved`). DOF numbering is implicit: node `i` (1-indexed) has DOFs `2*(i-1)` and `2*(i-1)+1` (0-indexed). Any mutation should set `is_modified = True` and `is_solved = False` — the existing setters already do this, so prefer them over touching the dicts directly.

Global analysis config also lives on the project: `analysis_type`, `element_type`, `unit_system`, `gravity` (default `9.81`) and `include_gravity` (default `False`). All five are serialized by `to_dict`/`from_dict`, so any new field needs to be added to both.

Helper [models/mesh_utils.py](models/mesh_utils.py) exposes `expand_q4_to_q9(project)`: generates the 5 missing nodes (4 edge midpoints deduped between neighbors + 1 centroid) for every Q4 element and rewrites `element.node_ids` to length 9. Idempotent, uses `TOLERANCE` from [config/settings.py](config/settings.py) for dedupe. This is the sanctioned way to let the user define only the 4 vertices and still solve as Q9 — **never duplicate nodes manually** from GUI code.

### FEM engine — [fem/](fem/)
Pure NumPy/SciPy, no GUI dependency. Pipeline:
1. `shape_functions` → `jacobian` → `b_matrix` → `constitutive` → `stiffness` (per-element `ke` via `gauss_quadrature`)
2. `assembly.assemble_global_system(project)` → global `K`, `F`, and per-element data (Gauss points, DOF indices)
3. `solver.solve_system(project)` → returns dict with `u`, `K`, `F`, `K_red`, `free_dofs`, `restrained_dofs`, `reactions`, `element_data`. BCs are applied by row/column elimination on free DOFs.
4. `stress.compute_all_stresses` → element Gauss stresses + nodal-averaged stresses + von Mises
5. `mesh_quality.evaluate_mesh_quality` → aspect ratio / Jacobian / skew metrics

Element-type-specific behavior keys off strings from `config.settings` (`ELEMENT_Q4` / `ELEMENT_Q9`); `GAUSS_POINTS` maps those to 2×2 or 3×3 integration.

### GUI — [gui/](gui/)
[gui/main_window.py](gui/main_window.py) builds a horizontal `PanedWindow`:
- **Left:** `Notebook` with three tabs — [preprocessing/pre_tab.py](gui/preprocessing/pre_tab.py), [processing/proc_tab.py](gui/processing/proc_tab.py), [postprocessing/post_tab.py](gui/postprocessing/post_tab.py).
- **Right:** a **single shared** [MeshCanvas](gui/preprocessing/mesh_canvas.py) used by all tabs. PostProcess overlays results on the same canvas rather than swapping to a different one. When the model changes, `MainWindow._update_all_project_refs()` rebinds `project` on *every* tab and on the canvas — follow this pattern if you add new project-dependent widgets.

Switching to the Post-Proceso tab auto-solves (`post_tab.auto_solve()` in `_on_tab_changed`). `_refresh_all_tabs()` + `mesh_canvas.redraw()` is the standard "data changed" broadcast. The post-tab also calls `main_window._refresh_menu_state()` after auto-solve so Exportar PDF/CSV get enabled.

#### Barra de menús, toolbar y estado (filosofía minimalista)

La barra tiene **4 menús únicamente** — "pocos e importantes" es decisión de diseño, no añadir *Editar*, *Ver* o *Análisis*:

| Menú | Contenido |
|---|---|
| 📁 **Archivo** | Nuevo / Abrir / Abrir Recientes ▸ / Cargar Ejemplo / Guardar / Guardar Como / Exportar PDF / Exportar CSV / Salir |
| 📐 **Modelo** | 🔬 Análisis y Elemento… / 📏 Unidades y Gravedad… / 🧱 Materiales… — **3 pop-ups autónomos**, cada uno resuelve una configuración completa |
| 🎓 **Educación** | M1..M6 (acceso directo, también desde `proc_tab`) |
| ❓ **Ayuda** | Manual / Atajos / Acerca de |

Los diálogos de Modelo (`AnalysisElementDialog`, `UnitsGravityDialog`, `MaterialDialog`) viven en [gui/dialogs/](gui/dialogs/) y reciben `(parent, project, main_window=None)` — deben ser invocables también desde toolbar / pre_tab sin acoplarse a la barra de menús. `MaterialDialog` se **amplía** (no se divide) con la constante `TYPICAL_MATERIALS` y un botón "📚 Importar material típico"; no crear una librería persistente separada en `resources/`.

**Toolbar** (`_build_toolbar`, debajo del menú): botones emoji `📄 📂 💾 │ 🧪 ▶ │ 📊 📑 │ 🎯 🔳`. Cada uno usa el helper `ToolTip` de [gui/widgets/tooltip.py](gui/widgets/tooltip.py).

**Título dinámico** (`_update_title`): prefijo `●` cuando `project.is_modified`, se limpia tras guardar. Llamar a `_update_title()` tras cualquier mutación que toque `is_modified`.

**Enable/disable inteligente** (`_refresh_menu_state`): las referencias a items de menú y botones de toolbar se guardan en `self._menu_items` / `self._toolbar_items` para poder habilitarlas/deshabilitarlas según `is_modified` (Guardar) e `is_solved` (Exportar PDF/CSV, Resolver). Invocar tras `_on_new_project`, `_on_open_project`, `_on_load_example`, `_on_save_project`, auto-solve, cambio de pestaña.

**Atajos de teclado** (registrados en `_bind_shortcuts`, reflejados exactamente en `_on_shortcuts`):

| Atajo | Acción |
|---|---|
| Ctrl+N / O / S / Shift+S | Nuevo / Abrir / Guardar / Guardar Como |
| Ctrl+E | Cargar Ejemplo |
| Ctrl+Q | Salir |
| Ctrl+1..6 | Abrir módulos educativos M1..M6 |
| F5 | Resolver (delega en `post_tab.auto_solve`) |
| F11 / F | Pantalla completa / Ajustar vista |
| Ctrl+Tab / Ctrl+Shift+Tab | Pestaña siguiente / anterior |
| Ctrl+/ | Ver atajos · F1 Manual |

`_is_entry_focused()` corta los atajos de una sola tecla (p. ej. `F`) cuando el foco está en un `Entry`/`Combobox`. Si añades un atajo nuevo, añádelo a la tabla y a `_on_shortcuts` — ambos deben coincidir.

**Archivos recientes**: persistencia JSON en `~/.edufem/recent.json` vía [config/recent_files.py](config/recent_files.py) (`load` / `add` / `remove` / `clear`, máx `RECENT_FILES_MAX = 10`). Invocar `recent_files.add(path)` tras guardar o abrir correctamente, y `_build_recent_menu()` para repoblar el submenu.

### Education modules — [education/](education/)
Six interactive Toplevel windows that together walk through the FEM chain `coordenadas → B → D → K → F → ensamblaje`:

| ID | Archivo | Clase | Concepto |
|----|---------|-------|----------|
| M1 | [mod01_iso_mapping.py](education/mod01_iso_mapping.py) | `IsoMappingModule` | Coordenadas naturales, Nᵢ, Jacobiano (4 paneles 2×2 con click bidireccional físico↔natural; combobox 3D / Contornos) |
| M2 | [mod02_b_matrix.py](education/mod02_b_matrix.py) | `BMatrixModule` | Matriz B con snap automático a puntos de Gauss; B numérica en LaTeX abajo |
| M3 | [mod03_constitutive.py](education/mod03_constitutive.py) | `ConstitutiveModule` | Matriz D(E,ν) en LaTeX + video Manim embebido (`resources/videos/constitutive_intro.mp4`) |
| M4 | [mod04_stiffness_gauss.py](education/mod04_stiffness_gauss.py) | `StiffnessGaussModule` | Notebook de 2 tabs: integrando simbólico (sympy→mathtext, superficie 3D de \|K_ij\|) + cuadratura de Gauss paso a paso |
| M5 | [mod05_assembly.py](education/mod05_assembly.py) | `AssemblyModule` | Ensamblaje K/F global con "flying elements" (overlay animado del kₑ cayendo en K) + overlay de BCs + sistema reducido |
| M6 | [mod06_equivalent_forces.py](education/mod06_equivalent_forces.py) | `EquivalentForcesModule` | Fuerzas equivalentes nodales; radio-button `Carga de arista` / `Peso propio` con animación de flechitas migrando a los nodos |

All subclass [BaseEducationalModule](education/base_module.py) with a fixed layout (header / scrollable controls | visualization / animation footer) and override:
- `build_controls(parent)` — left-side parameter widgets
- `build_visualization(parent)` — right-side matplotlib / canvas content
- `build_theory(doc, ctx)` — optional, consumed by `TheoryViewer`
- `animate_step(t)` — optional, driven by `StepAnimator` when `HAS_ANIMATION = True`

Shared widgets live in [education/components/](education/components/):
- Layout / inputs: `PlotPanel`, `FourPanel` (2×2 con bordes suaves y mezcla 2D/3D), `ParamInput`, `ElementPicker`
- Animación / teoría: `StepAnimator`, `TheoryViewer`, `TheoryDoc` (sigue usando `pylatex` + `PyMuPDF` para la ventana de teoría extendida)
- Matemática: `render_matrix_latex` / `render_expression_latex` en [latex_figure.py](education/components/latex_figure.py) (LaTeX vía `matplotlib.mathtext`, **sin** compilador externo), `iso_inverse_map` y `natural_to_physical` en [iso_inverse.py](education/components/iso_inverse.py)
- Video: `VideoPlayer` en [video_player.py](education/components/video_player.py) (`tkvideoplayer`, degrada a mensaje si el paquete o el MP4 faltan)

New modules should reuse these rather than reimplementing layout. **No duplicar `fem/`**: los módulos son sólo visualización — consumen `shape_functions`, `jacobian`, `b_matrix`, `constitutive`, `stiffness`, `gauss_quadrature`, `assembly`.

**Registro y lanzamiento de módulos**: [education/module_launcher.py](education/module_launcher.py) centraliza el `MODULE_MAP` (`mod01..mod06 → (módulo, clase)`) y expone `open_module(parent_tk, project, mod_key, mesh_canvas=None, elem_id=None)`. Tanto el menú Educación de `MainWindow` como `proc_tab._open_module` delegan aquí — si añades un módulo nuevo, **regístralo en `MODULE_MAP`**, no dupliques el import dinámico.

### Other
- [config/settings.py](config/settings.py) — all magic strings (analysis types, element types, file extension, canvas colors, tolerances). Also `USER_CONFIG_DIR` (= `~/.edufem`), `RECENT_FILES_PATH`, `RECENT_FILES_MAX`, `DEFAULT_GRAVITY`. Import from here instead of hardcoding.
- [config/units.py](config/units.py) — unit-system definitions.
- [config/recent_files.py](config/recent_files.py) — JSON persistence of recent project paths (`load`/`add`/`remove`/`clear`).
- [gui/widgets/tooltip.py](gui/widgets/tooltip.py) — `ToolTip(widget, text)` helper (Toplevel overrideredirect) used by the emoji toolbar.
- [file_io/](file_io/) — CSV (`csv_io`), PDF reports (`pdf_report`, uses `reportlab`/`PyMuPDF`/`pylatex`), project JSON (`project_io`).
- [tests/example_data.py](tests/example_data.py) — canonical 9-node / 4-Q4 validation case (E=225000, ν=0.2, t=0.8, P at node 7, nodes 1/3/6 fixed). Used by the File → "Cargar Ejemplo" menu and by `test_fem.py`.

## Convenciones al tocar los módulos educativos

- **LaTeX → usar `matplotlib.mathtext`** (`render_matrix_latex` / `render_expression_latex`). No reintroducir la cadena `pylatex → pdflatex → PyMuPDF → PIL` dentro de un módulo — eso quedó confinado a `TheoryDoc` para la ventana de teoría extendida.
- **Video Manim** se embebe con `tkvideoplayer`; los MP4 viven en [resources/videos/](resources/videos/) y el módulo debe degradar a un mensaje si falta el archivo o el paquete (ver `VideoPlayer._build`).
- La clase simbólica `SymbolicIntegrandQ4` ahora vive dentro de [mod04_stiffness_gauss.py](education/mod04_stiffness_gauss.py) (migrada del desaparecido `ModuloIntegrandoQ4.py`). Si necesita reusarse en otro módulo, moverla a `fem/` en vez de duplicar.
- La pestaña "Post-Proceso" ya cubre esfuerzos/Von Mises; no reintroducir un `mod_stress` educativo.
