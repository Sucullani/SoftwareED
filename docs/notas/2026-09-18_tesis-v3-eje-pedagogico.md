# Tesis v3: eje causa-efecto pedagógico (alternativa C)

**Fecha**: 2026-09-18 · **Autor**: Claude (sesión con el autor) · **Estado**: terminado, espera revisión del autor

## Qué se pedía

El autor pidió alternativas de eje causa-efecto porque la tesis mezclaba varios enfoques y
la forma no cerraba (dos pares VI/VD, tres nomenclaturas de variables, hipótesis con
cláusulas de los dos pares). Se le presentaron cuatro (A diseño purgado, B numérico,
C pedagógico, D sin par causal). Eligió **C** («encaja con el canon de una tesis; las otras
parecen proyectos de grado») y pidió una **versión v3 completa** que aplique C sin estudio
con estudiantes ni juicio de expertos, validando por la literatura, y que cite la
bibliografía nueva recomendada.

## Qué se hizo

- **`tesis/main_v3.tex`** compila con `latexmk -pdf main_v3.tex` (pdflatex + biber):
  **178 hojas, 0 referencias indefinidas, 0 desbordes, 0 flotantes grandes, biber sin
  avisos**. Comparte con v1/v2 el preámbulo, la portada, las figuras, `referencias.bib`
  y los capítulos que no cambian (`03_diseno_implementacion`, `06_anexos`,
  `07_anexo_memoria`, `00_preliminares`).
- **`tesis/capitulos_v3/`**: copias reescritas de `00_resumen`, `00b_nomenclatura`
  (+ ICAP, LORI, PI), `01_introduccion`, `02_marco_teorico`, `02b_diseno_metodologico`,
  `04_resultados` y `05_conclusiones`. Las etiquetas (`sec:*`, `tab:*`) que los capítulos
  no tocados referencian se conservaron con el mismo nombre.
- **`tesis/bibliografia/referencias_v3.bib`**: 16 entradas nuevas que **solo** carga
  `main_v3.tex` (`\addbibresource` en el maestro, después del preámbulo). Cada una se
  cita al menos dos veces. Metadatos verificados contra el registro del editor o
  repositorio (no contra un ejemplar): Plomp y Nieveen 2013 (SLO, acceso abierto);
  Nieveen y Folmer 2013; Sandoval 2014; Sweller, van Merriënboer y Paas 2019 (acceso
  abierto); Atkinson et al. 2000; Mayer 2009; Chi y Wylie 2014; du Boulay, O'Shea y Monk
  1981; Rutten et al. 2012; D'Angelo et al. 2014 (SRI, acceso abierto); Wieman, Adams y
  Perkins 2008; Squires y Preece 1999; Leacock y Nesbit 2007 (acceso abierto); Anderson y
  Krathwohl 2001; Cataldi 2000 (SEDICI, acceso abierto); Galvis 1992.

### El diseño de la v3, en una página

- **Problema científico** (única formulación): «¿de qué manera la exposición transparente,
  interactiva y numéricamente verificable del canal de cálculo […] mediante un software
  educativo que opera sobre el modelo del propio estudiante, apoya la comprensión de los
  fundamentos del método en los estudiantes de ingeniería civil?». **VI** = forma de
  exponer el canal; **VD** = comprensión de los fundamentos; **interviniente** = EduFEM.
- **Objeto de estudio** = proceso de enseñanza y aprendizaje del análisis de medios
  continuos en elasticidad plana por el MEF (vuelve a ser pedagógico, como exige C);
  **campo de acción** = los medios didácticos: el software y la memoria.
- **Modelo de investigación** = investigación basada en diseño, **primer ciclo**: la
  unidad de análisis es el artefacto. Criterios de Nieveen y Folmer: relevancia y
  consistencia (sobre el diseño y la literatura), practicidad **esperada** (sin usuarios)
  y efectividad (segundo ciclo, prueba de campo).
- **Hipótesis** en futuro afirmativo («…apoyará la comprensión…») contrastada en cuatro
  cláusulas comprobables sin estudiantes: (a) relevancia, (b) corrección (las cifras de
  V&V de siempre), (c) consistencia, (d) practicidad esperada. La efectividad queda como
  **conjetura teórica** del mapa de conjeturas.
- **Siete objetivos específicos** (OE7 nuevo: evaluar el potencial didáctico y diseñar
  la prueba de campo) y **cuatro preguntas de investigación**, una por cláusula.
- **Tabla 2.1** con una sola pareja VI/VD (la VD con tres subdimensiones medidas y una
  no medida); las magnitudes numéricas pasan a «factores» y «magnitudes medidas», sin las
  palabras independiente/dependiente. Desaparecen el párrafo duplicado de «aporte,
  atributo, efecto» y la oración «no deben confundirse».
- **Cap. 1**: §1.2 crece de cuatro a **diez principios** (caja de cristal, carga
  cognitiva y ejemplo resuelto, multimedia, ICAP, simulaciones + los cuatro específicos
  del MEF + carga cognitiva en la interfaz) y aparece **§1.3 Evaluación de software
  educativo e investigación basada en diseño** (IBD, criterios de Nieveen, mapa de
  conjeturas, tabla de especificaciones, heurísticas de Squires y Preece, LORI, Galvis y
  Cataldi). Las secciones del MEF corren un número.
- **Cap. 3 §3.6** pasa a «Potencial didáctico»: 3.6.1 cobertura (lo de antes), 3.6.2
  **tabla de especificaciones** (11 unidades × 5 niveles de Bloom: 11/11 en recordar,
  comprender y aplicar; 8/11 en analizar; 7/11 en evaluar), 3.6.3 **mapa de conjeturas +
  matriz de trazabilidad** (10/10 principios con encarnación; 8 cumple, 2 parcial), 3.6.4
  **LORI** (4 cumple, 3 parcial, 1 no evaluable sin usuarios, 1 no aplica). §3.7 suma la
  interpretación del potencial y §3.8 contrasta las cuatro cláusulas.
- **Conclusiones**: una por OE (siete), aportes con el bloque metodológico, limitaciones
  («potencial no es efectividad»; autoevaluación), y la recomendación «Segundo ciclo:
  prueba de campo» con población, muestra dirigida, diseño preprueba-posprueba,
  tratamiento (las estructuras de tarea del mapa), instrumento y análisis.

## Qué se descartó y por qué

- **Editar `capitulos/` en el lugar**: rompería la v1 y la v2, que el autor todavía no
  decidió abandonar. Por eso `capitulos_v3/` y `referencias_v3.bib` separados; adoptar
  la v3 es mover archivos, no reescribir.
- **Agregar las referencias nuevas a `referencias.bib`**: ese archivo describe los
  ejemplares que el autor tiene (regla del 2026-09-09). Las nuevas no están descargadas.
- **Puntuar LORI con números**: una autoevaluación con puntajes se lee como
  autocomplacencia; se usó un veredicto en cuatro grados con evidencia por ítem y el
  criterio de aceptación exige evidencia, no puntaje.
- **Inventar localizadores de página** para las fuentes nuevas: contra la skill
  `tesis-bibliografia`. Se dejaron marcados.
- **Reformular «estudio piloto» como estudio reducido**: en Sampieri la prueba piloto
  ensaya el instrumento; lo que C exige se llama prueba de campo (o cuasiexperimento
  preprueba-posprueba). La tesis usa «prueba de campo».

## Trampas encontradas

- `grep -P` con `\x{2190}` falla en el Git Bash de esta máquina («character value too
  large») y el heredoc con acentos sigue saliendo en cp1252: el escáner de Unicode se
  escribió con `Write` en el scratchpad y se corrió con el Python del `.venv`
  (`scan_unicode.py`, resultado: 0 problemas).
- En la matriz de consistencia, «importación/exportación» en una celda `p{}` se partía
  como «importació-n/exportación»; se cambió por «importación y exportación».
- La `longtable` con `\caption[]{…(continuación)}` en `\endhead` evita una segunda
  entrada en la lista de tablas; funciona con el paquete `caption` del preámbulo.

## Reacción del autor (mismo día) y documento de alternativas

Al ver la v3 el autor la encontró **demasiado pesada** (dieciséis fuentes, cuatro cláusulas,
dos ciclos) y pidió: validar pedagógicamente con la literatura que ya tiene, una tesis
**lineal con una sola brecha**, y alternativas de eje causa-efecto **pedagógicas** que sigan
los tres moldes de Miranda (problema como interrogante con VI/VD, objeto y campo, OG con
verbo + qué + cómo + para qué, escalera de OE, hipótesis con tres variables). Propuso como
efecto «el bajo criterio de los estudiantes para interpretar la respuesta estructural».

Resultado: `tesis/alternativas/alternativas_causa_efecto.tex` → `.pdf` (12 páginas,
0 desbordes; no forma parte de la tesis). Contiene: (1) qué valida la literatura (validez de
contenido y coherencia del diseño) y qué no (efectividad); (2) el consenso de 67 expertos de
Pérez-Santiago y Campos 2023 como **criterio externo de validez de contenido** (ítems FEM1–15
y FEA1–34, pp. 1162–1163; ranking p. 1168), con la salvedad de generalización que el propio
artículo declara (p. 1171); (3) el molde de las guías; (4) siete parejas causa→efecto;
(5) tres alternativas pedagógicas desarrolladas con el molde: 1 «exposición → comprensión»,
2 «memoria verificable → capacidad de verificar y validar», 3 «caja negra → bajo criterio
para interpretar la respuesta estructural» (**recomendada**: forma negativa del ejemplo de la
guía, déficit con diagnóstico publicado, destrezas de ranking alto FEA13–18 y FEA26–34,
instrumento de prueba de campo más fácil); (6) comparación; (7) plan mínimo sobre la **v1**
(no sobre la v3): 5 OE en escalera, una pareja VI/VD, tabla de especificaciones con los ítems
de expertos, matriz de los 4 principios de §1.2, 0 referencias nuevas (1 opcional);
(8) anexo con la correspondencia ítem por ítem EduFEM ↔ Pérez-Santiago, lista para §3.6.

**Consecuencia para la v3**: queda como archivo de referencia; de ella se rescatan la tabla de
especificaciones y la matriz de principios. No se sigue desarrollando salvo pedido.

## Qué quedó pendiente

1. **Decidir si la v3 reemplaza a la v1/v2** (el autor). Si sí: mover `capitulos_v3/*`
   sobre `capitulos/`, fusionar `referencias_v3.bib` en `referencias.bib`, borrar
   `main_v3.tex` y actualizar `main_v2.tex` (Arial) para que apunte a los mismos
   capítulos. La presentación (`tesis/presentacion/guion.json`) y el video siguen
   sincronizados con el eje A: hay que rehacer las láminas de problema, hipótesis,
   variables, matriz y §3.6.
2. **Conseguir los 16 ejemplares** (siete son de acceso abierto, listados arriba),
   guardarlos como `Autor ANO - Titulo.pdf` en `tesis/bibliografia/`, y completar los
   **20 `% LOCALIZADOR PENDIENTE`** (2 en la Introducción, 16 en el Cap. 1, 2 en §2.1) y
   el respaldo en `tesis/respaldo_citas/`. Sin ejemplar, la regla de la skill es no
   citar: si alguna fuente no se consigue, quitar la cita y el principio que sostiene.
3. **`% DATO PENDIENTE`** en §2.1.4: nombre, sigla y semestre de la asignatura en que se
   introduce el MEF en la Carrera (plan de estudios vigente).
4. Confirmar en los ejemplares el lugar de edición de Mayer 2009 y de Galvis 1992, y el
   tipo exacto de la tesis de Cataldi.
5. Revisar con ojo de autor las tres tablas nuevas (3.7, 3.8, 3.9) y la LORI (3.10):
   cada celda afirma algo del software; si alguna función descrita no existe tal cual en
   la versión distribuida, corregir la celda, no el software.

## Verificación

- `latexmk -pdf main_v3.tex` desde `tesis/`: **EXIT 0**, 178 hojas, 0 referencias o
  citas indefinidas, 0 `Overfull`, 0 `Float too large`, `main_v3.blg` sin avisos.
- Páginas renderizadas y revisadas: Tablas 2.1, 2.2, 3.7, 3.8, 3.9, 3.10, §3.8, índice y
  las tres hojas de referencias (las 16 entradas nuevas salen en Vancouver correcto).
- Cada clave nueva se cita ≥ 2 veces (contado con `grep`).
- `main.tex` y `main_v2.tex` **no se tocaron** y no leen nada de la v3.
