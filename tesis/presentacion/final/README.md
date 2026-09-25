# Defensa de EduFEM — presentación interactiva y video (tesis final)

Presentación de la defensa sincronizada con la **tesis final** (`tesis/main_final.tex`, eje
«caja negra → baja trazabilidad y verificabilidad del análisis»). Reemplaza a las versiones
PowerPoint v1 y v2 de `tesis/presentacion/`, que seguían los ejes anteriores y quedan como archivo.

| Archivo | Qué es |
|---|---|
| `Defensa_EduFEM.html` | **La presentación.** Se abre con doble clic, sin internet y sin instalar nada |
| `Presentar_defensa.bat` | La abre a pantalla completa, sin barras del navegador (Chrome o Edge) |
| `Defensa_EduFEM_v2.html` · `Presentar_defensa_v2.bat` | **Versión 2, estilo PowerPoint**: las mismas láminas, animaciones, datos y botones, con el aspecto de la plantilla PowerPoint anterior (ver abajo) |
| `Defensa_EduFEM_v2.pptx` | **La versión 2 en PowerPoint**: editable, con animaciones por clic, enlaces, notas del orador y los videos del software |
| `Defensa_EduFEM_v2.pdf` | Respaldo estático de la versión 2 |
| `Defensa_EduFEM_final.pdf` | Respaldo estático: una lámina por hoja, en su último paso |
| `../video/Defensa_EduFEM_final.mp4` | Video narrado: la presentación grabada cuadro a cuadro, con voz, subtítulos seleccionables y capítulos por bloque |
| `../video/Defensa_EduFEM_final.srt` · `guion_video_final.md` | Subtítulos aparte y guion con la marca de tiempo de cada paso |
| `herramientas/` | Lo que genera los datos, la voz, el video y el PDF (no hace falta para proyectar) |

## Cómo se presenta

57 láminas principales en el orden del **Taller 6** (carátula → introducción → base teórica →
diseño y desarrollo del modelo → resultados → análisis → conclusiones) y 6 de **respaldo para
preguntas**, que no están en el recorrido: se llega a ellas desde el índice.

| Tecla | Acción |
|---|---|
| → · Espacio · Av Pág | siguiente paso (cada lámina revela su contenido por pasos) |
| ← · Re Pág | paso anterior |
| **M** · Esc | índice: todas las láminas, los laboratorios y el respaldo |
| **S** | **vista del orador** en otra ventana: guion del paso, lo que viene, cronómetro total y por bloque contra los tiempos del Taller 6 |
| **A** | presentación **narrada automática** (voz y avance solos); **C** subtítulos |
| **L** | puntero láser · **B** pantalla negra · **W** blanca |
| **T** | tema claro u oscuro (claro para salas con mucha luz) · **F** pantalla completa |
| Retroceso | volver después de seguir un enlace |
| número + Intro | ir a la lámina con ese número |

**Botones.** El pie muestra los seis bloques (clic para saltar a uno), el avance y la
navegación. Dentro de las láminas: las filas de la **matriz de consistencia** y los criterios
del **veredicto** llevan a su evidencia; la carátula, la demostración y el cierre tienen accesos
directos a los laboratorios. Después de seguir un enlace aparece **«Volver a …»** en el pie.

**Laboratorios** (◆ en el índice): láminas que además de animarse se manejan con el mouse.

| Laboratorio | Qué se puede hacer |
|---|---|
| Trazabilidad en acción | seguir la tensión del nodo 7 hacia atrás, etapa por etapa, hasta los datos, con los números del motor |
| Mapeo isoparamétrico | arrastrar los nodos del elemento real; ver cada función de forma en 3D; Q4 o Q9 |
| Jacobiano y matriz B | fórmula ↔ valores; ver cómo cae det J al distorsionar el elemento |
| Cuadratura de Gauss | reglas 1×1, 2×2, 3×3; los modos espurios de reloj de arena |
| Ensamblaje | cada elemento sumándose en K (18 × 18), restricciones y solución |
| Post-proceso | sonda en cualquier nodo con su círculo de Mohr; von Mises, σx, σy, τxy; crudo y suavizado |
| Convergencia MMS | normas L², H¹ y σ*; las cuatro configuraciones |
| Viga de Timoshenko | campo σx sobre la deformada; puntos A, B y C frente a la analítica y SAP2000 |
| Membrana de Cook | Q4 o Q9 con N = 2 … 32; la curva de convergencia y los valores de Štembera y Füssl |
| La lección de la extrapolación | la E correcta frente a la E con la numeración equivocada |

**Si en la sala no está EduFEM**, la lámina de demostración lleva a esos laboratorios: usan la
salida real del motor, no ilustraciones.

**Con dos pantallas** (proyector + laptop): abrir la presentación, llevar la ventana al
proyector, presionar **F**, y presionar **S** para abrir la vista del orador en la laptop.

## Versión 2 (estilo PowerPoint) y el archivo .pptx

**`Defensa_EduFEM_v2.html`** es la misma presentación con otro traje: láminas blancas, títulos
en azul marino con Calibri y un acento naranja debajo, rótulo del bloque con barra naranja,
puntos de avance arriba a la derecha (clic para saltar de bloque), pie con la fuente en la
tesis y el número, separadores y cierre en azul marino, carátula partida y transiciones de
fundido, como la plantilla de `tesis/presentacion/build_deck.py`. Todo lo demás es igual:
laboratorios, botones, «Volver», índice (M), vista del orador (S), modo narrado (A). No tiene
tema oscuro. No se edita a mano: `herramientas/generar_v2.mjs` la arma a partir de
`Defensa_EduFEM.html` (agrega `data-estilo="ppt"`, que activa `assets/css/estilo_ppt.css`), así
una corrección en una lámina se hace una sola vez. Si el equipo no tiene Calibri, usa Carlito,
de métricas idénticas, que va en `assets/terceros/`.

**`Defensa_EduFEM_v2.pptx`** es la versión 2 convertida a PowerPoint, lámina por lámina y paso
por paso:

- Una diapositiva por lámina (57 + 6 de respaldo, ocultas, + un índice oculto). Cada paso de la
  presentación es **un clic**: lo que aparece entra con «Desvanecer» y lo que se va sale igual;
  lo que en la HTML entra solo al llegar a la lámina, aquí también. Transición de fundido.
- Texto, cajas, tablas, fichas e imágenes son **formas nativas y editables** (Calibri). Los
  gráficos, los lienzos del MEF y las fórmulas son imágenes al doble de resolución: se ven
  nítidos proyectados, pero para cambiarlos hay que regenerarlos desde la HTML.
- **Enlaces**: los puntos de bloque, los bloques de los separadores, las filas de la matriz de
  consistencia, los criterios del veredicto, los accesos de la carátula, la demostración y el
  cierre, y un botón «↩ Volver» en las láminas de destino y de respaldo. El índice se abre desde
  «☰ Índice» en la carátula y en el cierre.
- **Notas del orador**: la narración de cada paso, rotulada con el clic que la muestra.
- Los **dos videos del software** (tensión y deformación plana; bloqueo Q4/Q9) se reproducen
  solos en bucle.
- En la vista de edición, las láminas cuyos pasos cambian un gráfico muestran los pasos
  superpuestos: es como PowerPoint guarda las animaciones de entrada y salida. En la
  presentación se ven de a uno.
- Lo que no pasa a PowerPoint: los laboratorios que se manejan con el mouse (arrastrar nodos,
  la sonda, los botones N = 2…32 de Cook) quedan en el estado que muestra cada paso, y las
  animaciones continuas (la malla deformándose, el recorrido de las nueve etapas) quedan en un
  cuadro fijo. Para eso está la versión HTML.

Regenerar (desde `herramientas/`, después de `node generar_v2.mjs`):

```
node extraer_pptx.mjs                                     # escena: formas e imágenes por paso (~3 min)
..\..\..\..\.venv\Scripts\python.exe construir_pptx.py    # -> ../Defensa_EduFEM_v2.pptx
node exportar_pdf.mjs --html=Defensa_EduFEM_v2.html       # -> ../Defensa_EduFEM_v2.pdf
```

Para revisar la conversión: `construir_pptx.py --pasos-separados --salida=<otro.pptx>` arma una
diapositiva por paso, sin animaciones; `exportar_png_pptx.ps1` la exporta a PNG con PowerPoint
y `foto.mjs <carpeta> --pasos --pptx --html=Defensa_EduFEM_v2.html` fotografía los mismos pasos
en la HTML, con el mismo instante de captura. `inspeccionar_pptx.ps1` lista lo que PowerPoint
entendió de cada diapositiva: efectos, clics, transición, enlaces y videos.

## De dónde salen los datos

Toda cifra que se anima sale del motor de EduFEM, no de una copia a mano:
`herramientas/exportar_datos.py` corre `fem/` y `models/` sobre los casos de la tesis y escribe
`assets/data/datos_edufem.js` (ejemplo canónico completo —N, J, B, D, kₑ por punto de Gauss, K
de 18 × 18, u, reacciones, tensiones—, membrana de Cook Q4/Q9 con N = 2 … 32, viga de
Timoshenko Q9 56 × 8, campos del MMS y la rigidez con 1×1/2×2/3×3). Las tablas de convergencia
se leen de `docs/vyv/datos/*.csv`, las mismas que respaldan la tesis. Las cifras que la tesis
imprime (Tablas 3.2, 3.3, 3.9, 3.10…) se escriben tal como allí figuran y se contrastaron con
esos datos. Lo único que se calcula en vivo es lo que el usuario arrastra en el laboratorio del
mapeo y del Jacobiano, con las mismas fórmulas, y la lámina lo rotula así.

## Fidelidad a la tesis

Sigue `tesis/main_final.tex` tal como está en el repositorio (`capitulos_final/`), no la versión
en mejora `main_final1.tex`. El rótulo de cada lámina cita la sección, tabla o figura de esa
versión; la lámina de la memoria de cálculo remite a las páginas impresas del Anexo G
(pp. 164–171), y las citas llevan el número de su lista de referencias. Una auditoría
independiente cotejó cada lámina y cada texto de la narración con `main_final.pdf`: sus 25
observaciones están aplicadas.

Si otra versión reemplaza a `main_final`, hay que repasar los rótulos
(`class="fuente-sec"` en `Defensa_EduFEM.html`), las imágenes del Anexo G
(`assets/img/anexoG_*.png`), las páginas del Anexo G que nombran `assets/js/viz/diseno.js`
(lámina de la memoria) y `analisis.js` (cálculo manual de respaldo), y los números de cita.

**Dónde se aparta de la tesis: el alcance del MMS.** La `u_M` del MMS tiene tr ε = 0 y
γ = 0, así que no distingue la D de tensión plana de la de deformación plana (decisión abierta
en `docs/notas/ESTADO.md`). La presentación no repite lo que la tesis le atribuye de más: la
tarjeta de «Casos» ya no dice que ejercita «las dos D», «Alcances» dice «núcleo numérico» y no
«en los dos estados planos», las limitaciones dicen «deformación plana sin contraste externo»,
y el respaldo «Deformación plana: qué la verifica hoy» explica el límite y cita la prueba
uniaxial de `tests/test_vv_extensions.py`. Si el autor cambia la `u_M` (opción a), hay que
regenerar los datos (`exportar_datos.py` lee `docs/vyv/datos/*.csv`) y rehacer ese respaldo.

**Licencia.** La tesis final no declara la licencia del código; el archivo `LICENSE` del
repositorio es MIT. Las láminas que citan la tesis dicen «libre, código abierto», como la
Tabla 1.1; el MIT figura solo en la lámina de respaldo «Licencia del software», con su fuente.

## Regenerar

Desde la raíz del repositorio. Requiere el `.venv` del proyecto (con `edge-tts` y `mutagen`),
Node.js, `ffmpeg` y Chrome o Edge instalados.

```
cd tesis\presentacion\final\herramientas && npm install && cd ..\..\..\..
.venv\Scripts\python.exe tesis\presentacion\final\herramientas\exportar_datos.py     # 1. datos del motor (5 s)
.venv\Scripts\python.exe tesis\presentacion\final\herramientas\sintetizar_voz.py     # 2. voz (edge-tts, internet, ~2 min)
node tesis\presentacion\final\herramientas\grabar_video.mjs --partes=3               # 3. video mudo, 3 procesos (~45 min)
.venv\Scripts\python.exe tesis\presentacion\final\herramientas\montar_video.py --trabajo=<las carpetas que imprime el paso 3>
node tesis\presentacion\final\herramientas\exportar_pdf.mjs                          # 4. PDF de respaldo
```

- **Cambiar lo que se dice**: editar `herramientas/narracion_final.json` (un texto por paso de
  cada lámina, con ortografía normal: el sintetizador pasa las cifras a palabras) y repetir los
  pasos 2 y 3. Las pistas que no cambiaron se reutilizan. La voz y la velocidad están en ese
  mismo archivo (`es-BO-MarceloNeural`, `+8%`).
- **Cambiar una lámina**: `Defensa_EduFEM.html` (contenido), `assets/css/` (aspecto) y
  `assets/js/viz/` (animaciones). Si cambia el número de pasos de una lámina, ajustar su
  narración: `capturar_video.mjs` avisa cuando no coinciden.
- **Revisar sin abrir el navegador**: `node herramientas/foto.mjs <carpeta> --todas`
  fotografía cada lámina en su último paso; `node herramientas/probar_interaccion.mjs` prueba
  teclado, enlaces, «Volver», índice, tema, vista del orador y narración automática
  (19 comprobaciones).

## Decisiones de diseño

- **Tecnología**: HTML + JavaScript propio, sin frameworks. Las animaciones usan SVG y Canvas
  2D; las fórmulas, KaTeX; la tipografía, Inter. Todo va dentro de `assets/terceros/` (≈ 1 MB),
  así la presentación funciona sin conexión en cualquier equipo con un navegador actual.
- **Un solo reloj**: toda animación pasa por `EF.tween` / `EF.bucle` (`assets/js/nucleo.js`). En
  vivo corre con el reloj del sistema; en la grabación, con un reloj virtual que avanza cuadro a
  cuadro. Por eso el video muestra las mismas animaciones que la presentación, sincronizadas con
  la voz paso a paso, y sale idéntico en cada corrida.
- **Tamaños del Taller 6**: lienzo de 1920 × 1080; títulos de 64 px (32 pt) y texto de lectura
  de 38 a 48 px. Las tablas densas, los rótulos de gráficos y los pies van más chicos, como en
  la versión PowerPoint.
- **Tema oscuro por omisión**, porque las capturas de EduFEM son oscuras y los campos en *jet* se
  leen mejor sobre fondo oscuro; el claro está a una tecla.
- **Vocabulario**: el de `tesis/capitulos_final/CRITERIOS.md` (procedimiento de cálculo,
  cobertura de contenido, comprobador de salud, módulo educativo, estudiante; ninguna afirmación
  de efecto sobre quien usa el software). Citas con el número de la lista de referencias de la
  tesis final.
- **Respaldo para preguntas**: seis láminas con los datos de las preguntas de mayor riesgo de
  la auditoría final (cálculo manual, apoyos de la viga, umbrales, «educativo», licencia,
  deformación plana), con cifras tomadas de la tesis.

## Lo que queda para el autor

Un agente no puede juzgar el ritmo de la voz ni ensayar en la sala: mirar el video, verificar la
pronunciación de los nombres propios, ensayar con la vista del orador contra los 40–45 minutos
del Taller 6 y probar el lanzador en el equipo de la defensa (Chrome o Edge).
