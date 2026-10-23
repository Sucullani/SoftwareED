# Tesis final4: observaciones del tribunal tras la defensa de borrador (2026-10-20)

## Qué pidió el tribunal

1. Cambiar la hipótesis por un texto que dictó, con su contraste claro en la tesis.
2. Eliminar «Aportes del trabajo» y «Limitaciones» de las Conclusiones (redundantes con la
   Introducción).
3. Conclusiones más claras, concisas y visuales, sin los títulos «Conclusión 1, 2, 3».
4. Títulos de figuras y tablas sin cursiva.
5. Pie de página abajo y con mejor estilo.

El autor sumó en la misma sesión:
- cambiar «ejemplo canónico» por un nombre más claro, porque el tribunal recomendó evitar
  términos muy técnicos;
- abrir cada conclusión con «se concluye que»;
- acortar las Conclusiones y no repetir en ellas la hipótesis.

## Qué se hizo

Versión nueva **final4** (`tesis/main_final4.tex` + `tesis/capitulos_final4/`). final3 pasó a
`tesis/archivo/final3/`. Registro de cada cambio, con su motivo:
[`tesis/auditoria_final/IMPLEMENTACION-FINAL4.md`](../../tesis/auditoria_final/IMPLEMENTACION-FINAL4.md).

## Decisiones del autor (no revertir)

- **Hipótesis literal del tribunal, con «dada»**. Las variables, el problema y el objetivo
  general **no** cambian: «análisis» y «procedimiento de cálculo» nombran la misma unidad (el
  objeto de estudio se define como el análisis realizado mediante su procedimiento de cálculo), y
  la Introducción lo dice en una oración.
- La interviniente sigue siendo EduFEM, ahora «desarrollado bajo un método de diseño de software
  educativo», que es la ciencia del diseño. No se agregó bibliografía de metodologías de software
  educativo.
- Contraste en cuatro partes, en el orden del enunciado (condición, intervención, efecto y
  antecedente), con regla de decisión conjuntiva.
  - La tabla de partida y logro vive en §3.8 (Tabla 3.11) y la Figura CR.1 la resume.
  - No se repite como tabla en las Conclusiones, ni se copia allí el enunciado.
- Aportes y Limitaciones: fuera como secciones; lo único, en §3.7.5 y en una oración de las
  Conclusiones. Taller 5 exige «señalar falencias o debilidades», por eso queda un párrafo breve
  de debilidades.
- Conclusiones en unas 650 palabras. Cada una abre con «De … (Capítulo N) se concluye que…», una
  sola vez por párrafo.
- Cursiva fuera solo en los rótulos (y en los títulos internos de las tablas). Los títulos de
  nivel 3 y 5 siguen en negrita cursiva.
- Pie: número abajo a la derecha, capítulo a la izquierda, filete; la apertura de capítulo lleva
  solo el número.
- «ejemplo guía» y no «ejemplo de demostración»: «demostración» se lee como prueba matemática y
  choca con la actividad «Demostrar» del método.
- H1 y H4 corregidos en la redacción (vía b de H1), sin tocar el código.

## Trampas encontradas

- **Hojas de flotantes con mucho blanco.** Una figura o tabla que pasa de la mitad de la hoja y
  se difiere termina sola en una hoja de flotantes, centrada, porque `\floatpagefraction` vale
  0,5. En las Conclusiones y en §3.8 se subió a 0,85 dentro de un grupo. La Figura 2.1 se
  compactó (8,5 cm de alto) y su rótulo se acortó.
- **El guion de figuras validaba contra final3.** `TESIS` estaba fijo en `capitulos_final3`.
  Ahora la versión es un parámetro (`--version`) y la guarda aísla la tabla de veredicto: las
  cadenas «7 de 7»… también aparecen fuera de ella.
- **`\chaptermark` de fancyhdr** se define una sola vez, al cargar el paquete: se puede
  redefinir después de `\pagestyle{fancy}` sin que se pise. Los capítulos cuyo título es el
  objetivo completo necesitan un `\chaptermark{corto}` tras su `\label`.
- **H4, más fino de lo que decía la auditoría.** Los guiones de V&V existen desde el 25-05
  (`ed852bf`) sin umbrales, pero ya imprimían y guardaban los errores. Los umbrales de la
  flecha, Cook y las tasas entraron el 01-06 (`c8885e0`) y los de σx y el equilibrio el 16-09
  (`4a60eb2`): **ninguno precede a sus resultados**. La tesis lo dice así («Ningún umbral
  numérico se escribió antes de las primeras corridas, ni se calculó a partir de sus
  resultados») y el veredicto descansa en el margen. La auditoría general de final3 afirmaba
  que `c8885e0` era el primer commit (es `02ab0d4`, 27-02) y su respuesta A11 preparaba al autor
  para decirlo: lleva ahora una fe de erratas.
- **`\pagestyle` de fancyhdr 5 no se deshace solo.** Un estilo definido con `\fancypagestyle`
  (sin asterisco) y activado con `\pagestyle` reescribe los campos del estilo `fancy`, y
  `\pagestyle{fancy}` no los restituye. El estilo de la Nomenclatura va dentro de un grupo.
- Con Blender usando toda la CPU, una compilación completa tarda 5 a 6 minutos.
- **Viudas y huérfanas.** Con `\raggedbottom`, el `\parskip` rígido de APA y el doble espacio,
  las penalizaciones por defecto no deciden nada: el objetivo general salía partido entre dos
  hojas. Van a 10000 en el preámbulo (T-19).
- **Segunda revisión adversarial (21-10)**: cinco lentes con un verificador por lente. Los
  verificadores de 32 y 16 hallazgos se cortaron por falta de respuesta de la API; en lotes de
  ocho, leyendo los hallazgos de un archivo, terminaron sin problemas.

## Pendiente (para el autor)

Lista en «Lo que queda para el autor» de `IMPLEMENTACION-FINAL4.md`:
- revisión visual del PDF;
- material de defensa, que sigue a final3;
- el menú del software, que dice «Cuadrado de validación»;
- `\anioTesis` («octubre de 2026»: ajustarlo al mes de la entrega);
- el comentario «fijados a priori» de `tests/vv_timoshenko.py:478` (software, no se tocó);
- `verificado.json`;
- los pendientes de auditorías anteriores (H5, H6, H7, H8, H9, H10, H-1).
