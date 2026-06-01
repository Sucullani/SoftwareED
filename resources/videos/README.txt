Videos WebP animados usados por la GUI (formato .webp, reproducidos por
gui/widgets/webp_player.py — solo Pillow, sin FFmpeg/PyAV).

Activos actuales:
    cantilever_q4_q9.webp          -> ElementTypeDialog (Modelo > Tipo de Elemento)
    tension_deformacion_plana.webp -> AnalysisTypeDialog (Modelo > Tipo de Análisis)

Si un .webp falta, el diálogo degrada a un mensaje informativo y sigue
funcionando. Los videos se regeneran offline con Manim (ver tools/render_*_manim/).

Nota: el proyecto migró de MP4 a WebP (instalador más liviano, sin DLLs de
FFmpeg). No volver a usar .mp4 ni tkvideoplayer/av en runtime.
