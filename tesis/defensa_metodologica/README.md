# Defensa metodológica: tesis tecnológica frente al molde experimental

Material de estudio y de respaldo para la defensa de la tesis final (`tesis/main_final.pdf`).
**No forma parte de la tesis** ni de la presentación principal (`tesis/presentacion/final/`).

| Archivo | Qué es |
|---|---|
| `contexto_defensa.pdf` | Documento de estudio (23 p.): la tesis en una página, la respuesta madre ante «debió ser experimental», la diferencia experimental/tecnológica con sus fuentes, el material docente lámina por lámina, 14 argumentos con cita literal y página, pieza por pieza, 34 preguntas probables, lo que no hay que decir, cifras, flancos abiertos y chuleta final |
| `contexto_defensa.tex` | Fuente del PDF. Compilar con `pdflatex contexto_defensa` dos veces |
| `respaldo_diferencia.html` | Seis láminas animadas de respaldo, en el estilo de la presentación final: 1) experimental o tecnológica (tarjetas que giran), 2) dos procesos (García-Córdoba, fig. 1.5), 3) sí hay experimento (gráfica real de convergencia), 4) el material de la Carrera, 5) la pregunta decide el método, 6) tesis, no proyecto de grado |

## Cómo usar las láminas

Abrir `respaldo_diferencia.html` con doble clic: funciona **sin internet** (toma la fuente Inter
de `../presentacion/final/assets/terceros/`). Teclas: `→`, espacio o `PageDown` avanzan paso a
paso; `←` retrocede; `1`-`6` saltan a una lámina; `N` muestra el guion de lo que conviene decir;
`T` cambia entre tema oscuro y claro; `F` pantalla completa. Un clic en una tarjeta de la lámina 1
la gira sola; el interruptor gira todas. En la lámina 3, «Ver datos» muestra la tabla de la gráfica.

Se puede enlazar desde la presentación principal como diapositiva de respaldo (por ejemplo, un
botón con `href="../../defensa_metodologica/respaldo_diferencia.html#diferencia"`); las anclas son
`#diferencia`, `#procesos`, `#experimento`, `#material`, `#pregunta` y `#modalidad`.

## De dónde sale cada cita

Todas las páginas se leyeron en el ejemplar: `tesis/bibliografia/` (Hevner, Peffers, Wieringa,
Hernández-Sampieri, Álvarez de Zayas y Oberkampf con capa de texto; García-Córdoba, que es un
escaneo, como imagen) y `tesis/Material docente/` (el número de lámina es la página del PDF).
Las páginas de la tesis son las impresas de `main_final.pdf` al 22 de septiembre de 2026: si la
tesis se recompila con cambios que muevan páginas, hay que revisarlas.
