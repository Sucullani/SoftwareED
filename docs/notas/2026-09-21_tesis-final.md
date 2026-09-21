# Tesis final: eje tecnológico «caja negra → análisis no trazable ni verificable»

**Fecha**: 2026-09-21 · **Autor**: Claude (sesión con el autor) · **Estado**: en `origin/main` (commits `f22d139` y `e06f884`); espera la revisión del autor

## Qué se pedía

Implementar la formulación final (`tesis/alternativas/formulacion_final.pdf`, aprobada por el
autor el mismo día) y **construir la tesis de entrega**, sin repetir los errores que la
auditoría de redacción de la v4 dejó registrados (`tesis/auditoria_v4/`, 225 hallazgos), con
lenguaje comprensible en el contexto boliviano, con libertad para reformular lo que hiciera
falta, agregando las referencias recomendadas sin inflar la bibliografía y **eliminando las que
otra referencia pudiera reemplazar**.

## Qué se hizo

### La versión final es autocontenida

`tesis/main_final.tex` + `tesis/capitulos_final/` (los once capítulos). No lee nada de
`capitulos/` ni de `capitulos_v4/`: las versiones anteriores quedan como archivo y ya no se
sincronizan. Comparte `preambulo.tex`, `portada/`, `figuras/` y `bibliografia/referencias.bib`.
Los **criterios editoriales** que gobiernan todos los capítulos están versionados en
`capitulos_final/CRITERIOS.md`: formulación, tabla de términos canónicos, estilo y higiene
LaTeX. Es el documento que hay que leer antes de tocar un capítulo.

### El cambio de eje, en una línea

La variable efecto baja del estudiante al análisis. Antes: «bajo criterio del estudiante para
interpretar la respuesta». Ahora: **baja trazabilidad y verificabilidad del análisis**, que es
una propiedad del medio de cálculo y se mide sobre el software. Con eso, las dos cláusulas de
la hipótesis se comprueban dentro del documento y **no queda nada diferido**: desaparecen las
quince líneas de «prueba de campo», el «en esta etapa» y las salvedades de efecto no medido que
la auditoría señalaba como el problema de mayor impacto.

### Lo que se reescribió entero

- **Resumen**: de 470 a ~300 palabras, sin fórmulas sin glosar, con la cota de SAP2000 acotada
  a la magnitud que mide (era el hallazgo crítico TRZ-01: «0,56 %» sin decir «en
  desplazamientos», cuando la Tabla 3.2 registra 4,56 % en una componente secundaria).
- **Introducción**: problema con «incidir en» (no «afectar en»: régimen incorrecto, CAL-04),
  las dos propiedades definidas de forma operativa, objeto técnico recuperado de la v1, objetivo
  general sin finalidad no medida, cinco OE, dos PI, apartado propio de normas de citación
  (antes enterradas en un párrafo de 700 palabras) y frase de alcance en positivo.
- **§2.1 Diseño metodológico**: tabla de las seis actividades de la ciencia del diseño
  (`tab:dsrm`), por qué la evaluación es de laboratorio, versión evaluada identificada
  (EduFEM 1.0.0, revisión `91e3df0`), universo de contenido con los 49 ítems del consenso
  repartidos y justificados uno por uno, y **tabla de criterios de aceptación** (`tab:criterios`)
  con umbral, procedencia y qué lo refutaría: reemplaza a la oración de 180 palabras que la
  auditoría marcó como imposible de auditar (CLA-01, DEF-13).
- **§1.1 y §1.2**: párrafo de método de la revisión y afirmación de vacío acotada a los
  recursos revisados (DEF-04); ocho atributos en lista numerada; cinco requisitos que el
  capítulo 2 y las conclusiones citan por la misma lista (TRZ-26); nota de la Tabla 1.1 con la
  asimetría de la base de evidencia y las glosas de sus códigos; §1.2 declara que la agrupación
  en cuatro principios es propia (TRZ-03) y que no es evidencia de eficacia.
- **§3.1, §3.6 a §3.8**: cobertura del procedimiento y del contenido con su regla de marcado y
  con qué prueba y qué no prueba el 18/18 (DEF-20); la matriz de principios pasa a ser
  «trazabilidad de las decisiones de diseño»; **subsección propia para la lección del defecto de
  extrapolación** (`sec:leccion-extrapolacion`), que además es la prueba de que la hipótesis no
  es circular; y **tabla criterio–umbral–cifra–veredicto** (`tab:veredicto`) en §3.8, que es lo
  que pedía TRZ-07 y lo que el Taller 6 describe para las conclusiones.
- **Conclusiones**: una por objetivo, rotuladas con el objetivo que cierran (APF-02); aportes
  reorganizados como las tres contribuciones que la ciencia del diseño distingue (artefacto,
  conocimiento de diseño, conocimiento de evaluación); limitaciones en lista, con las tres que
  faltaban (nadie ajeno al autor usó el software; el software no obliga a recorrer el
  procedimiento; la deformación plana solo se verifica con soluciones manufacturadas).

### Lo que se corrigió por zonas, con verificación independiente

Cuatro zonas en paralelo, cada una con un agente que aplicó los hallazgos de su parte y otro que
verificó sintaxis LaTeX, términos prohibidos, remisiones y cifras: teoría §1.3-1.13 más
nomenclatura, software §2.2, verificación y validación §3.2-3.5, y anexos A-G.

### La revisión de defensa, y lo que encontró

Terminado el documento, una revisión simuló un tribunal de tres miembros —metodología,
estructuralista usuario de SAP2000 y métodos numéricos— y verificó cada hallazgo contra las
tablas del propio documento y contra el código del software. Salieron doce, todos válidos, y
todos aplicados. El más grave: la memoria del ejemplo canónico se declaraba «coincide con el
cálculo manual», pero el Anexo G reproduce la salida del motor y no un cálculo independiente,
de modo que el criterio era circular; ahora el criterio es que cada etapa se desarrolle con
sustitución numérica remitida a su ecuación, que es lo que sí se sostiene. El más fino: lo que
se compara contra SAP2000 pasa a llamarse «diferencia» y no «error», porque el propio documento
advierte que la cáscara y el continuo de tensión plana no son la misma formulación y ninguna es
el patrón de la otra. También apareció una contradicción de cifras —la flecha es un
desplazamiento, y el texto le atribuía menos del 0,3 % frente a SAP2000 mientras admitía
0,56 % en desplazamientos— y una mezcla de umbrales del Jacobiano entre el comprobador de salud
(0,30 y 0,70) y el módulo M0 (0,50 y 0,80), comprobada leyendo `fem/mesh_quality.py` y
`education/mod00_mesh_quality.py`.

### Bibliografía: +3 y −3

Entran `hevner2004design`, `peffers2007dsrm` y `wieringa2014design`, con ejemplar en
`tesis/bibliografia/`, metadatos leídos de la portada y **diez respaldos con pasaje literal y
folio impreso** en `respaldo_citas/verificado.json`. Salen del documento final —no del `.bib`,
porque la v4 las cita— `rutten2012learning`, `chi2014icap` y `atkinson2000learning`: sostenían
la plausibilidad de un efecto de aprendizaje que la formulación final ya no afirma, y lo que
queda lo cubren Lee, Bishay y Pérez-Santiago, que son específicas de la enseñanza del MEF. La
lista de referencias de la versión final queda en el mismo tamaño que antes.

## Qué se descartó y por qué

- **Pegar salvedades** («este efecto no se midió y queda pendiente de la prueba de campo»), que
  es lo que proponía la mayoría de los hallazgos de calibración de la auditoría: con la variable
  dependiente en el análisis, esas afirmaciones no necesitan salvedad porque ya no se hacen. Los
  hallazgos quedaron sin objeto, no sin aplicar.
- **Nombrar la prueba de campo** como línea pendiente. Solo queda una línea en las
  recomendaciones, como investigación distinta y de otra naturaleza.
- **Mover la matriz de principios a §2.2.1**, como decía el primer plan: habría obligado a
  tocar un archivo que otro agente estaba editando, y en §3.6 cumple igual su función.
- **Cambiar el título de la tesis.** El del perfil defendido es tecnológico y nunca prometió
  medir aprendizaje: la formulación final es la que mejor le corresponde.

## Trampas encontradas

- El **límite del modelo** cortó las cuatro tareas paralelas a mitad de sesión. No alcanzaron a
  editar nada, así que se relanzaron como workflow. Al retomar trabajo delegado conviene
  comprobar primero con `git status` si los agentes dejaron algo a medias.
- **Dos agentes no pueden editar el mismo archivo.** `02_marco_teorico.tex` y `04_resultados.tex`
  se reparten entre el coordinador y un agente; la solución fue que el coordinador escribiera sus
  bloques aparte y los insertara después **cortando por `\label`**, no por número de línea
  (`scratchpad/aplicar_bloques.py`).
- En un script de workflow, `String.raw` es obligatorio para los prompts con comandos LaTeX
  (`\autoref` se convertiría en `autoref`), pero **una ruta que termina en `\` rompe el
  literal**: las rutas de Windows van con barras normales.
- El heredoc del shell manda en cp1252: los scripts con acentos van por Write (ya estaba
  anotado, y volvió a morder).

## Qué quedó pendiente

1. **Revisión del autor**, que es lo único que un agente no puede hacer: leer la Introducción,
   §2.1 y §3.8 completas y confirmar que la formulación es la que quiere defender.
2. **Personalizar los preliminares** (`capitulos_final/00_preliminares.tex`): dedicatoria,
   agradecimientos y la decisión sobre el párrafo de declaración de uso de herramientas de
   inteligencia artificial, que quedó redactado y comentado (hallazgo DEF-06, riesgo de defensa
   sin respuesta en la v4).
3. **H-1 sigue abierto**: conseguir el Reglamento de Graduación y citar sus artículos de la
   fuente y no de las láminas del Taller 1. De él depende también si la carátula debe llevar
   tutor.
4. **Presentación y video**: `tesis/presentacion/guion_v2.json` sigue con el eje de la v4. Hay
   que rehacer las láminas de problema, objeto y campo, objetivos, hipótesis, variables, matriz
   y §3.6, y regenerar el video.

## Verificación

- `latexmk -pdf main_final.tex`: EXIT 0, **189 hojas**, 0 errores, 0 `Overfull`, 0 referencias
  ni citas indefinidas, 0 `Float too large`, biber sin avisos.
- **25 entradas citadas** (las 22 de siempre más las tres de la ciencia del diseño); las tres
  pedagógicas quedan en el `.bib` sin citar, como se decidió.
- **Términos prohibidos: cero** en los once capítulos (el único hit de «esta etapa» está en los
  agradecimientos y significa otra cosa).
- **Universo de contenido**: 18 dentro + 31 fuera = 49, sin repeticiones, sin solapamientos y
  sin ítems por clasificar. Comprobado por script sobre los códigos de la tabla y de su nota.
- **Oraciones de 70 palabras o más: 14**, frente a las 101 que medía la auditoría de la v4.
- 152 `\label`, sin duplicados; ningún `DATO PENDIENTE` ni `\pendiente` en el documento.
- Páginas revisadas en imagen: planteamiento del problema, Tabla 1.1, §1.13, tabla de contraste
  de la hipótesis y conclusiones.
