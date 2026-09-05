# ============================================================
#  build_all.ps1  -  Pipeline de empaquetado de EduFEM
# ------------------------------------------------------------
#  Hace TODA la cadena en un solo paso:
#    1) Regenera el icono            (tools/make_icon.py)
#    2) Compila el .exe              (PyInstaller, onefile)
#    3) Compila el instalador        (Inno Setup -> EduFEM-Setup.exe)
#
#  Usar despues de tocar el icono, el codigo o el .iss:
#    powershell -ExecutionPolicy Bypass -File tools\build_all.ps1
#
#  Entregable final: installer\Output\EduFEM-Setup.exe
# ============================================================

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot          # raiz del repo (.. de tools/)
Set-Location $root

$venv = Join-Path $root ".venv\Scripts\python.exe"
$iscc = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) { $iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" }

Write-Host "[1/3] Generando icono (make_icon.py)..." -ForegroundColor Cyan
& $venv (Join-Path $root "tools\make_icon.py")

Write-Host "[2/3] Compilando el .exe (PyInstaller, ~varios minutos)..." -ForegroundColor Cyan
& $venv -m PyInstaller --noconfirm (Join-Path $root "build.spec")

Write-Host "[3/3] Compilando el instalador (Inno Setup)..." -ForegroundColor Cyan
if (Test-Path $iscc) {
    & $iscc (Join-Path $root "installer\EduFEM.iss")
    Write-Host "OK -> installer\Output\EduFEM-Setup.exe" -ForegroundColor Green
} else {
    Write-Warning "ISCC no encontrado. Instala Inno Setup (winget install JRSoftware.InnoSetup) o ajusta la ruta."
    Write-Host "El .exe quedo en dist\EduFEM.exe (sin instalador)." -ForegroundColor Yellow
}
