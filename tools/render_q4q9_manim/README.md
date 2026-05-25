# Pipeline cantilever Q4 vs Q9 — Manim

Genera el video comparativo Q4 vs Q9 para el diálogo `🔲 Tipo de
Elemento` de EduFEM. Reemplaza al pipeline anterior
[`tools/render_q4q9/`](../render_q4q9/) (Claude Design + Chrome
headless + DevTools Protocol), unificándose con el de TPvsDP
([`tools/render_tp_dp_manim/`](../render_tp_dp_manim/)) en un único
runtime (manim).

## Por qué Manim (no Claude Design + Chrome)

- Pipeline más simple: 1 sola conversión ffmpeg vs el Chrome+CDP+ffmpeg
  del render_q4q9 original.
- Output determinístico — frame N siempre se ve igual entre corridas.
- Reusa el mismo entorno Manim que TPvsDP — un solo set de
  dependencias para los dos videos.
- Coherencia visual: misma paleta, mismo layout 2 columnas con
  separadores, misma estrategia de loop seamless.

## Requisitos

- Python con manim instalado (`pip install manim`)
- ffmpeg en el PATH (manim lo trae como dependencia)
- LaTeX (recomendado, para `\delta_{\text{TEÓRICA}}` y el `DecimalNumber`
  del contador). Sin LaTeX, `MathTex` cae a su renderer interno con
  resultado aceptable.

## Renderizar

Desde esta carpeta:

```bash
manim -qh q4_vs_q9.py Q4vsQ9
```

Flags:
- `-q h` = quality high (resolución final 1920×1080 por default)
- `-q l` = quality low (480×270, para iterar rápido)

El script forza la resolución final a 900×600 @ 22 fps vía `config.*`
en el header, sin importar el flag de quality.

Salida: `media/videos/q4_vs_q9/<calidad>/Q4vsQ9.mp4`

## Convertir a WebP animado (para el diálogo)

```bash
ffmpeg -i media/videos/q4_vs_q9/600p22/Q4vsQ9.mp4 \
       -vcodec libwebp \
       -filter:v "fps=22,scale=900:600:flags=lanczos" \
       -lossless 0 \
       -compression_level 6 \
       -q:v 75 \
       -loop 0 \
       -an \
       -vsync 0 \
       ../../resources/videos/cantilever_q4_q9.webp
```

Tamaño esperado: ~0.5 – 1.2 MB para 4s @ 22fps a 900×600.

## Anatomía del script

`q4_vs_q9.py` contiene una única clase `Q4vsQ9(Scene)`. Métodos:

| Método | Qué hace |
|---|---|
| `construct()` | Orquestador del timeline (~4s, 5 segmentos). |
| `_build_layout()` | Separadores, títulos de columna, labels `δ/δ_TEÓRICA`. |
| `_build_cantilever(side, element_type)` | Cantilever completo: cuerpo + nodos + soporte + carga + ratio_value. |
| `_subdivided_rect(...)` | Polygon con aristas horizontales subdivididas (necesario para que `apply_function` curve la silueta). |
| `_make_internal_lines(...)` | Líneas verticales que separan elementos (también subdivididas). |
| `_make_nodes(...)` | Q4: 4 corners/elem. Q9: 9 nodos/elem (corners más grandes que mids). |
| `_make_fixed_support(...)` | Pared vertical + hatching diagonal -45° (convención Resmat). |

### Deformación FEM real (no Bernoulli analítico continuo)

El video muestra **dos diferencias simultáneas** entre Q4 y Q9, ambas
visibles a simple vista:

**(1) Carácter de la silueta — viene de las shape functions del FEM:**

Las nodal displacements se computan con el perfil analítico de
Bernoulli `δ(s) = s²(3-s)/2` evaluado en cada nodo, pero la
interpolación DENTRO de cada elemento usa las shape functions reales
del FEM (no la analítica continua):

- **Q4 (bilineal)**: `N1(ξ) = 1-ξ`, `N2(ξ) = ξ` → interpolación
  **LINEAR** entre los 2 nodos en x del elemento. La silueta deformada
  es una **polilínea**: 4 segmentos rectos con **kinks** (saltos de
  pendiente) en las 3 fronteras interiores. En `s=0.25` la pendiente
  cambia ~2.6× (de 0.34 a 0.91) — el quiebre es el síntoma visual
  del elemento Q4 bajo flexión pura.

- **Q9 (bicuadrático)**: `L1(ξ) = -ξ(1-ξ)/2`, `L2(ξ) = 1-ξ²`,
  `L3(ξ) = ξ(1+ξ)/2` → interpolación **CUADRÁTICA** Lagrange entre
  los 3 nodos en x del elemento (izq + medio + der). La silueta es
  una sucesión de parábolas que en este caso pegan con **continuidad
  C1** entre elementos → curva **suave** sin kinks visibles.

**(2) Magnitud de la deflexión — viene del ratio FEM/analítica:**

- Q4: `MAX_TIP_DEFLECTION_Q4 = ANALITICO · 0.62` (shear locking).
- Q9: `MAX_TIP_DEFLECTION_Q9 = ANALITICO · 0.99` (casi exacto).

La punta del Q4 termina visiblemente más arriba que la del Q9.

Las dos diferencias en simultáneo son la pedagogía. **Si solo se
escalara magnitud (Q4 y Q9 ambos con el mismo perfil analítico
continuo), se perdería el mensaje visual del carácter — el alumno
no vería por qué Q4 es "menos preciso".**

Implementación en `_make_fem_bend(base_x, n_elements, max_tip_norm,
element_type)`. La subdivisión `N_SUB_HORIZONTAL=24` da 6 segmentos
por elemento — suficiente para visualizar la polilínea de Q4 y las
parábolas de Q9 sin oversampling.

### Counter `δ/δ_TEÓRICA`

Cada columna tiene un `DecimalNumber` bound a un `ValueTracker`:

```python
tracker = ValueTracker(0.0)
ratio_value = DecimalNumber(0.00, num_decimal_places=2, color=...)
ratio_value.add_updater(lambda m: m.set_value(tracker.get_value()))
self.play(tracker.animate.set_value(RATIO_FINAL), ...)
```

Color semántico:
- Q4 ratio en **naranja** (warning): subestima la analítica → ratio < 1.
- Q9 ratio en **verde** (success): captura casi exactamente → ratio ≈ 1.

### Loop seamless

Frame 0 = layout estático (títulos + separadores + labels
`δ/δ_TEÓRICA`). El cantilever, soporte, ratio_value y load son
opacity 0 al inicio (`dynamic_group.set_opacity(0)`).

El bloque final del `construct()` hace `FadeOut` de TODO lo dinámico:
- `dynamic_group` (cantilever + soporte + ratio_value) → opacity 0.
- `load_arrow` + `load_label` (FadeOut explícito porque viven fuera
  del `dynamic_group`).
- `tracker` baja a 0.0 → el `DecimalNumber` muestra "0.00".

El frame 110 (último) se ve idéntico al frame 0 → loop sin "salto".

### Anti-superposición

- Q4 ocupa `x ∈ [-5.2, -0.8]`, Q9 ocupa `x ∈ [0.8, 5.2]`.
- Separador vertical en `x = 0` divide las dos columnas.
- Banda superior (`y > 3.0`) exclusiva de los títulos.
- Banda inferior (`y < -3.0`) exclusiva de los labels `δ/δ_TEÓRICA` y
  el `DecimalNumber`.
- La carga `P` arranca afuera de la columna del cantilever y entra
  hasta la punta vía `GrowArrow` — nunca atraviesa elementos.

### Por qué NO hay texto explicativo en la animación

La justificación textual (qué es shear locking, por qué Q4 subestima,
qué es un elemento bicuadrático) NO debe vivir en el video — el
diálogo `ElementTypeDialog` lleva el hint operacional ("En Q9, los 5
nodos internos se generan automáticamente"). El video se enfoca en
mostrar el **resultado físico** (cuánto deflecta cada uno) y los
**números clave** (DOF por elemento y ratio `δ/δ_TEÓRICA`).

## Después del .webp

`ElementTypeDialog` en
[`gui/dialogs/element_type_dialog.py`](../../gui/dialogs/element_type_dialog.py)
apunta directamente a `resources/videos/cantilever_q4_q9.webp` —
reemplazar el archivo es suficiente, no hay que tocar código GUI.
