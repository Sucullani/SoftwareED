# Ventanas recortadas al instalar en otro equipo (escalado de Windows)

**Fecha**: 2026-09-10 · **Autor**: Claude (sesión de VSCode) · **Estado**: terminado, sin commit

## Qué se pedía

Reporte del autor: *"la app se descuadra al instalarla en otros equipos: en algunas
pantallas los botones no se ven o quedan cortados"*. Diagnosticar la causa real y
arreglarla.

## Causa real

**No** es la virtualización de DPI de Windows (esa fue la primera hipótesis y es falsa):
`ttk.Window(hdpi=True)` —el default que usa `MainWindow`— llama a `SetProcessDPIAware()`
antes de crear el intérprete, así que el proceso corre como **system DPI aware** y Tk
recibe el DPI real del monitor. Verificado: `GetProcessDpiAwareness()` devuelve 0
(*unaware*) con un `tk.Tk()` pelado y **1** (*system*) con un `ttk.Window`.

La consecuencia es la que el código no contemplaba: Tk mide las **fuentes en puntos**, y
todas las del programa se declaran así (`("Segoe UI", 9)`). Con el escalado de Windows al
125 % Tk ve 120 dpi, `tk scaling` pasa de 1,33 a 1,67 y cada fuente —y cada widget que la
contiene— se dibuja 1,25× más grande. Los tamaños de ventana, en cambio, estaban escritos
como enteros de píxeles elegidos a mano sobre el monitor de desarrollo (1366x768 al 100 %)
y no crecían. Dos modos de falla, ninguno visible en el equipo del autor:

**(a) el contenido crece, la ventana no** → Tk recorta lo **último** que se empaquetó, que
en casi todos los diálogos era justo la barra de botones del pie. Medido con Tk real:

| Diálogo | ventana fija | contenido a 96 dpi | a 120 dpi | a 144 dpi |
|---|---|---|---|---|
| `AboutDialog` | 450x**350** | 323x**390** | 375x**465** | 444x**530** |
| `MaterialDialog` | **680**x460 | **740**x396 | **914**x469 | **1075**x541 |
| `UnitsDialog` | 440x**180** | 252x161 | 257x174 | 293x**185** |
| `MemoriaStyleDialog` | 460x**210** | 446x202 | 446x208 | 446x**214** |

`AboutDialog` y `MaterialDialog` ya se recortaban **al 100 %**, en el equipo de
desarrollo: el botón Cerrar salía a medias y el nombre del material se leía "Acero E".

**(b) la ventana no entra en el escritorio** → `ElementTypeDialog` fijaba 760x**720** px y
era `resizable(False, False)`, contra un área útil de 1366x**728** en una pantalla de 768
con la barra de tareas: 8 px de margen en el equipo del autor, negativos en cualquier
portátil más chico, con la barra de tareas más alta o con el escalado subido. La ventana
principal exigía `minsize(1200, 700)`, así que ni siquiera podía encogerse para entrar.

## Qué se hizo

**[gui/scaling.py](../../gui/scaling.py)** (nuevo) es la única vía para dimensionar un
Toplevel. `fit_window(win, ancho, alto, parent=…, minimo=…)`: escala la medida de diseño
(px a 96 dpi) por el DPI real, la toma como **piso** y agranda la ventana si el contenido
pide más, la **recorta** al área útil del monitor del padre, la centra ahí dentro y la
deja redimensionable. El área útil sale de `MonitorFromWindow` + `GetMonitorInfoW`: barra
de tareas descontada esté donde esté, y monitor correcto en multi-monitor. `fit_size` y
`fit_position` son puras y se testean sin pantalla.

Consumidores: los 11 diálogos de `gui/dialogs/` (vía `size_dialog` de
`_dialog_helpers.py`, para no romper la regla dura 19), `MainWindow` (minsize),
`TheoryViewer` (900x**820**, que no entraba en ninguna pantalla de 768), la ventana de
K_ij de M5, `Surface3DViewer`, los overlays de los módulos educativos (su alto sale del
contenido y no tenía tope) y los tres tooltips flotantes.

**Orden de empaquetado**: la barra de botones se empaqueta **primero** con `side=BOTTOM` y
el área elástica (el video, en los diálogos de tipo de elemento y análisis) **última** con
`expand`. Ídem la barra de estado de `MainWindow`, que ahora se construye antes que el
layout principal. Es la mitad del arreglo: sin esto, recortar la ventana sigue borrando los
botones.

Regla dura **23** en `CLAUDE.md`; canon en
[convenciones/arquitectura.md](../convenciones/arquitectura.md) §diálogos.

## Qué se descartó y por qué

- **Activar per-monitor DPI v2**: no hacía falta (ttkbootstrap ya activa system-aware) y
  con Tk 8.6 sería peor: no maneja `WM_DPICHANGED`, así que al arrastrar la ventana a un
  monitor con otro escalado quedaría del tamaño físico equivocado.
- **Achicar los tamaños de diseño hasta que entren en 1280x680**: deja la app apretada en
  los equipos donde sí hay lugar. El recorte tiene que ser por pantalla, no global.
- **Envolver cada diálogo en un canvas con scroll**: mucho más invasivo, y con la barra de
  botones fuera del área scrolleable el resultado es equivalente al de empaquetarla
  primero, que es una línea.
- **Escalar por DPI los glifos del canvas** (radios de nodo, flechas, grosores) y las
  figuras matplotlib embebidas: se ven algo más chicos en una pantalla HiDPI, pero no
  recortan nada ni esconden botones. Es ajuste fino visual, decisión del autor —
  anotado en el BACKLOG.

## Trampas encontradas

- `ttkbootstrap.Window(hdpi=True)` llama a `SetProcessDPIAware()` **antes** de `Tk()`. Un
  `tk.Tk()` pelado en un script de prueba **no** reproduce las condiciones de la app: da
  *unaware* y no se ve el bug. Toda medición tiene que salir de un `ttk.Window`.
- `winfo_fpixels("1i")` sigue a `tk scaling`, así que **forzar `tk scaling` simula un
  equipo con otro escalado de forma fiel**: las fuentes crecen de verdad y los
  `winfo_req*` crecen con ellas. Es lo que hace `test_dpi_layout_gui`.
- ttkbootstrap no soporta **dos raíces Tk en el mismo intérprete**: la segunda revienta con
  `TclError: Layout Round.Toggle not found`. Por eso el test corre una pantalla por
  subproceso.
- `winfo_width()` devuelve 1 mientras la ventana no está **mapeada**: para medir hay que
  `deiconify()` + `update()` (no alcanza `update_idletasks()`).
- Los diálogos que llaman `wait_window()` en su constructor (health, memoria_style,
  pdflatex) bloquean cualquier arnés de medición: el test lo neutraliza con un
  monkeypatch.

## Qué quedó pendiente

- **Validación visual del autor** (única decisión abierta): abrir *Modelo → Tipo de
  Elemento* y *Tipo de Análisis* y confirmar que el video, ahora elástico, se ve bien
  cuando el diálogo se achica; y *Modelo → Materiales*, que ahora abre ~740 px de ancho en
  vez de 680 (el ancho que su contenido siempre pidió).
- Para reproducir otro equipo sin tocar el escalado de Windows:
  `set EDUFEM_AREA_UTIL=1280x680 && python main.py`.
- Glifos del canvas y figuras matplotlib sin escalar por DPI (ver arriba).

## Verificación

- `python -m tests.run_gates` → **verde** (27 módulos).
- `python -m tests.run_gates --con-gui` → **verde**, incluido `test_dpi_layout_gui`
  (26,6 s): abre `MainWindow` + 7 diálogos en 4 pantallas simuladas (1366x768 al 100 % y al
  125 %, 1920x1080 al 150 %, 1600x900 al 125 %) y verifica en cada uno que la ventana entre
  en el área útil, que su contenido no quede recortado y que su barra de botones siga
  visible.
- **Contraprueba**: con los diálogos originales restaurados, el mismo test falla — a 144
  dpi `AboutDialog` "pide 530 px y tiene 350", `MaterialDialog` "pide 1075 px y tiene 680"
  y su barra `Nuevo`/`Eliminar` queda en 0 px de alto; con área útil 1280x680,
  `ElementTypeDialog` "mide 760x720 y el área útil es 1280x680".
- **Captura con `PrintWindow`** a 120 dpi, antes y después, de `AboutDialog` (el botón
  Cerrar pasa de no existir a verse entero) y de `MaterialDialog` (los botones
  `Nuevo`/`Eliminar` pasan de estar cortados por la mitad a verse enteros, y el campo
  Nombre de "Acero E" a "Acero Estructural").
