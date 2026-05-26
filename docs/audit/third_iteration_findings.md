# EduFEM — Tercera iteración de rendimiento (iter3)

**Fecha:** 2026-05-26  
**Branch:** `claude/perf-iter3-speed` (base: `claude/perf-iter2-postproc`)  
**Modelo de referencia:** Q4 4800 elem / 4961 nodos / 9922 GDL, Q9 200 elem / 861 nodos / 1722 GDL

---

## Lo que hizo iter2 (verificado en PR #3)

iter2 atacó el hot path del solver y la GUI. Los cambios principales, verificados en el branch base:

| Área | Cambio iter2 | Impacto medido |
|------|-------------|----------------|
| **Solver** | `scipy.sparse.linalg.spsolve` sobre K CSR (antes K denso + `scipy.linalg.solve`) | Factor 10-100× en mallas grandes — el cambio más grande de iter2 |
| **Ensamblaje K** | K ensamblado vía acumuladores COO (`coo_rows/cols/data`) → `coo_matrix.tocsr()` con sum-duplicates automática | Elimina O(n²) scatter en Python; memoria proporcional a nnz |
| **`node_index_map`** | Property cacheada `{node_id → índice ordinal 0..N-1}` (antes recomputada en cada `get_dof_indices`) | ~O(N) lookup eliminado por elemento |
| **GUI Post** | Cache del contorno de resultados en `post_tab`; imports diferidos de matplotlib | Redibujado O(1) si los datos no cambiaron |
| **Lectura DXF** | `_require_ezdxf()` import diferido | Inicio más rápido |

**Lo que iter2 NO tocó:** el cálculo de esfuerzos (`fem/stress.py`), que según el profiling previo a iter3 consumía 1.226s de los 2.535s totales en Q4 — casi el 50% del runtime.

---

## Top-5 hallazgos del profiling iter3 (BEFORE)

Profiling con `cProfile`, 5 runs, Q4 4800 elementos (ver `third_iteration_profile.txt` para datos completos).

### #1 — `compute_element_stresses`: 4.595s / 5 runs (24,000 llamadas)

**Causa raíz:** `compute_all_stresses` recalculaba desde cero las matrices B, J, dN para cada elemento en la fase de esfuerzos — exactamente el mismo trabajo que ya hizo `element_stiffness` durante el ensamblaje. Las matrices B están almacenadas en `element_data["gauss_data"]` desde iter2, pero `stress.py` no las reutilizaba.

**Coste real:** 4× llamadas a `compute_b_matrix` + 4× `compute_jacobian` + 4× `dshape_functions_q4` por elemento → 192,000 llamadas redundantes en 5 runs.

### #2 — `np.mean` en promedio nodal: 1.435s / 5 runs (148,830 llamadas)

**Causa raíz:** `compute_all_stresses` llamaba `np.mean(values)` para promediar esfuerzos en nodos compartidos. `np.mean` sobre una lista Python de 1-4 floats tiene ~10µs de overhead de dispatch (conversión a ndarray, validación de dtype, reducción genérica). Con ~148,000 llamadas el overhead acumula ~1.4s.

### #3 — `meshgrid` + `broadcast_arrays`: 1.343s / 5 runs (24,000 llamadas)

**Causa raíz:** el ensamblaje COO usaba `np.meshgrid(idx, idx, indexing="ij")` para construir el producto exterior de índices. `meshgrid` delega en `broadcast_arrays` que llama `stride_tricks._broadcast_to` (dos niveles de dispatch). Para un vector de 8 elementos (Q4 tiene 8 GDL), esto es más overhead de Python que datos útiles.

### #4 — `get_gauss_points_*`: 0.977s / 5 runs (48,000 llamadas)

**Causa raíz:** `get_gauss_points_for_element` y `get_gauss_points_2d` se llamaban una vez por punto de Gauss por elemento, tanto en `element_stiffness` como en `compute_element_stresses`. Cada llamada recomputaba el producto tensorial de los puntos 1D — trabajo idéntico en 48,000 invocaciones.

### #5 — `extrapolate_to_nodes_q4`: 1.211s / 5 runs (24,000 llamadas)

**Causa raíz:** la función extrapolaba 6 componentes de esfuerzo con 6 productos matriciales separados (`E_mat @ gauss_values` por componente). La matriz de extrapolación 4×4 se reconstruía en cada llamada con `_build_q4_extrap()`.

---

## Implementación (qué se hizo)

### P1 — Reutilización de matrices B precalculadas (`fem/stress.py`)

Nueva función `_gauss_stresses_from_precomputed(gauss_data_list, u_elem, D)` que lee `B` directamente del `gauss_data` almacenado por `element_stiffness`. Elimina las 96,000 llamadas redundantes a `compute_b_matrix`, `compute_jacobian` y `dshape_functions_q4` en la fase de esfuerzos.

`compute_all_stresses` usa este path cuando `"B"` está en `gauss_data[0]` (siempre en flujos normales); el path lento con `compute_element_stresses` queda como fallback para compatibilidad retroactiva con `element_data` construido manualmente en tests.

También se agrega `D_cache` indexado por `(E, nu, analysis_type)` — cuando un mismo material se asigna a muchos elementos (caso habitual), la matriz constitutiva D se computa solo una vez en lugar de N veces.

**Speedup esfuerzos Q4: 1226ms → 374ms (3.27×)**

### P2 — Eliminación de `np.mean` en promedio nodal (`fem/stress.py`)

Reemplaza `np.mean(values)` por `sum(values) / len(values)` en el loop de promedio nodal. Las listas tienen 1-4 elementos (nodos compartidos entre 1-4 elementos en mallas estructuradas); el overhead de dispatch numpy domina el trabajo real.

**Speedup promedio nodal: 1.435s → ~0ms (eliminado del top 30)**

### P3 — Sustitución de `meshgrid` por `repeat`/`tile` (`fem/assembly.py`)

El producto exterior de índices `(idx × idx)` para el triplete COO se construía con `np.meshgrid(idx, idx, indexing="ij")`. Reemplazado por:
```python
coo_rows.append(np.repeat(idx, n_e))   # [i0,i0,...,i1,i1,...] (n_e²)
coo_cols.append(np.tile(idx, n_e))     # [j0,j1,...,j0,j1,...] (n_e²)
```
`repeat` y `tile` son operaciones directas sin el overhead de `broadcast_arrays`.

**Speedup ensamblaje Q4: 1141ms → 869ms (1.31×)**

### P4 — Cache de módulo para puntos de Gauss (`fem/gauss_quadrature.py`)

`get_gauss_points_2d` y `get_gauss_points_for_element` ahora cachean sus resultados en dicts de módulo (`_GAUSS_2D_CACHE`, `_GAUSS_FOR_ELEM_CACHE`). Las funciones se llaman una vez por configuración de integración y retornan el mismo par de arrays en todas las llamadas posteriores.

**Speedup: 0.977s → ~0ms (eliminado del top 30 en AFTER)**

### P5 — Extrapolación vectorizada con matmul único (`fem/stress.py`)

Las matrices de extrapolación `_Q4_EXTRAP` (4×4) y `_Q9_EXTRAP_MATRIX` (9×9) se precomputan como constantes de módulo. La extrapolación pasa de 6 productos vector separados a un único matmul:

```python
gauss_mat = np.array([[gs[k] for k in _STRESS_KEYS] for gs in gauss_stresses])  # (4, 6)
nodal_mat = _Q4_EXTRAP @ gauss_mat  # (4, 6) — un solo matmul
```

**Speedup extrapolación Q4: 1.211s → 0.557s (2.17×)**

### P6 — Índice inverso `_node_to_elements` (`models/project.py`)

Nuevo dict `{node_id: set[elem_id]}` mantenido incrementalmente en `add_element`, `remove_element`, `change_node_id`. Los tres métodos que antes hacían scan O(E) ahora son O(1):

- `is_node_referenced`: `bool(self._node_to_elements.get(node_id))`
- `remove_element` (check de huérfanos): `bool(self._node_to_elements.get(nid))`
- `remove_node_with_cascade`: `list(self._node_to_elements.get(node_id, set()))`

El índice se reconstruye en `from_dict` y `restore_from_dict`. Para mutaciones directas de `elem.node_ids` en `mesh_utils.py` (`expand_q4_to_q9`, `shrink_q9_to_q4`), se llama `project.rebuild_node_to_elements()` al final del loop.

**Impacto:** operaciones de borrado cascade con mallas grandes pasan de O(E) a O(1) en el check de huérfanos.

### P7 — Shoelace inlineado en `_check_negative_jacobians` (`models/model_health.py`)

El loop Python `for i in range(4)` se desenrolló explícitamente en 4 multiplicaciones cruzadas:

```python
p0, p1, p2, p3 = pts
area2 = (p0.x * p1.y - p1.x * p0.y
       + p1.x * p2.y - p2.x * p1.y
       + p2.x * p3.y - p3.x * p2.y
       + p3.x * p0.y - p0.x * p3.y)
```

La vectorización numpy (`np.roll` + `np.sum` sobre array `(N,4,2)`) se intentó pero fue **más lenta** (15.28ms vs 10.55ms baseline) porque construir el array requiere N lookups en `project.nodes`, que es Python puro. El inline sin numpy logra 7.01ms.

**Speedup validate_project: 10.55ms → 6.80ms (1.55×)**

---

## Mediciones antes/después

| Métrica | ANTES (iter2) | DESPUÉS (iter3) | Speedup |
|---------|---------------|-----------------|---------|
| Q4 total (solve + stress) | 2535ms | 1413ms | **1.79×** |
| Q4 stress | 1226ms | 374ms | **3.27×** |
| Q4 assembly | 1141ms | 869ms | **1.31×** |
| Q9 total (solve + stress) | 304ms | 202ms | **1.51×** |
| Q9 stress | 142ms | 46ms | **3.08×** |
| validate_project (Q4, 4800 elem) | 10.6ms | 6.8ms | **1.55×** |
| Llamadas totales cProfile Q4 (5 runs) | 7,594,906 | 3,831,046 | -49.6% |

El número de llamadas casi se redujo a la mitad: el mayor factor fue eliminar las 192,000 llamadas a `compute_b_matrix`/`compute_jacobian`/`dshape_functions_q4` redundantes en la fase de esfuerzos.

---

## Qué se difirió y por qué

### Ensamblaje vectorizado con `einsum` (P6 original)

Un `np.einsum("egki,kl,eglj,eg,g->eij", B_batch, D, B_batch, det_J, w)` batch eliminaría el loop Python por elemento en `element_stiffness`. No se implementó por:

1. **Complejidad de refactor:** `element_stiffness` es consumido directamente por M5 (`education/mod05_stiffness.py`) que necesita la versión escalar por-Gauss-point para la visualización pedagógica del integrando. El refactor requiere mantener ambas versiones y añadir un flag o un módulo paralelo en `fem/educational.py`.
2. **ROI menor que P1-P4:** el profiling muestra que `element_stiffness` tarda 4.69s/5runs, pero el loop interno B/J representa solo parte del tiempo — el coste dominante es la construcción de arrays NumPy intermedios, que el einsum batch también generaría.
3. **Prerrequisito:** vectorizar requiere que todas las mallas tengan el mismo tipo de elemento (Q4 o Q9 homogéneo), lo que hoy es la norma pero no está garantizado por la API.

### RCM (Reverse Cuthill–McKee)

`scipy.sparse.csgraph.reverse_cuthill_mckee` reduciría el fill-in de spsolve 2-5× en mallas estructuradas. No se implementó porque:

1. El tiempo de spsolve (~143ms Q4) ya no es el cuello de botella después de iter3 — el assembly Python domina con ~870ms.
2. Requiere guardar la permutación para reordenar el vector solución, y después revertir antes de computar esfuerzos. Pequeño riesgo de regresión numérica si la permutación no se maneja consistentemente.
3. Se sugiere para iter4 junto con el einsum batch una vez que assembly sea el nuevo techo.

### Spatial hash para snap de nodo en canvas

El hit-test de snap del modo dibujo itera todos los nodos cada vez. No se implementó porque:

1. En el profiling real (GUI inactiva durante solve/stress) no aparece en el top de cuellos de botella.
2. El canvas raramente tiene >500 nodos donde importaría; la malla de 4800 elementos se crea via `generate_structured_quad_mesh`, no vía clicks manuales.

---

## Tests ejecutados

Todos pasan sin regresión numérica:

```
python -m tests.test_fem               ✓
python -m tests.test_vv_extensions     ✓
python -m tests.vv_mms                 ✓
python -m tests.vv_timoshenko          ✓
python -m tests.vv_cook                ✓
python -m tests.test_q9_q4_cycle       ✓
python -m tests.test_undo_stack        ✓
python -m tests.test_serialization     ✓
python -m tests.test_unit_conversion   ✓
python -m tests.test_node_cascade      ✓
```

Nota: durante el desarrollo se detectó un bug introducido al añadir `_node_to_elements` — `expand_q4_to_q9` mutaba `elem.node_ids` directamente sin pasar por `add_element`, dejando el índice desactualizado. El fix (`rebuild_node_to_elements()` al final del loop en `mesh_utils.py`) fue validado por `test_node_cascade` y `test_q9_q4_cycle`.
