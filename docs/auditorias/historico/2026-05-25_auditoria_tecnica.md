# Auditoría técnica EduFEM — 2026-05-25 (nocturna)

> Auditoría de rendimiento, arquitectura, seguridad y calidad de código sobre la
> rama `main` (commit `ed852bf`). Fase 1 = diagnóstico (este documento). Fase 2 =
> implementación de *quick wins* de bajo riesgo (ver tabla §7 y PR asociado).
>
> **Entorno de auditoría**: el contenedor venía **sin** `numpy`/`scipy`/`sympy`/
> `matplotlib` instalados — se instalaron desde `requirements.txt` para poder
> correr la suite. El intérprete disponible es **Python 3.11.15** (el brief
> mencionaba 3.13; se audita contra el intérprete real del entorno).

---

## 1. Tecnologías y dependencias

Declaradas en [`requirements.txt`](../../../requirements.txt). No hay `pyproject.toml`
ni lockfile; todas las restricciones son `>=` (sin techo de versión).

| Paquete | Restricción repo | Última versión (PyPI, may-2026) | Función en el sistema | Flag |
|---|---|---|---|---|
| `numpy` | `>=1.24.0` | 2.4.x | Álgebra densa: K, F, B, D, solución `u`, esfuerzos. Núcleo de `fem/`. | Mayor 2.x ya en uso (probado con 2.4.6) — OK, pero el salto 1.x→2.x tuvo cambios de API (`np.float_`, copy semantics). Verificar que no se usen símbolos removidos. |
| `scipy` | `>=1.10.0` | 1.17.x | `scipy.linalg.solve` (solver denso LU) en `fem/solver.py`. | OK. Sólo se usa `linalg.solve`; `scipy.sparse` **no** se usa (ver §3/§5). |
| `sympy` | `>=1.12` | 1.14.x | Integrando simbólico de K_e en módulos educativos (M5) + `memoria_calculo`. | OK. Solo educativo/PDF. |
| `matplotlib` | `>=3.7.0` | 3.10.x / 4.x | Gráficos de módulos educativos, vistas Post, V&V plots. | OK. |
| `ttkbootstrap` | `>=1.10.0` | 1.13.x | Tema `darkly`, widgets ttk. Capa GUI. | OK. |
| `reportlab` | `>=4.0.0` | 4.5.1 (2026-05-12) | Generación PDF de la memoria de cálculo. | OK. El piso `>=4.0.0` evita CVE-2023-33733 (RCE vía `rl_safe_eval` en `<para>`, afectaba `<3.6.13`). Mantener el piso ≥4.0. |
| `pylatex` | `>=1.4.2` | 1.4.2 | Ruta alternativa de generación LaTeX/PDF. | **Mantenimiento bajo**: 1.4.2 es la última release y lleva años sin actualizarse. Shell-out a `pdflatex` (binario externo, requiere TeX). No es un riesgo de seguridad directo pero es una dependencia estancada. |
| `PyMuPDF` | `>=1.24.0` | 1.27.2.3 (2026-04-24) | Render/embed de PDF (memoria, fitz). | Empaqueta la lib C MuPDF; históricamente con CVEs de memory-safety en versiones viejas. Piso `>=1.24` es razonable; conviene **fijar** un piso más alto y revisar advisories al releasear. |
| `Pillow` | `>=10.0.0` | 12.2.0 (2026-04-01) | Iconos PIL, mini-iconos de diálogos, decodificación WebP en `WebpPlayer`. | Pillow es históricamente CVE-prone (decoders de imagen). Piso `>=10.0` es bajo: existen CVEs en la serie 10.x. **Subir el piso a `>=11.0`** mitiga varios advisories de decoders. |
| `ezdxf` | `>=1.0` | 1.4.4 (2026-05-14) | Import de geometría DXF (`file_io/dxf_io.py`). Import diferido. | OK. Piso `>=1.0` amplio; la API usada (`readfile`, capas, polilíneas) es estable desde 1.0. |

**Incompatibilidades / riesgos de versionado**:

- **Sin techos de versión ni lockfile**: `pip install -r requirements.txt` puede
  traer mayores nuevas (numpy 3, matplotlib 4) con cambios incompatibles. Para un
  software de tesis distribuido con PyInstaller, conviene un `requirements.lock`
  (o `pip freeze`) reproducible y techos `<X.0` en las dependencias con historial
  de breaking changes (numpy, matplotlib, ttkbootstrap).
- **numpy 2.x**: el código corre con 2.4.6, pero el piso `>=1.24` mezcla dos
  generaciones de API. Recomendado fijar `>=2.0,<3.0` una vez verificada la suite
  (ya pasa en 2.4.6).
- **Pisos de seguridad bajos** en `Pillow` (`>=10`) y `PyMuPDF` (`>=1.24`):
  ambos decodifican formatos binarios de origen potencialmente no confiable
  (imágenes, PDFs). Subir pisos.

---

## 2. Arquitectura

Patrón **MVC-ish**. La pieza central es `ProjectModel`
([`models/project.py`](../../../models/project.py)): un contenedor mutable de dicts
(`nodes`, `elements`, `materials`, `nodal_loads`, `boundary_conditions`,
`surface_loads`) + configuración (`analysis_type`, `element_type`, `unit_system`,
gravedad) + estado de solución. Todos los componentes toman una referencia y la
mutan; los setters marcan `is_modified=True` / `is_solved=False`.

### Capas

```
                 ┌─────────────────────────────────────────────┐
                 │                  GUI (tkinter)               │
                 │  main_window · pre_tab · proc_tab · post_tab │
                 │  mesh_canvas · dialogs/ · widgets/           │
                 └───────────────┬─────────────────────────────┘
                                 │ lee/muta
                                 ▼
   education/ ───────────►  ProjectModel  ◄──────── file_io/
   (M0..M9, overlays)      (models/project)        (json/csv/zip/dxf/pdf)
   solo VISUALIZA               │                   serializa/deserializa
                                │ to_dict/from_dict
            ┌───────────────────┼───────────────────┐
            ▼                    ▼                    ▼
       models/             models/model_health   models/mesh_utils
       (node, element,     validate_project()    expand/shrink/subdiv
        material, load,    (función pura)         classify_*
        boundary,
        undo_stack)
                                 │
                                 ▼ (consumido por el solve)
                 ┌─────────────────────────────────────────────┐
                 │                    fem/                       │
                 │  shape_functions → jacobian → b_matrix →      │
                 │  constitutive → stiffness → assembly →        │
                 │  solver → stress / error_norms / probe_query  │
                 │           (NumPy/SciPy puro, sin GUI)         │
                 └─────────────────────────────────────────────┘
```

### Flujo de datos del *solve*

```
ProjectModel
   │  assemble_global_system(project)
   ▼
element_stiffness (por elem) ─► ke + gauss_data ─┐
   │                                             ├─► K (densa n×n), F, element_data
surface/nodal/body forces  ───────────────────-─┘
   │  apply_boundary_conditions(K,F,restrained,u_pre)
   ▼
K_red, F_red ──► scipy.linalg.solve ──► u_free ──► u (completo)
   │                                                │
   │  reactions = K·u − F                           ▼
   ▼                                          compute_all_stresses
solution dict {u,K,F,K_red,F_red,...}  ──►  element_stresses + nodal_avg
```

### Acoplamientos y separación de capas

- ✅ **`fem/` es puro** (NumPy/SciPy, sin imports de tk/matplotlib/ttkbootstrap).
  Verificado: corre headless en los tests V&V. Separación correcta.
- ✅ **`models/model_health` es función pura** sin dependencias UI.
- ✅ **`education/` solo visualiza**: importa `fem/` y `models/` pero no los
  modifica (salvo sandboxes que hacen `deepcopy`).
- ⚠️ **Imports diferidos dentro de funciones** abundan para romper ciclos:
  `models/project.py` importa `numpy` dentro de `get_prescribed_displacement_vector`;
  `mesh_utils.generate_structured_quad_mesh` importa `ProjectModel` dentro de la
  función; `fem/solver` importa `assemble_global_system` dentro de `solve_system`.
  Funciona, pero señala un acoplamiento `models ↔ fem ↔ models` que conviene
  documentar. No es un defecto crítico.
- ⚠️ **`controllers/`** existe pero está esencialmente vacío (`__init__.py`); el
  rol de controlador lo cumple `MainWindow`. Carpeta muerta.
- ⚠️ **`node_index_map` es una `@property` recomputada en cada acceso**
  (`sorted(self.nodes.keys())`, O(n log n)). Se invoca varias veces por solve
  (assembly, get_restrained_dofs, get_free_dofs, get_prescribed_*). Para mallas
  educativas es despreciable, pero es un punto caliente latente (ver §3/§5).

### Componentes críticos
- **`fem/assembly.py`** — ensamblaje de K densa (CPU + memoria).
- **`fem/solver.py`** — factorización densa (CPU).
- **`fem/stress.py`** — recuperación de esfuerzos (recomputa B/J, ver §4).
- **`models/project.py`** — cleanup en cascada (O(E) por nodo, ver §3/§4).
- **`gui/preprocessing/mesh_canvas.py`** — redibujado del canvas (no auditado en
  profundidad: fuera del scope de modificación nocturno).

---

## 3. Cuellos de botella

### CPU

| Punto | Archivo:línea | Complejidad | Comentario |
|---|---|---|---|
| Scatter de kₑ → K con doble bucle Python | [`fem/assembly.py:116-118`](../../../fem/assembly.py) | O(d²) Python por elemento (d=8/18) | El núcleo del ensamblaje hace el *scatter* celda por celda en Python puro. Vectorizable con `K[np.ix_(dof,dof)] += ke` (bit-idéntico, medido ~35% más rápido en el scatter). **Quick win.** |
| Factorización densa general | [`fem/solver.py:97`](../../../fem/solver.py) | O(N³) LU | `scipy.linalg.solve` general, no explota simetría/SPD. Probado `assume_a='pos'`: sólo ~5% más rápido en el rango educativo y cambia el modo de fallo (LinAlgError si no es SPD). **No vale el riesgo en la ruta densa**; la ganancia real es *sparse* (§5). |
| Recuperación de esfuerzos recomputa B/J | [`fem/stress.py:32-41`](../../../fem/stress.py) | O(elem·gp) duplicado | `compute_element_stresses` recalcula `dN`, J, inv_J y B en cada punto de Gauss, **pese a que `element_stiffness` ya los guardó** en `element_data[eid]["gauss_data"]`. Duplica el trabajo de B/J en el Post. Reutilizable (bit-idéntico). Riesgo medio (ver §8). |
| Reconstrucción de `u` con bucle | [`fem/solver.py:102-106`](../../../fem/solver.py) | O(N) Python | `for i,dof in enumerate(free_dofs): u[dof]=u_free[i]`. Vectorizable con fancy-indexing `u[free_dofs]=u_free`. Bit-idéntico. **Quick win** (impacto chico). |
| `validate_project` recorre elementos varias veces | [`models/model_health.py:272,291,307,399,451`](../../../models/model_health.py) | O(E) ×N pasadas | Cada `_check_*` reconstruye `nodes_in_elements` / `used_mat_names`. Son O(E) lineales (no cuadráticos) y la validación corre por acción del usuario, no por frame. Bajo impacto. |

### Memoria

| Punto | Archivo:línea | Comentario |
|---|---|---|
| **K global densa** | [`fem/assembly.py:80`](../../../fem/assembly.py) | `K = np.zeros((n_dof, n_dof))`. O(N²) memoria. Para 10k GDL ≈ 800 MB. El roadmap del propio `CLAUDE.md` marca *K sparse* como prioridad alta. **No es quick win seguro** (rompe consumidores densos: M5 `K.toarray()`, `post_tab`, `memoria_calculo`, que están fuera del scope nocturno). Ver §8. |
| `K_red = K[np.ix_(free,free)]` | [`fem/solver.py:42`](../../../fem/solver.py) | Copia densa adicional (N_red²). Inherente a la ruta densa. |
| `gauss_data` guarda copias por punto | [`fem/stiffness.py:72-84`](../../../fem/stiffness.py) | Cada gp guarda `J.copy()`, `B.copy()`, `ke_contribution.copy()`, etc. Necesario para los módulos educativos M2/M4/M5, pero infla `element_data` ~10× el tamaño de K. Aceptable por valor pedagógico; documentar. |

### Disco
- I/O de proyecto/CSV/ZIP es síncrono y corre en el hilo de GUI
  ([`file_io/project_io.py`](../../../file_io/project_io.py),
  [`file_io/model_io.py`](../../../file_io/model_io.py)). Para archivos chicos
  (`.edufem` ≈ KB) es imperceptible. La **generación de PDF sí** se hizo
  asíncrona (`gui/main_window.py` `_worker` en daemon thread con `root.after`)
  — patrón correcto.

### Red
- N/A — aplicación de escritorio sin red.

### UI
- ✅ Los módulos overlay usan capas (`add_overlay_layer`) con tags propios y
  `mesh.after(33, ...)` para ~30 fps — patrón correcto documentado.
- ✅ No se hallaron `FuncAnimation` sin referencia persistente en el código
  activo (el anti-pattern documentado en `CLAUDE.md` fue migrado a WebP).
- ⚠️ `mesh_canvas.redraw()` completo se dispara en varios flujos; no auditado a
  fondo (archivo fuera del scope de modificación).

### Concurrencia
- 6 usos de `threading.Thread` (warmup mathtext, PDF worker, compilación LaTeX
  async, render de imágenes LaTeX, locks de cache LaTeX).
- ✅ **Thread-safety de Tk correcta**: todas las actualizaciones de widgets se
  marshalean vía `root.after(0, cb)` / `widget.after(0, cb)`; `latex_image`
  además chequea `winfo_exists()`. **No se detectó acceso cross-thread directo
  a widgets Tk.** Sin race conditions evidentes sobre `ProjectModel` (las
  mutaciones ocurren en el hilo de UI).

---

## 4. Código duplicado y subóptimo

| Hallazgo | Archivo:línea | Detalle |
|---|---|---|
| **Scatter celda-a-celda** (vectorizable) | [`fem/assembly.py:116-118`](../../../fem/assembly.py) | Doble `for` Python → `np.ix_`. Bit-idéntico. |
| **Bucle de reconstrucción de `u`** | [`fem/solver.py:102-106`](../../../fem/solver.py) | Reemplazable por fancy-indexing. |
| **`list(project.materials.values())[0]`** | [`fem/assembly.py:100`](../../../fem/assembly.py), [`fem/stress.py:161-162`](../../../fem/stress.py) | Construye lista completa para tomar `[0]`. `next(iter(...))` evita la copia. Micro, pero `probe_query` ya usa el idioma correcto. |
| **Re-chequeo O(E) de pertenencia de nodo** | [`models/project.py:330-332`](../../../models/project.py) `remove_element`; [`models/project.py:223`](../../../models/project.py) `preview_node_cascade`; cascada en `remove_node_with_cascade` | `any(nid in e.node_ids for e in self.elements.values())` **dentro** del bucle sobre los nodos del elemento → O(npe·E) por borrado, y O(E²) bajo `remove_node_with_cascade` (llama `remove_element` por cada elemento). Precomputar **una vez** el set de node_ids referenciados por los elementos restantes lo baja a O(E+npe). Bit-idéntico. Cubierto por `test_node_cascade`. **Quick win.** |
| **B/J recomputados en el Post** | [`fem/stress.py:32-41`](../../../fem/stress.py) vs [`fem/stiffness.py:55-64`](../../../fem/stiffness.py) | `gauss_data` ya tiene B, J, inv_J; `compute_element_stresses` los recalcula. Reutilizar evitaría duplicar el cómputo más caro. Riesgo medio (toca la ruta del Post). Ver §8. |
| **Lógica de fuerzas equivalentes** (posible duplicación M6) | [`fem/equivalent_forces.py`](../../../fem/equivalent_forces.py) ↔ `education/mod06_equivalent_forces.py` | `CLAUDE.md` pide deduplicar en favor de `fem/`. **No verificable/implementable nocturno**: `education/` está fuera del scope de modificación. Documentar. |
| **`node_index_map` recomputado** | [`models/project.py:518-525`](../../../models/project.py) | `@property` que ordena las claves en cada acceso. Cachearlo con invalidación es tentador pero **riesgoso** (staleness si se muta `nodes` sin invalidar). No tocar sin un mecanismo de invalidación robusto. Ver §8. |

**Operaciones sparse→dense innecesarias**: no se halló ningún `.toarray()` /
`.todense()` en `fem/` ni `models/` (no se usa `scipy.sparse` en absoluto). El
único `K.toarray()` conceptual está en el módulo educativo M5, que **requiere** K
densa por diseño.

**Listas vs sets**: `model_health` y `mesh_utils` ya usan `set()` para los
*membership checks* (`nodes_in_elements`, `still_referenced`, `in_element`). El
único *membership check* repetido sobre listas es el de `project.py:330` (arriba).

---

## 5. Algoritmos y estructuras (Big-O actual vs propuesto)

| Componente | Actual | Propuesto | Notas |
|---|---|---|---|
| **Ensamblaje (scatter)** | O(E·d²) en Python | O(E·d²) en C vía `np.ix_` | Mismo orden, constante ~35% menor. Implementado nocturno (bit-idéntico). El roadmap pide además `np.einsum` batch — mayor reescritura, **mantener versión escalar pedagógica** (M2/M4/M5). Ver §8. |
| **K global** | densa O(N²) mem, ensamblaje O(N²) cero-init | `scipy.sparse.lil_matrix` → `.tocsr()` | Roadmap prioridad alta. Memoria O(nnz). **Bloqueado nocturno**: cambia el tipo de `K` en el dict de retorno → rompe M5/post/pdf (fuera de scope). Ver §8. |
| **Solver** | `scipy.linalg.solve` LU densa O(N³) | `scipy.sparse.linalg.spsolve` (UMFPACK) / CHOLMOD | Va de la mano con K sparse. RCM ordering (`reverse_cuthill_mckee`) detrás de flag `SOLVER_USE_RCM`. Roadmap. Ver §8. |
| **Recuperación de esfuerzos** | O(E·gp) recomputando B/J | O(E·gp) reutilizando `gauss_data` | Constante ~2× menor en el Post. Riesgo medio. Ver §8. |
| **`remove_element` cleanup** | O(npe·E) | O(E+npe) | Precómputo del set de nodos referenciados. Implementado nocturno. |
| **`node_index_map`** | O(n log n) por acceso, varias veces/solve | O(1) cacheado + O(n log n) en invalidación | Requiere invalidación segura. **No nocturno** (riesgo de staleness). |

---

## 6. Seguridad y estabilidad

> **No se detectaron hallazgos CRÍTICOS** (sin secretos en el repo, sin
> `eval`/`exec`, sin `shell=True`, sin deserialización insegura tipo `pickle`).

### `eval` / `exec` / `pickle` / `os.system` / `shell=True`
- ✅ **Cero** ocurrencias de `eval(`, `exec(`, `pickle`, `os.system`,
  `shell=True`, `__import__` en código de producción. (Esperado y cumplido.)
- ✅ Único `subprocess` en [`config/latex_cache.py:194-210`](../../../config/latex_cache.py):
  `subprocess.run([...], timeout=20)` con **lista de args** (no shell), captura
  de salida, y manejo explícito de `FileNotFoundError` / `TimeoutExpired`. Seguro.

### `except` bare / genéricos
- ✅ **Cero `except:` bare.**
- ⚠️ ~357 `except Exception` (mayoría en GUI/PDF, tolerancia de UI aceptable).
  Puntos a revisar en capas no-GUI:
  - [`file_io/model_io.py:232`](../../../file_io/model_io.py): `except Exception: continue`
    al construir `Material` — silencia cualquier error de fila. Acotar a
    `(ValueError, TypeError)` sería más correcto (el `continue` intencional se
    conserva). Bajo impacto (los `_to_float` ya dan defaults). No implementado
    nocturno por bajo valor + riesgo de cambiar qué errores se silencian.
  - [`file_io/dxf_io.py:109`](../../../file_io/dxf_io.py): `except Exception: return None`
    leyendo `$INSUNITS` — demasiado amplio.
  - [`models/undo_stack.py:133`](../../../models/undo_stack.py): `except Exception` en
    callbacks de listeners — **intencional** (no debe romper otros listeners). OK.

### Validación de input en `file_io/`
- ⚠️ [`file_io/project_io.py:36-38`](../../../file_io/project_io.py): `json.load(f)` sin
  `try/except`; el dict no se valida antes de `from_dict`. Un `.edufem` corrupto
  produce un `KeyError`/`JSONDecodeError` crudo. **Recomendación**: envolver y
  re-lanzar con mensaje claro. **No implementado nocturno**: introduciría un
  string que puede llegar a un `messagebox` (regla "no tocar strings visibles").
- ⚠️ [`file_io/csv_io.py:30-32,93-94`](../../../file_io/csv_io.py): `float()/int()` sin
  protección — una celda no numérica lanza `ValueError` no capturado. Mismo
  criterio: documentar, no tocar (riesgo de string visible + cambia el flujo).
- ✅ [`file_io/model_io.py`](../../../file_io/model_io.py): defensivo. Helpers
  `_to_int/_to_float/_to_bool` con defaults; valida existencia de nodos/materiales
  antes de crear elementos/cargas. Buen patrón.
- ⚠️ [`file_io/dxf_io.py`](../../../file_io/dxf_io.py): el factor `scale` provisto por el
  usuario se aplica sin chequeo de cota (podría ser 0 o negativo). Idempotencia
  por `frozenset(node_ids)` y forzado CCW vía shoelace — correctos.

### Manejo de archivos
- ✅ **Todos** los `open(...)` de `file_io/` usan `with` (context manager);
  `zipfile.ZipFile` también como context manager. Sin handles colgantes.

### Thread-safety de Tk
- ✅ Correcta (ver §3 Concurrencia). Todo update de widget marshaleado por
  `after(0, ...)`.

### Paleta congelada (regla de `CLAUDE.md`)
- ⚠️ **218 literales hex fuera de `config/`** (83 en `gui/`, 135 en `education/`)
  — viola la regla "cero hex fuera de `config/settings.py`". Ejemplos:
  `gui/main_window.py:401,517,519`, `education/mod02_jacobian.py:72,265,270,525`.
  **No implementable nocturno** (todos los archivos están fuera del scope de
  modificación: `gui/`, `education/`). Documentado para follow-up diurno.

---

## 7. Reporte priorizado

| id | problema | archivo:línea | impacto | dificultad | quick_win | riesgo_UX | implementado_en_fase2 |
|---|---|---|---|---|---|---|---|
| A1 | Scatter kₑ→K en doble bucle Python | fem/assembly.py:116-118 | medio | baja | sí | no | **sí** |
| A2 | Reconstrucción de `u` con bucle Python | fem/solver.py:102-106 | bajo | baja | sí | no | **sí** |
| A3 | `remove_element` cleanup O(npe·E) → O(E²) en cascada | models/project.py:330-332 | medio | baja | sí | no | **sí** |
| A4 | `preview_node_cascade` re-chequeo O(C·E) | models/project.py:220-237 | bajo | baja | sí | no | **sí** |
| A5 | `list(...)[0]` para material fallback | fem/assembly.py:100; fem/stress.py:161 | bajo | baja | sí | no | **sí** |
| A6 | Faltan type hints + `from __future__ import annotations` en `fem/` núcleo | fem/assembly,solver,stiffness,jacobian,b_matrix,constitutive,shape_functions,gauss_quadrature | bajo | baja | sí | no | **sí** |
| B1 | K global densa (memoria O(N²)) | fem/assembly.py:80 | alto | alta | no | sí | no |
| B2 | Solver denso general (no SPD/sparse) | fem/solver.py:97 | alto | alta | no | sí | no |
| B3 | B/J recomputados en recuperación de esfuerzos | fem/stress.py:32-41 | medio | media | no | sí | no |
| B4 | `node_index_map` recomputado por acceso | models/project.py:518-525 | bajo | media | no | sí | no |
| B5 | Ensamblaje `np.einsum` batch | fem/assembly.py | medio | alta | no | sí | no |
| C1 | 218 literales hex fuera de `config/` | gui/**, education/** | medio | media | no | sí | no |
| C2 | `json.load` sin validación | file_io/project_io.py:36 | medio | baja | no | sí | no |
| C3 | `float()/int()` sin protección en CSV | file_io/csv_io.py:30-32,93 | medio | baja | no | sí | no |
| C4 | `except Exception` amplios en file_io | file_io/model_io.py:232; dxf_io.py:109 | bajo | baja | no | no | no |
| C5 | `scale` DXF sin cota | file_io/dxf_io.py | bajo | baja | no | no | no |
| C6 | Sin lockfile / techos de versión; pisos Pillow/PyMuPDF bajos | requirements.txt | medio | baja | no | no | no |
| C7 | Dedup `fem/equivalent_forces` ↔ M6 | education/mod06_*.py | bajo | media | no | sí | no |
| C8 | Carpeta `controllers/` muerta | controllers/ | bajo | baja | no | no | no |

> **Criterio `implementado_en_fase2`**: sólo `sí` si NO toca dirs prohibidos
> (gui/dialogs, gui/widgets, education, gui/preprocessing/{mesh_canvas,pre_tab},
> gui/postprocessing, gui/processing, gui/main_window), NO cambia strings
> visibles, NO añade dependencias, NO cambia firmas públicas, NO viola
> `CLAUDE.md`, y la suite de 8 tests pasa con `max|Δu| ≤ 1e-9`.

---

## 8. Recomendaciones de alto impacto NO implementadas

### B1 — K global *sparse* (`scipy.sparse`)
- **Por qué fuera de scope**: cambia el **tipo** de `K` en el dict de retorno de
  `solve_system` (de `ndarray` a matriz sparse). Aunque la *firma* (las claves
  del dict) no cambia, el contrato implícito sí: M5 (`education/`), `post_tab`
  (`gui/postprocessing/`) y `memoria_calculo` (`file_io/`) consumen `K` como
  array denso e indexan con `np.ix_`. Esos consumidores están **fuera del scope
  de modificación nocturno**, así que no puedo adaptarlos. Riesgo UX alto.
- **Cómo abordarlo (follow-up diurno)**: ensamblar en `lil_matrix`/COO,
  `.tocsr()` antes de resolver, `spsolve`. **Mantener una rama densa** detrás de
  un flag para M5 (que necesita `K.toarray()`), o exponer K densa sólo bajo
  pedido (`solve_system(..., dense_K=True)`). Validar con toda la suite + revisar
  cada consumidor de `solution["K"]`.

### B2 — Solver SPD / sparse + RCM
- **Por qué fuera de scope**: ligado a B1. En la ruta **densa** actual,
  `assume_a='pos'` da sólo ~5% (medido) y cambia el modo de fallo a
  `LinAlgError` cuando K no es SPD — no compensa el riesgo. El beneficio real
  (orden de magnitud) viene con sparse + reordenamiento.
- **Cómo abordarlo**: `spsolve` por defecto; `sksparse.cholmod` opcional con
  import diferido (patrón `_require_cholmod()` como `ezdxf`); RCM
  (`reverse_cuthill_mckee`) detrás de `SOLVER_USE_RCM` en `settings`, default
  `False`, para comparar fill-in en M9.

### B3 — Reutilizar B/J en recuperación de esfuerzos
- **Por qué fuera de scope nocturno (riesgo medio)**: `compute_element_stresses`
  es función pública y podría llamarse fuera del flujo `compute_all_stresses`;
  reutilizar `gauss_data` exige garantizar el mismo orden de puntos de Gauss y no
  romper consumidores. Toca la ruta del Post. Bit-idéntico si se hace bien, pero
  requiere validación cuidadosa con el render del contorno.
- **Cómo abordarlo**: pasar `element_data[eid]["gauss_data"]` a
  `compute_all_stresses` y leer `gp["B"]`/`gp["det_J"]` ya cacheados; mantener
  `compute_element_stresses(node_coords, ...)` como variante standalone para
  llamadas sueltas. Test de regresión contra `nodal_avg_stresses`.

### B4 — Cachear `node_index_map`
- **Por qué fuera de scope**: requiere invalidación en **cada** mutación de
  `nodes` (add/remove/change_id/restore). Un cache mal invalidado produce índices
  obsoletos → corrupción silenciosa de K/F. Riesgo > beneficio para el tamaño de
  malla educativo.
- **Cómo abordarlo**: atributo privado `self._index_map_cache` invalidado en
  todos los setters de `nodes` + en `restore_from_dict`. Test que verifique
  invalidación tras cada mutación.

### B5 — Ensamblaje `np.einsum` batch
- **Por qué fuera de scope**: reescritura no trivial del lazo de ensamblaje;
  debe **preservar** la versión escalar legible (referencia pedagógica de
  M2/M4/M5) en paralelo. Mayor superficie de revisión que un *quick win*.
- **Cómo abordarlo**: `np.einsum("egki,kl,eglj,eg,g->eij", B, D, B, detJ, w)`
  batcheando elementos del mismo tipo; gate por `VECTORIZED_THRESHOLD`.

### C1 — 218 literales hex fuera de `config/`
- **Por qué fuera de scope**: todos los hits están en `gui/` y `education/`,
  directorios **prohibidos** para modificación nocturna (riesgo UX directo). Es,
  además, una violación de la "paleta congelada" de `CLAUDE.md` que conviene
  saldar con revisión visual.
- **Cómo abordarlo**: extraer cada literal a una constante nombrada en
  `config/settings.py` (sección comentada por dominio) e importar. Auditar
  `Grep '#[0-9a-fA-F]{3,8}'` hasta 0 hits. Verificar a ojo que la paleta no
  cambie (WCAG AA contra `darkly`).

### C2 / C3 — Validación de input en JSON/CSV
- **Por qué fuera de scope**: el manejo correcto implica mensajes de error que
  terminan en `messagebox` (string visible al usuario) — choca con "no tocar
  strings visibles" de la directiva nocturna.
- **Cómo abordarlo**: capa de validación en `file_io/` que lance excepciones de
  dominio (`ProjectLoadError`) con mensajes en español, y que `main_window` las
  muestre. Tests con archivos malformados.

### C6 — Higiene de dependencias
- **Por qué fuera de scope**: la directiva prohíbe **editar `requirements.txt`
  para agregar paquetes**; subir pisos/agregar techos es edición de versiones, no
  de paquetes, pero se deja para decisión explícita del mantenedor (puede romper
  el build PyInstaller).
- **Cómo abordarlo**: generar `requirements.lock` con `pip freeze` del entorno
  validado; subir pisos de seguridad (`Pillow>=11`, `PyMuPDF>=1.26`); agregar
  techos `<X.0` en numpy/matplotlib/ttkbootstrap. Re-correr toda la suite.

### C7 — Dedup M6 ↔ `fem/equivalent_forces`
- **Por qué fuera de scope**: `education/` prohibido. Documentado por `CLAUDE.md`.
- **Cómo abordarlo**: que `mod06` importe y use `surface_load_to_nodal_forces[_q9]`
  de `fem/` en lugar de reimplementar.
