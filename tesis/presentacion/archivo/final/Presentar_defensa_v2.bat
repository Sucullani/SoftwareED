@echo off
rem =====================================================================
rem  Abre la version 2 (estilo PowerPoint) de la defensa en una ventana propia,
rem  a pantalla completa y sin barras del navegador (modo aplicacion).
rem  Funciona sin internet. Prefiere Chrome; si no esta, usa Edge (viene con
rem  Windows 10 y 11); si no encuentra ninguno, abre el navegador predeterminado.
rem  Teclas utiles una vez abierta: flechas avanzan, M indice, S vista del
rem  orador, F pantalla completa, ? ayuda.
rem =====================================================================
setlocal EnableDelayedExpansion
set "PAG=%~dp0Defensa_EduFEM_v2.html"
set "URL=file:///!PAG:\=/!"
set "URL=!URL: =%%20!"

set "NAV=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "!NAV!" set "NAV=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "!NAV!" set "NAV=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not exist "!NAV!" set "NAV=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "!NAV!" set "NAV=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"

if exist "!NAV!" (
  start "" "!NAV!" --new-window --start-fullscreen --app="!URL!"
) else (
  start "" "!PAG!"
)
endlocal
