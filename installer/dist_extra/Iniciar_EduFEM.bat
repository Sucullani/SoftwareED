@echo off
rem ============================================================
rem  Iniciar EduFEM  -  Lanzador
rem ------------------------------------------------------------
rem  Abre EduFEM.exe evitando el aviso de SmartScreen
rem  ("Windows protegio su PC").
rem
rem  USO: doble clic en este archivo.
rem  Manten "Iniciar EduFEM.bat" en la MISMA carpeta que
rem  EduFEM.exe. No requiere instalacion, permisos de
rem  administrador ni configuracion alguna.
rem ============================================================

setlocal
set "EDUFEM_EXE=%~dp0EduFEM.exe"

if not exist "%EDUFEM_EXE%" (
  echo.
  echo   No se encontro EduFEM.exe en esta carpeta:
  echo     %~dp0
  echo.
  echo   Coloca "Iniciar EduFEM.bat" junto a EduFEM.exe.
  echo.
  pause
  exit /b 1
)

rem  1) Quita la marca de "descargado de internet" (si la tuviera).
rem  2) Lanza EduFEM con CreateProcess (UseShellExecute = $false):
rem     ese metodo NO dispara el muro de SmartScreen que aparece
rem     al hacer doble clic sobre el .exe desde el Explorador.
powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command "Unblock-File -LiteralPath $env:EDUFEM_EXE -ErrorAction SilentlyContinue; $psi = New-Object System.Diagnostics.ProcessStartInfo; $psi.FileName = $env:EDUFEM_EXE; $psi.WorkingDirectory = Split-Path $env:EDUFEM_EXE; $psi.UseShellExecute = $false; [System.Diagnostics.Process]::Start($psi) | Out-Null"

endlocal
exit /b 0
