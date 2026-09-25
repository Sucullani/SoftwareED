# Defensa metodológica: tesis tecnológica frente al molde experimental

**Fecha**: 2026-09-23 · **Autor**: Claude (sesión con el autor) · **Estado**: terminado; sin commit

## Qué se pedía

Todo el contexto para defender la tesis final como investigación tecnológica (problema,
hipótesis, variables…) ante un tribunal que la querría experimental, en particular el
Ing. Miranda; argumentos anclados a la bibliografía de la tesis y al material docente, con
página; una diapositiva dinámica de la diferencia; y un PDF para estudiar de memoria.

## Qué se hizo

Carpeta nueva **`tesis/defensa_metodologica/`** (ver su `README.md`):

- `contexto_defensa.pdf` (+ `.tex`, pdflatex ×2): 23 p. La tesis en una página, la respuesta
  madre, tabla experimental/tecnológica con fuentes, material docente lámina por lámina,
  14 argumentos (fuente, pasaje literal, dónde está en la tesis, frase para decir), pieza por
  pieza, 34 preguntas con respuesta, «no digas / di», cifras, flancos abiertos, chuleta.
- `respaldo_diferencia.html`: 6 láminas animadas en el estilo de la presentación final
  (tokens de `presentacion/final/assets/css/deck.css`), sin internet, con guion (`N`).
  Publicada también como artefacto privado: https://claude.ai/artifact/XwP2wk6471RkMGugefgExn

**La presentación final (`tesis/presentacion/final/`) no se tocó**: se estaba construyendo en
otra sesión a la misma hora. Las láminas son un archivo aparte que puede enlazarse con anclas.

## Anclas nuevas encontradas (no estaban en la formulación final ni en la tesis)

- **García-Córdoba [7]**: fig. 1.5 (p. 52), procesos de la ciencia (observar → predecir) y de
  la tecnología (determinar el problema → comunicar); p. 48, «el proceder experimental es lo
  ideal» en el paso *verificar* de la ciencia; p. 51, la hipótesis tecnológica «es un diseño de
  carácter operativo» y evaluar es «determinar errores o desviaciones»; p. 82 (fig. 3.4), el
  problema, el marco, la hipótesis y la comunicación cambian de rasgos; pp. 94-97 (fig. 3.8),
  la investigación tecnológica tiene planos teórico, **experimental** y práctico.
- **Hernández-Sampieri [24]**: p. 151, «no consideramos que un tipo de investigación […] sea
  mejor que otro (experimental frente a no experimental)»; p. 152, experimentos «con […]
  ciertos objetos»; p. 196, poblaciones de «productos, procesos, […] objetos».
- **Álvarez de Zayas [8]**: p. 6, el para qué de la investigación científica es «la creación de
  nuevos conocimientos o tecnologías»; p. 12, el experimento con grupo control «deja mucho que
  desear en las Ciencias Sociales»; pp. 47-48, definición de experimento que cubre la V&V.
- **Wieringa [25]**: Tabla 1.1 (p. 5), la pregunta de conocimiento fija el instrumento
  (exactitud → simulación; utilidad → sujetos); pp. 47-48 y 65, experimentos estadísticos con
  muestras, «extremadamente caros» en campo.
- **Miranda, objetivo general, lám. 7 y 10**: en su escalera, *experimentar* es «elaborar
  modelos estructurales»; *validar*, comparar. Lám. 13: «Tesis de grado – Caso I: sin diagnóstico».
- **Manual de Procesos Académico-Administrativos UATF (2022), p. 93** (PDF p. 97): transcribe el
  Reglamento General de Tipos y Modalidades de Graduación del S.U.B. con las definiciones de
  tesis y proyecto de grado. **Cierra en parte el pendiente H-1**: ya hay fuente institucional;
  el Reglamento de la Carrera sigue citado desde el Taller 1.

## Qué se descartó y por qué

- **Usar el tipo «Slides» de claude.ai**: no admite la animación que se pedía ni funciona sin
  internet en la sala; se hizo una página propia con el sistema de diseño de la presentación.
- **Editar la tesis** para cerrar los flancos de la auditoría final: no se pidió y el autor
  decidió corregir por su cuenta. Quedan listados en la sección 10 del PDF.

## Trampas encontradas

- Una fila de tabla que empieza con `[3]` tras `\toprule` o `\\` se lee como argumento
  opcional («Illegal unit of measure»): envolver en llaves, `{[3]}`.
- En una tarjeta que gira, el contenedor de las caras debe ser `display: block`: un `span` en
  línea deja las caras sin alto y el texto se desborda sobre el título.
- La animación de entrada con `fill-mode: both` pisa `opacity` y `transform`: para atenuar o
  escalar después, usar `filter` y la propiedad `scale`.
- `sed` con `\\b` en el reemplazo, desde el Bash de esta máquina, perdió las barras invertidas:
  para LaTeX, editar con el editor, no con `sed`.

## Qué quedó pendiente

1. **Del autor**: ensayar la respuesta madre y la chuleta en voz alta; llevar impreso el
   Manual de Procesos, p. 93; decidir si enlaza las láminas desde la presentación principal.
2. **Arreglos de cinco minutos en la tesis**, si los quiere antes de imprimir: «kN y cm» →
   «kgf y cm» en el Anexo G (p. 164); «PI-1 a PI-3» → «PI-1 y PI-2» en la Nomenclatura; mover
   «extrapolación de Richardson» de instrumento a evidencia en la fila FEA30 (Tabla 3.7).
3. Si la tesis se recompila y se mueven páginas, revisar las páginas citadas en el PDF.

## Verificación

- `pdflatex contexto_defensa` ×2: EXIT 0, 23 páginas, 0 errores, 0 `Overfull`, 0 referencias
  indefinidas. Cuatro páginas revisadas en imagen.
- Láminas: una hoja de contactos con las seis en su último paso y la primera en su paso inicial,
  tomada con el Chrome sin pantalla de `presentacion/final/herramientas` (sin tocar esa
  carpeta); sin errores de consola. Se corrigieron tres fallos vistos en esa revisión.
- Cada página citada se leyó en el ejemplar; García-Córdoba (escaneo) como imagen.
