---
paths:
  - "models/**/*.py"
  - "fem/**/*.py"
  - "file_io/**/*.py"
  - "gui/dialogs/**/*.py"
  - "gui/main_window.py"
---

# Modelo, motor y diálogos

Canon completo: **[docs/convenciones/arquitectura.md](../../docs/convenciones/arquitectura.md)**.
Leelo antes de cambiar comportamiento acá; abajo van solo las trampas que rompen cosas.

- **Índices de GDL**: `project.dof_x(nid)` / `dof_y(nid)` / `Element.get_dof_indices(project)`;
  en bucles capturá `project.node_index_map` en una local. `2*(nid-1)` explota con IDs no
  contiguos (`tests/test_noncontiguous_ids.py`). Invalidá el cache (`= None`) al agregar,
  borrar o renombrar nodos.
- **Undo**: `self._capture(label)` **antes** de mutar, una vez por acción del usuario.
- **`restore_from_dict`** muta in-place y preserva refs (undo/redo); **`from_dict`** crea
  instancia nueva (abrir/guardar). No los intercambies.
- Campo nuevo en `ProjectModel` → `to_dict` **y** `from_dict`, con backward-compat.
- Toda mutación setea `is_modified = True` e `is_solved = False`.
- Todo flujo que cree elementos con `add_element` termina en `auto_expand_if_q9(project)`.
- **`fem/` es puro**: sin `tkinter`, `matplotlib` ni `ttkbootstrap`; debe correr headless.
  Cambios en `assembly`/`batch`/`solver`/`stress` → `python -m tests.test_solver_regression`
  (motor por lotes contra la versión legible, error relativo ≤ 1e-9) y `python -m tests.test_fem`.
- **Sin numba ni JIT**: el rendimiento sale de vectorizar por lotes en NumPy (`fem/batch.py`,
  `gui/preprocessing/canvas_raster.py`). La versión legible elemento a elemento se conserva
  como referencia pedagógica y oráculo; no la reemplaces por la optimizada.
- **Cargas superficiales**: la normal es la **exterior**, rotación −90° del tangente
  (`nx, ny = ty, -tx`), asumiendo CCW. Usá siempre `fem/equivalent_forces.py`.
- **Normas de error**: `n_gauss = p+1` (3 en Q4, 4 en Q9); reusar el orden de `K` subestima
  el error a un `O(h^{p+2})` artificial.
- **Recursos**: `config.settings.resource_path(*parts)`, nunca rutas relativas al CWD.
  Espejo en `gui/fonts_loader.py::_resources_root` — mantener ambos en sync.
- **Diálogos**: firma `(parent, project, main_window=None)` y centrado con `center_dialog`
  de `gui/dialogs/_dialog_helpers.py`.
- **Validación**: `_check_xxx(project, report)` en `models/model_health.py` + hint en
  `EDUCATIONAL_HINTS`. La GUI muestra el reporte, no valida por su cuenta.
