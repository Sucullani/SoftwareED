# inspeccionar_pptx.ps1 — abre un .pptx con PowerPoint (COM) y lista, por diapositiva, lo que
# PowerPoint entendió: efectos de la secuencia principal, transición, si está oculta,
# hipervínculos y videos. Si el archivo tuviera XML inválido, PowerPoint no lo abriría.
#
#   powershell -File herramientas/inspeccionar_pptx.ps1 <archivo.pptx>
param([Parameter(Mandatory = $true)][string]$Pptx)
$ErrorActionPreference = 'Stop'
$Pptx = (Resolve-Path $Pptx).Path
$app = New-Object -ComObject PowerPoint.Application
try {
  $pres = $app.Presentations.Open($Pptx, -1, 0, 0)
  "diapositivas: $($pres.Slides.Count)"
  foreach ($s in $pres.Slides) {
    $seq = $s.TimeLine.MainSequence
    $clics = 0; $conClic = 0
    for ($i = 1; $i -le $seq.Count; $i++) { if ($seq.Item($i).Timing.TriggerType -eq 1) { $clics++ } }
    $enlaces = 0; $videos = @()
    foreach ($sh in $s.Shapes) {
      try { if ($sh.ActionSettings.Item(1).Action -ne 0) { $enlaces++ } } catch {}
      if ($sh.Type -eq 16) {
        $ps = $sh.AnimationSettings.PlaySettings
        $videos += "video(auto=$($ps.PlayOnEntry) bucle=$($ps.LoopUntilStopped))"
      }
    }
    $oculta = if ($s.SlideShowTransition.Hidden -eq -1) { ' OCULTA' } else { '' }
    "{0,3} efectos={1,3} clics={2,2} transicion={3} enlaces={4,2} formas={5,3}{6} {7}" -f $s.SlideIndex, $seq.Count, $clics, $s.SlideShowTransition.EntryEffect, $enlaces, $s.Shapes.Count, $oculta, ($videos -join ' ')
  }
  $pres.Close()
} finally {
  $app.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
