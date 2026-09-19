# Tesis v4: alternativa 3 («caja negra → bajo criterio») aplicada sobre la v1

**Fecha**: 2026-09-19 · **Autor**: Claude (sesión con el autor) · **Estado**: terminado, espera revisión del autor

## Qué se pedía

El autor confirmó la **alternativa 3** del documento
`tesis/alternativas/alternativas_causa_efecto.pdf` (eje pedagógico ligero con el molde de
Miranda) y pidió: una **v4 construida sobre la v1** (no sobre la v3), con las tres fuentes
nuevas que él ya descargó, el **respaldo de citas actualizado** y los PDF **resaltados** con
los nombres de la convención del proyecto.

## Qué se hizo

- **`tesis/main_v4.tex`** + **`tesis/capitulos_v4/`** (resumen, nomenclatura, introducción,
  cap. 1, §2.1, cap. 3, conclusiones; el resto se lee de `capitulos/`). Compila con
  `latexmk -pdf main_v4.tex`: **167 hojas, 0 indefinidas, 0 desbordes, 0 flotantes grandes,
  biber sin avisos**. v1, v2 y v3 intactas.
- **Eje**: problema «¿de qué manera el uso del software de análisis estructural como caja
  negra podrá afectar en el bajo criterio para interpretar la respuesta estructural obtenida
  por el MEF en los estudiantes de la Carrera de Ingeniería Civil de la UATF en la gestión
  2026?». VI = forma de exponer el canal y la respuesta; VD = criterio del estudiante;
  interviniente = EduFEM. Objeto = proceso de enseñanza-aprendizaje; campo = medios
  didácticos (software + memoria). OG con «para qué» = mejorar ese criterio.
- **Cinco OE en escalera** (diagnosticar → Cap. 1 §1.1 y Tabla 1.1; fundamentar → Cap. 1;
  desarrollar → Cap. 2; verificar → Cap. 3; validar → Cap. 3 §3.6.2). **Tres PI**, una por
  cláusula de la hipótesis: (a) exposición, (b) corrección, (c) validez de contenido y
  coherencia. **Hipótesis** en futuro afirmativo con el molde de Miranda, comprobada en su
  parte de diseño y contenido; el efecto se fundamenta y se deja a la prueba de campo.
- **Tabla 2.1** con una sola pareja VI/VD (la VD con dos dimensiones medidas y una no medida);
  lo numérico como «factores» y «magnitudes medidas». **Matriz de consistencia** de 5 filas.
  §2.1.4 define el **universo de contenido**: 15 destrezas (FEA13–18, FEA26–34) + 3 conceptos
  (FEM2, FEM8, FEM9) del consenso de 67 expertos de Pérez-Santiago y Campos 2023, con la
  salvedad de generalización que el propio artículo declara (p. 1171).
- **Cap. 3 §3.6**: 3.6.1 cobertura (lo de la v1) + 3.6.2 **tabla de especificaciones**
  (18/18 con instrumento y evidencia) y **matriz de principios** (4/4). §3.7 con la lectura
  conjunta; §3.8 contrasta las tres cláusulas. Conclusiones: una por OE, aportes
  (+ instrumentos), limitaciones («validez de contenido no es efectividad»), recomendación
  de **prueba de campo** con instrumento de juicio de resultados.
- **Tabla 1.1** con fila nueva «Lectura de la respuesta» y §1.1 con la frase de Suárez 1998
  p. 253 (su post-proceso «no explica el suavizado nodal… meramente descriptivo»); la
  Introducción cita la p. 246 (caja negra) del mismo artículo.
- **Bibliografía**: `referencias.bib` pasa a **25 entradas** con `rutten2012learning`,
  `chi2014icap` y `atkinson2000learning` (metadatos leídos de los ejemplares; DOI de Atkinson
  del registro de SAGE, no impreso). Cada una citada ≥ 2 veces. Ejemplares copiados a
  `tesis/bibliografia/` con la convención `Autor ANO - Titulo.pdf`.
- **Respaldo de citas**: `verificado.json` pasa a 25 fichas (+3) y suma respaldos a Suárez
  (pp. 246 y 253, páginas escaneadas → nota anclada) y a Pérez-Santiago (pp. 1160, 1162-1163,
  1168, 1171). `resaltar.py`: 169 pasajes → 109 resaltados + 60 notas en 25 PDF.
  `respaldo_citas.pdf` regenerado: 47 páginas. Copia previa del JSON en
  `verificado.json.bak_v4`.
- **Seguridad**: la carpeta `tesis/bibliografia/Bibliografia pedagogico/` (12 PDF con
  copyright) **no estaba ignorada** y se iba a subir al repo público; se agregó
  `tesis/bibliografia/**/*.pdf` al `.gitignore` raíz.

## Qué se descartó y por qué

- **La v3** como base: el autor la juzgó demasiado pesada. De ella se rescataron solo la
  idea de la tabla de especificaciones y la matriz de principios, recortadas a lo que la v1
  ya tenía (cuatro principios) y al criterio externo publicado (sin Bloom, sin LORI, sin
  Sandoval, sin Nieveen). `capitulos_v3/`, `main_v3.tex` y `referencias_v3.bib` quedan como
  archivo de referencia; **no** se mantienen.
- **du Boulay 1981**: el PDF que el autor bajó con ese nombre es otro artículo
  (Hidalgo-Céspedes et al. 2016, CLEI). No se cita: la idea de caja negra ya tiene página en
  Suárez y en Pérez-Santiago. Conviene borrar ese PDF de la carpeta.
- Las otras 9 fuentes de la carpeta pedagógica (Mayer, D'Angelo, Wieman, Plomp/Nieveen,
  Sandoval, LORI, Squires, Cataldi) no se citan en la v4; quedan disponibles.
- **Puntaje en la matriz de principios**: se dejó en «encarnación comprobable + evidencia»
  para no convertir una autoevaluación en un número.

## Trampas encontradas

- `latexmk` marca «Float too large» para una `table` que crece con una fila: Tabla 1.1,
  Tabla 2.1 y Tabla 3.7 pasaron a `longtable` con `\caption[]{… (continuación)}` en el
  `\endhead` (no duplica la entrada en la lista de tablas). Funciona con el `caption` del
  preámbulo.
- `resaltar.py` busca el pasaje en el texto **con saltos de línea**; el script que agrega
  respaldos normaliza espacios y ligaduras (`ﬁ`, `ﬂ`) antes de buscar. Atkinson es OCR de
  JSTOR: el pasaje de la p. 187 no se encontró letra por letra y quedó como nota anclada.
- Conteo: FEA13–18 + FEA26–34 son **15** destrezas, no 16 (corregido en el PDF de
  alternativas).

## Qué quedó pendiente

1. **Revisión del autor**: Introducción (problema en negativo, 5 OE, hipótesis), §2.1.2 y
   §2.1.4, Tabla 3.7 (cada celda afirma qué hace el software) y las conclusiones.
2. **`% DATO PENDIENTE`** en §2.1.4: nombre, sigla y semestre de la asignatura en que se
   introduce el MEF.
3. Si la v4 se adopta: mover `capitulos_v4/*` sobre `capitulos/`, borrar `main_v4.tex`, y
   rehacer las láminas de problema, hipótesis, variables, matriz y §3.6 de
   `tesis/presentacion/guion.json` y el video. Decidir qué hacer con la v3 (borrarla o
   dejarla) y con `main_v2.tex` (Arial), que sigue leyendo `capitulos/`.
4. Confirmar la cita de la p. 187 de Atkinson abriendo el PDF (OCR).

## Verificación

- `latexmk -pdf main_v4.tex`: EXIT 0, 167 hojas, 0 refs/citas indefinidas, 0 `Overfull`,
  0 `Float too large` tras convertir las tres tablas, `main_v4.blg` sin avisos.
- Páginas revisadas en imagen: Tablas 2.1, 2.2, 3.7, 3.8, §3.8 y las referencias (las tres
  entradas nuevas salen en Vancouver correcto, [19], [20] y otra).
- `resaltar.py` y `gen_respaldo.py` corrieron sin error; `respaldo_citas.pdf` compila (47 p.).
- `alternativas_causa_efecto.pdf` recompilado con el conteo corregido (12 p., 0 desbordes).
