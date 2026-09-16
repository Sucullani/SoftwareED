# Guion del video de defensa — EduFEM

Voz: es-BO-MarceloNeural (Microsoft Edge TTS, rate +11%) · duración 30:54 · 39 láminas.

| Lámina | Inicio | Duración | Título |
|---:|---:|---:|---|
| 1 | 00:00 | 37 s | Carátula |
| 2 | 00:37 | 7 s | Introducción |
| 3 | 00:43 | 46 s | La brecha |
| 4 | 01:29 | 61 s | Del problema al objetivo |
| 5 | 02:30 | 67 s | Objetivos |
| 6 | 03:36 | 69 s | Hipótesis y preguntas |
| 7 | 04:45 | 10 s | Base teórica |
| 8 | 04:55 | 75 s | Estado del arte |
| 9 | 06:10 | 47 s | De la forma fuerte a K u = F |
| 10 | 06:57 | 55 s | El canal isoparamétrico |
| 11 | 07:52 | 57 s | Dos patologías |
| 12 | 08:49 | 74 s | Recuperación de tensiones y verificación |
| 13 | 10:04 | 12 s | Diseño y desarrollo del modelo |
| 14 | 10:16 | 68 s | Variables |
| 15 | 11:24 | 39 s | Matriz de consistencia |
| 16 | 12:04 | 77 s | Procedimiento de verificación y validación |
| 17 | 13:20 | 70 s | Criterios de aceptación |
| 18 | 14:31 | 53 s | Arquitectura |
| 19 | 15:24 | 47 s | Pre-proceso |
| 20 | 16:11 | 47 s | Ocho módulos |
| 21 | 16:58 | 26 s | M5 |
| 22 | 17:24 | 36 s | Post-proceso |
| 23 | 18:00 | 64 s | Memoria de cálculo |
| 24 | 19:04 | 24 s | Demostración |
| 25 | 19:29 | 7 s | Presentación de resultados |
| 26 | 19:36 | 64 s | MMS |
| 27 | 20:40 | 36 s | El modelo no deriva |
| 28 | 21:16 | 85 s | Viga de Timoshenko |
| 29 | 22:41 | 47 s | Membrana de Cook |
| 30 | 23:28 | 59 s | El canal expuesto |
| 31 | 24:27 | 7 s | Análisis de resultados |
| 32 | 24:34 | 37 s | Mismos GDL |
| 33 | 25:12 | 61 s | Escalabilidad y alcance |
| 34 | 26:12 | 7 s | Conclusiones y recomendaciones |
| 35 | 26:20 | 63 s | Seis objetivos, seis conclusiones |
| 36 | 27:23 | 62 s | Hipótesis confirmada |
| 37 | 28:25 | 67 s | Limitaciones |
| 38 | 29:32 | 64 s | Líneas de continuación |
| 39 | 30:36 | 17 s | Cierre |

## 1. Carátula  ·  00:00

Buenos días, señores miembros del tribunal. Mi nombre es Hedy Yhassmany Oyola Sucullani y presento la tesis «Desarrollo de software educativo de elementos finitos para el análisis estructural empleando el lenguaje de programación Python», para optar al título de Licenciatura en Ingeniería Civil. Su producto es EduFEM: un programa de escritorio, libre y en español, que expone el método de los elementos finitos paso a paso sobre el modelo del propio estudiante. La exposición sigue el orden reglamentario: introducción, base teórica, diseño y desarrollo del modelo, presentación y análisis de resultados, y conclusiones y recomendaciones.

## 2. Introducción  ·  00:37

Comienzo por la fundamentación: de dónde nace el problema, qué se estudia, qué me propuse y cómo lo contrasto.

## 3. La brecha  ·  00:43

La enseñanza del método enfrenta una brecha doble. Los textos clásicos presentan la formulación matricial con rigor, pero de manera abstracta: funciones de forma, Jacobiano, matriz B y cuadratura de Gauss aparecen como una cadena algebraica sin una geometría concreta a la vista, y el desarrollo a mano no escala más allá de uno o dos elementos. El software profesional hace lo contrario: recibe geometría, material y cargas, devuelve tensiones, y oculta todo el procesamiento intermedio; además es costoso, no tiene propósito didáctico y su localización al español es limitada. La consecuencia es concreta: el estudiante aprende a operar sin comprender, y no puede diagnosticar un resultado anómalo ni reconocer el bloqueo por cortante o los modos espurios. Esa es la situación problemática de la que parte esta tesis.

## 4. Del problema al objetivo  ·  01:29

De esa situación deriva el problema científico, que formulo como una única interrogante: ¿cómo debe construirse un software educativo para que exponga, de forma transparente, interactiva y numéricamente verificable, el canal de cálculo completo del método en elasticidad plana, de modo que cada etapa resulte observable y contrastable por el estudiante, como apoyo a la comprensión de sus fundamentos? El objeto de estudio es técnico: el análisis de medios continuos en elasticidad lineal plana por el método, del mapeo isoparamétrico a la recuperación de tensiones, con elementos Q4 y Q9. El campo de acción es su enseñanza: el software y la memoria de cálculo que lo documenta. En la nomenclatura de tres variables del diseño clásico de investigación, el aporte es EduFEM; el atributo manipulado, la forma en que se expone el canal de cálculo; y el efecto esperado, la observabilidad y contrastabilidad del procedimiento. El trabajo se delimita a la Carrera de Ingeniería Civil de la Universidad Autónoma Tomás Frías, al aula y al equipo personal del estudiante, sin licencias, y a la gestión dos mil veintiséis.

## 5. Objetivos  ·  02:30

El objetivo general es desarrollar, en el lenguaje de programación Python y sobre bibliotecas numéricas de código abierto, EduFEM: un software educativo de escritorio para el análisis por elementos finitos de problemas bidimensionales de elasticidad lineal, en tensión plana y deformación plana, con elementos isoparamétricos Q4 y Q9, que integre la formulación matemática, la construcción y visualización interactiva del modelo y la verificación numérica. Se concreta en seis objetivos específicos: fundamentar teóricamente el método; implementar el motor de cálculo con todas las etapas, de las funciones de forma a la recuperación de tensiones; diseñar una interfaz en pre-proceso, proceso y post-proceso sobre un único lienzo; desarrollar módulos educativos que expongan, paso a paso y sobre el modelo real, las etapas desde el mapeo isoparamétrico hasta el ensamblaje, completadas por el post-proceso y la memoria para la solución y las tensiones; verificar y validar el software con soluciones manufacturadas, casos de referencia clásicos y un programa comercial; y generar la memoria de cálculo automática en PDF, con la interoperabilidad de datos como complemento instrumental. Al final volveré a esta tabla con la columna de cumplimiento.

## 6. Hipótesis y preguntas  ·  03:36

No planteo una hipótesis estadística, sino una hipótesis de diseño: en la investigación tecnológica la hipótesis es la solución tentativa a un problema concreto, y su criterio de veracidad es la efectividad en la práctica. La enuncio en forma condicional y comprobable: si se construye un software que exponga el canal completo de forma transparente, interactiva y coherente con el flujo de trabajo profesional, entonces, primero, su motor reproducirá las tasas teóricas de convergencia y acotará el error por debajo del tres por ciento en la flecha y del uno por ciento en la tensión normal frente a la viga de Timoshenko y frente a SAP2000; segundo, evidenciará sobre la membrana de Cook el bloqueo por cortante del Q4 frente a la convergencia del Q9; y tercero, cada etapa del canal resultará observable en un módulo educativo o en la memoria de cálculo. Cada cláusula puede resultar falsa: un motor con un error de orden, un Q4 que no bloqueara o una etapa sin exposición la refutarían. Que esa transparencia además apoye el aprendizaje es un supuesto fundamentado en la literatura, que este trabajo no contrasta empíricamente y deja planteado como recomendación. De la hipótesis se desprenden las tres preguntas de investigación que responderé en el análisis y en las conclusiones.

## 7. Base teórica  ·  04:45

Paso a la base teórica, en el mismo orden que sigue el canal de cálculo del programa: el estado del arte y después la cadena que va del equilibrio a la recuperación de tensiones.

## 8. Estado del arte  ·  04:55

Los antecedentes se agrupan en tres familias: las herramientas de análisis matricial de barras, como el analizador de reticulados de Bishay; los simuladores de un eslabón aislado del método, como los de Lee, embebidos en el programa comercial VisualFEA; y las herramientas de propósito general, tanto las bibliotecas de programación, donde el cálculo se inspecciona en el código y no en una representación gráfica, como los paquetes comerciales, que entregan resultados sin exponer las matrices intermedias. El antecedente más directo es ED-Elas2D, de la Universitat Politècnica de Catalunya: comparte con EduFEM el dominio, el idioma y hasta los elementos Q4 y Q9, pero es un software académico ligado a la tecnología de los años noventa, cuya licencia y disponibilidad la publicación no documenta. La tabla está organizada por atributos, y donde la fuente consultada no documenta uno, la celda dice «no consta»: registra un límite de mi revisión, no una carencia del recurso. El contraste evidencia un vacío: ninguno reúne a la vez español, licencia libre, el continuo elástico plano, el cálculo paso a paso sobre el modelo del usuario, el canal completo, una memoria de cálculo automática, los fenómenos numéricos observables y una verificación y validación publicadas junto con la herramienta. EduFEM se diseñó para cubrir ese vacío.

## 9. De la forma fuerte a K u = F  ·  06:10

El punto de partida es el equilibrio en su forma fuerte: la divergencia del tensor de tensiones más la fuerza de volumen es igual a cero en todo el dominio, lo que exige continuidad de segundo orden. El método parte de la forma débil: multiplicando por un desplazamiento virtual e integrando por partes se llega al principio de los trabajos virtuales, que rebaja el requisito a primer orden y habilita polinomios a trozos. Al discretizar con funciones de forma, la deformación se obtiene con la matriz B, la tensión con la matriz constitutiva D, y el problema se reduce al sistema K por u igual a F. La matriz constitutiva distingue tensión plana, con tensión normal al plano nula, de deformación plana, con deformación normal nula; en esta última aparece el factor uno menos dos nu, que tiende a cero cuando el coeficiente de Poisson se acerca a cero coma cinco: el origen del bloqueo volumétrico.

## 10. El canal isoparamétrico  ·  06:57

El elemento isoparamétrico interpola geometría y desplazamientos con la misma familia de funciones de forma, definidas sobre el cuadrado natural de coordenadas xi y eta. El Q4 usa cuatro nodos y una interpolación bilineal, con ocho grados de libertad; el Q9, nueve nodos y una bicuadrática completa, con dieciocho. La matriz Jacobiana conecta el cuadrado natural con el elemento real: su determinante debe ser positivo y su inversa construye la matriz B, de tres por dos ene. La rigidez elemental es la integral de B transpuesta, D, B por el espesor; como el integrando no es polinómico, se integra por cuadratura de Gauss: dos por dos puntos en el Q4 y tres por tres en el Q9. Las matrices elementales se ensamblan en una matriz global dispersa, el sistema se resuelve con una factorización LU dispersa, y las tensiones se evalúan en los puntos de Gauss, se extrapolan a los nodos y se promedian. Este es el canal que los módulos exponen sobre el elemento que el alumno selecciona.

## 11. Dos patologías  ·  07:52

Hay dos fenómenos numéricos que un alumno solo comprende cuando los ve. El bloqueo por cortante: en flexión, el campo bilineal del Q4 no reproduce la curvatura sin generar un corte espurio, así que el elemento resulta artificialmente rígido. En la membrana de Cook con ocho por ocho elementos, el Q4 da veintidós coma cero setenta y nueve frente a la referencia de veintitrés coma noventa y seis, un siete coma ochenta y cinco por ciento por debajo; el Q9 está prácticamente libre del bloqueo. Y los modos espurios, u hourglass: aparecen al subintegrar, por ejemplo con un solo punto de Gauss en el Q4, porque la matriz de rigidez pierde rango y admite modos de energía nula. EduFEM los evita con integración completa. Decidí no implementar la integración reducida selectiva ni la formulación B-barra: ofrezco el Q9 y aprovecho el Q4 como recurso didáctico. La regla es que m puntos de Gauss integran exactamente grado dos m menos uno: subintegrar produce modos espurios y sobreintegrar solo encarece.

## 12. Recuperación de tensiones y verificación  ·  08:49

Las tensiones se evalúan en los puntos de la cuadratura con que se integra la rigidez, donde el campo es más preciso; se llevan a los nodos con la inversa de la matriz de funciones de forma evaluada en esos mismos puntos, que en el Q4 tiene forma cerrada con los coeficientes que ven en pantalla; y se promedian entre los elementos que comparten cada nodo. La numeración de los puntos de Gauss no es un detalle: permutarla permuta las columnas de la matriz de extrapolación y corrompe las tensiones nodales sin alterar los desplazamientos, de modo que una verificación basada solo en desplazamientos no lo detectaría; por eso el motor construye esa matriz invirtiendo numéricamente con sus propios puntos, y una prueba comprueba que reproduce exactamente los campos polinómicos. El orden de convergencia de esta secuencia no lo tomo de la literatura: lo mido. En cuanto a la verificación, el método de soluciones manufacturadas elige la solución de antemano, deduce la fuerza de volumen que la produce y mide el error con las normas L dos y H uno, que deben decrecer con las tasas teóricas: orden p más uno y orden p. Conviene ser preciso: verificar es comprobar que las ecuaciones se resuelven bien; validar, que representan la realidad. Este trabajo hace verificación de código, verificación de solución y comparación código a código; la validación frente a mediciones físicas queda fuera de su alcance, y lo declaro desde ahora.

## 13. Diseño y desarrollo del modelo  ·  10:04

El tercer bloque tiene dos partes: cómo diseñé la investigación, con sus variables, la matriz de consistencia y los criterios de aceptación; y cómo construí el software. Cierra con la demostración.

## 14. Variables  ·  10:16

El modelo de investigación es un modelo de simulación numérica: no hay unidades experimentales ni aleatorización; la confiabilidad descansa en el determinismo del motor, en la reproducibilidad de cada caso y en la convergencia bajo refinamiento. La primera fila operacionaliza las variables del propio problema científico como atributos del artefacto, con indicadores que se cuentan: etapas del canal con módulo interactivo y con desarrollo numérico en la memoria, fases que comparten el lienzo y formatos con prueba de ida y vuelta. Las demás son las variables del experimento numérico con que establezco la corrección del motor. La variable independiente tiene dos componentes: la definición del modelo, con geometría, material, acciones y apoyos, y las decisiones de discretización, tipo de elemento y densidad de malla. La dependiente es la respuesta estructural y su exactitud frente a las referencias, medida con el orden de convergencia observado, las normas L dos y H uno, la norma del campo de tensiones recuperado, el error relativo y el residuo de equilibrio de las reacciones. Las controladas son el tipo de análisis y el orden de cuadratura, fijo en dos por dos para el Q4 y tres por tres para el Q9; y el desempeño del solucionador se registra sin criterio de aceptación.

## 15. Matriz de consistencia  ·  11:24

La matriz de consistencia traza cada objetivo con su pregunta de investigación, su indicador, su instrumento y la evidencia en el documento. El primer objetivo es transversal, porque la fundamentación sostiene a las tres preguntas; el segundo y el quinto responden a la precisión verificable; el tercero y el cuarto, a la organización de la interfaz y de los módulos; y el quinto también al bloqueo por cortante. El sexto responde a la segunda pregunta en su parte principal: la memoria de cálculo es la forma escrita en que el canal se expone de manera transparente y contrastable, y su cobertura se cuenta con el mismo indicador que la de los módulos; la interoperabilidad de datos es su complemento instrumental, y se verifica por ida y vuelta e idempotencia.

## 16. Procedimiento de verificación y validación  ·  12:04

Cada caso sigue el mismo procedimiento. Un guion construye la malla y define material, cargas y apoyos. Un validador de salud, una función pura sin dependencias de la interfaz, comprueba la consistencia de los datos antes de resolver: que existan elementos, que las restricciones supriman los movimientos de cuerpo rígido y que el Jacobiano sea positivo. El sistema se ensambla y resuelve con las mismas funciones del motor que consumen los módulos educativos y la memoria. Las normas de error se integran con un punto de Gauss más por dirección que la rigidez, para no subestimar el error, y los criterios se evalúan en el propio guion. Los casos son una selección intencional por valor probatorio: el método de soluciones manufacturadas aporta una solución exacta arbitraria y ejercita la fuerza de volumen, las restricciones no homogéneas y las dos matrices constitutivas; la viga de Timoshenko aporta una solución analítica y un modelo en SAP2000; y la membrana de Cook, una referencia histórica sensible al bloqueo. El refinamiento y la comparación entre el Q4 y el Q9 se hacen en los dos casos con secuencia de mallas, el de soluciones manufacturadas y el de Cook; la viga de Timoshenko se resuelve con una única malla fina de elementos Q9 y constituye un contraste puntual de exactitud. Declaro una excepción: la carga superficial linealmente variable no interviene en ningún caso de referencia y no tiene contraste externo.

## 17. Criterios de aceptación  ·  13:20

Los criterios de aceptación quedaron fijados a priori en los propios guiones, que terminan con error si alguno falla. Para el motor: las tasas de convergencia observadas deben quedar dentro de más menos cero coma cinco de las teóricas en las cuatro configuraciones del método de soluciones manufacturadas; la tensión normal de la viga de Timoshenko, dentro del uno por ciento tanto de la solución analítica como de SAP2000, en los tres puntos de control; la flecha central, dentro del tres por ciento de la analítica con corrección de cortante; el equilibrio global, con un residuo relativo menor que diez a la menos ocho; y para el campo de tensiones recuperado, cuya tasa teórica no está establecida para esta secuencia, una cota empírica declarada como tal. En la membrana de Cook, el desplazamiento del Q9 con ocho elementos por lado dentro del uno coma cinco por ciento de la referencia, y la flecha del Q4 inferior a la del Q9 con la misma malla, que es la firma del bloqueo. Y para los atributos del artefacto: módulo interactivo en cada una de las siete etapas elementales y de ensamblaje, desarrollo numérico de las nueve etapas en la memoria, las tres fases sobre un mismo lienzo y los formatos con ida y vuelta sin pérdida. Así la hipótesis se contrasta cláusula por cláusula, y la verificación no se ajusta a posteriori.

## 18. Arquitectura  ·  14:31

Cuatro requisitos gobernaron el diseño: orientación educativa, con cada operación inspeccionable; español con terminología canónica; primacía de lo visual; e independencia tecnológica, con Python y bibliotecas libres. La arquitectura es un modelo-vista-controlador en seis capas alrededor de un único modelo de proyecto, el estado que todas comparten por referencia. El motor numérico, con NumPy y SciPy, es puro: no importa la interfaz, corre sin pantalla, y por eso es a la vez el motor de la aplicación y el oráculo de las pruebas. Una decisión crítica separa la identidad pública de cada nodo, que puede tener huecos tras borrar, del índice ordinal que fija sus grados de libertad, de modo que la matriz global se dimensiona por el número de nodos. El programa se distribuye con un instalador único para Windows que incorpora Python, las bibliotecas y una distribución reducida de TeX Live: la memoria de cálculo compila sin instalar nada más.

## 19. Pre-proceso  ·  15:24

El modelo se construye en cinco tablas o dibujando sobre el lienzo, que es el mismo en las tres fases. El modo de dibujo funciona como en un programa de CAD: el usuario marca cuatro vértices, el lienzo ajusta a los nodos existentes y la orientación se fuerza a sentido antihorario para garantizar un Jacobiano positivo. Cada acción captura una instantánea del modelo, lo que hace todo reversible, y la selección se sincroniza entre tablas y lienzo. Antes de resolver, el validador de salud aplica veintidós chequeos: trece errores críticos que bloquean el cálculo, ocho advertencias y uno de información, con explicación pedagógica y autocorrección cuando es posible. El módulo cero evalúa la calidad de la malla con dos métricas de la biblioteca Verdict; para el Jacobiano escalado, EduFEM eleva el corte de cero coma treinta a cero coma cincuenta por prudencia pedagógica.

## 20. Ocho módulos  ·  16:11

El componente pedagógico central son ocho módulos, del cero al siete, que recorren el canal en su orden canónico: calidad de malla, mapeo isoparamétrico, Jacobiano, matriz B, matriz constitutiva, rigidez elemental con Gauss, fuerzas nodales equivalentes y ensamblaje. Cada módulo es una capa superpuesta al lienzo: un panel flotante más una iluminación dibujada sobre la malla real del proyecto, no sobre un ejemplo prefabricado, y el elemento se selecciona con un clic. El módulo cero colorea cada elemento por su calidad y deja distorsionar un vértice en vivo; el cinco contrapone la integral, irresoluble a mano, con su aproximación por cuadratura; el siete resalta las filas y columnas de la matriz global que recibe cada elemento. Solo una capa está activa a la vez, y un conmutador alterna entre la fórmula simbólica y su evaluación numérica.

## 21. M5  ·  16:58

Tomo el módulo cinco como ejemplo. A la izquierda, el elemento real con sus puntos de Gauss iluminados y los ejes naturales dibujados sobre él. A la derecha, el salto de la integral a la suma de cuadratura y la matriz de rigidez elemental, que crece al sumar la contribución de cada punto. El alumno cambia entre uno por uno, dos por dos y tres por tres puntos y observa cómo cambia la matriz; con un solo punto ve nacer los modos espurios.

## 22. Post-proceso  ·  17:24

Resuelto el sistema, los resultados se presentan sobre el mismo lienzo: el campo se dibuja como un contorno continuo con interpolación de Gouraud y puede superponerse la malla deformada con un factor de escala. Una sonda puntual localiza cualquier punto dentro de su elemento por mapeo inverso y abre un panel con las componentes cartesianas, las tensiones principales y la de von Mises, junto con un círculo de Mohr. Una vista tridimensional muestra el campo como superficie, cruda o suavizada. La paleta es la jet, el arcoíris de los programas comerciales: la elegí a sabiendas de sus limitaciones perceptuales porque es la que el alumno encontrará en la práctica profesional.

## 23. Memoria de cálculo  ·  18:00

El sexto objetivo se cumple con la memoria de cálculo automática: el programa compone un documento LaTeX y lo compila a PDF con el TeX Live embebido, en un estilo educativo, con explicaciones, y en uno directo, con el desarrollo matricial escueto. El anexo G de la tesis la reproduce sobre el ejemplo canónico: nueve nodos, cuatro elementos Q4, módulo de elasticidad de doscientos veinticinco mil, Poisson cero coma dos, espesor cero coma ocho y una carga de mil en el nodo siete. El flujo es el de la memoria: la matriz constitutiva con su factor de doscientos treinta y cuatro mil trescientos setenta y cinco; la rigidez del elemento tres, con un determinante del Jacobiano de cuatro coma siete seis cero cuatro en el primer punto de Gauss; la matriz global de dieciocho por dieciocho; la partición en seis grados de libertad restringidos y doce libres; las reacciones, que suman exactamente cero en horizontal y mil en vertical; y una von Mises máxima de ochocientos sesenta y cuatro coma setenta en el nodo siete. Todas las cifras son salida bit-exacta del motor. Completan el objetivo el formato nativo, los CSV comprimidos y la importación DXF.

## 24. Demostración  ·  19:04

En la defensa presencial este es el momento de la demostración en vivo, en tres pasos: cargo el ejemplo canónico con control E; abro el módulo cinco con control cinco sobre un elemento y muestro cómo cambia la rigidez al agregar o quitar puntos de Gauss; y resuelvo con F5, recorro el contorno de von Mises, sondeo un punto con el círculo de Mohr y exporto la memoria de cálculo en PDF. Todo sobre el mismo lienzo, sin cambiar de contexto.

## 25. Presentación de resultados  ·  19:29

Presento ahora los resultados de la batería de verificación y validación, reproducibles con los tres guiones del repositorio.

## 26. MMS  ·  19:36

En el método de soluciones manufacturadas impuse una solución conocida como restricciones de Dirichlet y su término fuente como fuerza de volumen, y resolví mallas de dos por dos hasta treinta y dos por treinta y dos elementos en cuatro configuraciones: cuadrado unitario y cuadrilátero distorsionado, en tensión plana y en deformación plana. En escala doble logarítmica la pendiente de cada recta es el orden de convergencia. El Q4 alcanza orden dos en norma L dos y uno en seminorma H uno; el Q9, tres y dos: exactamente lo que predice la teoría. El campo de tensiones recuperado converge con orden uno coma cincuenta y cuatro en el Q4 y dos en el Q9. Las otras configuraciones dan las mismas tasas con diferencias inferiores a cero coma cero uno, lo que descarta errores de orden en el ensamblaje, la cuadratura, el mapeo distorsionado y la matriz constitutiva de ambos estados planos. Un detalle de honestidad metodológica: la matriz de extrapolación del Q4 tuvo un defecto de numeración de puntos de Gauss invisible para estas normas; lo detecté al inspeccionar la memoria de cálculo, y desde entonces una prueba de regresión exige reproducir exactamente campos polinómicos.

## 27. El modelo no deriva  ·  20:40

Además de exacto, el modelo de datos no deriva. Convertir la malla de Q4 a Q9 y volver deja los desplazamientos con diferencias menores que diez a la menos nueve. Resolver con identificadores de nodo con huecos, como uno, cinco, cincuenta y noventa y nueve, da lo mismo que con identificadores contiguos, lo que valida la indexación de grados de libertad. El ejemplo exportado a CSV y reimportado reproduce los desplazamientos con diferencia menor que diez a la menos doce. Y el DXF de ejemplo entra como seis elementos y doce nodos compartidos; al reimportarlo no crea nada nuevo: la importación es idempotente.

## 28. Viga de Timoshenko  ·  21:16

La validación externa usa una viga de hormigón simplemente apoyada, de catorce metros de luz y uno coma veinte de peralte, con una carga uniforme de cinco mil kilogramos fuerza por metro, modelada con una malla Q9 de cincuenta y seis por ocho elementos y tres mil ochocientos cuarenta y dos grados de libertad. El valor concreto del módulo de elasticidad no condiciona la validación: en elasticidad lineal, escalarlo deja las tensiones inalteradas y divide los desplazamientos, de modo que los errores relativos son invariantes. La contrasté con la solución elástica de Timoshenko y Goodier y con un modelo de cáscara en SAP2000. La tensión normal difiere de la analítica en cero coma cero cuatrocientos catorce por ciento como máximo, y de SAP2000 en cero coma dos mil sesenta y seis por ciento. La flecha central es de dos coma cero tres cuatro seis centímetros frente a dos coma cero dos nueve dos seis de la referencia con corrección de cortante: cero coma veintiséis por ciento de error. Con la fórmula de Euler-Bernoulli, que desprecia el cortante, el error aparente habría sido del uno coma ochenta y cinco por ciento: el modelo plano captura el cortante en una viga de relación luz-peralte cercana a once coma siete. En las componentes secundarias, cuya magnitud es entre seis y treinta y cinco veces menor, los errores relativos crecen: cero coma noventa y cuatro por ciento en la tensión transversal y dos coma ochenta y nueve por ciento en la cortante frente a la analítica. Y la suma de las reacciones verticales iguala la carga total, setenta mil kilogramos fuerza, con un residuo relativo del orden de diez a la menos trece.

## 29. Membrana de Cook  ·  22:41

La membrana de Cook es un trapecio empotrado con un corte unitario en el extremo libre, con material adimensional en tensión plana. No tiene solución cerrada: la referencia de veintitrés coma noventa y seis es un límite de convergencia, con una incertidumbre del mismo orden que la diferencia entre mis dos mallas más finas, y la extrapolación de Richardson de mi secuencia Q9 apunta a veintitrés coma noventa y siete. En la malla más gruesa el Q4 subestima la respuesta en más de un cincuenta por ciento, y con dos mil ciento setenta y ocho grados de libertad todavía conserva un error de menos cero coma quinientos noventa y cuatro por ciento. El Q9 con ocho elementos por lado ya cumple el criterio del uno coma cinco por ciento, y con dos mil ciento setenta y ocho grados de libertad queda por debajo del cero coma uno por ciento, donde las diferencias ya no son significativas frente a la propia referencia.

## 30. El canal expuesto  ·  23:28

Los atributos del artefacto también son resultados, y los reporto con los mismos indicadores de la tabla de variables. De las nueve etapas del canal de cálculo, las siete primeras —del mapeo isoparamétrico al ensamblaje— tienen módulo interactivo propio, del M1 al M7, y las nueve tienen desarrollo con sustitución numérica en la memoria de cálculo. La solución del sistema y la recuperación de tensiones, que no tienen módulo propio, se exponen además en el post-proceso: la sonda puntual en sus modos crudo y suavizado, la vista tridimensional y la tabla de resultados. La lámina muestra las tres fases trabajando sobre el mismo lienzo y el mismo modelo: a la izquierda el pre-proceso, agregando un elemento con el modo de dibujo; en el centro el proceso, con el módulo de la matriz B desplegado sobre el elemento seleccionado; y a la derecha el post-proceso, con el contorno de von Mises sobre la deformada, las reacciones en los apoyos y el círculo de Mohr del nodo siete. Con esto queda cumplido el criterio de cobertura que fijé de antemano: siete de siete etapas con módulo y nueve de nueve en la memoria.

## 31. Análisis de resultados  ·  24:27

Interpreto ahora qué significan estas cifras para las preguntas de investigación y hasta dónde llega la evidencia.

## 32. Mismos GDL  ·  24:34

La comparación justa es a igualdad de grados de libertad. Con los mismos dos mil ciento setenta y ocho, el Q4 conserva un error de menos cero coma quinientos noventa y cuatro por ciento y el Q9 de menos cero coma cero cuarenta y cuatro: trece veces menos, un orden de magnitud a favor del elemento de mayor orden, y esa diferencia no depende de la incertidumbre de la referencia. La curva del Q4 sube lenta y monótona por debajo de la referencia: es la firma del bloqueo por cortante. La del Q9 se pega a la referencia casi de inmediato. Esto responde la tercera pregunta de investigación, y el estudiante puede reproducirlo cargando el ejemplo de Cook en Q4 y en Q9.

## 33. Escalabilidad y alcance  ·  25:12

La transparencia no se pagó con lentitud. En un equipo con un procesador de dos mil doce, con el motor vectorizado por lotes en NumPy puro, la malla más exigente de las validaciones, de ocho mil cuatrocientos cincuenta grados de libertad, se ensambla y resuelve en menos de dos décimas de segundo, y un problema de treinta y tres mil grados de libertad en menos de un segundo. A ese tamaño la matriz densa ocuparía cerca de ocho coma nueve gigabytes; la dispersa, menos de trece megabytes. El ordenamiento de mínimo grado reduce el tiempo de factorización entre uno coma siete y dos coma nueve veces frente al ordenamiento genérico. Sobre el alcance: las magnitudes primarias quedan por debajo del cero coma tres por ciento frente a la solución analítica y del cero coma seis por ciento frente a SAP2000, aunque en la componente cortante el modelo de cáscara queda más cerca del analítico que EduFEM. Frente al software comercial, EduFEM no compite en cobertura: su valor es la transparencia del canal. El bloqueo por cortante se muestra, no se mitiga, y no hay validación frente a mediciones físicas.

## 34. Conclusiones y recomendaciones  ·  26:12

Cierro con el cumplimiento de los objetivos, la hipótesis, las limitaciones que asumo y las líneas de continuación.

## 35. Seis objetivos, seis conclusiones  ·  26:20

Vuelvo a la tabla de objetivos, ahora con su cumplimiento. El primero, la fundamentación teórica, está cumplido, pero conviene decir en qué sentido: es el fundamento del trabajo y no un resultado medido; lo que los resultados comprueban es que el motor construido sobre esa base se comporta como la teoría predice. El segundo, el motor, está cumplido y verificado: las tasas de convergencia coinciden con las teóricas en ambos elementos y en los dos estados planos. El tercero, la interfaz en tres fases sobre un lienzo único, con deshacer y rehacer y validación de salud, está cumplido. El cuarto, los módulos que operan sobre el elemento seleccionado del modelo real, está cumplido con el alcance que declaré: llegan hasta el ensamblaje, y la solución del sistema y la recuperación de tensiones se exponen en el post-proceso y en la memoria. El quinto, la verificación y validación, está cumplido con las cifras que presenté. Y el sexto, la memoria de cálculo con las nueve etapas y la interoperabilidad con ida y vuelta e idempotencia, está cumplido. Seis objetivos específicos cumplidos y, con ello, el objetivo general.

## 36. Hipótesis confirmada  ·  27:23

La hipótesis de diseño se confirma cláusula por cláusula. La primera: el motor reprodujo las tasas teóricas de convergencia en las cuatro configuraciones, y los errores quedaron en cero coma cero cuatro por ciento en tensión normal y cero coma veintiséis en flecha frente a la solución analítica, y en cero coma veintiuno y cero coma cincuenta y seis frente a SAP2000, dentro de los umbrales que fijé de antemano. La segunda: la membrana de Cook reprodujo el bloqueo por cortante del Q4 frente a la convergencia del Q9, cuantificado a igualdad de grados de libertad. La tercera: siete de las siete etapas elementales y de ensamblaje tienen módulo interactivo, las nueve tienen desarrollo numérico en la memoria, las tres fases operan sobre un mismo lienzo y los formatos superan la ida y vuelta. Con ello las tres preguntas se responden afirmativamente y queda respondido el problema científico: el canal de cálculo es observable, mediante los módulos y la memoria, y contrastable, mediante una batería de verificación con criterios fijados a priori. El supuesto de que esa observabilidad apoya el aprendizaje no lo contrasté: medirlo excede este trabajo y queda como recomendación.

## 37. Limitaciones  ·  28:25

Asumo las limitaciones que fijé de antemano y las que el desarrollo puso de manifiesto. El alcance se restringe a la elasticidad lineal estática en dos dimensiones: sin no linealidad, dinámica, tres dimensiones, placas ni cáscaras. La biblioteca de elementos se limita a los cuadriláteros Q4 y Q9, sin triángulos ni mallado automático. La cobertura por módulos interactivos llega hasta el ensamblaje: la solución del sistema y la recuperación de tensiones se exponen en el post-proceso y en la memoria, y no en un módulo propio. El bloqueo por cortante del Q4 se ilustra, pero no se mitiga, y en deformación plana la matriz constitutiva degenera cuando el coeficiente de Poisson se acerca a un medio: el módulo cuatro lo señala, pero el software no lo resuelve. El solucionador directo es eficiente hasta decenas de miles de grados de libertad, pero su coste crece desfavorablemente en mallas masivas. La validación descansa en tres casos de referencia y en un único caso con material de ingeniería civil, y la carga superficial linealmente variable no tiene contraste externo. Y no hubo validación empírica del impacto educativo con estudiantes: la utilidad didáctica se sostiene por diseño y en la literatura.

## 38. Líneas de continuación  ·  29:32

De esas limitaciones derivan tres líneas de continuación, una por capítulo. Sobre la formulación: incorporar técnicas de tratamiento del bloqueo, como la integración reducida selectiva o la formulación B-barra, que además habilitarían un módulo educativo que contraste, sobre un mismo modelo, el comportamiento bloqueado y el corregido; y ampliar la biblioteca con triángulos y cuadriláteros de transición. Sobre el software: una factorización de Cholesky, aplicable porque la matriz reducida es simétrica y definida positiva; un solucionador iterativo precondicionado para problemas masivos; la extensión a tres dimensiones con hexaedros y tetraedros; y un generador de mallas sobre el contorno dibujado, con las métricas del módulo cero como control. Y sobre la evidencia: un caso con carga superficial linealmente variable, que ningún caso de referencia ejercita; al menos un caso civil en deformación plana con solución publicada, como una presa de gravedad, un muro de contención o un túnel somero; y la más importante, un estudio con estudiantes, con comparación entre cohortes o antes y después e instrumentos de percepción, que dé sustento cuantitativo a la utilidad didáctica que hoy justifico por diseño.

## 39. Cierre  ·  30:36

La caja negra se puede abrir, y abierta calcula igual de bien. EduFEM es software libre, en español, y está disponible en el repositorio público para cualquier estudiante, sin licencias. Muchas gracias por su atención. Quedo a disposición del tribunal para sus preguntas.
