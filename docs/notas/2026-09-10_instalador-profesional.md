# Instalador profesional: un archivo que deja todo listo

**Fecha**: 2026-09-10 · **Estado**: implementado, sin commit (espera validación del autor)

> Pedido del autor: *«tener un solo archivo instalador profesional para distribuir y que
> ejecute todo, crear acceso directo, etc., aplicando las mejores prácticas estándar de
> instaladores»*, y actualizar toda la documentación, la tesis y `dist/`.

## Qué había

`installer/EduFEM.iss` copiaba el `.exe`, el LEEME y el TeX embebido, creaba tres accesos
directos y registraba el desinstalador. Funcionaba, pero le faltaba casi todo lo que
distingue a un instalador terminado de uno improvisado:

- El `.exe` **no tenía datos de versión**: Windows lo mostraba sin Descripción ni Empresa en
  Propiedades ▸ Detalles, que es además una de las señales que miran los filtros de
  reputación.
- La versión estaba **escrita a mano en el `.iss`** además de en `config/settings.py`.
- El asistente usaba las **imágenes genéricas de Inno** y no mostraba la licencia.
- Los archivos `.edufem` eran **archivos de tipo desconocido**: hoja blanca en el Explorador y
  doble clic que no abría nada.
- Si EduFEM estaba abierto, el instalador **copiaba sobre el `.exe` en uso**.
- Los accesos directos no declaraban **AppUserModelID**, así que el icono anclado a la barra
  de tareas se desprendía del acceso directo.
- Sin `MinVersion` ni `ArchitecturesAllowed`: se dejaba instalar donde después no arranca.

## Qué se hizo

### 1. El ejecutable se identifica

`build.spec` genera `build/edufem_version_info.txt` a partir de `APP_VERSION` y lo pasa como
`version=` al `EXE`. El `.exe` ahora declara nombre de producto, versión, empresa,
descripción, copyright y nombre de archivo original.

### 2. Una sola fuente para la versión

`config/settings.py::APP_VERSION`. La leen `build.spec` (con regex, para no importar la app
durante el `Analysis`) y el preprocesador del `.iss`, que recorre el archivo y toma el valor
entre comillas de la asignación que empieza en la columna 1. Si esa línea se indenta o pasa a
comillas simples, el build aborta con un `#error` explícito, y `tests/test_distribucion.py` lo
detecta antes.

El único lugar que todavía repite la versión a mano es el texto del LEEME. Está anotado en
`tools/README.md`.

### 3. Integración real con Windows

Tres piezas que la aplicación y el instalador tienen que compartir, hoy en
`config/settings.py` y espejadas en el `.iss`:

| Qué | Constante | Para qué |
|---|---|---|
| `APP_USER_MODEL_ID` | `Sucullani.EduFEM.Aplicacion.1` | `main.py` lo fija en el proceso y el `.iss` lo declara en los accesos directos. Sin eso, Windows agrupa la ventana por el nombre del ejecutable y el icono anclado deja de corresponder al acceso directo |
| `APP_MUTEX_NAME` | `EduFEM.InstanciaEnEjecucion` | `main.py` crea el mutex nombrado; el `.iss` lo declara en `AppMutex`, así el asistente detecta EduFEM abierto y ofrece cerrarlo en vez de copiar sobre un `.exe` en uso |
| `PROJECT_FILE_EXTENSION` | `.edufem` | La extensión que el instalador asocia |

`tests/test_distribucion.py` compara las tres contra el `.iss`: si se desincronizan, nada
falla al compilar, falla en la máquina del alumno.

### 4. Los proyectos `.edufem` se abren con doble clic

- `tools/make_icon.py` genera además `resources/icons/edufem_doc.ico`: el mismo emblema
  birrete-malla sobre una hoja con la esquina doblada. Se instala como archivo suelto en
  `{app}` porque el Explorador lee la ruta que apunta el registro, no el interior del `.exe`.
- El `.iss` registra el ProgID `EduFEM.Proyecto.1` con su icono y su
  `shell\open\command "%1"`, más `OpenWithProgids` y `Applications\EduFEM.exe\SupportedTypes`
  para que aparezca en *Abrir con*. Todo bajo `HKA`, que con instalación por usuario resuelve
  a `HKCU`. Es una **tarea opcional** del asistente, marcada por defecto.
- `main.py` acepta la ruta como argumento y `MainWindow.__init__(project_path=...)` la abre.
  La carga se difiere con `after()`: dentro del constructor, un error dejaría el `messagebox`
  sin ventana padre y el canvas todavía no conoce su tamaño real para `fit_view`.

### 5. El asistente

- **Imágenes propias**: `tools/make_installer_images.py` genera `installer/assets/wizard*.bmp`
  (panel vertical con el emblema, el nombre y la barra JET; sello de cabecera sobre blanco) en
  la serie de tamaños que Windows elige según el DPI. BMP de 24 bits, que es lo único que Inno
  lee.
- **Licencia MIT** en su propia página, e instalada como `{app}\LICENCIA.txt`.
- Texto de bienvenida que dice lo que importa: no hace falta Python, ni MiKTeX, ni internet,
  ni permisos de administrador.
- `MinVersion=10.0` y `ArchitecturesAllowed=x64compatible`.
- `SetupLogging=yes`: deja un registro en `%TEMP%`, que es lo único que permite diagnosticar
  una instalación fallida en la máquina de otro.
- `App Paths` registrado: Win+R ▸ `edufem` abre el programa.
- Desinstalación que borra `{app}\texlive` y el caché de teoría regenerable, y **no toca** los
  `.edufem` del alumno ni su lista de recientes.

### 6. Un ejecutable 3,9 MB más chico

Comparando los `hooks` de PyInstaller contra el build del 2026-09-08 apareció `lxml` en el
bundle. No está en `requirements.txt` y ningún módulo de EduFEM lo importa: entra porque
`fontTools.misc.etree` lo prefiere si está instalado en el entorno y, si no, cae a
`xml.etree` (su comportamiento documentado). Excluido en `build.spec` junto con `bs4`.

## Medido

| | Antes (2026-09-08) | Ahora |
|---|---|---|
| `dist/EduFEM.exe` | 106,2 MB | 106,4 MB |
| `installer/Output/EduFEM-Setup.exe` | 126,2 MB | 126,4 MB |
| Instalado en `{app}` | — | 156,4 MiB |

El entregable quedó prácticamente igual pese a sumar la licencia, el icono de documento y
1,5 MB de imágenes del asistente: lo compensan la exclusión de `lxml` (−3,7 MB) y el cambio de
`lzma2/max` a `lzma2/ultra64`, que se midió contra la alternativa (124,0 contra 124,2 MiB a
favor de ultra64, con la misma duración de compilación, ~60 s).

## Verificado en este equipo

Se instaló el paquete en modo silencioso (`/VERYSILENT /TASKS=desktopicon,asociar`) sobre la
instalación que había, y se comprobó: los cuatro archivos y la carpeta `texlive` en `{app}`;
los accesos directos del Escritorio y del menú Inicio, **ambos con el AppUserModelID**
`Sucullani.EduFEM.Aplicacion.1` y con el comentario acentuado (lo que confirma que el BOM del
`.iss` funciona); el ProgID, el icono y el comando `"%1"` de la extensión `.edufem` en el
registro; `App Paths`; y la entrada en Aplicaciones. Aparte, un smoke con Tk real confirmó que
`MainWindow(project_path=...)` abre el modelo y actualiza el título.

**Un detalle de la actualización**: agregar `ArchitecturesInstallIn64BitMode` hace que Inno no
reutilice el desinstalador de una instalación anterior hecha en modo 32 bits, así que en un
equipo que venía de un paquete previo queda un `unins000.*` huérfano de ~4 MB (se borró a mano
acá). Es por única vez: la segunda instalación ya reutilizó `unins001`. En una instalación
nueva no ocurre. El acceso directo que cambió de nombre sí se limpia solo, con `[InstallDelete]`.

## Decisiones

- **La carpeta portable pasa a ser opcional.** Se armaba en cada build y el autor no
  distinguía cuál de las cuatro carpetas grandes era el entregable. Ahora `build_all.ps1`
  tiene cuatro pasos y `dist/` queda con **solo `EduFEM.exe`**, que es lo que el instalador
  empaqueta adentro; la carpeta autónoma se arma con `build_all.ps1 -Portable`. Motivo: con el
  TeX embebido son 4180 archivos y ~50 MB duplicados de `vendor/texlive`, y el instalador hace
  todo lo que ella no hace (accesos directos, asociación, desinstalador). La capacidad no se
  quitó, cambió el valor por defecto. `docs/MAPA.md` §2 tiene ahora una tabla de cuál es cuál
  y cuál se puede borrar.
- **Sin firma de código**, como estaba decidido. El aviso de SmartScreen aparece una vez, en
  el `setup.exe`, y el LEEME explica cómo seguir.
- **Instalación por usuario, sin UAC**, como estaba decidido. No se agregó la opción «para
  todos los usuarios»: complicaría la lógica de la carpeta ASCII sin beneficio para el caso de
  uso.

## Trampas encontradas (para el próximo que toque el `.iss`)

- Inno lee como etiqueta de sección **toda línea cuyo primer carácter no blanco sea `[`**. Un
  arreglo de `FmtMessage` al principio de una línea aborta la compilación con «Invalid section
  tag». Hay un test que lo verifica.
- El `.iss` va en **UTF-8 con BOM**. Sin BOM, Inno 6 lo lee como ANSI y los acentos de los
  mensajes salen rotos. También verificado por test.
- `MB` y `MiB`: el Explorador y PowerShell informan MiB. Los tamaños de esta nota son MB
  (10⁶), que es como los reporta el resto del repo.

## Qué queda para el autor

1. **Instalar el paquete nuevo en un equipo limpio**, idealmente sin MiKTeX y con un usuario
   de Windows con tilde o espacio en el nombre (el asistente debe proponer
   `C:\ProgramData\EduFEM`). Comprobar: accesos directos, icono anclado a la barra de tareas,
   doble clic sobre un `.edufem`, Memoria de Cálculo en PDF, desinstalación.
2. **Decidir si sube `MyAppVersion`** más allá de 1.0.0 antes de la defensa.
3. Los pendientes visuales previos siguen abiertos (ver `docs/rutina/BACKLOG.md`).
