# Backlog de la rutina de mejora continua

Cola de trabajo entre sesiones. Cada sesión **empieza acá** y **termina acá**: toma el área
marcada como siguiente, drena primero los ítems que le pertenecen, y antes de cerrar suma lo
que encontró y no hizo.

Reglas del archivo, en [RUTINA.md](RUTINA.md) §4 y §9. Historial de lo hecho, en
[BITACORA.md](BITACORA.md).

---

## Área siguiente

> **1 — Canvas del Pre-Proceso** (`gui/preprocessing/mesh_canvas.py`, `canvas_logic.py`,
> `canvas_raster.py`). Capítulo a leer antes:
> [../convenciones/canvas-preproceso.md](../convenciones/canvas-preproceso.md).

Al cerrar la sesión, reemplazá esta línea por el área que sigue en la rotación de
[RUTINA.md](RUTINA.md) §4 (1 → 2 → … → 14 → 1).

---

## Abierto

Formato: `[área Nº] descripción — evidencia — quién decide`.

### Coherencia con la tesis

- **[14] La tesis todavía dice que la memoria PDF necesita una distribución LaTeX
  instalada.** `tesis/capitulos/06_anexos.tex:14` ("La generación de la memoria de cálculo en
  PDF necesita, además, una distribución LaTeX instalada (MiKTeX o TeX Live) […] el programa
  abre un diálogo que explica cómo instalar MiKTeX") y `06_anexos.tex:46` ("Un único
  componente es opcional: una distribución LaTeX"). Desde el 2026-09-08 el instalador embebe
  un TeX Live recortado y `education/components/latex_runtime.py` lo resuelve antes que el
  PATH: la afirmación es falsa para la vía de instalación recomendada. `README.md:35` y
  `installer/dist_extra/LEEME.txt:48` ya están corregidos; la tesis no. **Corrige el `.tex`**
  (es el caso "tesis desactualizada" de [RUTINA.md](RUTINA.md) §6), sin tocar el resto del
  Anexo A. Ojo: el diálogo de fallback (`gui/dialogs/pdflatex_missing_dialog.py`) sigue
  existiendo y sigue siendo correcto para la versión portable sin la carpeta `texlive/`.

- **[14] Barrido pendiente, capítulo por capítulo.** Nadie contrastó todavía `tesis/` contra
  el software de forma sistemática. Cada vez que toque el área 14, tomá **una** sección que no
  esté marcada acá abajo, verificá cada afirmación comprobable contra el código, y anotá la
  sección como barrida con la fecha. Secciones barridas hasta ahora: *ninguna*.

### Interacción e incongruencias

- **[transversal] 274 `except Exception` en `gui/` + `education/`.** Algunos son legítimos
  (Tk destruyendo widgets durante el cierre, `iconbitmap` que puede no existir). Otros tragan
  un fallo en un camino que el alumno recorre y lo dejan sin saber qué pasó. **No hacer un
  barrido masivo**: cada sesión revisa los de **su** área, decide caso por caso, y anota
  acá cuántos revisó y cuántos cambió. Revisados hasta ahora: 0 de 274.

### Heredado de otras revisiones

- **Hallazgos abiertos** de [../auditorias/ESTADO_AUDITORIAS.md](../auditorias/ESTADO_AUDITORIAS.md):
  antes de trabajar un área, mirá si ya tiene hallazgos ahí y cerralos en el mismo pase.
- **Dictamen del 2026-09-07**: quedan abiertos los hallazgos MAYOR y MENOR no mecánicos
  (objeto de estudio vs. población, hipótesis circular, preliminares, estado del arte). Son
  **decisiones de autor** sobre el marco metodológico: la rutina **no los toca**, están acá
  solo para que ninguna sesión crea que se olvidaron.

---

## Pendientes visuales para el autor

Lo que el gate no puede juzgar. Cada ítem dice qué abrir, qué mirar y cómo revertir.

- **Post-Proceso y Memoria tras la vectorización y la corrección de la extrapolación Q4**
  (abierto desde el 2026-09-07, ver [../notas/ESTADO.md](../notas/ESTADO.md)). Abrir la GUI
  con el ejemplo canónico Q4 y con Cook 32×32 Q9: gradiente, isolíneas, modo crudo, probe y
  vista 3D; después generar una Memoria de Cálculo. **Todas** las tensiones nodales Q4
  cambiaron (VM máximo del ejemplo canónico: 977,46 → 864,70); Q9 no cambió.
- **TeX Live embebido** (abierto desde el 2026-09-08). Exportar Memoria (Q4 canónico y Cook
  Q9, ambos estilos) y la Teoría MEF: deberían verse idénticas a las de MiKTeX. Probar
  `installer/Output/EduFEM-Setup.exe` en una PC **sin MiKTeX**.
- **Tests que necesitan un Tk real**: `python -m tests.run_gates --con-gui` corre
  `test_draw_mode` y `test_selection_integration`, que el sandbox no puede ejecutar. Conviene
  correrlo en Windows de vez en cuando.

---

## Cerrado

Se mueve acá lo resuelto, con la sesión que lo cerró. Se conserva: evita que una sesión
futura reabra algo ya decidido.

- *(vacío — la rutina arranca el 2026-09-08)*

---

## Propuestas que esperan al autor

Cosas que la rutina **no** hace sin un OK explícito: cambios de alcance, dependencias nuevas,
o reversiones de decisiones congeladas cuya justificación no es evidente.

- *(vacío)*
