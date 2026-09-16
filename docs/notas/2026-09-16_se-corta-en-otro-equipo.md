# Lo que se cortaba en otro equipo: matrices, Vista 3D y tablas de la Memoria

**Fecha**: 2026-09-16 · **Estado**: implementado, gate verde con `--con-gui`, sin commit

> Reporte del autor, con capturas tomadas en otra PC: *«no se visualiza correctamente la
> matriz B, J en el overlay», «no se visualiza el botón de la vista 3D de los resultados»* y
> *«corregí las tablas de la memoria de cálculo, la parte derecha; reducí los bordes laterales
> a 1,5 cm y acomodá sin que existan vacíos»*.

Son tres síntomas con una familia común: **medidas en píxeles fijos que sólo alcanzan en el
equipo de desarrollo**, más una causa numérica que nadie había mirado.

---

## 1. Las matrices del overlay (M2, M3)

Tres causas superpuestas, las tres medidas.

### 1a. El ruido de redondeo ensanchaba las matrices y mentía

En un elemento **rectangular** la J es diagonal, pero invertirla numéricamente deja
`7,11e-18` fuera de la diagonal, y ese ruido se propaga a `∂N_xy` y a `B`. Con `{:.3g}`, cada
cero teórico ocupaba nueve caracteres:

```
ANTES   J^-1 = [0.02  7.11e-18 ; -3.55e-19  0.0667]
        dN_xy = [3.1e-19  -2.44e-18  2.44e-18  -3.1e-19  -1.42e-18 ...]
AHORA   J^-1 = [0.02  0 ; 0  0.0667]
        dN_xy = [0  0  0  0  0  0.0254 ...]
```

No es sólo ancho: el alumno leía como valor lo que la teoría dice que es **cero**.

`config.settings.MATRIX_DISPLAY_ZERO_REL_TOL = 1e-12`, aplicado en `_matrix_to_strings`, que
es el punto único por donde pasa **toda** matriz de los overlays. El criterio es RELATIVO al
mayor módulo de la propia matriz, así que sirve igual para una B de entradas ~1e-3 que para
una k_e de ~1e6, y una matriz entera de valores chicos no se toca.

### 1b. El ancho tope estaba en píxeles de diseño

`_mat_vw()` devolvía `OVERLAY_WIDTH - 40` crudo, pero el overlay se abre con
`scaled(OVERLAY_WIDTH)`. Con el escalado de Windows al 125-150 % la matriz seguía topada en
700 px dentro de una ventana de 925-1110: se cortaba con **200-400 px de panel vacío al
lado**. Ahora hay un solo método, `CanvasOverlayModule.matrix_viewport_width()`, que calcula
el ancho REAL (escalado y recortado al área útil). M2 y M3 lo delegan; M5 lo usa para su k_e.

| escalado | tope antes | tope ahora |
|---|---|---|
| 100 % | 700 px | 700 px (sin cambio) |
| 125 % | 700 px | **875 px** |
| 150 % | 700 px | **1050 px** |

### 1c. El overlay se recortaba por abajo y no había forma de ver el resto

El alto sale del contenido y `_tamano_final` lo recorta al área útil. Medido en un escritorio
de **1280x600**: M2 perdía 76 px y M3, 61 — justo donde viven la J y la B. No había scroll:
ese contenido era inalcanzable.

Ahora el body de `CanvasOverlay` vive dentro de un canvas desplazable. Para los ocho módulos
no cambia nada (siguen empaquetando en `self.body`). La rueda sobre cualquier punto del
overlay desplaza el body y **sigue cortando la propagación**, que es lo que evita el zoom
accidental de la MeshCanvas y el cuelgue del `FigureCanvasTkAgg` de la regla de oro #3.
Verificado: en 1280x600, M2 y M3 alcanzan ahora el 100 % de su contenido con la rueda.

### Lo que queda

La **B de Q9 es 3x18**: aun con los ceros limpios mide ~1500 px y no entra en un panel de 720
a fuente legible. Sigue siendo `ScrollableMatrixImage` —decisión previa, `force_scroll=True`—
con cursor de arrastre y tooltip; lo que cambió es que ahora se ve bastante más de golpe en
pantallas escaladas. Si el autor prefiere, la alternativa sería partirla en dos bloques de 9
columnas, como hace la Memoria con `matrix_blocks`.

---

## 2. El botón de la Vista 3D

**Violación directa de la regla dura 23**: `surface_3d_viewer._build_ui` empaquetaba el
`footer` —modos Crudo/Suavizado, los dos interruptores y el botón **Cerrar**— DESPUÉS del
cuerpo elástico.

Tk le quita espacio a lo último empaquetado, y el `FigureCanvasTkAgg` pide **siempre** más de
lo que tiene: el backend Tk de matplotlib multiplica su tamaño por el *device pixel ratio*, así
que al 150 % un lienzo que ocupa 1350 px declara pedir 2001. Todo ese exceso se descontaba del
pie.

Reproducido y medido, con el código original:

| área útil | alto del pie |
|---|---|
| 1896x1016 | 56 px (se ve) |
| 1366x728 | 56 px (se ve) |
| **1280x600** | **1 px — el alumno no ve ningún control** |
| **1024x600** | **1 px** |

Con `footer.pack(side=BOTTOM)` **antes** del body: 56 px en las cuatro. Lo que se encoge es el
gráfico, que es elástico y se redibuja.

La misma auditoría (script AST sobre `gui/` y `education/`) encontró otros tres casos de la
familia, también corregidos: `dxf_import_dialog` (botones Cancelar/Importar),
`material_dialog._build_list_panel` (Nuevo/Eliminar) y la ventana del integrando completo de
M5 (su pie informativo).

### Por qué el gate no lo agarraba

Dos fallas del propio test, las dos arregladas:

1. **`PANTALLAS` no bajaba de 728 px de alto.** El bug necesita ~600. Se agregó
   `("1280x720 con 600 px utiles de alto", 1280, 600, None)`.
2. **`barras_de_botones` exigía que TODOS los hijos fueran `Button`.** El pie de la Vista 3D
   tiene rótulo, radios, separador y checks, así que no lo detectaba ninguno. Peor: la lectura
   de los rótulos iba en un solo `try`, y la `TclError` de `ttk.Separator` (que no tiene
   opción `text`) saltaba el `continue` y se llevaba puesta la comprobación **entera** de la
   barra — en silencio.

Comprobado que el test ahora **falla** con el archivo original de git y **pasa** con el
arreglo.

---

## 3. Las tablas de la Memoria

Medido con `pdflatex` contando `Overfull \hbox` (el compilador ya lo denunciaba; nadie miraba
el log). Las dos tablas de las capturas son la de tensiones por punto de Gauss (8 columnas) y
la de tensiones nodales (7).

| | antes | con márgenes 1,5 cm | + encabezado apilado |
|---|---|---|---|
| peor desborde | 89,9 pt | 50,0 pt | **0** |

- **Márgenes laterales a 1,5 cm**, como pidió el autor: `MemoriaCalculo.MARGEN_LATERAL`, que
  `TheoryDoc` recibe como parámetro. El default de `TheoryDoc` sigue en 2,2 cm para la Teoría,
  que es prosa y quiere un renglón de ~80 caracteres. Aporta 40 pt.
- **La unidad va apilada bajo el símbolo** (`_th_unidad` → `\shortstack`). Era el arreglo
  decisivo: seis columnas repitiendo `[kgf/cm²]`, tres veces más ancho que el `$\sigma_x$` que
  rotulan. Apilada, la columna mide lo que mide la unidad, y el rótulo no se pierde porque el
  encabezado es lo que `longtable` repite en cada hoja. Se aplicó a **todas** las tablas con
  unidad, también donde no hacía falta por ancho: dos formatos conviviendo en la misma hoja se
  ven como un descuido.
- **Sin huecos**: `Underfull \vbox` = 0 y el conteo de hojas no cambió (23 en Timoshenko Q9).

### Un desborde que nadie había visto: 566 pt

El barrido por los seis ejemplos destapó que en los modelos **Q4** la entrada simbólica
`K_11(ξ,η)` se imprimía **566,2 pt fuera de la hoja**, dentro de un `equation*` que no admite
corte de línea: texto sencillamente invisible. Misma causa que 1a — el ruido
(`1,07e-13·η - 750,0`) le impedía a sympy plegar los paréntesis. `fem.symbolic_integrand.
podar_ruido` lo elimina y `sp.N(expr, 6)` recorta los 15 dígitos:

```
ANTES  659 caracteres de LaTeX, ilegibles y fuera de la hoja
AHORA   86 caracteres:  K_11 = 164835·(η−1)² + 641025·(ξ−1)²
```

### Barrido final

6 modelos de ejemplo × 2 estilos = 12 documentos: **0 tablas o fórmulas fuera de la hoja, 0
huecos verticales**.

### Trampa

El desborde **depende del sistema de unidades**: con `MPa` el encabezado entraba, con
`kgf/cm²` no. El ejemplo canónico nunca lo habría mostrado — por eso el guard nuevo,
`test_nada_se_sale_de_la_hoja`, usa Timoshenko Q9. Comprobado que falla (8 cajas, la peor de
50 pt) si se vuelve al encabezado en línea.

---

## Qué mirar en la GUI

1. **M3 (Ctrl+3) sobre un Q9**, pestaña *Valores*, moviendo el punto a un PG: la `J⁻¹` tiene
   que decir `0` donde antes decía `7.11e-18`, y `∂N_xy` entrar entera.
2. **Overlay en una pantalla chica**: `set EDUFEM_AREA_UTIL=1280x600 && python main.py`, abrir
   M2 y girar la rueda sobre el panel — tiene que desplazarse hasta la última fila.
3. **Vista 3D** en el Post: la barra de modos y el botón Cerrar, presentes.
4. **Memoria de Cálculo en PDF** de un modelo en kgf/cm²: las dos tablas de tensiones
   completas, con la unidad debajo del símbolo.
