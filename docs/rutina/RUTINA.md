# Rutina de mejora continua de EduFEM

**Creada**: 2026-09-08 · **Cadencia**: cada hora · **Modelo**: Opus 5 (contexto 1M) ·
**Rama**: `main` directo, sin ramas · **Superficie**: rutina de claude.ai (Claude Code remoto),
`trig_01MYK6MCRy1yja6WwnB8bHFN`, dispara a las :13 de cada hora

> Este archivo es el **prompt completo y autoritativo** de la rutina. El disparador de
> claude.ai solo contiene un resumen operativo y la orden de leer este documento entero.
> Si los dos se contradicen, manda este archivo.
>
> Los otros dos archivos de esta carpeta son el estado vivo de la rutina:
> **[BITACORA.md](BITACORA.md)** (qué hizo cada sesión y por qué) y
> **[BACKLOG.md](BACKLOG.md)** (qué falta, en qué orden, y qué espera al autor).

---

## 1. Objetivo

Que EduFEM **cumpla de verdad lo que la tesis promete** y que usarlo sea evidente para un
alumno que abre el programa por primera vez. En concreto, y por orden de prioridad:

1. **Coherencia con la tesis.** Lo que `tesis/` afirma que el software hace, el software lo
   hace; y lo que el software hace, la tesis lo describe bien. Cada divergencia es un
   defecto de una de las dos partes: se corrige la que esté equivocada.
2. **Incongruencias e ilogismos de la interacción.** Un botón que no dice qué va a pasar,
   un estado que no se ve, un error que se traga en silencio, un flujo que exige saber algo
   que la pantalla no muestra, dos caminos que llevan al mismo lado con nombres distintos,
   una acción destructiva sin confirmación ni undo. Esto es lo que rompe la intuitividad, y
   es lo primero que hay que cazar.
3. **Errores.** Cualquier bug que aparezca durante la sesión —en el área trabajada o al
   lado— se corrige **en la misma sesión**. No se anota "para después" salvo que arreglarlo
   exija una decisión del autor; en ese caso se anota en el BACKLOG con la evidencia.
4. **Funcionalidad existente, mejor.** Más versátil sin ser más complicada: atajos que
   faltan, valores por defecto que obligan a trabajo manual, operaciones que solo se pueden
   hacer de a una, información que hay que calcular a mano.
5. **Gráficas y estilo.** Que el canvas, las figuras de la memoria y los overlays educativos
   se vean como una herramienta profesional moderna (referencia declarada por el autor:
   ANSYS / SAP2000) y no como una demo.

## 2. Qué NO es esta rutina

- **No es un generador de features.** No se inventan capacidades nuevas que la tesis no
  reclama. Versatilidad significa que lo que ya existe se pueda usar mejor.
- **No agrega dependencias.** El stack está cerrado: `tkinter` + `ttkbootstrap` (tema
  `darkly`), NumPy/SciPy, matplotlib, Pillow, pylatex, ezdxf, PyMuPDF. **Cero librerías
  nuevas**, cero `pip install`, cero `requirements.txt` tocado. Si algo parece necesitar una
  librería, se resuelve con lo que hay o se anota en el BACKLOG como propuesta.
- **No es una auditoría.** Auditar sin tocar ya lo hace `/schedule`
  ([docs/auditorias/](../auditorias/)). Acá cada sesión **entrega código commiteado**.
- **No toca el motor por gusto.** `fem/` se toca solo cuando el resultado numérico que ve el
  alumno está mal o la tesis dice otra cosa. La versión legible elemento a elemento **no se
  reemplaza nunca**: es la referencia pedagógica de M2/M3/M5 y el oráculo de
  `test_solver_regression`.

## 3. Paso 0 obligatorio, antes de tocar nada

```bash
git fetch origin && git checkout main && git pull --ff-only origin main
```

Después, en este orden:

1. **[BACKLOG.md](BACKLOG.md)** — de acá sale el área de esta sesión. Es lo primero.
2. **[BITACORA.md](BITACORA.md)**, las últimas 3 entradas — qué hicieron las sesiones
   previas, para no repetir ni deshacer.
3. **[../../CLAUDE.md](../../CLAUDE.md)** entero — las 22 reglas duras son ley.
4. **[../notas/ESTADO.md](../notas/ESTADO.md)** — trabajo a medias y decisiones que esperan
   al autor. Si tu área figura ahí como *en curso*, asumí que hay algo empezado.
5. **El capítulo de [../convenciones/](../convenciones/) que le toca a tu área** (la tabla
   de ruteo está en `CLAUDE.md`), y **siempre**
   [no-reintroducir.md](../convenciones/no-reintroducir.md).
6. **[../auditorias/ESTADO_AUDITORIAS.md](../auditorias/ESTADO_AUDITORIAS.md)** — por si tu
   área ya tiene hallazgos abiertos; conviene cerrarlos en el mismo pase.

## 4. Una sola área por sesión

Tenés alrededor de una hora. **Una** área, terminada y verificada, vale más que cinco a
medias. El BACKLOG lleva la cola: tomá el área marcada como *siguiente*, y al cerrar marcá
la que sigue.

| # | Área | Archivos |
|---|---|---|
| 1 | Canvas del Pre-Proceso | `gui/preprocessing/mesh_canvas.py`, `canvas_logic.py`, `canvas_raster.py` |
| 2 | Spreadsheet y tablas | `gui/preprocessing/pre_tab.py`, `_table_helpers.py` |
| 3 | Proceso | `gui/processing/proc_tab.py` |
| 4 | Post-Proceso | `gui/postprocessing/*` (panel de detalles, probe, vista 3D) |
| 5 | Diálogos | `gui/dialogs/*` |
| 6 | Ventana, menús, atajos, barra de estado | `gui/main_window.py`, `gui/widgets/*` |
| 7 | Módulos educativos M0–M3 | `education/mod00..mod03`, `overlay_module.py` |
| 8 | Módulos educativos M4–M7 | `education/mod04..mod07`, `module_launcher.py` |
| 9 | Componentes educativos y Teoría | `education/components/*`, `gui/dialogs/theory_hub_dialog.py` |
| 10 | Memoria de cálculo y figuras | `file_io/memoria_calculo.py`, `file_io/figure_export.py` |
| 11 | Modelo, salud y validación | `models/*` |
| 12 | Resultados numéricos visibles | `fem/*`, solo lo que llega al alumno |
| 13 | Interoperabilidad y archivos | `file_io/*` restante, DXF, CSV/ZIP, `.edufem` |
| 14 | Cumplimiento de la tesis | una sección de `tesis/` contrastada contra el software |

Regla de la cola: **primero se drenan los ítems del BACKLOG que pertenecen a tu área**;
recién cuando no queda ninguno, buscás material nuevo en ella. Si tu área quedó sin nada que
hacer, decilo en la bitácora y pasá a la siguiente sin gastar la sesión.

### Antes de refactorizar: el contrato del área

Escribí (en el mensaje de trabajo, no hace falta commitearlo) qué hace hoy el área: cada
función pública y **todos** sus llamadores encontrados con `grep`, cada string visible al
alumno, cada diálogo con su geometría y sus teclas, cada resultado numérico. Al terminar,
verificá el contrato punto por punto. Lo que cambie tiene que ser porque lo decidiste, no
porque se cayó.

## 5. Margen sobre las decisiones congeladas

**Podés revertir una decisión congelada si la justificás.** Es una autorización explícita
del autor (2026-09-08) y aplica tanto a la paleta de `config/settings.py` como a las filas
de [no-reintroducir.md](../convenciones/no-reintroducir.md) y a la estructura de la GUI.

Pero congelada significa que alguien ya la pensó, así que el protocolo no es opcional:

1. **Leé el motivo real** en el capítulo de `convenciones/` que la fila enlaza. La tabla es
   un índice; el capítulo es la fuente de verdad. Muchas decisiones parecen arbitrarias
   hasta que se lee por qué se tomaron (el halo grueso de la selección, la ausencia de
   scrollbars, los 3 menús).
2. **Que la mejora sea concreta y verificable**, no estética abstracta. "Se ve más moderno"
   no alcanza; "el alumno no puede saber qué elemento está seleccionado en una malla de
   32×32 porque el relleno punteado se pierde a ese zoom" sí.
3. **Actualizá el capítulo y la fila de `no-reintroducir.md`** en el mismo commit. Nunca
   dejes dos reglas en conflicto: se borra la vieja, no se agrega una nota de
   "actualización".
4. **Destacalo en la bitácora** bajo `DECISIÓN CONGELADA REVERTIDA`, con el antes, el
   después y el motivo. El autor lo revisa; si no le gusta, revierte un commit y no una
   arqueología.

**Tres cosas siguen sin discusión**, porque no son estética sino consecuencias medidas:
`numba` y los kernels `@njit` (nunca corrían en el `.exe`), el colormap **jet** para todos
los campos, y la sustitución de la versión legible de `fem/` por la vectorizada.

## 6. La tesis es especificación, y también se corrige

`tesis/` define el alcance comprometido ante el tribunal. Vale en las dos direcciones:

- **Software equivocado** (lo normal): la tesis describe una capacidad, un valor o un flujo
  que el programa no cumple → **se arregla el software**.
- **Tesis desactualizada**: el software cambió y el `.tex` quedó viejo → **se corrige el
  `.tex`** con la skill `tesis-redactar` / `tesis-revisar`, respetando el español académico y
  la citación Vancouver. Cambios mínimos y quirúrgicos: la frase que quedó falsa, no el
  párrafo entero.
- **Números**: cualquier cifra de la tesis que salga del software (tablas de V&V, VM máximo,
  tiempos) se regenera con su script (`tests/vv_*.py`, `tesis/figuras/gen_anexo_calculo.py`),
  nunca se edita a mano.
- **Prohibido** tocar el marco metodológico, la hipótesis, los objetivos, la bibliografía y
  las decisiones que `tesis/README.md` marca como **decisiones de autor**. Eso lo resuelve el
  autor con el tribunal; si detectás un problema ahí, va al BACKLOG.
- Si tocaste `tesis/`, **compilá** antes de pushear. Un `.tex` que no compila es un gate rojo.

## 7. Cómo se caza una incongruencia

No alcanza con leer el archivo. Las cosas que rompen la intuitividad se encuentran
recorriendo el flujo del alumno y preguntando en cada paso *"¿cómo sabe el alumno esto?"*:

- **Estados invisibles**: modo dibujo, ortho, selección activa, módulo educativo abierto,
  proyecto sin resolver, proyecto modificado. Si cambia el comportamiento y no cambia la
  pantalla, es un defecto.
- **Callejones sin salida**: el modelo no resuelve y el mensaje no dice qué falta ni cómo
  arreglarlo. Todo error visible al alumno debe nombrar la causa y el siguiente paso
  (`models/model_health.py` + su hint en `EDUCATIONAL_HINTS` es la vía; la GUI no valida por
  su cuenta).
- **Excepciones tragadas**: `except Exception: pass` en un camino que el alumno puede
  recorrer. O se maneja de verdad, o se muestra.
- **Dos vías para lo mismo** con nombres distintos, o una acción destructiva sin `_capture()`
  previo (si no hay snapshot, no hay undo: es la regla dura 4 y también un defecto de UX).
- **Vocabulario**: todo string visible en español y con la terminología canónica de
  `CLAUDE.md` (**GDL**, **MEF**, restricción, tensión, malla). Un `DOF` o un `FEM` que llegue
  al alumno es un bug.
- **Números sin `fmt(value, kind)`**, unidades ausentes, decimales que no dicen nada.
- **Coherencia entre fases**: el mismo dato con distinto nombre, formato o color en Pre,
  Proceso, Post, módulos y memoria PDF.

## 8. Gates — ninguno es opcional

```bash
pip install -r requirements.txt           # solo si el sandbox viene sin el stack
python -m tests.run_gates                 # obligatorio siempre (~30 s, sin pantalla)
python -m tests.run_gates --con-latex     # si tocaste memoria, teoría o LaTeX
python -m tests.run_gates --con-vv        # si tocaste fem/ o los números de la tesis
```

Instalar `requirements.txt` **no es** "agregar una dependencia": es preparar el entorno, y es
obligatorio si el sandbox arranca sin el stack. Lo prohibido es sumar una librería que hoy no
está en ese archivo, o editarlo. Si el intérprete se llama `python3`, usá `python3`.

`run_gates` importa los 97 módulos del proyecto, audita los hex literales de `gui/` y
`education/` (regla dura 2) y corre la suite headless, incluida la regresión numérica que
exige la regla dura 21. **Sale 0 o no se pushea.**

Si tocaste `tesis/`, además: `cd tesis && latexmk -pdf main.tex` (o `pdflatex` dos veces más
`biber`) sin errores.

**Lo que el gate no puede juzgar es cómo se ve la aplicación.** El sandbox no tiene pantalla
y el juicio visual es del autor. Por eso todo cambio que se note a la vista termina en un
**pendiente visual** en el BACKLOG, con: qué mirar, en qué modelo, qué debería verse, y cómo
revertir si está mal. Máximo 3 por sesión, y van arriba de todo en el resumen final.

Si el gate se pone en rojo por algo que rompiste y no podés arreglarlo con seguridad:
`git checkout -- <archivos>` y reportalo. **Jamás pushear con el gate en rojo.**

## 9. Cierre: bitácora, commit y push

1. **Apilá** tu entrada en [BITACORA.md](BITACORA.md) (append al final, **nunca** reescribir
   entradas previas) con el formato que ese archivo define.
2. **Actualizá el BACKLOG**: cerrá lo que resolviste, sumá lo que encontraste y no hiciste,
   marcá el área siguiente y agregá los pendientes visuales.
3. **Actualizá `../notas/ESTADO.md`** solo si cambió el panorama general del proyecto.
4. **Commit en español**, con el código, la bitácora, el BACKLOG y los capítulos de
   `convenciones/` que hayas tocado. Cerrá el mensaje con
   `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.
5. **`git push origin main`. Sin push el trabajo no existe.** Si lo rechazan:
   `git pull --rebase origin main` y reintentá el push **normal**, nunca forzado. Si el
   rebase da conflicto y no lo podés resolver con seguridad, abortalo, no pushees y
   reportalo en la bitácora: puede haber otra sesión o el propio autor trabajando sobre el
   mismo repo.

## 10. Prohibido

- Crear ramas, abrir PRs, hacer force-push, reescribir historia.
- Agregar dependencias, tocar `requirements*.txt`, correr `pip install`.
- Pushear con el gate en rojo, o "arreglar" un test para que pase.
- Reescribir entradas previas de la bitácora, o borrar ítems del BACKLOG sin cerrarlos.
- Reintroducir `numba`/`@njit`, cambiar el colormap **jet**, o reemplazar la versión legible
  de `fem/` por la vectorizada.
- Hex literales fuera de `config/settings.py`; rutas que no pasen por `resource_path`;
  mutaciones sin `_capture()`; `tree.selection_set` desde el callback del canvas;
  `2*(nid-1)` para índices de GDL; imports de `tkinter`/`matplotlib` en `fem/`.
- Un cuarto menú o una toolbar (la barra tiene exactamente Archivo / Modelo / Ayuda).
- Tocar el marco metodológico, la hipótesis, los objetivos o la bibliografía de la tesis.
- Mover cualquiera de las rutas frágiles de [../MAPA.md](../MAPA.md) §3.
- Dejar el repo con cambios sin commitear al terminar.

## 11. Resumen final de la sesión, en este orden

1. **Pendientes visuales para el autor** (qué abrir, qué mirar, qué debería verse) — o
   "ninguno".
2. **Decisiones congeladas revertidas** — o "ninguna".
3. Área trabajada y qué cambió, en una línea por cambio.
4. Errores encontrados y corregidos en el camino.
5. Estado de los gates (`run_gates`, LaTeX si aplica).
6. Hash pusheado.
7. Área siguiente.
