# Roadmap incremental del motor FEM

> Capitulo del canon de EduFEM. Indice: [../../CLAUDE.md](../../CLAUDE.md) - mapa del repo: [../MAPA.md](../MAPA.md) - prohibiciones: [no-reintroducir.md](no-reintroducir.md).

**Leelo antes de optimizar** `fem/assembly.py`, `fem/batch.py`, `fem/solver.py` o `fem/stress.py`.

---

### Estado del motor (2026-09-06)

API pública `solve_system(project) → dict` queda fija para no obligar a tocar `post_tab`, `file_io/memoria_calculo.py`, M5.

**Dos versiones de la misma formulación, y las dos se conservan**:

- **Legible, elemento a elemento y punto a punto**: `fem/shape_functions.py`, `fem/jacobian.py`, `fem/b_matrix.py`, `fem/constitutive.py`, `fem/stiffness.element_stiffness` (ke con todos los intermedios por punto de Gauss) y `fem/stress.compute_element_stresses`. Es la referencia pedagógica de M1..M5/M7 y de la memoria de cálculo, y el **oráculo** de `tests/test_solver_regression.py`. El solve productivo **no** pasa por ella.
- **Vectorizada por lotes** (`fem/batch.py`): `gather_elements` (conectividad, coordenadas, GDL vía `node_index_map`, D por elemento), `geometry_at_points` (J, det J y B de todos los elementos × puntos con `einsum`), `stiffness_batch` (un único `matmul` apilando los puntos de Gauss), `assemble_sparse` (COO → CSR), `body_force_batch` y `stress_at_points`. La consumen `fem/assembly.py`, `fem/stress.compute_all_stresses`, `fem/probe_query.compute_raw_grids` y `fem/mesh_quality`. Es NumPy puro: corre igual en el `.exe` que en el repo.

Ítems del roadmap (todos implementados salvo 5 y 6):

1. **K sparse** — ✅ `assemble_sparse`: tripletes COO por lote (`np.repeat`/`np.tile` sobre `dofs (e, 2n)`) → `coo_matrix(...).tocsr()`. K nunca se materializa densa (memoria O(nnz)); el único `K.toarray()` vive en el módulo educativo M7.
2. **Solver SPD sparse** — ✅ `fem/solver._solve_reduced`: `scipy.sparse.linalg.spsolve` (SuperLU) sobre K_red en **CSC** con `permc_spec=SOLVER_PERMC_SPEC` (`"MMD_AT_PLUS_A"` en `config/settings.py`): ordenamiento de mínimo grado sobre Aᵀ + A, que aprovecha la simetría de K. Frente al default COLAMD: 2178 GDL 14,3 → 9,1 ms (1,6×); 8450 GDL 128 → 61 ms (2,1×); 33 282 GDL 888 → 421 ms (2,1×), con |Δu| ~ 3e-11. Cholesky (`scikit-sparse`) y UMFPACK quedan fuera: dependencias binarias sin ganancia clara sobre MMD.
3. **RCM** — ❌ **eliminado el 2026-09-06**. Medido contra el mismo solve sin permutar: pierde por debajo de ~8500 GDL (a 2178 GDL cuesta ~2 ms extra; a 50 GDL duplica el tiempo) y recién gana 7–19 % por encima (25 538 GDL: 288 → 234 ms). Esas decenas de milisegundos son invisibles en mallas donde el resto de la app tarda segundos, así que la rama de permutación y sus dos constantes se borraron. El ordenamiento de mínimo grado del ítem 2 ya se llevó la ganancia grande. Ver [no-reintroducir.md](no-reintroducir.md).
4. **Ensamblaje y post-proceso vectorizados por lotes** — ✅ **Implementado el 2026-09-06** en `fem/batch.py`; reemplazó a los kernels `@njit` de numba, que en el `.exe` (sin numba) corrían como loops escalares en Python puro. Membrana de Cook Q9 32×32 (1024 elementos, 8450 GDL), sin numba: ensamblaje 3,35 s → 0,054 s; tensiones 0,50 s → 0,06 s; contorno crudo 2,95 s → 0,04 s. A 33 k GDL el solve completo tarda 0,73 s. La tabla completa sale de `tests/bench_timing.py` y está en la tesis (`tab:tiempos`). El canvas tiene su análogo en `gui/preprocessing/canvas_raster.py` (rasterizado e isolíneas por lotes, paridad píxel a píxel con `tests/test_canvas_raster.py`), que desde el 2026-09-06 reusa también `file_io/figure_export._fill_field`: el contorno de la memoria de cálculo pasó de 16,7 s a 0,51 s en 1024 elementos (47,6 s → 1,26 s en 4096), con 0 píxeles distintos.
5. **Cache de B/J por shape signature** (baja): innecesario tras el lote; solo si un perfil muestra que `geometry_at_points` domina (hoy domina `spsolve`).
6. **SRI / B-bar para volumetric locking** (baja, alto valor pedagógico): opt-in vía `Material.use_sri`. Excelente para un módulo M10 "Locking volumétrico".

**Reglas transversales**:
- **Pureza `fem/`**: cero imports de tk/matplotlib/ttkbootstrap. Debe correr sin GUI.
- **Sin numba ni JIT** (decisión 2026-09-06): el rendimiento sale de vectorizar por lotes en NumPy, no de compilar. Un kernel escalar "pensado para numba" es el peor código posible cuando numba no está, que es el caso del `.exe` (onefile extrae a una carpeta aleatoria y el cache del JIT nunca acierta). Si algo es lento, el camino es `fem/batch.py`, o un helper NumPy análogo en `gui/preprocessing/canvas_raster.py` para el canvas.
- **Contrato de `element_data`**: `assemble_global_system` retorna un `ElementData` (dict `{elem_id: {ke, dof_indices, node_coords, B, det_J}}` con vistas) más el atributo `.batch` (`ElementBatch`). El post-proceso lee `.batch`; la memoria de cálculo y los scripts de la tesis leen el dict.
- **Tipado**: `from __future__ import annotations` + type hints en firmas públicas.
- **Tolerancias centralizadas**: `NUMERICAL_TOLERANCE = 1e-10`, `JACOBIAN_MIN_DETERMINANT = 1e-12` de settings. No introducir tolerancias locales ad-hoc.
- **Regresión numérica**: cualquier cambio en `assembly` / `batch` / `solver` / `stress` debe pasar `python -m tests.test_solver_regression` (motor por lotes contra la versión legible, error relativo ≤ 1e-9) y `python -m tests.test_fem`.
- **Invariantes nodales**: `σ₁`, `σ₂` y von Mises **nunca** se extrapolan ni se promedian. Se extrapolan y promedian las tres componentes cartesianas y las invariantes se recomputan desde ellas (`fem.batch.principal_and_vm_batch`), porque son funciones no lineales. Hacerlo al revés daba un VM nodal hasta 8 % distinto e incoherente con la propia fila de componentes y con el probe.
- **Profiling antes de optimizar**: `cProfile` sobre `tests/bench_timing.build_project(32, ELEMENT_Q9)`. Hoy el costo está en `spsolve` (factorización); ensamblaje y tensiones suman ~0,1 s a 8450 GDL. En el PDF de la memoria el costo dominante ya no es el motor sino Pillow: `render_mesh_diagram` hace una llamada de dibujo por elemento (0,83 s en 1024 elementos).
- **Compatibilidad con M2/M3/M5**: si añadís una variante optimizada, exponer también la legible. **No** sacrificar claridad pedagógica por velocidad.
