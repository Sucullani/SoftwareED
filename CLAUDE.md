# CLAUDE.md

Guía para Claude Code al trabajar en este repositorio.

## Proyecto

**EduFEM** — GUI educativa de elementos finitos 2D (tensión plana / deformación plana) con
elementos Q4 y Q9. Stack: `tkinter` + `ttkbootstrap` (tema `darkly`), NumPy/SciPy, matplotlib,
pylatex. ~121 archivos `.py`. **Sin pytest ni linter**: los tests son scripts tipo printout.
Los proyectos usan extensión `.edufem` (JSON vía `ProjectModel.to_dict` / `from_dict`).

## Terminología (todo lo visible al alumno va en español)

| Término inglés | Traducción canónica | Notas |
|---|---|---|
| DOF (Degree of Freedom) | **GDL** (Grado de Libertad) | Singular "GDL", plural "GDLs". Aplica al chip `Q4 · 8 GDL` / `Q9 · 18 GDL`, al validador de salud, al PDF de memoria de cálculo |
| FEM (Finite Element Method) | **MEF** (Método de Elementos Finitos) | Dos excepciones fijas: la marca **EduFEM** y la capa DXF `FEM_ELEMENTS` |
| Plane stress / strain | Tensión plana / Deformación plana | |
| Boundary condition (BC) | Restricción | Plural "restricciones" |
| Mesh · Node · Element | Malla · Nodo · Elemento | |
| Load · Stress · Strain | Carga · Tensión · Deformación | |
| Displacement · Stiffness | Desplazamiento · Rigidez | |
| Shape function | Función de forma | |
| Solver | Solucionador | "Resolver" como verbo (botón F5) se mantiene |
| Hourglass modes | Modos espurios (hourglass) | Conservar "hourglass" entre paréntesis: es el término de la literatura |

Aplica a todo string que llegue al alumno (`text=`, `label=`, `title=`, captions de plots,
status bar, `messagebox`, tooltips, banners, verdict labels de Manim) y a los documentos
LaTeX/PDF generados. **No** aplica a nombres de variables y clases, keys internas (`"vm"`),
paths ni logs. Casos borde en
[convenciones/estilo-paleta.md](docs/convenciones/estilo-paleta.md).

## Comandos

```bash
python main.py                        # GUI
pip install -r requirements.txt
pyinstaller --noconfirm build.spec    # -> dist/EduFEM.exe (onefile, ~101 MB)
```

Tests — scripts printout, se corren sueltos con `python -m tests.<nombre>`:

| Grupo | Módulos |
|---|---|
| Motor FEM | `test_solver_regression` (motor por lotes vs. versión legible, ≤ 1e-9) · `test_fem` (Q4/Q9 + cargas superficiales) · `test_vv_extensions` · `test_noncontiguous_ids` |
| V&V | `vv_mms` (convergencia) · `vv_timoshenko` (+ SAP2000) · `vv_cook` |
| Modelo | `test_serialization` · `test_undo_stack` · `test_node_cascade` · `test_unit_conversion` · `test_q9_q4_cycle` |
| GUI e interacción | `test_draw_mode` · `test_pick_ghost` · `test_selection_integration` · `test_canvas_visualization` · `test_canvas_raster` (paridad píxel a píxel del rasterizado, isolíneas y contorno de la memoria) |
| Otros | `test_memoria_calculo` · `test_probe_query` · `bench_timing` · `generate_example_dxf` |

**Empaquetado**: PyInstaller en modo onefile → un `dist/EduFEM.exe` autoextraíble; el
bootloader descomprime a `sys._MEIPASS` y lanza la app como proceso hijo. Bundlea
`resources/`, los datos de matplotlib y los hidden imports (pylatex, fitz, ezdxf,
scipy.sparse, TkAgg y `education/mod*.py` por glob). No bundlea MiKTeX: la Memoria PDF exige
`pdflatex` y, si falta, abre un diálogo con botón de descarga. Detalle —
[convenciones/arquitectura.md](docs/convenciones/arquitectura.md).

## Mapa del repositorio

```
main.py  build.spec  requirements*.txt          arranque / empaquetado
config/      constantes, paleta, unidades, colormaps   → ÚNICA fuente de colores y tolerancias
models/      ProjectModel, undo, salud, mesh_utils     → el estado que todos mutan
fem/         motor NumPy/SciPy puro (sin GUI)
file_io/     .edufem JSON, CSV/ZIP, DXF, memoria PDF, figuras Pillow
gui/         tkinter + ttkbootstrap (pre / proc / post + canvas compartido)
education/   módulos M0..M7 (overlays sobre el canvas real)
tests/       scripts printout: test_* (regresión) y vv_* (verificación y validación)
resources/   videos .webp, iconos, fuentes, DXF de ejemplo   → RUTAS DURAS, no mover
tools/       scripts de build: icono, instalador, render Manim de los videos
installer/   EduFEM.iss (Inno Setup) + dist_extra/ (lanzadores .bat + LEEME)
docs/        documentación del proyecto → ver docs/README.md
tesis/       fuente LaTeX de la tesis   → ver tesis/README.md
```

Mapa detallado, reglas de colocación ("dónde va un archivo nuevo") y tabla de
**rutas frágiles** (paths hardcodeados que no se pueden mover):
**[docs/MAPA.md](docs/MAPA.md)**.

## Antes de tocar código: qué leer

El detalle del canon vive en [docs/convenciones/](docs/convenciones/). Este archivo
es el índice + las reglas duras; **cada capítulo se lee bajo demanda**, según lo que
vayas a tocar:

| Vas a tocar | Lee antes |
|---|---|
| `models/`, `fem/`, `file_io/`, `gui/main_window.py`, `gui/dialogs/`, importador DXF | [convenciones/arquitectura.md](docs/convenciones/arquitectura.md) |
| cualquier archivo de `education/` | [convenciones/modulos-educativos.md](docs/convenciones/modulos-educativos.md) |
| `gui/preprocessing/`, `gui/postprocessing/` (spreadsheet, canvas, probe) | [convenciones/canvas-preproceso.md](docs/convenciones/canvas-preproceso.md) |
| `file_io/memoria_calculo.py`, `file_io/figure_export.py`, `theory_hub_dialog.py` | [convenciones/memoria-calculo.md](docs/convenciones/memoria-calculo.md) |
| algo que dibuje, coloree o formatee números | [convenciones/estilo-paleta.md](docs/convenciones/estilo-paleta.md) |
| optimizar `fem/assembly.py`, `fem/batch.py`, `fem/solver.py`, `fem/stress.py` | [convenciones/roadmap-fem.md](docs/convenciones/roadmap-fem.md) |
| **agregar de vuelta** un widget, botón, flag o feature que "falta" | [convenciones/no-reintroducir.md](docs/convenciones/no-reintroducir.md) — **la mayoría de las ausencias son decisiones tomadas, no olvidos** |
| `tesis/` | [tesis/README.md](tesis/README.md) + skills `tesis-redactar` / `tesis-revisar` / `tesis-bibliografia` |
| saber qué falta arreglar en el repo | [docs/auditorias/ESTADO_AUDITORIAS.md](docs/auditorias/ESTADO_AUDITORIAS.md) |

## Notas de trabajo

Antes de arrancar una tarea, leé **[docs/notas/ESTADO.md](docs/notas/ESTADO.md)**
(qué está en curso, qué quedó a medias, decisiones abiertas). Al terminar algo que
otro agente necesitaría saber, dejalo anotado ahí o en una nota propia siguiendo
[docs/notas/README.md](docs/notas/README.md). No uses `CLAUDE.md` como bitácora:
acá solo van reglas permanentes.

## Reglas duras (no negociables)

Se aplican siempre, sin importar qué capítulo estés tocando. Romper una es un bug,
no una preferencia.

1. **Español** en todo string visible al alumno, docstring y comentario. Terminología
   canónica: la tabla de arriba (**GDL**, **MEF**, restricción, tensión, malla…).
2. **Definí cada color como constante `<DOMINIO>_<USO>_COLOR` en `config/settings.py`
   e importalo.** Cero hex literales en el código de `gui/**` y `education/**`.
3. **Todo recurso pasa por `config.settings.resource_path(*parts)`**. Nunca rutas
   relativas al CWD (`os.path.join("resources", ...)`): funcionan en dev y fallan en el `.exe`.
4. **Toda mutación del usuario llama `self._capture(label)` ANTES de mutar**. Una
   acción del usuario = un snapshot. Si no lo hacés, esa acción no es reversible.
5. **Todo flujo que cree elementos vía `add_element` llama `auto_expand_if_q9(project)`**
   al final.
6. **Índices de GDL solo vía `project.node_index_map` / `dof_x` / `dof_y` /
   `Element.get_dof_indices(project)`**. Nunca `2*(nid-1)`. `K` se dimensiona
   `2*num_nodes`, no `2*max(node_id)`. Invalidar el cache (`= None`) en cada mutación
   que agregue, borre o renombre nodos.
7. **`fem/` es puro**: cero imports de `tkinter`, `matplotlib` o `ttkbootstrap`. Debe
   correr headless.
8. **Números con `fmt(value, kind)`**, nunca `f"{x:.4f}"`. Decimales por magnitud en
   `config/settings.py`.
9. **Tolerancias centralizadas** (`NUMERICAL_TOLERANCE`, `JACOBIAN_MIN_DETERMINANT`).
   Nada de tolerancias locales ad-hoc.
10. **Campo nuevo en `ProjectModel` → va en `to_dict` Y en `from_dict`**, con
    backward-compat para archivos `.edufem` viejos.
11. **`restore_from_dict` muta in-place** (undo/redo, preserva refs); **`from_dict`
    crea instancia nueva** (save/load). Cada uno en su flujo.
12. **Mutaciones setean `is_modified = True` e `is_solved = False`.**
13. **Colormap de resultados: `jet`**, para todos los campos (los que tienen signo, centrados
    en 0). `hsv` prohibido. Aplica a canvas, vista 3D y memoria PDF.
14. **Cambiá la selección con `select_*` / `replace_*_selection`**; `highlighted_*` es un
    espejo de solo lectura. En el callback canvas → spreadsheet sincronizá con el tag
    `canvas_selected`, nunca con `tree.selection_set` (congela la GUI).
15. **Cargas superficiales: usar `fem/equivalent_forces.py`.** No duplicar la fórmula
    en módulos educativos.
16. **Validación del modelo: agregá `_check_xxx(project, report)` en
    `models/model_health.py`** + su hint en `EDUCATIONAL_HINTS`. La GUI solo muestra el
    reporte; no valida por su cuenta.
17. **Módulo educativo nuevo**: nombre `education/modNN_*.py` (el `build.spec` lo
    recoge por glob para `hiddenimports`) + registrarlo en los **4** dicts de
    `education/module_launcher.py`. Cualquier `importlib` nuevo replica ese patrón.
18. **La barra tiene exactamente 3 menús** (Archivo / Modelo / Ayuda). Toda acción nueva
    entra en uno de esos tres; no hay toolbar ni menús *Editar* / *Ver* / *Análisis*.
19. **Diálogos: centrar con `center_dialog`** de `gui/dialogs/_dialog_helpers.py`.
20. **Strings LaTeX de la memoria en ASCII**: `\sigma`, `\to`, `\le` — nunca σ,
    → o ≤ literales (rompen la compilación en cp1252).
21. **Regresión numérica**: cualquier cambio en `assembly` / `batch` / `solver` / `stress`
    debe pasar `python -m tests.test_solver_regression` (motor por lotes contra la versión
    legible, error relativo ≤ 1e-9) y `python -m tests.test_fem`.
22. **Sin numba ni JIT.** El rendimiento sale de vectorizar por lotes en NumPy
    (`fem/batch.py`, `gui/preprocessing/canvas_raster.py`); la versión legible elemento a
    elemento se conserva como referencia pedagógica y oráculo, nunca se reemplaza.

### Auditoría pre-merge

```
Grep "#[0-9a-fA-F]{3,8}" --glob "gui/**"        # 0 hits en código ejecutable
Grep "#[0-9a-fA-F]{3,8}" --glob "education/**"  # (los hits en comentarios y docstrings son OK)
Grep "DOF" --glob "**/*.py"                     # hits solo en nombres, keys y comentarios
Grep "FEM" --glob "**/*.py"                     # idem (la marca EduFEM y la capa FEM_ELEMENTS son OK)
```

Cualquier hit de `DOF`/`FEM` dentro de un string que llegue al alumno se convierte a
**GDL** / **MEF**.

## Al revisar o modificar código

Aplica a todo cambio, no solo a las tareas explícitas de review.

1. **Auditá lo que tocaste** —y lo que el cambio impacta de costado— contra las reglas duras:
   `_capture()` antes de mutar, `auto_expand_if_q9` al final, hex fuera de `config/`,
   decimales sin `fmt()`, imports de `tk`/`matplotlib` en `fem/`, `tree.selection_set` desde
   el callback del canvas, `from_dict` donde correspondía `restore_from_dict`.
2. **Olfatos que las reglas no cubren**: lógica invertida u off-by-one, race conditions en
   callbacks Tk, refs rotas tras mutar el `ProjectModel`, loops O(n²) sobre nodos habiendo
   dict, `K.toarray()` innecesario, recomputar `B`/`J` con cache disponible, `redraw()`
   completo del canvas donde alcanza `redraw_overlays_only()`.
3. **Corregí en el mismo cambio** lo que encuentres, salvo que ensanche el alcance pedido.
   **Preservá la versión legible** donde el código tiene valor pedagógico (M1..M7, `fem/`
   como referencia de M2/M3/M5): exponé la variante optimizada en paralelo, no la reemplaces.
   Justificá cada mejora en una línea (`# vectorizado: O(n²) → O(n) en surface loads`).
4. **Si cambiás una regla**, actualizá `CLAUDE.md` o el capítulo de `docs/convenciones/` que
   corresponda y **borrá la versión vieja**: nunca dejes dos reglas en conflicto ni notas del
   tipo "actualización" o "ver también". Lo que es novedad de trabajo va a `docs/notas/`.
