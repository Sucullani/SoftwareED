# Solucionador disperso — documento teórico

Explica cómo resuelve EduFEM el sistema reducido `K_ff u_f = F_f` **sin invertir la matriz de
rigidez**, con ejemplos resueltos a mano y cifras medidas con el propio motor. Sustenta
[`fem/solver.py`](../../../fem/solver.py), [`fem/batch.assemble_sparse`](../../../fem/batch.py) y la
constante `SOLVER_PERMC_SPEC` de [`config/settings.py`](../../../config/settings.py).

| Documento | Responde |
|---|---|
| [solucionador_disperso](solucionador_disperso.pdf) · [`.tex`](solucionador_disperso.tex) | Por qué no se invierte `K`; la factorización LU paso a paso; los formatos COO, CSR y CSC y cómo arma EduFEM la matriz; qué es el llenado; el ordenamiento de mínimo grado sobre `Kᵀ + K`; qué hace SuperLU por dentro; el código, línea por línea; preguntas de defensa con respuesta corta |

## Decisiones vigentes que el documento explica (no las cambia)

- **Nunca se invierte `K`**: se factoriza con SuperLU (`scipy.sparse.linalg.spsolve`) y se
  resuelve por sustitución. Las únicas inversas del motor son el Jacobiano 2×2 (cofactores) y
  la matriz de extrapolación de tensiones, constante por tipo de elemento.
- **`SOLVER_PERMC_SPEC = "MMD_AT_PLUS_A"`**: mínimo grado sobre el patrón de `Aᵀ + A`, que para
  `K` simétrica es el grafo de la propia malla. Frente al `COLAMD` por defecto de SciPy da
  alrededor de la mitad de llenado.
- **`spsolve`, no `splu`**: un solo vector de cargas por resolución; las dos funciones usan el
  mismo SuperLU y el mismo `permc_spec`.
- **Sin Cholesky disperso**: SciPy no lo trae y CHOLMOD (`scikit-sparse`) sería una dependencia
  binaria más para el instalador. La tesis lo deja como recomendación.
- **Sin RCM**: retirado el 2026-09-06 ([roadmap-fem.md](../../convenciones/roadmap-fem.md), ítem 3).

## Regenerar

Todas las cifras del texto entran por macros `\cifra{...}` desde `datos/cifras.tex`; las filas
de tabla, desde `datos/tabla_*.tex`; los grafos del mínimo grado, desde `figuras/md_*.tex`. Nada
se copia a mano. Desde la raíz del repositorio:

```bash
python docs/teoria/solucionador/generar_datos.py                # todo (unos 7 min)
python docs/teoria/solucionador/generar_datos.py --rapido       # sin los casos de más de 10 s
python docs/teoria/solucionador/generar_datos.py --solo-figuras # reusa datos/mediciones.json
cd docs/teoria/solucionador && pdflatex solucionador_disperso.tex   # dos veces
```

El guion verifica antes en aritmética exacta los cuatro ejemplos a mano (cadena de resortes,
estrella, malla 2×2 con búsqueda exhaustiva del orden óptimo, barra en COO con la misma
`assemble_sparse` del motor) y que el desplazamiento de la traza coincida con
`docs/vyv/datos/cook.csv`; si algo deja de cumplirse, se detiene antes de escribir.

Los tiempos dependen del equipo y de su carga: el documento cita sobre todo razones entre
tiempos. Los `.pdf` compilados se versionan junto al `.tex` para poder consultarlos sin LaTeX.
