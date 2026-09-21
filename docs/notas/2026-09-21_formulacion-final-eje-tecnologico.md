# Formulación metodológica final: eje tecnológico «caja negra → análisis no trazable ni verificable»

**Fecha**: 2026-09-21 · **Autor**: Claude (sesión con el autor) · **Estado**: propuesta entregada, espera la decisión del autor

## Qué se pedía

Una formulación metodológica sólida para defender EduFEM como tesis de investigación
tecnológica, con la evidencia en el diseño, desarrollo, verificación y validación del artefacto:
**sin prueba de campo con estudiantes**, sin disfrazarla de tesis experimental, con una cadena
causa–efecto lineal, usando todo lo ya escrito, y sin que pueda leerse como proyecto de grado.
El autor pidió revisar si el material docente lo permite y sumó tres fuentes en
`tesis/bibliografia/Bib. DSM/` (Hevner 2004, Peffers 2007, Wieringa 2014).

## Qué se hizo

- **`tesis/alternativas/formulacion_final.pdf`** (16 p., `.tex` al lado; compila con
  `pdflatex` dos veces, 0 desbordes). No forma parte de la tesis.
- **La decisión**: se conserva la causa de la v4 (uso del software como caja negra) y se cambia
  **una sola pieza**: la variable efecto baja del estudiante («bajo criterio») al análisis:
  **baja trazabilidad y verificabilidad del análisis por el MEF**. Interviniente = EduFEM
  (un «sistema», en el vocabulario de Miranda). Objeto de estudio técnico (el de la v1);
  campo = los medios de cálculo con que ese análisis se enseña.
- **Hipótesis** con el molde de Miranda y **dos cláusulas**, una por dimensión de la VD:
  (a) trazabilidad → cobertura del canal (7/7 módulos, 9/9 en la memoria, 3 fases) y del
  contenido (18/18); (b) verificabilidad → V&V con criterios a priori. **Dos PI**. Cinco OE
  en la misma escalera de la v4, con OE1 (diagnóstico documental sobre el software), OE4 y
  OE5 reescritos. El título aprobado no cambia.
- La tabla 18/18 deja de llamarse «validez de contenido» y pasa a ser **cobertura de
  contenido** (verificación de requisitos), indicador de la trazabilidad; la matriz de los
  cuatro principios pasa a la §2.2.1 como fundamentación del diseño.
- **Método**: ciencia del diseño. Proceso de seis actividades de Peffers mapeado al índice de
  tres capítulos; la Tabla 2 de Hevner (p. 86) muestra que la tesis usa cuatro de las cinco
  familias de evaluación; Wieringa (pp. 30-31) restringe la investigación al ciclo de diseño y
  define la validación de laboratorio, y (p. 247) define las pruebas sobre un artefacto como
  experimentos causa–efecto con X e Y **sin sujetos**.
- **Lectura del material docente** (los 8 PDF), con lámina: Reglamento Art. 6, 8, 9 (tesis)
  frente a Art. 57 y 61 (proyecto: convenio Universidad–Empresa); «modelación de simulación
  teórica» (Taller 4, lám. 4); **Ejemplo 2 del Taller 5** (software validado contra casos
  publicados con % de aproximación); «Tesis de grado – Caso I: sin diagnóstico» y Caso II
  (4 OE en 3 capítulos) de Miranda. Ninguna lámina exige sujetos ni prueba de campo.
- El documento trae además: tabla criterio–umbral–cifra–veredicto (la que pedía TRZ-07), once
  preguntas de defensa con respuesta corta, apertura de 30 segundos, **mapa de cambios
  archivo por archivo sobre `capitulos_v4/`**, entradas `.bib` de las tres fuentes y los
  pasajes literales con página impresa.

## Qué se descartó y por qué

- **Volver a la v1 tal cual**: su problema no sigue el molde causa–efecto y su hipótesis
  condicional hace depender la exactitud de la transparencia (la «hipótesis circular» del
  dictamen).
- **Conservar la VD de la v4 con salvedades** (la salida «a» de la auditoría): deja en pie las
  preguntas críticas 1, 2, 4, 20, 21 y 31 del tribunal simulado.
- **Nombrar la prueba de campo como pendiente**: con la VD en el análisis no es un eslabón de
  la cadena. Se recomienda retirarla de los 15 renglones de la v4 donde aparece, dejar una
  oración afirmativa de alcance y, a lo sumo, una línea en Recomendaciones.
- **«Investigación aplicada de tipo tecnológico» atribuida a García-Córdoba**: el respaldo de
  citas ya había detectado que la fuente *contrasta* tecnológica con aplicada (pp. 90-92).
  Se propone «investigación tecnológica, de carácter propositivo».

## Trampas encontradas

- `Garcia-Cordoba 2005` es un escaneo sin capa de texto: los pasajes salen de
  `tesis/respaldo_citas/verificado.json`, no de una búsqueda.
- En el PDF de Wieringa el desfase entre página del PDF y folio impreso **no es constante**
  (14 en la p. 16, 12 en la p. 31, 11 en la p. 53): hay que leer el folio de cada página.
- La p. 59 de Wieringa tiene una errata en el original («we can we validate»); en el anexo va
  con [sic].

## Qué quedó pendiente

1. **Decide el autor**: si adopta esta formulación (conviene acordarla con el tutor). Si sí,
   el paso siguiente es construir la versión final sobre `capitulos_v4/` con el mapa de la
   sección 7 del PDF, cargar las tres entradas al `.bib` (skill `tesis-bibliografia`), copiar
   los ejemplares a `tesis/bibliografia/` con la convención de nombres, regenerar el respaldo
   de citas y rehacer las láminas de problema, hipótesis, variables, matriz y §3.6.
2. **H-1 sigue abierto**: el Reglamento de Graduación está citado desde las láminas del
   Taller 1; hay que conseguir el texto.
3. Los hallazgos numéricos y de redacción de la auditoría v4 no dependen del eje y siguen en
   pie (0,56 % «en desplazamientos», razón Q4/Q9 de Cook, procedencia de los umbrales, cota
   de σ*, partición en nueve etapas, regla de marcado de la tabla 18/18).

## Verificación

- `pdflatex formulacion_final` ×2: EXIT 0, 16 páginas, 0 `Overfull`, 0 referencias
  indefinidas. Páginas 1 y 7 revisadas en imagen.
- Las citas literales del anexo se cotejaron contra el texto extraído de cada PDF, con el
  folio impreso leído en la propia página. Las cifras de la tabla de criterios son las de la
  §3.8 y las tablas de `capitulos_v4/04_resultados.tex`.
