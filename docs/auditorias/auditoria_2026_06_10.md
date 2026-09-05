# Informe I — Auditoría general del repositorio

**Proyecto**: EduFEM (SoftwareED) · **Fecha**: 2026-06-10 · **Rama auditada**: `claude/github-audit-prompt-ldit2b` (base `d7a4e19`)
**Método**: 5 agentes de auditoría en paralelo (modelo Fable 5) + ejecución completa de la batería de tests. Cada hallazgo fue verificado leyendo el contexto del código (no solo por grep); los 3 hallazgos más graves fueron **reproducidos** con scripts headless. No se aplicó ningún fix — este informe es solo diagnóstico.

## Resumen ejecutivo

El repo está en **muy buen estado general**: las reglas duras del proyecto (paleta congelada, terminología GDL/MEF, pureza de `fem/`, `resource_path`, captura de undo, indexación de GDL por `node_index_map`, prohibiciones "No reintroducir") se respetan casi sin excepción, la serialización es simétrica, no hay problemas de seguridad y 14/15 tests pasan. Sin embargo, la auditoría de correctitud encontró **1 hallazgo crítico reproducible** (corrupción de `_node_to_elements` al renombrar elementos → crash en flujo GUI común) y **1 alto** (autofix de cargas superficiales borra la carga equivocada), más un grupo de medios accionables. En lo documental, `CLAUDE.md` tiene 4 afirmaciones desactualizadas que pueden inducir regresiones si un dev "alinea el código con el doc".

| Severidad | Cantidad | Dónde se concentra |
|---|---|---|
| Crítico | 1 | models/project.py (change_element_id) |
| Alto | 3 | model_health autofix · CLAUDE.md (×2 doc-código) |
| Medio | 12 | assembly, validador, undo, PDF worker, M6, paste, docs |
| Bajo | ~25 | tolerancias, código muerto menor, comentarios stale, higiene |

## Resultados de la batería de tests (2026-06-10)

| Test | Resultado |
|---|---|
| test_fem · test_vv_extensions · vv_mms · vv_timoshenko · vv_cook | PASS (5/5) |
| test_q9_q4_cycle · test_undo_stack · test_serialization | PASS (3/3) |
| test_unit_conversion · test_node_cascade · test_noncontiguous_ids | PASS (3/3) |
| test_pick_ghost · test_canvas_visualization | PASS (2/2) |
| test_selection_integration | PASS (se auto-omite sin Tk, con mensaje) |
| test_draw_mode | FAIL en entorno headless — ver hallazgo T-1 |

**T-1 (bajo)** — `tests/test_draw_mode.py:29` importa `MeshCanvas` (y por lo tanto `tkinter`) **a nivel módulo**, pese a que CLAUDE.md lo declara "testeable sin Tk". En un entorno sin tkinter el test aborta en el import, antes de llegar a la lógica pura. Fix: replicar el patrón de `test_selection_integration` (guard de import con skip) o extraer `_shoelace_signed` del import del canvas.

**T-2 (bajo)** — Correr los scripts V&V regenera `docs/vyv/datos/*.csv` y `docs/vyv/figuras/*.png` **sobre archivos versionados**, con diff solo de fin de línea (CRLF commiteado vs LF generado). El contenido numérico es idéntico (verificado en `cook.csv`: los datos versionados están al día con el código). Fix: `.gitattributes` con `*.csv text eol=lf` o normalizar una vez.

<<<PAGEBREAK>>>

## 1. Correctitud y robustez

### Hallazgos principales (reproducidos)

| Severidad | Archivo:línea | Hallazgo | Fix propuesto |
|---|---|---|---|
| **CRÍTICO** | models/project.py:489-504 | `change_element_id` no actualiza `_node_to_elements`: los sets quedan con el id viejo. **Reproducido**: renombrar un elemento y luego borrar uno de sus nodos crashea `preview_node_cascade` con KeyError (explota el modal de confirmación de pre_tab y canvas); además `is_node_referenced` y el auto-cleanup quedan rotos (huérfanos nunca limpiados). | Tras reasignar, por cada nodo del elemento: `discard(old_id)` + `add(new_id)` (o `rebuild_node_to_elements()`). Agregar caso a test_node_cascade. |
| **ALTO** | models/model_health.py:539-557 + health_report_dialog.py:454-469 | Autofix de surface loads usa el **índice posicional** de la validación original: dos clicks "Corregir" seguidos sobre issues de surface borran la carga **equivocada** o son no-op silencioso. **Reproducido.** | Identificar la surface por identidad de objeto (guardar la ref en `extra` y usar `.remove(ref)`), o re-validar y reconstruir cards tras cada fix. |
| Medio | fem/assembly.py:219 | Carga nodal sobre `node_id` inexistente (posible vía `.edufem` editado a mano — `from_dict` no valida): el validador la marca solo como warning y el solve crashea con `KeyError: 999` crudo ("Error al resolver: 999"). **Reproducido.** | `idx = idx_map.get(load.node_id)` + skip si None (mismo patrón que `get_restrained_dofs`), o elevar el caso a error en el validador. |
| Medio | models/model_health.py (ausente) | Nodo huérfano sin datos → el validador dice "✓ Modelo sano" pero aporta 2 filas nulas a K → solve falla con mensaje genérico de NaN. Además el mensaje de `load_orphan_node` ("la carga no contribuye") es incorrecto: la carga SÍ entra a F y el sistema queda singular. | Agregar `_check_orphan_free_nodes` (error, fixable con borrado) + corregir el mensaje. |
| Medio | gui/dialogs/health_report_dialog.py:454-456 | `_on_fix` muta el project (`apply_autofix`) **sin captura de undo** — los autofixes no son reversibles con Ctrl+Z, violando la regla de CLAUDE.md. | `stack.capture(f"autofix {issue.code}")` antes de aplicar. |
| Medio | gui/main_window.py:1016-1027 | El worker de la Memoria PDF lee `self.project` mutable mientras la GUI sigue interactiva (el progress dialog no hace grab_set): editar el modelo a mitad de generación produce excepción espuria o PDF inconsistente. | Snapshot inmutable (`from_dict(to_dict())` + refs de solución) antes de lanzar el thread. |
| Medio | gui/preprocessing/pre_tab.py:1943-2049 | Los 5 `_paste_*` usan `float(...)` **sin** el fallback de coma decimal que CLAUDE.md exige ("deben tolerar `,` de Excel español"): pegar `1,5` descarta la fila en silencio. | Helper compartido `_to_float_flex(v)` con `replace(",", ".")`. |
| Medio | models/undo_stack.py:130-135 | `_notify_restored` traga cualquier excepción de los listeners sin log: un bug en `_on_state_restored` dejaría la UI desincronizada sin rastro. | Mantener el no-bloqueo pero `traceback.print_exc()` en el except. |

### Hallazgos menores

| Severidad | Archivo:línea | Hallazgo | Fix propuesto |
|---|---|---|---|
| Bajo | element_type_dialog.py:96,214 · analysis_type_dialog.py:65,138 · dxf_import_dialog.py:133 | `after(...)` sin guardar id ni cancelar: cerrar el diálogo antes de ~200 ms dispara el callback sobre widgets destruidos (TclError). | Guardar id + `after_cancel` en cierre, o guard `winfo_exists()`. |
| Bajo | gui/dialogs/element_type_dialog.py:247-273 | `_on_accept` captura snapshot de undo **antes** del askyesno Q9→Q4: si el usuario cancela queda un nivel de undo no-op espurio. | Mover `capture` después de la confirmación. |
| Bajo | fem/error_norms.py:103 | `1.0/det_J` sin guard de `JACOBIAN_MIN_DETERMINANT` (probe_query/stiffness/jacobian sí lo tienen) — elemento degenerado → inf/NaN en normas V&V. | Guard + skip del punto. |
| Bajo | gui/postprocessing/post_tab.py:436-438 | `except Exception` de auto_solve muestra solo `str(e)[:60]` — produce diagnósticos crípticos (ver KeyError de assembly). | Loggear traceback completo a stderr además del messagebox. |
| Bajo | models/project.py:88-117 | `remove_node` legacy desincroniza `_node_to_elements` si gana callers nuevos (hoy su único caller GUI opera sobre nodos recién creados). | Assert/warning defensivo opcional. |

**Limpias**: indexación de GDL (cero `2*(nid-1)` fuera de comentarios/tests), invalidación de `is_modified`/`is_solved` y del cache de índices en todos los caminos, serialización simétrica con backward-compat completa, normal exterior de surface loads consistente con la convención documentada, fórmulas L/6 correctas, patrón undo/redo (fuera del autofix), warmup numba y worker PDF respetan "no tocar Tk desde otro hilo".

<<<PAGEBREAK>>>

## 2. Convenciones del proyecto y código muerto

**Limpias** (verificación exhaustiva): hex literales fuera de config (0 violaciones — 11 hits, todos en comentarios/docstrings), terminología GDL/MEF user-facing (0 violaciones), rutas de recursos vía `resource_path` (0 violaciones), pureza de `fem/` (0 imports GUI), y **ninguna** de las ~25 reglas "No reintroducir" verificadas fue violada (reportlab, tkvideoplayer, PyAV, FuncAnimation sin ref, MatrixZoom, Material.color, zebra, selection_set desde canvas, normal +90°, modo Personalizado, hsv, etc.).

| Severidad | Archivo:línea | Hallazgo | Fix propuesto |
|---|---|---|---|
| Medio | education/components/theory_builder.py:340 | `TheoryDoc.margin_formula()` tiene **cero consumidores** — CLAUDE.md la documenta como pieza viva ("fórmulas al margen" del estilo educativo) pero la memoria nunca la llama; `memoria_calculo.py:302-303` (marginparwidth) es preámbulo vestigial. | Cablearla en la memoria (y honrar el doc) o eliminar método + 2 líneas de preámbulo y actualizar CLAUDE.md. |
| Medio | gui/dialogs/memoria_style_dialog.py:129-139 | `_center()` local verbatim — viola "No reintroducir un _center() local; usar `center_dialog`". | Reemplazar por `center_dialog(self._top, parent)`. |
| Bajo | gui/dialogs/about_dialog.py:71-75 | Centrado inline duplicado con dimensiones hardcodeadas. | Usar `center_dialog`. |
| Bajo | config/settings.py:41,46,196,197,337 | 5 constantes sin consumidor: `ANALYSIS_TYPES`, `ELEMENT_TYPES`, `PROBE_PIN_LABEL_FG`, `PROBE_HOVER_COLOR`, `OVERLAY_ACCENT_MUTED`. | Eliminar o documentar por qué se conservan. |
| Bajo | gui/preprocessing/mesh_canvas.py:3053-3057 | `highlight_node()`/`highlight_element()` legacy con 0 callers — su existencia invita a reintroducir el bug "second-click deselects" prohibido. | Eliminar. |
| Bajo | gui/dialogs/ (6 diálogos) | Llamadas explícitas a `_refresh_menu_state()` tras mutar (material:401, units:125, analysis_type:180, gravity:277, dxf_import:412, element_type:285) — la regla del `postcommand` dice que duplican trabajo. | Eliminar las 6 (redundancia, no bug). |
| Bajo | mesh_canvas.py:1774,1798 · model_health.py:366,376 · mesh_quality.py:388 · iso_inverse.py:28,76 | Tolerancias ad-hoc (1e-10/1e-12/1e-9) que duplican el valor de `NUMERICAL_TOLERANCE` sin importar la constante. | Importar de config/settings. |
| Bajo | details_panel.py:217 · gravity_dialog.py:233 | Decimales hardcodeados en strings user-facing en vez de `fmt(value, kind)`. | Usar `fmt` (o documentar excepción para aceleración). |
| Bajo | mesh_canvas.py:4,632,2459 · surface_3d_viewer.py:10 · module_launcher_panel.py:196 | Comentarios/docstrings stale: "viridis/coolwarm" como paleta (es jet), "M0..M9" (M9 eliminado), fallback simpledialog inexistente. | Actualizar comentarios. |

## 3. Consistencia documental (CLAUDE.md)

| Severidad | Ubicación | Hallazgo | Fix propuesto |
|---|---|---|---|
| **ALTO** | CLAUDE.md:248 | Tabla de Atajos con orden "(mapeo, Jacobiano, **D, B**, K+Gauss…)" — orden PRE-swap que contradice la regla vigente B→D (línea 186) y el código (`_kbd_map`). Riesgo de que alguien "corrija" el código en la dirección equivocada. | Corregir a "(…, B, D, …)". |
| **ALTO** | CLAUDE.md:213 | Documenta los chips como `Q4 · 8 DOF` / `Q9 · 18 DOF`, violando su propia tabla de terminología — el código ya usa GDL (element_type_dialog.py:139,146). | Actualizar a GDL. |
| Medio | CLAUDE.md:215 | Tres errores en un párrafo de `AnalysisTypeDialog`: describe 2 videos (`tension_plana.webp`/`deformacion_plana.webp`) que no existen — el código usa un único `tension_deformacion_plana.webp` sin recarga — y atribuye la matriz D al "módulo M3" (es M4 tras el swap). | Reescribir el párrafo. |
| Medio | CLAUDE.md:225 | Referencia `tools/render_q4q9/record.mjs` como "conservado como referencia" pero el directorio **no existe**. | Reescribir en pasado sin link. |
| Bajo | CLAUDE.md (varios) | Links rotos a `education/base_module.py` y `gauss_inset.py` (eliminados, reconocido por el propio doc) en bullets históricos; rename histórico apunta a `mod05_stiffness_gauss.py` (real: `mod05_stiffness.py`); `RECENT_FILES_MAX` atribuido a recent_files.py (vive en settings.py:359). | Des-linkear / corregir. |

De un muestreo de 20 afirmaciones verificables de CLAUDE.md contra el código, **16 correctas, 4 desactualizadas** (las tabuladas arriba).

## 4. Dependencias y seguridad

**Seguridad: limpia.** Sin `eval`/`exec`/`pickle.load`/`shell=True`/`os.system` en todo el repo; sin secretos ni credenciales; escrituras de file_io atómicas (tmp+fsync+replace) con manejo de excepciones; `os.startfile` y `webbrowser.open` solo con paths/URLs controlados.

**Dependencias: limpias.** Los 9 paquetes de requirements.txt tienen imports reales; los opcionales (numba, ezdxf, pdflatex) tienen manejo de ausencia correcto. Única nota: `manim` (tools de render offline) no está mencionado en requirements-dev.txt — agregar comentario.

## 5. Higiene de repo

| Severidad | Ubicación | Hallazgo | Fix propuesto |
|---|---|---|---|
| Medio | tesis/compile_out.txt, tesis/compile_run.txt | Logs de compilación LaTeX trackeados — el patrón `.gitignore` `compile_output*.txt` no los matchea. | Patrón `compile_*.txt` + `git rm --cached`. |
| Medio | (raíz) | **No existe README.md** — el único doc de nivel repo es CLAUDE.md (orientado a agentes, no a humanos que clonan). | README mínimo: qué es EduFEM, instalación, `python main.py`. |
| Bajo | docs/*.pdf · tesis/main.pdf | PDFs compilados versionados junto a su fuente (~21 MB) — decidir política (distribución deliberada vs. artefacto). | Si no son distribuibles, ignorarlos. |
| Bajo | docs/ | Huérfanos no referenciados: audit_2026-05-25.md, auditoria_proyecto_2026-05-31.md, LEEME_distribucion.txt, propuesta_ux_modulos_educativos.{tex,pdf}. | Mover a docs/archive/ (sin urgencia). |
| Bajo | tests/ vs CLAUDE.md "Running" | `test_memoria_calculo`, `test_probe_query`, `test_noncontiguous_ids` existen pero no figuran en la lista "Running". | Agregarlos. |

Sin `__pycache__`/`dist`/`build` trackeados, sin archivos >5 MB fuera de `.git`, **cero TODO/FIXME/HACK reales** en producción.

## 6. Rendimiento

| Severidad | Archivo:línea | Hallazgo | Fix propuesto |
|---|---|---|---|
| Medio | education/mod06_equivalent_forces.py:246 | El tween de partículas (~60 fps) llama `redraw()` **completo** por frame — viola la regla de oro 5 de overlays (raster completo 80-200 ms/frame; M3/M7/probe ya usan `redraw_overlays_only()`). | `redraw_overlays_only()` en el loop (+ un `redraw()` inicial). |
| Bajo | fem/assembly.py:239-243 | Fallback Q9 de surface load sin `element_id`: escaneo O(E) por carga (solo si `element_id is None`). | Aceptable; precomputar dict arista→mid si crece. |
| Bajo | gui/preprocessing/pre_tab.py:853-856 | Edición de coord: loop O(E) buscando Q9 que contengan el nodo — existe `_node_to_elements` O(1). | Usar el dict. |

Lo demás sano: K nunca se densifica fuera de los puntos documentados, ensamblaje precomputa dN/N/Gauss por tipo con kernel JIT, canvas coalesce redraws, post_tab cachea el grid del probe, mod02 debouncia la superficie 3D.

<<<PAGEBREAK>>>

## Top-10 priorizado (impacto / esfuerzo)

1. **(P0)** `models/project.py:489` — `change_element_id` + `_node_to_elements` stale: crash reproducible en flujo GUI común y corrupción del auto-cleanup. Fix de 4 líneas + test.
2. **(P0)** `fem/assembly.py:219` — KeyError crudo por carga nodal huérfana: `.get()` + skip, 2 líneas.
3. **(P1)** `models/model_health.py:539` — autofix de surface loads por índice posicional: fix por identidad de objeto.
4. **(P1)** Validador: chequeo faltante de nodos huérfanos libres (K singular con "modelo sano") + mensaje incorrecto de `load_orphan_node`.
5. **(P1)** CLAUDE.md:248 y :213 — corregir orden B/D y chips GDL (riesgo de regresión inducida por doc).
6. **(P2)** `health_report_dialog.py:456` — `capture()` antes de los autofixes (reversibilidad Ctrl+Z).
7. **(P2)** `main_window.py:1016` — snapshot inmutable del project para el worker PDF.
8. **(P2)** `pre_tab.py` `_paste_*` — tolerancia de coma decimal Excel español (regla explícita de CLAUDE.md no implementada).
9. **(P3)** `mod06:246` — `redraw_overlays_only()` en el loop de animación.
10. **(P3)** Higiene: `compile_*.txt` fuera de git, README.md en raíz, `.gitattributes` para EOL de docs/vyv, tests faltantes en la lista "Running".

## Falsos positivos descartados (decisiones documentadas — NO tocar)

- `K.toarray()` en memoria_calculo (gated ≤12/≤24 GDL) y fallback denso del solver (backward-compat de tests).
- `subdivide_q4_mesh` sin consumidor activo, `remove_node` legacy, rama Toplevel defensiva del launcher, modo `bipolar` de QualityBar, `seek_*` de WebpPlayer, flag `zoomable` deprecado, setters `focus_mode`/`boundary_emphasis` — capacidad/API conservada por decisión.
- LUTs `coolwarm`/`turbo`/`viridis` definidos sin uso en resultados (jet es la única paleta de resultado por pedido del usuario; coolwarm/viridis viven en superficies pedagógicas M1/M2/M7).
- `tree.selection_set` en pre_tab/post_tab/health_report — ninguno está en el callback canvas→spreadsheet (lo único prohibido).
- Hex en docstrings (documentación de paleta), `#150` en hints de paste (sintaxis de coordenada), TSV del probe a precisión completa.
- `except Exception` masivos de education/figure_export/memoria — degradación defensiva de render documentada.
- `askyesnocancel` de "¿guardar cambios?" en main_window (lo prohibido era el modal del UnitsDialog, que no existe).
- det J lineal en Q9 de lados rectos, probe sobre malla deformada, sin selección de elementos en Post — decisiones de usuario documentadas.
- `_PDFProgressDialog` sin grab_set — documentado (el hallazgo 7 es la falta de snapshot, no el no-modal).

---

## Anexo: comando `/schedule`

Se creó `.claude/commands/schedule.md` con el prompt de esta auditoría, ampliado con: comparación contra auditorías previas (reincidencias/resueltos), seguridad y secretos, salud de dependencias, higiene de repo (artefactos, archivos grandes, TODO), y verificación de empaquetado PyInstaler/`resource_path`. Para ejecutarla recurrentemente: `/loop 8h /schedule` (no se dejó programado por defecto para no generar ramas de auditoría sin supervisión).
