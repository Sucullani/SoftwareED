# Auditoría de distribución: que el setup sea lo único que el alumno toca

**Fecha**: 2026-09-10 · **Estado**: implementado y medido, sin commit

> Vara del autor: *«que el usuario ejecute el setup y todo funcione: un solo archivo, sin
> instalar nada externo, sin problemas de LaTeX, DPI, etc.»*.

Continúa [2026-09-10_instalador-profesional.md](2026-09-10_instalador-profesional.md), que dejó
el instalador terminado. Esta pasada audita el resultado **desde la máquina del alumno**, no
desde el repositorio: se midió el paquete ya instalado en
`%LOCALAPPDATA%\Programs\EduFEM`, no el código.

## Lo que ya estaba bien (verificado, no supuesto)

| Qué | Cómo se comprobó |
|---|---|
| **LaTeX embebido, de punta a punta** | `EDUFEM_TEXLIVE_DIR=<instalado>\texlive python -m tests.test_memoria_calculo` → **43/43**, PDF Q4 de 616 KB y Q9 de 640 KB. Compilado con el TeX **instalado**, no con el del repositorio |
| **El TeX llega completo** | Los 4180 archivos de `{app}\texlive` son idénticos a `vendor/texlive` (diff de árboles vacío) |
| **DPI** | `tests.test_dpi_layout_gui` con Tk real: **132 comprobaciones OK**, cada ventana entra y conserva su barra de botones en las 4 pantallas simuladas (1366×768 al 100 %, 1920×1080 al 150 %, 1366×768 al 125 %) |
| **Nada externo** | Ni una llamada de red en el código de runtime: los únicos `https://` son las URL que muestra el diálogo de «falta pdflatex», que con el instalador nunca aparece. El runtime de MSVC viaja en el bundle |
| **Rutas** | Ningún `__file__` ni ruta relativa apunta a datos: los dos que hay son los *fallback* de desarrollo, guardados por `sys.frozen`. Ninguna escritura con ruta relativa |
| **Contrato instalador ↔ app** | `tests.test_distribucion` (versión, AppUserModelID, mutex, asociación, BOM del `.iss`) |

## Hallazgo 1 — el arranque: 11-15 segundos, siempre

Medido lanzando el `.exe` instalado y esperando a que el proceso **hijo** tenga ventana (el
proceso padre de un onefile nunca la tiene: el bootloader descomprime y lanza otro proceso —
una primera medición que miraba el padre esperó 90 s sin ver nada).

| | onefile (como estaba) | onedir (ahora) |
|---|---|---|
| arranque en frío | 10,9 s | 7,0 s |
| arranque habitual | 11,9 - 14,8 s | **3,0 - 3,5 s** |
| procesos | 2 | 1 |
| restos en `%TEMP%` | 189 MB por cada cierre anormal | ninguno |

El onefile **no se acelera nunca**: en cada arranque re-extrae ~190 MB a `%TEMP%`, que el
antivirus vuelve a revisar. El `LEEME.txt` documentaba el síntoma como si fuera normal —«el
primer arranque tarda entre 10 y 40 segundos […] no hagas doble clic varias veces»—, que es la
señal de que era un defecto y no una característica.

Se comprobó además que había **26 carpetas `_MEI*` huérfanas** en el `%TEMP%` de este equipo,
1767 MB en total; 6 de ellas de EduFEM (1132 MB), de arranques que no cerraron limpio. Se
borraron las 6.

**Corrección**: `build.spec` pasa a **onedir** (`exclude_binaries=True` + `COLLECT`) y el `.iss`
copia `dist\EduFEM\*` con `recursesubdirs`. **El entregable no cambia: sigue siendo un único
`EduFEM-Setup.exe`.** La ventaja que justificaba onefile —un archivo suelto— no aplicaba: lo
que se distribuye es el instalador, y la carpeta portable ya era una carpeta, porque el TeX
embebido va al lado del `.exe`.

`tests/test_distribucion.py` ata ahora las dos mitades: si alguien vuelve el spec a onefile, el
`Source:` del `.iss` queda apuntando a una carpeta inexistente, y el test lo dice antes que
ISCC.

### El entregable, además, adelgazó 31 MB

| | onefile | onedir |
|---|---|---|
| `EduFEM-Setup.exe` | 126,4 MB | **95,5 MB** |
| instalado en `{app}` | 156 MB | 271 MB |
| pico de disco durante el uso | 156 + 190 en `%TEMP%` | 271 |

El instalador encoge porque el onefile llegaba a Inno **ya comprimido** (zlib) y LZMA2 no podía
recomprimir ese blob; con onedir, Inno comprime los `.dll` y `.pyd` crudos y los aprovecha
mucho mejor. Ocupa más en disco instalado, pero menos que el pico real del onefile, que además
de sus 156 MB mantenía ~190 MB extraídos en `%TEMP%` mientras el programa corría.

### Verificado sobre el paquete instalado

Se recorrió el ciclo entero en modo silencioso (`/VERYSILENT /TASKS=desktopicon,asociar`):
actualización sobre la instalación previa, desinstalación, instalación **limpia** sobre un
equipo sin rastros, y desinstalación otra vez.

| Qué | Resultado |
|---|---|
| arranque, recién instalado | **4,7 - 6,8 s** (Windows todavía está revisando los archivos nuevos) |
| arranque, ya asentado | **3,0 - 3,2 s**, un solo proceso |
| restos en `%TEMP%` tras varios arranques | **ninguno** |
| doble clic sobre un `.edufem` | abre el proyecto; el título pasa a `prueba_instalacion.edufem — EduFEM …` |
| registro | extensión → ProgID, `shell\open\command` con `"%1"`, icono `{app}\edufem_doc.ico` |
| accesos directos | Escritorio y menú Inicio, presentes |
| TeX embebido | los 4180 archivos, idénticos a `vendor/texlive`; `test_memoria_calculo` **43/43** compilando con **ese** árbol |
| `{app}` | 269 MB en 5652 archivos; el `EduFEM.exe` de 106 MB quedó reemplazado por el lanzador de 25,7 MB |
| desinstalación | `{app}` entera, accesos directos, ProgID, extensión, *Abrir con* y App Paths: **todo se va**. `~/.edufem/recent.json` y los `.edufem` del alumno: **se quedan** |

## Hallazgo 2 — los modelos del alumno iban a parar dentro del programa

Ninguno de los seis `filedialog` de `gui/main_window.py` declaraba `initialdir`, así que Tk los
abría en el **directorio de trabajo del proceso**. Corriendo desde el repositorio eso es la raíz
del código, molesto pero inofensivo. En la aplicación instalada es `{app}`, porque el acceso
directo que crea el instalador arranca ahí: el primer «Guardar Como» del alumno dejaba su
modelo dentro de `AppData\Local\Programs\EduFEM`, una carpeta oculta que él no visita y que la
desinstalación deja huérfana con el trabajo adentro. Lo mismo la Memoria en PDF y el ZIP del
modelo.

**Corrección**: `config/user_paths.py`. Los seis diálogos abren en `Documentos\EduFEM` la
primera vez y después en la última carpeta usada (`~/.edufem/paths.json`, al lado de
`recent.json`); los tres de guardar proponen además el nombre del proyecto con la extensión que
corresponda (`viga.edufem` → `viga.pdf`). «Documentos» se le pregunta a Windows por su *known
folder*: el nombre real depende del idioma y suele estar redirigida a OneDrive.

## Hallazgo 3 — UPX quedaba encendido sin estar instalado

`build.spec` pedía `upx=True` en el `EXE` (y ahora también podría hacerlo en el `COLLECT`).
En este equipo UPX no está en el PATH, así que la opción no hacía nada y el build salía sin
empaquetar. El día que alguien lo instale, el mismo comando produciría un entregable distinto:
DLL empaquetadas con UPX, que es una de las señales de más peso en los heurísticos de los
antivirus. EduFEM ya viaja **sin firma de código**; sumarle esa marca por unos pocos MB —que
además el instalador recomprime igual con LZMA2— es un mal negocio. Queda `upx=False` explícito
en los dos sitios, con la razón escrita al lado.

## Hallazgo 4 — la desinstalación dejaba dos claves huérfanas

Se desinstaló de verdad, en silencio, y se miró qué quedaba. Los 5652 archivos de `{app}`, los
accesos directos, el ProgID y `App Paths` se van bien; `~/.edufem/recent.json` y los `.edufem`
del alumno se conservan, que es lo correcto. Pero quedaban dos cáscaras en el registro:

- `HKCU\Software\Classes\.edufem` con un `OpenWithProgids` vacío. El valor sí se borraba
  (`uninsdeletevalue`, deliberado: esa clave puede tener entradas de otros programas), pero la
  clave vacía sobrevivía. Ahora lleva además `uninsdeletekeyifempty`, que la borra solo si
  nadie más dejó nada. Inno desinstala en orden inverso, así que `OpenWithProgids` se vacía
  antes de que se evalúe la clave padre.
- `HKCU\Software\Classes\Applications\EduFEM.exe` entera. El `uninsdeletekey` estaba puesto en
  la hoja `shell\open\command`, así que borraba esa hoja y dejaba el padre y `SupportedTypes`.
  El flag pasó a una entrada nueva sobre la clave **raíz** —sin `ValueType`, solo para crearla
  y marcarla—, que borra el subárbol completo.

## Trampas encontradas

- **Medir el arranque de un onefile mirando el proceso que uno lanzó da un resultado falso.**
  `Start-Process -PassThru` devuelve el bootloader, que jamás abre una ventana; la primera
  medición esperó 90 s mirando el proceso equivocado. Hay que buscar, entre todos los procesos
  del mismo nombre, el que tenga `MainWindowHandle`.
- **Y el título de la ventana hay que leerlo tarde.** `MainWindow` difiere la carga del proyecto
  con `after(0, …)`: si se lee el título apenas aparece la ventana, todavía dice el genérico y
  parece que el doble clic no funcionó.
- **PyInstaller en onedir puede morir por el antivirus, y parece permanente.** El `COLLECT`
  vuelca 1466 archivos de golpe y Defender abre cada uno apenas aparece. Acá falló **dos veces
  seguidas** en el mismo archivo (`PermissionError: … _internal\ucrtbase.dll`), y siempre
  después de cuatro minutos de análisis. No era permanente: cuando el archivo a medio escribir
  se borra mientras el antivirus lo tiene abierto, Windows lo deja en *delete pending* y el
  intento siguiente vuelve a fallar en el mismo nombre. Copiarlo a mano funcionaba, y el tercer
  intento —con la carpeta borrada y una pausa— pasó limpio. `build_all.ps1` reintenta ahora el
  paso 3 hasta tres veces, borrando `dist\EduFEM` y esperando 20 s entre intentos.
- **`/SUPPRESSMSGBOXES` convierte «Reintentar» en «Anular».** Instalar inmediatamente después de
  desinstalar falló con **código 5**: el log (`%TEMP%\Setup Log *.txt`) muestra que `EduFEM.exe`
  —el primer archivo que se copia— dio `MoveFile falló; código 5. Acceso denegado.` durante ocho
  segundos, porque el antivirus tenía tomado el ejecutable de 26 MB recién escrito en una
  carpeta que se acababa de borrar. Inno reintenta solo y después ofrece **Anular / Reintentar /
  Omitir**; con `/SUPPRESSMSGBOXES` esa pregunta se auto-responde *Anular* y la instalación se
  revierte entera. Repetida 20 s más tarde pasó limpia. Para el alumno esto es recuperable
  —vería el diálogo y haría clic en *Reintentar*—, pero **al automatizar pruebas hay que dejar
  pasar medio minuto entre desinstalar y volver a instalar**. Es el mismo fenómeno de
  *delete pending* que hace fallar al `COLLECT` de PyInstaller.
- **El heredoc de bash se come las barras invertidas** en este entorno: los scripts auxiliares
  de esta sesión se escribieron con `chr(92)` en vez de literales.

## Lo que queda abierto (decide el autor)

1. **`resources/examples/ejemplo_geometria.dxf` viaja en el bundle y el alumno no lo alcanza.**
   Ningún módulo lo referencia; queda en `{app}\_internal\resources\examples\`, donde nadie
   entra. O se cablea (que «Importar DXF» lo ofrezca la primera vez) o se saca del `datas`.
2. **`installer/assets/*.bmp` y `resources/icons/edufem_doc.ico` están sin versionar**, mientras
   que `resources/icons/edufem.ico` sí lo está. Commitear con `git add -u` dejaría el
   repositorio sin poder compilar el instalador y el gate rojo en un clon limpio: **hay que
   agregarlos explícitamente**.
3. **`~/.edufem/latex_cache/`**: 1,3 MB de PNG de mayo, de una implementación anterior de
   `LatexBlock`. Hoy nadie lo escribe ni lo borra, y el desinstalador tampoco lo toca.
4. **`resources/fonts/` sigue sin las CMU** (ver el README de esa carpeta): los *overlays* de
   `LatexBlock` usan el serif de Tk. Está documentado y no rompe nada.

## Qué queda para el autor

Instalar `installer/Output/EduFEM-Setup.exe` en un equipo limpio y comprobar el arranque, la
Memoria en PDF y que «Guardar Como» proponga `Documentos\EduFEM`.
