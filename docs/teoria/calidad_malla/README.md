# Métricas de calidad de malla — documentos teóricos

Tres documentos LaTeX **complementarios** (no redundantes) que sustentan
[`fem/mesh_quality.py`](../../../fem/mesh_quality.py) y el módulo educativo **M0**. Se leen
en este orden.

| Documento | Responde | Cuándo leerlo |
|---|---|---|
| [mesh_quality_theory](mesh_quality_theory.pdf) · [`.tex`](mesh_quality_theory.tex) | **Qué mide cada métrica.** Notación, marco teórico y desarrollo de las métricas de distorsión de Robinson (relación de aspecto, conicidad, sesgo) y del Jacobiano escalado | Al tocar el cálculo de una métrica |
| [mesh_quality_normalized_metrics](mesh_quality_normalized_metrics.pdf) · [`.tex`](mesh_quality_normalized_metrics.tex) | **Por qué se presentan como se presentan.** Justificación del rango, los cortes de aceptabilidad y las decisiones de coloreado | Al tocar los umbrales, las barras o los colores de M0 |
| [mesh_quality_worked_example](mesh_quality_worked_example.pdf) · [`.tex`](mesh_quality_worked_example.tex) | **Cómo se calcula, con números.** Ejemplo paso a paso sobre un Q4 distorsionado y su equivalente Q9 | Para verificar una implementación contra valores conocidos |

## Decisiones vigentes que salen de acá

- Las dos métricas que muestra M0 son **Jacobiano escalado** (`SJ ∈ [-1, 1]`, valor crudo) y
  **compacidad / Stretch** (`∈ [0, 1]`), cada una en su rango bibliográfico completo
  (Verdict/Cubit, SAND2007-1751).
- Los cortes de aceptabilidad son **distintos por métrica** (`SJ ≥ 0,50`, `Stretch ≥ 0,25`),
  literales de la bibliografía. **No unificarlos.**
- El coloreado **bipolar gris-centro** está desaconsejado por
  `mesh_quality_normalized_metrics`: hacía ilegible la frontera de validez.

El detalle de cómo esto se traduce a la interfaz está en
[../../convenciones/modulos-educativos.md](../../convenciones/modulos-educativos.md) (M0), y
las prohibiciones asociadas en
[../../convenciones/no-reintroducir.md](../../convenciones/no-reintroducir.md).

## Compilar

```bash
pdflatex mesh_quality_theory.tex   # requiere MiKTeX o TeX Live
```

Los `.pdf` compilados se versionan junto al `.tex` para poder consultarlos sin LaTeX
instalado.
