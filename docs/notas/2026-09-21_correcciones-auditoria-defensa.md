# Correcciones de la auditoría de defensa, y qué se dejó como está

**Fecha**: 2026-09-21 · **Autor**: Claude (sesión con el autor) · **Estado**: aplicado y compilado
**Fuente**: [`docs/auditorias/Auditoria_defensa_tesis_EduFEM.md`](../auditorias/Auditoria_defensa_tesis_EduFEM.md) (22 hallazgos, H01 a H22)
**Documento corregido**: `tesis/main_final.tex` — 187 hojas, 0 errores, 0 desbordes, 0 referencias ni citas indefinidas

## Qué pidió el autor

Quitar los preliminares para la predefensa; decidir **con criterio propio** qué hallazgos de
la auditoría corregir, sin seguirla al pie de la letra, sabiendo que el punto «alinear
problema, hipótesis y conclusión con evaluación tecnológica» sí tiene razón; usar para la
membrana de Cook la fuente que él consiguió; y dejar el 18/18 en pie salvo que hubiera motivo
para tocarlo.

## Criterio con que se decidió

La auditoría es buena y sus contraejemplos son reales: **los tres que se podían comprobar con
un cálculo se comprobaron en esta sesión antes de tocar nada**, y los tres resultaron ciertos.
Pero no todo lo que propone conviene hacerlo. Se aplicó lo que cae en tres categorías:

1. **Lo que es falso y un tribunal puede refutar con un cálculo de treinta segundos.** No es
   negociable: una afirmación técnica equivocada cuesta credibilidad sobre todo lo demás.
2. **Lo que promete más de lo que el trabajo midió.** Es el punto que el autor señaló, y es
   donde una tesis tecnológica se defiende o se cae.
3. **Lo que se puede afirmar mejor con la evidencia que ya existe.** Aquí entra la fuente
   nueva de Cook, que convierte una debilidad señalada en la validación externa más fuerte
   del documento.

Se descartó lo que habría exigido rehacer el trabajo o desmontar decisiones ya tomadas.

## Comprobaciones hechas antes de corregir

| Qué se comprobó | Cómo | Resultado |
|---|---|---|
| Von Mises al omitir $\sigma_z$ | Álgebra con $\sigma_x=\sigma_y=100$, $\nu=0{,}30$ | 40 con $\sigma_z$ correcto, 100 al omitirlo: **sobreestima**, no subestima |
| Jacobiano muestreado en Gauss | Q4 cóncavo de vértices (0;0), (1;0), (0,4;0,4), (0;1) | Los cuatro $\det\bm{J}$ positivos (+0,187; +0,100; +0,100; +0,013) y una **esquina en $-0{,}050$** |
| Control por esquinas del software | `fem/mesh_quality.scaled_jacobian_corners` sobre ese mismo elemento | $-0{,}38$: **sí detecta** el vértice entrante que el muestreo interior no ve |
| Base polinómica del Q4 | Reproducción de monomios sobre el elemento de referencia | Reproduce $1$, $\xi$, $\eta$ y $\xi\eta$ con error $10^{-16}$; **es completo en grado 1** |
| Licencias de las dependencias | `importlib.metadata` en el entorno del proyecto | **PyMuPDF: AGPL-3.0 o licencia comercial**, no permisiva |
| Cifras de Cook | Tabla 5 del artículo nuevo frente a la Tabla 3.4 de la tesis | Coinciden **en las cinco mallas**, dígito a dígito |

## Lo que se corrigió

### 1. Preliminares fuera (pedido del autor)

`main_final.tex` deja comentada la línea de `00_preliminares`. El archivo se conserva, con su
dedicatoria, sus agradecimientos y el párrafo opcional de declaración de uso de herramientas
de inteligencia artificial: para la entrega final basta descomentar una línea. El documento
pasó de 189 a 187 hojas.

### 2. Alineación de problema, hipótesis y conclusión (H01)

Es el punto que el autor señaló y el de mayor efecto. Las conclusiones respondían al problema
diciendo que la caja negra «incide de raíz», lo que se lee como un hallazgo empírico sobre la
Carrera. Ahora la respuesta se enuncia como lo que es:

> La respuesta que este trabajo sostiene es de orden técnico: la incidencia está en el medio
> de cálculo. […] El trabajo lo establece por la vía que le corresponde a una investigación
> tecnológica: construyendo ese software y midiendo sobre él las dos propiedades, con
> criterios fijados de antemano.

Y se añadió, en el lugar donde el tribunal lo busca, un párrafo que declara el alcance de la
inferencia: la evidencia evalúa el software en escenarios controlados, la Carrera es el
contexto al que el trabajo se destina y no un lugar del que se hayan tomado observaciones, y
queda fuera de lo medido qué ocurre cuando el medio se pone en manos de un curso. El mismo
alcance se repite al cerrar el contraste de la hipótesis en el Capítulo 3, y el veredicto pasa
a ser «comprobada en sus dos cláusulas, **sobre el software y los casos de estudio**».

**No se reformuló el problema como «diseño y evaluación de una solución técnica»**, que era lo
que proponía la auditoría: eso habría roto el molde causa-efecto que el tribunal exige. La
corrección es quirúrgica, en la respuesta y en el alcance, no en el molde.

### 3. Tres errores técnicos (H09, H08, H10)

- **Von Mises.** Decía que omitir $\sigma_z$ en deformación plana «subestima la tensión
  equivalente». Es falso y se demuestra en una línea. Ahora dice que la altera y puede
  sobreestimarla, **con el contraejemplo escrito en el propio texto** (40 frente a 100). La
  ecuación siempre estuvo bien: el error era de interpretación.
- **Jacobiano.** Decía que, controlando $\det\bm{J}$ en los puntos de Gauss, «ninguna geometría
  degenerada o invertida llega al ensamblaje». Un muestreo finito no puede garantizar eso.
  Ahora el texto describe **los tres controles que el software realmente tiene** —determinante
  en los puntos de Gauss, orientación por área signada en el comprobador de salud, y Jacobiano
  escalado por esquinas en el módulo de calidad de malla— y dice qué cubre cada uno. En el
  Capítulo 1 se distingue además la condición (que se exige en todo el elemento) de su
  comprobación (que se hace en puntos). El cambio no debilita al software: lo describe mejor,
  porque el control por esquinas sí detecta el caso que el interior no ve.
- **Q4 y Q9.** Decía que la pareja contrasta «una base polinómica incompleta con una completa».
  El Q4 reproduce los polinomios lineales completos: lo que lo distingue del Q9 es el orden,
  bilineal frente a bicuadrático. Corregido, con la consecuencia dicha: la diferencia gobierna
  el comportamiento en flexión, que es de lo que trata la membrana de Cook.

### 4. La membrana de Cook, con fuente publicada (H07) — y una validación externa que no estaba aprovechada

El valor de referencia 23,96 se presentaba como «de uso extendido», sin fuente junto al dato.
Era un hallazgo repetido en dos auditorías. El artículo que consiguió el autor lo resuelve y
regala algo más.

- **Referencia con fuente.** Štembera y Füssl advierten que el problema no tiene solución
  analítica disponible y obtienen su referencia numéricamente, con una malla de 192×128, en
  **23,965** (p. 28). El texto lo cita y señala que ese valor **cae dentro del intervalo
  [23,96 ; 23,97]** que la tesis ya estimaba por su cuenta con extrapolación de Richardson: la
  fuente externa y la evidencia propia se respaldan mutuamente.
- **Contraste externo de toda la secuencia.** Los desplazamientos que EduFEM calcula con Q4
  —11,845; 18,299; 22,079; 23,430 y 23,818— coinciden **en las cinco mallas y hasta la última
  cifra publicada** con los que esa fuente reporta para un cuadrilátero de cuatro nodos. Se
  añadió un párrafo que lo dice y que acota lo que eso prueba: no que ambos programas sean
  correctos —un error compartido de formulación se reproduciría en los dos— sino que el motor
  de EduFEM resuelve el caso como lo resuelve un código independiente y publicado.
- La razón de errores Q4/Q9 se completó con el valor publicado: doce veces con 23,97, quince
  con 23,96 y **trece con 23,965**.

**Bibliografía**: entra `stembera2019dkmq24` como preprint de arXiv (1906.06136v3), que es la
versión que el autor tiene. No se consignan revista, volumen ni DOI, que el ejemplar no
imprime. Quedan **26 entradas citadas**. El respaldo documental suma tres fichas con pasaje
literal y folio verificado en `respaldo_citas/verificado.json`.

### 5. Dos afirmaciones documentales excesivas (H20, H05)

- **Licencias.** La nota decía que todas las bibliotecas son «de licencia permisiva». PyMuPDF
  se distribuye bajo AGPL-3.0 o licencia comercial, comprobado en el entorno del proyecto. La
  nota ahora lo distingue y explica por qué importa: una licencia recíproca condiciona los
  términos con que puede redistribuirse el conjunto. **Esto le toca decidirlo al autor**: ver
  más abajo.
- **CSV.** «Ida y vuelta sin pérdida» se acotó a lo que la prueba cubre —las entidades del
  modelo ensayado— y se dice que el formato de intercambio no equivale al nativo, que guarda
  además el valor de los desplazamientos prescritos y la configuración del proyecto.

### 6. FEA18 y FEA30, reforzados sin bajar el 18/18 (H03)

El autor pidió mantener el 18/18 y se mantiene: es defendible, porque el universo lo fija un
consenso publicado y la regla de marcado está declarada. Pero **FEA18 era la celda más
atacable**: se apoyaba solo en la membrana de Cook, cuyo refinamiento es global, mientras el
ítem pide refinar donde se concentran las tensiones. Se corrigió nombrando el instrumento
real —la construcción de la malla con densidad variable, por tabla o sobre el lienzo, con la
calidad de cada elemento a la vista en M0— y se añadió, en la lectura de la tabla, la
precisión que un tribunal va a pedir:

> El refinamiento local de FEA18 se obtiene construyendo la malla con más elementos donde se
> los necesita, no con un algoritmo adaptativo […]. Y la regla de parada de FEA30 la aplica
> quien compara dos mallas sucesivas. En ambos casos el instrumento existe y está descrito,
> pero lo ejecuta el usuario sobre el modelo.

Así la fila se sostiene por lo que el software hace, y no por una remisión que no la respalda.

## Lo que NO se corrigió, y por qué

| Hallazgo | Por qué se deja |
|---|---|
| **H03** reauditar las 18 filas con cuatro estados y una tarea documentada por ítem | Es rehacer el instrumento a días de la predefensa, y la auditoría misma advierte que cambiar la regla de marcado obliga a declararlo como revisión metodológica. Lo que hacía débil la tabla era una celda, y esa celda ya está corregida |
| **H04** cotejo manual independiente de las nueve etapas | El criterio ya se había reformulado antes de esta auditoría: no se afirma reproducción manual realizada, sino desarrollo remitido a su ecuación. Un cotejo completo a mano es trabajo de días y no cambia ningún veredicto |
| **H01** reformular el problema como «diseño y evaluación» | Rompería el molde causa-efecto del tribunal. Se corrigió la respuesta y el alcance, que es donde estaba el defecto |
| **H12, H13** aislar diferencias de modelado con SAP2000 | Ya se corrigió lo esencial en la sesión anterior: la columna se rotula «diferencia» y no «error», con la razón en la leyenda |
| **H14, H16, H17, H21, H22** | Acotaciones de alcance de segundo orden. No hay tiempo infinito y su rendimiento en la defensa es bajo frente al riesgo de tocar texto ya verificado |

## Lo que queda en manos del autor

1. **La licencia del proyecto.** PyMuPDF es AGPL-3.0 o comercial, y el instalador lo distribuye
   dentro del ejecutable. Conviene decidir bajo qué licencia se publica EduFEM y declararlo en
   el repositorio. Si se prefiere una licencia permisiva, habría que sustituir PyMuPDF —se usa
   solo para mostrar los PDF de teoría dentro de la herramienta— o distribuir ese visor por
   separado. **No es un problema de la tesis, pero sí una pregunta posible en la defensa.**
2. **Los preliminares**, cuando pase de predefensa a entrega final.
3. **El Reglamento de Graduación**, del que sigue dependiendo la cita de sus artículos y si la
   carátula debe llevar tutor.

## Bibliografía: qué haría falta y qué no

El autor preguntó si conviene conseguir más fuentes. **Con lo que hay, no hace falta ninguna
para defender**. Si quisiera reforzar un punto concreto, el orden de rendimiento sería:

1. **Ninguna con más urgencia que el Reglamento de Graduación de la Carrera**, que no es
   bibliografía sino norma, y que hoy se cita desde las láminas de un taller.
2. Una fuente sobre validez de contenido en evaluación —si el tribunal insiste en el 18/18—,
   aunque el documento ya declara que es un cotejo del autor y eso basta.
3. Nada más. La bibliografía tiene 26 entradas citadas y cada una sostiene algo concreto;
   añadir más la debilita en vez de reforzarla.

## Verificación

- `latexmk -pdf main_final.tex`: EXIT 0, **187 hojas**, 0 errores, 0 `Overfull`, 0 referencias
  ni citas indefinidas, biber sin avisos.
- **26 entradas citadas**; las tres pedagógicas de la v4 siguen sin citarse, como se decidió.
- **Términos prohibidos: cero** en los capítulos del cuerpo.
- **Universo de contenido: 18 + 31 = 49**, sin repeticiones ni solapamientos. El script de
  comprobación se corrigió para leer solo la nota de exclusiones: desde hoy hay prosa vecina
  que también nombra ítems, y antes la contaba como parte de la nota.
- **Oraciones de 70 palabras o más: 14**, igual que antes de estas correcciones.
- Páginas revisadas en imagen: la de la membrana de Cook con el contraste externo (folio 85).
- Los preliminares no aparecen en el PDF: comprobado buscando «originalidad» en las primeras
  páginas.
