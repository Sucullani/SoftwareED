### A. Tabla propuesta para los umbrales de calidad (folio 56)

Sustituye a la oración de unas 150 palabras que hoy los enumera en línea.

| Índice | Símbolo | Qué mide | «Bueno» | «Aceptable» |
|---|---|---|---|---|
| Jacobiano escalado | q_SJ | Cuánto se aparta el elemento de la forma rectangular ideal; 1 es el cuadrado perfecto, 0 un elemento degenerado | ≥ 0,70 | ≥ 0,30 |
| Relación de jacobianos | R_J | Uniformidad de la distorsión dentro del elemento (mínimo sobre máximo entre puntos de Gauss) | ≥ 0,50 | ≥ 0,20 |
| Relación de aspecto | AR | Cociente entre el lado mayor y el menor; mide el alargamiento | ≤ 3 | ≤ 5 |
| Sesgo (taper) | T_R | Desviación respecto del paralelogramo; mide el afilamiento de los lados | ≤ 0,30 | ≤ 0,50 |
| Desviación de nodos intermedios (solo Q9) | — | Apartamiento del nodo intermedio respecto del punto medio del lado | ≤ 0,10 | ≤ 0,25 |

Notas al pie de la tabla: (1) el corte del jacobiano escalado para rechazar un elemento se eleva de 0,30 a 0,50 —el valor que Verdict fija para el triángulo y el hexaedro— por prudencia pedagógica; (2) el módulo M0 marca como «buenos» los elementos con q_SJ ≥ 0,80 y Q ≥ 0,50.

### B. Leyendas de figura reescritas (autosuficientes)

| Figura (folio) | Leyenda actual | Leyenda propuesta |
|---|---|---|
| Arquitectura (52) | «Arquitectura por capas centrada en el modelo de proyecto.» | «Arquitectura por capas de EduFEM. Cada flecha indica dependencia: una capa solo invoca a las que están por debajo, y todas comparten por referencia el mismo objeto de proyecto; el motor numérico no depende de ninguna capa de interfaz, por lo que puede ejecutarse sin entorno gráfico.» |
| Lienzo (55) | «Lienzo compartido con modo de dibujo y nivel de detalle por acercamiento.» | «Lienzo compartido durante el trazado de un elemento: los vértices ya marcados, el anclaje al nodo existente más próximo y, a la derecha, la misma malla alejada, donde el nivel de detalle reduce el dibujo a la silueta del dominio.» |
| Módulo (57) | «Módulo educativo como capa interactiva sobre el lienzo.» | «Módulo M2 (Jacobiano) abierto como capa sobre el lienzo: el panel flotante muestra la matriz jacobiana evaluada en el punto de Gauss seleccionado, que aparece resaltado a la vez sobre el elemento real del modelo.» |
| Post-proceso (59) | «Visualización de resultados en el post-proceso.» | «Post-proceso del modelo de la viga en voladizo: contorno de la tensión de von Mises con interpolación continua entre nodos, malla deformada superpuesta en trazo alámbrico con factor de escala X y geometría original atenuada como referencia.» |

Las figuras concretas deben confirmarse contra el PDF antes de fijar la redacción: el detalle de cada leyenda (módulo mostrado, campo representado, factor de escala) debe corresponder a lo que la imagen realmente muestra.