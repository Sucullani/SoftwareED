---
name: tesis-redactar
description: Guia para redactar o ampliar secciones de la tesis de EduFEM en espanol academico claro y natural (LaTeX, citacion Vancouver, terminologia MEF del proyecto). Usar al escribir, expandir o reescribir contenido de cualquier capitulo de la version vigente de la tesis (hoy tesis/capitulos_final4/).
---

# Redactar la tesis de EduFEM

Tesis MIXTA (ingenieria + software educativo) sobre **EduFEM**, una GUI educativa de
elementos finitos 2D. Fuente en `tesis/` (LaTeX puro, clase `report`, biblatex+biber,
estilo **Vancouver**, babel espanol). La version vigente compila con XeLaTeX en MiKTeX (Times New Roman real, texto justificado).

**Version vigente**: hoy `tesis/main_final4.tex` + `tesis/capitulos_final4/`, que lleva su
propio `preambulo.tex`, su `referencias.bib`, sus figuras rehechas y su `CRITERIOS.md` (reglas
editoriales obligatorias: leelas antes de escribir). No se edita `tesis/archivo/` (final, que es
la base auditada, final1, final2, final3 y v1 a v4). Una mejora grande abre una version nueva (`capitulos_final5/`…) segun
`tesis/README.md`, «Versiones». Compila con `latexmk -xelatex main_final4.tex` desde `tesis/`.

## Antes de escribir

1. **Lee la seccion actual** del `.tex` que vas a tocar y los capitulos vecinos: no
   repitas explicaciones ya dadas (la teoria del MEF vive en el Cap. 1; el Cap. 2
   describe *como se implemento*, no reexplica la teoria).
2. **Extrae material real del proyecto** — no inventes. Fuentes por tema:
   - Teoria/formulacion (Cap. 1): `fem/` (shape_functions, jacobian, b_matrix,
     constitutive, stiffness, assembly, solver, stress, gauss_quadrature,
     equivalent_forces, error_norms, mesh_quality).
   - Arquitectura/GUI (Cap. 2): `CLAUDE.md`, `models/project.py`, `gui/`, `config/`.
   - Modulos educativos (Cap. 2 / aporte): `education/` (mod00..mod07), `CLAUDE.md`.
   - Entrada/salida y memoria de calculo (Cap. 2): `file_io/`.
   - Resultados numericos (Cap. 3): `tests/vv_*`, `tests/test_*`, `docs/vyv/`,
     `tests/example_data.py`. **Usa los numeros EXACTOS** que aparecen ahi.
3. Si te falta un dato concreto, deja `% DATO PENDIENTE: <que falta>` en vez de inventar.

## Principios de redaccion (claridad y naturalidad)

- Espanol academico claro. Frases directas, una idea por oracion, parrafos cohesionados.
- **Prohibido el relleno y las muletillas de IA**: "en la actualidad", "hoy en dia",
  "a lo largo de la historia", "cabe destacar que", "es importante mencionar",
  "en un mundo cada vez mas...". Si una frase no aporta informacion, se borra.
- Precision tecnica sin pedanteria: define un termino la primera vez, despues usalo.
- Sujetos segun el `CRITERIOS.md` vigente (seccion 3): "el autor adopto / eligio" para las
  decisiones de diseno, "EduFEM resuelve / reporta / recupera" para lo que hace el software y
  "la literatura predice" para lo tomado de fuentes; evitar el impersonal que oculta quien
  decidio. Sin primera persona del plural.
- Parrafos para el argumento; toda enumeracion de cuatro elementos o mas sale a lista o tabla
  (`CRITERIOS.md`, seccion 3).

## Terminologia OBLIGATORIA (igual que el codigo, ver CLAUDE.md)

| Ingles | Usar en la tesis |
|---|---|
| DOF | **GDL** (singular "GDL", plural "GDLs") |
| FEM | **MEF** (excepcion: la marca **EduFEM** se mantiene) |
| plane stress / strain | tension plana / deformacion plana |
| boundary condition / BC | restriccion |
| mesh, node, element, load | malla, nodo, elemento, carga |
| stress, strain, displacement | tension, deformacion, desplazamiento |
| stiffness, shape function, solver | rigidez, funcion de forma, solucionador |
| hourglass modes | modos espurios (hourglass) — conservar "hourglass" entre parentesis |

No reintroducir ingles en prosa para conceptos que ya tienen traduccion canonica.

## Convenciones LaTeX

- Capitulos numerados (1,2,3): `\chapter{...}` + `\section`/`\subsection`.
- Frontales/cierre sin numerar: `\chapter*{...}` + `\addcontentsline{toc}{chapter}{...}`
  y subsecciones con `\section*{...}`.
- **Figuras pendientes**: usa el comando `\figpend{descripcion}` (definido en el
  `preambulo.tex` de la version vigente) dentro de un `figure` con `\caption` y `\label`. **Nunca**
  `\includegraphics` de un archivo que no existe (rompe la compilacion). Cuando exista
  la imagen real, reemplaza `\figpend{...}` por `\includegraphics[width=...]{figuras/...}`.
- Ecuaciones: `equation`/`align`. Matrices: `bmatrix`. Simbolos: `\sigma`, `\varepsilon`,
  `\xi`, `\eta`, `\det\mathbf{J}`, etc. Notacion de matrices en negrita (`\mathbf{B}`,
  `\mathbf{D}`, `\mathbf{K}`) coherente con la Memoria de Calculo del software.
- Tablas: `table`+`tabular` reales con los numeros del proyecto.
- Referencias cruzadas: `\label{cap:...}/\label{fig:...}/\label{tab:...}/\label{eq:...}`
  y `\autoref{...}`. Etiquetas unicas en todo el documento (prefijo por tipo).

## Citacion Vancouver

- Citas numericas por orden de aparicion. Cita con `\autocite{clave}` o
  `\autocite{clave1,clave2}` (ver el `preambulo.tex` de la version vigente).
- **Solo claves que existan** en el `referencias.bib` de la version vigente (hoy
  `tesis/capitulos_final4/referencias.bib`). Si necesitas una
  fuente nueva, agregala primero (skill `tesis-bibliografia`) o deja
  `% CITA PENDIENTE: <descripcion>`. No inventes claves.
- Cita los textos clasicos donde corresponde (Zienkiewicz, Bathe, Cook, Hughes, Reddy,
  Timoshenko-Goodier para la teoria; Oberkampf y Roy, y Salari y Knupp, para V&V; NumPy/SciPy
  para las tecnologias empleadas). Roache 1998 esta de baja: ver `tesis-bibliografia`.

## Mapa de capitulos (indice minimo, no rigido)

- **Resumen** — 1 parrafo (~300 palabras) + palabras clave.
- **Introduccion** — planteamiento del problema, justificacion, objetivos (general +
  especificos), hipotesis/preguntas, alcance y limitaciones, estructura del documento.
- **Cap. 1 Fundamentacion teorica** (su titulo es el OE1 completo: ver CRITERIOS.md) —
  antecedentes y estado del arte del software educativo MEF, de donde salen los requisitos;
  principios que orientan la exposicion; fundamentos MEF y formulacion variacional; elasticidad
  plana y D; Q4/Q9 e isoparametria; Jacobiano; matriz B; rigidez e integracion de Gauss;
  bloqueo y modos espurios; ensamblaje, restricciones y cargas; resolucion y recuperacion de
  tensiones; calidad de malla; verificacion y validacion (MMS, normas L2/H1).
- **Cap. 2 Desarrollo de EduFEM** (titulo: el OE2 completo) — seccion 2.1, diseno metodologico
  (tipo de investigacion y metodo de la ciencia del diseno, variables, matriz de consistencia,
  casos de estudio, instrumentos, criterios de aceptacion y contraste de la hipotesis); seccion
  2.2, el software: requisitos y decisiones; tecnologias empleadas; arquitectura (ProjectModel,
  capas); motor MEF; pre-proceso; modulos educativos M0-M7; post-proceso; memoria de calculo e
  intercambio de datos.
- **Cap. 3 Verificacion y validacion** (titulo: el OE3 completo) — medicion; MMS; consistencia
  interna (ciclo Q4->Q9->Q4); viga de Timoshenko (analitica + SAP2000); membrana de Cook
  (bloqueo por cortante); cobertura del procedimiento y del contenido; interpretacion y
  limitaciones observadas (3.7.5); contraste de la hipotesis (3.8).
- **Conclusiones y recomendaciones** — triada sin rotulos: apertura con el objetivo general y
  la respuesta al problema; veredicto de la hipotesis sin copiar su enunciado; un parrafo por
  capitulo que abre con 'De ... (Capitulo N) se concluye que...'; debilidades con remision a la
  seccion 3.7.5; recomendaciones en tres grupos; sin 'Aportes' ni 'Limitaciones' (ver
  CRITERIOS.md).
- **Anexos** — instalacion, manual de uso, listados de codigo clave, resultados extendidos.

## Al terminar

- Releé lo escrito en voz alta (mentalmente): si una oracion no se entiende a la primera,
  reescribila mas corta.
- Verifica que toda `\autocite` resuelve y que no quedan muletillas. Para una revision
  sistematica, usa el skill `tesis-revisar`.
