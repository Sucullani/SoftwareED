### Cobertura real de la batería de V&V (reconstruida de 3.2 a 3.5)

| Dimensión | Lo que la batería SÍ ejercita | Lo que NO cubre |
|---|---|---|
| Estado plano | Tensión plana: MMS + Timoshenko + Cook. Deformación plana: MMS (dos configuraciones). | Deformación plana sin ninguna referencia externa: no hay caso analítico ni contraste con otro programa. Es el estado que la práctica civil emplea con más frecuencia (lo reconocen las recomendaciones, folio 94). |
| Elemento | Q4 y Q9 en MMS y en Cook (desplazamiento u_y). | Tensiones del Q4 sin contraste externo alguno: la viga de Timoshenko se resolvió únicamente con Q9 (nota de la Tabla 3.6) y Cook solo mide un desplazamiento. La fila "Timoshenko sigma_x" de la Tabla 3.6 lleva raya en la columna Q4. |
| Tipo de carga | Volumétrica (término fuente del MMS), uniforme sobre el borde (Timoshenko), tangencial total (Cook), puntual (ejemplo canónico). | Carga superficial linealmente variable: no interviene en ningún caso de referencia (declarado en 2.1 y en Limitaciones). |
| Material | Adimensional (MMS, Cook) y un único hormigón E = 217 370 kgf/cm2, nu = 0,20 (Timoshenko). | Un solo material de ingeniería civil; nu próximo a 0,5 (bloqueo volumétrico) no se ensaya, solo se señala en M4. |
| Magnitud contrastada | Desplazamiento (L2, H1, u_y, flecha), sigma_x, y en un punto sigma_y y tau_xy. | Reacciones solo por equilibrio global (una suma), no punto a punto; tensiones principales y von Mises sin contraste externo. |
| Malla | Regular y distorsionada en MMS; una única malla 56x8 en Timoshenko; secuencias N = 2 a 32 en Cook. | Timoshenko no es estudio de convergencia (declarado): un solo tamaño de malla. |

### Estatus de las afirmaciones fuertes de 3.7, 3.8, Conclusiones, Aportes y Resumen

| Afirmación | Folio | Estatus real | El texto lo deja claro |
|---|---|---|---|
| Tasas de convergencia teóricas reproducidas | 65, 88, i | Medida (4 configuraciones MMS) | Sí, salvo el salto a "libre de errores de orden" en Conclusiones |
| Errores del 0,04 % / 0,26 % / 0,56 % | 69, 84, 88, i | Medida (un caso) | No: el Resumen omite el 4,56 % de sigma_y y el plural "problemas de referencia estudiados" generaliza desde un caso |
| Bloqueo del Q4 frente al Q9 (trece veces) | 71, 88 | Medida | Sí |
| Equilibrio de reacciones | 69, 88 | Medida (residuo 1,7e-13) | Parcial: Conclusiones suprime la cifra |
| 18 de 18 destrezas y conceptos con instrumento | 77, 80, 89, i | Supuesta por diseño (cotejo del autor, universo recortado al alcance) | No en el punto de la afirmación; sí en 3.1 y en Limitaciones |
| 4 de 4 principios con encarnación | 77, 81, 89 | Supuesta por diseño (los principios guiaron el diseño) | No: se presenta como corroboración independiente |
| Siete de siete etapas con módulo | 75, 78 | Medida, pero sobre un canal de nueve etapas | No en el punto; sí catorce folios después |
| Vacío en el estado del arte | 15, 17 | Fundamentada, con alcance no declarado | No: "no existe" y "ninguno reúne" sin acotar la revisión |
| Dos instrumentos reutilizables | 91 | Supuesta (una sola aplicación, un solo evaluador) | No |
| Efecto sobre el criterio del estudiante | 84, 89, ii, 94 | Fundamentada en literatura ajena, no medida | Sí, de forma explícita y repetida (es el punto mejor calibrado del documento) |
