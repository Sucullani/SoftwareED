# Guion del video de defensa — EduFEM

Voz: es-BO-MarceloNeural (Microsoft Edge TTS, rate +11%) · duración 25:31 · 38 láminas.

| Lámina | Inicio | Duración | Título |
|---:|---:|---:|---|
| 1 | 00:00 | 37 s | Carátula |
| 2 | 00:37 | 7 s | Introducción |
| 3 | 00:43 | 46 s | La brecha |
| 4 | 01:29 | 53 s | Del problema al objetivo |
| 5 | 02:22 | 50 s | Objetivos |
| 6 | 03:11 | 54 s | Hipótesis y preguntas |
| 7 | 04:06 | 10 s | Base teórica |
| 8 | 04:16 | 57 s | Estado del arte |
| 9 | 05:13 | 47 s | De la forma fuerte a K u = F |
| 10 | 06:00 | 55 s | El canal isoparamétrico |
| 11 | 06:55 | 57 s | Dos patologías |
| 12 | 07:53 | 50 s | Recuperación de tensiones y verificación |
| 13 | 08:43 | 12 s | Diseño y desarrollo del modelo |
| 14 | 08:55 | 46 s | Variables |
| 15 | 09:40 | 29 s | Matriz de consistencia |
| 16 | 10:10 | 53 s | Procedimiento de verificación y validación |
| 17 | 11:03 | 39 s | Criterios de aceptación |
| 18 | 11:42 | 53 s | Arquitectura |
| 19 | 12:35 | 47 s | Pre-proceso |
| 20 | 13:22 | 47 s | Ocho módulos |
| 21 | 14:09 | 26 s | M5 |
| 22 | 14:35 | 36 s | Post-proceso |
| 23 | 15:11 | 64 s | Memoria de cálculo |
| 24 | 16:15 | 24 s | Demostración |
| 25 | 16:40 | 7 s | Presentación de resultados |
| 26 | 16:47 | 64 s | MMS |
| 27 | 17:51 | 36 s | El modelo no deriva |
| 28 | 18:27 | 61 s | Viga de Timoshenko |
| 29 | 19:28 | 42 s | Membrana de Cook |
| 30 | 20:10 | 7 s | Análisis de resultados |
| 31 | 20:17 | 37 s | Mismos GDL |
| 32 | 20:54 | 61 s | Escalabilidad y alcance |
| 33 | 21:55 | 7 s | Conclusiones y recomendaciones |
| 34 | 22:02 | 59 s | Seis objetivos, seis conclusiones |
| 35 | 23:02 | 42 s | Hipótesis confirmada |
| 36 | 23:44 | 42 s | Limitaciones |
| 37 | 24:26 | 48 s | Líneas de continuación |
| 38 | 25:14 | 17 s | Cierre |

## 1. Carátula  ·  00:00

Buenos días, señores miembros del tribunal. Mi nombre es Hedy Yhassmany Oyola Sucullani y presento la tesis «Desarrollo de software educativo de elementos finitos para el análisis estructural empleando el lenguaje de programación Python», para optar al título de Licenciatura en Ingeniería Civil. Su producto es EduFEM: un programa de escritorio, libre y en español, que expone el método de los elementos finitos paso a paso sobre el modelo del propio estudiante. La exposición sigue el orden reglamentario: introducción, base teórica, diseño y desarrollo del modelo, presentación y análisis de resultados, y conclusiones y recomendaciones.

## 2. Introducción  ·  00:37

Comienzo por la fundamentación: de dónde nace el problema, qué se estudia, qué me propuse y cómo lo contrasto.

## 3. La brecha  ·  00:43

La enseñanza del método enfrenta una brecha doble. Los textos clásicos presentan la formulación matricial con rigor, pero de manera abstracta: funciones de forma, Jacobiano, matriz B y cuadratura de Gauss aparecen como una cadena algebraica sin una geometría concreta a la vista, y el desarrollo a mano no escala más allá de uno o dos elementos. El software profesional hace lo contrario: recibe geometría, material y cargas, devuelve tensiones, y oculta todo el procesamiento intermedio; además es costoso, no tiene propósito didáctico y su localización al español es limitada. La consecuencia es concreta: el estudiante aprende a operar sin comprender, y no puede diagnosticar un resultado anómalo ni reconocer el bloqueo por cortante o los modos espurios. Esa es la situación problemática de la que parte esta tesis.

## 4. Del problema al objetivo  ·  01:29

De esa situación deriva el problema científico: ¿cómo debe construirse un software educativo para que exponga, de forma transparente, interactiva y numéricamente verificable, el canal de cálculo completo del método en elasticidad plana, de modo que cada etapa resulte observable y contrastable por el estudiante? La variable causa es la forma en que la herramienta expone ese canal; la variable efecto, la observabilidad y contrastabilidad del procedimiento intermedio que el software profesional encapsula. El objeto de estudio es técnico: el análisis de medios continuos en elasticidad lineal plana por el método, del mapeo isoparamétrico a la recuperación de tensiones, con elementos Q4 y Q9. El campo de acción es su enseñanza: el software y la memoria de cálculo que lo documenta. El trabajo se delimita a la Carrera de Ingeniería Civil de la Universidad Autónoma Tomás Frías, al aula y al equipo personal del estudiante, sin licencias, y a la gestión dos mil veintiséis.

## 5. Objetivos  ·  02:22

El objetivo general es desarrollar EduFEM: un software educativo de escritorio para el análisis por elementos finitos de problemas bidimensionales de elasticidad lineal, en tensión plana y deformación plana, con elementos isoparamétricos Q4 y Q9, que integre la formulación matemática, la construcción y visualización interactiva del modelo y la verificación numérica. Se concreta en seis objetivos específicos: fundamentar teóricamente el método; implementar un motor de cálculo verificado numéricamente; diseñar una interfaz en pre-proceso, proceso y post-proceso sobre un único lienzo; desarrollar módulos educativos que expongan cada etapa sobre el modelo real; verificar y validar el software con soluciones manufacturadas, casos de referencia clásicos y un programa comercial; y generar una memoria de cálculo automática con interoperabilidad de datos. Al final volveré a esta tabla con la columna de cumplimiento.

## 6. Hipótesis y preguntas  ·  03:11

Por tratarse de un desarrollo tecnológico no planteo una hipótesis estadística sino una hipótesis de diseño, cuyo criterio de veracidad es la efectividad en la práctica. Sostiene que es factible construir un software que exponga el canal de cálculo completo del método en elasticidad plana de forma transparente, con cada matriz y cada paso observables; interactiva, sobre el modelo del alumno; numéricamente verificable frente a referencias de exactitud conocida; y coherente con el flujo de trabajo profesional. Se verifica por diseño, comprobando que la herramienta reúne esos atributos. De ella se desprenden tres preguntas: si es posible un motor de precisión verificable frente a soluciones analíticas y software comercial; qué organización de la interfaz y de los módulos expone la cadena de cálculo; y de qué modo la herramienta evidencia el bloqueo por cortante del Q4 frente a la convergencia del Q9. La investigación es propositiva, aplicada de tipo tecnológico, cuantitativa, y descriptiva y comparativa.

## 7. Base teórica  ·  04:06

Paso a la base teórica, en el mismo orden que sigue el canal de cálculo del programa: el estado del arte y después la cadena que va del equilibrio a la recuperación de tensiones.

## 8. Estado del arte  ·  04:16

Los antecedentes se agrupan en tres familias: las herramientas de análisis matricial de barras, como el analizador de reticulados de Bishay; los simuladores de un eslabón aislado del método, como los de Lee, embebidos en el programa comercial VisualFEA; y las herramientas de propósito general, tanto las bibliotecas de programación, donde el cálculo se inspecciona en el código y no en una representación gráfica, como los paquetes comerciales, que entregan resultados sin exponer las matrices intermedias. El antecedente más directo es ED-Elas2D, de la Universitat Politècnica de Catalunya: comparte con EduFEM el dominio, el idioma y hasta los elementos Q4 y Q9, pero es un software académico cerrado y ligado a la tecnología de los años noventa. El contraste evidencia un vacío: ninguno reúne a la vez español, licencia libre, el continuo elástico plano, el cálculo paso a paso sobre el modelo del usuario, el canal completo y una memoria de cálculo automática. EduFEM se diseñó para cubrir ese vacío.

## 9. De la forma fuerte a K u = F  ·  05:13

El punto de partida es el equilibrio en su forma fuerte: la divergencia del tensor de tensiones más la fuerza de volumen es igual a cero en todo el dominio, lo que exige continuidad de segundo orden. El método parte de la forma débil: multiplicando por un desplazamiento virtual e integrando por partes se llega al principio de los trabajos virtuales, que rebaja el requisito a primer orden y habilita polinomios a trozos. Al discretizar con funciones de forma, la deformación se obtiene con la matriz B, la tensión con la matriz constitutiva D, y el problema se reduce al sistema K por u igual a F. La matriz constitutiva distingue tensión plana, con tensión normal al plano nula, de deformación plana, con deformación normal nula; en esta última aparece el factor uno menos dos nu, que tiende a cero cuando el coeficiente de Poisson se acerca a cero coma cinco: el origen del bloqueo volumétrico.

## 10. El canal isoparamétrico  ·  06:00

El elemento isoparamétrico interpola geometría y desplazamientos con la misma familia de funciones de forma, definidas sobre el cuadrado natural de coordenadas xi y eta. El Q4 usa cuatro nodos y una interpolación bilineal, con ocho grados de libertad; el Q9, nueve nodos y una bicuadrática completa, con dieciocho. La matriz Jacobiana conecta el cuadrado natural con el elemento real: su determinante debe ser positivo y su inversa construye la matriz B, de tres por dos ene. La rigidez elemental es la integral de B transpuesta, D, B por el espesor; como el integrando no es polinómico, se integra por cuadratura de Gauss: dos por dos puntos en el Q4 y tres por tres en el Q9. Las matrices elementales se ensamblan en una matriz global dispersa, el sistema se resuelve con una factorización LU dispersa, y las tensiones se evalúan en los puntos de Gauss, se extrapolan a los nodos y se promedian. Este es el canal que los módulos exponen sobre el elemento que el alumno selecciona.

## 11. Dos patologías  ·  06:55

Hay dos fenómenos numéricos que un alumno solo comprende cuando los ve. El bloqueo por cortante: en flexión, el campo bilineal del Q4 no reproduce la curvatura sin generar un corte espurio, así que el elemento resulta artificialmente rígido. En la membrana de Cook con ocho por ocho elementos, el Q4 da veintidós coma cero setenta y nueve frente a la referencia de veintitrés coma noventa y seis, un siete coma ochenta y cinco por ciento por debajo; el Q9 está prácticamente libre del bloqueo. Y los modos espurios, u hourglass: aparecen al subintegrar, por ejemplo con un solo punto de Gauss en el Q4, porque la matriz de rigidez pierde rango y admite modos de energía nula. EduFEM los evita con integración completa. Decidí no implementar la integración reducida selectiva ni la formulación B-barra: ofrezco el Q9 y aprovecho el Q4 como recurso didáctico. La regla es que m puntos de Gauss integran exactamente grado dos m menos uno: subintegrar produce modos espurios y sobreintegrar solo encarece.

## 12. Recuperación de tensiones y verificación  ·  07:53

Las tensiones se evalúan en los puntos de Gauss, que en el Q4 coinciden con los puntos de Barlow, donde la precisión es superconvergente; se extrapolan a los nodos con la inversa de la matriz de funciones de forma evaluada en esos puntos, que en el Q4 tiene forma cerrada con los coeficientes que ven en pantalla, y se promedian entre los elementos que comparten cada nodo. En cuanto a la verificación, el método de soluciones manufacturadas elige la solución de antemano, deduce la fuerza de volumen que la produce y mide el error con las normas L dos y H uno, que deben decrecer con las tasas teóricas: orden p más uno y orden p. Conviene ser preciso: verificar es comprobar que las ecuaciones se resuelven bien; validar, que representan la realidad. Este trabajo hace verificación de código, verificación de solución y comparación código a código; la validación frente a mediciones físicas queda fuera de su alcance, y lo declaro desde ahora.

## 13. Diseño y desarrollo del modelo  ·  08:43

El tercer bloque tiene dos partes: cómo diseñé la investigación, con sus variables, la matriz de consistencia y los criterios de aceptación; y cómo construí el software. Cierra con la demostración.

## 14. Variables  ·  08:55

El modelo de investigación es un modelo de simulación numérica: no hay unidades experimentales ni aleatorización; la confiabilidad descansa en el determinismo del motor, en la reproducibilidad de cada caso y en la convergencia bajo refinamiento. La variable independiente tiene dos componentes: la definición del modelo, con geometría, material, acciones y apoyos, y las decisiones de discretización, tipo de elemento y densidad de malla. La variable dependiente es la respuesta estructural y su exactitud frente a las referencias, medida con el orden de convergencia observado, las normas L dos y H uno y el error relativo. Las controladas son el tipo de análisis y el orden de cuadratura, fijo en dos por dos para el Q4 y tres por tres para el Q9. Dentro de cada caso solo se manipulan el tipo de elemento y la densidad de malla.

## 15. Matriz de consistencia  ·  09:40

La matriz de consistencia traza cada objetivo con su pregunta de investigación, su indicador, su instrumento y la evidencia en el documento. El primer objetivo es transversal, porque la fundamentación sostiene a las tres preguntas; el segundo y el quinto responden a la precisión verificable; el tercero y el cuarto, a la organización de la interfaz y de los módulos; y el quinto también al bloqueo por cortante. El sexto es instrumental: la memoria y la interoperabilidad apoyan la transparencia, pero no derivan de una pregunta propia.

## 16. Procedimiento de verificación y validación  ·  10:10

Cada caso sigue el mismo procedimiento. Un guion construye la malla y define material, cargas y apoyos. Un validador de salud, una función pura sin dependencias de la interfaz, comprueba la consistencia de los datos antes de resolver: que existan elementos, que las restricciones supriman los movimientos de cuerpo rígido y que el Jacobiano sea positivo. El sistema se ensambla y resuelve con las mismas funciones del motor que consumen los módulos educativos y la memoria. Las normas de error se integran con un punto de Gauss más por dirección que la rigidez, para no subestimar el error, y los criterios se evalúan en el propio guion. Los casos son una selección intencional por valor probatorio: el método de soluciones manufacturadas aporta una solución exacta arbitraria; la viga de Timoshenko, una solución analítica y un modelo en SAP2000; y la membrana de Cook, una referencia histórica sensible al bloqueo. Cada uno se corre con Q4 y con Q9.

## 17. Criterios de aceptación  ·  11:03

Los criterios de aceptación quedaron fijados a priori en los propios guiones, que terminan con error si alguno falla. Las tasas de convergencia observadas deben quedar dentro de más menos cero coma cinco de las teóricas en las cuatro configuraciones del método de soluciones manufacturadas; la flecha central de la viga de Timoshenko, dentro del tres por ciento de la solución analítica con corrección de cortante; en la membrana de Cook, el desplazamiento del Q9 con ocho elementos por lado, dentro del uno coma cinco por ciento de la referencia; y la flecha del Q4 debe ser inferior a la del Q9 con la misma malla, que es la firma del bloqueo por cortante. Así la hipótesis se contrasta por diseño, y la verificación no se ajusta a posteriori.

## 18. Arquitectura  ·  11:42

Cuatro requisitos gobernaron el diseño: orientación educativa, con cada operación inspeccionable; español con terminología canónica; primacía de lo visual; e independencia tecnológica, con Python y bibliotecas libres. La arquitectura es un modelo-vista-controlador en seis capas alrededor de un único modelo de proyecto, el estado que todas comparten por referencia. El motor numérico, con NumPy y SciPy, es puro: no importa la interfaz, corre sin pantalla, y por eso es a la vez el motor de la aplicación y el oráculo de las pruebas. Una decisión crítica separa la identidad pública de cada nodo, que puede tener huecos tras borrar, del índice ordinal que fija sus grados de libertad, de modo que la matriz global se dimensiona por el número de nodos. El programa se distribuye con un instalador único para Windows que incorpora Python, las bibliotecas y una distribución reducida de TeX Live: la memoria de cálculo compila sin instalar nada más.

## 19. Pre-proceso  ·  12:35

El modelo se construye en cinco tablas o dibujando sobre el lienzo, que es el mismo en las tres fases. El modo de dibujo funciona como en un programa de CAD: el usuario marca cuatro vértices, el lienzo ajusta a los nodos existentes y la orientación se fuerza a sentido antihorario para garantizar un Jacobiano positivo. Cada acción captura una instantánea del modelo, lo que hace todo reversible, y la selección se sincroniza entre tablas y lienzo. Antes de resolver, el validador de salud aplica dieciocho chequeos: nueve errores críticos que bloquean el cálculo, ocho advertencias y uno de información, con explicación pedagógica y autocorrección cuando es posible. El módulo cero evalúa la calidad de la malla con dos métricas de la biblioteca Verdict; para el Jacobiano escalado, EduFEM eleva el corte de cero coma treinta a cero coma cincuenta por prudencia pedagógica.

## 20. Ocho módulos  ·  13:22

El componente pedagógico central son ocho módulos, del cero al siete, que recorren el canal en su orden canónico: calidad de malla, mapeo isoparamétrico, Jacobiano, matriz B, matriz constitutiva, rigidez elemental con Gauss, fuerzas nodales equivalentes y ensamblaje. Cada módulo es una capa superpuesta al lienzo: un panel flotante más una iluminación dibujada sobre la malla real del proyecto, no sobre un ejemplo prefabricado, y el elemento se selecciona con un clic. El módulo cero colorea cada elemento por su calidad y deja distorsionar un vértice en vivo; el cinco contrapone la integral, irresoluble a mano, con su aproximación por cuadratura; el siete resalta las filas y columnas de la matriz global que recibe cada elemento. Solo una capa está activa a la vez, y un conmutador alterna entre la fórmula simbólica y su evaluación numérica.

## 21. M5  ·  14:09

Tomo el módulo cinco como ejemplo. A la izquierda, el elemento real con sus puntos de Gauss iluminados y los ejes naturales dibujados sobre él. A la derecha, el salto de la integral a la suma de cuadratura y la matriz de rigidez elemental, que crece al sumar la contribución de cada punto. El alumno cambia entre uno por uno, dos por dos y tres por tres puntos y observa cómo cambia la matriz; con un solo punto ve nacer los modos espurios.

## 22. Post-proceso  ·  14:35

Resuelto el sistema, los resultados se presentan sobre el mismo lienzo: el campo se dibuja como un contorno continuo con interpolación de Gouraud y puede superponerse la malla deformada con un factor de escala. Una sonda puntual localiza cualquier punto dentro de su elemento por mapeo inverso y abre un panel con las componentes cartesianas, las tensiones principales y la de von Mises, junto con un círculo de Mohr. Una vista tridimensional muestra el campo como superficie, cruda o suavizada. La paleta es la jet, el arcoíris de los programas comerciales: la elegí a sabiendas de sus limitaciones perceptuales porque es la que el alumno encontrará en la práctica profesional.

## 23. Memoria de cálculo  ·  15:11

El sexto objetivo se cumple con la memoria de cálculo automática: el programa compone un documento LaTeX y lo compila a PDF con el TeX Live embebido, en un estilo educativo, con explicaciones, y en uno directo, con el desarrollo matricial escueto. El anexo G de la tesis la reproduce sobre el ejemplo canónico: nueve nodos, cuatro elementos Q4, módulo de elasticidad de doscientos veinticinco mil, Poisson cero coma dos, espesor cero coma ocho y una carga de mil en el nodo siete. El flujo es el de la memoria: la matriz constitutiva con su factor de doscientos treinta y cuatro mil trescientos setenta y cinco; la rigidez del elemento tres, con un determinante del Jacobiano de cuatro coma siete seis cero cuatro en el primer punto de Gauss; la matriz global de dieciocho por dieciocho; la partición en seis grados de libertad restringidos y doce libres; las reacciones, que suman exactamente cero en horizontal y mil en vertical; y una von Mises máxima de ochocientos sesenta y cuatro coma setenta en el nodo siete. Todas las cifras son salida bit-exacta del motor. Completan el objetivo el formato nativo, los CSV comprimidos y la importación DXF.

## 24. Demostración  ·  16:15

En la defensa presencial este es el momento de la demostración en vivo, en tres pasos: cargo el ejemplo canónico con control E; abro el módulo cinco con control cinco sobre un elemento y muestro cómo cambia la rigidez al agregar o quitar puntos de Gauss; y resuelvo con F5, recorro el contorno de von Mises, sondeo un punto con el círculo de Mohr y exporto la memoria de cálculo en PDF. Todo sobre el mismo lienzo, sin cambiar de contexto.

## 25. Presentación de resultados  ·  16:40

Presento ahora los resultados de la batería de verificación y validación, reproducibles con los tres guiones del repositorio.

## 26. MMS  ·  16:47

En el método de soluciones manufacturadas impuse una solución conocida como restricciones de Dirichlet y su término fuente como fuerza de volumen, y resolví mallas de dos por dos hasta treinta y dos por treinta y dos elementos en cuatro configuraciones: cuadrado unitario y cuadrilátero distorsionado, en tensión plana y en deformación plana. En escala doble logarítmica la pendiente de cada recta es el orden de convergencia. El Q4 alcanza orden dos en norma L dos y uno en seminorma H uno; el Q9, tres y dos: exactamente lo que predice la teoría. El campo de tensiones recuperado converge con orden uno coma cincuenta y cuatro en el Q4 y dos en el Q9. Las otras configuraciones dan las mismas tasas con diferencias inferiores a cero coma cero uno, lo que descarta errores de orden en el ensamblaje, la cuadratura, el mapeo distorsionado y la matriz constitutiva de ambos estados planos. Un detalle de honestidad metodológica: la matriz de extrapolación del Q4 tuvo un defecto de numeración de puntos de Gauss invisible para estas normas; lo detecté al inspeccionar la memoria de cálculo, y desde entonces una prueba de regresión exige reproducir exactamente campos polinómicos.

## 27. El modelo no deriva  ·  17:51

Además de exacto, el modelo de datos no deriva. Convertir la malla de Q4 a Q9 y volver deja los desplazamientos con diferencias menores que diez a la menos nueve. Resolver con identificadores de nodo con huecos, como uno, cinco, cincuenta y noventa y nueve, da lo mismo que con identificadores contiguos, lo que valida la indexación de grados de libertad. El ejemplo exportado a CSV y reimportado reproduce los desplazamientos con diferencia menor que diez a la menos doce. Y el DXF de ejemplo entra como seis elementos y doce nodos compartidos; al reimportarlo no crea nada nuevo: la importación es idempotente.

## 28. Viga de Timoshenko  ·  18:27

La validación externa usa una viga de hormigón simplemente apoyada, de catorce metros de luz y uno coma veinte de peralte, con una carga uniforme de cinco mil kilogramos fuerza por metro, modelada con una malla Q9 de cincuenta y seis por ocho elementos y tres mil ochocientos cuarenta y dos grados de libertad. La contrasté con la solución elástica de Timoshenko y Goodier y con un modelo de cáscara en SAP2000. La tensión normal difiere de la analítica en cero coma cero cuatrocientos catorce por ciento como máximo, y de SAP2000 en cero coma dos mil sesenta y seis por ciento. La flecha central es de dos coma cero tres cuatro seis centímetros frente a dos coma cero dos nueve dos seis de la referencia con corrección de cortante: cero coma veintiséis por ciento de error. Con la fórmula de Euler-Bernoulli, que desprecia el cortante, el error aparente habría sido del uno coma ochenta y cinco por ciento: el modelo plano captura el cortante en una viga de relación luz-peralte cercana a once coma siete. En la tensión cortante el error llega al dos coma nueve por ciento, y frente a SAP2000 los desplazamientos difieren hasta cero coma cincuenta y seis por ciento.

## 29. Membrana de Cook  ·  19:28

La membrana de Cook es un trapecio empotrado con un corte unitario en el extremo libre, con material adimensional en tensión plana. No tiene solución cerrada: la referencia de veintitrés coma noventa y seis es un límite de convergencia con una incertidumbre del orden del cero coma cero cinco por ciento, y la extrapolación de Richardson de mi secuencia Q9 apunta a veintitrés coma noventa y siete. En la malla más gruesa el Q4 subestima la respuesta en más de un cincuenta por ciento, y con dos mil ciento setenta y ocho grados de libertad todavía conserva un error de menos cero coma quinientos noventa y cuatro por ciento. El Q9 con ocho elementos por lado ya cumple el criterio del uno coma cinco por ciento, y con dos mil ciento setenta y ocho grados de libertad queda dentro de la incertidumbre de la propia referencia.

## 30. Análisis de resultados  ·  20:10

Interpreto ahora qué significan estas cifras para las preguntas de investigación y hasta dónde llega la evidencia.

## 31. Mismos GDL  ·  20:17

La comparación justa es a igualdad de grados de libertad. Con los mismos dos mil ciento setenta y ocho, el Q4 conserva un error de menos cero coma quinientos noventa y cuatro por ciento y el Q9 de menos cero coma cero cuarenta y cuatro: trece veces menos, un orden de magnitud a favor del elemento de mayor orden, y esa diferencia no depende de la incertidumbre de la referencia. La curva del Q4 sube lenta y monótona por debajo de la referencia: es la firma del bloqueo por cortante. La del Q9 se pega a la referencia casi de inmediato. Esto responde la tercera pregunta de investigación, y el estudiante puede reproducirlo cargando el ejemplo de Cook en Q4 y en Q9.

## 32. Escalabilidad y alcance  ·  20:54

La transparencia no se pagó con lentitud. En un equipo con un procesador de dos mil doce, con el motor vectorizado por lotes en NumPy puro, la malla más exigente de las validaciones, de ocho mil cuatrocientos cincuenta grados de libertad, se ensambla y resuelve en menos de dos décimas de segundo, y un problema de treinta y tres mil grados de libertad en menos de un segundo. A ese tamaño la matriz densa ocuparía cerca de ocho coma nueve gigabytes; la dispersa, menos de trece megabytes. El ordenamiento de mínimo grado reduce el tiempo de factorización entre uno coma siete y dos coma nueve veces frente al ordenamiento genérico. Sobre el alcance: las magnitudes primarias quedan por debajo del cero coma tres por ciento frente a la solución analítica y del cero coma seis por ciento frente a SAP2000, aunque en la componente cortante el modelo de cáscara queda más cerca del analítico que EduFEM. Frente al software comercial, EduFEM no compite en cobertura: su valor es la transparencia del canal. El bloqueo por cortante se muestra, no se mitiga, y no hay validación frente a mediciones físicas.

## 33. Conclusiones y recomendaciones  ·  21:55

Cierro con el cumplimiento de los objetivos, la hipótesis, las limitaciones que asumo y las líneas de continuación.

## 34. Seis objetivos, seis conclusiones  ·  22:02

Vuelvo a la tabla de objetivos, ahora con su cumplimiento. El primero, la fundamentación teórica, está cumplido: el marco teórico es la misma formulación que implementa el motor, exhiben los módulos y sustituye numéricamente la memoria. El segundo, el motor, está cumplido y verificado: las tasas de convergencia coinciden con las teóricas en ambos elementos y en los dos estados planos. El tercero, la interfaz en tres fases sobre un lienzo único, con deshacer y rehacer y validación de salud, está cumplido. El cuarto, los módulos que operan sobre el elemento seleccionado del modelo real, está cumplido. El quinto, la verificación y validación, está cumplido con las cifras que presenté: cero coma cero cuatro por ciento en tensión normal, cero coma veintiséis en flecha y el contraste de Cook entre el Q4 y el Q9. Y el sexto, la memoria de cálculo en dos estilos y la interoperabilidad con ida y vuelta e idempotencia, está cumplido. Seis objetivos específicos cumplidos y, con ello, el objetivo general.

## 35. Hipótesis confirmada  ·  23:02

La hipótesis de diseño se confirma atributo por atributo: transparente, porque cada matriz es visible en los módulos y en la memoria; interactiva, porque opera sobre el elemento que el alumno selecciona; verificable, con soluciones manufacturadas, Timoshenko, Cook y SAP2000; y coherente con el flujo profesional. Las tres preguntas se responden afirmativamente: la primera con las cifras de verificación; la segunda por diseño, con el lienzo único y los ocho módulos; la tercera con la membrana de Cook. Con ello queda respondido el problema científico: el canal de cálculo es observable, mediante los módulos y la memoria, y contrastable, mediante una batería de verificación con criterios fijados a priori. Ese es exactamente el efecto que el problema pedía.

## 36. Limitaciones  ·  23:44

Asumo cinco limitaciones. El alcance se restringe a la elasticidad lineal estática en dos dimensiones: sin no linealidad, dinámica, tres dimensiones, placas ni cáscaras. La biblioteca de elementos se limita a los cuadriláteros Q4 y Q9, sin triángulos ni mallado automático. El solucionador directo es eficiente hasta decenas de miles de grados de libertad, pero su coste crece desfavorablemente en mallas masivas. El bloqueo por cortante del Q4 se ilustra, pero no se mitiga. Y no hubo validación empírica del impacto educativo con estudiantes: la utilidad didáctica se sostiene por diseño y en la literatura. Las validaciones numéricas son analíticas y código a código, no frente a mediciones físicas.

## 37. Líneas de continuación  ·  24:26

De esas limitaciones derivan cinco líneas de continuación. En el solucionador, una factorización de Cholesky sobre la matriz reducida, simétrica y definida positiva, con la mitad del trabajo de una LU, y un solucionador iterativo precondicionado para problemas masivos. En la formulación, la integración reducida selectiva o la formulación B-barra, con un módulo que contraste el comportamiento bloqueado y el corregido. En la biblioteca de elementos, triángulos, cuadriláteros de transición y la extensión a tres dimensiones. En la evidencia, casos civiles en deformación plana con solución publicada: una presa de gravedad, un muro de contención o un túnel somero. Y la más importante: un estudio con estudiantes, con comparación antes y después e instrumentos de percepción, que dé sustento cuantitativo a la utilidad didáctica que hoy justifico por diseño.

## 38. Cierre  ·  25:14

La caja negra se puede abrir, y abierta calcula igual de bien. EduFEM es software libre, en español, y está disponible en el repositorio público para cualquier estudiante, sin licencias. Muchas gracias por su atención. Quedo a disposición del tribunal para sus preguntas.
