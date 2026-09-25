## A. Glosario de variantes: un concepto, un nombre

| Concepto | Variantes halladas (recuento) | Nombre canónico recomendado | ¿Induce a error? |
|---|---|---|---|
| Secuencia del cálculo | canal de cálculo (27) · canal del MEF (1, f. 17) · flujo del Método de Elementos Finitos (1, f. 109) · proceso de cálculo (2, f. 2 y 86) | **canal de cálculo** | Sí: es el concepto del objetivo general; la variante «proceso» lo confunde con la fase «proceso» de la interfaz |
| Fases de la interfaz | pre-proceso (30) · post-proceso (51) · Postproceso (1, f. 73) | **pre-proceso / proceso / post-proceso** | No, cosmético |
| Magnitud σ | tensión (203) · esfuerzo (8: 7 en el Anexo E, 1 en cabecera CSV) | **tensión** | Sí, en el Anexo E: «esfuerzo cortante» puede leerse como esfuerzo interno de viga, no como τxy |
| Condición de Dirichlet | restricción (54) · apoyo (21) · condición de contorno (2: la regla en f. 48 y su infracción en f. 71) · vínculo (4) | **restricción** (y «apoyo» solo para el dispositivo físico de los casos) | Sí: el documento proscribe «condición de contorno» y luego la usa |
| Grado de libertad | GDL (46) · grados de libertad (20) · DOF (1, mencionada para descartarla) | **GDL**, desarrollada en su primera aparición | No |
| Método | MEF (65) · Método de los Elementos Finitos (7) · Método de Elementos Finitos (1) · FEM/FEA (códigos del consenso) | **MEF** | No, salvo el artículo omitido en f. 109 |
| Discretización | malla (123) · mallado (11) · discretización (11) | **malla** para el objeto, **discretización** para la operación | No |
| Área de dibujo | lienzo (56) · canvas (0) | **lienzo** | No |
| Documento generado | memoria de cálculo (47) · informe (1) · reporte (0) | **memoria de cálculo** | No |
| Componentes M0–M7 | módulo educativo (33) · módulo interactivo (6) | **módulo educativo** | Sí: «módulo interactivo» es el nombre del indicador de la cláusula (a) y no coincide con el de la cosa medida |
| Revisión previa del modelo | comprobador de salud (8, anexos) · validador de salud (5, cuerpo) · salud del modelo (6) | **comprobador de salud** | Sí: parecen dos instrumentos distintos entre el Capítulo 3 y el Anexo B.8 |
| Fenómeno del Q4 | bloqueo por cortante (27) · shear-locking (4, siempre entre paréntesis) | **bloqueo por cortante (shear-locking)** en la primera aparición de cada capítulo | No |
| Modos de energía nula | modos espurios (7) · hourglass (6, siempre entre paréntesis) | **modos espurios (hourglass)** | No |
| Resolutor del sistema | solucionador (15) · solver (0) · motor de cálculo (12, concepto más amplio) | **solucionador** | No |
| Variable dependiente | criterio (66) · criterio logrado (f. 39-40) · juicio de resultados (f. 39-40) · comprensión (6) | **criterio para interpretar la respuesta estructural** | Sí: es la variable que el tribunal rastrea de punta a punta |
| Destinatario | estudiante (62) · alumno (22) · usuario (26) · egresado (10, correcto en las citas del consenso) | **estudiante** en el cuerpo; **usuario** solo en los manuales | Sí: la población se define sobre «estudiantes» |
| El producto | herramienta (57) · software (106) · programa (51) · aplicación (19) · artefacto (15) · recurso (20) | **EduFEM** / **la herramienta**; «el artefacto» solo en 2.1 | Sí: «software» sirve a la vez para el producto y para el género |
| Contraste externo | verificación (91) · validación (97) · comprobación (1) · validez de contenido (24) | **verificación** / **validación numérica** / **validez de contenido** | Sí: 1.13 declara una sola acepción de «validación» y el documento usa cuatro |
| Instrumento documental | tabla de especificaciones (20) · matriz de especificaciones (0) · matriz de principios (16) · matriz de consistencia (7) | **tabla de especificaciones** (son tres instrumentos distintos, bien diferenciados) | No |
| Ítems del consenso | destrezas (42) · competencias (1) · habilidades (0) | **destrezas** | No, cosmético |
| Unidades de análisis | casos de estudio (5) · casos de referencia (17) · problemas de referencia (3) · banco de prueba (2) · ejemplo canónico (14) · caso canónico (1) | **casos de estudio** (unidades) y **ejemplo canónico** (el cuadrado de nueve nodos) | Sí: el lector debe deducir que son siempre los mismos tres |
| Magnitud de salida | respuesta estructural (19) · resultados (108) | **respuesta estructural** cuando se hable de la variable; «resultados» para el resto | No |

## B. Tabla de notación: símbolos frente a la Nomenclatura

### B.1 Símbolos con dos significados

| Símbolo | Significado 1 (declarado) | Significado 2 (no declarado) | Dónde | Propuesta |
|---|---|---|---|---|
| p | Orden polinómico del elemento (Nomenclatura, f. xiii; f. 35; f. 63) | Índice del punto de cuadratura: Σ_p, w_p, (ξ_p, η_p), σ_p | §1.7 | Índice de cuadratura → **g** (coherente con n_g y con mín_g de §1.12) |
| N | Función de forma N_i y matriz N (Nomenclatura, f. xiii) | Número de subdivisiones por lado: «N × N», «N = 16» | f. 39, 63 y pies de figura del Anexo D | Subdivisiones → **n_el**, o declarar N en la Nomenclatura |
| h | Tamaño característico de malla (Nomenclatura, f. xiii) | Subíndice de la solución discreta: u_h, σ*_h | §1.13, Cap. 3, Anexo D | Declarar el subíndice h en la Nomenclatura: «(·)_h — magnitud de la solución discreta» |
| e | Subíndice de elemento: k_e, u_e, f_e^vol | Subíndice de extremo de arista: q_e (frente a q_s) | §1.10 | Carga en los extremos → **q_1, q_2** |
| L | Longitud de la arista cargada (§1.10) | Factor triangular de Cholesky, K_ff = L Lᵀ (§1.11) | §1.10-1.11 | Mantener L para la longitud; el factor, en negrita y declarado |
| Q | Compacidad o stretch, ∈ [0,1] (Nomenclatura) | Prefijo de los elementos Q4 y Q9 | §1.12 | Sin riesgo real, pero conviene escribir siempre «la compacidad Q» |
| E, t | Bien resueltos: la Nomenclatura advierte que E es el módulo y **E** la matriz de extrapolación, t el espesor y **t** las tracciones | — | f. xiii | Mantener; es el modelo a seguir para los demás casos |

### B.2 Símbolos usados y ausentes de la Nomenclatura

| Símbolo | Significado | Primera aparición |
|---|---|---|
| 𝒜 (operador de ensamblaje) | Ensamblaje de las matrices elementales | ec. (1.17), f. 28 |
| X_e | Coordenadas nodales del elemento | ec. (1.9), f. 24 |
| u_e | Desplazamientos nodales del elemento | §1.3, f. 20 |
| n | Número de nodos del elemento | ec. (1.8), f. 23 |
| δu, δε | Desplazamientos y deformaciones virtuales | ec. (1.2), f. 20 |
| M | Funciones de forma en los puntos de Gauss; E = M⁻¹ | ec. (1.23), f. 32 |
| f_e^vol, F_n, F_Γ | Aportes volumétrico, nodal y de superficie al vector de cargas | ec. (1.17), f. 28 |
| K_ff, K_fr, K_rf, K_rr, u_f, u_r, F_f, F_r | Partición libre/restringida del sistema | ec. (1.18), f. 29 |
| L, q, q_s, q_e | Arista cargada y carga distribuida en sus extremos | §1.10, f. 28 |
| n_e | Número de elementos que comparten un nodo | ec. (1.26), f. 32 |
| m | Número de puntos de la regla de Gauss unidimensional | §1.7, f. 26 |
| R_J | Razón entre el menor y el mayor det J del elemento | §1.12, f. 33 |
| AR, T_R | Relación de aspecto y estrechamiento (taper) | ec. (1.27), f. 34 |
| X_1, X_2, X_3, r_i | Descomposición bilineal del cuadrilátero | ec. (1.27), f. 34 |
| u_h, σ*_h, u_M | Solución numérica, tensión recuperada y solución manufacturada | §1.13, f. 35 |
| c, l, I, V, H, f′c | Semiperalte, semiluz, inercia, cortante, canto y resistencia característica | Anexo E, f. 130-135 |

### B.3 Entradas de la Nomenclatura sin uso en el documento

| Entrada | Situación |
|---|---|
| GUI | Una sola aparición en todo el documento: la propia entrada (f. xiv). El texto dice siempre «interfaz gráfica» |
| TP, DP | Solo como subíndices de D y en una tabla del Anexo D; nunca en prosa. Corresponden a la tabla de símbolos, no a la de siglas |
| FEA, FEM | Correctamente acotadas: la propia entrada advierte que son códigos de ítems y no siglas de la prosa |
