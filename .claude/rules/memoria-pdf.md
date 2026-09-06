---
paths:
  - "file_io/memoria_calculo.py"
  - "file_io/figure_export.py"
  - "gui/dialogs/theory_hub_dialog.py"
  - "education/components/theory_builder.py"
---

# Memoria de cálculo (PDF) y figuras

Canon completo: **[docs/convenciones/memoria-calculo.md](../../docs/convenciones/memoria-calculo.md)**.

- **Los strings del `.tex` van en ASCII**: `\sigma`, `\to`, `\le`, `\mathbf{k}_e` — un σ, →,
  ε o ≤ literal aborta la compilación con `'charmap' codec can't encode` (pylatex escribe con
  la codificación del sistema, cp1252 en Windows). Los acentos españoles sí entran.
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
- `pdflatex` es obligatorio y **no tiene fallback**: si falta, `memoria_calculo.compile` eleva
  `PdflatexNotFoundError` y la GUI abre el diálogo con botón de descarga.
