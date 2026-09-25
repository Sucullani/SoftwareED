# docs/vyv — Capítulo de Verificación y Validación

Documento standalone que reporta la campaña V&V del solver EduFEM. Salida:
`main.pdf`.

## Cómo regenerar datos y figuras

Los `.csv` en `datos/` y los `.png` en `figuras/` se generan desde los scripts
del proyecto (raíz del repo):

```
python -m tests.vv_mms          # ~30 s — MMS: docs/vyv/datos/mms_*.csv y figuras/mms_*.png
python -m tests.vv_timoshenko   # ~10 s — viga: docs/vyv/datos/timoshenko_*.csv y figuras/timoshenko_*.png
python -m tests.vv_cook         # ~30 s — Cook: docs/vyv/datos/cook.csv y figuras/cook_*.png
```

## Cómo compilar el PDF

Desde este directorio (`docs/vyv/`):

```
pdflatex -interaction=nonstopmode main.tex
biber main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Requisitos: MiKTeX o TeX Live con `biber` instalado.

## Estructura

- `main.tex` — scaffold standalone (article, biblatex Vancouver, paquetes habituales).
- `capitulo_vyv.tex` — cuerpo del capítulo (~6 secciones).
- `referencias.bib` — base bibliográfica (Vancouver, 18 entradas).
- `datos/` — CSVs crudos generados por los scripts.
- `figuras/` — PNGs generados por los scripts.

## MMS paso a paso (`mms_paso_a_paso/`)

Documento de estudio que desarrolla el MMS desde cero con el caso base (Q4, `N = 2` a mano, luego
el refinamiento), con todas las fórmulas y cifras intermedias. Salida: `mms_paso_a_paso.pdf`.
Todas las cifras salen de guiones; ninguna se transcribe a mano:

```
python docs/vyv/mms_paso_a_paso/generar_datos.py         # ~30 s -> datos.tex, convergencia.dat, pendientes.dat
python docs/vyv/mms_paso_a_paso/experimento_sabotaje.py  # ~3 min -> datos_sabotaje.tex (sección 8)
cd docs/vyv/mms_paso_a_paso && pdflatex mms_paso_a_paso.tex && pdflatex mms_paso_a_paso.tex
```

- `mms_independiente.py` es una réplica del MMS que **no importa nada de EduFEM**; el generador
  la usa y además contrasta sus cifras con EduFEM (`K_red`, `F_red`, `u_5`, normas de `N = 2` y
  los 20 valores de `datos/mms_q4.csv` y `mms_q9.csv`): si algo no coincide, aborta.
- La sección 8 documenta un límite del MMS actual: con la `u_M` de `tests/vv_mms.py`,
  `tr(ε) = 0` y `γxy = 0`, así que la prueba no ve `λ` ni `D33` (no distingue tensión plana de
  deformación plana). `experimento_sabotaje.py` lo comprueba y prueba una `u_M` alternativa que
  sí los detecta.

## Notas

- El capítulo cita los datos crudos de `datos/` literalmente en sus tablas.
  Si se re-corren los scripts y los números cambian, hay que actualizar las
  tablas de `capitulo_vyv.tex` manualmente (no hay carga dinámica con
  `csvsimple`).
- Convención de eje y: el solver usa la convención FEM estándar (y arriba).
  El script `vv_timoshenko.py` invierte el signo de y al probar los puntos
  del PDF de referencia (que usa convención Timoshenko-Goodier, y abajo).
  Documentado dentro del script.
