# exportar_png_pptx.ps1 — exporta cada diapositiva de un .pptx a PNG con el propio PowerPoint
# (COM). Sirve para comparar lo que arma construir_pptx.py con la presentación HTML.
#
#   powershell -File herramientas/exportar_png_pptx.ps1 <archivo.pptx> <carpeta_salida> [ancho=1920]
param(
  [Parameter(Mandatory = $true)][string]$Pptx,
  [Parameter(Mandatory = $true)][string]$Salida,
  [int]$Ancho = 1920
)
$ErrorActionPreference = 'Stop'
$Pptx = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force -Path $Salida | Out-Null
$Salida = (Resolve-Path $Salida).Path
$alto = [int]($Ancho * 9 / 16)
$app = New-Object -ComObject PowerPoint.Application
try {
  # ReadOnly, sin título, sin ventana
  $pres = $app.Presentations.Open($Pptx, -1, 0, 0)
  $n = $pres.Slides.Count
  for ($i = 1; $i -le $n; $i++) {
    $destino = Join-Path $Salida ('d{0:D3}.png' -f $i)
    $pres.Slides.Item($i).Export($destino, 'PNG', $Ancho, $alto)
  }
  "exportadas $n diapositivas"
  $pres.Close()
} finally {
  $app.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
