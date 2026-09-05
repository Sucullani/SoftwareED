@echo off
rem ============================================================
rem  Crear acceso directo de EduFEM en el Escritorio
rem ------------------------------------------------------------
rem  Doble clic UNA VEZ. Crea el icono "EduFEM" en tu Escritorio,
rem  que abre el programa con un clic y SIN avisos de seguridad.
rem  Manten esta carpeta intacta (EduFEM.exe + "Iniciar EduFEM.bat"
rem  + este archivo deben estar juntos).
rem ============================================================

setlocal
set "LAUNCHER=%~dp0Iniciar EduFEM.bat"
set "ICON=%~dp0EduFEM.exe"

if not exist "%ICON%" (
  echo.
  echo   No se encontro EduFEM.exe en esta carpeta.
  echo   Coloca este archivo junto a EduFEM.exe e "Iniciar EduFEM.bat".
  echo.
  pause
  exit /b 1
)
if not exist "%LAUNCHER%" (
  echo.
  echo   No se encontro "Iniciar EduFEM.bat" en esta carpeta.
  echo.
  pause
  exit /b 1
)

rem Crea el .lnk en el Escritorio: apunta al launcher (que abre EduFEM por
rem CreateProcess, sin SmartScreen), con el icono del .exe y ventana minimizada.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=[Environment]::GetFolderPath('Desktop'); $w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut((Join-Path $d 'EduFEM.lnk')); $s.TargetPath=$env:LAUNCHER; $s.WorkingDirectory=(Split-Path $env:LAUNCHER); $s.IconLocation=($env:ICON + ',0'); $s.WindowStyle=7; $s.Description='EduFEM - Software Educativo de Elementos Finitos'; $s.Save()"

echo.
echo   Listo: se creo el icono "EduFEM" en tu Escritorio.
echo   Abri el programa con doble clic en ese icono.
echo.
pause
exit /b 0
