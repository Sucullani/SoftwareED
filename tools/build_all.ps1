# ============================================================
#  build_all.ps1  -  Pipeline de empaquetado de EduFEM
# ------------------------------------------------------------
#  Hace TODA la cadena en un solo paso:
#    0) TeX Live recortado           (tools/build_texlive.py -> vendor/texlive,
#                                     solo si no existe; necesita internet)
#    1) Regenera el icono            (tools/make_icon.py)
#    2) Compila el .exe              (PyInstaller, onefile)
#    3) Compila el instalador        (Inno Setup -> EduFEM-Setup.exe,
#                                     incluye vendor/texlive como {app}\texlive)
#
#  Usar despues de tocar el icono, el codigo o el .iss:
#    powershell -ExecutionPolicy Bypass -File tools\build_all.ps1
#
#  Entregable final: installer\Output\EduFEM-Setup.exe
#  Carpeta portable equivalente: dist\EduFEM.exe + vendor\texlive copiada
#  como dist\texlive (la app busca "texlive" junto al .exe).
# ============================================================

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot          # raiz del repo (.. de tools/)
Set-Location $root

$venv = Join-Path $root ".venv\Scripts\python.exe"
$iscc = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) { $iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" }

$texlive = Join-Path $root "vendor\texlive\bin\windows\pdflatex.exe"
Write-Host "[0/4] TeX Live embebido (vendor\texlive)..." -ForegroundColor Cyan
if (Test-Path $texlive) {
    Write-Host "      ya existe; se reutiliza (para rehacerlo: python tools\build_texlive.py --force)"
} else {
    & $venv (Join-Path $root "tools\build_texlive.py")
    if ($LASTEXITCODE -ne 0) { throw "build_texlive.py fallo (ver salida)" }
}

Write-Host "[1/4] Generando icono (make_icon.py)..." -ForegroundColor Cyan
& $venv (Join-Path $root "tools\make_icon.py")

Write-Host "[2/4] Compilando el .exe (PyInstaller, ~varios minutos)..." -ForegroundColor Cyan
& $venv -m PyInstaller --noconfirm (Join-Path $root "build.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller fallo" }

Write-Host "[3/4] Compilando el instalador (Inno Setup)..." -ForegroundColor Cyan
if (Test-Path $iscc) {
    & $iscc (Join-Path $root "installer\EduFEM.iss")
    if ($LASTEXITCODE -ne 0) { throw "ISCC fallo" }
    Write-Host "OK -> installer\Output\EduFEM-Setup.exe" -ForegroundColor Green
} else {
    Write-Warning "ISCC no encontrado. Instala Inno Setup (winget install JRSoftware.InnoSetup) o ajusta la ruta."
    Write-Host "El .exe quedo en dist\EduFEM.exe (sin instalador)." -ForegroundColor Yellow
}
