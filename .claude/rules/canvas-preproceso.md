---
paths:
  - "gui/preprocessing/**/*.py"
  - "gui/postprocessing/**/*.py"
---

# Canvas, spreadsheet y post-proceso

Canon completo: **[docs/convenciones/canvas-preproceso.md](../../docs/convenciones/canvas-preproceso.md)**.

- **Selección**: `select_*()` / `replace_*_selection()`. `highlighted_*` es un espejo de solo
  lectura — no lo setees a mano.
- **Canvas → spreadsheet**: aplicá el tag visual `canvas_selected`. **Nunca
  `tree.selection_set` desde ese callback**: dispara `<<TreeviewSelect>>` async sin guard y
  congela la GUI. Sentido inverso (spreadsheet → canvas) sí es síncrono.
- **Prioridad de tags en `ttk.Treeview` = orden de `tag_configure`** (gana el primero
  configurado, no la posición en la tupla del item). `canvas_selected` se configura primero.
- **Trampa de orden**: las 3 pestañas se construyen **antes** que `MeshCanvas`, así que
  cualquier wiring `*_tab → mesh_canvas` desde `__init__` falla. Va en `_wire_canvas_callbacks()`,
  que `MainWindow._build_main_layout` invoca después de crear el canvas.
- **Colormap de resultados: `jet`** en todos los campos (los que tienen signo, centrados en 0).
  `hsv` prohibido. Canvas, vista 3D y memoria PDF comparten paleta.
- **En Post no hay selección de elementos**: la inspección es por probe y contorno. `_on_click`
  retorna temprano cuando la fase es `post`.
- **Colores** desde `config/settings.py`; **números** con `fmt(value, kind)`. El editor
  flotante se pre-llena con `fmt(raw, kind)`, no con el float crudo.
- Los `_paste_*` toleran coma decimal (Excel en español).
