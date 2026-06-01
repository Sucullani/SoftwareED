---
name: tesis-revisar
description: Revisa y pule borradores de la tesis de EduFEM (claridad, cohesion, registro academico, redundancia, muletillas de IA, consistencia de terminologia MEF y de citas Vancouver, higiene LaTeX). Usar al corregir o mejorar texto ya escrito de la tesis en tesis/.
---

# Revisar y pulir la tesis de EduFEM

Revision de calidad sobre texto ya redactado. NO reescribe el sentido: mejora la forma,
corrige errores y asegura consistencia. Aplica los arreglos en el mismo pase (editar el
`.tex` directamente) y reporta lo hecho.

## Checklist de revision

1. **Claridad y concision**
   - Oraciones largas que se pueden partir; subordinadas innecesarias; voz pasiva confusa.
   - Borra relleno y muletillas de IA: "en la actualidad", "hoy en dia", "cabe destacar",
     "es importante mencionar", "en un mundo cada vez mas", "a lo largo de la historia".
   - Cada parrafo tiene una idea clara y conecta con el siguiente.

2. **Registro academico y voz**
   - Tono tecnico pero legible; sin coloquialismos.
   - Voz consistente en todo el documento (preferente impersonal: "se implemento").

3. **Terminologia (ver CLAUDE.md y skill `tesis-redactar`)**
   - Reemplaza DOF->GDL, FEM->MEF (salvo marca EduFEM), BC/boundary condition->restriccion,
     stress->tension, strain->deformacion, displacement->desplazamiento, mesh->malla, etc.
   - Busca fugas de ingles en prosa. Auditoria rapida (Grep en tesis/):
     `\b(DOF|FEM|boundary condition|stress|strain|stiffness|displacement)\b`
     y descarta los hits que sean la marca EduFEM o aparezcan dentro de codigo/verbatim.

4. **Citas Vancouver**
   - Toda `\autocite{clave}` debe resolver a una entrada de
     `tesis/bibliografia/referencias.bib`. Lista claves usadas vs definidas y marca las
     huerfanas. Convierte cualquier "% CITA PENDIENTE" en cita real o en nota explicita.
   - Las citas numericas deben ir donde aporta respaldo (afirmaciones teoricas, datos
     externos), no decorar cada oracion.

5. **Higiene LaTeX**
   - `\label` unicos (prefijos cap:/sec:/fig:/tab:/eq:); `\autoref` sin referencias rotas.
   - Nada de `\includegraphics` a archivos inexistentes; usar `\figpend` si la figura falta.
   - Math bien formado (entornos cerrados, `bmatrix`, simbolos correctos).
   - Acentos y caracteres especiales validos para la codificacion del proyecto.

6. **Consistencia entre capitulos**
   - Un mismo dato numerico (errores de validacion, tasas de convergencia, dimensiones de
     la viga, etc.) debe coincidir en todos los capitulos donde aparece.
   - No repetir la teoria del Cap. 1 dentro del Cap. 2; el Cap. 2 describe la
     implementacion, no reexplica el metodo.
   - Conclusiones alineadas con los objetivos de la Introduccion (una por objetivo).

7. **Verificacion de compilacion (opcional pero recomendado)**
   - Si MiKTeX esta disponible: `pdflatex main` -> `biber main` -> `pdflatex main` x2 en
     `tesis/`. Reporta errores/warnings (referencias rotas, citas sin resolver).

## Salida

- Lista breve de hallazgos por categoria (que estaba mal y donde: `archivo:linea`).
- Los arreglos ya aplicados al texto.
- Lo que requiere decision del autor (datos pendientes, citas faltantes) marcado aparte.
