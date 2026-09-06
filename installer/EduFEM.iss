; ============================================================
;  Instalador de EduFEM (Inno Setup)
; ------------------------------------------------------------
;  Genera un unico EduFEM-Setup.exe que instala el programa,
;  crea accesos directos (Inicio + Escritorio) con el icono
;  propio y registra un desinstalador.
;
;  Instalacion POR USUARIO (PrivilegesRequired=lowest): no pide
;  permisos de administrador. El .exe se instala "limpio" (sin
;  marca de internet), por lo que abrirlo desde el icono NO
;  dispara el aviso de SmartScreen.
;
;  Compilar:
;    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\EduFEM.iss
;  Salida:
;    installer\Output\EduFEM-Setup.exe
; ============================================================

#define MyAppName "EduFEM"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tesis de Grado"
#define MyAppExeName "EduFEM.exe"
#define MyAppURL "https://github.com/Sucullani/SoftwareED"

[Setup]
AppId={{9C4E2A18-7B3D-4F6A-A1C9-3E5D8B2F0A71}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=EduFEM-Setup
SetupIconFile=..\resources\icons\edufem.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Instalador de {#MyAppName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\EduFEM.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist_extra\LEEME.txt"; DestDir: "{app}"; DestName: "LEEME.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Leeme (instrucciones)"; Filename: "{app}\LEEME.txt"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
