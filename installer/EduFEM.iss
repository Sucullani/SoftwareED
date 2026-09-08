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
;  Incluye un TeX Live recortado (vendor\texlive, generado por
;  tools\build_texlive.py) como {app}\texlive: la Memoria de
;  Calculo y la Teoria se compilan sin MiKTeX, sin internet y sin
;  dialogos. TeX Live no resuelve rutas con tildes, asi que si el
;  perfil del usuario las tiene (C:\Users\Jose Perez\...), la
;  carpeta por defecto pasa a C:\ProgramData\EduFEM (escribible
;  sin administrador; mismo criterio que TinyTeX). Ver [Code].
;
;  Compilar (requiere vendor\texlive; con /DNOTEX se omite el TeX):
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
DefaultDirName={code:DefaultInstallDir}
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
#ifndef NOTEX
  #if !FileExists(SourcePath + "\..\vendor\texlive\bin\windows\pdflatex.exe")
    #error Falta vendor\texlive (TeX Live recortado). Correr: python tools\build_texlive.py  (o compilar con /DNOTEX)
  #endif
; TeX Live recortado: ~50 MB, solo pdflatex + los paquetes de la Memoria/Teoria.
Source: "..\vendor\texlive\*"; DestDir: "{app}\texlive"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif

[UninstallDelete]
; Archivos que pdflatex pueda generar dentro de la carpeta (caches) y el
; cache de teoria del usuario no se tocan; solo lo instalado bajo {app}.
Type: filesandordirs; Name: "{app}\texlive"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Leeme (instrucciones)"; Filename: "{app}\LEEME.txt"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// TeX Live (carpeta texlive) no resuelve rutas con caracteres fuera de ASCII y
// sus scripts tampoco toleran espacios. Si el perfil del usuario los tiene, la
// carpeta por defecto pasa a {commonappdata}\EduFEM (C:\ProgramData\EduFEM),
// que un usuario sin privilegios puede crear. Mismo criterio que TinyTeX.
function IsAsciiNoSpaces(const S: String): Boolean;
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

function DefaultInstallDir(Param: String): String;
begin
  Result := ExpandConstant('{localappdata}\Programs\{#MyAppName}');
  if not IsAsciiNoSpaces(Result) then
    Result := ExpandConstant('{commonappdata}\{#MyAppName}');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = wpSelectDir) and (not IsAsciiNoSpaces(WizardDirValue)) then
    Result := MsgBox('La carpeta elegida tiene espacios o tildes:' + #13#10 +
      WizardDirValue + #13#10 + #13#10 +
      'La Memoria de Calculo (PDF) puede fallar en esa ruta. Se recomienda instalar en ' +
      ExpandConstant('{commonappdata}\{#MyAppName}') + '.' + #13#10 + #13#10 +
      'Continuar de todas formas?', mbConfirmation, MB_YESNO) = IDYES;
end;
