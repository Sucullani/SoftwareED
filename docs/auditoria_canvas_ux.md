# Auditoría UX/UI del Canvas FEM — EduFEM

> Auditoría ejecutada el 2026-05-30 sobre `gui/preprocessing/mesh_canvas.py` (3.667 líneas).
> Perspectiva: Senior FEM Software Engineer + UX Designer + CAD Systems Architect.
> Usuario objetivo: estudiante / ingeniero trabajando con mallas Q4 / Q9.
> Benchmarks de referencia: Abaqus/CAE, ANSYS Mechanical, HyperMesh, GiD, SAP2000, ETABS, Robot Structural, COMSOL.

---

## Resumen ejecutivo

El canvas de EduFEM tiene una **base de rendering sólida y sofisticada** para ser un proyecto educativo en tkinter:
rasterizado Gouraud con Numba (`_rasterize_triangle_njit`, 15–30× sobre NumPy), marching squares JIT, caché de bitmap PIL
reutilizado en pan/zoom vía `canvas.move`/`canvas.scale` en C, y un *interaction mode* que difiere el redibujado pesado 150 ms.
El motor de pintado **no es el problema**.

El problema es la **política de visibilidad**: el canvas opera con un único nivel de detalle, "todo encendido, todo el tiempo".
Concretamente, los defaults son:

```python
# mesh_canvas.py:348-351
self.show_node_labels = True   # ← TODOS los IDs de nodo, siempre
self.show_elem_labels = True   # ← TODOS los IDs de elemento, siempre
self.show_loads = True
self.show_constraints = True
```

No existe ningún gating por zoom (LOD), ni distinción entre "elemento de interés" y "contexto", ni toggle en la toolbar
para apagar la numeración (la búsqueda en `gui/` fuera de `mesh_canvas.py` no encontró ningún control de UI que toque
estos flags). El resultado es exactamente el cuadro que describís: en una malla Q9 de tamaño medio el canvas crea
**6.000–12.000 ítems Tk**, la mayoría texto, y la selección —un simple cambio de color a amarillo `#ffeb3b` sin halo ni
realce de grosor— se pierde en ese ruido.

La tesis de esta auditoría: **el 80 % de la mejora percibida se obtiene con dos cambios de política de visibilidad
(LOD por zoom + numeración bajo demanda) y un rediseño del realce de selección, sin tocar el motor de rasterizado.**

---

## A. Diagnóstico UX/UI

Clasificación por severidad. Cada ítem incluye causa raíz (anclada a código), impacto, frecuencia y prioridad.

### A.1 Visualización geométrica

| # | Problema | Severidad | Causa raíz | Impacto | Frecuencia | Prioridad |
|---|---|---|---|---|---|---|
| G1 | **Todos los IDs de nodo visibles permanentemente** | **Crítico** | `show_node_labels = True` por default (`:348`); `_draw_nodes` crea 1 `create_text` por nodo (`:1336-1347`) sin condición de zoom | En Q9 los mid-nodes triplican el conteo; los números se solapan entre sí y tapan aristas. La malla deja de leerse a partir de ~50 nodos | Siempre (default) | **P0** |
| G2 | **Todos los IDs de elemento visibles permanentemente** | **Alto** | `show_elem_labels = True` (`:349`); 1 `create_text` por elemento en el centroide (`:1256-1266`) | El número en el centro compite con el campo de color del resultado y con las cruces principales del post | Siempre (default) | **P0** |
| G3 | **Todos los nodos dibujados como doble óvalo, sin LOD** | **Alto** | `_draw_nodes` dibuja 2 óvalos por nodo (outer+inner, `:1316-1333`) para *todos* los nodos a cualquier zoom | A zoom lejano los nodos se funden en una masa de puntos; 2 ítems × N nodos infla el árbol Tk sin aportar lectura | Siempre | **P1** |
| G4 | **Mid/center nodes Q9 con el mismo peso visual que corners** | **Medio** | Distinción solo por color/radio (`CANVAS_NODE_MID_COLOR`, radio 3 vs 4) pero siempre presentes | El alumno no distingue la malla macro (lo que importa pedagógicamente) del andamiaje Q9 | Siempre en Q9 | **P1** |
| G5 | **Grid siempre visible compitiendo con la geometría** | **Bajo** | `_draw_grid` incondicional (`:622`) | Ruido de fondo de baja prioridad que resta contraste a aristas | Siempre | **P3** |
| G6 | **Aristas de elemento sin diferenciar contorno-de-malla vs interior** | **Medio** | `_draw_elements` pinta todas las aristas igual (`CANVAS_ELEMENT_COLOR`, width 1.5, `:1234-1246`) | El borde exterior del dominio (la "silueta" del modelo, clave en CAE) no resalta sobre las aristas internas | Siempre | **P2** |

### A.2 Interacción

| # | Problema | Severidad | Causa raíz | Impacto | Frecuencia | Prioridad |
|---|---|---|---|---|---|---|
| I1 | **Selección débil: solo color-swap, sin halo ni grosor** | **Crítico** | `_draw_highlight()` está intencionalmente vacío salvo aristas (`:1595-1620`); nodo/elem solo cambian a amarillo (`:1314`, `:1243`) | En malla grande un nodo amarillo entre 2.000 nodos azules es casi invisible; el elemento seleccionado (outline width 2 vs 1.5) apenas se distingue | Cada selección | **P0** |
| I2 | **Sin estado hover visual** | **Alto** | `<Motion>` (`:497`) solo actualiza coords y dispara callback de M0 (`:1982-2016`); no hay realce de pre-selección | El usuario no sabe qué va a seleccionar antes de hacer click → clicks erróneos, prueba y error | Cada movimiento de mouse | **P1** |
| I3 | **No hay LOD por zoom** | **Crítico** | Zoom (`:1868-1913`) escala ítems con `canvas.scale` pero nunca cambia *qué* se dibuja; no hay umbral de zoom | Hacer zoom no "limpia" la vista lejana ni "revela" detalle de cerca — el ruido es constante a toda escala | Siempre | **P0** |
| I4 | **Numeración no responde a la acción del usuario** | **Alto** | Labels gobernados por flags globales, no por selección ni por zoom | No se puede "ver solo el ID del elemento que estoy inspeccionando" — patrón estándar en Abaqus (query) | Siempre | **P1** |
| I5 | **Redibujado completo `delete("all")` en cada `redraw()`** | **Medio** | `:621` borra y recrea todos los ítems | Mitigado por interaction-mode, pero cada cambio de selección reconstruye 10.000 ítems → micro-lag perceptible en mallas grandes | Cada cambio de estado | **P2** |
| I6 | **Pan en botón central/derecho, no estándar** | **Bajo** | Pan en Button-2/3 (`:1915`) | Convención mixta; CAE usa MMB-drag (ok) pero el usuario novato espera barra espaciadora o MMB | Ocasional | **P3** |

### A.3 Resultados

| # | Problema | Severidad | Causa raíz | Impacto | Frecuencia | Prioridad |
|---|---|---|---|---|---|---|
| R1 | **Colormap JET en el canvas** | **Alto** | JET inline en el kernel Numba (`:237-252`) y en `_draw_colorbar` | JET no es perceptualmente uniforme: crea bandas falsas (el amarillo aparenta un máximo donde no lo hay), problema documentado en visualización científica. Contradice la regla de `config/settings.py` (viridis/coolwarm) que el resto del proyecto sí respeta | Cada post-proceso | **P1** |
| R2 | **Labels de resultado sobreimpresos en cada nodo** | **Alto** | Cuando `result_values` está poblado, el label de nodo pasa a `"{nid}: {valor}"` (`:1336-1341`) | En post-proceso cada nodo muestra `id: valor`, saturando completamente el campo de color que es lo que hay que leer | Cada post con labels on | **P0** (se resuelve con G1) |
| R3 | **Isolíneas sin etiqueta de nivel** | **Medio** | `_draw_isolines` dibuja líneas blancas width 1.2 sin rótulo de valor (`:1206-1211`) | El usuario ve curvas pero no sabe a qué valor corresponde cada una (en GiD/COMSOL cada isolínea lleva su valor) | Cuando isolíneas on | **P2** |
| R4 | **Deformada y campo compiten sin control de opacidad** | **Medio** | Ghost + gradiente + deformada se apilan sin transparencia regulable | Difícil separar "forma deformada" de "campo de tensión" | Post con deformada | **P2** |
| R5 | **Cruces principales / contorno / numeración sin jerarquía** | **Alto** | Capas dibujadas en orden fijo sin atenuación contextual | Todo a máximo contraste → el ojo no sabe dónde mirar | Post avanzado | **P1** |

### A.4 Causa raíz transversal

Las tres causas raíz que explican casi todos los síntomas:

1. **Modelo de visibilidad binario y global** (flags `show_*` true/false para *toda* la malla) en lugar de un modelo
   **contextual** (visible según zoom + según selección + según fase).
2. **Realce de selección por sustitución de un atributo** (color) en vez de por **adición de una capa de énfasis**
   (halo/glow/atenuación del resto) — el estándar CAD.
3. **Ausencia de un concepto de "foco"**: el canvas no tiene noción de "esto es lo que el usuario está mirando ahora",
   así que no puede degradar el contexto para resaltarlo.

---

## B. Reducción de ruido visual — estrategia de visualización progresiva

### B.1 Principio rector

> *Mostrar lo mínimo necesario para la tarea actual; revelar detalle bajo demanda (zoom, selección, query).*
> Es el principio de **"detail-on-demand"** de Shneiderman ("Overview first, zoom and filter, then details-on-demand"),
> que Abaqus, COMSOL y HyperMesh aplican religiosamente.

### B.2 Niveles de detalle (LOD) por zoom

Definir tres bandas de zoom usando `self.scale` (px por unidad-mundo). Calcular dinámicamente un **px-por-arista-media**
(no `scale` absoluto, para que sea independiente de las unidades del modelo):

```
edge_px = mediana(longitud de arista en mundo) * self.scale
```

| Banda | Condición | Geometría | Nodos | Numeración | Puntos Gauss |
|---|---|---|---|---|---|
| **Lejano** (overview) | `edge_px < 14 px` | Solo silueta del dominio + campo de color. Aristas internas atenuadas | Ocultos (o 1 px sin halo) | Ninguna | No |
| **Medio** (navegación) | `14 ≤ edge_px < 60 px` | Todas las aristas. Corners sólidos | Corners visibles; mid/center Q9 atenuados o puntuales | Solo del elemento **seleccionado** | No |
| **Cercano** (inspección) | `edge_px ≥ 60 px` | Aristas + relleno | Todos los nodos con su rol cromático | IDs de nodo y elemento **visibles** (auto) + IDs del seleccionado siempre | Puntos de integración del elemento bajo cursor |

Implementación: una sola función `self._lod_level()` que devuelve `"far"|"mid"|"near"` consultada por `_draw_nodes`,
`_draw_elements`, `_draw_grid`. **Cero costo nuevo de rasterizado** — solo decide cuántos `create_text`/`create_oval` emitir.
Como el cuello de botella en mallas grandes es precisamente la cantidad de ítems Tk de texto, este gating **mejora también
el rendimiento** (ítem E).

### B.3 Numeración bajo demanda (independiente del LOD)

Reemplazar los dos flags globales por una política de tres capas:

1. **Default = OFF.** `show_node_labels = False`, `show_elem_labels = False` al iniciar. (Hoy están en `True`, ese es el
   cambio de una línea de mayor impacto de toda la auditoría.)
2. **Auto por zoom:** en banda *cercano* se muestran automáticamente (LOD).
3. **Por selección (siempre, a cualquier zoom):** el o los ítems seleccionados muestran su ID aunque la numeración global
   esté apagada — patrón "query" de Abaqus. Esto convierte la numeración en una herramienta de inspección puntual, no en
   ruido permanente.
4. **Toggle manual en toolbar** (override): tres estados `Auto / Siempre / Nunca` para nodos y para elementos, persistido
   en el canvas. El usuario avanzado fuerza, el novato confía en el auto.

### B.4 Estrategia recomendada (síntesis)

**LOD por zoom + numeración auto/selección/manual**, con default OFF. Es la combinación que (a) elimina el ruido de
arranque, (b) escala a mallas grandes sin que el usuario haga nada, (c) preserva el control del experto, y (d) tiene un
costo de implementación bajo porque se apoya en los flags y métodos que ya existen — solo cambia *cuándo* se evalúan.

---

## C. Sistema de selección profesional

### C.1 Estados y su especificación visual

El estándar CAD/CAE separa **selección** (qué color/forma) de **énfasis** (cómo se destaca del resto). EduFEM hoy solo
hace lo primero. Propuesta de máquina de 7 estados:

| Estado | Color recomendado | Grosor línea | Transparencia | Halo / Glow | Prioridad visual | Notas |
|---|---|---|---|---|---|---|
| **Normal** | `CANVAS_ELEMENT_COLOR` / rol del nodo | 1.5 px | 0 % | No | Base | Sin cambios |
| **Hover** (pre-selección) | `CANVAS_HOVER_COLOR` (nuevo, cian claro `#8be9fd`) | 2.0 px | 0 % | Halo fino 2 px, semitransp. | Media | Aparece solo bajo cursor; feedback de "esto seleccionarías" |
| **Selected** | `CANVAS_SELECTED_COLOR` `#ffeb3b` | **2.5 px** | 0 % | **Halo exterior 4–5 px** en amarillo translúcido | **Máxima** | Halo = clave para verlo en malla grande |
| **Multi-selected** | mismo amarillo | 2.5 px | 0 % | Halo + **atenuación del NO-seleccionado** (ver C.3) | Máxima colectiva | El conjunto destaca por contraste contra contexto apagado |
| **Locked** | gris `#6c757d` | 1.5 px | 40 % | No, candado opcional | Baja | No seleccionable; útil para fijar geometría de referencia |
| **Hidden** | — | — | 100 % | — | Nula | No se dibuja (no solo atenuado): clave para aislar regiones |
| **Editing** | naranja `PHASE_PROC_COLOR` | 2.5 px | 0 % | Halo pulsante naranja (~2 Hz) | Máxima exclusiva | Mientras se arrastra un nodo / se dibuja un elemento |

### C.2 Cómo simular el halo en tkinter (sin alpha real)

`tk.Canvas` no soporta alpha en vectores, pero el proyecto **ya** simula glow apilando líneas (`_draw_loads` usa 2
`create_line`, una `width+3` con color sombra debajo). Aplicar la misma técnica a la selección:

```python
# Halo de selección: línea ancha tenue DEBAJO + línea de selección nítida ENCIMA
# (mismo patrón que el glow de cargas, ya presente en el código)
self.canvas.create_line(pts, width=6, fill=CANVAS_SELECTED_HALO, capstyle=ROUND, tags=...)
self.canvas.create_line(pts, width=2.5, fill=CANVAS_SELECTED_COLOR, capstyle=ROUND, tags=...)
```

Para nodos: óvalo exterior extra de radio `r+4` en amarillo translúcido (color pre-mezclado con el fondo vía `lerp_hex`,
helper que ya existe en `gauss_glyph.py`). Costo: +1 ítem por *ítem seleccionado* (no por ítem total) → despreciable.

### C.3 La técnica decisiva: **atenuar el contexto, no solo resaltar el target**

El motivo por el que en Abaqus/HyperMesh un elemento seleccionado "salta" aunque haya 100.000 elementos no es el color del
target — es que **todo lo demás baja de intensidad**. EduFEM ya tiene la infraestructura exacta para esto: el modo
`ghost_geometry` (`MeshCanvas.ghost_geometry`, usado por M0) que dibuja toda la malla en `CANVAS_GHOST_COLOR` tenue.

Propuesta: un modo **`focus_mode`** que, cuando hay selección activa, dibuja:
- el/los ítems seleccionados + sus vecinos inmediatos a intensidad plena con halo,
- **el resto de la malla atenuado** (mismo mecanismo que ghost, pero conservando el campo de color del post a media opacidad).

Esto resuelve I1 de raíz: la selección destaca por **diferencia de contraste con el fondo**, que es robusta a cualquier
tamaño de malla, en lugar de por un color que se diluye estadísticamente.

---

## D. Arquitectura visual FEM — jerarquía recomendada

Orden de dominancia visual (1 = domina, 8 = fondo). La regla: **en cada momento solo UN nivel debe estar en máximo
contraste; el resto se subordina según contexto.**

| Nivel | Capa | Tratamiento en estado "inspección" | Tratamiento cuando NO es el foco |
|---|---|---|---|
| **1** | **Elemento/nodo seleccionado** | Amarillo + halo + ID + Gauss + grosor 2.5 | n/a (es el foco) |
| **2** | **Elementos vecinos del seleccionado** | Aristas a intensidad plena, sin label | Atenuados con el resto |
| **3** | **Restricciones y cargas** (condiciones de contorno) | Símbolos a contraste medio-alto, color semántico | Reducir a 50 % opacidad simulada en focus_mode |
| **4** | **Geometría principal** (silueta del dominio + aristas) | Aristas internas medias, **borde exterior realzado** | Atenuada (ghost) en focus_mode |
| **5** | **Campo de resultados** (contorno de color) | Fondo legible, colormap perceptual | Media opacidad bajo la selección |
| **6** | **Malla fina** (mid/center Q9, subdivisión) | Solo en zoom cercano | Oculta en zoom lejano/medio |
| **7** | **Numeración** | Bajo demanda (LOD/selección) | Oculta |
| **8** | **Auxiliares** (grid, ejes, info) | Tenue, screen-anchored | Grid se desvanece en zoom lejano |

**Qué debe dominar:** la condición de contorno (cargas/restricciones) y la silueta del dominio son lo que define el
*problema* FEM — deben ser legibles siempre. **Qué va al fondo:** grid, numeración global y el andamiaje Q9. La regla de
oro CAE: *las cargas y restricciones nunca deben perderse bajo el campo de color* — hoy en EduFEM compiten al mismo nivel.

---

## E. Optimización de rendimiento

### E.1 Estado actual (medido por arquitectura, no profiling — recomendar `cProfile` real)

Lo que el código **ya hace bien** (no tocar):
- **Rasterizado Gouraud con Numba** `_rasterize_triangle_njit` (`:179-257`): per-pixel barycentric + JET inline, 15–30×.
- **Caché de bitmap PIL** reutilizado en pan (`canvas.move` en C) y zoom (`Image.resize` NEAREST ~5–10 ms).
- **Interaction-mode** que difiere isolíneas + redibujado pesado 150 ms (`_schedule_interaction_end`).
- **Marching squares JIT** (`:52-151`).
- **Clasificación de nodos cacheada una vez por frame** (`:642-643`).

### E.2 Cuello de botella real: cantidad de ítems Tk (no el rasterizado)

| Malla | Elem | Nodos Q9 aprox | Ítems Tk con defaults actuales | Síntoma |
|---|---|---|---|---|
| **100 elem** | 100 | ~450 | ~2.000 | Fluido |
| **1.000 elem** | 1.000 | ~4.000 | ~18.000 | `delete("all")`+recrear perceptible (~100–200 ms por redraw) en cada selección |
| **10.000 elem** | 10.000 | ~40.000 | ~180.000 | Inusable: cada redraw segundos; el árbol de ítems Tk es el límite duro |
| **100.000 elem** | 100.000 | ~400.000 | >1.8 M | Imposible con ítems vectoriales Tk |

El rasterizado es O(píxeles del viewport) → **constante** respecto al tamaño de malla. El que explota es el **número de
ítems vectoriales** (óvalos de nodo + textos), que es O(nodos). Por eso **el LOD del ítem B no es solo UX, es la principal
palanca de rendimiento**: ocultar labels y nodos en zoom lejano recorta el árbol Tk de decenas de miles a cientos.

### E.3 Soluciones por escala

1. **100–1.000 elem (cubre el 95 % del caso educativo):**
   - Aplicar LOD (ítem B): elimina labels en lejano/medio → árbol Tk 5–10× menor.
   - **Render incremental de selección:** en vez de `delete("all")` al cambiar selección, mantener tags estables y solo
     reconfigurar los ítems afectados (`itemconfig` sobre el tag del ítem viejo y nuevo seleccionado). Hoy `_emit_selection_changed`
     fuerza redraw completo; un `_restyle_selection(old, new)` que toque ~4 ítems elimina el micro-lag (I5).

2. **1.000–10.000 elem:**
   - **Rasterizar también nodos y aristas en el bitmap PIL** cuando `edge_px < umbral`: dibujar la malla como parte de la
     imagen (ya se rasteriza el campo; agregar wireframe al mismo bitmap) en lugar de miles de óvalos vectoriales. Los
     nodos vectoriales solo aparecen en zoom cercano sobre la región visible.
   - **Culling por viewport:** dibujar solo ítems cuyo bbox intersecta el área visible (+ padding). Hoy se itera *toda* la
     malla aunque el 90 % esté fuera de pantalla. Un índice espacial simple (grid hashing) acota a O(visibles).

3. **10.000–100.000 elem (fuera del alcance educativo, pero por completitud):**
   - El modelo de ítems vectoriales Tk no escala. La vía es **render a un único bitmap** (canvas como image-blit puro) y
     hit-testing por estructura espacial en mundo, no por ítems Tk. Es un reescritura del backend; no recomendada salvo que
     el proyecto apunte a mallas de producción.

### E.4 Prácticas modernas a adoptar

- **Dirty-region / restyle incremental** para cambios de selección (no `delete("all")`).
- **Viewport culling** con índice espacial (grid hash) — barato y de alto impacto.
- **LOD como primera línea de defensa de rendimiento** (no solo de estética).
- **Desacoplar "datos" de "ítems Tk"**: mantener un mapa `id → item_handle` para `itemconfig` quirúrgico.
- **Profiling antes de optimizar** (regla ya en `CLAUDE.md`): `cProfile` sobre redraw de 1.000 elem confirmará que el
  costo está en `create_text`/`create_oval`, no en el rasterizado.

---

## F. Colormap y legibilidad de resultados (complemento de A.3)

- **Migrar el canvas de JET a un colormap perceptualmente uniforme.** El resto del proyecto ya usa viridis/coolwarm
  (`CLAUDE.md` lo exige para matplotlib y la memoria). El canvas es la excepción (JET inline en el kernel Numba). Sugerido:
  **viridis** para magnitudes no negativas (σ von Mises) y **coolwarm** (divergente, cero físico) para σx/σy/τxy. Requiere
  reemplazar las ~15 líneas del bloque JET por una LUT de 256 entradas precomputada (más rápido además que el branching JET
  por píxel).
- **Etiquetar isolíneas** con su valor de nivel cada N segmentos (patrón GiD/COMSOL).
- **Control de opacidad** campo ↔ deformada cuando ambos están activos.

---

## G. Roadmap

### Fase 1 — Eliminación de ruido visual *(la de mayor ROI)*
- **Objetivos:** llevar el canvas de "todo encendido" a "detail-on-demand". Default limpio.
- **Tareas:**
  1. `show_node_labels`/`show_elem_labels` default `False` (`:348-349`).
  2. Implementar `_lod_level()` y consumirlo en `_draw_nodes`/`_draw_elements`/`_draw_grid`.
  3. Numeración auto en zoom cercano + siempre en seleccionado.
  4. Toggle toolbar `Auto/Siempre/Nunca` para nodos y elementos.
  5. Realzar borde exterior del dominio vs aristas internas.
- **Dependencias:** ninguna (se apoya en flags/métodos existentes).
- **Tiempo estimado:** 2–3 días.
- **Impacto esperado:** elimina ~90 % del ruido percibido **y** recorta el árbol Tk 5–10× → mejora UX y rendimiento a la vez.

### Fase 2 — Sistema de selección profesional
- **Objetivos:** selección que destaca a cualquier escala.
- **Tareas:**
  1. Halo de selección (apilado de líneas/óvalos, técnica del glow existente). Constantes `CANVAS_SELECTED_HALO`, `CANVAS_HOVER_COLOR` en `settings.py`.
  2. Estado **hover** vía `<Motion>` (ya bindeado) + restyle del ítem bajo cursor.
  3. **`focus_mode`**: atenuar contexto reutilizando la maquinaria `ghost_geometry`.
  4. Estados Locked/Hidden (atenuar / no dibujar) — base para "aislar región".
  5. Restyle incremental de selección (`itemconfig` en vez de `delete("all")`).
- **Dependencias:** Fase 1 (el focus_mode se apoya en el LOD).
- **Tiempo estimado:** 3–4 días.
- **Impacto esperado:** selección inmediatamente legible en malla grande; elimina clicks por prueba y error.

### Fase 3 — Jerarquía visual FEM
- **Objetivos:** que cargas/restricciones/silueta nunca se pierdan; un solo nivel domina por vez.
- **Tareas:**
  1. Atenuación contextual de las 8 capas según foco.
  2. Migrar canvas a viridis/coolwarm (LUT 256).
  3. Etiquetas de isolíneas + control de opacidad campo/deformada.
  4. Realce semántico permanente de BC/cargas en focus_mode.
- **Dependencias:** Fases 1 y 2.
- **Tiempo estimado:** 3–4 días.
- **Impacto esperado:** lectura clara del *problema* FEM (no solo de la geometría); coherencia cromática con el resto del proyecto.

### Fase 4 — Optimización de rendimiento
- **Objetivos:** fluidez hasta ~10.000 elem.
- **Tareas:**
  1. `cProfile` sobre redraw de 1.000 elem (confirmar hot path).
  2. Viewport culling con grid-hash espacial.
  3. Rasterizar wireframe/nodos al bitmap PIL en zoom lejano.
  4. Mapa `id → item_handle` para restyle quirúrgico.
- **Dependencias:** Fase 1 (LOD ya da la mayor parte de la ganancia).
- **Tiempo estimado:** 4–6 días.
- **Impacto esperado:** redraw sub-100 ms a 1.000 elem; viabilidad a 10.000.

### Fase 5 — Validación con usuarios
- **Objetivos:** confirmar que el alumno lee mejor la malla y comete menos errores de selección.
- **Tareas:**
  1. Test con 5–8 estudiantes: tareas "seleccioná el elemento E12", "identificá la zona de máxima σ", "contá los nodos restringidos".
  2. Métricas: tiempo a tarea, clics erróneos, errores de identificación, SUS.
  3. A/B contra el canvas actual.
  4. Iterar umbrales de LOD según feedback.
- **Dependencias:** Fases 1–3.
- **Tiempo estimado:** 1 semana (incluye reclutar + analizar).
- **Impacto esperado:** validación empírica; calibración de los umbrales `edge_px`.

---

## H. Recomendación final — arquitectura UX/UI óptima

### La arquitectura: **"Contexto atenuado + foco progresivo"** (Focus-and-Context con LOD)

Un único modelo de visibilidad gobernado por dos ejes —**zoom (LOD)** y **foco (selección)**— sobre el motor de rasterizado
que ya tenés. En cada frame el canvas responde dos preguntas: *¿a qué escala estoy?* (cuánto detalle revelar) y *¿hay algo
en foco?* (cuánto atenuar el resto). Todo lo demás —numeración, nodos Q9, grid, halos— se deriva de esas dos respuestas.

### Por qué esta y no otra

- **Claridad visual:** ataca la causa raíz (visibilidad global binaria) con el patrón que el alumno ya conoció en cualquier
  CAD. El default limpio + revelado bajo demanda es lo que distingue a Abaqus/COMSOL de un visor naïve.
- **Escalabilidad:** el LOD es simultáneamente la palanca de UX **y** de rendimiento — apagar ítems en zoom lejano es lo que
  permite que la misma arquitectura sirva a 100 y a 10.000 elementos sin reescribir el backend.
- **Rendimiento:** reutiliza todo lo bueno que ya existe (Numba, caché PIL, interaction-mode, ghost) y solo agrega *decisiones
  de cuándo dibujar*, más culling/restyle incremental. No hay reescritura del rasterizador.
- **Facilidad de implementación:** las Fases 1–2 (el 80 % del valor) se construyen sobre flags y métodos existentes
  (`ghost_geometry`, glow apilado, `<Motion>` ya bindeado, flags `show_*`). Riesgo bajo, alto retorno.
- **Experiencia de aprendizaje:** la numeración por selección/query convierte el canvas en una herramienta de *inspección*
  pedagógica ("hacé click para ver el ID y los puntos de Gauss de ESTE elemento") en lugar de una pizarra saturada — alinea
  el canvas con la filosofía de los módulos educativos (click en canvas = single source of truth).

### Acciones concretas inmediatas (orden de ejecución)

1. **Una línea, máximo impacto:** `show_node_labels = False`, `show_elem_labels = False` por default (`mesh_canvas.py:348-349`).
2. **`_lod_level()`** basado en `edge_px` + gating en `_draw_nodes`/`_draw_elements`/`_draw_grid`.
3. **Numeración por selección** (ítem seleccionado muestra su ID a cualquier zoom).
4. **Halo de selección** (apilado de líneas, técnica del glow ya presente) + constantes nuevas en `settings.py`.
5. **`focus_mode`** reutilizando `ghost_geometry` para atenuar el contexto.
6. **Hover** sobre el `<Motion>` ya existente.
7. **Restyle incremental** de selección (sin `delete("all")`).
8. **viridis/coolwarm** en el canvas (LUT 256).
9. **Viewport culling** con grid-hash.

Las acciones 1–3 entregan la transformación más visible en ~1 día de trabajo. Las 4–6 hacen que la selección sea
profesional. Las 7–9 son escalabilidad. Ninguna toca el rasterizador Numba ni la API pública del canvas.

---

*Toda referencia `archivo:línea` apunta a `gui/preprocessing/mesh_canvas.py` salvo indicación contraria.*
