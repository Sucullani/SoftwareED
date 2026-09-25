# ============================================================
#  build_all.ps1  -  Cadena de empaquetado de EduFEM
# ------------------------------------------------------------
#  Produce el entregable unico:  installer\Output\EduFEM-Setup.exe
#
#  Pasos:
#    1) TeX Live recortado   tools\build_texlive.py -> vendor\texlive
#                            (solo si falta; necesita internet)
#    2) Iconos e imagenes    tools\make_icon.py            -> resources\icons\*.ico
#                            tools\make_installer_images.py -> installer\assets\*.bmp
#    3) Ejecutable           PyInstaller (onedir)          -> dist\EduFEM\
#                            + control de lo que entro y avisos de licencia
#                            tools\licencias_terceros.py   -> installer\dist_extra\LICENCIAS-TERCEROS.txt
#    4) Instalador           Inno Setup                    -> EduFEM-Setup.exe
#
#  Uso:
#    powershell -ExecutionPolicy Bypass -File tools\build_all.ps1
#  Opciones:
#    -RehacerTeX     rehace vendor\texlive desde cero
#    -Portable       ademas deja dist\EduFEM\ lista como carpeta portable
#                    (agrega una copia del TeX embebido, el LEEME y los
#                    lanzadores .bat). NO es la via de distribucion: son
#                    ~57 MB duplicados de vendor\texlive, y sin ella
#                    dist\EduFEM\ es exactamente lo que el instalador
#                    empaqueta adentro.
#
#  La version sale de config\settings.py (APP_VERSION): el .exe la lleva en
#  sus datos de version y el .iss la lee del mismo archivo.
# ============================================================

[CmdletBinding()]
param(
    [switch]$RehacerTeX,
    [switch]$Portable
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot          # raiz del repo (.. de tools/)
Set-Location $root

$venv = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venv)) { throw "No se encontro el entorno virtual en $venv" }

$iscc = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) { $iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" }

function Paso([string]$n, [string]$texto) {
    Write-Host ""
    Write-Host "[$n/4] $texto" -ForegroundColor Cyan
}

function MB([string]$path) {
    if (Test-Path $path -PathType Leaf) { return (Get-Item $path).Length / 1MB }
    return ((Get-ChildItem $path -Recurse -File | Measure-Object Length -Sum).Sum) / 1MB
}

# ── 1. TeX Live recortado ───────────────────────────────────────────────────
Paso 1 "TeX Live embebido (vendor\texlive)"
$texlive = Join-Path $root "vendor\texlive\bin\windows\pdflatex.exe"
if ($RehacerTeX) {
    & $venv (Join-Path $root "tools\build_texlive.py") --force
    if ($LASTEXITCODE -ne 0) { throw "build_texlive.py fallo" }
} elseif (Test-Path $texlive) {
    Write-Host "      ya existe; se reutiliza (para rehacerlo: -RehacerTeX)"
} else {
    & $venv (Join-Path $root "tools\build_texlive.py")
    if ($LASTEXITCODE -ne 0) { throw "build_texlive.py fallo" }
}

# ── 2. Iconos e imagenes del asistente ──────────────────────────────────────
Paso 2 "Iconos de la app y del tipo .edufem, imagenes del asistente"
& $venv (Join-Path $root "tools\make_icon.py")
if ($LASTEXITCODE -ne 0) { throw "make_icon.py fallo" }
& $venv (Join-Path $root "tools\make_installer_images.py")
if ($LASTEXITCODE -ne 0) { throw "make_installer_images.py fallo" }

# ── 3. Ejecutable ───────────────────────────────────────────────────────────
# Con dos reintentos. En onedir, el COLLECT vuelca 1466 archivos de golpe en
# dist\EduFEM\_internal\ y el antivirus abre cada uno apenas aparece; si
# engancha alguno, PyInstaller muere con "PermissionError: ... .dll" DESPUES
# de cuatro minutos de analisis. Peor: cuando el archivo a medio escribir se
# borra mientras el antivirus lo tiene abierto, Windows lo deja en "borrado
# pendiente" y el intento siguiente vuelve a fallar en el MISMO archivo, lo
# que hace parecer permanente algo que no lo es. De ahi la pausa antes de
# repetir: le da tiempo a cerrar el handle.
Paso 3 "Ejecutable con PyInstaller (onedir, varios minutos)"
$distApp = Join-Path $root "dist\EduFEM"
$intentos = 3
for ($i = 1; $i -le $intentos; $i++) {
    & $venv -m PyInstaller --noconfirm (Join-Path $root "build.spec")
    if ($LASTEXITCODE -eq 0) { break }
    if ($i -eq $intentos) { throw "PyInstaller fallo en $intentos intentos" }
    Write-Warning "PyInstaller fallo (posible bloqueo del antivirus). Reintento $($i+1)/$intentos..."
    if (Test-Path $distApp) { Remove-Item $distApp -Recurse -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 20
}

# PyMuPDF no puede volver al paquete: es AGPL-3.0 y dejaria el instalador
# entero sujeto a esa licencia. build.spec lo excluye (sigue en el venv para
# dos guiones de la tesis); esto frena el build si alguien quita la exclusion.
$internal = Join-Path $distApp "_internal"
foreach ($prohibido in @("pymupdf", "fitz")) {
    if (Test-Path (Join-Path $internal $prohibido)) {
        throw "El paquete trae '$prohibido' (PyMuPDF, AGPL-3.0): revisar los excludes de build.spec"
    }
}

# Avisos de licencia de lo que efectivamente entro: el guion lee la lista que
# PyInstaller acaba de dejar en build\build\*.toc.
& $venv (Join-Path $root "tools\licencias_terceros.py")
if ($LASTEXITCODE -ne 0) { throw "licencias_terceros.py fallo" }

# ── 4. Instalador ───────────────────────────────────────────────────────────
Paso 4 "Instalador con Inno Setup"
if (-not (Test-Path $iscc)) {
    Write-Warning "ISCC no encontrado. Instalar Inno Setup (winget install JRSoftware.InnoSetup)."
    Write-Host "El programa quedo en dist\EduFEM\ (sin instalador)." -ForegroundColor Yellow
    exit 1
}
& $iscc (Join-Path $root "installer\EduFEM.iss")
if ($LASTEXITCODE -ne 0) { throw "ISCC fallo" }

# ── Extra opcional: carpeta portable ────────────────────────────────────────
# Solo con -Portable. El .exe busca `texlive` a su lado, asi que hay que
# copiarlo. Se borra y se copia entero en vez de espejar con `robocopy /MIR`:
# son unos segundos y no deja margen para que un /MIR mal apuntado borre otra
# cosa.
if ($Portable) {
    Write-Host ""
    Write-Host "[extra] Carpeta portable en dist\EduFEM\ (texlive + LEEME + lanzadores)" -ForegroundColor Cyan
    $portable = Join-Path $root "dist\EduFEM"
    $destinoTeX = Join-Path $portable "texlive"
    if (Test-Path $destinoTeX) { Remove-Item $destinoTeX -Recurse -Force }
    Copy-Item (Join-Path $root "vendor\texlive") $destinoTeX -Recurse -Force
    Copy-Item (Join-Path $root "installer\dist_extra\LEEME.txt") (Join-Path $portable "LEEME.txt") -Force
    Copy-Item (Join-Path $root "installer\dist_extra\Iniciar_EduFEM.bat") (Join-Path $portable "Iniciar EduFEM.bat") -Force
    Copy-Item (Join-Path $root "installer\dist_extra\Crear_acceso_directo_EduFEM.bat") (Join-Path $portable "Crear acceso directo EduFEM.bat") -Force
    Copy-Item (Join-Path $root "LICENSE") (Join-Path $portable "LICENCIA.txt") -Force
    Copy-Item (Join-Path $root "installer\dist_extra\LICENCIAS-TERCEROS.txt") (Join-Path $portable "LICENCIAS-TERCEROS.txt") -Force
}

# ── Resumen ─────────────────────────────────────────────────────────────────
$setup = Join-Path $root "installer\Output\EduFEM-Setup.exe"
Write-Host ""
Write-Host "OK  --  el entregable es UN archivo:" -ForegroundColor Green
Write-Host ("  {0}" -f $setup) -ForegroundColor Green
Write-Host ("  {0:N0} MB. Esta en una carpeta ignorada por git, por eso el editor puede no mostrarla." -f (MB $setup))
Write-Host ""
Write-Host "Lo demas es maquinaria del build, no se distribuye:"
Write-Host ("  dist\EduFEM\      {0,6:N0} MB   lo que el instalador empaqueta adentro" -f (MB (Join-Path $root "dist\EduFEM")))
Write-Host ("  vendor\texlive    {0,6:N0} MB   el TeX embebido (tarda ~5 min y pide internet rehacerlo)" -f (MB (Join-Path $root "vendor\texlive")))
if (Test-Path (Join-Path $root "build")) {
    Write-Host ("  build\            {0,6:N0} MB   descartable: cache de PyInstaller" -f (MB (Join-Path $root "build")))
}
