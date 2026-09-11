; ============================================================
;  Instalador de EduFEM  --  Inno Setup 6
; ------------------------------------------------------------
;  Produce un unico EduFEM-Setup.exe que deja el programa listo
;  para usar: no requiere Python, ni MiKTeX, ni conexion a
;  internet, ni permisos de administrador.
;
;  Que hace, y por que:
;
;  * Instala POR USUARIO (PrivilegesRequired=lowest): sin UAC.
;    El .exe queda "limpio" (sin marca de internet), asi que
;    abrirlo desde el icono NO dispara SmartScreen.
;  * Lleva un TeX Live recortado (vendor\texlive, ~57 MB, lo
;    genera tools\build_texlive.py) como {app}\texlive. Es lo
;    que compila la Memoria de Calculo y la Teoria en PDF.
;    TeX Live no resuelve rutas con tildes ni espacios: por eso
;    la carpeta por defecto pasa a C:\ProgramData\EduFEM cuando
;    el perfil del usuario los tiene. Ver [Code].
;  * Asocia la extension .edufem con su propio icono, de modo
;    que un proyecto se abre con doble clic. main.py recibe la
;    ruta como argumento.
;  * Declara AppUserModelID en los accesos directos, el mismo
;    que el proceso fija en main.py: sin eso, el icono anclado
;    a la barra de tareas se desprende del acceso directo.
;  * Declara AppMutex: si EduFEM esta abierto, el instalador
;    ofrece cerrarlo en vez de copiar sobre un .exe en uso.
;  * Registra App Paths, de modo que Win+R -> "edufem" abre el
;    programa.
;
;  La version NO se escribe aca: se lee de config\settings.py
;  (APP_VERSION), que es la unica fuente. Ver el bloque ISPP.
;
;  Compilar (requiere dist\EduFEM\ y vendor\texlive):
;    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\EduFEM.iss
;  Con /DNOTEX se omite el TeX embebido (build de prueba).
;  Salida:
;    installer\Output\EduFEM-Setup.exe
;
;  La cadena completa (TeX + icono + imagenes + .exe + esto) la
;  corre tools\build_all.ps1.
; ============================================================

; ─── Version: unica fuente = config\settings.py ────────────────────────────
; El preprocesador lee el archivo linea por linea y toma el valor entre
; comillas de la asignacion APP_VERSION. Se exige que empiece en la columna 1
; para no confundirla con la mencion que hace el comentario de ese archivo.
#define SettingsFile AddBackslash(SourcePath) + "..\config\settings.py"
#define MyAppVersion ""
#define FileHandle
#define FileLine

#sub LeerLineaDeVersion
  #expr FileLine = FileRead(FileHandle)
  #if (MyAppVersion == "") && (Pos("APP_VERSION", FileLine) == 1)
    #expr MyAppVersion = Copy(FileLine, Pos('"', FileLine) + 1)
    #expr MyAppVersion = Copy(MyAppVersion, 1, Pos('"', MyAppVersion) - 1)
  #endif
#endsub

#expr FileHandle = FileOpen(SettingsFile)
#if !FileHandle
  #error No se pudo abrir config\settings.py para leer APP_VERSION.
#endif
#for {0; !FileEof(FileHandle); 0} LeerLineaDeVersion
#expr FileClose(FileHandle)
#if MyAppVersion == ""
  #error No se encontro la asignacion APP_VERSION en config\settings.py
#endif

#define MyAppName "EduFEM"
#define MyAppLongName "EduFEM - Software Educativo de Elementos Finitos"
#define MyAppPublisher "Hedy Yhassmany Oyola Sucullani"
#define MyAppExeName "EduFEM.exe"
#define MyAppDocIcon "edufem_doc.ico"
#define MyAppURL "https://github.com/Sucullani/SoftwareED"
; Identificadores compartidos con config\settings.py (APP_USER_MODEL_ID y
; APP_MUTEX_NAME): si cambia uno, cambian los dos.
#define MyAppUserModelId "Sucullani.EduFEM.Aplicacion.1"
#define MyAppMutex "EduFEM.InstanciaEnEjecucion"
; Tipo de archivo de los proyectos.
#define ProjExt ".edufem"
#define ProjProgId "EduFEM.Proyecto.1"

[Setup]
; AppId identifica al producto entre versiones: NO cambiarlo, es lo que hace
; que una version nueva actualice la instalada en vez de duplicarla.
AppId={{9C4E2A18-7B3D-4F6A-A1C9-3E5D8B2F0A71}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
AppCopyright=Copyright (C) 2026 {#MyAppPublisher} - Licencia MIT
AppComments={#MyAppLongName}
AppReadmeFile={app}\LEEME.txt

; Requisitos. El .exe es de 64 bits y la app usa APIs de Windows 10 en
; adelante; declararlo evita una instalacion que despues no arranca.
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Instalacion por usuario: sin UAC, sin privilegios de administrador.
PrivilegesRequired=lowest
DefaultDirName={code:CarpetaPorDefecto}
DisableDirPage=auto
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
UsePreviousAppDir=yes

; No copiar sobre un EduFEM abierto: con AppMutex el asistente detecta la
; instancia en ejecucion (main.py crea ese mutex) y ofrece cerrarla.
AppMutex={#MyAppMutex}
SetupMutex={#MyAppName}SetupMutex
CloseApplications=yes
RestartApplications=no

; El instalador registra un tipo de archivo: hay que avisarle al Explorador.
ChangesAssociations=yes

; Desinstalacion
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}

; Aspecto del asistente
WizardStyle=modern
DisableWelcomePage=no
SetupIconFile=..\resources\icons\edufem.ico
WizardImageFile=assets\wizard-164x314.bmp,assets\wizard-192x386.bmp,assets\wizard-246x459.bmp,assets\wizard-328x604.bmp
WizardSmallImageFile=assets\wizard-small-55x55.bmp,assets\wizard-small-83x80.bmp,assets\wizard-small-110x106.bmp,assets\wizard-small-138x140.bmp,assets\wizard-small-164x161.bmp
LicenseFile=..\LICENSE

; Salida y compresion. lzma2/ultra64 tarda mas en comprimir pero el
; entregable viaja en pendrive: el tamano importa mas que el tiempo de build.
OutputDir=Output
OutputBaseFilename=EduFEM-Setup
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
InternalCompressLevel=max

; Deja un log en %TEMP% (setup-log-*.txt): es lo unico que permite
; diagnosticar una instalacion fallida en la maquina de otro.
SetupLogging=yes

; Datos de version del propio EduFEM-Setup.exe.
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador de {#MyAppName} {#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[CustomMessages]
spanish.GrupoIntegracion=Integración con Windows:
spanish.TareaAsociar=&Asociar los archivos .edufem con EduFEM
spanish.VerGuia=Ver la &guía de uso
spanish.ComentarioApp=Analizar estructuras 2D por el Método de los Elementos Finitos
spanish.ComentarioGuia=Guía de uso, requisitos y solución de problemas
spanish.TipoProyecto=Proyecto de EduFEM
spanish.VerboAbrir=&Abrir con EduFEM
spanish.RutaConEspacios=La carpeta elegida tiene espacios o caracteres con tilde:%n%n%1%n%nLa Memoria de Cálculo en PDF necesita compilar LaTeX y puede fallar en una ruta así. Se recomienda instalar en:%n%n%2%n%n¿Continuar de todas formas?

[Messages]
spanish.WelcomeLabel2=Este asistente instalará [name/ver] en su equipo.%n%nNo hace falta instalar nada más: EduFEM incluye el intérprete de Python, todas sus bibliotecas y la distribución LaTeX que genera la Memoria de Cálculo en PDF. No requiere conexión a internet ni permisos de administrador.%n%nSe recomienda cerrar las demás aplicaciones antes de continuar.
spanish.BeveledLabel=EduFEM - Trabajo de tesis de grado

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "asociar"; Description: "{cm:TareaAsociar}"; GroupDescription: "{cm:GrupoIntegracion}"

[Files]
; Carpeta onedir completa: el lanzador EduFEM.exe y su carpeta _internal con
; el interprete, las bibliotecas y resources\. Es un solo entregable igual
; --este instalador--, pero el programa arranca en ~3 s en vez de ~12: un
; onefile se re-extrae entero a %TEMP% en CADA arranque. Ver build.spec.
Source: "..\dist\EduFEM\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Icono de los proyectos: tiene que quedar como archivo suelto porque el
; Explorador lee la ruta que apunta el registro, no el interior del .exe.
Source: "..\resources\icons\{#MyAppDocIcon}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist_extra\LEEME.txt"; DestDir: "{app}"; DestName: "LEEME.txt"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; DestName: "LICENCIA.txt"; Flags: ignoreversion
#ifndef NOTEX
  #if !FileExists(AddBackslash(SourcePath) + "..\vendor\texlive\bin\windows\pdflatex.exe")
    #error Falta vendor\texlive (TeX Live recortado). Correr: python tools\build_texlive.py  (o compilar con /DNOTEX)
  #endif
; TeX Live recortado: solo pdflatex y los paquetes que usan la Memoria y la Teoria.
Source: "..\vendor\texlive\*"; DestDir: "{app}\texlive"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif

[InstallDelete]
; Rastros de versiones anteriores. Inno no renombra los accesos directos al
; actualizar: si no se borra el viejo, el menu Inicio queda con los dos.
Type: files; Name: "{group}\Leeme (instrucciones).lnk"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{cm:ComentarioApp}"; AppUserModelID: "{#MyAppUserModelId}"
Name: "{group}\{#MyAppName} - Guía de uso"; Filename: "{app}\LEEME.txt"; Comment: "{cm:ComentarioGuia}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{cm:ComentarioApp}"; AppUserModelID: "{#MyAppUserModelId}"; Tasks: desktopicon

[Registry]
; --- Tipo de archivo .edufem -------------------------------------------
; HKA con PrivilegesRequired=lowest resuelve a HKCU: la asociacion es del
; usuario que instala, que es justo lo que corresponde sin admin.
Root: HKA; Subkey: "Software\Classes\{#ProjProgId}"; ValueType: string; ValueName: ""; ValueData: "{cm:TipoProyecto}"; Flags: uninsdeletekey; Tasks: asociar
Root: HKA; Subkey: "Software\Classes\{#ProjProgId}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppDocIcon}"; Tasks: asociar
Root: HKA; Subkey: "Software\Classes\{#ProjProgId}\shell\open"; ValueType: string; ValueName: ""; ValueData: "{cm:VerboAbrir}"; Tasks: asociar
Root: HKA; Subkey: "Software\Classes\{#ProjProgId}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: asociar
; La extension apunta al ProgID. Solo se borra ESE valor al desinstalar: la
; clave de la extension puede tener entradas de otros programas.
; `uninsdeletekeyifempty` remata: si nadie mas dejo nada, la clave se va en vez
; de quedar como un cascaron vacio. Inno desinstala las entradas en orden
; inverso, asi que OpenWithProgids se vacia ANTES de evaluar la clave padre.
Root: HKA; Subkey: "Software\Classes\{#ProjExt}"; ValueType: string; ValueName: ""; ValueData: "{#ProjProgId}"; Flags: uninsdeletevalue uninsdeletekeyifempty; Tasks: asociar
Root: HKA; Subkey: "Software\Classes\{#ProjExt}\OpenWithProgids"; ValueType: string; ValueName: "{#ProjProgId}"; ValueData: ""; Flags: uninsdeletevalue uninsdeletekeyifempty; Tasks: asociar
; --- "Abrir con" del Explorador (independiente de la asociacion) --------
; El `uninsdeletekey` va en la clave RAIZ: puesto en `shell\open\command` solo
; borraba esa hoja y dejaba huerfanos el propio `Applications\EduFEM.exe` y su
; `SupportedTypes`. Esta primera linea no escribe ningun valor (sin ValueType);
; existe para crear la clave y marcarla para el borrado del subarbol entero.
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: "{#ProjExt}"; ValueData: ""
; --- App Paths: Win+R -> "edufem" --------------------------------------
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\{#MyAppExeName}"; ValueType: string; ValueName: "Path"; ValueData: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\LEEME.txt"; Description: "{cm:VerGuia}"; Flags: postinstall shellexec skipifsilent unchecked

[UninstallDelete]
; El TeX embebido escribe archivos auxiliares dentro de su propio arbol, asi
; que la carpeta no queda vacia y hay que borrarla explicitamente.
Type: filesandordirs; Name: "{app}\texlive"
; Idem _internal: el desinstalador borra los 1466 archivos que registro, pero
; cualquier .pyc o cache que Python haya dejado adentro impediria vaciar la
; carpeta. Solo contiene el runtime; nada del alumno vive aca.
Type: filesandordirs; Name: "{app}\_internal"
; Cache de los PDF de teoria: se regenera solo, no es dato del usuario. Los
; proyectos .edufem y la lista de recientes (~\.edufem\recent.json) NO se
; tocan: son del alumno.
Type: filesandordirs; Name: "{%USERPROFILE}\.edufem\theory_cache"
Type: dirifempty; Name: "{app}"

[Code]
// ── Carpeta de instalacion y rutas que LaTeX no soporta ──────────────────
// pdflatex (TeX Live) no resuelve rutas con caracteres fuera de ASCII, y sus
// scripts tampoco toleran espacios. El destino habitual de una instalacion
// por usuario, %LOCALAPPDATA%\Programs, lleva el nombre del perfil: con un
// usuario "Jose Perez" el TeX embebido quedaria inutilizable. En ese caso se
// propone C:\ProgramData\EduFEM, que es ASCII y que un usuario sin
// privilegios puede crear (mismo criterio que TinyTeX).

function EsAsciiSinEspacios(const S: String): Boolean;
var
  I: Integer;
begin
  Result := True;
  for I := 1 to Length(S) do
    if (Ord(S[I]) > 126) or (Ord(S[I]) < 32) or (S[I] = ' ') then
    begin
      Result := False;
      Exit;
    end;
end;

function CarpetaSegura: String;
begin
  Result := ExpandConstant('{commonappdata}\{#MyAppName}');
end;

function CarpetaPorDefecto(Param: String): String;
begin
  Result := ExpandConstant('{localappdata}\Programs\{#MyAppName}');
  if not EsAsciiSinEspacios(Result) then
    Result := CarpetaSegura;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Aviso: String;
begin
  Result := True;
  if (CurPageID = wpSelectDir) and (not EsAsciiSinEspacios(WizardDirValue)) then
  begin
    // El arreglo de FmtMessage va en la misma linea a proposito: Inno lee
    // toda linea que empiece con '[' como una etiqueta de seccion.
    Aviso := FmtMessage(CustomMessage('RutaConEspacios'), [WizardDirValue, CarpetaSegura]);
    Result := MsgBox(Aviso, mbConfirmation, MB_YESNO) = IDYES;
  end;
end;
