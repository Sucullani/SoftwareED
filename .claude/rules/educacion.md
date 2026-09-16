---
paths:
  - "education/**/*.py"
---

# Módulos educativos (M0..M7)

Canon completo: **[docs/convenciones/modulos-educativos.md](../../docs/convenciones/modulos-educativos.md)**.
Antes de agregar un widget que "falta":
**[no-reintroducir.md](../../docs/convenciones/no-reintroducir.md)**.

**Numeración vigente** — M0 calidad de malla · M1 mapeo iso · M2 Jacobiano ·
**M3 matriz B** (`mod03_b_matrix.py`) · **M4 matriz D** (`mod04_constitutive.py`) ·
M5 rigidez + Gauss · M6 fuerzas equivalentes · M7 ensamblaje. `Ctrl+3` abre B, `Ctrl+4` abre D.
Los bullets históricos del capítulo usan la numeración anterior (B era M4): leelos con esa nota.

**Ciclo de vida del overlay — romper esto mata la app**:
- `CanvasOverlay.close()` hace `withdraw()`, **nunca `destroy()`**: destruir un Toplevel
  `overrideredirect=True + transient(root)` desde un handler de un widget hijo dispara un
  WM_CLOSE al root en Tcl/Tk de Windows.
- `transient(root)` **es necesario** (sin él Windows oculta el Toplevel al primer cambio de
  foco), y por eso **no** se registra `protocol("WM_DELETE_WINDOW", ...)`.
- El botón × va en `<ButtonRelease-1>` y difiere el cierre con `after_idle`.

**Al dibujar sobre el canvas**:
- Registrá la capa con `mesh_canvas.add_overlay_layer`; tag propio `edu_mN_*` y primer paso
  de `draw_canvas_layer` siempre `mesh.canvas.delete(_TAG)`.
- En loops de animación (~30 fps con `mesh.after(33, ...)`) usá `mesh.redraw_overlays_only()`,
  no `redraw()` (rasteriza toda la malla, 80-200 ms por frame). Guardá el `after_id` y
  cancelalo en `on_closed()`.
- El click en el `MeshCanvas` elige el elemento: ningún módulo duplica esa selección con un
  combobox interno.
- No mutes el `ProjectModel`: los sandboxes trabajan sobre `deepcopy` con `file_path = None`.

**Módulo nuevo**: archivo `education/modNN_*.py` (el `build.spec` lo toma por glob para
`hiddenimports`) + registrarlo en los **4** dicts de `education/module_launcher.py`.

**LaTeX**: matrices con `LatexMatrixImage` / `ScrollableMatrixImage`, escalares con
`LatexExpressionImage`. mathtext **no** soporta `\begin{bmatrix}` (los vectores van con
`\substack`). Nada de duplicar `fem/`: los módulos solo visualizan.

**Ancho de las matrices: `self.matrix_viewport_width()`, nunca `OVERLAY_WIDTH - N`.**
`OVERLAY_WIDTH` es una medida de diseño a 96 dpi; el overlay real mide `scaled(OVERLAY_WIDTH)`
recortado al área útil. Con el escalado de Windows al 125-150 % el número crudo dejaba la
matriz topada en 700 px dentro de una ventana de 925-1110, cortándola con el panel medio
vacío al lado.

**El body del overlay SE DESPLAZA** (`CanvasOverlay._viewport`): el alto sale del contenido y
se recorta a la pantalla, así que en un escritorio chico las últimas filas quedaban fuera y sin
forma de alcanzarlas — medido en 1280x600: M2 perdía 76 px y M3, 61, justo donde están la J y
la B. La rueda sobre cualquier punto del overlay desplaza el body (`_scroll_body`) y sigue
cortando la propagación, que es lo que evita el zoom accidental de la MeshCanvas y el cuelgue
del `FigureCanvasTkAgg`. Los módulos no cambian: siguen empaquetando en `self.body`.
