# Auditoría crítica para la defensa de la tesis EduFEM

**Autor de la tesis:** Hedy Yhassmany Oyola Sucullani  
**Documento auditado:** `main_final.pdf`, versión de septiembre de 2026, 189 páginas físicas.  
**Fecha de auditoría:** 21 de septiembre de 2026.  
**Finalidad:** identificar objeciones razonables del tribunal y preparar correcciones y respuestas sustentadas.

## 1. Dictamen ejecutivo

La tesis tiene una base defendible como investigación tecnológica: construye un artefacto concreto, fundamenta su formulación y reporta pruebas numéricas con referencias identificables. Su vulnerabilidad principal está en la distancia entre algunas afirmaciones generales y la evidencia que efectivamente presenta. No recomendaría convertirla, por esa sola razón, en una investigación experimental con estudiantes. Recomendaría ajustar las afirmaciones y completar comprobaciones documentales y computacionales específicas.

**Antes de defender, atendería cinco puntos:**

1. La hipótesis y las conclusiones afirman una mejora causal, pero la evaluación demuestra principalmente cumplimiento de requisitos y exactitud en casos seleccionados.
2. El resultado de cobertura **18/18** incluye correspondencias discutibles, especialmente FEA18: refinamiento local en zonas de concentración de tensiones.
3. La memoria se presenta como comprobada manualmente, aunque el Anexo G reproduce salidas del mismo motor y condensa pasos importantes.
4. El intercambio CSV se describe como sin pérdida, pero el esquema del Anexo F omite información que sí existe en el modelo nativo.
5. Hay afirmaciones técnicas que deben corregirse: garantía geométrica por muestreo del Jacobiano, explicación del efecto de omitir σz en von Mises y caracterización del Q4 como base incompleta.

**Una fortaleza comprobada en esta auditoría:** reconstruí independientemente el problema Q4 del Anexo G, a partir de sus coordenadas, conectividades, material, cargas y restricciones. Los desplazamientos nodales, la primera fila de la rigidez E3 y sus tensiones en los cuatro puntos de Gauss concuerdan con las cifras publicadas al redondeo mostrado. Esto apoya ese ejemplo; no certifica todo el programa.

## 2. Alcance y lectura de los hallazgos

La revisión se apoya en el PDF suministrado: planteamiento, teoría, metodología, resultados, conclusiones y anexos pertinentes. Se hicieron comprobaciones algebraicas y numéricas puntuales e inspección visual de páginas seleccionadas. Se consultaron fuentes primarias externas para puntos concretos de formulación, bibliografía y licencia.

No se ejecutó la versión distribuida de EduFEM ni su instalador; no se auditó el repositorio completo ni se reprodujeron las baterías MMS, Cook y SAP2000. El intento de abrir el repositorio desde la consulta web no permitió inspeccionarlo: esto **no demuestra** que sea privado o inexistente. Tampoco se revisó un reglamento institucional de modalidades de graduación. No corresponde emitir un dictamen normativo sobre si la UATF debe clasificar el trabajo como tesis o proyecto de grado.

Las referencias de página son los **folios impresos de la tesis**. Desde la Introducción, para ubicar el número físico del visor PDF, sumar 19: folio 90 = página física 109.

- **Crítica:** puede comprometer una conclusión central si se mantiene sin ajustar.
- **Alta:** objeción técnica o metodológica importante que conviene resolver antes de la defensa.
- **Media:** limita alcance, reproducibilidad o claridad; normalmente admite corrección acotada.
- **Confirmado:** la discrepancia se comprueba en el documento o por un cálculo explícito.
- **Riesgo de inferencia:** la conclusión excede lo demostrado; no implica que los resultados sean falsos.
- **Pendiente de código:** el PDF permite identificar el riesgo, pero no concluir cómo se comporta la implementación.

## 3. Mapa de prioridades

| ID | Prioridad | Punto vulnerable | Localización principal |
|---|---|---|---|
| H01 | Crítica | Mejora causal e incidencia local sin comparación equivalente | pp. 2–8, 43–46, 99–104 |
| H02 | Alta | Indicadores solapados y definición de verificabilidad | pp. 3, 44–45, 73–74 |
| H03 | Crítica | Cobertura 18/18 no suficientemente acreditada | pp. 48–51, 90–92, 98 |
| H04 | Crítica | Reproducción manual confundida con salida documentada | pp. 52, 89, 163–169 |
| H05 | Alta | CSV sin pérdida contradicho por su esquema | pp. 71, 79–80, 157–161 |
| H06 | Alta | Uso ambiguo de validación y V&V | pp. 36, 73, 101–104 |
| H07 | Alta | Referencia de Cook y su incertidumbre poco independientes | pp. 84–86 |
| H08 | Alta | Garantía excesiva sobre Jacobiano y geometría | pp. 25, 62, 65–67 |
| H09 | Alta | Explicación incorrecta de von Mises en deformación plana | p. 31 |
| H10 | Alta | Q4 incompleto y continuo exclusivamente bidimensional | pp. 9, 23–24 |
| H11 | Media | Afirmaciones universales sobre cuadratura | pp. 27, 37–38 |
| H12 | Alta | Comparación SAP2000 y condiciones de referencia | pp. 80–83, 93, Anexo E |
| H13 | Media | Error pequeño de σx no representa todo el campo | pp. 81–83, 93–94, 140–142 |
| H14 | Alta | Convergencia MMS presentada como descarte demasiado amplio | pp. 38, 52, 76, 93–95 |
| H15 | Media | Cobertura de pruebas limitada para algunas funciones | pp. 48, 106, 108 |
| H16 | Alta | Campo verificado y representación gráfica no equivalentes | pp. 69–70, 75 |
| H17 | Media | Promediado nodal en interfaces y discontinuidades | pp. 33–34, 57–62 |
| H18 | Alta | Trazabilidad de versión, criterios y corridas | pp. 43, 51–53, 114, 136–138 |
| H19 | Alta | Brecha y aporte frente al estado del arte | pp. 13–18, 101, 104–105 |
| H20 | Media | Todas las licencias descritas como permisivas | p. 57 |
| H21 | Media | Benchmark del motor confundible con desempeño integral | pp. 96–97 |
| H22 | Media | Errores y formulaciones residuales en anexos y teoría | pp. 21, 30, 144–156, 167 |

## 4. Hallazgos y preparación de respuestas

### H01. La evidencia no aísla la mejora causal que enuncia la hipótesis

**Estado:** riesgo de inferencia. **Prioridad:** crítica.

**Evidencia.** El problema pregunta cómo el uso como caja negra incide en la baja trazabilidad y verificabilidad en la Carrera durante 2026 (p. 2). La variable independiente tiene dos niveles (p. 43), pero el nivel de referencia se documenta con una comparación bibliográfica heterogénea; no se aplica a dos condiciones equivalentes una misma evaluación sobre el mismo problema. Las conclusiones responden que la caja negra “incide de raíz” (p. 101) y que la hipótesis queda comprobada (p. 104).

**Pregunta probable:** «¿Dónde midió esa incidencia en la Carrera? ¿Qué comparación demuestra que la exposición del procedimiento causó la mejora?»

**Vulnerabilidad.** Mostrar que EduFEM cumple requisitos no estima por sí solo el efecto de cambiar una variable. Además, la Carrera es destinataria declarada, no un contexto donde se hayan tomado observaciones de uso. La distinción aparece en el método, pero pierde precisión en el problema y las conclusiones.

**Corrección propuesta.** Formular el problema como diseño y evaluación de una solución técnica. Sustituir la confirmación causal general por apoyo a una proposición tecnológica bajo criterios y casos definidos. Si se conserva “mejora”, definir qué atributo cambia y compararlo con una referencia explícita, mediante el mismo protocolo. Puede hacerse sin estudiantes: por ejemplo, resolver un modelo y comprobar qué valores intermedios permiten reconstruir ambas condiciones de exposición. Esa comparación demostraría disponibilidad de información, no aprendizaje ni necesariamente mayor exactitud.

**Respuesta defendible hoy:** «La Carrera es el contexto destinatario. La evidencia evalúa propiedades del artefacto en escenarios controlados; no mide un efecto causal sobre los estudiantes ni sobre el uso institucional. La conclusión debe leerse y redactarse con ese alcance».

### H02. Trazabilidad, verificabilidad y exactitud se mezclan

**Estado:** confirmado en la operacionalización. **Prioridad:** alta.

**Evidencia.** Los indicadores de la independiente y de la trazabilidad comparten exposición de etapas, memoria y organización de la interfaz (Tabla 2.2). La verificabilidad se define incluyendo que la comprobación “da conforme” (p. 3).

**Pregunta probable:** «¿No está midiendo lo mismo con dos nombres? ¿Un cálculo erróneo deja de ser verificable si precisamente pude verificar que está mal?»

**Vulnerabilidad.** La capacidad de comprobar un resultado y la corrección del resultado son propiedades relacionadas, pero distintas. Un mismo lienzo tampoco es condición necesaria de trazabilidad: es una decisión de interfaz. El episodio del error de extrapolación muestra que un procedimiento puede ser trazable y verificable mientras contiene un error.

**Corrección propuesta.** Separar: a) disponibilidad y correspondencia de datos intermedios; b) posibilidad de reproducción independiente; c) exactitud frente a referencias. Tratar el lienzo compartido como requisito de diseño, sin usarlo como equivalente de trazabilidad. Denominar EduFEM “artefacto o solución propuesta”; si se conserva “variable interviniente”, explicar que pertenece al esquema metodológico adoptado y no a un modelo estadístico de mediación.

**Respuesta defendible:** «La exposición es una característica de diseño; la trazabilidad se evalúa siguiendo vínculos concretos desde una salida hasta sus entradas. La exactitud se comprueba aparte. Corregiré la definición para que verificar no signifique necesariamente aprobar».

### H03. El 18/18 debe revisarse; FEA18 es el caso más débil

**Estado:** insuficiencia documental confirmada. **Prioridad:** crítica.

**Evidencia.** La Tabla 3.7 vincula “Refinar en zonas de concentración de tensiones” con Cook y remite a §3.5 (p. 90). Esa sección presenta mallas N × N refinadas globalmente. Identificar vértices singulares o refinar toda la malla no demuestra un procedimiento de refinamiento localizado. FEA30 se vincula a secuencias y Richardson, sin presentar allí una regla operativa de parada por una diferencia prefijada. FEM3 se excluye expresamente porque no lo expone el software (p. 91).

**Pregunta probable:** «Muéstreme dónde refina localmente. ¿Seleccionó los 18 ítems antes de evaluar o quitó los que no cumplía?»

**Vulnerabilidad.** El criterio exige 18/18 y falla si falta uno. Las exclusiones por alcance disciplinar son defendibles; excluir un ítem por no estar implementado exige mayor justificación. Además, un consenso externo de 49 ítems no convierte la selección de 18 hecha por el autor en un universo completamente externo.

**Corrección propuesta.** Reauditar las filas con cuatro estados: implementado y demostrado; ejercitable mediante una práctica documentada; parcial; no demostrado. Añadir para cada fila una tarea concreta, archivo de entrada, pasos y evidencia de salida. Para FEA18, aportar una malla conformante con concentración local y su comparación, si el software efectivamente lo permite, o declarar cobertura parcial. No basta agregar una etiqueta “refinamiento”. Revisar también FEA15, FEA30 y FEM9 contra la redacción original del artículo.

Si cambia la regla de marcado, declarar que es una revisión metodológica; no presentarla como criterio original fijado antes de las corridas. Actualizar Resumen, Tablas 2.4 y 3.10 y conclusiones de manera conjunta.

**Respuesta defendible:** «El consenso orienta el contenido, pero no constituye una evaluación de EduFEM. El cotejo es mío. La evidencia de refinamiento global no basta para acreditar refinamiento local; esa fila necesita una demostración o una calificación parcial».

### H04. Memoria reproducible no equivale a reproducción independiente realizada

**Estado:** confirmado documentalmente; comprobación parcial favorable en esta auditoría. **Prioridad:** crítica.

**Evidencia.** El Anexo G declara que sus valores provienen del mismo motor (p. 163). Desarrolla un elemento y remite los restantes al mismo procedimiento (p. 165); para K muestra el patrón de no nulos, no la matriz numérica; la solución se resume en que la factorización entrega los desplazamientos (p. 167). El ejemplo tiene únicamente carga nodal: no demuestra con sustitución no trivial la conversión de cargas distribuidas a fuerzas equivalentes, una de las nueve etapas.

**Pregunta probable:** «¿Quién rehízo el cálculo por una vía independiente? ¿Dónde están los valores que necesito para comprobar el ensamblaje y la solución?»

**Vulnerabilidad.** Compartir funciones evita divergencia entre salidas, pero también comparte errores. Compilar un PDF sin errores no comprueba su contenido. El anexo condensado puede ser adecuado como ilustración, pero no basta para sostener por sí solo una reproducción completa de las nueve etapas.

**Corrección propuesta.** Incorporar un cotejo independiente con etapas, valor del motor, valor del cálculo de referencia, discrepancia y tolerancia. Publicar la memoria completa y un modelo pequeño con carga de borde. Para el ejemplo Q4, proporcionar K y el sistema reducido en un anexo digital, conservando suficiente precisión.

**Comprobación propia de esta auditoría:** usando integración 2 × 2, ensamblaje y solución densa independientes, se obtuvo para el nodo 7 ux ≈ −0,00689361 y uy ≈ −0,01307629. Para E3, en el primer punto de Gauss, σx ≈ −41,04336346; σy ≈ −421,74760404; τxy ≈ −63,97938925. Coinciden con las cifras del anexo al redondeo mostrado. No se comprobó aquí la totalidad de la memoria automática, su variante Q9 ni todas las tensiones nodales promediadas.

**Respuesta defendible:** «La memoria expone el cálculo y permite reproducirlo. Compartir el motor garantiza consistencia interna, pero la comprobación independiente necesita otra ruta. El ejemplo Q4 tiene concordancia numérica puntual; debo documentar el cotejo y completar las etapas no ejercitadas».

### H05. El alcance “sin pérdida” del CSV es excesivo

**Estado:** contradicción documental confirmada; comportamiento concreto pendiente de código. **Prioridad:** alta.

**Evidencia.** El formato nativo incluye ux_value/uy_value, configuración, gravedad y conectividad completa (pp. 158–159). En CSV, las restricciones solo contienen indicadores booleanos; los elementos solo contienen N1–N4; los nodos adicionales Q9 se regeneran; ciertas cargas y restricciones se descartan silenciosamente si no se encuentra su nodo (pp. 159–161). La prueba publicada usa el ejemplo canónico Q4 (pp. 79–80).

**Pregunta probable:** «¿Qué sucede con un asentamiento impuesto, un nodo intermedio Q9 desplazado o una carga aplicada en él después de exportar e importar?»

**Vulnerabilidad.** La prueba acredita una ida y vuelta para ese caso, no conservación general del estado del modelo. El esquema descrito no muestra cómo transportar algunos datos que el programa admite.

**Corrección propuesta.** Reservar “sin pérdida” para las entidades y configuraciones efectivamente preservadas y probadas. Declarar el formato nativo como vía de conservación completa si se ha verificado. Ampliar CSV o explicitar sus restricciones. Probar una ida y vuelta con desplazamiento prescrito no nulo, Q9 con geometría intermedia modificada, carga sobre nodo intermedio y cambio de unidades. Informar descartes al usuario.

**Respuesta defendible:** «El resultado sin pérdida publicado corresponde al ejemplo Q4 ensayado. El formato editable tiene límites que deben quedar explícitos; no lo presentaré como equivalente completo al formato nativo».

### H06. “Validación” cambia de significado dentro del discurso

**Estado:** riesgo terminológico reconocido por la propia tesis. **Prioridad:** alta.

**Evidencia.** §1.13 distingue correctamente verificación de validación física, pero después conserva “validación” para soluciones analíticas y comparación entre códigos (p. 36). En §2.1.1 también aparece validación del artefacto en ciencia del diseño.

**Pregunta probable:** «Si no comparó con mediciones físicas, ¿qué validó exactamente?»

**Vulnerabilidad.** Declarar una acepción particular reduce la ambigüedad, pero no hace equivalentes los conceptos. SAP2000 tampoco es una referencia de exactitud conocida por el solo hecho de ser comercial.

**Corrección propuesta.** Emplear “verificación numérica y contraste con referencias” para MMS, Timoshenko, Cook y SAP2000. Reservar “evaluación de la propuesta tecnológica” para requisitos; especificar “validación física” y “evaluación educativa” como fuera de alcance. La propia p. 36 ofrece fundamento suficiente para esta corrección.

**Respuesta defendible:** «Verifiqué la resolución numérica y contrasté soluciones. Evalué el cumplimiento de requisitos del artefacto. No realicé validación física experimental ni evaluación de aprendizaje».

### H07. Cook necesita una referencia externa trazable y una incertidumbre mejor acotada

**Estado:** insuficiencia documental y riesgo de inferencia. **Prioridad:** alta.

**Evidencia.** Se adopta uy = 23,96 en (48;52) como valor de uso extendido, sin una fuente concreta junto al dato; se corrobora con la secuencia del propio Q9. El 0,05 % se estima con la diferencia entre mallas y Richardson (p. 84).

**Pregunta probable:** «¿Quién publicó ese valor para ese punto y esas condiciones? ¿Cómo puede su programa ser a la vez el programa evaluado y quien establece la referencia?»

**Vulnerabilidad.** La convergencia interna es útil, pero no sustituye una referencia independiente. El punto de lectura, estado plano, carga total, distribución de tracción y parámetros deben coincidir. Una diferencia entre dos mallas es un indicador de sensibilidad; no constituye por sí sola una cota rigurosa de incertidumbre.

**Corrección propuesta.** Citar una fuente primaria con configuración idéntica o generar una solución externa documentada de mayor resolución. Exponer la fórmula de Richardson, datos sin redondear, orden estimado y supuestos. Con los valores redondeados 23,925; 23,949; 23,961, el orden observado resulta aproximadamente 1 y la extrapolación 23,973: esta cuenta es coherente con lo reportado, pero continúa siendo una estimación interna.

**Respuesta defendible:** «23,96 es una referencia aproximada, no exacta. Mi secuencia la respalda internamente, pero debo identificar su fuente independiente y tratar el 0,05 % como estimación de sensibilidad».

### H08. Jacobiano positivo en puntos de Gauss no garantiza validez en todo el elemento

**Estado:** afirmación refutada mediante contraejemplo; aceptación efectiva del caso pendiente de código. **Prioridad:** alta.

**Evidencia.** La p. 62 afirma que, al controlar det J en los puntos de Gauss, ninguna geometría degenerada o invertida llega al ensamblaje. La p. 25 también presenta positividad local como garantía general de biyección.

**Contraejemplo calculado.** Un Q4 con nodos consecutivos (0,0), (1,0), (0,4;0,4), (0,1) tiene, en los cuatro puntos de la regla 2 × 2:

`det J ≈ 0,186603; 0,100000; 0,100000; 0,013397`.

Todos son positivos. En la esquina natural (1,1), sin embargo, `det J = −0,05`. Es un cuadrilátero cóncavo e inválido para el mapeo pretendido. Otro control geométrico podría rechazarlo; lo demostrado aquí es que **el muestreo de Gauss por sí solo no garantiza lo afirmado**.

**Pregunta probable:** «¿Cómo detecta una inversión entre los puntos que evalúa?»

**Corrección propuesta.** Cambiar “garantiza” por la descripción exacta del control implementado. En Q4 de lados rectos, controlar también esquinas y validez del contorno. Para Q9 curvo se necesita un tratamiento más cuidadoso; agregar unos puntos no constituye automáticamente una certificación global. Diferenciar invertibilidad local, validez del contorno e inyectividad global. Documentar también valor y escala de la tolerancia geométrica: det J tiene dimensiones de longitud al cuadrado.

**Respuesta defendible:** «El control en Gauss es necesario para integrar, pero no certifica toda la geometría. Debo completar el control o limitar la garantía que expresa el texto».

### H09. Omitir σz no subestima necesariamente von Mises

**Estado:** error de explicación confirmado por la propia fórmula. **Prioridad:** alta.

**Evidencia.** La p. 31 afirma que omitir σz en deformación plana subestima la tensión equivalente. La Ecuación 1.20 sí incluye correctamente σz = ν(σx + σy).

**Contraejemplo.** Para σx = σy = 100, τxy = 0 y ν = 0,30, resulta σz = 60. La equivalente tridimensional es 40. Si se impone indebidamente σz = 0, resulta 100. En este caso se **sobreestima**, no se subestima.

Más generalmente, manteniendo σx, σy y τxy, la diferencia entre los cuadrados de ambas equivalentes es `ν(ν−1)(σx+σy)²`. Para 0 ≤ ν < 0,5 es no positiva.

**Pregunta probable:** «¿Puede demostrar el sentido del error que afirma?»

**Corrección propuesta.** Sustituir por: “Omitir σz altera la tensión equivalente y puede sobreestimarla; debe emplearse el estado tridimensional correspondiente a deformación plana”. No cambiar la fórmula correcta por esta errata de interpretación. Añadir una prueba puntual del cálculo y de su presentación.

**Respuesta defendible:** «La ecuación incluye la componente correcta; la frase que describía el sentido del error estaba equivocada y debe corregirse».

### H10. La justificación Q4–Q9 contiene dos generalizaciones incorrectas

**Estado:** error conceptual de redacción. **Prioridad:** alta.

**Evidencia.** La p. 9 caracteriza la pareja como contraste de una base incompleta con una completa; también afirma que los conceptos isoparamétricos solo aparecen al pasar al continuo bidimensional.

**Problema técnico.** En el elemento de referencia, Q4 usa el espacio tensorial Q1 = span{1, ξ, η, ξη} y reproduce los polinomios lineales completos. Q9 usa Q2 y contiene los polinomios cuadráticos completos. La diferencia adecuada es orden bilineal frente a bicuadrático, no incompletitud lineal frente a completitud cuadrática. Además, una barra puede formularse como continuo unidimensional con coordenadas naturales, Jacobiano y cuadratura; en 2D estos objetos adquieren mayor riqueza geométrica. Las definiciones de espacios tensoriales pueden cotejarse en [DefElement: Lagrange](https://defelement.org/elements/lagrange.html).

**Pregunta probable:** «¿Qué término lineal le falta al Q4? ¿Una barra no es un continuo?»

**Corrección propuesta.** Justificar la pareja por incremento de orden dentro de la familia tensorial, tamaño de matrices y contraste de comportamiento en flexión. Justificar 2D por visibilidad de distorsión angular, acoplamiento entre direcciones y estados tensionales, evitando negar el caso 1D.

**Respuesta defendible:** «El Q4 es completo para campos lineales; su limitación en flexión no es falta de completitud lineal. Elegí 2D porque permite mostrar un conjunto más rico de conceptos manteniendo matrices manejables».

### H11. Cuadratura: algunas frases necesitan condiciones

**Estado:** generalización no demostrada. **Prioridad:** media.

**Evidencia.** La p. 27 afirma que aumentar la cuadratura en Q4 no aporta precisión apreciable y que en elementos distorsionados la diferencia es marginal. Las pp. 37–38 presentan una cuadratura de orden superior como garantía de no subestimar error.

**Pregunta probable:** «¿Es marginal para cualquier distorsión? ¿Qué demuestra que 3 × 3 o 4 × 4 integra suficientemente el error de campos trigonométricos?»

**Corrección propuesta.** Conservar 2 × 2 y 3 × 3 como reglas adoptadas, explicando que integración completa no significa exactitud algebraica para toda geometría. Acotar el comentario sobre sobreintegración a casos verificados. Hacer una comprobación de sensibilidad de las normas a aumentar la cuadratura; no se necesita una nueva campaña extensa.

**Respuesta defendible:** «Son reglas de integración estándar del elemento, pero no prometo exactitud de la integral para toda distorsión. La suficiencia de la cuadratura de error se puede comprobar aumentando su orden».

### H12. La comparación con SAP2000 requiere aislar diferencias de modelado

**Estado:** riesgo de atribución e información incompleta. **Prioridad:** alta.

**Evidencia.** Se atribuyen diferencias a la formulación shell frente al continuo plano (pp. 81, 93). El Anexo E menciona cargas distribuidas mediante un frame NONE (p. 146). Las capturas y tablas no sustituyen una especificación inequívoca de todas las opciones del modelo.

**Pregunta probable:** «¿Qué tipo exacto de shell utilizó? ¿Cómo se transfirió la carga? ¿Las restricciones y tensiones comparadas son equivalentes?»

**Vulnerabilidad.** La etiqueta Mindlin–Reissner por sí sola no demuestra la causa de la diferencia de tensiones membranales en un problema plano. Pueden intervenir interpolación, malla, apoyos, recuperación y promedio de tensiones, ejes locales y aplicación de cargas.

**Corrección propuesta.** Adjuntar modelo editable y ficha: versión, tipo de elemento, malla, espesor, material, opciones, ejes, grados de libertad restringidos, auto mallado, cargas equivalentes, peso propio, magnitud y ubicación de salida y criterio de promediado. Mostrar que frame NONE transmite la resultante correcta sin aporte de rigidez. Distinguir la solución elástica de Timoshenko–Goodier de una teoría unidimensional de viga de Timoshenko; documentar las condiciones de borde de la referencia de flecha.

**Respuesta defendible:** «La comparación es un contraste adicional. La diferencia observada no permite atribuir una causa única ni declarar superioridad. La ficha del modelo debe permitir repetirla con las mismas opciones».

### H13. La exactitud de σx en tres puntos no es exactitud global

**Estado:** limitación correctamente declarada, con algunas explicaciones excesivas. **Prioridad:** media.

**Evidencia.** La p. 82 aclara que el máximo corresponde a A, B y C; las Tablas 3.2 y D.4 muestran hasta 2,89 % en τxy. Se atribuye el incremento del error relativo principalmente a la escala de las componentes.

**Pregunta probable:** «¿Por qué eligió solo esos puntos? ¿Qué sucede cerca de los apoyos y con el cortante?»

**Corrección propuesta.** Mantener “máximo entre los tres puntos de control”. La escala explica la sensibilidad de un porcentaje, pero no identifica el origen de la discrepancia absoluta. Para reforzar, añadir un perfil o norma por componente y una comparación de dos o tres mallas en la viga. Evitar máximos de tensión en singularidades como criterio de convergencia global. La fórmula analítica de σx del Anexo E contiene un término cúbico en y: sustituir “distribución lineal” de pp. 83 y 142 por “predominantemente lineal, con corrección de elasticidad”.

**Respuesta defendible:** «El 0,04 % no caracteriza toda la solución: corresponde a σx en los puntos definidos. Reporto también componentes con mayor error y no lo oculto».

### H14. Alcanzar el orden MMS esperado no descarta todo error de implementación

**Estado:** inferencia excesiva, parcialmente corregida por la propia discusión. **Prioridad:** alta.

**Evidencia.** Las pp. 76 y 93 usan “descarta errores de orden” en varios mecanismos. La p. 38 atribuye una tasa inferior a un defecto de implementación; la Tabla 2.4 justifica ±0,5 por separación respecto de un orden inferior asociado a error de programación. Las pp. 94–95 reconocen límites mediante el defecto de extrapolación.

**Pregunta probable:** «¿Todo error cambia el orden? ¿Toda pérdida de orden implica que programó mal?»

**Vulnerabilidad.** Un error puede mantener una tasa; una tasa menor puede proceder de regularidad, geometría, cuadratura o régimen no asintótico. En el MMS suave ensayado esos factores pueden controlarse, pero es necesario declararlo. Una malla obtenida subdividiendo un cuadrilátero distorsionado no representa toda geometría Q9 curva o toda secuencia de distorsión.

**Corrección propuesta.** Usar “no se detectaron pérdidas de orden en las configuraciones ensayadas”. Documentar independencia de la fuente manufacturada, derivación de f y evaluación del error; evitar que una misma rutina equivocada defina el patrón y la solución. Conservar la prueba polinómica de extrapolación. Si se incorporan patch tests, movimientos rígidos y comprobaciones de simetría, explicar qué ruta verifica cada uno.

**Respuesta defendible:** «Las tasas son evidencia fuerte para esas configuraciones; no son una prueba de ausencia universal de errores. Por eso la batería separa desplazamientos, recuperación y pruebas algebraicas».

### H15. Las funciones implementadas superan las funciones contrastadas

**Estado:** limitación declarada. **Prioridad:** media.

**Evidencia.** No se contrasta externamente carga superficial linealmente variable; deformación plana solo se ejercita mediante MMS; Timoshenko se resuelve únicamente con Q9 (pp. 48, 106). No se presenta una campaña sobre heterogeneidad de materiales, geometría Q9 curva o proximidad a incompresibilidad.

**Pregunta probable:** «¿Su resultado vale también para esa función del programa que no aparece en las pruebas?»

**Corrección propuesta.** Añadir una matriz función–prueba–alcance. Priorizar una carga lineal de borde con fuerzas equivalentes analíticas y un caso independiente en deformación plana si se desea fortalecer esa rama. No es necesario construir una presa completa: su realismo no garantiza mayor capacidad de detectar errores. Mantener explícito el límite cercano a ν = 0,5.

**Respuesta defendible:** «No extiendo el resultado a funciones no ejercitadas. Las distingo en la matriz de cobertura y propongo casos específicos para ampliarla».

### H16. El campo de tensiones medido por MMS no coincide necesariamente con el color dibujado

**Estado:** discrepancia entre descripciones; implementación pendiente de inspección. **Prioridad:** alta.

**Evidencia.** La p. 75 define σh* interpolado mediante funciones de forma y lo identifica con lo que muestra el post-proceso. La p. 69 describe triangulación y sombreado de Gouraud, que interpola sobre triángulos. La p. 70 describe una sonda mediante mapeo inverso.

**Pregunta probable:** «¿La norma de error verifica la misma magnitud que ve el usuario en cualquier punto del contorno?»

**Vulnerabilidad.** Interpolación isoparamétrica, evaluación directa D B u e interpolación gráfica no son en general idénticas. Además, interpolar von Mises nodal no equivale a calcularlo a partir de componentes interpoladas.

**Corrección propuesta.** Documentar separadamente: campo de Gauss, extrapolado, promediado, evaluado por la sonda y representado mediante colores. Declarar cuál verifica cada norma. Añadir una comprobación puntual sobre un Q9 con variación no lineal. Si el color es aproximación visual, decirlo expresamente sin prometer identidad con el campo verificado.

**Respuesta defendible:** «La norma evalúa el campo numérico definido. La imagen es una representación que puede incorporar otra interpolación; debo distinguirla de los valores de la sonda y las tablas».

### H17. Promediar tensiones puede borrar discontinuidades físicas

**Estado:** riesgo condicionado al uso multimaterial; pendiente de código. **Prioridad:** media.

**Evidencia.** La Ecuación 1.24 promedia aportes de elementos adyacentes sin expresar separación por material (p. 34). El programa admite materiales por elemento. La misma página presenta el salto entre elementos como indicador de malla gruesa.

**Pregunta probable:** «¿Qué ocurre en una interfaz entre materiales? ¿Todo salto es un error?»

**Corrección propuesta.** Aclarar si se promedia por región/material y qué ocurre en interfaces. No todos los componentes de tensión deben ser continuos en una interfaz; un salto no siempre es un error de discretización. Mantener acceso a valores elementales y distinguir discontinuidad física de falta de resolución numérica.

**Respuesta defendible:** «El suavizado es un recurso de post-proceso; no debe borrar una discontinuidad material ni interpretarse siempre como una mejora de exactitud».

### H18. “Fijado de antemano” y “reproducible” necesitan evidencia de versión

**Estado:** documentación parcial, sin indicio de falsedad. **Prioridad:** alta.

**Evidencia.** Se identifica EduFEM 1.0.0, revisión 91e3df0 y fecha (p. 43), lo cual es positivo. Se declara que criterios y umbrales precedieron a las corridas (p. 51). El Anexo A indica clonar el repositorio sin seleccionar esa revisión. La tabla D.1 no reúne todos los guiones citados en el cuerpo, como el benchmark y algunas regresiones.

**Pregunta probable:** «Si descargo hoy, ¿obtengo exactamente la versión de sus tablas? ¿Cómo sé que los criterios no se ajustaron después?»

**Corrección propuesta.** Añadir checkout del hash completo, archivo de dependencias con versiones, entorno, datos de entrada, CSV y registro de ejecución. Identificar el instalador mediante checksum y correspondencia con la revisión. Un protocolo fechado o historial de commits puede respaldar cuándo se fijaron criterios; si no existe, evitar certificar una cronología que no puede documentarse. No crear retrospectivamente evidencia con apariencia de previa. Mantener la distinción honesta ya declarada para los umbrales de tensiones escogidos después de observar resultados.

**Respuesta defendible:** «La versión está identificada; completaré las instrucciones para ejecutarla exactamente. Los umbrales retrospectivos están separados de los criterios de la hipótesis».

### H19. El aporte debe formularse sin depender de ausencia universal de alternativas

**Estado:** revisión limitada correctamente declarada, con sobreextensiones posteriores. **Prioridad:** alta.

**Evidencia.** §1.1 declara revisión no exhaustiva y evidencia asimétrica. Sin embargo, algunas conclusiones pasan de “no reúne la combinación de atributos” a “no ofrece atributos que hacen trazable y verificable” (p. 101). El problema también equipara caja negra con imposibilidad de comprobar resultados.

**Pregunta probable:** «¿Por qué no bastaba ED-Elas2D o VisualFEA? ¿No puedo verificar un programa comercial mediante equilibrio, benchmarks y convergencia?»

**Corrección propuesta.** Distinguir falta de exposición del cálculo interno de imposibilidad de verificación externa. Conservar “entre los recursos y versiones documentados”. Añadir fecha, consultas, fuentes y tabla de evidencia de la revisión; “no consta” no significa “no existe”. Defender el aporte como integración documentada, diseño de trazabilidad y evaluación reproducible en un dominio acotado. Python y el idioma por sí solos no constituyen novedad científica.

La referencia de Lee [17], volumen 23, número 2, pp. 157–169, coincide con la [ficha editorial de Wiley](https://onlinelibrary.wiley.com/doi/10.1002/cae.21586). Ese dato no debe cambiarse al número 1 por una referencia anterior.

**Respuesta defendible:** «No afirmo haber inventado el MEF ni el software educativo. El aporte es la integración y documentación de un diseño que permite seguir el cálculo y evaluarlo; la comparación de novedad se restringe a los antecedentes revisados».

### H20. Código abierto no significa licencia permisiva

**Estado:** error verificable en la nota de la Tabla 2.5. **Prioridad:** media.

**Evidencia.** La p. 57 llama permisivas a todas las bibliotecas listadas. La documentación oficial de PyMuPDF declara disponibilidad bajo AGPL y licencia comercial, por lo que esa descripción colectiva es incorrecta. Véase [PyMuPDF: License and Copyright](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright).

**Pregunta probable:** «¿Cuál es la licencia concreta de EduFEM y de sus dependencias?»

**Corrección propuesta.** Sustituir la nota general por una tabla de licencias correspondiente a las versiones distribuidas y documentar la licencia propia del repositorio. No confundir publicación del código, gratuidad, software libre y licencia permisiva. Este hallazgo corrige una afirmación documental; no concluye que la distribución incumpla una licencia, porque no se inspeccionó el paquete.

**Respuesta defendible:** «La nota generaliza indebidamente. Debo identificar las licencias reales de las versiones incluidas y la del proyecto».

### H21. Los tiempos y la memoria reportados corresponden a una parte del sistema

**Estado:** alcance incompleto del benchmark. **Prioridad:** media.

**Evidencia.** La Tabla 3.9 mide ensamblaje y solución en una corrida representativa; especifica “procesador Intel de 2012”, pero no modelo, RAM ni hilos. La memoria compara almacenamiento de K densa con K dispersa (p. 96).

**Pregunta probable:** «¿Los 13 MB incluyen factores LU, arreglos temporales, interfaz y memoria PDF? ¿Un segundo significa que toda la aplicación termina?»

**Corrección propuesta.** Especificar que son tiempos del núcleo y memoria de K. Añadir hardware, versiones, número de hilos, calentamiento y mediana/rango de repeticiones breves. Para una afirmación sobre consumo total, medir memoria máxima del proceso. Una malla de Cook de 33 282 GDL no acredita por sí sola análisis de una estructura real con idéntico rendimiento o exactitud.

**Respuesta defendible:** «La tabla caracteriza ensamblaje, solución y almacenamiento de K; no el consumo total ni la generación del informe. El rendimiento integral es una medición distinta».

### H22. Corregir residuos de teoría, notación y anexos reduce preguntas evitables

**Estado:** hallazgos editoriales y conceptuales puntuales. **Prioridad:** media.

**Evidencia y acción:**

- **Forma fuerte, p. 21:** “continuidad de segundo orden” debe acotarse a formulación clásica y regularidad por regiones. No afirmar C² global para cualquier material o dominio.
- **Sistema particionado, pp. 30 y 167:** si Fr denota fuerzas aplicadas, el bloque restringido requiere la reacción: `Krf uf + Krr ur = Fr + Rr`. El propio texto luego calcula R correctamente. Distinguir cargas aplicadas de fuerzas totales para que las dos ecuaciones sean consistentes.
- **Anexo E, pp. 144–156:** se conservan explicaciones originales que la introducción al anexo corrige. Es mejor corregir las hojas o colocar notas al lado de cada afirmación, evitando que el lector encuentre dos versiones. En particular, la explicación de p. 156 sobre que subdividir un frame “produce” el efecto cortante debe sustentarse mediante opciones y resultados del modelo; no se deduce de la subdivisión por sí sola.
- **Capacidad del hormigón:** conservar fuera de las conclusiones la comparación aislada de tensiones con f'c. El ejemplo es elástico y no constituye diseño resistente de hormigón armado, como ya advierte el anexo.
- **Presentación:** revisar encabezados con doble punto, consistencia de “desplazamiento/deformación”, unidad kgf frente a kg, títulos, numeración de preguntas y referencias cruzadas. La nomenclatura anuncia PI-1 a PI-3, pero la formulación presenta dos preguntas.
- **Estilo bibliográfico:** “En:” no es por sí solo un error de contenido. Sin embargo, la declaración de Vancouver y APA debe corresponder al estilo requerido por la Carrera; comprobarlo con la guía institucional, sin presumir cuál exige.

**Respuesta defendible:** «Son correcciones de claridad y consistencia que realizaré sin alterar los resultados. Los anexos también forman parte de la evidencia y deben sostener las mismas definiciones que el cuerpo».

## 5. Objeciones que la tesis ya puede responder

### «Sin alumnos no puede llamarse software educativo»

Respuesta sugerida: «Educativo designa la finalidad y las funciones de diseño: exposición del procedimiento, módulos y memoria. Esta investigación evalúa su realización técnica; no afirma que haya demostrado mejorar el aprendizaje. Esa eficacia requiere otra evaluación».

La tesis ya distingue esos planos en pp. 20, 55 y 106. No conviene borrar esa delimitación ni presentar el consenso publicado como validación pedagógica de EduFEM.

### «Tres casos son una muestra demasiado pequeña»

Respuesta sugerida: «No busco una inferencia estadística sobre personas. Los casos se seleccionan para ejercitar mecanismos y comparar con referencias. Su suficiencia depende de la cobertura de funciones, no solo de su cantidad. Declaro las rutas que no cubren».

La respuesta gana fuerza con una matriz de cobertura, no con una afirmación de que tres casos bastan universalmente.

### «Usó NumPy y SciPy; entonces no desarrolló el cálculo»

Respuesta sugerida: «Las bibliotecas resuelven operaciones algebraicas generales. Mi implementación formula elementos, integración, ensamblaje, condiciones de borde, recuperación y exposición del procedimiento. El Anexo C distingue esas responsabilidades».

No es necesario reprogramar un solucionador lineal para que exista un aporte de ingeniería.

### «Es un proyecto de grado, no una tesis»

Respuesta sugerida: «El trabajo entrega un producto y estudia un problema de diseño: qué decisiones permiten exponer y comprobar el procedimiento. Fundamenta esas decisiones y las evalúa con criterios explícitos. El aporte que someto a consideración es el artefacto acompañado de conocimiento de diseño y de evaluación reproducible».

Esta es una defensa académica, no una garantía de clasificación administrativa. Para esa clasificación se necesita el reglamento vigente y la modalidad aprobada. Evitar responder que toda investigación tecnológica está exenta de evidencia: su evidencia debe corresponder a lo que afirma.

### «Los elementos Q4 y Q9 ya existen»

Respuesta sugerida: «La novedad no se atribuye a la formulación de esos elementos. Se encuentra en la solución educativa integrada, su trazabilidad y la documentación de su evaluación, dentro del alcance comparativo declarado».

## 6. Redacciones propuestas para alinear el trabajo

Estas propuestas son alternativas de ajuste, no modificaciones ya realizadas en la tesis. Deben mantenerse consistentes en Introducción, metodología, resultados y conclusiones.

### Problema

> ¿Cómo desarrollar y evaluar un software educativo que permita inspeccionar y reconstruir el procedimiento de cálculo del MEF en elasticidad lineal plana con elementos Q4 y Q9, y comprobar sus resultados frente a referencias definidas, como recurso destinado a la Carrera de Ingeniería Civil de la UATF?

### Proposición tecnológica o hipótesis de trabajo

> La integración de un motor de elementos finitos, módulos de exposición vinculados al modelo y una memoria de cálculo permitirá reconstruir las etapas del análisis en los casos definidos; la corrección numérica y la reproducibilidad se evaluarán mediante criterios explícitos de cobertura, cotejo independiente y concordancia con soluciones de referencia.

Debe especificarse la prueba de reconstrucción y conservar la posibilidad de incumplimiento. No declarar que todo criterio se cumple mientras H03 y H04 continúen pendientes.

### Conclusión ajustada al estado actual de la evidencia

> Los resultados reportados respaldan la implementación de EduFEM y su concordancia numérica en las configuraciones ensayadas. El documento muestra mecanismos de exposición y seguimiento del cálculo, aunque la cobertura de algunos contenidos y la reproducción independiente completa de la memoria requieren evidencia adicional. No se evaluó el efecto sobre el aprendizaje ni se realizó validación física experimental.

### Después de completar las correcciones

Puede formularse una conclusión más afirmativa si se acompaña de resultados: «La versión identificada cumplió los criterios revisados de cobertura y reproducción que se enumeran en la tabla final». Si los criterios se revisaron durante la preparación, debe explicitarse esa revisión.

## 7. Plan de corrección sin prueba de campo

| Orden | Acción concreta | Evidencia de cierre |
|---|---|---|
| 1 | Alinear problema, hipótesis y conclusión con evaluación tecnológica | Mismos términos y alcance en las cuatro secciones |
| 2 | Reauditar las 18 filas, especialmente FEA18 y FEA30 | Tabla con estado real y demostración por ítem |
| 3 | Documentar un cotejo independiente de la memoria | Comparación por etapa con valores y tolerancias |
| 4 | Corregir Jacobiano, von Mises, Q4 y ecuación de reacciones | Texto y ecuaciones consistentes; pruebas puntuales |
| 5 | Acotar o completar CSV | Casos de ida y vuelta que incluyan datos hoy omitidos |
| 6 | Aclarar referencia de Cook y modelo SAP2000 | Fuente/configuración de Cook y archivo/ficha SAP2000 |
| 7 | Congelar la versión evaluada | Hash completo, dependencias, datos, comandos y logs |
| 8 | Ajustar afirmaciones del benchmark, anexos y licencias | Tablas precisas y notas corregidas |

**Lo que no priorizaría ahora:** ampliar a 3D, añadir numerosos tipos de elemento, modelar una presa completa o introducir una campaña con alumnos solamente para responder a una objeción general. Primero hay que asegurar que las afirmaciones actuales se sostengan con evidencia concreta.

## 8. Material breve que conviene llevar a la defensa

1. Una diapositiva con tres columnas: qué se desarrolló, cómo se evaluó y qué no se afirma.
2. Un caso pequeño listo para ejecutar, con un elemento seleccionado y su correspondencia N → J → B → ke → K → u → σ.
3. Una hoja de cotejo independiente, con una operación completa y su discrepancia numérica.
4. La matriz corregida de contenido y de funciones verificadas.
5. La versión congelada, los archivos de los casos y la memoria completa.
6. Una lámina de limitaciones, expresadas como fronteras de evidencia y no como promesas pendientes.

## 9. Comprobaciones efectuadas y límites de esta auditoría

| Comprobación propia | Resultado | Qué permite concluir |
|---|---|---|
| Reconstrucción independiente del Q4 del Anexo G | Desplazamientos coincidentes al redondeo publicado | Concordancia del ejemplo para esos datos |
| Primera fila de ke de E3 | Coincide con la matriz publicada al redondeo | Consistencia de esa operación elemental |
| Tensiones de Gauss de E3 | Coinciden con Tabla G.4 al redondeo | Consistencia de la recuperación en esos puntos |
| Equilibrio del ejemplo reconstruido | ΣRx ≈ 3,98 × 10⁻¹³; ΣRy ≈ 1000, compensando la carga −1000 | Equilibrio global del cálculo independiente |
| Q4 cóncavo con Gauss positivo | det J negativo en una esquina | Refuta la suficiencia del muestreo de Gauss por sí solo |
| Von Mises con σx = σy = 100 y ν = 0,3 | 40 con σz correcto; 100 al omitirlo | Refuta la frase “subestima” como regla general |
| Referencia de Lee [17] | Ficha editorial: 23(2), 157–169 | Ese número de revista está bien consignado |
| Licencia de PyMuPDF | Documentación oficial: AGPL o comercial | No corresponde llamar permisivas a todas las dependencias |

Los cálculos puntuales se realizaron a partir de los datos publicados, sin importar rutinas de EduFEM. No representan una certificación del código ni del uso profesional de la herramienta. Los hallazgos marcados como pendientes de código deben comprobarse en la revisión exacta evaluada antes de atribuirle un fallo de ejecución.

**Valoración final:** la defensa más sólida combina reconocimiento de los límites con demostraciones concretas. Hay resultados numéricos plausibles y un ejemplo que sí pudo reproducirse; las correcciones prioritarias se concentran en no convertir esa evidencia acotada en garantías universales o en conclusiones causales que el diseño no midió.
