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

## Notas

- El capítulo cita los datos crudos de `datos/` literalmente en sus tablas.
  Si se re-corren los scripts y los números cambian, hay que actualizar las
  tablas de `capitulo_vyv.tex` manualmente (no hay carga dinámica con
  `csvsimple`).
- Convención de eje y: el solver usa la convención FEM estándar (y arriba).
  El script `vv_timoshenko.py` invierte el signo de y al probar los puntos
  del PDF de referencia (que usa convención Timoshenko-Goodier, y abajo).
  Documentado dentro del script.
