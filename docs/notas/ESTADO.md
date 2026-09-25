# Estado del trabajo

**Última actualización**: 2026-09-25

> **Nota de sincronización (2026-09-25)**: **todo el trabajo está en `origin/main`.** El 25-09
> se integró en ocho commits (`b9a5b61`…`ef1687b`) lo que venía sin commit desde el 22-09: el
> paso de v1 a v4 a `tesis/archivo/`, el retiro de PyMuPDF (software, instalador y tesis), las
> correcciones de V&V, los documentos de estudio (MMS paso a paso y solucionador disperso),
> **final1**, **final2**, **final3** (observaciones del Ing. Miranda), la presentación
> interactiva con su video, la defensa metodológica y este estado. Las marcas «sin commit» que
> quedan en el historial de abajo son de su fecha y ya no aplican.

> Lo primero que lee un agente al entrar. Qué está en curso, qué quedó a medias y qué
> decisión espera al autor. Se edita; lo que deja de aplicar se borra.
> Convención: [README.md](README.md).

## Contexto del proyecto

EduFEM está **funcional y empaquetado**: la GUI corre, el motor pasa su batería de tests,
hay `.exe` (`dist/EduFEM/`, onedir) e instalador (`installer/EduFEM.iss` → `EduFEM-Setup.exe`).
El trabajo activo no es construir features nuevas, sino **pulir** el software y **cerrar la
tesis** (versión vigente `tesis/main_final3.tex`, 189 páginas, compila limpio con XeLaTeX).

## En curso

| Tema | Dónde | Estado |
|---|---|---|
| **TESIS FINAL3 (versión vigente)** | `tesis/main_final3.tex` + `tesis/capitulos_final3/` | **Hecha el 2026-09-25, en `origin/main`. Se compila con XeLaTeX** (`latexmk -xelatex main_final3.tex`). Aplica las **observaciones del Ing. Miranda** (tribunal), adaptadas al contenido y no al pie de la letra: problema, objetivo general e hipótesis en el molde del tribunal y sin la universidad (queda solo en la delimitación); VI = transparencia del procedimiento de cálculo, VD = trazabilidad y verificabilidad del procedimiento de cálculo; **tres objetivos específicos, uno por capítulo** (Fundamentar, Desarrollar, Verificar y validar; «Diagnosticar» fuera), que dan su título a cada capítulo; Introducción por apartados; Conclusiones en **tríada** con Figuras CR.1-CR.2 y Tabla CR.1; Figura 2.1 nueva; **Times New Roman 12 justificado**, con las fórmulas en Latin Modern. Lleva también el retiro de PyMuPDF de final2. El título de cada capítulo es su objetivo completo. 189 páginas, 0 errores, 0 desbordes, 0 referencias indefinidas, 153 etiquetas intactas más 4 nuevas. Diagnóstico para el autor: `tesis/observaciones_miranda/diagnostico_miranda.pdf`; registro: `tesis/auditoria_final/IMPLEMENTACION-FINAL3.md`; nota: [2026-09-25_observaciones-miranda-final3.md](2026-09-25_observaciones-miranda-final3.md) |
| **TESIS FINAL2 (segunda iteración, no se edita)** | `tesis/main_final2.tex` + `tesis/capitulos_final2/` | **Hecha el 2026-09-25, en `origin/main`.** Segunda iteración de mejora continua: se verificó lo implementado en final1 y se revisó el documento entero por diez unidades (portada a Anexo G) contra el código, las fuentes en PDF y los datos de V&V; cada hallazgo se volvió a contrastar antes de aplicarlo. 256 disposiciones (236 aplicadas, 8 para el autor, 2 descartadas; el resto ya resuelto o cubierto). 197 páginas, 0 errores, 0 desbordes, ninguna etiqueta perdida. **Cambios de fondo que el autor debe revisar** (ED-Elas2D sí expone las matrices y está en inglés; dos versiones del motor unidas por la prueba de regresión; det J negativo no detiene el cálculo; «Resolver de todos modos»; MMS fuera de la interfaz; V&V fuera del instalador; tiempos de la Tabla 3.9), decisiones pendientes y **observaciones sobre el software** (no se tocó el código): `tesis/auditoria_final/IMPLEMENTACION-FINAL2.md`. Fuera de la tesis solo tocó `tesis/figuras/generar_figuras.py` (pie de la Figura 2.2) |
| **TESIS FINAL1 (primera iteración, no se edita)** | `tesis/main_final1.tex` + `tesis/capitulos_final1/` (con su `preambulo.tex`, `referencias.bib`, `CRITERIOS.md` y `figuras/`) | **Hecha el 2026-09-23, en `origin/main`.** La final con la **auditoría de redacción** (`tesis/auditoria_final/`, del 22-09) implementada entera: los 299 hallazgos vivos tienen disposición (184 aplicados, 58 adaptados, 16 cubiertos, 13 decisiones del autor, 13 diferidos, 3 parciales, 7 descartados, 5 sin cambio), más 4 observaciones del crítico y 3 hallazgos nuevos verificados contra el código. 194 páginas, 0 errores, 0 desbordes, ninguna etiqueta perdida. **Registro y lo que queda en manos del autor**: `tesis/auditoria_final/IMPLEMENTACION-FINAL1.md`. Convención de versiones (final → final1 → final2…, cada una intacta): `tesis/README.md`. Tocó tres archivos fuera de la tesis: `tests/vv_timoshenko.py` (σx de SAP2000 con los seis decimales de la captura), `tests/vv_mms.py` (tilde del rótulo) y `tesis/figuras/generar_figuras.py` (rótulo de la Figura 2.2), con sus datos y figuras regenerados |
| **TESIS FINAL (base auditada)** | `tesis/main_final.tex` + `tesis/capitulos_final/` | Se conserva **exactamente** como se auditó (commit `ee7b5a6`), como base de comparación de final1; no se edita. **Terminada el 2026-09-21 y en `origin/main`.** Autocontenida: no lee de `capitulos/` ni de `capitulos_v4/`, y las versiones v1 a v4 quedan como archivo. Eje tecnológico: causa = uso del software como caja negra, efecto = **baja trazabilidad y verificabilidad del análisis** (propiedad del medio de cálculo, medible en el software). Dos cláusulas, las dos comprobadas dentro del documento: **no hay prueba de campo ni efecto diferido**. Método: ciencia del diseño (Hevner, Peffers, Wieringa). Compila limpio: 189 hojas, 0 errores, 0 desbordes, 0 referencias indefinidas. **Reglas de edición obligatorias**: `tesis/capitulos_final/CRITERIOS.md`. El mismo día se aplicaron las correcciones de la **auditoría de defensa** (`docs/auditorias/Auditoria_defensa_tesis_EduFEM.md`): alineación de problema, hipótesis y conclusión con lo que el trabajo evalúa; tres errores técnicos comprobados con contraejemplo (von Mises, Jacobiano, base del Q4); la membrana de Cook con fuente publicada y **contraste externo de las cinco mallas**; licencias y alcance del CSV; FEA18 reforzado sin bajar el 18/18. **Los preliminares quedan fuera para la predefensa** (una línea comentada en `main_final.tex`). 187 hojas. Detalle: [2026-09-21_tesis-final.md](2026-09-21_tesis-final.md) y [2026-09-21_correcciones-auditoria-defensa.md](2026-09-21_correcciones-auditoria-defensa.md) |
| **Defensa metodológica (tesis tecnológica frente al molde experimental)** | `tesis/defensa_metodologica/` | **Hecha el 2026-09-23, en `origin/main`.** `contexto_defensa.pdf` (23 p., documento de estudio: la tesis en una página, respuesta madre, 14 argumentos con cita literal y página, material docente lámina por lámina, 34 preguntas) y `respaldo_diferencia.html` (6 láminas animadas de respaldo, sin internet, con guion). No toca la tesis ni `presentacion/final/`. **Hallazgo**: el *Manual de Procesos Académico-Administrativos* UATF 2022, p. 93, trae las definiciones de tesis y proyecto de grado del Reglamento General del S.U.B.: cierra en parte H-1. Detalle: [2026-09-23_defensa-metodologica.md](2026-09-23_defensa-metodologica.md) |
| **MMS paso a paso (documento de estudio)** | `docs/vyv/mms_paso_a_paso/` | **Hecho el 2026-09-23, en `origin/main`.** `mms_paso_a_paso.pdf` (21 p.): el MMS desde cero siguiendo los pasos de Salari y Knupp, con el caso base resuelto a mano (Q4, `N = 2`, un solo nodo libre: rigidez, ensamblaje, fuerzas, sustitución estática, normas `L²`/`H¹` punto por punto), el refinamiento y las tasas. Todas las cifras salen de `generar_datos.py`, que usa una réplica independiente (`mms_independiente.py`, sin importar EduFEM) y **aborta si no coincide con EduFEM** (hoy coincide con los 20 valores de `mms_q4/q9.csv`). La §8 documenta el límite del MMS de la decisión abierta de abajo. Cómo regenerar: `docs/vyv/README.md` |
| **Presentación interactiva y video de la tesis final** | `tesis/presentacion/final/` (`Defensa_EduFEM.html`, `Presentar_defensa.bat`, PDF de respaldo) y `tesis/presentacion/video/Defensa_EduFEM_final.*` | **Construidos el 2026-09-23** para la tesis final. Presentación HTML propia, sin internet: 57 láminas + 6 de respaldo para preguntas, animaciones con los datos del motor (exportador en `herramientas/`), laboratorios que se manejan con el mouse (trazabilidad del nodo 7 hasta los datos, mapeo, Jacobiano, Gauss, ensamblaje, sonda y Mohr, MMS, Timoshenko, Cook, la lección de la extrapolación), botones entre láminas con «Volver», vista del orador y modo narrado. El video es la misma presentación grabada cuadro a cuadro con voz, subtítulos y capítulos. Sigue `main_final.tex` tal como está en el repositorio, no `main_final1.tex`; una auditoría de fidelidad contra `main_final.pdf` dejó 25 observaciones, todas aplicadas. Desde el mismo día hay una **versión 2 estilo PowerPoint** (`Defensa_EduFEM_v2.html`, generada desde la v1 por `herramientas/generar_v2.mjs`) y su conversión a **PowerPoint** (`Defensa_EduFEM_v2.pptx`: un clic por paso, enlaces, notas, videos; `extraer_pptx.mjs` + `construir_pptx.py`, verificada paso por paso contra la HTML). **En `origin/main`.** Falta que el autor mire el video, ensaye con la vista del orador y pruebe el lanzador en la sala. Detalle: [2026-09-23_presentacion-interactiva-final.md](2026-09-23_presentacion-interactiva-final.md). Las v1 y v2 (PowerPoint, ejes anteriores) quedan como archivo |
| Versiones v1 a v4 de la tesis y auditoría de la v4 (archivo, no se mantienen) | `tesis/archivo/` (`v1_v2/`, `v3/`, `v4/` con `auditoria_v4/`) | **Movidas el 2026-09-23, en `origin/main`**, para que en `tesis/` quede solo la línea de versiones finales. Cada carpeta conserva su fuente y su PDF compilado; qué es cada una y cómo recompilarla si hiciera falta: `tesis/archivo/README.md`. Las reemplazó la tesis final (2026-09-21). Detalle de cada una: [2026-09-18_tesis-v3-eje-pedagogico.md](2026-09-18_tesis-v3-eje-pedagogico.md), [2026-09-19_tesis-v4-alternativa-3.md](2026-09-19_tesis-v4-alternativa-3.md) |
| Cierre de la tesis (v1/v2, eje de diseño) | `tesis/` | Compila limpio (158 hojas, APA doble espacio). La auditoría integral del 2026-09-11 está **implementada** salvo lo que el autor reservó (1.5, 1.6, 5.4), y la **auditoría por sesiones** ([AUDITORIA_TESIS.md](../auditorias/AUDITORIA_TESIS.md)) quedó **implementada el 2026-09-16**: 45 de 47 hallazgos resueltos, H-13 parcial y H-1 abierto (el Reglamento de Graduación, que solo el autor puede conseguir). En `origin/main`; el autor revisa (ver *Decisiones abiertas*). Pendiente que necesita la GUI: recapturar las Figuras 3.3, B.1 y B.6-B.13 a mayor resolución |
| Deuda técnica de la auditoría 2026-06-10 | repo | **Cerrada el 2026-09-06** (Top-10 + medios y bajos de §1, §2, §5 y §6). Único pendiente: decidir si se cablea `TheoryDoc.margin_formula()` en la memoria — cambia el layout del PDF, así que necesita validación visual del autor |
| Mejora continua del software | `docs/rutina/` | **Activa desde el 2026-09-08**: rutina horaria de claude.ai que trabaja directo sobre `main`, una área por sesión con rotación de 14. Qué hizo cada sesión: [../rutina/BITACORA.md](../rutina/BITACORA.md); qué falta y qué espera al autor: [../rutina/BACKLOG.md](../rutina/BACKLOG.md) |
| Distribución del `.exe` | `installer/` | Vía principal decidida: instalador Inno Setup por usuario, sin admin. Sin firma de código (decisión tomada). Empaquetado **onedir** desde el 2026-09-10 (arranque 3 s en vez de 12; el entregable sigue siendo un solo archivo). Desde el 2026-09-25 **sin PyMuPDF** (AGPL-3.0) ni cinco extras que se colaban desde el `.venv`, y con los avisos de licencia de terceros (`installer/dist_extra/LICENCIAS-TERCEROS.txt`, lo genera `tools/licencias_terceros.py`): instalador de 95,6 a 78,7 MB. **En `origin/main`** |

## Decisiones abiertas (esperan al autor)

- **Auditoría general de final3 (2026-09-25)**:
  [`tesis/auditoria_final/AUDITORIA-GENERAL-FINAL3.md`](../../tesis/auditoria_final/AUDITORIA-GENERAL-FINAL3.md).
  **Veredicto**: defendible; solo H1 es una afirmación falsa (el MMS y la deformación plana,
  la decisión de abajo). No se tocó la tesis ni el código. Trae un banco de unas 60 preguntas
  del tribunal con respuesta y página. **Hallazgos nuevos, todos verificados**:
  - H2: la flecha de Timoshenko medida respecto del nodo de apoyo **crece** al refinar
    (0,18/0,26/0,35/0,44 %), por la singularidad del apoyo puntual (Flamant); respecto de la
    sección extrema es −0,03 % en toda malla.
  - H3: τxy en B converge O(h²) (11,9 → 2,89 → 0,72 → 0,18 %).
  - H4: los umbrales de σx < 1 % y del equilibrio entraron a `tests/vv_timoshenko.py` el 16-09,
    con los resultados conocidos desde junio; conviene matizar «fijados de antemano».
  - H5: faltan en «Versión evaluada» el hash `ec5876e` (PyMuPDF) y `9232819` (σx de SAP2000).
  - H6: más rótulos en inglés que los dos declarados, y el 23,95 de Cook en el menú de la
    interfaz.
  - H7: el PDF de XeLaTeX codifica 427 «;» como U+037E; se arregla con
    `\XeTeXgenerateactualtext=1` (probado).
  - H8: **bug del software**, el deshacer no revierte la edición de un vértice en la tabla de
    Elementos (`Element.to_dict` devuelve la lista viva).
  - H9: la p. 2 atribuye a Pérez-Santiago, p. 1160, algo que no dice; la p. 1164 respalda
    excluir FEM3.

- **El MMS no verifica `λ` ni `D33` (2026-09-23)** — la `u_M` de `tests/vv_mms.py`
  (`sin πx sin πy`, `cos πx cos πy`) tiene `tr(ε) = 0` y `γxy = 0` en todo punto, así que
  `b = π²(D11 − D12)(…)`: el término fuente es el mismo en tensión y en deformación plana, y la
  prueba no distingue los dos estados. Comprobado saboteando `fem/constitutive.py`: si la rama
  DP devolviera la `D` de TP, o si `D33` estuviera duplicado, el MMS pasaría 8/8 (lo detectan
  `test_vv_extensions` [8/8] y Cook, respectivamente). Reproducible con
  `docs/vyv/mms_paso_a_paso/experimento_sabotaje.py`. **El motor está bien**; lo que sobra es
  lo que la tesis le atribuye al MMS: `02b_diseno_metodologico.tex:136` («ejercita… las dos
  matrices constitutivas»), `04_resultados.tex:30` (término fuente «deducido en cada caso de la
  ley constitutiva»), `04_resultados.tex:61` («descarta errores… en la matriz constitutiva de
  ambos estados planos») y `05_conclusiones.tex:47` («la deformación plana solo se verifica con
  el MMS»). **Qué decide el autor**: (a) cambiar la `u_M` (probada: `v = cos πx cos 2πy`
  conserva las tasas y detecta los dos errores) y regenerar CSV, figuras y tablas de la tesis, o
  (b) dejar el código y corregir esas cuatro frases, citando el test [8/8] como verificación de
  la deformación plana. La misma idea está en `04_resultados.tex:357` («descarta errores… en
  la matriz constitutiva de ambos estados planos»). La presentación de defensa ya no repite
  ninguna de esas afirmaciones (ver `tesis/presentacion/final/README.md`); con la opción (a)
  hay que regenerar sus datos y rehacer el respaldo de deformación plana. Los números de línea
  de arriba son de `capitulos_final/`; la decisión se aplica sobre la versión vigente,
  `capitulos_final3/`, donde siguen las mismas frases. La implementación de la auditoría dejó
  para este momento los tres hallazgos que las reescriben (H-097, H-100, H-197), para no
  escribirlas dos veces.
  - *Ampliación (auditoría general, 25-09):* en `capitulos_final3/` hay dos frases más, además
    de las cuatro de arriba: `05_conclusiones.tex:49` («verificada por soluciones manufacturadas
    en ambos estados») y `02b_diseno_metodologico.tex:149` («…ambos estados planos»). Lista
    completa con páginas en H1 de `AUDITORIA-GENERAL-FINAL3.md`.
  - Otra ampliación: un error en el `D33` **solo de la rama de deformación plana** no lo
    detecta ninguna prueba de la batería. Cook es de tensión plana y
    `test_vv_extensions` [8/8] no ve D33.

- **Material de defensa desactualizado por el retiro de PyMuPDF (2026-09-25)** — el software
  ya no lleva PyMuPDF (ver *Hecho recientemente*), pero el autor pidió **no** tocar todavía el
  material de defensa y dejar anotado qué falta: (1) `tesis/presentacion/final/Defensa_EduFEM.html`,
  lámina de respaldo `r-licencia`: la tarjeta «Paquete binario · + AGPL-3.0 de PyMuPDF» pasa a
  decir que el paquete es enteramente de licencias libres y permisivas, con los avisos en
  `LICENCIAS-TERCEROS.txt`; (2) `assets/js/viz/diseno.js`, lámina de diseño: salen la ficha
  «PyMuPDF» y la frase «PyMuPDF se distribuye bajo AGPL-3.0 (nota de la Tabla 2.5)»; (3)
  regenerar lo que sale de esas dos: `Defensa_EduFEM_v2.html` (`generar_v2.mjs`), los dos PDF
  de respaldo (`exportar_pdf.mjs`), el `.pptx` (`extraer_pptx.mjs` + `construir_pptx.py`) y el
  **video** (`grabar_video.mjs` + `montar_video.py`; la narración no nombra PyMuPDF, así que la
  voz se reutiliza); (4) `tesis/defensa_metodologica/contexto_defensa.tex`: la respuesta PD-04
  «¿Bajo qué licencia?» (línea 447) y el ítem «La licencia» (línea 513), y recompilar su PDF.
  Cómo se regenera cada cosa: `tesis/presentacion/final/README.md`.

- **Probar el instalador sin PyMuPDF (2026-09-25)** — instalar `installer/Output/EduFEM-Setup.exe`
  (78,7 MB, antes 95,6) y abrir *Ayuda ▸ Teoría MEF*: debe abrirse en el visor de PDF de
  Windows —la primera vez tras unos 3 s, con «Preparando la Teoría MEF…» en la barra de
  estado— con el nombre «Teoría MEF — EduFEM.pdf» en el título. Exportar también una Memoria.
  Un agente verificó el arranque del `.exe` armado, la compilación real de la Teoría con el TeX
  embebido y el flujo con dobles, pero no el visor abierto en pantalla. Detalle:
  [2026-09-25_pymupdf-retirado.md](2026-09-25_pymupdf-retirado.md).

- **Revisar final3, la versión con las observaciones del Ing. Miranda (2026-09-25)** — **Qué
  decide el autor**:
  - (1) leer en `main_final3.pdf` la Introducción (apartados nuevos), la Figura 2.1 y la matriz
    de consistencia (§2.1.2-2.1.3), y las Conclusiones (tríada, Figuras CR.1-CR.2, Tabla CR.1);
  - (2) aceptar o corregir los ajustes que se hicieron a sus sugerencias, justificados uno por
    uno en `tesis/observaciones_miranda/diagnostico_miranda.pdf`: «escasa» y no «nula»; el molde
    «¿De qué manera… podrá incidir…?»; «procedimiento» y no «proceso»; el «¿cómo?» del objetivo
    general; «verificar» solo en el Cap. 3;
  - (3) confirmar con el Reglamento (H-1) el interlineado y los márgenes, que siguen APA;
  - (4) rehacer la presentación y el video de defensa, que siguen `main_final.tex` y no tienen la
    formulación nueva.

- **Revisar la tesis final (2026-09-21)** — el autor confirmó la formulación de eje
  tecnológico y se construyó la tesis de entrega, que ya está en `origin/main`. **Qué decide
  el autor**: (1) leer la Introducción, la §2.1 y la §3.8 y confirmar que es la tesis que
  quiere defender —hoy sobre `main_final3.pdf`, la versión vigente—; (2) para la **entrega
  final**, descomentar en `main_final3.tex` la línea de `00_preliminares` —que la predefensa
  lleva fuera— y personalizar `capitulos_final3/00_preliminares.tex`:
  dedicatoria, agradecimientos y la decisión sobre el párrafo, hoy comentado, de
  declaración de uso de herramientas de inteligencia artificial; (3) conseguir el Reglamento de Graduación (H-1),
  del que depende también si la carátula debe llevar tutor. La presentación y el video ya
  siguen la tesis final (2026-09-23, `tesis/presentacion/final/`).
  **Esta decisión reemplaza a las dos que seguían abiertas sobre el eje** (elegir el eje
  pedagógico y decidir entre la v3 y la v1/v2): las cuatro versiones anteriores quedan como
  archivo y no se mantienen.

- **Lo que la implementación de la auditoría dejó al autor (2026-09-23)** — ordenado en la
  segunda sección de `tesis/auditoria_final/IMPLEMENTACION-FINAL1.md`: datos que solo él tiene
  (de dónde salen los umbrales de 3 %, 1 % y 1,5 %; si los criterios documentales se fijaron
  antes del cotejo; el localizador de Cook; dónde consultar la monografía de Álvarez de Zayas;
  el anclaje del problema en la Carrera), decisiones de forma (Resumen de unas 310 palabras
  frente al tope de 250 de APA; objetivo general en una sola oración; el 23,96 de Cook «de uso
  extendido» sin cita; el doble listado bibliográfico del Taller 1, a consultar con el tutor) y
  trabajo de figuras (el texto de las capturas imprime a 0,7-1,1 mm; las figuras del Anexo G
  salen de `file_io/figure_export.py` con títulos sin tildes y punto decimal). Dos
  observaciones del software, sin tocar: la explicación de `NEGATIVE_JACOBIAN` en
  `gui/dialogs/health_report_dialog.py` dice que con los vértices en sentido horario «la
  integracion da signos incorrectos», pero la rigidez usa |det J| (`fem/batch.py`) y ese
  elemento se integra bien; y el docstring de `fem/solver.py` da 2,1x para el reordenamiento de
  mínimo grado a 33 k GDL, donde la tesis da 2,9 (el factor depende de la carga del equipo).

- **Presentación y video puestos al día (2026-09-16)** — el guion quedó sincronizado con la
  tesis posterior a la auditoría por sesiones y la capa visual se rediseñó entera (detalle en
  *Hecho recientemente*). **Qué decide el autor**: (1) si la **lámina nueva 30** —cobertura del
  canal, §3.6— se queda como figura apaisada a toda página con el remate «7/7 · 9/9», o vuelve
  a texto con la figura al costado; (2) si el video, que pasó de 25:31 a 30:54 por el texto
  agregado, se acorta subiendo `rate` en `narracion.json` (hoy +11 %); (3) si la tabla del
  estado del arte, que en la tesis tiene siete atributos, se queda con los **seis** que caben
  legibles en la lámina —quedó fuera «fenómenos numéricos observables», que sigue en el remate—.
  Lo que **no** puede hacer un agente: mirar el video y juzgar el ritmo y la pronunciación de
  las cifras, y ensayar los tiempos en vivo contra los 40-45 min del Taller 6.

- **Versión 2 de la tesis en Arial 12 (2026-09-16)** — pedido del autor. `tesis/main_v2.tex`
  comparte preámbulo, capítulos y bibliografía con `main.tex`: lo único que cambia es la
  fuente del cuerpo (Arial real del sistema, por eso **xelatex**); las fórmulas siguen en
  Latin Modern Math. 161 hojas contra 158, y **menos** invasiones de margen que la v1 (13
  contra 27). **Qué decide el autor**: cuál de las dos versiones se entrega al tribunal, y si
  con la v2 conviene reescalar alguna figura. Detalle, y los tres arreglos no obvios que
  necesitó (babel-spanish bajo XeLaTeX, entre ellos):
  [2026-09-16_tesis-version-arial.md](2026-09-16_tesis-version-arial.md).

- **Lo que se cortaba en otro equipo (2026-09-16)** — gate verde con `--con-gui`. Tres reportes
  con capturas, tres causas medidas: (a) las matrices de M2/M3 se
  cortaban porque el ruido de redondeo (`7,11e-18` donde la teoría dice 0) las ensanchaba,
  porque el tope de ancho estaba en píxeles de diseño y no en los reales de la pantalla, y
  porque el overlay se recortaba por abajo **sin scroll** (en 1280x600, M2 perdía 76 px);
  (b) la **Vista 3D** empaquetaba su barra de controles después del área elástica, así que con
  600 px de escritorio Tk le daba **1 px** y desaparecía el botón Cerrar — regla dura 23, más
  otros tres casos de la misma familia; (c) las dos tablas de tensiones de la Memoria se salían
  89,9 pt de la hoja, y en los modelos Q4 la `K_11` simbólica se imprimía **566 pt** afuera.
  Márgenes a 1,5 cm como se pidió, y la unidad apilada bajo el símbolo en todas las tablas.
  **Qué decide el autor**: si la **B de Q9 (3x18)** se parte en dos bloques de 9 columnas —hoy
  sigue siendo una sola matriz con scroll, como estaba decidido— y si el encabezado apilado le
  gusta también en las tablas donde no hacía falta por ancho (se aplicó a todas por
  consistencia). Detalle y mediciones:
  [2026-09-16_se-corta-en-otro-equipo.md](2026-09-16_se-corta-en-otro-equipo.md).

- **Tesis tras la auditoría por sesiones (2026-09-16)** — implementados 45 de los 47 hallazgos
  de [AUDITORIA_TESIS.md](../auditorias/AUDITORIA_TESIS.md). Cinco decisiones
  que el autor debe confirmar porque tocan lo que él mismo fijó o lo que el tribunal ya vio:
  (1) la **hipótesis de diseño** ahora es condicional y comprobable —tres cláusulas con
  criterios a priori en §2.1.6— y el «apoyo al aprendizaje» es un supuesto declarado, no
  contrastado; (2) **OE2, OE4 y OE6 reformulados** (sin «verificado numéricamente»; módulos
  hasta el ensamblaje con post-proceso y memoria para solución y tensiones; memoria principal e
  interoperabilidad instrumental) y el **objetivo general** nombra Python; (3) el **Cap. 1 se
  titula** «Marco teórico del análisis por el Método de los Elementos Finitos en elasticidad
  plana» y tiene una §1.2 nueva de fundamentos pedagógicos, así que todas sus secciones
  corrieron un número; (4) la lista se titula **«Referencias bibliográficas»** y los
  **localizadores de página** siguen una regla única declarada en la Introducción, que
  reemplaza la decisión «Vancouver puro sin página» del 09-09; (5) la **nota de procedencia de
  Álvarez de Zayas** en el `.bib` («empleada en la Carrera de Ingeniería Civil de la UATF como
  referencia del marco metodológico») se redactó a partir del uso que la carrera hace de la
  fuente, no de un dato impreso: confirmar o ajustar. Qué mirar en el PDF: Tabla 2.1 (fila
  nueva), Tabla 3.6 y Figura 3.5 (§3.6, las tres fases sobre el mismo lienzo), Tabla 3.2 (σy,
  τxy y SAP2000), Tabla 3.3 (columna SAP2000), §3.8 (interpretación reunida), Conclusiones y
  Recomendaciones (reescritas, tres grupos por capítulo), Anexo G (G.2.1–G.2.6). **H-1 sigue en
  manos del autor**: conseguir el Reglamento de Graduación y dejarlo en `tesis/normas/`.

- **Tabla 1.1 (`tab:comparativa`) reescrita como matriz de atributos (2026-09-10)**: los
  recursos pasaron a columnas y los atributos a filas, y se agregaron cuatro diferenciadores
  —memoria de cálculo automática, fenómenos numéricos observables, V&V publicada con la
  herramienta y requisitos de ejecución—. Las celdas de los otros recursos salen de
  `tesis/respaldo_citas/` y de los PDF de `tesis/bibliografia/`: donde la fuente no
  documenta el atributo dice **«No consta»**, y las categorías de propósito general llevan
  raya en V&V (criterio de armado del propio texto). De paso se aplicaron dos correcciones
  que el respaldo de citas tenía pendientes para Bishay: «1D/2D» → «2D/3D (barras)» y
  licencia «Libre» → «No declarada (código MATLAB)». Compila limpio, sin overfull. El autor
  decide si conserva «No consta» como valor de celda (es honesto pero visible). La copia de
  esta tabla en `tesis/presentacion/guion.json` ya está actualizada (2026-09-16).
- **Probar el instalador nuevo en un equipo limpio (2026-09-10)**: el entregable pasó a ser
  un instalador terminado (versión en el `.exe`, licencia, imágenes propias del asistente,
  asociación de `.edufem` con icono propio, detección de la app abierta, App Paths,
  desinstalación limpia). Está **sin commit**. Qué comprobar, idealmente en una PC **sin
  MiKTeX** y con un usuario de Windows con **tilde o espacio** en el nombre —el asistente debe
  proponer `C:\ProgramData\EduFEM`—: los accesos directos, que el icono anclado a la barra de
  tareas siga siendo el del acceso directo, el doble clic sobre un `.edufem`, la Memoria de
  Cálculo en PDF y la desinstalación. Falta decidir si **sube `APP_VERSION`** más allá de
  1.0.0 antes de la defensa. Detalle:
  [2026-09-10_instalador-profesional.md](2026-09-10_instalador-profesional.md).
  **Al commitear**: `installer/assets/*.bmp` y `resources/icons/edufem_doc.ico` están sin
  versionar y el `.iss` los necesita — `git add -u` no los toma y el repositorio quedaría sin
  poder compilar el instalador.
- **Auditoría de distribución (2026-09-10)**, encima de lo anterior y también **sin commit**:
  el empaquetado pasó a **onedir**, con lo que el programa instalado abre en **3 s** en vez de
  los 11-15 s que tardaba *siempre* el autoextraíble, ya no deja 189 MB en `%TEMP%` por cada
  cierre anormal y el `EduFEM-Setup.exe` bajó de 126,4 a **95,5 MB**. Aparte, los seis
  `filedialog` no declaraban `initialdir`: el primer «Guardar Como» del alumno dejaba su modelo
  **dentro de la carpeta del programa**, en `AppData`; ahora abren en `Documentos\EduFEM` y
  recuerdan la última usada. Se verificó sobre el paquete instalado (arranque, doble clic sobre
  un `.edufem`, registro, accesos directos, Memoria PDF con el TeX instalado). Qué mirar:
  que «Guardar Como» proponga `Documentos\EduFEM` y el nombre del proyecto. Detalle y lo que
  quedó abierto: [2026-09-10_un-solo-archivo-que-funcione.md](2026-09-10_un-solo-archivo-que-funcione.md).
- **Presentación de la tesis en APA 7 (2026-09-10)**: la tesis pasó a formato APA en su
  presentación (márgenes 2,54 cm, doble espacio, sangría 1,27 cm, texto sin justificar,
  paginación arriba a la derecha, títulos y rótulos APA) y **sigue citando en Vancouver**.
  131 hojas → 143. Está commiteado y en `origin/main`. Quedan dos cosas que decide el autor:
  (a) si el interlineado se queda en **doble** (norma, 143 hojas) o baja a **1,5** (120
  hojas; es una línea en `preambulo.tex`); (b) si los ~90 títulos pasan a **Title Case**,
  que es lo que pide APA pero contradice la ortografía del español. Qué se aplicó, qué no y
  por qué: [2026-09-10_apa-presentacion.md](2026-09-10_apa-presentacion.md).
- **Validación visual del dimensionado de ventanas (2026-09-10)**: se arregló el reporte
  *"la app se descuadra en otros equipos, los botones no se ven o quedan cortados"*. La
  causa no era la que parecía: la app corre **con** conciencia de DPI (`ttk.Window(hdpi=True)`
  llama a `SetProcessDPIAware`), así que con el escalado de Windows al 125-150 % las fuentes
  —y con ellas los widgets— crecen 1,25-1,5× dentro de ventanas cuyo tamaño estaba escrito
  en píxeles fijos, y Tk recorta lo último empaquetado: la barra de botones. `AboutDialog` y
  `MaterialDialog` ya se recortaban **al 100 %**. Ahora todo Toplevel pasa por
  [gui/scaling.py](../../gui/scaling.py) (regla dura 23) y las barras de botones se
  empaquetan primero. Está **sin commit**. Qué mirar: *Modelo → Tipo de Elemento* y *Tipo de
  Análisis* (el video ahora es la pieza elástica) y *Modelo → Materiales* (abre ~740 px de
  ancho, el que su contenido siempre pidió). Para reproducir otro equipo:
  `set EDUFEM_AREA_UTIL=1280x680 && python main.py`. Detalle en
  [2026-09-10_ventanas-contra-la-pantalla-real.md](2026-09-10_ventanas-contra-la-pantalla-real.md).
- **Validación visual del rediseño de la capa visual y de la pasada sobre los módulos
  (2026-09-09)**: cuadrícula anclada al mundo, franja lectora, lente de Proceso (índices de
  GDL, numeración local + ejes ξη + PG del elemento seleccionado), tira del método en el
  banner de Proceso, reacciones en el Post; y en los módulos: esqueleto de K + cabecera del
  sistema en **M7** (donde el autor pidió que viviera la lectura del sistema, que había nacido
  como panel propio de Proceso), ejes ξη con los mismos colores en el cuadrado natural y sobre
  el elemento en M1/M2/M3/M5, unidades y `fmt` en M6, descripciones del panel de módulos sin
  recortes. Está **sin commit**; el guion de qué abrir y qué mirar está en
  [../rutina/BACKLOG.md](../rutina/BACKLOG.md) (*Pendientes visuales*, primer ítem) y el
  razonamiento y las alternativas descartadas en
  [2026-09-09_rediseno-capa-visual.md](2026-09-09_rediseno-capa-visual.md). Dos decisiones
  chicas van adentro: si los visitados de la tira se limpian con *Nuevo Proyecto* (hoy no) y
  si la capa de GDL debe quedar prendida también en Pre por default (hoy solo Proceso).
- **Validación visual de la Memoria de Cálculo rediseñada (2026-09-09)**: sin índice impreso
  ni hojas apaisadas, portada de una hoja (ficha a dos columnas + diagrama del modelo + mapa
  del cálculo), contornos en grilla 2×2, matrices anchas en bloques de columnas y tablas
  topeadas con muestreo. Medido sobre PDFs reales: llenado 95–97 %, 0 hojas flojas, 0 overfull,
  0 apaisadas; Cook Q9 32×32 pasó de **493 hojas a 24**. Aparecieron y se corrigieron ocho
  bugs de producto, seis de ellos **preexistentes**: la Memoria **no compilaba** para mallas
  de 11–12 nodos; la tabla de recuperación imprimía **ε = 0 junto a σ ≠ 0**; la verificación
  de equilibrio ignoraba las cargas superficiales y declaraba **roto con residuo del 100 %**
  el ejemplo Cook del propio menú Ayuda; el `κ₂` se medía sobre la `K` sin restricciones
  —singular por construcción— y marcaba **`Crítico` en todos los modelos**; el formato
  factorizado imprimía **64 celdas de 324 como `0.00`** en la `kₑ` del Q9, que no tiene ni un
  cero; las tablas recortadas mandaban al alumno a una **exportación que no tiene resultados**;
  la flecha de carga se dibujaba fuera de la figura. Está **sin commit**; el guion de
  qué exportar y qué mirar está en [../rutina/BACKLOG.md](../rutina/BACKLOG.md)
  (*Pendientes visuales*) y el razonamiento y lo descartado en
  [2026-09-09_memoria-aprovecha-la-hoja.md](2026-09-09_memoria-aprovecha-la-hoja.md).
- **Marco metodológico de la tesis** frente al canon del tribunal (UATF): objeto/campo,
  formulación del problema como interrogante, 3 vs. 4 capítulos, preliminares. Ver
  `tesis/README.md`.
- **Redundancia transversal** en la tesis y el criterio del 0,3 % en la validación contra
  SAP2000: pendientes de criterio del autor según la revisión del 06-10.
- **Validación visual del Post-Proceso y de la Memoria** tras la vectorización y tras la
  corrección de la extrapolación Q4 (2026-09-07): el autor debe abrir la GUI con el ejemplo
  canónico Q4 y con Cook 32×32 Q9 (gradiente, isolíneas, crudo, probe, 3D) y generar una
  Memoria de Cálculo. **Todas las tensiones nodales Q4 cambian** (el VM máximo del ejemplo
  canónico pasa de 977,46 a 864,70); Q9 no cambia. El diagrama de malla ya no rotula elementos
  demasiado chicos para el texto. **Sumar a esa validación** (rutina, sesión 04, 2026-09-08):
  la **Vista 3D en modo Crudo** —que hasta ahora dibujaba el campo transpuesto dentro de cada
  elemento— y su **nueva escala de color**. **Sumar también** (rutina, sesión 11, 2026-09-09):
  las **figuras de la Memoria en una malla real** (con Cook Q9, el diagrama del modelo y la
  deformada ya no son una mancha de discos: los nodos siguen el LOD del canvas), la colorbar
  del contorno con **símbolo y unidad** (`σVM [MPa]`) y las **tablas con unidades**; el
  ejemplo canónico debe salir igual que antes. El detalle de qué mirar está en
  [../rutina/BACKLOG.md](../rutina/BACKLOG.md), *Pendientes visuales*.
- **Editar un material ya invalida la solución** (rutina, sesión 08, 2026-09-09). Hasta este
  commit, cambiar E, ν o ρ desde *Modelo ▸ Material* no ponía `is_solved = False`, así que
  `F5` cortaba con el fast-path de `post_tab._auto_solve` y devolvía **las tensiones del
  material anterior**, con *Exportar Memoria PDF* habilitado sobre esa corrida vieja. Si en
  algún momento se anotó un resultado después de tocar la librería de materiales **sin
  reabrir el proyecto**, ese número hay que regenerarlo. Las cifras de la tesis **no** están
  afectadas: salen de `tests/vv_*.py` y de `tesis/figuras/gen_anexo_calculo.py`, que arman el
  proyecto desde cero y no pasan por el diálogo.
- **Tesis, párrafo sobre el defecto corregido**: `04_resultados.tex` (§MMS, análisis) declara
  que la matriz E_Q4 estuvo mal hasta la revisión final y que por eso se agregó la prueba de
  reproducción polinómica. Es honestidad de V&V; el autor decide si lo conserva.
- **Validación del autor del TeX Live embebido (2026-09-08)**: (1) abrir la GUI y exportar
  una Memoria (Q4 canónico y Cook Q9, ambos estilos) y la Teoría MEF: debería verse idéntica
  a la de MiKTeX (mismas fuentes Latin Modern, mismo pdfTeX); (2) probar el instalador nuevo
  `installer/Output/EduFEM-Setup.exe` (126 MB) en una PC **sin MiKTeX** y, si se puede, con un
  usuario de Windows con tilde o espacio en el nombre (el instalador debe proponer
  `C:\ProgramData\EduFEM`); (3) decidir si sube `MyAppVersion` (1.0.0) en el `.iss`; (4) la
  tesis afirma en `06_anexos.tex` (Anexo A, párrafos "Es la vía recomendada…" y "El núcleo
  numérico…") que la Memoria requiere MiKTeX instalado: ya no es cierto, hay que reescribirlo.
- **Dictamen 2026-09-07** (artifact "Dictamen EduFEM"): quedan abiertos los hallazgos MAYOR y
  MENOR no mecánicos (objeto de estudio vs. población, hipótesis circular, preliminares,
  estado del arte, etc.). Los bloqueantes están cerrados (ver abajo).

## Convenciones que conviene tener presentes

- El canon está partido: [../../CLAUDE.md](../../CLAUDE.md) tiene las reglas duras y el
  ruteo; el detalle vive en [../convenciones/](../convenciones/) y se lee **según lo que
  vayas a tocar**.
- Antes de agregar algo que "falta", pasá por
  [no-reintroducir.md](../convenciones/no-reintroducir.md): la mayoría de las ausencias son
  decisiones tomadas.
- Rutas que no se pueden mover: [../MAPA.md](../MAPA.md) §3.
- La validación **visual** la hace el autor abriendo la GUI. Un agente puede correr smoke
  tests headless (`MainWindow` + `root.withdraw()`, sin `mainloop`), pero no debe declarar
  que algo "se ve bien".

## Hecho recientemente

- **2026-09-25** — **PyMuPDF retirado; la Teoría MEF se abre con el visor del sistema.** Cierra
  la decisión «Elegir la licencia con que se publica EduFEM»: PyMuPDF (AGPL-3.0 o comercial)
  viajaba en el instalador y dejaba el paquete sujeto a esa licencia. Pillow y pylatex no pueden
  dibujar un PDF; entre `pypdfium2` (BSD/Apache, probado en prototipo) y el visor de Windows, el
  autor eligió el visor: cero bibliotecas nuevas, igual que la Memoria. `theory_viewer.py`
  reescrito (caché `<hash>/<título>.pdf`, hilo que no toca Tk, doble clic, barra de estado, tres
  fallos cubiertos; cierra la mitad de la Teoría del BACKLOG [9]); `build.spec` excluye PyMuPDF
  y cinco extras que se colaban desde el `.venv` —entre ellos `certifi`, MPL-2.0—; avisos de
  terceros generados desde el armado real (`tools/licencias_terceros.py` →
  `LICENCIAS-TERCEROS.txt`, instalado en `{app}`); LEEME, `.iss`, `build_all.ps1` y el canon
  al día. Paquete de 225,0 a 178,7 MB; instalador de 95,6 a 78,7 MB; el arranque ya no carga
  una biblioteca de PDF (170 ms). Tesis **sobre final2**, por decisión del autor (Tabla 2.5 y
  su nota, Anexo A y «Versión evaluada», con la V&V verificada idéntica); final3, que otra
  sesión abrió en paralelo copiando final2 antes de esas ediciones, las lleva con la misma
  redacción (verificado). Versión 1.0.0 sin
  cambios. Pendiente del autor: la prueba del instalador y el material de defensa (arriba).
  Detalle: [2026-09-25_pymupdf-retirado.md](2026-09-25_pymupdf-retirado.md).

- **2026-09-16** — **Presentación de defensa y video, puestos al día y rediseñados**
  ([tesis/presentacion/](../../tesis/presentacion/)). *Contenido*: el guion se sincronizó con
  la tesis después de la auditoría por sesiones —OE2/OE4/OE6 reformulados y objetivo general
  con Python; hipótesis condicional de tres cláusulas más el supuesto declarado; Tabla 1.1
  como matriz de atributos (la columna EduFEM va resaltada); Tabla 2.1 con los atributos del
  artefacto; matriz de consistencia con OE6 → PI-2; criterios a priori completos (σx < 1 %
  también contra SAP2000, equilibrio < 1e-8, cobertura 7/7 y 9/9); Timoshenko con σy, τxy y el
  residuo de equilibrio; «puntos de Barlow» fuera; validador de salud con 22 chequeos (eran 18
  en el guion viejo); conclusiones con OE1 como fundamento y no resultado medido; hipótesis
  confirmada cláusula por cláusula; recomendaciones en tres grupos por capítulo—. Entra una
  **lámina nueva** (la 30) con §3.6, la cobertura del canal, sobre `fig_fases_lienzo_ancho.png`
  —versión apaisada de la Figura 3.5 que ahora genera `tesis/figuras/generar_figuras.py`—:
  quedan **39 diapositivas** y el bloque de resultados pasa a 7 min (45 en total). *Forma*:
  cabecera con rótulo del bloque en versalita y puntos de avance del hilo conductor, carátula y
  cierre con panel oscuro y malla de marca, tarjetas con borde fino y barra de acento, tablas
  con línea naranja bajo la cabecera y destacado de columna, tarjetas de cifra alineadas entre
  sí (y hasta seis por lámina), pasos del flujo compactos y centrados, `comparacion` de hasta
  tres tarjetas y figuras en tarjeta ajustada a su tamaño real. El **video** se regeneró
  entero: `narracion.json` con los mismos cambios de contenido y la lámina nueva, y con él el
  MP4, el guion cronometrado y la copia narrada del `.pptx`. De paso apareció un **bug del
  video que venía del 09-11**: la carátula salía **negra sus 37 segundos**. El demuxer `concat`
  entrega un fotograma por lámina con una duración larguísima, así que `fade=t=in:st=0:d=0.8`
  —que aplica el alfa según el PTS— alcanzaba solo al primer fotograma, con alfa 0, y el
  fundido de salida no llegaba a activarse nunca; se arregla poniendo `fps=25` antes de los
  fundidos en `hacer_video.py`. Falta la revisión del autor (ver *Decisiones abiertas*).

- **2026-09-16** — **Auditoría por sesiones de la tesis, implementada** (45 de 47 hallazgos;
  H-13 parcial, H-1 espera el Reglamento). Introducción: problema en formulación única,
  hipótesis condicional comprobable, OG con Python, OE2/OE4/OE6 reescritos, «canal de
  cálculo» unificado, norma de citación declarada, lista «Referencias bibliográficas».
  Cap. 1: título completo, §1.2 «Fundamentos pedagógicos» (cuatro principios con página y con
  sus límites), justificación de las ediciones clásicas, decisiones de implementación movidas
  a §2.2 (umbral del Jacobiano, `MMD_AT_PLUS_A`, cortes de calidad), Cholesky como teoría,
  «validación» definida una vez, citas de Cook/Hughes recolocadas y 23,96 sin cita, «puntos
  de Barlow» retirado. §2.1: tipo de investigación en §2.1.1 con nivel descriptivo y
  comparativo, Tabla 2.1 con «atributos del artefacto» y «desempeño», matriz con OE6 → PI-2 y
  OE3 → §2.2.6–2.2.8, casos con lo que ejercita cada uno y la excepción (carga variable),
  procedimiento real (Timoshenko = contraste puntual Q9), criterios a priori ampliados (σx
  < 1 % analítico y SAP2000, equilibrio < 1e-8, σ* como cota empírica ≥ 1,4/1,9, cobertura
  7/7 y 9/9, fases, formatos), hipótesis contrastada cláusula por cláusula. §2.2: «El
  software EduFEM», §2.2.1 con lo que cada fuente sostiene. Cap. 3: §3.6 con `tab:fases` y
  `fig:fases-lienzo` (nueva, compuesta por `generar_figuras.py` a partir de tres capturas
  reales), Tabla 3.2 con σy/τxy y Tabla 3.3 con SAP2000, equilibrio de reacciones reportado,
  descripción e interpretación separadas (§3.8.1 reúne juicios y la lección de E_Q4), §3.8.2
  reducido, §3.9 por cláusulas y con OE1 declarado sin resultado medido. Conclusiones
  reescritas (sin citas; veredicto matizado; limitaciones remiten a la Introducción y agregan
  lo descubierto; recomendaciones en tres grupos por capítulo, sin Cuthill-McKee ni cifras
  nuevas). Anexo G con subsecciones numeradas. `.bib`: CSI con `publisher` (biblatex 3.21
  imprimía `organization` antes del pie de imprenta), Reddy sin nota, Oñate «Barcelona:
  CIMNE», García-Córdoba «México (DF)», Bishay con nota de procedencia, Álvarez con nota de
  procedencia; citas múltiples con página separadas por punto y coma (delimitador de `\parencites`); localizadores según la regla única (100
  citas revisadas). `tests/vv_timoshenko.py` (σx vs analítico y SAP2000 < 1 %, equilibrio,
  CSV nuevo `timoshenko_equilibrio.csv`) y `tests/vv_mms.py` (cota empírica de σ*) corridos en
  verde. Guía Vancouver (ficha E, ficha D con `publisher`, corrección 4) y respaldo de citas
  regenerados. Compila limpia: 158 hojas, 0 errores, 0 indefinidas, biber 0 avisos, 0
  desbordes. Decisiones del autor en *Decisiones abiertas*.

- **2026-09-11** — **Auditoría integral de la tesis, implementada el mismo día.** El informe
  ([docs/auditorias/2026-09-11_auditoria_tesis.md](../auditorias/2026-09-11_auditoria_tesis.md))
  cruzó el PDF con el código (V&V corrida, Anexo G regenerado bit a bit), los 22 ejemplares de
  la bibliografía, el `.log` y las normas: 2 bloqueantes de maquetación, 10 mayores, 31
  menores y 18 cosméticos. Se aplicó casi todo: Tabla D.1 en `longtable` (salía cortada),
  Figuras G.3/G.4 con rótulo propio (`\captionof`; con `plaintop` un float de dos `\caption`
  perdía uno), Anexo E foliado (hojas apaisadas giradas 90° con `angle=90`), la frase de la
  Introducción que insinuaba una muestra de estudiantes, «el Q9 evita el bloqueo» acotado al
  cortante (Hughes, fig. 4.4.3), cuatro chequeos que faltaban en la Tabla B.3, tres citas mal
  atribuidas (membrana de Cook y 23,96; von Mises recalculado; Barlow → Zienkiewicz),
  Álvarez de Zayas como `@unpublished`, localizadores de página en 22 citas, fascículos
  verificados por CrossRef, rayas unificadas, y el párrafo de E_Q4 reformulado como lección
  de diseño de la batería (recomendación del auditor, aceptada). **Excluido por el autor**:
  tutor/macro del título en portada, preliminares, abstract en inglés y *Title Case*;
  interlineado doble se mantiene. **Queda para la GUI**: recapturar las figuras de baja
  resolución (3.3, B.1, B.6-B.13).

- **2026-09-11** — **Presentación de defensa y video narrado**, primera versión, en
  [tesis/presentacion/](../../tesis/presentacion/): `Defensa_EduFEM.pptx` (editable, con notas
  del orador; también en PDF) construido con `build_deck.py` a partir de `guion.json`, con el
  orden y los tiempos del Taller 6 de la UATF, y `video/Defensa_EduFEM.mp4` narrado con voz
  neuronal `es-BO-MarceloNeural` (edge-tts + ffmpeg, `video/hacer_video.py`), su guion
  cronometrado y una copia del `.pptx` con la narración embebida. Los binarios (`.mp4`,
  `.pptx` narrado, ~60 MB) quedaron versionados. Estado actual: ver la entrada del 09-16.

- **2026-09-10** — **Instalador profesional: un archivo que deja todo listo.** El `.exe` ya
  lleva datos de versión (Windows lo mostraba sin Descripción ni Empresa, que es además una
  señal que miran los filtros de reputación) y la versión pasó a tener **una sola fuente**,
  `config/settings.py::APP_VERSION`, que leen `build.spec` y el preprocesador del `.iss`. El
  asistente estrena imágenes propias, licencia MIT y un texto de bienvenida que dice lo que
  importa; declara `MinVersion` y arquitectura; deja registro en `%TEMP%` para diagnosticar
  instalaciones fallidas; registra `App Paths` (Win+R ▸ `edufem`); y **asocia los `.edufem`**
  con su propio icono (`resources/icons/edufem_doc.ico`, nuevo en `make_icon.py`), de modo que
  un proyecto se abre con doble clic: `main.py` recibe la ruta como argumento y
  `MainWindow(project_path=...)` la abre. `main.py` además fija el **AppUserModelID** (sin él,
  el icono anclado a la barra de tareas se desprende del acceso directo) y crea el **mutex**
  que le permite al asistente ver que EduFEM está abierto en vez de copiar sobre un `.exe` en
  uso; las tres constantes viven en `config/settings.py` y `tests/test_distribucion.py` (12
  checks, en el gate) verifica que el `.iss` no se desincronice. `tools/build_all.ps1` quedó
  en cuatro pasos, con la carpeta portable como opción (`-Portable`) en vez de armarla en cada
  build: `dist/` queda con solo `EduFEM.exe`, y `docs/MAPA.md` §2 explica cuál de las carpetas
  generadas es el entregable y cuál se puede borrar. **El `.exe` adelgazó 3,9 MB**: apareció
  `lxml` en el bundle, que entra porque `fontTools` lo prefiere si está en el entorno y que
  nadie en EduFEM importa; excluido en `build.spec`. Actualizados el LEEME, `README.md`,
  `CLAUDE.md`, `docs/MAPA.md`, `tools/README.md`, `requirements.txt`,
  `.claude/rules/empaquetado.md` y la **tesis** (Anexo A y §3: el manual ya no pide instalar
  MiKTeX). Gate verde. **Sin commit** (el autor prueba el instalador). Detalle y trampas del
  `.iss`: [2026-09-10_instalador-profesional.md](2026-09-10_instalador-profesional.md).
- **2026-09-09** — **Las tres fuentes que el autor no tiene, resueltas; `.bib` ajustado a sus
  ejemplares.** `roache1998verification` → **`oberkampf2010vv`** (que sí tiene);
  `perezsantiago2023fem` se retiró y **volvió el mismo día**, porque el autor consiguió el PDF:
  las cuatro fuentes que lo habían reemplazado se dieron de baja por inflar la bibliografía; `cook1974membrane` → atribución en prosa, porque **Cook 2002 no
  contiene la membrana de Cook** (verificado). Además se corrigieron las **9 entradas que
  declaraban una edición distinta de la que el autor tiene** y **30 pasajes de prosa** cuya
  fuente no los sostenía: la contradicción de `tab:comparativa` (los simuladores de Lee pasan a
  licencia «Comercial» y a «2D/3D»: están embebidos en VisualFEA), «modos propios de vibración»
  → «de la matriz de rigidez», el umbral de Verdict (**es 0,30, no 0,50**), la paleta jet, el
  ordenamiento de mínimo grado y el «0,05 %» de la nota de Cook, que no salía de ningún GCI
  calculado. 25 entradas, 132 páginas, cero citas indefinidas.
  El `.bib` queda en **22 entradas**, todas con el ejemplar en mano salvo Roache y Cook 1974,
  que se sustituyeron. Detalle en
  [2026-09-08_bibliografia-tesis.md](2026-09-08_bibliografia-tesis.md).

- **2026-09-09** — **Bibliografía: Vancouver puro en el cuerpo + respaldo documental
  verificado.** Se retiraron los localizadores de página de las citas (decisión del autor: el
  cuerpo queda `[7]` a secas) y se trasladaron a **`tesis/respaldo_citas/respaldo_citas.pdf`**
  (44 pág.), que registra por cada cita el ejemplar consultado, la página impresa y el pasaje
  textual que la sostiene. Auditoría multiagente de los 22 PDF de `tesis/bibliografia/`
  (42 agentes, 147 respaldos localizados); copias con los pasajes resaltados en
  `tesis/bibliografia/resaltados/` (gitignorado, copyright). **Dos resultados que esperan al
  autor**: (1) el `.bib` declara **ediciones que no son las que él tiene** — Zienkiewicz
  7.ª/2013 vs. **6.ª/2005**, Bathe 2.ª/2014 vs. **Prentice Hall 1996**, Strang 2.ª/2008 vs.
  **1.ª/1973**, Timoshenko 3.ª/1970 vs. **2.ª/1951**, Hughes Dover 2000 vs. **Prentice-Hall
  1987**; (2) **contradicciones internas** en `tab:comparativa` (los simuladores de Lee
  figuran con licencia «Libre» pero están embebidos en VisualFEA, que el propio párrafo
  llama «cerrados y de pago»; y como «2D» cuando el artículo documenta sólidos 3D de 20
  nodos). Detalle en [2026-09-08_bibliografia-tesis.md](2026-09-08_bibliografia-tesis.md).
  Faltan en la carpeta **Roache 1998 y Cook 1974**: no se pudieron verificar.

- **2026-09-09** — **Rediseño de la capa visual, el lienzo y la interacción: "la interfaz
  enseña el método"** (pedido del autor con libertad total; sin commit, espera validación
  visual). El mismo modelo se mira con **tres lentes** según la fase: (a) *geometría* en Pre,
  con la **cuadrícula anclada al mundo** (serie 1-2-5, ejes X=0/Y=0 rotulados, paso en el
  readout) y una **franja lectora** al pie del lienzo que describe en términos del MEF lo que
  hay bajo el cursor (nodo: coordenadas, índices de GDL, restricción, carga, elementos que lo
  comparten; elemento: conectividad antihoraria, material, espesor, área, GDL → tamaño de kₑ)
  o la pista de gesto de la fase; (b) *sistema discreto* en Proceso: los dos **índices de GDL
  en K** junto a cada nodo (los restringidos tachados), la **lente del elemento seleccionado**
  (numeración local 1..4, ejes ξη según la convención del motor, puntos de Gauss físicos), el
  banner con la **tira del método** `N › J › B › D › kₑ › F › K` (chips clickeables 1:1 con
  M1..M7, con estado inactivo/visitado/activo; reemplaza al breadcrumb de la barra de estado);
  (c) *campo* en Post: contorno + **reacciones en los apoyos** (`R = K·u − F`, flechas que
  llegan al nodo desde afuera con rótulo en la cola, toggle en el panel del Post). Además:
  subtítulos de banner con el orden del método, barra de estado con `GDL: 18 (12 incógnitas)`
  y mensajes por fase con los números del modelo. **Segunda tanda, módulos educativos** (pedido
  del autor): la vista viva del sistema K·u = F que había nacido como panel propio de Proceso
  **se fundió en M7** (esqueleto gris de K bajo el heatmap —la forma que la malla decide, que
  cada kₑ rellena— + cabecera `2N GDL · restringidos → incógnitas · bloques ≠ 0 · semiancho`;
  lógica pura en `education/components/system_structure.py`); los ejes ξη del cuadrado natural
  de M1/M2/M3/M5 pasaron a flechas naranja/violeta y esos módulos dibujan los mismos ejes sobre
  el elemento real con el glifo compartido `gui/preprocessing/canvas_glyphs.py`; M6 rotula con
  `fmt` y unidades (cierra el ítem [8] del BACKLOG); el panel de módulos envuelve las
  descripciones al ancho real. Lógica pura en `canvas_logic.py`; widget nuevo
  `method_strip.py`; tests `test_canvas_lens` (sin display) y `test_canvas_lens_gui` (Tk, abre
  M7 de verdad) en el gate. Gate verde. Nota:
  [2026-09-09_rediseno-capa-visual.md](2026-09-09_rediseno-capa-visual.md).
- **2026-09-08** — **Bibliografía de la tesis auditada, saneada y con los vacíos cerrados**
  (23 entradas, todas con ≥2 citas; se retiró `oberkampf2010verification` y se sumaron las tres
  del **material docente de la carrera**, que estaba en `tesis/Material docente/` y es la fuente
  normativa que le faltaba al capítulo metodológico). La bibliografía **no** sobraba: el
  problema era de cobertura. Los demás huecos se cerraron **sin entradas nuevas** —
  redirigiendo a fuentes ya presentes, volviendo autosuficientes las afirmaciones (Cook 23,96
  por extrapolación propia; invariancia frente a $E$ en Timoshenko) y cambiando apelaciones a
  autoridad ausente por el argumento técnico. Ver
  [2026-09-08_bibliografia-tesis.md](2026-09-08_bibliografia-tesis.md).
- **2026-09-09** — **Las citas al material docente se reemplazaron por sus fuentes de origen**:
  Álvarez de Zayas (objeto/campo/problema), Hernández-Sampieri y Mendoza 2018 (enfoque
  cuantitativo, variables, muestra dirigida) y García-Córdoba 2005 (investigación tecnológica).
  Motivo: los tres decks de cátedra **no tienen bibliografía** y uno de los docentes integra el
  tribunal. Siguen 23 entradas. **Hechos también los localizadores de página** (8 citas con
  `p.~NN`, verificados abriendo cada libro: el desfase PDF↔impresa no es constante).
  **Pendientes del autor**: la monografía de Álvarez no trae pie de imprenta (se cita sin año);
  y `tesis/bibliografia/Elast2DOñante.pdf` más los ocho PDF de `tesis/Material docente/` siguen
  **trackeados en un repo público** siendo material ajeno — decidir si se sacan de HEAD (ya están
  en el historial). Los libros nuevos sí quedaron gitignorados.
- **2026-09-08** — **TeX Live recortado embebido: la Memoria y la Teoría ya no dependen de
  MiKTeX.** Motivo: en PCs de usuarios, MiKTeX básico abría un diálogo de instalación por cada
  paquete faltante (booktabs, tcolorbox, pgf, babel-spanish, listings…) y sin internet fallaba;
  medido con `pdflatex -recorder`, los cuatro documentos reales consumen 263 archivos (19,2 MB,
  de los que 13,3 MB son el `.fmt` de MiKTeX). Implementado: (a) `tools/build_texlive.py`
  genera `vendor/texlive` (gitignored) desde TinyTeX-0 v2026.09 (TeX Live 2026) + `tlmgr
  install` de la lista fija `PACKAGES` contra el snapshot `texlive.info/tlnet-archive/2026/09/07`
  + formato pdflatex con silabeo español + poda (Perl, Ghostscript, docs, OpenType, motores Lua)
  + `ls-R` regenerados; valida compilando Memoria Q4 educativo/directo, Memoria Q9 y Theory Hub
  antes y después de podar. Resultado: **50,9 MB / 4180 archivos**; el instalador pasa de 102 a
  **126 MB**. Hallazgos del build: `ec` es obligatorio (pylatex carga `fontenc[T1]` antes de
  `lmodern` y LaTeX pide `ecrm1095.tfm`), `l3backend` ya vive en `l3kernel`, y en TL 2026
  `pdflatex.exe` es un lanzador de 6 KB que carga `pdftex.dll`. (b) Nuevo
  `education/components/latex_runtime.py`: resuelve el compilador (`EDUFEM_TEXLIVE_DIR` →
  `texlive/` hermana del `.exe` o `vendor/texlive` → PATH, donde MiKTeX recibe
  `-enable-installer`), compila en un temporal con ruta ASCII sin ventana de consola, dos
  pasadas, y mueve el PDF al destino; `TheoryDoc.compile_to` y `TheoryViewer` pasan por ahí
  (adiós `Document.generate_pdf` y `latexmk`). La Memoria guarda sus figuras en ese `workdir` y
  las referencia por nombre relativo. (c) `installer/EduFEM.iss` copia `vendor/texlive` a
  `{app}\texlive`, y `[Code]` elige `C:\ProgramData\EduFEM` como carpeta por defecto si el
  perfil del usuario tiene tildes o espacios (TeX Live no resuelve rutas no ASCII).
  (d) `tools/build_all.ps1` arma el bundle si falta; LEEME, README, CLAUDE.md, MAPA, reglas y
  convenciones actualizados. Verificado: `test_memoria_calculo` 23/23 y nuevo
  `test_latex_runtime` 7/7 con el bundle (incluye PDF en destino con tilde y espacio), bundle
  copiado a otra ruta con espacio compila, `.exe` recompilado (`dist/EduFEM.exe`, 106 MB) e
  instalador compilado (`installer/Output/EduFEM-Setup.exe`). **Sin commit** (el autor revisa);
  pendientes del autor en *Decisiones abiertas*.
- **2026-09-07** — **Bug real corregido: extrapolación Q4 Gauss→nodos.** `fem/stress.py`
  tenía `_Q4_EXTRAP` escrita a mano para OTRO orden de puntos de Gauss que el que produce
  `get_gauss_points_2d(2)` ((-,-),(-,+),(+,-),(+,+)): columnas de los PG 3 y 4 intercambiadas,
  desde el primer commit (2026-02-27). No reproducía ni un campo lineal. Ahora Q4 y Q9 se
  construyen igual (`_build_extrapolation_matrix`: E = inv(M), M_ji = N_i(ξ_j, η_j) con los
  puntos reales). Copias a mano eliminadas en `file_io/memoria_calculo.py` y
  `tesis/figuras/gen_anexo_calculo.py` (fuente única `fem.stress.extrapolation_matrix`).
  Guard: `tests/test_vv_extensions` [7/7] exige reproducción exacta de campos polinómicos en Q4 y
  Q9. Por qué nadie lo vio: el MMS mide desplazamientos, Timoshenko usa Q9, Cook mide flecha; y en
  mallas finas uniformes los errores nodales se cancelan por simetría (en el ejemplo canónico de 4
  elementos el VM de algunos nodos estaba 2–4× mal). Regresión 81/81 OK, batería completa en verde.
  **MMS ampliado** (`tests/vv_mms.py`): 4 configuraciones {unitario, distorsionado} ×
  {tensión plana, deformación plana} + norma L² del campo de tensiones recuperado
  (`fem.error_norms.compute_stress_recovery_error`); tasas: desplazamiento teóricas en las 4;
  σ* O(h^1,5) Q4 / O(h²) Q9. CSV nuevos `mms_*_{dist_tp,unif_dp,dist_dp}.csv` + `mms_resumen.csv`;
  figura `mms_convergence_stress.png`. **Tesis**: Anexo G regenerado (`anexo_calculo_data.tex`,
  `mem_contorno_vm.png`); eq:extrap-q4 con el orden real de PG; cotas de error honestas ("0,05 %
  en tensiones" → 0,04 % en σx, 2,9 % en τxy, 0,26 % flecha; vs SAP2000 0,21 %/0,56 %); Barlow
  corregido para Q9; regla "p+1" → "un punto más por dirección"; criterios de aceptación explícitos
  en §2.1; tab:mms con columna σ*, nueva tab:mms-configs y fig:convergencia-tension; tabla de
  componentes de Timoshenko con columna de error.
  **Segunda tanda del mismo día**: (1) **von Mises correcto en deformación plana** en todas las
  rutas (`fem/batch.py::principal_and_vm_batch(stress, sigma_z)`, `out_of_plane_factor`,
  `sigma_z_from`; `fem/stress.py`; `fem/probe_query.py` raw/smooth/grids; memoria; oráculo
  de regresión) con `sigma_z = nu (sx+sy)`; guard `test_vv_extensions` [8/8]; eq:principales-vm
  de la tesis con `\sigma_z`. (2) **Jacobiano escalado por FILAS** (tangentes) en
  `fem/mesh_quality._jacobian_samples` (antes columnas: cantidad distinta); tesis: eq:jacobiano
  con la convención del motor (filas ξ,η), eq:scaled-jacobian por filas, umbrales Verdict vs.
  UI y estado de 4 métricas documentados. (3) **Cook**: `U_Y_REF = 23.96` en `vv_cook.py`
  (antes 23.95), CSV/figura regenerados, tabla y textos con los errores nuevos e incertidumbre
  de la referencia (Richardson ≈ 23,97). (4) **`tests/bench_timing.py`** mide COLAMD vs
  MMD_AT_PLUS_A (1,7×/2,0×/2,9× a 2178/8450/33 282 GDL); tab:tiempos remedida hoy. (5) Nuevo
  **`tests/test_interop.py`** (CSV/ZIP ida y vuelta + DXF idempotente) citado en §3.3 y en
  tab:vyv-repro (objetivo 5 con evidencia). (6) Mecánicos: portada con tildes, `\markboth` en
  Introducción/Resumen/Conclusiones, `\appendixautorefname` vía `\extrasspanish` (ya no
  "Apéndice"), `sec:metodologia`, artículos ante `\autoref{eq:}`, "Cap. 3", palabras clave 6,
  bib (organization {{}}, Lee = "Jae Young Lee" + Ryu, issue 2 y 5, {van der Walt}), 21,32 GPa y
  origen de E, pdflatex en Anexo A, fila `orphan_free_node`, DXF→Q9 automático y unidades,
  Anexo G "condensada", rango 0..2N−1, Anexo E en la lista de anexos, doble "variable
  independiente", PyMuPDF, CALFEM, cobertura del canal. Compila limpio, 128 páginas. Batería
  completa en verde (regresión 81/81, vv_extensions 8/8, interop, fem, memoria 23/23, probe,
  canvas). **Sin commit** (el autor revisa).
  **Tercera tanda (pedido del autor)**: §2.1 reestructurado de 10 subtítulos de diseño
  experimental (control, repetición, protocolo…) a 6 que siguen el diagrama del Taller 4 del
  tribunal (modelo de simulación numérica · variables · matriz de consistencia · casos de
  estudio y criterio de selección · procedimiento, instrumentos y reproducibilidad · criterios
  de aceptación y contraste de la hipótesis); la parte de software pasó a ser §2.2 «Diseño e
  implementación de EduFEM» con sus antiguas secciones como subsecciones (2.2.1–2.2.9).
  Etiquetas conservadas: `sec:metodologia`, `sec:proceso-met`, `sec:variables-met`,
  `sec:matriz-consistencia`, `sec:poblacion`, `sec:validacion-datos`,
  `sec:validacion-resultados`; nueva `sec:diseno-edufem`; borradas (sin referencias)
  `sec:hipotesis-met`, `sec:sistema-control`, `sec:sistema-repeticion`,
  `sec:protocolo-calculo`. Frases de la Introducción que enumeraban los subtítulos viejos
  actualizadas. Compila limpio, 127 páginas.
  **Cuarta tanda (2026-09-08, pedido del autor tras analizar el material del tribunal):**
  coherencia Introducción ↔ Cap. 2 ↔ Cap. 3 ↔ Conclusiones según el esquema
  problema–objeto–campo–objetivo–hipótesis–tríada. (a) **Objeto de estudio técnico** («el
  análisis de medios continuos en elasticidad lineal plana por el MEF») y **campo de acción
  pedagógico** («su enseñanza: el software que expone el canal y la memoria»), como en el
  ejemplo del propio catedrático (objeto = losas, campo = costos); así población, variables y
  resultados quedan dentro del objeto. (b) **Problema científico** reformulado como
  respondible: VI = forma de exponer el canal (transparencia, interactividad,
  verificabilidad); VD = observabilidad y contrastabilidad del procedimiento; «apoyo a la
  comprensión» pasa a ser el para qué. (c) **Delimitación** institucional (Carrera de Ing.
  Civil UATF como destinataria), espacial (aula y equipo del estudiante), temporal (gestión
  2026) y disciplinar. (d) **Sexto objetivo específico**: nuevo OE1 «Fundamentar
  teóricamente…» (cubre el Cap. 1) + fila en `tab:consistencia`; el instrumental pasa a ser
  el sexto (01, 02b, 04:95, 05). (e) **Hipótesis**: puente de tres variables en la intro,
  coherente con las variables del problema. (f) **Tríada**: cada conclusión nombra su
  capítulo; conclusión nueva para el Cap. 1; recomendaciones ancladas por capítulo + nueva
  «Ampliación de la batería de validación» (caso civil en deformación plana). (g) §3.8
  responde explícitamente al problema y al objeto. Compila limpio, 130 páginas. Sin commit.
- **2026-09-06** — **Cerradas las tres decisiones abiertas del post-proceso.**
  (a) **Invariantes nodales**: σ1, σ2 y von Mises ya no se extrapolan ni se promedian; se
  extrapolan y promedian las tres componentes cartesianas y las invariantes se recomputan desde
  ellas (`fem/stress.py` + `fem.batch.principal_and_vm_batch`). Las componentes no cambian ni un
  bit y **ningún CSV de V&V se movió**; sí cambia el VM nodal mostrado: +3,0 % en el máximo de
  Cook Q9 32×32 y +8,3 % en el ejemplo canónico. Corrige una incoherencia real — el nodo 8 del
  Anexo F mostraba VM = 8,96 con σx = −54,23, σy = −11,55 y τxy = −84,65, cuyo VM coherente con
  esas componentes es 154,74 (componentes que, a su vez, eran incorrectas por el bug de
  extrapolación Q4 corregido el 2026-09-07; hoy el nodo 8 da σx = 39,34, σy = −74,16,
  τxy = 107,67, VM = 211,52). El marco teórico de la tesis (§2, extrapolación) **ya describía este comportamiento**;
  ahora el código lo cumple. `tesis/figuras/anexo_calculo_data.tex` regenerado con
  `gen_anexo_calculo.py`.
  (b) **RCM eliminado**: medido, solo gana por encima de ~8500 GDL (7–19 %) y por debajo pierde;
  a ese tamaño el resto de la app tarda segundos. Se borraron `SOLVER_USE_RCM`,
  `SOLVER_RCM_MIN_DOF` y la rama de permutación. Queda `SOLVER_PERMC_SPEC = "MMD_AT_PLUS_A"`,
  remedido: 1,6× a 2178 GDL y 2,1× a 8450 y 33 282 GDL (la constante citaba mal la malla).
  Menciones a RCM quitadas de la tesis (nomenclatura, marco teórico, conclusiones).
  (c) **`figure_export._fill_field` vectorizado** sobre `canvas_raster.rasterize_triangles`:
  el contorno de la memoria pasó de 16,7 s a 0,51 s en 1024 elementos y de 47,6 s a 1,26 s en
  4096, con **0 píxeles distintos** (`test_canvas_raster.test_figure_export_field`). En el
  ejemplo canónico de 4 elementos hay una regresión de ~100 ms (155 → 245 ms) por el overhead
  del camino por lotes: irrelevante frente a los segundos de `pdflatex`. `render_mesh_diagram`
  ya no rotula elementos más chicos que el texto (ilegibles y caros): 1,65 s → 0,83 s en 1024
  elementos. Lo que queda caro ahí es Pillow, una llamada de dibujo por elemento.

- **2026-09-06** — **Motor vectorizado por lotes y retiro de numba.** Nuevo `fem/batch.py`
  (geometría J/det J/B, rigidez, scatter COO y tensiones de todos los elementos a la vez con
  `einsum`/`matmul`); `fem/assembly.py`, `fem/stress.py`, `fem/probe_query.compute_raw_grids`,
  `fem/mesh_quality` y `fem/error_norms` lo usan. Solucionador con `SOLVER_PERMC_SPEC =
  "MMD_AT_PLUS_A"` (SuperLU sobre CSC). Canvas: `gui/preprocessing/canvas_raster.py`
  (rasterizado Gouraud e isolíneas vectorizados, paridad píxel a píxel). Borrados
  `fem/_numba_compat.py`, los 17 kernels `@njit` y el warm-up de numba; `build.spec` excluye
  `numba`/`llvmlite`. Motivo: el `.exe` nunca tuvo numba (onefile extrae a una carpeta
  aleatoria y el cache del JIT jamás acertaba) y los kernels escalares corrían en Python puro.
  Cook Q9 32×32 (8450 GDL) sin numba: ensamblaje 3,35 s → 0,054 s, tensiones 0,50 s → 0,06 s,
  contorno crudo 2,95 s → 0,04 s, isolíneas 51 s → ~0,1 s; 33 k GDL: solve 0,73 s (antes 2,2 s
  con numba). Versión legible de `fem/` intacta como oráculo de `tests/test_solver_regression.py`
  (81 checks ≤ 1e-9); `tests/test_canvas_raster.py` (paridad); batería completa y V&V en verde
  con CSV idénticos; tabla `tab:tiempos` de la tesis regenerada. **Pendiente del autor:
  validación visual** del Post-Proceso (gradiente, isolíneas, crudo, probe, 3D) — debería verse
  idéntico y responder en < 1 s en Cook 32×32 Q9 — y rebuild del `.exe` + instalador.
- **2026-09-06** — Reorganización del repositorio y espacio de trabajo para agentes:
  `docs/` estructurado (`convenciones/`, `notas/`, `auditorias/`, `teoria/`), auditorías
  consolidadas, `CLAUDE.md` reducido de 909 a ~230 líneas, `README.md` y `AGENTS.md`
  creados, insumos de distribución movidos a `installer/dist_extra/`. Detalle:
  [2026-09-06_reorganizacion-repo.md](2026-09-06_reorganizacion-repo.md).
- **2026-09-06** — Segunda tanda de la auditoría 2026-06-10 (medios y bajos): traza en los
  listeners de undo y en el error de `auto_solve`; guard de `det J` en `error_norms`; el
  snapshot de undo del cambio Q4↔Q9 pasó a después del `askyesno`; guards de `winfo_exists`
  en los `after()` de tres diálogos; `memoria_style_dialog` y `about_dialog` usan
  `center_dialog`; tolerancias `1e-10` reemplazadas por `NUMERICAL_TOLERANCE`; eliminados
  5 constantes sin consumidor, `highlight_node`/`highlight_element` y 6 llamadas redundantes
  a `_refresh_menu_state`; comentarios de paleta y de módulos M8/M9 corregidos;
  `recompute_q9_midnodes` por índice inverso; `test_draw_mode` con guard de Tk.
- **2026-09-06** — Cerrado el Top-10 de la auditoría 2026-06-10. P0: `change_element_id`
  ahora sincroniza `_node_to_elements` (reg. en `test_node_cascade`) y `assembly` ignora la
  carga nodal huérfana en vez de romper el solve. P1: autofix de cargas superficiales por
  identidad de objeto; `_check_orphan_free_nodes` nuevo (con autofix e hint) y
  `nodes_in_elements` deja de contar los sets vacíos que `remove_element` deja al preservar
  huérfanos. P2: `capture()` antes de los autofixes, snapshot inmutable del project para el
  worker del PDF, y `to_float_flex` para la coma decimal de Excel. P3: `mod06` usa
  `redraw_overlays_only()`; `.gitattributes` creado. Batería completa + V&V en verde.
- **2026-09-06** — Auditoría del canon de instrucciones: corregidas 21 afirmaciones obsoletas
  en `docs/convenciones/` (orden `Ctrl+1..7` que daba `D, B` en vez de `B, D`; chips
  `Q4 · 8 DOF` → `GDL`; `AnalysisTypeDialog` con dos videos inexistentes y la matriz D
  atribuida a M3; fallback a `simpledialog`, botón Reset y sub-pestaña de Educación en el Post,
  los tres inexistentes; contrato `BaseEducationalModule` / `GaussCoordReadout` descrito en
  presente; bullet duplicado en M4; `pdf_report`). `CLAUDE.md` 229 → 187 líneas quitando
  duplicación interna, y `.claude/rules/` (5 archivos con `paths:`) hace que cada capítulo se
  cargue solo al tocar su área.
- **2026-06-10** — Auditoría general del repo + revisión profesional de la tesis
  (diagnóstico, sin fixes) y comando `/schedule`.
- **2026-06-01** — Implementadas las recomendaciones P0–P2 de la auditoría integral del
  2026-05-31 (incluido el bug de `node_index_map` stale).
