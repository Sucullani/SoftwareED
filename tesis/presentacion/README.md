# Presentación de defensa — EduFEM

**Vigente: [`final4/`](final4/README.md)**, la defensa final, sincronizada con la tesis vigente
(`tesis/main_final4.pdf`, 2026-10-20).

| Qué necesita | Archivo (en `final4/`) |
|---|---|
| Presentar en la sala (estilo PowerPoint, sin internet) | `Presentar_defensa_v2.bat` → abre `Defensa_EduFEM_v2.html` a pantalla completa |
| **Llevarla a otra laptop o a un USB** (un solo archivo, cualquier navegador) | `Defensa_EduFEM_v2_portable.html` |
| La misma, en tema oscuro | `Presentar_defensa.bat` → `Defensa_EduFEM.html` |
| PowerPoint editable, un clic por paso, con notas del orador | `Defensa_EduFEM_final4.pptx` (PowerPoint 2019, 2021 o 365) |
| PowerPoint narrado, que avanza solo con la voz | `Defensa_EduFEM_final4_narrada.pptx` |
| Escuchar la narración completa (29,6 min) para ensayar | `audio/Defensa_EduFEM_final4_narracion.mp3` (+ `indice_audio.md`, el minuto de cada lámina) |

Cómo se presenta, qué cambió respecto de la defensa de borrador y cómo se regenera cada pieza:
[`final4/README.md`](final4/README.md). Qué dice cada lámina y con qué fuente: [`final4/GUION.md`](final4/GUION.md).

## Archivo (no se mantiene)

| Carpeta | Qué es |
|---|---|
| `archivo/final3/` | La defensa de borrador de final3 (2026-09-27/28): HTML de 60 láminas, versión 2, `.pptx` interactivo (y su versión narrada), PDF y los dos videos (36:47 y 38:11). **Queda solo en el disco del autor**: no se sube al repositorio (417 MB; la excluye `tesis/.gitignore`) |
| [`archivo/final/`](archivo/final/README.md) | La defensa de la tesis final (`main_final`, 2026-09-23): HTML interactiva, versión 2, `.pptx`, PDF y su video en `video/` |
| [`archivo/v1_v2/`](archivo/v1_v2/README.md) | Las presentaciones PowerPoint v1 y v2 (2026-09-11 a 09-19, ejes anteriores de la tesis), su constructor `build_deck.py` y sus videos en `video/` |

Las herramientas del archivo se dejan como estaban: sus rutas apuntan a la ubicación anterior y
no se vuelven a ejecutar.
