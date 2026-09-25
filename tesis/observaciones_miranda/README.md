# Observaciones del Ing. Miranda (2026-09-25)

Documento de trabajo para el autor. **No forma parte de la tesis.**

El Ing. Julio Saúl Miranda (tribunal) hizo una revisión rápida de la tesis y dejó observaciones
sobre la causa y el efecto, el problema, el objetivo general, los objetivos específicos, la
hipótesis, las conclusiones y el formato. El autor las transmitió el 25-09-2026 y pidió adaptarlas
al contenido de la tesis, no aplicarlas al pie de la letra. Después agregó una: que
«Diagnosticar» no corresponde como objetivo y conviene unirlo a «Fundamentar».

| Archivo | Qué es |
|---|---|
| `diagnostico_miranda.pdf` (`.tex` al lado) | El diagnóstico de cada observación: lo que dijo, el veredicto (se adopta / se adopta con ajustes), por qué, y el ancla en sus láminas (PP, OG, SP) o en los talleres de Barrios. Incluye el antes y después de la formulación, la tríada objetivo → capítulo → conclusión → recomendación, y qué responder si pregunta por los ajustes. Puede mostrarse al tutor o al propio Ing. Miranda |

Dónde quedó aplicado: la versión **final3** de la tesis (`tesis/main_final3.tex` +
`tesis/capitulos_final3/`). El registro de cada cambio está en
[`../auditoria_final/IMPLEMENTACION-FINAL3.md`](../auditoria_final/IMPLEMENTACION-FINAL3.md).

Compilar el diagnóstico (usa las figuras de `../capitulos_final3/figuras/`):

```
cd tesis/observaciones_miranda
pdflatex diagnostico_miranda.tex    # dos veces
```

Las láminas citadas están en `tesis/Material docente/`:

- **PP**: *Planteamiento del problema científico e hipótesis*.
- **OG**: *Cómo se construye el objetivo general*.
- **SP**: *Situación problemática, objeto de estudio y campo de acción*.
- **T1…T6**: los talleres de Barrios.
