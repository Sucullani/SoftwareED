---
paths:
  - "build.spec"
  - "installer/**"
  - "tools/**/*.py"
  - "tools/*.ps1"
  - "main.py"
  - "config/settings.py"
---

# Empaquetado y distribución

Canon: **[docs/convenciones/arquitectura.md](../../docs/convenciones/arquitectura.md)** ·
rutas frágiles: **[docs/MAPA.md](../../docs/MAPA.md)**.

**El entregable es uno solo: `installer/Output/EduFEM-Setup.exe`.** Lo arma
`tools/build_all.ps1` en cuatro pasos (TeX → iconos e imágenes → `.exe` → instalador).

Lo demás es maquinaria y **no se distribuye**: `dist/EduFEM/` es lo que el instalador
empaqueta adentro, `vendor/texlive` el TeX embebido, `build/` el caché de PyInstaller (que se
puede borrar en cualquier momento). La **carpeta portable** —`dist/EduFEM/` con una copia del
TeX, el LEEME y los lanzadores `.bat`— solo se arma con `build_all.ps1 -Portable`: son ~57 MB
duplicados de `vendor/texlive` y no da accesos directos, asociación ni desinstalador.

## Ejecutable

- **Todo acceso a un recurso pasa por `config.settings.resource_path(*parts)`**, que resuelve
  vía `sys._MEIPASS` en el `.exe` y vía la raíz del repo en dev. Una ruta relativa al CWD
  funciona en desarrollo y falla en el ejecutable. `gui/fonts_loader.py::_resources_root` es su
  espejo: si tocás uno, tocá el otro.
- **Los `education/mod*.py` van sí o sí en `hiddenimports`** (el spec los toma por glob):
  `module_launcher.open_module` los carga con `importlib.import_module` y el analizador
  estático de PyInstaller no los ve. Sin esa entrada el `.exe` abre pero cada módulo falla.
  Cualquier import dinámico nuevo replica el patrón.
- Modo **onedir**: `dist/EduFEM/` = lanzador `EduFEM.exe` + `_internal/`. El instalador la
  copia entera a `{app}` con `recursesubdirs`, así que el entregable sigue siendo un archivo.
  **No volver a onefile.** Medido el 2026-09-10 en este equipo: el autoextraíble arrancaba en
  10,9 s en frío y 11,9-14,8 s las veces siguientes —re-extrae ~190 MB a `%TEMP%` en *cada*
  arranque, los revisa el antivirus y corre en dos procesos—, contra 7,0 s y 3,0-3,5 s de
  onedir; y cada cierre anormal (crash, Administrador de tareas) dejaba una carpeta
  `%TEMP%\_MEI*` de 189 MB. La única ventaja de onefile no aplicaba: el entregable es el
  instalador, y la carpeta portable ya era una carpeta porque el TeX va al lado del `.exe`.
  `tests/test_distribucion.py` ata el `COLLECT` del spec con el `Source:` del `.iss`.
- **Los `filedialog` declaran `initialdir`** (`config/user_paths.py`). El acceso directo del
  instalador arranca en `{app}`: sin `initialdir`, el primer «Guardar Como» del alumno deja su
  modelo dentro de la carpeta del programa, en `AppData`.
- **El `.exe` lleva datos de versión** (`version=` en el `EXE` del spec, generado en
  `build/edufem_version_info.txt` a partir de `APP_VERSION`). Sin ese recurso Windows lo
  muestra sin Descripción ni Empresa en Propiedades y los filtros de reputación lo castigan.

## Versión: una sola fuente

`config/settings.py::APP_VERSION`. La leen `build.spec` (regex, para no importar la app
durante el `Analysis`) y el preprocesador de `installer/EduFEM.iss`. **No escribir la versión
en el `.iss`.** El único lugar que la repite a mano es el texto de
`installer/dist_extra/LEEME.txt`: al subir la versión, tocar los dos.

## TeX Live embebido

- `tools/build_texlive.py` genera `vendor/texlive` (gitignored, ~57 MB en 4180 archivos, solo pdflatex + los
  paquetes de la Memoria/Teoría) y el instalador lo copia a `{app}\texlive`. Va **junto** al
  `.exe`, nunca dentro del bundle (4180 archivos que no tienen por qué pasar por el
  analizador de PyInstaller).
- `education/components/latex_runtime.py` lo resuelve (env `EDUFEM_TEXLIVE_DIR` → `texlive/`
  hermana del `.exe` o `vendor/texlive` en dev → PATH, donde MiKTeX recibe
  `-enable-installer`). Sin ninguno, la Memoria muestra el diálogo con botón de descarga. Las
  fórmulas in-app siguen en mathtext.
- **El TeX embebido debe vivir en una ruta ASCII sin espacios**: el `.iss` elige
  `C:\ProgramData\EduFEM` cuando el perfil del usuario tiene tildes o espacios, y la app
  compila en un temporal ASCII (`latex_runtime.safe_workdir_root`).

## Instalador (`installer/EduFEM.iss`)

Inno Setup 6, **por usuario** (`PrivilegesRequired=lowest`: sin UAC) y **sin firma de código**
(decisión tomada). Lo que el archivo ya resuelve y no hay que deshacer:

- **`AppId` no se toca**: es lo que hace que una versión nueva actualice la instalada en vez de
  duplicarla en Aplicaciones.
- **`AppMutex` + `CloseApplications`**: el asistente detecta EduFEM abierto y ofrece cerrarlo.
  El mutex lo crea `main.py`; el nombre vive en `config/settings.py::APP_MUTEX_NAME`.
- **`AppUserModelID` en los accesos directos** = `config/settings.py::APP_USER_MODEL_ID`, que
  `main.py` fija en el proceso. Si difieren, el icono anclado a la barra de tareas se
  desprende del acceso directo. Son dos archivos: cambiá los dos.
- **Asociación de `.edufem`** (tarea opcional `asociar`): ProgID `EduFEM.Proyecto.1`, icono
  `{app}\edufem_doc.ico` (archivo suelto: el Explorador lee la ruta del registro, no el
  interior del `.exe`) y `shell\open\command` con `"%1"`. **`main.py` tiene que seguir
  aceptando la ruta como argumento**, o la asociación abre la app vacía.
- **Desinstalación**: borra `{app}\texlive`, `{app}\_internal` y el caché de teoría
  (`~\.edufem\theory_cache`). **No borra** los `.edufem` del alumno ni `~\.edufem\recent.json`.
  Los flags del registro importan: `uninsdeletekey` va en la clave **raíz**
  (`Applications\EduFEM.exe`), no en una hoja, y las claves de la extensión llevan
  `uninsdeletekeyifempty` para no dejar cáscaras vacías. Verificado con un ciclo real
  instalar → desinstalar → instalar.
- **Al probar el instalador en modo silencioso, dejá ~30 s entre desinstalar y reinstalar.**
  Si no, el antivirus todavía tiene tomado el `EduFEM.exe` recién escrito, `MoveFile` falla con
  «Acceso denegado» y `/SUPPRESSMSGBOXES` auto-responde **Anular** al diálogo de reintento: la
  instalación se revierte entera y devuelve código 5. El diagnóstico está en el log que deja
  `SetupLogging=yes` (`%TEMP%\Setup Log *.txt`).
- **Cuidado con Pascal Script**: Inno lee como etiqueta de sección **toda línea cuyo primer
  carácter no blanco sea `[`**. Un arreglo de `FmtMessage` al principio de una línea aborta la
  compilación con «Invalid section tag».
- **El `.iss` se guarda en UTF-8 con BOM.** Sin BOM, Inno 6 lo lee como ANSI y los acentos de
  los mensajes salen rotos.
- `/DNOTEX` compila el instalador sin el TeX embebido: sirve para validar sintaxis rápido.

## Recursos generados

`tools/make_icon.py` → `resources/icons/edufem.ico` (app) y `edufem_doc.ico` (archivos
`.edufem`). `tools/make_installer_images.py` → `installer/assets/wizard*.bmp` (BMP de 24 bits;
Inno no lee PNG), en la serie de tamaños que Inno elige según el DPI de la pantalla.
