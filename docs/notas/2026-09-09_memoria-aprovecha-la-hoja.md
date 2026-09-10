# Memoria de Cálculo: que aproveche la hoja

**Fecha**: 2026-09-09 · **Estado**: implementado, gate verde con `--con-latex`, **sin commit**
(espera validación visual del autor).

Pedido del autor, textual:

> «Ahora enfocate en mejorar la memoria de cálculo que aproveche toda la hoja sin sobrepuestos
> de tablas datos, etc. que se ajuste para Q4 y Q9, que muestre el paso a paso pero sin
> sobrecargarla, quitá los índice o sumario del documento; debe ser algo que el usuario
> consulte para verificar sus resultados y pueda aprender del mismo.»

El canon actualizado vive en
[../convenciones/memoria-calculo.md](../convenciones/memoria-calculo.md) (§*La Memoria
aprovecha la hoja*) y las prohibiciones en
[../convenciones/no-reintroducir.md](../convenciones/no-reintroducir.md). Esta nota guarda lo
que esos dos archivos no deberían llevar: **cómo se midió** y **qué se descartó**.

## Cómo se midió

No a ojo. Un script del scratchpad genera los PDFs de 7 casos —Q4 canónico, Q9 canónico,
Cook Q9 N=4 y Cook Q9 N=32, en los estilos `educativo` y `directo`—, conserva el `.tex` y el
`.log`, y de cada PDF saca:

- **páginas**;
- **llenado vertical**: fracción de la banda de texto (entre `margen + headheight` y
  `margen + pie`) que tiene tinta. Recortar esa banda importa: medir la hoja entera daba
  108 %, porque el encabezado y el pie viven **fuera** de la caja de texto;
- **hojas flojas**: las que llenan menos del 60 %, con su número;
- **`Overfull \hbox` / `\vbox`** del `.log`, con el peor sobrante en puntos;
- **hojas apaisadas**;
- **contact sheets** de 4 páginas por PNG, para mirarlas.

Sin esa medición no se veía el problema: una memoria de 23 hojas al 84 % «parece bien» hasta
que se cuenta que 4 de esas hojas están al 30 %.

| caso | antes | después |
|---|---|---|
| Q4 educativo | 23 hojas · 84 % · 1 apaisada | **16 hojas · 96 %** |
| Q4 directo | 17 hojas · 87 % · 1 apaisada | **12 hojas · 97 %** |
| Q9 educativo | 30 hojas · 79 % · 5 overfull · 4 apaisadas | **18 hojas · 96 %** |
| Q9 directo | 25 hojas · 78 % · 5 overfull · 4 apaisadas | **14 hojas · 97 %** |
| Cook Q9 N=4 educativo | 38 hojas · 79 % · 7 overfull · 4 apaisadas | **20 hojas · 97 %** |
| Cook Q9 N=4 directo | — | **16 hojas · 96 %** |
| **Cook Q9 N=32 educativo** | **493 hojas** · 3 vbox + 1 hbox | **25 hojas · 93 %** |

En todos los casos finales: **0 hojas flojas, 0 overfull, 0 apaisadas**. Compilación de Cook
32×32: 43 s → 8 s.

La última hoja de cada documento queda fuera de la cuenta de llenado: termina donde termina el
contenido, así que medirla mide aritmética, no maquetado. Antes parecía llena, y no lo estaba:
el colofón salía con un `\vfill` que empujaba la tinta hasta el pie de una hoja casi en blanco.

## Los tres bugs que aparecieron midiendo la maquetación

Ninguno era el objetivo de la tarea; los tres rompían el uso que el autor pidió («consultar
para verificar»).

1. **La Memoria no compilaba para mallas de 11 o 12 nodos.** `_mostrar_matriz_K` emitía la K
   literal hasta 24 columnas mientras `MaxMatrixCols` estaba en 20. Verificado: una malla Q4
   de 5×1 (12 nodos, 24 GDL) **fallaba entera**; la de 4×1 (10 nodos, 20 GDL) compilaba. El
   alumno recibía un error genérico, no un PDF. Hoy el tope es `_K_LITERAL_MAX_DOF = 18` y
   `matrix_blocks` declara su propio `ensure_matrix_cols`.
2. **La tabla de recuperación imprimía ε = 0 al lado de σ ≠ 0.** `_tabla_recuperacion_showcase`
   leía `gs.get("strain", [0,0,0])` y `gauss_stresses` no tiene esa clave (tiene `eta`,
   `sigma_1`, `sigma_2`, `sigma_x`, `sigma_y`, `tau_xy`, `von_mises`, `xi`). O sea: la tabla
   titulada «recuperación ε = B·u_e → σ = D·ε» contradecía la fórmula impresa en la misma
   hoja, justo en la tabla que existe para verificar esa cadena. Hoy `_deformaciones_por_gauss`
   la recalcula y `test_recuperacion_epsilon_reproduce_sigma` verifica que `D·ε` reproduce las
   σ del solver con error relativo ≤ 1e-9.
3. **La flecha de carga se dibujaba fuera de la hoja.** Aparece mirando la portada nueva: una
   línea roja entra desde el borde superior de la figura del modelo y cruza el título. La
   flecha va **de afuera hacia el nodo**, así que la cola cae fuera del área de la malla, y
   nadie le reservaba margen: en el ejemplo canónico la cola quedaba **47 px arriba del borde**
   a 900 px de ancho, y 11 px a 560 px. O sea que existía desde antes, en el tamaño que se
   venía usando. Hoy `render_mesh_diagram` calcula la geometría de las flechas antes de armar
   la vista y se la suma al padding del borde que corresponda.

## La auditoría: cinco formas de imprimir un número equivocado

Terminada la maquetación, una auditoría multi-agente (cinco lentes independientes sobre el
diff, cada hallazgo verificado por un agente que intentaba refutarlo) buscó lo que las
métricas no ven. Encontró **cuatro bugs de gravedad alta, todos preexistentes**, en un
documento cuyo propósito declarado es verificar resultados:

1. **La verificación de equilibrio ignoraba las cargas superficiales y másicas.** Sumaba sólo
   `project.nodal_loads`, mientras que las reacciones se calculan contra el `F` del solver,
   que trae además las fuerzas equivalentes. Cualquier modelo cargado por presión de borde
   salía con «Cargas aplicadas = 0» frente a las reacciones completas: **residuo del 100 %**.
   La membrana de Cook, un ejemplo del propio menú Ayuda, recibía el veredicto rojo `Crítico`
   con un residuo real de `1e-13`.
2. **El $\kappa_2$ se medía sobre la `K` sin restricciones**, que es singular por
   construcción. Daba ~1e17 y `Crítico` en **todos** los modelos, incluido el ejemplo
   canónico, cuya `K_ff` tiene $\kappa_2 = 32{,}6$.
3. **La fila «Promedio» de la comparación nodal no es el promedio en $\sigma_{VM}$** (se
   recalcula desde las componentes ya promediadas, que es lo correcto), pero la ecuación
   inmediatamente encima dice que sí lo es: 310,06 contra 278,58.

Y una cuarta, la más difícil de ver desde el código: **la nota de las tablas recortadas
mandaba al alumno a una exportación que no tiene lo que promete**. Decía «Archivo, Exportar,
Modelo Excel/CSV» debajo de las cinco tablas topeadas, pero `export_model_csv` exporta sólo
el modelo: cero desplazamientos, cero tensiones, cero reacciones, cero métricas de calidad, y
es la única exportación del programa. El que buscaba el valor de un nodo recortado abría el
ZIP y no encontraba un solo número. Hoy el destino lo pasa quien llama (`donde=`), y cuando no
existe ninguno —puntos de Gauss, calidad de malla— la nota **no promete nada**.

Y **dos regresiones que había introducido este mismo trabajo**:

4. **`matrix_blocks(factored=True)` perdió el guardia de rango dinámico** que sí tenía
   `matrix_factored_tex`: toda entrada bajo el 0,5 % del máximo se imprimía `0.00`. En la
   `k_e` 18×18 del Q9 canónico eran **64 celdas de 324, y esa matriz no tiene un solo cero de
   verdad**. La versión apaisada anterior no tenía el problema. Ahora las tres rutas
   (`matrix_factored_tex`, `vector_factored_tex`, `matrix_blocks`) comparten
   `_decidir_formato`.
5. **La nota del extracto de vector prometía una tabla que no existe** (detrás de `F` hay un
   desglose agregado) o que viene topeada (`u`, `R`).

Lección: el llenado de hoja se puede medir con un script; que los números sean ciertos, no.
Para eso hizo falta leer el documento como lo lee un profesor, y esa es exactamente la lente
que faltaba en las siete mediciones.

## Qué se descartó

- **Bajar el cuerpo de letra** para que entre más por hoja. El documento se imprime y se
  consulta; los rótulos de las figuras ya estaban en 5,5 pt. Se ganó espacio quitando hojas
  vacías y duplicaciones, no apretando el texto.
- **Floats reales (`[ht]`) para las figuras.** Resolvían los huecos automáticamente, pero
  reordenan: la figura de la deformada podía caer **después** del encabezado del capítulo
  ⑧. En un documento que se lee como un paso a paso, el orden es el contenido. Se mantuvo
  `[H]` y se achicaron los bloques hasta que dejaron de partir hojas.
- **Grilla 2×2 de contornos en un solo bloque flotante.** Un bloque de ~420 pt que no entra
  parte la hoja y deja un hueco de 420 pt. Se emite **fila por fila**: el hueco peor es de
  media figura.
- **`needspace.sty`** para evitar encabezados viudos: no está en el bundle de TeX Live
  recortado. Hay un `\edufemNeedspace` escrito a mano en `TheoryDoc.ensure_layout_macros()`
  (ojo: **sin `%` de continuación de línea** — pylatex emite el preámbulo en UNA línea y el
  `%` comentaba el resto de la definición, lo que rompía la compilación con
  `File ended while scanning use of \@argdef`).
- **Redimensionar la imagen pre-renderizada** que puede llegar por `contour_figures=` /
  `mesh_diagram=`. Achicar los píxeles achica también las fuentes, que son absolutas: se
  volvería al problema de los 3,3 pt. `_compacta()` descarta la imagen grande y re-renderiza.
- **Reservar espacio antes de cada encabezado** (`TheoryDoc.needspace`) para que ninguno
  quede solo al pie. Implementado y medido: cuesta **tres hojas** en la Memoria Q4 educativa
  (16 → 19) y baja la tinta por hoja del 58 % al 48 %. Son ~37 encabezados y cada reserva que
  dispara vacía un pie de hoja. Revertido. (De paso quedó al descubierto un defecto del
  `\edufemNeedspace` escrito a mano: el `\addvspace` con que arranca `\section` **borra** el
  `\vskip-\dimen@` final de la macro y deja el alto reservado como blanco real. Se le agregó
  un `\penalty\@M` al cierre, que no está en `needspace.sty`, para que el skip sobreviva.)

## Trampa que conviene recordar

Las fuentes de `file_io/figure_export.py` son de **tamaño absoluto en píxeles**. El cuerpo con
que se imprime un rótulo es `13 px × ancho_pt / ancho_px`. Entonces:

- achicar el render **y** el ancho de impresión en la misma proporción **no** cambia la
  legibilidad, y ahorra alto de hoja;
- mostrar un render grande en poco ancho la arruina (920 px a 231 pt → 3,3 pt);
- una malla con más nodos necesita **más** ancho impreso, no menos: por eso el diagrama del
  modelo es chico con ≤ 40 nodos y de ancho completo por encima.

## Qué falta

- **Validación visual del autor** (ítem en [../rutina/BACKLOG.md](../rutina/BACKLOG.md),
  *Pendientes visuales*).
- Sin commit. Revertir es `git checkout` de `file_io/memoria_calculo.py`,
  `education/components/theory_builder.py`, `tests/test_memoria_calculo.py` y los tres
  archivos de `docs/`.
