# Estado del trabajo

**Última actualización**: 2026-09-07

> Lo primero que lee un agente al entrar. Qué está en curso, qué quedó a medias y qué
> decisión espera al autor. Se edita; lo que deja de aplicar se borra.
> Convención: [README.md](README.md).

## Contexto del proyecto

EduFEM está **funcional y empaquetado**: la GUI corre, el motor pasa su batería de tests,
hay `.exe` (`dist/EduFEM.exe`) e instalador (`installer/EduFEM.iss` → `EduFEM-Setup.exe`).
El trabajo activo no es construir features nuevas, sino **pulir** el software y **cerrar la
tesis** (`tesis/`, 130 páginas, compila limpio).

## En curso

| Tema | Dónde | Estado |
|---|---|---|
| Cierre de la tesis | `tesis/` | Compila limpio. Abiertas las 5 observaciones bloqueantes de la revisión del 2026-06-10 — ver [ESTADO_AUDITORIAS.md](../auditorias/ESTADO_AUDITORIAS.md) §*Abierto — revisión de la tesis*. Varias son **decisiones de autor**, no fixes mecánicos |
| Deuda técnica de la auditoría 2026-06-10 | repo | **Cerrada el 2026-09-06** (Top-10 + medios y bajos de §1, §2, §5 y §6). Único pendiente: decidir si se cablea `TheoryDoc.margin_formula()` en la memoria — cambia el layout del PDF, así que necesita validación visual del autor |
| Mejora continua del software | `docs/rutina/` | **Activa desde el 2026-09-08**: rutina horaria de claude.ai que trabaja directo sobre `main`, una área por sesión con rotación de 14. Qué hizo cada sesión: [../rutina/BITACORA.md](../rutina/BITACORA.md); qué falta y qué espera al autor: [../rutina/BACKLOG.md](../rutina/BACKLOG.md) |
| Distribución del `.exe` | `installer/` | Vía principal decidida: instalador Inno Setup por usuario, sin admin. Sin firma de código (decisión tomada) |

## Decisiones abiertas (esperan al autor)

- **Marco metodológico de la tesis** frente al canon del tribunal (UATF): objeto/campo,
  formulación del problema como interrogante, 3 vs. 4 capítulos, preliminares. Ver
  `tesis/README.md`.
- **Redundancia transversal** en la tesis y el criterio del 0,3 % en la validación contra
  SAP2000: pendientes de criterio del autor según la revisión del 06-10.
- **Validación visual del Post-Proceso y de la Memoria** tras la vectorización y tras la
  corrección de la extrapolación Q4 (2026-09-07): el autor debe abrir la GUI con el ejemplo
  canónico Q4 y con Cook 32×32 Q9 (gradiente, isolíneas, crudo, probe, 3D) y generar una
  Memoria de Cálculo. **Todas las tensiones nodales Q4 cambian** (el VM máximo del ejemplo
  canónico pasa de 977,46 a 864,70); Q9 no cambia. El diagrama de malla ya no rotula elementos
  demasiado chicos para el texto. **Sumar a esa validación** (rutina, sesión 04, 2026-09-08):
  la **Vista 3D en modo Crudo** —que hasta ahora dibujaba el campo transpuesto dentro de cada
  elemento— y su **nueva escala de color**. El detalle de qué mirar está en
  [../rutina/BACKLOG.md](../rutina/BACKLOG.md), *Pendientes visuales*.
- **Editar un material ya invalida la solución** (rutina, sesión 08, 2026-09-09). Hasta este
  commit, cambiar E, ν o ρ desde *Modelo ▸ Material* no ponía `is_solved = False`, así que
  `F5` cortaba con el fast-path de `post_tab._auto_solve` y devolvía **las tensiones del
  material anterior**, con *Exportar Memoria PDF* habilitado sobre esa corrida vieja. Si en
  algún momento se anotó un resultado después de tocar la librería de materiales **sin
  reabrir el proyecto**, ese número hay que regenerarlo. Las cifras de la tesis **no** están
  afectadas: salen de `tests/vv_*.py` y de `tesis/figuras/gen_anexo_calculo.py`, que arman el
  proyecto desde cero y no pasan por el diálogo.
- **Tesis, párrafo sobre el defecto corregido**: `04_resultados.tex` (§MMS, análisis) declara
  que la matriz E_Q4 estuvo mal hasta la revisión final y que por eso se agregó la prueba de
  reproducción polinómica. Es honestidad de V&V; el autor decide si lo conserva.
- **Validación del autor del TeX Live embebido (2026-09-08)**: (1) abrir la GUI y exportar
  una Memoria (Q4 canónico y Cook Q9, ambos estilos) y la Teoría MEF: debería verse idéntica
  a la de MiKTeX (mismas fuentes Latin Modern, mismo pdfTeX); (2) probar el instalador nuevo
  `installer/Output/EduFEM-Setup.exe` (126 MB) en una PC **sin MiKTeX** y, si se puede, con un
  usuario de Windows con tilde o espacio en el nombre (el instalador debe proponer
  `C:\ProgramData\EduFEM`); (3) decidir si sube `MyAppVersion` (1.0.0) en el `.iss`; (4) la
  tesis afirma en `06_anexos.tex` (Anexo A, párrafos "Es la vía recomendada…" y "El núcleo
  numérico…") que la Memoria requiere MiKTeX instalado: ya no es cierto, hay que reescribirlo.
- **Dictamen 2026-09-07** (artifact "Dictamen EduFEM"): quedan abiertos los hallazgos MAYOR y
  MENOR no mecánicos (objeto de estudio vs. población, hipótesis circular, preliminares,
  estado del arte, etc.). Los bloqueantes están cerrados (ver abajo).

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

- **2026-09-08** — **Bibliografía de la tesis auditada, saneada y con los vacíos cerrados**
  (23 entradas, todas con ≥2 citas; se retiró `oberkampf2010verification` y se sumaron las tres
  del **material docente de la carrera**, que estaba en `tesis/Material docente/` y es la fuente
  normativa que le faltaba al capítulo metodológico). La bibliografía **no** sobraba: el
  problema era de cobertura. Los demás huecos se cerraron **sin entradas nuevas** —
  redirigiendo a fuentes ya presentes, volviendo autosuficientes las afirmaciones (Cook 23,96
  por extrapolación propia; invariancia frente a $E$ en Timoshenko) y cambiando apelaciones a
  autoridad ausente por el argumento técnico. Ver
  [2026-09-08_bibliografia-tesis.md](2026-09-08_bibliografia-tesis.md). **Pendientes del
  autor**: confirmar el año 2024 de los dos PDF de Miranda, y decidir si los ocho PDF de
  `tesis/Material docente/` —material de cátedra ajeno, hoy trackeados en un repo público—
  se sacan de HEAD. Los localizadores de página siguen sin hacerse (requieren los libros).
- **2026-09-08** — **TeX Live recortado embebido: la Memoria y la Teoría ya no dependen de
  MiKTeX.** Motivo: en PCs de usuarios, MiKTeX básico abría un diálogo de instalación por cada
  paquete faltante (booktabs, tcolorbox, pgf, babel-spanish, listings…) y sin internet fallaba;
  medido con `pdflatex -recorder`, los cuatro documentos reales consumen 263 archivos (19,2 MB,
  de los que 13,3 MB son el `.fmt` de MiKTeX). Implementado: (a) `tools/build_texlive.py`
  genera `vendor/texlive` (gitignored) desde TinyTeX-0 v2026.09 (TeX Live 2026) + `tlmgr
  install` de la lista fija `PACKAGES` contra el snapshot `texlive.info/tlnet-archive/2026/09/07`
  + formato pdflatex con silabeo español + poda (Perl, Ghostscript, docs, OpenType, motores Lua)
  + `ls-R` regenerados; valida compilando Memoria Q4 educativo/directo, Memoria Q9 y Theory Hub
  antes y después de podar. Resultado: **50,9 MB / 4180 archivos**; el instalador pasa de 102 a
  **126 MB**. Hallazgos del build: `ec` es obligatorio (pylatex carga `fontenc[T1]` antes de
  `lmodern` y LaTeX pide `ecrm1095.tfm`), `l3backend` ya vive en `l3kernel`, y en TL 2026
  `pdflatex.exe` es un lanzador de 6 KB que carga `pdftex.dll`. (b) Nuevo
  `education/components/latex_runtime.py`: resuelve el compilador (`EDUFEM_TEXLIVE_DIR` →
  `texlive/` hermana del `.exe` o `vendor/texlive` → PATH, donde MiKTeX recibe
  `-enable-installer`), compila en un temporal con ruta ASCII sin ventana de consola, dos
  pasadas, y mueve el PDF al destino; `TheoryDoc.compile_to` y `TheoryViewer` pasan por ahí
  (adiós `Document.generate_pdf` y `latexmk`). La Memoria guarda sus figuras en ese `workdir` y
  las referencia por nombre relativo. (c) `installer/EduFEM.iss` copia `vendor/texlive` a
  `{app}\texlive`, y `[Code]` elige `C:\ProgramData\EduFEM` como carpeta por defecto si el
  perfil del usuario tiene tildes o espacios (TeX Live no resuelve rutas no ASCII).
  (d) `tools/build_all.ps1` arma el bundle si falta; LEEME, README, CLAUDE.md, MAPA, reglas y
  convenciones actualizados. Verificado: `test_memoria_calculo` 23/23 y nuevo
  `test_latex_runtime` 7/7 con el bundle (incluye PDF en destino con tilde y espacio), bundle
  copiado a otra ruta con espacio compila, `.exe` recompilado (`dist/EduFEM.exe`, 106 MB) e
  instalador compilado (`installer/Output/EduFEM-Setup.exe`). **Sin commit** (el autor revisa);
  pendientes del autor en *Decisiones abiertas*.
- **2026-09-07** — **Bug real corregido: extrapolación Q4 Gauss→nodos.** `fem/stress.py`
  tenía `_Q4_EXTRAP` escrita a mano para OTRO orden de puntos de Gauss que el que produce
  `get_gauss_points_2d(2)` ((-,-),(-,+),(+,-),(+,+)): columnas de los PG 3 y 4 intercambiadas,
  desde el primer commit (2026-02-27). No reproducía ni un campo lineal. Ahora Q4 y Q9 se
  construyen igual (`_build_extrapolation_matrix`: E = inv(M), M_ji = N_i(ξ_j, η_j) con los
  puntos reales). Copias a mano eliminadas en `file_io/memoria_calculo.py` y
  `tesis/figuras/gen_anexo_calculo.py` (fuente única `fem.stress.extrapolation_matrix`).
  Guard: `tests/test_vv_extensions` [7/7] exige reproducción exacta de campos polinómicos en Q4 y
  Q9. Por qué nadie lo vio: el MMS mide desplazamientos, Timoshenko usa Q9, Cook mide flecha; y en
  mallas finas uniformes los errores nodales se cancelan por simetría (en el ejemplo canónico de 4
  elementos el VM de algunos nodos estaba 2–4× mal). Regresión 81/81 OK, batería completa en verde.
  **MMS ampliado** (`tests/vv_mms.py`): 4 configuraciones {unitario, distorsionado} ×
  {tensión plana, deformación plana} + norma L² del campo de tensiones recuperado
  (`fem.error_norms.compute_stress_recovery_error`); tasas: desplazamiento teóricas en las 4;
  σ* O(h^1,5) Q4 / O(h²) Q9. CSV nuevos `mms_*_{dist_tp,unif_dp,dist_dp}.csv` + `mms_resumen.csv`;
  figura `mms_convergence_stress.png`. **Tesis**: Anexo G regenerado (`anexo_calculo_data.tex`,
  `mem_contorno_vm.png`); eq:extrap-q4 con el orden real de PG; cotas de error honestas ("0,05 %
  en tensiones" → 0,04 % en σx, 2,9 % en τxy, 0,26 % flecha; vs SAP2000 0,21 %/0,56 %); Barlow
  corregido para Q9; regla "p+1" → "un punto más por dirección"; criterios de aceptación explícitos
  en §2.1; tab:mms con columna σ*, nueva tab:mms-configs y fig:convergencia-tension; tabla de
  componentes de Timoshenko con columna de error.
  **Segunda tanda del mismo día**: (1) **von Mises correcto en deformación plana** en todas las
  rutas (`fem/batch.py::principal_and_vm_batch(stress, sigma_z)`, `out_of_plane_factor`,
  `sigma_z_from`; `fem/stress.py`; `fem/probe_query.py` raw/smooth/grids; memoria; oráculo
  de regresión) con `sigma_z = nu (sx+sy)`; guard `test_vv_extensions` [8/8]; eq:principales-vm
  de la tesis con `\sigma_z`. (2) **Jacobiano escalado por FILAS** (tangentes) en
  `fem/mesh_quality._jacobian_samples` (antes columnas: cantidad distinta); tesis: eq:jacobiano
  con la convención del motor (filas ξ,η), eq:scaled-jacobian por filas, umbrales Verdict vs.
  UI y estado de 4 métricas documentados. (3) **Cook**: `U_Y_REF = 23.96` en `vv_cook.py`
  (antes 23.95), CSV/figura regenerados, tabla y textos con los errores nuevos e incertidumbre
  de la referencia (Richardson ≈ 23,97). (4) **`tests/bench_timing.py`** mide COLAMD vs
  MMD_AT_PLUS_A (1,7×/2,0×/2,9× a 2178/8450/33 282 GDL); tab:tiempos remedida hoy. (5) Nuevo
  **`tests/test_interop.py`** (CSV/ZIP ida y vuelta + DXF idempotente) citado en §3.3 y en
  tab:vyv-repro (objetivo 5 con evidencia). (6) Mecánicos: portada con tildes, `\markboth` en
  Introducción/Resumen/Conclusiones, `\appendixautorefname` vía `\extrasspanish` (ya no
  "Apéndice"), `sec:metodologia`, artículos ante `\autoref{eq:}`, "Cap. 3", palabras clave 6,
  bib (organization {{}}, Lee = "Jae Young Lee" + Ryu, issue 2 y 5, {van der Walt}), 21,32 GPa y
  origen de E, pdflatex en Anexo A, fila `orphan_free_node`, DXF→Q9 automático y unidades,
  Anexo G "condensada", rango 0..2N−1, Anexo E en la lista de anexos, doble "variable
  independiente", PyMuPDF, CALFEM, cobertura del canal. Compila limpio, 128 páginas. Batería
  completa en verde (regresión 81/81, vv_extensions 8/8, interop, fem, memoria 23/23, probe,
  canvas). **Sin commit** (el autor revisa).
  **Tercera tanda (pedido del autor)**: §2.1 reestructurado de 10 subtítulos de diseño
  experimental (control, repetición, protocolo…) a 6 que siguen el diagrama del Taller 4 del
  tribunal (modelo de simulación numérica · variables · matriz de consistencia · casos de
  estudio y criterio de selección · procedimiento, instrumentos y reproducibilidad · criterios
  de aceptación y contraste de la hipótesis); la parte de software pasó a ser §2.2 «Diseño e
  implementación de EduFEM» con sus antiguas secciones como subsecciones (2.2.1–2.2.9).
  Etiquetas conservadas: `sec:metodologia`, `sec:proceso-met`, `sec:variables-met`,
  `sec:matriz-consistencia`, `sec:poblacion`, `sec:validacion-datos`,
  `sec:validacion-resultados`; nueva `sec:diseno-edufem`; borradas (sin referencias)
  `sec:hipotesis-met`, `sec:sistema-control`, `sec:sistema-repeticion`,
  `sec:protocolo-calculo`. Frases de la Introducción que enumeraban los subtítulos viejos
  actualizadas. Compila limpio, 127 páginas.
  **Cuarta tanda (2026-09-08, pedido del autor tras analizar el material del tribunal):**
  coherencia Introducción ↔ Cap. 2 ↔ Cap. 3 ↔ Conclusiones según el esquema
  problema–objeto–campo–objetivo–hipótesis–tríada. (a) **Objeto de estudio técnico** («el
  análisis de medios continuos en elasticidad lineal plana por el MEF») y **campo de acción
  pedagógico** («su enseñanza: el software que expone el canal y la memoria»), como en el
  ejemplo del propio catedrático (objeto = losas, campo = costos); así población, variables y
  resultados quedan dentro del objeto. (b) **Problema científico** reformulado como
  respondible: VI = forma de exponer el canal (transparencia, interactividad,
  verificabilidad); VD = observabilidad y contrastabilidad del procedimiento; «apoyo a la
  comprensión» pasa a ser el para qué. (c) **Delimitación** institucional (Carrera de Ing.
  Civil UATF como destinataria), espacial (aula y equipo del estudiante), temporal (gestión
  2026) y disciplinar. (d) **Sexto objetivo específico**: nuevo OE1 «Fundamentar
  teóricamente…» (cubre el Cap. 1) + fila en `tab:consistencia`; el instrumental pasa a ser
  el sexto (01, 02b, 04:95, 05). (e) **Hipótesis**: puente de tres variables en la intro,
  coherente con las variables del problema. (f) **Tríada**: cada conclusión nombra su
  capítulo; conclusión nueva para el Cap. 1; recomendaciones ancladas por capítulo + nueva
  «Ampliación de la batería de validación» (caso civil en deformación plana). (g) §3.8
  responde explícitamente al problema y al objeto. Compila limpio, 130 páginas. Sin commit.
- **2026-09-06** — **Cerradas las tres decisiones abiertas del post-proceso.**
  (a) **Invariantes nodales**: σ1, σ2 y von Mises ya no se extrapolan ni se promedian; se
  extrapolan y promedian las tres componentes cartesianas y las invariantes se recomputan desde
  ellas (`fem/stress.py` + `fem.batch.principal_and_vm_batch`). Las componentes no cambian ni un
  bit y **ningún CSV de V&V se movió**; sí cambia el VM nodal mostrado: +3,0 % en el máximo de
  Cook Q9 32×32 y +8,3 % en el ejemplo canónico. Corrige una incoherencia real — el nodo 8 del
  Anexo F mostraba VM = 8,96 con σx = −54,23, σy = −11,55 y τxy = −84,65, cuyo VM coherente con
  esas componentes es 154,74 (componentes que, a su vez, eran incorrectas por el bug de
  extrapolación Q4 corregido el 2026-09-07; hoy el nodo 8 da σx = 39,34, σy = −74,16,
  τxy = 107,67, VM = 211,52). El marco teórico de la tesis (§2, extrapolación) **ya describía este comportamiento**;
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
