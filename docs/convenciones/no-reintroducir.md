# No reintroducir — índice de decisiones tomadas

> Capítulo del canon de EduFEM. Índice: [../../CLAUDE.md](../../CLAUDE.md) · mapa del repo: [../MAPA.md](../MAPA.md).

**Para qué sirve**: en EduFEM la mayoría de las ausencias son **decisiones deliberadas**, no
olvidos. Un agente que ve "falta un botón de cerrar", "falta el scrollbar", "falta la matriz D
en el diálogo de análisis" y lo agrega, está revirtiendo trabajo hecho. **Antes de agregar algo
que no está, buscalo acá.**

**Cómo usarlo**: `Ctrl+F` sobre esta página. Cada fila es un recordatorio de una línea; el
**motivo completo y su contexto** están en el capítulo enlazado, que es la fuente de verdad
(esta tabla nunca la reemplaza).

**Si tenés que revertir una de estas decisiones**: no lo hagas en silencio. Documentá en el
capítulo correspondiente qué mejora pedagógica o funcional concreta lo justifica, y actualizá
esta fila.

Abreviaturas de capítulo:
**[ARQ]** = [arquitectura.md](arquitectura.md) ·
**[EDU]** = [modulos-educativos.md](modulos-educativos.md) ·
**[CAN]** = [canvas-preproceso.md](canvas-preproceso.md) ·
**[MEM]** = [memoria-calculo.md](memoria-calculo.md) ·
**[EST]** = [estilo-paleta.md](estilo-paleta.md) ·
**[FEM]** = [roadmap-fem.md](roadmap-fem.md)

---

## Modelo, unidades y motor FEM

| No reintroducir | Motivo (resumen) | Cap. |
|---|---|---|
| El sistema de unidades **"Personalizado"** | Eran solo rótulos sin factores reales; rompía conversión y health checks | [ARQ] |
| Indexado de GDL `2*(nid-1)` | `IndexError` con IDs no contiguos tras borrar nodos; usar `node_index_map` | [ARQ] |
| Dimensionar `K` como `2*max(node_id)` | Idem: se dimensiona `2*num_nodes` | [ARQ] |
| Normal de carga superficial `nx0, ny0 = -ty, tx` | Da la normal **interior**: aplicaba la presión al revés | [ARQ] |
| Duplicar el cálculo de fuerzas equivalentes en M6 | Fuente única: `fem/equivalent_forces.py` | [ARQ] |
| Duplicar la validación del modelo en la GUI | Se agrega `_check_xxx` en `models/model_health.py` | [ARQ] |
| `reportlab` como dependencia | Estaba declarada y sin un solo import; la memoria es 100 % pylatex | [ARQ] |
| `messagebox.showerror` cuando falta `pdflatex` | Se usa el diálogo con botón de descarga (`pdflatex_missing_dialog`) | [ARQ] |
| Tolerancias numéricas locales ad-hoc | Centralizadas en `config/settings.py` | [FEM] |
| Reemplazar la versión legible de `fem/` por la optimizada | Es la referencia pedagógica de M2/M3/M5 y el oráculo de `test_solver_regression`: exponer ambas | [FEM] |
| `numba`, `@njit`, `fem/_numba_compat.py` o kernels escalares "para JIT" | El motor está vectorizado por lotes en NumPy (`fem/batch.py`); en el `.exe` numba nunca corría y sus kernels escalares eran el peor caso (51 s de isolíneas) | [FEM] |
| Kernels por píxel / por celda en `mesh_canvas.py` (`_rasterize_triangle_njit`, `_marching_squares_njit`) | Reemplazados por `gui/preprocessing/canvas_raster.py`, vectorizado y con paridad píxel a píxel | [CAN] |
| El loop por triángulo de `file_io/figure_export._fill_field` | Reusa `canvas_raster.rasterize_triangles` desde el 2026-09-06: el contorno de la memoria bajó de 16,7 s a 0,51 s en 1024 elementos, con 0 píxeles distintos | [MEM] |
| `SOLVER_USE_RCM`, `SOLVER_RCM_MIN_DOF` y el reordenamiento Cuthill-McKee inverso en `_solve_reduced` | Eliminados el 2026-09-06: solo rinden por encima de ~8500 GDL y ahí ahorran decenas de ms en flujos que tardan segundos; por debajo son una pérdida. `SOLVER_PERMC_SPEC = "MMD_AT_PLUS_A"` ya da 2,1× | [FEM] |
| Extrapolar o promediar `σ₁` / `σ₂` / von Mises entre nodos | Son no lineales en las componentes: se recomputan desde las cartesianas ya extrapoladas o promediadas (2026-09-06). Antes la tabla nodal mostraba un VM que no correspondía a las componentes de su propia fila | [FEM] |

## Menús y diálogos

| No reintroducir | Motivo (resumen) | Cap. |
|---|---|---|
| Un cuarto menú (*Editar*, *Ver*, *Análisis*, *Educación*) o una toolbar | Diseño de 3 menús: Archivo / Modelo / Ayuda | [ARQ] |
| Menú de *Preferencias / Configuración* | Defaults sanos hardcodeados en `config/settings.py` | [ARQ] |
| La entrada de menú *Exportar Resultados CSV* | Los resultados se copian del Post con `Ctrl+C` (TSV) | [ARQ] |
| Llamadas explícitas a `_refresh_menu_state` tras mutaciones | Lo sincroniza el `postcommand` del menú Archivo | [ARQ] |
| Reordenar el menú Modelo | El orden Elemento → Unidades → Material → Gravedad → Análisis es el flujo FEM | [ARQ] |
| Un `_center()` local en un diálogo nuevo | Usar `center_dialog` de `_dialog_helpers.py` | [ARQ] |
| `Material.color`, swatch, paleta o colorchooser | El atributo no lo consumía ni el solver ni el canvas | [ARQ] |
| Scrollbar visible, botón Duplicar o footer *Cerrar* en `MaterialDialog` | Scroll por rueda; la X del Toplevel cierra | [ARQ] |
| En `GravityDialog`: Labelframes, botón preset, labels de unidad, hints | La flecha en vivo sobre el canvas hace el trabajo pedagógico | [ARQ] |
| En `UnitsDialog`: chip-line de unidades derivadas, modal de confirmación | Ruido: el nombre del sistema ya enumera las unidades | [ARQ] |
| `fit_view()` automático tras convertir unidades | Rompía el pan/zoom del usuario; se compensa `scale` | [ARQ] |
| En `ElementTypeDialog`: header-pregunta, subtítulo, banner bidireccional, tiles | Consolidados en video + 2 toolbuttons | [ARQ] |
| La matriz **D** dentro de `AnalysisTypeDialog` | D depende del material: se explora por elemento en M4 | [ARQ] |
| `tkvideoplayer`, `av` / `PyAV` | Migración deliberada a WebP: instalador más liviano, sin DLLs de FFmpeg | [ARQ] |
| `FuncAnimation` sin guardar referencia persistente | El GC mata la animación y congela el Toplevel modal | [ARQ] |

## Canvas, spreadsheet y Post-Proceso

| No reintroducir | Motivo (resumen) | Cap. |
|---|---|---|
| Atajos en tablas más allá de `Delete` / `Ctrl+C` / `Ctrl+V` | Sin Insert, F2, Ctrl+G/R/M/L/U/I, hint `<FocusIn>` ni menú contextual | [CAN] |
| `tree.selection_set` desde el callback canvas → spreadsheet | Disparaba `<<TreeviewSelect>>` async sin guard y congelaba la GUI | [CAN] |
| Zebra striping (`even`/`odd`) en Treeview | Compite con los 4 estados semánticos de fila | [CAN] |
| Azul `#1f6feb` para la fila seleccionada | La selección es amarilla, venga del canvas o de la tabla | [CAN] |
| Migrar a `tksheet` | Descartado | [CAN] |
| El botón "Aceptar todas con defaults" de las filas fantasma | No resuelve el caso real; para creación masiva está el paste TSV | [CAN] |
| Numeración global incondicional / flags `show_node_labels`, `show_elem_labels` | Reemplazados por `node_label_mode` / `elem_label_mode` (auto/always/never) | [CAN] |
| El halo grueso del elemento seleccionado | El relleno punteado es la señal primaria; el halo era "muy fuerte" | [CAN] |
| Quitar el relleno punteado de la selección | Es lo que evita perder la selección en mallas grandes | [CAN] |
| Botón `Limpiar Resultados`, método `clear_results`, menubutton "Vista", botón `Ajustar` en la barra | Consolidados en el menú del título del viewport | [CAN] |
| Toggles de foco/silueta en el menú del viewport | Solo actúan en mallas grandes: quedan en automático | [CAN] |
| Un toggle de capa *Elementos* | Ocultar la malla deja nodos y cargas flotando | [CAN] |
| Controles de resultado (deformada, VM/σx, isolíneas, 3D) en la barra del viewport | Viven en el panel del Post: una sola vía | [CAN] |
| Selección de elementos en Post-Proceso | La inspección es por probe y contorno; el realce tapa el colormap | [CAN] |
| Probe sobre coordenadas sin deformar con la malla deformada | Los marcadores quedaban descolgados de la malla visible | [CAN] |
| Clamp de decoraciones en px absolutos | Rompe las flechas (base 44 capada a un techo pensado para nodos) | [CAN] |
| `is_roller_x` como triángulo lateral sin rodillo | Era indistinguible del empotramiento | [CAN] |
| Aristas curvas en Q9 | La GUI prioriza la claridad del polígono macro | [CAN] |
| Setear `highlighted_*` directo | Usar `select_*` / `replace_*_selection` | [CAN] |

## Colores y estilo

| No reintroducir | Motivo (resumen) | Cap. |
|---|---|---|
| Hex literales fuera de `config/settings.py` | Regla dura; auditoría pre-merge espera 0 hits en `gui/` y `education/` | [EST] |
| `coolwarm` / `turbo` / `viridis` en campos de resultado | El usuario pidió **jet** para todo (2026-05-31) | [EST] |
| `hsv` como colormap | Prohibido | [EST] |
| Decimales hardcodeados (`f"{x:.4f}"`) | Usar `fmt(value, kind)` | [EST] |
| Prefijo `+` en celdas positivas de matrices/vectores | Solo el `-` de los negativos | [MEM] |

## Módulos educativos (transversal)

| No reintroducir | Motivo (resumen) | Cap. |
|---|---|---|
| Botón *Cerrar* propio en el header de un módulo | La X nativa del Toplevel ya cierra | [EDU] |
| Botón *? / Teoría* propio | La teoría vive en Ayuda ▸ Teoría FEM (transversal) | [EDU] |
| Badge de Q4/Q9, TP/DP, material, E, ν, ρ, t | El alumno ya definió su modelo | [EDU] |
| Combobox de elemento dentro de un módulo | El click en el canvas es la única vía de selección | [EDU] |
| Hints "Click aquí para…" cuando ya hay feedback visual | La invitación está en la animación | [EDU] |
| Scrollbar visible o badges textuales en el panel de módulos | El chip a la derecha resuelve el id de elemento | [EDU] |
| Deshabilitar módulos globales (M0) por falta de selección | No la necesitan | [EDU] |
| `highlight_element` para sincronizar al abrir un módulo | Tiene semántica "second-click deselects" y apagaba la selección | [EDU] |
| El `simpledialog.askinteger` del launcher | Cero diálogos modales: el módulo espera el click en el canvas | [EDU] |
| Mezclar herencias `CanvasOverlayModule` + base Toplevel | Cada módulo elige UNA | [EDU] |
| `CanvasOverlay` con `place()` y clamp contra el parent | Tapaba elementos clickeables; es un Toplevel borderless | [EDU] |
| `protocol("WM_DELETE_WINDOW")` o `destroy()` en un overlay borderless | Mata la app en Tcl/Tk de Windows: `close()` hace `withdraw()` | [EDU] |
| Las legacy `on_element_select` / `on_node_select` | Están muertas: el canvas no las dispara | [EDU] |
| El pop-up `MatrixZoom` / `LatexMatrixImage(zoomable=True)` | Reemplazado por `ScrollableMatrixImage` (scroll in-frame) | [EDU] |
| `ScrollableMatrixImage` para matrices que **sí** entran | Su canvas de ancho fijo recortaba columnas: usar el label auto-dimensionado | [EDU] |
| `\begin{bmatrix}` en strings de mathtext | matplotlib mathtext no lo soporta | [EDU] |
| Subíndices Unicode tipográficos (`ᵧ`) | Faltan en DejaVu Sans Mono: usar sufijos ASCII | [EDU] |
| Expanders para la fórmula principal de un módulo | Destruye la jerarquía visual: el expander es excepcional | [EDU] |
| Duplicar código de `fem/` en `education/` | Los módulos solo visualizan | [EDU] |
| Los literales `#4fa3ff` / `#3a5278` locales | Viven en `EDU_NATURAL_*` de settings | [EDU] |

## Módulos educativos (por módulo)

| Módulo | No reintroducir | Cap. |
|---|---|---|
| **M0** | Coloreado bipolar gris-centro; umbral único compartido entre las dos métricas; dos banners simultáneos; un refit por banner; el `refit` diferido `after(50)`; el botón Reset; el radar de 4 ejes; el histograma; los expanders de derivación LaTeX; el relleno sólido o punteado denso; la malla base a color normal bajo M0 | [EDU] |
| **M1** | El chip de dualidad `(x,y) ↔ (ξ,η)` y su pulso; widgets tk de fórmula/valor bajo la figura; el título `N{idx}(ξ,η)`; el label `Nᵢ=valor` sobre el canvas; las coords en la línea de estado; el readout pinneado en esquina; el signo `+` en positivos | [EDU] |
| **M2** | El readout tk (`GaussCoordReadout`); apilar cuadrado + superficie; **drag** en el cuadrado matplotlib (laguea la 3D); la J de derivadas abstractas `∂x/∂ξ`; el banner **verde** de validez (el rojo de degenerado sí queda); la ∂N simbólica en blanco; forzar `ScrollableMatrixImage` para matrices que entran; "corregir" la superficie plana de det J en Q9 (no es un bug) | [EDU] |
| **M3 (B)** | El readout tk; la notación `N1x`; la **relación escalar malformada** `∂Nᵢ/∂x = J⁻¹ ∂Nᵢ/∂ξ` (usar siempre la vectorial 2×1); la descripción del mapeo; el `_lbl_status`; el viewport hardcodeado de B | [EDU] |
| **M4 (D)** | El dial circular; el Entry numérico `ν =`; el botón "Reset al ν del material"; el título `ν = …` sobre la matriz; la regla de materiales dentro del probe; los nombres largos en el espectro; el caption "Efecto Poisson"; el rótulo "deformación exagerada"; las flechas ámbar de contracción; el semáforo de 4 colores del fill; **cualquier ancho del probe dependiente de ν**; las constantes muertas `_PROBE_VIS_SCALE`/`_CONTRACT_COLOR`; la línea de isotropía aparte; las flechas de ∇Nᵢ sobre el elemento | [EDU] |
| **M5** | El `GaussCoordReadout` tk; `_lbl_k_title`; el viewport de kₑ de 300 px; el `after(120)` sin cancelar; el triple mensaje de estado vacío | [EDU] |
| **M7** | (ex-M7 y ex-M8 fueron consolidados en el Post: no recrear `mod07_stress_discontinuity.py` ni `mod08_principal_stresses.py`) | [EDU] |
| **ex-M9** | `mod09_q4_vs_q9_comparison.py` y su renderer `result_image_renderer.py` | [EDU] |
| **Post** | Las cruces principales σ₁/σ₂ (toggle + `principal_cross_layer.py`) y su rotación global por drag; Toplevels separados para 3D / Mohr | [EDU] |

## Memoria de Cálculo y Theory Hub

| No reintroducir | Motivo (resumen) | Cap. |
|---|---|---|
| El estilo `'completo'` y un tercer estilo sin documentarlo | `STYLES = ("educativo", "directo")` | [MEM] |
| Los apéndices A/B/C (`_build_appendix_*`) | Eliminados | [MEM] |
| El pipeline `_build_directo` separado / superficial y la property `_appendices` | Hay un único pipeline; solo la prosa va gateada | [MEM] |
| `td.equation` / `td.matrix` dentro de un `if self._prose` | Desaparecerían del estilo directo, que es el procedimiento matricial | [MEM] |
| Mostrar solo `J` / `B` resultado sin la cadena de sustitución | Rompe la consistencia con M2/M3 | [MEM] |
| Cómputos repetidos de `evaluate_mesh_quality` / `validate_project` | Usar los memoizadores `_mesh_quality()` / `_health()` | [MEM] |
| Figuras matplotlib en `figure_export.py` | Es Pillow-only; las 3D viven en el Post nativo | [MEM] |
| `render_surface_3d` o una 3D estática en el PDF | Suma peso sin ganancia sobre el contorno 2D | [MEM] |
| Internals del software en la narrativa (`spsolve`, SuperLU, `node_index_map`, rutas `fem/…`) | La teoría es general, estilo libro de texto | [MEM] |
| Caracteres no-ASCII literales (σ, →, ≤, ₑ, κ, ε) en strings LaTeX | Abortan la compilación en cp1252 | [MEM] |

---

## Cómo agregar una fila

Cuando elimines algo a pedido del usuario o por decisión de diseño:

1. Documentá el **motivo** en el capítulo que corresponda (`docs/convenciones/*.md`), donde
   vive el contexto completo.
2. Agregá acá **una línea** en la tabla del área correspondiente, con el enlace al capítulo.
3. Si la decisión revierte una anterior, **borrá la fila vieja** — no acumular contradicciones.
