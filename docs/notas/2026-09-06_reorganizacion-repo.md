# Reorganización del repositorio y espacio de trabajo para agentes

**Fecha**: 2026-09-06 · **Autor**: agente (Claude Code) · **Estado**: terminado

## Qué se pedía

Ordenar el repo: agrupar documentos, imágenes, iconos y recursos en carpetas claras sin
tocar el código pero respetando las rutas que el código referencia; consolidar documentos
redundantes y archivar el resto; y construir un espacio de trabajo para agentes con mapa
de la estructura, convenciones y un lugar definido para notas.

## Qué se hizo

**Documentación** — `docs/` pasó de cajón de sastre a cinco áreas con propósito:
`convenciones/` (el canon), `notas/` (este espacio), `auditorias/` (+ `historico/`),
`teoria/calidad_malla/` y `vyv/` (intacto).

**Consolidaciones**:
- Las seis auditorías se resumen en `docs/auditorias/ESTADO_AUDITORIAS.md`; los informes
  superados quedaron en `historico/`.
- `LEEME_app.txt` + `LEEME_distribucion.txt` → un único
  `installer/dist_extra/LEEME.txt` que cubre las dos vías de entrega (instalado / portable).
- Las ~70 prohibiciones "**No reintroducir**" dispersas en `CLAUDE.md` se indexaron en
  `docs/convenciones/no-reintroducir.md` (una línea por decisión + enlace al capítulo).

**`CLAUDE.md`**: de 909 líneas / 182 KB a ~230 líneas / 17,5 KB. El detalle se movió
**verbatim** a seis capítulos en `docs/convenciones/`; la raíz conserva identidad,
terminología, comandos y el flujo de revisión tal cual estaban, más tres bloques nuevos:
mapa, tabla de ruteo ("vas a tocar X → leé Y") y 22 reglas duras.

**Nuevos**: `README.md` (humanos), `AGENTS.md`, `docs/MAPA.md`, `docs/README.md`,
`docs/notas/{README,ESTADO,PLANTILLA}.md`, `tools/README.md`,
`docs/teoria/calidad_malla/README.md`.

**Higiene**: `tesis/compile_out.txt` y `compile_run.txt` fuera del control de versiones
(cierra parcialmente el ítem 10 del Top-10 de la auditoría del 2026-06-10).

## Qué se descartó y por qué

- **Fusionar los tres documentos de calidad de malla** (teoría / normalización / ejemplo
  resuelto): parecían redundantes por el nombre, pero son complementarios y cada uno es un
  artículo LaTeX autónomo ya compilado. Se agruparon con un índice en vez de fusionarse.
- **Mover `docs/vyv/`**: los scripts `tests/vv_*.py` **escriben** ahí con rutas literales y
  la tesis las cita. Intocable sin editar código funcional.
- **Reestructurar `tools/`** (agrupar los dos `render_*_manim/` bajo `tools/videos/`):
  `build_all.ps1` resuelve `make_icon.py` por ruta relativa y los diálogos nombran esas
  carpetas en mensajes visibles al usuario. Beneficio nulo frente al riesgo.
- **Dejar stubs** en las rutas viejas de los documentos movidos: se optó por actualizar las
  9 líneas de comentario que los citaban (aprobado por el autor), que envejece mejor.

## Trampas encontradas

- **Rutas de documentación dentro del código**: nueve líneas de comentario/docstring citaban
  rutas de `docs/`. Tres ya estaban rotas desde antes (`docs/Timoshenko,sap2000.pdf`, que
  hoy es `tesis/anexos/validacion_sap2000.pdf`). Quedaron todas actualizadas; el inventario
  vive en `docs/MAPA.md` §3.
- **Enlaces relativos al partir `CLAUDE.md`**: los capítulos bajaron dos niveles, así que
  todo `](models/x.py)` tuvo que pasar a `](../../models/x.py)`. Si en el futuro se mueve
  un capítulo de nivel, hay que rehacer esa reescritura.
- **`installer/EduFEM.iss` dependía de `..\docs\LEEME_app.txt`** — una ruta con backslash
  que el primer barrido (`grep "docs/"`) no detectó. Habría roto la compilación del
  instalador. Se repuntó a `dist_extra\LEEME.txt`. **Lección**: en este repo hay rutas con
  separador Windows en `.iss`, `.ps1` y `.bat`; barrer con `docs[\\/]`, no solo `docs/`.
- Los `.bat` de `docs/` eran **copias idénticas** de los de `dist/`. `dist/` es generado y
  está en `.gitignore`: la copia versionada ahora es la de `installer/dist_extra/`.
  `tools/build_all.ps1` no los copiaba (solo encadena icono → PyInstaller → Inno Setup): si
  alguna vez se quiere que la carpeta portable los incluya, hay que agregar ese paso.

## Qué quedó pendiente

- Del ítem 10 de la auditoría del 06-10 faltan `.gitattributes` para el EOL de `docs/vyv` y
  completar la lista de tests de la sección *Running*.
- El hallazgo 5 de esa auditoría (orden B/D y chips `DOF` en vez de `GDL` en la
  documentación) sigue abierto: el contenido se movió **verbatim**, sin corregirlo.

## Verificación

- `git status` sin cambios inesperados; todos los movimientos con `git mv` (historial
  preservado).
- El diff sobre archivos `.py` toca **solo** líneas de comentario y docstring — ninguna
  línea ejecutable.
- `python -m tests.test_fem`, `test_serialization`, `test_unit_conversion` y
  `test_canvas_visualization` corren igual que antes del cambio.
- No se verificó visualmente la GUI (corresponde al autor).
