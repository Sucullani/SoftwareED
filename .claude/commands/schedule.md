---
description: Auditoría general programada del repo EduFEM — genera informe priorizado en docs/auditorias/ sin aplicar fixes
---

Hacé una auditoría general del repositorio. Trabajá en una rama nueva
`audit/AAAA-MM-DD` (fecha de hoy) y NO apliques fixes todavía — el entregable
es un informe en `docs/auditorias/auditoria_AAAA_MM_DD.md` con hallazgos
priorizados. Si el archivo de una auditoría previa existe, compará y marcá
qué hallazgos persisten (reincidencias) y cuáles se resolvieron.

Auditá estas dimensiones, en este orden:

1. **Código muerto y duplicación**
   - Módulos, clases, funciones y constantes sin ningún consumidor
     (verificá con Grep antes de declarar algo muerto — incluí imports
     dinámicos y strings de registro tipo MODULE_MAP).
   - Lógica duplicada que ya tiene helper canónico (element_coords,
     lerp_hex, fit_matrix_widget, center_dialog, fmt, etc.).

2. **Cumplimiento de convenciones del proyecto** (según CLAUDE.md)
   - Hex literales fuera de config/settings.py: `Grep "#[0-9a-fA-F]{3,8}"`
     sobre gui/** y education/** (excluyendo config/). Esperado: 0 hits.
   - Strings user-facing con "DOF"/"FEM" en vez de GDL/MEF:
     `Grep "DOF"` y `Grep "FEM"` sobre **/*.py, clasificando cada hit
     (user-facing = violación; docstring/variable/magic string = OK).
   - Decimales hardcodeados (f"{x:.4f}") en vez de fmt(value, kind).
   - Mutaciones de usuario sin _capture() previo (rompen undo).
   - Flujos que crean elementos sin auto_expand_if_q9 al final.
   - Rutas a recursos que no pasan por resource_path() (fallan en el .exe).
   - Imports de tk/matplotlib/ttkbootstrap dentro de fem/ (debe ser puro).
   - Tolerancias numéricas locales en vez de las de config/settings.py.
   - Cosas marcadas "No reintroducir" en CLAUDE.md que hayan reaparecido.

3. **Correctitud y robustez**
   - Indexación de GDL: cualquier uso de `2*(nid-1)` directo en vez de
     node_index_map / dof_x / dof_y.
   - Setters que mutan el modelo sin is_modified=True / is_solved=False.
   - Callbacks Tk con referencias a objetos que pudieron ser reemplazados
     tras restore_from_dict / set_project; `after()` sin cancelar en cleanup.
   - Manejo de errores: excepts silenciosos que tragan bugs.
   - Serialización: campos en to_dict ausentes en from_dict o viceversa.

4. **Rendimiento**
   - Loops O(n²) sobre nodos/elementos donde hay dict lookup.
   - K.toarray() o materializaciones densas fuera del fallback documentado.
   - redraw() completo donde bastaría redraw_overlays_only().

5. **Tests y cobertura funcional**
   - Correr TODOS los scripts de tests listados en la sección "Running"
     de CLAUDE.md y reportar pass/fail de cada uno.
   - Identificar áreas tocadas recientemente (git log) sin test asociado.

6. **Consistencia documental**
   - Contradicciones internas en CLAUDE.md (reglas que se invalidan entre
     sí, secciones históricas que parecen vigentes).
   - Enlaces [archivo](ruta) rotos (archivos renombrados/eliminados).
   - Dependencias en requirements.txt sin un solo import (estilo reportlab),
     e imports usados sin declarar.

7. **Seguridad e higiene de repo**
   - Patrones peligrosos: eval/exec/pickle.load/shell=True/os.system con
     input del usuario; secretos o credenciales hardcodeados.
   - Artefactos generados commiteados que deberían estar en .gitignore
     (__pycache__, dist/, build/, PDFs compilados, logs de compilación).
   - Archivos > 5 MB fuera de resources/.
   - Inventario de TODO/FIXME/HACK en código de producción.

8. **Empaquetado (.exe)**
   - build.spec sincronizado con los recursos reales (resources/, hidden
     imports, fuentes TTF).
   - Toda ruta a recurso pasa por config.settings.resource_path
     (espejo con gui.fonts_loader._resources_root en sync).

Formato del informe: tabla por dimensión con columnas
Severidad (crítico/alto/medio/bajo) · Archivo:línea · Hallazgo ·
Fix propuesto (1 línea). Al final, un top-10 priorizado por
impacto/esfuerzo, una lista explícita de "falsos positivos descartados"
(cosas que parecen problema pero son decisión documentada en CLAUDE.md),
y el delta contra la auditoría anterior si existía.

No modifiques código en esta pasada. Cuando termine el informe,
commiteá solo el .md y pushealo a la rama de auditoría.
