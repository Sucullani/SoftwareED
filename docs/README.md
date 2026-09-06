# Documentación de EduFEM

Índice de todo lo que hay en `docs/`. Para el mapa completo del repositorio ver
[MAPA.md](MAPA.md); para las reglas de trabajo, [../CLAUDE.md](../CLAUDE.md).

## Convenciones del proyecto — [convenciones/](convenciones/)

El canon de EduFEM, partido en capítulos que se leen **bajo demanda**. Es la fuente de
verdad sobre cómo está construido el software y por qué.

| Archivo | Cubre |
|---|---|
| [arquitectura.md](convenciones/arquitectura.md) | `ProjectModel` e indexación de GDL · undo/redo · cascadas de borrado · helpers de malla · validador de salud · motor `fem/` · GUI y barra de menús · diálogos · importación DXF |
| [modulos-educativos.md](convenciones/modulos-educativos.md) | Los 8 módulos M0..M7 · infraestructura de overlays · filosofía minimalista · componentes de `education/` |
| [canvas-preproceso.md](convenciones/canvas-preproceso.md) | Spreadsheet de 5 tablas · selección múltiple y sincronización con el canvas · filas fantasma · modo dibujo · render, LOD y colormaps del canvas · identidad visual por fase |
| [memoria-calculo.md](convenciones/memoria-calculo.md) | Los 2 estilos del PDF · pipeline compartido · render de figuras con Pillow |
| [estilo-paleta.md](convenciones/estilo-paleta.md) | Tipografía · decimales por magnitud · paleta congelada · auditoría de color |
| [roadmap-fem.md](convenciones/roadmap-fem.md) | Estado y próximos pasos del motor (sparse, solver, vectorización, locking) |
| [no-reintroducir.md](convenciones/no-reintroducir.md) | **Índice de decisiones tomadas.** Consultar antes de agregar algo que "falta" |

Los mismos capítulos tienen un disparador automático en `.claude/rules/`: son archivos cortos
con un glob `paths:` que Claude Code carga solo cuando abre un archivo del área
(`education/`, `gui/preprocessing/`, `models/`…). Llevan el puntero al capítulo y las trampas
que rompen la app. El capítulo completo sigue siendo esta carpeta.

## Notas de trabajo — [notas/](notas/)

Espacio compartido entre sesiones y agentes: [notas/ESTADO.md](notas/ESTADO.md) dice qué
está en curso; [notas/README.md](notas/README.md) explica la convención.

## Auditorías — [auditorias/](auditorias/)

- [ESTADO_AUDITORIAS.md](auditorias/ESTADO_AUDITORIAS.md) — **empezar acá**: consolida los
  hallazgos de todas las auditorías y marca cuáles siguen abiertos.
- [2026-06-10_auditoria_general.md](auditorias/2026-06-10_auditoria_general.md) — última
  auditoría técnica del repositorio.
- [2026-06-10_revision_tesis.md](auditorias/2026-06-10_revision_tesis.md) — revisión de la
  tesis estilo tribunal.
- [historico/](auditorias/historico/) — informes superados, conservados como referencia.

## Teoría — [teoria/](teoria/)

- [teoria/calidad_malla/](teoria/calidad_malla/) — las tres piezas sobre métricas de calidad
  de elementos cuadriláteros (teoría, normalización, ejemplo resuelto). Sustentan
  `fem/mesh_quality.py` y el módulo educativo M0.

## Verificación y validación — [vyv/](vyv/)

Capítulo LaTeX de V&V + datos crudos y figuras. **No editar a mano**: `datos/*.csv` y
`figuras/*.png` los generan los scripts `tests/vv_mms.py`, `tests/vv_timoshenko.py` y
`tests/vv_cook.py`, y los consume la tesis.

## Fuera de `docs/`

| Dónde | Qué |
|---|---|
| [../README.md](../README.md) | Presentación del proyecto e instalación |
| [../CLAUDE.md](../CLAUDE.md) | Reglas duras + ruteo a los capítulos |
| [../tesis/README.md](../tesis/README.md) | Estado, decisiones y estructura de la tesis |
| [../installer/dist_extra/LEEME.txt](../installer/dist_extra/LEEME.txt) | Guía para el usuario final del `.exe` |
| [../tools/README.md](../tools/README.md) | Scripts de build y de generación de recursos |
