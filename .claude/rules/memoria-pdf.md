---
paths:
  - "file_io/memoria_calculo.py"
  - "file_io/figure_export.py"
  - "gui/dialogs/theory_hub_dialog.py"
  - "education/components/theory_builder.py"
  - "education/components/theory_viewer.py"
  - "education/components/latex_runtime.py"
---

# Memoria de cálculo (PDF) y figuras

Canon completo: **[docs/convenciones/memoria-calculo.md](../../docs/convenciones/memoria-calculo.md)**.

- **Los strings del `.tex` van en ASCII**: `\sigma`, `\to`, `\le`, `\mathbf{k}_e` — un σ, →,
  ε o ≤ literal aborta la compilación (`LaTeX Error: Unicode character σ (U+03C3) not set up
  for use with LaTeX`: el `.tex` se escribe en UTF-8, pero esos símbolos no tienen definición
  con `inputenc`). Los acentos españoles sí entran.
- **Regla de oro del pipeline compartido**: las **fórmulas, matrices y ecuaciones se emiten
  siempre**; solo los párrafos narrativos y las cajas pedagógicas van detrás de
  `if self._prose:`. Una `td.equation` o `td.matrix` gateada desaparece del estilo `directo`,
  que es justamente el procedimiento matricial.
- **`figure_export.py` es Pillow puro**: no importa matplotlib y así se queda. Fondo blanco
  (el PDF se imprime) y **sin subíndices unicode** (₁ ₂ ₑ se rinden como cajas en la fuente
  del sistema: usá `σ1`, `ke`).
- **Teoría general, no internals**: la narrativa sigue la formulación clásica del MEF. No
  menciones `spsolve`, SuperLU, `node_index_map`, CSR/COO ni rutas `fem/...`; el solver es
  "factorización LU directa" en abstracto.
- Los umbrales `_COMPACT_MAX_ELEMENTS_Q4 = 2` / `_Q9 = 1` gobiernan si se desarrollan todos
  los elementos o solo el de máxima energía. Subirlos desborda la página.
- **Unidad APILADA bajo el símbolo**: todo encabezado con magnitud física pasa por
  `MemoriaCalculo._th_unidad(simbolo, unidad)`, nunca `simbolo + unidad`. En línea, seis
  columnas de tensiones repitiendo `[kgf/cm²]` sacaban las dos tablas de tensiones de la hoja
  (89,9 pt con márgenes de 2,2 cm; 50,0 pt aun con los 1,5 cm actuales). Y el desborde depende
  del **sistema de unidades**: con `MPa` entra, con `kgf/cm²` no — probalo con el ejemplo de
  Timoshenko, no con el canónico.
- **Márgenes laterales 1,5 cm** (`MemoriaCalculo.MARGEN_LATERAL`), contra los 2,2 cm que
  `TheoryDoc` usa por defecto para la Teoría, que es prosa. No unificarlos.
- **Al tocar tablas, matrices o ecuaciones: compilar y mirar el `.log`.**
  `test_nada_se_sale_de_la_hoja` exige cero `Overfull \hbox` sobre Timoshenko Q9. Un
  `equation*` no parte línea: la entrada simbólica `K_11` llegó a imprimirse **566 pt fuera de
  la hoja**, invisible, por el ruido de redondeo que
  `fem.symbolic_integrand.podar_ruido` ahora elimina.
- **Compilación solo vía `latex_runtime.compile_document`** (`TheoryDoc.compile_to` y
  `TheoryViewer` ya pasan por ahí): resuelve el TeX Live embebido antes que el PATH, compila en
  un temporal con ruta ASCII sin ventana de consola y mueve el PDF al destino. No volver a
  llamar `Document.generate_pdf` de pylatex ni a `latexmk`.
- **Las figuras de la Memoria se referencian por nombre relativo** (`_save_figure` devuelve
  `nombre.png` y se compila en ese mismo `workdir`): ninguna ruta absoluta entra al `.tex`.
- `pdflatex` sigue sin fallback: si no hay ni bundle ni PATH, `memoria_calculo.compile` eleva
  `PdflatexNotFoundError` y la GUI abre el diálogo con botón de descarga.
