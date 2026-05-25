# Pipeline TP vs DP — Manim

Genera el video comparativo Tension Plana vs Deformacion Plana para el
dialogo `🔬 Tipo de Analisis` de EduFEM.

## Por que Manim (no Claude Design)

- Estructuras realistas (chapa metalica con remaches, presa de hormigon
  con agua) que serian costosas de animar a mano en SVG/React.
- Easing y composicion de animaciones nativos (sin manejar timelines a
  mano).
- Output deterministico — el frame N siempre se ve igual entre corridas.
- El pipeline a WebP es 1 sola conversion ffmpeg en lugar del proceso
  Chrome+CDP+ffmpeg del render_q4q9.

## Requisitos

- Python con manim instalado (`pip install manim`)
- ffmpeg en el PATH (manim lo trae como dependencia)
- LaTeX (opcional pero recomendado, para `\sigma_z` y `\varepsilon_z`).
  Sin LaTeX, `MathTex` cae a su renderer interno con resultado aceptable.

## Renderizar

Desde esta carpeta:

```bash
manim -pqh tpvsdp.py TPvsDP
```

Flags:
- `-p` = preview automatico al terminar
- `-q h` = quality high (resolucion final 1920x1080 por default)
- `-q l` = quality low (480x270, para iterar rapido)

El script forza la resolucion final a 900x600 @ 22 fps via `config.*`
en el header, sin importar el flag de quality. El flag de quality
solo afecta supersampling interno.

Salida: `media/videos/tpvsdp/<calidad>/TPvsDP.mp4`

## Convertir a WebP animado (para el dialogo)

Una vez tengas el .mp4 a 900x600 y 22 fps:

```bash
ffmpeg -i media/videos/tpvsdp/1080p60/TPvsDP.mp4 \
       -vcodec libwebp \
       -filter:v "fps=22,scale=900:600:flags=lanczos" \
       -lossless 0 \
       -compression_level 6 \
       -q:v 75 \
       -loop 0 \
       -an \
       -vsync 0 \
       ../../resources/videos/tension_deformacion_plana.webp
```

Notas:
- `-loop 0` = loop infinito (clave para el seamless del dialogo).
- `-q:v 75` = balance calidad/tamano. Subir a 85 si pesa muy poco;
  bajar a 60 si el .webp queda > 2 MB.
- `-vsync 0` evita duplicacion de frames si el .mp4 tiene fps diferente.

Tamano esperado: ~1.0 - 1.5 MB para 5s @ 22fps a 900x600.

## Anatomia del script

`tpvsdp.py` contiene una unica clase `TPvsDP(Scene)` con metodos:

| Metodo | Que hace |
|---|---|
| `construct()` | Orquestador: layout → estructuras → timeline 5s. |
| `_build_layout()` | Bandas superior/inferior, separador vertical, titulos. |
| `_build_tp()` | Chapa metalica + remaches + pinzas + sensor + trail. |
| `_build_dp()` | Presa de hormigon + agua + terreno + secciones fantasma + barreras. |
| `_make_axes()` | Trio compacto X/Y/Z (rojo/verde/azul). |
| `_make_pinch()` | Pinza industrial estilizada con 3 dientes. |

### Loop seamless

El frame 0 muestra solo el layout (bandas + titulos + separadores +
ejes); las estructuras (`tp["geometry"]`, `dp["geometry"]`) arrancan
con `opacity=0`. El bloque final del `construct()` hace fade-out de
TODO lo que aparecio durante la animacion, dejando el frame 110 igual
al frame 0. Asi el WebP loop infinito no tiene "salto".

### Anti-superposicion

- Todo el contenido TP vive en `x < 0`; todo el contenido DP en `x > 0`.
- La banda superior (`y > 3.15`) es exclusiva de los titulos.
- La banda inferior (`y < -3.15`) es exclusiva de las ecuaciones.
- Las cargas (flechas naranjas) arrancan FUERA de cada estructura y
  entran solo hasta el borde — nunca atraviesan.
- Los ejes X/Y/Z viven en las esquinas inferiores de cada columna, no
  sobre las estructuras.

### Por que NO hay texto explicativo en la animacion

En la version anterior (Claude Design v1) el texto "espesor pequeno →
sigma_z no tiene espacio..." desaparecia antes de poder leerse. La
solucion arquitectonica es: la animacion muestra el comportamiento
visual; el dialogo `analysis_type_dialog.py` lleva la justificacion
textual como caption persistente bajo el video. El alumno lee a su
ritmo, sin presion de loop.

## Despues del .webp

Para wirearlo al dialogo:

1. Verificar que `resources/videos/tension_deformacion_plana.webp`
   existe.
2. Refactorizar `gui/dialogs/analysis_type_dialog.py`:
   - Eliminar `VIDEO_TP`, `VIDEO_DP`, `_video_for_case`,
     `_load_video_for_current_case`, `_show_missing_video_message`,
     `_restore_video_widget` (~80 lineas).
   - Apuntar a un solo `VIDEO_PATH` cargado una vez al __init__.
   - Cambiar geometry de 900x680 a algo como 720x740 (header + radios
     + video 660x440 + caption 2-cols + footer).
   - Agregar caption persistente 2 columnas con el texto explicativo.
