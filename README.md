# EduFEM

**Software educativo de elementos finitos para análisis estructural 2D.**

EduFEM resuelve problemas de elasticidad plana (tensión plana y deformación plana) con
elementos cuadriláteros **Q4** y **Q9**, y —lo que lo distingue de un solucionador
convencional— **muestra el procedimiento**: ocho módulos interactivos superpuestos a la
malla real explican paso a paso el mapeo isoparamétrico, el Jacobiano, las matrices **B** y
**D**, la rigidez por cuadratura de Gauss, las fuerzas equivalentes y el ensamblaje global.

Interfaz íntegramente en español. Desarrollado como trabajo de tesis de grado en Ingeniería
Civil (Universidad Autónoma "Tomás Frías", Potosí, Bolivia).

## Qué hace

- **Pre-proceso** — dibujo de la malla sobre lienzo, hoja de cálculo de 5 tablas (nodos,
  elementos, cargas, restricciones, cargas superficiales), materiales, gravedad, importación
  de geometría desde **DXF** y de modelos desde **CSV/Excel**.
- **Proceso** — resolución por el MEF (ensamblaje disperso + factorización LU) con un
  validador de salud del modelo que detecta errores antes de resolver, y los ocho módulos
  educativos.
- **Post-proceso** — contornos de tensión y desplazamiento, malla deformada, isolíneas,
  vista 3D del campo y sonda puntual con círculo de Mohr.
- **Memoria de Cálculo en PDF** — el procedimiento completo con fórmulas, matrices y
  diagramas, en dos estilos (educativo y directo).

## Instalación

### Usuario final (Windows)

Descargá `EduFEM-Setup.exe` y ejecutalo: se instala por usuario, sin permisos de
administrador. Guía completa: [installer/dist_extra/LEEME.txt](installer/dist_extra/LEEME.txt).

Para generar la **Memoria de Cálculo en PDF** hace falta una distribución LaTeX
([MiKTeX](https://miktex.org/download)). Sin ella, el resto del programa funciona normalmente.

### Desde el código fuente

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

Requiere **Python 3.11+**. Dependencias: NumPy, SciPy, SymPy, matplotlib, ttkbootstrap,
pylatex, PyMuPDF, Pillow, ezdxf. Opcional: `pdflatex` (memoria en PDF).

## Uso rápido

1. **Ayuda ▸ Cargar Ejemplo** — cuadrado de validación, viga de Timoshenko o membrana de
   Cook, en Q4 y Q9.
2. **F5** para resolver (o abrir la pestaña Post-Proceso).
3. **Ctrl+1..7** abren los módulos educativos sobre el elemento seleccionado.
4. **Archivo ▸ Guardar** — los modelos se guardan como `.edufem` (JSON).

## Verificación y validación

El motor está verificado con el **método de soluciones manufacturadas** (tasas de
convergencia asintóticas en normas L2 y H1) y validado contra la solución analítica de
**Timoshenko-Goodier** y un modelo Shell de **SAP2000** (error < 0,3 % en Q9), además del
benchmark de la **membrana de Cook**. Los scripts, datos y figuras están en
[docs/vyv/](docs/vyv/):

```bash
python -m tests.test_fem          # regresión numérica
python -m tests.vv_mms            # convergencia MMS
python -m tests.vv_timoshenko     # viga + contraste con SAP2000
python -m tests.vv_cook           # membrana de Cook
```

## Empaquetado

```bash
pyinstaller --noconfirm build.spec              # dist/EduFEM.exe (onefile)
powershell -File tools/build_all.ps1            # icono + .exe + instalador
```

## Estructura y documentación

| Ruta | Contenido |
|---|---|
| [docs/README.md](docs/README.md) | Índice de toda la documentación |
| [docs/MAPA.md](docs/MAPA.md) | Mapa del repositorio y dónde va cada cosa |
| [docs/convenciones/](docs/convenciones/) | Cómo está construido el software y por qué |
| [CLAUDE.md](CLAUDE.md) | Reglas de trabajo para agentes y colaboradores |
| [tesis/](tesis/) | Fuente LaTeX de la tesis |

## Licencia

MIT — ver [LICENSE](LICENSE).

**Autor**: Hedy Yhassmany Oyola Sucullani · <hedy.yhassmany@gmail.com>
