# Auditorías archivadas

Informes **superados** por auditorías posteriores o ya implementados. Se conservan porque la
trazabilidad de las decisiones es parte de su valor: varias reglas del canon
(`docs/convenciones/`) se justifican citando estos documentos.

**No los leas para saber qué falta hacer** — para eso está
[../ESTADO_AUDITORIAS.md](../ESTADO_AUDITORIAS.md), que consolida el estado real.

| Archivo | Qué es |
|---|---|
| `2026-05-25_auditoria_tecnica.md` | Auditoría de rendimiento, arquitectura y seguridad. *Quick wins* aplicados; el resto lo absorbió el informe del 05-31 |
| `2026-05-30_auditoria_canvas_ux.md` | Auditoría UX/UI del `MeshCanvas` contra Abaqus, ANSYS, GiD y SAP2000. **Implementada** (LOD, culling, focus-and-context, silueta, hover). Citada desde comentarios de `config/`, `gui/preprocessing/canvas_logic.py` y `models/mesh_utils.py` |
| `2026-05-31_auditoria_integral.md` | Auditoría integral con verificación adversarial. P0–P2 implementados el 2026-06-01; P3 (god objects, ciclo `gui`↔`education`) diferido con justificación |
| `2026-06-03_auditoria_tesis.tex` / `.pdf` | Revisión de la tesis anterior a la del 06-10 |
| `2026-05-03_propuesta_ux_modulos.tex` / `.pdf` | Propuesta de rediseño UX de los módulos educativos. **Ejecutada**: los 8 módulos son overlays sobre el canvas |
| `plantilla_latex_ejemplo.tex` | Plantilla LaTeX con estilos de caja (tcolorbox) que sirvió de base a los documentos teóricos. Sin versionar (`.gitignore`) |
