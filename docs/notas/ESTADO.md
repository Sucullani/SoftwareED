# Estado del trabajo

**Última actualización**: 2026-09-06

> Lo primero que lee un agente al entrar. Qué está en curso, qué quedó a medias y qué
> decisión espera al autor. Se edita; lo que deja de aplicar se borra.
> Convención: [README.md](README.md).

## Contexto del proyecto

EduFEM está **funcional y empaquetado**: la GUI corre, el motor pasa su batería de tests,
hay `.exe` (`dist/EduFEM.exe`) e instalador (`installer/EduFEM.iss` → `EduFEM-Setup.exe`).
El trabajo activo no es construir features nuevas, sino **pulir** el software y **cerrar la
tesis** (`tesis/`, ~102 páginas, compila limpio).

## En curso

| Tema | Dónde | Estado |
|---|---|---|
| Cierre de la tesis | `tesis/` | Compila limpio. Abiertas las 5 observaciones bloqueantes de la revisión del 2026-06-10 — ver [ESTADO_AUDITORIAS.md](../auditorias/ESTADO_AUDITORIAS.md) §*Abierto — revisión de la tesis*. Varias son **decisiones de autor**, no fixes mecánicos |
| Deuda técnica de la auditoría 2026-06-10 | repo | **Cerrada el 2026-09-06** (Top-10 + medios y bajos de §1, §2, §5 y §6). Único pendiente: decidir si se cablea `TheoryDoc.margin_formula()` en la memoria — cambia el layout del PDF, así que necesita validación visual del autor |
| Distribución del `.exe` | `installer/` | Vía principal decidida: instalador Inno Setup por usuario, sin admin. Sin firma de código (decisión tomada) |

## Decisiones abiertas (esperan al autor)

- **Marco metodológico de la tesis** frente al canon del tribunal (UATF): objeto/campo,
  formulación del problema como interrogante, 3 vs. 4 capítulos, preliminares. Ver
  `tesis/README.md`.
- **Redundancia transversal** en la tesis y el criterio del 0,3 % en la validación contra
  SAP2000: pendientes de criterio del autor según la revisión del 06-10.
- **Validación visual del Post-Proceso y de la Memoria** tras la vectorización: el autor debe
  abrir la GUI con Cook 32×32 Q9 (gradiente, isolíneas, crudo, probe, 3D) y generar una Memoria
  de Cálculo. El contorno del PDF cambió de valor en σ1/σ2/VM nodales (ver abajo) y el diagrama
  de malla ya no rotula elementos demasiado chicos para el texto.

## Convenciones que conviene tener presentes

- El canon está partido: [../../CLAUDE.md](../../CLAUDE.md) tiene las reglas duras y el
  ruteo; el detalle vive en [../convenciones/](../convenciones/) y se lee **según lo que
  vayas a tocar**.
- Antes de agregar algo que "falta", pasá por
  [no-reintroducir.md](../convenciones/no-reintroducir.md): la mayoría de las ausencias son
  decisiones tomadas.
- Rutas que no se pueden mover: [../MAPA.md](../MAPA.md) §3.
- La validación **visual** la hace el autor abriendo la GUI. Un agente puede correr smoke
  tests headless (`MainWindow` + `root.withdraw()`, sin `mainloop`), pero no debe declarar
  que algo "se ve bien".

## Hecho recientemente

- **2026-09-06** — **Cerradas las tres decisiones abiertas del post-proceso.**
  (a) **Invariantes nodales**: σ1, σ2 y von Mises ya no se extrapolan ni se promedian; se
  extrapolan y promedian las tres componentes cartesianas y las invariantes se recomputan desde
  ellas (`fem/stress.py` + `fem.batch.principal_and_vm_batch`). Las componentes no cambian ni un
  bit y **ningún CSV de V&V se movió**; sí cambia el VM nodal mostrado: +3,0 % en el máximo de
  Cook Q9 32×32 y +8,3 % en el ejemplo canónico. Corrige una incoherencia real — el nodo 8 del
  Anexo F mostraba VM = 8,96 con σx = −54,23, σy = −11,55 y τxy = −84,65, cuyo VM verdadero es
  154,74. El marco teórico de la tesis (§2, extrapolación) **ya describía este comportamiento**;
  ahora el código lo cumple. `tesis/figuras/anexo_calculo_data.tex` regenerado con
  `gen_anexo_calculo.py`.
  (b) **RCM eliminado**: medido, solo gana por encima de ~8500 GDL (7–19 %) y por debajo pierde;
  a ese tamaño el resto de la app tarda segundos. Se borraron `SOLVER_USE_RCM`,
  `SOLVER_RCM_MIN_DOF` y la rama de permutación. Queda `SOLVER_PERMC_SPEC = "MMD_AT_PLUS_A"`,
  remedido: 1,6× a 2178 GDL y 2,1× a 8450 y 33 282 GDL (la constante citaba mal la malla).
  Menciones a RCM quitadas de la tesis (nomenclatura, marco teórico, conclusiones).
  (c) **`figure_export._fill_field` vectorizado** sobre `canvas_raster.rasterize_triangles`:
  el contorno de la memoria pasó de 16,7 s a 0,51 s en 1024 elementos y de 47,6 s a 1,26 s en
  4096, con **0 píxeles distintos** (`test_canvas_raster.test_figure_export_field`). En el
  ejemplo canónico de 4 elementos hay una regresión de ~100 ms (155 → 245 ms) por el overhead
  del camino por lotes: irrelevante frente a los segundos de `pdflatex`. `render_mesh_diagram`
  ya no rotula elementos más chicos que el texto (ilegibles y caros): 1,65 s → 0,83 s en 1024
  elementos. Lo que queda caro ahí es Pillow, una llamada de dibujo por elemento.

- **2026-09-06** — **Motor vectorizado por lotes y retiro de numba.** Nuevo `fem/batch.py`
  (geometría J/det J/B, rigidez, scatter COO y tensiones de todos los elementos a la vez con
  `einsum`/`matmul`); `fem/assembly.py`, `fem/stress.py`, `fem/probe_query.compute_raw_grids`,
  `fem/mesh_quality` y `fem/error_norms` lo usan. Solucionador con `SOLVER_PERMC_SPEC =
  "MMD_AT_PLUS_A"` (SuperLU sobre CSC). Canvas: `gui/preprocessing/canvas_raster.py`
  (rasterizado Gouraud e isolíneas vectorizados, paridad píxel a píxel). Borrados
  `fem/_numba_compat.py`, los 17 kernels `@njit` y el warm-up de numba; `build.spec` excluye
  `numba`/`llvmlite`. Motivo: el `.exe` nunca tuvo numba (onefile extrae a una carpeta
  aleatoria y el cache del JIT jamás acertaba) y los kernels escalares corrían en Python puro.
  Cook Q9 32×32 (8450 GDL) sin numba: ensamblaje 3,35 s → 0,054 s, tensiones 0,50 s → 0,06 s,
  contorno crudo 2,95 s → 0,04 s, isolíneas 51 s → ~0,1 s; 33 k GDL: solve 0,73 s (antes 2,2 s
  con numba). Versión legible de `fem/` intacta como oráculo de `tests/test_solver_regression.py`
  (81 checks ≤ 1e-9); `tests/test_canvas_raster.py` (paridad); batería completa y V&V en verde
  con CSV idénticos; tabla `tab:tiempos` de la tesis regenerada. **Pendiente del autor:
  validación visual** del Post-Proceso (gradiente, isolíneas, crudo, probe, 3D) — debería verse
  idéntico y responder en < 1 s en Cook 32×32 Q9 — y rebuild del `.exe` + instalador.
- **2026-09-06** — Reorganización del repositorio y espacio de trabajo para agentes:
  `docs/` estructurado (`convenciones/`, `notas/`, `auditorias/`, `teoria/`), auditorías
  consolidadas, `CLAUDE.md` reducido de 909 a ~230 líneas, `README.md` y `AGENTS.md`
  creados, insumos de distribución movidos a `installer/dist_extra/`. Detalle:
  [2026-09-06_reorganizacion-repo.md](2026-09-06_reorganizacion-repo.md).
- **2026-09-06** — Segunda tanda de la auditoría 2026-06-10 (medios y bajos): traza en los
  listeners de undo y en el error de `auto_solve`; guard de `det J` en `error_norms`; el
  snapshot de undo del cambio Q4↔Q9 pasó a después del `askyesno`; guards de `winfo_exists`
  en los `after()` de tres diálogos; `memoria_style_dialog` y `about_dialog` usan
  `center_dialog`; tolerancias `1e-10` reemplazadas por `NUMERICAL_TOLERANCE`; eliminados
  5 constantes sin consumidor, `highlight_node`/`highlight_element` y 6 llamadas redundantes
  a `_refresh_menu_state`; comentarios de paleta y de módulos M8/M9 corregidos;
  `recompute_q9_midnodes` por índice inverso; `test_draw_mode` con guard de Tk.
- **2026-09-06** — Cerrado el Top-10 de la auditoría 2026-06-10. P0: `change_element_id`
  ahora sincroniza `_node_to_elements` (reg. en `test_node_cascade`) y `assembly` ignora la
  carga nodal huérfana en vez de romper el solve. P1: autofix de cargas superficiales por
  identidad de objeto; `_check_orphan_free_nodes` nuevo (con autofix e hint) y
  `nodes_in_elements` deja de contar los sets vacíos que `remove_element` deja al preservar
  huérfanos. P2: `capture()` antes de los autofixes, snapshot inmutable del project para el
  worker del PDF, y `to_float_flex` para la coma decimal de Excel. P3: `mod06` usa
  `redraw_overlays_only()`; `.gitattributes` creado. Batería completa + V&V en verde.
- **2026-09-06** — Auditoría del canon de instrucciones: corregidas 21 afirmaciones obsoletas
  en `docs/convenciones/` (orden `Ctrl+1..7` que daba `D, B` en vez de `B, D`; chips
  `Q4 · 8 DOF` → `GDL`; `AnalysisTypeDialog` con dos videos inexistentes y la matriz D
  atribuida a M3; fallback a `simpledialog`, botón Reset y sub-pestaña de Educación en el Post,
  los tres inexistentes; contrato `BaseEducationalModule` / `GaussCoordReadout` descrito en
  presente; bullet duplicado en M4; `pdf_report`). `CLAUDE.md` 229 → 187 líneas quitando
  duplicación interna, y `.claude/rules/` (5 archivos con `paths:`) hace que cada capítulo se
  cargue solo al tocar su área.
- **2026-06-10** — Auditoría general del repo + revisión profesional de la tesis
  (diagnóstico, sin fixes) y comando `/schedule`.
- **2026-06-01** — Implementadas las recomendaciones P0–P2 de la auditoría integral del
  2026-05-31 (incluido el bug de `node_index_map` stale).
