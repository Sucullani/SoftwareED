---
name: tesis-redactar
description: Guia para redactar o ampliar secciones de la tesis de EduFEM en espanol academico claro y natural (LaTeX, citacion Vancouver, terminologia MEF del proyecto). Usar al escribir, expandir o reescribir contenido de cualquier capitulo en tesis/capitulos/.
---

# Redactar la tesis de EduFEM

Tesis MIXTA (ingenieria + software educativo) sobre **EduFEM**, una GUI educativa de
elementos finitos 2D. Fuente en `tesis/` (LaTeX puro, clase `report`, biblatex+biber,
estilo **Vancouver**, babel espanol). Compila con pdflatex en MiKTeX.

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
- Voz consistente (preferentemente impersonal: "se implemento", "se valido"). No mezclar
  con primera persona del plural salvo en conclusiones si el resto del documento lo usa.
- Parrafos, no listas de bullets, salvo donde la lista es natural (objetivos especificos,
  requisitos, trabajo futuro).

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
- **Figuras pendientes**: usa el comando `\figpend{descripcion}` (definido en
  `tesis/preambulo.tex`) dentro de un `figure` con `\caption` y `\label`. **Nunca**
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
  `\autocite{clave1,clave2}` (ver `tesis/preambulo.tex`).
- **Solo claves que existan** en `tesis/bibliografia/referencias.bib`. Si necesitas una
  fuente nueva, agregala primero (skill `tesis-bibliografia`) o deja
  `% CITA PENDIENTE: <descripcion>`. No inventes claves.
- Cita los textos clasicos donde corresponde (Zienkiewicz, Bathe, Cook, Hughes, Reddy,
  Timoshenko-Goodier para la teoria; Roache/Oberkampf para V&V; NumPy/SciPy para el stack).

## Mapa de capitulos (indice minimo, no rigido)

- **Resumen** — 1 parrafo (~300 palabras) + palabras clave.
- **Introduccion** — planteamiento del problema, justificacion, objetivos (general +
  especificos), hipotesis/preguntas, alcance y limitaciones, estructura del documento.
- **Cap. 1 Marco teorico** — fundamentos MEF y formulacion debil; elasticidad plana y D;
  Q4/Q9 e isoparametria; Jacobiano; matriz B; rigidez e integracion de Gauss; ensamblaje,
  restricciones y cargas; resolucion y recuperacion de tensiones; calidad de malla; V&V
  (MMS, normas L2/H1, benchmarks, shear-locking); antecedentes de software educativo MEF.
- **Cap. 2 Diseno e implementacion** — requisitos y decisiones; stack; arquitectura MVC
  (ProjectModel, capas); motor MEF; pre-proceso; modulos educativos M0-M7; post-proceso;
  memoria de calculo e interoperabilidad.
- **Cap. 3 Resultados y analisis** — verificacion MMS; ciclo Q4->Q9->Q4; validacion
  Timoshenko (analitica + SAP2000); membrana de Cook (shear-locking); resultados del
  software/modulos; discusion.
- **Conclusiones y recomendaciones** — una conclusion por objetivo; aportes; limitaciones;
  trabajo futuro (solucionador disperso, B-bar/SRI, mas elementos, 3D, validacion con
  estudiantes).
- **Anexos** — instalacion, manual de uso, listados de codigo clave, resultados extendidos.

## Al terminar

- Releé lo escrito en voz alta (mentalmente): si una oracion no se entiende a la primera,
  reescribila mas corta.
- Verifica que toda `\autocite` resuelve y que no quedan muletillas. Para una revision
  sistematica, usa el skill `tesis-revisar`.
